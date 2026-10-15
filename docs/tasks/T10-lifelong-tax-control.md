# T10. A survivable matched control: the lifelong cycle tax

Status: specified 2026-10-15 (Fable, from E016 record §8.1 and §8.7
item 2); built 2026-10-15 (Opus; `749f8ae` engine and tests, `3272adf`
runner and calibration; founders exempt `8ef2f7f`, calibration per
organism-tick `e72de6b`; §7 below). Calibrated F = 0.79995, P = 26:
mean check holds (F × P 20.80% of cap against 21.06%). Pilot at that
pair, founders exempt (§7.2): persists **10 of 10**, but only **7 of
10** inside tierra_n0's band (s2 118, s5 184, s8 183 against 189–253):
gate **fails by one seed**, realised debit 17.3–19.3% of cap. The 30
seeds are not launched; a decision. Builder: Opus. Argument: E016's random per-tick tax
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

`--cycle-tax-lifelong F P`: at each organism's birth (division) and
at each injection (`inject_due`) one PRNG draw; with probability F the
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

Founders never draw (amended 2026-10-15, after the first pilot): the
founder is the one body that is not born next to anything, so nothing
could enter it. `seed`, `seed_founders` and `inject` called directly
create untaxed bodies. As first written the founder drew too, and at
P = 66 a taxed founder died at tick 73 before its first child, which
decided 4 of the first pilot's 10 seeds before the control could act.

Physical reading, for the doc comment: a lifelong tax is a body that
was born into a slow slot of the machine and stays there, the control
for a body that was born next to a parasite and stays entered.

### 2.1 Config, CLI, state

`config.rs`: `cycle_tax_life_frac: f64` (default 0.0) and
`cycle_tax_life_pct: i64` (default 0), both in `Config::fields()` so
`meta.json` carries them. CLI `--cycle-tax-lifelong F P` with the
range checks the other flags have (F in 0–1, P in 0–100).

`Org` gains `pub taxed_for_life: bool`, false when `seed` builds the
`Org` (the one site) and drawn by `Sim::draw_life_tax` for each child at
division and each copy `inject_due` places (amended 2026-10-15; founders
are untaxed). It is physics
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

- F = the share of organism-ticks spent in **entered** bodies: Σ `age`
  of the entered replicator-class deaths over Σ `age` of all of them.
- P = 100 × Σ `cycles_lost_m` of the entered / (their Σ `age` ×
  32,000), the debit per tick of an entered body's life, to the nearest
  whole percent.

Corrected 2026-10-15 (the first pilot's calibration). As first written
the rule matched per death: F = the entered share of deaths (0.4299)
and P from the mean of `cycles_lost_m / age` over the entered (21,080
milli-units, P = 66). That pair gives F × P = 28.4% of cap, 35% above
the theft's 21.1%, because entered hosts live about five times longer
than unentered ones (mean age 708 ticks against 133): 43% of the deaths
hold 80% of the organism-ticks. The lifelong tax draws at birth,
independent of lifespan, so a taxed body is expected to live as long as
an untaxed one and F must be the share of time, not of deaths. With the
E016 numbers (tierra_t50 seeds 1–30, replicator-class deaths after
25,000): F = 3,764,424,123 / 4,705,804,390 = 0.79995; P = 100 ×
31,718,765,563,000 / (3,764,424,123 × 32,000) = 26.33, rounded to 26;
F × P = 20.80% against r / cap = 31,718,765,563,000 / 4,705,804,390 /
32,000 = 21.06%, −1.3%. (An unentered death loses nothing, so F × P is
exactly r / cap before rounding.)

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

## 7. Build report (2026-10-15)

Engine as §2 (`--cycle-tax-lifelong F P`, `Org::taxed_for_life` drawn in
`Sim::seed`, which every creation goes through; F = 1 taxes with no
draw, as the per-tick tax at F = 1). Two additions §2 did not ask for:
`taxed_for_life` enters `state_hash` only when set, so a world with no
taxed body keeps its old hash (T08's pinned hashes hold); and the
snapshot format is version 2 while version 1 files (every E016
snapshot) are still read, as the world with no lifelong tax, since
otherwise a rebuilt binary could replay none of them. §5's five tests
pass, plus the version 1 read; `cargo test` 77 before, 82 after.
Test 2 measured 115 of 230 lone exact births (0.500); test 3 31,611 of
62,417 deaths taxed (0.506).

The harness runs untaxed (`harness_physics` in the runner): under the
flag the harness bodies draw from the harness's fixed seed (seed 1 draws
untaxed at F = 0.43, seed 2 taxed), and the tierra ancestor taxed for
life at P = 66 dies alone at tick 73 with no child, so a taxed harness
would class every genome `dies`. tierra_taxL's harness is tierra_n0's,
as tierra_t50's `alone` is unentered.

**Calibration (§2.2)**, tierra_t50 seeds 1–30, replicator-class deaths
after 25,000 (`runs/e016/tierra_taxL_pilot/tax_life.json`): F =
5,319,020 / 12,371,784 = 0.4299; mean `cycles_lost_m / age` over the
entered deaths = 112,124,844,706.8 / 5,319,020 = 21,080.0 milli-units,
P = 65.87, rounded to 66; r = 31,718,765,563,000 / 4,705,804,390 =
6,740.35, as `tax.json`. Mean check: F × P = 28.38% of cap against r /
cap = 21.06%, **+34.7%**, outside 2%. §1's "0.43 × 66% ≈ 21%" is the slip:
it is 28%. The entered deaths hold 80.0% of the organism-ticks (mean age
708 ticks against 133 unentered), so the count share times the
per-death mean is not the per-tick mean. The time-weighted pair, F =
0.8000 of organism-ticks in entered bodies and P = 26.33 (their pooled
Σ lost / Σ age), multiplies to r / cap by construction; it is recorded
beside and was not piloted.

**Pilot (§4)**, 50,000 ticks, `runs/e016/tierra_taxL_pilot/` (per pair
`pilot.csv`, `pilot.json`). tierra_n0's band (replicator-class census
bodies, mean over ticks 25,000–50,000, its 29 persisting seeds): 189–253,
median 230. The founder draws too, and at P = 66 or 88 a taxed founder
dies at tick 73 or 79 with no child.

