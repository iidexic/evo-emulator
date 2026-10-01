# Avida and Stringmol: verified notes for evo

Date: 2026-09-30. Scope: mechanics of Avida and Stringmol that bear on evo's
design (PLAN.md sections 2, 3, 5). This file checks and extends
`docs/research-historic/Review.md` and `References.md`; it does not repeat them.

How this was checked. Where possible I read the code or the paper itself,
not a summary of it:

- Avida source, cloned from https://github.com/devosoft/avida (commit
  `47f13dad`, 2025-01-27). File paths below are relative to `avida-core/`.
- Stringmol source, cloned from https://github.com/uoy-research/stringmol
  (commit `15dad84`, 2025-01-17).
- Full-text PDFs of each paper cited, converted with `pdftotext` and searched.

Tags. **UNVERIFIED** means I could not confirm the claim from a primary
source. Short verbatim quotes are marked with quotation marks and are used
only where the wording matters or the point is contested.

---

## Part 1. Avida

### 1.1 The virtual CPU in the default ("heads") hardware

- Each organism runs its own virtual CPU with **3 registers** (AX, BX, CX),
  **2 stacks**, and **4 heads**: the instruction pointer (IP), a read head, a
  write head and a flow head. A "head" is simply a pointer into the
  organism's own memory. Sources: `source/cpu/cHardwareCPU.h`
  (`NUM_REGISTERS = 3`); `source/cpu/nHardware.h`
  (`enum tHeads { HEAD_IP = 0, HEAD_READ, HEAD_WRITE, HEAD_FLOW }`); Bryson &
  Ofria 2013, https://arxiv.org/abs/1309.0719 ("three registers ... two
  stacks").
- The genome is circular: after the last instruction, execution wraps to the
  first. Organisms cannot normally read or write each other's memory. Source:
  Ofria, Bryson & Wilke 2009, "Avida: A Software Platform for Research in
  Computational Evolutionary Biology" (book chapter),
  https://www.cse.msu.edu/~ofria/pubs/2009AvidaIntro.pdf, pp. 14 and 21-22.
- The world is a grid of cells, **one organism per cell**. The default is a
  60x60 torus (`WORLD_X 60`, `WORLD_Y 60`, `WORLD_GEOMETRY 2` in
  `support/config/avida.cfg`).
- The default ancestor (`support/config/default-heads.org`) is **100
  instructions long**: 15 functional instructions plus 85 `nop-C` filler.

### 1.2 The default 26-instruction set

From `support/config/instset-heads.cfg`, with semantics taken from the
library table and implementations in `source/cpu/cHardwareCPU.cc`. The
notation `?BX?` means "BX by default; a following nop can change it".

| Instruction | What it does (default operands) |
|---|---|
| `nop-A`, `nop-B`, `nop-C` | Do nothing when executed directly. They also act as modifiers and label characters (1.3). |
| `if-n-equ` | Execute the next instruction only if `?BX?` != its complement register; otherwise skip it. |
| `if-less` | Execute the next instruction only if `?BX?` < `?CX?`; otherwise skip it. |
| `if-label` | Read the following label, take its complement, and execute the next instruction only if the most recently *copied* nops equal that complement. |
| `mov-head` | Move `?IP?` to the flow head. |
| `jmp-head` | Move `?IP?` forward by the value in CX. |
| `get-head` | CX = position of `?IP?`. (This is how an organism reads its own IP.) |
| `set-flow` | Flow head = `?CX?`, an absolute position. |
| `shift-r`, `shift-l`, `inc`, `dec` | Operate on `?BX?`. |
| `push`, `pop` | Move `?BX?` to or from the active stack. |
| `swap-stk` | Toggle which of the two stacks is active. |
| `swap` | Swap `?BX?` with its complement register. |
| `add`, `sub`, `nand` | `?BX?` = BX op CX. The operands are fixed; only the destination can be modified. `nand` is the only logic operation. |
| `h-alloc` | Extend memory for the offspring. The new space goes at the end of the genome. |
| `h-copy` | Copy the instruction under the read head to the write head, applying copy mutations, and advance both heads. Cannot be nop-modified. |
| `h-divide` | Split off the instructions between the read head and the write head as the offspring. |
| `IO` | Output `?BX?`, check it against the rewarded tasks, and load a new input into `?BX?`. |
| `h-search` | Read the following label, find its complement, and put the flow head just after the match. BX = distance to the match; CX = label length. |

### 1.3 How nop modifiers work

This is the part closest to evo's 3 modifier bits.

- **Mechanism.** When an instruction that accepts a modifier executes, the
  CPU looks at the *next* instruction. If it is a nop, the CPU uses that nop
  to pick the register or head, **moves the IP past the nop**, and marks the
  nop as executed. If it is not a nop, the default is used. Source:
  `FindModifiedRegister`, `FindModifiedHead` and `FindModifiedNextRegister`
  in `source/cpu/cHardwareCPU.cc`. The consequence is that a nop used as a
  modifier is consumed as part of the instruction and does not run on its
  own.
- **Mapping.** `nop-A` means AX or the IP; `nop-B` means BX or the read head;
  `nop-C` means CX or the write head. Examples: `inc nop-A` increments AX,
  and a bare `inc` increments BX. Source: `cHardwareCPU.cc` lines 74-76
  (`cNOPEntryCPU("nop-A", REG_AX)` ...); Ofria, Bryson & Wilke 2009, p. 13.
- **Two-register instructions.** These use the complement register as the
  second operand. The complement cycle is BX to CX, CX to AX, AX to BX.
  "By default, if-n-equ compares whether the contents of the BX and CX
  registers are identical. However, if if-n-equ is followed by a nop-A, then
  it will compare AX and BX" (2009 chapter, p. 13). In the code,
  `FindNextRegister(r) = (r+1) % 3`.
- **Only one nop counts.** In the default set a modifier is one nop. Two
  instructions read a whole label instead: `h-search` and `if-label` (Bryson
  & Ofria 2013, lines 123-125 of the extracted text).
- **Evidence on richer modifiers.** Bryson & Ofria 2013 tested a
  "Fully-Associative" variant in which several nops can specify both source
  and destination registers. It "shows significant improvement in six of the
  seven environments", and in the final dominant genotypes 9-16% of
  instructions that could take several modifiers actually did. Adding
  registers, up to 16 in total (with one extra nop per register), showed
  "little variation in performance", and 16 registers hurt one environment.
  Source: https://arxiv.org/abs/1309.0719, Results. Caveat: these are
  task-reward environments (logic functions, sorting, navigation), not
  replication-only worlds.

### 1.4 Labels, complements, and `h-search`

- **Templates.** A template (label) is a run of consecutive nops, ending at
  the first non-nop. Nops complement in a cycle: "the complement of nop-A is
  nop-B, the complement of nop-B is nop-C, and the complement of nop-C is
  nop-A" (2009 chapter, p. 12). In the code this is
  `cCodeLabel::Rotate(1, 3)` in `source/cpu/cCodeLabel.h`. The maximum label
  length is 10 (`cCodeLabel::MAX_LENGTH = 10` in `cCodeLabel.cc`).
