# evo-analysis

Python side of evo (PLAN.md §6.2): experiment runners and analysis of
`evo-core` output. A uv project, separate from the Rust crate; the two talk
only through files in `runs/` (§6.3).

```
cd analysis
uv sync                         # create .venv from uv.lock
uv run e002_dispersal.py        # run an experiment script
uv add <package>                # add a dependency (updates pyproject + lock)
```

Experiment runners build `evo-core` in release mode themselves, so cargo
must be on PATH. `e004_physics.py` records every run (`--out`), classifies
it, and writes `runs/e004/summary.md`; its big-world arms take about
300 MB of event files per run. `e005_parasites.py` reads the E004
p512_far runs, completes their world-physics classes
(`classes_world.csv`), and writes `runs/e005/summary.md` plus a
dependent-genome table per run.

World memory at every census tick is in `world.bin` (since 2026-10-07):
`evo_run.world(run_dir)[tick]` gives `.bytes` and `.state` (0 free, 1
debris, 2 owned) as numpy arrays, and `evo_run.disasm(w.bytes[a:b])`
decodes a slice through `evo-core --disasm`.

## Standing measures (T05)

`measures.py RUN_DIR [--every K] [--depths 187,1870] [--group COL] [--knockout] [--out DIR]`
writes QNN, tree measures, and MODES by census (`series.csv`,
`summary.json`); its `compute(run, group=...)` entry point is also
available to experiment runners. The module docstring states every
column's definition. `--group` picks the QNN components: `func_hash`
(default; genotype turnover, blind to a trait that sweeps across many
genotypes), any other `genomes.csv` column, or `absorb_class` (`lt96` /
`ge96` by `traits.py`'s absorb-count read of the body, `unmatched` where
the read does not apply), which is the trait-level sweep detector.
`--knockout` adds `sites_<window>.csv` per 25,000-tick window: for the
top replicator-class body, each site's entropy over the window's
same-length exact births against its `pad` knockout (`evo-core
--neighbours HEX --neighbours-pad-only`; the unmutated body's exact
births alone from `--classify` at the same `--harness-ticks`), with
`meaningful` = exact births below half the body's or class changed, and
a `sites` record (meaningful count, Spearman and AUC of entropy against
meaningful) in `summary.json`. The engine is `--evo-bin PATH`, else `$EVO_BIN`, else
`evo-core/target/release/evo-core.exe` (not built); `--evo-flags "..."`
passes physics flags to it. Runs recorded before T08 (2026-10-13) need
`--evo-flags "--legacy-pending-range"` with a post-T08 binary.
`measures_baseline.py` applies it to E007, E012 and E013 with both
groupings and writes the per-seed table and the shakedown criteria to
`runs/measures/summary.md`. Tests, from the repo root:
`uv run --project analysis --with pytest pytest analysis/tests/test_measures.py`.

To see what one genome does, tick by tick, without reading its
disassembly: `cargo run --release --example trace -- HEX [ticks]
[ADDR=HEX ...]` in `evo-core/` (the last form plants dead code in free
memory). To test a genome against a host: `evo-core --host HEX`, with
`--host-body HEX` to use a genome from a run as the host instead of the
ancestor (E007). `e007_long_run.py` runs the standard world for 250,000
ticks and reads it in windows (`runs/e007/summary_windows.md`).

## Line of descent (T06)

`lod.py` draws one line of descent and measures every step on it, in the
manner of Lenski, Ofria, Pennock & Adami (2003); spec
`docs/tasks/T06-lenski-lod.md`.

```
uv run lod.py RUN_DIR [--at TICK] [--pick top|id:N] [--harness-ticks 3000] [--out DIR] [--evo-bin PATH]
```

The end organism is the body with the most offspring in the largest
replicator-class `func_hash` group alive at the census `--at` (default the
last). The line runs back from it through `births.csv` (child to executor)
to the founder. Each step (consecutive birth genomes that differ) gets its
edits, whether it is synonymous, whether it was a copy error or a somatic
change in the parent, the absorb count, and its fitness. Fitness is
measured in the harness alone and with a `pad` before it, and in the world
over the step's 25,000-tick window. Output goes to `RUN_DIR/lod/`:
`steps.csv`, `genomes.csv`, `line.csv` and `summary.md`. The harness binary
is `--evo-bin`, else `$EVO_BIN`, else the cargo build.

