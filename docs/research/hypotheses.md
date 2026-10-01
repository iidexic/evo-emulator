# Hypotheses log

Numbered, dated predictions, written before the experiment that tests them.
Each entry names the observation that would confirm it and the one that
would refute it. Entries are never edited after the fact; a change of mind
is a new entry that cites the old one. Experiments that bear on an entry
are listed under it as they happen (see `experiments/`).

Status values: open, supported, refuted, mixed, superseded.

---

## H1. Register vs stack ISA (2026-09-27)

**Prediction.** On the same world, energy model, and mutation rate, a
register ISA gives longer and more mutationally robust genomes; a stack ISA
gives shorter genomes, a higher fraction of lethal single-byte mutations,
and more natural chaining of computation.

**Reasoning.** In a register machine each byte names its own operand, so a
point mutation changes one op and at most one register. In a stack machine
any mutation that changes stack depth shifts the operand of every later
instruction (high epistasis), which tightens the error threshold.

**Confirms.** Stack ISA shows a higher lethal-mutation fraction in the
single-genome harness and a lower error-threshold genome length, with
shorter mean genome at equilibrium.

**Refutes.** No difference in lethal fraction, or the stack ISA sustains
longer genomes.

**Caveat from the literature.** Agüera y Arcas et al. (2024) found the
details of each encoding mattered more than the register/stack split:
SUBLEQ never produced replicators, long-tape Forth needed a second
instruction set, and long-tape 8080 gave only non-looping replicators.
Minimal replicator length was the deciding factor. So H1 may be swamped by
encoding details; the experiment must hold minimal replicator length
roughly equal across the two ISAs.

**Status.** Open. Phase 4.

---

## H2. Producer/consumer split is diagnostic (2026-09-27)

**Prediction.** If the energy model is right, a persistent split appears
between organisms that spend most cycles on `absorb` (producers) and
organisms that get most energy by other means (parasites of copy loops,
later `drain`). If the split does not appear within the first long Phase 1
run, the energy ratios are wrong: either absorbing is too cheap relative to
copying, or parasitism pays nothing.

**Confirms.** Bimodal distribution of absorb-fraction per genome, stable
over many generations, with the low-absorb mode dependent on the
high-absorb mode (it disappears when the producers are removed).

**Refutes.** Unimodal absorb-fraction, or the low-absorb mode persists
alone.

**Prior evidence.** Cosmos (Taylor 1999) charged one energy token per
instruction, as here, and its first adaptation was stacking energy-collect
ops in the copy loop, followed by stasis. That is the failure mode to watch
for: everything becomes a producer and nothing else happens.

**Status.** Open. Phase 1 to 3.

---

## H3. Interior size optimum does not appear on its own (2026-09-30)

**Prediction.** Under the default Phase 1 settings (constant tick cap,
c1 = 0, small upkeep u) genome length shrinks toward the minimal replicator,
as in Tierra under a constant slice (22 to 30 instructions) and Cosmos. No
setting of c1 alone yields an interior optimum: c1 = 0 shrinks, c1 large
enough to matter bloats and collapses (Cosmos: doubling and collapse in 5
of 9 runs; Tierra: 400 to 800 under slice ∝ size, past 23,000 under
superlinear slice).

**Confirms.** A c1 sweep shows only shrink or bloat regimes with a narrow or
absent stable band.

**Refutes.** A band of c1 exists where mean genome length settles well above
the minimal replicator and stays there over many generations without
collapse.

**Why it matters.** PLAN.md §5.8 claims size limits emerge from the rules. The
literature has no example of that. If H3 holds, the counter-pressure has to
come from elsewhere: interaction richness or environmental complexity
(Phase 3), which is H9.

**Status.** Open. Phase 1 gives the c1 = 0 point; Phase 3 sweeps.

---

## H4. Write protection is necessary for coexistence (2026-09-30)

**Prediction.** With write protection off (any organism may overwrite any
byte within its locality radius), the seeded population collapses to a
single fast overwriter within a short time and no two genotypes coexist
for long. With protection on (living bodies writable only by their owner),
parasites and hosts coexist.

**Evidence.** Coreworld's seeded replicators broke within about 200
iterations without protection; Amoeba-IV never held two species; Tierra
had protection and got coexisting parasites and hosts; spatial Stringmol
got coexistence through spatial pattern rather than protection.

**Confirms.** Protection-off runs show one dominant genotype and a
distinct-genotype count near 1 after the initial transient; protection-on
runs sustain more than one lineage with dependency between them.

**Refutes.** Protection-off runs sustain multiple lineages, which would mean
locality radius or energy cost already does protection's job.

**Status.** Open. Phase 1 (protection on) vs Phase 4 control (off).

---

## H5. Upkeep plus decay is enough turnover (2026-09-30)

