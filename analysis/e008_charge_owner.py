"""E008: parasitism that costs the host. Runs seeds 1-10 of the standard
world (the code default, E007) with `--charge-owner` (the living owner of
the byte at IP pays for an instruction another organism executes there)
for 250,000 ticks, records and classifies each run, applies the E004
persistence and E005 parasite measures to the whole run, and reads each
run in windows of 25,000 ticks with every E007 window measure plus the
E008 ones: the defence probe (the one-byte `pad` before the window's top
host in the two-genome harness), the share of replicator-class deaths
that had paid for others, the share of spent energy paid for others, and
foreign and unowned execution shares over living bodies.

Usage (from analysis/):

    uv run e008_charge_owner.py                 # build, run, classify, analyse
    uv run e008_charge_owner.py --analyse-only  # runs exist; redo the tables
    uv run e008_charge_owner.py --seeds 3
    uv run e008_charge_owner.py --seeds 1 --ticks 50000 --out /tmp/x  # smoke test only

Run directories: runs/e008/co/s<seed>/. Output: runs/e008/runs_e004.csv
and summary_e004.md (persistence, as E004), runs.csv and summary.md
(parasites, as E005), windows.csv and summary_windows.md (per-window
measures, the E007 tables, the E008 table and the prediction checks).
Protocol and predictions:
docs/research/experiments/2026-10-07-e008-charge-owner.md.

Physics in the harness. Every harness call uses the arm's physics
(`--charge-owner`): the single-genome classifier that writes classes.csv
(so "replicator-class" means a replicator under this physics; a lone
genome executes no foreign code, so the flag should change little there),
the E005 world classes (classes_world.csv, a copy of classes.csv, as in
E007), the E005 host harness (`e005.ARMS` is pointed at this arm at run
time; E005's registered arms are not edited), the resistance test and the
probe.

Deaths are joined to classes by `birth_hash` (as E004's death tables do):
`now_hash`, the body at death, is not always in genomes.csv
(docs/instrumentation.md), and `birth_hash` always is. A host whose body
changed after birth is classed by its birth genome. The share of energy
paid for others is a proxy over deaths in the window: sum of
`paid_for_others_m` over those deaths / sum of their `spent_m` (lifetime
totals of the organisms that died in the window, so a death early in a
window carries spending from the previous one). Foreign and unowned
execution shares are lifetime counters summed over the bodies alive at
the window's last census.

Exploratory, for prediction 7: the probe's host death tick
(`probe_host_death_tick`, the first `--harness-ticks` value at which the
host is dead, found by bisection; the harness itself reports only
`ticks_run`, which is when the intruder died or the run ended), the share
of exact births by one-byte genomes per window, and the deepest one-byte
dependent lineage per run.
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

OUT = ROOT / "runs" / "e008"
ARM = "co"
FLAGS = ["--charge-owner"]  # world run, --classify and every --host call
TICKS = 250_000
WINDOW = 25_000
LATE_FROM = 200_000  # E007's per-seed column: parasite genomes first born after this tick
PROBE = "00"  # the one-byte `pad`
DEFENDED_MIN = 50  # prediction 5: host exact births with the probe present


def run_one(exe: Path, seed: int, ticks: int, force: bool) -> str:
    """E004's run_one with the arm's flags passed to `--classify` too."""
    d = OUT / ARM / f"s{seed}"
    if not force and (d / "classes.csv").exists():
        return f"{ARM}/s{seed}: done"
    t0 = time.time()
    if force or not (d / "genomes.csv").exists():
        if d.exists():
            shutil.rmtree(d)
        d.parent.mkdir(parents=True, exist_ok=True)
        cmd = [str(exe), "--ticks", str(ticks), "--seed", str(seed), "--report", str(e004.CENSUS),
               "--census", str(e004.CENSUS), "--out", str(d), *FLAGS]
        with open(d.parent / f"s{seed}.stdout", "w") as out:
            subprocess.run(cmd, stdout=out, stderr=subprocess.DEVNULL, check=True)
    t1 = time.time()
    subprocess.run([str(exe), "--classify", str(d), "--harness-ticks", str(e005.HARNESS_TICKS), *FLAGS],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return f"{ARM}/s{seed}: run {t1 - t0:.0f} s, classify {time.time() - t1:.0f} s"


def host_harness(exe: Path, genome_hex: str, host_hex: str | None, ticks: int = e005.HARNESS_TICKS) -> dict:
    """Two-genome harness under the arm's physics: `genome_hex` placed right
    before `host_hex` (the ancestor when None), quiet, `ticks` ticks."""
    cmd = [str(exe), "--host", genome_hex, "--harness-ticks", str(ticks), *FLAGS]
    if host_hex is not None:
        cmd += ["--host-body", host_hex]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    header, row = out.strip().splitlines()[:2]
    vals = dict(zip(header.split(","), row.split(",")))
    return {k: (v == "true" if v in ("true", "false") else int(v)) for k, v in vals.items()}


def host_death_tick(exe: Path, genome_hex: str, host_hex: str) -> int | None:
    """First harness length at which the host is dead (None if alive after
    the full run). The harness is deterministic and death is final, so
    `host_alive` is monotone in the length and bisection finds it."""
    if host_harness(exe, genome_hex, host_hex)["host_alive"]:
        return None
    lo, hi = 0, e005.HARNESS_TICKS  # alive at lo (0 ticks), dead at hi
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if host_harness(exe, genome_hex, host_hex, mid)["host_alive"]:
            lo = mid
        else:
            hi = mid
    return hi


def windows(seed: int, exe: Path | None) -> list[dict]:
    """Per-window measures for one run. Needs classes.csv and the E005
    dependent table (runs/e008/co_s<seed>_dependent.csv)."""
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
    known = set(hexes)

    b = run.births.with_columns(
        exact=pl.col("raw_hash") == pl.col("parent_now_hash"),
        win=((pl.col("tick") + WINDOW - 1) // WINDOW).cast(pl.Int64),
    )
    exact_all = run.class_of(b.filter(pl.col("exact")), "raw_hash")
    first_tick = dict(exact_all.group_by("raw_hash").agg(pl.col("tick").min()).iter_rows())
    orgs = run.class_of(run.orgs, "now_hash")
    tr = {r["bin"]: r for r in traits.track(run, WINDOW).iter_rows(named=True)}
    deaths = run.class_of(run.deaths, "birth_hash").with_columns(
        win=((pl.col("tick") + WINDOW - 1) // WINDOW).cast(pl.Int64),
        paid=pl.col("paid_for_others_m") > 0,
        now_known=pl.col("now_hash").is_in(list(known)),
    )

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

        # --- E008 measures ---------------------------------------------------
        # Defence probe: `pad` before the window's top host.
        r.update(probe_exact=None, host_exact_with_probe=None, host_alive=None, probe_ticks_run=None,
                 probe_stopped_early=None, defended=None, probe_host_death_tick=None)
        if exe and top:
            p = host_harness(exe, PROBE, hexes[top["raw_hash"]])
            r.update(
                probe_exact=p["exact_births"],
                host_exact_with_probe=p["host_exact_births"],
                host_alive=p["host_alive"],
                probe_ticks_run=p["ticks_run"],
                probe_stopped_early=p["stopped_early"],
                defended=p["host_alive"] and p["host_exact_births"] >= DEFENDED_MIN and not p["stopped_early"],
                probe_host_death_tick=None if p["host_alive"] else host_death_tick(exe, PROBE, hexes[top["raw_hash"]]),
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
    yn = lambda ok: "yes" if ok else "no"
    surviving = sorted(persist.filter(pl.col("replicating"))["seed"].to_list())
    n_surv = len(surviving)
    live = wdf.filter(pl.col("seed").is_in(surviving))
    n_windows = int(wdf["window"].max())
    last = n_windows

    lines = [
        f"E008 windows (`{' '.join(FLAGS)}`): {wdf['seed'].n_unique()} seeds x {TICKS:,} ticks in windows of "
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
        p = persist.filter(pl.col("seed") == seed).row(0, named=True)
        tops = x["top_hash"].to_list()
        sweeps = sum(1 for a, b_ in zip(tops, tops[1:]) if a is not None and b_ is not None and a != b_)
        main_len = None
        dep = pl.read_csv(OUT / f"{ARM}_s{seed}_dependent.csv", schema_overrides={"raw_hash": pl.Utf8, "bytes_hex": pl.Utf8})
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
        "E008 measures. Medians across the same seeds except the defended column (count of seeds). Probe: `pad` "
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
    cnt = lambda x, col: int(x[col].drop_nulls().sum()) if x[col].drop_nulls().len() else 0
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
        "| host death tick, last | defended windows (of 10) | replicator deaths that paid, window 1 / 2 / last "
        "| last / window 2 | deepest one-byte dependent lineage | one-byte dependent exact births | one-byte parasites |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    p5_def = 0
    p6_ok = 0
    for seed in order:
        x = wdf.filter(pl.col("seed") == seed).sort("window")
        val = lambda col, w: x.filter(pl.col("window") == w)[col][0] if x.filter(pl.col("window") == w).height else None
        r2, rl = val("rep_deaths_paid_share", 2), val("rep_deaths_paid_share", last)
        ratio = rl / r2 if (r2 and rl is not None) else None
        dl = val("defended", last)
        if seed in surviving:
            p5_def += bool(dl)
            p6_ok += ratio is not None and 0.5 <= ratio <= 2
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

    # Prediction checks (record: E008 "Predictions").
    surv_persist = persist.filter(pl.col("replicating"))
    pop_end_med = surv_persist["pop_end"].median() if n_surv else None
    p1 = n_surv >= 7 and pop_end_med is not None and 700 <= pop_end_med <= 1100

    ab = lambda s, w: (live.filter((pl.col("seed") == s) & (pl.col("window") == w))["absorb_med"].to_list() or [None])[0]
    w1_ok = sum(1 for s in surviving if (v := ab(s, 1)) is not None and v >= 96)
    w2_ok = sum(1 for s in surviving if (v := ab(s, 2)) is not None and v >= 112)
    w1_med = _med(live.filter(pl.col("window") == 1), "absorb_med")
    w2_med = _med(live.filter(pl.col("window") == 2), "absorb_med")
    p2 = w1_ok >= 8 and w2_ok >= 8

    later = range(2, n_windows + 1)
    par_meds = [_med(live.filter(pl.col("window") == w), "par_share") for w in later]
    tramp_meds = [_med(live.filter(pl.col("window") == w), "tramp_share") for w in later]
    dep_meds = [_med(live.filter(pl.col("window") == w), "dep_share") for w in later]
    dep_w1 = _med(live.filter(pl.col("window") == 1), "dep_share")
    p3a = all(v is not None and v < 0.003 for v in par_meds)
    p3b = all(v is not None and v >= 0.025 for v in tramp_meds)
    p3c = all(v is not None and v >= 0.05 for v in dep_meds)

    paid_w1 = _med(live.filter(pl.col("window") == 1), "rep_deaths_paid_share")
    p4 = paid_w1 is not None and paid_w1 >= 0.05

    host_last = _med(live.filter(pl.col("window") == last), "host_exact_with_probe")
    p5 = p5_def <= 2 and host_last is not None and host_last < DEFENDED_MIN

    paid_w2 = _med(live.filter(pl.col("window") == 2), "rep_deaths_paid_share")
    paid_last = _med(live.filter(pl.col("window") == last), "rep_deaths_paid_share")
    p6 = p6_ok >= 7

    lines += [
        "",
        "Prediction checks (medians across surviving seeds unless counted in seeds):",
        "",
        f"1. Replicating at the end in {n_surv} of {persist.height} (>= 7 wanted); population at end, median over "
        f"surviving seeds {f0(pop_end_med)} (700–1,100 wanted). Holds: {yn(p1)}.",
        f"2. Absorb median of replicator-class exact births >= 96 in window 1 in {w1_ok} of {n_surv} surviving seeds "
        f"and >= 112 in window 2 in {w2_ok} of {n_surv} (>= 8 each wanted); medians across seeds {f0(w1_med)} and "
        f"{f0(w2_med)}. Holds: {yn(p2)}.",
        f"3. Parasite share medians, windows 2–{last}: {', '.join(pct(v) for v in par_meds)} (all < 0.3%: {yn(p3a)}); "
        f"trampoline share medians: {', '.join(f3(v) for v in tramp_meds)} (all >= 0.025: {yn(p3b)}); dependent "
        f"share medians: {', '.join(f3(v) for v in dep_meds)} (all >= 0.05: {yn(p3c)}; window 1 {f3(dep_w1)}). "
        f"Holds: {yn(p3a and p3b and p3c)}.",
        f"4. Replicator-class deaths with paid_for_others > 0, window 1: {pct(paid_w1)} (>= 5% wanted). Holds: {yn(p4)}.",
        f"5. Defended top host in the last window in {p5_def} of {n_surv} surviving seeds (<= 2 wanted); host exact "
        f"births with `pad` present, last window, median {f0(host_last)} (< {DEFENDED_MIN} wanted). Holds: {yn(p5)}.",
        f"6. Replicator deaths that paid, last window within a factor of 2 of window 2 in {p6_ok} of {n_surv} "
        f"surviving seeds (>= 7 wanted); medians window 2 {pct(paid_w2)}, last {pct(paid_last)}. Holds: {yn(p6)}.",
    ]
    return "\n".join(lines)


def main() -> None:
    global OUT, TICKS
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=TICKS, help="override for smoke tests only")
    ap.add_argument("--out", type=Path, default=OUT, help="output root (smoke tests only)")
    ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--windows-only", action="store_true", help="reuse runs.csv and runs_e004.csv")
    a = ap.parse_args()
    OUT, TICKS = a.out, a.ticks
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = range(1, a.seeds + 1)

    e004.OUT = OUT
    e004.ARMS = {ARM: FLAGS}
    exe = binary()
    if not a.analyse_only and not a.windows_only:
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda s: run_one(exe, s, a.ticks, a.force), seeds):
                print(msg, flush=True)

    # classes.csv was written under the arm's physics, which is the world's,
    # so classes_world.csv (which E005's analysis reads) is a copy of it.
    for s in seeds:
        d = OUT / ARM / f"s{s}"
        if (d / "classes.csv").exists() and not (d / "classes_world.csv").exists():
            shutil.copyfile(d / "classes.csv", d / "classes_world.csv")

    e005.RUNS = OUT
    e005.OUT = OUT
    e005.ARMS = {ARM: FLAGS}  # run-time only: E005's host harness and world classify use this arm's flags
    if a.windows_only:
        persist = pl.read_csv(OUT / "runs_e004.csv")
    else:
        rows = [e004.metrics(ARM, s, a.ticks) for s in seeds if (OUT / ARM / f"s{s}" / "classes.csv").exists()]
        persist = pl.DataFrame(rows)
        persist.write_csv(OUT / "runs_e004.csv")
        text = e004.summarize(a.seeds, a.ticks, [ARM]).replace("E004 summary", "E008 persistence (E004 measures)")
        (OUT / "summary_e004.md").write_text(text + "\n", encoding="utf-8")
        print(text)
        e005.run_all([ARM], a.seeds, min(a.jobs, 8), host=True)

    wrows = []
    for s in seeds:
        if (OUT / f"{ARM}_s{s}_dependent.csv").exists():
            t0 = time.time()
            wrows += windows(s, exe)
            print(f"{ARM}/s{s}: windows done ({time.time() - t0:.0f} s)", flush=True)
    wdf = pl.DataFrame(wrows, infer_schema_length=None)
    wdf.write_csv(OUT / "windows.csv")
    text = summarize_windows(wdf, persist)
    (OUT / "summary_windows.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
