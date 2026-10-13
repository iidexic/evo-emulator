"""Run T05 measures on E007, E012 and E013 and write the baseline report
(docs/tasks/T05-measures.md §4).

    uv run measures_baseline.py

Writes to runs/measures/: `runs.csv` (one row per run), `<exp>_series.csv`
(the full series, QNN over `func_hash`), `<exp>_absorb_class_series.csv`
(QNN over `absorb_class`, measures.py `--group absorb_class`) and
`summary.md` (the per-seed table and the shakedown criteria as amended
2026-10-13). E007 seeds are read from runs/lod/e007/s<seed>/ (the complete
reruns) before runs/e007/std/s<seed>/.

Criterion 1, as evaluated here: on the `absorb_class` series, the peak is
the census of maximum `qnn` after tick 2,500. The crossing window is
(t_a, t_75]: t_75 the first census with `absorb_ge96_share` >= 0.75 and t_a
the last census before it with the share below 0.25 (QNN at a census is
the change since the previous one, so the census at which the share first
stands at or above 0.25 is inside). A seed passes when the peak is inside
the window and the mean `qnn` over censuses at or after 25,000 is below a
fifth of the peak. Criterion 2: the largest `mrca_tick` over the censuses
is below 1,000, and in every such seed `root_lines` at the last census is
at least 2. `mrca_changes` is reported without a threshold.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import polars as pl

from evo_run import ROOT, load
from measures import STATIONARY, compute, last_value, qnn_series

RUNS = ROOT / "runs"
OUT = RUNS / "measures"
METRICS = ("mpd", "mean_ed", "change_187", "novelty_187", "ecology_187",
           "change_1870", "novelty_1870", "ecology_1870")
FOUNDER_PHASE = 2_500   # criterion 1 looks for the peak after this tick
SWEEP_LO, SWEEP_HI = 0.25, 0.75
MRCA_EARLY = 1_000      # criterion 2


def _find(runs: Path, exp: str, arm: str, seed: int) -> Path | None:
    candidates = [runs / exp / arm / f"s{seed}"]
    if exp == "e007":
        candidates.insert(0, runs / "lod" / "e007" / f"s{seed}")
    for p in candidates:
        if not (p / "meta.json").exists():
            continue
        # Prefer completed runs with genomes.csv. An extinct seed can still
        # be complete when its final census is early.
        if (p / "genomes.csv").exists() or (p / "genomes.csv.gz").exists():
            return p
    return next((p for p in candidates if (p / "meta.json").exists()), None)


def sweep_check(absorb: pl.DataFrame) -> dict:
    """Criterion 1's numbers from an `absorb_class` QNN series."""
    late = absorb.filter(pl.col("tick") > FOUNDER_PHASE)
    peak = late.sort(["qnn", "tick"], descending=[True, False]).row(0, named=True) if late.height else None
    share = absorb.select("tick", s="absorb_ge96_share").drop_nulls("s")
    hi = share.filter(pl.col("s") >= SWEEP_HI)
    lo_tick = hi_tick = None
    if hi.height:
        hi_tick = int(hi["tick"][0])
        below = share.filter((pl.col("tick") < hi_tick) & (pl.col("s") < SWEEP_LO))
        lo_tick = int(below["tick"][-1]) if below.height else None
    stationary = absorb.filter(pl.col("tick") >= STATIONARY)["qnn"].mean()
    out = dict(sweep_peak_tick=int(peak["tick"]) if peak else None,
               sweep_peak_qnn=float(peak["qnn"]) if peak else None,
               sweep_lo_tick=lo_tick, sweep_hi_tick=hi_tick,
               sweep_stationary=float(stationary) if stationary is not None else None)
    out["sweep_ratio"] = (out["sweep_stationary"] / out["sweep_peak_qnn"]
                          if out["sweep_stationary"] is not None and out["sweep_peak_qnn"] else None)
    inside = (peak is not None and hi_tick is not None
              and (lo_tick is None or lo_tick < out["sweep_peak_tick"]) and out["sweep_peak_tick"] <= hi_tick)
    out["c1"] = bool(inside and out["sweep_ratio"] is not None and out["sweep_ratio"] < 0.2)
    return out


