# Recent work, cluster 1: host-parasite coevolution and evolved defence in digital systems

Compiled 2026-10-08 (finished 2026-10-09). Purpose: cluster 1 of
`docs/research/literature-recent-plan.md`. It asks whether anyone has explained
why an evolved defence against parasites was *reachable* (the mutational path and
the fitness of the intermediates), and whether anyone has run a controlled
comparison of parasite cost against defence evolution. Context for evo: E008-E010
charged the host for intruder execution (full charge, split, transfer) and no
defence evolved; E009 argued that the five-byte self-scan prefix needs four
neutral insertions before the fifth pays, so it is out of reach.

This file does not repeat `notes/avida-stringmol.md` (Zaman 2011 and 2014,
Stringmol 2021 mechanisms) or `notes/tierra-coreworld-amoeba.md`; it extends them
where a re-reading changed something.

How this was checked:

- PDFs downloaded and converted with `pdftotext`, then read: Hickinbotham, Stepney
  & Hogeweg 2021 (RSOS 210441, White Rose eprint); Ray 1992 "Evolution, Ecology
  and Optimization of Digital Organisms" (SFI working paper, Georgia Tech mirror);
  Lenski, Ofria, Pennock & Adami 2003 (Nature, MSU mirror); Zaman, Devangam & Ofria
  2011 (GECCO, Ofria's site); Standish 2004 (arXiv nlin/0404012); Seoane & Sole
  2023 (arXiv 1910.14339v4); Spirov 2023 (arXiv 2312.17540, body in Russian, only
  the English abstract and reference list read).
- Read as journal HTML: Gupta et al. 2022 (PMC9259030), Fortuna et al. 2017 (PLoS
  Comp Biol), Acosta & Zaman 2022 (Frontiers), Vostinar et al. 2021 (Frontiers),
  Stepney 2025 (PMC12489504).
- Abstract only (Europe PMC, arXiv or bioRxiv abstract page): Wilke et al. 2001,
  Covert et al. 2013, Draghi et al. 2024, Jha et al. 2026, Stepney & Hickinbotham
  2021 "What is a Parasite?". These are tagged **UNVERIFIED** where a claim goes
  beyond the abstract.
- Not reachable (HTTP 403 from MIT Press, ACM, Nature, PNAS; 404 at York Pure):
  Zaman 2018 ALIFE, Hickinbotham 2023 GECCO Nanopond, Vostinar et al. 2022 ISAL
  review, Wilke 2001 full text, Covert 2013 full text. Listed under "Not reached"
  at the end.
- Searches that found nothing are recorded in section 9.

Terms:

- *Path analysis*: a published list of the mutations between an ancestor and an
  evolved trait, each with the fitness (or viability) of the intermediate carrying
  it.
- *Cost arm*: an experimental treatment that varies how much the parasite costs
  the host, holding everything else fixed.
- *Reachability*: whether a trait that would pay once complete can be assembled by
  single mutations each of which is at least neutral.

---

## 1. Stringmol spatial parasitism (Hickinbotham, Stepney & Hogeweg 2021), re-read for the path

Source: *R. Soc. Open Sci.* 8:210441,
https://eprints.whiterose.ac.uk/id/eprint/176868/1/rsos.210441.pdf. Mechanisms of
the three defences are in `avida-stringmol.md` section 2.10 and are not repeated.

**Is there a path to the self-scan?** Yes, a qualitative one, and the intermediates
are not fitness-graded. Section 2.6 ("Macromutations") says: "A series of single-
point mutations appears to be a highly improbably route to the observed
rearrangements of the program instructions that yield the innovative behaviours.
By studying the sequence of products from long lineages of replicating reactions,
we have found that these changes are consequences of single point mutations
combined with subsequent changes in binding and cleaving of strings at points
different from the original design." And: "Some single point mutations change the
function of the program such that a cascade of mutant species are subsequently
produced, none of which is self-sustaining, but which eventually result in new
replicators that are able to increase in number. As an example of these
mutational cascades, figure 6 illustrates stages in the transition to the first
self-scanning replicator."

The six stages of figure 6, as the text gives them
(https://eprints.whiterose.ac.uk/id/eprint/176868/1/rsos.210441.pdf, section 2.6):

| Stage | Event | Status of the product |
|---|---|---|
| 1 | Seed replicator: two complementary bind sites, copy loop, cleave/end region | viable (hand-designed) |
| 2 | A mutation in the write-pointer position copies the trailing three regions onto another replicator; the first bind site is lost, copy and terminate regions are repeated | "persists for some time, and fixes by copying itself onto whatever it is bound to" |
| 3 | A mutation in the flow-pointer position for cleave truncates the string | not self-sustaining (by the paragraph above) |
| 4 | A second repositioned cleave truncates it again | not self-sustaining |
| 5 | The truncated string is copied onto the start of a longer string that carries the copy and cleave regions at its end | not self-sustaining |
| 6 | A further mispositioned cleave truncates that; "the trailing portion of the string forms a viable replicator, and the copy loop additionally functions as the bind site" | viable: the first self-scanning replicator |

So the path is three to five reaction products long, most of them non-replicating
strings that exist only because a working replicator keeps copying them. No
fitness is given for any stage, no counts, no time between stages. The paper's
own framing is that the route is *not* a walk of individually neutral point
mutations; it is a cascade of mis-positioned copy and cleave operations, possible
because in Stringmol a point mutation can move where `$` (search) or `%` (cleave)
lands and thereby splice or truncate whole regions (section 2.6, and
`avida-stringmol.md` 2.10 "Macro-mutations").

**Fitness of the finished self-scan.** Section 2.4: "The main effect is to slow
down the entire replication process. The selective advantage of this feature is
apparent only in the presence of parasites, since their rate of reproduction is
also slowed." "The self-scan feature adds a fixed cost to replication which
parasites cannot avoid." Side effect: "the point mutation rate is approximately
doubled for replicating reactions that have this feature." The only number: at
t6 of run 2 the ZAA replicator does both self-scan and copy in one loop "in 157
timesteps" (section 2.4). No replication time without self-scan is given for a
matched string, so the cost is not quantified. After the toggle checks were
added, "only 323 of a total of 5671 reactions at t5 are parasitic".

**Cost arm.** None. All runs use the same chemistry; the paper varies only grid
shape (100x125 vs 250x50) and seed layout
(https://eprints.whiterose.ac.uk/id/eprint/176868/1/rsos.210441.pdf, section 2.1;
`avida-stringmol.md` 2.10). Energy is effectively unlimited in these runs
(`literature.md` 2.7), so "cost" to a host here is time, not energy.

**Why the defence was reachable in Stringmol and not in evo (inference).** Two
features of the substrate do the work. (a) A parasite in Stringmol is a *bound
partner* that the replicator's own program copies, so a change in the
replicator's program (scan self first, toggle to partner and back) acts on every
interaction; in evo an intruder is an executor that falls through into the
host's bytes, and the host's program is not running when it happens. (b) The
variation operator is not a point-mutation walk: cleave and search mis-positioning
produce region-level rearrangements in one step, so a five-opcode prefix is not
five events. E009's "four neutral insertions" count assumes single-byte
insertions as the only route; the Stringmol result does not contradict it, it
just does not apply.

**Scale** (for plan question 5): 20 runs, 12,500 cells, 2 x 10^6 timesteps, one
seed replicator of 65 symbols; 8 runs survived
(https://eprints.whiterose.ac.uk/id/eprint/176868/1/rsos.210441.pdf, section 2.1
and 2.2). Venue: Royal Society Open Science.

**For evo:** the closest published "evolved defence" has a described but not
graded path, and it ran under a variation operator that makes multi-opcode jumps
cheap. A path analysis with intermediate fitness for a defence does not exist in
the Stringmol literature.

## 2. Stepney & Hickinbotham 2021, "What is a Parasite?" (ALIFE 2021)

Source: abstract on Stepney's page,
https://www-users.york.ac.uk/~ss44/bib/ss/nonstd/alife2021-parasite.htm; the paper
is at https://direct.mit.edu/isal/proceedings/isal2021/33/80/102870 (not fetched,
403). Abstract: "We provide definitions for several emergent properties, such as
parasitism and hypercycles, observed to emerge in an RNA world configuration of
the Stringmol automata chemistry, and show how these can simultaneously be
mathematically simple, capture the complexity of the processes, and be readily
implementable." **UNVERIFIED** beyond the abstract. It is a definitions paper
(what counts as a parasitic reaction in a reaction network), not a path or cost
study. Relevant to evo only as a precedent for defining "parasite" from the
reaction record, which E005's dependent-genome test already does by a different
route.

## 3. Stringmol after 2021: nothing new on defences

Searches "stringmol 2022..2025 parasite self-scan", "Hickinbotham Stepney
stringmol ALIFE 2023 2024 2025" returned only the 2021 RSOS paper, the 2021 ALIFE
definitions paper, the 2024 *Artificial Life* measurement paper (already in
`literature.md` 2.7 and `avida-stringmol.md` 2.11), and Hickinbotham's 2024
ALIFE poster on truss morphogen grammars (unrelated;
https://2024.alife.org/detailed_program.html, seen in a search snippet only).
Nothing found on the self-scan path after 2021.

## 4. Tierra: Ray's immunity and hyper-parasites, re-read

Source: Ray, "Evolution, Ecology and Optimization of Digital Organisms", SFI
working paper 92-08-042,
https://faculty.cc.gatech.edu/~turk/bio_sim/articles/tierra_thomas_ray.pdf
(read in full after `pdftotext`). This settles the UNVERIFIED tag on the
immunity mechanism in `literature.md` 2.2: **Ray gives no mechanism**, only the
assay.

- **Parasite 0045aaa.** "A creature born with a mutation in the low order bit of
  instruction 42 would calculate its size as 45. It would allocate a daughter
  cell of size 45 and copy only instructions 0 through 44 into the daughter
  cell. The daughter cell then, would not include the copy procedure." It
  reproduces by matching the template of a neighbouring 0080aaa's copy procedure
  "within the search limit (generally set at 200-400 instructions)". "The host is
  not adversely affected by this informational parasitism, except through
  competition with the parasite, which is a superior competitor" (Fig. 1
  caption). So Tierra's basic parasite costs the host nothing directly, as evo's
  `pad` under the executor rule.
- **Immunity (0079aab).** The whole account: "At least some of the size 79
  genotypes demonstrate some measure of resistance to parasites. If genotype
  45aaa is introduced into a soup, flanked on each side with one individual of
  genotype 0079aab, 0045aaa will initially reproduce somewhat, but will be
  quickly eliminated from the soup. When the same experiment is conducted with
  0045aaa and the ancestor, they enter a stable cycle in which both genotypes
  coexist indefinitely. Freely evolving systems have been observed to become
  dominated by size 79 genotypes for long periods, during which parasitic
  genotypes repeatedly appear, but fail to invade." No instruction-level
  mechanism, no count of mutations from the ancestor, no intermediates.
- **Circumvention (0051aao).** "a direct, one step, descendant of 0045aaa in
  which instruction 39 is replaced by an insertion of seven instructions of
  unknown origin"; it enters a stable cycle with 0079aab. "The fourteen
  genotypes 0051aaa through 0051aan were also tested with 0079aab, and none were
  able to invade." This is the one place Ray reports a mutational neighbourhood
  for a parasite-related trait: 15 size-51 genotypes assayed, 1 circumvents.
- **Hyper-parasite (0080gai).** "differs by 19 instructions from the ancestor".
  "Their ability to subvert the energy metabolism of parasites is based on two
  changes. The copy procedure does not return, but jumps back directly to the
  proper address of the reproduction loop. In this way it effectively seizes the
  instruction pointer from the parasite. However it is another change which
  delivers the coup de grace: after each reproduction, the hyper-parasite
  re-examines itself, resetting the bx register with its location and the cx
  register with its size. After the instruction pointer of the parasite passes
  through this code, the CPU of the parasite contains the location and size of
  the hyper-parasite and the parasite thereafter replicates the hyper-parasite
  genome." Two functional changes among 19 differences; which of the other 17
  were neutral is not said, and no intermediate was assayed.
- **Social hyper-parasites (0061acg) and cheaters (0027aab)** as in
  `tierra-coreworld-amoeba.md`; Ray's reading of the selection pressure for
  sociality is size reduction ("The social species are 24% smaller than the
  ancestor"), with templates shrunk from four to three instructions.
- **Path analysis:** none for any of these. Ray assays finished genotypes
  pairwise in a soup and reports who wins.

**Later reanalysis of Tierra.** The only one found that bears on reachability is
Standish 2004 (section 7 below). Searches for "Tierra immunity mechanism
reanalysis" returned nothing else.

**For evo:** Tierra's hyper-parasite is the Tierra equivalent of a defence that
*ejects by register state* (it resets bx and cx so the parasite's CPU points at
the hyper-parasite). It is the same trick as E009's self-scan prefix and E010's
eject (set the intruder's registers so its next jump goes where the host wants).
Ray never explained how 0080gai's 19 changes accumulated, so this does not
answer plan question 1.

## 5. Avida host-parasite line after Zaman 2014

### 5.1 Zaman, Devangam & Ofria 2011 (GECCO), re-read for the cost arm

Source: https://cse.msu.edu/~ofria/pubs/2011ZamanEtAl.pdf (read after
`pdftotext`). Mechanism in `avida-stringmol.md` 1.10.

- Virulence is the only cost knob: "The probability of a parasite steeling a
  CPU cycle from its host is configurable, and we will refer to it as
  'virulence'. When virulence is set to one, parasites steal all CPU cycles from
  their hosts, killing them and using them for energy like predators ... When
  virulence is set to 0.5, parasites and hosts split CPU cycles evenly and there
  is a stable equilibrium of host and parasite frequencies." Virulence 1.0 gives
  "classic Lotka-Volterra dynamics (Figure 1)". The experiments use 0.80.
- Resistance in Avida is a task switch with a built-in cost: "In order to become
  resistant, hosts must loose their ancestral task (so that the parasites cannot
  infect them) while also evolving a novel task." The discussion names the
  trade-off but does not measure it: "hosts may have trade-offs between
  resistance and competitive ability. When parasites are common, the cost of
  being resistant may be worth the ..." (section 4; the sentence continues off
  the extracted column).
- Scale: 50 replicates with parasites and 50 without, 200,000 updates, 14,400
  cells, well mixed, 320-instruction host and 80-instruction parasite ancestors,
  parasites injected into 400 cells at update 3,000.
- **Cost arm against defence evolution: no.** Virulence 1.0 and 0.5 are shown
  only as ecological time series; the diversity measurements are all at 0.8.

### 5.2 Zaman et al. 2014 (PLoS Biology)

Already in `avida-stringmol.md` 1.10 and `literature.md` 2.3. Nothing on path
or cost beyond what is there. 50 replicates, 500,000 updates, virulence 0.8.

### 5.3 Fortuna, Zaman, Ofria & Wagner 2017 (PLoS Comp Biol): genotype networks in Avida

Source: https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005414
(read as HTML). No parasites. It is the Avida neutral-network paper the plan
asks for.

- Space: 10^141 genotypes, 512 phenotypes (logic-function sets). About 6.6 x
  10^-7 of random genotypes are viable; 1.5 x 10^9 random genotypes were screened
  to find 1,000 viable ones, then 1,000 populations were evolved for 10^6 updates
  each to sample 1,000 genotypes per phenotype.
- Findings as the page states them: "The higher the complexity of a phenotype,
  the lower is its robustness" (Spearman rho = -0.689); for single-trait
  phenotypes "at least one pair of genotypes of every phenotype is connected"
  through phenotype-preserving mutations, and "the average minimum distance
  between genotype pairs increases with trait complexity"; "The greater the
  complexity of phenotype i is, the greater is the probability of finding a
  genotype with a novel phenotype" by a single mutation (rho = 0.633). Conclusion
  on reachability: complex phenotypes are more evolvable per genotype but occupy
  smaller regions of sequence space, so they are smaller targets.
- Method detail: 1,000 double-mutant random walks per phenotype; connectivity
  tested on 100 genotype pairs per phenotype.

**For evo:** this is the framework for a reachability claim (sample the neutral
network of the current host, count the one-mutation neighbours that carry each
step of the defence), and it was never applied to a defence. E009's count was
made by hand from the ISA; the Fortuna method would make it a measurement.

### 5.4 Vostinar, Skocelas, Lalejini & Zaman 2021 (Frontiers Ecol Evol), review

Source: https://www.frontiersin.org/journals/ecology-and-evolution/articles/10.3389/fevo.2021.739047/full
(read as HTML). "Symbiosis in Digital Evolution: Past, Present, and Future."
Avida parasites are "obligate endosymbionts that steal a user-configured amount
of resources (in the form of CPU cycles) from their hosts"; "The injection is
only successful, however, if the parasite performed one of the same tasks as the
would-be host." Post-2014 Avida parasite work it lists: Fortuna et al. 2017
("non-adaptive mutations play a significant role in the host phenotypic
diversity"), Zaman 2018 (diversity "unbounded trajectory" with larger carrying
capacity and more behaviours). On resistance paths it says only that
function-switching mutations were "more common in hosts that evolved with
parasites". No cost of resistance is quantified in the review.

### 5.5 Zaman 2018, "Investigating Open-Ended Coevolution in Digital Organisms" (ALIFE 2018)

https://direct.mit.edu/isal/proceedings/alife2018/30/258/99616 (403; 2 pages,
doi 10.1162/isal_a_00052). Known only through the Vostinar 2021 review
(section 5.4): carrying capacity and the number of possible resource-uptake
behaviours were raised and host and parasite diversity rose with them.
**UNVERIFIED.** Not a path or cost study.

