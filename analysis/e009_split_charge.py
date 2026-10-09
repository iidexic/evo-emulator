"""E009: the split charge. Runs seeds 1-10 of the standard world (the code
default, E007) in two arms, `lo` and `hi`, each with `--charge-owner-pct N`
(the living owner of the byte at IP pays floor(cost * N / 100) of an
instruction another organism executes there, or its whole store if less,
and the executor the rest), for 250,000 ticks; records and classifies each
run, applies the E004 persistence and E005 parasite measures to the whole
run, and reads each run in windows of 25,000 ticks with every E007 and
E008 window measure plus the E009 ones: probe labels, the graded-cost
table, the genome traits from traits.track_genome (endowment by pattern,
self-scan progress, body length) and intruder fate.

Usage (from analysis/; N for each arm comes from the calibration table in
the design and has no default):

    uv run e009_split_charge.py --pct-lo 25 --pct-hi 50                 # build, run, classify, analyse
    uv run e009_split_charge.py --pct-lo 25 --pct-hi 50 --analyse-only  # runs exist; redo the tables
    uv run e009_split_charge.py --pct-lo 25 --pct-hi 50 --seeds 3
    uv run e009_split_charge.py --pct-lo 25 --pct-hi 50 --seeds 1 --ticks 50000 --out /tmp/x  # smoke test only

Run directories: runs/e009/<arm>/s<seed>/ (arm `lo` or `hi`). Output:
runs/e009/runs_e004.csv and summary_e004.md (persistence, as E004),
runs.csv and summary.md (parasites, as E005), windows.csv and
summary_windows.md (per arm: the E007 tables, the E008 tables, the E009
tables; then the prediction checks for both arms). Protocol and
predictions: docs/research/experiments/2026-10-08-e009-split-charge.md.

Physics in the harness. Every harness call uses the arm's flag, as in
E008: the classifier that writes classes.csv, the E005 world classes
(classes_world.csv, a copy of classes.csv), the E005 host harness
(`e005.ARMS` is pointed at the two arms at run time), the resistance test
and the probe. Deaths are joined to classes by `birth_hash` as in E008.

E009 measures and what they are computed from:

- Probe label per seed-window (`probe_label`), from the `pad` probe before
  the window's top host: `defended` (host alive at the end, >= 50 own exact
  births, not `stopped_early`), `starver` (alive, `stopped_early`),
  `survivor` (alive, < 50, ran to the end), `dead` (host dead; death tick
  in `probe_host_death_tick` by E008's bisection).
- Graded cost, over replicator-class deaths in the window split by
  `paid_for_others_m > 0`: median `age`, share with `offspring > 0` (had
  divided), and mean exact children per lifetime. Exact children are
  counted from births.csv: rows with `executor` = the dead organism's `id`
  and `raw_hash == parent_now_hash` (the child is a copy of the executor's
  body at `divide`), over the whole run. `offspring` in deaths.csv counts
  every divide, exact or not, so it is not used for this. This unbanded
  comparison measures exposure (an entered organism lived in a dense
  colony; the seed-1 calibration gave paid organisms 4.5-7 times the
  children at equal median age) and is kept but not tested.
- Banded graded cost (prediction 2, second wording): in age bands 20-39,
  40-79 and 80-159 ticks, the mean exact children of replicator-class
  deaths with `paid_for_others_m` >= 10% of `spent_m` (and > 0) against
  those with `paid_for_others_m` = 0, with counts (`kids_band<lo>_paid`,
  `_unpaid`, `_ratio`, `n_band<lo>_paid`, `_unpaid`) and the median of the
  three band ratios (`kids_band_ratio_med`). The check is the median over
  all seed x band x window (2-10) ratios of the `hi` arm, within 0.5-0.9.
- Genome traits per window from traits.track_genome (see its docstring):
  endowment >= 37 over all replicator-class exact births of bodies of 21
  bytes or more (`endow_all_ge37`; E007/E008's `endow_ge37`, over births
  keeping `lit` at byte 16, is kept), `self1_share`,
  `first_not_self0_share`, the prefix histogram `prefix_0`..`prefix_5`,
  `prefix_ge3`, and body length median and 10th/90th percentiles; absorb
  10th/90th percentiles from traits.track.
- Intruder fate. births.csv carries no execution counters, so "the parent
  executed foreign code at birth" is not recorded. Used instead: the
  executor's lifetime `exec_foreign` and `len` from its deaths.csv row, or
  for an executor alive at the end of the run its row in orgs.csv at the
  last census. This counts a birth whose parent first ran foreign code
  after it (an upper bound on the true set). Per window, over all births
  (exact or not) whose executor has `exec_foreign > 0` by that rule: the
  count and the shares by one-byte executors and by executors of 21 bytes
  or more. Births whose executor has neither row (born after the last
  census and alive at the end) are left out.

Prediction 4 is on the over-all-births basis (`endow_all_ge37`, where a
body of >= 21 bytes without the `lit R ; divide R` pattern counts as
below 37): per seed above 15% (E007's figure on this basis was 13-15%) in
both of windows 9 and 10, and the median across seeds of the two-window
means >= 30%. E007's fixed-offset `endow_ge37` (18-19%) is kept in
windows.csv for comparison.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

import e004_physics as e004
import e005_parasites as e005
import traits
from evo_run import ROOT, binary, load

OUT = ROOT / "runs" / "e009"
ARM_NAMES = ("lo", "hi")
ARMS: dict[str, list[str]] = {}  # arm -> flags for the world run, --classify and every --host call; set in main
PCT: dict[str, int] = {}
TICKS = 250_000
WINDOW = 25_000
LATE_FROM = 200_000  # E007's per-seed column: parasite genomes first born after this tick
PROBE = "00"  # the one-byte `pad`
DEFENDED_MIN = 50  # host exact births with the probe present
E007_ENDOW_TOP = 0.15  # prediction 4, per seed: E007's endowment >= 37 over all births, last windows (13-15%)
ENDOW_MED_MIN = 0.30  # prediction 4: median across seeds of the two-window means
AGE_BANDS = ((20, 40), (40, 80), (80, 160))  # prediction 2: age bands [lo, hi) in ticks
BAND_PAID_MIN = 0.10  # prediction 2: "paid" = paid_for_others_m >= this share of spent_m
KIDS_BAND_RANGE = (0.5, 0.9)  # prediction 2: median band ratio, paid / unpaid
LABELS = ("defended", "starver", "survivor", "dead")
LETTER = {"defended": "D", "starver": "S", "survivor": "v", "dead": "x", None: "-"}


def set_arms(pct_lo: int, pct_hi: int) -> None:
    PCT.update(lo=pct_lo, hi=pct_hi)
    ARMS.clear()
    ARMS.update({arm: ["--charge-owner-pct", str(PCT[arm])] for arm in ARM_NAMES})


def run_dir(arm: str, seed: int) -> Path:
    return OUT / arm / f"s{seed}"


def dep_path(arm: str, seed: int) -> Path:
    return OUT / f"{arm}_s{seed}_dependent.csv"


def read_dep(arm: str, seed: int) -> pl.DataFrame:
    return pl.read_csv(dep_path(arm, seed), schema_overrides={"raw_hash": pl.Utf8, "bytes_hex": pl.Utf8})


def run_one(exe: Path, arm: str, seed: int, ticks: int, force: bool) -> str:
    """E004's run_one with the arm's flags passed to `--classify` too."""
    d = run_dir(arm, seed)
    if not force and (d / "classes.csv").exists():
        return f"{arm}/s{seed}: done"
    t0 = time.time()
    if force or not (d / "genomes.csv").exists():
        if d.exists():
            shutil.rmtree(d)
        d.parent.mkdir(parents=True, exist_ok=True)
        cmd = [str(exe), "--ticks", str(ticks), "--seed", str(seed), "--report", str(e004.CENSUS),
               "--census", str(e004.CENSUS), "--out", str(d), *ARMS[arm]]
        with open(d.parent / f"s{seed}.stdout", "w") as out:
            subprocess.run(cmd, stdout=out, stderr=subprocess.DEVNULL, check=True)
    t1 = time.time()
    subprocess.run([str(exe), "--classify", str(d), "--harness-ticks", str(e005.HARNESS_TICKS), *ARMS[arm]],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return f"{arm}/s{seed}: run {t1 - t0:.0f} s, classify {time.time() - t1:.0f} s"


def host_harness(exe: Path, arm: str, genome_hex: str, host_hex: str | None,
                 ticks: int = e005.HARNESS_TICKS) -> dict:
    """Two-genome harness under the arm's physics: `genome_hex` placed right
    before `host_hex` (the ancestor when None), quiet, `ticks` ticks."""
    cmd = [str(exe), "--host", genome_hex, "--harness-ticks", str(ticks), *ARMS[arm]]
    if host_hex is not None:
        cmd += ["--host-body", host_hex]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    header, row = out.strip().splitlines()[:2]
    vals = dict(zip(header.split(","), row.split(",")))
    return {k: (v == "true" if v in ("true", "false") else int(v)) for k, v in vals.items()}


def host_death_tick(exe: Path, arm: str, genome_hex: str, host_hex: str) -> int | None:
    """First harness length at which the host is dead (None if alive after
    the full run). The harness is deterministic and death is final, so
    `host_alive` is monotone in the length and bisection finds it."""
    if host_harness(exe, arm, genome_hex, host_hex)["host_alive"]:
        return None
    lo, hi = 0, e005.HARNESS_TICKS  # alive at lo (0 ticks), dead at hi
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if host_harness(exe, arm, genome_hex, host_hex, mid)["host_alive"]:
            lo = mid
        else:
            hi = mid
    return hi


def probe_label(p: dict) -> str:
    if not p["host_alive"]:
        return "dead"
    if p["stopped_early"]:
        return "starver"
    return "defended" if p["host_exact_births"] >= DEFENDED_MIN else "survivor"


def windows(arm: str, seed: int, exe: Path | None) -> list[dict]:
    """Per-window measures for one run. Needs classes.csv and the E005
    dependent table (runs/e009/<arm>_s<seed>_dependent.csv)."""
    d = run_dir(arm, seed)
    run = load(d)
    cfg_pct = run.meta.get("config", {}).get("charge_owner_pct")
    if cfg_pct is not None and arm in PCT and cfg_pct != PCT[arm]:
        raise SystemExit(f"{d}: meta.json has charge_owner_pct {cfg_pct}, --pct-{arm} is {PCT[arm]}")
    dep = read_dep(arm, seed)
    if dep.height:
        parasites = dep.filter(pl.col("parasite_2")).sort("exact_births", descending=True)
        tramps = set(dep.filter(pl.col("foreign_med_2") < 0.05)["raw_hash"])
    else:
        parasites, tramps = dep, set()
    par_set = set(parasites["raw_hash"]) if parasites.height else set()
    main_par = parasites.row(0, named=True) if parasites.height else None
    dep_set = set(dep["raw_hash"]) if dep.height else set()
    hexes = dict(run.genomes.select("raw_hash", "bytes_hex").iter_rows())
    known = set(hexes)

    b = run.births.with_columns(
        exact=pl.col("raw_hash") == pl.col("parent_now_hash"),
        win=((pl.col("tick") + WINDOW - 1) // WINDOW).cast(pl.Int64),
    )
    exact_all = run.class_of(b.filter(pl.col("exact")), "raw_hash")
    first_tick = dict(exact_all.group_by("raw_hash").agg(pl.col("tick").min()).iter_rows())
    orgs = run.class_of(run.orgs, "now_hash")
    tr = {r["bin"]: r for r in traits.track(run, WINDOW).iter_rows(named=True)}
    tg = {r["bin"]: r for r in traits.track_genome(run, WINDOW).iter_rows(named=True)}
    # Exact children per organism over the whole run (see the docstring).
    kids = b.filter(pl.col("exact")).group_by("executor").agg(exact_kids=pl.len())
    deaths = (
        run.class_of(run.deaths, "birth_hash")
        .join(kids, left_on="id", right_on="executor", how="left")
        .with_columns(
            win=((pl.col("tick") + WINDOW - 1) // WINDOW).cast(pl.Int64),
            paid=pl.col("paid_for_others_m") > 0,
            now_known=pl.col("now_hash").is_in(list(known)),
            exact_kids=pl.col("exact_kids").fill_null(0),
        )
    )
    # Intruder fate: the executor's lifetime exec_foreign and length, from
    # its death row or its last-census row if alive at the end.
    final = run.orgs["tick"].max()
    alive_end = run.orgs.filter(pl.col("tick") == final).select("id", "len", "exec_foreign")
    parent = pl.concat([
        run.deaths.select("id", "len", "exec_foreign"),
        alive_end.join(run.deaths.select("id"), on="id", how="anti"),
    ]).rename({"id": "executor", "len": "p_len", "exec_foreign": "p_foreign"})
    fb = b.select("win", "executor").join(parent, on="executor", how="inner").filter(pl.col("p_foreign") > 0)

    base = host_harness(exe, arm, main_par["bytes_hex"], None) if (exe and main_par) else None
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
            arm=arm,
            pct=PCT.get(arm),
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
            h = host_harness(exe, arm, main_par["bytes_hex"], hexes[top["raw_hash"]])
            r["main_par_vs_top"] = h["exact_births"]
            r["top_exact_with_main_par"] = h["host_exact_births"]
            r["resistance"] = h["exact_births"] / base["exact_births"] if base["exact_births"] else None
            if top_par:
                r["top_par_vs_top"] = host_harness(exe, arm, hexes[top_par["raw_hash"]], hexes[top["raw_hash"]])["exact_births"]
        t = tr.get(w, {})
        r["genotypes_func"] = t.get("geno_func", 0)
        r["top_func_hash"] = t.get("top_func_hash")
        r["top_func_share"] = t.get("top_func_share")
        for tt in traits.DEFAULTS:
            for c in (f"{tt.name}_med", tt.ge, f"{tt.name}_anc", f"{tt.name}_excl"):
                r[c] = t.get(c)

        # --- E008 measures ---------------------------------------------------
        # Defence probe: `pad` before the window's top host.
        r.update(probe_exact=None, host_exact_with_probe=None, host_alive=None, probe_ticks_run=None,
                 probe_stopped_early=None, defended=None, probe_host_death_tick=None, probe_label=None)
        if exe and top:
            p = host_harness(exe, arm, PROBE, hexes[top["raw_hash"]])
            lab = probe_label(p)
            r.update(
                probe_exact=p["exact_births"],
                host_exact_with_probe=p["host_exact_births"],
                host_alive=p["host_alive"],
                probe_ticks_run=p["ticks_run"],
                probe_stopped_early=p["stopped_early"],
                defended=lab == "defended",
                probe_host_death_tick=None if p["host_alive"] else host_death_tick(exe, arm, PROBE, hexes[top["raw_hash"]]),
                probe_label=lab,
            )
        # Hosts killed by intruders: deaths in the window, classed by birth hash.
        dw = deaths.filter(pl.col("win") == w)
        rd = dw.filter(pl.col("class") == "replicator")
        spent = int(dw["spent_m"].sum())
        r.update(
            deaths=dw.height,
            rep_deaths=rd.height,
            rep_deaths_paid_share=float(rd["paid"].mean()) if rd.height else None,
            deaths_paid_share=float(dw["paid"].mean()) if dw.height else None,
            paid_energy_share=int(dw["paid_for_others_m"].sum()) / spent if spent else None,
            death_now_hash_missing=1 - float(dw["now_known"].mean()) if dw.height else None,
        )
        # Execution shares over living bodies at the window's last census.
        executed = int(alive["executed"].sum())
        r.update(
            foreign_exec_share=int(alive["exec_foreign"].sum()) / executed if executed else None,
            unowned_exec_share=int(alive["exec_unowned"].sum()) / executed if executed else None,
            alive_paid_share=float((alive["paid_for_others_m"] > 0).mean()) if alive.height else None,
            one_byte_share=share(int(per_g.filter(pl.col("len") == 1)["n"].sum())),
        )

        # --- E009 measures ---------------------------------------------------
        # Graded cost: replicator-class deaths that paid for others against
        # those that did not.
        yes, no = rd.filter(pl.col("paid")), rd.filter(~pl.col("paid"))
        med = lambda df, c: float(df[c].median()) if df.height else None
        mean = lambda df, c: float(df[c].mean()) if df.height else None
        age_p, age_n = med(yes, "age"), med(no, "age")
        kid_p, kid_n = mean(yes, "exact_kids"), mean(no, "exact_kids")
        r.update(
            rep_deaths_paid=yes.height,
            rep_deaths_unpaid=no.height,
            age_med_paid=age_p,
            age_med_unpaid=age_n,
            age_ratio=age_p / age_n if (age_p is not None and age_n) else None,
            divided_paid=mean(yes.with_columns(dv=pl.col("offspring") > 0), "dv"),
            divided_unpaid=mean(no.with_columns(dv=pl.col("offspring") > 0), "dv"),
            kids_mean_paid=kid_p,
            kids_mean_unpaid=kid_n,
            kids_ratio=kid_p / kid_n if (kid_p is not None and kid_n) else None,
            paid_by_energy_share=int(dw["paid_by_others_m"].sum()) / spent
            if (spent and "paid_by_others_m" in dw.columns) else None,
        )
        # Banded graded cost (prediction 2, second wording): within each age
        # band, organisms that paid >= BAND_PAID_MIN of their spending for
        # others against those that paid nothing.
        heavy = pl.col("paid_for_others_m") >= BAND_PAID_MIN * pl.col("spent_m")
        none_ = pl.col("paid_for_others_m") == 0
        ratios = []
        for lo_a, hi_a in AGE_BANDS:
            band = rd.filter((pl.col("age") >= lo_a) & (pl.col("age") < hi_a))
            bp, bn = band.filter(heavy & (pl.col("paid_for_others_m") > 0)), band.filter(none_)
            kp, kn = mean(bp, "exact_kids"), mean(bn, "exact_kids")
            ratio = kp / kn if (kp is not None and kn) else None
            r.update({
                f"kids_band{lo_a}_paid": kp, f"kids_band{lo_a}_unpaid": kn,
                f"n_band{lo_a}_paid": bp.height, f"n_band{lo_a}_unpaid": bn.height,
                f"kids_band{lo_a}_ratio": ratio,
            })
            if ratio is not None:
                ratios.append(ratio)
        r["kids_band_ratio_med"] = float(pl.Series(ratios).median()) if ratios else None
        # Genome traits (traits.track_genome) and the absorb percentiles.
        g = tg.get(w, {})
        r["absorb_p10"], r["absorb_p90"] = t.get("absorb_p10"), t.get("absorb_p90")
        for c in ("rep_n", "len_med", "len_p10", "len_p90", "endow_all_n", "endow_all_ge37", "endow_all_nolit",
                  "endow_all_med", "endow_all_p10", "endow_all_p90", "self1_share", "first_not_self0_share",
                  "prefix_ge3", *(f"prefix_{k}" for k in range(len(traits.PREFIX) + 1))):
            r[c] = g.get(c)
        # Intruder fate (see the docstring for what "foreign at birth" means here).
        fw = fb.filter(pl.col("win") == w)
        r.update(
            foreign_parent_births=fw.height,
            foreign_parent_one_byte_share=float((fw["p_len"] == 1).mean()) if fw.height else None,
            foreign_parent_ge21_share=float((fw["p_len"] >= 21).mean()) if fw.height else None,
        )
        rows.append(r)
    return rows


def _med(df: pl.DataFrame, col: str):
    s = df[col].drop_nulls()
    return s.median() if s.len() else None


f0 = lambda v: "–" if v is None else f"{v:,.0f}"
f2 = lambda v: "–" if v is None else f"{v:.2f}"
f3 = lambda v: "–" if v is None else f"{v:.3f}"
pct = lambda v: "–" if v is None else f"{100 * v:.2f}%"
yn = lambda ok: "yes" if ok else "no"
cnt = lambda x, col: int(x[col].drop_nulls().sum()) if x[col].drop_nulls().len() else 0


def surviving_seeds(persist: pl.DataFrame, arm: str) -> list[int]:
    return sorted(persist.filter((pl.col("arm") == arm) & pl.col("replicating"))["seed"].to_list())


def summarize_arm(wdf: pl.DataFrame, persist: pl.DataFrame, arm: str) -> list[str]:
    """E007 and E008 tables for one arm, then the E009 tables."""
    flags = " ".join(ARMS.get(arm, [f"--charge-owner-pct {PCT.get(arm)}"]))
    surviving = surviving_seeds(persist, arm)
    n_surv = len(surviving)
    live = wdf.filter(pl.col("seed").is_in(surviving))
    n_windows = int(wdf["window"].max())
    last = n_windows

    lines = [
        f"## Arm `{arm}` (`{flags}`)",
        "",
        f"{wdf['seed'].n_unique()} seeds x {TICKS:,} ticks in windows of "
        f"{WINDOW:,}. Medians across the {n_surv} seeds replicating at the end ({', '.join(map(str, surviving))}); "
        f"shares are of the window's exact births. Every harness column uses the arm's physics.",
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

    # Per-seed table (E007's columns).
    lines += [
        "",
        "Per seed (surviving seeds first):",
        "",
        "| seed | replicating at end | population at end | sweeps (top host changes, of 9) | top host len, last window "
        "| main parasite len | resistance, window 2 | resistance, last window | parasite share, max over windows "
        f"| parasite genomes first born after {LATE_FROM:,} | genotypes, window 2 / last |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    order = sorted(wdf["seed"].unique().to_list(), key=lambda s: (s not in surviving, s))
    one_byte = {}
    for seed in order:
        x = wdf.filter(pl.col("seed") == seed).sort("window")
        p = persist.filter((pl.col("arm") == arm) & (pl.col("seed") == seed)).row(0, named=True)
        tops = x["top_hash"].to_list()
        sweeps = sum(1 for a, b_ in zip(tops, tops[1:]) if a is not None and b_ is not None and a != b_)
        main_len = None
        dep = read_dep(arm, seed)
        if dep.height and dep["parasite_2"].sum():
            main_len = int(dep.filter(pl.col("parasite_2")).sort("exact_births", descending=True)["len"][0])
            new_late = int((dep.filter(pl.col("parasite_2"))["first_tick"] > LATE_FROM).sum())
        else:
            new_late = 0
        ob = dep.filter(pl.col("len") == 1) if dep.height else dep
        one_byte[seed] = (
            int(ob["depth"].max()) if ob.height else None,
            int(ob["exact_births"].sum()) if ob.height else 0,
            int(ob["parasite_2"].sum()) if ob.height else 0,
        )
        val = lambda col, w: x.filter(pl.col("window") == w)[col][0] if x.filter(pl.col("window") == w).height else None
        par_max = x["par_share"].drop_nulls().max() if x["par_share"].drop_nulls().len() else None
        lines.append(
            f"| {seed} | {yn(p['replicating'])} | {p['pop_end']} | {sweeps} | {f0(val('top_len', last))} | {f0(main_len)} "
            f"| {f2(val('resistance', 2))} | {f2(val('resistance', last))} | {pct(par_max)} | {new_late} "
            f"| {val('genotypes', 2)} / {val('genotypes', last)} |"
        )

    # Post-hoc E007 columns.
    a, e = traits.ABSORB, traits.ENDOW
    lines += [
        "",
        "E007's post-hoc columns: canonical genotypes and two trait bytes. Medians across the "
        f"same {n_surv} seeds. Genotypes by `func_hash` over all exact births; top canonical host share of the "
        "window's exact births; trait columns over replicator-class exact births of 21-byte bodies (traits.py): "
        f"absorb count (byte {a.offset}, ancestor {a.ancestor}) and endowment (byte {e.offset}, ancestor "
        f"{e.ancestor}); 'not lit' is the share whose byte {e.guard} is no longer `lit`.",
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

    # E008 table.
    lines += [
        "",
        "E008 measures. Medians across the same seeds except the counted columns (seeds). Probe: `pad` "
        f"before the window's top host, {e005.HARNESS_TICKS:,} ticks; defended = host alive at the end, >= "
        f"{DEFENDED_MIN} exact births of its own, and the probe did not stop early. Host death tick by bisection "
        "(median over probe runs in which the host died). Deaths in the window classed by birth hash; energy "
        "share = paid for others / spent, summed over the window's deaths. Execution shares: lifetime counters "
        "summed over bodies alive at the window's last census.",
        "",
        "| window | probe exact | host exact with probe | host alive (seeds) | defended (seeds) | probe stopped early (seeds) "
        "| host death tick | replicator deaths that paid | all deaths that paid | energy share paid for others "
        "| foreign exec share | unowned exec share | living bodies that have paid | one-byte share of exact births |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for w in range(1, n_windows + 1):
        x = live.filter(pl.col("window") == w)
        lines.append(
            f"| {w} | {f0(_med(x, 'probe_exact'))} | {f0(_med(x, 'host_exact_with_probe'))} "
            f"| {cnt(x, 'host_alive')} | {cnt(x, 'defended')} | {cnt(x, 'probe_stopped_early')} "
            f"| {f0(_med(x, 'probe_host_death_tick'))} | {pct(_med(x, 'rep_deaths_paid_share'))} "
            f"| {pct(_med(x, 'deaths_paid_share'))} | {pct(_med(x, 'paid_energy_share'))} "
            f"| {pct(_med(x, 'foreign_exec_share'))} | {pct(_med(x, 'unowned_exec_share'))} "
            f"| {pct(_med(x, 'alive_paid_share'))} | {pct(_med(x, 'one_byte_share'))} |"
        )

    # E008 per seed.
    lines += [
        "",
        "E008 per seed:",
        "",
        "| seed | probe exact / host exact, last window | host alive, last | defended, last | stopped early, last "
        f"| host death tick, last | defended windows (of {n_windows}) | replicator deaths that paid, window 1 / 2 / last "
        "| last / window 2 | deepest one-byte dependent lineage | one-byte dependent exact births | one-byte parasites |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for seed in order:
        x = wdf.filter(pl.col("seed") == seed).sort("window")
        val = lambda col, w: x.filter(pl.col("window") == w)[col][0] if x.filter(pl.col("window") == w).height else None
        r2, rl = val("rep_deaths_paid_share", 2), val("rep_deaths_paid_share", last)
        ratio = rl / r2 if (r2 and rl is not None) else None
        dl = val("defended", last)
        hl = val("host_alive", last)
        sl = val("probe_stopped_early", last)
        ob = one_byte[seed]
        lines.append(
            f"| {seed} | {f0(val('probe_exact', last))} / {f0(val('host_exact_with_probe', last))} "
            f"| {'–' if hl is None else yn(hl)} | {'–' if dl is None else yn(dl)} | {'–' if sl is None else yn(sl)} "
            f"| {f0(val('probe_host_death_tick', last))} | {cnt(x, 'defended')} "
            f"| {pct(val('rep_deaths_paid_share', 1))} / {pct(r2)} / {pct(rl)} | {f2(ratio)} "
            f"| {f0(ob[0])} | {f0(ob[1])} | {ob[2]} |"
        )

    # --- E009 tables -----------------------------------------------------------
    lines += [
        "",
        "E009 probe labels (counts of surviving seeds) and graded cost (medians across the same seeds). Labels from "
        f"the `pad` probe: defended = alive, >= {DEFENDED_MIN} own exact births, not stopped early; starver = alive, "
        f"stopped early; survivor = alive, < {DEFENDED_MIN}, ran to the end; dead = host dead (death tick median over "
        "the dead). Exposure measure (unbanded; the first wording of prediction 2, kept because it measures "
        "exposure, not cost: being entered marks an organism that lived in a dense colony): over replicator-class "
        "deaths in the window, paid = `paid_for_others_m` > 0: median age at death, share with offspring > 0, mean "
        "exact children per lifetime (births.csv rows with that executor and child == executor's body). Ratios are "
        "per seed (paid / unpaid), then the median.",
        "",
        "| window | defended | starver | survivor | dead | dead: host death tick | paid deaths | unpaid deaths "
        "| age paid | age unpaid | age ratio | divided paid | divided unpaid | exact children paid | exact children unpaid "
        "| children ratio | energy share paid by others |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    lab = lambda x, name: int((x["probe_label"] == name).sum()) if x["probe_label"].drop_nulls().len() else 0
    for w in range(1, n_windows + 1):
        x = live.filter(pl.col("window") == w)
        dead = x.filter(pl.col("probe_label") == "dead")
        lines.append(
            f"| {w} | {lab(x, 'defended')} | {lab(x, 'starver')} | {lab(x, 'survivor')} | {lab(x, 'dead')} "
            f"| {f0(_med(dead, 'probe_host_death_tick'))} | {f0(_med(x, 'rep_deaths_paid'))} "
            f"| {f0(_med(x, 'rep_deaths_unpaid'))} | {f0(_med(x, 'age_med_paid'))} | {f0(_med(x, 'age_med_unpaid'))} "
            f"| {f2(_med(x, 'age_ratio'))} | {pct(_med(x, 'divided_paid'))} | {pct(_med(x, 'divided_unpaid'))} "
            f"| {f3(_med(x, 'kids_mean_paid'))} | {f3(_med(x, 'kids_mean_unpaid'))} | {f2(_med(x, 'kids_ratio'))} "
            f"| {pct(_med(x, 'paid_by_energy_share'))} |"
        )

    # Banded graded cost (prediction 2, second wording).
    bands = [lo_a for lo_a, _ in AGE_BANDS]
    lines += [
        "",
        "E009 graded cost within age bands (prediction 2): over replicator-class deaths in the window, mean exact "
        f"children of organisms with `paid_for_others_m` >= {BAND_PAID_MIN:.0%} of `spent_m` (paid) and of those with "
        "`paid_for_others_m` = 0 (unpaid), per age band; medians across the same seeds (n = median count per cell). "
        "Ratio = paid / unpaid per seed and band; last column = median across seeds of each seed's median over "
        "the three bands.",
        "",
        "| window | " + " | ".join(f"{lo_a}–{hi_a - 1}: paid / unpaid (n) | ratio" for lo_a, hi_a in AGE_BANDS)
        + " | band ratio median |",
        "|---|" + "---|---|" * len(AGE_BANDS) + "---|",
    ]
    for w in range(1, n_windows + 1):
        x = live.filter(pl.col("window") == w)
        cells = " | ".join(
            f"{f2(_med(x, f'kids_band{b}_paid'))} / {f2(_med(x, f'kids_band{b}_unpaid'))} "
            f"({f0(_med(x, f'n_band{b}_paid'))} / {f0(_med(x, f'n_band{b}_unpaid'))}) "
            f"| {f2(_med(x, f'kids_band{b}_ratio'))}"
            for b in bands
        )
        lines.append(f"| {w} | {cells} | {f2(_med(x, 'kids_band_ratio_med'))} |")

    lines += [
        "",
        "E009 genome traits (traits.track_genome) over replicator-class exact births of any length, medians across "
        "the same seeds. Endowment by pattern (`lit R v ; divide R`) over bodies of >= 21 bytes, a body without the "
        "pattern counting as below 37; prefix k = longest match of `self 1 ; swap C ; self 0 ; sub C ; jmpr A` at"
        "byte 0 on canonical instructions.",
        "",
        "| window | length p10 / median / p90 | absorb p10 / median / p90 | endowment p10 / median / p90 "
        "| endowment >= 37 (all) | no endowment pattern | `self 1` present | first not `self 0` "
        "| prefix 0 | 1 | 2 | 3 | 4 | 5 | prefix >= 3 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for w in range(1, n_windows + 1):
        x = live.filter(pl.col("window") == w)
        hist = " | ".join(pct(_med(x, f"prefix_{k}")) for k in range(len(traits.PREFIX) + 1))
        lines.append(
            f"| {w} | {f0(_med(x, 'len_p10'))} / {f0(_med(x, 'len_med'))} / {f0(_med(x, 'len_p90'))} "
            f"| {f0(_med(x, 'absorb_p10'))} / {f0(_med(x, 'absorb_med'))} / {f0(_med(x, 'absorb_p90'))} "
            f"| {f0(_med(x, 'endow_all_p10'))} / {f0(_med(x, 'endow_all_med'))} / {f0(_med(x, 'endow_all_p90'))} "
            f"| {pct(_med(x, 'endow_all_ge37'))} | {pct(_med(x, 'endow_all_nolit'))} | {pct(_med(x, 'self1_share'))} "
            f"| {pct(_med(x, 'first_not_self0_share'))} | {hist} | {pct(_med(x, 'prefix_ge3'))} |"
        )

    lines += [
        "",
        "E009 intruder fate: births (exact or not) whose executor's lifetime `exec_foreign` > 0 (from its death row, "
        "or its last-census row if alive at the end; births.csv has no counters at birth), medians across the same "
        "seeds.",
        "",
        "| window | births by foreign-executing parents | by one-byte parents | by parents >= 21 bytes |",
        "|---|---|---|---|",
    ]
    for w in range(1, n_windows + 1):
        x = live.filter(pl.col("window") == w)
        lines.append(
            f"| {w} | {f0(_med(x, 'foreign_parent_births'))} | {pct(_med(x, 'foreign_parent_one_byte_share'))} "
            f"| {pct(_med(x, 'foreign_parent_ge21_share'))} |"
        )

    lines += [
        "",
        "E009 per seed: probe label per window (D defended, S starver, v survivor, x dead, - no top host), "
        "endowment >= 37 (all) in the last two windows, max prefix-5 and prefix->=3 shares over windows.",
        "",
        f"| seed | labels, windows 1–{n_windows} | last label | host death tick, last | endowment >= 37, "
        f"window {last - 1} / {last} | max prefix 5 | max prefix >= 3 |",
        "|---|---|---|---|---|---|---|",
    ]
    for seed in order:
        x = wdf.filter(pl.col("seed") == seed).sort("window")
        val = lambda col, w: x.filter(pl.col("window") == w)[col][0] if x.filter(pl.col("window") == w).height else None
        labs = "".join(LETTER.get(v, "-") for v in x["probe_label"].to_list())
        mx = lambda c: x[c].drop_nulls().max() if x[c].drop_nulls().len() else None
        lines.append(
            f"| {seed} | `{labs}` | {val('probe_label', last) or '–'} | {f0(val('probe_host_death_tick', last))} "
            f"| {pct(val('endow_all_ge37', last - 1))} / {pct(val('endow_all_ge37', last))} "
            f"| {pct(mx('prefix_5'))} | {pct(mx('prefix_ge3'))} |"
        )
    return lines


def predictions(wdf: pl.DataFrame, persist: pl.DataFrame) -> list[str]:
    """Prediction checks 1-6 of the design, arm by arm where the prediction
    covers both arms."""
    n_windows = int(wdf["window"].max())
    last = n_windows
    later = range(2, n_windows + 1)
    lines = ["", "## Prediction checks", "",
             "Medians across surviving seeds of the arm unless counted in seeds; thresholds in brackets.", ""]

    def live_of(arm):
        s = surviving_seeds(persist, arm)
        return s, wdf.filter((pl.col("arm") == arm) & pl.col("seed").is_in(s))

    # 1. Persistence, both arms.
    p1 = {}
    for arm in ARM_NAMES:
        surv, _ = live_of(arm)
        pa = persist.filter(pl.col("arm") == arm)
        pop = pa.filter(pl.col("replicating"))["pop_end"].median() if surv else None
        p1[arm] = len(surv) >= 7 and pop is not None and 700 <= pop <= 1100
        lines.append(f"1 ({arm}). Replicating at the end in {len(surv)} of {pa.height} [>= 7]; population at end, "
                     f"median {f0(pop)} [700–1,100]. Holds: {yn(p1[arm])}.")
    lines.append(f"1. Holds in both arms: {yn(all(p1.values()))}.")

    # 2. Graded cost within age bands, hi arm, windows 2-10 (lo for reference).
    lo_r, hi_r = KIDS_BAND_RANGE
    ratio_cols = [f"kids_band{lo_a}_ratio" for lo_a, _ in AGE_BANDS]
    for arm in ("hi", "lo"):
        _, live = live_of(arm)
        lw = live.filter(pl.col("window").is_in(list(later)))
        pooled = pl.concat([lw[c].cast(pl.Float64) for c in ratio_cols]).drop_nulls() if lw.height else pl.Series([])
        m = float(pooled.median()) if pooled.len() else None
        ok = m is not None and lo_r <= m <= hi_r
        per_w = [_med(live.filter(pl.col("window") == w), "kids_band_ratio_med") for w in later]
        ages = [_med(live.filter(pl.col("window") == w), "age_ratio") for w in later]
        kids = [_med(live.filter(pl.col("window") == w), "kids_ratio") for w in later]
        tag = "" if arm == "hi" else " (reference only; the prediction is for `hi`)"
        lines.append(
            f"2 ({arm}){tag}. Mean exact children, paid (>= {BAND_PAID_MIN:.0%} of spending) / unpaid, within age "
            f"bands {', '.join(f'{x}–{y - 1}' for x, y in AGE_BANDS)}: median across seeds, bands and windows "
            f"2–{last} {f2(m)} over {pooled.len()} seed-band-window ratios [{lo_r}–{hi_r}]. Holds: {yn(ok)}. "
            f"Per-window medians of the band-ratio median: {', '.join(f2(v) for v in per_w)}. Exposure measure "
            f"(unbanded, first wording, not tested): age ratio {', '.join(f2(v) for v in ages)}; children ratio "
            f"{', '.join(f2(v) for v in kids)}."
        )

    # 3. Parasitism in the E007 form, hi arm (lo for reference).
    for arm in ("hi", "lo"):
        _, live = live_of(arm)
        par = [_med(live.filter(pl.col("window") == w), "par_share") for w in later]
        fx = [_med(live.filter(pl.col("window") == w), "foreign_exec_share") for w in later]
        ok_p = all(v is not None and 0.003 <= v <= 0.015 for v in par)
        ok_f = all(v is not None and 0.05 <= v <= 0.15 for v in fx)
        tag = "" if arm == "hi" else " (reference only)"
        lines.append(
            f"3 ({arm}){tag}. Parasite share, windows 2–{last}: {', '.join(pct(v) for v in par)} "
            f"[all 0.3–1.5%: {yn(ok_p)}]; foreign exec share over living bodies: {', '.join(pct(v) for v in fx)} "
            f"[all 5–15%: {yn(ok_f)}]. Holds: {yn(ok_p and ok_f)}."
        )

    # 4. Endowment starver selected: hi arm, windows 9-10.
    w_late = [w for w in (last - 1, last) if w >= 1]
    meds = {}
    for arm in ("hi", "lo"):
        surv, live = live_of(arm)
        per_seed = {}
        for s in surv:
            v = live.filter((pl.col("seed") == s) & pl.col("window").is_in(w_late))["endow_all_ge37"].drop_nulls()
            per_seed[s] = (v.min() if v.len() == len(w_late) else None, v.mean() if v.len() else None)
        above = sum(1 for lo_, _ in per_seed.values() if lo_ is not None and lo_ > E007_ENDOW_TOP)
        means = [m for _, m in per_seed.values() if m is not None]
        meds[arm] = pl.Series(means).median() if means else None
        if arm == "hi":
            p4 = above >= 6 and meds[arm] is not None and meds[arm] >= ENDOW_MED_MIN
            lines.append(
                f"4 (hi). Endowment >= 37 over all replicator-class exact births of >= 21-byte bodies, windows "
                f"{'–'.join(map(str, w_late))}: above E007's {pct(E007_ENDOW_TOP)} [per-seed threshold] in both windows in {above} of "
                f"{len(surv)} surviving seeds [>= 6]; median across seeds of the two-window mean {pct(meds[arm])} "
                f"[>= {pct(ENDOW_MED_MIN)}]. Holds: {yn(p4)}."
            )
        else:
            same = meds["lo"] is not None and meds["hi"] is not None and E007_ENDOW_TOP < meds["lo"] < meds["hi"]
            lines.append(
                f"4 (lo). Same measure: above {pct(E007_ENDOW_TOP)} in both windows in {above} of {len(surv)} "
                f"surviving seeds; median {pct(meds['lo'])} [above {pct(E007_ENDOW_TOP)} and below hi's "
                f"{pct(meds['hi'])}: {yn(same)}]."
            )

    # 5. Self-scan not found: every window of every seed (with data), both arms.
    p5 = {}
    for arm in ARM_NAMES:
        x = wdf.filter(pl.col("arm") == arm)
        m5 = x["prefix_5"].drop_nulls().max() if x["prefix_5"].drop_nulls().len() else None
        m3 = x["prefix_ge3"].drop_nulls().max() if x["prefix_ge3"].drop_nulls().len() else None
        p5[arm] = m5 is not None and m5 < 0.01 and m3 is not None and m3 <= 0.05
        where = ""
        if m3 is not None and m3 > 0:
            r = x.sort("prefix_ge3", descending=True, nulls_last=True).row(0, named=True)
            where = f" (seed {r['seed']}, window {r['window']})"
        lines.append(
            f"5 ({arm}). Prefix 5 at byte 0, max over all {x['seed'].n_unique()} seeds x windows: {pct(m5)} [< 1%]; "
            f"prefix >= 3, max: {pct(m3)}{where} [<= 5%]. Holds: {yn(p5[arm])}."
        )
    lines.append(f"5. Holds in both arms: {yn(all(p5.values()))}.")

    # 6. Defence, H14: hi arm, last window.
    for arm in ("hi", "lo"):
        surv, live = live_of(arm)
        x = live.filter(pl.col("window") == last)
        n_def = int((x["probe_label"] == "defended").sum()) if x.height else 0
        n_st = int((x["probe_label"] == "starver").sum()) if x.height else 0
        n_sv = int((x["probe_label"] == "survivor").sum()) if x.height else 0
        n_dd = int((x["probe_label"] == "dead").sum()) if x.height else 0
        if arm == "hi":
            p6 = n_def <= 2 and n_st >= 4
            lines.append(
                f"6 (hi). Last window, of {len(surv)} surviving seeds: defended {n_def} [<= 2], starver {n_st} "
                f"[>= 4] (survivor {n_sv}, dead {n_dd}). Holds: {yn(p6)}."
            )
        else:
            lines.append(
                f"6 (lo, reference). Last window, of {len(surv)} surviving seeds: defended {n_def}, starver {n_st}, "
                f"survivor {n_sv}, dead {n_dd}."
            )
    return lines


def summarize_windows(wdf: pl.DataFrame, persist: pl.DataFrame) -> str:
    # All-null columns (no binary, so no probe) come out as dtype Null.
    wdf = wdf.with_columns(pl.col("probe_label").cast(pl.Utf8))
    lines = [
        f"E009 windows: arms {', '.join(f'`{a}` (N = {PCT.get(a)})' for a in ARM_NAMES)}, "
        f"{TICKS:,} ticks, windows of {WINDOW:,}.",
        "",
    ]
    for arm in ARM_NAMES:
        x = wdf.filter(pl.col("arm") == arm)
        if x.height:
            lines += summarize_arm(x, persist, arm) + [""]
    if all(wdf.filter(pl.col("arm") == a).height for a in ARM_NAMES):
        lines += predictions(wdf, persist)
    else:
        lines.append("Prediction checks need both arms; skipped.")
    return "\n".join(lines)


def main() -> None:
    global OUT, TICKS
    ap = argparse.ArgumentParser()
    ap.add_argument("--pct-lo", type=int, default=None, help="N for the `lo` arm (from the calibration)")
    ap.add_argument("--pct-hi", type=int, default=None, help="N for the `hi` arm (from the calibration)")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=TICKS, help="override for smoke tests only")
    ap.add_argument("--out", type=Path, default=OUT, help="output root (smoke tests only)")
    ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--windows-only", action="store_true", help="reuse runs.csv and runs_e004.csv")
    a = ap.parse_args()
    if a.pct_lo is None or a.pct_hi is None:
        ap.error("--pct-lo and --pct-hi are required: the arms' N come from the calibration table in "
                 "docs/research/experiments/2026-10-08-e009-split-charge.md")
    if not (0 <= a.pct_lo < a.pct_hi <= 100):
        ap.error(f"need 0 <= --pct-lo < --pct-hi <= 100, got {a.pct_lo} and {a.pct_hi}")
    set_arms(a.pct_lo, a.pct_hi)
    OUT, TICKS = a.out, a.ticks
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = range(1, a.seeds + 1)
    jobs = [(arm, s) for arm in ARM_NAMES for s in seeds]

    e004.OUT = OUT
    e004.ARMS = dict(ARMS)
    exe = binary()
    if not a.analyse_only and not a.windows_only:
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda j: run_one(exe, j[0], j[1], a.ticks, a.force), jobs):
                print(msg, flush=True)

    # classes.csv was written under the arm's physics, which is the world's,
    # so classes_world.csv (which E005's analysis reads) is a copy of it.
    for arm, s in jobs:
        d = run_dir(arm, s)
        if (d / "classes.csv").exists() and not (d / "classes_world.csv").exists():
            shutil.copyfile(d / "classes.csv", d / "classes_world.csv")

    e005.RUNS = OUT
    e005.OUT = OUT
    e005.ARMS = dict(ARMS)  # run-time only: E005's host harness and world classify use these arms' flags
    if a.windows_only:
        persist = pl.read_csv(OUT / "runs_e004.csv")
    else:
        rows = [e004.metrics(arm, s, a.ticks) for arm, s in jobs if (run_dir(arm, s) / "classes.csv").exists()]
        persist = pl.DataFrame(rows)
        persist.write_csv(OUT / "runs_e004.csv")
        text = e004.summarize(a.seeds, a.ticks, list(ARM_NAMES)).replace("E004 summary", "E009 persistence (E004 measures)")
        (OUT / "summary_e004.md").write_text(text + "\n", encoding="utf-8")
        print(text)
        e005.run_all(list(ARM_NAMES), a.seeds, min(a.jobs, 8), host=True)

    wrows = []
    for arm, s in jobs:
        if dep_path(arm, s).exists():
            t0 = time.time()
            wrows += windows(arm, s, exe)
            print(f"{arm}/s{s}: windows done ({time.time() - t0:.0f} s)", flush=True)
    wdf = pl.DataFrame(wrows, infer_schema_length=None)
    wdf.write_csv(OUT / "windows.csv")
    text = summarize_windows(wdf, persist)
    (OUT / "summary_windows.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
