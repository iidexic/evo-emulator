# T10. A survivable matched control: the lifelong cycle tax

Status: specified 2026-10-15 (Fable, from E016 record §8.1 and §8.7
item 2); not built. Builder: Opus. Argument: E016's random per-tick tax
at the calibrated rate (P = 88, F = 0.2398) killed 25 of 30 seeds where
the targeted theft killed none, so the one control H16 has cannot be
read. This task gives the control the shape of the treatment, so that
the mean debit matches **and** the per-organism distribution matches,
and the control is as survivable as the treatment for the same reason
the treatment is. Depends on T02 (built). E017 (the control arm) waits
on it; nothing else does.

## 1. Why the per-tick tax killed

Under the theft a host is in one of two states for life: entered (a
resident parasite runs its copy loop in it every tick, debiting about
66% of its cap; E016 §8.3, 21,194 of 32,000 milli-units) or not
(debited nothing). About 43% of replicator-class deaths in
`tierra_t50` are entered. The per-tick tax instead gives every
organism an independent draw each tick: with probability F = 0.24 it
loses 88% of its cap that tick. The mean per organism-tick is the same
(0.24 × 88% ≈ 0.43 × 66% ≈ 21% of cap) but the per-organism picture is
not: under the tax every replicator runs at about 79% of its speed on
average, with no untaxed class; under the theft 57% of replicators run
at full speed and 43% at a third. The template body's break-even
ration is 95.6% of a full ration at sun 1 and the world only persists
at sun 2 (E015 stage 2c), so the margin of an unentered body is thin,
and a 21% slowdown on every body is below it where a 66% slowdown on
some bodies and none on the rest is not. The control killed the
population by spreading the same cost evenly. (Inference from the
numbers in the E016 record; the pilot in §4 checks it.)

## 2. Rule

`--cycle-tax-lifelong F P`: at each organism's creation (seed, founder
set, injection, division) one PRNG draw; with probability F the
organism is **taxed for life**: every tick, before it runs, `cap × P /
100` milli-units are debited from its budget, exactly as the per-tick
tax debits (`sim.rs`, the `cycle_tax_pct` block: the debit is
`min(cap × P / 100, cap − debit)` after the theft debt is taken, and it
is added to `cycles_taxed_m`). With probability 1 − F it is never
taxed. The flag taxes nobody at F = 0 or P = 0 and is then bit-identical
to no flag (no draw is made; test this). It may be combined with
`--cycle-theft-pct` and with the per-tick tax; nothing is refused.

The state is inherited by nobody: each child draws for itself. (A
heritable tax would be selected against as a trait, which is not the
control; being entered is not heritable either, it is where a child
lands.)

Physical reading, for the doc comment: a lifelong tax is a body that
was born into a slow slot of the machine and stays there, the control
for a body that was born next to a parasite and stays entered.

### 2.1 Config, CLI, state

`config.rs`: `cycle_tax_life_frac: f64` (default 0.0) and
`cycle_tax_life_pct: i64` (default 0), both in `Config::fields()` so
`meta.json` carries them. CLI `--cycle-tax-lifelong F P` with the
range checks the other flags have (F in 0–1, P in 0–100).

`Org` gains `pub taxed_for_life: bool`, set at creation in `seed`,
`seed_founders`, `inject`, `inject_due` and at division, wherever an
`Org` is built (grep `cycle_debt: 0` for every site). It is physics
state: in the full-state snapshot (T04) and in `state_hash`, so a
replay from a snapshot continues bit-identically (test this with the
T04 continuation test pattern on a short lifelong-tax run). The PRNG
draw happens only when `cycle_tax_life_frac > 0`, so an untaxed run's
stream is unchanged.

`OrgStats`: `cycles_taxed_m` already exists and is reused; no new
column. `deaths.csv` gains `taxed_for_life` (0/1) so the analysis can
split deaths by tax state as it splits them by entered state.

### 2.2 Calibration

Against `tierra_t50`'s own numbers, over replicator-class deaths after
tick 25,000, seeds 1–30 pooled (the values are in E016 `runs.csv`
and `tax.json`; recompute them in the runner, do not copy them):