### 5.6 Acosta & Zaman 2022 (Frontiers Ecol Evol): ecological opportunity and necessity

Source: https://www.frontiersin.org/journals/ecology-and-evolution/articles/10.3389/fevo.2021.750772/full
(read as HTML). Avida hosts and parasites with 1, 4, 10 or 20 resources; 22,500
cells; 10 replicates per treatment; 300,000 updates; parasites "steal 80% of
the CPU cycles allocated to their hosts"; host mutation 0.25 per genome (90%
point), parasite 0.5. Result: "both ecological opportunity and necessity drive
similar levels of diversity" in some treatments, but "the phenotypes that hosts
uncover while coevolving with parasites are dramatically more complex than
hosts evolving alone"; coevolution raised host diversity at low abiotic
complexity and lowered it at the highest. No resistance cost measured, no path
analysis, virulence fixed.

### 5.7 Searches that found nothing

"Avida parasite virulence evolution 2016-2019", "Avida parasites 2023 2024 2025
coevolution virulence Zaman", "Avida parasite neutral network resistance
mutational neighborhood 2015-2026": no Avida paper after 2014 that varies
virulence as a treatment against a resistance outcome, and none that traces a
resistance mutation path. The 2024 bioRxiv Draghi et al. paper (section 7.4)
came up in the last search and is theory, not Avida.

