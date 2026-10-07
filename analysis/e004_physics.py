"""E004: physics pass. Runs every arm x seed with recording, classifies each
run, then summarizes.

Usage (from analysis/):

    uv run e004_physics.py                     # build, run, classify, summarize
    uv run e004_physics.py --summarize-only
    uv run e004_physics.py --arms control p512_far --seeds 3

Run directories go to runs/e004/<arm>/s<seed>/ (docs/instrumentation.md);
finished runs are skipped unless --force. Per-run metrics are written to
runs/e004/runs.csv and the per-arm table to runs/e004/summary.md. Protocol
and predictions: docs/research/experiments/2026-10-05-e004-physics-pass.md.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

from evo_run import ROOT, binary, load
from report import births_typed, deaths_with_signature

OUT = ROOT / "runs" / "e004"
CENSUS = 500
LATE_WINDOW = 5000  # "replicating at the end" looks at the last this-many ticks

# World -> CLI args. Since 2026-10-07 the code default is the E004 world
# (128 patches of 512 bytes at 8x sun, far `alloc`, proportional absorb,
# bit rot 1e-4), so the arms are written as deviations from it:
# `--world-e001` is the Phase 1 control world, and the plain arms turn
# proportional absorb and bit rot 1e-4 off. Flags before 2026-10-07 were
# relative to the old default; meta.json in each run has the full config.
WORLDS = {
    "control": ["--world-e001"],
    "far": ["--world-e001", "--alloc-far"],
    "p512": ["--alloc-near"],
    "p512_far": [],
}
BASE = ["--absorb-fixed", "--rot", "1e-5"]  # the "plain" arm of each world
PROP = ["--rot", "1e-5"]
ROT = ["--absorb-fixed"]


def arms() -> dict[str, list[str]]:
    out = {}
    for w, args in WORLDS.items():
        for suffix, extra in [("", BASE), ("_prop", PROP), ("_rot", ROT), ("_prop_rot", [])]:
            name = (w + suffix) if w != "control" or not suffix else suffix[1:]
            out[name] = args + extra
    out["sun8"] = ["--world-e001", "--sun", "8", *BASE]
    # Added after the main results (post hoc): 8x sun and far `alloc` in the
    # control patch layout, to separate patch size from sun plus dispersal.
    out["sun8_far"] = ["--world-e001", "--sun", "8", "--alloc-far", *BASE]
    return out


ARMS = arms()


def run_one(exe: Path, arm: str, seed: int, ticks: int, force: bool) -> str:
    d = OUT / arm / f"s{seed}"
    if not force and (d / "classes.csv").exists():
        return f"{arm}/s{seed}: done"
    t0 = time.time()
    if force or not (d / "genomes.csv").exists():
        if d.exists():
            shutil.rmtree(d)
        d.parent.mkdir(parents=True, exist_ok=True)
        cmd = [str(exe), "--ticks", str(ticks), "--seed", str(seed), "--report", str(CENSUS),
               "--census", str(CENSUS), "--out", str(d), *ARMS[arm]]
        with open(d.parent / f"s{seed}.stdout", "w") as out:
            subprocess.run(cmd, stdout=out, stderr=subprocess.DEVNULL, check=True)
    t1 = time.time()
    subprocess.run([str(exe), "--classify", str(d)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return f"{arm}/s{seed}: run {t1 - t0:.0f} s, classify {time.time() - t1:.0f} s"


def metrics(arm: str, seed: int, ticks: int) -> dict:
    run = load(OUT / arm / f"s{seed}")
    final = run.patches["tick"].max()
    b = births_typed(run)
    late = b.filter(
        (pl.col("tick") > ticks - LATE_WINDOW)
        & (pl.col("kind") == "exact")
        & (pl.col("parent_class") == "replicator")
    )
    alive = run.class_of(run.orgs.filter(pl.col("tick") == final), "now_hash")
    cen = run.class_of(run.census, "now_hash")
    rep_ticks = cen.filter(pl.col("class") == "replicator")["tick"]
    rep_deaths = deaths_with_signature(run).filter(pl.col("class") == "replicator")
    n_alive = alive.height
    share = lambda df, col, val: (df[col] == val).sum() / df.height if df.height else None
    occ = run.patches.filter((pl.col("tick") == final) & (pl.col("orgs") > 0)).height
    return dict(
        arm=arm,
        seed=seed,
        replicating=late.height > 0,
        late_exact=late.height,
        extinct=n_alive == 0,
        final_tick=final,
        last_rep_tick=rep_ticks.max() if rep_ticks.len() else -1,
        rep_alive_end=(alive["class"] == "replicator").sum(),
        pop_end=n_alive,
        patches_end=occ,
        n_patches=run.patches["patch"].n_unique(),
        age_med_end=(final - alive["birth_tick"]).median() if n_alive else None,
        nonrep_share_end=(1 - share(alive, "class", "replicator")) if n_alive else None,
        births=b.height,
        exact_share=share(b, "kind", "exact"),
        stillborn_share=share(b, "kind", "stillborn"),
        rep_deaths=rep_deaths.height,
        newborn_share=share(rep_deaths, "sig", "newborn"),
    )


def summarize(seeds: int, ticks: int, arm_names: list[str]) -> str:
    rows = []
    for arm in arm_names:
        for s in range(1, seeds + 1):
            if (OUT / arm / f"s{s}" / "classes.csv").exists():
                rows.append(metrics(arm, s, ticks))
    df = pl.DataFrame(rows)
    df.write_csv(OUT / "runs.csv")
    agg = (
        df.group_by("arm", maintain_order=True)
        .agg(
            n=pl.len(),
            replicating=pl.col("replicating").sum(),
            extinct=pl.col("extinct").sum(),
            last_rep=pl.col("last_rep_tick").median(),
            pop_end=pl.col("pop_end").median(),
            patches_end=pl.col("patches_end").median(),
            n_patches=pl.col("n_patches").first(),
            age_med_end=pl.col("age_med_end").median(),
            nonrep_end=pl.col("nonrep_share_end").median(),
            births=pl.col("births").median(),
            exact=pl.col("exact_share").median(),
            stillborn=pl.col("stillborn_share").median(),
            newborn=pl.col("newborn_share").median(),
        )
    )
    f0 = lambda v: "–" if v is None else f"{v:,.0f}"
    f2 = lambda v: "–" if v is None else f"{v:.2f}"
    lines = [
        f"E004 summary: {seeds} seeds x {ticks} ticks, census every {CENSUS}. "
        f"Counts out of n; other columns are medians across seeds.",
        "",
        "| arm | replicating at end | extinct | last replicator census | population at end "
        "| patches occupied at end | median age at end | non-replicator share at end "
        "| births | exact share | stillborn share | newborn share of replicator deaths |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in agg.iter_rows(named=True):
        lines.append(
            f"| {r['arm']} | {r['replicating']}/{r['n']} | {r['extinct']}/{r['n']} "
            f"| {f0(r['last_rep'])} | {f0(r['pop_end'])} | {f0(r['patches_end'])} of {r['n_patches']} "
            f"| {f0(r['age_med_end'])} | {f2(r['nonrep_end'])} | {f0(r['births'])} "
            f"| {f2(r['exact'])} | {f2(r['stillborn'])} | {f2(r['newborn'])} |"
        )
    return "\n".join(lines)


def main() -> None:
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=50_000)
    ap.add_argument("--jobs", type=int, default=20)
    ap.add_argument("--arms", nargs="*", default=list(ARMS))
    ap.add_argument("--force", action="store_true", help="re-run finished runs")
    ap.add_argument("--summarize-only", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT, help="output root (for test runs)")
    a = ap.parse_args()
    OUT = a.out

    if not a.summarize_only:
        exe = binary()
        jobs = [(arm, s) for arm in a.arms for s in range(1, a.seeds + 1)]
        with ThreadPoolExecutor(a.jobs) as ex:
            futs = [ex.submit(run_one, exe, arm, s, a.ticks, a.force) for arm, s in jobs]
            for f in futs:
                print(f.result(), flush=True)

    text = summarize(a.seeds, a.ticks, a.arms)
    (OUT / "summary.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
