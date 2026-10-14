//! T08: the `alloc`/`copy` range edge (docs/tasks/T08-alloc-copy-edge.md).
//!
//! `alloc` checks that its whole run lies within locality of its own IP; the
//! far rule puts a backward child's byte 0 exactly `locality` behind that IP.
//! The `copy` loop runs a few bytes later, so before T08 its writes to the
//! child's first bytes were out of range from the `copy` IP and faulted, and
//! the child kept the stale bytes there. Since T08 a write into the
//! executor's own pending region passes the range check;
//! `Config::legacy_pending_range` (`--legacy-pending-range`) keeps the old
//! rule, bit for bit.
//!
//! How many bytes the edge costs is the distance from `alloc` to `copy`: 1
//! for the 21-byte ancestor (`alloc C` is byte 11, `copy` byte 12: byte 0 is
//! lost, `self` becomes whatever was there) and 3 for the 41-byte template
//! ancestor (`alloc C` byte 25, `lit D -4`, `copy` byte 28: bytes 0-2, its
//! start label L0). The spec's §1 says 3 for both; it is 1 for the 21-byte
//! body, as the E015 record's "lose byte 0" measurement already says.

use evo_core::config::{Config, MILLI};
use evo_core::isa::assemble;
use evo_core::sim::{ancestor, ancestor_t, AncestorKind, Event, Sim, ANCESTOR_T_K, DEBRIS};

fn quiet(cfg: &mut Config) {
    cfg.p_write_flip = 0.0;
    cfg.q_slip = 0.0;
    cfg.p_debris_decay = 0.0;
    cfg.p_bit_rot = 0.0;
}

/// Seed `g` at 1,000 in the quiet default world (far `alloc`), with stale
/// debris bytes `0xee` where its second child's first `lost` bytes will go,
/// and run until it has two children. The first goes to the forward edge,
/// which it then blocks, so the second goes to the backward edge, starting
/// `locality` behind the `alloc` IP. Returns the two children's starts, the
/// second child's genome, and the parent's `range_faults` during the second
/// copy loop (with the first loop's, which must be 0, checked).
fn backward_child(g: &[u8], alloc_at: u32, lost: u32, legacy: bool) -> ([u32; 2], Vec<u8>, u64) {
    let mut cfg = Config::default();
    quiet(&mut cfg);
    assert!(cfg.alloc_far && cfg.locality == 512);
    cfg.legacy_pending_range = legacy;
    let mut sim = Sim::new(cfg);
    let at = 1000u32;
    let parent = sim.seed(at, g, 100 * MILLI, 0);
    let back = at + alloc_at - 512;
    for a in back..back + lost {
        sim.bytes[a as usize] = 0xee;
        sim.owner[a as usize] = DEBRIS;
    }
    let mut kids = Vec::new();
    for _ in 0..400 {
        sim.run_tick();
        let faults = sim.genome_of(parent).unwrap().stats.range_faults;
        for ev in sim.events.drain(..) {
            if let Event::Birth { executor, child, start, copy_errors, slips, .. } = ev {
                if executor == parent {
                    assert_eq!((copy_errors, slips), (0, 0));
                    kids.push((child, start, faults));
                }
            }
        }
        if kids.len() >= 2 {
            break;
        }
    }
    assert_eq!(kids.len(), 2, "legacy={legacy}: {kids:?}");
    let len = g.len() as u32;
    assert_eq!(kids[0].1, at + alloc_at + 512 - (len - 1), "first child at the forward edge");
    assert_eq!(kids[1].1, back, "second child at the backward edge");
    assert_eq!(kids[0].2, 0, "legacy={legacy}: the forward child's copy loop faulted");
    let child = sim.genome_of(kids[1].0).unwrap().genome.clone();
    assert_eq!(child, sim.region(back, len));
    ([kids[0].1, kids[1].1], child, kids[1].2 - kids[0].2)
}

