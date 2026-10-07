import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="evo run explorer")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # evo run explorer

    An interactive look at one `evo-core` run directory (written by
    `evo-core --out DIR`; file formats in `docs/instrumentation.md`).

    ```
    cd analysis
    uv run marimo edit explore.py     # notebook: code visible and editable
    uv run marimo run explore.py      # app: controls and charts only
    ```

    **How marimo works.** Each cell is a Python function. A name that a cell
    defines (without a leading `_`) is visible to every other cell, and
    marimo runs cells in dependency order, not page order. Change a control
    (the run picker, the tick window, a click on the space-time plot) and
    every cell that reads it re-runs by itself; nothing goes stale. Two
    rules follow from that: each name is defined in exactly one cell, and
    names starting with `_` stay private to their cell. The notebook is a
    plain `.py` file, so it diffs and commits like any other code.
    """)
    return


@app.cell
def _():
    # Libraries, plus two local modules from this folder: evo_run loads a
    # run directory into polars frames; report has the derived tables
    # (birth kinds, death signatures) and the palette of the static report.
    import altair as alt
    import marimo as mo
    import polars as pl

    from evo_run import ROOT, classify, load
    from report import (
        BIRTH_COLOR,
        BIRTH_ORDER,
        BLUE,
        CLASS_COLOR,
        GRAY,
        GRAY_LIGHT,
        GRID,
        INK,
        INK_2,
        SEQ_STEPS,
        SIG_COLOR,
        SIG_ORDER,
        SURFACE,
        births_typed,
        class_order,
        deaths_with_signature,
        population_by_class,
    )

    # Altair embeds each chart's rows in the page and by default refuses
    # more than a few thousand. A 50,000-tick run with a census every 100
    # ticks has about 8,000 patch rows; for much longer runs, narrow the
    # tick window rather than let the page grow.
    alt.data_transformers.disable_max_rows()
    return (
        BIRTH_COLOR,
        BIRTH_ORDER,
        BLUE,
        CLASS_COLOR,
        GRAY,
        GRAY_LIGHT,
        GRID,
        INK,
        INK_2,
        ROOT,
        SEQ_STEPS,
        SIG_COLOR,
        SIG_ORDER,
        SURFACE,
        alt,
        births_typed,
        class_order,
        classify,
        deaths_with_signature,
        load,
        mo,
        pl,
        population_by_class,
    )


@app.cell
def _(CLASS_COLOR, GRAY_LIGHT, GRID, INK, INK_2, SURFACE, alt, class_order):
    # Small helpers used by the chart cells below.

    def look(chart):
        """Apply the palette's surface, ink and grid colors. Call it last, on
        the outermost chart: altair only accepts `configure_*` at the top
        level. Charts keep this light surface in marimo's dark theme too."""
        return (
            chart.configure(background=SURFACE, padding=8)
            .configure_view(stroke=None)
            .configure_axis(
                domainColor=GRID, gridColor=GRID, tickColor=GRID,
                labelColor=INK_2, titleColor=INK_2, titleFontWeight="normal",
            )
            .configure_title(anchor="start", color=INK, fontSize=13, fontWeight="normal")
            .configure_legend(orient="top", labelColor=INK_2, titleColor=INK_2, symbolOpacity=1)
        )

    def class_color(names):
        """Color scale for harness classes. A class keeps its color whatever
        other classes a run contains; an unexpected label is drawn gray."""
        dom = class_order(names)
        return alt.Scale(domain=dom, range=[CLASS_COLOR.get(k, GRAY_LIGHT) for k in dom])

    def listing(disasm, ip=None):
        """One instruction per line with its byte offset, from a genome's
        `disasm` column. `lit` is the only two-byte instruction. Marks the
        line the instruction pointer is on, if `ip` is given."""
        lines, off = [], 0
        for ins in disasm.split(" ; "):
            mark = "   <- ip" if off == ip else ""
            lines.append(f"{off:3}  {ins}{mark}")
            off += 2 if ins.startswith("lit ") else 1
        return "\n".join(lines)

    return class_color, listing, look


