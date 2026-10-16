# Other repos in `evolution-sims`: quick review for evo

Compiled 2026-10-15. A quick pass over the repositories in
`C:\dev\repos\evolution-sims` other than ALIEN, which has its own note
(`alien.md`). Each repo was read by a subagent with evo's goals as the
brief and spot-checked here; none was run. Anchors are `path:line`
relative to each repo's root. "(inference)" marks reasoning rather than
what the source says. The review was quick: verdicts are about relevance
to evo, not about the quality of the projects.

## Summary

| Repo | What it is | Verdict |
|---|---|---|
| alien | GPU soft-body ALife, designed trophic roles | Relevant; see `alien.md` |
| dgm | Darwin Gödel Machine: self-modifying coding agents with an archive | Tangential: archive search under a benchmark score |
| yoyo-evolve | A Rust coding agent that rewrites itself daily | Unrelated to the science; some process lessons |
| biosim4 | Neural agents on a grid, selected by a survival zone | Tangential: a GA, not an ecology |
| jelly-evolution-sim-jes | Soft-body jellies selected for distance moved | Tangential: species bookkeeping only |
| evolving-cellular-automata | GA over CA rule tables | Unrelated |
| evox | GPU black-box optimisation library | Tangential, GPU engineering only |
| Evolutionary-Algorithm | GA/ES tutorial scripts | Unrelated |

Every repo except ALIEN, DGM and yoyo-evolve has a designed fitness
function or selection zone, which is the opposite of evo's design. Their
value to evo is in bookkeeping and analysis, not in mechanisms.

## dgm (Darwin Gödel Machine, Sakana)

**What it is.** A Python coding agent whose own source is changed by
LLM-written patches; each variant is scored on SWE-bench or Polyglot. The
archive keeps every child that compiles (`DGM_outer.py:174-190`), and
parents are drawn with probability proportional to
sigmoid(10·(score − 0.5)) × 1/(1 + children) (`DGM_outer.py:91-99`), so
high scorers are favoured but a parent with many children is drawn less.
The only measure is benchmark accuracy, plus a plot of the line of descent
to the best agent (`analysis/plot_progress.py:58-82`).

**Verdict: tangential.** Its open-endedness is an archive-based search for
a better score under an explicit fitness function.

**Takeaways.** Both are things evo already does, which is worth knowing
rather than worth adopting:

- **Ablations as the argument.** `no_darwin` always builds on the latest
  child (`DGM_outer.py:79-82`); `no_selfimprove` freezes the modifying
  agent while still evaluating the modified one
  (`self_improve_step.py:294`). Evo's off controls (E016 with and without
  the cost; Line B rule-off controls) are the same move.
- **Line of descent to the best.** DGM's stepping-stone claim rests on
  ancestors of the best agent that scored worse than their contemporaries.
  The E016 write-up already reports the fitness of each intermediate on
  the path to the first relabelling, which is the stronger version.
- Staged evaluation (10 tasks, then 50 if ≥ 40% solved, then the full set
  only if the child beats the second best; `self_improve_step.py:153-155`,
  `DGM_outer.py:192-219`) matches evo's pilot-then-full pattern.

**Not worth taking.** The parent-selection formula (it needs a score). The
self-improvement prompt shows the LLM the hidden answer and test patches
for the same tasks used to score it
(`prompts/self_improvement_prompt.py:95-99, 320-323`), so there is no
train/test split. Small bugs suggest the published baselines were not run
from this code as it stands: a missing comma in the `choices` list makes
`score_child_prop` and `best` unselectable from the command line
(`DGM_outer.py:228`), and `best` sorts ascending, so it picks the worst
(`DGM_outer.py:103-104`).

## yoyo-evolve

**What it is.** One Rust coding agent editing its own repo about three
times a day. A change is kept only if the build and tests pass and a
separate LLM evaluator returns PASS. There is no population and no
selection between variants, so "evolution" is a metaphor.

**Verdict: unrelated to the science.** Its process lessons apply to evo's
human-plus-agents workflow, and several come from logged incidents:

- **"Could not check" is never zero.** Sessions reported green while every
  agent call returned HTTP 404 (`.yoyo.toml:8-12`); three HTTP 429 errors
  became "No outstanding commitments" (`scripts/scan_commitments.py:35-39`).
  The fix is a `COULD_NOT_CHECK` state that is never folded into a verdict
  (`scripts/counterfactual_green.py:37-45`). For evo's analysis scripts
  (inference): a missing input file, an empty window or a failed seed
  should print as "not checked", never as a zero count.
