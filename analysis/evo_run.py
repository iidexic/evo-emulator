"""Load an evo-core run directory into polars frames.

File formats are specified in docs/instrumentation.md. Energy columns in the
files are integer milli-units with a `_m` suffix; `load` also adds each one
in energy units without the suffix (e.g. `energy_m` -> `energy`).

    from evo_run import load
    run = load("../runs/diag/control_s1")
    run.deaths.filter(pl.col("offspring") == 0)
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "evo-core"
MILLI = 1000

# Hash columns are 16 hex digits; without an override polars would parse an
# all-digit hash as an integer.
HASH_COLS = {
    "births": ["raw_hash", "parent_hash", "parent_now_hash", "source_hash"],
    "deaths": ["birth_hash", "now_hash"],
    "census": ["now_hash"],
    "orgs": ["birth_hash", "now_hash"],
    "patches": [],
    "genomes": ["raw_hash", "func_hash", "parent_hash", "bytes_hex"],
    "classes": ["raw_hash"],
}

CLASSES = ["replicator", "one_shot", "inexact", "loafer", "dies", "unknown"]


@dataclass
class Run:
    dir: Path
    meta: dict
    births: pl.DataFrame
    deaths: pl.DataFrame
    census: pl.DataFrame
    orgs: pl.DataFrame
    patches: pl.DataFrame
    genomes: pl.DataFrame
    classes: pl.DataFrame | None

    def class_of(self, df: pl.DataFrame, hash_col: str, out: str = "class") -> pl.DataFrame:
        """Join the harness class of `hash_col` onto `df` as column `out`.
        Hashes missing from classes.csv get `unknown`."""
        if self.classes is None:
            return df.with_columns(pl.lit("unknown").alias(out))
        c = self.classes.select(pl.col("raw_hash").alias(hash_col), pl.col("class").alias(out))
        return df.join(c, on=hash_col, how="left").with_columns(pl.col(out).fill_null("unknown"))


def binary() -> Path:
    """Build evo-core in release mode and return the binary's path."""
    subprocess.run(["cargo", "build", "--release", "--quiet"], cwd=CORE, check=True)
    for name in ("evo-core.exe", "evo-core"):
        p = CORE / "target" / "release" / name
        if p.exists():
            return p
    raise FileNotFoundError("evo-core binary not found after build")


def classify(run_dir: str | Path, harness_ticks: int = 3000) -> None:
    """Run the single-genome harness on every genome; writes classes.csv."""
    subprocess.run(
        [str(binary()), "--classify", str(run_dir), "--harness-ticks", str(harness_ticks)],
        check=True,
    )


def disasm(data: bytes | np.ndarray) -> str:
    """Disassemble bytes with evo-core (`--disasm`), e.g. a slice of a world
    snapshot: `disasm(w.bytes[17:40])`."""
    hx = bytes(data).hex()
    return subprocess.run([str(binary()), "--disasm", hx], capture_output=True, text=True, check=True).stdout.strip()


@dataclass
class World:
    """One world snapshot: `bytes[a]` is the byte at address a, `state[a]`
    is 0 free, 1 debris, 2 owned by a living organism."""
    tick: int
    bytes: np.ndarray
    state: np.ndarray


def world(run_dir: str | Path) -> dict[int, World]:
    """Every world snapshot in RUN_DIR/world.bin, keyed by tick (written at
    census ticks since 2026-10-07; older runs have no file and get {})."""
    p = Path(run_dir) / "world.bin"
    if not p.exists():
        return {}
    raw = np.fromfile(p, dtype=np.uint8)
    out: dict[int, World] = {}
    pos = 0
    while pos + 12 <= raw.size:
        tick = int(raw[pos:pos + 8].view(np.uint64)[0])
        n = int(raw[pos + 8:pos + 12].view(np.uint32)[0])
        pos += 12
        out[tick] = World(tick, raw[pos:pos + n].copy(), raw[pos + n:pos + 2 * n].copy())
        pos += 2 * n
    return out


# Non-hash text columns. Everything else is numeric.
TEXT_COLS = {"cause", "op_at_ip", "origin", "disasm", "class", "alive"}


def _read(path: Path, name: str) -> pl.DataFrame:
    df = pl.read_csv(path, schema_overrides={c: pl.Utf8 for c in HASH_COLS[name]})
    if df.height == 0:
        # A header-only file (no births yet, no deaths) infers every column
        # as text; give the numeric ones their real type.
        df = df.with_columns(
            pl.col(c).cast(pl.Int64) for c in df.columns if c not in TEXT_COLS and c not in HASH_COLS[name]
        )
    units = [
        (pl.col(c) / MILLI).alias(c[:-2])
        for c in df.columns
        if c.endswith("_m") and c[:-2] not in df.columns
    ]
    return df.with_columns(units) if units else df


def load(run_dir: str | Path) -> Run:
    d = Path(run_dir)
    meta = json.loads((d / "meta.json").read_text())
    frames = {n: _read(d / f"{n}.csv", n) for n in HASH_COLS if n != "classes"}
    classes = _read(d / "classes.csv", "classes") if (d / "classes.csv").exists() else None
    return Run(dir=d, meta=meta, classes=classes, **frames)
