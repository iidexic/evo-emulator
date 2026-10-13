# Recent work, round 2 cluster 5: emergence in program soups (ALIFE proceedings 2023–2026)

Compiled 2026-10-12. Purpose: cluster 5 of `docs/research/literature-recent-plan.md`
("# Round 2"), for Phase 4's BFF calibration harness (PLAN §8) and the
minimal-replicator question (H3). It answers round-2 questions 1 (does Dušek et al.
2026 change Phase 4's protocol?) and 4 (is Myers et al.'s pseudo-perplexity computable
from evo's records, and does it add anything over knockout complexity?), plus what this
cluster says about minimal replicator length and soup size. Round 1's file on the same
topic is `recent-2-soup-emergence.md`; nothing here repeats it.

## How this was checked

- **Full texts of the five 2026 papers** came from the complete ALIFE 2026 proceedings
  volume, which the conference's emerging-researchers group hosts on GitHub:
  https://github.com/emerging-researchers-alife/conference_proceedings, file
  `ALIFE2026Proceedings.pdf` (Git LFS, 115,082,459 bytes, 1,109 PDF pages, SHA-256
  `0667242b740ec76fa19a987ceda6737223fbb19688c9bda8d99009507ecd0eee`, matching the LFS
  pointer). I found the link on Dušek et al.'s companion website. The volume's printed
  page numbers equal the PDF page minus 20. Each paper was cut out with pypdf and saved
  to `docs/downloaded-papers/` (gitignored): `isal.a.986_Dusek.pdf` (pp. 478–486),
  `isal.a.974_Myers.pdf` (pp. 369–375), `isal.a.976_Horiguchi.pdf` (pp. 385–392),
  `isal.a.1044_Perrico.pdf` (pp. 1003–1011), `isal.a.1020_HillRoy.pdf` (pp. 789–799).
  I checked the first and last pages of each cut. Text was extracted with `pdftotext`;
  where symbols were lost (×, ≈, ≥, minus signs on exponents) I re-read them with pypdf.
  Page numbers below are the printed proceedings pages.
- **Authors' code and data**, cloned and read:
  https://github.com/koutefra/bff-replicator-discovery (commit 28d786d, 2026-08-19,
  Dušek et al.: README, `docs/REPRODUCIBILITY.md`, `data/paper/*.csv`,
  `expected_results.json`, `data/pathways/summary.json`, the CUDA kernels for the
  regimes and the replication test, and the companion website's source
  `web/index.html`), and https://github.com/tydymy/bff-functional-information
  (commit d5ef96c, 2026-08-27, Myers et al.: README, METHODS.md, WALKTHROUGH.md,
  `simulation/*.py`, `analysis/train_bff_gpt2.py`).
- **Extended version of Horiguchi & Sayama**: arXiv 2607.28219 (PDF,
  https://arxiv.org/abs/2607.28219), a 26-page review by the same authors that
  includes the ALIFE result plus a boundary-condition control. It is cited separately
  from the ALIFE paper.
- **Abstract only**: Crossref (`api.crossref.org/works/10.1162/<suffix>`) for 2026,
  OpenAlex (`abstract_inverted_index`) for 2023 and 2024. Claims beyond an abstract
  are tagged **UNVERIFIED**.
- direct.mit.edu was not fetched (it returns HTTP 403 to scripts).
- Nothing is from memory. Arithmetic and judgements of my own are marked
  "(inference)". Numbers from the code repositories are labelled as such, because
  a repository is not the paper.

## Terms used below

- *BFF*: the self-modifying Brainfuck variant of Agüera y Arcas et al. 2024. Two
  64-byte programs are joined into one 128-byte tape, executed (code and data share
  the tape, so execution can rewrite either program), and split again.
- *Epoch* (Dušek): one round in which every program in the population takes part in
  exactly one interaction.
- *Execution* or *interaction*: one run of a joined 128-byte tape.
- *Discovery*: the first time a program passes the replication test. *Takeover*:
  replicators persist in the soup for at least 500 epochs. Round 1 called takeover
  "emergence" when following the original paper's soup-level transition.
- *Regimes U, N, R* (Dušek): uniform sampling with no execution; execution against a
  fresh random partner each time, with no coupling between population members; the
  standard soup.
- *Focal / partner tape*: in a discovery event, the right-hand half that becomes the
  replicator, and the left-hand half that acts on it.
- *Pre-replicator loop*: a short copy loop that is completed only when two programs
  are joined, and whose execution writes a replicator onto the focal tape.
- *Pseudo-perplexity*: a language model's surprisal at each position of a sequence.
  For a *masked* model, each position is hidden in turn and predicted from both
  sides; for a *causal* model, each position is predicted from the bytes before it
  only. Low surprisal means a predictable, conserved position.
- *Functional information* (Hazen et al. 2007, as quoted by Myers et al. p. 369):
  I(Ex) = −log F(Ex), where F(Ex) is the fraction of all configurations that reach a
  degree of function Ex.
- *Knockout complexity* (MODES): the number of genome sites whose replacement breaks
  function in a test harness (`recent-3-oee-measures.md` §4).

---

## 1. Short answers

1. **Dušek et al. 2026 changes Phase 4's protocol, in what it measures rather than in
   the soup it runs.** In standard BFF at 2^17 programs with no mutation, a
   replicator is *discovered* in 99 of 100 runs within 16,000 epochs, but only 45 of
   100 runs reach *takeover*. The original paper's "40% of runs transition" (44% at
   zero mutation, `bff-and-recent.md` §1.5) is therefore a takeover-type number.
   First-discovery time is a measurement every run produces, so a rule-by-rule sweep
   on it has far more statistical power than a yes/no fraction (inference). The
   paper's headline, that population coupling halves the discovery rate, holds per
   epoch and per focal slot. It disappears per executed tape, because regime N runs
   2^17 tapes per epoch against R's 2^16, and the two medians fall at 1.60 × 10^8 and
   1.61 × 10^8 executions (inference from the code and the committed data, §2.9).
   The harness should therefore report time in executions as well as in epochs. It
   should also run U and N as controls next to R, and log operator frequencies. §8.1
   gives the full list.
