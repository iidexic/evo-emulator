# Experiments: index and status log

One record per experiment, E001 onward, each with seed, config,
commit, what was varied, what was observed and which hypothesis it
bears on. Predictions are written into the record before the runs.
Runs are reproducible from seed and config, so a record plus the repo
regenerates any figure.

| E | date | file | question | outcome, one line |
|---|---|---|---|---|
| E001 | 2026-10-01 | `2026-10-01-e001-first-runs.md` | does the ancestor replicate in the Phase 1 world? | yes; non-replicating absorbers hoard, so store cap and bit rot added |
| E002 | 2026-10-01 | `2026-10-01-e002-dispersal.md` | does dispersal sustain replication? (H10) | far `alloc` helps a little; smaller patches hurt; mixed |
| E003 | 2026-10-03 | `2026-10-03-e003-crash-diagnosis.md` | what kills replicators in a crash? | starvation in the parent's crowded patch; loafers survive |
| E004 | 2026-10-05 | `2026-10-05-e004-physics-pass.md` | which physics keeps replication going? (H10, H11) | 128 patches of 512 bytes at 8x sun with far `alloc`: 38 of 40 runs; the standard world |
| E005 | 2026-10-06 | `2026-10-06-e005-parasite-search.md` | are there parasites? | yes, fall-through placement lineages, 0.4–0.8% of exact births |
| E006 | 2026-10-07 | `2026-10-07-e006-self-owner.md` | does `self` = owner change the ecology? (H8) | parasitism gone, intruders become donors; executor rule kept |
| E007 | 2026-10-07 | `2026-10-07-e007-long-run.md` | 250,000 ticks: persistence, resistance, sweeps (H12, H5, H3, H6) | stationary from 25,000; one sweep (absorb count 64 to 112–127); no resistance |
| E008 | 2026-10-07 | `2026-10-07-e008-charge-owner.md` | does a full owner-side charge produce a defence? (H13) | no; entered host dies in one pass, killer profits |
| E009 | 2026-10-08 | `2026-10-08-e009-split-charge.md` | does a split charge grade the host? (H14) | cliff, not a grade; search not run |
| E009a | 2026-10-08 | `2026-10-08-e009a-invasion.md` | is the five-byte self-scan maintained among founders? | lost at a length-matched control's rate |
| E009b | 2026-10-08 | `2026-10-08-e009b-late-injection.md` | is it maintained when injected at tick 25,000? | lost in every seed under every rule |
| E010 | 2026-10-08 | `2026-10-08-e010-transfer.md` | does a transfer make intrusion profit and an eject pay? (H15) | intruders not energy-limited; entries stay rare and fatal; falsified on its premise |
| E011 | 2026-10-12 | `2026-10-12-e011-absorb-split.md` | is there a producer/consumer split in E007? (H2) | no consumer mode; 97–99% of income from `absorb` for every persistent genome |
| E012 | 2026-10-12 | `2026-10-12-e012-no-protect.md` | is write protection needed for coexistence? (H4) | no, in this world; `alloc` gives every replicator a private target |
| E013 | 2026-10-12 | `2026-10-12-e013-founders.md` | do sixteen founders change anything after the founder phase? | all seeds persist; window 2 matches E007; absorb sweep slower in its second half |
| E014 | 2026-10-13 | `2026-10-13-e014-cycle-theft.md` | pilot: is an entered host graded, not killed, under `--cycle-theft-pct`? (H16) | yes, 0.90 at N = 50 on reproducing hosts, dose clean, tax control clean; but intruders not resident (< 10%), so the main stage is skipped and gate 2 moves to E016 with the template ancestor |
| E015 | 2026-10-13 | `2026-10-13-e015-template-ancestor.md` | does a template-addressed ancestor have a one-hop parasite, and does it persist? (H17) | one-hop parasite by construction (1,095 `parasite_jump` rows, 996 label flips; std 25, none by search); persistence gate fails 0 of 10 at K = 127; sun and noise-off arms added per the registered branch |

Next: E014 (cost in time), E015 (template-addressed ancestor), E016
(cost x ancestor, the defence search), per PLAN.md §8.3 and
`synthesis-2026-10-13.md`.

## Status log (moved verbatim from PLAN.md §8 on 2026-10-13)

The text below is the per-experiment status log as PLAN.md §8 carried
it from 2026-10-01 to 2026-10-12, including the phase headings it was
written under. It is kept as written; the roadmap that replaced it is
PLAN.md §8.


**Phase 0 — Design (this doc).** ISA draft, op cost table, world model. Each
rule with its physical justification. Decide open questions in §9.

