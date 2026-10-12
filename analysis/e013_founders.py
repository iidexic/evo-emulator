"""E013: sixteen founders instead of one. Runs the standard world (the code
default, the E004 p512_far_prop_rot world that E007 ran) seeded with
sixteen copies of the ancestor instead of one (`--founder
13325271fc11401605086c5a1845486c11101c130d:16`, the ancestor with K = 64
and E = 16, 100 units each, founder j at 32,768 + 4,096 j mod 65,536: one
in every eighth patch), seeds 1-10 x 50,000 ticks, census every 500.
Records and classifies each run as E004/E007 did (default physics, which
is the world's), applies the E004 persistence and E005 parasite measures
and the E007 window measures for windows 1-2, and compares with E007
seeds 1-10 over the same ticks.

Usage (from analysis/):

    uv run e013_founders.py                  # build, check, run, classify, analyse
    uv run e013_founders.py --analyse-only   # runs exist; redo the tables
    uv run e013_founders.py --seeds 1 --ticks 2000 --out ../runs/e013/smoke  # smoke test only

Run directories: runs/e013/f16/s<seed>/. The earlier scripts are reused by
setting their globals (as e007_long_run.py does): e004_physics.run_one /
metrics / summarize (persistence), e005_parasites.run_all (parasites),
e007_long_run.windows / summarize_windows with e007.TICKS = 50,000
(windows 1-2, including the post-run columns genotypes_func,
top_func_share and the traits.py absorb_* / endow_* medians).

Added here:

- Absorb-count course: per 2,500-tick bin (bin k holds ticks
  ((k-1)*2,500, k*2,500]), over replicator-class exact births (child ==
  executor's body at `divide`, class of the child's genome from
  classes.csv) of 21-byte bodies, the median of byte 6 read as a signed
  byte, as encoded and with no guard check: the computation behind the
  E007 record's 72 / 96 / 112 / 120 (runs/e007_followup/early.py). Median
  per seed, then the median of those across seeds. The same code runs on
  E007 seeds 1-9 over ticks 0-50,000 (`control`). A second column gives
  the effective loop count of runs/e007_followup/k/analyse.py (`K`: byte
  5 a `lit`, byte 7 `absorb` and byte 8 `dec A` with a positive byte or
  `inc A` with a negative one, or the operand route where byte 6 doubles
  as the `absorb`; other bodies excluded); a robustness check only.
- Founder lineages: founders have ids 2-17 (checked against orgs.csv at
  tick 0 and meta.json). Every child gets its executor's founder,
  processing births.csv in (tick, child) order; a lineage is alive at a
  census tick when one of its organisms is in orgs.csv at that tick.
  Counted at every census (lineages.csv) and reported at 1,000, 5,000,
  25,000 and 50,000.
- Occupied patches at tick 1,000 (patches.csv rows with `orgs` > 0), the
  population there, and the first census tick with population (patches.csv
  `orgs` summed, equal to census.csv's counts) >= 900, for f16 and E007
  seeds 1-10.

Checks: before running, the binary must reproduce E007 seed 1's report
line at tick 20,000 with no flags (the line E010 checks); every f16 run's
meta.json must list the ancestor x 16 at the expected starts, and
orgs.csv at tick 0 must hold ids 2-17 there.

Output in runs/e013/: runs_e004.csv and summary_e004.md (persistence),
runs.csv, summary.md and f16_s<seed>_dependent.csv / _other_source.csv
(parasites), windows.csv and summary_windows.md (windows 1-2; E007's own
prediction lines are left out and its "after 200,000" column reads "after
25,000" here), absorb_course.csv (per arm, seed and bin), lineages.csv
(per seed and census tick), per_seed.csv (founder phase, both arms), and
summary_e013.md (the comparison and the prediction checks). Protocol and
predictions: docs/research/experiments/2026-10-12-e013-founders.md.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

import e004_physics as e004
import e005_parasites as e005
import e007_long_run as e007
from evo_run import HASH_COLS, ROOT, binary

OUT = ROOT / "runs" / "e013"
ARM = "f16"
ANCESTOR = "13325271fc11401605086c5a1845486c11101c130d"  # K = 64, E = 16 (genomes.csv)
FOUNDERS = 16
FIRST_ID = 2  # sim::FIRST_ID; founders are ids 2 .. 17
FLAGS = ["--founder", f"{ANCESTOR}:{FOUNDERS}"]
TICKS = 50_000
WINDOW = 25_000
BIN = 2_500
LEN = 21
LINEAGE_TICKS = (1_000, 5_000, 25_000, 50_000)
EARLY_TICK = 1_000
POP_MIN = 900
BAND = 0.10                    # prediction 2: +-10%
PAR_LO, PAR_HI = 0.001, 0.03   # prediction 2: parasite share 0.1-3%

E007_DIR = ROOT / "runs" / "e007"
E007_SEEDS = range(1, 11)
# The E007 record (2026-10-07-e007-long-run.md, "What the top hosts are").
RECORD_ABSORB = {2_500: 72, 5_000: 96, 10_000: 112, 25_000: 120}
RECORD_W2 = {"pop": 939, "rep_alive": 255}
# E007's seed-1 report line at tick 20,000 (no flags); E010 checks the same.
REF_20000 = "20000,953,536,27,21,20.7,50,238498,237546,879038,378839,127,242"

# Counts as integers; a median of an even number of seeds can end in .5 and
# keeps its decimal (E013: the f16 window-2 replicator-class median is 229.5).
f0 = lambda v: "–" if v is None else (f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}")
f1 = lambda v: "–" if v is None else f"{v:,.1f}"
f2 = lambda v: "–" if v is None else f"{v:.2f}"
f3 = lambda v: "–" if v is None else f"{v:.3f}"
pct = lambda v: "–" if v is None else f"{100 * v:.2f}%"
yn = lambda ok: "confirmed" if ok else "not confirmed"


def _med(s: pl.Series):
    s = s.drop_nulls()
    return s.median() if s.len() else None


def run_dir(seed: int) -> Path:
    return OUT / ARM / f"s{seed}"


# ---- checks -------------------------------------------------------------------


def check_reference(exe: Path) -> str:
    out = subprocess.run([str(exe), "--ticks", "20000", "--seed", "1", "--report", "500"],
                         capture_output=True, text=True, check=True).stdout
    line = next((x for x in out.splitlines() if x.startswith("20000,")), None)
    if line != REF_20000:
        raise SystemExit(f"binary does not reproduce E007 seed 1 at tick 20,000:\n got  {line}\n want {REF_20000}")
    return "reference check: the binary reproduces E007 seed 1's report line at tick 20,000"


def expected_starts(world_size: int) -> list[int]:
    return [(world_size // 2 + world_size * j // FOUNDERS) % world_size for j in range(FOUNDERS)]


def check_founders(seed: int) -> dict:
    """meta.json lists the ancestor x 16 at 32,768 + 4,096 j mod 65,536, and
    orgs.csv at tick 0 holds ids 2-17 there (id 2 + j at start j)."""
    d = run_dir(seed)
    meta = json.loads((d / "meta.json").read_text())
    ws = int(meta["config"]["world_size"])
    starts = expected_starts(ws)
    if ws != 65_536 or starts != [(32_768 + 4_096 * j) % 65_536 for j in range(FOUNDERS)]:
        raise SystemExit(f"{d}: world size {ws}, expected 65,536")
    if meta.get("founders") != [{"hex": ANCESTOR, "count": FOUNDERS}]:
        raise SystemExit(f"{d}: meta.json founders {meta.get('founders')}")
    if meta.get("founder_starts") != starts:
        raise SystemExit(f"{d}: meta.json founder_starts {meta.get('founder_starts')}, expected {starts}")
    o = (pl.scan_csv(d / "orgs.csv", schema_overrides={c: pl.Utf8 for c in HASH_COLS["orgs"]})
         .filter(pl.col("tick") == 0).select("id", "parent", "birth_tick", "start", "len").collect().sort("id"))
    want = pl.DataFrame({"id": list(range(FIRST_ID, FIRST_ID + FOUNDERS)), "start": starts})
    got = o.select("id", "start")
    if not got.equals(want.cast(got.schema)) or (o["parent"] != 0).any() or (o["len"] != LEN).any():
        raise SystemExit(f"{d}: orgs.csv at tick 0 is not ids 2-17 at the founder starts:\n{o}")
    return dict(seed=seed, ticks_run=meta["ticks_run"], git_commit=meta.get("git_commit"),
                git_dirty=meta.get("git_dirty"))


# ---- absorb-count course --------------------------------------------------------


def _ubyte(off: int) -> pl.Expr:
    return pl.col("bytes_hex").str.slice(2 * off, 2).str.to_integer(base=16, strict=False)


def _sbyte(off: int) -> pl.Expr:
    v = _ubyte(off)
    return pl.when(v >= 128).then(v - 256).otherwise(v)


def absorb_course(d: Path, max_tick: int) -> pl.DataFrame:
    """Per bin: n and median absorb count (byte 6, signed, as encoded; E007's
    early.py) over replicator-class exact births of 21-byte bodies up to
    `max_tick`, and the effective count K of k/analyse.py (n_K, K_med)."""
    b = (pl.scan_csv(d / "births.csv", schema_overrides={c: pl.Utf8 for c in HASH_COLS["births"]})
         .filter((pl.col("raw_hash") == pl.col("parent_now_hash")) & (pl.col("len") == LEN)
                 & (pl.col("tick") <= max_tick))
         .select("tick", "raw_hash").collect())
    cls = pl.scan_csv(d / "classes.csv", schema_overrides={"raw_hash": pl.Utf8}).select("raw_hash", "class")
    g = (pl.scan_csv(d / "genomes.csv", schema_overrides={c: pl.Utf8 for c in HASH_COLS["genomes"]})
         .select("raw_hash", "bytes_hex")
         .join(b.select("raw_hash").unique().lazy(), on="raw_hash", how="semi")
         .join(cls, on="raw_hash", how="left").collect())
    b5, b6, b7, b8 = _ubyte(5), _ubyte(6), _ubyte(7), _ubyte(8)
    k, lit5 = _sbyte(6), (b5 & 0x1F) == 17
    absorb7, op7, op6, op8 = (b7 & 0x1F) == 22, b7 & 0x1F, b6 & 0x1F, b8 & 0x1F
    g = g.with_columns(
        absorb=k,
        K=pl.when(lit5 & absorb7 & (op8 == 5) & (k > 0)).then(k)
        .when(lit5 & absorb7 & (op8 == 4) & (k < 0)).then(-k)
        .when(lit5 & (op7 == 5) & (op6 == 22) & (k > 0)).then(k)
        .when(lit5 & (op7 == 4) & (op6 == 22) & (k < 0)).then(-k),
    )
    x = (b.join(g, on="raw_hash", how="left").filter(pl.col("class") == "replicator")
         .with_columns(bin=((pl.col("tick") + BIN - 1) // BIN).cast(pl.Int64)))
    return (x.group_by("bin").agg(n=pl.len(), med=pl.col("absorb").median(),
                                  n_K=pl.col("K").is_not_null().sum(), K_med=pl.col("K").median())
            .with_columns(tick_end=pl.col("bin") * BIN).sort("bin"))


# ---- founder lineages and the founder phase ----------------------------------------


def lineages(seed: int) -> tuple[pl.DataFrame, int]:
    """Lineages alive per census tick, and the number of births whose executor
    had no founder (0 expected)."""
    d = run_dir(seed)
    b = pl.scan_csv(d / "births.csv").select("tick", "child", "executor").collect().sort("tick", "child")
    top = max(int(b["child"].max() or 0), FIRST_ID + FOUNDERS - 1)
    f = [0] * (top + 1)
    for i in range(FIRST_ID, FIRST_ID + FOUNDERS):
        f[i] = i
    orphans = 0
    for c, e in zip(b["child"].to_list(), b["executor"].to_list()):
        fe = f[e] if e < len(f) else 0
        orphans += fe == 0
        f[c] = fe
    fdf = pl.DataFrame({"id": list(range(top + 1)), "founder": f}, schema={"id": pl.Int64, "founder": pl.Int64})
    o = pl.scan_csv(d / "orgs.csv", schema_overrides={c: pl.Utf8 for c in HASH_COLS["orgs"]}).select("tick", "id").collect()
    o = o.with_columns(pl.col("id").cast(pl.Int64)).join(fdf, on="id", how="left")
    per = (o.group_by("tick").agg(
        pop=pl.len(),
        lineages=pl.col("founder").filter(pl.col("founder") > 0).n_unique(),
        unassigned=(pl.col("founder").fill_null(0) == 0).sum(),
        largest=pl.col("founder").filter(pl.col("founder") > 0).mode().first(),
    ).with_columns(seed=pl.lit(seed)).sort("tick"))
    return per.select("seed", "tick", "pop", "lineages", "largest", "unassigned"), orphans


def early(d: Path) -> dict:
    """Occupied patches and population at tick 1,000, first census tick with
    population >= 900. Population = sum of patches.csv `orgs` (living body
    starts), which equals census.csv's counts summed and, unlike census.csv,
    has rows when the world is empty."""
    p = pl.read_csv(d / "patches.csv")
    at = p.filter(pl.col("tick") == EARLY_TICK)
    pop = p.group_by("tick").agg(pop=pl.col("orgs").sum()).sort("tick")
    reached = pop.filter(pl.col("pop") >= POP_MIN)["tick"]
    return dict(
        patches_1000=at.filter(pl.col("orgs") > 0).height if at.height else None,
        pop_1000=int(at["orgs"].sum()) if at.height else None,
        first_900=int(reached.min()) if reached.len() else None,
    )


# ---- summary -----------------------------------------------------------------------


def course_by_tick(df: pl.DataFrame, seeds: list[int]) -> pl.DataFrame:
    x = df.filter(pl.col("seed").is_in(seeds))
    return x.group_by("tick_end").agg(
        med=pl.col("med").median(), lo=pl.col("med").min(), hi=pl.col("med").max(),
        n_seeds=pl.len(), K_med=pl.col("K_med").median(),
    ).sort("tick_end")


def summary(persist: pl.DataFrame, wdf: pl.DataFrame, course: pl.DataFrame, per_seed: pl.DataFrame,
            lin: pl.DataFrame, orphans: dict[int, int], checks: list[dict], ticks: int) -> str:
    surv = sorted(persist.filter(pl.col("replicating"))["seed"].to_list())
    n_all = persist.height
    e7p = pl.read_csv(E007_DIR / "runs_e004.csv")
    e7_surv = sorted(e7p.filter(pl.col("replicating"))["seed"].to_list())
    e7w = pl.read_csv(E007_DIR / "windows.csv", schema_overrides={"top_hash": pl.Utf8, "top_par_hash": pl.Utf8,
                                                                 "top_func_hash": pl.Utf8})
    e7w = e7w.filter(pl.col("window") <= 2)
    wcols = ["pop", "rep_alive", "patches", "exact_share", "genotypes", "genotypes_func", "top_func_share",
             "top_share", "par_share", "dep_share", "tramp_share", "resistance", "absorb_med", "absorb_ge96",
             "endow_med", "endow_ge37"]

    def wmed(df, seeds, w, col):
        return _med(df.filter(pl.col("seed").is_in(seeds) & (pl.col("window") == w))[col])

    commits = sorted({(c["git_commit"], c["git_dirty"]) for c in checks})
    lines = [
        f"# E013 summary: sixteen founders (f16) against E007 seeds 1–10, {ticks:,} ticks",
        "",
        f"Arm f16: `--founder {ANCESTOR}:{FOUNDERS}`, seeds {', '.join(str(s) for s in persist['seed'].to_list())}, "
        f"{ticks:,} ticks, census every {e004.CENSUS}. Binary {', '.join(f'{c} (dirty {d})' for c, d in commits)}. "
        f"Checks: meta.json lists the ancestor x {FOUNDERS} at 32,768 + 4,096 j mod 65,536 and orgs.csv at tick 0 "
        f"holds ids 2–17 at those starts in {len(checks)} of {n_all} runs; births whose executor had no founder: "
        f"{sum(orphans.values())}.",
        "",
        f"f16 medians are over the {len(surv)} seeds replicating at the end ({', '.join(map(str, surv))}); E007 "
        f"medians over seeds {', '.join(map(str, e7_surv))} (seed 10 died at tick 1,179), read from "
        "runs/e007/windows.csv (windows 1–2 of the 250,000-tick runs, which are ticks 0–50,000).",
        "",
        "## Windows 1–2, medians over seeds",
        "",
        "| measure | f16 w1 | E007 w1 | f16 w2 | E007 w2 | f16 w2 / E007 w2 |",
        "|---|---|---|---|---|---|",
    ]
    fmt = {"pop": f0, "rep_alive": f0, "patches": f0, "genotypes": f0, "genotypes_func": f0, "absorb_med": f0,
           "endow_med": f0, "par_share": pct, "resistance": f2}
    for c in wcols:
        fm = fmt.get(c, f3)
        a1, b1 = wmed(wdf, surv, 1, c), wmed(e7w, e7_surv, 1, c)
        a2, b2 = wmed(wdf, surv, 2, c), wmed(e7w, e7_surv, 2, c)
        ratio = a2 / b2 if (a2 is not None and b2) else None
        lines.append(f"| {c} | {fm(a1)} | {fm(b1)} | {fm(a2)} | {fm(b2)} | {f3(ratio)} |")

    # Per-seed tables.
    e7_seed = {r["seed"]: r for r in e7w.filter(pl.col("window") == 2).iter_rows(named=True)}
    f_seed = {r["seed"]: r for r in wdf.filter(pl.col("window") == 2).iter_rows(named=True)}
    rep = {r["seed"]: r["replicating"] for r in persist.iter_rows(named=True)}
    e7rep = {r["seed"]: r["replicating"] for r in e7p.iter_rows(named=True)}
    lines += [
        "",
        "## Per seed, window 2 (ticks 25,000–50,000; population and replicator-class bodies at the last census)",
        "",
        "| seed | f16 replicating at end | E007 replicating | f16 population | E007 population "
        "| f16 replicator-class | E007 replicator-class | f16 canonical genotypes (>= 2 exact) | E007 canonical genotypes "
        "| f16 top canonical share | E007 top canonical share | f16 parasite share | E007 parasite share "
        "| f16 absorb median | E007 absorb median |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in sorted(set(f_seed) | set(e7_seed)):
        a, b_ = f_seed.get(s, {}), e7_seed.get(s, {})
        lines.append(
            f"| {s} | {'yes' if rep.get(s) else 'no'} | {'yes' if e7rep.get(s) else 'no'} "
            f"| {f0(a.get('pop'))} | {f0(b_.get('pop'))} | {f0(a.get('rep_alive'))} | {f0(b_.get('rep_alive'))} "
            f"| {f0(a.get('genotypes_func'))} | {f0(b_.get('genotypes_func'))} "
            f"| {f3(a.get('top_func_share'))} | {f3(b_.get('top_func_share'))} "
            f"| {pct(a.get('par_share'))} | {pct(b_.get('par_share'))} "
            f"| {f0(a.get('absorb_med'))} | {f0(b_.get('absorb_med'))} |"
        )

    ps = {(r["arm"], r["seed"]): r for r in per_seed.iter_rows(named=True)}
    lt = {(r["seed"], r["tick"]): r for r in lin.iter_rows(named=True)}
    one_tick = {s: (lin.filter((pl.col("seed") == s) & (pl.col("lineages") == 1))["tick"].min()) for s in rep}
    lines += [
        "",
        f"## Per seed, founder phase (f16 lineages: founders with living descendants at the census tick)",
        "",
        f"| seed | f16 patches occupied at {EARLY_TICK:,} | E007 patches at {EARLY_TICK:,} "
        f"| f16 population at {EARLY_TICK:,} | E007 population at {EARLY_TICK:,} "
        f"| f16 first census with population >= {POP_MIN} | E007 first census >= {POP_MIN} "
        + "".join(f"| f16 lineages at {t:,} " for t in LINEAGE_TICKS)
        + "| f16 first census with one lineage | f16 founder of the most bodies at the end |",
        "|" + "---|" * (8 + len(LINEAGE_TICKS)),
    ]
    for s in sorted({k[1] for k in ps}):
        a, b_ = ps.get((ARM, s), {}), ps.get(("e007", s), {})
        lins = "".join(f"| {f0(lt[(s, t)]['lineages']) if (s, t) in lt else '–'} " for t in LINEAGE_TICKS)
        end = lin.filter(pl.col("seed") == s).sort("tick").tail(1)
        largest = end["largest"][0] if end.height else None
        lines.append(
            f"| {s} | {f0(a.get('patches_1000'))} | {f0(b_.get('patches_1000'))} "
            f"| {f0(a.get('pop_1000'))} | {f0(b_.get('pop_1000'))} "
            f"| {f0(a.get('first_900')) if a.get('first_900') is not None else 'never'} "
            f"| {f0(b_.get('first_900')) if b_.get('first_900') is not None else 'never'} "
            f"{lins}| {f0(one_tick.get(s)) if one_tick.get(s) is not None else '–'} | {largest if largest is not None else '–'} |"
        )
    fs = per_seed.filter((pl.col("arm") == ARM) & pl.col("seed").is_in(surv))
    es = per_seed.filter(pl.col("arm") == "e007")
    es9 = es.filter(pl.col("seed").is_in(e7_surv))
    med_lin = {t: _med(lin.filter((pl.col("tick") == t) & pl.col("seed").is_in(surv))["lineages"]) for t in LINEAGE_TICKS}
    lines.append(
        f"| median ({len(surv)} f16 / {len(e7_surv)} E007 seeds) | {f0(_med(fs['patches_1000']))} "
        f"| {f0(_med(es9['patches_1000']))} | {f0(_med(fs['pop_1000']))} | {f0(_med(es9['pop_1000']))} "
        f"| {f0(_med(fs['first_900']))} | {f0(_med(es9['first_900']))} "
        + "".join(f"| {f1(med_lin[t])} " for t in LINEAGE_TICKS) + "| | |"
    )

    # Absorb-count course.
    cf = course_by_tick(course.filter(pl.col("arm") == ARM), surv)
    ce = course_by_tick(course.filter(pl.col("arm") == "e007"), e7_surv)
    cj = cf.join(ce, on="tick_end", how="full", suffix="_e7", coalesce=True).sort("tick_end")
    lines += [
        "",
        "## Absorb-count course",
        "",
        "Median absorb count (byte 6, signed, as encoded) over replicator-class exact births of 21-byte bodies per "
        f"2,500-tick bin, per seed, then the median across seeds (f16: {len(surv)} seeds; E007: seeds "
        f"{', '.join(map(str, e7_surv))}, recomputed here from runs/e007/std/ with the same code, ticks 0–50,000). "
        "Range = min–max of the per-seed medians. The last two columns are the effective loop count K of "
        "runs/e007_followup/k/analyse.py (dec / inc / operand routes; other bodies excluded), a robustness check.",
        "",
        "| bin end | f16 median | f16 range | f16 seeds | E007 median | E007 range | E007 seeds | E007 record "
        "| f16 K median | E007 K median |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in cj.iter_rows(named=True):
        t = r["tick_end"]
        lines.append(
            f"| {t:,} | {f1(r['med'])} | {f1(r['lo'])}–{f1(r['hi'])} | {r['n_seeds'] or 0} "
            f"| {f1(r['med_e7'])} | {f1(r['lo_e7'])}–{f1(r['hi_e7'])} | {r['n_seeds_e7'] or 0} "
            f"| {RECORD_ABSORB.get(t, '')} | {f1(r['K_med'])} | {f1(r['K_med_e7'])} |"
        )

    # Prediction checks.
    n_rep = len(surv)
    p1 = n_rep == n_all == 10
    p2_rows, p2_ok = [], True
    for c, label in (("pop", "population at the last census"), ("rep_alive", "replicator-class bodies"),
                     ("genotypes_func", "canonical genotypes with >= 2 exact births")):
        a, b_ = wmed(wdf, surv, 2, c), wmed(e7w, e7_surv, 2, c)
        ok = a is not None and b_ is not None and abs(a - b_) <= BAND * b_
        p2_ok &= ok
        p2_rows.append(f"{label} {f0(a)} against {f0(b_)} ({'+' if a is not None and b_ and a >= b_ else ''}"
                       f"{f1(100 * (a / b_ - 1)) if (a is not None and b_) else '–'}%, band {f0((1 - BAND) * b_)}–"
                       f"{f0((1 + BAND) * b_)}: {'in' if ok else 'out'}"
                       f"{', on the boundary' if ok and abs(abs(a - b_) - BAND * b_) < 1e-9 else ''})")
    par2 = wmed(wdf, surv, 2, "par_share")
    par_ok = par2 is not None and PAR_LO <= par2 <= PAR_HI
    par_seeds = wdf.filter(pl.col("seed").is_in(surv) & (pl.col("window") == 2))["par_share"]
    par_in = int(((par_seeds >= PAR_LO) & (par_seeds <= PAR_HI)).sum())
    p2_ok &= par_ok
    e7_pop2, e7_rep2 = wmed(e7w, e7_surv, 2, "pop"), wmed(e7w, e7_surv, 2, "rep_alive")
    get = lambda df, t, col: (df.filter(pl.col("tick_end") == t)[col][0] if df.filter(pl.col("tick_end") == t).height else None)
    p3_parts, p3_own, p3_rec = [], True, True
    for t in (5_000, 10_000):
        a, own, rec = get(cf, t, "med"), get(ce, t, "med"), RECORD_ABSORB[t]
        ok_own = a is not None and own is not None and a >= own
        ok_rec = a is not None and a >= rec
        p3_own &= ok_own
        p3_rec &= ok_rec
        p3_parts.append(f"tick {t:,}: f16 {f1(a)} against E007 {f1(own)} (recomputed; {'>=' if ok_own else '<'}) "
                        f"and {rec} (record; {'>=' if ok_rec else '<'})")
    lines += [
        "",
        "## Prediction checks",
        "",
        f"1. Every seed persists (replicating at tick {ticks:,}, the E004 measure: replicator-class exact births in "
        f"the last {e004.LATE_WINDOW:,} ticks, in 10 of 10): {n_rep} of {n_all}. **{yn(p1)}** "
        f"(E004/E007: 9 of 10).",
        f"2. Window 2 medians within ±{100 * BAND:.0f}% of E007's window 2 medians over seeds "
        f"{e7_surv[0]}–{e7_surv[-1]} (E007 from windows.csv: population {f0(e7_pop2)}, replicator-class "
        f"{f0(e7_rep2)}; the record says {RECORD_W2['pop']} and {RECORD_W2['rep_alive']}): "
        + "; ".join(p2_rows)
        + f"; parasite share of exact births, window 2 median {pct(par2)} "
        f"({'in' if par_ok else 'out of'} {pct(PAR_LO)}–{pct(PAR_HI)}; {par_in} of {len(surv)} seeds in range "
        f"individually). **{yn(p2_ok)}**.",
        f"3. Absorb sweep no slower (across-seed median absorb count at ticks 5,000 and 10,000 at least E007's): "
        + "; ".join(p3_parts)
        + f". **{yn(p3_own and p3_rec)}**"
        + ("" if p3_own == p3_rec else
           f" (against the recomputed control: {yn(p3_own)}; against the record's 96 and 112: {yn(p3_rec)})")
        + ".",
    ]

    # Exploratory item 4.
    end_tick = max(t for t in LINEAGE_TICKS if t <= ticks) if any(t <= ticks for t in LINEAGE_TICKS) else None
    end_one = int(lin.filter((pl.col("tick") == end_tick) & (pl.col("lineages") == 1)).height) if end_tick else 0
    rng = lambda s: f"{f0(s.min())}–{f0(s.max())}" if s.drop_nulls().len() else "–"
    lin_txt = []
    for t in LINEAGE_TICKS:
        x = lin.filter(pl.col("tick") == t)["lineages"]
        if x.len():
            lin_txt.append(f"{t:,}: median {f1(_med(x))}, range {rng(x)}")
    f_all = per_seed.filter(pl.col("arm") == ARM)
    lines += [
        f"4. Exploratory. Founder lineages with living descendants ({f_all.height} f16 seeds) at "
        + "; ".join(lin_txt)
        + f". Seeds ending with one lineage (at {f0(end_tick)}): {end_one} of {f_all.height}. Occupied patches at "
        f"tick {EARLY_TICK:,}: f16 {rng(f_all['patches_1000'])} (median {f0(_med(f_all['patches_1000']))}), E007 "
        f"seeds 1–10 {rng(es['patches_1000'])} (median of seeds 1–9 {f0(_med(es9['patches_1000']))}; the E007 "
        f"follow-up at K = 64, one founder: 87–95). First census with population >= {POP_MIN}: f16 "
        f"{rng(f_all['first_900'])} (median {f0(_med(f_all['first_900']))}; never in "
        f"{int(f_all['first_900'].is_null().sum())}), E007 {rng(es9['first_900'])} (median of seeds 1–9 "
        f"{f0(_med(es9['first_900']))}; never in {int(es['first_900'].is_null().sum())} of {es.height}).",
    ]
    return "\n".join(lines)


def windows_text(wdf: pl.DataFrame, persist: pl.DataFrame) -> str:
    """e007.summarize_windows for windows 1-2, without E007's prediction lines."""
    lines = e007.summarize_windows(wdf, persist).splitlines()
    i = lines.index("Prediction checks:")
    j = next(k for k in range(i, len(lines)) if lines[k].startswith("Added after the run"))
    lines = lines[:i] + lines[j:]
    n_w = int(wdf["window"].max())
    out = []
    for x in lines:
        x = x.replace("E007 windows:", f"E013 {ARM} windows (E007 measures):")
        x = x.replace("(top host changes, of 9)", f"(top host changes, of {n_w - 1})")
        x = x.replace("Added after the run (not pre-registered): canonical genotypes and two trait bytes.",
                      "Canonical genotypes and two trait bytes (E007's post-run columns; part of E013's measures).")
        out.append(x)
    return "\n".join(out)


