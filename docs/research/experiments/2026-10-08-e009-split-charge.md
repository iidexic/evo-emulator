# E009: the split charge (2026-10-08)

Status: design draft, written 2026-10-08 before any code for the split
exists and before any run. The calibration table and the arm choice are
to be filled in before the first world run; the predictions are fixed
now.

Bears on: H13 (E008: the full charge kills an entered host within one
intruder cycle, so there is no infected host for selection to grade, and
the registered next move was a softer charge or a cheaper defence), H12
(E007: hosts sweep a paying byte in 10,000 ticks, so selection strength
is not the limit), H14 (below), PLAN §9 (energy location), PLAN §10.

## Question

E008 made parasitism cost the host everything and got no defence; the
charge was so harsh that an entered host died within 13–18 ticks, before
any partial defence could pay, and the intruder then ran the corpse for
free. What happens when the host pays a share and survives the visit?
Two things become testable that E008 could not test:

1. Whether a graded cost (an infected host that lives, reproduces less,
   and dies later) is enough for selection to find any defence at all
   over 250,000 ticks.
2. Whether the defences that are already one or two bytes away get
   picked up once they pay. There are two known candidates, both found
   while reading E007 and E008:
   - **The endowment starver.** A host whose `lit A E` before `divide`
     has E ≥ 35 gives a one-byte `pad` running its loop nearly all of the
     intruder's store at the intruder's first `divide`, and the intruder
     starves (E007: 2 children against 340). Under E007 this cost the
     host nothing and gained it nothing; under E008 the host died anyway;
     under a split the host pays for one short pass and the intruder is
     gone. One byte, already at 13–19% of births in E007's last windows.
     It works against one-byte intruders only.
   - **The self-scan prefix.** `self 1` sets A to the IP and `self 0`
     sets A to the executor's body start (PLAN §5.3). At the host's byte
     0 these are equal for the host's own restart and for a newborn, and
     differ for a fall-through intruder. The prefix
     `self 1 ; swap C ; self 0 ; sub C ; jmpr A` (5 bytes; the first
     draft kept the IP in B, which `self 0` overwrites with the body
     length, see the calibration) leaves the
     host's A at 0, so `jmpr A` falls through for the host, and sends an
     intruder to its own start + 5 (`jmpr` adds A to the address after
     the op, and A = own start − host byte 0 was taken four bytes
     earlier). A 21-byte intruder sitting right before the host lands
     inside its own body. A one-byte `pad` right before the host has
     A = −1, so the jump lands on the `jmpr` itself and the intruder
     spins there until its store (at most 64 units) runs out, the host
     paying its share of each spin; under the split that is cheaper
     than a 260-unit pass and the intruder dies instead of
     reproducing. The harness must check both cases. The body's first `self` then resets
     A and B, so each of the first four insertions is neutral for the
     host apart from the cost of a longer body, and only the fifth needs
     the others in place; the order of the first four is partly
     constrained (`swap C` must sit between the two `self` forms). This
     is the Stringmol defence, expressible in the current ISA with no
     new op. It would have worked under E008 too (an intruder runs 5
     cheap ops instead of a 260-unit pass), and it did not appear in
     250,000 ticks; E009 measures how far along the path the population
     gets.

## Change under test

`--charge-owner-pct N` (`Config.charge_owner_pct`, integer 0–100,
default 0): for an instruction executed at a byte owned by a living
organism other than the executor, the owner pays `floor(cost × N / 100)`
or its whole store if that is less, and the executor pays the rest. The
executor must afford its own part by the usual base-cost rule; otherwise
nothing runs and its tick ends. An owner at zero therefore slows nothing;
the intruder pays full price on a drained host, as it does on debris.
This differs from `--charge-owner` (E008), where an owner that cannot pay
stops the intruder; the two flags are separate, and N = 100 is not E008.
N = 0 must be bit-identical to E007 (`census.csv` `6f523da9f7e05a4e`,
`births.csv` `33b07ce87cc80ea6` at tick 20,000 of seed 1). The counter
`paid_for_others_m` records the owner's share as in E008; a new
`paid_by_others_m` on the executor records what others paid for it, so
that per-organism ledgers still balance against `spent_m`.

Energy conservation holds as before: every unit charged leaves exactly one
store.

