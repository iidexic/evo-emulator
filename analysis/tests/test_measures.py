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


def test_single_founder_living_ancestors_stem_free_ed_and_mrca_change(tmp_path):
    # Tips: t1 {1, 2, 3}; t2 {2, 3, 4, 5, 6}; t3 {2, 4, 7, 8}. The MRCA is
    # a real organism throughout (1, 1, then 2), living at t1 and t3.
    series, summary = compute(load(one_founder(tmp_path)), depths=(1, 5))
    t1, t2, t3 = series.iter_rows(named=True)
    assert (t1["mrca_gen"], t1["mrca_tick"]) == (0, 0)
    assert (t2["mrca_gen"], t2["mrca_tick"]) == (0, 0)
    assert (t3["mrca_gen"], t3["mrca_tick"]) == (1, 1)
    assert summary["mrca_changes"] == 1 and summary["mrca_tick"] == 1
    # Induced trees. t1: 1 -> {2, 3}. t2: 1 -> {2, 3}, 2 -> {4, 5}, 3 -> {6}.
    # t3: 2 -> {4, 8 (through 5, stripped)}, 4 -> {7}.
    # Internal nodes (branch points): t1 the living 1; t2 the dead 1 and the
    # living 2 (3 has one line, through 6); t3 the living 2 (4 has one
    # line, through 7, and is a unifurcation like 5).
    assert [r["ancestor_count"] for r in (t1, t2, t3)] == [1, 2, 1]
    # Pair distances (generations through the LCA). t1: 1+1+2. t2: (2,3) 2,
    # (2,4) 1, (2,5) 1, (2,6) 3, (3,4) 3, (3,5) 3, (3,6) 1, (4,5) 2, (4,6) 4,
    # (5,6) 4. t3: (2,4) 1, (2,7) 2, (2,8) 2, (4,7) 1, (4,8) 3, (7,8) 4.
    assert [r["spd"] for r in (t1, t2, t3)] == [4, 24, 13]
    assert np.isclose(t1["mpd"], 4 / 3) and np.isclose(t2["mpd"], 2.4) and np.isclose(t3["mpd"], 13 / 6)
    # Fair-proportion ED below the MRCA (the stem to the virtual root is
    # dropped). t1: 0, 1, 1. t2: 2 1/3, 3 1/2, 4 and 5 1 + 1/3, 6 1 + 1/2.
    # t3: 2 0, 4 1/2, 7 1 + 1/2, 8 2. With the stem t3 would be 1.5.
    assert np.isclose(t1["mean_ed"], 2 / 3)
    assert np.isclose(t2["mean_ed"], 1.0)
    assert np.isclose(t3["mean_ed"], 1.0)
    # Depth 5 is beyond the run's deepest generation (3): censored.
    assert series["change_5"].null_count() == 3 and series["ecology_5"].null_count() == 3
    assert series["modes_censored_5"].to_list() == [True, True, True]
    assert summary["max_gen"] == 3
    assert summary["mean_change_5"] == "censored" and "5" in summary["censored_depths"]
    assert summary["mean_change_1"] is None  # no census at or after 25,000


def test_modes_censored_is_held_once_set(tmp_path):
    # Depth 1, deepest generation 3. t3's tips reach generation 3, so 3 < 3
    # + 1 censors it; at t4 only generation 1 is alive (3 >= 1 + 1), and the
    # flag stays set.
    alive = {**ONE_ALIVE, 4: [2]}
    run = write_run(tmp_path, ONE_BIRTHS, alive, ONE_BODY, ONE_BORN)
    series, _ = compute(load(run), depths=(1,))
    assert series["modes_censored_1"].to_list() == [False, False, True, True]
    assert series["modes_censored"].to_list() == [False, False, True, True]


def test_injected_lines_are_left_out_of_mrca_changes(tmp_path):
    # Id 9, an injected copy at tick 2, alive at t2 only. The MRCA of all
    # tips is the virtual root at t2; the sweep counter follows the
    # founder's line (1, 1, 2) and counts one change, not two.
    alive = {1: [1, 2, 3], 2: [2, 3, 4, 5, 6, 9], 3: [2, 4, 7, 8]}
    body, born = {**ONE_BODY, 9: "a"}, {**ONE_BORN, 9: 2}
    inj = [{"tick": 2, "hex": ANC, "count": 1, "starts": [0]}]
    series, summary = compute(load(write_run(tmp_path / "inj", ONE_BIRTHS, alive, body, born,
                                             injections=inj)), depths=(1,))
    assert series["mrca_gen"].to_list() == [0, -1, 1]
    assert series["mrca_changed"].to_list() == [False, False, True]
    assert summary["mrca_changes"] == 1
    # The same run without `injections` in meta.json: id 9 is a second line
    # and both MRCA moves count.
    _, plain = compute(load(write_run(tmp_path / "plain", ONE_BIRTHS, alive, body, born)), depths=(1,))
    assert plain["mrca_changes"] == 2


def parasite_run(d: Path, world_class: str | None) -> Run:
    # Founder 2 carries genome p; five exact births of p in a chain (3..7),
    # so p's exact-birth generation depth is 5. Founder 8 carries r. Every
    # p carrier ran half its instructions in foreign bytes.
    d.mkdir(parents=True, exist_ok=True)
    if world_class is not None:
        pl.DataFrame({"raw_hash": ["p", "r"], "class": [world_class, "replicator"]}).write_csv(
            d / "classes_world.csv")
    births = pl.DataFrame({"tick": [1, 2, 3, 4, 5], "child": [3, 4, 5, 6, 7],
                           "executor": [2, 3, 4, 5, 6], "raw_hash": ["p"] * 5,
                           "parent_now_hash": ["p"] * 5, "len": [21] * 5})
    orgs = pl.DataFrame({"tick": [10, 10, 10], "id": [6, 7, 8], "parent": [5, 6, 0],
                         "birth_tick": [4, 5, 0], "birth_hash": ["p", "p", "r"], "len": [21] * 3,
                         "executed": [10, 10, 10], "exec_foreign": [5, 5, 0],
                         "exec_by_others": [1, 0, 1]})
    deaths = pl.DataFrame({"tick": [6, 6, 7, 8], "id": [2, 3, 4, 5], "birth_hash": ["p"] * 4,
                           "executed": [10] * 4, "exec_foreign": [5] * 4})
    census = pl.DataFrame({"tick": [10, 10], "now_hash": ["p", "r"], "count": [2, 1]})
    genomes = pl.DataFrame({"raw_hash": ["p", "r"], "func_hash": ["P", "R"]})
    classes = pl.DataFrame({"raw_hash": ["p", "r"], "class": ["one_shot", "replicator"]})
    patches = pl.DataFrame({"tick": [10], "patch": [0]})
    return Run(d, {}, births, deaths, census, orgs, patches, genomes, classes)


def test_parasite_share_applies_e005_world_class_and_entered_share_is_over_replicators(tmp_path):
    rows = {}
    for wc in ("one_shot", "replicator", None):
        series, _ = compute(parasite_run(tmp_path / str(wc), wc), depths=(1,))
        rows[wc] = series.row(0, named=True)
    # p passes E005's test only when its world class is not replicator.
    assert np.isclose(rows["one_shot"]["parasite_share"], 2 / 3)
    assert rows["replicator"]["parasite_share"] == 0.0
    assert rows[None]["parasite_share"] is None  # no classes_world.csv
    # Entered share over replicator-class bodies (by birth hash): only 8,
    # which was entered; over all bodies it would be 2/3.
    assert rows["one_shot"]["entered_share"] == 1.0
    assert rows["one_shot"]["rep_alive"] == 1
