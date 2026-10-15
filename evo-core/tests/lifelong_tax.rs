//! T10: the lifelong cycle tax (`--cycle-tax-lifelong F P`), the control
//! shaped like the theft (docs/tasks/T10-lifelong-tax-control.md). One PRNG
//! draw when an organism is created makes it taxed for life with
//! probability F; a body taxed for life loses P% of its cap every tick.
//! The snapshot continuation test under the flag is in `snapshots.rs`
//! (`lifelong_tax_survives_snapshot`); the energy ledger tests are
//! unchanged and still pass.

use evo_core::config::{Config, MILLI};
use evo_core::harness::{run_alone, run_alone_with};
use evo_core::sim::{ancestor, Event, Sim};

/// The standard one-founder world under `cfg`, as the CLI seeds it: the
/// K = 64 ancestor once at `world_size / 2`, 100 units, noise on.
fn seeded(cfg: Config) -> Sim {
    let mut sim = Sim::new(cfg);
    sim.seed_founders(&[(ancestor(64, 16), 1)], 100 * MILLI);
    sim
}

fn life(f: f64, p: i64) -> Config {
    let mut c = Config::default();
    c.cycle_tax_life_frac = f;
    c.cycle_tax_life_pct = p;
    c
}

/// State hash at every 500th tick of `ticks`, and the number of events.
fn census_hashes(mut sim: Sim, ticks: u64) -> (Vec<u64>, usize) {
    let (mut hs, mut n) = (Vec::new(), 0);
    for t in 1..=ticks {
        sim.run_tick();
        n += sim.events.drain(..).count();
        if t % 500 == 0 {
            hs.push(sim.state_hash());
        }
    }
    (hs, n)
}

#[test]
fn lifelong_tax_off_is_bit_identical() {
    // T10 §5 test 1: F = 0 or P = 0 taxes nobody and draws nothing, so the
    // world is the one with no flag at every census (the state hash covers
    // the PRNG, memory, pools and every organism). F = 0.5, P = 50 must
    // differ, or the comparison is empty.
    let none = census_hashes(seeded(Config::default()), 5000);
    assert!(none.1 > 1000, "only {} events: the test is vacuous", none.1);
    for (f, p) in [(0.0, 0), (0.0, 50), (0.5, 0)] {
        assert_eq!(census_hashes(seeded(life(f, p)), 5000), none, "F {f}, P {p}");
    }
    let on = census_hashes(seeded(life(0.5, 50)), 5000);
    assert_ne!(on.0.last(), none.0.last());
}

#[test]
fn lifelong_tax_debits_every_tick() {
    // T10 §5 test 2. In the harness, the K = 64 ancestor taxed for life at
    // P = 50 (F = 1, no draw) runs on half its cap and makes about half its
    // lone exact births: within 0.1 of T02 gate 1's 0.465 (theft N = 50).
    let host = ancestor(64, 16);
    let alone = run_alone(&host, 3000).exact_births;
    let taxed = run_alone_with(&host, 3000, &life(1.0, 50));
    let ratio = taxed.exact_births as f64 / alone as f64;
    eprintln!("ancestor alone: {alone} exact births in 3000 ticks; taxed for life at 50%: {} ({ratio:.3})",
              taxed.exact_births);
    assert!(taxed.alive && !taxed.stopped_early);
    assert!((ratio - 0.465).abs() <= 0.1, "ratio {ratio:.3}");

    // Every body is taxed every tick it runs. A body is first processed the
    // tick after it is created and is killed at the upkeep of the tick it
    // dies in, before the tax, so a death of age a paid a - 1 taxes (one
    // tick short of a x 16,000), and a living body of age a paid a. Default
    // world, noise on, F = 1, P = 50, 3,000 ticks.
    let cfg = life(1.0, 50);
    let per_tick = cfg.cap_c0 * 50 / 100;
    assert_eq!(per_tick, 16_000);
    let mut sim = seeded(cfg);
    let mut deaths = 0;
    for _ in 0..3000 {
        sim.run_tick();
        for ev in sim.events.drain(..) {
            if let Event::Death { age, stats, taxed_for_life, .. } = ev {
                assert!(taxed_for_life);
                assert_eq!(stats.cycles_taxed_m, (age as i64 - 1) * per_tick, "death at age {age}");
                deaths += 1;
            }
        }
    }
    let living: Vec<_> = sim.orgs.iter().filter(|o| o.alive).collect();
    assert!(deaths > 100 && living.len() > 10, "{deaths} deaths, {} living: the test is weak", living.len());
    for o in living {
        assert!(o.taxed_for_life);
        assert_eq!(o.stats.cycles_taxed_m, (sim.tick - o.birth_tick) as i64 * per_tick, "organism {}", o.id);
    }
    eprintln!("F = 1, P = 50, 3000 ticks: {deaths} deaths, every one taxed (age - 1) x 16,000");
}

