"""Standing evolutionary measures for recorded evo runs (T05,
docs/tasks/T05-measures.md).

    uv run measures.py RUN_DIR [--every K] [--depths 187,1870] [--group COL] [--knockout] [--out DIR]

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
- Summary means (`mean_mpd`, `mean_mean_ed`, `mean_<modes>_D`) are over
  censuses at or after tick 25,000 (MODES: uncensored ones only).
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import polars as pl

from evo_run import Run, load

STATIONARY = 25_000  # the stationary phase starts here (summary means)
FIRST_ID = 2  # evo-core's first organism id (sim.rs FIRST_ID)


def _tree(run: Run):
    """Return dense parent/depth/tick arrays and binary-lifting ancestors."""
    b = run.births.select("child", "executor", "tick").sort("child")
    org = run.orgs.select("id", "parent", "birth_tick").unique("id")
    max_id = max(int(b["child"].max()) if b.height else 0,
                 int(org["id"].max()) if org.height else 0)
    parent = np.zeros(max_id + 1, dtype=np.int32)
    born = np.zeros(max_id + 1, dtype=np.int32)
    # Birth rows are in creation order (IDs increase), so each executor's
    # generation is known when its child is visited.
    depth = np.zeros(max_id + 1, dtype=np.int32)
    if b.height:
        for child, executor, tick in b.iter_rows():
            child, executor = int(child), int(executor)
            parent[child] = executor
            born[child] = int(tick)
            depth[child] = depth[executor] + 1
    if org.height:
        for ident, par, tick in org.iter_rows():
            ident = int(ident)
            if ident > 0 and parent[ident] == 0:
                parent[ident] = int(par)
                born[ident] = int(tick)
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
    mrca = int(tips[0])
    for tip in tips[1:]:
        mrca = _lca(mrca, int(tip), depth, up)
    if n == 1:
        return dict(mrca_id=mrca, mrca_gen=int(depth[mrca]) if mrca else -1,
                    mrca_tick=int(born[mrca]) if mrca else 0, root_lines=0,
                    ancestor_count=0, mpd=0.0, spd=0, mean_ed=0.0)

    ordered = tips[np.argsort(tin[tips])]
    nodes = list(map(int, ordered))
    nodes.extend(_lca(int(a), int(b), depth, up) for a, b in zip(ordered[:-1], ordered[1:]))
    nodes.append(0)
    nodes = sorted(set(nodes), key=lambda x: int(tin[x]))
    stack: list[int] = []
    vparent: dict[int, int] = {}
    children: dict[int, int] = {x: 0 for x in nodes}
    for node in nodes:
        while stack and not (tin[stack[-1]] <= tin[node] < tout[stack[-1]]):
            stack.pop()
        if stack:
            vparent[node] = stack[-1]
            children[stack[-1]] += 1
        stack.append(node)
    tip_set = set(map(int, tips))
    counts = {x: (1 if x in tip_set else 0) for x in nodes}
    spd = 0
    eds = np.zeros(n, dtype=np.float64)
    tip_pos = {int(t): i for i, t in enumerate(tips)}
    ordered_tip_tin = tin[ordered]
    ordered_eds = np.zeros(n, dtype=np.float64)
    for node in sorted(nodes, key=lambda x: int(depth[x]), reverse=True):
        k = counts[node]
        par = vparent.get(node)
        if par is not None and k:
            length = (int(depth[node]) if node else -1) - (int(depth[par]) if par else -1)
            spd += length * k * (n - k)
            counts[par] += k
    # Internal nodes of the induced tree: its branch points, tips included
    # (a living organism whose living descendants run through two or more of
    # its children). A tip with one line of living descendants is a
    # unifurcation, stripped as any other.
    ancestors = sum(1 for x in nodes if children[x] >= 2)
    # Fair proportion over the original root paths, below the MRCA only (the
    # stem from the MRCA to the virtual root is shared by every tip and would
    # make ED grow with MRCA depth). On the virtual tree each edge represents
    # a chain with constant descendant-tip count.
    for node in nodes:
        par = vparent.get(node)
        if par is None or node == mrca:
            continue
        k = counts[node]
        if not k:
            continue
        length = (int(depth[node]) if node else -1) - (int(depth[par]) if par else -1)
        # Edges on a contracted path have equal descendant count, so their
        # combined fair-proportion length is length / k.
        # Attribute it to the descendant tips using their ancestor relation.
        lo = int(np.searchsorted(ordered_tip_tin, tin[node], side="left"))
        hi = int(np.searchsorted(ordered_tip_tin, tout[node], side="left"))
        ordered_eds[lo:hi] += length / k
    for i, tip in enumerate(ordered):
        eds[tip_pos[int(tip)]] = ordered_eds[i]
    pairs = n * (n - 1) // 2
    # Children of the MRCA with living descendants: on the virtual tree each
    # child of the MRCA stands for one original child's line.
    return dict(mrca_id=mrca, mrca_gen=int(depth[mrca]) if mrca else -1,
                mrca_tick=int(born[mrca]) if mrca else 0, root_lines=int(children[mrca]),
                ancestor_count=int(ancestors), spd=int(spd), mpd=float(spd / pairs),
                mean_ed=float(eds.mean()))


def _euler(parent: np.ndarray, depth: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Euler entry/exit intervals for ancestry checks in the virtual tree."""
    size = len(parent)
    counts = np.bincount(parent[1:], minlength=size).astype(np.int64)
    offsets = np.empty(size + 1, dtype=np.int64)
    offsets[0] = 0
    np.cumsum(counts, out=offsets[1:])
    children = np.empty(max(0, size - 1), dtype=np.int32)
    cursor = offsets[:-1].copy()
    for child in range(1, size):
        p = int(parent[child])
        children[cursor[p]] = child
        cursor[p] += 1
    tin = np.zeros(size, dtype=np.int32)
    tout = np.zeros(size, dtype=np.int32)
    clock = 0
    stack: list[tuple[int, int]] = [(0, 0)]
    while stack:
        node, idx = stack[-1]
        if idx == 0:
            tin[node] = clock
            clock += 1
        lo, hi = int(offsets[node]), int(offsets[node + 1])
        if lo + idx < hi:
            child = int(children[lo + idx])
            stack[-1] = (node, idx + 1)
            stack.append((child, 0))
        else:
            tout[node] = clock
            stack.pop()
    return tin, tout


