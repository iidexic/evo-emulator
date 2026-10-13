from pathlib import Path
import sys

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evo_run import Run
from measures import _euler, _tree, compute, site_entropy, spd_edge, spd_pairwise


def tiny_run(tmp_path: Path) -> Run:
    # Three generations: founders 1/2; children 3/4; grandchildren 5/6.
    births = pl.DataFrame({"tick": [1, 1, 2, 2], "child": [3, 4, 5, 6],
                           "executor": [1, 2, 3, 4]})
    census = pl.DataFrame({"tick": [1, 1, 2, 2], "now_hash": ["a", "c", "b", "d"],
                           "count": [1, 1, 1, 1]})
    orgs = pl.DataFrame({"tick": [1, 1, 2, 2], "id": [1, 2, 3, 4],
                         "parent": [0, 0, 1, 2], "birth_tick": [0, 0, 1, 1],
                         "birth_hash": ["a", "c", "b", "d"], "len": [4, 1, 4, 1],
                         "executed": [0, 0, 0, 0], "exec_foreign": [0, 0, 0, 0]})
    genomes = pl.DataFrame({"raw_hash": ["a", "b", "c", "d", "e", "f"],
                            "func_hash": ["A", "B", "C", "D", "E", "F"]})
    classes = pl.DataFrame({"raw_hash": ["a", "b", "c", "d", "e", "f"],
                            "class": ["replicator"] * 6})
    empty = pl.DataFrame()
    return Run(tmp_path, {}, births, empty, census, orgs, empty, genomes, classes)


def test_hand_calculated_forest_measures_and_qnn(tmp_path):
    series, summary = compute(tiny_run(tmp_path), depths=(1, 2))
    t1, t2 = series.iter_rows(named=True)

    # Tick 1 has the two founders as tips; virtual root is their MRCA.
    assert (t1["mrca_gen"], t1["mrca_tick"]) == (-1, 0)
    assert t1["ancestor_count"] == 1
    assert t1["spd"] == 2
    assert t1["mpd"] == 2.0
    assert t1["mean_ed"] == 1.0

    # At tick 2, the two generation-1 children descend from different
    # founders. Each path to the virtual root has length 2.
    assert (t2["mrca_gen"], t2["mrca_tick"]) == (-1, 0)
    assert t2["ancestor_count"] == 1
    assert t2["spd"] == 4
    assert t2["mpd"] == 4.0
    assert t2["mean_ed"] == 2.0

    # Tick 1 is the starting state, so it has no change. Tick 2 replaces
    # both equally common functions with two new equally common functions.
    assert t1["qnn"] == 0
    assert t1["qnn_cum"] == 0
    assert t2["qnn"] == 0.5
    assert t2["qnn_cum"] == 0.5
    assert (t1["n_func"], t2["n_func"]) == (2, 2)
    assert (t1["top_func_share"], t2["top_func_share"]) == (0.5, 0.5)

    # At t1 each founder is persistent at both depths (descendants reach
    # generation 2). At t2, the children are persistent only at depth 1.
    for d in (1, 2):
        assert t1[f"change_{d}"] == 2
        assert t1[f"novelty_{d}"] == 2
        assert t1[f"ecology_{d}"] == 1.0
    assert (t2["change_1"], t2["novelty_1"], t2["ecology_1"]) == (2, 2, 1.0)
    assert (t2["change_2"], t2["novelty_2"], t2["ecology_2"]) == (0, 0, 0.0)
    assert t1["modes_censored"] is False
    assert t2["modes_censored"] is True
    assert summary["mrca_changes"] == 0


def test_spd_methods_agree_on_random_500_tip_tree():
    rng = np.random.default_rng(9217)
    n = 1800
    parent = np.zeros(n, dtype=np.int32)
    depth = np.zeros(n, dtype=np.int32)
    parent[1] = 0
    for node in range(2, n):
        parent[node] = rng.integers(1, node)
        depth[node] = depth[parent[node]] + 1
    levels = int(depth.max()).bit_length() + 1
    up = [parent]
    for _ in range(1, levels):
        up.append(up[-1][up[-1]])
    tips = rng.choice(np.arange(1, n), size=500, replace=False)
    assert spd_edge(tips, parent, depth) == spd_pairwise(tips, depth, up)


def test_site_entropy_counts_births_and_returns_bits():
    got = site_entropy([bytes([0, 4]), bytes([1, 4]), bytes([1, 4])])
    assert np.isclose(got[0], -(1 / 3) * np.log2(1 / 3) - (2 / 3) * np.log2(2 / 3))
    assert got[1] == 0
