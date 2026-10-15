"""B0 / T07: replicator density by uniform sampling (docs/tasks/T07-density.md §2).

Runs `evo-core --density LEN:N` on every cell of §2 and writes
`runs/b0/density.csv` (one row per cell and seed: the class counts and the
wall time) and `runs/b0/summary.md`: per cell the `replicator` count, the
point estimate and the Clopper-Pearson 95% interval, the same for
`one_shot + replicator` (Dusek's test counts a tape that makes one copy),
the hex of every body in either class, and §3's decision line, against
BFF's 7.1e-11 per 64-byte tape.

Cells (§2): LEN in {8, 12, 16, 21, 24, 32, 45, 64} at N = 10^6, T = 1,000
harness ticks; LEN 21 also at T = 3,000; then LEN <= 16 at N = 10^7 if the
10^6 pass (every N = 10^6 cell) took under 10 minutes of wall time. Seeds
1 and 2 for every cell, two independent samples. The first 10^6 bodies of
a 10^7 cell are its seed's 10^6 cell (`--density` draws body i from the
same place in the PRNG stream at any N), so the headline per length uses
the largest N per seed and pools the two seeds.

    uv run --project analysis analysis/b0_density.py run [--threads K]
    uv run --project analysis analysis/b0_density.py summary
    uv run --project analysis analysis/b0_density.py run --smoke

`--smoke` divides both N by 100 (10^4 and 10^5) and writes to
runs/b0_smoke unless `--out` says otherwise. `--big-max-len 32`
extends the 10^7 pass to every LEN <= 32, which §3's second bullet reads
("zero hits at 10^7 for every LEN <= 32"); §2 runs it to 16 only, the
default. Each cell's kept bodies (`--density-out`: every body that is
neither `dies` nor `loafer`) are in OUT/cells/L<len>_T<ticks>_N<n>_s<seed>.csv.
Resumable: a cell already in density.csv with its cell file is not rerun
without `--force`. `--threads` defaults to 12 when other evo-core
processes are running, else to the machine's parallelism. The binary is
`--evo-bin`, else $EVO_BIN, else evo-core/target/release (not built here).
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "b0"
LENS = (8, 12, 16, 21, 24, 32, 45, 64)
SEEDS = (1, 2)
N_MAIN, N_BIG = 10**6, 10**7
T_MAIN, T_LONG = 1000, 3000
BIG_MAX_LEN = 16
BIG_IF_UNDER_S = 600.0  # §2: the 10^7 pass runs if the 10^6 pass took under 10 minutes
BFF = 7.1e-11  # Dusek et al. 2026, uniform sampling, per 64-byte tape
ALPHA = 0.05
CLASSES = ("replicator", "one_shot", "inexact", "loafer", "dies")
COLS = ("len", "n", "ticks", "seed", *CLASSES, "seconds", "threads")
SUMMARY_HEADER = "len,n,ticks,replicator,one_shot,inexact,loafer,dies,seconds"


@dataclass(frozen=True, order=True)
class Cell:
    len: int
    ticks: int
    n: int
    seed: int

    @property
    def name(self) -> str:
        return f"L{self.len}_T{self.ticks}_N{self.n}_s{self.seed}"


def main_cells(n: int = N_MAIN, lens=LENS, seeds=SEEDS) -> list[Cell]:
    """The 10^6 pass: every LEN at T = 1,000, and LEN 21 at T = 3,000."""
    cells = [Cell(L, T_MAIN, n, s) for L in lens for s in seeds]
    if 21 in lens:
        cells += [Cell(21, T_LONG, n, s) for s in seeds]
    return cells


def big_cells(n: int = N_BIG, max_len: int = BIG_MAX_LEN, lens=LENS, seeds=SEEDS) -> list[Cell]:
    """The 10^7 pass: LEN <= max_len at T = 1,000."""
    return [Cell(L, T_MAIN, n, s) for L in lens if L <= max_len for s in seeds]


# ---- Clopper-Pearson ------------------------------------------------------------------

def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta (modified Lentz; Numerical
    Recipes 6.4). Converges in O(sqrt(max(a, b))) terms for x < (a+1)/(a+b+2)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 100_000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            return h
    raise ArithmeticError(f"betacf did not converge (a={a}, b={b}, x={x})")


def betainc(a: float, b: float, x: float) -> float:
    """The regularized incomplete beta I_x(a, b), a, b > 0."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbt) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbt) * _betacf(b, a, 1.0 - x) / b