2. **Myers et al.'s pseudo-perplexity can be computed from evo's records but adds
   little.** `genomes.csv` holds every body's bytes and `func_hash`, and
   `census.csv` holds the counts. Their BFF model is a 154,560-parameter character
   GPT-2 (my count from their configuration) trained for about 10 minutes on CPU.
   Their BFF result, however, comes from a genetic algorithm on classic Brainfuck
   (fitness = output length), not from a self-replicating soup. Its
   conserved-versus-variable contrast (r = 0.99) is built in by the mutation
   operator, which per their code draws conserved sites from 8 opcode values and
   variable sites from 248 others. For evo's fixed-length bodies (21 bytes in every
   E007 window), per-column entropy over the census gives the same conservation
   profile without a model, and knockouts test function directly (inference, §3.4).
3. **Minimal replicator length (H3).** No paper in the cluster measures it against
   emergence. Dušek gives BFF numbers: a 9-instruction reverse-copy core, a
   5-instruction precursor, and a density of 7.1 × 10^-11 replicators per random
   64-byte program. That density equals about 33.7 bits of functional information
   (inference). The authors name "varying the minimal replicator length" as future
   work. Perrico & Banzhaf evolve a copier with 3 active instructions, but it copies
   into a buffer it is given, without allocating or dividing, so it is not a
   minimal replicator. Dušek's U regime is the template for H3's harness search
   (§8.3).
4. **Soup size.** Horiguchi & Sayama's size threshold (L ≈ 300–320) is an artefact
   of open boundaries. In their extended version, periodic boundaries give runaway
   at every L tested. It sets nothing for a well-mixed BFF soup or for evo's ring,
   which has no edge. The useful size handle comes from Dušek: in N, discovery is
   close to a constant rate per program, so what matters is the total number of
   executions, not the soup size (inference, §8.4).

---

## 2. Dušek, Papadopoulos & Hudcová 2026, "Replicator Discovery Is Faster Without Population Coupling in a Self-Modifying Program Soup"

ALIFE 2026, pp. 478–486, https://doi.org/10.1162/isal.a.986, CC BY 4.0. Authors:
František Dušek (Czech Technical University in Prague), Vassilis Papadopoulos and
Barbora Hudcová (EPFL). Full text read from the proceedings volume (see "How this was
checked"). Code and data: https://github.com/koutefra/bff-replicator-discovery,
derived from Google's cubff (Apache 2.0). Its README says the companion website is
"Updated framing and additional analysis of the ALIFE 2026 paper"; numbers taken only
from the site or the repository are labelled so.

### 2.1 Substrate and protocol (pp. 479–480)

- Tapes of L = 64 bytes. Ten byte values are instructions, the rest are "neutral
  bytes". The instruction pointer and the two heads (head0, head1) all start at 0,
  and the heads wrap modulo the tape length. Execution ends when the instruction
  pointer leaves the tape, when a bracket needs a jump that has no match, or after
  2^13 steps (p. 479).
- Soup: 2^17 programs. Each epoch, programs are paired at random into disjoint pairs,
  joined "in a random order", executed and split. "No explicit fitness function,
  mutation operator, or reproduction mechanism is defined" (p. 479). The launcher
  passes `--mutation_prob 0.0` and `--lang bff_noheads` for all three regimes
  (`experiments/run_regimes.py`), so mutation is off throughout. The original
  protocol in PLAN §8 uses 2^-12.
- N and R ran 16,000 epochs × 100 runs each. U's sample count is matched to them
  (pp. 479–480).

### 2.2 Definition of "replicator" (p. 480)

- They adopt "without modification the behavioral replication test from the publicly
  released implementation of Agüera y Arcas et al. (2024)". The candidate P sits on
  the left of the tape with a random partner on the right, in each of 13 independent
  trials. The offspring then replaces the parent for four more generations.
- A byte position is *stable* if the same value appears in more than 3 of the 13
  trials. On the parent half it must also equal P's original byte.
  score(P) = min(S_parent, S_offspring), and P is a self-replicator if
  score ≥ 60 (of 64): "at least 94% of the tape is copied reliably across random
  partners. Below this threshold, replication typically depends on partner-specific
  structure rather than autonomous copying."
- Discrepancy: the paper says each generation uses "new random partners" (p. 480).
  The kernel (`CheckSelfRep` in `src/common_language.h`) reuses the trial's own
  partner (`noise[]`) in all five executions, and the companion site says
  "against that trial's same partner". The code also moves the offspring from the
  right half to the left before each extra generation.
- Takeover: "robust self-replicators ... appear and persist continuously in the
  population for at least 500 epochs" (p. 480).

### 2.3 The three regimes (pp. 479–480, Table 2)

| Regime | Execution | Population coupling | Partner |
|---|---|---|---|
| U, uniform sampling | no | no | none: programs drawn uniformly from {0..255}^64 and tested |
| N, noise interaction | yes | no | a fresh uniform random program each interaction; the partner is discarded and the soup program keeps its modified half |
| R, population-coupled | yes | yes | other soup programs; both halves return to the soup |

In N, "programs never interact with other soup members and cannot propagate through
the population, but self-modification of each program accumulates over time"
(p. 480).

### 2.4 Results

| Quantity | U | N | R | Source |
|---|---|---|---|---|
| Replicators found | 15 in ≈ 2.1 × 10^11 samples | 100/100 runs | 99/100 runs | pp. 480–481 |
| Per-program probability | ≈ 7.1 × 10^-11 (repo: 15 / 209,715,200,000 = 7.15 × 10^-11) | | | p. 480; `expected_results.json` |
| Median first discovery (epochs) | ≈ 7.4 × 10^4 (geometric model, 1 epoch = 2^17 samples; repo 73,935.7) | 1,220 | 2,453 | pp. 480–481 |
| Speed-up over U | | ≈ 60× | ≈ 30× | p. 481 |
| Shape of first-discovery distribution | | about geometric (constant rate per epoch) | early delay, peak near epochs 2,000–2,500 | p. 481 |
| Discovery events per run (0 → ≥1 replicators) | | ≈ 8 (repo 8.19; 819 in total) | R_cond ≈ 4 (repo: 301 events, exposure-normalised 3.98) | p. 481 |
| Takeover | | n/a | 45/100 runs, mean takeover epoch ≈ 6,000 (repo 6,076) | p. 481 |

First-discovery quantiles, computed by me from `data/paper/discovery_times.csv`:
N: 10th percentile 180, 25th 642, 75th 2,348, 90th 3,846, range 20–8,554 epochs.
R: 586, 1,686, 4,789 and 7,508, range 96–14,282.

All replicators, in every regime, are one family: a *reverse-copy* mechanism. "a
program writes a reversed copy of itself onto the partner tape during execution.
Replication proceeds over two interactions--the first produces a reversed copy, the
second reconstructs the original program". They "share a compact functional core of
nine instructions, which need not be contiguous". There are two loop types,
H0-type `[<},]` and H1-type `[>{.]`, and the minimal embedding is `[>{.].{>[`
(Fig. 1, pp. 480–481). Variants mixing the two loop types are common under U but
"nearly absent" in N and R (p. 481).

### 2.5 Mechanism of discovery from a non-replicator (pp. 481–483)

- 100 discovery events were reconstructed (50 N, 50 R). "In all cases, a
  non-replicating program becomes a functional replicator in a single interaction,
  without intermediate partially functional states, and with large-scale rewrites of
  the resulting program (typically 32–64 bytes modified)" (pp. 481–482).
- The replicator appears on the right-hand (focal) tape "in all sampled discovery
  events" (p. 482). The repository's `data/pathways/summary.json` gives 50/50 for N
  and 48/50 for R.
- Dominant pathway, 43/50 in N and 45/50 in R: "a short loop is completed across the
  interaction boundary and executed, inducing an asymmetric transport-and-copy
  process that constructs a reverse-copy replicator on the focal tape". The other
  events in N go by "arithmetic activation of neutral bytes" (`+` and `-` turning
  non-instruction bytes into instructions). In R the exceptions are "minor variants or
  detection artifacts" (p. 482).
- A pre-replicator loop, e.g. `[<},}]`, is one that "(i) contain[s] at least one copy
  operation (. or ,) transferring values between the two heads, (ii) induce[s]
  non-zero net displacement of both heads over one traversal, and (iii) exclude[s]
  disruptive arithmetic operations (+, -)". Head strides are "typically 1 and 2". In
  about 80% of events in both regimes, the closing `]` comes from the focal tape and
  the rest of the loop from the partner (p. 482). Fig. 3 (p. 483) shows the jump on a
  reduced 16-byte tape: the loop is completed at t = 0 and the tape stabilises at
  t = 307. Step counts on full 128-byte tapes are not given.
- From the companion site only (not in the paper): the 5-instruction fragment has
  probability 6.6 × 10^-7 per uniform program "(the five bytes in this order among 64
  positions, everything else neutral)", about "ten thousand times more common than
  the replicator it helps build".
