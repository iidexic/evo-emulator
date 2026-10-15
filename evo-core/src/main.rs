//! CLI: run a seeded world and print a census.
//!
//! evo-core [--ticks N] [--seed S] [--report N] [--log PATH]
//!          [--ancestor std|tierra] [--k K] [--e E]
//!          [--no-protect] [--p P] [--world N] [--patch N]
//!          [--alloc-far | --alloc-near] [--absorb-prop | --absorb-fixed]
//!          [--legacy-pending-range]
//!          [--locality N] [--out DIR] [--census N] [--sun N] [--rot P]
//!          [--self-owner] [--charge-owner] [--charge-owner-pct N] [--transfer-pct N]
//!          [--cycle-theft-pct N] [--cycle-tax-pct P] [--cycle-tax-frac F]
//!          [--cycle-tax-lifelong F P]
//!          [--world-e001] [--founder HEX:COUNT]... [--inject TICK:HEX:COUNT]...
//!          [--state-every N] [--replay-from FILE]
//! evo-core --classify DIR [--harness-ticks N] [--classes-out NAME] [physics flags]
//! evo-core --host HEX [--host-body HEX] [--host-pad] [--harness-ticks N] [physics flags]
//! evo-core --neighbours HEX [--host-body HEX] [--harness-ticks N] [--neighbours-out FILE]
//!          [--neighbours-pad-only | --neighbours-ins] [--threads T] [physics flags]
//! evo-core --disasm HEX
//!
//! --ancestor NAME (T03) picks the seeded ancestor: `std` (default, the
//! 21-byte body of PLAN §5.3.3, `sim::ancestor`) or `tierra` (the
//! template-addressed 41-byte body, `sim::ancestor_t`, E015). --k and --e
//! apply to either; --k defaults to 64 for `std` and to 127 for `tierra`
//! (`sim::ANCESTOR_T_K`, the smallest K at which it pays for itself in the
//! harness), --e to 16. meta.json records `"ancestor"`. --founder replaces
//! the ancestor as before; --host without --host-body uses the selected
//! ancestor as the host.
//!
//! The default physics is the E004 world (`Config::default()`: 128 patches
//! of 512 bytes at 8x the Phase 1 sunlight per byte, far `alloc`,
//! proportional absorb, bit rot 1e-4). --world-e001 starts from the Phase 1
//! world of E001–E003 instead (`Config::e001()`); every other flag then
//! modifies that base. To reproduce an E004 arm: control = `--world-e001`,
//! p512_far = `--absorb-fixed --rot 1e-5`, p512_far_prop_rot = no flags.
//!
//! --patch N sets the patch size and scales per-patch income and cap so
//! energy per byte stays at the base world's density (E002). --sun N then
//! multiplies per-patch income and cap by N (E004).
//!
//! --legacy-pending-range (T08, 2026-10-13) restores the world before the
//! fix of the `alloc`/`copy` range edge: every write checks locality from
//! the IP, so a child `alloc` placed at the backward edge of the radius
//! loses the first bytes the `copy` loop writes (a few bytes past the
//! `alloc`, out of range) and keeps the stale bytes there. Without it
//! (the default) a write into the executor's own pending region passes
//! the range check, since `alloc` checked the whole region when it claimed
//! it. Every run recorded before 2026-10-13 is the legacy world, and the
//! flag reproduces it bit for bit. meta.json records
//! `legacy_pending_range`; runs before the flag have no key.
//!
//! --absorb-prop / --absorb-fixed choose whether `absorb` takes a ration
//! proportional to how full the pool is, or a fixed one. --rot P sets the
//! per-byte per-tick bit-rot probability. --self-owner makes `self` name
//! the living owner of the byte at IP instead of the executing organism
//! (E006, H8). --charge-owner makes the living owner of the byte at IP pay
//! for an instruction another organism executes there, instead of the
//! executor (E008: parasitism costs the host). --charge-owner-pct N
//! (0-100, default 0) splits that cost instead (E009): the owner pays
//! floor(cost * N / 100), or its whole store if less, and the executor the
//! rest; only the executor's part has to be affordable, so an owner at zero
//! never stops the intruder. If both are given, --charge-owner wins.
//! --transfer-pct N (N >= 0, default 0) is the transfer rule (E010): the
//! executor pays for every instruction itself, as with no flag, and then,
//! if the byte at IP belongs to another living organism, that owner loses
//! floor(cost * N / 100), or its whole store if less, and the executor
//! gains it up to its own store cap (the rest is dissipated). It cannot be
//! combined with --charge-owner or a non-zero --charge-owner-pct; the run
//! is refused with an error.
//!
//! --cycle-theft-pct N (0-100, default 0) is cycle theft (E014): energy is
//! matter and is conserved, the per-tick cap is time. When an organism runs
//! an instruction at a byte owned by another living organism (its body or
//! pending region), it pays the energy as with no flag, and the owner's
//! execution budget is debited floor(cost * N / 100) milli-units, cost
//! being the instruction's full price (search and alloc extras included).
//! The debit is carried as the owner's debt and taken from its budget at
//! the start of its next turns, at most one cap per tick; a host that owes
//! a cap or more pays upkeep and runs nothing that tick. Energy is never
//! touched and nothing is drawn from the PRNG. Debris, free bytes and dead
//! owners debit nothing. N = 0 is bit-identical to no flag.
//! --cycle-tax-pct P (0-100, default 0) is its matched control, a random
//! cycle tax: each tick, each living organism, with probability
//! --cycle-tax-frac F (0-1, default 1), loses P% of its cap that tick (on
//! top of any theft debt, never below zero). F = 1 taxes every organism
//! every tick with no PRNG draw; 0 < F < 1 draws once per organism per tick
//! (after upkeep, in the shuffled order). The three flags combine with each
//! other and with any energy rule; nothing is refused.
//! --cycle-tax-lifelong F P (T10; F 0-1, P 0-100, default off) is the
//! control shaped like the theft: when an organism is born at `divide` or
//! placed by --inject, one PRNG draw makes it taxed for life with
//! probability F (founders are never taxed: the founder is the one body
//! not born next to anything), and a body taxed for life loses P% of its
//! cap every tick before it runs (after any theft debt and random tax,
//! never below zero; counted in `cycles_taxed_m`). The state is not
//! inherited: each child draws for itself. A body born into a slow slot of
//! the machine that stays there, as the control for a body born next to a
//! parasite that stays entered. F = 0 or P = 0 taxes nobody and draws
//! nothing (bit-identical to no flag); F = 1 taxes every body with no
//! draw. deaths.csv's `taxed_for_life` column (0/1) says which bodies were
//! taxed. It combines with the other two cost rules; nothing is refused.
//!
//! --founder HEX:COUNT (repeatable, E009a) seeds COUNT copies of the genome
//! HEX, 100 units each, instead of the one ancestor. All copies from all
//! --founder flags are placed in the order given (first flag's copies
//! first) at world_size / 2 + world_size * j / total, modulo world_size,
//! for j = 0 .. total - 1 (`sim::founder_starts`): evenly around the ring,
//! no two in one patch when total is at most the patch count (128 in the
//! default world), and one founder lands where the single ancestor always
//! has. Without the flag the run is the ancestor (--k, --e) once at
//! world_size / 2, bit-identical to runs before the flag existed; one
//! `--founder <that ancestor's hex>:1` gives the same run. meta.json lists
//! the founders and their start addresses.
//!
//! --inject TICK:HEX:COUNT (repeatable, E009b) places COUNT copies of HEX,
//! 100 units each, `parent` 0 and birth tick TICK, at the start of tick
//! TICK (>= 1) before any organism steps (`Sim::inject`). Copy j targets
//! world_size / 2 + world_size * j / COUNT modulo world_size and takes the
//! first run of len(HEX) bytes, scanning forward from the target, with no
//! byte owned by a living organism (free or debris; overwritten). If no
//! such run begins before the next copy's target (for the last copy, the
//! first copy's target plus world_size) the copy is skipped. No PRNG draw;
//! without the flag the run is unchanged. Injected bodies are recorded as
//! founders are (genomes.csv origin `seed`, no births.csv row); meta.json
//! lists each injection with the start of every copy (-1 if skipped).
//!
//! --out DIR writes a run directory (docs/instrumentation.md): event CSVs,
//! census/organism/patch snapshots every --census ticks (default: the
//! --report interval), genomes.csv, and meta.json.
//!
//! --state-every N (T04; needs --out) also writes a full-state snapshot
//! `DIR/state/<tick>.bin` every N ticks and at the final tick
//! (`Sim::save_state`; about 0.7 MB at the default world size). Without
//! the flag nothing changes. meta.json records `state_every`.
//!
//! --replay-from FILE [--seed S] (T04) starts the run from that snapshot
//! instead of seeding tick 0. The physics flags on the command line must
//! give the file's config exactly, `seed` aside, or the run is refused
//! with an error naming the first field that differs. --ticks is then an
//! absolute tick and must be above the snapshot's. Without --seed the
//! file's PRNG stream continues and the run is bit-identical to the
//! original's from that tick on; with --seed S the PRNG is re-seeded with
//! `Rng::new(S)` at the snapshot tick (`Sim::reseed`). --out works as
//! usual from the snapshot tick: the census, organism and patch rows and a
//! world.bin record are written for it, every living body's genome goes
//! into genomes.csv with origin `replay`, and meta.json records
//! `replay_from` (path, tick, the file's seed, and S or null). --founder
//! is refused, and so is --inject at or before the snapshot's tick; later
//! injections work. --ancestor, --k and --e seed nothing in a replay and
//! are only recorded in meta.json, so pass the original run's.
//!
//! --classify DIR reads DIR/genomes.csv, runs each genome alone in the
//! single-genome harness, and writes DIR/classes.csv (or DIR/NAME with
//! --classes-out). The harness uses the physics given on the command line
//! (default physics if none) with every noise source off (E005).
//!
//! --host HEX runs the genome given as hex immediately before the ancestor
//! (two-genome harness, E005) and prints a CSV header and one row:
//! `len,births,exact_births,host_copies,host_exact_births,alive,host_alive,
//! executed,exec_foreign,ticks_run,stopped_early,entry_off`: the genome's
//! births and exact births, the host copies it made, the host's exact
//! births, who is alive, the genome's foreign-execution share, how many
//! ticks ran, and where it first ran a host byte (offset from the host's
//! start, -1 if never; T03).
//! The harness stops when the genome dies, so `stopped_early` = true means
//! fewer than --harness-ticks ticks were simulated and the counts cover only
//! `ticks_run` ticks (E007: not evidence of a resistant host). Physics flags
//! apply, so `--host 00 --cycle-theft-pct 50` is E014's gate 1 (a `pad`
//! before the ancestor). --host-pad
//! replaces every byte of the genome with `pad` first, to test whether its
//! content matters.
//! --host-body HEX uses that genome as the host instead of the ancestor
//! (E007: a parasite against the hosts that evolved alongside it).
//!
//! --neighbours HEX (T03, E015) classifies every single-byte mutant of HEX:
//! at each position each of the 255 substitutions, then the deletion (with
//! --neighbours-pad-only, only the substitution by `pad`, byte 0, at each
//! position: T05's knockout set). --neighbours-ins (T11) adds after the
//! deletion at each position the 256 insertions of every byte value before
//! it, and the 256 after the last byte at the end (`kind` `ins`, `pos` the
//! byte it goes before); it is ignored with --neighbours-pad-only, and off
//! by default, so the files of T05, E015 and E016 are unchanged. Each
//! mutant runs alone in the quiet harness for --harness-ticks ticks
//! (default 3,000) and immediately before
//! a host, which is HEX itself unless --host-body gives another body; the
//! physics flags apply as for --host. One CSV row per mutant, in that order,
//! to FILE (--neighbours-out; default neighbours.csv in the current
//! directory): `pos,kind,byte,hex,raw_hash,func_hash,class_alone,
//! births_alone,exact_alone,alive_alone,births_host,exact_host,host_copies,
//! host_exact,alive_host,host_alive,executed,exec_foreign,entry_off,
//! ticks_run,label` (`byte` empty for a deletion, the inserted value for
//! an insertion; `executed` through
//! `ticks_run` from the run before the host; the label rule is
//! `harness::label`, docs/instrumentation.md). stdout gets the counts by
//! label and the `parasite_jump` rows by position. --threads T (default:
//! the available parallelism) runs the mutants on T threads; the file is
//! the same at any T.

