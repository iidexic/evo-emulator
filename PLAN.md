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
| Coreworld (Rasmussen) | 1990 | Core War with noise, per-address compute resource, 1D | Cooperative structures dominated the core for 100,000+ iterations, seven epochs. "Degraded to noise" is a misreading; only hand-seeded replicators broke, within ~200 iterations, for lack of write protection | Stable structures, but no organisms in the Tierra sense |
| Tierra (Ray) | 1991 | Custom 32-op VM, shared memory, write protection, reaper | Parasites, immunity, hyper-parasites, cheaters within hours | Stasis. Size trend was a scheduler setting: constant CPU slice shrank genomes to 22–30, slice ∝ size grew them to 400–800, slice ∝ size^>1 past 23,000. Standish 2003: genomes grew 80 to 526 with no complexity gain |
| Avida (Ofria, Adami) | 1994+ | Grid, one VM per cell, CPU share ∝ genome length (size-neutral by design), tasks add merit | Real published biology (Lenski 2003, Nature); parasites, coevolution (Zaman 2014) | With no rewarded tasks, complexity rose then fell and plateaued (MODES, Dolson 2019). Kept an age limit because non-replicators otherwise "persist since organisms have no means by which to be purged" |
| Amoeba (Pargellis) | 1996 | Random soup, 5% of CPUs given to random code each generation | Replicators emerge spontaneously; emergence fell once NOPs passed 25% of memory | No write protection; never saw two species coexist |
| Cosmos (Taylor) | 1999 | Spatial, one energy token per instruction, energy death, no reaper (cull at cap) | Closest precedent to this design | Stasis after the copy loop filled with energy-collect ops. CPU ∝ length: genome doubling and collapse in 5 of 9 runs. Energy theft from neighbours froze evolution |
| Stringmol (York) | 2010+ | Artificial chemistry, molecules bind by soft matching and execute each other, energy per opcode, stochastic decay | Spatial runs: parasites contained by spatial pattern, 8 of 20 runs survived 2M steps; evolved defences (self-scan, trapping foreign executors) | Universal-constructor variant: all 500 runs died of "bureaucratic death", none of parasites. Decay rule shaped everything: only constant decay in every state kept species turning over |
| BFF / "Computational Life" (Agüera y Arcas et al.) | 2024 | Brainfuck-like programs concatenated and run against each other | Self-replicators emerge from noise, no seed, no fitness function, even at zero mutation rate; SUBLEQ never did | Open question; no energy, no ownership, pairing imposed by the environment |

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
- Patches (coarse regions of the array) carry environmental parameters
  (§5.6). "Patch" rather than "cell" to avoid the biological sense.

Analog: matter is finite and occupies space.

Evidence status: Stringmol's "conservation of matter increases evolutionary
activity" (Hickinbotham & Stepney 2015) has no unconserved control, so it
does not test this premise. Conservation here is a physics choice, not a
result borrowed from the literature.

### 5.2 Organisms

An organism is an execution context: instruction pointer, a few registers, an
energy store, and an owned region of the byte array (its body). Bodies are
contiguous in Phase 1; whether to allow non-contiguous bodies later is an
open question.

Organism state lives in the emulator's organism table, not in world memory:
registers `A`–`D` and `IP` (32-bit, wrapping arithmetic; an address is the
value mod world size), the fail flag, the energy store, body start and
length, and at most one pending region claimed by `alloc` but not yet
divided. Registers are not subject to bit rot, cost no upkeep, and cannot
be read by other organisms.

At birth: `A`–`D` = 0, `IP` = body start, fail flag clear, energy = the
endowment passed by `divide`. The child first runs on the tick after its
birth.

Locality is measured from `IP`, not from the body: every op acts at the
place it is executed. One reference point for all ops; a parasite running a
host's code acts near the host; an IP that walks away from its body pays
energy per byte walked, so travel is a physical cost.

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
- Every op has an energy cost. Costs are the main tuning surface and should
  be in a table, not scattered in code.
- All ops are total: no traps, no faults that kill. Addresses wrap on the
  torus. An op whose target is protected or outside the locality radius does
  nothing to memory, sets the fail flag, and still costs its base energy
  (`load` then gives r = 0; `copy` still advances A and B so loops keep
  stepping). The only death is energy exhaustion plus decay (§5.7). A trap
  that kills is a reaper in disguise.
