# E003: crash diagnosis with the Phase 2 instrumentation (2026-10-03)

Status: run 2026-10-03 with the first instrumentation build
(`docs/instrumentation.md`), committed as 2ec7aa7. The runs were made
before that commit, so their `meta.json` shows df11a9a with `git_dirty`
true. The physics is unchanged from df11a9a (stdout and instruction
counts identical seed for seed). Diagnostic run: no predictions were written beforehand. The question
comes from the post-hoc section of E002.

Bears on: H5 (turnover), H6 (absorb-loop takeover), H10 (dispersal).

## Question

In every E001/E002 control run, replication stops within about 10,000 ticks
and the survivors are mutants whose `absorb` loop never exits. What kills the
replicators while those absorbers survive?

## Setup

- Control config (`Config::default()`), ancestor K = 64, E = 16, seeds 1–5,
  50,000 ticks, census every 100 ticks:
  `evo-core --ticks 50000 --seed N --census 100 --out runs/diag/control_sN`,
  then `uv run report.py ../runs/diag/control_sN --classify` from `analysis/`.
- E002 `far` arm re-run with recording, seeds 1–10, census every 500:
  `--alloc-far --out runs/diag/far_sN`, then `--classify`.
- Classes are the single-genome harness labels (3,000 ticks alone, noise
  off, from a fresh start): `replicator` (2+ exact children), `inexact`,
  `loafer` (no children, alive), `dies`.
- Birth kinds: `exact` (child bytes equal the executor's body at `divide`),
  `mutant` (differ), `stillborn` (endowment 0).
- Raw output in `runs/diag/` (gitignored); regenerate with the commands
  above at the instrumentation commit.

## Results

### 1. Replicator lineages end early

Last census with a replicator-class body alive: tick 2,600 / 5,100 / 5,300 /
9,400 / 2,100 for seeds 1–5.

### 2. How replicator-class organisms die

6,584 replicator-class deaths over the 5 seeds (of 13,905 deaths total).
Every one is an upkeep death (the only physical cause).

| signature | n | share | median age | median max energy held | median share of absorbs short | `alloc` failures |
|---|---|---|---|---|---|---|
| newborn (never divided) | 2,836 | 43% | 3 | 26.8 | ~0.53 per seed | 0 |
| mid_copy (died holding a half-built child) | 2,512 | 38% | 14 | 171.6 | 0.21–0.24 per seed | 0 |
| after_dividing | 1,110 | 17% | 17 | 235.1 | 0.125–0.16 per seed | 0 |
| stillborn (endowment 0) | 126 | 2% | 1 | 0 | – | 0 |

"Absorbs short" = absorbs that returned less than a full 8-unit ration
because the patch pool was short.

Reading: replicators starve in their own crowded patch. Space is never the
constraint (zero `alloc` failures in 6,584 deaths). A newborn starts with
16 units; at the 32-unit-per-tick execution cap that is half a tick of
running if its absorbs come back empty, and half of its absorbs do. Adults
die young too (median 14–17 ticks, about one reproduction cycle: the
ancestor's first child comes at tick 14 in the harness) and never hold much
(median peak 172–235 units against a store cap of 1,344).

Mechanism, from the config: one ancestor in its absorb loop draws up to 64
units per tick (8 absorbs at 8 units within the 32-unit cap, since each
4-instruction loop pass costs 4 and yields 8). Patch income is 256 per tick,
so about 4 organisms absorbing at full rate use up a patch. Children land
next to the parent (nearest-free `alloc`), the colony stays in 1–2 patches,
the pool drains, and everyone with a small buffer dies within a few ticks.

### 3. After the replicators: junk births

Across the 5 seeds, 28% of all births were `exact`, 44% `mutant`, and 28%
`stillborn`. E001/E002 birth counts therefore overstate replication.

Example, seed 1, organism 199: born at tick 327 with `skipnz C` in place of
`skipz C`, so its copy loop exits after one byte. It lived 22,520 ticks and
had 1,616 children. The first 415 (ticks 337–4,063) got a 16-unit
endowment; then its body changed from `lit A 16` to `lit A 0` (one bit),
and the next 1,201 (ticks 4,072–9,852) were stillborn.

### 4. Reproduction from debris

Organism 199 copies only one byte into each child; the other 20 bytes are
whatever the claimed region already held (`alloc` claims free or debris
bytes and does not clear them). Near the colony that region is mostly the
debris of dead ancestors. 225 of its 415 endowed children were working
replicators by the harness test, with zero copy errors recorded. Organism 200
did the same, with 179. This is a form of scavenging, one of the
outcomes PLAN.md §10 lists as realistic. Nobody designed it.

### 5. Survivors

All 23 organisms alive at tick 50,000 across seeds 1–5 have bodies that
changed since birth (ages 23,145–49,906 ticks). In the last census interval
22 of 23 spent exactly 25% of their instructions on `absorb` (a
4-instruction absorb loop that never exits) and the other 17%; none divided.
Three of them also ran `copy` 500 times per interval, inside the loop. All
but one are labeled `dies` or `loafer` by the harness: from a fresh start
their genomes do something else, so the class says what a genome does when
started fresh, not what a stuck organism is doing.

### 6. Correction to E002 (far arm)

E002's "still replicating" counted any birth in the last 5,000 ticks. With
the far arm re-run under recording, the two seeds that met it (6 and 8) had
their last `exact` birth at tick 9,839 and 31,875, and their last
replicator-class body at 9,000 and 11,500. Their late births were mutants.
Under an exact-copy criterion, 0 of 10 far seeds were still replicating at
tick 45,000 (control was 0 of 10 already). Far's other result stands: 0 of 10
extinct vs 2 of 10 for control.

## What this says about the physics

The binding problem is local: a patch can feed about 4 full-rate absorbers,
every child is born into its parent's patch with a buffer worth well under
one tick of running, and nothing moves a lineage elsewhere before the patch
crashes. Broken-exit absorbers win the crash because they never stop
absorbing and never spend on copies.

Options for the next design pass (not decided):

- Dispersal at birth beyond locality (E002 far helped survival but not
  persistence).
- Larger endowments or a minimum endowment (a physics change, or something
  evolution could find by mutating `lit A 16`; it has not in these runs).
- Density-dependent absorb yield, so stacking absorbers in one patch pays
  less per organism (H6's design response).
- Loafer turnover (E001 open item): the 23 survivors are 23,145–49,906
  ticks old; bit rot at 1e-5 changes their bodies but does not remove them.

## Caveats

- 5 control seeds. Per seed, newborn plus mid_copy is 78–86% of
  replicator-class deaths (newborn and mid_copy swap order in seeds 1 and
  5), and `alloc` failures are zero in all 5.
- Harness classes start every genome fresh with 100 units and full pools; a
  genome that replicates only from some running state is labeled otherwise
  (seed 2 has 44 exact births from `dies`-class parents).
- The death signature is assigned from counters at death; "starved" is
  inferred from short absorbs and low peak energy, not logged as a cause.
