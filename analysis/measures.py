"""Standing evolutionary measures for recorded evo runs.

Run with ``uv run measures.py RUN_DIR`` (from analysis/), or import
``compute`` from experiment runners.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import polars as pl

from evo_run import Run, load


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
        return dict(mrca_id=0, mrca_gen=-1, mrca_tick=0,
                    ancestor_count=0, mpd=None, spd=None, mean_ed=None)
    mrca = int(tips[0])
    for tip in tips[1:]:
        mrca = _lca(mrca, int(tip), depth, up)
    if n == 1:
        return dict(mrca_id=mrca, mrca_gen=int(depth[mrca]) if mrca else -1,
                    mrca_tick=int(born[mrca]) if mrca else 0,
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
    ancestors = sum(1 for x in nodes if x not in tip_pos and children[x] >= 2)
    # Fair proportion over the original root paths. On the virtual tree each
    # edge represents a chain with constant descendant-tip count.
    for node in nodes:
        par = vparent.get(node)
        if par is None:
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
    return dict(mrca_id=mrca, mrca_gen=int(depth[mrca]) if mrca else -1,
                mrca_tick=int(born[mrca]) if mrca else 0,
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


def _parasite_genomes(run: Run) -> set[str] | None:
    """E005's parasite-lineage test, evaluated once over the whole run."""
    required = {"raw_hash", "parent_now_hash", "child", "executor", "tick"}
    if run.classes is None or not required.issubset(run.births.columns):
        return None
    exact = run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash"))
    replicated = exact.group_by("raw_hash").len().filter(pl.col("len") >= 2)
    replicated = run.class_of(replicated, "raw_hash").filter(pl.col("class") != "replicator")
    candidates = set(replicated["raw_hash"].to_list())
    if not candidates or not {"exec_foreign", "executed"}.issubset(run.deaths.columns):
        return set()
    rows = exact.filter(pl.col("raw_hash").is_in(list(candidates))).sort("tick", "child")
    lineage_depth: dict[tuple[str, int], int] = {}
    best = {h: 0 for h in candidates}
    for h, child, executor in rows.select("raw_hash", "child", "executor").iter_rows():
        d = lineage_depth.get((h, int(executor)), 0) + 1
        lineage_depth[(h, int(child))] = d
        if d > best[h]:
            best[h] = d
    if not {"birth_hash", "executed", "exec_foreign"}.issubset(run.orgs.columns):
        return set()
    last = int(run.orgs["tick"].max()) if run.orgs.height else -1
    living = run.orgs.filter(pl.col("tick") == last)
    carriers = pl.concat([
        run.deaths.select("birth_hash", "executed", "exec_foreign"),
        living.select("birth_hash", "executed", "exec_foreign"),
    ]).filter(pl.col("executed") > 0).with_columns(
        foreign=pl.col("exec_foreign") / pl.col("executed")
    ).group_by("birth_hash").agg(foreign_med=pl.col("foreign").median())
    median_foreign = dict(carriers.iter_rows())
    return {h for h in candidates if best.get(h, 0) >= 5
            and median_foreign.get(h) is not None and median_foreign[h] > 0.25}


