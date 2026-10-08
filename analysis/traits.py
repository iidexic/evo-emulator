"""Trait tracker: follow single genome bytes through a run, in tick bins.

E007 found that raw-hash sweep and diversity measures miss a sweep of one
trait (the absorb count, byte 6 of the ancestor) because bit-7 flips in
register operands make many raw genotypes synonymous. This reads a trait
byte directly. Per bin, over exact births (child == executor's body at
`divide`) by replicator-class parents of bodies of one length (default
21), it gives for each trait: n, median, 10th and 90th percentile, share
at the ancestor's value, share at or above a threshold, and the share
excluded because the guard byte (the `lit` that loads the trait byte) is
no longer a `lit` op. The guard is checked at its fixed offset only; a
body whose instruction alignment shifted before it is not detected. The
byte is read as encoded: a loop that counts the other way is not followed
(E007 seed 3 has `lit A -114 ; inc A`, which absorbs 114 times, and its
absorb median is negative from window 7), so look at the code when a
median jumps sign.

Per bin it also counts genotypes with >= 2 exact births, by raw hash and
by canonical `func_hash`, over all exact births in the bin (`geno_raw`,
`geno_func`; `geno_raw` is E007's `genotypes`) and over the trait births
only (`geno_raw_sel`, `geno_func_sel`), and gives the leading
replicator-class canonical genotype and its share of all the bin's exact
births (`top_func_hash`, `top_func_share`; E007's `top_share` by raw hash).

Bins follow the E007 windows: bin k holds ticks ((k-1)*BIN, k*BIN].

    from traits import track
    t = track("../runs/e007/std/s1", bin_size=25_000)

    uv run traits.py ../runs/e007/std/s1 --bin 25000 [--len 21] [--out CSV]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from evo_run import Run, load

LIT = 17  # an op byte is `lit` when byte & 0x1f == LIT


@dataclass(frozen=True)
class Trait:
    name: str
    offset: int          # byte offset in the body
    signed: bool         # read as a signed byte (a `lit` operand is)
    guard: int | None    # offset that must hold a `lit` op, or None
    ancestor: int        # the ancestor's value
    threshold: int       # report the share >= this

    @property
    def ge(self) -> str:
        return f"{self.name}_ge{self.threshold}"


# Ancestor 13325271fc11401605086c5a1845486c11101c130d:
# byte 5 `lit A`, byte 6 the absorb-loop count; byte 16 `lit A`, byte 17
# the endowment given at `divide`.
ABSORB = Trait("absorb", offset=6, signed=True, guard=5, ancestor=64, threshold=96)
ENDOW = Trait("endow", offset=17, signed=True, guard=16, ancestor=16, threshold=37)
DEFAULTS = (ABSORB, ENDOW)


def _byte(off: int, signed: bool) -> pl.Expr:
    v = pl.col("bytes_hex").str.slice(2 * off, 2).str.to_integer(base=16, strict=False)
    return pl.when(v >= 128).then(v - 256).otherwise(v) if signed else v


def exact_births(run: Run, bin_size: int) -> pl.DataFrame:
    """Exact births with `bin`, the parent's harness `class` (`unknown`
    without classes.csv), `func_hash` and `bytes_hex`."""
    b = run.births.filter(pl.col("raw_hash") == pl.col("parent_now_hash")).select(
        "tick", "len", "raw_hash",
        bin=((pl.col("tick") + bin_size - 1) // bin_size).cast(pl.Int64),
    )
    b = run.class_of(b, "raw_hash")
    return b.join(run.genomes.select("raw_hash", "func_hash", "bytes_hex"), on="raw_hash", how="left")


def _genotypes(df: pl.DataFrame, col: str) -> pl.DataFrame:
    return df.group_by("bin", col).len().filter(pl.col("len") >= 2).group_by("bin").len()


def track(
    run: Run | str | Path,
    bin_size: int = 25_000,
    traits: tuple[Trait, ...] | list[Trait] = DEFAULTS,
    length: int = 21,
) -> pl.DataFrame:
    """One row per bin with births; columns as in the module docstring.
    Without classes.csv the class filter is dropped (all exact births of
    the given length) and a note goes to stderr."""
    if not isinstance(run, Run):
        run = load(run)
    ex = exact_births(run, bin_size)
    has_classes = run.classes is not None
    if not has_classes:
        print(f"traits: no classes.csv in {run.dir}; using all exact births, not replicator-class only",
              file=sys.stderr)
    rep = pl.col("class") == "replicator" if has_classes else pl.lit(True)
    sel = ex.filter(rep & (pl.col("len") == length))

    bins = ex.group_by("bin").agg(exact=pl.len()).with_columns(tick_end=pl.col("bin") * bin_size)
    out = bins.join(sel.group_by("bin").agg(n=pl.len()), on="bin", how="left")

    for t in traits:
        ok = (pl.col("bytes_hex").str.slice(2 * t.guard, 2).str.to_integer(base=16, strict=False) & 0x1F) == LIT \
            if t.guard is not None else pl.lit(True)
        s = sel.with_columns(ok=ok, v=_byte(t.offset, t.signed))
        inc = s.filter(pl.col("ok"))
        agg = s.group_by("bin").agg(**{f"{t.name}_excl": 1 - pl.col("ok").mean()}).join(
            inc.group_by("bin").agg(**{
                f"{t.name}_n": pl.len(),
                f"{t.name}_med": pl.col("v").median(),
                f"{t.name}_p10": pl.col("v").quantile(0.1, "linear"),
                f"{t.name}_p90": pl.col("v").quantile(0.9, "linear"),
                f"{t.name}_anc": (pl.col("v") == t.ancestor).mean(),
                t.ge: (pl.col("v") >= t.threshold).mean(),
            }),
            on="bin", how="left",
        )
        out = out.join(agg, on="bin", how="left")

    top = (
        ex.filter(rep).group_by("bin", "func_hash").len()
        .sort(["bin", "len", "func_hash"], descending=[False, True, False])
        .group_by("bin", maintain_order=True).first()
        .select("bin", top_func_hash="func_hash", top_n="len")
    )
    out = (
        out.join(_genotypes(ex, "raw_hash").rename({"len": "geno_raw"}), on="bin", how="left")
        .join(_genotypes(ex, "func_hash").rename({"len": "geno_func"}), on="bin", how="left")
        .join(_genotypes(sel, "raw_hash").rename({"len": "geno_raw_sel"}), on="bin", how="left")
        .join(_genotypes(sel, "func_hash").rename({"len": "geno_func_sel"}), on="bin", how="left")
        .join(top, on="bin", how="left")
        .with_columns(top_func_share=pl.col("top_n") / pl.col("exact"))
        .drop("top_n")
        .with_columns(pl.col(c).fill_null(0) for c in ("n", "geno_raw", "geno_func", "geno_raw_sel", "geno_func_sel"))
    )
    return out.sort("bin").select("bin", "tick_end", pl.exclude("bin", "tick_end"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir")
    ap.add_argument("--bin", type=int, default=25_000)
    ap.add_argument("--len", type=int, default=21, dest="length")
    ap.add_argument("--out", help="CSV path (default RUN_DIR/traits_<bin>.csv)")
    a = ap.parse_args()
    df = track(a.run_dir, a.bin, DEFAULTS, a.length)
    out = Path(a.out) if a.out else Path(a.run_dir) / f"traits_{a.bin}.csv"
    df.write_csv(out)
    show = df.drop("top_func_hash").with_columns(pl.selectors.float().round(3))
    with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=400, tbl_hide_dataframe_shape=True,
                   tbl_hide_column_data_types=True):
        print(show)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