def _persistence(run: Run, depth: np.ndarray) -> np.ndarray:
    """Maximum descendant generation for each organism id."""
    max_desc = depth.copy()
    b = run.births.select("child", "executor").sort("child", descending=True)
    for child, executor in b.iter_rows():
        child, executor = int(child), int(executor)
        if max_desc[child] > max_desc[executor]:
            max_desc[executor] = max_desc[child]
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
    hashmap = dict(run.genomes.select("raw_hash", "func_hash").iter_rows())
    classes = dict(run.classes.select("raw_hash", "class").iter_rows()) if run.classes is not None else {}
    parasites = _parasite_genomes(run)
    if run.classes is not None:
        org = run.class_of(org, "birth_hash", "birth_class")
    if parasites is not None:
        org = org.with_columns(is_parasite=pl.col("birth_hash").is_in(sorted(parasites)))
    rows = []
    org_by_tick = {int(k[0] if isinstance(k, tuple) else k): v
                   for k, v in org.partition_by("tick", as_dict=True).items()}
    seen_components: dict[int, set[str]] = {d: set() for d in depths}
    previous_modes: dict[int, set[str]] = {d: set() for d in depths}
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
                sweep_mrca = None
                if own.size:
                    sweep_mrca = int(own[0])
                    for tip in own[1:]:
                        sweep_mrca = _lca(sweep_mrca, int(tip), gen, up)
            if sweep_mrca is not None:
                mrca_changed = previous_mrca is not None and sweep_mrca != previous_mrca
                previous_mrca = sweep_mrca
        hashes = alive["birth_hash"].to_list()
        tips_list = alive["id"].to_list()
        component_bodies = []
        persistent_components = {d: [] for d in depths}
        for ident, h in zip(tips_list, hashes):
            c = hashmap.get(h)
            component_bodies.append(c)
            if c is None:
                continue
            for d in depths:
                if max_desc[int(ident)] >= gen[int(ident)] + d:
                    persistent_components[d].append(c)
        row = dict(qnn[tick], pop=alive.height,
                   rep_alive=(sum(classes.get(h) == "replicator" for h in hashes)
                              if run.classes is not None else None),
                   len_med=float(alive["len"].median()) if alive.height else None,
                   mrca_gen=tm["mrca_gen"] if tm else None, mrca_tick=tm["mrca_tick"] if tm else None,
                   mrca_changed=mrca_changed,
                   root_lines=tm["root_lines"] if tm else None,
                   ancestor_count=tm["ancestor_count"] if tm else None,
                   mpd=tm["mpd"] if tm else None, spd=tm["spd"] if tm else None,
                   mean_ed=tm["mean_ed"] if tm else None,
                   parasite_share=None, entered_share=None)
        top_gen = max((int(gen[int(i)]) for i in tips_list), default=0)
        for d in depths:
            f = set(persistent_components[d])
            counts = {}
            for c in persistent_components[d]:
                counts[c] = counts.get(c, 0) + 1
            n = sum(counts.values())
            if applies[d]:
                row[f"change_{d}"] = len(f - previous_modes[d])
                row[f"novelty_{d}"] = len(f - seen_components[d])
                row[f"ecology_{d}"] = -sum((v / n) * math.log2(v / n) for v in counts.values()) if n else 0.0
            else:
                row[f"change_{d}"] = row[f"novelty_{d}"] = row[f"ecology_{d}"] = None
            seen_components[d] |= f
            previous_modes[d] = f
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
        for col in ("mpd", "mean_ed"):
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
        out.append(float(-(p * np.log2(p)).sum()))
    return out


