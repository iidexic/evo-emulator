"""T11: is there a closed defence for the template body?
(docs/tasks/T11-closed-defence-screen.md; E016 record §1, §8.2, §8.7 item 4.)

Stages (§1, the insertion screen, is `e016_defence.py screen --nbhd-ins`):

- `own` (§2): the relabelled genomes that arose. Candidates are the
  structural complete genomes of E016's tierra_n0 and tierra_t50 runs
  (`runs/e016/<arm>/s<seed>/defence.csv`), ranked by their replicator-class
  exact births summed over every run of both arms: the top 20 of the
  ancestor's length (41 bytes), plus any other length that ranks in the top
  20 of the same ranking. One body each: the raw body with the most exact
  births summed over the per-run rows (defence.csv keeps each run's most
  common raw body of the func_hash). Writes runs/e016/own_nbhd/candidates.csv.
  For each candidate G, and for the ancestor as the reference row,
  `evo-core --neighbours G` under tierra_n0's physics (G is its own host,
  3,000 harness ticks as E015 stage 1) to runs/e016/own_nbhd/<func_hash>.csv
  (the ancestor: ancestor.csv), then E016's screen test with G's own label
  flip as the probe (the first byte of the label G's `searchf` finds in G,
  nop0 <-> nop1, the analogue of the registered probe), and writes
  runs/e016/own_nbhd/summary.md and own.csv.

    uv run --project analysis analysis/t11_closed.py own [--threads 12]

`--threads` defaults to 12 when other evo-core processes are running (the
E016 replay stage), else to the machine's parallelism. Resumable: a
neighbourhood file that exists is not rerun without `--force`.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import polars as pl

import e016_defence as e16
import lod
from e015_template import HEX, check_binary

OUT = e16.OUT
OWN = OUT / "own_nbhd"
ARMS = ("tierra_n0", "tierra_t50")
REF_ARM = "tierra_n0"  # §2: the physics of every neighbourhood and screen here
TOP = 20
ANC_LEN = 41
TEMPLATE, L1 = (13, 16), (18, 21)  # the ancestor's searchf template and L1 (inclusive)
NOP0, NOP1, LIT, SEARCHF = 1, 3, 17, 10
CLOSED_FRAC = 0.1  # §2: fewer than a tenth of the ancestor's parasite_jump rows


def is_nop(b: int) -> bool:
    return b & 0x1F in (NOP0, NOP1)


def nop_digits(g: bytes, lo: int, hi: int) -> str:
    """Bytes lo..hi (inclusive) as nop digits: 0 for nop0, 1 for nop1, x for
    any other op (blank past the body's end)."""
    return "".join("" if i >= len(g) else "0" if g[i] & 0x1F == NOP0 else "1" if g[i] & 0x1F == NOP1 else "x"
                   for i in range(lo, hi + 1))


def first_searchf(g: bytes) -> int | None:
    """Offset of the first `searchf` in a linear parse from byte 0 (a `lit`
    operand is skipped)."""
    i = 0
    while i < len(g):
        op = g[i] & 0x1F
        if op == SEARCHF:
            return i
        i += 2 if op == LIT else 1
    return None


def own_label(g: bytes) -> tuple[int, int, str] | None:
    """The label G's first `searchf` finds in G itself, by sim.rs's rule: the
    template is the run of nops after the `searchf`; the scan starts at the
    byte after the template and takes the first window whose ops are the
    template's complement, whatever follows it (the match is not
    exact-length). Returns (first, last, template digits) or None (no
    `searchf`, empty template, or no match inside G)."""
    s = first_searchf(g)
    if s is None:
        return None
    p = s + 1
    tmpl = []
    while p < len(g) and is_nop(g[p]):
        tmpl.append(g[p] & 0x1F == NOP1)
        p += 1
    if not tmpl:
        return None
    want = [NOP0 if bit else NOP1 for bit in tmpl]
    for c in range(p, len(g) - len(want) + 1):
        if all(g[c + j] & 0x1F == w for j, w in enumerate(want)):
            return c, c + len(want) - 1, "".join("1" if b else "0" for b in tmpl)
    return None


def addressing(g: bytes) -> str:
    """How G reaches its procedure: `label N` (its `searchf` finds an N-nop
    label in G), `searchf, no match`, `searchf, empty template` (the search
    fails and G runs on), or `no searchf` (straight-line, as the std body)."""
    s = first_searchf(g)
    if s is None:
        return "no searchf"
    lab = own_label(g)
    if lab:
        return f"label {lab[1] - lab[0] + 1}"
    return "searchf, empty template" if s + 1 >= len(g) or not is_nop(g[s + 1]) else "searchf, no match"


def own_flip(g: bytes) -> str:
    """G with the first byte of its own label flipped, nop0 <-> nop1 (low
    bits 1 <-> 3, modifier bits kept): for the ancestor, byte 18 0x03 ->
    0x01, the registered probe."""
    lab = own_label(g)
    if lab is None:
        raise ValueError(f"{g.hex()}: no own label")
    b = bytearray(g)
    b[lab[0]] ^= 0x02
    return b.hex()


def threads_default() -> int:
    """12 when other evo-core processes run (T11 §2), else all cores."""
    try:
        out = subprocess.run(["tasklist"], capture_output=True, text=True).stdout
        busy = "evo-core" in out
    except OSError:
        busy = False
    return 12 if busy else (os.cpu_count() or 8)


# ---- candidates ------------------------------------------------------------------

def load_complete(out: Path, seeds: int) -> pl.DataFrame:
    """Every structural complete row of the tierra n0 and t50 defence.csv
    files, with arm and seed."""
    parts = []
    for arm in ARMS:
        for s in range(1, seeds + 1):
            df = e16.read_defence(e16.run_dir(out, arm, s))
            if df is None:
                continue
            df = df.filter((pl.col("immune") | pl.col("tolerant")) & (pl.col("mechanism") == "structural"))
            parts.append(df.select("func_hash", "raw_hash", "len", "exact_births", "bytes_hex", "immune", "tolerant",
                                   "p_probed").with_columns(arm=pl.lit(arm), seed=pl.lit(s)))
    if not parts:
        raise SystemExit(f"no defence.csv under {out}/{{{','.join(ARMS)}}}: run `e016_defence.py screen` first")
    return pl.concat(parts)


def rank_candidates(rows: pl.DataFrame, top: int = TOP, anc_len: int = ANC_LEN) -> pl.DataFrame:
    """§2's list: func_hashes ranked by summed exact births (ties: func_hash);
    the first `top` of length `anc_len`, plus any other length in the first
    `top` overall. One body per func_hash: the raw body with the most summed
    exact births (ties: the smaller raw_hash)."""
    per = rows.group_by("func_hash").agg(
        births=pl.col("exact_births").sum(),
        **{f"runs_{a.split('_')[1]}": (pl.col("arm") == a).sum() for a in ARMS},
        **{f"births_{a.split('_')[1]}": pl.col("exact_births").filter(pl.col("arm") == a).sum() for a in ARMS},
        len=pl.col("len").first(),
        immune_runs=pl.col("immune").sum(), tolerant_runs=pl.col("tolerant").sum(),
        e016_p_probed_max=pl.col("p_probed").max(),
    )
    body = (rows.group_by("func_hash", "raw_hash").agg(k=pl.col("exact_births").sum(), hex=pl.col("bytes_hex").first())
            .sort(["func_hash", "k", "raw_hash"], descending=[False, True, False])
            .group_by("func_hash", maintain_order=True).agg(pl.col("raw_hash").first(), pl.col("hex").first()))
    ranked = (per.join(body, on="func_hash").sort(["births", "func_hash"], descending=[True, False])
              .with_row_index("overall_rank", offset=1))
    same = ranked.filter(pl.col("len") == anc_len).head(top)
    other = ranked.filter((pl.col("len") != anc_len) & (pl.col("overall_rank") <= top))
    out = pl.concat([same, other]).sort("overall_rank").with_row_index("rank", offset=1)
    lab = [own_label(bytes.fromhex(h)) for h in out["hex"].to_list()]
    gs = [bytes.fromhex(h) for h in out["hex"].to_list()]
    return out.with_columns(
        template_13_16=pl.Series([nop_digits(g, *TEMPLATE) for g in gs]),
        l1_18_21=pl.Series([nop_digits(g, *L1) for g in gs]),
        label_first=pl.Series([x[0] if x else None for x in lab], dtype=pl.Int64),
        label_last=pl.Series([x[1] if x else None for x in lab], dtype=pl.Int64),
        searchf_template=pl.Series([x[2] if x else None for x in lab], dtype=pl.Utf8),
    )


# ---- neighbourhoods and the own-flip screen ------------------------------------------

def run_nbhd(exe: Path, hx: str, dst: Path, threads: int, ticks: int, force: bool) -> str:
    """`evo-core --neighbours hx` under REF_ARM's physics, G its own host;
    writes dst and dst.stdout (the binary's summary); returns the summary."""
    so = dst.with_suffix(".stdout")
    if dst.exists() and so.exists() and not force:
        return so.read_text(encoding="utf-8")
    cmd = [str(exe), "--neighbours", hx, "--harness-ticks", str(ticks), "--threads", str(threads),
           "--neighbours-out", str(dst), *e16.physics(REF_ARM)]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    so.write_text(r.stdout, encoding="utf-8", newline="")
    print(f"  {dst.name}: {r.stderr.strip()}", flush=True)
    return r.stdout


def jump_stats(nb: Path, label: tuple[int, int] | None) -> dict:
    """parasite_jump rows of a neighbourhood file, their positions
    (`pos:count` runs), and how many sit on the label bytes."""
    df = pl.read_csv(nb, infer_schema=False).with_columns(pl.col("pos").cast(pl.Int64))
    pj = df.filter(pl.col("label") == "parasite_jump")
    by = pj.group_by("pos").agg(n=pl.len()).sort("pos")
    on = pj.filter(pl.col("pos").is_between(*label)).height if label else 0
    return dict(mutants=df.height, replicator=int((df["label"] == "replicator").sum()),
                parasite_jump=pj.height, on_label=on,
                parasite_fallthrough=int((df["label"] == "parasite_fallthrough").sum()),
                positions=" ".join(f"{p}:{n}" for p, n in by.iter_rows()))


def screen_own(exe: Path, hexes: list[str], ticks: int, jobs: int, ref: e16.Ref) -> dict[str, dict]:
    """E016's §1 test for each G with G's own label flip as the probe, under
    REF_ARM's physics, judged against REF_ARM's reference (the ancestor with
    the registered probe): b_alone, b_probed, p_probed, immune, tolerant."""
    from concurrent.futures import ThreadPoolExecutor
    flags = tuple(e16.physics(REF_ARM))
    alone = lod.harness_alone(exe, {f"g{i}": h for i, h in enumerate(hexes)}, ticks, flags=flags)
    # A body with no own label (no `searchf`, an empty template, or no match
    # inside itself) has no own flip: those fields are None.
    flips = [own_flip(bytes.fromhex(h)) if own_label(bytes.fromhex(h)) else None for h in hexes]
    todo = [(h, f) for h, f in zip(hexes, flips) if f is not None]
    with ThreadPoolExecutor(max(1, jobs)) as pool:
        got = list(pool.map(lambda hp: lod.harness_entered(exe, hp[0], ticks, flags=flags, probe=hp[1]), todo))
    probed = {h: p for (h, _), p in zip(todo, got)}
    out = {}
    for i, (h, f) in enumerate(zip(hexes, flips)):
        a = alone[f"g{i}"]
        p = probed.get(h)
        imm, tol = e16.is_defence(a["class"], a["exact_births"], p["host_exact"], p["pad_exact"], ref) if p else (None, None)
        out[h] = dict(flip_hex=f, class_alone=a["class"], b_alone=a["exact_births"],
                      b_probed_own=p["host_exact"] if p else None, p_probed_own=p["pad_exact"] if p else None,
                      own_entry_off=p["entry_off"] if p else None, own_immune=imm, own_tolerant=tol)
    return out


def screen_e016(exe: Path, hexes: list[str], ticks: int, jobs: int, ref: e16.Ref) -> dict[str, dict]:
    """E016's §1 test with the registered probe (REF_ARM)."""
    rows = e16.harness_rows(exe, hexes, REF_ARM, None, ticks, jobs)
    out = {}
    for h, r in rows.items():
        imm, tol = e16.is_defence(r["class_alone"], r["b_alone"], r["b_probed"], r["p_probed"], ref)
        out[h] = dict(b_probed_e016=r["b_probed"], p_probed_e016=r["p_probed"], e016_immune=imm, e016_tolerant=tol)
    return out


def yn(b: bool) -> str:
    return "yes" if b else "no"


def stage_own(exe: Path, out: Path, seeds: int, threads: int, ticks: int, jobs: int, force: bool) -> None:
    OWN.mkdir(parents=True, exist_ok=True)
    cand = rank_candidates(load_complete(out, seeds))
    cand.write_csv(OWN / "candidates.csv")
    print(f"own: {cand.height} candidates ({(cand['len'] != ANC_LEN).sum()} of another length); "
          f"{OWN / 'candidates.csv'}", flush=True)
    anc = HEX["tierra"]
    ref = e16.reference(exe, REF_ARM, None, ticks)
    print(f"own: reference {REF_ARM}: {ref}", flush=True)
    jobs_hex = [("ancestor", anc)] + list(zip(cand["func_hash"].to_list(), cand["hex"].to_list()))
    stats = {}
    for name, hx in jobs_hex:
        run_nbhd(exe, hx, OWN / f"{name}.csv", threads, ticks, force)
        lab = own_label(bytes.fromhex(hx))
        stats[name] = jump_stats(OWN / f"{name}.csv", (lab[0], lab[1]) if lab else None)
    hexes = [h for _, h in jobs_hex]
    sc = screen_own(exe, hexes, ticks, jobs, ref)
    e = screen_e016(exe, hexes, ticks, jobs, ref)
    anc_pj = stats["ancestor"]["parasite_jump"]
    rows = []
    for k, (name, hx) in enumerate(jobs_hex):
        g = bytes.fromhex(hx)
        lab = own_label(g)
        c = cand.filter(pl.col("func_hash") == name).row(0, named=True) if name != "ancestor" else None
        s = stats[name]
        few = s["parasite_jump"] < CLOSED_FRAC * anc_pj
        closed = name != "ancestor" and (few or bool(sc[hx]["own_immune"]))
        rows.append(dict(
            rank=c["rank"] if c else 0, func_hash=name, len=len(g), births=c["births"] if c else None,
            runs_n0=c["runs_n0"] if c else None, runs_t50=c["runs_t50"] if c else None,
            addressing=addressing(g), template=nop_digits(g, *TEMPLATE), l1=nop_digits(g, *L1),
            label_first=lab[0] if lab else None, label_last=lab[1] if lab else None,
            **s, on_label_frac=s["on_label"] / s["parasite_jump"] if s["parasite_jump"] else None,
            **sc[hx], **e[hx], few_jumps=few, closed=closed, hex=hx))
    df = pl.DataFrame(rows, infer_schema_length=None)
    df.write_csv(OWN / "own.csv")
    text = own_summary(df, ref, anc_pj, ticks)
    (OWN / "summary.md").write_text(text, encoding="utf-8", newline="")
    print(text)
    if df["closed"].any():
        print("CLOSED DEFENCE FOUND (T11 §2): " + ", ".join(df.filter(pl.col("closed"))["func_hash"].to_list())
              + "; stop for a decision", flush=True)


def own_summary(df: pl.DataFrame, ref: e16.Ref, anc_pj: int, ticks: int) -> str:
    lines = [
        "# T11 §2: own-neighbourhood parasites of the relabelled genomes", "",
        f"Candidates: the structural complete genomes of E016's tierra_n0 and tierra_t50 runs, ranked by "
        f"replicator-class exact births summed over both arms' runs; the top {TOP} of the ancestor's length "
        f"({ANC_LEN} bytes) plus any other length in the overall top {TOP} (`candidates.csv`). Each: "
        f"`evo-core --neighbours G` (G its own host; every substitution and deletion) under {REF_ARM}'s physics "
        f"(`{' '.join(e16.physics(REF_ARM))}`, fixed edge), {ticks:,} quiet harness ticks; the ancestor row is the "
        f"same run of the ancestor (E015 stage 1, default physics, had 1,095 `parasite_jump` rows, 996 of them on "
        f"L1). Label: the window G's own `searchf` finds in G (by sim.rs's rule); template and L1 are bytes 13-16 "
        f"and 18-21 as nop digits (x = not a nop). Own flip: G with its label's first byte flipped (nop0 <-> nop1), "
        f"placed before G; immune per E016 §1 against {REF_ARM}'s reference (the ancestor with the registered "
        f"probe: b_alone {ref.b_alone}, b_probed {ref.b_probed}, p_probed {ref.p_probed}; immune needs p_probed < "
        f"{CLOSED_FRAC * ref.p_probed:g}). E016 probe: the registered probe before G (G's E016 status).", "",
        "| rank | func_hash | len | births | addressing | template / L1 | label bytes | parasite_jump rows | "
        "on own label | parasite_fallthrough rows | own flip p_probed (entry) | immune to own flip | "
        "E016 probe p_probed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in df.iter_rows(named=True):
        lab = f"{r['label_first']}-{r['label_last']}" if r["label_first"] is not None else "none"
        on = f"{r['on_label']} ({100 * r['on_label_frac']:.0f}%)" if r["on_label_frac"] is not None else "0"
        births = f"{r['births']:,}" if r["births"] is not None else "ancestor"
        flip = f"{r['p_probed_own']} ({r['own_entry_off']})" if r["p_probed_own"] is not None else "n/a"
        imm = yn(r["own_immune"]) if r["own_immune"] is not None else "n/a"
        lines.append(f"| {r['rank'] or '-'} | `{r['func_hash']}` | {r['len']} | {births} | {r['addressing']} | "
                     f"{r['template']} / {r['l1']} | {lab} | {r['parasite_jump']:,} | {on} | "
                     f"{r['parasite_fallthrough']:,} | {flip} | {imm} | {r['p_probed_e016']} |")
    c = df.filter(pl.col("func_hash") != "ancestor")
    lab = c.filter(pl.col("label_first").is_not_null())
    pj = c["parasite_jump"]
    lines += ["",
              f"Candidates {c.height} ({lab.height} with an own label, {c.height - lab.height} without). "
              f"`parasite_jump` rows: all {pj.min()}-{pj.max()} (median {pj.median():g}); with an own label "
              f"{lab['parasite_jump'].min()}-{lab['parasite_jump'].max()} (median {lab['parasite_jump'].median():g}); "
              f"ancestor {anc_pj}. On own label {lab['on_label'].sum():,} of {lab['parasite_jump'].sum():,} rows of "
              f"the labelled candidates. Immune to own flip {int(lab['own_immune'].sum())} of {lab.height}; immune to "
              f"the E016 probe {int(c['e016_immune'].sum())} of {c.height}; below a tenth of the ancestor's "
              f"`parasite_jump` rows {int(c['few_jumps'].sum())}.",
              f"Own flip entered G (entry_off >= 0) in {int((lab['own_entry_off'] >= 0).sum())} of {lab.height} "
              f"labelled candidates (ranks {', '.join(str(x) for x in lab.filter(pl.col('own_entry_off') >= 0)['rank'])}); "
              f"in the others it never ran a byte of G. `parasite_fallthrough` rows: candidates "
              f"{c['parasite_fallthrough'].min()}-{c['parasite_fallthrough'].max()} (median "
              f"{c['parasite_fallthrough'].median():g}), ancestor "
              f"{df.filter(pl.col('func_hash') == 'ancestor')['parasite_fallthrough'][0]}.",
              f"Flagged by T11 §2's stop rule (fewer than a tenth of the ancestor's `parasite_jump` rows, or immune "
              f"to its own flip), {int(c['closed'].sum())}: "
              f"{', '.join(c.filter(pl.col('closed'))['func_hash'].to_list()) or 'none'}.",
              "", "Positions of the `parasite_jump` rows (pos:count) are in `own.csv`.", ""]
    return "\n".join(lines)


# ---- main --------------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["own"])
    ap.add_argument("--evo-bin", help="evo-core binary (default $EVO_BIN, else evo-core/target/release)")
    ap.add_argument("--out", type=Path, default=OUT, help="E016 output root (default runs/e016)")
    ap.add_argument("--seeds", type=int, default=e16.SEEDS)
    ap.add_argument("--harness-ticks", type=int, default=e16.HARNESS_TICKS)
    ap.add_argument("--threads", type=int, help="--threads for evo-core --neighbours (default: 12 if other "
                                                "evo-core processes run, else all cores)")
    ap.add_argument("--jobs", type=int, default=8, help="parallel harness calls for the screens")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    exe = e16.evo_bin(a.evo_bin)
    check_binary(exe)
    threads = a.threads or threads_default()
    if a.stage == "own":
        stage_own(exe, a.out, a.seeds, threads, a.harness_ticks, a.jobs, a.force)


if __name__ == "__main__":
    sys.exit(main())