- F = the entered share of replicator-class deaths in `tierra_t50`
  (0.4299 in E016 §2's calibration note).
- P = 100 × (mean `cycles_lost_m` per organism-tick among **entered**
  replicator-class deaths) / 32,000 (E016 §8.3: 21,194 milli-units,
  so about 66).

This differs from T02 §4.2's rule, which took F from the no-cost arm
and r over all deaths; that rule matched the mean only. Record F, P and
the sums in the experiment file before the arm is launched. Mean check:
F × P must equal, within 2%, the E016 r / cap figure (6,740 / 32,000 =
21.1%); report it.

## 3. The arm: E017

A sixth E016 arm, `tierra_taxL`, 30 seeds, 250,000 ticks, the tierra
ancestor at sun 2 under the fixed edge (every other flag as
`tierra_n0`), with `--cycle-tax-lifelong F P` and no theft. The runner
is `e016_defence.py`: add the arm to `ARMS` (not `FIRST_ARMS`), give
`physics()` its flags, let `calibrate` write `tax_life.json` beside
`tax.json`, and let `screen`, `analyse`, `lod` and `replay` take it as
they take `tierra_tax` (same probe, same reference run). Outputs under
`runs/e016/tierra_taxL/`. The record is a new section in the E016 file
(§9, "E017: the lifelong tax control"), pre-registered before launch:

- **Survivability gate** (pilot first, §4): ≥ 24 of 30 seeds persist
  to 250,000. If not, the arm is read as the per-tick tax was, and
  this task's reading is that no random slowdown of this mean is
  survivable for this body, which is itself a result (the theft is
  survivable only because it falls on bodies that are already lost).
- **The paired reading** that E016 §7.4 could not make: structural
  complete share of replicator-class exact births in the last bin,
  `tierra_t50` against `tierra_taxL` by seed. H16's remaining claim is
  that the cost of being entered, not slowness as such, raises the
  relabelled share by a third. Prediction if it holds: t50 above taxL
  in ≥ 20 of 30 pairs, and taxL not above n0 in more than 18 of 30
  (the tax does not raise the share on its own). Prediction if the
  rise is a slowness effect (a slower world selects harder on copy
  speed, and a relabelled body is entered less): taxL above n0 in
  ≥ 20 of 30, t50 against taxL within 12–18 of 30.
- Everything else E016 §3 measures, for the table.

## 4. Pilot and gate

Before the 30 seeds: 10 seeds, 50,000 ticks, at the calibrated F and P.
Persist in ≥ 8 of 10 with a replicator-class population inside
`tierra_n0`'s 25,000–50,000 band: launch the 30. Persist in fewer:
run the pilot once more at the same mean with F = 0.24 and P = 88 in
the lifelong form (the E016 numbers), to separate "the lifelong shape
is survivable at this mean" from "this mean is not survivable in any
shape"; report both and stop, the 30 are not launched without a
decision.

## 5. Tests

1. `lifelong_tax_off_is_bit_identical`: a 5,000-tick default-world run
   with `--cycle-tax-lifelong 0 0` and with no flag have equal
   `state_hash` at every census.
2. `lifelong_tax_debits_every_tick`: in the harness, the ancestor with
   F = 1, P = 50 makes about half its lone births (compare against T02
   gate 1's 0.465 at theft N = 50: within 0.1 of it) and
   `cycles_taxed_m` at death equals `age × 16,000` within one tick's
   worth.
3. `lifelong_tax_is_drawn_at_birth`: F = 0.5, P = 100 (a taxed body
   never runs), 3,000 ticks of the default world: the share of deaths
   with `taxed_for_life` = 1 is within 0.45–0.55, and no taxed body has
   `executed` > 0.
4. `lifelong_tax_survives_snapshot`: T04's continuation test under
   F = 0.3, P = 60: state file, CSV rows and `world.bin` bit-identical
   between the straight run and the replay from tick 2,500.
5. The energy ledger tests pass unchanged.

## 6. Report back

F, P, the sums and the mean check (§2.2); the pilot's persistence and
population; test count and commit ids; the T10 row in
`docs/tasks/README.md` and the Status line here updated. Do not launch
the 30-seed arm: that is a decision after the pilot, taken with the
E016 write-up.
