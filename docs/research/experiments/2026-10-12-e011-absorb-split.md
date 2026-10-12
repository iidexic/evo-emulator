# E011: is there a producer/consumer split in E007? (2026-10-12)

Status: design and predictions written 2026-10-12, before any query of
the E007 files for the measures below. The E007 record and its window
tables had been read; none of them reports `absorbs`, `executed`,
`absorb_gain_m` or `born_with_m` per organism or per genome. One E007
column was read while designing E012 (`writes_blocked`, seeds 1 and 2)
and has no bearing here. No new run: the data are the ten E007 runs
(`runs/e007/std/s<seed>/`, Linux, commit fa60c1c), so this experiment
can only be done on the machine that holds them.

Bears on: H2 (producer/consumer split is diagnostic, 2026-09-27; the
2026-10-09 note says it is testable from the E007 death records and
has not been tested), the gap review of 2026-10-09 (§1), E005 and E007
(fall-through parasites are 0.8–1.0% of exact births and run the
host's absorb loop with their own energy).

## Question

H2 predicts a bimodal distribution of absorb fraction per genome: a
high mode of producers that spend their cycles on `absorb`, and a
persistent low mode of organisms that get most of their energy some
other way, which depends on the high mode. If the split does not appear
in a long run, H2 says the energy ratios are wrong: absorbing is too
cheap relative to copying, or parasitism pays nothing.

E007 is the long run of the standard world. Its death records hold
every organism's lifetime `absorbs`, `executed`, `absorb_gain_m` and
`born_with_m`, so the distribution can be read off the files.

## What the physics allows, written before the query

In the standard world an organism has exactly two incomes: its
endowment at birth (`born_with_m`) and `absorb`. Nothing moves energy
between living organisms (no `drain`; `--charge-owner`,
`--charge-owner-pct` and `--transfer-pct` are off, so `paid_by_others_m`
and `gained_from_others_m` are 0). A fall-through parasite runs the
host's code but pays for it and absorbs with its own registers into its
own store. So the interaction H2 calls parasitism moves code and
placement, not energy, and there is no route by which a "consumer" can
get most of its energy from a producer.

The cycle of the ancestor's form is about 4K + 94 instructions (5 of
preamble, the absorb loop of 4 per pass, `alloc`, the copy loop of 4 per
byte for 21 bytes, 4 to divide and restart), of which K are `absorb`.
At K = 120, the E007 phenotype from window 2 on, that is
120 / 574 = 0.21 of instructions. The one-byte parasite `pad` runs the
same preamble and absorb loop and copies one byte: about 4K + 15
instructions, so 120 / 495 = 0.24. The parasite spends a larger share
of its instructions on `absorb` than its host does. A cycle costs about
165 + 4K units plus the child's endowment, and bodies are born with
16–85 units, so a body that makes two exact children has absorbed
several times its endowment.

## Data and units

- Runs: E007 seeds 1–10, 250,000 ticks. Seed 10 died at tick ~1,180 and
  is reported but left out of medians, as in E007.
- Carriers: every organism, from `deaths.csv`, plus the organisms alive
  at the last census (`orgs.csv` at tick 250,000), with `executed` ≥ 1.
- Per carrier: instruction share a = `absorbs` / `executed`; income
  share g = `absorb_gain_m` / (`absorb_gain_m` + `born_with_m`).
- Genome: the raw birth hash, as E005's tables use (`birth_hash` in the
  carrier rows). In scope: genomes with ≥ 2 exact births (E005's
  world-replicating set; exact means `raw_hash == parent_now_hash` in
  `births.csv`). Per genome, pooled over its carriers:
  a_G = Σ`absorbs` / Σ`executed` and
  g_G = Σ`absorb_gain_m` / Σ(`absorb_gain_m` + `born_with_m`).
- Weight: the genome's exact births. Distributions over genomes are
  reported both weighted by exact births and unweighted.
- Groups: replicator-class (harness class `replicator` in
  `classes.csv`), dependent (in scope, class not `replicator`), and
  parasite (E005's 2+-children test, `parasite_2` in
  `runs/e007/std_s<seed>_dependent.csv`).
- Windows: E007's ten windows of 25,000 ticks. Per window, the carriers
  that die in it (and, for window 10, those alive at the end) and the
  exact births in it; a genome is in scope in a window if it has ≥ 2
  exact births there.
- The low-absorb mode is defined as in-scope genomes with g_G < 0.5,
  which take most of their lifetime income from somewhere other than
  `absorb`. In this world that can only be the endowment.

## Predictions

