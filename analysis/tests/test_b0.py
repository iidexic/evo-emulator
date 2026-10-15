"""Tests for b0_density.py (T07 §2): the Clopper-Pearson interval, the cell
list and the summary, on synthetic files (no binary).

    uv run --project analysis --with pytest pytest analysis/tests/test_b0.py
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import b0_density as b0  # noqa: E402


def test_betainc_closed_forms():
    # I_x(1, b) = 1 - (1 - x)^b and I_x(a, 1) = x^a.
    for x in (1e-9, 1e-4, 0.3, 0.9):
        for b in (1.0, 7.0, 1e6):
            assert b0.betainc(1.0, b, x) == pytest.approx(-math.expm1(b * math.log1p(-x)), rel=1e-10, abs=1e-300)
        for a in (2.0, 5.0):
            assert b0.betainc(a, 1.0, x) == pytest.approx(x**a, rel=1e-10)


def test_clopper_pearson_table_values():
    # The textbook exact intervals at n = 10.
    lo, hi = b0.clopper_pearson(1, 10)
    assert (lo, hi) == (pytest.approx(0.002529, abs=1e-6), pytest.approx(0.445016, abs=1e-6))
    lo, hi = b0.clopper_pearson(5, 10)
    assert (lo, hi) == (pytest.approx(0.187086, abs=1e-6), pytest.approx(0.812914, abs=1e-6))
    lo, hi = b0.clopper_pearson(10, 10)
    assert (lo, hi) == (pytest.approx(0.025 ** 0.1, rel=1e-9), 1.0)


def test_clopper_pearson_zero_and_rare():
    # Zero hits: 1 - 0.025^(1/N), about 3.7 / N (spec §2).
    for n in (10**6, 10**7):
        lo, hi = b0.clopper_pearson(0, n)
        assert lo == 0.0
        assert hi == pytest.approx(1 - 0.025 ** (1 / n), rel=1e-6)
        assert hi * n == pytest.approx(3.689, abs=1e-3)
    # One hit in 10^7: the Poisson limits 0.0253 / N and 5.572 / N.
    lo, hi = b0.clopper_pearson(1, 10**7)
    assert lo * 1e7 == pytest.approx(0.02532, rel=1e-3)
    assert hi * 1e7 == pytest.approx(5.5716, rel=1e-3)
    # The beta-quantile form against the binomial tail it inverts.
    k, n = 3, 2_000_000
    lo, hi = b0.clopper_pearson(k, n)

    def cdf(p, upto):
        return sum(math.exp(math.lgamma(n + 1) - math.lgamma(j + 1) - math.lgamma(n - j + 1)
                            + j * math.log(p) + (n - j) * math.log1p(-p)) for j in range(upto + 1))

    assert cdf(hi, k) == pytest.approx(0.025, rel=1e-6)
    assert 1 - cdf(lo, k - 1) == pytest.approx(0.025, rel=1e-6)


def test_cells():
    main = b0.main_cells()
    assert len(main) == 8 * 2 + 2
    assert {c.n for c in main} == {10**6}
    assert sorted(c.seed for c in main if c.ticks == 3000) == [1, 2]
    assert {c.len for c in main if c.ticks == 3000} == {21}
    big = b0.big_cells()
    assert sorted({c.len for c in big}) == [8, 12, 16] and {c.n for c in big} == {10**7} and len(big) == 6
    assert len(b0.big_cells(max_len=32)) == 12
    assert b0.Cell(21, 3000, 10**6, 2).name == "L21_T3000_N1000000_s2"


def test_parse_summary():
    s = b0.parse_summary(f"{b0.SUMMARY_HEADER}\n21,10000,1000,0,1,93,7,9899,0.03\n")
    assert s == {"len": 21, "n": 10000, "ticks": 1000, "replicator": 0, "one_shot": 1, "inexact": 93,
                 "loafer": 7, "dies": 9899, "seconds": 0.03}
    with pytest.raises(ValueError):
        b0.parse_summary("tick,alive\n1,1\n")


def _row(cell: b0.Cell, rep: int = 0, one: int = 0, secs: float = 1.0) -> dict:
    inexact, loafer = 5, 2
    return {"len": cell.len, "n": cell.n, "ticks": cell.ticks, "seed": cell.seed, "replicator": rep,
            "one_shot": one, "inexact": inexact, "loafer": loafer, "dies": cell.n - rep - one - inexact - loafer,
            "seconds": secs, "threads": 8}


def test_summary_on_synthetic_cells(tmp_path):
    out = tmp_path / "b0"
    (out / "cells").mkdir(parents=True)
    rows = {}
    for c in b0.main_cells(n=1000):
        hit = c.len == 8 and c.seed == 2 and c.ticks == 1000
        rows[c] = _row(c, rep=1 if hit else 0)
        with open(out / "cells" / f"{c.name}.csv", "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["index", "hex", "class", "births", "exact_births", "first_birth_tick", "executed"])
            w.writerow([3, "00" * c.len, "inexact", 1, 0, 1, 9])
            if hit:
                w.writerow([17, "13325271fc11", "replicator", 40, 40, 13, 5000])
    # A larger cell for one seed supersedes its smaller one in the headline.
    big = b0.Cell(8, 1000, 10_000, 1)
    rows[big] = _row(big)
    (out / "cells" / f"{big.name}.csv").write_text("index,hex,class,births,exact_births,first_birth_tick,executed\n")
    b0.write_rows(out, rows)
    assert b0.load_rows(out) == rows
    head = {(h["len"], h["ticks"]): h for h in b0.headline(rows)}
    assert head[(8, 1000)]["n"] == 11_000 and head[(8, 1000)]["rep"] == 1
    assert head[(21, 3000)]["n"] == 2000
    text = b0.write_summary(out, rows, exe=None)
    assert (out / "summary.md").read_text(encoding="utf-8") == text
    assert "| 8 | 1,000 | 11,000 | 1,2 | 1 | 9.09e-05 |" in text
    assert "§3 bullet 3 met" in text and "`13325271fc11`" in text
    assert "inexact" not in text.split("## Replicators")[1]
    # No hits at LEN 21-24 and no 10^7 cells: no other bullet, and the
    # resolution line says why.
    assert "bullet 1 met" not in text and "bullet 2 met" not in text
    assert "Neither the first nor the second bullet" in text and "Resolution" in text


def test_decision_negative_branch():
    rows = {}
    for c in b0.big_cells(max_len=32) + b0.main_cells():
        rows[c] = _row(c)
    lines = b0.decision(b0.headline(rows))
    assert any("§3 bullet 2 met" in x for x in lines)
    # With the 10^7 pass only to LEN 16 (§2's default) the clause is not met.
    rows = {c: _row(c) for c in b0.big_cells() + b0.main_cells()}
    lines = b0.decision(b0.headline(rows))
    assert not any("bullet 2 met" in x for x in lines)
    assert any("--big-max-len 32" in x for x in lines)
