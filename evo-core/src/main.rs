//! CLI: run a seeded world and print a census.
//!
//! evo-core [--ticks N] [--seed S] [--report N] [--log PATH] [--k K] [--e E]
//!          [--no-protect] [--p P] [--world N] [--patch N]
//!          [--alloc-far | --alloc-near] [--absorb-prop | --absorb-fixed]
//!          [--locality N] [--out DIR] [--census N] [--sun N] [--rot P]
//!          [--self-owner] [--world-e001]
//! evo-core --classify DIR [--harness-ticks N] [--classes-out NAME] [physics flags]
//! evo-core --host HEX [--host-body HEX] [--host-pad] [--harness-ticks N] [physics flags]
//! evo-core --disasm HEX
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
//! --absorb-prop / --absorb-fixed choose whether `absorb` takes a ration
//! proportional to how full the pool is, or a fixed one. --rot P sets the
//! per-byte per-tick bit-rot probability. --self-owner makes `self` name
//! the living owner of the byte at IP instead of the executing organism
//! (E006, H8).
//!
//! --out DIR writes a run directory (docs/instrumentation.md): event CSVs,
//! census/organism/patch snapshots every --census ticks (default: the
//! --report interval), genomes.csv, and meta.json.
//!
//! --classify DIR reads DIR/genomes.csv, runs each genome alone in the
//! single-genome harness, and writes DIR/classes.csv (or DIR/NAME with
//! --classes-out). The harness uses the physics given on the command line
//! (default physics if none) with every noise source off (E005).
//!
//! --host HEX runs the genome given as hex immediately before the ancestor
//! (two-genome harness, E005) and prints one CSV line: the genome's births
//! and exact births, the host's exact births, who is alive, and the
//! genome's foreign-execution share. --host-pad replaces every byte of the
//! genome with `pad` first, to test whether its content matters.
//! --host-body HEX uses that genome as the host instead of the ancestor
//! (E007: a parasite against the hosts that evolved alongside it).

use evo_core::config::{Config, MILLI};
use evo_core::harness;
use evo_core::record::{Recorder, RunInfo};
use evo_core::sim::{ancestor, Event, Sim};
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
    let mut k: i8 = 64;
    let mut e: i8 = 16;
    let mut patch: Option<u32> = None;
    let mut sun: i64 = 1;
    let mut i = 0;
    while i < args.len() {
        let next = || args.get(i + 1).expect("missing value").clone();
        match args[i].as_str() {
            "--ticks" => { ticks = next().parse().unwrap(); i += 1; }
            "--seed" => { cfg.seed = next().parse().unwrap(); i += 1; }
            "--report" => { report = next().parse().unwrap(); i += 1; }
            "--census" => { census = Some(next().parse().unwrap()); i += 1; }
            "--log" => { log = Some(next()); i += 1; }
            "--out" => { out = Some(next()); i += 1; }
            "--classify" => { classify = Some(next()); i += 1; }
            "--harness-ticks" => { harness_ticks = next().parse().unwrap(); i += 1; }
            "--classes-out" => { classes_out = next(); i += 1; }
            "--host" => { host = Some(next()); i += 1; }
            "--host-body" => { host_body = Some(next()); i += 1; }
            // Disassemble hex bytes and exit: for reading world.bin from Python.
            "--disasm" => { println!("{}", evo_core::record::disasm(&parse_hex(&next()))); return; }
            "--host-pad" => host_pad = true,
            "--k" => { k = next().parse().unwrap(); i += 1; }
            "--e" => { e = next().parse().unwrap(); i += 1; }
            "--p" => { cfg.p_write_flip = next().parse().unwrap(); cfg.q_slip = cfg.p_write_flip / 4.0; i += 1; }
            "--world" => { cfg.world_size = next().parse().unwrap(); i += 1; }
            "--patch" => { patch = Some(next().parse().unwrap()); i += 1; }
            "--locality" => { cfg.locality = next().parse().unwrap(); i += 1; }
            "--sun" => { sun = next().parse().unwrap(); i += 1; }
            "--rot" => { cfg.p_bit_rot = next().parse().unwrap(); i += 1; }
            "--alloc-far" => cfg.alloc_far = true,
            "--alloc-near" => cfg.alloc_far = false,
            "--absorb-prop" => cfg.absorb_proportional = true,
            "--absorb-fixed" => cfg.absorb_proportional = false,
            "--self-owner" => cfg.self_owner = true,
            "--world-e001" => {}
            "--no-protect" => cfg.write_protection = false,
            other => { eprintln!("unknown arg {other}"); std::process::exit(2); }
        }
        i += 1;
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

    if let Some(dir) = classify {
        run_classify(Path::new(&dir), &classes_out, harness_ticks, &cfg);
        return;
    }
    if let Some(hex) = host {
        let mut g = parse_hex(&hex);
        if host_pad {
            g.iter_mut().for_each(|b| *b = 0);
        }
        let h = host_body.map(|hx| parse_hex(&hx)).unwrap_or_else(|| ancestor(k, e));
        let r = harness::run_with_host(&g, &h, harness_ticks, &cfg);
        println!("len,births,exact_births,host_copies,host_exact_births,alive,host_alive,executed,exec_foreign");
        println!(
            "{},{},{},{},{},{},{},{},{}",
            g.len(), r.births, r.exact_births, r.host_copies, r.host_exact_births, r.alive,
            r.host_alive, r.executed, r.exec_foreign
        );
        return;
    }
    let census = census.unwrap_or(report);
    assert!(census > 0 && report > 0, "--census and --report must be positive");

    let mut sim = Sim::new(cfg.clone());
    let g = ancestor(k, e);
    sim.seed(cfg.world_size / 2, &g, 100 * MILLI, 0);
    let mut logf = log.map(|p| std::io::BufWriter::new(std::fs::File::create(p).unwrap()));
    let mut rec = out.map(|d| {
        let info = RunInfo { ticks_requested: ticks, census_every: census, ancestor_k: k, ancestor_e: e };
        let mut r = Recorder::create(Path::new(&d), &sim, info).expect("create run directory");
        r.snapshot(&sim).unwrap();
        r
    });
    let t0 = std::time::Instant::now();

    println!("tick,alive,genotypes,top_count,top_len,mean_len,max_len,births,deaths,energy_org,energy_patch,patches_occ,active");
    let mut births = 0u64;
    let mut deaths = 0u64;
    // Organisms that ran `divide` since the last report line; the `active`
    // column counts those still alive at the report.
    let mut dividers: std::collections::HashSet<u32> = Default::default();
    for _ in 0..ticks {
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
    let executed: u64 = sim.orgs.iter().map(|o| o.stats.executed).sum();
    eprintln!("# {:.2}s, {} instructions, {:.1} M instr/s", dt, executed, executed as f64 / dt / 1e6);
    // Top genotypes with disassembly.
    for (h, count, len) in sim.census().into_iter().take(5) {
        let o = sim.orgs.iter().find(|o| o.alive && o.genome_hash == h).unwrap();
        eprintln!("# {count:6} x len {len:3} [{h:016x}] {}", evo_core::record::disasm(&o.genome));
    }
}

/// Genome bytes from the `bytes_hex` form (two lowercase hex digits per byte).
fn parse_hex(hex: &str) -> Vec<u8> {
    assert!(hex.len() % 2 == 0, "odd-length hex");
    (0..hex.len())
        .step_by(2)
        .map(|j| u8::from_str_radix(&hex[j..j + 2], 16).expect("bad bytes_hex"))
        .collect()
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
