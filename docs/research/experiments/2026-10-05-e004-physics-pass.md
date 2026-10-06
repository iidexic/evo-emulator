# E004: physics pass, population room vs. absorb rule vs. bit rot (2026-10-05)

Status: design and predictions written 2026-10-05, before any E004 run
(including smoke tests); design revised after four smoke runs (section
below); run and recorded the same day.

Bears on: H5 (turnover), H6 (absorb-loop takeover, design response), H10
(dispersal), H11 (new, this file).

## Question

E003 found that replicators starve in their own crowded patch and that
broken-loop absorbers outlive them. Which physics change keeps replication
going: more room for the population, a different absorb rule, or faster
turnover of the absorbers?

## What E003's files show, read again for this design

Numbers from `runs/diag/control_s1..5` and `far_s1..10` (E003 runs).

- **The population is tiny and never leaves its first two patches.** The
  ancestor is seeded at byte 32,768, the boundary between patches 7 and 8.
  In all 5 control seeds no organism was ever counted in any other patch
  (patches ever occupied: 2 of 16). Median population over the run: 4–9;
  maximum 20–31. 14 of 16 patches sit full and unused for 50,000 ticks.
  Far `alloc` reached 2–5 patches in 9 of 10 seeds, and 11 in seed 8, the
  seed that kept exact births going longest (to tick 31,875).
- **Why the colony stays put.** `alloc` claims the nearest free run, and
  dead bodies are claimable debris, so children refill the gaps left by
  the dead. The colony's footprint is about its living bodies (≈ 15 × 21
  bytes), far smaller than a 4,096-byte patch. The pool is uniform within a
  patch, so nothing pushes outward.
- **Why it is so small.** An organism with energy runs its full slice of
  32 units per tick, plus 2.1 upkeep. A 256-per-tick patch therefore feeds
  about 7.5 organisms at full speed, whether or not they are absorbing
  anything. Two patches: about 15. That is what the census shows.
- **How scarcity lands.** Each organism runs its whole slice in turn, in a
  random order. In a drained patch the first four in the order take the
  256 income (64 each); the rest absorb nothing and burn 34. A newborn
  holds 16, so one unlucky tick kills it. E003: newborns died at a median
  age of 3 ticks, and about half of their absorbs came back short.
- **Late stillbirths are one or two organisms.** In seed 1, organism 199
  made 1,201 of the run's 1,211 stillborn births; in seed 2, organism 1451
  made 2,456 of 2,599. Both have a copy loop that exits after one or two
  bytes and an endowment of zero (`lit A 0` or `zero A` before `divide`).
  They spin absorb, claim 21 bytes, copy one or two, divide with nothing,
  repeat; each child dies on its first upkeep charge. Seeds 3–5 have no
  late stillbirths at all.

## Changes under test

Each is a switch; the defaults stay as they were so E001–E003 still
reproduce.

1. **Room: 128 patches of 512 bytes, each a copy of a control patch**
   (`--patch 512 --sun 8`: income 256 and cap 4,096 per patch). Eight times
   the sunlight per byte, delivered in patches no larger than the locality
   radius, so a child can land in the next patch in one generation. Analog
   and reason: PLAN §4 ties the sun's total power to the host's instruction
   budget, and the control world uses a tiny fraction of it (about 10
   organisms × 32 instructions per tick). Potential population: about 960.
2. **Room without spread: 16 patches of 4,096, income and cap × 8**
   (`--sun 8`). Same total sunlight as change 1 in the control's patch
   layout. Run only with the other two switches off. Separates "more
   energy" from "more patches to spread into".