- Two-factor account (p. 483): discovery rate(t) ≈ C · M̂(t) · Â(t), with a fitted
  C = 30, described as "a calibration constant rather than a mechanistic parameter".
  - M (motif availability): the number of programs that, placed on the left, turn at
    least one fixed focal tape into a replicator. It is sparse ("typically less than
    one motif-compatible program per run per sampled epoch"). In R it rises, peaks
    "around epoch ≈ 3800", then declines; N is a flat baseline (p. 482).
  - A (activation probability): the fraction of programs that at least one fixed
    partner turns into a replicator when they sit on the right. In R it is first
    comparable to or above N, then "falls below that of N and remains lower for most
    of the run" (p. 482).
  - My pooled averages over 2,000-epoch windows, from `data/paper/activation.csv`
    and `pre_replicator_availability.csv` (fixed tapes of all origins):
    - A, N: 0.120 (0–2k), 0.106, 0.101, then 0.099 to the end.
    - A, R: 0.134 (0–2k), 0.023 (2–4k), 0.011 (4–6k), 0.038, then 0.073–0.082.
    - M as a fraction of tested programs, N: 1.3–2.1 × 10^-6 throughout.
    - M, R: 1.2 × 10^-6 (0–2k), 3.6 × 10^-6 (2–4k), 2.6 × 10^-6 (4–6k), then
      0.4–0.9 × 10^-6.
  - Assay size: the paper says "8 independent runs per regime; for R, only runs without
    takeover" (p. 482). The repository's REPRODUCIBILITY.md and `activation.csv`
    (`seed_count` 4) show 4 seeds for activation; availability used 8.

### 2.6 Operator attractors and the perturbation test (pp. 484–485)

- N converges to a "bracket-enriched attractor" (`[` accumulates). R_cond converges to
  a state dominated by `<`, `>` and `,`. "By epoch 4,000, the R_cond soup contains
  approximately 20% BFF instruction bytes ... In N, this figure remains below 8%"
  (p. 484).
- In a toy run, the rate of one-step uniform rewrites of at least 30 contiguous bytes
  "is approximately 3.5× higher in N" per interaction (p. 485). Repository
  (`uniform_rewrite_summary.csv`): 871 events in 1,600,000 interactions for N and 125
  in 800,000 for R, a ratio of 3.484.
- Perturbation: "We forked four N runs at epochs 500–8,000 and continued each fork
  under R dynamics; in all cases without takeover, the population trajectory moved
  away from the N attractor and toward the R_cond attractor" (p. 485).
- Their reading (p. 485), offered as plausible rather than shown: R's denser
  instruction content raises motif availability but makes the execution environment
  "more interference-prone", which lowers activation.

### 2.7 Limitations and compute, per the authors (pp. 485–486)

- The M × A decomposition is "an approximate first-order model". The causal link from
  attractor to activation "has not been isolated directly". Results are "specific to
  BFF and to the dominant reverse-copy replicator class". "varying the minimal
  replicator length may provide a way to study how discoverability scales with
  replicator complexity".
- Compute: "NVIDIA A100 40GB GPU. A typical 16,000-epoch run required approximately
  2–4 hours" (p. 486). The paper says the implementation is "available from the
  authors upon reasonable request"; the repository has been public since 2026-08-19.

### 2.8 What the code adds

- Regimes are command-line flags on cubff's `main`: U is `--reinit_each_epoch`, N is
  `--random_partner_interaction`, and R is the default. There is also an
  `--allowed_interactions` / interaction-pattern path for structured pairing
  (`src/common_language.h`).
- **Executions per epoch differ between the regimes.** N runs one kernel thread per
  program, 2^17 executions per epoch (`num_runs += num_programs`). R runs one per pair,
  2^16 (`num_runs += num_indices`, with `num_indices = num_programs / 2`). In N, a
  random bit (`a_first`) puts the soup program on the left in half of its executions.
- The repository says the CPU smoke profile (`make CUDA=0 smoke`, 128 programs,
  3 epochs) needs no GPU, and that full runs need `--confirm-full` and CUDA.

### 2.9 Discovery rate per interaction in each regime (inference)

The paper compares regimes per epoch, and an epoch matches the number of *programs
evaluated* (2^17, p. 480), not the number of tapes executed. Converting with §2.8:

| Regime | Tapes executed per epoch | Retained right-hand (focal) slots per epoch | Median first discovery | Executions to median | Rate |
|---|---|---|---|---|---|
| U | 0 (2^17 samples) | n/a | 7.4 × 10^4 epochs | n/a | 7.15 × 10^-11 per sampled program |
| N | 2^17 = 131,072 | 2^16 (soup program on the right half the time) | 1,220 epochs | 1.599 × 10^8 | about geometric: ln 2 / 1,220 = 5.7 × 10^-4 per epoch, so 4.3 × 10^-9 per execution |
| R | 2^16 = 65,536 | 2^16 | 2,453 epochs | 1.608 × 10^8 | not constant; median-equivalent 4.3 × 10^-9 per execution |

The factor of two the paper reports holds per epoch (per program updated) and per
retained focal slot. Per executed tape, which is also per unit of compute, N and R
reach their median first discovery after the same number of executions (ratio 1.005).
The paper does not discuss this normalisation. It does not overturn the mechanism
results (§2.5–2.6), which are measured within regimes, but it does change which
headline a harness reports.

### 2.10 Transfer to a ring with locality (inference)

- **What carries over.** The event that matters is that code from one region,
  completed by a byte of the neighbouring region, runs a copy loop that rewrites the
  neighbour in one go. On evo's ring, every region is permanently joined to its
  neighbours, and an instruction pointer (IP) that walks off one body runs the next
  one. E005's "falling into" the body behind is the seeded form of this. So the
  cross-boundary completion has a direct analogue, and without the pairing step it
  needs no luck in who meets whom.
- **What does not carry over.**
  1. Partners: ring neighbours are fixed and evolve together, which is always R-like.
     Nothing on the ring corresponds to N's fresh random partner, unless noise keeps
     refreshing free bytes.
  2. Write protection: a living organism's bytes cannot be written by another
     organism (PLAN §5.3). Activation by rewrite can therefore only target free or
     debris bytes. That is everything in a seedless soup at first, but any organism
     that forms is then closed to further activation.
  3. A replicator in evo must `alloc` and `divide`. A loop that only lays down bytes
     is not yet a replicator, so the replication test has to be evo's own (the
     `--classify` replicator class), not cubff's stable-byte score.
  4. Energy: BFF's 32–64-byte rewrite in a single interaction is free up to 8,192
     steps, whereas in evo every step is paid. Whether the precursor-to-replicator
     jump fits in one start-execution event's energy is exactly what the energy step
     of the sweep would test.
