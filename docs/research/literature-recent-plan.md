# Recent-work review: plan (2026-10-08)

Executed 2026-10-09 by four agents, one per cluster, in about an hour
of fetching rather than the two or three days planned. Output:
`notes/recent-1-host-parasite.md`, `recent-2-soup-emergence.md`,
`recent-3-oee-measures.md`, `recent-4-energy-accounting.md`;
`literature.md` §6 (answers to the five questions in §6.4);
`hypotheses.md` note on H13–H15; PLAN §8 Phase 4, §9, §10. Not
reached: MIT Press (HTTP 403 on every ISAL and *Artificial Life*
page), so Bohm, Zhang & Dolson 2024 and Willkens & Pollack 2023 are
abstract-only; Google Scholar cited-by was not attempted.

Purpose: before committing to a question that could carry a paper, find
what has been done since the sources in `literature.md` (which stops at
the 2024 *Computational Life* paper and the two 2026 follow-ups already
noted) and in the areas the project is now walking into: evolved
defences against parasites, the reachability of such defences, and
rule-by-rule emergence studies. Output goes into `literature.md` in its
existing format (one subsection per system or paper, a parameter table
where the paper gives numbers, a plateau line, and what the authors
thought was missing), and into `notes/` as one file per cluster with a
URL on every fact and UNVERIFIED tags kept. Nothing is cited from memory;
every claim is read from the paper or its abstract.

Two or three days of reading. Candidate questions it has to settle are
listed at the end; the review is done when each has an answer or a
documented gap.

## Clusters, in priority order

### 1. Host–parasite coevolution and evolved defence in digital systems

What is known about hosts evolving resistance, and whether anyone has
explained reachability (how many mutations away a defence was, and what
each intermediate cost).

- Avida host–parasite line after Zaman et al. 2014 (PLoS Biology,
  coevolution drives complexity): later work on parasite-driven
  complexity, resistance mechanisms, mutational neighbourhoods of
  resistance, and the role of parasite virulence. Search names: Zaman,
  Fortuna, Ofria, Lenski, Dolson; "Avida parasite" 2015–2026.
- Stringmol: the spatial-pattern coexistence paper and any follow-up on
  the self-scan defence (Hickinbotham, Stepney, Clark, Nellis). The
  question for us: did they describe the mutational path to the
  self-scan, or only its presence?
- Tierra: Ray's accounts of immunity and hyper-parasites (1991, 1992)
  re-read for the mechanism and whether a path analysis exists; any
  later reanalysis.
- Coreworld, Amoeba, Nanopond, Cosmos: already covered; only check
  for post-2020 follow-ups.
- Theory: mutational robustness and neutral-network reachability in
  digital organisms (Wilke, Lenski, Adami "survival of the flattest"
  line; neutral networks in Avida), as the frame for E009's
  four-neutral-insertions argument.

### 2. Emergence from random soups and rule-by-rule studies

For Phase 4's calibration question (which physics rule kills
emergence).

- Agüera y Arcas et al. 2024 (*Computational Life*) and everything
  citing it through 2026: Knierim 2026 and Cicala 2026 are in the review;
  find the rest. Attention to papers that vary one rule at a time
  (interaction length, mutation rate, spatial structure, instruction
  set) and report emergence rate.