3. **Proportional absorb** (`--absorb-prop`). The ration is
   `absorb_rate × pool / patch_cap` instead of `min(pool, absorb_rate)`.
   Analog: uptake of a dilute resource is proportional to its
   concentration (first-order kinetics); a leaf in half light gets half
   the energy. Under the current rule the last 8 units of a pool are as
   easy to collect as the first. Expected effect: scarcity is felt by
   everyone in a patch as the pool falls, instead of as a lottery once it
   is empty (H6's design response). Side effect, from the arithmetic: the
   K = 64 ancestor's 64 absorbs then pay for a copy only when the pool is
   above about 89% full, so a patch holds about 4–5 replicators instead of
   7.5.
4. **Bit rot × 10** (`--rot 1e-4`, from 1e-5). No new rule. PLAN §5.7 says
   sweep rates in log steps. At 1e-5 a 4-byte absorb loop takes a flip
   about once per 25,000 ticks, which matches the E003 survivors' ages
   (23,145–49,906). At 1e-4 that becomes about 2,500 ticks. Replicators
   take the same damage (21 bytes × 1e-4 = 0.002 flips per tick, about
   0.03 per 14-tick cycle, against a copy load of 0.1).

## Arms (first design; revised below)

2 × 2 × 2 factorial on room (control layout / 512-byte patches), absorb
rule (fixed / proportional) and bit rot (1e-5 / 1e-4), plus `sun8`.

| arm | patches | sun per byte | absorb | bit rot |
|---|---|---|---|---|
| control | 16 × 4,096 | 1× | fixed | 1e-5 |
| rot | 16 × 4,096 | 1× | fixed | 1e-4 |
| prop | 16 × 4,096 | 1× | proportional | 1e-5 |
| prop_rot | 16 × 4,096 | 1× | proportional | 1e-4 |
| p512 | 128 × 512 | 8× | fixed | 1e-5 |
| p512_rot | 128 × 512 | 8× | fixed | 1e-4 |
| p512_prop | 128 × 512 | 8× | proportional | 1e-5 |
| p512_prop_rot | 128 × 512 | 8× | proportional | 1e-4 |
| sun8 | 16 × 4,096 | 8× | fixed | 1e-5 |

Ancestor K = 64, E = 16, seeds 1–10, 50,000 ticks, census every 500, every
run recorded with `--out` and classified with the default harness (fixed
absorb, full pools, so the class is the same yardstick in every arm).
Runner: `analysis/e004_physics.py`. Output: `runs/e004/<arm>/s<seed>/`.

## Measures

Primary, per run: **replicating at the end** = at least one exact birth in
ticks 45,001–50,000 whose parent's body at `divide` is replicator class.
This is stricter than E002's "any birth" and avoids counting junk births
(E003 §6).

Secondary: extinct; replicator-class bodies alive at the final census;
last census with one alive; population and patches occupied at the end;
median age of the living at the end; class shares of the living at the
end; birth kinds (exact / mutant / stillborn); the newborn share of
replicator-class deaths.

## Predictions

1. control: 0 or 1 of 10 replicating at the end (E002 control 0 of 10 by a
   looser test; E003 0 of 5).
2. Room is the largest single effect: p512 has at least 5 of 10
   replicating at the end, a median end population of at least 100, and at
   least 32 of 128 patches occupied at the end.
3. sun8 has more organisms than control but stays in 2–3 patches, and at
   most 3 of 10 replicating at the end. More energy without room to
   spread helps less than the same energy spread out.
4. prop cuts the newborn share of replicator-class deaths from about 43%
   (E003) to under 25%, and lowers the population per occupied patch. On
   its own, in the control layout, at most 3 of 10 replicating at the end.
5. rot brings the median age of the living at the end below 5,000 ticks
   (E003: survivors 23,145–49,906) and lowers the share of loafer and dies
   class among them. On its own, in the control layout, at most 2 of 10
   replicating at the end: the colony is still stuck in two patches.
6. p512_prop_rot: at least 8 of 10 replicating at the end.

Plan by outcome: if room alone does it, small patches with more sun become
the default and the other two switches are adopted only if they add a
measured benefit (fewer newborn deaths, younger survivors) without
costing replication. If nothing reaches 5 of 10, the next candidates are
the ones E003 listed and this design left out: a minimum endowment and
dispersal beyond the locality radius.

## Design revision after smoke tests (2026-10-05)

Before the main runs, four 5,000-tick smoke runs at seed 101 (not in the
result set) checked the code and the file sizes. Two of them changed the
design:

- **p512 did not spread.** 14–19 organisms in patches 62–63 for the whole
  run, the same as control. Births landed 21–378 bytes from the parent,
  inside a 700-byte cluster. Reason: a 512-byte patch at 8× sun feeds about
  7.5 full-speed organisms, and 7.5 bodies of 21 bytes take about 160
  bytes, so the colony is still energy-limited long before it is short of
  space, and nearest-free `alloc` keeps refilling debris inside the
  cluster. Patch size does not change that; only the sun per byte against
  the burn per body byte does (a colony is pushed outward only above about
  12× control sun). Prediction 2 is expected to fail; it is left as
  written.
- **p512 with far `alloc` spread at once.** 128 of 128 patches occupied by
  tick 1,500, about 970 organisms and 550 genotypes from then to tick
  5,000. With patches no larger than the ~490-byte jump, every generation
  can found a new patch, and each new patch can feed its founder (unlike
  E002's far_p1024 at 1× sun, which died).

So the world factor gains far `alloc` as a second axis. Arms are now 4
worlds (control layout or 512-byte patches at 8× sun, each with nearest or
far `alloc`) × absorb rule × bit rot, plus sun8: 17 arms, seeds 1–10.

| world | patches | sun per byte | `alloc` |
|---|---|---|---|
| (control) | 16 × 4,096 | 1× | nearest |
| far | 16 × 4,096 | 1× | far |
| p512 | 128 × 512 | 8× | nearest |
| p512_far | 128 × 512 | 8× | far |

Each world runs plain and with `_prop`, `_rot` and `_prop_rot` (for the
control world the plain arm is `control` and the others are `prop`, `rot`,
`prop_rot`, as above). sun8 as before.

Added predictions (written after the smoke runs above, before the main
runs):

7. p512_far: at least 8 of 10 replicating at the end. The smoke run already
   showed it spreading; what is predicted is that the spread population
   keeps replicating to 50,000 ticks.
8. far (control layout): at most 2 of 10 replicating at the end (E003's
   re-run of E002 far: 0 of 10 by the exact-copy test at tick 45,000).
9. Inside p512_far, prop and rot do not change replicating-at-the-end by
   more than 2 seeds either way, and show their mechanism effects from
   predictions 4 and 5 (newborn share of replicator deaths down with prop,
   median age of the living down with rot).

## Results (2026-10-05)

Run from the working tree on top of 1cc5d21 with the three switches added
(uncommitted at run time, so `meta.json` shows 1cc5d21 with `git_dirty`
true). The defaults are unchanged: stdout for seeds 1–3, 20,000 ticks, is
byte-identical to the 1cc5d21 binary. 180 runs, 7.2 GB in `runs/e004/`.
`sun8_far` (8× sun and far `alloc` in the control patch layout) was added
after the other 170 runs had been read, to separate patch size from sun
plus dispersal; it is post hoc.

Counts out of 10 seeds; other columns are medians across seeds.

| arm | replicating at end | extinct | last replicator census | population at end | patches occupied at end | median age at end | non-replicator share at end | births | exact share | stillborn share | newborn share of replicator deaths |
|---|---|---|---|---|---|---|---|---|---|---|---|
| control | 0/10 | 2/10 | 2,750 | 4 | 2 of 16 | 48,662 | 1.00 | 1,625 | 0.50 | 0.02 | 0.39 |
| prop | 0/10 | 0/10 | 4,250 | 4 | 2 of 16 | 48,780 | 1.00 | 1,696 | 0.32 | 0.00 | 0.07 |
| rot | 0/10 | 10/10 | 1,500 | 0 | 0 of 16 | – | – | 749 | 0.64 | 0.02 | 0.33 |
| prop_rot | 0/10 | 10/10 | 1,000 | 0 | 0 of 16 | – | – | 452 | 0.55 | 0.03 | 0.05 |
| far | 0/10 | 0/10 | 4,250 | 6 | 2 of 16 | 48,944 | 1.00 | 3,798 | 0.23 | 0.00 | 0.41 |
| far_prop | 0/10 | 1/10 | 2,250 | 3 | 2 of 16 | 49,050 | 1.00 | 826 | 0.39 | 0.00 | 0.06 |
| far_rot | 0/10 | 10/10 | 1,000 | 0 | 0 of 16 | – | – | 816 | 0.47 | 0.01 | 0.29 |
| far_prop_rot | 0/10 | 10/10 | 750 | 0 | 0 of 16 | – | – | 457 | 0.43 | 0.04 | 0.07 |
| p512 | 0/10 | 1/10 | 3,750 | 4 | 2 of 128 | 49,383 | 1.00 | 2,452 | 0.46 | 0.01 | 0.40 |
| p512_prop | 0/10 | 0/10 | 4,250 | 4 | 2 of 128 | 48,780 | 1.00 | 1,696 | 0.32 | 0.00 | 0.07 |
| p512_rot | 0/10 | 10/10 | 1,500 | 0 | 0 of 128 | – | – | 1,321 | 0.54 | 0.04 | 0.35 |
| p512_prop_rot | 0/10 | 10/10 | 1,000 | 0 | 0 of 128 | – | – | 452 | 0.55 | 0.03 | 0.05 |
| p512_far | 10/10 | 0/10 | 50,000 | 964 | 128 of 128 | 10,736 | 0.81 | 551,136 | 0.57 | 0.03 | 0.60 |
| p512_far_prop | 10/10 | 0/10 | 50,000 | 926 | 128 of 128 | 13,394 | 0.83 | 443,594 | 0.58 | 0.04 | 0.30 |
| p512_far_rot | 9/10 | 1/10 | 50,000 | 970 | 128 of 128 | 1,176 | 0.74 | 682,907 | 0.60 | 0.03 | 0.54 |
| p512_far_prop_rot | 9/10 | 1/10 | 50,000 | 939 | 128 of 128 | 1,188 | 0.73 | 548,251 | 0.60 | 0.03 | 0.23 |
| sun8 | 0/10 | 0/10 | 20,000 | 63 | 2 of 16 | 45,878 | 1.00 | 21,128 | 0.40 | 0.10 | 0.49 |
| sun8_far | 2/10 | 0/10 | 30,750 | 558 | 16 of 16 | 42,960 | 1.00 | 166,778 | 0.34 | 0.06 | 0.48 |

### Predictions

1. control 0 or 1 of 10: **confirmed**, 0 of 10.
2. p512 alone the largest effect: **refuted**, 0 of 10, 4 organisms in 2
   of 128 patches at the end (the smoke run had flagged this).
3. sun8 more organisms than control, 2–3 patches, at most 3 of 10:
   **confirmed**, 63 organisms in 2 patches, 0 of 10. The last replicator
   census moved from tick 2,750 to 20,000: eight times the energy delays
   the end, it does not prevent it.
4. prop cuts the newborn share of replicator deaths below 25% and lowers
   population per patch; at most 3 of 10 alone: **confirmed**. Newborn
   share 0.39 to 0.07 in the control layout, 0.60 to 0.30 in p512_far;
   p512_far population at the end 964 to 926; 0 of 10 in the control
   layout.
5. rot brings the median age of the living below 5,000 and lowers the
   non-replicator share; at most 2 of 10 alone: **mixed**. In p512_far the
   median age at the end fell from 10,736 to 1,176 and the non-replicator
   share from 0.81 to 0.74. In every world where the colony stays small,
   rot made every run go extinct (60 of 60 runs across rot, prop_rot,
   far_rot, far_prop_rot, p512_rot and p512_prop_rot), which was not
   predicted. By the time rot matters there, only loafers are left, and
   rot removes them with nothing to replace them.
6. p512_prop_rot at least 8 of 10: **refuted**, 10 of 10 extinct.
7. p512_far at least 8 of 10: **confirmed**, 10 of 10.
8. far at most 2 of 10: **confirmed**, 0 of 10.
9. Inside p512_far, prop and rot move replicating-at-the-end by at most 2
   seeds and show their mechanism effects: **confirmed**. 10, 10, 9 and 9
   of 10; the two losses are the same seed (10), whose single founder
   lineage died by tick 1,179 under rot in both rot arms (with full pools,
   the two absorb rules give identical runs until a pool first drops).

### What this says

- **Dispersal into patches that can each feed a founder is what works.**
  The four p512_far arms kept replicating to tick 50,000 in 38 of 40 runs,
  with 926–970 organisms (median per arm) spread over all 128 patches
  from about tick 1,500 on. The other 130 runs in the main design: 0
  replicating.
- **Patch size matters, not just sun plus dispersal** (post hoc
  `sun8_far`). Same total sunlight and the same far `alloc`, but 16
  patches of 4,096: the colony reached all 16 patches and about 560
  organisms, yet only 2 of 10 were replicating at the end, and the living
  were all non-replicators at the median seed (median age 42,960). Many
  small patches behave like many small, separate populations: a crash or
  a loafer takeover stays in one patch, and neighbors recolonize it.
  Ecology calls this a metapopulation. Sixteen large patches are too few
  for that to work.
- **Room alone, or patch size alone, does nothing.** p512 without far
  `alloc` stayed in 2 patches, like control. In the prop arms the colony
  never left bytes 32,768–32,852, so prop and p512_prop wrote
  byte-identical files (checked).
- **The spread population settles.** In p512_far, replicator-class bodies
  fall from a median of about 400 at tick 1,000 to about 170 by tick
  10,000 and then stay flat to 50,000. Loafers are about 360–460 and
  `dies`-class bodies (stuck in a state a fresh start would not reach)
  rise from about 210 to 325. With rot: replicators about 250, loafers
  about 260, `dies` about 360.

  | median class counts, p512_far | tick 1,000 | 10,000 | 30,000 | 50,000 |
  |---|---|---|---|---|
  | replicator | 400 | 171 | 178 | 178 |
  | loafer | 138 | 462 | 408 | 363 |
  | dies | 90 | 211 | 288 | 326 |
  | replicator, with rot | 317 | 249 | 267 | 249 |
  | loafer, with rot | 174 | 270 | 272 | 266 |

- **Bit rot × 10** does in a big population what H5 asked for (younger
  population, about 50% more replicators at the end) and is fatal to a
  small one. Its one cost in p512_far is the founder phase: a single
  21-byte founder takes a flip about every 480 ticks.
- **Proportional absorb** halves newborn starvation and costs about 20% of
  births (551,136 to 443,594 median), with no change in persistence or in
  the class mix.
- **Not analysed yet: possible parasitism.** In each p512_far run, 1,212
  to 4,687 births (0.2–0.8%) copied their bytes from a living organism
  other than the executor, still happening after tick 40,000 in every
  seed; 10,000–14,600 organisms per run executed another organism's code
  at some point; lengths from 1 to 336 bytes appear. Whether any of this
  is a heritable parasite lineage is the Phase 2 success question and
  needs its own look.

### Decision

2026-10-05, Derek: record the winning world; code defaults stay as they
are for now. The **E004 world** is the standard world for the next
experiments. Run it with:

```
evo-core --patch 512 --sun 8 --alloc-far --absorb-prop --rot 1e-4
```

That is arm p512_far_prop_rot (9 of 10 replicating at tick 50,000; the
tenth lost its single founder by tick 1,179). Without the last two
switches it is p512_far (10 of 10). Making it the code default is still
open; doing so means reworking tests that assume nearest-free `alloc`,
the harness yardstick, and flags to reproduce E001–E003.

Recommendation at the time of writing: make the p512_far world the default (128
patches of 512 bytes, income 256 and cap 4,096 each, far `alloc`), with
proportional absorb (less newborn starvation, no cost to persistence, the
more physical rule) and bit rot 1e-4 (turnover; younger population, more
replicators). The founder-phase risk under rot can be handled by seeding
more than one founder. Far `alloc` is a crude stand-in for dispersal (the
child always lands at the edge of reach); making dispersal distance
evolvable is a candidate for the next design pass.

## Caveats

- One founder per run, always at byte 32,768.
- Far `alloc` is deterministic: always the farthest fitting run, about 490
  bytes from the IP.
- The p512_far arms change three things together relative to control
  (patch size, sun per byte, `alloc` rule). p512, sun8, far and sun8_far
  each remove one or two of them and all fail, so all three matter here,
  but the levels tested are single points (512, 8×, farthest).
- Classes are the single-genome harness labels at default physics (fixed
  absorb, 4,096-byte patches, full pools), the same yardstick in every arm.
- "Replicating at the end" needs one exact birth by a replicator-class
  parent in the last 5,000 ticks. In p512_far it is never close: each run
  has 23,998–28,191 such births.
