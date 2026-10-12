# Recent work, cluster 6: hosts, symbionts and the reachability of defence (ALIFE 2023–2026)

Compiled 2026-10-12. Purpose: cluster 6 of `docs/research/literature-recent-plan.md`
(round 2, ALIFE proceedings). This file covers the Dolson, Vostinar, Lalejini, Ofria,
Ferguson and Bohm line, the peer-reviewed neighbour of E008–E010. It answers the
plan's questions 2, 3 and 5, plus an added question 6 on store depth. Context for
evo: E008–E010 charged a host for instructions an intruder ran on its bytes (full
charge, split, transfer), and no defence evolved. The diagnosis was that the host's
store is less than one pass of its copy loop, so an owner-side cost is either
invisible or fatal. E009 also argued that its five-byte self-scan defence needs four
neutral insertions before the fifth pays, so it is out of reach. The next experiment on store depth will make
store depth a parameter.

This file does not repeat `notes/recent-1-host-parasite.md` (Lenski 2003, Covert
2013, Standish 2004, Zaman 2011/2014, Stringmol) or `notes/recent-4-energy-accounting.md`
§3 (Vostinar & Ofria 2019). It extends them where these papers add something.

## How each paper was checked

| Paper | DOI | How read | Source of the text |
|---|---|---|---|
| Kelley et al. 2026 | 10.1162/isal.a.1024 | full text + experiment code | EcoEvoRxiv preprint (CC BY camera-ready layout), https://ecoevorxiv.org/repository/object/12471/download/25539/ ; repo https://github.com/amlalejini/2026-alife-mutualism-constrains-evolution |
| Johnson et al. 2026, "Saved by the Symbiont" | 10.1162/isal.a.1025 | full text + code + Symbulation source at the pinned commit | EcoEvoRxiv https://ecoevorxiv.org/repository/object/13555/download/23817/ ; Zenodo https://doi.org/10.5281/zenodo.19477499 |
| Johnson, Croft, Vostinar, Lalejini & Dolson 2025 | 10.1162/isal.a.885 | abstract + code + the authors' erratum + supplement of the journal follow-up | Crossref abstract; https://github.com/john-k-903849031/ALIFE2025-TagPartnerChoice ; https://github.com/john-k-903849031/TagPartnerChoice_journal |
| Croft, Johnson, Vostinar & Dolson 2024 | 10.1162/isal_a_00790 | abstract + analysis script | OpenAlex abstract; https://github.com/emilydolson/ALIFE-2024-DeNovoMutualism |
| Ferguson, Ofria & Bohm 2024 | 10.1162/isal_a_00801 | full text | proceedings PDF on Ferguson's site, https://fergusonaj.github.io/docs/pubs/ferguson_et_al_2024_replaying_adaptive_momentum.pdf |
| Ferguson & Ofria 2023 | 10.1162/isal_a_00684 | full text | https://fergusonaj.github.io/docs/pubs/ferguson_ofria_2023_potentiating_mutations_facilitate_learning.pdf |
| Ragusa & Bohm 2023 | 10.1162/isal_a_00660 | abstract only; the full study read as Bohm, Ragusa, Ofria, Lenski & Adami 2024 | bioRxiv https://doi.org/10.1101/2024.04.08.588357 (PDF https://www.biorxiv.org/content/biorxiv/early/2024/04/11/2024.04.08.588357.full.pdf) |
| Sanson & Ferguson 2025 | 10.1162/isal.a.895 | full text | https://fergusonaj.github.io/docs/pubs/sanson_ferguson_2025_evolvability.pdf |
| Escondo & Ferguson 2026 | 10.1162/isal.a.1014 | full text | https://fergusonaj.github.io/docs/pubs/escondo_ferguson_2026_replay_methods.pdf (also EcoEvoRxiv https://ecoevorxiv.org/repository/object/13054/download/23133/) |
| Gordon, Ferguson, Dolson & Lalejini 2025 | 10.1162/isal.a.863 | full text | https://fergusonaj.github.io/docs/pubs/gordon_et_al_2025_env_connectivity.pdf |
| Shea, Leither, Foreback, Dolson & Lalejini 2024 | 10.1162/isal_a_00749 | full text, skimmed | EcoEvoRxiv https://ecoevorxiv.org/repository/object/6994/download/13420/ |
| Johnson, Dirkswager & Vostinar 2023 | 10.1162/isal_a_00661 | no abstract found; code only | https://github.com/K-Johnson-Horrigan/SGP-Endosymbiosis-Evolution |
| Leither 2023, Foreback 2023, Chaturvedi 2026, Bielawski 2025, Gaylinn 2025 | see §13 | abstract only, **UNVERIFIED** | Crossref (2025/2026) and OpenAlex (2023) |

All PDFs fetched were saved to `docs/downloaded-papers/` as `<doi-suffix>_<FirstAuthor>.pdf`.
The bioRxiv paper is saved as `biorxiv.2024.04.08.588357_Bohm.pdf`. Text was extracted with
`pdftotext`. Code facts come from the repository file named next to them. Code
repositories count as evidence for how a mechanism is encoded, not for what a paper
reports. Where a paper's text and its code disagree, both are given.

## Terms

- *Symbulation*: Vostinar's agent-based platform for host–symbiont coevolution. It has
  two modes. In "default" mode each organism is one number, the *interaction value*
  in [−1, +1]: negative values mean defence (hosts) or theft (symbionts), positive
  values mean donation. In "SGP" mode each organism is a 100-instruction program in
  the SignalGP representation, run on a small virtual CPU.
- *Endosymbiont*: a symbiont that lives inside a host; at most one per host in every
  paper here. *Vertical transmission*: a symbiont's offspring enters the host's
  offspring. *Horizontal transmission*: it infects another, random host.
- *Update* (Symbulation, Avida): one time step. In SGP-mode Symbulation every organism
  gets 16 *CPU cycles* (16 instructions) per update.
- *Logic-9 tasks*: the Boolean functions NOT, NAND, AND, ORN, OR, ANDN, NOR, XOR and EQU.
  Their *complexity* is the minimum number of NAND gates that implement them: 1 for
  NOT/NAND, up to 5 for EQU.
- *Trait (task) matching*: a symbiont interacts with its host only if both perform
  the same task. A host that switches to a task its symbiont does not perform is
  *resistant*, the "lock and key" of round 1.
- *Tag matching*: each organism carries an evolvable bit string (the *tag*). A
  symbiont can infect a host only if their tags are similar enough.
  *Permissiveness* sets how much mismatch is allowed.
- *Bottleneck control*: a run in which hosts are killed at random at the same rate as
  in the treatment. It separates selection by the symbiont from plain mortality.
- *Potentiation*: the probability that a population or genotype goes on to evolve a
  target trait, measured by *analytic replay*: many runs are restarted from a saved
  point in history and the fraction that reach the trait is counted.
- *Fitness valley*: a series of mutations that each lower fitness before a later one
  raises it. *Valley crossing* means a lineage finishes that series.
- *Selective sweep*: a beneficial mutation spreading through the population. On a
  line or ring it spreads as a front, the *leading edge*.
