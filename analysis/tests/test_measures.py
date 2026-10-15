"""Tests for measures.py (T05 §5, §4.1).

    uv run --project analysis --with pytest pytest analysis/tests/test_measures.py
"""
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
import gzip
import json
import subprocess
import sys

import numpy as np
import polars as pl
import pytest

ANALYSIS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ANALYSIS))
sys.path.insert(0, str(ANALYSIS / "tests"))  # measures_ref

from evo_run import Run, load
from measures import (_euler, _persistence, _tree, _tree_metrics, absorb_class, compute, evo_bin,
                      is_meaningful, knockout, knockout_windows, merge_knockout, parse_args,
                      qnn_series, read_neighbours, site_entropy, site_windows, sites_relation,
                      spd_edge, spd_pairwise)
import measures_baseline
import measures_ref

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
    # Calls the engine: $EVO_BIN, else evo-core/target/release; skipped
    # without one.
    try:
        exe = evo_bin()
    except FileNotFoundError as e:
        pytest.skip(str(e))
    run = one_founder(tmp_path / "run")
    out = tmp_path / "out"
    res = run_cli(run, "--every", "2", "--knockout", "--evo-bin", exe, "--depths", "1,2", "--out", out)
    assert res.returncode == 0, res.stderr
    series = pl.read_csv(out / "series.csv")
    assert series["tick"].to_list() == [1, 2, 3]
    summary = json.loads((out / "summary.json").read_text())
    assert summary["final_tick"] == 3
    # One window; its top body is the ancestor (3 exact births of `a`).
    sites = pl.read_csv(out / "sites_1.csv")
    assert sites.columns == ["pos", "op", "entropy", "exact_pad", "class_pad", "meaningful"]
    assert sites.height == 21 and sites.null_count().row(0) == (0,) * 6
    rec = summary["sites"]["1"]
    assert rec["hex"] == ANC and rec["exact_births_window"] == 3 and rec["class_alone"] == "replicator"
    assert rec["meaningful"] == int(sites["meaningful"].sum())
    assert summary["sites_harness"]["harness_ticks"] == 3000


NB_HEADER = ("pos,kind,byte,hex,raw_hash,func_hash,class_alone,births_alone,exact_alone,alive_alone,"
             "births_host,exact_host,host_copies,host_exact,alive_host,host_alive,executed,exec_foreign,"
             "entry_off,ticks_run,label")


def nb_csv(rows: list[tuple]) -> str:
    """A --neighbours CSV (T03 §2 header) from (pos, kind, byte, class_alone,
    exact_alone) tuples; the other columns are filler, hashes all digits."""
    lines = [NB_HEADER]
    for pos, kind, byte, cls, exact in rows:
        lines.append(f"{pos},{kind},{'' if byte is None else byte},00,{1000 + pos:016d},{2000 + pos:016d},"
                     f"{cls},{exact},{exact},true,0,0,0,0,true,true,10,0,-1,3000,{cls}")
    return "\n".join(lines) + "\n"


def test_meaningful_rule():
    # Below half the unmutated body's exact births alone, or the class changed.
    assert not is_meaningful(100, "replicator", 100, "replicator")
    assert not is_meaningful(50, "replicator", 100, "replicator")   # exactly half: not below
    assert is_meaningful(49, "replicator", 100, "replicator")
    assert is_meaningful(120, "inexact", 100, "replicator")          # more births, other class
    assert is_meaningful(0, "dies", 100, "replicator")
    assert not is_meaningful(0, "loafer", 0, "loafer")


