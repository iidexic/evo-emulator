"""E007: the standard world over 250,000 ticks. Runs seeds 1-10 of the code's
default physics (E004 p512_far_prop_rot) for five times the E004 length,
records and classifies each run as E004 did, applies the E004 persistence
and E005 parasite measures to the whole run, and then reads each run in
windows of 25,000 ticks: population and classes, the top host (the
replicator-class genome with the most exact births in the window),
parasite and trampoline shares, and the resistance test, which puts the
run's main parasite before the window's top host in the two-genome
harness (`--host HEX --host-body HEX`).

Usage (from analysis/):

    uv run e007_long_run.py                 # build, run, classify, analyse
    uv run e007_long_run.py --analyse-only  # runs exist; redo the tables
    uv run e007_long_run.py --seeds 3

Run directories: runs/e007/std/s<seed>/. Output: runs/e007/runs_e004.csv
and summary_e004.md (persistence, as E004), runs.csv and summary.md
(parasites, as E005), windows.csv and summary_windows.md (per-window
measures and the prediction checks). Protocol and predictions:
docs/research/experiments/2026-10-07-e007-long-run.md.

Added after the run (not pre-registered; the original columns are
unchanged and come first): per window, canonical genotypes
(`genotypes_func`, `top_func_hash`, `top_func_share`: `genotypes` and
`top_share` counted by `func_hash` instead of raw hash) and the
absorb-count and endowment bytes from traits.py (`absorb_*`, `endow_*`:
median, share at or above the threshold, share at the ancestor's value,
share whose guard byte is no longer `lit`), over replicator-class exact
births of 21-byte bodies. E007's review found the raw-hash measures blind
to the absorb-count sweep. summary_windows.md shows them in a second
table at the end.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

import e004_physics as e004
import e005_parasites as e005
import traits
from evo_run import ROOT, binary, load

OUT = ROOT / "runs" / "e007"
ARM = "std"
TICKS = 250_000
WINDOW = 25_000
LATE_FROM = 200_000  # prediction 2: a parasite genome first born after this tick


def host_harness(exe: Path, genome_hex: str, host_hex: str | None) -> dict:
    """Two-genome harness: `genome_hex` placed right before `host_hex` (the
    ancestor when None), quiet default physics, 3,000 ticks."""
    cmd = [str(exe), "--host", genome_hex, "--harness-ticks", str(e005.HARNESS_TICKS)]
    if host_hex is not None:
        cmd += ["--host-body", host_hex]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    header, row = out.strip().splitlines()[:2]
    vals = dict(zip(header.split(","), row.split(",")))
    return {k: (v == "true" if v in ("true", "false") else int(v)) for k, v in vals.items()}


def windows(seed: int, exe: Path | None) -> list[dict]:
    """Per-window measures for one run. Needs classes.csv and the E005
    dependent table (runs/e007/std_s<seed>_dependent.csv)."""
    d = OUT / ARM / f"s{seed}"
    run = load(d)
    dep = pl.read_csv(OUT / f"{ARM}_s{seed}_dependent.csv", schema_overrides={"raw_hash": pl.Utf8, "bytes_hex": pl.Utf8})
    if dep.height:
        parasites = dep.filter(pl.col("parasite_2")).sort("exact_births", descending=True)
        tramps = set(dep.filter(pl.col("foreign_med_2") < 0.05)["raw_hash"])
    else:
        parasites, tramps = dep, set()
    par_set = set(parasites["raw_hash"]) if parasites.height else set()
    main_par = parasites.row(0, named=True) if parasites.height else None
    dep_set = set(dep["raw_hash"]) if dep.height else set()
    hexes = dict(run.genomes.select("raw_hash", "bytes_hex").iter_rows())

    b = run.births.with_columns(
        exact=pl.col("raw_hash") == pl.col("parent_now_hash"),
        win=((pl.col("tick") + WINDOW - 1) // WINDOW).cast(pl.Int64),
    )
    exact_all = run.class_of(b.filter(pl.col("exact")), "raw_hash")
    first_tick = dict(exact_all.group_by("raw_hash").agg(pl.col("tick").min()).iter_rows())
    orgs = run.class_of(run.orgs, "now_hash")
    tr = {r["bin"]: r for r in traits.track(run, WINDOW).iter_rows(named=True)}

    base = host_harness(exe, main_par["bytes_hex"], None) if (exe and main_par) else None
    n_windows = TICKS // WINDOW
    rows = []
    for w in range(1, n_windows + 1):
        lo, hi = (w - 1) * WINDOW, w * WINDOW
        bw = b.filter(pl.col("win") == w)
        ex = exact_all.filter(pl.col("win") == w)
        alive = orgs.filter(pl.col("tick") == hi)
        occupied = run.patches.filter((pl.col("tick") == hi) & (pl.col("orgs") > 0)).height
        per_g = ex.group_by("raw_hash").agg(n=pl.len(), len=pl.col("len").first(), cls=pl.col("class").first())
        reps = per_g.filter(pl.col("cls") == "replicator").sort("n", descending=True)
        top = reps.row(0, named=True) if reps.height else None
        pw = per_g.filter(pl.col("raw_hash").is_in(list(par_set))).sort("n", descending=True) if par_set else per_g.clear()
        top_par = pw.row(0, named=True) if pw.height else None
        n_ex = ex.height
        share = lambda n: n / n_ex if n_ex else None
        r = dict(
            seed=seed,
            window=w,
            tick_end=hi,
            births=bw.height,
            exact=n_ex,
            exact_share=n_ex / bw.height if bw.height else None,
            pop=alive.height,
            rep_alive=int((alive["class"] == "replicator").sum()),
            patches=occupied,
            genotypes=int((per_g["n"] >= 2).sum()),
            top_hash=top["raw_hash"] if top else None,
            top_len=top["len"] if top else None,
            top_share=share(top["n"]) if top else None,
            dep_share=share(int(per_g.filter(pl.col("raw_hash").is_in(list(dep_set)))["n"].sum())) if dep_set else share(0),
            par_share=share(int(pw["n"].sum())) if pw.height else share(0),
            par_active=pw.height,
            par_new=sum(1 for g in par_set if lo < first_tick.get(g, -1) <= hi),
            tramp_share=share(int(per_g.filter(pl.col("raw_hash").is_in(list(tramps)))["n"].sum())) if tramps else share(0),
            top_par_hash=top_par["raw_hash"] if top_par else None,
            top_par_len=top_par["len"] if top_par else None,
            main_par_vs_ancestor=base["exact_births"] if base else None,
            ancestor_exact_with_main_par=base["host_exact_births"] if base else None,
            main_par_vs_top=None,
            top_exact_with_main_par=None,
            resistance=None,
            top_par_vs_top=None,
        )
        if exe and top and main_par:
            h = host_harness(exe, main_par["bytes_hex"], hexes[top["raw_hash"]])
            r["main_par_vs_top"] = h["exact_births"]
            r["top_exact_with_main_par"] = h["host_exact_births"]
            r["resistance"] = h["exact_births"] / base["exact_births"] if base["exact_births"] else None
            if top_par:
                r["top_par_vs_top"] = host_harness(exe, hexes[top_par["raw_hash"]], hexes[top["raw_hash"]])["exact_births"]
        t = tr.get(w, {})
        r["genotypes_func"] = t.get("geno_func", 0)
        r["top_func_hash"] = t.get("top_func_hash")
        r["top_func_share"] = t.get("top_func_share")
        for tt in traits.DEFAULTS:
            for c in (f"{tt.name}_med", tt.ge, f"{tt.name}_anc", f"{tt.name}_excl"):
                r[c] = t.get(c)
        rows.append(r)
    return rows


def _med(df: pl.DataFrame, col: str):
    s = df[col].drop_nulls()
    return s.median() if s.len() else None


def summarize_windows(wdf: pl.DataFrame, persist: pl.DataFrame) -> str:
    f0 = lambda v: "–" if v is None else f"{v:,.0f}"
    f2 = lambda v: "–" if v is None else f"{v:.2f}"
    f3 = lambda v: "–" if v is None else f"{v:.3f}"
    pct = lambda v: "–" if v is None else f"{100 * v:.2f}%"
    surviving = sorted(persist.filter(pl.col("replicating"))["seed"].to_list())
    n_surv = len(surviving)
    live = wdf.filter(pl.col("seed").is_in(surviving))
    n_windows = int(wdf["window"].max())
    last = n_windows

    lines = [
        f"E007 windows: {wdf['seed'].n_unique()} seeds x {TICKS:,} ticks in windows of {WINDOW:,}. "
        f"Medians across the {n_surv} seeds replicating at the end ({', '.join(map(str, surviving))}); "
        f"shares are of the window's exact births.",
        "",
        "| window | ticks | population | replicator-class alive | genotypes (>= 2 exact) | top host share | top host len "
        "| exact share | dependent share | parasite share | parasite genomes active | new parasite genomes "
        "| trampoline share | main parasite exact before top host | before ancestor | resistance ratio "
        "| top host exact with parasite | ancestor exact with parasite | window's top parasite before top host |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for w in range(1, n_windows + 1):
        x = live.filter(pl.col("window") == w)
        lines.append(
            f"| {w} | {(w - 1) * WINDOW:,}–{w * WINDOW:,} | {f0(_med(x, 'pop'))} | {f0(_med(x, 'rep_alive'))} "
            f"| {f0(_med(x, 'genotypes'))} | {f2(_med(x, 'top_share'))} | {f0(_med(x, 'top_len'))} "
            f"| {f2(_med(x, 'exact_share'))} | {f3(_med(x, 'dep_share'))} | {pct(_med(x, 'par_share'))} "
            f"| {f0(_med(x, 'par_active'))} | {f0(_med(x, 'par_new'))} | {f3(_med(x, 'tramp_share'))} "
            f"| {f0(_med(x, 'main_par_vs_top'))} | {f0(_med(x, 'main_par_vs_ancestor'))} | {f2(_med(x, 'resistance'))} "
            f"| {f0(_med(x, 'top_exact_with_main_par'))} | {f0(_med(x, 'ancestor_exact_with_main_par'))} "
            f"| {f0(_med(x, 'top_par_vs_top'))} |"
        )

    # Per-seed checks.
    lines += [
        "",
        "Per seed (surviving seeds first):",
        "",
        "| seed | replicating at end | population at end | sweeps (top host changes, of 9) | top host len, last window "
        "| main parasite len | resistance, window 2 | resistance, last window | parasite share, max over windows "
        f"| parasite genomes first born after {LATE_FROM:,} | genotypes, window 2 / last |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    checks = dict(p2=0, p4=0, p5=0, sweeps=[], par_max_over=0)
    for seed in sorted(wdf["seed"].unique().to_list(), key=lambda s: (s not in surviving, s)):
        x = wdf.filter(pl.col("seed") == seed).sort("window")
        p = persist.filter(pl.col("seed") == seed).row(0, named=True)
        tops = x["top_hash"].to_list()
        sweeps = sum(1 for a, b_ in zip(tops, tops[1:]) if a is not None and b_ is not None and a != b_)
        main_len = None
        dep_path = OUT / f"{ARM}_s{seed}_dependent.csv"
        dep = pl.read_csv(dep_path, schema_overrides={"raw_hash": pl.Utf8, "bytes_hex": pl.Utf8})
        if dep.height and dep["parasite_2"].sum():
            main_len = int(dep.filter(pl.col("parasite_2")).sort("exact_births", descending=True)["len"][0])
            new_late = int((dep.filter(pl.col("parasite_2"))["first_tick"] > LATE_FROM).sum())
        else:
            new_late = 0
        r2 = x.filter(pl.col("window") == 2)["resistance"][0]
        rl = x.filter(pl.col("window") == last)["resistance"][0]
        par_max = x["par_share"].drop_nulls().max() if x["par_share"].drop_nulls().len() else None
        g2 = x.filter(pl.col("window") == 2)["genotypes"][0]
        gl = x.filter(pl.col("window") == last)["genotypes"][0]
        tl = x.filter(pl.col("window") == last)["top_len"][0]
        if seed in surviving:
            checks["p2"] += new_late >= 1
            checks["p4"] += rl is not None and rl >= 0.5
            checks["p5"] += tl is not None and 18 <= tl <= 24
            checks["sweeps"].append(sweeps)
        lines.append(
            f"| {seed} | {'yes' if p['replicating'] else 'no'} | {p['pop_end']} | {sweeps} | {f0(tl)} | {f0(main_len)} "
            f"| {f2(r2)} | {f2(rl)} | {pct(par_max)} | {new_late} | {g2} / {gl} |"
        )

    # Prediction checks (record: E007 "Predictions").
    pop_end_med = persist.filter(pl.col("replicating"))["pop_end"].median() if n_surv else None
    par_med_by_w = [_med(live.filter(pl.col("window") == w), "par_share") for w in range(2, n_windows + 1)]
    par_med_ok = all(v is not None and 0.001 <= v <= 0.03 for v in par_med_by_w)
    par_any_over = int((live["par_share"] > 0.10).sum())
    res2 = _med(live.filter(pl.col("window") == 2), "resistance")
    resl = _med(live.filter(pl.col("window") == last), "resistance")
    res_ratio = (resl / res2) if (res2 and resl is not None) else None
    sweeps_med = pl.Series(checks["sweeps"]).median() if checks["sweeps"] else None
    g2m = _med(live.filter(pl.col("window") == 2), "genotypes")
    glm = _med(live.filter(pl.col("window") == last), "genotypes")
    div_ratio = glm / g2m if (g2m and glm is not None) else None
    lines += [
        "",
        "Prediction checks:",
        "",
        f"1. Replicating at the end in {n_surv} of {persist.height} (>= 7 wanted); population at end, median over "
        f"surviving seeds {f0(pop_end_med)} (700–1,100 wanted).",
        f"2. A parasite genome first born after tick {LATE_FROM:,} in {checks['p2']} of {n_surv} surviving seeds "
        f"(>= 8 wanted).",
        f"3. Parasite share medians, windows 2–{last}: {', '.join(pct(v) for v in par_med_by_w)} "
        f"(all within 0.1%–3%: {'yes' if par_med_ok else 'no'}); seed-windows above 10%: {par_any_over} (0 wanted).",
        f"4. Resistance ratio >= 0.5 in the last window in {checks['p4']} of {n_surv} (>= 8 wanted); median ratio "
        f"window 2 {f2(res2)}, last {f2(resl)}, last/window 2 = {f2(res_ratio)} (0.5–1.5 wanted).",
        f"5. Top host of the last window 18–24 bytes in {checks['p5']} of {n_surv} (>= 8 wanted).",
        f"6. Sweeps: median {f0(sweeps_med)} top-host changes out of {n_windows - 1} (>= 3 wanted).",
        f"7. Genotypes with >= 2 exact births, last window / window 2 = {f2(div_ratio)} (0.5–2 wanted).",
    ]

    # Added after the run, not pre-registered (module docstring).
    a, e = traits.ABSORB, traits.ENDOW
    lines += [
        "",
        "Added after the run (not pre-registered): canonical genotypes and two trait bytes. Medians across the "
        f"same {n_surv} seeds. Genotypes by `func_hash` (bit-7 flips in register operands collapsed) over all exact "
        "births; top canonical host share of the window's exact births; trait columns over replicator-class exact "
        f"births of 21-byte bodies (traits.py): absorb count (byte {a.offset}, ancestor {a.ancestor}) and endowment "
        f"(byte {e.offset}, ancestor {e.ancestor}); 'not lit' is the share whose byte {e.guard} is no longer `lit`.",
        "",
        "| window | genotypes (>= 2 exact) | canonical genotypes (>= 2 exact) | top canonical host share "
        f"| absorb median | absorb >= {a.threshold} | absorb = {a.ancestor} "
        f"| endowment median | endowment >= {e.threshold} | endowment = {e.ancestor} | endowment byte not lit |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for w in range(1, n_windows + 1):
        x = live.filter(pl.col("window") == w)
        lines.append(
            f"| {w} | {f0(_med(x, 'genotypes'))} | {f0(_med(x, 'genotypes_func'))} | {f3(_med(x, 'top_func_share'))} "
            f"| {f0(_med(x, 'absorb_med'))} | {f3(_med(x, a.ge))} | {f3(_med(x, 'absorb_anc'))} "
            f"| {f0(_med(x, 'endow_med'))} | {f3(_med(x, e.ge))} | {f3(_med(x, 'endow_anc'))} "
            f"| {f3(_med(x, 'endow_excl'))} |"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=TICKS)
    ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--windows-only", action="store_true", help="reuse runs.csv and runs_e004.csv")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = range(1, a.seeds + 1)

    e004.OUT = OUT
    e004.ARMS = {ARM: []}
    exe = binary()
    if not a.analyse_only and not a.windows_only:
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda s: e004.run_one(exe, ARM, s, a.ticks, a.force), seeds):
                print(msg, flush=True)

    # The harness physics is the world's physics, so classes_world.csv (which
    # E005's analysis reads) is a copy of classes.csv.
    for s in seeds:
        d = OUT / ARM / f"s{s}"
        if (d / "classes.csv").exists() and not (d / "classes_world.csv").exists():
            shutil.copyfile(d / "classes.csv", d / "classes_world.csv")

    e005.RUNS = OUT
    e005.OUT = OUT
    e005.ARMS = {ARM: []}
    if a.windows_only:
        persist = pl.read_csv(OUT / "runs_e004.csv")
    else:
        rows = [e004.metrics(ARM, s, a.ticks) for s in seeds if (OUT / ARM / f"s{s}" / "classes.csv").exists()]
        persist = pl.DataFrame(rows)
        persist.write_csv(OUT / "runs_e004.csv")
        text = e004.summarize(a.seeds, a.ticks, [ARM]).replace("E004 summary", "E007 persistence (E004 measures)")
        (OUT / "summary_e004.md").write_text(text + "\n", encoding="utf-8")
        print(text)
        e005.run_all([ARM], a.seeds, min(a.jobs, 8), host=True)

    wrows = []
    for s in seeds:
        if (OUT / f"{ARM}_s{s}_dependent.csv").exists():
            wrows += windows(s, exe)
            print(f"{ARM}/s{s}: windows done", flush=True)
    wdf = pl.DataFrame(wrows)
    wdf.write_csv(OUT / "windows.csv")
    text = summarize_windows(wdf, persist)
    (OUT / "summary_windows.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
