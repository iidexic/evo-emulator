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
