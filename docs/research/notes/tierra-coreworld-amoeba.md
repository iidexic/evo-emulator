# Tierra, Coreworld, Amoeba: verified notes

Compiled 2026-09-30. These are raw research notes for the evo design (PLAN.md
§2, §3, §5), read from primary sources wherever they could be reached. They
verify and extend `docs/research-historic/Review.md` rather than repeat it.

Conventions:

- Every claim carries a source link. The keys are defined in the "Sources"
  section at the end; each key is a clickable link.
- "Quote:" marks verbatim text. OCR slips in the scanned sources are fixed
  silently only where the reading is certain.
- **UNVERIFIED** marks anything that is not backed by a primary source I
  actually read, or where the sources conflict.
- "(inference)" marks my own reasoning, as opposed to what the source says.

Access notes (useful for anyone repeating this work):

- `tomray.me` is now a parked domain (sedoparking). All Ray papers and the
  Tierra docs were read through Wayback Machine copies.
- The Ray 1991 URL used in the task brief and in `References.md`
  (`.../Ray1991AnApproachToLife.pdf`) has the wrong file name. The real file
  is `.../Ray1991AnApproachToTheSynthesisOfLife.pdf` ([Ray91]).
- The Coreworld 1990 paper and the Pargellis 1996, 1996b and 2001 papers are
  paywalled (Elsevier, MIT Press) and have no open-access copy. For those I
  used verbatim abstracts plus later primary papers by the same authors:
  Rasmussen, Knudsen & Feldberg in *Artificial Life II* ([RKF92]), and
  Greenbaum & Pargellis 2016 ([GP16]), which gives a first-hand history of
  every Amoeba version. Adami's 1998 textbook ([Adami98]) and Howard's 1996
  magazine article ([Howard96]) are used only as marked secondary sources.

---

## 1. Tierra (Ray, 1990 onward)

### 1.1 The virtual CPU

- Each creature gets its own virtual CPU with two address registers (ax, bx),
  two numeric registers (cx, dx), a flag register, a stack pointer, a
  10-word stack, and an instruction pointer ([Ray91] p.375, App. A;
  [TDoc] §8.3).
- ax and bx hold soup addresses kept modulo SoupSize. cx and dx are numeric,
  bounded to ±SoupSize, and reset to 0 if they leave that range ([TDoc]
  §8.4).
- Failure semantics (set 0): a failed instruction does nothing except advance
  the IP and set the flag. Every instruction, successful or not, costs
  exactly one unit of the CPU's "instruction bank" ([TDoc] §8.4). Quote:
  "Every instruction decrements the instruction bank by one, regardless of
  success or failure." **This includes template searches, whatever distance
  they scan.**
- A 5-bit opcode per soup cell, with no operands. Ray's argument: Core War
  redcode has only about 10 opcodes but, once the operands and addressing
  modes are counted, "this set works out to be about 10^11 in size" ([Ray91]
  p.376). Integers are built with bit operations (`zero`, `not0`, `shl`)
  instead of literals.

### 1.2 The 32-instruction set (set 0, the original 1990 design)

Opcode numbers are from [Ray91] App. B and the `opcode0.map` listing in
[TDoc] §8.3; semantics are from [TDoc] §8.4.

| hex | mnemonic (1991 / docs) | effect |
|---|---|---|
| 00 | nop_0 / nop0 | no-op; template bit 0 |
| 01 | nop_1 / nop1 | no-op; template bit 1 |
| 02 | or1 / not0 | flip low bit of cx |
| 03 | shl | cx <<= 1 |
| 04 | zero | cx = 0 |
| 05 | if_cz / ifz | execute next instruction only if cx == 0, otherwise skip it |
| 06 | sub_ab / subCAB | cx = ax - bx |
| 07 | sub_ac / subAAC | ax = ax - cx |
| 08 | inc_a | ax++ |
| 09 | inc_b | bx++ |
| 0a | dec_c | cx-- |
| 0b | inc_c | cx++ |
| 0c-0f | push_ax .. push_dx | push register |
| 10-13 | pop_ax .. pop_dx | pop into register |
| 14 | jmp / jmpo | jump to the nearest complementary template, searching outward (both directions) |
| 15 | jmpb | jump to the complementary template, searching backward only |
| 16 | call | push the return address, then jump like jmp (outward) |
| 17 | ret | pop the IP |
| 18 | mov_cd / movDC | dx = cx |
| 19 | mov_ab / movBA | bx = ax |
| 1a | mov_iab / movii | copy the instruction at [bx] to [ax] (the replication op) |
| 1b | adr / adro | search outward for the template; ax = address, cx = template size |
| 1c | adrb | same, searching backward only |
| 1d | adrf | same, searching forward only |
| 1e | mal | allocate cx cells for a daughter; ax = its address |
| 1f | divide | split the daughter off as an independent cell |

Grouping per [TDoc]: 2 no-ops, 11 memory moves, 9 calculations, 5 IP
manipulations, 5 "biological and sensory".

Ray's own later verdict on this set ([TDoc] §2): "one third of the original
instruction set is taken up by pushing and popping from the stack; there are
only two inter-register moves... dx isn't used for anything... there are no
moves between CPU registers and RAM". In August 1992 three alternative
32-instruction sets were added (register indirection, RPN-style roll/exchange,
and push/pop-only moves). All of them add `movdi`/`movid`, put/get I/O, a
flag test, and a `divide` that passes registers and an IP offset to the
daughter ([TDoc] §8.5; [Ray94a] "Four Artificial Worlds").

### 1.3 Template addressing: exact rules

From [TDoc] §8.4 (set 0), confirmed by [Ray91] pp.376-377:

- A template is the maximal run of consecutive nop0/nop1 cells immediately
  after the jmp/call/adr instruction. Its size is the number of nops.
- Matching is by complement (nop0 matches nop1). Quote: "The target template
  can be larger than the source template (the entire source template must be
  matched, but it may match to a sub-template in the target template)."
- Search order for outward ops (jmp, call, adr): let a be the address of the
  first template cell and s its size. The forward search starts at a+s+1 and
  the backward search at a-s-1. Quote: "The search looks in the forward
  direction first, then alternately looks ahead or back one additional step
  until the complementary template is found, or the search limit
  (Search_limit) is reached. The template searches wrap around the ends of
  the soup." jmpb, adrb and adrf search in one direction only.
- Result: jmp moves the IP to the instruction after the found template. adr*
  puts that address in ax and the template size in cx.
- Failure: the op fails if the template is shorter than MinTemplSize
  (default 1) or no match lies within the search limit. On failure the IP
  skips past the template and the flag is set. For adr*, cx is left
  unchanged.
- Maximum search distance:
  - 1991: "generally set at 200-400 instructions" ([Ray91] p.384).
  - Long size-neutral runs used a search limit of 10,000 ([Ray91] p.387).
  - Later versions: `SearchLimit = 5`, meaning 5 times the average adult
    cell size, recomputed every million instructions ([TDoc] §7).