def main() -> None:
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--ticks", type=int, default=TICKS)
    ap.add_argument("--jobs", type=int, default=4, help="parallel simulation + classify jobs")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT, help="output root (smoke tests)")
    a = ap.parse_args()
    OUT = a.out.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = list(range(1, a.seeds + 1))

    e004.OUT = OUT
    e004.ARMS = {ARM: FLAGS}
    exe = binary()
    # Pin the binary for the rest of the run: e005.run_all would call
    # cargo build again, and other work may be editing the tree meanwhile.
    e005.binary = lambda: exe
    t0 = time.time()
    if not a.analyse_only:
        print(check_reference(exe), flush=True)
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda s: e004.run_one(exe, ARM, s, a.ticks, a.force), seeds):
                print(msg, flush=True)
        print(f"runs and classes: {time.time() - t0:.0f} s", flush=True)

    # The harness physics is the world's physics, so classes_world.csv (which
    # E005's analysis reads) is a copy of classes.csv, as in E007.
    for s in seeds:
        d = run_dir(s)
        if (d / "classes.csv").exists() and not (d / "classes_world.csv").exists():
            shutil.copyfile(d / "classes.csv", d / "classes_world.csv")
    done = [s for s in seeds if (run_dir(s) / "classes.csv").exists()]
    checks = [check_founders(s) for s in done]
    print(f"founder check: {len(checks)} of {len(done)} runs ok", flush=True)

    t1 = time.time()
    rows = [e004.metrics(ARM, s, a.ticks) for s in done]
    persist = pl.DataFrame(rows)
    persist.write_csv(OUT / "runs_e004.csv")
    text = e004.summarize(a.seeds, a.ticks, [ARM]).replace("E004 summary", "E013 persistence (E004 measures)")
    (OUT / "summary_e004.md").write_text(text + "\n", encoding="utf-8")
    print(text, flush=True)

    e005.RUNS = OUT
    e005.OUT = OUT
    e005.ARMS = {ARM: []}
    e005.run_all([ARM], a.seeds, 2, host=True)

    e007.OUT = OUT
    e007.ARM = ARM
    e007.TICKS = 2 * WINDOW  # windows 1-2
    e007.LATE_FROM = WINDOW  # the per-seed table's "first born after" column
    wrows = []
    for s in done:
        if (OUT / f"{ARM}_s{s}_dependent.csv").exists():
            wrows += e007.windows(s, exe)
            print(f"{ARM}/s{s}: windows done", flush=True)
    wdf = pl.DataFrame(wrows)
    wdf.write_csv(OUT / "windows.csv")
    text = windows_text(wdf, persist)
    (OUT / "summary_windows.md").write_text(text + "\n", encoding="utf-8")
    print(text, flush=True)

    # Absorb course, f16 and E007 seeds 1-9 (same code, ticks 0 .. run length).
    crow = []
    for s in done:
        crow.append(absorb_course(run_dir(s), a.ticks).with_columns(arm=pl.lit(ARM), seed=pl.lit(s)))
    e7_surv = pl.read_csv(E007_DIR / "runs_e004.csv").filter(pl.col("replicating"))["seed"].to_list()
    for s in e7_surv:
        crow.append(absorb_course(E007_DIR / "std" / f"s{s}", a.ticks).with_columns(arm=pl.lit("e007"), seed=pl.lit(s)))
        print(f"e007/s{s}: absorb course done", flush=True)
    course = pl.concat(crow).select("arm", "seed", "bin", "tick_end", "n", "med", "n_K", "K_med")
    course.write_csv(OUT / "absorb_course.csv")

    # Lineages and the founder phase.
    lin_rows, orphans = [], {}
    for s in done:
        per, orphans[s] = lineages(s)
        lin_rows.append(per)
    lin = pl.concat(lin_rows)
    lin.write_csv(OUT / "lineages.csv")
    prow = []
    for s in done:
        r = dict(arm=ARM, seed=s, **early(run_dir(s)))
        for t in LINEAGE_TICKS:
            x = lin.filter((pl.col("seed") == s) & (pl.col("tick") == t))["lineages"]
            r[f"lineages_{t}"] = int(x[0]) if x.len() else None
        prow.append(r)
    for s in E007_SEEDS:
        prow.append(dict(arm="e007", seed=s, **early(E007_DIR / "std" / f"s{s}"),
                         **{f"lineages_{t}": None for t in LINEAGE_TICKS}))
    per_seed = pl.DataFrame(prow, schema_overrides={f"lineages_{t}": pl.Int64 for t in LINEAGE_TICKS})
    per_seed.write_csv(OUT / "per_seed.csv")

    text = summary(persist, wdf, course, per_seed, lin, orphans, checks, a.ticks)
    (OUT / "summary_e013.md").write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"analysis: {time.time() - t1:.0f} s", flush=True)


if __name__ == "__main__":
    main()
