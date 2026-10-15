# T12. `drain` in the narrow form: an income take that cannot kill, gated in the harness

Status: specified 2026-10-15 (Fable; Derek accepted the memo's
recommendation the same night: `docs/research/drain-decision-memo-2026-10-15.md`
§4). Built 2026-10-15 (Opus, engine commit `724f91d`, gate G1/G2 in
the commit after it; branch `worktree-agent-af767620b674b761b`, not
merged; four deviations from §1, listed in §5). G1 and G2 run (§5):
**G2 fails** at every tabled (P, L) under both opcodes: the drained
ancestor dies before its first child from P = 25 (from P = 10 in
fact); at P = 5 it keeps all 119 births but the drainer gains under
2% of its income by `drain` and makes exactly its lone count. G3 not
run. pseudo.py's `drain` and the `docs/instrumentation.md` rows not
done. Builder: Opus. Argument: PLAN §5.5 (the energy
channel between organisms as the diagnostic for trophic levels),
`drain-proposal-2026-10-12.md` (conditions 2–4; condition 1, store
depth, is dropped per synthesis §3.3 and T01), `literature.md` §7.5
(the form with precedent: a take from income, capped so it cannot
kill; Symbulation's nutrient mode, Jha's STEAL, Seoane & Solé).
Depends on nothing in the engine; E018 (the world runs) waits on the
gate in §4 and on E017's result for its arm list. Scope here: the
rule, the engine, the harness gate, the neighbourhood count. The
world experiment is pre-registered separately once the gate passes.

## 1. Rule

A new instruction `drain`. When organism X executes it at IP:

1. **Target.** The owner of the byte at address A (the register
   `load` and `store` use), if that owner is a living organism other
   than X and the address is within `locality` of IP. Otherwise the
   op does nothing but set the fail flag and cost its energy. (The
   register form, not "nearest body": a drainer must address its
   victim, as `copy` must address its source, so a drain loop is a
   program and not a reflex, and a flipped `absorb` in a loop that
   never sets A drains nobody. Proposal "to decide", target.)
2. **Amount.** `take = min(victim.income_prev_m × drain_pct / 100,
   victim.energy − victim.upkeep_tick_m, drainer_room)`, floored at
   0, where `income_prev_m` is the victim's `absorb` gain over its
   previous whole tick (a new per-organism field, rolled at the start
   of each of its turns), `upkeep_tick_m` is the victim's upkeep for
   one tick (`upkeep_per_byte × len`), and `drainer_room` is X's
   store cap minus its energy. The second term is the cannot-kill
   clause: the victim keeps enough to pay its next upkeep, so no
   `drain` ever starves a body that would otherwise have lived
   through the tick. The take is from the victim's store, sized by
   its income, so a body that absorbed nothing last tick yields
   nothing: an idle or starving host is a poor target, as a dead
   one is.
