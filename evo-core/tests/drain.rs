//! T12: `drain`, the income take that keeps the victim's next upkeep
//! (docs/tasks/T12-drain-income-take.md). The no-target cases are unit
//! tests in `sim.rs` (`drain_needs_a_living_other_owner`), where `step` is
//! reachable; the harness gate's tables are printed by
//! `examples/drain_gate.rs`.

use evo_core::config::{Config, MILLI};
use evo_core::harness;
use evo_core::isa::{encode, Isa, Op};
use evo_core::sim::{ancestor, ancestor_t, Event, OrgStats, Sim, ANCESTOR_T_K};

/// The designed drainer of the gate (G2), 26 bytes, under `isa`: A is set
/// to the byte after its own body (the neighbour's byte 0 when it sits
/// immediately before one), then a loop of K = `k` rounds of `drain ;
/// absorb`, then the 21-byte ancestor's copy procedure with E = 16.
pub fn drainer(isa: &Isa, k: i8) -> Vec<u8> {
    isa.assemble(&format!(
        "self
add B
lit C {k}
lit D -5
drain
absorb
dec C
skipz C
jmpr D
self
swap B
swap C
alloc C
lit D -4
copy
dec C
skipz C
jmpr D
lit A 16
divide A
self
jmpa A
"
    ))
    .unwrap()
}

/// `tierra_n0`'s physics (`--sun 2`, the fixed edge) with `drain` at `op`.
fn tierra_n0(op: u8, pct: i64, loss: i64) -> Config {
    let mut c = Config::default();
    c.patch_income *= 2;
    c.patch_cap *= 2;
    c.drain_op = op;
    c.drain_pct = pct;
    c.drain_loss_pct = loss;
    c
}

/// The standard one-founder world under `cfg`, noise on: the state hash at
/// every census (every 1,000 ticks) of 5,000.
fn census_hashes(cfg: Config) -> Vec<u64> {
    let mut sim = Sim::new(cfg);
    sim.seed_founders(&[(ancestor(64, 16), 1)], 100 * MILLI);
    let mut out = Vec::new();
    for t in 1..=5000u64 {
        sim.run_tick();
        sim.events.clear();
        if t % 1000 == 0 {
            out.push(sim.state_hash());
        }
    }
    out
}

#[test]
fn drain_off_is_bit_identical() {
    // `--drain-pct 50 --drain-loss-pct 50` (and other values) without
    // `--drain-op` is the world with no flag at every census. T08's three
    // pinned hashes are checked by `legacy_flag_is_bit_identical_to_head`
    // (tests/pending_range.rs), unchanged.
    let none = census_hashes(Config::default());
    let mut c = Config::default();
    c.drain_pct = 50;
    c.drain_loss_pct = 50;
    assert_eq!(census_hashes(c), none);
    let mut c = Config::default();
    c.drain_pct = 100;
    c.drain_loss_pct = 0;
    assert_eq!(census_hashes(c), none);
    // The keys are in meta.json and the snapshot config text.
    let f = Config::default().fields();
    for k in ["drain_op", "drain_pct", "drain_loss_pct"] {
        assert!(f.iter().any(|(n, _)| *n == k), "{k} not in Config::fields");
    }
}

