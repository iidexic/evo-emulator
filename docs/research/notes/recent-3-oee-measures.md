# Open-endedness measurement, 2020-2026 (review cluster 3)

> Research notes, 2026-10-08. Cluster 3 of
> [../literature-recent-plan.md](../literature-recent-plan.md). They extend
> [oee-metrics-and-other-systems.md](oee-metrics-and-other-systems.md) §A
> (Bedau-Packard, Channon 2024, MODES, QNN, phylogeny metrics, compression
> measures), which is not repeated here.
>
> - Every fact carries a source link.
> - "Read" means the full text was read (HTML or extracted PDF). **UNVERIFIED**
>   marks a fact taken from an abstract, a landing page or a search snippet
>   only. The UNVERIFIED items are collected at the end.
> - Nothing is cited from memory. A search that found nothing is recorded.

Contents:

- How this was checked
- Terms
- 1. MODES since 2019: Bohm, Zhang & Dolson 2024; Willkens & Pollack 2023; other citers
- 2. Activity statistics since Channon 2024: de Pinho & Sinapayen 2026 (ToLSim); Flow-Lenia 2025
- 3. Ancestry-based metrics: Dolson et al. 2020; Moreno, Rodriguez-Papa & Dolson 2024/25; Moreno et al. 2025 (multi-level selection)
- 4. Knockout complexity: Moreno 2024 (cryptic sequence complexity); Moreno, Rodriguez Papa & Ofria 2024/25 (DISHTINY)
- 5. Definitions and measures from the ML open-endedness line: Hughes et al. 2024; Xu, Zhu & Van Roy 2026; OMNI; Sakana/ASAL follow-ups
- 6. One-liners (read, not relevant)
- 7. What evo can compute today, and what is missing
- UNVERIFIED list

---

## How this was checked

- Semantic Scholar "cited by" on MODES (DOI 10.1162/artl_a_00280), via the
  public Graph API on 2026-10-09: 33 citing records returned
  ([query](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1162/artl_a_00280/citations?fields=title,year,venue,externalIds&limit=100)).
  The list is incomplete: neither Bohm, Zhang & Dolson 2024 nor Willkens &
  Pollack 2023 is in it, so it was supplemented by web search. The API
  rate-limited further paper lookups (HTTP 429).
- MIT Press (direct.mit.edu, ISAL proceedings and the *Artificial Life*
  journal) returned HTTP 403 to every fetch, including via curl with a
  browser user agent and via a reader proxy. Everything hosted only there
  is abstract-only here. arXiv HTML versions were read where they exist.
- About 25 fetches in total, within the half-day box.

## Terms

- *Component*: the unit whose existence or abundance is tracked (allele,
  genotype, parameter set, gene value). Every measure below depends on this
  choice.
- *Persistence filter* (MODES): a component counts only if it has living
  descendants *t* generations later.
- *Shadow*: a neutral copy of the run with the same births and deaths but
  random parents, used to subtract drift (Bedau-Packard; Channon 2024
  resets it to the real population at each snapshot).
- *Nopout / knockout*: replace one genome site with a null instruction and
  test whether the phenotype or fitness changes; the surviving sites are
  the "meaningful" or "critical" ones.
- *Tokyo type 1*: Channon's label for unbounded evolutionary activity in
  the Bedau-Packard sense (as used by de Pinho & Sinapayen).

---

## 1. MODES since 2019

### 1.1 Bohm, Zhang & Dolson 2024, "Assessing the ability of the MODES toolbox to detect hallmarks of open-endedness", ALIFE 2024

