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

Not yet run into `runs/e015/`; filled in after the runs.