1. **No low-absorb mode.** In every window from 2 on, genomes with
   g_G < 0.5 hold under 1% of the window's exact births, in at least 8
   of the 9 surviving seeds. The exact-birth-weighted median g_G is
   above 0.9 for replicator-class genomes and for parasite genomes in
   every seed.
2. **The parasites absorb more, not less.** Over the whole run, the
   exact-birth-weighted median a_G of parasite genomes is higher than
   that of replicator-class genomes in at least 8 of 9 seeds. Ranges,
   per seed, whole run: replicator-class 0.17–0.23, parasite
   0.20–0.25. (Carriers that die mid-cycle pull a_G toward whichever
   loop they died in, so the ranges are wider than the cycle
   arithmetic above.)
3. **One mode.** The exact-birth-weighted distribution of a_G over
   in-scope genomes has at least 90% of its weight in [0.15, 0.26] in
   every window from 2 on (median over seeds).
4. Exploratory, no threshold: the per-carrier distributions of a and
   g over all carriers, reproducing or not. Newborns that die before
   absorbing have g near 0 and are a large share of deaths (24% of
   replicator-class deaths are newborns, E007), so a per-organism
   histogram may well be bimodal. That is not H2's split, which is per
   genome and over many generations, and it is reported only so that
   nobody reads it as one. Also: the same tables grouped by `func_hash`
   instead of raw hash.

## Scoring H2

- **Refuted** if prediction 1 holds: no persistent low-absorb mode
  (H2's own refutation, "unimodal absorb-fraction"). H2's diagnosis for
  that case is "absorbing is too cheap relative to copying, or
  parasitism pays nothing"; the reading registered here is the second,
  in energy: the only interaction moves code, and the physics has no
  energy flow between organisms. That is the same diagnosis E008–E010
  reached from the cost-rule side.
- **Supported** if genomes with g_G < 0.5 hold at least 5% of exact
  births in the median window from 2 on and at least half of that
  weight is dependent-class.
- **Mixed** otherwise.

## Runner

`analysis/e011_absorb_split.py`: reads each seed's files lazily (the
`deaths.csv` files are about 420 MB each), one seed at a time, and
writes `runs/e011/genomes_s<seed>.csv` (per genome per window),
`runs/e011/seeds.csv` (per seed and window: the prediction measures)
and `runs/e011/summary.md`.

## Caveats, known now

- One world. H2 was written for the Phase 1 physics; the standard world
  is the one the project now runs, and E007 is the only long run of it.
- g counts the endowment as non-absorb income. A genome whose carriers
  reproduce on a large endowment alone would show as low-absorb; none
  is expected (the cost arithmetic above), but if one appears it is a
  consumer of its parent, not of a producer of another genome.
- The pooled shares weight long-lived carriers more (they executed
  more). That is the intended reading of "spends most cycles on".

## Results (2026-10-12)

`analysis/e011_absorb_split.py` over E007 seeds 1–10 (seed 10: 3
births, no exact birth, left out of medians), about 6 s per seed;
output in `runs/e011/` (`summary.md`, `seeds.csv`, per-seed genome and
`func_hash` tables, `hist.csv`, `carriers.csv`, `sanity.csv`). Checks:
births + founder = deaths + alive in every run; the in-scope sets equal
E005's world-replicating sets and the dependent counts equal E005's
tables exactly; every carrier has `born_with_m` > 0 (the 53,000–79,000
rows per run with 0 are stillborns with `executed` = 0); the E007 files
have no other-income columns. Seed 2 was recomputed independently from
the raw files and matched to every digit; the post-hoc somatic share
below was rechecked on seed 1.

### Numbers

Medians over seeds 1–9, exact-birth-weighted over in-scope genomes.

| | replicator-class | parasite | dependent | all in scope |
|---|---|---|---|---|
| genomes per seed (whole run) | 15,151 | 211 | 20,864 | 35,973 |
| g_G, whole run | 0.992 | 0.989 | 0.973 | 0.991 |
| a_G, whole run | 0.229 | 0.245 | 0.217 | 0.228 |
| a_G, per window 2–10 | 0.225–0.228 | 0.238–0.246 | 0.216–0.218 | |

Share of the window's exact births held by in-scope genomes with
g_G < 0.5, medians over seeds, windows 1–10: 2.13, 2.37, 2.31, 2.48,
2.19, 2.41, 2.40, 2.30, 2.09, 2.38%; per seed-window from window 2 on,
1.84–2.89%. Weighted share of a_G in [0.15, 0.26], windows 2–10:
0.974–0.978 (lowest seed-window 0.967).

### Predictions