`lod_e007.py` runs it on E007's ten seeds at tick 250,000 and writes
`runs/lod/summary.md` and `runs/lod/seeds.csv`. A seed whose E007 directory
is incomplete is rerun into `runs/lod/e007/` and checked against the
partial run. Tests: `uv run --with pytest pytest tests/test_lod.py`.

Data note. On the desktop, `runs/e007/std/s1`–`s9` are the first Windows
launch, killed at ticks 141,543–145,451 and without `genomes.csv`.
Complete reruns are at `runs/lod/e007/s<seed>/` (`lod_e007.py` makes them
when a seed is incomplete), and other analyses on this machine should read
E007 from there.

## E016 defence search

`e016_defence.py` runs E016 against its pre-registration
(`docs/research/experiments/2026-10-13-e016-defence-search.md`), in stages:
`world` (five arms, 30 seeds, 250,000 ticks, snapshots every 2,500,
gzipped after the run; it refuses a binary without T04's `--state-every`),
`calibrate` (the tax control's P and F, `runs/e016/tax.json`), `screen`
(the §1 defence rule with §7's viability floor, against the probe parasite,
on the E015 neighbourhoods and on each run: `defence.csv`, each complete
genome classed `structural` or `parameter`), `analyse` (per-bin measures,
H16 gate 2 on structural defences, §7.4's paired sign test, H17 counts, T05
with a `defence_class` grouping: `runs/e016/summary.md`),
`lod` (lod.py's line to the first complete genome, with the arm's physics
and probe, binned world fitness, Croft's look-back, time-to-loss) and
`replay` (T04's `--replay-from` from the last 2,500 snapshot below the
first structural defence, or runs from the founder when it arose before
2,500). The module docstring has every rule.
`--smoke --out DIR` for short test runs (`--no-snapshots` only with it).
Tests: `uv run --project analysis --with pytest pytest analysis/tests/test_e016.py`.

## Looking at a run

Record a run directory with the CLI, then report on it:

```
../evo-core/target/release/evo-core --ticks 50000 --seed 1 --census 100 --out ../runs/diag/control_s1
uv run report.py ../runs/diag/control_s1 --classify
```

`--classify` runs every genome in the run through the single-genome harness
(writes `classes.csv`, under the code's default physics, which has been
the E004 world since 2026-10-07; `classes.csv` files older than that used
the Phase 1 physics); `report.py` prints summary tables and writes PNGs to
`RUN_DIR/report/`. File formats: `docs/instrumentation.md`. For ad-hoc
queries, `evo_run.load(run_dir)` returns polars frames for every file.

On Windows, set `PYTHONIOENCODING=utf-8` if printing polars tables fails
with a `UnicodeEncodeError`.

## Interactive explorer

`explore.py` is a [marimo](https://marimo.io) notebook over the same run
directories. It opens in the browser:

```
uv run marimo edit explore.py   # notebook, code visible and editable
uv run marimo run explore.py    # app view, controls and charts only
```

Pick a run (any folder under `runs/` with a `meta.json`), narrow the tick
window, hover charts for values, and click a body in the space-time view
to see that organism's energy, children and genome listing. The
**Classify genomes** button runs `--classify` for runs without
`classes.csv`. Further down: interactions (share of births copied from
another organism's bytes or from free memory, and of instructions run
outside the own body), diversity (top genotypes over time by birth
genome or current body, genotype counts, share of bodies changed since
birth, body length), and for a selected genome its ancestry back to the
seed with the bytes each step changed, plus buttons that run it through
`examples/trace.rs` or `--host` (both in the code's default physics). The
last cell is scratch space for polars queries.

`world.py` is the companion notebook for runs with a `world.bin`:

```
uv run marimo edit world.py
```

It classifies every address at every snapshot as living body, pending
region (claimed for an unfinished child), intact dead body (unowned bytes
at a death site that still equal a known genome), debris or free; plots
that over time; draws the world map at a chosen snapshot (one row per
patch, bodies colored by class, dead bodies faded, off-body IPs marked);
and has an inspector that decodes any address span at that snapshot,
with the owner of each byte and whose IP is on it, and the same span at
every snapshot. Two tables find what to inspect: organisms whose IP was
outside their own body at the snapshot, and the addresses where the most
organisms had an off-body IP across the run (dead-code trampolines).
Loading a 100-snapshot run takes a few seconds.

marimo notebooks are plain `.py` files. Cells re-run on their own when a
value they read changes, so each name may be defined in only one cell;
prefix cell-local names with `_`.
