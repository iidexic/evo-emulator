# Measures and phylogeny methods, ALIFE 2023-2026 (review cluster 7)

> Compiled 2026-10-12. Cluster 7 of round 2 in
> [../literature-recent-plan.md](../literature-recent-plan.md). Extends
> [recent-3-oee-measures.md](recent-3-oee-measures.md) (MODES since 2019,
> Dolson 2020 phylogeny metrics, Moreno 2024/25 journal paper, knockout
> complexity), which is not repeated here.
>
> - Every fact carries a source link. Numbers are as printed.
> - "Read" means the full text was read (PDF, arXiv HTML, or the authors'
>   LaTeX source). **UNVERIFIED** marks a fact taken from an abstract only.
> - "(inference)" marks my reasoning, not the paper's.
> - Nothing is cited from memory. Searches that found nothing are recorded.

## Purpose

Three questions from the round-2 plan, cluster 7:

1. Does anything here change the measure chosen in round 1 (QNN over
   `func_hash` groups per census interval, plus MRCA depth and mean
   pairwise distance from the ancestry table)? Which phylometrics are
   computable from evo's ancestry table, and which would separate the
   ring's spatial structure from ecological interaction (parasites)?
2. Is MODES worth keeping as a candidate, given what Bohm, Zhang & Dolson
   2024 found it can and cannot detect?
3. Scale bars: population, generations and replicates in Moreno et al.
   2024 and Singhvi et al. 2025.

Plus: clear the UNVERIFIED tags on Willkens & Pollack 2023 and Bohm 2024,
and resolve four garbled ALIFE titles in
[isal-proceedings-2023-2026.md](isal-proceedings-2023-2026.md).

## How each paper was checked

MIT Press (`direct.mit.edu`) was not fetched (403 to scripts, per the
plan). Abstracts came from the OpenAlex and Crossref APIs. Open copies
were searched on arXiv (export API, by title and by author), Semantic
Scholar (`openAccessPdf`), OpenAlex `locations`, Zenodo, OSF and GitHub.

