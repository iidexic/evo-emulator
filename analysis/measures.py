"""Standing evolutionary measures for recorded evo runs (T05,
docs/tasks/T05-measures.md).

    uv run measures.py RUN_DIR [--every K] [--depths 187,1870] [--group COL] [--out DIR]
                       [--knockout [--evo-bin PATH] [--harness-ticks 3000] [--evo-flags "..."]]

from analysis/, or `compute(run)` from experiment runners. Writes
`RUN_DIR/measures/series.csv` (one row per census), `summary.json`, and
with `--knockout` also `sites_<window>.csv`.

Definitions, as computed (spec §2, with the §4 amendment and §4.1):

- QNN (`qnn`, `qnn_cum`, `n_func`, `top_func_share`): census bodies by
  `now_hash`, joined to genomes.csv for their component; q_i = max(0,
  p_i(t) - p_i(t_prev))^2 summed over components; the first census is 0.
  Components are `--group COL`: `func_hash` by default (the headline for
  genotype turnover; blind to a trait that sweeps across many genotypes,
  spec §4 amendment), any other genomes.csv column, or `absorb_class`:
  traits.py's absorb-count read of the body bytes (`traits.ABSORB`, byte 6
  guarded by a `lit` at byte 5, on 21-byte bodies) as `lt96` / `ge96`, and
  `unmatched` for a body the read does not match; with it the series also
  has `absorb_ge96_share` (among matched bodies) and
  `absorb_unmatched_share`. `n_func` and `top_func_share` count groups.
- Tree: an organism's parent is the `executor` of its births row;
  founders and injected copies hang from a virtual root at generation -1.
  Tips are the living ids at the census. The induced tree is the union of
  the tips' root paths with non-tip unifurcations stripped; edge length is
  the difference in generation.
- `mrca_gen`, `mrca_tick`: the MRCA of all tips (the virtual root, -1 and
  0, when they descend from different roots).
- `root_lines`: children of that MRCA with living descendants (a child
  alive itself counts); founders with living descendants when the MRCA is
  the virtual root; 0 for a single tip.
- `mrca_changed`, summary `mrca_changes`: the sweep counter. It follows the
  MRCA of the tips that descend from founders: tips from `--inject` copies
  (ids after the founders with no births row, read when meta.json lists
  `injections`) are left out, so an injection's arrival and loss are not
  counted. With `--every K`, consecutive sampled censuses are compared.
- `ancestor_count`: internal nodes of the induced tree, i.e. its branch
  points, living or dead: a living organism counts when its living
  descendants run through two or more of its children (one line of living
  descendants makes it a unifurcation, stripped like any other). The
  virtual root counts when it is a branch point. (E007 seed 1's last
  census: 383 dead branch points + 97 living = 480; 112 more living
  organisms have one line of living descendants.)
- `spd`, `mpd`: sum and mean over tip pairs of the generations between
  them through their LCA (edge identity sum of length x k x (n - k)).
- `mean_ed`: mean over tips of Isaac et al. 2007's fair proportion, summed
  over the edges of the tip's path below the MRCA: the stem from the MRCA
  to the virtual root is dropped, so ED does not grow with MRCA depth. A
  tip that is itself the MRCA has ED 0.
- MODES at each depth D (`change_D`, `novelty_D`, `ecology_D`): components
  are `func_hash` of birth genomes; an organism of generation g is
  persistent at D if a descendant reaches g + D. `ecology_D` takes p(c)
  over persistent bodies only (Dolson's definition). `modes_censored_D` is
  set from the first census at which the run's deepest generation is below
  (deepest living generation) + D and held true from then on;
  `modes_censored` is the deepest D's flag. A depth D above the run's
  deepest generation does not apply: its three columns are empty at every
  census, and summary.json gives "censored" for their means and the reason
  under `censored_depths`.
- `rep_alive`: living bodies whose birth hash is replicator-class
  (classes.csv). `entered_share`: among those, the share with
  `exec_by_others` > 0 (T02 §4.3); empty without classes.csv.
- `parasite_share`: living bodies whose birth hash passes E005's
  registered parasite-lineage test (`_parasite_genomes`), world-class
  condition included; empty without classes.csv and classes_world.csv.
  `foreign_share`: sum of `exec_foreign` over sum of `executed`, living.
- Summary means (`mean_mpd`, `mean_mean_ed`, `mean_rep_alive`,
  `mean_parasite_share`, `mean_entered_share`, `mean_<modes>_D`) are over
  censuses at or after tick 25,000 (MODES: uncensored ones only); a class
  column's mean is null when the run lacks the classes files. For E007-like
  runs, whose harness physics is the world's, classes_world.csv is a copy
  of classes.csv (as `e007_long_run.py` makes it).

Sites (`--knockout`, spec §3), per 25,000-tick window `w` (ticks
25,000(w-1)+1 .. 25,000w), `sites_<w>.csv` with `pos, op, entropy,
exact_pad, class_pad, meaningful`:

- The top component is the replicator-class (classes.csv) `func_hash` with
  the most exact births in the window; the body knocked out is its most
  common raw body among them. `pos` is a byte position (the canonical body
  of `traits.canonical_instrs` has the raw body's length), `op` the
  canonical op number there or `operand` for a `lit`'s operand byte.
- `entropy`: Shannon entropy (bits) of the canonical byte at `pos` over the
  window's replicator-class exact births of bodies of the same length.
- `exact_pad`, `class_pad`: `exact_alone` and `class_alone` of the mutant
  with `pad` (byte 0) at `pos`, from `evo-core --neighbours HEX
  --neighbours-pad-only` (T03 §2; a position already `pad` gives the body
  itself). The unmutated body's own `exact_alone` and `class_alone` come
  from `evo-core --classify` on a one-row genomes.csv: the same
  `harness::run_alone_with` the neighbours mode runs each mutant alone
  with, at the same `--harness-ticks` and physics flags (the neighbours CSV
  has no unmutated row).
- `meaningful` (`is_meaningful`): `exact_pad` below half the unmutated
  body's exact births alone, or `class_pad` differs from its class alone.
- summary.json gains `sites` (per window: the body, its exact births in the
  window, the number of bodies the entropy is over, the unmutated harness
  result, the meaningful count, mean entropy of meaningful and other sites,
  Spearman's rho of entropy with meaningful and `auc`, the chance that a
  meaningful site has lower entropy than a non-meaningful one;
  `sites_relation`) and `sites_harness`. Single
  knockouts mishandle interacting sites (Willkens 2023): a diagnostic.
- The engine is `--evo-bin PATH`, else $EVO_BIN, else
  evo-core/target/release/evo-core.exe (not built here). `--evo-flags
  "..."` (split on whitespace) is passed to both engine calls so the
  harness physics matches the run's (e.g. `--no-protect` for E012). Runs
  recorded before T08's alloc/copy range edge fix (2026-10-13) are the
  legacy world: with a post-T08 binary give them `--evo-flags
  "--legacy-pending-range"`; a binary built before T08 (the t03 build)
  needs nothing.
"""
from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
import polars as pl