## 6. Other recent host-parasite models

### 6.1 Seoane & Sole 2023, "How Turing parasites expand the computational landscape of digital life" (Phys. Rev. E 108:044407)

Source: arXiv 1910.14339v4, https://arxiv.org/abs/1910.14339 (read after
`pdftotext`). Not a program substrate: hosts are "bit-guessers" that predict an
environment bit string; a guesser's complexity is its size n, "which also
imposes a replication cost". Cost is explicit: "Bit-guessers pay a cost c for
each bit that they attempt to predict, and they rip off a reward r for each
correct prediction", net reward (p - c/r) r n, with c/r "measuring how meager an
environment is". A parasite "does not die nor replicate. It just sucks off
reward according to equation 4 whenever its host is evaluated. Even the simplest
(n' = 1) parasite ... suffices to achieve a remarkable complexity boost. Simpler
hosts are more predictable, hence parasites extract more reward--favoring
complex hosts. In return, the point at which the ecosystem collapses happens for
lower [c/r]." N = 1000 spots, 200 generations in the ecosystem figures.

**For evo:** this is the one model found in which the host's defence (more
complexity) has a per-unit cost that is swept as a parameter, and the result is
a phase diagram (monotonic, punctuated, collapse) rather than a reachability
claim: the host's "defence" is a one-parameter dial (n), so there is no path to
analyse. It supports E010's structural conclusion from the other side: a
defence is selected only where the parasite's take is a large share of the
host's budget, and raising the cost dial moves the system to collapse before it
moves it to defence.

