# T08. The `alloc`/`copy` range edge: writes into one's own pending region

Status: specified 2026-10-13 (decision taken the same day: fix it,
keep the old behaviour behind a flag). Argument: PLAN §9 ("`alloc`/
`copy` range edge"), E015 record (stage 2 arms), E005 (the
fall-through lineages). Depends on T03 (the tierra body and the
E015 runner's gate stage, which this re-runs).

## 1. The defect

`alloc` checks that the whole run `[s, s + want)` lies within
`locality` (512) of the IP at the `alloc` instruction
(`sim.rs`, `Op::Alloc`: `in_range(ip, s) && in_range(ip, s + want -
1)`). Under the default far placement the backward candidate is
`ip − locality − want + 1`, so the child's first byte sits exactly
`locality` behind the `alloc` IP. The copy loop runs later and its
IP has moved on: for the 21-byte body `copy` sits 3 bytes after
`alloc`, for the 41-byte body also 3. `write` re-checks range from
the `copy` IP (`sim.rs`, `fn write`: `in_range(ip, addr)`), and
the first bytes of the child are now `locality + 1` to `locality +
3` away. Those writes fail with `range_faults`, and the child keeps
whatever stale bytes were there when it divides.

Measured (E015 record): std ancestor, noise off, 3,000 ticks: 12.8%
of births lose byte 0 (`self` becomes `pad`); the founder's second
child, tick 27, is the first. Tierra body, seed 1, first 5,000
ticks: 2,384 of 26,657 births lose L0 (bytes 0–2) and are
return-parasites with no mutation. The same edge is in every
recorded run (E001 onward; the far placement since E004), so part
of E005's fall-through parasite lineages and part of E015's
parasitism is manufactured by it.

## 2. The rule

A write (`store` or `copy`) whose target byte lies inside the
executor's own pending region passes the locality check. The
reasoning for the doc comment: `alloc` already checked the whole
region against locality when it was claimed, and the region is the
organism's own; the second check at the `copy` IP measures the
wrong thing (where the copy loop happens to sit in the body). Every
other write still checks range from the IP. Reads are unchanged:
`copy` reads its source from the IP's range as today. Write
protection, write noise, `pending_errors`, `pending_source`, slips:
unchanged.

Flag: `Config::legacy_pending_range: bool`, default `false` (the
new rule). CLI `--legacy-pending-range` sets it; `meta.json` gets
it through `Config::fields` (the destructuring has no `..`, so the
compiler enforces the listing). Under the flag the engine is
bit-identical to today's: same bytes, same `state_hash`, same CSVs.
Nothing else changes with the flag; in particular `alloc`'s own
check is as today in both modes.

Implementation: in `fn write`, before the `in_range` test,

```rust
let own_pending = self.orgs[i].pending
    .map_or(false, |(ps, pl)| self.off(addr, -(ps as i64)) < pl);
if !(own_pending && !self.cfg.legacy_pending_range) && !self.in_range(ip, addr) { ... fault ... }
```

(`self.off(addr, -(ps as i64)) < pl` is the pattern the file already
uses for "inside the pending region".) No PRNG draw is added or
moved: the noise draw in `write` happens after the range check in
both modes, and a write that used to fault drew nothing, so under
the new rule the first non-faulting write at the edge draws one
more `chance` than before. That is the intended divergence, not a
side effect; the legacy flag keeps the old draw sequence.

The `harness.rs` modes (`run_alone`, `run_with_host`, the
neighbourhood function) take the config they are given and need no
change. `--classify` of an old run under the new default
re-classifies its genomes under the new physics; the E015 runner's
classify step passes the arm's flags, and the baseline below passes
`--legacy-pending-range` where it means the old world.

## 3. Tests

1. `copy_into_own_pending_region_passes_range`: a hand-built `Sim`
   with the std ancestor at some start, run until its `alloc` has
   placed a child at the backward edge (the far placement puts it
   there; `alloc_far_places_child_at_locality_edge` in `sim.rs`
   shows how to reach that state). Under the default: the child's
   bytes 0–2 equal the parent's, `range_faults` 0 for the copy
   loop. Under `legacy_pending_range`: bytes 0–2 unchanged from
   before the copy, `range_faults` ≥ 3.
2. `store_outside_pending_still_faults`: a `store` to an address at
   `locality + 1` that is not in the pending region faults in both
   modes.
3. `legacy_flag_is_bit_identical_to_head`: before changing anything,
   run `evo-core --seed 1 --ticks 5000` (default physics) and
   `--ancestor tierra --sun 2 --seed 1 --ticks 5000` at HEAD and
   record the two `state_hash` values (print them with a one-off
   `eprintln!` or through a test that prints; remove the print).
   The test runs the same two under `legacy_pending_range = true`
   and asserts the pinned hashes. Also pin the current hash of a
   noise-on run so the PRNG sequence is covered (seed 1, 5,000
   ticks, default physics, is noise-on; good).
4. `noise_off_births_are_exact_under_the_new_rule`: std ancestor,
   `p_write_flip` 0, `p_bit_rot` 0, 3,000 ticks, single founder in
   the default world: every birth's `raw_hash` equals its
   `parent_now_hash` and `copy_errors` is 0 (today 12.8% differ).
   Same for the tierra body at `--sun 2`.
5. Existing tests: `cargo test` whole. Any test that pinned bytes or
   hashes under the old edge and now fails is checked by hand: if
   its expectation encoded the defect, update it and say so in the
   report; if it reveals something else, stop and report.

## 4. Baseline runs (`analysis/e015_template.py`, gate stage)

Add gate arms (same `GATE_ARMS` / `ARM_FLAGS` tables; `base(arm)`
must return `std` for the std arms, so the std arm's flags set
`--ancestor std`):

| arm | flags |
|---|---|
| `std_fix` | `--ancestor std` |
| `std_fix_sun2` | `--ancestor std --sun 2` |
| `tierra_fix` | `--ancestor tierra` |
| `tierra_fix_sun2` | `--ancestor tierra --sun 2` |

10 seeds, 50,000 ticks, `--census 500`, the gate's existing
summary (replicator-class alive at 50,000; E004's ≥ 8 of 10) and
the gate detail (parasite-lineage share per 2,500-tick bin, entered
share of replicator-class deaths after 25,000, resident share) for
every arm. Runs go under `runs/e015/` as the other gate arms do,
gzip on. Keep the old arms' results in place; the old world is now
`--legacy-pending-range` and the existing `gate*.md` files already
say which binary ran them (check `check_meta` still passes on the
old directories: it compares `meta.json` flags with the arm's
flags, and the old runs' `meta.json` has no `legacy_pending_range`
key; treat a missing key as the old default, do not fail).

The analysis also prints, per arm, the share of births whose
`copy_errors` is 0 but whose `raw_hash` differs from
`parent_now_hash` (the edge's signature under noise: a child that
differs from the parent with no recorded copy error). Under the
fix this is 0 by construction in the quiet arm and should be near 0
under noise (bit rot can still hit the pending region; note that
case). Under legacy it is the 9–13% above.

Runtime: 40 runs of 50,000 ticks, about 25 s each, all cores: a few
minutes. Build with `cargo build --release` in `evo-core/` (the
default target dir; the runner finds `target/release/evo-core.exe`).

## 5. Docs

- `docs/instrumentation.md`: the flag, one paragraph.
- `PLAN.md` §9 entry "`alloc`/`copy` range edge": append the
  decision (fixed 2026-10-13 as the default; old behaviour under
  `--legacy-pending-range`; every run recorded before this date is
  the legacy world) and the baseline result in one sentence.
- E015 record `docs/research/experiments/2026-10-13-e015-template-ancestor.md`:
  a section "Stage 2c: the four gate arms under the fixed edge" with
  the table (pass count, replicator-class alive, parasite share last
  bin, entered share, resident share, edge signature share) and a
  one-paragraph reading: does tierra still need `--sun 2` once the
  free parasites are gone, and does std's parasite share fall to
  the 0–2% H17 predicts.
- `docs/research/experiments/README.md` E015 row: one clause.
- `docs/tasks/README.md`: T08 row status and the E015 branch
  bullet ("Decision pending …" becomes the outcome).
- `analysis/README.md`: nothing unless the runner's usage line
  changes.

## 6. Files

`evo-core/src/config.rs` (field, `fields()`, doc), `sim.rs`
(`write`, doc comments on `alloc` and `write`), `main.rs` (flag,
header doc), `evo-core/tests/` (new file `pending_range.rs` for
tests 1–4), `analysis/e015_template.py` (arms, `base`, `check_meta`,
edge-signature column), the docs above.

## 7. Report back

The three pinned hashes and that test 3 passes; `cargo test`
totals; the four-arm table from §4 with the edge-signature share;
anything in §3 item 5. Commit per item (engine + tests; runner;
runs + record + docs), subjects `T08: …` / `E015: …` / `docs: …`,
each ending `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
Do not push.