- **`h-search` semantics** (`Inst_HeadSearch`, `FindLabel(0)`):
  - The search starts at the *beginning of the genome*, not at the IP, and
    finds the first occurrence of the complement.
  - A match may lie inside a longer run of nops. The comment in
    `FindLabel_Forward` reads: "It is okay to find search label's match
    inside another label."
  - On success, the flow head is placed just after the match.
  - On failure the flow head does not jump: it lands just past the search
    instruction's own label. No flag is set, because the instruction always
    "succeeds".
  - With an **empty label**, the flow head is set to the instruction right
    after `h-search`. This is the ancestor's idiom for "mark the start of
    this loop".
- **`if-label` and the read label.** Each `h-copy` records the instruction
  it copied. The CPU keeps a running "read label" of the nops copied most
  recently, and clears it whenever a non-nop is copied (`ReadInst` in
  `cHardwareCPU.cc`). `if-label` compares the complement of its own label
  with that record. So the copy loop can end without a counter: it stops
  when the end-of-genome label has just been copied.
- **The default copy loop, step by step** (`default-heads.org`):
  1. `h-alloc` makes room for the offspring.
  2. `h-search nop-C nop-A` finds the complement label, `nop-A nop-B`, which
     is the last two instructions of the genome. The flow head lands just
     past it, which is the start of the new space.
  3. `mov-head nop-C` moves the write head there.
  4. 85 filler nops follow.
  5. `h-search` with no label marks the loop start (flow head = next
     instruction).
  6. `h-copy` copies one instruction.
  7. `if-label nop-C nop-A` checks "was `nop-A nop-B` just copied?". If yes,
     `h-divide` runs. If no, it is skipped, and `mov-head nop-A` sends the IP
     back to the flow head.

  Note that the final `nop-A` does double duty. It is the modifier of
  `mov-head` and also the first character of the end label.

### 1.5 Allocation, copy, divide

- **Allocation.** `h-alloc` allocates up to `OFFSPRING_SIZE_RANGE` (default
  2.0) times the current size, placed between the end and the start of the
  circular memory (`Inst_MaxAlloc`; 2009 chapter, p. 14). New space is
  filled with a default instruction or random code, depending on
  `ALLOC_METHOD`.
- **Divide.** `h-divide` splits off the region from the read head to the
  write head and discards anything after the write head. By default the
  parent's CPU is then reset "effectively creating 2 offspring"
  (`DIVIDE_METHOD 1` in `avida.cfg`).
- **A failed divide is not death.** "Failure of a command means essentially
  that the command is ignored" (2009 chapter, p. 15). The divide fails if:
  - the parent or the child would be smaller than 10 instructions;
  - no memory was allocated;
  - fewer than half of the parent's instructions were executed
    (`MIN_EXE_LINES 0.5`);
  - fewer than half of the child's instructions were copied
    (`MIN_COPIED_LINES 0.5`);
  - the child's size is outside the allowed range.

  Source: `Divide_CheckViable` in `source/cpu/cHardwareBase.cc`.

### 1.6 Mutation rules and defaults

Defaults from `support/config/avida.cfg` (VERSION_ID 2.14.0):

| Kind | Parameter | Default | When it applies |
|---|---|---|---|
| Copy (substitution) | `COPY_MUT_PROB` | **0.0075** per copied instruction | inside `h-copy`; the replacement is a uniformly random instruction |
| Copy insertion / deletion | `COPY_INS_PROB`, `COPY_DEL_PROB` | 0 | inside `h-copy` |
| Divide insertion | `DIVIDE_INS_PROB` | **0.05** per divide (at most one) | on the child at divide |
| Divide deletion | `DIVIDE_DEL_PROB` | **0.05** per divide (at most one) | on the child at divide |
| Per-site divide mutation | `DIV_MUT_PROB` etc. | 0 | per site, at divide |
| Point ("cosmic ray") | `POINT_MUT_PROB` | 0 | per memory location per update, hitting living organisms |
| Slip (large duplication or deletion) | `COPY_SLIP_PROB`, `DIVIDE_SLIP_PROB` | 0 | |

- With the 100-instruction ancestor, 0.0075 per copy gives about 0.75
  substitutions per offspring.
- Point mutations "affect not only organisms as they are being created ...
  but all living organisms ... a program may change while it is being
  executed" (2009 chapter, pp. 15-16).
- **Implicit mutations** are changes caused by a faulty copy algorithm, for
  example skipped or duplicated code. They are the one source the
  experimenter cannot set with a rate. Avida can discard offspring that
  would differ deterministically (`FAIL_IMPLICIT`; 2009 chapter, p. 16).
- The mutation-rate settings used in the papers cited below differ from the
  defaults and are given with each paper.

### 1.7 Scheduling: merit is CPU time, not energy

- **Merit.** Each organism has a merit (metabolic rate), and CPU cycles are
  handed out in proportion to it. With `SLICING_METHOD 1` the scheduler
  picks the next organism at random, weighted by merit. An "update" is the
  time in which the average organism executes `AVE_TIME_SLICE` = 30
  instructions. Sources: `avida.cfg`; 2009 chapter, pp. 18-19.
- **Base merit grows with genome size.** This is easy to miss. With
  `BASE_MERIT_METHOD 4`, base merit is proportional to the smaller of the
  executed length and the copied length (`CalcSizeMerit` in
  `source/main/cPhenotype.cc`). Fitness is `merit_base * bonus /
  gestation_time` (`CalcFitness`). Copy time grows linearly with length, and
  in the default configuration CPU speed grows with length too, so the two
  roughly cancel. Avida removes the pressure to shrink that Tierra has, by
  design.
- **Task bonuses multiply merit.** The default `environment.cfg` rewards 9
  logic functions with `type=pow`:
  - NOT and NAND: value 1.0 (merit x2)
  - AND and ORN: 2.0 (x4)
  - OR and ANDN: 3.0 (x8)
  - NOR and XOR: 4.0 (x16)
  - EQU: 5.0 (x32)

  Each is rewarded at most once per gestation (`requisite:max_count=1`).
- **Merit is set at birth.** An organism's speed is fixed at the start of its
  gestation. The bonuses it earns take effect at divide, for itself and its
  offspring: "the organisms collect resources for their offspring, rather
  than for themselves" (2009 chapter, p. 21). The stated reason: otherwise
  "mutants specialized in carrying out tasks but not dividing could
  concentrate all CPU time on them".
- **Contrast with evo.** In Avida the total number of cycles per update is
  fixed at 30 times the population, and no organism ever starves. Merit only
  changes each organism's share. In evo, energy income limits the total
  amount of computation, and an organism can stop running.

### 1.8 Death: replacement plus an age limit (Avida's "reaper")

- **Replacement at birth.** Each cell holds one organism, and a birth puts
  the offspring into a cell. If that cell is occupied, "the organism
  currently occupying that cell is killed and removed, irrespective of
  whether it has already reproduced or not" (2009 chapter, p. 18). By
  default the target is a random cell in the neighbourhood, with empty cells
  preferred (`BIRTH_METHOD 0`, `PREFER_EMPTY 1`).
- **Replace-oldest.** "Evolution occurs more rapidly when the oldest organism
  in a neighborhood is the first to be killed off ... when replace oldest is
  used in 2-D neighborhoods, 40% of the time it is the parent that is killed
  off" (2009 chapter, p. 19).
