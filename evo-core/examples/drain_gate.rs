//! T12 §3, the harness gate for `drain` (docs/tasks/T12-drain-income-take.md):
//! G1 (the tierra ancestor with its `absorb` flipped to `drain`) and G2 (the
//! designed drainer of tests/drain.rs) before the tierra ancestor under
//! `tierra_n0`'s physics (`--sun 2`, the fixed edge), 3,000 harness ticks.
//!
//! cargo run --release --example drain_gate [g1|g2|k K] [ticks]

use evo_core::config::Config;
use evo_core::harness::{run_alone_with, run_with_host, HostResult};
use evo_core::isa::Isa;
use evo_core::config::MILLI;
use evo_core::sim::{ancestor_t, Event, Sim, ANCESTOR_T_K};

fn drainer(isa: &Isa, k: i8) -> Vec<u8> {
    isa.assemble(&format!(
        "self\nadd B\nlit C {k}\nlit D -5\ndrain\nabsorb\ndec C\nskipz C\njmpr D\nself\nswap B\nswap C\nalloc C\nlit D -4\ncopy\ndec C\nskipz C\njmpr D\nlit A 16\ndivide A\nself\njmpa A\n"
    ))
    .unwrap()
}

fn cfg(op: u8, pct: i64, loss: i64) -> Config {
    let mut c = Config::default();
    c.patch_income *= 2;
    c.patch_cap *= 2;
    c.drain_op = op;
    c.drain_pct = pct;
    c.drain_loss_pct = loss;
    c
}

fn row(label: &str, r: &HostResult) {
    println!(
        "{label:<28} | {:>6} {:>6} {:>5} | {:>6} {:>5} {:>8.1} | {:>10.1} {:>10.1} {:>7} {:>7} {:>5}",
        r.births, r.exact_births, r.alive, r.host_exact_births, r.host_alive, r.host_drained_m as f64 / 1e3,
        r.drain_gain_m as f64 / 1e3, r.absorb_gain_m as f64 / 1e3, r.drains, r.drains_fail, r.ticks_run
    );
}

/// One harness pair run to the end (children culled each tick, nobody
/// stopped early): `drainer` (if any) immediately before `host`, the host
/// seeded with `host_e`, the drainer with 100 units. Returns (drainer
/// births, host births, host alive, host death tick, drainer drain gain,
/// drainer absorb gain), energies in units.
fn pair(drainer: Option<&[u8]>, host: &[u8], c: &Config, host_e: i64, ticks: u64) -> (u32, u32, bool, Option<u64>, f64, f64) {
    let c = evo_core::harness::quiet(c.clone());
    let mut sim = Sim::new(c.clone());
    let mid = c.world_size / 2;
    let hid = sim.seed(mid, host, host_e, 0);
    let did = drainer.map(|d| sim.seed(mid - d.len() as u32, d, 100 * MILLI, 0));
    let keep: Vec<u32> = std::iter::once(hid).chain(did).collect();
    let (mut db, mut hb, mut death) = (0, 0, None);
    let (mut dg, mut ag) = (0, 0);
    for t in 1..=ticks {
        sim.run_tick();
        for ev in sim.events.drain(..) {
            match ev {
                Event::Birth { executor, .. } if executor == hid => hb += 1,
                Event::Birth { executor, .. } if Some(executor) == did => db += 1,
                Event::Death { id, .. } if id == hid => death = Some(t),
                _ => {}
            }
        }
        sim.cull_except(&keep);
        if let Some(o) = did.and_then(|d| sim.genome_of(d)) {
            dg = o.stats.drain_gain_m;
            ag = o.stats.absorb_gain_m;
        }
    }
    (db, hb, death.is_none(), death, dg as f64 / 1e3, ag as f64 / 1e3)
}

fn sun(op: u8, pct: i64, loss: i64, sun: i64) -> Config {
    let mut c = Config::default();
    c.patch_income *= sun;
    c.patch_cap *= sun;
    c.drain_op = op;
    c.drain_pct = pct;
    c.drain_loss_pct = loss;
    c
}

const HEAD: &str = "row                          | births  exact alive | host_x h_alv host_drnd | drain_gain absorb_gain  drains   fails ticks";

