# BFF, its follow-ups, and adjacent recent work: verified notes

Compiled 2026-09-30. Purpose: check and deepen `docs/research-historic/Review.md` on
BFF / *Computational Life* and related recent work, from primary sources only.

How this was checked:

- arXiv PDFs downloaded and read in full: 2406.19108v2 (Computational Life),
  2607.01483v1 (Knierim et al.), 2607.09211 (Cicala et al.), 2412.17799 (ASAL).
- Code read directly: `paradigms-of-intelligence/cubff` cloned at commit `f212e84`
  (2025-08-17, main branch); `znah/zff` cloned at `3e58d97`.
- Ackley papers read in full from his UNM site (HotOS 2011, ALIFE 14, CACM 2013
  preprint, ECAL 2015, AAAI 2016).
- Anything seen only through a search-engine snippet, or not seen at all, is tagged
  **UNVERIFIED**.

Terms used below:

- *Tape*: a fixed-length byte string. In BFF it is both a program and its data.
- *Epoch*: one sweep in which every tape in the soup takes part in one interaction.
- *Takeover* (the authors also say "gelation"): one replicator family filling most of
  the soup. *Emergence* or *discovery* means the first working replicator appears.
  The 2026 follow-up shows these two are different events, and much of the confusion
  in secondary accounts comes from mixing them up.

---

## 1. *Computational Life* (Agüera y Arcas et al., arXiv 2406.19108)

### 1.1 Status

- Authors: Agüera y Arcas, Alakuijala, Evans, Laurie, Mordvintsev, Niklasson,
  Randazzo, Versari (Google Paradigms of Intelligence and U. Chicago). v1 was posted
  27 Jun 2024 and v2 on 2 Aug 2024. https://arxiv.org/abs/2406.19108
