"""E012: the standard world without write protection. Runs seeds 1-10 of
the code's default physics (the E007 world) with `--no-protect` for
100,000 ticks, records and classifies each run twice (`--classify`, default
physics, classes.csv; `--classify --no-protect`, classes_world.csv), applies
the E004 persistence and E005 parasite measures to the whole run and E007's
window measures to windows of 25,000 ticks, adds the foreign-write measures
(`writes_foreign`, `overwritten`), reads the E007 control (seeds 1-10,
windows 1-4, `writes_blocked` in place of `writes_foreign`), and checks the
record's predictions and its H4 scoring rule.

Usage (from analysis/; cargo must be on PATH):

    uv run e012_no_protect.py                  # build, run, classify, analyse, summarise
    uv run e012_no_protect.py --sims-only      # runs and both classifies only
    uv run e012_no_protect.py --analyse-only   # runs exist; redo every table
    uv run e012_no_protect.py --summary-only   # reuse the CSVs; rewrite summary_e012.md
    uv run e012_no_protect.py --seeds 1 --ticks 2000 --window 500 --control-seeds 1 \
        --out ../runs/e012/smoke                # smoke test only

Run directories: runs/e012/noprot/s<seed>/. Outputs in runs/e012/:
timing.csv (wall time per run: simulation, default classify, world
classify), classes_check.csv (classes.csv against classes_world.csv),
runs_e004.csv and summary_e004.md (persistence, as E004), runs.csv,
summary.md and noprot_s<seed>_dependent.csv (parasites, as E005),
windows.csv and summary_windows.md (E007's window measures plus the E012
columns below), writes_run.csv (whole-run write measures),
noprot_s<seed>_writers.csv (the 20 genomes with the most foreign writes),
control.csv and control_run.csv (E007 seeds 1-10 to tick 100,000), and
summary_e012.md (tables, prediction checks, H4 scoring). Protocol and
predictions: docs/research/experiments/2026-10-12-e012-no-protect.md.

Reuse: e004_physics.run_one / metrics / summarize, e005_parasites.run_all
and ensure_world_classes, and e007_long_run.windows / summarize_windows,
with their module globals pointed at runs/e012 and the arm `noprot`
(`--no-protect`). E007's resistance-harness columns in windows.csv
(`main_par_vs_top`, `resistance`, ...) are kept as E007 computes them,
with the two-genome harness under default physics (protection on).

Definitions added here (each window holds ticks (lo, hi], as E007):

  carriers          organisms born with genome G (birth_hash): deaths.csv
                    plus orgs.csv at the final census (as E005)
  window of a death the death tick's window ("by death tick")
  writes_foreign    sum of `writes_foreign` over the deaths in the window;
                    `writers` the number of those deaths with
                    writes_foreign > 0; `overwritten_share` the share of
                    the window's deaths with `overwritten` > 0
  writer class      replicator (classes_world.csv class `replicator`),
                    dependent (in the E005 dependent table and not
                    replicator; `wf_par` is the parasite_2 subset of
                    it), other (the rest); of the carrier's birth genome
  top canonical, any class
                    the canonical genotype (`func_hash`) with the most of
                    the window's exact births, any harness class, and its
                    share of them (`top_func_share_any`). E007's
                    `top_func_share` (traits.py) takes the leader among
                    replicator-class exact births only; both are kept.
                    The record says "the leading canonical genotype", so
                    the predictions and the H4 rule use the any-class one.
  foreign-write rate
                    per genome, sum writes_foreign / sum executed over its
                    carriers (executed > 0). The 99th percentile (linear
                    interpolation) is taken over the genomes with at least
                    one carrier with writes_foreign > 0 ("writing
                    genomes"); a genome is high-rate if its rate is
                    strictly above it. The same over every genome with
                    executed > 0 is reported second (`_all`).
  control           E007 seeds 1-10 (runs/e007/std/s<seed>/), deaths with
                    tick <= 100,000 and living bodies at the census of
                    tick 100,000; per-window E007 columns from
                    runs/e007/windows.csv.
"""

from __future__ import annotations

import argparse
import filecmp
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

import e004_physics as e004
import e005_parasites as e005
import e007_long_run as e007
from evo_run import ROOT, binary

OUT = ROOT / "runs" / "e012"
ARM = "noprot"
FLAGS = ["--no-protect"]
TICKS = 100_000
WINDOW = 25_000

CONTROL = ROOT / "runs" / "e007"
CONTROL_ARM = "std"
CONTROL_TICKS = 100_000
CONTROL_WINDOW = 25_000

# Prediction thresholds (record: "Predictions" and "Scoring H4").
P1_SEEDS, P1_POP = 8, (700, 1100)
P2_TOP, P2_GENO = 0.25, 1000
P3_RATIO = (0.67, 1.5)
P4_RATIO = (0.5, 2.0)
P5_PAR = (0.001, 0.03)
P6_ABSORB, P6_SEEDS = 112, 8
H4_TAKEOVER, H4_SEEDS = 0.5, 6
RATE_Q, RATE_SHARE = 0.99, 0.01

WCOLS = ["executed", "writes_foreign", "overwritten", "writes_blocked"]


def _scan(path: Path, cols: list[str], hashes: tuple[str, ...] = (), text: tuple[str, ...] = ()) -> pl.LazyFrame:
    """Selected columns of a run CSV; hashes read as text, every other
    column cast to Int64 (a header-only file would infer text)."""
    lf = pl.scan_csv(path, schema_overrides={c: pl.Utf8 for c in hashes}).select(cols)
    return lf.with_columns(pl.col(c).cast(pl.Int64) for c in cols if c not in hashes and c not in text)