### 6.2 Jha, Cicala, Aguera y Arcas, Richards, Jaques, Kleiman-Weiner & Niklasson 2026, "Tapes Together Strong" (arXiv 2609.10817)

Source: abstract page https://arxiv.org/abs/2609.10817, submitted 2026-09-09.
Abstract: Z80 random-program soup where "social interactions, replication
mechanisms, and their associated computational costs are endogenous"; "When
resources are scarce ... parasitic stealing destroys shared energy, slows
execution, and can prevent reliable replication. Empirically, evolved programs
suppress stealing across several Z80 environments, while spatial assortment
further supports structural complexity". **UNVERIFIED** beyond the abstract.
This is the closest 2026 item to E010's transfer rule (stealing moves energy
between programs; execution is tied to energy) and it reports evolved
suppression of stealing. Whether "suppress" means a host-side defence or a
population-level loss of stealers is not in the abstract; the full text is the
first thing cluster 2 or a follow-up should read.

### 6.3 Spirov 2023, "Co-evolution of replicators and their parasites" (arXiv 2312.17540)

https://arxiv.org/abs/2312.17540. 14-page review, body in Russian. Abstract:
parasites "arise as soon as the first replicators appear", compartmentalisation
avoids elimination, "The co-evolutionary arms race between defense systems and
counter-defense mechanisms among parasites and hosts can progress for a
considerable duration". The reference list covers Tierra, Avida (Zaman 2011,
2014), Stringmol and Seoane & Sole. No new model, no numbers. One line: a
pointer list, nothing to cite.

