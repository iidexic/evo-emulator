# T03. A template-addressed ancestor, the neighbourhood mode, and E015

Status: specified 2026-10-13. Not built. Argument: synthesis §2 C and
§3.2, PLAN §8.3 and §9 ("Ancestor addressing"), hypothesis H17.
Depends on T02 only for the `exec_by_others` counter (the entered
fraction in §4); build T02 first.

## 1. The body: `sim::ancestor_t(k, e)`

Assembled with `isa::assemble` next to `ancestor`:

```
nop0 ; nop0 ; nop1 ; nop1 ; nop0     ; L0, the start label (bytes 0-4)
lit C -4
lit A {k}
absorb ; dec A ; skipz A ; jmpr C     ; absorb loop
searchf ; nop0 ; nop1 ; nop0 ; nop1 ; nop1   ; template = complement of L1
jmpa D                                ; D = address past L1
nop1 ; nop0 ; nop1 ; nop0 ; nop0     ; L1, the procedure label (bytes 20-24)
self 0 ; swap B ; swap C              ; B = start, C = len
alloc C                               ; A = child start
lit D -4
copy ; dec C ; skipz C ; jmpr D       ; copy loop
lit A {e} ; divide A
searchb ; nop1 ; nop1 ; nop0 ; nop0 ; nop1   ; template = complement of L0
jmpa D                                ; D = address past L0
```

45 bytes; 20 are label nops. Checked against `sim.rs` semantics:

- `searchf` reads its template from the nops that follow it, sets the
  IP past them, scans forward from there for the complement, and sets
  D to the address just past the match and C to the template length;
  on no match D = 0 and the flag is set. The first candidate that
  matches is its own L1 (`jmpa D` does not match; L0 is not the
  complement). D then points at `self 0`.
- `searchb` scans backward from `ip − tl − k`; the first complement of
  its template going backward is L0 (neither L1 nor the `searchf`
  template matches). D = start + 5, `lit C -4`.
- `swap C` after `swap B` leaves C = len (C held the template length
  from the search, which is overwritten), A = 5. `alloc C` wants len.
- Both loops are four bytes, so `-4` relative to the byte after the
  `jmpr` lands on the loop head.

