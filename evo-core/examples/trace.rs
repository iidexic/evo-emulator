//! Trace one genome alone under the E004 world physics (noise off): per
//! tick, IP offset, registers, energy, counters. Diagnostic for reading a
//! genome's behaviour without stepping through it by hand (E005).
//!
//!     cargo run --release --example trace -- HEX [ticks] [ADDR=HEX ...]
//!
//! Each ADDR=HEX writes bytes into free memory at ADDR before the run
//! (dead code left by an earlier body), to test what a genome does with it.
use evo_core::config::{Config, MILLI};
use evo_core::isa::disasm_at;
use evo_core::sim::Sim;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let hex = &args[0];
    let ticks: u64 = args.get(1).map_or(60, |s| s.parse().unwrap());
    let g: Vec<u8> = (0..hex.len())
        .step_by(2)
        .map(|j| u8::from_str_radix(&hex[j..j + 2], 16).unwrap())
        .collect();
    let mut cfg = Config::default();
    cfg.p_write_flip = 0.0;
    cfg.q_slip = 0.0;
    cfg.p_bit_rot = 0.0;
    cfg.p_debris_decay = 0.0;
    cfg.alloc_far = true;
    cfg.patch_size = 512;
    cfg.patch_income = 256 * MILLI;
    cfg.patch_cap = 4096 * MILLI;
    let mut sim = Sim::new(cfg.clone());
    for spec in args.iter().skip(2) {
        let (addr, hx) = spec.split_once('=').expect("ADDR=HEX");
        let addr: usize = addr.parse().unwrap();
        for (k, j) in (0..hx.len()).step_by(2).enumerate() {
            sim.bytes[addr + k] = u8::from_str_radix(&hx[j..j + 2], 16).unwrap();
        }
    }
    sim.seed(cfg.world_size / 2, &g, 100 * MILLI, 0);
    for _ in 0..ticks {
        sim.run_tick();
        let line = {
            let o = &sim.orgs[0];
            let off = sim.ip_off(o);
            let op = if off < o.len {
                disasm_at(&g, off as usize).0
            } else {
                format!("ip={} owner={}", o.ip, sim.owner[o.ip as usize])
            };
            format!(
                "t{:3} alive={} ip_off={:5} {:14} A={:6} B={:6} C={:6} D={:6} E={:5} exec={} unowned={} kids={}",
                sim.tick, o.alive, off, op, o.regs[0] as i32, o.regs[1] as i32, o.regs[2] as i32,
                o.regs[3] as i32, o.energy / MILLI, o.stats.executed, o.stats.exec_unowned, o.offspring
            )
        };
        println!("{line}");
        let alive = sim.orgs[0].alive;
        sim.cull_all_but(0);
        if !alive {
            break;
        }
    }
}
