"""E005: parasite search in the E004 p512_far runs. No new world runs; reads
runs/e004/p512_far*/s*/ (docs/instrumentation.md), completes the
world-physics classes (classes_world.csv), and tests the predictions in
docs/research/experiments/2026-10-06-e005-parasite-search.md.

Usage (from analysis/):

    uv run e005_parasites.py                 # classify (if needed), analyse, summarise
    uv run e005_parasites.py --arms p512_far --seeds 3
    uv run e005_parasites.py --no-host       # skip the two-genome harness runs

Definitions (E005 record, repeated here so the code can be checked against
them):

  exact birth        raw_hash == parent_now_hash: the child equals the
                     executor's body at `divide`
  world-replicating  a raw hash with >= 2 exact births in the run
  dependent          world-replicating, default harness class != replicator
  world class        harness class under the run's own physics flags
  generation depth   longest chain of exact G births in which each executor
                     was itself born by an exact G birth
  foreign share      exec_foreign / executed over a carrier's life, carriers
                     being organisms born with genome G (deaths.csv plus the
                     last census of orgs.csv for the living)
  parasite lineage   dependent, world class != replicator, median carrier
                     foreign share > 0.25, generation depth >= 5

Per-run output goes to runs/e005/<arm>_s<seed>_dependent.csv (the dependent
genome table) and runs/e005/<arm>_s<seed>_other_source.csv; per-run metrics
to runs/e005/runs.csv; the arm table and prediction checks to
runs/e005/summary.md.
"""

from __future__ import annotations

import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

from evo_run import HASH_COLS, ROOT, binary, load

E004 = ROOT / "runs" / "e004"
OUT = ROOT / "runs" / "e005"
HARNESS_TICKS = 3000
AFTER_TICK = 10_000  # prediction 1 counts exact births after this tick
ANCESTOR_LEN = 21

# Physics flags per arm, for the world-physics classify and the host
# harness. Noise flags are ignored by the harness, so --rot is left out.
WORLD = ["--patch", "512", "--sun", "8", "--alloc-far"]
ARMS = {
    "p512_far": WORLD,
    "p512_far_prop": WORLD + ["--absorb-prop"],
    "p512_far_rot": WORLD,
    "p512_far_prop_rot": WORLD + ["--absorb-prop"],
}


def _rows(path: Path) -> int:
    """Data rows in a CSV (header excluded), 0 if missing."""
    if not path.exists():
        return 0
    with open(path, "rb") as f:
        return sum(1 for _ in f) - 1


def ensure_world_classes(exe: Path, arm: str, seed: int) -> str:
    """Write classes_world.csv unless it exists with one row per genome.
    Six of the 2026-10-06 files were cut short, so a file that exists is not
    enough; the row count must match genomes.csv."""
    d = E004 / arm / f"s{seed}"
    want = _rows(d / "genomes.csv")
    have = _rows(d / "classes_world.csv")
    if have == want:
        return f"{arm}/s{seed}: classes_world.csv complete ({want} genomes)"
    cmd = [str(exe), "--classify", str(d), "--classes-out", "classes_world.csv",
           "--harness-ticks", str(HARNESS_TICKS), *ARMS[arm]]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return f"{arm}/s{seed}: classified {want} genomes under world physics (had {have})"


def host_harness(exe: Path, arm: str, hex_bytes: str, pad: bool) -> dict:
    """Two-genome harness: the genome placed right before the ancestor."""
    cmd = [str(exe), "--host", hex_bytes, "--harness-ticks", str(HARNESS_TICKS), *ARMS[arm]]
    if pad:
        cmd.append("--host-pad")
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    header, row = out.strip().splitlines()[:2]
    vals = dict(zip(header.split(","), row.split(",")))
    return {k: (v == "true" if v in ("true", "false") else int(v)) for k, v in vals.items()}


def _read_classes(path: Path) -> pl.DataFrame:
    return pl.read_csv(path, schema_overrides={c: pl.Utf8 for c in HASH_COLS["classes"]})


