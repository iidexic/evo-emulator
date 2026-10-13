# T06. Line of descent with fitness per step: E007's absorb-count sweep

Status: specified 2026-10-13; built the same day (Opus, commit
`2f27841`; reviewed by Fable, accepted; findings in the E007 record's
T06 follow-up). Amendments from the build: the step to read is the
*sweep step*, the first step whose absorb count reaches 96 or more
(`traits.ABSORB`'s threshold), since §3's "first reached its final
value" lands on later drift across the 112–127 plateau; both are
reported. Result in one line: 1,294 steps over 9 seeds (seed 10 went
extinct at tick 1,179), 261 beneficial / 747 neutral / 286
deleterious; a deleterious step immediately precedes the sweep step
in 1 of 9 seeds (seed 3: `lit A 64` to `-64`, a loop that never
ends, repaired by `-128` with `inc A`), and the sweep step itself is
deleterious *in the harness* in 8 of 9 seeds, which is §4's caveat
made concrete. Desktop data note: `runs/e007/std/` here is the
killed first launch; the complete reruns are under `runs/lod/e007/`.
Argument: `literature.md`
§7 (Lenski, Ofria, Pennock & Adami 2003 as the canonical
path-with-fitness analysis), synthesis §3.5, PLAN §8.5. Line C: the
shakedown of the method E016 needs for a defence, run on a sweep E007
has already seen. Python only; the harness through the CLI.

## 1. Interface

```
uv run lod.py RUN_DIR [--at TICK] [--pick top|id:N] [--harness-ticks 3000] [--out DIR]
```

Writes `RUN_DIR/lod/steps.csv`, `genomes.csv` and `summary.md` (or
`--out`). `analysis/lod_e007.py` runs it on the 10 E007 seeds at
`--at 250000` and writes `runs/lod/summary.md`.

## 2. The line

1. **Pick the end organism.** At `--at` (default the last census):
   the replicator-class `func_hash` with the most living bodies in
   `orgs.csv`; among them the organism with the most `offspring`
   (`--pick id:N` overrides).
2. **Walk back** through `births.csv` by `child → executor` to a
   founder (parent 0). Each organism on the line contributes its
   birth genome (`genomes.csv` by `birth_hash`); the line is a list of
   (id, birth_tick, generation, raw_hash, func_hash, bytes).
3. **Steps.** Consecutive organisms whose bytes differ form a step.
   For each: the position(s) and byte(s) changed, the kind
   (substitution, insertion, deletion, by a shortest-edit diff),
   `synonymous` = same `func_hash`, and the executor's
   `parent_now_hash` at that birth (whether the change was a copy error
   or inherited from a somatic change in the parent).
4. **Fitness per distinct genome on the line**, from the harness:
   alone (`--classify` over a temporary `genomes.csv` holding the
   line's genomes, or `--host` per genome; class, `exact_births` in
   3,000 ticks, `first_birth_tick`), and with a `pad` intruder in
   front (`--host 00 --host-body HEX`: `host_exact_births`,
   `host_alive`). Two numbers per genome: exact children per 3,000
   ticks alone, and entered.
5. **World fitness per genome** as the second column: over organisms
   born with that `raw_hash` in the 25,000-tick window of the step,
   mean exact children per death and median age (from `deaths.csv`
   and `births.csv`).

## 3. Classification of steps

With f(g) the harness exact-children count alone: a step is
`beneficial` if f(child) > f(parent) + 1, `deleterious` if f(child) <
f(parent) − 1, else `neutral` (the ±1 absorbs the integer count's
jitter; report the raw numbers too). Lenski's reading: how many of
each, in what order, and whether any deleterious step immediately
precedes the step that raised the absorb count (`traits.ABSORB` byte,
or the pattern-located `lit A` before the absorb loop).

Summary per seed: steps total, beneficial/neutral/deleterious counts,
the step and tick at which the absorb count first reached its final
value, the fitness series as a table, and the three steps before the
absorb-count step with their fitness.

## 4. Caveats to carry into the record

Harness fitness is measured with a full pool and no neighbours; the
world fitness column is the check (the break-even argument in E007's
record says the longer absorb phase wins on a *lower* ration, which
the harness cannot see, so a `neutral` harness step may be the
beneficial one in the world). The line is one path; E007 seed 3's
negative-count loop (`lit A -114 ; inc A`) is a case where byte
reading fails and the pattern must be followed.

## 5. Tests

A synthetic run directory with a known three-step line (built by the
test from the CSV formats) gives the expected steps and kinds; the
harness calls are mocked in the unit test and run for real in
`lod_e007.py`.

## 6. Report back

`runs/lod/summary.md`; whether the absorb-count step is preceded by
deleterious steps in any seed; runtime per seed.
