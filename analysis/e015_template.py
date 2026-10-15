"""E015: a template-addressed ancestor (H17). Spec: docs/tasks/T03-template-ancestor.md
section 4; record docs/research/experiments/2026-10-13-e015-template-ancestor.md.

The template ancestor (`--ancestor tierra`, `sim::ancestor_t(127, 16)`, 41
bytes) enters its copy procedure by `searchf` on a label and returns by
`searchb` to its start label, so a body whose procedure label is broken by
one substitution finds a neighbour's procedure instead: Tierra's parasite,
one mutation away. The spec's body had five-nop labels (45 bytes); it pays
for itself at no K a `lit` byte holds, and the T03 branch's first fix
(four-nop labels) was applied, which pays at K = 127 and no lower step
(sim.rs, `ancestor_t`).

Stages (subcommands):

- `nbhd` (stage 1): the single-mutant neighbourhoods of `ancestor(64, 16)`
  (`std`) and `ancestor_t(127, 16)` (`tierra`), `evo-core --neighbours HEX`
  with the unmutated body as host, 3,000 harness ticks, default physics.
  Writes runs/e015/nbhd/<name>.csv and <name>.stdout (the binary's summary),
  and runs/e015/nbhd/summary.md: label counts, and every `parasite_jump`
  row grouped by position with the ancestor's instruction there, the
  mutant ops and the entry offsets.
- `gate` (stage 2, the persistence gate): `--ancestor tierra`, 10 seeds,
  50,000 ticks, the standard world (no physics flag), one founder,
  `--census 500`, classified with the default physics. Pass: replicator-
  class bodies (harness class of the current body) alive at tick 50,000 in
  >= 8 of 10 seeds (E004's criterion). Runs go to runs/e015/world/tierra/
  s<seed>, with the same command line as stage 3's tierra arm, so they are
  its first ten seeds. Writes runs/e015/world/gate.csv and gate.md. If it
  fails, the protocol's first and only knob is K (no K above 127 fits a
  `lit` byte, so that knob is spent), then `--sun` as a declared arm change.
  Gate arms added after the gate failed (`gate --arm NAME`, directories
  runs/e015/world/<arm>/s<seed>, outputs gate_<arm>.csv and .md):
  `tierra_quiet` (noise off: `--p 0 --rot 0`), `tierra_sun2` and
  `tierra_sun3` (`--sun 2`, `--sun 3`, noise on; the choice of N is in
  GATE_ARMS's comment). These four, and the registered `tierra` gate, are
  the world before T08 (2026-10-13), which fixed the `alloc`/`copy` range
  edge; they now carry `--legacy-pending-range`, which reproduces it bit for
  bit (their runs were made before the flag existed, and their meta.json
  has no `legacy_pending_range` key, which `check_meta` reads as the legacy
  world). T08's baseline arms, under the fixed edge: `std_fix` (`--ancestor
  std`), `std_fix_sun2` (`--ancestor std --sun 2`), `tierra_fix` and
  `tierra_fix_sun2` (`--ancestor tierra`, without and with `--sun 2`). Each
  gate summary also has stage 3's per-bin measures on its runs
  (gate[_<arm>]_bins.csv, _runs.csv), the per-run summary (parasite share in
  the last bin, entered and resident shares after 25,000), the edge
  signature (births with `copy_errors` 0 whose `raw_hash` differs from
  `parent_now_hash`: under the legacy edge, children that lost their first
  bytes; with slips 0, and with the difference confined to bytes 0-2), and
  the profile of replicator-class deaths (median age, share with no child,
  share of absorbs short, mean ration).
- `world` (stage 3, the comparison): `tierra` against `std`, 30 seeds each,
  50,000 ticks, one founder (as E007), `--census 500`, classified. Not run
  until the gate passes (the runner refuses unless `--force-world`).
  Directories runs/e015/world/<arm>/s<seed>. As coded (the registered
  design) its `tierra` arm is the gate's ten legacy seeds plus twenty more,
  and its `std` arm is the default physics, which since T08 is the fixed
  edge; the runner refuses to compare arms under different edges. Stage 3
  under the fixed edge, with a same-sun std control, is folded into E016's
  cost-off arms (docs/research/experiments/2026-10-13-e016-defence-search.md).
  Per 2,500-tick bin (bin k
  holds ticks ((k-1)*2500, k*2500]) and per run:
  - `par_share`: E005's parasite-lineage share of exact births (exact: the
    child equals the executor's body at `divide`). Parasite genomes, over
    the whole run, are E005's `parasite_2` test as E007 used it: >= 2 exact
    births in the run, harness class not `replicator`, median
    `exec_foreign / executed` > 0.25 over carriers with >= 2 children (the
    "two children" rule), generation depth >= 5 (a chain of exact births of
    the genome each by an executor itself born so), and here also exact
    births by >= 2 distinct executors (implied by depth >= 5; checked).
  - `entered_share`: replicator-class deaths (class of the birth genome)
    with `exec_by_others` > 0 (T02's counter).
  - `resident_share`: deaths with `executed` > 0 whose `exec_foreign /
    executed` > 0.9; and `resident_intr_share`, the same over deaths with
    `exec_foreign` > 0 (E014's reading).
  - `ip_off_share`: at the bin's last census, living bodies whose IP is
    outside their own body (`ip_off` >= `len`).
  - `nop_share`: at the bin's last census, the share of living bodies'
    bytes (from world.bin, at each body's start and length) that decode as
    `nop0` or `nop1` (Amoeba's 25% warning line; the tierra ancestor is
    16 of 41 = 39% nops, the std ancestor none).
  - `len_p10`, `len_p50`, `len_p90`: living body lengths at that census.
  - T05's `measures.compute` per run (QNN and tree measures; RUN_DIR/
    measures/), unless `--no-measures`.
  Predictions (H17, T03 section 4), checked on the world stage: parasite
  share in the last bin (ticks 47,500-50,000) > 5% in >= 20 of 30 tierra
  seeds, and <= 2% in >= 20 of 30 std seeds; entered share of replicator-
  class deaths in ticks (25,000, 50,000] above 25% for tierra and 7-14% for
  std (medians over seeds). The neighbourhood clause ("at least one
  `parasite_jump` row for ancestor_t and none for ancestor") is read in
  stage 1's summary.

Disk: every file but patches.csv and meta.json is gzipped after the run is
classified (evo_run.gzip_verified; evo_run.load reads .gz), as E014.

The binary is `--evo-bin`, else $EVO_BIN, else evo-core/target/release/
evo-core(.exe), which is not built here: build first (`cargo build
--release` in evo-core/, or with CARGO_TARGET_DIR and point --evo-bin at
it). The runner checks that the binary's `std` and `tierra` ancestors are
the bodies above (a one-tick run, read back from meta.json).

Usage (from analysis/):

    uv run e015_template.py nbhd --threads 12
    uv run e015_template.py gate --jobs 6
    uv run e015_template.py gate --analyse-only
    uv run e015_template.py gate --arm std_fix_sun2 --jobs 12    # T08's baseline arms
    uv run e015_template.py world --jobs 6 --force-world     # only after the gate passes
    EVO_BIN=../evo-core/target/t03/release/evo-core.exe uv run e015_template.py gate
    uv run e015_template.py gate --seeds 2 --ticks 3000 --out ../runs/e015-smoke   # smoke test
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import polars as pl

from evo_run import CORE, ROOT, gunzip_verified, gzip_verified, load, world

OUT = ROOT / "runs" / "e015"
HEX = {
    "std": "13325271fc11401605086c5a1845486c11101c130d",  # sim::ancestor(64, 16)
    "tierra": "0101030351fc117f1605084c0a010301036d030103011332525a71fc1845486c11101c0b030301016d",  # ancestor_t(127, 16)
}
ARM_FLAGS = {"std": [], "tierra": ["--ancestor", "tierra"]}
ARMS = ["std", "tierra"]
# T08 (2026-10-13): a write into the executor's own pending region passes the
# range check, so a child at the backward locality edge no longer keeps stale
# first bytes. The flag restores the world every run before it was made in.
LEGACY = "--legacy-pending-range"
# Gate arms. `tierra` is the registered gate; the next three were added after
# it failed (docs/tasks/README.md, "E015 persistence and world"); all four
# were run before T08 and carry LEGACY. The `_fix` arms are T08's baseline
# under the fixed edge (T08 section 4). Physics flags only (the run adds
# `--ancestor <base(arm)>`); `--classify` gets the same flags (the harness
# ignores the noise ones; `--sun` and LEGACY act on it).
# - tierra_quiet: no write flips, no copy slips, no bit rot (`--p 0` sets
#   both write probabilities, `--rot 0` bit rot): E005's quiet world but for
#   debris decay, which has no flag and changes no byte (it relabels debris
#   as free, and every op treats the two alike; it only draws from the PRNG).
# - tierra_sun2, tierra_sun3: the registered next knob, `--sun N` (patch
#   income and cap times N), noise on. `--sun` does not move the body's
#   break-even ration (the share of a full ration at which a cycle pays:
#   95.61% at every N, 92.34% for the 21-byte body; the ration at a full pool
#   is 8 units whatever the sun). It moves the load a patch carries at that
#   ration: a patch whose bodies would draw D units per tick at a full ration
#   settles at the share income / D, so it carries D* = income / break-even.
#   The 21-byte body at sun 1: 256 / 0.9234 = 277.2 units per tick, 7.04
#   bodies at 39.38 each; this body at sun N: 256 N / 0.9561 = 267.8 N, 6.59 N
#   bodies at 40.64 each. Equal at N = 1.068; `--sun` is a whole number, so 2,
#   then 3 if 2 fails. (2026-10-13: sun 2 passed 10 of 10; sun 3 not run.)
GATE_ARMS = {
    "tierra": [LEGACY],
    "tierra_quiet": ["--p", "0", "--rot", "0", LEGACY],
    "tierra_sun2": ["--sun", "2", LEGACY],
    "tierra_sun3": ["--sun", "3", LEGACY],
    "std_fix": [],
    "std_fix_sun2": ["--sun", "2"],
    "tierra_fix": [],
    "tierra_fix_sun2": ["--sun", "2"],
}


def base(arm: str) -> str:
    """The ancestor an arm seeds (`std` or `tierra`): the name up to the
    first underscore."""
    return arm.split("_")[0]


for _arm, _flags in GATE_ARMS.items():
    ARM_FLAGS[_arm] = ["--ancestor", base(_arm), *_flags]


TICKS = 50_000
CENSUS = 500
BIN = 2_500
HARNESS_TICKS = 3_000
GATE_SEEDS, GATE_NEED = 10, 8
WORLD_SEEDS = 30
LATE_WINDOW = 5_000  # E004's "replicating at the end": exact births by replicator-class parents
SECOND_HALF = 25_000  # entered / resident shares are read over deaths after this tick
RESIDENT = 0.9
PAR_HI, STD_LO = 0.05, 0.02  # prediction thresholds
ENTER_T, ENTER_STD = 0.25, (0.07, 0.14)
COMPRESS = ("births.csv", "deaths.csv", "orgs.csv", "census.csv", "world.bin", "genomes.csv", "classes.csv")
LABELS = ["replicator", "parasite_fallthrough", "parasite_jump", "one_shot", "inexact", "loafer", "dies"]
NOP0, NOP1 = 1, 3


# ---- binary --------------------------------------------------------------------

def evo_bin(path: str | Path | None = None) -> Path:
    """`path`, else $EVO_BIN, else the release binary in evo-core/target
    (not built here)."""
    p = path or os.environ.get("EVO_BIN")
    if p:
        p = Path(p)
    else:
        p = next((CORE / "target" / "release" / n for n in ("evo-core.exe", "evo-core")
                  if (CORE / "target" / "release" / n).exists()), CORE / "target" / "release" / "evo-core")
    if not p.exists():
        raise SystemExit(f"evo-core binary not found: {p} (build it, or give --evo-bin / EVO_BIN)")
    return p


def check_binary(exe: Path) -> None:
    """The binary's seeded ancestors must be the bodies in HEX (a T03 binary
    with K = 127 as tierra's default)."""
    with tempfile.TemporaryDirectory(prefix="e015_") as tmp:
        for arm in ARMS:
            d = Path(tmp) / arm
            subprocess.run([str(exe), "--ticks", "1", "--out", str(d), *ARM_FLAGS[arm]],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            meta = json.loads((d / "meta.json").read_text())
            got = meta["founders"][0]["hex"]
            if meta.get("ancestor") != arm or got != HEX[arm]:
                raise SystemExit(f"{exe}: --ancestor {arm} seeds {got} (meta ancestor {meta.get('ancestor')}); "
                                 f"expected {HEX[arm]}")


def disasm(exe: Path, hx: str) -> str:
    return subprocess.run([str(exe), "--disasm", hx], capture_output=True, text=True, check=True).stdout.strip()


# ---- stage 1: neighbourhoods ---------------------------------------------------------

def run_nbhd(exe: Path, out: Path, threads: int, ticks: int, force: bool) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for arm in ARMS:
        csv = out / f"{arm}.csv"
        if csv.exists() and not force:
            print(f"nbhd {arm}: exists", flush=True)
            continue
        t0 = time.time()
        cmd = [str(exe), "--neighbours", HEX[arm], "--harness-ticks", str(ticks), "--threads", str(threads),
               "--neighbours-out", str(csv)]
        r = subprocess.run(cmd, capture_output=True, text=True, check=True)
        (out / f"{arm}.stdout").write_text(r.stdout + r.stderr, encoding="utf-8", newline="")
        print(f"nbhd {arm}: {time.time() - t0:.1f} s; {r.stderr.strip()}", flush=True)


def instr_at(body: bytes, pos: int, exe: Path, cache: dict) -> str:
    """The instruction covering byte `pos` of `body` in a linear parse from
    byte 0 (a `lit` operand byte reports its `lit`)."""
    key = (body, pos)
    if key not in cache:
        i = 0
        while i < len(body):
            n = 2 if (body[i] & 0x1F) == 17 else 1
            if i <= pos < i + n:
                cache[key] = disasm(exe, body[i:i + n].hex()) + (" (operand)" if pos > i else "")
                break
            i += n
    return cache[key]


def summarize_nbhd(exe: Path, out: Path, ticks: int) -> str:
    lines = ["# E015 stage 1: single-mutant neighbourhoods", "",
             "Every substitution and deletion of each ancestor, alone and immediately before the unmutated "
             f"ancestor, {ticks:,} quiet harness ticks, default physics (`evo-core --neighbours`). "
             "Labels per `harness::label` (docs/instrumentation.md).", ""]
    frames = {}
    for arm in ARMS:
        p = out / f"{arm}.csv"
        if p.exists():
            frames[arm] = pl.read_csv(p, schema_overrides={"hex": pl.Utf8, "raw_hash": pl.Utf8, "func_hash": pl.Utf8})
    if not frames:
        return "\n".join(lines + ["No neighbourhood files."])
    lines += ["| label | " + " | ".join(frames) + " |", "|---|" + "---|" * len(frames)]
    counts = {a: dict(df.group_by("label").len().iter_rows()) for a, df in frames.items()}
    for lab in LABELS:
        lines.append(f"| {lab} | " + " | ".join(f"{counts[a].get(lab, 0):,}" for a in frames) + " |")
    lines.append("| mutants | " + " | ".join(f"{df.height:,}" for df in frames.values()) + " |")
    cache: dict = {}
    for arm, df in frames.items():
        anc = bytes.fromhex(HEX[arm])
        j = df.filter(pl.col("label") == "parasite_jump")
        lines += ["", f"## {arm}: `parasite_jump` rows by position ({j.height})", ""]
        if not j.height:
            lines.append("None.")
            continue
        lines += ["| pos | ancestor there | rows | subs | dels | entry offsets (count) | exact before host | host alive | mutant ops (subs) |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for pos in sorted(j["pos"].unique().to_list()):
            x = j.filter(pl.col("pos") == pos)
            ent = x.group_by("entry_off").len().sort("entry_off")
            ents = ", ".join(f"{e} ({n})" for e, n in ent.iter_rows())
            subs = x.filter(pl.col("kind") == "sub")
            ops: dict[str, int] = {}
            for v in subs["byte"].to_list():
                mutant = anc[:pos] + bytes([int(v)]) + anc[pos + 1:]
                op = instr_at(mutant, pos, exe, cache)
                ops[op] = ops.get(op, 0) + 1
            opstr = "; ".join(f"{o} x{n}" for o, n in sorted(ops.items(), key=lambda t: -t[1])[:6])
            if len(ops) > 6:
                opstr += f"; ... ({len(ops)} distinct)"
            lines.append(f"| {pos} | `{instr_at(anc, pos, exe, cache)}` | {x.height} | {subs.height} "
                         f"| {x.height - subs.height} | {ents} | {x['exact_host'].min()}-{x['exact_host'].max()} "
                         f"| {x['host_alive'].mean():.2f} | {opstr} |")
        f = df.filter(pl.col("label") == "parasite_fallthrough")
        fp = f.group_by("pos").len().sort("pos")
        lines += ["", f"{arm} `parasite_fallthrough` rows by position: "
                  + (", ".join(f"{p} ({n})" for p, n in fp.iter_rows()) or "none") + "."]
    t = frames.get("tierra")
    s = frames.get("std")
    if t is not None and s is not None:
        tj = t.filter(pl.col("label") == "parasite_jump").height
        sj = s.filter(pl.col("label") == "parasite_jump").height
        lines += ["", f"H17 neighbourhood clause (at least one `parasite_jump` row for ancestor_t, none for "
                  f"ancestor): tierra {tj}, std {sj}: first part {'holds' if tj else 'fails'}, second part "
                  f"{'holds' if sj == 0 else 'fails'}."]
    return "\n".join(lines)


# ---- world runs -------------------------------------------------------------------------

def run_dir(out: Path, arm: str, seed: int) -> Path:
    return out / "world" / arm / f"s{seed}"


def has(d: Path, name: str) -> bool:
    return (d / name).exists() or (d / f"{name}.gz").exists()


def commands(exe: Path, d: Path, arm: str, seed: int, ticks: int) -> tuple[list[str], list[str]]:
    run = [str(exe), "--ticks", str(ticks), "--seed", str(seed), "--report", str(CENSUS), "--census", str(CENSUS),
           "--out", str(d), *ARM_FLAGS[arm]]
    cls = [str(exe), "--classify", str(d), "--harness-ticks", str(HARNESS_TICKS), *GATE_ARMS.get(arm, [])]
    return run, cls


def run_one(exe: Path, out: Path, arm: str, seed: int, ticks: int, force: bool, compress: bool) -> str:
    d = run_dir(out, arm, seed)
    tag = f"{arm}/s{seed}"
    if not force and has(d, "classes.csv"):
        if compress and any((d / n).exists() for n in COMPRESS):
            for n in COMPRESS:
                if (d / n).exists():
                    gzip_verified(d / n)
            return f"{tag}: done; compressed"
        return f"{tag}: done"
    run, cls = commands(exe, d, arm, seed, ticks)
    t0 = time.time()
    if force or not has(d, "genomes.csv"):
        if d.exists():
            shutil.rmtree(d)
        d.parent.mkdir(parents=True, exist_ok=True)
        with open(d.parent / f"s{seed}.stdout", "w", encoding="utf-8", newline="") as f:
            subprocess.run(run, stdout=f, stderr=subprocess.DEVNULL, check=True)
    if not (d / "genomes.csv").exists():
        gunzip_verified(d / "genomes.csv.gz")
    t1 = time.time()
    subprocess.run(cls, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    msg = f"{tag}: run {t1 - t0:.0f} s, classify {time.time() - t1:.0f} s"
    if compress:
        a = b = 0
        for n in COMPRESS:
            if (d / n).exists():
                x, y = gzip_verified(d / n)
                a, b = a + x, b + y
        msg += f", gzip {a / 1e6:.1f} -> {b / 1e6:.1f} MB"
    return msg


def check_meta(run, arm: str) -> None:
    """The run seeded the arm's ancestor under the arm's physics (sun, noise
    and the `alloc`/`copy` edge as its flags say). A meta.json with no
    `legacy_pending_range` key is from before T08, so the legacy world."""
    m, b = run.meta, base(arm)
    if m.get("ancestor") != b or m["founders"][0]["hex"] != HEX[b]:
        raise SystemExit(f"{run.dir}: meta.json ancestor {m.get('ancestor')}, founder {m['founders'][0]['hex']}; "
                         f"expected {b} {HEX[b]}")
    flags = GATE_ARMS.get(arm, [])
    sun = int(flags[flags.index("--sun") + 1]) if "--sun" in flags else 1
    c = m["config"]
    quiet = "--p" in flags
    legacy = LEGACY in flags
    ok = (int(c["patch_income"]) == 256_000 * sun and int(c["patch_cap"]) == 4_096_000 * sun
          and (float(c["p_write_flip"]) == 0.0) == quiet and (float(c["q_slip"]) == 0.0) == quiet
          and (float(c["p_bit_rot"]) == 0.0) == quiet
          and bool(c.get("legacy_pending_range", True)) == legacy)
    if not ok:
        raise SystemExit(f"{run.dir}: meta.json config does not match arm {arm} (sun {sun}, quiet {quiet}, "
                         f"legacy edge {legacy}; meta legacy_pending_range {c.get('legacy_pending_range', 'absent')})")


# ---- stage 2: the persistence gate -------------------------------------------------------

def gate_row(out: Path, arm: str, seed: int, ticks: int) -> dict:
    run = load(run_dir(out, arm, seed))
    check_meta(run, arm)
    final = int(run.orgs["tick"].max()) if run.orgs.height else 0
    alive = run.class_of(run.orgs.filter(pl.col("tick") == final), "now_hash")
    cen = run.class_of(run.orgs, "now_hash").filter(pl.col("class") == "replicator")
    exact = run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash"))
    late = run.class_of(exact.filter(pl.col("tick") > ticks - LATE_WINDOW), "parent_now_hash", "pclass")
    pops = dict(run.orgs.group_by("tick").len().iter_rows())
    rep_alive_end = int((alive["class"] == "replicator").sum()) if final == ticks else 0
    row = dict(
        seed=seed, final_tick=final, extinct=alive.height == 0 or final < ticks,
        pop_end=alive.height if final == ticks else 0, rep_alive_end=rep_alive_end,
        passed=rep_alive_end > 0,
        late_exact_rep=int((late["pclass"] == "replicator").sum()),
        last_rep_census=int(cen["tick"].max()) if cen.height else -1,
        births=run.births.height, exact_births=exact.height,
        last_birth=int(run.births["tick"].max()) if run.births.height else -1,
    )
    for t in range(5_000, ticks + 1, 5_000):
        row[f"pop_{t // 1000}k"] = pops.get(t, 0)
    return row


def summarize_gate(rows: list[dict], ticks: int, seeds: list[int], arm: str = "tierra") -> str:
    df = pl.DataFrame(rows).sort("seed")
    n = df.height
    passed = int(df["passed"].sum())
    need = math.ceil(GATE_NEED * len(seeds) / GATE_SEEDS)
    verdict = "passes" if passed >= need else "fails"
    pop_cols = [c for c in df.columns if c.startswith("pop_") and c.endswith("k")]
    flags = " ".join(ARM_FLAGS[arm])
    k = 127 if base(arm) == "tierra" else 64
    lines = [f"# E015 persistence gate, arm `{arm}` (`{flags}`; K = {k}, E = 16), {n} seeds, {ticks:,} ticks", "",
             f"Pass: replicator-class bodies (harness class of the current body) alive at tick {ticks:,} in >= {need} "
             f"of {len(seeds)} seeds (E004's criterion; 8 of 10 scaled). **{passed} of {n}: the gate {verdict}.**", "",
             "Per seed: last census with a living body, replicator-class bodies alive at the run's end, last census with a "
             f"replicator-class body, exact births by replicator-class parents in the last {LATE_WINDOW:,} ticks "
             "(E004's `replicating`), births, exact births, last birth tick, and the population every 5,000 ticks.", "",
             "| seed | last census with life | pop at tick end | rep alive at tick end | last rep census | late exact (rep) | births | exact | last birth |"
             + "".join(f" {c[4:]} |" for c in pop_cols),
             "|---|---|---|---|---|---|---|---|---|" + "---|" * len(pop_cols)]
    for r in df.iter_rows(named=True):
        lines.append(f"| {r['seed']} | {r['final_tick']:,} | {r['pop_end']} | {r['rep_alive_end']} | "
                     f"{r['last_rep_census']:,} | {r['late_exact_rep']} | {r['births']:,} | {r['exact_births']:,} | "
                     f"{r['last_birth']:,} |" + "".join(f" {r[c]} |" for c in pop_cols))
    return "\n".join(lines)


def gate_detail(out: Path, arm: str, seeds: list[int], ticks: int, bin_size: int, name: str) -> list[str]:
    """For a gate arm: stage 3's per-bin measures on its runs (medians over
    seeds; written to <name>_bins.csv and <name>_runs.csv), and the profile of
    replicator-class deaths (class of the birth genome): count, median age,
    share with no child, and the share of absorbs short of a full ration
    (sum `absorb_short` / sum `absorbs`), over all ticks and over the first
    5,000."""
    res = [analyse_world(out, arm, s, ticks, bin_size, False) for s in seeds
           if has(run_dir(out, arm, s), "classes.csv")]
    wd = out / "world"
    bdf = pl.DataFrame([b for bins, _ in res for b in bins], infer_schema_length=None)
    pl.DataFrame([s for _, s in res], infer_schema_length=None).write_csv(wd / f"{name}_runs.csv")
    bdf.write_csv(wd / f"{name}_bins.csv")
    pct = lambda v: "–" if v is None else f"{100 * v:.1f}%"
    f0 = lambda v: "–" if v is None else f"{v:,.0f}"
    med = lambda x, c: x[c].drop_nulls().median() if x[c].drop_nulls().len() else None
    lines = ["", f"Per {bin_size:,}-tick bin, over the {len(res)} seeds: seeds with exact births; medians of exact births, "
             "parasite-lineage share of exact births (E007's `parasite_2` set per run; min-max over seeds with exact "
             "births), entered share of replicator-class deaths (`exec_by_others` > 0; replicator-class deaths in the "
             "bin), living bodies, IP off own body, nop share of living bytes, body length p10/p50.", "",
             "| ticks | seeds with exact births | exact | parasite share (min-max) | entered (rep deaths) | living | IP off body | nop share | len p10/p50 |",
             "|---|---|---|---|---|---|---|---|---|"]
    for k in sorted(bdf["bin"].unique().to_list()):
        x = bdf.filter(pl.col("bin") == k)
        p = x["par_share"].drop_nulls()
        rng = f" ({pct(p.min())}-{pct(p.max())})" if p.len() else ""
        lines.append(f"| {(k - 1) * bin_size:,}-{k * bin_size:,} | {int((x['exact'] > 0).sum())} | {f0(med(x, 'exact'))} "
                     f"| {pct(med(x, 'par_share'))}{rng} | {pct(med(x, 'entered_share'))} ({f0(med(x, 'rep_deaths'))}) "
                     f"| {f0(med(x, 'pop'))} | {pct(med(x, 'ip_off_share'))} | {pct(med(x, 'nop_share'))} "
                     f"| {f0(med(x, 'len_p10'))}/{f0(med(x, 'len_p50'))} |")
    rdf = pl.DataFrame([s for _, s in res], infer_schema_length=None)
    pct2 = lambda v: "–" if v is None else f"{100 * v:.2f}%"

    def mm(c: str, f=pct) -> str:
        x = rdf[c].drop_nulls() if c in rdf.columns else pl.Series([], dtype=pl.Float64)
        return "–" if not x.len() else f"{f(x.median())} ({f(x.min())}-{f(x.max())})"

    par_hi = int((rdf["par_share_last"].fill_null(0) > PAR_HI).sum()) if rdf.height else 0
    ent_hi = int((rdf["entered_share_post"].fill_null(0) > ENTER_T).sum()) if rdf.height else 0
    lines += ["", f"Per run, median (min-max) over the {rdf.height} seeds: parasite-lineage share of exact births in the "
              f"last bin (and seeds above {pct(PAR_HI)}), entered share of replicator-class deaths after {SECOND_HALF:,} "
              f"(and seeds above {pct(ENTER_T)}), resident share after {SECOND_HALF:,} of deaths that ran and of "
              "intruder deaths (`exec_foreign / executed` > 0.9).", "",
              "| parasite share, last bin | seeds > 5% | entered after 25,000 | seeds > 25% | resident (deaths that ran) "
              "| resident (intruder deaths) |", "|---|---|---|---|---|---|",
              f"| {mm('par_share_last')} | {par_hi} | {mm('entered_share_post')} | {ent_hi} "
              f"| {mm('resident_share_post')} | {mm('resident_intr_share_post')} |"]
    tot = lambda c: int(rdf[c].sum()) if c in rdf.columns and rdf.height else 0
    pooled = lambda c: pct2(tot(c) / tot("births_all")) if tot("births_all") else "–"
    lines += ["", "Edge signature (T08): births with `copy_errors` 0 whose `raw_hash` differs from `parent_now_hash`, "
              "as a share of all births; then those with no slip either, and of those the ones that differ from the "
              "parent's body only in bytes 0-2 (same length, longer than 3 bytes: the legacy edge's footprint; the "
              "rest of the signature is mostly bodies that copy a shifted or partial region every time). Pooled over "
              "seeds, then "
              "the per-seed median (min-max).", "",
              "| births | edge signature | no slip | bytes 0-2 only |", "|---|---|---|---|",
              f"| {tot('births_all'):,} | {pooled('edge_sig')}; {mm('edge_sig_share', pct2)} "
              f"| {pooled('edge_sig_noslip')}; {mm('edge_sig_noslip_share', pct2)} "
              f"| {pooled('edge_sig_head')}; {mm('edge_sig_head_share', pct2)} |"]
    parts = []
    for s in seeds:
        d = run_dir(out, arm, s)
        if has(d, "classes.csv"):
            run = load(d)
            parts.append(run.class_of(run.deaths, "birth_hash").filter(pl.col("class") == "replicator")
                         .select("tick", "age", "offspring", "absorbs", "absorb_short", "absorb_gain_m"))
    dd = pl.concat(parts) if parts else None
    lines += ["", "Replicator-class deaths (class of the birth genome), seeds pooled: count, median age, share with no "
              "child, share of their absorbs short of a full ration (any pool below its cap counts, under the "
              "proportional rule), and their mean ration as a share of a full one (sum `absorb_gain_m` / sum "
              "`absorbs` / 8,000; the ancestor breaks even at about "
              f"{'95.6' if base(arm) == 'tierra' else '92.3'}% in the harness).", "",
              "| ticks | deaths | median age | no child | absorbs short | mean ration |", "|---|---|---|---|---|---|"]
    for lab, x in (("0-2,500", dd.filter(pl.col("tick") <= 2_500) if dd is not None else None),
                   ("0-5,000", dd.filter(pl.col("tick") <= 5_000) if dd is not None else None), ("all", dd)):
        if x is None or not x.height:
            lines.append(f"| {lab} | 0 | – | – | – | – |")
            continue
        n_abs = max(1, x["absorbs"].sum())
        lines.append(f"| {lab} | {x.height:,} | {x['age'].median():,.0f} | {pct((x['offspring'] == 0).mean())} "
                     f"| {pct(x['absorb_short'].sum() / n_abs)} | {pct(x['absorb_gain_m'].sum() / n_abs / 8_000)} |")
    return lines


# ---- stage 3: the world comparison --------------------------------------------------------

def parasite_genomes(run) -> tuple[set[str], pl.DataFrame]:
    """E005's `parasite_2` set over the whole run (module docstring)."""
    exact = run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash"))
    per_g = exact.group_by("raw_hash").agg(n=pl.len(), executors=pl.col("executor").n_unique()).filter(pl.col("n") >= 2)
    per_g = run.class_of(per_g, "raw_hash").filter(pl.col("class") != "replicator")
    cand = set(per_g["raw_hash"].to_list())
    if not cand:
        return set(), per_g
    # Exact-birth generation depth (E005's generation_depth): the longest
    # chain of exact births of h whose executor was itself born by an exact
    # birth of h, as a tree depth over those links (T09 §5).
    from measures import _jump
    rows = exact.filter(pl.col("raw_hash").is_in(list(cand))).select("raw_hash", "child", "executor") \
        .with_row_index("i")
    link = rows.join(rows.select("raw_hash", pl.col("child").alias("executor"), pl.col("i").alias("up")),
                     on=["raw_hash", "executor"], how="left", maintain_order="left")
    m = rows.height
    nxt = np.append(link["up"].fill_null(m).to_numpy().astype(np.int64), m)  # row m: the root
    chain = _jump(nxt, (np.arange(m + 1) < m).astype(np.int64))[:m]
    best = dict(rows.with_columns(d=pl.Series(chain)).group_by("raw_hash")
                .agg(pl.col("d").max()).iter_rows())
    final = int(run.orgs["tick"].max()) if run.orgs.height else -1
    cols = ["birth_hash", "executed", "exec_foreign", "offspring"]
    carriers = pl.concat([run.deaths.select(cols), run.orgs.filter(pl.col("tick") == final).select(cols)]) \
        .filter((pl.col("executed") > 0) & (pl.col("offspring") >= 2)) \
        .group_by("birth_hash").agg(foreign_med_2=(pl.col("exec_foreign") / pl.col("executed")).median())
    fm = dict(carriers.iter_rows())
    per_g = per_g.with_columns(
        depth=pl.col("raw_hash").replace_strict(best, default=0, return_dtype=pl.Int64),
        foreign_med_2=pl.col("raw_hash").replace_strict(fm, default=None, return_dtype=pl.Float64))
    par = per_g.filter((pl.col("depth") >= 5) & (pl.col("foreign_med_2") > 0.25) & (pl.col("executors") >= 2))
    return set(par["raw_hash"].to_list()), par


def edge_signature(run) -> dict:
    """T08 section 4: births with `copy_errors` 0 whose `raw_hash` differs from
    `parent_now_hash`, a child that differs from its parent's body with no
    recorded copy error. Under the legacy `alloc`/`copy` edge these are
    mostly children placed at the backward locality edge, whose first bytes
    (1 for std, 3 for tierra) the copy loop could not write. Also counted:
    those with no slip either (a slip shifts or skips bytes and is not a copy
    error), and of those the ones whose difference from the parent's body is
    confined to bytes 0-2, same length and longer than 3 bytes (the edge's
    footprint; bit rot in the pending region or in the parent's body during
    the copy, the other quiet source, lands anywhere, but also lands there).
    Most of the signature in these worlds is neither: bodies that copy a
    shifted or partial region of themselves, or free memory, every time
    (deterministic inexact copiers), so the bytes 0-2 column is the one that
    tracks the edge. Shares are of all births."""
    b = run.births
    sig = b.filter((pl.col("copy_errors") == 0) & (pl.col("raw_hash") != pl.col("parent_now_hash")))
    noslip = sig.filter(pl.col("slips") == 0)
    hx = dict(run.genomes.select("raw_hash", "bytes_hex").iter_rows())
    head = 0
    for c, p, k in noslip.group_by("raw_hash", "parent_now_hash").len().iter_rows():
        cb, pb = hx.get(c), hx.get(p)
        # bytes_hex has two digits per byte, so bytes 3 on start at digit 6.
        if cb is not None and pb is not None and len(cb) == len(pb) > 6 and cb[6:] == pb[6:]:
            head += k
    n = b.height
    share = lambda x: x / n if n else None
    return dict(births_all=n, edge_sig=sig.height, edge_sig_share=share(sig.height),
                edge_sig_noslip=noslip.height, edge_sig_noslip_share=share(noslip.height),
                edge_sig_head=head, edge_sig_head_share=share(head))


def nop_share(run, w: dict, tick: int) -> float | None:
    """Share of living bodies' bytes at census `tick` that decode as a nop."""
    snap = w.get(tick)
    o = run.orgs.filter(pl.col("tick") == tick).select("start", "len")
    if snap is None or not o.height:
        return None
    n = snap.bytes.size
    idx = np.concatenate([np.arange(s, s + ln) % n for s, ln in o.iter_rows()])
    op = snap.bytes[idx] & 0x1F
    return float(np.isin(op, (NOP0, NOP1)).mean())


def analyse_world(out: Path, arm: str, seed: int, ticks: int, bin_size: int, measures: bool) -> tuple[list[dict], dict]:
    d = run_dir(out, arm, seed)
    run = load(d)
    check_meta(run, arm)
    par, par_df = parasite_genomes(run)
    binx = lambda c: ((pl.col(c) + bin_size - 1) // bin_size).cast(pl.Int64)
    ex = run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash")).with_columns(
        bin=binx("tick"), par=pl.col("raw_hash").is_in(list(par)))
    deaths = run.class_of(run.deaths, "birth_hash").with_columns(
        bin=binx("tick"), entered=pl.col("exec_by_others") > 0,
        resident=(pl.col("executed") > 0) & (pl.col("exec_foreign") > RESIDENT * pl.col("executed")))
    rep = deaths.filter(pl.col("class") == "replicator")
    ran = deaths.filter(pl.col("executed") > 0)
    intr = deaths.filter(pl.col("exec_foreign") > 0)
    orgs = run.orgs.with_columns(off=pl.col("ip_off") >= pl.col("len"))
    w = world(d)
    by = lambda df, key: {r[key]: r for r in df.iter_rows(named=True)}
    eb = by(ex.group_by("bin").agg(exact=pl.len(), par_share=pl.col("par").mean()), "bin")
    rb = by(rep.group_by("bin").agg(rep_deaths=pl.len(), entered_share=pl.col("entered").mean()), "bin")
    ab = by(ran.group_by("bin").agg(resident_share=pl.col("resident").mean()), "bin")
    ib = by(intr.group_by("bin").agg(resident_intr_share=pl.col("resident").mean()), "bin")
    cb = by(orgs.group_by("tick").agg(pop=pl.len(), ip_off_share=pl.col("off").mean(),
                                      len_p10=pl.col("len").quantile(0.1, "linear"),
                                      len_p50=pl.col("len").median(),
                                      len_p90=pl.col("len").quantile(0.9, "linear")), "tick")
    bins = []
    for k in range(1, ticks // bin_size + 1):
        hi = k * bin_size
        e, r, a, i, c = eb.get(k, {}), rb.get(k, {}), ab.get(k, {}), ib.get(k, {}), cb.get(hi, {})
        bins.append(dict(arm=arm, seed=seed, bin=k, tick_end=hi, exact=e.get("exact", 0),
                         par_share=e.get("par_share"), rep_deaths=r.get("rep_deaths", 0),
                         entered_share=r.get("entered_share"), resident_share=a.get("resident_share"),
                         resident_intr_share=i.get("resident_intr_share"), pop=c.get("pop", 0),
                         ip_off_share=c.get("ip_off_share"), nop_share=nop_share(run, w, hi),
                         len_p10=c.get("len_p10"), len_p50=c.get("len_p50"), len_p90=c.get("len_p90")))
    late = lambda df: df.filter(pl.col("tick") > SECOND_HALF)
    final = int(run.orgs["tick"].max()) if run.orgs.height else 0
    pshares = [b["par_share"] for b in bins if b["par_share"] is not None]
    s = dict(arm=arm, seed=seed, final_tick=final, pop_end=cb.get(final, {}).get("pop", 0),
             par_genomes=len(par), par_share_last=bins[-1]["par_share"] if bins else None,
             par_share_max=max(pshares) if pshares else None,
             entered_share_post=late(rep)["entered"].mean() if late(rep).height else None,
             resident_share_post=late(ran)["resident"].mean() if late(ran).height else None,
             resident_intr_share_post=late(intr)["resident"].mean() if late(intr).height else None,
             ip_off_share_post=late(orgs)["off"].mean() if late(orgs).height else None,
             nop_share_end=bins[-1]["nop_share"] if bins else None,
             len_p50_end=bins[-1]["len_p50"] if bins else None,
             **edge_signature(run))
    if measures:
        try:
            import measures as t05
            series, summ = t05.compute(run)
            md = d / "measures"
            md.mkdir(exist_ok=True)
            series.write_csv(md / "series.csv")
            (md / "summary.json").write_text(json.dumps(summ, indent=2) + "\n", encoding="utf-8", newline="")
            s["qnn_cum"] = summ.get("qnn_cum")
            s["mean_mpd"] = summ.get("mean_mpd")
        except Exception as err:  # T05's measures are an add-on; a failure is reported, not fatal
            s["measures_error"] = repr(err)[:200]
    par_df.write_csv(d.parent / f"s{seed}_parasites.csv")
    return bins, s


def summarize_world(bdf: pl.DataFrame, runs: pl.DataFrame, seeds: list[int]) -> str:
    n = len(seeds)
    need = math.ceil(20 * n / 30)
    pct = lambda v: "–" if v is None else f"{100 * v:.2f}%"
    med = lambda x, c: x[c].drop_nulls().median() if x[c].drop_nulls().len() else None
    lines = [f"# E015 stage 3: tierra against std, {n} seeds x {TICKS:,} ticks, bins of {BIN:,}", "",
             "Per arm, medians over seeds per bin: exact births, parasite-lineage share of exact births, entered share "
             "of replicator-class deaths, resident share of deaths (and of intruder deaths), living bodies, share with "
             "IP off their own body, nop share of living bytes, body length p10/p50/p90.", "",
             "| arm | bin | exact | parasite | entered | resident | resident (intruders) | pop | IP off body | nop share | len p10/p50/p90 |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm in ARMS:
        for k in sorted(bdf["bin"].unique().to_list()):
            x = bdf.filter((pl.col("arm") == arm) & (pl.col("bin") == k))
            if not x.height:
                continue
            f0 = lambda v: "–" if v is None else f"{v:,.0f}"
            lines.append(f"| {arm} | {k} | {f0(med(x, 'exact'))} | {pct(med(x, 'par_share'))} | {pct(med(x, 'entered_share'))} "
                         f"| {pct(med(x, 'resident_share'))} | {pct(med(x, 'resident_intr_share'))} | {f0(med(x, 'pop'))} "
                         f"| {pct(med(x, 'ip_off_share'))} | {pct(med(x, 'nop_share'))} "
                         f"| {f0(med(x, 'len_p10'))}/{f0(med(x, 'len_p50'))}/{f0(med(x, 'len_p90'))} |")
    t = runs.filter(pl.col("arm") == "tierra")
    s = runs.filter(pl.col("arm") == "std")
    t_hi = int((t["par_share_last"].fill_null(0) > PAR_HI).sum())
    s_lo = int((s["par_share_last"].fill_null(0) <= STD_LO).sum())
    te, se = med(t, "entered_share_post"), med(s, "entered_share_post")
    lines += ["", "## Prediction checks (H17, T03 section 4)", "",
              f"1. Parasite share of exact births in the last bin > {pct(PAR_HI)} in >= {need} of {n} tierra seeds: "
              f"{t_hi}; <= {pct(STD_LO)} in >= {need} of {n} std seeds: {s_lo}. "
              f"{'holds' if t_hi >= need and s_lo >= need else 'fails'}. Medians: tierra {pct(med(t, 'par_share_last'))}, "
              f"std {pct(med(s, 'par_share_last'))}; max over bins, medians: tierra {pct(med(t, 'par_share_max'))}, "
              f"std {pct(med(s, 'par_share_max'))}.",
              f"2. Entered share of replicator-class deaths after {SECOND_HALF:,} (median over seeds): tierra {pct(te)} "
              f"[> {pct(ENTER_T)}], std {pct(se)} [{pct(ENTER_STD[0])}-{pct(ENTER_STD[1])}]. "
              f"{'holds' if te is not None and se is not None and te > ENTER_T and ENTER_STD[0] <= se <= ENTER_STD[1] else 'fails'}.",
              "3. The neighbourhood clause is in stage 1's summary (runs/e015/nbhd/summary.md).", "",
              "Per run: " + ", ".join(runs.columns)]
    for r in runs.sort("arm", "seed").iter_rows(named=True):
        lines.append("- " + ", ".join(f"{k}={v:.4g}" if isinstance(v, float) else f"{k}={v}" for k, v in r.items()))
    return "\n".join(lines)


# ---- driver -------------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["nbhd", "gate", "world"])
    ap.add_argument("--evo-bin", help="evo-core binary (default $EVO_BIN, else evo-core/target/release; not built)")
    ap.add_argument("--out", type=Path, default=OUT, help="output root (default runs/e015)")
    ap.add_argument("--seeds", type=int, help="seeds 1..N (default 10 for gate, 30 for world)")
    ap.add_argument("--ticks", type=int, default=TICKS, help="override for smoke tests only")
    ap.add_argument("--harness-ticks", type=int, default=HARNESS_TICKS, help="nbhd: override for smoke tests only")
    ap.add_argument("--bin", type=int, default=BIN, help="world: bin size; override for smoke tests only")
    ap.add_argument("--threads", type=int, default=12, help="nbhd: --threads for evo-core")
    ap.add_argument("--jobs", type=int, default=6, help="gate/world: runs in parallel")
    ap.add_argument("--force", action="store_true", help="redo runs that exist")
    ap.add_argument("--force-world", action="store_true", help="run stage 3 although the gate has not passed")
    ap.add_argument("--no-compress", action="store_true")
    ap.add_argument("--no-measures", action="store_true", help="world: skip T05's measures")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--arm", choices=list(GATE_ARMS), default="tierra",
                    help="gate: which arm (tierra is the registered gate; the other legacy-edge arms were added after "
                         "it failed; the _fix arms are T08's baseline under the fixed edge)")
    a = ap.parse_args()
    t_all = time.time()
    exe = evo_bin(a.evo_bin)
    if not a.analyse_only:
        check_binary(exe)

    if a.stage == "nbhd":
        out = a.out / "nbhd"
        if not a.analyse_only:
            run_nbhd(exe, out, a.threads, a.harness_ticks, a.force)
        text = summarize_nbhd(exe, out, a.harness_ticks)
        (out / "summary.md").write_text(text + "\n", encoding="utf-8", newline="")
        print(text)
        print(f"total {time.time() - t_all:.0f} s")
        return

    seeds = list(range(1, (a.seeds or (GATE_SEEDS if a.stage == "gate" else WORLD_SEEDS)) + 1))
    arms = [a.arm] if a.stage == "gate" else ARMS
    if a.stage == "world" and len({LEGACY in ARM_FLAGS[arm] for arm in arms}) > 1:
        raise SystemExit("stage 3 as registered compares " + ", ".join(
            f"{arm} ({'legacy' if LEGACY in ARM_FLAGS[arm] else 'fixed'} edge)" for arm in arms)
            + ": not one physics. Since T08 the `tierra` arm (the gate's ten seeds) is the legacy world and `std` "
              "the fixed one; stage 3 under the fixed edge is folded into E016's cost-off arms "
              "(docs/research/experiments/2026-10-13-e016-defence-search.md)")
    if a.stage == "world" and not a.force_world:
        g = a.out / "world" / "gate.csv"
        ok = g.exists() and pl.read_csv(g)["passed"].sum() >= GATE_NEED
        if not ok:
            raise SystemExit("stage 3 waits for the persistence gate (runs/e015/world/gate.csv with >= 8 passes); "
                             "--force-world overrides")
    jobs = [(arm, s) for arm in arms for s in seeds]
    if not a.analyse_only:
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda j: run_one(exe, a.out, j[0], j[1], a.ticks, a.force, not a.no_compress), jobs):
                print(msg, flush=True)
        print(f"runs and classes: {time.time() - t_all:.0f} s", flush=True)

    wd = a.out / "world"
    if a.stage == "gate":
        name = "gate" if a.arm == "tierra" else f"gate_{a.arm}"
        rows = [gate_row(a.out, a.arm, s, a.ticks) for s in seeds if has(run_dir(a.out, a.arm, s), "classes.csv")]
        pl.DataFrame(rows).write_csv(wd / f"{name}.csv")
        text = summarize_gate(rows, a.ticks, seeds, a.arm)
        text += "\n" + "\n".join(gate_detail(a.out, a.arm, seeds, a.ticks, a.bin, name))
        (wd / f"{name}.md").write_text(text + "\n", encoding="utf-8", newline="")
    else:
        done = [j for j in jobs if has(run_dir(a.out, *j), "classes.csv")]
        with ThreadPoolExecutor(min(a.jobs, 4)) as ex:
            res = list(ex.map(lambda j: analyse_world(a.out, j[0], j[1], a.ticks, a.bin, not a.no_measures), done))
        bdf = pl.DataFrame([b for bins, _ in res for b in bins], infer_schema_length=None)
        runs = pl.DataFrame([s for _, s in res], infer_schema_length=None)
        bdf.write_csv(wd / "bins.csv")
        runs.write_csv(wd / "runs.csv")
        text = summarize_world(bdf, runs, seeds)
        (wd / "summary.md").write_text(text + "\n", encoding="utf-8", newline="")
    print(text)
    print(f"total {time.time() - t_all:.0f} s")


if __name__ == "__main__":
    main()