def test_merge_of_a_neighbours_csv_into_the_sites_frame(tmp_path):
    p = tmp_path / "neighbours.csv"
    # Pad rows out of order, plus a substitution by 5 and a deletion that the
    # merge must leave out.
    p.write_text(nb_csv([(2, "sub", 0, "replicator", 49), (0, "sub", 0, "replicator", 100),
                         (1, "sub", 0, "replicator", 50), (3, "sub", 0, "inexact", 120),
                         (1, "sub", 5, "dies", 0), (2, "del", None, "dies", 0)]))
    nb = read_neighbours(p)
    assert nb["raw_hash"].dtype == pl.Utf8 and nb["raw_hash"][0] == "0000000000001002"
    assert nb["byte"].to_list()[-1] is None
    sites = pl.DataFrame({"pos": [0, 1, 2, 3], "op": ["19", "operand", "18", "5"],
                          "entropy": [0.0, 0.5, 0.0, 0.1], "exact_pad": [None] * 4,
                          "class_pad": [None] * 4, "meaningful": [None] * 4})
    got = merge_knockout(sites, nb, dict(exact_alone=100, class_alone="replicator"))
    assert got.columns == ["pos", "op", "entropy", "exact_pad", "class_pad", "meaningful"]
    assert got["exact_pad"].to_list() == [100, 50, 49, 120]
    assert got["class_pad"].to_list() == ["replicator", "replicator", "replicator", "inexact"]
    assert got["meaningful"].to_list() == [False, False, True, True]
    assert got["op"].to_list() == ["19", "operand", "18", "5"]
    rel = sites_relation(got)
    # Entropy ranks 1.5, 4, 1.5, 3 against meaningful ranks 1.5, 1.5, 3.5,
    # 3.5: rho = -1 / sqrt(4.5 * 4).
    assert (rel["positions"], rel["meaningful"]) == (4, 2)
    assert np.isclose(rel["entropy_meaningful"], 0.05) and np.isclose(rel["entropy_other"], 0.25)
    assert np.isclose(rel["spearman"], -1 / np.sqrt(18))
    # Meaningful 0.0, 0.1 against other 0.0, 0.5: pairs tie, below, above,
    # below.
    assert rel["auc"] == 0.625
    with pytest.raises(ValueError):
        merge_knockout(sites, nb.filter(pl.col("pos") != 3), dict(exact_alone=100, class_alone="replicator"))


def fake_engine(calls: list, dead: set[int]):
    """A stand-in for subprocess.run: `--classify` writes a replicator with
    230 exact births; `--neighbours` writes a pad row per position of the
    body, `dies` at the positions in `dead`, the body's result elsewhere."""
    def run(cmd, **kw):
        calls.append(cmd)
        if "--classify" in cmd:
            d = Path(cmd[cmd.index("--classify") + 1])
            assert (d / "genomes.csv").read_text().splitlines()[0] == "raw_hash,bytes_hex"
            (d / "classes.csv").write_text(
                "raw_hash,class,births,exact_births,first_birth_tick,alive,final_energy_m,executed,absorbs\n"
                "base,replicator,231,230,14,true,1,1,1\n")
        else:
            n = len(cmd[cmd.index("--neighbours") + 1]) // 2
            Path(cmd[cmd.index("--neighbours-out") + 1]).write_text(nb_csv(
                [(p, "sub", 0, "dies" if p in dead else "replicator", 0 if p in dead else 230)
                 for p in range(n)]))
        return SimpleNamespace(returncode=0, stderr="")
    return run


def test_knockout_calls_classify_and_pad_only_neighbours_with_the_flags():
    calls = []
    base, nb = knockout(ANC, "evo", 1234, ["--sun", "2"], runner=fake_engine(calls, {0}))
    assert base == dict(class_alone="replicator", births_alone=231, exact_alone=230)
    assert nb.height == 21 and nb["exact_alone"][0] == 0
    cls, nbr = calls
    assert cls[:2] == ["evo", "--classify"] and cls[3:] == ["--harness-ticks", "1234", "--sun", "2"]
    assert nbr[:4] == ["evo", "--neighbours", ANC, "--neighbours-pad-only"]
    assert nbr[4] == "--neighbours-out" and nbr[6:] == ["--harness-ticks", "1234", "--sun", "2"]


