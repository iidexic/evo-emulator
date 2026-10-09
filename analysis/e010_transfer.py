"""E010: the transfer rule (the intruder gains what the host loses). Two
subcommands, run in order:

- `calibrate`: the standard one-founder world for 50,000 ticks under each N
  of `--transfer-pct N` and the N = 0 reference, seeds 1-3, measured over
  ticks 40,000-50,000; then the design's arm rule picks the gate's N.
- `inject`: the E009b injection test under the chosen rule(s): 50 copies of
  a test genome into free memory at the start of tick 25,000
  (`--inject 25000:HEX:50`), followed to tick 50,000.

Protocol and predictions: docs/research/experiments/2026-10-08-e010-transfer.md.
This is analysis/e009b_late_injection.py parameterised by rule set and
genome set; its matching and readings are unchanged unless said here.

Usage (from analysis/):

    uv run e010_transfer.py calibrate --jobs 12                 # build, run, classify, analyse
    uv run e010_transfer.py calibrate --analyse-only            # runs exist; redo the table
    uv run e010_transfer.py inject --rules 0,150 --jobs 12      # the gate at the chosen N
    uv run e010_transfer.py inject --rules 0,150 --analyse-only
    uv run e010_transfer.py inject --rules 0,150 --seeds 1 --ticks 6000 --inject-tick 3000 --out /tmp/x  # smoke test only

Rules. `n0` = no flag (E007 physics, re-run under this binary so the CSV
columns match); `n<N>` = `--transfer-pct N`. Every `--classify` call gets
the rule's flags (a lone genome executes no foreign code, so the classes
are those of N = 0).

Calibration (`runs/e010_calib/n<N>/s<seed>/`; table in calib.csv and
calib.md). Per run, over the window (ticks 4/5 of the run to its end:
40,000-50,000), with replicator class from classes.csv as in E009b (exact
births by the child's raw hash, deaths by birth hash, living bodies by
now hash):

- `rep_births_per_1k`: replicator-class exact births (child == executor's
  body at `divide`) per 1,000 ticks; `rep_births_vs_n0` = that over the n0
  run of the same seed.
- `rep_alive_end`: living replicator-class bodies at the last census.
- `foreign_deaths`: sum `exec_foreign` / sum `executed` over all deaths in
  the window (lifetime counters; lifetimes are about 20 ticks, so this is
  close to the window's own instructions); `foreign_census`: the E009b
  measure, the same over living bodies at the last census.
- `entered`: share of replicator-class deaths in the window with
  `paid_for_others_m` > 0 (0 by construction at n0).
- `entry_cost_med`: median `paid_for_others_m` (units) among entered
  replicator-class deaths; `entry_cost_share_med`: median of each one's
  `paid_for_others_m / spent_m`.
- `profit`: sum `gained_from_others_m` / sum `spent_m` over deaths in the
  window that are not replicator-class.
- `pad_share`: share of all births in the window (exact or not) with a body
  of 3 bytes or less.
- `entered_first`, `entered_last`: `entered` over replicator-class deaths
  whose body start is in the first patch, and in the last patch (the
  design's sink: an `eject` sends intruders to addresses 0 and
  world_size - 4); with their counts.

Arm rule (the design's, read mechanically, fixed before the runs): for each
N, the median over seeds of `entered` and the median over seeds of
`rep_births_vs_n0`. The gate's N is the lowest N with median `entered` >=
50% and median `rep_births_vs_n0` >= 25%. A second arm is the N one step
lower in the list (100, 150, 200, 300) if its median `entered` is >= 30%
(the entered clause only, as written; if it fails the births clause the
table says so). If no N qualifies: median `entered` < 50% at the highest N
means the transfer does not make intrusion common (stop); otherwise births
< 25% wherever entries are common means parasite-driven collapse (stop).

Gate (`runs/e010a/<rule>_<genome>/s<seed>/`; bins.csv, runs.csv,
living.csv, deaths.csv, summary.md in runs/e010a/). Genomes:

- `eject` = `self 1 ; swap C ; self 0 ; sub C ; skipz A ; jmpa D`
  (33 52 13 4f 08 6d) + the K = 120 ancestor, 27 bytes;
- `trap` = `self 1 ; swap C ; self 0 ; sub C ; jmpr A` (33 52 13 4f 0c) +
  the ancestor, 26 bytes (E009b's `prefix`);
- `inert` = six `zero D` (70 x 6) + the ancestor, 27 bytes;
- `resident` = the K = 120 ancestor, 21 bytes.

Matching as in E009b: a genome is the test genome when its canonical
instruction list equals the test genome's in full; it carries the test
prefix when its first canonical (op, modifier) pairs equal traits.EJECT
(six, `eject`), traits.INERT6 (six, `inert`) or traits.PREFIX (five,
`trap`); for `resident` the prefix measure is the canonical match. Per-bin
measures, `last_above_1pct`, `last_alive_gt10`, `alive_end` and the deaths
table as in E009b (`long_share` is still bodies of 26 bytes or more).
Added per run, from tick `inject` on: `rep_entered_post` (share of
replicator-class deaths after the injection with `paid_for_others_m` > 0),
`profit_post` (sum `gained_from_others_m` / sum `spent_m` over
non-replicator-class deaths after the injection), `entry_cost_med_post`
(median `paid_for_others_m`, units, of those entered replicator-class
deaths), `rep_births_late` (replicator-class exact births in the last
fifth of the run, 40,000-50,000), the sink entered fractions after the
injection and the living bodies in the first and last patch at the end
(all, and test-genome ones).

Predictions, read mechanically (fixed here, before the runs; "N" is each
non-zero rule run; "3 of 3" is over seeds):

1. World persists: `rep_births_late` at N over the n0 run of the same
   genome and seed >= 25%, in 3 of 3 seeds for every genome.
2. Entries common and profitable: at N, `rep_entered_post` >= 50% in 3 of
   3 seeds and `profit_post` > 0.5 in 3 of 3 seeds, for every genome.
3. Eject maintained: at N, `eject`'s `last_above_1pct` later than
   `inert`'s in 3 of 3 seeds, and `eject` `alive_end` >= 1 in >= 2 of 3.
   The fail branch's comparison is printed: the median
   `entry_cost_med_post` against the six-byte cost (about 36 units).
4. Trap a liability: at N, `trap`'s `last_above_1pct` <= `inert`'s in >= 2
   of 3 seeds.
5. N = 0 reference: at n0, the ratio max/min of ticks since the injection
   (`last_above_1pct` - inject; both 0 counts as 1, one 0 as infinite) of
   `eject` against `inert` <= 2 in >= 2 of 3 seeds, and the same for
   `trap` against `inert`.

Checks printed with the gate: within each rule and seed every genome's run
prints the same report line at the last report before the injection, equal
to the calibration run of that rule and seed if present; the n0 seed-1 runs
print the E007 reference line at tick 20,000.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

import traits
from evo_run import ROOT, binary, load

OUT_CAL = ROOT / "runs" / "e010_calib"
OUT_INJ = ROOT / "runs" / "e010a"
TICKS = 50_000
INJECT = 25_000
COPIES = 50
CENSUS = 500
BIN = 2_500
FINE = 100  # resolution of `last_above_1pct` (births carry exact ticks)
HARNESS_TICKS = 3_000
LONG = 26
ALIVE_MIN = 10
PAD_LEN = 3  # a `pad` lineage: bodies of 3 bytes or less
CAL_NS = (100, 150, 200, 300)
ENTERED_MIN = 0.50  # arm rule and prediction 2
SECOND_MIN = 0.30   # arm rule, second arm
BIRTHS_MIN = 0.25   # arm rule and prediction 1
PROFIT_MIN = 0.5    # prediction 2
SIX_BYTE_COST = 36  # units, the design's figure for the eject's cost per cycle
GONE = 0.01  # "lost" and "last > 1%"
RATE_FACTOR = 2.0
# E007's seed-1 report line at tick 20,000 (no flags); N = 0 must reproduce it.
REF_20000 = "20000,953,536,27,21,20.7,50,238498,237546,879038,378839,127,242"

ANC120 = "13325271fc11781605086c5a1845486c11101c130d"  # sim::ancestor(120, 16), checked by --disasm
GENOMES = {
    "eject": "3352134f086d" + ANC120,  # self 1 ; swap C ; self 0 ; sub C ; skipz A ; jmpa D
    "trap": "3352134f0c" + ANC120,     # self 1 ; swap C ; self 0 ; sub C ; jmpr A
    "inert": "70" * 6 + ANC120,        # zero D x 6
    "resident": ANC120,
}
SEQ = {"eject": traits.EJECT, "trap": traits.PREFIX, "inert": traits.INERT6, "resident": None}


def rule_name(n: int) -> str:
    return f"n{n}"


def rule_flags(n: int) -> list[str]:
    return [] if n == 0 else ["--transfer-pct", str(n)]


def run_world(exe: Path, d: Path, seed: int, ticks: int, flags: list[str], extra: list[str], force: bool) -> str:
    """Run one world into `d` and classify it under `flags`; skip what exists."""
    tag = f"{d.parent.name}/{d.name}"
    if not force and (d / "classes.csv").exists():
        return f"{tag}: done"
    t0 = time.time()
    if force or not (d / "genomes.csv").exists():
        if d.exists():
            shutil.rmtree(d)
        d.parent.mkdir(parents=True, exist_ok=True)
        cmd = [str(exe), "--ticks", str(ticks), "--seed", str(seed), "--report", str(CENSUS),
               "--census", str(CENSUS), "--out", str(d), *extra, *flags]
        with open(d.parent / f"s{seed}.stdout", "w") as out:
            subprocess.run(cmd, stdout=out, stderr=subprocess.DEVNULL, check=True)
    t1 = time.time()
    subprocess.run([str(exe), "--classify", str(d), "--harness-ticks", str(HARNESS_TICKS), *flags],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return f"{tag}: run {t1 - t0:.0f} s, classify {time.time() - t1:.0f} s"


def check_rule(run, n: int) -> None:
    got = run.meta.get("config", {}).get("transfer_pct")
    if got is None or int(got) != n:
        raise SystemExit(f"{run.dir}: meta.json has transfer_pct {got}, expected {n}")


def stdout_line(path: Path, tick: int) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        if line.startswith(f"{tick},"):
            return line
    return None


pct = lambda v: "–" if v is None else f"{100 * v:.2f}%"
f0 = lambda v: "–" if v is None else f"{v:,.0f}"
f1 = lambda v: "–" if v is None else f"{v:,.1f}"
f2 = lambda v: "–" if v is None else f"{v:.2f}"
yn = lambda ok: "holds" if ok else "fails"


def _frac(df: pl.DataFrame, expr: pl.Expr) -> float | None:
    return float(df.select(expr.mean()).item()) if df.height else None


def _ratio_sum(df: pl.DataFrame, num: str, den: str) -> float | None:
    d = int(df[den].sum()) if df.height else 0
    return int(df[num].sum()) / d if d else None


def deaths_measures(rd: pl.DataFrame, nd: pl.DataFrame, n_patches: int, patch_size: int) -> dict:
    """Entered fraction, entry cost and the sink split over replicator-class
    deaths `rd`; intruder profit over non-replicator-class deaths `nd`."""
    paid = pl.col("paid_for_others_m") > 0
    ent = rd.filter(paid)
    patch = (pl.col("start") // patch_size)
    first, last = rd.filter(patch == 0), rd.filter(patch == n_patches - 1)
    return dict(
        rep_deaths=rd.height,
        entered=_frac(rd, paid),
        entry_cost_med=float(ent["paid_for_others_m"].median()) / 1000 if ent.height else None,
        entry_cost_share_med=float(ent.select((pl.col("paid_for_others_m") / pl.col("spent_m")).median()).item())
        if ent.height else None,
        profit=_ratio_sum(nd, "gained_from_others_m", "spent_m"),
        nonrep_deaths=nd.height,
        entered_first=_frac(first, paid), n_first=first.height,
        entered_last=_frac(last, paid), n_last=last.height,
    )


# ---- calibrate ---------------------------------------------------------------


def calib_dir(out: Path, n: int, seed: int) -> Path:
    return out / rule_name(n) / f"s{seed}"


def calib_run(out: Path, n: int, seed: int, ticks: int) -> dict:
    d = calib_dir(out, n, seed)
    run = load(d)
    check_rule(run, n)
    cfg = run.meta["config"]
    patch_size, n_patches = int(cfg["patch_size"]), int(cfg["world_size"]) // int(cfg["patch_size"])
    lo, hi = ticks * 4 // 5, ticks
    win = (pl.col("tick") > lo) & (pl.col("tick") <= hi)
    ex = traits.exact_births(run, BIN).filter(win & (pl.col("class") == "replicator"))
    final = int(run.orgs["tick"].max())
    alive = run.class_of(run.orgs.filter(pl.col("tick") == final), "now_hash")
    deaths = run.class_of(run.deaths.filter(win), "birth_hash")
    rd, nd = deaths.filter(pl.col("class") == "replicator"), deaths.filter(pl.col("class") != "replicator")
    births = run.births.filter(win)
    ex_alive = int(alive["executed"].sum()) if alive.height else 0
    r = dict(
        n=n, seed=seed, window=f"{lo}-{hi}", final_tick=final,
        rep_births=ex.height,
        rep_births_per_1k=ex.height / ((hi - lo) / 1000),
        rep_alive_end=int((alive["class"] == "replicator").sum()) if alive.height else 0,
        pop_end=alive.height,
        foreign_deaths=_ratio_sum(deaths, "exec_foreign", "executed"),
        foreign_census=int(alive["exec_foreign"].sum()) / ex_alive if ex_alive else None,
        pad_share=_frac(births, pl.col("len") <= PAD_LEN),
        births=births.height,
        **deaths_measures(rd, nd, n_patches, patch_size),
        paid_by_sum=int(deaths["paid_by_others_m"].sum()) if deaths.height else 0,
    )
    return r


def arm_rule(cal: pl.DataFrame, ns: list[int]) -> tuple[list[str], int | None, int | None]:
    """The design's arm rule on the per-N medians. Returns the text, the
    chosen N and the second arm (None if none)."""
    med = {}
    for n in ns:
        x = cal.filter(pl.col("n") == n)
        e = x["entered"].drop_nulls()
        b = x["rep_births_vs_n0"].drop_nulls()
        med[n] = (e.median() if e.len() else None, b.median() if b.len() else None)
    lines = ["## Arm rule", "",
             f"Lowest N with median entered >= {pct(ENTERED_MIN)} and median replicator-class births >= "
             f"{pct(BIRTHS_MIN)} of n0's (same seed), over seeds; a second arm one step lower if its median "
             f"entered >= {pct(SECOND_MIN)}.", ""]
    chosen = None
    for n in ns:
        e, b = med[n]
        ok_e = e is not None and e >= ENTERED_MIN
        ok_b = b is not None and b >= BIRTHS_MIN
        lines.append(f"- N = {n}: median entered {pct(e)} [{'>=' if ok_e else '<'} {pct(ENTERED_MIN)}], "
                     f"median births vs n0 {pct(b)} [{'>=' if ok_b else '<'} {pct(BIRTHS_MIN)}]: "
                     f"{'qualifies' if ok_e and ok_b else 'does not qualify'}.")
        if chosen is None and ok_e and ok_b:
            chosen = n
    lines.append("")
    second = None
    if chosen is not None:
        k = ns.index(chosen)
        if k > 0:
            lower = ns[k - 1]
            e, b = med[lower]
            if e is not None and e >= SECOND_MIN:
                second = lower
                note = "" if (b is not None and b >= BIRTHS_MIN) else \
                    f" (note: its median births vs n0 is {pct(b)}, below {pct(BIRTHS_MIN)})"
                lines.append(f"Chosen N = {chosen}; second arm N = {lower} (median entered {pct(e)} >= "
                             f"{pct(SECOND_MIN)}){note}.")
            else:
                lines.append(f"Chosen N = {chosen}; no second arm (N = {lower} median entered {pct(e)} < "
                             f"{pct(SECOND_MIN)}).")
        else:
            lines.append(f"Chosen N = {chosen}; no second arm (no lower N in the list).")
    else:
        top = ns[-1]
        e_top = med[top][0]
        if e_top is None or e_top < ENTERED_MIN:
            lines.append(f"No N qualifies. Median entered at N = {top} is {pct(e_top)} < {pct(ENTERED_MIN)}: the "
                         "transfer does not make intrusion common (H15 fails on its premise). Stop.")
        else:
            common = [n for n in ns if med[n][0] is not None and med[n][0] >= ENTERED_MIN]
            lines.append(f"No N qualifies. Entries are common (median entered >= {pct(ENTERED_MIN)}) at N = "
                         f"{', '.join(map(str, common))} and births are below {pct(BIRTHS_MIN)} of n0's there: "
                         "parasite-driven collapse. Stop.")
    return lines, chosen, second


def calibrate(a: argparse.Namespace) -> None:
    out = a.out or OUT_CAL
    out.mkdir(parents=True, exist_ok=True)
    seeds = list(range(1, a.seeds + 1))
    ns = sorted(int(x) for x in a.ns.split(","))
    allns = [0, *ns]
    jobs = [(n, s) for n in allns for s in seeds]
    exe = binary()
    t_all = time.time()
    if not a.analyse_only:
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda j: run_world(exe, calib_dir(out, *j), j[1], a.ticks, rule_flags(j[0]), [],
                                                  a.force), jobs):
                print(msg, flush=True)
        print(f"runs and classes: {time.time() - t_all:.0f} s", flush=True)

    def one(j):
        return calib_run(out, *j, a.ticks) if (calib_dir(out, *j) / "classes.csv").exists() else None

    with ThreadPoolExecutor(min(a.jobs, 6)) as ex:
        rows = [r for r in ex.map(one, jobs) if r is not None]
    cal = pl.DataFrame(rows, infer_schema_length=None)
    base = cal.filter(pl.col("n") == 0).select("seed", rep_births_n0="rep_births")
    cal = (cal.join(base, on="seed", how="left")
           .with_columns(rep_births_vs_n0=pl.when(pl.col("rep_births_n0") > 0)
                         .then(pl.col("rep_births") / pl.col("rep_births_n0")).otherwise(None))
           .drop("rep_births_n0").sort(["n", "seed"]))
    cal.write_csv(out / "calib.csv")

    lo, hi = a.ticks * 4 // 5, a.ticks
    lines = [f"# E010 calibration: --transfer-pct N in {{{', '.join(map(str, ns))}}} and n0, seeds "
             f"{', '.join(map(str, seeds))}, {a.ticks:,} ticks, window {lo:,}-{hi:,}", "",
             "Replicator-class exact births per 1,000 ticks and as a share of n0's same-seed rate; living "
             "replicator-class bodies and population at the last census; foreign execution (deaths in the window; "
             "living at the last census); entered = replicator-class deaths with paid_for_others_m > 0; entry cost "
             "= median paid_for_others_m of entered replicator-class deaths (units) and median of its share of "
             "their spent_m; profit = sum gained_from_others_m / sum spent_m over non-replicator-class deaths; "
             f"pad = births of bodies <= {PAD_LEN} bytes; entered in the first and last patch (sink), with the "
             "number of replicator-class deaths there.", "",
             "| N | seed | rep births /1k | vs n0 | rep alive end | pop end | foreign (deaths) | foreign (census) "
             "| entered | entry cost (units) | cost / spent | profit | pad share | entered first patch | "
             "entered last patch |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in cal.iter_rows(named=True):
        lines.append(
            f"| {r['n']} | {r['seed']} | {f1(r['rep_births_per_1k'])} | {pct(r['rep_births_vs_n0'])} "
            f"| {f0(r['rep_alive_end'])} | {f0(r['pop_end'])} | {pct(r['foreign_deaths'])} "
            f"| {pct(r['foreign_census'])} | {pct(r['entered'])} | {f1(r['entry_cost_med'])} "
            f"| {pct(r['entry_cost_share_med'])} | {f2(r['profit'])} | {pct(r['pad_share'])} "
            f"| {pct(r['entered_first'])} ({r['n_first']}) | {pct(r['entered_last'])} ({r['n_last']}) |")
    lines += ["", "Medians over seeds:", "",
              "| N | rep births /1k | vs n0 | rep alive end | foreign (deaths) | entered | entry cost (units) "
              "| cost / spent | profit | pad share | entered first | entered last |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    med = lambda x, c: x[c].drop_nulls().median() if x[c].drop_nulls().len() else None
    for n in allns:
        x = cal.filter(pl.col("n") == n)
        lines.append(f"| {n} | {f1(med(x, 'rep_births_per_1k'))} | {pct(med(x, 'rep_births_vs_n0'))} "
                     f"| {f0(med(x, 'rep_alive_end'))} | {pct(med(x, 'foreign_deaths'))} | {pct(med(x, 'entered'))} "
                     f"| {f1(med(x, 'entry_cost_med'))} | {pct(med(x, 'entry_cost_share_med'))} "
                     f"| {f2(med(x, 'profit'))} | {pct(med(x, 'pad_share'))} | {pct(med(x, 'entered_first'))} "
                     f"| {pct(med(x, 'entered_last'))} |")
    bad = cal.filter(pl.col("paid_by_sum") != 0)
    lines += ["", f"paid_by_others_m summed over the window's deaths is 0 in "
                  f"{cal.height - bad.height} of {cal.height} runs (it must be 0 under the transfer).", ""]
    ref = stdout_line(out / "n0" / "s1.stdout", 20_000)
    if ref is not None:
        lines += [f"n0 seed 1 at tick 20,000: `{ref}` ({'equals' if ref == REF_20000 else 'DIFFERS from'} the "
                  "E007 reference line).", ""]
    rule_lines, chosen, second = arm_rule(cal, ns)
    lines += rule_lines
    text = "\n".join(lines)
    (out / "calib.md").write_text(text + "\n", encoding="utf-8", newline="")
    print(text)
    print(f"total {time.time() - t_all:.0f} s")


# ---- inject -------------------------------------------------------------------


def inj_dir(out: Path, rule: str, genome: str, seed: int) -> Path:
    return out / f"{rule}_{genome}" / f"s{seed}"


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


def analyse_inj(out: Path, n: int, genome: str, seed: int, ticks: int, inject: int
                ) -> tuple[list[dict], dict, list[dict], pl.DataFrame]:
    rule = rule_name(n)
    d = inj_dir(out, rule, genome, seed)
    run = load(d)
    check_rule(run, n)
    cfg = run.meta["config"]
    patch_size, n_patches = int(cfg["patch_size"]), int(cfg["world_size"]) // int(cfg["patch_size"])
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
            rule=rule, n=n, genome=genome, seed=seed, bin=k, tick_end=hi,
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
              .sort("tick").with_columns(rule=pl.lit(rule), n=pl.lit(n), genome=pl.lit(genome), seed=pl.lit(seed)))
    gt = living.filter(pl.col("test_alive") > ALIVE_MIN)
    final = int(run.orgs["tick"].max())
    end = orgs.filter(pl.col("tick") == final).with_columns(patch=pl.col("start") // patch_size)
    inj = (run.meta.get("injections") or [{}])[0]
    starts = inj.get("starts", [])
    post = [b for b in bins if b["tick_end"] > inject]
    shares = [b["test_share"] for b in post if b["test_share"] is not None]
    after = deaths.filter(pl.col("tick") > inject)
    dm = deaths_measures(after.filter(pl.col("class") == "replicator"), after.filter(pl.col("class") != "replicator"),
                         n_patches, patch_size)
    late_lo = ticks * 4 // 5
    summary = dict(
        rule=rule, n=n, genome=genome, seed=seed,
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
        final_pop=end.height,
        test_deaths=tdeaths.height,
        test_entered=int((tdeaths["paid_for_others_m"] > 0).sum()) if tdeaths.height else 0,
        rep_births_late=ex.filter((pl.col("tick") > late_lo) & (pl.col("tick") <= ticks)).height,
        rep_entered_post=dm["entered"],
        profit_post=dm["profit"],
        entry_cost_med_post=dm["entry_cost_med"],
        entry_cost_share_med_post=dm["entry_cost_share_med"],
        rep_deaths_post=dm["rep_deaths"],
        entered_first_post=dm["entered_first"], n_first_post=dm["n_first"],
        entered_last_post=dm["entered_last"], n_last_post=dm["n_last"],
        sink_alive_end=end.filter((pl.col("patch") == 0) | (pl.col("patch") == n_patches - 1)).height,
        sink_test_alive_end=end.filter(((pl.col("patch") == 0) | (pl.col("patch") == n_patches - 1))
                                       & pl.col("test")).height,
        sink_rep_alive_end=end.filter(((pl.col("patch") == 0) | (pl.col("patch") == n_patches - 1))
                                      & (pl.col("class") == "replicator")).height,
        paid_by_sum=int(deaths["paid_by_others_m"].sum()) if deaths.height else 0,
    )
    for k in (11, 12, 14, 17, 20):
        summary[f"share_b{k}"] = bins[k - 1]["test_share"] if k <= len(bins) else None
    return bins, summary, living.to_dicts(), tdeaths.select(
        pl.lit(rule).alias("rule"), pl.lit(n).alias("n"), pl.lit(genome).alias("genome"), pl.lit(seed).alias("seed"),
        "tick", "id", "age", "paid_for_others_m", "gained_from_others_m", "exact_children", "offspring")


def ratio(a: int | None, b: int | None) -> float | None:
    if a is None or b is None:
        return None
    if a == 0 and b == 0:
        return 1.0
    if min(a, b) == 0:
        return float("inf")
    return max(a, b) / min(a, b)


rs = lambda r: "–" if r is None else ("inf" if r == float("inf") else f"{r:.2f}")


def predictions(runs: pl.DataFrame, ns: list[int], seeds: list[int], inject: int, ticks: int) -> list[str]:
    def get(n, genome, seed, col):
        x = runs.filter((pl.col("n") == n) & (pl.col("genome") == genome) & (pl.col("seed") == seed))
        return x[col][0] if x.height else None

    def tick_s(n, genome, seed):
        t = get(n, genome, seed, "last_above_1pct")
        return "–" if t is None else (f">= {t:,} (not lost)" if get(n, genome, seed, "censored") else f"{t:,}")

    need = (len(seeds) * 2 + 2) // 3  # 2 of 3
    late_lo = ticks * 4 // 5
    lines = ["## Prediction checks", "",
             f"'last > 1%' = end tick of the last {FINE}-tick bin after the injection with the test share above "
             f"{pct(GONE)}; rates compared as ticks since the injection ({inject:,}). 'After the injection' = deaths "
             f"in ticks ({inject:,}, {ticks:,}]; late births = replicator-class exact births in ({late_lo:,}, "
             f"{ticks:,}].", ""]
    for n in [x for x in ns if x != 0]:
        # 1. World persists.
        ok1 = True
        cells = []
        for g in GENOMES:
            vals = []
            for s in seeds:
                a, b = get(n, g, s, "rep_births_late"), get(0, g, s, "rep_births_late")
                vals.append(a / b if (a is not None and b) else None)
            good = sum(1 for v in vals if v is not None and v >= BIRTHS_MIN)
            ok1 &= good == len(seeds)
            cells.append(f"{g} {', '.join(pct(v) for v in vals)} ({good} of {len(seeds)})")
        lines.append(f"1 (N = {n}). Late replicator-class births vs n0, same genome and seed, >= {pct(BIRTHS_MIN)} "
                     f"in 3 of 3 for every genome: {'; '.join(cells)}. {yn(ok1)}.")
        # 2. Entries common and profitable.
        ok2 = True
        cells = []
        for g in GENOMES:
            ent = [get(n, g, s, "rep_entered_post") for s in seeds]
            pro = [get(n, g, s, "profit_post") for s in seeds]
            ge = sum(1 for v in ent if v is not None and v >= ENTERED_MIN)
            gp = sum(1 for v in pro if v is not None and v > PROFIT_MIN)
            ok2 &= ge == len(seeds) and gp == len(seeds)
            cells.append(f"{g} entered {', '.join(pct(v) for v in ent)} ({ge} of {len(seeds)}), profit "
                         f"{', '.join(f2(v) for v in pro)} ({gp} of {len(seeds)})")
        lines.append(f"2 (N = {n}). Replicator-class deaths after the injection entered >= {pct(ENTERED_MIN)} and "
                     f"intruder profit > {PROFIT_MIN:g}, 3 of 3 each, every genome: {'; '.join(cells)}. {yn(ok2)}.")
        # 3. Eject maintained.
        later = 0
        cells = []
        for s in seeds:
            a, b = get(n, "eject", s, "last_above_1pct"), get(n, "inert", s, "last_above_1pct")
            w = a is not None and b is not None and a > b
            later += w
            cells.append(f"s{s} {tick_s(n, 'eject', s)} / {tick_s(n, 'inert', s)} ({'later' if w else 'not later'})")
        alive = [get(n, "eject", s, "alive_end") for s in seeds]
        n_alive = sum(1 for v in alive if v is not None and v >= 1)
        ok3 = later == len(seeds) and n_alive >= need
        costs = [v for g in GENOMES for s in seeds if (v := get(n, g, s, "entry_cost_med_post")) is not None]
        cm = sorted(costs)[len(costs) // 2] if costs else None
        lines.append(f"3 (N = {n}). Last > 1% eject / inert: {'; '.join(cells)}; eject later in {later} of "
                     f"{len(seeds)} [3 of 3]. Eject living at the end: {', '.join(f0(v) for v in alive)}, >= 1 in "
                     f"{n_alive} [>= {need}]. {yn(ok3)}. (Fail-branch comparison: median over runs of the median "
                     f"entry cost of entered replicator-class deaths after the injection {f1(cm)} units, against "
                     f"the six-byte cost of about {SIX_BYTE_COST} units.)")
        # 4. Trap a liability.
        nl = 0
        cells = []
        for s in seeds:
            a, b = get(n, "trap", s, "last_above_1pct"), get(n, "inert", s, "last_above_1pct")
            w = a is not None and b is not None and a <= b
            nl += w
            cells.append(f"s{s} {tick_s(n, 'trap', s)} / {tick_s(n, 'inert', s)} ({'not later' if w else 'later'})")
        lines.append(f"4 (N = {n}). Last > 1% trap / inert: {'; '.join(cells)}; trap not later in {nl} of "
                     f"{len(seeds)} [>= {need}]. {yn(nl >= need)}.")
    # 5. N = 0 reference.
    if 0 in ns:
        ok5 = True
        for g in ("eject", "trap"):
            rr = [ratio(get(0, g, s, "since_inject"), get(0, "inert", s, "since_inject")) for s in seeds]
            within = sum(1 for r in rr if r is not None and r <= RATE_FACTOR)
            ok5 &= within >= need
            lines.append(
                f"5 (n0, {g}). Last > 1% {g} / inert: "
                f"{'; '.join(f's{s} {tick_s(0, g, s)} / {tick_s(0, 'inert', s)}' for s in seeds)}; max/min of ticks "
                f"since injection {', '.join(rs(r) for r in rr)} [<= {RATE_FACTOR:g} in >= {need}: {within}].")
        lines.append(f"5. Both: {yn(ok5)}.")
    return lines


def pre_injection_checks(out: Path, cal_out: Path, ns: list[int], seeds: list[int], inject: int) -> list[str]:
    t = (inject - 1) // CENSUS * CENSUS  # last report line before the injection tick
    lines = [f"Pre-injection identity (report line at tick {t:,}):", ""]
    for n in ns:
        for s in seeds:
            got = {g: stdout_line(out / f"{rule_name(n)}_{g}" / f"s{s}.stdout", t) for g in GENOMES}
            vals = {v for v in got.values() if v is not None}
            cal = stdout_line(calib_dir(cal_out, n, s).parent / f"s{s}.stdout", t)
            same = len(vals) == 1 and None not in got.values()
            lines.append(f"- {rule_name(n)} s{s}: genomes {'identical' if same else 'DIFFER'}"
                         + ("" if cal is None else f"; calibration run {'equal' if same and cal in vals else 'DIFFERS'}")
                         + f" (`{next(iter(vals)) if vals else '–'}`)")
    if 0 in ns:
        line = stdout_line(out / f"{rule_name(0)}_{next(iter(GENOMES))}" / "s1.stdout", 20_000)
        if line is not None:
            lines.append(f"- n0 s1 at tick 20,000: `{line}` "
                         f"({'equals' if line == REF_20000 else 'DIFFERS from'} the E007 reference)")
    return lines


def summarize(bdf: pl.DataFrame, runs: pl.DataFrame, living: pl.DataFrame, tdeaths: pl.DataFrame,
              ns: list[int], seeds: list[int], ticks: int, inject: int, checks: list[str]) -> str:
    n_bins = ticks // BIN
    k0 = inject // BIN  # last pre-injection bin
    order = {g: i for i, g in enumerate(GENOMES)}
    rules = [rule_name(n) for n in ns]
    lines = [f"# E010a injection under the transfer: rules {', '.join(rules)} x {len(GENOMES)} genomes x seeds "
             f"{', '.join(map(str, seeds))}, {ticks:,} ticks, {COPIES} copies at {inject:,}, bins of {BIN:,}", ""]
    lines += checks + [""]
    lines += [
        f"Per run: copies placed, test share of replicator-class exact births in bin {k0} (pre-injection) and bins "
        f"{k0 + 1}–{n_bins}, end tick of the last {FINE}-tick bin above 1%, last census with > {ALIVE_MIN} living "
        "test bodies, living test bodies at the end, final population.", "",
        "| rule | genome | seed | placed | " + " | ".join(f"b{k}" for k in range(k0, n_bins + 1))
        + " | last > 1% | alive > 10 last | alive end | final pop |",
        "|---|---|---|---|" + "---|" * (n_bins - k0 + 1) + "---|---|---|---|",
    ]
    srt = runs.with_columns(o=pl.col("genome").replace_strict(order)).sort(["n", "o", "seed"])
    for r in srt.iter_rows(named=True):
        x = bdf.filter((pl.col("rule") == r["rule"]) & (pl.col("genome") == r["genome"]) & (pl.col("seed") == r["seed"])
                       & (pl.col("bin") >= k0)).sort("bin")
        sh = " | ".join(pct(v) for v in x["test_share"].to_list())
        t = r["last_above_1pct"]
        lines.append(f"| {r['rule']} | {r['genome']} | {r['seed']} | {r['placed']}/{r['copies']} | {sh} "
                     f"| {'>= ' if r['censored'] else ''}{t:,} | {f0(r['last_alive_gt10'])} | {r['alive_end']} "
                     f"| {r['final_pop']} |")
    lines += [
        "", "Per run, after the injection: replicator-class deaths entered (paid_for_others_m > 0), intruder profit "
        "(gained / spent over non-replicator-class deaths), median entry cost of entered replicator-class deaths "
        "(units, and share of their spent), late replicator-class exact births (last fifth of the run) and as a "
        "share of the n0 run with the same genome and seed; the sink: entered among replicator-class deaths with "
        "the body start in the first / last patch (count), living bodies there at the end (replicator-class, "
        "test genome).", "",
        "| rule | genome | seed | entered | profit | entry cost | cost / spent | late rep births | vs n0 "
        "| entered first patch | entered last patch | sink alive (rep, test) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    late0 = {(r["genome"], r["seed"]): r["rep_births_late"] for r in runs.filter(pl.col("n") == 0).iter_rows(named=True)}
    for r in srt.iter_rows(named=True):
        b0 = late0.get((r["genome"], r["seed"]))
        lines.append(
            f"| {r['rule']} | {r['genome']} | {r['seed']} | {pct(r['rep_entered_post'])} | {f2(r['profit_post'])} "
            f"| {f1(r['entry_cost_med_post'])} | {pct(r['entry_cost_share_med_post'])} | {f0(r['rep_births_late'])} "
            f"| {pct(r['rep_births_late'] / b0 if b0 else None)} "
            f"| {pct(r['entered_first_post'])} ({r['n_first_post']}) | {pct(r['entered_last_post'])} "
            f"({r['n_last_post']}) | {r['sink_alive_end']} ({r['sink_rep_alive_end']}, {r['sink_test_alive_end']}) |")
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
    for rule in rules:
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
        "(`paid_for_others_m` > 0), median `paid_for_others_m` of the entered (units), median age, mean exact "
        "children; and the same by seed (deaths, entered, age, children).", "",
        "| rule | genome | deaths | entered | entry cost | median age | mean exact children | by seed |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for rule in rules:
        for g in GENOMES:
            x = tdeaths.filter((pl.col("rule") == rule) & (pl.col("genome") == g))
            ent = x.filter(pl.col("paid_for_others_m") > 0)
            per = []
            for s in seeds:
                y = x.filter(pl.col("seed") == s)
                per.append(f"s{s} {y.height}, {pct(float((y['paid_for_others_m'] > 0).mean()) if y.height else None)}, "
                           f"{f0(y['age'].median() if y.height else None)}, "
                           f"{f1(y['exact_children'].mean() if y.height else None)}")
            lines.append(f"| {rule} | {g} | {x.height} "
                         f"| {pct(float((x['paid_for_others_m'] > 0).mean()) if x.height else None)} "
                         f"| {f1(float(ent['paid_for_others_m'].median()) / 1000 if ent.height else None)} "
                         f"| {f0(x['age'].median() if x.height else None)} "
                         f"| {f1(x['exact_children'].mean() if x.height else None)} | {'; '.join(per)} |")
    bad = runs.filter(pl.col("paid_by_sum") != 0)
    lines += ["", f"paid_by_others_m summed over all deaths is 0 in {runs.height - bad.height} of {runs.height} runs."]
    lines += [""] + predictions(runs, ns, seeds, inject, ticks)
    return "\n".join(lines)


def inject(a: argparse.Namespace) -> None:
    if not a.rules:
        raise SystemExit("inject needs --rules, e.g. --rules 0,150")
    out = a.out or OUT_INJ
    out.mkdir(parents=True, exist_ok=True)
    seeds = list(range(1, a.seeds + 1))
    ns = sorted(int(x) for x in a.rules.split(","))
    jobs = [(n, g, s) for n in ns for g in GENOMES for s in seeds]
    exe = binary()
    t_all = time.time()
    if not a.analyse_only:
        def go(j):
            n, g, s = j
            extra = ["--inject", f"{a.inject_tick}:{GENOMES[g]}:{COPIES}"]
            return run_world(exe, inj_dir(out, rule_name(n), g, s), s, a.ticks, rule_flags(n), extra, a.force)

        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(go, jobs):
                print(msg, flush=True)
        print(f"runs and classes: {time.time() - t_all:.0f} s", flush=True)

    def one(j):
        n, g, s = j
        return analyse_inj(out, n, g, s, a.ticks, a.inject_tick) \
            if (inj_dir(out, rule_name(n), g, s) / "classes.csv").exists() else None

    with ThreadPoolExecutor(min(a.jobs, 6)) as ex:
        results = [r for r in ex.map(one, jobs) if r is not None]
    bdf = pl.DataFrame([b for bins, _, _, _ in results for b in bins], infer_schema_length=None)
    runs = pl.DataFrame([s for _, s, _, _ in results], infer_schema_length=None)
    living = pl.DataFrame([x for _, _, lv, _ in results for x in lv], infer_schema_length=None)
    tdeaths = pl.concat([td for _, _, _, td in results], how="vertical_relaxed")
    bdf.write_csv(out / "bins.csv")
    runs.write_csv(out / "runs.csv")
    living.write_csv(out / "living.csv")
    tdeaths.write_csv(out / "deaths.csv")
    checks = pre_injection_checks(out, a.cal_out or OUT_CAL, ns, seeds, a.inject_tick)
    text = summarize(bdf, runs, living, tdeaths, ns, seeds, a.ticks, a.inject_tick, checks)
    (out / "summary.md").write_text(text + "\n", encoding="utf-8", newline="")
    print(text)
    print(f"total {time.time() - t_all:.0f} s")


def main() -> None:
    # The tables use en dashes; a Windows console would fail to print them.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("calibrate", "inject"):
        p = sub.add_parser(name)
        p.add_argument("--seeds", type=int, default=3)
        p.add_argument("--ticks", type=int, default=TICKS, help="override for smoke tests only")
        p.add_argument("--out", type=Path, default=None, help="output root (smoke tests only)")
        p.add_argument("--jobs", type=int, default=12)
        p.add_argument("--force", action="store_true")
        p.add_argument("--analyse-only", action="store_true")
    sub.choices["calibrate"].add_argument("--ns", default=",".join(map(str, CAL_NS)),
                                          help="transfer percentages besides the n0 reference")
    sub.choices["inject"].add_argument("--rules", help="comma-separated N, 0 = no flag (e.g. 0,150)")
    sub.choices["inject"].add_argument("--inject-tick", type=int, default=INJECT, help="override for smoke tests only")
    sub.choices["inject"].add_argument("--cal-out", type=Path, default=None,
                                       help="calibration root for the pre-injection check (smoke tests only)")
    a = ap.parse_args()
    calibrate(a) if a.cmd == "calibrate" else inject(a)


if __name__ == "__main__":
    main()