- **What the ring version should log.** By analogy with Dušek's attractor result:
  the operator histogram, and the fraction of instruction bytes, in free and debris
  memory over time. `world.bin` already stores world bytes and ownership state at
  every census.

---

## 3. Myers, Song & Bartko 2026, "Prediction and Entropy of Evolving Sequences: A Transformer-Based Estimator of Functional Information"

ALIFE 2026, pp. 369–375, https://doi.org/10.1162/isal.a.974, CC BY 4.0. UC San Diego.
Full text read from the volume. Code: https://github.com/tydymy/bff-functional-information.

### 3.1 What the paper says

- Proposal: "pseudo-perplexity, the per position surprisal of a masked language model,
  as an estimator of this biological functional information" (abstract, p. 369).
- BFF part (pp. 370–373):
  - "Five independent runs each initialized 300 clonal individuals from a single
    ancestor genome, evolved over 2,000 generations under tournament selection (k = 5)
    with per-position mutation rate 0.01. Fitness was defined as BFF program output
    length (zero output = lethal)" (Methods, p. 373).
  - Each 64-byte genome "contains three conserved opcode blocks at fixed positions
    (0–6, 13–20, 35–40) encoding core replicator logic, interspersed with variable
    NOP regions" (p. 373).
  - Table 1 (p. 370) defines `.` as "Output byte at data pointer" and `,` as "Input
    byte to data pointer". That is classic Brainfuck with a separate data tape, not
    the self-modifying BFF of Agüera y Arcas et al., even though the introduction
    motivates the work by that paper's spontaneous emergence (p. 369).
- Model for BFF (p. 373): "A character-level GPT-2 (4 layers, 4 heads, 64-dim
  embeddings, vocabulary 257) was trained for 100 epochs on evolved BFF genomes (30 per
  snapshot, deduplicated; learning rate 1e-3, batch size 32). Per position
  pseudo-perplexity was computed as the causal LM loss: −log P(x_i | x_<i)". So the
  BFF half uses a causal model, not the masked model the abstract describes.
- Results:
  - BFF conserved vs variable positions: Mann–Whitney U, r = 0.99 (p. 371).
  - 16S rRNA with a fine-tuned Nucleotide Transformer (NT-v2-50M): p = 1 × 10^-16,
    r = 0.2.
  - Essential vs non-essential genes: p = 6.1 × 10^-20, r = 0.14.
  - Genome pseudo-perplexity vs essential-gene fraction over 12 organisms:
    Spearman ρ = −0.58, p = 0.048 (pp. 371–372).
  - Drift: BFF variable-region pseudo-perplexity rises with Hamming distance from the
    ancestor (β = 3.54, p = 3.7 × 10^-127), conserved regions modestly (β = 0.30,
    p = 3.8 × 10^-11). The 16S equivalents are β = 1.10 (p = 1.5 × 10^-3) and
    β = 0.52 (p = 3.9 × 10^-2) (p. 372).
- Authors' limitation: "The BFF simulation employs a simplified genome architecture
  with predefined conserved and variable blocks, which overstates the sharpness of
  functional boundaries relative to biological genomes" (p. 374).

### 3.2 What the code shows beyond the paper

From `simulation/bff_interpreter.py` and `simulation/evolution.py`:

- The conserved blocks are fixed opcode strings: `+++++[>` at 0–6, `+++++<-]` at 13–20,
  and `>...<<` at 35–40. The ancestor is random NOP bytes with these blocks stamped in.
- Mutation: "Conserved positions mutate within opcode space; variable positions mutate
  within NOP space". A conserved site is redrawn from the 8 opcode bytes and a
  variable site from the 248 non-opcode bytes. METHODS.md says the same thing. The
  paper's Methods give only "per-position mutation rate 0.01".
- The interpreter is classic Brainfuck: a 256-cell data tape separate from the
  program, output collected by `.`, and `,` setting the cell to 0. Programs do not
  copy themselves; the genetic algorithm copies them.
- Training set: 30 genomes per snapshot. Snapshots are taken every 50 generations
  (41 per run including the last) plus 30 final genomes, over 5 runs, so at most
  6,300 genomes before deduplication (computed from the code).

### 3.3 What the estimator needs

