"""E014: cycle theft. A cost in time for being entered (H16): under
`--cycle-theft-pct N` an instruction run by organism X on a byte owned by
living organism Y debits Y's per-tick execution budget by
floor(cost * N / 100), carried as a debt; energy is untouched. The question
is whether the six-byte eject injected into the parasitised world is then
maintained where its inert length control is lost, and lost under a
random cycle tax that costs the population the same time without being
tied to entry (the matched control). Spec: docs/tasks/T02-cycle-theft.md,
section 4.

This is analysis/e009b_late_injection.py with the E014 rules and genomes:
the same world (one founder, 50 copies of a test genome placed into memory
not owned by a living organism at the start of tick 25,000 with
`--inject 25000:HEX:50`), the same bins, matching rules and column names,
so the two records read side by side. What is added is said below.

Stages (subcommands):

- `pilot`: 3 seeds, 50,000 ticks, every arm. Not evidence: it checks the
  engine and the population under each N, and calibrates the tax. The four
  theft rules run first; the tax is then calibrated from the `t50_resident`
  runs (written to calib.json) and the `tax` arms run with it.
  Directories runs/e014_pilot/<rule>_<genome>/s<seed>/.
- `main`: 30 seeds, 250,000 ticks, every arm, the tax from the pilot's
  calib.json (or --tax-pct and --tax-frac). Directories
  runs/e014/<rule>_<genome>/s<seed>/.

Both use injection tick 25,000, 50 copies, `--census 500` (and `--report
500`), and classify every genome with the rule's flags (as E009b; a lone
genome executes no foreign code, so the theft rules classify as N = 0,
while the tax does act on a lone genome: the tax arm's classes are those
of the taxed world).

Disk. A 250,000-tick run is about 0.5 GB of CSV (E007), so after each run
is classified its births.csv, deaths.csv, orgs.csv and census.csv are
gzipped in place (level 6; each is read back and compared by SHA-256
before the plain file is deleted). genomes.csv, patches.csv and world.bin
stay as they are (`--classify` reads genomes.csv). evo_run.load reads
NAME.csv.gz transparently. A run found finished with plain files left
(an interrupted compression) is compressed on the next call.
`--no-compress` keeps everything plain.

Usage (from analysis/):

    uv run e014_cycle_theft.py pilot --jobs 12             # build, run, calibrate, run tax, analyse
    uv run e014_cycle_theft.py pilot --analyse-only        # runs exist; redo calibration and tables
    uv run e014_cycle_theft.py main --jobs 12              # the main stage, tax from the pilot
    uv run e014_cycle_theft.py main --dry-run              # print the command lines, run nothing
    uv run e014_cycle_theft.py main --no-compress          # keep the run CSVs plain
    uv run e014_cycle_theft.py pilot --rules n0 --genomes eject --seeds 1 --ticks 2000 \
        --inject-tick 1000 --bin 500 --out ../runs/e014-smoke  # smoke test only

Arms (rule x genome):

- rules: `n0` (no flag), `t25`, `t50`, `t75` (`--cycle-theft-pct N`), `tax`
  (`--cycle-tax-pct P --cycle-tax-frac F`, calibrated below).
- genomes: `eject` = `self 1 ; swap C ; self 0 ; sub C ; skipz A ; jmpa D`
  (33 52 13 4f 08 6d) + the K = 120 ancestor, 27 bytes (traits.EJECT);
  `inert` = six `zero D` (70 x 6) + the K = 120 ancestor, 27 bytes
  (traits.INERT6); `resident` = the K = 120 ancestor alone, 21 bytes.

Tax calibration (T02 §4.2), from the pilot's `t50_resident` runs, seeds
pooled, over replicator-class deaths (class of the birth hash) after the
injection tick: `F` = share with `exec_by_others` > 0 (entered); `r` =
sum `cycles_lost_m` / sum `age` over all of those deaths (mean debit per
organism-tick, entered or not); `P` = 100 r / (F cap), cap = 32,000
milli-units, rounded to the nearest whole percent (halves up), clamped to
0-100. The control debits each organism with probability F per tick by
cap P / 100. F is passed to the binary as Python's repr of the measured
share (exact), P as the rounded integer.

Matching, as E009b: a genome is the test genome when its canonical
instruction list equals the test genome's in full; it carries the test
prefix when its first six canonical (op, modifier) pairs equal traits.EJECT
(`eject`) or traits.INERT6 (`inert`); for `resident` the prefix measure is
the canonical match itself.

Measures. E009b's per 2,500-tick bin, verbatim (bin k holds ticks
((k-1)*2500, k*2500]; bin 10 is the last before the injection):
`rep_n`, `test_share`, `prefix_share`, `long_share` (bodies of 26 bytes or
more), `test_alive`, `pop`, `rep_alive`, `foreign_exec_share`,
`rep_deaths`, `rep_deaths_paid`, `rep_deaths_paid_share`, `test_deaths`,
`test_entered_share`, `test_age_med`, `test_children_mean`. The `paid`
columns are E009b's (`paid_for_others_m` > 0); energy is untouched under
these rules, so they are 0 here and stay only so the files line up. Added
per bin, over replicator-class deaths in the bin, with "entered" =
`exec_by_others` > 0:

- `entered_share`: share entered.
- `cycles_lost_per_tick`: mean of `cycles_lost_m / age` (milli-units per
  tick; the cap is 32,000) over entered deaths with age > 0.
- `entered_rate_ratio`: exact children (births with the organism as
  executor and child == executor's body at `divide`) per tick of life of
  entered deaths over that of unentered (sum of children over sum of age
  in each group).
- `entered_rate_norm`: `entered_rate_ratio` over the same bin's
  `entered_rate_ratio` in the n0 run with the same injected genome and
  seed (1 for n0 itself; empty without that n0 run). This is the
  governing measure (decided 2026-10-13, replacing T02's
  `entered_children_ratio`): entry is more likely the longer an organism
  lives, so the raw children ratio is well above 1 with no cost at all
  (the n0 smoke run, 2,000 ticks: 3.78, age ratio 3.18, rate ratio 1.19).
  The rate takes the lifespan out; dividing by n0 takes out what entry
  selects for without a cost. The pilot branch reads its mean over seeds
  of `entered_rate_norm_post` (below), and prediction 2 its per-seed
  values.
- `entered_children_ratio`, `entered_age_ratio` (diagnostics, reported,
  not tested): mean exact children, and mean age, of entered deaths over
  those of unentered deaths.
- `test_alive_entered_share`: at the bin's last census, share of living
  test bodies with `exec_by_others` > 0 (lifetime so far).

Per run (runs.csv), E009b's (`placed`, `last_share`, `last_prefix_share`,
`pre_share`, `last_above_1pct`, `since_inject`, `censored`, `mean_share`,
`last_alive_gt10`, `alive_end`, `final_tick`, `final_pop`, `test_deaths`,
`test_entered`, `share_b<k>`), plus, over the ticks after the injection:
`pop_mean_post` (mean living bodies over the censuses), `rep_entered_post`,
`entered_rate_ratio_post`, `entered_rate_norm_post` (over the n0 run's
`entered_rate_ratio_post`, same genome and seed),
`entered_children_ratio_post`, `entered_age_ratio_post`,
`cycles_lost_per_tick_post` (the per-bin measures pooled over all
replicator-class deaths after the injection), `lost_per_age_post` and
`taxed_per_age_post` (sum `cycles_lost_m` and sum `cycles_taxed_m` over
sum `age`, the same deaths: the r of the calibration, so the tax arm can be
checked against t50), and `intruders_post` and `intruder_resident_share_post`
(deaths of any class with `exec_foreign` > 0, and the share of those with
`exec_foreign / executed` > 0.9: the README's resident-fraction check).
living.csv gains `test_entered` and `test_entered_share` per census.

Pilot branch (tasks README, E014 pilot; decided 2026-10-13): the mean over
the pilot seeds of the `t50_resident` runs' `entered_rate_norm_post`. In
[0.3, 0.8]: the expected branch (calibrate, main stage). Above 0.8: entries
are too brief for the cost to bite; read `intruder_resident_share_post`.
The summary prints which.

Predictions (T02 §4.4, H16), read on the main stage; "k of 30" scales to
other seed counts as ceil(k n / 30) for "at least" and floor(k n / 30) for
"at most" (the thresholds used are printed):

1. Persistence: `resident` `alive_end` >= 10 and `last_share` >= 1% in
   >= 27 of 30 seeds, under every rule. If `t75` fails this it is reported
   as the slow-starvation arm and dropped from 2-5.
2. Entered hosts graded, not killed (on the `resident` runs, the world with
   nothing added but more of the ancestor): under `t50`,
   `entered_rate_norm_post` between 0.3 and 0.8 in >= 20 of 30 seeds (the
   pilot's reading is the branch above). T02's n0 clause ("above 0.8") is 1
   by construction in this currency; n0's raw `entered_rate_ratio_post`
   and the two diagnostics are printed beside it.
3. The eject pays: under `t50`, `eject` `last_share` >= 1% in >= 20 of 30
   seeds; `inert` >= 1% in <= 5 of 30. Also printed for t25 and t75.
4. The control: under `tax`, the `eject` and `inert` counts of seeds with
   `last_share` >= 1% differ by at most 3 (of 30).
5. Dose: the eject's seed count in 3 is non-decreasing in N over `t25`,
   `t50`, `t75` (ties allowed).
Refuted if 3's eject clause fails at every N, or if 4 fails with the eject
maintained under the tax (eject count above inert's by more than 3): an
accounting error to audit before anything else.

Outputs in the stage directory: bins.csv, runs.csv, living.csv,
deaths.csv (test-genome deaths), calib.json (pilot) and summary.md.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

import traits
from evo_run import CORE, ROOT, binary, load

STAGES = {
    "pilot": dict(out=ROOT / "runs" / "e014_pilot", seeds=3, ticks=50_000),
    "main": dict(out=ROOT / "runs" / "e014", seeds=30, ticks=250_000),
}
INJECT = 25_000
COPIES = 50
CENSUS = 500
BIN = 2_500
FINE = 100  # resolution of `last_above_1pct` (births carry exact ticks)
HARNESS_TICKS = 3_000
LONG = 26
ALIVE_MIN = 10
GONE = 0.01  # "lost" and "last > 1%"
CAP_M = 32_000  # Config::default(): cap_c0 = 32 units, cap_c1 = 0
RESIDENT_FRAC = 0.9  # tasks README, pilot branch: exec_foreign / executed
RATIO_LO, RATIO_HI = 0.3, 0.8  # prediction 2 and the pilot branch
# Gzipped in place after each run (evo_run.load reads NAME.csv.gz).
# genomes.csv stays plain: `--classify` reads it.
COMPRESS = ("births.csv", "deaths.csv", "orgs.csv", "census.csv")
CHUNK = 1 << 20

ANC120 = "13325271fc11781605086c5a1845486c11101c130d"  # sim::ancestor(120, 16)
GENOMES = {
    "eject": "3352134f086d" + ANC120,  # self 1 ; swap C ; self 0 ; sub C ; skipz A ; jmpa D
    "inert": "70" * 6 + ANC120,        # zero D x 6
    "resident": ANC120,
}
SEQ = {"eject": traits.EJECT, "inert": traits.INERT6, "resident": None}
THEFT = {"n0": 0, "t25": 25, "t50": 50, "t75": 75}
RULES = [*THEFT, "tax"]

Tax = tuple[int, float]  # (P, F)


def run_dir(out: Path, rule: str, genome: str, seed: int) -> Path:
    return out / f"{rule}_{genome}" / f"s{seed}"


def rule_flags(rule: str, tax: Tax | None) -> list[str]:
    """Physics flags of a rule, for the world run and `--classify`. The tax
    arm without a calibration gets placeholders (dry run only)."""
    if rule == "tax":
        if tax is None:
            return ["--cycle-tax-pct", "<P>", "--cycle-tax-frac", "<F>"]
        p, f = tax
        return ["--cycle-tax-pct", str(p), "--cycle-tax-frac", repr(f)]
    n = THEFT[rule]
    return [] if n == 0 else ["--cycle-theft-pct", str(n)]


def commands(exe: Path, d: Path, genome: str, seed: int, ticks: int, inject: int,
             flags: list[str]) -> tuple[list[str], list[str]]:
    run = [str(exe), "--ticks", str(ticks), "--seed", str(seed), "--report", str(CENSUS),
           "--census", str(CENSUS), "--out", str(d),
           "--inject", f"{inject}:{GENOMES[genome]}:{COPIES}", *flags]
    cls = [str(exe), "--classify", str(d), "--harness-ticks", str(HARNESS_TICKS), *flags]
    return run, cls


def gzip_verified(src: Path) -> tuple[int, int]:
    """Replace `src` by `src`.gz: compress to a temporary file, read it
    back and compare SHA-256 with the original, then rename it into place
    and delete the original. Returns (plain bytes, gzip bytes)."""
    dst = src.with_name(src.name + ".gz")
    tmp = src.with_name(src.name + ".gz.tmp")
    h_in, h_out = hashlib.sha256(), hashlib.sha256()
    with open(src, "rb") as fi, gzip.open(tmp, "wb", compresslevel=6) as fo:
        while chunk := fi.read(CHUNK):
            h_in.update(chunk)
            fo.write(chunk)
    with gzip.open(tmp, "rb") as fi:
        while chunk := fi.read(CHUNK):
            h_out.update(chunk)
    if h_in.digest() != h_out.digest():
        tmp.unlink()
        raise RuntimeError(f"{src}: gzip read-back differs; plain file kept")
    plain = src.stat().st_size
    os.replace(tmp, dst)
    src.unlink()
    return plain, dst.stat().st_size


def compress_run(d: Path) -> tuple[int, int]:
    """Gzip the large CSVs of a finished run that are still plain (so an
    interrupted compression is finished on the next call). A stale .gz
    next to a plain file is replaced. Returns total (plain, gzip) bytes
    of the files compressed now."""
    plain = packed = 0
    for name in COMPRESS:
        src = d / name
        if src.exists():
            a, b = gzip_verified(src)
            plain += a
            packed += b
    return plain, packed


def run_one(exe: Path, out: Path, rule: str, genome: str, seed: int, ticks: int, inject: int,
            tax: Tax | None, force: bool, compress: bool) -> str:
    d = run_dir(out, rule, genome, seed)
    tag = f"{rule}_{genome}/s{seed}"
    if not force and (d / "classes.csv").exists():
        if compress and any((d / n).exists() for n in COMPRESS):
            a, b = compress_run(d)
            return f"{tag}: done; gzipped {a / 1e6:.1f} -> {b / 1e6:.1f} MB"
        return f"{tag}: done"
    run, cls = commands(exe, d, genome, seed, ticks, inject, rule_flags(rule, tax))
    t0 = time.time()
    if force or not (d / "genomes.csv").exists():
        if d.exists():
            shutil.rmtree(d)
        d.parent.mkdir(parents=True, exist_ok=True)
        with open(d.parent / f"s{seed}.stdout", "w") as f:
            subprocess.run(run, stdout=f, stderr=subprocess.DEVNULL, check=True)
    t1 = time.time()
    subprocess.run(cls, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    msg = f"{tag}: run {t1 - t0:.0f} s, classify {time.time() - t1:.0f} s"
    if compress:
        t2 = time.time()
        a, b = compress_run(d)
        msg += f", gzip {a / 1e6:.1f} -> {b / 1e6:.1f} MB in {time.time() - t2:.0f} s"
    return msg


def canon(bytes_hex: str) -> tuple:
    return tuple(traits.canonical_instrs(bytes.fromhex(bytes_hex)))


def matchers(genome: str, genomes: pl.DataFrame) -> tuple[set[str], set[str]]:
    """Raw hashes in genomes.csv that are the test genome (canonical match)
    and that carry the test prefix at byte 0 (E009b's rule)."""
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


def check_rule(run, rule: str, tax: Tax | None) -> None:
    """The run's meta.json must carry the rule's flags (and a binary from
    T02 on, which writes the cycle fields)."""
    c = run.meta.get("config", {})
    got = (c.get("cycle_theft_pct"), c.get("cycle_tax_pct"), c.get("cycle_tax_frac"))
    if None in got:
        raise SystemExit(f"{run.dir}: meta.json has no cycle_* fields (binary before T02?)")
    t, p, f = int(got[0]), int(got[1]), float(got[2])
    if rule == "tax":
        ok = t == 0 and p > 0 and (tax is None or (p, f) == (tax[0], float(tax[1])))
        want = f"theft 0, tax {tax if tax else '(P > 0, F)'}"
    else:
        ok = (t, p, f) == (THEFT[rule], 0, 1.0)
        want = f"theft {THEFT[rule]}, tax 0, frac 1.0"
    if not ok:
        raise SystemExit(f"{run.dir}: meta.json has theft {t}, tax {p}, frac {f}; expected {want}")


def ratio_of(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def rate_ratio(r: dict) -> float | None:
    """Exact children per tick of life, entered deaths over unentered
    (sums over each group): `entered_rate_ratio`."""
    if not r["age_sum_in"] or not r["age_sum_out"]:
        return None
    return ratio_of(r["kids_sum_in"] / r["age_sum_in"], r["kids_sum_out"] / r["age_sum_out"])


def sel_bins(k0: int, n_bins: int) -> list[int]:
    """Bins shown in the wide tables: the last before the injection, the
    first two after, the fifth after, every tenth, and the last."""
    ks = {k0, k0 + 1, k0 + 2, k0 + 5, n_bins} | {k for k in range(k0 + 1, n_bins + 1) if k % 10 == 0}
    return sorted(k for k in ks if 1 <= k <= n_bins)


def death_aggs(prefix: str = "") -> list[pl.Expr]:
    """E014's entered measures over a frame of deaths (`entered`,
    `exact_children`, `age`, `cycles_lost_m`, `cycles_taxed_m`)."""
    e = pl.col("entered")
    return [
        pl.len().alias(f"{prefix}n"),
        e.sum().alias(f"{prefix}entered_n"),
        (pl.col("cycles_lost_m") / pl.col("age")).filter(e & (pl.col("age") > 0)).mean().alias(f"{prefix}lost_tick"),
        pl.col("exact_children").filter(e).mean().alias(f"{prefix}kids_in"),
        pl.col("exact_children").filter(~e).mean().alias(f"{prefix}kids_out"),
        pl.col("age").filter(e).mean().alias(f"{prefix}age_in"),
        pl.col("age").filter(~e).mean().alias(f"{prefix}age_out"),
        pl.col("exact_children").filter(e).sum().alias(f"{prefix}kids_sum_in"),
        pl.col("exact_children").filter(~e).sum().alias(f"{prefix}kids_sum_out"),
        pl.col("age").filter(e).sum().alias(f"{prefix}age_sum_in"),
        pl.col("age").filter(~e).sum().alias(f"{prefix}age_sum_out"),
        pl.col("cycles_lost_m").sum().alias(f"{prefix}lost_sum"),
        pl.col("cycles_taxed_m").sum().alias(f"{prefix}taxed_sum"),
        pl.col("age").sum().alias(f"{prefix}age_sum"),
        (pl.col("paid_for_others_m") > 0).sum().alias(f"{prefix}paid_n"),
    ]


def analyse_run(out: Path, rule: str, genome: str, seed: int, ticks: int, inject: int, bin_size: int,
                tax: Tax | None) -> tuple[list[dict], dict, list[dict], pl.DataFrame]:
    d = run_dir(out, rule, genome, seed)
    run = load(d)
    check_rule(run, rule, tax)
    n_bins = ticks // bin_size
    is_test, has_prefix = matchers(genome, run.genomes)
    tl, pl_ = sorted(is_test), sorted(has_prefix)  # plain lists for `is_in`
    binx = lambda c: ((pl.col(c) + bin_size - 1) // bin_size).cast(pl.Int64)

    ex = traits.exact_births(run, bin_size).filter(pl.col("class") == "replicator").with_columns(
        test=pl.col("raw_hash").is_in(tl), pre=pl.col("raw_hash").is_in(pl_),
        fine=((pl.col("tick") + FINE - 1) // FINE).cast(pl.Int64))
    orgs = run.class_of(run.orgs, "now_hash").with_columns(
        test=pl.col("now_hash").is_in(tl), entered=pl.col("exec_by_others") > 0)
    # Exact children per executor (child == executor's body at `divide`).
    kids = (run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash"))
            .group_by("executor").agg(exact_children=pl.len()).rename({"executor": "id"}))
    deaths = (run.class_of(run.deaths, "birth_hash")
              .with_columns(bin=binx("tick"), test=pl.col("birth_hash").is_in(tl),
                            entered=pl.col("exec_by_others") > 0)
              .join(kids, on="id", how="left").with_columns(pl.col("exact_children").fill_null(0)))
    rdeaths = deaths.filter(pl.col("class") == "replicator")
    tdeaths = deaths.filter(pl.col("test"))

    # Per-bin aggregates, as dicts keyed by bin (or census tick).
    by = lambda df, key: {r[key]: r for r in df.iter_rows(named=True)}
    eb = by(ex.group_by("bin").agg(rep_n=pl.len(), test_share=pl.col("test").mean(),
                                   prefix_share=pl.col("pre").mean(),
                                   long_share=(pl.col("len") >= LONG).mean()), "bin")
    cb = by(orgs.group_by("tick").agg(
        pop=pl.len(), test_alive=pl.col("test").sum(),
        test_entered=(pl.col("test") & pl.col("entered")).sum(),
        rep_alive=(pl.col("class") == "replicator").sum(),
        exec_foreign=pl.col("exec_foreign").sum(), executed=pl.col("executed").sum()), "tick")
    rb = by(rdeaths.group_by("bin").agg(death_aggs()), "bin")
    tb = by(tdeaths.group_by("bin").agg(
        n=pl.len(), paid_n=(pl.col("paid_for_others_m") > 0).sum(),
        age_med=pl.col("age").median(), kids_mean=pl.col("exact_children").mean()), "bin")

    bins = []
    for k in range(1, n_bins + 1):
        hi = k * bin_size
        e, c, r, t = eb.get(k), cb.get(hi), rb.get(k), tb.get(k)
        bins.append(dict(
            rule=rule, genome=genome, seed=seed, bin=k, tick_end=hi,
            rep_n=e["rep_n"] if e else 0,
            test_share=e["test_share"] if e else None,
            prefix_share=e["prefix_share"] if e else None,
            long_share=e["long_share"] if e else None,
            test_alive=c["test_alive"] if c else 0,
            pop=c["pop"] if c else 0,
            rep_alive=c["rep_alive"] if c else 0,
            foreign_exec_share=c["exec_foreign"] / c["executed"] if c and c["executed"] else None,
            rep_deaths=r["n"] if r else 0,
            rep_deaths_paid=r["paid_n"] if r else 0,
            rep_deaths_paid_share=r["paid_n"] / r["n"] if r else None,
            test_deaths=t["n"] if t else 0,
            test_entered_share=t["paid_n"] / t["n"] if t else None,
            test_age_med=t["age_med"] if t else None,
            test_children_mean=t["kids_mean"] if t else None,
            entered_share=r["entered_n"] / r["n"] if r else None,
            cycles_lost_per_tick=r["lost_tick"] if r else None,
            entered_children_ratio=ratio_of(r["kids_in"], r["kids_out"]) if r else None,
            entered_age_ratio=ratio_of(r["age_in"], r["age_out"]) if r else None,
            entered_rate_ratio=rate_ratio(r) if r else None,
            test_alive_entered_share=c["test_entered"] / c["test_alive"] if c and c["test_alive"] else None,
        ))

    # Fine bins after the injection: births in ticks (inject, ticks].
    fine = (ex.filter(pl.col("tick") > inject).group_by("fine").agg(share=pl.col("test").mean())
            .with_columns(tick_end=pl.col("fine") * FINE).sort("fine"))
    above = fine.filter(pl.col("share") > GONE)
    last_fine = int(fine["tick_end"].max()) if fine.height else inject
    last_tick = int(above["tick_end"].max()) if above.height else inject
    censored = above.height > 0 and last_tick >= last_fine

    living = (orgs.filter(pl.col("tick") >= inject).group_by("tick")
              .agg(test_alive=pl.col("test").sum(), test_entered=(pl.col("test") & pl.col("entered")).sum())
              .sort("tick")
              .with_columns(test_entered_share=pl.when(pl.col("test_alive") > 0)
                            .then(pl.col("test_entered") / pl.col("test_alive")),
                            rule=pl.lit(rule), genome=pl.lit(genome), seed=pl.lit(seed)))
    gt = living.filter(pl.col("test_alive") > ALIVE_MIN)
    final = int(run.orgs["tick"].max())
    inj = (run.meta.get("injections") or [{}])[0]
    starts = inj.get("starts", [])
    post = [b for b in bins if b["tick_end"] > inject]
    shares = [b["test_share"] for b in post if b["test_share"] is not None]
    k0 = inject // bin_size

    # After the injection, pooled.
    rp = rdeaths.filter(pl.col("tick") > inject).select(death_aggs()).row(0, named=True)
    intr = deaths.filter((pl.col("tick") > inject) & (pl.col("exec_foreign") > 0))
    resident = intr.filter(pl.col("exec_foreign") > RESIDENT_FRAC * pl.col("executed")).height
    pops = orgs.filter(pl.col("tick") > inject).group_by("tick").len()
    end = living.filter(pl.col("tick") == final)
    summary = dict(
        rule=rule, genome=genome, seed=seed,
        placed=sum(1 for s in starts if s >= 0), copies=len(starts),
        last_share=bins[-1]["test_share"] if bins else None,
        last_prefix_share=bins[-1]["prefix_share"] if bins else None,
        pre_share=bins[k0 - 1]["test_share"] if 1 <= k0 <= len(bins) else None,
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
        pop_mean_post=float(pops["len"].mean()) if pops.height else None,
        rep_deaths_post=rp["n"],
        rep_entered_post=rp["entered_n"] / rp["n"] if rp["n"] else None,
        entered_children_ratio_post=ratio_of(rp["kids_in"], rp["kids_out"]),
        entered_age_ratio_post=ratio_of(rp["age_in"], rp["age_out"]),
        entered_rate_ratio_post=rate_ratio(rp),
        cycles_lost_per_tick_post=rp["lost_tick"],
        lost_per_age_post=rp["lost_sum"] / rp["age_sum"] if rp["age_sum"] else None,
        taxed_per_age_post=rp["taxed_sum"] / rp["age_sum"] if rp["age_sum"] else None,
        intruders_post=intr.height,
        intruder_resident_share_post=resident / intr.height if intr.height else None,
        test_alive_entered_share_end=end["test_entered_share"][0] if end.height else None,
    )
    for k in sel_bins(k0, n_bins):
        if k > k0:
            summary[f"share_b{k}"] = bins[k - 1]["test_share"]
    return bins, summary, living.to_dicts(), tdeaths.select(
        pl.lit(rule).alias("rule"), pl.lit(genome).alias("genome"), pl.lit(seed).alias("seed"),
        "tick", "id", "age", "paid_for_others_m", "exec_by_others", "cycles_lost_m", "cycles_taxed_m",
        "exact_children", "offspring")


def add_norms(bdf: pl.DataFrame, runs: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """`entered_rate_norm`: each run's `entered_rate_ratio` over the n0 run
    with the same injected genome and seed (per bin in bins.csv, after the
    injection in runs.csv). Null where the n0 run or either ratio is missing,
    or the n0 ratio is 0; 1 for the n0 runs themselves."""
    def norm(df, key, col, out_col):
        base = df.filter(pl.col("rule") == "n0").select(*key, pl.col(col).alias("_n0"))
        return (df.join(base, on=key, how="left", maintain_order="left")
                .with_columns(pl.when(pl.col("_n0") > 0).then(pl.col(col) / pl.col("_n0")).alias(out_col))
                .drop("_n0"))
    return (norm(bdf, ["genome", "seed", "bin"], "entered_rate_ratio", "entered_rate_norm"),
            norm(runs, ["genome", "seed"], "entered_rate_ratio_post", "entered_rate_norm_post"))


def mean_of(x: pl.DataFrame, c: str):
    v = x[c].drop_nulls()
    return v.mean() if v.len() else None


# ---- tax calibration -----------------------------------------------------------

def calibrate(out: Path, seeds: list[int], inject: int) -> dict | None:
    """T02 §4.2 from the `t50_resident` runs; None if any is missing."""
    parts = []
    for s in seeds:
        d = run_dir(out, "t50", "resident", s)
        if not (d / "classes.csv").exists():
            return None
        run = load(d)
        check_rule(run, "t50", None)
        parts.append(run.class_of(run.deaths, "birth_hash")
                     .filter((pl.col("tick") > inject) & (pl.col("class") == "replicator"))
                     .select("age", "exec_by_others", "cycles_lost_m"))
    df = pl.concat(parts)
    n = df.height
    entered = int((df["exec_by_others"] > 0).sum())
    if n == 0 or entered == 0:
        raise SystemExit(f"calibration: {n} replicator-class deaths after {inject}, {entered} entered; "
                         "cannot set the tax")
    f = entered / n
    lost, age = int(df["cycles_lost_m"].sum()), int(df["age"].sum())
    r = lost / age
    p_exact = 100 * r / (f * CAP_M)
    p = min(100, max(0, math.floor(p_exact + 0.5)))
    if p == 0:
        raise SystemExit(f"calibration: P = {p_exact:.3f} rounds to 0 (F = {f!r}, r = {r:.2f}); a tax of 0 "
                         "is no control. Check the t50 runs before going on.")
    return dict(source="t50_resident", seeds=seeds, inject=inject, deaths=n, entered=entered,
                F=f, cycles_lost_m=lost, age=age, r=r, cap_m=CAP_M, P_exact=p_exact, P=p)


def tax_of(calib: dict | None, pct: int | None, frac: float | None) -> Tax | None:
    if pct is not None or frac is not None:
        if pct is None or frac is None:
            raise SystemExit("--tax-pct and --tax-frac go together")
        return (pct, frac)
    return (int(calib["P"]), float(calib["F"])) if calib else None


# ---- tables ----------------------------------------------------------------------

pct = lambda v: "–" if v is None else f"{100 * v:.2f}%"
f0 = lambda v: "–" if v is None else f"{v:,.0f}"
f1 = lambda v: "–" if v is None else f"{v:,.1f}"
f2 = lambda v: "–" if v is None else f"{v:.2f}"
yn = lambda ok: "holds" if ok else "fails"


def med(x: pl.DataFrame, c: str):
    v = x[c].drop_nulls()
    return v.median() if v.len() else None


def pilot_table(runs: pl.DataFrame, calib: dict | None, tax: Tax | None) -> list[str]:
    """What T02 §6 asks for before the main stage: population and
    `entered_children_ratio` per rule, with the README's other readings."""
    lines = ["## Pilot readings (not evidence)", "",
             "After the injection: population (median over seeds of the mean over censuses, and at the end), "
             "replicator-class deaths entered (`exec_by_others` > 0, median), `entered_rate_ratio` (median) and "
             "`entered_rate_norm` (that over the n0 run of the same genome and seed; mean over seeds, which "
             "governs the branch), the diagnostics `entered_children_ratio` and `entered_age_ratio` (medians), "
             "mean debit per tick of entered deaths (milli-units; cap 32,000), intruder deaths resident "
             f"(`exec_foreign / executed` > {RESIDENT_FRAC}), and the test genome's last-bin share.", "",
             "| rule | genome | pop mean | pop end | entered | rate ratio | rate norm (mean) | children ratio "
             "| age ratio | lost/tick | resident intruders | last share | per seed rate norm |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for rule in RULES:
        for g in GENOMES:
            x = runs.filter((pl.col("rule") == rule) & (pl.col("genome") == g)).sort("seed")
            if not x.height:
                continue
            per = ", ".join(f"s{s} {f2(v)}" for s, v in zip(x["seed"], x["entered_rate_norm_post"]))
            lines.append(f"| {rule} | {g} | {f0(med(x, 'pop_mean_post'))} | {f0(med(x, 'final_pop'))} "
                         f"| {pct(med(x, 'rep_entered_post'))} | {f2(med(x, 'entered_rate_ratio_post'))} "
                         f"| {f2(mean_of(x, 'entered_rate_norm_post'))} "
                         f"| {f2(med(x, 'entered_children_ratio_post'))} | {f2(med(x, 'entered_age_ratio_post'))} "
                         f"| {f0(med(x, 'cycles_lost_per_tick_post'))} "
                         f"| {pct(med(x, 'intruder_resident_share_post'))} | {pct(med(x, 'last_share'))} | {per} |")
    x = runs.filter((pl.col("rule") == "t50") & (pl.col("genome") == "resident"))
    if x.height:
        m = mean_of(x, "entered_rate_norm_post")
        if m is None:
            branch = "not computable (no n0 pair, or no entered or unentered deaths)"
        elif m > RATIO_HI:
            branch = (f"above {RATIO_HI}: entries too brief for the cost to bite; read the resident-intruder "
                      "column (tasks README, E014 pilot)")
        elif m < RATIO_LO:
            branch = f"below {RATIO_LO}: outside the window, no branch written for it"
        else:
            branch = f"in [{RATIO_LO}, {RATIO_HI}]: the expected branch"
        lines += ["", f"Pilot branch (decided 2026-10-13): mean over seeds of t50_resident "
                  f"`entered_rate_norm_post` = {f2(m)}, {branch}."]
    lines += ["", "## Tax calibration", ""]
    if calib:
        lines.append(f"From {calib['source']}, seeds {calib['seeds']}, replicator-class deaths after tick "
                     f"{calib['inject']:,}: {calib['deaths']:,} deaths, {calib['entered']:,} entered, "
                     f"F = {calib['F']!r}; r = {calib['cycles_lost_m']:,} / {calib['age']:,} = {calib['r']:.2f} "
                     f"milli-units per organism-tick; P = 100 r / (F x {calib['cap_m']:,}) = "
                     f"{calib['P_exact']:.3f}, rounded {calib['P']}.")
    else:
        lines.append("Not calibrated: the t50_resident runs are not all present.")
    if tax:
        lines.append(f"Tax arm run with --cycle-tax-pct {tax[0]} --cycle-tax-frac {tax[1]!r}.")
        x = runs.filter(pl.col("rule") == "tax")
        y = runs.filter(pl.col("rule") == "t50")
        if x.height and y.height:
            lines.append(f"Check: median `taxed_per_age_post` under tax {f1(med(x, 'taxed_per_age_post'))} "
                         f"against median `lost_per_age_post` under t50 {f1(med(y, 'lost_per_age_post'))} "
                         "(milli-units per organism-tick).")
    return lines


def predictions(runs: pl.DataFrame, seeds: list[int]) -> list[str]:
    n = len(seeds)
    at_least = lambda k: math.ceil(k * n / 30)
    at_most = lambda k: math.floor(k * n / 30)

    def col(rule, genome, c):
        x = runs.filter((pl.col("rule") == rule) & (pl.col("genome") == genome))
        return dict(zip(x["seed"].to_list(), x[c].to_list()))

    def kept(rule, genome):  # seeds with last-bin share >= 1%
        return sum(1 for s, v in col(rule, genome, "last_share").items() if s in seeds and v is not None and v >= GONE)

    lines = ["## Prediction checks (H16, T02 section 4.4)", "",
             f"{n} seeds; k of 30 read as >= ceil(k n / 30), <= floor(k n / 30). 'Kept' = last-bin share >= "
             f"{pct(GONE)} of replicator-class exact births.", ""]

    # 1. Persistence of the resident under every rule.
    need1 = at_least(27)
    fail1 = []
    for rule in RULES:
        a, sh = col(rule, "resident", "alive_end"), col(rule, "resident", "last_share")
        good = sum(1 for s in seeds if (a.get(s) or 0) >= ALIVE_MIN and sh.get(s) is not None and sh[s] >= GONE)
        ok = good >= need1
        if not ok:
            fail1.append(rule)
        lines.append(f"1 ({rule}). Resident >= {ALIVE_MIN} alive at the end and last share >= {pct(GONE)}: "
                     f"{good} of {n} [>= {need1}]. {yn(ok)}.")
    dropped = "t75" in fail1
    theft_ns = ["t25", "t50"] if dropped else ["t25", "t50", "t75"]
    lines.append(f"1. Every rule: {yn(not fail1)}."
                 + (" t75 is the slow-starvation arm and is dropped from 2-5." if dropped else ""))

    # 2. Entered hosts graded, on the resident runs, in the normalised
    # rate (decided 2026-10-13; n0's norm is 1 by construction).
    need2 = at_least(20)
    r50 = col("t50", "resident", "entered_rate_norm_post")
    in50 = sum(1 for s in seeds if r50.get(s) is not None and RATIO_LO <= r50[s] <= RATIO_HI)
    ok2 = in50 >= need2
    res = lambda rule: runs.filter((pl.col("rule") == rule) & (pl.col("genome") == "resident"))
    lines.append(f"2. `entered_rate_norm_post` (resident runs): t50 in [{RATIO_LO}, {RATIO_HI}] in {in50} of {n} "
                 f"[>= {need2}], mean {f2(mean_of(res('t50'), 'entered_rate_norm_post'))}. {yn(ok2)}. The n0 clause "
                 f"is 1 by construction in this currency; n0's raw `entered_rate_ratio_post` median "
                 f"{f2(med(res('n0'), 'entered_rate_ratio_post'))} (t50 "
                 f"{f2(med(res('t50'), 'entered_rate_ratio_post'))}). Diagnostics, medians n0 / t50: "
                 f"`entered_children_ratio_post` {f2(med(res('n0'), 'entered_children_ratio_post'))} / "
                 f"{f2(med(res('t50'), 'entered_children_ratio_post'))}, `entered_age_ratio_post` "
                 f"{f2(med(res('n0'), 'entered_age_ratio_post'))} / {f2(med(res('t50'), 'entered_age_ratio_post'))}.")

    # 3. The eject pays.
    need3, most3 = at_least(20), at_most(5)
    counts = {}
    for rule in ["t25", "t50", "t75"]:
        e, i = kept(rule, "eject"), kept(rule, "inert")
        counts[rule] = e
        tag = " (dropped)" if rule not in theft_ns else ""
        lines.append(f"3 ({rule}{tag}). Kept: eject {e} of {n} [>= {need3}], inert {i} of {n} [<= {most3}]."
                     + (f" {yn(e >= need3 and i <= most3)}." if rule == "t50" else ""))
    ok3 = kept("t50", "eject") >= need3 and kept("t50", "inert") <= most3
    lines.append(f"3. At t50: {yn(ok3)}.")

    # 4. The control.
    diff4 = at_most(3)
    te, ti = kept("tax", "eject"), kept("tax", "inert")
    ok4 = abs(te - ti) <= diff4
    lines.append(f"4. Under tax, kept: eject {te}, inert {ti}; difference {abs(te - ti)} [<= {diff4}]. {yn(ok4)}.")

    # 5. Dose.
    seq = [counts[r] for r in theft_ns]
    ok5 = all(a <= b for a, b in zip(seq, seq[1:]))
    lines.append(f"5. Eject kept over {', '.join(theft_ns)}: {', '.join(map(str, seq))}; non-decreasing: {yn(ok5)}.")

    # Refutation.
    every = all(counts[r] < need3 for r in theft_ns)
    acct = (not ok4) and te > ti
    lines += ["", f"Refuted by 3 (eject not kept in >= {need3} at every N in {', '.join(theft_ns)}): "
              f"{'yes' if every else 'no'}. Refuted by 4 (eject maintained under the tax beyond inert by more than "
              f"{diff4}; audit the accounting first): {'yes' if acct else 'no'}."]
    return lines


def summarize(stage: str, bdf: pl.DataFrame, runs: pl.DataFrame, living: pl.DataFrame, tdeaths: pl.DataFrame,
              seeds: list[int], ticks: int, inject: int, bin_size: int, calib: dict | None,
              tax: Tax | None) -> str:
    n_bins = ticks // bin_size
    k0 = inject // bin_size
    ks = sel_bins(k0, n_bins)
    rules = [r for r in RULES if runs.filter(pl.col("rule") == r).height]
    genomes = [g for g in GENOMES if runs.filter(pl.col("genome") == g).height]
    lines = [f"# E014 cycle theft, {stage}: rules {', '.join(rules)} x genomes {', '.join(genomes)} x seeds "
             f"{', '.join(map(str, seeds))}, {ticks:,} ticks, {COPIES} copies at {inject:,}, bins of {bin_size:,}", ""]
    if tax:
        lines += [f"Tax arm: --cycle-tax-pct {tax[0]} --cycle-tax-frac {tax[1]!r}.", ""]
    lines += [
        f"Per run: copies placed, test share of replicator-class exact births in bins {', '.join(map(str, ks))} "
        f"(bin {k0} is before the injection), end tick of the last {FINE}-tick bin above 1%, last census with "
        f"> {ALIVE_MIN} living test bodies, living test bodies at the end, final population.", "",
        "| rule | genome | seed | placed | " + " | ".join(f"b{k}" for k in ks)
        + " | last > 1% | alive > 10 last | alive end | final pop |",
        "|---|---|---|---|" + "---|" * len(ks) + "---|---|---|---|",
    ]
    order = {g: i for i, g in enumerate(GENOMES)}
    rorder = {r: i for i, r in enumerate(RULES)}
    srt = runs.with_columns(o=pl.col("genome").replace_strict(order), ro=pl.col("rule").replace_strict(rorder)
                            ).sort(["ro", "o", "seed"])
    for r in srt.iter_rows(named=True):
        x = bdf.filter((pl.col("rule") == r["rule"]) & (pl.col("genome") == r["genome"]) & (pl.col("seed") == r["seed"]))
        m = dict(zip(x["bin"].to_list(), x["test_share"].to_list()))
        t = r["last_above_1pct"]
        lines.append(f"| {r['rule']} | {r['genome']} | {r['seed']} | {r['placed']}/{r['copies']} | "
                     + " | ".join(pct(m.get(k)) for k in ks)
                     + f" | {'>= ' if r['censored'] else ''}{t:,} | {f0(r['last_alive_gt10'])} | {r['alive_end']} "
                     f"| {r['final_pop']} |")
    ticks_l = [inject] + [k * bin_size for k in ks if k > k0]
    lines += [
        "", "Living test bodies (canonical match of the current body), and the share of them entered so far, at "
        "the injection and the bin ends above.", "",
        "| rule | genome | seed | " + " | ".join(f"{t:,}" for t in ticks_l) + " |",
        "|---|---|---|" + "---|" * len(ticks_l),
    ]
    for r in srt.iter_rows(named=True):
        x = living.filter((pl.col("rule") == r["rule"]) & (pl.col("genome") == r["genome"]) & (pl.col("seed") == r["seed"]))
        m = {t: (a, s) for t, a, s in zip(x["tick"].to_list(), x["test_alive"].to_list(),
                                          x["test_entered_share"].to_list())}
        cell = lambda t: "–" if t not in m else f"{f0(m[t][0])} ({pct(m[t][1])})"
        lines.append(f"| {r['rule']} | {r['genome']} | {r['seed']} | " + " | ".join(cell(t) for t in ticks_l) + " |")
    lines += [
        "", "Per bin, medians across seeds: test share / prefix share / bodies >= 26 bytes / living test / population / "
        "replicator-class alive / foreign exec share / replicator deaths entered / entered rate ratio / "
        "entered rate norm (mean across seeds) / entered children ratio / entered age ratio / debit per tick of "
        "entered deaths (milli-units).", "",
        "| rule | genome | bin | test | prefix | >= 26 bytes | test alive | pop | rep alive | foreign | entered "
        "| rate ratio | rate norm | children ratio | age ratio | lost/tick |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for rule in rules:
        for g in genomes:
            for k in ks:
                x = bdf.filter((pl.col("rule") == rule) & (pl.col("genome") == g) & (pl.col("bin") == k))
                if not x.height:
                    continue
                lines.append(f"| {rule} | {g} | {k} | {pct(med(x, 'test_share'))} | {pct(med(x, 'prefix_share'))} "
                             f"| {pct(med(x, 'long_share'))} | {f0(med(x, 'test_alive'))} | {f0(med(x, 'pop'))} "
                             f"| {f0(med(x, 'rep_alive'))} | {pct(med(x, 'foreign_exec_share'))} "
                             f"| {pct(med(x, 'entered_share'))} | {f2(med(x, 'entered_rate_ratio'))} "
                             f"| {f2(mean_of(x, 'entered_rate_norm'))} | {f2(med(x, 'entered_children_ratio'))} "
                             f"| {f2(med(x, 'entered_age_ratio'))} | {f0(med(x, 'cycles_lost_per_tick'))} |")
    lines += [
        "", "Deaths of test-genome organisms (birth genome is the test genome), seeds pooled: count, share entered "
        "(`exec_by_others` > 0), median age, mean exact children; and the same by seed.", "",
        "| rule | genome | deaths | entered | median age | mean exact children | by seed (deaths, entered, age, children) |",
        "|---|---|---|---|---|---|---|",
    ]
    ent = lambda y: float((y["exec_by_others"] > 0).mean()) if y.height else None
    for rule in rules:
        for g in genomes:
            x = tdeaths.filter((pl.col("rule") == rule) & (pl.col("genome") == g))
            per = []
            for s in seeds:
                y = x.filter(pl.col("seed") == s)
                per.append(f"s{s} {y.height}, {pct(ent(y))}, {f0(y['age'].median() if y.height else None)}, "
                           f"{f1(y['exact_children'].mean() if y.height else None)}")
            lines.append(f"| {rule} | {g} | {x.height} | {pct(ent(x))} "
                         f"| {f0(x['age'].median() if x.height else None)} "
                         f"| {f1(x['exact_children'].mean() if x.height else None)} | {'; '.join(per)} |")
    lines += [""] + pilot_table(runs, calib, tax)
    if stage == "main":
        lines += [""] + predictions(runs, seeds)
    return "\n".join(lines)


# ---- driver ----------------------------------------------------------------------

def exe_path() -> Path:
    """The release binary's path, without building (dry run)."""
    for name in ("evo-core.exe", "evo-core"):
        p = CORE / "target" / "release" / name
        if p.exists():
            return p
    return CORE / "target" / "release" / "evo-core"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="See the module docstring for the measures and predictions.")
    ap.add_argument("stage", choices=list(STAGES), help="pilot (3 seeds, 50,000 ticks) or main (30, 250,000)")
    ap.add_argument("--seeds", type=int, help="seeds 1..N (default: the stage's)")
    ap.add_argument("--ticks", type=int, help="override for smoke tests only")
    ap.add_argument("--inject-tick", type=int, default=INJECT, help="override for smoke tests only")
    ap.add_argument("--bin", type=int, default=BIN, help="bin size; override for smoke tests only")
    ap.add_argument("--out", type=Path, help="output root (default runs/e014_pilot or runs/e014)")
    ap.add_argument("--rules", default=",".join(RULES), help=f"comma list from {','.join(RULES)}")
    ap.add_argument("--genomes", default=",".join(GENOMES), help=f"comma list from {','.join(GENOMES)}")
    ap.add_argument("--tax-pct", type=int, help="tax P for the tax arm instead of the pilot's calibration")
    ap.add_argument("--tax-frac", type=float, help="tax F for the tax arm instead of the pilot's calibration")
    ap.add_argument("--calib", type=Path, help="calib.json to take the tax from (main; default the pilot's)")
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--force", action="store_true", help="redo runs that exist")
    ap.add_argument("--no-compress", action="store_true",
                    help="leave births, deaths, orgs and census CSVs plain (default: gzip each after its run)")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the command lines and exit")
    a = ap.parse_args()

    st = STAGES[a.stage]
    out = a.out or st["out"]
    ticks = a.ticks or st["ticks"]
    seeds = list(range(1, (a.seeds or st["seeds"]) + 1))
    rules = [r.strip() for r in a.rules.split(",") if r.strip()]
    genomes = [g.strip() for g in a.genomes.split(",") if g.strip()]
    for r in rules:
        if r not in RULES:
            raise SystemExit(f"unknown rule {r}")
    for g in genomes:
        if g not in GENOMES:
            raise SystemExit(f"unknown genome {g}")
    if not 0 < a.inject_tick < ticks:
        raise SystemExit("the injection tick must be inside the run")
    theft_jobs = [(r, g, s) for r in rules if r != "tax" for g in genomes for s in seeds]
    tax_jobs = [("tax", g, s) for g in genomes for s in seeds] if "tax" in rules else []

    # The tax: given, from this stage's calibration (pilot, once the t50
    # resident runs exist), or from the pilot's calib.json (main).
    calib_path = out / "calib.json"
    calib = json.loads(calib_path.read_text()) if calib_path.exists() else None
    if a.stage == "main" and calib is None:
        src = a.calib or STAGES["pilot"]["out"] / "calib.json"
        calib = json.loads(src.read_text()) if src.exists() else None
    tax = tax_of(calib, a.tax_pct, a.tax_frac)

    if a.dry_run:
        exe = exe_path()
        for r, g, s in theft_jobs + tax_jobs:
            run, cls = commands(exe, run_dir(out, r, g, s), g, s, ticks, a.inject_tick, rule_flags(r, tax))
            print(" ".join(run))
            print(" ".join(cls))
        if tax_jobs and tax is None:
            print("# tax arm: P and F come from the pilot's calibration (t50_resident), not yet available")
        return

    out.mkdir(parents=True, exist_ok=True)
    t_all = time.time()
    exe = None if a.analyse_only else binary()

    def run_all(jobs, tax_):
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda j: run_one(exe, out, *j, ticks, a.inject_tick, tax_, a.force,
                                                not a.no_compress), jobs):
                print(msg, flush=True)

    if exe is not None:
        run_all(theft_jobs, None)
    if a.stage == "pilot" and a.tax_pct is None:
        c = calibrate(out, seeds, a.inject_tick)
        if c is not None:
            calib = c
            calib_path.write_text(json.dumps(c, indent=2) + "\n", encoding="utf-8", newline="")
            tax = tax_of(calib, None, None)
            print(f"calibration: F = {c['F']!r}, r = {c['r']:.2f}, P = {c['P']} ({c['P_exact']:.3f})", flush=True)
    if exe is not None and tax_jobs:
        if tax is None:
            print("tax arm skipped: no calibration (run the t50 resident arm first, or give --tax-pct/--tax-frac)")
        else:
            run_all(tax_jobs, tax)
    if exe is not None:
        print(f"runs and classes: {time.time() - t_all:.0f} s", flush=True)

    jobs = theft_jobs + tax_jobs

    def one(j):
        d = run_dir(out, *j)
        if not (d / "classes.csv").exists():
            return None
        return analyse_run(out, *j, ticks, a.inject_tick, a.bin, tax)

    with ThreadPoolExecutor(min(a.jobs, 6)) as ex:
        results = [r for r in ex.map(one, jobs) if r is not None]
    if not results:
        raise SystemExit("no finished runs to analyse")
    bdf = pl.DataFrame([b for bins, _, _, _ in results for b in bins], infer_schema_length=None)
    runs = pl.DataFrame([s for _, s, _, _ in results], infer_schema_length=None)
    bdf, runs = add_norms(bdf, runs)
    living = pl.DataFrame([x for _, _, lv, _ in results for x in lv], infer_schema_length=None)
    tdeaths = pl.concat([td for _, _, _, td in results], how="vertical_relaxed")
    bdf.write_csv(out / "bins.csv")
    runs.write_csv(out / "runs.csv")
    living.write_csv(out / "living.csv")
    tdeaths.write_csv(out / "deaths.csv")
    text = summarize(a.stage, bdf, runs, living, tdeaths, seeds, ticks, a.inject_tick, a.bin, calib, tax)
    (out / "summary.md").write_text(text + "\n", encoding="utf-8", newline="")
    print(text)
    print(f"total {time.time() - t_all:.0f} s")


if __name__ == "__main__":
    main()