- Searches ignore ownership: they match templates in other creatures, in
  daughters, in dead code, and in free memory. The genebank bit fields
  record exactly these cases ("TCf = matches template complement of free
  memory") ([TDoc] §7, WatchTem).
- Mutation fragility of templates: with 5-bit opcodes, 4 of the 5 possible
  single-bit flips of a nop turn it into a non-nop (destroying or shortening
  the template), and 1 in 5 turns it into the complementary nop ([Ray91]
  p.384).

### 1.4 Memory: MAL, ownership, "privileges"

- Soup: "In most of the work described here the soup consisted of 60,000
  bytes" ([Ray91] p.377). The v5 default is 50,000 ([TDoc] §7).
- Semi-permeable membrane. Quote: "Each creature has exclusive write
  privileges within its allocated block of memory... While write privileges
  are protected, read and execute privileges are not. A creature may examine
  the code of another creature, and even execute it, but it can not write
  over it." ([Ray91] p.378)
- A creature holds at most 2 blocks: its own ("mother cell") and one from
  `mal` ("daughter cell"). On `divide` the mother loses write access to the
  daughter, and the daughter gets its own IP and enters the queues
  ([Ray91] p.378).
- Configurable protection ([TDoc] §7): MemModeFree / MemModeMine / MemModeProt
  are rwx masks. The default MemModeProt = 2 write-protects other creatures'
  memory. Read and execute protection exist only as compile-time options,
  and "The version distributed on disk only has write protection turned on."
- `mal` ([TDoc] §8.4):
  - The request size is in cx. mal invokes the reaper if no free block
    exists, but "the reaper will never kill the creature making the
    request". The block may not wrap around the end of the soup.
  - mal fails if the request is <= 0, if it repeats the same size without
    an intervening `divide`, or if it exceeds MaxMalMult (3) times the
    creature's size. Reason given: "This prevents mutants from requesting
    the entire soup".
  - Successful mal moves the creature down the reaper queue.
- Placement (`MalMode`): 0 = first fit (all versions before 4.0), 1 = better
  fit (default), 2 = random, 3 = near mother, 4/5/6 = near an address in a
  register or on the stack. With placement modes the reaper can be limited
  to kill only near the requested location (`MalReapTol`) ([TDoc] §7).
- `divide` fails if:
  - the daughter is smaller than MinCellSize (8-12). Reason: "there is a
    tendency for some mutants to spawn large numbers of very small cells";
  - the mother wrote less than MovPropThrDiv (0.7) of the daughter's size
    into it. Reason: "without it, mutants will attempt to spew out large
    numbers of empty cells";
  - DivSameGen or DivSameSiz is set and the daughter differs. These
    switches exist to freeze evolution for ecology experiments
    ([TDoc] §7, §8.4).
- Dead code stays. Quote: "Their 'dead' code is not removed from the soup."
  ([Ray91] p.379) Embryos take a lot of space: "embryos generally fill half
  the soup" ([TDoc] §7, SavThrMem).

### 1.5 The slicer (CPU scheduling)

- A circular queue. A newborn gets its own virtual CPU and is inserted next
  to its mother, so that "the newborn will be the last creature in the soup
  to get another time slice after the mother" ([Ray91] p.378).
- Slice length depends on genome size. Quote ([Ray91] pp.378-379): "The
  number of instructions to be executed in each time slice is set
  proportional to the size of the genome of the creature being executed,
  raised to a power. If the 'slicer power' is equal to one, then the slicer
  is size neutral... If the power is greater than one, large creatures get
  more CPU cycles per instruction... A constant slice size selects for small
  creatures."
- v5 parameters ([TDoc] §7):
  - `SizDepSlice` (0 = constant, 1 = size^SlicePow).
  - `SliceSize` (default 25).
  - `SliceStyle`: 0 = fixed, 1 = photon, 2 = fixed plus random component.
    The sample config uses SliceStyle 2 with slice uniform on 0..50, **not
    size-dependent, so the default config selects for small size**.
  - Unused slice is carried over in an "instruction bank".
- Photon slicer (`SliceStyle = 1`). Quote ([TDoc] §7, PhotonPow): "Imagine
  that photons are raining down on the soup at random. The cell hit by the
  photon gets a time slice that is proportional to the goodness of fit
  between the pattern of instructions that are hit, and an arbitrary pattern
  (defined by PhotonWord)." The default PhotonWord is `chlorophill`, the
  match score is raised to PhotonPow = 1.5, and the photon slides over a
  PhotonWidth = 8 window. **UNVERIFIED:** any published results from runs
  using this slicer.

### 1.6 The reaper

- It starts killing when memory reaches a threshold ("e.g., 80%"). Killing
  means freeing the memory and removing the creature from both queues
  ([Ray91] p.379).
- A linear queue:
  - a newborn enters at the bottom and the top is killed;
  - an instruction that raises an error moves the creature up one place,
    "as long as the individual ahead of it in the queue has not accumulated
    a greater number of errors";
  - successful execution of the two hard instructions moves it down one
    place ([Ray91] p.379). [TDoc] §8.4 identifies these as `mal` and
    `divide`.
- Ray's summary: "algorithms which are fundamentally flawed... rise to the
  top of the queue and die... in general, the probability of death increases
  with age" ([Ray91] p.379).
- v5 extras ([TDoc] §7):
  - `ReapRndProp = 0.3` kills a random creature from the top 30% of the
    queue;
  - `MalReapTol` kills the oldest creature near the requested allocation;
  - `DistFreq`/`DistProp` add disturbance (mass reaping);
  - `EjectRate = 50` removes 1 in 50 newborns. On a single node, ejection
    means death.
- (inference) The error rule is a small built-in fitness function: failed
  searches and failed calls shorten life. Ray credits it for density
  dependence: when hosts are scarce, parasites' "calls to the copy procedure
  fail and generate errors, causing them to rise to the top of the reaper
  queue and die" ([Ray91] p.391).
- Alternatives to the reaper that others tried ([Ray94b] "Artificial Death"):
  - Barton-Davis: flaw rate rises with age, and death comes at 100%;
  - Skipper: a suicide instruction, so organisms evolve to make *others*
    execute it;
  - Litherland: death by local crowding;
  - Davidge: death on certain register values;
  - Gray: death after six reproduction attempts.

### 1.7 Mutation

Three noise sources ([Ray91] pp.379-380):

1. **Background "cosmic rays".** Random bits anywhere in the soup (60,000
   instructions = 300,000 bits), including free memory. The rate is "about 1
   bit flipped for every 10,000 Tierran instructions executed by the system".
   Purpose: it "has the effect of preventing any creature from being
   immortal, as it will eventually mutate to death."
2. **Copy mutation.** Bits flipped in copies made by mov_iab, "about 1 bit
   flipped for every 1,000 to 2,500 instructions moved". One of the 5 bits
   is chosen at random ([TDoc] §7, GenPerMovMut).
3. **Flaws.** Results are off by ±1 at a low rate: inc adds 2 or 0, shl
   shifts by 2 or 0, register choice can be wrong ([Ray91] p.380; [Ray94b]
   "Flaws"). [TDoc] §7: the flaw rate "has a profound effect on the rate at
   which creatures shrink in size under selection for small size."

More detail:

- Intervals between mutations are drawn at random "to avoid possible
  periodic effects" ([Ray91] p.379). In v5 the rates are set per generation:
  GenPerMovMut = 8 (about 1 in 8 cells gets a copy mutation per
  generation), GenPerBkgMut = 16, GenPerFlaw = 32 or 64. The realized
  intervals are uniform with range twice the mean ([TDoc] §5, §7).
- Tierra's genetic operators are bit flips only (plus optional haploid
  crossover, `MateProb`). Insertions and size changes arise indirectly:
  mutated self-examination copies the wrong length, and parasites are
  "sloppy replicators" whose "ad hoc sexuality" moves code between creatures
  ([Ray91] p.380; [Ray94b] "Mutations"; [TDoc] §7 mating).
  - Example: 0051aao is 0045aaa with "instruction 39... replaced by an
    insertion of seven instructions of unknown origin" ([Ray91] p.385).
- Consequence: evolution continues with the mutation rate at 0. Ecology
  experiments therefore also had to force "creatures must breed true"
  (DivSameGen) ([Ray92] ECOLOGY).
- Rate scan ([Ray92] "Evolutionary optimization"; rates expressed as 1
  mutation per N generations):
  - N = 1 or 2: "The genomes melt"; the community often dies.
  - N = 4: fastest optimization without collapse.
  - N = 8 or 16: "the diversity of coexisting size classes... the greatest,
    and... persist the longest."
- Error threshold observed directly. Two long-run communities died when
  "the mutation rate was not lowered during the run, while the average
  genome size increased by an order of magnitude until it approached the
  average mutation rate... the genomes may simply have 'melted'" ([Ray91]
  p.390).

### 1.8 The ancestor 0080aaa

Listing in [Ray91] App. C and [TDoc] §9.1 (identical code). 80 instructions,
of which 48 are nops forming 12 four-bit templates ([Ray91] p.382).

| cells | role |
|---|---|
| 0-3 | begin marker `1111` |
| 4-8 | build cx = 4 (zero, not0, shl, shl), movDC: dx = 4 (dx is vestigial) |
| 9-15 | `adrb 0000` (finds its own start), subAAC, movBA: bx = own start |
| 16-22 | `adrf 0001` (finds its end), incA, subCAB: cx = size |
| 23-26 | reproduction-loop marker `1101` |
| 27-33 | `mal` (daughter address in ax), `call 0011` (copy procedure), `divide` |
| 34-38 | `jmp 0010` back to the reproduction loop |
| 39 | dummy `ifz` separating templates |
| 40-46 | copy-procedure marker `1100`, push ax, bx, cx |
| 47-65 | copy loop `1010`: movii, decC, ifz, `jmp 0100` (exit), incA, incB, `jmp 0101` (loop) |
| 66-74 | dummy, exit marker `1011`, pop cx, bx, ax, `ret` |
| 75-79 | end marker `1110`, dummy `ifz` |