def generation_depth(exact: pl.DataFrame, genomes: set[str]) -> dict[str, int]:
    """Longest chain of exact G births where each executor was itself born by
    an exact G birth. `exact` holds exact births only; ids rise with tick, so
    sorting by (tick, child) visits every executor before its children."""
    depth_of: dict[tuple[str, int], int] = {}
    best: dict[str, int] = {g: 0 for g in genomes}
    rows = exact.filter(pl.col("raw_hash").is_in(list(genomes))).sort("tick", "child")
    for g, child, executor in rows.select("raw_hash", "child", "executor").iter_rows():
        d = depth_of.get((g, executor), 0) + 1
        depth_of[(g, child)] = d
        if d > best[g]:
            best[g] = d
    return best


def analyse(arm: str, seed: int, exe: Path | None) -> dict:
    d = E004 / arm / f"s{seed}"
    run = load(d)
    world = _read_classes(d / "classes_world.csv").select(
        pl.col("raw_hash"), pl.col("class").alias("world_class")
    )
    final = run.patches["tick"].max()

    # --- births by copy source -------------------------------------------
    b = run.births.with_columns(
        exact=pl.col("raw_hash") == pl.col("parent_now_hash"),
        src=pl.when(pl.col("source") == pl.col("executor"))
        .then(pl.lit("self"))
        .when(pl.col("source") >= 2)
        .then(pl.lit("other"))
        .otherwise(pl.lit("unowned")),
    )
    n_births = b.height
    src_counts = {k: int(v) for k, v in b.group_by("src").len().iter_rows()}

    # --- genomes: exact births, classes -----------------------------------
    exact = b.filter(pl.col("exact"))
    per_g = (
        exact.group_by("raw_hash")
        .agg(
            exact_births=pl.len(),
            exact_after=(pl.col("tick") > AFTER_TICK).sum(),
            first_tick=pl.col("tick").min(),
            last_tick=pl.col("tick").max(),
            len=pl.col("len").first(),
        )
        .filter(pl.col("exact_births") >= 2)
    )
    per_g = run.class_of(per_g, "raw_hash").join(world, on="raw_hash", how="left")
    per_g = per_g.with_columns(pl.col("world_class").fill_null("unknown"))
    dep = per_g.filter(pl.col("class") != "replicator")

    # --- carriers: foreign and unowned execution share ---------------------
    cols = ["birth_hash", "executed", "exec_foreign", "exec_unowned", "offspring"]
    living = run.orgs.filter(pl.col("tick") == final).select(cols)
    carriers = pl.concat([run.deaths.select(cols), living]).with_columns(
        foreign=pl.col("exec_foreign") / pl.col("executed").clip(lower_bound=1),
        unowned=pl.col("exec_unowned") / pl.col("executed").clip(lower_bound=1),
    )
    ran = carriers.filter(pl.col("executed") > 0)
    shares = ran.group_by("birth_hash").agg(
        carriers=pl.len(),
        foreign_med=pl.col("foreign").median(),
        unowned_med=pl.col("unowned").median(),
        foreign_med_dividers=pl.col("foreign").filter(pl.col("offspring") > 0).median(),
        # Carriers with at least two children: a carrier that dies right
        # after its first `divide` has not yet reached whatever follows it.
        foreign_med_2=pl.col("foreign").filter(pl.col("offspring") >= 2).median(),
        unowned_med_2=pl.col("unowned").filter(pl.col("offspring") >= 2).median(),
        carriers_2=(pl.col("offspring") >= 2).sum(),
    )
    per_g = per_g.join(shares.rename({"birth_hash": "raw_hash"}), on="raw_hash", how="left")
    # Exact births of each genome by copy source. Resurrection from debris
    # (an exact child whose bytes came from unowned memory) shows up here,
    # not in the execution counters.
    by_src = (
        exact.group_by("raw_hash", "src").len().pivot(on="src", index="raw_hash", values="len").fill_null(0)
    )
    for c in ("self", "other", "unowned"):
        if c not in by_src.columns:
            by_src = by_src.with_columns(pl.lit(0, dtype=pl.UInt32).alias(c))
    per_g = per_g.join(
        by_src.rename({"self": "exact_self", "other": "exact_other", "unowned": "exact_unowned"}),
        on="raw_hash",
        how="left",
    )
    dep = per_g.filter(pl.col("class") != "replicator")

    # --- generation depth and the parasite test ----------------------------
    # `parasite` is the registered test (median foreign share over every
    # carrier). Most carriers of any genome die as newborns without leaving
    # their body, so that median is near 0 even for a genome whose
    # reproducing carriers run host code; `parasite_div` (post hoc, seed 1
    # smoke run, 2026-10-07) takes the median over carriers that divided.
    depth = generation_depth(exact, set(dep["raw_hash"]))
    dep = dep.with_columns(
        depth=pl.col("raw_hash").map_elements(lambda h: depth.get(h, 0), return_dtype=pl.Int64)
    ).with_columns(
        parasite=(pl.col("world_class") != "replicator")
        & (pl.col("foreign_med") > 0.25)
        & (pl.col("depth") >= 5),
        parasite_div=(pl.col("world_class") != "replicator")
        & (pl.col("foreign_med_dividers") > 0.25)
        & (pl.col("depth") >= 5),
        parasite_2=(pl.col("world_class") != "replicator")
        & (pl.col("foreign_med_2") > 0.25)
        & (pl.col("depth") >= 5),
    ).sort("exact_births", descending=True)
    gen = run.genomes.select("raw_hash", "bytes_hex", "disasm")
    dep = dep.join(gen, on="raw_hash", how="left")
    dep.write_csv(OUT / f"{arm}_s{seed}_dependent.csv")

    # --- prediction 1-3 numbers --------------------------------------------
    exact_after = int((exact["tick"] > AFTER_TICK).sum())
    dep_after = int(dep["exact_after"].sum())
    dep_after_world = int(dep.filter(pl.col("world_class") != "replicator")["exact_after"].sum())
    rep_g = per_g.filter(pl.col("class") == "replicator")

    parasites_reg = dep.filter(pl.col("parasite"))
    parasites = dep.filter(pl.col("parasite_2"))
    main_par = parasites.row(0, named=True) if parasites.height else None
    # Dependent genomes whose reproducing carriers run no foreign code at all.
    dep_nonpar = dep.filter(pl.col("foreign_med_2") < 0.05)
    main_rep = rep_g.sort("exact_births", descending=True).row(0, named=True) if rep_g.height else None

    # --- prediction 6: births copied from another living organism ----------
    other = b.filter(pl.col("src") == "other")
    other_exact = other.filter(pl.col("raw_hash") == pl.col("source_hash"))
    per_src = (
        other.group_by("source_hash")
        .agg(births=pl.len(), exact_of_source=(pl.col("raw_hash") == pl.col("source_hash")).sum())
        .sort("exact_of_source", descending=True)
    )
    per_src.head(50).write_csv(OUT / f"{arm}_s{seed}_other_source.csv")

    # --- prediction 7: two-genome harness on the main parasite --------------
    host = host_pad = None
    if main_par is not None and exe is not None:
        host = host_harness(exe, arm, main_par["bytes_hex"], pad=False)
        host_pad = host_harness(exe, arm, main_par["bytes_hex"], pad=True)

    share = lambda n, d: n / d if d else None
    return dict(
        arm=arm,
        seed=seed,
        births=n_births,
        src_self=src_counts.get("self", 0),
        src_other=src_counts.get("other", 0),
        src_unowned=src_counts.get("unowned", 0),
        exact_births=exact.height,
        exact_after=exact_after,
        world_replicating=per_g.height,
        dependent=dep.height,
        dependent_world_rep=int((dep["world_class"] == "replicator").sum()),
        dep_exact_after_share=share(dep_after, exact_after),
        dep_still_dep_share=share(dep_after_world, dep_after),
        dep_exact_unowned=int(dep["exact_unowned"].sum()),
        dep_foreign_med=dep["foreign_med"].median() if dep.height else None,
        dep_foreign_med_div=dep["foreign_med_dividers"].median() if dep.height else None,
        dep_unowned_med=dep["unowned_med"].median() if dep.height else None,
        rep_foreign_med=rep_g["foreign_med"].median() if rep_g.height else None,
        rep_foreign_med_div=rep_g["foreign_med_dividers"].median() if rep_g.height else None,
        parasites_reg=parasites_reg.height,
        parasites_div=int(dep["parasite_div"].sum()),
        parasites=parasites.height,
        dep_nonpar_exact_after_share=share(int(dep_nonpar["exact_after"].sum()), exact_after),
        dep_nonpar_unowned_med=dep_nonpar["unowned_med_2"].median() if dep_nonpar.height else None,
        parasite_exact_after_share=share(int(parasites["exact_after"].sum()), exact_after),
        main_parasite_len=main_par["len"] if main_par else None,
        main_parasite_exact=main_par["exact_births"] if main_par else None,
        main_parasite_depth=main_par["depth"] if main_par else None,
        main_parasite_foreign=main_par["foreign_med_2"] if main_par else None,
        main_parasite_unowned=main_par["unowned_med_2"] if main_par else None,
        main_parasite_hash=main_par["raw_hash"] if main_par else None,
        main_parasite_disasm=main_par["disasm"] if main_par else None,
        main_rep_len=main_rep["len"] if main_rep else None,
        main_rep_exact=main_rep["exact_births"] if main_rep else None,
        parasites_le4=int((parasites["len"] <= 4).sum()),
        parasite_len_med=parasites["len"].median() if parasites.height else None,
        host_exact=host["exact_births"] if host else None,
        host_pad_exact=host_pad["exact_births"] if host_pad else None,
        host_foreign=share(host["exec_foreign"], host["executed"]) if host else None,
        other_births=other.height,
        other_exact_share=share(other_exact.height, other.height),
        other_max_per_source=int(per_src["exact_of_source"].max()) if per_src.height else 0,
    )