def test_knockout_windows_on_a_tiny_run_with_a_fake_engine(tmp_path):
    run = load(one_founder(tmp_path))
    sw = site_windows(run)
    assert list(sw) == [1] and sw[1].hex == ANC and sw[1].exact_births == 3
    # Entropy over the four same-length exact births (a a a h1): byte 6 only.
    ent = sw[1].sites["entropy"].to_list()
    assert np.isclose(ent[6], -(0.75 * np.log2(0.75) + 0.25 * np.log2(0.25)))
    assert sum(ent) == ent[6] and sw[1].bodies == 4
    calls = []
    frames, record = knockout_windows(run, "evo", runner=fake_engine(calls, {6, 7}))
    assert frames[1]["meaningful"].to_list() == [p in (6, 7) for p in range(21)]
    rec = record["1"]
    assert (rec["meaningful"], rec["positions"], rec["exact_alone"]) == (2, 21, 230)
    assert rec["spearman"] > 0  # the varying site is a meaningful one here
    assert len(calls) == 2


def test_evo_flags_take_a_lone_flag_value():
    a = parse_args(["RUN", "--knockout", "--evo-flags", "--legacy-pending-range", "--harness-ticks", "500"])
    assert a.evo_flags == ["--legacy-pending-range"] and a.harness_ticks == 500 and a.knockout
    assert parse_args(["RUN", "--evo-flags", "--sun 2 --no-protect"]).evo_flags == ["--sun", "2", "--no-protect"]
    assert parse_args(["RUN"]).evo_flags == []


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
        series, summary = compute(parasite_run(tmp_path / str(wc), wc), depths=(1,))
        rows[wc] = series.row(0, named=True)
        # The one census is at tick 10, before the stationary phase.
        assert summary["mean_parasite_share"] is None and summary["mean_rep_alive"] is None
    # p passes E005's test only when its world class is not replicator.
    assert np.isclose(rows["one_shot"]["parasite_share"], 2 / 3)
    assert rows["replicator"]["parasite_share"] == 0.0
    assert rows[None]["parasite_share"] is None  # no classes_world.csv
    # Entered share over replicator-class bodies (by birth hash): only 8,
    # which was entered; over all bodies it would be 2/3.
    assert rows["one_shot"]["entered_share"] == 1.0
    assert rows["one_shot"]["rep_alive"] == 1


def test_root_lines_and_qnn_over_absorb_class_by_hand(tmp_path):
    run = load(one_founder(tmp_path))
    series, summary = compute(run, depths=(1,), group="absorb_class")
    # Children of the MRCA with living descendants: t1 and t2 2 and 3 under
    # 1; t3 4 and 5 (through 8) under 2.
    assert series["root_lines"].to_list() == [2, 2, 2]
    assert summary["root_lines"] == 2 and summary["group"] == "absorb_class"
    # Bodies: t1 a a a; t2 a a h1 h2 a; t3 a h1 h1 u. By absorb class
    # (lt96, ge96, unmatched): t1 1/0/0, t2 .6/.4/0, t3 .25/.5/.25.
    assert np.allclose(series["qnn"].to_list(), [0.0, 0.4 ** 2, 0.1 ** 2 + 0.25 ** 2])
    assert series["n_func"].to_list() == [1, 2, 3]
    assert np.allclose(series["top_func_share"].to_list(), [1.0, 0.6, 0.5])
    assert np.allclose(series["absorb_ge96_share"].to_list(), [0.0, 0.4, 2 / 3])
    assert np.allclose(series["absorb_unmatched_share"].to_list(), [0.0, 0.0, 0.25])
    # By func_hash h1 and h2 are apart: t2 .6/.2/.2, t3 a .25, h1 .5, u .25.
    by_func = qnn_series(run)
    assert np.allclose(by_func["qnn"].to_list(), [0.0, 2 * 0.2 ** 2, 0.3 ** 2 + 0.25 ** 2])
    assert "absorb_ge96_share" not in by_func.columns