@app.cell
def _(ROOT, mo):
    # Every directory under runs/ that holds a meta.json is a run.
    run_dirs = {
        p.parent.relative_to(ROOT / "runs").as_posix(): p.parent
        for p in sorted((ROOT / "runs").rglob("meta.json"))
    }
    mo.stop(not run_dirs, mo.md("No run directories under `runs/`. Record one with `evo-core --out DIR`."))
    _default = "diag/control_s1" if "diag/control_s1" in run_dirs else next(iter(run_dirs))
    picker = mo.ui.dropdown(options=list(run_dirs), value=_default, searchable=True, label="run")
    classify_btn = mo.ui.run_button(
        label="Classify genomes",
        tooltip="Run every genome alone in the single-genome harness (writes classes.csv)",
    )
    mo.hstack([picker, classify_btn], justify="start", gap=1)
    return classify_btn, picker, run_dirs


@app.cell
def _(births_typed, classify, classify_btn, deaths_with_signature, load, picker, run_dirs):
    # Load the picked run. The button first runs `evo-core --classify`, which
    # labels every genome replicator / one_shot / inexact / loafer / dies by running it
    # alone from a fresh start. Without classes.csv every class is "unknown".
    run_dir = run_dirs[picker.value]
    if classify_btn.value:
        classify(run_dir)
    run = load(run_dir)
    births = births_typed(run)  # + kind: exact, mutant, stillborn
    deaths = deaths_with_signature(run)  # + sig, and class of the birth genome
    orgs = run.class_of(run.orgs, "now_hash")  # census rows + class of the current body
    every = run.meta["census_every"]
    end = run.meta["ticks_run"]
    return births, deaths, end, every, orgs, run


@app.cell(hide_code=True)
def _(births, deaths, end, mo, orgs, pl, run):
    _m = run.meta
    _cfg = _m["config"]
    _tiles = mo.hstack(
        [
            mo.stat(str(_cfg["seed"]), label="seed"),
            mo.stat(f"{end:,}", label="ticks run", caption=f"of {_m['ticks_requested']:,}"),
            mo.stat(f"{births.height:,}", label="births",
                    caption=f"{(births['kind'] == 'exact').sum():,} exact copies"),
            mo.stat(f"{deaths.height:,}", label="deaths"),
            mo.stat(f"{orgs.filter(pl.col('tick') == end).height:,}", label="alive at end"),
            mo.stat(f"{run.genomes.height:,}", label="genomes seen"),
        ],
        widths="equal",
    )
    _dirty = " with uncommitted changes" if _m["git_dirty"] else ""
    _parts = [
        _tiles,
        mo.md(f"Built from commit `{_m['git_commit']}`{_dirty}; census every {_m['census_every']} ticks."),
    ]
    if run.classes is None:
        _parts.append(mo.callout(
            mo.md("No `classes.csv` for this run, so every class shows as `unknown`. "
                  "Press **Classify genomes**."),
            kind="warn",
        ))
    _config = pl.DataFrame({"field": list(_cfg), "value": [str(v) for v in _cfg.values()]})
    _parts.append(mo.accordion({"Config (energy fields are milli-units)": mo.ui.table(
        _config, selection=None, page_size=40, show_column_summaries=False)}))
    mo.vstack(_parts)
    return


@app.cell
def _(end, every, mo):
    # The tick window limits every time-based chart below. A UI element's
    # value can only be read in a cell other than the one that creates it,
    # so the slider lives in its own cell.
    _stop = max(end, every)
    window = mo.ui.range_slider(
        start=0, stop=_stop, step=every, value=[0, _stop],
        show_value=True, full_width=True, label="tick window",
    )
    window
    return (window,)


