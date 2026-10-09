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

E009 additions (`track_genome`, separate from `track`, whose columns are
unchanged). Over replicator-class exact births of any length per bin
(`rep_n`), each genome parsed once as `isa::canonical` does (linearly from
byte 0, a `lit` taking its operand byte; register ops keep `mod & 3`,
`self` keeps `min(mod, 2)`, other ops modifier 0, unassigned opcodes become
`pad`; docs/instrumentation.md, "Two genome hashes"):

- `len_med`, `len_p10`, `len_p90`: body length.
- Endowment located by pattern, not offset: the first `lit R v` whose next
  instruction is `divide R` with the same register (`divide` gives the
  child the value of its register), read as a signed byte. Over births of
  bodies of 21 bytes or more (`endow_all_n`): `endow_all_ge37` is the share
  with v >= 37 where a body with no such pair counts as below; `endow_all_nolit`
  is the share with no pair; `endow_all_med/_p10/_p90` are over bodies with a
  pair. Misses: an endowment loaded by any other route (`lit` then `inc`,
  a `lit` separated from `divide` by another instruction, a register copied
  by `swap`), a pair hidden by a misaligned parse (a stray `lit` op earlier
  swallowing the `divide`'s `lit`), and a second pair after the first (only
  the first in parse order is read; execution order is not followed).
- `self1_share`: the canonical genome has `self 1` at an instruction
  position (not inside a `lit` operand). Presence, not execution.
- `first_not_self0_share`: the first canonical instruction is not `self 0`.
- `prefix_k` (k = 0..5): share whose longest match at byte 0 of
  `self 1 ; swap C ; self 0 ; sub C ; jmpr A` (the self-scan prefix, E009;
  the IP is kept in C because `self 0` writes B as well as A)
  is k instructions, compared on canonical instructions, so a bit-7 flip
  of a register op still matches; a flip that changes `self 1` to
  `self 5` does not, because that is `self 2`. `prefix_ge3` is k >= 3.
  Other prefixes are passed as `prefix=`: INERT (E009a), and for E010
  EJECT (`self 1 ; swap C ; self 0 ; sub C ; skipz A ; jmpa D`) and
  INERT6 (six `zero D`), six pairs each, so k = 0..6.

    from traits import track
    t = track("../runs/e007/std/s1", bin_size=25_000)
    g = track_genome("../runs/e007/std/s1", bin_size=25_000)

    uv run traits.py ../runs/e007/std/s1 --bin 25000 [--len 21] [--out CSV] [--genome]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from itertools import pairwise
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


# --- E009: canonical parse, endowment by pattern, self-scan prefix --------------

SELF, SWAP, SUB, JMPR, DIVIDE = 19, 18, 15, 12, 28
# Opcodes that read the register-select modifier (`isa::uses_reg`).
USES_REG = {4, 5, 6, 7, 14, 15, 16, LIT, SWAP, 20, 21, 8, 9, JMPR, 13, 26, DIVIDE}
ASSIGNED = {0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 26, 28}
# `self 1 ; swap C ; self 0 ; sub C ; jmpr A` as canonical (op, modifier).
# Registers: A = 0, B = 1, C = 2, D = 3. C, not B: `self 0` overwrites B.
PREFIX = ((SELF, 1), (SWAP, 2), (SELF, 0), (SUB, 2), (JMPR, 0))
# E009a's control: five `zero D` (byte 0x70: op ZERO = 16, register D = 3
# in modifier bits 5-6), the same length as PREFIX and no effect, because
# the ancestor's `lit D -4` resets D.
ZERO = 16
INERT = ((ZERO, 3),) * 5
# E010's `eject`: `self 1 ; swap C ; self 0 ; sub C ; skipz A ; jmpa D`
# (bytes 33 52 13 4f 08 6d). The host (A = 0) skips the `jmpa`; an
# intruder jumps to the absolute address in its D. SKIPZ = 8 and JMPA = 13
# read their register (`isa::uses_reg`). INERT6 is its length control, six
# `zero D` (byte 0x70).
SKIPZ, JMPA = 8, 13
EJECT = ((SELF, 1), (SWAP, 2), (SELF, 0), (SUB, 2), (SKIPZ, 0), (JMPA, 3))
INERT6 = ((ZERO, 3),) * 6
ENDOW_MIN_LEN = 21


def canonical_instrs(body: bytes) -> list[tuple[int, int, int | None]]:
    """(op, canonical modifier, lit operand or None) per instruction, parsed
    linearly from byte 0 as `isa::canonical` does. A `lit` at the last byte
    has no operand (None)."""
    out = []
    i = 0
    while i < len(body):
        op, m = body[i] & 0x1F, body[i] >> 5
        if op not in ASSIGNED:
            op = 0
        cm = m & 3 if op in USES_REG else (min(m, 2) if op == SELF else 0)
        v = None
        if op == LIT and i + 1 < len(body):
            v = body[i + 1]
            v = v - 256 if v >= 128 else v
            i += 1
        out.append((op, cm, v))
        i += 1
    return out


