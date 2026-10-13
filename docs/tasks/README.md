# Task specs and the decision tree

One file per engine or analysis work item from PLAN.md §8.6, written
2026-10-13 for the builder (Opus or Codex; a second model reviews;
Fable reads the diff summary, per PLAN §12 and the delegation split).
Each spec fixes interfaces, semantics, tests and what to report back.
The experiment protocols (E014, E015) sit inside the task that builds
their engine piece; the experiment records are written from them
before the runs, as always.

| task | what | depends on | status |
|---|---|---|---|
| [T01](T01-reserve-check.md) | E007 reserve check: does any host bank energy? | nothing | done 2026-10-13 (Opus, laptop; `654783b`): **fails** in every seed; branch below taken |
| [T02](T02-cycle-theft.md) | `--cycle-theft-pct`, `--cycle-tax-pct`, counters, harness gate, E014 runner | nothing | built 2026-10-13 (`0ce3338`); gate 1 passed at N = 50 (0.465, host alive; dies from N = 51 in the harness); E014 pilot run, skip branch taken, no main stage |
| [T03](T03-template-ancestor.md) | `--ancestor tierra`, `--neighbours HEX`, E015 runner | T02's `exec_by_others` | not built |
| [T04](T04-snapshots-replay.md) | full-state snapshots, `--replay-from` | T02/T03 fields (or extend later) | not built |
| [T05](T05-measures.md) | `measures.py`: QNN, phylometrics, MODES, sites; baselines on E007/E012/E013 | T03's `--neighbours-pad-only` for sites only | built 2026-10-13 (Codex, `0d0c36b`; Opus review: numbers match independent recomputation); shakedown criteria 1 and 2 rewritten (spec §4 amendment), fixes in §4.1 pending |
| [T06](T06-lenski-lod.md) | line of descent with fitness per step, on E007's absorb sweep | nothing | built 2026-10-13 (`2f27841`); E007 record follow-up; sweep step deleterious in the harness in 8 of 9 seeds, D-before-B in seed 3 |
| [T07](T07-density.md) | replicator density by uniform sampling (B0) | nothing | not built |

## Order

T01 is done (fails; see below). Now, in parallel where hands allow:
T02 (engine, Opus), T05 (analysis, Codex trial) and T06 (analysis,
Opus). T03 after T02. T04 before
E016's main stage, not before. T07 whenever a machine is idle; it
decides line B's route and nothing in line A waits on it.

Experiments: E014 pilot as soon as T02 passes its tests (done
2026-10-13; it took the skip branch, so there is no E014 main). E015
after T03. E016 after E015 and T05's baselines (so the measures are
applied to E016 on their second use, not their first).

## Expected path, and what changes at each gate

The branches below are planned so that the next step after any
outcome is already decided; where an outcome would call for a
redesign rather than a re-sequence, that is said and the redesign is
left for then.

**T01, reserve check.**
- Holds (expected): cite the numbers; nothing moves.
- Partial or fails: `drain`'s condition 1 stands for the bodies that
  bank. T02 still goes first (its case is from the literature, not
  from the margin argument), and E016 gets an income-take `drain` arm
  on the list. E010's "not energy-limited" reading is re-read against
  the banking genotypes.
