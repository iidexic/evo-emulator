# T05. `analysis/measures.py`: the standing measures for every experiment

Status: specified 2026-10-13. Not built. Argument: synthesis finding
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

## 5. Tests (`analysis/tests/test_measures.py`, pytest via uv)

Hand-built tiny runs: a three-generation forest where every number
(MPD, SPD, ED, ancestor count, MRCA, the three MODES columns at Δ =
1 and 2, QNN over two censuses) is computed by hand in the test;
the two SPD methods agree on a random tree of 500 tips.

## 6. Report back

The baseline summary table and the three shakedown checks; the
runtime per 250,000-tick run (target: under 2 minutes without
`--knockout`); any column that could not be computed and why.
