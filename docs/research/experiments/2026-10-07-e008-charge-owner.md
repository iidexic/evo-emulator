# E008: parasitism that costs the host (2026-10-07)

Status: design and predictions written 2026-10-07 before any E008 run
longer than one 25,000-tick smoke run at seed 1 (used only to check
that the switch runs and the population persists: 934 organisms at tick
25,000) and the harness calibrations below.

Bears on: H12 (E007: hosts do not evolve resistance to parasites that
cost them nothing, and the pre-registered branch for "4 holds" was to
make parasitism costly before expecting immunity), H13 (below), PLAN
§5.5 (defence costs energy; a drain op is Phase 3), PLAN §9 (energy
location, "revisit with drain"), and the E007 finding that hosts sweep a
beneficial trait in about 10,000 ticks, so selection is not the
bottleneck.

## Question

E007 showed the standard world's hosts change fast when a trait pays
(the absorb count, 64 to 112–127 inside 10,000 ticks in every seed) and
never change against parasites over 250,000 ticks. The physics argument
was that a fall-through parasite runs the host's copy loop with its own
energy, so the host loses nothing selection can act on. What happens when
the host pays?

## Change under test

`--charge-owner` (`Config.charge_owner`, default off): an instruction
executed at a byte owned by a living organism other than the executor is
paid from that owner's store, not the executor's. If the owner cannot pay
the op's base cost the instruction does not run and the executor's tick
ends, as it would if the executor itself could not pay. The executor's
per-tick instruction cap, registers, `self`, write protection, `absorb`
income (still credited to the executor) and `divide` endowment (still
taken from the executor) are unchanged. The executor's own body and
pending region are its own; a dead owner's bytes are debris and are
executed at the executor's cost as before. A new per-organism counter
`paid_for_others_m` (last column of `orgs.csv` and `deaths.csv`) records
what an organism paid for instructions others executed in its body; it is
0 with the flag off, and the flag-off world is bit-identical to E007's
(census.csv and births.csv hashes unchanged at tick 20,000 of seed 1;
deaths.csv and orgs.csv differ only by the added column).

Analog: a parasite that uses a host's machinery consumes the host's
resources. This is the whole of the cost; it is not a drain op (the
intruder takes nothing into its own store) and not a split (the intruder
pays nothing while in the host). The intruder gets the free ride it had,
and the host pays for it.

What the two-genome harness says before the runs (`--host`, quiet
default physics, 3,000 ticks, both bodies start with 100 units; the
harness stops if the intruder dies):

| body before the host | host | rule | intruder exact births | host exact births | host alive at the end |
|---|---|---|---|---|---|
| `pad` | ancestor (K = 64, E = 16) | executor pays | 340 | 211 | yes |
| `pad` | ancestor | owner pays | 340 | 0 | no, dies at tick 11 |
| `pad` | ancestor with K = 120 (E007's evolved host) | executor pays | 189 | 140 | yes |
| `pad` | ancestor with K = 120 | owner pays | 189 | 0 | no |
| `pad` | ancestor with E = 35 | executor pays | 2 (intruder starves, tick 28) | 2 | yes |
| `pad` | ancestor with E = 35 | owner pays | 2 (intruder starves) | 0 | no |
| 21 pads | ancestor | executor pays | 214 | 141 | yes |
| 21 pads | ancestor | owner pays | 214 | 0 | no |

Under the owner rule the intruder's yield does not change (its birth rate
is set by its own per-tick cap, not by who pays) and every host tested
dies before its first child: one pass of the intruder through the absorb
loop costs about 260 units and the host starts with 100. The E007
"endowment ≥ 35" side effect, which starved a `pad` after one child, now
kills the host as well, so it is not a defence under this rule. In the
world a host holds up to 1,344 units (64 per byte), so it can survive a
few intruder cycles there, not in the harness.

Smoke run (seed 1, 25,000 ticks, `--charge-owner`): population 934 at
the end against 953 without the flag at tick 20,000; births 338,236
against about 300,000; the foreign-execution share of instructions over
living bodies at the last census is 0.4% (E007 world: 13.8%) and the
unowned-execution share 6.1%; 277 of 934 living bodies have paid for
others; 13% of all deaths in ticks 20,000–25,000 are of organisms that
had paid for others. So hosts that are run die quickly, their bytes
become debris, and the intruder goes on running the dead host's code at
its own cost.

## World and runs