Landing page: [direct.mit.edu/isal/proceedings/isal2024/36/10/123479](https://direct.mit.edu/isal/proceedings/isal2024/36/10/123479)
(DOI 10.1162/isal_a_00721). PDF and HTML both returned 403; the facts
below are from the abstract as shown in search snippets. **UNVERIFIED**
throughout.

- Authors Clifford Bohm, Ivy Zhang, Emily Dolson
  ([search result](https://direct.mit.edu/isal/proceedings/isal2024/36/10/123479)).
- Motivation: MODES "had only been applied to a few systems so far"; they
  built "a custom digital evolution platform (Evo-Sandbox) designed
  specifically for this purpose". **UNVERIFIED**
- Treatments: "two diversity promoting mechanisms, fit-when-rare and
  parasites", "across a range of conditions". **UNVERIFIED**
- Conclusion in the abstract: "the regions of parameter space in which
  different hallmarks of open-endedness are maximized are non-intuitive",
  and MODES "is a valuable tool for understanding the resulting
  behavior". **UNVERIFIED**
- Numbers (population, generations, replicates, filter length): not
  reachable.
- For evo: this is the closest methodological precedent (a purpose-built
  small platform with parasites, measured with MODES). Worth obtaining
  the PDF by another route before Phase 4. Inputs are the MODES inputs:
  ancestry with generation depth, genomes, and a knockout harness.

### 1.2 Willkens & Pollack 2023, "MODES analysis of prediction games", ALIFE 2023

DOI 10.1162/isal_a_00647; the MIT Press page and doi.org redirect both
returned 403. From the abstract as shown in search snippets
([ALIFE 2023 programme](https://2023.alife.org/programme/),
[ResearchGate profile listing](https://www.researchgate.net/profile/Jordan-Pollack)).
**UNVERIFIED** throughout.

- Applies MODES to the "Linguistic Prediction Game" domain: finite state
  machines playing formal-language prediction games, a complexity metric
  defined over the machines; the MODES analysis "lend[s] support to prior
  hypotheses regarding evolutionary stable states". **UNVERIFIED**
- The earlier system paper is Willkens & Pollack 2019, *Artificial Life*
  25(1):74-91, "Evolving complexity in prediction games"
  ([page](https://direct.mit.edu/artl/article/25/1/74/2913/Evolving-Complexity-in-Prediction-Games)).
- For evo: not a replicator system; the only transferable point is that
  MODES has been run on a non-Avida population with a system-specific
  complexity measure.

### 1.3 Other citers of MODES, 2020-2026 (from the Semantic Scholar list)

Read from the citation list only; each is placed here so it is not
re-read. Titles and years from
[the API result](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1162/artl_a_00280/citations?fields=title,year,venue,externalIds&limit=100).

- Papers that *compute* MODES: none in the list besides the originals.
  Lorantos & Spector 2025, "Adaptive exploration in Lenia with intrinsic
  multi-objective ranking" ([arXiv 2506.02990](https://arxiv.org/abs/2506.02990))
  mentions MODES as a measure they intend to apply; the abstract does not
  say it was computed. **UNVERIFIED**
- The Dolson/Moreno phylogeny line (Tape of Life 2020, Phylotrack 2024,
  phylogenetic signatures 2024/25, multi-level selection 2025): §3.
- Channon 2024 and Stepney & Hickinbotham 2024: already in the main notes.
- Hughes et al. 2024 (ICML): §5.
- López-Díaz et al. 2025/26, random Boolean networks: §6.
- Not relevant to evo (one line each): "Toward artificial open-ended
  evolution within Lenia using quality-diversity" (Faldor & Cully, ALIFE
  2024, [arXiv 2406.04235](https://arxiv.org/abs/2406.04235); QD search,
  no formal OEE metric in the abstract, **UNVERIFIED**); "Exploring
  Flow-Lenia universes with a curiosity-driven AI scientist" (ALIFE 2025,
  arXiv 2505.15998, not read); "Spore in the wild" (blockchain agents,
  ALIFE 2025, not read); "Evolving many worlds: PBT in Petri-dish NCA"
  (2026, §6); "Methods to estimate cryptic sequence complexity" (§4);
  "What is artificial life today, and where should it go?" (editorial);
  "A roadmap toward the synthesis of life" (*Chem* 2025); r/place
  predictability; graph-theoretic emergence; self-modifying-code
  metamodels (Complex Systems 2024); "Chapter 2: What is life?"
  (Astrobiology 2024).

Search record: "MODES toolbox" with "applied" 2022-2025 returned no
application beyond Bohm 2024 and Willkens 2023. A web search with
"evo-sandbox" on GitHub (API query `evo-sandbox MODES`) returned no
repository.

## 2. Activity statistics since Channon 2024

### 2.1 de Pinho & Sinapayen 2026, "A speciation simulation that partly passes open-endedness tests"

[arXiv 2603.01701](https://arxiv.org/abs/2603.01701), submitted 2026-03-02,
12 pages; HTML [v1](https://arxiv.org/html/2603.01701v1) read.

- System: ToLSim, a 50x50 grid with a central 30x30 spawning area; agents
  with heritable traits (speed, maxEnergy, kidEnergy, nKids, death age,
  maturity age, sensors) and non-heritable energy; cloning with a 50%
  chance of mutation per offspring
  ([HTML](https://arxiv.org/html/2603.01701v1)).
- Component: one gene value ("one gene is one property value (e.g. speed
  = 3, nKids = 6, etc.)"). The authors say future work should try
  individuals or species as components.
- Method: Channon's 2024 procedure, steps 1-3. A neutral shadow mimics the
  real run's births and deaths with randomly chosen components; the
  shadow is reset to the real population every 1,000 timesteps.
- Scale: 20 runs of 2,000,000 timesteps.
- Results: step 1 (total cumulative activity unbounded): 8 of 20 runs
  unbounded, 4 bounded, 8 unclear, "ToLSim therefore can be said to
  partially pass the test of step 1". Steps 2-3: normalised total and
  median cumulative activity bounded in all 20 runs; new activity
  "mostly null"; "none passed the second test (step 3)".
- Inputs used: per-timestep births with parent, deaths, the genome (gene
  values) of each agent, and the existence interval of each gene value.
- For evo: the exact pipeline evo could run. Components would be
  `func_hash` genotypes or template-delimited code segments
  (Channon's suggestion for Tierra-like systems); `births.csv` and
  `deaths.csv` give births, parents and deaths per tick; the shadow
  needs only those counts plus the per-birth mutation flag
  (`copy_errors > 0` or `raw_hash != parent_now_hash`). Venue: arXiv
  only as of the fetch.

### 2.2 Plantec et al. 2025, "Flow-Lenia: emergent evolutionary dynamics in mass conservative continuous cellular automata", *Artificial Life* 31(2):228-248

[arXiv 2506.08569](https://arxiv.org/abs/2506.08569); HTML
[read](https://arxiv.org/html/2506.08569). The main notes (B7) cover the
2022 preprint; this is the journal version's measurement section.

- Component: "a unique point in the parameter space"; any difference in
  parameters is a new species, acknowledged as "a current limitation of
  the study".
- No shadow run.
- Two activities: count-based, a_p^C(t) = (a_p^C(t-1) + M(p,t)) · [p in
  P^t], where M is the mass carried by parameter set p; and non-neutral
  activity, incremented by the square of the increase in the component's
  proportion of the population (QNN's rule).
- Diversity: mean pairwise Euclidean distance between parameter sets.
- Scale: 128x128 grid (1024x1024 for the multi-species demonstration),
  500,000 steps, 5 seeds, recorded every 100 steps, 64 initial creatures.
- Results: activity falls with mutation rate as a power law, slope -0.5
  (R² 0.75) for non-neutral activity and -0.71 (R² 0.71) for count-based
  activity; the dissipative and food variants have higher activity than
  vanilla (p < 1e-5), reversed when corrected for total mass.
- For evo: confirms the QNN rule is now a standard second measure
  alongside Bedau-Packard counts, and that a journal paper accepted 5
  seeds x 500k steps for this kind of claim.

### 2.3 Stepney & Hickinbotham 2024, "On the open-endedness of detecting open-endedness", *Artificial Life* 30(3):390-416

[Journal page](https://direct.mit.edu/artl/article/30/3/390/114972/On-the-Open-Endedness-of-Detecting-Open-Endedness)
(403); [author's page](https://www-users.york.ac.uk/~ss44/bib/ss/nonstd/artl23.htm)
read (abstract only). Already in the main notes (A5); new here:

- Eight long runs of spatial Stringmol, originally designed to test that
  spatial structure defends against parasites; "a typical open-endedness
  measure" (QNN, per the Semantic Scholar entry) is applied, then
  system-specific measures
  ([York page](https://www-users.york.ac.uk/~ss44/bib/ss/nonstd/artl23.htm)).
  Run length and grid size are not on the page. **UNVERIFIED** beyond
  the abstract.
- The argument: a system that is open-ended "will eventually move outside
  its current model of behavior, and hence outside any measure based on
  that model".

Search record: "Bedau-Packard applied 2021-2025 Lenia / NCA / artificial
chemistry shadow run" found no further shadow-based application beyond
Channon 2024 and de Pinho & Sinapayen 2026.

## 3. Ancestry-based metrics

### 3.1 Dolson, Lalejini, Jorgensen & Ofria 2020, "Interpreting the tape of life", *Artificial Life* 26(1):58-79

[PDF](https://lalejini.com/pubs/Dolson_et_al_2020_Interpreting_the_Tape_of_Life.pdf)
read (text extracted). Extends A6 of the main notes with the definitions
and the run scale.

- Three lineage metrics: *lineage length* (states traversed; a state can be
  an individual, a genotype, a phenotype or one trait, so length counts
  only changes of the chosen state); *mutation accumulation* (counts of
  beneficial, deleterious and neutral steps along the lineage, needing
  fitness at each step); *phenotypic volatility* (rate of phenotype change
  down a lineage).
- Four phylogeny metrics, all on the *pruned* tree (dead branches
  removed) and excluding taxa before the MRCA: *MRCA depth* ("the number
  of steps it is from the original ancestor"; "A recent MRCA implies
  frequent selective sweeps and less long-term stable coexistence between
  clades"; the authors note it never changes once a stable ecology forms,
  so also count how often it changes); *phylogenetic richness* as
  phylogenetic diversity, "the number of nodes in the minimum spanning
  tree from the MRCA to all extant taxa", or the sum of pairwise distances;
  *phylogenetic divergence* as the mean pairwise distance among extant
  taxa; *phylogenetic regularity* as the variance of pairwise distances
  (or of evolutionary distinctiveness).
- Data: the ALife data standards phylogeny format; code in Empirical.
- Scale: niching benchmarks, 1,000 organisms, 5,000 generations,
  tournament sizes 1-16, eight mutation rates, 10 replicates; Avida,
  "thirty replicate populations of size 500 for 200,000 generations in
  four different environments" (empty, limited-resource, changing
  NAND/NOT at 200 updates, and a fourth), and one 8,000,000-update
  phenotype plot.
- Findings: with ecology (Eco-EA or Avida's limited-resource environment)
  "the MRCA depth is far lower than it was for tournament selection", and
  mean pairwise distance higher; stronger selection raises coalescence
  and lowers richness and divergence; deleterious steps hover near 2,500
  across selection schemes at the benchmark scale.
- For evo: every phylogeny metric here is computable from `births.csv`
  (`child`, `executor`, `tick`) plus `deaths.csv` (`id`, `tick`) with the
  lineage parent being the executor; the pruned tree is the set of
  ancestors of the organisms alive at a census. MRCA depth and its
  change frequency are the cheapest sweep-versus-coexistence readout
  evo does not yet report.

### 3.2 Moreno, Rodriguez-Papa & Dolson 2024/25, "Ecology, spatial structure, and selection pressure induce strong signatures in phylogenetic structure", *Artificial Life* 31(2):129-

[arXiv 2405.07245](https://arxiv.org/abs/2405.07245), HTML
[v2](https://arxiv.org/html/2405.07245v2) read;
[journal page](https://direct.mit.edu/artl/article-abstract/31/2/129/130570/Ecology-Spatial-Structure-and-Selection-Pressure).

- Four metrics: sum pairwise distance (richness), Colless-like index
  (imbalance, for multifurcating trees), mean pairwise distance
  (divergence), mean evolutionary distinctiveness (divergence weighted by
  branch length).
- Inputs: a full phylogeny; also reconstructed trees from hereditary
  stratigraphy (hstrat), to test robustness.
- Regimes: 1-8 niches; island models with 1,024 islands or toroidal
  grids; tournament sizes 1, 2, 4.
- Scale: simple model 32,768 individuals for 262,144 generations, 30-50
  replicates; Avida 3,600 for about 20,000 generations, 30 replicates;
  Gen3sis 30 million years.
- Findings: "All evolutionary regimes in the simple model depress the
  Colless-like index" relative to baseline; ecology's effects are
  "generally weak compared to spatial structure and selection effects"
  but "sufficiently strong ecology can be detected in the presence of
  spatial structure"; 3% reconstruction resolution usually suffices, and
  mean evolutionary distinctiveness showed no bias even at 33%.
- For evo: spatial structure (evo's ring with locality) is the strongest
  signature, so a change in these metrics across E-series physics would
  need a spatial-only control before being read as ecology.

### 3.3 Moreno, Hasanzadeh Fard, Zaman & Dolson 2025, "Extending a phylogeny-based method for detecting signatures of multi-level selection for applications in artificial life", ALIFE 2025

[arXiv 2508.14232](https://arxiv.org/abs/2508.14232), abstract read.
**UNVERIFIED** beyond the abstract.

- Extends Bonetti Franceschi & Volz 2024: screens a phylogeny for
  mutations that appear unusually often but whose descendant clades are
  small or short-lived (individual gain, clade loss).
- Applied to an agent-based epidemiological model (within-host
  replication versus transmissibility). Detects 30% effect sizes
  reliably, not 10%.
- For evo: the parasite-versus-host trade-off is the same shape (a fast
  intruder that kills its host's patch). Needs per-mutation annotation of
  the ancestry table (which site changed), which `genomes.csv` plus
  `births.csv` give for exact and mutant births.

### 3.4 Phylotrack and the data standard

[Phylotrack](https://arxiv.org/abs/2405.09389) and
[A guide to tracking phylogenies in parallel and distributed models](https://arxiv.org/abs/2405.10183)
(both 2024, in the citation list, not read here; the standard is in
A6 of the main notes). The standard's `id`, `ancestor_list`,
`origin_time`, `destruction_time` map to evo's `child`/`id`,
`executor`, birth `tick`, death `tick`.

## 4. Knockout complexity

### 4.1 Moreno 2024, "Methods to estimate cryptic sequence complexity"

[arXiv 2404.10854](https://arxiv.org/abs/2404.10854) (ALIFE 2024),
abstract read. **UNVERIFIED** beyond the abstract.

- Problem: sites with small fitness effects, or redundant (epistatic)
  sites, escape single-site knockouts, so MODES-style "meaningful site"
  counts undercount. Three knockout-based assay procedures are proposed
  and tested on a genome model with configured site effects; estimates
  "reflect ground truth cryptic sequence complexities well".
- For evo: if MODES complexity is ever reported, this is the caveat;
  the single-knockout count is a lower bound.

### 4.2 Moreno, Rodriguez Papa & Ofria 2024/25, "Case study of novelty, complexity, and adaptation in a multicellular system" (DISHTINY)

[arXiv 2405.07241](https://arxiv.org/abs/2405.07241), HTML
[read](https://arxiv.org/html/2405.07241).

- Novelty: qualitative; ten morphologies identified over 101 "stints"
  (7,565,309 updates, 20,212 cell generations), with phylogenies rebuilt
  by parsimony over 35 64-bit genome tags.
- Complexity: *critical fitness complexity* by sequential single-site
  nopouts, keeping an instruction only if its removal changes the
  phenotype (resource concentration diverging within 2,048 updates);
  *state interface complexity* and *messaging interface complexity* by
  swapping sensor/output states or rerouting messages and testing fitness
  at p < 0.01.
- Adaptation: head-to-head competition of each stint's most abundant
  genome against the previous stint's population, 50-50 seeding, 20
  replicates, a gain if the newer wins more than 17 (p < 0.005).
- Scale: 120x120 cells; competitions on 60x60 for about 2,000-8,000
  updates.
- Finding: "a loose, sometimes divergent, relationship can exist among
  novelty, complexity, and adaptation".
- For evo: the competition assay is the same thing as E009a's invasion
  runs (founder A versus founder B, count who wins); the nopout
  complexity is what `--classify` could do with a per-site loop.

## 5. The ML open-endedness line: what they measure

### 5.1 Hughes et al. 2024, "Open-endedness is essential for artificial superhuman intelligence", ICML 2024

[arXiv 2406.04268](https://arxiv.org/abs/2406.04268), HTML
[read](https://arxiv.org/html/2406.04268).

- Definition, from an observer O with a statistical model that predicts
  artifacts X_t with loss l(t,T) (model trained on history up to t,
  predicting the artifact at T). *Novelty*: for all t and all T > t there
  is T' > T with E[l(t,T')] > E[l(t,T)]. *Learnability*: for all T and
  t < t' < T, E[l(t',T)] < E[l(t,T)]. Open-ended iff both hold.
- No computable metric is proposed; an appendix mentions
  compression-based views without developing them.
- For evo: the definition is observer-relative and needs a predictor,
  not a census. Not computable from evo's tables as stated; the nearest
  cheap proxy would be the compression-based "high-order entropy" already
  in the main notes (A7), which this paper does not endorse.

### 5.2 Xu, Zhu & Van Roy 2026, "An information-theoretic definition for open-ended learning"

[arXiv 2606.08369](https://arxiv.org/abs/2606.08369), abstract read.
**UNVERIFIED** beyond the abstract.

- Defines a "bit-equivalent": the information an agent needs to reach a
  given expected reward; an environment is open-ended if an agent can
  attain linear growth in bit-equivalent. Shown on bandit environments.
- For evo: a reward-based definition; nothing to compute from a census.

### 5.3 OMNI and OMNI-EPIC (Zhang, Lehman, Stanley, Clune 2023; 2024)

[OMNI, NeurIPS 2023 ALOE workshop](https://mlanthology.org/neuripsw/2023/zhang2023neuripsw-omni/),
abstract read; OMNI-EPIC [NeurIPS 2024](https://neurips.cc/virtual/2024/101085),
not read. **UNVERIFIED** beyond the abstract.

- What is measured: task selection quality, i.e. whether the chosen tasks
  are both learnable (learning progress) and interesting (the model's
  judgement), against uniform sampling and learning-progress-only
  baselines. "Interestingness" is a model judgement, not a statistic of
  the population.
- For evo: nothing computable from a census; the learnability half is
  learning progress, which has no analogue in a replicator soup.

### 5.4 Sakana / ASAL follow-ups

- ASAL ([Kumar et al. 2024](https://arxiv.org/abs/2412.17799)) is in the
  main notes (A7): historical nearest-neighbour novelty over CLIP
  embeddings of frames.
- Earle et al. 2026, "In search of the ingredients of open-endedness:
  replicating Picbreeder with large vision-language models"
  ([arXiv 2605.23908](https://arxiv.org/abs/2605.23908), abstract read,
  **UNVERIFIED**): measures "phylogenetic complexity" (lineage depth and
  branching of the image tree) and visual and semantic novelty against
  the human Picbreeder baseline. The phylogenetic half is the Dolson 2020
  family again, which evo's ancestry table supports.
- Berdica, Foerster, Hutter & Zela 2026, "Evolving many worlds: PBT in
  Petri-dish NCA" ([arXiv 2604.11248](https://arxiv.org/abs/2604.11248),
  abstract read, **UNVERIFIED**): rewards "historical behavioral novelty
  and contemporary visual diversity" and penalises monocultures and dead
  states. Novelty is an objective, not a detector.

Search record: "ALOE workshop open-endedness metric novelty
interestingness learnability compression 2022-2024" returned only the
Hughes definition and OMNI; no population-statistic measure came out of
the ALOE line.

## 6. One-liners (read, not relevant to evo's question)

- López-Díaz, Rivera Torres, Febres & Gershenson 2025/26,
  "Characterizing open-ended evolution through undecidability mechanisms
  in random Boolean networks" ([arXiv 2512.15534](https://arxiv.org/abs/2512.15534),
  npj Systems Biology and Applications; abstract read, **UNVERIFIED**):
  proposes Omega, the residence-time-weighted contribution of attractor
  cycle lengths over recurrent episodes; zero for a single attractor,
  vanishes for pure novelty without recurrence. Needs attractor
  detection on a state trajectory; not a population statistic.
- Sayama 2024, "Non-spatial hash chemistry as a minimalistic open-ended
  evolutionary system" ([arXiv 2404.18027](https://arxiv.org/abs/2404.18027),
  IEEE CEC 2024; abstract read, **UNVERIFIED**): evidence is unbounded
  growth of the maximal and average size of replicating higher-order
  entities. Size growth as the measure; evo's analogue would be body
  length percentiles (`traits.py`), which E-series runs show shrinking,
  not growing.
- Faldor & Cully 2024 (Leniabreeder), Lorantos & Spector 2025: QD search
  in Lenia, no detector computed (§1.3).

## 7. What evo can compute today, and what is missing

Inputs evo records ([../../instrumentation.md](../../instrumentation.md)):
`census.csv` (tick, now_hash, count); `orgs.csv` (per living organism per
census: id, parent, birth_tick, hashes, stats); `births.csv` (tick,
child, executor, source, copy_errors, raw_hash, parent_hash,
parent_now_hash); `deaths.csv` (tick, id, cause, age, offspring, hashes,
stats); `genomes.csv` (raw_hash, func_hash, parent_hash, bytes); and the
`--classify` harness (one genome alone, counts exact births).

| Measure | Inputs needed | From evo's files | Missing |
|---|---|---|---|
| QNN (A5; used by Stepney 2024, Flow-Lenia 2025 as non-neutral activity) | (time, species, count) | `census.csv` directly; group by `func_hash` via `genomes.csv` | nothing |
| Bedau-Packard A_cum, D, A_new with Channon 2024 shadow (A1, A2; de Pinho 2026) | births with parent and child component, deaths, per-birth mutation flag, census per snapshot | `births.csv` (`executor`, `raw_hash`, `parent_now_hash`, `copy_errors`), `deaths.csv`, `census.csv` | the shadow run itself (offline Python, no simulator change); a component choice (genotype by `func_hash`, or template-delimited segments) |
| MODES change, novelty, ecology (A4) | persistent components: ancestry with generation depth, census | `births.csv` (`child`, `executor`, `tick`) gives the tree; generation depth by walking `executor` links; persistence = descendants alive at tick + t generations from `orgs.csv`/`deaths.csv` | choice of t in generations (Dolson: about the population size); nothing in the simulator |
| MODES complexity (A4; Moreno 2024 caveat) | per-site knockout of each persistent genome | `--classify` harness, with a per-site `pad` replacement loop and "meaningful" = exact-birth count drops | the loop (analysis-side, calls the binary per variant); cost about `len` runs per genome |
| MRCA depth and change count, phylogenetic diversity, mean pairwise distance (Dolson 2020) | pruned phylogeny with origin and destruction times | `births.csv` + `deaths.csv` + `orgs.csv` at a census | nothing; a Python walk over at most a few hundred thousand rows |
| Competition fitness (DISHTINY) | two founders in one world, replicate seeds | E009a `--founder` runs | nothing |
| Hughes 2024 novelty/learnability, OMNI, Xu 2026 | a predictor or reward model | none | not a population statistic |

The pick for E009 onward, in order of cost: QNN per census interval over
`func_hash` groups (zero new code beyond a 20-line reader), then MRCA
depth and its change count at each census (sweeps versus coexistence,
which is exactly what the parasite experiments ask), then MODES change
and novelty with the persistence filter at t equal to the mean
population in generations. The Channon shadow and MODES complexity are
the two that need new machinery; both are analysis-side.

## UNVERIFIED list

- Bohm, Zhang & Dolson 2024: everything (abstract snippet only; MIT Press
  403).
- Willkens & Pollack 2023: everything (snippets only).
- Lorantos & Spector 2025: whether MODES was computed.
- Stepney & Hickinbotham 2024: that QNN is the "typical measure", and the
  run scale.
- Moreno et al. 2025 (multi-level selection), Moreno 2024 (cryptic
  complexity), Xu et al. 2026, OMNI, Earle et al. 2026, Berdica et al.
  2026, López-Díaz et al. 2025, Sayama 2024, Faldor & Cully 2024: abstract
  only.
