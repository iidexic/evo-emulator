# Open-endedness metrics, the error threshold, and systems the first review missed

> Research notes, 2026-09-30. They fill gaps in [../../research-historic/Review.md](../../research-historic/Review.md).
>
> - Every fact carries a source link. Wherever possible I read the primary paper, thesis, source code or config file itself; the few secondary sources are named as such in the text.
> - Parts of B were drafted by two research sub-agents. I spot-checked their key claims against the primary sources, noted as "(spot-checked)".
> - **UNVERIFIED** marks claims I could not confirm from a primary source. They are collected at the end.
> - Some formulas come from PDFs whose text extracts badly. Where I rebuilt the typesetting by hand, the text says so.

Contents:

- A. Measuring open-endedness: A1 Bedau–Packard, A2 Channon 2024, A3 York/Tokyo categories, A4 MODES, A5 QNN, A6 phylogeny metrics, A7 compression measures
- B. Systems the first review missed: B1 Cosmos, B2 Nanopond, B3 Squirm3, B4 Evoloops, B5 AlChemy, B6 Adami's physical complexity, B7 recent CA/Lenia work
- C. The Eigen error threshold and the mutation rates Tierra and Avida actually used
- D. Design implications for evo
- UNVERIFIED list

---

## A. Measuring open-endedness

### A1. Bedau–Packard evolutionary activity statistics

**The original 1992 version: gene-level activity counted by use.**