- It is still a preprint. The group's own July 2026 papers cite it as
  "arXiv preprint arXiv:2406.19108" (https://arxiv.org/pdf/2607.01483, ref [1];
  https://arxiv.org/pdf/2607.09211, bibliography). I found no journal version
  (**UNVERIFIED** that none exists).

### 1.2 The BFF language (exact)

Source: paper §2 (https://arxiv.org/pdf/2406.19108) and `bff.inc.h` in cubff
(https://github.com/paradigms-of-intelligence/cubff/blob/main/bff.inc.h).

- Brainfuck with the input/output streams replaced by copies between two heads, so
  instructions and data share one tape. There are three pointers: the instruction
  pointer, `head0` (read head) and `head1` (write head). All of them index the same
  tape.
- Ten operations:
  - `<` / `>` move head0 left or right.
  - `{` / `}` move head1 left or right.
  - `-` / `+` decrement or increment `tape[head0]`.
  - `.` copies: `tape[head1] = tape[head0]`.
  - `,` copies the other way: `tape[head0] = tape[head1]`.
  - `[` jumps forward past the matching `]` if `tape[head0] == 0`.
  - `]` jumps back to the matching `[` if `tape[head0] != 0`.
  - Every other byte value is a no-op. Byte 0 is the "true zero" that ends loops. In
    the paper's words: "out of the 256 possible characters, only 10 are valid
    instructions and 1 corresponds to the true 'zero'".
- The program terminates on an unmatched bracket, or after 2^13 = 8,192 characters
  have been read. In code, the limit is `Evaluate(tape, 8 * 1024, ...)` and the step
  counter includes no-op bytes.
- Details visible only in the code:
  - The paper runs the `bff_noheads` variant. Its initial head position is
    `2*kSingleTapeSize` = 128, which is masked with `& 127` to 0. So **both heads
    start at byte 0**, the first byte of the first program, and the instruction
    pointer starts at 0 too.
  - The heads wrap modulo 128, the length of the joined pair. The instruction
    pointer does not wrap: running off the end ends the run.
- Other variants in cubff:
  - `bff`: head positions are taken from the first two bytes, and the instruction
    pointer starts at 2.
  - `bff_selfmove`: 7 ops on byte values 0–6, a single copy op `,` that
    post-increments head1, and no head1 movement ops.
  - `bff8`: brackets jump a fixed 8 bytes.
  - `bff_perm`: a different byte-to-op mapping.
  - `bff8_noheads` and `bff_noheads_4bit`.
- The 2025 book *What Is Intelligence?* describes a 7-instruction bff (`<>+−,[]`)
  with heads initialized from the first two bytes, and says the paper version with
  `{` `}` was replaced by "a stripped-down alternative"
  (https://whatisintelligence.antikythera.org/chapter-01/, notes). This matches
  cubff's `bff_selfmove` op set. So **"BFF" names a family of variants.** Knierim et
  al. say the same: "we have seen many different variants of BFF ... with very
  similar results".

### 1.3 Soup protocol (exact)

Sources: paper §2.1 and `common_language.h` / `common.h` / `main.cc` in cubff.

- The soup holds 2^17 = 131,072 tapes of 64 bytes each (`num_programs = 128 * 1024`).
  Tapes start as uniform random bytes (SplitMix64).
- Each epoch:
  1. A random permutation splits the soup into 65,536 disjoint ordered pairs, so every
     tape interacts exactly once per epoch.
  2. Each pair is concatenated into a 128-byte tape.
  3. Mutation is applied to that 128-byte tape: **each byte is replaced by a uniformly
     random byte** with probability `mutation_prob / 2^30` = 2^18/2^30 = 2^-12 ≈
     0.0244%. This is the paper's "0.024%". It is byte replacement, not a bit flip.
  4. The joined tape is executed.
  5. It is split back into two 64-byte tapes.
- A run of 16k epochs is therefore about 1.07e9 interactions.
- Nothing is created or deleted: "no new programs are generated or removed". A tape
  "dies" only by being overwritten.
- Chemistry framing from the paper: `A + B → split(exec(AB)) = A' + B'`. A replicator
  S acts on "food" F as `S + F → 2·S`. The authors say the other tape "gets
  repurposed as available real estate".
- There is no energy, no ownership and no write protection. Execution is free up to
  the 8,192-step budget, and every tape is executed as the first half of a pair on
  about half of its interactions.

### 1.4 How the transition is detected: "high-order entropy"

- Definition (paper §2.1): "the difference between (1) its Shannon entropy (computed
  over individual tokens – i.e. bytes) and (2) its 'normalized' Kolmogorov complexity
  (i.e. its Kolmogorov complexity divided by n)."
- Kolmogorov complexity is approximated by the compressed size under
  "`brotli -q2` ... brotli v1.1.0" (footnote 1).
- In code, it is computed over the **whole soup** as one string:
  `higher_entropy = h0 - brotli_bpb`. Here `h0` is the byte-histogram entropy in bits
  per byte, and `brotli_bpb` is the compressed bits per byte from
  `BrotliEncoderCompress(2, 24, ...)`.
- Stated properties: i.i.d. noise tends to 0, and many copies of one string tend to
  that string's symbol entropy. So a soup taken over by copies scores high.
- *Tracer tokens*: every byte carries a 64-bit (epoch, position, char) token. Copy
  ops move tokens. `+` and `-` change only the char part. The number of unique tokens
  drops sharply at the transition, "perfectly aligned" with the complexity jump.
  Without a transition, unique tokens settle around 3M of the initial 8M (2^23).

### 1.5 Numbers (BFF well-mixed soup, 1000 runs per condition)

Source: paper §2.1, Figs. 5–7.

- **40% of runs transition within 16k epochs** at the default 0.024% mutation rate
  (Fig. 5).
- Fig. 6, fraction of runs that did *not* reach complexity ≥ 1 within 16k epochs
  (read from the rendered figure):

  | mutation rate | fraction not reaching complexity ≥ 1 |
  |---|---|
  | 0% | 0.56 |
  | 0.012% | 0.65 |
  | 0.024% | 0.60 |
  | 0.048% | 0.50 |
  | 0.1% | 0.42 |
  | 0.5% | 0.62 |
  | **1%** | **0.94** |

- The text says "Generally, we observe that increasing the mutation rate speeds up
  the rise of self-replicators". The figure supports that only up to about 0.1%.
  Above that, far fewer runs cross the threshold. The paper does not say whether this
  is because fewer replicators arise or because heavy noise lowers a
  compression-based metric (**UNVERIFIED** which).
- **Zero mutation still works.** "even without any background mutation, this state
  transition occurs with roughly the same frequency as our default case" (44% vs 40%
  in Fig. 6).
- Fig. 7 compares run types:
  - "short" (128 epochs, random init): transitions only 3 times in 1000.
  - "seeded" (one hand-written replicator added, 128 epochs): 22% take over. The
    authors read this as "roughly 1/5 of all self-replicators manage to take over".
  - "long-no-noise" (zero mutation plus a fixed, non-random pairing schedule): about
    50%, "even more likely" than the default.
  - Authors' conclusion: replicators "arise mostly due to self-modification and
    interaction among different programs and are not simply due to random
    initialization and random mutations."
- Case study (Figs. 2–3):
  - The first replicator appears at epoch 2354–2355 in "a complex rewrite event".
  - A "zero-poisoning" period follows, with about 14% of the soup at zero, because the
    first replicator family (`[,}<]`) "can copy '0', but can't write over '0'".
  - A zero-tolerant family (`[<,}]`) then takes over.
  - The hand-sanitized example replicator `[[{.>]-]   ]-]>.{[[` is a palindrome that
    copies itself in reverse (Fig. 4).

### 1.6 Spatial (2D) variant

- 32,400 tapes on a 240 × 135 grid. Two tapes can interact only if
  `|x0−x1| ≤ 2 and |y0−y1| ≤ 2` (paper §2.2).
- Each epoch, tapes are visited in random order. Each picks a random neighbour, and
  the pair runs if neither tape is already taken. "Note that programs that do not
  execute still get mutated."
- In code, the neighbour list comes from `make_2d_pattern.py` (`RANGE = 2`, edges
  clipped). The grid is **bounded, not a torus**.
- The paper also tried 1D ("self-replicators emerge in all configurations").
- Main effect: in a well-mixed soup a replicator takes over half the soup in about
  log n steps. In 2D, takeover takes a number of epochs proportional to the grid side.
  2D "provides a fertile ground for multiple variations of self-replicators to
  co-exist and compete".

### 1.7 "Long tape" variants

This is the closest setup to evo's single shared array.

- **BFF long tape.** One tape "usually 65,536 bytes". Each iteration picks a random
  start position and runs until an op limit or an error.
  - If both heads start at the start position, "trivial (non-looping)
    self-replicators rapidly take over the universe".
  - "Adding an offset to head1 is sufficient to allow looping self-replicators to
    arise ... an offset somewhat larger than 8 ... (e.g., 12 or 16)."
  - Code: https://github.com/benlaurie/bff-ben (branch `paper2`).
- **Forth long tape.**
  - The first ISA tried used offsets from the program counter or from a 64-byte
    "pseudo-tape" marker. "Neither of these variants gave rise to replicators",
    although a hand-seeded 9-byte replicator "proceeded to occupy the entire long
    tape, further complexify, and persist indefinitely".
  - A different 6-op ISA, with a relative copy `*(pc + top-1 + top) = *(pc + top-1)`,
    did work: "good" replicators emerged in about 60 s, or 180 billion instructions.
    This was on a 65,536-byte tape, with 1 mutation per 400,000 instructions, at
    about 3e9 instructions/s over 8 threads.
  - Determinism was dropped for speed: "We sacrifice determinacy for performance by
    foregoing locking".
  - Stack over- or underflow ends a run. As a result, replicators evolved "a fairly
    long non-functional head followed by a relatively short functional replicating
    tail", because starting mid-replicator usually errors.
- **8080 long tape.** Replicators were "always two bytes repeated", for example
  `01 c5` (LXI BC then PUSH BC). These are non-looping: "we have never seen a looping
  variant emerge in 8080."

### 1.8 Other substrates and the one that failed

| Substrate | Setting | Result | Source |
|---|---|---|---|
| BFF (`bff_noheads`) | well-mixed soup, 1D, 2D, long tape | replicators emerge; 40% of runs within 16k epochs (soup) | §2 |
| Forth (`forthtrivial`) | soup and 2D | trivial 1-byte replicator `0C`; full-tape replicators (e.g. `0C 08 04 81 2C C4`); "Almost all runs show a state transition within 1k epochs"; 2D soup "never dominated by one individual program" after 20k steps | §3.1.1 |
| Forth | long tape | first ISA: no spontaneous replicators; second ISA: yes | §3.1.2 |
| Z80 | 2D grid, 16-byte tapes, adjacent pairs in random order AB/BA, 256 steps, addresses mod 32, random mutation | several "generations" of replicators: stack-based `PUSH` first, then `LDIR`/`LDDR` block copy; "symbiotic ecosystems" | §3.3; https://github.com/znah/zff (200×200 grid, 4-neighbour pairs, bounded edges, C compiled to WASM) |
| 8080 | long tape | only 2-byte non-looping replicators | §3.3 |
| **SUBLEQ, RSUBLEQ4** | soup | seeded replicators "quickly and often take over", but random soups "remained in almost complete random uniformity even following billions of executions" | §3.2 |

Why SUBLEQ failed, in the authors' words:

- The smallest hand-written SUBLEQ replicator is 60 bytes, and the RSUBLEQ4 one is
  25 bytes. "There are no dynamics to change the distribution of strings, and
  self-replicators are too rare to be generated by random background mutation."
- "SUBLEQ-like languages seem to have a much higher expected length for a
  functioning initial self-replicator. We believe that such a length plays a critical
  role ... but we expect it to not be the sole factor at play" (§4).
- Note that even the 25-byte RSUBLEQ4 replicator did not emerge. The working
  substrates had first replicators of roughly 1–10 bytes.

### 1.9 What happened after emergence

- The claims are qualitative. The abstract says: "We also show how increasingly
  complex dynamics continue to emerge following the rise of self-replicators." The
  discussion calls it "anecdotal evidence that this is the beginning of more complex
  dynamics".
- The concrete observations:
  - successive replicator families replacing each other (BFF zero-tolerance, Z80
    PUSH → LDIR);
  - long-lived coexistence in 2D Forth and Z80;
  - replicators that keep changing slowly (long-tape Forth).
- The book adds that after whole-tape replication, sub-replicators appear inside
  tapes and can kill, ignore or help their host, and that replicated tapes carry "a
  level of complexity ... that seems unnecessarily—even implausibly—high"
  (https://whatisintelligence.antikythera.org/chapter-01/).
- No quantitative open-endedness measure is reported in any of these sources.

### 1.10 What cubff actually implements

- A CUDA or CPU/OpenMP simulator. The README says "Most experiments in the
  'Computational Life' ... paper ... were done using this code"; the paper says CUDA
  and CPU "give identical results".
- Languages: `bff`, `bff_noheads`, `bff_noheads_4bit`, `bff8`, `bff8_noheads`,
  `bff_perm`, `bff_selfmove`, `forth`, `forthcopy`, `forthtrivial`,
  `forthtrivial_reset`, `subleq`, `rsubleq4`.
- Main flags: `--num` (soup size), `--mutation_prob` (default 1/4096),
  `--interaction_pattern` (neighbour list, used for 2D), `--fixed_shuffle`,
  `--zero_init`, `--eval_selfrep`, `--stopping_selfrep_count`, save and load.
  Python bindings and analysis scripts are included (`python/`, `cubff_walk_back.py`).
- Added in 2025: a self-replicator detector (`CheckSelfRep`, Feb 2025) and an
  "estimator of how likely a program is to generate a self-replicator" (Obryk,
  commit `e21076b`).
- Not in cubff: Z80 (it is in `znah/zff`) and long-tape BFF/Forth (in
  `benlaurie/bff-ben`).
- License: Apache-2.0 (GitHub API).

---

## 2. Knierim et al. 2026, "BFF: Simple explanations for complex phenomena"

**The citation is real.** arXiv 2607.01483v1, dated 1 Jul 2026 (PDF dated 3 Jul 2026).
Authors: Charlotte Knierim, Luca Versari, Robert Obryk, Blaise Agüera y Arcas,
Rif A. Saurous (Google Paradigms of Intelligence). https://arxiv.org/abs/2607.01483

This is a **self-critique by the same group**; Agüera y Arcas and Versari are
coauthors. It is not an outside challenge. Its main variant is `bff_selfmove`.

### 2.1 The self-replicator detector

- Algorithm 1 in the paper, in plain terms:
  1. Put the candidate program P in the second half of a tape and noise in the first.
  2. Repeat 5 times: move the second half into the first half, put fresh noise in the
     second half, and run.
  3. Do this on several independent branches.
  4. Score = min over two counts. For the first half: the number of bytes that match
     P in at least 3 of the final tapes. For the second half: the number of bytes on
     which at least 3 tapes agree.
- The score runs from 0 to 64, and a program counts as a replicator at ≥ 48.
  "results do not change significantly for thresholds of at least ≈ 20". The chain
  length is kept odd so that self-inverting replicators are detected.
- The public cubff main branch (`CheckSelfRep`, commit `f212e84`) uses slightly
  different constants: 13 branches, 4 extra generations, agreement `count > 13/4`,
  and a CLI "replicator" threshold of 5 (`kSelfrepThreshold`). The exact detector
  version behind the paper is not in the main branch (**UNVERIFIED** whether another
  branch has it).

### 2.2 Results

- **Baseline** (their Experiment 3.1): the average time to the first detected
  replicator in BFF is ≈ 2.5e6 interactions, i.e. 5e6 programs tested, averaged over
  100 seeds. The soup size used is not stated (**UNVERIFIED**).
- **Fresh random programs** (whole programs resampled each time):

  | sampling distribution | programs tested per replicator found | vs BFF soup |
  |---|---|---|
  | uniform bytes | 2.9e7 | about 6× slower |
  | the byte distribution the BFF soup itself writes | 1.7e6 | about 3× faster |
  | "CUST": half operators, half no-ops | 4.5e5 | about 10× faster |
  | "CUST64": CUST plus byte 64, so the heads start 64 apart | 9.4e4 | about 25× faster |

- **Mutation random walk** (every byte mutated with probability p). Table 1, programs
  tested per replicator found:

  | p | Uniform | BFF-dist | CUST | CUST64 |
  |---|---|---|---|---|
  | 1/200 | 9.5e8 | 3.5e7 | 7.9e6 | 1.9e6 |
  | 1/100 | 4.4e8 | 1.9e7 | 4.1e6 | 9.9e5 |
  | 1/50 | 2.0e8 | 1.0e7 | 2.1e6 | 5.2e5 |
  | 1 | 2.9e7 | 1.7e6 | 4.5e5 | 9.4e4 |

  They note that in BFF "the fraction of bytes that change per interaction grows from
  1/100 to ≈1/50", so p = 1/200 to 1/50 is the fair comparison range.

- **Reading the table carefully** (my reading of their Table 1):
  - At BFF-like change rates, a random walk over *uniform* bytes is roughly 40–190×
    **slower** than the BFF soup (2e8–9.5e8 vs 5e6).
  - Even with the soup's own byte distribution it is 2–7× slower.
  - The walk beats the soup only with the hand-designed CUST or CUST64 distributions.
  - So the result is: a soup is not a *better search operator* than a random walk
    over a good byte distribution. It is not: a soup is useless. Much of the soup's
    advantage is that it shifts the byte distribution toward operators.
  - The authors address this directly. They say CUST shows the distribution is easy
    to find by hand ("The next experiment shows that this is not the case").
- **Merger blocking** (§3.3):
  - A *merger* is "a consecutive copy of at least two bytes that were not copied
    together before".
  - Capping merger depth or width means "we cancel the interaction and return the
    programs to the soup in their original state".
  - Result: "emergence of self-replicators is quite robust to merger blocking". Limits
    as low as 2 only slow it. Limit 0 (and depth 1) forbids all copying, yet
    replicators are still found through `+`/`-` alone, "just significantly slower",
    reaching 40% after 50 million epochs.
  - Conclusion: "limiting the width or depth of a merger does not actually prevent
    the emergence of self-replicators, but rather prevents them from taking over the
    soup. Thus compositionality is not needed for the discovery of self-replicators".
  - The per-limit percentages in their Fig. 4 were not extractable from the PDF text
    (**UNVERIFIED**).
- **Their conclusion**: "program interaction in BFF ... is not an unusually powerful
  search operator ... we do not currently consider program interaction in BFF to be
  an effective model of [recombination and HGT]." They thank Vassilis Papadopoulos
  "for bringing the issue of randomness being fast at solving self-replicators to our
  attention".

### 2.3 Whose claim is being tested

- The 2024 paper never proposes depth or width caps. The "symbiogenesis beats
  mutation" story does appear in Agüera y Arcas's 2025 book: "Bff suggests that
  symbiogenesis is a more important driver of evolutionary innovation than random
  mutation", and "each larger replicator is composed of smaller ones—an inverted tree
  of life, consisting of mergers over time rather than splits"
  (https://whatisintelligence.antikythera.org/chapter-01/).
- The specific claim that capping stops emergence was not found in the paper or in
  book chapter 1. It is probably from talks or other chapters (**UNVERIFIED**).
- Knierim et al. directly undercut the book's claim about *discovery*. They leave
  open that mergers matter for *takeover*.

---

## 3. Other 2022–2026 work on emergence in instruction or chemistry substrates

### 3.1 Cicala et al. 2026, "Coevolution of self-replication and function in a digital primordial soup"

arXiv 2607.09211 (10 Jul 2026); the same Google team plus Mila/McGill.
https://arxiv.org/abs/2607.09211

- **Setup:**
  - 2^19 random 32-byte Z80 programs, in 32 isolated niches of 128×128 cells.
  - Pairing is local (von Neumann neighbour) with probability 0.95. Otherwise the
    partner is drawn from anywhere ("cross-niche pollination").
  - Each program has a 1/64 chance per epoch of one byte being reinitialized.
  - Before interacting, a program is "validated". It runs alone for up to 512
    instructions and must compute its niche's polynomial on 3 inputs. Passing raises
    its interaction probability from 0.3 to 1.0.
- **Their metabolic constraint.** The interaction probability of *validated*
  programs is discounted in proportion to the steps used during validation. Result:
  "the average number of execution steps spent during validation fell significantly"
  and conditional halting evolved more often.
  - This is a runtime cost on the *task*, applied as a bias on interaction
    probability. Interactions themselves remain free. It is not per-instruction
    energy that can kill.
- **Replicator succession.**
  - "Load–Push" replicators come first. They have no loop and use the whole 32-byte
    tape.
  - LDIR block-copy replicators take over later. They need "only a few bytes" and
    leave room for task code.
  - With LDIR, LDI and LDDR removed from the ISA, an LDD-plus-explicit-loop
    replicator emerges instead, "much more slowly".
  - Robustness to copy errors ranks LDIR > LDD > Load–Push.
  - Without task pressure, the Load–Push → LDD transition "fails to complete within
    ten million epochs".
- **Emergent vs hard-wired replication.** When replication is hard-wired (the
  partner is overwritten by an exact copy), the genealogies are narrower.
  Emergent replication "supports a significantly wider set of evolutionary paths",
  but the hard-wired system "solves more of the harder tasks".
- Why it matters for evo: this is the closest published system to "cost for
  computation plus emergent replication". It shows (a) that replicator architecture
  keeps evolving after emergence, and (b) that compactness and copy robustness decide
  which replicator wins.

### 3.2 Mathis, Patel, Weimer, Forrest 2024, "Self-Organization in Computation & Chemistry: Return to AlChemy"

arXiv 2408.12137; published in *Chaos*, Sep 2024 (https://pubmed.ncbi.nlm.nih.gov/39345193).
This is the actual 2024 re-analysis of Fontana's AlChemy. It is not by Google, and not
by anyone named Devlin.

- Findings: "complex, stable organizations emerge more frequently than previously
  expected, ... these organizations are robust against collapse into trivial
  fixed-points, but ... cannot be easily combined into higher order entities."
- The results depend on which random-expression generator is used.
- Source: https://arxiv.org/abs/2408.12137

### 3.3 Kruszewski & Mikolov 2022, "Emergence of Self-Reproducing Metabolisms as Recursive Algorithms in an Artificial Chemistry"

*Artificial Life* 27(3–4), 2022; arXiv 2103.08245.

- An artificial chemistry based on combinatory logic "with conservation laws".
- From a tabula rasa it finds structures "including ones that self-reproduce in each
  cycle".
- Hypothesis: the key requirement is "an auto-catalyzed subset of Turing-complete
  reactions".
- This is conservation-of-matter precedent, cited by the BFF paper as its ref [28].
  https://arxiv.org/abs/2103.08245

### 3.4 Cotler, Hongler, Hudcová 2025, "Self-replication and Computational Universality"

arXiv 2510.08342.

- They construct "a cellular automaton that is Turing-universal but cannot sustain
  non-trivial self-replication".
- Lesson: being able to compute everything does not imply supporting replicators.
  This is a formal cousin of the SUBLEQ counterexample. https://arxiv.org/abs/2510.08342

### 3.5 C G, LaBar, Hintze, Adami 2017, "Origin of life in a digital microcosm"

This is background, older than 2022, but cited by Knierim et al.

- Avida. They generate "the exhaustive set of minimal-genome self-replicators".
- The probability that a given replicator out-competes others "is not uniform".
- It is the Avida analogue of "estimate replicator density by sampling".
  https://arxiv.org/abs/1701.03993

### 3.6 Moreno, Rodriguez Papa, Ofria, Zaman, Dolson 2026, "Trust, but Verify: Rigorously Profiling Best-Effort High-Performance Computing for Digital Evolution"

arXiv 2608.23955.

- On relaxing determinism for multi-core and wafer-scale digital evolution. Best
  effort "can help accommodate such constraints, but complicate reproducibility and
  risk introducing artifactual biases".
- Reports 92% scaling efficiency at 64 processes for a best-effort model.
- Relevant to evo §9 (multi-core strategy). https://arxiv.org/abs/2608.23955

### 3.7 Independent reproductions

Secondary; code not reviewed.

- `ricky0123/complexity`: browser version, repo created 2025-01-18.
- `gustavsoderstrom/computational-life`: Python, created 2026-01-09.
- An identically described `peterseb1969/computational-life`, created 2026-09-06.
- All exist per the GitHub API.
- A blog replication (https://jonamiki.com/posts/bff-emergent-complexity-experiment/,
  7 Mar 2026) reports emergence around 20 million interactions with only 1,024
  programs in 5 of 5 seeds. Seen via a WebFetch summary only (**UNVERIFIED** detail).

### 3.8 Searched for and not found

- Follow-up papers by Alakuijala or "Chiu" on BFF.
- A work titled "Life in silico" on replicator emergence.
- A Google "AlChemy" re-analysis. The AlChemy revisit that exists is §3.2.
- A "Symbiosis / Barricelli" ALICE 2026 workshop report exists (arXiv 2603.08463). It
  is about 1D/2D Barricelli numerical organisms, not instruction soups, and only its
  abstract was read.

---

## 4. Sakana AI, ASAL: "Automating the Search for Artificial Life with Foundation Models"

Kumar, Lu, Kirsch, Tang, Stanley, Isola, Ha; arXiv 2412.17799 (23 Dec 2024).
Code: https://github.com/SakanaAI/asal (Apache-2.0).

- **What it is:** an *outer-loop search over simulation parameters*, scored by
  vision-language foundation models (CLIP; DINOv2 in ablations) applied to
  **rendered images** of the simulation. It has three modes: match a target prompt,
  find "open-ended" simulations, and "illuminate" a diverse set.
- **Substrates:** Boids, Particle Life, Life-like cellular automata, Lenia, neural
  cellular automata.
- **Open-endedness score (Eq. 3):** for each time T, take the maximum CLIP similarity
  between the frame at T and any earlier frame, average over T, and search for
  parameters that minimize this. It is "historical nearest neighbor novelty", which
  they found better than variance-based novelty.
  - The subjectivity is openly delegated: "This formulation outsources the
    subjectivity of measuring open-endedness to the construction of the
    representation function, which embodies the observer."
  - Result: Conway's Life "ranks among the top 5% most open-ended CAs according to our
    open-endedness metric".
  - Representation dominates. In pixel space the trajectory "exhibits a convergent
    trajectory". CLIP ≈ DINOv2, and both are "significantly better than a pixel based
    representations" for human-aligned diversity.
- **Usable for evo?**
  - As-is, no. Evo's state is a byte array. Any image of it (for example, colour by
    opcode or lineage) is a synthetic rendering far from CLIP's training data, so
    CLIP novelty would measure texture changes in our own visualization, not genomic
    or behavioural novelty.
  - Also, ASAL scores whole runs to choose parameters. That costs a full run per
    candidate, which is feasible only for short runs.
  - What transfers is the **formula**: "historical nearest-neighbour novelty over time
    in some embedding". The embedding should be a domain one, for example:
    - opcode k-mer histograms of the dominant genomes;
    - compression distance between snapshots;
    - behavioural phenotype vectors (ops-class usage, write targets, interaction
      partners).
  - Record it next to high-order entropy (§1.4), not instead of it.

---

## 5. David Ackley: robust-first computing, MFM, ulam, T2 tiles

### 5.1 The Movable Feast Machine (MFM)

Sources: HotOS 2011 paper, https://www.cs.unm.edu/~ackley/papers/hotos-11.pdf; ALIFE 14
paper, https://www.cs.unm.edu/~ackley/papers/ackley-small-alife14.pdf.

- **Hardware model:** an open-ended 2D grid of tiles. Each tile (in 2011) had a
  72 MHz processor, 32 KB RAM, and 4 neighbour links, and held 48×48 "sites".
- **Atoms:** each site holds one fixed-width *atom* (64 bits in 2011; 96 bits in
  2015). The atom's type selects an *element* (a class-like definition) whose update
  method defines its behaviour.
- **Locality via event windows** (HotOS §2.1):
  - "Computation in the MFM is based on event windows, each of which consists of a
    center site and its {R = 4} nearest neighbors, exclusively held for the event
    duration."
  - Distance is city-block, so a window is 41 sites. The Computer Journal 2013 paper
    is described by a search snippet as "41 sites within Manhattan distance 4";
    the full text was not read (**UNVERIFIED** directly, but it follows from R = 4).
  - Centres are chosen randomly and "starvation-free", and "an indefinite number of
    non-overlapping windows may occur in parallel".
  - Code inside an event is ordinary serial code. However, it "cannot access any
    persistent state outside the event window or assume anything about event window
    contents between invocations."
  - Tiles use inter-tile locking so a window that spans tiles is still consistent
    (ALIFE 14).
- **Physics is fixed.** The MFM is a strict Harvard architecture: element code lives
  in "an entirely separate address space from the atoms, so nothing that happens
  during atomic level computations can affect the 'laws of physics'" (ALIFE 14).
  **So MFM is not an evolving-code substrate.** Its elements are hand-designed.
  - It is prior art for spatial, asynchronous, noisy, conserved-resource *physics*
    and for engineered robustness. It is not prior art for evolved replicators.
  - The one "movable program" in the 2011 work is an interpreted opcode chain (base
    chain, interpreter, polymerase) used to rebuild Sorters.

### 5.2 Why Ackley rejects deterministic global execution

- The scaling argument (AAAI 2016, https://www.cs.unm.edu/~ackley/papers/ackley-aaai16-smpt.pdf):
  "if we then keep adding more and more of those hardware units to the system, and
  running it longer and longer, eventually the aggregate space-time computational
  volume will exceed the reciprocal of the hardware unit failure rate, and the
  machine will deliver undetected errors to the software level. That's why, even in
  principle, hardware determinism doesn't scale".
- Five properties he calls incompatible with indefinite scalability (ALIFE 14):
  1. global synchronization;
  2. perfect reliability;
  3. free communication, including "any local use of (finitely-old) global data—such
     as conditioning local reproduction decisions on the current global population
     size";
  4. more than 3 scalable dimensions;
  5. periodic boundaries in 3 scalable dimensions. Periodic boundaries "can be
     tolerated in models with at most two scalable dimensions".
- Against deterministic alife models (ECAL 2015,
  https://www.cs.unm.edu/~ackley/papers/ecal2015-author-copy.pdf): "the properties of
  such models typically depend critically on deterministic execution, as typified by
  the utter collapse of constructs in Conway's game of life when facing even mild
  asynchrony". Also: "Determinism is a property of the small and the fragile".
- Energy (ECAL 2015, "Use it or lose it"): "energy is a nonrefundable sunk cost ...
  A cycle saved is a cycle wasted." This is the opposite of evo's
  pay-per-instruction model. In MFM, computation is free and idle hardware is waste.
- The efficiency-vs-robustness demo (CACM 2013, preprint
  https://www.cs.unm.edu/~ackley/be-201301131528.pdf):
  - Task: sort 52 cards with a comparator that is wrong 10% of the time.
  - Bubble sort's many local comparisons and one-position moves beat quicksort and
    merge sort on positional error.
  - With a "sticky" faulty comparator, bubble sort's error rose "to nearly 90—but
    quick exceeded 550, merge exceeded 650".
  - Moral: efficiency removes the redundancy that robustness needs.

### 5.3 DReg / Res, Demon Horde Sort, cells

- **DReg (Dynamic Regulator):** it mostly diffuses, but "probabilistically may delete
  an atom in a nearby site, or create a new 'resource' atom (element Res), or another
  DReg". It fills space with "a churning mixture of DReg, Res, and empty sites in
  roughly fixed proportions".
  - Anything sharing space with DReg must survive random deletion. If reproduction
    works only by transmuting Res, "this DReg homeostatic mechanism will regulate
    their density as well" (HotOS §3.1).
  - That is population control by background decay plus a conserved raw material,
    with no reaper.
- **Demon Horde Sort** (HotOS §3.4; ALIFE 14; AAAI 2016):
  - Setup: a 128×64 region. Input columns emit random-valued Datum atoms, which a
    self-maintained horde of Sorters carries right-to-left while nudging them up or
    down based on comparison with the previous datum. DReg randomly destroys atoms,
    including data.
  - Results: "remarkably resilient, recovering from insults like flipping bits in many
    atoms at once, or flat-out resetting two-thirds of the grid sites". More load made
    it work better ("like a 'sorting muscle'") until inputs could not be cleared.
  - It "doesn't" sort correctly: "correctness really isn't an option ... Welcome to
    best-effort" (AAAI 2016).
  - Tiled vs untiled 160×96 runs (ALIFE 14 Fig. 6): "no obvious differences in sorting
    accuracy" despite about 30% event-rate variation across tile regions.
- **Cells and structures:**
  - Membranes use a "bond exclusion" (`BX`) header bit that restricts diffusion
    through a ring of atoms. Two cells can exchange messages over self-healing wire
    (HotOS §3.2–3.3).
  - Self-healing wire survives much higher atom-loss rates than singly or doubly
    linked chains (HotOS Fig. 4).
  - A self-assembling four-port switch was reset on three of its four tiles at
    2,500 AEPS (average events per site) and "by 3000 AEPS, it is almost healed"
    (AAAI 2016).
  - The 2018 "C211" digital protocell (ALIFE 2018, doi 10.1162/isal_a_00021) is
    described as a variable-density "cytoplasm" using gossip, inside an asymmetric
    "bilayer membrane", written in SPLAT (2D pattern transforms on ulam), and
    supporting splitting and fusion. Abstract seen via search snippet only; the MIT
    page returned 403 (**UNVERIFIED** beyond the abstract).
- **ulam:** a language for MFM elements, compiling to C++ (*Artificial Life* 22(4),
  2016, doi 10.1162/ARTL_a_00212, abstract via Semantic Scholar).
- **T2 Tile:** Ackley's hardware tile project, still running around 2018–2024 per
  secondary sources; not fetched (**UNVERIFIED**).

---

## 6. Checks on the prior report and on PLAN.md

- **Knierim 2026 citation: real**, with the correct arXiv id, title and first author.
  The summary in `Review.md` is accurate as far as it goes. Missing:
  - It is the *same team* (Agüera y Arcas is a coauthor).
  - It measures *discovery* with a new detector, not takeover.
  - The "at least as easily" result needs a tuned byte distribution (CUST/CUST64).
    With uniform bytes at BFF-like change rates, the random walk is 40–190× *slower*
    than the soup.
  - The caps are on *mergers* (copy events), not on ancestry in general.
- `Review.md`'s "counterexample substrate" is correct: SUBLEQ, plus the RSUBLEQ4
  variant.
- `Review.md` names Computational Life and Knierim as "the most directly relevant
  recent computational-origin results". It misses Cicala et al. 2026, which is the
  only one with a computation cost and is arguably the most relevant to evo.
- `References.md` reproduction repos: both exist.
- **PLAN.md §2 table, "debris essential":** not supported by the BFF paper, the
  cubff code or Knierim et al. The word does not appear, and no ablation of
  "debris" was done. The closest idea is that the partner tape is "food" /
  "available real estate". Suggest removing it or rewording to "overwrites
  neighbours; no seed, no fitness function; replicators arise even at zero
  mutation".
- **PLAN.md §5.3.1 (register vs stack):**
  - BFF is a two-head tape machine, neither register nor stack.
  - Z80 worked in a 2D *pairwise* grid of 16-byte programs.
  - 8080 was tried only as a long tape and produced only 2-byte *non-looping*
    replicators.
  - Long-tape Forth *failed* with its first ISA and worked with a second one.
  - So the paper supports "ISA details and minimal replicator length matter more
    than the register/stack class". It does not support "both styles work".

---

## 7. UNVERIFIED items (collected)

1. The source of the "capping merger depth/width stops emergence" claim that Knierim
   et al. test. It is not in the 2024 paper or in book chapter 1.
2. Knierim et al.: soup size for the 2.5e6-interaction baseline, and the per-limit
   numbers in their Fig. 4.
3. Which detector version the Knierim paper used. The public cubff main branch
   constants differ from the paper text.
4. Whether *Computational Life* was ever published in a peer-reviewed venue. As of
   July 2026 it is still cited as an arXiv preprint.
5. Whether the high-mutation drop in Fig. 6 (0.5–1%) reflects fewer replicators or a
   noise-depressed complexity metric.
6. The "41-site event window": derived from R = 4 city-block in HotOS 2011; the
   Computer Journal 2013 full text was not read.
7. The C211 protocell (ALIFE 2018): abstract via search snippet only.
8. The current state of the T2 Tile project.
9. Independent reproduction details (jonamiki numbers; repo code not reviewed).
10. Cicala et al.'s parameter table: the PDF table extracted garbled. Values quoted
    above come from the running text and figure captions.

---

## Design implications for evo

These are judgements drawn from the sources above. Items marked *(inference)* are my
reasoning, not a published result.

### A. BFF's result rests on features evo does not have

1. **Free, forced execution.**
   - In BFF every tape is executed as the first half of a pair on about half its
     interactions, for up to 8,192 steps, at no cost, forever. The long-tape variants
     do the same by starting execution at random positions.
   - Nothing has to "stay alive" to keep computing. The pre-life phase, where
     imperfect copy fragments pile up, is paid for by the environment.
   - In evo, a random organism pays for every instruction, and a dead organism's
     bytes are never executed again. **A no-seed evo soup will likely die before the
     pre-life phase starts** unless there is some free or background execution
     *(inference)*.
   - None of the substrates where replicators emerged (BFF, Forth, Z80, 8080)
     charges per instruction, and Ackley's MFM treats computation as free as well.
     Cicala et al.'s "metabolic" cost is a mild bias applied only after task
     validation.
2. **Imposed mixing.**
   - Pairing is done by the environment (a global shuffle, or random neighbours in
     2D). In evo, interaction happens only if code reaches out: `searchf`, `copy`,
     `store` within the locality radius.
3. **No ownership, so replication by overwriting.**
   - BFF replicators spread by overwriting the partner tape. The partner becomes a
     replicator the next time it is executed as the first half.
   - Evo's §5.2 appears to allow writes into neighbours. If so, the evo analogue of
     BFF replication is a **virus**: code that overwrites a live neighbour's body
     where the neighbour's instruction pointer will run it. Such a virus needs no
     `alloc`/`divide` at all.
   - *(inference; worth a hypotheses-log entry)* In a no-seed evo run, the first
     replicators to appear will be overwriters, not `alloc`/`divide` organisms,
     unless foreign writes are costly or guarded.
4. **Two independently steerable pointers that start inside the code.**
   - In `bff_noheads` both heads start at byte 0 (the code itself). The ops `<>{}`
     move each head by one with a single byte, and `.`/`,` copy between them. That is
     why a full replicator loop fits in about 5 bytes (`[<,}]`).
   - Long-tape BFF needed head1 offset from the instruction pointer by more than 8
     bytes; otherwise trivial non-looping replicators took over.
   - Compact copy primitives win after emergence: Z80 LDIR beat PUSH chains, and
     `bff_selfmove` has a copy that auto-advances the head.
5. **A very short minimal replicator.**
   - The working substrates had first replicators of about 1–10 bytes: Forth `0C`
     (1 byte), BFF loops of about 5–8 bytes, Z80 PUSH chains, 8080 2-byte pairs.
   - SUBLEQ (60 bytes) and even RSUBLEQ4 (25 bytes) never emerged.
   - The authors single out minimal replicator length as the key predictor.
     Cotler et al. 2025 show formally that universality alone is not enough.

### B. An urgent check on the Phase-1 op set (PLAN §5.3.3)

*(inference; not from the literature)*

- As drafted, only `A` ever receives an address (from `self` and `alloc`), plus `D`
  from `search`. There is no op that moves `A` into another register, since `add r`
  and `sub r` write only into `A`.
- `copy` needs `B` to hold a source address. No op copies an address into `B`: it can
  only receive constants (`lit`), single bytes (`load`), the body length (`self`), or
  arithmetic on those.
- `self` and `alloc` both overwrite `A`, so the parent start and the child start
  cannot both be held at once.
- If this reading is right, **even a hand-written ancestor cannot express a copy
  loop.** Emergence from soup would then be impossible by construction.
- Cheap fixes suggested by the BFF and Z80 results, any one of which would work:
  - Initialize registers at birth relative to the body, BFF-heads style: for
    example `A = B = own start` at `divide`.
  - Add a register move (`mov r`: r = A) or a swap.
  - Make `copy` post-increment both `A` and `B`, like `bff_selfmove` and Z80
    `LDI`/`LDIR`.
- Example: with `B = own start` at birth and an auto-incrementing `copy`, the minimal
  `alloc`/`copy`/`divide` replicator is about 10–12 bytes:
  `lit C L; lit D -k; alloc C; loop: copy; dec C; skipz C; jmpr D; divide`. That is
  in the range where the paper saw emergence.
- **Before building Phase 4, write the ancestor by hand and count its bytes.**

### C. What a faithful BFF-style benchmark inside evo needs

Run it as a separate harness mode in `evo-core`, not as the world.

1. **Reproduce BFF exactly first, as a calibration.**
   - 2^17 tapes of 64 bytes; uniform init; per-epoch random permutation into disjoint
     pairs; concatenate to 128 bytes.
   - Per-byte *replacement* mutation at 2^-12 on the joined tape before execution.
   - Execute `bff_noheads` semantics: heads start at 0 and wrap mod 128; the
     instruction pointer starts at 0 and does not wrap; unmatched brackets halt; the
     step limit is 8,192 bytes read, counting no-ops.
   - Split back into two tapes.
   - Targets to hit over seeds: about 40% transitions within 16k epochs; about 44% at
     zero mutation; about 50% with the fixed shuffle and no noise; about 22% takeover
     for the seeded 128-epoch run.
   - cubff testdata (`testdata/bff_noheads.txt`) can be used as a golden-output test.
2. **Then swap in evo's ISA in the same harness.**
   - Keep the same pairing, budget and mutation, and remove energy and ownership.
   - Treat the 128-byte pair as the world, with addresses mod 128.
   - Reset registers and set the instruction pointer to 0 at each interaction.
     Replication there means copying into the other half.
   - This isolates "is the evo encoding evolvable?" from world rules. It is the
     §5.3 criterion ("with a random soup and no seed, do replicators emerge?") made
     testable.
3. **Then a long-tape mode.** One shared array, random start positions, a fixed op
   budget, and a head/register offset sweep (0, 8, 12, 16). This is the closest step
   to the evo world.
4. **Then add evo physics one at a time,** recording which addition kills emergence:
   energy cost (with an energy grant per execution), ownership and guards,
   persistent instruction pointers instead of restart-per-interaction, and
   `alloc`/`divide`.
5. **Metrics:**
   - High-order entropy: h0 minus brotli-q2 bits per byte over the whole array. Use
     the Rust `brotli` crate for comparability with the paper.
   - Unique-token count from 64-bit tracer tokens: (epoch, position, char) per byte,
     carried by copy ops. This costs 8× memory in the harness only.
   - A Knierim-style detector (run candidate + noise for 5 chained generations over
     about 10–13 branches, then byte-agreement score) to time *discovery* separately
     from *takeover*.
6. **A cheap pre-test before any soup run, after Knierim et al.**
   - Sample random evo genomes (uniform bytes, and an operator-enriched
     distribution). Run each alone in a small sandbox with ample energy. Count
     replicators per sample.
   - Reference points: BFF gives 1 in 2.9e7 uniform 64-byte programs, and 1 in 9.4e4
     for CUST64.
   - If evo's density is many orders of magnitude lower, no desktop soup will find
     one. Fix the ISA first.

### D. Other concrete points

- **Mutation level.** BFF transitions were most frequent around 0.1% per byte per
  epoch. At 1%, 94% of runs failed to cross the threshold in 16k epochs. Keep evo's
  default noise per byte per copy generation well under about 0.5%, and sweep it.
  Zero noise is a required control, since BFF still works there.
- **2D layout.** BFF 2D used a bounded grid with Chebyshev radius 2. It slows
  takeover (time proportional to grid side) and keeps several variants coexisting,
  which is what evo wants. Ackley says wrap-around is acceptable in 2 scalable
  dimensions, so evo's torus is fine.
- **Determinism vs Ackley.** Ackley's objection is about scaling hardware; a seeded
  simulation can stay deterministic.
  - Take his warning seriously anyway: models whose behaviour depends on update
    order are fragile.
  - Randomize (seeded) the order of organism execution, and never let local rules
    read global quantities like population size. ALIFE 14 names this explicitly as
    non-scalable.
  - Add a robustness check: same config, different scheduler seeds. Qualitative
    outcomes should agree.
- **Multi-core** *(inference)*. MFM's model of non-overlapping, exclusively locked
  event windows running in parallel is a direct template. Partition the torus into
  regions larger than the locality radius, and run non-adjacent regions in parallel
  in a fixed, seeded colouring order. This keeps determinism, unlike cubff's lockless
  long-tape Forth or best-effort HPC (Moreno et al. 2026).
- **No reaper, density control.** DReg/Res shows a known working pattern: random
  background deletion plus reproduction only from a conserved raw material (evo:
  `alloc` only from free or debris bytes). It regulates density without a reaper.
  Ackley's structures were designed rather than evolved. In evo, repair must evolve,
  so the decay rate must leave repair affordable.
- **Size vs robustness.** Long-tape Forth replicators grew non-functional "heads" as
  landing pads against mid-code starts. Cicala's compact LDIR replicators won on
  copy robustness. Expect evo genome length to be shaped by (a) where execution can
  start and (b) copy fidelity. Log both.
- **Open-endedness metric.** Adopt ASAL's historical nearest-neighbour novelty
  *formula* over a genome or behaviour embedding, alongside high-order entropy and
  tracer tokens. Do not use CLIP on renderings of the byte array.
