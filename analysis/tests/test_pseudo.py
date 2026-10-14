"""Tests for pseudo.py, the static pseudo-code reading of a genome.

Bodies are the two ancestors (sim.rs `ancestor`, `ancestor_t`), hand
assembled ones for single features, and random bytes for crashes.

    cd analysis
    uv run --with pytest pytest tests/test_pseudo.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pseudo import OPS, REGS, decode, explain  # noqa: E402

ANC = bytes.fromhex("13325271fc11401605086c5a1845486c11101c130d")
ANC_T = bytes.fromhex("0101030351fc117f1605084c0a010301036d030103011332525a71fc1845486c11101c0b030301016d")
OPCODE = {name: code for code, name in OPS.items()}


def asm(src: str) -> bytes:
    """`isa::assemble` in Python: "op", "op R", "self N", "lit R v";
    instructions separated by ";" or newlines."""
    out = bytearray()
    for line in src.replace(";", "\n").splitlines():
        parts = line.split()
        if not parts:
            continue
        op, args = parts[0], parts[1:]
        mod = 0
        if args:
            mod = REGS.index(args[0]) if args[0] in REGS else int(args[0])
        out.append(OPCODE[op] | (mod & 7) << 5)
        if op == "lit":
            out.append(int(args[1]) & 0xFF)
    return bytes(out)


def note(r, off: int) -> str:
    return next(row.note for row in r.rows if row.off == off)


def test_asm_matches_the_ancestor():
    assert asm("self 0 ; swap B ; swap C ; lit D -4 ; lit A 64 ; absorb ; dec A ; skipz A ; jmpr D ; alloc C ;"
               "copy ; dec C ; skipz C ; jmpr D ; lit A 16 ; divide A ; self 0 ; jmpa A") == ANC


def test_ancestor():
    r = explain(ANC)
    assert r.story == "absorb×64 → alloc 21 → copy×21 → divide(16) → repeat"
    assert r.unresolved == []
    assert note(r, 0) == "A = 64, B = @0 (my start), C = 21 (my length), D = -4"
    assert note(r, 7) == "repeat 64 times: absorb energy"
    assert note(r, 12) == "repeat 21 times (my length): copy all 21 of my bytes into the child"
    assert note(r, 16) == "split off the child, giving it 16 energy"
    assert note(r, 19) == "go to 0 (start over)"
    assert [row.off for row in r.rows] == [0, 7, 11, 12, 16, 19]


def test_template_ancestor():
    r = explain(ANC_T)
    assert r.story == "absorb×127 → alloc 41 → copy×41 → divide(16) → repeat from 4"
    assert note(r, 0).startswith("label 0011: searchb at 35 lands after it")
    assert note(r, 18) == "label 1010: searchf at 12 lands after it"
    assert note(r, 12) == "find label 1010 ahead: D = @22, C = 4"
    assert note(r, 40) == "go to 4"


def test_mutant_reads_as_a_change_of_numbers():
    m = bytearray(ANC)
    m[6], m[17] = 121, 40
    assert explain(bytes(m)).story == "absorb×121 → alloc 21 → copy×21 → divide(40) → repeat"


def test_counting_up_and_zero_count():
    up = explain(asm("lit A -114 ; lit D -4 ; absorb ; inc A ; skipz A ; jmpr D"))
    assert up.story.startswith("absorb×114 →")
    assert note(up, 4).startswith("repeat 114 times: absorb energy")
    zero = explain(asm("lit A 0 ; lit D -4 ; absorb ; dec A ; skipz A ; jmpr D"))
    assert zero.story.startswith("absorb×∞")
    assert "in effect forever" in note(zero, 4)


def test_counter_is_zero_after_its_loop():
    r = explain(asm("lit A 3 ; lit D -4 ; absorb ; dec A ; skipz A ; jmpr D ; alloc A"))
    assert note(r, 8).startswith("claim 0 bytes: always fails, so A = 0, flag set")


def test_pad_runs_off_its_end():
    r = explain(bytes(21))
    assert r.story == "nothing → runs on past its end"
    assert len(r.rows) == 1 and r.rows[0].code == "pad ×21"


def test_dead_code():
    r = explain(ANC + asm("absorb ; absorb ; copy"))
    assert r.rows[-1].code == "absorb ×2 ; copy" and r.rows[-1].note == "never runs"


def test_jump_whose_target_differs_between_rounds():
    # The first round enters with C = 0, so `jmpr C` runs on to the absorb;
    # the search sets C = 1 (its label's length), so later rounds skip it.
    r = explain(asm("nop1 ; jmpr C ; absorb ; searchb ; nop0 ; jmpa D"))
    assert note(r, 1) == "go to 2 or 3"
    assert r.story == "absorb → repeat from 1; later rounds: nothing → repeat from 1"


def test_search_with_no_match_in_the_body():
    r = explain(asm("searchf ; nop0 ; nop1 ; jmpa D"))
    assert r.story == "search 10 outside → jump to label 10 outside"
    assert "none in this body" in note(r, 0)


def test_store_into_own_code_is_flagged():
    r = explain(asm("self 0 ; lit B 7 ; store B"))
    assert "its own code" in note(r, 0)


def test_jump_into_a_lit_operand():
    # lit A 22: its operand byte is `absorb`; `jmpr D` lands on it.
    r = explain(bytes([OPCODE["lit"], OPCODE["absorb"]]) + asm("lit D -4 ; jmpr D"))
    assert "its byte 1 also runs, as `absorb`" in note(r, 0)
    assert r.story == "absorb → repeat from 2"


def test_span_mode():
    r = explain(ANC, own=False, fresh=False, base=65530, wrap=65536)
    assert r.pos(7) == 1
    assert r.story == "absorb×64 → alloc ? → copy×? → divide(16) → jump into the executor"
    assert r.rows[-1].note.startswith("go to the executor's start")
    assert "@" not in r.text().splitlines()[0]


def test_decode():
    assert decode(bytes([23]), 0).op == "pad"          # unassigned opcode
    assert decode(bytes([0xF3]), 0).text == "self 7"   # printed raw, read as self 2
    assert decode(bytes([0xF3]), 0).reg == 2
    assert decode(bytes([OPCODE["lit"]]), 0).text == "lit A ?"
    assert decode(asm("lit D -4"), 0).val == -4


def test_random_bytes_do_not_raise():
    rng = random.Random(1)
    for _ in range(500):
        code = bytes(rng.randrange(256) for _ in range(rng.choice([1, 2, 7, 21, 41, 100])))
        explain(code).text(ip=0)
        explain(code, own=False, fresh=False, base=65000, wrap=65536).text()