use evo_core::config::{Config, MILLI};
use evo_core::harness;
use evo_core::record::{Recorder, ReplayFrom, RunInfo};
use evo_core::sim::{AncestorKind, Event, Injection, Sim};
use std::io::Write;
use std::path::Path;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    // The world flag sets the base every other flag modifies, so it is read
    // first wherever it appears.
    let mut cfg = if args.iter().any(|a| a == "--world-e001") { Config::e001() } else { Config::default() };
    let mut ticks: u64 = 10_000;
    let mut report: u64 = 1000;
    let mut census: Option<u64> = None;
    let mut log: Option<String> = None;
    let mut out: Option<String> = None;
    let mut classify: Option<String> = None;
    let mut harness_ticks: u64 = 3000;
    let mut classes_out = String::from("classes.csv");
    let mut host: Option<String> = None;
    let mut host_body: Option<String> = None;
    let mut host_pad = false;
    let mut neighbours: Option<String> = None;
    let mut neighbours_out = String::from("neighbours.csv");
    let mut neighbours_pad_only = false;
    let mut neighbours_ins = false;
    let mut threads: Option<usize> = None;
    let mut kind = AncestorKind::Std;
    // --k defaults by ancestor (resolved after parsing).
    let mut k: Option<i8> = None;
    let mut e: i8 = 16;
    let mut patch: Option<u32> = None;
    let mut sun: i64 = 1;
    // (genome, copies) per --founder flag, in the order given.
    let mut founders: Vec<(Vec<u8>, u32)> = Vec::new();
    // --inject flags, in the order given.
    let mut injections: Vec<Injection> = Vec::new();
    // T04: snapshot interval, snapshot to start from, and whether --seed
    // was given at all (a replay re-seeds only then).
    let mut state_every: Option<u64> = None;
    let mut replay_from: Option<String> = None;
    let mut seed_given: Option<u64> = None;
    let mut i = 0;
    while i < args.len() {
        let next = || args.get(i + 1).expect("missing value").clone();
        match args[i].as_str() {
            "--ticks" => { ticks = next().parse().unwrap(); i += 1; }
            "--seed" => { cfg.seed = next().parse().unwrap(); seed_given = Some(cfg.seed); i += 1; }
            "--state-every" => {
                let n: u64 = next().parse().expect("--state-every N must be a whole number");
                assert!(n > 0, "--state-every must be at least 1");
                state_every = Some(n);
                i += 1;
            }
            "--replay-from" => { replay_from = Some(next()); i += 1; }
            "--report" => { report = next().parse().unwrap(); i += 1; }
            "--census" => { census = Some(next().parse().unwrap()); i += 1; }
            "--log" => { log = Some(next()); i += 1; }
            "--out" => { out = Some(next()); i += 1; }
            "--classify" => { classify = Some(next()); i += 1; }
            "--harness-ticks" => { harness_ticks = next().parse().unwrap(); i += 1; }
            "--classes-out" => { classes_out = next(); i += 1; }
            "--host" => { host = Some(next()); i += 1; }
            "--host-body" => { host_body = Some(next()); i += 1; }
            "--neighbours" => { neighbours = Some(next()); i += 1; }
            "--neighbours-out" => { neighbours_out = next(); i += 1; }
            "--neighbours-pad-only" => neighbours_pad_only = true,
            "--neighbours-ins" => neighbours_ins = true,
            "--threads" => {
                let t: usize = next().parse().expect("--threads T must be a whole number");
                assert!(t > 0, "--threads must be at least 1");
                threads = Some(t);
                i += 1;
            }
            "--ancestor" => {
                let v = next();
                kind = AncestorKind::parse(&v).unwrap_or_else(|| {
                    eprintln!("error: --ancestor wants std or tierra, not {v}");
                    std::process::exit(2);
                });
                i += 1;
            }
            "--founder" => {
                let v = next();
                // `split_once` returns Option<(&str, &str)>, Rust's way of
                // saying "maybe a pair"; `expect` panics with the message on None.
                let (hex, count) = v.split_once(':').expect("--founder wants HEX:COUNT");
                let count: u32 = count.parse().expect("--founder COUNT must be a whole number");
                assert!(count > 0 && !hex.is_empty(), "--founder wants a non-empty HEX and COUNT >= 1");
                founders.push((parse_hex(hex), count));
                i += 1;
            }
            "--inject" => {
                let v = next();
                // `splitn(3, ':')` yields at most three pieces; collecting
                // into a Vec lets us check there were exactly three.
                let p: Vec<&str> = v.splitn(3, ':').collect();
                assert!(p.len() == 3, "--inject wants TICK:HEX:COUNT");
                let tick: u64 = p[0].parse().expect("--inject TICK must be a whole number");
                let count: u32 = p[2].parse().expect("--inject COUNT must be a whole number");
                assert!(tick >= 1 && count > 0 && !p[1].is_empty(), "--inject wants TICK >= 1, a non-empty HEX and COUNT >= 1");
                injections.push(Injection { tick, genome: parse_hex(p[1]), count });
                i += 1;
            }
            // Disassemble hex bytes and exit: for reading world.bin from Python.
            "--disasm" => { println!("{}", evo_core::record::disasm(&parse_hex(&next()))); return; }
            "--host-pad" => host_pad = true,
            "--k" => { k = Some(next().parse().unwrap()); i += 1; }
            "--e" => { e = next().parse().unwrap(); i += 1; }
            "--p" => { cfg.p_write_flip = next().parse().unwrap(); cfg.q_slip = cfg.p_write_flip / 4.0; i += 1; }
            "--world" => { cfg.world_size = next().parse().unwrap(); i += 1; }
            "--patch" => { patch = Some(next().parse().unwrap()); i += 1; }
            "--locality" => { cfg.locality = next().parse().unwrap(); i += 1; }
            "--sun" => { sun = next().parse().unwrap(); i += 1; }
            "--rot" => { cfg.p_bit_rot = next().parse().unwrap(); i += 1; }
            "--alloc-far" => cfg.alloc_far = true,
            "--alloc-near" => cfg.alloc_far = false,
            "--legacy-pending-range" => cfg.legacy_pending_range = true,
            "--absorb-prop" => cfg.absorb_proportional = true,
            "--absorb-fixed" => cfg.absorb_proportional = false,
            "--self-owner" => cfg.self_owner = true,
            "--charge-owner" => cfg.charge_owner = true,
            "--charge-owner-pct" => {
                cfg.charge_owner_pct = next().parse().unwrap();
                assert!((0..=100).contains(&cfg.charge_owner_pct), "--charge-owner-pct must be 0-100");
                i += 1;
            }
            "--transfer-pct" => {
                cfg.transfer_pct = next().parse().expect("--transfer-pct N must be a whole number");
                assert!(cfg.transfer_pct >= 0, "--transfer-pct must be 0 or more");
                i += 1;
            }
            "--cycle-theft-pct" => {
                cfg.cycle_theft_pct = next().parse().expect("--cycle-theft-pct N must be a whole number");
                assert!((0..=100).contains(&cfg.cycle_theft_pct), "--cycle-theft-pct must be 0-100");
                i += 1;
            }
            "--cycle-tax-pct" => {
                cfg.cycle_tax_pct = next().parse().expect("--cycle-tax-pct N must be a whole number");
                assert!((0..=100).contains(&cfg.cycle_tax_pct), "--cycle-tax-pct must be 0-100");
                i += 1;
            }
            "--cycle-tax-frac" => {
                cfg.cycle_tax_frac = next().parse().expect("--cycle-tax-frac F must be a number");
                assert!((0.0..=1.0).contains(&cfg.cycle_tax_frac), "--cycle-tax-frac must be 0-1");
                i += 1;
            }
            "--cycle-tax-lifelong" => {
                cfg.cycle_tax_life_frac = next().parse().expect("--cycle-tax-lifelong F P: F must be a number");
                assert!((0.0..=1.0).contains(&cfg.cycle_tax_life_frac), "--cycle-tax-lifelong F must be 0-1");
                let p = args.get(i + 2).expect("--cycle-tax-lifelong wants F and P");
                cfg.cycle_tax_life_pct = p.parse().expect("--cycle-tax-lifelong F P: P must be a whole number");
                assert!((0..=100).contains(&cfg.cycle_tax_life_pct), "--cycle-tax-lifelong P must be 0-100");
                i += 2;
            }
            "--world-e001" => {}
            "--no-protect" => cfg.write_protection = false,
            other => { eprintln!("unknown arg {other}"); std::process::exit(2); }
        }
        i += 1;
    }

    // The transfer (E010) and the owner-pays rules (E008, E009) are
    // different answers to who pays for foreign execution; one at a time.
    if cfg.transfer_pct > 0 && (cfg.charge_owner || cfg.charge_owner_pct > 0) {
        eprintln!("error: --transfer-pct cannot be combined with --charge-owner or --charge-owner-pct");
        std::process::exit(2);
    }

    if let Some(ps) = patch {
        assert!(ps > 0 && cfg.world_size % ps == 0, "--patch must divide the world size");
        let base = cfg.patch_size as i64;
        cfg.patch_income = cfg.patch_income * ps as i64 / base;
        cfg.patch_cap = cfg.patch_cap * ps as i64 / base;
        cfg.patch_size = ps;
    }
    assert!(sun > 0, "--sun must be positive");
    cfg.patch_income *= sun;
    cfg.patch_cap *= sun;
    let k = k.unwrap_or(kind.default_k());

    if let Some(dir) = classify {
        run_classify(Path::new(&dir), &classes_out, harness_ticks, &cfg);
        return;
    }
    if let Some(hex) = neighbours {
        let g = parse_hex(&hex);
        assert!(!g.is_empty(), "--neighbours wants a non-empty HEX");
        let h = host_body.map(|hx| parse_hex(&hx)).unwrap_or_else(|| g.clone());
        let t = threads.unwrap_or_else(|| std::thread::available_parallelism().map_or(1, |n| n.get()));
        let t0 = std::time::Instant::now();
        let set = if neighbours_pad_only {
            harness::MutantSet::PadOnly
        } else if neighbours_ins {
            harness::MutantSet::WithIns
        } else {
            harness::MutantSet::SubDel
        };
        let rows = harness::neighbours(&g, &h, harness_ticks, &cfg, set, t);
        let mut w = std::io::BufWriter::new(std::fs::File::create(&neighbours_out).expect("create neighbours file"));
        harness::write_neighbours(&mut w, &rows).expect("write neighbours file");
        w.flush().expect("write neighbours file");
        print!("{}", harness::neighbours_summary(&rows));
        eprintln!("# {} mutants x 2 runs of {harness_ticks} ticks on {t} threads in {:.1}s; wrote {neighbours_out}",
                  rows.len(), t0.elapsed().as_secs_f64());
        return;
    }
    if let Some(hex) = host {
        let mut g = parse_hex(&hex);
        if host_pad {
            g.iter_mut().for_each(|b| *b = 0);
        }
        let h = host_body.map(|hx| parse_hex(&hx)).unwrap_or_else(|| kind.body(k, e));
        let r = harness::run_with_host(&g, &h, harness_ticks, &cfg);
        println!(
            "len,births,exact_births,host_copies,host_exact_births,alive,host_alive,executed,exec_foreign,ticks_run,stopped_early,entry_off"
        );
        println!(
            "{},{},{},{},{},{},{},{},{},{},{},{}",
            g.len(), r.births, r.exact_births, r.host_copies, r.host_exact_births, r.alive,
            r.host_alive, r.executed, r.exec_foreign, r.ticks_run, r.stopped_early, r.entry_off
        );
        return;
    }
    let census = census.unwrap_or(report);
    assert!(census > 0 && report > 0, "--census and --report must be positive");
    if state_every.is_some() && out.is_none() {
        eprintln!("error: --state-every needs --out DIR (snapshots go to DIR/state/)");
        std::process::exit(2);
    }

    let (mut sim, founder_starts, replay) = match &replay_from {
        None => {
            let mut sim = Sim::new(cfg.clone());
            // No --founder: the ancestor once, which `seed_founders` puts at
            // world_size / 2, where the single founder has always been.
            if founders.is_empty() {
                founders.push((kind.body(k, e), 1));
            }
            let starts = sim.seed_founders(&founders, 100 * MILLI);
            (sim, starts, None)
        }
        // T04: continue from a snapshot. Every refusal exits before a tick runs.
        Some(path) => {
            if !founders.is_empty() {
                refuse(path, "--founder seeds tick 0, which a replay does not run");
            }
            let f = std::fs::File::open(path).unwrap_or_else(|e| refuse(path, &e.to_string()));
            let mut sim = Sim::load_state(&mut std::io::BufReader::new(f), cfg.clone())
                .unwrap_or_else(|e| refuse(path, &e.to_string()));
            let t = sim.tick;
            if ticks <= t {
                refuse(path, &format!("--ticks {ticks} is not above the snapshot's tick {t} (in a replay --ticks is absolute)"));
            }
            if let Some(j) = injections.iter().find(|j| j.tick <= t) {
                refuse(path, &format!("--inject at tick {} is at or before the snapshot's tick {t}", j.tick));
            }
            let file_seed = sim.cfg.seed;
            if let Some(s) = seed_given {
                sim.reseed(s);
            }
            let how = seed_given.map_or(format!("seed {file_seed}, stream continued"), |s| format!("re-seeded with {s}"));
            eprintln!("# replay from {path} at tick {t} ({how})");
            (sim, Vec::new(), Some(ReplayFrom { path: path.clone(), tick: t, file_seed, reseed: seed_given }))
        }
    };
    let mut logf = log.map(|p| std::io::BufWriter::new(std::fs::File::create(p).unwrap()));
    let mut rec = out.map(|d| {
        let info = RunInfo {
            ticks_requested: ticks,
            census_every: census,
            ancestor_k: k,
            ancestor_e: e,
            ancestor: kind.name().to_string(),
            founders: founders.iter().map(|(g, n)| (to_hex(g), *n)).collect(),
            founder_starts: founder_starts.clone(),
            injections: injections.iter().map(|j| (j.tick, to_hex(&j.genome), j.count)).collect(),
            state_every,
            replay_from: replay,
        };
        let mut r = Recorder::create(Path::new(&d), &sim, info).expect("create run directory");
        r.snapshot(&sim).unwrap();
        r
    });
    let t0 = std::time::Instant::now();
    let executed_before = sim.executed_total();

    println!("tick,alive,genotypes,top_count,top_len,mean_len,max_len,births,deaths,energy_org,energy_patch,patches_occ,active");
    let mut births = 0u64;
    let mut deaths = 0u64;
    // Organisms that ran `divide` since the last report line; the `active`
    // column counts those still alive at the report.
    let mut dividers: std::collections::HashSet<u32> = Default::default();
    // Snapshots written (--state-every) and the time spent writing them.
    let (mut states, mut state_secs) = (0u32, 0.0f64);
    // `ticks` is absolute: a run from tick 0 runs `ticks` ticks, a replay
    // from the snapshot tick up to `ticks`.
    while sim.tick < ticks {
        // Injections due this tick, before any organism steps (no-op
        // without --inject).
        for done in sim.inject_due(&injections, 100 * MILLI) {
            if let Some(r) = rec.as_mut() {
                r.injected(&sim, &done);
            }
        }
        sim.run_tick();
        // Take this tick's events out of the sim so memory stays flat.
        let events: Vec<Event> = sim.events.drain(..).collect();
        for ev in &events {
            match ev {
                Event::Birth { executor, .. } => {
                    births += 1;
                    dividers.insert(*executor);
                }
                Event::Death { .. } => deaths += 1,
            }
            if let Some(f) = logf.as_mut() {
                writeln!(f, "{ev:?}").unwrap();
            }
        }
        let extinct = sim.alive_count() == 0;
        if let Some(r) = rec.as_mut() {
            r.events(&sim, &events).unwrap();
            if sim.tick % census == 0 || extinct || sim.tick == ticks {
                r.snapshot(&sim).unwrap();
            }
            // After the tick's events are drained, as `save_state` wants.
            if let Some(n) = state_every {
                if sim.tick % n == 0 || extinct || sim.tick == ticks {
                    let ts = std::time::Instant::now();
                    r.save_state(&sim).expect("write state snapshot");
                    state_secs += ts.elapsed().as_secs_f64();
                    states += 1;
                }
            }
        }
        // Also report on extinction so short-lived runs leave a final row.
        if sim.tick % report == 0 || extinct {
            let c = sim.census();
            let alive = sim.alive_count();
            let (mut sum, mut max) = (0u64, 0u32);
            for o in sim.orgs.iter().filter(|o| o.alive) {
                sum += o.len as u64;
                max = max.max(o.len);
            }
            let mean = if alive > 0 { sum as f64 / alive as f64 } else { 0.0 };
            // Patches holding at least one living body start: spatial spread.
            let occ: std::collections::HashSet<u32> =
                sim.orgs.iter().filter(|o| o.alive).map(|o| o.start / cfg.patch_size).collect();
            let (tc, tl) = c.first().map(|x| (x.1, x.2)).unwrap_or((0, 0));
            println!(
                "{},{},{},{},{},{:.1},{},{},{},{},{},{},{}",
                sim.tick, alive, c.len(), tc, tl, mean, max, births, deaths,
                sim.energy_in_organisms() / MILLI, sim.energy_in_patches() / MILLI,
                occ.len(),
                dividers.iter().filter(|&&id| sim.genome_of(id).map_or(false, |o| o.alive)).count()
            );
            dividers.clear();
        }
        if extinct {
            println!("# extinct at tick {}", sim.tick);
            break;
        }
    }
    let dt = t0.elapsed().as_secs_f64();
    if let Some(r) = rec {
        r.finish(&sim).unwrap();
    }
    // Instructions run in this run: a replay's snapshot carries the count
    // since tick 0.
    let executed = sim.executed_total() - executed_before;
    eprintln!("# {:.2}s, {} instructions, {:.1} M instr/s", dt, executed, executed as f64 / dt / 1e6);
    if states > 0 {
        eprintln!("# {states} state snapshots in {:.3}s ({:.1} ms each)", state_secs, 1e3 * state_secs / states as f64);
    }
    // Top genotypes with disassembly.
    for (h, count, len) in sim.census().into_iter().take(5) {
        let o = sim.orgs.iter().find(|o| o.alive && o.genome_hash == h).unwrap();
        eprintln!("# {count:6} x len {len:3} [{h:016x}] {}", evo_core::record::disasm(&o.genome));
    }
}

