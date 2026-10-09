"""E009b: the self-scan injected into a parasitised world. Each run is the
standard one-founder world for 50,000 ticks; at the start of tick 25,000,
50 copies of a test genome are placed into memory not owned by a living
organism (`--inject 25000:HEX:50`), and the test genome's share of
replicator-class exact births is followed to tick 50,000.

Arms: 4 rules x 3 test genomes, seeds 1-3 (36 runs).

- rules: `n0` (E007 physics, no flag), `n25` (`--charge-owner-pct 25`),
  `n50` (`--charge-owner-pct 50`), `e008` (`--charge-owner`).
- genomes: `prefix` = `self 1 ; swap C ; self 0 ; sub C ; jmpr A`
  (33 52 13 4f 0c) + the K = 120 ancestor; `inert` = five `zero D` (70 x 5)
  + the K = 120 ancestor (both 26 bytes); `resident` = the K = 120 ancestor
  itself (21 bytes).

Usage (from analysis/):

    uv run e009b_late_injection.py                 # build, run, classify, analyse
    uv run e009b_late_injection.py --analyse-only  # runs exist; redo the tables
    uv run e009b_late_injection.py --seeds 1 --ticks 6000 --inject-tick 3000 --out /tmp/x  # smoke test only

Run directories: runs/e009b/<rule>_<genome>/s<seed>/. Output in runs/e009b/:
bins.csv (per run and 2,500-tick bin), runs.csv (per run), living.csv (living
test bodies per run and census from the injection on), deaths.csv (test
deaths per rule and genome) and summary.md.
Protocol and predictions: docs/research/experiments/2026-10-08-e009b-late-injection.md.

Matching. A genome "is the test genome" when its canonical instruction list
(traits.canonical_instrs: op, canonical modifier, lit operand) equals the
test genome's, compared in full. A genome "carries the test prefix" when its
first five canonical (op, modifier) pairs equal traits.PREFIX (`prefix`) or
traits.INERT (`inert`); for `resident` the prefix measure is the canonical
match itself.

Measures, per 2,500-tick bin (bin k holds ticks ((k-1)*2500, k*2500]; bins
11-20 are after the injection, bin 10 is the pre-injection baseline), over
replicator-class exact births (child == executor's body at `divide`, class
of the child's genome from classes.csv written under the rule's flags):

- `test_share`: share whose genome is the test genome (canonical match).
- `prefix_share`: share carrying the test prefix at byte 0.
- `long_share`: share of bodies of 26 bytes or more.
- `test_alive`, `pop`, `rep_alive`, `foreign_exec_share` at the bin's last
  census (living bodies; test by the canonical match of the current body,
  `now_hash`; foreign = lifetime `exec_foreign` / `executed` over all).
- `rep_deaths`, `rep_deaths_paid`, `rep_deaths_paid_share`: replicator-class
  deaths in the bin (by birth hash), those with `paid_for_others_m` > 0.
- `test_deaths`, `test_entered_share` (`paid_for_others_m` > 0),
  `test_age_med`, `test_children_mean` (exact children: births with the
  organism as executor and child == executor's body): deaths of organisms
  whose birth genome is the test genome.

Whole run: `placed` = copies placed (meta.json starts not -1); `last_share`
= test share in bin 20; `last_above_1pct` = end tick of the last 100-tick
bin of births after the injection in which the test share exceeds 1%
(the injection tick if none; `censored` if it still does in the final
100-tick bin); `last_alive_gt10` = last census tick with more than 10 living
test bodies; `alive_end` = living test bodies at the final census.

Operational readings of the predictions (fixed here, before the runs):

- "lost" = last-bin share below 1%.
- Rates are compared as time since the injection, `last_above_1pct` minus
  the injection tick (absolute ticks from 25,000 on are always within a
  factor of 2 of each other, so the comparison would be empty). Ratio
  max/min; both 0 counts as 1, one 0 as infinite.
1. `resident`: under every rule, >= 2 of 3 seeds with >= 10 living test
   bodies at the final census and last-bin share >= 1% (both in the same seed).
2. `n0`: `prefix` and `inert` each lost in 3 of 3 seeds; and per seed the
   ratio of their times since injection <= 2 in >= 2 of 3 seeds.
3. `n25` and `n50`: `prefix` lost in >= 2 of 3 seeds at each N; and the
   ratio of `prefix`'s and `inert`'s times since injection <= 2 in >= 2 of 3
   seeds at each N.
4. `e008`: `prefix` `last_above_1pct` <= `inert`'s in >= 2 of 3 seeds.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

import traits
from evo_run import ROOT, binary, load

OUT = ROOT / "runs" / "e009b"
TICKS = 50_000
INJECT = 25_000
COPIES = 50
CENSUS = 500
BIN = 2_500
FINE = 100  # resolution of `last_above_1pct` (births carry exact ticks)
HARNESS_TICKS = 3_000
LONG = 26
ALIVE_MIN = 10

ANC120 = "13325271fc11781605086c5a1845486c11101c130d"  # sim::ancestor(120, 16), checked by --disasm
GENOMES = {
    "prefix": "3352134f0c" + ANC120,  # self 1 ; swap C ; self 0 ; sub C ; jmpr A
    "inert": "70" * 5 + ANC120,       # zero D x 5
    "resident": ANC120,
}
SEQ = {"prefix": traits.PREFIX, "inert": traits.INERT, "resident": None}
RULES: dict[str, list[str]] = {
    "n0": [],
    "n25": ["--charge-owner-pct", "25"],
    "n50": ["--charge-owner-pct", "50"],
    "e008": ["--charge-owner"],
}
GONE = 0.01  # "lost" and "last > 1%"
RATE_FACTOR = 2.0


def run_dir(rule: str, genome: str, seed: int) -> Path:
    return OUT / f"{rule}_{genome}" / f"s{seed}"


def run_one(exe: Path, rule: str, genome: str, seed: int, ticks: int, inject: int, force: bool) -> str:
    d = run_dir(rule, genome, seed)
    tag = f"{rule}_{genome}/s{seed}"
    if not force and (d / "classes.csv").exists():
        return f"{tag}: done"
    t0 = time.time()
    if force or not (d / "genomes.csv").exists():
        if d.exists():
            shutil.rmtree(d)
        d.parent.mkdir(parents=True, exist_ok=True)
        cmd = [str(exe), "--ticks", str(ticks), "--seed", str(seed), "--report", str(CENSUS),
               "--census", str(CENSUS), "--out", str(d),
               "--inject", f"{inject}:{GENOMES[genome]}:{COPIES}", *RULES[rule]]
        with open(d.parent / f"s{seed}.stdout", "w") as out:
            subprocess.run(cmd, stdout=out, stderr=subprocess.DEVNULL, check=True)
    t1 = time.time()
    subprocess.run([str(exe), "--classify", str(d), "--harness-ticks", str(HARNESS_TICKS), *RULES[rule]],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return f"{tag}: run {t1 - t0:.0f} s, classify {time.time() - t1:.0f} s"


def canon(bytes_hex: str) -> tuple:
    return tuple(traits.canonical_instrs(bytes.fromhex(bytes_hex)))


def matchers(genome: str, genomes: pl.DataFrame) -> tuple[set[str], set[str]]:
    """Raw hashes in genomes.csv that are the test genome (canonical match)
    and that carry the test prefix at byte 0."""
    target = canon(GENOMES[genome])
    seq = SEQ[genome]
    is_test, has_prefix = set(), set()
    for h, x in genomes.select("raw_hash", "bytes_hex").iter_rows():
        if x is None:
            continue
        c = canon(x)
        if c == target:
            is_test.add(h)
        if seq is None:
            if c == target:
                has_prefix.add(h)
        elif len(c) >= len(seq) and all(c[k][:2] == seq[k] for k in range(len(seq))):
            has_prefix.add(h)
    return is_test, has_prefix


def analyse_run(rule: str, genome: str, seed: int, ticks: int, inject: int) -> tuple[list[dict], dict, list[dict], pl.DataFrame]:
    d = run_dir(rule, genome, seed)
    run = load(d)
    n_bins = ticks // BIN
    is_test, has_prefix = matchers(genome, run.genomes)
    tl, pl_ = sorted(is_test), sorted(has_prefix)  # plain lists for `is_in`

    ex = traits.exact_births(run, BIN).filter(pl.col("class") == "replicator").with_columns(
        test=pl.col("raw_hash").is_in(tl), pre=pl.col("raw_hash").is_in(pl_),
        fine=((pl.col("tick") + FINE - 1) // FINE).cast(pl.Int64))
    orgs = run.class_of(run.orgs, "now_hash").with_columns(test=pl.col("now_hash").is_in(tl))
    deaths = run.class_of(run.deaths, "birth_hash").with_columns(
        bin=((pl.col("tick") + BIN - 1) // BIN).cast(pl.Int64), test=pl.col("birth_hash").is_in(tl))
    # Exact children per executor (child == executor's body at `divide`).
    kids = (run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash"))
            .group_by("executor").agg(exact_children=pl.len()).rename({"executor": "id"}))
    tdeaths = (deaths.filter(pl.col("test")).join(kids, on="id", how="left")
               .with_columns(pl.col("exact_children").fill_null(0)))

    bins = []
    for k in range(1, n_bins + 1):
        hi = k * BIN
        e = ex.filter(pl.col("bin") == k)
        alive = orgs.filter(pl.col("tick") == hi)
        executed = int(alive["executed"].sum()) if alive.height else 0
        rd = deaths.filter((pl.col("bin") == k) & (pl.col("class") == "replicator"))
        paid = int((rd["paid_for_others_m"] > 0).sum()) if rd.height else 0
        td = tdeaths.filter(pl.col("bin") == k)
        bins.append(dict(
            rule=rule, genome=genome, seed=seed, bin=k, tick_end=hi,
            rep_n=e.height,
            test_share=float(e["test"].mean()) if e.height else None,
            prefix_share=float(e["pre"].mean()) if e.height else None,
            long_share=float((e["len"] >= LONG).mean()) if e.height else None,
            test_alive=int(alive["test"].sum()) if alive.height else 0,
            pop=alive.height,
            rep_alive=int((alive["class"] == "replicator").sum()) if alive.height else 0,
            foreign_exec_share=int(alive["exec_foreign"].sum()) / executed if executed else None,
            rep_deaths=rd.height,
            rep_deaths_paid=paid,
            rep_deaths_paid_share=paid / rd.height if rd.height else None,
            test_deaths=td.height,
            test_entered_share=float((td["paid_for_others_m"] > 0).mean()) if td.height else None,
            test_age_med=td["age"].median() if td.height else None,
            test_children_mean=td["exact_children"].mean() if td.height else None,
        ))

    # Fine bins after the injection: births in ticks (inject, ticks].
    fine = (ex.filter(pl.col("tick") > inject).group_by("fine").agg(share=pl.col("test").mean())
            .with_columns(tick_end=pl.col("fine") * FINE).sort("fine"))
    above = fine.filter(pl.col("share") > GONE)
    last_fine = int(fine["tick_end"].max()) if fine.height else inject
    last_tick = int(above["tick_end"].max()) if above.height else inject
    censored = above.height > 0 and last_tick >= last_fine

    living = (orgs.filter(pl.col("tick") >= inject).group_by("tick").agg(test_alive=pl.col("test").sum())
              .sort("tick").with_columns(rule=pl.lit(rule), genome=pl.lit(genome), seed=pl.lit(seed)))
    # Censuses where no test body is alive have no rows with test = true but
    # still appear (every census has living bodies unless extinct).
    gt = living.filter(pl.col("test_alive") > ALIVE_MIN)
    final = int(run.orgs["tick"].max())
    inj = (run.meta.get("injections") or [{}])[0]
    starts = inj.get("starts", [])
    post = [b for b in bins if b["tick_end"] > inject]
    shares = [b["test_share"] for b in post if b["test_share"] is not None]
    summary = dict(
        rule=rule, genome=genome, seed=seed,
        placed=sum(1 for s in starts if s >= 0), copies=len(starts),
        last_share=bins[-1]["test_share"] if bins else None,
        last_prefix_share=bins[-1]["prefix_share"] if bins else None,
        pre_share=bins[inject // BIN - 1]["test_share"] if inject // BIN >= 1 else None,
        last_above_1pct=ticks if censored else last_tick,
        since_inject=(ticks if censored else last_tick) - inject,
        censored=censored,
        mean_share=sum(shares) / len(shares) if shares else None,
        last_alive_gt10=int(gt["tick"].max()) if gt.height else None,
        alive_end=int(living.filter(pl.col("tick") == final)["test_alive"].sum()) if living.height else 0,
        final_tick=final,
        final_pop=run.orgs.filter(pl.col("tick") == final).height,
        test_deaths=tdeaths.height,
        test_entered=int((tdeaths["paid_for_others_m"] > 0).sum()) if tdeaths.height else 0,
    )
    for k in (11, 12, 14, 17, 20):
        summary[f"share_b{k}"] = bins[k - 1]["test_share"] if k <= len(bins) else None
    return bins, summary, living.to_dicts(), tdeaths.select(
        pl.lit(rule).alias("rule"), pl.lit(genome).alias("genome"), pl.lit(seed).alias("seed"),
        "tick", "id", "age", "paid_for_others_m", "exact_children", "offspring")


pct = lambda v: "–" if v is None else f"{100 * v:.2f}%"
f0 = lambda v: "–" if v is None else f"{v:,.0f}"
f1 = lambda v: "–" if v is None else f"{v:,.1f}"
yn = lambda ok: "holds" if ok else "fails"


def ratio(a: int | None, b: int | None) -> float | None:
    if a is None or b is None:
        return None
    if a == 0 and b == 0:
        return 1.0
    if min(a, b) == 0:
        return float("inf")
    return max(a, b) / min(a, b)


rs = lambda r: "–" if r is None else ("inf" if r == float("inf") else f"{r:.2f}")


def predictions(runs: pl.DataFrame, seeds: list[int], inject: int) -> list[str]:
    def get(rule, genome, seed, col):
        x = runs.filter((pl.col("rule") == rule) & (pl.col("genome") == genome) & (pl.col("seed") == seed))
        return x[col][0] if x.height else None

    def tick_s(rule, genome, seed):
        t = get(rule, genome, seed, "last_above_1pct")
        return "–" if t is None else (f">= {t:,} (not lost)" if get(rule, genome, seed, "censored") else f"{t:,}")

    lost = lambda rule, g, s: (v := get(rule, g, s, "last_share")) is not None and v < GONE
    need = (len(seeds) * 2 + 2) // 3  # 2 of 3
    lines = ["## Prediction checks", "",
             f"Lost = last-bin share < {pct(GONE)}; 'last > 1%' = end tick of the last {FINE}-tick bin after the "
             f"injection with the test share above {pct(GONE)}; rates compared as ticks since the injection "
             f"({inject:,}).", ""]

    # 1. resident survives under every rule.
    ok1 = True
    for rule in RULES:
        good = 0
        cells = []
        for s in seeds:
            a, sh = get(rule, "resident", s, "alive_end"), get(rule, "resident", s, "last_share")
            g = a is not None and a >= ALIVE_MIN and sh is not None and sh >= GONE
            good += g
            cells.append(f"s{s} {f0(a)} alive, {pct(sh)}")
        ok = good >= need
        ok1 &= ok
        lines.append(f"1 ({rule}). Resident living at end >= {ALIVE_MIN} and last-bin share >= {pct(GONE)}: "
                     f"{'; '.join(cells)}; {good} of {len(seeds)} [>= {need}]. {yn(ok)}.")
    lines.append(f"1. Every rule: {yn(ok1)}.")

    # 2. n0: both 26-byte genomes lost in 3 of 3; rates within 2 in >= 2 of 3.
    nl = {g: sum(lost("n0", g, s) for s in seeds) for g in ("prefix", "inert")}
    rr = [ratio(get("n0", "prefix", s, "since_inject"), get("n0", "inert", s, "since_inject")) for s in seeds]
    within = sum(1 for r in rr if r is not None and r <= RATE_FACTOR)
    ok2 = nl["prefix"] == len(seeds) and nl["inert"] == len(seeds) and within >= need
    lines.append(
        f"2 (n0). Last-bin share < {pct(GONE)}: prefix in {nl['prefix']} of {len(seeds)} "
        f"({', '.join(pct(get('n0', 'prefix', s, 'last_share')) for s in seeds)}), inert in {nl['inert']} of "
        f"{len(seeds)} ({', '.join(pct(get('n0', 'inert', s, 'last_share')) for s in seeds)}) [3 of 3 each]. "
        f"Last > 1% prefix / inert: {'; '.join(f's{s} {tick_s('n0', 'prefix', s)} / {tick_s('n0', 'inert', s)}' for s in seeds)}; "
        f"max/min of ticks since injection {', '.join(rs(r) for r in rr)} [<= {RATE_FACTOR:g} in >= {need}: {within}]. "
        f"{yn(ok2)}.")

    # 3. n25, n50: prefix lost in >= 2 of 3; within a factor 2 of inert in >= 2 of 3.
    ok3_all = True
    for rule in ("n25", "n50"):
        n_lost = sum(lost(rule, "prefix", s) for s in seeds)
        rr = [ratio(get(rule, "prefix", s, "since_inject"), get(rule, "inert", s, "since_inject")) for s in seeds]
        within = sum(1 for r in rr if r is not None and r <= RATE_FACTOR)
        ok = n_lost >= need and within >= need
        ok3_all &= ok
        lines.append(
            f"3 ({rule}). Prefix last-bin share < {pct(GONE)} in {n_lost} of {len(seeds)} "
            f"({', '.join(pct(get(rule, 'prefix', s, 'last_share')) for s in seeds)}) [>= {need}]; inert "
            f"{', '.join(pct(get(rule, 'inert', s, 'last_share')) for s in seeds)}. Last > 1% prefix / inert: "
            f"{'; '.join(f's{s} {tick_s(rule, 'prefix', s)} / {tick_s(rule, 'inert', s)}' for s in seeds)}; "
            f"max/min of ticks since injection {', '.join(rs(r) for r in rr)} [<= {RATE_FACTOR:g} in >= {need}: "
            f"{within}]. {yn(ok)}.")
    lines.append(f"3. Both N: {yn(ok3_all)}.")

    # 4. e008: prefix not later than inert in >= 2 of 3.
    nl4 = 0
    cells = []
    for s in seeds:
        a, b = get("e008", "prefix", s, "last_above_1pct"), get("e008", "inert", s, "last_above_1pct")
        w = a is not None and b is not None and a <= b
        nl4 += w
        cells.append(f"s{s} {tick_s('e008', 'prefix', s)} / {tick_s('e008', 'inert', s)} "
                     f"({'not later' if w else 'later'})")
    lines.append(f"4 (e008). Last > 1% prefix / inert: {'; '.join(cells)}. Prefix not later in {nl4} of "
                 f"{len(seeds)} [>= {need}]. {yn(nl4 >= need)}.")
    return lines


def summarize(bdf: pl.DataFrame, runs: pl.DataFrame, living: pl.DataFrame, tdeaths: pl.DataFrame,
              seeds: list[int], ticks: int, inject: int) -> str:
    n_bins = ticks // BIN
    k0 = inject // BIN  # last pre-injection bin
    order = {g: i for i, g in enumerate(GENOMES)}
    lines = [f"# E009b late injection: {len(RULES)} rules x {len(GENOMES)} genomes x seeds "
             f"{', '.join(map(str, seeds))}, {ticks:,} ticks, {COPIES} copies at {inject:,}, bins of {BIN:,}", ""]
    lines += [
        f"Per run: copies placed, test share of replicator-class exact births in bin {k0} (pre-injection) and bins "
        f"{k0 + 1}–{n_bins}, end tick of the last {FINE}-tick bin above 1%, last census with > {ALIVE_MIN} living "
        "test bodies, living test bodies at the end, final population.", "",
        "| rule | genome | seed | placed | " + " | ".join(f"b{k}" for k in range(k0, n_bins + 1))
        + " | last > 1% | alive > 10 last | alive end | final pop |",
        "|---|---|---|---|" + "---|" * (n_bins - k0 + 1) + "---|---|---|---|",
    ]
    srt = runs.with_columns(o=pl.col("genome").replace_strict(order)).sort(["rule", "o", "seed"])
    for r in srt.iter_rows(named=True):
        x = bdf.filter((pl.col("rule") == r["rule"]) & (pl.col("genome") == r["genome"]) & (pl.col("seed") == r["seed"])
                       & (pl.col("bin") >= k0)).sort("bin")
        sh = " | ".join(pct(v) for v in x["test_share"].to_list())
        t = r["last_above_1pct"]
        lines.append(f"| {r['rule']} | {r['genome']} | {r['seed']} | {r['placed']}/{r['copies']} | {sh} "
                     f"| {'>= ' if r['censored'] else ''}{t:,} | {f0(r['last_alive_gt10'])} | {r['alive_end']} "
                     f"| {r['final_pop']} |")
    lines += [
        "", f"Living test bodies (canonical match of the current body) at every {BIN:,} ticks from the injection.", "",
        "| rule | genome | seed | " + " | ".join(f"{t:,}" for t in range(inject, ticks + 1, BIN)) + " |",
        "|---|---|---|" + "---|" * len(range(inject, ticks + 1, BIN)),
    ]
    for r in srt.iter_rows(named=True):
        x = living.filter((pl.col("rule") == r["rule"]) & (pl.col("genome") == r["genome"]) & (pl.col("seed") == r["seed"]))
        m = dict(zip(x["tick"].to_list(), x["test_alive"].to_list()))
        lines.append(f"| {r['rule']} | {r['genome']} | {r['seed']} | "
                     + " | ".join(f0(m.get(t)) for t in range(inject, ticks + 1, BIN)) + " |")
    lines += [
        "", "Per bin, medians across seeds: test share / prefix share / bodies >= 26 bytes / living test / population / "
        "replicator-class alive / foreign exec share / replicator deaths that paid (share).", "",
        "| rule | genome | bin | test | prefix | >= 26 bytes | test alive | pop | rep alive | foreign | paid deaths |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    med = lambda x, c: x[c].drop_nulls().median() if x[c].drop_nulls().len() else None
    for rule in RULES:
        for g in GENOMES:
            for k in range(k0, n_bins + 1):
                x = bdf.filter((pl.col("rule") == rule) & (pl.col("genome") == g) & (pl.col("bin") == k))
                if not x.height:
                    continue
                lines.append(f"| {rule} | {g} | {k} | {pct(med(x, 'test_share'))} | {pct(med(x, 'prefix_share'))} "
                             f"| {pct(med(x, 'long_share'))} | {f0(med(x, 'test_alive'))} | {f0(med(x, 'pop'))} "
                             f"| {f0(med(x, 'rep_alive'))} | {pct(med(x, 'foreign_exec_share'))} "
                             f"| {f0(med(x, 'rep_deaths_paid'))} ({pct(med(x, 'rep_deaths_paid_share'))}) |")
    lines += [
        "", "Deaths of test-genome organisms (birth genome is the test genome), seeds pooled: count, share entered "
        "(`paid_for_others_m` > 0), median age, mean exact children; and the same by seed.", "",
        "| rule | genome | deaths | entered | median age | mean exact children | by seed (deaths, entered, age, children) |",
        "|---|---|---|---|---|---|---|",
    ]
    for rule in RULES:
        for g in GENOMES:
            x = tdeaths.filter((pl.col("rule") == rule) & (pl.col("genome") == g))
            per = []
            for s in seeds:
                y = x.filter(pl.col("seed") == s)
                per.append(f"s{s} {y.height}, {pct(float((y['paid_for_others_m'] > 0).mean()) if y.height else None)}, "
                           f"{f0(y['age'].median() if y.height else None)}, "
                           f"{f1(y['exact_children'].mean() if y.height else None)}")
            lines.append(f"| {rule} | {g} | {x.height} "
                         f"| {pct(float((x['paid_for_others_m'] > 0).mean()) if x.height else None)} "
                         f"| {f0(x['age'].median() if x.height else None)} "
                         f"| {f1(x['exact_children'].mean() if x.height else None)} | {'; '.join(per)} |")
    lines += [""] + predictions(runs, seeds, inject)
    return "\n".join(lines)


def main() -> None:
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--ticks", type=int, default=TICKS, help="override for smoke tests only")
    ap.add_argument("--inject-tick", type=int, default=INJECT, help="override for smoke tests only")
    ap.add_argument("--out", type=Path, default=OUT, help="output root (smoke tests only)")
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    a = ap.parse_args()
    OUT = a.out
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = list(range(1, a.seeds + 1))
    jobs = [(r, g, s) for r in RULES for g in GENOMES for s in seeds]
    exe = binary()
    t_all = time.time()
    if not a.analyse_only:
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda j: run_one(exe, *j, a.ticks, a.inject_tick, a.force), jobs):
                print(msg, flush=True)
        print(f"runs and classes: {time.time() - t_all:.0f} s", flush=True)

    def one(j):
        return analyse_run(*j, a.ticks, a.inject_tick) if (run_dir(*j) / "classes.csv").exists() else None

    with ThreadPoolExecutor(min(a.jobs, 6)) as ex:
        results = [r for r in ex.map(one, jobs) if r is not None]
    bdf = pl.DataFrame([b for bins, _, _, _ in results for b in bins], infer_schema_length=None)
    runs = pl.DataFrame([s for _, s, _, _ in results], infer_schema_length=None)
    living = pl.DataFrame([x for _, _, lv, _ in results for x in lv], infer_schema_length=None)
    tdeaths = pl.concat([td for _, _, _, td in results], how="vertical_relaxed")
    bdf.write_csv(OUT / "bins.csv")
    runs.write_csv(OUT / "runs.csv")
    living.write_csv(OUT / "living.csv")
    tdeaths.write_csv(OUT / "deaths.csv")
    text = summarize(bdf, runs, living, tdeaths, seeds, a.ticks, a.inject_tick)
    (OUT / "summary.md").write_text(text + "\n", encoding="utf-8", newline="")
    print(text)
    print(f"total {time.time() - t_all:.0f} s")


if __name__ == "__main__":
    main()