def test_absorb_class_follows_traits_absorb_read():
    bodies = {"anc": ANC, "h1": HI1, "h2": HI2, "guard": UNM,
              "long": ANC + "00",                    # 22 bytes: not read
              "neg": ANC[:12] + "8e" + ANC[14:],     # -114, read as encoded
              "x95": ANC[:12] + "5f" + ANC[14:]}
    g = pl.DataFrame({"raw_hash": list(bodies), "bytes_hex": list(bodies.values())})
    got = dict(absorb_class(g).iter_rows())
    assert got == {"anc": "lt96", "h1": "ge96", "h2": "ge96", "guard": "unmatched",
                   "long": "unmatched", "neg": "lt96", "x95": "lt96"}


def test_tree_metrics_match_a_pairwise_loop_on_a_random_500_tip_tree():
    rng = np.random.default_rng(9217)
    n = 1800
    parent = np.zeros(n, dtype=np.int32)
    depth = np.zeros(n, dtype=np.int32)
    for node in range(2, n):
        parent[node] = rng.integers(1, node)
        depth[node] = depth[parent[node]] + 1
    up = [parent]
    for _ in range(1, int(depth.max()).bit_length() + 1):
        up.append(up[-1][up[-1]])
    tin, tout = _euler(parent, depth)
    tips = sorted(map(int, rng.choice(np.arange(1, n), size=500, replace=False)))
    tm = _tree_metrics(np.array(tips), depth, np.zeros(n, dtype=np.int32), tin, tout, up)

    def path(x):
        out = []
        while x:
            out.append(x)
            x = int(parent[x])
        return out
    paths = {t: path(t) for t in tips}
    sets = {t: set(p) for t, p in paths.items()}
    m = len(tips)
    dist = np.zeros((m, m))
    for i in range(m):
        for j in range(i + 1, m):
            lca = max(int(depth[c]) for c in sets[tips[i]] & sets[tips[j]])
            dist[i, j] = dist[j, i] = depth[tips[i]] + depth[tips[j]] - 2 * lca
    upper = dist[np.triu_indices(m, 1)]
    assert tm["spd"] == int(upper.sum())
    assert np.isclose(tm["mpd"], upper.mean())
    # MRCA, fair-proportion ED below it, branch points, root lines.
    common = set.intersection(*sets.values())
    mrca = max(common, key=lambda x: int(depth[x]))
    assert tm["mrca_id"] == mrca
    below: dict[int, int] = {}
    for t in tips:
        for x in paths[t]:
            below[x] = below.get(x, 0) + 1
    ed = [sum(1 / below[x] for x in paths[t] if x not in common) for t in tips]
    assert np.isclose(tm["mean_ed"], np.mean(ed))
    kids: dict[int, set] = {}
    for t in tips:
        for x in paths[t]:
            kids.setdefault(int(parent[x]), set()).add(x)
    assert tm["ancestor_count"] == sum(1 for c in kids.values() if len(c) >= 2)
    assert tm["root_lines"] == len(kids[mrca])
    assert any(t in kids for t in tips)  # living ancestors among the tips


def test_gz_input_and_cli_summary_with_group(tmp_path):
    plain, _ = compute(load(one_founder(tmp_path / "plain")), depths=(1,), group="absorb_class")
    gz_dir = one_founder(tmp_path / "gz", gz=True)
    assert not list(gz_dir.glob("*.csv")) and list(gz_dir.glob("*.csv.gz"))
    gz, _ = compute(load(gz_dir), depths=(1,), group="absorb_class")
    assert gz.equals(plain)
    out = tmp_path / "out"
    res = run_cli(gz_dir, "--group", "absorb_class", "--every", "2", "--depths", "1,5", "--out", out)
    assert res.returncode == 0, res.stderr
    summary = json.loads((out / "summary.json").read_text())
    # Censuses t1 and t3 are sampled (every 2): MRCA 1, then 2.
    assert summary["group"] == "absorb_class"
    assert (summary["mrca_tick"], summary["mrca_gen"], summary["root_lines"]) == (1, 1, 2)
    assert summary["mrca_changes"] == 1
    assert summary["max_gen"] == 3 and summary["mean_change_5"] == "censored"
    series = pl.read_csv(out / "series.csv")
    assert series["root_lines"].to_list() == [2, None, 2]
    assert np.allclose(series["absorb_ge96_share"].to_list(), [0.0, 0.4, 2 / 3])


