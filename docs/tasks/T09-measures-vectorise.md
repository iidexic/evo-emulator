# T09. `measures.py`: the per-id and per-census loops in numpy

Status: specified 2026-10-14 (Fable, from a profile of E016's `analyse`
stage); not built. Builder: Opus. Argument: E016's `analyse` stage spends
about 70% of its time per run in T05's `measures.compute`, and that time is
in Python loops over organism ids and over the tips of each census, not in
polars or numpy. The numbers are correct (T05's review and tests) and
nothing in the output changes; this task makes the same numbers in a
fraction of the time. Depends on T05 (built). Nothing depends on it; it
is for the next 150-run analysis (E016's reruns, E017), not for E016's
first pass, which has run.

## 1. The profile

`analysis/measures.py` `_series`, cProfile, E016 `runs/e016/std_t50/s21`
(births 4,137,158 rows; orgs 1,035,518 rows over 501 censuses; max
generation 1,059; 12 binary-lifting levels). Wall time without the
profiler is 20.3 s for `_series`, 26–27 s for the whole `analyse_run`;
a tierra run (2 M births) is 13.7 s and 16–17 s.

| function | own s | cumulative s | calls | what loops |
|---|---|---|---|---|
| `_tree_metrics` | 6.4 | 16.2 | 501 | per census: an LCA chain over all tips, the virtual-tree stack, a dict per node, `searchsorted` per node |
| `_lca` | 4.2 | 4.2 | 2,070,034 | Python binary lifting, one pair at a time |
| `searchsorted` | 1.8 | 3.5 | 2,899,186 | one call per virtual-tree node |
| `_euler` | 5.8 | 6.4 | 1 | Python DFS over every id |
| `_tree` | 1.9 | 2.6 | 1 | `iter_rows` over every birth and every orgs row |
| `_persistence` | 1.1 | 1.6 | 1 | `iter_rows` over every birth, reverse |
| `_series` body | 1.5 | 31.2 | 1 | per census: `zip(tips, hashes)` loop, `sum(classes.get(h) == ...)`, dict counts per depth |

Everything else in E016's `analyse_run` (`analysis/e016_defence.py`) and
in E015's `parasite_genomes` is polars or numpy already, except E015's
`parasite_genomes` generation-depth loop (`iter_rows` over candidate exact
births; 0.5 s here) and `edge_signature`'s per-pair loop (not on E016's
path). Those two are §5, optional.

## 2. The rule

Output identical. `series.csv` and `summary.json` from `compute(run)` on
the three reference runs of §4 are equal to the current build's column
for column: integer and boolean columns bitwise, float columns within a
relative 1e-9 (the sums are reordered, nothing else), nulls in the same
rows. `qnn_series` is untouched (already polars). The public names stay:
`compute`, `qnn_series`, `_tree`, `_euler`, `_persistence`, `_injected`,
`_tree_metrics`, `_lca`, `spd_edge`, `spd_pairwise` (the tests import
the private ones; `measures_baseline.py`, `e015_template.py` and
`e016_defence.py` import `compute`, `qnn_series`, `last_value`,
`STATIONARY`; grep before renaming anything). `_lca` on two ints may stay as it is for callers that need
one pair; the per-census path must not call it per tip.

Facts the vectorisation may rely on (from `sim.rs` and `_tree`'s own
comment): ids are issued in sequence, so every executor id is smaller
than its child's id; id 0 is the virtual root and `parent[0] == 0`;
`depth[0] == 0` and the code treats the root's depth as −1 where it
measures edge lengths; a run may have several founders and injected
copies (several ids with `parent == 0`), and `_injected` must keep
working (it is already numpy).

## 3. The pieces

Any correct numpy formulation is acceptable; these are the known ones.

1. **`_tree`.** `parent[child] = executor`, `born[child] = tick` are
   fancy-index assignments from the birth columns as numpy arrays; the
   orgs fill is a boolean mask (`ident > 0 & parent[ident] == 0`). Depth:
   build the lifting table `up` from `parent` first (as now), then
   `depth` by pointer jumping over all ids at once (for level j from
   high to low, nodes whose `up[j]` is not the root jump and add 2^j),
   or by a level loop over generations (at most max generation
   iterations, about 1,100, each a numpy op on that level's ids).
   Either is O(n log n) or O(n) numpy.
2. **`_euler`.** `tin`/`tout` from subtree sizes: size by a reverse pass
   over depth levels (`np.add.at(size, parent[level_ids], size[level_ids])`
   from the deepest level up), then `tin[child] = tin[parent] + 1 +
   (sum of sizes of earlier siblings)`, with siblings ordered by id
   (sort ids by `(parent, id)`, cumulative size within each parent
   group), filled level by level from the root down; `tout = tin +
   size`. The current DFS visits children in id order, so this gives
   the same `tin`; equality is checked by the tests, not assumed.
3. **`_persistence`.** `max_desc` by a reverse pass over depth levels
   with `np.maximum.at(max_desc, parent[level_ids], max_desc[level_ids])`.
4. **`_tree_metrics`.** With tips sorted by `tin`: the MRCA is the LCA
   of the first and the last tip (one pair); the consecutive-pair LCAs
   come from a vectorised binary lifting over all pairs at once (the
   same two phases as `_lca`, on arrays, log n steps); the virtual
   tree's nodes are tips ∪ pair LCAs ∪ root, sorted by `tin`
   (`np.unique` on `tin`, then the ids); the virtual parent of each
   node after the first is the LCA of it and its predecessor in that
   order (the standard construction; the stack version now in the code
   gives the same tree). Descendant-tip counts per node are two
   `searchsorted` calls on arrays (`tin[nodes]` and `tout[nodes]`
   against the sorted tip `tin`s), which is also what gives `lo`/`hi`
   for ED. Then `spd = Σ length · k · (n − k)` over nodes with a
   parent, `children[x] >= 2` from `np.unique(vparent,
   return_counts=True)`, `root_lines` the MRCA's count in that, and
   `ordered_eds` by a difference array (add `length / k` at `lo`,
   subtract at `hi`, cumulative sum) instead of the slice adds. Edge
   lengths use the root's depth as −1 exactly as now.
5. **`_series` body.** Before the census loop: one polars join gives
   every orgs row its `func_hash` (or the `group` column) and its class,
   and numpy arrays per id (`comp_code` as an integer code per
   `group` value, with −1 for a hash not in genomes.csv; `is_rep`).
   Per census, with `tips` an int array: `rep_alive` is
   `is_rep[tips].sum()`; the persistent set for depth d is
   `comp_code[tips][max_desc[tips] >= gen[tips] + d]` with the −1 code
   dropped; `change`, `novelty`, `ecology` from `np.unique(...,
   return_counts=True)` and set differences on the code arrays
   (`np.setdiff1d`, or keep `seen`/`previous` as boolean arrays over
   the code range and index them). `top_gen` is `gen[tips].max()`. The
   `qnn` dict lookup per tick, `len_med`, `foreign_share`,
   `parasite_share` and `entered_share` already run on the per-tick
   frame and stay. `org.partition_by("tick", as_dict=True)` may stay
   (it is one polars call) or become one sort plus index slices; it is
   not the time.

Not in scope: `qnn_series`, `site_entropy`, `site_windows` (not on
E016's path; T05 §3.1 territory), the knockout loop, `lod.py`.

## 4. Tests

1. **Reference copy.** Before changing anything, copy the current
   `_tree`, `_euler`, `_persistence`, `_tree_metrics` and `_lca` into
   `analysis/tests/measures_ref.py` (unchanged, with a one-line header
   saying they are T05's build at commit `224fc7e` kept as the
   reference). The existing random tests
   (`test_spd_methods_agree_on_random_500_tip_tree`,
   `test_tree_metrics_match_a_pairwise_loop_on_a_random_500_tip_tree`)
   stay as they are and must pass on the new code.
2. **`test_tree_arrays_match_reference_on_random_forests`**: random
   forests with 2–4 founders (`parent == 0`), 20,000–50,000 ids, a
   few hundred ids with no births row (the `_injected` shape), generated
   as a `Run`-like object with `births` and `orgs` frames; `parent`,
   `depth`, `born`, every `up` level, `tin`, `tout` and `max_desc`
   equal to the reference's, `np.array_equal`. Ten seeds.
3. **`test_tree_metrics_match_reference_on_random_tip_sets`**: on the
   same forests, 50 random tip sets of 1–3,000 tips, every key of the
   returned dict equal (floats within 1e-9), including the cases n = 0
   and n = 1 and a tip set that is a single lineage (chain) and one
   where every tip is a founder.
4. **Reference runs** (not pytest; the report): `compute(run)` on
   `runs/e007/std/s1` (T05's own baseline run; any whole E007 seed
   does), `runs/e016/std_t50/s21` and
   `runs/e016/tierra_n0/s1`, before and after, compared by §2's rule
   over every column of `series.csv` and every key of `summary.json`.
   Time each, before and after. The E016 runs have `classes.csv.gz` and
   `defence.csv`; the comparison is on `compute(run,
   group="func_hash")` as T05 calls it, and on E016's call
   (`group="defence_class"` after `analyse_run`'s genomes join; the
   simplest way is to run `analysis/e016_defence.py analyse --force
   --arms std_t50 --seeds 21` and compare the run's `measures/` and
   `analyse.json` against copies taken before).
5. Existing tests: `uv run --project analysis pytest analysis/tests`
   whole (T05's 20, E016's, lod's). Any test that fails is checked by
   hand: if it pinned an intermediate that the new code no longer
   produces (a dict, a list), update it and say so; if a number
   changes, stop and report.

## 5. Optional, same rules

E015's `parasite_genomes` depth loop (`analysis/e015_template.py`): the
chain depth per genome is a tree depth on a parent array restricted to
same-hash exact-birth links (`parent'[child] = executor` when the
executor is itself an exact birth of the same `raw_hash`, else 0),
computed by the same lifting as §3.1. Only if §3 is done and the three
reference runs match; E016's `analyse_run` and E015's runner both call
it, so the §4.4 comparison covers it.

## 6. Docs

- `docs/tasks/README.md`: the T09 row (status, time before and after on
  the std run).
- T05 record `docs/tasks/T05-measures.md`: one sentence at the status
  paragraph, "loops vectorised in T09 (commit), numbers unchanged".
- `analysis/README.md`: nothing unless the usage line changes.

## 7. Files

`analysis/measures.py` (`_tree`, `_euler`, `_persistence`,
`_tree_metrics`, `_series`; `_lca` may stay), `analysis/tests/measures_ref.py`
(new), `analysis/tests/test_measures.py` (tests 2–3), optionally
`analysis/e015_template.py`, the docs above.

## 8. Report back

The before/after times of `_series` and of `analyse_run` on the three
reference runs; the §4.4 comparison (columns compared, max relative
float difference, which columns were bitwise equal); `pytest` totals;
anything from §4.5. Commit per item (reference copy and tests first,
then the vectorised functions, then docs), subjects `T09: …` / `docs:
…`, each ending `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
Do not push.
