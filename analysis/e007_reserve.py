"""E007 reserve check (synthesis-2026-10-13 §2 B, PLAN §8.5). No new world runs;
reads the ten E007 runs (runs/e007/std/s<seed>/, docs/instrumentation.md).

The synthesis argues that the host's store is one pass deep because
proportional absorb on a shared pool equilibrates every host to zero margin,
"whatever the cap", and names the check: the distribution of `energy_m` and
`max_energy_m` for replicator-class bodies against the store cap (64 units per
byte, 1,344 for 21 bytes); "if `max_energy_m` sits an order of magnitude below
1,344 in every seed, the argument holds".

Usage (from analysis/):

    uv run e007_reserve.py                    # all seeds, then the summary
    uv run e007_reserve.py --summarize-only   # reuse the CSVs below

Definitions:

  replicator-class  classes.csv class == replicator for the body's birth hash
  stationary        death or census tick in (25,000, 250,000] (PLAN §8.2)
  cap               store_cap_per_byte * len (meta.json; 1,344 units at 21)
  reached the cap   max_energy_m >= cap. Absorb clamps the store at exactly
                    the cap (`take = min(avail, room)`), and E007 has no
                    transfer, so this is "absorb was refused by the cap at
                    least once in its life".
  reproducer        a death with divides_ok >= 1. A body that dies before its
                    first divide never finished an absorb phase, so its
                    max_energy_m says little about the reserve; both groups
                    are reported.
  capped share      sum(absorb_capped) / sum(absorbs) over the group: absorbs
                    that got less than the pool offered because the store was
                    full.
  births share      sum(divides_ok) of reproducers that reached the cap over
                    sum(divides_ok) of all reproducers.
  cost per pass     (spent_m + upkeep_m + endowed_m) / divides_ok, median over
                    reproducers with divides_ok >= 3 and allocs_fail == 0. It
                    includes the unfinished last pass, so it overstates a pass
                    by up to a third at 3 divides.
  active to death   a reproducer whose last divide was at most ACTIVE ticks
                    before it died
  snapshot          orgs.csv rows (living bodies at census ticks, every 500)
  state             of a snapshot body, by ticks since its last divide
                    (ACTIVE = 50; a K = 120 cycle is about 20 ticks):
                    `active` divided within ACTIVE ticks; `first` has never
                    divided and is at most ACTIVE ticks old; `stalled` is
                    every other body. `host` is active or first.
  unchanged         now_hash == birth_hash (no somatic change since birth)
  near cap          snapshot energy_m >= 0.9 cap (a body at the cap spends
                    while it runs, so the snapshot rarely sees exactly cap)
  ration            the absorb ration of the body's patch at the snapshot,
                    absorb_rate * pool_m / patch_cap (units), patch = start //
                    patch_size

Outputs in runs/e007/reserve/: seeds.csv (one row per seed), bins.csv (per
seed and tick bin: 2,500-tick bins to 25,000, then the E007 25,000-tick
windows), summary.md.
"""

from __future__ import annotations

import argparse
import gc
import json

import polars as pl

from evo_run import HASH_COLS, MILLI, ROOT

RUNS = ROOT / "runs" / "e007"
ARM = "std"
OUT = RUNS / "reserve"
SEEDS = list(range(1, 11))
EXCLUDED = {10}  # died at tick 1,179 (E007); reported, not in medians
T0 = 25_000
EARLY_BIN = 2_500
WINDOW = 25_000
NEAR = 0.9
ACTIVE = 50
STATES = ["host", "active", "first", "stalled"]
DEATH_COLS = ["tick", "age", "len", "birth_hash", "energy_m", "max_energy_m", "absorbs", "absorb_capped",
              "absorb_short", "divides_ok", "allocs_ok", "allocs_fail", "spent_m", "upkeep_m", "endowed_m",
              "last_divide_tick"]


def _scan(seed: int, name: str) -> pl.LazyFrame:
    return pl.scan_csv(RUNS / ARM / f"s{seed}" / f"{name}.csv",
                       schema_overrides={c: pl.Utf8 for c in HASH_COLS[name]})


