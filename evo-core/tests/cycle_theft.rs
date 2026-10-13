//! E014: cycle theft (`--cycle-theft-pct N`) and its control, the random
//! cycle tax (`--cycle-tax-pct P --cycle-tax-frac F`). docs/tasks/T02-cycle-theft.md.
//!
//! An instruction one organism runs on another living organism's bytes
//! debits the owner's per-tick execution budget (time), never its energy
//! (matter). Gate 1, the two-genome harness, is in `harness.rs`
//! (`cycle_theft_slows_the_entered_host`).

use evo_core::config::{Config, MILLI};
use evo_core::sim::{ancestor, Event, OrgStats, Sim};

/// The standard one-founder world under `cfg`: the K = 64 ancestor once at
/// `world_size / 2`, 100 units, noise on.
fn seeded(cfg: Config) -> Sim {
    let mut sim = Sim::new(cfg);
    sim.seed(sim.cfg.world_size / 2, &ancestor(64, 16), 100 * MILLI, 0);
    sim
}

fn cfg(theft: i64, tax: i64, frac: f64) -> Config {
    let mut c = Config::default();
    c.cycle_theft_pct = theft;
    c.cycle_tax_pct = tax;
    c.cycle_tax_frac = frac;
    c
}

/// Run `ticks` ticks; return the state hash and the number of events.
fn run(mut sim: Sim, ticks: u64) -> (u64, usize) {
    let mut n = 0;
    for _ in 0..ticks {
        sim.run_tick();
        n += sim.events.drain(..).count();
    }
    (sim.state_hash(), n)
}

#[test]
fn cycle_theft_zero_is_the_default_world() {
    // N = 0 (and a tax of 0, whatever its frequency) is the world with no
    // flag, tick for tick: same state hash after 5,000 ticks, which covers
    // the PRNG, memory, pools and every organism's VM, energy and debt.
    // N = 50 in the same world must differ, or the comparison is empty.
    let none = run(seeded(Config::default()), 5000);
    assert!(none.1 > 1000, "only {} events: the test is vacuous", none.1);
    assert_eq!(run(seeded(cfg(0, 0, 1.0)), 5000), none);
    assert_eq!(run(seeded(cfg(0, 0, 0.5)), 5000), none);
    assert_ne!(run(seeded(cfg(50, 0, 1.0)), 5000).0, none.0);
}

#[test]
fn cycle_theft_leaves_energy_alone() {
    // N = 50, a `pad` immediately before the ancestor, noise on, so the
    // world fills with descendants and intruders of every kind. Energy is
    // conserved over the world and every store balances against its own
    // ledger (for the living at every tick, for the dead at their death
    // row), with nothing paid for or by others and nothing transferred.
    // The second arm adds the random tax at half the organisms per tick.
    for (tax, frac) in [(0, 1.0), (25, 0.5)] {
        let mut sim = Sim::new(cfg(50, tax, frac));
        let seed_energy = 100 * MILLI;
        let host = sim.seed(1000, &ancestor(64, 16), seed_energy, 0);
        sim.seed(999, &[0x00], seed_energy, 0);
        let ledger = |energy: i64, s: &OrgStats| {
            assert_eq!(energy, s.born_with_m + s.absorb_gain_m + s.gained_from_others_m - s.spent_m - s.upkeep_m - s.endowed_m);
            assert_eq!((s.paid_for_others_m, s.paid_by_others_m, s.gained_from_others_m), (0, 0, 0));
        };
        let (mut lost, mut taxed, mut host_lost) = (0, 0, 0);
        for _ in 0..2000 {
            sim.run_tick();
            for ev in sim.events.drain(..) {
                if let Event::Death { id, energy, stats, .. } = ev {
                    ledger(energy, &stats);
                    lost += stats.cycles_lost_m;
                    taxed += stats.cycles_taxed_m;
                    if id == host {
                        host_lost = stats.cycles_lost_m;
                    }
                }
            }
            for o in sim.orgs.iter().filter(|o| o.alive) {
                ledger(o.energy, &o.stats);
            }
        }
        for o in sim.orgs.iter().filter(|o| o.alive) {
            lost += o.stats.cycles_lost_m;
            taxed += o.stats.cycles_taxed_m;
            if o.id == host {
                host_lost = o.stats.cycles_lost_m;
            }
        }
        assert!(host_lost > 0, "tax {tax}: the pad never took the host's cycles");
        assert!(lost > 0);
        assert_eq!(taxed > 0, tax > 0, "tax {tax}");
        let initial_pools = sim.patches.len() as i64 * sim.cfg.patch_cap;
        let lhs = 2 * seed_energy + initial_pools + sim.energy_in;
        let rhs = sim.energy_in_organisms() + sim.energy_in_patches() + sim.energy_out + sim.energy_overflow;
        assert_eq!(lhs, rhs, "tax {tax}");
        eprintln!("theft N=50, tax {tax}% at {frac}, 2000 ticks: cycles lost {lost}, taxed {taxed} (milli-units)");
    }
}