- **Age limit.** `DEATH_METHOD 2` with `AGE_LIMIT 20`: an organism dies after
  executing 20 x genome_length instructions.
- **Why the age limit exists.** This is directly relevant to evo's no-reaper
  design: "Without this setting, it is possible in some cases for a
  population to lose all ability to self-replicate, but persist since
  organisms have no means by which to be purged" (2009 chapter, p. 20).
- **Death on a failed divide** is off by default (`DEATH_PROB 0.0`).

### 1.9 The Avida energy model (Beckmann, McKinley and Ofria)

The brief guessed Bryson & Ofria. In fact the energy model was built by
Benjamin Beckmann (with McKinley and Ofria), first published in 2007 and
described fully in his 2010 PhD thesis.

- **Sources:**
  - Beckmann, McKinley & Ofria 2007, "Evolution of an Adaptive Sleep Response
    in Digital Organisms", ECAL 2007,
    https://cse.msu.edu/~ofria/pubs/2007bBeckmannEtAl.pdf
  - Beckmann 2010, PhD thesis, "Evolving Cooperative, Energy-Conserving,
    Agent-Based Systems", Michigan State University,
    https://d.lib.msu.edu/etd/17557
- **Current code:**
  - `ENERGY_ENABLED 0` is the default in `avida.cfg`.
  - `SingleProcess_PayPreCosts` in `source/cpu/cHardwareBase.cc`.
  - `ConvertEnergyToMerit` in `source/main/cPhenotype.cc`.
- **Mechanics, from the thesis (pp. 26-27) and the code:**
  - Energy is gained only by completing rewarded tasks ("reactions"). In the
    thesis experiments the reward is applied at divide.
  - metabolic rate = stored energy / `NUM_CYCLES_EXC_BEFORE_0_ENERGY`. The
    thesis runs set this to 2000, so an organism "can execute at most 2000
    instructions within its lifetime".
  - Cost of one instruction = metabolic rate x that instruction's energy
    cost, set per instruction in the instruction-set file. In the code:
    `m_inst_energy_cost[op] * merit/100`.
  - Consequence: an organism with more energy runs faster **and** pays more
    per instruction. The thesis calls this a trade-off: "selection attempts
    to both maximize metabolic rate while minimizing energy cost per
    executed instruction" (p. 28).
  - **Zero energy means death.** "When an organism depletes its energy, it
    dies" (thesis p. 26). In the code this is `SetToDie()`, with the comment
    "no more, your died... (evil laugh)".
  - At divide, the parent's energy decays by a set fraction (5% in the
    thesis) and is split equally between parent and offspring.
  - **Offspring still replace occupants of cells.** Energy is added on top
    of the space-competition model; it does not replace it (thesis p. 29).
- **Energy model compared with merit, thesis chapter 2** (10 reactions, 50
  runs per treatment, three treatments: merit with exponential rewards,
  merit with additive rewards, and energy):
  - "A population's size can be constrained by restricting the inflow of
    resources" (p. 29). Under merit, the population always fills the grid.
  - With the energy model, evolved gestation time falls steadily as
    resource inflow rises: "from approximately 2000 instructions to 300
    instructions" (p. 38). The drop is steepest where the population
    switches from energy-limited to space-limited.
  - When inflow was low (10 or less), the grid never filled. "No existing
    organisms is ever replaced ... This lack of space competition forces
    selection to act on the collection and use of resources, which leads to
    long gestation times" (p. 41).
  - Merit with exponential rewards and low inflow gave a *split* outcome:
    64% of runs evolved short gestation (65.7-764.6 instructions) and the
    rest long (1742.6-1902.0), with nothing in between (pp. 38-39). The
    energy and additive treatments did not split.
  - Thesis conclusion: energy "produces results consistent with evolutionary
    theory and avoids divergent evolution that is present in other
    non-energy trials" (p. 14), and "energy costs do not adversely affect
    ecotype diversity" (p. 49).
- **Sleep result** (ECAL 2007):
  - Tasks were rewarded only while a periodic resource was present, and its
    availability fell by 6.25% of each "day" per "year".
  - The sleep instructions cost 1/100 of normal energy and last 10-80 times
    longer.
  - A resource-aware sleep response evolved in 37 of 50 runs.
  - In the control, sleep was replaced by `nop-x`, which costs the full
    amount. Evolution preferred `nop-x`: "Selective pressures ... favored
    doing nothing for 1 CPU cycle and paying a higher energy cost, over
    doing nothing for multiple CPU cycles and using 100 times less energy."
    Because speed depends on stored energy here, saving energy does not
    obviously pay.

### 1.10 Parasites in Avida

- **How they work (the platform).** "The more typical way of allowing
  parasites in Avida is to enable the inject command ... instead of replacing
  an organism in a target cell, the would-be offspring is inserted into the
  memory of the organism occupying the target cell" (2009 chapter, p. 22).
  Unlike Tierra's parasites, "a parasite exists directly inside of its host,
  and makes use of the CPU cycles that would otherwise belong to the host".
- **How they work (the code).**
  - `Inst_Inject` is in `source/cpu/cHardwareTransSMT.cc`; it uses a
    different hardware type with several threads and memory spaces.
  - `cPopulation::ActivateParasite` in `source/main/cPopulation.cc` picks a
    target cell (a random neighbour, or anywhere in a well-mixed world). It
    requires the host to have a free thread slot and, by default, the
    "task overlap" test (`INJECT_IS_TASK_SPECIFIC 1`).
  - `PARASITE_VIRULENCE` sets the probability that each CPU cycle goes to
    the parasite (`avida.cfg`).
- **Zaman, Devangam & Ofria 2011**, GECCO,
  https://cse.msu.edu/~ofria/pubs/2011ZamanEtAl.pdf:
  - A parasite "must inject it's offspring into a host ... the new parasite
    is treated like a thread in the host organism, consuming CPU cycles".
  - Infection needs at least one logic task in common with the host. It
    fails if the target cell is empty or the host is already infected (the
    thread limit is 2).
  - Hosts cannot make extra threads, "preventing host organisms from
    becoming resistant by simply creating additional threads".
  - Infections are cleared when the host divides, so there is no inheritance
    from parent host to child.
  - Virulence 1.0 kills the host and gives Lotka-Volterra cycles. Virulence
    0.5 gives a stable equilibrium. The standard setting was 0.8.
  - Ancestors: a 320-instruction host and an 80-instruction parasite, well
    mixed, 14,400 cells.
- **Zaman et al. 2014.** The brief's venue is wrong: this is *PLoS Biology*
  12(12): e1002023, not Nature Communications.
  https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1002023
  (PMC4267771).
  - A parasite that infects "acquires 80% of the infected host's CPU
    cycles". One parasite per host at most. The world was a well-mixed
    chemostat.
  - Mutation rates were 0.25 per genome for hosts and 0.5 for parasites
    (90% point, 5% insertion, 5% deletion). There were 50 replicates per
    treatment, run for 500,000 updates.
  - Results:
    - EQU evolved in 17 of 50 coevolving host populations and in none
      without parasites.
    - Function-switching mutations were more than 10 times as common in
      coevolved hosts.
    - "Cured" hosts kept more complexity than hosts that never met
      parasites.