def genome_features(bytes_hex: str, prefix: tuple[tuple[int, int], ...] = PREFIX) -> dict:
    """E009 per-genome features: endowment by pattern, `self 1` presence,
    first instruction, length of the longest match of `prefix` (canonical
    (op, modifier) pairs; default the self-scan) at byte 0 (module docstring)."""
    ins = canonical_instrs(bytes.fromhex(bytes_hex))
    endow = None
    for (op, m, v), (op2, m2, _) in pairwise(ins):
        if op == LIT and v is not None and op2 == DIVIDE and m2 == m:
            endow = v
            break
    k = 0
    while k < len(prefix) and k < len(ins) and ins[k][:2] == prefix[k]:
        k += 1
    return {
        "endow_pat": endow,
        "has_self1": any(op == SELF and m == 1 for op, m, _ in ins),
        "first_self0": bool(ins) and ins[0][:2] == (SELF, 0),
        "prefix": k,
    }


def track_genome(run: Run | str | Path, bin_size: int = 25_000,
                 prefix: tuple[tuple[int, int], ...] = PREFIX) -> pl.DataFrame:
    """One row per bin with replicator-class exact births; E009 columns as in
    the module docstring. `prefix` is the sequence the `prefix_k` histogram
    matches at byte 0 (default the self-scan, PREFIX; E009a also passes
    INERT), with columns `prefix_0` .. `prefix_<len(prefix)>`. Without
    classes.csv all exact births are used."""
    if not isinstance(run, Run):
        run = load(run)
    ex = exact_births(run, bin_size)
    if run.classes is None:
        print(f"traits: no classes.csv in {run.dir}; using all exact births, not replicator-class only",
              file=sys.stderr)
    else:
        ex = ex.filter(pl.col("class") == "replicator")
    hexes = ex.select("raw_hash", "bytes_hex").unique("raw_hash").drop_nulls()
    feats = pl.DataFrame(
        [{"raw_hash": h, **genome_features(x, prefix)} for h, x in hexes.iter_rows()],
        schema={"raw_hash": pl.Utf8, "endow_pat": pl.Int64, "has_self1": pl.Boolean,
                "first_self0": pl.Boolean, "prefix": pl.Int64},
    )
    ex = ex.join(feats, on="raw_hash", how="left")
    long_ = pl.col("len") >= ENDOW_MIN_LEN
    e_ok = long_ & pl.col("endow_pat").is_not_null()
    out = ex.group_by("bin").agg(
        rep_n=pl.len(),
        len_med=pl.col("len").median(),
        len_p10=pl.col("len").quantile(0.1, "linear"),
        len_p90=pl.col("len").quantile(0.9, "linear"),
        endow_all_n=long_.sum(),
        endow_all_ge37=(long_ & (pl.col("endow_pat") >= ENDOW.threshold).fill_null(False)).sum() / long_.sum(),
        endow_all_nolit=(long_ & pl.col("endow_pat").is_null()).sum() / long_.sum(),
        endow_all_med=pl.col("endow_pat").filter(e_ok).median(),
        endow_all_p10=pl.col("endow_pat").filter(e_ok).quantile(0.1, "linear"),
        endow_all_p90=pl.col("endow_pat").filter(e_ok).quantile(0.9, "linear"),
        self1_share=pl.col("has_self1").mean(),
        first_not_self0_share=1 - pl.col("first_self0").cast(pl.Float64).mean(),
        prefix_ge3=(pl.col("prefix") >= 3).mean(),
        **{f"prefix_{k}": (pl.col("prefix") == k).mean() for k in range(len(prefix) + 1)},
    ).with_columns(
        # 0/0 when a bin has no long bodies
        pl.when(pl.col("endow_all_n") > 0).then(pl.col(c)).otherwise(None).alias(c)
        for c in ("endow_all_ge37", "endow_all_nolit")
    ).with_columns(tick_end=pl.col("bin") * bin_size)
    return out.sort("bin").select("bin", "tick_end", pl.exclude("bin", "tick_end"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir")
    ap.add_argument("--bin", type=int, default=25_000)
    ap.add_argument("--len", type=int, default=21, dest="length")
    ap.add_argument("--out", help="CSV path (default RUN_DIR/traits_<bin>.csv, or genome_traits_<bin>.csv)")
    ap.add_argument("--genome", action="store_true", help="E009 columns (track_genome) instead of track")
    a = ap.parse_args()
    if a.genome:
        df = track_genome(a.run_dir, a.bin)
        out = Path(a.out) if a.out else Path(a.run_dir) / f"genome_traits_{a.bin}.csv"
    else:
        df = track(a.run_dir, a.bin, DEFAULTS, a.length)
        out = Path(a.out) if a.out else Path(a.run_dir) / f"traits_{a.bin}.csv"
    df.write_csv(out)
    show = df.drop("top_func_hash", strict=False).with_columns(pl.selectors.float().round(3))
    with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=400, tbl_hide_dataframe_shape=True,
                   tbl_hide_column_data_types=True):
        print(show)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