## Calibration (to do before the arms are fixed)

Two-genome harness, quiet default physics, 3,000 ticks, 100 units each,
`pad` before the host, for N in {10, 25, 50, 75, 100}:

| N | intruder exact | host exact | host alive at end | host death tick |
|---|---|---|---|---|
| 0 (E007 rule) | 340 | 211 | yes | – |
| 100 (E008 rule, for comparison) | 340 | 0 | no | 11 |
| 10 | 340 | 13 | no | 171 |
| 25 | 340 | 1 | no | 27 |
| 50 | 340 | 0 | no | 14 |
| 75 | 340 | 0 | no | 12 |
| 100 (split) | 340 | 0 | no | 11 |

Same table for the ancestor with K = 120 (E007's evolved host), for the
ancestor with E = 35, for a 21-byte fall-through parasite (E005's main
21-byte parasite before the ancestor), and for the ancestor carrying the
5-byte self-scan prefix, with each of its four intermediates alone (the
intermediate check is the path audit: each must be `replicator` class in
the single-genome harness and make within 10% of the ancestor's 230
children alone).

Filled 2026-10-08 (Opus, after the code; binary built from the working
tree). Host death ticks by bisection on `--harness-ticks`, as in E008.
Where the intruder dies first the harness stops (`stopped_early`); those
rows give the harness numbers, and the host's own births over the full
3,000 ticks come from a run that goes on after the intruder dies (the
harness test helper `run_on_with_host`), marked "run on".

`pad` before the ancestor with K = 120:

| N | intruder exact | host exact | host alive at end | host death tick |
|---|---|---|---|---|
| 0 | 189 | 140 | yes | – |
| 10 | 189 | 140 | yes | – |
| 25 | 189 | 140 | yes | – |
| 50 | 189 | 1 | no | 22 |
| 75 | 189 | 0 | no | 19 |
| 100 | 189 | 0 | no | 17 |
| E008 rule | 189 | 0 | no | 17 |

`pad` before the ancestor with E = 35 (the pad starves in every row; its
death tick is the harness's `ticks_run`):

| N | intruder exact | host exact | host alive at end | host death tick | pad death tick |
|---|---|---|---|---|---|
| 0 | 2 | 2 | yes | – | 27 |
| 10 | 7 | 4 | no | 54 | 71 |
| 25 | 4 | 1 | no | 27 | 46 |
| 50 | 2 | 0 | no | 14 | 27 |
| 75 | 2 | 0 | no | 12 | 27 |
| 100 | 2 | 0 | no | 11 | 27 |
| E008 rule | 2 | 0 | no | 11 | 28 |

E005's main 21-byte parasite before the ancestor (K = 64). Taken as the
largest 21-byte main parasite of E005's default-physics arm,
`p512_far_prop_rot` seed 4 (1,379 exact births in that run; the ancestor
with `copy` re-encoded and the closing `jmpa A` turned into `sub A`), hex
`13325271fc11401605086c5a5845486c11101c130f`:

| N | intruder births / exact | host exact | host alive at end | host death tick |
|---|---|---|---|---|
| 0 | 230 / 180 | 165 | yes | – |
| 10 | 230 / 180 | 165 | yes | – |
| 25 | 230 / 229 | 4 | no | 80 |
| 50 | 230 / 230 | 1 | no | 27 |
| 75 | 230 / 230 | 1 | no | 25 |
| 100 | 230 / 230 | 1 | no | 24 |

The self-scan prefix as written here does not work.
`self 1 ; swap B ; self 0 ; sub B ; jmpr A`: `self 0` sets B to the body
length as well as A to the body start (PLAN §5.3), so the IP saved in B
is overwritten, `sub B` leaves A = start − length, and `jmpr A` sends the
host itself out of its body. Alone the 26-byte host makes 0 children and
dies (`dies` at K = 64 and at K = 120); before it, `pad` makes 0 children,
and the host is dead by tick 4 at every N including 0.

The same defence with the IP kept in C, which `self 0` does not touch,
`self 1 ; swap C ; self 0 ; sub C ; jmpr A` (`33 52 13 4f 0c`), works as
the design describes. A = own start − IP: 0 for the host at its byte 0,
so `jmpr A` falls through; −1 for a `pad` right before the host, which
then lands on the `jmpr` and spins there. On the plain ancestor (K = 64)
it is not viable alone for a length reason (below: 5 children, dead at
tick 72). On the K = 120 ancestor it is a replicator alone (142 exact,
against 149 for the K = 120 ancestor). `pad` before the K = 120 prefixed
host:

| N | pad births | pad death tick | host exact (run on) | host alive at end (run on) | host death tick | host paid for pad (units) |
|---|---|---|---|---|---|---|
| 0 | 0 | 11 | 142 | yes | – | 0 |
| 10 | 0 | 10 | 142 | yes | – | 10.9 |
| 25 | 0 | 8 | 142 | yes | – | 32.75 |
| 50 | 0 | 11 | 142 | yes | – | 98 |
| 75 | 0 | 16 | 1 | no | 23 | – |
| 100 | 0 | 21 | 0 | no | 17 | – |
| E008 rule | 0 | 31 | – | no | 17 | – |

The pad-spin case: the pad does land on the `jmpr` and spin, and makes
no child at any N, but who dies depends on N. Each spin costs 1 unit;
the pad pays (100 − N)% of it, so a pad with store S spins S × 100 /
(100 − N) units' worth before it starves and the host pays S × N /
(100 − N): about S at N = 50 (98 units here, S = 100), 3S at 75 and
without bound at N = 100, where the pad pays nothing per spin and spins
on the host's store until the host is dead (then the pad pays full price
for three ticks and starves too). With the harness's 100-unit host, the
trap is survivable up to N = 50 and kills the host at 75 and 100. In the
world a one-byte pad holds at most 64 units and a 26-byte host up to
1,664, so at 75 the host would pay at most 192 units and survive; at 100
it still dies. The 26-byte prefixed K = 64 host with `pad` before it, run
on: host exact 5, 5, 3, 0, 0, 0 and death ticks 72, 72, 44, 17, 12, 11
for N = 0, 10, 25, 50, 75, 100 (pad 0 births throughout). E005's 21-byte
parasite before the K = 120 prefixed host is sent to its own start + 5,
makes 1 exact child and dies at tick 34–35 at every N; the host is alive
when the harness stops.

Path audit, single-genome harness (K = 64 unless stated, 230 for the
ancestor):

| prefix at byte 0 | bytes | class | exact children | within 10% of 230 |
|---|---|---|---|---|
| `self 1` | 22 | replicator | 230 | yes |
| `self 1 ; swap B` | 23 | replicator | 222 | yes |
| `self 1 ; swap B ; self 0` | 24 | replicator | 214 | yes |
| `self 1 ; swap B ; self 0 ; sub B` | 25 | replicator | 11 (dead by tick ~155) | no |
| full prefix, as designed | 26 | dies | 0 | no |
| `swap C` / `sub C` intermediates 2–4 | 23–25 | replicator | 222, 214, 11 | yes, yes, no |
| full prefix through C | 26 | replicator | 5 (dead at tick 72) | no |
| full prefix through C, K = 120 | 26 | replicator | 142 (ancestor K = 120: 149) | yes, against 149 |

The fourth intermediate's failure is length, not content: four inert
`zero D` bytes before the ancestor also give 11 exact children and death
(1, 2, 3 inert bytes give 230, 222, 214, as the intermediates do). At
K = 64 and E = 16 a body of 25 bytes or more loses about 8 units per
cycle in the harness and runs down from its 100-unit start. At K = 120
the intermediates make 149, 146, 142, 142, all within 10% of the K = 120
ancestor's 149. So the path is neutral on hosts that have already taken
the absorb sweep (K ≥ 112 by window 1 in E007 and E008), and blocked by
length on the founder.

Calibration results (2026-10-08). By the rule below, the plain ancestor
is alive at the end with ≥ 50 children of its own at no N ≥ 10, so
`hi` = 10 and `lo` = 5. The harness shows a cliff, not a grade: with
`pad` before the plain ancestor the host makes 211 children (the N = 0
count) at every N from 1 to 8, and dies at N = 9 (25 children) and above.
Below the cliff the host rides at its store cap and pays out of energy it
would have lost to the cap (4,756 units over the run at N = 5); above it
the share outruns its income. The K = 120 host has the same cliff
between 25 and 50. So in the harness `lo` = 5 is the E007 result
exactly and `hi` = 10 kills the founder within 171 ticks; whether the
world (larger stores, crowded pools) turns either into a graded cost is
what the runs measure.

Arm choice, first rule (superseded the same day, kept for the record):
`hi` is the largest N in the table at which the plain ancestor is alive
at the end of the probe run with at least 50 exact children of its own;
`lo` is the next value down. By that rule `hi` = 10 and `lo` = 5.

Arm choice, second rule (2026-10-08, after the harness calibration and
before any 250,000-tick run). The harness is the wrong instrument for
this choice: a `pad` in the harness runs every tick for 3,000 ticks, so
the host faces a constant drain against a constant income and the result
is a cliff (free below N = 9 for the founder and below N = 50 for the
K = 120 host, dead above). In the world an intrusion is intermittent and
the host's store is 13 times the harness's. So the arms are chosen in
the world: three 25,000-tick runs of seed 1 at N = 10, 25 and 50 (one
window), classified as usual, read with the E009 runner's graded-cost
table. `hi` is the largest N at which, over replicator-class deaths in
ticks 5,000–25,000, the mean exact children per lifetime of organisms
that had paid for others is 0.5–0.9 of the non-paying mean and their
median age at death is at least 1.5 times the non-paying median (the
prediction-2 quantities); `lo` is the next value down among {10, 25, 50},
or 10 if `hi` = 10 then `lo` = 5. If no N in the set meets both,
`hi` is the N whose kids ratio is nearest 0.7 and the design says so
here before the runs. Prediction 2 is then not a test of seed 1's first
window, which chose the arm; it is a test of windows 2–10 across the
other seeds, and is kept as written on that understanding. The chosen
values and the seed-1 numbers go here.

World calibration, filled 2026-10-08 (Opus). Seed 1, standard world,
25,000 ticks, census every 500, run and classified by the runner's
`run_one` under the arm's flag (`runs/e009_calib/n<N>/s1/`). Kids and age
ratios (paid / unpaid) over replicator-class deaths in ticks 5,001–25,000;
paid share and energy share over all of ticks 0–25,000 (E008's window-1
basis; over 5,001–25,000 they are 6.28/8.92/11.59% and 0.67/1.11/1.33%);
foreign and unowned at the tick-25,000 census; absorb median over
replicator-class exact births of 21-byte bodies in the window. E008 window
1 for comparison: 12.75% paid, 1.54% energy, 0.46% foreign, 6.78%
unowned, population 945, absorb 112.

| N | kids ratio | age ratio | paid share | energy share | foreign | unowned | population | absorb median |
|---|---|---|---|---|---|---|---|---|
| 10 | 6.99 (4.92 / 0.70) | 1.11 (20 / 18) | 6.70% | 0.73% | 9.68% | 2.85% | 928 | 112 |
| 25 | 5.73 (3.86 / 0.67) | 1.06 (19 / 18) | 9.44% | 1.23% | 3.57% | 6.02% | 908 | 112 |
| 50 | 4.53 (3.09 / 0.68) | 1.00 (18 / 18) | 11.86% | 1.49% | 1.28% | 5.96% | 929 | 112 |

No N meets either condition: the kids ratio is above 0.9 at every N (4.5–7)
and the age ratio is below 1.5 at every N (1.00–1.11). By the fallback,
`hi` is the N whose kids ratio is nearest 0.7, which is 50 (4.53), and
`lo` = 25. The paying organisms have more exact children than the
non-paying ones, not fewer, falling with N (7.0 to 4.5 times) while the
median age stays at 18–20 for both: having paid marks an organism that
lived and copied long enough to be entered, so the ratio as defined
measures exposure as much as cost, and prediction 2's 0.5–0.9 band is
not reachable on this basis at any N tried. Foreign execution falls
from E007-like (9.7% at N = 10) toward E008 (1.3% at N = 50).

## World and runs

The standard world (code default, E007) plus `--charge-owner-pct N`, two
arms, seeds 1–10, 250,000 ticks, census every 500, recorded, classified
and analysed as E008 was (`analysis/e009_split_charge.py`, forked from
the E008 runner, output `runs/e009/<arm>/s<seed>/`). Harness classes and
every `--host` call use the arm's flag. About 20 minutes of wall time on
the Linux machine at E008's rate and about 22 GB.

## Measures

Everything E008 measured per window of 25,000 ticks (persistence, E005
parasite tables, the `pad` probe before the window's top host, paid
replicator deaths, energy paid for others, foreign and unowned execution,
absorb and endowment traits, canonical genotypes). Changes and additions:

- **Probe labels.** Per seed-window the top host is one of: *defended*
  (alive at the end, ≥ 50 own exact births, probe not `stopped_early`),
  *starver* (alive at the end, probe `stopped_early`), *survivor* (alive,
  fewer than 50 own births, probe ran to the end), *dead* (host dead at
  the end, with its death tick). E008 folded starvers into "not
  defended"; here they are the endowment candidate and are counted.
- **Graded cost.** Over replicator-class deaths in the window: the median
  age at death and the share that had divided, split by whether
  `paid_for_others_m` is above 0 (E008: 19 ticks both, 36% against 26%).
  And the mean exact children per lifetime of paying against non-paying
  replicator-class organisms that died in the window.
- **Endowment trait.** From `traits.py` as in E007 and E008: the share of
  replicator-class exact births with endowment ≥ 37 (over all births, not
  only those keeping `lit`), per window.
- **Self-scan progress.** Over replicator-class exact births per window:
  the share whose genome executes `self 1` anywhere (the op appears with
  modifier 1 in the canonical genome), the share whose first instruction
  is not `self 0`, and the length of the longest prefix of
  `self 1 ; swap C ; self 0 ; sub C ; jmpr A` present at byte 0 (0–5),
  as a histogram. Prefix length 5 is the complete defence.
- **Intruder fate.** Per window, over births whose parent executed
  foreign code (`exec_foreign` above 0 at birth): the share by one-byte
  parents and by 21-byte parents, to see which intruder kind the hosts
  are selected against.
- **Trait-tracked sweeps.** Prediction-6-style leader counts are dropped.
  Sweeps are read as per-window medians and 10th/90th percentiles of
  absorb count, endowment and body length over replicator-class exact
  births, with `func_hash` for genotype counts.

## Predictions

Written to be wrong if the world disagrees. Medians are across surviving
seeds unless stated; "last window" is window 10.

1. Persistence: replicating at tick 250,000 in at least 7 of 10 seeds in
   both arms; population at the end a median of 700–1,100. The cost
   falls on entered hosts, 12% of replicator deaths in E008.
2. The cost is graded. First wording (superseded 2026-10-08 before any
   250,000-tick run, see the calibration block): paying replicator-class
   deaths have a median age at least 1.5 times the non-paying and a mean
   exact-children-per-lifetime 0.5–0.9 of the non-paying mean. The
   seed-1 calibration showed that comparison is confounded: organisms
   that had paid had 4.5–7 times the exact children of those that had
   not at equal median age, because being entered marks an organism that
   lived in a dense colony long enough to have a neighbour run into it.
   Second wording, fixed before the runs: the comparison is made within
   age bands. Over replicator-class deaths in windows 2–10, in each of
   the age bands 20–39, 40–79 and 80–159 ticks, the mean exact children
   of organisms whose `paid_for_others_m` is at least 10% of their
   `spent_m` is 0.5–0.9 of the mean for organisms in the same band that
   paid nothing, in the `hi` arm, as a median across seeds and bands.
   Below 0.5 the charge is still a kill; above 0.9 there is nothing to
   select on, and either way the arm is uninformative about defence. The
   runner adds the banded table; the unbanded ratio stays in the file as
   the exposure measure it turned out to be.
3. Parasitism returns to the E007 form: in the `hi` arm the parasite share
   by the E005 test is 0.3–1.5% of exact births in windows 2–10 (E007
   0.77–1.03%, E008 0.03–0.07%), and foreign execution over living bodies
   is 5–15% (E007 12–15%, E008 0.4%).
4. The endowment starver is selected: in the `hi` arm the share of
   replicator-class exact births with endowment ≥ 37, over all such
   births (E007 measured 13–15% in windows 9–10 on that basis; the
   18–19% figure there is over births keeping `lit` at byte 16), is
   above 15% in windows 9 and 10 in at least 6 of the surviving seeds,
   and the median across seeds of the mean of those two windows is at
   least 30%. (Baseline wording corrected 2026-10-08 before any run,
   when the runner was written: the first draft named the 18–19%
   figure, which is on the other basis.) (E007: a drift with a widening
   tail, no common direction; here the tail pays.) The `lo` arm shows the
   same direction with a smaller median.
5. The self-scan is not found: the complete 5-byte prefix is at byte 0 in
   fewer than 1% of replicator-class exact births in every window of
   every seed in both arms, and no prefix of length ≥ 3 is above 5% of
   births in any window. Reasoning: four neutral insertions of specific
   bytes at specific positions must each drift to high frequency in a
   population of about 1,000 before the fifth pays; insertion here is
   `q_slip` duplication plus write flips, and E008 ran the same path
   under a stronger payoff without finding it.
6. Defence, H14: a *defended* top host (the probe label: alive at the
   end, probe ran to the end, host made ≥ 50 children; a self-scan is
   the expected mechanism but the label is by the probe outcome alone)
   in the last window in at most 2 of the surviving seeds; a *starver* top host in the last window
   in at least 4 of the surviving seeds of the `hi` arm. The first
   evolved defence in this project, if it comes, is the endowment, and it
   is a defence against one-byte intruders only.
7. Exploratory, no threshold: the fate of 21-byte intruders (they are not
   starved by the endowment because a 21-byte body holds 1,344 units);
   whether top hosts with high endowment also change their absorb count;
   the absorb sweep's course (expected unchanged: 112 by window 1, 120 by
   window 2); whether the `pad` lineage falls back to E007 size; median
   age at the end against E007's 1,368 and E008's 769.