### 6.4 Gupta et al. 2022 (eLife 11:e76162), biological, one paragraph

Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC9259030/ (read as HTML). Phage
lambda on E. coli, not a digital system. It is the one paper found that
measures the fitness of intermediates on a path to an innovation under
coevolution: 580 lambda genotypes assayed on the ancestral host and 131 on the
resistant (malT-) host; 21 of 45 possible mutation x mutation x host
interaction terms significant (12.62% of fitness variance); the first OmpF-path
mutation is favoured on the ancestral host and later ones on the resistant
host; Wright-Fisher simulations (960 generations, about 6.3 x 10^9 particles)
show 7 of 9 "shifting landscape" treatments raising the frequency of OmpF+
evolution over a static landscape. The authors' phrase: "fluctuating
landscapes, also known as fitness seascapes, can promote evolutionary
innovations." **For evo:** this is the template for a path analysis with
intermediate fitness (assay every intermediate genotype against both partner
types), and it is for the parasite's innovation, not the host's defence.

## 7. Theory: neutral networks, flatness, deleterious stepping stones

### 7.1 Lenski, Ofria, Pennock & Adami 2003 (Nature 423:139)

Source: https://directory.natsci.msu.edu/media/Directory/Profiles/2003,%20Natu20260121115450.pdf
(read after `pdftotext`; also https://www.nature.com/articles/nature01568).
This is the canonical digital path analysis with intermediate fitness; it is for
a logic task, not a defence.

- Case-study line of descent: "The EQU function first appeared at step 111
  (update 27,450). There were 103 single mutations, six double mutations, and
  two triple mutations among these steps. Forty-five of the steps increased
  overall fitness, 48 were neutral and 18 were deleterious relative to the
  immediate parent." "Fifteen of the 18 deleterious mutations reduced fitness by
  <3% ... However, two mutations reduced fitness by >50%." One of those, "a point
  mutation, at depth 110, that knocked out NAND", was the step immediately
  before EQU: "Only two individuals had this maladapted genotype, yet their
  descendants emerged as eventual winners." Reverting it in the first EQU
  genotype "eliminated the EQU function. Therefore, a mutation that was highly
  deleterious when it appeared was highly beneficial in combination with a
  subsequent mutation."
- Across populations: "The case-study population was one of 50 that evolved
  under identical conditions, 23 of which acquired EQU." "Five of the 23
  one-step-prior mutations were deleterious in the backgrounds in which they
  occurred ... When these five were reverted in the pivotal genotypes, the EQU
  function was eliminated in three cases." "Twenty of the 23 pivotal mutations
  would have been deleterious if EQU had not been rewarded." In 36 environments
  that withheld reward for one or two simpler functions, "124 of 360 (34%)"
  evolved EQU; with only EQU rewarded, none of 50 did (the text says "the
  complex feature never evolved when simpler functions were not rewarded").
- Functional genomics: the first EQU genome had 60 instructions; "eliminating
  any of 35 of them destroyed that function"; across the 23 pivotal genotypes
  the number required for EQU "ranged from 17" upward.

| Quantity | Value |
|---|---|
| Population | 3,600 cells, lattice, birth replaces a neighbour |
| Ancestor | 50 instructions, 15 functional, 35 `nop-C` |
| Mutation | 0.0025 per instruction copied; insertion and deletion 0.05 per genome each; 0.225 per genome |
| Run | 100,000 updates (30 instructions per organism per update); 15,873 ancestral generations |
| Replicates | 50 per environment; 36 withheld-reward environments x 10 = 360; 50 EQU-only |

**For evo:** the method (walk the line of descent, classify every step as
beneficial, neutral or deleterious against its parent, revert the one-step-prior
mutation in the pivotal genotype) is exactly what a reachability claim for a
defence would need, and E009 could run it on any seed-planted defence lineage
from the ancestry table. The result that matters for the "four neutral
insertions" argument: in Avida the path to a 17-35-instruction feature ran
through 48 neutral and 18 deleterious steps in 111, and the feature was still
reached in 23 of 50 populations in 100,000 updates, because intermediate
functions paid.

### 7.2 Wilke, Wang, Ofria, Lenski & Adami 2001 (Nature 412:331), survival of the flattest

Source: Europe PMC abstract, PMID 11460163
(https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/35085569&format=json&resultType=core);
full text not reached. Abstract numbers: "Forty pairs of populations were
derived from 40 different ancestors ... one of each pair experienced a 4-fold
higher mutation rate. In 12 cases, the dominant genotype that evolved at the
lower mutation rate achieved a replication rate >1.5-fold faster than its
counterpart ... In each case, as mutation rate was increased, the outcome of
competition switched to favour the genotype with the lower replication rate."
**UNVERIFIED** beyond the abstract. **For evo:** this is the frame in which
neutral insertions are not free: at evo's mutation rate a longer prefix is a
larger target, so each "neutral" insertion in the E009 path lowers the host's
flatness even if it leaves the fitness peak where it was. E009's invasion tests
(self-scan lost at nearly the rate of a length-matched inert prefix) are
consistent with that reading.

### 7.3 Covert, Lenski, Wilke & Ofria 2013 (PNAS 110:E3171), deleterious stepping stones

Source: Europe PMC abstract, PMID 23918358, PMCID PMC3752215
(https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1073/pnas.1313424110&format=json&resultType=core);
PNAS page returned 403. Abstract: "we used digital organisms to compare the
extent of adaptive evolution in populations when deleterious mutations were
disallowed with control populations in which such mutations were allowed.
Significantly higher fitness levels were achieved over the long term in the
control populations because some of the deleterious mutations served as
stepping stones across otherwise impassable fitness valleys ... Populations
evolving without neutral mutations were able to leverage deleterious and
compensatory mutation pairs to overcome, at least partially, the absence of
neutral mutations. Substantially raising or lowering the mutation rate reduced
or eliminated the long-term benefit of deleterious mutations". **UNVERIFIED**
beyond the abstract. **For evo:** the experimental design (disallow a class of
mutation, measure what is no longer reached) is a direct test of a reachability
argument; evo could disallow insertions, or disallow neutral insertions, and
see whether a seed-planted defence's assembly rate changes.

### 7.4 Draghi, Ogbunugafor, Zaman & Parsons 2024 (bioRxiv 2024.07.09.602773), relaxed selection and valley crossing

Source: https://www.biorxiv.org/content/10.1101/2024.07.09.602773v1 (abstract).
"relaxed selection is generally favorable for valley-crossing when adaptive
pathways require more than a single deleterious step. We also demonstrate that
spatial heterogeneity in selection pressures could, by relaxing selection,
allow populations to cross valleys much more rapidly than expected."
Population-genetic simulation and analysis, not a digital-organism substrate.
**UNVERIFIED** beyond the abstract. **For evo:** the E009 path is a multi-step
neutral-to-slightly-deleterious walk; this says patches where selection on the
host is weaker (evo's 128 patches differ in density) are where such a walk is
most likely to complete, which argues for reporting defence-prefix frequency
per patch, not per world.

### 7.5 Standish 2004, "Tierra's missing neutrality: case solved" (arXiv nlin/0404012)

Source: https://arxiv.org/abs/nlin/0404012 (read after `pdftotext`). Three
Tierra runs, one per mutation mode (cosmic ray, copy error, flaw), 69,139,
87,003 and 198,982 genotypes "generated over a time period of about 1000
million executed instructions"; 83, 86 and 158 unique phenotypes by pairwise
tournament. "In each data set, around 7% of these genotypes were created by a
mutation at a single site and were neutrally equivalent to its parent." The
measured neutrality excess (neutral links followed over neutral links available
in the one-hop neighbourhood of 32 x length) "is substantially less than 1, so
something in Tierran evolution is favouring non-neutral evolution." Explanation
(section "Competition Effects"): a neutral variant invading a population at
carrying capacity has growth rate about zero, so it fails to establish; a toy
RNA-folding host-parasite model with N = 100 reproduces a host neutrality
excess well below 1 "for the parasites over a broad range of model parameters".
Abstract: "It turns out that competition for resources between host and
parasite inhibits neutral evolution."

**For evo:** this is the one Tierra reanalysis that bears on E009's argument,
and it cuts against the path: in a soup at carrying capacity with parasites
present, neutral steps are *under*-represented in the lineages that survive,
so "four neutral insertions" are harder to accumulate than a neutral-network
count suggests. It also offers a measurement evo can copy from the ancestry
table: for each surviving lineage, the fraction of parent-child steps that are
neutral by the harness, against the fraction of neutral one-byte neighbours of
the parent.

## 8. Coreworld, Amoeba, Nanopond, Cosmos after 2020

- **Nanopond.** Hickinbotham 2023, "Drivers of Replicator Organisation in the
  Nanopond Artificial Chemistry", GECCO '23 Companion pp. 147-150,
  https://dl.acm.org/doi/10.1145/3583133.3590572 (403; ResearchGate 403; York
  Pure 404). From the search snippet: Nanopond "until now had no publications
  available to document its features", and "several common self-replicating
  attractor states in the emergent patterns exhibited by Nanopond are related to
  the distribution of energy around the system". **UNVERIFIED.** Four pages;
  nothing in the snippet on parasites or defence.
- **Amoeba, Coreworld, Cosmos.** Searches "Amoeba Pargellis / Coreworld / Cosmos
  Taylor 2021-2025" returned only the pre-2020 papers already in
  `literature.md`, plus an arXiv 2603.08463 "Evolving Symbiosis, from
  Barricelli's Legacy to Collective Intelligence" (search snippet only, not
  fetched; title suggests a Barricelli-style symbiogenesis model, not a
  Coreworld follow-up) and arXiv 2601.03335 "Digital Red Queen: Adversarial
  Program Evolution in Core War with LLMs" (snippet only; Core War with LLM
  mutation, not Coreworld). Nothing found.