- The fail flag is set by a failed `search`, a failed `alloc`, `divide`
  with no pending region, and any blocked or out-of-range `load`, `store`,
  or `copy`. It is sticky until read: `self` modifier 2 copies it into A and
  clears it. Without a reader an organism could not tell that a write was
  blocked except by reading the byte back.
- Write protection is a physics switch, default on: bytes owned by a living
  organism cannot be written by another organism; free and debris bytes can.
  Reads and execution are never restricted. Every system that lacked
  protection collapsed (Coreworld's seeded replicators within ~200
  iterations, Amoeba-IV never held two species); Tierra had it and got
  coexisting parasites. Phase 3 `guard`/`drain` then evolve the boundary
  rather than create it. A no-protection run is a Phase 4 control.

Evaluation criterion for the ISA: with a random soup and no seed, do
replicators emerge? If not, the encoding is probably not evolvable enough.
This is a Phase 4 experiment but the ISA should be designed with it in mind.

#### 5.3.1 Register vs stack machine

Decision: register machine for Phase 1, with the decode/execute step
isolated behind a trait so a stack ISA can be swapped in as a Phase 4
experiment on the same world, energy model, and instrumentation.

Reasoning. In a register machine each instruction byte names its operand, so
a point mutation changes one op and at most one register; effects are local.
In a stack machine operands are implicit (top of stack), so genomes are
denser, but any mutation that changes stack depth shifts the operand of every
later instruction. That is high epistasis and lower mutational robustness,
which tightens the Eigen error threshold. Agüera y Arcas et al. (2024) saw
replicators emerge from soup under both styles (BFF tape machine, Forth
stack, Z80 and 8080 register), but not equally: SUBLEQ never produced one,
the first Forth variant failed on long tapes and needed a second instruction
set, and 8080 gave only non-looping replicators on long tapes. The authors
name minimal replicator length as the deciding factor. So neither style is
fatal, but the details of each encoding matter more than the register/stack
split; which evolves richer structure afterwards is an open question worth
testing.

Prediction (to record in the hypotheses log): register ISA gives longer and
more robust genomes; stack ISA gives shorter genomes, more frequent
catastrophic mutations, and more natural chaining of computation.

#### 5.3.2 Encoding

One byte per instruction. Low 5 bits select the opcode (32 slots). High 3
bits are a modifier whose meaning depends on the opcode: register select for
register ops, direction or variant for others. Every byte decodes.

Registers: `A`, `B`, `C`, `D` (general purpose, machine word), plus `IP`
(instruction pointer) and a small flag set (last search/alloc failed). With 4
registers and a 3-bit field, each register has two encodings; the redundant
encodings are neutral mutations. Unassigned opcodes decode as `pad`: does
nothing and is not a template character. Decoding them as `nop0` would make
11 of 32 opcode slots template letters, so random and decayed bytes would
spell templates everywhere; Amoeba's emergence rate fell once nops passed
25% of memory. `pad` keeps unused slots as neutral drift space without that.

Opcode numbers are assigned so that one-bit flips are mild where possible:
`inc`/`dec`, `shl`/`shr`, `skipz`/`skipnz`, `searchf`/`searchb`,
`nop0`/`nop1` one bit apart; `divide`, `alloc`, `copy` at Hamming distance
2 or more from `nop0`, `nop1`, `pad`, so filler does not drift into ops
that do something drastic. Stringmol arranges its mutation cycle the same
way.

Registers hold world offsets when used as addresses. Genome bytes never
contain an address; address values arise only at runtime from `search`,
`self`, or arithmetic. This invariant is what makes a copied genome work at
its new location.

Alternative considered: Avida-style nop modifiers (ops take no operand, the
following nop selects the register, so nops double as labels and modifiers).
Elegant but more indirect. Fixed field chosen for simplicity; revisit if the
ISA proves hard to evolve.

#### 5.3.3 Phase 1 op set (25 ops)

Templates and neutral filler:

| op | effect |
|---|---|
| `nop0`, `nop1` | Do nothing. A run of nops directly after a search op is a template. Also the neutral filler. |
| `pad` | Do nothing, ends a template. All unassigned opcode slots decode to this. |

Data:

| op | effect |
|---|---|
| `zero r` | r = 0 |
| `inc r`, `dec r` | r += 1, r -= 1 |
| `shl r`, `shr r` | shift left / right by one bit |
| `add r`, `sub r` | A += r, A -= r |
| `lit r` | r = next byte, sign-extended (the byte is a signed value -128..127); skip that byte. Cheap constants. The skipped byte is still a valid op if jumped into. |
| `swap r` | Exchange A and r. The only register-to-register move. Without it nothing can get an address out of A into B, and `copy` is unreachable even for a hand-written ancestor (found 2026-09-30 while checking the op set against a copy loop). Avida has the same op. |

