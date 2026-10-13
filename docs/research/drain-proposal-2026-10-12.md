# Where things stand, and the case for `drain` (2026-10-12)

Status: a proposal written after E011–E013. Nothing in it is built,
run or pre-registered. It argues for bringing `drain` (PLAN §5.5, held
back for Phase 3) forward as the next design step, paired with store
depth (PLAN §9), and lists what has to be decided before a hypothesis
and an experiment record are written.

## Where things stand

The world has one energy channel, `absorb`, and one interaction
between organisms, running another organism's code. Every result so far
comes back to that:

- **No producer/consumer split (E011, H2).** About 99% of a genome's
  energy comes from `absorb` and about 23% of its instructions are
  absorbs, for replicators and parasites alike. There is no consumer
  mode because nothing moves energy from one organism to another.
- **No defence (E008–E010, H13–H15).** A host's store is smaller than
  one pass of its own loop, so any cost charged to an entered host is
  either invisible or fatal within the pass. Three owner-side cost
  rules (full charge, split, transfer) failed for that reason, and the
  entered fraction (7–14%) is set by placement, not by any rule.
- **Write protection does not matter here (E012, H4).** `alloc` gives
  every replicator a private copy target, so turning protection off
  changes nothing structural. Nobody has a reason to touch anyone
  else's bytes.
- **The world is stationary** from about tick 25,000 over 250,000
  ticks (E007). The one adaptation is the longer absorb loop (K 64 to
  about 120), which sweeps in the first 10,000 ticks.
- **Sixteen founders** remove founder loss and leave the world the same
  after tick 35,000 (E013), so new experiments can count every seed.

So the world is not short of run time or of selection. It is missing a
way for energy to pass between organisms, which is the gradient PLAN
§5.5 named as the diagnostic for trophic levels.

## Why `drain`, and how it differs from E010

PLAN §5.5: "A drain op takes energy from a neighboring organism's
store. It is lossy (some fraction dissipates)." A consumer is then an
organism that spends its cycles draining where a producer spends them
absorbing.

E010's transfer rule already moved energy from host to intruder, and
failed. It differs from `drain` in two ways that are the reasons it
failed:

- **Gain was tied to placement.** The intruder gained only while
  executing the host's bytes, so how many hosts were entered was the
  geometric chance of falling through into one (12–14% at every N).
  `drain` is an instruction: whoever runs it gains, from wherever it
  is, within range.
- **Gain went to organisms that could not use it.** The intruders were
  one-byte pads whose 64-unit store was full from seed energy; their
  numbers are set by room, not energy (E010 condition (b)). The
  organisms that are energy-limited are full replicators, which spend
  about 23% of their instructions absorbing (E011) and whose absorb
  loop is the one thing selection lengthened (E007). A drain that
  yields more per instruction than a shared, depleting pool shortens
  their cycle, so the payoff lands where it changes fitness.

## Conditions

1. **Pair it with store depth.** A host holds about 100–130 units
   (E010), and `absorb` yields at most 8 per instruction. A drain
   taking as much per instruction as absorb gives empties a host in
   13–16 drains, a small fraction of one of the drainer's passes. On
   the current store `drain` is predation or nothing: a host that is
   drained at all dies, and a drain weak enough not to kill is not worth
   running. That might still produce a consumer mode, which would be
   worth knowing, but it cannot produce a graded defence. Run it as a
   2 × 2: `drain` off/on × the current store/a store several passes
   deep (PLAN §9: where a charged host evolved a defence elsewhere, it
   paid from a budget 4–20 passes deep).
2. **Choose its opcode on purpose.** `absorb` is 22 (0b10110). The free
   slots are 2, 23, 25, 27, 29, 30 and 31; by Hamming distance in the
   low five bits, 23 and 30 are one flip from `absorb`, 2 and 31 two,
   27 and 29 three, 25 four. At one flip every absorb loop is one
   mutation from a drain loop and drainers arrive at once; at four they
   may never arrive. That choice sets the outcome as much as the energy
   numbers, so it is fixed in the pre-registration, and two placements
   may be worth running as arms. A flip turns the instruction, not
   necessarily a working drain loop: whether a flipped absorb loop
   drains anything depends on how `drain` finds its target (next
   section).
3. **Lossy and range-limited**, as §5.5 specifies, so that a trophic
   pyramid has a shape and a drainer cannot reach the whole world.
   Locality is already 512 bytes (one patch).
4. **Gate it in the harness first**, as E009 and E010 were: does a
   one- or two-mutation drainer next to the ancestor out-replicate it,
   and does a drained host survive at each store depth? World runs only
   if the gate passes.
5. **Hold `guard` and `sense` back** until something exists to defend
   against or to sense.

## To decide before pre-registration

- **Target.** How a drain picks its victim: the nearest living body to
  IP within locality, the owner of the byte at a register-held address,
  or the body adjacent to the drainer's own. This decides whether the
  ancestor's loop with `absorb` flipped is a working drainer, and so
  the reachability question in condition 2.
- **Amount and loss.** Units taken per instruction, the fraction that
  dissipates, and whether the take is fixed or proportional to the
  victim's store (proportional, like the proportional absorb rule, makes
  a nearly empty host a poor target).
- **The drainer's store cap.** Gain beyond the drainer's room
  dissipates, as under E010, so a drainer cannot bank more than its
  body allows.
- **Ledger.** E010's `paid_for_others_m` and `gained_from_others_m`
  already carry energy moved between organisms; reuse them, or add
  `drained` / `drained_by` columns so a world with both rules can tell
  them apart. The per-organism ledger test extends to cover it.
- **Write protection.** `drain` moves energy, not bytes, so protection
  does not block it. PLAN §5.3 (the write-protection bullet) says every
  system without protection collapsed and that `guard`/`drain` "then
  evolve the boundary". E012 weakens the first half for this world;
  revise that bullet when `drain` is designed.

## Hypothesis to register

H16, as H2 with its mechanism in place: with `drain` available, a
consumer mode appears (a cluster of genomes that take most of their
energy from other organisms), and whether it persists alongside
producers depends on store depth: at the current store, consumers crash
their hosts and themselves or never pay; at a store several passes deep
they coexist. The thresholds, the opcode and the target rule are fixed
in the experiment record before any run.

## Status note (2026-10-13)

Demoted, not dropped, by `synthesis-2026-10-13.md` §3.3 and PLAN §8.3.
Two of its conditions no longer stand as written. Condition 1 (pair
`drain` with store depth): store depth is not reachable by a cap or
income setting in this world, because proportional absorb on a shared
pool equilibrates every host to zero margin (synthesis §2 B); a 21-byte
body may hold 1,344 units and holds 100–130 at any cap. The next cost
rule is a cost in time (`--cycle-theft-pct`, E014, H16), which needs no
reserve. The "where things stand" section above is unchanged and
correct. `drain` itself follows E016 if a consumer mode is still
wanted, in the form with precedent (a take from income or proportional
to the victim's store, capped so it cannot kill; Symbulation's nutrient
mode, Jha 2026's STEAL at α = 0.8). The opcode-placement argument in
condition 2 and the target, amount and ledger questions carry over
unchanged.

Correction (2026-10-13, E007 reserve check): "holds 100–130 at any
cap" is wrong for E007. Active hosts hold a median of about 600 units,
a fifth of them sit at the cap, and the cap is 1.7 passes. Condition 1
stands in its original form: on the current store, a drain that takes
at absorb's rate still empties a host within a fraction of the
drainer's passes. Whether a higher cap gives store depth is untested.
