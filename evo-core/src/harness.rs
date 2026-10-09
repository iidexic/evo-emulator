//! Single-genome harness (PLAN.md §7): run one genome alone in a clean,
//! noiseless world and see what it does. Used to label genomes from a run
//! by test (`--classify`), not by reading their disassembly.

use crate::config::{Config, MILLI};
use crate::sim::{fnv1a, Event, Sim, FIRST_ID};

pub struct HarnessResult {
    pub births: u32,
    /// Children whose bytes equal the tested genome.
    pub exact_births: u32,
    /// Tick of the first birth, -1 if none.
    pub first_birth_tick: i64,
    pub alive: bool,
    pub final_energy: i64,
    pub executed: u64,
    pub absorbs: u64,
    /// Ticks actually simulated: `ticks`, or fewer if the genome died first.
    pub ticks_run: u64,
    /// The loop stopped before `ticks` because the genome died.
    pub stopped_early: bool,
}

impl HarnessResult {
    /// `replicator`: at least 2 exact children. `one_shot`: exactly one
    /// child, an exact one, and nothing after it in the harness run (a
    /// working copy loop whose tail leaves the body for good; E005 found
    /// these making 29–53% of the dependent class's exact births, each
    /// carrier one child). `inexact`: some children but fewer than 2 exact,
    /// not a one-shot. `loafer`: no children, still alive. `dies`: no
    /// children, died alone.
    pub fn class(&self) -> &'static str {
        if self.exact_births >= 2 {
            "replicator"
        } else if self.births == 1 && self.exact_births == 1 {
            "one_shot"
        } else if self.births >= 1 {
            "inexact"
        } else if self.alive {
            "loafer"
        } else {
            "dies"
        }
    }
}

/// Config the harness runs under: defaults with every noise source off.
pub fn quiet_config() -> Config {
    quiet(Config::default())
}

/// `cfg` with every noise source off.
pub fn quiet(mut cfg: Config) -> Config {
    cfg.p_write_flip = 0.0;
    cfg.q_slip = 0.0;
    cfg.p_bit_rot = 0.0;
    cfg.p_debris_decay = 0.0;
    cfg
}

/// Run `genome` alone for `ticks` ticks with 100 units of seed energy,
/// removing its children at the end of every tick. Default physics.
pub fn run_alone(genome: &[u8], ticks: u64) -> HarnessResult {
    run_alone_with(genome, ticks, &Config::default())
}

/// `run_alone` under `cfg`'s physics, noise off (E005: world-physics class).
pub fn run_alone_with(genome: &[u8], ticks: u64, cfg: &Config) -> HarnessResult {
    let cfg = quiet(cfg.clone());
    let mut sim = Sim::new(cfg.clone());
    sim.seed(cfg.world_size / 2, genome, 100 * MILLI, 0);
    let me = fnv1a(genome);
    let mut r = HarnessResult {
        births: 0,
        exact_births: 0,
        first_birth_tick: -1,
        alive: true,
        final_energy: 0,
        executed: 0,
        absorbs: 0,
        ticks_run: 0,
        stopped_early: false,
    };
    for t in 0..ticks {
        sim.run_tick();
        for ev in sim.events.drain(..) {
            if let Event::Birth { tick, genome_hash, .. } = ev {
                r.births += 1;
                if genome_hash == me {
                    r.exact_births += 1;
                }
                if r.first_birth_tick < 0 {
                    r.first_birth_tick = tick as i64;
                }
            }
        }
        sim.cull_all_but(FIRST_ID);
        r.ticks_run = t + 1;
        if !sim.orgs[0].alive {
            r.stopped_early = r.ticks_run < ticks;
            break;
        }
    }
    // The genome is orgs[0] while alive, and until the next tick once dead.
    let o = &sim.orgs[0];
    r.alive = o.alive;
    r.final_energy = o.energy;
    r.executed = o.stats.executed;
    r.absorbs = o.stats.absorbs;
    r
}