def _win(window: int) -> pl.Expr:
    return ((pl.col("tick") + window - 1) // window).cast(pl.Int64).alias("win")


# --- runs ---------------------------------------------------------------------


def sim_one(exe: Path, seed: int, ticks: int, force: bool) -> dict:
    """Run, classify (default physics) and classify under the world's
    physics; return the wall times (None where a step was skipped)."""
    msg = e004.run_one(exe, ARM, seed, ticks, force)
    t1 = time.time()
    msg2 = e005.ensure_world_classes(exe, ARM, seed)
    t2 = time.time()
    m = re.search(r"run (\d+) s, classify (\d+) s", msg)
    print(f"{msg}; {msg2}" + (f" in {t2 - t1:.0f} s" if "classified" in msg2 else ""), flush=True)
    return dict(
        seed=seed,
        sim_s=int(m[1]) if m else None,
        classify_s=int(m[2]) if m else None,
        classify_world_s=round(t2 - t1) if "classified" in msg2 else None,
    )


def compare_classes(seed: int) -> dict:
    """Are classes.csv and classes_world.csv the same file? If not, how many
    genomes change class and how many rows differ at all."""
    d = OUT / ARM / f"s{seed}"
    a, b = d / "classes.csv", d / "classes_world.csv"
    same = filecmp.cmp(a, b, shallow=False)
    out = dict(seed=seed, identical=same, genomes=e005._rows(a), class_differs=0, rows_differ=0, cols_differ="")
    if not same:
        x = pl.read_csv(a, schema_overrides={"raw_hash": pl.Utf8})
        y = pl.read_csv(b, schema_overrides={"raw_hash": pl.Utf8})
        j = x.join(y, on="raw_hash", how="full", suffix="_w", coalesce=True)
        out["class_differs"] = int((j["class"] != j["class_w"]).fill_null(True).sum())
        ne = {c: (pl.col(c) != pl.col(f"{c}_w")).fill_null(True) for c in x.columns if c != "raw_hash"}
        out["rows_differ"] = int(j.select(pl.any_horizontal(list(ne.values())).sum()).item())
        out["cols_differ"] = " ".join(c for c, e in ne.items() if j.select(e.any()).item())
    return out


# --- E012 write measures --------------------------------------------------------


def concentration(df: pl.DataFrame, col: str, prefix: str) -> dict:
    """How the writes in `col` are spread over the carriers that made any
    (one row per carrier): median and max per writer, the share of all of
    them made by the top 1% of writers (at least one), and the share made by
    carriers whose body had changed since birth (now_hash != birth_hash)."""
    w = df.filter(pl.col(col) > 0).sort(col, descending=True)
    tot = int(w[col].sum()) if w.height else 0
    k = max(1, w.height // 100)
    return {
        f"{prefix}_per_writer_med": w[col].median() if w.height else None,
        f"{prefix}_max_carrier": int(w[col].max()) if w.height else 0,
        f"{prefix}_top1pct_share": int(w[col].head(k).sum()) / tot if tot else None,
        f"{prefix}_changed_share": int(w.filter(pl.col("now_hash") != pl.col("birth_hash"))[col].sum()) / tot
        if tot else None,
    }


def writes(seed: int, ticks: int, window: int) -> tuple[list[dict], dict]:
    """Per-window and whole-run foreign-write measures for one noprot run
    (module docstring). Writes noprot_s<seed>_writers.csv."""
    d = OUT / ARM / f"s{seed}"
    n_w = ticks // window
    final = _scan(d / "patches.csv", ["tick"]).select(pl.col("tick").max()).collect().item()
    world = pl.read_csv(d / "classes_world.csv", columns=["raw_hash", "class"], schema_overrides={"raw_hash": pl.Utf8})
    dep = pl.read_csv(OUT / f"{ARM}_s{seed}_dependent.csv", columns=["raw_hash", "parasite_2"],
                      schema_overrides={"raw_hash": pl.Utf8})
    dep = dep.select(
        birth_hash=pl.col("raw_hash"),
        dep=pl.lit(True),
        par=pl.col("parasite_2").cast(pl.Utf8).str.to_lowercase() == "true",
    )

    def classed(df: pl.DataFrame) -> pl.DataFrame:
        df = df.join(world.rename({"raw_hash": "birth_hash"}), on="birth_hash", how="left")
        df = df.join(dep, on="birth_hash", how="left").with_columns(
            pl.col("dep").fill_null(False), pl.col("par").fill_null(False), pl.col("class").fill_null("unknown")
        )
        return df.with_columns(
            grp=pl.when(pl.col("class") == "replicator").then(pl.lit("replicator"))
            .when(pl.col("dep")).then(pl.lit("dependent")).otherwise(pl.lit("other"))
        )

    hc = ("birth_hash", "now_hash")
    deaths = classed(_scan(d / "deaths.csv", ["tick", "age", *hc, *WCOLS], hc).collect())
    deaths = deaths.with_columns(_win(window), ow=pl.col("overwritten") > 0)
    living = _scan(d / "orgs.csv", ["tick", *hc, *WCOLS], hc).filter(pl.col("tick") == final).collect()

    wf = pl.col("writes_foreign")

    def agg(df: pl.DataFrame, by: list[str]) -> pl.DataFrame:
        exprs = dict(
            deaths=pl.len(),
            writes_foreign=wf.sum(),
            writers=(wf > 0).sum(),
            writes_blocked=pl.col("writes_blocked").sum(),
            overwritten=pl.col("overwritten").sum(),
            n_overwritten=pl.col("ow").sum(),
            overwritten_share=pl.col("ow").mean(),
            wf_rep=wf.filter(pl.col("grp") == "replicator").sum(),
            wf_dep=wf.filter(pl.col("grp") == "dependent").sum(),
            wf_par=wf.filter(pl.col("par") & (pl.col("grp") == "dependent")).sum(),
            wf_other=wf.filter(pl.col("grp") == "other").sum(),
            writers_rep=((wf > 0) & (pl.col("grp") == "replicator")).sum(),
            writers_dep=((wf > 0) & (pl.col("grp") == "dependent")).sum(),
            writers_other=((wf > 0) & (pl.col("grp") == "other")).sum(),
            age_med_overwritten=pl.col("age").filter(pl.col("ow")).median(),
            age_med_rest=pl.col("age").filter(~pl.col("ow")).median(),
        )
        if by:
            return df.group_by(by).agg(**exprs)
        return df.select(**exprs)

    in_run = deaths.filter((pl.col("win") >= 1) & (pl.col("win") <= n_w))
    per_w = agg(in_run, ["win"])

    # Exact births per window, canonical leader of any class.
    ex = (
        _scan(d / "births.csv", ["tick", "raw_hash", "parent_now_hash"], ("raw_hash", "parent_now_hash"))
        .filter(pl.col("raw_hash") == pl.col("parent_now_hash"))
        .select("tick", "raw_hash", _win(window))
        .collect()
    )
    gen = _scan(d / "genomes.csv", ["raw_hash", "func_hash"], ("raw_hash", "func_hash")).collect()
    ex = ex.join(gen, on="raw_hash", how="left")
    n_ex = ex.group_by("win").agg(exact=pl.len())
    top = (
        ex.group_by("win", "func_hash").len()
        .sort(["win", "len", "func_hash"], descending=[False, True, False])
        .group_by("win", maintain_order=True).first()
        .join(n_ex, on="win")
        .select("win", top_func_hash_any="func_hash", top_func_share_any=pl.col("len") / pl.col("exact"))
    )

    # Foreign-write rate per genome over its carriers.
    carriers = pl.concat([deaths.select("birth_hash", *WCOLS), living.select("birth_hash", *WCOLS)])
    per_g = (
        carriers.group_by("birth_hash")
        .agg(carriers=pl.len(), writers=(wf > 0).sum(), wf=wf.sum(), ow=pl.col("overwritten").sum(),
             executed=pl.col("executed").sum())
        .filter(pl.col("executed") > 0)
        .with_columns(rate=pl.col("wf") / pl.col("executed"))
    )
    writing = per_g.filter(pl.col("writers") >= 1)
    g_ex = ex.group_by("win", "raw_hash").len().join(n_ex, on="win").with_columns(
        share=pl.col("len") / pl.col("exact")
    ).rename({"raw_hash": "birth_hash"})

    def high_rate(pool: pl.DataFrame, tag: str) -> tuple[dict, pl.DataFrame]:
        q = pool["rate"].quantile(RATE_Q, "linear") if pool.height else None
        hi = pool.filter(pl.col("rate") > q) if q is not None else pool.clear()
        sh = g_ex.join(hi.select("birth_hash", "rate"), on="birth_hash", how="inner")
        best = sh.sort("share", descending=True).row(0, named=True) if sh.height else None
        win_max = sh.group_by("win").agg(pl.col("share").max().alias(f"high_{tag}_share_max"))
        return {
            f"p99_{tag}": q,
            f"n_pool_{tag}": pool.height,
            f"n_high_{tag}": hi.height,
            f"n_high_{tag}_exact": int(sh["birth_hash"].n_unique()) if sh.height else 0,
            f"high_{tag}_share_max": best["share"] if best else 0.0,
            f"high_{tag}_share_max_win": best["win"] if best else None,
            f"high_{tag}_share_max_hash": best["birth_hash"] if best else None,
            f"high_{tag}_share_max_rate": best["rate"] if best else None,
            f"high_{tag}_reaches_1pct": bool(best and best["share"] >= RATE_SHARE),
            f"high_{tag}_windows_1pct": int(sh.filter(pl.col("share") >= RATE_SHARE)["win"].n_unique()) if sh.height else 0,
        }, win_max

    hw, hw_win = high_rate(writing, "writing")
    ha, ha_win = high_rate(per_g, "all")

    # The 20 genomes with the most foreign writes.
    exact_g = ex.group_by("raw_hash").agg(exact_births=pl.len()).rename({"raw_hash": "birth_hash"})
    top_w = classed(writing.sort("wf", descending=True).head(20)).join(exact_g, on="birth_hash", how="left")
    names = _scan(d / "genomes.csv", ["raw_hash", "len", "disasm"], ("raw_hash",), ("disasm",)).filter(
        pl.col("raw_hash").is_in(top_w["birth_hash"].to_list())
    ).collect().rename({"raw_hash": "birth_hash"})
    top_w = top_w.join(names, on="birth_hash", how="left").with_columns(pl.col("exact_births").fill_null(0)).sort("wf", descending=True)
    top_w.select("birth_hash", "len", "class", "grp", "dep", "par", "carriers", "writers", "wf", "executed", "rate",
                 "ow", "exact_births", "disasm").write_csv(OUT / f"{ARM}_s{seed}_writers.csv")

    rows = []
    pw = {r["win"]: r for r in per_w.join(top, on="win", how="full", coalesce=True)
          .join(hw_win, on="win", how="left").join(ha_win, on="win", how="left").iter_rows(named=True)}
    for w in range(1, n_w + 1):
        r = pw.get(w, {})
        row = {k: r.get(k) for k in per_w.columns if k != "win"}
        for k in ("deaths", "writes_foreign", "writers", "writes_blocked", "overwritten", "n_overwritten",
                  "wf_rep", "wf_dep", "wf_par", "wf_other", "writers_rep", "writers_dep", "writers_other"):
            row[k] = int(row[k] or 0)
        row.update(
            seed=seed, window=w,
            top_func_hash_any=r.get("top_func_hash_any"),
            top_func_share_any=r.get("top_func_share_any"),
            high_writing_share_max=r.get("high_writing_share_max") or 0.0,
            high_all_share_max=r.get("high_all_share_max") or 0.0,
        )
        rows.append(row)

    tot = agg(deaths, []).row(0, named=True)
    wf_d, ow_d = int(deaths["writes_foreign"].sum()), int(deaths["overwritten"].sum())
    wf_l, ow_l = int(living["writes_foreign"].sum()), int(living["overwritten"].sum())
    run = dict(
        seed=seed,
        final_tick=final,
        deaths=deaths.height,
        living=living.height,
        wf_deaths=int(deaths.filter(pl.col("tick") <= ticks)["writes_foreign"].sum()),
        wf_living=wf_l,
        ow_deaths=ow_d,
        ow_living=ow_l,
        wf_total=wf_d + wf_l,
        ow_total=ow_d + ow_l,
        wf_eq_ow=(wf_d + wf_l) == (ow_d + ow_l),
        wb_deaths=int(deaths["writes_blocked"].sum()),
        writers_deaths=int(tot["writers"]),
        n_overwritten_deaths=int(tot["n_overwritten"]),
        overwritten_share=tot["overwritten_share"],
        wf_rep=int(tot["wf_rep"]), wf_dep=int(tot["wf_dep"]), wf_par=int(tot["wf_par"]), wf_other=int(tot["wf_other"]),
        writers_rep=int(tot["writers_rep"]), writers_dep=int(tot["writers_dep"]), writers_other=int(tot["writers_other"]),
        age_med_overwritten=tot["age_med_overwritten"],
        age_med_rest=tot["age_med_rest"],
        writing_genomes=writing.height,
        genomes_executed=per_g.height,
        **hw, **ha,
        # Deaths only, as the control's writes_blocked.
        **concentration(deaths, "writes_foreign", "wf"),
    )
    return rows, run


# --- control: E007 to tick 100,000 ----------------------------------------------


def control_one(seed: int) -> tuple[list[dict], dict]:
    """E007 seed `seed` to CONTROL_TICKS: writes_blocked by death window,
    the any-class canonical leader, and a recomputation of E007's
    replicator-class leader and canonical genotype count (to check this
    code against runs/e007/windows.csv)."""
    d = CONTROL / CONTROL_ARM / f"s{seed}"
    n_w = CONTROL_TICKS // CONTROL_WINDOW
    deaths = (
        _scan(d / "deaths.csv", ["tick", "age", "birth_hash", "now_hash", "writes_blocked"], ("birth_hash", "now_hash"))
        .filter(pl.col("tick") <= CONTROL_TICKS)
        .with_columns(_win(CONTROL_WINDOW))
        .collect()
    )
    living = _scan(d / "orgs.csv", ["tick", "writes_blocked"]).filter(pl.col("tick") == CONTROL_TICKS).collect()
    wb = pl.col("writes_blocked")
    per_w = deaths.filter(pl.col("win") >= 1).group_by("win").agg(
        c_deaths=pl.len(), writes_blocked=wb.sum(), blockers=(wb > 0).sum()
    )
    ex = (
        _scan(d / "births.csv", ["tick", "raw_hash", "parent_now_hash"], ("raw_hash", "parent_now_hash"))
        .filter((pl.col("raw_hash") == pl.col("parent_now_hash")) & (pl.col("tick") <= CONTROL_TICKS))
        .select("tick", "raw_hash", _win(CONTROL_WINDOW))
        .collect()
    )
    gen = _scan(d / "genomes.csv", ["raw_hash", "func_hash"], ("raw_hash", "func_hash")).collect()
    cls = pl.read_csv(d / "classes.csv", columns=["raw_hash", "class"], schema_overrides={"raw_hash": pl.Utf8})
    ex = ex.join(gen, on="raw_hash", how="left").join(cls, on="raw_hash", how="left")
    n_ex = ex.group_by("win").agg(c_exact=pl.len())

    def leader(df: pl.DataFrame, name: str) -> pl.DataFrame:
        return (
            df.group_by("win", "func_hash").len()
            .sort(["win", "len", "func_hash"], descending=[False, True, False])
            .group_by("win", maintain_order=True).first()
            .join(n_ex, on="win")
            .select("win", **{f"{name}_hash": "func_hash", f"{name}_share": pl.col("len") / pl.col("c_exact")})
        )

    top_any = leader(ex, "c_top_any")
    top_rep = leader(ex.filter(pl.col("class") == "replicator"), "c_top_rep")
    geno = ex.group_by("win", "func_hash").len().filter(pl.col("len") >= 2).group_by("win").agg(c_geno_func=pl.len())
    tab = (
        per_w.join(n_ex, on="win", how="full", coalesce=True)
        .join(top_any, on="win", how="left").join(top_rep, on="win", how="left").join(geno, on="win", how="left")
    )
    by_w = {r["win"]: r for r in tab.iter_rows(named=True)}
    rows = []
    for w in range(1, n_w + 1):
        r = by_w.get(w, {})
        rows.append(dict(
            seed=seed, window=w,
            c_deaths=int(r.get("c_deaths") or 0),
            c_writes_blocked=int(r.get("writes_blocked") or 0),
            c_blockers=int(r.get("blockers") or 0),
            c_exact_check=int(r.get("c_exact") or 0),
            c_top_func_share_any=r.get("c_top_any_share"),
            c_top_func_hash_any=r.get("c_top_any_hash"),
            c_top_func_share_rep_check=r.get("c_top_rep_share"),
            c_geno_func_check=int(r.get("c_geno_func") or 0),
        ))
    run = dict(
        seed=seed,
        c_wb_deaths=int(deaths["writes_blocked"].sum()),
        c_wb_living=int(living["writes_blocked"].sum()),
        c_blockers=int((deaths["writes_blocked"] > 0).sum()),
        c_deaths=deaths.height,
        c_first_blocker_death=deaths.filter(pl.col("writes_blocked") > 0)["tick"].min(),
        **concentration(deaths, "writes_blocked", "c_wb"),
    )
    return rows, run


def diverge(seed: int) -> int | None:
    """Tick of the first births.csv row where the noprot run and its E007
    seed differ (the files share a format), or None if one is a prefix of
    the other within the noprot run."""
    a, b = OUT / ARM / f"s{seed}" / "births.csv", CONTROL / CONTROL_ARM / f"s{seed}" / "births.csv"
    if not (a.exists() and b.exists()):
        return None
    with open(a) as fa, open(b) as fb:
        for la, lb in zip(fa, fb):
            if la != lb:
                return int(la.split(",", 1)[0])
    return None


def control(seeds: list[int], jobs: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Control tables for `seeds`, joined with E007's per-window columns."""
    with ThreadPoolExecutor(jobs) as ex:
        res = list(ex.map(control_one, seeds))
    for s, (_, r) in zip(seeds, res):
        print(f"control std/s{s}: writes_blocked over deaths to {CONTROL_TICKS:,} = {r['c_wb_deaths']:,}", flush=True)
    cw = pl.DataFrame([row for rows, _ in res for row in rows], infer_schema_length=None)
    cr = pl.DataFrame([{**r, "diverge_tick": diverge(r["seed"])} for _, r in res], infer_schema_length=None)
    e7 = pl.read_csv(CONTROL / "windows.csv", schema_overrides={"top_hash": pl.Utf8, "top_func_hash": pl.Utf8,
                                                                 "top_par_hash": pl.Utf8})
    keep = ["births", "exact", "exact_share", "pop", "rep_alive", "genotypes", "genotypes_func", "top_func_hash",
            "top_func_share", "par_share", "dep_share", "absorb_med", "absorb_ge96", "endow_med"]
    e7 = e7.filter(pl.col("window") <= CONTROL_TICKS // CONTROL_WINDOW).select(
        "seed", "window", *[pl.col(c).alias(f"c_{c}") for c in keep]
    )
    cw = cw.join(e7, on=["seed", "window"], how="left").sort("seed", "window")
    return cw, cr


# --- summary -------------------------------------------------------------------


def _f0(v):
    return "–" if v is None else f"{v:,.0f}"


def _f2(v):
    return "–" if v is None else f"{v:.2f}"


def _f3(v):
    return "–" if v is None else f"{v:.3f}"


def _pct(v):
    return "–" if v is None else f"{100 * v:.2f}%"


def _ok(b: bool) -> str:
    return "confirmed" if b else "not confirmed"


def _med(df: pl.DataFrame, col: str):
    s = df[col].drop_nulls()
    return s.median() if s.len() else None


def takeover(wdf: pl.DataFrame, seed: int, n_w: int) -> int | None:
    """First window w >= 2 from which one canonical genotype (any class)
    leads with >= 50% of exact births in every window w..n_w, or None."""
    x = {r["window"]: r for r in wdf.filter(pl.col("seed") == seed).iter_rows(named=True)}
    for w in range(2, n_w + 1):
        h = x.get(w, {}).get("top_func_hash_any")
        if h is None:
            continue
        if all(x.get(v, {}).get("top_func_hash_any") == h and (x[v].get("top_func_share_any") or 0) >= H4_TAKEOVER
               for v in range(w, n_w + 1)):
            return w
    return None


def summarize_e012(persist: pl.DataFrame, wdf: pl.DataFrame, wrun: pl.DataFrame, cw: pl.DataFrame,
                   cr: pl.DataFrame, cls: pl.DataFrame, timing: pl.DataFrame, ticks: int, window: int) -> str:
    n_w = ticks // window
    seeds = sorted(persist["seed"].to_list())
    surv = sorted(persist.filter(pl.col("replicating"))["seed"].to_list())
    live = wdf.filter(pl.col("seed").is_in(surv))
    e7p = pl.read_csv(CONTROL / "runs_e004.csv")
    c_surv = sorted(e7p.filter(pl.col("replicating"))["seed"].to_list())
    c_live = cw.filter(pl.col("seed").is_in(c_surv))
    W = lambda df, s, w: df.filter((pl.col("seed") == s) & (pl.col("window") == w))
    one = lambda df, s, w, c: (W(df, s, w)[c][0] if W(df, s, w).height else None)

    L = [
        f"# E012 summary: arm noprot (`--no-protect`), seeds {seeds[0]}–{seeds[-1]}, {ticks:,} ticks, "
        f"windows of {window:,}",
        "",
        f"Control: E007 (`runs/e007/std`, protection on) seeds {cw['seed'].min()}–{cw['seed'].max()}, windows 1–"
        f"{CONTROL_TICKS // CONTROL_WINDOW}. Seeds replicating at the end: noprot {', '.join(map(str, surv)) or 'none'} "
        f"({len(surv)} of {len(seeds)}); E007 {', '.join(map(str, c_surv))} ({len(c_surv)} of {e7p.height}). "
        "Shares are of the window's exact births. Canonical = `func_hash`; 'top any' is the leading canonical "
        "genotype among all exact births (the record's measure), 'top rep' E007's `top_func_share` (leader among "
        "replicator-class exact births). Parasite share is E005's 2+-children test over each arm's own run "
        "(E007's over 250,000 ticks). Writes are summed over the deaths in the window (by death tick); "
        "noprot `writes_foreign`, E007 `writes_blocked`. Record: "
        "docs/research/experiments/2026-10-12-e012-no-protect.md.",
        "",
        "## Per seed and window: structure (noprot / E007)",
        "",
        "| seed | window | population | replicator-class alive | exact births | canonical genotypes (>= 2 exact) "
        "| top any share | top rep share | parasite share | absorb median |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in seeds:
        for w in range(1, n_w + 1):
            g = lambda c: one(wdf, s, w, c)
            h = lambda c: one(cw, s, w, c)
            L.append(
                f"| {s} | {w} | {_f0(g('pop'))} / {_f0(h('c_pop'))} | {_f0(g('rep_alive'))} / {_f0(h('c_rep_alive'))} "
                f"| {_f0(g('exact'))} / {_f0(h('c_exact'))} | {_f0(g('genotypes_func'))} / {_f0(h('c_genotypes_func'))} "
                f"| {_f3(g('top_func_share_any'))} / {_f3(h('c_top_func_share_any'))} "
                f"| {_f3(g('top_func_share'))} / {_f3(h('c_top_func_share'))} "
                f"| {_pct(g('par_share'))} / {_pct(h('c_par_share'))} | {_f0(g('absorb_med'))} / {_f0(h('c_absorb_med'))} |"
            )
    L += [
        "",
        "## Per seed and window: writes",
        "",
        "noprot: deaths in the window, Σ`writes_foreign`, writers (deaths with `writes_foreign` > 0), share of "
        "deaths with `overwritten` > 0, Σ`writes_blocked` (0 expected), and the median age at death of overwritten "
        "bodies against the rest. E007: deaths, Σ`writes_blocked`, deaths with `writes_blocked` > 0.",
        "",
        "| seed | window | deaths | Σ writes_foreign | writers | overwritten share of deaths | Σ writes_blocked "
        "| age at death, overwritten / rest | E007 deaths | E007 Σ writes_blocked | E007 blocking writers "
        "| foreign / blocked |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in seeds:
        for w in range(1, n_w + 1):
            g = lambda c: one(wdf, s, w, c)
            h = lambda c: one(cw, s, w, c)
            cb = h("c_writes_blocked")
            L.append(
                f"| {s} | {w} | {_f0(g('deaths'))} | {_f0(g('writes_foreign'))} | {_f0(g('writers'))} "
                f"| {_pct(g('overwritten_share'))} | {_f0(g('writes_blocked'))} "
                f"| {_f0(g('age_med_overwritten'))} / {_f0(g('age_med_rest'))} "
                f"| {_f0(h('c_deaths'))} | {_f0(cb)} | {_f0(h('c_blockers'))} "
                f"| {_f2(g('writes_foreign') / cb) if (cb and g('writes_foreign') is not None) else '–'} |"
            )

    # Medians per window.
    L += [
        "",
        f"## Medians per window (noprot over its {len(surv)} surviving seeds / E007 over its {len(c_surv)})",
        "",
        "| window | population | canonical genotypes | top any share | top rep share | parasite share | absorb median "
        "| Σ writes_foreign / Σ writes_blocked | writers / blocking writers | overwritten share of deaths |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for w in range(1, n_w + 1):
        x, y = live.filter(pl.col("window") == w), c_live.filter(pl.col("window") == w)
        L.append(
            f"| {w} | {_f0(_med(x, 'pop'))} / {_f0(_med(y, 'c_pop'))} "
            f"| {_f0(_med(x, 'genotypes_func'))} / {_f0(_med(y, 'c_genotypes_func'))} "
            f"| {_f3(_med(x, 'top_func_share_any'))} / {_f3(_med(y, 'c_top_func_share_any'))} "
            f"| {_f3(_med(x, 'top_func_share'))} / {_f3(_med(y, 'c_top_func_share'))} "
            f"| {_pct(_med(x, 'par_share'))} / {_pct(_med(y, 'c_par_share'))} "
            f"| {_f0(_med(x, 'absorb_med'))} / {_f0(_med(y, 'c_absorb_med'))} "
            f"| {_f0(_med(x, 'writes_foreign'))} / {_f0(_med(y, 'c_writes_blocked'))} "
            f"| {_f0(_med(x, 'writers'))} / {_f0(_med(y, 'c_blockers'))} | {_pct(_med(x, 'overwritten_share'))} |"
        )

    # Whole-run write table and prediction 4.
    j = wrun.join(cr, on="seed", how="left").sort("seed")
    L += [
        "",
        f"## Per seed, whole run to tick {ticks:,}",
        "",
        "Σ over deaths with tick <= the run's end; 'with living' adds the bodies alive at the final census. "
        "Σ`writes_foreign` = Σ`overwritten` is checked over deaths + living.",
        "",
        "| seed | replicating | population at end | Σ writes_foreign (deaths) | E007 Σ writes_blocked (deaths) | ratio "
        "| in 0.5–2 | Σ writes_foreign with living | E007 with living | ratio with living | Σ overwritten (deaths + living) "
        "| foreign = overwritten | writers | E007 blocking writers | Σ writes_blocked noprot |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    p4_ok = p4_n = 0
    ratios = []
    for r in j.iter_rows(named=True):
        p = persist.filter(pl.col("seed") == r["seed"]).row(0, named=True)
        cb, cl = r.get("c_wb_deaths"), r.get("c_wb_living")
        ratio = r["wf_deaths"] / cb if cb else None
        ratio_l = r["wf_total"] / (cb + cl) if cb is not None and (cb + (cl or 0)) else None
        inr = ratio is not None and P4_RATIO[0] <= ratio <= P4_RATIO[1]
        if ratio is not None:
            p4_n += 1
            p4_ok += inr
            ratios.append(ratio)
        L.append(
            f"| {r['seed']} | {'yes' if p['replicating'] else 'no'} | {p['pop_end']} | {r['wf_deaths']:,} | {_f0(cb)} "
            f"| {_f2(ratio)} | {'yes' if inr else ('–' if ratio is None else 'no')} | {r['wf_total']:,} "
            f"| {_f0(None if cb is None else cb + (cl or 0))} | {_f2(ratio_l)} | {r['ow_total']:,} "
            f"| {'yes' if r['wf_eq_ow'] else 'NO'} | {r['writers_deaths']:,} | {_f0(r.get('c_blockers'))} "
            f"| {r['wb_deaths']:,} |"
        )

    # Prediction checks.
    pop_med = persist.filter(pl.col("replicating"))["pop_end"].median() if surv else None
    p1 = len(surv) >= P1_SEEDS and pop_med is not None and P1_POP[0] <= pop_med <= P1_POP[1]
    late = live.filter(pl.col("window") >= 2)
    p2_top_bad = late.filter(~(pl.col("top_func_share_any") < P2_TOP))
    p2_geno_bad = late.filter(~(pl.col("genotypes_func") >= P2_GENO))
    p2 = len(surv) > 0 and p2_top_bad.height == 0 and p2_geno_bad.height == 0
    p2_rep_bad = late.filter(~(pl.col("top_func_share") < P2_TOP)).height
    p3_parts, p3 = [], len(surv) > 0
    for w in range(2, n_w + 1):
        a = _med(live.filter(pl.col("window") == w), "genotypes_func")
        b = _med(c_live.filter(pl.col("window") == w), "c_genotypes_func")
        rr = a / b if (a is not None and b) else None
        p3 = p3 and rr is not None and P3_RATIO[0] <= rr <= P3_RATIO[1]
        p3_parts.append(f"window {w}: {_f0(a)} / {_f0(b)} = {_f2(rr)}")
    p4 = p4_n > 0 and p4_ok == p4_n
    p5_parts, p5 = [], len(surv) > 0
    for w in range(2, n_w + 1):
        v = _med(live.filter(pl.col("window") == w), "par_share")
        p5 = p5 and v is not None and P5_PAR[0] <= v <= P5_PAR[1]
        p5_parts.append(f"window {w} {_pct(v)}")
    ab2 = live.filter(pl.col("window") == 2).sort("seed")
    p6_n = int((ab2["absorb_med"].fill_null(-999) >= P6_ABSORB).sum()) if ab2.height else 0
    p6 = p6_n >= P6_SEEDS
    rmed = pl.Series(ratios).median() if ratios else None

    L += [
        "",
        "## Prediction checks",
        "",
        f"1. Persistence: replicating at tick {ticks:,} in {len(surv)} of {len(seeds)} (>= {P1_SEEDS} wanted); "
        f"median population at the end over surviving seeds {_f0(pop_med)} ({P1_POP[0]:,}–{P1_POP[1]:,} wanted; "
        f"E007 9 of 10, 936). Per seed: "
        + ", ".join(f"s{r['seed']} {r['pop_end']}{'' if r['replicating'] else ' (not replicating)'}"
                    for r in persist.sort("seed").iter_rows(named=True))
        + f". **{_ok(p1)}**",
        f"2. No takeover: over the {late.height} seed-windows (surviving seeds, windows 2–{n_w}), top any share "
        f"max {_f3(late['top_func_share_any'].max() if late.height else None)} (< {P2_TOP} wanted; above or at it: "
        f"{p2_top_bad.height}), canonical genotypes min {_f0(late['genotypes_func'].min() if late.height else None)} "
        f"(>= {P2_GENO:,} wanted; below: {p2_geno_bad.height}). With E007's replicator-class leader instead: "
        f"max {_f3(late['top_func_share'].max() if late.height else None)}, at or above {P2_TOP}: {p2_rep_bad}. "
        f"**{_ok(p2)}**",
        f"3. Diversity near the protected world: median canonical genotypes noprot / E007 for "
        f"{'; '.join(p3_parts)} (each {P3_RATIO[0]}–{P3_RATIO[1]} wanted). **{_ok(p3)}**",
        f"4. Foreign writes at about the blocked rate: Σ`writes_foreign` / E007 Σ`writes_blocked` (deaths to tick "
        f"{ticks:,}) per seed: "
        + ", ".join(f"s{s} {_f2(r)}" for s, r in zip(j.filter(pl.col('c_wb_deaths') > 0)['seed'].to_list(), ratios))
        + f"; in {P4_RATIO[0]}–{P4_RATIO[1]} in {p4_ok} of {p4_n} seeds with a non-zero control (every one wanted); "
        f"median ratio {_f2(rmed)}. **{_ok(p4)}**",
        f"5. Parasites persist: median parasite share over surviving seeds, {', '.join(p5_parts)} "
        f"(each {_pct(P5_PAR[0])}–{_pct(P5_PAR[1])} wanted). **{_ok(p5)}**",
        f"6. Absorb sweep: window-2 absorb median >= {P6_ABSORB} in {p6_n} of {len(surv)} surviving seeds "
        f"(>= {P6_SEEDS} wanted). Per seed: "
        + ", ".join(f"s{r['seed']} {_f0(r['absorb_med'])}" for r in ab2.iter_rows(named=True))
        + f". **{_ok(p6)}**",
    ]

    # Exploratory 7.
    tw = j.select(pl.col("wf_rep").sum(), pl.col("wf_dep").sum(), pl.col("wf_par").sum(), pl.col("wf_other").sum(),
                  pl.col("writers_rep").sum(), pl.col("writers_dep").sum(), pl.col("writers_other").sum()).row(0, named=True)
    tot = tw["wf_rep"] + tw["wf_dep"] + tw["wf_other"]
    share = lambda v: _pct(v / tot) if tot else "–"
    L += [
        "",
        "## 7. Exploratory",
        "",
        "Foreign writes by the writer's genome class (deaths, whole run; replicator = classes_world.csv "
        "`replicator`, dependent = E005 dependent table, parasite = its parasite_2 subset, other = the rest), "
        "median age at death of bodies with `overwritten` > 0 against the rest, and the high-rate genomes "
        f"(foreign-write rate above the {RATE_Q:.0%} quantile; module docstring):",
        "",
        "| seed | Σ writes_foreign | replicator | dependent (of which parasite) | other | writers rep / dep / other "
        "| overwritten deaths | age at death overwritten / rest | writing genomes | p99 rate (writing) | high-rate "
        "| high-rate with exact births | max share of a window's exact births (window) | p99 rate (all) | high-rate (all) "
        "| max share (all) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in j.iter_rows(named=True):
        t = r["wf_rep"] + r["wf_dep"] + r["wf_other"]
        sh = lambda v: _pct(v / t) if t else "–"
        L.append(
            f"| {r['seed']} | {r['wf_deaths']:,} | {sh(r['wf_rep'])} | {sh(r['wf_dep'])} ({sh(r['wf_par'])}) "
            f"| {sh(r['wf_other'])} | {r['writers_rep']:,} / {r['writers_dep']:,} / {r['writers_other']:,} "
            f"| {r['n_overwritten_deaths']:,} ({_pct(r['overwritten_share'])}) "
            f"| {_f0(r['age_med_overwritten'])} / {_f0(r['age_med_rest'])} | {r['writing_genomes']:,} "
            f"| {_f3(r['p99_writing'])} | {r['n_high_writing']} | {r['n_high_writing_exact']} "
            f"| {_pct(r['high_writing_share_max'])} ({_f0(r['high_writing_share_max_win'])}) "
            f"| {_f3(r['p99_all'])} | {r['n_high_all']:,} | {_pct(r['high_all_share_max'])} |"
        )
    L += [
        "",
        "How the writes are spread over the carriers that made any (deaths only, both arms): median and maximum "
        "per writer, share of all of them made by the top 1% of writers, and share made by carriers whose body "
        "had changed since birth (`now_hash` != `birth_hash`). noprot `writes_foreign` / E007 `writes_blocked`.",
        "",
        "| seed | writes per writer, median | max by one carrier | top 1% of writers' share | by changed bodies |",
        "|---|---|---|---|---|",
    ]
    for r in j.iter_rows(named=True):
        L.append(
            f"| {r['seed']} | {_f0(r['wf_per_writer_med'])} / {_f0(r.get('c_wb_per_writer_med'))} "
            f"| {_f0(r['wf_max_carrier'])} / {_f0(r.get('c_wb_max_carrier'))} "
            f"| {_pct(r['wf_top1pct_share'])} / {_pct(r.get('c_wb_top1pct_share'))} "
            f"| {_pct(r['wf_changed_share'])} / {_pct(r.get('c_wb_changed_share'))} |"
        )
    reach = int(j["high_writing_reaches_1pct"].sum())
    reach_all = int(j["high_all_reaches_1pct"].sum())
    L += [
        "",
        f"All seeds pooled: foreign writes by replicator-class writers {share(tw['wf_rep'])}, dependent "
        f"{share(tw['wf_dep'])} (parasites {share(tw['wf_par'])}), other {share(tw['wf_other'])}; writers "
        f"{tw['writers_rep']:,} / {tw['writers_dep']:,} / {tw['writers_other']:,}. Median over seeds of the median "
        f"age at death: overwritten {_f0(j['age_med_overwritten'].median())}, rest {_f0(j['age_med_rest'].median())}. "
        f"A high-rate genome reaches {_pct(RATE_SHARE)} of a window's exact births in {reach} of {j.height} seeds "
        f"(writing-genome percentile), {reach_all} of {j.height} (all-genome percentile"
        + (": " + "; ".join(
            f"s{r['seed']} genome {r['high_all_share_max_hash']}, rate {r['high_all_share_max_rate']:.4f} against a "
            f"p99 of {r['p99_all']:.4f}, {_pct(r['high_all_share_max'])} of window {r['high_all_share_max_win']}"
            for r in j.filter(pl.col("high_all_reaches_1pct")).iter_rows(named=True)) if reach_all else "")
        + "). The all-genome percentile sits near 0.001 because most genomes never write, so it marks about 1% "
        "of all genomes, ordinary replicators among them; the writing-genome percentile (primary) marks the "
        "genomes that write fastest.",
    ]

    # H4.
    tk = {s: takeover(wdf, s, n_w) for s in surv}
    n_tk = sum(1 for v in tk.values() if v is not None)
    ended = len(seeds) - len(surv)
    if p1 and p2:
        verdict = "refuted"
    elif n_tk >= H4_SEEDS or ended >= H4_SEEDS:
        verdict = "supported"
    else:
        verdict = "mixed"
    L += [
        "",
        "## H4 scoring (record, as written)",
        "",
        f"- Refuted if predictions 1 and 2 hold: prediction 1 {_ok(p1)}, prediction 2 {_ok(p2)}.",
        f"- Supported if in >= {H4_SEEDS} surviving seeds one canonical genotype holds >= {H4_TAKEOVER:.0%} of exact "
        f"births in some window from 2 on and keeps it to the end (seeds: {n_tk} of {len(surv)}"
        + (f"; {', '.join(f's{s} from window {w}' for s, w in tk.items() if w)}" if n_tk else "")
        + f"; max top any share in windows 2–{n_w}: {_f3(late['top_func_share_any'].max() if late.height else None)}), "
        f"or replication ends in >= {H4_SEEDS} seeds by tick {ticks:,} (ended in {ended}).",
        f"- **H4: {verdict}.**",
    ]

    # Checks and times.
    L += [
        "",
        "## Checks",
        "",
        f"- classes.csv and classes_world.csv identical in {int(cls['identical'].sum())} of {cls.height} runs"
        + ("" if cls["identical"].all() else
           "; differing: " + ", ".join(f"s{r['seed']} ({r['class_differs']} genomes change class, "
                                       f"{r['rows_differ']} rows of {r['genomes']:,} differ, in "
                                       f"`{r['cols_differ']}`)"
                                       for r in cls.filter(~pl.col("identical")).iter_rows(named=True)))
        + ".",
        f"- Σ`writes_foreign` = Σ`overwritten` over deaths + living at the final census in "
        f"{int(wrun['wf_eq_ow'].sum())} of {wrun.height} runs.",
        f"- Σ`writes_blocked` over noprot deaths: {', '.join(f's{s} {v:,}' for s, v in wrun.sort('seed').select('seed', 'wb_deaths').iter_rows())} "
        "(0 expected with protection off).",
        f"- E007 control, Σ`writes_blocked` over deaths to tick {CONTROL_TICKS:,}: "
        + ", ".join(f"s{s} {v:,}" for s, v in cr.sort("seed").select("seed", "c_wb_deaths").iter_rows())
        + " (record: s1 132,578, s2 176,908).",
        "- Shared start (record: a run is bit-identical to its E007 seed until the first write protection would "
        "have refused): births.csv first differs at tick / E007's first death with `writes_blocked` > 0: "
        + ", ".join(f"s{r['seed']} {_f0(r['diverge_tick'])} / {_f0(r['c_first_blocker_death'])}"
                    for r in cr.sort("seed").iter_rows(named=True))
        + " (the first refused write comes before its writer's death, and births.csv shows the parting only "
        "at the first birth that differs, so the two ticks should be close; – = no difference within the "
        "shorter file / no blocked write).",
    ]
    chk = cw.filter(pl.col("c_exact").is_not_null())
    if chk.height:
        d_geno = (chk["c_geno_func_check"] - chk["c_genotypes_func"]).abs().max()
        d_top = (chk["c_top_func_share_rep_check"].fill_null(0) - chk["c_top_func_share"].fill_null(0)).abs().max()
        d_ex = (chk["c_exact_check"] - chk["c_exact"]).abs().max()
        L.append(
            f"- Control recomputation against runs/e007/windows.csv (windows 1–4): max |Δ| exact births {d_ex}, "
            f"canonical genotypes {d_geno}, replicator-class top share {d_top:.2g}."
        )
    if timing.height:
        L += ["", "## Wall time per run (s)", "", "| seed | simulation | classify (default) | classify (--no-protect) |",
              "|---|---|---|---|"]
        for r in timing.sort("seed").iter_rows(named=True):
            L.append(f"| {r['seed']} | {_f0(r['sim_s'])} | {_f0(r['classify_s'])} | {_f0(r['classify_world_s'])} |")
    return "\n".join(L)


# --- main ----------------------------------------------------------------------


def main() -> None:
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=TICKS)
    ap.add_argument("--window", type=int, default=WINDOW)
    ap.add_argument("--control-seeds", type=int, default=10)
    ap.add_argument("--jobs", type=int, default=6, help="parallel simulations")
    ap.add_argument("--analysis-jobs", type=int, default=2, help="parallel analyses (memory)")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--sims-only", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--summary-only", action="store_true")
    a = ap.parse_args()
    OUT = a.out.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = list(range(1, a.seeds + 1))

    e004.OUT = OUT
    e004.ARMS = {ARM: FLAGS}
    e005.RUNS = OUT
    e005.OUT = OUT
    e005.ARMS = {ARM: FLAGS}
    e007.OUT = OUT
    e007.ARM = ARM
    e007.TICKS = a.ticks
    e007.WINDOW = a.window
    # E007's "parasite genomes first born after" column: the last window here.
    e007.LATE_FROM = a.ticks - a.window

    timing_path = OUT / "timing.csv"
    if not (a.analyse_only or a.summary_only):
        exe = binary()
        with ThreadPoolExecutor(a.jobs) as ex:
            t = list(ex.map(lambda s: sim_one(exe, s, a.ticks, a.force), seeds))
        new = pl.DataFrame([r for r in t if r["sim_s"] is not None or r["classify_world_s"] is not None],
                           schema={"seed": pl.Int64, "sim_s": pl.Int64, "classify_s": pl.Int64,
                                   "classify_world_s": pl.Int64})
        if timing_path.exists():
            old = pl.read_csv(timing_path, schema_overrides={c: pl.Int64 for c in new.columns})
            new = pl.concat([old.filter(~pl.col("seed").is_in(new["seed"].to_list())), new])
        new.sort("seed").write_csv(timing_path)
        if a.sims_only:
            return

    if a.summary_only:
        persist = pl.read_csv(OUT / "runs_e004.csv")
        wdf = pl.read_csv(OUT / "windows.csv", infer_schema_length=None,
                          schema_overrides={c: pl.Utf8 for c in ("top_hash", "top_par_hash", "top_func_hash",
                                                                 "top_func_hash_any")})
        wrun = pl.read_csv(OUT / "writes_run.csv", infer_schema_length=None,
                           schema_overrides={c: pl.Utf8 for c in ("high_writing_share_max_hash", "high_all_share_max_hash")})
        cw = pl.read_csv(OUT / "control.csv", infer_schema_length=None,
                         schema_overrides={c: pl.Utf8 for c in ("c_top_func_hash", "c_top_func_hash_any")})
        cr = pl.read_csv(OUT / "control_run.csv")
        cls = pl.read_csv(OUT / "classes_check.csv")
    else:
        exe = binary()
        rows =[e004.metrics(ARM, s, a.ticks) for s in seeds if (OUT / ARM / f"s{s}" / "classes.csv").exists()]
        persist = pl.DataFrame(rows)
        persist.write_csv(OUT / "runs_e004.csv")
        text = e004.summarize(a.seeds, a.ticks, [ARM]).replace("E004 summary", "E012 persistence (E004 measures), arm noprot")
        (OUT / "summary_e004.md").write_text(text + "\n", encoding="utf-8")
        print(text)
        # run_all also writes any missing classes_world.csv; compare after it.
        e005.run_all([ARM], a.seeds, a.analysis_jobs, host=True)
        cls =pl.DataFrame([compare_classes(s) for s in seeds])
        cls.write_csv(OUT / "classes_check.csv")
        print(cls)

        def one(s: int):
            rows = e007.windows(s, exe)
            wrows, run = writes(s, a.ticks, a.window)
            by_w = {r["window"]: r for r in wrows}
            for r in rows:
                r.update({k: v for k, v in by_w[r["window"]].items() if k not in ("seed", "window")})
            print(f"{ARM}/s{s}: windows and writes done", flush=True)
            return rows, run

        with ThreadPoolExecutor(a.analysis_jobs) as ex:
            res = list(ex.map(one, [s for s in seeds if (OUT / f"{ARM}_s{s}_dependent.csv").exists()]))
        wdf = pl.DataFrame([r for rows, _ in res for r in rows], infer_schema_length=None)
        wdf.write_csv(OUT / "windows.csv")
        wrun = pl.DataFrame([run for _, run in res], infer_schema_length=None)
        wrun.write_csv(OUT / "writes_run.csv")
        text = e007.summarize_windows(wdf.select(pl.exclude("top_func_hash_any")), persist)
        text = text.replace("E007 windows:", f"E012 windows, arm noprot (`--no-protect`):")
        text = text.replace("top host changes, of 9", f"top host changes, of {a.ticks // a.window - 1}")
        i, k = text.find("Prediction checks:"), text.find("Added after the run")
        if i >= 0 and k > i:
            text = text[:i] + "E007's prediction checks do not apply here; E012's are in summary_e012.md.\n\n" + text[k:]
        text = text.replace("Added after the run (not pre-registered): canonical", "Canonical")
        (OUT / "summary_windows.md").write_text(text + "\n", encoding="utf-8")
        print(text)

        cw, cr = control(list(range(1, a.control_seeds + 1)), a.analysis_jobs)
        cw.write_csv(OUT / "control.csv")
        cr.write_csv(OUT / "control_run.csv")

    timing = pl.read_csv(timing_path) if timing_path.exists() else pl.DataFrame()
    text = summarize_e012(persist, wdf, wrun, cw, cr, cls, timing, a.ticks, a.window)
    (OUT / "summary_e012.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
