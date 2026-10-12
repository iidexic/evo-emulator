"""E011: is there a producer/consumer split in E007? No new world runs; reads
the ten E007 runs (runs/e007/std/s<seed>/, docs/instrumentation.md) and
E005's dependent-genome tables (runs/e007/std_s<seed>_dependent.csv), and
tests the predictions in
docs/research/experiments/2026-10-12-e011-absorb-split.md.

Usage (from analysis/):

    uv run e011_absorb_split.py                    # all seeds, then the summary
    uv run e011_absorb_split.py --seeds 1 2        # only these seeds (others reused)
    uv run e011_absorb_split.py --summarize-only   # reuse the CSVs below

Seeds are read one at a time with lazy scans (`deaths.csv` is about 420 MB),
selecting only the columns used.

Definitions (E011 record, repeated here so the code can be checked against
them):

  carrier        a row of deaths.csv, or of orgs.csv at tick 250,000 (alive
                 at the end), with executed >= 1
  a, g           per carrier: a = absorbs / executed;
                 g = absorb_gain_m / (absorb_gain_m + born_with_m)
  exact birth    births.csv row with raw_hash == parent_now_hash
  genome         the raw birth hash (`birth_hash` of the carrier rows)
  in scope       >= 2 exact births: over the whole run for whole-run
                 measures, inside the window for window measures
  a_G, g_G       pooled over the genome's carriers: sum(absorbs) /
                 sum(executed), sum(absorb_gain_m) / sum(absorb_gain_m +
                 born_with_m). Window w pools the carriers that die in it
                 (window 10 also those alive at the end); the whole run
                 pools all of them. Null when the genome has no carrier there.
  weight         the genome's exact births (in the window, or whole run)
  windows        w = 1..10 covers ticks (25,000 (w-1), 25,000 w] (E007);
                 births by birth tick, carriers by death tick
  groups         replicator-class: classes.csv class == replicator;
                 dependent: in scope, class != replicator (no classes.csv
                 row counts as `unknown`); parasite: parasite_2 true in
                 E005's dependent table (a subset of dependent)
  low-absorb     in-scope genome with g_G < 0.5

Weighted median (`wmedian`): sort the genomes by value, accumulate the
weights, and take the first value at which the cumulative weight reaches
half the total; if it lands exactly on half, the mean of that value and the
next. With all weights 1 this is the ordinary median, which is how the
unweighted medians are computed.

Prediction measures:

  1. `lowg_share`: exact births of in-scope genomes with g_G < 0.5 over all
     the window's exact births (in scope or not); whole-run weighted median
     g_G of replicator-class and parasite genomes.
  2. whole-run weighted median a_G, parasite vs replicator-class.
  3. `band_share`: weighted share of a_G in [0.15, 0.26] over in-scope
     genomes with a carrier in the window.
  4. (exploratory) per-carrier histograms of a and g (20 bins on [0, 1]),
     the share of carriers with g < 0.5 by the carrier's genome class, the
     per-genome distributions, and measures 1-3 with genomes grouped by
     `func_hash` (genomes.csv) instead of raw hash. A func group's exact
     births are the sum over its raw members (still raw-exact births); its
     scope is >= 2 such births; its parasite flag is true if any member is
     flagged; its class is the class of the member with the most whole-run
     exact births (ties: lowest raw hash), in every window.

Added after the first run on seed 1 (post hoc, not registered; the
registered columns are unchanged): per genome, `exact_somatic` (exact
births whose executor's body had changed since its own birth, births.csv
parent_hash != parent_now_hash), `executors` (distinct executors of its
exact births) and `reproducers` (carriers with >= 1 offspring); per seed and
window, where the low-absorb weight comes from (`somatic_share`,
`lowg_somatic_frac`, `lowg_rep_exact`, `lowg_par_exact`, `lowg_repro_frac`,
`repro_frac_other`, `lowg_executors_med`, `no_carrier_share`) and
`lowg_share_germ`, the prediction-1 share when scope also requires >= 2
non-somatic exact births. summary.md shows them in a separate section.

Outputs in runs/e011/:

  genomes_s<seed>.csv  one row per in-scope raw genome per window; window 0
                       is the whole run
  funcs_s<seed>.csv    the same for func_hash groups (key `func_hash`)
  seeds.csv            per seed, grouping (raw / func) and window (0 = whole
                       run): the prediction measures
  carriers.csv         per seed: carrier counts, g < 0.5 shares and medians of
                       a and g, split by class, group and offspring
  hist.csv             per seed: carrier histograms of a and g by stratum
  sanity.csv           per seed: row counts, consistency checks, wall time
  summary.md           tables and the prediction checks

Seed 10 died at tick 1,179; it is reported but left out of every median and
count, as in E007.
"""

from __future__ import annotations

import argparse
import gc
import json
import time

import numpy as np
import polars as pl

from evo_run import HASH_COLS, ROOT

RUNS = ROOT / "runs" / "e007"
ARM = "std"
OUT = ROOT / "runs" / "e011"
TICKS = 250_000
WINDOW = 25_000
N_WIN = TICKS // WINDOW
SEEDS = list(range(1, 11))
EXCLUDED = {10}  # died at tick 1,179 (E007); reported, not in medians
LOW_G = 0.5
BAND = (0.15, 0.26)
BINS = 20
EDGES = np.linspace(0.0, 1.0, BINS + 1)
P2_RANGE = {"rep": (0.17, 0.23), "par": (0.20, 0.25)}
STATS = ["executed", "absorbs", "absorb_gain_m", "born_with_m"]
SUMS = [*STATS, "reproducers"]  # reproducers: carriers with >= 1 offspring (post hoc)
OTHER_INCOME = ["gained_from_others_m", "paid_by_others_m", "paid_for_others_m"]
CLASS_ORDER = ["replicator", "one_shot", "inexact", "loafer", "dies", "unknown"]
GROUP_ORDER = ["replicator", "dependent_nonparasite", "parasite", "out_of_scope"]


def _hash_overrides(name: str) -> dict:
    return {c: pl.Utf8 for c in HASH_COLS[name]}


