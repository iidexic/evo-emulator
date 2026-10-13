"""E014 pilot re-read: the entered/unentered children-per-tick ratio on
reproducing deaths only (offspring > 0, age > 50), normalised to the n0
arm of the same genome and seed.

The runner's `entered_rate_norm` is computed over every replicator-class
death and is confounded (its raw ratio is 0.54 with no cost); this set
gives 0.83-0.85 with no cost and a clean dose under theft. Written
2026-10-13 from the pilot; see the E014 record.

    uv run e014_pilot_reproducers.py [--root ../runs/e014_pilot]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

RULES = ["n0", "t25", "t50", "t75", "tax"]
GENOMES = ["eject", "inert", "resident"]
SEEDS = [1, 2, 3]
INJECT = 25_000


def one(root: Path, rule: str, genome: str, seed: int) -> tuple[float, float, float, float]:
    d = pl.read_csv(root / f"{rule}_{genome}" / f"s{seed}" / "deaths.csv.gz",
                    columns=["tick", "age", "offspring", "exec_by_others", "cycles_lost_m"])
    d = d.filter((pl.col("tick") > INJECT) & (pl.col("age") > 50) & (pl.col("offspring") > 0))
    d = d.with_columns((pl.col("offspring") / pl.col("age")).alias("cpt"))
    u = d.filter(pl.col("exec_by_others") == 0)
    e = d.filter(pl.col("exec_by_others") > 0)
    lost = e["cycles_lost_m"] / e["age"]
    return e["cpt"].mean() / u["cpt"].mean(), e.height / d.height, lost.median(), lost.mean()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).parent.parent / "runs" / "e014_pilot")
    a = ap.parse_args()
    res = {(r, g, s): one(a.root, r, g, s) for r in RULES for g in GENOMES for s in SEEDS}
    print("rule genome | ratio s1 s2 s3 | norm vs n0 s1 s2 s3 | mean norm | entered share of reproducers "
          "| entered debit per tick median/mean (milli)")
    for r in RULES:
        for g in GENOMES:
            ratios = [res[(r, g, s)][0] for s in SEEDS]
            norms = [res[(r, g, s)][0] / res[("n0", g, s)][0] for s in SEEDS]
            print(r, g, "|", " ".join(f"{x:.3f}" for x in ratios), "|",
                  " ".join(f"{x:.3f}" for x in norms), f"| {sum(norms) / len(norms):.3f} |",
                  " ".join(f"{res[(r, g, s)][1] * 100:.1f}%" for s in SEEDS), "|",
                  " ".join(f"{res[(r, g, s)][2]:.0f}/{res[(r, g, s)][3]:.0f}" for s in SEEDS))


if __name__ == "__main__":
    main()