def _series(run: Run, every: int, depths: tuple[int, ...]) -> pl.DataFrame:
    parent, gen, born, up = _tree(run)
    tin, tout = _euler(parent, gen)
    max_desc = _persistence(run, gen)
    genome = run.genomes.select("raw_hash", "func_hash")
    cens = run.census.join(genome, left_on="now_hash", right_on="raw_hash", how="left")
    func = cens.group_by("tick", "func_hash").agg(n=pl.col("count").sum()).drop_nulls("func_hash")
    totals = func.group_by("tick").agg(total=pl.col("n").sum())
    func = func.join(totals, on="tick").with_columns(p=pl.col("n") / pl.col("total"))
    proportions: dict[int, dict[str, float]] = {}
    for tick, h, p in func.select("tick", "func_hash", "p").iter_rows():
        proportions.setdefault(int(tick), {})[str(h)] = float(p)
    ticks = sorted(proportions)
    max_depth = int(gen.max()) if gen.size else 0
    org = run.orgs
    hashmap = dict(run.genomes.select("raw_hash", "func_hash").iter_rows())
    classes = dict(run.classes.select("raw_hash", "class").iter_rows()) if run.classes is not None else {}
    parasites = _parasite_genomes(run)
    rows = []
    org_by_tick = {int(k[0] if isinstance(k, tuple) else k): v
                   for k, v in org.partition_by("tick", as_dict=True).items()}
    seen_components: dict[int, set[str]] = {d: set() for d in depths}
    previous_modes: dict[int, set[str]] = {d: set() for d in depths}
    previous_mrca = None
    cumulative = 0.0
    for ix, tick in enumerate(ticks):
        current = proportions[tick]
        previous = proportions[ticks[ix - 1]] if ix else {}
        # Tick 0 is the observed starting state, not a transition from an
        # invented empty population. New components after it still compare
        # against an absent previous share of zero.
        qnn = (0.0 if ix == 0 else
               sum(max(0.0, p - previous.get(h, 0.0)) ** 2 for h, p in current.items()))
        cumulative += qnn
        alive = org_by_tick[tick]
        tips = alive["id"].to_numpy().astype(np.int32, copy=False)
        sampled = ix % every == 0
        tm = _tree_metrics(tips, gen, born, tin, tout, up) if sampled else None
        if tm is not None:
            mrca_changed = previous_mrca is not None and tm["mrca_id"] != previous_mrca
            previous_mrca = tm["mrca_id"]
        else:
            mrca_changed = None
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
        row = dict(tick=tick, qnn=qnn, qnn_cum=cumulative, n_func=len(current),
                   top_func_share=max(current.values(), default=0.0), pop=alive.height,
                   rep_alive=(sum(classes.get(h) == "replicator" for h in hashes)
                              if run.classes is not None else None),
                   len_med=float(alive["len"].median()) if alive.height else None,
                   mrca_gen=tm["mrca_gen"] if tm else None, mrca_tick=tm["mrca_tick"] if tm else None,
                   mrca_changed=mrca_changed,
                   ancestor_count=tm["ancestor_count"] if tm else None,
                   mpd=tm["mpd"] if tm else None, spd=tm["spd"] if tm else None,
                   mean_ed=tm["mean_ed"] if tm else None,
                   parasite_share=None, entered_share=None)
        for d in depths:
            f = set(persistent_components[d])
            row[f"change_{d}"] = len(f - previous_modes[d])
            row[f"novelty_{d}"] = len(f - seen_components[d])
            seen_components[d] |= f
            previous_modes[d] = f
            counts = {}
            for c in persistent_components[d]:
                counts[c] = counts.get(c, 0) + 1
            n = sum(counts.values())
            row[f"ecology_{d}"] = -sum((v / n) * math.log2(v / n) for v in counts.values()) if n else 0.0
            row[f"modes_censored_{d}"] = bool(
                max_depth < (max((int(gen[int(i)]) for i in tips_list), default=0) + d)
            )
        deepest = max(depths, default=0)
        row["modes_censored"] = bool(
            max_depth < (max((int(gen[int(i)]) for i in tips_list), default=0) + deepest)
        )
        if "exec_foreign" in alive.columns:
            row["foreign_share"] = float(alive["exec_foreign"].sum() / max(1, alive["executed"].sum()))
            if parasites is not None:
                row["parasite_share"] = float(
                    alive["birth_hash"].is_in(list(parasites)).mean()
                )
        if "exec_by_others" in alive.columns:
            row["entered_share"] = float((alive["exec_by_others"] > 0).mean())
        rows.append(row)
    return pl.DataFrame(rows) if rows else pl.DataFrame()


def compute(run: Run | str | Path, every: int = 1, depths: tuple[int, ...] = (187, 1870)) -> tuple[pl.DataFrame, dict]:
    """Compute per-census series and whole-run summary for an evo run."""
    if every < 1:
        raise ValueError("every must be at least 1")
    if not isinstance(run, Run):
        run = load(run)
    series = _series(run, every, depths)
    summary: dict = {}
    if series.height:
        summary = {
            "run": str(run.dir),
            "qnn_cum": float(series["qnn_cum"][-1]),
            "mrca_changes": int(series["mrca_changed"].sum()),
            "final_tick": int(series["tick"][-1]),
        }
        stationary_tree = series.filter(pl.col("tick") >= 25_000)
        for col in ("mpd", "mean_ed"):
            summary[f"mean_{col}"] = float(stationary_tree[col].mean()) if stationary_tree.height else None
        for d in depths:
            stationary_modes = series.filter(
                (pl.col("tick") >= 25_000) & pl.col(f"modes_censored_{d}").eq(False)
            )
            for name in ("change", "novelty", "ecology"):
                col = f"{name}_{d}"
                summary[f"mean_{col}"] = float(stationary_modes[col].mean()) if stationary_modes.height else None
        summary["mrca_tick"] = int(series["mrca_tick"][-1])
    return series, summary


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
    ap.add_argument("--knockout", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    depths = tuple(int(x) for x in a.depths.split(","))
    if a.knockout:
        run = load(a.run_dir)
        out = Path(a.out) if a.out else Path(a.run_dir) / "measures"
        out.mkdir(parents=True, exist_ok=True)
        for win, sites in site_entropy_windows(run).items():
            sites.write_csv(out / f"sites_{win}.csv")
        print("knockout columns require evo-core --neighbours/--neighbours-pad-only from task T03; entropy-only site rows were written where classes.csv was available.", file=sys.stderr)
        raise SystemExit(2)
    series, summary = compute(a.run_dir, a.every, depths)
    out = Path(a.out) if a.out else Path(a.run_dir) / "measures"
    out.mkdir(parents=True, exist_ok=True)
    series.write_csv(out / "series.csv")
    import json
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
