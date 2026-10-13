# T02. Cost of intrusion in time: `--cycle-theft-pct`, its control, and E014

Status: specified 2026-10-13; built the same day (Opus, commit
`0ce3338`; reviewed by Fable, accepted). Gate 1 passed at N = 50
(host alive, 0.465 of its lone births; the host dies at every N from
51 up in the harness, where it is entered every tick). Amendments
after the build, below in §4.3 and §4.4: the pilot branch is governed
by `entered_rate_norm`, not `entered_children_ratio`; the runner gzips
each run's CSVs. Argument: synthesis §3.1, PLAN §5.4 and §8.3,
hypothesis H16.

## 1. Rule

When organism X executes an instruction whose byte at IP is owned by
a living organism Y ≠ X, X pays the energy exactly as today, and Y's
per-tick execution budget is debited `floor(cost × N / 100)` in the
budget's own units (milli-units; `cost` is the instruction's actual
charge, including the search and `alloc` extras). The debit is added
to a debt on Y and taken from Y's budget at the start of its next
turns. Energy is never touched. N = 0 is bit-identical to the current
world.

Physical reading (for the doc comments): energy is matter and is
conserved; the per-tick cap is time, the organism's share of the
machine. An intruder running on Y's bytes occupies Y's cycles.

### 1.1 Config and CLI

`config.rs`:

```rust
/// Cycle theft (E014), percent 0-100: an instruction run by one
/// organism at a byte owned by another living organism debits the
/// owner's per-tick execution budget by floor(cost * pct / 100),
/// carried as `Org::cycle_debt`. Energy is untouched. 0 (default) is
/// off and bit-identical to no flag.
pub cycle_theft_pct: i64,
/// Random cycle tax (E014's matched control), percent 0-100 of the
/// per-tick cap, applied each tick to each living organism with
/// probability `cycle_tax_frac`. 0 (default) is off.
pub cycle_tax_pct: i64,
/// Probability per organism per tick that the cycle tax applies.
/// 1.0 (default) taxes every organism every tick with no PRNG draw.
pub cycle_tax_frac: f64,
```

All three go into `Config::fields()` (so `meta.json` carries them;
the destructuring forces it). CLI: `--cycle-theft-pct N`,
`--cycle-tax-pct N`, `--cycle-tax-frac F`, with the range checks the
other percent flags have (0–100; F in 0–1). They may be combined
with each other and with any energy rule; nothing is refused.

### 1.2 State

`Org` gains `pub cycle_debt: i64` (milli-units of budget, 0 at birth;
`seed` and `inject` start it at 0). It is part of the physics, so
`state_hash` includes it (append after `alive`; the hash is compared
only between runs of the same binary, never stored, so its value may
change).

### 1.3 Execution (`sim.rs`)

In `step`, after the energy settlement and the transfer block, before
`Some(total)`:

```rust
let tp = self.cfg.cycle_theft_pct;
if tp > 0 && own >= FIRST_ID && own != self.orgs[i].id {
    if let Some(j) = self.org_index(own) {
        if self.orgs[j].alive {
            let debit = cost * tp / 100;
            self.orgs[j].cycle_debt += debit;
            self.orgs[j].stats.cycles_lost_m += debit;
            self.orgs[i].stats.cycles_taken_m += debit;
        }
    }
}
```

`own` is the owner read before the op ran, as the other rules use it.
A pending region's bytes belong to the organism that allocated them.
Debris, free bytes and a dead owner debit nothing. The executor's own
tick budget is debited by `total` only, as now.

In `run_tick`, after the upkeep charge and before the execution loop:

```rust
let cap = self.cfg.cap_c0 + self.cfg.cap_c1 * self.orgs[i].len as i64;
let mut debit = self.orgs[i].cycle_debt.min(cap);
self.orgs[i].cycle_debt -= debit;
let tax_pct = self.cfg.cycle_tax_pct;
if tax_pct > 0 {
    let f = self.cfg.cycle_tax_frac;
    if f >= 1.0 || self.rng.chance(f) {
        let taxed = (cap * tax_pct / 100).min(cap - debit);
        debit += taxed;
        self.orgs[i].stats.cycles_taxed_m += taxed;
    }
}
let mut left = cap - debit;
```

