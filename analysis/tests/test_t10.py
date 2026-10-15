"""Tests for T10's part of e016_defence.py: the tierra_taxL arm's flags (world
and harness), its meta.json check, the lifelong calibration arithmetic and
its mean check (§2.2), the calibration files, the pilot's population reading
(§4) and the E017 paired reading (§3). One engine call: the harness under
the lifelong flag (skipped without the binary).

    uv run --project analysis --with pytest pytest analysis/tests/test_t10.py
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import e016_defence as e  # noqa: E402


def good_meta(arm: str) -> dict:
    b = e.base(arm)
    return {
        "ticks_requested": 250_000, "ticks_run": 250_000, "ancestor": b, "founders": [{"hex": e.HEX[b], "count": 1}],
        "founder_starts": [32_768], "state_every": 2_500, "replay_from": None,
        "config": {"patch_income": 512_000, "patch_cap": 8_192_000, "legacy_pending_range": False,
                   "cycle_theft_pct": 50 if arm.endswith("t50") else 0, "cycle_tax_pct": 0, "cycle_tax_frac": 1.0,
                   "cycle_tax_life_frac": 0.0, "cycle_tax_life_pct": 0, **e.NOISE},
    }


def test_taxl_flags_world_and_harness():
    t = {"tierra_tax": (88, 0.24), "tierra_taxL": (66, 0.43)}
    assert e.physics("tierra_taxL", t) == ["--sun", "2", "--cycle-tax-lifelong", "0.43", "66"]
    assert e.physics("tierra_taxL", (66, 0.43)) == e.physics("tierra_taxL", t)       # the arm's own pair
    assert e.physics("tierra_tax", t) == ["--sun", "2", "--cycle-tax-pct", "88", "--cycle-tax-frac", "0.24"]
    assert e.harness_physics("tierra_taxL", t) == e.physics("tierra_n0") == ["--sun", "2"]
    assert e.harness_physics("tierra_tax", t) == e.physics("tierra_tax", t)            # the per-tick tax stays
    assert e.harness_physics("tierra_t50", t) == ["--sun", "2", "--cycle-theft-pct", "50"]
    with pytest.raises(SystemExit):
        e.physics("tierra_taxL", {"tierra_tax": (88, 0.24)})
    with pytest.raises(SystemExit):
        e.physics("tierra_taxL")
    cmd = e.world_cmd(Path("evo"), Path("d"), "tierra_taxL", 3, 50_000, t, False)
    assert cmd[cmd.index("--cycle-tax-lifelong"):][:3] == ["--cycle-tax-lifelong", "0.43", "66"]
    assert "--cycle-tax-lifelong" not in e.classify_cmd(Path("evo"), Path("d"), "tierra_taxL", t)
    assert "tierra_taxL" in e.ARMS and "tierra_taxL" not in e.FIRST_ARMS and e.N0_OF["tierra_taxL"] == "tierra_n0"


def test_meta_check_lifelong_tax():
    t = {"tierra_taxL": (66, 0.43)}
    m = good_meta("tierra_taxL")
    m["config"].update(cycle_tax_life_frac=0.43, cycle_tax_life_pct=66)
    assert e.meta_problems(m, "tierra_taxL", 250_000, tax=t) == []
    assert e.meta_problems(m, "tierra_taxL", 250_000, tax={"tierra_taxL": (65, 0.43)}) != []
    assert any("uncalibrated" in p for p in e.meta_problems(m, "tierra_taxL", 250_000, tax=None))
    assert e.meta_problems(m, "tierra_n0", 250_000, tax=t) == ["lifelong tax F / P 0.43 / 66, not off"]
    both = copy.deepcopy(m)
    both["config"].update(cycle_tax_pct=88, cycle_tax_frac=0.24)                     # the per-tick tax is off in taxL
    assert any("cycle tax 88" in p for p in e.meta_problems(both, "tierra_taxL", 250_000, tax=t))
    old = good_meta("tierra_n0")
    del old["config"]["cycle_tax_life_frac"], old["config"]["cycle_tax_life_pct"]    # runs before T10: off
    assert e.meta_problems(old, "tierra_n0", 250_000) == []
    assert e.meta_problems(old, "tierra_taxL", 250_000, tax=t) != []


def deaths(entered: list[int], lost: list[int], age: list[int]) -> pl.DataFrame:
    return pl.DataFrame({"exec_by_others": entered, "cycles_lost_m": lost, "age": age})


def test_life_calibration_arithmetic_and_mean_check():
    # Entered deaths of 10 and 50 ticks losing 16,000 and 8,000 a tick, unentered of 10 and 10: r = (160,000 +
    # 400,000) / 80 = 7,000 a tick. Per organism-tick (the corrected rule): F = 60 / 80 = 0.75, P = 100 x 560,000 /
    # (60 x 32,000) = 29.17 -> 29, F x P = 21.75% against 21.875%. Per death (the rule first given): F = 1/2,
    # P = 100 x 12,000 / 32,000 = 37.5, F x P = 18.75%, -14%: entered bodies live longer.
    t50 = deaths([4, 1, 0, 0], [160_000, 400_000, 0, 0], [10, 50, 10, 10])
    c = e.life_calibration(t50)
    assert (c["F"], c["P_exact"], c["P"]) == (0.75, pytest.approx(100 * 560_000 / (60 * 32_000)), 29)
    assert c["r"] == 7_000 and c["target"] == pytest.approx(7_000 / 32_000)
    assert c["mean_exact"] == pytest.approx(c["target"])                              # exact before rounding
    assert c["mean"] == pytest.approx(0.75 * 0.29) and c["mean_check_ok"]               # -0.6%
    assert (c["F_deaths"], c["P_deaths_exact"]) == (0.5, pytest.approx(37.5))
    assert c["mean_deaths_rel"] == pytest.approx(0.1875 / 0.21875 - 1)
    assert (c["mean_age_entered"], c["mean_age_unentered"]) == (30, 10)
    # Rounding can fail the check: F = 1/3 of organism-ticks at P_exact 1.5 -> 2 is +33%.
    off = e.life_calibration(deaths([1, 0, 0], [4_800, 0, 0], [10, 10, 10]))
    assert (off["P"], off["mean_check_ok"]) == (2, False)
    with pytest.raises(SystemExit):
        e.life_calibration(deaths([0, 0], [0, 0], [5, 5]))                            # nobody entered


def test_calibration_files_and_load_tax(tmp_path):
    assert e.load_tax(tmp_path) is None
    c = dict(P=66, F=0.43, note="a")
    e.write_calibration(tmp_path / "tax_life.json", c, False, "tierra_taxL")
    assert e.load_tax(tmp_path) == {"tierra_taxL": (66, 0.43)}
    before = (tmp_path / "tax_life.json").stat().st_mtime_ns
    e.write_calibration(tmp_path / "tax_life.json", c, False, "tierra_taxL")         # same text: untouched
    assert (tmp_path / "tax_life.json").stat().st_mtime_ns == before
    with pytest.raises(SystemExit):
        e.write_calibration(tmp_path / "tax_life.json", dict(c, P=65), False, "tierra_taxL")
    e.write_calibration(tmp_path / "tax_life.json", dict(c, P=65), True, "tierra_taxL")
    (tmp_path / "tax.json").write_text(json.dumps(dict(P=88, F=0.24)))
    assert e.load_tax(tmp_path) == {"tierra_tax": (88, 0.24), "tierra_taxL": (65, 0.43)}
    assert e.tax_of(e.load_tax(tmp_path), "tierra_tax") == (88, 0.24) and e.tax_of(None, "tierra_taxL") is None


def write_run(d: Path, census: list[tuple[int, str, int]], ticks_run: int) -> None:
    d.mkdir(parents=True)
    pl.DataFrame(census, schema=["tick", "now_hash", "count"], orient="row").write_csv(d / "census.csv")
    pl.DataFrame({"raw_hash": ["aa", "bb"], "class": ["replicator", "dies"]}).write_csv(d / "classes.csv")
    (d / "meta.json").write_text(json.dumps(dict(ticks_run=ticks_run)))


def test_population_reading_counts_replicator_bodies_and_zero_after_extinction(tmp_path):
    a = tmp_path / "a"
    write_run(a, [(500, "aa", 3), (500, "bb", 4), (1_000, "aa", 5), (1_000, "cc", 1), (1_500, "aa", 7)], 1_500)
    r = e.population_row(a, 500, 1_500)
    assert (r["persisted"], r["rep_end"], r["pop_end"], r["rep_mean"], r["rep_min"]) == (True, 7, 7, 5.0, 3)
    b = tmp_path / "b"
    write_run(b, [(500, "aa", 3), (500, "bb", 4)], 700)                              # extinct at 700
    x = e.rep_population(b, 500, 1_500)
    assert x["rep"].to_list() == [3, 0, 0]
    assert not e.population_row(b, 500, 1_500)["persisted"]


def test_taxed_deaths_and_the_founder(tmp_path):
    d = tmp_path / "r"
    write_run(d, [(500, "aa", 3)], 1_000)
    pl.DataFrame({"tick": [73, 600, 700, 800], "id": [2, 5, 6, 7], "age": [73, 100, 300, 9],
                  "birth_hash": ["aa", "aa", "aa", "bb"], "cycles_taxed_m": [0, 0, 6_336_000, 0],
                  "taxed_for_life": [1, 0, 1, 1]}).write_csv(d / "deaths.csv")
    pl.DataFrame({"tick": [10, 20]}).write_csv(d / "births.csv")
    r = e.taxed_deaths(d, 500)                         # deaths after 500, replicator class: ids 5 and 6
    assert (r["rep_deaths"], r["taxed_share"], r["founder_taxed"], r["births"]) == (2, 0.5, True, 2)
    assert r["debit"] == pytest.approx(6_336_000 / 400 / 32_000)


def test_e017_paired_reading():
    seeds = list(range(1, 31))
    runs = pl.DataFrame({
        "arm": ["tierra_n0"] * 30 + ["tierra_t50"] * 30 + ["tierra_taxL"] * 30,
        "seed": seeds * 3,
        "structural_share_end": [0.15] * 30 + [0.21] * 30 + [0.14] * 25 + [0.16] * 5,
        "final_tick": [250_000] * 85 + [40_000] * 5, "pop_end": [1_500] * 85 + [0] * 5,
    })
    lines = e.e017_lines(runs, 30, 250_000)
    assert "persists to 250,000 in 25 of 30 seeds [>= 24]: holds" in lines[1]
    assert "t50 above taxL in 30 of 30 pairs" in lines[2] and "taxL above n0 in 5 of 30" in lines[2]
    assert "the cost of being entered [t50 above taxL >= 20, taxL above n0 <= 18]: holds" in lines[3]
    assert "slowness" in lines[3] and lines[3].endswith("fails.")
    assert e.e017_lines(runs.filter(pl.col("arm") != "tierra_taxL"), 30, 250_000) == []


def test_harness_bodies_are_founders_and_never_taxed():
    # The harness seeds its bodies, and founders are never taxed (T10 §2), so at F = 1 (no draw) the harness under
    # the flag is the harness without it; children, removed the tick they are born, never run. harness_physics
    # drops the flag anyway: at 0 < F < 1 the children's draws would move the shuffle order.
    try:
        exe = e.evo_bin(None)
    except SystemExit:
        pytest.skip("no evo-core binary")

    def host(*flags: str) -> list[str]:
        r = subprocess.run([str(exe), "--host", e.PROBE["tierra"], "--host-body", e.HEX["tierra"], "--harness-ticks",
                            "3000", "--sun", "2", *flags], capture_output=True, text=True)
        if r.returncode != 0:
            pytest.skip("binary without --cycle-tax-lifelong (T10)")
        return r.stdout.strip().splitlines()[-1].split(",")

    plain = host()
    assert int(plain[4]) > 100                                                    # host_exact_births
    assert host("--cycle-tax-lifelong", "1", "66") == plain