- Cost: 839 instructions for the first replication and 813 for each later one
  ([Ray91] p.382). The docs' genome header gives 827/809 ([TDoc] §9.1).
  That is about 10 CPU cycles per instruction copied ([Ray92]).
- After its first replication it does not re-examine itself; it loops
  mal → copy → divide ([Ray91] p.382).
- Scale: starting from one ancestor, the soup fills to 80% with about 375
  size-80 creatures (plus gestating daughters) in about 400,000 instructions
  ([Ray91] p.382).
- Speed: 12 M Tierran instructions per hour on a 20 MHz 386 laptop, about
  1 M per minute on "mini and mainframe computers" ([Ray91] p.382).

### 1.9 What evolved, and how it worked mechanically

All from [Ray91] pp.383-387 and [Ray92] unless noted.

- **Parasite 0045aaa.**
  - Origin: a low-bit flip at instruction 42 turns the copy-procedure marker
    `1100` into `1110`, the end marker. Self-exam then measures size 45 and
    copies only cells 0-44, leaving out the copy procedure.
  - How it replicates: its `call` finds no local template, but "if it is
    within the search limit (generally set at 200-400 instructions) of the
    copy procedure of a creature of genotype 0080aaa, it will match
    templates, and send its instruction pointer to the copy code of
    0080aaa."
  - It runs on its own CPU with its own registers, so the host's code copies
    the parasite. Harm is only competition: "The host is not adversely
    affected by this informational parasitism, except through competition"
    (Fig. 1 caption).
  - Timing: parasites appear "within the first few million instructions".
- **Immunity (0079aab).** Flanked by 0079aab, 0045aaa is "quickly
  eliminated". 79-dominated soups repel parasites for long periods.
  **UNVERIFIED:** the mechanism of the immunity (Ray does not give it).
- **Circumvention (0051aao).** Coexists with 0079aab in a stable cycle; its
  14 siblings 0051aaa-aan cannot. Mechanism not given.
- **Hyper-parasite 0080gai** (19 instructions differ from the ancestor). Two
  changes:
  - (a) the copy procedure jumps straight back into the reproduction loop
    instead of `ret`, which captures the IP of any parasite that called it;
  - (b) it re-examines itself after every reproduction, writing its own
    location into bx and size into cx.
  - When a parasite's CPU runs through that code, "the CPU of the parasite
    contains the location and size of the hyper-parasite and the parasite
    thereafter replicates the hyper-parasite genome." This is theft of
    another CPU's time, i.e. energy.
  - It only works because self-location is computed by template search
    relative to the IP inside the hyper-parasite's own code.
- **Social hyper-parasites (0061acg).**
  - They jump back to a template at the *end* of their genome. The match is
    found in the tail of the neighbour above, and execution "falls off the
    end of the creature" into the start of the active one (Fig. 2 caption).
  - They cannot replicate alone. They are 24% smaller than the ancestor and
    use 3-bit templates (only 8 labels), so catching each other's jumps
    lets them reuse templates.
  - Ray's explanation: sociality "facilitates size reduction".
- **Cheaters (0027aab).** Sit between social creatures, capture the IP as it
  passes, load their own location and size into the registers, and hand
  control back after skipping self-exam.
- **Novel self-exam.** One lineage marks start and middle, subtracts, and
  shifts left to double.
- **Loop unrolling.** Found in a 15-billion-instruction run: a size-36
  creature repeats the copy work three times per loop, "18 CPU cycles to
  copy three instructions" ([Ray92] §EVOLUTIONARY OPTIMIZATION). The
  genome size of 36 is stated in [Ray92] §INCREASING COMPLEXITY, and the
  code listing is in App. E.
- **Optimization under selection for small size.** Plateaus at 22, 27 and
  30 instructions. The 22-instruction creature needs 146 cycles per
  replication versus the ancestor's 839: "a 5.75-fold difference". Quote:
  "each run decreases to a size limit which it can not proceed past even if
  it is allowed to run much longer" ([Ray92]).
- **Symbiosis was hand-made.** "The ancestor was manually dissected into two
  creatures" (46 and 64). "It is not known if such relationships have
  evolved spontaneously." ([Ray91] p.393)

### 1.10 Ecology experiments (mutation off, breed-true on)

- Hosts with parasites show Lotka-Volterra cycling. The coupling is
  density-dependent through the search limit ([Ray91] p.391).
- Competitive exclusion (size 79 against larger sizes):
  - 79 vs 80 and 79 vs 81: stable cycles;
  - 79 vs 82-89: chaotic but symmetric;
  - asymmetric from size 90; size 93 extinct after about 6 M instructions;
  - the "metabolic cripple" size 89 (40% more cycles) was eliminated in
    under 1 M instructions ([Ray91] pp.391-392).
- Keystone parasite: a 20-size-class host community dropped to 8 classes in
  30 M instructions. With 0045aaa added, 16 classes remained ([Ray91] p.392).

### 1.11 Long runs and stasis

Size-selection regimes ([Ray91] p.387; [Ray92] Macro-evolution):

- **Selection for small** (constant slice): proliferation of small
  parasites, and optimization to a local plateau (22-30).
- **Selection for large** (slicer power > 1): "continuous incrementally
  increasing sizes... until a plateau in the upper hundreds". In one run,
  "genomes larger than 23,000 instructions".
- **Size-neutral** (power = 1, search limit 10,000; runs up to 2.86 × 10^9
  instructions):
  - dominated by sizes in the 80s for 178 M to 1.44 × 10^9 instructions;
  - then "very abruptly (in a span of 1 or 2 million instructions)" a jump
    to 400-800;
  - after that, punctuated equilibrium, with chaotic phases where "no
    genotypes breed true".

Diversity:

- 366 size classes in a 526 M-instruction run (93 reached 5 or more
  individuals); 1180 size classes in a 2.56 × 10^9 run.
- More than 29,000 self-replicating genotypes in more than 300 size classes
  were banked ([Ray91] p.390).

Ray's later verdict ([RayATR], about 1999). Quote: "after a prolonged period
of rich adaptive evolution, Tierra inevitably enters a period of permanent
evolutionary stasis... it could be argued that the ecological community
increases in complexity, before entering stasis. However, the individual
replicators generally do not increase in complexity, although some examples
of increased algorithmic complexity in the replicators have been found."

### 1.12 Instruction set changes evolution (Ray 1994)

[Ray94a] ran the same ancestor, adapted to four instruction sets, 8 runs
each (4 for the original). Sizes are the smallest evolved genomes:

| set | ancestor | smallest per run | mean opt. | pattern |
|---|---|---|---|---|
| I1 (original) | 73 | 27, 27, 26, 22 | 0.35 | "punctuated gradualism", plateau within about 600 generations |
| I2 (register indirection) | 94 | 54-60 | 0.60 | pure gradualism, about 1000 generations |
| I3 (RPN) | 93 | 34-54 | 0.48 | pure gradualism |
| I4 (push/pop moves) | 82 | 23-43 | 0.34 | "punctuated equilibrium, with no clear signs of gradualism" |

- In I4, the *larger* end-points were the *more* efficient ones, because they
  unrolled the loop (3.33 vs 5.19 cycles per byte; ancestor 8.39).
- Ancestor 688 cycles per replication versus 95 for a size-24 creature
  (7.24-fold).
- Ray's conclusion ([Ray99evo]): "many aspects of the evolutionary process
  depend on the structure of the underlying genetic language. Yet, there
  exists no body of theory to guide in the design of enhanced evolvability."

### 1.13 Standish 2003: size is not complexity

[Std03]:

- Method: organisms from one size-neutral Tierra run were grouped into 26
  phenotype archetypes by pairwise tournaments in miniTierra (about 1000×
  faster). Complexity was then measured as information: the number of
  neutral variants, explored by a neutral-network walk out to 2 hops (C2),
  plus a cheap proxy C_NV, the count of sites where some mutation changes
  the phenotype.
- Result. Quote: "Over this Tierra run of 6 × 10^9 instructions, there is no
  sign of complexity increase, although lengths of the organisms do increase
  from 80 initially to 526 instructions long by 1.4 × 10^9 instructions
  executed."
- The ancestor 0080aaa has the highest C2 in the table (69.96). Later large
  organisms (0182aaa-0397aab) score about 34-63.
- C_NV is a good proxy: at most 58% off, computed in about 3 CPU-hours
  versus about 8 CPU-years for C2.
- Network Tierra, per Standish: organisms persisted "in a multicellular state
  under mutational load... they haven't achieved their aim of complexity
  growth."

### 1.14 What Ray thought was missing, and why he moved on

