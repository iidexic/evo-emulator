# Synthesis after the literature review (2026-10-13)

Status: a reading of everything in `docs/research/` (the two review
rounds, `literature.md` §1–§7, the seven `notes/recent-*` files, the
four original notes, `hypotheses.md`, E001–E013, the gap review and the
`drain` proposal) against the code as it stands at commit a03a80e, done
in one pass by Fable. Its job is to say what the evidence adds up to,
what that changes in the plan, and what the project would look like if
it were started today with this review in hand. PLAN.md §8 carries the
decisions; this file carries the argument. Nothing here is a result.

Inferences of my own are marked "(inference)" as the notes do.

## 1. What the whole review says, in ten findings

1. **Every task-free instruction substrate ends at "efficient
   replicator", and evo has reached that end.** Tierra under a constant
   slice: optimise to 22 instructions, then stasis ("there is just no
   need to do anything more complicated than copy yourself quickly",
   Ray 1995). Cosmos: more `et_collect` in the copy loop, then "steady
   microevolution" with no innovation. Avida with no rewarded tasks:
   complexity rose, then fell, then levelled (MODES, Dolson 2019).
   Squirm3, Evoloops, AlChemy: selection toward the smallest copier.
   evo: the absorb count sweeps from 64 to 112–127 inside 10,000 ticks
   in every seed, then nothing moves for 240,000 ticks (E007), length
   fixed at 21. This is not a tuning failure. It is the known endpoint
   of a world in which the only thing selection can see is cycle time.