| pair | seeds 1–10 persisted | inside the band (gate ≥ 8) | founders taxed in 1–10 | founder untaxed: persisted | first 10 of those inside the band | taxed share of rep. deaths | realised debit / cap |
|---|---|---|---|---|---|---|---|
| F 0.4299, P 66 (calibrated) | 6 | 6: fails | s2, s4, s5, s9 | 13 of 13 (seeds 1–20) | 9 (s17 at 254) | 42.6–43.4% | 5.3–6.7% |
| F 0.2398, P 88 (E016's numbers) | 8 | 7: fails (s1 at 259) | s2, s9 (and s11) | 12 of 12 (seeds 1–15) | 9 (s1 at 259) | 23.8–24.3% | 0.5–0.8% |

Reading, for the decision (not taken here): once the founder is
untaxed, the lifelong shape persists in every seed at both pairs, with a
replicator-class population inside or just above tierra_n0's band, so
§1's inference holds as far as survival goes. But the debit it realises
in the world is not the theft's: a body taxed at 66% or 88% for life is
sterile and dies young, so the tax removes F of the births rather than
slowing them, and the per-organism-tick debit is 6% or 0.7% of cap
against the theft's 21.1%. Matched on the share of deaths, not on the
mean. Two things to settle before E017: whether founders (and injected
bodies) should draw at all, since no parasite can enter a body before
one exists, or be counted out under E016 §5; and which pair is the
control (the calibrated one, E016's, or the time-weighted one, which
slows 80% of bodies by 26% and may fail as the per-tick tax did).

### 7.2 Second pilot: founders exempt, the organism-tick pair (2026-10-15)

Decisions after the first pilot (coordinator): founders never draw
(§2, `8ef2f7f`), and the control pair is the one matched per
organism-tick (§2.2, `e72de6b`): F = 0.7999533790651251, P = 26. Same
pilot, 10 seeds, 50,000 ticks, `runs/e016/tierra_taxL_pilot/f80p26/`;
and 3 seeds at F = 1, P = 21 (every body taxed, the per-tick tax's mean
in lifelong form), `f100p21/`, for the "any shape" comparison. Band
and debit measured as in §7 (tierra_n0 band 189–253, median 230; debit
= Σ `cycles_taxed_m` / Σ `age` / 32,000 over replicator-class deaths
after 25,000).

| pair | persisted to 50,000 | replicator-class population, mean 25,000–50,000 | inside the band | taxed share of rep. deaths | realised debit / cap |
|---|---|---|---|---|---|
| F 0.80, P 26 (10 seeds) | 10 of 10 | 118–233, median 210 | 7 (s2 118, s5 184, s8 183 below) | 79.6–80.2% | 17.3–19.3% |
| F 1.0, P 21 (3 seeds) | 3 of 3 | 104, 107, 161 | 0 | 100% | 20.9% |
| first pilot, F 0.43, P 66, untaxed founders | 13 of 13 | 204–254 | 9 of 10 | 42.6–43.4% | 5.3–6.7% |
| first pilot, F 0.24, P 88, untaxed founders | 12 of 12 | 221–259 | 9 of 10 | 23.8–24.3% | 0.5–0.8% |

Reading: no shape of this mean kills the population in 50,000 ticks
(13 of 13 at the two organism-tick-matched rows), so §1's inference
that the per-tick tax killed by spreading the cost evenly does not
survive as stated: the lifelong all-bodies form at 21% persists. What
the shape changes is the population: the more evenly the slowdown is
spread, the lower the replicator-class population (F = 1: about half
of tierra_n0's; F = 0.8: a median 210, 9% under n0's 230 and three
seeds below the band; the sterile-minority forms sit at n0's level
because they barely debit at all). The registered gate fails by one
seed at the chosen pair. 21 of the per-tick tax's 25 extinctions came
between 35,690 and 54,330 (E016 §8.1), at the end of this window, so 50,000 ticks
does not show whether these pairs survive to 250,000.
