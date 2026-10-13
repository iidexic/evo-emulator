"""Run T05 measures on E007, E012 and E013 and write the baseline report."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import polars as pl

from evo_run import ROOT, load
from measures import compute


RUNS = ROOT / "runs"
OUT = RUNS / "measures"
METRICS = ("mpd", "mean_ed", "change_187", "novelty_187", "ecology_187",
           "change_1870", "novelty_1870", "ecology_1870")


def _find(exp: str, arm: str, seed: int) -> Path | None:
    candidates = [RUNS / exp / arm / f"s{seed}"]
    if exp == "e007":
        candidates.insert(0, RUNS / "lod" / "e007" / f"s{seed}")
    for p in candidates:
        if not (p / "meta.json").exists():
            continue
        # Prefer completed runs with genomes.csv. An extinct seed can still
        # be complete when its final census is early.
        if (p / "genomes.csv").exists() or (p / "genomes.csv.gz").exists():
            return p
    return next((p for p in candidates if (p / "meta.json").exists()), None)


def _process(exp: str, arm: str, seed: int) -> tuple[dict | None, pl.DataFrame | None, str | None]:
    path = _find(exp, arm, seed)
    if path is None:
        return None, None, f"missing {exp}/{arm}/s{seed}"
    try:
        start = time.perf_counter()
        run = load(path)
        series, summary = compute(run)
        runtime = time.perf_counter() - start
        if series.height == 0:
            return None, None, f"empty census series: {path}"
        at25 = series.filter(pl.col("tick") == 25_000)
        max_row = series.sort("qnn", descending=True).row(0, named=True)
        mrca_max = series["mrca_tick"].max()
        row = dict(exp=exp, arm=arm, seed=seed,
                   qnn_cum_25k=float(at25["qnn_cum"][0]) if at25.height else None,
                   qnn_cum_end=float(series["qnn_cum"][-1]),
                   qnn_max=float(max_row["qnn"]), qnn_max_tick=int(max_row["tick"]),
                   qnn_max_window=max(1, (int(max_row["tick"]) - 1) // 25_000 + 1),
                   mrca_tick=int(series["mrca_tick"][-1]),
                   mrca_tick_max=int(mrca_max) if mrca_max is not None else None,
                   mrca_changes=int(series["mrca_changed"].sum()),
                   runtime_s=runtime,
                   **{m: summary.get(f"mean_{m}") for m in METRICS},
                   run=str(path))
        return row, series, None
    except Exception as e:
        return None, None, f"{path}: {type(e).__name__}: {e}"


def _shakedown(rows: list[dict], series_by_key: dict[tuple[str, str, int], pl.DataFrame]) -> list[str]:
    e007 = sorted((r for r in rows if r["exp"] == "e007"), key=lambda r: r["seed"])
    first = 0
    first_details = []
    for r in e007:
        s = series_by_key[("e007", r["arm"], r["seed"])]
        mx = r["qnn_max"]
        stationary = s.filter(pl.col("tick") >= 25_000)["qnn"].mean()
        ok = (r["qnn_max_tick"] <= 10_000 and stationary is not None
              and stationary < mx / 5)
        first += bool(ok)
        ratio = "no stationary censuses" if stationary is None else f"stationary/max={stationary / mx:.3g}"
        first_details.append(f"s{r['seed']} max@{r['qnn_max_tick']} {ratio}")
    second_ok = sum(r["mrca_tick"] > 10_000 and r["mrca_changes"] >= 1 for r in e007)
    lines = [f"1. QNN sweep: {first}/{len(e007)} available E007 seeds pass (need ≥8/10). " + "; ".join(first_details),
             f"2. MRCA replacement: {second_ok}/{len(e007)} available E007 seeds pass both final-tick checks (mrca_tick > 10,000 and mrca_changes ≥1)."]
    if len(e007) != 10:
        lines[0] += " Only complete seed runs are available here."
    comps = [r for r in rows if r["exp"] in ("e012", "e013")]
    if not comps:
        lines.append("3. E012/E013 comparison: unavailable; those run directories are absent on this machine.")
    else:
        lines.append("3. E012/E013 comparison: see per-seed rows; full spread check requires all arms and seeds.")
    return lines


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [("e007", "std", s) for s in range(1, 11)]
    for exp, arms in (("e012", None), ("e013", None)):
        root = RUNS / exp
        if not root.exists():
            continue
        for arm_path in sorted(p for p in root.iterdir() if p.is_dir()):
            jobs.extend((exp, arm_path.name, s) for s in range(1, 11))
    rows, series_by_key, missing = [], {}, []
    series_by_exp: dict[str, list[pl.DataFrame]] = {}
    for exp, arm, seed in jobs:
        row, series, err = _process(exp, arm, seed)
        if err:
            missing.append(err)
            print(err, file=sys.stderr, flush=True)
            continue
        rows.append(row)
        series_by_key[(exp, arm, seed)] = series
        series_by_exp.setdefault(exp, []).append(
            series.with_columns(pl.lit(exp).alias("exp"), pl.lit(arm).alias("arm"), pl.lit(seed).alias("seed"))
        )
        print(f"{exp}/{arm}/s{seed}: qnn_cum={row['qnn_cum_end']:.4g}, "
              f"mrca={row['mrca_tick']}, changes={row['mrca_changes']}", flush=True)
    if rows:
        pl.DataFrame(rows).write_csv(OUT / "runs.csv")
    for exp, frames in series_by_exp.items():
        pl.concat(frames, how="diagonal_relaxed").write_csv(OUT / f"{exp}_series.csv")
    verdicts = _shakedown(rows, series_by_key)
    lines = ["# T05 measures baseline", "", "Per-seed results; stationary tree and MODES columns are means over uncensored censuses at or after tick 25,000.",
             "", "| experiment | arm | seed | QNN cumulative at 25k | QNN cumulative end | max QNN window | MRCA changes | MRCA tick | MPD | mean ED | change/novelty/ecology Δ187 | change/novelty/ecology Δ1870 | seconds/run |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|"]
    for r in rows:
        f = lambda x: "–" if x is None else f"{x:.4g}"
        lines.append(f"| {r['exp']} | {r['arm']} | {r['seed']} | {f(r['qnn_cum_25k'])} | {f(r['qnn_cum_end'])} | {r['qnn_max_window']} | {r['mrca_changes']} | {r['mrca_tick']} | {f(r['mpd'])} | {f(r['mean_ed'])} | {f(r['change_187'])}/{f(r['novelty_187'])}/{f(r['ecology_187'])} | {f(r['change_1870'])}/{f(r['novelty_1870'])}/{f(r['ecology_1870'])} | {r['runtime_s']:.1f} |")
    lines += ["", "## Shakedown", ""] + [f"- {v}" for v in verdicts]
    if missing:
        lines += ["", "## Unavailable runs", ""] + [f"- {m}" for m in missing]
    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