@app.cell
def _(BIRTH_COLOR, BIRTH_ORDER, INK_2, SURFACE, alt, births, class_color, class_order, every, look, mo, pl, population_by_class, run, window):
    # Population by harness class of each body's current bytes, and births
    # per census interval by kind. Hover the top chart for the counts at a
    # census tick.
    _lo, _hi = window.value
    _x = alt.Scale(domain=[_lo, _hi], nice=False)

    _wide = population_by_class(run).filter(pl.col("tick").is_between(_lo, _hi))
    _classes = [c for c in _wide.columns if c != "tick" and _wide[c].sum() > 0]
    _rank = {k: i for i, k in enumerate(class_order(_classes))}
    _long = _wide.unpivot(index="tick", on=_classes, variable_name="class", value_name="organisms")
    _long = _long.with_columns(rank=pl.col("class").replace_strict(_rank))
    _area = alt.Chart(_long).mark_area(stroke=SURFACE, strokeWidth=1).encode(
        x=alt.X("tick:Q", scale=_x, title=None),
        y=alt.Y("organisms:Q", stack=True, title="organisms"),
        color=alt.Color("class:N", scale=class_color(_classes), title="class of current body"),
        order=alt.Order("rank:Q"),
    )
    # Crosshair: an invisible rule at every census tick; the one nearest
    # the pointer shows and carries the tooltip.
    _hover = alt.selection_point(nearest=True, on="pointerover", fields=["tick"], empty=False, clear="pointerout")
    _rule = alt.Chart(_wide).mark_rule(color=INK_2).encode(
        x="tick:Q",
        opacity=alt.condition(_hover, alt.value(0.6), alt.value(0)),
        tooltip=[alt.Tooltip("tick:Q", format=",")] + [alt.Tooltip(f"{c}:Q") for c in _classes],
    ).add_params(_hover)
    _pop = (_area + _rule).properties(
        width="container", height=240, title="Living organisms by harness class of their current body")

    # Bar [bin, bin + every) holds the births in that interval. The stack
    # is computed here (y0 to y1 per kind, exact at the bottom) and drawn
    # as rectangles, which keeps the x axis identical to the chart above.
    _b = (
        births.filter(pl.col("tick").is_between(_lo, _hi))
        .with_columns(bin=(pl.col("tick") // every) * every)
        .group_by("bin", "kind").len("births")
        .with_columns(rank=pl.col("kind").replace_strict({k: i for i, k in enumerate(BIRTH_ORDER)}))
        .sort("bin", "rank")
        .with_columns(y1=pl.col("births").cum_sum().over("bin"))
        .with_columns(y0=pl.col("y1") - pl.col("births"), bin_end=pl.col("bin") + every * 0.85)
    )
    _bars = alt.Chart(_b).mark_rect().encode(
        x=alt.X("bin:Q", scale=_x, title="tick"),
        x2="bin_end:Q",
        y=alt.Y("y0:Q", title="births"),
        y2="y1:Q",
        color=alt.Color("kind:N", title="birth kind",
                        scale=alt.Scale(domain=BIRTH_ORDER, range=[BIRTH_COLOR[k] for k in BIRTH_ORDER])),
        tooltip=[alt.Tooltip("bin:Q", title="interval from tick", format=","), "kind:N", "births:Q"],
    ).properties(width="container", height=130, title=f"Births per {every}-tick interval")

    mo.vstack([mo.md("## Population"), look(_pop), look(_bars)])
    return


@app.cell
def _(INK_2, alt, class_color, every, look, mo, orgs, pl, run, window):
    # Space-time view, like a cellular-automaton diagram: position on the
    # ring across, time down. Each census row of each living organism is one
    # block, from its body start to its end, one census interval tall.
    # Organisms that lived and died between two censuses do not appear.
    # Click a block to inspect that organism below; click empty space to clear.
    _lo, _hi = window.value
    _ps = run.meta["config"]["patch_size"]
    _o = orgs.filter(pl.col("tick").is_between(_lo, _hi)).select(
        "tick", "id", "start", "len", "class", "energy", "offspring", "op_at_ip", "ip_off",
        end=pl.col("start") + pl.col("len"),
        tick_end=pl.col("tick") + every,
        age=pl.col("tick") - pl.col("birth_tick"),
        somatic=pl.col("birth_hash") != pl.col("now_hash"),
    )
    mo.stop(_o.height == 0, mo.md("No living organisms in this tick window."))

    # Zoom to the occupied stretch of the ring, plus a margin.
    _x0, _x1 = _o["start"].min(), _o["end"].max()
    _pad = max(64, (_x1 - _x0) // 20)
    _x0, _x1 = max(0, _x0 - _pad), _x1 + _pad
    # Axis ticks on a step that divides the patch size, so every patch
    # boundary is a tick; boundaries get a darker grid line.
    _steps = sorted({max(1, _ps >> k) for k in range(9)} | {_ps << k for k in range(1, 6)})
    _step = next((s for s in _steps if (_x1 - _x0) / s <= 12), _steps[-1])
    _ticks = list(range(-(-_x0 // _step) * _step, _x1 + 1, _step))
    _axis = alt.Axis(
        values=_ticks, format="d",
        gridColor={"condition": {"test": f"datum.value % {_ps} === 0", "value": INK_2}, "value": "#ecebe7"},
        gridWidth={"condition": {"test": f"datum.value % {_ps} === 0", "value": 1.5}, "value": 1},
        title=f"position on the ring (byte address); dark lines are patch boundaries ({_ps} bytes)",
    )

    _pick = alt.selection_point(fields=["id"], on="click")
    _color = class_color(_o["class"].unique().to_list())
    # The thin stroke in the fill color closes hairline gaps between
    # neighbouring blocks that anti-aliasing would otherwise leave.
    _chart = alt.Chart(_o).mark_rect(strokeWidth=0.6).encode(
        x=alt.X("start:Q", scale=alt.Scale(domain=[_x0, _x1], nice=False, zero=False), axis=_axis),
        x2="end:Q",
        y=alt.Y("tick:Q", scale=alt.Scale(domain=[_lo, _hi + every], reverse=True, nice=False), title="tick"),
        y2="tick_end:Q",
        color=alt.Color("class:N", scale=_color, title="class of current body"),
        stroke=alt.Stroke("class:N", scale=_color),
        opacity=alt.condition(_pick, alt.value(1), alt.value(0.25)),
        tooltip=[
            "id:Q", "class:N", alt.Tooltip("tick:Q", format=","), "age:Q",
            "start:Q", "len:Q", alt.Tooltip("energy:Q", format=".1f"), "offspring:Q",
            alt.Tooltip("op_at_ip:N", title="next op"), alt.Tooltip("somatic:N", title="body changed since birth"),
        ],
    ).add_params(_pick).properties(width="container", height=520, title="Space-time: bodies at each census")

    spacetime = mo.ui.altair_chart(look(_chart), legend_selection=False)
    mo.vstack([mo.md("## Space-time"), spacetime])
    return (spacetime,)


@app.cell
def _(BIRTH_COLOR, BIRTH_ORDER, BLUE, alt, births, deaths, listing, look, mo, orgs, pl, run, spacetime):
    # One organism's life: the one clicked above, or before any click the
    # one with the most children.
    _sel = spacetime.value
    if len(_sel) > 0:
        org_id = int(_sel["id"][0])
    else:
        org_id = int(orgs.sort("offspring", descending=True)["id"][0])

    _life = orgs.filter(pl.col("id") == org_id).sort("tick")
    _death = deaths.filter(pl.col("id") == org_id)
    _born = births.filter(pl.col("child") == org_id)
    _kids = births.filter(pl.col("executor") == org_id)
    _first, _last = _life.row(0, named=True), _life.row(-1, named=True)

    # Summary line.
    _birth_txt = (f"born tick {_first['birth_tick']:,} from organism {_first['parent']} "
                  f"({_born['kind'][0]} birth)" if _born.height else "seeded at tick 0")
    if _death.height:
        _d = _death.row(0, named=True)
        _end_txt = f"died tick {_d['tick']:,} at age {_d['age']:,} ({_d['sig']}, {_d['energy']:.1f} energy left)"
    else:
        _end_txt = f"alive at tick {_last['tick']:,}"
    _kid_counts = ", ".join(f"{n} {k}" for k, n in _kids.group_by("kind").len().sort("kind").iter_rows()) or "none"

    # Energy at each census, plus the death record; children as ticks on
    # the baseline, colored by kind.
    _e = _life.select("tick", "energy")
    if _death.height:
        _e = pl.concat([_e, _death.select("tick", "energy")])
    _line = alt.Chart(_e).mark_line(color=BLUE, strokeWidth=2, point=alt.OverlayMarkDef(color=BLUE, size=50)).encode(
        x=alt.X("tick:Q", title="tick", scale=alt.Scale(zero=False)),
        y=alt.Y("energy:Q", title="energy (units)"),
        tooltip=[alt.Tooltip("tick:Q", format=","), alt.Tooltip("energy:Q", format=".1f")],
    )
    _k = _kids.select("tick", "kind", "child").with_columns(y=pl.lit(0))
    _marks = alt.Chart(_k).mark_tick(thickness=2, size=14).encode(
        x="tick:Q", y="y:Q",
        color=alt.Color("kind:N", title="child", scale=alt.Scale(domain=BIRTH_ORDER, range=[BIRTH_COLOR[k] for k in BIRTH_ORDER])),
        tooltip=[alt.Tooltip("tick:Q", format=","), "kind:N", "child:Q"],
    )
    _energy = (_line + _marks).properties(
        width="container", height=200, title=f"Organism {org_id}: energy at each census (last point: at death)")

    # Genome at birth, and the body at the last census with the instruction
    # pointer marked. They differ when the body changed after birth (bit rot
    # or a foreign write): a somatic change.
    _g = dict(zip(run.genomes["raw_hash"], run.genomes["disasm"]))
    _bh, _nh = _first["birth_hash"], _last["now_hash"]
    _code = [mo.md(f"**Birth genome** `{_bh}`\n```\n{listing(_g[_bh])}\n```")]
    if _nh != _bh:
        _code.append(mo.md(f"**Body at tick {_last['tick']:,}** `{_nh}` (somatic change)\n"
                           f"```\n{listing(_g[_nh], _last['ip_off'])}\n```"))
    else:
        _code.append(mo.md(f"**At tick {_last['tick']:,}** body unchanged; ip at offset {_last['ip_off']}, "
                           f"next op `{_last['op_at_ip']}`"))

    _cls = run.class_of(pl.DataFrame({"h": [_bh]}), "h")["class"][0]
    mo.vstack([
        mo.md(f"## Organism {org_id}\n{_birth_txt}; {_end_txt}. Class of birth genome: `{_cls}`. "
              f"Children: {_kids.height:,} ({_kid_counts})."),
        look(_energy),
        mo.hstack(_code, justify="start", gap=2, align="start"),
    ])
    return (org_id,)


@app.cell
def _(mo):
    patch_metric = mo.ui.dropdown(
        options={
            "pool energy (units)": "pool",
            "living organisms (body starts)": "orgs",
            "energy absorbed in the interval (units)": "absorbed",
            "income lost to the cap in the interval (units)": "overflow",
        },
        value="pool energy (units)",
        label="patch metric",
    )
    return (patch_metric,)


@app.cell
def _(SEQ_STEPS, alt, every, look, mo, patch_metric, pl, run, window):
    # One row per patch, one column per census. Pools and organism counts
    # are the state at the census tick (drawn over the interval after it);
    # absorbed and overflow are totals over the interval that ends there
    # (drawn over the interval before it).
    _lo, _hi = window.value
    _col = patch_metric.value
    _shift = -every if _col in ("absorbed", "overflow") else 0
    _p = run.patches.filter(pl.col("tick").is_between(_lo, _hi)).with_columns(
        # Each cell reaches half an interval into the next one, which is
        # drawn over it; this hides hairline gaps from anti-aliasing.
        x0=pl.col("tick") + _shift, x1=pl.col("tick") + _shift + every * 1.5)
    _top = run.meta["config"]["patch_cap"] / 1000 if _col == "pool" else max(_p[_col].max() or 1, 1)
    _scale = alt.Scale(domain=[0, _top], range=SEQ_STEPS)
    _heat = alt.Chart(_p.sort("tick", "patch")).mark_rect(clip=True).encode(
        x=alt.X("x0:Q", title="tick", scale=alt.Scale(domain=[_lo, _hi + every], nice=False)),
        x2="x1:Q",
        y=alt.Y("patch:O", title="patch"),
        color=alt.Color(f"{_col}:Q", title=None, scale=_scale),
        tooltip=[alt.Tooltip("tick:Q", format=","), "patch:O", alt.Tooltip("pool:Q", format=".1f"), "orgs:Q",
                 alt.Tooltip("absorbed:Q", format=".1f"), alt.Tooltip("overflow:Q", format=".1f")],
    ).properties(width="container", height=max(160, 14 * run.patches["patch"].n_unique()),
                 title=f"Patches: {patch_metric.selected_key}")
    mo.vstack([mo.md("## Patches"), patch_metric, look(_heat)])
    return


@app.cell
def _(GRAY, SIG_COLOR, SIG_ORDER, alt, deaths, look, mo, pl, window):
    # Every death as a dot: when it died and how old it was (log scale).
    # Signatures, assigned in this order: stillborn (born with 0 energy),
    # mid_copy (died holding a half-built child), newborn (never divided),
    # after_dividing. All deaths so far are from failed upkeep (starvation).
    _lo, _hi = window.value
    _d = deaths.filter(pl.col("tick").is_between(_lo, _hi)).select(
        "tick", "id", "age", "sig", "class", "born_with", "max_energy", "offspring", "absorbs", "absorb_short",
        age1=pl.col("age").clip(lower_bound=1),
    )
    _dots = alt.Chart(_d).mark_circle(size=40, opacity=0.55).encode(
        x=alt.X("tick:Q", title="tick of death", scale=alt.Scale(domain=[_lo, _hi], nice=False)),
        y=alt.Y("age1:Q", title="age at death (ticks, log; age 0 drawn at 1)", scale=alt.Scale(type="log"),
                axis=alt.Axis(values=[1, 10, 100, 1_000, 10_000, 100_000], format=",")),
        color=alt.Color("sig:N", title="signature",
                        scale=alt.Scale(domain=SIG_ORDER, range=[SIG_COLOR.get(k, GRAY) for k in SIG_ORDER])),
        tooltip=["id:Q", "sig:N", "class:N", alt.Tooltip("tick:Q", format=","), "age:Q",
                 alt.Tooltip("born_with:Q", format=".1f"), alt.Tooltip("max_energy:Q", format=".1f"),
                 "offspring:Q", "absorbs:Q", "absorb_short:Q"],
    ).properties(width="container", height=260, title="Deaths: age at death by signature")

    # Same breakdown as report.py, for the window. short_share: fraction of
    # an organism's absorbs that got less than a full ration because the
    # patch pool was short (median over deaths).
    _table = (
        deaths.filter(pl.col("tick").is_between(_lo, _hi))
        .group_by("class", "sig")
        .agg(
            n=pl.len(),
            age_median=pl.col("age").median(),
            born_with_median=pl.col("born_with").median(),
            max_energy_median=pl.col("max_energy").median(),
            short_share=pl.col("short_share").median().round(2),
            alloc_fail_any=(pl.col("allocs_fail") > 0).mean().round(2),
        )
        .sort("class", "n", descending=[False, True])
    )
    mo.vstack([mo.md("## Deaths"), look(_dots),
               mo.ui.table(_table, selection=None, show_column_summaries=False)])
    return


@app.cell
def _(births, end, mo, pl, run):
    # Every genome seen in the run. raw_hash is over the bytes; func_hash
    # ignores modifier bits the decoder does not read, so genomes that only
    # differ in encoding share one. Select a row to see its listing.
    _births = births.group_by("raw_hash").agg(births_in_run=pl.len())
    _alive = run.census.filter(pl.col("tick") == end).select(pl.col("now_hash").alias("raw_hash"), alive_at_end="count")
    _g = (
        run.class_of(run.genomes, "raw_hash")
        .join(_births, on="raw_hash", how="left")
        .join(_alive, on="raw_hash", how="left")
        .fill_null(0)
        .select("raw_hash", "func_hash", "class", "len", "origin", "first_tick", "births_in_run", "alive_at_end", "disasm")
        .sort("births_in_run", descending=True)
    )
    genome_table = mo.ui.table(_g, selection="single", page_size=10, show_column_summaries=False,
                               label=f"{_g.height} raw genomes, {_g['func_hash'].n_unique()} functional")
    mo.vstack([mo.md("## Genomes"), genome_table])
    return (genome_table,)


@app.cell
def _(genome_table, listing, mo):
    _sel = genome_table.value
    mo.stop(len(_sel) == 0, mo.md("_Select a genome above to see its listing._"))
    _r = _sel.row(0, named=True)
    mo.md(f"**{_r['raw_hash']}** ({_r['class']}, {_r['len']} bytes, {_r['origin']})\n```\n{listing(_r['disasm'])}\n```")
    return


@app.cell
def _(deaths):
    # Scratch space for your own queries. `run` holds every file as a polars
    # frame (run.births, run.deaths, run.census, run.orgs, run.patches,
    # run.genomes, run.classes, run.meta); `births`, `deaths` and `orgs`
    # above add the derived columns. Energy columns come in milli-units
    # (`energy_m`) and units (`energy`). Example: the longest-lived deaths.
    deaths.sort("age", descending=True).select("id", "age", "class", "sig", "offspring", "max_energy").head(10)
    return


if __name__ == "__main__":
    app.run()
