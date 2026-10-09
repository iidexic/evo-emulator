# Recent work, cluster 2: emergence from random soups and rule-by-rule studies

Compiled 2026-10-08 (finished 2026-10-09). Purpose: cluster 2 of
`docs/research/literature-recent-plan.md`. Everything citing *Computational
Life* (arXiv 2406.19108) through 2026 beyond the three papers already in
`notes/bff-and-recent.md` (Knierim 2026, Cicala 2026, ASAL), plus
self-replication emergence in other substrates since 2020, plus any direct
measurement of minimal replicator length against emergence rate. The question
this cluster has to settle is plan question 3: has anyone added physics rules one
at a time to a random-soup protocol and reported which rule kills emergence, and
is energy among the rules tried.

How this was checked:

- Citation sweeps: Semantic Scholar Graph API "citations" on arXiv 2406.19108
  (24 citing works returned,
  https://api.semanticscholar.org/graph/v1/paper/arXiv:2406.19108/citations?fields=title,year,externalIds,venue,abstract&limit=200),
  on 2607.01483 and 2607.09211 (both empty); OpenAlex `cites:W4400141836`
  (2 works, https://api.openalex.org/works?filter=cites:W4400141836&per-page=50).
  Google Scholar was not attempted (no API; blocked to fetchers in the earlier
  review). MIT Press ISAL proceedings pages returned HTTP 403. The arXiv API
  returned HTTP 429 twice and once zero results for a quoted query; the arXiv
  sweep is therefore incomplete.
- Papers read in full text (arXiv HTML, via a summarising fetch, not the PDF):
  2609.10817 (Tapes Together Strong) in two passes, 2509.03534 (Prebiotic
  Functional Programs), 2506.08569 (Flow-Lenia, multispecies section only).
- Abstract-only (tagged **UNVERIFIED** where a claim goes beyond the
  abstract): 2609.19902, 2305.19504, 2503.19869, 2503.19177, 2603.08463,
  2406.09654, 2005.03742, 2305.13043, and the Semantic Scholar one-line
  summaries of the remaining citing works.
- Web pages read: brlabsgroup.com computational-life (two passes),
  jonamiki.com BFF replication.
- Nothing is cited from memory. Where a fetch summary was the only source,
  the claim is attributed to the fetch, and numbers that the summary could
  not find are marked "not stated".

Terms used below:

- *Soup*: a population of fixed-length tapes paired at random (well-mixed) or
  by neighbourhood (spatial), as in BFF.
- *Emergence*: the first working self-replicator appears. *Takeover*: one
  family fills the soup. Knierim 2026 separated the two (see
  `bff-and-recent.md` §2).
- *Rule-by-rule study*: a protocol in which one physical rule (energy,
  ownership, locality, death, mutation) is switched on or off with the rest
  held fixed, and the emergence rate is reported per condition.

---

## 1. Short answer to plan question 3

No paper found adds evo's physics rules one at a time to a random-soup
protocol and reports which rule kills emergence. The nearest things are:

- The original paper's own single-factor variations (mutation rate; spatial
  grid; long tape; head start offset; instruction set), all in
  `bff-and-recent.md` §1.5–1.8 and `literature.md` §2.8, with emergence
  fractions reported only for the mutation-rate series.
- Knierim 2026's variations (byte distribution, head offset, merger caps), in
  `bff-and-recent.md` §2.
- **Tapes Together Strong (Jha et al., arXiv 2609.10817, Sep 2026)**: a Z80
  soup with per-instruction energy (c = 1 per op), an energy injection per
  epoch (ε = 24), execution speed proportional to energy share, a lossy
  STEAL op, and well-mixed versus 2D-grid pairing. Energy *is* in this
  system, and self-replicators "naturally emerge over time" in every reported
  condition. The paper does not report emergence time or emergence fraction,
  and does not compare energy-on with energy-off. It does report one
  condition in which a resource rule kept the soup at "basic, low-complexity
  replicators": uneven energy injection in a well-mixed population (§2 below).
  So energy has been added to a soup and did not kill emergence at ε = 24,
  c = 1, 32-byte tapes; but no one has found the energy level at which it
  does, and no one has tried ownership, write protection or death-by-energy.
- brlabsgroup's browser reproduction (§4) varies head position, mutation
  rate, tape-edge mode and bracket handling, but calls its sweeps "in
  progress" and gives rates only for head position.

Energy as a rule that *kills* emergence is therefore a documented gap.
Ownership and write protection as rules in a soup are a gap with no near
neighbour at all.

---

## 2. Jha, Cicala, Agüera y Arcas, Richards, Jaques, Kleiman-Weiner, Niklasson 2026, "Tapes Together Strong: The Co-evolution of Computation and Cooperation"

arXiv 2609.10817, submitted 9 Sep 2026, cs.MA. https://arxiv.org/abs/2609.10817
Full text read via https://arxiv.org/html/2609.10817 (fetch summary, two
passes). The same Google group as *Computational Life* plus Cicala's
co-authors; "Autopoietic Game Theory" is their name for the framework.

### 2.1 Substrate and protocol

All from https://arxiv.org/html/2609.10817.

- 16,384 programs of 32 bytes, Z80 machine code, initialised as "32-byte
  sequences of completely random bytes".
