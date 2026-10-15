# What to build after E016: the `drain` decision and its alternatives (memo, 2026-10-15)

Status: a decision memo from Fable for Derek, written after E016's
results and before the pending pieces (replays, T10's control, T11's
closure screen) are in. It frames the choice, says what each branch
would and would not find, and recommends. Derek decides. The goals it
is judged against, in Derek's order of 2026-10-15: (1) work at the
front of the field; (2) more complex and more varied evolution; (3)
more ways to gather and use energy. A consumer mode (`drain`) is a
means to those, not an end.

## 1. Where E016 leaves the question

E016 asked whether a graded, survivable, lifelong cost of parasitism
selects a defence in a world whose ancestor has a one-hop parasite.
What it found (`e016-writeup-2026-10-15.md`):

- The one defence class, immunity to the label parasite (Tierra's
  relabelling, a redundant label, or the loss of the label; record
  §8.8), arises by mutation supply with or without the cost; the cost
  raises its share by a third.
- No tolerant defence in 150 runs.
- The cost at N = 50 is near-sterilising for an entered template
  host in the harness (1 child against 119), survivable only for the
  population. The literature's condition (an entered host reproduces,
  more slowly) held at the population level and not for the
  individual. The premise was not cleanly tested for this body.
- The matched control failed; T10 redoes it.
- The world under the template ancestor is far from E007's stasis:
  parasite share 20–30% of births, 43% of replicator deaths entered
  under the cost, thousands of relabelling origins per run, the
  class's lineages turning over in thousands of ticks. That is more
  turnover and more interaction than any earlier arm. It is not more
  complexity: what was selected is a label change, a redundant label,
  or the loss of the label and the search with it (bodies of 32–36
  bytes, 40% of the immune class's births; T11 §2, record §8.8). The
  world's answer to a parasite by search is to stop being searchable,
  which is the efficient-replicator endpoint by another route.

So the two-channel world (code and placement, now with a cost in
time) does the thing the literature says such worlds do: a parasite,
an immunity, an arms race of labels. It has not produced anything
with a second step. The question for the next build is what would.

## 2. The three branches

### A. Build `drain` now (E018: an energy channel between organisms)

The form with precedent (`literature.md` §7.5; synthesis §3.3): a
`drain` instruction that takes from a victim within locality, either
a fraction of the victim's income that tick or a fraction of its
store, capped so it cannot kill; lossy; the drainer's gain capped by
its own room. Opcode placed on purpose (Hamming distance from
`absorb` decides whether drainers arrive at once or never; proposal
condition 2). Gated in the harness (a one- or two-mutation drainer
next to the ancestor out-replicates it; a drained host survives).
Then 30 seeds × arms (off; on at two takes; two opcode placements if
the budget allows), on the template ancestor at sun 2, with the
measures.

What it would find:

- Whether a consumer mode exists in this world at all (H2, E011's
  negative turned into a test). A yes is a second trophic level in a
  task-free program substrate with energy conservation, which nobody
  has shown; Tierra had no energy, Avida's parasites take cycles,
  Jha 2026's STEAL is in a soup without ownership or a store.
- Whether a drained host evolves a defence (`guard` is held back, so
  the only defences are behavioural: move, shorten, absorb faster).
  Under the reserve argument (synthesis §2 B, qualified by T01: hosts
  are 1.7 passes deep, a fifth at the cap) a store take that cannot
  kill is survivable by construction, so this time the individual
  condition holds.

What it risks: the proposal's own condition 1 says that on the
current store a drain is predation or nothing unless it is capped
small, and a capped-small drain may not pay against `absorb` at sun
2, where the pool is rich. If drainers never arrive or never pay, the
result is a harness negative in a week and a world negative in two.
That is reportable but thin. The 2 × 2 with store depth needs a
`--store-cap` flag that does not exist (one field).

Cost: a week of spec and build (opcode, target rule, ledger columns,
tests, harness gate), a day of world runs, a week of analysis and
record. Three to four weeks to a result with the measures.

Against the goals: (1) novel if positive, routine if negative; (2) a
consumer mode is the first non-replicator role the world could have,
which is the kind of variety wanted; (3) directly a new way to gather
energy. Highest ceiling, highest variance.

### B. Close line A cleanly, then line B (emergence rule by rule)

Finish what E016 opened: T10's control (E017, 30 runs, a day), T11's
closure screen (a day), a lower-N arm for the template body (N = 10
and 25, 60 runs, a day) so the premise is tested where the entered
individual survives, the replay table, the figure set, the paper.
Then line B: evo's replicator density (T07, B0), Dušek's protocol on
the GPU (B1), rules one at a time with controls (B2). Line B's
question (which physics rule kills seedless emergence) is open,
active this year, and every outcome is a number (synthesis §3.6:
"the more certain paper").

What it would find: a complete E016 paper with a readable control
and a tested premise; then the first rule-by-rule emergence study,
which no one has done (`literature.md` §6.3.3).

What it risks: line A ends as a negative-with-a-method paper and the
world stays at label arms races; nothing in B makes evo's ring more
complex. The GPU work is a new codebase (the cubff fork) for two
months.

Cost: two weeks to a submittable E016; then B0 a day of CPU, B1 two
weeks, B2 a month or more.

Against the goals: (1) the surest route to two publishable results;
(2) does nothing for variety on the ring; (3) nothing.

### C. A second energy source rather than a second channel

Derek's third goal, read on its own: more ways to gather energy. The
candidates with a physical reading and no prior art in this
substrate:

- **Scavenging**: a dead body's unspent store and its bytes carry
  energy that an `absorb` on debris (or a `scavenge` op) can take.
  Today a dead organism's energy is lost and its bytes decay. This
  is the producer-to-decomposer link, with precedent in Avida's
  resource models only indirectly. It is a channel that does not
  need a living victim, so it cannot be predation, and it rewards
  being where things die (crowded patches), which the current world
  punishes (E003).
- **A second, concentrated, patchy resource**: a few patches with a
  richer pool or a resource that only a longer loop can tap
  (heterogeneity in resource type, not in time). The literature has
  no record of heterogeneity producing open-endedness (PLAN §8.1,
  Phase 3 retired), so this is the weakest.

What it would find: whether a second income makes two metabolic
strategies coexist (absorber and scavenger), which is a producer and
consumer split without an attack. Nobody has shown a decomposer
niche emerging in a program substrate. A negative (everyone absorbs,
nobody scavenges) is as thin as A's negative.

Cost: scavenging is a smaller engine change than `drain` (no target
rule, no victim, the ledger already exists for debris), a week to a
gated result.

Against the goals: (1) novel if positive; (2) a second role without
needing a defence to co-evolve first; (3) literally the goal.

## 3. What the literature says will drive complexity here

One finding governs (synthesis §1 items 1 and 2): task-free
instruction substrates end at the efficient replicator, and the only
endogenous driver of complexity on record is coevolution with a
parasite that costs its host in a graded, survivable way. E016 now
has that parasite and that cost, and got Tierra's result. The step
the literature points to after immunity is a **hyper-parasite** (a
body that exploits the parasite) and a **second interaction channel
that is not code**: in Tierra the arms race went immunity,
hyper-parasites, social hyper-parasites, cheaters, over several
layers of code interaction alone. evo has not looked for
hyper-parasites in E016's data at all. That is free: the
neighbourhood screen and `defence.csv` can be re-read for bodies
that profit from a resident parasite (a relabelled body whose
parasite copies it, then the parasite's own children are hosts of
the relabelled body: the `parasite_jump` rows at the new labels say
whether that is one mutation away).

`drain` is the second channel. Its evidence base is indirect: no
system has an energy take between organisms under ownership and a
store; the systems with income takes (Symbulation, Seoane & Solé)
got scalar defences, not code. The honest statement is that `drain`
is the untested design with the best physical reading, not one the
literature predicts will work.

## 4. Recommendation

Do B's first two weeks regardless: E016 is a paper only with the
control, the closure measurement and the lower-N arm, and those are
cheap. In parallel, spend the engine time on **A, in the narrow
form**: `drain` as an income take capped at a fraction of what the
victim absorbed that tick (so it cannot kill and cannot drain an
idle body), opcode one flip from `absorb` as the primary arm and
four flips as the second, gated in the harness. That gate takes a
week and says whether drainers can arise and pay at sun 2 before any
world run is committed. If the gate fails, run C's scavenging
instead, which needs no victim and reuses the debris machinery. Line
B waits for the engine time to free, with T07 (a day of CPU) run
now because it decides B's route and costs nothing.

Why A over C first: A tests a channel between living organisms,
which is what every published complexity driver has; C tests one
with the dead, which nothing in the literature bears on either way.
A's negative is a known result (predation or nothing); C's negative
is only a shrug.

Why not A in the wide form (store take, store-depth 2 × 2): T01
showed the cap binds for a fifth of hosts and the reserve is shallow;
a store take is the E008–E010 family again with a different name,
and three negatives from that family exist. The income take is the
form every system where it worked used.

What I would not do: run more arms of E016's shape (other N, other
labels) before the control is readable. T10 says whether the
one-third effect is real; until then every further theft arm is
reading an uncontrolled number.

