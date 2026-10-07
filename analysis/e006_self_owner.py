"""E006: the `self` switch (H8). Runs the E004 standard world and the plain
p512_far world with `--self-owner` (`self` names the living owner of the
byte at IP instead of the executing organism), records and classifies each
run, then applies the E004 persistence metrics and the E005 parasite
analysis. Controls are the E004 runs of the same two worlds.

Usage (from analysis/):

    uv run e006_self_owner.py                  # build, run, classify, analyse
    uv run e006_self_owner.py --seeds 3 --arms owner_prop_rot

Run directories: runs/e006/<arm>/s<seed>/. Output: runs/e006/runs_e004.csv
and summary_e004.md (persistence, as E004), runs/e006/runs.csv and
summary.md (parasites, as E005). Protocol and predictions:
docs/research/experiments/2026-10-07-e006-self-owner.md.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

import e004_physics as e004
import e005_parasites as e005
from evo_run import ROOT, binary

OUT = ROOT / "runs" / "e006"
WORLD = ["--patch", "512", "--sun", "8", "--alloc-far"]
ARMS = {
    "owner_prop_rot": WORLD + ["--absorb-prop", "--rot", "1e-4", "--self-owner"],
    "owner": WORLD + ["--self-owner"],
}
# Harness flags per arm (noise flags are ignored by the harness).
HARNESS = {
    "owner_prop_rot": WORLD + ["--absorb-prop", "--self-owner"],
    "owner": WORLD + ["--self-owner"],
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=50_000)
    ap.add_argument("--jobs", type=int, default=20)
    ap.add_argument("--arms", nargs="*", default=list(ARMS))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    # Point the E004 runner at our arms and output root, then run as it did.
    e004.OUT = OUT
    e004.ARMS = ARMS
    if not a.analyse_only:
        exe = binary()
        jobs = [(arm, s) for arm in a.arms for s in range(1, a.seeds + 1)]
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda j: e004.run_one(exe, j[0], j[1], a.ticks, a.force), jobs):
                print(msg, flush=True)
    rows = [e004.metrics(arm, s, a.ticks) for arm in a.arms for s in range(1, a.seeds + 1)
            if (OUT / arm / f"s{s}" / "classes.csv").exists()]
    pl.DataFrame(rows).write_csv(OUT / "runs_e004.csv")
    text = e004.summarize(a.seeds, a.ticks, a.arms).replace("E004 summary", "E006 persistence (E004 measures)")
    (OUT / "summary_e004.md").write_text(text + "\n", encoding="utf-8")
    print(text)

    # Parasite analysis as in E005, on these runs.
    e005.RUNS = OUT
    e005.OUT = OUT
    e005.ARMS = HARNESS
    e005.run_all(a.arms, a.seeds, min(a.jobs, 8), host=True)


if __name__ == "__main__":
    main()