- **The single-node environment rewards nothing but fast copying.** Quote
  ([Ray95] "How"): "A primary obstacle to the evolution of complexity in the
  Tierra system has been that in the relatively simple single node
  installation, a very simple twenty to sixty byte algorithm that quickly
  and efficiently copies itself can not be beat by a much more complex
  algorithm, which due to its greater size would take much longer to
  replicate. There is just no need to do anything more complicated than copy
  yourself quickly."
- **Scale alone will not fix it.** Quote ([RayATR]): "a simple scaling up of
  the original Tierra experiment would certainly not cause an evolution of
  complexity or an escape from stasis."
  - The network was wanted for its *heterogeneity*: Tierra ran as a
    low-priority background process, so CPU time varied by machine and by
    time of day. Sensing and migration were added so organisms could track
    it ([Ray95]; [RayATR]).
  - It also gave more space: "a single individual might fill such a small
    space" ([RayATR]).
- **Multicellularity as the next major transition.** Ray saw it as the
  analog of the Cambrian explosion: the move from single-threaded to
  differentiated multi-threaded code ([RayATR]; [TDoc] §12).
  - Implementation: several CPUs share one genome (`split`, `join`,
    `csync`), and the mother sets the daughter's IP and registers
    (differentiation) ([TDoc] §12, §8.5).
  - Seed: 2 reproductive cells plus 8 sensory cells. Result: the sensory
    tissue split into two, so cell types went from 2 to 3 ([RayATR]).
- **Ray's own 1991 proposals match evo's premises.** [Ray91] p.399-400:
  - "predation could be selected for by removing the reaper from the
    system";
  - "make instructions expensive": mov_iab should leave zeros behind
    ("conservation of instructions"), and creatures would synthesize
    instructions by bit operations;
  - CPU time via "special arrays of instructions or bit patterns (analogous
    to chlorophyll) which capture potential CPU time packets raining like
    photons onto the soup";
  - a genotype/phenotype split.
  - Also from 1991: "there is always free memory space available; thus,
    there would be little to be gained through seizing space."
- **Ray was sceptical of 2D Euclidean memory.** Quote ([Ray94b] "Spatial
  Topology"): "The flaw in all of this logic derives from the erroneous
  supposition that computer memory is a Euclidean space." He preferred to
  enrich memory topology through cache, RAM, disk and network distances.

---

## 2. Coreworld (Rasmussen, Knudsen, Feldberg, Hindsholm 1990)

### 2.1 What was readable

- The full 1990 paper (Physica D 42:111-134) is paywalled and not in any open
  repository (OpenAlex: `closed`). Verbatim abstract via [Ras90abs].
- The mechanism is from the same group's *Artificial Life II* paper [RKF92]
  ("Dynamics of Programmable Matter", pp. 211-254). It defines "Venus I" and
  states: "Venus I is also discussed in Rasmussen et al. [Physica D 1990]".
  Venus I is the Coreworld system with parallel update; Venus II is the same
  with sequential update.

### 2.2 Abstract (verbatim, [Ras90abs])

> We have developed an artificial chemistry in the computer core, where one
> is able to evolve assembler-automaton code without any predefined
> evolutionary path. The core simulator in the present version has one
> dimension, is updated in parallel, the instructions are only able to
> communicate locally, and the system is continuously subjected to noise.
> The system also has a notion of local computational resources. We see
> different evolutionary paths depending on the specified parameters and the
> level of complexity, measured as distance from initially randomized core.
> For several initial conditions the system is able to develop extremely
> viable cooperative structures (organisms?) which totally dominate the core.
> We have been able to identify seven successive evolutionary epochs each
> characterized by different functional properties. Our study demonstrates a
> successive emergence of complex functional properties in a computational
> environment.

### 2.3 The machine (Venus I and II) [RKF92] §3.1

- **Core and instruction set.** A 1D cyclic core. Each address holds one
  redcode instruction from the 10 Dewdney Core War opcodes: DAT, MOV, ADD,
  SUB, JMP, JMZ, JMN, DJN, CMP, SPL. There are 4 addressing modes (#, $, @,
  <), and all addressing is relative. Rasmussen kept redcode "out of
  historical reasons... This instruction set is by no means optimal for our
  purpose".
- **Pointers.** Up to L execution pointers. SPL creates one; DAT or lack of
  resources kills one. New random pointers are injected with probability
  P_point on each update "to assure that the system is always active".
- **Locality.** Reads, writes and jumps are limited to an operation radius
  R_opr; out-of-radius targets wrap back into it.
- **The computational-resource rule** (the key physics). Quote: "Each
  address is, therefore, associated with a certain amount of computational
  resources r(y,t) (0 < r(y,t) < 1) measured in fractions of one
  execution... An instruction is executed if its address has a pointer, and
  its local resource neighborhood (R_res addresses to either side...) has
  sufficient computational strength (at least what corresponds to one
  execution). Insufficient resources will eliminate execution pointers...
  At each core update, a certain amount of computational resource, Δr, is
  supplied to every address up to a given maximal level r_max, which is
  always smaller than the equivalent of one execution." Why it was added:
  "primarily to prevent a high number of pointers at the same address and to
  enhance cooperative interactions among different instructions."
- **Noise.** Each executed MOV mutates the moved word with probability
  P_mut. The word becomes any of the 10 legal instructions with random
  operands, so every result is valid syntax.
- **Parameters.** Defaults are (N, L, Δr, r_max, R_res) = (3584, 220, 0.5,
  0.5, 3), with R_opr = 800 or = N. Quote: "the most interesting
  self-organizing processes occur when the system parameters are combined to
  yield a high resource regeneration rate... It corresponds to a 'fertile
  computational jungle.'"
- **Initial conditions matter.** A homogeneous random core "is not optimal".
  Cores are biased with Markov matrices (e.g. MOV followed by a jump back),
  or seeded with a self-replicating program, to create "initial reactivity"
  ([RKF92] §4.2).

### 2.4 What happened [RKF92] §4.3-4.6, §7

- **Seeded self-replicators broke.** Quote: "the self-replicating programs
  typically start malfunctioning after 200 iterations due to computational
  noise and copying on top of each other, and, hence, no higher-order
  self-replicating properties are preserved. The valuable effect of this
  program is that it creates a reactive, inhomogeneous core."
- **Cooperative structures emerged and persisted.**
  - *MOV-SPL*: MOVs copy MOVs and SPLs, and SPLs hand pointers to MOVs and
    SPLs. It "persists indefinitely (more than 100,000 iterations) although
    some other instructions, due to noise, enter the system".
  - *Jump / fixed-point cores*: pointers trapped on JMN loops, refreshed by
    MOVs. These were "more perturbation stable than the MOV-SPL structures".
  - *SPL-JMZ colonies* that compete for pointers.
  - *Pure MOV cores*.
  - Frequencies in Venus I (R_opr = N = 3584): the fixed point "a little more
    than every second simulation", viable MOV-SPL "one out of four".
- **What "cooperative structure" means.** A recurrent set in the
  *interaction graph* of which instructions hand pointers to, or copy,
  which others. Quote: "these cooperative structures are spatio-temporal
  structures which reproduce as a whole and not through an individual
  reproduction of the each of the parts." The authors compare them to
  autocatalytic sets.
- **Epochs.** Successive quasi-stationary states, visible as plateaus in
  opcode Shannon entropy and mutual information: "The functional dynamics
  exhibits what population biologists call punctuated equilibria" ([RKF92]
  §4.5). Transient length grows with core size (180 runs, N = 112 to 3584).
- **Role of noise** ([RKF92] §7 iii-v):
  - "noise in such a system is still an important driving factor. The noise
    can 'push' the system from one metastable state to another and speed up
    the evolutionary search process";
  - "Functional stability to perturbations is a product of evolution and not
    a property of the details of the underlying programmable matter";
  - frozen accidents; qualitatively different outcomes from identical
    parameters.
- **Driving matters.** With weak driving (small Δr) "the systems are
  virtually inert".
- **Luna shows why the resource rule exists** ([RKF92] §5). A simpler
  5-instruction machine (COPY, ADD, CREATE, REVERSE, DAT) with no resource
  limit is taken over by one instruction: COPY(0,+1) floods the core. Quote:
  "a clear example of a self-sufficient, one-object replication process,
  which does not leave any room for a more involved evolution process... To
  enhance the cooperation between different instructions... we need to
  eliminate some of the COPY instruction's self-sufficiency. This can be done
  through a definition of computational resources as in Venus or by
  assigning a finite lifetime to each pointer." Also: "Simplifying the
  instruction set below a certain level of complexity inhibits the emergence
  of higher-order cooperative structures" (§7 vii).

