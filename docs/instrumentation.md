# Instrumentation spec (Phase 2, first cut)

Status: spec written 2026-10-03, built the same day; first use is E003
(`research/experiments/2026-10-03-e003-crash-diagnosis.md`). Implements the
diagnostic subset of PLAN.md §7. The first question it has to answer comes
from the E002 post-hoc check: in a population crash, what kills the
replicators while broken-loop absorbers survive?

Out of scope for this cut: snapshots and replay from a mid-run tick, the
standard ALife phylogeny export, Bedau–Packard and MODES statistics, and an
interactive viewer. The files below are the raw input all of those need.

## Ground rules

- Instrumentation never draws from the PRNG and never changes simulation
  state. Counters are written by the simulation; everything else reads it.
  A test checks that a run with full recording and a run without it end in
  the same state hash.
- The stdout census line of the CLI stays byte-for-byte as it was, so
  `analysis/e002_dispersal.py` keeps working.
- Energy in output files is in milli-units (integers), column suffix `_m`.
  1 energy unit = 1,000 milli-units (`config.rs`).
- Hashes are FNV-1a 64-bit, written as 16 lowercase hex digits.

## Two genome hashes

- `raw_hash`: FNV-1a of the body bytes. This is the existing `genome_hash`.
- `func_hash`: FNV-1a of the canonical form. Canonicalization parses the
  bytes linearly from offset 0 and rewrites each instruction byte to one
  encoding per meaning: register ops keep `mod & 3`; `self` keeps
  `min(mod, 2)`; ops that ignore the modifier get modifier 0; every
  unassigned opcode becomes `pad` (byte 0). A `lit` operand byte is kept
  verbatim. Two genomes with the same `func_hash` behave identically unless
  the genome reads its own bytes as data or jumps into a `lit` operand.

Genotype counts in the census use raw hashes (as Tierra did); grouping by
`func_hash` is a query on top.

## Simulation-side counters

`Org.stats: OrgStats`, cumulative over the organism's life:

| field | meaning |
|---|---|
| `born_with_m` | energy at birth (seed energy or endowment) |
| `executed` | instructions executed (moved from `Org.executed`) |
| `absorbs` | `absorb` ops executed |
| `absorb_gain_m` | energy gained by `absorb` |
| `absorb_short` | absorbs that got less than a full ration because the pool was short |
| `absorb_capped` | absorbs that got less than a full ration because the store was near cap |
| `copies` | `copy` ops executed |
| `reads_foreign` | `load`/`copy` reads of a byte owned by another organism |
| `exec_foreign` | instructions executed at an address owned by another organism |
| `exec_unowned` | instructions executed at a free or debris address |
| `writes_blocked` | writes refused by write protection |
| `range_faults` | reads or writes outside locality |
| `allocs_ok`, `allocs_fail` | `alloc` outcomes |
| `divides_ok`, `divides_fail` | `divide` with and without a pending region |
| `endowed_m` | energy given to children |
| `spent_m` | energy charged for instructions |
| `upkeep_m` | energy paid as upkeep |
| `starved_ticks` | ticks in which it paid upkeep but could not afford one instruction |
| `last_divide_tick` | tick of the last successful `divide`, -1 if none |
| `max_energy_m` | highest energy held |

Ledger identity (tested): for a living organism,
`energy = born_with + absorb_gain - spent - upkeep - endowed`.

`Patch` gains two cumulative counters: `absorbed` (energy taken by
absorbs) and `overflow` (income lost to the cap).

## Events

