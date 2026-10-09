# Recent-work review: plan (2026-10-08)

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