#[test]
fn cycle_counters_agree_over_a_world() {
    // In the standard world, over every organism living or dead: the budget
    // intruders took equals the budget owners lost (N = 50), and the
    // instructions run on others' bytes equal the instructions others ran
    // on one's own (at N = 50 and at N = 0, where it is pure counting).
    const TICKS: u64 = 20_000;
    for theft in [50, 0] {
        let mut sim = seeded(cfg(theft, 0, 1.0));
        let (mut lost, mut taken, mut by_others, mut foreign) = (0i64, 0i64, 0u64, 0u64);
        let mut add = |s: &OrgStats| {
            lost += s.cycles_lost_m;
            taken += s.cycles_taken_m;
            by_others += s.exec_by_others;
            foreign += s.exec_foreign;
        };
        for _ in 0..TICKS {
            sim.run_tick();
            for ev in sim.events.drain(..) {
                if let Event::Death { stats, .. } = ev {
                    add(&stats);
                }
            }
        }
        for o in sim.orgs.iter().filter(|o| o.alive) {
            add(&o.stats);
        }
        assert!(sim.alive_count() > 0, "N {theft}: extinct");
        assert_eq!(lost, taken, "N {theft}");
        assert_eq!(by_others, foreign, "N {theft}");
        assert!(foreign > 0, "N {theft}: no foreign execution");
        if theft == 0 {
            assert_eq!(lost, 0);
        } else {
            assert!(lost > 0, "N {theft}: nothing taken");
        }
        eprintln!("N={theft}, {TICKS} ticks: {foreign} foreign instructions, {taken} milli-units of budget taken");
    }
}

#[test]
fn cycle_tax_frac_one_draws_nothing() {
    // Eight founders, noise on, one tick. A tax applied to every organism
    // (F = 1.0) draws nothing, so the PRNG stream matches the run with no
    // tax, although the taxed organisms ran less; at F = 0.5 there is one
    // draw per organism and the stream differs.
    let start = |c: Config| {
        let mut sim = Sim::new(c);
        sim.seed_founders(&[(ancestor(64, 16), 8)], 100 * MILLI);
        sim.run_tick();
        sim
    };
    let none = start(Config::default());
    let all = start(cfg(0, 25, 1.0));
    let half = start(cfg(0, 25, 0.5));
    assert_eq!(all.rng.state(), none.rng.state());
    assert_ne!(half.rng.state(), none.rng.state());
    let cap = Config::default().cap_c0;
    for (a, n) in all.orgs.iter().zip(&none.orgs) {
        assert_eq!(a.stats.cycles_taxed_m, cap / 4);
        assert!(a.stats.executed < n.stats.executed);
    }
}

#[test]
fn cycle_debt_carries_over() {
    // A host owing three caps runs nothing for three ticks (each a starved
    // tick: it pays upkeep and runs nothing), then all of the fourth, which
    // is the first tick of a host with no debt.
    let mut c = Config::default();
    c.p_write_flip = 0.0;
    c.q_slip = 0.0;
    c.p_bit_rot = 0.0;
    c.p_debris_decay = 0.0;
    let cap = c.cap_c0 + c.cap_c1 * ancestor(64, 16).len() as i64;
    let mut fresh = seeded(c.clone());
    fresh.run_tick();
    let mut sim = seeded(c);
    sim.orgs[0].cycle_debt = 3 * cap;
    for t in 1..=3 {
        sim.run_tick();
        let o = &sim.orgs[0];
        assert_eq!((o.stats.executed, o.stats.starved_ticks), (0, t), "tick {t}");
        assert_eq!(o.cycle_debt, (3 - t as i64) * cap, "tick {t}");
    }
    sim.run_tick();
    let (o, f) = (&sim.orgs[0], &fresh.orgs[0]);
    assert!(f.stats.executed > 0);
    assert_eq!((o.stats.executed, o.stats.spent_m, o.ip, o.regs), (f.stats.executed, f.stats.spent_m, f.ip, f.regs));
    assert_eq!((o.cycle_debt, o.stats.starved_ticks), (0, 3));
    // Theft and tax counters are untouched: the debt was set by hand.
    assert_eq!((o.stats.cycles_lost_m, o.stats.cycles_taxed_m), (0, 0));
}