def _bin() -> pl.Expr:
    """Bin label: ticks ((k-1)*B, k*B] with B = 2,500 to 25,000, then 25,000."""
    t = pl.col("tick")
    return (pl.when(t <= T0).then((t + EARLY_BIN - 1) // EARLY_BIN * EARLY_BIN)
            .otherwise((t + WINDOW - 1) // WINDOW * WINDOW)).cast(pl.Int64).alias("bin_end")


def _q(col: str, qs: list[float], scale: float = MILLI) -> list[pl.Expr]:
    return [(pl.col(col).quantile(q, "nearest") / scale).alias(f"{col.removesuffix('_m')}_p{int(q * 100)}")
            for q in qs]


def analyse(seed: int) -> tuple[dict, list[dict]]:
    d = RUNS / ARM / f"s{seed}"
    cfg = json.loads((d / "meta.json").read_text())["config"]
    per_byte, rate, pcap, psize = (cfg["store_cap_per_byte"], cfg["absorb_rate"], cfg["patch_cap"],
                                   cfg["patch_size"])
    reps = (pl.read_csv(d / "classes.csv", schema_overrides={"raw_hash": pl.Utf8})
            .filter(pl.col("class") == "replicator").select(pl.col("raw_hash").alias("birth_hash")))
    cap = pl.col("len") * per_byte

    de = (_scan(seed, "deaths").select(DEATH_COLS).join(reps.lazy(), on="birth_hash", how="semi")
          .with_columns(cap.alias("cap"), _bin()).with_columns(
              (pl.col("max_energy_m") >= pl.col("cap")).alias("reached"),
              (pl.col("divides_ok") >= 1).alias("repro")).collect())
    row: dict = {"seed": seed, "rep_deaths_all": de.height}
    st = de.filter(pl.col("tick") > T0)
    rp = st.filter("repro")
    row |= {
        "rep_deaths": st.height,
        "reproducers": rp.height,
        "cap_units_med": rp["cap"].median() / MILLI if rp.height else None,
    }
    for name, g in (("all", st), ("repro", rp)):
        if not g.height:
            continue
        row |= g.select(*_q("max_energy_m", [0.1, 0.5, 0.9, 0.99])).rename(
            lambda c: f"{name}_{c}").row(0, named=True)
        row |= {
            f"{name}_ge_tenth": g.select((pl.col("max_energy_m") >= pl.col("cap") / 10).mean()).item(),
            f"{name}_reached": g["reached"].mean(),
            f"{name}_capped_share": g["absorb_capped"].sum() / max(g["absorbs"].sum(), 1),
            f"{name}_short_share": g["absorb_short"].sum() / max(g["absorbs"].sum(), 1),
        }
    if rp.height:
        hit, miss = rp.filter("reached"), rp.filter(~pl.col("reached"))
        row |= {
            "births_share_reached": hit["divides_ok"].sum() / rp["divides_ok"].sum(),
            "age_med_reached": hit["age"].median(), "age_med_other": miss["age"].median(),
            "div_med_reached": hit["divides_ok"].median(), "div_med_other": miss["divides_ok"].median(),
            "allocfail_reached": hit["allocs_fail"].sum() / max(hit["allocs_ok"].sum() + hit["allocs_fail"].sum(), 1),
            "allocfail_other": miss["allocs_fail"].sum() / max(miss["allocs_ok"].sum() + miss["allocs_fail"].sum(), 1),
            "capped_share_reached": hit["absorb_capped"].sum() / max(hit["absorbs"].sum(), 1),
            "repro_energy_at_death_med": rp["energy_m"].median() / MILLI,
        }
        ad = rp.filter(pl.col("tick") - pl.col("last_divide_tick") <= ACTIVE)
        row |= {
            "active_to_death": ad.height / rp.height,
            "atd_births_share": ad["divides_ok"].sum() / rp["divides_ok"].sum(),
            "atd_reached": ad["reached"].mean(),
            "atd_births_share_reached": ad.filter("reached")["divides_ok"].sum() / rp["divides_ok"].sum(),
            **ad.select(*_q("max_energy_m", [0.5, 0.9])).rename(lambda c: f"atd_{c}").row(0, named=True),
        }
        cp = rp.filter((pl.col("divides_ok") >= 3) & (pl.col("allocs_fail") == 0))
        row |= {"pass_n": cp.height,
                "pass_cost_med": cp.select(((pl.col("spent_m") + pl.col("upkeep_m") + pl.col("endowed_m"))
                                            / pl.col("divides_ok")).median()).item() / MILLI if cp.height else None}

    bins = (de.filter("repro").group_by("bin_end").agg(
        pl.len().alias("reproducers"),
        (pl.col("max_energy_m").median() / MILLI).alias("max_energy_med"),
        (pl.col("max_energy_m").quantile(0.9, "nearest") / MILLI).alias("max_energy_p90"),
        pl.col("reached").mean().alias("reached"),
        (pl.col("absorb_capped").sum() / pl.col("absorbs").sum()).alias("capped_share"),
        (pl.col("divides_ok").filter("reached").sum() / pl.col("divides_ok").sum()).alias("births_share_reached"),
    ).sort("bin_end").with_columns(pl.lit(seed).alias("seed")))
    del de, st, rp
    gc.collect()

    # Snapshots: living bodies at census ticks, with the ration of their patch.
    pa = (_scan(seed, "patches").filter(pl.col("tick") > T0)
          .select("tick", "patch", (pl.col("pool_m") * rate / pcap / MILLI).alias("ration")))
    sn = (_scan(seed, "orgs").filter(pl.col("tick") > T0)
          .select("tick", "len", "start", "birth_hash", "now_hash", "birth_tick", "last_divide_tick", "energy_m",
                  "absorbs", "absorb_capped")
          .with_columns(cap.alias("cap"), (pl.col("start") // psize).alias("patch"))
          .join(pa, on=["tick", "patch"], how="left").collect())
    row["snap_all_energy_mean"] = sn["energy_m"].mean() / MILLI
    since = pl.col("tick") - pl.col("last_divide_tick")
    sn = sn.join(reps, on="birth_hash", how="semi").with_columns(
        (pl.col("energy_m") >= NEAR * pl.col("cap")).alias("near"),
        (pl.col("now_hash") == pl.col("birth_hash")).alias("unchanged"),
        pl.when((pl.col("last_divide_tick") >= 0) & (since <= ACTIVE)).then(pl.lit("active"))
        .when((pl.col("last_divide_tick") < 0) & (pl.col("tick") - pl.col("birth_tick") <= ACTIVE))
        .then(pl.lit("first")).otherwise(pl.lit("stalled")).alias("state"))
    row |= {"snap_n": sn.height, "ration_patches": pa.select(pl.col("ration").mean()).collect().item()}
    for st_name in STATES:
        g = sn.filter(pl.col("state").is_in(["active", "first"]) if st_name == "host" else pl.col("state") == st_name)
        row |= {
            f"{st_name}_share": g.height / sn.height,
            f"{st_name}_unchanged": g["unchanged"].mean(),
            f"{st_name}_energy_mean": g["energy_m"].mean() / MILLI,
            **g.select(*_q("energy_m", [0.1, 0.5, 0.9])).rename(lambda c: f"{st_name}_{c}").row(0, named=True),
            f"{st_name}_ge_tenth": g.select((pl.col("energy_m") >= pl.col("cap") / 10).mean()).item(),
            f"{st_name}_near": g["near"].mean(),
            f"{st_name}_capped_share": g["absorb_capped"].sum() / max(g["absorbs"].sum(), 1),
            f"{st_name}_ration": g["ration"].mean(),
        }
    u = sn.filter((pl.col("state") == "active") & pl.col("unchanged"))
    row |= {"active_unch_energy_p50": u["energy_m"].median() / MILLI, "active_unch_near": u["near"].mean()}
    return row, bins.to_dicts()


def _fmt(v, nd: int = 2) -> str:
    if v is None:
        return "–"
    if isinstance(v, float):
        return f"{v:,.{nd}f}"
    return f"{v:,}"


def _rng(df: pl.DataFrame, col: str, nd: int = 2, pct: bool = False) -> str:
    s = df[col].drop_nulls()
    if pct:
        return f"{s.min() * 100:.{nd}f}–{s.max() * 100:.{nd}f}%"
    return f"{s.min():,.{nd}f}–{s.max():,.{nd}f}"


def summarize() -> str:
    df = pl.read_csv(OUT / "seeds.csv").sort("seed")
    bins = pl.read_csv(OUT / "bins.csv")
    ok = df.filter(~pl.col("seed").is_in(list(EXCLUDED)))
    tenth = ok["cap_units_med"][0] / 10
    lines = [
        "# E007 reserve check (synthesis-2026-10-13 §2 B)",
        "",
        f"Seeds {', '.join(map(str, ok['seed']))}; seed 10 lost its founder at tick 1,179 and is not included. "
        f"Replicator-class bodies, deaths and census snapshots in ticks (25,000, 250,000]. Cap = 64 units per "
        f"byte ({ok['cap_units_med'][0]:,.0f} at the median length); a tenth of it is {tenth:,.1f}.",
        "",
        "## The check as stated: `max_energy_m` at death (units)",
        "",
        "| seed | reproducers | p10 | median | p90 | p99 | ≥ cap/10 | reached cap | all deaths: median | p90 | reached cap |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in ok.iter_rows(named=True):
        lines.append(
            f"| {r['seed']} | {r['reproducers']:,} | {_fmt(r['repro_max_energy_p10'], 0)} | "
            f"{_fmt(r['repro_max_energy_p50'], 0)} | {_fmt(r['repro_max_energy_p90'], 0)} | "
            f"{_fmt(r['repro_max_energy_p99'], 0)} | {r['repro_ge_tenth']:.3f} | {r['repro_reached']:.3f} | "
            f"{_fmt(r['all_max_energy_p50'], 0)} | {_fmt(r['all_max_energy_p90'], 0)} | {r['all_reached']:.3f} |")
    lines += [
        "",
        "Reproducers are deaths with at least one divide; \"all deaths\" includes the replicator-class bodies "
        "that died before their first divide (the majority), whose maximum is mostly the 16-unit endowment.",
        "",
        "## Who reaches the cap",
        "",
        "| seed | capped absorbs, all | capped absorbs, reached | births by reached | age med reached / other | "
        "divides med reached / other | alloc fail reached / other | energy at death med | cost per pass med (n) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in ok.iter_rows(named=True):
        lines.append(
            f"| {r['seed']} | {r['all_capped_share']:.3f} | {r['capped_share_reached']:.3f} | "
            f"{r['births_share_reached']:.3f} | {r['age_med_reached']:,.0f} / {r['age_med_other']:,.0f} | "
            f"{r['div_med_reached']:,.0f} / {r['div_med_other']:,.0f} | {r['allocfail_reached']:.3f} / "
            f"{r['allocfail_other']:.3f} | {r['repro_energy_at_death_med']:,.1f} | "
            f"{_fmt(r['pass_cost_med'], 0)} ({r['pass_n']:,}) |")
    lines += [
        "",
        "Reproducers active to death (last divide at most 50 ticks before death), per seed: "
        + "; ".join(f"s{r['seed']} {r['active_to_death']:.2f} of reproducers, {r['atd_births_share']:.2f} of "
                    f"divides, reached cap {r['atd_reached']:.3f} ({r['atd_births_share_reached']:.2f} of all "
                    f"divides), max median {r['atd_max_energy_p50']:,.0f} / p90 {r['atd_max_energy_p90']:,.0f}"
                    for r in ok.iter_rows(named=True)) + ".",
        "",
        "## Snapshots of living replicator-class bodies (census every 500 ticks), by state",
        "",
        "State by ticks since the last divide: active ≤ 50, first = never divided and ≤ 50 ticks old, "
        "host = active or first, stalled = the rest. Energy in units.",
        "",
        "| seed | state | share | unchanged | mean | p10 | median | p90 | ≥ cap/10 | ≥ 0.9 cap | capped absorbs (lifetime) | patch ration |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in ok.iter_rows(named=True):
        for st in STATES:
            lines.append(
                f"| {r['seed']} | {st} | {r[f'{st}_share']:.3f} | {r[f'{st}_unchanged']:.3f} | "
                f"{r[f'{st}_energy_mean']:,.0f} | {_fmt(r[f'{st}_energy_p10'], 0)} | {_fmt(r[f'{st}_energy_p50'], 0)} | "
                f"{_fmt(r[f'{st}_energy_p90'], 0)} | {r[f'{st}_ge_tenth']:.3f} | {r[f'{st}_near']:.3f} | "
                f"{r[f'{st}_capped_share']:.3f} | {_fmt(r[f'{st}_ration'])} |")
    tc = (bins.filter(~pl.col("seed").is_in(list(EXCLUDED))).group_by("bin_end").agg(
        pl.col("max_energy_med").median(), pl.col("max_energy_p90").median(), pl.col("reached").median(),
        pl.col("capped_share").median(), pl.col("births_share_reached").median()).sort("bin_end"))
    lines += [
        "",
        "## Time course (reproducers by death tick; medians across seeds)",
        "",
        "| ticks up to | max energy median | p90 | reached cap | capped absorbs | births by reached |",
        "|---|---|---|---|---|---|",
    ]
    for r in tc.iter_rows(named=True):
        lines.append(f"| {r['bin_end']:,} | {r['max_energy_med']:,.0f} | {r['max_energy_p90']:,.0f} | "
                     f"{r['reached']:.3f} | {r['capped_share']:.3f} | {r['births_share_reached']:.3f} |")
    lines += [
        "",
        "## Ranges across seeds",
        "",
        f"- Reproducers' median `max_energy_m`: {_rng(ok, 'repro_max_energy_p50', 0)} units; p90 "
        f"{_rng(ok, 'repro_max_energy_p90', 0)}; share reaching the cap {_rng(ok, 'repro_reached', 1, True)}.",
        f"- Share of all replicator-class absorbs refused in part by the cap: {_rng(ok, 'all_capped_share', 1, True)}.",
        f"- Share of reproducers' divides made by bodies that reached the cap: {_rng(ok, 'births_share_reached', 1, True)}.",
        f"- Living replicator-class bodies, hosts (active or first pass): {_rng(ok, 'host_share', 1, True)} of them; "
        f"median energy {_rng(ok, 'host_energy_p50', 0)}, mean {_rng(ok, 'host_energy_mean', 0)}, p90 "
        f"{_rng(ok, 'host_energy_p90', 0)}; at ≥ 0.9 cap {_rng(ok, 'host_near', 1, True)}; ≥ cap/10 "
        f"{_rng(ok, 'host_ge_tenth', 1, True)}.",
        f"- Active hosts only: median energy {_rng(ok, 'active_energy_p50', 0)}; at ≥ 0.9 cap "
        f"{_rng(ok, 'active_near', 1, True)}; unchanged active hosts median {_rng(ok, 'active_unch_energy_p50', 0)}, "
        f"at ≥ 0.9 cap {_rng(ok, 'active_unch_near', 1, True)}.",
        f"- Stalled: {_rng(ok, 'stalled_share', 1, True)} of living replicator-class bodies; unchanged "
        f"{_rng(ok, 'stalled_unchanged', 2, True)}; median energy {_rng(ok, 'stalled_energy_p50', 0)}; at ≥ 0.9 cap "
        f"{_rng(ok, 'stalled_near', 1, True)}.",
        f"- Mean energy of all living bodies, any class: {_rng(ok, 'snap_all_energy_mean', 0)}; patch ration mean "
        f"{_rng(ok, 'ration_patches')}.",
        f"- Cost per pass (median): {_rng(ok, 'pass_cost_med', 0)} units, so the cap is "
        f"{ok['cap_units_med'][0] / ok['pass_cost_med'].max():.2f}–{ok['cap_units_med'][0] / ok['pass_cost_med'].min():.2f} passes.",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summarize-only", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not a.summarize_only:
        rows, bins = [], []
        for s in SEEDS:
            if s in EXCLUDED:
                continue
            r, b = analyse(s)
            rows.append(r)
            bins += b
            print(f"s{s}: {r['reproducers']:,} reproducers, reached cap {r['repro_reached']:.3f}", flush=True)
        pl.DataFrame(rows, infer_schema_length=None).write_csv(OUT / "seeds.csv")
        pl.DataFrame(bins, infer_schema_length=None).write_csv(OUT / "bins.csv")
    text = summarize()
    (OUT / "summary.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