def test_sweep_check_window_and_ratio():
    absorb = pl.DataFrame({
        "tick": [0, 2500, 3000, 3500, 4000, 25000, 25500],
        "qnn": [0.0, 0.5, 0.01, 0.09, 0.04, 0.001, 0.001],
        "absorb_ge96_share": [0.0, 0.2, 0.3, 0.6, 0.8, 0.8, 0.8]})
    got = measures_baseline.sweep_check(absorb)
    # The founder-phase 0.5 at 2,500 is excluded; the window is (2500, 4000].
    assert (got["sweep_peak_tick"], got["sweep_lo_tick"], got["sweep_hi_tick"]) == (3500, 2500, 4000)
    assert np.isclose(got["sweep_ratio"], 0.001 / 0.09) and got["c1"]
    late = absorb.with_columns(qnn=pl.Series([0.0, 0.5, 0.01, 0.02, 0.04, 0.1, 0.001]))
    assert not measures_baseline.sweep_check(late)["c1"]


def test_measures_baseline_on_a_tiny_synthetic_run(tmp_path):
    runs, out = tmp_path / "runs", tmp_path / "out"
    one_founder(runs / "lod" / "e007" / "s1")
    lines = measures_baseline.run_baseline(runs, out, seeds=2)
    text = (out / "summary.md").read_text(encoding="utf-8")
    assert text.splitlines() == lines
    assert "| e007 | std | 1 |" in text and "missing e007/std/s2" in text
    assert "absent on this machine" in text
    row = pl.read_csv(out / "runs.csv").row(0, named=True)
    assert (row["root_lines"], row["mrca_changes"], row["mrca_tick_max"]) == (2, 1, 1)
    assert row["c2_early"] and not row["c1"]  # no census after tick 2,500
    # Class columns: stationary means, none here (no census at or after
    # 25,000), and in the table.
    assert {"rep_alive", "parasite_share", "entered_share"} <= set(row) and row["rep_alive"] is None
    assert "| rep alive | parasite | entered |" in text
    assert pl.read_csv(out / "e007_series.csv").height == 3
    assert pl.read_csv(out / "e007_absorb_class_series.csv")["absorb_ge96_share"].to_list()[1] == 0.4


# T09: the numpy tree functions against T05's loops (tests/measures_ref.py).
FOREST_SEEDS = range(10)


