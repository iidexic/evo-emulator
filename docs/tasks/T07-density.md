# T07. Replicator density by uniform sampling (line B, step B0)

Status: specified 2026-10-13. Not built. Argument: synthesis §3.6
line B, PLAN §8.4 B0, `notes/recent-5-soup-emergence-isal.md` (Dušek
et al. 2026's U control: uniform sampling with a fixed test). Needs
no GPU and no new physics. Answers, before the cubff work: how rare
is a self-replicator in evo's ISA, against BFF's 7.1 × 10^-11 per
64-byte tape, and is the H3 shortest-replicator question answerable by
enumeration.

## 1. Mode

```
evo-core --density LEN:N [--density-ticks T] [--density-out FILE]
         [--threads K] [--seed S] [physics flags]
```

Draw N bodies of LEN bytes, each byte `rng.below(256)` from
`Rng::new(S)` in order (so the sample is reproducible and the first
n bodies of a larger N are the same). Run each alone in the quiet
harness (`run_alone_with`, noise off, 100 units of seed energy,
children removed every tick) for T ticks (default 1,000; stop early
on death, as the harness does) in a small world: 8,192 bytes, 16
patches of 512, otherwise the physics given. Classes as the harness
gives them.

Output to stdout: `len, n, ticks, replicator, one_shot, inexact,
loafer, dies, seconds`. `--density-out FILE`: one CSV row per body
that is not `dies` or `loafer` (`hex, class, births, exact_births,
first_birth_tick, executed`), so every replicator found is kept.
Threads as T03's `--neighbours` (chunks in sample order; the file is
identical at any thread count).

Optional, if cheap: `--enumerate LEN` for LEN ≤ 3 (every body, 2^24
at LEN = 3), same output: the H3 question "what is the shortest
replicator in this ISA" by exhaustion.

## 2. Runner: `analysis/b0_density.py`

LEN ∈ {8, 12, 16, 21, 24, 32, 45, 64}, N = 10^6 each at T = 1,000;
LEN = 21 also at T = 3,000 and N = 10^6 (sensitivity of the class to
the run length); LEN ≤ 16 at N = 10^7 if the 10^6 pass takes under 10
minutes. Seeds 1 and 2 for every cell (two independent samples).
Output `runs/b0/density.csv` and `summary.md`: per cell the
replicator count, the point estimate, and the Clopper–Pearson 95%
interval (the beta-quantile form; with zero hits the upper bound is
1 − 0.025^(1/N), about 3.7 / N), plus the same for `one_shot +
replicator` (a one-shot is a copier that leaves; Dušek's test counts a
tape that produces one copy).

The comparison line: BFF at 7.1 × 10^-11 per 64-byte tape (Dušek
2026, uniform sampling). Note the protocol differences in the summary
(BFF's test is a tape-pair interaction over epochs; this one is a body
alone with energy and a per-tick cap), so the number is read as an
order of magnitude.

## 3. What it decides

- Density at LEN = 21 or 24 within two orders of magnitude of BFF's:
  seedless emergence on the ring is worth trying (line B3's soup mode
  and H7's start-execution rule).
- Three or more orders below, or zero hits at 10^7 for every LEN ≤
  32: seedless emergence on this ISA is out of reach without an ISA
  change, which is known before any GPU time, and line B proceeds in
  the cubff fork (B1, B2) with evo's rules rather than evo's ISA.
- Any replicator found at LEN ≤ 12: a body shorter than the 21-byte
  ancestor exists; keep its hex in the record and classify its
  neighbourhood (T03).

## 4. Tests

`density_sample_is_reproducible` (same seed, same first bodies at any
N and thread count); `density_finds_the_ancestor_if_planted` (a test
hook that replaces body 0 by `ancestor(64, 16)` counts one
replicator).

## 5. Report back

The density table; the hex of every replicator found; runtime per
cell; the decision line from §3.
