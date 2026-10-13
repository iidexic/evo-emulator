# T01. The E007 reserve check

Status: specified 2026-10-13; a build was already started on the laptop
(Opus) from the synthesis text alone. This file is the acceptance
standard for whatever that run produces; if it reported something
else, redo it to this.

## Question

Does a replicator in the standard world ever bank energy, or does it
sit at one pass of reserve? The synthesis
(`docs/research/synthesis-2026-10-13.md` §2 B) argues from the
equilibrium that it cannot bank: proportional absorb on a shared pool
lets the population grow until the ration per `absorb` equals the
cycle cost, so the store cap (64 units per byte, 1,344 for a 21-byte
body) is never approached. Line A's choice of a cost in time rests on
this; so does the demotion of the `drain` proposal. It is an inference
and has not been measured.

## Data

E007, seeds 1–10, `runs/e007/std/s<seed>/`: `orgs.csv` (every census,
one row per living organism) and `deaths.csv`, both carrying
`energy_m`, `max_energy_m`, `absorbs`, `absorb_capped`, `absorb_short`,
`len`, `birth_hash`; `classes.csv` for the class of each birth hash.
Energy columns are milli-units (`docs/instrumentation.md`).

## Procedure

Script `analysis/e007_reserve.py`, read-only over the run
directories, output `runs/e007/reserve.csv` and `reserve.md`.

Per seed, over organisms whose birth hash is replicator-class, from
tick 25,000 on (the stationary phase):

1. From `deaths.csv`: `max_energy_m / 1000` percentiles 50, 90, 99 and
   the maximum, and the same for `energy_m` at death; `cap` = 64 × `len`
   per row, and the same percentiles of `max_energy_m / cap`.
2. From `orgs.csv`: percentiles of `energy_m / 1000` over all
   organism-census rows, and the share of rows with `energy_m` above
   half the cap.
3. `absorb_capped` summed over the same deaths divided by `absorbs`
   summed: the share of absorbs cut short by a full store.
4. The same table for the first 25,000 ticks, as the contrast (the
   founder phase, where a lone body in a full patch may bank).

One row per seed and phase; a final table with the ten seeds side by
side.

## Decision rule, fixed now

The zero-margin argument **holds** if, in every seed after tick
25,000, the median `max_energy_m` of replicator-class deaths is at or
below one tenth of the cap (134 units for 21 bytes), the 99th
percentile is below a third of the cap, and capped absorbs are below
1% of absorbs.

It **fails** if in any seed the median `max_energy_m` after 25,000 is
above a third of the cap, or capped absorbs exceed 10% of absorbs.

Anything between is **partial**: some bodies bank. Report which
genotypes (by `birth_hash`, with their `classes.csv` class and absorb
count from `traits.py`) hold the top 1% of `max_energy_m`.

## What follows

- Holds: nothing changes; cite the numbers in the synthesis §2 B
  (replace "inference" with the measured figure) and in
  `hypotheses.md` under the H13–H15 note.
- Fails or partial: the `drain` proposal's condition 1 stands for the
  bodies that bank. T02 (cost in time) still goes first, because its
  argument from the literature does not depend on this. Add an
  income-take `drain` arm to the E016 design (synthesis §3.3) and note
  in E010's record that its "intruders are not energy-limited" reading
  should be re-read against the banking genotypes.

Either way: one paragraph in `docs/research/experiments/README.md`
under E007 (an addendum, dated), and the status line here.