**Phase 1 — Minimal living system.** Status 2026-10-01: `evo-core` builds
and passes its tests, the ancestor replicates, first runs are recorded in
`docs/research/experiments/2026-10-01-e001-first-runs.md`.
Follow-ups 2026-10-01: entropy loops use a geometric skip, about 29x faster
(2ade71f); `alloc` range check fixed to cover the whole region (12513a3);
E002 dispersal experiment set up, not yet run: six arms over patch size and
farthest-free `alloc`, runner `analysis/e002_dispersal.py`, hypothesis H10
(5c7aa74). E002 run at d89e634: farthest-free `alloc` helped a little (0 of
10 extinct, 2 of 10 still replicating vs 0 for control); smaller patches
made extinction more likely, because founder and first child starve in
one small patch. H10 mixed. Rust VM, 1D ring world, energy, noisy
writes, hand-written ancestor. Success criterion: the ancestor replicates,
mutants appear, and parasites (organisms that use another's copy loop)
emerge. This is roughly a Tierra reimplementation with energy instead of a
reaper.

**Phase 2 — Instrumentation.** Everything in §7. Success criterion: we can
draw the phylogeny of a Phase 1 run and see the parasite lineage appear.
Status 2026-10-03: diagnostic first cut built (§7). First use, E003
(`docs/research/experiments/2026-10-03-e003-crash-diagnosis.md`):
replicators starve in their own crowded patch (newborns at a median age of
3 ticks, adults at 14–17, zero `alloc` failures), replicator lineages end
by tick 2,100–9,400 in control seeds 1–5, and broken-loop absorbers are
what remains. Also seen: reproduction from debris, where an organism that
copies one byte per child gets working replicators because the claimed
region already holds dead ancestors' bytes. The parasite criterion cannot be
met until replication persists, so the next design pass is physics (E003
lists the options).
Physics pass, E004 (2026-10-05,
`docs/research/experiments/2026-10-05-e004-physics-pass.md`): replication
persists when children disperse into a world of many small patches that
can each feed a founder. 128 patches of 512 bytes, each with a control
patch's income and cap (8× sun per byte), with far `alloc`: replicating at
tick 50,000 in 38 of 40 runs, about 950 organisms over all 128 patches.
Every arm without all three of small patches, more sun and far `alloc`
failed (0 of 10, or 2 of 10 for 8× sun and far `alloc` in 16 large
patches). Proportional absorb (§5.4) halves newborn starvation; bit rot
1e-4 turns loafers over in a large population and wipes out a small one.
Standard world from here on (recorded 2026-10-05; code defaults
unchanged for now): `--patch 512 --sun 8 --alloc-far --absorb-prop
--rot 1e-4` (E004 "Decision"). Decision 2026-10-07: the code defaults
stay as they are until E005 is recorded, because E005 reads the E004
run files and the harness yardstick must not move under it. Done the
same day, after E005 and E006: `Config::default()` is now the E004 world
(`Config::e001()` and `--world-e001` give the Phase 1 world; `--alloc-near`
and `--absorb-fixed` undo the two new rules), checked byte-for-byte
against the recorded E004 stdout of the control, p512_far and
p512_far_prop_rot arms over 3,000 ticks. The single-genome harness
therefore labels genomes under the E004 world from now on; `classes.csv`
files written before this date used the Phase 1 physics, and E005's
`classes_world.csv` is the same yardstick as a new `classes.csv`. Every
run's `meta.json` carries every config field, so older runs stay
reproducible either way.
E005 (2026-10-06, `docs/research/experiments/2026-10-06-e005-parasite-search.md`):
parasite search in the 40 p512_far runs, pre-registered before any query
of the files. Definitions, predictions and the runner are in the record.
A consequence of Phase 1 `self` (executing organism) plus far `alloc`,
noticed while reviewing the design: any body that ends without a jump and
sits right before a replicator reproduces by falling into it, and the
smallest such body is one byte, so a "parasite lineage" may be a
placement lineage rather than a code lineage. E005 reports both.
Result 2026-10-07: criterion met in the letter. Every surviving run has
13–72 lineages (depth up to 63 generations) that replicate by running a
neighbour's copy loop, almost all of them the ancestor with a broken
restart falling into the body behind it; 1–2-byte bodies do the same
under proportional absorb. Parasites are 0.4–0.8% of exact births.
Also found: genomes that jump to a fixed address and come home through
`self ; jmpa` left in free memory by a dead body (dead-code
trampolines), as common as the parasites; and that world snapshots are
needed to read such cases (§7).
E006 (2026-10-07, `docs/research/experiments/2026-10-07-e006-self-owner.md`):
the same world with `self` naming the owner of the byte at IP
(`--self-owner`). Persistence unchanged; parasitism through living
hosts gone (host harness 0–2 exact children against 60–180), replaced
by intruders copying their hosts (3.9–4.1% of births, from 0.4–0.5%)
with no measurable gain to the hosts; dead-code users unchanged. H8
supported in kind. Decision: `self` = executor stays the default, since
parasites are the interaction to evolve defences against; the switch
stays for Phase 4 ISA comparisons.
E007 (2026-10-07, `docs/research/experiments/2026-10-07-e007-long-run.md`):
the standard world over 250,000 ticks, 10 seeds, on Linux (bit-identical
to Windows over the 20,000 ticks checked). Stationary from tick 25,000
on: population about 935, length 21 in every window of every seed,
parasites 0.8–1.0% of exact births and reinvented at E005's rate, no
resistance (H12 supported). The one event is a post-hoc find: the absorb
loop count swept from 64 to 112–127 inside the first 10,000 ticks in
every run, with or without parasites (three `--self-owner` runs do the
same), and the landscape is flat from 112 up (K-seeded follow-up). So
selection acts within 10,000 ticks when a byte pays, and the missing
defence is a mutational-path problem, not a selection-strength problem.
Lesson for measures: predictions 6 and 7 counted raw-genotype leaders
among 2%-share near-ties and could not see the sweep; track traits (a
byte, a loop constant) and canonical genomes (`func_hash`) from now on.
E008 (2026-10-07, `docs/research/experiments/2026-10-07-e008-charge-owner.md`):
`--charge-owner`, the living owner of the byte at IP pays for every
instruction another organism executes there. H13 supported: no top host
survives the `pad` probe in any of 90 seed-windows. The outcome was
implied by the pre-run harness table (every host dies at tick 11–18
before its first child), so the registered test was safe; the
informative part is the ecology. An entered host dies within one
intruder cycle, so foreign execution fell from 12–15% to 0.4%, unowned
execution rose to 6–7%, and `pad`'s lineage doubled its output by
running the hosts it killed: the full charge rewards killing. There is
no long-lived infected host for selection to grade. Next: E009, a split
charge, so an infected host survives and a partial defence can pay.
E009 (2026-10-08, `docs/research/experiments/2026-10-08-e009-split-charge.md`,
designed and built; the 250,000-tick search itself not run, its gates
E009a and E009b were): `--charge-owner-pct N`, the owner pays a
share. Calibration found no graded cost at any N (a cliff in the
harness; matched-age entered hosts reproduce as well as unentered ones
in the world), so the search was gated by invasion tests of the
finished defence, a working five-byte self-scan
(`self 1 ; swap C ; self 0 ; sub C ; jmpr A`; the ISA already allows
it). New tools: `--founder HEX:COUNT` and `--inject TICK:HEX:COUNT`.
E009a (founder mix) and E009b (injected at tick 25,000 into the
parasitised world): the defence is lost in every seed under every rule,
at a length-matched control's rate, because few hosts are ever entered
and an entry costs at most one pass; the saving is an order of
magnitude below the five-byte cost. Split-charge line closed; next cost
rule is a transfer (the intruder gains what the host loses), checked
first by injection.
E010 (2026-10-08, `docs/research/experiments/2026-10-08-e010-transfer.md`,
designed): `--transfer-pct N`, every instruction run on another living
organism's bytes moves `floor(cost * N / 100)` from the owner to the
executor, on top of the executor's own cost; informative for N > 100,
where intrusion profits. H15. Gated as E009 was: world calibration
picks N (entries common, hosts persist), then the E009b injection test
with an ejecting six-byte defence (`skipz A ; jmpa D` after the
self-scan; the E009 trap is a drain under transfer and becomes the
negative control). Calibration (15 runs, 50,000 ticks): entered
fraction 12–14% at every N, births 104–122% of N = 0's; no N qualifies,
stop rule applied, gate and search not run. Intruders are not
energy-limited (profit does not multiply them) and an entry still
kills the host within one pass (the store is one pass deep), so
entries stay rare and fatal under any per-instruction rule. H15
falsified on its premise. The eject defence works in the harness and
is kept. Cost-rule line (E008–E010) closed; the cause is physics (the
one-pass store, placement-limited intruders), see §9 energy location.
Next: the recent-literature review, then choose between the
energy-location change and the Phase 4 BFF harness.
E011 (2026-10-12, `docs/research/experiments/2026-10-12-e011-absorb-split.md`,
no new runs): H2's producer/consumer split read from E007's death
records. Persistent genomes take 97–99% of their income from `absorb`,
and parasites spend more of their instructions on it than their hosts
(0.245 against 0.229): a fall-through parasite runs the host's absorb
loop. The registered "under 1% low-absorb" failed at 2.1–2.5%, all of
it single-parent bursts (a parent damaged after birth copies a body its
children cannot run), so H2 is mixed by the rule and leaning refuted:
the physics moves no energy between organisms. Measure lesson: 16.5% of
E007's exact births copy a parent's body as changed after birth, and
E005's ≥ 2-exact-births test admits these bursts (about a quarter of
the dependent genomes); a lineage test should require two executors.
E012 (2026-10-12, `docs/research/experiments/2026-10-12-e012-no-protect.md`):
`--no-protect` in the standard world, 10 seeds × 100,000 ticks, with
new counters `writes_foreign` and `overwritten`. Nothing structural
changed: population 941, about 2,300 canonical genotypes per window,
leader at most 15%, parasites 0.8–0.9%, the absorb sweep on E007's
course; foreign writes land at 0.7–1.1 times E007's refused rate,
mostly from a few damaged bodies. H4 refuted in this world: `alloc`
gives every replicator a private copy target, so nothing gains from
overwriting. Protection stays the default.
E013 (2026-10-12, `docs/research/experiments/2026-10-12-e013-founders.md`):
sixteen founders instead of one, 10 seeds × 50,000 ticks. All 10
persist (seed 10 included), the world fills twice as fast, and window 2
matches E007 (population −0.6%, canonical genotypes −2.5%,
replicator-class bodies −10%, on the registered bound). Not as
predicted: the absorb sweep is slower in its second half (median 105.5
against 112 at tick 10,000; level from 32,500), plausibly because 9–16
founder lineages share the world through it. Sixteen founders are fine
for measures after tick 35,000 or against a matched control.
Next: unchanged, the energy-location change (store depth) or the Phase
4 BFF harness.
E007 reserve check (2026-10-13, E007 record, `analysis/e007_reserve.py`,
no new runs): the check the synthesis named in §2 B fails in every seed.
Hosts are not held at zero margin. Active hosts (divided within 50
ticks) hold a median of about 600 units, a fifth of them sit at the
1,344 cap, and the 7–8% of reproducers that reach it make half the
divides. The cap is 1.7 passes, so the store is still shallow at this
cap, but "whatever the cap" is unsupported. About 42% of living
replicator-class bodies are stalled: broken by bit rot,
non-reproducing, at the cap.

