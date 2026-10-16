# ALIEN: notes for evo

Compiled 2026-10-15. Source read from a local clone of
[chrxh/alien](https://github.com/chrxh/alien) at commit `0dbf03dee`
(2026-10-15), `C:\dev\repos\evolution-sims\alien`. ALIEN was not run for
this note; everything below comes from the source, the docs under
`resources/docs/` and `RELEASE-NOTES.md`.

Conventions, as in the other notes: anchors are `path:line` relative to the
ALIEN repo root; "(inference)" marks my own reasoning rather than what the
source says. Kernel paths are shortened to `Kernels/` for
`source/Engine/Impl/Kernels/`.

---

## 1. What ALIEN is

ALIEN is a 2D artificial-life simulator that runs on the GPU (CUDA, C++23,
Vulkan). Everything in the world is a particle; cells are particles bonded
into soft bodies, and each cell runs a small neural network. A genome is a
list of genes, each a list of nodes; a constructor cell reads the genome and
builds the offspring cell by cell. Cells have types (attacker, defender,
digestor, depot, injector, sensor, muscle, and others), and the cell type
decides what a cell can do.

Selection is emergent: there is no fitness function. But the trophic roles
are designed in. A predator is a creature with attacker cells, a plant is a
creature with many digestors, a virus is a creature with an injector. The
docs describe the intended food chain directly (`resources/docs/energy.md:84`:
"Plant-like creatures with many digestor cells absorb the particles,
herbivores attack the plants and predators attack the herbivores").

ALIEN publishes no quantitative open-endedness result. Its evidence that
evolution happens is the dashboard (creature count, mean cells per creature,
mean genome nodes, mean generation; `resources/docs/evolution.md:22`) plus
screenshots and videos. Its own reading of complexity is "A rising number of
genome nodes indicates that genomes become more complex"
(`resources/docs/evolution.md:22`).

It ships an MCP server (run, pause, step, flashbacks, statistics,
screenshots, editing, parameters; `resources/docs/ai-agents.md`), so an
agent can drive it.

## 2. Lessons for evo

Ordered by how directly they bear on current work.

### 2.1 Predation shaped to hit reproduction first (bears on T12 `drain`)

ALIEN's attacker cell steals energy from a neighbouring creature. Three
details of how it does so are relevant to `drain`.

**The take comes out of reproduction before survival.**
`absorbAttackableEnergy` (`Kernels/AttackerProcessor.cuh:205-218`) takes
first from a depot's stored energy, then from the constructor's build
reserve, and only then from the usable energy that keeps the cell alive. A
victim's reproduction slows before its life is at risk, so the cost is
graded by the order of the take, not by a clause that forbids killing. T12
gets the same gradedness by capping the take at `victim.energy −
victim.upkeep_tick_m` (`docs/tasks/T12-drain-income-take.md`); ALIEN's
version is the more biological reading of "survivable" (inference).

**The predator's gain is capped by its own body.** Loot arrives as raw
energy (`resources/docs/energy.md:12, 24`), which is useless until a
digestor cell converts it. The attacker does nothing while its raw energy is
2 or more (`Kernels/AttackerProcessor.cuh:44`; threshold
`attackerMaxRawEnergyThreshold = 2.0f` at `source/Data/SimulationParameters.h:164`).
A digestor converts at most `(1 − rawEnergyConductivity) ×
maxRawEnergyConversion × 6` raw energy per activation
(`Kernels/DigestorProcessor.cuh:33-36`), with `maxRawEnergyConversion`
default 0.1 (`source/Data/SimulationParameters.h:169`),
`TIMESTEPS_PER_CELL_FUNCTION = 6` (`source/Data/EngineConstants.h:22`) and
the conductivity a genome trait defaulting to 0.5
(`source/Data/CellTypeConstants.h:457`). So predation only pays with
digestion machinery behind it. T12 caps the drainer's gain only by
`drainer_room`, its free store space.

**Kin rules are hard-coded.** An attacker never attacks its own offspring
(`Kernels/AttackerProcessor.cuh:125-128`), and there is an optional
`attackerRelatedLineageProtection` parameter, default 0
(`source/Data/SimulationParameters.h:160`).

**What evo is missing.** Neither T12 nor the drain memo logs how related the
drainer and its victim are. T12's target is the owner of the byte at the
address the drainer sets (T12 §1), and the expected way a drainer finds a
target is a template search for the ancestor's label (T12 G2). A search for
one's own label finds organisms that carry the same label, which in a world
dominated by one class are mostly the drainer's relatives (inference). A
positive drain result could then be mostly kin cannibalism. Proposed: E018
logs, per successful drain, whether the victim is the drainer's parent, its
child, or shares its `func_hash`.

### 2.2 Graded, stackable defence (contrast with E016)

ALIEN's defences come in small additive steps:

- Each defender cell on the victim divides the stolen energy by
  `defenderAntiAttackerStrength + 1` (1.5 at the default 0.5), and defenders
  multiply: `powf(strength + 1, numDefenderCells)`
  (`Kernels/AttackerProcessor.cuh:142-145`).
- Each defender raises the cost of an injection (ALIEN's virus mechanic, which
  takes over the host's constructor to build the injector's gene) by 50%:
  `injectorEnergyCost *= (1.0f + toFloat(numDefenders) * 0.5f)`
  (`Kernels/InjectorProcessor.cuh:65`).

So selection has a slope to climb: one more defender cell is a little more
protection.

E016's only evolved defence is a relabelling of the copy template, which is
all-or-nothing (`docs/research/e016-writeup-2026-10-15.md` §1). Caveat
(Fable, 2026-10-15): "each new label has its own one-hop parasite" is the
E016 record's first reading; T11 §2 then found 28 of the 34 most common
immune bodies closed against their own label flip (15 label-free, 13 with
a 1–2-nop label and a second copy behind it), so the class is mostly
closed, not a moving target. The contrast with ALIEN stands either way:
evo's defence is a step, ALIEN's is a slope.

ALIEN proves nothing about evo here, because its gradient is designed in: a
defender is one cell-type mutation away, and full immunity to injection is a
genome flag (`resistanceToInjection`, `Kernels/Genome.cuh:476`, checked at
`Kernels/InjectorProcessor.cuh:53`) that no mutation touches.

What it suggests (inference, untested): exact template matching may be what
forces all-or-nothing defence in evo. Under exact matching a parasite either
finds its target or does not. Stringmol's probabilistic binding
(Smith-Waterman alignment, probability rising with match quality;
`docs/research/literature.md:120`) makes infection succeed with a
probability set by how well the templates match, which is the
instruction-level way to make defence graded. A candidate hypothesis for the
log: "with probabilistic template matching, defence against the one-hop
parasite evolves by degrees (match quality falls over time) rather than by
relabelling".

### 2.3 Energy pathways through conversion steps (goal 3)

ALIEN has seven energy forms (`resources/docs/energy.md:9-17`): usable, raw,
the constructor's reserve, depot storage, object energy (free cells as
food), drifting energy particles, and an external pool outside the world.
Energy inside the world is conserved; the external pool can add energy and,
through "backflow", take some back (`resources/docs/energy.md:19, 40, 78`).

The variety of pathways comes from conversion steps rather than from the
number of forms. Raw energy is worthless until digested, so an organism
needs a digestor to use any food at all. Released energy reappears as
particles, near the dead cell or at a radiation source elsewhere, so energy
moves through space as well as between organisms.

A possible evo version (inference, unvalidated): drain loot, or energy
scavenged from dead organisms (the drain memo's branch C), arrives as a
second form that a `digest`-like op converts to usable energy at a capped
rate. Each food source would then need its own code, and specialisation on
one source could pay. This is a design option for after T12, not a
recommendation now.

### 2.4 Evolvable mutation rates, and a cheap check for evo

In ALIEN, mutation rates are stored in the genome. With meta-mutation on,
each copy nudges every rate a little (`Kernels/MutationProcessor.cuh:1980`).
The presets start every rate at zero with meta-mutation strength 0.0002, and
"Over millions of time steps the successful lineages arrive at
probabilities between about 0.0001 and 0.015, different for each kind of
mutation" (`resources/docs/evolution.md:70`). That is a claim in the docs,
not a reported measurement.

In evo, noise is physics, and fidelity can change only through evolved code
(proofreading, or sloppier copying; PLAN.md §3, lines 83-84). That route is
much longer than a rate parameter.

Cheap check: do any one-hop mutants of the ancestor copy more or less
faithfully than the ancestor? `neighbours.csv` from `--neighbours` already
has `births_alone` and `exact_alone` (`docs/tasks/T03-template-ancestor.md:119`),
so per-mutant fidelity is `exact_alone / births_alone`. If no one-hop
mutant changes fidelity, the "fidelity under selection" principle is
dormant in practice, however true in principle.

**Checked 2026-10-15 (Fable), on `runs/e015/nbhd/std.csv` and
`tierra.csv`** (E015 stage 1; the files exist, the sentence above that
said otherwise was wrong). Among mutants with at least 5 births alone
(879 of 5,376 std, 2,287 of 10,496 tierra), `exact_alone / births_alone`
is exactly 0 or exactly 1 for every row; no intermediate value. That is
expected: the harness runs quiet (noise off), so the ratio measures
whether the program copies itself correctly, not how it fares under
noise. The check as stated cannot see fidelity. A real version needs
the neighbourhood run with the world's `--p` and `--rot`, comparing each
mutant's exact share against the ancestor's under the same noise, and
even then a one-hop mutant that proofreads is implausible. Dropped as an
action item; the E016 line of descent (195 of 196 repairs carrying no
copy error, T06 note in `docs/tasks/README.md`) is the existing evidence
on copy fidelity.

### 2.5 Paying for complexity was tried, then removed

ALIEN 4.8.0 (2024-02-25) made attack and particle absorption depend on
"genome complexity" (`RELEASE-NOTES.md:185-186`). Later 4.x versions added
complexity plots, a complexity-variance autosave trigger, and sensors that
could target "less and more complex" mutants (`RELEASE-NOTES.md:25, 50, 58,
81, 105`), plus a cell age limiter (`RELEASE-NOTES.md:109`). Commit
`5375fdcb7` (2025-09-06), "Remove genome complexity logic", took the
complexity logic out; none of it is in the current source.

The commit gives no reason, so this is not evidence that rewarding
complexity failed. It does show a leading ALife simulator paying for
complexity directly for about 18 months and then backing out.

ALIEN's evolution recipe still requires a maximum cell age: "To keep
evolution going, old creatures must make room for new ones"
(`resources/docs/evolution.md:81`; recommended values at lines 88 and 92).
That is a reaper, and it matches Avida's age limit already in PLAN §2.

## 3. Lower value, or not worth taking

- **Lineage id.** Each creature accumulates mutation size divided by its
  genome's node count; past `newLineageThreshold` (default 0.25,
  `source/Data/SimulationParameters.h:127`) it gets a new lineage id
  (`Kernels/MutationProcessor.cuh:2113-2131`). A cheap live label, but much
  weaker than evo's planned phylogeny measures.
- **Per-lineage accumulators** in `Kernels/SimulationStatistics.cuh`:
  creatures created, total mutations, attacked energy, muscle activity,
  kept after a lineage goes extinct. Evo's T04 snapshots already allow this
  after the fact.
- **The physics, rendering and per-cell neural networks** belong to a
  different research programme.
- **An MCP server for evo.** T04 snapshots and replay cover the research
  need. Note in passing: ALIEN's `AGENTS.md` gives agents their own build
  tree, separate from the IDE's, the same problem evo solved with worktrees.

Minor ALIEN bug, for the record: the per-colour parameter
`defenderAntiInjectorStrength` is defined in `source/Data/SimulationParameters.h`
but no kernel reads it; the injector uses a hard-coded 0.5
(`Kernels/InjectorProcessor.cuh:65`).

## 4. Proposed PLAN §2 row

| System | Year | Substrate | Key result | Where it stalled |
|---|---|---|---|---|
| ALIEN (Heinemann) | 2008; GPU versions 2021+ | GPU 2D particle physics; soft bodies of typed cells, each with a small neural net; genome of genes built by constructor cells; mutation rates in the genome | Designed trophic roles (attacker, digestor, injector, defender) produce plant / herbivore / predator worlds; mutation rates evolve under meta-mutation | No quantitative open-endedness measure; evidence is dashboard plots and video. Paid for genome complexity directly from 4.8.0 (2024) and removed it in 2025 without a stated reason. Still needs a maximum cell age (a reaper) to keep evolution going |

## 5. Candidate action items (for review, not yet in PLAN)

1. T12 / E018: log drainer–victim relatedness per drain (parent, child,
   same `func_hash`). Small; belongs in T12 §1.1's ledger.
2. ~~One-hop fidelity check from `--neighbours` output~~ Done
   2026-10-15, uninformative: the quiet harness gives 0 or 1 for every
   mutant (§2.4). Dropped.
3. Register the probabilistic-matching hypothesis (§2.2) in
   `docs/research/hypotheses.md` if Line A is going to try graded binding.
4. Add the §4 row to PLAN §2.
5. Optional: run ALIEN's "Evolution Results" presets through its MCP server
   to see whether mean genome nodes keep rising or plateau, which would put
   a number in the §4 row instead of a description. Needs the nightly
   Windows build or a CUDA build, and competes with Line B for the GPU.

## Sources

- ALIEN source at `0dbf03dee`: https://github.com/chrxh/alien
- Heinemann, C.: *Artificial Life Environment*. Informatik-Spektrum 31, 55–61 (2008). https://doi.org/10.1007/s00287-007-0205-1 (the citation ALIEN asks for, `README.md:241`)
- `resources/docs/energy.md`, `evolution.md`, `ai-agents.md`,
  `how-life-works.md`, `genomes.md`, `cell-types.md` in the same tree.
- `RELEASE-NOTES.md` (ends at 4.12.2, 2025-05-26; the current code is a
  2025–2026 rewrite past that).