### 2.5 Verdict on "Coreworld degraded to noise"

**Wrong as stated.**

- The abstract reports "extremely viable cooperative structures (organisms?)
  which totally dominate the core" and "seven successive evolutionary
  epochs".
- The companion paper shows noise-stable structures persisting for more than
  100,000 iterations.

**The kernel of truth:**

- Seeded Core-War self-replicators did fall apart within about 200 iterations
  under noise and overwriting ([RKF92]).
- No individual program with a fixed genotype ever emerged. Adami: "While no
  program with a fixed genotype ever emerges in this world, the overall core
  can evolve to be stable with cooperating program fragments" ([Adami98]
  §2.2).
- The persistent structures were collective (reproduce-as-a-whole), not
  individual replicators.

**Where the shorthand probably comes from:** Wikipedia, "Digital organism":
"Rasmussen did not observe the evolution of complex and stable programs. It
turned out that the programming language in which core world programs were
written was very brittle, and more often than not mutations would completely
destroy the functionality of a program" ([WPdo]). The same article also says
Coreworld introduced "a genetic algorithm", which does not match the
primary description.

**Accurate one-liner for PLAN.md §2:** "Seeded redcode replicators broke
within ~200 updates; what emerged instead were noise-stable, core-dominating
collective structures (MOV-SPL, jump cores) with punctuated epochs, but no
individual replicators. Redcode's operand-carrying ISA was the limit."

### 2.6 Follow-ups

- [RKF92] also sketches a stepwise transformation Coreworld → CA and
  AlChemy → Coreworld, noting that "somewhere along this particular
  transformation path, we come close to the definition of the Tierra
  system."
- Ray visited Los Alamos and watched the Coreworld team; this led to Tierra
  ([Adami98] §2.2-2.3).
- Adami describes two regimes, "desert" and "jungle"; the jungle gave
  "complex adaptation, but very much dependent on random events in the early
  history of the core" ([Adami98] §2.2, secondary).

---

## 3. Amoeba (Pargellis 1996, 1996b, 2001, 2003; Greenbaum & Pargellis 2016, 2017)

### 3.1 Version history (first-hand, [GP16] Introduction)

| version | paper | ISA | addressing | memory topology |
|---|---|---|---|---|
| Amoeba-I | [Par96a], [Par96b] | 16 opcodes, no stack, not computation-universal | "Complements of the opcodes themselves were the addresses so it was impossible to move to arbitrary positions in memory" | short sequences on a 2D "interaction grid" |
| Amoeba-II | [Par01] | 32 opcodes, computationally universal, 2 stacks per CPU | 64 address labels, randomly assigned per instruction ("opcode::address pairs, making it difficult to navigate throughout memory") | UNVERIFIED (not stated in the abstract) |
| Amoeba-III | [Par03] | codon templates mapped to opcodes through an evolving assignment matrix | opcode::address pairs | 500 parallel bands ("mini Turing tapes") |
| Amoeba-IV | [GP16], [GP17] | 25 opcodes, universal, Avida-style nop modifiers | Tierra nop templates | 500 bands × 2399 = about 1.2 M opcodes, toroidal 2D |

### 3.2 Amoeba-I (1996)

- **Abstract, verbatim** ([Par96a]): "Digital cells, consisting of sequences
  of computer operations which code for self-replication, spontaneously
  emerge from a primordial 'soup', initially composed only of random
  sequences. The probability of generating a self-replicator increases with
  the number of operations in its sequence. Random mutations drive the
  self-replicators to evolve into more efficient and complex organisms as
  they compete with other species for the computer system's two main
  resources, cpu time and internal memory. The initially large replicators
  first reduce their size by eliminating useless operations. Later, their
  size increases again as they optimize their replication efficiency by
  adding more subroutines."
- **Companion abstract, verbatim** ([Par96b]): "...randomly generated
  sequences of computer operations selected from a basis set of 16 opcodes.
  With a probability of about 10^-4, these sequences spontaneously generate
  large and inefficient self-replicating 'organisms'. Driven by mutations,
  these protobiotic ancestors more efficiently generate offspring by
  initially eliminating unnecessary code. Later they increase their
  complexity by adding additional subroutines... The ensuing biology
  includes replicating hosts, parasites and colonies."
- **ISA structure** (secondary, [Adami98] §2.4):
  - Pargellis cut fragility by using 16 instructions, with no stack, no
    push/pop, and no register arithmetic. "Once addresses are loaded into
    registers, they can only be changed by loading a different address."
  - "all instructions can be used as patterns, and eight of the 16
    instructions are the complement of another eight."
  - The minimal self-replicator is 5 instructions. Most replicators use 6-7
    of the 16.
  - The replicator probability P_n rises monotonically with length n: P_1-P_5
    computed exactly, larger n measured (Adami Fig. 2.10, from [Par96b]).
    **UNVERIFIED:** the exact P_5 value (the scan is garbled).
  - Adami argues the rise happens *because* the set is not universal: in
    Tierra or Avida extra instructions usually corrupt registers, so P_n
    falls with n.
- **Phases** ([Adami98] §2.4, secondary; the names are confirmed as
  Pargellis's own in [GP16]): prebiotic → protobiotic (copies itself
  correctly once but not twice; survives in colonies of similar genotype
  "that replicate each other if the instruction pointer is lost to a
  neighbor") → biotic (robust self-replicators).
  - In Adami's reproduced run, entropy drops sharply and a robust replicator
    appears at generation 1274; the biotic phase starts around generation
    4000.
- **Scale and initialization. UNVERIFIED; secondary sources conflict.**
  - [Howard96]: 1000 memory locations, each holding one cell of up to 30
    instructions. 70% of the soup is seeded with cells of 1-25 random
    instructions. When all 1000 are full, a reaper kills 30% and adds new
    random cells. Replicators appear "after about 400 generations" on
    average. Mutation: 10% chance per reproduction that one instruction
    changes.
  - [Adami98]: "a thousand cells... a constant percentage (4 percent in this
    case) of the cells were replaced by random code"; mutation at a fixed
    small rate (the scan is garbled around 10^-4 to 10^-3); cells on a 2D
    grid, moving at random, with "a global reaper queue much as in tierra".
- **After emergence:** shrink first (drop useless code), then grow by adding
  subroutines; hosts, parasites and colonies appear ([Par96a]; [Par96b]).
  **UNVERIFIED:** how large the growth was, and over what time.

### 3.3 Amoeba-II (2001): the address-label change

- **Abstract, verbatim** ([Par01]): "The current version of Amoeba broadens
  the original system's capability by using a basis set of 32 machine
  instructions that is computationally universal. In addition, Amoeba uses a
  set of 64 address labels, each of which is randomly assigned to a machine
  instruction each time a sequence is randomly created. This eliminates the
  constraint that occurs when the complements of predefined codons are used
  for addressing. A more open-ended system results because programs can now
  form subroutines that are arranged in an arbitrary manner."