- **What "defence" means in Avida.** Resistance is a phenotype: the host
  changes which tasks it performs, because the infection rule is a
  lock-and-key test on tasks. The genetic code for a task "rarely, if ever,
  correspond[s] at the sequence level" between host and parasite (Zaman
  2014). Hosts evolve no defence in their code. This differs sharply from
  Stringmol (2.10).

### 1.11 Robustness and evolvability (the 2008 paper)

Elena & Sanjuán 2008, "The effect of genetic robustness on evolvability in
digital organisms", *BMC Evol Biol* 8:284, doi 10.1186/1471-2148-8-284,
https://pmc.ncbi.nlm.nih.gov/articles/PMC2588588/. (The brief says "Elena et
al"; the authors are Elena and Sanjuán.)

- Method: robust and fragile genotypes of similar fitness were evolved under
  different mutation rates and population sizes, then adapted to new
  environments with 8 or 77 tasks.
- Result: "In the short-term, genetic robustness hampers evolvability
  because it reduces the intensity of selection, but that, in the long-term,
  relaxed selection facilitates the accumulation of genetic diversity and
  thus, promotes evolutionary innovation."
- The effect was clear in the simple (8-task) environment and inconsistent
  in the complex (77-task) one.

### 1.12 What Avida's own researchers say about open-endedness

