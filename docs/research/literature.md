# Literature review: prior digital-evolution systems

Compiled 2026-09-30 for evo (PLAN.md §11) from the four verified note files in
`docs/research/notes/`. It does not change PLAN.md; §5 ranks the changes the
literature argues for against PLAN.md as it stood on 2026-09-30.

## 1. Scope and method

This review covers the systems named in PLAN.md §2 and §11, the systems the first pass missed (Cosmos, Nanopond, Ackley's Movable Feast Machine, Squirm3, Evoloops, AlChemy, the 2026 BFF follow-ups), the main open-endedness measures, and error-threshold theory. It is synthesized from four notes in `docs/research/notes/` (`tierra-coreworld-amoeba.md`, `avida-stringmol.md`, `bff-and-recent.md`, `oee-metrics-and-other-systems.md`), written from primary sources wherever reachable: full papers and theses, Avida, Stringmol, cubff and Nanopond source at named commits, and Wayback copies of Ray's papers (`tomray.me` is now parked). The notes hold the per-fact citations and quotes; this document gives the main URL per claim. **UNVERIFIED** and "(inference)" tags are carried over exactly as the notes have them. `docs/research-historic/` holds an earlier pass by another AI (Codex, per PLAN §11). The notes found it mostly accurate but with three substantive errors: the Coreworld shorthand "programs degraded to noise" (carried in PLAN.md §2 until 2026-09-30; Review.md itself cautioned against it, but missed that the seeded replicators really did break); two DOIs that do not resolve, for the 2021 Stringmol parasitism paper (correct: *R. Soc. Open Sci.* 8:210441, [10.1098/rsos.210441](https://doi.org/10.1098/rsos.210441)) and for Ofria & Wilke 2004 (correct: *Artificial Life* 10(2):191-229, [10.1162/106454604773563612](https://doi.org/10.1162/106454604773563612)); and an overstated Stringmol 2015 conservation-of-matter result, which had no non-conserving control. Smaller corrections appear in place.

## 2. Systems

### 2.1 Coreworld (Rasmussen, Knudsen, Feldberg & Hindsholm 1990)

Sources: the paywalled paper's abstract ([archived](https://web.archive.org/web/20231202101659/https://ui.adsabs.harvard.edu/abs/1990PhyD...42..111R/abstract)) and the group's *Artificial Life II* chapter ([Rasmussen, Knudsen & Feldberg 1992](https://archive.org/details/1992-langton-artificiallife-2)).

**Substrate.** A one-dimensional cyclic core of redcode (Dewdney's 10 Core War opcodes, 4 relative addressing modes), run by up to L execution pointers. `SPL` creates a pointer; `DAT` or a resource shortage kills one. Reads, writes and jumps stay within an operation radius, and each executed `MOV` mutates the moved word, with probability P_mut, into a random legal instruction.

**Energy, space, death.** Each address holds a resource level below one execution, refilled by Δr per update up to r_max; an instruction runs only if its neighbourhood sums to one execution. The rule was added to stop pointers piling up and "to enhance cooperative interactions". Random pointers are injected "to assure that the system is always active". There is no ownership.

**What emerged.** Seeded self-replicators "typically start malfunctioning after 200 iterations due to computational noise and copying on top of each other". Instead, *cooperative structures* emerged: sets of instructions that copy each other or pass pointers and "reproduce as a whole", such as MOV-SPL structures lasting over 100,000 iterations and more robust jump cores. The abstract reports "seven successive evolutionary epochs". Without a resource rule, the simpler Luna machine was flooded by one self-sufficient `COPY` instruction.

**Plateau.** No individual program with a fixed genotype ever emerged ([Adami 1998](https://archive.org/details/introductiontoar0000adam), secondary). The authors blamed redcode ("by no means optimal for our purpose") but warned that simplifying the set "below a certain level of complexity inhibits the emergence of higher-order cooperative structures". Weak driving was "virtually inert"; the productive regime was a "fertile computational jungle". **UNVERIFIED:** the content of the seven epochs, and P_mut.

| Parameter | Value |
|---|---|
| Core N; pointers L | 3,584 (180 runs from 112 to 3,584); 220 |
| Δr; r_max; R_res; R_opr | 0.5; 0.5; 3; 800 or N |
| Pointer injection P_point | 0.05 |
| Outcome frequency | fixed-point cores in a little over half of runs; viable MOV-SPL in one in four |

### 2.2 Tierra (Ray, 1990 onward)

Sources: [Ray 1991](https://web.archive.org/web/20250514135407/https://tomray.me/pubs/alife2/Ray1991AnApproachToTheSynthesisOfLife.pdf), the [v5 documentation](https://web.archive.org/web/20250801144228/http://tomray.me/pubs/doc/index.html) and Ray's later papers, all via the Wayback Machine.

**Substrate.** A shared soup. Each creature has its own CPU (two address and two numeric registers, a 10-word stack, an IP) running 32 operand-free five-bit opcodes. Addressing is by complementary nop templates, searched outward up to a limit: 200-400 cells in 1991, 10,000 in size-neutral runs, later 5 × the mean adult size. Searches ignore ownership, and every instruction costs one unit, even a long failed search.

**Energy, space, death.** CPU time comes from a slicer with slice proportional to size raised to a power: a constant slice "selects for small creatures", power 1 is size-neutral, a power above 1 favours large ones. The v5 sample configuration's random 0-50 slice ignores size, so **the default selects for small size**. Each creature can write only its own block, but "read and execute privileges are not" protected. Hard guards stop mutants spewing tiny or empty cells. A reaper kills from the top of a queue once memory is about 80% full; errors move a creature up, which Ray credited for host-parasite density dependence. Mutation is bit flips from "cosmic rays" (meant to prevent immortality), copy errors and off-by-one "flaws"; sloppy parasites produced insertions, so evolution continued at zero mutation.

**What emerged.** From the 80-instruction ancestor: parasites within a few million instructions (a one-bit change that borrows a neighbour's copy loop); immunity and its circumvention (mechanisms **UNVERIFIED**); hyper-parasites that capture parasites' CPUs; social creatures and cheaters that rely on execution running from one creature into the next; loop unrolling; and optimisation to 22 instructions and 146 cycles per copy, against the ancestor's 839. With mutation off there were Lotka-Volterra cycles, and a keystone parasite kept 16 size classes where 8 survived without it. Symbiosis was hand-made.

**Plateau.** The size trend was a scheduler setting ([Ray 1992](https://web.archive.org/web/2024/https://tomray.me/pubs/tierra/tierra.tex)). A constant slice shrank genomes to 22-30; size-neutral runs held in the 80s for up to 1.44 × 10^9 instructions, then jumped to 400-800; a power above 1 reached the upper hundreds and once exceeded 23,000. Ray's later verdict was permanent stasis, in which "the individual replicators generally do not increase in complexity" ([Ray, ATR](https://web.archive.org/web/2024/https://tomray.me/pubs/atrjournal/)). Standish found lengths growing from 80 to 526 with "no sign of complexity increase", and the ancestor scoring highest ([Standish 2003](https://arxiv.org/abs/nlin/0210027)). Taylor et al. call the stasis neutral variation ([2016](https://www.tim-taylor.com/papers/taylor2016openended.pdf)); the Tierra note marks this UNVERIFIED, the metrics note quotes it. Ray's diagnosis: a single node rewards only fast copying ("There is just no need to do anything more complicated than copy yourself quickly", [Ray 1995](https://web.archive.org/web/2024/https://tomray.me/pubs/reserves/reserves.tex)), and scaling up alone "would certainly not" help; his heterogeneous network Tierra took cell types from 2 to 3. The instruction set mattered: one ancestor adapted to four sets ended at 34-60% of its size, with different tempos ([Ray 1994a](https://web.archive.org/web/2024/https://tomray.me/pubs/oji/ojihtml.tex)). Ray also doubted that 2D Euclidean memory is natural ([Ray 1994b](https://web.archive.org/web/2024/https://tomray.me/pubs/zen/zen.tex)).

| Quantity | Value |
|---|---|
| Soup | 60,000 cells (1991); 50,000 (v5) |
| Ancestor | 80 instructions, 48 of them nops; 839 cycles for the first copy, 813 after (about 10 per instruction copied) |
| Copy error | about 1 bit per 1,000-2,500 instructions moved; v5: about 1 in 8 cells per generation |
| Rate scan | 1 mutation per 1-2 generations "melts"; 1 per 4 optimises fastest; 1 per 8-16 gives the richest coexistence |
| Runs | 2.86 × 10^9 instructions (size-neutral); 15 × 10^9 (unrolling); 1,180 size classes in a 2.56 × 10^9 run |

### 2.3 Avida (Ofria, Adami and colleagues)

Source at commit `47f13dad` ([devosoft/avida](https://github.com/devosoft/avida)); platform chapter ([Ofria, Bryson & Wilke 2009](https://www.cse.msu.edu/~ofria/pubs/2009AvidaIntro.pdf)).

**Substrate.** One organism per cell of a 60 × 60 torus, each with 3 registers, 2 stacks and 4 heads over a circular genome; organisms cannot normally read or write each other's memory. The 26-instruction set uses nops both as labels and as operand modifiers (a following nop selects the register and is consumed). `h-search` searches from the genome start, may match inside a longer nop run, and with an empty label marks the next instruction; `h-copy` advances both heads; `get-head` reads the IP. The default ancestor is 100 instructions, 85 of them filler.

**Energy, space, death.** CPU share follows *merit*. Base merit is proportional to the smaller of executed and copied length, so longer genomes also run faster: Avida removes Tierra's shrink pressure by design. Rewarded tasks multiply merit (×2 for NOT up to ×32 for EQU). Total cycles are fixed, so nobody starves. A birth kills the occupant of the target cell, and an age limit of 20 × length instructions exists because otherwise a population can "lose all ability to self-replicate, but persist since organisms have no means by which to be purged". An optional energy model ([Beckmann 2010](https://d.lib.msu.edu/etd/17557)) pays energy only for tasks and kills at zero.

**What emerged.** Parasites are an engine feature: `inject` places a thread in a host that shares a task. With them, EQU evolved in 17 of 50 host populations and in none without ([Zaman et al. 2014](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1002023)); resistance was task-switching, not defence written in code. Under the energy model, energy-limited populations never filled the grid and evolved slow gestation (about 2,000 instructions), falling to about 300 as space became limiting. Richer multi-nop modifiers helped in 6 of 7 environments while extra registers did little ([Bryson & Ofria 2013](https://arxiv.org/abs/1309.0719)).

**Plateau.** In the MODES study ([Dolson et al. 2019](https://cse.msu.edu/~dolsonem/pdfs/modes_paper.pdf)), task-free complexity showed "a rapid rise... followed by a decrease and leveling out", attributed to "strong pressure... to become a more efficient self-replicator"; with the Logic-9 tasks it kept rising. Ecology stayed low everywhere. The authors conclude that unbounded complexity growth needs an environment where "there is always new information to be integrated into the genome." **The notes disagree on size:** the Avida note reads the default merit rule as roughly size-neutral; the metrics note quotes Avida papers reporting "shrinking genome size" ([Adami, Ofria & Collier 2000](https://pmc.ncbi.nlm.nih.gov/articles/PMC18257/)) and "a pressure to shrink the genome" ([Ofria, Adami & Collier 2003](https://arxiv.org/abs/quant-ph/0301075)). Their merit settings are not recorded, so this is probably configuration (unverified).

| Quantity | Value |
|---|---|
| Copy mutation | 0.0075 per instruction, plus 0.05 insertion and 0.05 deletion per divide: 0.85 per genome |
| Divide rules | at least 10 instructions; at least 50% executed and 50% copied; failure ignored, not fatal |
| Zaman 2014 | 0.25 (host) and 0.5 (parasite) mutations per genome; 50 runs of 500,000 updates |

### 2.4 Amoeba (Pargellis 1996-2003; Greenbaum & Pargellis 2016-2017)

Sources: abstracts of the paywalled early papers, the first-hand history in [Greenbaum & Pargellis 2016](https://doi.org/10.7551/978-0-262-33936-0-ch016), and marked secondary sources.

| Version | Instruction set | Addressing | Note |
|---|---|---|---|
| I (1996) | 16 ops, not universal | opcode complements; "impossible to move to arbitrary positions in memory" | replicators in about 10^-4 of random sequences |
| II (2001) | 32 ops, universal | 64 random address labels per instruction | results UNVERIFIED |
| III (2003) | evolving codon-to-opcode map | opcode::address pairs | emergence rate doubled |
| IV (2016) | 25 ops, Avida-style modifiers | Tierra templates | about 1.2 M opcodes, 2,000 CPUs |

**Amoeba-I.** Large, inefficient replicators arose from random sequences, with a probability that rises with length ([Pargellis 1996b](https://web.archive.org/web/20240415120545/https://www.sciencedirect.com/science/article/abs/pii/0167278996000899)); Adami argues it rises *because* the set is not universal. The minimal replicator is 5 instructions (secondary). Replicators shrank, then added subroutines, and hosts, parasites and colonies appeared ([Pargellis 1996a](https://web.archive.org/web/20241212055606/https://ui.adsabs.harvard.edu/abs/1996PhyD...91...86P/abstract)). **UNVERIFIED:** scale, seeding and reaper, where the secondary sources conflict (Howard: 70% seeded, 30% reaped; Adami: 4% replaced by random code). Amoeba-II decoupled what an instruction does from where it can be reached from ([Pargellis 2001](https://pubmed.ncbi.nlm.nih.gov/11461689/)).

**Amoeba-IV.** *Substrate:* 500 bands of prime length 2,399. *Energy, space, death:* no energy; slice proportional to size, clamped to 6-100 operations; each generation 5% of CPUs get random code and 100 random short sequences are inserted, mostly mid-memory; **no write protection**. *Emerged:* the opcode distribution narrows to 15-20 effective opcodes in about 50,000 generations, building blocks such as the endless propagator {CALL, COPY, INCA, RETN} spread, and a proto-replicator appears "usually within a million generations" in 25 of 49 runs, then sheds code and unrolls its loop. *Plateau:* "We have never observed two radically different species co-existing. Viruses occur, but are quickly eliminated"; the authors suggest Tierra-like write protection. Emergence probability falls after about 10^6 generations as nops pass 25% of memory by 10^7. Cheaters inflated the register value that set their slice, and `MALL` auto-loading the child's address made `ADRB` disappear.

| Amoeba-IV | Value |
|---|---|
| Mutation | 0.005 per copy; per divide 0.02 insertion, 0.02 deletion, 0.06 substitution |
| Divide-mutation window | above 0.20 randomises; below 0.05 "NOPs dominate" |
| Sizes | minimal replicator about 15 opcodes; first replicators 200-300; cap 450 |

### 2.5 Cosmos (Taylor 1999)

From Taylor's [thesis](http://archive.tim-taylor.com/papers/thesis/html/main.html).

**Substrate.** Several thousand programs with 62 six-bit instructions and gene regulation; a cell reads, writes and executes only inside itself. **Energy, space, death.** One energy token per instruction. CPU per slice is N = c·L^p with p = 1 by default (formula rebuilt from text, **UNVERIFIED**). Each sweep drops 30 tokens on every square of a 40 × 40 torus, and under the default "shared" scheme cells collect from their neighbours' stores. Death is by starvation, plus a cull of the poorest 10% at 2,500 cells. Mutation is bit flips, on average one per 10^6 bits.

| Condition | Result |
|---|---|
| Standard | "Steady microevolution, with no spectacular macroevolutionary innovation" (Bedau class 2); genomes 348 to 390 bits, mostly more `et_collect` in the copy loop; no parasites |
| Re-runs | 5 of 9 fell to class 1: a genome-doubling "selfish DNA" mutant, favoured by length-scaled CPU and shared collection, locked the grid into a checkerboard of about 400 organisms |
| Fixed 10 instructions per slice | all 9 runs stayed class 2 |
| Private energy collection | evolution continued, more slowly |
| High / low mutation | all class 1 / a junk-adding "cancer" mutant caused extinctions |
| Energy gradient 1-59 / 26-34 tokens | several genome lengths coexisted / no effect |
| Neighbours' code readable | no parasites: none was a single mutation from the ancestor |
| Seed-only differences | each run differed significantly from at least a third of the others |

**Plateau.** Both available adaptations (more `et_collect`, less redundant code) run out, with "little evidence for other innovations". Taylor faulted Tierra-like systems for predefined organism structure, restricted interactions, no real competition for energy, and reproduction written into programs rather than physics; he recommended embedded individuals and changing environments, and later called Tierra's genotype-to-phenotype map "extrinsic and trivial" ([Taylor 2019](https://arxiv.org/abs/1806.01883)).

### 2.6 Nanopond (Ierymenko)

From [nanopond.c](https://raw.githubusercontent.com/adamierymenko/nanopond/master/nanopond.c). **Substrate:** a toroidal grid of cells, each a genome of 4-bit codons from a 16-op Brainfuck-like set. **Energy, space, death:** every 100 ticks one random cell receives energy *and* a fully random genome; each instruction costs one unit. Output overwrites the faced neighbour only if it has energy and access succeeds, so energy acts as territory. Access is a "logo" check: harmful actions succeed with probability (d+1)/16, d being the Hamming distance between the target's logo and the actor's register, and a failed `KILL` costs the attacker (the code contradicts its comments). No reaper; cells die by overwrite, kill or reseeding. **Emerged:** "random genesis" of replicators; the author says evolution "doesn't get 'stuck'" but never ran month-long tests. A third party reports copy-then-kill dominance after 3 × 10^9 iterations ([Hacker News](https://news.ycombinator.com/item?id=2723001), not primary). No stated limitations were found (**UNVERIFIED** that none exist). Scale (v2.0): 800 × 600 cells of up to 1,024 codons; mutation about 1.16 × 10^-6 per executed instruction.

### 2.7 Stringmol (Hickinbotham, Stepney and colleagues, York)

Sources: the [specification](https://www.cs.york.ac.uk/library/reports/2010/YCS/458/YCS-2010-458.pdf) and the [source](https://github.com/uoy-research/stringmol) at commit `15dad84`.

**Substrate.** An artificial chemistry: strings over 33 symbols (26 template no-ops, 7 function codes) that execute only while bound in pairs. Binding is Smith-Waterman alignment against the partner's complement, with probability 0 for an aligned length l ≤ 2 and min(score, l - 1.124)/(l - 1.124) otherwise; the string whose bind site lies further from its start executes. There are no registers, and template matching is probabilistic.

**Energy, space, death.** The well-mixed spec charges one energy unit per binding attempt or instruction; the 2021/2024 spatial runs effectively did not limit energy (Review.md generalised past this). Molecules decay at a constant rate. The spec's decay lessons: decay only while unbound selected endless reactions, after which "No further evolution of the system can be observed"; length-dependent decay gave long molecules "a huge evolutionary advantage"; only constant decay in every state kept species turning over.

**What emerged, and the plateaus.**

- *Well-mixed:* no trial self-maintained indefinitely; parasites that the replicase copies faster than it copies itself killed them.
- *Conservation of matter* ([2015](https://doi.org/10.7551/978-0-262-33027-5-ch024)): per-symbol counts fixed, mutation only from scarcity. Species count peaked at 1,700 copies per opcode (error catastrophe), QNN activity at 2,400; GA-tuned mixes reached median QNN about 300 against under 100. There was no non-conserving control, and the mutation mechanism changed too.
- *Universal constructor* ([2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5454285/)): all 500 runs died, none from parasites: "bureaucratic death", a cascade of worsening expressors. Mutation and decay rates "are not under the control of systems designed in stringmol".
- *Spatial parasitism* ([2021](https://eprints.whiterose.ac.uk/id/eprint/176868/1/rsos.210441.pdf)): 8 of 20 runs survived, evolving defences: binding through self-matching function codes, so parasites stick to each other; "self-scan", a fixed cost "reducing the benefit of evolving to be short" that also roughly doubles point mutation; and toggle checks that hold non-self partners "in an unproductive reaction". Parasites "continually arise from mutated replicators", defences vanish without them, and there is "selective advantage in actively wasting resources".
- *Measurement* ([2024](https://www-users.york.ac.uk/~ss44/bib/ss/nonstd/artl23.pdf)): seed layout decided survival; all 12 runs seeded with 500 scattered pairs died. The highest cumulative QNN (2.874) was mostly churn, the lowest (0.972) the most novel run. The 2021 and 2024 papers describe the treatments differently; the repository config supports 2024.

| Quantity | Value |
|---|---|
| Decay | 1/65² ≈ 2.37 × 10^-4 per step (spec); 0.24 × 10^-4 (UCA) |
| Copy mutation | 10^-5 per symbol (spec); 0.5 × 10^-6 (UCA); 2 × 10^-4 in the repository spatial config (**UNVERIFIED** as used) |
| Sizes | 65-symbol spatial seed; UCA genome about 3,656 opcodes |
| Runs | well-mixed: 1,000 trials, modal extinction 750,000 steps; UCA: mean extinction 6,572,488 steps; spatial: 20 runs of 2 × 10^6 steps on 12,500 cells |

### 2.8 BFF / *Computational Life*, Knierim 2026, Cicala 2026

**Substrate.** [Agüera y Arcas et al. 2024](https://arxiv.org/abs/2406.19108), still a preprint, use BFF: Brainfuck with I/O replaced by copies between two heads on the code's own tape. Ten byte values are instructions, byte 0 ends loops, and all others are no-ops. In the paper's `bff_noheads` variant the heads and the IP all start at byte 0 ([cubff](https://github.com/paradigms-of-intelligence/cubff)); later variants add an auto-advancing copy.

**Energy, space, death.** Each epoch, 2^17 tapes of 64 bytes are paired at random and concatenated; each byte is replaced by a random byte with probability 2^-12; the pair runs for up to 8,192 free steps and is split back. Nothing is created or destroyed; a tape "dies" only by being overwritten. There is no energy, ownership or protection.

**What emerged.** Replicators take over within 16k epochs in 40% of runs, 44% at zero mutation and about 50% with fixed pairing and no noise, so they arise "mostly due to self-modification and interaction". A bounded 2D grid slowed takeover and let variants coexist. Forth soups almost always transitioned (1-byte replicator); Z80 grids went from `PUSH` to `LDIR` replicators and "symbiotic ecosystems". **SUBLEQ never produced a replicator** "even following billions of executions"; its smallest is 60 bytes (25 for RSUBLEQ4), against about 1-10 where emergence worked. The authors call replicator length critical "but... not the sole factor". On one long shared tape, the setup closest to evo, identical head starts gave only trivial non-looping replicators, and looping ones needed a head offset "somewhat larger than 8"; Forth needed a second instruction set and grew "a fairly long non-functional head" as a landing pad; 8080 only gave 2-byte non-looping copies.

**Plateau.** Unmeasured. Post-emergence complexity is "anecdotal", and no open-endedness statistic is reported.

**Knierim et al. 2026** ([arXiv 2607.01483](https://arxiv.org/abs/2607.01483)), by the same group, separated *discovery* from *takeover*. First discovery took about 2.5 × 10^6 interactions (soup size **UNVERIFIED**). Freshly sampled programs needed 2.9 × 10^7 tries per replicator from uniform bytes, 1.7 × 10^6 from the soup's own byte distribution, 4.5 × 10^5 from a half-operator mix (CUST) and 9.4 × 10^4 with the heads 64 apart (CUST64). A random walk from uniform bytes at BFF-like rates was 40-190× *slower* than the soup. So the soup is not an unusually strong search operator, and much of its edge is shifting bytes toward operators; Review.md's "at least as easily" holds only for the tuned mixes. Blocking "mergers" (new multi-byte copies) slowed discovery but prevented takeover. Who claimed that merger caps stop emergence is **UNVERIFIED**.

**Cicala et al. 2026** ([arXiv 2607.09211](https://arxiv.org/abs/2607.09211)) is the only recent emergence study with a computation cost, and a mild one: Z80 programs that compute their niche's polynomial interact more often (0.3 to 1.0), discounted by the steps used. That biases a task; it is not per-instruction energy that can kill. Replicators kept evolving after emergence: whole-tape Load-Push copiers gave way to compact `LDIR` copiers that leave room for task code, copy robustness ranking `LDIR` above `LDD` above Load-Push; without task pressure the transition stalled for 10^7 epochs. (Parameter table garbled: **UNVERIFIED** beyond the text.)

| Quantity | Value |
|---|---|
| Soup | 2^17 tapes of 64 bytes; 8,192 free steps per interaction |
| Mutation | byte replacement at 2^-12 per byte per interaction |
| Fraction *not* transitioning in 16k epochs | 0.60 at 0.024%; 0.42 at 0.1%; 0.62 at 0.5%; 0.94 at 1% (whether the rise above 0.1% means fewer replicators or a noise-depressed metric is **UNVERIFIED**) |
| Cicala | 2^19 Z80 programs of 32 bytes in 32 niches of 128 × 128 |

### 2.9 Ackley's Movable Feast Machine

Sources: [HotOS 2011](https://www.cs.unm.edu/~ackley/papers/hotos-11.pdf), [ALIFE 14](https://www.cs.unm.edu/~ackley/papers/ackley-small-alife14.pdf). **Substrate:** a 2D grid of tiles whose sites each hold one fixed-width atom of a hand-written element type. Events run in exclusively held windows of radius 4 (41 sites; derived, **UNVERIFIED** directly), with non-overlapping windows in parallel. Element code lives outside the grid, so the physics cannot evolve: MFM is prior art for robust spatial physics, not for evolved replicators. **Energy, space, death:** computation is free ("A cycle saved is a cycle wasted", [ECAL 2015](https://www.cs.unm.edu/~ackley/papers/ecal2015-author-copy.pdf)). DReg atoms randomly delete neighbours and create `Res`, so anything that reproduces only from `Res` is density-regulated with no reaper. **What it showed:** designed structures recovered from "resetting two-thirds of the grid sites" ([AAAI 2016](https://www.cs.unm.edu/~ackley/papers/ackley-aaai16-smpt.pdf)). Ackley argues that determinism does not scale, that local rules must not read global data such as "the current global population size", and that periodic boundaries are acceptable in two scalable dimensions. The C211 protocell and T2 Tile are **UNVERIFIED** beyond abstracts.

### 2.10 Others, briefly

**Squirm3** ([Hutton 2002](https://faculty.cc.gatech.edu/~turk/bio_sim/articles/hutton_rep_molecules.pdf), [2007](https://web.archive.org/web/20210117085336id_/http://www.sq3.org.uk/papers/cells2007.pdf)): an atom chemistry with replication "by design", no energy, conserved matter, and floods that clear half the world. Replicators emerged from random soup with cosmic rays on (first at about 400,000 iterations on 100 × 100), but "The only selection pressures encountered have been towards shorter molecules". Shared enzymes bred parasites and global extinction (2003, **UNVERIFIED**, via the 2007 paper); membrane cells (2007) reached 145 species, and a new-food gene let a longer genome win. Limit: new enzymes need about 14 bases, but "unused bases tend to be gradually removed".

**Evoloops** ([Sayama 1999](https://pubmed.ncbi.nlm.nih.gov/10829086/); [Salzberg et al. 2004](https://bingdev.binghamton.edu/sayama/papers/alife9-evoloop.pdf)): self-replicating CA loops that vary only through collisions; a dissolver state erases loops jammed by overcrowding, a reaper built into the physics. Loops evolved "toward the smallest ones"; with a size floor of 15, dominance kept shifting for over 6 × 10^6 iterations (7,106 species). The 25-year review finds that spatial systems end in "dominance by one or a few most successful species", and that dynamic environments "may not work for indefinitely long terms" ([Sayama & Nehaniv 2024](https://arxiv.org/abs/2402.03961)). How the "hostile environments" were built is **UNVERIFIED**.

**AlChemy** ([Fontana & Buss 1994](https://sfi-edu.s3.amazonaws.com/sfi-edu/production/uploads/sfi-com/dev/uploads/filer/f2/8b/f28b8075-4e73-4696-989e-1cfbe06b2dc8/93-09-055.pdf)): λ-calculus in a flow reactor of 1,000 objects, each product displacing a random object. Copiers take over because "objects that replicate eliminate objects that do not"; forbidding copying, or accepting copies only 75% of the time, allows self-maintaining organizations. The 2024 revisit ([Mathis et al.](https://arxiv.org/abs/2408.12137)) found long copy-allowed runs can still organize (about 380 expressions in one run), robust to 90% replacement but rarely combining, and generator-dependent. Its venue is *Chaos* per the BFF note ([PubMed](https://pubmed.ncbi.nlm.nih.gov/39345193)) and **UNVERIFIED** per the metrics note.

**Geb** (Channon): the notes cover only its measurement record. It is the one artificial system to pass step 3 of Channon's test (§3.2), yet its maximum complexity grew only as about 10.17 + 1.87·log₂(size), so 6.4 × 10^15 agents would give about 53 active genes ([Channon 2024](http://www.channon.net/alastair/papers/channon-ArtificialLifeJournal2024a-authorsFinalVersion.pdf)). Review.md's description of Geb as embodied neural-controlled agents was not re-verified.

## 3. Measurement

### 3.1 Bedau-Packard activity statistics

The 1992 version ([Bedau & Packard](https://people.reed.edu/~mab/publications/papers/alife2.pdf)) counts use: each gene's usage counter rises when the gene is used, is inherited, and resets on mutation. With N(t,u) the fraction of genes at usage u and P(t,u) = Σ_{u′≥u} N(t,u′), activity is A(t) = -∂P(t,u)/∂u at a threshold u₀.

The standard 1997/98 version ([Bedau, Snyder & Packard 1998](https://people.reed.edu/~mab/publications/papers/alife6.pdf)) counts existence. Component i (allele, genotype or family) has Δᵢ(t) = 1 while it exists; aᵢ(t) = Σ_{τ≤t} Δᵢ(τ) while it exists, else 0; D(t) = #{i : aᵢ(t) > 0}; A_cum = Σᵢ aᵢ; Ā_cum = A_cum/D; and A_new(t) = (1/D(t))·Σ_{a₀ ≤ aᵢ ≤ a₁} aᵢ(t). The strip comes from a neutral shadow with the same birth and death counts and mutation rate but random parents and victims: a₀, a₁ = a* ∓ 0.05·(a_max - a*), where a* is where the real and shadow activity distributions cross (rebuilt from garbled text, **UNVERIFIED**). A series is unbounded iff lim sup f(t)/t > 0; with finite data, fit bounded and unbounded models rather than eyeballing. Classes: 1 none; 2 "uncreative" (unbounded Ā_cum, zero A_new; attribution **UNVERIFIED**); 3 bounded; 4a-4c unbounded in D, in Ā_cum, or both. Echo reached only classes 1-2; Evita and Tierra drifted neutrally. Weaknesses: components are fixed in advance, shadows drift, the mean is fragile (use the median), and stabilising selection reads as activity. *Raw logs:* births with the child's genotype, and deaths, which give exact existence intervals; shadow inputs per timestep (Evita's shadow needed only mutations and reproductions per timestep).

### 3.2 Channon 2024

[Channon 2024](http://www.channon.net/alastair/papers/channon-ArtificialLifeJournal2024a-authorsFinalVersion.pdf) resets the shadow to the real population at each snapshot, stopping drift. Δᵢᴺ = Δᵢᴿ - Δᵢˢ (real presence minus shadow presence); aᵢᴺ(t) = Σ_{τ≤t} Δᵢᴺ(τ) while i exists in the real run; A_cumᴺ = Σ aᵢᴺ, reported as a total, a mean over Dᴿ and a median; A_newᴺ = (1/Dᴿ)·Σ_{i new} aᵢᴺ, where a component is new once aᵢᴺ exceeds "the absolute value of the most negative component-normalized evolutionary activity". The five steps: (1) stop if A_cum is bounded (only the biosphere, Geb and Pichler's ecosystem pass); (2) compute normalised statistics; (3) require positive A_newᴺ with unbounded total and median, backed by phenotypes (only Geb has passed); (4) show rising bounds as memory and population limits are raised; (5) beat logarithmic scaling. Channon rejects persistence filters as a substitute for the shadow, and for Tierra-like systems suggests the code between consecutive nop runs as a component: evo's template-delimited segments. *Raw logs:* a census at each snapshot, births and deaths between snapshots, and the per-birth probability of a new genotype; the shadow can run offline.

### 3.3 MODES

[Dolson et al. 2019](https://cse.msu.edu/~dolsonem/pdfs/modes_paper.pdf) count only *persistent* components, those with living descendants t generations later (t about equal to population size worked in Avida). Components are reduced to meaningful sites, found by *replacing* each site with a null instruction (not deleting it, since spacing can carry information) and keeping sites whose loss lowers fitness or lifetime reproductive output. With F and F′ the persistent sets now and at the previous point, and S every component ever seen: change = Σ_{c∈F} [c ∉ F′]; novelty = Σ_{c∈F} [c ∉ S]; complexity = max over c ∈ F of meaningful sites; ecology = -Σ_{c∈F} p(c)·log₂ p(c). MODES cannot separate class 1 from 2, or 3 from 4b. *Raw logs:* parent ids with generation depth, the genome store and the census, plus a single-genome test harness for knockouts.

### 3.4 QNN

From the authors' R code ([franticspider/qnn](https://github.com/franticspider/qnn)): pᵢ(t) = nᵢ(t)/N(t); qᵢ(t) = (max(0, pᵢ(t) - pᵢ(t-1)))²; QNN(t) = Σᵢ qᵢ(t), summed over the run. It rewards rapid rises in abundance, which drift rarely produces, so it needs no neutral model. Its users concluded that "System-specific measures are essential", "Behavioral measures are key", and that a single quantitative measure is "a dead end". *Raw logs:* rows of (time, species, count).

Also cheap to support from snapshots and the harness: *high-order entropy* (byte entropy minus brotli-q2 bits per byte; a takeover detector, not an open-endedness test; bits per byte per the BFF note's reading of the code, units **UNVERIFIED** per the metrics note); Standish's *C_NV* (sites where some mutation changes the phenotype); and ASAL's *historical nearest-neighbour novelty* ([Kumar et al. 2024](https://arxiv.org/abs/2412.17799)) over a genome or behaviour embedding, not CLIP on images.

## 4. Cross-cutting findings

### 4.1 Size selection is set by the scheduler or energy rule, not by biology

Genome size went wherever the resource rule pointed. Tierra shrank to 22-30 under a constant slice and grew to 400-800 (with no measured complexity gain) or past 23,000 under size-scaled slices. Cosmos's length-scaled CPU let selfish DNA win in 5 of 9 runs, while a fixed budget kept all 9 in class 2. Amoeba-IV's register-derived slice was gamed. Stringmol's length-dependent decay favoured long molecules, and fixed-cost self-scan blunted the gain from being short. Evoloops, Squirm3 and AlChemy selected the smallest copier. Avida's size-scaled merit cancels the copy-time penalty, yet Avida papers still report shrink pressure (§2.3), and Beckmann shows the regime matters too (gestation near 2,000 instructions when energy-limited, near 300 when space-limited).

PLAN §5.4's cap of c0 + c1 × body length with c1 = 0 is Tierra's constant slice, and PLAN expects shrinking. The notes disagree on the next step: the Tierra note would scale cap and absorb yield with owned bytes, as a named ablation; the metrics note, from Cosmos, would keep the budget per organism. Both effects are real. (inference) Avida's rule pays only for bytes that run.

### 4.2 Systems without a reaper still had forced turnover

| System | What removed individuals or freed space |
|---|---|
| Nanopond | a random cell reseeded every 100 ticks; overwrite; `KILL` |
| Squirm3 | floods clear half the world |
| Evoloops | a dissolver erases jammed loops |
| Cosmos | cull of the poorest 10% at 2,500 cells |
| AlChemy | each product displaces a random object |
| BFF | overwrite by the partner |
| Stringmol | constant decay; bound partners die together |
| MFM | DReg random deletion |
| Avida | overwrite at birth; age limit of 20 × L instructions |
| Tierra | the reaper, plus cosmic rays against immortality |

Anything that escapes turnover gets exploited (Stringmol's decay-only-while-unbound gave immortal loops; Avida's sterile populations "persist"), and without clearance space locks up (Ray's reason for the reaper; Evoloops' debris). PLAN answers with upkeep per byte (H5). (inference) Upkeep removes only organisms whose absorb income falls below it; a small absorb loop in a rich cell can still run a surplus, which is H6.

### 4.3 Write protection and ownership decide whether parasites coexist or collapse the system

Tierra (exclusive write, open read and execute) sustained parasites, hyper-parasites and cheaters, and a keystone parasite doubled diversity. Without protection, Coreworld's seeded replicators broke in about 200 iterations, Amoeba-IV never held two species at once, Squirm3's shared enzymes bred parasites and extinction (**UNVERIFIED**) until membranes were added, and well-mixed Stringmol lost all 1,000 trials to parasites, though spatial Stringmol kept 8 of 20 runs alive with parasites coexisting. In BFF, replication *is* overwriting, and 2D lets variants coexist. Avida has no shared memory and gets parasites only through `inject`. Cosmos made code readable but not writable and got no parasites, because none was one mutation away.

(inference, across these) Exclusive write with open read and execute gives sustainable, commensal parasitism; open write in a well-mixed world gives collapse or monoculture; space partly substitutes for a membrane; and a parasite must be a short mutational hop from its host. PLAN §5.3 now defaults protection on. Since the executor pays in evo, running another's code or capturing its IP already moves energy, before `drain` exists.

### 4.4 The error threshold

With per-site error μ, genome length L and superiority σ, a master sequence persists only if σ·e^(-μL) > 1, so **L_max ≈ ln σ / μ**, equivalently **U = μL < ln σ**; Eigen's own worked example checks out (threshold 0.11, formula 0.115; [Eigen 2002](https://pmc.ncbi.nlm.nih.gov/articles/PMC129678/)); at μ = 10^-3 and σ = 10, L_max is 2,303. evo has no fixed population size, so the failure that matters is extinction: a lineage persists only if **U_d < ln R_max**, where U_d is deleterious mutations per genome per generation and R_max the low-density offspring count of the mutation-free genotype ([Bull, Sanjuán & Wilke 2007](https://pmc.ncbi.nlm.nih.gov/articles/PMC1865999/)). No primary value of σ for digital organisms was found (**UNVERIFIED**), so U_d and R_max should be measured.

| Reference | Copy mutations per genome copy |
|---|---|
| Tierra v5 docs (80 instructions) | about 0.13 (1 in 8 cells per generation) |
| Avida defaults (100) | 0.85 |
| Adami et al. 2000 (100, fixed) | 1.0 |
| Zaman et al. 2014 | 0.25 host, 0.5 parasite |
| Avida critical rates, 54-272 instructions ([Comas et al. 2005](https://pmc.ncbi.nlm.nih.gov/articles/PMC546199/)) | 0.5-3.6 |
| Avida evolved rates ([Gupta et al. 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4867773/)) | 0.13-24.85 |
| BFF | 2^-12 per byte per interaction; no generations |

The notes quote Tierra's rate from different sources: the 1991 text's 1 bit per 1,000-2,500 instructions moved (Tierra note) and a v5 sample run's 1 per 608, about 1.6 × 10^-3 (metrics note); these are different versions, not a contradiction. At the edges, Tierra genomes "melt" at 1 mutation per 1-2 generations, and two communities died when genome size grew 10× at a fixed rate; Cosmos collapsed at high rates and bred a "cancer" at low ones; 94% of BFF runs failed at 1% per byte; Amoeba-IV needed divide mutation between 0.05 and 0.20; Stringmol's UCA revealed a second threshold on *expression* fidelity; and Avida genome size tracks the mutation rate (ρ = -0.72).

### 4.5 Seedless emergence depends on replicator length and a rule that starts execution

| System | Smallest replicator | Outcome | What started execution |
|---|---|---|---|
| BFF; Forth soups | about 5 bytes; 1 byte | 40% of runs; almost all | forced, free execution of every tape |
| SUBLEQ; RSUBLEQ4 | 60; 25 bytes | never | same |
| Long tapes | 2 bytes (8080) | looping only with a head offset above 8, or a second ISA | random start positions |
| Amoeba-I | 5 (secondary) | about 10^-4 of sequences | reseeding (**UNVERIFIED**) |
| Amoeba-IV | about 15 | 25 of 49 runs | 5% of CPUs given random code |
| Coreworld | none | collective structures only | random pointers, P_point = 0.05 |
| Nanopond | not reported | "random genesis" | energy plus a random genome every 100 ticks |

Every success had execution paid for by the environment. The notes differ at the margin: the BFF note says no emergence substrate charged per instruction; Nanopond does, but its inflow grants energy with each random genome, so execution is still externally funded (inference). Replicator length matters: 1-15 where emergence worked, 25-60 where it never did, with Knierim's densities giving the scale. Universality is not enough: a Turing-universal CA can be unable to sustain non-trivial replication ([Cotler et al. 2025](https://arxiv.org/abs/2510.08342)). Where execution starts matters too (long-tape offsets, Forth landing pads). PLAN's hand-written ancestor, about 12 bytes, is in range, but a random evo region has no IP and no energy unless a rule supplies them (§9, H7).

### 4.6 Nop and template inflation

Amoeba-IV's nops rose past 25% of memory by 10^7 generations, and emergence fell after 10^6. Tierra's ancestor is 48 of 80 nops, and 4 of a nop's 5 single-bit flips destroy it; (inference) zeroed Tierra memory is a field of `nop0`. Avida's ancestor is 85 of 100 filler; Stringmol's alphabet is 26 of 33 no-ops. BFF shows the other side: enriching operators found replicators about 10× faster than the soup (25× with a head offset). Long-tape Forth grew landing pads, Cosmos grew selfish DNA, and Squirm3 stripped the unused bases new functions would need. So filler is neither neutral nor free: free filler dilutes the operators emergence needs, and costly filler is stripped along with latent material. PLAN §5.3.2 already decodes unassigned slots as a non-template `pad` instead of `nop0`.

## 5. Consolidated design implications for evo

The four notes' implication lists, merged and deduplicated, ranked by how much each would still change PLAN.md as of 2026-09-30. Items PLAN.md had already absorbed are grouped last. Evidence pointers name a section above and the note section holding the details (notes abbreviated by file name; "oee" is `oee-metrics-and-other-systems.md`).

1. **Specify the seedless start-execution rule, and pre-test replicator density.** Either wrap a random region as an organism with a small energy grant at a low, spatially patterned rate (Tierra note), or give random bytes free background execution (BFF note). Before any soup, count replicators among random genomes in the harness against BFF's one in 2.9 × 10^7 (uniform) and one in 9.4 × 10^4 (CUST64); if evo is far sparser, fix the ISA first. *Evidence:* §4.5; bff-and-recent A.1, C.6; tierra-coreworld-amoeba §6.20. *Affects:* §9 (open question to rule), §5.3 evaluation criterion, §8 Phase 4, H7.

2. **Add a BFF calibration ladder.** Reproduce `bff_noheads` exactly (targets 40%, 44%, about 50%, 22%; cubff test data as golden output), then swap in evo's ISA, then a long tape with head offsets 0, 8, 12 and 16, then evo physics one rule at a time, recording which kills emergence. *Evidence:* §2.8; bff-and-recent C.1-C.4. *Affects:* §8 Phase 4, §6.1.

3. **Scale the tick cap by executed length, not owned length.** Owned-length scaling rewards padding (Cosmos); Avida uses the smaller of executed and copied length, and Amoeba-IV shows it must come from engine records. The notes disagree on the default, so keep per-organism and per-byte arms, and decide whether `absorb` yield scales too. *Evidence:* §4.1; oee D2.2; tierra-coreworld-amoeba §6.1-6.2. *Affects:* §5.4, §5.8, §9.

4. **Decide what `alloc` does to debris and fresh memory.** If debris is not cleared, alloc plus divide without copying resurrects a dead genome cheaply (inference): choose zeroing, a required written fraction, or allow-and-log. Test hostile alloc-divide and tiny-cell mutants, since Tierra and Avida both needed hard guards, and state what byte 0x00 decodes to. *Evidence:* §2.2, §2.3, §4.6; tierra-coreworld-amoeba §6.6, §6.12. *Affects:* §5.3.3, §5.3.2.

5. **Specify search fully.** Add outward search (Tierra's parasites used it) or accept downstream-only parasites; define empty templates (Avida: mark the next address) and matches inside longer nop runs; fix the radius at about 4-8 × ancestor length, not Tierra's moving 5 × mean size; log failed-search energy, the density-dependence mechanism. *Evidence:* §2.2, §2.3; tierra-coreworld-amoeba §6.3-6.5; avida-stringmol Part 5.3. *Affects:* §5.3.3, §9.

6. **Add an IP read.** Stringmol's survivors used code-level self/non-self checks. An evo host could trap foreign executors by comparing `self` with the IP, but only if the IP is readable (Avida's `get-head`): have `self` set C = IP, or add `getip`. The notes differ on keeping `self` (the Tierra note would drop it; the Avida note builds defences on it); PLAN's switch (H8) covers both. *Evidence:* §2.7, §4.3; avida-stringmol Part 5.4, 5.8; tierra-coreworld-amoeba §6.7. *Affects:* §5.3.3, §9.

7. **Make heterogeneity a hypothesis with static and homogeneous controls.** PLAN §5.6 calls non-stationarity "the best known tool against equilibrium", but Ray's heterogeneity bet gave 2 to 3 cell types, Cosmos needed a strong gradient, Sayama finds dynamic environments "may not work for indefinitely long terms", and MODES finds complexity grows only while the environment supplies new information. *Evidence:* §2.2, §2.3, §2.5, §2.10; oee D2.4. *Affects:* §2 (list item 2), §5.6, §11.

8. **Set noise by U = p·L.** PLAN's p = 2 × 10^-3 was calibrated on 80-100-instruction references; on the roughly 12-byte hand ancestor, p·L falls below every load in §4.4 (inference). The notes' start targets differ (about 0.08; 0.1-0.5; 0.1-1). Sweep p from 3 × 10^-4 to 3 × 10^-2 with a zero-noise control; keep background hits at most half the copy hits; measure U_d and R_max; make sure the copy loop can change length. *Evidence:* §4.4; oee D3; avida-stringmol Part 5.11; tierra-coreworld-amoeba §6.14. *Affects:* §5.7, §5.8.

9. **Treat the energy regime as a knob.** Energy-limited and space-limited populations evolve different gestation (Beckmann); shared cell pools let incumbents drain newborns (Cosmos); weak driving is inert (Coreworld). Log absorb yield relative to memory size as a regime variable, and make `drain` lossy and costly. *Evidence:* §2.1, §2.3, §2.5; oee D2.3; avida-stringmol Part 5.6. *Affects:* §5.4, §5.5.

10. **Finish the instrumentation:** energy handed over at birth; a per-organism summary at death (op histogram, instructions and energy spent inside other bodies, searches succeeded and failed); series for alloc failures, debris fraction, turnover and "alive but not divided in N ticks"; mutation cause and owner; components at four levels (genotype, meaningful sites, template segments, phenotype). *Evidence:* §3; oee D1; tierra-coreworld-amoeba §6.9-6.13. *Affects:* §7.

11. **Specify the analysis stack.** MODES with replacement knockouts and generation-counted persistence; Channon's reset shadow offline; QNN; high-order entropy; C_NV; nearest-neighbour novelty. Decide boundedness by model fits, and never use genome length as a complexity proxy. *Evidence:* §3. *Affects:* §6.2.

12. **Check that a working parasite is one or two mutations from the ancestor** before Phase 1's success criterion depends on one. *Evidence:* §2.5, §4.3; oee D2.7. *Affects:* §8 Phase 1.

13. **Decide whether the IP may run off the body.** Tierra's social creatures and cheaters needed it, and §5.2 implies it; count foreign-byte execution. *Evidence:* §2.2; tierra-coreworld-amoeba §6.9-6.10. *Affects:* §5.2, §5.5.

14. **Correct the remaining PLAN text.** §3: Tierra had a decay analog (cosmic rays), just no conservation or costs. §5.3: Tierra mutated only by bit flips. §5.3.1: replicator length is critical "but... not the sole factor", and BFF is neither register nor stack. §2: Stringmol's spatial runs had no energy limit; Coreworld's source blames noise and overwriting (missing write protection is the Tierra note's inference); Avida's size-neutrality is contested. *Evidence:* §2; tierra-coreworld-amoeba §4; bff-and-recent §6; avida-stringmol Part 3. *Affects:* §2, §3, §5.3, §5.3.1.

15. **Run at least 9 seeds per condition, vary seed placement, and report survival fractions.** *Evidence:* §2.5, §2.7. *Affects:* §8, `experiments/`.

16. **Guard determinism against order effects:** a seeded random execution order, no rule reading global quantities, and a check that scheduler seeds agree qualitatively; for multi-core, disjoint regions in a fixed seeded colouring (MFM's event windows), not best-effort schemes (Moreno et al. 2026). *Evidence:* §2.9; bff-and-recent D. *Affects:* §3, §9.

17. **Add a breed-true switch and Tierra's benchmarks** (parasite onset, Lotka-Volterra cycles, keystone 8 versus 16 size classes, energy per byte copied). *Evidence:* §2.2; tierra-coreworld-amoeba §6.15-6.16. *Affects:* §8 Phase 2.

18. **Compare ISAs by Ray's protocol:** same ancestor, 8 seeds, smallest viable size, energy per byte, tempo. Avida's evidence is that registers are not the bottleneck. *Evidence:* §2.2, §2.3. *Affects:* §5.3.1, H1.

19. **Expect proofreading only when something rewards it, and spatial parasitism to be the main counter to shrinking.** *Evidence:* §2.7, §4.1; avida-stringmol Part 5.7, 5.14. *Affects:* §10, §11.

20. **Smaller items:** keep "alloc nearest the body" (kin clusters), with random placement as an ablation; record the 2D torus and evo's hidden state (registers, IP and energy outside the byte array) as hypotheses; consider Nanopond's logo check instead of a paid `guard`; a symbol-conserving chemistry is a possible Phase 4 test. *Evidence:* tierra-coreworld-amoeba §6.23-6.24; oee D2.8, D2.10; avida-stringmol Part 5.9. *Affects:* §5.1, §5.3.3, §5.5, §5.6.

21. **Already adopted in PLAN.md.** `swap`; a post-incrementing `copy`; `pad` and a mutation-aware opcode layout; write protection by default; upkeep per byte; the c1 knob; the `self` switch; two parents per birth, heritable versus somatic events, census and harness; the Stringmol 2015 status; the corrected §2 table; H1-H8.
