//! Single-genome harness (PLAN.md §7): run one genome alone in a clean,
//! noiseless world and see what it does. Used to label genomes from a run
//! by test (`--classify`), not by reading their disassembly.

use crate::config::{Config, MILLI};
use crate::sim::{fnv1a, Event, Sim};

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
}

impl HarnessResult {
    /// `replicator`: at least 2 exact children. `inexact`: some children but
    /// fewer than 2 exact. `loafer`: no children, still alive. `dies`: no
    /// children, died alone.
    pub fn class(&self) -> &'static str {
        if self.exact_births >= 2 {
            "replicator"
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
    };
    for _ in 0..ticks {
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
        sim.cull_all_but(0);
        if !sim.orgs[0].alive {
            break;
        }
    }
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
    };
    for _ in 0..ticks {
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
        sim.cull_except(&[0, 1]);
        if !sim.orgs[1].alive {
            break;
        }
    }
    r.alive = sim.orgs[1].alive;
    r.host_alive = sim.orgs[0].alive;
    r.executed = sim.orgs[1].stats.executed;
    r.exec_foreign = sim.orgs[1].stats.exec_foreign;
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