3. **Loss.** The victim loses `take`; X gains `take × (100 −
   drain_loss_pct) / 100`; the rest dissipates (counted into the
   patch's `absorbed`-style sink column so the ledger balances).
4. **Cost.** `cost_drain` = `cost_absorb` (same instruction cost;
   the difference between absorbing and draining is the yield, not
   the price). Executor pays, as always.
5. **Opcode.** Two placements, both built, chosen by flag:
   `--drain-op 23` (one bit from `absorb` = 22: every absorb loop is
   one flip from a drain loop) and `--drain-op 25` (four bits: a
   drainer must be assembled). Default: the slot stays `pad`
   (`drain_op = 0` means off), so every existing run is bit-identical
   and every pinned hash holds. `--drain-pct P` (default 50) and
   `--drain-loss-pct L` (default 50). The three flags go in
   `Config::fields()`.

Physical reading, for the doc comments: energy is matter and
conserved; `absorb` is photosynthesis from a dilute pool; `drain` is
taking from a neighbour's recent intake, with loss, as every trophic
step loses most of what it moves. The cannot-kill clause is not
biology, it is the experimental condition under which every published
defence evolved (the victim keeps reproducing, more slowly), written
into the physics so that E018 tests the premise and not a predation
cliff (E008's lesson).

### 1.1 Ledger

`OrgStats` gains `drained_m` (taken from this organism), `drain_gain_m`
(gained by this organism), `drains` (count), `drains_fail` (no target
or zero take). `deaths.csv` and `orgs.csv` carry them. The per-organism
ledger test extends: for every organism `energy_end = endowment +
absorb_gain_m + drain_gain_m − spent_m − drained_m − upkeep_paid_m`
(whatever the current identity is, plus the two new terms), and the
world total loses exactly the dissipated share. E010's
`gained_from_others_m` is left for the transfer rule; do not reuse
it.

### 1.2 Interaction with the other rules

`drain` moves energy, not bytes: write protection does not block it.
Under `--cycle-theft-pct` an intruder's `drain` on its host's bytes is
also a stolen instruction (the theft debit applies as to any
instruction); nothing special. Under the charge rules (E008–E010
flags) nothing special either; they are off in every planned arm.

## 2. Engine

- `isa.rs`: `Op::Drain` decoded from `cfg.drain_op` when non-zero
  (the decoder takes the config, or the opcode table is built once
  per `Sim`; pick whichever keeps `decode` cheap and say which in the
  commit). Assembler name `drain`. The disassembler in `pseudo.py`
  (analysis) gains the name, reading the opcode from `meta.json`.
- `sim.rs`: the op per §1; `income_prev_m` and `income_tick_m` on
  `Org` (physics state: in the snapshot and in `state_hash`); the
  stats of §1.1.
- `main.rs`: the three flags with range checks (op in {23, 25} only,
  for now; P and L in 0–100).
- Tests (`cargo test`):
  1. `drain_off_is_bit_identical`: default world 5,000 ticks with no
     flag and with `--drain-pct 50 --drain-loss-pct 50` but no
     `--drain-op`: equal `state_hash` at every census. The three pinned
     hashes T08 checks still hold.
  2. `drain_takes_from_income_and_cannot_kill`: harness, a hand-written
     drainer (A set to a byte of the victim, `drain` in a loop) next to
     the ancestor for 3,000 ticks: the victim's `drained_m` > 0, the
     victim never dies of upkeep while the drainer runs (its deaths are
     0), and no single take exceeds `income_prev_m × P / 100`.
  3. `drain_ledger_balances`: the identity of §1.1 on every organism of
     a 2,000-tick run with drainers injected; the dissipated total
     equals Σ take × L / 100.
  4. `drain_needs_a_living_other_owner`: `drain` with A on own body,
     on debris, on a dead body, and out of locality: fail flag set,
     energy unchanged, `drains_fail` incremented.
  5. `absorb_flip_is_drain_at_23`: the tierra ancestor's `absorb` byte
     with bit 0 set decodes to `drain` under `--drain-op 23` and to
     `pad` under `--drain-op 25` and with the flag off.

## 3. The harness gate (before any world run)

Under `tierra_n0`'s physics (`--sun 2`, fixed edge) plus
`--drain-op 23 --drain-pct 50 --drain-loss-pct 50`:

- **G1, the one-flip drainer.** The tierra ancestor with its `absorb`
  flipped to `drain`, placed before the ancestor in the harness,
  3,000 ticks: its exact births against the ancestor's 119 alone, and
  the ancestor's births with it present. Note that this mutant's A
  register holds whatever the loop left there; report whether it
  drains anything (`drain_gain_m` > 0). The expected answer is that
  the bare flip drains nothing because A is not on the neighbour, and
  the question is how many edits a working drainer is from the
  ancestor (G3).
- **G2, the designed drainer.** The smallest hand-written body that
  sets A onto the neighbour (a `searchf` for the ancestor's label and
  `swap`, or `self 0 ; lit ...`) and drains in a loop while copying
  itself, under both opcodes: its births against the ancestor's, the
  ancestor's births with it present, `drain_gain_m` per 3,000 ticks
  against its `absorb_gain_m`. Pass if the drainer out-reproduces the
  ancestor alone by at least 10% **and** the drained ancestor keeps at
  least 50% of its lone rate (the graded, survivable condition at the
  individual level, which E016 §8.2 showed the theft at N = 50 failed
  for this body). Report the numbers at P ∈ {25, 50, 100} and L ∈
  {0, 50, 90}; the arm values for E018 are chosen from this table, not
  fixed here.
- **G3, reachability.** `--neighbours` of the tierra ancestor under
  `--drain-op 23` (substitutions and deletions; insertions if T11 §1
  has landed): how many single mutants have `drain_gain_m` > 0 in the
  host run, how many of those are replicator-class alone, and their
  births against the ancestor. The same under `--drain-op 25`
  (expected 0). This is the proposal's condition 2 measured.

Pass: G2 passes at some (P, L) and G3 at op 23 has at least one
replicator-class mutant that drains. Then E018 is pre-registered
(arms: off; op 23; op 25; on the tierra ancestor at sun 2, 30 seeds,
250,000 ticks; plus one `std_n0` + op 23 arm for H2's consumer-mode
question in the standard world; measures: E011's income-share
classification with `drain_gain_m` as the third income, parasite and
entered shares, T05's set, the defence screen with a drainer probe).
Fail at G2 (no (P, L) where the drainer pays and the victim survives):
report the table; the memo's branch C (scavenging) is next, and the
engine piece here stays as a flag. Fail at G3 only (a drainer pays
but nothing one hop from the ancestor drains): E018 still runs at
op 23, with the expectation written down that drainers arrive late or
never, and the neighbourhood count is the reported reason.

## 4. Report back

Test count and commit ids; the G1 numbers; the G2 table over (P, L)
and both opcodes; the G3 counts; the T12 row in `docs/tasks/README.md`
and this Status line. Do not pre-register or launch E018.

## 5. As built, and the gate (2026-10-15, Opus)

### 5.1 Deviations from §1

1. **The P% cap is per victim per turn, not per instruction.** Read
   literally, §1.2's `take` applies to each `drain`, so a drain loop
   takes P% of the victim's income on every instruction, several
   times a tick, which is the predation the memo's "capped at a
   fraction of what the victim absorbed that tick" rules out. As
   built, `Org::drain_left_m` opens at `income_prev_m × P / 100` when
   the victim's turn starts (the roll) and every take, by any
   drainer, comes off it. A single take still never exceeds
   `income_prev_m × P / 100` (test 2's bound).
2. The kept upkeep counts the victim's pending region, which
   `run_tick` charges; §1.2 says `upkeep_per_byte × len`.
3. Dissipation goes to `Sim::energy_out`, as E010's transfer loss
   does; no patch column. Over a world it is Σ `drained_m` − Σ
   `drain_gain_m`, and test 3 checks it against Σ take × L / 100.
4. **The cannot-kill clause does not keep the victim alive.** A
   victim drained to its floor pays its upkeep, has 0 left, cannot
   pay for one `absorb`, and dies of upkeep the next tick. The clause
   guarantees one tick, not survival; survival needs P below the
   victim's margin. Test 2 runs at P = 5 for that reason.

Also: the opcode table is built once per `Sim` (`isa::Isa`, `Sim::isa`;
decoding is one lookup); snapshot format 2, the loader still reads
format 1 as `drain_op` 0; `--host` prints six more columns
(`drain_gain_m,absorb_gain_m,host_drained_m,drains,drains_fail,host_energy_m`).

### 5.2 G1, the one-flip drainer

`examples/drain_gate.rs g1`. The tierra ancestor alone at sun 2: 119
exact births in 3,000 ticks. With byte 8 flipped (`absorb` 0x16 to
0x17) and placed before the ancestor: 0 births, dead at tick 4 under
op 23, 25 and with the flag off (it has no income: its seed 100 units
last three ticks of the loop). Under op 23 it ran 21 drains, all
failed (A holds the loop counter, 127 down, an address 32,000 bytes
from its IP), `drain_gain_m` 0. The ancestor is unaffected (alive;
the harness stops when the intruder dies). As expected: the bare flip
drains nothing; the question moves to G3.

### 5.3 G2, the designed drainer

`examples/drain_gate.rs g2 120`. The drainer (tests/drain.rs
`drainer`, 26 bytes): `self ; add B` puts A on the byte after its
body, then K rounds of `drain ; absorb ; dec C ; skipz C ; jmpr D`,
then the 21-byte ancestor's copy procedure (E = 16). At K = 120,
before the tierra ancestor, sun 2, 3,000 ticks; op 23 and op 25 give
identical rows (the body is assembled at its slot):

| P | L | drainer births | ancestor births (alone 119) | `host_drained_m` | `drain_gain_m` | `absorb_gain_m` |
|---|---|---|---|---|---|---|
| off | – | 120 | 119 | 0 | 0 | 109,051.8 |
| 25 | 0 / 50 / 90 | 120 | 0 (dead) | 221.2 | 221.2 / 110.6 / 22.1 | 108,830–109,030 |
| 50 | 0 / 50 / 90 | 120 | 0 (dead) | 442.5 | 442.5 / 221.2 / 44.2 | 108,609–109,008 |
| 100 | 0 / 50 / 90 | 120 | 0 (dead) | 281.7 | 281.7 / 140.9 / 28.2 | 108,770–109,024 |
| 5 | 50 | 120 | 119 | 4,556.9 | 2,278.5 | 106,773.3 |
| 10 | 50 | 120 | 2 (dead) | 247.1 | 123.6 | 108,928.2 |

(Energy in units.) The drainer's births are its lone count (120) in
every row: it is energy-saturated on `absorb` and its cycle time sets
its births, so the take buys nothing. The ancestor, seeded with 100
units, is drained to its floor in its first cycle and dies before its
first child at every P from 10; its margin is about 4% of its income
(the T03 budget, +37.9 a cycle). Shorter loops do not help: at K = 50
to 80 the drainer cannot pay for itself alone and dies within 120
ticks with 1–6 children, draining at most 315 units; at K = 100 it
makes 136 with or without a victim (136 alone), the ancestor 119 at
P = 5 and dead from P = 10. That row meets the pass rule's letter
(+14%, victim at 100%) and not its sense: the 14% is the shorter body,
the drain gives 1.7% of its income.

**G2 fails** at every (P, L) in the table, under both opcodes. Per §3
the memo's branch C (scavenging) is next; `drain` stays as a flag.
Not measured: a host seeded at its store cap rather than with 100
units (the first-cycle death may be the harness's seed, not the rule),
and G3.