- **The constraint it removed.** In Amoeba-I the opcode *was* the address:
  a jump target was found by complement matching on opcodes ([GP16]: "it was
  impossible to move to arbitrary positions in memory"). What an
  instruction does and where it can be reached from were welded together.
  So subroutine entry points were tied to which opcodes happened to sit
  there, and the layout of code was constrained by its own labels.
  (inference: my paraphrase of the abstract plus [GP16].)
- **What replaced it.** Every instruction carries an independent label drawn
  from 64. [GP16]'s criticism of this design: opcode::address pairing makes
  it "difficult to navigate throughout memory" (Amoeba-II and III).
- **UNVERIFIED:** Amoeba-II memory size, run lengths, emergence rates, and
  post-emergence size and subroutine trends. The full text was unavailable.
  The abstract makes no result claims beyond "more open-ended".

### 3.4 Amoeba-III (2003)

- **Abstract, verbatim** ([Par03]): "The computer world, Amoeba, has many
  virtual CPUs acting upon sequences of randomly generated codons (opcode
  templates). An assignment matrix degenerately maps these codons to a
  genetic basis set of opcodes... Amoeba self-organizes by increasing
  assignment probabilities for those codon-opcode pairs in successfully
  generated children. This halves the effective size of the opcode basis
  set, doubling the rate of emergence over the control case."

### 3.5 Amoeba-IV (2016/2017): the most detailed primary data [GP16]

- **ISA.** 25 opcodes (table in [GP16]):
  - templates: NOP1, NOP2;
  - reproduction: MALL, COPY, DIVD;
  - control: IFAG, IFAL, JMPB, JMPF, CALL, RETN;
  - addressing: ADRB, ADRF;
  - registers and stacks: SWEF, TOGS, PSHA, POPA, ADDA, SUBB, BEQA, AEQZ,
    INCA, DECA, INCD, DECD.
  - 8 ops take an Avida-style modifier from a following NOP.
- **CPUs.** 4 numeric registers, 2 address registers, 2 stacks, and an IP.
- **Memory.** About 1.2 M opcodes in 500 bands × 2399. The band length is
  prime "to prevent cells from being able to generate an integral number of
  children along a band".
- **Scheduling.** 2000 virtual CPUs. The slice is proportional to size, with
  a minimum of 6 and a maximum of 100 operations.
- **Random influx.** Each generation, 5% of CPUs are assigned to random
  sequences, and 100 random 1-3 opcode sequences are inserted, peaked in the
  middle bands ("melted" middle, quiet edges).
- **No write protection.** "The MALL opcode only defines the start position
  for a child's opcodes and assigns it a virtual CPU."
- **Mutation.**
  - Per COPY: 0.005 substitution.
  - At DIVD: insertion 0.02, deletion 0.02, substitution 0.06.
  - "Divide mutation rates above 0.20 randomize opcodes faster than
    building-blocks... are propagated while rates below 0.05 overly bias the
    opcode basis set; NOPs dominate".
- **Emergence path:**
  1. The basis set biases from 25 to about 15-20 effective opcodes within
     about 50,000 generations.
  2. Short "building blocks" spread through memory. An example is the
     propagator {CALL, COPY, INCA, RETN}, which copies forever with no exit.
  3. A proto-replicator appears "usually within a million generations".
  4. It then becomes robust, sheds code, and unrolls the copy loop.
- **Emergence rate.** 25 of 49 runs. The probability of emergence falls after
  about 1 M generations because NOPs keep rising: "after ten million
  generations more than 25% of the opcodes are either NOP1 or NOP2".
- **Sizes.**
  - Smallest self-replicator about 15 opcodes (14 without self-exam).
  - Ancestral replicators "typically include 200 to 300 opcodes".
  - Protobiotics reach the 450-opcode cap.
- **Ecology.**
  - "The Amoeba systems have always been dominated by variants of a single
    species after emergence. We have never observed two radically different
    species co-existing. Viruses occur, but are quickly eliminated". The
    authors suggest adding "write-protection... (similar to Tierra)" or
    region-specific slice rules.
  - Cheaters: because the slice depends on a size read from the AX
    register, "they use multiple ADDA opcodes to increase the AX-value to
    many times the cell's size".
- **An engine convenience changed evolution.** MALL auto-loads the child's
  start address into CX, so replicators often lose ADRB. It is kept only to
  "capture rogue IPs, enabling the host to commandeer the virtual CPUs
  associated with other cells".
- **2017 journal version** ([GP17]): same system and conclusions. Quote: "the
  lack of artificial encapsulation (there is no write protection) and a
  computationally universal opcode basis set... It was previously thought
  such changes would make it highly unlikely that an ancestral replicator
  could emerge".

---

## 4. Corrections to earlier project documents

Against PLAN.md §2 table:

- **Coreworld "Programs degraded to noise": wrong.** See §2.5 above. The
  "instruction set not evolvable" half is fair: Rasmussen called redcode "by
  no means optimal", and Adami attributes the limit to "fragility under
  mutations... a direct consequence of using the Redcode scheme".
- **Tierra "everything shrank toward minimal parasites": only true under a
  size-selecting slicer.** That was the default: constant or random slice
  ([TDoc] §7).
  - Size-neutral runs grew to 400-800 ([Ray91]) and to 526 ([Std03]).
  - Slicer power > 1 gave genomes over 23,000 instructions ([Ray91]).
  - The robust finding is stasis plus no growth in *individual* complexity
    ([RayATR]; [Std03]), not shrinkage as such.
- **Amoeba "small scale": true of Amoeba-I** (about 1000 cells; secondary).
  Amoeba-IV used about 1.2 M opcodes and 2000 CPUs ([GP16]).
- **PLAN.md §3 says Tierra "needed an artificial reaper" because it had no
  second law.** Partly: Tierra did have a decay analog. Background cosmic
  rays hit the whole soup and were meant to stop immortality ([Ray91]
  p.379). What it lacked was conservation and costs.
- **PLAN.md §5.3: "Template matching is what let Tierra's organisms keep
  working after insertions and deletions."** Tierra's mutation operators
  were bit flips only. Insertions arose indirectly (§1.7). Template
  addressing is what made code relocatable and robust to size changes, so
  the spirit is right.

Against `docs/research-historic/`:

- **Review.md is accurate on all points I checked:**
  - Coreworld seven epochs and cooperative structures; its warning against
    "degraded into noise";
  - hand-coded Tierra mutualists;
  - the Standish result;
  - Amoeba 1996 (length-increasing replicator probability; shrink, then
    subroutines);
  - the Amoeba 2001 ISA and label change.
- **Review.md omissions that matter:**
  - Tierra's size trend was a slicer setting;
  - Coreworld's self-replicators did break;
  - Amoeba-IV's single-species dominance without write protection.
- **References.md links:**
  - the Ray 1991 link has a wrong file name, and the whole `tomray.me`
    domain is now parked, so all Tierra links there are dead. Use Wayback
    (keys below).
  - The Amoeba 2001 DOI is fine.

---

## 5. UNVERIFIED list

1. The content of Coreworld's "seven successive evolutionary epochs"; the
   full 1990 paper was not accessible.
2. Exact Coreworld 1990 run parameters (noise rate P_mut; garbled in the
   [RKF92] scan) and whether every 1990 run used R_opr = N.
3. Amoeba-I soup initialization, reaper rule and mutation rates. Only
   secondary sources, and they conflict (Howard 70% seed / 30% kill versus
   Adami 4% random replacement).
4. The exact Amoeba-I opcode list and the exact P_5.
5. Amoeba-II (2001) scale, run lengths and results after emergence.
6. The mechanisms of Tierra's parasite immunity (0079aab) and of its
   circumvention (0051aao); Ray does not state them.
7. Any published results from Tierra's photon (chlorophyll) slicer.
8. Taylor et al. 2016's characterization of Tierra stasis as "mostly neutral
   variation" (cited in Review.md; not re-read).
9. Ray & Hart 1998 (ALife VI) details beyond the ATR summary.
10. (inference, not stated in the docs) Freshly zeroed Tierra memory is a
    field of nop0, since opcode 0x00 = nop0 and ejected space "is set to
    zero".

---

## 6. Design implications for evo

Each point ties a verified fact to a specific evo decision.

1. **Per-organism caps make evo select for small size, as Tierra did.** In
   Tierra the size regime was a scheduler parameter:
   - constant slice → shrink to 22-30;
   - slice ∝ size → size-neutral (80 → 400-800);
   - slice ∝ size^>1 → growth to over 23,000 ([Ray91]).

   evo's "per-tick instruction cap" (§5.4) and `absorb` yield are
   per-organism, which equals Tierra's constant slice. Decide deliberately.
   Options: make the cap and absorb yield scale with owned body bytes (or
   make energy per-byte, §9 open question) so that §5.8's cost tradeoffs,
   not the scheduler, set the size optimum. Treat "cap per organism" versus
   "cap per byte" as a named ablation.
2. **Size-dependent resources must use engine truth.** Amoeba-IV cheaters
   inflated a register-derived size to get bigger slices ([GP16]). Any evo
   resource that scales with size must read ownership records, never a
   register value.
3. **Search radius.** Tierra used 200-400 cells for an 80-cell ancestor
   (about 2.5-5 genome lengths), later 5 × mean adult size, and 10,000 for
   size-neutral runs ([Ray91]; [TDoc]). evo's locality radius plays the same
   role, and parasitism depends on it. Tierra's host-parasite
   Lotka-Volterra cycles came from parasites falling outside the search
   limit when hosts were scarce ([Ray91] p.391). Suggestions:
   - start with a radius of about 4-8 × ancestor length (about 512 bytes for
     an 80-byte ancestor);
   - keep it a fixed constant, not Tierra's moving "5 × average size",
     which silently couples physics to the population.
4. **Charge for search distance. Tierra did not.** Every Tierra instruction,
   including a 10,000-cell search, cost 1 ([TDoc] §8.4). evo's "1 + 1 per 16
   bytes scanned" creates the energy analog of Tierra's error-driven reaper
   penalty on distant parasites, and needs no reaper. Record failed-search
   energy as a separate ledger line, because it is the density-dependence
   mechanism.
5. **Consider outward (bidirectional) search.** Tierra's `jmp`, `call` and
   `adr` search forward first, then alternate back and forth from a±s±1
   ([TDoc] §8.4). The ancestor's `call` to its copy procedure, and therefore
   parasitism, used outward search. evo has only `searchf`/`searchb`, so a
   parasite can only find hosts in one direction. Either add `search`
   (outward, costed by distance) or accept that parasites need hosts
   "downstream". Also copy Tierra's rules:
   - the target may be longer than the source template;
   - on failure, skip past the template;
   - result = address after the match, with template length in a register
     (Tierra used cx; evo uses C, so these match).
6. **The unassigned-opcode rule biases templates. Fix before Phase 1.**
   PLAN §5.3.2 decodes the 10 unassigned slots as `nop0`. Then 11/32 of
   random opcodes are nop0 and 1/32 are nop1. Mutations would mostly
   lengthen or corrupt templates toward all-zeros, and debris would be full
   of nop0 runs. Amoeba-IV lost emergence when NOPs drifted above 25% of
   memory ([GP16]).

   Also decide what byte 0x00 decodes to. In Tierra 0x00 = nop0, so zeroed
   memory is template material (inference). Recommendations:
   - unassigned slots and 0x00 decode to an inert op that is **not** a
     template bit (a template breaker);
   - keep nop0 and nop1 at equal frequency.
7. **`self` breaks a Tierra ecology path. Decide knowingly.** Tierra had no
   self op: organisms found their bounds by template search relative to the
   IP ([Ray91] App. C). That is why a parasite running host code copies
   itself (its own registers), and why the hyper-parasite trick works: the
   host's code re-runs self-exam and writes *its own* location into the
   parasite's registers ([Ray91] p.385).

   With evo's `self` (A = executor's body), host code that calls `self`
   copies whoever runs it. That makes every copy loop a free public service,
   removes the Tierra hyper-parasite mechanism, and bypasses PLAN §5.2's "no
   privileged access". Options: drop `self` from the Phase 1 ISA and write
   the ancestor with templates, or keep it as a named ablation. Amoeba-IV
   saw an engine convenience (MALL auto-loading CX) remove ADRB and alter
   IP-capture ecology ([GP16]).
