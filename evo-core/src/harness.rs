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
    let mut cfg = Config::default();
    cfg.p_write_flip = 0.0;
    cfg.q_slip = 0.0;
    cfg.p_bit_rot = 0.0;
    cfg.p_debris_decay = 0.0;
    cfg
}

/// Run `genome` alone for `ticks` ticks with 100 units of seed energy,
/// removing its children at the end of every tick.
pub fn run_alone(genome: &[u8], ticks: u64) -> HarnessResult {
    let cfg = quiet_config();
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::isa::assemble;
    use crate::sim::ancestor;

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
}