A host whose debt exceeds its cap runs nothing this tick (`left` = 0,
`starved_ticks` counts it as today, since it paid upkeep and ran
nothing) and carries the rest. It still pays upkeep, so a host under
several intruders at a high N can starve; that is the graded, slow
death the caveat in H16 names, and it is reported, not prevented.

PRNG: theft draws nothing. The tax draws one `chance(f)` per living
organism per tick, in the shuffled order, only when 0 < f < 1;
organisms killed by upkeep that tick draw nothing. With the tax off
the stream is unchanged.

### 1.4 Counters

Append to `OrgStats`, in this order, after `overwritten`:

| field | meaning |
|---|---|
| `cycles_lost_m` | budget debited from this organism by intruders' instructions (theft), cumulative |
| `cycles_taken_m` | budget this organism's instructions debited from the owners of the bytes it ran |
| `cycles_taxed_m` | budget debited by the random tax |
| `exec_by_others` | instructions other organisms executed at bytes this organism owned (body or pending region): the victim-side counterpart of `exec_foreign`, counted whatever the flags, so "entered" can be read in a world with no cost rule |

`CSV_HEADER` and `csv_row` extended; `docs/instrumentation.md` gets
the four rows and a paragraph on the rule in the style of the
`--transfer-pct` one. Over a world, Σ `cycles_lost_m` = Σ
`cycles_taken_m` and Σ `exec_by_others` = Σ `exec_foreign` (both
tested, as `foreign_write_counters_agree_over_a_world` does).

## 2. Tests (`cargo test`)

1. `cycle_theft_zero_is_the_default_world`: seeded standard world,
   5,000 ticks, N = 0 against no flag: equal `state_hash`.
2. `cycle_theft_leaves_energy_alone`: `energy_is_conserved` and the
   ledger identity hold at N = 50 with a `pad` before the ancestor,
   noise on; `paid_for_others_m` and `gained_from_others_m` stay 0.
3. `cycle_counters_agree_over_a_world`: 20,000 ticks at N = 50, the
   two sums above equal, and the Σ `exec_by_others` identity also at
   N = 0.
4. `cycle_theft_slows_the_entered_host` (gate 1 of H16): harness,
   `pad` immediately before `ancestor(64, 16)`, N = 50, 3,000 ticks:
   the host is alive at the end and `host_exact_births` is between 35%
   and 65% of `run_alone(ancestor(64, 16), 3000).exact_births`. The
   test also prints the ratio at N ∈ {25, 50, 75, 100} and the host's
   final energy, as `print_duel` does, so the record can quote them.
5. `cycle_tax_frac_one_draws_nothing`: tax at F = 1.0 leaves the
   PRNG stream identical to the no-tax run (compare `rng.state()`
   after a tick); at F = 0.5 it differs.
6. `cycle_debt_carries_over`: a host with `cycle_debt` = 3 × cap runs
   nothing for three ticks and all of the fourth.

## 3. Harness and CLI

`--host HEX [--host-body HEX] [--host-pad]` already carries physics
flags; nothing to add but the new flags. Gate 1 is also runnable from
the shell for the record:

```
evo-core --host 00 --cycle-theft-pct 50 --harness-ticks 3000
```

(`00` is one `pad`, placed immediately before the ancestor.)

## 4. E014 runner: `analysis/e014_cycle_theft.py`

Modelled on `e009b_late_injection.py` (same bins, matching rules and
column names, so the two records read side by side). Protocol and
predictions go into `docs/research/experiments/2026-10-NN-e014-cycle-theft.md`
before any run, by the person who runs it; H16 holds the predictions
already.

### 4.1 Stages

**Pilot** (3 seeds, 50,000 ticks, injection at 25,000): every arm
below, to check the engine, the population under each N, and to
calibrate the tax. Not evidence.

**Main** (30 seeds, 250,000 ticks, injection at 25,000; `--census 500`).

Arms (rule × genome):

- rules: `n0` (no flag), `t25`, `t50`, `t75` (`--cycle-theft-pct N`),
  `tax` (`--cycle-tax-pct P --cycle-tax-frac F`, calibrated below).