- **Stepney 2025 overview**, "Towards origins of virtual artificial life",
  *Phil Trans R Soc B* 380:20240298, https://pmc.ncbi.nlm.nih.gov/articles/PMC12489504/
  (read as HTML): names Tierra, Avida, Aevol, Nanopond, Stringmol but says
  nothing on parasites or defences, and on energy only that systems implement
  "a simple energy model that imposes artificial constraints with little or no
  feedback, and no consideration of entropy". One line: not relevant to this
  cluster.

## 9. Searches recorded as "nothing found"

- "Avida parasite virulence evolution resistance cost 2016-2019" and "Avida
  parasites 2023-2025 coevolution virulence": no Avida study varying virulence
  against a resistance outcome after 2011.
- "digital organisms parasite neutral network resistance mutational
  neighborhood 2015-2026": nothing on parasite resistance; only the Fortuna 2017
  map (no parasites) and the 2023-2024 evolvability papers (environment change,
  not parasites).
- "stringmol 2022-2025 parasite self-scan": no follow-up on the self-scan path.
- "Tierra immunity 0079aab mechanism": only Ray's own papers and secondary
  summaries that repeat them.
- "Tierra/Avida hosts parasites evolved resistance mechanism ALIFE 2022-2025":
  only the 2022 ISAL review by Vostinar et al.
  (https://direct.mit.edu/isal/proceedings/isal2022/34/4/112293, 403, not read).
- "Amoeba / Coreworld / Cosmos 2021-2025": nothing.

## 10. Answers to the plan's questions, from this cluster

**Q1. Has anyone explained why an evolved defence was reachable, with the path
and the fitness of intermediates?** No. The closest are: Stringmol 2021, which
gives a six-stage qualitative path to the first self-scan with no fitness and
with intermediates that are explicitly "not self-sustaining" (section 1); Ray
1992, which gives the finished mechanism of the hyper-parasite (2 functional
changes among 19 differences) and only an assay for immunity (section 4); and
Lenski 2003, which does the full path-with-fitness analysis but for a rewarded
logic function, not a defence (section 7.1). A path analysis for an evolved
defence, with the fitness of each intermediate, is the gap. E009's framing is
therefore not a replication.

**Q2. Controlled comparison of parasite cost against defence evolution?** No in
a program substrate. Avida's virulence knob exists (Zaman 2011) but was used
only to show Lotka-Volterra against equilibrium dynamics, and every later Avida
parasite paper fixes it at 0.8 (sections 5.1, 5.2, 5.6). Stringmol has no cost
arm (section 1). Seoane & Sole 2023 sweep a per-bit cost in a bit-guesser model
and get a phase diagram, not a defence-evolution rate (section 6.1). Jha et al.
2026 (abstract only) tie execution to energy in a Z80 soup and report suppressed
stealing, with no cost sweep visible in the abstract (section 6.2). E008-E010
are the comparison.

**Q5. Venue and scale of the closest work.**

| Work | Venue | Replicates | Length | Population / world |
|---|---|---|---|---|
| Hickinbotham et al. 2021 | R. Soc. Open Sci. | 20 runs (8 survived) | 2 x 10^6 timesteps | 12,500 cells, 65-symbol seed |
| Zaman et al. 2011 | GECCO | 50 + 50 | 200,000 updates | 14,400 cells |
| Zaman et al. 2014 | PLoS Biology | 50 per treatment | 500,000 updates | well-mixed chemostat |
| Acosta & Zaman 2022 | Frontiers Ecol Evol | 10 per treatment | 300,000 updates | 22,500 cells |
| Lenski et al. 2003 | Nature | 50 per environment (960 runs in all) | 100,000 updates | 3,600 cells |
| Fortuna et al. 2017 | PLoS Comp Biol | 1,000 populations | 10^6 updates | sampled genotypes only |
| Seoane & Sole 2023 | Phys. Rev. E | not stated in the parts read | 200 generations | N = 1,000 spots |
| Ray 1992 | SFI working paper | single runs, pairwise assays | up to 10^9 instructions | 60,000-cell soup |

evo's E007-E010 (10 seeds x 250,000 ticks, about 900-1,000 organisms over 128 x
512 bytes) are inside this range on replicates and population and at the short
end on length measured in generations: Lenski's 100,000 updates were 15,873
ancestral generations; E008's hosts die at a median age of about 19 ticks, so
250,000 ticks is of the order of 10^4 generations, comparable.