fn main() {
    let a: Vec<String> = std::env::args().skip(1).collect();
    let what = a.first().map(String::as_str).unwrap_or("g2");
    let ticks: u64 = 3000;
    let host = ancestor_t(ANCESTOR_T_K, 16);
    let alone = run_alone_with(&host, ticks, &cfg(0, 50, 50));
    println!("tierra ancestor alone, sun 2: {} exact births in {ticks} ticks", alone.exact_births);
    match what {
        "g1" => {
            let mut m = host.clone();
            m[8] ^= 1;
            println!("G1 mutant: byte 8 {:02x} -> {:02x}; {}", host[8], m[8], evo_core::record::disasm_in(&Isa::new(23), &m));
            println!("{HEAD}");
            for op in [0u8, 23, 25] {
                let r = run_with_host(&m, &host, ticks, &cfg(op, 50, 50));
                row(&format!("flip before anc, op {op}"), &r);
                let s = run_alone_with(&m, ticks, &cfg(op, 50, 50));
                println!("  alone op {op}: class {} births {} exact {} alive {}", s.class(), s.births, s.exact_births, s.alive);
            }
        }
        // The host seeded at its store cap instead of 100 units: is the
        // first-cycle death the harness's seed or the rule?
        "full" => {
            let k: i8 = a.get(1).and_then(|t| t.parse().ok()).unwrap_or(120);
            let isa = Isa::new(23);
            let d = drainer(&isa, k);
            println!("host seeded full; drainer K {k}");
            println!("   P   L | drainer_births host_births host_alive host_death_tick | host_drained drain_gain");
            for (p, l) in [(0, 50), (5, 50), (10, 50), (25, 0), (25, 50), (25, 90), (50, 50), (100, 50)] {
                let c = evo_core::harness::quiet(cfg(if p == 0 { 0 } else { 23 }, p, l));
                let mut sim = Sim::new(c.clone());
                let mid = c.world_size / 2;
                let full = c.store_cap_per_byte * host.len() as i64;
                let hid = sim.seed(mid, &host, full, 0);
                let mid_d = sim.seed(mid - d.len() as u32, &d, 100 * MILLI, 0);
                let (mut db, mut hb, mut death) = (0, 0, None);
                for t in 1..=ticks {
                    sim.run_tick();
                    for ev in sim.events.drain(..) {
                        match ev {
                            Event::Birth { executor, .. } if executor == hid => hb += 1,
                            Event::Birth { executor, .. } if executor == mid_d => db += 1,
                            Event::Death { id, .. } if id == hid => death = Some(t),
                            _ => {}
                        }
                    }
                    sim.cull_except(&[hid, mid_d]);
                }
                let (hd, dg) = (
                    sim.genome_of(hid).map_or(-1.0, |o| o.stats.drained_m as f64 / 1e3),
                    sim.genome_of(mid_d).map_or(-1.0, |o| o.stats.drain_gain_m as f64 / 1e3),
                );
                println!("{p:>4} {l:>3} | {db:>14} {hb:>11} {:>10} {:>15} | {hd:>12.1} {dg:>10.1}",
                         death.is_none(), death.map_or("-".to_string(), |t| t.to_string()));
            }
        }
        // Victims with slack (coordinator, 2026-10-15): the std ancestor at
        // sun 1 and 2, the tierra ancestor at sun 4; P 5, 10, 25; L 50; op 23.
        "slack" => {
            let k: i8 = a.get(1).and_then(|t| t.parse().ok()).unwrap_or(120);
            let d = drainer(&Isa::new(23), k);
            let std = evo_core::sim::ancestor(64, 16);
            println!("drainer K {k}, {} bytes; op 23, L 50; {ticks} ticks", d.len());
            println!("victim       sun seed |  P | drn_births drn_alone | vic_births vic_alone vic_alive death | drain_gain absorb_gain share");
            for (name, v, sn) in [("std K64", &std, 1i64), ("std K64", &std, 2), ("tierra K127", &host, 4)] {
                let full = Config::default().store_cap_per_byte * v.len() as i64;
                let drn_alone = run_alone_with(&d, ticks, &sun(23, 50, 50, sn)).exact_births;
                for (seed_name, he) in [("100", 100 * MILLI), ("full", full)] {
                    let (_, vic_alone, _, _, _, _) = pair(None, v, &sun(0, 50, 50, sn), he, ticks);
                    for p in [5, 10, 25] {
                        let (db, hb, alive, death, dg, ag) = pair(Some(&d), v, &sun(23, p, 50, sn), he, ticks);
                        println!("{name:<12} {sn:>3} {seed_name:>4} | {p:>2} | {db:>10} {drn_alone:>9} | {hb:>10} {vic_alone:>9} {alive:>9} {:>5} | {dg:>10.1} {ag:>11.1} {:>5.3}",
                                 death.map_or("-".to_string(), |t| t.to_string()), dg / (dg + ag));
                    }
                }
            }
        }
        "k" => {
            let k: i8 = a.get(1).and_then(|t| t.parse().ok()).unwrap_or(40);
            println!("{HEAD}");
            for kk in [k] {
                let isa = Isa::new(23);
                let d = drainer(&isa, kk);
                for (p, l) in [(5, 50), (10, 50), (25, 50), (50, 50)] {
                    let r = run_with_host(&d, &host, ticks, &cfg(23, p, l));
                    row(&format!("K {kk} P {p} L {l}"), &r);
                }
                let s = run_alone_with(&d, ticks, &cfg(23, 50, 50));
                println!("  alone: class {} exact {} alive {}", s.class(), s.exact_births, s.alive);
            }
        }
        _ => {
            let k: i8 = a.get(1).and_then(|t| t.parse().ok()).unwrap_or(120);
            println!("designed drainer K {k}, {} bytes", drainer(&Isa::new(23), k).len());
            println!("{HEAD}");
            for op in [23u8, 25] {
                let isa = Isa::new(op);
                let d = drainer(&isa, k);
                let off = run_with_host(&d, &host, ticks, &cfg(0, 50, 50));
                row(&format!("op {op} flag off (drain=pad)"), &off);
                for p in [25, 50, 100] {
                    for l in [0, 50, 90] {
                        let r = run_with_host(&d, &host, ticks, &cfg(op, p, l));
                        row(&format!("op {op} P {p:>3} L {l:>2}"), &r);
                    }
                }
            }
        }
    }
}