If 4 and 6 hold and 5 holds: a cost that leaves the host alive is enough
for selection to pick up a one-byte defence that was already drifting,
and the five-byte defence is out of reach by neutral drift at this
population and mutation supply. The next move is then to shorten the
path (an op that compares IP to own start in one byte, or `self 1` made
to set the fail flag when IP is outside the body, so that `self 2 ;
skipz A` reads it) and rerun the `hi` arm; that is the 2 × 2 of cost
against path length that PLAN §10's "immunity" needs. If 4 fails while 2
holds, a paying one-byte defence that is already present at 13–19% does
not rise, and the fitness accounting (prediction 2's numbers) is read
before anything else. If 2 fails, the arm choice was wrong and the
calibration is redone in the world rather than the harness. If 5 fails,
the self-scan genomes are read and their path reconstructed from the
ancestry tables; that is the result of the year.

## Code changes needed (Opus, after this design is agreed)

- `Config.charge_owner_pct: i64`, `--charge-owner-pct N`, in `fields()`;
  `OrgStats.paid_by_others_m` (last column after `paid_for_others_m` in
  `orgs.csv` and `deaths.csv`); the split in `Sim::step`, with the owner
  resolved as in E008's `charge_owner` branch.
- Tests: N = 0 bit-identical to the E007 hashes above; the ledger test
  from E008 extended to the split (every store balances, world totals
  conserved); a harness test that the ancestor with the 5-byte prefix
  survives `pad` and makes children at N = 100, and that each
  intermediate is `replicator` class alone.
- `analysis/traits.py`: endowment share over all births; `self 1`
  presence; first-instruction op; prefix length at byte 0.
- `analysis/e009_split_charge.py`: fork of the E008 runner with two arms,
  the probe labels, the graded-cost table and the prediction checks.
- `docs/instrumentation.md`: the new column and the new traits.

## Caveats, known now

- 10 seeds per arm, one founder per run.
- The probe is `pad` only; a starver label says nothing about 21-byte
  intruders, which prediction 7 reads but does not test.
- "Paid for others" marks a death as entered, not as killed; prediction
  2's age comparison is between entered and unentered organisms, which
  differ in other ways (position next to an intruder, for one).
- The self-scan prefix is one of several possible self-scans; the prefix
  histogram tracks that one. The `self 1` share and the first-instruction
  share are the broader nets.
- Classes are written under the arm's flag, as in E008; a lone genome
  pays nothing for others, so the flag should not change classes, to be
  checked on one seed as E008 did.