| Paper | DOI | How read | Source used |
|---|---|---|---|
| Bohm, Zhang & Dolson 2024 | [isal_a_00721](https://doi.org/10.1162/isal_a_00721) | full text | PDF downloaded by hand, `docs/downloaded-papers/isal_a_00721_Bohm-Zhang-Dolson.pdf` (10 pages; text extracted, figure pages rendered and viewed); code archive [Zenodo 10.5281/zenodo.11539390](https://doi.org/10.5281/zenodo.11539390) for the sweep grid |
| Willkens & Pollack 2023 | [isal_a_00647](https://doi.org/10.1162/isal_a_00647) | full text | PDF downloaded by hand, `docs/downloaded-papers/isal_a_00647_Willkens-Pollack.pdf` (9 pages) |
| Moreno, Dolson & Rodriguez-Papa 2023 | [isal_a_00694](https://doi.org/10.1162/isal_a_00694) | full text | authors' LaTeX source at the `camera-ready` tag of [github.com/mmore500/hstrat-evolutionary-inference](https://github.com/mmore500/hstrat-evolutionary-inference/tree/camera-ready) (`text/body/*.tex`, figure captions); its abstract is word-for-word the [OpenAlex abstract](https://api.openalex.org/works/doi:10.1162/isal_a_00694). Journal extension [arXiv 2405.07245v2](https://arxiv.org/html/2405.07245v2) consulted for the spatial-background question |
| Willkens 2026 | [isal.a.994](https://doi.org/10.1162/isal.a.994) | full text | author's LaTeX source [spg_paper/spg.tex](https://github.com/twillkens/Spatial_Prediction_Game/blob/main/spg_paper/spg.tex) (a compiled `spg.pdf` sits beside it); abstract identical to the [Crossref abstract](https://api.crossref.org/works/10.1162/isal.a.994) except that the source has a placeholder `\url{...}` where the published abstract gives [Zenodo 20794188](https://zenodo.org/records/20794188) |
| Willkens & Pollack 2024 | [isal_a_00729](https://doi.org/10.1162/isal_a_00729) | abstract only | [OpenAlex](https://api.openalex.org/works/doi:10.1162/isal_a_00729); datasets only at [Zenodo 10.5281/zenodo.11626077](https://doi.org/10.5281/zenodo.11626077) |
| Moreno, Yang, Dolson & Zaman 2024 | [isal_a_00830](https://doi.org/10.1162/isal_a_00830) | full text | [arXiv 2404.10861v3](https://arxiv.org/html/2404.10861v3) (2 June 2024); abstract matches OpenAlex |
| Singhvi, Wagner, Dolson, Zaman & Moreno 2025 | [isal.a.890](https://doi.org/10.1162/isal.a.890) | full text (scale sections) | [arXiv 2508.15074v1](https://arxiv.org/html/2508.15074v1); abstract matches Crossref |
| Nehaniv, Derets & Do 2026 | [isal.a.990](https://doi.org/10.1162/isal.a.990) | abstract only | [Crossref](https://api.crossref.org/works/10.1162/isal.a.990) |
| Bohm 2026 | [isal.a.937](https://doi.org/10.1162/isal.a.937) | abstract only | [Crossref](https://api.crossref.org/works/10.1162/isal.a.937) |

A LaTeX source can differ in small ways from the published PDF; where a
fact comes from a source file rather than the publisher's PDF, the table
says so.

## Terms

- *Persistence filter* (MODES): keep only individuals that still have
  living descendants a fixed number of generations later, the *filter
  depth*. Filters out short-lived mutants.
- *Change / novelty / ecology / complexity* (MODES): count of persistent
  types not present one delay earlier; count never seen before; Shannon
  entropy of persistent types; most informative sites in any persistent
  type. Definitions in `literature.md` §3.3.
- *Knockout*: replace or remove one genome site and see whether fitness
  drops; sites whose loss hurts are "informative".
- *Phylometric*: a number computed from the shape of a phylogeny.
  *Ancestor count* here is the number of internal (non-leaf) nodes after
  removing nodes with a single child; *mean pairwise distance* (MPD) is
  the mean number of nodes between two extant tips; *sum pairwise
  distance* is the total; *evolutionary distinctiveness* (ED) quantifies
  "how evolutionarily different that taxon is from all other taxa in the
  phylogeny", averaged over extant tips for *mean ED*, and is "heavily
  influenced by branch length"; the *Colless-like index* is a tree
  imbalance measure extended to trees whose nodes can have more than two
  children (all as defined in Moreno 2023, §3).
- *Hereditary stratigraphy* (hstrat): random "fingerprint" values
  appended to a genome each generation so a phylogeny can be estimated
  afterwards without central tracking. evo tracks every birth exactly,
  so it does not need this.
- *PE*: processing element, one core of the Cerebras wafer-scale chip.

---

## 1. Bohm, Zhang & Dolson 2024, "Assessing the ability of the MODES toolbox to detect hallmarks of open-endedness", ALIFE 2024

Read from the PDF (see table). Code and settings from the
[Zenodo archive](https://doi.org/10.5281/zenodo.11539390) (GitHub
[cliff-bohm/ALIFE_2024_MODES](https://github.com/cliff-bohm/ALIFE_2024_MODES/tree/2024_ALIFE_EVO_SANDBOX));
facts from the code are marked "(code)".

### System (Evo-Sandbox)

- Bit strings of length 15; "roulette selection (i.e., fitness
  proportional)"; offspring are mutated copies, "each bit in the genome
  has a .1% chance to flip"; "Experiments are run with population size
  500, for 200,000 generations." Figure 1 caption: "Data are from 10
  replicates."
- Built on MABE; the Evo-Sandbox files are `code/World/MODESWorld/`
  (code, README).
- Three fitness criteria, added together, each scaled by a "fitness
  control value"; 0 turns a criterion off; "The relative values of these
  controls is not meaningful, as the ranges of each fitness criterion
  are unrelated."
- (code) The summed score s becomes a selection weight
  `pow(selectionBenefit, s - max s)`, with `CONTROL_selectionBenefit =
  1.1` in `work/settings_world.cfg` (the code default is 1.5).
- *Target*: proportion of ones in the genome (0.0 for none, 1.0 for 15).
- *Fit-when-rare (FWR)*, labelled "Fit-when-Rare (Fitness Sharing)": for
  every pair of genomes, comparison value 1.0 if they differ in more than
  the upper threshold (10) bits, 0.0 if at most the lower threshold (5),
  and (differences − lower)/(upper − lower) in between; "The FWR fitness
  is then just the sum of the comparison values divided by the population
  size." (code) In the sweep file the paper's FWR variable sets
  `CONTROL_SHARE`.

### Parasite parameters

All from the paper's Parasites section unless marked (code):

| Parameter | Value |
|---|---|
| Parasite genome | 15 bits, same length as hosts |
| Infection rule | parasite must "match at least 10 bits of the host genome exactly"; a host with fewer than 10 ones is "automatically infected" |
| Generalist cost | "penalized 5% of their resource gain for each additional one in their genome over 10" |
| Migration | after each host generation, each parasite has an "80% change [chance] to migrate to a randomly selected host" |
| Parasite updates per host generation | 10 ("parasites undergo 10 time update steps"); (code) `PARASITE_gensPerHost = 10` |
| Death | a parasite that "has lived for at least 5 parasite updates has a 50% to die" |
| Resource | 1.0 per update if it infects, minus the penalty, with "±10%" noise |
| Reproduction | at 4 resource, one offspring, cost 4; offspring mutated at 0.1% per bit |
| Cap | more than 20 on a host after births: random culling to 20 |
| Floor | every host keeps at least one parasite; a lone parasite cannot migrate or die |
| Host cost | "−1 times the average number of parasites on that host over the 20 parasite updates" (the paper says 10 updates above and 20 here; the config says 10), multiplied by the parasite control value |

- MODES was applied to the host population only: "we intentionally do
  not apply MODES to the parasite population."
- An earlier design used 50-bit hosts and short parasites matching a
  substring. There, "increased parasite costs always decreased ecology",
  attributed to "an unstable ecological coexistence regime, where the
  parasites were promoting constant diversification into unparisitized
  niches (analogous to the pure red-queen region ...)", with "low but
  constant change and novelty, as the genospace was so large" (the PDF
  prints the size as a garbled "2^50") "that any repetition in niches was
  unlikely". The 15-bit redesign "was sufficient for our system to
  reproduce Zaman et. al's results, implying that the size and/or
  topology of the parasite search space may be important in determining
  the population dynamics that parasites create."

### MODES settings

- Persistence filter by "ancestor tag inheritance" (Lalejini et al.
  2019). Five filter depths: 100 (N/5), 250 (N/2), 500 (N), 1,000 (2N),
  2,500 (5N); "In prior work, a filter depth of two times the population
  size (2N) was generally used". (code) `MODES_filterDepthList =
  100-,250-,500+,1000+,2500+`.
- Change delay set equal to the filter depth. Ecology is the Shannon
  entropy of persistent types "based on their representation when they
  were alive"; at filter depth 0 it "is simply the Shannon entropy of the
  population".
- Complexity is system-specific: "the absolute value of the number of
  ones in the genome minus half the genome length". Complexity metrics
  for FWR and parasites were developed but "the coevolutionary nature of
  both of these mechanisms, combined with the locality of parasites, made
  evaluating the results of those metrics challenging." No knockouts were
  used.

### Sweep

- Shown in the figures: Target 0.0, 0.5, 1.0, 2.5; FWR axis ticks 0,
  150, 350, 1000, 16000; parasite axis ticks 0.00, 0.075, 0.50, 2.50,
  10.0; Figure 1 rows at parasites 0.00, 2.50, 7.50; Figure 2 rows at
  FWR 0, 300, 8000; heat maps (Figure 3) at filter depth 1,000.
- (code) The full grid, on the commented "run the data set" line of
  `work/mq_conditions.txt`: `FWR=0,25,50,100,150,200,250,300,350,400,450,500,7:50,1000,2000,4000,8000,16000`
  (`7:50` as written), `TAR=0.0,0.5,1.0,2.5`,
  `PAR=0.00,0.025,0.05,0.075,0.10,0.25,0.50,0.75,1.00,2.50,5.00,7.50,10.0`.

### Which MODES metric moved under parasites

- **Ecology at high filter depth.** "Intermediate costs produced higher
  levels of high-filter-depth ecology ... consistent with prior results
  showing that parasites promote diversity (Zaman et al., 2011)." Low at
  low cost ("insufficient selective pressure") and low again at high
  cost, where "the parasites cost is so high that having more than a
  single parasite is lethal. Survival, then, depends upon having no extra
  parasites, which may come down to luck."
- **Ecology with change and novelty together.** Under FWR, more ecology
  went with less change and novelty (stable coexistence); "in the
  parasite analysis, we see that higher rates of ecology tend to
  associate with elevated change and novelty", read as "semi-stable
  host/parasite pairs" with "subtle genetic variation ... within hosts as
  they continuously attempt to escape infection."
- **Ecology across filter depths.** "under high parasite cost and low FWR
  cost ... the ecology metric was high at a low filter depth but low at a
  high filter depth", read as "unstable ecology, in which clades
  specialized on different niches regularly evolve and then die out."
- **Interaction with FWR.** With no parasites, FWR 4000, 8000 and 16000
  give ecology 0 at depth 2,500 ("complete coalescence always occurs in
  less than 2500 generations"); at parasite values 2.50 and 7.50 the FWR
  4000 point "moves up", read as "stable coexistence of two lineages".
- Complexity (|ones − 7.5|) rises at the highest parasite values in
  Figure 2 (read from the figure; the text does not discuss it).

### What the authors say MODES cannot do

- "Distinguishing drift from unstable ecology without manual examination
  would be a worthwhile topic for future research."
- Depth-0 ecology "can be inflated by transient sources of diversity,
  such as a high mutation rate".
- "In cases of strong selection, the number of persistent individuals
  may be one, resulting in a maximum change and novelty value of one";
  at high filter depth "change and novelty may provide less information
  ... a lower filter depth may provide a more accurate picture."
- Non-additivity: "the values of parasites and FWR that promote the
  highest metrics are different when both of these dynamics are present
  than when they are acting in isolation."

### For evo (inference)

- Closest precedent in *method* (a parasite-cost sweep read with MODES at
  several filter depths), not in *substrate*: bit strings, no execution,
  parasites a separate population on each host and excluded from the
  metrics. In evo hosts and parasites share one ring and one census.
- The 50-bit preliminary design is the warning for evo: a large genome
  space gave constant diversification, low constant change and novelty,
  and long-depth ecology that fell with parasite cost. evo's byte genomes
  are a far larger space, so a flat ecology at 2N would not show that
  parasites do nothing.
- The high-cost regime ("more than a single parasite is lethal") is the
  bit-string analogue of E010's cost dial reaching collapse before
  defence.

## 2. Willkens & Pollack 2023, "MODES Analysis of Prediction Games", ALIFE 2023

Read from the PDF (see table). Code stated at
[github.com/twillkens/coevo](https://github.com/twillkens/coevo).

- Domain: the linguistic prediction game of Moran & Pollack 2019 (not
  Willkens & Pollack; see the tag ledger). Each organism is a
  deterministic finite state machine (DFSM): each state emits a 0 or 1,
  and the partner's emitted bit selects one of two transitions. A game
  ends when the pair revisits a state pair; fitness is the mean score in
  that loop. Cooperative partners both seek to match (or mismatch);
  competitive ones have opposite goals. Ecosystems: Control (no
  selection), Coop, Comp, 3-Comp, and 3-Mixed (a "host" cooperating with
  a "symbiotic" population and competing with a "parasitic" one).
- Evolution starts from a single-state machine; fitness-proportionate
  selection; four equally likely mutations (add state, remove state,
  change label, reassign link).
- Scale: "population size N of fifty"; persistence window "t ... the same
  size as the population, N: 50"; "forty trials"; Figure 3's axis runs
  to 50,000 generations. Two machines count as the same component if
  isomorphic as labelled graphs.
- Knockouts: the MODES knockout "was found to have detrimental fitness
  effects in this domain on account of interactions between sites", so
  an 8-step "fitness-preserving heuristic" was used instead (remove
  untraversed states, then try removing each remaining state from newest
  to oldest, keeping the removal if fitness does not drop, then minimise
  with Hopcroft's algorithm). Note the paper describes the generic
  knockout as "remove that site", where `literature.md` §3.3 has Dolson
  2019 replacing it with a null instruction.
- Results: Comp-KO change slope "X = -0.000016, p < 0.722" and novelty
  slope "X = -0.00022, p < 0.0001" over the last 25,000 generations, read
  as cycling; Coop-KO complexity far below Control (Glass's Δ = 26.5);
  3-Mixed-KO complexity far below unpruned 3-Mixed (Δ = 13.11), so "the
  complexity observed in the 3-Mixed ecosystem appears largely
  nonadaptive".
- For evo (inference): a single-site knockout loop around `--classify`
  will meet the same interacting-site problem, and growth in body size
  can be non-adaptive bloat (cf. nop and template inflation,
  `literature.md` §4.6). MODES has here been used with t = N, not 2N.

## 3. Moreno, Dolson & Rodriguez-Papa 2023, "Toward Phylogenetic Inference of Evolutionary Dynamics at Scale", ALIFE 2023

Read from the authors' camera-ready LaTeX (see table). The journal
version ([arXiv 2405.07245](https://arxiv.org/html/2405.07245v2)) says it
"extends a conference paper Moreno et al., (2023), by adding (1)
replications of experiments in full-fledged evolution simulation
frameworks (i.e., Avida and Gen3sis ...) and (2) refining the set of
phylogeny metrics"; recent-3 §3.2 covers it and is not repeated.

### Model and regimes

- Genome: "a single floating-point value, with higher magnitude
  corresponding to higher fitness". "Population size 32,768 (2^15)";
  tournament selection, synchronous generations; Gaussian mutation added
  to all genomes; runs end at "262,144 (2^18) generations"; "Each run
  required around 4 hours"; "each treatment comprised 50 replicates".
- **Space is a ring of islands:** "individuals were evenly divided among
  1,024 islands and only competed in selection tournaments against
  sympatric population members. Islands were arranged in a
  one-dimensional closed ring and 1% of population members migrated to a
  neighboring island each generation."
- Ecology: niches with fixed slots; organisms swap niche with probability
  3.0517578125 × 10^-8 per generation ("one niche swap would be expected
  every 1,000 generations").
- Regimes: plain (tournament 2); weak selection (1); strong selection
  (4); spatial structure (2, 1,024 islands); weak 4-niche ecology (swap
  probability ×100); 4-niche ecology; and "8 niche ecology: tournament
  size 8 with 4 niches" as printed (the journal version defines its "rich
  ecology" as "tournament size 2 with 8 niches"). Follow-up: plain and
  the three ecology regimes, all "over 1,024 islands".
- Sensitivity: runs of 32,768 and 98,304 generations, and an exponential
  mutation operator ("deleterious mutations are not possible").
- Metrics: ancestor count (internal nodes, unifurcations stripped),
  Colless-like index, MPD ("measured in terms of the number of nodes in
  between the pair, not in terms of branch lengths"), mean ED ("heavily
  influenced by branch length").

### Results that bear on space versus ecology

No spatial background (each regime against plain):

| Phylometric | Spatial structure | Ecology | Selection |
|---|---|---|---|
| Ancestor count | up | "no significant relationship" | weak up, strong down |
| MPD | up | "None of the ecological regimes induced significant changes" | strong down; weak inconsistent (see note) |
| Mean ED | up, the largest effect | up, scaling with niche count, but "more strongly driven by weak selection and even more strongly driven by spatial structure" | weak up, strong down |
| Colless-like | down | down | down ("depressed under all evolutionary regimes") |

(Note: the results paragraph says MPD went "significantly higher under
weak selection", but the heat-map paragraph says weak and strong
selection "both significantly decrease Colless-like index and mean
pairwise distance", and the conclusion repeats the decrease; the source
is inconsistent on weak selection.)

- Authors' reading: "Ancestor count and mean pairwise distance may play a
  role in identifying ecological dynamics, as ecological dynamics --- in
  contrast to other factors such as spatial structure and changes in
  selection pressure --- have little to no discernible effect on these
  phylometrics." Colless-like "appears to be the least useful metric".

With a spatial background (all regimes on 1,024 islands, ecology versus
spatial-only plain):

- Mean ED: ecology still "drove significant increases".
- Ancestor count: "under ecological conditions sharply exceeded ancestor
  count under non-ecological conditions", and rose again from 4 to 8
  niches.
- MPD: "the 8 niche regime significantly decreased mean pairwise distance
  under spatially-structured conditions. This was not the case without
  spatial structure."
- Colless-like: "spatial structure mutes the effects of ecology"; only 8
  niches lowered it.
- Conclusion: "background spatial population structure can accentuate the
  phylometric signature of ecology."

Reconstruction (not needed by evo, which tracks exactly): 3% resolution
usually suffices; mean ED showed no bias even at 33%; ancestor count
stayed biased even at 1%.

### Caveats from the journal extension (arXiv 2405.07245v2)

- The sign of ecology's effect on mean ED without space differs between
  versions: the journal says mean ED "significantly decreased under
  strong selection and under ecological regimes", while its own
  spatial-background section says "As in prior experiments, all ecology
  treatments drove significant increases in mean evolutionary
  distinctiveness and sum pairwise distance".
- Avida with a toroidal grid ("Avidians replicating exclusively between
  neighboring population sites"), 30 replicates, population 3,600,
  100,000 updates ("c. 20k generations"): "Spatial-background rich
  ecology results from Avida agreed with the simple model. However,
  significant phylometric effects were not detected from the ecology and
  weak ecology treatments under spatial structure conditions." Rich
  ecology there is 28 rewarded tasks, each with its own resource.
- Tree unit matters: in Avida, genome-level trees "were notably different
  than those using individual-level tracking", including "changes in the
  sign of some treatment effects".

### For evo (inference)

- The 2023 spatial treatment (islands on a one-dimensional closed ring
  with neighbour migration) is the nearest published structure to evo's
  ring with locality.
- evo cannot turn space off, so the 2023 follow-up design, ecology versus
  plain on the same spatial background, is the right one: parasite runs
  against parasite-free runs at the same `--locality` and world size.
- On that design the readouts are ancestor count (up), sum pairwise
  distance and mean ED (up), MPD (down only for strong ecology). Avida on
  a grid detected only its strongest ecology at n = 30, so a null result
  for evo's parasites would not be evidence of no ecology.
- The spatial term itself is measured by varying `--locality` (radius of
  every memory operation, default 512 on a 65,536-byte ring,
  `evo-core/src/config.rs`) or `--alloc-far` (E002), with parasites held
  fixed.
- Results must be read on individual-level trees to be comparable;
  `func_hash` genotype trees may flip signs.

## 4. Willkens 2026, "MODES Analysis of Spatial Prediction Games with Logic Gate Cellular Automata", ALIFE 2026

Read from the author's LaTeX source (see table).

- Domain: two coevolving populations ("learners" and "tests") of
  recurrent Boolean circuits, both running as cellular automata on a
  "4 × 4 toroidal grid over 32 timesteps"; learners win if mean white
  density exceeds 0.5. Genotype: 2-input gates, "a neutral space of 200
  inactive nodes"; mutation 0.01 per truth-table bit and per edge.
- Conditions: Random (drift-only control), (μ + λ) with μ = 50, λ = 50,
  and CFS+QMEU (competitive fitness sharing with the QMEU test archive).
  "Evolution runs for 5,000 generations with MODES checkpoints every 50
  generations. We run 20 seeds per condition." The persistence filter
  depth is not stated; "Different persistence filter lengths could also
  be tested".
- Knockout complexity (KO): replace each node's truth table with an
  identity relay (PASS_A, then PASS_B), keep it knocked out if no match
  outcome changes, then test pairs of redundant nodes jointly. "knockout
  complexity is measured against the coevolved test population ... the
  metric captures functional complexity relative to the current
  competitive context."
- Results (late-game means, generations 3,750–5,000): KO 86 ± 12
  (CFS+QMEU), 66 ± 7 ((μ + λ)), 31 ± 5 (Random). KO slope per 1,000
  generations: +8.4 (p = .033), +0.5 (p = .94), +9.2 (p = .042). Change
  and novelty "nearly identical, suggesting that duplicates very rarely
  occur"; ecology higher under CFS+QMEU and Random than (μ + λ).
- For evo (inference): the drift-only control showed significant KO
  growth, so any complexity trend in evo needs a no-selection baseline.
  KO measured against the current opponents is the right definition for
  a parasite, whose function exists only next to a host (evo's two-genome
  harness in `analysis/e005_parasites.py`), but it makes KO
  context-dependent.

Background, Willkens & Pollack 2024, "Coevolutionary Heuristics for
Maximization of Expected Utility"
([abstract](https://api.openalex.org/works/doi:10.1162/isal_a_00729),
**UNVERIFIED**): proposes QueMEU, "a novel test generator and memory
mechanism that uses a sampling policy over a queue", tested on numbers
games and density classification. Not a measurement paper; not read
further.

## 5. One line each

- **Moreno, Yang, Dolson & Zaman 2024** ([arXiv 2404.10861v3](https://arxiv.org/html/2404.10861v3)):
  island-model GA on the Cerebras WSE. Abstract: "upwards of 1 million
  generations a minute for population sizes reaching 16 million agents".
  On-hardware validation: "four on-hardware replicates of each treatment
  instantiated on 10k (100×100), 250k (500×500) and 562.5k (750×750) PE
  arrays", "halted each PE after it elapsed 1 million generations",
  tournament size 5, phylometrics from "10k sampled end-state agents".
  Emulator benchmarks used "a per-PE population size of 32". Result:
  "purifying-only treatment phylogenies consistently exhibited greater
  sum branch length and mean evolutionary distinctiveness" than runs
  with beneficial mutations (selective sweeps), "the effect on branch
  length particularly strong". (inference) Supports branch-length
  metrics next to MRCA depth as evo's sweep detector.
- **Singhvi, Wagner, Dolson, Zaman & Moreno 2025** ([arXiv 2508.15074v1](https://arxiv.org/html/2508.15074v1)):
  trie-building reconstruction, "300-fold speedup" at 10,000 tips. Data:
  "run for 5 million generation cycles"; "A per-PE population size of 256
  organisms ... net population size of 190.8 million organisms";
  tournament size 2; two treatments (adaptive, purifying), one run each,
  "Real-time runtime under each treatment was 24 minutes"; abstract: "1
  billion genome datasets ... encompassing 954 trillion replication
  events", reconstruction in "2.6 and 2.9 hours". Microbenchmarks 3–5
  replicates. Accuracy check: "populations of 100 agents under neutral
  evolution conditions, with runs lasting 500 generations".
- **Nehaniv, Derets & Do 2026** ([abstract](https://api.crossref.org/works/10.1162/isal.a.990),
  **UNVERIFIED**): Krohn–Rhodes complexity bounds of Fogel's evolved
  finite automata; "environmental complexity and organismal complexity
  are distinct"; evolved traversers sit "within a few levels of the
  theoretical maximum". (inference) Needs an automaton's transformation
  semigroup; nothing comparable is defined for evo's byte programs.
- **Bohm 2026** ([abstract](https://api.crossref.org/works/10.1162/isal.a.937),
  **UNVERIFIED**): argues "evolution by natural selection is not a
  separate principle added to nature but a special case of persistence";
  framing only, the same persistence idea as the MODES filter.

## 6. Housekeeping: the four "System.Xml.XmlElement" titles

Crossref, OpenAlex and Semantic Scholar all carry the garbled title.
Abstracts from [OpenAlex](https://api.openalex.org/works/doi:10.1162/isal_a_00572)
(same URL pattern for each DOI); titles from the
[ALIFE 2023 programme](https://2023.alife.org/programme/) and, for
00763, the [University of Namur repository copy](https://pure.unamur.be/ws/files/99905088/ALife_conference_2024.pdf),
whose cover page cites `10.1162/isal_a_00763`.

| DOI | Title | Authors | Subject (from abstract) | Relevant to evo |
|---|---|---|---|---|
| [isal_a_00572](https://doi.org/10.1162/isal_a_00572) | Daphnia as a living sensor for underwater biohybrid systems | Rajewicz, Schmickl, Thenius | Daphnia swimming behaviour calibrated against salinity | no |
| [isal_a_00629](https://doi.org/10.1162/isal_a_00629) | Life-like Behavior of an Oil Droplet in an Aqueous Surfactant Solution: Comparative Analysis with Tetrahymena Movement and Numerical Investigation | Adachi, Kojima, Ikegami | oil droplet motion versus Tetrahymena; Langevin simulation | no |
| [isal_a_00672](https://doi.org/10.1162/isal_a_00672) | The Nexican Stand-Off: Social Contracts and Popular Legitimacy in n-Player High Stakes Resource Competition Games (spelling as in the programme, poster 193; not checked against the published PDF) | Scott, Pitt | n-player Mexican standoff, social contracts and "buy-in" in a multiagent system | no |
| [isal_a_00763](https://doi.org/10.1162/isal_a_00763) | Hybrid Modelling of Stimuli-Based and Density-Induced Aggregation in C. elegans | Vellinger, Antonic, Tuci | C. elegans aggregation: mathematical model plus agent-based simulator | no |

(inference) All four titles contain an italicised term (Daphnia,
Tetrahymena, n, C. elegans), which is probably what broke the Crossref
deposit.

## 7. UNVERIFIED-tag ledger

### `recent-3-oee-measures.md` §1 (edited in place, dated 2026-10-12)

| Claim | Status |
|---|---|
| §1.1 Bohm 2024: authors Bohm, Zhang, Dolson | confirmed |
| §1.1 "had only been applied to a few systems so far"; Evo-Sandbox "designed specifically for this purpose" | confirmed (abstract text) |
| §1.1 two diversity mechanisms, "fit-when-rare and parasites", "across a range of conditions" | confirmed |
| §1.1 conclusion quote | confirmed; second half reads "MODES is, in fact, a valuable tool for understanding the resulting behaviors" |
| §1.1 numbers "not reachable" | corrected: 500, 200,000 generations, 10 replicates, depths 100–2,500 |
| §1.1 "Inputs are ... a knockout harness" | corrected: no knockouts; complexity = |ones − 7.5|; parasites not analysed |
| §1.2 Willkens 2023: MODES on the linguistic prediction game, "lending support to prior hypotheses regarding evolutionary stable states" | confirmed |
| §1.2 "finite state machines playing formal-language prediction games" | corrected: DFSMs emitting one bit per step, rewarded for matching or mismatching the partner's bit |
| §1.2 "The earlier system paper is Willkens & Pollack 2019, *Artificial Life* 25(1):74-91" | corrected: Moran & Pollack 2019, DOI [10.1162/artl_a_00281](https://doi.org/10.1162/artl_a_00281) (Crossref: Nick Moran, Jordan Pollack, 25(1):74–91), cited so in the paper |

### `literature.md` (not edited; for whoever extends it)

The plan places these tags in §6.3.3, but §6.3.3 is "Rule-by-rule
emergence studies" and does not mention either paper. The tagged claims
are in **§6.2, paragraph "MODES since 2019"** (line 357 on 2026-10-12),
with one follow-up in §6.5.

| Claim in §6.2 / §6.5 | Status | Correct wording |
|---|---|---|
| "Applied outside Avida twice" | corrected | "Outside the original paper (Avida and NK landscapes), applied by Willkens & Pollack 2023 and Bohm, Zhang & Dolson 2024, and since by Willkens 2026; Soros 2018 applied many of its concepts to Chromaria (per Bohm 2024)." |
| Willkens & Pollack 2023 "(abstract only, **UNVERIFIED**) on finite-state prediction games" | confirmed | "(full text read 2026-10-12) on deterministic finite state machines playing bit-prediction games (N = 50, 40 trials, 50,000 generations)" |
| Bohm, Zhang & Dolson 2024 "(abstract only, **UNVERIFIED**, MIT Press blocked the PDF), who built Evo-Sandbox with fit-when-rare and parasites as diversity mechanisms" | confirmed | add "(full text read 2026-10-12; 15-bit genomes, population 500, 200,000 generations, 10 replicates)" |
| Quote "the regions of parameter space in which different hallmarks of open-endedness are maximized are non-intuitive" | confirmed verbatim | unchanged |
| "That paper is the closest measurement precedent for evo's parasite work and is worth obtaining by another route." | qualified | "closest precedent in method (a parasite-cost sweep read with MODES at five filter depths), not in substrate: bit strings, no execution, and parasites a separate population excluded from the metrics" |
| §6.5 "Obtain Bohm, Zhang & Dolson 2024 before Phase 4 measurement decisions" | done | read 2026-10-12; see this file §1 |

Not a tag, but related: `literature.md` §3.3 gives the MODES filter as "t
about equal to population size"; Bohm 2024 says prior work "generally
used" 2N, and Willkens 2023 used t = N.

## 8. Answers

### What evo's ancestry table supports

Inputs (`docs/instrumentation.md`): `births.csv` (`tick, child,
executor, source, start, ...`), `deaths.csv` (`tick, id, ...`),
`orgs.csv` (living organisms at each census, with `parent`), and
`genomes.csv` (`raw_hash, func_hash, ...`). Founders and injected copies
have parent 0 and no births row, so the tree is a forest under a virtual
root. The lineage parent is the executor, including under parasitism.

| Phylometric | Computable now | Note |
|---|---|---|
| MRCA depth and its change count (Dolson 2020) | yes | already planned |
| MPD in nodes; sum pairwise distance | yes | about 950 tips, about 450,000 pairs per census |
| Ancestor count (internal nodes, unifurcations stripped) | yes | |
| Mean evolutionary distinctiveness | yes | branch lengths from birth ticks or generation counts |
| Colless-like index | yes, more code | multifurcating balance index |
| MODES change, novelty, ecology at several depths | yes | exact persistence from the tree; components = `func_hash` |
| MODES complexity | needs a knockout loop around `--classify`; a parasite needs a host next to it | Willkens 2023: single knockouts mis-handle interacting sites |

(inference) Parent choice is evo's own decision: under parasitism the
child's bytes come from `source` while the lineage parent is `executor`.
The Avida sign flips between tree units suggest computing both trees
before relying on any sign.

### Q1. Does anything change the round-1 choice?

No change to the headline. QNN over `func_hash` per census interval stays
the single number. Additions (inference):

1. Add ancestor count, sum pairwise distance and mean ED to MRCA depth
   and MPD, on individual-level trees. Moreno 2024's sweep result points
   to branch-length metrics as the stronger sweep signal.
2. The "same-physics control" of round 1 needs to be specific: same
   `--locality`, same world size, parasites on versus off. Moreno 2023
   shows space moves MPD, ancestor count and mean ED more than ecology,
   and on a spatial background ecology shows as more ancestors and
   higher mean ED, with lower MPD only when strong.
3. Measure the spatial term separately with a `--locality` or
   `--alloc-far` sweep, because evo's ring cannot be turned off.
4. Expect weak power: Avida on a grid (n = 30) detected only its
   strongest ecology. Decide the sign of each metric from evo's own
   controls, since the two Moreno versions disagree on ecology's sign
   for mean ED.

The Lenski 2003 line-of-descent analysis is untouched by this cluster.

### Q2. Is MODES worth keeping?

Keep change, novelty and ecology as a cheap secondary readout; drop
MODES complexity as a headline. (inference, from Bohm 2024 and the two
Willkens papers)

- Worth having: Bohm's result that comparing ecology at short and long
  filter depths separates stable from unstable ecology is exactly the
  question for evo's host–parasite runs (stable coexistence versus
  turnover), and evo's exact ancestry makes the filter free. Report at
  least N/5 and 2N in generations, not one depth.
- Limits the authors give: it cannot tell drift from unstable ecology
  without manual inspection; strong selection caps change and novelty at
  1; depth-0 ecology is inflated by mutation. In the large-genome-space
  design, parasites produced constant diversification that long-depth
  ecology did not register, which is evo's likely regime.
- Complexity: system-specific in Bohm (|ones − 7.5|), knockout-fragile in
  Willkens 2023, context-dependent in Willkens 2026, and it grew under
  drift in Willkens 2026's Random control.
- Willkens 2026 adds a third outside application but no method that
  changes this.

### Q3. Scale bars

| Paper | Population | Length | Replicates |
|---|---|---|---|
| Moreno et al. 2023 | 32,768 (split over 1,024 islands in the spatial regime, 32 each by division) | 262,144 generations (also 32,768 and 98,304) | 50 per treatment |
| Moreno et al. 2024 | up to 16 million agents (abstract); 10k–562.5k PEs, 32 per PE in emulator benchmarks | 1 million generations on hardware | 4 per treatment per array size |
| Singhvi et al. 2025 | 190.8 million (256 per PE) | 5 million generations; 954 trillion replication events | 1 per treatment (2 treatments) |
| Bohm, Zhang & Dolson 2024 | 500 | 200,000 generations | 10 |
| Willkens & Pollack 2023 | 50 | 50,000 generations | 40 |
| Willkens 2026 | 100 per population | 5,000 generations | 20 per condition |
| evo, E-series (`literature.md` §6.4) | about 950 organisms | 250,000 ticks | 10 seeds |

(inference) The wafer-scale papers are engineering demonstrations with
1–4 replicates; they set no bar for evo. The measurement papers that a
reviewer would hold evo to are Moreno 2023 (50 replicates) and the
MODES applications (10–40).

## Searches that found nothing

- arXiv API, title "phylogenetic inference of evolutionary dynamics at
  scale": 0 hits. Author search Moreno AND Dolson: 15 papers, none the
  2023 paper (the journal extension 2405.07245 is there). Found instead
  via the journal version's data statement (Zenodo
  [10896667](https://zenodo.org/records/10896667), OSF
  [vtxwd](https://osf.io/vtxwd/)) and the repository's tags.
- arXiv: "spatial prediction games" 0; Willkens AND "maximization of
  expected utility" 0 (author search returned only 2404.06588); Nehaniv
  AND "fossil record" 0; "where does life begin" 0; Bohm AND MODES 0;
  Rajewicz 0; Pitt AND "standoff" 0.
- Semantic Scholar by DOI: `isal_a_00830` and `isal.a.890` returned 404;
  the four garbled DOIs return the garbled title.
- OpenAlex: no title for the garbled four; search "Excavating Fogel's
  Fossil Record" returned no results; the search for the Bohm 2026 title
  returned HTTP 400.
- Crossref: no abstracts for `isal_a_00694`, `isal_a_00830`,
  `isal_a_00729` (OpenAlex had them).
- Zenodo search `"alife 2024 modes"`: 0 (found by "cliff-bohm").
- GitHub repository search for the Moreno 2023 paper under user mmore500:
  0.
- No open copy of Willkens & Pollack 2024 anywhere searched (OpenAlex
  locations list only MIT Press; Zenodo holds datasets only).

## Not reached

- Publisher PDFs of Moreno 2023 and Willkens 2026 (read from the
  authors' LaTeX sources, so the published figures were not seen).
- Moreno 2023's supplementary tables (`tab/*.tex` downloaded, numbers not
  read) and OSF data.
- Exact metric values in Bohm 2024's figures (only tick labels and
  shapes); the Evo-Sandbox code was read for settings, not run.
- Full texts of Willkens & Pollack 2024, Nehaniv 2026, Bohm 2026
  (abstracts sufficed for one-liners).
- PhyloFrame (Moreno et al., [arXiv 2605.28545](https://arxiv.org/abs/2605.28545)),
  a phylometrics library seen in the arXiv author listing, not read.

## UNVERIFIED list

- Willkens & Pollack 2024: everything (abstract only).
- Nehaniv, Derets & Do 2026: everything (abstract only).
- Bohm 2026: everything (abstract only).
- Title of `isal_a_00672`: from the conference programme only.