Control:

| op | effect |
|---|---|
| `skipz r`, `skipnz r` | Skip the next instruction if r == 0 / r != 0. A whole instruction: 2 bytes when the next op is `lit`, else 1. |
| `jmpr r` | IP = (address of the byte after this op) + r, r signed. For loops with a constant offset. |
| `jmpa r` | IP = r. Absolute jump to a computed address. `self ; jmpa A` restarts a body from anywhere without a length-coupled constant, and `searchf ... ; jmpa D` jumps straight to a search result. Added 2026-09-30 when the ancestor turned out to run off its own end. |
| `searchf`, `searchb` | Read the template (run of nops) immediately following this op, skip past it, scan forward / backward within the locality radius for the complementary pattern (`nop0` matches `nop1`). On success D = address just past the match, C = template length. On failure, or if the template is empty, D = 0 and the fail flag is set. Cost grows with distance scanned. Byte 0x00 decodes as `pad`, so zeroed memory is never a template. |
| `self` | Modifier 0: A = own body start, B = own body length. Modifier 1: A = IP. Modifier 2: A = fail flag (0 or 1), then clears the flag. The IP form lets a host's copy loop check who is running it (Stringmol's evolved defences did exactly this) and lets code find itself after a jump. Self-knowledge, not privileged access: the body remains ordinary memory. Phase 1: "own" means the executing organism. Alternative (§9): the owner of the byte IP is on, which restores Tierra's hyper-parasite trick where a host's copy loop, run by a parasite's CPU, copies the host. |

Memory (fixed-register conventions keep the encoding to one byte):

| op | effect |
|---|---|
| `load r` | r = byte at [A] |
| `store r` | byte at [A] = r |
| `copy` | byte at [A] = byte at [B], then A += 1 and B += 1. Tierra's `mov_iab` plus the two increments its ancestor spent separate ops on. A one-op copy step keeps the replication loop short, which makes it more robust to mutation. |

All writes are noisy (§5.7): with probability p per write the stored byte
gets a random bit flip. `copy` also slips: with probability q per `copy`,
A or B either fails to advance or advances twice (DNA polymerase slippage
analog), which duplicates or drops a byte in the child. Bit flips alone are
substitutions only; without slippage, nothing at the physics level can
insert or delete, and gene duplication is the main source of new function
in biology. Default q = p / 4. Caveat: the child's length is still fixed by
`alloc`, so a slip shifts the tail and loses the last byte; genome growth
still needs the length arithmetic to mutate, as in Tierra. Mutation is
physics, not a separate step, so proofreading (read back, compare, rewrite)
is something an organism can evolve.

Body and reproduction:

| op | effect |
|---|---|
| `alloc r` | Claim r contiguous free bytes (free or debris) nearest to IP within the locality radius. Claimed bytes are not cleared: matter is conserved, so debris content comes along. `alloc` then `divide` with no copying therefore resurrects whatever was there. That is scavenging, allowed on purpose, and logged as a birth whose copy source is debris. A = start of the claimed region; on failure A = 0 and the fail flag is set. The region is owned by the parent until `divide`: protected from other writers, and it pays upkeep like body bytes, otherwise `alloc` would be free protected storage. An organism holds at most one pending region; a second `alloc` releases the first (content stays, ownership returns to free). On death a pending region becomes debris. Cost: base plus per byte. |
| `divide r` | The pending region becomes a new organism with IP at its start and registers zeroed (§5.2). The parent transfers min(r, parent's store) energy units to it; r is read as unsigned, so a "negative" value hands over everything. That value is parental investment, and evolvable. With no pending region: nothing happens, fail flag set. |

Energy:

| op | effect |
|---|---|
| `absorb` | Take min(patch pool, absorb rate) from the pool of the patch containing the byte at IP and add it to the store. Pool decreases by the same amount: conserved, dilute by construction. |

Held back for Phase 3 (§5.5): `drain`, `guard`, `sense`. Tierra-style
parasites do not need them; reading a neighbour's copy loop needs only
`searchf` and `jmpr`.

Sanity check, a hand-written ancestor in this op set (the op set is only
complete if this loop can be written and can pay for itself):

```
self        ; A = own start, B = own length
swap B      ; A = length,    B = own start
swap C      ; A = 0,         C = length      (copy counter)
lit D -4    ; one loop offset serves both 4-byte loops below
lit A K     ; A = absorb count
absorb      ; <-+  gather energy K times
dec A       ;   |
skipz A     ;   |
jmpr D      ; --+
alloc C     ; A = child start (B, C untouched)
copy        ; <-+  [A] = [B]; A++, B++
dec C       ;   |
skipz C     ;   |
jmpr D      ; --+  loop while C != 0
lit A E     ; A = endowment
divide A    ; child born with E energy
self        ; A = own start
jmpa A      ; start over
```

21 bytes. An earlier 12-byte sketch (2026-09-27) never absorbed, passed a
garbage register to `divide`, and ran off its own end after dividing; the
hand trace that found this is the reason the sanity check exists. A
replicator with no absorb loop is about 15 bytes, which is the minimal
replicator length that matters for seedless emergence (Phase 4).

Budget at the draft costs (§5.3.4) with absorb rate 8, K = 64, E = 16,
u = 0.1, about 13 ticks per cycle at c0 = 32:

| item | energy |
|---|---|
| absorb income | +512 |
| absorb loop (64 × 4, minus the skipped jump) | -255 |
| alloc (2 + 21) and copy loop (21 × 6, minus the skipped jump) | -148 |
| prologue, endowment literal, divide, restart | -16 |
| endowment to child | -16 |
| upkeep (21 bytes × 0.1 × 13 ticks) | -27 |
| net per child | +50 |

The absorb loop is 61% of executed instructions, which is the intended
"gathering sunlight takes most of a producer's time". The child needs
E ≥ 5 to pay its prologue; after that its own absorb loop nets positive.
Every number here is a guess; the structure is the point, and the single
genome harness (§7) measures the real budget.

Register pressure is real: all four registers are in use. Evolution's
first easy wins are visible in the listing: raise K, lower E, move
`absorb` into the copy loop (H6).

#### 5.3.4 Cost draft

| op class | cost (energy units) |
|---|---|
| nop, data, skip, jmpr, jmpa | 1 |
| load, store | 2 |
| copy | 3 |
| search | 1 + 1 per 16 bytes scanned |
| alloc | 2 + 1 per byte |
| divide | 8 |
| absorb | 1 (yields up to absorb rate) |

Numbers are guesses. Only the ratios matter, and they are tuned when the
ancestor cannot pay for replication or when nothing bothers to absorb.

### 5.4 Energy

- Each patch receives an energy income per tick (sunlight). Income varies
  in space and cycles in time (§5.6).
- Energy in a patch pool accumulates up to a cap and is otherwise lost.
- An organism gains energy only by executing an absorb op at its location.
  Absorb yields a small amount per execution: sunlight is dilute. Gathering it
  should take a large fraction of a producer's cycles.
- Every executed instruction costs energy from the organism's store.
- Upkeep: every tick an organism pays u energy per byte of body whether or
  not it executes anything. Existence has a metabolic cost. This is what
  prevents immortal loafers: without it a genome that only executes `absorb`
  never dies except by bit rot. Avida needed an explicit age limit for the
  same reason.
- An organism that cannot pay upkeep is dead: it stops, its bytes become
  debris, and they decay (§5.7) until claimed.
- Energy is compute. There is no separate scheduler fairness; an organism runs
  as many instructions per tick as it can pay for, up to a per-tick cap of
  cap = c0 + c1 × body length. This cap is the analog of Tierra's CPU slice,
  and that slice set Tierra's size trend outright (§2). Phase 1: c1 = 0
  (constant slice; expect shrinking). Phase 3 sweeps c1. An instruction
  whose cost exceeds the remaining cap waits for the next tick.
- Tick order: upkeep is charged to every organism at the start of the tick,
  then organisms execute in a seeded random permutation, fresh each tick.
  Fixed id order would give the first-born permanent priority on contested
  free space. Births take effect at the end of the tick.

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

Per patch:

- Energy income (spatial gradient + temporal cycle: day/night, seasons).
- Background bit-flip rate (radiation).
- Instruction cost multiplier (temperature/viscosity).
- Optionally, several resource types where different ops consume different
  types and regional abundance differs (crude chemistry). Deferred to Phase 3
  or later.

Slow drift: all per-patch parameters change slowly over long timescales
(continental drift analog). A non-stationary environment is a plausible
pressure against equilibrium, not an established one: no reviewed system
showed it working, and Avida's fluctuating-environment results are about
phenotypic plasticity, not open-endedness. So heterogeneity is hypothesis
H9 (§11): compare homogeneous, static-heterogeneous, and drifting worlds
with replicated seeds before crediting drift with anything.

Locality plus heterogeneity gives geography, and geography gives allopatric
speciation (populations separated by distance drift apart).

### 5.7 Entropy, noise, death

- Every tick, each byte flips with a small region-dependent probability.
- Every write has a small probability of writing the wrong value. This is the
  primary mutation mechanism during copying.
- Maintenance: since the body decays, an organism must spend cycles checking
  and repairing itself or accept accumulating damage. Bigger bodies cost more
  to maintain. Whether repair evolves is an experimental result.
- Death: an organism is dead when it cannot pay upkeep (§5.4). No fault
  kills; all ops are total (§5.3).
- No reaper. Dead bodies remain as debris until claimed or decayed. Note
  that every "no reaper" system in the literature still had forced
  turnover (Nanopond reseeds random cells, Cosmos culls at a population
  cap, Evoloops dissolves loops). Here upkeep plus decay is that turnover;
  whether it suffices is a Phase 1 measurement (§11).
- Rates: set by mutation load per genome copy, p × L, not by p alone.
  Reference loads: Tierra about 0.13 per 80-byte copy (about 1 bit per
  1,000–2,500 instructions moved), Avida default 0.85 per copy, evolved
  Avida genomes tolerate 2 to 3.6. Start at load 0.1 on the ancestor, which
  for a 12-byte ancestor means p = 8e-3 per byte written, and sweep by log
  steps. Log realized load per birth (§7) since L drifts. Tierra communities died when genome size grew 10x at a fixed
  rate: the error threshold, observed.

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
Every predecessor shrank under a constant CPU slice and bloated or collapsed
under a size-proportional one (Tierra, Cosmos; Avida is size-neutral by
construction and its complexity still plateaued). The literature gives no
example of size settling at an interior optimum by itself. The intended
counter-pressures here are interaction richness and environmental
complexity, which reward carrying more code, plus the c1 term in the tick
cap (§5.4) as a tunable. Whether an interior optimum appears is hypothesis
H3 (§11).

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
  docs/                design notes, ISA spec
  docs/research/       literature review, hypotheses log, experiment records
  evo-core/            Rust crate: VM, world, CLI
  analysis/            Python: uv project
  runs/                run outputs (gitignored)
```

## 7. Instrumentation (build before more physics)

- Organism table: id, birth tick, death tick, death cause, genome hash at
  birth, length, position, lifetime offspring count.
- Two parents per birth: the executor (whose CPU ran `divide`) and the copy
  source (whose bytes were copied). Under Tierra-style hyper-parasitism
  these differ, and Ray's logs recorded the wrong one.
- Birth record also carries generation depth and number of copy errors
  relative to the source genome.
- Genome store keyed by hash, with parent hash, so the phylogeny exports in
  the standard ALife phylogeny format.
- Mutation events tagged heritable (copy error into a child) vs somatic (bit
  rot or foreign write into a living body). Activity statistics assume
  genomes do not change in place; ours do.
- Periodic census: genome hash and count, every N ticks. This is the raw
  input for Bedau–Packard activity statistics, Channon's shadow test, MODES,
  and QNN (docs/research/literature.md); all can run offline from it.
- Per-N-ticks summary: population, distinct genomes, mean/max length, total
  energy, energy by region, interaction counts (foreign reads, foreign
  execution, blocked writes).
- Single-genome test harness: run one genome alone in a clean world to
  measure replication time, deleterious mutation fraction, and offspring
  per lifetime. Needed for MODES complexity and for the error-threshold
  check (§5.8).
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

**Phase 3 — Richer physics.** 2D torus, per-patch parameters, bit rot,
seasons, slow drift, debris, drain/defense ops. Success criteria: spatial
differentiation of lineages; some form of producer/consumer split;
evidence for or against evolved repair.

**Phase 4 — Experiments.** BFF calibration harness first: reproduce
Agüera y Arcas et al. (2024) exactly (2^17 tapes of 64 bytes, random
pairing, 8,192 steps per interaction, byte-replacement mutation at 2^-12)
to confirm their 40% emergence rate, then swap in evo's ISA on the same
protocol, then add evo's physics one rule at a time (energy, ownership,
locality). This isolates which rule, if any, kills emergence. Then soup
runs with no seed in the full world, with a start-execution rule (§9). Chemistry (multiple
resource types). Multi-day runs. Compare ISA variants for evolvability.

## 9. Open questions

- Register machine vs stack machine for the VM. Tierra and Avida are register
  machines; BFF is a two-tape Brainfuck. Register machine is the default
  guess.
- Contiguous bodies only, or allow fragmented bodies?
- Fault semantics: which faults are recoverable, which kill?
- Exact locality radius and whether cost grows with distance.
- Energy location: per organism (Phase 1 decision, 2026-09-30) or per byte
  of body (makes "where the energy is" spatial, which might matter for
  predation). Revisit with `drain` in Phase 3.
- Locality from IP (Phase 1 decision) vs from body start. IP-relative lets
  an IP wander far from its body at a per-byte energy cost; whether that
  gets abused (organisms executing free space to reach distant debris) is a
  Phase 1 observation.
- Copy slippage rate q relative to p; whether `alloc` length should also be
  able to slip, which would let bodies grow without a length-arithmetic
  mutation.
- Multi-core strategy: partition the torus into strips with halo exchange, or
  run independent worlds and migrate organisms between them (islands).
- Snapshot format: hand-rolled vs serde/bincode.
- `self` semantics: executing organism (Phase 1) vs owner of the byte at
  IP (Tierra-like, enables hyper-parasites). Cheap ISA switch; test both.
- Search: Tierra searched both directions alternately at flat cost. We have
  directional search at distance-proportional cost. Locality radius plays
  Tierra's max-search-distance role (200–400 in 1991, 5x mean adult size
  later, 10,000 in size-neutral runs).
- Seedless soup needs a rule that starts execution on random bytes
  (Coreworld injected random pointers at p = 0.05 per update; Amoeba gave
  5% of CPUs to random code). Not needed while seeded. Phase 4.
- Upkeep u and tick-cap slope c1 are the two knobs that set size selection.
  Defaults u small, c1 = 0. Sweep in Phase 3. Variant worth testing: scale
  the cap by distinct bytes executed last tick rather than bytes owned, so
  padding earns nothing (Cosmos's owned-length slice rewarded padding).

## 10. Expectations

Realistic at desktop scale: parasites, immunity, arms races, evolved
proofreading, scavenging, regionally specialized metabolic strategies, some
producer/consumer structure. Any of the latter four would exceed most prior
work.

Not realistic: multicellularity, nervous systems, anything requiring the
roughly 20+ orders of magnitude of scale separating a desktop from Earth.

## 11. Research record

The project keeps a written record from the start so that anything found can
be reported, and so that predictions are dated before the experiments that
test them.

- `docs/research/literature.md`: deeper review of prior systems (Tierra,
  Avida, Coreworld, Amoeba, BFF/Computational Life, Stringmol, Geb, and the
  open-endedness literature). For each: substrate, what emerged, where it
  plateaued, and what the authors thought was missing. This is a prerequisite
  for Phase 1 design decisions, not optional reading.
- `docs/research/hypotheses.md`: numbered, dated predictions with the
  observation that would confirm or refute each. Nine entries as of
  2026-09-30: H1 register vs stack (§5.3.1), H2 producer/consumer diagnostic
  (§5.5), H3 no interior size optimum on its own (§5.8), H4 write protection
  needed for coexistence (§5.3), H5 upkeep plus decay is enough turnover
  (§5.4, §5.7), H6 absorb-loop takeover (§5.4), H7 seedless emergence needs
  a start-execution rule (§9), H8 `self` semantics change the ecology (§9),
  H9 environmental drift delays equilibrium (§5.6).
- `docs/research/notes/`: raw per-source notes from the 2026-09-30 review,
  one file per cluster, URL on every fact, UNVERIFIED tags kept.
- `docs/research-historic/`: the earlier Codex pass. Superseded by
  `literature.md`; kept for the reference list.
- `docs/research/experiments/`: one file per experiment: seed, config hash,
  commit, what was varied, what was observed, which hypothesis it bears on.
  Runs are reproducible from seed and config (§3), so a record plus the repo
  is sufficient to regenerate any figure.

## 12. Working notes

- Languages: Rust core, Python analysis. The author knows Zig, Go, and Python;
  Rust is new. Code should be written with that in mind: idiomatic but
  explained, with comparisons to Zig/Go where a Rust concept differs
  (ownership and borrowing, traits vs interfaces, enums with data, error
  handling with `Result`).
- Related prior work by the author: cellular automata in Go at
  `D:\coding\github\go-CA-experiments`.
- Toolchain present as of 2026-09-26: cargo 1.95, rustc 1.95, Python 3.13,
  uv 0.10.
