import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="evo leaderboards")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # evo leaderboards

    Who did best in one run, by many measures: the top few organisms and
    the top few genotypes in each category. `explore.py` follows a run
    over time and `world.py` follows the memory; this notebook ranks.

    ```
    cd analysis
    uv run marimo edit leaders.py
    ```

    **Organism**: one body, from its birth to its death (or to the end of
    the run). Rows come from `deaths.csv`, plus the last census row of
    every organism alive at the end, so every organism that ever lived is
    ranked, including those that lived and died between two censuses.

    **Genotype**: every organism born with the same genome bytes (its
    birth `raw_hash`). These organisms copy themselves without sex, so
    there is no interbreeding test to draw species lines with; the
    genotype is the nearest unit. The grouping control also offers
    `func_hash`, which merges genomes that differ only in bits the CPU
    ignores, so they behave the same (unless a genome reads its own bytes
    as data or jumps into a `lit` operand). That is the closer analogue of
    a species here.

    **Children** count for the organism that executed the `divide` (the
    parent). Kinds as in `explore.py`: `exact` (the child's bytes equal
    the parent's body at `divide`: same genotype), `mutant` (they differ:
    a copy error, or bytes copied from somewhere else), `stillborn` (born
    with no energy; it dies at its first upkeep). Live children are exact
    plus mutant.

    **Class** is the single-genome harness label of the birth genome
    (`classes.csv`): a `replicator` makes exact copies alone, the other
    classes do not.

    **Distance.** Bodies never move: an organism keeps one address from
    birth to death (no organism's start changes between censuses in the
    E015 and E016 runs checked). Two measures stand in for distance
    travelled: how far from its own body start it placed a child (ring
    distance between the two starts, at most half the world), and how far
    from its own body its instruction pointer (IP, the address of the next
    instruction it runs) was seen at a census. Both are large only when
    the IP has left the body, since `alloc` claims the child's memory near
    the IP.

    **Generation depth**: the longest unbroken chain of exact copies of one
    genome that ends at an organism. An exact child of a carrier that was
    not itself born by an exact copy has depth 1, its exact child depth 2,
    and so on. This is E005's measure except that E005 also counted
    stillborn exact copies, which here are `stillborn` and can only have
    added one generation at the end of a chain.

    **Parasite**, as E005 defined a parasite lineage: a genotype that does
    not replicate alone (class not `replicator` or `unknown`), with at
    least 2 exact copies in the world and a generation depth of at least
    5, whose carriers with two or more children ran more than 25% of their
    instructions on other living organisms' bytes (median over those
    carriers). A single organism counts as a parasite when more than 25%
    of its instructions ran on other living organisms' bytes; those are
    ranked by exact children.

    Click a row in any table to see that organism or genotype at the
    bottom, with buttons to walk to its parent or its genotype.
    """)
    return


@app.cell
def _():
    # Libraries, the run-set lister and file locator from evo_run, the
    # pseudo-code reader, and the palette shared with report.py.
    import gzip
    import json

    import altair as alt
    import marimo as mo
    import numpy as np
    import polars as pl

    from evo_run import HASH_COLS, MILLI, TEXT_COLS, csv_path, run_sets
    from pseudo import explain
    from report import BLUE, GRID, INK, INK_2, SURFACE

    return (
        BLUE,
        GRID,
        HASH_COLS,
        INK,
        INK_2,
        MILLI,
        SURFACE,
        TEXT_COLS,
        alt,
        csv_path,
        explain,
        gzip,
        json,
        mo,
        np,
        pl,
        run_sets,
    )


@app.cell
def _(GRID, HASH_COLS, INK, INK_2, MILLI, SURFACE, TEXT_COLS, csv_path, gzip, pl):
    # Small helpers used by the cells below.

    # The lifetime counters read for every organism (docs/instrumentation.md,
    # OrgStats). Runs older than a counter lack its column; `read` skips it.
    STATS = [
        "born_with_m", "executed", "absorb_gain_m", "copies", "reads_foreign", "exec_foreign",
        "exec_unowned", "endowed_m", "max_energy_m", "starved_ticks", "paid_for_others_m",
        "gained_from_others_m", "writes_foreign", "overwritten", "cycles_taken_m", "cycles_lost_m",
        "exec_by_others",
    ]

    def read(run_dir, name, cols, keep=None, **exprs):
        """The listed columns of one CSV of a run (plain or .gz) that the
        file has, plus the named expressions, then only the `keep` columns
        if given; read in polars' streaming mode, so a 4 M-row
        deaths.csv.gz peaks under 1 GB instead of being decompressed whole
        first. Energy columns (`_m`, milli-units) come back in units,
        without the suffix. None if the file is missing."""
        p = csv_path(run_dir, name)
        if p is None:
            return None
        with gzip.open(p, "rt") if p.suffix == ".gz" else open(p) as f:
            have, empty = f.readline().strip().split(","), not f.readline().strip()
        cols = [c for c in cols if c in have]
        lf = pl.scan_csv(p, schema_overrides={c: pl.Utf8 for c in HASH_COLS[name] if c in cols}).select(cols)
        if empty:
            # A header-only file (no births yet) infers every column as text.
            lf = lf.with_columns(pl.col(c).cast(pl.Int64) for c in cols if c not in TEXT_COLS | set(HASH_COLS[name]))
        milli = [c for c in cols if c.endswith("_m")]
        lf = lf.with_columns(**exprs).with_columns((pl.col(c) / MILLI).alias(c[:-2]) for c in milli).drop(milli)
        return (lf if keep is None else lf.select(keep)).collect(engine="streaming")

    def look(chart):
        """The palette's surface, ink and grid colors (as in explore.py). Call
        it last, on the outermost chart."""
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

    return STATS, look, read


@app.cell
def _(mo, run_sets):
    # Every complete run under runs/, grouped into sets as in explore.py:
    # newest set first, dated by the day its earliest run finished.
    runs_by_set = run_sets()
    mo.stop(not runs_by_set, mo.md("No complete run directories under `runs/`. Record one with `evo-core --out DIR`."))
    set_picker = mo.ui.dropdown(options=list(runs_by_set), value=next(iter(runs_by_set)), searchable=True, label="set")
    return runs_by_set, set_picker


@app.cell
def _(mo, runs_by_set, set_picker):
    # The runs of the picked set, newest first; a new set picks its first.
    _runs = runs_by_set[set_picker.value]
    picker = mo.ui.dropdown(options=_runs, value=next(iter(_runs)), searchable=True, label="run")
    mo.hstack([set_picker, picker], justify="start", gap=1)
    return (picker,)


@app.cell
def _(STATS, json, mo, np, pl, picker, read):
    # Load the picked run into one row per organism that ever lived, with
    # what it did. For a 250,000-tick E016 run (4 M organisms) the whole
    # notebook takes about 9 s and peaks near 4.4 GB; only the tables
    # returned here are kept.
    run_dir = picker.value
    meta = json.loads((run_dir / "meta.json").read_text())
    n = meta["config"]["world_size"]
    ps = meta["config"]["patch_size"]

    with mo.status.spinner(title="Reading the run"):
        # Every organism: its death row, or for one alive at the end its
        # last census row. Bodies never move, so start and len are fixed.
        _dead = read(run_dir, "deaths", ["tick", "id", "age", "len", "start", "birth_hash", *STATS],
                     birth_tick=pl.col("tick") - pl.col("age"), alive=pl.lit(False))
        _orgs = read(run_dir, "orgs", ["tick", "id", "birth_tick", "start", "len", "energy_m", "ip_off",
                                       "birth_hash", *STATS], alive=pl.lit(True))
        _keep = ["id", "birth_tick", "end_tick", "alive", "len", "start", "birth_hash",
                 *[c for c in _dead.columns if c not in ("tick", "id", "age", "len", "start", "birth_hash",
                                                         "birth_tick", "alive")]]
        _dead = _dead.rename({"tick": "end_tick"}).select(_keep)
        _alive = (_orgs.filter(pl.col("tick") == _orgs["tick"].max()).rename({"tick": "end_tick"})
                  .join(_dead.select("id"), on="id", how="anti").select(_keep))
        _lives = pl.concat([_dead, _alive], how="vertical_relaxed")
        del _dead, _alive

        # Births: who made whom, of which kind (0 exact, 1 mutant, 2
        # stillborn), and the ring distance from the parent's body start to
        # the child's. Per-organism results go into numpy arrays indexed by
        # id and become new columns, which copies no other column (a join
        # would copy all 4 M rows each time).
        _b = read(run_dir, "births", ["child", "executor", "start", "endowment_m", "raw_hash", "parent_now_hash"],
                  kind=pl.when(pl.col("endowment_m") == 0).then(2)
                  .when(pl.col("raw_hash") == pl.col("parent_now_hash")).then(0).otherwise(1).cast(pl.Int8),
                  keep=["child", "executor", "kind", "start"])
        _ids = _lives["id"].to_numpy()
        _c, _e, _k = (_b[c].to_numpy() for c in ("child", "executor", "kind"))
        _size = int(max(_ids.max(), _c.max(initial=0))) + 1

        def _array(fill, idx=None, values=None):
            a = np.full(_size, fill, np.int64)
            if idx is not None:
                a[idx] = values
            return a

        _start = _array(0, _ids, _lives["start"].to_numpy())
        _dist = (_b["start"].to_numpy() - _start[_e]) % n
        _dist = np.minimum(_dist, n - _dist)
        _child_dist = _array(-1)
        np.maximum.at(_child_dist, _e, _dist)
        _children = np.bincount(_e, minlength=_size)
        _by_kind = [np.bincount(_e[_k == i], minlength=_size) for i in range(3)]
        # Furthest the IP was seen from the own body at a census: 0 inside
        # it, else the ring distance to the nearer end of the body.
        _r = _orgs.group_by("id").agg(d=pl.when(pl.col("ip_off") >= pl.col("len")).then(
            pl.min_horizontal(pl.col("ip_off") - pl.col("len") + 1, n - pl.col("ip_off"))).otherwise(0).max())

        # Generation depth, by list ranking: link each exact child to its
        # parent when the parent was itself born by an exact copy of the
        # same genome, then add up each chain by pointer doubling (one pass
        # per doubling, about 22 for a chain of 4 M).
        _gcode = _array(-1, _ids, _lives["birth_hash"].cast(pl.Categorical).to_physical().to_numpy())
        _exact_born = np.zeros(_size, bool)
        _exact_born[_c[_k == 0]] = True
        _same = (_k == 0) & (_gcode[_c] == _gcode[_e]) & _exact_born[_e]
        _link = _array(-1, _c[_same], _e[_same])
        _depth = _exact_born.astype(np.int64)
        while (_act := np.flatnonzero(_link >= 0)).size:
            _depth[_act] += _depth[_link[_act]]
            _link[_act] = _link[_link[_act]]

        _kinds = pl.Enum(["exact", "mutant", "stillborn"])
        _lives = _lives.with_columns(
            parent=_array(-1, _c, _e)[_ids],
            birth_kind=_array(-1, _c, _k)[_ids],
            children=_children[_ids],
            exact=_by_kind[0][_ids],
            mutant=_by_kind[1][_ids],
            stillborn=_by_kind[2][_ids],
            grandchildren=np.bincount(_e, weights=_children[_c], minlength=_size).astype(np.int64)[_ids],
            child_dist=_child_dist[_ids],
            ip_reach=_array(-1, _r["id"].to_numpy(), _r["d"].to_numpy())[_ids],
            depth=_depth[_ids],
            age=pl.col("end_tick") - pl.col("birth_tick"),
        ).with_columns(
            pl.col("parent", "child_dist", "ip_reach").replace(-1, None),
            birth_kind=pl.col("birth_kind").replace_strict({0: "exact", 1: "mutant", 2: "stillborn"}, default=None,
                                                           return_dtype=_kinds),
            live_children=pl.col("exact") + pl.col("mutant"),
            foreign=pl.col("exec_foreign") / pl.col("executed").clip(lower_bound=1),
        )
        del _b, _c, _e, _k, _dist, _link, _depth, _gcode, _exact_born, _same

        # Genomes with their harness class, and each organism's class (by a
        # narrow join, kept in the order of the organisms).
        genomes = read(run_dir, "genomes", ["raw_hash", "func_hash", "len", "first_tick", "first_id", "origin",
                                            "parent_hash", "bytes_hex"])
        _cls = read(run_dir, "classes", ["raw_hash", "class"])
        has_classes = _cls is not None
        genomes = (genomes.join(_cls, on="raw_hash", how="left") if has_classes else genomes).with_columns(
            pl.col("class").fill_null("unknown") if has_classes else pl.lit("unknown").alias("class"))
        lives = _lives.with_columns(
            _lives.select("birth_hash").join(genomes.select(birth_hash="raw_hash", **{"class": "class"}),
                                             on="birth_hash", how="left", maintain_order="left")["class"])
        # Census rows, for population and energy over time.
        census = _orgs.select("tick", "id", "birth_hash", "len", "energy", patch=pl.col("start") // ps)
        del _lives, _orgs
    return census, genomes, has_classes, lives, meta, n, ps, run_dir


@app.cell
def _(explain, meta):
    # Genome listings in pseudo-code (pseudo.py), read from a new
    # organism's start; searches use this run's locality.
    _locality = meta["config"].get("locality", 512)

    def read_genome(hexstr):
        return explain(bytes.fromhex(hexstr), locality=_locality)

    return (read_genome,)


@app.cell(hide_code=True)
def _(has_classes, lives, meta, mo, n, ps):
    _ext = meta.get("replay_from")
    _parts = [
        mo.hstack([
            mo.stat(str(meta["config"]["seed"]), label="seed"),
            mo.stat(f"{meta['ticks_run']:,}", label="ticks run", caption=f"census every {meta['census_every']:,}"),
            mo.stat(f"{lives.height:,}", label="organisms", caption=f"{lives['alive'].sum():,} alive at the end"),
            mo.stat(f"{lives['birth_hash'].n_unique():,}", label="genotypes", caption="distinct birth genomes"),
            mo.stat(f"{n:,}", label="world bytes", caption=f"{n // ps} patches of {ps}"),
        ], widths="equal"),
    ]
    if _ext:
        _parts.append(mo.md(f"A replay from tick {_ext['tick']:,}: organisms alive then have no birth row, "
                            "so no parent, and children born before it are not counted."))
    if not has_classes:
        _parts.append(mo.callout(mo.md(
            "No `classes.csv` for this run, so every class is `unknown` and no genotype passes the parasite "
            "rule. Classify it from `explore.py` (or `uv run report.py RUN_DIR --classify`)."), kind="warn"))
    mo.vstack(_parts)
    return


@app.cell
def _(mo):
    # Controls shared by both sets of tables.
    top_n = mo.ui.number(start=1, stop=50, step=1, value=5, label="rows per table")
    group = mo.ui.dropdown(
        options={"birth genome (raw_hash)": "raw_hash", "function (func_hash)": "func_hash"},
        value="birth genome (raw_hash)", label="group genotypes by",
    )
    mo.hstack([top_n, group], justify="start", gap=2)
    return group, top_n


@app.cell
def _(group, mo, run_dir):
    # The row picked in any table: ("organism", id) or ("genotype", key).
    # The cell reads the run and the grouping so that a new one clears the
    # pick. Self loops let the detail cell's own buttons move it.
    _ = (run_dir, group.value)
    get_pick, set_pick = mo.state(None, allow_self_loops=True)
    return get_pick, set_pick


@app.cell
def _(census, genomes, group, lives, pl, ps):
    # One row per genotype, grouped by the control above. `rep` is the raw
    # genome with the most carriers (itself under raw_hash grouping): its
    # bytes, length and class stand for the group.
    _key = group.value
    _gk = genomes.select(birth_hash="raw_hash", genotype=_key)

    def _of(df):
        """df with its genotype under the grouping, as one new column."""
        if _key == "raw_hash":
            return df.with_columns(genotype="birth_hash")
        return df.with_columns(df.select("birth_hash").join(_gk, on="birth_hash", how="left",
                                                            maintain_order="left")["genotype"])

    # Lazy, so each query reads only the columns it needs from the 4 M rows.
    _l = _of(lives).lazy()
    _rep = (
        _l.group_by("genotype", "birth_hash").len().sort("len", "birth_hash", descending=[True, False])
        .unique("genotype", keep="first").select("genotype", rep="birth_hash")
        .join(genomes.lazy().select(rep="raw_hash", len="len", **{"class": "class"}), on="rep", how="left")
        .collect()
    )
    _g = _l.group_by("genotype").agg(
        carriers=pl.len(),
        alive_end=pl.col("alive").sum(),
        first_seen=pl.col("birth_tick").min(),
        last_seen=pl.col("end_tick").max(),
        exact_copies=(pl.col("birth_kind") == "exact").sum(),
        children=pl.col("children").sum(),
        exact_children=pl.col("exact").sum(),
        mutants_made=pl.col("mutant").sum(),
        absorbed=pl.col("absorb_gain").sum(),
        mean_absorbed=pl.col("absorb_gain").mean(),
        mean_life=pl.col("age").mean(),
        depth=pl.col("depth").max(),
        patches_ever=(pl.col("start") // ps).n_unique(),
        foreign_total=pl.col("exec_foreign").sum(),
        foreign_med=(pl.col("exec_foreign") / pl.col("executed").clip(lower_bound=1))
        .filter(pl.col("children") >= 2).median(),
        **({"entered": pl.col("exec_by_others").sum()} if "exec_by_others" in lives.columns else {}),
    ).with_columns(
        span=pl.col("last_seen") - pl.col("first_seen"),
        exact_per_carrier=pl.col("exact_children") / pl.col("carriers"),
    ).collect()
    # At the censuses: carriers alive, the patches holding their bodies,
    # and the bytes their bodies fill.
    pop = _of(census).group_by("tick", "genotype").agg(
        count=pl.len(), patches=pl.col("patch").n_unique(), bytes=pl.col("len").sum())
    _peak = pop.group_by("genotype").agg(
        peak=pl.col("count").max(),
        peak_tick=pl.col("tick").get(pl.col("count").arg_max()),
        censuses=pl.len(),
        peak_patches=pl.col("patches").max(),
        peak_bytes=pl.col("bytes").max(),
    )
    # New genotypes founded: the first organism of a genotype (the earliest
    # genome of the group to appear, if that was at a birth) counts for the
    # genotype of its parent, when that is a different one.
    _first = (
        genomes.lazy().select("raw_hash", "first_tick", "first_id", "origin", genotype=_key)
        .sort("first_tick", "first_id").unique("genotype", keep="first")
        .filter(pl.col("origin") == "birth")
        .join(_l.select(first_id="id", parent="parent"), on="first_id")
        .join(_l.select(parent="id", parent_genotype="genotype"), on="parent")
        .filter(pl.col("parent_genotype") != pl.col("genotype"))
        .group_by(genotype="parent_genotype").agg(founded=pl.len())
        .collect()
    )
    geno = (
        _g.join(_rep, on="genotype", how="left").join(_peak, on="genotype", how="left")
        .join(_first, on="genotype", how="left")
        .with_columns(pl.col("peak", "censuses", "peak_patches", "peak_bytes", "founded").fill_null(0))
        .with_columns(parasite=~pl.col("class").is_in(["replicator", "unknown"]) & (pl.col("exact_copies") >= 2)
                      & (pl.col("depth") >= 5) & (pl.col("foreign_med") > 0.25))
    )
    return geno, pop


@app.cell
def _(lives, mo, pl, set_pick, top_n):
    # Organism leaderboards. Each table ranks every organism that ever
    # lived by one measure, ties broken by children and then by the
    # earlier id; the measure is the second column. A measure that is 0
    # for every organism (a counter this run's physics never moves) says
    # so instead of showing a table. The tables are kept in org_tables:
    # marimo holds UI elements weakly, and one with no reference left
    # would drop its clicks.
    org_tables = []
    _ctx = {"id": "organism", "birth_hash": "genotype", "class": "class", "len": "len", "birth_tick": "born",
            "age": "life", "alive": "alive", "children": "children", "exact": "exact"}

    def _board(col, title, note, where=None, unit=None):
        if col not in lives.columns:
            return None
        # Rank on the few columns the ranking reads, then fetch the rows of
        # the winners: a filter of all 4 M rows would copy every column.
        _keep = pl.col(col) > 0 if where is None else (pl.col(col) > 0) & where
        _ids = (lives.lazy().filter(_keep).select(*dict.fromkeys(["id", col, "children"]))
                .top_k(top_n.value, by=[col, "children", -pl.col("id")]).collect()["id"])
        _top = lives.filter(pl.col("id").is_in(_ids.implode())).sort(
            [col, "children", "id"], descending=[True, True, False])
        if _top.height == 0:
            return mo.md(f"**{title}**: none in this run.")
        _cols = [col] + [c for c in _ctx if c != col]
        _t = _top.select(_cols).rename({k: v for k, v in _ctx.items() if k != col} | {col: unit or col})
        if _top[col].dtype.is_float():
            _t = _t.with_columns(pl.col(unit or col).round(1))
        _t = _t.select("organism", pl.exclude("organism"))
        org_tables.append(mo.ui.table(
            _t, selection="single", page_size=top_n.value, show_column_summaries=False, show_download=False,
            on_change=lambda v: set_pick(("organism", int(v["organism"][0]))) if len(v) else None))
        return mo.vstack([mo.md(f"**{title}**: {note}"), org_tables[-1]])

    _par = (pl.col("foreign") > 0.25) & (pl.col("exact") > 0)
    _boards = {
        "Size": [
            _board("len", "Longest body", "bytes in the body (it never changes in a life)."),
        ],
        "Energy": [
            _board("absorb_gain", "Most energy absorbed", "total gained by `absorb` over its life, in energy units.",
                   unit="absorbed"),
            _board("max_energy", "Richest", "the most energy it held at one time.", unit="peak energy"),
            _board("endowed", "Most generous", "energy given to its children in total.", unit="given to children"),
        ],
        "Life": [
            _board("age", "Longest life", "ticks from birth to death, or to the end of the run for the living.",
                   unit="life"),
            _board("age", "Oldest alive at the end", "the living, by age.", where=pl.col("alive"), unit="life"),
            _board("executed", "Busiest", "instructions executed over its life."),
            _board("starved_ticks", "Hungriest", "ticks it paid upkeep but could not afford one instruction.",
                   unit="starved ticks"),
        ],
        "Children": [
            _board("children", "Most children", "every `divide` it executed, stillborn included."),
            _board("live_children", "Most live children", "exact plus mutant: born with energy.",
                   unit="live children"),
            _board("exact", "Most exact copies", "children equal to its body at `divide`: the same genotype.",
                   unit="exact copies"),
            _board("mutant", "Most mutant children", "children that differ from its body: a new genotype "
                   "(a copy error, or bytes copied from somewhere else).", unit="mutant children"),
            _board("stillborn", "Most stillborn children", "children born with no energy.", unit="stillborn children"),
            _board("grandchildren", "Most grandchildren", "children of its children, every kind."),
            _board("depth", "Deepest lineage", "the longest chain of exact copies of its genome ending at it.",
                   unit="generation depth"),
        ],
        "Distance": [
            _board("child_dist", "Farthest child", f"ring distance from its body start to a child's, in bytes "
                   "(bodies never move).", unit="child distance"),
            _board("ip_reach", "Farthest IP", "the most bytes outside its own body its IP was seen at, at a "
                   "census (an organism living between two censuses is never seen).", unit="IP distance"),
        ],
        "Parasites and hosts": [
            _board("exact", "Most successful parasites", "most exact copies among organisms that ran more than "
                   "25% of their instructions on other living organisms' bytes.", where=_par, unit="exact copies"),
            _board("exec_foreign", "Most foreign code run", "instructions it ran on another living organism's "
                   "body or pending region.", unit="foreign instructions"),
            _board("exec_unowned", "Most dead code run", "instructions it ran on free memory or debris (old code "
                   "left by the dead).", unit="unowned instructions"),
            _board("exec_by_others", "Most entered host", "instructions other organisms ran on its bytes "
                   "(recorded since E014).", unit="run by others"),
            _board("copies", "Most copying", "`copy` instructions executed.", unit="copies"),
            _board("reads_foreign", "Most foreign reads", "`load` or `copy` reads of another organism's byte.",
                   unit="foreign reads"),
            _board("gained_from_others", "Most energy taken from hosts", "under `--transfer-pct` (E010).",
                   unit="taken"),
            _board("paid_for_others", "Most energy paid for intruders", "under the owner-pays and transfer rules.",
                   unit="paid for others"),
            _board("overwritten", "Most overwritten", "writes by others that landed on its body or pending "
                   "region (only with `--no-protect`).", unit="overwritten"),
            _board("writes_foreign", "Most foreign writes", "its writes that landed on another organism (only "
                   "with `--no-protect`).", unit="foreign writes"),
            _board("cycles_taken", "Most execution budget taken", "under `--cycle-theft-pct` (E014).",
                   unit="budget taken"),
        ],
    }
    org_tabs = mo.ui.tabs({k: mo.vstack([b for b in v if b is not None], gap=1.5) for k, v in _boards.items()})
    mo.vstack([mo.md("## Organisms"), org_tabs])
    return org_tables, org_tabs


@app.cell
def _(geno, genomes, group, mo, pl, read_genome, set_pick, top_n):
    # Genotype leaderboards, grouped by the control above. Ties broken by
    # carriers and then by the earlier first appearance. `path`: the
    # pseudo-code route of the genome (or of the group's commonest raw
    # genome), read from a new organism's start. Tables kept in
    # geno_tables, as above.
    geno_tables = []
    _ctx = {"genotype": "genotype", "class": "class", "len": "len", "peak": "peak alive", "carriers": "carriers",
            "exact_copies": "exact copies", "first_seen": "first seen"}

    def _board(col, title, note, where=None, unit=None, min_carriers=1):
        if col not in geno.columns:
            return None
        _keep = (pl.col(col) > 0) & (pl.col("carriers") >= min_carriers)
        _top = (
            geno.lazy().filter(_keep if where is None else _keep & where)
            .top_k(top_n.value, by=[col, "carriers", -pl.col("first_seen")])
            .sort([col, "carriers", "first_seen"], descending=[True, True, False])
            .join(genomes.lazy().select(rep="raw_hash", hex="bytes_hex"), on="rep", how="left",
                  maintain_order="left")
            .collect()
        )
        if _top.height == 0:
            return mo.md(f"**{title}**: none in this run.")
        _cols = [col] + [c for c in _ctx if c != col]
        _t = _top.select(*_cols, path=pl.Series([read_genome(h).story for h in _top["hex"]], dtype=pl.Utf8))
        _t = _t.rename({k: v for k, v in _ctx.items() if k != col} | {col: unit or col})
        if _top[col].dtype.is_float():
            _t = _t.with_columns(pl.col(unit or col).round(2))
        _t = _t.select("genotype", pl.exclude("genotype"))
        geno_tables.append(mo.ui.table(
            _t, selection="single", page_size=top_n.value, show_column_summaries=False, show_download=False,
            on_change=lambda v: set_pick(("genotype", v["genotype"][0])) if len(v) else None))
        return mo.vstack([mo.md(f"**{title}**: {note}"), geno_tables[-1]])

    _rep = pl.col("exact_copies") >= 2
    _boards = {
        "Population": [
            _board("peak", "Biggest population at once", "carriers alive at one census (the tick is in the "
                   "detail below).", unit="peak alive"),
            _board("carriers", "Most organisms over the run", "every organism ever born with it, the founders and "
                   "injected copies included."),
            _board("alive_end", "Most alive at the end", "carriers alive at the last tick.", unit="alive at end"),
            _board("peak_bytes", "Most memory at once", "bytes its living bodies filled at one census.",
                   unit="peak bytes"),
        ],
        "Persistence": [
            _board("span", "Longest-lasting", "ticks from its first carrier's birth to its last carrier's death "
                   "(or the end), whether or not carriers lived the whole time.", unit="ticks"),
            _board("censuses", "Most censuses present", "censuses with at least one carrier alive.",
                   unit="censuses"),
            _board("depth", "Deepest lineage", "the longest unbroken chain of exact copies.",
                   unit="generation depth"),
        ],
        "Reproduction": [
            _board("exact_copies", "Most exact copies", "births that were exact copies of it."),
            _board("exact_per_carrier", "Best copiers", "exact children per carrier, among genotypes with at least "
                   "50 carriers.", unit="exact per carrier", min_carriers=50),
            _board("founded", "Most new genotypes founded", "genotypes whose first organism was born to one of its "
                   "carriers (a mutant child that started a genotype)."),
            _board("mutants_made", "Most mutant children", "children its carriers made that differ from the "
                   "parent's body.", unit="mutant children"),
        ],
        "Size": [
            _board("len", "Longest replicating genome", "bytes, among genotypes with at least 2 exact copies.",
                   where=_rep),
            _board("len", "Longest genome", "bytes, any genotype (most long ones are a single stillborn "
                   "or newborn mistake)."),
        ],
        "Energy": [
            _board("absorbed", "Most energy absorbed", "by all its carriers together, in energy units."),
            _board("mean_absorbed", "Best absorbers", "mean energy absorbed per carrier, among genotypes with at "
                   "least 50 carriers.", unit="absorbed per carrier", min_carriers=50),
            _board("mean_life", "Longest-lived", "mean carrier life in ticks, among genotypes with at least 50 "
                   "carriers.", unit="mean life", min_carriers=50),
        ],
        "Space": [
            _board("peak_patches", "Most widespread at once", "patches holding a living carrier's body start at "
                   "one census.", unit="patches"),
            _board("patches_ever", "Most widespread over the run", "patches any carrier's body started in.",
                   unit="patches"),
        ],
        "Parasites and hosts": [
            _board("exact_copies", "Most successful parasites", "exact copies, among genotypes that pass the parasite "
                   "rule at the top (not a replicator alone, 2 or more exact copies, depth 5 or more, dividing "
                   "carriers' median foreign share above 25%).", where=pl.col("parasite")),
            _board("foreign_total", "Most foreign code run", "instructions its carriers ran on other living "
                   "organisms' bytes.", unit="foreign instructions"),
            _board("entered", "Most entered hosts", "instructions other organisms ran on its carriers' bytes "
                   "(recorded since E014).", unit="run by others"),
        ],
    }
    geno_tabs = mo.ui.tabs({k: mo.vstack([b for b in v if b is not None], gap=1.5) for k, v in _boards.items()})
    mo.vstack([mo.md(f"## Genotypes, by {group.selected_key}"), geno_tabs])
    return geno_tables, geno_tabs


@app.cell
def _(BLUE, alt, census, geno, genomes, get_pick, group, lives, look, mo, pl, pop, read_genome, set_pick):
    # The picked organism or genotype. Buttons walk to an organism's parent
    # or genotype; a genotype's top carriers can be picked in their table.
    # detail_ui keeps those elements alive (see org_tables).
    detail_ui = []
    _pick = get_pick()
    mo.stop(_pick is None, mo.md("## Detail\n_Select a row in any table above to see it here._"))
    _what, _key = _pick
    _found = (lives if _what == "organism" else geno).filter(
        pl.col("id" if _what == "organism" else "genotype") == _key).height
    mo.stop(not _found, mo.md(f"## Detail\n_{_what.capitalize()} {_key} is not in this run or grouping: pick a "
                              "row again._"))
    _gen = {r["raw_hash"]: r for r in genomes.filter(pl.col("raw_hash").is_in(
        list(lives.filter(pl.col("id") == _key)["birth_hash"]) if _what == "organism"
        else list(geno.filter(pl.col("genotype") == _key)["rep"]))).iter_rows(named=True)}

    def _line(df, y, title, y_title):
        return look(alt.Chart(df).mark_line(color=BLUE, strokeWidth=2, point=alt.OverlayMarkDef(color=BLUE, size=30))
                    .encode(x=alt.X("tick:Q", title="tick", scale=alt.Scale(zero=False)),
                            y=alt.Y(f"{y}:Q", title=y_title),
                            tooltip=[alt.Tooltip("tick:Q", format=","), alt.Tooltip(f"{y}:Q", format=",.1f")])
                    .properties(width="container", height=180, title=title))

    if _what == "organism":
        _r = lives.filter(pl.col("id") == _key).row(0, named=True)
        _g = _gen[_r["birth_hash"]]
        _gkey = _r["birth_hash"] if group.value == "raw_hash" else _g["func_hash"]
        _born = (f"born at tick {_r['birth_tick']:,} to organism {_r['parent']} ({_r['birth_kind']} birth)"
                 if _r["parent"] is not None else
                 f"no birth row (a founder, an injected copy, or alive at a replay's start); first tick "
                 f"{_r['birth_tick']:,}")
        _end = (f"alive at the end (tick {_r['end_tick']:,}), age {_r['age']:,}" if _r["alive"]
                else f"died at tick {_r['end_tick']:,}, age {_r['age']:,}")
        detail_ui = [
            mo.ui.button(label="parent", disabled=_r["parent"] is None,
                         on_click=lambda _, p=_r["parent"]: set_pick(("organism", int(p)))),
            mo.ui.button(label="its genotype", on_click=lambda _, g=_gkey: set_pick(("genotype", g))),
        ]
        _e = census.filter(pl.col("id") == _key).select("tick", "energy")
        _fmt = lambda v, f=",": "-" if v is None else format(v, f)
        _tiles = mo.hstack([
            mo.stat(f"{_r['children']:,}", label="children",
                    caption=f"{_r['exact']:,} exact, {_r['mutant']:,} mutant, {_r['stillborn']:,} stillborn"),
            mo.stat(f"{_r['grandchildren']:,}", label="grandchildren"),
            mo.stat(f"{_r['absorb_gain']:,.1f}", label="energy absorbed", caption=f"peak {_r['max_energy']:,.1f}"),
            mo.stat(f"{_r['executed']:,}", label="instructions", caption=f"{_r['foreign']:.0%} on others' bytes"),
            mo.stat(f"{_r['depth']:,}", label="generation depth"),
            mo.stat(_fmt(_r["child_dist"]), label="farthest child", caption=f"IP seen {_fmt(_r['ip_reach'])} "
                    "bytes out"),
        ], widths="equal")
        _view = [
            mo.md(f"## Organism {_key}\n{_born}; {_end}. Body: {_r['len']} bytes at address {_r['start']:,}. "
                  f"Birth genome `{_r['birth_hash']}` ({_r['class']})."),
            mo.hstack(detail_ui, justify="start", gap=1),
            _tiles,
        ]
        if _e.height >= 2:
            _view.append(_line(_e, "energy", f"Organism {_key}: energy at each census", "energy (units)"))
        _view.append(mo.md(f"**Birth genome** `{_r['birth_hash']}`\n```\n{read_genome(_g['bytes_hex']).text()}\n```"))
        _out = mo.vstack(_view)
    else:
        _r = geno.filter(pl.col("genotype") == _key).row(0, named=True)
        _g = _gen[_r["rep"]]
        _members = (lives.filter(pl.col("birth_hash") == _key) if group.value == "raw_hash" else
                    lives.join(genomes.filter(pl.col("func_hash") == _key).select(birth_hash="raw_hash"),
                               on="birth_hash"))
        detail_ui = [mo.ui.table(
            _members.top_k(10, by=["exact", "children", -pl.col("id")]).sort(
                ["exact", "children", "id"], descending=[True, True, False]).select(
                organism="id", exact="exact", children="children", life="age", born="birth_tick",
                alive="alive", absorbed=pl.col("absorb_gain").round(1)),
            selection="single", page_size=10, show_column_summaries=False, show_download=False,
            on_change=lambda v: set_pick(("organism", int(v["organism"][0]))) if len(v) else None,
            label="Its 10 carriers with the most exact copies: select one to see it")]
        _p = pop.filter(pl.col("genotype") == _key).sort("tick")
        _rep_note = "" if group.value == "raw_hash" else (
            f" Shown: its commonest raw genome `{_r['rep']}`, of "
            f"{genomes.filter(pl.col('func_hash') == _key).height:,} raw genomes with this `func_hash`.")
        _tiles = mo.hstack([
            mo.stat(f"{_r['carriers']:,}", label="carriers", caption=f"{_r['alive_end']:,} alive at the end"),
            mo.stat(f"{_r['peak']:,}", label="peak alive", caption=f"at tick {_r['peak_tick']:,}"
                    if _r["peak_tick"] is not None else "never at a census"),
            mo.stat(f"{_r['exact_copies']:,}", label="exact copies",
                    caption=f"{_r['exact_per_carrier']:.2f} exact children per carrier"),
            mo.stat(f"{_r['depth']:,}", label="generation depth"),
            mo.stat(f"{_r['founded']:,}", label="genotypes founded"),
            mo.stat("-" if _r["foreign_med"] is None else f"{_r['foreign_med']:.0%}", label="foreign share",
                    caption="median, carriers with 2+ children"),
        ], widths="equal")
        _view = [
            mo.md(f"## Genotype `{_key}`\n{_r['class']}, {_r['len']} bytes, first born at tick "
                  f"{_r['first_seen']:,}, last carrier gone at {_r['last_seen']:,}. Origin of the genome: "
                  f"{_g['origin']}, parent genome `{_g['parent_hash']}`."
                  + (" **Passes the parasite rule.**" if _r["parasite"] else "") + _rep_note),
            _tiles,
        ]
        if _p.height >= 2:
            _view.append(_line(_p, "count", f"Carriers of {_key} alive at each census", "organisms"))
        _view += [detail_ui[0], mo.md(f"**Genome** `{_r['rep']}`\n```\n{read_genome(_g['bytes_hex']).text()}\n```")]
        _out = mo.vstack(_view)
    _out
    return (detail_ui,)


@app.cell
def _(lives, pl):
    # Scratch space. `lives` has one row per organism (lifetime counters in
    # energy units, children by kind, depth, distances); `geno` one per
    # genotype under the current grouping; `pop` carriers alive per census
    # and genotype; `census` every census row; `genomes` every genome with
    # its class. Example: organisms that made exact copies while running
    # mostly other organisms' code.
    lives.filter(pl.col("foreign") > 0.5, pl.col("exact") > 0).sort("exact", descending=True).head(10)
    return


if __name__ == "__main__":
    app.run()