#[test]
fn copy_into_own_pending_region_passes_range() {
    // (body, `alloc` offset, bytes the edge costs under the old rule)
    for (name, g, alloc_at, lost) in
        [("tierra", ancestor_t(ANCESTOR_T_K, 16), 25u32, 3u32), ("std", ancestor(64, 16), 11, 1)]
    {
        let n = lost as usize;
        // Default: every byte copied, no fault, the child equals the parent.
        let (starts, child, faults) = backward_child(&g, alloc_at, lost, false);
        assert_eq!(faults, 0, "{name}: the backward copy loop faulted");
        assert_eq!(&child[..3], &g[..3], "{name}");
        assert_eq!(child, g, "{name}");
        // Legacy: the first `lost` bytes are out of range from the `copy` IP,
        // fault, and keep the stale bytes; the rest is copied.
        let (starts_l, child_l, faults_l) = backward_child(&g, alloc_at, lost, true);
        assert_eq!(starts_l, starts, "{name}: placement differs between the modes");
        assert_eq!(faults_l, lost as u64, "{name}: range faults in the backward copy loop");
        assert!(child_l[..n].iter().all(|&b| b == 0xee), "{name}: {:02x?}", &child_l[..n]);
        assert_eq!(&child_l[n..], &g[n..], "{name}");
        eprintln!("{name}: backward child at {}; legacy {faults_l} faults, first bytes {:02x?}", starts[1], &child_l[..4]);
    }
}

#[test]
fn store_outside_pending_still_faults() {
    // A hand-built organism at 10,000 whose IP is at a `store D` with A =
    // IP + 513 (one past locality) and D = 0x77, and a pending region set
    // as `alloc` sets one (owner and `pending`). With the region elsewhere
    // the store faults in both modes; as a control, with the region over
    // the target it lands under the new rule and faults under the old one.
    let body = assemble("store D\npad\npad\npad\n").unwrap();
    let s = 10_000u32;
    let target = s + 513;
    for (region, legacy, lands) in [
        ((s + 100, 21), false, false),
        ((s + 100, 21), true, false),
        ((target - 5, 21), false, true),
        ((target - 5, 21), true, false),
    ] {
        let mut cfg = Config::default();
        quiet(&mut cfg);
        cfg.legacy_pending_range = legacy;
        let mut sim = Sim::new(cfg);
        let id = sim.seed(s, &body, 100 * MILLI, 0);
        let (ps, pl) = region;
        for a in ps..ps + pl {
            sim.owner[a as usize] = id;
        }
        let o = &mut sim.orgs[0];
        o.pending = Some(region);
        o.regs[0] = target;
        o.regs[3] = 0x77;
        sim.run_tick();
        let o = &sim.orgs[0];
        let tag = format!("region {region:?} legacy={legacy}");
        assert!(o.stats.executed >= 1, "{tag}");
        if lands {
            assert_eq!(sim.bytes[target as usize], 0x77, "{tag}");
            assert_eq!(o.stats.range_faults, 0, "{tag}");
        } else {
            assert_eq!(sim.bytes[target as usize], 0, "{tag}");
            assert_eq!(o.stats.range_faults, 1, "{tag}");
            assert!(o.flag, "{tag}");
        }
    }
}

/// A run as `evo-core --seed 1 --ticks T` would make it with the given
/// ancestor, `--sun` and (if `quiet`) `--p 0 --rot 0`: `Config::default()`,
/// patch income and cap times `sun`, the ancestor at its default K and E =
/// 16 seeded once at `world_size / 2` with 100 units (`seed_founders`), ticks
/// run until T or extinction. Returns the state hash and every birth's
/// (`copy_errors`, raw hash == parent's body hash at `divide`).
fn cli_run(kind: AncestorKind, sun: i64, quiet: bool, legacy: bool, ticks: u64) -> (u64, Vec<(u32, bool)>) {
    let mut cfg = Config::default();
    cfg.seed = 1;
    if quiet {
        // `--p 0` sets the write flip and the slip; `--rot 0` bit rot.
        cfg.p_write_flip = 0.0;
        cfg.q_slip = 0.0;
        cfg.p_bit_rot = 0.0;
    }
    cfg.patch_income *= sun;
    cfg.patch_cap *= sun;
    cfg.legacy_pending_range = legacy;
    let mut sim = Sim::new(cfg);
    sim.seed_founders(&[(kind.body(kind.default_k(), 16), 1)], 100 * MILLI);
    let mut births = Vec::new();
    for _ in 0..ticks {
        sim.run_tick();
        for ev in sim.events.drain(..) {
            if let Event::Birth { copy_errors, genome_hash, parent_now_hash, .. } = ev {
                births.push((copy_errors, genome_hash == parent_now_hash));
            }
        }
        if sim.alive_count() == 0 {
            break;
        }
    }
    (sim.state_hash(), births)
}