def site_entropy_windows(run: Run, window: int = 25_000) -> dict[int, pl.DataFrame]:
    """Compute the registered entropy half of the sites analysis.

    Returns window-number keyed frames with the available ``pos``, ``op``
    and ``entropy`` columns. Knockout results remain absent until T03 adds
    the engine's neighbour command.
    """
    if run.classes is None:
        return {}
    from traits import canonical_instrs

    exact = run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash")).select(
        "tick", "raw_hash", "len", bin=((pl.col("tick") - 1) // window + 1).cast(pl.Int64)
    )
    exact = run.class_of(exact, "raw_hash").filter(pl.col("class") == "replicator")
    exact = exact.join(run.genomes.select("raw_hash", "func_hash", "bytes_hex"), on="raw_hash", how="left")
    results: dict[int, pl.DataFrame] = {}
    for win in sorted(exact["bin"].unique().to_list()):
        frame = exact.filter(pl.col("bin") == win)
        top = (frame.group_by("func_hash").len().sort(["len", "func_hash"], descending=[True, False]).row(0, named=True))
        top_hash = top["func_hash"]
        top_hex = frame.filter(pl.col("func_hash") == top_hash)["bytes_hex"][0]
        top_body = bytes.fromhex(top_hex)
        top_ins = canonical_instrs(top_body)
        ops, canonical = [], bytearray()
        for op, modifier, operand in top_ins:
            canonical.append(op | (modifier << 5))
            ops.append(str(op))
            if operand is not None:
                canonical.append(operand & 0xFF)
                ops.append("operand")
        same_len = frame.filter(pl.col("len") == len(top_body))
        bodies = [bytes.fromhex(h) for h in same_len["bytes_hex"].to_list()]
        ent = site_entropy([bytes(_canonical_body(b, canonical_instrs)) for b in bodies])
        results[int(win)] = pl.DataFrame({
            "pos": list(range(len(canonical))), "op": ops[:len(canonical)], "entropy": ent,
            "exact_pad": [None] * len(canonical), "class_pad": [None] * len(canonical),
            "meaningful": [None] * len(canonical),
        })
    return results


def _canonical_body(body: bytes, parser) -> bytes:
    out = bytearray()
    for op, modifier, operand in parser(body):
        out.append(op | (modifier << 5))
        if operand is not None:
            out.append(operand & 0xFF)
    return bytes(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute QNN, tree measures and MODES for a run")
    ap.add_argument("run_dir")
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--depths", default="187,1870")
    ap.add_argument("--group", default="func_hash",
                    help="QNN components: func_hash (default), another genomes.csv column, "
                         "or absorb_class (lt96 / ge96 / unmatched by traits.py's absorb read)")
    ap.add_argument("--knockout", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    depths = tuple(int(x) for x in a.depths.split(","))
    run = load(a.run_dir)
    series, summary = compute(run, a.every, depths, a.group)
    out = Path(a.out) if a.out else Path(a.run_dir) / "measures"
    out.mkdir(parents=True, exist_ok=True)
    series.write_csv(out / "series.csv")
    import json
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if a.knockout:
        # The sites files come on top of the normal output.
        for win, sites in site_entropy_windows(run).items():
            sites.write_csv(out / f"sites_{win}.csv")
        print("sites: entropy columns written where classes.csv is present; the knockout columns "
              "(exact_pad, class_pad, meaningful) stay empty until the --neighbours loop is wired in.",
              file=sys.stderr)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