#[test]
fn absorb_flip_is_drain_at_23() {
    let g = ancestor_t(ANCESTOR_T_K, 16);
    assert_eq!(g[8], encode(Op::Absorb, 0), "the tierra ancestor's absorb is byte 8");
    let flipped = g[8] ^ 1;
    assert_eq!(Isa::new(23).decode(flipped).0, Op::Drain);
    assert_eq!(Isa::new(25).decode(flipped).0, Op::Pad);
    assert_eq!(Isa::BASE.decode(flipped).0, Op::Pad);
    assert_eq!(Isa::new(0), Isa::BASE);
    // Op 25 is four bits from absorb, and decodes there only.
    assert_eq!((22u8 ^ 25).count_ones(), 4);
    assert_eq!(Isa::new(25).decode(25 | 7 << 5).0, Op::Drain);
    assert_eq!(Isa::new(23).decode(25).0, Op::Pad);
    // A world's `Sim` decodes with its own table.
    let sim = Sim::new(tierra_n0(23, 50, 50));
    assert_eq!(sim.isa.decode(flipped).0, Op::Drain);
    assert_eq!(Sim::new(Config::default()).isa.decode(flipped).0, Op::Pad);
    // The assembler, disassembler and canonical form follow the table.
    let isa = Isa::new(23);
    assert_eq!(isa.assemble("drain\n").unwrap(), vec![23]);
    assert_eq!(Isa::new(25).assemble("drain 3\n").unwrap(), vec![25 | 3 << 5]);
    assert!(evo_core::isa::assemble("drain\n").is_err());
    assert_eq!(isa.disasm_at(&[23 | 2 << 5], 0).0, "drain");
    assert_eq!(evo_core::isa::disasm_at(&[23], 0).0, "pad");
    assert_eq!(isa.canonical(&[23 | 5 << 5]), vec![23]);
    assert_eq!(evo_core::isa::canonical(&[23 | 5 << 5]), vec![0]);
}

#[test]
fn drain_takes_from_income_and_cannot_kill() {
    // The designed drainer immediately before the tierra ancestor under
    // tierra_n0 + `--drain-op 23`, quiet, children culled every tick, 3,000
    // ticks. The ancestor is drained, never dies, and per tick loses no
    // more than its open window allows: what was left of the window at
    // the start of the tick plus a fresh window of income_prev × P / 100
    // (each turn opens one; the take in a turn never exceeds it). A take
    // never leaves it below its next upkeep. P = 5 and the drainer at
    // K = 120 (a replicator alone): the window rule is what is tested
    // here, not the gate (examples/drain_gate.rs). From P = 10 this host,
    // seeded with 100 units, is drained to its upkeep floor before its
    // first child and then dies: keeping one upkeep is not survival (the
    // gate's finding).
    let pct = 5;
    let cfg = harness::quiet(tierra_n0(23, pct, 50));
    let isa = Isa::new(23);
    let d = drainer(&isa, 120);
    let host = ancestor_t(ANCESTOR_T_K, 16);
    let mut sim = Sim::new(cfg.clone());
    let mid = cfg.world_size / 2;
    let host_id = sim.seed(mid, &host, 100 * MILLI, 0);
    let me_id = sim.seed(mid - d.len() as u32, &d, 100 * MILLI, 0);
    let (mut host_births, mut max_tick_take) = (0, 0);
    for _ in 0..3000 {
        let h = sim.genome_of(host_id).expect("host alive");
        let (left0, drained0) = (h.drain_left_m, h.stats.drained_m);
        sim.run_tick();
        for ev in sim.events.drain(..) {
            match ev {
                Event::Death { id, cause, .. } => assert_ne!(id, host_id, "host died ({cause:?})"),
                Event::Birth { executor, .. } if executor == host_id => host_births += 1,
                _ => {}
            }
        }
        sim.cull_except(&[host_id, me_id]);
        let h = sim.genome_of(host_id).unwrap();
        let took = h.stats.drained_m - drained0;
        assert!(took <= left0 + h.income_prev_m * pct / 100, "took {took}, window {left0} + {}", h.income_prev_m * pct / 100);
        assert!(h.energy >= 0);
        max_tick_take = max_tick_take.max(took);
    }
    let h = sim.genome_of(host_id).unwrap();
    let me = sim.genome_of(me_id).unwrap();
    assert!(h.alive);
    assert!(h.stats.drained_m > 0, "the host was never drained");
    assert!(me.stats.drain_gain_m > 0);
    assert!(host_births > 0);
    eprintln!("P {pct}: host drained {:.1} units, {host_births} births; drainer gained {:.1} by drain, {:.1} by absorb; max take per tick {:.3}",
              h.stats.drained_m as f64 / 1e3, me.stats.drain_gain_m as f64 / 1e3, me.stats.absorb_gain_m as f64 / 1e3, max_tick_take as f64 / 1e3);
}

