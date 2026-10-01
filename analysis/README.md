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
