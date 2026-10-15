"""T05's build of _tree, _lca, _tree_metrics, _euler and _persistence at commit 224fc7e, kept unchanged as the reference for T09."""
from __future__ import annotations

import numpy as np


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