def _win(col: str = "tick") -> pl.Expr:
    return ((pl.col(col) + WINDOW - 1) // WINDOW).cast(pl.Int32)


def wmedian(values, weights=None) -> float | None:
    """Weighted median (module docstring); nulls/NaN and zero weights are
    dropped. Without weights, the ordinary median."""
    v = np.asarray(values, dtype=float)
    w = np.ones_like(v) if weights is None else np.asarray(weights, dtype=float)
    keep = ~np.isnan(v) & (w > 0)
    v, w = v[keep], w[keep]
    if v.size == 0:
        return None
    o = np.argsort(v, kind="stable")
    v, w = v[o], w[o]
    c = np.cumsum(w)
    half = c[-1] / 2
    k = int(np.searchsorted(c, half, side="left"))
    if c[k] == half and k + 1 < v.size:
        return float((v[k] + v[k + 1]) / 2)
    return float(v[k])


# --- per seed ----------------------------------------------------------------


def genome_table(ex: pl.DataFrame, car: pl.DataFrame, info: pl.DataFrame) -> pl.DataFrame:
    """In-scope genomes per window (0 = whole run) with pooled a_G, g_G.
    `ex`: one row per exact birth (key, win, somatic, executor); `car`: one
    row per carrier (key, win, SUMS); `info`: key -> class, parasite."""
    eagg = dict(exact=pl.len(), exact_somatic=pl.col("somatic").sum(), executors=pl.col("executor").n_unique())
    ecols = ["key", "win", *eagg]
    ea = ex.group_by("key").agg(**eagg).with_columns(win=pl.lit(0, pl.Int32))
    ew = ex.group_by("key", "win").agg(**eagg)
    e = pl.concat([ea.select(ecols), ew.select(ecols)]).filter(pl.col("exact") >= 2)
    sums = [pl.col(s).sum() for s in SUMS]
    ca = car.group_by("key").agg(pl.len().alias("carriers"), *sums).with_columns(win=pl.lit(0, pl.Int32))
    cw = car.group_by("key", "win").agg(pl.len().alias("carriers"), *sums)
    cols = ["key", "win", "carriers", *SUMS]
    c = pl.concat([ca.select(cols), cw.select(cols)])
    g = e.join(c, on=["key", "win"], how="left").with_columns(
        pl.col(x).fill_null(0) for x in ["carriers", *SUMS]
    )
    den = pl.col("absorb_gain_m") + pl.col("born_with_m")
    g = g.with_columns(
        a_G=pl.when(pl.col("executed") > 0).then(pl.col("absorbs") / pl.col("executed")),
        g_G=pl.when(den > 0).then(pl.col("absorb_gain_m") / den),
    ).join(info, on="key", how="left").with_columns(
        pl.col("class").fill_null("unknown"), pl.col("parasite").fill_null(False)
    ).with_columns(
        replicator=pl.col("class") == "replicator",
        dependent=pl.col("class") != "replicator",
    )
    return g.sort("win", "exact", "key", descending=[False, True, False])


def window_measures(g: pl.DataFrame, ex_tot: dict[int, int], som_tot: dict[int, int]) -> list[dict]:
    """The prediction measures for each window (0 = whole run) of one seed
    and one grouping."""
    rows = []
    for w in range(0, N_WIN + 1):
        x = g.filter(pl.col("win") == w)
        tot = ex_tot.get(w, 0)
        scope_ex = int(x["exact"].sum())
        hasa = x.filter(pl.col("a_G").is_not_null())
        hasg = x.filter(pl.col("g_G").is_not_null())
        low = hasg.filter(pl.col("g_G") < LOW_G)
        low_ex = int(low["exact"].sum())
        band = hasa.filter((pl.col("a_G") >= BAND[0]) & (pl.col("a_G") <= BAND[1]))
        div = lambda n, d: n / d if d else None
        r = dict(
            window=w,
            exact=tot,
            genomes=x.height,
            scope_exact=scope_ex,
            no_carrier_genomes=int(x["a_G"].is_null().sum()),
            no_carrier_exact=int(x.filter(pl.col("a_G").is_null())["exact"].sum()),
            rep_genomes=int(x["replicator"].sum()),
            dep_genomes=int(x["dependent"].sum()),
            par_genomes=int(x["parasite"].sum()),
            rep_exact=int(x.filter(pl.col("replicator"))["exact"].sum()),
            dep_exact=int(x.filter(pl.col("dependent"))["exact"].sum()),
            par_exact=int(x.filter(pl.col("parasite"))["exact"].sum()),
            # Prediction 1
            lowg_genomes=low.height,
            lowg_exact=low_ex,
            lowg_share=div(low_ex, tot),
            lowg_share_scope=div(low_ex, scope_ex),
            lowg_share_unw=div(low.height, hasg.height),
            lowg_dep_exact=int(low.filter(pl.col("dependent"))["exact"].sum()),
            lowg_dep_frac=div(int(low.filter(pl.col("dependent"))["exact"].sum()), low_ex),
            # Prediction 3
            band_share=div(int(band["exact"].sum()), int(hasa["exact"].sum())),
            band_share_unw=div(band.height, hasa.height),
            # Post hoc (not registered): where the low-absorb weight comes from.
            somatic_share=div(som_tot.get(w, 0), tot),
            lowg_somatic_exact=int(low["exact_somatic"].sum()),
            lowg_somatic_frac=div(int(low["exact_somatic"].sum()), low_ex),
            lowg_rep_exact=int(low.filter(pl.col("replicator"))["exact"].sum()),
            lowg_par_exact=int(low.filter(pl.col("parasite"))["exact"].sum()),
            lowg_repro_frac=div(int(low["reproducers"].sum()), int(low["carriers"].sum())),
            repro_frac_other=div(int(hasg.filter(pl.col("g_G") >= LOW_G)["reproducers"].sum()),
                                 int(hasg.filter(pl.col("g_G") >= LOW_G)["carriers"].sum())),
            lowg_executors_med=wmedian(low["executors"].to_numpy()),
            lowg_share_germ=div(int(low.filter(pl.col("exact") - pl.col("exact_somatic") >= 2)["exact"].sum()), tot),
            no_carrier_share=div(int(x.filter(pl.col("a_G").is_null())["exact"].sum()), tot),
        )
        groups = {"all": pl.lit(True), "rep": pl.col("replicator"), "dep": pl.col("dependent"),
                  "par": pl.col("parasite")}
        for name, f in groups.items():
            y = x.filter(f)
            for m, col in (("g", "g_G"), ("a", "a_G")):
                r[f"{m}_med_{name}"] = wmedian(y[col].to_numpy(), y["exact"].to_numpy())
                r[f"{m}_med_{name}_unw"] = wmedian(y[col].to_numpy())
        rows.append(r)
    return rows


def _scan(seed: int, name: str) -> pl.LazyFrame:
    return pl.scan_csv(RUNS / ARM / f"s{seed}" / f"{name}.csv", schema_overrides=_hash_overrides(name))


def analyse(seed: int) -> dict:
    """Read one seed, write genomes_s<seed>.csv and funcs_s<seed>.csv, and
    return its seeds.csv rows, carriers/hist rows and sanity row."""
    t0 = time.perf_counter()
    d = RUNS / ARM / f"s{seed}"
    meta = json.loads((d / "meta.json").read_text())

    # --- births ---------------------------------------------------------------
    b = _scan(seed, "births").select(
        "tick", "raw_hash", "executor",
        exact=pl.col("raw_hash") == pl.col("parent_now_hash"),
        # The executor's body had changed since its own birth (post hoc).
        somatic=pl.col("parent_hash") != pl.col("parent_now_hash"),
    ).collect()
    n_births = b.height
    ex_raw = b.filter(pl.col("exact")).select("somatic", "executor", key="raw_hash", win=_win())
    del b

    # --- carriers -------------------------------------------------------------
    dscan = _scan(seed, "deaths")
    names = dscan.collect_schema().names()
    other = [c for c in OTHER_INCOME if c in names]
    cols = ["tick", "birth_hash", "offspring", *STATS, *other]
    deaths = dscan.select(cols).collect()
    alive = _scan(seed, "orgs").filter(pl.col("tick") == TICKS).select(cols).collect()
    rows = pl.concat([deaths.with_columns(alive=pl.lit(False)), alive.with_columns(alive=pl.lit(True))])
    n_deaths, n_alive = deaths.height, alive.height
    del deaths, alive
    other_nonzero = {c: int((rows[c] != 0).sum()) for c in other}
    founders = len(meta.get("founders") or [None])  # ancestor once before E009a
    car = rows.filter(pl.col("executed") >= 1).with_columns(
        win=_win(), reproducers=(pl.col("offspring") >= 1).cast(pl.Int64)
    )
    sanity = dict(
        seed=seed,
        ticks_run=meta["ticks_run"],
        births=n_births,
        exact_births=ex_raw.height,
        deaths=n_deaths,
        alive_end=n_alive,
        balance=n_births + founders - n_deaths - n_alive,
        carriers=car.height,
        executed0=rows.height - car.height,
        born0_rows=int((rows["born_with_m"] == 0).sum()),
        born0_carriers=int((car["born_with_m"] == 0).sum()),
        born0_carriers_absorbed=int(((car["born_with_m"] == 0) & (car["absorb_gain_m"] > 0)).sum()),
        g_undefined=int(((car["born_with_m"] + car["absorb_gain_m"]) == 0).sum()),
        other_income_cols=",".join(other) if other else "absent",
        other_income_nonzero=sum(other_nonzero.values()),
    )
    del rows

    # --- genome info -----------------------------------------------------------
    cls = _scan(seed, "classes").select("raw_hash", "class").collect()
    gen = _scan(seed, "genomes").select("raw_hash", "func_hash", "len").collect()
    dep = pl.read_csv(RUNS / f"{ARM}_s{seed}_dependent.csv",
                      schema_overrides={"raw_hash": pl.Utf8, "bytes_hex": pl.Utf8})
    par = dep.filter(pl.col("parasite_2").cast(pl.Boolean))["raw_hash"].to_list() if dep.height else []
    info_raw = (
        gen.join(cls, on="raw_hash", how="left")
        .with_columns(pl.col("class").fill_null("unknown"),
                      parasite=pl.col("raw_hash").is_in(pl.Series(par, dtype=pl.Utf8).implode()))
    )

    # --- raw grouping ------------------------------------------------------------
    car_raw = car.select(pl.col("birth_hash").alias("key"), "win", *SUMS)
    g_raw = genome_table(ex_raw, car_raw, info_raw.select(key="raw_hash", **{"class": "class"}, parasite="parasite"))
    g_raw = g_raw.join(info_raw.select(key="raw_hash", func_hash="func_hash", len="len"), on="key", how="left")
    ex_tot = {0: ex_raw.height, **dict(ex_raw.group_by("win").len().iter_rows())}
    som_tot = {0: int(ex_raw["somatic"].sum()),
               **dict(ex_raw.group_by("win").agg(pl.col("somatic").sum()).iter_rows())}
    srows = [dict(seed=seed, grouping="raw", **r) for r in window_measures(g_raw, ex_tot, som_tot)]
    g_raw.rename({"key": "raw_hash", "win": "window"}).select(
        pl.lit(seed).alias("seed"), "window", "raw_hash", "func_hash", "len", "class", "replicator", "dependent",
        "parasite", "exact", "exact_somatic", "executors", "carriers", *SUMS, "a_G", "g_G",
    ).write_csv(OUT / f"genomes_s{seed}.csv")
    whole = g_raw.filter(pl.col("win") == 0)
    sanity.update(
        scope_raw=whole.height,
        dependent_raw=int(whole["dependent"].sum()),
        dependent_e005=dep.height,
        parasites=len(par),
        parasites_in_scope=int(whole["parasite"].sum()),
    )

    # --- func grouping -------------------------------------------------------------
    f_of = gen.select("raw_hash", "func_hash")
    ex_by_raw = ex_raw.group_by("key").agg(exact=pl.len()).rename({"key": "raw_hash"})
    finfo = (
        info_raw.join(ex_by_raw, on="raw_hash", how="left")
        .with_columns(pl.col("exact").fill_null(0))
        .sort(["exact", "raw_hash"], descending=[True, False])
        .group_by("func_hash", maintain_order=True)
        .agg(pl.col("class").first(), pl.col("parasite").any(), members=pl.len(),
             members_par=pl.col("parasite").sum(), len=pl.col("len").first())
        .rename({"func_hash": "key"})
    )
    ex_func = ex_raw.join(f_of.rename({"raw_hash": "key"}), on="key", how="left")
    car_func = car_raw.join(f_of.rename({"raw_hash": "key"}), on="key", how="left")
    sanity.update(
        unmapped_exact=int(ex_func["func_hash"].is_null().sum()),
        unmapped_carriers=int(car_func["func_hash"].is_null().sum()),
    )
    # A hash missing from genomes.csv is its own group (counted above; expected 0).
    ex_func = ex_func.select("somatic", "executor", key=pl.coalesce("func_hash", "key"), win="win")
    car_func = car_func.select(pl.coalesce("func_hash", "key").alias("key"), "win", *SUMS)
    g_func = genome_table(ex_func, car_func, finfo.select("key", "class", "parasite"))
    g_func = g_func.join(finfo.select("key", "members", "members_par", "len"), on="key", how="left")
    srows += [dict(seed=seed, grouping="func", **r) for r in window_measures(g_func, ex_tot, som_tot)]
    g_func.rename({"key": "func_hash", "win": "window"}).select(
        pl.lit(seed).alias("seed"), "window", "func_hash", "members", "members_par", "len", "class", "replicator",
        "dependent", "parasite", "exact", "exact_somatic", "executors", "carriers", *SUMS, "a_G", "g_G",
    ).write_csv(OUT / f"funcs_s{seed}.csv")
    wf = g_func.filter(pl.col("win") == 0)
    sanity.update(
        scope_func=wf.height,
        func_par_rep_class=int((wf["parasite"] & wf["replicator"]).sum()),
    )
    del ex_func, car_func, g_func, f_of, finfo

    # --- exploratory: carriers ------------------------------------------------------
    scope = whole.select(
        birth_hash="key",
        group=pl.when(pl.col("parasite")).then(pl.lit("parasite"))
        .when(pl.col("replicator")).then(pl.lit("replicator"))
        .otherwise(pl.lit("dependent_nonparasite")),
    )
    den = pl.col("absorb_gain_m") + pl.col("born_with_m")
    c = (
        car.select("birth_hash", "offspring", *STATS)
        .join(cls.rename({"raw_hash": "birth_hash"}), on="birth_hash", how="left")
        .join(scope, on="birth_hash", how="left")
        .with_columns(
            pl.col("class").fill_null("unknown"),
            pl.col("group").fill_null("out_of_scope"),
            off=pl.when(pl.col("offspring") == 0).then(pl.lit("0"))
            .when(pl.col("offspring") == 1).then(pl.lit("1")).otherwise(pl.lit("2+")),
            a=pl.col("absorbs") / pl.col("executed"),
            g=pl.when(den > 0).then(pl.col("absorb_gain_m") / den),
        )
        .select("class", "group", "off", "offspring", "a", "g")
    )
    del car, car_raw
    crows = []
    for split, col in (("all", None), ("class", "class"), ("group", "group"), ("offspring", "off")):
        keyed = c.with_columns(k=pl.lit("all")) if col is None else c.with_columns(k=pl.col(col))
        agg = keyed.group_by("k").agg(
            carriers=pl.len(),
            g_defined=pl.col("g").is_not_null().sum(),
            low_g=(pl.col("g") < LOW_G).sum(),
            a_med=pl.col("a").median(),
            g_med=pl.col("g").median(),
        )
        crows += [dict(seed=seed, split=split, key=r.pop("k"), **r) for r in agg.iter_rows(named=True)]
    hrows = []
    strata = {"all": pl.lit(True), "offspring0": pl.col("offspring") == 0, "offspring1plus": pl.col("offspring") >= 1}
    for st, f in strata.items():
        y = c.filter(f)
        for m in ("a", "g"):
            v = y[m].drop_nulls().to_numpy()
            for i, n in enumerate(np.histogram(v, bins=EDGES)[0]):
                hrows.append(dict(seed=seed, measure=m, stratum=st, bin=i, lo=float(EDGES[i]),
                                  hi=float(EDGES[i + 1]), carriers=int(n)))
    del c
    gc.collect()
    sanity["wall_s"] = round(time.perf_counter() - t0, 1)
    return dict(seeds=srows, carriers=crows, hist=hrows, sanity=sanity)


# --- summary -------------------------------------------------------------------------

f2 = lambda v: "–" if v is None else f"{v:.2f}"
f3 = lambda v: "–" if v is None else f"{v:.3f}"
f0 = lambda v: "–" if v is None else f"{v:,.0f}"
pct = lambda v: "–" if v is None else f"{100 * v:.2f}%"
pct1 = lambda v: "–" if v is None else f"{100 * v:.1f}%"


def _get(df: pl.DataFrame, seed: int, w: int, col: str):
    x = df.filter((pl.col("seed") == seed) & (pl.col("window") == w))
    return x[col][0] if x.height else None


def _med_over(df: pl.DataFrame, w: int, col: str, seeds: list[int]):
    s = df.filter((pl.col("window") == w) & pl.col("seed").is_in(seeds))[col].drop_nulls()
    return s.median() if s.len() else None


def _checks(df: pl.DataFrame, live: list[int], label: str) -> tuple[list[str], dict]:
    """Prediction 1-3 tables and check lines for one grouping."""
    W = range(1, N_WIN + 1)
    late = range(2, N_WIN + 1)
    seeds = sorted(df["seed"].unique().to_list(), key=lambda s: (s in EXCLUDED, s))
    out: list[str] = []
    res: dict = {}

    # Prediction 1, window shares.
    out += [
        f"#### Prediction 1 ({label}): share of the window's exact births held by in-scope genomes with g_G < {LOW_G}",
        "",
        "| seed | " + " | ".join(f"w{w}" for w in W) + " | whole run | max w2–10 | all w2–10 < 1% |",
        "|---|" + "---|" * (N_WIN + 3),
    ]
    ok_seeds = 0
    for s in seeds:
        vals = [_get(df, s, w, "lowg_share") for w in W]
        lv = [_get(df, s, w, "lowg_share") for w in late]
        good = all(v is not None and v < 0.01 for v in lv)
        mx = max((v for v in lv if v is not None), default=None)
        if s in live:
            ok_seeds += good
        tag = f"{s} (excluded)" if s in EXCLUDED else str(s)
        out.append(f"| {tag} | " + " | ".join(pct(v) for v in vals)
                   + f" | {pct(_get(df, s, 0, 'lowg_share'))} | {pct(mx)} | {'yes' if good else 'no'} |")
    meds = [_med_over(df, w, "lowg_share", live) for w in W]
    out.append(f"| median 1–9 | " + " | ".join(pct(v) for v in meds)
               + f" | {pct(_med_over(df, 0, 'lowg_share', live))} | | |")
    res["p1_seeds"] = ok_seeds
    res["p1_meds"] = meds

    # Prediction 1, whole-run medians of g_G; prediction 2, a_G.
    out += [
        "",
        f"#### Predictions 1 and 2 ({label}): whole-run exact-birth-weighted medians per seed (unweighted in brackets)",
        "",
        "| seed | rep genomes | par genomes | g_G rep | g_G par | g_G dep | g_G all | a_G rep | a_G par | a_G dep "
        "| a_G all | par > rep | rep in 0.17–0.23 | par in 0.20–0.25 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    p1b = dict(rep=0, par=0, both=0)
    p2 = dict(gt=0, rep_in=0, par_in=0, rep_vals=[], par_vals=[])
    for s in seeds:
        v = lambda c: _get(df, s, 0, c)
        gr, gp, ar, ap = v("g_med_rep"), v("g_med_par"), v("a_med_rep"), v("a_med_par")
        gt = ar is not None and ap is not None and ap > ar
        rin = ar is not None and P2_RANGE["rep"][0] <= ar <= P2_RANGE["rep"][1]
        pin = ap is not None and P2_RANGE["par"][0] <= ap <= P2_RANGE["par"][1]
        if s in live:
            p1b["rep"] += gr is not None and gr > 0.9
            p1b["par"] += gp is not None and gp > 0.9
            p1b["both"] += (gr is not None and gr > 0.9) and (gp is not None and gp > 0.9)
            p2["gt"] += gt
            p2["rep_in"] += rin
            p2["par_in"] += pin
            if ar is not None:
                p2["rep_vals"].append(ar)
            if ap is not None:
                p2["par_vals"].append(ap)
        both = lambda c: f"{f3(v(c))} ({f3(v(c + '_unw'))})"
        tag = f"{s} (excluded)" if s in EXCLUDED else str(s)
        out.append(
            f"| {tag} | {f0(v('rep_genomes'))} | {f0(v('par_genomes'))} | {both('g_med_rep')} | {both('g_med_par')} "
            f"| {both('g_med_dep')} | {both('g_med_all')} | {both('a_med_rep')} | {both('a_med_par')} "
            f"| {both('a_med_dep')} | {both('a_med_all')} | {'yes' if gt else 'no'} | {'yes' if rin else 'no'} "
            f"| {'yes' if pin else 'no'} |"
        )
    mv = lambda c: _med_over(df, 0, c, live)
    out.append(
        f"| median 1–9 | {f0(mv('rep_genomes'))} | {f0(mv('par_genomes'))} | {f3(mv('g_med_rep'))} | {f3(mv('g_med_par'))} "
        f"| {f3(mv('g_med_dep'))} | {f3(mv('g_med_all'))} | {f3(mv('a_med_rep'))} | {f3(mv('a_med_par'))} "
        f"| {f3(mv('a_med_dep'))} | {f3(mv('a_med_all'))} | | | |"
    )
    res["p1b"] = p1b
    res["p2"] = p2

    # Prediction 3.
    out += [
        "",
        f"#### Prediction 3 ({label}): exact-birth-weighted share of in-scope genomes with a_G in "
        f"[{BAND[0]}, {BAND[1]}]",
        "",
        "| seed | " + " | ".join(f"w{w}" for w in W) + " | whole run |",
        "|---|" + "---|" * (N_WIN + 1),
    ]
    for s in seeds:
        tag = f"{s} (excluded)" if s in EXCLUDED else str(s)
        out.append(f"| {tag} | " + " | ".join(f3(_get(df, s, w, "band_share")) for w in W)
                   + f" | {f3(_get(df, s, 0, 'band_share'))} |")
    bmeds = [_med_over(df, w, "band_share", live) for w in W]
    out.append("| median 1–9 | " + " | ".join(f3(v) for v in bmeds) + f" | {f3(_med_over(df, 0, 'band_share', live))} |")
    res["p3_meds"] = bmeds

    # Per window medians over seeds: group medians and unweighted shares.
    out += [
        "",
        f"#### Per window, medians over seeds 1–9 ({label}): weighted group medians, unweighted shares, scope",
        "",
        "| window | in-scope genomes | in-scope share of exact births | no-carrier share of in-scope births "
        "| g_G rep | g_G par | g_G dep | a_G rep | a_G par | a_G dep | low-g share (unweighted, genomes) "
        "| band share (unweighted) | low-g weight that is dependent |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for w in [0, *W]:
        x = df.filter((pl.col("window") == w) & pl.col("seed").is_in(live)).with_columns(
            scope_frac=pl.col("scope_exact") / pl.col("exact"),
            nocar_frac=pl.col("no_carrier_exact") / pl.col("scope_exact"),
        )
        m = lambda c: x[c].drop_nulls().median() if x[c].drop_nulls().len() else None
        out.append(
            f"| {'whole run' if w == 0 else w} | {f0(m('genomes'))} | {f3(m('scope_frac'))} | {pct(m('nocar_frac'))} "
            f"| {f3(m('g_med_rep'))} | {f3(m('g_med_par'))} | {f3(m('g_med_dep'))} | {f3(m('a_med_rep'))} "
            f"| {f3(m('a_med_par'))} | {f3(m('a_med_dep'))} | {pct(m('lowg_share_unw'))} | {f3(m('band_share_unw'))} "
            f"| {f3(m('lowg_dep_frac'))} |"
        )

    # Check lines.
    n = len(live)
    late_meds = meds[1:]
    late_b = bmeds[1:]
    p1_ok = ok_seeds >= 8 and p1b["both"] == n
    p2_ok = p2["gt"] >= 8
    p3_ok = all(v is not None and v >= 0.90 for v in late_b)
    rng = lambda xs: f"{min(xs):.3f}–{max(xs):.3f}" if xs else "–"
    out += [
        "",
        f"#### Prediction checks ({label})",
        "",
        f"1. Low-absorb share < 1% in every window 2–10 in {ok_seeds} of {n} surviving seeds (>= 8 wanted); "
        f"seed medians by window 2–10: {', '.join(pct(v) for v in late_meds)}. Whole-run weighted median g_G "
        f"> 0.9: replicator-class in {p1b['rep']} of {n}, parasite in {p1b['par']} of {n}, both in {p1b['both']} "
        f"of {n} ({n} wanted). **{'Confirmed' if p1_ok else 'Not confirmed'}.**",
        f"2. Whole-run weighted median a_G parasite > replicator-class in {p2['gt']} of {n} (>= 8 wanted). "
        f"Replicator-class {rng(p2['rep_vals'])} (registered 0.17–0.23; in range in {p2['rep_in']} of {n}); "
        f"parasite {rng(p2['par_vals'])} (registered 0.20–0.25; in range in {p2['par_in']} of {n}). "
        f"**{'Confirmed' if p2_ok else 'Not confirmed'}** (direction; the ranges are reported, not scored).",
        f"3. Weighted share of a_G in [{BAND[0]}, {BAND[1]}], seed medians by window 2–10: "
        f"{', '.join(f3(v) for v in late_b)} (>= 0.90 in every window wanted; minimum "
        f"{f3(min((v for v in late_b if v is not None), default=None))}). **{'Confirmed' if p3_ok else 'Not confirmed'}.**",
    ]
    res.update(p1_ok=p1_ok, p2_ok=p2_ok, p3_ok=p3_ok)
    return out, res


def _posthoc(df: pl.DataFrame, live: list[int], label: str) -> list[str]:
    """Post hoc (not registered): where the low-absorb weight comes from.
    'Somatic' exact birth: the executor's body had changed since its own
    birth (births.csv parent_hash != parent_now_hash), so the child copies a
    body no carrier of the genome was born with."""
    late = range(2, N_WIN + 1)
    seeds = sorted(df["seed"].unique().to_list(), key=lambda s: (s in EXCLUDED, s))
    out = [
        f"#### Low-absorb genomes ({label}), post hoc",
        "",
        "Columns: share of all exact births made by an executor whose body had changed since its own birth "
        "('somatic'; whole run); registered low-g share, median over windows 2–10; of the low-g exact births in "
        "windows 2–10, the share made by such executors, and the split by class (replicator / dependent / of which "
        "parasite); median number of distinct executors per low-g genome (whole run); share of carriers that "
        "had >= 1 offspring, low-g genomes vs in-scope genomes with g_G >= 0.5 (whole run); low-g share when scope "
        "also requires >= 2 non-somatic exact births (executor born with the genome), max over windows 2–10, and "
        "whether it is < 1% in all of them; in-scope births with no carrier in the window (g_G undefined, not "
        "low-g), max over windows 2–10.",
        "",
        "| seed | somatic share of exact births | low-g share, median w2–10 | low-g weight somatic | low-g weight rep / dep / par "
        "| executors per low-g genome | carriers reproducing, low-g / other | low-g share, non-somatic scope, max w2–10 "
        "| all < 1% | no-carrier share, max w2–10 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    ok = 0
    for s in seeds:
        x = df.filter(pl.col("seed") == s)
        xl = x.filter(pl.col("window").is_in(list(late)))
        w0 = x.filter(pl.col("window") == 0)
        if not w0.height or not w0["exact"][0]:
            out.append(f"| {s} (excluded) | – | – | – | – | – | – | – | – | – |")
            continue
        r0 = w0.row(0, named=True)
        lowex = int(xl["lowg_exact"].sum())
        div = lambda n, d: n / d if d else None
        germ = xl["lowg_share_germ"].drop_nulls()
        good = germ.len() == len(late) and bool((germ < 0.01).all())
        if s in live:
            ok += good
        tag = f"{s} (excluded)" if s in EXCLUDED else str(s)
        out.append(
            f"| {tag} | {pct1(r0['somatic_share'])} | {pct(xl['lowg_share'].median())} "
            f"| {pct1(div(int(xl['lowg_somatic_exact'].sum()), lowex))} "
            f"| {pct1(div(int(xl['lowg_rep_exact'].sum()), lowex))} / {pct1(div(int(xl['lowg_dep_exact'].sum()), lowex))} "
            f"/ {pct1(div(int(xl['lowg_par_exact'].sum()), lowex))} | {f0(r0['lowg_executors_med'])} "
            f"| {pct1(r0['lowg_repro_frac'])} / {pct1(r0['repro_frac_other'])} | {pct(germ.max() if germ.len() else None)} "
            f"| {'yes' if good else 'no'} | {pct(xl['no_carrier_share'].max())} |"
        )
    meds = [_med_over(df, w, "lowg_share_germ", live) for w in late]
    out += [
        "",
        f"Low-g share with the non-somatic scope ({label}), seed medians by window 2–10: "
        f"{', '.join(pct(v) for v in meds)}; < 1% in every window 2–10 in {ok} of {len(live)} surviving seeds. "
        "Post hoc, not a test of the registered prediction.",
        "",
    ]
    return out


def _hist_tables(h: pl.DataFrame, live: list[int]) -> list[str]:
    x = h.filter(pl.col("seed").is_in(live)).group_by("measure", "stratum", "bin", "lo", "hi").agg(pl.col("carriers").sum())
    out = []
    for m, name in (("a", "a = absorbs / executed"), ("g", "g = absorb_gain / (absorb_gain + born_with)")):
        y = x.filter(pl.col("measure") == m)
        tot = {st: int(y.filter(pl.col("stratum") == st)["carriers"].sum()) for st in ("all", "offspring0", "offspring1plus")}
        out += [
            f"Per-carrier {name}, pooled seeds 1–9, 20 bins (counts and share of the column's carriers; "
            f"columns: all carriers / carriers with no offspring / carriers with >= 1 offspring):",
            "",
            "| bin | all | % | no offspring | % | >= 1 offspring | % |",
            "|---|---|---|---|---|---|---|",
        ]
        for i in range(BINS):
            cell = []
            for st in ("all", "offspring0", "offspring1plus"):
                n = int(y.filter((pl.col("stratum") == st) & (pl.col("bin") == i))["carriers"].sum())
                cell += [f"{n:,}", pct1(n / tot[st] if tot[st] else None)]
            hi = "]" if i == BINS - 1 else ")"
            out.append(f"| [{EDGES[i]:.2f}, {EDGES[i + 1]:.2f}{hi} | " + " | ".join(cell) + " |")
        out.append(f"| total | {tot['all']:,} | | {tot['offspring0']:,} | | {tot['offspring1plus']:,} | |")
        out.append("")
    return out


def _carrier_split_tables(c: pl.DataFrame, live: list[int]) -> list[str]:
    out = []
    x = c.filter(pl.col("seed").is_in(live))
    for split, order, title in (
        ("class", CLASS_ORDER, "the harness class of the carrier's birth genome"),
        ("group", GROUP_ORDER, "the E011 group of the carrier's birth genome (whole-run scope; "
                               "`out_of_scope` = < 2 exact births in the run)"),
        ("offspring", ["0", "1", "2+"], "the carrier's offspring count"),
        ("all", ["all"], "all carriers"),
    ):
        y = x.filter(pl.col("split") == split)
        out += [
            f"Carriers with g < {LOW_G} by {title}; pooled seeds 1–9 (share of carriers with g defined), with the "
            "range of the per-seed shares and the median over seeds of the per-seed median a and g:",
            "",
            "| key | carriers | share of all carriers | g < 0.5 | share g < 0.5 | per-seed range | median a | median g |",
            "|---|---|---|---|---|---|---|---|",
        ]
        tot_all = int(x.filter(pl.col("split") == "all")["carriers"].sum())
        for k in order:
            z = y.filter(pl.col("key") == k)
            if not z.height:
                continue
            nc, nd, nl = int(z["carriers"].sum()), int(z["g_defined"].sum()), int(z["low_g"].sum())
            per = (z["low_g"] / z["g_defined"]).drop_nulls().drop_nans()
            rng = f"{100 * per.min():.1f}–{100 * per.max():.1f}%" if per.len() else "–"
            out.append(
                f"| {k} | {nc:,} | {pct1(nc / tot_all)} | {nl:,} | {pct1(nl / nd if nd else None)} | {rng} "
                f"| {f3(z['a_med'].median())} | {f3(z['g_med'].median())} |"
            )
        out.append("")
    return out


def _genome_hist(live: list[int]) -> list[str]:
    """Whole-run per-genome distributions of a_G and g_G over in-scope raw
    genomes, pooled over seeds, weighted and unweighted."""
    frames = []
    for s in live:
        p = OUT / f"genomes_s{s}.csv"
        if p.exists():
            frames.append(pl.scan_csv(p, schema_overrides={"raw_hash": pl.Utf8, "func_hash": pl.Utf8})
                          .filter(pl.col("window") == 0).select("exact", "a_G", "g_G", "dependent").collect())
    if not frames:
        return []
    g = pl.concat(frames)
    out = [
        "Per-genome whole-run distributions over in-scope raw genomes, pooled seeds 1–9: share of genomes "
        "(unweighted) and of exact births (weighted) per bin of a_G and of g_G; last two columns: share of the bin's "
        "exact births that is dependent-class.",
        "",
        "| bin | a_G genomes | a_G weighted | g_G genomes | g_G weighted | dependent share of a_G bin | dependent share of g_G bin |",
        "|---|---|---|---|---|---|---|",
    ]
    cols = {}
    for m in ("a_G", "g_G"):
        y = g.filter(pl.col(m).is_not_null())
        v = y[m].to_numpy()
        w = y["exact"].to_numpy().astype(float)
        dep = y["dependent"].to_numpy()
        n_u = np.histogram(v, bins=EDGES)[0]
        n_w = np.histogram(v, bins=EDGES, weights=w)[0]
        n_d = np.histogram(v[dep], bins=EDGES, weights=w[dep])[0]
        cols[m] = (n_u / n_u.sum(), n_w / n_w.sum(), np.where(n_w > 0, n_d / np.maximum(n_w, 1), np.nan))
    for i in range(BINS):
        hi = "]" if i == BINS - 1 else ")"
        dfmt = lambda v: "–" if np.isnan(v) else f"{v:.2f}"
        out.append(
            f"| [{EDGES[i]:.2f}, {EDGES[i + 1]:.2f}{hi} | {pct1(cols['a_G'][0][i])} | {pct1(cols['a_G'][1][i])} "
            f"| {pct1(cols['g_G'][0][i])} | {pct1(cols['g_G'][1][i])} | {dfmt(cols['a_G'][2][i])} | {dfmt(cols['g_G'][2][i])} |"
        )
    out.append(f"| genomes | {g.height:,} | {int(g['exact'].sum()):,} exact births | | | | |")
    out.append("")
    return out


def summarize() -> str:
    df = pl.read_csv(OUT / "seeds.csv")
    san = pl.read_csv(OUT / "sanity.csv")
    car = pl.read_csv(OUT / "carriers.csv", schema_overrides={"key": pl.Utf8})
    hist = pl.read_csv(OUT / "hist.csv")
    live = sorted(s for s in df["seed"].unique().to_list() if s not in EXCLUDED)
    raw, func = df.filter(pl.col("grouping") == "raw"), df.filter(pl.col("grouping") == "func")

    lines = [
        "# E011 summary: producer/consumer split in E007",
        "",
        f"Seeds {', '.join(map(str, live))} (seed 10 died at tick 1,179; shown, not in medians or counts). "
        f"Windows of {WINDOW:,} ticks, window w = ({WINDOW:,}(w−1), {WINDOW:,}w]; 'whole run' is window 0 in the "
        "CSVs. Shares of exact births are weighted by exact births; medians of a_G and g_G are exact-birth-weighted "
        "medians over in-scope genomes unless marked unweighted. Record: "
        "docs/research/experiments/2026-10-12-e011-absorb-split.md. Runner: analysis/e011_absorb_split.py.",
        "",
        "## Sanity checks",
        "",
        "| seed | ticks run | births | exact births | deaths | alive at end | births + founders − deaths − alive "
        "| carriers (executed >= 1) | executed = 0 (left out) | born_with_m = 0 (all rows / carriers / of which absorbed) "
        "| g undefined | other-income columns | in-scope genomes raw / func | dependent (E011 / E005 table) "
        "| parasite genomes (E005 / in scope) | func groups: parasite with replicator class | hashes missing from genomes.csv | wall s |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in san.sort("seed").iter_rows(named=True):
        lines.append(
            f"| {r['seed']} | {r['ticks_run']:,} | {r['births']:,} | {r['exact_births']:,} | {r['deaths']:,} | {r['alive_end']:,} "
            f"| {r['balance']} | {r['carriers']:,} | {r['executed0']:,} | {r['born0_rows']:,} / {r['born0_carriers']:,} / "
            f"{r['born0_carriers_absorbed']:,} | {r['g_undefined']:,} | {r['other_income_cols']} "
            f"| {r['scope_raw']:,} / {r['scope_func']:,} | {r['dependent_raw']:,} / {r['dependent_e005']:,} "
            f"| {r['parasites']} / {r['parasites_in_scope']} | {r['func_par_rep_class']} "
            f"| {r['unmapped_exact'] + r['unmapped_carriers']} | {r['wall_s']} |"
        )
    lines += ["", "## Predictions 1–3, raw birth hash (registered)", ""]
    text, res = _checks(raw, live, "raw hash")
    lines += text

    # H2 scoring inputs.
    lm = res["p1_meds"][1:]
    lm_v = [v for v in lm if v is not None]
    med_window = float(np.median(lm_v)) if lm_v else None
    late = raw.filter(pl.col("seed").is_in(live) & (pl.col("window") >= 2))
    low_ex, low_dep = int(late["lowg_exact"].sum()), int(late["lowg_dep_exact"].sum())
    supported = med_window is not None and med_window >= 0.05 and low_ex and low_dep / low_ex >= 0.5
    verdict = "Refuted" if res["p1_ok"] else ("Supported" if supported else "Mixed")
    lines += [
        "",
        "#### H2 scoring inputs (record, 'Scoring H2')",
        "",
        f"- Prediction 1 {'holds' if res['p1_ok'] else 'does not hold'}.",
        f"- Low-absorb share of exact births in the median window from 2 on (median over windows 2–10 of the seed "
        f"medians): {pct(med_window)} (>= 5% for 'supported').",
        f"- Dependent-class part of the low-absorb weight, pooled over seeds 1–9 and windows 2–10: "
        f"{low_dep:,} of {low_ex:,} exact births ({pct(low_dep / low_ex if low_ex else None)}).",
        f"- By the record's rule: **{verdict}**.",
        "",
        "## Post hoc (not registered): what the low-absorb genomes are",
        "",
        "Added after the first look at seed 1, where prediction 1 failed: the low-g genomes' exact births were "
        "almost all made by executors whose body had changed since birth. These columns describe that; they do "
        "not change the scoring above.",
        "",
    ]
    lines += _posthoc(raw, live, "raw hash")
    lines += _posthoc(func, live, "func_hash")
    lines += [
        "## Exploratory (item 4)",
        "",
        "### Per-carrier distributions",
        "",
        "Every carrier is counted once (deaths plus alive at the end, executed >= 1). Carriers with "
        "born_with_m + absorb_gain_m = 0 have no g and are left out of the g columns (sanity table, 'g undefined').",
        "",
    ]
    lines += _hist_tables(hist, live)
    lines += _carrier_split_tables(car, live)
    lines += ["### Per-genome distributions", ""]
    lines += _genome_hist(live)
    lines += [
        "### Predictions 1–3 with genomes grouped by func_hash",
        "",
        "A func group's exact births are the sum of its raw members' exact births (raw_hash == parent_now_hash); "
        "in scope with >= 2 of them; parasite if any raw member has parasite_2; class = harness class of the member "
        "with the most whole-run exact births (ties: lowest raw hash), used in every window. Carriers are pooled "
        "over all raw members.",
        "",
    ]
    ftext, fres = _checks(func, live, "func_hash")
    lines += ftext
    lines += [
        "",
        "## Implementation notes",
        "",
        "- Low-absorb share (prediction 1): numerator = exact births in the window of in-scope genomes with "
        "g_G < 0.5; denominator = all exact births in the window, including genomes with a single exact birth "
        "there (the record: 'of the window's exact births'). `lowg_share_scope` in seeds.csv uses in-scope "
        "births as the denominator.",
        "- A genome in scope in a window may have no carrier that dies in that window (its children die in the "
        "next one). Its a_G and g_G are then undefined: it counts in the prediction-1 denominator but not as "
        "low-absorb, and it is left out of the prediction-3 distribution (denominator = in-scope births with a "
        "defined a_G). The share of in-scope births affected is in the per-window table ('no-carrier share').",
        "- Prediction 1's g_G > 0.9 part is scored on the whole-run medians, one per seed; per-window group "
        "medians are in seeds.csv (`g_med_rep`, `g_med_par`) and in the per-window table.",
        "- A seed without parasite genomes would count as failing the g_G and a_G parts that need them.",
        "- Prediction 2's ranges are reported with a count in range; the check line scores the direction "
        "(parasite > replicator-class in >= 8 of 9), the only part stated as a count.",
        "- 'Alive at the end' is orgs.csv at tick 250,000. For seed 10 (ticks run 1,179) there is no such "
        "census, so its carriers are its deaths only; every organism of that run died.",
        "- The founder (the ancestor, seeded with 100 units, no births.csv row) is a carrier of the ancestor "
        "genome like any other.",
        "- H2 scoring, 'the median window from 2 on': the median over windows 2–10 of the per-window medians "
        "over seeds. The per-seed medians over windows 2–10 (post hoc table) are 2.13–2.47%, the same side of 5%.",
        "- Post hoc 'somatic' exact birth: births.csv parent_hash (the executor's birth hash) != parent_now_hash "
        "(its body at `divide`). It is a raw-hash test in both groupings, so under func_hash an executor whose "
        "body changed silently (same func_hash) also counts as somatic.",
        "- Weighted medians: the exact-birth-weighted median of the module docstring (first value at which the "
        "cumulative weight reaches half; mean of two values on an exact tie). Checked against np.median over "
        "values repeated by their weights for seed 2, whole run, and the seed-2 window-5 prediction 1 and 3 "
        "shares against a separate recomputation from the raw files: identical.",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*", default=SEEDS)
    ap.add_argument("--summarize-only", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    if not a.summarize_only:
        old = {}
        for name in ("seeds", "carriers", "hist", "sanity"):
            p = OUT / f"{name}.csv"
            old[name] = pl.read_csv(p, schema_overrides={"key": pl.Utf8} if name == "carriers" else None) \
                .filter(~pl.col("seed").is_in(a.seeds)) if p.exists() else None
        new = {k: [] for k in old}
        for s in a.seeds:
            r = analyse(s)
            new["seeds"] += r["seeds"]
            new["carriers"] += r["carriers"]
            new["hist"] += r["hist"]
            new["sanity"].append(r["sanity"])
            print(f"s{s}: {r['sanity']['carriers']:,} carriers, {r['sanity']['exact_births']:,} exact births, "
                  f"{r['sanity']['wall_s']} s", flush=True)
            gc.collect()
        for k, rows in new.items():
            df = pl.DataFrame(rows, infer_schema_length=None)
            if old[k] is not None and old[k].height:
                df = pl.concat([old[k], df], how="diagonal_relaxed")
            df.sort("seed").write_csv(OUT / f"{k}.csv")

    text = summarize()
    (OUT / "summary.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
