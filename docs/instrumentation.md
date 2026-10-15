# Instrumentation spec (Phase 2, first cut)

Status: spec written 2026-10-03, built the same day; first use is E003
(`research/experiments/2026-10-03-e003-crash-diagnosis.md`). Implements the
diagnostic subset of PLAN.md §7. The first question it has to answer comes
from the E002 post-hoc check: in a population crash, what kills the
replicators while broken-loop absorbers survive?

Out of scope for this cut: snapshots and replay from a mid-run tick, the
standard ALife phylogeny export, Bedau–Packard and MODES statistics, and an
interactive viewer. The files below are the raw input all of those need.
(Snapshots and replay were added on 2026-10-13 by T04; see "Snapshots
and replay" below.)

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
| `paid_for_others_m` | energy charged for instructions other organisms executed in its body (`charge_owner`, E008: the whole cost; `--charge-owner-pct N`, E009: the owner's share, `floor(cost × N / 100)` or its whole store if less; `--transfer-pct N`, E010: what it lost to the executor, `floor(cost × N / 100)` or its whole store if less, whether or not the executor could keep it); included in `spent_m`, 0 with all three flags off |
| `paid_by_others_m` | energy other organisms (the owners of the bytes it ran) paid for its instructions, the counterpart of `paid_for_others_m` (2026-10-08, E009); not included in `spent_m`, which holds only what it paid itself; 0 with both owner-pays flags off, and always 0 under `--transfer-pct` (the executor pays its own cost there). Summed over all organisms it equals the sum of `paid_for_others_m` under the owner-pays rules |
| `gained_from_others_m` | energy received from the owners of the bytes it ran under `--transfer-pct N` (2026-10-08, E010): the owner's loss, capped by the room left below its store cap after it paid its own cost; what does not fit is dissipated (`energy_out`). 0 without the flag. Summed over all organisms it is at most the sum of `paid_for_others_m` |
| `writes_foreign` | writes (`store`, `copy`) that landed on a byte owned by another living organism, its body or pending region (2026-10-12, E012). Possible only with `--no-protect`; with protection on the same writes are refused and counted in `writes_blocked`, and this is 0 |
| `overwritten` | writes by other organisms that landed on this organism's body or pending region, the victim-side counterpart of `writes_foreign` (2026-10-12, E012). Summed over all organisms the two agree (tested); 0 with protection on |
| `cycles_lost_m` | execution budget debited from this organism by intruders' instructions under `--cycle-theft-pct N` (2026-10-13, E014): `floor(cost × N / 100)` per instruction another organism ran on its body or pending region, in the budget's own milli-units, cumulative. Not energy: it is in no ledger. 0 without the flag |
| `cycles_taken_m` | budget this organism's instructions debited from the owners of the bytes it ran under `--cycle-theft-pct N`, the counterpart of `cycles_lost_m`. Summed over all organisms the two agree (tested); 0 without the flag |
| `cycles_taxed_m` | budget debited by the random cycle tax, `--cycle-tax-pct P` with `--cycle-tax-frac F` (2026-10-13, E014's control): `floor(cap × P / 100)` per taxed tick, less if theft debt already took most of that tick's cap; and by the lifelong tax, `--cycle-tax-lifelong F P` (2026-10-15, T10): `floor(cap × P / 100)` every tick of a body taxed for life, after the theft debt and the random tax, again never more than they left. 0 without either flag |
| `exec_by_others` | instructions other organisms executed at bytes this organism owned (body or pending region), the victim-side counterpart of `exec_foreign` (2026-10-13, E014; the last column). Counted whatever the flags, so "entered" can be read in a world with no cost rule. Summed over all organisms it equals the sum of `exec_foreign` (tested, with and without theft) |

Ledger identity (tested): for a living organism, and for a dead one with
the `energy` of its death row,
`energy = born_with + absorb_gain + gained_from_others - spent - upkeep - endowed`.
It holds under `--charge-owner` and `--charge-owner-pct N` because each
unit an owner pays for an intruder is in the owner's `spent_m`, not the
intruder's (tested at N = 50), and under `--transfer-pct N` because the
owner's loss is in its `spent_m` and the executor's receipt in its
`gained_from_others_m` (tested at N = 150). Runs before E010 have no
`gained_from_others_m` column; it was 0 in all of them. Runs before
2026-10-12 have no `writes_foreign` or `overwritten` column; every run
before E012 had protection on, so both were 0. Runs before 2026-10-13
have no `cycles_lost_m`, `cycles_taken_m`, `cycles_taxed_m` or
`exec_by_others` column; the first three were 0 in all of them, and
`exec_by_others` was not recorded (the executor side, `exec_foreign`,
was).

`--transfer-pct N` (`Config.transfer_pct`, E010, default 0): the
executor pays its own full cost for every instruction, as with no flag
(same affordability check and tick budget); then, if the byte at IP is
owned by a living organism other than the executor, that owner loses
`floor(cost × N / 100)` (or its whole store if less) and the executor
gains it up to its store cap. Debris, free bytes and dead owners transfer
nothing. N = 0 is bit-identical to the run without the flag. It cannot
be combined with `--charge-owner` or a non-zero `--charge-owner-pct`
(the CLI exits with an error; `Sim::new` panics).

`--cycle-theft-pct N` (`Config.cycle_theft_pct`, E014, 0–100, default 0):
energy is matter and is conserved; the per-tick cap is time, the
organism's share of the machine. When an organism executes an
instruction whose byte at IP is owned by a living organism other than
itself, it pays the energy exactly as with no flag, and the owner's
execution budget is debited `floor(cost × N / 100)` milli-units, where
`cost` is the instruction's full price (search and `alloc` extras
included). The debit is added to the owner's `Org.cycle_debt` and taken
from its budget at the start of its next turns, after upkeep, at most
one cap per tick; the rest carries over. An owner that owes a cap or more
pays upkeep and runs nothing that tick (a `starved_ticks` tick), so a host
under heavy intrusion can starve slowly through upkeep; that is reported,
not prevented. The executor's own budget is debited by its own charge
only. Debris, free bytes and dead owners debit nothing; a pending
region's bytes belong to the organism that allocated it. Energy is never
touched and the PRNG is not drawn; `cycle_debt` is in `Sim::state_hash`.
N = 0 is bit-identical to the run without the flag (tested). Its matched
control, the random cycle tax (`--cycle-tax-pct P`, `--cycle-tax-frac F`,
`Config.cycle_tax_pct` and `cycle_tax_frac`, 0–100 and 0–1, defaults 0
and 1): each tick, after upkeep and any theft debit, each living
organism with probability F loses `floor(cap × P / 100)` of that tick's
budget (less if the debit left less). F = 1 taxes every organism every
tick with no PRNG draw; 0 < F < 1 draws one `chance(F)` per organism per
tick in the shuffled order (organisms killed by upkeep that tick draw
nothing); with P = 0 the stream is unchanged. The three flags combine
with each other and with any energy rule.

`--cycle-tax-lifelong F P` (`Config.cycle_tax_life_frac` and
`cycle_tax_life_pct`, T10, 2026-10-15, F 0–1 and P 0–100, defaults 0):
the control shaped like the theft. When an organism is created
(`Sim::seed`, which the founder, `--founder`, `--inject` and every birth
at `divide` go through) one `chance(F)` makes it taxed for life
(`Org.taxed_for_life`); a body taxed for life loses `floor(cap × P /
100)` of its budget every tick it runs, after upkeep, the theft debit
and the random tax (never more than they left), counted in
`cycles_taxed_m`. The state is not inherited: each child draws for
itself. Physical reading: a body born into a slow slot of the machine
that stays there, the control for a body born next to a parasite that
stays entered. F = 0 or P = 0 taxes nobody and draws nothing, so the run
is bit-identical to no flag (tested); F = 1 taxes every body with no
draw. `taxed_for_life` is in `Sim::state_hash` (only when set, so a
world with no taxed body hashes as before the field) and in the
snapshot. It combines with the other two flags. In the harness
(`--classify`, `--host`) the flag taxes the tested bodies by the same
draw from the harness's fixed seed, so a caller that wants a definite
state should pass F = 0 or F = 1 (`analysis/e016_defence.py` passes the
harness no lifelong tax).

`--legacy-pending-range` (`Config.legacy_pending_range`, T08,
2026-10-13, default off) restores the `alloc`/`copy` range edge every
run before that date was made with. Since T08 a write (`store` or
`copy`) whose target lies inside the executor's own pending region
passes the locality check, because `alloc` already checked the whole
region against locality from its own IP when it claimed it; every other
write still checks range from the IP, and reads (including `copy`'s
source) are unchanged, as are write protection, write noise,
`copy_errors`, `slips` and `source`. Under the flag every write checks
range from the IP, so a child that the far `alloc` placed at the
backward edge of the radius (byte 0 exactly `locality` behind the
`alloc`) loses the bytes the `copy` loop cannot reach from its own IP a
few bytes on (byte 0 for the 21-byte ancestor, whose `copy` is one byte
after `alloc`; bytes 0–2 for the template ancestor, three bytes on):
those writes are `range_faults` and the child keeps whatever stale bytes
were there. The flag is bit-identical to the engine before T08 (tested
against three pinned state hashes); the default draws one more write-
noise `chance` per write that used to fault, so the PRNG streams part at
the first such write. `meta.json`'s config has the key since T08; runs
before it have none and are the legacy world. `--classify` and the
harness modes take the flag like any physics flag.

`Patch` gains two cumulative counters: `absorbed` (energy taken by
absorbs) and `overflow` (income lost to the cap).

`Org::first_foreign_off` (2026-10-13, T03): where the organism first ran
another living organism's byte. Set in `step` the first time the
organism executes a byte owned by another living organism (its body or
pending region), to the IP's offset from that owner's `start`, wrapped
around the ring, and never changed after; `None` until then. It is
harness-only state, not a counter in `OrgStats` and not in any output
file: nothing in the physics reads it, no PRNG draw depends on it, and
`Sim::state_hash` leaves it out (tested). The two-genome harness reports
it as `HostResult::entry_off` (-1 if never), and `--host` prints it as a
last column, `entry_off`. 0 is the fall-through entry (an intruder that
runs off its own end into the host's byte 0, E005); anything else is a
jump, a search, or an end byte that consumes or skips the host's byte 0
(`lit`, a firing skip: entry 1).

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
  (captured at build time by `build.rs`). Since 2026-10-08 (E009a) also
  `founders`, the seeded genomes as `[{"hex": ..., "count": N}, ...]` in
  seeding order, and `founder_starts`, the start address of every founder
  copy in the same order. Without `--founder HEX:COUNT` the list is the
  ancestor (K, E) once at `world_size / 2`, as in every earlier run. With
  it (repeatable), all copies of all flags, first flag first, sit at
  `world_size / 2 + world_size * j / total` modulo the world size, 100
  units each (`sim::founder_starts`); no two share a patch when the total
  is at most the patch count. Runs before 2026-10-08 have neither key.
  Since E009b (2026-10-08) also `injections`, one entry per
  `--inject TICK:HEX:COUNT` flag in the order given, as
  `[{"tick": T, "hex": ..., "count": N, "starts": [...]}, ...]`
  (`[]` without the flag). `starts` has one entry per copy: the start
  address it was placed at, or -1 if skipped; it is empty if the run
  ended before tick T. Copy j targets `world_size / 2 + world_size * j /
  N` modulo the world size and takes the first run of `len(HEX)` bytes,
  scanning forward, with no byte owned by a living organism (free or
  debris, overwritten), which must begin before the next copy's target
  (the last copy's limit is the first target plus the world size).
  Copies are placed at the start of tick T before any organism steps,
  100 units each, `parent` 0, `birth_tick` T, with no PRNG draw; like
  founders they have no `births.csv` row and their genome appears in
  `genomes.csv` with origin `seed` (unless already present).
  Since T03 (2026-10-13) also `ancestor`: `"std"` (the 21-byte body,
  the default) or `"tierra"` (`--ancestor tierra`, `sim::ancestor_t`,
  the 41-byte template-addressed body of E015). It names what `--k` and
  `--e` apply to and what is seeded without `--founder`; `ancestor_k`
  is the K actually used (`--k` defaults to 64 for `std`, 127 for
  `tierra`). Runs before 2026-10-13 have no key; they are all `std`.
  Since T04 (2026-10-13) also `state_every` (`--state-every N`, or
  `null`) and `replay_from` (`null`, or for a `--replay-from` run
  `{"path": FILE, "tick": T, "file_seed": F, "reseed": S}`, with `reseed`
  `null` when the stream continued); see "Snapshots and replay". Runs
  before have neither key.
- `births.csv`: `tick,child,executor,source,start,len,copy_errors,slips,endowment_m,raw_hash,parent_hash,parent_now_hash,source_hash`
- `deaths.csv`: `tick,id,cause,age,offspring,len,start,pending_len,ip_off,op_at_ip,energy_m,pool_m,birth_hash,now_hash,` then every `OrgStats` field, then `taxed_for_life` (0/1, the body was taxed for life under `--cycle-tax-lifelong`; since 2026-10-15, T10; runs before have no column, and none of their bodies was).
- `census.csv` (every census tick): `tick,now_hash,count`. Hash of current body bytes.
- `orgs.csv` (every census tick, one row per living organism): `tick,id,parent,birth_tick,start,len,pending_len,energy_m,ip_off,op_at_ip,birth_hash,now_hash,offspring,` then every `OrgStats` field.
- `patches.csv` (every census tick): `tick,patch,pool_m,orgs,absorbed_m,overflow_m`. `orgs` counts living body starts in the patch; `absorbed_m` and `overflow_m` are totals since the previous census row.
- `world.bin` (every census tick, since 2026-10-07): binary, one record
  per snapshot: `tick` (u64 little-endian), `n` (u32 little-endian, the
  world size), then `n` bytes of world memory, then `n` state bytes (0
  free, 1 debris, 2 owned by a living organism). Owner ids are not
  stored; `orgs.csv` at the same tick gives every living body's start and
  length. 128 KB per snapshot at the default world size. Added because
  E005 found genomes running dead code left in free memory and could not
  read it. `analysis/evo_run.world(run_dir)` loads it; `evo-core --disasm
  HEX` and `evo_run.disasm(bytes)` decode a slice.
- `genomes.csv` (written at the end): `raw_hash,func_hash,len,first_tick,first_id,origin,parent_hash,bytes_hex,disasm`. One row per raw hash ever seen. `origin` is `seed`, `birth`, `somatic`, or (since T04, in a `--replay-from` run only) `replay`: a body alive at the snapshot tick, `first_tick` that tick, `parent_hash` 0. For `birth`, `parent_hash` is the executor's body at `divide` (`parent_now_hash`), so a lineage runs birth genome, then somatic variant, then child. A `somatic` row is a body that changed after birth, seen at a census or at a `divide`; its `parent_hash` is that body's birth hash. Under parasitism (copy source not the executor) the lineage parent is still the executor; `births.csv` has `source_hash` for other rules. A body's state at death is not stored (its bytes can be reused within the tick), so `deaths.now_hash` may be missing from this file.

`--census N` sets the census interval (default: the `--report` interval).
Event rows are written as they happen; the in-memory event list is drained
after each tick so long runs do not grow memory.

## Snapshots and replay (`--state-every`, `--replay-from`)

Added 2026-10-13 (T04, `docs/tasks/T04-snapshots-replay.md`), for
E016's replays from the snapshot before a defence first appears.

`--state-every N` (needs `--out DIR`) writes `DIR/state/<tick>.bin`
(plain decimal tick, e.g. `state/25000.bin`) every N ticks and at the
final tick (the last tick run, `--ticks` or extinction). A snapshot is
taken after the tick's events are written, before the next tick's
injections. Each file holds everything `Sim` needs to continue bit for
bit (`Sim::save_state`, `Sim::load_state`); it is written under a
temporary name and renamed, so a killed run leaves no half-written
`.bin`. Not in it: the event list (empty at that point) and the
recorder's genome store (output). Size: 680–700 KB in the default world
(about 950 bodies), 886 KB in E016's `tierra_t50` world at 25,000 ticks
(1,405 bodies). Writing one takes about 1.2 ms in the release build
(0.3 ms to serialise, 0.4 ms to load); 100 snapshots over a 50,000-tick
run cost 0.12 s of 15 s. The loader reads the plain file only: gunzip a
compressed snapshot before replaying from it.

Format (`STATE_VERSION` 2 since 2026-10-15, T10; 1 before), little-endian:

```
magic      8 bytes  "EVOSTATE"
version    u32      2
cfg_len    u32      then cfg_len bytes: Config::fields() as UTF-8
                    "name=value\n" lines, in order (sim::config_text)
tick       u64
rng        4 × u64  (Rng::state(); Rng::from_state)
next_id    u32
energy_in, energy_out, energy_overflow   3 × i64
retired_executed  u64
retired_absorb_gain_m  i64
n          u32      world size, then n bytes, then n × u32 owner ids
np         u32      patches, then per patch pool, absorbed, overflow (3 × i64)
norgs      u32      then per organism, in `orgs` order (the dead since
                    the last retire included):
  id u32; regs 4 × u32; ip u32; flag u8; energy i64; start u32; len u32;
  pending: u8 present, u32 start, u32 len;
  pending_source: u8 present, u32 owner, u64 owner's birth hash;
  pending_errors u32; pending_slips u32; alive u8; birth_tick u64;
  offspring u32; genome_hash u64; parent u32; cycle_debt i64;
  taxed_for_life u8 (version 2 only);
  first_foreign_off: u8 present, u32;
  glen u32 then glen genome bytes (the birth genome);
  stats: the 31 OrgStats fields in CSV_HEADER order, 8 bytes each
  (i64 or u64 as declared; OrgStats::to_words)
```

An absent option is written as present 0 and zero values. A new field in
`Sim`, `Org`, `Patch` or `OrgStats` is a new version (`save_state`
destructures each without `..`, so it fails to compile until handled).
The loader refuses another magic or version, a config whose fields differ
from the loading run's (every field but `seed`, compared as text in
order; the error names the first that differs, e.g. `snapshot config
differs at cycle_theft_pct: the file has 50, this run 0`), a world or
patch count that does not match, a truncated file and trailing bytes. It
rebuilds the id index from the organism list.

Version 1 (T04 to T10, every E016 snapshot) differs from 2 only in the
lifelong tax: its config text has no `cycle_tax_life_frac` or
`cycle_tax_life_pct` line and its organisms no `taxed_for_life` byte.
This build still reads it, as the world with no lifelong tax: the
loading run must leave both fields at 0 (else the load is refused,
naming the field), and every body is untaxed. Saved again it is a
version 2 file. Tested against a version 1 file written by the engine
before T10 (`evo-core/tests/data/`), which this build also reaches
bit for bit by running the same command.

`--replay-from FILE [--seed S]` starts the run from FILE instead of
seeding tick 0. Give the original run's physics flags: the config they
make must match the file's, `seed` aside, or the run exits with status 2
and the message above. `--ticks` is absolute and must be above the
snapshot's tick. Without `--seed` the file's PRNG stream continues and
the run is the original's continuation, bit for bit (tested: the same
state file at the end, and the same `births.csv`, `deaths.csv`,
`census.csv`, `orgs.csv`, `patches.csv` rows and `world.bin` records
after the snapshot tick, in the default world and in `tierra_t50`).
With `--seed S` the PRNG is re-seeded with `Rng::new(S)` at the snapshot
tick (`Sim::reseed`), which is not the continuation even when S is the
original seed; the same S from the same file gives the same run.
`meta.json`'s config `seed` is the seed the stream from the snapshot tick
on comes from (S, or the file's), and `replay_from` records the path as
given, the tick, the file's seed and S (`reseed`, `null` without
`--seed`).

With `--out`, the recorder starts at the snapshot tick: `census.csv`,
`orgs.csv`, `patches.csv` and `world.bin` get a record at that tick (the
same as the original's census there; `patches.csv`'s `absorbed_m` and
`overflow_m` are 0 in it, being totals since the recorder started), and
every living body's birth genome goes into `genomes.csv` with origin
`replay`, first seen at the snapshot tick, `parent_hash` 0. A body whose
bytes changed since birth also gets its `somatic` row at that census, as
in any run. Genomes first seen after the snapshot have the same rows as in
the original, unless the original had seen them before the snapshot and
they were extinct at it (a re-arisal is then a `birth` row in the
replay). `patches.csv` matches the original only when the snapshot tick
is a census tick (E016: 25,000 and 500). `ticks_requested` and
`ticks_run` are absolute ticks. stdout's census line counts births and
deaths from the snapshot tick, and the speed line counts only the
replay's instructions. `--founder` is refused (it seeds tick 0), and so
is `--inject` at or before the snapshot tick; later injections work as
usual. `--ancestor`, `--k` and `--e` seed nothing in a replay and only
go into `meta.json`, so pass the original's to keep it readable.
`--state-every` in a replay writes snapshots at its multiples above the
start tick and at the end, never the start tick itself.

## Classifier (`--classify DIR`)

Reads `DIR/genomes.csv`, runs each genome alone in a clean world (noise
off, 100 units of seed energy, children removed every tick; the harness
from `ancestor_pays_for_itself`) for `--harness-ticks` ticks (default
3,000), and writes `DIR/classes.csv`. The energy and `alloc` physics are
whatever the command line gives (`--world-e001`, `--patch`, `--sun`,
`--alloc-far`/`--alloc-near`, `--absorb-prop`/`--absorb-fixed`; the code
default if none; `--self-owner`, `--charge-owner`, `--charge-owner-pct
N`, `--transfer-pct N` and `--cycle-theft-pct N` are carried too, though
a lone genome executes no foreign code, and so is the cycle tax, which
does act on a lone genome); noise
flags are ignored. With `--classes-out NAME` the
file is `DIR/NAME` instead, so one run can carry classes under two
physics (E005, 2026-10-06). The code default changed on 2026-10-07 from
the Phase 1 world to the E004 world: a `classes.csv` written before that
date used Phase 1 physics (what E005 calls the default class), and E005's
`classes_world.csv` files are the same yardstick as a `classes.csv`
written after it. Columns:

`raw_hash,class,births,exact_births,first_birth_tick,alive,final_energy_m,executed,absorbs`

| class | rule |
|---|---|
| `replicator` | at least 2 children whose bytes equal the parent's |
| `one_shot` | exactly 1 child, an exact one, and no other birth in the run: a working copy loop whose tail leaves the body for good (added 2026-10-07 after E005; before that these were `inexact`) |
| `inexact` | at least 1 child, but fewer than 2 exact ones, and not `one_shot` |
| `loafer` | no children, alive at the end |
| `dies` | no children, dead at the end |

This labels genomes by test, not by eye. It says what a genome does alone,
with full pools, from a fresh start (IP at the body start, registers zero).
A `replicator` can still fail in a crowded, drained patch, and a living
organism can be stuck in a state a fresh start never reaches (E003: most
long-lived absorb-loopers are labeled `dies`). `report.py` therefore also
shows each survivor's activity over the last census interval.

## Neighbourhood (`--neighbours HEX`)

Added 2026-10-13 (T03, E015; `harness::neighbours`). Classifies every
single-byte mutant of HEX alone and before a host:

    evo-core --neighbours HEX [--host-body HEX2] [--harness-ticks N]
             [--neighbours-out FILE] [--neighbours-pad-only] [--threads T]
             [physics flags]

Mutant set, in file order: position by position, at each position the
255 substitutions by every other byte value in ascending order, then the
deletion of that byte (256 rows per position; a deletion that would
leave no body, from a one-byte HEX, is left out). With
`--neighbours-pad-only`, only the substitution by `pad` (byte 0) at each
position, one row per position (T05's knockout set; where HEX already
holds 0 the row is HEX itself). Insertions are not in this cut.

Each mutant runs twice in the quiet harness (noise off, the physics
flags given, `--harness-ticks` ticks, default 3,000): `run_alone`, and
`run_with_host` with the mutant immediately before the host, which is
HEX itself unless `--host-body` gives another body. Mutants are
independent and run on `--threads` threads (default: the available
parallelism), each run with its own `Sim`; rows are written in mutant
order, so the file is byte-identical at any thread count (tested).
Speed: the 21-byte ancestor's 5,376 mutants take 0.8 s on 12 threads,
the 41-byte one's 10,496 about 2 s.

Output: `FILE` (`--neighbours-out`, default `neighbours.csv` in the
current directory), one row per mutant:

`pos,kind,byte,hex,raw_hash,func_hash,class_alone,births_alone,exact_alone,alive_alone,births_host,exact_host,host_copies,host_exact,alive_host,host_alive,executed,exec_foreign,entry_off,ticks_run,label`

| column | meaning |
|---|---|
| `pos`, `kind`, `byte` | the mutation: `sub` of `byte` (decimal) at `pos`, or `del` of `pos` (`byte` empty) |
| `hex`, `raw_hash`, `func_hash` | the mutant's bytes and its two hashes |
| `class_alone`, `births_alone`, `exact_alone`, `alive_alone` | the classifier's result alone (`--classify`'s columns) |
| `births_host`, `exact_host` | before the host: children whose `divide` the mutant executed, and of those the ones equal to the mutant |
| `host_copies` | children the mutant executed that equal the host |
| `host_exact`, `host_alive` | the host's own exact children, and whether it is alive at the end |
| `alive_host` | the mutant alive at the end of the run before the host |
| `executed`, `exec_foreign` | the mutant's instructions before the host, and those run on another living organism's bytes |
| `entry_off` | `HostResult::entry_off`: offset from the owner's start of the first foreign byte the mutant ran, -1 if none |
| `ticks_run` | ticks simulated before the host (fewer than N if the mutant died first) |
| `label` | below |

`label`, derived in Rust (`harness::label`) so every reader uses one rule:

| label | rule |
|---|---|
| `replicator` | `class_alone` is `replicator` (viable alone; `exact_host` says whether it also works next to a host) |
| `parasite_fallthrough` | not `replicator` alone, `exact_host` >= 2, `exec_foreign / executed` > 0.25, `entry_off` = 0 |
| `parasite_jump` | as above with `entry_off` != 0 |
| `one_shot`, `inexact`, `loafer`, `dies` | `class_alone` otherwise |

`entry_off` != 0 is "entered by a jump or a search, not by running off
its own end" only approximately: E015 found that the 21-byte ancestor's
16 end-byte mutants that turn `jmpa A` into a `lit` or a firing skip run
off their own end but consume or skip the host's byte 0, so they enter
at 1 and are labelled `parasite_jump`, and that `jmpr` by a constant
into the adjacent host (`lit D 13`, or `jmpr C` with C the own length)
also gives `parasite_jump`. Neither addresses its host by search; both
work only at the harness's adjacency. Read `pos`, `byte` and
`entry_off` before reading a `parasite_jump` count as search-addressed.

stdout: the number of mutants, the count of each label (all seven, in
the table's order), and the `parasite_jump` rows grouped by position:
rows, deletions among them, entry offsets with counts, and the range of
`exact_host`.

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
- `world.py` (2026-10-07): a marimo notebook over `world.bin`. Labels
  every address at every snapshot as living body, pending region, intact
  dead body (unowned bytes at a death site equal to a known genome),
  debris or free; world map per snapshot; an address inspector across
  snapshots; and off-body IPs (organisms whose IP is outside their own
  body at a census) with the kind of address they are at.
- `traits.py` (2026-10-07, E007 follow-ups; extended 2026-10-08, E009):
  trait bytes over replicator-class exact births per window. `track()`
  reads the absorb count (byte 6) and the endowment (byte 17, where byte
  16 is still `lit`) of 21-byte bodies by fixed offset, as E007 and E008
  reported them. `track_genome()` reads the canonical instruction list
  (a Python copy of `isa::canonical`) and gives: the endowment found by
  pattern (the first `lit R v` whose next instruction is `divide R`),
  with a share for bodies that have no such pattern; body length
  percentiles; the share of births whose genome contains `self 1`; the
  share whose first instruction is not `self 0`; and a histogram (0–5) of
  the longest match at byte 0 of the self-scan prefix
  `self 1 ; swap C ; self 0 ; sub C ; jmpr A`, compared on the op and the
  modifier bits the op reads, so silent bit-7 flips do not break a match.
  Any other prefix can be passed: `INERT` (five `zero D`, E009a), and
  since E010 `EJECT` (`self 1 ; swap C ; self 0 ; sub C ; skipz A ;
  jmpa D`) and `INERT6` (six `zero D`), giving a 0–6 histogram.
  Since T03 (2026-10-13) a trait pair for the 41-byte template ancestor,
  `TIERRA` = (`ABSORB_T`: absorb count at byte 7, guard 6, ancestor 127;
  `ENDOW_T`: endowment at byte 33, guard 32, ancestor 16), used with
  `length=TIERRA_LEN` (41); on the command line `--ancestor tierra`.
  `track_genome()`'s endowment by pattern works on it unchanged.

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
