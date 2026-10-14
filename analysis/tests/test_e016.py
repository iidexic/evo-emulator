"""Tests for e016_defence.py: the defence rule, candidate selection, the tax
calibration arithmetic (T02 §4.2), the probe body, the replay snapshot tick,
the meta.json check, and the reading helpers. One engine call: the probe
parasite against the tierra ancestor (skipped without the binary).

    uv run --project analysis --with pytest pytest analysis/tests/test_e016.py
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import e016_defence as e  # noqa: E402
import lod  # noqa: E402
import measures  # noqa: E402

# The tierra ancestor in the harness at n0 and t50 (sun 2), 2026-10-13: b_alone 119; with the probe before it
# 119 exact births at n0 and 1 at t50 (the host starves), the probe 119 either way.
REF_N0 = e.Ref("replicator", 119, 119, 119)
REF_T50 = e.Ref("replicator", 119, 1, 119)


# ---- the defence rule (§1) ----------------------------------------------------------------

def test_immune_needs_the_probe_below_a_tenth_of_its_rate_on_the_ancestor():
    assert e.is_defence("replicator", 100, 100, 11, REF_N0) == (True, False)    # 11 < 11.9
    assert e.is_defence("replicator", 100, 100, 12, REF_N0) == (False, False)   # 12 >= 11.9
    assert e.is_defence("replicator", 100, 100, 0, REF_N0) == (True, False)


def test_tolerant_needs_its_own_rate_kept_and_above_the_ancestors_probed_rate():
    ref = e.Ref("replicator", 100, 50, 100)
    assert e.is_defence("replicator", 100, 90, 100, ref) == (False, True)   # 90 >= 0.9 x 100, 90 >= 1.2 x 50
    assert e.is_defence("replicator", 100, 89, 100, ref) == (False, False)  # below 0.9 of its own rate alone
    assert e.is_defence("replicator", 50, 59, 100, ref) == (False, False)   # keeps its rate, but 59 < 60
    assert e.is_defence("replicator", 50, 60, 100, ref) == (False, True)


def test_neither_without_replicator_class_alone_or_for_the_ancestor_itself():
    assert e.is_defence("inexact", 100, 100, 0, REF_N0) == (False, False)
    assert e.is_defence("one_shot", 1, 200, 0, REF_N0) == (False, False)
    # The ancestor against its own reference, at n0 and t50: neither kind.
    assert e.is_defence("replicator", 119, 119, 119, REF_N0) == (False, False)
    assert e.is_defence("replicator", 119, 1, 119, REF_T50) == (False, False)
    # Under t50 a host that keeps 108 of 119 while entered is tolerant (and both kinds can hold at once).
    assert e.is_defence("replicator", 119, 108, 119, REF_T50) == (False, True)
    assert e.is_defence("replicator", 119, 119, 3, REF_T50) == (True, True)


def test_apply_rule_adds_both_columns():
    df = pl.DataFrame({"class_alone": ["replicator", "replicator", "dies"], "b_alone": [119, 119, 0],
                       "b_probed": [1, 119, 0], "p_probed": [119, 5, 0]})
    out = e.apply_rule(df, REF_T50)
    assert out["immune"].to_list() == [False, True, False]
    assert out["tolerant"].to_list() == [False, True, False]


# ---- candidate selection (§3) --------------------------------------------------------------

def births(rows: list[tuple[int, str, str, str, int]]) -> pl.DataFrame:
    """(tick, raw_hash, func_hash, class, count) -> one exact-birth row per count."""
    out = [(t, r, f, c) for t, r, f, c, n in rows for _ in range(n)]
    return pl.DataFrame(out, schema={"tick": pl.Int64, "raw_hash": pl.Utf8, "func_hash": pl.Utf8, "class": pl.Utf8},
                        orient="row")


def test_candidates_by_window_share_and_by_run_count():
    ex = births([
        # Window 1 (ticks 1-25,000): 1,000 exact births.
        (100, "a1", "A", "replicator", 3), (25_000, "a2", "A", "replicator", 2),   # 5 = 0.5%: in
        (200, "b1", "B", "replicator", 4),                                         # 4 = 0.4%: out
        (300, "d1", "D", "parasite_jump", 200),                                    # not replicator: out
        (400, "f1", "F", "replicator", 791),                                       # in
        # Windows 2 and 3: 10,000 exact births each.
        (25_001, "c1", "C", "replicator", 25), (50_001, "c1", "C", "replicator", 25),  # 0.25% each, 50 in all: in
        (30_000, "e1", "E", "replicator", 24), (60_000, "e1", "E", "replicator", 25),  # 49 in all: out
        (30_000, "g1", "G", "replicator", 9_951), (60_000, "g1", "G", "replicator", 9_950),
    ])
    c = e.candidates(ex)
    assert c["func_hash"].to_list() == ["A", "C", "F", "G"]
    row = dict(zip(c["func_hash"], c.iter_rows(named=True)))
    assert row["A"]["raw_hash"] == "a1" and row["A"]["exact_births"] == 5
    assert row["A"]["max_window_share"] == pytest.approx(0.005)
    assert row["C"]["exact_births"] == 50 and row["C"]["max_window_share"] == pytest.approx(0.0025)


def test_candidate_body_tie_break_and_parasite_births_in_the_denominator():
    ex = births([(10, "x2", "X", "replicator", 2), (10, "x1", "X", "replicator", 2),
                 (10, "p", "P", "parasite_jump", 996)])
    assert e.candidates(ex).height == 0                # 4 of 1,000 with the parasite births counted: < 0.5%
    c = e.candidates(ex, share=0.004)
    assert c["raw_hash"].to_list() == ["x1"]           # tie on count: the smaller hash
    assert c["max_window_share"][0] == pytest.approx(0.004)
    assert e.candidates(ex.clear()).height == 0


# ---- tax calibration (T02 §4.2) --------------------------------------------------------------

def deaths(entered: list[int], lost: list[int], age: list[int]) -> pl.DataFrame:
    return pl.DataFrame({"exec_by_others": entered, "cycles_lost_m": lost, "age": age})


def test_tax_calibration_arithmetic():
    n0 = deaths([0, 0, 0, 5], [0, 0, 0, 0], [10, 10, 10, 10])        # F = 1/4
    t50 = deaths([3, 0, 0, 0, 1], [60_000, 0, 0, 0, 36_000], [200, 200, 200, 200, 200])
    c = e.tax_calibration(n0, t50)
    assert c["F"] == 0.25
    assert c["r"] == pytest.approx(96_000 / 1_000)                    # sum lost / sum age, entered or not
    assert c["P_exact"] == pytest.approx(100 * 96 / (0.25 * 32_000))  # 1.2
    assert c["P"] == 1
    assert c["F_t50"] == pytest.approx(0.4)                           # kept for the record, not used


def test_tax_rounds_halves_up_and_refuses_zero():
    n0 = deaths([1, 0, 0, 0], [0] * 4, [1] * 4)
    assert e.tax_calibration(n0, deaths([1], [200_000], [1_000]))["P"] == 3   # P_exact = 2.5
    assert e.tax_calibration(n0, deaths([1], [1_000_000], [1]))["P"] == 100   # clamped
    with pytest.raises(SystemExit):
        e.tax_calibration(n0, deaths([1], [100], [1_000]))                   # P_exact 0.125 -> 0
    with pytest.raises(SystemExit):
        e.tax_calibration(deaths([0, 0], [0, 0], [1, 1]), deaths([1], [100], [1]))  # nothing entered in n0


# ---- the probe and the replay tick -------------------------------------------------------------

def test_tierra_probe_flips_byte_18_from_nop1_to_nop0_and_nothing_else():
    anc, probe = bytes.fromhex(e.HEX["tierra"]), bytes.fromhex(e.PROBE["tierra"])
    assert len(anc) == len(probe) == 41
    assert [i for i in range(41) if anc[i] != probe[i]] == [18]
    assert (anc[18], probe[18]) == (e.NOP1, e.NOP0)
    assert e.PROBE["tierra"] == "0101030351fc117f1605084c0a010301036d010103011332525a71fc1845486c11101c0b030301016d"
    assert e.PROBE["std"] == "00"
    with pytest.raises(ValueError):
        e.probe_hex(e.HEX["std"])


def test_snapshot_tick_is_the_last_multiple_of_25000_below_t():
    assert e.snapshot_tick(25_001) == 25_000
    assert e.snapshot_tick(50_000) == 25_000      # below, not at
    assert e.snapshot_tick(50_001) == 50_000
    assert e.snapshot_tick(249_999) == 225_000
    assert e.snapshot_tick(25_000) is None        # no snapshot at tick 0
    assert e.snapshot_tick(1) is None


# ---- meta.json ----------------------------------------------------------------------------------

def good_meta(arm: str = "tierra_t50") -> dict:
    b = e.base(arm)
    return {
        "ticks_requested": 250_000, "ticks_run": 250_000, "ancestor": b, "founders": [{"hex": e.HEX[b], "count": 1}],
        "founder_starts": [32_768], "state_every": 25_000, "replay_from": None,
        "config": {"patch_income": 512_000, "patch_cap": 8_192_000, "legacy_pending_range": False,
                   "cycle_theft_pct": 50 if arm.endswith("t50") else 0,
                   "cycle_tax_pct": 0, "cycle_tax_frac": 1.0, **e.NOISE},
    }


def test_meta_check_accepts_each_arm_and_names_what_differs():
    for arm in ("tierra_n0", "tierra_t50", "std_n0", "std_t50"):
        assert e.meta_problems(good_meta(arm), arm, 250_000) == []
    m = good_meta()
    assert e.meta_problems(m, "tierra_n0", 250_000) == ["cycle_theft_pct 50, not 0"]
    assert e.meta_problems(m, "std_t50", 250_000)[0].startswith("ancestor tierra")

    def changed(**kw):
        x = copy.deepcopy(good_meta())
        for k, v in kw.items():
            if k in x["config"] or k in ("legacy_pending_range", "patch_income"):
                x["config"][k] = v
            else:
                x[k] = v
        return e.meta_problems(x, "tierra_t50", 250_000)

    assert any("legacy_pending_range" in p for p in changed(legacy_pending_range=True))
    assert any("sun" in p for p in changed(patch_income=256_000))
    assert any("p_bit_rot" in p for p in changed(p_bit_rot=0.0))
    assert any("ticks_run None" in p for p in changed(ticks_run=None))  # a killed run
    assert changed(ticks_run=94) == []                                  # an extinct run stops early
    assert any("ticks_requested 50000" in p for p in changed(ticks_requested=50_000))
    assert any("founder_starts" in p for p in changed(founder_starts=[0]))
    no_key = copy.deepcopy(good_meta())
    del no_key["config"]["legacy_pending_range"]                       # before T08: the legacy world
    assert any("legacy_pending_range absent" in p for p in e.meta_problems(no_key, "tierra_t50", 250_000))


def test_meta_check_snapshots_tax_and_replay():
    no_snap = good_meta()
    del no_snap["state_every"]
    assert any("state_every" in p for p in e.meta_problems(no_snap, "tierra_t50", 250_000))
    assert e.meta_problems(no_snap, "tierra_t50", 250_000, snapshots=False) == []
    tax = good_meta("tierra_tax")
    tax["config"].update(cycle_tax_pct=4, cycle_tax_frac=0.25)
    assert e.meta_problems(tax, "tierra_tax", 250_000, tax=(4, 0.25)) == []
    assert e.meta_problems(tax, "tierra_tax", 250_000, tax=(5, 0.25)) != []
    assert e.meta_problems(tax, "tierra_tax", 250_000, tax=None) != []
    assert e.meta_problems(good_meta("tierra_n0") | {"config": {**good_meta("tierra_n0")["config"], "cycle_tax_pct": 4}},
                           "tierra_n0", 250_000) == ["cycle tax 4 / 1.0, not off"]
    rep = good_meta()
    rep.update(founders=[], founder_starts=[], state_every=None, ticks_run=75_000,
               replay_from={"path": "x", "tick": 25_000, "file_seed": 3, "reseed": 1001})
    assert e.meta_problems(rep, "tierra_t50", None, snapshots=False, replay=dict(tick=25_000, reseed=1001)) == []
    assert e.meta_problems(rep, "tierra_t50", None, snapshots=False, replay=dict(tick=50_000, reseed=1001)) != []
    assert e.meta_problems(rep, "tierra_t50", None, snapshots=False, replay=dict(tick=25_000, reseed=1002)) != []


def test_physics_flags_per_arm():
    assert e.physics("tierra_n0") == ["--sun", "2"]
    assert e.physics("std_t50") == ["--sun", "2", "--cycle-theft-pct", "50"]
    assert e.physics("tierra_tax", (4, 0.25)) == ["--sun", "2", "--cycle-tax-pct", "4", "--cycle-tax-frac", "0.25"]
    with pytest.raises(SystemExit):
        e.physics("tierra_tax")
    cmd = e.world_cmd(Path("evo"), Path("d"), "tierra_t50", 7, 250_000, None, True)
    assert cmd[-2:] == ["--state-every", "25000"] and "--legacy-pending-range" not in cmd
    assert "--state-every" not in e.world_cmd(Path("evo"), Path("d"), "tierra_t50", 7, 2_000, None, False)


# ---- reading helpers ----------------------------------------------------------------------------

def test_maintained_rule():
    lo, hi = 0.005, 0.02
    assert e.maintained([None, lo, hi, hi, hi, hi, hi, hi, hi, hi])["clause"] == "to_end"
    m = e.maintained([hi, hi, hi, hi, lo, lo, lo, lo, lo, lo])
    assert m["clause"] == "run" and m["longest_windows"] == 4
    assert e.maintained([hi, hi, hi, lo, hi, hi, hi, lo, lo, lo])["maintained"] is False
    assert e.maintained([lo] * 9 + [hi]) == dict(maintained=True, clause="to_end", first_window=10,
                                                 longest_windows=1, windows_held=1)  # as §1 is written
    assert e.maintained([lo] * 10)["first_window"] is None
    assert e.maintained([0.01])["maintained"] is True                                   # >= 1%, not >


def test_pair_off_break_and_repair():
    s = lambda eff, fp, fc: {"effect": eff, "f_parent": fp, "f_child": fc}
    steps = [s("neutral", 100, 100), s("deleterious", 100, 0), s("beneficial", 0, 99), s("deleterious", 99, 50),
             s("beneficial", 50, 90), s("deleterious", 90, 0), s("beneficial", 0, 90)]
    assert e.pair_off(steps) == {1, 2, 5, 6}


def test_lineages_and_time_to_loss():
    b = pl.DataFrame({
        "child":    [3, 4, 5, 6, 7, 8, 9],
        "executor": [2, 3, 3, 4, 6, 2, 8],
        "tick":     [10, 20, 30, 40, 55, 60, 90],
        "raw_hash":        ["C", "C", "X", "C", "C", "C", "C"],
        "parent_now_hash": ["C", "C", "X", "C", "C", "A", "C"],
    })
    lin = e.lineages(b, {"C"}, alive={9})
    r = {x["origin_id"]: x for x in lin.iter_rows(named=True)}
    assert set(r) == {3, 8}                                   # 3 from the founder 2, 8 from it again
    assert r[3]["carriers"] == 4 and r[3]["exact"] == 3 and r[3]["time_to_loss"] == 55 - 10
    assert r[3]["censored"] is False
    assert r[8]["exact"] == 1 and r[8]["time_to_loss"] == 30 and r[8]["censored"] is True


def test_look_back_by_region():
    anc = bytes.fromhex(e.HEX["tierra"])
    target = bytearray(anc)
    target[14] ^= 0x02    # template byte
    target[19] ^= 0x02    # label byte
    parent = bytearray(anc)
    parent[14] ^= 0x02
    rows = {r["who"]: r for r in e.look_back(anc, bytes(target), {"parent": bytes(parent), "grandparent": anc},
                                             "tierra")}
    assert rows["parent"]["n_carried"] == 1 and rows["parent"]["by_region"] == "label 0/1; template 1/1"
    assert rows["parent"]["to_target"] == "sub@19:01>03"
    assert rows["grandparent"]["n_carried"] == 0 and rows["grandparent"]["n_target"] == 2


# ---- the one engine call ------------------------------------------------------------------------

def test_probe_is_a_jump_parasite_on_the_tierra_ancestor():
    try:
        exe = measures.evo_bin(None)
    except FileNotFoundError:
        pytest.skip("evo-core binary not built")
    r = lod.harness_entered(exe, e.HEX["tierra"], 3_000, flags=("--sun", "2"), probe=e.PROBE["tierra"])
    assert r["pad_exact"] >= 2           # the probe's exact births before the host (`exact_host`)
    assert r["entry_off"] == 22          # entered just past the host's L1
    assert r["host_alive"]
    alone = lod.harness_alone(exe, {"probe": e.PROBE["tierra"]}, 3_000, flags=("--sun", "2"))["probe"]
    assert alone["class"] != "replicator"


def test_world_refuses_a_binary_without_snapshots(monkeypatch):
    """The `--state-every` probe reads the dry run's exit code and error text
    (the engine before T04 exits 2 with `unknown arg --state-every`)."""
    import subprocess

    def fake(answer):
        def run(cmd, **kw):
            assert "--state-every" in cmd and "--ticks" in cmd and cmd[cmd.index("--ticks") + 1] == "1"
            return subprocess.CompletedProcess(cmd, answer[0], stdout="", stderr=answer[1])
        return run

    monkeypatch.setattr(e.subprocess, "run", fake((2, "unknown arg --state-every")))
    with pytest.raises(SystemExit, match="does not accept --state-every"):
        e.require_snapshots(Path("evo-core"))
    monkeypatch.setattr(e.subprocess, "run", fake((0, "")))
    e.require_snapshots(Path("evo-core"))  # a T04 binary passes


def test_replay_plan_snapshots_and_background():
    runs = pl.DataFrame({"arm": ["tierra_t50"] * 4, "seed": [1, 2, 3, 4], "screened": [True] * 4,
                         "first_complete_tick": [60_000, 500, None, None]}, schema_overrides={"first_complete_tick": pl.Int64})
    plan, notes = e.replay_plan(runs, "tierra_t50")
    defence = [p for p in plan if p[0] == 1]
    assert defence == [(1, 50_000, s, 110_000) for s in range(1001, 1011)]
    assert any("s2" in n and "no snapshot" in n for n in notes)
    background = [p for p in plan if p[3] == e.BACKGROUND_TO]
    assert [p[0] for p in background] == [3, 4] * 5          # two seeds without a defence, cycled
    assert [p[2] for p in background] == list(range(1001, 1011))
    assert all(p[1] == 25_000 for p in background)
    assert len(e.replay_plan(runs, "tierra_t50", 2)[0]) == 4  # smoke: two per source
