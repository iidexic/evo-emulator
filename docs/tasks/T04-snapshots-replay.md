# T04. Full-state snapshots and replay from a tick

Status: specified 2026-10-13; built the same day (Opus, `63cae21`;
docs/instrumentation.md, "Snapshots and replay"). §2's list needed no
addition: it already had every `Sim` and `Org` field T02, T03 and T08
added (`exec_by_others` and the cycle counters are `OrgStats` words,
`legacy_pending_range` is in the config text); `meta.json`'s
`replay_from` is `{path, tick, file_seed, reseed}` and a `state_every`
key was added. §6: `cargo test` 77 passed; 680–700 KB per snapshot in
the default world, 886 KB in E016's `tierra_t50` world; save 0.3 ms,
load 0.4 ms (release); `--state-every 500` over 50,000 ticks cost 0.12 s
of 15 s (under 1%). Test 2 replays 5,000 from 2,500 (not 10,000 from
5,000), in the default world and in `tierra_t50`; both continuations
are bit-identical. PLAN §7 had listed this as
"not yet" since 2026-10-03; E016 needs it for replay-based
potentiation (Escondo & Ferguson 2026 seed replays from full
snapshots, not from lineages). Independent of T02 and T03, but every
`Org` field they add goes into the format, so build it after them or
leave a note to extend it.

## 1. What a snapshot is

Everything `Sim` needs to continue bit-for-bit: tick, PRNG state,
world bytes and owner ids, patches, every organism with registers
and IP, the id counter, the conservation totals and the retired
counters. Not included: `Sim::events` (drained every tick by the
recorder; a snapshot is taken after `run_tick`, when it has been
drained, so it is empty), and the `Recorder`'s genome store (output,
not state).

`Sim::save_state(&self, w: &mut impl Write) -> io::Result<()>` and
`Sim::load_state(r: &mut impl Read, cfg: Config) -> io::Result<Sim>`.
The loader rebuilds `index` from the organism list.

## 2. Format

Little-endian throughout. One file per snapshot.

```
magic      8 bytes  "EVOSTATE"
version    u32      1
cfg_len    u32      then cfg_len bytes: Config::fields() as UTF-8
                    "name=value\n" lines, in order
tick       u64
rng        4 × u64  (Rng::state(); add Rng::from_state)
next_id    u32
energy_in, energy_out, energy_overflow   3 × i64
retired_executed  u64
retired_absorb_gain_m  i64
n          u32      world size, then n bytes, then n × u32 owner ids
np         u32      patches, then per patch pool, absorbed, overflow (3 × i64)
norgs      u32      then per organism:
  id u32; regs 4 × u32; ip u32; flag u8; energy i64; start u32; len u32;
  pending: u8 present, u32, u32; pending_source: u8 present, u32, u64;
  pending_errors u32; pending_slips u32; alive u8; birth_tick u64;
  offspring u32; genome_hash u64; parent u32; cycle_debt i64 (T02);
  first_foreign_off: u8 present, u32 (T03);
  glen u32 then glen genome bytes;
  stats: every OrgStats field in CSV_HEADER order, 8 bytes each
  (i64 or u64 as declared)
```

Organisms are written in `orgs` order, including those dead since the
last `retire`, so the loaded `orgs` list is identical. The loader
refuses a file whose magic or version differ, and whose config text
differs from `cfg.fields()` of the config it is given, except for
`seed` (see §3). A refusal names the first differing field.

## 3. CLI

- `--state-every N`: with `--out DIR`, write `DIR/state/<tick>.bin`
  every N ticks (and at the final tick). Default off. About 0.5 MB per
  file at the default world size (65,536 bytes + 262,144 bytes of
  owner ids + about 1,000 organisms at roughly 350 bytes each).
- `--replay-from FILE [--seed S]`: load FILE under the physics flags
  on the command line (which must match the file's config, or the run
  refuses), then run to `--ticks` (an absolute tick; refuse if it is
  not above the snapshot's tick). With `--seed S` the PRNG is
  re-seeded with `Rng::new(S)` at the snapshot tick and `meta.json`
  records both the file's seed and S; without it the stream continues
  and the continuation is bit-identical to the original run. `--out`
  works as usual: the `Recorder` is created at the snapshot tick, and
  every living body at that tick is entered into `genomes.csv` with
  origin `replay` (a new origin value; `evo_run.py` and
  `docs/instrumentation.md` list it). `meta.json` records
  `replay_from` (path and tick). `--founder` and `--inject` with a
  tick at or before the snapshot are refused; later injections work.

## 4. Tests

1. `snapshot_round_trips`: seeded standard world, 5,000 ticks, save;
   load into a new `Sim`; `state_hash` equal immediately, and equal
   again after both run 5,000 more ticks.
2. `replay_events_match` (integration test next to
   `tests/instrumentation.rs`): record a 10,000-tick run with
   `--state-every 5000`; replay from 5,000 to 10,000 with `--out`;
   `births.csv`, `deaths.csv`, `census.csv`, `orgs.csv`,
   `patches.csv` rows with tick > 5,000 are identical to the original
   run's rows in that range; `world.bin` records at 10,000 identical.
3. `replay_reseed_diverges_deterministically`: `--seed 2` from the
   same file twice gives equal state hashes to each other and a
   different one from the continuation.
4. `loader_refuses_a_config_mismatch`: a file saved under
   `--cycle-theft-pct 50` refused under no flag, naming the field.

## 5. Files

`evo-core/src/sim.rs` (`save_state`, `load_state`), `rng.rs`
(`from_state`), `main.rs` (flags, docs), `record.rs` (`replay`
origin, `meta.json` keys, the `state/` directory), `tests/`,
`docs/instrumentation.md` (format and flags), `analysis/evo_run.py`
(`origin` value; a `state(run_dir, tick)` helper is optional).

## 6. Report back

`cargo test`; file size per snapshot; the time to save and to load;
and the speed cost of `--state-every 500` over 50,000 ticks (expected
under 5%).
