# Historic artificial-life systems: lessons for `evo`

> Research snapshot: 2026-09-28. This is a planning-stage synthesis, not a claim that one design recipe is known to produce open-ended evolution.

## Executive summary

The named systems establish several increasingly ambitious results, but they answer different questions. Coreworld explored noisy, local computational chemistry; Tierra demonstrated ecological dynamics around hand-seeded replicators; Amoeba and the 2024 *Computational Life* study demonstrated spontaneous replicator emergence from random computational material; Avida became an experimental platform for controlled evolutionary biology; Stringmol explored reaction-based replication, parasitism, spatial protection, and a universal-constructor architecture. None settles the long-term open-ended-evolution problem. “Open-ended” has multiple operational definitions, and 2024 field reviews still treat it as an active research program rather than a solved engineering target ([Taylor et al. 2016](https://doi.org/10.1162/ARTL_A_00210); [Packard et al. 2019](https://arxiv.org/abs/1909.04430); [Bourgeois et al. 2024](https://direct.mit.edu/artl/article/30/3/300/123431/Editorial-Introduction-to-the-2024-Special-Issue)).

For this project, the strongest practical lessons are:

1. **A substrate can enable a behavior without making it likely.** Instruction semantics, addressing, mutation, interaction topology, and resource accounting jointly shape the reachable evolutionary neighborhood. Test those interactions rather than treating “all bytes decode” as a sufficient evolvability guarantee.
2. **Spatial structure can contain ecological failure.** Parasites can collapse a well-mixed system, but local clusters can protect hosts and support continuing coevolution. Spatiality is not just scenery; it changes which interactions and lineages persist ([Hickinbotham et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8334846/)).
3. **Emergent replication and sustained evolution are separate milestones.** Amoeba and *Computational Life* make strong cases for the first. They do not by themselves establish robust, long-lived ecological complexity or unbounded novelty.
4. **Instrument first and make claims measurable.** Avida’s influence came in large part from repeatable experiments, controls, lineage data, and well-defined interventions. “Complexity,” “novelty,” “robustness,” and “ecological interaction” need separate operational measures.
5. **The source of energy, mutation, mortality, and space is part of the theory.** A reaper, a fixed task reward, stochastic molecule decay, cell energy, and instruction-time allocation are not interchangeable implementation details. Document what is conserved and what is imposed.
6. **Treat no-seed soup as a separate experimental regime.** BFF-style pairwise interaction starts from random programs and asks whether replicators arise. A resident ecology seeded with a replicator asks what evolution does after that transition. They should not be collapsed into one benchmark.

## What the projects did and what transfers

### Coreworld (Rasmussen et al., 1990)

Coreworld was an early noisy, one-dimensional computational chemistry: local communication in a cyclic core, parallel updates, mutation in copied code, and local computational resources. The original authors report parameter-dependent trajectories, seven successive functional epochs, and cases where cooperative structures dominated the core ([Rasmussen et al. 1990](https://doi.org/10.1016/0167-2789(90)90070-6)). Secondary summaries describe limits in stable, persistent complex programs and sensitivity to mutation/encoding, but this should not overwrite the positive primary result; the shorthand “it degraded into noise” is not an adequate account of the 1990 paper.

**Transfer:** local interactions and environmental/resource parameters can create staged organization without a hand-authored evolutionary path. But “complexity” measured as distance from random initial core is not the same as organismal complexity or open-ended novelty. Record the exact observable and the run conditions. Coreworld is also a useful warning that asynchronous or parallel update semantics are part of the model, not merely a performance choice.

### Tierra (Ray, 1991 onward)

Tierra put programs in a shared virtual memory, with CPU time and memory as limited resources. A virtual instruction set, relative/template-based addressing, and imperfect copying made programs more tolerant of mutation than ordinary machine code. From a hand-written ancestor, Ray observed parasites that borrowed host replication code, host resistance, hyperparasites, social dependence, cheaters, and other ecological dynamics ([Ray 1991, “An Approach to the Synthesis of Life”](https://tomray.me/pubs/alife2/Ray1991AnApproachToLife.pdf); [Ray’s Tierra publications and documentation](https://www.tomray.me/pubs/)). Memory pressure was handled by an explicit reaper, which made mortality and allocation policy consequential. The reaper is a designed mortality mechanism, not a natural consequence of finite memory alone.

Tierra’s ecological richness is a major precedent, but it is not evidence of indefinitely increasing complexity. A review notes runs reaching stasis with mostly neutral variation, and a size-neutral Tierra study found no increase in measured organismal complexity even as organism size increased ([Taylor et al. 2016](https://doi.org/10.1162/ARTL_A_00210); [Standish 2003](https://arxiv.org/abs/nlin/0210027)). Mutualism did not arise de novo in the reviewed Tierra experiments; Ray hand-coded mutualists to establish that they could persist ([Zaman et al. 2021](https://doi.org/10.3389/fevo.2021.739047)).

**Transfer:** template matching can make addressing robust to genome insertions/deletions and enable interaction across genomes. Parasites are both a stress test and a source of evolutionary pressure. But the exploitability of neighbors depends on execution/memory protection rules; those rules define ecology. Track reaper deaths, energy deaths, decay, and failed replication separately. A system with no reaper still needs a precise rule for what happens when bodies occupy all memory.

### Avida (Ofria, Adami, colleagues; 1990s onward)

Avida is a research platform, not one fixed world rule set. The classic model puts self-replicating instruction strings in a population/grid. Replication rate competes for CPU time and space; task/resource configurations can grant organisms additional computational merit. The 2003 *Nature* study used task rewards to ask how complex logic functions evolve. It found that complex functions could arise by building on simpler functions that were selectively favored, while no particular intermediate was essential ([Lenski et al. 2003](https://www.nature.com/articles/nature01568)). Calling this simply “designer-rewarded complexity” misses the scientific result: researchers deliberately define a tractable selection regime, then study mutation, historical contingency, and pathways under it. It does not demonstrate task-free open-endedness.

Avida’s major contribution is experimental control and analysis: replicated runs, configurable environments, lineage and genotype tracking, explicit hypotheses, and a large research community. It supports work on robustness, parasites, spatial ecology, and cross-feeding. However, task rewards, global versus local resource distribution, and organism memory rules materially change which ecologies are possible ([Ofria & Wilke 2004](https://doi.org/10.1093/bib/5.3.243); [Zaman et al. 2021](https://doi.org/10.3389/fevo.2021.739047)).

**Transfer:** adopt Avida’s experiment discipline even if `evo` rejects its fitness/reward mechanics. Keep world configuration versioned; run replicated seeds; log genomes, ancestors, mutations, births/deaths, and resource flows; compare interventions. Avida also warns that there is no neutral “resource” abstraction: a task reward that boosts CPU time gives an indirect, explicit selection gradient.

### Amoeba (Pargellis, 1996; expanded 2001)

Amoeba began from randomly generated instruction sequences and reported spontaneous self-replicators. In the 1996 paper, larger random sequences had higher probability of containing a replicator; once replication appeared, mutations first favored deletion of useless code and later the addition of subroutines that improved replication efficiency ([Pargellis 1996](https://doi.org/10.1016/0167-2789(95)00268-5)). The follow-up broadened the instruction set to a computationally universal 32-opcode basis and used randomly assigned address labels, loosening a constraint caused by predefined complementary codons ([Pargellis 2001](https://pubmed.ncbi.nlm.nih.gov/11461689/)).

**Transfer:** the probability of a replicator emerging is a property of genome-length distribution, opcode semantics, soup initialization, execution scheduling, and system scale together. Report transition rates across independent runs, not just a successful movie. Amoeba is close to `evo`’s Phase 4 criterion but uses a different ecology and replication model; it is a reference experiment, not a drop-in validation test.

### BFF / *Computational Life* (Agüera y Arcas et al., 2024)

The paper studies multiple computational substrates and reports spontaneous self-replicator emergence from random programs without an explicit fitness landscape; emergence can occur with or without background mutation. The proposed mechanism involves random program interactions and self-modification. It also reports increasingly complex dynamics after replicators arise, and gives a counterexample substrate where replicators are possible but were not observed to emerge in the experiments ([Agüera y Arcas et al. 2024](https://arxiv.org/abs/2406.19108)). “No fitness function” does not mean “no selection”: differential persistence/reproduction still arises from the substrate dynamics. The experiments’ pairing, concatenation, execution and splitting protocol is materially different from a spatial world with local ownership and energy.

A 2026 follow-up preprint re-examines the mechanism using improved self-replicator detection. It reports that simple mutation random walks in program space can find replicators at least as easily as paired interactions, and argues that ancestry depth/width caps can prevent takeover without preventing replicator discovery ([Knierim et al. 2026](https://arxiv.org/abs/2607.01483)). This is a useful, current challenge to the interpretation of the 2024 result, not a settled replacement: it is a preprint, and the competing methods should be compared on matched substrates, budgets, and detection criteria.

**Transfer:** implement a faithful small BFF-like benchmark as a substrate experiment, not by casually adapting its claim to a different VM. It tests whether interactions can synthesize copying behavior from noise. In `evo`, distinguish a BFF-like spontaneous-origin experiment from a seeded ecosystem run. The paper’s multiple substrates also support treating ISA variants as controlled experiments on the same world rules.

### Stringmol

Stringmol is an artificial chemistry: variable-length opcode strings bind probabilistically by soft matching and execute together through pointers. Opcode execution consumes energy; molecules decay stochastically; copying introduces point, insertion, and deletion mutations ([Hickinbotham et al. 2010 specification](https://www.cs.york.ac.uk/library/reports/2010/YCS/458/YCS-2010-458.pdf); [Clark et al. 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5454285/)). In a spatial 2D Stringmol study, local Moore-neighborhood reactions allowed spatial patterns to shelter replicators from parasites. Across 20 runs, 8 survived two million time steps; surviving runs showed increases in both population and species count, with host–parasite dynamics changing over time ([Hickinbotham et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8334846/)). This is a concrete example where spatial patterning affects system survival, not just lineage geography.

A separate Stringmol universal-constructor architecture encoded genome, copier, expressor and payload components. It demonstrated transition between viable semantically closed systems, but 500 runs eventually died; the dominant failure was “bureaucratic death” after diversity explosion and cascading expression errors, rather than the parasite-driven extinction found in earlier replicase systems ([Clark et al. 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5454285/)). This makes a useful caution: adding complexity can introduce a new failure mode rather than solve persistence.

**Transfer:** consider the interaction-as-execution model as a later alternative to organism-owned sequential VMs. Its soft binding, no-crash instruction semantics, energy costs, and explicit molecular decay are all evolvability/ecology design choices worth comparing. The semantic-closure result suggests a long-horizon question: can an encoding, its copier, and its expression machinery co-evolve? It also argues for separately measuring copying fidelity and expression/phenotype fidelity.

In a separate Stringmol study, conservation of matter was experimentally associated with greater evolutionary activity and diversity under particular opcode concentrations; the authors found that opcode abundance had an optimum and that configurations differed between runs ([Hickinbotham & Stepney 2015](https://doi.org/10.7551/978-0-262-33027-5-ch024)). This is encouraging precedent for `evo`’s finite-memory premise, but it is a specific result in Stringmol, not proof that conservation alone prevents stagnation.

## Other useful comparators and newer work

### Geb and embodied digital evolution

Geb (Channon) is not a genome-copying soup; it is a world of embodied agents with neural controllers. Reviews report Geb as an early system that met Bedau–Packard evolutionary-activity criteria, and describe novel behaviors such as following, fighting, fleeing, and mimicry ([Taylor et al. 2016](https://doi.org/10.1162/ARTL_A_00210)). It is relevant as a contrast: richer embodiment can support behavioral novelty, but its agents and objectives differ from `evo`’s self-replicating program ecology. Use it as a source of measurement ideas, not as evidence that its design can be transplanted directly.

### Open-endedness metrics and limits

The field has developed behavioral categories and activity measures rather than a single accepted scalar “open-endedness” test. Current reviews emphasize ongoing adaptive novelty and/or complexity growth as hallmarks, with explicit procedures proposed for particular categories ([Taylor et al. 2016](https://doi.org/10.1162/ARTL_A_00210); [Channon et al. 2024](https://doi.org/10.1162/artl_e_00445); [Channon 2024](https://doi.org/10.1162/artl_a_00430)). Stepney and Hickinbotham apply several measures to long spatial Stringmol runs, but argue that the focus should be on understanding mechanisms and moving from generic to system-specific analysis, since an open-ended system may outgrow any current model/measure ([Stepney & Hickinbotham 2024](https://doi.org/10.1162/artl_a_00399)). For this project, use a dashboard of independent observables and state the time horizon and null model; treat measured novelty as evidence, not proof of indefinite growth.

### Recent computational origin experiments

The 2024 *Computational Life* work and its 2026 follow-up are the most directly relevant recent computational-origin results in this review. Nearby fields offer useful boundary comparisons: DigiHive (2023) is an artificial chemistry aimed at self-organization and constructing a cell-like self-replicator, described as preliminary rather than a demonstrated mature evolving ecology ([DigiHive 2023](https://pubmed.ncbi.nlm.nih.gov/36787452/)); 2024 synthetic-protocell work demonstrated Darwinian evolution of a DNA-encoded self-replicator in vitro, a very different physical substrate with externally supplied biological machinery ([Nature Communications 2024](https://www.nature.com/articles/s41467-024-53226-0)). These projects broaden the landscape but are not directly comparable to a digital instruction soup.

## Implications for the current plan

### Keep the two success questions separate

- **Origin:** Can a self-replicator emerge from random matter? Record per-seed emergence probability, time-to-first-replicator, and dependence on soup size and genome-length distribution.
- **Ecology/evolution:** Given a seed, what lineages, interactions, complexity, and evolutionary activity persist? Record parasite burden, host extinction, spatial clustering, lineage depth, behavioral novelty, genome/function measures, and resource flow.

Success on one does not establish the other. Avida is particularly strong on controlled seeded evolutionary experiments; Amoeba and the BFF paper target spontaneous origin.

### Treat the ISA as an experimental factor, not a one-shot design bet

The plan’s “every byte is valid” rule is sensible fault containment, but total decoding alone does not guarantee a useful mutational neighborhood. Measure viable-neighbor fraction, mutational robustness, replication-capable neighborhood size, and the distribution of phenotypic effects for each ISA. Compare register and stack versions using identical world, resource, and mutation conditions as planned. Test template addressing, redundant op encodings, and instruction locality as factors. BFF’s substrate counterexample and Amoeba’s address-label redesign both show that small representation details can alter emergence.

### Reconcile noisy write, bit decay, and “mutation is physics”

These are three different processes if implemented literally: mutation during copying (heritable), environmental corruption of genomes (heritable only if it persists into reproduction), and body/material decay (possibly non-genetic damage or death). Define each event, its target, and whether repair restores information. A universal background bit-flip can destroy data, executable body, owner metadata, or energy state unless the substrate rule specifies what is exposed to noise. Keep mutation rates/decay rates configurable and log realized events; do not describe one as a proxy for another.

### Make space, ownership, and mortality coherent

The plan combines finite conserved memory, contiguous owned bodies, external writes/drains, guarded bytes, dead debris, and no reaper. Specify how an organism can overwrite, copy from, or execute a neighbor if ownership guards disallow access; this is a central design choice governing parasitism. Also define allocation failure, the status of a dead organism’s bytes, and what happens when no free/debris region exists. Tierra’s reaper is an example of an explicit rule; Stringmol decay is another. The lesson is to expose these policies rather than let them emerge accidentally from implementation details.

### Energy model: distinguish energy from CPU scheduling

Avida allocates execution opportunity via merit; Tierra allocates CPU time according to its scheduler; Stringmol charges each opcode against energy flux. `evo`’s paid-per-instruction execution is a useful distinct choice. Its mass/energy analogy needs dimensional consistency: can stored energy be gained only by `absorb`, or also by draining? Does energy move spatially with a body or stay in a cell? If the cell pool is dilute but free to all occupants, co-location may reward crowding. Treat energy by-cell versus by-organism as an experiment, as the plan already notes.

### Heterogeneity is a hypothesis to test

Spatial structure is supported by parasite-containment and ecological results; non-stationarity is plausible but not a universal cure for stagnation. A changing environment can create ongoing selection while also making results hard to interpret. Start with fixed heterogeneous landscapes, then compare fixed vs seasonal vs drifting conditions and a homogeneous control. Avoid attributing novelty to “environmental change” without replicated controls.

### Instrumentation and analysis should be built before adding many physics rules

Use deterministic seeds and versioned configs, but also record execution semantics, scheduler order, mutation/decay events, and energy transfers. Keep full lineage/genome references and periodic spatial snapshots. In addition to population and genome length, collect: unique genotypes and functional phenotypes; phenotype novelty under a declared distance; replication rate and cost; mutation robustness; local interaction network; parasite/host dependencies; spatial autocorrelation; extinction/recovery events; energy input/output; and time series needed for evolutionary-activity measures. Preserve raw runs so later metrics can be recomputed.

### Recommended staged research workflow

1. **Replicate historical baselines** as small, isolated benchmarks where feasible: a seeded Tierra-like host–parasite ecology; Amoeba-style random soup; BFF-style pair-interaction emergence. Document differences from the original.
2. **Phase 1** should prove the ancestor can copy, mutate and reproduce under the energy ledger. Add an adversarial parasite only after basic reproduction is understood; instrument before making the ecological claim.
3. **Ablate one design decision at a time:** spatial vs well-mixed, noisy-copy vs background flips, per-organism vs per-cell energy, locality cost, and guard/access policy.
4. **Run replicated seeds and publish negative results.** Report distributions and extinction rates, not a single visually compelling run.
5. **Maintain a dated hypotheses log.** For each expected outcome, identify a measurable result that would count against it.

## Bottom line for planning

The plan’s emphasis on a custom evolvable VM, locality, ecological interaction, determinism, and observability has strong historical motivation. The literature does not justify treating size-scaling costs, climate drift, or natural bit rot as proven solutions to equilibrium. Those are testable hypotheses. The most valuable early deliverable is therefore not a more biologically elaborate world, but a small world whose accounting and semantics are explicit and whose behavior can be compared across controlled, reproducible variants.

## Selected citations

- Rasmussen, S., Knudsen, C., Feldberg, R., & Hindsholm, M. (1990). [The Coreworld: Emergence and evolution of cooperative structures in a computational chemistry](https://doi.org/10.1016/0167-2789(90)90070-6). *Physica D*, 42, 111–134.
- Ray, T. S. (1991). [An approach to the synthesis of life](https://tomray.me/pubs/alife2/Ray1991AnApproachToLife.pdf). In *Artificial Life II*.
- Pargellis, A. N. (1996). [The spontaneous generation of digital “Life”](https://doi.org/10.1016/0167-2789(95)00268-5). *Physica D*, 91, 86–96.
- Pargellis, A. N. (2001). [Digital life behavior in the Amoeba world](https://doi.org/10.1162/106454601300328025). *Artificial Life*, 7(1), 63–75.
- Lenski, R. E., Ofria, C., Pennock, R. T., & Adami, C. (2003). [The evolutionary origin of complex features](https://doi.org/10.1038/nature01568). *Nature*, 423, 139–144.
- Ofria, C., & Wilke, C. O. (2004). [Avida: A software platform for research in computational evolutionary biology](https://doi.org/10.1093/bib/5.3.243). *Briefings in Bioinformatics*, 5(3), 243–254.
- Hickinbotham, S. et al. (2010). [Specification of the Stringmol chemical programming language](https://www.cs.york.ac.uk/library/reports/2010/YCS/458/YCS-2010-458.pdf). University of York Technical Report YCS-2010-458.
- Taylor, T. et al. (2016). [Open-Ended Evolution: Perspectives from the OEE Workshop in York](https://doi.org/10.1162/ARTL_A_00210). *Artificial Life*, 22(3), 408–423.
- Hickinbotham, S. J., & Stepney, S. (2015). [Conservation of matter increases evolutionary activity](https://doi.org/10.7551/978-0-262-33027-5-ch024). In *European Conference on Artificial Life 2015*, 98–105.
- Clark, E. B., Hickinbotham, S. J., & Stepney, S. (2017). [Semantic closure demonstrated by the evolution of a universal constructor architecture in an artificial chemistry](https://doi.org/10.1098/rsif.2016.1033). *Journal of the Royal Society Interface*, 14, 20161033.
- Agüera y Arcas, B. et al. (2024). [Computational Life: How Well-formed, Self-replicating Programs Emerge from Simple Interaction](https://arxiv.org/abs/2406.19108). arXiv:2406.19108.
- Knierim, C. et al. (2026). [BFF: Simple explanations for complex phenomena](https://arxiv.org/abs/2607.01483). arXiv:2607.01483, preprint.
- Hickinbotham, S. et al. (2021). [Nothing in evolution makes sense except in the light of parasitism: evolution of complex replication strategies](https://doi.org/10.1098/rsif.2021.0022). *Journal of the Royal Society Interface*, 18, 20210022.
- Zaman, L. et al. (2021). [Symbiosis in Digital Evolution: Past, Present, and Future](https://doi.org/10.3389/fevo.2021.739047). *Frontiers in Ecology and Evolution*, 9, 739047.
- Stepney, S., & Hickinbotham, S. (2024). [On the Open-Endedness of Detecting Open-Endedness](https://doi.org/10.1162/artl_a_00399). *Artificial Life*, 30(3), 390–416.
- Channon, A. (2024). [A Procedure for Testing for Tokyo Type 1 Open-Ended Evolution](https://doi.org/10.1162/artl_a_00430). *Artificial Life*, 30(3), 345–355.
- Channon, A., Bedau, M. A., Packard, N. H., & Taylor, T. (2024). [Editorial Introduction to the 2024 Special Issue on Open-Ended Evolution](https://doi.org/10.1162/artl_e_00445). *Artificial Life*, 30(3), 300–301.