- Pairs are concatenated into "a single 64-byte cyclic shared memory tape".
- Two topologies: "well-mixed pool (uniform random pairings)" and "2D spatial
  grid (pairings restricted to the four immediate horizontal and vertical
  neighbors)".
- Background mutation μ = 1/128 per byte; μ = 0 in the invasion assays.
- Petri-dish assays ran 10^6 epochs; α/δ sweeps used 10 seeds per cell.
  Seed counts for the other experiments are "inconsistently reported"
  (fetch summary). **UNVERIFIED** beyond that.
- Step budget per interaction: not stated in the text the fetch saw.
  Execution within a pair is asynchronous: "the probability that program i
  executes the next instruction instead of program j is exactly
  E_i/(E_i+E_j)".

### 2.2 The energy rule (the part that matters for evo)

- "Every operation costs exactly c = 1 unit of energy; if a program attempts
  an invalid instruction, the emulator safely advances the program counter,
  but the energy cost is still consumed."
- "Every program receives a baseline energy injection (ε = 24)" per epoch.
  In the task variant, energy is "only provided if an agent's reserves fall
  below a strict threshold".
- Bounds: "at most E_max = 255 units of energy at any given time and at least
  E_min = 0".
- Running out: a program with E = 0 has execution probability zero in the
  pair. The paper does not say the program is removed or "dies" (fetch
  summary; **UNVERIFIED** whether a zero-energy tape can still be overwritten,
  which it presumably can since writes are by the partner).
- Whose account is charged: two modes, "CPU-as-Agent, where operation costs
  are deducted from the actively executing program's budget, and
  Tape-as-Agent, where costs are deducted from the accessed memory segment,
  regardless of executing CPU." Tape-as-Agent is evo's E008 `--charge-owner`
  (the owner of the executed byte pays), published by this group six days
  before E008 was run (E008 commit 461b143, 2026-10-07; arXiv v1 2026-09-09).
- Whether a copy inherits energy, or energy is attached to the tape slot, is
  not stated (fetch summary). **UNVERIFIED**.
- "an efficient replicator in this substrate can be handcrafted in just
  L = 11 bytes", so one replication costs about 11 energy units against an
  income of 24 per epoch. The fetch found no measured length for evolved
  replicators.

### 2.3 The stealing rule

- A STEAL instruction "attempts to drain δ energy from the partner and absorbs
  that energy with efficiency α = 0.8", so "each successful steal destroys
  (1−α)·δ energy from the system".
- Programs that execute STEAL during replication are labelled defectors
  (DD), the rest cooperators (CC). Payoff per interaction, Table 1:
  CC vs CC ε − L·c; CC vs DD ε − L·c − δ; DD vs CC ε − L·c + α·δ;
  DD vs DD ε − L·c − (1−α)·δ.

### 2.4 Conditions and outcomes

| Condition | Rules | Replicators emerged | Reported result |
|---|---|---|---|
| RQ1 well-mixed, uniform ε | μ = 1/128, ε = 24, δ and α varied | yes | STEAL "heavily suppressed" in all configurations |
| RQ1 dynamic stealing | δ set by evolved registers | yes | converges "to safely suppressed levels" |
| RQ2 invasion, μ = 0 | 1% replicators seeded + 1% stealers | yes (seeded) | defectors "a minority ... across the board" |
| RQ2 α/δ sweep | α ∈ {0.25, 0.5, 0.75, 0.95}, δ ∈ {4, 8, 16, 24, 32, 64}, 10 seeds | yes | defector share weakly sensitive to α; α·δ product r = 0.14, p = 0.03 |
| RQ3 spatial vs well-mixed | 2D grid, μ = 1/128, uniform ε | yes, both | spatial has higher high-order entropy (d = 2.81), lower edit distance (d = 7.32) |
| RQ4 asymmetric ε | uneven injection, both topologies | spatial only reaches complex replicators | well-mixed "collapse"; spatial keeps higher terminal energy (d = 8.98) and complexity (d = 3.54) |
| RQ5 math tasks | sequential social dilemma, energy threshold 25% | yes | solo task suppressed, joint task optimised |
| Replication dilemma | δ = 0, CPU-as-Agent vs Tape-as-Agent | yes, both | spatial evolves "interdependent, mutualistic" strategies |

Marginal defector proportion by δ (Table 3): δ = 4: 0.111 ± 0.036; 8: 0.168;
16: 0.313; 24: 0.075; 32: 0.226; 64: 0.300 (SE 0.027–0.052). By α (Table 2):
0.169–0.213, flat.

### 2.5 What it says about emergence under energy

- "When our simulation begins with a computational soup of entirely random
  bytes, self-replicating programs naturally emerge over time." No epoch
  count, no fraction of seeds, no comparison of ε values or of energy-on
  versus energy-off (second fetch pass, which looked for exactly this).
- The one resource rule that stalled complexity: "Under these systematic
  inequalities, well-mixed populations remain stuck as basic, low-complexity
  replicators ... cannot rely on a predictable baseline influx", while the
  spatial grid allowed "efficient, cooperative replicators". This is a
  statement about complexity after emergence, not about emergence.
- "As free energy increases, the incentive to execute complex math tasks
  diminishes" (p < 0.001).

