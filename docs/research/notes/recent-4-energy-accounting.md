# Energy and resource accounting in digital evolution: verified notes (cluster 4)

Compiled 2026-10-08 (finished 2026-10-09). Purpose: cluster 4 of
`docs/research/literature-recent-plan.md`. Whether anyone has made parasitism
cost the host, as E008–E010 did (`docs/research/experiments/2026-10-07-e008-*`,
`2026-10-08-e009-*`, `2026-10-08-e010-*`); how energy is stored and paid in
other systems; and what that says about PLAN §9 "energy location" (the host's
store is smaller than one pass of its own loop, so an owner-side charge is
either invisible or fatal).

How this was checked:

- PDF text extracted with `pdftotext` and read directly: Cooper & Ofria 2002,
  Vostinar et al. 2021 (NSF PAR copy), Kruszewski & Mikolov 2020 and 2021/22,
  Seoane & Solé (arXiv 1910.14339 v4).
- Full HTML read through the fetch tool, which returns a summary of the whole
  page rather than the raw text: Zaman et al. 2014 (PLoS Biology), Vostinar &
  Ofria 2019 (bioRxiv full text), Strona & Lafferty 2016 (PMC), Cicala et al.
  2026 (arXiv HTML), Dolson & Ofria 2021 (Frontiers), the Avida wiki energy page,
  `avida.cfg` and `nanopond.c` on GitHub. Numbers from these are as the tool
  returned them; where a number matters and I could not see the sentence, I say
  so.
- Taylor's Cosmos thesis chapters fetched over plain HTTP with `curl` and read
  as stripped text (the host's TLS certificate is wrong, so the fetch tool
  cannot reach it).
- Abstract only (via Europe PMC or Semantic Scholar): Chow et al. 2004, Young &
  Neshatian 2013, Zaman et al. 2011, Buliga 2023. Facts from these are
  tagged **UNVERIFIED** where they go beyond the abstract.
- Paywalled and not read: Zaman et al. 2011 (ACM), Young & Neshatian 2013
  (Springer), Chow 2004 (Science), Ashby et al. 2014 (UChicago). Noted below.
- Nothing is cited from memory. Searches that returned nothing are recorded in
  §10.

Terms used below:

- *Store*: energy held by one organism and spent per instruction (evo, Cosmos,
  Nanopond, Avida's energy model). *Rate*: a per-update instruction budget with
  nothing saved between updates (Tierra's slice, Avida's merit). *Depth*: store
  divided by the instructions in one pass of the organism's loop; evo's hosts
  are under 1 pass deep (E010).
- *Owner pays*: the organism whose bytes are executed is charged (E008). *Split*:
  owner and executor share the charge (E009). *Transfer*: the executor gains
  what the owner loses (E010).

---

## 1. Avida parasites: the host pays for the intruder's execution (Zaman et al. 2011, 2014)

This is the closest published precedent for E008/E009, and it predates them.

**Mechanism.** In Avida a parasite is a genome injected into a host's CPU;
it has no cell of its own. "When a parasite infects a host, it acquires a
portion of the infected host's CPU cycles"; "The probability of a parasite
stealing a CPU cycle from its host is configurable and referred to as
'virulence'. When virulence is set to one, parasites steal all CPU cycles
from their hosts", killing them (Vostinar et al. 2021 review, read from the
PDF, https://par.nsf.gov/servlets/purl/10354950; the same wording is on the
PLoS page https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1002023).
So the host pays, in CPU cycles, for every instruction the parasite executes,
at a fixed probability. This is E009's split rule with the split set by
virulence, and E008's owner-pays rule at virulence 1.

**Zaman, Meyer, Devangam, Bryson, Lenski, Ofria 2014**, "Coevolution Drives
the Emergence of Complex Traits and Promotes Evolvability", *PLoS Biology*
12(12): e1002023,
https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1002023
(fetch summary of the full article):

