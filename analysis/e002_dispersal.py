"""E002: dispersal arms. Runs every arm x seed, then summarizes.

Stdlib only, so plain `python` works too. Usage (from analysis/):

    uv run e002_dispersal.py                 # build, run, summarize
    uv run e002_dispersal.py --summarize-only
    uv run e002_dispersal.py --seeds 3 --ticks 10000   # quick look

Raw output goes to runs/e002/<arm>/s<seed>.csv (census lines from the CLI)
and .err (timing and top genotypes). The summary table is printed and
written to runs/e002/summary.md. Protocol and predictions:
docs/research/experiments/2026-10-01-e002-dispersal.md.
"""

import argparse
import csv
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "evo-core"
BIN = CORE / "target" / "release" / ("evo-core.exe" if sys.platform == "win32" else "evo-core")
OUT = ROOT / "runs" / "e002"

# Arm name -> extra CLI args. --patch keeps energy per byte constant.
ARMS = {
    "control": [],
    "p2048": ["--patch", "2048"],
    "p1024": ["--patch", "1024"],
    "p512": ["--patch", "512"],
    "far": ["--alloc-far"],
    "far_p1024": ["--alloc-far", "--patch", "1024"],
}

REPORT = 500
LATE_WINDOW = 5000  # "still replicating" = births in the last this-many ticks


def run_one(arm: str, seed: int, ticks: int) -> None:
    d = OUT / arm
    d.mkdir(parents=True, exist_ok=True)
    cmd = [str(BIN), "--ticks", str(ticks), "--report", str(REPORT), "--seed", str(seed), *ARMS[arm]]
    with open(d / f"s{seed}.csv", "w", newline="") as out, open(d / f"s{seed}.err", "w") as err:
        subprocess.run(cmd, stdout=out, stderr=err, check=True)


def load(path: Path):
    rows, extinct = [], None
    with open(path, newline="") as f:
        for line in f:
            if line.startswith("# extinct at tick"):
                extinct = int(line.split()[-1])
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(l for l in f if not l.startswith("#"))]
    for r in rows:
        for k in r:
            r[k] = float(r[k])
    return rows, extinct


def summarize_run(rows, extinct, ticks):
    if not rows:
        return dict(extinct=extinct, last_birth=0, births=0, alive=0.0, occ=0.0, active_frac=0.0, late=False)
    last_birth, prev = 0, 0.0
    for r in rows:
        if r["births"] > prev:
            last_birth = int(r["tick"])
        prev = r["births"]
    half = [r for r in rows if r["tick"] > ticks / 2]
    mean = lambda xs: statistics.fmean(xs) if xs else 0.0
    frac = [r["active"] / r["alive"] for r in half if r["alive"] > 0]
    return dict(
        extinct=extinct,
        last_birth=last_birth,
        births=int(rows[-1]["births"]),
        alive=mean([r["alive"] for r in half]),
        occ=mean([r["patches_occ"] for r in half]),
        active_frac=mean(frac),
        late=extinct is None and last_birth > ticks - LATE_WINDOW,
    )


def summarize(seeds: int, ticks: int) -> str:
    med = statistics.median
    lines = [
        f"E002 summary: {seeds} seeds x {ticks} ticks, report every {REPORT}. "
        f"Second-half means over ticks > {ticks // 2}; medians across seeds.",
        "",
        "| arm | extinct | still replicating | last birth tick | births | alive | patches occupied | active fraction |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for arm in ARMS:
        runs = []
        for s in range(1, seeds + 1):
            p = OUT / arm / f"s{s}.csv"
            if p.exists():
                runs.append(summarize_run(*load(p), ticks))
        if not runs:
            continue
        n = len(runs)
        lines.append(
            f"| {arm} | {sum(r['extinct'] is not None for r in runs)}/{n} "
            f"| {sum(r['late'] for r in runs)}/{n} "
            f"| {med([r['last_birth'] for r in runs]):.0f} "
            f"| {med([r['births'] for r in runs]):.0f} "
            f"| {med([r['alive'] for r in runs]):.1f} "
            f"| {med([r['occ'] for r in runs]):.1f} "
            f"| {med([r['active_frac'] for r in runs]):.2f} |"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=50_000)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--summarize-only", action="store_true")
    a = ap.parse_args()

    if not a.summarize_only:
        subprocess.run(["cargo", "build", "--release"], cwd=CORE, check=True)
        jobs = [(arm, s) for arm in ARMS for s in range(1, a.seeds + 1)]
        with ThreadPoolExecutor(a.jobs) as ex:
            for f in [ex.submit(run_one, arm, s, a.ticks) for arm, s in jobs]:
                f.result()

    text = summarize(a.seeds, a.ticks)
    (OUT / "summary.md").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