Ordering note 2026-10-09: E005–E010 were run as Phase 2 follow-ups
while Phase 3 (richer physics) has not started, and the next step is a
choice between an energy-location change and the Phase 4 BFF harness.
Phase 3 as written is therefore not next; its items (2D torus, drift,
`drain`) stay listed but are not scheduled, and the c1 sweep it was to
carry (H3) has no date.

**Phase 3 — Richer physics.** 2D torus, per-patch parameters,
seasons, slow drift, drain/defense ops (bit rot and debris exist since
Phase 1, §5.7). Success criteria: spatial
differentiation of lineages; some form of producer/consumer split;
evidence for or against evolved repair.

**Phase 4 — Experiments.** BFF calibration harness first: reproduce
Agüera y Arcas et al. (2024) exactly (2^17 tapes of 64 bytes, random
pairing, 8,192 steps per interaction, byte-replacement mutation at 2^-12)
to confirm their 40% emergence rate, then swap in evo's ISA on the same
protocol, then add evo's physics one rule at a time (energy, ownership,
locality). This isolates which rule, if any, kills emergence. Literature
(2026-10-09, `literature.md` §6.3.3, §6.4): nobody has done this;
energy was added to a soup once (Jha et al. 2026, c = 1 per op,
ε = 24 per epoch) without an off control, and ownership, write
protection and death by energy never. Sweep order: start-execution
head position first (the one rule with quantified prior art), energy
with an off control second, ownership third. Report QNN over
`func_hash` groups and MRCA depth from the next experiment on
(§6.4 question 4); and run the Lenski 2003 line-of-descent analysis
(fitness of every step on the winning lineage) on E007's ancestry
table for the K sweep, which no digital system has done for a
defence or a physiological trait. Round 2 (2026-10-12, `literature.md`
§7.1, §7.4): the 40% is a takeover statistic; Dušek et al. 2026 find a
replicator in 99 of 100 standard soups at mutation 0 (median 2,453
epochs) but takeover in 45. So the sweep's primary outcome is
first-discovery time per seed, counted in executed tapes as well as
epochs, with takeover second; Dušek's uniform-sampling (U) and
fresh-partner (N) regimes run beside the soup as controls; operator
frequencies are logged. Build from their cubff fork
(`koutefra/bff-replicator-discovery`), where the regimes are flags.
Then soup
runs with no seed in the full world, with a start-execution rule (§9). Chemistry (multiple
resource types). Multi-day runs. Compare ISA variants for evolvability.
