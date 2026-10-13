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
| [T02](T02-cycle-theft.md) | `--cycle-theft-pct`, `--cycle-tax-pct`, counters, harness gate, E014 runner | nothing | not built |
| [T03](T03-template-ancestor.md) | `--ancestor tierra`, `--neighbours HEX`, E015 runner | T02's `exec_by_others` | not built |
| [T04](T04-snapshots-replay.md) | full-state snapshots, `--replay-from` | T02/T03 fields (or extend later) | not built |
| [T05](T05-measures.md) | `measures.py`: QNN, phylometrics, MODES, sites; baselines on E007/E012/E013 | T03's `--neighbours-pad-only` for sites only | not built |
| [T06](T06-lenski-lod.md) | line of descent with fitness per step, on E007's absorb sweep | nothing | not built |
| [T07](T07-density.md) | replicator density by uniform sampling (B0) | nothing | not built |

## Order

T01 is done (fails; see below). Now, in parallel where hands allow:
T02 (engine, Opus), T05 (analysis, Codex trial) and T06 (analysis,
Opus). T03 after T02. T04 before
E016's main stage, not before. T07 whenever a machine is idle; it
decides line B's route and nothing in line A waits on it.

Experiments: E014 pilot as soon as T02 passes its tests; E014 main
after T05's baselines exist (so the measures are applied to E014 on
their second use, not their first). E015 after T03. E016 after both.

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
- Host dies: the slowdown starves it through upkeep. Report the N at
  which it lives; if that is below 25, the rule needs a floor (a debit
  cap per tick, say half the budget), which is one more flag and a
  re-run of the gate, not a redesign.
- Host unaffected: `cycles_taken_m` says whether the intruder ran
  (if 0, the pad never entered: placement bug in the harness); if it
  ran and the host is unaffected, the debit is not reaching
  `run_tick`. Engine bug either way.

**E014 pilot** (3 seeds, 50,000 ticks, all arms).
- Population within E007's range at N ≤ 50 and `entered_children_ratio`
  between 0.3 and 0.8 (expected): calibrate the tax, start the main
  stage.
- Population collapses at N = 50: run the main stage at N ∈ {10, 25,
  40} instead and say so in the record; the dose prediction still
  applies.
- `entered_children_ratio` above 0.8 at N = 50: entries are too brief
  for the cost to bite (the fall-through intruder is not staying
  resident as E009b's reading assumed). Measure resident fraction
  (`exec_foreign / executed` > 0.9 at death among intruders). If it
  is low, E014 gate 2 cannot pass for want of a resident intruder, and
  the right move is to skip to T03 and run gate 2 with the template
  ancestor, whose parasite is resident by construction: that is E016
  without the separate E014 main stage.

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

**T05 shakedown fails** (the measures do not see E007's sweep): the
implementation is wrong; fix before E014 main, since the arms would
otherwise be judged by a blind instrument.