The standard world (code default, E007) plus `--charge-owner`. One arm,
`co`. Seeds 1–10, 250,000 ticks, census every 500, recorded, classified
and analysed exactly as E007 was (`analysis/e008_charge_owner.py`,
output `runs/e008/co/s<seed>/`), so every E007 table has a matching one
here. Harness classes and the E005 parasite tables use the arm's physics
(`--charge-owner` passed to `--classify` and `--host`), as E005 did per
arm; the two-genome harness then has the host paying.

## Measures

Everything E007 measured, in the same ten windows of 25,000 ticks
(persistence, E005 parasite tables, top host, parasite / trampoline /
dependent shares, the resistance test with the run's main parasite, and
the post-hoc additions: canonical genotypes, absorb and endowment trait
bytes from `traits.py`). Added:

- **Defence probe.** Per window, the one-byte `pad` before the window's
  top host in the two-genome harness under the arm's physics, 3,000
  ticks: `pad`'s exact births, the host's exact births, whether the host
  is alive at the end, `ticks_run` and `stopped_early`. `pad` is a fixed
  probe so the test does not depend on a parasite lineage existing in
  the run. The run's main parasite is tested too when the E005 test
  finds one. Baseline: `pad` before the ancestor under this rule gives
  340 and 0, host dead.
- **Defended** top host: alive at the end of the probe run, and ≥ 50
  exact births of its own with `pad` there (the ancestor alone makes 230
  in 3,000 ticks; with `pad` there and no charge, 211). A host that
  survives only because the probe starved (`stopped_early`) is not
  defended.
- **Hosts killed by intruders.** Per window, the share of
  replicator-class deaths whose `paid_for_others_m` at death is above 0,
  and the share of all energy spent that was paid for others.
- **Execution shares.** Foreign and unowned execution as shares of
  instructions executed, over living bodies at the window's last census
  (E007 world at tick 20,000: 13.8% foreign).

## Predictions

1. Persistence: replicating at tick 250,000 in at least 7 of 10 seeds;
   population at the end a median of 700–1,100 (smoke run: 934 at
   25,000). The cost falls on hosts that are entered, and hosts are
   entered rarely (0.4% foreign execution in the smoke run).
2. The absorb sweep repeats: the median absorb count of replicator-class
   exact births in window 1 is ≥ 96 in at least 8 of the surviving
   seeds, and ≥ 112 in window 2 (E007: 112 at tick 10,000, 120 at
   25,000). The sweep was not parasite-driven and the energy rules
   inside a body are unchanged.
3. Parasites by the E005 test become rare and their share moves to
   debris-runners: the median across seeds of the parasite share of
   exact births is below 0.3% in every window from the second on (E007:
   0.77–1.03%), the trampoline share (dependent, foreign share below
   0.05) is at least 0.025 in every window from the second on (E007:
   0.016–0.019), and the dependent share stays at least 0.05 (E007:
   0.110–0.119). A `pad` that enters a host kills it within a cycle and
   then runs its debris, so its foreign share falls below the test's
   0.25.
4. Hosts pay: the share of replicator-class deaths with
   `paid_for_others_m` above 0 is at least 5% in window 1, median across
   seeds (smoke run: 13% of all deaths, ticks 20,000–25,000).
5. No defence (H13): a defended top host in the last window in at most 2
   of the surviving seeds, and the median across seeds of the host's
   exact births with `pad` present in the last window is below 50. The
   trap has to fire within about 100 instructions of entry (the host
   has 100–1,344 units and one intruder pass costs about 260), on a
   register difference between an intruder and the host's own restart,
   and the host's own restart has to pass it; this is still several
   coordinated mutations, now with a payoff once complete but none
   before. If 5 fails, the defended hosts' genomes are read for the
   mechanism, and that is the first evolved defence in the project.
6. The cost shows in time: the share of replicator-class deaths with
   `paid_for_others_m` above 0 in the last window is within a factor of
   2 of window 2 in at least 7 of the surviving seeds. (If 5 fails it
   should fall instead.)
7. Exploratory, no threshold: the endowment byte per window (E007:
   drift); the depth and share of one-byte lineages; the share of energy
   paid for others; the fate of the window's top host in the probe
   (`ticks_run` when it dies).