Source: [Bedau & Packard 1992, "Measurement of evolutionary activity, teleology, and life", *Artificial Life II*](https://people.reed.edu/~mab/publications/papers/alife2.pdf). The PDF is wrapped in a MacBinary header; drop the first 128 bytes to read it.

- Each gene (allele) has a usage counter.
  - The counter goes up each time the gene is used.
  - It is inherited when the gene is copied into offspring.
  - It is reset to zero if the gene mutates.
- *N(t,u)* is the usage distribution: the fraction of genes with usage *u* at time *t*.
- *P(t,u) = Σ_{u' ≥ u} N(t,u')* is the "net persistence".
- **Evolutionary activity** is *A(t) = −[∂P(t,u)/∂u] evaluated at u = u₀*.
  - The threshold *u₀* is set high enough that useless genes are gone before they reach it.
  - Bands rising through the (t, u) plane are called **activity waves**. Each one is a useful gene cluster being used again and again.

**The 1997/1998 version: component activity counted by how long a component exists.**

This is the standard form today. Sources: [Bedau, Snyder, Brown & Packard 1997, ECAL97](https://people.reed.edu/~mab/publications/papers/ecal97.pdf) and [Bedau, Snyder & Packard 1998, "A classification of long-term evolutionary dynamics", *Artificial Life VI* pp. 228–237](https://people.reed.edu/~mab/publications/papers/alife6.pdf) (same MacBinary wrapper).

A "component" can be an allele, a genotype or a taxonomic family. The 1997 paper used whole genotypes for the Tierra-like system Evita.

| Symbol | Definition |
|---|---|
| Δᵢ(t) | 1 if component *i* exists at *t*, else 0 |
| aᵢ(t) | Σ_{τ≤t} Δᵢ(τ) if *i* exists at *t*, else 0. The time present so far, gaps not counted. |
| D(t) | #{i : aᵢ(t) > 0}, the number of components present (diversity) |
| C(t,a) | Σᵢ δ(a − aᵢ(t)), the component activity distribution |
| A_cum(t) | Σᵢ aᵢ(t) = ∫ a·C(t,a) da, total cumulative activity |
| Ā_cum(t) | A_cum(t)/D(t), mean cumulative activity ("mean activity") |
| A_new(t) | (1/D(t))·Σ_{i: a₀ ≤ aᵢ(t) ≤ a₁} aᵢ(t), new activity |

**Choosing the strip [a₀, a₁]** ([1998](https://people.reed.edu/~mab/publications/papers/alife6.pdf); formula rebuilt from garbled extraction, consistent with the paper's own numbers):

1. Collapse the activity distributions of the real run and of the neutral shadow over time.
2. Let *a\** be where the two cross. At *a\** an activity count is equally likely to come from either run.
3. Let *a_max* be the highest activity where either distribution is positive.
4. Set *a₀, a₁ = a\* ∓ 0.05·(a_max − a\*)*.

Worked example from the paper: *a\** = 2.1×10⁵, *a₀* = 1.7×10⁵, *a₁* = 2.5×10⁵.

**The neutral shadow** as defined for Echo ([1998](https://people.reed.edu/~mab/publications/papers/alife6.pdf)):

- The shadow copies "the timing and number of birth and death events" of the real run, and its mutation rate.
- Each real birth triggers a shadow birth. The shadow parent is chosen uniformly at random, and the child inherits its genotype "unless a mutation gives the child a new, unique genotype".
- Each real death kills a uniformly random shadow creature.
- To normalise, subtract the shadow's new or cumulative activity from the real run's.

**Evita's neutral model** ([1997](https://people.reed.edu/~mab/publications/papers/ecal97.pdf)) is the closest precedent to evo:

- Evita is Tierra-like, on a 40×40 grid, with parasitism blocked.
- The neutral model has only two inputs, both recorded from the real run: "mutations in the population per timestep" and "programs that reproduce per timestep".
- A reproducing program is chosen at random, and its oldest neighbour dies to make room.

**Operational definitions** ([1998 appendix](https://people.reed.edu/~mab/publications/papers/alife6.pdf); typesetting rebuilt):

- *f* is **unbounded** iff lim_{t→∞} sup(f(t))/t > 0.
- *f* is **positive** iff lim_{t→∞} (1/t)∫₀ᵗ f dt > 0.
- You cannot take limits on finite data. [Dolson et al. 2019](https://cse.msu.edu/~dolsonem/pdfs/modes_paper.pdf) and [Taylor et al. 2016](https://www.tim-taylor.com/papers/taylor2016openended.pdf) both recommend fitting bounded and unbounded models and keeping whichever fits best, instead of eyeballing plateaus.

**The classes.** The 1998 paper defined 3. Later work extended the scheme, which is why it is often described as "classes 1 to 4".

[1998 Table 1](https://people.reed.edu/~mab/publications/papers/alife6.pdf):

| Class | Adaptive activity | D | A_new | Ā_cum | Seen in |
|---|---|---|---|---|---|
| 1 | none | bounded | zero | zero | Echo with mutation rate near 0 or near 1; all neutral shadows |
| 2 | bounded | bounded | positive | bounded | Echo in its best region of parameter space |
| 3 | unbounded | unbounded | positive | bounded | Phanerozoic fossil record only |

The authors wrote that they "suspect that no existing artificial evolving system has class 3 dynamics".

Later additions:

- [Channon 2001](http://www.channon.net/alastair/geb/ecal2001/channon_ad_ecal2001.pdf) split class 3 into 3a (unbounded D), 3b (unbounded Ā_cum) and 3c (both). Geb was classified 3b.
- Skusa & Bedau added an "unbounded, uncreative" class: bounded D, unbounded Ā_cum, zero A_new. This is the signature of stabilising selection or a stable ecology. I know it only from secondary sources, [Standish's Ecolab paper](https://arxiv.org/pdf/nlin/0004026) and [MODES Table 1](https://cse.msu.edu/~dolsonem/pdfs/modes_paper.pdf), so the attribution is **UNVERIFIED**.

The merged table in [MODES Table 1](https://cse.msu.edu/~dolsonem/pdfs/modes_paper.pdf):

| Class | Label | Ā_cum (median) | A_new | D |
|---|---|---|---|---|
| 1 | None | zero | zero | bounded |
| 2 | Uncreative | unbounded | zero | bounded |
| 3 | Bounded | bounded | positive | bounded |
| 4a | Unbounded | bounded | positive | unbounded |
| 4b | Unbounded | unbounded | positive | bounded |
| 4c | Unbounded | unbounded | positive | unbounded |

[Standish](https://arxiv.org/pdf/nlin/0004026) found that Ecolab's move from class 3 to class 2 at high mutation "corresponds to an error threshold".

**What the statistics have found:**

- **Echo:** only classes 1 and 2 ([1998](https://people.reed.edu/~mab/publications/papers/alife6.pdf)).
- **Evita:** after early gains, "the bulk of this simulation consists of a random drift among genotypes that are selectively neutral" ([1997](https://people.reed.edu/~mab/publications/papers/ecal97.pdf)). Its diversity was bounded ([Taylor et al. 2016, footnote 15](https://www.tim-taylor.com/papers/taylor2016openended.pdf)).
- **Tierra:** runs "would eventually reach a state of stasis where only selectively neutral variations were seen to emerge" ([Taylor et al. 2016](https://www.tim-taylor.com/papers/taylor2016openended.pdf)).
- **Cosmos:** see B1.

**Known weaknesses:**

- **The "emergence problem":** components are chosen in advance, so a genuinely new *kind* of component is not seen ([1998](https://people.reed.edu/~mab/publications/papers/alife6.pdf)).
- **Shadow drift:** once the shadow has evolved on its own for a while, it no longer shadows the real run ([Channon 2001](http://www.channon.net/alastair/geb/ecal2001/channon_ad_ecal2001.pdf)).
- **Mean activity is fragile:** with bounded D, one component kept forever makes the mean unbounded. Use the median instead ([Channon 2001](http://www.channon.net/alastair/geb/ecal2001/channon_ad_ecal2001.pdf)).
- **Stabilising selection and ecology read as "activity"** ([Dolson et al. 2019](https://cse.msu.edu/~dolsonem/pdfs/modes_paper.pdf)).

### A2. Channon 2024: component-normalised activity and a five-step test

Source: [Channon 2024, "A procedure for testing for Tokyo Type 1 Open-Ended Evolution", *Artificial Life* 30(3):345–355 (author's final version)](http://www.channon.net/alastair/papers/channon-ArtificialLifeJournal2024a-authorsFinalVersion.pdf).

**Shadow resetting.** After each snapshot, the shadow's population and activity history are reset to the real run's. Between snapshots the shadow evolves with random selection. This stops shadow drift.

**Component-normalised statistics:**

- Increments:
  - Δᵢᴿ(t) = 1 if *i* exists in the real run at *t*.
  - Δᵢˢ(t) = 1 if *i* exists in the shadow at *t*.
  - Δᵢᴺ = Δᵢᴿ − Δᵢˢ.
- Adaptive activity of a component: aᵢᴺ(t) = Σ_{τ≤t} Δᵢᴺ(τ) while *i* exists in the real run, else 0.
- Totals, over components present in the real run:
  - A_cumᴺ = Σ aᵢᴺ.
  - Mean: Ā_cumᴺ = A_cumᴺ/Dᴿ.
  - Median of aᵢᴺ.
  - Dᴿ(t) = #{i : aᵢ(t) > 0}.
- New activity: A_newᴺ(t) = (1/Dᴿ(t))·Σ_{i new} aᵢᴺ(t).
  - A component counts as new, meaning adaptively significant, once aᵢᴺ passes a threshold.
  - The threshold is "the absolute value of the most negative component-normalized evolutionary activity".

**Robustness of the test.** Stout & Spector (2005) tried to make obviously unlifelike systems pass: genetic drift, static fitness functions, and fitness functions switched at intervals. None were classed as unbounded. They credited component normalisation as "of particular importance to the scheme's robustness".

Channon therefore rejects the MODES persistence filter as a replacement for the shadow: "persistence alone is not an adequate substitute".

**The five steps:**

1. **Basic activity statistics.** Stop if A_cum is bounded.
   - No shadow is needed for this step.
   - Only three self-contained systems have ever shown unbounded A_cum: the biosphere, Geb, and Pichler's computational ecosystem.
2. **Component-normalised statistics**, using a shadow with resetting.
3. **Long-term classification.** The system needs positive A_newᴺ together with unbounded total *and* median normalised cumulative activity.
   - Only Geb has passed.
   - Channon also asks that the evolved artefacts be "evidenced by phenotypes rather than just by metrics".
4. **Indefinite scalability** of diversity and complexity. Raise the physical limits (memory, population) and look for a sequence of ever-higher upper bounds.
5. **Order of scalability.** In Geb, maximum complexity grew only logarithmically: roughly 10.17 + 1.87·log₂(size). Extrapolated, even 6.4×10¹⁵ agents would give only about 53 active genes. Beating logarithmic scaling is the "grand challenge".

**Components for Tierra/Avida-like systems.** Channon suggests whole genotypes, or "sections of code that lie between consecutive no-operation instructions (which are used for pattern-based addressing)". These are exactly evo's template-delimited segments.

### A3. York hallmarks (2016) and Tokyo categories (2019)

**York list** ([Taylor et al. 2016, *Artificial Life* 22(3):408–423](https://www.tim-taylor.com/papers/taylor2016openended.pdf)):

1. **Ongoing adaptive novelty:**
   - (a) new adaptations. This is what the Bedau–Packard statistics were built to detect.
   - (b) new kinds of entities.
   - (c) major transitions.
   - (d) evolution of evolvability.
2. **Ongoing growth of complexity:**
   - (a) of entities. What matters is "the complexity of the most complex entities, rather than entities with mean or modal complexity".
   - (b) of interactions, for example food webs.

The paper also makes these points:

- There is more than one kind of open-ended evolution (OEE), a position the authors call **pluralism**.
- Separate **hallmarks** (what you observe) from **mechanisms** (hypothesised causes).
- Ackley's **indefinite scalability** is the practical stand-in for "unbounded".

**Tokyo list** ([Packard et al. 2019, *Artificial Life* 25(2):93–103](https://arxiv.org/abs/1909.04430)). Ongoing generation of:

1. "interesting new kinds of entities and interactions". This merges York 1a, 1b, 2a and 2b. The authors themselves flag "interesting" as vague and subjective.
2. evolution of evolvability.
3. major transitions.
4. semantic evolution.

Channon 2024 (A2) operationalises "interesting": an entity counts if it is, or contains, a new component whose normalised activity passes the threshold.

### A4. MODES toolbox (Dolson, Vostinar, Wiser & Ofria 2019)

Source: [Dolson et al. 2019, *Artificial Life* 25(1):50–73](https://cse.msu.edu/~dolsonem/pdfs/modes_paper.pdf). A C++ implementation is in the Empirical library, and the Avida integration code is at [doi:10.5281/zenodo.1439479](https://doi.org/10.5281/zenodo.1439479).

**Persistence filter:**

- Tag every organism at time *A* with a lineage ID and pass the tag to offspring for *t* generations.
- At time *A + t*, a component from time *A* is "persistent" if it still has descendants alive.
- *t* must be counted in **generations**.
  - The median coalescence time for a neutral, well-mixed asexual population of size N is 2N generations. Selection shortens it.
  - For Avida, "a value of t equal to the population size seems to yield an adequate filter".
- Use the same *t* for any runs you compare.

**Meaningful sites:**

- Knock out one site at a time. Replace it with a null instruction rather than deleting it, because spacing can carry information.
- Sites whose knockout lowers fitness are meaningful.
- A component is then defined as its sequence of meaningful sites only.
- Where a system has no fitness function, use "average lifetime reproductive output" instead (footnote 3).

**The four metrics.** Notation: F is the set of persistent components now, F′ the set at the previous timepoint, and S every component that has ever passed the filter.

| Metric | Formula | Notes |
|---|---|---|
| Change | Σ_{c∈F} [c ∉ F′] | Positive during adaptation *and* when the population cycles between states |
| Novelty | Σ_{c∈F} [c ∉ S] | Each component counts once. Equivalent to A_new. |
| Complexity | max over c ∈ F of (number of meaningful sites in c) | No counterpart in Bedau's statistics |
| Ecology | −Σ_{c∈F} p(c)·log₂ p(c), with p(c) = c's share of F | Shannon diversity. Equivalent to D. |

**Results:**

- **Avida, "empty" environment** (the only selection is for replicating): complexity "rapid[ly] rise[s] … followed by a decrease and leveling out", "due to the strong pressure … to become a more efficient self-replicator by optimizing code". This is the case closest to evo's.
- **Avida, Logic-9 environment** (rewards for logic tasks): complexity kept rising.
- **Ecology** stayed low in every condition that had no multiple niches.

**Implementation notes:**

- Store S in a Bloom filter to save memory. Its errors can only make novelty more conservative.
- Prune taxa that have no living descendants or died before (now − *t*).
- Track two clocks: generations, and a strictly increasing tick.

**Stated limits:** MODES cannot tell class 1 from class 2, or class 3 from 4b.

### A5. QNN: a no-shadow measure for systems where fitness is intrinsic

Sources:

- [Droop & Hickinbotham 2012, ALIFE XIII](https://direct.mit.edu/isal/proceedings/alife2012/24/45/98669). The paper page returned HTTP 403, so I took the definition from the authors' R package, [franticspider/qnn, `qnn/R/genqnn.R`](https://github.com/franticspider/qnn).

Definition from the code:

- pᵢ(t) = nᵢ(t)/N(t), species *i*'s share of the population.
- qᵢ(t) = (max(0, pᵢ(t) − pᵢ(t−1)))².
- QNN(t) = Σᵢ qᵢ(t). The run summary is Σ_t QNN(t).
- An optional flag multiplies by N(t).
- Input is rows of (time, species, count).

Why it works: a species that has just gained a beneficial adaptation grows fast, while one drifting neutrally does not. No model of neutral evolution is needed.

Where it has been used:

- As the generic first measure on long spatial Stringmol runs in [Stepney & Hickinbotham 2024, *Artificial Life* 30(3):390–416](https://direct.mit.edu/artl/article/30/3/390/114972/On-the-Open-Endedness-of-Detecting-Open-Endedness). I read only the abstract. Their argument is that an open-ended system eventually outgrows any model-based measure, so analysis must move from generic to system-specific measures.
- As the "non-neutral activity" in Flow-Lenia (B7).

### A6. Phylogeny metrics and a standard file format

- [Dolson et al. 2020, "Interpreting the Tape of Life", *Artificial Life*](https://lalejini.com/pubs/Dolson_et_al_2020_Interpreting_the_Tape_of_Life.pdf) define:
  - Lineage metrics: lineage length, mutation accumulation, phenotypic volatility.
  - Phylogeny metrics: depth of the most recent common ancestor (MRCA), phylogenetic diversity, mean pairwise distance, regularity.
  - Reading the MRCA: a recent MRCA means frequent selective sweeps; an MRCA that stays deep means stable coexistence.
- [ALife phylogeny data standard](https://alife-data-standards.github.io/alife-data-standards/phylogeny.html):
  - Required columns: `id` (non-negative integer) and `ancestor_list`.
  - Optional columns: `origin_time` and `destruction_time`.
  - Extra columns are allowed.
  - Tools that read it include [Phylotrack (C++/Python)](https://arxiv.org/pdf/2405.09389).

### A7. Compression and complexity measures, 2024–2026

- **Computational Life "high-order entropy"** ([Agüera y Arcas et al. 2024](https://arxiv.org/html/2406.19108v2)):
  - Defined as Shannon entropy over bytes minus Kolmogorov complexity ÷ *n*.
  - Kolmogorov complexity is approximated by the size of `brotli -q2` output (brotli v1.1.0), computed on the whole soup.
  - It jumps at the transition to self-replicators. It is a cheap takeover detector, not an OEE test.
  - The exact units are **UNVERIFIED**; I assume bits per byte for both terms.
- **Flow-Lenia.png** ([Adachi et al., ALIFE 2024](https://arxiv.org/abs/2408.06374)): image compressibility is the GA's fitness *target*, not a detector.
- **MSPD** ([Akhtyrchenko, Katsnelson & Ustyuzhanin 2026, preprint](https://arxiv.org/abs/2606.17091)):
  - "Multi-Scale Path Divergence" is a scalar borrowed from renormalisation-group ideas. It measures how varied the local transition laws are across scales.
  - It is used both as a fitness function and as a post-hoc lens, on Flow-Lenia, Life-like CA and Particle Life++.
  - It does not use compression. I read the abstract only.
- **ASAL** ([Kumar et al. 2024](https://arxiv.org/html/2412.17799)):
  - The open-endedness score is E_T[max_{T′<T} ⟨CLIP(frame_T), CLIP(frame_T′)⟩], and the search *minimises* it. In words: every frame should be unlike its most similar earlier frame.
  - It was applied only to the Life-like CA rule space. There Game of Life ranks in the top 5%.
  - The authors dropped Lenia and Boids because novelty was "hard to sustain" there. (spot-checked)
- **Caution about compression:** random strings have maximal Kolmogorov complexity, so compressed genome length is a poor complexity measure on its own. That is why the entropy-minus-compression form above is used, and why Adami's information measure (B6) is used.

---

## B. Systems the first review missed

### B1. Cosmos (Tim Taylor, PhD thesis, Edinburgh 1999)

Primary source: [Taylor 1999 thesis, HTML version](http://archive.tim-taylor.com/papers/thesis/html/main.html).

**Substrate:**

- "Several thousand" self-reproducing programs run under a virtual operating system.
- Cells have bitstring genomes with 62 instructions of 6 bits each.
- Promoters and repressors regulate which parts of the genome are translated ([node56](http://archive.tim-taylor.com/papers/thesis/html/node56.html), [node157](http://archive.tim-taylor.com/papers/thesis/html/node157.html)).
- A cell can read, write and execute only inside itself. It copies its genome into its own working memory, then divides ([node61](http://archive.tim-taylor.com/papers/thesis/html/node61.html)).

**Energy:**

- A cell "must pay one energy token to the processor for each instruction it executes", and its store may leak ([node59](http://archive.tim-taylor.com/papers/thesis/html/node59.html), spot-checked).
- CPU share per time slice scales with length as N = c·L^p. The defaults are c = 0.025 and p = 1, which gives the 348-bit ancestor 8 instructions per slice ([node50](http://archive.tim-taylor.com/papers/thesis/html/node50.html)). The formula is an image missing from the HTML and was rebuilt by a sub-agent.
- Tokens are dropped on every grid square each sweep, 30 per square with a cap of 100.
- Cells gather tokens with `et_collect`: 10 per call, up to 100 held.
- Under the default "shared" scheme, a cell on an empty square collects from the stores of cells on the 8 neighbouring squares ([node76](http://archive.tim-taylor.com/papers/thesis/html/node76.html), [node78](http://archive.tim-taylor.com/papers/thesis/html/node78.html), [node110](http://archive.tim-taylor.com/papers/thesis/html/node110.html)).

**Space:**

- 40×40 torus.
- Cells of different organisms may share a square ("two-and-a-half dimensional").
- Taylor concedes the grid "only holds pointers to the cells, in much the same way as in a GA" ([node75](http://archive.tim-taylor.com/papers/thesis/html/node75.html), [node173](http://archive.tim-taylor.com/papers/thesis/html/node173.html)).

**Death:**

- Energy exhaustion.
- A backstop cap: at 2500 cells, the 10% with the least energy are culled. The cap was not reached in the standard run but was reached in the private-energy runs ([node60](http://archive.tim-taylor.com/papers/thesis/html/node60.html), [node145](http://archive.tim-taylor.com/papers/thesis/html/node145.html), spot-checked).

**Mutation:**

- Random bit flips across the genome *and* cell state.
- `mutation_period` (default 10⁶; tested at 10⁵ and 10⁷) is the expected number of untouched bits between hits.
- "Flaws" make instructions run twice or be skipped ([node83](http://archive.tim-taylor.com/papers/thesis/html/node83.html), [node110](http://archive.tim-taylor.com/papers/thesis/html/node110.html)).

**Results (verdicts are Bedau classes, A1):**

| Condition | Result | Source |
|---|---|---|
| Standard | "Steady microevolution, with no spectacular macroevolutionary innovation", Class 2. Genomes grew 348 → 390 bits, mostly by adding `et_collect` into the copy loop. No parasites, no multicellularity. | [node111](http://archive.tim-taylor.com/papers/thesis/html/node111.html), [node117](http://archive.tim-taylor.com/papers/thesis/html/node117.html) |
| Re-runs | 5 of 9 fell to **Class 1**: zero mean and new activity, diversity near population size, long programs. | [node133](http://archive.tim-taylor.com/papers/thesis/html/node133.html), spot-checked |
| Fixed 10 instructions per slice, not length-scaled | All 9 runs stayed Class 2. Length still grew slowly (354–402 bits) through `et_collect` build-up. | [node140](http://archive.tim-taylor.com/papers/thesis/html/node140.html), spot-checked |
| Private energy collection | Evolution continued after the transition, "although it proceeds at a slower pace". | [node145](http://archive.tim-taylor.com/papers/thesis/html/node145.html), spot-checked |
| High mutation | All runs Class 1. | [node136](http://archive.tim-taylor.com/papers/thesis/html/node136.html) |
| Low mutation | A "cancer" mutant that adds junk every generation wiped out whole populations. | [node138](http://archive.tim-taylor.com/papers/thesis/html/node138.html) |
| Energy gradient 1→59 tokens | Several program lengths coexisted. A 26→34 gradient did not produce this. | [node150](http://archive.tim-taylor.com/papers/thesis/html/node150.html) |
| Neighbours' code made readable | No parasites (0.277 vs 0.010 unfaithful copies). The mechanism was "too complicated to be exploited… no single mutation of the ancestor which would produce a functional parasite". | [node154](http://archive.tim-taylor.com/papers/thesis/html/node154.html) |
| 19 runs differing only in seed | Each differed significantly from at least a third of the others. Taylor then ran each experiment ≥9 times. | [node157](http://archive.tim-taylor.com/papers/thesis/html/node157.html), spot-checked |

- **What caused the Class 1 collapse:** a copy-loop mutation that doubled the genome, with the second half acting as "selfish DNA". Under length-proportional CPU, the longer programs ran more `et_collect` per slice. Through shared collection they drained their neighbours, and the grid locked into a checkerboard of about 400 organisms ([node133](http://archive.tim-taylor.com/papers/thesis/html/node133.html), [node144](http://archive.tim-taylor.com/papers/thesis/html/node144.html)).
- **Why both adaptations ran out:** adding `et_collect` and deleting redundant code "each… can be applied" only up to a limit, and there was "little evidence for other innovations" ([node157](http://archive.tim-taylor.com/papers/thesis/html/node157.html)).
- **Taylor et al. 2016 on Cosmos:** it showed "evolutionary dynamics similar to those of Evita" ([Taylor et al. 2016, footnote 15](https://www.tim-taylor.com/papers/taylor2016openended.pdf)).

**What Taylor concluded was missing:**

His five problems with Tierra-like systems ([node159](http://archive.tim-taylor.com/papers/thesis/html/node159.html)):

1. No explicit theoretical grounding.
2. The structure of an organism is predefined.
3. Ecological interactions are restricted.
4. No competition for matter or energy. In Tierra, copied instructions appear "spontaneously" and programs "are not even really competing for energy (CPU-time)" ([node163](http://archive.tim-taylor.com/papers/thesis/html/node163.html)).
5. Self-reproduction is written into the program rather than being implicit in the physics.

His recommendations:

- "The more embedded they are, and the less restricted the interactions are, then the more potential there is for the very structure of the individual to be modified" ([node173](http://archive.tim-taylor.com/papers/thesis/html/node173.html)).
- Fully embedded individuals and a copying process "implicit in the environment" ([node179](http://archive.tim-taylor.com/papers/thesis/html/node179.html)).
- Heterogeneous, changing environments ([node181](http://archive.tim-taylor.com/papers/thesis/html/node181.html)).

Later papers:

- [Taylor 2004](http://archive.tim-taylor.com/papers/evoca_final.pdf): "The Tierran language… is computationally universal, but this does not mean that Tierran programs can interact with their environment in unlimited ways". Self-reproduction with heritable variation and selection are "by themselves… insufficient".
- [Taylor 2019, "Evolutionary innovations and where to find them" (arXiv:1806.01883)](https://arxiv.org/abs/1806.01883):
  - Separates **intrinsic** processes (made of the system's own parts, and so able to evolve) from **extrinsic** hard-coded shortcuts.
  - Expansive and transformational novelty needs new possibility space, which must come from rich physics or outside resources. Two routes are proposed:
    - "domains, exaptations and transdomain bridges", meaning parts that have several kinds of properties.
    - non-additive compositional systems.
  - Tierra "implements [evaluation] intrinsically, but [the genotype→phenotype map] is extrinsic and trivial, and the abiotic environment… is very impoverished".
  - The phrases "exploration of new physical properties" and "exploitation of physics" do not appear in the paper (sub-agent search).

### B2. Nanopond (Adam Ierymenko; v2.0 source, v1.9 in `attic/`)

Sources: [nanopond.c](https://raw.githubusercontent.com/adamierymenko/nanopond/master/nanopond.c) (constants and access function spot-checked by me) and [nanopond-1.9-orig.c](https://raw.githubusercontent.com/adamierymenko/nanopond/master/attic/nanopond-1.9-orig.c).

**Substrate:**

- A toroidal grid of cells.
- Each cell holds up to `POND_DEPTH` 4-bit codons from a 16-instruction set inspired by Brainfuck.
- Codon 0 is the "logo". Execution starts after it.
- The VM has one 4-bit register, a memory pointer, a facing direction, and an output buffer.

| Constant | v2.0 | v1.9 |
|---|---|---|
| POND_SIZE_X × Y | 800 × 600 | 640 × 480 |
| POND_DEPTH | 1024 | 512 |
| MUTATION_RATE (out of 2³²) | 5000 (≈1.16×10⁻⁶ per executed instruction) | 21475 (≈5×10⁻⁶) |
| INFLOW_FREQUENCY | 100 | 100 |
| INFLOW_RATE_BASE / _VARIATION | 600 / 1000 | 4000 / 8000 |
| FAILED_KILL_PENALTY | 3 | 2 |

**Energy:**

- "Every INFLOW_FREQUENCY clock ticks a random x,y location is picked, energy is added… and it's genome is filled with completely random bits". The single inflow event is therefore both the only energy source *and* a random disturbance that erases whatever lived there.
- A randomly chosen cell runs until STOP or until it runs out of energy. "Each instruction costs one unit energy".
- `SHARE` evens out energy with the neighbour the cell is facing.

**Reproduction:**

- After a cell runs, a non-empty output buffer is written over the neighbour it faces, but only `if ((tmpptr->energy)&&accessAllowed(tmpptr,reg,0))`.
- So the child inherits the *target square's* energy, and cannot be born on a square with no energy. Energy works like territory.

**Permission ("logo") check** (my reading of line 502):

- Let d be the Hamming distance between the target's logo and the actor's register.
- Harmful actions (overwriting with offspring, `KILL`) succeed with probability (d+1)/16.
- `SHARE` succeeds with probability (16−d)/16.
- Cells that are random, meaning they have no parent, are always accessible.
- A failed `KILL` costs the attacker energy/`FAILED_KILL_PENALTY`.
- The source comments contradict the code: they call harmful access "more probable if they are more similar".

**Death:**

- No reaper. A cell with no energy is simply skipped.
- Cells also die when overwritten, killed, or reseeded by an inflow event.

**Results (author's comments in the source):**

- "Random genesis": replicators appear from the random inflow.
- The scarce resources are "space in the NxN grid and energy".
- Evolution "doesn't get 'stuck'", which the author credits partly to simplicity and "embeddedness". He also admits he had not run "the kind of multiple-month-long experiment necessary to really see this".
- No limitations are stated by the author (**UNVERIFIED** that none exist).
- A third party reports that after 3×10⁹ iterations the dominant strategy was copy-then-`KILL`, and that switching replication strategies was "almost impossible" by small steps ([Hacker News comment](https://news.ycombinator.com/item?id=2723001); not a primary source).

### B3. Squirm3 (Tim Hutton, 2002–2007)

Sources: [Hutton 2002, "Evolvable self-replicating molecules in an artificial chemistry", *Artificial Life* 8(4)](https://faculty.cc.gatech.edu/~turk/bio_sim/articles/hutton_rep_molecules.pdf) and [Hutton 2007, "Evolvable self-reproducing cells in a two-dimensional artificial chemistry", *Artificial Life* 13(1)](https://web.archive.org/web/20210117085336id_/http://www.sq3.org.uk/papers/cells2007.pdf).

**Physics:**

- A 2D grid with one atom per square.
- Atoms have a fixed type (a–f) and a changeable state.
- Atoms random-walk but must stay adjacent to the atoms they are bonded to.
- 8 reaction templates expand to 188 concrete reactions.

**Replication:**

- Replication is **designed in**: "any string of a1's, b1's, c1's and d1's with an e8 at one end and an f1 at the other will replicate… This is by design".
- Replicators still emerged from a random soup when "cosmic rays" were on (p = 10⁻⁵ per atom per step). The first appeared at about 400,000 iterations in a 100×100 world.

**Resources and death:**

- No energy model. Matter is conserved.
- Periodic "floods" clear half the world and refill it with raw atoms. They act as both reaper and resupply.
- Variation came from "dirty" cross-molecule bonding, which recombines strands.

**2002 results:**

- Shorter replicators won. "After optimal replicators become prevalent we see no further evolution".
- "The only selection pressures encountered have been towards shorter molecules".
- Hutton declined to hand-add reactions, which "would surely rob the simulation of the 'surprise!' factor".

**2003 enzymes paper** (known only through the 2007 summary, **UNVERIFIED**):

- Enzymes made by one replicator helped every molecule nearby.
- Result: "parasites: shorter molecules that replicate faster… typically lead to a global extinction event".

**2007 cells:**

- A membrane keeps each cell's enzymes to itself.
- In the longest run there were 15,772 reproductions and 145 genetic species. A neutral variant took over.
- Giving cells a second gene that let them eat a new food atom let the *longer* genome drive the shorter one extinct by about 500,000 iterations.

Stated limits:

- "The system does not have sufficient evolvability".
- A new enzyme needs about 14 bases, but "unused bases tend to be gradually removed".
- The decoding scheme is "hard-wired".
- Cells "are not yet capable of attacking each other for food".

Hutton explicitly adopts Taylor's criteria of conserved components, full embeddedness and rich interactions.

### B4. Evoloops (Sayama 1999) and the 2024/2025 review

Sources: [Sayama 1999, *Artificial Life* 5(4):343–365 (abstract)](https://pubmed.ncbi.nlm.nih.gov/10829086/) and [Salzberg, Antony & Sayama, ALIFE IX 2004](https://bingdev.binghamton.edu/sayama/papers/alife9-evoloop.pdf).

**Substrate:**

- A deterministic 9-state cellular automaton on the 5-cell von Neumann neighbourhood, derived from Langton's loop.
- The genome is a train of signals that circulates in the loop.
- Variation comes only from collisions between loops: "collisions of loop sheath structures during replication often lead to a change in the gene sequence of offspring". There is no mutation operator.

**Death:**

- A **dissolver state 8** spreads through a loop and erases it. It is "triggered by local configurations non-integral to the normal self-replication cycle… typically aris[ing] from shortage of space due to overcrowding" ([ALIFE IX](https://bingdev.binghamton.edu/sayama/papers/alife9-evoloop.pdf)).
- The 2024 review says this is what frees space that "otherwise would become clogged with the debris and remnants from no longer active individuals" ([Sayama & Nehaniv](https://arxiv.org/pdf/2402.03961)).
- In effect this is a reaper built into the physics.

**Results:**

- "Smaller individuals were naturally selected thanks to their quicker self-reproductive ability, and the whole population gradually evolved toward the smallest ones" ([1999 abstract](https://pubmed.ncbi.nlm.nih.gov/10829086/)).
- When seeded loops could not shrink below size 15, the system "fluctuates between dominant species, demonstrating continuous, long-lasting evolutionary behavior": more than 6×10⁶ iterations, 7,106 species, 58 of them self-replicating, on a 401×401 grid ([ALIFE IX](https://bingdev.binghamton.edu/sayama/papers/alife9-evoloop.pdf)).
- "Hostile environments" slowed selection toward smaller loops enough for larger ones to appear. The complexity gained was "limited", and driven by "biased genealogical connectivity… and not just by adaptation" ([BioSystems 2004 abstract](https://pubmed.ncbi.nlm.nih.gov/15555763/)). How the environments were made hostile is **UNVERIFIED**.

**The review:** [Sayama & Nehaniv, "Self-Reproduction and Evolution in Cellular Automata: 25 Years after Evoloops", arXiv:2402.03961; *Artificial Life* 31(1):81 (2025)](https://arxiv.org/abs/2402.03961).

- It covers:
  - asynchronous evoloops
  - self-protection
  - sexyloops (Oros & Nehaniv)
  - loops and worms that encode their shape
  - loops that adapt to local space (Huang et al.)
  - Adams et al. 2017
  - Andras 2017, which applied Bedau's activity statistics to CA
  - Lenia, neural CA and Flow-Lenia
- Its verdict: "nearly all the above evolutionary systems built within spatially distributed media exhibited the eventual dominance by one or a few most successful species in the long run". Dynamic environments help, but "may not work for indefinitely long terms".
- Open problems it lists:
  - von Neumann-style replicators that are robust to noise and collisions, and have sex and self-repair.
  - Mechanisms that stop one or a few species from dominating (the "pseudo-equilibrium").
  - Parameters carried by local regions of space (as in Flow-Lenia) versus genomes explicitly present in space.
  - Autopoiesis.
  - "Intelligence" measured as dynamics that become increasingly hard to compress or simulate over evolutionary time.

### B5. AlChemy (Fontana & Buss 1994) and the 2024 revisit

Source: [Fontana & Buss, "The Arrival of the Fittest", *Bull. Math. Biol.* 56 (SFI working paper 93-09-055)](https://sfi-edu.s3.amazonaws.com/sfi-edu/production/uploads/sfi-com/dev/uploads/filer/f2/8b/f28b8075-4e73-4696-989e-1cfbe06b2dc8/93-09-055.pdf). The PNAS 1994 paper says the same thing in short form ([PMC43028](https://pmc.ncbi.nlm.nih.gov/articles/PMC43028/)).

**Substrate:**

- λ-calculus expressions in a well-stirred reactor holding N = 1000 objects.
- In each collision (j)k is reduced to normal form. If the product is valid, a **random object is removed** and the product added. This dilution flow is a reaper.

**The three levels of outcome:**

- **Level 0:** copying is allowed. The system ends in copy-dominated sets, often a single self-copier or a hypercycle.
- **Level 1:** copying is disallowed. Self-maintaining "organizations" appear, with an invariant grammar and a centre.
- **Level 2:** two organizations meet and either displace each other or merge into a meta-organization.

**Why copying suppresses organization:**

- "Since the system is constrained to maintain a constant size, objects that replicate eliminate objects that do not".
- "The time required for a self-maintaining metabolism to dominate the system is longer than the time required for self-replicators to dominate."
- Accepting copy products only 75% of the time "was typically sufficient to permit organizations to develop".

**The revisit:** [Mathis, Patel, Weimer & Forrest 2024, "Self-Organization in Computation & Chemistry: Return to AlChemy", arXiv:2408.12137](https://arxiv.org/abs/2408.12137). The venue is **UNVERIFIED**.

- With longer runs, some copy-allowed Level 0 runs reached complex organizations: "10–100s of distinct expressions", about 380 in one run.
- These organizations were extremely robust. Replacing 90% of the objects did not destroy most of them.
- Organizations from different runs rarely coexisted. The exact percentages are **UNVERIFIED**.
- A different random-expression generator made even copy-prohibited runs "rapidly collapse into a trivial fixed point": "the richness of the organization depends on the accessibility of the space of objects".

### B6. Adami: physical complexity, and Avida numbers

**Physical complexity** ([Adami, Ofria & Collier 2000, PNAS 97:4463](https://pmc.ncbi.nlm.nih.gov/articles/PMC18257/); [arXiv:physics/0005074](https://arxiv.org/abs/physics/0005074)):

- Per-site entropy: Hᵢ = −Σ_j p_j(i)·log_D p_j(i), with D the alphabet size.
- Complexity: C = ℓ − Σᵢ Hᵢ, with ℓ the genome length. This counts the information the genome holds about its environment.

Two ways to estimate Hᵢ:

1. **From population frequencies at each site.**
   - Easiest when genome length is fixed. Otherwise the genomes must be aligned.
   - Sites that hitchhiked on a recent sweep look fixed, so wait after sweeps.
2. **From mutants.** Test "all single-mutation genomes… in isolation" and set Hᵢ = log_D(N_ν), where N_ν is the number of non-lethal substitutions at that site. Avida's alphabet was D = 28.

Setup of that study:

- 60×60 torus.
- Genome length fixed at 100.
- Copy error 0.01 per instruction copied.
- The authors note that an "information-poor landscape leads to selection for replication only, and shrinking genome size".

**Compression pressure** ([Ofria, Adami & Collier 2003, *J. Theor. Biol.* 222:477](https://arxiv.org/abs/quant-ph/0301075)):

- "Since it takes time to copy each symbol, there is a pressure to shrink the genome to the minimal length that can still self-replicate."
- Copy rates used: 0.5%, 0.75%, 1.0% and 1.5% per instruction.

"Digital genetics" ([Adami 2006, *Nat Rev Genet* 7:109](https://www.nature.com/articles/nrg1771)): abstract only. Its quantitative content is **UNVERIFIED**.

### B7. Recent CA and Lenia work (brief)

**Flow-Lenia** ([Plantec et al. 2025 journal version, arXiv:2506.08569](https://arxiv.org/html/2506.08569), spot-checked). This is the only one of these that reports OEE statistics.

- It adds mass conservation to Lenia, with the update parameters carried along with the matter.
- Activity measures used:
  - count-based evolutionary activity
  - non-neutral activity, which "penalizes stasis by incrementing only when component proportion increases" (the QNN idea)
- A species is defined as "a unique point in the parameter space". The authors flag this definition as a limitation.
- Both measures fell as a power law in mutation rate: γ = −0.5 (R² = 0.75) for non-neutral, −0.71 for count-based.
- "The mass conservation constraint acts as a regularizer".
- Normalising by total mass *reversed* the ranking between variants of the model.

**Other systems, briefly:**

- **ASAL:** see A7.
- **Leniabreeder** ([Faldor & Cully 2024](https://arxiv.org/abs/2406.04235)): external quality-diversity search, not intrinsic evolution.
- **Particle Life:** no primary OEE measurement found, apart from the MSPD preprint (A7).
- **Self-replicating neural CA** (Sinapayen 2023): no OEE statistic found (**UNVERIFIED**).

---

## C. The Eigen error threshold and the mutation rates actually used

### C1. Formula

Define:

- μ = 1 − q, the error rate per site per copy.
- L, the genome length.
- σ, the "superiority" of the master sequence: its replication rate relative to the average of its mutant cloud.

The chance of an error-free copy is Q = q^L ≈ e^{−μL}. The master sequence holds its place only if σQ > 1. Rearranged:

> **L_max ≈ ln σ / μ**, equivalently the genomic mutation rate **U = μL < ln σ**.

**Check against a published number.** In Eigen's worked example the sequences are binary with N = 20, and the master replicates 10 times faster than everything else. The threshold appears at 1 − q ≈ 0.11 ([Eigen 2002, PNAS](https://pmc.ncbi.nlm.nih.gov/articles/PMC129678/)). The formula gives ln 10/20 = 0.115, which matches.

**L_max for some values** (ln 2 = 0.69, ln 10 = 2.30, ln 100 = 4.61):

| μ per site | σ = 2 | σ = 10 | σ = 100 |
|---|---|---|---|
| 1×10⁻³ | 693 | 2303 | 4605 |
| 3×10⁻³ | 231 | 768 | 1535 |
| 1×10⁻² | 69 | 230 | 461 |
| 3×10⁻² | 23 | 77 | 154 |

### C2. Why the textbook formula does not apply directly to evo

- **Lethal mutants.** The classic threshold is a relative-fitness result, derived for a fixed-size population ("soft selection").
  - [Wilke 2005](https://pmc.ncbi.nlm.nih.gov/articles/PMC1208876/), citing Wagner & Krall: an error threshold requires "the complete absence of lethal genotypes".
  - [Takeuchi & Hogeweg 2007](https://pmc.ncbi.nlm.nih.gov/articles/PMC1805495/) dispute this. In high-dimensional genotype space a threshold does exist when most mutants are lethal. At high error rates the population's ancestry drifts away from the fittest genotype whatever the lethal fraction.
- **Hard selection.** evo has no fixed population size: space and energy set the numbers. So the relevant failure is **extinction**, called mutational meltdown or lethal mutagenesis.
  - [Bull, Sanjuán & Wilke 2007](https://pmc.ncbi.nlm.nih.gov/articles/PMC1865999/): a population declines if **R_max · e^{−U_d} < 1**.
    - U_d is the number of deleterious mutations per genome per generation.
    - R_max is the number of successful offspring the mutation-free genotype produces at low density.
    - e^{−U_d} is both the equilibrium mean fitness and the fraction of offspring with no harmful mutation.
  - So a lineage persists only if **U_d < ln R_max**. This has the same shape as Eigen's rule, with σ replaced by R_max and μL replaced by U_d.
  - Both terms can be measured in evo directly (see D).
- **"Survival of the flattest".** At high mutation rates, genotypes with slower replication but more mutationally robust neighbourhoods beat faster ones ([Wilke et al. 2001, abstract](https://www.nature.com/articles/35085569)).
  - Measured critical genomic rates in Avida ranged from **0.5 to 3.6 mutations per genome per generation**, for genomes of 54–272 instructions, with no correlation to genome size ([Comas, Moya & González-Candelas 2005](https://pmc.ncbi.nlm.nih.gov/articles/PMC546199/)).
  - So evolved digital organisms tolerate U well above 1.
- **Genome size tracks the mutation rate** ([Gupta, LaBar, Miyagi & Adami 2016, *Sci Rep*](https://pmc.ncbi.nlm.nih.gov/articles/PMC4867773/)).
  - Setup: 20-instruction ancestor, 3600 organisms, 2×10⁵ generations, per-locus rates from 0.0025 to 0.1.
  - Genome size was negatively correlated with mutation rate (Spearman ρ = −0.72). Genomic rates evolved to anywhere from 0.13 to 24.85.
  - Swapping the rates halfway through flipped the trend: long genomes shrank and short ones grew.
  - At low mutation rates, insertions drove growth, and 87% of new traits were preceded by an insertion within the previous 20 ancestors.
  - Genomes evolved at low rates held more essential sites, i.e. more information.
- **Typical σ.** I found no primary measurement of σ for Tierra- or Avida-like organisms, and no primary figure for the fraction of mutations that are lethal (Lenski et al. 1999, *Nature* 400:661, is paywalled). Both are **UNVERIFIED**. Measure U_d and R_max in evo instead of assuming σ.

### C3. Rates the reference systems used

| System | Per-site rate | Typical L | Copy mutations per genome per generation | Other noise | Source |
|---|---|---|---|---|---|
| Tierra v5 docs | `GenPerMovMut = 8`: about 1 in 8 cells hit by a copy mutation per generation. A sample run's `RateMovMut = 1216` means 1 per 608 instructions copied, ≈1.6×10⁻³. A mutated instruction gets one of its 5 bits flipped. | ancestor 0080aaa = 80 | ≈0.13 | `GenPerBkgMut = 16` ("cosmic rays": 1 in 16 cells per generation, free space included); `GenPerFlaw = 32` or 64 ("profound effect on the rate at which creatures shrink"); SoupSize 50,000–60,000 | [Tierra docs](https://dendrit.tuke.sk/~newalife/kapitola/1263/Doc.htm) (mirror; the original tomray.me/life.ou.edu hosts no longer serve it) |
| Avida defaults | `COPY_MUT_PROB 0.0075` per copied instruction | 100 | 0.75 + 0.05 insertion + 0.05 deletion = **0.85** | Age death after 20×L executed instructions; births overwrite neighbours | [avida.cfg](https://github.com/devosoft/avida/blob/master/avida-core/support/config/avida.cfg); [Nelson & Sanford 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3102618/) for the 0.85 figure |
| Adami et al. 2000 | 0.01 | 100 (fixed) | 1.0 | | [PMC18257](https://pmc.ncbi.nlm.nih.gov/articles/PMC18257/) |
| Ofria et al. 2003 | 0.005–0.015 | | | | [arXiv](https://arxiv.org/abs/quant-ph/0301075) |
| Nanopond v2 | ≈1.16×10⁻⁶ per *executed* instruction; copying errors come from the program itself | up to 1024 codons | n/a | Random reseeding every 100 ticks | [nanopond.c](https://raw.githubusercontent.com/adamierymenko/nanopond/master/nanopond.c) |
| Cosmos | Bit flips, mean gap `mutation_period` = 10⁶ bits (high 10⁵, low 10⁷); flaws every 2.5×10⁵ | 348 bits | n/a | Both extremes collapsed the runs (B1) | [node110](http://archive.tim-taylor.com/papers/thesis/html/node110.html) |

---

## D. Design implications for evo

### D1. What to log from day one

Everything below is raw data. All the metrics are computed offline in Python. Most of it follows from the organism table and genome store already planned in PLAN §7.

| Record | Fields | Needed for |
|---|---|---|
| **births** (one per `divide`) | tick, child_id, parent_id, child genome hash *as copied*, length, position, generation depth (parent + 1), count of noisy-write errors that landed in the child region, energy handed over | Existence intervals for activity statistics; an offline neutral shadow with resetting; MODES lineages; the empirical U (fraction of births with ≥1 error); ancestry metrics |
| **deaths** | tick, id, cause (starved / overwritten / decayed / region claimed), age, lifetime offspring count | Existence intervals; lifetime reproductive output, which serves as "fitness" for MODES meaningful sites; R estimates; turnover |
| **genomes** (store keyed by hash) | bytes, first-seen tick, first organism id, parent genome hash | A genotype-level phylogeny in the [ALife standard](https://alife-data-standards.github.io/alife-data-standards/phylogeny.html) (`id, ancestor_list, origin_time, destruction_time`); novelty (the ever-seen set); segment components |
| **census** every K ticks | (tick, genome hash, count), and optionally per region | QNN; per-genotype counts; the ecology metric; physical complexity from the population; checks on the exact intervals |
| **mutation events** | tick, address, owner (organism, free or debris), old byte, new byte, cause (copy noise / store noise / background flip / foreign write) | Separating heritable changes from somatic damage; the realised per-site rate |
| **phenotype summary** per organism at death | instructions executed, energy absorbed and spent, ticks per offspring, histogram of 22–32 op classes, counts of foreign reads / execs / writes, template searches that succeeded and failed | Phenotype-level components (Channon found genotypes a poor component when there is much neutral variation); phenotypic volatility; "absorb per copied byte" as an early warning of stagnation (B1) |
| **interaction counts** per census interval | (actor genotype, target genotype, kind) → count | Interaction complexity (York 2b); detecting parasites; food webs once `drain` exists |
| **world snapshots** | Byte array, owner map, cell parameters | Compression and high-order entropy (A7); spatial analysis; replay |

Notes on the logging:

- **Existence intervals come from births and deaths exactly.** A genotype exists from the first birth of a carrier to the death of its last carrier. The census does not have to sample fast enough to catch short-lived genotypes; K only sets the resolution of the counts.
- **The offline shadow is cheap.** Channon's shadow with resetting needs only three things per snapshot interval:
  - the real population's composition at each snapshot (census),
  - the number of births and deaths in the interval (births/deaths),
  - the per-birth probability that the child's genotype differs from its parent's (births).
  
  The shadow does not need to run inside the Rust VM.
- **Somatic mutation is new for these metrics.** In evo, bodies change in place: background flips and foreign writes alter living organisms. Activity statistics assume a component is fixed at birth. So:
  - Define the component as the genome *as copied at birth* (germline).
  - Log changes to living bodies separately, as mutation events whose owner is an organism.
  - Optionally record in the census how many living bodies no longer match their birth hash.
- **Build a single-genome test harness early.** It runs one genome alone in an empty patch with a fixed energy supply and returns viability, ticks per offspring, offspring fidelity and lifetime offspring count. It is needed for:
  - MODES meaningful sites and the complexity metric (knockouts),
  - Adami's mutant-based Hᵢ = log_D N_ν,
  - measuring U_d and R_max (C2),
  - checking whether a parasite is one or two mutations from the ancestor (see D2).

  It is the equivalent of Avida's test CPU.
- **Two clocks.** Record ticks and per-organism generation depth. MODES *t* is counted in generations, with *t* ≈ population size as the starting point.

**Components to compute** (all from the same raw logs):

1. exact genotype hash;
2. the genotype reduced to its meaningful sites;
3. **template-delimited segments**: the code between nop runs, which Channon 2024 suggests for Tierra/Avida and which matches evo's template addressing;
4. a phenotype signature.

Report statistics per component type. Flow-Lenia's lesson is that the choice of species definition dominates the results.

### D2. What Cosmos, Nanopond and the others imply for energy per instruction and locality

1. **Charging energy per instruction works**, since Cosmos charged exactly 1 token per instruction. But expect the first adaptation to be "more `absorb` inside the copy loop", then saturation, then stasis ([node157](http://archive.tim-taylor.com/papers/thesis/html/node157.html)). Log absorb calls per copied byte, per genotype.
2. **The instruction budget must not grow with body size.** Cosmos's length-scaled CPU led to genome-doubling "selfish DNA" and Class 1 in 5 of 9 runs. A fixed budget kept all 9 in Class 2.
   - PLAN §5.4 has a per-tick instruction cap. Make it per organism, not per body byte.
   - Likewise, if energy ever becomes per byte of body (the open question in §9), check that this does not reward padding.
3. **Watch energy flowing between neighbours.** Cosmos's "shared" collection let established cells drain newborns and froze the grid into a checkerboard; "private" collection brought evolution back.
   - Implications for evo:
     - If several organisms share one cell's sunlight pool, crowding is rewarded.
     - The Phase 3 `drain` op must be lossy and must cost the drainer.
     - `divide r` (the energy a parent hands to its child) matters, because newborns are the most vulnerable.
4. **Make the environment strongly uneven.** Cosmos's weak gradient (26–34 tokens) did nothing, while a strong one (1–59) let several program lengths coexist. Hutton's new food source let longer genomes win. Sayama & Nehaniv add that static heterogeneity eventually gives way to one or a few dominant species. So plan for drift (§5.6), and compare it against a static control.
5. **No reaper still needs a source of turnover and a way to clear debris.** Every "reaper-free" system here has one:
   - Nanopond reseeds a random cell every 100 ticks.
   - Squirm3 floods half the world.
   - Evoloops dissolves broken loops.
   - Cosmos culls the lowest-energy cells at a cap.
   - AlChemy removes random objects.

   In evo, decay plus starvation plus claiming debris must do this job. Measure turnover and the fraction of the world that is debris from Phase 1 on, and treat an explicit disturbance (like Nanopond's inflow) as an experimental factor rather than a fix.
6. **Mutation-rate extremes killed Cosmos runs.** High mutation sent every run to Class 1. Low mutation let a "cancer" mutant cause extinctions. See D3 for a starting rate.
7. **Parasites need a short mutational path.** Tierra's free reads put parasites one mutation away. Cosmos's readable-code mode produced none because "no single mutation of the ancestor… would produce a functional parasite". Before Phase 1, use the test harness to check that a working parasite (`searchf` to a neighbour's template, then `jmpr` into it) is one or two mutations from the ancestor.
8. **Nanopond's permission check is a cheap, evolvable defence.** Harmful access succeeds with probability (d+1)/16, where d is the Hamming distance between the target's logo and the actor's guess, and a failed attack costs the attacker. This is an alternative to a paid `guard` flag for §5.5. Also, a Nanopond child inherits the energy of the square it lands on, which makes energy behave like territory. evo's `divide r` makes parental investment evolvable instead; keep that.
9. **Watch copy dominance.** AlChemy (fixed capacity plus copying leads to copier takeover), Evoloops (evolution toward the smallest loop), Avida's empty environment (complexity rises then falls), and Squirm3's 2002 runs all show that a physics which only rewards copying picks the minimal copier.
   - evo's energy costs strengthen this pressure.
   - The counter-pressures have to come from the environment and from interactions: Squirm3's food gene, Avida's Logic-9 tasks, Salzberg's minimum-size loops.
   - The MODES complexity metric on the persistent population is the right early detector of this shrink-to-minimum behaviour.
10. **Embeddedness.** By Taylor's critique:
    - evo does well on conserved matter: `alloc` claims existing free bytes or debris; nothing is created from nothing.
    - Registers, the instruction pointer and the energy store live outside the byte array. That is "hidden" state in Taylor's sense.
    - This is a conscious trade-off, not a flaw. Record it in the hypotheses log.
11. **Replicates.** Cosmos runs that differed only in seed diverged significantly. Use at least 9 seeds per condition, and decide boundedness by fitting models (A1).

### D3. Setting the noisy-write rate

- Anchor points:
  - Tierra ran at about **0.13** copy mutations per genome per generation.
  - Avida's defaults give about **0.85**.
  - Avida organisms that have adapted to high rates survive up to about **2–3.6**.
- So aim for U_copy = p·L_ancestor ≈ **0.1–0.5** at the start. For an ancestor of 64–128 bytes that means **p ≈ 1–5×10⁻³ per byte written**.
- Then sweep p on a log scale from 3×10⁻⁴ to 3×10⁻², with several seeds each. Record where the ancestral lineage is lost and where the population goes extinct. That locates evo's actual threshold, U_d ≈ ln R_max, empirically.
- Set the background bit-flip rate so that background hits per genome per generation are at most about half the copy hits, matching Tierra's 1/16 versus 1/8.
- In evo's 1-byte encoding (5-bit opcode, 3-bit modifier), a random single-bit flip changes the opcode with probability 5/8 and the modifier with probability 3/8. Some modifier flips are neutral because each register has two encodings. Remember too that `store` writes are also noisy, so only writes into the offspring's region count toward U. Other writes are somatic.
- Expect genome length to respond to p, as in Gupta et al. 2016. Mean genome length against p is itself a useful hypothesis to log.

---

## UNVERIFIED list

1. Attribution of the "unbounded, uncreative" class 2 to Skusa & Bedau. Known only from Standish and MODES; the original is unread.
2. Exact typesetting of Bedau's "unbounded" definition, and the ±0.05 formula for [a₀, a₁]. Both were rebuilt from garbled PDF text, though they match the paper's numbers.
3. Units and normalisation of the *Computational Life* high-order entropy.
4. QNN definition taken from the authors' R code, not the ALIFE 2012 paper (403). Stepney & Hickinbotham 2024: abstract only.
5. Hutton's 2003 programmable-enzyme results, known only through his 2007 paper.
6. Nanopond: no author statement on limitations found. The kill-after-copy dominance comes from a third-party comment.
7. How the Evoloops "hostile environment" was built. The Salzberg & Sayama *Complexity* 10(2) findings are known via the review.
8. Venue of Mathis et al. 2024, and the percentages of Level 2 outcomes.
9. Wilke et al. 2001's exact genomic rates (0.5/2.0 are reported by a replication paper). Quantitative content of Adami 2006, "Digital genetics".
10. Typical σ for digital organisms. The lethal fraction of point mutations in Avida (Lenski et al. 1999).
11. OEE statistics for self-replicating neural CA (Sinapayen 2023).
12. The Cosmos CPU-share formula N = c·L^p, rebuilt from text because the image is missing.
13. Evita's exact mutation-rate scaling. The ECAL97 text describing it is garbled.