K and E: start at (64, 16). The body costs more per cycle than the
21-byte one (45 copies at 3, `alloc` 2 + 45, two searches at about 2
and 3, upkeep 4.5 per tick), so verify in the harness, as the
2026-09-30 ancestor was: `run_alone` class `replicator` and energy not
trending down over 3,000 ticks with a full pool
(`ancestor_pays_for_itself`'s check). If (64, 16) fails, raise K in
steps of 16 and record the smallest K that passes; that K is the
default for `--ancestor tierra`. Record the cycle cost table (as PLAN
§5.3.3 has for the 21-byte body) in the doc comment.

One-hop parasite, by design: any substitution at bytes 20–24 that
changes the op (a nop of either kind keeps its op under any modifier,
so 7 of the 255 substitutions at each label byte are silent) breaks
the self-match, and the search continues forward up to `locality`
(512) and finds the next intact L1: a neighbour's. Under `self` =
executor the neighbour's procedure copies the intruder, and the
neighbour's `searchb` returns the intruder to the neighbour's L0, so
the intruder is resident for life.

### 1.1 CLI

`--ancestor NAME`, `std` (default, the 21-byte body) or `tierra`;
`--k` and `--e` apply to either. `meta.json` gets `"ancestor"`. The
harness modes (`--classify`, `--host` without `--host-body`) use the
selected ancestor as their host. `--founder` is unaffected.

`analysis/traits.py` gains a `Trait` pair for the tierra body (absorb
count at byte 8 with guard 7; endowment located by pattern already
works) and `evo_run.py` nothing.

## 2. Neighbourhood mode: `--neighbours HEX`

Classifies every single-byte mutant of HEX alone and before a host.

```
evo-core --neighbours HEX [--host-body HEX2] [--harness-ticks N]
         [--neighbours-out FILE] [--neighbours-pad-only] [--threads T]
         [physics flags]
```

Mutant set: for each position p in 0..len and each byte value v ≠
HEX[p], the substitution (255 × len bodies); for each p, the deletion
(len bodies). With `--neighbours-pad-only`, only the substitution by
`pad` (byte 0) at each position (len bodies): the MODES knockout set
(T05). Insertions are not in this cut.

For each mutant, in the quiet harness (noise off, the physics flags
given): `run_alone` for N ticks (default 3,000), and `run_with_host`
with the mutant immediately before the host, which is HEX itself
unless `--host-body` gives another body.

One new piece of state for the harness: `Org::first_foreign_off:
Option<u32>`, set in `step` the first time the organism executes a
byte owned by another living organism, to the IP's offset from that
owner's `start` (wrapped). No PRNG, nothing reads it in the physics;
`state_hash` leaves it out. `HostResult` gains `entry_off: i64` (−1 if
never) from it.

Output CSV (`neighbours.csv` in the current directory unless
`--neighbours-out`), one row per mutant:

```
pos,kind,byte,hex,raw_hash,func_hash,class_alone,births_alone,exact_alone,alive_alone,
births_host,exact_host,host_copies,host_exact,alive_host,host_alive,executed,exec_foreign,
entry_off,ticks_run,label
```

`kind` is `sub` or `del`; `byte` the new value (empty for `del`).
`label`, derived in Rust so every reader uses one rule:

- `replicator`: `class_alone` is `replicator` (the mutant is viable
  alone; `exact_host` says whether it also works next to a host).
- `parasite_fallthrough`: `class_alone` ≠ `replicator`, `exact_host`
  ≥ 2, `exec_foreign / executed` > 0.25, `entry_off` = 0.
- `parasite_jump`: as above with `entry_off` ≠ 0 (entered by a jump
  or a search, not by running off its own end).
- `one_shot`, `inexact`, `loafer`, `dies`: `class_alone` otherwise.

A summary to stdout: counts by `label`, and the `parasite_jump` rows
grouped by `pos` (for the tierra body the label-flip parasites sit at
positions 20–24; the `searchf` template at 12–16 is the other place to
look).

Threads: the mutants are independent; run them with
`std::thread::scope` over `--threads` chunks (default: available
parallelism), each with its own `Sim`. Results are written in mutant
order, so the file is identical at any thread count (test this).

Runtime: about 11,500 mutants × 2 runs × 3,000 ticks of a two-body
world, a few minutes on 24 threads.

## 3. Tests

1. `ancestor_t_replicates_exactly_without_noise` and
   `ancestor_t_pays_for_itself`, mirroring the 21-byte tests.
2. `ancestor_t_label_flip_is_a_parasite`: the body with byte 20
   changed from `nop1` to `nop0`, placed before `ancestor_t`, in the
   harness: `class_alone` ≠ `replicator`, `exact_host` ≥ 2, `entry_off`
   = 25 (the byte after L1), host alive. The same mutant alone: no
   births.
3. `neighbours_of_the_std_ancestor_has_no_jump_parasite`: the full
   neighbourhood of `ancestor(64, 16)`: zero `parasite_jump` rows, at
   least one `parasite_fallthrough` row (E005's `pad` lineages are
   this class). Mark `#[ignore]` if it takes more than ~30 s in a
   debug build, and run it in release in the report.
4. `neighbours_file_is_thread_count_independent`: T = 1 and T = 4 on
   a short genome give byte-identical output.
5. `first_foreign_off_is_set_once`.

## 4. E015: protocol for the runner (`analysis/e015_template.py`)

Experiment file `docs/research/experiments/2026-10-NN-e015-template-ancestor.md`
written before the runs; H17 holds the predictions.

1. **Neighbourhoods** of `ancestor(64, 16)` and `ancestor_t(K, 16)`
   (the K from §1), 3,000 ticks, default physics, both with the
   unmutated body as host. Record both CSVs under `runs/e015/nbhd/`
   and the label counts in the experiment file. This is literature
   item 12 (2026-09-30), done.
2. **Persistence gate**: `--ancestor tierra`, 10 seeds, 50,000 ticks,
   standard world. Pass: replicator-class bodies alive at 50,000 in
   ≥ 8 of 10 seeds (E004's criterion). If it fails, the first and only
   knob is K (re-run at the next K that passes the harness); if that
   fails, `--sun` as a declared arm change, never silently.
3. **World comparison**, 30 seeds each, 50,000 ticks, `--census 500`:
   `tierra` against `std` (E013's sixteen-founder form is not used;
   one founder, as E007). Measures: E005's parasite-lineage share of
   exact births (two executors required), per 2,500-tick bin; the
   entered fraction of replicator-class deaths (`exec_by_others` > 0,
   from T02) and the resident fraction (deaths whose `exec_foreign /
   executed` > 0.9); the share of living bodies whose IP is outside
   their own body at each census; the nop share of living bytes
   (Amoeba's 25% warning line); body-length percentiles; and T05's
   measures if built.

Predictions (H17): parasite share > 5% in ≥ 20 of 30 `tierra` seeds
by 50,000 against ≤ 2% in `std`; entered fraction > 25% in `tierra`
against 7–14% in `std`; at least one `parasite_jump` row for
`ancestor_t` and none for `ancestor`.

## 5. Files

`evo-core/src/sim.rs` (`ancestor_t`, `first_foreign_off`),
`harness.rs` (`entry_off`, the neighbourhood function), `main.rs`
(`--ancestor`, `--neighbours*`, `--threads`, docs), `record.rs`
(`ancestor` in `meta.json`), `docs/instrumentation.md` (the mode and
the field), `analysis/traits.py`, `analysis/e015_template.py`.

## 6. Report back

The K that passes and its cycle-cost table; the two neighbourhood
summaries (label counts, and the positions of every `parasite_jump`
row); `cargo test`; the persistence gate before stage 3 is started.