**Prediction.** With no reaper, no age limit, and no population cap, the
population does not fill with non-replicating absorbers. Per-byte upkeep
makes a pure absorber lose energy at the rate its body costs, so it dies
unless absorb income exceeds upkeep. The design must set absorb yield below
per-byte upkeep for a body above some small size, or the loafer is immortal.

**Evidence.** Avida kept an age limit because otherwise non-replicators
"persist since organisms have no means by which to be purged." Every
no-reaper system in the literature had another forced-turnover rule
(Nanopond random reseed, Cosmos cull at cap, Evoloops dissolution).

**Confirms.** The fraction of living organisms with zero lifetime offspring
and age above N generations stays small, and world memory does not fill
with them.

**Refutes.** Memory fills with old non-replicators and births stop.

**Status.** Open. Phase 1.

---

## H6. Absorb-loop takeover (2026-09-30)

**Prediction.** The first adaptation of the seeded ancestor is not better
copying but more `absorb` ops in the copy loop, as in Cosmos. If nothing
else changes, the population then stalls.

**Confirms.** Absorb-fraction per genome rises before replication time
falls; genotype turnover then drops.

**Refutes.** Copy-loop efficiency improves first, or absorb-fraction stays
flat.

**Design response if confirmed.** Make absorb yield depend on cell pool
state (dilute, depleting) so stacking absorbs has diminishing returns, which
is already the intent in §5.4; the experiment tests whether the ratio is
right.

**Status.** Open. Phase 1.

---

## H7. Seedless emergence fails without a start-execution rule (2026-09-30)

**Prediction.** In a random soup with no seed and no rule that starts CPUs
on random bytes, nothing happens: no organism exists to execute anything,
so no replicator can be found. With such a rule (Coreworld: random pointer
injection at p = 0.05 per update; Amoeba: 5% of CPUs on random code), and
with a minimal replicator around 10 bytes, replicators appear with a
per-run probability that depends mainly on minimal replicator length and
on the fraction of memory that is template characters.

**Confirms.** No emergence without the rule; emergence with it at a rate
that falls as minimal replicator length rises.

**Refutes.** Emergence without the rule (which would mean debris execution
or some other path starts CPUs), or no emergence with it over long runs.

**Status.** Open. Phase 4.

---

## H8. `self` semantics change the ecology (2026-09-30)

**Prediction.** With `self` meaning the executing organism, parasites that
jump into a host's copy loop get copies of themselves, and hosts cannot
turn the tables. With `self` meaning the owner of the byte at IP, a host's
copy loop run by a parasite's CPU copies the host, which is Tierra's
hyper-parasite mechanism. So the second semantics yields a longer
host/parasite arms race and more genotype turnover.

**Confirms.** Higher sustained genotype turnover and observed
executor-differs-from-source births under the owner-of-IP semantics.

**Refutes.** No difference, or the owner-of-IP semantics collapses because
parasites cannot reproduce at all.

**Status.** Open. Phase 3 or 4; cheap ISA switch.

---

## H9. Environmental drift delays equilibrium (2026-09-30)

**Prediction.** A slowly drifting heterogeneous environment sustains higher
genotype turnover and later plateau than a static heterogeneous one, which
in turn beats a homogeneous one.

**Evidence status.** None of the reviewed systems demonstrated this. Avida's
fluctuating-environment work (2018) concerns phenotypic plasticity under
imposed task switching, not open-endedness. Treat drift as untested.

**Confirms.** Ranked ordering drift > static > homogeneous on new-activity
and QNN over replicated seeds, holding energy input constant in total.

**Refutes.** No ordering, or drift lowers turnover because lineages cannot
track it.

**Status.** Open. Phase 3, with the three-way control built in from the
start.

---

## H5 note (2026-10-01)

E001 refutes the first form of H5: with absorb income far above upkeep,
upkeep alone does not purge non-replicators. Store cap and bit rot were
added. Whether upkeep plus store cap plus bit rot plus decay is enough
turnover is the revised question; E001 run 4 suggests not yet (loafers
outlive replicators through patch crashes). Status: mixed.

---

## H10. Dispersal across patches sustains replication (2026-10-01)

**Prediction.** When children can land in patches other than their
parent's, replication continues through 50,000 ticks in more runs than when
they cannot, because a crash in one patch no longer takes the whole colony
and loafers no longer inherit the only habitable patch.

**Reasoning.** E001: every child landed in the parent's 4,096-byte patch
(locality 512, nearest-free `alloc`), the colony overshot that patch's
income, and loafers survived the crashes that killed replicators.

**Confirms.** In E002, the best dispersal arm (smaller patches at constant
energy density, or farthest-free `alloc`) has at least 3 more of 10 seeds
still replicating at 50,000 ticks than the control, and more patches
occupied.

**Refutes.** No dispersal arm beats the control on runs still replicating,
or arms that spread wider replicate no longer.

**Status.** Open. E002.
