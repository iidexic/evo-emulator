"""Tests for lod.py on a synthetic run directory with a known line (T06 §5).

The run is written from the CSV formats in docs/instrumentation.md. The
harness calls are mocked; lod_e007.py runs them for real.

    cd analysis
    uv run --with pytest pytest tests/test_lod.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import lod  # noqa: E402
from traits import LIT, canonical_instrs  # noqa: E402

STATS = ["born_with_m", "executed", "absorbs", "absorb_gain_m", "absorb_short", "absorb_capped", "copies",
         "reads_foreign", "exec_foreign", "exec_unowned", "writes_blocked", "range_faults", "allocs_ok",
         "allocs_fail", "divides_ok", "divides_fail", "endowed_m", "spent_m", "upkeep_m", "starved_ticks",
         "last_divide_tick", "max_energy_m", "paid_for_others_m", "paid_by_others_m", "gained_from_others_m",
         "writes_foreign", "overwritten"]
BIRTHS = ["tick", "child", "executor", "source", "start", "len", "copy_errors", "slips", "endowment_m", "raw_hash",
          "parent_hash", "parent_now_hash", "source_hash"]
DEATHS = ["tick", "id", "cause", "age", "offspring", "len", "start", "pending_len", "ip_off", "op_at_ip", "energy_m",
          "pool_m", "birth_hash", "now_hash", *STATS]
ORGS = ["tick", "id", "parent", "birth_tick", "start", "len", "pending_len", "energy_m", "ip_off", "op_at_ip",
        "birth_hash", "now_hash", "offspring", *STATS]
GENOMES = ["raw_hash", "func_hash", "len", "first_tick", "first_id", "origin", "parent_hash", "bytes_hex", "disasm"]


def fnv(b: bytes) -> str:
    h = 0xCBF29CE484222325
    for x in b:
        h = ((h ^ x) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{h:016x}"


def func_hash(b: bytes) -> str:
    """FNV-1a of the canonical form (docs/instrumentation.md, 'Two genome hashes')."""
    out = bytearray()
    for op, cm, v in canonical_instrs(b):
        out.append(op | (cm << 5))
        if op == LIT and v is not None:
            out.append(v & 0xFF)
    return fnv(bytes(out))


ANC = bytes.fromhex("13325271fc11401605086c5a1845486c11101c130d")  # absorb 64 (byte 6), endowment 16
G0 = ANC
G1 = b"\x00" + G0                                # insertion of `pad` at 0; absorb byte unreadable, pattern 64
G2 = G1[:7] + bytes([120]) + G1[8:]              # absorb count 64 -> 120 (byte 7 in the shifted body)
G3 = G2[1:]                                      # deletion of the `pad`: the ancestor with absorb 120
GX = G2[:-1] + b"\x0e"                           # the executor's somatic body at step 3 (not on the line)
GL = b"\x00"                                     # a loafer: the largest living group, to be passed over
H = {name: fnv(g) for name, g in (("G0", G0), ("G1", G1), ("G2", G2), ("G3", G3), ("GX", GX), ("GL", GL))}
ALONE = {H["G0"]: 230, H["G1"]: 100, H["G2"]: 150, H["G3"]: 151, H["GL"]: 0}


def write_run(d: Path, births: list[tuple], deaths: list[tuple], alive: dict[int, list[tuple]],
              genomes: dict[str, bytes], last_tick: int) -> None:
    """births: (tick, child, executor, genome, parent birth genome, parent body at divide, copy_errors).
    deaths: (tick, id, age, offspring, genome). alive: census tick -> (id, parent, birth_tick, genome,
    offspring)."""
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"ticks_requested": last_tick, "ticks_run": last_tick,
                                             "census_every": 50_000}))

    def w(name, header, rows):
        with open(d / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            cw = csv.writer(f, lineterminator="\n")
            cw.writerow(header)
            cw.writerows(rows)

    w("births", BIRTHS, [
        (t, c, e, e, 1000 + c, len(g), ce, 0, 16000, fnv(g), fnv(pb), fnv(pn), fnv(pb))
        for t, c, e, g, pb, pn, ce in births])
    w("deaths", DEATHS, [
        (t, i, "upkeep", age, off, len(g), 0, 0, 0, "absorb", 0, 0, fnv(g), fnv(g), *([0] * len(STATS)))
        for t, i, age, off, g in deaths])
    w("orgs", ORGS, [
        (tick, i, p, bt, 0, len(g), 0, 50000, 0, "absorb", fnv(g), fnv(g), off, *([0] * len(STATS)))
        for tick, rows in sorted(alive.items()) for i, p, bt, g, off in rows])
    census = sorted(set(alive) | {last_tick})
    w("patches", ["tick", "patch", "pool_m", "orgs", "absorbed_m", "overflow_m"],
      [(t, p, 4096000, 1, 0, 0) for t in census for p in range(2)])
    w("census", ["tick", "now_hash", "count"], [(t, fnv(G0), 1) for t in census])
    w("genomes", GENOMES, [
        (fnv(g), func_hash(g), len(g), 0, 0, "birth", "0" * 16, g.hex(), "") for g in genomes.values()])


@pytest.fixture
def mock_harness(monkeypatch):
    calls = {"alone": [], "entered": []}

    def alone(exe, genomes, ticks):
        calls["alone"].append(dict(genomes))
        return {h: {"class": "replicator" if ALONE[h] >= 2 else "loafer", "births": ALONE[h],
                    "exact_births": ALONE[h], "first_birth_tick": 20 if ALONE[h] else -1, "alive": True}
                for h in genomes}

    def entered(exe, host_hex, ticks):
        calls["entered"].append(host_hex)
        f = ALONE[fnv(bytes.fromhex(host_hex))]
        return {"host_exact": max(0, f - 10), "host_alive": True, "pad_exact": 5, "ticks_run": ticks,
                "stopped_early": False}

    monkeypatch.setattr(lod, "harness_alone", alone)
    monkeypatch.setattr(lod, "harness_entered", entered)
    return calls


@pytest.fixture
def three_step_run(tmp_path) -> Path:
    """Founder 2 (G0) -> 3 (G0) -> 4 (G1, insertion, copy error) -> 5 (G1) -> 6 (G2, substitution inherited
    from a somatic change in 5) -> 7 (G3, deletion, copied with errors from a somatically changed 6)
    -> 8 (G3), alive at tick 100,000 with the most offspring in its group."""
    births = [
        # tick, child, executor, genome, parent's birth genome, parent's body at divide, copy errors
        (100, 3, 2, G0, G0, G0, 0),
        (30_000, 4, 3, G1, G0, G0, 1),
        (30_100, 5, 4, G1, G1, G1, 0),
        (30_200, 22, 5, G1, G1, G1, 0),
        (30_300, 23, 5, G1, G1, G1, 0),
        (40_000, 30, 3, GL, G0, G0, 3), (40_001, 31, 3, GL, G0, G0, 3), (40_002, 32, 3, GL, G0, G0, 3),
        (40_003, 33, 3, GL, G0, G0, 3), (40_004, 34, 3, GL, G0, G0, 3), (40_005, 35, 3, GL, G0, G0, 3),
        (40_006, 36, 3, GL, G0, G0, 3),
        (52_000, 6, 5, G2, G1, G2, 0),
        (80_000, 7, 6, G3, G2, GX, 2),
        (80_100, 8, 7, G3, G3, G3, 0),
        (80_200, 20, 7, G3, G3, G3, 0),
        (80_300, 21, 7, G3, G3, G3, 0),
        (90_000, 24, 8, G3, G3, G3, 0),
        (95_000, 25, 8, G3, G3, G3, 0),
        (105_000, 26, 21, G3, G3, G3, 0),
    ]
    births.sort(key=lambda r: r[1])  # births.csv is in id order in a real run
    deaths = [
        # tick, id, age, offspring, genome
        (5_000, 2, 5_000, 1, G0), (35_000, 3, 34_900, 8, G0), (40_000, 4, 10_000, 1, G1),
        (60_000, 5, 29_900, 3, G1), (85_000, 6, 33_000, 1, G2), (81_000, 7, 1_000, 3, G3),
        (110_000, 20, 29_800, 0, G3), (110_000, 21, 29_700, 1, G3),
    ]
    alive = {
        0: [(2, 0, 0, G0, 0)],
        100_000: [
            (8, 7, 80_100, G3, 2), (20, 7, 80_200, G3, 0), (21, 7, 80_300, G3, 0),
            (24, 8, 90_000, G3, 0), (25, 8, 95_000, G3, 0),
            (22, 5, 30_200, G1, 0), (23, 5, 30_300, G1, 0),
            *[(i, 3, 40_000 + i - 30, GL, 0) for i in range(30, 37)],
        ],
    }
    d = tmp_path / "run"
    write_run(d, births, deaths, alive, {k: g for k, g in (("G0", G0), ("G1", G1), ("G2", G2), ("G3", G3),
                                                          ("GL", GL))}, last_tick=120_000)
    return d


def test_edit_script():
    assert lod.edit_script(b"\x01\x02\x03", b"\x01\x09\x03") == [("sub", 1, 2, 9)]
    assert lod.edit_script(b"\x01\x02\x03", b"\x01\x03") == [("del", 1, 2, None)]
    assert lod.edit_script(b"\x01\x02", b"\x01\x02\x07") == [("ins", 2, None, 7)]
    # an insertion into a run of equal bytes goes at the run's left end
    assert lod.edit_script(b"\x05\x00\x00\x06", b"\x05\x00\x00\x00\x06") == [("ins", 1, None, 0)]
    ops = lod.edit_script(b"\x01\x02\x03\x04", b"\x02\x03\x09")
    assert len(ops) == 2 and lod.step_kind(ops) == "substitution+deletion"
    assert lod.format_edits([("sub", 6, 0x40, 0x78), ("ins", 0, None, 0), ("del", 20, 0x0D, None)]) \
        == "sub@6:40>78;ins@0:+00;del@20:-0d"


def test_absorb_count():
    assert lod.absorb_count(ANC) == 64 and lod.absorb_byte(ANC) == 64
    # E007 seed 3's loop: `lit A -114 ; absorb ; inc A ; skipz A`
    inc = bytearray(ANC)
    inc[6], inc[8] = 0x8E, 0x04
    assert lod.absorb_byte(bytes(inc)) == -114
    assert lod.absorb_pattern(bytes(inc)) == (True, 114)
    assert lod.absorb_count(bytes(inc)) == 114
    # a `dec` loop from a negative count cannot end: no count, not the byte
    neg = bytearray(ANC)
    neg[6] = 0x8E
    assert lod.absorb_pattern(bytes(neg)) == (True, None) and lod.absorb_count(bytes(neg)) is None
    # shifted body: the byte is unreadable, the pattern still finds the loop
    assert lod.absorb_byte(G1) is None and lod.absorb_count(G1) == 64
    assert lod.absorb_count(G2) == 120 and lod.absorb_count(G3) == 120


def test_three_step_line(three_step_run, mock_harness, tmp_path):
    out = tmp_path / "out"
    r = lod.lod(three_step_run, at=100_000, out=out, exe=Path("mock-evo"), log=lambda *_: None)

    # The pick passes over the larger loafer group and takes the most offspring in the replicator group.
    assert r.pick.end_id == 8
    assert r.pick.group_size == 5
    assert r.pick.skipped == [(func_hash(GL), 7, "loafer")]
    assert r.line["id"].to_list() == [2, 3, 4, 5, 6, 7, 8]
    assert r.line["generation"].to_list() == list(range(7))
    assert r.genomes["raw_hash"].to_list() == [H["G0"], H["G1"], H["G2"], H["G3"]]

    s = r.steps.rows(named=True)
    assert len(s) == 3
    want = [
        # child, generation, tick, kind, edits, origin, absorb, f, effect
        (4, 2, 30_000, "insertion", "ins@0:+00", "copy", (64, 64), (230, 100), "deleterious"),
        (6, 4, 52_000, "substitution", "sub@7:40>78", "somatic", (64, 120), (100, 150), "beneficial"),
        (7, 5, 80_000, "deletion", "del@0:-00", "somatic+copy", (120, 120), (150, 151), "neutral"),
    ]
    for got, (child, gen, tick, kind, edits, origin, ab, f, eff) in zip(s, want):
        assert (got["child_id"], got["generation"], got["tick"]) == (child, gen, tick)
        assert (got["kind"], got["edits"], got["origin"]) == (kind, edits, origin)
        assert (got["absorb_parent"], got["absorb_child"]) == ab
        assert (got["f_parent"], got["f_child"], got["df"]) == (*f, f[1] - f[0])
        assert got["effect"] == eff
        assert got["synonymous"] is False
        assert got["entered_child"] == f[1] - 10
    assert [x["copy_errors"] for x in s] == [1, 0, 2]

    # World fitness of G3 in window 4 (ticks 75,000-100,000): born 7, 8, 20, 21, 24, 25; died 7, 20, 21;
    # exact children of the dead 3 + 0 + 1; ages 1,000, 29,800, 29,700.
    st = s[2]
    assert (st["world_born_child"], st["world_died_child"]) == (6, 3)
    assert st["world_exact_per_death_child"] == pytest.approx(4 / 3)
    assert st["world_age_med_child"] == 29_700
    assert (st["world_born_parent"], st["world_exact_per_death_parent"]) == (0, None)
    g = r.genomes.filter(pl.col("raw_hash") == H["G1"]).row(0, named=True)
    # G1 first on the line in window 2: born 4, 5, 22, 23; died 4, 5; exact children 1 (5) + 2 (22, 23).
    assert (g["world_window"], g["world_born"], g["world_died"]) == (2, 4, 2)
    assert g["world_exact_per_death"] == pytest.approx(1.5)
    assert (g["absorb_byte"], g["absorb_pat"], g["absorb"]) == (None, 64, 64)

    c = lod.counts(r.steps)
    assert (c["total"], c["beneficial"], c["neutral"], c["deleterious"], c["order"]) == (3, 1, 1, 1, "DBn")
    assert (c["to_zero"], c["from_zero"]) == (0, 0)
    assert not any(r.steps["entered_stopped_child"])
    a = r.absorb
    assert (a["start"], a["final"], a["raises"], a["raises_after_deleterious"]) == (64, 120, 1, 1)
    for key in ("final_step", "sweep_step"):
        assert a[key]["index"] == 1 and a[key]["held"]
        assert a[key]["prev_effect"] == "deleterious"
        assert [x["step"] for x in a[key]["before"]] == [1]

    for f in ("steps.csv", "genomes.csv", "line.csv", "summary.md"):
        assert (out / f).exists()
    text = (out / "summary.md").read_text(encoding="utf-8")
    assert "beneficial 1, neutral 1, deleterious 1" in text
    assert "Step immediately before: deleterious" in text
    assert b"\r" not in (out / "summary.md").read_bytes()
    # Distinct genomes go through the harness once each; the pick's classifications are reused.
    assert sorted(mock_harness["entered"]) == sorted(g.hex() for g in (G0, G1, G2, G3))
    assert sum(len(x) for x in mock_harness["alone"]) == 5


def test_pick_id_and_default_tick(three_step_run, mock_harness, tmp_path):
    r = lod.lod(three_step_run, at=100_000, pick="id:4", out=tmp_path / "o1", exe=Path("mock-evo"),
                log=lambda *_: None)
    assert r.line["id"].to_list() == [2, 3, 4]
    assert r.steps.height == 1 and r.steps["kind"][0] == "insertion"
    # The last census (120,000) has no orgs rows here: nothing alive to pick from.
    with pytest.raises(lod.NoLine):
        lod.lod(three_step_run, out=tmp_path / "o2", exe=Path("mock-evo"), log=lambda *_: None)
    with pytest.raises(lod.NoLine):
        lod.lod(three_step_run, at=250_000, out=tmp_path / "o3", exe=Path("mock-evo"), log=lambda *_: None)


def test_synonymous_step(tmp_path, mock_harness):
    syn = bytearray(G0)
    syn[2] |= 0x80  # `swap C` with bit 7 set: the decoder reads bits 5-6 only
    syn = bytes(syn)
    assert func_hash(syn) == func_hash(G0) and fnv(syn) != fnv(G0)
    ALONE[fnv(syn)] = 229
    try:
        d = tmp_path / "run"
        write_run(d, [(10, 3, 2, syn, G0, G0, 1)], [], {0: [(2, 0, 0, G0, 0)], 500: [(3, 2, 10, syn, 0)]},
                  {"G0": G0, "S": syn}, last_tick=500)
        r = lod.lod(d, out=tmp_path / "o", exe=Path("mock-evo"), log=lambda *_: None)
        s = r.steps.row(0, named=True)
        assert (s["synonymous"], s["kind"], s["edits"], s["effect"]) == (True, "substitution", "sub@2:52>d2",
                                                                          "neutral")
    finally:
        del ALONE[fnv(syn)]


def test_evo_bin_override(tmp_path, monkeypatch):
    exe = tmp_path / "evo-core.exe"
    exe.write_bytes(b"")
    assert lod.evo_bin(str(exe)) == exe
    monkeypatch.setenv("EVO_BIN", str(exe))
    assert lod.evo_bin(None) == exe
    monkeypatch.setenv("EVO_BIN", str(tmp_path / "missing.exe"))
    with pytest.raises(FileNotFoundError):
        lod.evo_bin(None)