def _process(runs: Path, exp: str, arm: str, seed: int):
    path = _find(runs, exp, arm, seed)
    if path is None:
        return None, None, None, f"missing {exp}/{arm}/s{seed}"
    try:
        start = time.perf_counter()
        run = load(path)
        series, summary = compute(run)
        absorb = qnn_series(run, "absorb_class")
        runtime = time.perf_counter() - start
        if series.height == 0:
            return None, None, None, f"empty census series: {path}"
        at25 = series.filter(pl.col("tick") == STATIONARY)
        max_row = series.sort("qnn", descending=True).row(0, named=True)
        mrca_max = series["mrca_tick"].max()
        row = dict(exp=exp, arm=arm, seed=seed,
                   qnn_cum_25k=float(at25["qnn_cum"][0]) if at25.height else None,
                   qnn_cum_end=float(series["qnn_cum"][-1]),
                   qnn_max=float(max_row["qnn"]), qnn_max_tick=int(max_row["tick"]),
                   qnn_max_window=max(1, (int(max_row["tick"]) - 1) // 25_000 + 1),
                   mrca_tick=last_value(series["mrca_tick"]),
                   mrca_tick_max=int(mrca_max) if mrca_max is not None else None,
                   mrca_gen=last_value(series["mrca_gen"]),
                   root_lines=last_value(series["root_lines"]),
                   mrca_changes=int(series["mrca_changed"].sum()),
                   max_gen=summary["max_gen"],
                   **sweep_check(absorb),
                   runtime_s=runtime,
                   **{m: summary.get(f"mean_{m}") for m in METRICS},
                   run=str(path))
        row["c2_early"] = row["mrca_tick_max"] is not None and row["mrca_tick_max"] < MRCA_EARLY
        row["c2_lines"] = row["root_lines"] is not None and row["root_lines"] >= 2
        return row, series, absorb, None
    except Exception as e:
        return None, None, None, f"{path}: {type(e).__name__}: {e}"


def _f(x) -> str:
    if x is None:
        return "–"
    if isinstance(x, str):
        return x
    return f"{x:.4g}" if isinstance(x, float) else str(x)


def _shakedown(rows: list[dict], seeds: int) -> list[str]:
    e007 = sorted((r for r in rows if r["exp"] == "e007"), key=lambda r: r["seed"])
    lines = ["| seed | `qnn` peak after 2,500 (tick) | peak `qnn` | ≥96 share 0.25→0.75 window | stationary mean | stationary / peak | C1 | max `mrca_tick` | `mrca_gen` | `root_lines` | `mrca_changes` | C2 |",
             "|---:|---:|---:|---|---:|---:|---|---:|---:|---:|---:|---|"]
    for r in e007:
        win = ("never reaches 0.75" if r["sweep_hi_tick"] is None
               else f"({_f(r['sweep_lo_tick'])}, {r['sweep_hi_tick']}]")
        c2 = ("pass" if r["c2_early"] and r["c2_lines"] else
              "lines < 2" if r["c2_early"] else "MRCA late")
        lines.append(f"| {r['seed']} | {_f(r['sweep_peak_tick'])} | {_f(r['sweep_peak_qnn'])} | {win} "
                     f"| {_f(r['sweep_stationary'])} | {_f(r['sweep_ratio'])} | {'pass' if r['c1'] else 'fail'} "
                     f"| {_f(r['mrca_tick_max'])} | {_f(r['mrca_gen'])} | {_f(r['root_lines'])} "
                     f"| {r['mrca_changes']} | {c2} |")
    c1 = sum(r["c1"] for r in e007)
    early = [r for r in e007 if r["c2_early"]]
    lines_ok = sum(r["c2_lines"] for r in early)
    lines += ["",
              f"1. Trait-level sweep (`--group absorb_class`): {c1}/{seeds} E007 seeds pass "
              f"(need ≥ 8/10): **{'pass' if c1 >= 8 else 'fail'}**.",
              f"2. Coexisting lines from the founder: `mrca_tick` stays below 1,000 in {len(early)}/{seeds} seeds "
              f"(need ≥ 8/10) and {lines_ok}/{len(early)} of those have `root_lines` ≥ 2 (need all): "
              f"**{'pass' if len(early) >= 8 and lines_ok == len(early) else 'fail'}**.",
              ]
    if len(e007) != seeds:
        lines[-1] += f" Only {len(e007)} E007 seeds could be read."
    comps = [r for r in rows if r["exp"] in ("e012", "e013")]
    lines.append("3. E012/E013 against E007: " + (
        "not evaluated; runs/e012 and runs/e013 are absent on this machine." if not comps else
        "see the per-run rows; the spread check needs all arms and seeds."))
    return lines


def run_baseline(runs: Path = RUNS, out: Path = OUT, seeds: int = 10) -> list[str]:
    """Process every available run, write the files under `out` and return
    the summary.md lines."""
    out.mkdir(parents=True, exist_ok=True)
    jobs = [("e007", "std", s) for s in range(1, seeds + 1)]
    for exp in ("e012", "e013"):
        root = runs / exp
        if not root.exists():
            continue
        for arm_path in sorted(p for p in root.iterdir() if p.is_dir()):
            jobs.extend((exp, arm_path.name, s) for s in range(1, seeds + 1))
    rows, missing = [], []
    series_by_exp: dict[str, list[pl.DataFrame]] = {}
    absorb_by_exp: dict[str, list[pl.DataFrame]] = {}
    for exp, arm, seed in jobs:
        row, series, absorb, err = _process(runs, exp, arm, seed)
        if err:
            missing.append(err)
            print(err, file=sys.stderr, flush=True)
            continue
        rows.append(row)
        tag = [pl.lit(exp).alias("exp"), pl.lit(arm).alias("arm"), pl.lit(seed).alias("seed")]
        series_by_exp.setdefault(exp, []).append(series.with_columns(tag))
        absorb_by_exp.setdefault(exp, []).append(absorb.with_columns(tag))
        print(f"{exp}/{arm}/s{seed}: {row['runtime_s']:.1f} s, absorb peak {row['sweep_peak_tick']}, "
              f"window ({row['sweep_lo_tick']}, {row['sweep_hi_tick']}], mrca_tick {row['mrca_tick']}, "
              f"root_lines {row['root_lines']}", flush=True)
    if rows:
        pl.DataFrame(rows).write_csv(out / "runs.csv")
    for exp, frames in series_by_exp.items():
        pl.concat(frames, how="diagonal_relaxed").write_csv(out / f"{exp}_series.csv")
    for exp, frames in absorb_by_exp.items():
        pl.concat(frames, how="diagonal_relaxed").write_csv(out / f"{exp}_absorb_class_series.csv")
    lines = ["# T05 measures baseline", "",
             "Per-run results. Stationary tree and MODES columns are means over censuses at or after "
             "tick 25,000 (MODES: uncensored ones only). QNN here is over `func_hash`, the headline for "
             "genotype turnover; it is blind to a trait sweeping across many genotypes (spec §4 "
             "amendment), so the sweep is read from the `absorb_class` grouping below. Δ1870 is "
             "`censored` where the run's deepest generation (`max gen`) is below 1,870.",
             "", "| experiment | arm | seed | QNN cumulative at 25k | QNN cumulative end | max QNN window "
             "| MRCA changes | MRCA tick | MRCA gen | root lines | max gen | MPD | mean ED "
             "| change/novelty/ecology Δ187 | change/novelty/ecology Δ1870 | seconds/run |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|"]
    for r in rows:
        lines.append(f"| {r['exp']} | {r['arm']} | {r['seed']} | {_f(r['qnn_cum_25k'])} | {_f(r['qnn_cum_end'])} "
                     f"| {r['qnn_max_window']} | {r['mrca_changes']} | {_f(r['mrca_tick'])} | {_f(r['mrca_gen'])} "
                     f"| {_f(r['root_lines'])} | {r['max_gen']} | {_f(r['mpd'])} | {_f(r['mean_ed'])} "
                     f"| {_f(r['change_187'])}/{_f(r['novelty_187'])}/{_f(r['ecology_187'])} "
                     f"| {_f(r['change_1870'])}/{_f(r['novelty_1870'])}/{_f(r['ecology_1870'])} "
                     f"| {r['runtime_s']:.1f} |")
    lines += ["", "## Shakedown (criteria as amended 2026-10-13, spec §4)", "",
              "Criterion 1 on the `absorb_class` QNN series: the window is (t_a, t_75], t_75 the first "
              "census with the ≥96 share (among bodies the absorb read matches) at or above 0.75, t_a "
              "the last census before it below 0.25. Criterion 2: largest `mrca_tick` over the censuses; "
              "`root_lines` and `mrca_gen` at the last census.", ""]
    lines += _shakedown(rows, seeds)
    if missing:
        lines += ["", "## Unavailable runs", ""] + [f"- {m}" for m in missing]
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def main() -> None:
    lines = run_baseline()
    print("\n".join(lines))


if __name__ == "__main__":
    main()