- BFF model: GPT-2 with `n_embd=64, n_layer=4, n_head=4, n_inner=128, n_positions=64,
  vocab_size=257`. That is 154,560 parameters with tied output embeddings (my count
  from the configuration in `analysis/train_bff_gpt2.py`).
- Training time, per WALKTHROUGH.md: "~10 minutes on MPS/CPU, ~3 minutes on CUDA".
  The authors' machine was an "Apple M2 Max with 32 GB" (METHODS.md).
- Biology models: NT-v2-50M (50M parameters), fine-tuned on 3,000 16S sequences in the
  paper (METHODS.md says about 15,000). Not relevant to evo.

### 3.4 For evo (question 4; inference)

- **Can it be computed?** Yes, offline. `census.csv` (`tick,now_hash,count`) joined
  to `genomes.csv` (`raw_hash,func_hash,len,...,bytes_hex`) gives the population of
  bodies at each census tick, weighted by count. `genomes.csv` includes somatic
  variants seen at a census, so every census hash has bytes. The canonical form
  (`isa::canonical`, with a Python copy in `analysis/traits.py`) would be the input,
  so that register-alias encodings do not count as variation. A 0.15M-parameter
  causal model trains in minutes on CPU.
- **Does it add anything over knockout complexity?** Little.
  1. Myers et al.'s BFF evidence does not test the claim, because the contrast is
     built in. A conserved site can hold at most log2 8 = 3 bits and a variable site
     up to log2 248 ≈ 7.95 bits, whatever selection does.
  2. For aligned, fixed-length genomes (E007: length 21 in every window of every
     seed), the per-column Shannon entropy of the census-weighted canonical bodies
     gives a conservation profile directly, with no model.
  3. Knockout complexity (`recent-3-oee-measures.md` §4: replace each site with
     `pad` and run `--classify`) measures *function* by test, which pseudo-perplexity
     only infers from conservation.
  4. A language model would help only for genomes of varying length, where column
     alignment fails, and evo is not there yet.
- **The combination that could be useful.** Put a per-site conservation profile
  (column entropy) next to a per-site knockout profile. A site that is conserved in
  the world but neutral in the solo harness marks selection that acts only in the
  crowded world. E007's absorb-count byte is the kind of trait this would catch.
  This costs one entropy pass over `census.csv` beyond the knockout loop already
  planned.
- **Functional information, directly.** Myers et al. quote Hazen's
  I(Ex) = −log F(Ex). Dušek's U regime measures F for BFF replication by sampling:
  F ≈ 7.15 × 10^-11, so I ≈ 33.7 bits. The same sampling design, with evo's harness
  as the test, gives evo's F without any language model (see §8.3).

---

## 4. Perrico & Banzhaf 2026, "Self-Modifying Linear Genetic Programming"

ALIFE 2026, pp. 1003–1011, https://doi.org/10.1162/isal.a.1044, CC BY 4.0. Michigan
State University. Full text read from the volume.

- **System (SMLGP)**, pp. 1004–1006:
  - An individual is an array of "memory banks": REGS (MEM0) holds the registers,
    with the program counter at REGS[0]; CODE (MEM1) holds the program; further banks
    are optional.
  - A line of code is 4 values: operation code, target register, operand specifier,
    addressing mode. The addressing modes are immediate, plus direct and indirect for
    each bank, so 1 + 2N modes for N banks.
  - Every index is reduced modulo its range, so out-of-range values never fault. The
    program counter (PC) advances by 4 per line and wraps around CODE, so programs
    loop until STOP or a timeout.
  - Operations: STOP, LOAD, STORE, ADD, SUB, MUL, DIV (protected), IFEQ.
- **Self-reproduction experiment** (p. 1006, Tables 3–4):
  - Goal: copy CODE into a provided bank MEM2. Fitness is the number of differing
    values (fitness-driven, so not a soup).
  - Settings: 50 replicates, 1,000 generations, population 256, length 16, value
    limit 16, at most 64 lines executed. Operations STOP, LOAD, STORE, ADD, SUB, IFEQ;
    tournament size 2, elitism 2, two-point crossover 0.7, point mutation 0.7.
  - The evolved copier is 4 lines, 3 of them active:
    `LOAD 1 3 CODE INDIRECT; STORE 1 3 MEM2 INDIRECT; (SUB, neutral); ADD 3 1 IMMEDIATE`.
    It runs through its 4 lines 16 times through PC wrap-around, "once for each value
    in CODE".
- The authors distinguish three mechanisms: real self-modification (registers
  reallocated, intermediate results stored inside CODE, the PC shifted off a line
  boundary so that the reading frame and the mutation bias change, pp. 1008–1009);
  retained memory between test cases; and PC looping.
- Caveat in their words: "As this is an initial exploration of SMLGP, parameters were
  not held constant across the experiments, and results are presented as
  demonstrations rather than statistically validated claims" (p. 1006).
- **For evo (inference).** A register machine with indirect addressing and implicit
  looping needs only three active instructions to copy itself *into a buffer it is
  given*. Allocation and division are what an evo replicator adds on top, and they
  are where any search for H3's floor should look for savings. The frame-shift
  result, where evolution reads constants as opcodes by moving the PC mid-line, is
  the same hazard `func_hash` already notes for jumps into `lit` operands
  (`docs/instrumentation.md`).

---

## 5. Horiguchi & Sayama 2026, "Space-Size-Driven Transition of Evolutionary Dynamics in Structural Cellular Hash Chemistry"

ALIFE 2026, pp. 385–392, https://doi.org/10.1162/isal.a.976, CC BY 4.0. Full text read
from the volume. Extended version: arXiv 2607.28219 (cited as [HS-arXiv]). Code:
https://github.com/NeoGendaijin/py-hash-chemistry (not cloned).

- **Model** (pp. 386–387): Structural Cellular Hash Chemistry (SCHC).
  - An L × L grid, k = 1,000 cell types. Individuals are 8-connected components.
  - Two active cells are sampled uniformly from the whole grid (global competition).
    Their components are scored by a 32-bit hash surrogate, and the winner's padded
    bounding box is copied onto the loser's location, with per-cell death
    p_death = 0.001 and mutation 0.002. Boundaries are open: copies are clipped at the
    edge.
  - Clock: each contest advances time by |C_w| / N_active, and a step completes when
    the accumulated time exceeds 1.
