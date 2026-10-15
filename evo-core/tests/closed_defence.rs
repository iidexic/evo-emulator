//! T11 §3 (reduced to the eject): a tolerant defence for the template
//! body, hand-written. docs/tasks/T11-closed-defence-screen.md.
//!
//! The spec's candidate is E009b's six bytes (E010's `eject`, `self 1 ;
//! swap C ; self 0 ; sub C ; skipz A ; jmpa D`) inserted in the tierra
//! body's copy loop. Verbatim they cannot work there: they compute A =
//! executor start - IP, which is 0 only at a body's byte 0, so a host
//! running them anywhere else ejects itself; and inside the copy loop all
//! four registers are live (A the child pointer, B the source, C the count,
//! D the loop offset), and the six bytes overwrite A, B and C. The nearest
//! working eject sits just before the loop, before `alloc C`, where only A
//! and D are free and B already holds the executor's start (`self 0 ; swap
//! B`): `self 1 ; sub B` gives A = this byte's offset in the executor (25
//! for the host itself), `lit D 25 ; sub D` makes that 0, and `skipz A ;
//! jmpa D` sends anyone else to absolute address 25. Seven inserted bytes
//! (one more than E009b's six: the offset needs the `lit`), 48 in all.
//!
//! What it does: the registered probe (the label flip) finds the host's L1,
//! enters at 22, runs 9 of the host's instructions and is gone (0 copies;
//! the plain ancestor gives it 119). What it costs: the body is no longer
//! viable alone at K = 127 (2 exact children, then it dies), and seven inert
//! bytes in the same place cost the same, so it is the length, not the
//! check: the 41-byte body pays for at most two more bytes. A body that
//! wraps the world's end (start near 65535) would eject itself, since
//! `self 1` gives the wrapped IP; the harness never places one there.

use evo_core::config::{Config, MILLI};
use evo_core::harness::{run_alone_with, run_with_host};
use evo_core::isa::assemble;
use evo_core::sim::{ancestor_t, Sim, ANCESTOR_T_K};

/// Where the eject goes: before `alloc C`, the procedure's fourth byte.
const AT: usize = 25;

fn hex(g: &[u8]) -> String {
    g.iter().map(|b| format!("{b:02x}")).collect()
}

/// The ancestor with `src` (assembler text) inserted before byte `at`.
fn tierra_variant(at: usize, src: &str) -> Vec<u8> {
    let mut g = ancestor_t(ANCESTOR_T_K, 16);
    g.splice(at..at, assemble(src).unwrap());
    g
}

/// The eject body (T11 §3).
fn tierra_eject() -> Vec<u8> {
    tierra_variant(AT, "self 1\nsub B\nlit D 25\nsub D\nskipz A\njmpa D\n")
}

/// The registered probe: the ancestor with L1's first byte flipped.
fn probe() -> Vec<u8> {
    let mut m = ancestor_t(ANCESTOR_T_K, 16);
    m[18] = 0x01;
    m
}

#[test]
fn eject_layout() {
    let g = tierra_eject();
    let a = ancestor_t(ANCESTOR_T_K, 16);
    assert_eq!(g.len(), a.len() + 7);
    assert_eq!((&g[..AT], &g[AT + 7..]), (&a[..AT], &a[AT..]));
    // analysis/t11_closed.py screens this hex (EJECT_HEX).
    assert_eq!(hex(&g), "0101030351fc117f1605084c0a010301036d03010301133252332f71196f086d5a71fc1845486c11101c0b030301016d");
}

#[test]
fn eject_replicates_exactly_without_noise() {
    // `ancestor_t_replicates_exactly_without_noise`'s check: the Phase 1
    // world, noise off; the first child equals the parent and sits right
    // after it.
    let mut cfg = Config::e001();
    cfg.p_write_flip = 0.0;
    cfg.q_slip = 0.0;
    cfg.p_debris_decay = 0.0;
    cfg.p_bit_rot = 0.0;
    let mut sim = Sim::new(cfg);
    let g = tierra_eject();
    sim.seed(1000, &g, 100 * MILLI, 0);
    for _ in 0..200 {
        sim.run_tick();
        if sim.orgs.len() > 1 {
            break;
        }
    }
    assert!(sim.orgs.len() > 1, "no child within 200 ticks");
    assert_eq!(sim.orgs[1].genome, g);
    assert_eq!(sim.orgs[1].start, 1000 + 48);
}

#[test]
fn eject_sends_the_label_flip_away() {
    // The probe before the eject host: it enters at 22, runs `self 0 ; swap
    // B ; swap C` and the six check instructions on the host (9 foreign),
    // jumps to address 25 and starves in free memory without a child. The
    // same under E016's tierra_n0 (`--sun 2`) and tierra_t50 physics.
    let plain = ancestor_t(ANCESTOR_T_K, 16);
    for (name, sun, theft) in [("default", 1, 0), ("tierra_n0", 2, 0), ("tierra_t50", 2, 50)] {
        let mut cfg = Config::default();
        cfg.patch_income *= sun;
        cfg.patch_cap *= sun;
        cfg.cycle_theft_pct = theft;
        let r = run_with_host(&probe(), &tierra_eject(), 3000, &cfg);
        assert_eq!((r.births, r.entry_off, r.exec_foreign, r.alive, r.host_alive), (0, 22, 9, false, true), "{name}");
        let p = run_with_host(&probe(), &plain, 3000, &cfg);
        assert_eq!((p.exact_births, p.entry_off), (119, 22), "{name}");
    }
}

#[test]
fn eject_costs_the_body_its_viability() {
    // Alone at the default physics (and at `--sun 2`, which leaves a lone
    // body's ration unchanged): 2 exact children, then dead, against the
    // ancestor's 119; seven inert bytes (`zero A`, overwritten by `alloc`) in
    // the same place do the same, and the margin runs out at the third
    // inert byte. E009b's six bytes verbatim in the copy loop (after `copy`,
    // the loop's `lit D` operand moved to -10): the host ejects itself at
    // its first copied byte.
    let cfg = Config::default();
    let alone = |g: &[u8]| {
        let r = run_alone_with(g, 3000, &cfg);
        (r.class(), r.exact_births, r.alive)
    };
    assert_eq!(alone(&tierra_eject()), ("replicator", 2, false));
    let inert: Vec<(&str, u32, bool)> = (1..=7).map(|n| alone(&tierra_variant(AT, &"zero A\n".repeat(n)))).collect();
    assert_eq!(inert[0], ("replicator", 119, true));
    assert_eq!(inert[1], ("replicator", 115, true));
    assert_eq!(inert[2], ("replicator", 97, false));
    assert_eq!(inert[6], alone(&tierra_eject()));
    let mut sun2 = Config::default();
    sun2.patch_income *= 2;
    sun2.patch_cap *= 2;
    assert_eq!(run_alone_with(&tierra_eject(), 3000, &sun2).exact_births, 2);
    let mut verbatim = ancestor_t(ANCESTOR_T_K, 16);
    assert_eq!((verbatim[26], verbatim[27], verbatim[28]), (0x71, 0xfc, 0x18)); // lit D -4 ; copy
    verbatim[27] = (-10i8) as u8;
    verbatim.splice(29..29, assemble("self 1\nswap C\nself 0\nsub C\nskipz A\njmpa D\n").unwrap());
    assert_eq!(alone(&verbatim), ("dies", 0, false));
}
