"""Pseudo-code for evo genomes: a static reading of what a body does.

`explain(body)` decodes a body as the CPU does (isa.rs; semantics in
sim.rs `step`), follows every path from byte 0 with what each register
can hold, and returns the listing in rows: one or a few instructions and
a line saying what they do. Its `story` is the path a new organism takes,
in one line, e.g. `absorb×64 → alloc 21 → copy×21 → divide(16) → repeat`
for the ancestor.

    from pseudo import explain
    r = explain(bytes.fromhex("13325271fc11401605086c5a1845486c11101c130d"))
    print(r.text())          # the listing
    r.story                  # the path in one line

    uv run pseudo.py HEX                    # one genome
    uv run pseudo.py RUN_DIR [--top 10]     # a run's genomes with the most exact births

What it tracks. A register holds a number, an address in the body (`@k`,
the address of byte k: `self 0` gives @0, `self 1` the IP), the child's
start (`alloc`), the executor's start (span mode, below), or the address
after a label a search found outside the body; anything else is unknown
(`?`). A new organism starts at byte 0 with every register 0. Where paths
meet, a register keeps up to four values ("3 or 4"; more is unknown), so
a loop counter is unknown inside its loop while the jump offset it loops
with stays known. A `skipz`/`skipnz` tells each of its two ways whether
the register is 0, so a counter is 0 after its loop. A jump through a
known register is followed, one through an unknown register is listed as
unresolved. `body ; dec R ; skipz R ; jump back` reads as "repeat n
times", n being R where the loop is entered (0 counts as 2^32); with
`inc R` it counts up, 2^32 - n times (`lit A -114 ; ... inc A` is 114).

The story follows one path from a new organism's start with that path's
own values, not the merged ones, so a register that differs between the
first round and later ones is still known on each. When it comes back to
a byte it has run, it runs the next round too; if that round differs (a
jump that depended on a register's first value), the story adds it as
"later rounds". It stops at a branch it cannot decide (the flag, a value
read while running), a jump to an unknown place, or the body's edge.

What it does not see. (1) Values only known while running: a byte loaded
from outside the body, the flag (`self 2`). (2) Bytes changed after
birth: it reads the bytes it is given; a `store` into the own body is
flagged, not followed. (3) Other organisms: a search with no match in
the body, or a jump out of it, ends the path, since what runs there is
someone else's code. Under `self_owner` (E006) `self 0` run on a host's
bytes gives the host's start; this assumes the executor's. (4) Copy
slips, range faults, and `alloc` failing (A = 0; a `skipz` on the
child's start allows for it). An address in the body or the executor's
start is taken as nonzero (it is 0 only for a body at address 0). (5) A
path that enters the middle of a `lit` is followed, but the rows are the
linear decode from byte 0 (as `evo-core --disasm`), so it shows as a
note on that `lit` row.

Span mode (`own=False, fresh=False`, world.py's inspector): the bytes are
any address span, entered at its first byte with every register unknown;
`self 0` then gives the executor's start, whose place relative to the
span is not known.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from dataclasses import dataclass
from pathlib import Path

MASK = 0xFFFF_FFFF
REGS = "ABCD"
LOCALITY = 512  # config.rs default since E004
FOREVER = 1_000_000  # loop counts above this print as forever
SET_MAX = 4  # values a register keeps where paths meet before it is unknown

# Low 5 bits of a byte -> op (isa.rs `Op`); unassigned slots decode as pad.
OPS = {
    0: "pad", 1: "nop0", 3: "nop1", 4: "inc", 5: "dec", 6: "shl", 7: "shr", 8: "skipz",
    9: "skipnz", 10: "searchf", 11: "searchb", 12: "jmpr", 13: "jmpa", 14: "add", 15: "sub",
    16: "zero", 17: "lit", 18: "swap", 19: "self", 20: "load", 21: "store", 22: "absorb",
    24: "copy", 26: "alloc", 28: "divide",
}
# Ops that read the register-select modifier (`isa::uses_reg`).
REG_OPS = frozenset({
    "inc", "dec", "shl", "shr", "add", "sub", "zero", "lit", "swap", "load", "store",
    "skipz", "skipnz", "jmpr", "jmpa", "alloc", "divide",
})
NOPS = frozenset({"pad", "nop0", "nop1"})
# Ops that only change registers; a run of them reads as one row.
QUIET = NOPS | {"inc", "dec", "shl", "shr", "add", "sub", "zero", "lit", "swap", "self", "load"}
JUMPS = frozenset({"jmpr", "jmpa"})
SKIPS = frozenset({"skipz", "skipnz"})
SEARCHES = frozenset({"searchf", "searchb"})
# Ops a row of register ops may end with, when they read a register it set.
ACTIONS = frozenset({"alloc", "divide", "jmpr", "jmpa", "store", "skipz", "skipnz"})
ALL = frozenset(range(4))
GROUP_MAX = 5


@dataclass(frozen=True)
class Ins:
    off: int
    op: str
    reg: int          # register 0..3 for register ops; `self`'s variant 0..2; else 0
    mod: int          # the raw modifier bits
    val: int | None   # `lit` operand, signed; None if the body ends first
    size: int

    @property
    def text(self) -> str:
        if self.op == "lit":
            return f"lit {REGS[self.reg]} {'?' if self.val is None else self.val}"
        if self.op in REG_OPS:
            return f"{self.op} {REGS[self.reg]}"
        if self.op == "self":
            return f"self {self.mod}"
        return self.op


def decode(code: bytes, off: int) -> Ins:
    """The instruction at `code[off]`, as `isa::decode` and `disasm_at`."""
    b = code[off]
    op, m = OPS.get(b & 0x1F, "pad"), b >> 5
    reg = m & 3 if op in REG_OPS else (min(m, 2) if op == "self" else 0)
    if op == "lit":
        val = None
        if off + 1 < len(code):
            v = code[off + 1]
            val = v - 256 if v >= 128 else v
        return Ins(off, op, reg, m, val, 2)
    return Ins(off, op, reg, m, None, 1)


# ---- values ------------------------------------------------------------------

NUM = ""


@dataclass(frozen=True)
class V:
    """One value a register can hold. `base` NUM: the number `k` (as the
    u32 the register holds); "code": the address of byte k of the code;
    "child": the child's start + k; "exec": the executor's start + k;
    "found": the address after label `tag`, found outside the code, + k.
    For a number, `tag` says where it came from ("my length")."""
    base: str
    k: int
    tag: str = ""


# A register: the set of values it can hold, or None for unknown.
Val = frozenset | None
State = tuple[Val, Val, Val, Val]


def num(x: int, tag: str = "") -> V:
    return V(NUM, x & MASK, tag)


def known(x: int, tag: str = "") -> Val:
    return frozenset({num(x, tag)})


def only(v: V) -> Val:
    return frozenset({v})


def signed(x: int) -> int:
    return x - (1 << 32) if x >= 1 << 31 else x


def vals(vs) -> Val:
    """The set of `vs` (one value per number or address, a tag kept only
    if every copy has it), or None if it holds more than SET_MAX."""
    d: dict[tuple[str, int], V] = {}
    for v in vs:
        key = (v.base, v.k)
        if key in d and d[key].tag != v.tag:
            d[key] = V(v.base, v.k)
        else:
            d.setdefault(key, v)
    return frozenset(d.values()) if len(d) <= SET_MAX else None


def lift(f, *regs: Val) -> Val:
    """Apply `f` to every combination of the registers' values; unknown
    if any register is, or `f` gives None for any combination."""
    if any(r is None for r in regs):
        return None
    out = []
    for combo in itertools.product(*regs):
        x = f(*combo)
        if x is None:
            return None
        out.append(x)
    return vals(out)


def shift(v: V, d: int) -> V:
    if v.base == NUM:
        return num(v.k + d)
    return V(v.base, v.k + d, v.tag if v.base == "found" else "")


def add1(a: V, b: V) -> V | None:
    if b.base == NUM:
        return shift(a, signed(b.k))
    if a.base == NUM:
        return shift(b, signed(a.k))
    return None


def sub1(a: V, b: V) -> V | None:
    if b.base == NUM:
        return shift(a, -signed(b.k))
    if a.base == b.base and a.base != "found":
        return num(a.k - b.k)
    return None


def join(a: Val, b: Val) -> Val:
    return None if a is None or b is None else vals(a | b)


def join_state(s: State, t: State) -> State:
    return tuple(join(a, b) for a, b in zip(s, t))  # type: ignore[return-value]


def maybe_zero(v: V) -> bool:
    # The child's start is 0 when `alloc` failed; a search's find is 0 when
    # there was none.
    return (v.base == NUM and v.k == 0) or v.base in ("child", "found")


def maybe_nonzero(v: V) -> bool:
    return not (v.base == NUM and v.k == 0)


# ---- searches ----------------------------------------------------------------


@dataclass(frozen=True)
class Search:
    label: str        # the label it finds, as nop bits ("1010" = nop1 nop0 nop1 nop0)
    tl: int           # template length
    after: int        # offset after the template, where it carries on
    kind: str         # found | outside | fail | empty | open
    at: int = 0       # found: the offset after the matched label (D)
    start: int = 0    # found: the label's first byte


def search(code: bytes, ins: Ins, locality: int = LOCALITY) -> Search:
    """Where `searchf`/`searchb` at `ins` lands, within `code` (sim.rs: the
    template is the nops after it; a match is its complement; forward
    candidates start after the template, backward ones end before the
    search). `outside`: no match in the code, so it is wherever the first
    one in other memory is; `open`: the template runs to the end of the
    code, so its length is not known."""
    n, p, tmpl = len(code), ins.off + 1, []
    while p < n and len(tmpl) < locality and OPS.get(code[p] & 0x1F) in ("nop0", "nop1"):
        tmpl.append(code[p] & 0x1F == 3)
        p += 1
    label = "".join("0" if t else "1" for t in tmpl)
    tl = len(tmpl)
    if p >= n and tl < locality:
        return Search(label, tl, p, "open")
    if tl == 0:
        return Search(label, tl, p, "empty")
    want = ["nop0" if t else "nop1" for t in tmpl]

    def match(c: int) -> bool:
        return all(OPS.get(code[c + j] & 0x1F) == want[j] for j in range(tl))

    for k in range(locality):
        c = p + k if ins.op == "searchf" else ins.off - tl - k
        if c < 0 or c + tl > n:
            return Search(label, tl, p, "outside")
        if match(c):
            return Search(label, tl, p, "found", c + tl, c)
    return Search(label, tl, p, "fail")


# ---- reading -----------------------------------------------------------------


@dataclass
class Row:
    off: int          # first byte
    end: int          # one past the last byte
    code: str         # the instructions, " ; "-joined
    note: str         # what they do
    box: str = ""     # loop bracket: ┐ │ ┘
    reached: bool = True


@dataclass(frozen=True)
class Loop:
    head: int         # T, the jump target
    jump: int         # J, the jump back
    reg: int          # the counter
    up: bool          # counts up (`inc`)
    body: tuple[Ins, ...]
    entry: State      # registers where the loop is entered, over every way in
    defs: frozenset   # registers the loop writes


@dataclass
class Reading:
    code: bytes
    rows: list[Row]
    story: str
    unresolved: list[int]   # offsets of jumps with a target not known
    base: int = 0
    wrap: int | None = None

    def pos(self, off: int) -> int:
        a = self.base + off
        return a % self.wrap if self.wrap else a

    def text(self, ip: int | None = None) -> str:
        """The rows as a listing: address, instructions, loop bracket, what
        they do. `ip`: an offset to mark with `<- ip`."""
        w = min(max((len(r.code) for r in self.rows), default=0), 36)
        dw = max((len(str(self.pos(r.off))) for r in self.rows), default=1)
        out = [f"path: {self.story}", ""]
        for r in self.rows:
            mark = "   <- ip" if ip is not None and r.off <= ip < r.end else ""
            out.append(f"{self.pos(r.off):>{dw}}  {r.code:<{w}}  {r.box or ' '} {r.note}{mark}".rstrip())
        if any("@" in r.note for r in self.rows):
            out += ["", "@k: the address of byte k" + ("." if self.wrap is None else " (absolute).")]
        return "\n".join(out)


def _runs_text(ins: list[Ins]) -> str:
    """Instructions " ; "-joined, a run of one written once with `×count`."""
    runs: list[list] = []
    for x in ins:
        if runs and runs[-1][0] == x.text:
            runs[-1][1] += 1
        else:
            runs.append([x.text, 1])
    return " ; ".join(t if c == 1 else f"{t} ×{c}" for t, c in runs)


def _squeeze(words: list[str]) -> list[str]:
    """Runs of one word as `word×count`."""
    out: list[list] = []
    for w in words:
        if out and out[-1][0] == w:
            out[-1][1] += 1
        else:
            out.append([w, 1])
    return [w if c == 1 else f"{w}×{c}" for w, c in out]


def explain(code: bytes, own: bool = True, fresh: bool = True, locality: int = LOCALITY,
            base: int = 0, wrap: int | None = None) -> Reading:
    """Read `code` (module docstring). `own`: the code is the executor's
    body, so `self 0` gives @0 and the length; `fresh`: entered as a new
    organism (registers 0) rather than with registers unknown. `base`,
    `wrap`: show addresses as `base + offset` modulo `wrap` (span mode)."""
    return _Reader(bytes(code), own, fresh, locality, base, wrap).read()


class _Reader:
    def __init__(self, code: bytes, own: bool, fresh: bool, locality: int, base: int, wrap: int | None):
        self.code, self.n, self.own, self.fresh = code, len(code), own, fresh
        self.locality, self.base, self.wrap = locality, base, wrap
        self.where = "body" if own else "span"
        self._ins: dict[int, Ins] = {}
        self._search: dict[int, Search] = {}
        self.entry: State = (known(0),) * 4 if fresh else (None,) * 4  # type: ignore[assignment]

    # -- helpers

    def at(self, off: int) -> Ins:
        if off not in self._ins:
            self._ins[off] = decode(self.code, off)
        return self._ins[off]

    def srch(self, ins: Ins) -> Search:
        if ins.off not in self._search:
            self._search[ins.off] = search(self.code, ins, self.locality)
        return self._search[ins.off]

    def pos(self, off: int) -> str:
        a = self.base + off
        return str(a % self.wrap if self.wrap else a)

    def show1(self, v: V, addr: bool = False) -> str:
        if v.base == NUM:
            if addr:
                return f"address {v.k % self.wrap if self.wrap else signed(v.k)}"
            s = str(signed(v.k))
            return f"{s} ({v.tag})" if v.tag else s
        plus = f" + {v.k}" if v.k > 0 else (f" - {-v.k}" if v.k < 0 else "")
        if v.base == "code":
            if 0 <= v.k <= self.n:
                return f"@{self.pos(v.k)}" + (" (my start)" if v.k == 0 and self.own else "")
            return f"@{self.pos(0)}{plus}"
        if v.base == "child":
            return f"the child's start{plus}"
        if v.base == "exec":
            return f"the executor's start{plus}"
        return f"the address after label {v.tag or '?'} elsewhere{plus}"

    def show(self, r: Val, addr: bool = False) -> str:
        """A register's values in words; `addr`: numbers are addresses."""
        if r is None:
            return "?"
        return " or ".join(self.show1(v, addr) for v in sorted(r, key=lambda v: (v.base, v.k)))

    def brief(self, r: Val) -> str:
        """A number for the story: `21`, `16|40`, or `?`."""
        if r is None or any(v.base != NUM for v in r):
            return "?"
        return "|".join(str(signed(v.k)) for v in sorted(r, key=lambda v: signed(v.k)))

    # -- one instruction

    def step(self, ins: Ins, s: State) -> list[tuple[int | None, State]]:
        """Each way on from `ins` given registers `s`: (offset, or None if
        not known; registers there)."""
        r, x, op = list(s), ins.reg, ins.op
        nxt = ins.off + ins.size
        if op == "inc":
            r[x] = lift(lambda v: shift(v, 1), r[x])
        elif op == "dec":
            r[x] = lift(lambda v: shift(v, -1), r[x])
        elif op in ("shl", "shr"):
            r[x] = lift(lambda v: None if v.base != NUM else num(v.k << 1 if op == "shl" else v.k >> 1), r[x])
        elif op == "add":
            r[0] = lift(add1, r[0], r[x])
        elif op == "sub":
            r[0] = lift(sub1, r[0], r[x])
        elif op == "zero":
            r[x] = known(0)
        elif op == "lit":
            r[x] = None if ins.val is None else known(ins.val)
        elif op == "swap":
            r[0], r[x] = r[x], r[0]
        elif op == "self":
            if x == 0:
                r[0] = only(V("code" if self.own else "exec", 0))
                r[1] = known(self.n, "my length") if self.own else None
            elif x == 1:
                r[0] = only(V("code", ins.off))
            else:
                r[0] = None
        elif op == "load":
            def byte(a: V) -> V | None:
                ok = a.base == "code" and 0 <= a.k < self.n
                return num(self.code[a.k], f"byte {a.k}") if ok else None
            r[x] = lift(byte, r[0])
        elif op == "copy":
            r[0], r[1] = lift(lambda v: shift(v, 1), r[0]), lift(lambda v: shift(v, 1), r[1])
        elif op in SEARCHES:
            f = self.srch(ins)
            if f.kind == "found":
                r[3], r[2] = only(V("code", f.at)), known(f.tl, "label length")
            elif f.kind == "outside":
                r[3], r[2] = only(V("found", 0, f.label)), join(known(f.tl), r[2])
            elif f.kind in ("fail", "empty"):
                r[3] = known(0)
            else:
                r[3], r[2] = None, None
            return [(f.after, tuple(r))]  # type: ignore[list-item]
        elif op == "alloc":
            v = r[x]
            never = v is not None and all(e.base == NUM and not 1 <= e.k <= self.locality for e in v)
            r[0] = known(0) if never else only(V("child", 0))
        elif op in SKIPS:
            if nxt >= self.n:
                return [(nxt, tuple(r))]  # type: ignore[list-item]
            far = nxt + self.at(nxt).size
            v = r[x]
            z, nz = list(r), list(r)
            z[x] = known(0)
            nz[x] = None if v is None else vals(e for e in v if maybe_nonzero(e))
            can_z = v is None or any(maybe_zero(e) for e in v)
            can_nz = v is None or bool(nz[x])
            out = []
            if can_nz:
                out.append((far if op == "skipnz" else nxt, tuple(nz)))
            if can_z:
                out.append((far if op == "skipz" else nxt, tuple(z)))
            return out  # type: ignore[return-value]
        elif op in JUMPS:
            v = r[x]
            if v is None:
                return [(None, tuple(r))]  # type: ignore[list-item]
            # Each target gets the register's values that lead there.
            by: dict[int | None, list[V]] = {}
            for e in v:
                if op == "jmpr":
                    d = nxt + signed(e.k) if e.base == NUM else None
                else:
                    d = e.k if e.base == "code" else None
                by.setdefault(d, []).append(e)
            out = []
            for d in sorted(by, key=lambda d: (d is None, d or 0)):
                r[x] = vals(by[d])
                out.append((d, tuple(r)))
            return out  # type: ignore[return-value]
        return [(nxt, tuple(r))]  # type: ignore[list-item]

    def uses_defs(self, ins: Ins) -> tuple[set[int], set[int]]:
        x, op = ins.reg, ins.op
        if op in ("inc", "dec", "shl", "shr"):
            return {x}, {x}
        if op in ("add", "sub"):
            return {0, x}, {0}
        if op in ("zero", "lit"):
            return set(), {x}
        if op == "swap":
            return {0, x}, {0, x}
        if op == "self":
            return set(), {0, 1} if x == 0 else {0}
        if op == "load":
            return {0}, {x}
        if op == "store":
            return {0, x}, set()
        if op == "copy":
            return {0, 1}, {0, 1}
        if op in SEARCHES:
            return set(), {2, 3} if self.srch(ins).kind == "found" else {3}
        if op == "alloc":
            return {x}, {0}
        if op in ("divide", "skipz", "skipnz", "jmpr", "jmpa"):
            return {x}, set()
        return set(), set()

    # -- the whole body

    def flow(self) -> None:
        """Registers on entry to every reachable offset, over every path
        (`self.state`), and each offset's ways on (`self.edges`)."""
        self.state: dict[int, State] = {0: self.entry}
        self.edges: dict[int, list[tuple[int | None, State]]] = {}
        work = [0]
        while work:
            p = work.pop()
            self.edges[p] = self.step(self.at(p), self.state[p])
            for d, out in self.edges[p]:
                if d is None or not 0 <= d < self.n:
                    continue
                old = self.state.get(d)
                new = out if old is None else join_state(old, out)
                if new != old:
                    self.state[d] = new
                    work.append(d)
        self.preds: dict[int, list[tuple[int, State]]] = {}
        for p, es in self.edges.items():
            for d, st in es:
                if d is not None and 0 <= d < self.n:
                    self.preds.setdefault(d, []).append((p, st))

    def liveness(self) -> None:
        """Registers read later on some path, at each offset (leaving the
        body counts as reading every register)."""
        self.live_in = {p: set() for p in self.state}
        order = sorted(self.state, reverse=True)
        changed = True
        while changed:
            changed = False
            for p in order:
                ins, out = self.at(p), self.live_out(p)
                if ins.op == "swap":
                    # A move both ways: each side is read only if the other is.
                    x = ins.reg
                    new = (out - {0, x}) | ({x} if 0 in out else set()) | ({0} if x in out else set())
                else:
                    use, df = self.uses_defs(ins)
                    new = use | (out - df)
                if new != self.live_in[p]:
                    self.live_in[p], changed = new, True

    def live_out(self, p: int) -> set[int]:
        out: set[int] = set()
        for d, _ in self.edges.get(p, []):
            out |= self.live_in[d] if d in self.live_in else ALL
        return out

    def leader(self, p: int) -> bool:
        """Whether `p` is entered other than by running on from the
        instruction before it."""
        def falls(q: int) -> bool:
            ins = self.at(q)
            return q + ins.size == p and ins.op not in JUMPS
        return p == 0 or any(not falls(q) for q, _ in self.preds.get(p, []))

    def loops(self) -> None:
        """Jumps back (`self.back`: jump offset -> target) and, of those,
        counted loops (`self.counted`: head -> Loop)."""
        self.back: dict[int, int] = {}
        self.counted: dict[int, Loop] = {}
        for j, es in self.edges.items():
            if self.at(j).op not in JUMPS or len(es) != 1:
                continue
            t = es[0][0]
            if t is None or not 0 <= t <= j:
                continue
            self.back[j] = t
            lp = self.counted_loop(t, j)
            if lp is not None and t not in self.counted:
                self.counted[t] = lp

    def counted_loop(self, t: int, j: int) -> Loop | None:
        if j < 2 or not {t, j - 2, j - 1, j} <= self.linear:
            return None
        sk, dc = self.at(j - 1), self.at(j - 2)
        if sk.op != "skipz" or dc.op not in ("dec", "inc") or sk.reg != dc.reg:
            return None
        body, p = [], t
        while p < j - 2:
            body.append(self.at(p))
            p += body[-1].size
        if p != j - 2:
            return None
        if any(i.op in JUMPS | SKIPS | SEARCHES or dc.reg in self.uses_defs(i)[1] for i in body):
            return None
        ways_in = [st for q, st in self.preds.get(t, []) if not t <= q <= j]
        if not ways_in:
            return None
        entry = ways_in[0]
        for st in ways_in[1:]:
            entry = join_state(entry, st)
        defs = {dc.reg}
        for i in body:
            defs |= self.uses_defs(i)[1]
        return Loop(t, j, dc.reg, dc.op == "inc", tuple(body), entry, frozenset(defs))

    # -- words

    def counts(self, lp: Loop, s: State) -> list[int] | None:
        """Rounds the loop runs given registers `s` at its head."""
        v = s[lp.reg]
        if v is None or any(e.base != NUM for e in v):
            return None
        return sorted({((-e.k) & MASK if lp.up else e.k) or 1 << 32 for e in v})

    def times(self, lp: Loop, s: State) -> str:
        c, rn = self.counts(lp, s), REGS[lp.reg]
        if c is None:
            return f"until {rn} reaches 0 ({rn} not known on entry)"
        if max(c) > FOREVER:
            return f"{' or '.join(f'{x:,}' for x in c)} times (in effect forever)"
        tags = {e.tag for e in s[lp.reg]}  # type: ignore[union-attr]
        tag = f" ({tags.pop()})" if len(tags) == 1 and "" not in tags else ""
        return f"{' or '.join(f'{x:,}' for x in c)} times{tag}"

    def loop_says(self, lp: Loop, s: State) -> tuple[str, str]:
        """(what one round does, the story's word for the loop), given
        registers `s` at its head."""
        ops = [i.op for i in lp.body]
        n_ab, n_cp = ops.count("absorb"), ops.count("copy")
        other = [i for i in lp.body if i.op not in ("absorb", "copy")]
        moves_ab = any(self.uses_defs(i)[1] & {0, 1} for i in other)
        parts, words = [], []
        if n_cp:
            words.append("copy")
            a, b = s[0], s[1]
            if n_cp == 1 and not moves_ab and self.own and a == only(V("child", 0)) \
                    and b == only(V("code", 0)) and self.counts(lp, s) == [self.n]:
                parts.append(f"copy all {self.n} of my bytes into the child")
            elif n_cp == 1 and not moves_ab:
                parts.append(f"copy a byte from {self.show(b, True)} on to {self.show(a, True)} on")
            else:
                parts.append(f"copy {n_cp} bytes from B to A")
        if n_ab:
            words.append("absorb")
            parts.append("absorb energy" + (f" ({n_ab} per round)" if n_ab > 1 else ""))
        if other:
            parts.append(", ".join(i.text for i in other))
        if not lp.body:
            return "count only (a delay)", "wait"
        return "; ".join(parts), "+".join(words) or "loop"

    def lost(self, ins: Ins, s: State) -> str:
        """Where a jump goes when the reading cannot follow it."""
        v, rn = s[ins.reg], REGS[ins.reg]
        if v is None:
            return f"go to an unknown place ({rn} not known here)"
        e = next((e for e in v if not (e.base == "code" if ins.op == "jmpa" else e.base == NUM)), None)
        if e is None:
            return ""
        if e.base == "found":
            return f"go to the code after label {e.tag}, outside this {self.where} (address 0 if none was found)"
        if e.base in ("child", "exec"):
            return f"go to {self.show1(e)}"
        if e.base == NUM:
            return f"go to address {e.k}"
        return f"go to an unknown place ({rn} = {self.show(v)})"

    def jump_says(self, ins: Ins, s: State) -> str:
        dsts = [d for d, _ in self.edges.get(ins.off, [])]
        inside = [d for d in dsts if d is not None and 0 <= d < self.n]
        parts = []
        if inside:
            t = " or ".join(self.pos(d) for d in inside)
            parts.append(f"go to {t}" + (" (start over)" if inside == [0] and self.own else ""))
        for d in dsts:
            if d is not None and not 0 <= d < self.n:
                parts.append(f"go on past the end of the {self.where}" if d == self.n
                             else f"leave the {self.where}: go to offset {d}")
        if None in dsts:
            parts.append(self.lost(ins, s))
        return "; or ".join(p for p in parts if p)

    def says(self, ins: Ins, s: State) -> str:
        """What one instruction does, given the registers before it."""
        op, x, rn = ins.op, ins.reg, REGS[ins.reg]
        v = s[x]
        if op == "absorb":
            return "absorb energy"
        if op == "alloc":
            if v is not None and all(e.base == NUM and not 1 <= e.k <= self.locality for e in v):
                return f"claim {self.show(v)} bytes: always fails, so A = 0, flag set"
            return f"claim {self.show(v)} bytes for a child: A = its start (A = 0, flag set, if no room)"
        if op == "divide":
            return f"split off the child, giving it {self.show(v)} energy"
        if op == "copy":
            return f"copy the byte at {self.show(s[1], True)} to {self.show(s[0], True)}; A, B step on"
        if op == "store":
            a = s[0]
            t = f"write {rn} ({self.show(v)}) to {self.show(a, True)}"
            if a is not None and any(e.base == "code" and 0 <= e.k < self.n for e in a):
                t += ": its own code, so what runs may differ from this listing"
            return t
        if op == "load":
            return f"{rn} = the byte at {self.show(s[0], True)}"
        if op in JUMPS:
            return self.jump_says(ins, s)
        if op in SKIPS:
            t = f"if {rn} {'=' if op == 'skipz' else '≠'} 0, skip the next instruction"
            if v is not None and all(e.base == NUM for e in v):
                zs = {e.k == 0 for e in v}
                if len(zs) == 1:
                    skips = zs.pop() == (op == "skipz")
                    t += f" ({rn} = {self.show(v)} here: {'always skips' if skips else 'never skips'})"
            elif v is not None and not any(maybe_zero(e) for e in v):
                t += f" ({rn} = {self.show(v)}, not 0: {'never skips' if op == 'skipz' else 'always skips'})"
            return t
        if op in SEARCHES:
            f, way = self.srch(ins), "ahead" if op == "searchf" else "behind"
            if f.kind == "found":
                return f"find label {f.label} {way}: D = {self.show1(V('code', f.at))}, C = {f.tl}"
            if f.kind == "outside":
                return (f"look {way} for label {f.label}: none in this {self.where}, so D = the address after "
                        f"the first one in other code (0, flag set, if none within {self.locality})")
            if f.kind == "fail":
                return f"look {way} for label {f.label}: none within {self.locality}, so D = 0, flag set"
            if f.kind == "empty":
                return "search with no template: fails (D = 0, flag set)"
            return f"template runs past the end of the {self.where}: result unknown"
        if op in NOPS:
            return "does nothing"
        if op == "self":
            return ["A = my start, B = my length", "A = this address", "A = the flag, which is cleared"][x]
        return {
            "inc": f"{rn} + 1", "dec": f"{rn} - 1", "shl": f"{rn} × 2", "shr": f"{rn} ÷ 2",
            "add": f"A = A + {rn}", "sub": f"A = A - {rn}", "zero": f"{rn} = 0",
            "lit": f"{rn} = {ins.val}", "swap": f"swap A and {rn}",
        }[op]

    def assigns(self, regs: set[int], s: State) -> str:
        return ", ".join(f"{REGS[x]} = {self.show(s[x])}" for x in sorted(regs))

    # -- rows

    def rows(self) -> list[Row]:
        lin, reached = self.lin, self.state.keys()
        labels: dict[int, tuple[Search, list[int]]] = {}
        for p in reached:
            ins = self.at(p)
            if ins.op in SEARCHES and self.srch(ins).kind == "found":
                f = self.srch(ins)
                if all(q in self.linear for q in range(f.start, f.at)):
                    labels.setdefault(f.start, (f, []))[1].append(p)
        rows: list[Row] = []
        idx = {ins.off: i for i, ins in enumerate(lin)}
        i = 0
        while i < len(lin):
            ins = lin[i]
            p = ins.off
            if p in self.counted and p in reached:
                lp = self.counted[p]
                what, _ = self.loop_says(lp, lp.entry)
                tail = " ; ".join(self.at(q).text for q in (lp.jump - 2, lp.jump - 1, lp.jump))
                if len(lp.body) <= 2:
                    code_ = " ; ".join([b.text for b in lp.body] + [tail])
                    rows.append(Row(p, lp.jump + 1, code_, f"repeat {self.times(lp, lp.entry)}: {what}"))
                else:
                    for k, b in enumerate(lp.body):
                        rows.append(Row(b.off, b.off + b.size, b.text, self.says(b, self.state[b.off]),
                                        "┐" if k == 0 else "│"))
                    rows.append(Row(lp.jump - 2, lp.jump + 1, tail,
                                    f"repeat from {self.pos(p)}, {self.times(lp, lp.entry)} in all: {what}", "┘"))
                i = idx[lp.jump] + 1
                continue
            if ins.op in SEARCHES and p in reached:
                f = self.srch(ins)
                j = idx.get(f.after, len(lin))
                rows.append(Row(p, f.after, " ; ".join(x.text for x in lin[i:j]), self.says(ins, self.state[p])))
                i = j
                continue
            if p in labels:
                f, by = labels[p]
                j = idx.get(f.at, len(lin))
                note = f"label {f.label}: " + ", ".join(f"{self.at(q).op} at {self.pos(q)}" for q in sorted(by)) \
                    + " lands after it" + ("; runs as no-ops when reached" if p in reached else "")
                rows.append(Row(p, f.at, " ; ".join(x.text for x in lin[i:j]), note, reached=p in reached))
                i = j
                continue
            if p not in reached:
                j = i
                while j < len(lin) and lin[j].off not in reached and lin[j].off not in labels:
                    j += 1
                note = "not reached on any path found (some jumps are unresolved)" if self.unresolved \
                    else "never runs"
                # Rows of up to six runs of one instruction each.
                cuts = [k for k in range(i, j) if k == i or lin[k].text != lin[k - 1].text]
                for a, b in zip(cuts[::6], cuts[6::6] + [j]):
                    last = lin[b - 1]
                    rows.append(Row(lin[a].off, last.off + last.size, _runs_text(lin[a:b]), note, reached=False))
                i = j
                continue
            if ins.op in NOPS:
                j = i + 1
                while (j < len(lin) and lin[j].op in NOPS and lin[j].off in reached
                       and not self.leader(lin[j].off) and lin[j].off not in labels):
                    j += 1
                rows.append(Row(p, lin[j - 1].off + 1, _runs_text(lin[i:j]), "does nothing"))
                i = j
                continue
            if ins.op in QUIET:
                j = i + 1
                while (j < len(lin) and j - i < GROUP_MAX and lin[j].op in QUIET and lin[j].off in reached
                       and not self.leader(lin[j].off) and lin[j].off not in labels):
                    j += 1
                grp = lin[i:j]
                defs: set[int] = set()
                for x in grp:
                    defs |= self.uses_defs(x)[1]
                last = grp[-1]
                after = self.edges[last.off][0][1]
                act = lin[j] if j < len(lin) else None
                if (act is not None and act.op in ACTIONS and act.off in reached and not self.leader(act.off)
                        and self.uses_defs(act)[0] & defs):
                    keep = defs & self.live_out(act.off) - self.uses_defs(act)[1] - self.uses_defs(act)[0]
                    note = self.says(act, self.state[act.off]) + (f"; {self.assigns(keep, after)}" if keep else "")
                    grp = lin[i:j + 1]
                    j += 1
                else:
                    keep = defs & self.live_out(last.off)
                    if keep:
                        note = self.assigns(keep, after)
                    elif len(grp) == 1:
                        note = self.says(last, self.state[last.off]) + " (not used after)"
                    else:
                        note = "no lasting effect"
                rows.append(Row(p, grp[-1].off + grp[-1].size, " ; ".join(x.text for x in grp), note))
                i = j
                continue
            rows.append(Row(p, p + ins.size, ins.text, self.says(ins, self.state[p])))
            i += 1
        for r in rows:
            if not r.reached:
                continue
            for q in range(r.off, r.end):
                # Running on past the end of the body (a jump says so itself).
                if q in self.edges and self.at(q).op not in JUMPS and "past the end" not in r.note \
                        and any(d == self.n for d, _ in self.edges[q]):
                    r.note += f"; then runs on past the end of the {self.where}"
                # A path that runs a `lit` operand byte as an instruction.
                if q in self.state and q not in self.linear:
                    r.note += f"; its byte {self.pos(q)} also runs, as `{self.at(q).text}`"
        # Brackets for loops that are not counted loops, unless they hold
        # one (the life cycle's jump back to the start reads plainer as
        # "go to 0" than as a bracket round the whole listing).
        for j, t in sorted(self.back.items()):
            if any(t <= h <= j for h in self.counted):
                continue
            a = next((k for k, r in enumerate(rows) if r.off <= t < r.end), None)
            b = next((k for k, r in enumerate(rows) if r.off <= j < r.end), None)
            if a is None or b is None or a >= b or any(rows[k].box for k in range(a, b + 1)):
                continue
            for k in range(a, b + 1):
                rows[k].box = "┐" if k == a else ("┘" if k == b else "│")
        return rows

    # -- the story

    def event(self, ins: Ins, s: State) -> str:
        op, v = ins.op, s[ins.reg]
        if op == "absorb":
            return "absorb"
        if op == "alloc":
            return f"alloc {self.brief(v)}"
        if op == "divide":
            return f"divide({self.brief(v)})"
        if op in ("copy", "store"):
            return op
        if op in SEARCHES and self.srch(ins).kind in ("outside", "fail"):
            return f"search {self.srch(ins).label} outside"
        return ""

    def walk(self, p: int, s: State) -> tuple[list[str], tuple]:
        """Events from offset `p` with registers `s`, along one path, until
        it comes back to an offset it ran (("again", offset, registers,
        index of that offset's first event)) or stops (("stop", why))."""
        ev: list[str] = []
        first: dict[int, int] = {}
        while True:
            if not 0 <= p < self.n:
                end = "runs on past its end" if self.own else "runs on past the span"
                return ev, ("stop", end if p == self.n else f"leaves the {self.where} (to offset {p})")
            if p in first:
                return ev, ("again", p, s, first[p])
            first[p] = len(ev)
            if p in self.counted:
                lp = self.counted[p]
                c, (_, word) = self.counts(lp, s), self.loop_says(lp, s)
                ev.append(f"{word}×{'?' if c is None else ('∞' if max(c) > FOREVER else '|'.join(map(str, c)))}")
                for q in range(p, lp.jump + 1):
                    first.setdefault(q, first[p])
                # After the loop: its counter is 0; what it writes is as on
                # every way out; the rest is as it came in.
                # A copy loop moves A and B on by its rounds.
                out = list(next(st for d, st in self.edges[lp.jump - 1] if d == lp.jump + 1))
                if c is not None and len(c) == 1 and c[0] <= FOREVER and lp.reg > 1 \
                        and {i.op for i in lp.body} <= {"copy", "absorb"}:
                    k = c[0] * [i.op for i in lp.body].count("copy")
                    out[0], out[1] = lift(lambda v: shift(v, k), s[0]), lift(lambda v: shift(v, k), s[1])
                s = tuple(known(0) if x == lp.reg else (out[x] if x in lp.defs else s[x])  # type: ignore[assignment]
                          for x in range(4))
                p = lp.jump + 1
                continue
            ins = self.at(p)
            e = self.event(ins, s)
            if e:
                ev.append(e)
            ways = self.step(ins, s)
            if len(ways) > 1:
                return ev, ("stop", f"branch at {self.pos(p)} (on {REGS[ins.reg]})")
            d, s = ways[0]
            if d is None:
                v = s[ins.reg]
                e = next((e for e in v or () if e.base != "code"), None) if ins.op == "jmpa" else None
                if e is not None and e.base == "found":
                    why = f"jump to label {e.tag} outside"
                elif e is not None and e.base in ("child", "exec"):
                    why = "jump into the child" if e.base == "child" else "jump into the executor"
                elif e is not None and e.base == NUM:
                    why = f"jump to address {e.k}"
                else:
                    why = f"jump to ? (at {self.pos(p)})"
                return ev, ("stop", why)
            p = d

    def story(self) -> str:
        ev, end = self.walk(0, self.entry)
        words = _squeeze(ev)
        if end[0] == "stop":
            words.append(end[1])
        else:
            _, q, s, i = end
            again = "repeat" if q == 0 else f"repeat from {self.pos(q)}"
            ev2, end2 = self.walk(q, s)
            same = ev2 == ev[i:] and end2[0] == "again" and end2[1] == q
            words.append(again)
            if not same:
                more = (_squeeze(ev2) or ["nothing"]) + [end2[1] if end2[0] == "stop" else
                                        ("repeat" if end2[1] == 0 else f"repeat from {self.pos(end2[1])}")]
                words[-1] += "; later rounds: " + " → ".join(more)
        if not ev:
            words.insert(0, "nothing")
        return " → ".join(words)

    def read(self) -> Reading:
        if self.n == 0:
            return Reading(self.code, [], "empty body", [], self.base, self.wrap)
        self.flow()
        self.lin, self.linear, p = [], set(), 0
        while p < self.n:
            self.lin.append(self.at(p))
            self.linear.add(p)
            p += self.lin[-1].size
        self.unresolved = sorted(p for p, es in self.edges.items() if any(d is None for d, _ in es))
        self.liveness()
        self.loops()
        return Reading(self.code, self.rows(), self.story(), self.unresolved, self.base, self.wrap)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("what", help="a genome as hex, or a run directory")
    ap.add_argument("--top", type=int, default=10, help="with a run directory: how many genomes, by exact births")
    a = ap.parse_args()
    if (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    if not Path(a.what).is_dir():
        print(explain(bytes.fromhex(a.what)).text())
        return
    import polars as pl

    from evo_run import load

    run = load(a.what)
    loc = run.meta.get("config", {}).get("locality", LOCALITY)
    top = (run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash"))
           .group_by("raw_hash").len().sort("len", descending=True).head(a.top)
           .join(run.genomes.select("raw_hash", "bytes_hex"), on="raw_hash", how="left")
           .sort("len", descending=True))
    for h, births, hx in top.select("raw_hash", "len", "bytes_hex").iter_rows():
        print(f"== {h}: {births:,} exact births, {len(hx) // 2} bytes")
        print(explain(bytes.fromhex(hx), locality=loc).text())
        print()


if __name__ == "__main__":
    main()