8. **Write protection on owned bytes is load-bearing. Keep it in Phase 1.**
   - Tierra: exclusive write, open read and execute ([Ray91] p.378) → rich
     coexistence.
   - Coreworld: no membranes → seeded replicators broke within about 200
     updates from "copying on top of each other" ([RKF92]).
   - Amoeba-IV: no write protection → "never observed two radically
     different species co-existing"; the authors propose Tierra-like
     protection ([GP16]).

   evo's "stores into guarded bytes fail silently" is the Tierra membrane.
   Make overwrite and attack a costly Phase 3 op, not a default.
9. **Decide whether the IP may leave the body.** Tierra's social
   hyper-parasites and cheaters depended on execution falling off one
   creature's end into the next ([Ray91] Fig. 2). If evo allows it (implied
   by §5.2, "no privileged access"), expect sociality and cheaters. Log
   "executed foreign bytes" per organism, as Tierra's WatchExe bits did
   (EXo/EXh, [TDoc] §7).
10. **In evo, IP capture is energy theft even without `drain`.** In both
    Tierra and evo the executing CPU pays. Tierra's parasites were
    commensal: no direct harm to hosts ([Ray91] p.396). Hyper-parasites
    stole the parasite's CPU time. In evo the same move spends the victim's
    energy. So an energy-theft ecology is reachable in Phase 1 with
    `searchf`/`jmpr` alone. Instrument energy spent while executing in
    another organism's body.
11. **Lineage needs two parents.** Tierra docs: the recorded parent "is not
    necessarily the genetic parent... Hyper-parasites for example, force
    other creatures to replicate their genomes" ([TDoc] §9.1). evo's
    organism table (§7) should record:
    - the *executor* (whose divide and energy created the child);
    - the *template source* (the body the copied bytes were read from, via
      `copy` source addresses).
12. **Replace Tierra's divide guards with physics, and check that they
    hold.** Tierra hard-coded MinCellSize, MovPropThrDiv = 0.7 and
    MaxMalMult = 3 because mutants spewed empty or tiny cells or grabbed the
    whole soup ([TDoc] §7-8). evo's per-byte alloc cost and divide cost
    should make these self-limiting. Test with a hostile "alloc + divide
    without copy" mutant.

    Decide what that mutant does in evo. If alloc can claim debris without
    clearing it, then alloc+divide without copying *resurrects a dead
    genome* for the cost of the allocation (inference). That is cheap
    reproduction, or scavenging, or horizontal transfer. Choose explicitly:
    zero on alloc, require a written fraction, or allow and log it.
13. **No reaper means space becomes the fight, as Ray predicted.** Ray: "there
    is always free memory space available... predation could be selected for
    by removing the reaper" ([Ray91] p.399). Without a reaper, evo must
    guarantee turnover: an organism that stops at zero energy must lose its
    claim, and its bytes must become debris, on a known rule. Otherwise idle
    bodies lock space forever (Tierra's stated reason for the reaper:
    "rapidly fill the soup and lock up the system", [Ray91] p.379).
    Instrument "alloc failed: no space" as a key time series.
14. **Mutation-rate starting point and error threshold.**
    - Tierra's copy error was about 1 bit per 1,000-2,500 instructions moved,
      which is about 4e-4 to 1e-3 per byte ([Ray91]).
    - Best optimization came at 1 mutation per 4 generations, richest
      ecology at 1 per 8-16, and melting at 1 per 1-2 ([Ray92]).
    - Communities died when genome length grew 10× at a fixed rate ([Ray91]
      p.390). That is direct evidence for PLAN §5.8's L·μ ≈ 1 argument.

    Start evo's per-write flip probability around 1e-3 per byte for an
    80-byte ancestor (about 0.08 errors per copy), with a sweep of ×2 steps
    as in [Ray92].
15. **"Breed true" switch for ecology runs.** Tierra kept evolving with
    mutation off, because sloppy parasites recombine code, and needed
    DivSameGen to freeze it ([Ray91] p.380; [Ray92]). Add an equivalent
    config flag (divide fails unless child == parent) for Phase 2 ecology
    benchmarks.
16. **Benchmarks to reproduce (Phase 2):**
    - parasite onset within a few million instructions;
    - host-parasite Lotka-Volterra cycles;
    - keystone-parasite diversity: 8 versus 16 size classes after 30 M
      instructions ([Ray91] p.392);
    - optimization metric: energy per byte copied (Tierra: ancestor about
      10 cycles per byte, evolved 5-6, unrolled about 3.3; [Ray92];
      [Ray94a]).

    Rough budget with PLAN §5.3.4 costs (inference): a naive loop
    (copy 3 + inc A + inc B + dec + skip + jmpr) is about 8 energy per byte,
    so an 80-byte ancestor spends about 640 on copying plus about 82 on
    alloc plus 8 on divide, i.e. roughly 750 energy per offspring before
    parental investment. Size `absorb` so a producer can afford this in a
    few thousand ticks.
17. **Do not use genome length as a complexity proxy.** Standish found
    80 → 526 growth with zero complexity gain, and the ancestor scored
    highest ([Std03]). Add Standish's cheap proxy to `analysis/`: C_NV, the
    number of sites where some single-byte mutation changes behaviour,
    computed by replaying mutants in a mini-world against a fixed partner
    set.
18. **Scale is not the bottleneck; heterogeneity plus interaction is the
    bet.**
    - Tierra ran at about 3×10^3 to 2×10^4 instructions per second ([Ray91];
      [TDoc] §5). A Rust core should manage 10^8 per second or more, so
      Tierra's longest runs (2.86 × 10^9 instructions; 15 × 10^9 for
      unrolling) take seconds to minutes.
    - Ray: "a simple scaling up... would certainly not cause an evolution of
      complexity or an escape from stasis" ([RayATR]). His fix was
      spatio-temporal heterogeneity of the energy resource plus
      multicellularity, and it produced only 2 → 3 cell types ([RayATR];
      [Std03]).
    - So PLAN §5.6's heterogeneity is Ray's own bet, with a weak track
      record. Record it in `hypotheses.md` as a test, not an assumption.