- **Design** (pp. 386–388):
  - Long runs at L ∈ {100, 200, 400}: 20,000 steps × 100 replicates.
  - Coarse scan L = 200–400 in steps of 20, and fine scan L = 300–320 in steps of 2:
    20,000 steps × 10 replicates each.
  - Mutation μ ∈ {0.001, 0.002, 0.005, 0.01} and death p_death ∈ {0.0005, 0.001,
    0.005, 0.01}, each at L ∈ {200, 300, 320, 400}: 10,000 steps × 5 replicates.
- **Results** (pp. 387–389, Table 2):
  - At L ≤ 300, mean component size stays at about 2–3 cells, yet the number of
    distinct patterns keeps rising.
  - At L ≥ 320, mean size is 1,700–3,200 cells and the size–score correlation is
    below −0.56.
  - Runaway fractions are bimodal and non-monotone: 30% at L = 302, 50% at 304 and
    320, 0% at 300 and 316. Mean final size is 2.6 at L = 300 and 1,855 at L = 320.
  - Between L = 300 and 320: Welch's t = −2.85, p = 0.019; Cohen's d = −1.27.
  - At μ ≥ 0.005, runaway occurs at every L, including 200. At p_death = 0.0005 it
    occurs at L ≤ 300; at p_death ≥ 0.005 it never occurs.
  - The authors describe a "nucleation-like" regime shift. Its mechanism (p. 390) is
    size-biased sampling (a component of size s is drawn with probability ≈ 2s/N_active)
    plus open-boundary clipping.
- **[HS-arXiv] §4.2 boundary control, not in the ALIFE paper.** "under periodic
  boundaries runaway occurs at every L tested (L = 200 to 360), including every small
  grid (L ≤ 300) at which open boundaries produce no runaway whatsoever". 29 of 30
  periodic runs ran away, at 5 replicates per L and up to 5,000 steps. "The linear
  scale L controls the transition only through the open boundary; it is not a
  parameter of the competition rule." [HS-arXiv] also adds a local-competition range D
  and a "dyadic" interaction probability P at L = 100 (30 runs per condition):
  locality "promoted replication, population growth, and size growth".
- **For evo (inference).** The size effect belongs to the open edge, and evo's ring has
  no edge, so this paper sets no calibration-soup size. Two lessons transfer:
  1. Transitions with a rare seed event give bimodal outcomes per run. Ten replicates
     produced fractions that jump between 0 and 0.5 across adjacent sizes. Any
     rule-by-rule sweep that reports a fraction needs Wilson intervals and more
     seeds, or a per-run time measure instead.
  2. Mutation and death rates move the threshold. In a BFF calibration, the mutation
     setting (Dušek 0, original 2^-12) is a first-order choice and has to be stated.

---

## 6. Sayama 2024, "Hash Chemistry on a Cellular Grid: An Open-Ended Artificial Chemistry System with Computational Efficiency and Nontrivial Spatio-Temporal Dynamics"

https://doi.org/10.1162/isal_a_00762, ALIFE 2024. **Read in full on 2026-10-12** from a
PDF supplied by hand (`docs/downloaded-papers/isal_a_00762.pdf`). It is a two-page
extended abstract with no abstract block, which is why Crossref, OpenAlex and Semantic
Scholar had none.

**Model.** An L × L grid (L = 100) whose cells are empty or hold one element of type
1..k (k = 1,000). The run starts almost empty, with 10 random elements. One update:

1. Pick four non-overlapping squares, two of side l1 and two of side l2, with l1 and
   l2 drawn from {1, ..., L/2}.
2. Cut out the four patterns and "shrink" them by removing blank rows and columns, so
   that small shifts and gaps do not change a pattern's identity.
3. Score each shrunk pattern by a hash: (h(array) mod M)/M with M = 100,000,000, using
   Mathematica 14.0's `Hash` at its defaults.
4. The best of the four copies itself over the other square of its own size. Each
   copied cell is emptied with probability 0.2% or set to a random type with
   probability 0.2%.

**Cost.** "A simulation for 2 × 10^5 updates with L = 100 would complete in less than
10 minutes in an ordinary laptop without any code optimization."

**Evidence for open-endedness.** One run shown as twelve snapshots (t = 0 to 200,000).
The claim is visual: the system "does not converge to dynamic equilibria" but "keeps
dynamically changing indefinitely", in composition, density and small repeated spatial
structures. No measure is computed. The paper says a systematic study "is currently
underway".

**What the same author said later.** The later papers call this model a failure on
exactly the point the abstract claims:

- arXiv 2412.12790 (Sayama, "Structural Cellular Hash Chemistry", IEEE ALIFE-CIS 2025):
  the cellular version "failed to show meaningful adaptive evolution or complexity
  growth".
- [HS-arXiv] §2.3: "an unsuccessful prototype", in which "the entities lacked explicit
  individual identity".

**For evo.** (inference) No soup size, emergence rate or energy rule to extract.
Fitness is an arbitrary hash in a tournament, with no metabolism and no cost of
running. The transferable point is about evidence: "keeps changing and never settles",
judged from snapshots of a single run, was withdrawn by its own author once the model
was studied further. PLAN frames the open problem as escaping equilibrium (§2), so evo is
exposed to the same mistake: a ring that "keeps changing" is not yet evidence. Judge it
only through the planned measures (QNN over `func_hash`, MODES as a secondary readout),
never from ring snapshots or a census that looks unsettled. Superseded by SCHC (§5).

---

## 7. One-line entries

- **Folena & Kruszewski 2024**, "On the Emergence of Enzymes in an Artificial
  Chemistry", https://doi.org/10.1162/isal_a_00791 (abstract via OpenAlex). The paper
  proposes "a model to characterize artificial enzymes within an artificial 'soup' of
  functions", and argues that enzymes "can emerge from elementary interactions among
  functions" and "foster rapid complexity growth" through autocatalytic networks.
  No emergence rate is given in the abstract. **UNVERIFIED** beyond it.
- **Stenzel, Zorn, Altmann, Mansky, Kölle, Gabor 2024**, "Self-Replicating Prompts for
  Large Language Models", https://doi.org/10.1162/isal_a_00813 (abstract via
  OpenAlex). LLMs talking to LLMs show "a natural tendency for the evolution of
  self-replicating text pieces". Not an instruction substrate. An open copy exists at
  https://epub.ub.uni-muenchen.de/127158/1/isal_a_00813.pdf (HTTP 200, PDF; not read).
- **Kocherovsky & Banzhaf 2024**, "Crossover Destructiveness in Cartesian versus Linear
  Genetic Programming", https://doi.org/10.1162/isal_a_00735 (abstract via OpenAlex).
  Linear genetic programming (LGP) "produces children that are far more similar to
  their parents than" Cartesian genetic programming does. The authors attribute this
  to "steady-state memory registers and program size regulation". Not about soups.
