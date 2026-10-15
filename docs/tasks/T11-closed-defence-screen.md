# T11. Is there a closed defence for the template body? Insertions, own-neighbourhood parasites, designed candidates

Status: specified 2026-10-15 (Fable, from E016 record §6 and §8.7 item
4); built 2026-10-15 (Opus; §2 `ceda9e7`, §1 `03e2b19`, §3 `67c5ce3`,
with files of §1 and §3 in `3c01fe3` and `253f73f`). §2's stop rule
fired (the relabelled bodies close the label-flip class: 996 rows to 0
in 28 of 34); on the decision taken then, §2 reports label-flip rows as
the closure number with the old rule beside it, §1 was built with the
pad test as found (the search is not exact-length, but `pad` is not a
nop: beside L1 it changes nothing, inside L1 it breaks the label), and
§3 was reduced to the eject, since evolution answered the closure
question itself (the redundant label) and the longer-label and
procedure-check candidates were no longer needed; E009b's six bytes do
not work verbatim in the copy loop, so the eject is the nearest working
one, seven bytes before `alloc C` (evo-core/tests/closed_defence.rs).
Builder: Opus. Argument: E016 found one defence, Tierra's
relabelling, which is immune to the registered probe and open in the
evolutionary sense (the record says "every new label has its own
one-hop parasite"). That sentence is an inference from the mechanism,
not a measurement, and the write-up needs it measured. The record's
negative ("no tolerant defence in 150 runs") also needs its
reachability argument: the single-mutant neighbourhood that was
screened has substitutions and deletions only, and a tolerant eject or
a longer label is an insertion. Three pieces, independent of each
other; §2 needs no engine change and should run first. Depends on T03
(built) and the E016 `screen` stage (run).

## 1. Insertions in `--neighbours`

`harness::mutants` gains insertions: for each position p in
0..=len and each byte v in 0..=255, the body with v inserted before p
(256 × (len + 1) bodies; 10,752 for the 41-byte body, 5,632 for the
21-byte one). `kind` is `ins`, `pos` is p, `byte` is v. Order in the
file: after the substitutions and the deletion at p, the 256
insertions at p; the insertions at p = len come last. Behind a flag,
`--neighbours-ins`, off by default, so T05's knockout set, E015 stage 1
and E016's `nbhd_screen` files are unchanged and reproducible. With
`--neighbours-pad-only` the flag is ignored.

Tests: `neighbours_file_is_thread_count_independent` run with the
flag on a short genome; `insertions_count_and_order` (a 3-byte genome
gives 3 × 255 + 3 + 4 × 256 rows in the stated order);
`insertion_of_pad_is_a_knockout_of_nothing` (inserting `pad` inside a
nop run of the tierra body's L1 leaves `class_alone` = `replicator`:
a five-nop label still matches a four-nop template by `searchf`'s
rule; confirm against `isa.rs` before writing the assertion, and if
the search is exact-length, state that and assert the opposite).

Then run E016's `nbhd_screen` on the insertion set for both ancestors
under `tierra_n0`'s and `std_n0`'s physics (the E016 probe, the E016
reference; `e016_defence.py screen --nbhd-ins` or a new flag; output
`runs/e016/nbhd_screen_<ancestor>_ins.csv`), and print the same
counts: mutants, replicator-class alone, immune, tolerant, by kind.
Expected: zero complete of either kind for tierra; the std count is
the baseline. Either way the number goes in the record (§4).

## 2. Own-neighbourhood parasites of the relabelled genomes

No engine change: `evo-core --neighbours G` already classifies every
substitution and deletion of G **against G itself as the host** (T03
§2: the host is HEX unless `--host-body`). For the ancestor this gave
996 `parasite_jump` rows at the label bytes out of 10,496 (E015 stage
1). The measurement E016 §8.7 item 4 needs: the same count for the
relabelled genomes that actually arose.

Candidates: from `runs/e016/<arm>/s<seed>/defence.csv` over
`tierra_n0` and `tierra_t50`, the structural complete genomes of the
ancestor's length (41 bytes), ranked by their total replicator-class
exact births over all runs of both arms; take the top 20 by
`func_hash` (one body each, the most common `raw_hash` of that
`func_hash`), plus every complete genome of a different length that
reaches the top 20 by the same ranking if any does. Record the list
(`runs/e016/own_nbhd/candidates.csv`: rank, arm counts, hex, births,
the template bytes 13–16 and L1 bytes 18–21 decoded).

For each candidate G: `--neighbours G` under `tierra_n0`'s physics
(sun 2, fixed edge, the same `--harness-ticks` as E015 stage 1),
written to `runs/e016/own_nbhd/<func_hash>.csv`, and the summary line
per candidate: rows, `parasite_jump` rows, their positions, the
fraction of `parasite_jump` rows that sit on the candidate's own label
bytes. Also for each candidate, E016's screen test with **its own**
label flip as the probe (G with its L1 first byte flipped, the analogue
of the registered probe): is G immune to its own parasite? Expected
no, in every case, with the `parasite_jump` count near the ancestor's
996. If any candidate has fewer than a tenth of the ancestor's
`parasite_jump` rows, or is immune to its own flip, that is a closed
defence that arose and the write-up changes; name it and stop for a
decision.

Runtime: 20 candidates × about 3 minutes on 24 threads. Run them one
at a time (the replay stage may still be running; check `tasklist`
for `evo` processes and use `--threads 12` if it is).

Output: `runs/e016/own_nbhd/summary.md`, one table (candidate, births,
label bytes, `parasite_jump` rows, on own label, immune to own flip).

## 3. Designed closed candidates

The three candidates record §8.7 item 4 names, hand-written in the
harness assembler (`harness.rs` has `with_prefix` and the ancestor
builders; add a `tierra_variant` helper if that is cleaner), each
screened as §2 screens a candidate (own neighbourhood, own-flip probe,
E016 probe, `b_alone` against the ancestor's 119):

- **Longer label**: template and L1 both lengthened to 6 nops (two
  insertions in each, 4 edits). Does a 6-nop label have fewer one-hop
  parasites than a 4-nop one? Count `parasite_jump` rows; the
  expectation is the same count (any single flip of a label byte still
  makes a body whose search finds the neighbour), and if so the record
  says label length is not a route to closure.
- **Check at the procedure**: after the procedure's entry label, a
  guard that compares `self 0` with the address the body expects
  (the pattern of E009b's six-byte eject, placed at the entry rather
  than in the loop). Write the smallest body that passes
  `ancestor_t_replicates_exactly_without_noise`, count its edit
  distance from the ancestor (substitutions + insertions), screen it.
- **Eject in the copy loop**: E009b's six bytes inserted in the
  tierra body's loop. Same.

For each: viable alone (yes/no, `b_alone`), immune to the E016 probe,
immune to its own flip, tolerant, `parasite_jump` rows in its own
neighbourhood, edit distance from the ancestor. That table is the
reachability statement: "the nearest closed defence is k edits away
and costs x% of the ancestor's rate", or "none of the three designed
candidates is closed".

## 4. Report back

The three tables (§1 counts, §2 summary, §3 table), the candidate list,
commit ids, the T11 row in `docs/tasks/README.md` and the Status line
here. Do not edit the E016 record: Fable writes §8.8 from the report.
Keep the report under 400 words plus the tables.