### 2.6 What the authors say is missing

Quoted from the fetch of the Discussion: "Our simulations are limited to a
simplified Prisoner's Dilemma and a Z80 assembly substrate." "Different
instruction densities and hardware architectures may change replication costs
and starvation thresholds." "We also assume unrestricted read and write
access to partner memory ... many systems restrict access to an agent's
internal state." Open: "Why was a cooperative strategy even discoverable from
scratch"; "Testing the range between shared and private computation will help
determine when these dynamics persist."

### 2.7 Plateau

Not measured as such. The complexity measures are high-order entropy and
edit distance between tapes; no activity statistic, no genome-length
trajectory beyond the 32-byte cap.

### 2.8 What it means for evo

- This is the first soup from the BFF group with per-instruction energy, and
  the first with the owner-pays accounting of E008. Replicators still emerged
  at c = 1, ε = 24, L = 11; evo's Phase 4 energy step should start from this
  ratio (income per epoch about 2× the cost of one replication) and tighten
  it until emergence fails, which nobody has done.
- Their "unrestricted read and write access to partner memory" is exactly
  the rule evo's ownership and write protection remove; they name it as the
  untested dimension.
- STEAL is a designed opcode, so their parasitism is an instruction, not an
  evolved behaviour; evo's intruders use ordinary writes. The two are not
  the same experiment.
- Scale for plan question 5: 16,384 × 32 bytes, 10^6 epochs, 10 seeds per
  sweep cell, arXiv preprint (no venue yet).

---

## 3. Other works citing *Computational Life* (Semantic Scholar sweep)

Source: https://api.semanticscholar.org/graph/v1/paper/arXiv:2406.19108/citations?fields=title,year,externalIds,venue,abstract&limit=200.
24 works returned. Only the one-line abstract summaries were read unless a
separate fetch is listed. All **UNVERIFIED** beyond the abstract.

Already covered in `bff-and-recent.md`: 2607.01483 (Knierim), 2607.09211
(Cicala), 2412.17799 (ASAL; now also *Artificial Life* journal,
https://doi.org/10.1162/artl.a.8 per OpenAlex), 2603.08463 (Barricelli
workshop; abstract re-read below).

Relevant and new:

- **2609.10817 Tapes Together Strong**: §2 above.
- **2509.03534 Vimal, Mathis, Weimer, Forrest 2025, "Prebiotic Functional
  Programs: Endogenous Selection in an Artificial Chemistry"**: §5.1 below.
- **"Symbiogenesis: from Barricelli's Legacy to Collective Intelligence"**,
  GECCO Companion 2026, https://doi.org/10.1145/3795101.3814707: the
  published form of the ALICE workshop report. The arXiv abstract
  (https://arxiv.org/abs/2603.08463, 9 Mar 2026; Ashford, Cvjetko, Löffler,
  Sakallioglu, Valerio, Tataryn, Hartl, Pio-Lopez, Nichele) describes
  replicating Barricelli's 1953 1D numerical organisms, extending to 2D, and
  "preliminarily testing DNA-norms". Substrate is a CA of integers, not an
  instruction soup; the abstract does not give an emergence rate. One line:
  symbiosis-first framing, no rule-by-rule data.
- **2607.02954 "Microcosmos: Reimagining Artificial Life for the GPU Era"**,
  ISAL 2026: elastic filaments in viscous fluid; physical, not instruction
  substrate. Not relevant to emergence from code.
- **2607.09747 "Life as Plasmas"**, ISAL 2026, https://doi.org/10.1162/ISAL.a.939:
  complex plasmas "lack informational heredity". Irrelevant.