| Quantity | Value |
|---|---|
| Virulence | parasite takes 80% of the host's CPU cycles; constant, not varied across treatments |
| Infection rule | a parasite can infect only a host that performs at least one of the parasite's logic functions |
| Replicates | 50 per treatment |
| Length | 500,000 updates (an update is about 30 CPU cycles per organism) |
| Hosts | carrying capacity 14,400; 400 parasites injected at update 2,000 |
| Mutation | hosts 0.25 per genome copy, parasites 0.5; 90% point, 5% insertion, 5% deletion |
| Result | EQU evolved in 17/50 host populations with parasites, 0/50 without; median host complexity about 4–5 NAND-equivalents with parasites against under 2 without |
| Resistance | hosts escape by changing which functions they perform ("function-switching mutations" were ">10-fold more common in hosts that evolved with parasites") and by specialising on single functions |

**What the host pays with.** The cost is throughput, not survival. An
infected host runs at 20% speed, so it reproduces later and is more likely to
be overwritten by a neighbour's birth; it does not starve, because Avida's
merit is a per-update rate with no store to hit zero. Resistance is
lock-and-key (which task set the host expresses), not an energy defence;
parasites must match a task to enter. Dolson & Ofria 2021 describe the
same mechanism from the ecology side: parasites "steal CPU cycles" and
"Hosts must perform novel tasks to survive infection pressure"
(https://www.frontiersin.org/journals/ecology-and-evolution/articles/10.3389/fevo.2021.750779/full).

**Zaman, Devangam, Ofria 2011**, GECCO, "Rapid host-parasite coevolution
drives the production and maintenance of diversity in digital organisms",
https://doi.org/10.1145/2001576.2001607 (abstract and search snippets only;
paywalled). The snippet gives the same 80% figure and says the parasite
"uses [the cycles] to execute and copy its own genome, while imposing a
severe cost on the host" (**UNVERIFIED**, snippet).

**Graded or randomised virulence.** No Avida paper found varies virulence as
a treatment against resistance. Strona & Lafferty 2016 (§2) randomise it.
Vostinar et al. 2021 (§1 above) state that virulence "can be experimentally
varied across a continuum" but cite no study that did so against defence.

**For evo.** Someone has made the host pay for intruder execution, at 80% and
at 100%, in 50-replicate runs, and got resistance; but their host loses
reproduction rate, not life, because the cost is drawn from a rate rather
than a store. E008's "the full charge kills an entered host within one
intruder cycle" has no Avida counterpart because Avida has no store to
empty. The design difference is exactly PLAN §9's question.

## 2. Strona & Lafferty 2016: randomised, mutable virulence in Avida

"Environmental change makes robust ecological networks fragile", *Nature
Communications* 7:12462, PMC4987532,
https://pmc.ncbi.nlm.nih.gov/articles/PMC4987532/ (fetch summary of the
full article).

- Virulence is "the percentage of central processing unit (CPU) cycles
  subtracted from a host". Parasites start at virulence 1 and "we also
  allowed parasite virulence to mutate throughout the experiment".
- 100 coevolution simulations with randomised "carrying capacity, parasite
  virulence, resource availability, injection timing and amount of ancestral
  parasites"; parasites injected after 1,000–5,000 updates; runs end at a
  random point between 10^5 and 5 × 10^5 updates.
- Host vulnerability is measured after mutation is switched off, by the order
  in which host species go extinct in competition (h/H).
- No result links virulence to resistance; the paper is about network
  robustness.
- For evo: the only Avida study found with virulence as a free variable, and
  it does not report defence. The cost-vs-defence comparison is open there.

## 3. Symbulation (Vostinar & Ofria 2019): a graded host defence that evolves

