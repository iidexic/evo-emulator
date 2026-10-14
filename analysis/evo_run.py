"""Load an evo-core run directory into polars frames.

File formats are specified in docs/instrumentation.md. Energy columns in the
files are integer milli-units with a `_m` suffix; `load` also adds each one
in energy units without the suffix (e.g. `energy_m` -> `energy`).

    from evo_run import load
    run = load("../runs/diag/control_s1")
    run.deaths.filter(pl.col("offspring") == 0)

Each file may also be stored gzipped as NAME.gz (the E014 runner
compresses every CSV but patches.csv, and world.bin, after each run);
`load` and `world` read whichever is there, the plain file if both are.
`csv_path(run_dir, name)` gives the path for scripts that scan a file
themselves (polars' read_csv and scan_csv decompress gzip as of 1.44).
`evo-core --classify` needs a plain genomes.csv: `classify` here restores
one from genomes.csv.gz first, and `gunzip_verified` undoes any file.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
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


CHUNK = 1 << 20


def gzip_verified(src: Path) -> tuple[int, int]:
    """Replace `src` by `src`.gz: compress to a temporary file (level 6),
    read it back and compare SHA-256 with the original, then rename it into
    place and delete the original. A stale .gz is replaced. Returns (plain
    bytes, gzip bytes)."""
    src = Path(src)
    dst, tmp = src.with_name(src.name + ".gz"), src.with_name(src.name + ".gz.tmp")
    h_in, h_out = hashlib.sha256(), hashlib.sha256()
    with open(src, "rb") as fi, gzip.open(tmp, "wb", compresslevel=6) as fo:
        while chunk := fi.read(CHUNK):
            h_in.update(chunk)
            fo.write(chunk)
    with gzip.open(tmp, "rb") as fi:
        while chunk := fi.read(CHUNK):
            h_out.update(chunk)
    if h_in.digest() != h_out.digest():
        tmp.unlink()
        raise RuntimeError(f"{src}: gzip read-back differs; plain file kept")
    plain = src.stat().st_size
    os.replace(tmp, dst)
    src.unlink()
    return plain, dst.stat().st_size


def gunzip_verified(gz: Path, keep_gz: bool = False) -> Path:
    """Write NAME from NAME.gz (gzip checks its own CRC on the way), read the
    written file back and compare SHA-256, then delete the .gz unless
    `keep_gz`. Returns the plain path."""
    gz = Path(gz)
    dst = gz.with_suffix("")
    tmp = dst.with_name(dst.name + ".tmp")
    h_in, h_out = hashlib.sha256(), hashlib.sha256()
    with gzip.open(gz, "rb") as fi, open(tmp, "wb") as fo:
        while chunk := fi.read(CHUNK):
            h_in.update(chunk)
            fo.write(chunk)
    with open(tmp, "rb") as fi:
        while chunk := fi.read(CHUNK):
            h_out.update(chunk)
    if h_in.digest() != h_out.digest():
        tmp.unlink()
        raise RuntimeError(f"{gz}: decompressed file reads back differently; .gz kept")
    os.replace(tmp, dst)
    if not keep_gz:
        gz.unlink()
    return dst


def classify(run_dir: str | Path, harness_ticks: int = 3000) -> None:
    """Run the single-genome harness on every genome; writes classes.csv.
    The binary reads a plain genomes.csv: if the run has only
    genomes.csv.gz, a plain copy is written next to it first (the .gz is
    kept; the plain file is read in preference)."""
    d = Path(run_dir)
    if not (d / "genomes.csv").exists() and (d / "genomes.csv.gz").exists():
        gunzip_verified(d / "genomes.csv.gz", keep_gz=True)
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
    """Every world snapshot in RUN_DIR/world.bin (or world.bin.gz), keyed by
    tick (written at census ticks since 2026-10-07; older runs have no file
    and get {})."""
    d = Path(run_dir)
    p, pz = d / "world.bin", d / "world.bin.gz"
    if p.exists():
        raw = np.fromfile(p, dtype=np.uint8)
    elif pz.exists():
        with gzip.open(pz, "rb") as f:
            raw = np.frombuffer(f.read(), dtype=np.uint8)
    else:
        return {}
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


def csv_path(run_dir: str | Path, name: str) -> Path | None:
    """RUN_DIR/NAME.csv, or NAME.csv.gz if only that exists; None if neither."""
    d = Path(run_dir)
    for p in (d / f"{name}.csv", d / f"{name}.csv.gz"):
        if p.exists():
            return p
    return None


def _read(path: Path, name: str) -> pl.DataFrame:
    over = {c: pl.Utf8 for c in HASH_COLS[name]}
    if path.suffix == ".gz":
        try:
            df = pl.read_csv(path, schema_overrides=over)
        except Exception:
            # A polars build without gzip support: decompress here.
            with gzip.open(path, "rb") as f:
                df = pl.read_csv(io.BytesIO(f.read()), schema_overrides=over)
    else:
        df = pl.read_csv(path, schema_overrides=over)
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


def complete(run_dir: str | Path) -> bool:
    """Whether RUN_DIR has every file `load` reads. evo-core writes
    genomes.csv and the final meta.json last, so a run still going, or one
    killed before its end, is not complete: it has no genomes.csv."""
    d = Path(run_dir)
    return (d / "meta.json").exists() and all(csv_path(d, n) for n in HASH_COLS if n != "classes")


def _natural(name: str) -> list:
    """Sort key that puts s2 before s10."""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def run_sets(need_world: bool = False) -> dict[str, dict[str, Path]]:
    """The complete runs under runs/, grouped into sets for the notebooks'
    two run pickers: {set label: {run label: run directory}}.

    A set is the folder holding the run directories (`e004/far`, `diag`; a
    run directly under runs/ is a set of its own), and a run is its folder
    name (`s1`). Every label ends in ` | yyyymmdd`: for a run, the date of
    its meta.json, which evo-core rewrites at the end, so the day the run
    finished; for a set, the date of its earliest run. Sets come newest
    first by the time of their earliest run; runs newest day first, then
    by name (s2 before s10), since seeds of one batch finish in no useful
    order. `need_world`: only runs with world snapshots (world.bin or
    world.bin.gz)."""
    root = ROOT / "runs"
    sets: dict[str, list[tuple[float, str, Path]]] = {}
    for p in root.rglob("meta.json"):
        d = p.parent
        if not complete(d):
            continue
        if need_world and not ((d / "world.bin").exists() or (d / "world.bin.gz").exists()):
            continue
        rel = d.relative_to(root)
        key = (rel.parent if rel.parent != Path(".") else rel).as_posix()
        sets.setdefault(key, []).append((p.stat().st_mtime, d.name, d))

    def day(t: float) -> str:
        return datetime.fromtimestamp(t).strftime("%Y%m%d")

    out = {}
    for key, runs in sorted(sets.items(), key=lambda kv: min(t for t, _, _ in kv[1]), reverse=True):
        runs.sort(key=lambda r: _natural(r[1]))
        runs.sort(key=lambda r: day(r[0]), reverse=True)  # stable: name order within a day
        first = min(t for t, _, _ in runs)
        out[f"{key} | {day(first)}"] = {f"{name} | {day(t)}": d for t, name, d in runs}
    return out


def load(run_dir: str | Path) -> Run:
    d = Path(run_dir)
    meta = json.loads((d / "meta.json").read_text())
    paths = {n: csv_path(d, n) for n in HASH_COLS}
    missing = [n for n, p in paths.items() if p is None and n != "classes"]
    if missing:
        raise FileNotFoundError(f"{d}: no {', '.join(f'{n}.csv' for n in missing)} (plain or .gz)")
    frames = {n: _read(paths[n], n) for n in HASH_COLS if n != "classes"}
    classes = _read(paths["classes"], "classes") if paths["classes"] else None
    return Run(dir=d, meta=meta, classes=classes, **frames)