Irrelevant (one line each, from the abstract summaries): 2607.28250
(catalytic origin-of-life model, causal emergence); "Selection for Function,
Persistence, and Darwinian Evolution" (Peer Community Journal 2026,
https://doi.org/10.24072/pcjournal.753, conceptual); "Monad+" (Journal of Big
History); an integrated-STEM pedagogy paper; 2606.23874 (RNN structure);
2604.13934 (autopoietic software architectures); "Is Every Cognitive
Phenomenon Computable?" (Mathematics 2026); "Is the emergence of life and of
agency expected?" (Phil Trans B 2025, https://doi.org/10.1098/rstb.2024.0283,
autocatalytic sets); 2509.23212 (minimal agent-environment model); 2508.11423
(time and self-reference); bioRxiv 10.1101/2025.07.29.667458 (niche
construction before replication); 2507.13253 (adaptive threshold networks);
2404.04374 (information handling); 2404.03685 (Fermi paradox); two entries
with no identifiers ("Indeterminism in Large Language Models", "On the
feasibility of a nonadaptive–nonsequential abiogenesis").

Also found by search, not in the citation list: **2503.19869 Vidunas &
Vaicekauskas 2025, "Conway's game Life perturbed"**
(https://arxiv.org/abs/2503.19869): stochastic perturbation of Life patterns
on finite grids; not about replicator emergence. **2503.19177 Fischbacher
2025, "Life at the Boundary of Chemical Kinetics and Program Execution"**
(https://arxiv.org/abs/2503.19177, cond-mat.dis-nn, 47+17 pages): Markov
plus ODE framework for polymer sequence kinetics, chemically implemented
Turing machine near the Landauer bound; thermodynamic cost of computation
framed in chemistry, no random-soup emergence result in the abstract.
**UNVERIFIED** whether the body contains one.

---

## 4. Independent reproductions with parameter variation

### 4.1 brlabsgroup, "Computational Life" (browser reproduction, 2026)

https://www.brlabsgroup.com/research/computational-life/ (two fetch passes).
A demo with documentation, "© 2026", no author names, "source on GitHub",
plus a Node reference implementation for larger populations. Not a paper.

- Soup: "a few thousand" 64-byte programs (versus about 131,000 in the
  paper); pairs are 128 bytes.
- Parameters varied: second-head start position (0 vs 64); mutation rate
  (zero, low, high); tape-edge behaviour (wrap, invalidate, saturate);
  unmatched-bracket handling (strict vs lenient).
- Rates given: head at 64, "roughly a third of runs"; head at 0, emergence
  "rare" in this smaller soup; "a few percent" of runs show background
  fertility from noise. The page calls the quantitative sweeps "in
  progress" and gives no numbers for the mutation, edge or bracket
  conditions.
- Their claim: "the position of a copying head is half of the replication
  problem", which matches Knierim's CUST64 density result
  (`bff-and-recent.md` §2.2) and *Computational Life*'s long-tape offset
  finding.
- Three mutation regimes reported qualitatively: zero mutation, replicators
  emerge and dominate; low mutation, "dozens of lineages compete with
  quasispecies structure"; high mutation, "collapses as the error threshold
  is exceeded". No thresholds stated.
- Minimal replicator "about five bytes"; operator density in random bytes
  "near 4%" (10 of 256).

For evo: the only reproduction that varies rules one at a time, and it has
not published the rates. Head start position is the one rule it has
quantified, and it is the rule evo's start-execution question (PLAN §9) maps
onto.

### 4.2 Jonas Werner, "BFF - Emergent Complexity experiment" (7 Mar 2026)

https://jonamiki.com/posts/bff-emergent-complexity-experiment/ (fetched;
upgrades the **UNVERIFIED** tag in `bff-and-recent.md` §3.7).

- C with OpenMP, Python orchestration. 1,024 programs of 64 bytes, 128-byte
  pairs. Mutation rate not stated. 5 seeds × 50,000 epochs (51.2 million
  interactions per seed).
- Emergence: seed 3 at about 40 million interactions (smooth); seed 5 at
  about 20 million, then a crash and rebuild at the same point. The page as
  fetched gives timings for these two seeds only; the earlier note's "5 of 5
  seeds" is not confirmed by this fetch (**UNVERIFIED**).
- Detection: mean operations per interaction rising from about 700 to
  6,000–12,000, and compressibility dips, "the fingerprint of regime change".
- Author's own caveat: "not a perfect replica".

For evo: 1,024 tapes is close to evo's 128 patches × 512 bytes = 64 KiB in
total bytes; emergence at 2–4 × 10^7 interactions in a soup this small says
the Phase 4 harness does not need 2^17 tapes to see a transition, only
patience.

---

## 5. Self-replication emergence in other substrates since 2020

### 5.1 Vimal, Mathis, Weimer, Forrest 2025, "Prebiotic Functional Programs: Endogenous Selection in an Artificial Chemistry"

arXiv 2509.03534, 27 Aug 2025, cs.FL; Semantic Scholar lists the venue as
IEEE Symposium on Artificial Life (ISAL 2025). https://arxiv.org/abs/2509.03534.
Full text via https://arxiv.org/html/2509.03534 (fetch summary).

- Substrate: AlChemy, untyped λ-calculus. 5,000–6,000 expressions per
  reactor; two expressions chosen at random, one applied to the other,
  reduction allowed 8,000 steps or a 1,000-vertex tree; products replace
  random expressions (constant population). 16–100 runs for small
  experiments, 1,000 runs for large; 10^6 collisions per run.
- Initial soups are the combinators S, K, I (and sometimes P), or random
  expressions.
- "Endogenous selection": second-order "amplifier" expressions that encode
  unit tests; "application of the amplifier to a function f will return
  copies of f if f passes the test. Otherwise ... the amplifier will return
  itself." No external fitness function, but the amplifiers are hand-written
  and seeded.
- Results: successor reached ≥ 20% of the soup in 50% of runs by 10^6
  collisions given ≥ 5% amplifiers and ≥ 10% targets at start; add-two
  emerged reliably over 1,000 runs with 15% amplifiers; addition needed the
  P combinator and two amplifiers; "Without amplifiers, no runs exceeded 20%
  target function population".
- On copiers: "most functions that do not replicate themselves are fragile";
  quines are "notoriously rare and hard to construct". No spontaneous
  emergence of self-copiers is reported, and no suppression of them either
  (the fetch found neither).
- Missing, per authors: amplification "solves persistence, not generation"
  ("add" rarely emerges on its own); untyped λ is inefficient; "trickster
  functions" pass incomplete tests; soup-size interactions not understood.

For evo: AlChemy revisited still does not get replicators from a random
soup; it gets persistence of seeded functions through a seeded copier
(the amplifier). It is the λ-calculus analogue of evo's seeded ancestor, not
of Phase 4.

### 5.2 Jain, Reimers, Nichele 2026, "Self-Replicating Neural Cellular Automata: Quantifying Emergent Phenotypic and Genotypic Diversity in an Open-Ended Substrate"

arXiv 2609.19902, 17 Sep 2026, q-bio.PE. https://arxiv.org/abs/2609.19902.
Abstract only; **UNVERIFIED** beyond it.

- Every pixel of a two-channel CA grid "carries a tiny neural network (an
  agent) that senses its Moore neighborhood"; cells survive only by
  self-replication, with weight mutation on cloning.
- Populations grow "from initial seeded founders"; not seedless emergence.
- Scale: 200 × 200 grid, 24 long runs of 1,000 generations, 1,680 smaller
  sweep runs; 20 of 24 long configurations persisted.
- Finding: "raising phenotypic diversity collapses genotypic diversity and
  vice versa".

For evo: seeded, so irrelevant to Phase 4; its diversity trade-off measure is
cluster 3 material.

### 5.3 Plantec, Hamon, Etcheverry, Chan, Oudeyer, Moulin-Frier 2025, "Flow-Lenia: Emergent evolutionary dynamics in mass conservative continuous cellular automata"

*Artificial Life* 31(2): 228–248, 2025; arXiv 2506.08569.
https://arxiv.org/abs/2506.08569; multispecies section read via
https://arxiv.org/html/2506.08569 (fetch summary).

- Lenia with mass conservation, and model parameters embedded in the
  dynamics so that different "species" can share a grid.
- Multispecies runs are seeded: "64 creatures" as 20 × 20 patches with random
  parameters; 256 × 256 grid, 500,000 steps, 5 seeds per condition, 3
  channels and 45 kernels.
- Evolutionary activity (Bedau–Packard) declined with mutation rate as power
  laws, slopes γ = −0.5 and γ = −0.71 for the two measures.
- Missing, per authors: species definition (each parameter point counted as
  a species), phenotype-based species, individuality measures, assembly
  theory.

For evo: seeded, continuous, no emergence-from-noise claim; its use of
evolutionary activity against mutation rate is a template for cluster 3.

### 5.4 Bo Yang 2023, "Self-Replicating Hierarchical Structures Emerge in a Binary Cellular Automaton"

arXiv 2305.19504, 31 May 2023, nlin.CG. https://arxiv.org/abs/2305.19504.
Abstract only; **UNVERIFIED** beyond it.

- A binary, rotationally symmetric, Moore-neighbourhood rule ("Outlier")
  found by genetic programming. From "sparsely populated random initial
  conditions", clusters appear, some "periodically self-duplicate", and
  when the start is sparse enough they coalesce into larger self-replicating
  formations: "emergent self-replication across two spatial scales".
- No rates, grid sizes or seed counts in the abstract.

For evo: the only post-2020 CA result claiming replicators from random
initial state with no seeding, and the rule was searched for, not given.
The condition "sufficiently sparse" is a density rule of the kind Phase 4
would vary.

### 5.5 Sinapayen 2023, "Self-Replication, Spontaneous Mutations, and Exponential Genetic Drift in Neural Cellular Automata"

ALIFE 2023, https://doi.org/10.1162/isal_a_00591; arXiv 2305.13043
(https://arxiv.org/abs/2305.13043). Abstract only (MIT Press page 403);
**UNVERIFIED** beyond it.

- NCA patterns self-replicate with "spontaneous, inheritable mutations" and
  drift exponentially from the ancestor "even when the automaton is
  deterministic"; the models were "not explicitly trained for mutation or
  inheritability". The abstract does not say whether replication itself was
  trained for; the title's framing implies the NCA was trained to replicate
  (**UNVERIFIED**).

For evo: trained replicators; not a random-soup result.

### 5.6 Barbieux & Canaan 2024, "Coralai"

ALIFE 2024; arXiv 2406.09654 (https://arxiv.org/abs/2406.09654). Abstract
only. NCA ecosystems evolved by HyperNEAT with slime-mould-like physics;
competition, resource cycles and symbiosis reported; the abstract does not say
whether organisms emerge from random state. Irrelevant to seedless emergence.

### 5.7 Chan 2020, "Lenia and Expanded Universe"

ALIFE 2020; arXiv 2005.03742 (https://arxiv.org/abs/2005.03742). Abstract
only. Self-replication listed among new phenomena found "using semi-automatic
search e.g. genetic algorithm"; the abstract does not say whether it arises
from random initial conditions. A search-result snippet (not the paper)
says replication in extended Lenia "turns out to be not rare" and can
"develop out of debris" (**UNVERIFIED**).

### 5.8 Kruszewski & Mikolov, Combinatory Chemistry

Already in `bff-and-recent.md` §3.3 (*Artificial Life* 27(3–4), arXiv
2103.08245). The earlier 2020 version is arXiv 2003.07916 ("Combinatory
Chemistry: Towards a Simple Model of Emergent Evolution",
https://arxiv.org/pdf/2003.07916), per search results. Nothing newer found.

### 5.9 Searched for and not found

- Any Brainfuck, Forth, Z80 or 8080 soup paper beyond the three Google
  papers and the two reproductions above. Search:
  `Forth OR Z80 OR 8080 "primordial soup" self-replicating programs emergence 2025 2026`
  returned only 2406.19108 and 2607.09211.
- RISC-V, WebAssembly, Lisp, Piet or stack-machine soups: nothing found
  (search returned LLM kernel-optimisation papers).
- SUBLEQ follow-ups: nothing beyond the original counterexample.
- Chemlambda or graph-rewriting chemistry with a 2024–2026 emergence result:
  search returned only Buliga's 2014–2020 papers (arXiv 1403.8046,
  2005.06060, 2007.10288); not read.
- Particle Lenia self-replication: nothing beyond the Flow-Lenia and
  Evoloops-review results already noted.
- "Energy" or "instruction cost" soups: the search returned Cicala 2026 and
  Fischbacher 2025 only; Tapes Together Strong was found through the
  citation sweep, not search.

---

## 6. Minimal replicator length as a predictor of emergence rate

No paper found measures minimal replicator length against emergence rate
across substrates as a controlled variable. What exists:

| Source | Substrate | Minimal replicator | Emergence | Measured how |
|---|---|---|---|---|
| *Computational Life* (`bff-and-recent.md` §1.8) | BFF / Forth / SUBLEQ / RSUBLEQ4 | about 5 / 1 / 60 / 25 bytes | 40% / almost all / never / not reported | hand-crafted minimum; emergence from runs |
| Knierim 2026 (`bff-and-recent.md` §2.2) | BFF | n/a | 2.9 × 10^7 tries per replicator from uniform bytes down to 9.4 × 10^4 with heads 64 apart | replicator density by sampling |
| Tapes Together Strong (§2) | Z80 with energy | 11 bytes hand-crafted | "naturally emerge", rate not stated | hand-crafted |
| brlabsgroup (§4.1) | BFF | "about five bytes" | a third of runs with head at 64 | hand-crafted; browser runs |
| C G et al. 2017 (`bff-and-recent.md` §3.5) | Avida | exhaustive minimal-genome set | non-uniform takeover | enumeration |

So the length-versus-rate relation in `literature.md` §4.5 remains a
cross-paper inference from hand-crafted minima, with Knierim's densities the
only direct measurement, and only in BFF.

---

## 7. UNVERIFIED items (collected)

- Tapes Together Strong: seed counts outside the α/δ sweep; step budget per
  interaction; fate of zero-energy tapes; whether copies inherit energy;
  everything read through a fetch summary rather than the PDF.
- Jonas Werner: timings for seeds 1, 2 and 4; "5 of 5 seeds" from the
  earlier note.
- Bo Yang 2023, Jain 2026, Sinapayen 2023, Chan 2020, Coralai, Fischbacher
  2025, Vidunas 2025, Barricelli/GECCO 2026: abstract only.
- The 20 irrelevant citing works: one-line summaries only.
- The arXiv API sweep (429 twice) and MIT Press ISAL 2024–2026 proceedings
  (403) were not completed; a soup paper in ISAL proceedings not indexed by
  Semantic Scholar as citing 2406.19108 would have been missed.

---

## 8. Design implications for evo (cluster 2)

1. Phase 4's "add energy" step has one published anchor: c = 1 per op,
   ε = 24 per epoch, 32-byte tapes, 11-byte replicator, and emergence still
   happens (https://arxiv.org/abs/2609.10817). Start there and reduce ε (or
   raise c) until emergence stops; that curve does not exist anywhere.
2. The Tape-as-Agent mode is E008's rule, in a system where replicators
   emerged. Their tapes are 32 bytes with one 64-byte pair per epoch, so
   the "store smaller than one pass of the loop" failure mode in PLAN §9
   does not arise for them; it is a consequence of evo's 512-byte patches
   and long-running bodies, not of the rule.
3. Ownership and write protection: the one paper with energy names
   "unrestricted read and write access to partner memory" as its untested
   assumption. That is Phase 4's ownership step, and it has no prior.
4. Head/IP start position is the single rule with a quantified effect in
   both Google's and brlabsgroup's data; evo's start-execution rule (PLAN
   §9) should be swept before energy.
5. For the BFF calibration itself, 1,024 tapes sufficed for a transition at
   2–4 × 10^7 interactions in one reproduction; the 2^17 soup is for rate
   statistics, not for existence.

---

## Verification from PDF (2026-10-09)

Source: arXiv 2609.10817v1 PDF (37 pages), text extracted page by page
with pypdf; page numbers below are PDF/print page numbers. Nothing here
comes from a secondary source.

1. **Cost accounting, CPU-as-Agent vs Tape-as-Agent: VERIFIED.** App. A.2,
   p. 15: "We evaluate two distinct boundary definitions: CPU-as-Agent,
   where operation costs are deducted from the actively executing
   program's budget, and Tape-as-Agent, where costs are deducted from the
   accessed memory segment, regardless of the executing CPU." Worked
   example, same page: "rather than executing standard self-writes, CPU A
   navigates to Tape B's segment to execute writes back onto Tape A,
   forcing B's budget to absorb the reproductive cost (Figure 8, Right)."
   So under Tape-as-Agent the owner of the segment holding the executed
   instruction pays the whole cost; there is no split and the executor
   pays nothing. (Note "accessed memory segment" means where the
   instruction sits, not the write target: in the example the writes land
   on A but B pays.) The paper never says which mode the main-text runs
   use; Table 1 (p. 4) charges the replication cost Lc to the row player,
   which is CPU-as-Agent accounting, and A.4 (p. 18) calls CPU mode the
   "CPU-based energy accounting mode" alongside Tape mode as two settings
   of the same system. The per-op cost is "Every operation costs exactly
   c = 1 unit of energy; if a program attempts an invalid instruction, the
   emulator safely advances the program counter, but the energy cost is
   still consumed." (Sec. 3, p. 4; Table 5 p. 29 "Write cost 1").

2. **Energy-off run / emergence time or fraction: NOT IN PAPER.** No Z80
   run has the per-op cost disabled. The only "costs disabled" statement
   is for the toy Prisoner's Dilemma of Sec. 5, p. 28: "Mutation and
   explicit replication costs are disabled in both experiments." The
   nearest Z80 control is STEAL disabled: "we first isolate the
   Replication Dilemma by disabling the STEAL operation (delta = 0)"
   (p. 15). Emergence is asserted without a number: "When our simulation
   begins with a computational soup of entirely random bytes,
   self-replicating programs naturally emerge over time, mirroring prior
   work in artificial life [3]." (Sec. 4, p. 5). The only time stamps are
   the Figure 3b panels on the uneven grid, labelled "Epoch 0", "Epoch
   30k", "Epoch 420k" (p. 6), with the caption "initially random,
   non-functioning tapes give way to efficient self-replicators that
   first emerge in high-energy regions and later spread into lower-energy
   areas." No fraction of seeds reaching replication is given. The 99.3%,
   95.5%, 83.7% etc. figures (Figure 8, p. 15) are fixation rates of
   seeded replicators invading a naive soup (1% seeded), not emergence
   from random bytes.

3. **Fate of zero-energy tapes; inheritance on copy: VERIFIED (formal
   model).** Bounds: "Each program can have at most Emax = 255 units of
   energy at any given time and at least Emin = 0 units of energy."
   (p. 4). Execution share is "exactly Ei/(Ei+Ej)" (p. 4), so a tape at 0
   simply never executes while its partner has energy. The halt condition
   is on the pair total, not the individual: "If a pair runs out of
   energy (Etot <= 0), computation halts immediately, leading to
   starvation." (C.4, p. 29); "If Etot <= 0, the system starves
   (dt -> infinity) and operations cease." (B.1, p. 22). Starved tapes
   are not removed or reset: "starvation still returns two 32-byte
   programs after the split, but produces no faithful defector overwrite
   event in that encounter." (p. 26) and "If starvation occurs before
   either program completes L targeted opponent-writes, the tape splits
   into a recombination of both programs, yielding 0 viable copies of
   either of the originals." (p. 22). Inheritance, B.1 p. 22: "If program
   i successfully targeted and completed L writes into j's segment, the
   split yields two intact copies of i. The original half retains its
   remaining Ei as residual energy, and the newly written half inherits
   the remaining Ej as its residual energy." So energy is not split on
   copy: each slot keeps its own residual; the copy takes the victim's
   leftover energy. Residual carries across epochs: "Ei = min(epsilon +
   Ei,residual, Emax)" (p. 22). Caveat: this is stated in the Appendix B
   formal model; C.4 does not restate it for the emulator, but Sec. 3
   says programs "accumulate surplus across epochs" (p. 4) and Sec. 3
   also says "energy left on the partner tape remains available for that
   partner's future computation" (p. 5), consistent with it.

4. **Seeds, epochs, step budget: VERIFIED.** Table 5, p. 29 ("Base
   hyperparameters kept fixed across experiments unless specified
   otherwise"): "# of Seeds 10; Grid side length (Lpop) 128; Program
   length 32 bytes; Shared tape length 64 bytes; Initial energy budget
   255; Energy cap (Emax) 255; Background energy threshold 255
   (Non-math); Background energy regeneration (epsilon) 24; Mutation
   rarity 1/128; Write cost 1; Absorption efficiency (alpha) 0.8; Maximum
   Step count 512." Population 128^2 = "16,384 programs" (p. 3). Epochs,
   C.5 p. 29: "Non-math Experiments: The main evolutionary runs were
   executed for 6 million epochs. The subsequent 'petri dish' invasion
   assays (seeding mutants into naive soups) were run for 1 million
   epochs." and "Math experiments: The task-driven experiments were run
   for 10 million epochs". A.2 invasion assay: "seeding 1% representative
   replicators into a naive random soup (10^6 epochs, mu = 0, epsilon =
   24)" (p. 15). alpha/delta sweep: "We simulated 10 seeds of a
   well-mixed population" (p. 6). Toy PD (Sec. 5): "each experiment uses
   N = 1000 agents, runs for 500 generations, and is repeated across 1000
   independent seeds." (C.1, p. 27). Step budget per pairing: "epochs are
   strictly bounded by a maximum step count, after which execution is
   terminated" (C.4, p. 29) with the value 512 from Table 5; the formal
   model calls it Tmax (p. 22). Compute: "All of our simulations used 256
   CPU cores for every seed/hyperparameter combination." (p. 29).
   Preliminary epsilon sweep: "{12, 16, 24, 32, 64} ... We found if
   epsilon is too low, agents starve before they can replicate." (C.6,
   p. 29), no numbers per value.

5. **11-byte handcrafted replicator: VERIFIED claim, emergence rate NOT
   IN PAPER.** Sec. 3, p. 4: "Programs lack a built-in replication
   command; to reproduce, they must evolve code which explicitly
   overwrites the opponent's tape segment with their own code. Because an
   efficient replicator in this substrate can be handcrafted in just
   L = 11 bytes, the baseline epsilon = 24 provides sufficient energy for
   non-stealing tapes to safely replicate and accumulate surplus across
   epochs (epsilon > Lc)". The 11-byte program is not listed, and no rate
   of its (or any replicator's) emergence from random bytes is reported.
   The paper also mentions degenerate "structurally unstable 2-byte
   replicators that garble the shared tape" (p. 15) arising in collapsed
   Tape-as-Agent lineages. The D.1 trace (p. 31-37) shows an evolved
   replicator using LDIR-style block copies (bytes "ed b0", "ed b8").

6. **"Basic, low-complexity replicators": VERIFIED.** RQ4, p. 7: "we
   evaluated an asymmetric grid where the background energy epsilon
   varied significantly depending on an agent's physical location
   (Figure 21). Under these systematic inequalities, well-mixed
   populations remain stuck as basic, low-complexity replicators with
   lower energy because they cannot rely on a predictable baseline
   influx. In stark contrast, populations restricted to local spatial
   interactions successfully overcome the environmental asymmetry to
   evolve complex, cooperative replicators, maintaining significantly
   higher terminal energy (Cohen's d = 8.98) and higher-order entropy
   (Cohen's d = 3.54; both p < 0.001, two-sided t-tests) (Figure 3a)."
   The comparison is well-mixed vs local (von Neumann 4-neighbour) grid
   under asymmetric injection; Figure 21 (p. 30) labels the two regimes
   "Uniform Injection (+24 per timestep)" and "Asymmetric Injection (24
   -> 0 left -> right)". Under uniform injection both topologies suppress
   stealing: "While both topologies suppress defection under these
   conditions, local spatial interactions act as a powerful evolutionary
   catalyst. Spatial assortment significantly boosts higher-order entropy
   (Cohen's d = 2.81) and lowers edit distance (Cohen's d = 7.32)" (RQ3,
   p. 7). The A.2 steal-off assay adds a second collapse case: "Lineages
   historically evolved under high energy and well-mixed topologies
   suffer total architectural collapse (Figure 9), rapidly degrading into
   structurally unstable 2-byte replicators" (p. 15), for Tape-as-Agent
   lineages only.

7. **Ownership / write protection / evolved defence: VERIFIED as absent
   mechanism, with overwrite-as-defence reported.** No ownership or write
   protection exists in the substrate; the Limitations paragraph names it
   as untested (p. 10): "We also assume unrestricted read and write
   access to partner memory. Although this resembles biological
   horizontal gene transfer or AI agents sharing prompts and
   problem-solving harnesses, many systems restrict access to an agent's
   internal state. Testing the range between shared and private
   computation will help determine when these dynamics persist." The only
   defence against STEAL that the paper reports is out-executing and
   overwriting the thief, RQ1 p. 6: "a cooperative tape can utilize its
   speed advantage to stop a defector mid-execution and overwrite its
   malicious code entirely"; D.1 p. 31: "even after the cooperator's
   energy drops below the defector, it is able to overwrite the malicious
   steal operation, at first with code that forces the defector to jump
   to a HALT operation, and then with its functioning, replicator code."
   A.3 p. 16 uses the words "robust defenses against parasitism" and
   "They fiercely resist exploitation, permanently trapping malicious
   actors at a distinct minority frequency (Figure 13)", meaning the
   population-level outcome, not a protective instruction. No resistance
   to partner execution under Tape-as-Agent (the B-pays-for-A exploit of
   A.2) is reported; the paper only says the exploit "stabilizes almost
   exclusively under local spatial topologies" (p. 15).

8. **Date, authors, affiliations, venue: VERIFIED.** Stamp on p. 1:
   "arXiv:2609.10817v1 [cs.MA] 9 Sep 2026"; footer "Preprint." Authors
   (p. 1): Kunal Jha (1,2, "Work done as a student researcher at
   Google"), Francesco Cicala (2), Blaise Aguera y Arcas (2), Blake Aaron
   Richards (2,3), Natasha Jaques (1,4, equal advising), Max
   Kleiman-Weiner (1,4, equal advising), Eyvind Niklasson (2, equal
   advising). Affiliations: "1 Dept. of Computer Science, University of
   Washington. 2 Google Paradigms of Intelligence. 3 School of Computer
   Science, McGill University; Mila. 4 Google DeepMind." No venue is
   named anywhere in the PDF. PDF metadata: license CC BY 4.0; emulator
   is "a modified Z80 emulator based on the open-source implementation
   available at https://github.com/superzazu/z80" (C.3, p. 28); no code
   release URL for the paper itself is given.

Net effect on Section 7 above: the first bullet's open items (seed
counts, step budget, zero-energy fate, inheritance) are now answered from
the PDF; emergence rate and the identity of the 11-byte replicator remain
unreported by the authors.