"Spatial Structure Can Decrease Symbiotic Cooperation", *Artificial Life*
24(4): 229–249, https://doi.org/10.1162/artl_a_00273; full text read via
bioRxiv https://www.biorxiv.org/content/10.1101/393868v1.full (fetch
summary). ISAL outstanding student paper (search result,
https://www.carleton.edu/directory/vostinar/, **UNVERIFIED**).

**Substrate.** Not an instruction machine. Each host and each endosymbiont is
one evolvable number, the interaction value, in [-1, +1]. A host receives 25
resources per update. A host with a negative value "invests that proportion
of the new resources available to it into defense"; a symbiont with a
negative value steals: "The amount that the symbiont's value is more negative
than the host's value determines the proportion of resources the symbiont is
able to steal from the host" (example in the text: symbiont -0.8 against host
-0.3 steals 50% of what is left after the host's 7.5 defence spend). Positive
values donate, with a 5× synergy on returned resources. Hosts reproduce at
100 stored resources, symbionts at 50 (horizontal transmission); vertical
transmission probability is the treatment variable. Mutation is Gaussian,
SD 0.002.

| Quantity | Value |
|---|---|
| World | 10,000 organisms; well-mixed or 2D Moore neighbourhood |
| Length | 100,000 updates |
| Replicates | 20 per treatment |
| 0% vertical transmission, well-mixed | symbionts "fully parasitic", hosts "investing half of its resource into defense" |
| 100% vertical transmission | "extreme mutualism" |
| De novo from neutral values | symbionts went extinct "except when the vertical transmission rate is 100%" |
| Spatial, 60–70% VT | more parasitism locally (mean values -0.218 to 0.385 local against 0.663 to 0.759 global, as the fetch tool reported them) |

**Store depth.** The host's "store" is 100 resources at 25 per update: four
updates of income, and nothing is executed, so depth in passes has no
meaning here.

**For evo.** This is the one digital system found in which defence against a
parasite is a continuous, costed trait and the cost of parasitism is graded,
and the hosts did evolve to pay for defence (about half their income at 0%
vertical transmission). It is not an instruction-level substrate: defence is
a single number with a fixed exchange rate, not a code change that must be
reachable by mutation. So it answers "does graded cost select for a costed
defence" (yes, in 20 of 20 replicates per the text's description) but not
E009's reachability question.

## 4. Avida's energy model and resource models (Beckmann 2010; Cooper & Ofria 2002; Chow et al. 2004)

### 4.1 The energy model as it stands in the code

The thesis mechanics are in `avida-stringmol.md` §1.9 (store, metabolic
rate = store / `NUM_CYCLES_EXC_BEFORE_0_ENERGY`, cost per instruction =
rate × per-instruction cost, death at zero, 5% decay and an even split at
divide). The current `avida.cfg`
(https://raw.githubusercontent.com/devosoft/avida/master/avida-core/support/config/avida.cfg,
fetched) adds the options that bear on energy location:

| Option | Default | Meaning (comment in the file) |
|---|---|---|
| `ENERGY_ENABLED` | 0 | energy model off |
| `NUM_CYCLES_EXC_BEFORE_0_ENERGY` | 0 | "Number of virtual CPU cycles executed before energy is exhausted" |
| `ENERGY_CAP` | -1 | "Maximum amount of energy that can be stored in an organism. -1 = no max" |
| `FRAC_PARENT_ENERGY_GIVEN_TO_ORG_AT_BIRTH` | 0.5 | parent's energy given to the child |
| `FRAC_ENERGY_DECAY_AT_ORG_BIRTH` | 0.0 | lost at reproduction |
| `FRAC_ENERGY_TRANSFER` | 0.0 | "Fraction of replaced organism's energy take by new resident" |
| `ENERGY_SHARING_METHOD` / `ENERGY_SHARING_PCT` | 0 / 0.0 | donation between organisms, receiver-pull or pushed |
| `RESOURCE_SHARING_LOSS` | 0.0 | "Fraction of shared resource lost in transfer" |
| `ATTACK_DECAY_RATE` | 0.0 | "Percent of cell's energy decayed by attack" |
| `ENERGY_THRESH_LOW` / `HIGH` | 0.33 / 0.75 | thresholds for energy-level sensing, require `ENERGY_CAP` |
| `FIX_METABOLIC_RATE` | -1 | fixes the rate instead of deriving it from the store |

The wiki page (https://github.com/devosoft/avida/wiki/Energy-model-configuration)
gives the same options in older names (`NUM_INST_EXC_BEFORE_0_ENERGY`). Note
`FRAC_ENERGY_TRANSFER`: the organism that overwrites another can take a
fraction of the victim's store. That is a transfer rule at death, not per
instruction, and no paper using it was found (§10).

**Store depth, designed in.** Because the metabolic rate is store divided by
`NUM_CYCLES_EXC_BEFORE_0_ENERGY`, an Avida store always lasts that many
instructions whatever its size: depth in instructions is a constant, 2,000
in the thesis runs against a 100-instruction ancestor, so about 20 passes
(`avida-stringmol.md` §1.9, from the thesis
https://d.lib.msu.edu/etd/17557, pp. 26–27). Energy changes speed, not
lifetime. This is the opposite choice from evo's, where the store is a fixed
cap of 64 per byte and the spend rate is fixed, so depth is whatever the cap
and the loop length make it.

**Follow-ups after 2010.** Searched (§10); none found that use the energy
model for parasites or ownership. Beckmann's later Avida work is on quorum
sensing and quorum quenching (Beckmann, Knoester, Connelly, McKinley 2012,
*Artificial Life*, search result only, **UNVERIFIED**), not energy.

### 4.2 Limited resources (Cooper & Ofria 2002)

"Evolution of Stable Ecosystems in Populations of Digital Organisms",
*Artificial Life VIII* (MIT Press) pp. 227–232,
https://cse.msu.edu/~ofria/pubs/2002CooperOfria.pdf (PDF read).

- "Resources are globally available to all organisms. In previous versions
  of Avida, resource levels were infinite ... In this study, we add the
  capability of feedback between the use of a resource and its level, such
  that the use of a resource by one organism lowers the availability of that
  resource to all others. A low concentration of a resource will reduce the
  benefit that can be gained by performing its associated computation."
  The model is "analogous to ... bacterial chemostats".
- Nine resources, one per logic task (NOT through EQU). Using one "increases
  the speed at which an organism executes its instructions": the reward is
  merit (rate), never a store.
- 69 populations, 30 limited and 39 infinite; capacity 2,500; 100,000 updates
  with copy mutation 0.0075 per instruction and indel 0.05 per genome, then
  50,000 updates with mutation off ("ecology phase"). An update is 30 ×
  population size instructions.
- Result: genotypic and phenotypic diversity higher under limitation
  (Mann-Whitney, P < 0.0001 both); one generalist population settled to three
  stably coexisting genotypes by 300,000 updates and held them to 500,000;
  a nine-genotype specialist population held all nine for 100,000 updates;
  with resources set back to infinite "all populations quickly became
  dominated by" the fittest genotype.
- For evo: nobody pays for anything here. Depletion lowers the *reward* for a
  task; execution stays free. This is the "resource" that evo's patch sun
  already is (absorb yield falls as the pool drains, E004).

### 4.3 Adaptive radiation (Chow, Wilke, Ofria, Lenski, Adami 2004)

*Science* 305: 84–86, https://doi.org/10.1126/science.1096307. Abstract only
(Europe PMC): "maximum species richness emerges at intermediate productivity,
even in a spatially homogeneous environment, owing to frequency-dependent
selection to exploit an influx of mixed resources". Inflow rates, population
size and replicates are behind the paywall (**UNVERIFIED**). Same accounting
as §4.2: resources modulate merit; no per-instruction cost.

The 2009 platform chapter (https://www.cse.msu.edu/~ofria/pubs/2009AvidaIntro.pdf,
not re-read for this cluster) is the one that defines a resource by initial
quantity, inflow and outflow (search snippet, **UNVERIFIED**).

## 5. Cosmos (Taylor 1999): a one-pass-deep store, and neighbours as energy

Thesis chapters, fetched over HTTP from
http://archive.tim-taylor.com/papers/thesis/html/ and read as text:
`node59.html` (Energy Token Store), `node60.html` (Cell Death),
`node76.html`–`node79.html` (distribution and collection), `node94.html`
(differences from Tierra), `node110.html` (standard run parameters),
`node215.html` (minor-parameter defaults). This extends `literature.md` §2.5
with the store numbers.

- "it must pay one energy token to the processor for each instruction it
  executes." The store "may be leaky, in which case a number of energy tokens
  are lost from the store at the end of each time slice" (`ets_leak_rate_per_timeslice`,
  default 1).
- Death: "If the number of tokens in this store falls below a particular
  threshold (`ets_lower_threshold`, default 1), the cell dies." At
  `max_cells_per_process` (2,500 in the standard run) the processor kills
  cells with the fewest tokens. "When a cell dies, any energy tokens
  remaining in its Energy Token Store are distributed to the local
  environment."
- Standard run: 30 tokens per grid square per sweep, square cap 100
  (`max_energy_tokens_per_grid_pos`), 10 tokens per `et_collect`
  (`number_of_energy_tokens_per_collect`), **cell cap 100 tokens**
  (`max_energy_tokens_per_cell`), ancestor starts with 50
  (`default_ets_level_of_ancestor`), `et_value_power` 1.0, collection
  `shared`, distribution `land`.
- Shared collection: if the square lacks tokens the cell "looks for other
  cells at the same grid position or in one of the eight neighbouring grid
  positions ... energy tokens will be extracted from the Energy Token Store of
  one (or more) of these (at random)". Taylor saw the consequence: "a cell is
  a potential energy resource for other cells, and, if environmental energy
  were scarce, it would become advantageous for a cell to kill its neighbours
  by draining their energy. If cells could defend themselves against such
  attacks, some sort of coevolutionary process might arise." `literature.md`
  §2.5 records what happened instead: energy theft froze evolution and no
  parasites arose.

**Store depth.** The ancestor is 348 bits of 6-bit instructions, so 58
instructions (`literature.md` §2.5; ancestor page `node216.html` not
re-read). A 100-token cap is 1.7 passes; the 50-token start is under one
pass; each `et_collect` buys 10 instructions. Cosmos's store is as shallow
as evo's, and draining a neighbour by one `et_collect` takes a sixth of its
loop. Energy is per cell, as in evo, not per byte.

## 6. Nanopond (Ierymenko): per-instruction store, execution stops at zero

`nanopond.c`, https://raw.githubusercontent.com/adamierymenko/nanopond/master/nanopond.c
(fetched; constants as returned):

| Constant | Value |
|---|---|
| `INFLOW_FREQUENCY` | 100 ticks |
| `INFLOW_RATE_BASE` / `INFLOW_RATE_VARIATION` | 600 / 1000: a random cell gets 600 + rand(1000) energy and a random genome |
| `POND_DEPTH` | 1,024 codons |
| `MUTATION_RATE` | 5000 (the code's scale; `literature.md` §2.6 gives about 1.16 × 10^-6 per executed instruction) |
| `FAILED_KILL_PENALTY` | 3 |

- "Each instruction processed costs one unit of energy" (`--pptr->energy`);
  the execution loop is `while ((pptr->energy)&&(!stop))`, so a cell stops
  mid-pass at zero and waits for inflow. No store cap beyond what inflow
  gives.
- `SHARE` equalises the two cells' energy; `KILL` transfers nothing. A cell
  executes only its own genome, so there is no "executing another's bytes"
  and no one to charge.
- Depth: 600–1,600 units against a genome of up to 1,024 codons: about one
  pass of a full-length genome, many passes of a short one. Short genomes get
  more passes per inflow, a size pressure additional to the ones in
  `literature.md` §4.1.

## 7. Seoane & Solé: a parasite that "sucks off reward", host complexity as the defence

"How Turing parasites expand the computational landscape of digital life",
arXiv 1910.14339 (v4 read as PDF text), published *Physical Review E*
October 2023 per the arXiv page (https://arxiv.org/abs/1910.14339).

- Not an instruction machine. A host is an n-bit "guesser" predicting an
  m-bit random environment; "Bit-guessers pay a cost c for each bit that they
  attempt to predict, and they rip off a reward r for each correct
  prediction". Net reward per evaluation is (p − η)·r·n with η = c/r, so a
  guesser dies out where its hit rate p < η.
- A parasite is a guesser whose environment is the host (its genotype or its
  phenotype) and "just sucks off reward ... whenever its host is evaluated".
  In the spatial model, a host replicates when its accrued reward exceeds
  2nε0 and "an amount nε0 (as initial endowment for the daughter) is
  subtracted"; "The initial endowment of this daughter parasite is subtracted
  from the daughter host." So the host pays both the parasite's upkeep and its
  reproduction.
- Result: "Even the simplest (n' = 1) parasite ... suffices to achieve a
  remarkable complexity boost. Simpler hosts are more predictable, hence
  parasites extract more reward—favoring complex hosts. In return, the point
  at which the ecosystem collapses happens for lower η." Phases: monotonous
  growth, punctuated equilibrium, collapse; the abstract calls it a "minimal
  model".
- Store depth: the endowment is nε0, proportional to complexity, and
  replication needs 2nε0; depth is in evaluations, not instructions.
- For evo: a controlled comparison (no parasite / genotype parasite /
  phenotype parasite, Fig. 6 of the paper) of parasite cost against the
  evolution of a defence (complexity, which makes the host harder to predict).
  Host pays, defence evolves. But the defence is a scalar n, and the parasite
  is undying in that treatment; no mutational path to a defence exists to be
  analysed.

## 8. Artificial chemistries with conservation: matter yes, energy mostly no

### 8.1 Kruszewski & Mikolov 2020, 2021/22 (combinatory logic)

ALife 2020 paper, arXiv 2003.07916 (PDF read); journal version *Artificial
Life* 27(3–4) 2021/22, arXiv 2103.08245 (PDF read; also in
`bff-and-recent.md` §3.3). A reduction consumes its reactant from the
multiset, so "conservation laws keep the system bounded without introducing
any artificial limit on the size of the expressions" (2020 PDF, grep of the
text); the authors say "While the original Chemlambda did not consider
conservation laws, an extension called Hapax is currently exploring them"
(2021 PDF). **No energy in either paper**: the word does not occur in either
text. A search snippet claiming "the addition of energy control alone is able
to keep the molecules within reasonable length bounds" and "a narrow energy
range" could not be found in either PDF and is recorded as **UNVERIFIED and
unattributed**. No parasites or predation are discussed. For evo: conservation
of matter replaces a reaper, as `literature.md` §4.2 lists for Stringmol's
2015 conservation variant; nobody pays for computation.

### 8.2 Buliga: Chemlambda, Hapax, chemSKI with tokens

"chemSKI with tokens: world building and economy in the SKI universe",
arXiv 2306.00938 (abstract only). Tokens make graph rewrites conservative and
give "a new estimation of the cost of a combinatory calculus computation";
no evolution, selection or organisms. Hapax is "conservative graph rewriting
with tokens" (search results, https://mbuliga.github.io/hapax/chemlambda-and-hapax.html,
**UNVERIFIED**). Irrelevant to who pays for whom.

### 8.3 Young & Neshatian 2013

"A Constructive Artificial Chemistry to Explore Open-Ended Evolution", AI
2013, LNCS 8272, https://doi.org/10.1007/978-3-319-03680-9_25 (abstract only,
4 citations on Semantic Scholar). "an energy model based on the conservation
of total kinetic and potential energy" over a cheminformatics toolkit. No
organisms, no parasites reported in the abstract. **UNVERIFIED** beyond that.

### 8.4 Squirm3, Stringmol conservation

Already in `literature.md` §2.10 and §2.7: Squirm3 has conserved matter and
no energy; Stringmol 2015 fixed per-symbol counts. Nothing new found for
either after 2020 in this cluster's searches (§10). Vostinar et al. 2021
summarise the Stringmol 2021 defences in cost terms: "Introduction of fixed
reproductive costs further decreased the competitive advantage of parasites
because the relative cost was less for other hosts than for parasites"
(PDF, p. 9), which is the self-scan already in `literature.md`.

## 9. Cicala et al. 2026: a runtime penalty that cannot kill

arXiv 2607.09211 v2 (HTML fetched; mechanics also in `bff-and-recent.md`
§3.1). The "metabolic constraint" discounts a validated program's interaction
probability by C·(k/B), k the mean steps in three validation runs, B = 512,
C in 0 to 0.7. "No energy store or cap exists". Interactions, where a
program executes the concatenated 64-byte tape including its partner's half,
are free. Result as returned: conditional halting (skipping replication
during validation) rose with the penalty (Spearman ρ = 0.21, p < 0.0001 at
C = 0.3). Scale: 2^19 programs, 32 niches of 128 × 128, 10^6 epochs
(10^7 for controls), mutation 1/64 per program per epoch. For evo: the only
2024–2026 soup paper with a cost on computation, and it is a selection bias
on a rate, not a store, and nobody is charged for the partner's bytes.

## 10. Searched for and not found

- Any paper after 2010 using Avida's energy model with parasites, `inject`,
  `FRAC_ENERGY_TRANSFER` or `ENERGY_SHARING` (searches: "Avida energy model
  Beckmann 2011..2020", "ENERGY_SHARING Avida", "Avida energy model parasite").
  The energy model appears only in Beckmann's own 2007–2010 work.
- Any Avida study varying virulence as a treatment and reporting resistance
  (searches on "virulence" with Zaman, Fortuna, Lalejini, Dolson, 2015–2026).
  Zaman 2014 fixes it at 0.8; Strona & Lafferty randomise it and do not
  report resistance.
- Any instruction-level system after 2010 in which executing another
  organism's bytes charges the owner (searches: "per-instruction energy
  ownership", "digital evolution energy host pays executed instructions",
  Semantic Scholar 2021–2025). Tierra, Coreworld, Cosmos and BFF charge the
  executor or nobody; Avida charges the host but has no shared memory.
- Cosmos follow-ups after 2000 with energy: none.
- Winfield 2014, "Estimating the Energy Cost of (Artificial) Evolution",
  ALIFE 14 (https://direct.mit.edu/isal/proceedings-pdf/alife2014/26/872/1901349/978-0-262-32621-6-ch143.pdf):
  the electricity cost of running evolutionary robotics; irrelevant, not read.
- Spirov 2023, "Co-evolution of replicators and their parasites", arXiv
  2312.17540: a 14-page review in Russian on RNA-world models; no energy
  accounting in the abstract; not read further.
- Ashby, Gupta, Buckling 2014, "Spatial Structure Mitigates Fitness Costs in
  Host-Parasite Coevolution", *Am. Nat.* 183: E64 (abstract via search): a
  mathematical model of generalism costs, not a digital-organism system;
  paywalled; not read.
- Polyworld, Aevol and other agent systems with per-organism energy but no
  executable shared memory: not searched; out of scope by the plan's
  wording.

## 11. Store depth across systems

Depth = store ÷ instructions per pass of the organism's own loop.

| System | Store | Spend | Depth | Source |
|---|---|---|---|---|
| evo (E010) | cap 64 per owned byte; host holds about 100–130 | 1 per instruction, fixed | under 1 pass | `2026-10-08-e010-transfer.md` Results |
| Cosmos standard run | cap 100 per cell, ancestor starts at 50, +10 per `et_collect`, leak 1 per slice | 1 per instruction | 1.7 passes at cap, 0.9 at start (58-instruction ancestor) | §5 |
| Nanopond | 600–1,600 per inflow event, no cap | 1 per instruction; stops at 0 | about 1 pass of 1,024 codons, many of a short genome | §6 |
| Avida energy model (thesis runs) | uncapped (`ENERGY_CAP` -1); half to the child | rate = store / 2,000 per instruction | always 2,000 instructions = 20 passes of a 100-instruction genome, by construction | §4.1 |
| Avida default (merit) | none; per-update slice | n/a | n/a (rate) | `avida-stringmol.md` §1.7 |
| Tierra | none; CPU slice | n/a | n/a (rate) | `literature.md` §2.2 |
| Stringmol well-mixed | none per molecule; fixed energy per step for the whole vessel | 1 per bind attempt or instruction | n/a | `avida-stringmol.md` Part 2 |
| Symbulation | 100 resources to reproduce, 25 income per update | nothing executed | 4 updates (not instruction-based) | §3 |
| Seoane & Solé | endowment nε0, replicate at 2nε0 | per evaluation, (p − η)rn | 1 endowment = half a replication; scales with n | §7 |
| Cicala 2026 | none | selection bias C·k/512 | n/a (rate) | §9 |

Reading: the two systems whose store is spent per instruction at a fixed
rate and is capped per cell, Cosmos and evo, both sit near one pass deep,
and both saw no parasites and no defence. Avida's energy model is the only
one that makes depth a constant independent of store size, by tying spend
rate to the store. Nanopond's depth depends on genome length, which is a
size pressure.
