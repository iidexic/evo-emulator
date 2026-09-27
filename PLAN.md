# evo — Open-Ended Digital Evolution

Working plan and design notes. This document is meant to be iterated on and to
grow into the design spec. Nothing in it is final.

## 1. Goal

Build a computational environment in which evolution can happen as freely as
possible. The emphasis is not on features but on the *physics*: a small set of
rules, each justified by a real-world analog, from which replication, selection,
death, ecology, and (hopefully) increasing complexity emerge without being
scripted.

Non-goals:

- Reproducing Earth's biology. Biology is a reference for what constraints
  matter, not a target to imitate.
- A fitness function. Nothing in the system should reward organisms for doing
  what we want. Survival and replication are the only "reward".
- Running real OS processes or real machine code as organisms. See §3.

## 2. Prior art

The system sits in a lineage of artificial-life work. The failures are the most
informative part.

| System | Year | Substrate | Key result | Where it stalled |
|---|---|---|---|---|
| Coreworld (Rasmussen) | 1990 | Core War with mutation | Programs degraded to noise | Instruction set not evolvable |
| Tierra (Ray) | 1991 | Custom 32-op VM, shared memory, "reaper" | Parasites, immunity, hyper-parasites, cheaters within hours | Equilibrium; everything shrank toward minimal parasites |
| Avida (Ofria, Adami) | 1994+ | Grid, one VM per cell, CPU time rewarded for logic tasks | Real published biology (Lenski 2003, Nature) | Complexity only grows along designer-rewarded axes |
| Amoeba (Pargellis) | 1996 | Random soup | Replicators emerge spontaneously | Small scale |
| BFF / "Computational Life" (Agüera y Arcas et al.) | 2024 | Brainfuck-like programs concatenated and run against each other | Self-replicators emerge from noise, no seed, no fitness function; debris essential | Open question |

Shared lesson: replication and mutation are easy. What is hard is
**open-endedness**: keeping the system generating novelty instead of settling
into equilibrium. No digital system has solved this. The design below is
organized around the best current guesses for what pushes against equilibrium:

1. Spatial structure (geography).
2. Non-stationary environment (slow drift, seasons).
3. Rich organism-to-organism interaction (most of any organism's environment
   is other organisms).
4. Costs that scale with body size, so size is a tradeoff rather than a
   one-way pressure.
5. Scale: as many instructions per second as the hardware allows.

## 3. Core design principles

**Evolvability of the encoding.** A random mutation to real x86 code produces a
crash almost every time; the fraction of viable mutational neighbors is near
zero. Evolution needs a genotype space where most small changes are
survivable. Therefore: a custom virtual machine with an instruction set
designed so that every byte decodes to a valid instruction, there are no
absolute addresses, and operands are implicit or relative. This is the single
most important design decision and the one place where "going deep" is worth
it.

**Existence must cost something.** Physics has the second law. Tierra had
nothing equivalent and needed an artificial reaper. Here, bits decay unless
maintained and every instruction costs energy. Metabolism, death, and
proofreading then have a reason to exist.

**Conservation.** Memory is matter. It is never created, only claimed or
released. Energy enters from outside at a fixed rate and is dissipated by
computation.

**Mutation is physics, not a god-parameter.** Noise lives in the substrate
(noisy writes, background bit flips), not in a global "mutate the child"
step. That way fidelity itself is under selection: organisms can evolve
proofreading, or can evolve to be sloppier if that pays.

**Emergent, not hand-coded, limits.** Nothing says "you cannot be large."
Instead every cost has a physical basis and the scaling laws fall out (§5.8).

**Determinism.** Every run is reproducible from a seed. Non-negotiable for
debugging and for replaying interesting events.

**Observability first.** Lineage tracking, snapshots, and visualization are
half the project. Physics changes cannot be evaluated without them.

## 4. What "real hardware limits" means here

The host machine is the true outer boundary:

- Host RAM bounds the world's size (the planet).
- Host instructions per second bound total energy flux (the sun).
- Cache/memory hierarchy is a real, physical cost of non-locality and can be
  mirrored inside the VM (far reads cost more).

Everything else is a designed physics running inside a VM. Using actual OS
processes and files would cost roughly six orders of magnitude in speed
(process spawn is milliseconds; a VM instruction is nanoseconds), destroy
observability, and endanger the host.

## 5. Physics (draft)

Each rule below should carry a one-line physical justification. If a rule has
no analog and no clear emergent purpose, it is suspect.

### 5.1 Substrate

- One flat byte array, addressed as a 2D torus (wraps in both directions).
  Phase 1 may use a 1D ring for simplicity.
- Every byte is simultaneously matter and potential code.
- Each byte has an owner (organism id, or free, or debris).
- World cells (coarse regions of the array) carry environmental parameters
  (§5.6).

Analog: matter is finite and occupies space.

