"""Diagnostic report for one evo-core run directory (docs/instrumentation.md).

    uv run report.py ../runs/diag/control_s1 --classify

Prints a text summary and writes PNGs to RUN_DIR/report/. The death table
answers the E002 question: when replicators die, how do they die?

Death signatures, assigned in this order:
  stillborn       born with 0 energy (parent's `divide` gave nothing)
  mid_copy        died while holding a half-built child region
  newborn         never divided
  after_dividing  divided at least once, not mid-copy at death
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import polars as pl
from matplotlib.colors import LinearSegmentedColormap

from evo_run import CLASSES, Run, classify, load

# Reference palette (dataviz skill, light mode). Three categorical slots
# validate all-pairs for scatter; the rest are neutral grays.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GRAY, GRAY_LIGHT = "#8a8984", "#c3c2bd"
CLASS_COLOR = {"replicator": BLUE, "loafer": ORANGE, "inexact": AQUA, "dies": GRAY, "unknown": GRAY_LIGHT}
SIG_ORDER = ["newborn", "mid_copy", "after_dividing", "stillborn"]
SIG_COLOR = {"newborn": BLUE, "mid_copy": ORANGE, "after_dividing": AQUA, "stillborn": GRAY}
BIRTH_ORDER = ["exact", "mutant", "stillborn"]
BIRTH_COLOR = {"exact": BLUE, "mutant": ORANGE, "stillborn": GRAY}
SEQ = LinearSegmentedColormap.from_list(
    "blue", ["#fcfcfb", "#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"]
)


def style(ax, title: str, xlabel: str | None = None, ylabel: str | None = None) -> None:
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", color=INK, fontsize=11)
    if xlabel:
        ax.set_xlabel(xlabel, color=INK_2)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK_2)
    ax.tick_params(colors=INK_2, labelsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def legend(ax, **kw) -> None:
    leg = ax.legend(frameon=False, fontsize=9, labelcolor=INK_2, **kw)
    for h in leg.legend_handles:
        h.set_alpha(1)


# ---- derived tables --------------------------------------------------------


def deaths_with_signature(run: Run) -> pl.DataFrame:
    d = run.class_of(run.deaths, "birth_hash")
    return d.with_columns(
        sig=pl.when(pl.col("born_with_m") == 0)
        .then(pl.lit("stillborn"))
        .when(pl.col("pending_len") > 0)
        .then(pl.lit("mid_copy"))
        .when(pl.col("offspring") == 0)
        .then(pl.lit("newborn"))
        .otherwise(pl.lit("after_dividing")),
        short_share=pl.col("absorb_short") / pl.col("absorbs").clip(lower_bound=1),
    )


def births_typed(run: Run) -> pl.DataFrame:
    b = run.class_of(run.births, "parent_now_hash", "parent_class")
    return b.with_columns(
        kind=pl.when(pl.col("endowment_m") == 0)
        .then(pl.lit("stillborn"))
        .when(pl.col("raw_hash") == pl.col("parent_now_hash"))
        .then(pl.lit("exact"))
        .otherwise(pl.lit("mutant"))
    )


def population_by_class(run: Run) -> pl.DataFrame:
    ticks = run.patches.select("tick").unique()
    c = run.class_of(run.census, "now_hash")
    wide = (
        c.group_by("tick", "class")
        .agg(pl.col("count").sum())
        .pivot(on="class", index="tick", values="count")
    )
    out = ticks.join(wide, on="tick", how="left").fill_null(0).sort("tick")
    for k in CLASSES:
        if k not in out.columns:
            out = out.with_columns(pl.lit(0).alias(k))
    return out


def class_order(names) -> list[str]:
    """Known classes in fixed order, then any unexpected label (drawn gray)."""
    names = set(names)
    return [k for k in CLASSES if k in names] + sorted(names - set(CLASSES))


# ---- text ------------------------------------------------------------------


def text_report(run: Run) -> None:
    m = run.meta
    cfg = m["config"]
    dirty = " (dirty)" if m["git_dirty"] else ""
    print(f"# Run {run.dir}")
    print(
        f"seed {cfg['seed']}, {m['ticks_run']} of {m['ticks_requested']} ticks, "
        f"commit {m['git_commit']}{dirty}, census every {m['census_every']}"
    )
    if run.classes is None:
        print("\n(no classes.csv: run with --classify for harness labels)")

    b = births_typed(run)
    d = deaths_with_signature(run)
    # Organisms alive at the last tick run. An extinct run's final census
    # has no rows, so this is empty then (not the last census with rows).
    end = m["ticks_run"]
    alive = run.orgs.filter(pl.col("tick") == end)
    print(f"\nbirths {b.height}, deaths {d.height}, alive at end {alive.height}")

    print("\n## Births by kind and parent class")
    print("exact = child bytes equal the parent's body at divide; stillborn = 0 endowment")
    print(
        b.group_by("kind", "parent_class")
        .agg(n=pl.len(), first=pl.col("tick").min(), last=pl.col("tick").max())
        .sort("n", descending=True)
    )

    pop = run.class_of(run.orgs, "now_hash")
    rep = pop.filter(pl.col("class") == "replicator")
    if rep.height:
        print(f"\nlast census with a replicator-class body alive: tick {rep['tick'].max()}")
    exact_rep = b.filter((pl.col("kind") == "exact") & (pl.col("parent_class") == "replicator"))
    if exact_rep.height:
        print(f"last exact birth from a replicator-class parent: tick {exact_rep['tick'].max()}")

    print("\n## Deaths by birth class and signature")
    print("short_share: fraction of the organism's absorbs that got less than a full ration")
    print("because the pool was short (median over deaths)")
    print(
        d.group_by("class", "sig")
        .agg(
            n=pl.len(),
            age_median=pl.col("age").median(),
            age_max=pl.col("age").max(),
            born_with_median=pl.col("born_with").median(),
            short_share=pl.col("short_share").median(),
            offspring_mean=pl.col("offspring").mean().round(2),
            alloc_fail_any=(pl.col("allocs_fail") > 0).mean().round(2),
            first=pl.col("tick").min(),
            last=pl.col("tick").max(),
        )
        .sort("class", "n", descending=[False, True])
    )

    print("\n## Alive at end")
    print("class: harness label of the current body, run alone from a fresh start. A living")
    print("organism can be in a state a fresh start never reaches, so the `last_*` columns")
    print("(activity over the last census interval) say what it is actually doing.")
    prev = (
        run.orgs.filter(pl.col("tick") < end)
        .filter(pl.col("tick") == pl.col("tick").max())
        .select("id", p_exec="executed", p_abs="absorbs", p_copy="copies", p_div="divides_ok")
    )
    surv = (
        run.class_of(alive, "now_hash")
        .join(run.genomes.select(pl.col("raw_hash").alias("now_hash"), "disasm"), on="now_hash", how="left")
        .join(prev, on="id", how="left")
        .fill_null(0)
    )
    print(
        surv.select(
            "id",
            (pl.col("tick") - pl.col("birth_tick")).alias("age"),
            "class",
            "offspring",
            somatic=pl.col("birth_hash") != pl.col("now_hash"),
            energy=pl.col("energy"),
            last_exec=pl.col("executed") - pl.col("p_exec"),
            last_absorb_share=((pl.col("absorbs") - pl.col("p_abs"))
                               / (pl.col("executed") - pl.col("p_exec")).clip(lower_bound=1)).round(2),
            last_copies=pl.col("copies") - pl.col("p_copy"),
            last_divides=pl.col("divides_ok") - pl.col("p_div"),
            disasm=pl.col("disasm"),
        ).sort("age", descending=True)
    )

    # Organisms whose bodies changed after birth and kept dividing.
    som = b.filter(pl.col("parent_hash") != pl.col("parent_now_hash"))
    if som.height:
        print("\n## Births from executors whose body changed since their own birth")
        print(
            som.group_by("executor")
            .agg(n=pl.len(), first=pl.col("tick").min(), last=pl.col("tick").max(),
                 stillborn=(pl.col("kind") == "stillborn").sum())
            .sort("n", descending=True)
            .head(5)
        )


# ---- plots -----------------------------------------------------------------


def plot_population(run: Run, out: Path) -> None:
    pop = population_by_class(run)
    b = births_typed(run)
    every = run.meta["census_every"]
    # Bar at [bin, bin + every) holds births in that interval.
    b = b.with_columns(bin=(pl.col("tick") // every) * every)
    bw = (
        b.group_by("bin", "kind").len()
        .pivot(on="kind", index="bin", values="len")
        .fill_null(0)
        .sort("bin")
    )
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True, facecolor=SURFACE,
                                 gridspec_kw={"height_ratios": [3, 2]})
    present = [k for k in class_order(c for c in pop.columns if c != "tick") if pop[k].sum() > 0]
    a1.stackplot(pop["tick"], *[pop[k] for k in present], labels=present,
                 colors=[CLASS_COLOR.get(k, GRAY_LIGHT) for k in present], edgecolor=SURFACE, linewidth=0.8)
    style(a1, "Living organisms by harness class of their current body", ylabel="organisms")
    legend(a1, loc="upper right")
    bottom = None
    for k in BIRTH_ORDER:
        if k in bw.columns:
            a2.bar(bw["bin"], bw[k], width=every * 0.9, bottom=bottom, color=BIRTH_COLOR[k],
                   label=k, align="edge")
            bottom = bw[k] if bottom is None else bottom + bw[k]
    style(a2, f"Births per {every}-tick interval", xlabel="tick", ylabel="births")
    legend(a2, loc="upper right")
    fig.tight_layout()
    fig.savefig(out / "population.png", dpi=150)
    plt.close(fig)


def plot_spacetime(run: Run, out: Path) -> None:
    o = run.class_of(run.orgs, "now_hash")
    if o.height == 0:
        return
    ps = run.meta["config"]["patch_size"]
    lo, hi = o["start"].min(), (o["start"] + o["len"]).max()
    pad = max(64, (hi - lo) // 20)
    lo, hi = max(0, lo - pad), hi + pad
    fig, ax = plt.subplots(figsize=(10, 8), facecolor=SURFACE)
    for k in class_order(o["class"].unique()):
        s = o.filter(pl.col("class") == k)
        if s.height:
            ax.hlines(s["tick"], s["start"], s["start"] + s["len"], colors=CLASS_COLOR.get(k, GRAY_LIGHT),
                      linewidth=2.2, label=k)
    for x in range(-(-lo // ps) * ps, hi + 1, ps):
        ax.axvline(x, color=GRID, linewidth=0.8, zorder=0)
    style(ax, "Space-time: body positions at each census (patch boundaries as vertical lines)",
          xlabel="position on the ring (byte address)", ylabel="tick")
    ax.grid(False)
    ax.set_xlim(lo, hi)
    ax.invert_yaxis()
    legend(ax, loc="lower right")
    fig.tight_layout()
    fig.savefig(out / "spacetime.png", dpi=150)
    plt.close(fig)


def plot_patches(run: Run, out: Path) -> None:
    p = run.patches.sort("tick", "patch")
    grid = p.pivot(on="patch", index="tick", values="pool").sort("tick")
    ticks = grid["tick"].to_numpy()
    z = grid.drop("tick").to_numpy().T
    cap = run.meta["config"]["patch_cap"] / 1000
    fig, ax = plt.subplots(figsize=(10, 4), facecolor=SURFACE)
    im = ax.imshow(z, aspect="auto", cmap=SEQ, vmin=0, vmax=cap, interpolation="nearest",
                   extent=(ticks[0], ticks[-1], z.shape[0] - 0.5, -0.5))
    style(ax, "Patch pool energy (units) over time", xlabel="tick", ylabel="patch")
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, pad=0.01)
    cb.ax.tick_params(colors=INK_2, labelsize=8)
    cb.outline.set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "patches.png", dpi=150)
    plt.close(fig)


def plot_deaths(run: Run, out: Path) -> None:
    d = deaths_with_signature(run)
    if d.height == 0:
        return
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=SURFACE)
    for k in SIG_ORDER:
        s = d.filter(pl.col("sig") == k)
        if s.height:
            ax.scatter(s["tick"], s["age"].clip(lower_bound=1), s=9, color=SIG_COLOR[k],
                       alpha=0.6, linewidths=0, label=f"{k} ({s.height})")
    ax.set_yscale("log")
    style(ax, "Deaths: age at death by signature", xlabel="tick of death", ylabel="age (ticks, log)")
    legend(ax, loc="upper right", markerscale=2)
    fig.tight_layout()
    fig.savefig(out / "deaths.png", dpi=150)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--classify", action="store_true", help="(re)run the harness classifier first")
    ap.add_argument("--harness-ticks", type=int, default=3000)
    ap.add_argument("--no-plots", action="store_true")
    a = ap.parse_args()
    if a.classify:
        classify(a.run_dir, a.harness_ticks)
    run = load(a.run_dir)
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")
    pl.Config.set_tbl_hide_column_data_types(True)
    pl.Config.set_tbl_hide_dataframe_shape(True)
    pl.Config.set_tbl_rows(40)
    pl.Config.set_tbl_cols(20)
    pl.Config.set_tbl_width_chars(240)
    pl.Config.set_fmt_str_lengths(160)
    text_report(run)
    if not a.no_plots:
        out = Path(a.run_dir) / "report"
        out.mkdir(exist_ok=True)
        plot_population(run, out)
        plot_spacetime(run, out)
        plot_patches(run, out)
        plot_deaths(run, out)
        print(f"\nplots written to {out}")


if __name__ == "__main__":
    main()