**On E009's "four neutral insertions" argument.** It is not a known result;
nobody has counted the steps to a defence in any of these systems. Three
published results bear on it. (a) Lenski 2003: a 17-35-instruction feature was
reached in 23 of 50 populations through a line of descent with 48 neutral and
18 deleterious steps in 111, because intermediate steps were paid by other
functions; the implication for E009 is that a defence with *no* paying
intermediate is a different case from anything shown reachable in Avida. (b)
Standish 2004: with parasites present and the soup at capacity, neutral steps
are followed less often than their availability predicts, so a four-neutral-step
path is rarer than a neutral-network count gives. (c) Stringmol 2021: the only
evolved self-scan reached its state by region-level rearrangements, not by
single neutral insertions, under a variation operator evo does not have. None
contradicts E009; (b) strengthens it and (c) says the Stringmol precedent does
not transfer.

## Not reached

- Zaman 2018 ALIFE (MIT Press 403).
- Hickinbotham 2023 GECCO Nanopond (ACM 403, ResearchGate 403, York Pure 404).
- Vostinar et al. 2022 ISAL "Symbiosis in Digital Evolution: A Review and
  Future Directions" (MIT Press 403).
- Wilke 2001 and Covert 2013 full texts (Nature and PNAS 403); abstracts read.
- Jha et al. 2026 full text (only the abstract page was fetched in the time
  box); recommended first read for a follow-up.
- Stepney & Hickinbotham 2021 ALIFE full text (MIT Press, not attempted after
  the other 403s).
