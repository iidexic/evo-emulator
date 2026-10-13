"""T06 on E007: the line of descent at tick 250,000 in seeds 1-10, with
harness and world fitness per step (lod.py; spec docs/tasks/T06-lenski-lod.md).

    uv run lod_e007.py [--seeds 10] [--at 250000] [--evo-bin PATH] [--jobs 9] [--no-rerun]

Reads runs/e007/std/s<seed>/. A seed whose directory there is incomplete
(no genomes.csv, or `ticks_run` null in meta.json: E007's first launch, on
Windows, was killed at tick ~145,000 and the full runs were made on Linux)
is taken from runs/lod/e007/s<seed>/ instead, rerun there with E007's
command line (`--ticks 250000 --seed S --report 500 --census 500 --out
DIR`, as e004_physics.run_one; no classification, lod.py classifies what it
needs) unless that directory is already complete. A rerun's births.csv is
compared byte for byte with the killed run's over the killed run's
complete lines, which shows the rerun is the same run as far as the killed
one went. Seeds rerun in parallel (`--jobs`); lines are drawn one seed at a
time.

Writes each seed's lod.py output to <run dir>/lod/, the headline table to
runs/lod/seeds.csv, and runs/lod/summary.md (headline table, then each
seed's lod.py summary).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

import lod
from evo_run import ROOT

E007 = ROOT / "runs" / "e007" / "std"
OUT = ROOT / "runs" / "lod"
RERUN = OUT / "e007"
TICKS = 250_000
CENSUS = 500


def complete(d: Path) -> bool:
    if not (d / "genomes.csv").exists() or not (d / "meta.json").exists():
        return False
    return json.loads((d / "meta.json").read_text())["ticks_run"] is not None


def rerun(exe: Path, seed: int) -> float:
    """E007's command line for one seed into RERUN/s<seed>; returns seconds."""
    d = RERUN / f"s{seed}"
    d.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(exe), "--ticks", str(TICKS), "--seed", str(seed), "--report", str(CENSUS),
           "--census", str(CENSUS), "--out", str(d)]
    t0 = time.time()
    with open(d.parent / f"s{seed}.stdout", "w", encoding="utf-8", newline="\n") as out:
        subprocess.run(cmd, stdout=out, stderr=subprocess.DEVNULL, check=True)
    return time.time() - t0


def prefix_check(old: Path, new: Path) -> dict:
    """Compare `new` with `old` over old's bytes up to its last newline."""
    data = old.read_bytes()
    n = data.rfind(b"\n") + 1
    with open(new, "rb") as f:
        same = f.read(n) == data[:n]
    last = data[:n].rstrip(b"\n").rsplit(b"\n", 1)[-1].split(b",", 1)[0]
    return {"bytes": n, "match": same, "to_tick": int(last) if last.isdigit() else None}


def resolve(seed: int, exe: Path, allow_rerun: bool) -> tuple[Path | None, str]:
    """Run directory for a seed and a note on where it came from. Does not
    rerun (main does that in parallel); returns None if a rerun is needed."""
    d = E007 / f"s{seed}"
    if complete(d):
        return d, "E007 run"
    r = RERUN / f"s{seed}"
    if complete(r):
        return r, "rerun (found complete)"
    return None, "rerun needed" if allow_rerun else "incomplete, rerun disabled"


def _f(v, nd=2) -> str:
    return lod._f(v, nd)


def headline(seed: int, d: Path | None, source: str, res: lod.Result | None, err: str | None,
             secs: float | None, sim_secs: float | None, check: dict | None) -> dict:
    row = {"seed": seed, "run_dir": d.relative_to(ROOT).as_posix() if d else None, "source": source,
           "rerun_seconds": round(sim_secs, 1) if sim_secs is not None else None,
           "prefix_match": check["match"] if check else None, "prefix_to_tick": check["to_tick"] if check else None,
           "lod_seconds": round(secs, 1) if secs is not None else None, "status": err or "ok"}
    if res is None:
        return row
    c = lod.counts(res.steps)
    g = res.genomes
    a = res.absorb
    S = res.steps.rows(named=True)
    row.update({
        "end_id": res.pick.end_id, "end_generation": int(res.line["generation"][-1]),
        "end_birth_tick": int(res.line["birth_tick"][-1]), "end_offspring": res.pick.offspring,
        "group_size": res.pick.group_size, "line_organisms": res.line.height, "distinct_genomes": g.height,
        "steps": c["total"], "synonymous": c["synonymous"], "beneficial": c["beneficial"], "neutral": c["neutral"],
        "deleterious": c["deleterious"], "deleterious_to_zero": c["to_zero"],
        "beneficial_from_zero": c["from_zero"], "order": c["order"],
        "f_founder": int(g["alone_exact"][0]), "f_end": int(g["alone_exact"][-1]),
        "entered_founder": int(g["entered_host_exact"][0]), "entered_end": int(g["entered_host_exact"][-1]),
        "entered_founder_stopped": bool(g["entered_stopped_early"][0]),
        "entered_end_stopped": bool(g["entered_stopped_early"][-1]),
        "absorb_start": a["start"], "absorb_final": a["final"],
        "absorb_changes": len(a["changes"]), "absorb_raises": a["raises"],
        "absorb_raises_after_deleterious": a["raises_after_deleterious"],
    })
    for key, pre in (("final_step", "abs"), ("sweep_step", "sweep")):
        x = a[key]
        s = S[x["index"]] if x["index"] is not None else None
        row.update({
            f"{pre}_step": s["step"] if s else None,
            f"{pre}_tick": s["tick"] if s else None,
            f"{pre}_from": s["absorb_parent"] if s else None,
            f"{pre}_to": s["absorb_child"] if s else None,
            f"{pre}_effect": s["effect"] if s else None,
            f"{pre}_f": f"{s['f_parent']}->{s['f_child']}" if s else None,
            f"{pre}_prev_effect": x["prev_effect"],
            f"{pre}_deleterious_in_3_before": any(b["effect"] == "deleterious" for b in x["before"]) if s else None,
        })
    return row