- **Was the green earned?** Rerunning the old tests against the new code
  flagged 6 of 34 judgeable commits as UNEARNED
  (`dreams/counterfactual_verdicts.jsonl`, 28 EARNED, 6 UNEARNED, the rest
  not judgeable). The evo analogue (inference): when one commit changes
  both an analysis and its threshold, rerun the old check on the new data
  before reading the result.
- **Meters that count their own prose.** A grep-based meter counted the
  agent's own notes written into the same log
  (`scripts/measure_abstentions.py:8-25`); anchor counts on lines the tool
  itself emits.
- **Unrestored positive controls.** A deliberately broken check left in
  place cost about 22 hours of a broken main branch; the fix is a marker
  plus a test that fails while the marker is present (`CLAUDE.md:172`).

**Not worth taking.** The persona and journal files, the self-audit
scripts, and the end-of-session `git add -A` (`CLAUDE.md:172`), which
conflicts with evo's rule on staging named files. The project has drifted
into measuring its own measurements (`DREAM.md:29`) (inference).

## biosim4 (David Miller)

**What it is.** Each genome is a list of 32-bit genes, each one synapse
(source, sink, int16 weight), with source and sink reduced modulo the
number of sensors, neurons or actions so every bit pattern decodes
(`src/genome-neurons.h:23-35`, `src/genome.cpp:75-94`). Generations are
discrete, the population is fixed at 3,000, and at the end of each
generation only agents inside a challenge zone survive
(`src/survival-criteria.cpp:16-100`). Offspring are scattered to random
cells, which wipes out spatial structure each generation. The repo holds no
results data; its evidence is a YouTube video.

**Takeaways** (design choices; none is backed by evidence in the repo):

- **Log kills apart from other deaths.** `murderCount` is counted before
  environmental deaths are queued and written to the per-generation log
  (`src/analysis.cpp:272-285`). For `drain`: log drain-caused deaths, if the
  final rule allows any, separately from upkeep starvation. The subagent
  notes the same victim can be queued twice (`src/peeps.cpp:28-31`), so
  biosim4's count can be inflated.
- **Carried versus used.** Its sensor and action tallies count only
  connections that survive culling of dead-end neurons
  (`src/analysis.cpp:318-337`). The evo analogue: per genotype, `drain`
  present in the body versus `drain` executed, to tell a hitchhiking op
  from a working one. Evo's per-op execution counts may already cover this;
  not checked.
- **Scheduled parameter changes.** `name@gen = value` in the config changes
  a setting at a set generation (`src/params.cpp:284-300`). For evo, a
  within-run switch (e.g. turn `drain` on at tick N and compare activity
  before and after) is a cheap design for a first look, though it is not a
  substitute for paired seeds.
- **Graded kin sensing.** The `GENETIC_SIM_FWD` sensor returns a 0–1
  genome similarity for the neighbour ahead (`src/getSensor.cpp:344-354`).
  (inference) The ISA analogue would be an op that reports how well a
  neighbour matches one's own template: a graded recognition signal, the
  sensing half of the graded defence discussed in `alien.md` §2.2. There
  is no evidence in biosim4 that agents use the sensor.

**Not worth taking.** Kill is compiled out by default, free, binary and
pays the killer nothing (`src/sensors-actions.h:85-86`; `biosim4.ini:58`).
The altruism experiment hard-codes kin selection: parents are replaced by
relatives at similarity ≥ 0.7 (`src/spawnNewGeneration.cpp:300-327`). The
similarity metrics are flawed (e.g. "Jaro-Winkler" is only Jaro over the
first 20 genes, `src/genome-compare.cpp:40-42`), and `geneticDiversity`
(`src/genome-compare.cpp:153-172`) is far weaker than MODES or
Bedau–Packard.

## jelly-evolution-sim-jes (carykh)

**What it is.** Soft-body "jellies" selected on a fixed score, the mean
distance moved in x (`jes_sim.py:176`); in each rank-paired contest the
loser is replaced by a mutant of the winner (`jes_sim.py:203-215`). Its
interest for evo is how it records species.

**Takeaways** (design choices):

- **Species as a clade started by a marked event.** A "big mutation" gives
  the child a new species id, a plain counter
  (`jes_creature.py:105-107`), with the parent recorded
  (`jes_sim.py:246-247`). No distance or clustering is computed, so the
  definition is exact and cheap. For evo, a clade could start at a chosen
  mutation class, such as a change of `func_hash` or of length
  (inference).
