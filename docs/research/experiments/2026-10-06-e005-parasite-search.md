# E005: parasite search in the E004 world (2026-10-06)

Status: question, definitions and predictions written 2026-10-06, before
any query of the p512_far run files beyond the E004 summary numbers. No new
runs: this reads the 40 p512_far runs recorded in E004
(`runs/e004/p512_far*/s1..10/`).

Bears on: PLAN.md Phase 2 success criterion (see the parasite lineage
appear), H4 (write protection and coexistence), H8 (`self` semantics).

## Question

The E004 world keeps replication going. Does it also produce parasites:
heritable lineages that replicate in the world but not alone, because they
use another living organism's code?

E004 left two leads: 0.2–0.8% of births per run copied their bytes from a
living organism other than the executor, and 10,000–14,600 organisms per
run executed another organism's code at some point.

## How a parasite could work in this ISA

The ancestor has no templates and no `search`; it finds itself with
`self` (start and length of the executing organism) and loops with
`jmpr`. Phase 1 `self` means the executing organism, not the owner of the
byte at IP. So an organism whose IP enters a neighbor's body at the
neighbor's first byte runs the neighbor's whole replication loop, and that
loop copies the executor, not the neighbor. Then the neighbor's last two
ops (`self ; jmpa A`) send the IP back to the executor's own start. Any
body that ends without a jump and sits right before a replicator can
reproduce this way: it falls off its own end into the host.

Far `alloc` makes that layout common. It scans from the locality edge
inward and takes the first free run that fits, so when an organism sits
near the edge the child's region is placed so that it ends at the byte
just before that organism's start.

Births copied from another living organism (source not the executor) are
a different thing: the executor's `B` points into a neighbor, so the
child gets the neighbor's bytes. If one genome were copied this way again
and again, that genome would be using other organisms' CPUs, the trick
Tierra's hyper-parasites used.

## Definitions

- **Exact birth**: child bytes equal the executor's body at `divide`
  (`raw_hash == parent_now_hash`), as in E003/E004.