#[test]
fn drain_ledger_balances() {
    // The standard world (noise on) with `drain` at 23, P = 50, L = 30: two
    // designed drainers, each immediately before an ancestor, 2,000 ticks,
    // so the world fills with drainers, hosts and their mutants. Every
    // store balances against its ledger with the two drain terms (the
    // living at every tick, the dead at their death row); the world
    // conserves energy; and the dissipated total, Σ drained − Σ gained,
    // is Σ floor(take × L / 100): at most Σ drained × L / 100 and less than
    // that by under one milli-unit per take.
    let mut cfg = Config::default();
    cfg.drain_op = 23;
    cfg.drain_pct = 50;
    cfg.drain_loss_pct = 30;
    let isa = Isa::new(23);
    let d = drainer(&isa, 40);
    let mut sim = Sim::new(cfg.clone());
    let seed_energy = 100 * MILLI;
    let mut seeded = 0;
    for at in [10_000u32, 40_000] {
        sim.seed(at, &ancestor(64, 16), seed_energy, 0);
        sim.seed(at - d.len() as u32, &d, seed_energy, 0);
        seeded += 2;
    }
    let ledger = |energy: i64, s: &OrgStats| {
        assert_eq!(
            energy,
            s.born_with_m + s.absorb_gain_m + s.drain_gain_m + s.gained_from_others_m
                - s.spent_m - s.drained_m - s.upkeep_m - s.endowed_m
        );
        assert!(s.drains_fail <= s.drains);
    };
    let (mut drained, mut gained, mut takes) = (0i64, 0i64, 0u64);
    for _ in 0..2000 {
        sim.run_tick();
        for ev in sim.events.drain(..) {
            if let Event::Death { energy, stats, .. } = ev {
                ledger(energy, &stats);
                drained += stats.drained_m;
                gained += stats.drain_gain_m;
                takes += stats.drains - stats.drains_fail;
            }
        }
        for o in sim.orgs.iter().filter(|o| o.alive) {
            ledger(o.energy, &o.stats);
        }
    }
    for o in sim.orgs.iter().filter(|o| o.alive) {
        drained += o.stats.drained_m;
        gained += o.stats.drain_gain_m;
        takes += o.stats.drains - o.stats.drains_fail;
    }
    assert!(drained > 0 && takes > 0, "no drain took anything");
    let lost = drained - gained;
    let l = cfg.drain_loss_pct;
    assert!(lost * 100 <= drained * l, "lost {lost} > {drained} x {l}%");
    assert!(drained * l - lost * 100 < 100 * takes as i64, "lost {lost}, {drained} x {l}%, {takes} takes");
    let initial_pools = sim.patches.len() as i64 * sim.cfg.patch_cap;
    let lhs = seeded * seed_energy + initial_pools + sim.energy_in;
    let rhs = sim.energy_in_organisms() + sim.energy_in_patches() + sim.energy_out + sim.energy_overflow;
    assert_eq!(lhs, rhs);
    eprintln!("2000 ticks: {takes} takes, {:.1} units drained, {:.1} gained, {:.1} dissipated, {} alive",
              drained as f64 / 1e3, gained as f64 / 1e3, lost as f64 / 1e3, sim.alive_count());
}

#[test]
fn drain_snapshot_round_trips() {
    // The drain state (income window) is physics: a drain world saved and
    // loaded continues bit for bit.
    let cfg = tierra_n0(23, 50, 50);
    let isa = Isa::new(23);
    let mut a = Sim::new(cfg.clone());
    a.seed_founders(&[(ancestor_t(ANCESTOR_T_K, 16), 1), (drainer(&isa, 40), 1)], 100 * MILLI);
    for _ in 0..800 {
        a.run_tick();
        a.events.clear();
    }
    let mut buf = Vec::new();
    a.save_state(&mut buf).unwrap();
    let mut b = Sim::load_state(&mut buf.as_slice(), cfg.clone()).unwrap();
    assert_eq!(a.state_hash(), b.state_hash());
    for _ in 0..500 {
        a.run_tick();
        a.events.clear();
        b.run_tick();
        b.events.clear();
    }
    assert_eq!(a.state_hash(), b.state_hash());
    // The config must match: a drain-off run refuses the file.
    let e = Sim::load_state(&mut buf.as_slice(), Config::default()).err().unwrap().to_string();
    assert!(e.contains("patch_income") || e.contains("drain_op"), "{e}");
}
