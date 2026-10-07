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