- Self-replication emergence in other substrates since 2020: cellular
  automata (Lenia-style, "particle Lenia", neural CA self-replication),
  lambda-calculus and combinator soups (Fontana's AlChemy revisited),
  Brainfuck and Forth variants, Z80 and 8080 soups.
- Minimal replicator length as the predictor of emergence rate: any
  paper that measures it directly.

### 3. Open-endedness measurement, 2020–2026

For deciding what a "result" would be when a run is claimed to do
something new.

- MODES (Dolson et al. 2019) and its uses since.
- Channon 2024 (already in the review) and other activity-statistics
  updates; Bedau-Packard applied to recent systems.
- Novelty and "interestingness" measures from the open-endedness
  workshops (ALife, GECCO, NeurIPS ALOE), with a view to whether any is
  usable from our census and ancestry tables.
- Stanley, Soros, Lehman and the Sakana-style automated open-endedness
  work: note what they measure, not the LLM side.

### 4. Energy and resource accounting in digital evolution

Whether anyone has made parasitism cost the host, as E008 and E009 do.

- Avida resource models (limited resources, depletable tasks) and any
  per-instruction energy system.
- Cosmos's energy tokens (covered); Stringmol's energy per opcode
  (covered); anything after 2010 with per-op energy and ownership.
- Artificial-chemistry systems with conservation of matter and
  predation (Dittrich, Banzhaf; Hutton's Squirm3; "Chemlambda").

## Method

- Sources: Google Scholar and Semantic Scholar "cited by" on the 2024
  paper, Zaman 2014 and the Stringmol spatial paper; the ALife and ECAL
  proceedings 2020–2026 (MIT Press, open access); the *Artificial Life*
  journal tables of contents 2020–2026; arXiv cs.NE and q-bio.PE
  searches on "digital evolution", "artificial life", "self-replicator",
  "open-endedness".
- For each paper: substrate, what emerged, plateau, what was missing,
  the numbers in a table, and one line on what it means for evo. Papers
  that turn out irrelevant get one line in the notes file so they are
  not re-read.
- Verification: a fact goes into `literature.md` only after the paper
  (not a secondary source) was read; an abstract-only reading is tagged
  UNVERIFIED as the existing notes do.
- Time box: cluster 1 one day, cluster 2 one day, clusters 3 and 4 half
  a day each. A cluster that runs over is cut, not stretched.

## Questions the review must answer

1. Has anyone explained why an evolved defence was reachable, with the
   mutational path and the fitness of intermediates? If yes, E009's
   framing is a replication in a new substrate; if no, it is the gap.
2. Has anyone run a controlled comparison of parasite cost against
   defence evolution (cost on, cost off; or graded)? E008/E009 are that
   comparison.
3. For Phase 4: has anyone added physics rules one at a time to a
   random-soup emergence protocol and reported which rule kills
   emergence? If yes, which rules, and is energy among them?
4. What open-endedness measure, if any, is computable from what the
   simulator already records (census, births, deaths, ancestry,
   canonical genomes)? Pick one to report from E009 onward.
5. Which venues published the closest work, and at what scale (seeds,
   ticks, population): sets the bar for runs that would be taken
   seriously.

## Deliverables

- `literature.md`: new subsections under §2 and §3, and a new §4
  "2020–2026" summary with the answers to the five questions.
- `notes/`: one file per cluster above.
- `hypotheses.md`: a note under H12–H14 if the review changes the
  reasoning, as a new dated entry, never an edit.
- PLAN §10 (expectations) and §8 Phase 4 updated if the review changes
  what counts as beyond prior work.

---

# Round 2: ALIFE conference proceedings 2023–2026 (planned 2026-10-09)

Round 1 reached the ISAL proceedings only through arXiv preprints and
Semantic Scholar citation lists, because MIT Press returned HTTP 403 to
every fetch. On 2026-10-09 the four volumes (ALIFE 2023, 2024, 2025 and
2026, DOIs `10.1162/isal_a_00562` to `isal.a.1055`) were listed through
the Crossref API instead and every title screened. The listing, with a
triage mark per paper, is `notes/isal-proceedings-2023-2026.md`. Result:
17 of the relevant papers were already covered; 34 were not, of which
about 15 bear directly on E008–E010, Phase 4 or the choice of a measure.
The two abstract-only papers from round 1 (Willkens & Pollack 2023,
Bohm, Zhang & Dolson 2024) have since been downloaded by hand to
`docs/downloaded-papers/` (gitignored) and checked against their DOIs.

Full texts still have to be downloaded by hand from `direct.mit.edu`
(open access, but blocked to scripts). Crossref carries abstracts for
2025 and 2026; OpenAlex carried most of the 2023 and 2024 ones.

Output goes where round 1's did: one notes file per cluster below,
`literature.md` §6 extended with a dated subsection per cluster (never
an edit of what stands), `hypotheses.md` dated notes only if the
reasoning changes, PLAN §8 Phase 4 and §10 if the bar moves. The
UNVERIFIED tags on the two downloaded papers are cleared once they are
read in full.

## Cluster 5. Emergence in program soups (BFF and neighbours)

For Phase 4's calibration harness and the minimal-replicator question.

- **Dušek, Papadopoulos & Hudcová 2026**, "Replicator Discovery Is
  Faster Without Population Coupling in a Self-Modifying Program Soup"
  (`isal.a.986`). BFF. Three regimes: uniform sampling, execution
  without population coupling, full soup. Population coupling slows
  discovery by about 2x. Read first. Questions: what is the discovery
  rate per interaction in each regime, how do they define "replicator",
  what is the mechanism of discovery from a non-replicator, and does
  any of it transfer to a ring with locality.
- **Myers, Song & Bartko 2026**, "Prediction and Entropy of Evolving
  Sequences" (`isal.a.974`). Pseudo-perplexity of a fine-tuned GPT-2 on
  64-byte BFF replicators separates conserved opcode positions from
  variable ones (r = 0.99). Candidate functional-information measure
  on evo's canonical genomes; code at
  `github.com/tydymy/bff-functional-information`.
- **Perrico & Banzhaf 2026**, "Self-Modifying Linear Genetic
  Programming" (`isal.a.1044`). Self-replication in self-modifying LGP;
  separates self-modification from program-counter looping.
- **Horiguchi & Sayama 2026**, "Space-Size-Driven Transition of
  Evolutionary Dynamics in Structural Cellular Hash Chemistry"
  (`isal.a.976`), with **Sayama 2024**, "Hash Chemistry on a Cellular
  Grid" (`isal_a_00762`). A transition in dynamics at grid size L of
  about 300 to 320, with mutation rate and death probability as
  complementary controls. Precedent for soup-size sensitivity.
- One line each: Folena & Kruszewski 2024 (`isal_a_00791`, enzymes in a
  function soup); Stenzel et al. 2024 (`isal_a_00813`, self-replicating
  prompts); Kocherovsky & Banzhaf 2024 (`isal_a_00735`); Hill Roy et al.
  2026 (`isal.a.1020`, GPU populations); Usui, Suzuki & Arita 2023
  (`isal_a_00617`, no abstract found).

## Cluster 6. Hosts, symbionts and the reachability of defence

The Dolson, Vostinar, Lalejini, Ofria and Ferguson line, which is the
peer-reviewed neighbour of E008–E010. Mostly Avida-style digital
organisms and Symbulation.

- **Kelley et al. 2026**, "Endosymbiotic mutualism can constrain host
  diversity and evolved complexity" (`isal.a.1024`). Replicates
  "parasites increase host diversity and complex traits"; mutualists do
  the opposite; removing mutualists releases the host. Read for the
  replication's numbers (seeds, updates, population), as the scale bar.
- **Johnson et al. 2026**, "Saved by the Symbiont" (`isal.a.1025`).
  Hosts cycle between parasite-resistant and parasite-vulnerable states.
  Code on Zenodo (10.5281/zenodo.19477499). Read for how resistance is
  encoded and whether its loss is tracked, as the nearest thing to
  E009's defence-loss rate.
- **Johnson, Croft, Vostinar, Lalejini & Dolson 2025**, "Partner Choice
  Can Enable Parasite Exclusion" (`isal.a.885`). Tag matching as an
  evolvable defence; parameter ranges where parasites go extinct. The
  question for E009: is the path to the defence described, or only its
  presence and the parameter region.
- **Johnson, Dirkswager & Vostinar 2023**, ectosymbiosis hastens
  endosymbiosis (`isal_a_00661`). Symbulation; background.
- **Ferguson & Ofria 2023**, "Potentiating Mutations Facilitate the
  Evolution of Associative Learning in Digital Organisms"
  (`isal_a_00684`); **Ferguson, Ofria & Bohm 2024**, replay experiments
  and adaptive momentum (`isal_a_00801`); **Ragusa & Bohm 2023**, the
  free-for-all effect (`isal_a_00660`); **Sanson & Ferguson 2025**,
  long-term evolvability baseline (`isal.a.895`); **Escondo & Ferguson
  2026**, sampling in replay experiments (`isal.a.1014`). Together these
  are the current method for asking "was this adaptation reachable, and
  what made it reachable", which is E009's question. Adaptive momentum
  (deleterious steps tolerated during a sweep) is the mechanism that
  would let a defence with no paying intermediate appear; it belongs
  next to Lenski 2003 and Standish 2004 in `literature.md` §6.4 Q1.
- **Gordon, Ferguson, Dolson & Lalejini 2025**, environmental
  connectivity and long-term outcomes in Avida (`isal.a.863`); **Shea et
  al. 2024**, connectivity and the emergence of adaptive processes
  (`isal_a_00749`). Both bear on evo's ring with locality as a control.
- One line each: Leither et al. 2023 (`isal_a_00686`) and Foreback et
  al. 2023 (`isal_a_00692`) on egalitarian transitions; Chaturvedi et
  al. 2026 (`isal.a.980`); Bielawski et al. 2025 (`isal.a.836`); Gaylinn
  et al. 2025 (`isal.a.893`).

## Cluster 7. Measures and phylogeny methods

- **Willkens & Pollack 2023** (downloaded) and **Bohm, Zhang & Dolson
  2024** (downloaded): full read, clear the UNVERIFIED tags in
  `literature.md` §6.3.3 and `notes/recent-3-oee-measures.md` §1. From
  Bohm 2024 take the Evo-Sandbox parasite and fit-when-rare parameters
  and which MODES metric moved under parasites.
- **Willkens 2026**, "MODES Analysis of Spatial Prediction Games"
  (`isal.a.994`), with **Willkens & Pollack 2024** (`isal_a_00729`) as
  background. Only if MODES stays the chosen measure.
- **Moreno, Dolson & Rodriguez-Papa 2023** (`isal_a_00694`), **Moreno,
  Yang, Dolson & Zaman 2024** (`isal_a_00830`) and **Singhvi et al.
  2025** (`isal.a.890`): phylogenetic signatures of selection, space and
  ecology, and the wafer-scale pipeline (954 trillion replications).
  Read 2023 for which phylometrics separate spatial structure from
  ecology, since evo's ring confounds them; the other two set the scale
  bar and are otherwise one line each.
- One line each: Nehaniv et al. 2026 (`isal.a.990`); Bohm 2026
  (`isal.a.937`, framing).

## Method and time box

- Download by hand: `https://doi.org/<DOI>` resolves to the MIT Press
  page; the PDF link is on it. Save to `docs/downloaded-papers/` named
  `<doi-suffix>_<first-author>.pdf`, as the two existing files are.
  About 15 full reads and 20 one-liners; one-liners can be done from
  the abstracts already in the listing file.
- Same rules as round 1: a fact enters `literature.md` only from the
  paper itself; abstract-only facts are tagged UNVERIFIED; nothing from
  memory; searches that find nothing are recorded.
- Time box: cluster 5 half a day, cluster 6 one day, cluster 7 half a
  day. Order: Dušek 2026 first, then Kelley 2026 and Johnson 2025, then
  the two downloaded papers.

## Questions round 2 must answer

1. Does Dušek 2026 change Phase 4's protocol? If discovery is an
   execution-statistics effect rather than a population effect, the
   calibration harness should report discovery rate with and without
   coupling, not only emergence yes or no.
2. Does any paper in cluster 6 describe the mutational path to a
   defence, with intermediates and their cost? Round 1 answered no for
   2020–2026 outside ISAL; this closes the gap for ISAL. Johnson 2025
   and Johnson 2026 are the candidates.
3. Does adaptive momentum (Ferguson, Ofria & Bohm 2024) give E009's
   four-neutral-insertions argument a mechanism, or a counterargument?
4. Is pseudo-perplexity (Myers 2026) computable from evo's census and
   canonical genomes, and does it add anything over the knockout
   complexity already planned?
5. Scale bar: seeds, updates and population in Kelley 2026 and Johnson
   2026, to set what an E-series result needs to be taken seriously by
   that group.