`Event::Birth` gains `start`, `parent_now_hash` (raw hash of the
executor's current body bytes at the moment of `divide`) and `source_hash`
(birth `raw_hash` of the copy source organism, 0 if the source was free
space or debris). `parent_now_hash != parent_hash` means the executor's
body had changed since its birth, so a child can differ from its parent's
birth genome with zero copy errors.

`Event::Death` gains `len`, `start`, `pending_len` (length of a
half-built child region at death, 0 if none), `ip_off` (IP minus body
start, wrapped), `op_at_ip`, `energy_m` (energy before the failed upkeep
charge), `pool_m` (pool of the patch holding the body start), `birth_hash`,
`now_hash` (current body bytes), and the full `stats`.

## Run directory (`--out DIR`)

All CSV with a header row. Written by `record.rs` (`Recorder`).

- `meta.json`: every `Config` field, ticks requested, ticks run, census
  interval, ancestor K and E, crate version, git commit and dirty flag
  (captured at build time by `build.rs`).
- `births.csv`: `tick,child,executor,source,start,len,copy_errors,slips,endowment_m,raw_hash,parent_hash,parent_now_hash,source_hash`
- `deaths.csv`: `tick,id,cause,age,offspring,len,start,pending_len,ip_off,op_at_ip,energy_m,pool_m,birth_hash,now_hash,` then every `OrgStats` field.
- `census.csv` (every census tick): `tick,now_hash,count`. Hash of current body bytes.
- `orgs.csv` (every census tick, one row per living organism): `tick,id,parent,birth_tick,start,len,pending_len,energy_m,ip_off,op_at_ip,birth_hash,now_hash,offspring,` then every `OrgStats` field.
- `patches.csv` (every census tick): `tick,patch,pool_m,orgs,absorbed_m,overflow_m`. `orgs` counts living body starts in the patch; `absorbed_m` and `overflow_m` are totals since the previous census row.
- `genomes.csv` (written at the end): `raw_hash,func_hash,len,first_tick,first_id,origin,parent_hash,bytes_hex,disasm`. One row per raw hash ever seen. `origin` is `seed`, `birth`, or `somatic`. For `birth`, `parent_hash` is the executor's body at `divide` (`parent_now_hash`), so a lineage runs birth genome, then somatic variant, then child. A `somatic` row is a body that changed after birth, seen at a census or at a `divide`; its `parent_hash` is that body's birth hash. Under parasitism (copy source not the executor) the lineage parent is still the executor; `births.csv` has `source_hash` for other rules. A body's state at death is not stored (its bytes can be reused within the tick), so `deaths.now_hash` may be missing from this file.

`--census N` sets the census interval (default: the `--report` interval).
Event rows are written as they happen; the in-memory event list is drained
after each tick so long runs do not grow memory.

## Classifier (`--classify DIR`)

Reads `DIR/genomes.csv`, runs each genome alone in a clean world (noise
off, 100 units of seed energy, children removed every tick; the harness
from `ancestor_pays_for_itself`) for `--harness-ticks` ticks (default
3,000), and writes `DIR/classes.csv`. The energy and `alloc` physics are
whatever the command line gives (`--patch`, `--sun`, `--alloc-far`,
`--absorb-prop`; default physics if none); noise flags are ignored. With
`--classes-out NAME` the file is `DIR/NAME` instead, so one run can carry
both a default-physics `classes.csv` and a world-physics
`classes_world.csv` (E005, 2026-10-06). Columns:

`raw_hash,class,births,exact_births,first_birth_tick,alive,final_energy_m,executed,absorbs`

| class | rule |
|---|---|
| `replicator` | at least 2 children whose bytes equal the parent's |
| `inexact` | at least 1 child, but fewer than 2 exact ones |
| `loafer` | no children, alive at the end |
| `dies` | no children, dead at the end |

This labels genomes by test, not by eye. It says what a genome does alone,
with full pools, from a fresh start (IP at the body start, registers zero).
A `replicator` can still fail in a crowded, drained patch, and a living
organism can be stuck in a state a fresh start never reaches (E003: most
long-lived absorb-loopers are labeled `dies`). `report.py` therefore also
shows each survivor's activity over the last census interval.

## Analysis (`analysis/`)

- `evo_run.py`: `load(run_dir)` returns polars frames for every file above
  (and `classes.csv` if present) with hashes as strings and energy columns
  also available in units.
- `report.py RUN_DIR [--classify]`: optional classify step (calls the
  binary), a text summary, and PNGs in `RUN_DIR/report/`:
  population over time by class, a space-time plot of the ring (position
  vs tick, bodies colored by class), patch pools over time, and deaths by
  age and signature. The text summary answers the crash question directly:
  deaths grouped by birth class and signature, with counts, ages, peak
  energy, short-absorb share and `alloc` failures. Signatures, in order:
  `stillborn` (born with 0 energy), `mid_copy` (holding a half-built
  child), `newborn` (never divided), `after_dividing`. Births are typed
  `exact` (child equals the executor's body at `divide`), `mutant`, or
  `stillborn`.
- `explore.py` (added after this spec): a marimo notebook over the same
  files, with the same derived tables and palette. Interactive, but not
  the full viewer PLAN.md §7 has in mind (`analysis/README.md`).

## Acceptance

1. `cargo test` passes, including the new tests: determinism (same seed
   twice, identical event stream and state hash; with and without a
   `Recorder`, identical state hash), per-organism ledger identity,
   `func_hash` collapses register-alias encodings and separates a real
   mutation, and classifier labels for the ancestor (`replicator`), a
   broken-exit mutant (`loafer`), and a lone `pad` (`dead`).
2. The CLI stdout census for seed 1, 2,000 ticks is unchanged from the
   pre-instrumentation binary.
3. Speed at default config, seed 1, 20,000 ticks: within 15% of the
   pre-instrumentation binary with `--out` off.
4. `report.py` on a control run (seed 1, 50,000 ticks) prints the death
   signature table and writes the four plots.

Results 2026-10-03: `cargo test` 22 passed (18 unit, 4 integration).
Stdout for seed 1, 2,000 ticks byte-identical to the df11a9a binary, and
for seeds 1–3 at 50,000 ticks. Seed 2, 50,000 ticks: 29–30 M instructions/s
before, 39–40 M after (draining the event list each tick), 37.7 M with
`--out` and a census every 100 ticks. `report.py` on control seed 1 prints
the tables and writes the four plots.

Review 2026-10-03 (second Opus pass over the diff): stdout identity, PRNG
isolation, counter semantics, CSV column order and the ledger all checked
out. Fixed from its findings: `evo_run.py` failed on header-only CSVs;
`report.py` listed the last non-empty census as "alive at end" for extinct
runs, and drew the births bars one interval late; `--census 0` panicked;
the build's dirty flag ignored new untracked files; a reused `--out`
directory kept a stale `classes.csv` (now deleted on create); an exact
child of a body that changed again later in the same tick could get a
self-loop parent link (the child's bytes now stand in for the parent's).
Also fixed, older than this work: pending-region membership used
`wrap(a.wrapping_sub(start))`, which is wrong when the world size is not a
power of two; it only affected `copy_errors`, `slips` and copy-source
attribution in births, never the physics, and no run so far used such a
world.