/// Two-genome harness result (E005): `genome` placed immediately before
/// `host`, both with 100 units of seed energy, children removed every tick.
pub struct HostResult {
    /// Children whose `divide` was executed by the genome.
    pub births: u32,
    /// Of those, children whose bytes equal the genome.
    pub exact_births: u32,
    /// Children whose `divide` was executed by the genome and equal the host
    /// (the genome ran the host's loop under `self_owner`).
    pub host_copies: u32,
    /// Children whose `divide` was executed by the host and equal the host.
    pub host_exact_births: u32,
    pub alive: bool,
    pub host_alive: bool,
    pub executed: u64,
    /// Of the genome's instructions, how many ran at an address the host owned.
    pub exec_foreign: u64,
    /// Ticks actually simulated: `ticks`, or fewer if the genome died first
    /// (the host is not run on alone).
    pub ticks_run: u64,
    /// The loop stopped before `ticks` because the genome died. A run that
    /// stops early is not evidence of a resistant host (E007: a one-byte
    /// `pad` before a host with endowment 35 or more starves within a few
    /// hundred ticks).
    pub stopped_early: bool,
}

/// Run `genome` immediately before `host` under `cfg`'s physics, noise off,
/// for `ticks` ticks. Says whether the genome reproduces by falling into
/// the host (foreign execution), without reading its disassembly.
pub fn run_with_host(genome: &[u8], host: &[u8], ticks: u64, cfg: &Config) -> HostResult {
    let cfg = quiet(cfg.clone());
    let mut sim = Sim::new(cfg.clone());
    let mid = cfg.world_size / 2;
    let host_id = sim.seed(mid, host, 100 * MILLI, 0);
    let me_id = sim.seed(mid.wrapping_sub(genome.len() as u32), genome, 100 * MILLI, 0);
    let (me, hh) = (fnv1a(genome), fnv1a(host));
    let mut r = HostResult {
        births: 0,
        exact_births: 0,
        host_copies: 0,
        host_exact_births: 0,
        alive: true,
        host_alive: true,
        executed: 0,
        exec_foreign: 0,
        ticks_run: 0,
        stopped_early: false,
    };
    for t in 0..ticks {
        sim.run_tick();
        for ev in sim.events.drain(..) {
            if let Event::Birth { executor, genome_hash, .. } = ev {
                if executor == me_id {
                    r.births += 1;
                    if genome_hash == me {
                        r.exact_births += 1;
                    } else if genome_hash == hh {
                        r.host_copies += 1;
                    }
                } else if executor == host_id && genome_hash == hh {
                    r.host_exact_births += 1;
                }
            }
        }
        sim.cull_except(&[host_id, me_id]);
        r.ticks_run = t + 1;
        if !sim.genome_of(me_id).map_or(false, |o| o.alive) {
            r.stopped_early = r.ticks_run < ticks;
            break;
        }
    }
    // A dead organism stays readable until the next tick; a host that died
    // earlier has been retired, which counts as dead.
    let me_org = sim.genome_of(me_id).expect("genome readable at the tick it died or later");
    r.alive = me_org.alive;
    r.host_alive = sim.genome_of(host_id).map_or(false, |o| o.alive);
    r.executed = me_org.stats.executed;
    r.exec_foreign = me_org.stats.exec_foreign;
    r
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::isa::assemble;
    use crate::sim::ancestor;

    #[test]
    fn one_byte_pad_reproduces_through_a_host() {
        // E005 mechanism: a body that falls off its end into a replicator
        // runs the host's loop, and `self` makes that loop copy the body.
        let g = assemble("pad\n").unwrap();
        let host = ancestor(64, 16);
        let r = run_with_host(&g, &host, 3000, &Config::default());
        assert!(r.exact_births >= 10, "only {} exact births", r.exact_births);
        assert!(r.alive && r.host_alive);
        assert!(r.exec_foreign * 10 > r.executed * 9, "foreign {} of {}", r.exec_foreign, r.executed);
        assert!(r.host_exact_births >= 10);
        // Alone it is `dies`: the harness class is what makes it dependent.
        assert_eq!(run_alone(&g, 3000).class(), "dies");
    }

    #[test]
    fn harness_says_when_the_intruder_died_first() {
        // E007 caveat: a one-byte `pad` before a host whose divide endowment
        // is 35 or more gives its first child nearly everything and starves,
        // and the harness stops; at 34 it lives through the whole run.
        let g = assemble("pad\n").unwrap();
        assert_eq!(g, vec![0x00]);
        let cfg = Config::default();
        let r35 = run_with_host(&g, &ancestor(64, 35), 3000, &cfg);
        assert!(r35.stopped_early);
        assert!(r35.ticks_run < 3000, "ran {} ticks", r35.ticks_run);
        assert!(r35.exact_births <= 2, "{} exact births", r35.exact_births);
        assert!(!r35.alive);
        let r34 = run_with_host(&g, &ancestor(64, 34), 3000, &cfg);
        assert!(!r34.stopped_early);
        assert_eq!(r34.ticks_run, 3000);
        assert_eq!(r34.exact_births, 340);
        // The single-genome harness reports the same way.
        let alone = run_alone(&g, 3000);
        assert!(alone.stopped_early && alone.ticks_run < 3000);
        assert!(!run_alone(&ancestor(64, 16), 3000).stopped_early);
    }

    #[test]
    fn self_owner_makes_the_intruder_copy_the_host() {
        // E006 (H8): with `self` naming the owner of the byte at IP, a body
        // of pads that falls into the host runs the host's loop and produces
        // host copies, paid for by its own energy; none of its children
        // equal itself. A one-byte body cannot: its store cap (64 per body
        // byte) is below the cost of one host cycle, so it starves.
        let host = ancestor(64, 16);
        let mut cfg = Config::default();
        cfg.self_owner = true;
        let g = vec![0u8; 21];
        let r = run_with_host(&g, &host, 3000, &cfg);
        assert_eq!(r.exact_births, 0);
        assert!(r.host_copies >= 10, "only {} host copies", r.host_copies);
        assert!(r.exec_foreign * 10 > r.executed * 9);
        let one = run_with_host(&assemble("pad\n").unwrap(), &host, 3000, &cfg);
        assert_eq!(one.births, 0);
        assert!(!one.alive);
        // Alone, `self` still names the executor: the ancestor is unchanged.
        assert_eq!(run_alone_with(&host, 3000, &cfg).class(), "replicator");
    }

    #[test]
    fn charge_owner_makes_the_pad_kill_its_host() {
        // E008: with the owner of the byte at IP paying, the one-byte `pad`
        // runs the host's loop on the host's energy. The host (paying for
        // both) dies at tick 11 before its first child; its bytes become
        // debris but keep their code, and the pad goes on running them at
        // its own cost. Its births are bounded by its per-tick cap, not by
        // who pays, so they are the flag-off count again. Flag off: pad
        // 340 exact births, host 211.
        let g = assemble("pad\n").unwrap();
        let host = ancestor(64, 16);
        let off = run_with_host(&g, &host, 3000, &Config::default());
        assert_eq!((off.exact_births, off.host_exact_births), (340, 211));
        let mut cfg = Config::default();
        cfg.charge_owner = true;
        let on = run_with_host(&g, &host, 3000, &cfg);
        assert_eq!((on.births, on.exact_births, on.host_exact_births), (340, 340, 0));
        assert_ne!(on.host_exact_births, off.host_exact_births);
        assert!(on.alive && !on.host_alive && !on.stopped_early);
        // Foreign execution only while the host lived.
        assert_eq!(on.exec_foreign, 275);
    }

    #[test]
    fn charge_owner_leaves_a_lone_genome_alone() {
        // No foreign execution, so nothing changes.
        let mut cfg = Config::default();
        cfg.charge_owner = true;
        let off = run_alone(&ancestor(64, 16), 3000);
        let on = run_alone_with(&ancestor(64, 16), 3000, &cfg);
        assert_eq!(on.exact_births, off.exact_births);
        assert_eq!((on.births, on.executed, on.final_energy), (off.births, off.executed, off.final_energy));
    }

    #[test]
    fn charge_owner_pct_splits_the_pad_cost() {
        // E009: the split charge with `pad` before the ancestor. The pad's
        // births never change (its per-tick cap sets them, and an owner at
        // zero never stops it). The host pays its share and makes the
        // flag-off 211 children up to 8%, because it rides at its store cap
        // and pays out of energy it could not have kept; from 9% it dies.
        let g = assemble("pad\n").unwrap();
        let host = ancestor(64, 16);
        let off = run_with_host(&g, &host, 3000, &Config::default());
        let at = |pct: i64| {
            let mut cfg = Config::default();
            cfg.charge_owner_pct = pct;
            run_with_host(&g, &host, 3000, &cfg)
        };
        let zero = at(0);
        assert_eq!(
            (zero.births, zero.exact_births, zero.host_exact_births, zero.executed, zero.exec_foreign),
            (off.births, off.exact_births, off.host_exact_births, off.executed, off.exec_foreign)
        );
        assert_eq!((at(8).exact_births, at(8).host_exact_births, at(8).host_alive), (340, 211, true));
        let ten = at(10);
        assert_eq!((ten.exact_births, ten.host_exact_births), (340, 13));
        assert!(ten.alive && !ten.host_alive && !ten.stopped_early);
        // N = 100 is not E008: the host pays everything while it has
        // anything, then the pad pays full price instead of stopping.
        let all = at(100);
        assert_eq!((all.exact_births, all.host_exact_births, all.host_alive), (340, 0, false));
        let mut e008 = Config::default();
        e008.charge_owner = true;
        let e008 = run_with_host(&g, &host, 3000, &e008);
        assert_ne!(all.exec_foreign, e008.exec_foreign);
        // With both flags set, `charge_owner` wins.
        let mut both = Config::default();
        both.charge_owner = true;
        both.charge_owner_pct = 50;
        let both = run_with_host(&g, &host, 3000, &both);
        assert_eq!((both.executed, both.exec_foreign), (e008.executed, e008.exec_foreign));
    }

    #[test]
    fn charge_owner_pct_leaves_a_lone_genome_alone() {
        let mut cfg = Config::default();
        cfg.charge_owner_pct = 50;
        let off = run_alone(&ancestor(64, 16), 3000);
        let on = run_alone_with(&ancestor(64, 16), 3000, &cfg);
        assert_eq!((on.births, on.exact_births, on.executed, on.final_energy), (off.births, off.exact_births, off.executed, off.final_energy));
    }

    /// `genome` before `host` as in `run_with_host`, but the run goes on to
    /// `ticks` after the genome dies, so the host's own births are counted
    /// over the whole run. Returns (genome births, genome alive, host exact
    /// births, host alive).
    fn run_on_with_host(genome: &[u8], host: &[u8], ticks: u64, cfg: &Config) -> (u32, bool, u32, bool) {
        let cfg = quiet(cfg.clone());
        let mut sim = Sim::new(cfg.clone());
        let mid = cfg.world_size / 2;
        let host_id = sim.seed(mid, host, 100 * MILLI, 0);
        let me_id = sim.seed(mid.wrapping_sub(genome.len() as u32), genome, 100 * MILLI, 0);
        let hh = fnv1a(host);
        let (mut births, mut host_exact) = (0, 0);
        for _ in 0..ticks {
            sim.run_tick();
            for ev in sim.events.drain(..) {
                if let Event::Birth { executor, genome_hash, .. } = ev {
                    if executor == me_id {
                        births += 1;
                    } else if executor == host_id && genome_hash == hh {
                        host_exact += 1;
                    }
                }
            }
            sim.cull_except(&[host_id, me_id]);
        }
        let alive = |id| sim.genome_of(id).map_or(false, |o| o.alive);
        (births, alive(me_id), host_exact, alive(host_id))
    }

    /// The ancestor with `prefix` (assembler text) inserted at byte 0.
    fn prefixed(prefix: &str, k: i8) -> Vec<u8> {
        let mut g = assemble(prefix).unwrap();
        g.extend(ancestor(k, 16));
        g
    }

    #[test]
    fn self_scan_prefix_as_designed_breaks_the_host() {
        // E009 path audit. The design's prefix
        // `self 1 ; swap B ; self 0 ; sub B ; jmpr A` does not work: `self 0`
        // sets B to the body length as well as A to the start, so the IP
        // saved in B is gone and `sub B` leaves A = start - length, and
        // `jmpr A` throws the host out of its own body. Its four
        // intermediates are each `replicator` alone (the body's first `self`
        // resets A and B); the fourth makes only 11 children and dies, which
        // is the length, not the bytes: four inert `zero D` bytes do the
        // same at K = 64 (a 25-byte body does not pay for its cycle).
        let full = "self 1\nswap B\nself 0\nsub B\njmpr A\n";
        let lines: Vec<&str> = full.lines().collect();
        let mut kids = Vec::new();
        for n in 1..=4 {
            let r = run_alone(&prefixed(&lines[..n].join("\n"), 64), 3000);
            assert_eq!(r.class(), "replicator", "intermediate {n}");
            kids.push(r.exact_births);
        }
        assert_eq!(kids, vec![230, 222, 214, 11]);
        assert_eq!(run_alone(&prefixed("zero D\nzero D\nzero D\nzero D\n", 64), 3000).exact_births, 11);
        assert_eq!(run_alone(&prefixed(full, 64), 3000).class(), "dies");
        assert_eq!(run_alone(&prefixed(full, 120), 3000).class(), "dies");
    }

    #[test]
    fn self_scan_prefix_through_c_traps_the_pad() {
        // The same prefix with the IP kept in C, which `self 0` leaves alone:
        // `self 1 ; swap C ; self 0 ; sub C ; jmpr A`. A = own start - IP,
        // 0 for the host at its byte 0, so `jmpr A` falls through. A `pad`
        // right before the host gets A = -1 and spins on the `jmpr` until
        // its store runs out, without a child. At K = 64 the 26-byte body
        // does not pay for itself; at K = 120 (E007's evolved host) it does.
        // Under the split the host pays N% of every spin, so the trap costs
        // it pad's store * N / (100 - N): about 100 units at 50%, which it
        // survives, and without bound at 100%, where the pad pays nothing
        // per spin and the host dies.
        let host = prefixed("self 1\nswap C\nself 0\nsub C\njmpr A\n", 120);
        assert_eq!(host.len(), 26);
        let alone = run_alone(&host, 3000);
        assert_eq!((alone.class(), alone.exact_births), ("replicator", 142));
        assert_eq!(run_alone(&prefixed("self 1\nswap C\nself 0\nsub C\njmpr A\n", 64), 3000).exact_births, 5);
        let pad = assemble("pad\n").unwrap();
        let at = |pct: i64| {
            let mut cfg = Config::default();
            cfg.charge_owner_pct = pct;
            cfg
        };
        for pct in [0, 50] {
            let r = run_with_host(&pad, &host, 3000, &at(pct));
            assert_eq!(r.births, 0);
            assert!(r.stopped_early && r.host_alive, "pct {pct}");
            let (births, alive, host_exact, host_alive) = run_on_with_host(&pad, &host, 3000, &at(pct));
            assert_eq!((births, alive, host_exact, host_alive), (0, false, 142, true), "pct {pct}");
        }
        let (births, _, host_exact, host_alive) = run_on_with_host(&pad, &host, 3000, &at(100));
        assert_eq!((births, host_exact, host_alive), (0, 0, false));
    }

    #[test]
    fn labels() {
        assert_eq!(run_alone(&ancestor(64, 16), 3000).class(), "replicator");
        // E002 survivor pattern: `dec B` instead of `dec A`, so the absorb
        // loop never exits.
        let broken = ancestor(64, 16)
            .iter()
            .enumerate()
            .map(|(k, &b)| if k == 8 { crate::isa::encode(crate::isa::Op::Dec, crate::isa::REG_B) } else { b })
            .collect::<Vec<u8>>();
        assert_eq!(crate::isa::disasm_at(&broken, 8).0, "dec B");
        let r = run_alone(&broken, 3000);
        assert_eq!(r.class(), "loafer");
        assert!(r.absorbs > 1000);
        assert_eq!(run_alone(&assemble("pad\n").unwrap(), 3000).class(), "dies");
        // E005's trampoline genome: the ancestor with `self 0` before the
        // restart replaced by `pad`, so after one child it jumps to address
        // 17 (the endowment literal in A) and walks free memory until it
        // starves. Alone: one exact child, then nothing.
        let hex = "13325271fc1160b605086c5a384548ec11111c1b0d";
        let g: Vec<u8> = (0..hex.len()).step_by(2).map(|j| u8::from_str_radix(&hex[j..j + 2], 16).unwrap()).collect();
        let r = run_alone(&g, 3000);
        assert_eq!((r.births, r.exact_births, r.alive), (1, 1, false));
        assert_eq!(r.class(), "one_shot");
    }

    #[test]
    fn world_physics_class() {
        // E004 world (--patch 512 --sun 8 --alloc-far --absorb-prop): the
        // ancestor is still a replicator, and the harness runs noiseless
        // whatever noise the config carries.
        let mut cfg = Config::default();
        cfg.patch_size = 512;
        cfg.patch_income = 256 * MILLI;
        cfg.patch_cap = 4096 * MILLI;
        cfg.alloc_far = true;
        cfg.absorb_proportional = true;
        cfg.p_bit_rot = 1e-4;
        let r = run_alone_with(&ancestor(64, 16), 3000, &cfg);
        assert_eq!(r.class(), "replicator");
        assert_eq!(r.births, r.exact_births, "noise leaked into the harness");
        assert!(r.exact_births >= 100, "only {} exact births", r.exact_births);
    }
}