/// Refuse a `--replay-from` run (T04): print why and exit with status 2.
///
/// Rust note: `-> !` means the function never returns (Zig `noreturn`), so
/// it can stand where any value is expected, as in `unwrap_or_else`.
fn refuse(path: &str, why: &str) -> ! {
    eprintln!("error: --replay-from {path}: {why}");
    std::process::exit(2);
}

/// Genome bytes from the `bytes_hex` form (two lowercase hex digits per byte).
fn parse_hex(hex: &str) -> Vec<u8> {
    assert!(hex.len() % 2 == 0, "odd-length hex");
    (0..hex.len())
        .step_by(2)
        .map(|j| u8::from_str_radix(&hex[j..j + 2], 16).expect("bad bytes_hex"))
        .collect()
}

/// The `bytes_hex` form of a genome (inverse of `parse_hex`).
fn to_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

/// `--classify DIR`: label every genome in DIR/genomes.csv with the
/// single-genome harness under `cfg`'s physics and write DIR/`out`.
fn run_classify(dir: &Path, out: &str, ticks: u64, cfg: &Config) {
    let text = std::fs::read_to_string(dir.join("genomes.csv")).expect("read genomes.csv");
    let mut lines = text.lines();
    let header: Vec<&str> = lines.next().expect("empty genomes.csv").split(',').collect();
    let col = |name: &str| header.iter().position(|&h| h == name).unwrap_or_else(|| panic!("no column {name}"));
    let (c_hash, c_bytes) = (col("raw_hash"), col("bytes_hex"));
    let mut w = std::io::BufWriter::new(std::fs::File::create(dir.join(out)).expect("create classes file"));
    writeln!(w, "raw_hash,class,births,exact_births,first_birth_tick,alive,final_energy_m,executed,absorbs").unwrap();
    let mut n = 0;
    for line in lines {
        let f: Vec<&str> = line.split(',').collect();
        let bytes = parse_hex(f[c_bytes]);
        let r = harness::run_alone_with(&bytes, ticks, cfg);
        writeln!(
            w,
            "{},{},{},{},{},{},{},{},{}",
            f[c_hash], r.class(), r.births, r.exact_births, r.first_birth_tick, r.alive,
            r.final_energy, r.executed, r.absorbs
        )
        .unwrap();
        n += 1;
    }
    eprintln!("# classified {n} genomes ({ticks} harness ticks each)");
}