- **Outcome 2026-10-13: fails** (`analysis/e007_reserve.py`, E007
  record follow-up, commit `654783b`). Against the rule in T01 §3:
  reproducers' median `max_energy_m` is 279–283 units (rule: ≤ 134),
  p90 825–939 against a cap of 1,344 (rule: p99 < 448), and 34–35% of
  replicator absorbs are cut by the cap (rule: < 1%; fails above 10%).
  Active hosts hold a median of about 600 units, a fifth at the cap;
  42% of living replicator-class bodies are stalled at the cap and
  non-reproducing. A pass costs 787–798 units, so the cap is 1.7
  passes. What this changes: nothing in T02–T07's build order. E016
  gains the income-take `drain` arm as planned, now as a live
  comparator rather than a fallback (an energy charge of a tenth of
  income is survivable at a 600-unit store and a 790-unit pass). The
  stalled-at-cap bodies are the natural `drain` target and E016's
  record should say whether the arm selects for draining them. The
  store-depth sweep is reopened as a question, not a task; if it is
  brought back it needs a `--store-cap` flag (a T08, one field and one
  CLI flag, not specified until E016's design is written).

**T02 gate 1, the harness** (pad before the ancestor at N = 50).
- Host alive, 35–65% of its children (expected): proceed to the E014
  pilot.
- **Outcome 2026-10-13: passed**, ratio 0.465 at N = 50, host alive
  with 223 units left; 0.691 at N = 25, dead at N = 75 and at every N
  from 51 up (checked 51–59). The rates run as 1 − N/100 against the
  N = 0 host, as H16 says. The harness host is entered every tick, so
  the world's t50 arm is expected to sit above this, but near the
  margin; if the pilot's population collapses at N = 50 the branch
  below applies without further checking.
- Host dies: the slowdown starves it through upkeep. Report the N at
  which it lives; if that is below 25, the rule needs a floor (a debit
  cap per tick, say half the budget), which is one more flag and a
  re-run of the gate, not a redesign.
- Host unaffected: `cycles_taken_m` says whether the intruder ran
  (if 0, the pad never entered: placement bug in the harness); if it
  ran and the host is unaffected, the debit is not reaching
  `run_tick`. Engine bug either way.

**E014 pilot** (3 seeds, 50,000 ticks, all arms).
- Population within E007's range at N ≤ 50 and `entered_rate_norm`
  between 0.3 and 0.8 (expected): calibrate the tax, start the main
  stage. (Amended 2026-10-13: `entered_children_ratio` is confounded
  by lifespan, 3.78 at no cost in the smoke run; the governing
  measure is the per-tick rate normalised to the `n0` arm. T02 §4.3.)
- Population collapses at N = 50: run the main stage at N ∈ {10, 25,
  40} instead and say so in the record; the dose prediction still
  applies.
- `entered_rate_norm` above 0.8 at N = 50: entries are too brief
  for the cost to bite (the fall-through intruder is not staying
  resident as E009b's reading assumed). Measure resident fraction
  (`exec_foreign / executed` > 0.9 at death among intruders). If it
  is low, E014 gate 2 cannot pass for want of a resident intruder, and
  the right move is to skip to T03 and run gate 2 with the template
  ancestor, whose parasite is resident by construction: that is E016
  without the separate E014 main stage.
- **Outcome 2026-10-13: this third bullet** (record
  `docs/research/experiments/2026-10-13-e014-cycle-theft.md`).
  Population 930–985 at every N; `entered_rate_norm` as built 1.02
  at N = 50; resident intruders 7.8–10.4%. E014 main is not run; gate
  2 moves into E016 with the template ancestor. Two things the pilot
  adds. First, on reproducing hosts (`offspring` > 0, `age` > 50) the
  cost is real and graded: 0.97 / 0.90 / 0.85 at N = 25 / 50 / 75,
  1.0 under the tax, seeds within ±0.02; hosts run at 28 of 32 units
  per tick, so the mechanism is right and only the dose is small
  (median entered reproducer debited 2% of its cap at N = 50). E016's
  `theft` arm stands at N = 50 with that as the expected effect on the
  std ancestor. Second, the eject and the inert are lost within 2,000
  ticks of injection at every N including `n0`, as in E009b, with no
  separation between them: an injection test of a defence must put it
  on the evolved background or at tick 0. The runner's
  `entered_rate_norm` is confounded (0.54 raw at no cost) and must be
  recomputed on reproducers before any reuse (T02 §4.3).

**E014 main, gate 2** (30 seeds).
- Eject maintained at N = 50, lost under the tax (expected, the
  H16 result): E015, then E016 with N = 50.
- Eject lost at every N, tax indistinguishable: H16 refuted in this
  geometry. Two readings, told apart by the entered fraction: if
  under 10%, the gradient is too rare to select on (go to T03, as in
  the pilot branch); if above 10% and the eject is still lost, the
  eject's cost is higher than estimated or the saving is not realised
  (check `cycles_lost_m` per entered host against the model's 3.5–7%).
  Either way E016 still runs, because the template ancestor changes
  the entered fraction, and E014's negative is reported as such.
- Eject maintained under the tax as well: the tax is selecting for
  something (length? the eject's `jmpa D` behaviour on its own?).
  Audit before any other step; compare INERT6 under the tax.

**T03, harness and neighbourhood.**
- `ancestor_t` replicates at some K ≤ 128 and its neighbourhood has
  `parasite_jump` rows at positions 20–24 (expected): persistence
  gate.
- No K makes it a replicator: the body is wrong somewhere the
  semantics check missed; fix the body (candidates in order: a
  shorter label of four nops; `searchf` for the return as well; drop
  the `lit C -4` and reuse D). Harness-only work, a day.
- Replicates but no `parasite_jump` row: the neighbour's procedure is
  not copying the intruder. Check `self 0` under the executor rule in
  the harness placement (the mutant must be *before* the host for
  `searchf`'s forward scan, which the harness does), then the
  `searchb` return. If the ISA's search really cannot give a one-hop
  parasite, H17 is refuted on the ISA and PLAN §9's addressing
  question is the next design item; E016 then runs with the std
  ancestor and the cost alone.

**E015 persistence and world.**
- Persists in ≥ 8/10 and parasite share rises above 5% (expected):
  E016.
- Does not persist: K up, then `--sun` as a declared arm; if neither,
  the body is too expensive for this world and the ancestor needs
  shortening (labels of four nops save 8 bytes) before E016.
- Persists, parasites stay near 1%: placement, not addressing, limits
  entries (H17's second refutation). E016 still runs; its entered
  fraction is then the std ancestor's, and the design's expectation is
  revised down in the record before the main stage.

**E016, the defence search** (cost × ancestor, 30 seeds).
- A defence appears and is maintained: T06's line of descent on it,
  Croft's look-back on the first complete one per seed, T04 replays
  from the snapshot before its first appearance with new seeds
  (potentiation). This is the write-up.
- None in 30 seeds: a clean negative under a graded, survivable,
  lifelong cost with a one-hop parasite. Also a write-up, with the
  neighbourhood counts as the reachability argument. The next design
  question is then whether any one-mutation defence exists for the
  template body (a longer label; `self 1` eject) and what each costs
  in the harness, which the neighbourhood file already answers for
  substitutions and deletions, and which needs insertions added to
  `--neighbours`.

**T07, density.**
- Within two orders of BFF (expected only for short bodies, if at
  all): B3's soup mode is worth building.
- Far below for every LEN ≤ 32: line B goes through the cubff fork
  with evo's rules (B1, B2), not evo's ISA. Line A is unaffected.

**T06 outcome 2026-10-13.** The method works at 1.5–1.9 s per line.
What it found changes E016's reading rule, not its design: the
harness grades the sweep step as deleterious in 8 of 9 seeds because
the longer absorb phase wins on a lower ration, which a lone body with
a full pool never sees. So for E016 a defence step graded `neutral` or
`deleterious` alone is not evidence against it; the world-fitness
column is the one to read first, and the harness column second. T06's
spec §4 said this as a caveat; it is now the rule. The follow-up
(`95d6e55`) sharpens it: the 25,000-tick world mean per genome did
not resolve the sweep either (the 96-count genome's children per
death rise in 2 seeds and fall in 4, all within 0.89–0.98), so for
E016 the world column is read in bins of a few thousand ticks against
contemporaries, not as a window mean. And most beneficial/deleterious
pairs on the line are break-and-repair (178 of 196 breaks are
repaired at the next step, 195 of 196 repairs carry no copy error:
somatic damage passed on at `divide`, then the undamaged body again),
so E016's step counts are read after pairing those off; between
genomes that both have children the lines hold 65 B and 90 D. Also: the desktop's `runs/e007/std/` is
the killed first launch (to tick ~145,000, no `genomes.csv`); complete
reruns are at `runs/lod/e007/s<seed>/`, and `runs/e012`, `runs/e013`
are not on the desktop at all, so T05's baselines on those two run on
the laptop or after a copy.

**T05 shakedown fails** (the measures do not see E007's sweep): the
implementation is wrong; fix before E014 main, since the arms would
otherwise be judged by a blind instrument.
- **Outcome 2026-10-13: the branch is not taken.** Codex's build is
  right where Opus recomputed it independently (QNN, SPD, MPD, ED,
  MRCA, MODES on E007 seed 1, every value equal). The criteria were
  wrong: criterion 1's pass was the founder phase (QNN peaks at ticks
  500–1,500 while the population grows from 1 to 900; the absorb
  sweep, spread over many `func_hash`es, moves `qnn` by 0.001–0.002,
  the stationary level), and criterion 2's fail is a true result (the
  final tips descend from two generation-1 lines that each gained
  absorb ≥ 96 on their own and never merged; the run reaches
  generation 1,012, under 2N ≈ 1,870). Both rewritten in T05 §4:
  trait-level grouping (`--group absorb_class`) is the sweep
  detector; QNN over `func_hash` is blind to a trait sweeping on many
  backgrounds, which E016's reading rule now has to carry. Code fixes
  (`--every` crash, `--knockout` exit, thin tests, ED stem,
  `ancestor_count`) listed in T05 §4.1 for an Opus follow-up.