- **World-replicating genome**: a raw hash with at least 2 exact births by
  carriers in the run (the harness's replicator threshold).
- **Dependent genome**: world-replicating, but its harness class (alone,
  default physics, `classes.csv`) is not `replicator`.
- **World-physics class**: the harness class with the E004 world's energy
  and `alloc` rule (`--patch 512 --sun 8 --alloc-far`, plus
  `--absorb-prop` for the prop arms), noise still off. Needs a classify
  option that honors the physics flags. A dependent genome that is a
  replicator under world physics depends on physics, not on neighbors.
- **Generation depth**: for genome G, the longest chain of exact G births
  in which each executor was itself born by an exact G birth.
- **Foreign-execution share**: `exec_foreign / executed` over a carrier's
  life (`deaths.csv`, plus `orgs.csv` at the last census for the living).
  `exec_unowned` (free or debris addresses) is reported separately: running
  dead code is scavenging, not parasitism.
- **Parasite lineage**: a dependent genome, still not a replicator under
  world physics, whose carriers have a median foreign-execution share
  above 0.25 and whose generation depth is at least 5.
- **Content-free parasite** (added 2026-10-07, before any query): a
  parasite genome whose exact births do not depend on its bytes. Under
  Phase 1 `self` the smallest body that can fall into a host is one
  byte, and any body works as long as no byte in it jumps away, divides,
  or re-points `A` and `B` before the IP reaches the host. Test: the
  two-genome harness (`--host`, below) places the genome immediately
  before an ancestor in a quiet world and counts its exact births; then
  the same with every byte replaced by `pad`. Equal counts within 10%
  means content-free. A content-free lineage is heritable by placement,
  not by code, and the record says which kind was found.

## Predictions

1. Dependent genomes produce at least 5% of exact births after tick
   10,000 in at least 5 of the 10 p512_far seeds. Reason: far `alloc`
   puts children right before other bodies, and 81% of the living at the
   end are not replicator class.
2. Of those exact births, at least 80% come from genomes that are still
   not replicators under world physics.
3. Carriers of dependent genomes have a median foreign-execution share
   above 0.25; replicator-class carriers below 0.01.
4. At least one parasite lineage (definition above) in at least 5 of 10
   p512_far seeds, and in at least 5 of 10 p512_far_prop_rot seeds (the
   standard world).
5. The main parasite genome in a seed is shorter than the main replicator
   in that seed (21 bytes at the start).
6. Births copied from another living organism: fewer than 10% are exact
   copies of the source's birth genome, and no source genome has 100 or
   more such exact copies in one run. These are register errors, not a
   lineage. Caveat added 2026-10-07: far `alloc` places a child with its
   tail against a neighbour's head whenever the neighbour sits at the
   locality edge, so a length mutation that makes `B` overrun the child's
   own body reads the neighbour. Some of these could be heritable; the
   other-source table decides.
7. (Added 2026-10-07, before any query.) The main parasite genome in at
   least 5 of the 10 p512_far seeds is 4 bytes or shorter, and the
   two-genome harness labels it content-free. Reason: the one-byte
   fall-through parasite needs nothing but a non-jumping body and a host
   behind it, and shorter bodies are cheaper to carry and copy. If instead
   the main parasites are content-dependent (their bytes do something the
   pad version does not, such as finding a host by `search`), that is the
   stronger result and the record says so.

If 1–4 hold, the Phase 2 criterion is met and the next step is a
phylogeny figure of the parasite's origin. If dependent genomes exist but
run debris or physics-specific code instead of neighbors' code, the record
says so and the criterion is not met. If the parasites found are all
content-free, the criterion is met in the letter (a lineage that
replicates only by another organism's code) but the record flags that it
is a placement lineage, and H8 (`self` = owner of the byte at IP, under
which the same layout copies the host) becomes the next experiment.

## Method

Runner: `analysis/e005_parasites.py`. Per run: birth source kinds (self,
other living, debris or free), exact births by harness class of the
executor's body, the dependent-genome table (length, class, world-physics
class, exact births, first and last tick, generation depth, foreign and
unowned execution shares), and the other-source birth table. Then read
the disassembly of the top dependent genome in a few seeds by hand to
confirm the mechanism, and run it through the two-genome harness
(`evo-core --host GENOME_HEX [--host-pad]`, added for this experiment:
the genome is seeded immediately before an ancestor at the world centre,
quiet physics as for `--classify`, children removed every tick, and the
genome's exact births counted over `--harness-ticks`).

World-physics classes: `classes_world.csv` was written for 33 of the 40
runs on 2026-10-06 and 6 of those were cut short (the classify processes
were killed at 14:43; p512_far_rot s7–s9 and p512_far_prop_rot s1–s3 have
63,013–108,886 of 122,101–145,659 rows). The runner checks the row count
against `genomes.csv` and redoes any short or missing file before
reading anything.

## Results (2026-10-07)

Run from commit 1e70b85 plus the runner (`analysis/e005_parasites.py`,
committed with this section). World-physics classes were completed for
all 40 runs first (13 files rewritten, 14–60 s each). Output:
`runs/e005/summary.md`, `runs/e005/runs.csv`, and per run
`runs/e005/<arm>_s<seed>_dependent.csv` (every dependent genome with its
classes, exact births by copy source, carrier execution shares,
generation depth and disassembly) and `_other_source.csv`. The host
harness (`--host`) was run on the main parasite of each run.

Seed 10 of both rot arms lost its founder by tick 1,179 (E004), so those
two runs have no births after tick 10,000 and are left out of the counts
below (n = 9 for the rot arms).

### Measurement change made during the run

The registered foreign-execution share (median over every carrier of a
genome) is near 0 for every genome, replicator or not, because most
carriers of any genome die as newborns inside their own body: E004 found
newborns at 30–60% of replicator deaths, and a 16-energy child in a
drained patch dies before it executes anything foreign. The seed 1 smoke
run (first run of the runner, before the other 39 were read) showed
this, and two post-hoc measures were added and are reported next to the
registered one: the median over carriers that divided at least once
("dividers") and the median over carriers with at least two children. The
second is the one used below, because a carrier that dies right after
its first `divide` has not yet reached whatever lies after its body. The
registered P4 count is reported as registered.

### Numbers

Medians across seeds unless marked as counts.

| arm | n | exact births after 10,000 | dependent genomes | dependent share of exact births | dependent, but replicator under world physics | dependent exact births copied from debris or free space | parasite genomes (2+ children test) | parasite share of exact births | main parasite length | seeds whose main parasite is 1–2 bytes |
|---|---|---|---|---|---|---|---|---|---|---|
| p512_far | 10 | 228,000 | 1,265 | 0.084 | 0 | 82 | 32 | 0.008 | 21 | 0 |
| p512_far_prop | 10 | 193,000 | 826 | 0.088 | 0 | 79 | 20 | 0.006 | 21 | 2 |
| p512_far_rot | 9 | 327,000 | 5,378 | 0.103 | 0 | 70 | 56 | 0.004 | 21 | 0 |
| p512_far_prop_rot | 9 | 262,000 | 4,296 | 0.111 | 0 | 84 | 50 | 0.007 | 2 | 5 |

Foreign-execution share, median over genomes of the per-genome median:

| carriers counted | dependent genomes | replicator-class genomes |
|---|---|---|
| all (registered) | 0.00 | 0.000 |
| dividers | 0.00–0.01 | 0.000 |
| 2+ children | see breakdown below | 0.000 |

Parasite lineages (dependent, not a replicator under world physics,
depth ≥ 5, foreign share > 0.25) per arm, seeds with at least one:

| arm | registered (all carriers) | dividers | 2+ children |
|---|---|---|---|
| p512_far | 3 of 10 | 10 of 10 | 10 of 10 |
| p512_far_prop | 5 of 10 | 10 of 10 | 10 of 10 |
| p512_far_rot | 8 of 9 | 9 of 9 | 9 of 9 |
| p512_far_prop_rot | 9 of 9 | 9 of 9 | 9 of 9 |

Where the dependent genomes' exact births (after tick 10,000) come from,
by the 2+-children foreign share of the genome (medians across seeds of
the within-run share):

| arm | foreign > 0.25 (parasite) | foreign < 0.05 | 0.05–0.25 | no carrier with 2 children |
|---|---|---|---|---|
| p512_far | 0.21 | 0.26 | 0.24 | 0.29 |
| p512_far_prop | 0.23 | 0.25 | 0.13 | 0.39 |
| p512_far_rot | 0.15 | 0.18 | 0.14 | 0.52 |
| p512_far_prop_rot | 0.19 | 0.16 | 0.11 | 0.53 |

Dependent genomes are 21 bytes long in 1,175 of 1,212 cases (seed 1);
their default harness class is `inexact` (495–2,946 per run) or `dies`
(327–2,363), rarely `loafer` (4–56).

Births whose copy source was another living organism (P6): 0.2–0.5% of
births; of those, 0.1–0.4% are exact copies of the source's birth genome,
and the largest count of such copies from one source genome in one run is
16.

### Predictions

1. Dependent genomes ≥ 5% of exact births after tick 10,000 in ≥ 5 of 10
   p512_far seeds: **confirmed**, 10 of 10 (6.3–9.4%), and in every
   surviving run of the other arms (7.8–12.1%).
2. ≥ 80% of those from genomes still not replicators under world physics:
   **confirmed**, 100% in every run. The world-physics classes differ
   from the default ones for only 39–83 genomes per run, none of them
   dependent. What the dependent genomes depend on is not the energy or
   `alloc` physics.
3. Dependent carriers' median foreign share > 0.25, replicators' < 0.01:
   **refuted as registered** (0.00 for both, see the measurement note).
   With the 2+-children measure, the replicator half holds (0.000), and
   dependents split: about a fifth of their exact births come from
   genomes above 0.25, a fifth to a quarter from genomes below 0.05.
4. A parasite lineage in ≥ 5 of 10 p512_far and ≥ 5 of 10 standard-world
   seeds: **registered measure: refuted for p512_far (3 of 10),
   confirmed for p512_far_prop_rot (9 of 9)**. With the 2+-children
   measure, every surviving run of every arm has 13–72 parasite
   lineages, depth up to 63 generations.
5. Main parasite shorter than the main replicator: **refuted**, 0, 2, 0
   and 5 of 10. In 30 of 38 runs the main parasite is a 21-byte
   ancestor variant.
6. Other-source births are not a lineage: **confirmed** (0.1–0.4% exact
   copies of the source, at most 16 from one source genome).
7. Main parasite ≤ 4 bytes in ≥ 5 of 10 p512_far seeds and content-free:
   **refuted** for p512_far (0 of 10) and p512_far_rot (0 of 9); 2 of 10
   in p512_far_prop and 5 of 9 in p512_far_prop_rot. The 1–2-byte
   parasites exist only in the proportional-absorb arms. The content-free
   test as registered (padded version within 10% of the genome's exact
   births before a host) is met in 38 of 38, but the comparison runs the
   wrong way: the padded body does better (214 vs 81–180 for the 21-byte
   parasites, 340 vs 190 for `self 0`), because pure fall-through spends
   nothing on its own loop.

### What this says

**Mechanism 1: fall-through parasitism, as predicted.** The main
parasite in 30 of 38 runs is the ancestor with its restart (`self 0 ;
jmpa A`) broken by a mutation in the last 2 bytes, so after `divide` its
IP runs off the end of its body into whatever follows. When that is a
replicator, the host's `self` returns the executor's start and length,
the host's copy loop copies the executor, and the host's own `self 0 ;
jmpa A` sends the IP home. One cycle then yields two children: one from
the parasite's own loop, one from the host's. Carriers with 2+ children
have foreign shares of 0.28–0.56 in the main parasites. Depth reaches
33–63 generations in 11 of 38 runs, so these are lineages, not
accidents. In the two-genome harness (`--host`) every main parasite
reproduces before an ancestor (60–180 exact births in 3,000 ticks,
against 214 for a padded body of the same length).

**Mechanism 2: dead-code trampolines, not predicted.** The largest
dependent genome in p512_far seed 1 (1,088 exact births, depth 12, 23
independent origins) is the ancestor with `self 0` before `jmpa A`
replaced by `pad`, so after `divide` it jumps to absolute address 17
(the endowment literal left in A). Its reproducing carriers ran no
foreign code at all, but exactly 4 unowned instructions per child and
then came home. Free memory keeps the bytes of dead bodies (matter is
conserved, decay only changes the owner), and the trace example
(`evo-core/examples/trace.rs`) confirms that `self 0 ; jmpa A` planted as
free bytes at 19–20 makes the genome a replicator with exactly 4 unowned
instructions per cycle. The actual bytes at 17–20 in that run cannot be
recovered, because there are no world snapshots (PLAN §7, not yet
built); the counters and the harness reproduction are the evidence.
Genomes with foreign share below 0.05 produce 16–26% of dependent exact
births, with unowned-execution medians of 0.07–0.18, so this class is
about as common as fall-through parasitism.

**Mechanism 3: one-shot replicators.** 29–53% of dependent exact births
come from genomes no carrier of which ever had two children: a working
copy loop followed by a tail that leaves the body for good. Each carrier
makes one child, so the lineage is at replacement rate 1 and fades;
these genomes have 2–4 exact births each. The harness labels them
`inexact` (one exact child is below its threshold of 2).

**Obligate 1–2-byte parasites exist, only under proportional absorb.**
`pad`, `self 0` and `pad ; pad` lineages with 256–1,286 exact births and
depth 5–11 are the main parasite in 7 of 19 proportional-absorb runs and
in none of the 19 fixed-absorb runs. Their carriers with 2+ children
spend 0.43–0.68 of their instructions in unowned memory (walking from
their byte to the next body) and 0.32–0.56 in a host. Why the absorb
rule matters is not tested here; one guess is that under proportional
absorb a host's loop in a drained patch earns less, so the extra child
the parasite gets from it costs the parasite less relative to a 21-byte
body's upkeep.

**Phase 2 criterion.** Met in the letter: heritable lineages that
replicate by executing another living organism's code appear in every
surviving run and persist for tens of generations. Not met in the
spirit of Tierra's parasite, which found its host by template search
and carried no copy loop. Nothing here uses `search`. Parasitism here
is a side effect of `self` naming the executor: under that rule any
replicator's code is a public good for whatever body sits before it, and
a 1-byte body is enough to use it. The parasites are also a small part
of the economy: 0.4–0.8% of exact births, against 8–12% for the
dependent class as a whole and 88–92% for self-sufficient replicators.

### Caveats

- The foreign-share measure was changed after the first run was read
  (see the note above). The registered measure is reported alongside.
- Carriers are matched to genomes by birth hash; a body that mutated in
  place after birth (bit rot) is counted under its birth genome.
- The host harness places the genome directly before the ancestor. In
  the world the body behind a parasite is whatever far `alloc` put there,
  usually not the ancestor.
- No world snapshots, so the dead code at a trampoline address is
  inferred, not read.
- "After tick 10,000" is the registered window; the dependent share is
  similar in the whole run.

### Decision

2026-10-07: the next experiment is H8, the `self` switch (E006). Under
`self` = owner of the byte at IP, the same fall-through layout makes the
host's loop copy the host, paid for by the intruder's energy, so every
mechanism above should reverse or vanish: fall-through parasites become
donors, 1-byte bodies become host-copying machines, and dead-code
trampolines keep working only if `self` on unowned bytes falls back to
the executor. The two-genome harness and the E005 runner apply unchanged.
World snapshots at census ticks are the instrumentation gap this
experiment found; they go in before any experiment whose result depends
on free-space contents.
