# evo

An artificial-life simulator built around physics rather than features:
a small set of rules, each with a real-world analog (conserved matter,
energy that has to be absorbed and is spent per instruction, ownership,
decay, locality), from which replication, selection, death and ecology
are meant to emerge without a fitness function. Organisms are programs
in a one-byte-per-instruction register VM (25 ops) on a ring of 65,536
bytes split into patches with their own energy pools. The design, its
reasons and the prior art
(Tierra, Avida, Cosmos, Stringmol, Coreworld, BFF) are in
[PLAN.md](PLAN.md).

## Where it stands

Seeded with a 21-byte replicator, the standard world (128 patches of
512 bytes, far `alloc`, proportional absorb, bit rot 1e-4) replicates
indefinitely, holds about 935 bodies, and is stationary from about
tick 25,000 on over 250,000 ticks (E007). Parasites arise by mutation
and stay at about 1% of births (E005, E007). The one adaptation seen is
a longer absorb phase, which sweeps every run in its first 10,000
ticks. Hosts evolve no defence against parasites, and three rules that
make parasitism cost the host (E008–E010) did not change that; the
diagnosis is that a host's energy store is one pass of its loop deep,
so any cost to it is either invisible or fatal. The next design
question is store depth (PLAN §9), together with a `drain` op that
moves energy between organisms
([proposal](docs/research/drain-proposal-2026-10-12.md)). Turning write protection off
changes nothing structural (E012), there is no producer/consumer split
because nothing moves energy between organisms (E011), and sixteen
founders remove founder loss (E013). Every experiment, with its
predictions written before the runs, is in
[docs/research/experiments/](docs/research/experiments/).

## Layout

| path | what |
|---|---|
| [PLAN.md](PLAN.md) | design spec, phases, open questions, expectations, research record index |
| [evo-core/](evo-core/) | Rust crate: VM, world, recorder, harnesses, CLI (`src/main.rs` doc comment lists every flag) |
| [analysis/](analysis/) | Python (uv project): one runner per experiment, report and explorer notebooks; see its [README](analysis/README.md) |
| [docs/instrumentation.md](docs/instrumentation.md) | run-directory file formats and every recorded counter |
| [docs/research/hypotheses.md](docs/research/hypotheses.md) | numbered, dated predictions, with a status index at the top |
| [docs/research/experiments/](docs/research/experiments/) | one record per experiment (E001 onward): design, predictions, results |
| [docs/research/literature.md](docs/research/literature.md) | review of prior systems and of work since 2020 |
| `runs/` | run outputs (gitignored; regenerate from seed and commit) |

## Running it

Needs Rust (1.95 used here) and [uv](https://docs.astral.sh/uv/).

```
cd evo-core
cargo test --release
cargo run --release -- --ticks 50000 --seed 1 --census 500 --out ../runs/try/s1
cd ../analysis
uv sync
uv run report.py ../runs/try/s1 --classify     # tables and PNGs in runs/try/s1/report/
uv run marimo edit explore.py                  # interactive explorer over runs/
```

Runs are deterministic: the same seed, flags and commit give the same
files byte for byte, on Windows and Linux (checked over 20,000 ticks,
E007). Experiment runners (`analysis/e0*.py`) build the release binary
themselves and write under `runs/<experiment>/`.
