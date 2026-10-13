"""Line of descent with fitness per step (T06; Lenski, Ofria, Pennock & Adami
2003 as the model: the path from the founder to one late organism, with the
fitness of every genome on it). Spec: docs/tasks/T06-lenski-lod.md.

    uv run lod.py RUN_DIR [--at TICK] [--pick top|id:N] [--harness-ticks 3000]
                          [--out DIR] [--evo-bin PATH]

Writes OUT/steps.csv, OUT/genomes.csv, OUT/line.csv and OUT/summary.md
(OUT defaults to RUN_DIR/lod). The harness binary is `--evo-bin`, else the
`EVO_BIN` environment variable, else evo_run's (which builds evo-core).

The line.
1. End organism: at census tick `--at` (default the last census), the
   living bodies are grouped by the `func_hash` of their birth genome; the
   group with the most bodies whose genome is `replicator` in the harness
   is taken (the class of a group is that of its most common raw birth
   genome: from RUN_DIR/classes.csv if present, else the harness is run on
   the candidates, largest group first). Within it, the body with the most
   `offspring` (ties: earliest birth, then lowest id). `--pick id:N` names
   the end organism instead.
2. Walk back through births.csv by child -> executor to a founder (an
   organism with no births row: parent 0). Every organism on the line
   contributes its birth genome (line.csv: generation, id, birth tick,
   raw and func hash, bytes).
3. A step is a pair of consecutive organisms whose birth genomes differ.
   Edits come from a shortest edit script (Levenshtein, unit costs; among
   equal-cost scripts the backtrace prefers substitution, then deletion,
   then insertion, so an insertion into a run of equal bytes is placed at
   the run's left end). Positions are in the parent's bytes; an insertion
   at p goes before the parent's byte p. `synonymous` = same func_hash.
   `origin`: `copy` (the executor's body at divide was its birth genome, so
   the change arose in copying), `somatic` (the child equals the executor's
   body at divide, which had changed since its birth: inherited from a
   somatic change) or `somatic+copy` (both). `source_is_executor` is false
   when the copy loop read another organism's or free bytes.
4. Harness fitness per distinct genome on the line, `--harness-ticks`
   quiet ticks in the code's default physics (E007's world): alone
   (`--classify` over a temporary genomes.csv: class, births, exact
   births, first birth tick) and entered (`--host 00 --host-body HEX`: a
   one-byte `pad` placed before it; the host's exact births and whether it
   is alive, and the pad's exact births, ticks run and `stopped_early`;
   the harness stops when the pad dies, so counts then cover only
   `ticks_run` ticks).
5. World fitness per genome over organisms born with that raw hash in an
   E007 window of 25,000 ticks (window w = ticks ((w-1)*25000, w*25000];
   tick 0 is in window 1): born, died by the end of the run, mean exact
   children per death (children whose raw hash equals the organism's birth
   genome, summed over the organisms that died, over the number that
   died) and median age at death. In genomes.csv the window is the one in
   which the genome first appears on the line; in steps.csv both genomes
   of a step are measured in the step's window (the child's birth tick).

Effect of a step, from f = exact children alone: `beneficial` if
f(child) > f(parent) + 1, `deleterious` if f(child) < f(parent) - 1, else
`neutral`.

Absorb count of a genome: located by pattern, `lit R v ; absorb ; dec R ;
skipz R` (count v, if v > 0) or `lit R v ; absorb ; inc R ; skipz R`
(count -v, if v < 0; E007 seed 3's `lit A -114 ; inc A`), the first such
`absorb` in the canonical parse; a loop of that shape that cannot end
(dec from v <= 0, inc from v >= 0) gives no count. Without the pattern,
the byte (traits.ABSORB: byte 6 as a signed byte when byte 5 is `lit`).
Both are in genomes.csv (`absorb_pat`, `absorb_byte`); `absorb` is the one
used. The absorb-count step (the spec's) is the first step whose child has
the end genome's absorb count and whose parent does not. On E007 lines that
count is set by drift on the flat 112-127 plateau long after the sweep, so
the summary also gives the sweep step: the first step whose child reaches
traits.ABSORB's threshold (96) from below. Each comes with the effect of
the step immediately before it and the three steps before it.

Caveats (spec section 4): harness fitness is measured with a full pool and
no neighbours, and E007's break-even argument says the longer absorb phase
pays on a lower ration, which the harness cannot see; the world columns are
the check. The line is one path.
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import polars as pl

import evo_run
from evo_run import HASH_COLS
from traits import ABSORB, LIT, canonical_instrs

WINDOW = 25_000
ABSORB_OP, INC, DEC, SKIPZ = 22, 4, 5, 8
PAD_HEX = "00"
EFFECT_LETTER = {"beneficial": "B", "neutral": "n", "deleterious": "D"}


class NoLine(Exception):
    """No line can be drawn (no living organisms at the tick, or no
    replicator-class group, or an unknown id)."""


# --- binary and harness ------------------------------------------------------


def evo_bin(path: str | Path | None = None) -> Path:
    """`path`, else $EVO_BIN, else evo_run.binary() (builds evo-core)."""
    p = path or os.environ.get("EVO_BIN")
    if p:
        p = Path(p)
        if not p.exists():
            raise FileNotFoundError(f"evo-core binary not found: {p}")
        return p
    return evo_run.binary()


def harness_alone(exe: Path, genomes: dict[str, str], ticks: int) -> dict[str, dict]:
    """Single-genome harness (`--classify` over a temporary genomes.csv).
    `genomes` maps raw hash -> bytes hex; returns raw hash -> {class, births,
    exact_births, first_birth_tick, alive}."""
    if not genomes:
        return {}
    with tempfile.TemporaryDirectory(prefix="lod_") as tmp:
        with open(Path(tmp) / "genomes.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["raw_hash", "bytes_hex"])
            w.writerows(genomes.items())
        subprocess.run([str(exe), "--classify", tmp, "--harness-ticks", str(ticks)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(Path(tmp) / "classes.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    return {
        r["raw_hash"]: {
            "class": r["class"],
            "births": int(r["births"]),
            "exact_births": int(r["exact_births"]),
            "first_birth_tick": int(r["first_birth_tick"]),
            "alive": r["alive"] == "true",
        }
        for r in rows
    }


def harness_entered(exe: Path, host_hex: str, ticks: int) -> dict:
    """Two-genome harness: a one-byte `pad` placed immediately before the
    genome (`--host 00 --host-body HEX`). Returns {host_exact, host_alive,
    pad_exact, ticks_run, stopped_early}."""
    out = subprocess.run(
        [str(exe), "--host", PAD_HEX, "--host-body", host_hex, "--harness-ticks", str(ticks)],
        check=True, capture_output=True, text=True,
    ).stdout
    header, row = out.strip().splitlines()[:2]
    v = dict(zip(header.split(","), row.split(",")))
    return {
        "host_exact": int(v["host_exact_births"]),
        "host_alive": v["host_alive"] == "true",
        "pad_exact": int(v["exact_births"]),
        "ticks_run": int(v["ticks_run"]),
        "stopped_early": v["stopped_early"] == "true",
    }


# --- genome reading ----------------------------------------------------------


def edit_script(a: bytes, b: bytes) -> list[tuple[str, int, int | None, int | None]]:
    """Shortest edit script turning `a` into `b`: (kind, pos, old, new) with
    kind `sub`, `ins` or `del`, pos an index in `a` (an insertion goes before
    a[pos]). Tie-break as in the module docstring."""
    n, m = len(a), len(b)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j - 1] + (a[i - 1] != b[j - 1]), d[i - 1][j] + 1, d[i][j - 1] + 1)
    ops = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (a[i - 1] != b[j - 1]):
            if a[i - 1] != b[j - 1]:
                ops.append(("sub", i - 1, a[i - 1], b[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            ops.append(("del", i - 1, a[i - 1], None))
            i -= 1
        else:
            ops.append(("ins", i, None, b[j - 1]))
            j -= 1
    return ops[::-1]


KIND_NAME = {"sub": "substitution", "ins": "insertion", "del": "deletion"}


def step_kind(ops) -> str:
    """`substitution`, `insertion`, `deletion`, or several joined by `+`."""
    kinds = {k for k, *_ in ops}
    return "+".join(KIND_NAME[k] for k in ("sub", "ins", "del") if k in kinds)


def format_edits(ops) -> str:
    """`sub@6:40>78`, `ins@0:+00`, `del@20:-0d`, joined by `;`."""
    out = []
    for k, pos, old, new in ops:
        if k == "sub":
            out.append(f"sub@{pos}:{old:02x}>{new:02x}")
        elif k == "ins":
            out.append(f"ins@{pos}:+{new:02x}")
        else:
            out.append(f"del@{pos}:-{old:02x}")
    return ";".join(out)


def absorb_byte(body: bytes) -> int | None:
    """traits.ABSORB: byte 6 as a signed byte when byte 5 is `lit`."""
    t = ABSORB
    if len(body) <= t.offset or (body[t.guard] & 0x1F) != LIT:
        return None
    v = body[t.offset]
    return v - 256 if v >= 128 else v


def absorb_pattern(body: bytes) -> tuple[bool, int | None]:
    """(found, count) for the absorb loop located by pattern (module
    docstring); count None when the loop found cannot end."""
    ins = canonical_instrs(body)
    for k in range(1, len(ins) - 2):
        if ins[k][0] != ABSORB_OP:
            continue
        lop, lm, lv = ins[k - 1]
        xop, xm, _ = ins[k + 1]
        sop, sm, _ = ins[k + 2]
        if lop == LIT and lv is not None and xop in (DEC, INC) and xm == lm and sop == SKIPZ and sm == lm:
            if xop == DEC:
                return True, lv if lv > 0 else None
            return True, -lv if lv < 0 else None
    return False, None


def absorb_count(body: bytes) -> int | None:
    found, n = absorb_pattern(body)
    return n if found else absorb_byte(body)


def window_of(tick: int, size: int = WINDOW) -> int:
    return max(1, -(-tick // size))


# --- loading -----------------------------------------------------------------


def _path(run_dir: Path, name: str) -> Path:
    """NAME.csv, or NAME.csv.gz (E014 on compresses run files; polars reads
    either)."""
    p = evo_run.csv_path(run_dir, name)
    if p is None:
        raise FileNotFoundError(f"{run_dir}: no {name}.csv (plain or .gz)")
    return p


def _read(run_dir: Path, name: str, cols: list[str]) -> pl.DataFrame:
    over = {c: pl.Utf8 for c in HASH_COLS[name] if c in cols}
    return pl.read_csv(_path(run_dir, name), columns=cols, schema_overrides=over)


def _scan(run_dir: Path, name: str) -> pl.LazyFrame:
    return pl.scan_csv(_path(run_dir, name), schema_overrides={c: pl.Utf8 for c in HASH_COLS[name]})


@dataclass
class RunData:
    dir: Path
    births: pl.DataFrame      # sorted by child
    genomes: pl.DataFrame     # raw_hash, func_hash, len, bytes_hex, disasm
    founders: pl.DataFrame    # id, birth_tick, birth_hash (organisms with parent 0)
    census_ticks: list[int]
    classes: dict[str, str] | None
    _deaths: pl.DataFrame | None = None

    @property
    def deaths(self) -> pl.DataFrame:
        if self._deaths is None:
            self._deaths = _read(self.dir, "deaths", ["id", "age"])
        return self._deaths


def load_run(run_dir: str | Path) -> RunData:
    d = Path(run_dir)
    births = _read(d, "births", ["tick", "child", "executor", "source", "copy_errors", "slips",
                                 "raw_hash", "parent_hash", "parent_now_hash", "source_hash"]).sort("child")
    genomes = _read(d, "genomes", ["raw_hash", "func_hash", "len", "bytes_hex", "disasm"])
    founders = (
        _scan(d, "orgs").filter(pl.col("parent") == 0)
        .select("id", "birth_tick", "birth_hash").unique("id").collect().sort("id")
    )
    census_ticks = sorted(pl.read_csv(_path(d, "patches"), columns=["tick"])["tick"].unique().to_list())
    classes = None
    if (cp := evo_run.csv_path(d, "classes")) is not None:
        c = pl.read_csv(cp, columns=["raw_hash", "class"], schema_overrides={"raw_hash": pl.Utf8})
        classes = dict(c.iter_rows())
    return RunData(d, births, genomes, founders, census_ticks, classes)


# --- the line ----------------------------------------------------------------


@dataclass
class Pick:
    end_id: int
    at: int
    func_hash: str | None = None
    group_size: int | None = None
    group_class: str | None = None
    offspring: int | None = None
    skipped: list[tuple[str, int, str]] = field(default_factory=list)  # (func_hash, n, class) passed over


def pick_end(run: RunData, at: int, pick: str, exe: Path | None, ticks: int,
             cache: dict[str, dict]) -> Pick:
    if pick.startswith("id:"):
        return Pick(end_id=int(pick[3:]), at=at)
    if pick != "top":
        raise ValueError(f"--pick must be top or id:N, not {pick!r}")
    alive = _scan(run.dir, "orgs").filter(pl.col("tick") == at).select(
        "id", "birth_tick", "birth_hash", "offspring").collect()
    if alive.height == 0:
        raise NoLine(f"no living organisms at tick {at}")
    alive = alive.join(run.genomes.select(pl.col("raw_hash").alias("birth_hash"), "func_hash"),
                       on="birth_hash", how="left")
    groups = (
        alive.group_by("func_hash", "birth_hash").len()
        .sort(["func_hash", "len", "birth_hash"], descending=[False, True, False])
        .group_by("func_hash", maintain_order=True)
        .agg(rep=pl.col("birth_hash").first(), n=pl.col("len").sum())
        .sort(["n", "func_hash"], descending=[True, False])
    )
    hexes = dict(run.genomes.select("raw_hash", "bytes_hex").iter_rows())
    skipped = []
    rows = groups.rows(named=True)
    batch = 16
    for start in range(0, len(rows), batch):
        chunk = rows[start:start + batch]
        need = {r["rep"]: hexes[r["rep"]] for r in chunk
                if r["rep"] not in cache and not (run.classes and r["rep"] in run.classes)}
        if need:
            cache.update(harness_alone(exe, need, ticks))
        for r in chunk:
            cls = run.classes[r["rep"]] if run.classes and r["rep"] in run.classes else cache[r["rep"]]["class"]
            if cls != "replicator":
                skipped.append((r["func_hash"], r["n"], cls))
                continue
            g = alive.filter(pl.col("func_hash") == r["func_hash"]).sort(
                ["offspring", "birth_tick", "id"], descending=[True, False, False])
            e = g.row(0, named=True)
            return Pick(end_id=e["id"], at=at, func_hash=r["func_hash"], group_size=r["n"],
                        group_class=cls, offspring=e["offspring"], skipped=skipped)
    raise NoLine(f"no replicator-class func_hash among the living at tick {at}")


def walk_back(run: RunData, end_id: int) -> pl.DataFrame:
    """The line from the founder (generation 0) to `end_id`, one row per
    organism, with the births.csv fields of its own birth (null for the
    founder)."""
    b = run.births
    child = b["child"].to_numpy()
    executor = b["executor"].to_numpy()
    chain = []  # births row index per organism, end first
    cur = end_id
    seen = set()
    while True:
        k = int(np.searchsorted(child, cur))
        if k >= len(child) or child[k] != cur:
            break
        if cur in seen:
            raise RuntimeError(f"cycle in births at id {cur}")
        seen.add(cur)
        chain.append(k)
        cur = int(executor[k])
    founder_id = cur
    f = run.founders.filter(pl.col("id") == founder_id)
    if f.height == 0:
        raise NoLine(f"id {founder_id} has no births row and is not a founder (parent 0) in orgs.csv")
    fr = f.row(0, named=True)
    ints = ("id", "birth_tick", "executor", "source", "copy_errors", "slips")
    schema = {c: (pl.Int64 if c in ints else pl.Utf8) for c in (
        "id", "birth_tick", "raw_hash", "executor", "source", "copy_errors", "slips",
        "parent_hash", "parent_now_hash", "source_hash")}
    founder = pl.DataFrame([{"id": founder_id, "birth_tick": fr["birth_tick"], "raw_hash": fr["birth_hash"]}],
                           schema=schema)
    rows = b[list(reversed(chain))] if chain else b.clear()
    rows = rows.rename({"child": "id", "tick": "birth_tick"}).select(
        pl.col(c).cast(t) for c, t in schema.items())
    line = pl.concat([founder, rows]).with_row_index("generation").with_columns(pl.col("generation").cast(pl.Int64))
    return line.join(run.genomes.select("raw_hash", "func_hash", "len", "bytes_hex"), on="raw_hash",
                     how="left", maintain_order="left")


def world_fitness(run: RunData, pairs: set[tuple[str, int]], size: int = WINDOW) -> dict[tuple[str, int], dict]:
    """(raw_hash, window) -> {born, died, exact_per_death, age_med} over
    organisms born with that genome in that window (module docstring)."""
    if not pairs:
        return {}
    b = run.births.select("tick", "child", "executor", "raw_hash")
    birth_hash = pl.concat([
        b.select(pl.col("child").cast(pl.Int64).alias("executor"), pl.col("raw_hash").alias("exec_hash")),
        run.founders.select(pl.col("id").cast(pl.Int64).alias("executor"), pl.col("birth_hash").alias("exec_hash")),
    ])
    exact = (
        b.with_columns(pl.col("executor").cast(pl.Int64))
        .join(birth_hash, on="executor", how="inner")
        .filter(pl.col("raw_hash") == pl.col("exec_hash"))
        .group_by("executor").agg(exact=pl.len())
        .rename({"executor": "id"})
    )
    hashes = sorted({h for h, _ in pairs})
    born = pl.concat([
        b.filter(pl.col("raw_hash").is_in(hashes)).select(
            pl.col("child").cast(pl.Int64).alias("id"), pl.col("tick").cast(pl.Int64), "raw_hash"),
        run.founders.filter(pl.col("birth_hash").is_in(hashes)).select(
            pl.col("id").cast(pl.Int64), pl.col("birth_tick").cast(pl.Int64).alias("tick"),
            pl.col("birth_hash").alias("raw_hash")),
    ]).with_columns(win=pl.max_horizontal(pl.lit(1), (pl.col("tick") + size - 1) // size).cast(pl.Int64))
    want = pl.DataFrame(sorted(pairs), schema={"raw_hash": pl.Utf8, "win": pl.Int64}, orient="row")
    born = born.join(want, on=["raw_hash", "win"], how="inner")
    dead = run.deaths.select(pl.col("id").cast(pl.Int64), pl.col("age").cast(pl.Int64))
    born = born.join(dead, on="id", how="left").join(exact, on="id", how="left").with_columns(
        pl.col("exact").fill_null(0))
    agg = born.group_by("raw_hash", "win").agg(
        born=pl.len(),
        died=pl.col("age").is_not_null().sum(),
        exact_dead=pl.col("exact").filter(pl.col("age").is_not_null()).sum(),
        age_med=pl.col("age").median(),
    )
    out = {}
    for r in agg.iter_rows(named=True):
        out[(r["raw_hash"], r["win"])] = {
            "born": r["born"],
            "died": r["died"],
            "exact_per_death": r["exact_dead"] / r["died"] if r["died"] else None,
            "age_med": r["age_med"],
        }
    empty = {"born": 0, "died": 0, "exact_per_death": None, "age_med": None}
    return {p: out.get(p, empty) for p in pairs}


def effect(fp: int, fc: int) -> str:
    if fc > fp + 1:
        return "beneficial"
    if fc < fp - 1:
        return "deleterious"
    return "neutral"


@dataclass
class Result:
    run_dir: Path
    out: Path
    at: int
    pick: Pick
    line: pl.DataFrame
    genomes: pl.DataFrame
    steps: pl.DataFrame
    absorb: dict
    seconds: float
    harness_ticks: int
    exe: str


def lod(run_dir: str | Path, at: int | None = None, pick: str = "top", harness_ticks: int = 3000,
        out: str | Path | None = None, exe: str | Path | None = None, run: RunData | None = None,
        jobs: int = 8, log=print) -> Result:
    """Draw the line, measure it, write the files. Raises NoLine when there
    is nothing to draw."""
    t0 = time.time()
    run_dir = Path(run_dir)
    exe_path = exe if isinstance(exe, Path) else evo_bin(exe)
    run = run or load_run(run_dir)
    if not run.census_ticks:
        raise NoLine("no census rows")
    if at is None:
        at = run.census_ticks[-1]
    elif at not in run.census_ticks:
        last = run.census_ticks[-1]
        if at > last:
            raise NoLine(f"run ends at tick {last}; no census at {at}")
        raise NoLine(f"tick {at} is not a census tick")
    cache: dict[str, dict] = {}
    p = pick_end(run, at, pick, exe_path, harness_ticks, cache)
    line = walk_back(run, p.end_id)
    if line["bytes_hex"].null_count():
        raise RuntimeError("a line genome is missing from genomes.csv")
    log(f"lod: {run_dir}: end organism {p.end_id} at tick {at}, line of {line.height} organisms "
        f"({time.time() - t0:.1f} s)")

    # Distinct genomes, in order of first appearance on the line.
    first = line.unique("raw_hash", keep="first", maintain_order=True)
    hexes = dict(first.select("raw_hash", "bytes_hex").iter_rows())
    alone = {h: cache[h] for h in hexes if h in cache}
    alone.update(harness_alone(exe_path, {h: x for h, x in hexes.items() if h not in alone}, harness_ticks))
    with ThreadPoolExecutor(jobs) as pool:
        entered = dict(zip(hexes, pool.map(lambda x: harness_entered(exe_path, x, harness_ticks), hexes.values())))

    # Steps.
    L = line.rows(named=True)
    step_rows = []
    for i in range(1, len(L)):
        par, ch = L[i - 1], L[i]
        if par["raw_hash"] == ch["raw_hash"]:
            continue
        a, b = bytes.fromhex(par["bytes_hex"]), bytes.fromhex(ch["bytes_hex"])
        ops = edit_script(a, b)
        p_now = ch["parent_now_hash"]
        somatic = p_now != par["raw_hash"]
        inherited = ch["raw_hash"] == p_now
        origin = "somatic" if (somatic and inherited) else ("somatic+copy" if somatic else "copy")
        fp, fc = alone[par["raw_hash"]]["exact_births"], alone[ch["raw_hash"]]["exact_births"]
        step_rows.append({
            "step": len(step_rows) + 1,
            "generation": ch["generation"],
            "tick": ch["birth_tick"],
            "window": window_of(ch["birth_tick"]),
            "parent_id": par["id"],
            "child_id": ch["id"],
            "parent_hash": par["raw_hash"],
            "child_hash": ch["raw_hash"],
            "synonymous": par["func_hash"] == ch["func_hash"],
            "kind": step_kind(ops),
            "n_edits": len(ops),
            "positions": ";".join(str(o[1]) for o in ops),
            "edits": format_edits(ops),
            "parent_len": len(a),
            "child_len": len(b),
            "origin": origin,
            "parent_now_hash": p_now,
            "copy_errors": ch["copy_errors"],
            "slips": ch["slips"],
            "source_is_executor": ch["source"] == ch["executor"],
            "absorb_parent": absorb_count(a),
            "absorb_child": absorb_count(b),
            "f_parent": fp,
            "f_child": fc,
            "df": fc - fp,
            "effect": effect(fp, fc),
            "entered_parent": entered[par["raw_hash"]]["host_exact"],
            "entered_child": entered[ch["raw_hash"]]["host_exact"],
            "entered_alive_parent": entered[par["raw_hash"]]["host_alive"],
            "entered_alive_child": entered[ch["raw_hash"]]["host_alive"],
            "entered_stopped_parent": entered[par["raw_hash"]]["stopped_early"],
            "entered_stopped_child": entered[ch["raw_hash"]]["stopped_early"],
        })

    # World fitness.
    first_win = {r["raw_hash"]: window_of(r["birth_tick"]) for r in first.iter_rows(named=True)}
    pairs = {(h, w) for h, w in first_win.items()}
    for s in step_rows:
        pairs.add((s["parent_hash"], s["window"]))
        pairs.add((s["child_hash"], s["window"]))
    world = world_fitness(run, pairs)
    for s in step_rows:
        for side, h in (("parent", s["parent_hash"]), ("child", s["child_hash"])):
            w = world[(h, s["window"])]
            s[f"world_born_{side}"] = w["born"]
            s[f"world_died_{side}"] = w["died"]
            s[f"world_exact_per_death_{side}"] = w["exact_per_death"]
            s[f"world_age_med_{side}"] = w["age_med"]

    gen_rows = []
    counts = line.group_by("raw_hash").len()
    n_on_line = dict(counts.iter_rows())
    disasm = dict(run.genomes.select("raw_hash", "disasm").iter_rows())
    for r in first.iter_rows(named=True):
        h = r["raw_hash"]
        body = bytes.fromhex(r["bytes_hex"])
        found, pat = absorb_pattern(body)
        al, en, w = alone[h], entered[h], world[(h, first_win[h])]
        gen_rows.append({
            "order": len(gen_rows),
            "raw_hash": h,
            "func_hash": r["func_hash"],
            "len": len(body),
            "first_generation": r["generation"],
            "first_tick": r["birth_tick"],
            "organisms_on_line": n_on_line[h],
            "absorb_byte": absorb_byte(body),
            "absorb_pat": pat if found else None,
            "absorb": absorb_count(body),
            "alone_class": al["class"],
            "alone_births": al["births"],
            "alone_exact": al["exact_births"],
            "alone_first_birth_tick": al["first_birth_tick"],
            "alone_alive": al["alive"],
            "entered_host_exact": en["host_exact"],
            "entered_host_alive": en["host_alive"],
            "entered_pad_exact": en["pad_exact"],
            "entered_ticks_run": en["ticks_run"],
            "entered_stopped_early": en["stopped_early"],
            "world_window": first_win[h],
            "world_born": w["born"],
            "world_died": w["died"],
            "world_exact_per_death": w["exact_per_death"],
            "world_age_med": w["age_med"],
            "bytes_hex": r["bytes_hex"],
            "disasm": disasm.get(h),
        })

    step_schema = {
        "step": pl.Int64, "generation": pl.Int64, "tick": pl.Int64, "window": pl.Int64, "parent_id": pl.Int64,
        "child_id": pl.Int64, "parent_hash": pl.Utf8, "child_hash": pl.Utf8, "synonymous": pl.Boolean,
        "kind": pl.Utf8, "n_edits": pl.Int64, "positions": pl.Utf8, "edits": pl.Utf8, "parent_len": pl.Int64,
        "child_len": pl.Int64, "origin": pl.Utf8, "parent_now_hash": pl.Utf8, "copy_errors": pl.Int64,
        "slips": pl.Int64, "source_is_executor": pl.Boolean, "absorb_parent": pl.Int64,
        "absorb_child": pl.Int64, "f_parent": pl.Int64, "f_child": pl.Int64, "df": pl.Int64,
        "effect": pl.Utf8, "entered_parent": pl.Int64, "entered_child": pl.Int64,
        "entered_alive_parent": pl.Boolean, "entered_alive_child": pl.Boolean,
        "entered_stopped_parent": pl.Boolean, "entered_stopped_child": pl.Boolean,
        **{f"world_{k}_{side}": t for side in ("parent", "child")
           for k, t in (("born", pl.Int64), ("died", pl.Int64), ("exact_per_death", pl.Float64),
                        ("age_med", pl.Float64))},
    }
    steps = pl.DataFrame(step_rows, schema=step_schema, orient="row") if step_rows else pl.DataFrame(schema=step_schema)
    genomes = pl.DataFrame(gen_rows, infer_schema_length=None)

    absorb = absorb_summary(steps, genomes)
    out_dir = Path(out) if out else run_dir / "lod"
    out_dir.mkdir(parents=True, exist_ok=True)
    line.select("generation", "id", "birth_tick", "raw_hash", "func_hash", "len", "executor", "parent_now_hash",
                "copy_errors", "slips", "bytes_hex").write_csv(out_dir / "line.csv")
    steps.write_csv(out_dir / "steps.csv")
    genomes.write_csv(out_dir / "genomes.csv")
    res = Result(run_dir, out_dir, at, p, line, genomes, steps, absorb, time.time() - t0, harness_ticks,
                 str(exe_path))
    (out_dir / "summary.md").write_text(summary_md(res) + "\n", encoding="utf-8", newline="\n")
    log(f"lod: wrote {out_dir} ({res.seconds:.1f} s)")
    return res


def _ge(v: int | None, t: int) -> bool:
    return v is not None and v >= t


def absorb_summary(steps: pl.DataFrame, genomes: pl.DataFrame) -> dict:
    """Two absorb steps, each with the effect of the step immediately before
    it and the three steps before it:
    - `final_step`: the spec's absorb-count step, the first step whose child
      has the end genome's absorb count and whose parent does not; `held` if
      the count never leaves that value afterwards.
    - `sweep_step`: the first step whose child reaches traits.ABSORB's
      threshold (96, E007's sweep measure) from below; `held` if the count
      stays at or above it afterwards. On E007 lines the final count is set
      by drift on the flat 112-127 plateau, long after the sweep, so the
      two differ.
    Also every step that changed the count, how many raised it, and how many
    of those immediately follow a deleterious step."""
    final = genomes["absorb"][-1] if genomes.height else None
    start = genomes["absorb"][0] if genomes.height else None
    thr = ABSORB.threshold
    S = steps.rows(named=True)

    def ctx(k: int | None, held: bool) -> dict:
        if k is None:
            return {"index": None, "held": False, "prev_effect": None, "before": []}
        return {"index": k, "held": held, "prev_effect": S[k - 1]["effect"] if k > 0 else None,
                "before": S[max(0, k - 3):k]}

    kf = next((i for i, s in enumerate(S) if s["absorb_child"] == final and s["absorb_parent"] != final), None)
    ks = next((i for i, s in enumerate(S) if _ge(s["absorb_child"], thr) and not _ge(s["absorb_parent"], thr)),
              None)
    changes = [i for i, s in enumerate(S) if s["absorb_child"] != s["absorb_parent"]]
    raises = [i for i in changes if (S[i]["absorb_child"] or 0) > (S[i]["absorb_parent"] or 0)]
    return {
        "start": start,
        "final": final,
        "threshold": thr,
        "final_step": ctx(kf, kf is not None and all(s["absorb_child"] == final for s in S[kf:])),
        "sweep_step": ctx(ks, ks is not None and all(_ge(s["absorb_child"], thr) for s in S[ks:])),
        "changes": changes,
        "raises": len(raises),
        "raises_after_deleterious": sum(1 for i in raises if i > 0 and S[i - 1]["effect"] == "deleterious"),
    }


# --- summary -----------------------------------------------------------------


def _f(v, nd=2) -> str:
    if v is None:
        return "–"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return f"{v:,}" if isinstance(v, int) and not isinstance(v, bool) else str(v)


def counts(steps: pl.DataFrame) -> dict:
    """Effect counts, synonymous steps, the order string, and the
    deleterious steps to a genome with no exact children alone (`to_zero`)
    and the beneficial steps from one (`from_zero`)."""
    c = {e: int((steps["effect"] == e).sum()) for e in ("beneficial", "neutral", "deleterious")}
    c["total"] = steps.height
    c["synonymous"] = int(steps["synonymous"].sum()) if steps.height else 0
    c["order"] = "".join(EFFECT_LETTER[e] for e in steps["effect"].to_list())
    c["to_zero"] = int(((steps["effect"] == "deleterious") & (steps["f_child"] == 0)).sum())
    c["from_zero"] = int(((steps["effect"] == "beneficial") & (steps["f_parent"] == 0)).sum())
    return c


STOPPED_NOTE = ("`*` after an entered count: the pad died and the harness stopped early, so the host's count "
                "covers only the ticks run (E007: a host endowment of about 35 or more starves a one-byte pad "
                "at its first division).")


def _entered(n: int, stopped: bool) -> str:
    return f"{n}*" if stopped else str(n)


def step_table(rows: list[dict]) -> list[str]:
    out = [
        "| step | gen | tick | kind | edits | syn. | origin | absorb | alone f(p) → f(c) | effect "
        "| entered host exact p → c | world exact/death p → c | world median age p → c | world born p → c |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in rows:
        ab = (f"{_f(s['absorb_parent'])} → {_f(s['absorb_child'])}"
              if s["absorb_parent"] != s["absorb_child"] else _f(s["absorb_child"]))
        out.append(
            f"| {s['step']} | {s['generation']} | {s['tick']:,} | {s['kind']} | `{s['edits']}` "
            f"| {'yes' if s['synonymous'] else 'no'} | {s['origin']} | {ab} "
            f"| {s['f_parent']} → {s['f_child']} | {s['effect']} "
            f"| {_entered(s['entered_parent'], s['entered_stopped_parent'])} → "
            f"{_entered(s['entered_child'], s['entered_stopped_child'])} "
            f"| {_f(s['world_exact_per_death_parent'])} → {_f(s['world_exact_per_death_child'])} "
            f"| {_f(s['world_age_med_parent'], 0)} → {_f(s['world_age_med_child'], 0)} "
            f"| {s['world_born_parent']} → {s['world_born_child']} |"
        )
    return out


def summary_md(r: Result) -> str:
    c = counts(r.steps)
    a = r.absorb
    p = r.pick
    end = r.line.row(-1, named=True)
    g0 = r.genomes.row(0, named=True)
    S = r.steps.rows(named=True)
    try:
        shown = r.run_dir.resolve().relative_to(evo_run.ROOT).as_posix()
    except ValueError:
        shown = r.run_dir.as_posix()
    lines = [
        f"# Line of descent: {shown}",
        "",
        f"End organism {p.end_id} at tick {r.at:,}"
        + (f": func_hash {p.func_hash}, {p.group_size} living bodies (the largest replicator-class group), "
           f"{p.offspring} offspring" if p.func_hash else " (named with --pick)")
        + f"; born tick {end['birth_tick']:,}, generation {end['generation']}.",
    ]
    if p.skipped:
        lines.append("Larger groups passed over (not replicator): "
                     + ", ".join(f"{h} ({n} bodies, {cl})" for h, n, cl in p.skipped) + ".")
    lines += [
        f"Founder {r.line['id'][0]} ({g0['raw_hash']}). Line: {r.line.height} organisms, "
        f"{r.genomes.height} distinct genomes. Harness: {r.harness_ticks:,} quiet ticks, `{r.exe}`.",
        "",
        f"Steps: {c['total']} ({c['synonymous']} synonymous): beneficial {c['beneficial']}, "
        f"neutral {c['neutral']}, deleterious {c['deleterious']} "
        "(alone exact children, ±1 counted neutral). "
        f"Deleterious steps to a genome with no exact children alone: {c['to_zero']}; beneficial steps "
        f"from one: {c['from_zero']}.",
        f"Order (B beneficial, n neutral, D deleterious): `{c['order'] or '–'}`",
        "",
        f"Founder alone: {g0['alone_exact']} exact children ({g0['alone_class']}), entered host exact "
        f"{_entered(g0['entered_host_exact'], g0['entered_stopped_early'])}, absorb count {_f(g0['absorb'])}. "
        f"End genome alone: {r.genomes['alone_exact'][-1]} ({r.genomes['alone_class'][-1]}), entered "
        f"{_entered(r.genomes['entered_host_exact'][-1], r.genomes['entered_stopped_early'][-1])}, "
        f"absorb count {_f(a['final'])}. {STOPPED_NOTE}",
        "",
    ]
    lines.append(
        f"Absorb count {_f(a['start'])} at the founder, {_f(a['final'])} at the end. Steps that changed it: "
        f"{len(a['changes'])}; that raised it: {a['raises']}, of which {a['raises_after_deleterious']} "
        "immediately follow a deleterious step.")
    for key, name, what in (
        ("final_step", "Absorb-count step (the spec's)", f"first step into the final count {_f(a['final'])}"),
        ("sweep_step", "Sweep step", f"first step to an absorb count of {a['threshold']} or more"),
    ):
        x = a[key]
        if x["index"] is None:
            lines += ["", f"{name}: none ({what}: no such step on this line)."]
            continue
        s = S[x["index"]]
        held = ("held to the end" if x["held"] else "left and regained later") if key == "final_step" else (
            f"stayed at {a['threshold']} or more" if x["held"] else
            f"a later genome on the line is below {a['threshold']} or has no absorb loop")
        lines += [
            "",
            f"{name}, {what}: step {s['step']} (generation {s['generation']}, tick {s['tick']:,}), "
            f"{_f(s['absorb_parent'])} → {_f(s['absorb_child'])}, {held}; effect {s['effect']} "
            f"(alone {s['f_parent']} → {s['f_child']}). Step immediately before: {x['prev_effect'] or 'none'}. "
            "With the three steps before it:",
            "",
            *step_table(x["before"] + [s]),
        ]
    if a["changes"]:
        lines += ["", "Every step that changed the absorb count:", "", *step_table([S[i] for i in a["changes"]])]
    lines += ["", "Fitness series, every step:", "", *step_table(S)]
    lines += [
        "",
        "Caveat: harness fitness is with a full pool and no neighbours; the longer absorb phase pays on a "
        "lower ration (E007 break-even), which the harness cannot see, so a neutral harness step may be the "
        "beneficial one in the world. The world columns are the check, and they are per window of 25,000 "
        "ticks over every organism born with the genome, not along the line.",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir")
    ap.add_argument("--at", type=int, help="census tick (default: the last census)")
    ap.add_argument("--pick", default="top", help="top (default) or id:N")
    ap.add_argument("--harness-ticks", type=int, default=3000)
    ap.add_argument("--out", help="output directory (default RUN_DIR/lod)")
    ap.add_argument("--evo-bin", help="evo-core binary (default $EVO_BIN, else build with cargo)")
    ap.add_argument("--jobs", type=int, default=8, help="parallel --host harness calls")
    a = ap.parse_args()
    try:
        r = lod(a.run_dir, a.at, a.pick, a.harness_ticks, a.out, a.evo_bin, jobs=a.jobs)
    except NoLine as e:
        print(f"lod: {a.run_dir}: {e}", file=sys.stderr)
        sys.exit(1)
    print(summary_md(r).split("\n\nEvery step that changed")[0])


if __name__ == "__main__":
    main()