### 5.2 Organisms

An organism is an execution context: instruction pointer, a few registers, an
energy store, and an owned region of the byte array (its body). Bodies are
contiguous in Phase 1; whether to allow non-contiguous bodies later is an
open question.

Organisms have no privileged access to their own body. Reading, writing, and
executing are all memory operations subject to the same locality rules,
whether the target is self, neighbor, debris, or free space.

### 5.3 Instruction set

Design constraints:

- Small (32 to 64 ops). Every byte value maps to a valid op (use modulo or a
  redundant encoding).
- No absolute addresses. Addressing is relative to the instruction pointer,
  or by template matching (search nearby for a complementary pattern), as in
  Tierra. Template matching is what let Tierra's organisms keep working after
  insertions and deletions.
- Locality: reads and writes are limited to a radius around the organism.
  Optionally, cost grows with distance (memory-hierarchy analog).
- Ops needed at minimum: move/arithmetic on registers, conditional skip,
  relative jump, template search, read byte, write byte, allocate (claim free
  bytes), divide (spawn child from a claimed region), absorb (take energy
  from the local cell), and some form of interaction with other organisms
  (§5.5).
- Every op has an energy cost. Costs are the main tuning surface and should
  be in a table, not scattered in code.

Evaluation criterion for the ISA: with a random soup and no seed, do
replicators emerge? If not, the encoding is probably not evolvable enough.
This is a Phase 4 experiment but the ISA should be designed with it in mind.

### 5.4 Energy

- Each world cell receives an energy income per tick (sunlight). Income varies
  in space and cycles in time (§5.6).
- Energy in a cell accumulates up to a cap and is otherwise lost.
- An organism gains energy only by executing an absorb op at its location.
  Absorb yields a small amount per execution: sunlight is dilute. Gathering it
  should take a large fraction of a producer's cycles.
- Every executed instruction costs energy from the organism's store.
- An organism with zero energy stops executing. It does not immediately die;
  its body persists, decaying (§5.7), and it can be scavenged.
- Energy is compute. There is no separate scheduler fairness; an organism runs
  as many instructions per tick as it can pay for, up to a per-tick cap.

Analog: sunlight is the only external input; all work dissipates energy.

### 5.5 Interaction and trophic structure

Question raised in discussion: on Earth, producers (plants) do the hard work
of converting dilute sunlight into concentrated biomass, and everything else
eats that. Should the sim reproduce this?

It should not be a goal, but it is a useful **diagnostic**: if trophic levels
do not emerge, the physics is missing a concentration gradient. The design
provides that gradient without hand-coding roles:

- Absorb is slow (dilute sunlight).
- An organism's energy store and body are concentrated resources.
- A drain op takes energy from a neighboring organism's store. It is lossy
  (some fraction dissipates), which gives the trophic pyramid its shape without
  fixing a ratio.
- A body can be read and copied (horizontal gene transfer), overwritten
  (attack), or claimed once its owner is dead (scavenging debris).
- Defense costs energy (e.g. a membrane flag that makes external writes or
  drains fail, paid for per tick, or checks that the organism performs
  itself).

With these in place, a producer is simply an organism that spends its cycles
absorbing, and a consumer is one that spends them draining. Whether the split
happens, and at what ratio, is an experimental result.

### 5.6 Environment heterogeneity

Per world cell:

- Energy income (spatial gradient + temporal cycle: day/night, seasons).
- Background bit-flip rate (radiation).
- Instruction cost multiplier (temperature/viscosity).
- Optionally, several resource types where different ops consume different
  types and regional abundance differs (crude chemistry). Deferred to Phase 3
  or later.

Slow drift: all per-cell parameters change slowly over long timescales
(continental drift analog). A non-stationary environment is the best known
tool against equilibrium.

Locality plus heterogeneity gives geography, and geography gives allopatric
speciation (populations separated by distance drift apart).

### 5.7 Entropy, noise, death

- Every tick, each byte flips with a small region-dependent probability.
- Every write has a small probability of writing the wrong value. This is the
  primary mutation mechanism during copying.
- Maintenance: since the body decays, an organism must spend cycles checking
  and repairing itself or accept accumulating damage. Bigger bodies cost more
  to maintain. Whether repair evolves is an experimental result.
- Death: an organism is dead when it has no energy and cannot regain it, or
  when it faults in an unrecoverable way (exact fault semantics TBD; the ISA
  should make most faults recoverable so death is mostly energetic).
- No reaper. Dead bodies remain as debris until claimed or decayed.

Analog: the second law. Copying is imperfect. Bodies rot.

### 5.8 Emergent size limits

The scaling laws that limit body size in biology (square-cube, diffusion,
metabolic scaling) have analogs that emerge from the rules above:

- Copy time is linear in genome length: bigger reproduces slower.
- Per-byte copy error: a genome of length L with per-byte error rate mu cannot
  preserve its information once L * mu exceeds roughly 1 (Eigen's error
  threshold). Larger genomes need better fidelity, which costs cycles.
- Maintenance cost is proportional to body size (§5.7).
- Exposure is proportional to perimeter: a larger body has more neighbors that
  can drain or overwrite it.

Together these give an optimal size that depends on the local environment.
Tierra's problem was the opposite of "too big": everything shrank. The
intended counter-pressures are interaction richness and environmental
complexity, which reward carrying more code.

## 6. Architecture

### 6.1 Rust core (`evo-core`)

- The VM, the world array, the tick loop, the PRNG, and snapshot/replay.
- Performance target: as many VM instructions per second as possible on one
  host core first; multi-core later by partitioning the torus.
- Zero dependencies where reasonable. Likely small crates: `rand_xoshiro` or
  similar for a fast seeded PRNG, `serde` for snapshots, `clap` for the CLI.
- Output: binary snapshots of the world plus an append-only event log
  (births, deaths, mutations, lineage) in a simple framed format.

### 6.2 Python analysis (`analysis/`)

- Reads snapshots and event logs.
- Phylogenetic tree, diversity metrics, genome length over time, energy flow
  between organisms, spatial maps colored by lineage.
- Managed with `uv`. numpy, polars or pandas, matplotlib to start.

### 6.3 Interface between them

Flat binary files on disk, versioned format. No live IPC in early phases. A
later live viewer could read a memory-mapped snapshot.

### 6.4 Repository layout (proposed)

```
evo/
  PLAN.md              this file
  docs/                design notes, ISA spec, experiment logs
  evo-core/            Rust crate: VM, world, CLI
  analysis/            Python: uv project
  runs/                run outputs (gitignored)
```

## 7. Instrumentation (build before more physics)

- Organism table: id, parent id, birth tick, death tick, genome hash, length,
  position.
- Genome store keyed by hash so identical genomes are stored once.
- Per-N-ticks summary: population, distinct genomes, mean/max length, total
  energy, energy by region.
- Full world snapshot on demand and at intervals; replay from seed + tick.
- First visualizer: image of the byte array colored by lineage, one frame per
  snapshot. Web or terminal viewer later.

## 8. Phases

**Phase 0 — Design (this doc).** ISA draft, op cost table, world model. Each
rule with its physical justification. Decide open questions in §9.

**Phase 1 — Minimal living system.** Rust VM, 1D ring world, energy, noisy
writes, hand-written ancestor. Success criterion: the ancestor replicates,
mutants appear, and parasites (organisms that use another's copy loop)
emerge. This is roughly a Tierra reimplementation with energy instead of a
reaper.

**Phase 2 — Instrumentation.** Everything in §7. Success criterion: we can
draw the phylogeny of a Phase 1 run and see the parasite lineage appear.

**Phase 3 — Richer physics.** 2D torus, per-cell parameters, bit rot,
seasons, slow drift, debris, drain/defense ops. Success criteria: spatial
differentiation of lineages; some form of producer/consumer split;
evidence for or against evolved repair.

**Phase 4 — Experiments.** Soup runs with no seed. Chemistry (multiple
resource types). Multi-day runs. Compare ISA variants for evolvability.

## 9. Open questions

- Register machine vs stack machine for the VM. Tierra and Avida are register
  machines; BFF is a two-tape Brainfuck. Register machine is the default
  guess.
- Contiguous bodies only, or allow fragmented bodies?
- Fault semantics: which faults are recoverable, which kill?
- Exact locality radius and whether cost grows with distance.
- Whether energy is per organism or per byte of body (the latter makes
  "where the energy is" spatial, which might matter for predation).
- Multi-core strategy: partition the torus into strips with halo exchange, or
  run independent worlds and migrate organisms between them (islands).
- Snapshot format: hand-rolled vs serde/bincode.

## 10. Expectations

Realistic at desktop scale: parasites, immunity, arms races, evolved
proofreading, scavenging, regionally specialized metabolic strategies, some
producer/consumer structure. Any of the latter four would exceed most prior
work.

Not realistic: multicellularity, nervous systems, anything requiring the
roughly 20+ orders of magnitude of scale separating a desktop from Earth.

## 11. Working notes

- Languages: Rust core, Python analysis. The author knows Zig, Go, and Python;
  Rust is new. Code should be written with that in mind: idiomatic but
  explained, with comparisons to Zig/Go where a Rust concept differs
  (ownership and borrowing, traits vs interfaces, enums with data, error
  handling with `Result`).
- Related prior work by the author: cellular automata in Go at
  `D:\coding\github\go-CA-experiments`.
- Toolchain present as of 2026-09-26: cargo 1.95, rustc 1.95, Python 3.13,
  uv 0.10.