2. **The only endogenous driver of complexity in this literature is
   coevolution with a parasite that costs the host.** Zaman et al.
   2014: EQU in 17 of 50 host populations with parasites, 0 of 50
   without; Kelley et al. 2026 replicate it (16 of 50). Tierra's
   keystone parasite doubled the number of coexisting size classes.
   Spatial Stringmol evolved self-scan and toggle defences only in runs
   with parasites, and lost them when parasites were absent. Bohm,
   Zhang & Dolson 2024: ecology at long filter depth peaks at an
   intermediate parasite cost. Environmental heterogeneity, drift and
   seasons have no such record anywhere (Ray's network Tierra: 2 to 3
   cell types; Sayama & Nehaniv 2024: dynamic environments "may not
   work for indefinitely long terms"). So in a world with no external
   task, parasites are not one interaction among several to get right.
   They are the lever.

3. **Where a charged host evolved a defence, the charge was graded and
   the host kept reproducing.** Avida: each parasite instruction costs
   a host cycle with probability 0.8, paid from a rate (merit), so an
   infected host runs at 20% speed and never starves. Kelley 2026:
   parasites steal 75% of the host's CPU cycles. Symbulation: theft
   from the update's income, never from stored points, capped at what
   is left. Johnson 2026: a death probability per stress event. Seoane
   & Solé: a reward pool. In none of them does a parasite drain a
   reserve the host needs to keep running. The two systems that charge
   a per-instruction store, Cosmos and evo, are both about one pass
   deep and both got nothing (`literature.md` §6.3.2, §7.2).

4. **evo's three cost rules failed for a reason the review now makes
   structural, not parametric.** Full charge (E008): the entered host
   dies in one pass and the killer profits. Split (E009): a cliff, no
   grade. Transfer (E010): intruders are not energy-limited, so profit
   does not multiply them. All three charged energy, and the host's
   energy is one pass deep. The `drain` proposal and PLAN §9 name "store
   depth" as the next parameter. §2 below argues that store depth as a
   cap cannot be reached in this world at all, which is why this
   synthesis proposes a different medium for the charge.

5. **evo's parasites are a placement accident, not a mutational
   neighbour of the ancestor's strategy.** E005: every parasite lineage
   is a body with a broken restart that falls off its own end into the
   body behind it; the main parasite in every E007 seed is a one-byte
   `pad`. Tierra's parasite 0045aaa was one mutation from the ancestor
   because the ancestor entered its copy procedure by template search,
   so losing the procedure made the search find a neighbour's. Cosmos
   made neighbours' code readable and got no parasites "because none
   was a single mutation from the ancestor" (Taylor 1999). evo's
   ancestor uses relative jumps and `self ; jmpa` and never searches,
   so "borrow a neighbour's procedure" is not in its one-hop
   neighbourhood. Literature item 12 (2026-09-30, "check that a working
   parasite is one or two mutations from the ancestor") was never done;
   E005 found the degenerate case instead. (inference) This is why the
   entered fraction is stuck at 7–14% under every rule: it is the
   geometric chance of a broken restart landing in front of a host, not
   a strategy that selection can amplify.

6. **A defence with no paying intermediate has no precedent of
   reachability, and the ISAL 2023–2026 proceedings do not change
   that.** Every defence in the Symbulation and Avida line is graded at
   each step by construction (task switch, tag bit, scalar fraction).
   Adaptive momentum (Bohm et al. 2024; Ferguson, Ofria & Bohm 2024;
   Gordon et al. 2025) crosses valleys of mildly harmful steps during
   sweeps, on rings, with large mutational targets per step; for a
   neutral path the limit is supply, and evo's supply per specific byte
   at a specific executed position is of order 10^-5 per birth (H14
   note, 2026-10-12). Stringmol 2021's six-stage path went through
   region-level rearrangements evo cannot make. So the plan must not
   wait for a five-byte self-scan to appear by itself. It must make a
   one- or two-step defence pay, as every system that got one did.

7. **The traced path to an evolved defence, with the fitness of each
   intermediate, is still nobody's result.** Lenski 2003 did it for a
   rewarded task; Ferguson & Ofria 2023 for associative learning (four
   lineages, replays); Croft 2024 looks one step back for a cooperative
   trait on pruned trees. Nobody has done it for a defence, in any
   substrate, and nobody has done any of it in a substrate with energy
   and ownership. evo records every birth with both parents and every
   genome with its parent, so the measurement is a query once a
   defence exists. The same tools give a cheaper first: the Lenski
   line-of-descent analysis of E007's absorb-count sweep, which no
   digital system has done for a physiological trait.

8. **The seedless-emergence line has a clean protocol and an open
   question.** Dušek et al. 2026: in BFF at 2^17 tapes and mutation 0,
   a replicator is discovered in 99 of 100 runs (median 2,453 epochs),
   takeover in 45 of 100; N and R regimes coincide per executed tape
   (1.60 and 1.61 × 10^8); uniform density 7.1 × 10^-11 per 64-byte
   program. Nobody has added energy with an off control (Jha 2026 added
   c = 1, ε = 24 without one), or ownership, write protection or death
   by energy to any soup. First-discovery time per execution is the
   outcome to report; U and N are the controls; the cubff fork has the
   regimes as flags. The hardware here (RTX 4070 SUPER, 12 GB; 24 CPU
   threads) runs it.

9. **Measures: one headline, several diagnostics, no snapshots.** QNN
   over `func_hash` per census interval as the single number; MRCA
   depth, ancestor count, mean and sum pairwise distance and mean
   evolutionary distinctiveness on individual-level trees as the
   sweep-versus-coexistence readout, always against a same-physics
   control because space moves them more than ecology (Moreno 2023);
   MODES change, novelty and ecology at two filter depths (N/5 and 2N),
   no MODES complexity headline; per-column entropy against per-site
   knockout to find sites selected only in the crowded world;
   pseudo-perplexity dropped. Sayama 2024 is the warning: "keeps
   changing" judged from snapshots was withdrawn by its own author.
   None of this exists as a script yet.

10. **The bar for the peer-reviewed neighbours is 30–50 replicates,
    10^5 or more updates, and a mortality-matched control** (Kelley 50,
    Johnson 30, Croft 30, Moreno 50; Johnson 2026's bottleneck control).
    evo's 10 seeds per arm is a third to a fifth of it. The simulator
    does 250,000 ticks in about 130 s on Linux and the machine has 24
    threads, so 30 seeds per arm is an hour, not a constraint.

## 2. Diagnosis: three structural facts about the standard world

**A. Nothing passes between organisms except code and placement.**
E011: persistent genomes take 97–99% of their income from `absorb`;
parasites spend a larger share of their instructions absorbing than
their hosts. There is no consumer mode because the physics has no
channel for it. Every result from E007 to E013 is a corollary.

**B. The host's energy reserve is one pass deep because the world
equilibrates there, not because the cap is low (inference).** The
store cap is 64 units per byte, 1,344 for a 21-byte body, yet hosts
hold 100–130 units (E010). The reason is proportional absorb on a
shared, depleting pool: the population grows until the ration a body
gets per `absorb` is what its cycle costs. E007's follow-up measured
exactly this: a K = 120 cycle costs about 645 units plus endowment and
upkeep, and the break-even ration is about 6.0 units against a maximum
of 8; the longer absorb phase won because it breaks even on a lower
ration. At that equilibrium no host banks anything, whatever the cap.
Raising sun or cap raises the population until the margin is zero
again. The systems in which a charged host survived (Avida merit,
Symbulation's 25 or 100 per update) pay each organism a fixed income
that neighbours cannot deplete. So "store depth as a parameter" (PLAN
§9, the `drain` proposal's condition 1) is not reachable by a cap or by
income scaling in this world. A charge on energy will always be
invisible or fatal here. Check before relying on this: the
distribution of `energy_m` and `max_energy_m` for replicator-class
bodies in E007's `orgs.csv` and `deaths.csv` against the cap; if
`max_energy_m` sits an order of magnitude below 1,344 in every seed,
the argument holds.

**C. The ancestor's addressing makes a strategic parasite unreachable
and a placement parasite inevitable.** Finding 5. The parasite
neighbourhood is a property of the ancestor's design, and the ancestor
was designed (2026-09-30) for brevity and a self-contained loop, not
for its mutational neighbours. Tierra's dynamics came from template
addressing; evo dropped it from the ancestor while keeping it in the
ISA.

Together: the project built the right instrumentation and the right
discipline around a world whose two interaction channels (energy
reserve, fall-through placement) cannot carry the dynamics it is
looking for. The fixes are small and specific, and both are physics
rather than tuning.

## 3. Decisions

### 3.1 The cost of intrusion moves from energy to time

New rule, `--cycle-theft-pct N` (name provisional): when organism X
executes an instruction at a byte owned by a living organism Y ≠ X, X
pays the energy as now, and Y's per-tick execution budget is debited
`floor(cost × N / 100)` in the same units the budget counts. The debit
is carried as a debt on Y and taken from its next tick's budget
(`left = cap − min(debt, cap)`), so Y runs slower while it is being
run and never dies of it. N = 0 is bit-identical to the current world.
Energy is untouched, so every ledger test stands.

Physical reading: energy is matter-like and conserved; the per-tick cap
is time, the organism's share of the machinery. A virus does not drain
a cell's ATP by instruction; it occupies its ribosomes. An intruder
running on a host's bytes occupies the host's cycles. This is Avida's
virulence (0.8) and Kelley's cycle theft (75%) in a shared-memory
substrate with ownership, where nobody has put it.

What it buys, against E008–E010: an entered host survives and
reproduces at (1 − N/100) of its speed for as long as the intruder is
resident, and a fall-through intruder is resident for life (its restart
returns it to the host). So the saving from ejecting an intruder is
large and lasts, which is the gradient E009b found missing ("an entry
costs at most one pass; the saving is an order of magnitude below the
five-byte cost"). At the entered fraction of 7–14%, N = 50 is an
average fitness cost of 3.5–7% against a six-byte eject's cost of about
1% of a cycle plus six bytes of upkeep.

Caveat (inference): at zero margin even a slowdown costs upkeep, about
6% of a cycle per extra cycle of delay at K = 120, so at N = 75 or 90 an
entered host may still starve slowly. The harness gate measures it,
and the slow death would be graded in time rather than a cliff, which
is still the condition the literature names. N ∈ {25, 50, 75} is the
sweep. The control arm is a random cycle tax on unentered hosts at the
entered hosts' mean rate, the analogue of Johnson 2026's bottleneck
control.

### 3.2 The ancestor becomes template-addressed

A second ancestor (`--ancestor tierra`, name provisional) in which the
copy procedure is entered by `searchf` on a label and returns by
`searchb` to the body's start label, so that the one-hop neighbourhood
contains a parasite that uses a neighbour's procedure. A candidate in
the current ISA, to be verified in the harness as the 2026-09-30
ancestor was:

```
L0:  nop0 nop0 nop1 nop1 nop0        ; start label
     lit C -4
     lit A K
     absorb ; dec A ; skipz A ; jmpr C
     searchf nop0 nop1 nop0 nop1 nop1 ; D = address past L1
     jmpa D
L1:  nop1 nop0 nop1 nop0 nop0        ; procedure label (complement of the template)
     self 0 ; swap B ; swap C        ; B = start, C = len
     alloc C                         ; A = child start
     lit D -4
     copy ; dec C ; skipz C ; jmpr D
     lit A E ; divide A
     searchb nop1 nop1 nop0 nop0 nop1 ; D = address past L0
     jmpa D
```

45 bytes, 20 of them label nops (Tierra: 80 and 48). Two search costs
per cycle of about 2 and 3 units. A single bit flip in L1 (`nop0` and
`nop1` differ in one bit) makes the body's own procedure invisible to
its own search, which then finds the next L1 within 512 bytes: a
neighbour's. Under `self` = executor the neighbour's procedure copies
the intruder, and the neighbour's `searchb` returns the intruder to
the neighbour's L0, so it stays resident: Tierra's parasite, one
mutation away, and the resident intruder that §3.1's rule taxes. A
shorter parasite then has something to gain by shedding its dead
procedure, which is Tierra's 80-to-45 history and the profit E010
could not create. A host, for its part, has one-mutation defences
available in principle (a label longer than the template a parasite
carries; the `self 1` eject), and the experiment is whether it finds
one.

Before any world run, the whole single-mutant neighbourhood of the new
ancestor (45 × 255 substitutions plus 45 deletions, about 11,500
bodies) is classified in the two-genome harness before an ancestor.
That is literature item 12 done properly, and a number in itself: how
many one-hop parasites each ancestor has. The current ancestor's
neighbourhood is run the same way as the control (expected: zero
searching parasites, some fall-through ones).

Nop inflation becomes live with 20 label nops per body (Amoeba's
emergence rate fell once nops passed 25% of memory); the ring is
seeded, not seedless, so it is a thing to log, not a blocker.

### 3.3 `drain` and store depth are demoted, not dropped

`drain` stays the candidate mechanism for a consumer mode (H2), but
after the cost-of-time rule, and in the form the literature has
precedent for: a take from the victim's income or proportional to its
store, capped so it cannot kill (Symbulation's nutrient mode, Jha's
STEAL at α = 0.8). Store depth as a cap sweep is dropped on the
argument of §2 B. The proposal file gets a dated note.

### 3.4 Phase 3 as written is retired

2D torus, seasons, slow drift: no reviewed system shows them doing
anything for open-endedness, Ray doubted 2D memory, BFF's 2D grid
slowed takeover, and on a ring space already moves every phylometric
more than ecology does. H9 stays open as a hypothesis with its
three-way control, unscheduled. The ring with locality is the world.

### 3.5 Seeds, controls, measures

Thirty seeds per arm from E014 on. Every arm with a cost has a
cost-matched control (random tax, random kill). `analysis/measures.py`
(finding 9) is built before E014 is run and applied to E007, E012 and
E013 as the baselines, so that the first use of the measures is not on
the experiment they are meant to judge. The Lenski line-of-descent
analysis of E007's absorb-count sweep is run now, as the method's
shakedown.

### 3.6 Two research lines, one engine

**Line A, coevolution (the E-series continues).** E014: `--cycle-theft-pct`
gated in the harness (an ancestor with a resident `pad` at N = 50
survives and makes about half its children) and then by E009b's
injection test (the six-byte eject maintained where INERT6 is lost).
E015: the template ancestor's neighbourhood and its world dynamics
(parasite share, resident fraction) without the cost. E016: cost ×
ancestor, 30 seeds, 250,000 ticks, de novo defence search with Croft's
look-back on every first complete defence, time-to-loss per lineage,
replays from full ring snapshots. If a defence appears, its path with
harness fitness at every step is the result nobody has (finding 7). If
none appears under a graded, survivable, lifelong cost with a
one-mutation parasite, that is a clean negative against the whole
Tierra-with-energy premise and is also worth writing up.

**Line B, emergence rule by rule (Phase 4).** B0 now: evo's own
replicator density by uniform sampling with a short harness (the H3
search in Dušek's U form), and the ancestor-neighbourhood count from
§3.2. B1: reproduce Dušek on the local GPU (20 seeds first). B2: add
rules to the cubff fork one at a time with an off control each:
start-execution head position, per-op energy with income and death at
0 (Jha's c = 1, ε = 24 plus an ε sweep and ε = ∞), then ownership and
write protection (write only into dead tapes, with death by energy
freeing them). Primary outcome first-discovery time per executed tape;
U and N as controls; operator frequencies logged. B3: evo's ISA on the
same protocol in a soup mode of `evo-core`. Line B is the more certain
paper: every outcome is a number and the question is open in a line
that is active right now. Line A has the higher ceiling.

Both lines share the engine, the instrumentation, the measures script
and the record-keeping. The hobby and the research are the same repo;
the research discipline is the seed count, the controls, the measures
and the write-up.

### 3.7 Engine work implied

- `--cycle-theft-pct N` and a `cycle_debt` field; `--cycle-tax-pct N`
  random control; counters `cycles_lost` and `cycles_taken`.
- `--ancestor tierra` (the §3.2 body as `sim::ancestor_t(k, e)`), and a
  harness mode `--neighbours HEX` that classifies every single mutant
  of HEX alone and before an ancestor.
- Full-state snapshots (world bytes, ownership, organism table with
  registers, PRNG state) at census ticks, so a run can be replayed from
  tick T with a different seed from T on. Needed for replay-based
  potentiation (Escondo & Ferguson 2026: seed replays from full
  snapshots, not lineages). Listed in PLAN §7 since 2026-10-03 as "not
  yet".
- A soup mode for line B3 later.

## 4. If the project were started today

What I would build, given this review, with the aim of advancing the
field rather than only running a world.

1. **Question first, substrate second.** Two questions are live and
   publishable: which physics rules kill seedless emergence, and
   whether an evolved defence can be traced with the fitness of its
   intermediates under a costed, survivable parasitism. Everything in
   the engine is chosen to serve one of them.

2. **One engine, two arenas, rules as flags from day one.** A ring with
   locality and a random-pairing soup in the same Rust crate, sharing
   the VM, the recorder and the measures, so that the BFF protocol is a
   configuration rather than a separate harness. Energy on or off,
   ownership on or off, write protection on or off, the cost medium
   (energy, cycles, none), the start-execution rule and the income
   regime (shared depleting pool or fixed per-organism allowance) are
   all switches, because the rule-by-rule question needs each of them
   as an arm and the ring needs them as controls.

3. **The ISA is chosen by measurement, not argument.** Before anything
   else, two or three candidate encodings get a uniform-sampling
   density screen (Dušek's U regime with a short behavioural test) and
   a single-mutant neighbourhood count for a candidate ancestor. The
   one with the highest replicator density and a one-hop parasite is
   the ISA. evo spent two weeks on an ISA argued from robustness and
   never measured its density; the density is a day of CPU.

4. **The ancestor is designed with its neighbourhood.** Template
   addressing for procedures, so parasites and hyper-parasites are
   one or two mutations away, as in Tierra; its full single-mutant
   neighbourhood classified before the first world run.

5. **Time is the medium of interaction cost; energy is metabolism.**
   Intruders consume the host's cycles. Energy charges on reserves are
   not built, because a shared depleting pool equilibrates every host
   to zero margin (§2 B).

6. **Instrumentation, measures and replay before E001.** What evo did
   (both parents per birth, canonical hashes, census, world snapshots,
   determinism) plus full-state snapshots for replay and the measures
   script, so every experiment reports QNN, phylometrics against its
   control, and MODES at two depths from the first run.

7. **Thirty seeds, pre-registration, matched controls, from the
   start.** As evo does, with the seed count raised.

8. **Order of experiments.** Density screen; ancestor neighbourhood;
   persistence; parasites; cost medium; defence path; then the
   emergence ladder in the soup arena.

How far evo is from that: not far. Items 6 and 7 are largely in place
and are the part most projects never build. Item 2 is missing the
soup arena and two switches (cost medium, income regime). Items 3 and
4 were skipped and are the reason the parasite line stalled; both are
one to two weeks of work on the current code. Item 5 is one flag. No
restart is warranted; the engine's architecture is what the ideal
would have, and the differences are additive. The sequencing is what
the ideal does differently, and the plan in §3 is the current project
re-sequenced.

## 5. What is not changed by this review

- The physics principles (§3 of PLAN.md): evolvable encoding,
  existence costs, conservation, mutation in the substrate, no reaper,
  determinism, observability first. All still supported, and the last
  two are the project's edge.
- The pre-registration discipline and the hypotheses log.
- The E004 standard world as the baseline for everything on the ring.
- Executor-pays for energy; `self` = executor by default.
- Write protection on by default (E012 says it does not matter here;
  it may once bodies are worth overwriting, and it is the Tierra
  condition).