- **Prominence passes to ancestors.** A species that reaches 10% of the
  population (`jes_sim.py:40, 162`) is marked prominent, and so are all its
  ancestors (`jes_species_info.py:25-31`); the family tree draws only
  prominent species. The result is a pruned phylogeny that keeps the path
  back to the root, which is what a readable phylogeny figure for E016-type
  runs needs.
- **Four representatives per species:** the ancestor, the first member, the
  member at peak population, and the last (`jes_species_info.py:17`).
  Good default targets for T04 snapshot replay.

**Not worth taking.** The stacked-area chart orders species by id
(`jes_sim.py:149`), so child bands do not nest inside parent bands; it is
not a Muller plot. Evo's `analysis/explore.py` genotype stack
(around line 617) has the same limit.

## evolving-cellular-automata (one author, 2019 article)

**What it is.** A generational GA over cellular-automaton rule tables
(512-bit lookup tables, `draw_node.js:11`), with hand-written fitness
functions or human selection by checkbox (`testpop_from_file.js:343-355`).
Nothing reproduces itself; no ecology, no energy.

**Verdict: unrelated.** Two visualisation ideas only:

- **Gene-usage mask** (`docs/article.md:279-281`): grey out the rule-table
  entries a phenotype never visits. The evo analogue is a per-genome
  executed-site mask, separating neutral bytes from functional ones; it
  would show, for instance, whether a relabelled template sits in code
  that runs (inference).
- **Distribution raster** (`visualize.html:81-92`): one row per
  generation, a pixel lit wherever any individual has that value. Over
  genome length, store or parasite load this shows branching and
  extinction better than mean lines (inference).

## evox (EvoX)

**What it is.** A PyTorch library for fitness-based black-box
optimisation on the GPU (DE, ES, PSO, multi-objective EAs,
neuroevolution). It has no MAP-Elites, novelty search or other
open-ended algorithm.

**Verdict: tangential, GPU engineering only.** Line B runs through the
cubff fork (PLAN §8.4), which has its own RNG and kernels, so these matter
only if evo ever writes its own GPU interpreter (B3 on the GPU):

- **Counter-based random numbers.** Philox, keyed by a per-individual seed
  and a counter, so GPU thread order cannot change a replay
  (`src/evox/triton_kernels/kernels/philox.py:1-22, 52-68`). The file says
  the Triton and PyTorch paths are designed to give identical output
  (`philox.py:13-14`); the tests check the PyTorch path on CPU only.
- **A warning.** EvoX's vectorised code cannot branch on data; its
  `switch` computes every branch and picks one
  (`src/evox/utils/jit_fix_operator.py:6-21`). A virtual CPU where each
  organism runs a different instruction would compute every opcode every
  step under that model (inference). Per-thread CUDA kernels, as in cubff,
  are the better precedent.

## Evolutionary-Algorithm (MorvanZhou)

Teaching scripts for GA, ES, NES and the microbial GA, each with an
explicit fitness function. NEAT is the `neat-python` library
(`NEAT/run_xor.py:9`), so innovation numbers are not implemented here.
**Unrelated; skip.**

## Candidate action items (for review, not yet in PLAN)

None of these is large; all are analysis or bookkeeping, and the
mechanism lessons are in `alien.md` §5.

1. **Phylogeny figure (Line C).** A pruned clade tree in the JES style:
   start a clade at a marked event (a new `func_hash`, say), mark a clade
   prominent at a population share, pass prominence to its ancestors, draw
   only prominent clades; keep four representatives per clade (ancestor,
   first, peak, last) as replay targets. Pairs with a true Muller plot
   (child bands nested in parent bands) in place of `explore.py`'s
   genotype stack.
2. **Executed-site mask.** Per genotype, which body bytes ever execute.
   `OrgStats` has per-op counters (`evo-core/src/sim.rs:40-69`) but no
   per-byte map was found. Separates neutral bytes from working code, and
   would show whether relabelled templates and any `drain` sit in code
   that runs.
3. **"Not checked" is not zero.** A pass over `analysis/` scripts so that a
   missing file, empty window or failed seed prints as not checked.
4. **Graded template sensing.** Fold biosim4's similarity sensor into the
   graded-defence hypothesis in `alien.md` §2.2: graded matching gives
   graded recognition as well as graded infection.
5. **Deaths after drain.** T12's cap leaves the victim one tick of upkeep,
   so it can still starve soon after. Count deaths within a few ticks of
   being drained apart from other starvation.
