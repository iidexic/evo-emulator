# E015: a template-addressed ancestor (2026-10-13)

Status: record written 2026-10-13 before stages 1 and 2 were run into
`runs/e015/`; results sections added after. The registered gate failed
(0 of 10). Two arms were added after it failed, the same day, per the
registered branch in `docs/tasks/README.md` ("E015 persistence and
world"): `--sun 2`, the branch's declared next knob, which **passes 10
of 10**; and a noise-off arm as a diagnostic of why the gate failed (not
in the branch). Stage 3 (the 30-seed world comparison) is **not run**. The
protocol and predictions are T03 §4 (`docs/tasks/T03-template-ancestor.md`,
written before the build) and H17 (`docs/research/hypotheses.md`); the
body and K are what the T03 build found (below). Runner:
`analysis/e015_template.py` (stages `nbhd`, `gate`, `world`).
`analysis/README.md` does not list the runner yet; its line would be:
"`e015_template.py`: E015, the template ancestor: single-mutant
neighbourhoods (`nbhd`), the persistence gate (`gate`) and the world
comparison against the 21-byte ancestor (`world`)."

Bears on: H17 (a template-addressed ancestor has a one-hop parasite and
parasitism becomes common), PLAN §8.3 and §9 ("Ancestor addressing"),
synthesis-2026-10-13 §2 C and §3.2, literature item 12 (2026-09-30: how
many one-hop parasites each ancestor has), E016 (which ancestor carries
the defence search and E014's gate 2).

## Question

Does an ancestor that enters its copy procedure by template search have
a working parasite one mutation away, where the 21-byte ancestor has
only fall-through accidents (E005)? And in the standard world without
any cost rule, does that make parasitism common: above 5% of exact
births and above 25% of replicator-class deaths entered, against the
21-byte ancestor's 0.8–1.0% and 7–14%?

## The body (from the T03 build, commit `368ce56`)

`sim::ancestor_t(k, e)`, the synthesis §3.2 candidate with **four-nop
labels**, 41 bytes, K = 127, E = 16 (`--ancestor tierra`):

```
nop0 nop0 nop1 nop1                ; L0, bytes 0-3
lit C -4 ; lit A 127               ; K is byte 7
absorb ; dec A ; skipz A ; jmpr C
searchf nop0 nop1 nop0 nop1        ; template 13-16 = complement of L1
jmpa D
nop1 nop0 nop1 nop0                ; L1, bytes 18-21
self 0 ; swap B ; swap C ; alloc C ; lit D -4
copy ; dec C ; skipz C ; jmpr D
lit A 16 ; divide A                ; E is byte 33
searchb nop1 nop1 nop0 nop0        ; template 36-39 = complement of L0
jmpa D
```

Hex `0101030351fc117f1605084c0a010301036d030103011332525a71fc1845486c11101c0b030301016d`.

Why not the specified 45-byte body: it replicates exactly but pays for
itself at no K a `lit` byte holds. Alone in the quiet harness (default
world, full pool, 3,000 ticks, children culled): K = 64, 80, 96 die
without a child, 112 makes one, 127 makes 7 and dies, netting −12.8
units per 26-tick cycle. The T03 branch (`docs/tasks/README.md`, "No K
makes it a replicator") lists fixes in order; the first, labels of four
nops, was applied and was enough. For the 41-byte body: 64 and 80 die
childless, 96 makes one, 112 makes 7 and dies (−16.1 per 23-tick
cycle), 127 pays: +37.9 units per 25-tick cycle below the store cap,
119 children, alive at the cap. K = 128 does not fit a `lit` byte, so
127 is both the first K that passes and the last K there is. Cycle at
K = 127 (measured): income 1,009.3 (127 absorbs at about 7.95), absorb
loop −507, `alloc` and copy loop −288, searches −4, other −17,
endowment −16, upkeep −139.4. The 21-byte ancestor at K = 64 nets +35.9
per 13-tick cycle, so the template body has about half its margin per
tick, and 3.8% of its income against 7.1%.

What changes from the spec: L1 is bytes 18–21 (not 20–24), the
label-flip parasite enters its host at offset 22 (not 25), the
`searchf` template is 13–16, and there are 41 × 256 = 10,496 mutants.

## Protocol (T03 §4)

1. **Neighbourhoods** (`e015_template.py nbhd`): every substitution and
   deletion of `ancestor(64, 16)` and `ancestor_t(127, 16)`, each alone
   and immediately before its unmutated self, 3,000 quiet harness ticks,
   default physics (`evo-core --neighbours HEX`). Labels are
   `harness::label` (docs/instrumentation.md): `replicator`; else, with at
   least 2 exact copies before the host and more than a quarter of its
   instructions on foreign bytes, `parasite_fallthrough` (entered at the
   host's byte 0) or `parasite_jump` (entered anywhere else); else the
   class alone. CSVs and summary in `runs/e015/nbhd/`.
2. **Persistence gate** (`e015_template.py gate`): `--ancestor tierra`,
   seeds 1–10, 50,000 ticks, standard world, one founder, `--census 500`,
   classified in the default physics. Pass: replicator-class bodies
   (class of the current body) alive at tick 50,000 in at least 8 of 10
   seeds (E004's criterion). If it fails, the first and only knob is K,
   and no K above 127 exists; then `--sun` as a declared arm change,
   never silently. Neither is taken by this record: the gate result is
   reported and the next step is decided from it.
3. **World comparison** (`e015_template.py world`, not run until the
   gate passes): `tierra` against `std`, 30 seeds each, 50,000 ticks,
   one founder (as E007), `--census 500`. Per 2,500-tick bin: E005's
   parasite-lineage share of exact births (E007's `parasite_2` test:
   harness class not `replicator`, at least 2 exact births, generation
   depth at least 5, median foreign share over carriers with at least
   two children above 0.25, and exact births by at least two executors);
   the entered share of replicator-class deaths (`exec_by_others` > 0);
   the resident share of deaths (`exec_foreign / executed` > 0.9, over
   all deaths that ran and over intruder deaths); the share of living
   bodies whose IP is outside their own body at the bin's last census;
   the nop share of living bytes there (Amoeba's 25% line; the template
   ancestor is 39% nops by construction); body-length percentiles; and
   T05's `measures.compute` per run. The gate's ten runs are the tierra
   arm's seeds 1–10 (same command line).

## Predictions (H17, registered in T03 §4)

- Stage 1: at least one `parasite_jump` row for `ancestor_t`, at the
  label positions (here 18–21), and none for `ancestor`.
- Stage 2 (the gate, not an H17 prediction): replicator-class bodies at
  tick 50,000 in at least 8 of 10 seeds.
- Stage 3: parasite share of exact births above 5% in at least 20 of 30
  `tierra` seeds by tick 50,000 (read in the last bin, ticks
  47,500–50,000; the maximum over bins is also printed), against at most
  2% in `std` (read as at most 2% in at least 20 of 30 std seeds);
  entered share of replicator-class deaths after tick 25,000 above 25%
  in `tierra` against 7–14% in `std` (medians over seeds).

## What the T03 build had already shown when this was written

Stated so the reader knows what these predictions were written against.

- Both neighbourhoods were run during the build (the stage-1 command
  line, into a scratch directory, and the std one as a test):
  `ancestor_t` has 1,095 `parasite_jump` rows, 996 of them every
  op-changing substitution and every deletion at L1 (248 + 1 at each of
  bytes 18–21, all entering at 22). `ancestor` has 25, so the
  neighbourhood prediction's second clause fails under the registered
  label rule. None of the 25 searches: `lit D 13` at byte 4 (the absorb
  loop's `jmpr D` lands on the adjacent host's `lit D -4`, entry 3),
  `jmpr C` at bytes 7, 8, 9, 13 (C holds the own length, 21, so it lands
  at the same place in the adjacent host plus one), and 16 end-byte
  mutants at byte 20 (a `lit` or a firing skip in place of `jmpa A`
  swallows or skips the host's byte 0, so the intruder runs off its own
  end and enters at 1). All work only at the harness's adjacency.
- Three 20,000-tick tierra probes (seeds 1–3, standard world) **all
  collapsed**: the population peaked at about 220, 330 and 450 between
  ticks 2,000 and 5,000; from tick 7,000 (seed 1), 13,000 (seed 2) and
  11,000 (seed 3) no 1,000-tick report had more than one body that had
  divided since the last; and 12, 36 and 46 non-reproducing bodies were
  left at tick 19,000, with the patch pools nearly full (522,000–523,900
  of 524,288 units). A 12,000-tick profile of seed 1: the founder genome
  was gone from the living by tick 1,000; replicator-class bodies 43,
  4, 18 and 0 at ticks 1,000–4,000, and none after; replicator-class
  deaths at a median age of 26 ticks (one cycle), 53–58% of them with
  no child, most often at `copy`, with 97% of their absorbs short of a
  full ration. Tiny bodies (1–4 bytes: `pad`, `nop0 ; nop0`, `skipz A ;
  jmpr C`) that die alone, but whose carriers had up to 110 offspring
  between them, held the population as it fell: fall-through intruders
  run by hosts' procedures (`self 0` names the executor, so the host's
  loop copies them). A
  3,000-tick smoke run of stage 3 (2 seeds, scratch) already had the
  parasite-lineage share of tierra's exact births at 30–38% in the last
  500 ticks and 26–35% of replicator-class deaths entered (std: 0–2%
  and about 5%).
- So the gate is expected to fail. The reading taken into it: the body
  is a thin-margin replicator (a newborn starts with 16 units and needs
  most of a full ration for 127 absorbs to pay for its first copy), and
  it is overrun by parasites, of which the label-flip searcher is only
  one kind. Whether the collapse is the margin, the parasites, or both
  is not separated by these probes.

## Results

Run 2026-10-13 with the T03 binary at `e0610d6` (clean tree; built
into `evo-core/target/t03`), `EVO_BIN` pointing at it. Data in
`runs/e015/` (not in git): `nbhd/` (both CSVs, the binary's stdout,
`summary.md`), `world/tierra/s1`–`s10` (compressed, 3–7.5 MB each),
`world/gate.csv`, `gate.md`, and `gate_bins.csv` / `gate_runs.csv`
(the stage-3 per-bin measures computed on the ten gate runs, as a
description of the collapse; not stage 3).

### Stage 1: neighbourhoods (12 s; 1.0 s and 1.9 s in the binary on 12 threads)

Identical, byte for byte, to the build-time files.

| label | std (21 bytes) | tierra (41 bytes) |
|---|---|---|
| replicator | 462 | 1,608 |
| parasite_fallthrough | 236 | 218 |
| parasite_jump | 25 | 1,095 |
| one_shot | 434 | 1,942 |
| inexact | 860 | 998 |
| loafer | 1,200 | 1,145 |
| dies | 2,159 | 3,490 |
| mutants | 5,376 | 10,496 |

`parasite_jump` rows, by position (entry offset into the host; exact
copies before the host; every host alive):

- **tierra**: L1, bytes 18–21: 249 at each (all 248 op-changing
  substitutions and the deletion), entry 22, 63 copies each: 996 rows,
  the designed one-hop searcher. `searchb` turned into `searchf` (byte
  35, 8 rows) and the three `searchb` template bytes 36–38 turned into
  `searchf` (8 each): the return search runs forward and finds the
  host's L0, entry 4 (3 at byte 38): 32 more search-addressed rows. The
  rest are fixed-offset: `lit C v` at byte 5 (11 rows, the absorb
  loop's `jmpr C` lands in the adjacent host; entries 1–4 and 29–35),
  `lit D v` at byte 27 (8 rows), `jmpr A`/`jmpr C` in place of bytes
  24, 25, 28–31 and 39 (2 each), and the last byte (40; 34 rows: 16
  end-byte `lit`/skip mutants entering at 1, and 18 that search
  forward from there, entering at 4).
- **std**: 25 rows, none searching: `lit D 13` at byte 4 (entry 3),
  `jmpr C` in place of bytes 7, 8, 9, 13 (2 each; C = own length, so
  entry at the same offset plus one), and 16 end-byte mutants at byte 20
  (entry 1).

`parasite_fallthrough`: std at bytes 4, 16, 18, 19, 20 (236, of which
211 at byte 20); tierra at 5, 27, 32, 34–40 (218, of which 184 at
byte 40).

H17's neighbourhood prediction: **first clause holds** (996 label-flip
rows at L1, plus 32 return-search rows); **second clause fails under
the registered label rule** (25 std rows). Read by mechanism, the
template body has 1,028 search-addressed one-hop parasites and the
21-byte body none; both have a few dozen fixed-offset or end-byte rows
that work only at the harness's adjacency. The label rule
(`entry_off` != 0) does not separate these; the CSV has what is needed
to (`pos`, `byte`, `entry_off`).

### Stage 2: persistence gate (9 s: runs 0–2 s each, classify 1–3 s, 6 at a time)

**0 of 10 seeds have a replicator-class body at tick 50,000: the gate
fails.**

| seed | last census with a living body | living then | last census with a replicator-class body | births | exact | last birth | pop at 5k / 10k / 15k / 20k / 25k |
|---|---|---|---|---|---|---|---|
| 1 | 50,000 | 4 | 3,500 | 8,145 | 3,498 | 24,121 | 89 / 36 / 19 / 12 / 4 |
| 2 | 40,000 | 3 | 8,000 | 21,017 | 8,878 | 30,499 | 329 / 147 / 72 / 29 / 14 |
| 3 | 41,500 | 3 | 6,000 | 20,961 | 9,221 | 41,605 | 447 / 180 / 74 / 38 / 14 |
| 4 | 28,500 | 1 | 1,500 | 4,620 | 2,358 | 27,451 | 60 / 26 / 7 / 7 / 7 |
| 5 | 29,000 | 1 | 4,000 | 11,100 | 5,290 | 16,374 | 152 / 40 / 17 / 8 / 4 |
| 6 | 29,500 | 3 | 6,500 | 25,337 | 10,956 | 20,750 | 442 / 166 / 68 / 26 / 9 |
| 7 | 27,000 | 5 | 2,000 | 5,471 | 2,616 | 20,396 | 44 / 17 / 10 / 6 / 5 |
| 8 | 25,000 | 1 | 3,500 | 14,415 | 6,791 | 23,508 | 202 / 79 / 33 / 6 / 1 |
| 9 | 27,500 | 1 | 4,000 | 9,430 | 4,084 | 24,241 | 155 / 65 / 21 / 11 / 2 |
| 10 | 50,000 | 1 | 6,500 | 17,822 | 7,769 | 25,671 | 263 / 96 / 36 / 14 / 8 |

("Living then" is the population at the census in the second column.
Seeds 1 and 10 reach tick 50,000 with 4 and 1 non-replicating bodies;
the other eight go extinct at ticks 40,150, 41,640, 28,538, 29,451,
29,666, 27,378, 25,016 and 27,849, seeds 2–9 in order.) No seed has an exact birth by a replicator-class
parent in its last 5,000 ticks (E004's `replicating`).

What the population did, medians over the ten seeds per 2,500-tick bin
(`gate_bins.csv`; parasite lineages are E007's `parasite_2` set per
run):

| ticks | seeds with exact births | exact births | parasite share of exact births (min–max) | replicator-class deaths entered | living | IP off own body | nop share of living bytes | length p10 / p50 |
|---|---|---|---|---|---|---|---|---|
| 0–2,500 | 10 | 3,190 | 15.7% (2.7–32.2%) | 27.9% | 260 | 56.6% | 33.1% | 3 / 41 |
| 2,500–5,000 | 10 | 1,998 | 12.8% (0–29.2%) | 28.6% | 178 | 58.3% | 28.9% | 4 / 41 |
| 5,000–7,500 | 7 | 30 | 9.6% (0–20.4%) | 83% (of 6.5) | 114 | 59.1% | 26.2% | 4 / 41 |
| 7,500–10,000 | 4 | 0 | 5.0% (0–96.4%), 4 seeds | 75% (of 2.5) | 72 | 60.2% | 24.2% | 4 / 41 |

### Reading

The template body does what it was designed to do in the harness, and
in the world the parasitism H17 predicts shows up from the first bin:
16% of exact births by parasite lineages and 28% of replicator-class
deaths entered in the first 2,500 ticks, against E007's 0.8–1.0% and
7–14% for the 21-byte body. Then the hosts are gone within 1,500–8,000
ticks and nothing replicates after. As in the probes, they die in their
first cycle at a short ration, overrun by tiny fall-through bodies that
run their absorb loops and procedures. Under the template body's
`searchb` return, every intruder that reaches a host stays in it,
whether it came by search or fell in. That is the design, meant for
E016's cost rule, but here the residents only draw on the host's patch.

The probes do not separate the two causes. One is the body's margin:
it breaks even at a ration of about 95.6% of a full one, where the
21-byte body at K = 64 breaks even at 92.3%. The other is the parasite
load. The gate has its answer either way. The registered next steps
(T03 §4, README "E015 persistence and world"): K is the first knob and
is spent, since 127 is the largest K a `lit` byte holds; then `--sun`
as a declared arm change; if neither persists, the ancestor needs
shortening or another fix before E016. This record takes none of them;
stage 3 is not run.

## Arms added after the gate failed

Both added 2026-10-13, after the registered gate failed, per the
registered branch in `docs/tasks/README.md` ("E015 persistence and
world": K up, then `--sun` as a declared arm). K has no step left, so
`--sun` is the arm the branch names. The noise-off arm is not in the
branch: it is a diagnostic, asked for to separate the two causes the
reading above leaves open. Both use the gate's protocol unchanged (10
seeds, 50,000 ticks, K = 127, E = 16, one founder, `--census 500`, pass
at replicator-class bodies alive at 50,000 in at least 8 of 10),
classified under the arm's own physics flags. Runner:
`e015_template.py gate --arm tierra_quiet` and `--arm tierra_sun2`
(commits `8d95f4a`, `2fcba52`); data in `runs/e015/world/tierra_quiet/`
and `tierra_sun2/`, tables in `gate_<arm>.md`, per-bin measures in
`gate_<arm>_bins.csv`, per run in `gate_<arm>_runs.csv`. Same binary as
stages 1 and 2 (`e0610d6`).

### Noise off (`tierra_quiet`: `--p 0 --rot 0`; 20 s for runs and classes)

`--p 0` sets the write-flip and copy-slip probabilities to 0 and
`--rot 0` bit rot: E005's quiet world but for debris decay, which has no
flag and changes no byte (it relabels debris as free, and every op
treats the two alike). The question was: with no mutation, can a
parasite arise? If the body persists, parasite load killed it under
noise; if it still dies, its margin did.

**0 of 10 seeds have a replicator-class body at tick 50,000: the body
dies here too. Its world does not.**

| seed | last census with life | living then | replicator-class at 50,000 | last census with a replicator-class body | exact births by replicator-class parents, last 5,000 ticks | births | exact | living at 10k / 20k / 30k / 40k / 50k |
|---|---|---|---|---|---|---|---|---|
| 1 | 50,000 | 431 | 0 | 40,500 | 0 | 189,475 | 126,422 | 565 / 506 / 514 / 450 / 431 |
| 2 | 50,000 | 200 | 0 | 3,000 | 0 | 80,768 | 58,400 | 305 / 216 / 200 / 201 / 200 |
| 3 | 50,000 | 334 | 0 | 3,500 | 0 | 151,181 | 103,959 | 400 / 355 / 423 / 335 / 334 |
| 4 | 50,000 | 375 | 0 | 11,000 | 0 | 148,618 | 110,132 | 311 / 380 / 373 / 380 / 375 |
| 5 | 50,000 | 334 | 0 | 3,000 | 0 | 84,135 | 58,595 | 480 / 333 / 333 / 333 / 334 |
| 6 | 50,000 | 134 | 0 | 3,000 | 0 | 75,208 | 55,542 | 144 / 136 / 136 / 134 / 134 |
| 7 | 50,000 | 545 | 0 | 5,500 | 0 | 48,926 | 37,936 | 569 / 544 / 544 / 545 / 545 |
| 8 | 50,000 | 248 | 0 | 16,000 | 0 | 231,761 | 158,824 | 506 / 325 / 251 / 242 / 248 |
| 9 | 50,000 | 366 | 0 | 2,500 | 0 | 81,272 | 53,757 | 528 / 366 / 366 / 365 / 366 |
| 10 | 50,000 | 256 | 0 | 8,000 | 0 | 193,502 | 127,939 | 297 / 253 / 365 / 259 / 256 |

All ten worlds are alive at 50,000 (134-545 bodies), and eight still
make exact births in the last bin, but by bodies that are `one_shot`
or `dies` alone. Mutation is not needed for parasites: the `alloc` and
`copy` range edge (PLAN §9) makes them. In both quiet seeds checked
(1 and 2), the first non-exact birth is the founder's second child at
tick 51 (0 copy errors, 0 slips), which differs from its parent only in
bytes 0-2, its start label: placed at the backward edge of the
locality radius, its first three bytes are out of range of the `copy`
instruction three bytes after the `alloc`, and keep whatever stale bytes
were there. Every other child of every parent can be placed so. Such a
child replicates once, then its `searchb` misses its own L0 and finds a
neighbour's, where it stays. In the first 5,000 ticks of seed 1,
2,384 of 26,657 births lost only bytes 0-2 and 1,092 more differed
both there and elsewhere. The bodies left at 50,000 carry stale bytes for L0
and often for the `searchb` return (bytes 35-40), so after one child
they fall through into a neighbour.

Per 2,500-tick bin, medians over seeds (selected bins; all 20 in
`gate_tierra_quiet_bins.csv`):

| ticks | seeds with exact births | exact births | parasite-lineage share of exact births (min–max) | replicator-class deaths entered (deaths) | living | IP off own body | nop share of living bytes |
|---|---|---|---|---|---|---|---|
| 0–2,500 | 10 | 9,836 | 74.2% (55.5%–78.2%) | 22.5% (1,828) | 264 | 35.7% | 31.5% |
| 2,500–5,000 | 10 | 16,924 | 87.9% (57.3%–96.0%) | 48.1% (156) | 433 | 49.5% | 29.3% |
| 5,000–7,500 | 10 | 14,270 | 79.2% (49.9%–89.8%) | 48.7% (4) | 470 | 68.8% | 27.7% |
| 7,500–10,000 | 10 | 7,963 | 75.2% (42.8%–84.7%) | 43.5% (0) | 440 | 77.8% | 25.8% |
| 17,500–20,000 | 9 | 2,112 | 36.8% (0.0%–79.2%) | – (0) | 344 | 82.8% | 24.1% |
| 27,500–30,000 | 8 | 1,568 | 67.8% (0.0%–100.0%) | – (0) | 366 | 82.5% | 24.5% |
| 37,500–40,000 | 8 | 130 | 67.7% (0.0%–100.0%) | 100.0% (0) | 334 | 82.9% | 23.9% |
| 47,500–50,000 | 8 | 124 | 62.5% (0.0%–100.0%) | – (0) | 334 | 82.8% | 23.9% |

### `--sun 2` (`tierra_sun2`; 232 s for runs and classes)

Choosing N. The instruction was the smallest `--sun` at which the
body's harness break-even ration drops below the 21-byte body's 92.3%.
No N does that: `--sun` multiplies patch income and cap, and the ration
at a full pool is 8 units whatever the sun. Measured in the harness
below the store cap, a cycle pays at 95.61% of a full ration for this
body and 92.34% for the 21-byte one at every N from 1 to 4; only the
ration the harness actually delivers moves (99.34%, 99.67%, 99.77%,
99.83% of full at N = 1-4, so the template body's net per cycle goes
from +37.9 to +41.2, +42.3, +42.9). What `--sun` moves is the load a
patch can carry at break-even. A patch whose bodies would draw D units
per tick at a full ration settles, under the proportional ration, at the
share income / D (absorbed equals income), so it carries
D* = income / break-even. The 21-byte body at sun 1: 256 / 0.9234 =
277.2 units per tick, 7.04 bodies at 39.38 units per tick each (64
absorbs per 13-tick cycle); this body at sun N: 256 N / 0.9561 = 267.8 N
units per tick, 6.59 N bodies at 40.64 each (127 per 25 ticks). Equal
at N = 1.068. `--sun` takes whole numbers, so N = 2, and 3 if 2 failed.

**10 of 10 seeds have replicator-class bodies at tick 50,000 (210-274
of 1,179-1,506 living): the gate passes at `--sun 2`.** Sun 3 was not
run.

| seed | last census with life | living then | replicator-class at 50,000 | last census with a replicator-class body | exact births by replicator-class parents, last 5,000 ticks | births | exact | living at 10k / 20k / 30k / 40k / 50k |
|---|---|---|---|---|---|---|---|---|
| 1 | 50,000 | 1420 | 232 | 50,000 | 5,544 | 342,101 | 163,890 | 1453 / 1392 / 1497 / 1437 / 1420 |
| 2 | 50,000 | 1460 | 226 | 50,000 | 5,896 | 354,884 | 171,135 | 1254 / 1491 / 1458 / 1431 / 1460 |
| 3 | 50,000 | 1179 | 238 | 50,000 | 3,814 | 311,434 | 143,486 | 1047 / 1478 / 1299 / 1256 / 1179 |
| 4 | 50,000 | 1361 | 235 | 50,000 | 5,425 | 313,243 | 153,122 | 807 / 1280 / 1258 / 1450 / 1361 |
| 5 | 50,000 | 1420 | 210 | 50,000 | 5,868 | 343,360 | 166,968 | 1230 / 1383 / 1175 / 1356 / 1420 |
| 6 | 50,000 | 1439 | 247 | 50,000 | 5,196 | 327,285 | 152,400 | 1340 / 1399 / 1418 / 1466 / 1439 |
| 7 | 50,000 | 1430 | 247 | 50,000 | 4,599 | 325,925 | 153,763 | 882 / 1447 / 1467 / 1356 / 1430 |
| 8 | 50,000 | 1506 | 274 | 50,000 | 6,052 | 313,283 | 146,559 | 1261 / 1470 / 1489 / 1489 / 1506 |
| 9 | 50,000 | 1478 | 231 | 50,000 | 4,963 | 347,065 | 162,840 | 1423 / 1426 / 1279 / 1391 / 1478 |
| 10 | 50,000 | 1391 | 219 | 50,000 | 5,201 | 306,695 | 141,442 | 1218 / 1308 / 1402 / 1407 / 1391 |

Per 2,500-tick bin, medians over seeds (parasite lineages are E007's
`parasite_2` set per run, as stage 3 would compute them; "deaths" is the
median count of replicator-class deaths in the bin):

| ticks | seeds with exact births | exact births | parasite-lineage share of exact births (min–max) | replicator-class deaths entered (deaths) | living | IP off own body | nop share of living bytes |
|---|---|---|---|---|---|---|---|
| 0–2,500 | 10 | 10,420 | 45.4% (31.9%–51.3%) | 44.9% (2,004) | 1,044 | 61.9% | 32.9% |
| 2,500–5,000 | 10 | 13,225 | 42.9% (25.9%–47.4%) | 38.4% (3,323) | 1,213 | 63.6% | 30.8% |
| 5,000–7,500 | 10 | 8,401 | 29.0% (23.5%–43.6%) | 30.2% (3,046) | 1,213 | 58.6% | 28.9% |
| 7,500–10,000 | 10 | 8,412 | 31.4% (16.5%–36.3%) | 28.4% (3,030) | 1,242 | 56.6% | 27.2% |
| 10,000–12,500 | 10 | 8,689 | 27.4% (21.6%–33.7%) | 25.7% (3,704) | 1,374 | 54.4% | 25.6% |
| 12,500–15,000 | 10 | 9,513 | 30.0% (22.2%–42.4%) | 27.4% (4,024) | 1,336 | 53.8% | 24.5% |
| 15,000–17,500 | 10 | 7,473 | 27.6% (19.8%–41.8%) | 26.5% (3,474) | 1,358 | 53.7% | 22.9% |
| 17,500–20,000 | 10 | 7,936 | 29.8% (15.8%–35.6%) | 26.7% (3,513) | 1,412 | 53.4% | 22.5% |
| 20,000–22,500 | 10 | 9,394 | 31.4% (10.9%–42.8%) | 27.6% (3,981) | 1,434 | 54.4% | 20.9% |
| 22,500–25,000 | 10 | 7,556 | 26.0% (15.4%–35.2%) | 25.2% (3,518) | 1,340 | 52.2% | 19.8% |
| 25,000–27,500 | 10 | 7,192 | 24.0% (15.8%–44.4%) | 25.6% (3,679) | 1,408 | 49.2% | 19.1% |
| 27,500–30,000 | 10 | 6,912 | 24.4% (14.8%–30.4%) | 24.7% (3,626) | 1,410 | 47.8% | 17.9% |
| 30,000–32,500 | 10 | 6,081 | 16.8% (7.5%–37.3%) | 23.4% (3,898) | 1,443 | 47.7% | 17.0% |
| 32,500–35,000 | 10 | 6,425 | 20.8% (7.4%–29.8%) | 25.5% (3,459) | 1,443 | 46.8% | 15.9% |
| 35,000–37,500 | 10 | 6,786 | 24.0% (19.6%–29.0%) | 26.9% (3,897) | 1,439 | 47.6% | 15.3% |
| 37,500–40,000 | 10 | 6,502 | 21.5% (11.6%–26.7%) | 25.2% (3,800) | 1,419 | 46.3% | 14.5% |
| 40,000–42,500 | 10 | 6,004 | 20.5% (13.0%–29.0%) | 24.7% (3,728) | 1,415 | 46.5% | 14.0% |
| 42,500–45,000 | 10 | 4,930 | 13.5% (8.0%–28.6%) | 24.4% (3,588) | 1,421 | 45.4% | 13.4% |
| 45,000–47,500 | 10 | 5,440 | 18.4% (10.9%–22.3%) | 24.8% (3,488) | 1,424 | 43.1% | 13.1% |
| 47,500–50,000 | 10 | 5,332 | 16.7% (8.0%–27.0%) | 24.8% (3,484) | 1,425 | 43.6% | 13.0% |

Per seed, last bin (47,500-50,000): parasite-lineage share 17.5%,
27.0%, 12.0%, 16.7%, 16.7%, 17.3%, 8.0%, 25.9%, 10.7%, 13.1% (seeds 1-10;
above 5% in 10 of 10). Replicator-class deaths after tick 25,000
entered: 25.1%, 23.5%, 25.2%, 25.5%, 26.1%, 26.4%, 24.3%, 24.6%, 24.1%,
25.0% (median 25.0%, above 25% in 6 of 10). Deaths resident
(`exec_foreign / executed` > 0.9) after 25,000: 9.4-12.3% of all deaths
that ran, 23.4-30.1% of intruder deaths. The 21-byte ancestor was not
run at sun 2, so these have no same-sun control yet.

### The three arms side by side: replicator-class deaths

Seeds pooled; class of the birth genome; "mean ration" is
sum `absorb_gain_m` / sum `absorbs` / 8,000, as a share of a full
ration (the body breaks even at 95.6%); "absorbs short" counts any
absorb from a pool below its cap, so it says little on its own.

| arm | ticks | deaths | median age | no child | absorbs short | mean ration |
|---|---|---|---|---|---|---|
| gate (noise on) | 0-2,500 | 10,540 | 27 | 51.2% | 92.7% | 89.7% |
| gate (noise on) | 0-5,000 | 16,209 | 27 | 51.1% | 82.4% | 85.5% |
| noise off | 0-2,500 | 17,805 | 27 | 53.1% | 97.4% | 90.5% |
| noise off | 0-5,000 | 24,907 | 27 | 53.3% | 97.4% | 90.4% |
| `--sun 2` | 0-2,500 | 20,870 | 27 | 61.1% | 92.6% | 87.1% |
| `--sun 2` | 0-5,000 | 52,216 | 26 | 63.8% | 84.8% | 83.7% |

(The 26 ticks and 97% in "What the T03 build had already shown" are
seed 1's probe, first 2,000 ticks, absorbs short averaged per 500-tick
bin; pooled over the ten gate seeds the same reading is 27 and 92.7%.)

### Reading after the added arms

By the rule set for the noise-off arm (persists: parasite load; dies:
margin), the margin is the cause: with no mutation the replicator-class
body still dies in its first cycle, at a mean ration of about 90% of a
full one against a break-even of 95.6%, as under noise. The arm does
not exclude the parasite load, because it did not remove parasites:
the `alloc`/`copy` edge makes return-parasites from the founder's
second child on, and their lineages made a median 74-88% of exact
births per bin in the first 7,500 ticks. What it does show is that the
template body's world
collapses under noise but not without it: with noise the dependents
decay too and 8 of 10 worlds die; without it they persist as a
community of bodies none of which replicates alone.

At `--sun 2` the body persists in every seed and parasitism is common
for the whole run: about 45% of exact births by parasite lineages at
first, 17% by the last bin, never below 8% in any seed's last bin, and
a quarter of replicator-class deaths entered. That is the tierra side
of H17's world prediction met in the gate's ten seeds of a declared
arm. It is not the registered test: that is stage 3, 30 seeds against
the 21-byte ancestor, which has not been run at `--sun 2`. And
replicator-class bodies at sun 2 still die young (median 26 ticks, 64%
childless in the first 5,000) at a mean ration of 84%: the body
persists because enough of them pay, not because most do. Stage 3 is
not run.