- *Adaptive momentum*: during a sweep, lineages carrying the beneficial mutation sit
  above the population's mean fitness, so selection against further, mildly harmful
  mutations is weaker for them. The *momentum window* is the period of disequilibrium
  until the sweep completes. Earlier name: the *free-for-all effect* (FFA).
- *Sequential fixation* (SF) vs *clonal interference* (CI): in SF each beneficial
  mutation fixes before the next appears. In CI several compete at once.
- *Evolvability-enhancing (EE) mutation*: one that raises the long-term fitness a
  population reaches, measured by replicates (Sanson & Ferguson 2025).
- *NK landscape*: a bit-string fitness landscape whose ruggedness rises with K.

---

## 1. Kelley et al. 2026, "Endosymbiotic mutualism can constrain host diversity and evolved complexity"

Kelley, Hillary, Hillman-Emelianoff, Khalili, Zhang, Johnson, Dolson, Vostinar &
Lalejini. ALIFE 2026, https://doi.org/10.1162/isal.a.1024. Read in full from
EcoEvoRxiv (https://doi.org/10.32942/x2hq1w, PDF version 25539). Code:
https://github.com/amlalejini/2026-alife-mutualism-constrains-evolution.

**System** (paper, Methods). Symbulation, SGP mode. Well-mixed world with "a maximum
carrying capacity of 10,000 hosts", at most one endosymbiont per host, and
"endosymbionts could not survive outside of a host". Genome "fixed at 100
instructions". "On an update, each organism gains 16 'CPU cycles'". Mutation: "4%
per-instruction and per-argument substitution rates and a 0.5% per-bit tag mutation
rate". Hosts and symbionts gain resources by performing Logic-9 tasks. "To engage in
symbiosis, a host and its symbiont must have performed a matching logic function",
and organisms may perform one task type per lifetime. "Parasitic symbionts steal a
portion of their host's CPU cycles", modelled on Zaman et al. 2014. The cycles the
parasite receives are the stolen cycles times a "synergy factor".

**Experiment 1** (replication of Zaman 2014). Three treatments (parasite, mutualist,
no symbiont), "running 50 replicates of each". "Parasites stole 75% of their host's
CPU cycles", with synergy factor 4. All tasks give one resource. Reproduction costs
one resource. Minimum lifespans are "100 CPU cycles for hosts and 10 CPU cycles for
symbionts". The authors added these minimums because without them hosts evolved
"flow control that bypassed executing most of their genome". Result: "we observed
the evolution of EQU (the most complex function) in 16 of 50 replicates with
host-parasite coevolution", while the mutualist and no-symbiont hosts never evolved
beyond NOT.

Generations elapsed for hosts: 28,125 with mutualists, 8,621 with parasites and
11,600 with no symbiont. The spread figures are 121, 850 and 83.4; the symbols naming
the two statistics are lost in the PDF text layer. Parasite-treatment hosts "evolved
more complex functions with far fewer generations".

**Experiment 2** (graded rewards). Rewards are 1, 2, 4, 8 and 16 resources by task
complexity. "Host reproduction costs 256 resources and symbiont horizontal
transmission costs 128 resources". "We observed symbiont population extinctions in 36
of 50 host-parasite replicates ... Parasite extinctions occurred when hosts escaped
infection vulnerability by evolving a more complex function. Because performing more
complex functions conferred more resources ..., newly immune hosts could rapidly
out-compete the still-vulnerable host subpopulation". Seven parasite replicates
reached EQU.

In "48 of 50 replicates of the mutualist condition, mutualists fully constrained" host
complexity. Disengaged mutualists became "vestigial organelle[s]" that "rapidly lost
the ability to perform their original logic function". Removing the mutualists at
25%, 50% or 75% of the run released the hosts at once (Fig. 2C).

**Sweeps.** The paper also sweeps function reward (×0.5 to ×16), mutualist donation
proportion and synergy factor (0.5–8), and function restriction, at 50 replicates
each. The donation proportion is introduced as "five" values but six are listed:
12.5%, 25%, 50%, 75%, 87.5% and 100%. Statistics: Wilcoxon rank-sum and
Kruskal–Wallis tests with Bonferroni correction, and bootstrapped 99% CIs.

**Run length and world, from the code.** `experiments/2025-11-24-health-flat-rewards/hpc/gen-slurm.py`
and `2025-11-25-health-diff-rewards/hpc/gen-slurm.py` set `UPDATES 200000`,
`GRID_X 100`, `GRID_Y 100`, `GRID 0` (well-mixed), `CYCLES_PER_UPDATE 16` and
`PARASITE_CYCLE_LOSS_PROP 0.75`. They also set `HOST_REPRO_RES 1` with
`HOST_MIN_CYCLES_BEFORE_REPRO 100` (flat rewards), and `HOST_REPRO_RES 256` with
`SYM_HORIZ_TRANS_RES 128` (graded rewards). The matching `lalejini-run-gen-slurm.sh`
files set `REPLICATES=50`. The flat-reward job script sweeps the
donate/steal multiplier over 1, 2, 4 and 8; the paper reports the ×4 condition. Fig.
2's x-axes run to 200,000 updates.

**Citation slip.** The paper's supplement reference "10.5281/zenodo.16795778"
resolves to `amlalejini/alife-2025-env-conn`, the Gordon et al. 2025 archive
(https://zenodo.org/api/records/16795778). The repository README gives
10.5281/zenodo.19120615 for this paper.

**Exploratory nutrient mode.** The repository also contains exploratory "nutrient"
experiments (`2025-11-13-nutrient-maxlife-fixedtime`, `2025-11-18-nutrient-sym-spread`).
They are not in the README's list of experiments that appear in the manuscript
(`experiments/manuscript-analyses/README.md`).

**For evo.**

- (inference) Resistance here is task switching. Every new task a host evolves is a
  complete escape from parasites matched to the old one. In Experiment 2 the new task
  also pays on its own. The defence is therefore paid at every step, the opposite of
  E009's shape.
- The parasite's cost is a rate: 75% of cycles. A host never runs out of anything,
  because execution is free and the only store is the reproduction threshold.
- The scale bar for this group is 50 replicates × 200,000 updates × 10,000 hosts.

## 2. Johnson et al. 2026, "Saved by the Symbiont"

Johnson, Mendoza, Tucker, Lalejini, Vostinar & Dolson. ALIFE 2026,
https://doi.org/10.1162/isal.a.1025. Read in full from EcoEvoRxiv
(https://doi.org/10.32942/x20h3x). Code: Zenodo record
https://doi.org/10.5281/zenodo.19477499 (a GitHub release of
`john-k-903849031/ALIFE2026-StressSymbiosis` v1.0.0). Its submodule pins Symbulation
fork `K-Johnson-Horrigan/SymbulationEmp` at commit `b344a748` (each
`data/*/README.md`).

**System** (paper). Symbulation SGP mode. Well-mixed, "maximum carrying capacity of
10,000 hosts", one symbiont per host. Genomes "fixed at 100 instructions".
"Per-instruction and per-argument substitution rates were set to ≈ 0.0396 ... (the
precise per-bit mutation rate was set to 0.00495)". "Each timestep, organisms received
16 CPU cycles". Organisms are limited "to performing one type of task during their
lifetime" and interact by "task matching". An incoming symbiont can oust a resident
"only if the invading symbiont matched tasks with the host and the preexisting
symbiont did not".

**Stress events.** Stress hits every 25 or 200 timesteps, "for a total of 4,000 and
500 stress events", which implies 100,000 timesteps. Figures 1 and 3 say "over the
100,000 timesteps of the experiment".

- *Mutualism experiment.* Base death chance at a stress event is 0, 50% or 100%. A
  task-matching mutualist confers "full immunity". Hosts need 100 resources to
  reproduce. Symbionts need 0 to transmit vertically and 50 to transmit horizontally.
  Rewards are 1–16 by complexity (Table 1).
- *Parasitism experiment.* A task-matched parasite sets the host's death chance at a
  stress event to 0, 50% or 100% (otherwise 0%). "A parasite that caused the death of
  its host during a stress event reproduced horizontally 8 times for no resource cost".
  Parasites are never transmitted vertically. "Hosts required 10 resources to
  reproduce, and parasites required 5", with minimums of "400 and 25 CPU cycles before
  they could reproduce". "All completed tasks were rewarded with 5 resources", so
  nothing but parasite escape rewards complexity.
- *Controls.* No-symbiont controls, and bottleneck controls that remove random hosts
  to "match the experimental host population count at each stress event". Statistics:
  Fisher's exact test with Bonferroni correction.

**Replicates.** The text never states a replicate count. Figures 2 and 4 show
per-replicate panels numbered up to 30. From the code:
`data/parasitism_experiment/run_exp.sb` runs `--array=0-179` over 3 death chances × 2
stress frequencies, and `squish.py` loops `for b in range(0,30)`. That gives **30
replicates per condition**. The mutualism scripts run 90 array jobs × 2 frequencies =
180 runs, also 30 per condition. `SymSettings.cfg` sets `UPDATES 100001`,
`GRID_X 100`, `GRID_Y 100`, `CYCLES_PER_UPDATE 16`.

**Results.**

- Mutualists constrained host complexity when stress was frequent and at least mild,
  or infrequent and intense (p < 0.05, Fisher's exact test, corrected). Without
  mutualists, hosts "rapidly go extinct" (supplement Figure S1).
- Parasites promoted complexity. Hosts "evolve complex tasks (EQU, XOR, NOR)
  significantly more frequently" at stress frequency 25 with parasite death chance
  50% and 100% (p < 0.001). Against the bottleneck control, random killing never gave
  NOR, XOR or EQU in any replicate.

**How resistance is encoded and lost.** Resistance is performing a task the parasite
lacks. The code checks for any shared task bit (`SGPWorld::TaskMatchCheck` in
`source/sgp_mode/SGPWorldSetup.cc`). The death rule is in `StressHost::GetDeathChance`
(`source/sgp_mode/StressHost.h`).

Loss is reported qualitatively, per replicate:

- "In replicate 10, hosts evolve XOR early, and experience a lower kill rate. However,
  hosts start to lose XOR several times, which are accompanied by spikes in proportion
  of hosts killed and then a return of XORs completed. This cycle occurs several
  times."
- In replicate 23 the hosts gain XOR and "the parasites ... fall back to easier tasks
  and 'give up' on tracking (and killing) hosts".
- The abstract's summary: "Hosts cycle between complex, parasite-resistant and simpler,
  parasite-vulnerable states over time."

No rate of loss, no time to loss, and no lineage is reported.

**Loss counters in the code.** The archive's `squish.py` writes per-task columns
`lineage_gained_count_*`, `lineage_lost_count_*`, `toward_partner_count_*` and
`from_partner_count_*`. In the pinned Symbulation they are incremented in
`SGPHost::Reproduce` only `if (sgp_config->TRACK_PARENT_TASKS())`
(`source/sgp_mode/SGPHost.cc`), and they start at zero (`source/sgp_mode/CPUState.h`).
Both experiment configs set `TRACK_PARENT_TASKS 0`. (inference) The loss counters were
written to disk but would not have counted anything in these runs. The output files
were not checked.

**What a parasite takes.** In this stress mode (`INTERACTION_MECHANISM 2`) the parasite
takes nothing per update; its whole cost is the death lottery at stress events. The
host's points are a reproduction threshold, and execution is free.

**For evo.**

- This is the closest published analogue to E008's "invisible or fatal" cost: an
  entered host either dies or pays nothing.
- (inference) Even so, defence (task escape) evolved, for two reasons. The kill is a
  per-event probability, so expected fitness is graded by the death chance. And the
  escape needs only one task change, which pays at once.
- The scale bar is 30 replicates × 100,000 updates × 10,000 hosts, with a matched
  bottleneck control.

## 3. Johnson, Croft, Vostinar, Lalejini & Dolson 2025, "Keep Your Friends Close and Your Enemies Distant: Partner Choice Can Enable Parasite Exclusion in Endosymbiotic Coevolution"

ALIFE 2025, https://doi.org/10.1162/isal.a.885. Paper text **not reached**: OpenAlex
and Semantic Scholar list only the MIT Press PDF, and no preprint was found. Read
instead: the abstract (Crossref), the experiment repository
https://github.com/john-k-903849031/ALIFE2025-TagPartnerChoice, the Symbulation commit
it pins (`7f368f6a`, branch `tag-matching` of `K-Johnson-Horrigan/SymbulationEmp`),
and the repository of a journal follow-up,
https://github.com/john-k-903849031/TagPartnerChoice_journal, "Let the Wrong One In:
Partner Choice Evolution Can Select for Endosymbiotic Parasite–Mutualist Coexistence",
with data at OSF https://osf.io/8fcux.

**Abstract (UNVERIFIED beyond it).** Tag matching is implemented "as a mechanism for
partner choice". The authors "measured the levels of endosymbiotic mutualism that
evolved under a range of partner choice selectivity, tag mutation rates, and
endosymbiont vertical transmission rates". The abstract also reports:

- "mutualists and hosts evolving to have more similar tags than parasites and hosts";
- "ranges of partner selectivity and tag mutation rates that enabled the de novo
  evolution of exclusive mutualism (i.e. parasites went completely extinct)".

**Encoding, from the code.** This is Symbulation default mode (`./symbulation_default`
in every job script), so the interaction value is a scalar. Tags are `emp::BitSet<32>`
(`source/default_mode/Host.h`). At each horizontal infection attempt
(`source/default_mode/SymWorld.h`, `SymDoBirth`) the code computes
`tag_distance = hamming(...) * 32` and `cutoff = GetPoisson(TAG_DISTANCE * 32)`, and the
infection fails if `tag_distance > cutoff`. So acceptance is the probability that a
Poisson draw with mean 32 × permissiveness is at least the Hamming distance.
(inference) Every single bit flip changes a parasite's infection probability, so the
defence is graded by construction. Tags are checked only on horizontal infection.
Tags mutate by `FlipRandom` at `TAG_MUTATION_SIZE` per bit.

**Lineage tracking, from the code.** `Host::Reproduce` adds to `towards_partner_count`
and `from_partner_count` the number of tag bits that moved toward or away from the
host's current symbiont's tag (`Host.h`). This is a per-lineage step count of the
defence trait. Whether the paper reports it is unknown.

**Settings, from the code** (`data/tagmut_evolving/SymSettings.cfg` and job scripts).

- World: `UPDATES 100001`, 100 × 100, `RES_DISTRIBUTE 100`, `HOST_REPRO_RES 1000`,
  `SYM_HORIZ_TRANS_RES 500`, `VERTICAL_TRANSMISSION 0.5`, `HOST_INT -0.1`,
  `SYM_INT -0.5`, `MUTATION_SIZE 0.02`.
- Sweep: permissiveness `TAG_DISTANCE` ∈ {0.125, 0.1875, 0.25, 0.3125, 0.375, 0.4375,
  0.5, 0.5625, 0.625}, crossed with tag mutation ∈ {0, 0.0001, 0.0005, 0.001, 0.005,
  0.01, 0.05, 0.1} per bit.
- Replicates: `--array=1001-1240` over 8 mutation values gives 30 seeds per cell.
- The VT sweep (`vt_evolving`) crosses 11 VT values with permissiveness, at 30 seeds
  per cell (`--array=1001-1330`).

**Erratum, quoting the paper.** The repository README (dated 05/06/2026) quotes two
sentences of the paper. One: "Mutualists consistently have less tag mismatch than
parasites; this effect is medium or large in all cells other than permissiveness 0.125
and mutation 0.0001 (δ ≈ 0.1, less than small effect) and permissiveness 0.5625 and
mutation 0.1 (δ ≈ 0.15; small effect)". It then adds more small-effect cells
(permissiveness 0.625 with mutation 0.05, δ ≈ 0.25, and with 0.1, δ ≈ 0.14).

**Journal follow-up supplement** (README of `TagPartnerChoice_journal`; paper text not
found).

- It compares three tag metrics (Symbulation commit `19d7aeaa`, `ConfigSetup.h`,
  `TAG_METRIC`): "hamming [proportion of bits mismatching]", "streak", and "hash
  [arbitrary but consistent difference]".
- Supplementary Figure 3.4 caption: "Tighter host–symbiont correspondence arises when
  partner suitability can be tuned gradually by small-effect mutations (Hamming
  metric), compared to control where mutation randomizes partner choice criteria (Hash
  metric)". The test is a Wilcoxon signed-rank test, p < 0.0001.
- Supplementary Figure 3.1 pools "5,130 total replicates for each metric". Read off
  the bar chart (approximate; `raw_vs_cor_metric_behaviors.pdf`):

  | Outcome | Corrected Hamming | Hash |
  |---|---|---|
  | Exclusive mutualism | about 2,800 | about 2,000 |
  | Exclusive parasitism | about 930 | about 1,480 |
  | Symbiont extinction | about 140 | about 440 |

- Experiments 5 and 6 let host permissiveness itself evolve
  (`HOST_TAG_PERMISSIVENESS_EVOLVES`).

**For evo.** (inference) This is the one place in the cluster where the encoding of a
defence is varied while everything else is held fixed. A graded encoding (Hamming
distance with probabilistic acceptance) gave fewer exclusively parasitic outcomes than
an encoding in which one mutation re-randomises compatibility. It is the nearest
published analogue of E009's proposed 2 × 2 of cost against path length, though the
"path" here is one bit at a time and never neutral.

## 4. Croft, Johnson, Vostinar & Dolson 2024 (mutation size and rate in the origin of mutualism)

ALIFE 2024, https://doi.org/10.1162/isal_a_00790. Crossref and OpenAlex give the title
as "System.Xml.XmlElement". Abstract from OpenAlex
(https://api.openalex.org/works/doi:10.1162/isal_a_00790). Full text **not reached**.
The analysis script is at https://github.com/emilydolson/ALIFE-2024-DeNovoMutualism.

**Abstract (UNVERIFIED beyond it).** Using Symbulation, "increasing mutation size and
mutation rate both promote the evolution of mutualism, as does faster generational
turnover within symbionts". A probabilistic model "suggests that large regions of the
parameter space where mutualism evolves can be explained purely by mutation size and
rate". But "mutualism evolves in a wider region of parameter space than we would
expect under this simple probabilistic model", which the authors attribute to
coevolution, "corroborated by phylogenetic data showing that partners in the first
mutualism are often themselves descended from mutualists".

**What the analysis script does** (`phylo_analysis.Rmd`). It finds "the first
mutualistic partnerships" per seed. It then bins the immediate host and symbiont
ancestors as antagonistic (phylogeny bin ≤ 7), neutral (8–11) or mutualistic (≥ 12).
Mutation sizes 0.005, 0.01, 0.015, 0.05 and 0.1 appear in commented lines.

(inference) This is a one-step look back at the parent's behaviour class, not a path
with intermediate fitnesses.

## 5. Johnson, Dirkswager & Vostinar 2023, ectosymbiosis hastens endosymbiosis (background)

ALIFE 2023, https://doi.org/10.1162/isal_a_00661. No abstract in Crossref, OpenAlex or
Semantic Scholar, and no full text found. The repository
https://github.com/K-Johnson-Horrigan/SGP-Endosymbiosis-Evolution calls it "the
presentation". Its 2023-01-19 run:

- 30 seeds (`simple_repeat.py`, seeds 2001–2030), `UPDATES 60001`, 100 × 100 world;
- host income `RES_DISTRIBUTE 100` per update and `HOST_REPRO_RES 1000`;
- free-living symbionts on, with symbiont horizontal cost swept over 100, 250, 500,
  750 and 1,000, VT over 0–1, and ectosymbiosis and endosymbiosis switched on and off.

Nothing on defence.

## 6. Ferguson & Ofria 2023, "Potentiating Mutations Facilitate the Evolution of Associative Learning in Digital Organisms"

ALIFE 2023, https://doi.org/10.1162/isal_a_00684, read in full (PDF above). Three
pages.

**System.** An early build of Avida 5.0 inside MABE2, on a "60x60 toroidal grid,
resulting in a population cap of 3,600". "Point mutations occur in offspring at a rate
of 0.0075 per instruction, while single-instruction insertion and deletion mutations
occur at a rate of 0.05 per reproduction". Organisms "must execute 1,500 instructions
before the Repro instruction can be activated". The task is a simplified path-following
environment in which associative learning is optimal. Fitness is 1.25^score.

**Scale.** "200 independent replicates for 250,000 updates (about 3600 generations)".
"Only 16 of 200 replicates exhibited associative learning". Exploratory replays were
seeded at every 50th lineage step up to step 1,000. Targeted replays used 50 per step
in the window with the largest potentiation gain.

**Path results.** Four lineages (A–D) were analysed.

- "Each had a single step in the lineage that resulted in a substantial increase in
  potentiation (ranging from 36 to 64 percentage points)".
- "Of those four mutational events, two were neutral, one was deleterious, and one was
  beneficial", and "the number of mutations between the potentiating mutation and the
  appearance of learning varied wildly between lineages, ranging from 8 steps up to 91".
- Lineage A: the potentiating mutation at step 484 "had no immediate effect on
  fitness". It raised two-step mutations conferring learning "from 2 to 9 (of
  approximately 56 million)". Between it and learning, "only steps 516 and 525 caused
  any change in behavior; all other interim mutations occurred in unexecuted regions
  of the genome".
- Lineage C: the largest jump (64 points) came from a deleterious mutation, a "no-operation
  instruction into a conditional flow control instruction".
- Lineage D: the step-548 mutations "caused no discernible change in fitness even
  though they increased potentiation by 50 percentage points". They raised two-step
  learning neighbours "from under 800 to over 100,000".
- Potentiation also fell along successful lineages (A and D). In A, the mutations
  between steps 432 and 484 "dismantled that machinery".

**For evo.** This is the only path-with-replay analysis in the cluster. It concerns a
rewarded behaviour, not a defence.

- (inference) It confirms that single neutral steps can carry most of the potentiation
  and are invisible when they happen, which is the regime E009's argument is about.
- It also shows Avida's supply of such steps: insertions at 0.05 per birth, and
  neutral sites in unexecuted code. E009's self-scan has to be built in executed bytes
  at byte 0, and evo has nothing comparable.
- Escondo & Ferguson 2026 (§10) later show that lineage-traced replays, the method
  used here, overestimate potentiation.

## 7. Ferguson, Ofria & Bohm 2024, "Predicting the Unpredictable: Using replay experiments to disentangle how evolutionary outcomes are altered by adaptive momentum"

ALIFE 2024, https://doi.org/10.1162/isal_a_00801, read in full (PDF above).
Supplement: https://doi.org/10.5281/zenodo.11507982.

**Model.**

- Genome: "each organism's genome consists of a single integer". Score is a repeated
  sawtooth with "G = 1.0, D = 0.05, and w = 6", and fitness is 10^s.
- Valley: "Crossing a valley increases an organism's fitness by a factor of 10, and
  each step into the valley reduces fitness by 12%". With w = 6 a crossing is five
  deleterious steps, then the peak.
- Population: "populations of 512 organisms in a one-dimensional spatial population ...
  that did not wrap". Generations are non-overlapping, with roulette selection among
  self and two neighbours.
- Mutation: "a 0.0125 chance to mutate; mutations either increment or decrement" the
  integer. "Selective sweeps are thus limited to advancing one position in the
  population per generation".

**Experiment I** (validation).

- Setup: "500,000 evolutionary replicates ... 512 organisms at p1 and ran for 5,000
  generations". The results paragraph instead says the runs started "from a full
  population of p2"; the paper is inconsistent here.
- First crossing: "6,485 crossed the first valley within 5,000 generations (≈1.3%)",
  mean 2,569 generations, median 2,602.
- Second crossing: "we would expect roughly 84 replicates to cross twice ... but
  instead we see 902 replicates (≈0.18%)". The second crossing came a mean 579 and
  median 401 generations after the first.
- Late second crossings: when they occur "more than 1000 generations after a first
  crossing", the rate (≈1.23%) is similar to the first.

**Experiments II–III** (replays).

- Benchmark: a sweep of p2 organisms across p1, with an 8-organism leading edge placed
  0–5 steps into the next valley. "Each point represents 10,000 replicates."
- From the start of a sweep (500 replicates): 4 crossed two valleys (0.8%), 83 one
  (16.6%) and 413 none (82.6%). Replays: 1,000 at every fourth generation for 24 runs,
  and 10,000 per generation for three.
- Equilibrium runs: of 10,000 that started at equilibrium, 1 crossed twice, 19 once
  and 9,980 not at all. "While the potential in an adaptive momentum window starts at
  17%, the potential for replicates outside momentum windows starts at 0.2%."
- Leading edge: during a momentum window "every mutation in the leading edge is either
  potentiating or anti-potentiating". At equilibrium, "early mutations into the valley,
  although required for a valley crossing, have no substantial impact on the
  population's probability of crossing".
- Shuffling the population (destroying the leading edge) removed most of the
  potential. Only leading edges at p2 + 5 kept "greater than a 10% chance to cross"
  once the sweep had passed half the population.

**For evo.** The sawtooth with w = 6 has five harmful intermediates and then a large
payoff. That is E009's shape with deleterious rather than neutral steps, and the
answer to Q3 below uses it.

## 8. Ragusa & Bohm 2023, "The Role of Disequilibrium in Evolutionary Discovery", and its full version, Bohm, Ragusa, Ofria, Lenski & Adami 2024

**Ragusa & Bohm 2023.** ALIFE 2023, https://doi.org/10.1162/isal_a_00660. Abstract
only (OpenAlex), **UNVERIFIED** beyond it. During "genetic sweeps and range expansions,
the driving lineages have an increased competitiveness or experience an absence of
competition, which results in a higher tolerance of deleterious mutations". They name
this the "Free-for-All" effect, and "This document summarizes work that we are
preparing for publication."

**The full study.** "Reduced selection during sweeps lead to adaptive momentum on
rugged landscapes", bioRxiv https://doi.org/10.1101/2024.04.08.588357, posted
2024-04-11, version 1, not peer reviewed per the bioRxiv API. Read in full (37 pages).
Its acknowledgements thank colleagues "for contributions to an earlier version of this
study that referred to the 'Free-for-All Effect'", which ties it to the 2023 abstract.

**Conditions.**

- Landscape: valley width Vw, benefit per peak Sb and cost per valley step Sd.
- "Three-peaks": "Vw = 6, Sb = 0.5, and Sd = 0.03. The population size is N = 2,400 and
  the mutation rate is μ = 0.0025 per individual per generation, which produces an
  average of 6 new mutations per generation". Populations sit on "a one-dimensional
  ring". Each condition was "tested ... 1000 times", for 20,000 generations (Fig. 2).
- "Each newly produced offspring can gain only a single mutation".

**Results.**

- Three peaks: "only 35.1% of the populations in the fixed-start condition crossed the
  fitness valley to reach peak 3, whereas in the mixed-start condition 61.8% reached
  peak 3". Fixed start is all 2,400 on peak 2 (equilibrium). Mixed start is 2,395 on
  peak 1 and 5 on peak 2 (a sweep just begun). Extended Data Fig. 1 repeats this for N
  = 400 to 12,800 and Sd = 0.024, 0.03 and 0.036.
- "Infinite peaks" (N = 100 to 153,600; 56 replicates × 12 h for Tobs and Tst, 11 × 12
  h for Tnd and Tfix):
  - Tst is the stochastic tunnelling time from equilibrium.
  - Tnd is "the same approach ... except we set Sd = 0.0. Thus, Tnd tests the discovery
    time in the absence of purifying selection".
  - Tobs is the observed crossing time and Tfix the fixation time.
  - At small N (N = 200) "Tobs tracks Tst" (sequential fixation). At very large N
    (76,800) clonal interference dominates. In between (N = 2,400) is a "balanced"
    regime where "Tobs is substantially shorter than the expected crossing time by
    stochastic tunneling", with a bimodal Tobs distribution.
- Well-mixed populations: the effect "also occurs in well-mixed populations, although
  the effect is more subtle and requires larger population sizes". The ring "maximizes
  the fixation time of beneficial mutations, and thus it also maximizes the potential
  for adaptive cascades".
- Neutral landscapes: "If a fitness landscape is mostly neutral or contains many
  beneficial mutations, the increased exploration from adaptive momentum may not
  improve adaptation, since adaptation does not require crossing valleys."
- Fig. 4: N = 4,800 on a strip over 31,000 generations shows "a cascade with six
  sequential crossings".

## 9. Sanson & Ferguson 2025, "A computational baseline for changes in long-term evolvability"

ALIFE 2025, https://doi.org/10.1162/isal.a.895, read in full (PDF above).

**Setup.** NK landscapes, well-mixed, roulette selection. "Unless otherwise stated,
populations contained 1,000 organisms and organisms had a mutation rate of 0.1% per
bit. All replicates evolved for 1,000 generations", with 100 replicates per founding
genotype. Experiment 2 varies mutation rate (0.01%–1% per bit) and population size
(10–10,000).

**Results.**

- *Neutral region* (Landscape 3): "populations founded in the middle of the neutral
  region often failed to reach either optimum in the allotted 1,000 generations".
  Neutral mutations toward the global optimum increased evolvability.
- *Valley* (Landscape 4): "each step into the valley is a 5% reduction in fitness" and
  the global optimum is +46%. "Populations founded before or one step into the fitness
  valley ... never crossed the valley. Populations founded two steps into the valley
  crossed in 43 of 100 replicates, and populations founded three steps into the valley
  always crossed."
- *Population size and mutation rate*: "as we increase population size or mutation
  rate, populations are able to cross the valley from earlier steps".
- *Random NK landscapes* (N = 6): the fraction of EE mutations that were beneficial
  "varied by landscape in [22.8%, 59.2%]". The authors conclude that "many, if not
  most, mutations that increase evolvability are deleterious".

**For evo.** (inference) A neutral plateau of a few steps already stalls a 1,000-organism
population at 0.1% per bit for 1,000 generations, even with a far larger mutational
target per step than a specific byte in evo. This supports E009's reading.

## 10. Escondo & Ferguson 2026, "Summarizing Populations: Characterizing the Effects of Sampling in Computational Evolutionary Replay Experiments"

ALIFE 2026, https://doi.org/10.1162/isal.a.1014, read in full (proceedings PDF above).
Code: https://github.com/FergusonAJ/replay_methods.

**Setup.** NK landscapes with N = 20 and K = 9. Populations are "well-mixed and consist
of 1,000 organisms", with "a mutation rate of 1% per bit", tournament size 7, and 100
generations. 100 landscapes × 100 replicates were run. Replays were seeded from the
first 25 generations: 100 per generation per method, giving "176,332,500 total replay
replicates".

**Results.** "Dominant genotype replays consistently result in lower potentiation
values than population snapshots (Wilcoxon, adjusted p < 1e-145)", and "lineage
tracing replays consistently result in higher potentiation values than snapshot
replays (Wilcoxon, adjusted p < 1e-166)". Random sampling at 10%, 5% and 1%
underestimates on average, with variance rising as the sample shrinks. The authors
note that lineage-traced Avida studies (Yedid 2008, Ferguson & Ofria 2023) "likely
overestimat[e] potentiation".

**For evo.** If evo runs a Lenski-style line-of-descent analysis with replays, it
should seed replays from full snapshots of the ring (evo can save them), not clones of
the dominant genome or of line-of-descent ancestors.

## 11. Gordon, Ferguson, Dolson & Lalejini 2025, "Environmental connectivity influences long-term evolutionary outcomes"

ALIFE 2025, https://doi.org/10.1162/isal.a.863, read in full (PDF above).

**Setup.** Two systems, both with population and world size 3,600 and "50 independent
replicates of each treatment".

- *Graph model.* An evolutionary-graph-theory model with "a 1.25% chance the offspring
  mutates to a random, mutationally adjacent genotype". Its valley landscape: "a
  lineage must accumulate four deleterious (each a 5% fitness penalty) and then one
  beneficial mutation. Each fitness peak corresponds to a 50% fitness benefit". There
  are 100 repeated valleys over 100,000 generations.
- *Avida.* 400,000 updates "(48,000 generations under well-mixed conditions)". The
  copy error rate is "0.25% per instruction copied", and insertions and deletions
  occur "at a per-division probability of 5%". Merit is fixed-rate expression, and
  "older organisms that have performed fewer logic functions are preferentially
  replaced".

**Results.**

- Valley landscape: "all populations evolved on the chain and cycle graphs crossed all
  100 fitness valleys". Among lattices, "1x3600 and 2x1800 regimes crossed all 100
  fitness valleys". The authors tie this to adaptive momentum and to the fact that
  "in a linear chain, offspring of a lineage originating on one end of the chain would
  not compete with descendants ... from the opposite end of the chain for at least
  1,800 generations".
- Avida: the cycle graph was not distinguishable from well-mixed in number of
  functions. Among lattices, "1x3600 populations evolved to perform the least number
  of functions" (p < 0.003). "The wheel, linear-chain, and cycle structures evolved
  the shortest genome lengths, and had the fastest replication times".

**For evo.** evo's world is a 1D ring with local placement.

- (inference) In the simple model that is the geometry that crosses a
  four-harmful-steps-then-payoff valley most reliably.
- (inference) In Avida the same geometry favoured short, fast replicators over
  function. Both effects are confounded with ecology in evo's E-series and need a
  same-physics control.

## 12. Shea, Leither, Foreback, Dolson & Lalejini 2024, "Environmental connectivity influences the origination of adaptive processes"

ALIFE 2024, https://doi.org/10.1162/isal_a_00749, read (skimmed) from EcoEvoRxiv
https://doi.org/10.32942/x25g7n. An artificial ecology of autocatalytic cycles on 100
sites under ten connectivity patterns (including cycle and linear chain), with 20,000
steps plus 10,000 stabilisation steps and "20 independent replicates of each
connectivity regime". Every structure "amplified the emergence of adaptive dynamics for
at least one community type and suppressed" it for another. No organisms, no energy,
no defence. Peripheral for evo.

## 13. One line each (abstracts, **UNVERIFIED**)

- **Leither, Foreback, Baum & Dolson 2023** (https://doi.org/10.1162/isal_a_00686,
  OpenAlex): "transitionability" of ecological interaction networks toward egalitarian
  major transitions; "interaction strengths (i.e. edge weights) have a substantial
  impact on transitionability".
- **Foreback, Leither, Baum & Dolson 2023** (https://doi.org/10.1162/isal_a_00692,
  OpenAlex): a maximally simple artificial ecology shows "evidence of community-level
  selection". The promoting parameter regions "vary based on species interactions".
- **Chaturvedi, El-Gazzar & van Gerven 2026** (https://doi.org/10.1162/isal.a.980,
  Crossref; arXiv copy 2604.00810 exists, not read): multi-level selection with a
  shared substrate and mutation operator. A positive-sum intake channel and a zero-sum
  redistribution channel "both remain occupied", and "zero-sum channel usage increases
  over generations".
- **Bielawski, Gaylinn & Bongard 2025** (https://doi.org/10.1162/isal.a.836, Crossref):
  for functionally equivalent hierarchical neural CAs joined by a neutral genotype
  network, an intervention found for one instance seeds an efficient search for the
  others.
- **Gaylinn, Rees, Cheney & Bongard 2025** (https://doi.org/10.1162/isal.a.893,
  Crossref): spatial "local viability thresholds" with "ramps" of difficulty and
  "ratchet" effects induce selection pressure, and evolved environments beat
  hand-designed ones.

---

## 14. Answers to the questions

### Q2. Does any paper describe the mutational path to a defence, with intermediates and their cost or fitness?

**No.** None traces a path to a defence with the fitness of each intermediate.

- Kelley 2026 and Johnson 2026 report presence and parameter region:
  - counts of replicates whose hosts reach complex tasks;
  - parasite extinction in 36 of 50 runs (Kelley);
  - per-replicate time series of hosts gaining, losing and regaining XOR as kill rates
    rise and fall (Johnson, replicate 10).
- Johnson 2025's code counts tag bit flips toward and away from each host's partner
  per lineage, but the paper text was not reached. Its journal follow-up compares
  encodings (graded Hamming against randomising Hash) rather than paths.
- Croft 2024 (abstract and script) looks one step back, at the behaviour class of the
  first mutualist pair's parents, and its abstract credits large-effect mutations and
  "partners ... descended from mutualists".
- The only path-with-replay analysis in the cluster is Ferguson & Ofria 2023, for
  associative learning. Its single largest potentiating steps were twice neutral, once
  harmful and once beneficial, with learning 8–91 steps later.

(inference) Structurally, the defences in this line are built so that every step pays:

- *Task matching*: any new task escapes a parasite matched to the old one.
- *Tag matching*: one bit flip changes the infection probability through the Poisson
  cutoff.
- *Scalar defence*: a continuous fraction of income.

None has E009's shape (several neutral steps, then a payoff), so these systems neither
test nor refute E009's argument; they are designed around it. Where an "all-or-nothing"
host cost exists (Johnson 2026's death at stress events), it is a probability per
event, so expected fitness is still graded by the death chance.

### Q3. Do adaptive momentum, the free-for-all effect or potentiating mutations give E009's four-neutral-insertions argument a mechanism, or a counterargument?

**Mostly a counterargument for the neutral case, and a mechanism for a mildly harmful
one.**

**What the conditions were.** Adaptive momentum (Bohm et al. 2024, the full form of
Ragusa & Bohm 2023's free-for-all effect) and Ferguson, Ofria & Bohm 2024 show a
weakening of selection *against harmful* intermediates during a sweep. All their
evidence is for valleys of deleterious steps, under these conditions:

| | Bohm et al. 2024 | Ferguson et al. 2024 |
|---|---|---|
| Valley | width 6, Sd = 0.03 per step, peak benefit 0.5 | width 6 (five steps of about 12%), peak 10× |
| Space | 1D ring | 1D line of 512 that does not wrap |
| Mutation | 0.0025 per individual per generation, at most one per offspring | 0.0125 per offspring, ±1 |
| Population | N = 2,400 (three peaks); balanced regime at about N = 2,400, absent as a distinct effect at N = 200 | N = 512 |
| Sweep length | | at least the population length in generations, since a front advances at most one position per generation |
| Effect | crossings 61.8% vs 35.1% from a fresh sweep vs equilibrium | second crossings 902 vs about 84 expected within 5,000 generations of a first, mean 579 generations later; crossing potential 17% vs 0.2% at window start |

**Counterargument.** E009's intermediates were chosen to be neutral: the path audit
required each to make within 10% of the ancestor's children alone. Bohm et al. define
the neutral-valley time Tnd as the case with "no purifying selection" (Sd = 0), which
is the limit momentum works toward. They also state that on "mostly neutral"
landscapes momentum "may not improve adaptation". (inference) For a truly neutral path
there is no selection for momentum to relax. The limit is mutational supply, which
momentum does not change.

**Supply comparison.** (inference)

- In these models every step is a large mutational target: half of all mutations at
  0.0125 per offspring (Ferguson), or 1.25% per birth to an adjacent genotype (Gordon).
- In Avida the neutral steps sit in unexecuted code, with insertions at 0.05 per birth
  (Ferguson & Ofria 2023).
- In evo each self-scan step is a specific byte value at a specific executed position.
  At PLAN §5.7's reference p ≈ 8 × 10^-3 per byte written, that is of order 10^-5 per
  birth: two to three orders of magnitude less supply per step.
- Sanson & Ferguson 2025 found that even a large-target neutral plateau stalls 1,000
  organisms at 0.1% per bit for 1,000 generations.

E009's conclusion stands.

**Mechanism.** (inference) The same papers say what would make a self-scan reachable
in evo:

- intermediates that are slightly harmful rather than neutral, for example extra
  executed bytes;
- arising during a sweep, such as E007's absorb-phase sweep;
- on a ring, which is the geometry that maximises momentum windows. Gordon 2025's 1D
  cycle crossed every four-harmful-step valley.

evo's population of about 1,000 lies between Ferguson's 512 and Bohm's balanced 2,400.

**Potentiating mutations** (Ferguson & Ofria 2023) are evidence that neutral steps
carry most of the potentiation and are invisible when they occur. That is consistent
with E009's framing, not a way around it.

**Method.** To measure any of this in evo, seed replays from full ring snapshots
(Escondo & Ferguson 2026). Lineage-traced replays overestimate potentiation.

### Q5. Scale bar

| Paper | Replicates per condition | Length | Population / world |
|---|---|---|---|
| Kelley 2026 | 50 (text; `REPLICATES=50` in code) | 200,000 updates (code; Fig. 2 axes) | 10,000 hosts, well-mixed (text; 100 × 100 in code) |
| Johnson 2026 | 30 (code; not stated in text) | 100,000 timesteps (text) | 10,000 hosts, well-mixed |
| Johnson 2025 | 30 per cell over a 9 × 8 grid and a 9 × 11 grid (code) | 100,001 updates (code) | 10,000 hosts (code) |
| Journal follow-up | 5,130 per metric, pooled (README) | | |
| Johnson 2023 | 30 (code) | 60,001 updates (code) | 10,000 (code) |
| Ferguson & Ofria 2023 | 200 runs; 50 replays per lineage step | 250,000 updates, about 3,600 generations | 3,600 (Avida) |
| Ferguson et al. 2024 | 500,000; 500; 10,000; replays 1,000–10,000 per time point | 5,000 generations | 512 |
| Bohm et al. 2024 | 1,000 per start condition | 20,000 generations | N = 2,400 |
| Gordon 2025 | 50 | 100,000 generations / 400,000 updates | 3,600 |
| Sanson 2025 | 100 per genotype | 1,000 generations | 1,000 |
| Escondo 2026 | 100 per landscape × 100 landscapes | 100 generations | 1,000 |
| Shea 2024 | 20 | 30,000 steps | 100 sites |

**Statistics** used by this group: Wilcoxon, Kruskal–Wallis and Fisher's exact tests
on counts of replicates, with Bonferroni or Holm correction. Johnson 2026 adds a
matched bottleneck control.

(inference) For an E-series result to be taken seriously by this group it needs 30–50
seeds per arm, at least 10^5 updates, and a control that matches mortality. evo's 10
seeds per arm is a third to a fifth of the norm. Its population (about 950 organisms)
is a tenth of Symbulation's, though comparable to Sanson, Escondo and Ferguson 2024.

### Q6. Store depth, what a parasite takes, how resistance is encoded, and whether loss is tracked

**Execution is free.** In every Symbulation and Avida variant here, a host's store is
a reproduction threshold, not a survival reserve. Nothing a parasite does can starve a
host. What it takes:

- *Kelley 2026 (SGP mode, cycle theft).* "Parasites stole 75% of their host's CPU
  cycles" each update. (inference) A host's 100-instruction pass then takes 25 updates
  instead of 6.25, and its 100-cycle minimum before reproducing likewise.
- *Johnson 2025 and 2023 (default mode, income theft).*
  - Income is 100 per update and reproduction costs 1,000, so 10 updates of income per
    offspring.
  - A host with negative value h first spends |h| of the update's income on defence
    (`Host::DistribResToSym`). A symbiont with s < h then takes (h − s) of the rest
    (`Host::StealResources`), so theft comes from income, never from stored points.
  - (inference) At the starting values (h = −0.1, s = −0.5) the host keeps 54 of 100
    per update, against 90 when uninfected.
- *Johnson 2026 (stress mode).* No per-update take at all. A matched parasite sets the
  death chance at stress events (every 25 or 200 updates) to 0.5 or 1. Reproduction
  needs 10 resources (two tasks at 5) and 400 cycles. (inference) That is 25 updates,
  or four passes of a 100-instruction genome, so a host meets about one stress event
  per generation at frequency 25.
- *Symbulation's nutrient mode* (at Johnson 2026's commit `b344a748`,
  `SGPSymbiont::DoTaskInteraction`) is the one store-based theft: a parasite takes
  `min(host points, NUTRIENT_DONATE_STEAL_PROP × score)` from the host's points. It is
  capped at what the host holds and only delays reproduction. No paper in the cluster
  uses it; Kelley's repository has exploratory nutrient runs that are not in the
  manuscript.

**Resistance encoding:**

- task matching, one task per lifetime, any shared task bit (Kelley, Johnson 2026);
- 32-bit tags with Hamming distance and a Poisson cutoff, Hamming against Hash in the
  follow-up (Johnson 2025);
- a scalar defence fraction (default mode, as in Vostinar & Ofria 2019).

**Loss over time:**

- Johnson 2026 describes it per replicate: XOR is lost and regained several times,
  with kill-rate spikes. No rate is given.
- Kelley 2026 reports that unused traits go fast: disengaged mutualists "rapidly lost"
  their task.
- The SGP code has per-lineage task gain and loss counters, but they were disabled
  (`TRACK_PARENT_TASKS 0`) in Johnson 2026's runs.
- (inference) Nobody here measures a defence-loss rate in a form comparable to E010's
  "last generation above 1%".

## 15. What this suggests for the store-depth experiment (inference throughout)

1. **The literature's working condition is that an entered host keeps reproducing,
   more slowly; depth in passes is secondary.** In every system here where resistance
   evolved, the parasite cost slows reproduction (cycles or income) or kills with a
   probability per event; it never drains a reserve the host needs to keep running.
   The store-depth sweep should include that limit as an arm: a charge that can
   only reduce what the host banks toward its next child and cannot kill.
   - Its gate could be framed as "an entered host still completes a child, at a
     measured fraction of the uninfected rate".
   - An arm in which the owner-side charge is a per-entry death probability (Johnson
     2026's form) would test whether a lottery grades fitness where a deterministic
     drain did not.
2. **Add a mortality-matched control.** Johnson 2026's bottleneck control kills random
   hosts at the treatment's rate. In evo that means killing random unentered hosts at
   the entered-host death rate, so selection by intruders is separated from extra
   deaths.
3. **Pair depth with path length.** Every evolved defence in this line is graded at
   each step. E009b's one-byte candidate (the divide-endowment starver, one byte from
   the ancestor; E009b "What would change it") belongs in the store-depth experiment as the second factor of
   a 2 × 2 (depth × one-byte vs five-byte defence). [Corrected 2026-10-12 in
   integration: the first draft called this "a one-byte self-check op"; E009 adds no
   op.] Johnson's journal
   follow-up (Hamming against Hash) is the published precedent for varying the encoding
   of a defence.
4. **Seeds.** 30 per arm to meet this group's norm (Kelley 50, Johnson 30). evo's
   current 10 is below it.
5. **Measure loss directly.** Log per-lineage gain and loss of the defence prefix at
   birth (Johnson's counters, switched on), and report time-to-loss.
6. **Replays.** For any potentiation analysis, seed replays from full ring snapshots;
   lineage tracing overestimates.
7. **Ring effects.** On a 1D ring, expect both longer momentum windows (good for
   mildly harmful intermediates) and a bias toward short fast replicators (Gordon
   2025's 1 × 3600 Avida result). Read any change in body length against that.

## 16. Searches that found nothing

- arXiv export API, title phrase search, for Johnson 2025, Croft 2024, Ferguson 2024,
  Ferguson & Ofria 2023, Ragusa & Bohm 2023, Sanson 2025, Gordon 2025 and Johnson 2023:
  no entries.
- Semantic Scholar `openAccessPdf` by DOI: only MIT Press links. Ferguson & Ofria 2023
  is marked "CLOSED". Semantic Scholar's title search returned HTTP 429 each time.
- OpenAlex `locations` and title search for isal.a.885, isal_a_00790, isal_a_00660 and
  isal_a_00661: MIT Press only, no preprint. OpenAlex had no abstract for isal_a_00684
  or isal_a_00661, and Crossref no abstract for any 2023/2024 paper here.
- GitHub repository search for "partner choice endosymbiont", "parasite exclusion tag",
  "mutation size mutualism", "ectosymbiosis endosymbiosis" and "disequilibrium
  evolutionary discovery": nothing. "free-for-all effect": unrelated hits only.
- Lab pages:
  - lalejini.com/publications: PDFs only up to 2022.
  - anyaevostinar.github.io/Research: links to code, no PDFs of these papers.
  - dolsonlab.github.io: no publication list.
  - emilydolson.github.io: 404. emilyldolson.com: no response. ecodelab.com/publications: 404.
  - austinjferguson.com and cliffbohm.com: no response.
- OSF node 8fcux (journal follow-up): data archives only, no manuscript.
- `docs/downloaded-papers/` was checked at the start and again at the end. None of this
  cluster's papers had been added by hand. The files that appeared during the session
  belong to cluster 5.

## Not reached

- **Johnson, Croft, Vostinar, Lalejini & Dolson 2025** (isal.a.885): full text. Only
  the abstract, code, and two sentences quoted in the authors' erratum were read.
  Download by hand.
- **Croft, Johnson, Vostinar & Dolson 2024** (isal_a_00790): full text. Download by
  hand.
- **Johnson, Dirkswager & Vostinar 2023** (isal_a_00661): text and abstract. Download
  by hand if needed; background only.
- **Ragusa & Bohm 2023** (isal_a_00660): the two-page extended abstract itself. Its
  content is superseded by the bioRxiv full study read here; optional.
- The journal paper "Let the Wrong One In" (Johnson et al., in preparation or under
  review; venue unknown): only its supplement README and figures were read.
- Chaturvedi et al. 2026: an arXiv copy (2604.00810) exists but was not read, being a
  one-liner.
- Johnson 2026's output data, to check whether the loss counters are all zero: not
  downloaded.