- **Hill Roy, Naqvi, Shao, Kelly 2026**, "In Search of Larger Populations: Rethinking
  GPU Execution for Genetic Programming in Artificial Life",
  https://doi.org/10.1162/isal.a.1020 (abstract; full text cut from the volume,
  pp. 789–799, not read beyond the abstract). It is a position paper arguing for
  "flatter array-based GP" and three GPU execution paradigms ("Warp-Level Execution,
  Opcode Multiplexing, and Wavefront Execution"). It bears on evo only if evo moves to
  GPU.
- **Usui, Suzuki & Arita 2023**, "Towards open-ended evolution based on CVT-MAP-Elites
  with dynamic switching between feature spaces", https://doi.org/10.1162/isal_a_00617.
  There is still no abstract in Crossref, OpenAlex or Semantic Scholar. The Suzuki lab
  list (https://sites.google.com/view/alcore-suzuki/home/publications) gives only the
  citation ("isal 2023, 98") and an AROB 2024 version ("Seeking open-ended evolution
  ...", pp. 106–110). A search-engine summary, not the paper, describes it as
  MAP-Elites that switches feature spaces (**UNVERIFIED**). Not about soups.
- **Lu, Beukman, Matthews, Foerster 2024**, "JaxLife: An Open-Ended Agentic Simulator",
  https://doi.org/10.1162/isal_a_00770 (abstract via OpenAlex; arXiv 2409.00853 listed
  by OpenAlex as an open location). Neural-network agents in a world "containing
  programmable systems", with reported "communication protocols, agriculture, and
  tool-use" and complexity scaling with compute. Not an instruction soup.

---

## 8. Answers to the questions

### 8.1 Question 1: does Dušek 2026 change Phase 4's protocol?

Yes. The soup itself (2^17 × 64 bytes, random pairing, 8,192 steps) stays as PLAN §8
has it. Concretely, the calibration harness should report the following:

1. **Discovery and takeover separately, with Dušek's replicator test.**
   - Use cubff's 13-trial stable-byte test with score ≥ 60, per seed. Record the
     first-discovery epoch, and takeover as replicators persisting for at least 500
     epochs.
   - Reproduction targets:
     - At mutation 0: discovery in 99–100 of 100 runs, median 2,453 epochs (R); 45 of
       100 takeovers.
     - The original paper's soup-level transition, by high-order entropy: 40% at
       2^-12 and 44% at 0 (`bff-and-recent.md` §1.5).
   - (inference) The 45% and 44% figures agree. The PLAN's "confirm their 40%" is a
     takeover statistic, while discovery is nearly certain within 16,000 epochs.
2. **First-discovery time as the primary outcome of the rule-by-rule sweep**
   (inference). Every seed gives a number, whereas takeover gives yes or no for 40–45%
   of seeds. Compare distributions (median, quantiles, censoring at 16,000 epochs)
   between rule settings.
3. **Time in executed tapes as well as in epochs.** N runs 2^17 tapes per epoch and R
   runs 2^16 (§2.8–2.9). Per execution, the two medians coincide, so the normalisation
   decides whether "coupling slows discovery" at all.
4. **U and N as controls.** In Dušek's fork these are command-line flags, so they cost
   nothing to add.
   - U is the null for the replication test and a direct measurement of replicator
     density.
   - N separates a rule that hurts *execution-driven* discovery from one that changes
     only *population coupling*. Evo's physics steps act on different factors
     (inference): energy limits how long the activating rewrite can run, while
     ownership and write protection limit which bytes it can rewrite.
5. **Operator frequencies per seed over time** (the fraction of instruction bytes, and
   each operator's share). This separated N's and R's attractors and is cheap to log.
6. **Discovery events over time** (transitions from 0 to at least 1 replicators),
   truncated at takeover, as Dušek's R_cond.
7. **Mutation setting stated.** Dušek ran at 0, PLAN's protocol at 2^-12, and the
   original reports both.

Implementation note: koutefra/bff-replicator-discovery is cubff with the three regimes
already in place, a CPU smoke profile and committed reference outputs. Step 1 of the
harness can start from it rather than from scratch; the cubff golden-output test that
round 1 proposed still applies. Cost (inference from p. 486): one 16,000-epoch run is
2–4 hours on an A100. N's median discovery falls at about 8% of a run, so a
discovery-only calibration that stops each seed at first discovery costs roughly a
tenth of that. Takeover statistics need full runs.

What carries over to a ring with locality is in §2.10. The precursor mechanism has a
direct analogue, but neighbours are always "R-like", write protection blocks activation
of living bodies, and every step of the activating rewrite is paid for.

### 8.2 Question 4: pseudo-perplexity from evo's records

Computable now, from `census.csv` + `genomes.csv`, using canonical bytes. The estimator
needs a 0.15M-parameter causal model, at most a few thousand genomes, and minutes of CPU.
It adds little over the planned knockout loop plus a per-column entropy profile, and the
paper's BFF evidence does not test the claim, because the contrast is built into the
mutation operator (§3.2, §3.4). The cheap and informative variant is to compare per-site
conservation with per-site knockout effect, to find sites selected only in the world.

### 8.3 Minimal replicator length (H3)

- Nothing in the cluster measures minimal length against emergence rate in an
  instruction substrate. The relevant numbers:
  - Dušek (BFF): a 9-instruction reverse-copy core (Fig. 1, `[>{.].{>[`), a
    5-instruction precursor completed by one byte from the target, and a density of
    7.1 × 10^-11 per uniform 64-byte program.
  - Perrico & Banzhaf (SMLGP): a 3-active-instruction copier, with no allocation
    and a buffer provided.
  - Note for the main session: round 1 recorded "about 5 bytes" for BFF's minimal
    replicator (`recent-2-soup-emergence.md` §6, from brlabsgroup and *Computational
    Life*). Dušek's robust-test replicators all have a 9-instruction core. The
    5-instruction object in Dušek is the precursor, which is not a replicator by
    itself.
- For evo's H3 search (inference), take Dušek's U design:
  - a fixed behavioural test (`--classify` replicator class);
  - a declared number of candidates;
  - a density estimate with a confidence interval.
- A finite search that finds nothing gives an upper bound on the density, not proof
  that no shorter replicator exists. Exhaustive enumeration is feasible only over
  canonical op sequences of a few instructions. The practical H3 search is therefore
  shortening from the 21-byte ancestor, by deletions and substitutions, plus
  enumeration of short canonical bodies. Perrico's result points at `alloc`/`divide`
  and the restart as the places where length can be saved.

### 8.4 Soup size for a calibration soup

- Horiguchi & Sayama's size threshold is a boundary artefact ([HS-arXiv] §4.2) in a
  non-instruction chemistry. It gives no size.
- From Dušek (inference): in N, first discovery is about geometric per epoch at 2^17
  programs, so the per-program hazard is roughly constant once the attractor is
  reached. Smaller soups should then take proportionally more epochs, for about the
  same total of 1.6 × 10^8 executions to the median.
- R's dynamics depend on the evolving composition, so a smaller R soup may not scale
  the same way. Round 1's 1,024-tape reproduction saw transitions at 2–4 × 10^7
  interactions (`recent-2-soup-emergence.md` §4.2), with different detection and
  settings.
- Recommendation: keep 2^17 for the reproduction step, then measure discovery per
  execution at one smaller size (2^14, say) before shrinking further.

---

## 9. What this changes for evo's next step

- Phase 4's harness should measure **first-discovery time (per execution and per
  epoch)** as the primary outcome, with takeover secondary, and run **U and N controls**
  alongside R. "Confirm 40%" becomes "match Dušek's 99/100 discovery, median 2,453
  epochs, and 45/100 takeover at mutation 0, plus the original 40% at 2^-12".
- **Start the harness from Dušek's cubff fork** (Apache 2.0, regimes as flags, data and
  validation scripts committed).
- **Drop pseudo-perplexity** as a planned measure. Add a per-column entropy profile
  over `census.csv` to set against the knockout loop.
- **H3 search design**: Dušek's U regime, a fixed test, a declared sample size, and a
  density bound.
- **Hand downloads**: every ALIFE 2026 paper is in the GitHub volume. That includes
  cluster 6 and 7 papers from 2026 still on the list (Willkens 2026 `isal.a.994`,
  Chaturvedi `isal.a.980`, Nehaniv `isal.a.990`, Bohm `isal.a.937`), as well as the
  ones already downloaded. The 2025 papers (Johnson 2025 `isal.a.885`, Sanson 2025)
  are not in it.

---

## 10. Searches that found nothing

- arXiv API (export.arxiv.org), 2026-10-12:
  - `ti:"Replicator Discovery" AND ti:"Population Coupling"`: 0.
  - `all:"self-modifying program soup"`: 0.
  - `au:Dusek AND abs:BFF`: 0.
  - `au:Papadopoulos AND au:Hudcova`: 0.
  - `abs:"primordial soup" AND abs:"replicator discovery"`: 0.
  - `ti:"Prediction and Entropy of Evolving Sequences"`: 0.
  - `all:"pseudo-perplexity" AND all:BFF`: 0.
  - `ti:"Self-Modifying Linear Genetic Programming"`: 0.
  - `au:Perrico AND au:Banzhaf`: only two GPU-GP papers (2603.12292, 2604.24968).
  - `au:Sayama AND abs:"cellular grid"`: only 2412.12790 (SCHC).
  - A final id lookup for 2409.00853 returned an empty response.
- Semantic Scholar Graph API: `openAccessPdf` for all five full-read papers points only
  to doi.org or direct.mit.edu. There is no abstract or summary for `isal_a_00617` or
  `isal_a_00762`.
- OpenAlex: no abstract for `isal_a_00762` or `isal_a_00617`. No location other than
  MIT Press for the 2026 papers, Sayama 2024 or Usui 2023.
- Web search:
  - The exact Dušek title: no relevant hit.
  - Perrico title: the MIT page and Banzhaf's publication list
    (http://www.cs.mun.ca/~banzhaf/gp.html, fetched; no 2026 entry).
  - Sayama 2024 title: the MIT page, ResearchGate (not fetched), arXiv SCHC and review.
    The Sayama lab site https://coco.binghamton.edu/ has no PDF link for it, and two
    guessed paths returned 404.
- GitHub repository search: `Dusek BFF`, `Hudcova BFF`, `hash chemistry jax`,
  `self-modifying linear genetic programming` and `SMLGP` gave 0 results. The search
  `replicator discovery BFF` found the Dušek repository.

## 11. Found in passing (not in the cluster)

- **Cotler, Hongler & Hudcová 2025**, "Self-replication and Computational Universality",
  arXiv 2510.08342 (abstract only, **UNVERIFIED** beyond it). It constructs "a cellular
  automaton that is Turing-universal but cannot sustain non-trivial self-replication".
  Relevant to PLAN §5.3's criterion that the ISA be evolvable: universality of an ISA
  does not imply replicators can exist in it.
- **modularflow/energetic-primordial-soup** (GitHub, README only): a Rust BFF soup with
  CUDA, WGPU and CPU backends, 2D neighbour pairing, and "energy zones" that restrict
  *mutation* to regions. That is not a per-instruction cost, so it is not prior art for
  Phase 4's energy step. Other BFF repositories surfaced by the search, not read:
  Wouterbeets/cubff-culture, mathelehrer/BrainFuckLife, samoylenkodmitry/soup.
- **ALIFE 2026 full volume on GitHub** (see "How this was checked"), plus late-breaking
  abstracts and summaries in the same repository.

## 12. UNVERIFIED items

- Folena & Kruszewski 2024, Stenzel et al. 2024, Kocherovsky & Banzhaf 2024, JaxLife
  2024, Cotler et al. 2025: abstracts only.
- Usui 2023: the description comes from a search summary only.
- Dušek's companion-site numbers (fragment probability 6.6 × 10^-7, "ten thousand
  times"): from the site source in the repository, not the paper.
- Myers et al.'s mutation rule restricted by alphabet: from the code and METHODS.md,
  not the paper.

## 13. Not reached

- Sayama 2024 (`isal_a_00762`) was supplied by hand on 2026-10-12 and is now read in
  full (§6).
- Usui 2023: no abstract anywhere reachable.
- Hill Roy 2026 body (available in `docs/downloaded-papers/`; one line only was asked).
- Horiguchi & Sayama code (NeoGendaijin/py-hash-chemistry), not cloned.
- No simulation was rerun: neither Dušek's cubff fork (CUDA) nor Myers et al.'s
  pipeline. The per-execution comparison in §2.9 is arithmetic on committed data, not a
  rerun.
- Dušek's live companion website (koutefra.github.io/bff-replicator-discovery); its
  source was read from the repository.
