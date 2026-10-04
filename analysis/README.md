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
must be on PATH.

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