from evo_run import ROOT, Run, load

STATIONARY = 25_000  # the stationary phase starts here (summary means)
FIRST_ID = 2  # evo-core's first organism id (sim.rs FIRST_ID)
# Columns read from classes.csv (and classes_world.csv); empty without them.
CLASS_COLUMNS = ("rep_alive", "parasite_share", "entered_share")


def _jump(nxt: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """Pointer jumping: for every x, the sum of `weight` from x up to (not
    including) the root it reaches by following `nxt`. Roots point at
    themselves; O(n log depth) in numpy."""
    nxt = nxt.astype(np.int64)
    dist = weight.astype(np.int64)
    for _ in range(64):
        step = nxt[nxt]
        if np.array_equal(step, nxt):
            return dist
        dist += dist[nxt]
        nxt = step
    raise ValueError("the parent array has a cycle")


def _tree(run: Run):
    """Return dense parent/depth/tick arrays and binary-lifting ancestors."""
    b = run.births.select("child", "executor", "tick").sort("child")
    org = run.orgs.select("id", "parent", "birth_tick").unique("id")
    max_id = max(int(b["child"].max()) if b.height else 0,
                 int(org["id"].max()) if org.height else 0)
    parent = np.zeros(max_id + 1, dtype=np.int32)
    born = np.zeros(max_id + 1, dtype=np.int32)
    has_birth = np.zeros(max_id + 1, dtype=bool)
    if b.height:
        child = b["child"].to_numpy()
        parent[child] = b["executor"].to_numpy()
        born[child] = b["tick"].to_numpy()
        has_birth[child] = True
    # Generation: one more than the executor's, 0 without a births row. Ids
    # are issued in sequence (every executor's id is below its child's), so
    # this is the depth of the births alone, before the orgs fill below.
    ids = np.arange(max_id + 1, dtype=np.int32)
    depth = _jump(np.where(has_birth, parent, ids), has_birth).astype(np.int32)
    if org.height:
        ident = org["id"].to_numpy()
        fill = (ident > 0) & (parent[ident] == 0)
        parent[ident[fill]] = org["parent"].to_numpy()[fill]
        born[ident[fill]] = org["birth_tick"].to_numpy()[fill]
    levels = max(1, int(depth.max()).bit_length() + 1)
    up = [parent]
    for _ in range(1, levels):
        up.append(up[-1][up[-1]])
    return parent, depth, born, up


def _lca(a: int, b: int, depth: np.ndarray, up: list[np.ndarray]) -> int:
    if a == 0 or b == 0:
        return 0
    if depth[a] < depth[b]:
        a, b = b, a
    diff = int(depth[a] - depth[b])
    bit = 0
    while diff:
        if diff & 1:
            a = int(up[bit][a])
        diff >>= 1
        bit += 1
    if a == b:
        return a
    for j in range(len(up) - 1, -1, -1):
        if up[j][a] != up[j][b]:
            a, b = int(up[j][a]), int(up[j][b])
    return int(up[0][a])


def _lca_many(a: np.ndarray, b: np.ndarray, depth: np.ndarray, up: list[np.ndarray]) -> np.ndarray:
    """`_lca` over arrays of pairs at once (the same two phases)."""
    a = np.asarray(a, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    zero = (a == 0) | (b == 0)
    swap = depth[a] < depth[b]
    a, b = np.where(swap, b, a), np.where(swap, a, b)
    diff = (depth[a] - depth[b]).astype(np.int64)
    for j, step in enumerate(up):
        hop = ((diff >> j) & 1).astype(bool)
        a[hop] = step[a[hop]]
    for step in reversed(up):
        sa, sb = step[a], step[b]
        move = sa != sb
        a[move], b[move] = sa[move], sb[move]
    out = np.where(a == b, a, up[0][a])
    out[zero] = 0
    return out


def _mrca(ids: np.ndarray, depth: np.ndarray, tin: np.ndarray, up: list[np.ndarray]) -> int:
    """The LCA of a non-empty set of ids: that of its first and last in
    Euler (preorder) order."""
    t = tin[ids]
    return _lca(int(ids[np.argmin(t)]), int(ids[np.argmax(t)]), depth, up)


def spd_edge(tips: list[int] | np.ndarray, parent: np.ndarray,
             depth: np.ndarray) -> int:
    """Sum of tip-pair distances using Σ edge_length × k × (n-k)."""
    tips = list(map(int, tips))
    n = len(tips)
    counts: dict[int, int] = {}
    for tip in tips:
        node = tip
        while node:
            counts[node] = counts.get(node, 0) + 1
            node = int(parent[node])
    total = 0
    for node, k in counts.items():
        p = int(parent[node])
        plen = int(depth[p]) if p else -1
        total += (int(depth[node]) - plen) * k * (n - k)
    return total


def spd_pairwise(tips: list[int] | np.ndarray, depth: np.ndarray,
                 up: list[np.ndarray]) -> int:
    """Reference SPD by explicit tip pairs and LCA; useful for validation."""
    tips = list(map(int, tips))
    gd = lambda x: int(depth[x]) if x else -1
    return sum(gd(a) + gd(b) - 2 * gd(_lca(a, b, depth, up))
               for i, a in enumerate(tips) for b in tips[i + 1:])


def _tree_metrics(tips: np.ndarray, depth: np.ndarray, born: np.ndarray,
                  tin: np.ndarray, tout: np.ndarray, up: list[np.ndarray]) -> dict:
    tips = np.unique(tips.astype(np.int32, copy=False))
    n = len(tips)
    if not n:
        return dict(mrca_id=0, mrca_gen=-1, mrca_tick=0, root_lines=0,
                    ancestor_count=0, mpd=None, spd=None, mean_ed=None)
    if n == 1:
        mrca = int(tips[0])
        return dict(mrca_id=mrca, mrca_gen=int(depth[mrca]) if mrca else -1,
                    mrca_tick=int(born[mrca]) if mrca else 0, root_lines=0,
                    ancestor_count=0, mpd=0.0, spd=0, mean_ed=0.0)

    by_tin = np.argsort(tin[tips], kind="stable")
    ordered = tips[by_tin]
    mrca = _lca(int(ordered[0]), int(ordered[-1]), depth, up)
    # The virtual (induced) tree: tips, the LCAs of tips adjacent in Euler
    # order, and the root, in Euler order; the parent of each node after the
    # first is its LCA with the node before it.
    nodes = np.unique(np.concatenate([ordered, _lca_many(ordered[:-1], ordered[1:], depth, up), [0]]))
    nodes = nodes[np.argsort(tin[nodes], kind="stable")]
    node_tin = tin[nodes]
    vparent = _lca_many(nodes[:-1], nodes[1:], depth, up)
    par = np.searchsorted(node_tin, tin[vparent])  # position in `nodes` of each node's parent
    children = np.bincount(par, minlength=nodes.size)
    # Descendant tips of each node: the tips in its Euler interval.
    ordered_tip_tin = tin[ordered]
    lo = np.searchsorted(ordered_tip_tin, node_tin, side="left")
    hi = np.searchsorted(ordered_tip_tin, tout[nodes], side="left")
    k = (hi - lo)[1:]
    # Generations, the virtual root at -1; the edge from each node after the
    # first to its parent.
    gen = np.where(nodes != 0, depth[nodes], -1).astype(np.int64)
    length = gen[1:] - gen[par]
    spd = int((length * k * (n - k)).sum())
    # Internal nodes of the induced tree: its branch points, tips included
    # (a living organism whose living descendants run through two or more of
    # its children). A tip with one line of living descendants is a
    # unifurcation, stripped as any other.
    ancestors = int((children >= 2).sum())
    # Fair proportion over the original root paths, below the MRCA only (the
    # stem from the MRCA to the virtual root is shared by every tip and would
    # make ED grow with MRCA depth). On the virtual tree each edge represents
    # a chain with constant descendant-tip count, so their combined
    # fair-proportion length is length / k, attributed to the descendant
    # tips (Euler positions lo..hi) by a difference array.
    mrca_pos = int(np.searchsorted(node_tin, tin[mrca]))
    below = np.arange(1, nodes.size) != mrca_pos
    share = length[below] / k[below]
    delta = np.zeros(n + 1, dtype=np.float64)
    np.add.at(delta, lo[1:][below], share)
    np.add.at(delta, hi[1:][below], -share)
    eds = np.empty(n, dtype=np.float64)
    eds[by_tin] = np.cumsum(delta[:-1])
    pairs = n * (n - 1) // 2
    # Children of the MRCA with living descendants: on the virtual tree each
    # child of the MRCA stands for one original child's line.
    return dict(mrca_id=mrca, mrca_gen=int(depth[mrca]) if mrca else -1,
                mrca_tick=int(born[mrca]) if mrca else 0, root_lines=int(children[mrca_pos]),
                ancestor_count=ancestors, spd=spd, mpd=float(spd / pairs),
                mean_ed=float(eds.mean()))


def _levels(parent: np.ndarray, depth: np.ndarray) -> np.ndarray:
    """Each id's distance below the root 0 along `parent`: `depth` + 1 when
    `depth` is the tree's own (founders at 0), else by pointer jumping."""
    lvl = depth.astype(np.int64) + 1
    lvl[0] = 0
    if np.array_equal(lvl[1:], lvl[parent[1:]] + 1):
        return lvl
    weight = np.ones(len(parent), dtype=np.int64)
    weight[0] = 0
    nxt = parent.copy()
    nxt[0] = 0
    return _jump(nxt, weight)


def _euler(parent: np.ndarray, depth: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Euler entry/exit intervals for ancestry checks in the virtual tree:
    the preorder of a depth-first walk from the root 0 that visits children
    in id order, `tout` = `tin` + subtree size."""
    size = len(parent)
    lvl = _levels(parent, depth)
    top = int(lvl.max())
    # Ids by level (radix sort on a narrow key), level l at bounds[l]..bounds[l + 1].
    key = lvl.astype(np.int16) if top < 2 ** 15 else lvl
    by_level = np.argsort(key, kind="stable")
    bounds = np.searchsorted(lvl[by_level], np.arange(top + 2))
    sub = np.ones(size, dtype=np.int64)
    for lv in range(top, 0, -1):
        at = by_level[bounds[lv]:bounds[lv + 1]]
        np.add.at(sub, parent[at], sub[at])
    # Offset of each child within its parent's interval: the sizes of its
    # earlier siblings (lower ids).
    kids = np.argsort(parent[1:], kind="stable") + 1
    s = sub[kids]
    before = np.cumsum(s) - s
    first = np.flatnonzero(np.r_[True, parent[kids[1:]] != parent[kids[:-1]]]) if kids.size else kids
    offset = np.zeros(size, dtype=np.int64)
    offset[kids] = before - np.repeat(before[first], np.diff(np.r_[first, kids.size]))
    tin = np.zeros(size, dtype=np.int64)
    for lv in range(1, top + 1):
        at = by_level[bounds[lv]:bounds[lv + 1]]
        tin[at] = tin[parent[at]] + 1 + offset[at]
    return tin.astype(np.int32), (tin + sub).astype(np.int32)


def _persistence(run: Run, depth: np.ndarray) -> np.ndarray:
    """Maximum descendant generation for each organism id."""
    max_desc = depth.copy()
    if not run.births.height:
        return max_desc
    child = run.births["child"].to_numpy()
    executor = run.births["executor"].to_numpy()
    # Bottom up by the child's generation: every executor is one generation
    # above its child, so a child's maximum is final before it is passed up.
    lvl = depth[child]
    order = np.argsort(lvl, kind="stable")
    bounds = np.searchsorted(lvl[order], np.arange(int(lvl.max()) + 2))
    for lv in range(len(bounds) - 2, 0, -1):
        at = order[bounds[lv]:bounds[lv + 1]]
        np.maximum.at(max_desc, executor[at], max_desc[child[at]])
    return max_desc


def _injected(run: Run, parent: np.ndarray, depth: np.ndarray, up: list[np.ndarray]) -> np.ndarray:
    """Boolean per id: the organism descends from an `--inject` copy.

    Ids are issued in sequence from FIRST_ID (`sim.rs`): the founders first
    (meta.json `founders`, one copy without the key), then one id per birth
    or injected copy. An injected copy is an id after the founders with no
    births row; read only when meta.json lists `injections`."""
    size = len(parent)
    out = np.zeros(size, dtype=bool)
    if not run.meta.get("injections"):
        return out
    founders = sum(int(f.get("count", 1)) for f in run.meta.get("founders", [])) or 1
    seeded = np.ones(size, dtype=bool)
    seeded[:FIRST_ID + founders] = False
    if run.births.height:
        seeded[run.births["child"].to_numpy()] = False
    if not seeded.any():
        return out
    # Root of every id (its generation-0 ancestor) by binary lifting.
    node = np.arange(size, dtype=np.int64)
    d = depth.astype(np.int64)
    for j, step in enumerate(up):
        hop = ((d >> j) & 1).astype(bool)
        node[hop] = step[node[hop]]
    out = seeded[node]
    out[0] = False
    return out


def _parasite_genomes(run: Run) -> set[str] | None:
    """E005's registered parasite-lineage test (`e005_parasites.py`,
    `analyse`, column `parasite`), evaluated once over the whole run: a raw
    hash with >= 2 exact births, harness class (classes.csv) != replicator,
    world class (classes_world.csv, E005's world-physics classes; missing
    hashes `unknown`) != replicator, median foreign share > 0.25 over
    carriers that executed (deaths.csv plus the living at the last
    patches.csv tick), and exact-birth generation depth >= 5 (E005's
    `generation_depth`, imported). None when classes.csv or
    classes_world.csv is absent: the world-class condition cannot be read."""
    from evo_run import _read, csv_path
    from e005_parasites import generation_depth

    world_path = csv_path(run.dir, "classes_world")
    if run.classes is None or world_path is None:
        return None
    world = _read(world_path, "classes").select("raw_hash", world_class="class")
    exact = run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash"))
    per_g = exact.group_by("raw_hash").agg(exact_births=pl.len()).filter(pl.col("exact_births") >= 2)
    per_g = (run.class_of(per_g, "raw_hash").join(world, on="raw_hash", how="left")
             .with_columns(pl.col("world_class").fill_null("unknown")))
    cols = ["birth_hash", "executed", "exec_foreign"]
    final = run.patches["tick"].max()
    living = run.orgs.filter(pl.col("tick") == final).select(cols)
    carriers = pl.concat([run.deaths.select(cols), living]).with_columns(
        foreign=pl.col("exec_foreign") / pl.col("executed").clip(lower_bound=1))
    shares = (carriers.filter(pl.col("executed") > 0).group_by("birth_hash")
              .agg(foreign_med=pl.col("foreign").median()).rename({"birth_hash": "raw_hash"}))
    dep = per_g.join(shares, on="raw_hash", how="left").filter(pl.col("class") != "replicator")
    if not dep.height:
        return set()
    depth = generation_depth(exact, set(dep["raw_hash"]))
    dep = dep.with_columns(depth=pl.col("raw_hash").replace_strict(depth, default=0, return_dtype=pl.Int64))
    par = dep.filter((pl.col("world_class") != "replicator") & (pl.col("foreign_med") > 0.25)
                     & (pl.col("depth") >= 5))
    return set(par["raw_hash"].to_list())


ABSORB_LEN = 21  # body length traits.track reads the absorb count on (its default)


def absorb_class(genomes: pl.DataFrame) -> pl.DataFrame:
    """`raw_hash`, `absorb_class` for every genome: traits.py's absorb-count
    read (ABSORB: the signed byte at offset 6, guarded by a `lit` op at
    offset 5, on bodies of 21 bytes) gives `lt96` or `ge96` (threshold
    ABSORB.threshold); a body the read does not match (another length, or no
    `lit` at the guard) is `unmatched`. As in traits.py the byte is read as
    encoded, so a loop counting the other way (E007 seed 3's `lit A -114 ;
    inc A`) reads as below 96."""
    from traits import ABSORB, LIT, _byte

    hexes = pl.col("bytes_hex")
    guard = hexes.str.slice(2 * ABSORB.guard, 2).str.to_integer(base=16, strict=False)
    match = (hexes.str.len_chars() == 2 * ABSORB_LEN) & ((guard & 0x1F) == LIT).fill_null(False)
    value = _byte(ABSORB.offset, ABSORB.signed)
    t = ABSORB.threshold
    return genomes.select(
        "raw_hash",
        absorb_class=pl.when(~match).then(pl.lit("unmatched"))
        .when(value >= t).then(pl.lit(f"ge{t}")).otherwise(pl.lit(f"lt{t}")),
    )


def _groups(run: Run, group: str) -> pl.DataFrame:
    """`raw_hash` and the grouping column `group` for every genome."""
    if group == "absorb_class":
        if run.meta.get("ancestor", "std") != "std":
            raise ValueError("absorb_class reads the 21-byte std ancestor's absorb count; "
                             f"this run's ancestor is {run.meta['ancestor']!r}")
        return absorb_class(run.genomes)
    if group not in run.genomes.columns:
        raise ValueError(f"--group {group!r}: not a genomes.csv column or absorb_class")
    return run.genomes.select("raw_hash", pl.col(group).cast(pl.Utf8))


def qnn_series(run: Run, group: str = "func_hash") -> pl.DataFrame:
    """QNN per census tick over components given by `group` (spec §2.1,
    `--group`): `qnn`, `qnn_cum`, `n_func` (components with n > 0) and
    `top_func_share` (largest component's share), the last two counting
    groups of `group`. Census bodies by `now_hash`; bodies whose hash has no
    group value are left out of N. The first census has qnn 0. With
    `absorb_class` also `absorb_ge96_share` (the >= 96 share among bodies the
    read matches) and `absorb_unmatched_share` (unmatched among all)."""
    groups = _groups(run, group).rename({group: "g"})
    cens = run.census.join(groups, left_on="now_hash", right_on="raw_hash", how="left")
    comp = cens.group_by("tick", "g").agg(n=pl.col("count").sum()).drop_nulls("g")
    ticks = comp.select(pl.col("tick").unique().sort())
    ticks = ticks.with_columns(prev=pl.col("tick").shift(1))
    comp = comp.join(comp.group_by("tick").agg(total=pl.col("n").sum()), on="tick").with_columns(
        p=pl.col("n") / pl.col("total")).join(ticks, on="tick")
    prev = comp.select(prev="tick", g="g", p_prev="p")
    comp = comp.join(prev, on=["prev", "g"], how="left")
    out = comp.group_by("tick").agg(
        qnn=pl.when(pl.col("prev").is_null()).then(0.0).otherwise(
            (pl.col("p") - pl.col("p_prev").fill_null(0.0)).clip(lower_bound=0.0) ** 2).sum(),
        n_func=pl.len(),
        top_func_share=pl.col("p").max(),
    ).sort("tick").with_columns(qnn_cum=pl.col("qnn").cum_sum())
    out = out.select("tick", "qnn", "qnn_cum", "n_func", "top_func_share")
    if group == "absorb_class":
        from traits import ABSORB
        ge, lt = f"ge{ABSORB.threshold}", f"lt{ABSORB.threshold}"
        shares = comp.group_by("tick").agg(
            **{f"{ABSORB.ge}_share": pl.col("n").filter(pl.col("g") == ge).sum()
               / pl.col("n").filter(pl.col("g").is_in([ge, lt])).sum(),
               "absorb_unmatched_share": pl.col("n").filter(pl.col("g") == "unmatched").sum()
               / pl.col("n").sum()})
        out = out.join(shares, on="tick", how="left").with_columns(
            pl.col(f"{ABSORB.ge}_share").fill_nan(None))
    return out


def _series(run: Run, every: int, depths: tuple[int, ...],
            group: str = "func_hash") -> tuple[pl.DataFrame, int]:
    """Per-census rows, and the deepest generation reached in the run."""
    parent, gen, born, up = _tree(run)
    tin, tout = _euler(parent, gen)
    max_desc = _persistence(run, gen)
    qnn = {r["tick"]: r for r in qnn_series(run, group).iter_rows(named=True)}
    ticks = sorted(qnn)
    max_depth = int(gen.max()) if gen.size else 0
    injected = _injected(run, parent, gen, up)
    any_injected = bool(injected.any())
    org = run.orgs
    parasites = _parasite_genomes(run)
    if run.classes is not None:
        org = run.class_of(org, "birth_hash", "birth_class")
    if parasites is not None:
        org = org.with_columns(is_parasite=pl.col("birth_hash").is_in(sorted(parasites)))
    # Per orgs row: the MODES component (func_hash of the birth genome) as an
    # integer code, -1 without one, and whether the birth hash is
    # replicator-class. A hash listed twice takes its last row.
    funcs = run.genomes.select("raw_hash", "func_hash").unique("raw_hash", keep="last", maintain_order=True)
    codes = funcs.select("func_hash").drop_nulls().unique(maintain_order=True).with_row_index("code")
    funcs = funcs.join(codes, on="func_hash", how="left", maintain_order="left")
    lookup = lambda old, new, default, dtype: pl.col("birth_hash").replace_strict(
        old, new, default=default, return_dtype=dtype).fill_null(default)
    org = org.with_columns(_code=lookup(funcs["raw_hash"], funcs["code"].cast(pl.Int64).fill_null(-1),
                                        -1, pl.Int64))
    if run.classes is not None:
        cls = run.classes.select("raw_hash", "class").unique("raw_hash", keep="last", maintain_order=True)
        org = org.with_columns(_rep=lookup(cls["raw_hash"], cls["class"] == "replicator", False, pl.Boolean))
    rows = []
    org_by_tick = {int(k[0] if isinstance(k, tuple) else k): v
                   for k, v in org.partition_by("tick", as_dict=True).items()}
    # Components seen so far and those of the previous census, per depth.
    seen = {d: np.zeros(codes.height, dtype=bool) for d in depths}
    previous = {d: np.zeros(codes.height, dtype=bool) for d in depths}
    previous_codes = {d: np.zeros(0, dtype=np.int64) for d in depths}
    # A depth deeper than any generation the run reached is censored at every
    # census; its MODES columns are left empty.
    applies = {d: max_depth >= d for d in depths}
    censored = {d: not applies[d] for d in depths}
    deepest = max(depths, default=0)
    censored_all = deepest > 0 and not applies[deepest]
    previous_mrca = None
    for ix, tick in enumerate(ticks):
        alive = org_by_tick[tick]
        tips = alive["id"].to_numpy().astype(np.int32, copy=False)
        sampled = ix % every == 0
        tm = _tree_metrics(tips, gen, born, tin, tout, up) if sampled else None
        mrca_changed = None
        if tm is not None:
            # The sweep counter follows the MRCA of the tips that descend from
            # founders; lines from `--inject` copies are left out, so their
            # arrival and loss are not counted as MRCA changes.
            sweep_mrca = tm["mrca_id"]
            if any_injected and injected[tips].any():
                own = tips[~injected[tips]]
                sweep_mrca = _mrca(own, gen, tin, up) if own.size else None
            if sweep_mrca is not None:
                mrca_changed = previous_mrca is not None and sweep_mrca != previous_mrca
                previous_mrca = sweep_mrca
        code = alive["_code"].to_numpy()
        tip_gen, tip_desc = gen[tips], max_desc[tips]
        row = dict(qnn[tick], pop=alive.height,
                   rep_alive=int(alive["_rep"].sum()) if run.classes is not None else None,
                   len_med=float(alive["len"].median()) if alive.height else None,
                   mrca_gen=tm["mrca_gen"] if tm else None, mrca_tick=tm["mrca_tick"] if tm else None,
                   mrca_changed=mrca_changed,
                   root_lines=tm["root_lines"] if tm else None,
                   ancestor_count=tm["ancestor_count"] if tm else None,
                   mpd=tm["mpd"] if tm else None, spd=tm["spd"] if tm else None,
                   mean_ed=tm["mean_ed"] if tm else None,
                   parasite_share=None, entered_share=None)
        top_gen = int(tip_gen.max()) if tips.size else 0
        for d in depths:
            # Components of the bodies persistent at d, in census row order.
            persistent = code[(code >= 0) & (tip_desc >= tip_gen + d)]
            comps, first, counts = np.unique(persistent, return_index=True, return_counts=True)
            n = int(persistent.size)
            if applies[d]:
                row[f"change_{d}"] = int((~previous[d][comps]).sum())
                row[f"novelty_{d}"] = int((~seen[d][comps]).sum())
                # Summed in order of first appearance, as a dict count would be.
                counts = counts[np.argsort(first, kind="stable")].tolist()
                row[f"ecology_{d}"] = -sum((v / n) * math.log2(v / n) for v in counts) if n else 0.0
            else:
                row[f"change_{d}"] = row[f"novelty_{d}"] = row[f"ecology_{d}"] = None
            seen[d][comps] = True
            previous[d][previous_codes[d]] = False
            previous[d][comps] = True
            previous_codes[d] = comps
            # Held true once set: persistence cannot be known from here on.
            censored[d] = censored[d] or max_depth < top_gen + d
            row[f"modes_censored_{d}"] = censored[d]
        censored_all = censored_all or max_depth < top_gen + deepest
        row["modes_censored"] = censored_all
        if "exec_foreign" in alive.columns:
            row["foreign_share"] = float(alive["exec_foreign"].sum() / max(1, alive["executed"].sum()))
            if parasites is not None:
                row["parasite_share"] = float(alive["is_parasite"].mean())
        if "exec_by_others" in alive.columns and run.classes is not None:
            rep = alive.filter(pl.col("birth_class") == "replicator")
            row["entered_share"] = float((rep["exec_by_others"] > 0).mean()) if rep.height else None
        rows.append(row)
    return (pl.DataFrame(rows) if rows else pl.DataFrame()), max_depth


def compute(run: Run | str | Path, every: int = 1, depths: tuple[int, ...] = (187, 1870),
            group: str = "func_hash") -> tuple[pl.DataFrame, dict]:
    """Compute per-census series and whole-run summary for an evo run; the
    QNN columns are over components of `group` (`func_hash`, any other
    genomes.csv column, or `absorb_class`)."""
    if every < 1:
        raise ValueError("every must be at least 1")
    if not isinstance(run, Run):
        run = load(run)
    series, max_gen = _series(run, every, depths, group)
    summary: dict = {}
    if series.height:
        summary = {
            "run": str(run.dir),
            "group": group,
            "qnn_cum": float(series["qnn_cum"][-1]),
            "mrca_changes": int(series["mrca_changed"].sum()),
            "final_tick": int(series["tick"][-1]),
            "max_gen": max_gen,
        }
        stationary_tree = series.filter(pl.col("tick") >= STATIONARY)
        for col in ("mpd", "mean_ed", *CLASS_COLUMNS):
            summary[f"mean_{col}"] = _mean(stationary_tree[col])
        for d in depths:
            if max_gen < d:
                for name in ("change", "novelty", "ecology"):
                    summary[f"mean_{name}_{d}"] = "censored"
                summary.setdefault("censored_depths", {})[str(d)] = (
                    f"the run's deepest generation is {max_gen}, below {d}")
                continue
            stationary_modes = series.filter(
                (pl.col("tick") >= STATIONARY) & pl.col(f"modes_censored_{d}").eq(False)
            )
            for name in ("change", "novelty", "ecology"):
                summary[f"mean_{name}_{d}"] = _mean(stationary_modes[f"{name}_{d}"])
        summary["mrca_tick"] = last_value(series["mrca_tick"])
        summary["mrca_gen"] = last_value(series["mrca_gen"])
        summary["root_lines"] = last_value(series["root_lines"])
    return series, summary


def _mean(col: pl.Series) -> float | None:
    m = col.drop_nulls().mean() if col.len() else None
    return None if m is None else float(m)


def last_value(col: pl.Series):
    """Last non-null value of a series column, or None. With `--every K`
    the tree columns are null at unsampled censuses, the last one included."""
    vals = col.drop_nulls()
    return vals[-1] if vals.len() else None


def site_entropy(bodies: list[bytes]) -> list[float | None]:
    """Shannon entropy (bits) of canonical bytes at each body position."""
    if not bodies:
        return []
    width = max(map(len, bodies))
    out = []
    for pos in range(width):
        vals = [b[pos] for b in bodies if pos < len(b)]
        if not vals:
            out.append(None)
            continue
        counts = np.bincount(np.asarray(vals, dtype=np.uint8), minlength=256)
        p = counts[counts > 0] / len(vals)
        h = float(-(p * np.log2(p)).sum())
        out.append(h if h > 0 else 0.0)  # a constant site gives -0.0
    return out


SITE_WINDOW = 25_000
HARNESS_TICKS = 3_000  # evo-core's default --harness-ticks
SITES_COLUMNS = ("pos", "op", "entropy", "exact_pad", "class_pad", "meaningful")
# Integer columns of a --neighbours CSV (T03 §2); the rest stay strings.
NEIGHBOURS_INTS = ("pos", "byte", "births_alone", "exact_alone", "births_host", "exact_host",
                   "host_copies", "host_exact", "executed", "exec_foreign", "entry_off", "ticks_run")


@dataclass
class SiteWindow:
    """One window of the sites analysis before the knockout: the top
    replicator-class component, the raw body to knock out, and the sites
    frame (knockout columns empty)."""
    window: int
    func_hash: str
    hex: str
    exact_births: int  # the window's exact births of `func_hash`
    bodies: int        # same-length replicator-class exact births under `entropy`
    sites: pl.DataFrame


def site_windows(run: Run, window: int = SITE_WINDOW) -> dict[int, SiteWindow]:
    """The entropy half of the sites analysis (spec §3), keyed by window
    number (ticks (w-1)*window+1 .. w*window); empty without classes.csv."""
    if run.classes is None:
        return {}
    from traits import canonical_instrs

    exact = run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash")).select(
        "tick", "raw_hash", "len", bin=((pl.col("tick") - 1) // window + 1).cast(pl.Int64)
    )
    exact = run.class_of(exact, "raw_hash").filter(pl.col("class") == "replicator")
    exact = exact.join(run.genomes.select("raw_hash", "func_hash", "bytes_hex"), on="raw_hash", how="left")
    results: dict[int, SiteWindow] = {}
    for win in sorted(exact["bin"].unique().to_list()):
        frame = exact.filter(pl.col("bin") == win)
        top = (frame.group_by("func_hash").agg(n=pl.len())
               .sort(["n", "func_hash"], descending=[True, False]).row(0, named=True))
        # Raw bodies of one func_hash differ only in bits the canonical form
        # drops; the one knocked out is the most common among the births.
        raw = (frame.filter(pl.col("func_hash") == top["func_hash"]).group_by("bytes_hex").agg(n=pl.len())
               .sort(["n", "bytes_hex"], descending=[True, False]).row(0, named=True))
        top_body = bytes.fromhex(raw["bytes_hex"])
        ops, canonical = [], bytearray()
        for op, modifier, operand in canonical_instrs(top_body):
            canonical.append(op | (modifier << 5))
            ops.append(str(op))
            if operand is not None:
                canonical.append(operand & 0xFF)
                ops.append("operand")
        same_len = frame.filter(pl.col("len") == len(top_body))
        bodies = [bytes.fromhex(h) for h in same_len["bytes_hex"].to_list()]
        ent = site_entropy([bytes(_canonical_body(b, canonical_instrs)) for b in bodies])
        n = len(canonical)
        sites = pl.DataFrame({
            "pos": list(range(n)), "op": ops[:n], "entropy": ent,
            "exact_pad": [None] * n, "class_pad": [None] * n, "meaningful": [None] * n,
        }, schema_overrides={"exact_pad": pl.Int64, "class_pad": pl.Utf8, "meaningful": pl.Boolean})
        results[int(win)] = SiteWindow(int(win), top["func_hash"], raw["bytes_hex"], int(top["n"]),
                                       len(bodies), sites)
    return results


def evo_bin(path: str | Path | None = None) -> Path:
    """`path`, else $EVO_BIN, else evo-core/target/release/evo-core(.exe);
    not built here."""
    p = path or os.environ.get("EVO_BIN")
    if p:
        # Absolute, so a subprocess run from another directory finds it.
        p = Path(p).resolve()
    else:
        rel = ROOT / "evo-core" / "target" / "release"
        p = next((rel / n for n in ("evo-core.exe", "evo-core") if (rel / n).exists()), rel / "evo-core.exe")
    if not p.exists():
        raise FileNotFoundError(f"evo-core binary not found: {p} (give --evo-bin or EVO_BIN)")
    return p


def read_neighbours(path: str | Path) -> pl.DataFrame:
    """A `--neighbours` CSV (T03 §2 columns), hashes and labels as strings,
    counts as integers (`byte` null for a deletion)."""
    df = pl.read_csv(path, infer_schema=False)
    return df.with_columns(pl.col(c).cast(pl.Int64) for c in NEIGHBOURS_INTS if c in df.columns)


def _engine(runner: Callable, cmd: list[str]) -> None:
    res = runner(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}: exit {res.returncode}: {(res.stderr or '').strip()}")


def knockout(hex_: str, exe: str | Path, harness_ticks: int = HARNESS_TICKS,
             evo_flags: Sequence[str] = (), runner: Callable = subprocess.run) -> tuple[dict, pl.DataFrame]:
    """The engine half of the sites analysis for one body: `(base,
    neighbours)`. `base` is the unmutated body alone (`class_alone`,
    `births_alone`, `exact_alone`) from `--classify` on a one-row
    genomes.csv; `neighbours` the `--neighbours HEX --neighbours-pad-only`
    CSV (read_neighbours). Both calls get `--harness-ticks` and `evo_flags`.
    `runner` stands in for subprocess.run in tests."""
    flags = [*map(str, evo_flags)]
    ticks = ["--harness-ticks", str(harness_ticks)]
    with tempfile.TemporaryDirectory(prefix="t05_sites_") as tmp:
        tmp = Path(tmp)
        (tmp / "genomes.csv").write_text(f"raw_hash,bytes_hex\nbase,{hex_}\n", encoding="utf-8", newline="")
        _engine(runner, [str(exe), "--classify", str(tmp), *ticks, *flags])
        cls = pl.read_csv(tmp / "classes.csv", infer_schema=False).row(0, named=True)
        out = tmp / "neighbours.csv"
        _engine(runner, [str(exe), "--neighbours", hex_, "--neighbours-pad-only",
                         "--neighbours-out", str(out), *ticks, *flags])
        nb = read_neighbours(out)
    base = dict(class_alone=cls["class"], births_alone=int(cls["births"]),
                exact_alone=int(cls["exact_births"]))
    return base, nb


def is_meaningful(exact_pad: int, class_pad: str, base_exact: int, base_class: str) -> bool:
    """Spec §3: a knockout is meaningful when the mutant's exact births alone
    are below half the unmutated body's, or its class alone differs."""
    return 2 * exact_pad < base_exact or class_pad != base_class


def merge_knockout(sites: pl.DataFrame, neighbours: pl.DataFrame, base: dict) -> pl.DataFrame:
    """Fill `exact_pad`, `class_pad`, `meaningful` in a sites frame from a
    neighbours frame (its `sub` rows with byte 0, one per position) and the
    unmutated body's `base` (`exact_alone`, `class_alone`)."""
    pad = neighbours.filter((pl.col("kind") == "sub") & (pl.col("byte") == 0)).select(
        "pos", exact_pad="exact_alone", class_pad="class_alone")
    if sorted(pad["pos"].to_list()) != sites["pos"].to_list():
        raise ValueError(f"neighbours file has pad rows at {sorted(pad['pos'].to_list())}, "
                         f"sites positions are 0..{sites.height - 1}")
    out = sites.drop("exact_pad", "class_pad", "meaningful", strict=False).join(
        pad, on="pos", how="left").sort("pos")
    flags = [is_meaningful(e, c, base["exact_alone"], base["class_alone"])
             for e, c in zip(out["exact_pad"].to_list(), out["class_pad"].to_list())]
    return out.with_columns(meaningful=pl.Series(flags, dtype=pl.Boolean)).select(SITES_COLUMNS)


def sites_relation(sites: pl.DataFrame) -> dict:
    """The diagnostic per window: positions, meaningful count, mean entropy
    of meaningful and of other sites, Spearman's rho of entropy against
    meaningful (average ranks for ties; None when either is constant), and
    `auc`, the probability that a meaningful site has lower entropy than a
    non-meaningful one (ties count half; None when a group is empty).
    Negative rho, auc near 1: the low-entropy sites are the meaningful ones.
    With few non-meaningful sites rho is bounded well inside -1 (one of 21:
    about -0.37 at most), so auc is the one to read."""
    s = sites.drop_nulls(["entropy", "meaningful"])
    ent, mean = s["entropy"], s["meaningful"]
    rho = None
    if s.height > 1 and ent.n_unique() > 1 and mean.n_unique() > 1:
        rho = float(np.corrcoef(ent.rank("average").to_numpy(),
                                mean.cast(pl.Float64).rank("average").to_numpy())[0, 1])
    yes, no = ent.filter(mean).to_numpy(), ent.filter(~mean).to_numpy()
    auc = None
    if yes.size and no.size:
        auc = float(((yes[:, None] < no[None, :]).sum() + 0.5 * (yes[:, None] == no[None, :]).sum())
                    / (yes.size * no.size))
    return dict(positions=sites.height, meaningful=int(mean.sum()),
                entropy_meaningful=_mean(ent.filter(mean)), entropy_other=_mean(ent.filter(~mean)),
                spearman=rho, auc=auc)


def knockout_windows(run: Run, exe: str | Path, harness_ticks: int = HARNESS_TICKS,
                     evo_flags: Sequence[str] = (), window: int = SITE_WINDOW,
                     runner: Callable = subprocess.run) -> tuple[dict[int, pl.DataFrame], dict]:
    """The sites analysis (spec §3): per window the filled sites frame, and
    the `sites` record for summary.json. A body that tops several windows
    is run once."""
    frames, record, done = {}, {}, {}
    for win, sw in site_windows(run, window).items():
        if sw.hex not in done:
            done[sw.hex] = knockout(sw.hex, exe, harness_ticks, evo_flags, runner)
        base, nb = done[sw.hex]
        if base["class_alone"] != "replicator":
            print(f"sites window {win}: the top body is {base['class_alone']!r} in the harness, "
                  "replicator in classes.csv; check --evo-flags against the run's physics",
                  file=sys.stderr)
        frames[win] = merge_knockout(sw.sites, nb, base)
        record[str(win)] = dict(func_hash=sw.func_hash, hex=sw.hex, exact_births_window=sw.exact_births,
                                bodies=sw.bodies, **base, **sites_relation(frames[win]))
    return frames, record


def _canonical_body(body: bytes, parser) -> bytes:
    out = bytearray()
    for op, modifier, operand in parser(body):
        out.append(op | (modifier << 5))
        if operand is not None:
            out.append(operand & 0xFF)
    return bytes(out)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Compute QNN, tree measures and MODES for a run")
    ap.add_argument("run_dir")
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--depths", default="187,1870")
    ap.add_argument("--group", default="func_hash",
                    help="QNN components: func_hash (default), another genomes.csv column, "
                         "or absorb_class (lt96 / ge96 / unmatched by traits.py's absorb read)")
    ap.add_argument("--knockout", action="store_true",
                    help="also write sites_<window>.csv (entropy against pad knockouts, spec §3)")
    ap.add_argument("--evo-bin", help="evo-core binary for --knockout (default $EVO_BIN, else "
                                      "evo-core/target/release/evo-core.exe; not built)")
    ap.add_argument("--harness-ticks", type=int, default=HARNESS_TICKS)
    ap.add_argument("--evo-flags", default="",
                    help='physics flags for the engine calls, one string split on whitespace, '
                         'e.g. --evo-flags "--legacy-pending-range" for a pre-T08 run with a '
                         'post-T08 binary')
    ap.add_argument("--out")
    argv = list(sys.argv[1:] if argv is None else argv)
    # argparse takes a lone "--flag" value for an option; bind the value
    # after --evo-flags to it so `--evo-flags "--no-protect"` works.
    for i in range(len(argv) - 1):
        if argv[i] == "--evo-flags":
            argv[i:i + 2] = [f"--evo-flags={argv[i + 1]}"]
            break
    a = ap.parse_args(argv)
    a.evo_flags = a.evo_flags.split()
    return a


def main(argv: Sequence[str] | None = None) -> None:
    a = parse_args(argv)
    exe = None
    if a.knockout:
        try:
            exe = evo_bin(a.evo_bin)
        except FileNotFoundError as e:
            raise SystemExit(f"--knockout: {e}")
    depths = tuple(int(x) for x in a.depths.split(","))
    run = load(a.run_dir)
    series, summary = compute(run, a.every, depths, a.group)
    out = Path(a.out) if a.out else Path(a.run_dir) / "measures"
    out.mkdir(parents=True, exist_ok=True)
    series.write_csv(out / "series.csv")
    if exe is not None:
        # The sites files come on top of the normal output.
        frames, summary["sites"] = knockout_windows(run, exe, a.harness_ticks, a.evo_flags)
        summary["sites_harness"] = dict(binary=str(exe), harness_ticks=a.harness_ticks,
                                        evo_flags=a.evo_flags)
        for win, sites in frames.items():
            sites.write_csv(out / f"sites_{win}.csv")
        if not frames:
            print("sites: no classes.csv, so no replicator-class bodies; no sites files written",
                  file=sys.stderr)
    import json
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
