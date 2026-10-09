# E009b: the self-scan injected into a parasitised world (2026-10-08)

Status: design and predictions written 2026-10-08 before the `--inject`
flag exists and before any run. Gate for E009, replacing E009a, whose
founder-mix test was decided by body length in the colonisation race
before any intruder existed.

Bears on: H14, E009a (five extra bytes cost about 5% per generation and
are lost within 1,700 ticks from a 9% start under every rule, with or
without the defence), the E009 calibration (the split charge shows no
graded cost in hosts' reproduction), H13.

## Question

Does the complete five-byte self-scan earn its keep once intruders
exist? E009a could not ask this: its test genomes were gone before the
first parasite lineage arose. Here the standard world runs from one
founder to tick 25,000, by which point it is the E007 world (about 935
bodies, absorb count 112–127, foreign execution 12–15% of instructions
under E007 physics, parasites about 1% of births, `pad` lineages
present), and the test genome is then placed into free memory at 50
sites. If selection keeps it under some rule, that rule is E009's arm.
If it is lost at the inert control's rate under every rule, the
split-charge line is closed and the next cost rule is a transfer.

## Tool

`--inject TICK:HEX:COUNT`, repeatable, in `evo-core`. At the start of
tick TICK, before any organism steps, COUNT copies of HEX are seeded with
100 units each, as founders are. Copy j targets address
`world_size / 2 + world_size × j / COUNT` modulo the world size and takes
the first run of `len(HEX)` bytes, scanning forward from the target, that
is not owned by a living organism (free or debris; the bytes are
overwritten, as `alloc` plus `copy` would). A copy with no such run
before the next copy's target is skipped. No PRNG draw. `meta.json`
records each injection as given and the start address of every copy
placed (or −1 if skipped). Without the flag the run is bit-identical to
the current one (E007 hashes at tick 20,000 of seed 1). Births and
deaths of injected organisms are recorded as for founders (`parent` 0,
birth tick = TICK).

## World and runs

The standard world, one ancestor founder as usual, 50,000 ticks, census
every 500. At tick 25,000, 50 copies of one test genome (about 5% of
the population of about 935). Three test genomes:

- `prefix`: the K = 120 ancestor with `self 1 ; swap C ; self 0 ; sub C ;
  jmpr A` (`33 52 13 4f 0c`) at byte 0; 26 bytes.
- `inert`: the K = 120 ancestor with five `zero D` (`70 70 70 70 70`) at
  byte 0; 26 bytes. The length control.
- `resident`: the K = 120 ancestor itself
  (`13325271fc11781605086c5a1845486c11101c130d`), 21 bytes. The control
  for the injection: a genome that the resident cloud already contains
  in near-synonymous forms, so its fate measures what injection into
  free memory does to a genome with no length penalty.

Four rules: N = 0, `--charge-owner-pct 25`, `--charge-owner-pct 50`,
`--charge-owner` (E008). Seeds 1–3. 36 runs. The first 25,000 ticks of a
seed are shared by the three genomes within a rule and are bit-identical
to the E009 calibration runs for that rule and seed (N = 25 and 50, seed
1) and to E007 (N = 0). Runner `analysis/e009b_late_injection.py`, output
`runs/e009b/<rule>_<genome>/s<seed>/`.

## Measures

Per 2,500-tick bin from tick 25,000 to 50,000 (bins 11–20 in E009a's
numbering; bin 11 is ticks 25,000–27,500), over replicator-class exact
births:

- the test share: births whose canonical genome equals the test genome's
  canonical form, and separately births carrying the test prefix at byte
  0 (for `resident`, births whose canonical genome equals it).
- the share by bodies of 26 bytes or more.
- living test bodies at each census (`orgs.csv`, canonical match), as a
  count, and the count of injected copies actually placed (from
  `meta.json`).
- foreign execution at the bin's last census; replicator deaths that
  paid.
- among deaths of test-genome organisms: the share with
  `paid_for_others_m` above 0 (how many were entered), median age, mean
  exact children.

Whole run: last-bin test share; the last 100-tick bin with the test
share above 1% (E009a's reading); the tick at which the living test
count last exceeds 10.

Harness, before the runs: none new; E009's K = 120 and prefix rows and
E009a's inert row cover the three genomes.

## Predictions

1. The injection itself is survivable: `resident` has at least 10 living
   bodies at tick 50,000 in at least 2 of 3 seeds under every rule, and
   its share of exact births in the last bin is at least 1%. The cloud's
   landscape is flat from K = 112 up (E007 follow-up), so a K = 120
   ancestor dropped into it is near-neutral.
2. Under N = 0 both 26-byte genomes are lost, below 1% of exact births in
   the last bin in 3 of 3 seeds each, at the same rate within a factor
   of 2 (last > 1% tick, seed by seed, in at least 2 of 3 seeds). The
   intruder costs the host nothing, so the prefix earns nothing.
3. Under N = 25 and N = 50 the `prefix` genome is lost, below 1% in the
   last bin in at least 2 of 3 seeds at each N, and its last > 1% tick
   is within a factor of 2 of `inert`'s in at least 2 of 3 seeds. The
   calibration found no reproductive cost to being entered at these N,
   so there is nothing for the defence to earn back; the 5% length cost
   wins. This is the gate: if it fails at some N, E009 runs at that N.
4. Under the E008 rule the `prefix` genome does no better than `inert`
   (not later than inert's last > 1% tick in at least 2 of 3 seeds). A
   trapped `pad` spins at the host's expense and the host dies.
5. Exploratory: the share of test deaths that had been entered, by rule
   (at N = 0 the prefix host should be entered as often as inert and pay
   nothing; at N = 25–50 a prefixed host pays far less per entry than an
   inert one, 5 cheap ops against a 260-unit pass, and whether that
   shows in age or children is the number to look at); and whether the
   prefix share, while it lasts, moves with foreign execution.

If 3 holds and 1 holds, the split charge cannot pay for a five-byte
defence even in a parasitised world, and the cost rule is wrong, not the
timescale: next is a transfer rule (the intruder's gain is the host's
loss), checked first by this injection test. If 1 fails, injection into
free memory is itself lethal (a body dropped into debris with 100 units
and no neighbours may not establish) and the test is redone with more
copies or more energy before anything is concluded. If 3 fails, E009
runs at that N with the prefix histogram as its main measure, and the
50 injected copies' descent is reconstructed from the ancestry.

## Caveats, known now

- 50 copies at tick 25,000 is one frequency and one time; three seeds.
- "Entered" is read from `paid_for_others_m`, which is 0 under N = 0
  by construction; at N = 0 the entry rate is not measurable from
  counters and only foreign execution over all bodies is available.
- Injected bodies start with 100 units in whatever memory is free at the
  target, which may be a drawn-down patch; the resident control carries
  that effect.
- The inert control matches length, not behaviour: `zero D` is five
  executed instructions per cycle, as the prefix is, so cycle time is
  matched too; what differs is only what happens to an intruder.

## Results (2026-10-08)

Run on the Windows machine (Opus) with `analysis/e009b_late_injection.py`,
binary built from the working tree; 36 runs of 50,000 ticks, census every
500, `--inject 25000:<hex>:50`, classified under each rule's flags; 254 s
wall for runs and classes (12 in parallel; about 20 s run and 57–67 s
classify each), 280 s in all. Output in `runs/e009b/` (`summary.md`,
`bins.csv`, `runs.csv`, `living.csv`, `deaths.csv`). All 50 copies were
placed in every run. Genome hexes checked with `--disasm` before use.
Within each rule and seed the three genomes' runs print the same report
line at tick 24,500. Without the flag the tick-20,000 seed-1 run still ends
with `20000,953,536,27,21,20.7,50,238498,237546,879038,378839,127,242` and
`census.csv` `6f523da9f7e05a4e`, `births.csv` `33b07ce87cc80ea6`; the three
N = 0 seed-1 injection runs print that line at tick 20,000.

Operational readings fixed in the runner before the runs (its docstring):
test genome = canonical instruction list (`traits.canonical_instrs`) equal
to the test genome's in full; "lost" = last-bin (bin 20) share below 1%;
"last > 1%" = end tick of the last 100-tick bin of births after the
injection with the test share above 1%; rates compared as ticks since the
injection (absolute ticks from 25,000 on are always within a factor of 2
of each other), max/min, ≤ 2 in at least 2 of 3 seeds; prediction 1 =
under every rule, at least 2 of 3 seeds with ≥ 10 living resident bodies
at tick 50,000 and last-bin share ≥ 1% in the same seed; prediction 4's
"no better" = prefix "last > 1%" not later than inert's.

Per run, test share of replicator-class exact births per 2,500-tick bin
(bin 11 = ticks 25,000–27,500), living test bodies (canonical match of the
current body) at tick 50,000:

| rule | genome | seed | placed | bin 11 | bin 12 | bin 14 | bin 17 | bin 20 | last > 1% (tick) | living at 50,000 | final population |
|---|---|---|---|---|---|---|---|---|---|---|---|
| N = 0 | prefix | 1 | 50 | 2.84% | 0.08% | 0.00% | 0.00% | 0.00% | 27,600 | 0 | 913 |
| N = 0 | prefix | 2 | 50 | 2.45% | 0.26% | 0.00% | 0.00% | 0.00% | 27,800 | 0 | 890 |
| N = 0 | prefix | 3 | 50 | 0.95% | 0.00% | 0.00% | 0.00% | 0.00% | 25,800 | 0 | 957 |
| N = 0 | inert | 1 | 50 | 2.65% | 0.00% | 0.00% | 0.00% | 0.00% | 26,400 | 0 | 923 |
| N = 0 | inert | 2 | 50 | 1.30% | 0.00% | 0.00% | 0.00% | 0.00% | 25,900 | 0 | 977 |
| N = 0 | inert | 3 | 50 | 1.34% | 0.00% | 0.00% | 0.00% | 0.00% | 25,700 | 0 | 923 |
| N = 0 | resident | 1 | 50 | 10.26% | 9.09% | 13.39% | 12.33% | 13.90% | ≥ 50,000 | 40 | 949 |
| N = 0 | resident | 2 | 50 | 20.43% | 22.25% | 17.61% | 13.29% | 2.91% | ≥ 50,000 | 11 | 943 |
| N = 0 | resident | 3 | 50 | 11.45% | 16.55% | 19.27% | 15.97% | 8.97% | ≥ 50,000 | 24 | 940 |
| N = 25 | prefix | 1 | 50 | 4.48% | 1.03% | 0.00% | 0.00% | 0.00% | 28,400 | 0 | 938 |
| N = 25 | prefix | 2 | 50 | 1.49% | 0.00% | 0.00% | 0.00% | 0.00% | 25,800 | 0 | 931 |
| N = 25 | prefix | 3 | 50 | 0.81% | 0.00% | 0.00% | 0.00% | 0.00% | 25,700 | 0 | 961 |
| N = 25 | inert | 1 | 50 | 3.23% | 0.00% | 0.00% | 0.00% | 0.00% | 26,600 | 0 | 971 |
| N = 25 | inert | 2 | 50 | 0.68% | 0.00% | 0.00% | 0.00% | 0.00% | 25,500 | 0 | 941 |
| N = 25 | inert | 3 | 50 | 0.37% | 0.00% | 0.00% | 0.00% | 0.00% | 25,200 | 0 | 944 |
| N = 25 | resident | 1 | 50 | 17.80% | 20.95% | 14.12% | 14.79% | 4.56% | ≥ 50,000 | 8 | 947 |
| N = 25 | resident | 2 | 50 | 11.82% | 8.79% | 3.67% | 3.32% | 0.02% | 47,200 | 0 | 907 |
| N = 25 | resident | 3 | 50 | 23.62% | 10.42% | 7.43% | 0.88% | 0.00% | 40,700 | 0 | 925 |
| N = 50 | prefix | 1 | 50 | 0.24% | 0.00% | 0.00% | 0.00% | 0.00% | 25,100 | 0 | 920 |
| N = 50 | prefix | 2 | 50 | 0.76% | 0.00% | 0.00% | 0.00% | 0.00% | 25,700 | 0 | 933 |
| N = 50 | prefix | 3 | 50 | 1.03% | 0.00% | 0.00% | 0.00% | 0.00% | 26,500 | 0 | 955 |
| N = 50 | inert | 1 | 50 | 0.18% | 0.00% | 0.00% | 0.00% | 0.00% | 25,200 | 0 | 903 |
| N = 50 | inert | 2 | 50 | 0.24% | 0.00% | 0.00% | 0.00% | 0.00% | 25,200 | 0 | 927 |
| N = 50 | inert | 3 | 50 | 2.41% | 0.00% | 0.00% | 0.00% | 0.00% | 26,300 | 0 | 910 |
| N = 50 | resident | 1 | 50 | 10.97% | 4.59% | 0.10% | 2.11% | 0.04% | 42,600 | 0 | 943 |
| N = 50 | resident | 2 | 50 | 21.51% | 26.90% | 15.86% | 21.30% | 8.57% | ≥ 50,000 | 12 | 944 |
| N = 50 | resident | 3 | 50 | 24.52% | 14.61% | 25.94% | 3.22% | 0.01% | 46,100 | 0 | 958 |
| E008 | prefix | 1 | 50 | 0.57% | 0.00% | 0.00% | 0.00% | 0.00% | 25,300 | 0 | 930 |
| E008 | prefix | 2 | 50 | 0.29% | 0.00% | 0.00% | 0.00% | 0.00% | 25,100 | 0 | 942 |
| E008 | prefix | 3 | 50 | 0.58% | 0.00% | 0.00% | 0.00% | 0.00% | 25,400 | 0 | 941 |
| E008 | inert | 1 | 50 | 0.71% | 0.00% | 0.00% | 0.00% | 0.00% | 25,700 | 0 | 912 |
| E008 | inert | 2 | 50 | 0.59% | 0.00% | 0.00% | 0.00% | 0.00% | 25,600 | 0 | 935 |
| E008 | inert | 3 | 50 | 0.66% | 0.00% | 0.00% | 0.00% | 0.00% | 25,500 | 0 | 942 |
| E008 | resident | 1 | 50 | 10.45% | 11.03% | 2.31% | 6.08% | 6.66% | ≥ 50,000 | 11 | 929 |
| E008 | resident | 2 | 50 | 4.76% | 4.66% | 1.52% | 0.00% | 0.01% | 33,900 | 0 | 945 |
| E008 | resident | 3 | 50 | 13.09% | 8.49% | 2.03% | 4.81% | 0.00% | 44,500 | 0 | 928 |

Living test bodies by census: every 26-byte arm has 49–50 at tick 25,000
and 0 from tick 30,000 on (at 27,500: 2, 2, 0 for N = 0 prefix, 15, 0, 0
for N = 25 prefix, 0 elsewhere). The resident has 11–70 at 27,500 in
every run. The resident's canonical form is also present before the
injection in some worlds: bin 10 share 8.08% (N = 0 seed 1), 7.60% (N = 25
seed 3), 9.58% (N = 50 seed 2), at most 1.63% elsewhere, and 55–88 living
at tick 25,000 in those runs; the resident measure is not purely injected
descent. Full series in `summary.md` and `living.csv`.

Other per-bin measures (medians across seeds, `summary.md`): the prefix
share (test prefix at byte 0, any body) tracks the test share, 0.24–3.02%
in bin 11 and 0.00% from bin 13 in every 26-byte arm; bodies
of 26 bytes or more 0.25–4.76% in bin 11, ≤ 0.24% in bin 12 and 0.00% from
bin 13 in the 26-byte arms, 0.00–0.07% in the resident arms throughout;
population 902–996 throughout; foreign execution at the bin-20 census
13.4% / 14.9% / 15.0% (N = 0 prefix / inert / resident), 3.7% / 2.9% /
3.6% (N = 25), 1.35% / 1.07% / 0.98% (N = 50), 0.54% / 0.32% / 0.39%
(E008); replicator deaths that paid in bin 20 9.5% / 7.7% / 10.0% (N = 25),
10.4% / 11.1% / 12.0% (N = 50), 12.9% / 12.3% / 11.5% (E008).

Deaths of test-genome organisms (birth genome canonically the test
genome; injected copies and descendants), seeds pooled; by seed in
`summary.md`:

| rule | genome | deaths | entered (`paid_for_others_m` > 0) | median age | mean exact children |
|---|---|---|---|---|---|
| N = 0 | prefix | 1,081 | 0.00% | 19 | 1.1 |
| N = 0 | inert | 918 | 0.00% | 18 | 1.0 |
| N = 0 | resident | 98,542 | 0.00% | 19 | 1.0 |
| N = 25 | prefix | 1,347 | 8.09% | 20 | 0.9 |
| N = 25 | inert | 796 | 7.29% | 20 | 1.0 |
| N = 25 | resident | 54,727 | 9.61% | 19 | 1.0 |
| N = 50 | prefix | 448 | 9.15% | 19 | 0.7 |
| N = 50 | inert | 572 | 12.59% | 19 | 0.8 |
| N = 50 | resident | 71,324 | 10.63% | 19 | 1.0 |
| E008 | prefix | 380 | 11.84% | 19 | 0.7 |
| E008 | inert | 482 | 13.90% | 19 | 0.7 |
| E008 | resident | 25,490 | 13.59% | 19 | 1.0 |

Prediction checks:

1. Fails (holds under N = 0 only). Resident living at 50,000 / last-bin
   share: N = 0 40 / 13.90%, 11 / 2.91%, 24 / 8.97%, 3 of 3 [≥ 2]; N = 25
   8 / 4.56%, 0 / 0.02%, 0 / 0.00%, 0 of 3; N = 50 0 / 0.04%, 12 / 8.57%,
   0 / 0.01%, 1 of 3; E008 11 / 6.66%, 0 / 0.01%, 0 / 0.00%, 1 of 3.
2. Holds. Last-bin share 0.00% for prefix and inert in 3 of 3 seeds each;
   "last > 1%" prefix / inert 27,600 / 26,400, 27,800 / 25,900, 25,800 /
   25,700; ticks since injection max/min 1.86, 3.11, 1.14, ≤ 2 in 2 seeds
   [≥ 2].
3. Fails at N = 25, holds at N = 50. N = 25: prefix lost in 3 of 3 [≥ 2];
   "last > 1%" prefix / inert 28,400 / 26,600, 25,800 / 25,500, 25,700 /
   25,200, max/min since injection 2.12, 1.60, 3.50, ≤ 2 in 1 seed [≥ 2].
   N = 50: lost in 3 of 3; 25,100 / 25,200, 25,700 / 25,200, 26,500 /
   26,300, max/min 2.00, 3.50, 1.15, ≤ 2 in 2 seeds.
4. Holds, 3 of 3 seeds [≥ 2]: prefix / inert "last > 1%" 25,300 / 25,700,
   25,100 / 25,600, 25,400 / 25,500.

Both 26-byte genomes, with or without the self-scan, go from 50 bodies to
none living within 2,500–5,000 ticks under every rule, and prediction 3's
failure at N = 25 is the prefix lasting longer, not shorter, on spans of
200–3,400 ticks measured at 100-tick resolution. The 21-byte resident
establishes everywhere (11–70 living at tick 27,500) but its exact
canonical form keeps ≥ 1% of births to the end in only 6 of 12 runs, 3 of
3 only under N = 0, so prediction 1 fails as written.

### What this says (2026-10-08)

- **The injection works; the strict match does not.** Fifty copies of
  the 21-byte resident hold 10–25% of exact births in the first bin
  after injection and 11–70 living bodies at tick 27,500 in every run,
  so a body dropped into free memory with 100 units establishes.
  Prediction 1 fails under the three charge rules because the measure
  counts only the exact canonical form, which mutates away over
  10,000–25,000 ticks in a cloud where every lineage does; and in three
  worlds the form already existed before injection (7.6–9.6% of bin-10
  births), so the resident line is not purely injected descent. The
  control did its job (injection is survivable); the threshold was
  wrong.
- **The five-byte defence is lost under every rule, in every seed, in
  the parasitised world.** Both 26-byte genomes fall below 1% of exact
  births within 100–3,400 ticks of injection and have no living body
  from tick 30,000 in any of the 24 runs, while the resident injected
  the same way holds 10–25%. This is the same fate as in E009a, now
  with intruders present (foreign execution 12–15% at N = 0, 4–5% at
  N = 25, 1–2% at N = 50) and with 7–14% of the test bodies entered
  before they died.
- **Prediction 3 fails at N = 25 on the rate clause and holds on the
  maintenance clause.** The prefix is lost in 3 of 3 seeds at N = 25
  (last > 1% at 700–3,400 ticks after injection), but outlasts the
  inert control by factors 2.12, 1.60 and 3.50 in ticks since
  injection, against the ≤ 2 wanted in 2 of 3. The registered branch
  for "3 fails" was E009 at that N. The deviation is recorded here: the
  rate clause compares two genomes that each last 200–3,400 ticks from
  50 copies, at 100-tick resolution, and three seeds cannot separate
  "slower by 2" from placement luck (the bin-11 shares are 4.5 / 1.5 /
  0.8% against 3.2 / 0.7 / 0.4%). The maintenance clause is the gate's
  purpose, and it holds everywhere. Running E009 at N = 25 remains the
  registered option and is not ruled out by this reading; it is not
  recommended by it.
- **Why no owner-pays rule can pay for five bytes here, by the numbers.**
  Under the charge rules 7–14% of test deaths had been entered at all.
  An entry costs the owner at most one intruder pass, about 260 units
  times N / 100, and the self-scan saves nearly all of it. So the
  expected saving per host lifetime is roughly 0.1 × 65 units at
  N = 25 and 0.1 × 130 at N = 50, against a five-byte cost of about 5%
  of each cycle's 600-odd units, paid every cycle. The benefit is an
  order of magnitude short of the cost, and raising N does not close
  the gap because above the cliff the entered host dies and pays
  nothing further. The split-charge line is closed on this test: a cost
  that is paid rarely and bounded by one pass cannot select a defence
  that is paid for on every copy.
- **What would change it.** Either entries must be common (most hosts
  entered, many times), which needs intruders to profit from entry so
  that they proliferate, a transfer rule rather than a charge; or the
  defence must be no longer than the saving pays for, about one byte at
  these entry rates, which the endowment starver already is. E009 as
  designed (a 250,000-tick search for a defence under the split) is
  therefore not run; the next design is the transfer rule with this
  injection test as its first check, and the endowment byte tracked as
  the one-byte candidate.