1. Under 1% low-absorb share in every window from 2 in ≥ 8 of 9 seeds,
   and g_G above 0.9 for replicator-class and parasite genomes: **not
   confirmed**. The g_G half holds (0.992 and 0.989; above 0.979 in
   every seed-window). The share half fails in every seed: 1.84–2.89%,
   never under 1%.
2. Parasites' a_G above the replicator-class a_G in ≥ 8 of 9 seeds:
   **confirmed**, 9 of 9 (0.241–0.247 against 0.228–0.229; 80 of 81
   seed-windows). Both inside the registered ranges, the
   replicator-class values at the top edge of 0.17–0.23.
3. ≥ 90% of the weight of a_G in [0.15, 0.26] in every window from 2:
   **confirmed**, 0.974–0.978.
4. Exploratory: per carrier, g is bimodal as anticipated: 60% of
   carriers in [0.95, 1], 8.6% in [0, 0.05), and 99.5% of that low bin
   are carriers with no offspring. Among carriers with at least one
   child, 90.2% have g ≥ 0.95 and 0.2% below 0.05. Per carrier, a has
   78% of carriers in [0.20, 0.25) and a newborn tail below 0.15 (15%);
   only 127 of 22.3 million carriers are above 0.5. Grouped by
   `func_hash` the three checks come out the same (0 of 9, 9 of 9, 9 of
   9; low-absorb share 2.05–2.44% by window).

### What the low-absorb genomes are (post hoc)

Not part of the registered analysis; added once prediction 1 had
failed on seed 1.

- **One parent each, damaged after its birth.** 95% of the low-absorb
  genomes' exact births (94–96% per seed) come from a parent whose body
  had changed since its own birth (`parent_hash` ≠ `parent_now_hash` in
  `births.csv`), and the median low-absorb genome has one executor.
  The parent was born working, a bit flip hit its preamble while it
  lived, and it went on replicating on register values set before the
  hit, making exact copies of a body its children cannot run. Example
  (seed 1, `3431fdfcd0e52695`): `lit D -4` became `store D ; divide D`.
  The parent's D was already −4; a newborn's is 0, so `jmpr D` does not
  loop and each pass absorbs once, copies one byte and gives away a
  24-unit endowment. Alone in the trace harness the body is dead at
  tick 4.
- **They are short-lived, not consumers.** Pooled over seeds 1–9,
  carriers of low-absorb genomes execute about 39 instructions, absorb
  6.5 times and get 35 units from `absorb` against 69 from their
  endowment; 6.6% of them have any child (27% for the rest). By
  harness class the weight is 56% `inexact`, 35% `dies`, 5% one-shot,
  3% replicator, and parasites hold none of it. Their energy comes from
  their parent's endowment, once; nothing about them persists over
  generations.
- **Restricting scope removes them.** Requiring ≥ 2 exact births from
  parents with undamaged bodies, the low-absorb share falls to
  0.10–0.14% by window (under 1% in every window in 9 of 9 seeds), which
  prediction 1 would have passed.
- **Somatic copying is common.** 16.5–17.2% of all exact births in E007
  are copies of a parent's body as changed after birth (13% for the
  high-absorb genomes too), so bit rot in living bodies is a large
  share of the mutation supply and not only damage.

### Scoring H2

By the registered rule: **mixed** (low-absorb share 2.37% in the median
window, below the 5% needed for "supported", and 96.6% of that weight
dependent-class, so not "refuted" as prediction 1 was written).

The reading, post hoc: the 2% is the scope rule, not H2's split. The
weight is one-generation bursts, each from one damaged parent, with
children that die within a few ticks; H2 asks for a mode that is
"stable over many generations" and depends on producers, and these
depend on nobody but their own parent. Every persistent genome group
takes 97–99% of its income from `absorb`, and the one interaction the
world has, fall-through parasitism, makes the parasite more of a
producer than its host, not less (0.245 against 0.229 of its
instructions on `absorb`). H2's diagnosis for no split, "parasitism
pays nothing", holds in the energy sense: the physics moves no energy
between organisms, the same conclusion E008–E010 reached from the
cost-rule side. Status: mixed by the rule, leaning refuted.

### Caveats

- E005's world-replicating test (≥ 2 exact births of a raw hash) admits
  single-parent somatic bursts. About a quarter of the dependent
  genomes per run (about 5,200 of 20,900) are such bursts; E005's parasite
  test requires a generation depth of 5 and is unaffected (parasites
  hold none of the low-absorb weight). A lineage test should require
  exact births by at least two executors, or by parents with undamaged
  bodies, from now on.
- Prediction 1 failed on a case its author did not think of; the
  post-hoc restriction that passes it was chosen after seeing the data.
- One world (the standard one), one long run of it.