def summarize(df: pl.DataFrame) -> str:
    f0 = lambda v: "–" if v is None else f"{v:,.0f}"
    f2 = lambda v: "–" if v is None else f"{v:.2f}"
    f3 = lambda v: "–" if v is None else f"{v:.3f}"
    agg = df.group_by("arm", maintain_order=True).agg(
        n=pl.len(),
        births=pl.col("births").median(),
        other_share=(pl.col("src_other") / pl.col("births")).median(),
        unowned_share=(pl.col("src_unowned") / pl.col("births")).median(),
        world_rep=pl.col("world_replicating").median(),
        dependent=pl.col("dependent").median(),
        dep_world_rep=pl.col("dependent_world_rep").median(),
        p1_seeds=(pl.col("dep_exact_after_share") >= 0.05).sum(),
        dep_share=pl.col("dep_exact_after_share").median(),
        p2_seeds=(pl.col("dep_still_dep_share") >= 0.8).sum(),
        dep_unowned_births=pl.col("dep_exact_unowned").median(),
        dep_foreign=pl.col("dep_foreign_med").median(),
        dep_foreign_div=pl.col("dep_foreign_med_div").median(),
        nonpar_share=pl.col("dep_nonpar_exact_after_share").median(),
        nonpar_unowned=pl.col("dep_nonpar_unowned_med").median(),
        rep_foreign=pl.col("rep_foreign_med").median(),
        rep_foreign_div=pl.col("rep_foreign_med_div").median(),
        p4_reg_seeds=(pl.col("parasites_reg") >= 1).sum(),
        p4_div_seeds=(pl.col("parasites_div") >= 1).sum(),
        p4_seeds=(pl.col("parasites") >= 1).sum(),
        parasites=pl.col("parasites").median(),
        par_share=pl.col("parasite_exact_after_share").median(),
        p5_seeds=(pl.col("main_parasite_len") < pl.col("main_rep_len")).sum(),
        par_len=pl.col("main_parasite_len").median(),
        p7_seeds=((pl.col("main_parasite_len") <= 4)).sum(),
        content_free=(
            (pl.col("host_pad_exact") >= 0.9 * pl.col("host_exact")) & (pl.col("host_exact") > 0)
        ).sum(),
        host_tested=pl.col("host_exact").is_not_null().sum(),
        p6_share=pl.col("other_exact_share").median(),
        p6_max=pl.col("other_max_per_source").max(),
    )
    lines = [
        "E005 summary. Counts are seeds out of n; other columns are medians across seeds. "
        f"Exact-birth shares count births after tick {AFTER_TICK:,}.",
        "",
        "| arm | n | births | other-source share | unowned-source share | world-replicating genomes "
        "| dependent | dependent but replicator under world physics | P1 seeds (dependent share >= 5%) "
        "| dependent share | P2 seeds (>= 80% still dependent) | dependent exact births from debris "
        "| dependent foreign share (all carriers / dividers) | replicator foreign share (all / dividers) "
        "| non-parasitic dependent share of exact births | their unowned share "
        "| P4 seeds, registered (all carriers) | P4 seeds, dividers | P4 seeds, carriers with 2+ children | parasite genomes | parasite share of exact births "
        "| P5 seeds (parasite shorter) | main parasite len | P7 seeds (len <= 4) | content-free of tested "
        "| P6 other-source exact share | P6 max exact per source |",
        "|" + "---|" * 27,
    ]
    for r in agg.iter_rows(named=True):
        lines.append(
            f"| {r['arm']} | {r['n']} | {f0(r['births'])} | {f3(r['other_share'])} | {f3(r['unowned_share'])} "
            f"| {f0(r['world_rep'])} | {f0(r['dependent'])} | {f0(r['dep_world_rep'])} "
            f"| {r['p1_seeds']} | {f3(r['dep_share'])} | {r['p2_seeds']} | {f0(r['dep_unowned_births'])} "
            f"| {f2(r['dep_foreign'])} / {f2(r['dep_foreign_div'])} | {f3(r['rep_foreign'])} / {f3(r['rep_foreign_div'])} "
            f"| {f3(r['nonpar_share'])} | {f2(r['nonpar_unowned'])} "
            f"| {r['p4_reg_seeds']} | {r['p4_div_seeds']} | {r['p4_seeds']} | {f0(r['parasites'])} | {f3(r['par_share'])} "
            f"| {r['p5_seeds']} | {f0(r['par_len'])} | {r['p7_seeds']} | {r['content_free']} of {r['host_tested']} "
            f"| {f3(r['p6_share'])} | {f0(r['p6_max'])} |"
        )
    lines += ["", "Main parasite per seed (most exact births among parasite lineages by the 2+-children test; foreign and unowned shares are medians over those carriers):", "",
              "| arm | seed | len | exact births | depth | foreign share | unowned share | host harness exact (genome / padded) | disasm |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in df.sort("arm", "seed").iter_rows(named=True):
        if r["main_parasite_len"] is None:
            lines.append(f"| {r['arm']} | {r['seed']} | – | – | – | – | – | – | no parasite lineage |")
            continue
        lines.append(
            f"| {r['arm']} | {r['seed']} | {r['main_parasite_len']} | {f0(r['main_parasite_exact'])} "
            f"| {r['main_parasite_depth']} | {f2(r['main_parasite_foreign'])} | {f2(r['main_parasite_unowned'])} "
            f"| {f0(r['host_exact'])} / {f0(r['host_pad_exact'])} | `{r['main_parasite_disasm']}` |"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--arms", nargs="*", default=list(ARMS))
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--no-host", action="store_true", help="skip the two-genome harness")
    ap.add_argument("--summarize-only", action="store_true", help="reuse runs/e005/runs.csv")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    if a.summarize_only:
        df = pl.read_csv(OUT / "runs.csv")
    else:
        exe = binary()
        jobs = [(arm, s) for arm in a.arms for s in range(1, a.seeds + 1)]
        with ThreadPoolExecutor(a.jobs) as ex:
            for msg in ex.map(lambda j: ensure_world_classes(exe, *j), jobs):
                print(msg, flush=True)
        rows = []
        for arm, s in jobs:
            rows.append(analyse(arm, s, None if a.no_host else exe))
            r = rows[-1]
            print(f"{arm}/s{s}: dependent {r['dependent']}, parasites {r['parasites']}, "
                  f"main parasite len {r['main_parasite_len']}", flush=True)
        df = pl.DataFrame(rows)
        df.write_csv(OUT / "runs.csv")

    text = summarize(df)
    (OUT / "summary.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