def beta_ppf(q: float, a: float, b: float) -> float:
    """The q-quantile of Beta(a, b), by bisection on `betainc` (200 halvings
    of [0, 1], so absolute error below 1e-60; the CDF is monotone)."""
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mid in (lo, hi):
            break
        if betainc(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def clopper_pearson(k: int, n: int, alpha: float = ALPHA) -> tuple[float, float]:
    """The exact (Clopper-Pearson) 1 - alpha interval for k hits in n, in
    the beta-quantile form: lower Beta(alpha/2; k, n-k+1), upper
    Beta(1-alpha/2; k+1, n-k). With k = 0 the upper bound is
    1 - (alpha/2)^(1/n), about 3.7 / n at alpha 0.05."""
    if not 0 <= k <= n or n < 1:
        raise ValueError(f"k={k}, n={n}")
    lo = 0.0 if k == 0 else beta_ppf(alpha / 2, k, n - k + 1)
    if k == n:
        hi = 1.0
    elif k == 0:
        hi = -math.expm1(math.log(alpha / 2) / n)
    else:
        hi = beta_ppf(1 - alpha / 2, k + 1, n - k)
    return lo, hi


# ---- running -----------------------------------------------------------------------

def evo_bin(path: str | None) -> Path:
    p = path or os.environ.get("EVO_BIN")
    if p:
        p = Path(p).resolve()
    else:
        rel = ROOT / "evo-core" / "target" / "release"
        p = next((rel / x for x in ("evo-core.exe", "evo-core") if (rel / x).exists()), rel / "evo-core.exe")
    if not p.exists():
        raise SystemExit(f"evo-core binary not found: {p} (give --evo-bin or EVO_BIN)")
    return p


def check_binary(exe: Path) -> None:
    """The binary must accept --density (T07) and print its summary header."""
    r = subprocess.run([str(exe), "--density", "1:1", "--density-ticks", "1", "--threads", "1"],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.startswith(SUMMARY_HEADER):
        msg = (r.stderr + r.stdout).strip().splitlines()
        raise SystemExit(f"{exe} does not run --density (T07 not built?): exit {r.returncode}: "
                         f"{msg[-1] if msg else ''}")


def threads_default() -> int:
    """12 when other evo-core processes run, else all cores."""
    try:
        busy = "evo-core" in subprocess.run(["tasklist"], capture_output=True, text=True).stdout
    except OSError:
        busy = False
    return 12 if busy else (os.cpu_count() or 8)


def parse_summary(stdout: str) -> dict:
    lines = stdout.strip().splitlines()
    if len(lines) < 2 or lines[0] != SUMMARY_HEADER:
        raise ValueError(f"unexpected --density output: {stdout!r}")
    vals = lines[1].split(",")
    row = dict(zip(SUMMARY_HEADER.split(","), vals))
    return {k: (float(v) if k == "seconds" else int(v)) for k, v in row.items()}


def run_cell(exe: Path, cell: Cell, out: Path, threads: int) -> dict:
    dst = out / "cells" / f"{cell.name}.csv"
    cmd = [str(exe), "--density", f"{cell.len}:{cell.n}", "--density-ticks", str(cell.ticks),
           "--seed", str(cell.seed), "--threads", str(threads), "--density-out", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"{' '.join(cmd)}: exit {r.returncode}\n{r.stderr}")
    s = parse_summary(r.stdout)
    if (s["len"], s["n"], s["ticks"]) != (cell.len, cell.n, cell.ticks):
        raise SystemExit(f"{cell.name}: the binary reports {s}")
    return {**s, "seed": cell.seed, "threads": threads}


def load_rows(out: Path) -> dict[Cell, dict]:
    p = out / "density.csv"
    if not p.exists():
        return {}
    rows = {}
    with open(p, newline="") as f:
        for r in csv.DictReader(f):
            row = {k: (float(v) if k == "seconds" else int(v)) for k, v in r.items()}
            rows[Cell(row["len"], row["ticks"], row["n"], row["seed"])] = row
    return rows


def write_rows(out: Path, rows: dict[Cell, dict]) -> None:
    tmp = out / "density.csv.tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLS)
        for c in sorted(rows):
            w.writerow([rows[c][k] for k in COLS])
    os.replace(tmp, out / "density.csv")


def run(exe: Path, out: Path, threads: int, n_main: int, n_big: int, big_max_len: int, force: bool) -> None:
    (out / "cells").mkdir(parents=True, exist_ok=True)
    rows = load_rows(out)

    def do(cells: list[Cell]) -> None:
        for c in cells:
            if c in rows and (out / "cells" / f"{c.name}.csv").exists() and not force:
                print(f"{c.name}: done", flush=True)
                continue
            rows[c] = run_cell(exe, c, out, threads)
            write_rows(out, rows)
            r = rows[c]
            print(f"{c.name}: replicator {r['replicator']} one_shot {r['one_shot']} inexact {r['inexact']} "
                  f"loafer {r['loafer']} dies {r['dies']} in {r['seconds']:.2f}s", flush=True)

    main = main_cells(n_main)
    do(main)
    pass_s = sum(rows[c]["seconds"] for c in main)
    if pass_s < BIG_IF_UNDER_S:
        print(f"N = {n_main:,} pass {pass_s:.1f}s < {BIG_IF_UNDER_S:.0f}s: running N = {n_big:,} for LEN <= "
              f"{big_max_len}", flush=True)
        do(big_cells(n_big, big_max_len))
    else:
        print(f"N = {n_main:,} pass {pass_s:.1f}s >= {BIG_IF_UNDER_S:.0f}s: no N = {n_big:,} pass (§2)", flush=True)
    write_summary(out, rows, exe)


# ---- summary -----------------------------------------------------------------------

def sci(x: float) -> str:
    return "0" if x == 0 else f"{x:.2e}"


def headline(rows: dict[Cell, dict]) -> list[dict]:
    """Per (LEN, T): the largest-N cell of each seed, pooled over seeds."""
    best: dict[tuple[int, int, int], Cell] = {}
    for c in rows:
        key = (c.len, c.ticks, c.seed)
        if key not in best or c.n > best[key].n:
            best[key] = c
    out = []
    for L, T in sorted({(c.len, c.ticks) for c in rows}):
        cells = [best[k] for k in sorted(best) if k[:2] == (L, T)]
        n = sum(c.n for c in cells)
        rep = sum(rows[c]["replicator"] for c in cells)
        cop = rep + sum(rows[c]["one_shot"] for c in cells)
        out.append({"len": L, "ticks": T, "cells": cells, "n": n, "n_per_seed": sorted({c.n for c in cells}),
                    "seeds": [c.seed for c in cells], "rep": rep, "copy": cop})
    return out


def hits(out: Path, cells: list[Cell]) -> list[dict]:
    """Every `replicator` and `one_shot` body in the given cells' files."""
    found = []
    for c in cells:
        p = out / "cells" / f"{c.name}.csv"
        if not p.exists():
            continue
        with open(p, newline="") as f:
            for r in csv.DictReader(f):
                if r["class"] in ("replicator", "one_shot"):
                    found.append({"cell": c, **r})
    return found


def decision(head: list[dict]) -> list[str]:
    """§3's decision, bullet by bullet, from the T = 1,000 headline rows.
    Bullet 1 ("within two orders of BFF") is read one-sided, as "not more
    than two orders below": a hit at these N is orders above BFF's level."""
    main = [h for h in head if h["ticks"] == T_MAIN]
    lines = []
    decided = False  # bullet 1 or bullet 2 met
    short = [h for h in main if h["len"] <= 12 and h["rep"] > 0]
    if short:
        lens = ", ".join(str(h["len"]) for h in short)
        lines.append(f"- **§3 bullet 3 met**: a replicator at LEN {lens} (<= 12), shorter than the 21-byte "
                     "ancestor. Its hex is below; classify its neighbourhood (T03 `--neighbours`).")
    for h in (h for h in main if h["len"] in (21, 24)):
        if h["rep"] > 0:
            p = h["rep"] / h["n"]
            orders = math.log10(p / BFF)
            if orders >= -2:
                decided = True
                lines.append(f"- **§3 bullet 1 met** at LEN {h['len']}: density {sci(p)}, {orders:+.1f} orders "
                             "from BFF's: seedless emergence on the ring is worth trying (B3's soup mode, H7's "
                             "start-execution rule).")
            elif orders <= -3:
                decided = True
                lines.append(f"- **§3 bullet 2 met** at LEN {h['len']}: density {sci(p)}, {orders:+.1f} orders "
                             "from BFF's.")
    upto32 = [h for h in main if h["len"] <= 32]
    if upto32 and all(h["rep"] == 0 and min(h["n_per_seed"]) >= N_BIG for h in upto32):
        decided = True
        lines.append("- **§3 bullet 2 met**: zero replicators at 10^7 per seed for every LEN <= 32: seedless "
                     "emergence on this ISA is out of reach without an ISA change; line B proceeds in the cubff "
                     "fork (B1, B2) with evo's rules rather than evo's ISA.")
    if not decided:
        missing = [h["len"] for h in upto32 if min(h["n_per_seed"]) < N_BIG]
        lines.append("- Neither the first nor the second bullet of §3 is met." + (
            f" The second's zero-hit clause needs 10^7 per seed at LEN {', '.join(map(str, missing))} "
            "(`--big-max-len 32`)." if missing else ""))
    zero = [h for h in upto32 if h["rep"] == 0]
    if zero:
        hi = min(clopper_pearson(0, h["n"])[1] for h in zero)
        lines.append(f"- Resolution: zero hits in n bodies bound the density at 1 - 0.025^(1/n), about 3.7 / n; "
                     f"the smallest such bound here (LEN <= 32) is {sci(hi)}, {math.log10(hi / BFF):.1f} orders "
                     f"above BFF's {BFF:.1e}. A zero count cannot show a density three orders below BFF's "
                     f"without n of about {3.7 / (BFF / 1000):.0e}.")
    return lines


def disasm(exe: Path | None, hx: str) -> str:
    if exe is None:
        return ""
    r = subprocess.run([str(exe), "--disasm", hx], capture_output=True, text=True)
    return r.stdout.strip().replace("\n", " ; ") if r.returncode == 0 else ""


def write_summary(out: Path, rows: dict[Cell, dict], exe: Path | None) -> str:
    head = headline(rows)
    md = ["# B0: replicator density by uniform sampling (T07)", "",
          "`analysis/b0_density.py`; spec `docs/tasks/T07-density.md`. Each body: LEN uniform random bytes, "
          "alone in the quiet harness (noise off, 100 units of seed energy, children removed every tick) for "
          "T ticks in an 8,192-byte ring of 16 patches of 512, default physics. Classes as `--classify`. "
          "Intervals are Clopper-Pearson 95% (beta-quantile form; zero hits: upper 1 - 0.025^(1/N)). "
          "`copy` = `one_shot` + `replicator`.", "",
          f"Comparison: BFF at {BFF:.1e} per 64-byte tape (Dusek et al. 2026, uniform sampling). The protocols "
          "differ: BFF's test is a tape-pair interaction over epochs, this one a body alone with energy and a "
          "per-tick execution cap, so the comparison is an order of magnitude at best.", "",
          "## Per length (largest N per seed, seeds pooled)", "",
          "| LEN | T | N | seeds | replicator | p | 95% CI | copy | p | 95% CI |",
          "|---:|---:|---:|---|---:|---:|---|---:|---:|---|"]
    for h in head:
        n = h["n"]
        rlo, rhi = clopper_pearson(h["rep"], n)
        clo, chi = clopper_pearson(h["copy"], n)
        md.append(f"| {h['len']} | {h['ticks']:,} | {n:,} | {','.join(map(str, h['seeds']))} | {h['rep']} | "
                  f"{sci(h['rep'] / n)} | [{sci(rlo)}, {sci(rhi)}] | {h['copy']} | {sci(h['copy'] / n)} | "
                  f"[{sci(clo)}, {sci(chi)}] |")
    md += ["", "## Decision (§3)", "", *decision(head), "",
           "## Every cell", "",
           "| LEN | T | N | seed | replicator | 95% CI | copy | 95% CI | inexact | loafer | dies | seconds | threads |",
           "|---:|---:|---:|---:|---:|---|---:|---|---:|---:|---:|---:|---:|"]
    for c in sorted(rows):
        r = rows[c]
        rlo, rhi = clopper_pearson(r["replicator"], c.n)
        cop = r["replicator"] + r["one_shot"]
        clo, chi = clopper_pearson(cop, c.n)
        md.append(f"| {c.len} | {c.ticks:,} | {c.n:,} | {c.seed} | {r['replicator']} | [{sci(rlo)}, {sci(rhi)}] | "
                  f"{cop} | [{sci(clo)}, {sci(chi)}] | {r['inexact']} | {r['loafer']} | {r['dies']} | "
                  f"{r['seconds']:.2f} | {r['threads']} |")
    found = hits(out, [c for h in head for c in h["cells"]])
    md += ["", "## Replicators and one-shots found", ""]
    if not found:
        md.append("None.")
    else:
        md += ["| LEN | T | seed | index | class | exact births | first birth | hex | disassembly |",
               "|---:|---:|---:|---:|---|---:|---:|---|---|"]
        for f in found:
            c = f["cell"]
            md.append(f"| {c.len} | {c.ticks:,} | {c.seed} | {f['index']} | {f['class']} | {f['exact_births']} | "
                      f"{f['first_birth_tick']} | `{f['hex']}` | `{disasm(exe, f['hex'])}` |")
    text = "\n".join(md) + "\n"
    with open(out / "summary.md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return text


# ---- main ----------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["run", "summary"])
    ap.add_argument("--evo-bin", help="evo-core binary (default $EVO_BIN, else evo-core/target/release; not built)")
    ap.add_argument("--out", type=Path, help="output directory (default runs/b0, with --smoke runs/b0_smoke)")
    ap.add_argument("--threads", type=int, help="--threads for evo-core --density (default: 12 if other "
                                                "evo-core processes run, else all cores)")
    ap.add_argument("--smoke", action="store_true", help="N / 100 (10^4 and 10^5)")
    ap.add_argument("--big-max-len", type=int, default=BIG_MAX_LEN,
                    help="the 10^7 pass covers LEN <= this (default 16, §2; 32 makes §3 bullet 2 decidable)")
    ap.add_argument("--force", action="store_true", help="rerun cells already done")
    a = ap.parse_args()
    out = (a.out or (OUT.parent / "b0_smoke" if a.smoke else OUT)).resolve()
    if a.stage == "summary":
        rows = load_rows(out)
        if not rows:
            raise SystemExit(f"{out / 'density.csv'}: no cells")
        try:
            exe = evo_bin(a.evo_bin)
        except SystemExit:
            exe = None
        print(write_summary(out, rows, exe))
        return
    exe = evo_bin(a.evo_bin)
    check_binary(exe)
    scale = 100 if a.smoke else 1
    run(exe, out, a.threads or threads_default(), N_MAIN // scale, N_BIG // scale, a.big_max_len, a.force)
    print(f"wrote {out / 'density.csv'} and {out / 'summary.md'}")


if __name__ == "__main__":
    sys.exit(main())
