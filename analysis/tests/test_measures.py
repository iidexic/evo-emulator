"""Tests for measures.py (T05 §5, §4.1).

    uv run --project analysis --with pytest pytest analysis/tests/test_measures.py
"""
from pathlib import Path
import gzip
import json
import subprocess
import sys

import numpy as np
import polars as pl

ANALYSIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ANALYSIS))

from evo_run import Run, load
from measures import _euler, _tree, compute, site_entropy, spd_edge, spd_pairwise

# The E007 ancestor (absorb count 64 at byte 6, `lit A` at byte 5), two
# variants with the count at 96 and 112, and one whose guard byte is no
# longer a `lit` (the absorb read does not match it).
ANC = "13325271fc11401605086c5a1845486c11101c130d"
HI1 = ANC[:12] + "60" + ANC[14:]
HI2 = ANC[:12] + "70" + ANC[14:]
UNM = ANC[:10] + "12" + ANC[12:]
BODY = {"a": ANC, "h1": HI1, "h2": HI2, "u": UNM}


def write_run(d: Path, births: list[tuple], alive: dict[int, list[int]], body: dict[int, str],
              born: dict[int, int], gz: bool = False, injections: list | None = None) -> Path:
    """Write a run directory in the docs/instrumentation.md formats.

    `births` holds (tick, child, executor); `alive` maps census tick to the
    living ids; `body[id]` is a key of BODY (birth genome = current body);
    `born[id]` is the birth tick (founders and injected copies have no
    births row). Every birth is exact when child and executor share a body.
    """
    d.mkdir(parents=True, exist_ok=True)
    parent = {c: e for _, c, e in births}
    b = pl.DataFrame({
        "tick": [t for t, _, _ in births], "child": [c for _, c, _ in births],
        "executor": [e for _, _, e in births], "source": [e for _, _, e in births],
        "len": [len(BODY[body[c]]) // 2 for _, c, _ in births],
        "raw_hash": [body[c] for _, c, _ in births],
        "parent_hash": [body[e] for _, _, e in births],
        "parent_now_hash": [body[e] for _, _, e in births],
        "source_hash": [body[e] for _, _, e in births],
    }, schema_overrides={"tick": pl.Int64, "child": pl.Int64, "executor": pl.Int64,
                         "source": pl.Int64, "len": pl.Int64})
    rows = [dict(tick=t, id=i, parent=parent.get(i, 0), birth_tick=born[i],
                 len=len(BODY[body[i]]) // 2, birth_hash=body[i], now_hash=body[i],
                 executed=10, exec_foreign=0, exec_by_others=int(i % 2 == 0))
            for t, ids in alive.items() for i in ids]
    orgs = pl.DataFrame(rows)
    census = orgs.group_by("tick", "now_hash").agg(count=pl.len()).sort("tick", "now_hash")
    keys = sorted(set(body.values()))
    genomes = pl.DataFrame({"raw_hash": keys, "func_hash": [k.upper() for k in keys],
                            "len": [len(BODY[k]) // 2 for k in keys],
                            "bytes_hex": [BODY[k] for k in keys]})
    classes = pl.DataFrame({"raw_hash": keys, "class": ["replicator"] * len(keys)})
    deaths = pl.DataFrame({"tick": [1], "id": [999], "birth_hash": [keys[0]],
                           "executed": [0], "exec_foreign": [0], "exec_by_others": [0]})
    patches = pl.DataFrame({"tick": sorted(alive), "patch": [0] * len(alive)})
    frames = dict(births=b, deaths=deaths, census=census, orgs=orgs, patches=patches,
                  genomes=genomes, classes=classes)
    for name, df in frames.items():
        p = d / f"{name}.csv"
        df.write_csv(p)
        if gz:
            with open(p, "rb") as fi, gzip.open(d / f"{name}.csv.gz", "wb") as fo:
                fo.write(fi.read())
            p.unlink()
    (d / "meta.json").write_text(json.dumps({"census_every": 1, "injections": injections or []}))
    return d


# Single founder 1. Generation 1: 2, 3 (tick 1). Generation 2: 4, 5 from
# 2 and 6 from 3 (tick 2). Generation 3: 7 from 4, 8 from 5 (tick 3).
ONE_BIRTHS = [(1, 2, 1), (1, 3, 1), (2, 4, 2), (2, 5, 2), (2, 6, 3), (3, 7, 4), (3, 8, 5)]
ONE_ALIVE = {1: [1, 2, 3], 2: [2, 3, 4, 5, 6], 3: [2, 4, 7, 8]}
ONE_BODY = {1: "a", 2: "a", 3: "a", 4: "h1", 5: "h2", 6: "a", 7: "h1", 8: "u"}
ONE_BORN = {1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3}


def one_founder(d: Path, **kw) -> Path:
    return write_run(d, ONE_BIRTHS, ONE_ALIVE, ONE_BODY, ONE_BORN, **kw)


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ANALYSIS / "measures.py"), *map(str, args)],
                          capture_output=True, text=True, cwd=ANALYSIS)


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


def test_every_k_with_last_census_unsampled(tmp_path):
    # Two censuses, every=2: the last one has no tree columns.
    series, summary = compute(tiny_run(tmp_path), every=2, depths=(1, 2))
    assert series["mrca_tick"].to_list() == [0, None]
    assert summary["mrca_tick"] == 0
    assert summary["mrca_changes"] == 0


def test_cli_knockout_writes_normal_output_and_sites(tmp_path):
    run = one_founder(tmp_path / "run")
    out = tmp_path / "out"
    res = run_cli(run, "--every", "2", "--knockout", "--depths", "1,2", "--out", out)
    assert res.returncode == 0, res.stderr
    series = pl.read_csv(out / "series.csv")
    assert series["tick"].to_list() == [1, 2, 3]
    summary = json.loads((out / "summary.json").read_text())
    assert summary["final_tick"] == 3
    assert list(out.glob("sites_*.csv"))
