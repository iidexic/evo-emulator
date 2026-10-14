"""E016: cost x ancestor, the defence search (H16 gate 2; H17 under the fixed
edge). The record is the contract:
docs/research/experiments/2026-10-13-e016-defence-search.md (section numbers
below are its; §7 holds the amendments made before launch, which this runner
implements). Under `--cycle-theft-pct 50` an intruder's instruction on a
host's byte debits the host's per-tick budget by half its cost; in a world
seeded with the 41-byte template body (E015), whose one-hop parasite is a
label flip, does a defence against being entered arise and is it kept?

Arms (§2), sun S = 2 (resolved 2026-10-13), 30 seeds, 250,000 ticks,
`--census 500`, `--state-every 2500` (T04; §7.3), one founder at byte
32,768, T08's fixed `alloc`/`copy` edge (no `--legacy-pending-range`):

| arm | world flags |
|---|---|
| tierra_n0 | --ancestor tierra --sun 2 |
| tierra_t50 | --ancestor tierra --sun 2 --cycle-theft-pct 50 |
| tierra_tax | --ancestor tierra --sun 2 --cycle-tax-pct P --cycle-tax-frac F |
| std_n0 | --ancestor std --sun 2 |
| std_t50 | --ancestor std --sun 2 --cycle-theft-pct 50 |

Every harness call (`--classify`, `--host`) gets the arm's physics flags
(everything above but `--ancestor`; the harness has its noise off).

The probe parasite (§1). For `tierra`: the ancestor body with byte 18 (the
first byte of L1, `nop1`) changed to `nop0`; its `searchf` then misses its
own L1 and finds the host's, entering at offset 22 (`parasite_jump`, T03 §3
test 2):
0101030351fc117f1605084c0a010301036d010103011332525a71fc1845486c11101c0b030301016d.
For `std`: the std body has no label to flip, so its probe is the known
fall-through intruder of E005 and E014, a one-byte `pad` (`--host 00`):
it runs off its own end into the host and copies itself with the host's
loop (§7: a std "defence" is against a placement accident).

The defence rule (§1 with §7.1), per candidate genome G under the arm's
flags, two 3,000-tick harness runs: `alone` (G alone, `--classify`; class
and exact births b_alone) and `probed` (`--host PROBE --host-body G`; G's
exact births b_probed = `host_exact_births`, the probe's p_probed =
`exact_births`). Reference: the arm's ancestor A gives b_alone(A),
b_probed(A), p_probed(A). Viable: G replicator-class alone and b_alone(G)
>= 0.5 b_alone(A) (§7.1's floor). `immune`: viable and p_probed(G) < 0.1
p_probed(A). `tolerant`: viable, b_probed(G) >= 0.9 b_alone(G) and
b_probed(G) >= 1.2 b_probed(A). Complete = either. `mechanism` (§7.1):
`parameter` when G has the ancestor's length and differs from it only in
the operand bytes of `lit A {k}` and `lit A {e}` (traits.ABSORB / ENDOW,
bytes 6 and 17, for std; traits.ABSORB_T / ENDOW_T, bytes 7 and 33, for
tierra), else `structural`, compared on the canonical form (a synonymous
byte elsewhere, same func_hash, is no difference); given for every screened
genome, read on the complete ones. H16 gate 2, "maintained", the paired reading, `lod` and
`replay` use the structural complete set; `parameter` defences are reported
beside it. The harness stops when the probe dies (`stopped_early`), so a G
that kills the probe has b_probed over `ticks_run` ticks only and can
qualify as immune, not tolerant; `ticks_run`, `stopped_early` are kept.
`alone` is one `--classify` over a temporary genomes.csv holding every
candidate (lod.harness_alone); each genome runs alone in it, and a one-row
file gives the same row (checked 2026-10-13).

Stages (subcommands):

- `world`: the runs. Default arms tierra_n0, tierra_t50, std_n0, std_t50
  (`--arms tierra_tax` after `calibrate`). N at a time (`--jobs`, default
  os.cpu_count()). Each run is classified with the arm's flags and gzipped
  (every file but patches.csv and meta.json, and every state/<tick>.bin to
  <tick>.bin.gz; evo_run reads .gz, `replay` inflates the snapshot it
  needs). Resumable: a seed with classes.csv is skipped (its snapshots and
  meta are checked). Refuses to start unless a one-tick dry run of the
  binary accepts `--state-every` (T04), since the snapshots cannot be added
  afterwards (§2). `--no-snapshots` drops the flag for a smoke run only
  (refused without `--smoke`, which also needs `--out` away from
  runs/e016); so does any `--ticks` other than 250,000. Directories
  runs/e016/<arm>/s<seed>/.
- `calibrate`: the tax control (§2, T02 §4.2) over replicator-class deaths
  (class of the birth genome) after tick 25,000, seeds pooled: F = entered
  share (`exec_by_others` > 0) of tierra_n0's deaths (the record: "P, F
  from tierra_n0"); r = sum `cycles_lost_m` / sum `age` over tierra_t50's;
  P = 100 r / (F x 32,000) rounded to the nearest whole percent (halves up,
  clamped to 0-100; 0 is refused). Also kept for the record: t50's own
  entered share. Writes runs/e016/tax.json and prints F, r, P (record them
  in the experiment file before launching tierra_tax). An existing tax.json
  with other values is not overwritten without `--force`.
- `screen`: first the reachability baseline (§1, §3): every mutant of the
  E015 stage 1 neighbourhood files (runs/e015/nbhd/<ancestor>.csv, every
  substitution and deletion of the ancestor) through the defence rule under
  each selected arm's flags of that ancestor (tierra_tax only once tax.json
  exists); writes runs/e016/nbhd_screen_<ancestor>.csv (one row per mutant
  per arm) and prints the counts by mechanism. Then every finished world
  run of the selected arms: candidates are the replicator-class
  (classes.csv) `func_hash`es with >= 0.5% of a 25,000-tick window's exact
  births (all exact births in the window, any class, as the denominator) in
  some window, or >= 50 exact births in the run; each is tested on its most
  common raw body among its replicator-class exact births (synonymous
  bodies share a func_hash and behave alike). Writes RUN_DIR/defence.csv:
  `func_hash, len, b_alone, b_probed, p_probed, immune, tolerant,
  first_tick, last_tick` (first and last births.csv tick of any body with
  the func_hash), then `mechanism, raw_hash, class_alone, exact_births,
  max_window_share, host_alive, entry_off, ticks_run, stopped_early,
  bytes_hex`; RUN_DIR/defence_ref.json (the ancestor's numbers);
  runs/e016/screen.csv (counts per run, split by mechanism). Exact: the
  child equals the executor's body at `divide` (raw_hash ==
  parent_now_hash).
- `analyse`: per 2,500-tick bin per run (bin k holds ticks ((k-1)2500,
  k 2500]) E015's set (`exact`, `par_share` = E005's parasite-lineage share
  of exact births with E015's `parasite_2` set over the whole run,
  `rep_deaths`, `entered_share`, `resident_share`, `resident_intr_share`,
  `pop`, `ip_off_share`, `nop_share`, `len_p10/50/90`), plus `rep_exact`,
  `defence_share` (exact births by complete genomes over replicator-class
  exact births), its split `structural_share` / `parameter_share`,
  `immune_share`, `tolerant_share` (all complete genomes),
  `cycles_lost_per_tick` (mean `cycles_lost_m / age` over entered
  replicator-class deaths, E014), `entered_cpt` and `entered_cpt_norm`
  (offspring per tick of entered over unentered reproducers:
  replicator-class deaths with `age` > 50 and `offspring` > 0, mean of
  `offspring / age` in each group, E014's amendment; norm = over the same
  seed and bin of the arm's n0 partner). Per run: the structural and the
  parameter share by 25,000-tick window and `maintained` (§7.2: >= 1% of
  replicator-class exact births in at least four consecutive windows,
  100,000 ticks, anywhere in the run; on the structural set, with
  `maintained_parameter` beside it); `first_structural_tick`,
  `first_parameter_tick` (first births.csv birth of such a genome);
  `structural_share_end` (the run's last 2,500-tick bin); H17's readings at
  50,000 from the n0 arms (parasite share in the bin ending at 50,000 with
  the parasite set taken over the run cut at 50,000, as E015's 50,000-tick
  runs had it; entered share of replicator-class deaths in (25,000,
  50,000]). T05's `measures.compute` with a `defence_class` grouping
  (genomes.csv gains the column: `structural`, `parameter` (complete, by
  mechanism), `not` (screened, neither), `unmatched` (not in defence.csv))
  and `qnn_series` over `func_hash` as turnover context; the series, with
  `structural_share` and `parameter_share` of census bodies, goes to
  RUN_DIR/measures/. Writes runs/e016/bins.csv, runs.csv, summary.md: §4's
  counts (H16 gate 2 maintained structural seeds per arm against >= 10 /
  <= 2 / <= 2; H17 seeds with parasite share > 5% (tierra_n0, >= 20 of 30)
  and <= 2% (std_n0), entered-share medians against > 25% and 7-14%), and
  §7.4's paired reading next to the gate: tierra_t50 against tierra_n0 and
  against tierra_tax paired by seed, on `structural_share_end` and on
  maintained (yes/no): pairs with t50 above, below, tied; a two-sided sign
  test over the untied pairs (binomial, p = 1/2); prediction t50 above in
  >= 20 of 30 pairs each. A pair missing either share (an extinct run) is
  left out and counted.
- `lod`: for every run with a structural complete genome, T06's line of
  descent (lod.lod, unchanged logic, with the arm's physics flags and probe
  in its two harness calls) from the founder to the first organism born
  with one. Added per step (lod/e016_steps.csv): the world column in
  2,500-tick bins against contemporaries (T06 follow-up rule: exact children
  per death of organisms born with the genome in the step's bin over that
  of every replicator-class organism born in the bin, both from
  lod.world_fitness), the harness column alone and probed with the probe's
  exact births and the defence rule per genome, and break-and-repair pairs
  (a deleterious step to f = 0 alone followed at once by a beneficial step
  from f = 0) paired off before counting. Croft's look-back
  (lod/lookback.csv): the end organism's parent and grandparent on the line
  (and the parent's body at divide when it differs), each with which of the
  first structural genome's edits from the ancestor it carries (tierra by
  region: `template` bytes 13-16, `label` L1 bytes 18-21, `other`) and the
  diff from it to that genome. Time-to-loss (lod/lineages.csv): every
  origin of a structural complete lineage (a body born so whose parent was
  not), the ticks from its birth to the lineage's last exact birth, and
  whether it is alive at the last census (censored). Writes
  runs/e016/lod_seeds.csv and lod_summary.md.
- `replay` (§3 with §7.3, T04): for each run whose first structural
  complete genome is born at t, the snapshot at the last multiple of 2,500
  below t (state/<tick>.bin.gz, inflated to a temporary file for the run
  and removed after), replayed with `--replay-from FILE --seed S` (S =
  1001..1010) to tick t + 50,000. When that multiple is 0 (t <= 2,500)
  there is no snapshot: the replays are plain runs from the founder with
  the arm's flags and `--seed S` to tick 50,000, which is the per-seed
  arising rate itself; they are shared by every such source seed of the
  arm (runs/e016/replay/<arm>/founder/r<S>/) and reported as `founder`, not
  as potentiation. Background: 10 replays from the 25,000 snapshot of the
  arm's seeds with no structural complete genome by the run's end (the
  first 10 by seed; with fewer, they are cycled, each replay its own new
  seed), to tick 100,000. Each replay is classified and screened as a world
  run (same rule, same arm reference); it counts if a structural complete
  genome is born in it. Directories runs/e016/replay/<arm>/s<seed>/r<S>/;
  writes runs/e016/replay.csv (`kind`: potentiation, founder, background)
  and replay_summary.md. Refuses unless the binary accepts `--replay-from`.

Runs shorter than 50,000 ticks (smoke) read the "after 25,000" deaths after
half the run instead.

The binary is `--evo-bin`, else $EVO_BIN, else evo-core/target/release/
evo-core(.exe); nothing is built here. Its `std` and `tierra` ancestors are
checked against e015_template.HEX before any engine stage.

Usage (from the repo root):

    uv run --project analysis analysis/e016_defence.py screen        # nbhd baseline first
    uv run --project analysis analysis/e016_defence.py world --jobs 24
    uv run --project analysis analysis/e016_defence.py calibrate
    uv run --project analysis analysis/e016_defence.py world --arms tierra_tax --jobs 24
    uv run --project analysis analysis/e016_defence.py screen
    uv run --project analysis analysis/e016_defence.py analyse
    uv run --project analysis analysis/e016_defence.py lod
    uv run --project analysis analysis/e016_defence.py replay
    uv run --project analysis analysis/e016_defence.py world --smoke --seeds 2 --ticks 3000 \\
        --out runs/e016_smoke                                           # smoke test only
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl

import lod
import measures as t05
from e015_template import HEX, check_binary, nop_share, parasite_genomes
from traits import ABSORB, ABSORB_T, ENDOW, ENDOW_T, canonical_instrs
from evo_run import HASH_COLS, ROOT, Run, csv_path, gunzip_verified, gzip_verified, load, world

OUT = ROOT / "runs" / "e016"
NBHD = ROOT / "runs" / "e015" / "nbhd"
SUN = 2  # §2, resolved 2026-10-13
TICKS = 250_000
SEEDS = 30
CENSUS = 500
STATE_EVERY = 2_500  # §7.3
BIN = 2_500
WINDOW = 25_000  # §1's windows and the candidate windows
HARNESS_TICKS = 3_000
FOUNDER_START = 32_768
SECOND_HALF = 25_000
H17_TICK = 50_000
RESIDENT = 0.9
CAP_M = 32_000  # Config::default(): cap_c0 = 32 units
NOISE = {"p_write_flip": 0.004761904761904762, "q_slip": 0.0011904761904761906, "p_bit_rot": 0.0001}
# §1 with §7.1: the defence rule, its viability floor, and "maintained" (§7.2).
IMMUNE_FRAC, KEEP_FRAC, GAIN_FRAC, FLOOR_FRAC = 0.1, 0.9, 1.2, 0.5
MAINT_SHARE, MAINT_WINDOWS = 0.01, 4  # four consecutive 25,000-tick windows
# §7.1: a `parameter` defence differs from the ancestor only in these operand bytes
# (`lit A {k}`, `lit A {e}`).
PARAM_POS = {"std": (ABSORB.offset, ENDOW.offset), "tierra": (ABSORB_T.offset, ENDOW_T.offset)}
# §3: candidate selection.
CAND_SHARE, CAND_EXACT = 0.005, 50
# E014's amendment: reproducers are deaths with age > 50 and offspring > 0.
REPRO_AGE = 50
# §4.
H16_NEED, H16_MAX = 10, 2
PAR_HI, STD_LO = 0.05, 0.02
ENTER_T, ENTER_STD = 0.25, (0.07, 0.14)
H17_NEED = 20
# §3 replay.
REPLAY_SEEDS = tuple(range(1001, 1011))
REPLAY_AFTER = 50_000
FOUNDER_TO = 50_000  # §7.3: t <= 2,500 is replayed from the founder to this tick
BACKGROUND_FROM, BACKGROUND_TO = 25_000, 100_000

NOP0, NOP1 = 1, 3
PROBE_POS = 18
TIERRA_REGIONS = {"template": (13, 16), "label": (18, 21)}
ARMS = ["tierra_n0", "tierra_t50", "tierra_tax", "std_n0", "std_t50"]
FIRST_ARMS = ["tierra_n0", "tierra_t50", "std_n0", "std_t50"]
N0_OF = {"tierra_n0": "tierra_n0", "tierra_t50": "tierra_n0", "tierra_tax": "tierra_n0",
         "std_n0": "std_n0", "std_t50": "std_n0"}
# Gzipped after classification; classes.csv last, so an interrupted
# compression still leaves the run seen as classified. The state/ snapshots
# are gzipped too (deflate_state) and inflated one at a time for a replay.
COMPRESS = ("births.csv", "deaths.csv", "orgs.csv", "census.csv", "world.bin", "genomes.csv", "classes.csv")

Tax = tuple[int, float]


# ---- arms and the probe ----------------------------------------------------------

def base(arm: str) -> str:
    """The ancestor an arm seeds: the name up to the first underscore."""
    return arm.split("_")[0]


def probe_hex(ancestor_hex: str) -> str:
    """The tierra probe parasite: byte 18 (L1's first byte) from nop1 to nop0."""
    b = bytearray.fromhex(ancestor_hex)
    if b[PROBE_POS] != NOP1:
        raise ValueError(f"byte {PROBE_POS} of {ancestor_hex} is {b[PROBE_POS]:02x}, not nop1")
    b[PROBE_POS] = NOP0
    return b.hex()


PROBE = {"tierra": probe_hex(HEX["tierra"]), "std": lod.PAD_HEX}


def physics(arm: str, tax: Tax | None = None) -> list[str]:
    """The arm's physics flags (world and harness), without `--ancestor`."""
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm} (one of {', '.join(ARMS)})")
    f = ["--sun", str(SUN)]
    if arm.endswith("_t50"):
        f += ["--cycle-theft-pct", "50"]
    if arm.endswith("_tax"):
        if tax is None:
            raise SystemExit("tierra_tax needs P and F: run `calibrate` first (runs/e016/tax.json)")
        f += ["--cycle-tax-pct", str(tax[0]), "--cycle-tax-frac", repr(float(tax[1]))]
    return f