#[test]
fn lifelong_tax_is_drawn_at_birth() {
    // T10 §5 test 3: F = 0.5, P = 100, so a body taxed for life never runs
    // an instruction. Default world, noise on, 3,000 ticks; eight founders,
    // so the world does not hang on one draw. About half the deaths are of
    // taxed bodies, and no taxed body, dead or alive, ever executed.
    let mut sim = Sim::new(life(0.5, 100));
    sim.seed_founders(&[(ancestor(64, 16), 8)], 100 * MILLI);
    let (mut deaths, mut taxed) = (0u64, 0u64);
    for _ in 0..3000 {
        sim.run_tick();
        for ev in sim.events.drain(..) {
            if let Event::Death { stats, taxed_for_life, .. } = ev {
                deaths += 1;
                if taxed_for_life {
                    taxed += 1;
                    assert_eq!(stats.executed, 0);
                    assert_eq!(stats.cycles_taxed_m, (stats.starved_ticks as i64) * sim.cfg.cap_c0);
                }
            }
        }
    }
    let living_taxed = sim.orgs.iter().filter(|o| o.alive && o.taxed_for_life).count();
    for o in sim.orgs.iter().filter(|o| o.taxed_for_life) {
        assert_eq!(o.stats.executed, 0, "organism {}", o.id);
    }
    let share = taxed as f64 / deaths as f64;
    eprintln!("F = 0.5, P = 100, 3000 ticks: {taxed} of {deaths} deaths taxed for life ({share:.4}); \
               {} living, {living_taxed} of them taxed", sim.alive_count());
    assert!(deaths > 1000, "only {deaths} deaths: the test is weak");
    assert!((0.45..=0.55).contains(&share), "share {share:.4}");
}

#[test]
fn version_1_snapshot_reads_as_the_untaxed_world() {
    // `tests/data/state_v1_world2048_seed3_t300.bin` was written by the
    // engine before T10 (format version 1, as every E016 snapshot):
    // `evo-core --seed 3 --world 2048 --ticks 300 --state-every 300`.
    // This build reads it as the world with no lifelong tax: no body is
    // taxed, and it is exactly the state this build reaches running the
    // same command, so the engine with the tax off is the old one. Saved
    // again it is a version 2 file. A run that sets the tax is refused.
    let file = std::fs::read(concat!(env!("CARGO_MANIFEST_DIR"), "/tests/data/state_v1_world2048_seed3_t300.bin")).unwrap();
    assert_eq!(&file[8..12], &1u32.to_le_bytes());
    let mut cfg = Config::default();
    cfg.world_size = 2048;
    let old = Sim::load_state(&mut file.as_slice(), cfg.clone()).unwrap();
    assert_eq!((old.tick, old.cfg.seed), (300, 3));
    assert!(old.orgs.len() > 5 && old.orgs.iter().all(|o| !o.taxed_for_life));
    cfg.seed = 3;
    let mut fresh = Sim::new(cfg.clone());
    fresh.seed_founders(&[(ancestor(64, 16), 1)], 100 * MILLI);
    for _ in 0..300 {
        fresh.run_tick();
    }
    assert_eq!(old.state_hash(), fresh.state_hash());
    let save = |s: &Sim| {
        let mut b = Vec::new();
        s.save_state(&mut b).unwrap();
        b
    };
    let (a, b) = (save(&old), save(&fresh));
    assert_eq!(&a[8..12], &2u32.to_le_bytes());
    assert!(a == b, "the v1 file, saved again, differs from this build's own state at tick 300");
    let mut taxed = cfg.clone();
    taxed.cycle_tax_life_frac = 0.3;
    taxed.cycle_tax_life_pct = 60;
    let e = Sim::load_state(&mut file.as_slice(), taxed).err().unwrap().to_string();
    assert!(e.contains("cycle_tax_life_frac") && e.contains("version 1"), "{e}");
}