If 5 holds, a cost alone does not produce a defence on this timescale,
and the next move is to make a defence cheaper to find rather than the
cost larger: an op or `self` form that tells an organism who is running
its code (PLAN §5.3 `self 1`, Stringmol's self-scan), or a softer charge
(a split) that lets a host survive an intruder long enough for a partial
defence to pay. If 1 fails, the full charge is too harsh and the split
is the next arm. If 3 fails and parasites by the E005 test persist at
E007's rate, the cost is not reaching them and the accounting is read
before anything else.

Machine. Same as E007 (Linux, rustc 1.95.0). The E007 determinism
reference for deaths.csv (`81eed2b39fd47163`) no longer applies because
of the added column; census.csv `6f523da9f7e05a4e` and births.csv
`33b07ce87cc80ea6` at tick 20,000 of seed 1 with no flags still do.

## Results (2026-10-07)

Run on Linux (CachyOS, rustc 1.95.0) from commit 9dcc89a with the
`--charge-owner` change uncommitted (`git_dirty` in meta.json), using
`analysis/e008_charge_owner.py` with no flags: 10 runs of 250,000
ticks, 138–154 s of simulation and 363–393 s of classification each,
10.5 minutes in all; output in `runs/e008/` (`summary_e004.md`,
`summary.md`, `summary_windows.md`, `runs_e004.csv`, `runs.csv`,
`windows.csv`, per-run dependent tables), 11 GB in all. Seed 10 lost
its founder as in E004 and E007: 3 births, extinct at tick 1,179.

Classification. `classes.csv` was written with `--charge-owner` and
copied to `classes_world.csv`, so "replicator-class" and the E005
world class both mean the arm's physics. A lone genome executes no
foreign code, so the flag should not matter there, and it does not:
seed 1 reclassified without the flag gives the same class for all
686,445 genomes (336 differ in instructions executed, none in births).
Deaths are classed by `birth_hash`, as in E004's death tables;
`now_hash` is missing from genomes.csv for 2.4–3.0% of a window's
deaths. The share of energy paid for others is the sum of
`paid_for_others_m` over a window's deaths divided by the sum of their
`spent_m` (lifetime totals of the organisms that died in the window).

### Numbers

Medians across the 9 seeds replicating at the end (seeds 1–9), per
window of 25,000 ticks. Parasite, trampoline, dependent and one-byte
shares are of the window's exact births; the probe is `pad` before the
window's top host in the two-genome harness under this rule; paid
deaths are replicator-class deaths with `paid_for_others_m` above 0;
execution shares are lifetime counters summed over the bodies alive at
the window's last census.

| window | ticks | population | parasite share | trampoline share | dependent share | one-byte share | probe exact | host exact with probe | host death tick | replicator deaths that paid | energy paid for others | foreign exec | unowned exec | absorb median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0–25,000 | 945 | 0.10% | 0.042 | 0.172 | 1.13% | 224 | 0 | 15 | 12.75% | 1.54% | 0.46% | 6.78% | 112 |
| 2 | 25,000–50,000 | 942 | 0.07% | 0.037 | 0.151 | 0.92% | 189 | 0 | 17 | 11.95% | 1.20% | 0.39% | 6.89% | 120 |
| 3 | 50,000–75,000 | 939 | 0.05% | 0.033 | 0.149 | 1.13% | 187 | 0 | 17 | 12.06% | 1.14% | 0.45% | 6.73% | 122 |
| 4 | 75,000–100,000 | 949 | 0.04% | 0.034 | 0.150 | 0.93% | 183 | 0 | 17 | 12.02% | 1.14% | 0.39% | 7.28% | 123 |
| 5 | 100,000–125,000 | 930 | 0.06% | 0.037 | 0.146 | 1.00% | 183 | 0 | 17 | 11.73% | 1.08% | 0.41% | 7.08% | 124 |
| 6 | 125,000–150,000 | 943 | 0.04% | 0.035 | 0.148 | 1.02% | 182 | 0 | 17 | 12.07% | 1.13% | 0.42% | 7.01% | 124 |
| 7 | 150,000–175,000 | 937 | 0.04% | 0.035 | 0.142 | 0.76% | 182 | 0 | 17 | 11.55% | 1.09% | 0.38% | 6.89% | 125 |
| 8 | 175,000–200,000 | 933 | 0.03% | 0.036 | 0.146 | 1.25% | 181 | 0 | 17 | 11.46% | 1.08% | 0.40% | 6.40% | 125 |
| 9 | 200,000–225,000 | 932 | 0.04% | 0.033 | 0.150 | 0.82% | 181 | 0 | 17 | 12.26% | 1.17% | 0.42% | 7.26% | 124 |
| 10 | 225,000–250,000 | 932 | 0.03% | 0.035 | 0.147 | 1.07% | 181 | 0 | 17 | 12.05% | 1.13% | 0.41% | 7.33% | 124 |

E007 in the same windows (2–10), for comparison: parasite share
0.77–1.03%, trampoline 0.016–0.019, dependent 0.110–0.119; and, read
from E007's files for this comparison, one-byte share 0.37–0.64%,
foreign execution 12.2–14.8%, unowned execution 1.6–2.0%.

Per seed-window (90 in all): the host makes 0 exact children with
`pad` present in every one, and is dead by tick 13–18 of the probe
(13–17 in window 1, 16–18 after); `pad` makes 179–277 exact children,
except seed 7 window 4, whose top host has endowment 38: there `pad`
makes 2 and starves at tick 41 (`stopped_early`), and the host is dead
at tick 16 anyway. Replicator deaths that paid are 10.7–14.1% of a
window's replicator deaths, the energy paid for others 0.9–1.7% of
energy spent, foreign execution 0.28–1.15%, unowned execution
4.1–12.2%, parasite share at most 0.15% in any seed-window, trampoline
share 0.029–0.050, dependent share 0.133–0.178. Population is 880–1,007
at every window end. The absorb median is 106–113 in window 1, 118–122
in window 2 and 121–126 after.

The nine last-window top hosts are 21-byte ancestor variants with
absorb counts 113–127 and endowments of 9–20; re-probed under the
executor rule (no flag) they make 136–143 exact children with `pad`
there and live, as E007's hosts did (136–140). Under the owner rule
all of them make 0 and die.

The paying deaths (ticks 25,000–250,000, medians over seeds) had paid
62–64 units for others, 12% of their lifetime spending, and 54–55% had
paid at least 50 units. Their median age at death is 19 ticks, the same
as the replicator deaths that had not paid; 36% of them had divided
(26% of the others).

Parasites by the E005 test: 23–41 lineages per run (E007: 171–228),
28,141–29,697 dependent genomes (E007: 20,331–21,166). The main
parasite is a 21-byte ancestor variant in 8 seeds and the one-byte
`divide C` in seed 5; the 21-byte ones (60–212 exact children each,
`one_shot` alone) have lost the ancestor's closing `self 0 ; jmpa A`
or broken it, so after `divide` they fall off their end into whatever
follows. Before the ancestor they make 176–230 exact children (seed
2's makes 3 and starves), and the ancestor makes 0–2 and dies in all
nine. The resistance ratio (E007's test) is 0.80–0.86 by window median
and 0.57–1.00 per seed in the last window, but with the host dead in
every run it measures how well the parasite runs on a dead host's
code, not resistance.

The `pad` lineage is not a parasite by the test any more. Over each
run it makes 8,960–12,536 exact children (E007: 3,251–7,159) with
generation depth 6–12 (E007: 5–10); its carriers with two or more
children execute 4–6% of their instructions in a living body and
94–96% in free or debris memory (E007: 27–44% and 56–73%).

Persistence (E004 measures, medians over all 10 seeds): replicating at
the end 9 of 10, last replicator census 250,000, population at end 930
(917–954 per surviving seed), 128 of 128 patches occupied, median age
at end 769 (669–1,019; E007: 1,368), non-replicator share of living
bodies 0.74 (E007: 0.76), 3,010,407 births (E007: 2,580,315),
stillborn share 0.03 (E007: 0.02), newborn share of replicator deaths
0.24 (E007: 0.24).

### Predictions

1. Replicating at the end in ≥ 7 of 10, population 700–1,100:
   **confirmed**, 9 of 10 (seed 10 died at tick 1,179), median
   population 932 over the surviving seeds.
2. Absorb sweep: **confirmed**. The median absorb count of
   replicator-class exact births is ≥ 96 in window 1 in 9 of 9 seeds
   (106–113) and ≥ 112 in window 2 in 9 of 9 (118–122); medians 112 and
   120, the E007 course exactly.
3. Parasites rare, their share moved to debris-runners: **confirmed**
   on all three thresholds. Parasite share medians 0.03–0.07% in
   windows 2–10 (< 0.3% wanted; E007 0.77–1.03%); trampoline share
   0.033–0.037 (≥ 0.025 wanted; E007 0.016–0.019); dependent share
   0.142–0.151 (≥ 0.05 wanted; 0.172 in window 1). The mechanism named
   in the prediction is what the `pad` rows show: its foreign share
   fell from 0.27–0.44 to 0.04–0.06, below the test's 0.25, and its
   output roughly doubled.
4. Hosts pay: **confirmed**, 12.75% of replicator-class deaths in
   window 1 had paid for others (≥ 5% wanted; 12.05–14.12% per seed).
5. No defence (H13): **confirmed**. A defended top host in the last
   window in 0 of 9 seeds (≤ 2 wanted), and in no window of any seed;
   the median host exact births with `pad` present in the last window
   is 0 (< 50 wanted), and 0 in all 90 seed-windows.
6. The cost shows in time: **confirmed**. Paid replicator deaths in the
   last window are 0.90–1.06 times window 2 in 9 of 9 seeds (within a
   factor of 2 wanted in ≥ 7); medians 11.95% and 12.05%.
7. Exploratory. Endowment median 16–20 in every window; the share of
   births with endowment ≥ 37 (of those whose byte 16 is still `lit`)
   is 4% in window 1 and 6–10% after, 8% in the last window (E007: 5%,
   then 18–19% in windows 9–10), so the upper tail grew less than in
   E007, where it was the one side effect that hurt `pad`; one run per
   seed, so this is a direction to watch, not a result. One-byte
   genomes are 0.8–1.3% of exact births per window (E007 0.4–0.6%) and
   their deepest dependent lineage per run is 6–17 generations; one
   one-byte parasite lineage in all nine runs. The energy paid for
   others is 1.1–1.5% of energy spent. In the probe the top host dies
   at tick 15 in window 1 and 17 after. The ancestor dies at 11, and the
   ancestor with only the absorb count changed dies at 15 (96), 16
   (112), 17 (120) and 18 (127): the longer absorb loop is all of the
   difference.

### What this says

- **H13 supported on its registered test: a cost alone did not produce a
  defence.** Every top host in every window of every seed, probed with
  `pad`, dies within 18 ticks without a child, and nothing moved over
  250,000 ticks: the host's death tick, the paid share of replicator
  deaths and the energy share paid for others are flat from window 2
  to 10. The hosts are the E007 hosts: under the executor rule they
  make 136–143 children with `pad` there, as E007's did. The branch
  registered for "5 holds" applies: make a defence cheaper to find
  (`self 1`, a self-scan) or the charge softer (a split), not the cost
  larger.
- **The cost is paid, but it is small and mostly falls on hosts that
  are already finished.** About 12% of replicator deaths had paid
  something (median 63 units, an eighth of their own spending), but the
  energy paid for others is 1.1–1.5% of all energy spent. Under this
  rule a host that is entered dies within one intruder cycle, so the
  intrusion ends with the host; there is no long-lived infected host
  whose fitness loss selection could act on gradually, and the
  population (930), patch occupancy and replicator count are E007's.
- **Parasitism changed form rather than going away.** Foreign execution
  fell from 12–15% of instructions to 0.4%, and unowned execution rose
  from 1.6–2.0% to 6.4–7.3%: the intruders now run a host's code after
  the host is dead. `pad` is the clearest case: by the E005 test it is
  now a debris-runner, not a parasite, and its lineage is larger than
  in E007 (one-byte genomes are 1% of exact births against 0.5%). The
  E005 test's foreign-share threshold no longer tracks "uses a host"
  under this rule, because using a host kills it and turns it into
  debris within ticks. The remaining parasite lineages by the test are
  mostly 21-byte copies of the host design that have lost their closing
  jump and restart on the next body's code; each makes about 100
  children over a run.
- **Turnover went up.** The median age of the living at the end is 769
  ticks against E007's 1,368, with 17% more births and the same
  population. Some of that is hosts killed by intruders; how much is
  not separated here.
- **The absorb sweep is independent of the payment rule**: 112 by
  window 1 and 120 by window 2 in all nine seeds, as in E007 and in the
  self-owner runs, which is the third physics in which it happens.

### Caveats

- 10 seeds, one founder per run; 9 surviving seeds carry every median.
- The probe is one fixed intruder (`pad`) against one host per window,
  in a 3,000-tick quiet harness with 100 units each. A host in the
  world holds up to 1,344 units and could outlast an intruder there
  that kills it in the harness; "defended" is a harness label. A
  defence against other intruders, or one that works only in the
  crowded world, would not show.
- "Hosts killed by intruders" is measured as deaths that had paid
  anything for others; whether paying caused the death is not
  measured. Paying and non-paying replicator deaths have the same
  median age (19 ticks).
- The energy share is a proxy: lifetime spending of the organisms that
  died in a window, not the energy spent in the window. The two agree
  over a stationary run, which windows 2–10 are.
- Classes: written under `--charge-owner`; checked against the
  executor rule on seed 1 only (identical classes). Deaths are classed
  by birth genome, so a host whose body changed after birth is counted
  by what it was born as.
- The E005 parasite test and the E007 resistance ratio were kept as
  registered, but under this rule they measure different things: the
  test's 0.25 foreign-share threshold excludes intruders that kill
  their hosts fast, and the resistance ratio compares the parasite's
  yield on a dead host's code. Neither is evidence about defence here;
  the probe is.
- Exploratory item 7's host death tick was found by bisection on the
  harness length (the harness reports only when the intruder died), so
  it is exact for this deterministic harness but is not a harness
  output.
