//! Acceptance tests for the instrumentation (docs/instrumentation.md).
//!
//! Rust note: files under `tests/` are integration tests. Each compiles as a
//! separate crate that sees only the public API of `evo_core`, like a Go
//! `package foo_test` file.

use evo_core::config::{Config, MILLI};
use evo_core::record::{Recorder, RunInfo};
use evo_core::sim::{ancestor, func_hash, fnv1a, Event, Sim};

const TICKS: u64 = 6000;

fn seeded(seed: u64) -> Sim {
    let mut cfg = Config::default();
    cfg.seed = seed;
    let mut sim = Sim::new(cfg.clone());
    sim.seed(cfg.world_size / 2, &ancestor(64, 16), 100 * MILLI, 0);
    sim
}

fn scratch(name: &str) -> std::path::PathBuf {
    let d = std::env::temp_dir().join(format!("evo-test-{name}-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&d);
    d
}

/// Run with noise on; return the full event stream and the final state hash.
fn run(seed: u64, record: Option<&std::path::Path>) -> (Vec<Event>, u64) {
    let mut sim = seeded(seed);
    let mut rec = record.map(|d| {
        let info = RunInfo { ticks_requested: TICKS, census_every: 50, ancestor_k: 64, ancestor_e: 16 };
        Recorder::create(d, &sim, info).unwrap()
    });
    let mut all = Vec::new();
    for _ in 0..TICKS {
        sim.run_tick();
        let evs: Vec<Event> = sim.events.drain(..).collect();
        if let Some(r) = rec.as_mut() {
            r.events(&sim, &evs).unwrap();
            if sim.tick % 50 == 0 {
                r.snapshot(&sim).unwrap();
            }
        }
        all.extend(evs);
    }
    if let Some(r) = rec {
        r.finish(&sim).unwrap();
    }
    (all, sim.state_hash())
}

#[test]
fn same_seed_same_run() {
    let (ea, ha) = run(2, None);
    let (eb, hb) = run(2, None);
    assert!(ea.iter().any(|e| matches!(e, Event::Birth { .. })), "no births: test is vacuous");
    assert!(ea.iter().any(|e| matches!(e, Event::Death { .. })), "no deaths: test is vacuous");
    assert_eq!(ea, eb);
    assert_eq!(ha, hb);
    let (_, hc) = run(3, None);
    assert_ne!(ha, hc, "different seeds should diverge");
}

#[test]
fn recorder_does_not_perturb() {
    let dir = scratch("perturb");
    let (ea, ha) = run(2, None);
    let (eb, hb) = run(2, Some(&dir));
    assert_eq!(ea, eb);
    assert_eq!(ha, hb);
    for f in ["meta.json", "births.csv", "deaths.csv", "census.csv", "orgs.csv", "patches.csv", "genomes.csv"] {
        let text = std::fs::read_to_string(dir.join(f)).unwrap();
        assert!(text.lines().count() >= 2, "{f} has no data rows");
    }
    let births = std::fs::read_to_string(dir.join("births.csv")).unwrap();
    let n_births = ea.iter().filter(|e| matches!(e, Event::Birth { .. })).count();
    assert_eq!(births.lines().count() - 1, n_births);
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn ledger_balances_for_every_living_organism() {
    let mut sim = seeded(2);
    for _ in 0..TICKS {
        sim.run_tick();
        sim.events.clear();
        if sim.tick % 500 == 0 {
            for o in sim.orgs.iter().filter(|o| o.alive) {
                let s = &o.stats;
                assert_eq!(
                    o.energy,
                    s.born_with_m + s.absorb_gain_m - s.spent_m - s.upkeep_m - s.endowed_m,
                    "org {} at tick {}", o.id, sim.tick
                );
                assert!(s.max_energy_m >= o.energy);
            }
        }
    }
    // Patch totals agree with the organisms' absorb totals.
    let absorbed: i64 = sim.patches.iter().map(|p| p.absorbed).sum();
    assert_eq!(absorbed, sim.absorb_gain_total());
}

#[test]
fn func_hash_ignores_encoding_aliases() {
    let g = ancestor(64, 16);
    let mut alias = g.clone();
    alias[1] |= 0b100 << 5; // `swap B` through its second encoding
    assert_ne!(fnv1a(&alias), fnv1a(&g));
    assert_eq!(func_hash(&alias), func_hash(&g));
    let mut mutant = g.clone();
    mutant[8] = evo_core::isa::encode(evo_core::isa::Op::Dec, evo_core::isa::REG_B);
    assert_ne!(func_hash(&mutant), func_hash(&g));
}
