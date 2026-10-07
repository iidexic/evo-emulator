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

To see what one genome does, tick by tick, without reading its
disassembly: `cargo run --release --example trace -- HEX [ticks]
[ADDR=HEX ...]` in `evo-core/` (the last form plants dead code in free
memory). To test a genome against a host: `evo-core --host HEX`.

## Looking at a run

Record a run directory with the CLI, then report on it:

```
../evo-core/target/release/evo-core --ticks 50000 --seed 1 --census 100 --out ../runs/diag/control_s1
uv run report.py ../runs/diag/control_s1 --classify
```

`--classify` runs every genome in the run through the single-genome harness
(writes `classes.csv`); `report.py` prints summary tables and writes PNGs to
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
`classes.csv`. The last cell is scratch space for polars queries.

marimo notebooks are plain `.py` files. Cells re-run on their own when a
value they read changes, so each name may be defined in only one cell;
prefix cell-local names with `_`.