#[test]
fn legacy_flag_is_bit_identical_to_head() {
    // Pinned 2026-10-13 before T08 changed anything, at HEAD 4050ee8 (the
    // engine as at e0610d6, the binary of E015's stages 1-2 and its added
    // arms), with a temporary test driving `Sim` exactly as `cli_run` does;
    // the living, birth and death counts at tick 5,000 matched the CLI's
    // census line for the same flags (913 / 67,234 / 66,322; 1,419 / 58,891
    // / 57,473; 1,078 / 160,254 / 159,177). The first run is noise-on, so
    // the PRNG sequence is covered; the third is the noise-off world where
    // the edge is the only source of variation.
    let cases: [(&str, AncestorKind, i64, bool, u64); 3] = [
        ("--seed 1 --ticks 5000", AncestorKind::Std, 1, false, 0xab014cc96e8cfb59),
        ("--ancestor tierra --sun 2 --seed 1 --ticks 5000", AncestorKind::Tierra, 2, false, 0x1f3b73f93ea0a8b3),
        ("--p 0 --rot 0 --seed 1 --ticks 5000", AncestorKind::Std, 1, true, 0x9cb7abc8caaf5cbf),
    ];
    std::thread::scope(|sc| {
        let hs: Vec<_> = cases
            .iter()
            .map(|&(name, kind, sun, q, pinned)| {
                sc.spawn(move || {
                    let (legacy, _) = cli_run(kind, sun, q, true, 5000);
                    // The new rule diverges from the old at the founder's
                    // second child (tick 27 for std, 51 for tierra).
                    let (new, _) = cli_run(kind, sun, q, false, 300);
                    let (old, _) = cli_run(kind, sun, q, true, 300);
                    (name, legacy, pinned, new != old)
                })
            })
            .collect();
        for h in hs {
            let (name, got, pinned, differs) = h.join().unwrap();
            assert_eq!(got, pinned, "{name} --legacy-pending-range: 0x{got:016x}, pinned 0x{pinned:016x}");
            assert!(differs, "{name}: the default and legacy runs agree at tick 300");
        }
    });
}

#[test]
fn noise_off_births_are_exact_under_the_new_rule() {
    // Std ancestor and the tierra body at `--sun 2`, `--p 0 --rot 0`, 3,000
    // ticks, one founder in the default world. Under the new rule every
    // birth equals its parent's body at `divide` with no copy error; under
    // the old one some do not (the E015 record: 12.8% for std).
    let cases = [("std", AncestorKind::Std, 1i64), ("tierra --sun 2", AncestorKind::Tierra, 2)];
    std::thread::scope(|sc| {
        let hs: Vec<_> = cases
            .iter()
            .map(|&(name, kind, sun)| {
                sc.spawn(move || (name, cli_run(kind, sun, true, false, 3000).1, cli_run(kind, sun, true, true, 3000).1))
            })
            .collect();
        for h in hs {
            let (name, new, old) = h.join().unwrap();
            assert!(new.len() > 100, "{name}: only {} births", new.len());
            assert!(new.iter().all(|&(e, _)| e == 0), "{name}: a copy error with noise off");
            let inexact = new.iter().filter(|&&(_, exact)| !exact).count();
            assert_eq!(inexact, 0, "{name}: {inexact} of {} births differ from the parent", new.len());
            let old_inexact = old.iter().filter(|&&(_, exact)| !exact).count();
            assert!(old_inexact > 0, "{name}: the legacy run has no inexact birth; the test is weak");
            eprintln!("{name}: new rule {} births, all exact; legacy {} births, {old_inexact} ({:.1}%) differ",
                      new.len(), old.len(), 100.0 * old_inexact as f64 / old.len() as f64);
        }
    });
}
