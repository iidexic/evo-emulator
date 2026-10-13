# E015: a template-addressed ancestor (2026-10-13)

Status: record written 2026-10-13 before stages 1 and 2 were run into
`runs/e015/`; results sections added after. Stage 3 (the 30-seed world
comparison) is **not run**: it waits for the persistence gate. The
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
