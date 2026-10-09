"""E009a: invasion from rare. Is the complete five-byte self-scan worth
carrying? Each run seeds 110 founders in the standard world: 100 copies of
the K = 120 ancestor (E007's evolved host) and 10 copies of a test genome
(`--founder HEX:COUNT`, host first), and follows the test genome's share of
replicator-class exact births for 25,000 ticks.

Arms: 4 rules x 2 test genomes, seeds 1-3 (24 runs).

- rules: `n0` (E007 physics, no flag), `n25` (`--charge-owner-pct 25`),
  `n50` (`--charge-owner-pct 50`), `e008` (`--charge-owner`).
- genomes: `prefix` = `self 1 ; swap C ; self 0 ; sub C ; jmpr A`
  (33 52 13 4f 0c) + the K = 120 ancestor; `inert` = five `zero D` (70 x 5)
  + the K = 120 ancestor. Both 26 bytes.

Usage (from analysis/):

    uv run e009a_invasion.py                 # build, run, classify, analyse
    uv run e009a_invasion.py --analyse-only  # runs exist; redo the tables
    uv run e009a_invasion.py --seeds 1 --ticks 5000 --out /tmp/x  # smoke test only

Run directories: runs/e009a/<rule>_<genome>/s<seed>/. Output in runs/e009a/:
bins.csv (per run and 2,500-tick bin), runs.csv (per run), harness.csv
(the `pad` probe before the inert host under each rule) and summary.md.
Protocol and predictions: docs/research/experiments/2026-10-08-e009a-invasion.md.

Measures, per 2,500-tick bin (bin k holds ticks ((k-1)*2500, k*2500]),
over replicator-class exact births (child == executor's body at `divide`,
class of the child's genome from classes.csv written under the rule's
flags):

- `test_share`: share whose canonical genome carries the arm's test
  sequence at byte 0 in full (traits.track_genome with prefix = PREFIX or
  INERT, column `prefix_5`).
- `long_share`: share of bodies of 26 bytes or more.
- `pop`, `rep_alive`, `foreign_exec_share` at the bin's last census (living
  bodies; lifetime `exec_foreign` / `executed` summed over them).
- `rep_deaths`, `rep_deaths_paid`, `rep_deaths_paid_share`: replicator-class
  deaths in the bin (classed by birth hash), and those with
  `paid_for_others_m` > 0 (zero by construction under `n0`).

Whole run: `last_share` = test share in the last bin (22,500-25,000);
`last_above_1pct` = end tick of the last 100-tick bin of births in
which the test share exceeds 1% (25,000 if it still does at the end, i.e.
not lost; `censored` marks that case).

Operational readings of the predictions (fixed here, before the runs):

1. `n0`: last-bin share < 2% in 3 of 3 seeds for each genome; and per seed
   max/min of the two genomes' `last_above_1pct` <= 2.
2. `n25` and `n50`: `prefix` last-bin share < 2% in >= 2 of 3 seeds at
   each N; and "not clearly slower": per seed `prefix` `last_above_1pct`
   <= 2 x `inert`'s, in >= 2 of 3 seeds at each N.
3. `e008`: `prefix` does worse than `inert` in >= 2 of 3 seeds, "worse" =
   earlier `last_above_1pct`, or the same tick and a lower mean test share
   over the run's bins.
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

OUT = ROOT / "runs" / "e009a"
TICKS = 25_000
CENSUS = 500
BIN = 2_500
FINE = 100  # resolution of `last_above_1pct` (births carry exact ticks)
HARNESS_TICKS = 3_000
HOSTS, TESTS = 100, 10
LONG = 26
PROBE = "00"  # the one-byte `pad`

ANC120 = "13325271fc11781605086c5a1845486c11101c130d"  # sim::ancestor(120, 16), checked by --disasm
GENOMES = {
    "prefix": "3352134f0c" + ANC120,  # self 1 ; swap C ; self 0 ; sub C ; jmpr A
    "inert": "70" * 5 + ANC120,       # zero D x 5
}
SEQ = {"prefix": traits.PREFIX, "inert": traits.INERT}
RULES: dict[str, list[str]] = {
    "n0": [],
    "n25": ["--charge-owner-pct", "25"],
    "n50": ["--charge-owner-pct", "50"],
    "e008": ["--charge-owner"],
}
LOST = 0.02  # predictions 1-2: last-bin share below this
GONE = 0.01  # last tick above this share
RATE_FACTOR = 2.0


def run_dir(rule: str, genome: str, seed: int) -> Path:
    return OUT / f"{rule}_{genome}" / f"s{seed}"


def run_one(exe: Path, rule: str, genome: str, seed: int, ticks: int, force: bool) -> str:
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
               "--founder", f"{ANC120}:{HOSTS}", "--founder", f"{GENOMES[genome]}:{TESTS}", *RULES[rule]]
        with open(d.parent / f"s{seed}.stdout", "w") as out:
            subprocess.run(cmd, stdout=out, stderr=subprocess.DEVNULL, check=True)
    t1 = time.time()
    subprocess.run([str(exe), "--classify", str(d), "--harness-ticks", str(HARNESS_TICKS), *RULES[rule]],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return f"{tag}: run {t1 - t0:.0f} s, classify {time.time() - t1:.0f} s"


def host_harness(exe: Path, rule: str, genome_hex: str, host_hex: str, ticks: int = HARNESS_TICKS) -> dict:
    """Two-genome harness under the rule's physics: `genome_hex` right
    before `host_hex`, quiet, `ticks` ticks (the E009 runner's probe)."""
    cmd = [str(exe), "--host", genome_hex, "--host-body", host_hex, "--harness-ticks", str(ticks), *RULES[rule]]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    header, row = out.strip().splitlines()[:2]
    vals = dict(zip(header.split(","), row.split(",")))
    return {k: (v == "true" if v in ("true", "false") else int(v)) for k, v in vals.items()}


def host_death_tick(exe: Path, rule: str, genome_hex: str, host_hex: str) -> int | None:
    """First harness length at which the host is dead (bisection, as E008/E009)."""
    if host_harness(exe, rule, genome_hex, host_hex)["host_alive"]:
        return None
    lo, hi = 0, HARNESS_TICKS
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if host_harness(exe, rule, genome_hex, host_hex, mid)["host_alive"]:
            lo = mid
        else:
            hi = mid
    return hi


def harness_rows(exe: Path) -> list[dict]:
    rows = []
    for rule in RULES:
        p = host_harness(exe, rule, PROBE, GENOMES["inert"])
        rows.append(dict(
            rule=rule, pad_births=p["births"], pad_exact=p["exact_births"], host_exact=p["host_exact_births"],
            host_alive=p["host_alive"], pad_alive=p["alive"], ticks_run=p["ticks_run"],
            stopped_early=p["stopped_early"],
            host_death_tick=None if p["host_alive"] else host_death_tick(exe, rule, PROBE, GENOMES["inert"]),
        ))
    return rows


def analyse_run(rule: str, genome: str, seed: int, ticks: int) -> tuple[list[dict], dict]:
    d = run_dir(rule, genome, seed)
    run = load(d)
    seq = SEQ[genome]
    full = f"prefix_{len(seq)}"
    n_bins = ticks // BIN

    tg = {r["bin"]: r for r in traits.track_genome(run, BIN, prefix=seq).iter_rows(named=True)}
    fine = traits.track_genome(run, FINE, prefix=seq).sort("bin")
    ex = traits.exact_births(run, BIN).filter(pl.col("class") == "replicator")
    orgs = run.class_of(run.orgs, "now_hash")
    deaths = run.class_of(run.deaths, "birth_hash").with_columns(
        bin=((pl.col("tick") + BIN - 1) // BIN).cast(pl.Int64))

    bins = []
    for k in range(1, n_bins + 1):
        hi = k * BIN
        g = tg.get(k, {})
        e = ex.filter(pl.col("bin") == k)
        alive = orgs.filter(pl.col("tick") == hi)
        executed = int(alive["executed"].sum()) if alive.height else 0
        rd = deaths.filter((pl.col("bin") == k) & (pl.col("class") == "replicator"))
        paid = int((rd["paid_for_others_m"] > 0).sum()) if rd.height else 0
        bins.append(dict(
            rule=rule, genome=genome, seed=seed, bin=k, tick_end=hi,
            rep_n=g.get("rep_n", 0),
            test_share=g.get(full),
            long_share=float((e["len"] >= LONG).mean()) if e.height else None,
            pop=alive.height,
            rep_alive=int((alive["class"] == "replicator").sum()) if alive.height else 0,
            foreign_exec_share=int(alive["exec_foreign"].sum()) / executed if executed else None,
            rep_deaths=rd.height,
            rep_deaths_paid=paid,
            rep_deaths_paid_share=paid / rd.height if rd.height else None,
        ))

    above = fine.filter(pl.col(full) > GONE)
    last_tick = int(above["tick_end"].max()) if above.height else 0
    last_fine = int(fine["tick_end"].max()) if fine.height else 0
    censored = above.height > 0 and last_tick >= last_fine
    shares = [b["test_share"] for b in bins if b["test_share"] is not None]
    final = int(run.orgs["tick"].max())
    summary = dict(
        rule=rule, genome=genome, seed=seed,
        last_share=bins[-1]["test_share"] if bins else None,
        last_above_1pct=min(last_tick, ticks) if not censored else ticks,
        censored=censored,
        mean_share=sum(shares) / len(shares) if shares else None,
        final_tick=final,
        final_pop=run.orgs.filter(pl.col("tick") == final).height,
        replicating_end=bins[-1]["rep_n"] > 0 if bins else False,
    )
    for k in (1, 4, 7, 10):
        summary[f"share_b{k}"] = bins[k - 1]["test_share"] if k <= len(bins) else None
    return bins, summary


pct = lambda v: "–" if v is None else f"{100 * v:.2f}%"
f0 = lambda v: "–" if v is None else f"{v:,.0f}"
yn = lambda ok: "holds" if ok else "fails"


def predictions(runs: pl.DataFrame, seeds: list[int]) -> list[str]:
    def get(rule, genome, seed, col):
        x = runs.filter((pl.col("rule") == rule) & (pl.col("genome") == genome) & (pl.col("seed") == seed))
        return x[col][0] if x.height else None

    def tick_s(rule, genome, seed):
        t = get(rule, genome, seed, "last_above_1pct")
        return "–" if t is None else (f">= {t:,} (not lost)" if get(rule, genome, seed, "censored") else f"{t:,}")

    lines = ["## Prediction checks", "",
             f"Lost = last-bin share < {pct(LOST)}; 'last > 1%' = end tick of the last {FINE}-tick bin with the test "
             f"share above {pct(GONE)}.", ""]

    # 1. n0: both lost in 3 of 3; rates within a factor of 2 per seed.
    lost = {g: sum(1 for s in seeds if (v := get("n0", g, s, "last_share")) is not None and v < LOST) for g in GENOMES}
    ratios, rate_ok = [], True
    for s in seeds:
        a, b = get("n0", "prefix", s, "last_above_1pct"), get("n0", "inert", s, "last_above_1pct")
        r = max(a, b) / min(a, b) if (a and b) else None
        ratios.append(r)
        rate_ok &= r is not None and r <= RATE_FACTOR
    ok1 = lost["prefix"] == len(seeds) and lost["inert"] == len(seeds) and rate_ok
    lines.append(
        f"1 (n0). Last-bin share < {pct(LOST)}: prefix in {lost['prefix']} of {len(seeds)} seeds "
        f"({', '.join(pct(get('n0', 'prefix', s, 'last_share')) for s in seeds)}), inert in {lost['inert']} of "
        f"{len(seeds)} ({', '.join(pct(get('n0', 'inert', s, 'last_share')) for s in seeds)}) [3 of 3 each]. "
        f"Last > 1% prefix / inert per seed: "
        f"{'; '.join(f's{s} {tick_s('n0', 'prefix', s)} / {tick_s('n0', 'inert', s)}' for s in seeds)}; "
        f"max/min {', '.join('–' if r is None else f'{r:.2f}' for r in ratios)} [<= {RATE_FACTOR:g} each]. "
        f"{yn(ok1)}."
    )

    # 2. n25, n50: prefix lost in >= 2 of 3; not clearly slower than inert.
    ok2_all = True
    for rule in ("n25", "n50"):
        n_lost = sum(1 for s in seeds if (v := get(rule, "prefix", s, "last_share")) is not None and v < LOST)
        not_slower = 0
        rs = []
        for s in seeds:
            a, b = get(rule, "prefix", s, "last_above_1pct"), get(rule, "inert", s, "last_above_1pct")
            rs.append(a / b if (a is not None and b) else None)
            if a is not None and b and a <= RATE_FACTOR * b:
                not_slower += 1
        need = (len(seeds) * 2 + 2) // 3  # 2 of 3
        ok = n_lost >= need and not_slower >= need
        ok2_all &= ok
        lines.append(
            f"2 ({rule}). Prefix last-bin share < {pct(LOST)} in {n_lost} of {len(seeds)} seeds "
            f"({', '.join(pct(get(rule, 'prefix', s, 'last_share')) for s in seeds)}) [>= {need}]; inert "
            f"{', '.join(pct(get(rule, 'inert', s, 'last_share')) for s in seeds)}. Last > 1% prefix / inert: "
            f"{'; '.join(f's{s} {tick_s(rule, 'prefix', s)} / {tick_s(rule, 'inert', s)}' for s in seeds)}; "
            f"prefix/inert {', '.join('–' if r is None else f'{r:.2f}' for r in rs)} "
            f"[<= {RATE_FACTOR:g} in >= {need}: {not_slower}]. {yn(ok)}."
        )
    lines.append(f"2. Both N: {yn(ok2_all)}.")

    # 3. e008: prefix worse than inert in >= 2 of 3 seeds.
    worse = 0
    cells = []
    for s in seeds:
        a, b = get("e008", "prefix", s, "last_above_1pct"), get("e008", "inert", s, "last_above_1pct")
        ma, mb = get("e008", "prefix", s, "mean_share"), get("e008", "inert", s, "mean_share")
        w = a is not None and b is not None and (a < b or (a == b and ma is not None and mb is not None and ma < mb))
        worse += w
        cells.append(f"s{s} {tick_s('e008', 'prefix', s)} / {tick_s('e008', 'inert', s)}, mean share "
                     f"{pct(ma)} / {pct(mb)} ({'worse' if w else 'not worse'})")
    need = (len(seeds) * 2 + 2) // 3
    lines.append(
        f"3 (e008). Prefix / inert, last > 1% and mean share over bins: {'; '.join(cells)}. Prefix worse in "
        f"{worse} of {len(seeds)} [>= {need}]. {yn(worse >= need)}."
    )
    return lines


def summarize(bdf: pl.DataFrame, runs: pl.DataFrame, harness: pl.DataFrame | None, seeds: list[int],
              ticks: int) -> str:
    n_bins = ticks // BIN
    lines = [f"# E009a invasion: {len(RULES)} rules x {len(GENOMES)} genomes x seeds "
             f"{', '.join(map(str, seeds))}, {ticks:,} ticks, bins of {BIN:,}", ""]
    if harness is not None and harness.height:
        lines += [
            f"Harness: `pad` before the inert K = 120 host, {HARNESS_TICKS:,} ticks, quiet, 100 units each.", "",
            "| rule | pad births / exact | host exact | host alive at end | host death tick | ticks run | stopped early |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in harness.iter_rows(named=True):
            lines.append(f"| {r['rule']} | {r['pad_births']} / {r['pad_exact']} | {r['host_exact']} "
                         f"| {'yes' if r['host_alive'] else 'no'} | {f0(r['host_death_tick'])} | {r['ticks_run']} "
                         f"| {'yes' if r['stopped_early'] else 'no'} |")
        lines.append("")
    lines += [
        "Per run: test share of replicator-class exact births per bin (bins 1–10), last bin, end tick of the last "
        f"{FINE}-tick bin above 1%, final population.", "",
        "| rule | genome | seed | " + " | ".join(f"b{k}" for k in range(1, n_bins + 1))
        + " | last bin | last > 1% | final pop |",
        "|---|---|---|" + "---|" * n_bins + "---|---|---|",
    ]
    for r in runs.sort(["rule", "genome", "seed"], descending=[False, True, False]).iter_rows(named=True):
        x = bdf.filter((pl.col("rule") == r["rule"]) & (pl.col("genome") == r["genome"]) & (pl.col("seed") == r["seed"])).sort("bin")
        sh = " | ".join(pct(v) for v in x["test_share"].to_list())
        t = r["last_above_1pct"]
        lines.append(f"| {r['rule']} | {r['genome']} | {r['seed']} | {sh} | {pct(r['last_share'])} "
                     f"| {'>= ' if r['censored'] else ''}{t:,} | {r['final_pop']} |")
    lines += [
        "", "Per bin, medians across seeds: test share / bodies >= 26 bytes share / population / replicator-class "
        "alive / foreign exec share / replicator deaths that paid (share).", "",
        "| rule | genome | bin | test | >= 26 bytes | pop | rep alive | foreign | paid deaths |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    med = lambda x, c: x[c].drop_nulls().median() if x[c].drop_nulls().len() else None
    for rule in RULES:
        for g in GENOMES:
            for k in range(1, n_bins + 1):
                x = bdf.filter((pl.col("rule") == rule) & (pl.col("genome") == g) & (pl.col("bin") == k))
                if not x.height:
                    continue
                lines.append(f"| {rule} | {g} | {k} | {pct(med(x, 'test_share'))} | {pct(med(x, 'long_share'))} "
                             f"| {f0(med(x, 'pop'))} | {f0(med(x, 'rep_alive'))} | {pct(med(x, 'foreign_exec_share'))} "
                             f"| {f0(med(x, 'rep_deaths_paid'))} ({pct(med(x, 'rep_deaths_paid_share'))}) |")
    lines += [""] + predictions(runs, seeds)
    return "\n".join(lines)


def main() -> None:
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--ticks", type=int, default=TICKS, help="override for smoke tests only")
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
            for msg in ex.map(lambda j: run_one(exe, *j, a.ticks, a.force), jobs):
                print(msg, flush=True)
        print(f"runs and classes: {time.time() - t_all:.0f} s", flush=True)

    harness = pl.DataFrame(harness_rows(exe))
    harness.write_csv(OUT / "harness.csv")

    def one(j):
        return analyse_run(*j, a.ticks) if (run_dir(*j) / "classes.csv").exists() else None

    with ThreadPoolExecutor(min(a.jobs, 6)) as ex:
        results = [r for r in ex.map(one, jobs) if r is not None]
    bdf = pl.DataFrame([b for bins, _ in results for b in bins], infer_schema_length=None)
    runs = pl.DataFrame([s for _, s in results], infer_schema_length=None)
    bdf.write_csv(OUT / "bins.csv")
    runs.write_csv(OUT / "runs.csv")
    text = summarize(bdf, runs, harness, seeds, a.ticks)
    (OUT / "summary.md").write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"total {time.time() - t_all:.0f} s")


if __name__ == "__main__":
    main()