def run_dir(out: Path, arm: str, seed: int) -> Path:
    return out / arm / f"s{seed}"


def replay_dir(out: Path, arm: str, seed: int, new_seed: int) -> Path:
    return out / "replay" / arm / f"s{seed}" / f"r{new_seed}"


def has(d: Path, name: str) -> bool:
    return (d / name).exists() or (d / f"{name}.gz").exists()


def after(ticks: int) -> int:
    """The "after 25,000" tick; half the run for smoke runs under 50,000."""
    return min(SECOND_HALF, ticks // 2)


def world_cmd(exe: Path, d: Path, arm: str, seed: int, ticks: int, tax: Tax | None, snapshots: bool) -> list[str]:
    cmd = [str(exe), "--ticks", str(ticks), "--seed", str(seed), "--report", str(CENSUS), "--census", str(CENSUS),
           "--out", str(d), "--ancestor", base(arm), *physics(arm, tax)]
    return cmd + (["--state-every", str(STATE_EVERY)] if snapshots else [])


def classify_cmd(exe: Path, d: Path, arm: str, tax: Tax | None) -> list[str]:
    return [str(exe), "--classify", str(d), "--harness-ticks", str(HARNESS_TICKS), *physics(arm, tax)]


def replay_cmd(exe: Path, snap: Path, d: Path, arm: str, new_seed: int, to_tick: int, tax: Tax | None) -> list[str]:
    # --ancestor seeds nothing in a replay; it is passed so meta.json records it (T04).
    return [str(exe), "--replay-from", str(snap), "--seed", str(new_seed), "--ticks", str(to_tick),
            "--report", str(CENSUS), "--census", str(CENSUS), "--out", str(d), "--ancestor", base(arm),
            *physics(arm, tax)]


# ---- binary ------------------------------------------------------------------------

def evo_bin(path: str | None) -> Path:
    try:
        return t05.evo_bin(path)
    except FileNotFoundError as e:
        raise SystemExit(str(e))


def dry_run(exe: Path, args: list[str]) -> tuple[int, str]:
    """A one-tick run with `args` into a temporary directory: (exit code, output)."""
    with tempfile.TemporaryDirectory(prefix="e016_probe_") as tmp:
        r = subprocess.run([str(exe), "--ticks", "1", "--out", str(Path(tmp) / "p"), *args],
                           capture_output=True, text=True)
    return r.returncode, (r.stderr + r.stdout).strip()


def require_snapshots(exe: Path) -> None:
    code, msg = dry_run(exe, ["--state-every", str(STATE_EVERY)])
    if code != 0 or "unknown arg" in msg:
        raise SystemExit(
            f"{exe} does not accept --state-every (T04 not built?): exit {code}: {msg.splitlines()[-1] if msg else ''}\n"
            f"E016's world stage writes full-state snapshots every {STATE_EVERY:,} ticks (§2, §7.3), which cannot be "
            "added after the runs. Build T04 first. (`--smoke --no-snapshots` skips them for a smoke run only.)")


def require_replay(exe: Path) -> None:
    code, msg = dry_run(exe, ["--replay-from", str(Path(tempfile.gettempdir()) / "e016-no-such-state.bin")])
    if "unknown arg --replay-from" in msg:
        raise SystemExit(f"{exe} does not accept --replay-from (T04 not built?): {msg.splitlines()[-1]}")


def load_tax(out: Path) -> Tax | None:
    p = out / "tax.json"
    if not p.exists():
        return None
    c = json.loads(p.read_text())
    return int(c["P"]), float(c["F"])


# ---- meta checks -----------------------------------------------------------------------

def meta_problems(m: dict, arm: str, ticks: int | None = None, tax: Tax | None = None, snapshots: bool = True,
                  replay: dict | None = None) -> list[str]:
    """What in meta.json does not match the arm: the ancestor, one founder at
    32,768 (not for a replay), the run length, sun, default noise, the fixed
    edge (`legacy_pending_range` present and false), cycle theft and tax,
    `state_every` (when snapshots are expected), and for a replay its
    `replay_from` tick and re-seed. Empty when it all matches."""
    b = base(arm)
    c = m.get("config", {})
    p = []
    if m.get("ancestor") != b:
        p.append(f"ancestor {m.get('ancestor')}, not {b}")
    if replay is None:
        hexes = [(f.get("hex"), f.get("count")) for f in m.get("founders", [])]
        if hexes != [(HEX[b], 1)]:
            p.append(f"founders {hexes}, not one {b} ancestor")
        if m.get("founder_starts") != [FOUNDER_START]:
            p.append(f"founder_starts {m.get('founder_starts')}, not [{FOUNDER_START}]")
        # A killed run has no ticks_run; an extinct one stops early (counted, as E007 did).
        if ticks is not None and (m.get("ticks_requested") != ticks or m.get("ticks_run") is None):
            p.append(f"ticks_requested {m.get('ticks_requested')}, ticks_run {m.get('ticks_run')}: not a finished "
                     f"{ticks}-tick run")
        if snapshots and m.get("state_every") != STATE_EVERY:
            p.append(f"state_every {m.get('state_every', 'absent')}, not {STATE_EVERY}")
    else:
        rf = m.get("replay_from") or {}
        if rf.get("tick") != replay["tick"] or rf.get("reseed") != replay["reseed"]:
            p.append(f"replay_from {rf or 'absent'}, not tick {replay['tick']} reseed {replay['reseed']}")
    if c.get("patch_income") != 256_000 * SUN or c.get("patch_cap") != 4_096_000 * SUN:
        p.append(f"patch_income {c.get('patch_income')}, patch_cap {c.get('patch_cap')}: not sun {SUN}")
    for k, v in NOISE.items():
        if c.get(k) is None or abs(float(c[k]) - v) > 1e-15:
            p.append(f"{k} {c.get(k)}, not the default {v}")
    if c.get("legacy_pending_range", True) is not False:
        p.append(f"legacy_pending_range {c.get('legacy_pending_range', 'absent')}: not T08's fixed edge")
    theft = 50 if arm.endswith("_t50") else 0
    if c.get("cycle_theft_pct") != theft:
        p.append(f"cycle_theft_pct {c.get('cycle_theft_pct')}, not {theft}")
    if arm.endswith("_tax"):
        if tax is None or c.get("cycle_tax_pct") != tax[0] or float(c.get("cycle_tax_frac", -1)) != float(tax[1]):
            p.append(f"cycle tax {c.get('cycle_tax_pct')} / {c.get('cycle_tax_frac')}, not {tax}")
    elif c.get("cycle_tax_pct") != 0 or float(c.get("cycle_tax_frac", -1)) != 1.0:
        p.append(f"cycle tax {c.get('cycle_tax_pct')} / {c.get('cycle_tax_frac')}, not off")
    return p


def check_meta(d: Path, arm: str, ticks: int | None, tax: Tax | None, snapshots: bool,
               replay: dict | None = None) -> dict:
    m = json.loads((d / "meta.json").read_text())
    p = meta_problems(m, arm, ticks, tax, snapshots, replay)
    if p:
        raise SystemExit(f"{d}: meta.json does not match arm {arm}: " + "; ".join(p))
    return m


def snapshot_ticks(d: Path) -> list[int]:
    """Ticks with a snapshot in d/state, plain (<tick>.bin) or gzipped
    (<tick>.bin.gz)."""
    s = d / "state"
    if not s.is_dir():
        return []
    out = set()
    for p in s.iterdir():
        for suf in (".bin.gz", ".bin"):
            if p.name.endswith(suf) and p.name[:-len(suf)].isdigit():
                out.add(int(p.name[:-len(suf)]))
    return sorted(out)


def deflate_state(d: Path) -> tuple[int, int]:
    """gzip every d/state/<tick>.bin to <tick>.bin.gz (evo_run.gzip_verified:
    read back and compared before the plain file goes). (plain, gzip) bytes."""
    a = b = 0
    s = d / "state"
    if s.is_dir():
        for p in sorted(s.glob("*.bin")):
            x, y = gzip_verified(p)
            a, b = a + x, b + y
    return a, b


def inflate_to(gz: Path, dst: Path) -> Path:
    """Write the plain contents of `gz` to `dst` (gzip checks its CRC)."""
    with gzip.open(gz, "rb") as fi, open(dst, "wb") as fo:
        shutil.copyfileobj(fi, fo, 1 << 20)
    return dst


@contextmanager
def snapshot_file(d: Path, tick: int):
    """A plain path to the run's snapshot at `tick` for the length of the
    block: state/<tick>.bin if it is plain, else state/<tick>.bin.gz inflated
    into a temporary directory that is removed afterwards (replays of one
    snapshot in parallel each inflate their own copy)."""
    plain, gz = d / "state" / f"{tick}.bin", d / "state" / f"{tick}.bin.gz"
    if plain.exists():
        yield plain
        return
    if not gz.exists():
        raise SystemExit(f"{d}: no snapshot at tick {tick} (state/{tick}.bin or .bin.gz)")
    with tempfile.TemporaryDirectory(prefix="e016_state_") as tmp:
        yield inflate_to(gz, Path(tmp) / f"{tick}.bin")


def missing_snapshots(d: Path, ticks: int) -> list[int]:
    """Multiples of STATE_EVERY up to the run's last tick (an extinct run
    stops early) with no state/<tick>.bin or .bin.gz."""
    end = json.loads((d / "meta.json").read_text()).get("ticks_run") or ticks
    have = set(snapshot_ticks(d))
    return [t for t in range(STATE_EVERY, min(ticks, end) + 1, STATE_EVERY) if t not in have]


# ---- world -------------------------------------------------------------------------------

def compress_run(d: Path) -> tuple[int, int]:
    a = b = 0
    for n in COMPRESS:
        if (d / n).exists():
            x, y = gzip_verified(d / n)
            a, b = a + x, b + y
    return a, b


def run_world(exe: Path, out: Path, arm: str, seed: int, ticks: int, tax: Tax | None, snapshots: bool,
              force: bool, compress: bool) -> str:
    d = run_dir(out, arm, seed)
    tag = f"{arm}/s{seed}"
    meta = d / "meta.json"
    if not force and has(d, "classes.csv"):
        check_meta(d, arm, ticks, tax, snapshots)
        if snapshots and (miss := missing_snapshots(d, ticks)):
            raise SystemExit(f"{tag}: finished but snapshots missing at {miss}")
        if compress and (any((d / n).exists() for n in COMPRESS) or any((d / "state").glob("*.bin"))):
            compress_run(d)
            deflate_state(d)
            return f"{tag}: done; compressed"
        return f"{tag}: done"
    t0 = time.time()
    mj = json.loads(meta.read_text()) if meta.exists() else {}
    complete = mj.get("ticks_requested") == ticks and mj.get("ticks_run") is not None and has(d, "genomes.csv")
    if force or not complete:
        if d.exists():
            shutil.rmtree(d)
        d.parent.mkdir(parents=True, exist_ok=True)
        with open(d.parent / f"s{seed}.stdout", "w", encoding="utf-8", newline="") as f:
            subprocess.run(world_cmd(exe, d, arm, seed, ticks, tax, snapshots), stdout=f, stderr=subprocess.DEVNULL,
                           check=True)
    check_meta(d, arm, ticks, tax, snapshots)
    if snapshots and (miss := missing_snapshots(d, ticks)):
        raise SystemExit(f"{tag}: run finished without snapshots at {miss}")
    if not (d / "genomes.csv").exists():
        gunzip_verified(d / "genomes.csv.gz")
    t1 = time.time()
    subprocess.run(classify_cmd(exe, d, arm, tax), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    msg = f"{tag}: run {t1 - t0:.0f} s, classify {time.time() - t1:.0f} s"
    if compress:
        a, b = compress_run(d)
        x, y = deflate_state(d)
        msg += f", gzip {a / 1e6:.1f} -> {b / 1e6:.1f} MB, snapshots {x / 1e6:.1f} -> {y / 1e6:.1f} MB"
    return msg


# ---- reading --------------------------------------------------------------------------------

def read_cols(d: Path, name: str, cols: list[str]) -> pl.DataFrame:
    p = csv_path(d, name)
    if p is None:
        raise SystemExit(f"{d}: no {name}.csv (plain or .gz)")
    over = {c: pl.Utf8 for c in HASH_COLS[name] if c in cols}
    return pl.read_csv(p, columns=cols, schema_overrides=over)


def with_class(df: pl.DataFrame, classes: pl.DataFrame, col: str) -> pl.DataFrame:
    c = classes.select(pl.col("raw_hash").alias(col), "class")
    return df.join(c, on=col, how="left").with_columns(pl.col("class").fill_null("unknown"))


# ---- calibration ----------------------------------------------------------------------------

def rep_deaths_after(d: Path, tick: int) -> pl.DataFrame:
    deaths = read_cols(d, "deaths", ["tick", "age", "birth_hash", "exec_by_others", "cycles_lost_m"])
    classes = read_cols(d, "classes", ["raw_hash", "class"])
    return with_class(deaths, classes, "birth_hash").filter(
        (pl.col("class") == "replicator") & (pl.col("tick") > tick))


def tax_calibration(n0: pl.DataFrame, t50: pl.DataFrame) -> dict:
    """T02 §4.2 as the record states it: F = entered share of `n0`'s deaths,
    r = sum `cycles_lost_m` / sum `age` of `t50`'s, P = 100 r / (F cap) to the
    nearest whole percent (halves up), clamped to 0-100. Both frames are the
    replicator-class deaths after the calibration tick (`age`,
    `exec_by_others`, `cycles_lost_m`)."""
    n, entered = n0.height, int((n0["exec_by_others"] > 0).sum()) if n0.height else 0
    if n == 0 or entered == 0:
        raise SystemExit(f"calibration: tierra_n0 has {n} replicator-class deaths, {entered} entered; cannot set F")
    f = entered / n
    lost, age = int(t50["cycles_lost_m"].sum()), int(t50["age"].sum())
    if age == 0:
        raise SystemExit("calibration: tierra_t50 has no replicator-class death with age > 0")
    r = lost / age
    p_exact = 100 * r / (f * CAP_M)
    p = min(100, max(0, math.floor(p_exact + 0.5)))
    if p == 0:
        raise SystemExit(f"calibration: P = {p_exact:.3f} rounds to 0 (F = {f!r}, r = {r:.2f}); a tax of 0 is no "
                         "control. Check the t50 runs first.")
    t50_entered = int((t50["exec_by_others"] > 0).sum())
    return dict(F=f, deaths_n0=n, entered_n0=entered, cycles_lost_m=lost, age=age, r=r, deaths_t50=t50.height,
                F_t50=t50_entered / t50.height if t50.height else None, cap_m=CAP_M, P_exact=p_exact, P=p)


def run_calibrate(out: Path, seeds: list[int], ticks: int, force: bool) -> dict:
    parts = {"tierra_n0": [], "tierra_t50": []}
    for arm in parts:
        for s in seeds:
            d = run_dir(out, arm, s)
            if not has(d, "classes.csv"):
                raise SystemExit(f"calibrate: {arm}/s{s} is not finished; calibrate reads all {len(seeds)} seeds")
            check_meta(d, arm, ticks, None, False)
            parts[arm].append(rep_deaths_after(d, after(ticks)))
    c = tax_calibration(pl.concat(parts["tierra_n0"]), pl.concat(parts["tierra_t50"]))
    c = dict(source="tierra_n0 (F), tierra_t50 (r)", seeds=seeds, after=after(ticks), **c)
    p = out / "tax.json"
    if p.exists() and not force:
        old = json.loads(p.read_text())
        if (old.get("P"), old.get("F")) != (c["P"], c["F"]):
            raise SystemExit(f"{p} holds P = {old.get('P')}, F = {old.get('F')!r}; this calibration gives P = {c['P']}, "
                             f"F = {c['F']!r}. --force overwrites (only before any tierra_tax run).")
    out.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(c, indent=2) + "\n", encoding="utf-8", newline="")
    return c


def calib_text(c: dict) -> str:
    return (f"Tax calibration (T02 §4.2; record §2), seeds {c['seeds'][0]}-{c['seeds'][-1]} pooled, replicator-class "
            f"deaths after tick {c['after']:,}: F = {c['entered_n0']:,} / {c['deaths_n0']:,} entered in tierra_n0 = "
            f"{c['F']!r}; r = {c['cycles_lost_m']:,} / {c['age']:,} = {c['r']:.4f} milli-units per organism-tick in "
            f"tierra_t50 ({c['deaths_t50']:,} deaths; their own entered share {c['F_t50']!r}); P = 100 r / (F x "
            f"{c['cap_m']:,}) = {c['P_exact']:.4f}, rounded P = {c['P']}. tierra_tax runs with --cycle-tax-pct {c['P']} "
            f"--cycle-tax-frac {c['F']!r}.")


# ---- the harness and the defence rule ----------------------------------------------------------

@dataclass(frozen=True)
class Ref:
    """The arm's ancestor in the harness: class and exact births alone, its
    exact births with the probe before it, the probe's exact births."""
    class_alone: str
    b_alone: int
    b_probed: int
    p_probed: int


def is_defence(class_alone: str, b_alone: int, b_probed: int, p_probed: int, ref: Ref) -> tuple[bool, bool]:
    """(immune, tolerant) by §1's rule with §7.1's floor: both need G
    replicator-class alone with b_alone(G) >= 0.5 b_alone(A)."""
    viable = class_alone == "replicator" and b_alone >= FLOOR_FRAC * ref.b_alone
    immune = viable and p_probed < IMMUNE_FRAC * ref.p_probed
    tolerant = viable and b_probed >= KEEP_FRAC * b_alone and b_probed >= GAIN_FRAC * ref.b_probed
    return immune, tolerant


def canonical(body: bytes) -> bytes:
    """The body as `isa::canonical` reads it (traits.canonical_instrs, written
    back one byte per op and operand by T05's helper): a synonymous byte, such
    as a bit-7 flip of a register op or a modifier bit an op ignores, reads as
    the ancestor's. The ancestors are their own canonical form."""
    return t05._canonical_body(body, canonical_instrs)


def mechanism(body_hex: str, anc: str) -> str:
    """§7.1: `parameter` when the body has the ancestor's length and differs
    from it only in the operand bytes of `lit A {k}` and `lit A {e}`
    (PARAM_POS), else `structural`. Compared on the canonical form, so a
    synonymous byte elsewhere (same func_hash) is no difference: the std smoke
    worlds' absorb and endowment raises carry such flips (byte 3 0x71 -> 0xf1,
    byte 12 0x18 -> 0x58) and are parameter defences. (The ancestor itself is
    `parameter`, vacuously; it is never complete.)"""
    a, g = bytes.fromhex(HEX[anc]), bytes.fromhex(body_hex)
    if len(a) != len(g):
        return "structural"
    ca, cg = canonical(a), canonical(g)
    if len(ca) == len(cg) and all(i in PARAM_POS[anc] for i in range(len(ca)) if ca[i] != cg[i]):
        return "parameter"
    return "structural"


def harness_rows(exe: Path, hexes: list[str], arm: str, tax: Tax | None, ticks: int, jobs: int) -> dict[str, dict]:
    """Both §1 harness runs for each distinct body hex: alone (one
    `--classify` over all of them) and probed (`--host PROBE --host-body G`,
    in parallel), under the arm's physics."""
    flags = tuple(physics(arm, tax))
    uniq = list(dict.fromkeys(hexes))
    keys = {f"g{i}": h for i, h in enumerate(uniq)}
    alone = lod.harness_alone(exe, keys, ticks, flags=flags)
    probe = PROBE[base(arm)]
    with ThreadPoolExecutor(max(1, jobs)) as pool:
        probed = list(pool.map(lambda h: lod.harness_entered(exe, h, ticks, flags=flags, probe=probe), uniq))
    out = {}
    for (k, h), p in zip(keys.items(), probed):
        a = alone[k]
        out[h] = dict(class_alone=a["class"], b_alone=a["exact_births"], b_probed=p["host_exact"],
                      p_probed=p["pad_exact"], host_alive=p["host_alive"], entry_off=p["entry_off"],
                      ticks_run=p["ticks_run"], stopped_early=p["stopped_early"])
    return out


def reference(exe: Path, arm: str, tax: Tax | None, ticks: int) -> Ref:
    r = harness_rows(exe, [HEX[base(arm)]], arm, tax, ticks, 1)[HEX[base(arm)]]
    ref = Ref(r["class_alone"], r["b_alone"], r["b_probed"], r["p_probed"])
    if ref.class_alone != "replicator" or ref.p_probed < 2:
        print(f"WARNING {arm}: the ancestor in the harness is {ref}: the probe is not a parasite on a "
              "replicator-class ancestor under these flags, so the rule's reference is degenerate (check the binary "
              "and the flags)", file=sys.stderr, flush=True)
    return ref


def apply_rule(df: pl.DataFrame, ref: Ref, anc: str | None = None, hex_col: str | None = None) -> pl.DataFrame:
    """Add `immune`, `tolerant` to a frame with class_alone, b_alone, b_probed,
    p_probed; with `anc` and `hex_col` (the body's bytes) also `mechanism`."""
    flags = [is_defence(c, a, b, p, ref) for c, a, b, p in
             df.select("class_alone", "b_alone", "b_probed", "p_probed").iter_rows()]
    df = df.with_columns(immune=pl.Series([f[0] for f in flags], dtype=pl.Boolean),
                         tolerant=pl.Series([f[1] for f in flags], dtype=pl.Boolean))
    if anc is not None and hex_col is not None:
        df = df.with_columns(mechanism=pl.Series([mechanism(h, anc) for h in df[hex_col].to_list()], dtype=pl.Utf8))
    return df


# ---- screen ----------------------------------------------------------------------------------------

def candidates(exact: pl.DataFrame, window: int = WINDOW, share: float = CAND_SHARE,
               n_min: int = CAND_EXACT) -> pl.DataFrame:
    """§3's candidates from exact births (`tick`, `raw_hash`, `func_hash`,
    `class`): replicator-class func_hashes with >= `share` of some window's
    exact births (all classes in the denominator) or >= `n_min` exact births
    in the run. Columns func_hash, raw_hash (its most common raw body among
    its replicator-class exact births; ties: the smaller hash),
    exact_births, max_window_share; sorted by func_hash."""
    schema = {"func_hash": pl.Utf8, "raw_hash": pl.Utf8, "exact_births": pl.Int64, "max_window_share": pl.Float64}
    if not exact.height:
        return pl.DataFrame(schema=schema)
    ex = exact.with_columns(win=pl.max_horizontal(pl.lit(1), (pl.col("tick") + window - 1) // window))
    tot = ex.group_by("win").agg(total=pl.len())
    rep = ex.filter(pl.col("class") == "replicator")
    shares = (rep.group_by("win", "func_hash").agg(n=pl.len()).join(tot, on="win")
              .group_by("func_hash").agg(max_window_share=(pl.col("n") / pl.col("total")).max()))
    n = rep.group_by("func_hash").agg(exact_births=pl.len())
    body = (rep.group_by("func_hash", "raw_hash").agg(k=pl.len())
            .sort(["func_hash", "k", "raw_hash"], descending=[False, True, False])
            .group_by("func_hash", maintain_order=True).agg(pl.col("raw_hash").first()))
    sel = (n.join(shares, on="func_hash").join(body, on="func_hash")
           .filter((pl.col("max_window_share") >= share) | (pl.col("exact_births") >= n_min)))
    return sel.select(pl.col("func_hash"), pl.col("raw_hash"), pl.col("exact_births").cast(pl.Int64),
                      pl.col("max_window_share").cast(pl.Float64)).sort("func_hash")


DEFENCE_COLS = ["func_hash", "len", "b_alone", "b_probed", "p_probed", "immune", "tolerant", "first_tick", "last_tick",
                "mechanism", "raw_hash", "class_alone", "exact_births", "max_window_share", "host_alive", "entry_off", "ticks_run",
                "stopped_early", "bytes_hex"]


def screen_run(exe: Path, d: Path, arm: str, tax: Tax | None, ref: Ref, ticks: int, jobs: int) -> pl.DataFrame:
    """Candidates of one run through §1's rule; writes d/defence.csv."""
    births = read_cols(d, "births", ["tick", "raw_hash", "parent_now_hash"])
    genomes = read_cols(d, "genomes", ["raw_hash", "func_hash", "len", "bytes_hex"])
    if csv_path(d, "classes") is None:
        raise SystemExit(f"{d}: no classes.csv; the world stage classifies each run")
    classes = read_cols(d, "classes", ["raw_hash", "class"])
    funcs = genomes.select("raw_hash", "func_hash")
    b = births.join(funcs, on="raw_hash", how="left")
    span = b.group_by("func_hash").agg(first_tick=pl.col("tick").min(), last_tick=pl.col("tick").max())
    exact = with_class(b.filter(pl.col("raw_hash") == pl.col("parent_now_hash")), classes, "raw_hash")
    cand = candidates(exact).join(genomes.select("raw_hash", "len", "bytes_hex"), on="raw_hash", how="left")
    rows = harness_rows(exe, cand["bytes_hex"].to_list(), arm, tax, ticks, jobs) if cand.height else {}
    h = pl.DataFrame([dict(bytes_hex=x, **rows[x]) for x in cand["bytes_hex"].to_list()],
                     schema={"bytes_hex": pl.Utf8, "class_alone": pl.Utf8, "b_alone": pl.Int64, "b_probed": pl.Int64,
                             "p_probed": pl.Int64, "host_alive": pl.Boolean, "entry_off": pl.Int64,
                             "ticks_run": pl.Int64, "stopped_early": pl.Boolean}).unique("bytes_hex")
    df = apply_rule(cand.join(h, on="bytes_hex", how="left").join(span, on="func_hash", how="left"), ref,
                    base(arm), "bytes_hex")
    df = df.select(DEFENCE_COLS).sort("first_tick", "func_hash")
    df.write_csv(d / "defence.csv")
    (d / "defence_ref.json").write_text(json.dumps(dict(arm=arm, probe=PROBE[base(arm)], flags=physics(arm, tax),
                                                        harness_ticks=ticks, **ref.__dict__), indent=2) + "\n",
                                        encoding="utf-8", newline="")
    return df


def screen_counts(df: pl.DataFrame) -> dict:
    """Counts of one defence.csv, split by mechanism, and the first births."""
    comp = df.filter(pl.col("immune") | pl.col("tolerant"))
    first = lambda x: int(x["first_tick"].min()) if x.height and x["first_tick"].min() is not None else None
    st, pa = comp.filter(pl.col("mechanism") == "structural"), comp.filter(pl.col("mechanism") == "parameter")
    return dict(candidates=df.height, complete=comp.height, structural=st.height, parameter=pa.height,
                immune=int(df["immune"].sum()), tolerant=int(df["tolerant"].sum()),
                structural_immune=int(st["immune"].sum()), structural_tolerant=int(st["tolerant"].sum()),
                first_complete_tick=first(comp), first_structural_tick=first(st), first_parameter_tick=first(pa))


def nbhd_screen(exe: Path, out: Path, arms: list[str], tax: Tax | None, ticks: int, jobs: int, force: bool,
                nbhd: Path = NBHD) -> None:
    """The reachability baseline (§1, §3): every mutant in E015's stage 1 files."""
    out.mkdir(parents=True, exist_ok=True)
    for anc in ("tierra", "std"):
        src = nbhd / f"{anc}.csv"
        todo_arms = [a for a in arms if base(a) == anc and (a != "tierra_tax" or tax is not None)]
        if not todo_arms:
            continue
        if not src.exists():
            print(f"nbhd screen {anc}: {src} not found (E015 stage 1); skipped", flush=True)
            continue
        dst = out / f"nbhd_screen_{anc}.csv"
        old = pl.read_csv(dst, infer_schema=False) if dst.exists() and not force else None
        done = set(old["arm"].unique().to_list()) if old is not None else set()
        nb = t05.read_neighbours(src).select("pos", "kind", "byte", "hex", "raw_hash", "func_hash",
                                            pl.col("label").alias("e015_label"))
        parts = []
        for arm in todo_arms:
            if arm in done:
                continue
            t0 = time.time()
            ref = reference(exe, arm, tax, ticks)
            rows = harness_rows(exe, nb["hex"].to_list(), arm, tax, ticks, jobs)
            h = pl.DataFrame([dict(hex=x, **r) for x, r in rows.items()])
            df = apply_rule(nb.join(h, on="hex", how="left"), ref, anc, "hex").with_columns(arm=pl.lit(arm))
            parts.append(df.select("arm", *[c for c in df.columns if c != "arm"]))
            print(f"nbhd screen {anc} {arm}: reference b_alone {ref.b_alone}, b_probed {ref.b_probed}, p_probed "
                  f"{ref.p_probed}; {time.time() - t0:.0f} s", flush=True)
        if parts:
            new = pl.concat(parts)
            if old is not None:
                new = pl.concat([old, new.cast({c: pl.Utf8 for c in new.columns})], how="vertical_relaxed")
            new.write_csv(dst)
        for line in nbhd_counts(pl.read_csv(dst, infer_schema=False), anc):
            print(line, flush=True)


def nbhd_counts(df: pl.DataFrame, anc: str) -> list[str]:
    """One line per arm of a nbhd_screen file (read as text)."""
    lines = []
    for arm in sorted(df["arm"].unique().to_list()):
        x = df.filter(pl.col("arm") == arm)
        imm, tol = x["immune"] == "true", x["tolerant"] == "true"
        comp = x.filter(imm | tol)
        rep = int((x["class_alone"] == "replicator").sum())
        st = int((comp["mechanism"] == "structural").sum())
        lines.append(f"nbhd screen {anc} {arm}: {x.height:,} mutants, {rep:,} replicator-class alone; immune "
                     f"{int(imm.sum())}, tolerant {int(tol.sum())}, complete {comp.height} (structural {st}, "
                     f"parameter {comp.height - st})")
    return lines


# ---- analyse -----------------------------------------------------------------------------------------

DEFENCE_SCHEMA = {"func_hash": pl.Utf8, "len": pl.Int64, "b_alone": pl.Int64, "b_probed": pl.Int64,
                  "p_probed": pl.Int64, "immune": pl.Boolean, "tolerant": pl.Boolean, "first_tick": pl.Int64,
                  "last_tick": pl.Int64, "raw_hash": pl.Utf8, "class_alone": pl.Utf8, "exact_births": pl.Int64,
                  "mechanism": pl.Utf8, "max_window_share": pl.Float64, "host_alive": pl.Boolean, "entry_off": pl.Int64,
                  "ticks_run": pl.Int64, "stopped_early": pl.Boolean, "bytes_hex": pl.Utf8}


def read_defence(d: Path) -> pl.DataFrame | None:
    p = d / "defence.csv"
    if not p.exists():
        return None
    return pl.read_csv(p, schema_overrides=DEFENCE_SCHEMA)


def defence_sets(df: pl.DataFrame | None) -> dict[str, set[str]]:
    """func_hash sets: screened, complete, immune, tolerant (all complete),
    and the complete ones by mechanism, structural and parameter."""
    if df is None:
        return dict(screened=set(), complete=set(), immune=set(), tolerant=set(), structural=set(), parameter=set())
    f = lambda e: set(df.filter(e)["func_hash"].to_list())
    comp = pl.col("immune") | pl.col("tolerant")
    return dict(screened=set(df["func_hash"].to_list()), complete=f(comp), immune=f(pl.col("immune")),
                tolerant=f(pl.col("tolerant")), structural=f(comp & (pl.col("mechanism") == "structural")),
                parameter=f(comp & (pl.col("mechanism") == "parameter")))


def maintained(shares: list[float | None], threshold: float = MAINT_SHARE, run_windows: int = MAINT_WINDOWS) -> dict:
    """§7.2's "maintained" over per-window shares (window 1 first): >=
    `threshold` in at least `run_windows` consecutive windows anywhere in the
    run. A window with no replicator-class exact births does not hold."""
    ok = [s is not None and s >= threshold for s in shares]
    first = next((i for i, v in enumerate(ok) if v), None)
    longest = cur = 0
    for v in ok:
        cur = cur + 1 if v else 0
        longest = max(longest, cur)
    return dict(maintained=longest >= run_windows, first_window=None if first is None else first + 1,
                longest_windows=longest, windows_held=sum(ok))


def snapshot_tick(t: int, every: int = STATE_EVERY) -> int:
    """§7.3: the snapshot at the last multiple of `every` below t; 0 when
    there is none (t <= every), which means a replay from the founder."""
    return ((t - 1) // every) * every


def cpt_ratio(d: pl.DataFrame) -> float | None:
    """Mean `offspring / age` of entered reproducers over unentered (E014's
    amendment); `d` holds reproducing deaths with `entered`, `cpt`."""
    e = d.filter(pl.col("entered"))["cpt"]
    u = d.filter(~pl.col("entered"))["cpt"]
    if not e.len() or not u.len() or not u.mean():
        return None
    return float(e.mean() / u.mean())


def truncate(run: Run, tick: int) -> Run:
    """The run as if it had ended at `tick` (for H17's 50,000 reading)."""
    cut = lambda df: df.filter(pl.col("tick") <= tick)
    return Run(dir=run.dir, meta=run.meta, births=cut(run.births), deaths=cut(run.deaths), census=cut(run.census),
               orgs=cut(run.orgs), patches=cut(run.patches), genomes=run.genomes, classes=run.classes)


def defence_class(sets: dict) -> pl.Expr:
    """T05's grouping: structural, parameter (complete, by mechanism), not
    (screened, neither), unmatched (not screened)."""
    f = pl.col("func_hash")
    return (pl.when(f.is_in(sorted(sets["structural"]))).then(pl.lit("structural"))
            .when(f.is_in(sorted(sets["parameter"]))).then(pl.lit("parameter"))
            .when(f.is_in(sorted(sets["screened"]))).then(pl.lit("not")).otherwise(pl.lit("unmatched")))


def analyse_run(out: Path, arm: str, seed: int, ticks: int, bin_size: int, tax: Tax | None, snapshots: bool,
                do_measures: bool) -> tuple[list[dict], dict]:
    d = run_dir(out, arm, seed)
    check_meta(d, arm, ticks, tax, snapshots)
    run = load(d)
    ddf = read_defence(d)
    sets = defence_sets(ddf)
    funcs = run.genomes.select("raw_hash", "func_hash")
    raws = lambda key: sorted(set(funcs.filter(pl.col("func_hash").is_in(sorted(sets[key])))["raw_hash"].to_list()))
    comp_r, imm_r, tol_r, st_r, pa_r = (raws("complete"), raws("immune"), raws("tolerant"), raws("structural"),
                                        raws("parameter"))
    par, _ = parasite_genomes(run)
    binx = lambda c: ((pl.col(c) + bin_size - 1) // bin_size).cast(pl.Int64)
    winx = lambda c: pl.max_horizontal(pl.lit(1), (pl.col(c) + WINDOW - 1) // WINDOW).cast(pl.Int64)
    ex = run.class_of(run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash")), "raw_hash").with_columns(
        bin=binx("tick"), win=winx("tick"), par=pl.col("raw_hash").is_in(list(par)),
        comp=pl.col("raw_hash").is_in(comp_r), imm=pl.col("raw_hash").is_in(imm_r),
        tol=pl.col("raw_hash").is_in(tol_r), st=pl.col("raw_hash").is_in(st_r), pa=pl.col("raw_hash").is_in(pa_r))
    rex = ex.filter(pl.col("class") == "replicator")
    deaths = run.class_of(run.deaths, "birth_hash").with_columns(
        bin=binx("tick"), entered=pl.col("exec_by_others") > 0,
        resident=(pl.col("executed") > 0) & (pl.col("exec_foreign") > RESIDENT * pl.col("executed")))
    rep = deaths.filter(pl.col("class") == "replicator")
    repro = rep.filter((pl.col("age") > REPRO_AGE) & (pl.col("offspring") > 0)).with_columns(
        cpt=pl.col("offspring") / pl.col("age"))
    ran = deaths.filter(pl.col("executed") > 0)
    intr = deaths.filter(pl.col("exec_foreign") > 0)
    orgs = run.orgs.with_columns(off=pl.col("ip_off") >= pl.col("len"))
    w = world(d)
    by = lambda df, key: {r[key]: r for r in df.iter_rows(named=True)}
    has_def = ddf is not None
    eb = by(ex.group_by("bin").agg(exact=pl.len(), par_share=pl.col("par").mean()), "bin")
    xb = by(rex.group_by("bin").agg(rep_exact=pl.len(), defence_share=pl.col("comp").mean(),
                                    structural_share=pl.col("st").mean(), parameter_share=pl.col("pa").mean(),
                                    immune_share=pl.col("imm").mean(), tolerant_share=pl.col("tol").mean()), "bin")
    rb = by(rep.group_by("bin").agg(
        rep_deaths=pl.len(), entered_share=pl.col("entered").mean(),
        cycles_lost_per_tick=(pl.col("cycles_lost_m") / pl.col("age")).filter(
            pl.col("entered") & (pl.col("age") > 0)).mean()), "bin")
    cpt = {k: cpt_ratio(g) for (k,), g in repro.group_by("bin")} if repro.height else {}
    ab = by(ran.group_by("bin").agg(resident_share=pl.col("resident").mean()), "bin")
    ib = by(intr.group_by("bin").agg(resident_intr_share=pl.col("resident").mean()), "bin")
    cb = by(orgs.group_by("tick").agg(pop=pl.len(), ip_off_share=pl.col("off").mean(),
                                      len_p10=pl.col("len").quantile(0.1, "linear"), len_p50=pl.col("len").median(),
                                      len_p90=pl.col("len").quantile(0.9, "linear")), "tick")
    bins = []
    for k in range(1, ticks // bin_size + 1):
        hi = k * bin_size
        e, x, r, a, i, c = (eb.get(k, {}), xb.get(k, {}), rb.get(k, {}), ab.get(k, {}), ib.get(k, {}),
                            cb.get(hi, {}))
        dfs = lambda key: x.get(key) if has_def else None
        bins.append(dict(arm=arm, seed=seed, bin=k, tick_end=hi, exact=e.get("exact", 0), par_share=e.get("par_share"),
                         rep_exact=x.get("rep_exact", 0), defence_share=dfs("defence_share"),
                         structural_share=dfs("structural_share"), parameter_share=dfs("parameter_share"),
                         immune_share=dfs("immune_share"), tolerant_share=dfs("tolerant_share"),
                         rep_deaths=r.get("rep_deaths", 0), entered_share=r.get("entered_share"),
                         resident_share=a.get("resident_share"), resident_intr_share=i.get("resident_intr_share"),
                         cycles_lost_per_tick=r.get("cycles_lost_per_tick"), entered_cpt=cpt.get(k),
                         pop=c.get("pop", 0), ip_off_share=c.get("ip_off_share"), nop_share=nop_share(run, w, hi),
                         len_p10=c.get("len_p10"), len_p50=c.get("len_p50"), len_p90=c.get("len_p90")))

    # The defence per 25,000-tick window and §7.2's "maintained", structural
    # (the gate's) and parameter (reported beside it).
    n_win = ticks // WINDOW
    wb = by(rex.group_by("win").agg(n=pl.len(), st=pl.col("st").mean(), pa=pl.col("pa").mean()), "win")
    wst = [wb[k]["st"] if k in wb and has_def else None for k in range(1, n_win + 1)]
    wpa = [wb[k]["pa"] if k in wb and has_def else None for k in range(1, n_win + 1)]
    m, mp = maintained(wst), maintained(wpa)

    def first_birth(rs):
        b = run.births.filter(pl.col("raw_hash").is_in(rs))
        return b.sort("tick", "child").row(0, named=True) if b.height else None

    first, first_p, first_any = first_birth(st_r), first_birth(pa_r), first_birth(comp_r)

    # H17 at 50,000 (or the run's end, if shorter).
    t17 = min(H17_TICK, ticks)
    k17 = t17 // bin_size
    par17, _ = parasite_genomes(truncate(run, t17))
    ex17 = ex.filter(pl.col("bin") == k17)
    late = lambda df: df.filter(pl.col("tick") > after(ticks))
    e17 = rep.filter((pl.col("tick") > after(t17)) & (pl.col("tick") <= t17))
    lp = late(repro)
    final = int(run.orgs["tick"].max()) if run.orgs.height else 0
    s = dict(arm=arm, seed=seed, final_tick=final, pop_end=cb.get(final, {}).get("pop", 0), par_genomes=len(par),
             par_share_last=bins[-1]["par_share"] if bins else None,
             par_share_h17=float(ex17["raw_hash"].is_in(list(par17)).mean()) if ex17.height else None,
             entered_share_h17=float(e17["entered"].mean()) if e17.height else None,
             entered_share_post=late(rep)["entered"].mean() if late(rep).height else None,
             resident_share_post=late(ran)["resident"].mean() if late(ran).height else None,
             cycles_lost_per_tick_post=(late(rep).filter(pl.col("entered") & (pl.col("age") > 0))
                                        .select((pl.col("cycles_lost_m") / pl.col("age")).mean()).item()
                                        if late(rep).height else None),
             entered_cpt_post=cpt_ratio(lp) if lp.height else None,
             screened=has_def, candidates=len(sets["screened"]), complete=len(sets["complete"]),
             structural=len(sets["structural"]), parameter=len(sets["parameter"]),
             immune=len(sets["immune"]), tolerant=len(sets["tolerant"]),
             first_complete_tick=first_any["tick"] if first_any else None,
             first_structural_tick=first["tick"] if first else None,
             first_structural_id=first["child"] if first else None,
             first_structural_hash=first["raw_hash"] if first else None,
             first_parameter_tick=first_p["tick"] if first_p else None,
             maintained=m["maintained"] if has_def else None, first_window=m["first_window"],
             longest_windows=m["longest_windows"], windows_held=m["windows_held"],
             maintained_parameter=mp["maintained"] if has_def else None,
             longest_windows_parameter=mp["longest_windows"],
             structural_share_end=bins[-1]["structural_share"] if bins else None,
             parameter_share_end=bins[-1]["parameter_share"] if bins else None,
             structural_share_max=max((b["structural_share"] for b in bins if b["structural_share"] is not None),
                                      default=None),
             **{f"structural_w{k + 1}": v for k, v in enumerate(wst)},
             **{f"parameter_w{k + 1}": v for k, v in enumerate(wpa)})
    if do_measures:
        try:
            run.genomes = run.genomes.with_columns(defence_class=defence_class(sets))
            series, summ = t05.compute(run, group="defence_class")
            qf = t05.qnn_series(run, "func_hash").select(
                "tick", qnn_func=pl.col("qnn"), qnn_cum_func=pl.col("qnn_cum"), n_func_hash=pl.col("n_func"))
            cls = run.genomes.select(pl.col("raw_hash").alias("now_hash"), "defence_class")
            n = lambda c: pl.col("count").filter(pl.col("defence_class").fill_null("unmatched") == c).sum() \
                / pl.col("count").sum()
            share = (run.census.join(cls, on="now_hash", how="left").group_by("tick").agg(
                structural_share=n("structural"), parameter_share=n("parameter"), unmatched_share=n("unmatched")))
            series = series.join(qf, on="tick", how="left").join(share, on="tick", how="left")
            md = d / "measures"
            md.mkdir(exist_ok=True)
            series.write_csv(md / "series.csv")
            summ["qnn_cum_func"] = float(series["qnn_cum_func"].drop_nulls()[-1]) if series.height else None
            (md / "summary.json").write_text(json.dumps(summ, indent=2) + "\n", encoding="utf-8", newline="")
            stat = series.filter(pl.col("tick") >= after(ticks))
            s.update(qnn_cum_class=summ.get("qnn_cum"), qnn_cum_func=summ["qnn_cum_func"],
                     mean_mpd=summ.get("mean_mpd"), root_lines=summ.get("root_lines"),
                     census_structural_mean=stat["structural_share"].mean() if stat.height else None,
                     census_parameter_mean=stat["parameter_share"].mean() if stat.height else None)
        except Exception as err:  # an add-on; a failure is reported, not fatal
            s["measures_error"] = repr(err)[:200]
    return bins, s


def _analyse_job(args: tuple) -> tuple[list[dict], dict]:
    return analyse_run(*args)


def add_cpt_norm(bdf: pl.DataFrame, runs: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """`entered_cpt_norm`: each arm's ratio over its n0 partner's, same seed
    (and bin); 1 for the n0 arms, null without the partner."""
    def norm(df, key, col, out_col):
        part = df.select("arm", *key, pl.col(col).alias("_n0")).rename({"arm": "_partner"})
        return (df.with_columns(_partner=pl.col("arm").replace_strict(N0_OF, default=None))
                .join(part, on=["_partner", *key], how="left", maintain_order="left")
                .with_columns(pl.when(pl.col("_n0") > 0).then(pl.col(col) / pl.col("_n0")).alias(out_col))
                .drop("_n0", "_partner"))
    return (norm(bdf, ["seed", "bin"], "entered_cpt", "entered_cpt_norm"),
            norm(runs, ["seed"], "entered_cpt_post", "entered_cpt_norm_post"))


# ---- summary ------------------------------------------------------------------------------------------

pct = lambda v: "–" if v is None else f"{100 * v:.2f}%"
f0 = lambda v: "–" if v is None else f"{v:,.0f}"
f2 = lambda v: "–" if v is None else f"{v:.2f}"
yn = lambda ok: "holds" if ok else "fails"


def med(x: pl.DataFrame, c: str):
    if c not in x.columns:
        return None
    v = x[c].drop_nulls()
    return v.median() if v.len() else None


def mm(x: pl.DataFrame, c: str, f=pct) -> str:
    if c not in x.columns or not x[c].drop_nulls().len():
        return "–"
    v = x[c].drop_nulls()
    return f"{f(v.median())} ({f(v.min())}-{f(v.max())})"


def sign_test(plus: int, minus: int) -> float:
    """Two-sided exact sign test over the untied pairs: twice the binomial
    tail P(X >= max(plus, minus)) at p = 1/2, capped at 1; 1 with no untied
    pair."""
    n = plus + minus
    if n == 0:
        return 1.0
    k = max(plus, minus)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def paired(runs: pl.DataFrame, a: str, b: str, col: str) -> dict:
    """§7.4: arm `a` against arm `b` paired by seed on `col` (a share, or a
    yes/no): pairs, a above, below, tied, seeds without a pair or with a
    missing value in either (`unpaired`), and the sign test's p."""
    x = runs.filter(pl.col("arm") == a).select("seed", pl.col(col).cast(pl.Float64).alias("x"))
    y = runs.filter(pl.col("arm") == b).select("seed", pl.col(col).cast(pl.Float64).alias("y"))
    j = x.join(y, on="seed", how="full", coalesce=True)
    ok = j.filter(pl.col("x").is_not_null() & pl.col("y").is_not_null())
    plus, minus = int((ok["x"] > ok["y"]).sum()), int((ok["x"] < ok["y"]).sum())
    return dict(pairs=ok.height, plus=plus, minus=minus, ties=ok.height - plus - minus,
                unpaired=j.height - ok.height, p=sign_test(plus, minus))


def paired_lines(runs: pl.DataFrame, n_seeds: int) -> list[str]:
    need = math.ceil(H17_NEED * n_seeds / 30)
    lines = [f"Paired reading (§7.4; next to the registered gate, which it does not replace): tierra_t50 against "
             f"tierra_n0 and against tierra_tax, by seed, on the structural share of replicator-class exact births in "
             f"the run's last {BIN:,}-tick bin and on maintained (yes/no). Sign test over untied pairs (two-sided, "
             f"binomial p = 1/2). Prediction: t50 above in >= {need} of {n_seeds} pairs each (the share)."]
    have = lambda a: runs.filter(pl.col("arm") == a).height > 0
    for other in ("tierra_n0", "tierra_tax"):
        if not (have("tierra_t50") and have(other)):
            lines.append(f"- t50 against {other}: not readable (an arm missing).")
            continue
        for col, what in (("structural_share_end", "share at the end"), ("maintained", "maintained")):
            r = paired(runs, "tierra_t50", other, col)
            verdict = f" [>= {need}]: {yn(r['plus'] >= need)}" if col == "structural_share_end" else ""
            lines.append(f"- t50 against {other}, {what}: t50 above in {r['plus']} of {r['pairs']} pairs, below in "
                         f"{r['minus']}, tied {r['ties']}; {r['unpaired']} seeds unpaired; sign test p = {r['p']:.4g}"
                         f"{verdict}.")
    return lines


def predictions(runs: pl.DataFrame, n_seeds: int) -> list[str]:
    at_least = lambda k: math.ceil(k * n_seeds / 30)
    at_most = lambda k: math.floor(k * n_seeds / 30)
    arm = lambda a: runs.filter(pl.col("arm") == a)
    count = lambda a, c: int(arm(a)[c].fill_null(False).sum()) if arm(a).height else None
    kept = lambda a: count(a, "maintained")
    show = lambda a, c="maintained": "–" if count(a, c) is None else f"{count(a, c)} of {arm(a).height}"
    lines = ["## Predictions (§4, §7)", "",
             f"{n_seeds} seeds per arm; k of 30 read as >= ceil(k n / 30), <= floor(k n / 30). A defence is complete "
             "under §1 with §7.1's floor; the gate counts `structural` defences only, maintained by §7.2 (>= 1% of "
             "replicator-class exact births in 4 consecutive 25,000-tick windows).", ""]
    t50, n0, tax = kept("tierra_t50"), kept("tierra_n0"), kept("tierra_tax")
    ok = t50 is not None and n0 is not None and tax is not None and t50 >= at_least(H16_NEED) \
        and n0 <= at_most(H16_MAX) and tax <= at_most(H16_MAX)
    lines.append(f"H16 gate 2 (registered). Seeds with a maintained structural defence: tierra_t50 {show('tierra_t50')} "
                 f"[>= {at_least(H16_NEED)}], tierra_n0 {show('tierra_n0')} [<= {at_most(H16_MAX)}], tierra_tax "
                 f"{show('tierra_tax')} [<= {at_most(H16_MAX)}]: "
                 f"{'not decidable (an arm missing)' if None in (t50, n0, tax) else yn(ok)}. std_t50 {show('std_t50')}, "
                 f"std_n0 {show('std_n0')} (no prediction).")
    if None not in (t50, n0, tax):
        lines.append(f"Refutation: t50 not above n0 ({t50} against {n0}): {'yes' if t50 <= n0 else 'no'}; maintained "
                     f"equally under the tax ({tax} against {t50}): {'yes' if t50 and tax >= t50 else 'no'}.")
    lines.append("")
    lines += paired_lines(runs, n_seeds)
    arose = lambda a, c: int(arm(a)[c].is_not_null().sum()) if arm(a).height else 0
    lines += ["", "Seeds where a structural complete genome arose (maintained or not): " + ", ".join(
        f"{a} {arose(a, 'first_structural_tick')}" for a in ARMS if arm(a).height) + ". `parameter` defences "
        "(operand bytes of `lit A {k}` / `lit A {e}` only; reported, not counted): arose in " + ", ".join(
        f"{a} {arose(a, 'first_parameter_tick')}" for a in ARMS if arm(a).height) + "; maintained in " + ", ".join(
        f"{a} {show(a, 'maintained_parameter')}" for a in ARMS if arm(a).height) + "."]
    tn, sn = arm("tierra_n0"), arm("std_n0")
    need = at_least(H17_NEED)
    t_hi = int((tn["par_share_h17"].fill_null(0) > PAR_HI).sum()) if tn.height else 0
    s_lo = int((sn["par_share_h17"].fill_null(0) <= STD_LO).sum()) if sn.height else 0
    te, se = med(tn, "entered_share_h17"), med(sn, "entered_share_h17")
    lines += ["", f"H17 (E015 stage 3 under the fixed edge, read at {H17_TICK:,} from the n0 arms; parasite share of exact "
              f"births in the bin ending at {H17_TICK:,}, entered share of replicator-class deaths in "
              f"({SECOND_HALF:,}, {H17_TICK:,}]):",
              f"- parasite share > {pct(PAR_HI)} in {t_hi} of {tn.height} tierra_n0 seeds [>= {need}], <= {pct(STD_LO)} in "
              f"{s_lo} of {sn.height} std_n0 seeds [>= {need}]: {yn(t_hi >= need and s_lo >= need)}. Median (min-max): "
              f"tierra_n0 {mm(tn, 'par_share_h17')}, std_n0 {mm(sn, 'par_share_h17')} (E015's legacy world: 8-27%).",
              f"- entered share, median over seeds: tierra_n0 {pct(te)} [> {pct(ENTER_T)}], std_n0 {pct(se)} "
              f"[{pct(ENTER_STD[0])}-{pct(ENTER_STD[1])}]: "
              f"{yn(te is not None and se is not None and te > ENTER_T and ENTER_STD[0] <= se <= ENTER_STD[1])} "
              f"(E015's legacy world: 23.5-26.4%)."]
    return lines


def summarize(bdf: pl.DataFrame, runs: pl.DataFrame, n_seeds: int, ticks: int, bin_size: int,
              calib: dict | None) -> str:
    arms = [a for a in ARMS if runs.filter(pl.col("arm") == a).height]
    lines = [f"# E016 defence search: {', '.join(arms)}; {n_seeds} seeds x {ticks:,} ticks, sun {SUN}, bins of "
             f"{bin_size:,}", "",
             "Record: docs/research/experiments/2026-10-13-e016-defence-search.md. Runner: analysis/e016_defence.py "
             "(module docstring for every definition).", ""]
    lines += [calib_text(calib) if calib else "Tax not calibrated yet (no runs/e016/tax.json).", ""]
    lines += predictions(runs, n_seeds)
    lines += ["", "## Defence per seed", "",
              "Screened candidates; complete genomes (structural / parameter; immune / tolerant over both); first birth "
              "of a structural and of a parameter one; maintained structural (longest run of windows >= 1%) and "
              "maintained parameter; the structural set's share of replicator-class exact births per 25,000-tick "
              "window and in the last bin.", "",
              "| arm | seed | candidates | complete (str/par; imm/tol) | first structural | first parameter "
              "| maintained (run) | parameter maintained | structural share per window | end |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    wcols = sorted([c for c in runs.columns if c.startswith("structural_w")], key=lambda c: int(c[12:]))
    for r in runs.sort("arm", "seed").iter_rows(named=True):
        if not r["screened"]:
            lines.append(f"| {r['arm']} | {r['seed']} | not screened | | | | | | | |")
            continue
        lines.append(f"| {r['arm']} | {r['seed']} | {r['candidates']} | {r['complete']} ({r['structural']}/"
                     f"{r['parameter']}; {r['immune']}/{r['tolerant']}) | {f0(r['first_structural_tick'])} "
                     f"| {f0(r['first_parameter_tick'])} | {'yes' if r['maintained'] else 'no'} ({r['longest_windows']}) "
                     f"| {'yes' if r['maintained_parameter'] else 'no'} | "
                     + " ".join(pct(r[c]) if r[c] is not None else "–" for c in wcols)
                     + f" | {pct(r['structural_share_end'])} |")
    lines += ["", "## Per run", "",
              f"Median (min-max) over seeds: parasite share in the last bin, entered share of replicator-class deaths "
              f"after {after(ticks):,}, debit per tick of entered replicator-class deaths (milli-units; cap 32,000), "
              "entered reproducers' offspring per tick over unentered (`entered_cpt_post`) and that over the n0 "
              "partner (`_norm_post`), T05 `qnn_cum` over the defence class and over func_hash, structural and "
              f"parameter shares of census bodies after {after(ticks):,} (mean).", "",
              "| arm | runs | parasite last bin | entered | lost/tick | cpt | cpt norm | qnn class | qnn func "
              "| census structural | census parameter |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in arms:
        x = runs.filter(pl.col("arm") == a)
        lines.append(f"| {a} | {x.height} | {mm(x, 'par_share_last')} | {mm(x, 'entered_share_post')} "
                     f"| {mm(x, 'cycles_lost_per_tick_post', f0)} | {mm(x, 'entered_cpt_post', f2)} "
                     f"| {mm(x, 'entered_cpt_norm_post', f2)} | {mm(x, 'qnn_cum_class', f2)} "
                     f"| {mm(x, 'qnn_cum_func', f2)} | {mm(x, 'census_structural_mean')} "
                     f"| {mm(x, 'census_parameter_mean')} |")
    step = max(1, (10_000 // bin_size))
    lines += ["", "## Per bin", "",
              f"Medians over seeds, every {step * bin_size:,} ticks (all bins in bins.csv): exact births, parasite share, "
              "entered and resident shares of deaths, IP off body, nop share, length p10/p50/p90, structural / "
              "parameter / immune / tolerant share of replicator-class exact births, debit per tick of entered deaths, "
              "`entered_cpt_norm`.", "",
              "| arm | ticks | exact | parasite | entered | resident | IP off | nop | len | structural | parameter "
              "| immune | tolerant | lost/tick | cpt norm |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in arms:
        for k in sorted(bdf["bin"].unique().to_list()):
            if k % step and k != 1:
                continue
            x = bdf.filter((pl.col("arm") == a) & (pl.col("bin") == k))
            if not x.height:
                continue
            lines.append(f"| {a} | {(k - 1) * bin_size:,}-{k * bin_size:,} | {f0(med(x, 'exact'))} | {pct(med(x, 'par_share'))} "
                         f"| {pct(med(x, 'entered_share'))} | {pct(med(x, 'resident_share'))} | {pct(med(x, 'ip_off_share'))} "
                         f"| {pct(med(x, 'nop_share'))} | {f0(med(x, 'len_p10'))}/{f0(med(x, 'len_p50'))}/{f0(med(x, 'len_p90'))} "
                         f"| {pct(med(x, 'structural_share'))} | {pct(med(x, 'parameter_share'))} "
                         f"| {pct(med(x, 'immune_share'))} | {pct(med(x, 'tolerant_share'))} "
                         f"| {f0(med(x, 'cycles_lost_per_tick'))} | {f2(med(x, 'entered_cpt_norm'))} |")
    err = runs.filter(pl.col("measures_error").is_not_null()) if "measures_error" in runs.columns else runs.clear()
    if err.height:
        lines += ["", "T05 measures failed on: " + "; ".join(f"{r['arm']}/s{r['seed']}: {r['measures_error']}"
                                                            for r in err.iter_rows(named=True))]
    return "\n".join(lines)


# ---- lod -------------------------------------------------------------------------------------------------

def region_of(anc: str, pos: int) -> str:
    if anc == "tierra":
        for name, (lo, hi) in TIERRA_REGIONS.items():
            if lo <= pos <= hi:
                return name
    return "other"


def look_back(ancestor: bytes, target: bytes, bodies: dict[str, bytes | None], anc: str) -> list[dict]:
    """Croft's look-back: for each body, which of the target's edits from the
    ancestor it carries (by region), and its own diff to the target."""
    want = lod.edit_script(ancestor, target)
    rows = []
    for who, body in bodies.items():
        if body is None:
            continue
        have = set(lod.edit_script(ancestor, body))
        carried = [e for e in want if e in have]
        regions: dict[str, list[int]] = {}
        for e in want:
            r = regions.setdefault(region_of(anc, e[1]), [0, 0])
            r[1] += 1
            r[0] += e in have
        rest = lod.edit_script(body, target)
        rows.append(dict(who=who, len=len(body), target_edits=lod.format_edits(want), n_target=len(want),
                         carried=lod.format_edits(carried), n_carried=len(carried),
                         missing=lod.format_edits([e for e in want if e not in have]),
                         by_region="; ".join(f"{k} {a}/{b}" for k, (a, b) in sorted(regions.items())),
                         to_target=lod.format_edits(rest), n_to_target=len(rest), bytes_hex=body.hex()))
    return rows


def pair_off(steps: list[dict]) -> set[int]:
    """Indices of steps in break-and-repair pairs (T06 follow-up): a
    deleterious step to a genome with no exact children alone, followed at
    once by a beneficial step from it."""
    paired: set[int] = set()
    i = 0
    while i < len(steps) - 1:
        a, b = steps[i], steps[i + 1]
        if a["effect"] == "deleterious" and a["f_child"] == 0 and b["effect"] == "beneficial" and b["f_parent"] == 0:
            paired |= {i, i + 1}
            i += 2
        else:
            i += 1
    return paired


def lineages(births: pl.DataFrame, complete_raw: set[str], alive: set[int]) -> pl.DataFrame:
    """Every origin of a complete lineage: a body born with a complete genome
    whose executor was not born so. Carriers inherit their executor's origin.
    time_to_loss = last exact birth within the lineage (a carrier child equal
    to its carrier executor's body at divide) minus the origin's birth tick
    (0 with none); censored if a carrier of it is alive at the last census.
    `births`: child, executor, tick, raw_hash, parent_now_hash, sorted by child."""
    origin: dict[int, int] = {}
    st: dict[int, dict] = {}
    rows = births.filter(pl.col("raw_hash").is_in(sorted(complete_raw))).sort("child")
    for child, ex, tick, raw, pnow in rows.select("child", "executor", "tick", "raw_hash", "parent_now_hash").iter_rows():
        o = origin.get(ex)
        if o is None:
            o = child
            st[o] = dict(origin_id=child, origin_tick=tick, executor=ex, raw_hash=raw, carriers=0, exact=0,
                         last_exact=None)
        origin[child] = o
        s = st[o]
        s["carriers"] += 1
        if o != child and raw == pnow:
            s["exact"] += 1
            s["last_exact"] = tick
    live = {origin[i] for i in alive if i in origin}
    out = [dict(**s, time_to_loss=(s["last_exact"] - s["origin_tick"]) if s["last_exact"] is not None else 0,
                censored=o in live) for o, s in st.items()]
    schema = {"origin_id": pl.Int64, "origin_tick": pl.Int64, "executor": pl.Int64, "raw_hash": pl.Utf8,
              "carriers": pl.Int64, "exact": pl.Int64, "last_exact": pl.Int64, "time_to_loss": pl.Int64,
              "censored": pl.Boolean}
    return pl.DataFrame(out, schema=schema, orient="row") if out else pl.DataFrame(schema=schema)


def binned_world(rd: lod.RunData, steps: pl.DataFrame, size: int = BIN) -> pl.DataFrame:
    """T06 follow-up: each step's parent and child genomes in the step's bin
    of `size` ticks, exact children per death relative to every
    replicator-class organism born in that bin (lod.world_fitness for both)."""
    binof = lambda t: max(1, -(-int(t) // size))
    S = steps.rows(named=True)
    pairs = {(s[k], binof(s["tick"])) for s in S for k in ("parent_hash", "child_hash")}
    need = sorted({b for _, b in pairs})
    gw = lod.world_fitness(rd, pairs, size)
    born = rd.births.select("tick", "raw_hash").with_columns(
        b=pl.max_horizontal(pl.lit(1), (pl.col("tick") + size - 1) // size)).filter(pl.col("b").is_in(need))
    if rd.classes is not None:
        rep = {h for h, c in rd.classes.items() if c == "replicator"}
        born = born.filter(pl.col("raw_hash").is_in(sorted(rep)))
    allp = {(h, int(b)) for h, b in born.select("raw_hash", "b").unique().iter_rows()}
    cw = lod.world_fitness(rd, allp, size)
    pool: dict[int, list[float]] = {}
    for (h, b), v in cw.items():
        if v["died"]:
            p = pool.setdefault(b, [0.0, 0])
            p[0] += v["exact_per_death"] * v["died"]
            p[1] += v["died"]
    base_b = {b: (x / n if n else None) for b, (x, n) in pool.items()}
    out = []
    for s in S:
        b = binof(s["tick"])
        row = dict(step=s["step"], bin=b, contemporaries_exact_per_death=base_b.get(b))
        for side in ("parent", "child"):
            v = gw[(s[f"{side}_hash"], b)]
            row[f"bin_born_{side}"] = v["born"]
            row[f"bin_died_{side}"] = v["died"]
            row[f"bin_exact_per_death_{side}"] = v["exact_per_death"]
            c = base_b.get(b)
            row[f"bin_rel_{side}"] = v["exact_per_death"] / c if v["exact_per_death"] is not None and c else None
        out.append(row)
    return pl.DataFrame(out, infer_schema_length=None)


def lod_run(exe: Path, d: Path, arm: str, tax: Tax | None, ref: Ref, ticks_h: int, jobs: int) -> dict | None:
    ddf = read_defence(d)
    sets = defence_sets(ddf)
    if not sets["structural"]:
        return None
    rd = lod.load_run(d)
    comp_raw = set(rd.genomes.filter(pl.col("func_hash").is_in(sorted(sets["structural"])))["raw_hash"].to_list())
    cb = rd.births.filter(pl.col("raw_hash").is_in(sorted(comp_raw))).sort("tick", "child")
    if not cb.height:
        return None
    first = cb.row(0, named=True)
    at = next((t for t in rd.census_ticks if t >= first["tick"]), rd.census_ticks[-1])
    out_dir = d / "lod"
    res = lod.lod(d, at=at, pick=f"id:{first['child']}", harness_ticks=ticks_h, out=out_dir, exe=exe, run=rd,
                  jobs=jobs, flags=tuple(physics(arm, tax)), probe=PROBE[base(arm)], log=lambda *_: None)
    g = res.genomes
    kinds = {r["raw_hash"]: is_defence(r["alone_class"], r["alone_exact"], r["entered_host_exact"],
                                       r["entered_pad_exact"], ref) for r in g.iter_rows(named=True)}
    p_ex = dict(g.select("raw_hash", "entered_pad_exact").iter_rows())
    S = res.steps.rows(named=True)
    paired = pair_off(S)
    wb = binned_world(rd, res.steps) if res.steps.height else None
    steps = res.steps.with_columns(
        paired=pl.Series([i in paired for i in range(len(S))], dtype=pl.Boolean),
        probe_exact_parent=pl.Series([p_ex[s["parent_hash"]] for s in S], dtype=pl.Int64),
        probe_exact_child=pl.Series([p_ex[s["child_hash"]] for s in S], dtype=pl.Int64),
        immune_child=pl.Series([kinds[s["child_hash"]][0] for s in S], dtype=pl.Boolean),
        tolerant_child=pl.Series([kinds[s["child_hash"]][1] for s in S], dtype=pl.Boolean))
    if wb is not None:
        steps = wb.join(steps, on="step", how="left")
    steps.write_csv(out_dir / "e016_steps.csv")
    # Croft's look-back.
    L = res.line.rows(named=True)
    hexes = dict(rd.genomes.select("raw_hash", "bytes_hex").iter_rows())
    body = lambda h: bytes.fromhex(hexes[h]) if h in hexes and hexes[h] else None
    target = body(L[-1]["raw_hash"])
    bodies = {"parent": body(L[-2]["raw_hash"]) if len(L) > 1 else None}
    pnow = L[-1].get("parent_now_hash")
    if len(L) > 1 and pnow and pnow != L[-2]["raw_hash"]:
        bodies["parent_at_divide"] = body(pnow)
    bodies["grandparent"] = body(L[-3]["raw_hash"]) if len(L) > 2 else None
    lb = pl.DataFrame(look_back(bytes.fromhex(HEX[base(arm)]), target, bodies, base(arm)), infer_schema_length=None)
    lb.write_csv(out_dir / "lookback.csv")
    # Time-to-loss.
    last = rd.census_ticks[-1]
    alive = set(lod._scan(d, "orgs").filter(pl.col("tick") == last).select("id").collect()["id"].to_list())
    lin = lineages(rd.births, comp_raw, alive)
    lin.write_csv(out_dir / "lineages.csv")
    un = [s for i, s in enumerate(S) if i not in paired]
    eff = lambda rows, e: sum(1 for s in rows if s["effect"] == e)
    both = [s for s in un if s["f_parent"] > 0 and s["f_child"] > 0]
    kind = ddf.filter(pl.col("func_hash") == rd.genomes.filter(pl.col("raw_hash") == first["raw_hash"])["func_hash"][0])
    kr = kind.row(0, named=True) if kind.height else {}
    fin = lin.filter(~pl.col("censored"))
    return dict(arm=arm, seed=int(d.name[1:]), first_tick=first["tick"], first_id=first["child"],
                first_hash=first["raw_hash"], immune=kr.get("immune"), tolerant=kr.get("tolerant"),
                line_organisms=res.line.height, steps=len(S), paired=len(paired),
                beneficial=eff(un, "beneficial"), neutral=eff(un, "neutral"), deleterious=eff(un, "deleterious"),
                both_have_children_B=eff(both, "beneficial"), both_have_children_D=eff(both, "deleterious"),
                world_rel_last_step=wb["bin_rel_child"][-1] if wb is not None and wb.height else None,
                lookback="; ".join(f"{r['who']}: {r['n_carried']}/{r['n_target']} ({r['by_region']})"
                                   for r in lb.iter_rows(named=True)) if lb.height else None,
                origins=lin.height, origins_censored=int(lin["censored"].sum()) if lin.height else 0,
                ttl_median=fin["time_to_loss"].median() if fin.height else None,
                ttl_max=fin["time_to_loss"].max() if fin.height else None,
                first_origin_ttl=lin["time_to_loss"][0] if lin.height else None,
                first_origin_censored=lin["censored"][0] if lin.height else None, seconds=round(res.seconds, 1))


def lod_summary(rows: list[dict]) -> str:
    lines = ["# E016 lod stage: lines of descent to the first structural complete genome", "",
             "T06's line (analysis/lod.py) per run with a structural complete genome (§7.1; `parameter` defences are "
             "not followed), harness under the arm's flags with the arm's "
             "probe. Steps counted after pairing off break-and-repair pairs (B / n / D of the rest; of those between "
             "genomes that both have exact children alone, B and D). World column: the last step's child in its "
             "2,500-tick bin, exact children per death over contemporaries'. Look-back: edits of the first complete "
             "genome from the ancestor carried by its parent and grandparent (tierra by region). Time-to-loss over "
             "uncensored lineage origins (median, max); the first origin's own.", "",
             "| arm | seed | first complete (tick, kind) | line | steps (paired) | B/n/D | both-children B/D | world rel "
             "| look-back | origins (censored) | ttl median/max | first origin ttl |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        kind = "/".join(k for k in ("immune", "tolerant") if r[k]) or "?"
        lines.append(f"| {r['arm']} | {r['seed']} | {r['first_tick']:,}, {kind} | {r['line_organisms']} "
                     f"| {r['steps']} ({r['paired']}) | {r['beneficial']}/{r['neutral']}/{r['deleterious']} "
                     f"| {r['both_have_children_B']}/{r['both_have_children_D']} | {f2(r['world_rel_last_step'])} "
                     f"| {r['lookback']} | {r['origins']} ({r['origins_censored']}) | {f0(r['ttl_median'])}/{f0(r['ttl_max'])} "
                     f"| {f0(r['first_origin_ttl'])}{' (censored)' if r['first_origin_censored'] else ''} |")
    if not rows:
        lines.append("No run has a structural complete genome.")
    return "\n".join(lines)


# ---- replay ------------------------------------------------------------------------------------------------

Replay = tuple[str, int, int, int, int]  # (kind, source seed, snapshot tick, new seed, to tick)


def replay_job_dir(out: Path, arm: str, job: Replay) -> Path:
    """A founder run depends on the new seed only, so every source seed of
    the arm shares it."""
    kind, seed, _, new_seed, _ = job
    return out / "replay" / arm / "founder" / f"r{new_seed}" if kind == "founder" else replay_dir(out, arm, seed, new_seed)


def replay_one(exe: Path, out: Path, arm: str, job: Replay, tax: Tax | None, ref: Ref, jobs: int, force: bool,
               compress: bool) -> dict:
    """Run (or find), classify and screen one replay. `founder`: a plain run
    with the arm's flags and `--seed S` to FOUNDER_TO; otherwise
    `--replay-from` the source run's snapshot, inflated to a temporary file
    for the length of the run."""
    kind, seed, snap, new_seed, to_tick = job
    d = replay_job_dir(out, arm, job)
    founder = kind == "founder"
    rep = None if founder else dict(tick=snap, reseed=new_seed)
    ticks = to_tick if founder else None
    if force or not has(d, "classes.csv"):
        mj = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
        if force or not has(d, "genomes.csv") or mj.get("ticks_run") is None:
            if d.exists():
                shutil.rmtree(d)
            d.parent.mkdir(parents=True, exist_ok=True)
            with open(d.parent / f"r{new_seed}.stdout", "w", encoding="utf-8", newline="") as f:
                if founder:
                    subprocess.run(world_cmd(exe, d, arm, new_seed, to_tick, tax, False), stdout=f,
                                   stderr=subprocess.STDOUT, check=True)
                else:
                    with snapshot_file(run_dir(out, arm, seed), snap) as src:
                        subprocess.run(replay_cmd(exe, src, d, arm, new_seed, to_tick, tax), stdout=f,
                                       stderr=subprocess.STDOUT, check=True)
        check_meta(d, arm, ticks, tax, False, rep)
        if not (d / "genomes.csv").exists():
            gunzip_verified(d / "genomes.csv.gz")
        subprocess.run(classify_cmd(exe, d, arm, tax), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=True)
    else:
        check_meta(d, arm, ticks, tax, False, rep)
    df = read_defence(d) if (d / "defence.csv").exists() and not force else screen_run(exe, d, arm, tax, ref,
                                                                                        HARNESS_TICKS, jobs)
    if compress:
        compress_run(d)
    c = screen_counts(df)
    return dict(dir=str(d), **c, arose=c["first_structural_tick"] is not None)


def replay_plan(runs: pl.DataFrame, arm: str, n: int = len(REPLAY_SEEDS),
                ticks: int = TICKS) -> tuple[list[Replay], list[str]]:
    """The arm's replays (§3 with §7.3) and notes. A seed whose first
    structural complete genome is born at t: from the snapshot at the last
    multiple of 2,500 below t to t + 50,000 (`potentiation`), or, with no such
    snapshot (t <= 2,500), plain runs from the founder to FOUNDER_TO
    (`founder`). Background from the 25,000 snapshot of the seeds with none,
    to 100,000 (none for runs shorter than 25,000 ticks: smoke). `n` < 10 for
    a smoke run only."""
    new_seeds = REPLAY_SEEDS[:n]
    x = runs.filter(pl.col("arm") == arm).sort("seed")
    plan: list[Replay] = []
    notes = []
    for seed, t in (x.filter(pl.col("first_structural_tick").is_not_null())
                    .select("seed", "first_structural_tick").iter_rows()):
        s = snapshot_tick(t)
        if s == 0:
            notes.append(f"{arm}/s{seed}: first structural complete genome at tick {t:,}, before the first snapshot; "
                         f"replayed from the founder (tick 0) to {FOUNDER_TO:,}: the arising rate, not potentiation")
            plan += [("founder", seed, 0, k, FOUNDER_TO) for k in new_seeds]
        else:
            plan += [("potentiation", seed, s, k, t + REPLAY_AFTER) for k in new_seeds]
    bg = x.filter(pl.col("first_structural_tick").is_null() & pl.col("screened"))["seed"].to_list()
    if ticks < BACKGROUND_FROM:
        notes.append(f"{arm}: runs of {ticks:,} ticks have no {BACKGROUND_FROM:,} snapshot; no background replays")
    elif bg:
        plan += [("background", bg[i % len(bg)], BACKGROUND_FROM, k, BACKGROUND_TO) for i, k in enumerate(new_seeds)]
    else:
        notes.append(f"{arm}: no screened seed without a structural complete genome; no background replays")
    return plan, notes


def screened_runs(out: Path, arms: list[str], seeds: list[int]) -> pl.DataFrame:
    rows = []
    for a in arms:
        for s in seeds:
            df = read_defence(run_dir(out, a, s))
            if df is not None:
                rows.append(dict(arm=a, seed=s, screened=True, **screen_counts(df)))
    schema = {"arm": pl.Utf8, "seed": pl.Int64, "screened": pl.Boolean, "first_structural_tick": pl.Int64}
    return pl.DataFrame(rows, infer_schema_length=None) if rows else pl.DataFrame(schema=schema)


def replay_summary(df: pl.DataFrame, notes: list[str]) -> str:
    lines = ["# E016 replay stage: potentiation (§3, §7.3)", "",
             f"`potentiation`: a run whose first structural complete genome is born at t, replayed from the snapshot "
             f"at the last multiple of {STATE_EVERY:,} below t with new seeds {REPLAY_SEEDS[0]}-{REPLAY_SEEDS[-1]}, to "
             f"t + {REPLAY_AFTER:,}. `founder`: t <= {STATE_EVERY:,}, no snapshot below it; plain runs from tick 0 with "
             f"the new seeds to {FOUNDER_TO:,}, shared by every such seed of the arm: the arising rate, not "
             f"potentiation. `background`: replays from the {BACKGROUND_FROM:,} snapshot of the arm's seeds with no "
             f"structural complete genome, to {BACKGROUND_TO:,}. A replay counts if a structural complete genome (its "
             "own screen) is born in it.", "",
             "| arm | kind | source | snapshot | to tick | replays | with a structural complete genome |",
             "|---|---|---|---|---|---|---|"]
    if df.height:
        g = (df.with_columns(src=pl.when(pl.col("kind") == "background").then(pl.lit("background seeds"))
                             .otherwise(pl.format("s{}", pl.col("seed"))))
             .group_by("arm", "kind", "src", "snapshot", "to_tick").agg(n=pl.len(), arose=pl.col("arose").sum())
             .sort("arm", "kind", "src"))
        for r in g.iter_rows(named=True):
            lines.append(f"| {r['arm']} | {r['kind']} | {r['src']} | {r['snapshot']:,} | {r['to_tick']:,} | {r['n']} "
                         f"| {r['arose']} |")
    lines += [""] + [f"- {n}" for n in notes]
    return "\n".join(lines)


# ---- driver --------------------------------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["world", "calibrate", "screen", "analyse", "lod", "replay"])
    ap.add_argument("--evo-bin", help="evo-core binary (default $EVO_BIN, else evo-core/target/release; not built)")
    ap.add_argument("--out", type=Path, default=OUT, help="output root (default runs/e016)")
    ap.add_argument("--arms", help="comma list (default: world the first four, then every arm present)")
    ap.add_argument("--seeds", type=int, default=SEEDS, help="seeds 1..N (default 30)")
    ap.add_argument("--ticks", type=int, default=TICKS, help="run length (other than 250,000 only with --smoke)")
    ap.add_argument("--bin", type=int, default=BIN, help="analyse: bin size")
    ap.add_argument("--harness-ticks", type=int, default=HARNESS_TICKS)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 8, help="parallel runs or harness calls")
    ap.add_argument("--analyse-jobs", type=int, default=4, help="analyse: runs in parallel (memory-bound)")
    ap.add_argument("--force", action="store_true", help="redo what exists")
    ap.add_argument("--no-compress", action="store_true")
    ap.add_argument("--no-measures", action="store_true", help="analyse: skip T05's measures")
    ap.add_argument("--no-nbhd", action="store_true", help="screen: skip the neighbourhood baseline")
    ap.add_argument("--nbhd-dir", type=Path, default=NBHD, help="screen: E015 stage 1 files")
    ap.add_argument("--smoke", action="store_true", help="a smoke run: allows --no-snapshots and other --ticks; needs "
                                                         "--out away from runs/e016")
    ap.add_argument("--no-snapshots", action="store_true",
                    help="world: drop --state-every; other stages: the runs were made so (with --smoke only)")
    ap.add_argument("--replays", type=int, default=len(REPLAY_SEEDS), help="replay: replays per source (10; "
                                                                          "fewer with --smoke only)")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):  # a Windows console may not encode the record's characters
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    t_all = time.time()
    out = a.out.resolve()
    if a.smoke and out == OUT.resolve():
        raise SystemExit("--smoke writes elsewhere: give --out (e.g. runs/e016_smoke)")
    if a.no_snapshots and not a.smoke:
        raise SystemExit("--no-snapshots is for smoke runs only (--smoke): E016's world needs its snapshots (§2)")
    if a.replays != len(REPLAY_SEEDS) and not a.smoke:
        raise SystemExit(f"--replays {a.replays}: the record has {len(REPLAY_SEEDS)}; fewer need --smoke")
    if a.ticks != TICKS and not a.smoke:
        raise SystemExit(f"--ticks {a.ticks}: the record's runs are {TICKS:,} ticks; other lengths need --smoke")
    if a.no_snapshots:
        print("!" * 78 + "\nWARNING: --no-snapshots: these runs have no state/ snapshots and cannot be replayed. "
              "Smoke only; never E016's data.\n" + "!" * 78, file=sys.stderr, flush=True)
    snapshots = not a.no_snapshots
    seeds = list(range(1, a.seeds + 1))
    tax = load_tax(out)
    arms = [x.strip() for x in a.arms.split(",")] if a.arms else None
    for x in arms or []:
        if x not in ARMS:
            raise SystemExit(f"unknown arm {x} (one of {', '.join(ARMS)})")

    if a.stage == "calibrate":
        c = run_calibrate(out, seeds, a.ticks, a.force)
        print(calib_text(c))
        print("Record F, r and P in the experiment file before launching tierra_tax.")
        return

    present = [x for x in ARMS if (out / x).is_dir()]
    exe = None
    if a.stage in ("world", "screen", "lod", "replay"):
        exe = evo_bin(a.evo_bin)
        check_binary(exe)

    if a.stage == "world":
        arms = arms or FIRST_ARMS
        if "tierra_tax" in arms and tax is None:
            raise SystemExit("tierra_tax needs the calibration: run `calibrate` after tierra_n0 and tierra_t50")
        if snapshots:
            require_snapshots(exe)
        if tax and "tierra_tax" in arms:
            print(f"tierra_tax: --cycle-tax-pct {tax[0]} --cycle-tax-frac {tax[1]!r} ({out / 'tax.json'})", flush=True)
        jobs = [(x, s) for x in arms for s in seeds]
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda j: run_world(exe, out, j[0], j[1], a.ticks, tax, snapshots, a.force,
                                                  not a.no_compress), jobs):
                print(msg, flush=True)
        print(f"world: {len(jobs)} runs, {time.time() - t_all:.0f} s")
        return

    arms = arms or present
    if a.stage == "screen":
        if not a.no_nbhd:
            nbhd_screen(exe, out, arms or FIRST_ARMS, tax, a.harness_ticks, a.jobs, a.force, a.nbhd_dir)
        rows = []
        for x in arms:
            ref = None
            for s in seeds:
                d = run_dir(out, x, s)
                if not has(d, "classes.csv"):
                    continue
                check_meta(d, x, a.ticks, tax, snapshots)
                if (d / "defence.csv").exists() and not a.force:
                    df = read_defence(d)
                else:
                    ref = ref or reference(exe, x, tax, a.harness_ticks)
                    t0 = time.time()
                    df = screen_run(exe, d, x, tax, ref, a.harness_ticks, a.jobs)
                    print(f"screen {x}/s{s}: {df.height} candidates, {time.time() - t0:.0f} s", flush=True)
                rows.append(dict(arm=x, seed=s, **screen_counts(df)))
        if rows:
            sc = pl.DataFrame(rows, infer_schema_length=None)
            sc.write_csv(out / "screen.csv")
            for r in sc.group_by("arm").agg(
                    runs=pl.len(), with_structural=(pl.col("structural") > 0).sum(),
                    with_parameter=(pl.col("parameter") > 0).sum(), structural=pl.col("structural").sum(),
                    parameter=pl.col("parameter").sum()).sort("arm").iter_rows(named=True):
                print(f"screen {r['arm']}: {r['runs']} runs; with a structural complete genome {r['with_structural']} "
                      f"({r['structural']} func_hashes), with a parameter one {r['with_parameter']} "
                      f"({r['parameter']})", flush=True)
        print(f"screen: {time.time() - t_all:.0f} s")
        return

    if a.stage == "analyse":
        jobs = [(out, x, s, a.ticks, a.bin, tax, snapshots, not a.no_measures) for x in arms for s in seeds
                if has(run_dir(out, x, s), "classes.csv")]
        if not jobs:
            raise SystemExit(f"no finished runs under {out}")
        with ProcessPoolExecutor(max(1, a.analyse_jobs)) as ex:
            res = list(ex.map(_analyse_job, jobs))
        bdf = pl.DataFrame([b for bins, _ in res for b in bins], infer_schema_length=None)
        runs = pl.DataFrame([s for _, s in res], infer_schema_length=None)
        bdf, runs = add_cpt_norm(bdf, runs)
        bdf.write_csv(out / "bins.csv")
        runs.write_csv(out / "runs.csv")
        calib = json.loads((out / "tax.json").read_text()) if (out / "tax.json").exists() else None
        text = summarize(bdf, runs, len(seeds), a.ticks, a.bin, calib)
        (out / "summary.md").write_text(text + "\n", encoding="utf-8", newline="")
        print(text)
        print(f"analyse: {len(jobs)} runs, {time.time() - t_all:.0f} s")
        return

    if a.stage == "lod":
        rows = []
        for x in arms:
            ref = None
            for s in seeds:
                d = run_dir(out, x, s)
                if read_defence(d) is None or not defence_sets(read_defence(d))["structural"]:
                    continue
                check_meta(d, x, a.ticks, tax, snapshots)
                ref = ref or reference(exe, x, tax, a.harness_ticks)
                r = lod_run(exe, d, x, tax, ref, a.harness_ticks, a.jobs)
                if r:
                    rows.append(r)
                    print(f"lod {x}/s{s}: line of {r['line_organisms']}, {r['steps']} steps, {r['seconds']} s", flush=True)
        if rows:
            pl.DataFrame(rows, infer_schema_length=None).write_csv(out / "lod_seeds.csv")
        text = lod_summary(rows)
        (out / "lod_summary.md").write_text(text + "\n", encoding="utf-8", newline="")
        print(text)
        return

    if a.stage == "replay":
        require_replay(exe)
        runs = screened_runs(out, arms, seeds)
        rows, notes = [], []
        for x in arms:
            plan, nts = replay_plan(runs, x, a.replays, a.ticks)
            notes += nts
            if not plan:
                continue
            ref = reference(exe, x, tax, a.harness_ticks)
            uniq = list({str(replay_job_dir(out, x, j)): j for j in plan}.values())  # founder runs are shared
            # Replays run in parallel; each one's screen uses one harness thread.
            with ThreadPoolExecutor(a.jobs) as ex:
                done = dict(zip([str(replay_job_dir(out, x, j)) for j in uniq],
                                ex.map(lambda j: replay_one(exe, out, x, j, tax, ref, 1, a.force, not a.no_compress),
                                       uniq)))
            for j in plan:
                kind, seed, snap, new_seed, to_tick = j
                r = done[str(replay_job_dir(out, x, j))]
                rows.append(dict(arm=x, kind=kind, seed=seed, new_seed=new_seed, snapshot=snap, to_tick=to_tick, **r))
                print(f"replay {x} {kind} s{seed}/r{new_seed}: {r['structural']} structural complete", flush=True)
        df = pl.DataFrame(rows, infer_schema_length=None) if rows else pl.DataFrame()
        if rows:
            df.write_csv(out / "replay.csv")
        text = replay_summary(df, notes)
        (out / "replay_summary.md").write_text(text + "\n", encoding="utf-8", newline="")
        print(text)


if __name__ == "__main__":
    main()
