# E016: cost × ancestor, the defence search (2026-10-13)

Status: pre-registration written 2026-10-13, before any run. Two
parameters are left open here and are filled in from runs that are not
E016: the sun level (from T08's four gate arms under the fixed
`alloc`/`copy` edge, §2; resolved the same day, S = 2) and the tax control's `P` (from E016's own
cost-off tierra arm, calibrated as T02 §4.2, read before the tax arm
is launched). Everything else is fixed below. Runner:
`analysis/e016_defence.py` (to be written against this record; stages
`world`, `screen`, `lod`, `replay`). Needs T08 (built), T04 (snapshots,
not built: the `world` stage writes `--state-every 25000` and the
`replay` stage needs `--replay-from`; the `world` stage must not start
before T04 is built, since the snapshots cannot be added afterwards).

Bears on: H16 (gate 2, moved here from E014), H17 (its world shares
under the fixed physics with a same-sun std control, which is E015
stage 3 folded into the cost-off arms here), PLAN §8.3 and §9,
synthesis-2026-10-13 §3.6, literature §6.4 Q1 and §7.4 Q2 (a defence
with the fitness of every intermediate).

## Question

Under a graded, survivable, lifelong cost of being entered
(`--cycle-theft-pct 50`: an intruder's instruction on a host's byte
debits the host's per-tick budget by half the instruction's cost), in
a world whose ancestor has a one-hop parasite (the 41-byte template
body, E015), does a defence arise and is it maintained? If one does,
what is its path: the fitness of each intermediate in the harness and
against contemporaries, the parents and grandparents of the first
complete one (Croft 2024's look-back), and does it re-arise from the
snapshot before its first appearance under new seeds (potentiation,
Escondo & Ferguson 2026)? If none does in 30 seeds, that is a clean
negative against the Tierra-with-energy premise, reported as such.

## 1. What counts as a defence

Pre-registered, operational, tested in the two-genome harness with the
world's physics flags (cost included for the cost arms). The probe
parasite is the designed label flip: the arm's ancestor body with byte
18 (`nop1`, the first byte of L1) changed to `nop0` (T03 §3 test 2;
`parasite_jump`, entry offset 22). For a candidate genome G, two
harness runs of 3,000 ticks:

- `alone`: G alone (`--classify`-style); G's exact births `b_alone`.
- `probed`: the probe immediately before G (`--host HEX_PROBE
  --host-body G`); G's exact births `b_probed`, the probe's exact
  births `p_probed`.

Reference: the arm's ancestor A gives `b_alone(A)`, `b_probed(A)`,
`p_probed(A)`. Two kinds of defence, either qualifies:

- **Immune**: `p_probed(G) < 0.1 × p_probed(A)` with G
  replicator-class alone (the probe cannot use G's procedure: a new
  label pair, a changed entry, a check at the procedure).
- **Tolerant**: `b_probed(G) ≥ 0.9 × b_alone(G)` and `b_probed(G) ≥
  1.2 × b_probed(A)` with G replicator-class alone (G keeps its rate
  while entered: an eject, a reset, a self-check).

"Complete" means the harness test passes. "Maintained" means the
defence class (the set of complete genomes in a seed, by `func_hash`)
holds ≥ 1% of replicator-class exact births in every 25,000-tick
window from its first qualifying window to 250,000, or in every window
of at least 100,000 consecutive ticks. "Arises" means the first birth
of any complete genome in the seed, from `births.csv`.

Distance: for the template body an immune defence by relabelling needs
at least two coordinated changes (one in the `searchf` template, bytes
13–16, and the matching one in L1, bytes 18–21), since either alone
breaks the self-match; a tolerant eject is one insertion-sized change
(E009b's six bytes). The single-mutant neighbourhood (E015 stage 1) has
no complete defence of either kind by construction of the labels; this
is checked in the `screen` stage on the neighbourhood file before the
world runs and recorded here (expected: zero).

## 2. Arms and runs

30 seeds (1–30), 250,000 ticks, `--census 500`, `--state-every 25000`
(T04), single founder at byte 32,768 (as E007), default physics under
T08's fixed edge (no `--legacy-pending-range`), sun S:

| arm | flags |
|---|---|
| `tierra_n0` | `--ancestor tierra --sun S` |
| `tierra_t50` | `--ancestor tierra --sun S --cycle-theft-pct 50` |
| `tierra_tax` | `--ancestor tierra --sun S --cycle-tax-pct P --cycle-tax-frac F` |
| `std_n0` | `--ancestor std --sun S` |
| `std_t50` | `--ancestor std --sun S --cycle-theft-pct 50` |

S: 1 if T08's `tierra_fix` arm passes E004's gate (replicator-class
alive at 50,000 in ≥ 8 of 10), else 2 (`tierra_fix_sun2` passed at the
legacy edge 10 of 10; if the fixed-edge arm fails at sun 2 too, stop
and redesign, do not raise sun further without a new record). The
same S for every arm, so std is the same-sun control H17 lacked.

**Resolved 2026-10-13, S = 2** (E015 record, stage 2c; T08 gate arms
under the fixed edge, 10 seeds, 50,000 ticks): `tierra_fix` passes 1 of
10 at sun 1 (mean ration 86% against a 95.6% break-even), 10 of 10 at
sun 2 with parasite-lineage share 20.4% median (7.6–37.4%) in the last
bin and 24.8% of replicator-class deaths entered after 25,000, the same
as the legacy world; the edge was neither the margin problem nor the
source of the parasites. The same-sun std baseline for §4's reading:
`std_fix_sun2` parasite share 1.8% (1.1–3.3%; 6 of 10 at or under 2%),
entered 7.2%; at sun 1 0.6% and 4.4%.

`P`, `F` from `tierra_n0` exactly as T02 §4.2 (over replicator-class
deaths after 25,000: F = entered share, r = Σ `cycles_lost_m` / Σ
`age` read from `tierra_t50`, P = 100 r / (F × 32,000)). Record F, r,
P here before `tierra_tax` is launched. The tax arm is the bottleneck
control: the population pays the same time, not for being entered.

**Calibrated 2026-10-14** (`e016_defence.py calibrate`, `runs/e016/tax.json`;
seeds 1–30 pooled, replicator-class deaths after tick 25,000): F =
2,690,185 / 11,219,977 = 0.2398 entered in `tierra_n0`; r =
31,718,765,563,000 / 4,705,804,390 = 6,740.3 milli-units per
organism-tick in `tierra_t50` (12,371,784 deaths, their own entered
share 0.4299); P = 100 r / (F × 32,000) = 87.85, rounded to 88.
`tierra_tax` runs with `--cycle-tax-pct 88 --cycle-tax-frac
0.23976742554819855`. A first calibration on 2026-10-13 gave P = 86
(F = 0.2406, r = 6,615.0 over 7,978,799 `tierra_t50` deaths) and the
tax arm ran at it; it was wrong because a reboot during the world
stage had cut 24 runs' `--classify` part-way (`tierra_n0` s26–s30,
`tierra_t50` s1–s13 and s15–s20) and the runner's resume took the
short class lists as finished, so the replicator-class death sets
were incomplete (commit `ca7e436` makes the resume check them). Those
P = 86 runs are kept aside as `runs/e016/tierra_tax_p86/` and read in
§8 only as a second tax level. Seed 14 of the tierra arms went extinct
at tick 252 in both `tierra_n0` and `tierra_t50` (the founder died
after one birth, before any theft could differ between the arms); it
stays in the pooled sums (it contributes nothing after 25,000) and
counts as a seed with no defence in §3's per-seed reading.

Run order: `tierra_n0`, `tierra_t50`, `std_n0`, `std_t50` together
(120 runs; about 2 minutes each at 250,000 ticks, 9 at a time on the
desktop, so about 30 minutes at 24 wide), then `tierra_tax` after
calibration. Directories `runs/e016/<arm>/s<seed>/`, CSVs gzipped as
E014's runner does.

E015 stage 3 is read from `tierra_n0` and `std_n0` at tick 50,000
(same measures as T03 §4 stage 3, same 30-seed count); it is not run
separately. H17's world shares are judged there.

## 3. Pre-registered measures

Per 2,500-tick bin per seed (`world` stage), on top of E015's set
(parasite-lineage share of exact births, entered and resident shares
of replicator-class deaths, IP-outside-body share, nop share, length
percentiles):

- `defence_share`: exact births by complete-defence genomes over
  replicator-class exact births (needs the `screen` stage first).
- `immune_share`, `tolerant_share`: the same split by kind.
- `cycles_lost_per_tick` on replicator-class deaths (E014's column),
  `entered_cpt_norm` on reproducers only (E014's amendment: offspring
  per tick of entered reproducers over unentered, `age` > 50,
  `offspring` > 0).
- T05's columns through `measures.compute` with `--group
  defence_class` (complete / not / unmatched), read as T05's outcome
  rule says: the class share first, `qnn` over the class second,
  `qnn` over `func_hash` as turnover context.

`screen` stage: every replicator-class `func_hash` with ≥ 0.5% of a
window's exact births, or ≥ 50 exact births in the run, is harness-
tested per §1 under the arm's flags; results in
`runs/e016/<arm>/s<seed>/defence.csv` (`func_hash, len, b_alone,
b_probed, p_probed, immune, tolerant, first_tick, last_tick`). The
screen is also run on the whole single-mutant neighbourhood of both
ancestors (E015 stage 1 files) before the world stage, as the
reachability baseline.

`lod` stage (T06's method): for every seed with a complete defence,
the line of descent to the first complete genome, with the harness
fitness of each step alone and probed, and the world fitness in bins of
a few thousand ticks against contemporaries (T06's rule: the world
column first, the harness second, break-and-repair pairs paired off).
Croft's look-back: the first complete genome's parent and grandparent
classified by how much of the defence they carry (for an immune
relabelling: which of the template and label changes is present; for
a tolerant eject: which bytes of it). Time-to-loss: for every lineage
that first carries a complete defence, ticks until its last exact
birth.

`replay` stage (T04): for each seed whose first complete defence
appears at tick t, replay from the snapshot at the last multiple of
25,000 below t with 10 new seeds to t + 50,000; count replays in which
any complete defence arises. Potentiation is read as that count
against the count in 10 replays from the same arm's seeds with no
defence by 250,000, from their 25,000 snapshot (the background rate).

## 4. Predictions

H16 gate 2 (moved from E014): in `tierra_t50`, a maintained defence
in ≥ 10 of 30 seeds, against ≤ 2 of 30 in `tierra_n0` and ≤ 2 of 30
in `tierra_tax`. `std_t50` against `std_n0`: no prediction of a
defence (the std ancestor's intruders are placement accidents and not
resident, E014), reported.

H17 (E015 stage 3, read at 50,000 from the `n0` arms): parasite share
> 5% in ≥ 20 of 30 `tierra_n0` seeds against ≤ 2% in `std_n0`;
entered share > 25% against 7–14%. Under the fixed edge both numbers
are expected lower than E015's legacy-world figures (8–27% and
23.5–26.4%), since part of those was manufactured; how much lower is
the first thing the record reports.

Refutes H16 gate 2: no maintained defence in `tierra_t50` beyond the
`n0` rate, or a defence maintained equally under `tierra_tax` (then
the cost, not the intruder, selects it). A defence that arises and is
lost in every seed is reported with time-to-loss and is not a pass.

## 5. Decisions already taken that this record inherits

N = 50 (E014 pilot: cost on reproducing hosts 0.90 at N = 50, graded
0.97 / 0.90 / 0.85 at 25 / 50 / 75; tax control clean). The tierra
body of E015 (41 bytes, K = 127, four-nop labels). The fixed edge
(T08) as the physics, with every run before 2026-10-13 the legacy
world. One founder (E013 showed sixteen founders change nothing after
the founder phase; one founder keeps E007 comparable, and seeds that
lose the founder are counted and excluded as E007 did).

## 6. Not decided here

Whether `drain` follows (PLAN §8.3) is read after this record's
results. Insertions in `--neighbours` (a tolerant eject is an
insertion) are a T03 extension for the negative-case reachability
argument, built only if no defence appears.

## 7. Amendments before launch (2026-10-13, from the runner's smoke runs)

The runner (`analysis/e016_defence.py`, commit `28f029e`) was built
against §1–§3 and smoke-tested on 2,000- and 30,000-tick worlds before
any E016 run. Four things in the registration do not survive contact
with the harness and the smoke worlds. They are amended here, before
the first run, and the original text above is left as written.

1. **The immune rule had no viability floor and the probe harness
   stops when the probe dies.** The single-mutant neighbourhood is not
   defence-free: tierra has 85 "immune" single mutants at `n0` (78 at
   `t50`), std 97, nearly all endowment raises (`lit A {e}`, byte 33
   tierra / byte 17 std) or absorb-count changes (byte 7 / byte 6). The
   probe runs the host's procedure with the host's operands, divides
   with an endowment it cannot pay, and starves at its first division,
   so `p_probed` is 0 after about 10 ticks. Most of these barely
   replicate alone (tierra `b_alone` ≤ 19 against the ancestor's 119;
   std's endowment raises keep the full 230). Amended rule, both kinds:
   G must be replicator-class alone **and** `b_alone(G) ≥ 0.5 ×
   b_alone(A)`. And every complete genome is classed by mechanism:
   **`parameter`** if it differs from the arm's ancestor only in the
   operand bytes of `lit A {k}` and `lit A {e}` (`traits.py`'s ABSORB /
   ENDOW positions for the body), **`structural`** otherwise.
   `parameter` defences are reported (share, seeds) but do not count
   toward H16 gate 2; the gate is read on `structural` defences. The
   same endowment raises appear in std smoke worlds by tick 200, so
   without this split every std seed would be "complete" at once.
2. **"Maintained" could pass on one late window.** Amended: the
   defence class holds ≥ 1% of replicator-class exact births in at
   least four consecutive 25,000-tick windows (100,000 ticks), anywhere
   in the run. The "to 250,000" clause is dropped.
3. **Structural defences arise before the first snapshot.** In all
   three `t50` smoke seeds two-change relabellings (template byte 15
   with a matching L1 byte) appear by tick 500–1,800 and hold 32–52% of
   window 1. The one-change label flip is a viable parasite and the
   second change restores self-matching with a new pair, so the
   relabelling is two steps away through a parasite intermediate (the
   look-back is expected to show exactly that). Two amendments:
   snapshots every **2,500** ticks (`--state-every 2500`; about 90 MB
   raw per run, gzipped by the runner after the run and inflated for a
   replay), and the replay rule uses the last multiple of 2,500 below
   t. A defence with t < 2,500 is replayed from tick 0 with new seeds,
   which is the per-seed arising rate itself, and is reported as "from
   the founder" rather than as potentiation.
4. **Gate 2's `n0` clause is likely to fail for the wrong reason.** If
   relabellings are near-neutral they will arise in `tierra_n0` too,
   and "≤ 2 of 30 seeds with a maintained defence in `n0`" would be
   failed by mutation supply, not by selection. The gate stands as
   registered (it is H16's claim and the failure is informative), and a
   second, paired reading is added: `structural` defence share at
   250,000 (and the number of maintained seeds) in `tierra_t50` against
   `tierra_n0` and `tierra_tax`, paired by seed, sign test over 30
   seeds; prediction `t50 > n0` and `t50 > tax` in ≥ 20 of 30 pairs
   each. H16 gate 2 passes on the registered gate; the paired reading
   is how a cost that raises an already-present defence is reported if
   the gate fails.

Implemented in the runner (commit `98ae921`). One reading of item 1
accepted: G is compared with the ancestor on the canonical form
(`traits.canonical_instrs`), so a byte change that leaves the
`func_hash` unchanged is not a difference; byte for byte, every std
smoke-world endowment raise carried such a silent flip and would have
been `structural`. Neighbourhood baseline after the floor: tierra 0
complete of 85 (`n0`) and 78 (`t50`); std 22 of 97, 20 `parameter`
(endowment 35–54) and 2 `structural` (byte 19, the `sub B` after
`divide`, to `0x2f` or `0xaf`). World stage launched 2026-10-13 with
`world --jobs 24` (four non-tax arms, 30 seeds).

Runner choices the record left open, accepted as implemented: F from
`tierra_n0` as §2 says (T02 took it from the cost arm; both are kept
in `tax.json`); candidate share over all exact births in the window;
each `func_hash` tested on its most common raw body; `entered_cpt_norm`
over replicator-class reproducers; the H17 parasite set computed on
the run cut at 50,000; the neighbourhood screen under every arm's
flags; replay seeds 1001–1010; background replays from 25,000 to
100,000 with no-defence seeds cycled if fewer than 10. The std probe
is the `pad` (`--host 00`, E005/E014's fall-through intruder), since
std has no label to flip; a std "defence" is therefore against a
placement accident, which is why §4 makes no std prediction.

Cost: a 250,000-tick run writes about 1 GB of CSV before gzip (the
four killed smoke runs reached 2.6 GB at tick 168,000); gzipped, 150
runs are an estimated 15–20 GB plus snapshots. The desktop has 218 GB
free at launch.

## 8. Results (2026-10-14)

Runner `analysis/e016_defence.py`; outputs under `runs/e016/`
(`screen.csv`, `bins.csv`, `runs.csv`, `summary.md`, `lod_seeds.csv`,
`lod_summary.md`, `replay.csv`, `replay_summary.md`; per run
`defence.csv`, `measures/`, `analyse.json`, `lod/`). Every number below
is in those files; the per-seed tables are in `summary.md` and
`lod_summary.md` and are not repeated here.

### 8.1 The runs

150 runs of 250,000 ticks: the four non-tax arms launched 2026-10-13
(`world --jobs 24`, 1,077 s for the 120 once resumed), the tax arm
2026-10-14 at P = 88 (§2; 660 s). A reboot during the batch's
`--classify` step cut 24 class lists short (tierra_n0 s26–s30,
tierra_t50 s1–s13 and s15–s20); the runner's resume accepted them until
`analyse` failed on a half row, the check in commit `ca7e436` now
re-classifies such a run, and the 24 were redone before anything below
was computed. The tax calibration moved from P = 86 to P = 88 with the
whole class lists (§2); the P = 86 runs are kept as
`runs/e016/tierra_tax_p86/` and read only in §8.2.

Seed 14 of both tierra arms lost its founder at tick 252 (the same
tick in both: the two arms run the same stream until the first cost
event), so those two runs have no candidates and count as seeds with
no defence, as §2 says (the tierra gate counts below are "of 30" with
seed 14 a no); `tierra_tax` s14 survives (the tax draws from tick 0
and changes the stream). Every std
run and every other tierra_n0 and tierra_t50 run persists to 250,000
(population at the end, median: tierra about 1,530, std about 1,900 to
2,050).

**The tax arm is not survivable.** Under `--cycle-tax-pct 88
--cycle-tax-frac 0.2398`, 25 of 30 seeds die out: s6, s21, s11 and s30
at ticks 38, 64, 149 and 1,262, then 21 seeds in a wave between 35,690
(s7) and 54,330 (s9); s3, s14, s20, s22 and s25 reach 250,000. The
P = 86 arm did the same (21 of 30 extinct). The targeted cost at N = 50
kills no seed, the random tax calibrated to the same mean debit kills
most: the tax falls on every replicator with probability F regardless of
state, where the theft falls on entered hosts, which are the ones that
die anyway (the harness reference below: an entered tierra ancestor
makes 1 exact child in 3,000 ticks under the cost). In the harness the
tax alone lowers the ancestor's births from 119 to 93 (`defence_ref.json`
of the tax arm). So the tax control cannot be read as §4 meant it
("maintained equally under the tax"): where the tax is survivable the
population is one that outlived a 40,000-tick crash, and where it is
not there is nothing to maintain. The §7.4 pairing against the tax arm
is reported below and is not informative for the same reason.

### 8.2 The screen

Harness reference per arm (`defence_ref.json`; `b_alone`, `b_probed`,
`p_probed` of the arm's ancestor with the arm's probe before it, 3,000
ticks):

| arm | `b_alone` | `b_probed` | `p_probed` |
|---|---|---|---|
| tierra_n0 | 119 | 119 | 119 |
| tierra_t50 | 119 | 1 | 119 |
| tierra_tax | 93 | 48 | 92 |
| std_n0 | 230 | 230 | 340 |
| std_t50 | 230 | 116 | 340 |

Two things in this table were not known before the run. Without a
cost the label-flip probe costs the tierra ancestor nothing (119
births entered or not): it reads the host's procedure and the host
keeps its own rate, as Tierra's parasites did. Under the 50% theft the
entered tierra ancestor makes 1 exact child in 3,000 ticks against 119
alone; the std ancestor with its `pad` probe keeps half (116 of 230).
E014's 0.90 at N = 50 was the std body with a fall-through intruder
that runs a few bytes; a searching parasite runs the host's whole copy
loop in the host, and at N = 50 the host's budget goes with it. H16's
"graded, survivable" reads differently for the two bodies: graded for
std, near-lethal for tierra in the harness, while the tierra world
persists in 29 of 30 seeds under it with 43% of replicator-class deaths
entered. (Caveat on `b_probed` for immune genomes: the probe harness
stops when the probe dies, so `b_probed` of a complete genome is 1 or 0
by construction and says nothing about the host.)

Candidates and complete genomes, totals over the arm's runs
(`screen.csv`, `defence.csv`; "viable" = replicator-class alone with
`b_alone` ≥ half the ancestor's, §7.1):

| arm | runs with a candidate | screened | viable | complete | of which structural | parameter | tolerant |
|---|---|---|---|---|---|---|---|
| tierra_n0 | 29 | 29,983 | 21,935 | 20,741 | 20,741 | 0 | 0 |
| tierra_t50 | 29 | 37,894 | 30,896 | 29,737 | 29,737 | 0 | 0 |
| tierra_tax | 28 | 5,011 | 4,100 | 3,837 | 3,837 | 0 | 8 |
| std_n0 | 30 | 32,061 | 31,910 | 5,742 | 295 | 5,447 | 0 |
| std_t50 | 30 | 33,299 | 33,219 | 6,899 | 682 | 6,217 | 0 |

In the tierra arms 95% of every viable candidate is immune (20,741 of
21,935; 29,737 of 30,896); the probe reproduces at all on 1,195 and
1,159 of them, which are the ancestor and the mutants that keep its
labels. The complete genomes are the relabelling §1 named: of the
31,349 complete tierra genomes of the ancestor's length (41 bytes, n0
and t50 together), 31,304 change at least one byte of the `searchf`
template (bytes 13–16) **and** at least one of L1 (bytes 18–21); 40
change L1 only, 4 the template only, 1 neither. The rest of the complete
set (12,607 and 18,742 of the ancestor's length; the others shorter or
longer bodies) is the same relabelling in bodies that have changed
elsewhere too. No tolerant genome arose in the tierra arms (8 in the
tax arm, all in dying seeds). In the std arms almost every complete
genome is a `parameter` one (endowment raises, as §7.1 expected); the
structural std set (295 and 682 `func_hash`es) is a pad-placement
defence and is read below only for completeness.

Seeds with a structural complete genome: tierra_n0 29 of 30, tierra_t50
29 of 30, tierra_tax 21 of 30, std_n0 30 of 30, std_t50 27 of 30. First
structural complete genome, median tick: tierra_n0 1,859, tierra_t50
1,865 (max 9,402 and 9,823); std 46,393 and 16,927. Parameter defences
arose and were maintained in every std seed (60 of 60) and in no tierra
seed.

### 8.3 H16 gate 2

Registered gate (§4): seeds with a maintained structural defence (≥ 1%
of replicator-class exact births in four consecutive 25,000-tick
windows): **tierra_t50 29 of 30, tierra_n0 29 of 30, tierra_tax 5 of
30** (the five survivors, every one of them); std_t50 1 of 30 (s8, 8
windows), std_n0 1 of 30 (s21, 5 windows). The gate needed ≥ 10, ≤ 2
and ≤ 2: **fails on the `n0` clause**, in the way §7.4 said it would
fail. The relabelling is a defence against the registered probe, it is
two substitutions away, and it arises by tick 2,500 in 22 of 29
tierra_n0 seeds and 21 of 29 tierra_t50 seeds, cost or no cost. It then
holds 15–25% of replicator-class exact births in every window of every
`n0` seed (per-window medians over seeds at 50,000 / 100,000 / 150,000
/ 200,000 / 250,000: 19.3%, 15.2%, 19.3%, 17.4%, 14.9%). Mutation
supply, not the cost, makes it common.

Paired reading (§7.4), tierra_t50 against tierra_n0 by seed, 29 pairs:
structural share of replicator-class exact births in the last
2,500-tick bin, t50 above in **23 of 29**, below in 6, sign test p =
0.0023 (prediction ≥ 20: **holds**); per-window medians in t50 26.4%,
20.4%, 22.0%, 21.3%, 20.6% against the `n0` figures above; the
structural class's share of census bodies after 25,000, median over
seeds, 3.06% (1.52–6.47%) against 1.80% (0.84–4.33%). "Maintained"
yes/no is tied in all 29 pairs. Against the tax arm: share at the end
t50 above in 3 of 4 pairs (26 unpaired, the extinct seeds), maintained
above in 25 of 30 (the 25 extinctions): both uninformative (§8.1).

So the cost raises the relabelled class's share by about a third
(20.6% against 14.9% at the end, 23 of 29 pairs) and does not create
it. The share never approaches 100% in either arm, and the entered
share of replicator-class deaths after 25,000 stays at 43.0% (39.5–47.8%)
in tierra_t50 against 23.6% (22.5–27.2%) in tierra_n0, because the
defence is against one label: a relabelled lineage has its own one-hop
parasite, which follows it. This is Tierra's immunity by label change,
and it is a moving target, not a closed door.

Cost measures in the world (`runs.csv`, after 25,000, medians over
seeds): debit per tick of entered replicator-class deaths 21,194
milli-units in tierra_t50 (66% of the 32,000 cap; std_t50 12,140,
38%); offspring per tick of entered over unentered reproducers 0.53
in tierra_t50 against 0.72 in tierra_n0 (normalised 0.73; std 0.75
against 0.95, normalised 0.79). The cost is graded in the world as E014
measured it in the harness, for both bodies.

std: the structural std set is maintained in one seed per arm and is
lost at once elsewhere (§8.4). No std prediction was made and none is
read.

### 8.4 Line of descent, look-back, time-to-loss (`lod` stage)

79 tierra lines (29 + 29 + 21) and 57 std lines. Tierra: the line to the
first structural complete genome is short (median 31 organisms in
tierra_n0, 36 in tierra_t50, 45 in tierra_tax; median 6 steps after
pairing, of which in the two non-tax arms a median 5 are neutral alone
in the harness, 0 beneficial, 0 deleterious; tax 1 / 4 / 1); the world
column (T06's first reading: the
last step's child's exact children per death against its
contemporaries in its 2,500-tick bin) is above 1 in 19 of 29, 20 of 29
and 17 of 21 lines, median 1.18, 1.21 and 1.27. Neutral alone,
favoured in the world: the signature of a defence, and of the same size
with and without the cost. Look-back (Croft): the first complete
genome's parent carries a median 80% of its edits from the ancestor
(all of them in 1 line, none in 2); the parent's body as it was at the
division that made the first complete genome carries all of them in 34
of the 47 lines where that body is recorded; the grandparent a median
67%. The two coordinated changes therefore do not arrive by the route
§7.3 expected (a label flip that is a viable parasite, then the
matching template change): they are already both in the parent's
body in most lines, written into it during its life, and the first
"complete" child is that body copied. Time-to-loss: a relabelled
lineage's origins are thousands per run (median 6,273 in tierra_n0,
5,599 in tierra_t50); the median origin has no further exact births
(time-to-loss 0), the longest-lived lose it after 14,064 and 13,273
ticks, and about 30 lineages per run are alive at 250,000 (censored).
The class persists; its lineages turn over.

std: 37 steps median (14 paired), B / n / D 3.5 / 17 / 6, world column
0.81 (std_n0) and 1.06 (std_t50); origins 148 and 513 per run, the
first origin lost after 10 and 21 ticks (medians). The structural std
"defence" is deleterious in the world and is lost as it arises.

### 8.5 H17 (E015 stage 3, read at 50,000 from the `n0` arms)

Parasite-lineage share of exact births in the bin ending at 50,000:
above 5% in **29 of 30** tierra_n0 seeds (prediction ≥ 20), median
22.2% (7.6–40.0%); at or below 2% in 24 of 30 std_n0 seeds (≥ 20),
median 1.36% (0.46–3.33%): **holds**. Entered share of replicator-class
deaths in (25,000, 50,000]: tierra_n0 median 23.6% against the
registered > 25%: **fails by 1.4 points**; std_n0 7.23%, inside 7–14%.
E015's legacy-world figures (23.5–26.4% entered, 8–27% parasite share)
are the fixed-edge figures too: the `alloc`/`copy` edge manufactured
no part of the template body's parasitism that this measure can see.
Over the whole run the parasite share in the last bin is 19.2%
(1.8–33.7%) in tierra_n0 and 31.0% (1.5–47.6%) in tierra_t50 against
1.4% and 2.2% in std.

### 8.6 Replays (`replay` stage)

Pending at the time of writing (the stage runs; about 1,380 replays). What
the first 290 show: every tierra_n0 replay, from the founder (22
seeds) or from the 2,500-tick snapshot before the first relabelling (7
seeds), produces 171–217 structural complete genomes by tick 50,000.
With an arising rate of 100% the potentiation count against the
background rate is not informative, as §7.3's "from the founder" clause
anticipated for t ≤ 2,500. The table is added here when the stage ends.

### 8.7 Reading

1. **H16 gate 2 fails as registered and the paired reading holds.** The
   only defence that arose is Tierra's relabelling; it arises in every
   tierra seed by mutation supply, with or without the cost, and the
   cost raises its share by about a third (23 of 29 pairs, p = 0.0023).
   No tolerant defence (eject, reset, self-check) arose in 150 runs.
2. **The tax control failed as a control.** The random tax at the
   calibrated rate kills 25 of 30 seeds where the targeted theft kills
   none; the two debits are not interchangeable at the population level
   even at the same mean. A survivable control needs a different design
   (a lower P that matches the surviving arms' population, or a tax on
   entered hosts' neighbours), decided outside this record.
3. **H17 holds on the parasite share and misses the entered threshold
   by 1.4 points**, with the std control inside its band on both.
4. The relabelling is complete in the registered sense and open in the
   evolutionary one: every new label has its own one-hop parasite, the
   entered share under the cost stays at 43%, and the class's lineages
   turn over in thousands of origins per run. Whether a closed defence
   exists for this body (a longer label, a check at the procedure, an
   eject) is §6's question, and the neighbourhood screen (0 complete
   single mutants of 10,496 for tierra) says it is not one substitution
   away.
5. Not decided here: `drain` (PLAN §8.3, §6 above). The write-up of
   E016 and the `drain` decision go to Derek with this record.

### 8.8 What the immune class is, measured (T11 §2, 2026-10-15)

§8.7 item 4 said "every new label has its own one-hop parasite". T11
§2 (`analysis/t11_closed.py own`, `runs/e016/own_nbhd/`, commit
`ceda9e7`) measured it on the 34 most common structural complete
genomes of the two non-tax arms (the top 20 of the ancestor's length
and the 14 other lengths in the overall top 20, ranked by
replicator-class exact births over all runs), each run through
`--neighbours G` against itself under `tierra_n0`'s physics and probed
with its own label flip. The sentence is wrong for 28 of the 34.

- **15 have no label.** 32–36 bytes, no `searchf` or one with an empty
  template; the procedure is reached by running straight on, as the
  21-byte body does. Immune to the registered probe because the probe's
  search finds no label to enter. By births this class is 40% of the
  immune structural class: 761,276 of 1,884,620 replicator-class exact
  births in `tierra_n0` from bodies shorter than 41 bytes (8,116 of
  20,741 genomes), 1,107,125 of 2,842,736 in `tierra_t50` (10,984 of
  29,737); bodies longer than 41 are 0.1%. The relabelling of §8.2 is
  the other 60%.
- **12 of the 19 labelled bodies are closed against their own flip.**
  The template is down to 1–2 nops and a second copy of the label sits
  later in the body (in 11 of the 12 inside the `searchb` template), so
  a flipped mutant's search finds that copy inside itself and never
  runs a byte of G: 0 `parasite_jump` rows on the label, against the
  ancestor's 996 of 1,121 under the same physics.
- **6 stay open** (ranks 6, 21, 22, 25, 31, 32): the flip finds G's L1
  (entry 20–22) or L0 (entry 3), 489–498 rows on the label.

Every body keeps the fall-through parasites (median 228
`parasite_fallthrough` rows; ancestor 228) and 60–140 fixed-offset
`parasite_jump` rows (ancestor 125 off the label). All 34 are immune to
the registered probe. All but one `func_hash` occurs in one run only.

Reading: Tierra's immunity by relabelling is the minority of what
arose. The common outcomes are the loss of template addressing (the
world walks back to the straight-line body, which has no one-hop
parasite by search) and a redundant label that closes the search
against a single flip. §8.7 item 4's "moving target" holds for 6 of 34
top bodies; for the rest the defence is closed against the label
parasite and open only to the fall-through one, which every body in
this world has. The record's claim that no closed defence exists one
substitution away stands (the neighbourhood screen); the claim that
none arose does not.

