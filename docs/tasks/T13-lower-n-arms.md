# T13. E016's premise at a cost the entered individual survives: `tierra_t10` and `tierra_t20`

Status: specified 2026-10-15 (Fable; Derek accepted the memo's
recommendation). §1's curve run the same night (below): the arms are
**N = 10 and N = 20**. Engine and runner not built. Builder: Opus,
after T10 has merged (both touch `e016_defence.py`'s arm list). Argument: E016 record §8.2 and
write-up §5.4: under `--cycle-theft-pct 50` the entered template
ancestor makes 1 exact child in 3,000 harness ticks against 119
alone. The literature's condition for an evolved defence is that the
entered host reproduces, more slowly; at N = 50 that held for the
population and not for the individual. E014 showed the dose is linear
in the harness (0.97 / 0.90 / 0.85 at 25 / 50 / 75 for the std body
with a fall-through intruder). For the template body with a searching
parasite the dose is unmeasured below 50. Two arms close the gap.

## 1. Harness first

`defence_ref.json`-style reference for the tierra ancestor with the
registered probe before it at N ∈ {5, 10, 15, 20, 25, 30, 40}: the
ancestor's exact births probed (`b_probed`) against 119. Report the
curve. Pick the two arms as the N nearest to `b_probed` ≈ 0.75 × 119
and ≈ 0.5 × 119 if they lie in 5–40; otherwise N = 10 and 25 as
named, and say so. The point is an arm where the entered individual
keeps half or three quarters of its rate.

**Run 2026-10-15** (Fable, `evo-core --host PROBE --host-body ANCESTOR
--harness-ticks 3000 --sun 2 [--cycle-theft-pct N]`, the E016 binary):

| N | 0 | 5 | 10 | 15 | 20 | 25 | 30 | 40 | 50 |
|---|---|---|---|---|---|---|---|---|---|
| host exact births, probed | 119 | 115 | 107 | 101 | 94 | 34 | 7 | 2 | 1 |
| of 119 | 1.00 | 0.97 | 0.90 | 0.85 | 0.79 | 0.29 | 0.06 | 0.02 | 0.01 |
| host alive at 3,000 | yes | yes | yes | yes | yes | **no** | no | no | no |
| probe exact births | 119 | 119 | 119 | 119 | 119 | 119 | 119 | 119 | 119 |

The dose is graded to N = 20 (1 − N/100 within 0.01, as E014 found for
the std body) and a cliff at N = 25: the host **dies** of upkeep
inside 3,000 ticks with the probe resident, and from there the
"entered individual" is killed, not slowed. E016's N = 50 is in the
cliff regime. There is no N where the host keeps half its rate and
lives; the nearest to three quarters is N = 20 (0.79). Arms: **N = 10
(0.90, the rate E014 measured for std at N = 50) and N = 20 (0.79, the
last graded point)**. The record's §9 pre-registration should say
that the cliff, not the dose, is what the N = 50 arm tested.

## 2. Arms

Two E016 arms, `tierra_t<N1>` and `tierra_t<N2>`, 30 seeds, 250,000
ticks, every other flag as `tierra_t50` (sun 2, fixed edge, one
founder). Runner: generalise `physics()` so any `tierra_t<N>` arm
sets `--cycle-theft-pct N` (keep `tierra_t50` as it is), add the two
to `ARMS`, and let every stage take them as it takes `tierra_t50`
(same probe, own reference run per arm, since `b_probed` depends on
N). Outputs under `runs/e016/<arm>/`. `--jobs 16` at most while other
work runs.

## 3. Pre-registered reading (goes in the E016 record as §9 before launch)

Paired by seed against `tierra_n0` and against `tierra_t50`
(structural immune share of replicator-class exact births in the last
bin; maintained yes/no; entered share of replicator-class deaths after
25,000; T11 §2's three kinds, if `t11_closed.py own` is cheap enough
to run on each arm's top 20):

- **Dose on the share.** If the one-third rise at N = 50 is selection
  on being entered, the rise is monotone in N: `n0` < `t<N1>` <
  `t<N2>` < `t50` in at least 20 of 29 seed triples (ordered pairs
  counted separately, each ≥ 20 of 29). If the rise is a slowness
  effect, T10's arm says so and the lower-N arms show no order.
- **A tolerant defence.** The registered test is unchanged (E016 §1).
  Prediction under the premise: at an N where the entered individual
  keeps half its rate, an eject or reset has a payoff an individual
  can collect, and a tolerant genome arises in ≥ 3 of 30 seeds at one
  of the two N (none arose in 150 runs at 0 and 50). Prediction
  against: 0 of 60, and the negative is then stated at three N.
- **The kinds.** Does the lower cost shift the immune class toward
  the open kind (Tierra's moving target) and away from the closed
  (de-labelled, redundant label)? No prediction; reported.

## 4. Report back

The §1 curve, the arms chosen, the per-seed tables the E016 summary
already prints, the paired counts of §3, commit ids, the T13 row in
`docs/tasks/README.md`. Do not edit the E016 record beyond adding the
§9 pre-registration verbatim from §3 before launch; Fable writes the
outcome.
