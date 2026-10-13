# T05. `analysis/measures.py`: the standing measures for every experiment

Status: specified 2026-10-13; built the same day by Codex (commit
`0d0c36b`, its first evo task), reviewed by Opus against independent
recomputation (QNN at 501 censuses, SPD/MPD/ED/MRCA at 8 ticks, MODES
at 501 censuses on E007 seed 1: every value matched) and accepted by
Fable with fixes. Shakedown: criterion 1's nominal pass was a
founder-phase artefact and criterion 2's failure was a correct
result, so §4's criteria are rewritten below (amendment 2026-10-13)
and the README's "shakedown fails" branch is not taken. The §4.1
fixes went to two follow-up builds, both done (the knockout loop and
the class columns in the second; sites on E007 in §3.1); criterion 3
waits for E012/E013 data. Argument: synthesis finding
9 and §3.5, PLAN §8.5, `literature.md` §3.3, §3.4, §7 ("Measures").
Line C; built and run on E007, E012 and E013 before E014 is run, so
the first use of the measures is on known runs. Python only, except
the knockout loop, which uses T03's `--neighbours HEX
--neighbours-pad-only`.

## 1. Interface

```
uv run measures.py RUN_DIR [--every K] [--depths 187,1870] [--knockout] [--out DIR]
```

Reads a run directory (`docs/instrumentation.md`); writes
`RUN_DIR/measures/` (or `--out`): `series.csv` (one row per census
tick), `summary.json` (whole-run numbers), and, with `--knockout`,
`sites_<window>.csv`. A library entry point `measures.compute(run)
-> (series, summary)` for the experiment runners. `--every K`
computes the phylometrics at every K-th census (default 1).

## 2. Series, per census tick t

### 2.1 QNN over `func_hash` (the headline)

`census.csv` gives `now_hash` counts at t; join `genomes.csv` for
`func_hash` (every raw hash in a census is in `genomes.csv`, somatic
bodies included) and sum counts per `func_hash`. With p_i(t) =
n_i(t) / N(t):

```
q_i(t)  = max(0, p_i(t) − p_i(t_prev))²
QNN(t)  = Σ_i q_i(t)
QNNcum(t) = Σ_{s ≤ t} QNN(s)
```

A component absent at t_prev has p = 0 there (the authors' R code,
`franticspider/qnn`). Columns `qnn`, `qnn_cum`, `n_func` (components
with n > 0), `top_func_share`.

### 2.2 Phylometrics on the individual-level tree

Tree: nodes are organism ids; parent is the `executor` of the
`births.csv` row (the lineage parent, under parasitism too; `source`
is not used); founders and injected copies (no births row) hang from
a virtual root. Generation depth g = parent's g + 1, founders 0.
Tips at t: the living ids in `orgs.csv` at t.

- `mrca_gen`, `mrca_tick`: generation depth and birth tick of the most
  recent common ancestor of all tips (the virtual root when the tips
  descend from different founders; then `mrca_gen` = −1). Summary:
  `mrca_changes`, the number of censuses at which the MRCA id changed
  (Dolson 2020's sweep counter).
- The induced tree: the union of root paths of the tips, with every
  node of exactly one child removed (unifurcations stripped), edge
  length = difference in generation depth of its ends.
- `ancestor_count`: internal nodes of the induced tree.
- `mpd`, `spd`: mean and sum over tip pairs of the path length in
  edges' generations between them (through the lowest common
  ancestor). About 950 tips, 450,000 pairs: compute with depth-sorted
  LCA or the "sum over edges of k × (n − k)" identity for the sum, and
  a pairwise loop in numpy for the mean; both must agree (test).
- `mean_ed`: mean over tips of Isaac et al. 2007's fair-proportion
  evolutionary distinctiveness, Σ over edges on the tip's root path of
  edge_length / (tips below that edge).

### 2.3 MODES change, novelty, ecology at two filter depths

Components are `func_hash` of birth genomes. An organism born at
generation g is *persistent at depth Δ* if some descendant (by the
tree above) has generation depth ≥ g + Δ. F_Δ(t) is the set of
components of organisms alive at t that are persistent at depth Δ.
Then, with t_prev the previous census and S_Δ(t) the union of F_Δ(s)
over s < t:

```
change_Δ(t)  = |F_Δ(t) \ F_Δ(t_prev)|
novelty_Δ(t) = |F_Δ(t) \ S_Δ(t)|
ecology_Δ(t) = −Σ_{c ∈ F_Δ(t)} p(c) log₂ p(c),  p(c) over living bodies in F_Δ(t)
```

Depths default to N/5 and 2N generations with N = 935 (PLAN §8.5;
`--depths` overrides). Censoring: persistence cannot be known near
the end of the run. `modes_censored` = true from the first census at
which the deepest generation reached anywhere in the run is below
(max generation among organisms alive at that census) + Δ. The
summary gives each MODES column's mean over the uncensored stationary
phase (t ≥ 25,000). No complexity column: MODES complexity needs the
knockout loop, reported separately (§3) and never as a headline.

### 2.4 Also per census

`pop`, `rep_alive` (replicator-class by birth hash, from
`classes.csv` if present), `len_med`, and the parasite and entered
shares if the run has them (E005's and T02's definitions, through the
existing scripts; empty columns otherwise).

## 3. Sites: entropy against knockout (`--knockout`)

Per 25,000-tick window: the top replicator-class `func_hash` by exact
births; its canonical body (`traits.canonical_instrs`); over the
window's replicator-class exact births of bodies of the same length,
the Shannon entropy of the canonical byte at each position
(`entropy`). Then `evo-core --neighbours HEX --neighbours-pad-only`
on the top body: `exact_alone` per position with `pad` in that
position, against the unmutated body's; `meaningful` = exact births
below half of the unmutated body's or the class changed. Output
`sites_<window>.csv`: `pos, op, entropy, exact_pad, class_pad,
meaningful`. The record reads whether low-entropy sites are the
meaningful ones (Willkens 2023's warning: single knockouts mishandle
interacting sites, so this is a diagnostic).

### 3.1 Sites, E007 seeds 1, 3, 5 (2026-10-13)

`measures.py --knockout` with the t03 binary (pre-T08 physics, no
flags, 3,000 harness ticks) on `runs/lod/e007/s1`, `s3`, `s5`: ten
windows each, 21 sites per window, entropy over 112,000–158,000
same-length exact births per window; the top bodies make 142–176
exact births alone. AUC is the chance that a meaningful site has
lower entropy than a non-meaningful one; Spearman is bounded near
−0.37 when one site of 21 is not meaningful, so AUC is the one to
read.

| seed | meaningful of 21, windows 1–10 | not meaningful | AUC | Spearman |
|---:|---|---|---:|---:|
| 1 | 20 in every window | pos 17 | 0.95–1.00 | −0.38 to −0.34 |
| 3 | 19 19 20 20 20 20 20 20 20 20 | pos 17; pos 16 in w1–2 | 0.92–1.00 | −0.51 to −0.34 |
| 5 | 19 19 19 20 20 20 20 19 20 20 | pos 17; pos 16 in w1–3, w8 | 0.95–1.00 | −0.51 to −0.35 |

Low-entropy sites are the meaningful ones: of the 15–19 sites per
window under 0.5 bits all are meaningful except pos 16 in four
windows, and the one site meaningful in no window is pos 17, the
endowment operand (`lit` at 16; 2.3–4.6 bits), where a `pad` leaves
an exact replicator in the harness alone. The converse fails at pos
6, the absorb-count operand: 3.1–4.2 bits yet meaningful in all 30
windows (`pad` sets the count to 0, a loafer), because a knockout
tests one value, not the range a variable operand takes; pos 6 is
what keeps AUC below 1 (with pos 8 in seed 3's windows 1–2).

## 4. Baselines: `analysis/measures_baseline.py`

Runs `measures.compute` over E007 (10 seeds), E012 and E013 (all
arms, all seeds), writes `runs/measures/<exp>_series.csv` and
`runs/measures/summary.md`: per seed `qnn_cum` at 25,000 and at the
end, the window of the maximum `qnn`, `mrca_changes`, the stationary
means of MPD, ED and the MODES columns at both depths.

Shakedown criteria, fixed now (the measures must see what E007
already found):

1. `qnn` has its maximum in the first 10,000 ticks (the absorb-count
   sweep) in ≥ 8 of 10 E007 seeds, and the stationary mean is below a
   fifth of that maximum.
2. `mrca_tick` moves past 10,000 in every seed (the sweep's ancestor
   replaces the founder), and `mrca_changes` is at least 1.
3. E012 (`--no-protect`) and E013 (sixteen founders) against E007:
   no measure differs by more than the between-seed spread of E007 in
   the stationary phase, except E013's `mrca_gen` and
   `ancestor_count` in the first window (sixteen roots).

If 1 or 2 fail, the implementation is wrong, not the run.

**Amendment 2026-10-13, after the shakedown on E007.** The build is
numerically right where it was recomputed independently; the two
criteria were wrong for this world, as follows.

Criterion 1 as written passed in 9 of 10 seeds but mostly on the
founder phase: `qnn` peaks at ticks 500–1,500 while the population
grows from 1 to about 900, and in 6 of 9 seeds under 40% of the peak
comes from components with absorb count ≥ 96 (s1 6%, s2 15%, s4 4%,
s6 37%, s8 3%, s9 53%; s3, s5, s7 93–98%). The sweep itself is
invisible to QNN over `func_hash`: in seed 1 the share of bodies with
absorb ≥ 96 rises from 0.06 at tick 1,000 to 0.78 at 10,000 and 0.92
at 18,000, and `qnn` over that span is 0.0010–0.0022 against a
stationary mean of 0.00116, because the sweep is spread over many
`func_hash`es (the largest holds 0.03–0.05). A trait sweeping across
many genotypes is below a genotype-grouped turnover measure by
construction. This matters for E016: a defence spreading on many
backgrounds will not show in QNN over `func_hash` either.

Criterion 2 failed in 7 of 10 seeds and the result is correct: in
seed 1 the 902 final tips split 682 via id 10 (born tick 54) and 220
via id 7 (born tick 41), both children of id 3 (generation 1, tick
14), which is the MRCA; absorb ≥ 96 arose separately in each line
(ticks 918 and 4,976) and the lines never merged. The run reaches
generation 1,012, short of the roughly 2N ≈ 1,870 generations
expected before coalescence. The criterion also contradicted
criterion 1: a sweep finished by tick 10,000 has its ancestor born
before 10,000.

Criteria, as they now stand:

1. **The sweep is seen at the trait level.** `measures.py` gains
   `--group COL` (default `func_hash`; `absorb_class` groups bodies
   by `traits.py`'s absorb count read from the body, `< 96` against
   `≥ 96`, with a third class for bodies the pattern does not match).
   With `--group absorb_class`, `qnn` after tick 2,500 (the founder
   phase excluded) has its maximum inside the window in which the
   ≥ 96 share crosses from 0.25 to 0.75 in ≥ 8 of 10 E007 seeds, and
   the stationary mean is below a fifth of that maximum. The
   `func_hash` series is kept as the headline for genotype turnover
   and is reported beside it; its blindness to trait sweeps is stated
   in every record that uses it.
2. **Coexisting lines from the founder.** `mrca_tick` stays below
   1,000 in ≥ 8 of 10 seeds and the final tips descend from ≥ 2
   distinct generation-1 or generation-2 ancestors in every such
   seed (a new column `root_lines`, the number of children of the
   MRCA with living descendants). `mrca_changes` is reported with no
   threshold, and injections (`--inject`) are excluded from it.
3. Unchanged, pending the E012/E013 data (not on the desktop).

Filter depths: Δ1870 applies only when the run's deepest generation
is ≥ 1,870; otherwise the column is `censored` and the summary says
so (E007 at 250,000 ticks reaches 1,012).

**Outcome of the amended criteria, 2026-10-13** (follow-up build
`d198fa3`…`6cad7ca`, `runs/measures/summary.md`). Criterion 1 as
amended passes in 5 of 10 seeds (1, 2, 6, 8, 9). The failures are
features of the data: seeds 4 and 5 have their global `qnn` maximum
in a single late census (ticks 215,500 and 216,000) from a jump of
about 0.03 in the `unmatched` class, which holds 20–37% of bodies
(one-off damaged variants); their in-window peaks are 0.0030 at
3,500 and 0.00086 at 3,000. Seed 3's ≥ 96 share never reaches 0.75
(maximum 0.716), so its window never closes. Seed 7 peaks two
censuses after its window closes. Criterion 2 as amended cannot be
met: seeds 2, 7 and 9 coalesce late (`mrca_tick` 110,057, 77,422 and
101,820; generations 419, 347 and 400), so `mrca_tick` < 1,000 holds
in 6 of 9 living seeds, and only seeds 1, 6 and 8 have the MRCA at
generation 0–1 (seeds 3, 4, 5 at 2, 3, 20). `root_lines` is 2 in
every living seed.

Reading, and the criteria's final form. The measures are verified
(independent recomputation; 15 tests). What the shakedown shows is
that QNN under any grouping is a weak detector of this world's sweep:
the sweep's own trace is the trait-share series (`traits.py`'s
absorb count, the ≥ 96 share crossing 0.25 to 0.75 between ticks
500–2,000 and 3,500–12,500), and `qnn` over `absorb_class` marks it
in half the seeds, with late single-census spikes from the
`unmatched` class elsewhere. So criterion 1 is closed as "5 of 10,
explained", not re-tuned, and the rule carried into E016 is: a
defence's spread is read on its own trait share (pattern-located
presence of the defence bytes) first, `qnn` over the defence class
second, `qnn` over `func_hash` as genotype-turnover context only.
Criterion 2 is closed as a report with no threshold: coalescence
time is a feature of the run (2N ≈ 1,870 generations not reached;
three seeds coalesced anyway at generations 347–419), `root_lines`
= 2 is the common state. Criterion 3 waits for E012/E013 data (not
on the desktop).

Closed from §4.1 in the second follow-up (2026-10-13, `90a9887`,
`747b7e4`). `--knockout` runs the `--neighbours HEX
--neighbours-pad-only` loop and fills `exact_pad`, `class_pad` and
`meaningful`; the unmutated body's exact births alone come from
`--classify` on that one body, at the same harness ticks and physics,
since the neighbours CSV has no unmutated row (`--evo-bin`,
`--harness-ticks`, `--evo-flags`; results in §3.1). The class columns
are filled on the E007 reruns: `classes.csv` is present in
`runs/lod/e007/s1`–`s9`, and `classes_world.csv` is a copy of it, as
`e007_long_run.py` makes it, since the harness physics is the world's
(4,002 sampled genomes reclassified with the t03 binary matched in
class and exact births). The baseline rerun (seeds 1–9 from
`runs/lod/e007`, seed 10 from `runs/e007/std/s10`, extinct at tick
1,179) leaves the shakedown table unchanged; `summary.md` gains
stationary means `rep alive` 443–458 of about 931 bodies (48–49%) and
`parasite` 1.9 × 10⁻⁵–2.3 × 10⁻⁴. `entered_share` stays empty on E007:
its `orgs.csv` (binary `bf865e7`) predates the `exec_by_others`
column, so it is readable only on runs recorded since E014.

### 4.1 Fixes from the review, for the follow-up build

- `--every K` crashes when the last census is not sampled
  (`measures.py:366`, `measures_baseline.py:53`: `int(None)`); take
  the last non-null value.
- `--knockout` exits with code 2 and writes no `series.csv` or
  `summary.json`; the sites files are added on top of the normal
  output, not instead of it.
- Tests: the 500-tip test compares `spd_edge` with `spd_pairwise`
  but `compute()` uses neither; test the SPD `_tree_metrics` emits
  against a pairwise loop. Add a single-founder case whose MRCA is a
  real organism with `mrca_changes` > 0 and living ancestors among
  the tips, and cover `--every`, the CLI's `summary.json`, `.gz`
  input, `measures_baseline`, and the new `--group` and
  `root_lines`.
- Readings to fix in code and state in the module doc: `mean_ed`
  includes the stem from the MRCA to the virtual root (+0.447 of
  6.20 at seed 2's end), which is to be dropped so ED does not grow
  with MRCA depth; `ancestor_count` leaves out living organisms with
  living descendants (383 against 480 at seed 1's end), to be
  counted; `ecology` takes p(c) over persistent bodies only, which
  is Dolson's definition and stays, said in the doc;
  `modes_censored` is to be held true once set.
- `parasite_share` re-implements E005's test without its
  `world_class` condition (`e005_parasites.py:197`); call or match
  it. `entered_share` is to be over replicator-class bodies, as T02
  §4.3 names it.
- Delete the stale `runs/measures/e007_std_s*_series.csv` from the
  earlier runner version; rerun the baseline on E007 and update
  `runs/measures/summary.md`. The pytest command that works is
  `uv run --project analysis --with pytest pytest analysis/tests/test_measures.py`
  from the repo root; put it in `analysis/README.md`.

## 5. Tests (`analysis/tests/test_measures.py`, pytest via uv)

Hand-built tiny runs: a three-generation forest where every number
(MPD, SPD, ED, ancestor count, MRCA, the three MODES columns at Δ =
1 and 2, QNN over two censuses) is computed by hand in the test;
the two SPD methods agree on a random tree of 500 tips.

## 6. Report back

The baseline summary table and the three shakedown checks; the
runtime per 250,000-tick run (target: under 2 minutes without
`--knockout`); any column that could not be computed and why.