@lru_cache(maxsize=None)
def forest(seed: int):
    """A Run-like random forest (T09 §4.2): 2-4 founders from id 2, then ids
    in sequence up to 20,000-50,000, each a birth from an earlier id (mostly
    a recent one, so lines run deep) or, for a few hundred, an injected copy
    with no births row. Births rows are shuffled; orgs rows over three
    census ticks hold every founder and injected copy and samples of the
    rest. Returns the run, T05's arrays for it, the founders, and the
    founders with the injected copies."""
    rng = np.random.default_rng(seed)
    founders = int(rng.integers(2, 5))
    size = int(rng.integers(20_000, 50_001))
    first = 2 + founders
    ids = np.arange(first, size)
    injected = np.zeros(size, dtype=bool)
    injected[rng.choice(ids, size=int(rng.integers(200, 400)), replace=False)] = True
    if seed % 2:
        injected[size - 1] = True  # the largest id has an orgs row only
    # Lines 600-1,000 generations deep (11 lifting levels; E016's std run
    # has 1,059 and 12).
    recent = ids - rng.geometric(0.15, size=ids.size)
    anywhere = 2 + (rng.random(ids.size) * (ids - 2)).astype(np.int64)
    executor = np.maximum(2, np.where(rng.random(ids.size) < 0.99, recent, anywhere))
    tick = ids // 10 + 1
    born = ~injected[ids]
    births = pl.DataFrame({"child": ids[born], "executor": executor[born], "tick": tick[born]}).sample(
        fraction=1.0, shuffle=True, seed=seed)
    parent = np.zeros(size, dtype=np.int64)
    parent[ids[born]] = executor[born]
    birth_tick = np.zeros(size, dtype=np.int64)
    birth_tick[ids] = tick
    roots = np.r_[np.arange(2, first), ids[~born]]
    rows = [roots] + [rng.choice(ids, size=2_000, replace=False) for _ in range(3)]
    org_ids = np.concatenate(rows)
    org_tick = np.concatenate([np.full(r.size, 1_000 * (i + 1)) for i, r in enumerate(rows)])
    orgs = pl.DataFrame({"tick": org_tick, "id": org_ids, "parent": parent[org_ids],
                         "birth_tick": birth_tick[org_ids]})
    run = SimpleNamespace(births=births, orgs=orgs)
    r_parent, r_depth, r_born, r_up = measures_ref._tree(run)
    r_tin, r_tout = measures_ref._euler(r_parent, r_depth)
    return run, (r_parent, r_depth, r_born, r_up, r_tin, r_tout), np.arange(2, first), roots


def test_tree_arrays_match_reference_on_random_forests():
    for seed in FOREST_SEEDS:
        run, (r_parent, r_depth, r_born, r_up, r_tin, r_tout), _, _ = forest(seed)
        parent, depth, born, up = _tree(run)
        assert np.array_equal(parent, r_parent) and np.array_equal(depth, r_depth)
        assert np.array_equal(born, r_born)
        assert len(up) == len(r_up) and all(np.array_equal(a, b) for a, b in zip(up, r_up))
        tin, tout = _euler(parent, depth)
        assert np.array_equal(tin, r_tin) and np.array_equal(tout, r_tout)
        # A depth that is not the tree's own: _euler finds the levels itself.
        tin0, tout0 = _euler(parent, np.zeros_like(depth))
        assert np.array_equal(tin0, r_tin) and np.array_equal(tout0, r_tout)
        assert np.array_equal(_persistence(run, depth), measures_ref._persistence(run, r_depth))


def test_tree_metrics_match_reference_on_random_tip_sets():
    rng = np.random.default_rng(4096)
    for seed in FOREST_SEEDS:
        run, (r_parent, r_depth, r_born, r_up, r_tin, r_tout), founders, roots = forest(seed)
        parent, depth, born, up = _tree(run)
        tin, tout = _euler(parent, depth)
        organisms = np.arange(2, len(parent))
        # A single lineage: the deepest id and its ancestors (each a living
        # ancestor of the next), and every third of them.
        x, chain = int(np.argmax(depth)), []
        while x:
            chain.append(x)
            x = int(parent[x])
        tip_sets = [np.zeros(0, dtype=np.int32), organisms[[rng.integers(organisms.size)]],
                    np.array(chain), np.array(chain[::3]),
                    founders, roots,  # roots: the founders and the injected copies
                    rng.choice(organisms, size=500, replace=True)]  # repeated ids
        tip_sets += [rng.choice(organisms, size=int(rng.integers(1, 3_001)), replace=False)
                     for _ in range(5)]
        for tips in tip_sets:
            got = _tree_metrics(tips, depth, born, tin, tout, up)
            want = measures_ref._tree_metrics(tips, r_depth, r_born, r_tin, r_tout, r_up)
            assert got.keys() == want.keys()
            for key, w in want.items():
                if isinstance(w, float):
                    assert got[key] == pytest.approx(w, rel=1e-9, abs=0), (seed, tips.size, key)
                else:
                    assert got[key] == w and type(got[key]) is type(w), (seed, tips.size, key)