- genomes: `eject` = `self 1 ; swap C ; self 0 ; sub C ; skipz A ;
  jmpa D` + the K = 120 ancestor (EJECT6 in `traits.py`); `inert` =
  six `zero D` + the K = 120 ancestor (INERT6); `resident` = the K =
  120 ancestor alone.

Run directories `runs/e014/<rule>_<genome>/s<seed>/`. Fifty copies
injected (`--inject 25000:HEX:50`), as E009b.

### 4.2 Tax calibration (from the pilot's `t50_resident` runs)

Over replicator-class deaths after tick 25,000: `F` = share with
`exec_by_others` > 0 (entered); `r` = Σ `cycles_lost_m` / Σ `age`
over all those deaths (mean debit per organism-tick, entered or not).
The control debits each organism with probability `F` per tick by
`cap × P / 100`, so set `P` = 100 × `r` / (`F` × `cap`), `cap` =
32,000 milli-units, rounded to the nearest whole percent. Record `F`,
`r`, `P` in the experiment file. This is Johnson 2026's bottleneck
control in this currency: the population pays the same time, but not
for being entered.

### 4.3 Measures

E009b's per-bin measures verbatim (`test_share`, `prefix_share`,
`long_share`, `test_alive`, `pop`, `rep_alive`, `foreign_exec_share`,
the death columns, `last_above_1pct`, `last_alive_gt10`, `alive_end`),
plus per bin over replicator-class deaths: `entered_share`
(`exec_by_others` > 0), `cycles_lost_per_tick` (mean of
`cycles_lost_m / age` over entered deaths), `entered_children_ratio`
(mean exact children of entered deaths over unentered), and
`entered_age_ratio`. Over living test bodies at each census: the
same entered share.

Amendment 2026-10-13 (from the build): `entered_children_ratio` is
confounded by lifespan, since a body that lives longer is more likely
to be entered and has more children; in the no-cost smoke run it was
3.78 with an age ratio of 3.18. Two more columns: `entered_rate_ratio`
(exact children per tick of life, entered deaths over unentered) and
`entered_rate_norm` = that ratio divided by the same ratio in the `n0`
arm at the same injection and seed. `entered_rate_norm` governs
prediction 2 and the pilot branch in `README.md`; the other two are
diagnostics. The runner also gzips `births.csv`, `deaths.csv`,
`orgs.csv` and `census.csv` after each run (the main stage would
otherwise need about 220 GB), and `evo_run.py`'s loader reads
`.csv.gz`.

### 4.4 Predictions, operational (H16)

1. Persistence: `resident` alive with ≥ 10 bodies and ≥ 1% share at
   tick 250,000 in ≥ 27 of 30 seeds under every rule. If `t75` fails
   this, `t75` is reported as the slow-starvation arm and excluded
   from 2–4.
2. Entered hosts are graded, not killed: under `t50`,
   `entered_rate_norm` between 0.3 and 0.8 in the pilot and in
   ≥ 20 of 30 main seeds (amended 2026-10-13; it was
   `entered_children_ratio`, which is kept as a diagnostic, and the
   `n0` clause is now the normalisation itself).
3. The eject pays: under `t50`, `eject` `last_share` ≥ 1% in ≥ 20 of
   30 seeds; `inert` ≥ 1% in ≤ 5 of 30.
4. The control: under `tax`, `eject` and `inert` ≥ 1% counts differ
   by at most 3 seeds.
5. Dose: the seed count in 3 is monotone in N over `t25`, `t50`,
   `t75` (ties allowed).

Refuted if 3 fails at every N, or if 4 fails with `eject` maintained
under the tax (an accounting error to audit before anything else).

## 5. Files

`evo-core/src/config.rs`, `sim.rs`, `main.rs` (flags and the module
doc), `harness.rs` (test 4), `docs/instrumentation.md`,
`analysis/e014_cycle_theft.py`, `analysis/evo_run.py` only if a
column needs a type override (it should not).

## 6. Report back

The gate 1 numbers at each N; `cargo test` output; the speed at seed
1, 20,000 ticks, with and without the flag (expected within 5%); and
the pilot's population and `entered_children_ratio` per N before the
main stage is started.
