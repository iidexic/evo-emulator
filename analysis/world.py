import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="evo world viewer")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # evo world viewer

    The ring of memory itself, read from the world snapshots of one run
    directory (`world.bin`, one per census tick, recorded by every
    `evo-core --out DIR` run since 2026-10-07). `explore.py` follows
    organisms; this notebook follows bytes: who owns each address, what
    dead code sits in free memory, and where each organism's instruction
    pointer (IP) is running.

    ```
    cd analysis
    uv run marimo edit world.py
    ```

    Every address at a snapshot falls in exactly one of five kinds:

    - **living body**: the bytes of a living organism (start and len in `orgs.csv`).
    - **pending region**: memory an organism has claimed with `alloc` for a
      child it has not divided off yet. Owned, but not part of any body.
    - **dead body, intact**: unowned memory that starts where an organism
      died and still holds the exact bytes of a known genome of that
      length (any raw hash in `genomes.csv`). Code a stray IP could run as
      written. A 1- or 2-byte dead body matches almost by chance, so the
      short ones say little.
    - **debris**: other bytes of dead bodies that have not yet decayed back to free.
    - **free**: everything else. Free memory keeps its bytes (most of it is
      old code), it is only unowned.

    An **off-body IP** is an organism whose IP was outside its own body at
    the census: it was running another body's code, its own unfinished
    child, or dead code.

    Click anything on the world map, or a row in the two tables at the end,
    to load that address into the inspector.
    """)
    return


@app.cell
def _():
    # Libraries, plus the run loader (evo_run) and the palette shared with
    # report.py and explore.py.
    import functools
    import subprocess

    import altair as alt
    import marimo as mo
    import numpy as np
    import polars as pl

    from evo_run import ROOT, binary, load, world
    from report import CLASS_COLOR, GRAY_LIGHT, GRID, INK, INK_2, SEQ_STEPS, SURFACE, class_order

    # A world map has a few thousand segments; more than altair's default row limit.
    alt.data_transformers.disable_max_rows()
    return (
        CLASS_COLOR,
        GRAY_LIGHT,
        GRID,
        INK,
        INK_2,
        ROOT,
        SEQ_STEPS,
        SURFACE,
        alt,
        binary,
        class_order,
        functools,
        load,
        mo,
        np,
        pl,
        subprocess,
        world,
    )


@app.cell
def _(CLASS_COLOR, GRAY_LIGHT, GRID, INK, INK_2, SEQ_STEPS, SURFACE, alt, binary, class_order, functools, subprocess):
    # Small helpers used by the cells below.

    # The five kinds of address, in stacking order (alive at the bottom,
    # decayed at the top). Bodies in blues, living dark and dead light;
    # the rest in the grays the world map uses for them.
    KINDS = ["living body", "pending region", "dead body, intact", "debris", "free"]
    KIND_COLOR = dict(zip(KINDS, [SEQ_STEPS[6], INK_2, SEQ_STEPS[2], "#d9d8d3", "#f1f0ec"]))
    # State letters in tables: one per byte, from the snapshot's state byte.
    STATE_LETTER = ".do"  # 0 free, 1 debris, 2 owned

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

    def class_color(names):
        """Color scale for harness classes; an unexpected label is drawn gray."""
        dom = class_order(names)
        return alt.Scale(domain=dom, range=[CLASS_COLOR.get(k, GRAY_LIGHT) for k in dom])

    _exe = functools.cache(binary)

    @functools.cache
    def dis(hexstr):
        """Decode bytes (as hex) from their first byte: a tuple of
        (offset, size, instruction). Runs `evo-core --disasm`, building it on
        first use; cached because the same bytes recur at an address across
        many snapshots. `lit` is the only two-byte instruction."""
        if not hexstr:
            return ()
        out = subprocess.run([str(_exe()), "--disasm", hexstr], capture_output=True, text=True, check=True).stdout
        ins, off = [], 0
        for text in out.strip().split(" ; "):
            size = 2 if text.startswith("lit ") else 1
            ins.append((off, size, text))
            off += size
        return tuple(ins)

    return KINDS, KIND_COLOR, STATE_LETTER, class_color, dis, look


@app.cell
def _(ROOT, mo):
    # Only runs that carry world snapshots.
    run_dirs = {
        p.parent.relative_to(ROOT / "runs").as_posix(): p.parent
        for p in sorted((ROOT / "runs").rglob("world.bin"))
    }
    mo.stop(not run_dirs, mo.md(
        "No run under `runs/` has a `world.bin`. Every run recorded with `evo-core --out DIR` "
        "since 2026-10-07 writes one."))
    picker = mo.ui.dropdown(options=list(run_dirs), value=next(iter(run_dirs)), searchable=True, label="run")
    picker
    return picker, run_dirs


@app.cell
def _(load, picker, pl, run_dirs, world):
    run_dir = run_dirs[picker.value]
    run = load(run_dir)
    snaps = world(run_dir)  # tick -> World(bytes, state)
    snap_ticks = sorted(snaps)
    n = run.meta["config"]["world_size"]
    ps = run.meta["config"]["patch_size"]
    # Census rows with the class of the current body, and each IP as an
    # absolute address. ip_off is IP minus body start on the ring, so an IP
    # at or past the body's length is outside the body.
    orgs = run.class_of(run.orgs, "now_hash").with_columns(
        ip=(pl.col("start") + pl.col("ip_off")) % n,
        off_body=pl.col("ip_off") >= pl.col("len"),
    )
    # Every genome's bytes, to recognise intact dead bodies, and every
    # genome's harness class.
    genome_of = {bytes.fromhex(h): r for h, r in zip(run.genomes["bytes_hex"], run.genomes["raw_hash"])}
    class_of_hash = {} if run.classes is None else dict(zip(run.classes["raw_hash"], run.classes["class"]))
    return class_of_hash, genome_of, n, orgs, ps, run, snap_ticks, snaps


@app.cell
def _(KINDS, class_of_hash, functools, genome_of, n, np, orgs, pl, run, snaps):
    # The classifier for one snapshot. Everything below that needs to know
    # what an address is calls layout(tick).

    _deaths = run.deaths.select("tick", "id", "start", "len").sort("tick")
    _death_ticks = _deaths["tick"].to_numpy()

    def spans(starts, lens):
        """Expand ring spans [start, start + len) into one (span index,
        address) pair per byte, as two arrays."""
        starts = np.asarray(starts, np.int64)
        lens = np.asarray(lens, np.int64)
        span = np.repeat(np.arange(starts.size), lens)
        off = np.arange(span.size) - np.repeat(np.cumsum(lens) - lens, lens)
        return span, (starts[span] + off) % n

    @functools.lru_cache(maxsize=16)
    def layout(tick):
        """Classify every address at a snapshot tick. Returns
        - kind: index into KINDS per address,
        - who: per address, id of the living organism (living body) or the
          dead one (dead body, intact), else -1,
        - living: orgs.csv rows at this tick (with class),
        - dead: the intact dead bodies (tick, id, start, len, raw_hash, class).
        Cached; treat the arrays as read-only."""
        w = snaps[tick]
        living = orgs.filter(pl.col("tick") == tick)
        who = np.full(n, -1, np.int64)
        span, addr = spans(living["start"].to_numpy(), living["len"].to_numpy())
        who[addr] = living["id"].to_numpy()[span]
        # Owned bytes outside every body are pending regions; unowned bytes
        # start as free or debris from the state byte.
        kind = np.where(w.state == 2, np.where(who >= 0, 0, 1), np.where(w.state == 1, 3, 4)).astype(np.int8)

        # Candidate dead bodies: the latest death at each start address up
        # to this tick. Intact if no byte of the span is owned now and its
        # bytes are a known genome. The memory is doubled so a span that
        # wraps past the end reads as one slice.
        c = _deaths.head(int(np.searchsorted(_death_ticks, tick, side="right")))
        c = c.unique("start", keep="last").sort("tick")
        s, ln = c["start"].to_numpy(), c["len"].to_numpy()
        owned = np.concatenate([[0], np.cumsum(np.tile(w.state == 2, 2))])
        raw = w.bytes.tobytes() * 2
        hit, hashes = [], []
        for j in np.flatnonzero(owned[s + ln] == owned[s]):
            h = genome_of.get(raw[s[j]:s[j] + ln[j]])
            if h is not None:
                hit.append(j)
                hashes.append(h)
        dead = (
            c.with_row_index("_j").filter(pl.col("_j").is_in(hit)).drop("_j")
            .with_columns(raw_hash=pl.Series(hashes, dtype=pl.Utf8))
            .with_columns(**{"class": pl.col("raw_hash").replace_strict(class_of_hash, default="unknown", return_dtype=pl.Utf8)})
        )
        span, addr = spans(dead["start"].to_numpy(), dead["len"].to_numpy())
        kind[addr] = KINDS.index("dead body, intact")
        who[addr] = dead["id"].to_numpy()[span]
        return kind, who, living, dead

    return (layout,)


@app.cell
def _(KINDS, layout, mo, np, pl, snap_ticks):
    # One pass over every snapshot (a few seconds for 100 snapshots of
    # 64 KB): bytes of each kind, and for every organism whose IP was
    # outside its own body, the kind of address the IP was at.
    _rows, _ob = [], []
    for _t in mo.status.progress_bar(snap_ticks, title="Reading world snapshots"):
        _kind, _who, _living, _dead = layout(_t)
        _rows.append([_t, *np.bincount(_kind, minlength=len(KINDS)).tolist(), _living.height])
        _o = _living.filter(pl.col("off_body"))
        _ip = _o["ip"].to_numpy()
        _cls = dict(zip(_living["id"], _living["class"])) | dict(zip(_dead["id"], _dead["class"]))
        _tw = _who[_ip].tolist()
        _ob.append(_o.select("tick", "id", "class", "start", "len", "ip", "op_at_ip").with_columns(
            target=pl.Series([KINDS[k] for k in _kind[_ip]], dtype=pl.Utf8),
            target_id=pl.Series(_tw, dtype=pl.Int64),
            target_class=pl.Series([_cls.get(i, "") for i in _tw], dtype=pl.Utf8),
        ))
    composition = pl.DataFrame(_rows, schema=["tick", *KINDS, "organisms"], orient="row")
    offbody = pl.concat(_ob)
    return composition, offbody


@app.cell(hide_code=True)
def _(composition, mo, n, offbody, ps, run, snap_ticks):
    _m = run.meta
    _dirty = " with uncommitted changes" if _m["git_dirty"] else ""
    _intact = composition["dead body, intact"].mean() / n
    _parts = [
        mo.hstack([
            mo.stat(str(_m["config"]["seed"]), label="seed"),
            mo.stat(f"{len(snap_ticks)}", label="snapshots", caption=f"every {_m['census_every']} ticks"),
            mo.stat(f"{n:,}", label="world bytes", caption=f"{n // ps} patches of {ps}"),
            mo.stat(f"{_intact:.0%}", label="intact dead bodies", caption="share of memory, mean over snapshots"),
            mo.stat(f"{offbody.height / max(composition['organisms'].sum(), 1):.0%}", label="off-body IPs",
                    caption="share of census rows"),
        ], widths="equal"),
        mo.md(f"Built from commit `{_m['git_commit']}`{_dirty}."),
    ]
    if run.classes is None:
        _parts.append(mo.callout(mo.md(
            "No `classes.csv` for this run, so every body's class is `unknown`. "
            "Classify it from `explore.py` (or `uv run report.py RUN_DIR --classify`)."), kind="warn"))
    mo.vstack(_parts)
    return


@app.cell
def _(mo, snap_ticks):
    # The snapshot every per-tick view below shows.
    tick_pick = mo.ui.slider(
        steps=snap_ticks, value=snap_ticks[len(snap_ticks) // 2],
        show_value=True, full_width=True, label="snapshot tick",
    )
    tick_pick
    return (tick_pick,)


@app.cell
def _(INK, INK_2, KINDS, KIND_COLOR, alt, composition, look, mo, offbody, pl, tick_pick):
    # Memory by kind at every snapshot, and where off-body IPs were. The
    # dashed line marks the snapshot picked above; hover for the counts.
    _rank = {k: i for i, k in enumerate(KINDS)}
    _scale = alt.Scale(domain=KINDS, range=[KIND_COLOR[k] for k in KINDS])
    _now = alt.Chart(pl.DataFrame({"tick": [tick_pick.value]})).mark_rule(color=INK, strokeDash=[4, 3]).encode(x="tick:Q")

    def _stacked(wide, cols, y_title, title, extra=()):
        _long = wide.unpivot(index="tick", on=cols, variable_name="kind", value_name="v").with_columns(
            rank=pl.col("kind").replace_strict(_rank))
        _area = alt.Chart(_long).mark_area().encode(
            x=alt.X("tick:Q", title="tick", scale=alt.Scale(nice=False)),
            y=alt.Y("v:Q", stack=True, title=y_title),
            color=alt.Color("kind:N", scale=_scale, title=None),
            order=alt.Order("rank:Q"),
        )
        _hover = alt.selection_point(nearest=True, on="pointerover", fields=["tick"], empty=False, clear="pointerout")
        _rule = alt.Chart(wide).mark_rule(color=INK_2).encode(
            x="tick:Q",
            opacity=alt.condition(_hover, alt.value(0.6), alt.value(0)),
            tooltip=[alt.Tooltip("tick:Q", format=",")] + [alt.Tooltip(f"{c}:Q", format=",") for c in (*cols, *extra)],
        ).add_params(_hover)
        return look((_area + _rule + _now).properties(width="container", height=200, title=title))

    _mem = _stacked(composition, KINDS, "bytes", "Memory by kind at each snapshot")
    # Off-body IPs per snapshot by the kind of address the IP was at.
    _ob = (
        offbody.group_by("tick", "target").len()
        .pivot(on="target", index="tick", values="len")
        .join(composition.select("tick", "organisms"), on="tick", how="right")
        .fill_null(0).sort("tick")
    )
    _cols = [k for k in KINDS if k in _ob.columns]
    _ips = _stacked(_ob, _cols, "organisms", "Organisms whose IP was outside their own body, by where it was",
                    extra=("organisms",))
    mo.vstack([mo.md("## Memory over time"), _mem, _ips])
    return


@app.cell
def _(CLASS_COLOR, GRAY_LIGHT, INK, KINDS, KIND_COLOR, alt, class_order, layout, look, mo, n, np, pl, ps, tick_pick):
    # The world at the picked snapshot, as rows of memory read left to
    # right, top to bottom. With up to 160 rows, one row is one patch;
    # bigger worlds put several patches in a row. Each run of addresses
    # with the same kind and owner is one block; bodies are colored by the
    # harness class of their bytes, intact dead bodies faded. Black ticks
    # are off-body IPs. Click a block or a tick to inspect it.
    _t = tick_pick.value
    _kind, _who, _living, _dead = layout(_t)
    _row = ps
    while n // _row > 160:
        _row *= 2

    _addr = np.arange(n)
    _cut = np.flatnonzero((np.diff(_kind) != 0) | (np.diff(_who) != 0) | (_addr[1:] % _row == 0)) + 1
    _a0 = np.concatenate([[0], _cut])
    _a1 = np.concatenate([_cut, [n]])
    _owners = pl.concat([
        _living.select("id", "class", raw_hash="now_hash", energy="energy"),
        _dead.select("id", "class", "raw_hash", energy=pl.lit(None, dtype=pl.Float64)),
    ])
    _seg = (
        pl.DataFrame({"addr": _a0, "end": _a1, "k": _kind[_a0], "id": _who[_a0]})
        .with_columns(kind=pl.col("k").replace_strict(dict(enumerate(KINDS)), return_dtype=pl.Utf8))
        .join(_owners, on="id", how="left")
        .with_columns(label=pl.coalesce("class", "kind"), span=pl.min_horizontal(pl.col("end") - pl.col("addr"), 128))
    )
    # Off-body IPs as one-byte marks, several organisms at one address in one mark.
    _ips = (
        _living.filter(pl.col("off_body")).group_by("ip")
        .agg(ids=pl.col("id").sort().cast(pl.Utf8).str.join(", "), orgs=pl.len())
        .select(addr="ip", end=pl.col("ip") + 1, kind=pl.lit("off-body IP"), label=pl.lit("off-body IP"),
                ids="ids", orgs="orgs", span=pl.lit(24))
    )
    _data = pl.concat([_seg, _ips], how="diagonal_relaxed").with_columns(
        row=pl.col("addr") // _row, x0=pl.col("addr") % _row,
        x1=pl.col("addr") % _row + pl.col("end") - pl.col("addr"),
        len=pl.col("end") - pl.col("addr"),
    ).with_columns(row1=pl.col("row") + 1)

    _classes = class_order(_owners["class"].unique().to_list())
    _color = alt.Scale(
        domain=_classes + ["pending region", "debris", "free", "off-body IP"],
        range=[CLASS_COLOR.get(k, GRAY_LIGHT) for k in _classes]
        + [KIND_COLOR["pending region"], KIND_COLOR["debris"], KIND_COLOR["free"], INK],
    )
    _pick = alt.selection_point(fields=["addr"], on="click", empty=False)
    _rows = -(-n // _row)
    _map = alt.Chart(_data).mark_rect().encode(
        x=alt.X("x0:Q", scale=alt.Scale(domain=[0, _row], nice=False),
                axis=alt.Axis(values=list(range(0, _row + 1, max(ps // 4, 1))), format="d"),
                title=f"offset in the row (address = row × {_row} + offset); patches are {ps} bytes"),
        x2="x1:Q",
        y=alt.Y("row:Q", scale=alt.Scale(domain=[0, _rows], reverse=True, nice=False), title="row"),
        y2="row1:Q",
        color=alt.Color("label:N", scale=_color, title="class of the bytes, or kind"),
        opacity=alt.condition("datum.kind == 'dead body, intact'", alt.value(0.4), alt.value(1)),
        stroke=alt.condition(_pick, alt.value(INK), alt.value(None)),
        strokeWidth=alt.condition(_pick, alt.value(1.5), alt.value(0)),
        tooltip=[
            "kind:N", alt.Tooltip("class:N"), alt.Tooltip("id:Q", title="organism"),
            alt.Tooltip("addr:Q", title="address", format="d"), "len:Q",
            alt.Tooltip("raw_hash:N", title="genome"), alt.Tooltip("energy:Q", format=".1f"),
            alt.Tooltip("ids:N", title="IP of"),
        ],
    ).add_params(_pick).properties(
        width="container", height=max(200, 5 * _rows),
        title=f"World at tick {_t:,}: faded blocks are intact dead bodies, black ticks off-body IPs",
    )
    world_map = mo.ui.altair_chart(look(_map), legend_selection=False)
    mo.vstack([mo.md("## World map"), world_map])
    return (world_map,)


@app.cell
def _(mo):
    # The address span the inspector shows: (start address, length). Set
    # by the address inputs, a click on the map, or a row in the tables at
    # the end.
    get_span, set_span = mo.state((0, 32))
    return get_span, set_span


@app.cell
def _(set_span, world_map):
    _sel = world_map.value
    if len(_sel) > 0:
        _r = _sel.row(0, named=True)
        set_span((int(_r["addr"]), int(_r["span"])))
    return


@app.cell
def _(get_span, mo, n, set_span):
    addr_in = mo.ui.number(
        start=0, stop=n - 1, step=1, value=get_span()[0] % n, label="address",
        on_change=lambda v: set_span((int(v), get_span()[1])),
    )
    len_in = mo.ui.number(
        start=1, stop=256, step=1, value=get_span()[1], label="bytes",
        on_change=lambda v: set_span((get_span()[0], int(v))),
    )
    mo.vstack([mo.md("## Inspector"), mo.hstack([addr_in, len_in], justify="start", gap=1)])
    return


@app.cell
def _(STATE_LETTER, dis, get_span, layout, mo, n, np, orgs, pl, snaps, tick_pick):
    # The span at the picked snapshot, decoded from its first byte, one row
    # per instruction. Decoding is linear from the start you give, so a
    # start in the middle of a `lit` reads its operand as an instruction.
    _t = tick_pick.value
    _a, _len = get_span()
    _a %= n
    _w = snaps[_t]
    _kind, _who, _living, _dead = layout(_t)
    _idx = (_a + np.arange(_len)) % n
    _cls = dict(zip(_living["id"], _living["class"])) | dict(zip(_dead["id"], _dead["class"]))

    def _owner(addr):
        k, i = int(_kind[addr]), int(_who[addr])
        if k == 0:
            return f"organism {i} ({_cls[i]})"
        if k == 2:
            return f"dead organism {i} ({_cls[i]}), intact"
        return ["", "pending region", "", "debris", "free"][k]

    # Every IP at this tick, on its own body or not.
    _here = (
        orgs.filter(pl.col("tick") == _t)
        .with_columns(rel=(pl.col("ip") - _a + n) % n)
        .filter(pl.col("rel") < _len)
        .with_columns(who=pl.when(pl.col("off_body"))
                      .then(pl.col("id").cast(pl.Utf8))
                      .otherwise(pl.col("id").cast(pl.Utf8) + " (own)"))
        .group_by("rel").agg(pl.col("who").sort().str.join(", "))
    )
    _ips = dict(zip(_here["rel"], _here["who"]))
    _rows = []
    for _off, _size, _text in dis(_w.bytes[_idx].tobytes().hex()):
        if _off >= _len:
            break
        _b = _idx[_off:_off + _size]
        _rows.append({
            "address": int(_b[0]),
            "bytes": _w.bytes[_b].tobytes().hex(" "),
            "instruction": _text,
            "state": "".join(STATE_LETTER[s] for s in _w.state[_b]),
            "owner": _owner(_b[0]),
            "IP of": ", ".join(_ips[o] for o in range(_off, _off + _size) if o in _ips),
        })
    mo.vstack([
        mo.md(f"Addresses {_a:,} to {(_a + _len - 1) % n:,} at tick {_t:,}. State per byte: "
              "`.` free, `d` debris, `o` owned. **IP of**: organisms whose IP is on that "
              "instruction; `(own)` means inside its own body."),
        mo.ui.table(pl.DataFrame(_rows), selection=None, page_size=64, show_column_summaries=False),
    ])
    return


@app.cell
def _(STATE_LETTER, dis, get_span, mo, n, np, orgs, pl, snap_ticks, snaps):
    # The same span at every snapshot: when its bytes changed, whether it
    # was owned, and whose IPs were in it. This is how E005's trampoline
    # (bytes 17 to 20 of seed 1) was read.
    _a, _len = get_span()
    _a %= n
    _idx = (_a + np.arange(_len)) % n
    _ips = (
        orgs.with_columns(rel=(pl.col("ip") - _a + n) % n)
        .filter(pl.col("rel") < _len)
        .group_by("tick")
        .agg(ips_here=pl.len(), off_body=pl.col("off_body").sum(),
             ids=pl.col("id").sort().head(8).cast(pl.Utf8).str.join(", "))
    )
    _rows, _prev = [], None
    for _t in snap_ticks:
        _w = snaps[_t]
        _hex = _w.bytes[_idx].tobytes().hex()
        _rows.append({
            "tick": _t,
            "changed": _prev is not None and _hex != _prev,
            "state": "".join(STATE_LETTER[s] for s in _w.state[_idx]),
            "code": " ; ".join(t for o, _, t in dis(_hex) if o < _len),
            "bytes": _hex,
        })
        _prev = _hex
    _watch = (
        pl.DataFrame(_rows).join(_ips, on="tick", how="left")
        .with_columns(pl.col("ips_here", "off_body").fill_null(0))
        .select("tick", "changed", "ips_here", "off_body", "ids", "state", "code", "bytes")
    )
    mo.vstack([
        mo.md(f"### Addresses {_a:,} to {(_a + _len - 1) % n:,} at every snapshot\n"
              "`ips_here`: IPs anywhere in the span (`off_body` of them from outside their own body; "
              "`ids`: the first 8). `changed`: bytes differ from the previous snapshot."),
        mo.ui.table(_watch, selection=None, page_size=20, show_column_summaries=False),
    ])
    return


@app.cell
def _(mo, offbody, tick_pick):
    # Who was running outside their own body at the picked snapshot, and
    # what was at the IP. target_id is the organism whose body (living or
    # dead) holds the IP.
    off_table = mo.ui.table(
        offbody.filter(tick=tick_pick.value).drop("tick").sort("target", "ip"),
        selection="single", page_size=15, show_column_summaries=False,
        label=f"Off-body IPs at tick {tick_pick.value:,}: select a row to inspect 24 bytes from its IP",
    )
    mo.vstack([mo.md("## Off-body IPs"), off_table])
    return (off_table,)


@app.cell
def _(off_table, set_span):
    if len(off_table.value) > 0:
        set_span((int(off_table.value["ip"][0]), 24))
    return


@app.cell
def _(mo, offbody, pl):
    # Addresses where the most different organisms had an off-body IP,
    # over all snapshots. Dead code reached by an absolute jump (`jmpa`,
    # like E005's trampoline at address 17) is shared by every carrier of
    # the lineage, so it ranks high here; relative jumps land at a
    # different address for each body and do not. Ranking by census rows
    # instead would put a few long-lived organisms stuck in a neighbour's
    # loop on top. A census catches an IP only where it is at that tick,
    # so code passed through in a few instructions is undercounted.
    hot_table = mo.ui.table(
        offbody.group_by("ip")
        .agg(
            rows=pl.len(), organisms=pl.col("id").n_unique(),
            first_tick=pl.col("tick").min(), last_tick=pl.col("tick").max(),
            target=pl.col("target").mode().first(), op=pl.col("op_at_ip").mode().first(),
            ip_owner_classes=pl.col("class").unique().sort().str.join(", "),
        )
        .sort("organisms", "rows", descending=True)
        .head(50),
        selection="single", page_size=10, show_column_summaries=False,
        label="Off-body IP hot spots over all snapshots (organisms: distinct organisms with an IP "
              "there; rows: census rows; target: commonest kind of address there). Select a row to inspect it",
    )
    mo.vstack([mo.md("## Hot spots"), hot_table])
    return (hot_table,)


@app.cell
def _(hot_table, set_span):
    if len(hot_table.value) > 0:
        set_span((int(hot_table.value["ip"][0]), 24))
    return


@app.cell
def _(layout, tick_pick):
    # Scratch space. layout(tick) gives (kind, who, living, dead) for any
    # snapshot tick; `snaps[tick].bytes` and `.state` are the raw arrays;
    # `offbody` and `composition` are the per-snapshot tables above; `run`
    # has every CSV as a polars frame. Example: intact dead bodies at the
    # picked snapshot, by class.
    layout(tick_pick.value)[3].group_by("class").len().sort("len", descending=True)
    return


if __name__ == "__main__":
    app.run()