def summary(rows: list[dict], texts: dict[int, str], exe: Path, at: int) -> str:
    ok = [r for r in rows if r["status"] == "ok"]
    yes = lambda v: "–" if v is None else ("yes" if v else "no")
    lines = [
        f"# T06: line of descent on E007 at tick {at:,}",
        "",
        "Spec: docs/tasks/T06-lenski-lod.md. Script: analysis/lod_e007.py (lines by analysis/lod.py). "
        f"Harness binary: `{exe}`.",
        "",
        "Data. Seeds read from the E007 run directory when it is complete; otherwise rerun with E007's command "
        "line into runs/lod/e007/ (E007's first launch on this machine was killed at tick ~145,000; the full "
        "runs were made on Linux). Each rerun's births.csv is compared byte for byte with the killed run's over "
        "the killed run's complete lines.",
        "",
        "| seed | data | rerun (s, seeds in parallel) | births match killed run to tick | lod (s) |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        m = "–" if r["prefix_match"] is None else (
            f"{'yes' if r['prefix_match'] else 'NO'}, {_f(r['prefix_to_tick'])}")
        lines.append(f"| {r['seed']} | {r['run_dir'] or '–'} ({r['source']}) | {_f(r['rerun_seconds'], 1)} "
                     f"| {m} | {_f(r['lod_seconds'], 1)} |")
    lines += [
        "",
        "Headline. f = exact children alone in 3,000 quiet harness ticks; entered = the host's exact children "
        "with a `pad` before it. Effects: beneficial if f rises by more than 1, deleterious if it falls by more "
        "than 1. Absorb-count step (the spec's) = first step into the end genome's absorb count; sweep step = "
        "first step to an absorb count of 96 or more (traits.ABSORB threshold).",
        "",
        "| seed | end organism (gen) | line organisms | steps (syn.) | beneficial (from f = 0) | neutral "
        "| deleterious (to f = 0) "
        "| f founder → end | entered founder → end | absorb start → final "
        "| absorb-count step: step, tick, count, effect (f) | step before | D in 3 before "
        "| sweep step: step, tick, count, effect (f) | step before | D in 3 before "
        "| absorb raises (after a D step) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if r["status"] != "ok":
            lines.append(f"| {r['seed']} | {r['status']} |" + " |" * 15)
            continue
        cells = []
        for pre in ("abs", "sweep"):
            if r[f"{pre}_step"] is None:
                cells += ["none", "–", "–"]
            else:
                cells += [
                    f"{r[f'{pre}_step']}, {r[f'{pre}_tick']:,}, {_f(r[f'{pre}_from'])} → {_f(r[f'{pre}_to'])}, "
                    f"{r[f'{pre}_effect']} ({r[f'{pre}_f'].replace('->', ' → ')})",
                    r[f"{pre}_prev_effect"] or "none",
                    yes(r[f"{pre}_deleterious_in_3_before"]),
                ]
        lines.append(
            f"| {r['seed']} | {r['end_id']} ({r['end_generation']}) | {r['line_organisms']} "
            f"| {r['steps']} ({r['synonymous']}) | {r['beneficial']} ({r['beneficial_from_zero']}) | {r['neutral']} "
            f"| {r['deleterious']} ({r['deleterious_to_zero']}) | {r['f_founder']} → {r['f_end']} "
            f"| {lod._entered(r['entered_founder'], r['entered_founder_stopped'])} → "
            f"{lod._entered(r['entered_end'], r['entered_end_stopped'])} "
            f"| {_f(r['absorb_start'])} → {_f(r['absorb_final'])} | " + " | ".join(cells)
            + f" | {r['absorb_raises']} ({r['absorb_raises_after_deleterious']}) |"
        )
    if ok:
        tot = {k: sum(r[k] for r in ok) for k in ("steps", "synonymous", "beneficial", "neutral", "deleterious",
                                                  "deleterious_to_zero", "beneficial_from_zero",
                                                  "absorb_raises", "absorb_raises_after_deleterious")}
        n_abs_d = sum(1 for r in ok if r["abs_prev_effect"] == "deleterious")
        n_sw_d = sum(1 for r in ok if r["sweep_prev_effect"] == "deleterious")
        n_abs_3 = sum(1 for r in ok if r["abs_deleterious_in_3_before"])
        n_sw_3 = sum(1 for r in ok if r["sweep_deleterious_in_3_before"])
        n_sw_eff = {e: sum(1 for r in ok if r["sweep_effect"] == e) for e in ("beneficial", "neutral", "deleterious")}
        lines += [
            "",
            f"Over the {len(ok)} seeds with a line: {tot['steps']} steps ({tot['synonymous']} synonymous), "
            f"{tot['beneficial']} beneficial, {tot['neutral']} neutral, {tot['deleterious']} deleterious; "
            f"{tot['deleterious_to_zero']} of the deleterious steps go to a genome with no exact children alone "
            f"and {tot['beneficial_from_zero']} of the beneficial steps come from one (break, then repair). "
            f"The absorb-count step is immediately preceded by a deleterious step in {n_abs_d} of {len(ok)} "
            f"seeds (a deleterious step among the three before it in {n_abs_3}); the sweep step in {n_sw_d} of "
            f"{len(ok)} ({n_sw_3}). The sweep step itself is beneficial in {n_sw_eff['beneficial']}, neutral in "
            f"{n_sw_eff['neutral']} and deleterious in {n_sw_eff['deleterious']} seeds. Of {tot['absorb_raises']} "
            f"steps that raised the absorb count, {tot['absorb_raises_after_deleterious']} immediately follow a "
            "deleterious step.",
        ]
    lines += [
        "",
        lod.STOPPED_NOTE,
        "",
        "Caveats (spec §4). Harness fitness is measured with a full pool and no neighbours. E007's break-even "
        "argument says the longer absorb phase pays on a lower ration, which the harness cannot see, so a "
        "harness-deleterious absorb raise may be the beneficial step in the world; the world columns (exact "
        "children per death, median age, over every organism born with the genome in the step's 25,000-tick "
        "window) are the check. The line is one path. E007 seed 3's negative-count loop (`lit A -114 ; inc A`) "
        "is read by pattern, not by byte.",
    ]
    for seed in sorted(texts):
        lines += ["", texts[seed].replace("\n# ", "\n## ").replace("# Line of descent", f"## Seed {seed}: line of descent", 1)]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--at", type=int, default=TICKS)
    ap.add_argument("--evo-bin", help="evo-core binary (default $EVO_BIN, else build with cargo)")
    ap.add_argument("--jobs", type=int, default=9, help="parallel reruns")
    ap.add_argument("--no-rerun", action="store_true")
    a = ap.parse_args()
    exe = lod.evo_bin(a.evo_bin)
    seeds = list(range(1, a.seeds + 1))
    OUT.mkdir(parents=True, exist_ok=True)

    where = {s: resolve(s, exe, not a.no_rerun) for s in seeds}
    todo = [s for s in seeds if where[s][0] is None and not a.no_rerun]
    log_path = RERUN / "rerun.json"  # seconds per rerun, kept for later invocations
    reruns = json.loads(log_path.read_text()) if log_path.exists() else {}
    if todo:
        print(f"lod_e007: rerunning seeds {todo} ({TICKS:,} ticks each, {a.jobs} at a time)", flush=True)
        with ThreadPoolExecutor(a.jobs) as pool:
            for s, t in zip(todo, pool.map(lambda s: rerun(exe, s), todo)):
                reruns[str(s)] = {"seconds": round(t, 1), "binary": str(exe), "parallel": min(a.jobs, len(todo))}
                where[s] = (RERUN / f"s{s}", "rerun")
                print(f"  s{s}: {t:.0f} s", flush=True)
        log_path.write_text(json.dumps(reruns, indent=1) + "\n", encoding="utf-8", newline="\n")
    sim_secs = {int(s): v["seconds"] for s, v in reruns.items()}

    rows, texts = [], {}
    for s in seeds:
        d, source = where[s]
        check = None
        if d is not None and d.parent != RERUN:
            sim_secs.pop(s, None)
        if d is not None and d.parent == RERUN and (E007 / f"s{s}" / "births.csv").exists():
            check = prefix_check(E007 / f"s{s}" / "births.csv", d / "births.csv")
        res, err, secs = None, None, None
        if d is None:
            err = source
        else:
            t0 = time.time()
            try:
                res = lod.lod(d, at=a.at, exe=exe)
                texts[s] = (res.out / "summary.md").read_text(encoding="utf-8").rstrip("\n")
            except lod.NoLine as e:
                err = f"no line: {e}"
                print(f"lod_e007: s{s}: {err}", flush=True)
            secs = time.time() - t0
        rows.append(headline(s, d, source, res, err, secs, sim_secs.get(s), check))

    pl.DataFrame(rows, infer_schema_length=None).write_csv(OUT / "seeds.csv")
    text = summary(rows, texts, exe, a.at)
    (OUT / "summary.md").write_text(text + "\n", encoding="utf-8", newline="\n")
    print(text.split("\n\nCaveats")[0])
    print(f"wrote {OUT / 'summary.md'}")


if __name__ == "__main__":
    main()
