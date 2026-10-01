//! CLI: run a seeded world and print a census.
//!
//! evo-core [--ticks N] [--seed S] [--report N] [--log PATH] [--k K] [--e E]
//!          [--no-protect] [--p P] [--world N]

use evo_core::config::{Config, MILLI};
use evo_core::sim::{ancestor, Event, Sim};
use std::io::Write;

fn main() {
    let mut cfg = Config::default();
    let mut ticks: u64 = 10_000;
    let mut report: u64 = 1000;
    let mut log: Option<String> = None;
    let mut k: i8 = 64;
    let mut e: i8 = 16;
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mut i = 0;
    while i < args.len() {
        let next = || args.get(i + 1).expect("missing value").clone();
        match args[i].as_str() {
            "--ticks" => { ticks = next().parse().unwrap(); i += 1; }
            "--seed" => { cfg.seed = next().parse().unwrap(); i += 1; }
            "--report" => { report = next().parse().unwrap(); i += 1; }
            "--log" => { log = Some(next()); i += 1; }
            "--k" => { k = next().parse().unwrap(); i += 1; }
            "--e" => { e = next().parse().unwrap(); i += 1; }
            "--p" => { cfg.p_write_flip = next().parse().unwrap(); cfg.q_slip = cfg.p_write_flip / 4.0; i += 1; }
            "--world" => { cfg.world_size = next().parse().unwrap(); i += 1; }
            "--no-protect" => cfg.write_protection = false,
            other => { eprintln!("unknown arg {other}"); std::process::exit(2); }
        }
        i += 1;
    }

    let mut sim = Sim::new(cfg.clone());
    let g = ancestor(k, e);
    sim.seed(cfg.world_size / 2, &g, 100 * MILLI, 0);
    let mut logf = log.map(|p| std::io::BufWriter::new(std::fs::File::create(p).unwrap()));
    let mut flushed = 0usize;
    let t0 = std::time::Instant::now();

    println!("tick,alive,genotypes,top_count,top_len,mean_len,max_len,births,deaths,energy_org,energy_patch");
    let mut births = 0u64;
    let mut deaths = 0u64;
    for _ in 0..ticks {
        sim.run_tick();
        for ev in &sim.events[flushed..] {
            match ev {
                Event::Birth { .. } => births += 1,
                Event::Death { .. } => deaths += 1,
            }
            if let Some(f) = logf.as_mut() {
                writeln!(f, "{ev:?}").unwrap();
            }
        }
        flushed = sim.events.len();
        if sim.tick % report == 0 {
            let c = sim.census();
            let alive = sim.alive_count();
            let (mut sum, mut max) = (0u64, 0u32);
            for o in sim.orgs.iter().filter(|o| o.alive) {
                sum += o.len as u64;
                max = max.max(o.len);
            }
            let mean = if alive > 0 { sum as f64 / alive as f64 } else { 0.0 };
            let (tc, tl) = c.first().map(|x| (x.1, x.2)).unwrap_or((0, 0));
            println!(
                "{},{},{},{},{},{:.1},{},{},{},{},{}",
                sim.tick, alive, c.len(), tc, tl, mean, max, births, deaths,
                sim.energy_in_organisms() / MILLI, sim.energy_in_patches() / MILLI
            );
        }
        if sim.alive_count() == 0 {
            println!("# extinct at tick {}", sim.tick);
            break;
        }
    }
    let dt = t0.elapsed().as_secs_f64();
    let executed: u64 = sim.orgs.iter().map(|o| o.executed).sum();
    eprintln!("# {:.2}s, {} instructions, {:.1} M instr/s", dt, executed, executed as f64 / dt / 1e6);
    // Top genotypes with disassembly.
    for (h, count, len) in sim.census().into_iter().take(5) {
        let o = sim.orgs.iter().find(|o| o.alive && o.genome_hash == h).unwrap();
        let mut s = String::new();
        let mut i = 0;
        while i < o.genome.len() {
            let (t, l) = evo_core::isa::disasm_at(&o.genome, i);
            s.push_str(&t);
            s.push_str(" ; ");
            i += l;
        }
        eprintln!("# {count:6} x len {len:3} [{h:016x}] {s}");
    }
}