- **MODES toolbox.** Dolson, Vostinar, Wiser & Ofria 2019, *Artificial Life*
  25(1): 50-73, doi 10.1162/artl_a_00280,
  https://cse.msu.edu/~dolsonem/pdfs/modes_paper.pdf. It defines four
  metrics. All of them are computed only on "persistent" lineages: lineages
  that still have descendants t generations later (a persistence filter).
  1. **Change:** the persistent components in the population differ from
     those at the previous time point.
  2. **Novelty:** the number of persistent components never seen before in
     the run (equivalent to Bedau's A_new).
  3. **Complexity:** the largest number of "informative sites" in any
     persistent genome. A site is informative if knocking it out lowers
     fitness. In Avida the site must be *replaced with a null instruction*,
     not deleted, "because information can be encoded in the number of
     instructions between two other instructions".
  4. **Ecology:** the Shannon entropy of the persistent genotypes, reduced to
     their informative sites (equivalent to Bedau's D).
- **MODES results in Avida:**
  - "In Avida, there is always at least a little change."
  - Novelty declines slowly over time.
  - Complexity: "In the empty environment, there is a rapid rise in
    complexity followed by a decrease and leveling out. This behavior is
    likely due to the strong pressure in Avida to become a more efficient
    self-replicator by optimizing code." In the Logic-9 environment there is
    "an ongoing upward trajectory in complexity".
  - Ecology: "a consistent low level of ecology across all conditions".
  - Authors' conclusion: "Unbounded growth in complexity is only possible in
    a system with a sufficiently complex environment such that there is
    always new information to be integrated into the genome."
- **Dolson, Vostinar & Ofria 2015**, "What's holding artificial life back
  from open-ended evolution?", The Winnower, doi
  10.15200/winn.152418.86598. Only the abstract was verified (via OpenAlex,
  https://api.openalex.org/works/W1239044758). The authors propose
  "measuring obstacles to continued innovation" rather than open-endedness
  itself. **UNVERIFIED:** the specific list of barriers. The four MODES
  hallmarks appear to be where that framework ended up.

---

## Part 2. Stringmol (Hickinbotham, Stepney and colleagues, York)

### 2.1 The model

- **Soup, not organisms.** "Molecules" are strings of symbols. A molecule
  only runs code while it is bound to another molecule. A bound pair forms
  one computing unit whose program can read and write both strings. Source:
  Hickinbotham et al., *Specification of the Stringmol chemical programming
  language v0.2*, York tech report YCS-2010-458,
  https://www.cs.york.ac.uk/library/reports/2010/YCS/458/YCS-2010-458.pdf
  (sections 3-7).
- **Well-mixed version.** A container of area 2500 holds molecules of area
  10. The chance that two molecules meet is 1 - (1 - v_a/v_c)^n (spec eq. 1),
  and space appears in no other way.
- **Spatial version.** A 2D torus with one string per cell. Binding is only
  with the Moore neighbourhood. A product goes into an empty neighbouring
  cell, or is thrown away if there is none. Source: Hickinbotham, Stepney &
  Hogeweg 2021, Methods,
  https://eprints.whiterose.ac.uk/id/eprint/176868/1/rsos.210441.pdf.

### 2.2 The alphabet: 33 opcodes

- **Symbols.** There are 26 template codes (A-Z) and 7 function codes:
  `$ > ^ ? = % }`. "The remaining 26 opcodes, the characters A-Z, have no
  operation when executed (they are `no-ops'), but are used when binding
  strings, and as modifiers of the functional opcodes" (2021, Methods).
- **Complement.** Template codes complement like ROT13 (A with N, B with O,
  and so on). Function codes complement themselves (spec Table 2; 2021
  Methods).
- **Mutation on copy.** In the spec, a mutation moves a symbol one step
  forward or back along a fixed cycle,
  `ABC$DEF>GHIJ^KLM=NOP?QRS}TUV%WXYZ`. Function codes are spread along the
  cycle "to reduce any clustering of functional codes to form 'functional
  hotspots'" (spec 6.3). Rates: substitution Ps = 1e-5; insertion or
  deletion is rarer still (spec 10.6.1). By 2021 a miscopy writes "a
  randomly chosen different symbol" (2021 Methods). The code
  (`OpcodeAdjacent` in `src/opcodes.cpp`) keeps the adjacent-symbol version.

### 2.3 Soft binding

- **Alignment.** Binding uses Smith-Waterman local alignment: one string is
  aligned against the *complement* of the other. The scoring table gives 1.0
  for a matching template code and 0.5 for a matching function code. A
  mismatch costs more the further apart the two symbols are on the mutation
  cycle, averaging -1. An insertion or deletion costs -4/3. Source: spec
  6.3-6.4.
- **Bind probability.** From `ReactionCalculateBindProbability` in
  `src/alignment.cpp`, where l is the length of the aligned region:
  - If l <= 2, P = 0.
  - Otherwise P = min(score, l - 1.124) / (l - 1.124).

  So a long alignment with one near-miss still binds with certainty. The
  spec's eq. 13 has the same shape but garbles in PDF extraction; the code
  form above is authoritative.
- **Which string executes.** The string whose bind site lies further from its
  own start becomes the executor ("string1"). If both are equidistant it is
  chosen at random (spec 7.4.1; 2021 Methods). A molecule can therefore
  steer whether it is the copier or the copied, and much of its evolution
  consists of exactly that steering (spec 11.2.5).

### 2.4 Pointers and microcodes

- **Pointers.** There are 4 pointer types: instruction, flow, read and write.
  Each exists twice, once per string of the pair, and a flag per type says
  which string it currently points into. "There are no registers or stacks
  to hold values" (2021 Methods; spec 7.3-7.4).
- **Function codes** (spec section 10; the Table 4 layout garbles in PDF
  extraction, the section headings do not):

| Code | Name | Effect |
|---|---|---|
| `$` | search | Move the flow pointer to the end of the best match for the template that follows. The match is probabilistic (next bullet). |
| `>` | move | Move the IP (or, with a modifier, another pointer) to the flow pointer. This builds loops. |
| `^` | toggle | Switch a pointer to the partner string. |
| `?` | if | With a template: skip one or two instructions depending on a probabilistic template match at the read pointer. Without one: test whether the read pointer has run off the end of its string. |
| `=` | copy | Write the symbol at the read pointer to the write pointer, with mutation. This is the only way strings grow. Maximum string length is 512 in the spec, 2000 later. |
| `%` | cleave | Cut the string at the flow pointer; the part after the cut becomes a new molecule. |
| `}` | end | Stop, and unbind the pair. |

- **Modifiers.** Only A, B and C modify: A selects the IP, B the read
  pointer, C the write pointer (spec 8.1 and 9.4). This is the same trick as
  Avida's nop modifiers.
- **Probabilistic control flow.** Template matches during execution are also
  probabilistic. A slightly imperfect loop-exit template therefore acts as
  "a stochastic timer" (spec 9.5).

### 2.5 Energy, decay, mutation: the numbers

- **Energy in the well-mixed spec.** A fixed amount of energy enters per
  timestep. "One binding attempt or one execution of an instruction requires
  one unit of energy. Energy not used in one time step is available in the
  next" (spec section 3). In the code this is `ESTEP`, added each step
  (`A.energy += A.estep` in `src/stringmol.cpp`).
- **Energy in the spatial runs.** The energy limit is effectively off: "all
  opcodes waiting are executed, with a limit of one execution per reacting
  pair per timestep" (2021 Methods). In the code, `src/sm_spatial.cpp` sets
  energy to gridx*gridy each step.
- **Decay.** Each molecule is deleted with a constant probability per
  timestep of 1/65^2 (about 2.37e-4), whether bound or not. If a bound
  molecule decays, its partner goes with it (spec section 4 and Appendix C;
  `comass_AgentAttemptDecay` in `src/stringPM.cpp`).
- **UCA runs (2017).** Mutation was set to 0.5e-6 per copy, decay to 0.24e-4
  per step, and the maximum string length to 200,000.
- **Spatial runs.** The repository config `spatial_stringmol_v2.0.3.conf` has
  a 125x100 grid, `DECAY 0.0005`, `MUTATE 0.0002`, and the 2021 seed.
  **UNVERIFIED** that these exact values were used in the published runs:
  neither paper states them.

### 2.6 Lessons about decay (spec Appendix C)

These are directly relevant to evo, because decay shaped what evolved:

- **Decay only while unbound.** This "selects for molecules which remain in a
  reaction permanently (via the emergence of an infinite while loop)". The
  population ends up as "a set of pairs of molecules participating in
  non-terminating reactions. No further evolution of the system can be
  observed."
- **Decay rate that falls with length.** "Confers a huge evolutionary
  advantage on longer molecules."
- **Only constant decay in every state** ("DC + ALL") gave "a regular
  turnover of dominant molecular species".

### 2.7 Well-mixed results (spec section 11)

- **Invasion.** A mutant that bound more strongly replaced the resident
  replicase in 88 of 100 trials ("invasion when rare").
- **Long runs.** In 1,000 runs with mutation, "None of the 1,000 trials
  self-maintains indefinitely". The most common extinction time was 750,000
  timesteps.
- **Cause of extinction.** A parasite arises that cannot replicate itself but
  is copied by the resident replicase faster than the replicase copies
  itself. This produces the "death spike".
- **Other outcomes.**
  - Hypercycles, where two species copy each other but neither can copy
    itself, appeared in 30 trials.
  - Selection often *lowered* self-binding, because a molecule wins by
    making sure it is the one being copied.

### 2.8 Conservation of matter (Hickinbotham & Stepney 2015)

Citation: ECAL 2015, pp. 98-105, doi 10.7551/978-0-262-33027-5-ch024. The
MIT Press PDF is behind a Cloudflare check; I read an archived copy at
https://web.archive.org/web/2023/https://direct.mit.edu/isal/proceedings-pdf/ecal2015/27/98/1903947/978-0-262-33027-5-ch024.pdf.
The mechanics are confirmed in the source (`OpcodeCopy_Comass` in
`src/opcodes.cpp`; `comass_free_ag` in `src/stringPM.cpp`).

- **What is conserved.** The *count of each opcode type* is fixed. A buffer
  records how many free copies of each symbol exist.
  - Copying a symbol takes one of that symbol from the buffer.
  - Overwriting a symbol returns the old one to the buffer.
  - When a molecule decays, all of its symbols return to the buffer.
- **Mutation comes only from scarcity.** If the symbol being copied is not
  available, the adjacent (mutant) symbol is tried. If that is also
  unavailable, nothing is written, "the copy operation acts like a deletion".
  "Replication is exact unless there is a shortage of available opcodes."
  Insertion is not possible.
- **How activity was measured.** Not with Bedau-Packard statistics but with
  QNN ("quantitative non-neutral activity"; Droop & Hickinbotham 2012). For
  each species, square the increase in its share of the population since the
  previous time step, then sum over species and time. It rewards rapid rises
  in abundance.
- **Experiment I: equal amounts of every opcode.** They tried 1,000 to 3,000
  copies of each of the 33 opcodes, with 100 runs at each level, 150 seed
  molecules and runs of up to 1 million timesteps.
  - The number of species peaked at **1,700** per opcode, but runs there were
    very short: the "error catastrophe".
  - **QNN peaked at 2,400** per opcode, which is the lowest level at which
    the population could sustain itself.
  - Runs below 2,400 were particularly short.
- **Experiment II: tuning each opcode separately.** A microbial GA (25 runs,
  5,000 tournaments each) searched concentrations between 0 and 4,000 per
  opcode.
  - 20 of the 25 runs found self-sustaining settings.
  - After convergence, median QNN was about 300, against less than 100 for
    the uniform 2,400.
  - The runs agreed on no common set of concentrations, but each had
    *several scarce opcodes* (fewer than 400 copies). The copy opcode `=`
    was often scarce.
- **Experiment III: boosting the scarce opcodes.** Multiplying the scarce
  opcodes (D, E, =, X) by 10 gave a robust system with little evolutionary
  activity.
- **Caveats the review missed:**
  - The paper reports **no QNN comparison with ordinary Stringmol, where
    matter is not conserved**. It says only "possibly even more than the
    original Stringmol formulation".
  - Conserving matter also changed the mutation mechanism, from a fixed rate
    to scarcity. The effect cannot be separated from that change.
  - The authors' own framing: CoM is "an embodied mutation operator that
    responds to local conditions".

### 2.9 Semantic closure and "bureaucratic death" (Clark, Hickinbotham & Stepney 2017)

Citation: *J. R. Soc. Interface* 14: 20161033, doi 10.1098/rsif.2016.1033,
https://pmc.ncbi.nlm.nih.gov/articles/PMC5454285/. Quotes below were checked
against the Europe PMC full text.

- **Architecture.** A "universal constructor architecture" (UCA) with four
  parts:
  - a genome of about 3,656 opcodes;
  - a copier, which copies the genome;
  - an expressor, which uses a codon lookup table *that is itself encoded in
    the genome*, so the system defines its own meaning (hence "semantically
    closed");
  - a payload.

  Each run started with 50 each of the copier, the expressor and the genome.
- **Takeovers.** "The 500 runs produced 39 examples of container-wide
  takeovers, where one or more seed species is replaced by a mutated version
  while maintaining a viable UCA." 23 of these were genome mutations that
  became fixed, and in 16 the heritable change was *not* encoded on the
  genome.
- **Every run died.** Mean extinction time was 6,572,488 timesteps and the
  median 4,665,000; the longest run exceeded 30 million.
- **None died of parasites.** "Death by parasites did not occur in any of
  the 500 runs." None collapsed to a simple replicase either.
- **Bureaucratic death.** "The mode of death is referred to as 'bureaucratic
  death', as the system simply collapses under its own weight with no clear
  culpability." Diversity explodes, and then the viable system decays. The
  proposed cause is a cascade in which a mutated expressor builds worse
  expressors, which build worse ones still. The authors call this the mirror
  of Eigen's paradox: expression fidelity, not only copying fidelity, limits
  what can survive.
- **Relevant to evo.** "These [mutation and decay rates] are not under the
  control of systems designed in stringmol." Evo's noisy writes, with
  proofreading that organisms could evolve, address exactly this
  limitation.

### 2.10 Spatial parasitism (Hickinbotham, Stepney & Hogeweg 2021)

Citation: *R. Soc. Open Sci.* 8: 210441, doi 10.1098/rsos.210441,
https://eprints.whiterose.ac.uk/id/eprint/176868/1/rsos.210441.pdf
(PMC8334846).

- **Setup.** 20 runs on toroidal grids of 12,500 cells, either 100x125 or
  250x50. Each run was seeded with copies of the 65-symbol seed replicator
  `WWGEWLHHHRLUEUWJJJRJXUUUDYGRHJLRWWRE$BLUBO^B>C$=?>$$BLUBO%}OYHOB` and ran
  for 2 million timesteps.
- **Outcome.** "20 runs in total, of which 12 went extinct, and eight
  remained executing". In the survivors, population and species count both
  rose.
- **What distinguished the survivors.**
  - This paper says only: "extinction still occurs in about half the cases
    due to almost-immediately emerging fast replicating parasites. However,
    where the system survives long enough for the well-known
    replicator-parasite wave pattern to emerge, fascinating long-term
    evolution unfolds."
  - The 2024 paper (2.11) says more: "The initial block distribution appears
    to be the key factor in avoiding early extinction. The random pair
    distribution is much less stable in early periods of runs even with
    large initial count: Patches do not grow quickly enough before parasites
    swamp them."
- **Replicator defences** (2021 section 2.9: "Features common to all runs"):
  1. **Non-complementary binding.** Replicators came to bind through function
     codes, which match themselves. Parasites then bind *to each other* too,
     which wastes them. Under complementary binding a parasite can avoid
     sticking to other parasites.
  2. **"Self-scan".** Before copying its partner, the replicator copies
     itself over itself. This slows replication by a fixed amount that "is
     not proportional to the length of the string being replicated,
     reducing the benefit of evolving to be short". Side effect: "the point
     mutation rate is approximately doubled", which the authors count as
     "evolution itself evolves".
  3. **Toggle checks (self/non-self).** Execution jumps to the partner string
     and only returns if the partner has the right code. "If a non-self
     string does not have the toggle code, execution is not passed back ...
     and replication does not happen." Parasites without the code "are held
     in an unproductive reaction for long periods of time". Later
     replicators added "two additional checks on the partner string's code".
     In run 2 this brought parasitic reactions down to 323 of 5,671.
  4. **Hypercycles** in some runs: A copies B and B copies A, but neither
     copies itself.
- **Where parasites come from.** "New parasite species continually arise from
  mutated replicators, rather than from evolving parasite lineages." A
  parasite that descends from a replicator inherits the features that let it
  pass that replicator's checks.
- **Defences are not kept.** "Without the selection pressure of the
  parasites, these elaborate mechanisms are then lost, and new parasites
  emerge."
- **Macro-mutations.** A single point mutation that shifts where `$` search
  or `%` cleave lands can splice strings together, producing large changes
  that no single point mutation could.
- **Headline.** Parasites turn wasted work into a selected trait: "there is
  selective advantage in actively wasting resources outside of the main
  replicating activity ... giving a route to escape the relentless pressure
  to simply replicate ever more efficiently".

### 2.11 "On the Open-Endedness of Detecting Open-Endedness" (Stepney & Hickinbotham 2024)

Citation: *Artificial Life* 30(3): 390-416, doi 10.1162/artl_a_00399. Author
copy: https://www-users.york.ac.uk/~ss44/bib/ss/nonstd/artl23.pdf.

- **Data.** The eight surviving 2021 runs.
- **Table 1 of this paper:**
  - runs 1-4: 125x100 grid, block of 121 seeds;
  - runs 5-6: 125x100, 51 randomly placed pairs;
  - runs 7-8: 250x50, block of 121;
  - runs 9-20: 250x50, 500 randomly placed pairs. "All runs in the
    configuration on the bottom row went extinct".
- **Contested point.** The 2021 paper's Methods say instead that there were
  100 seeds, a 10x10 block, and "four treatments with five replicates each".
  The repository config uses an 11x11 = 121 block, which supports the 2024
  table. **Treat the 2021 description of treatments as unreliable.**
- **Measures applied, in order:**
  - QNN and cumulative QNN;
  - population size;
  - species count and new-species count;
  - abundance per species and the most abundant sequences;
  - string length against how long a species lasts, and length
    distributions over time;
  - "in vitro" re-tests: each observed string is bound to itself, with
    mutation off, to check whether it can still copy itself;
  - reaction types (parasitic, mutual replication, hypercycle, other);
  - how often the toggle opcode runs.
- **Findings:**
  - Final cumulative QNN ranged from 0.972 (run 6) to 2.874 (run 5).
  - QNN flattened in runs 1, 4, 6 and 8.
  - Run 5 scored highest but was mostly "churn", not innovation.
  - Run 6 scored *lowest* but was the most unusual: early hypercycles, and
    the only run that kept its alphabetic binding region.
  - Except during run 2's "flood" period, most species could not copy
    themselves in isolation.
- **Conclusions** (section 5.1):
  - "Summary statistics are not helpful."
  - "Generic measures make assumptions" (fitness from outside, discrete
    generations, a focus on individuals).
  - "QNN is a comparative measure."
  - "System-specific measures are essential."
  - "Behavioral measures are key."
  - "The understandable desire for a single quantitative measure of OE is
    nevertheless a dead end."
  - They also name a design limit: "currently the micromutation rate is hard
    coded and not evolvable. The copy opcode might be better broken down
    into smaller components".

---

## Part 3. Corrections to the prior report and to the brief

1. **The 2021 Stringmol parasitism paper is cited wrongly** in
   `Review.md` and `References.md`. They give *J. R. Soc. Interface* 18,
   20210022, doi `10.1098/rsif.2021.0022`; that DOI returns 404 from
   Crossref and doi.org. The correct citation is Hickinbotham, Stepney &
   **Hogeweg**, *R. Soc. Open Sci.* 8: 210441, doi 10.1098/rsos.210441. The
   PMC link the report uses (PMC8334846) does point to the right paper.
2. **Ofria & Wilke 2004 is cited wrongly.** The report gives *Briefings in
   Bioinformatics*, doi `10.1093/bib/5.3.243`, which does not resolve. The
   correct citation is *Artificial Life* 10(2): 191-229, doi
   10.1162/106454604773563612.
3. **The 2015 conservation-of-matter result is overstated.** It is summarised
   as "greater evolutionary activity and diversity". In fact:
   - the paper reports no comparison with Stringmol without conservation;
   - conservation also replaced the mutation mechanism (2.8);
   - species diversity peaked where runs died of error catastrophe, not
     where activity peaked.
4. **The 2017 UCA outcome is understated.** It is summarised as "the
   dominant failure was bureaucratic death". In fact all 500 runs died, none
   from parasites, and none collapsed to a replicase. Bureaucratic death was
   the only mode observed.
5. **Stringmol energy is generalised too far.** "Opcode execution consumes
   energy" holds for the well-mixed spec and the UCA runs. The 2021/2024
   spatial runs did not limit energy.
6. **Corrections to the brief:**
   - Zaman et al. 2014 is *PLoS Biology*, not Nature Communications.
   - The Avida energy model is Beckmann, McKinley & Ofria 2007 and Beckmann
     2010, not Bryson & Ofria. Bryson & Ofria 2013 is the ISA-design paper.
   - "Elena et al. 2008" is Elena & Sanjuán, *BMC Evol Biol* 8:284.

## Part 4. UNVERIFIED items

- The exact list of "barriers" in Dolson, Vostinar & Ofria 2015 (abstract
  only).
- The mutation and decay rates used in the 2021/2024 spatial Stringmol runs.
  The repository config (`MUTATE 0.0002`, `DECAY 0.0005`, `ESTEP 2500`) is
  plausible but not confirmed.
- That Zaman et al. 2014 used the same inject mechanism as the 2011 paper
  (thread in host, cleared at host divide). The 2014 paper cites earlier
  work for it and does not describe it.
- The exact form of the Stringmol spec's bind formula (eq. 13). The PDF
  extraction is garbled; the code form in 2.3 is verified.
- Whether the "85%" figure in spec 8.1 (how often an instruction falls back
  to its default pointer) is correct. With 3 modifier codes out of 33 or 34
  symbols the figure would be nearer 91%. This is the authors' arithmetic,
  not mine.

---

## Part 5. Design implications for evo

Each point says what the sources show and what it means for PLAN.md.

1. **Avida's nop modifiers compared with evo's 3 modifier bits.**
   - In Avida, an instruction's operand is an optional *following*
     instruction. As a result:
     - inserting or deleting a nop after an instruction silently changes
       its operand;
     - a point mutation that turns a nop into a non-nop removes the modifier
       *and* shortens a label.
   - Evo's fixed field keeps every mutation inside one byte, which is
     simpler and more local. Evidence from Avida itself: more flexible
     operands (the multi-nop "Fully-Associative" set) helped in 6 of 7
     environments, while more registers did little (1.3). Four registers is
     therefore not a bottleneck.
   - Worth copying from Avida: *default operands*. An instruction with no
     modifier still does something sensible.
   - Recommendation: keep the fixed field. Choose each op's modifier
     encoding so that the most useful register is reachable by the most bit
     patterns.
2. **Assign opcode numbers so that one-bit mutations are mild.**
   - Mutation in evo is a bit flip. Each op therefore has exactly 5
     opcode-changing neighbours (and 3 that change only the modifier).
   - Stringmol deliberately arranges its mutation cycle so that function
     codes are spread out, avoiding "functional hotspots" (2.2).
   - Recommendation: place pairs that are safe to swap one bit apart:
     `inc`/`dec`, `shl`/`shr`, `skipz`/`skipnz`, `searchf`/`searchb`,
     `nop0`/`nop1`. Keep `divide`, `alloc` and `copy` away from `nop0`, so
     that neutral filler does not drift into ops that do something drastic.
     Record the chosen mapping in the ISA spec.
3. **Define what a zero-length template does.** Avida's `h-search` with no
   label means "mark the next instruction", and its default ancestor relies
   on this idiom (1.4). It also matches labels *inside* longer nop runs and
   searches from the start of the genome.
   - Recommendation: give `searchf`/`searchb` with an empty template a
     useful meaning: D = address just past the search, and no fail flag.
   - Recommendation: say explicitly whether a match may sit inside a longer
     nop run. It matters for how robust labels are to mutation.
4. **Add a way to read the IP.** Avida has `get-head` (CX = IP). Evo can
   only get its position through the empty-search trick above.
   - This matters for parasites (point 8). Code in a host can check who is
     running it only if the executing organism can compare "where am I
     running" with `self`.
   - Recommendation: have `self` also set C = IP, or add a `getip r` op in a
     spare slot.
5. **Consider making `copy` auto-increment.** Avida's `h-copy` advances both
   heads, so its copy loop is 3-4 instructions long. Evo's `copy` does not
   advance A and B, so the loop needs `copy; inc A; inc B; dec C; skipz C;
   jmpr ...`.
   - A shorter loop is a smaller mutational target and faster, which is
     PLAN's own argument for a one-op copy.
   - Recommendation: use one modifier bit of `copy` for post-increment of A
     and B.
6. **Evo's pay-per-instruction model compared with Avida's energy model.**
   - Avida's energy model links speed to stored energy and charges per
     instruction in proportion to that speed. Zero energy means immediate
     death, and offspring still displace occupants (1.9).
   - Evo instead has a store, a per-tick cap, and no death at zero.
   - Transferable finding from Beckmann (2010, pp. 38-41): when the
     population is *limited by energy rather than space*, nobody gets
     displaced, and selection favoured organisms that were slow and thorough
     at gathering resources (gestation about 2,000 instructions). As inflow
     rose and space became the limit, gestation fell to about 300.
   - Recommendation: evo can move between these regimes by changing absorb
     yield relative to memory size. Log a hypothesis: "Mean genome length and
     gestation time are higher when the population is energy-limited than
     when it is space-limited."
   - Also plan for the sleep result. An op that does nothing cheaply is only
     favoured if saving energy has a payoff. In evo that payoff exists,
     because energy carries over and is not converted to speed.
7. **Length is not size-neutral in evo, so expect shrinking.**
   - Avida's default gives longer genomes proportionally more CPU (1.7).
     Even so, complexity in Avida worlds without tasks "rises then decreases
     and levels out" (1.12).
   - Evo has no such compensation (§5.8), so the Tierra-style push toward
     short genomes will be stronger.
   - The only mechanism in these sources that reliably pushed *back*,
     without a designer reward, is parasitism under spatial structure: the
     Stringmol self-scan and toggle checks (2.10).
   - This supports PLAN's bet on interactions. It also means Phase 1 should
     *expect* shrinking and treat parasite emergence as the main thing
     working against it.
8. **Parasite defences: what they look like as code, and whether evo's ISA
   allows them.** In Stringmol the defences are code-level checks on the
   partner (2.10). In Avida, resistance is only a matter of which tasks the
   host performs (1.10). Evo's analogues:
   - **Self-check trap.** A Tierra-style parasite in evo jumps into the
     host's copy loop and runs host code with *its own* registers. A host
     loop that first runs `self` and compares the executing organism's body
     with the loop's own address can send foreign executors into an endless
     loop that burns their energy. This is the evo version of Stringmol
     holding parasites "in an unproductive reaction".
     - The ISA supports this if `self` returns the *executor's* body and an
       IP read exists (point 4).
     - It costs a few instructions per copy. That is a fixed cost, just like
       self-scan.
   - **Fixed-cost padding.** A delay loop that does not depend on body size
     is expressible with existing ops, and it reduces the advantage of being
     short.
   - **Template specificity.** Changing loop labels so that parasites' search
     templates no longer match is expressible, and was a Tierra immunity
     route.
   - **Missing today.** There is no counterpart to Stringmol's
     non-complementary binding: evo has no binding step.
   - Recommendation: add a hypothesis entry predicting that, in evo,
     immunity will appear as self-checks placed before the copy loop.
9. **Stringmol's conservation result does not transfer directly.**
   - Stringmol conserved *counts of each symbol*, and its mutation came from
     running short of a symbol (2.8).
   - Evo conserves *bytes of space*, and a byte can hold any value. Evo's
     finite memory gives the carrying-capacity part of the argument ("growth
     is bounded"). It does not give scarcity-driven mutation or any pressure
     on *which* opcodes an organism uses.
   - Recommendation: do not cite the 2015 paper as support for §5.1.
   - Possible Phase 4 "chemistry" experiment: writes of value v must draw on
     a regional pool of v-valued debris. This is the direct analogue, and it
     ties in with §5.6's multiple resource types.
10. **With no reaper, decide what purges sterile organisms that still
    persist.**
    - Avida added age death because non-replicators "persist since organisms
      have no means by which to be purged" (1.8).
    - Stringmol found that any state that escapes decay gets exploited:
      decay only while unbound produced endless loops (2.6).
    - In evo, an `absorb; jmpr` loop with a positive energy balance is
      immortal except for bit rot.
    - Recommendation:
      - Bit rot and noisy writes must hit every owned byte whatever the
        owner is doing, with no state that shields it. Stringmol's "ALL"
        rule.
      - Consider a per-tick maintenance cost in proportion to body size
        (§5.7), so that a sterile absorber's net income shrinks as it grows.
      - Instrument "alive but has not divided in N ticks" as its own
        category.
11. **Pick the mutation rate against genome length.**
    - Reference points:
      - Avida default: about 0.75 substitutions per 100-instruction genome,
        plus 5% insertion and 5% deletion per divide (1.6);
      - Zaman 2014: 0.25 (hosts) and 0.5 (parasites) per genome;
      - Stringmol: much lower per symbol (1e-5 to 2e-4), but on 65-symbol
        strings.
    - Evo's per-write flip probability p, times ancestor length L, should
      start near L*p = 0.1-1.
    - Unlike Avida, evo has no way to insert or delete except through what
      programs do, which Avida calls "implicit mutations". Make sure the
      ancestor's copy loop can produce length changes, or length will stay
      fixed.
12. **Seeding and replicates.**
    - In spatial Stringmol, a clustered seed survived and a scattered seed
      went extinct (2.11): all 12 runs with 500 randomly placed pairs died.
    - Recommendation: make "clumped or scattered initial placement" an
      explicit Phase 1 factor, and expect many early extinctions. Report the
      fraction that survive, not only the best run.
13. **Measurement.** For Phase 2 analysis:
    - Use MODES with a persistence filter (1.12).
    - Compute "informative sites" by knocking out with `nop0` *replacement*,
      not deletion, because offsets carry information in evo just as in
      Avida.
    - Following Stepney & Hickinbotham, also log system-specific behavioural
      counts. Per organism: how often each op executes, and how many
      instructions ran with the IP inside *another* organism's body. The
      second is a direct, cheap measure of parasitism, the equivalent of
      their toggle count.
14. **Evo already addresses a limit Stringmol's authors name.** They want an
    evolvable mutation rate and a copy broken into smaller steps (2.9,
    2.11). Evo's noisy writes plus proofreading built from `load`/`sub`/
    `skipz` provide both. The defences in 2.10 show that organisms will
    evolve deliberate costly "waste" when parasites make it pay. That is
    reasonable grounds to expect proofreading to evolve only once something
    rewards it; the hypotheses log should say so.

---

## Source list

**Avida source and configuration**
- Avida source: https://github.com/devosoft/avida (commit 47f13dad, 2025-01-27)
- Default configuration and instruction set:
  - `avida-core/support/config/avida.cfg`
  - `avida-core/support/config/instset-heads.cfg`
  - `avida-core/support/config/default-heads.org`
  - `avida-core/support/config/environment.cfg`
- Implementation:
  - `avida-core/source/cpu/cHardwareCPU.cc`
  - `avida-core/source/cpu/cHardwareBase.cc`
  - `avida-core/source/cpu/cCodeLabel.h`
  - `avida-core/source/cpu/cHardwareTransSMT.cc`
  - `avida-core/source/main/cPhenotype.cc`
  - `avida-core/source/main/cPopulation.cc`

**Avida papers**
- Ofria, Bryson & Wilke 2009, chapter:
  https://www.cse.msu.edu/~ofria/pubs/2009AvidaIntro.pdf
- Ofria & Wilke 2004, *Artificial Life* 10(2): 191-229:
  https://doi.org/10.1162/106454604773563612
- Beckmann, McKinley & Ofria 2007:
  https://cse.msu.edu/~ofria/pubs/2007bBeckmannEtAl.pdf
- Beckmann 2010, thesis: https://d.lib.msu.edu/etd/17557
- Zaman, Devangam & Ofria 2011:
  https://cse.msu.edu/~ofria/pubs/2011ZamanEtAl.pdf
- Zaman et al. 2014:
  https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1002023
- Elena & Sanjuán 2008: https://pmc.ncbi.nlm.nih.gov/articles/PMC2588588/
- Bryson & Ofria 2012: https://cse.msu.edu/~ofria/pubs/2012BrysonOfria.pdf
- Bryson & Ofria 2013: https://arxiv.org/abs/1309.0719
- Dolson et al. 2019 (MODES): https://cse.msu.edu/~dolsonem/pdfs/modes_paper.pdf
- Dolson, Vostinar & Ofria 2015: https://doi.org/10.15200/winn.152418.86598

**Stringmol source and papers**
- Stringmol spec (YCS-2010-458):
  https://www.cs.york.ac.uk/library/reports/2010/YCS/458/YCS-2010-458.pdf
- Stringmol source: https://github.com/uoy-research/stringmol (commit
  15dad84, 2025-01-17)
- Hickinbotham & Stepney 2015: https://doi.org/10.7551/978-0-262-33027-5-ch024
- Clark, Hickinbotham & Stepney 2017:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5454285/
- Hickinbotham, Stepney & Hogeweg 2021:
  https://eprints.whiterose.ac.uk/id/eprint/176868/1/rsos.210441.pdf
- Stepney & Hickinbotham 2024:
  https://www-users.york.ac.uk/~ss44/bib/ss/nonstd/artl23.pdf
- Hoverd & Stepney 2011, "Energy as a driver of diversity in open-ended
  evolution" (abstract only):
  https://doi.org/10.7551/978-0-262-29714-1-ch055. It reports that adding an
  energy model "produces simulations with measurably increased diversity",
  in the Sticky Feet model, not Stringmol.