### 4.1 Addendum, the same night

T12 was built and gated within hours (branch
`worktree-agent-af767620b674b761b`, spec §5). Gate G2 **fails for the
tierra body at sun 2 at every P and L**: a 10% income take kills the
victim even from a full store, because the body is at break-even and
the spec's floor (one tick's upkeep) leaves it unable to afford its
next `absorb`; at P = 5 the victim lives and the take is 1.7% of the
drainer's income, so draining buys nothing. The same margin that made
the seven-byte eject unaffordable (E016 record §8.9) makes the victim
unfarmable. A second G2 pass against bodies with slack (the std
ancestor at sun 1, where hosts bank 600 units; tierra at sun 4) is
running; if drain pays and the victim lives there, E018 runs on the
std body in the standard world (H2's home) rather than on tierra at
sun 2, and if not, branch C (scavenging) is next as §4 says. Either
way the engine piece is built and flag-off bit-identical.

## 5. What Derek decides

1. A (narrow `drain` gate) in parallel with B's two weeks: yes or no.
2. If no to A: C (scavenging) or straight to line B.
3. The lower-N arm for the template body (N = 10, 25; 60 runs):
   worth a day? I say yes, it is the premise's clean test.
4. T07 now on idle CPU: yes or no. I say yes.

Not needed from Derek: the T10 pilot and T11 (already building), the
replay table, the write-up's figure set (Fable and Opus).