19. **Coreworld's resource rule is evo's per-cell energy, and it is
    necessary.** Coreworld supplied Δr per address up to r_max < 1 and
    executed only where the local neighbourhood summed to 1 or more
    ([RKF92] §3.1). Without such a rule, Luna was taken over by a
    single-instruction replicator ([RKF92] §5). evo's per-cell pool plus
    `absorb` does this job, as long as no op or tiny loop can *both* copy
    itself *and* spawn new execution cheaply. Keep `alloc`, `divide` and a
    minimum energy transfer as the only way to create an IP.

    Weak driving left Coreworld "virtually inert", so err toward a
    generous energy income early ("fertile computational jungle",
    Δr = 0.5).
20. **Phase 4 soups need a rule that creates execution.** A seedless evo
    soup has no organisms, hence no IPs, so nothing runs. Every soup system
    had an explicit influx:
    - Coreworld injected random pointers each update (P_point = 0.05,
      [RKF92]);
    - Amoeba-IV assigned 5% of CPUs to random sequences and inserted 100
      random 1-3-op sequences per generation ([GP16]);
    - Amoeba-I reseeded random cells after each reap ([Howard96], secondary).

    Add a "spontaneous organism" rule to the plan: at low rate, wrap a random
    region as an organism with a small energy grant. It should also be
    spatially patterned (Amoeba's melted-middle and quiet-edge bands).
21. **Expect big, sloppy first replicators, then shrink, then grow.** Amoeba-I
    replicators were 10^-4 of random sequences, arose large, shrank, then
    added subroutines ([Par96a]; [Par96b]). Amoeba-IV ancestors were
    200-300 opcodes against a 15-opcode minimum, and emerged through
    propagating building blocks ([GP16]). Size the Phase 4 maximum body
    well above the minimal replicator (Amoeba-IV capped at 450), and log
    n-gram frequencies and pairwise mutual information of ops as the
    self-organization signal. The emergence time coincided with peak MI
    rise ([GP16]).
22. **The ISA is an experimental variable with measurable effect sizes.**
    Ray's four sets gave mean end sizes of 34-60% of the ancestor and
    different tempos: gradual versus punctuated ([Ray94a]). This supports
    PLAN §5.3.1's register-versus-stack comparison. Use Ray's protocol:
    same ancestor algorithm per ISA, 8 seeds, report smallest viable size,
    energy per byte copied, and tempo.
23. **Allocation placement shapes spatial structure.** Tierra's default
    placement was first or better fit anywhere in the soup; "near mother"
    was an option that needed local reaping to work ([TDoc] §7). evo's
    `alloc` "nearest to the body" is MalMode 3 by default. It will create
    kin clusters, which Tierra's sociality needed (neighbours of the same
    genotype, [Ray91] p.385), and which Stringmol found protects hosts from
    parasites (Review.md). Keep it, and make "random placement" an ablation.
24. **On the 2D torus, Ray disagreed.** [Ray94b] argued that 2D Euclidean
    memory is an unnatural import and that access-time topology (cache, RAM,
    network) is the natural one. PLAN §4 already mirrors the memory
    hierarchy through distance costs. The 2D torus is a separate bet;
    record it as a hypothesis (Phase 3 2D versus a 1D ring with the same
    heterogeneity).

---

## Sources

- [Ray91] Ray, T. S. (1991). An approach to the synthesis of life. *Artificial
  Life II*, 371-408.
- [TDoc] Tierra simulator documentation (v5.x era, soup_in dated 1995; archived
  2025-08-01).
- [Ray92] Ray, T. S. (1992). Evolution, ecology and optimization of digital
  organisms. SFI Working Paper 92-08-042 (LaTeX source).
- [Ray94a] Ray, T. S. (1994). Evolution, complexity, entropy, and artificial
  reality. *Physica D* 75:239-263 (LaTeX source).
- [Ray94b] Ray, T. S. (1994). An evolutionary approach to synthetic biology: Zen
  and the art of creating life. *Artificial Life* 1(1/2):179-209 (LaTeX
  source).
- [Ray95] Ray, T. S. A proposal to create a network-wide biodiversity reserve
  for digital organisms (about 1995; LaTeX source).
- [RayATR] Ray, T. S. Evolution of complexity: tissue differentiation in
  network Tierra. *ATR Journal* (about 1999-2000; HTML).
- [Ray99evo] Ray, T. S. (1999). Some thoughts on evolvability (HTML note).
- [Std03] Standish, R. K. (2003). Open-ended artificial evolution. *Int. J.
  Comput. Intell. Appl.* 3:167.
- [Ras90abs] Rasmussen, Knudsen, Feldberg & Hindsholm (1990). The Coreworld.
  *Physica D* 42:111-134. The abstract was read from an archived ADS page;
  the DOI is https://doi.org/10.1016/0167-2789(90)90070-6
- [RKF92] Rasmussen, S., Knudsen, C. & Feldberg, R. (1992). Dynamics of
  programmable matter. *Artificial Life II*, 211-254 (open full-text scan of
  the ALife II volume).
- [Adami98] Adami, C. (1998). *Introduction to Artificial Life*. Springer, §2.2
  and §2.4 (secondary; read from a scan; lending-library record linked).
- [Par96a] Pargellis, A. N. (1996). The spontaneous generation of digital
  "Life". *Physica D* 91:86-96. The abstract was read from an archived ADS
  page; the DOI is https://doi.org/10.1016/0167-2789(95)00268-5
- [Par96b] Pargellis, A. N. (1996). The evolution of self-replicating computer
  organisms. *Physica D* 98:111-127 (abstract from archived ScienceDirect).
- [Par01] Pargellis, A. N. (2001). Digital life behavior in the Amoeba world.
  *Artificial Life* 7(1):63-75 (PubMed abstract).
- [Par03] Pargellis, A. N. (2003). Self-organizing genetic codes and the
  emergence of digital life. *Complexity* 8(4):69-78 (Crossref abstract).
- [GP16] Greenbaum, B. & Pargellis, A. N. (2016). Digital replicators emerge
  from a self-organizing prebiotic world. *ALife XV*, 60-67 (open-access
  proceedings, DOI below; text read from an archive.org copy of the
  proceedings).
- [GP17] Greenbaum, B. & Pargellis, A. N. (2017). Self-replicators emerge from a
  self-organizing prebiotic computer world. *Artificial Life* 23(3):318-342
  (PubMed abstract).
- [Howard96] Howard, T. (1996). Soup Opera (Artificial life with Amoeba).
  *Personal Computer World*, August 1996 (secondary).
- [WPdo] Wikipedia, "Digital organism" (the likely origin of the Coreworld
  "brittle, failed" shorthand).

[Ray91]: https://web.archive.org/web/20250514135407/https://tomray.me/pubs/alife2/Ray1991AnApproachToTheSynthesisOfLife.pdf
[TDoc]: https://web.archive.org/web/20250801144228/http://tomray.me/pubs/doc/index.html
[Ray92]: https://web.archive.org/web/2024/https://tomray.me/pubs/tierra/tierra.tex
[Ray94a]: https://web.archive.org/web/2024/https://tomray.me/pubs/oji/ojihtml.tex
[Ray94b]: https://web.archive.org/web/2024/https://tomray.me/pubs/zen/zen.tex
[Ray95]: https://web.archive.org/web/2024/https://tomray.me/pubs/reserves/reserves.tex
[RayATR]: https://web.archive.org/web/2024/https://tomray.me/pubs/atrjournal/
[Ray99evo]: https://web.archive.org/web/2024/https://tomray.me/pubs/evolvability/
[Std03]: https://arxiv.org/abs/nlin/0210027
[Ras90abs]: https://web.archive.org/web/20231202101659/https://ui.adsabs.harvard.edu/abs/1990PhyD...42..111R/abstract
[RKF92]: https://archive.org/details/1992-langton-artificiallife-2
[Adami98]: https://archive.org/details/introductiontoar0000adam
[Par96a]: https://web.archive.org/web/20241212055606/https://ui.adsabs.harvard.edu/abs/1996PhyD...91...86P/abstract
[Par96b]: https://web.archive.org/web/20240415120545/https://www.sciencedirect.com/science/article/abs/pii/0167278996000899
[Par01]: https://pubmed.ncbi.nlm.nih.gov/11461689/
[Par03]: https://doi.org/10.1002/cplx.10095
[GP16]: https://doi.org/10.7551/978-0-262-33936-0-ch016
[GP17]: https://pubmed.ncbi.nlm.nih.gov/28786722/
[Howard96]: https://www.cs.man.ac.uk/~toby/writing/PCW/life.htm
[WPdo]: https://en.wikipedia.org/wiki/Digital_organism
