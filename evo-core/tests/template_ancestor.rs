//! T03: the template-addressed ancestor (`--ancestor tierra`,
//! `sim::ancestor_t`), the entry offset (`Org::first_foreign_off`,
//! `HostResult::entry_off`) and the neighbourhood mode (`--neighbours HEX`).
//! docs/tasks/T03-template-ancestor.md.
//!
//! The body is the spec's with four-nop labels (41 bytes, not 45): the
//! five-nop body pays for itself at no K a `lit` byte holds, and four-nop
//! labels are the first fix the T03 branch in docs/tasks/README.md lists
//! (`sim::ancestor_t`'s comment has the harness evidence). So L1, the
//! procedure label, is bytes 18-21 here and the label-flip parasite enters
//! its host at byte 22 (the spec's 20-24 and 25).

use evo_core::config::{Config, MILLI};
use evo_core::harness::{self, run_alone, run_alone_with, run_with_host};
use evo_core::isa::{decode, Op};
use evo_core::sim::{ancestor, ancestor_t, Event, Sim, ANCESTOR_T_K, FIRST_ID};

fn quiet(cfg: &mut Config) {
    cfg.p_write_flip = 0.0;
    cfg.q_slip = 0.0;
    cfg.p_debris_decay = 0.0;
    cfg.p_bit_rot = 0.0;
}

fn hex(g: &[u8]) -> String {
    g.iter().map(|b| format!("{b:02x}")).collect()
}

/// The ancestor at the default K with L1's first byte (18) flipped from
/// `nop1` to `nop0`.
fn label_flip() -> Vec<u8> {
    let mut m = ancestor_t(ANCESTOR_T_K, 16);
    assert_eq!(decode(m[18]).0, Op::Nop1);
    m[18] = 0x01;
    m
}

#[test]
fn ancestor_t_layout() {
    // The byte positions the docs, traits.py and the tests rely on.
    let g = ancestor_t(ANCESTOR_T_K, 16);
    assert_eq!(g.len(), 41);
    let ops: Vec<Op> = g.iter().map(|&b| decode(b).0).collect();
    let nops = |r: std::ops::Range<usize>, bits: &[u8]| {
        for (k, &bit) in r.zip(bits) {
            assert_eq!(ops[k], if bit == 1 { Op::Nop1 } else { Op::Nop0 }, "byte {k}");
        }
    };
    nops(0..4, &[0, 0, 1, 1]); // L0
    nops(13..17, &[0, 1, 0, 1]); // searchf template, complement of L1
    nops(18..22, &[1, 0, 1, 0]); // L1
    nops(36..40, &[1, 1, 0, 0]); // searchb template, complement of L0
    assert_eq!((ops[6], g[7] as i8), (Op::Lit, ANCESTOR_T_K));
    assert_eq!((ops[32], g[33] as i8, ops[34]), (Op::Lit, 16, Op::Divide));
    assert_eq!((ops[12], ops[17], ops[22], ops[35], ops[40]), (Op::Searchf, Op::Jmpa, Op::Self_, Op::Searchb, Op::Jmpa));
    assert_eq!(hex(&g), "0101030351fc117f1605084c0a010301036d030103011332525a71fc1845486c11101c0b030301016d");
}

#[test]
fn ancestor_t_replicates_exactly_without_noise() {
    // As `ancestor_replicates_exactly_without_noise`: the Phase 1 world
    // (nearest-free `alloc`), noise off. The first child equals the parent,
    // carries the endowment, starts at its own byte 0 and sits right after
    // the parent (`alloc` at byte 25 finds the first free 41-byte run
    // forward at 1041 before any backward one).
    let mut cfg = Config::e001();
    quiet(&mut cfg);
    let mut sim = Sim::new(cfg);
    let g = ancestor_t(ANCESTOR_T_K, 16);
    sim.seed(1000, &g, 100 * MILLI, 0);
    let mut born = false;
    for _ in 0..200 {
        sim.run_tick();
        if sim.orgs.len() > 1 {
            born = true;
            break;
        }
    }
    assert!(born, "no child within 200 ticks");
    let child = &sim.orgs[1];
    assert_eq!(child.genome, g, "child genome differs from parent");
    assert_eq!(child.energy, 16 * MILLI);
    assert_eq!(child.ip, child.start);
    assert!(sim.orgs[0].alive);
    assert_eq!(child.start, 1000 + 41);
    // The parent's `searchb` took it back to its own L0: IP past the label.
    for _ in 0..5 {
        sim.run_tick();
    }
    let p = &sim.orgs[0];
    let off = sim.ip_off(p);
    assert!((4..41).contains(&off) && p.stats.exec_foreign == 0 && p.stats.exec_unowned == 0, "parent IP at offset {off}");
}

#[test]
fn ancestor_t_pays_for_itself() {
    // As `ancestor_pays_for_itself`: alone, full pool, children culled
    // every tick, 3,000 ticks. At K = 127 a cycle takes 25 ticks and nets
    // +37.9 units below the store cap (41 x 64 = 2,624 units), so it rides
    // near the cap rather than draining toward zero.
    let mut cfg = Config::default();
    quiet(&mut cfg);
    let mut sim = Sim::new(cfg);
    let g = ancestor_t(ANCESTOR_T_K, 16);
    sim.seed(1000, &g, 100 * MILLI, 0);
    let (mut min_first, mut min_second) = (i64::MAX, i64::MAX);
    for t in 0..3000 {
        sim.run_tick();
        sim.cull_all_but(FIRST_ID);
        let e = sim.orgs[0].energy;
        if t < 1500 { min_first = min_first.min(e) } else { min_second = min_second.min(e) }
    }
    let births = sim.events.iter().filter(|e| matches!(e, Event::Birth { .. })).count();
    assert!(births >= 100, "only {births} births");
    assert!(sim.orgs[0].alive, "ancestor died");
    assert!(sim.orgs[0].energy > 500 * MILLI, "energy {} too low", sim.orgs[0].energy);
    assert!(min_second > min_first, "energy trends down: min {min_first} then {min_second}");
    let r = run_alone(&g, 3000);
    assert_eq!((r.class(), r.exact_births, r.alive), ("replicator", 119, true));
    eprintln!("harness: {births} births in 3000 ticks, min energy {min_first} then {min_second}, final {}", sim.orgs[0].energy);
}

#[test]
fn ancestor_t_k_steps_below_127_do_not_pay() {
    // T03 §1's K-stepping from 64 in steps of 16 (128 does not fit a `lit`
    // byte): every K below 127 dies alone within 3,000 ticks, 127 lives.
    let got: Vec<(i8, &str, u32, bool)> = [64, 80, 96, 112, 127]
        .iter()
        .map(|&k| {
            let r = run_alone(&ancestor_t(k, 16), 3000);
            (k, r.class(), r.births, r.alive)
        })
        .collect();
    assert_eq!(
        got,
        vec![(64, "dies", 0, false), (80, "dies", 0, false), (96, "one_shot", 1, false),
             (112, "replicator", 7, false), (127, "replicator", 119, true)]
    );
}

#[test]
fn ancestor_t_label_flip_is_a_parasite() {
    // T03 §3 test 2. L1's first byte flipped (`nop1` to `nop0`): the
    // body's own `searchf` skips its broken label and finds the host's L1,
    // so it jumps into the host past L1 (offset 22), runs the host's
    // procedure (which copies the intruder: `self` = executor) and is sent
    // back to the host's L0 by the host's `searchb`: resident for life.
    // Alone it finds no L1 within locality, jumps to address 0 and walks
    // free memory until it starves.
    let m = label_flip();
    let host = ancestor_t(ANCESTOR_T_K, 16);
    let cfg = Config::default();
    let alone = run_alone_with(&m, 3000, &cfg);
    assert_ne!(alone.class(), "replicator");
    assert_eq!(alone.births, 0);
    let r = run_with_host(&m, &host, 3000, &cfg);
    assert!(r.exact_births >= 2, "{} exact births", r.exact_births);
    assert_eq!(r.entry_off, 22);
    assert!(r.host_alive && r.alive && !r.stopped_early);
    assert!(4 * r.exec_foreign > r.executed);
    assert_eq!(harness::label(&alone, &r), "parasite_jump");
    eprintln!("flip: exact {} of {} births, host exact {}, foreign {} of {}", r.exact_births, r.births,
              r.host_exact_births, r.exec_foreign, r.executed);
}

#[test]
fn neighbours_of_the_std_ancestor_jumps_only_by_fixed_offsets() {
    // T03 §3 test 3, as found. The spec expected no `parasite_jump` row for
    // the 21-byte ancestor; under the spec's label rule (entry offset not 0)
    // it has 25, and none of them addresses its host by search (the body
    // has no nop, so a mutant `searchf` has an empty template and fails).
    // Each enters the adjacent host at a fixed distance from its own code:
    // - pos 4 (`lit D -4` -> `lit D 13`): the absorb loop's `jmpr D` jumps
    //   13 past byte 11, to the host's byte 3 (`lit D -4`), and from there
    //   runs the host's cycle, which copies the intruder.
    // - pos 7, 8, 9, 13 (`absorb`, `dec A`, `skipz A`, `dec C` -> `jmpr C`,
    //   bytes 76 and 204): C holds the own length, 21, so the jump lands at
    //   the same place in the adjacent host plus one.
    // - pos 20 (`jmpa A` -> a `lit` or a skip that fires): the last byte
    //   takes the host's byte 0 as its operand or skips it, so the intruder
    //   runs off its own end into the host's byte 1. That is the fall-through
    //   E005 found, entered one byte late.
    // And at least one `parasite_fallthrough` row (E005's `pad` lineages).
    let g = ancestor(64, 16);
    let t = std::thread::available_parallelism().map_or(1, |n| n.get()).min(12);
    let rows = harness::neighbours(&g, &g, 3000, &Config::default(), harness::MutantSet::SubDel, t);
    assert_eq!(rows.len(), 21 * 256);
    let count = |l: &str| rows.iter().filter(|r| r.label == l).count();
    assert!(count("parasite_fallthrough") >= 1);
    let mut jumps: Vec<(usize, i64)> =
        rows.iter().filter(|r| r.label == "parasite_jump").map(|r| (r.mutant.pos, r.host.entry_off)).collect();
    jumps.dedup();
    assert_eq!(count("parasite_jump"), 25);
    assert_eq!(jumps, vec![(4, 3), (7, 8), (8, 9), (9, 10), (13, 14), (20, 1)]);
    for r in rows.iter().filter(|r| r.label == "parasite_jump" && r.mutant.pos != 20) {
        let (op, m) = decode(r.mutant.byte.unwrap());
        assert!(r.mutant.pos == 4 || (op == Op::Jmpr && m & 3 == 2), "pos {} byte {:?}", r.mutant.pos, r.mutant.byte);
    }
    eprintln!("std neighbourhood: {}", harness::neighbours_summary(&rows));
}

#[test]
fn neighbours_file_is_thread_count_independent() {
    // T03 §3 test 4: the CLI at T = 1 and T = 4 writes the same file and
    // prints the same summary. Three `pad`s before the 21-byte ancestor,
    // 300 harness ticks: 768 mutants of every kind; with `--neighbours-ins`
    // (T11 §1) 1,792, the first 768 of them in the same order as without.
    let exe = env!("CARGO_BIN_EXE_evo-core");
    let dir = std::env::temp_dir().join(format!("evo-test-neighbours-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    let run = |t: u32, ins: bool| {
        let out = dir.join(format!("t{t}-{ins}.csv"));
        let mut cmd = std::process::Command::new(exe);
        cmd.args(["--neighbours", "000000", "--host-body", &hex(&ancestor(64, 16)), "--harness-ticks", "300",
                  "--threads", &t.to_string(), "--neighbours-out"])
            .arg(&out);
        if ins {
            cmd.arg("--neighbours-ins");
        }
        let o = cmd.output().unwrap();
        assert!(o.status.success(), "{}", String::from_utf8_lossy(&o.stderr));
        (String::from_utf8(std::fs::read(&out).unwrap()).unwrap(), o.stdout)
    };
    let (f1, s1) = run(1, false);
    let (f4, s4) = run(4, false);
    assert_eq!(f1.lines().count(), 1 + 3 * 255 + 3);
    assert_eq!(f1.lines().next().unwrap(), harness::NEIGHBOURS_HEADER);
    assert!(f1.lines().skip(1).any(|l| l.ends_with(",parasite_fallthrough")), "no parasite: the test is weak");
    assert!(f1 == f4, "neighbours.csv differs between 1 and 4 threads");
    assert_eq!(s1, s4);
    let (i1, si1) = run(1, true);
    let (i4, si4) = run(4, true);
    assert_eq!(i1.lines().count(), 1 + 3 * 255 + 3 + 4 * 256);
    assert!(i1 == i4, "neighbours.csv with insertions differs between 1 and 4 threads");
    assert_eq!(si1, si4);
    let ins: Vec<&str> = i1.lines().filter(|l| l.split(',').nth(1) == Some("ins")).collect();
    assert_eq!(ins.len(), 4 * 256);
    let no_ins: Vec<&str> = i1.lines().filter(|l| l.split(',').nth(1) != Some("ins")).collect();
    assert_eq!(no_ins, f1.lines().collect::<Vec<_>>(), "the substitutions and deletions changed with the flag");
    // The flag is ignored with --neighbours-pad-only.
    let o = std::process::Command::new(exe)
        .args(["--neighbours", "000000", "--harness-ticks", "300", "--neighbours-pad-only", "--neighbours-ins",
               "--neighbours-out"])
        .arg(dir.join("pad.csv"))
        .output()
        .unwrap();
    assert!(o.status.success());
    assert_eq!(std::fs::read_to_string(dir.join("pad.csv")).unwrap().lines().count(), 1 + 3);
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn insertions_count_and_order() {
    // T11 §1: a 3-byte genome gives 3 x 255 substitutions + 3 deletions +
    // 4 x 256 insertions. At each position p: the 255 substitutions in
    // ascending byte order, the deletion of p, then the 256 bodies with
    // byte v (ascending) inserted before p; the 256 insertions after the
    // last byte come last.
    use harness::{mutants, MutantSet};
    let g = vec![0x10u8, 0x20, 0x30];
    let ms = mutants(&g, MutantSet::WithIns);
    assert_eq!(ms.len(), 3 * 255 + 3 + 4 * 256);
    let mut k = 0;
    for p in 0..=g.len() {
        if p < g.len() {
            for v in (0..=255u8).filter(|&v| v != g[p]) {
                let mut want = g.clone();
                want[p] = v;
                assert_eq!((ms[k].pos, ms[k].kind, ms[k].byte, &ms[k].genome), (p, "sub", Some(v), &want), "row {k}");
                k += 1;
            }
            let mut want = g.clone();
            want.remove(p);
            assert_eq!((ms[k].pos, ms[k].kind, ms[k].byte, &ms[k].genome), (p, "del", None, &want), "row {k}");
            k += 1;
        }
        for v in 0..=255u8 {
            let mut want = g.clone();
            want.insert(p, v);
            assert_eq!((ms[k].pos, ms[k].kind, ms[k].byte, &ms[k].genome), (p, "ins", Some(v), &want), "row {k}");
            k += 1;
        }
    }
    assert_eq!(k, ms.len());
    // Without insertions the set is the T03 one, in the same order.
    let subdel: Vec<_> = ms.iter().filter(|m| m.kind != "ins").map(|m| (m.pos, m.kind, m.byte)).collect();
    let t03: Vec<_> = mutants(&g, MutantSet::SubDel).iter().map(|m| (m.pos, m.kind, m.byte)).collect();
    assert_eq!(subdel, t03);
    assert_eq!(mutants(&g, MutantSet::PadOnly).len(), 3);
}

#[test]
fn insertions_in_l1_follow_the_search_rule() {
    // T11 §1, the spec's `insertion_of_pad_is_a_knockout_of_nothing` as
    // found. The search rule is in sim.rs (`Op::Searchf | Op::Searchb` in
    // `Sim::step`), not isa.rs: the template is the run of nops after the
    // search, and a candidate matches when the template's length of bytes
    // there are its complement, whatever follows. So the match is not
    // exact-length: a five-nop label that contains `1010` still answers the
    // four-nop template `0101`. But `pad` is not a nop (`Op::is_nop` is
    // `nop0 | nop1`), so a `pad` inserted inside L1 splits the run. Three
    // cases, at the default physics:
    // - `pad` beside L1 (inserted before byte 18 or before byte 22) changes
    //   nothing: L1 is intact, and the 42-byte body makes the ancestor's
    //   119 exact children alone (the `searchf` lands on the `pad` before
    //   `self 0` when it follows L1).
    // - `pad` inside L1 (before byte 19, 20 or 21) breaks the label: alone
    //   it finds no L1 and dies without a child; before the ancestor it
    //   finds the host's L1 and is the label-flip parasite (entry 22).
    // - Of the six nops inserted inside L1, exactly `nop1` before 19
    //   (`11010`) and `nop0` before 21 (`10100`) keep `1010` contiguous and
    //   replicate (119 exact children); the other four break the label.
    let g = ancestor_t(ANCESTOR_T_K, 16);
    let cfg = Config::default();
    let ins = |p: usize, v: u8| {
        let mut m = g.clone();
        m.insert(p, v);
        m
    };
    let alone = |m: &[u8]| run_alone_with(m, 3000, &cfg);
    let (pad, nop0, nop1) = (0x00u8, 0x01u8, 0x03u8);
    for p in [18, 22] {
        let r = alone(&ins(p, pad));
        assert_eq!((r.class(), r.exact_births), ("replicator", 119), "pad before {p}");
    }
    for p in [19, 20, 21] {
        let m = ins(p, pad);
        let a = alone(&m);
        assert_eq!((a.class(), a.births), ("dies", 0), "pad before {p}");
        let h = run_with_host(&m, &g, 3000, &cfg);
        assert_eq!((harness::label(&a, &h), h.entry_off), ("parasite_jump", 22), "pad before {p}");
        assert!(h.host_alive);
    }
    for (p, v, works) in [(19, nop0, false), (19, nop1, true), (20, nop0, false), (20, nop1, false),
                          (21, nop0, true), (21, nop1, false)] {
        let r = alone(&ins(p, v));
        if works {
            assert_eq!((r.class(), r.exact_births), ("replicator", 119), "byte {v} before {p}");
        } else {
            assert_ne!(r.class(), "replicator", "byte {v} before {p}");
        }
    }
}

#[test]
fn first_foreign_off_is_set_once() {
    // T03 §3 test 5. A one-byte `pad` before the 21-byte ancestor falls into
    // the host's byte 0 (E005): its entry offset is 0 from that tick on,
    // though it goes on to run every other byte of the host. The host,
    // which runs only its own bytes, never gets one. The field is not
    // physics: the state hash ignores it.
    let mut cfg = Config::default();
    quiet(&mut cfg);
    let mut sim = Sim::new(cfg);
    let host = sim.seed(1000, &ancestor(64, 16), 100 * MILLI, 0);
    let pad = sim.seed(999, &[0x00], 100 * MILLI, 0);
    let mut entered_at = None;
    let mut offsets = std::collections::HashSet::new();
    for t in 1..=600u64 {
        sim.run_tick();
        sim.events.clear();
        sim.cull_except(&[host, pad]);
        let p = sim.genome_of(pad).unwrap();
        if p.stats.exec_foreign == 0 {
            assert_eq!(p.first_foreign_off, None, "tick {t}");
        } else {
            entered_at.get_or_insert(t);
            assert_eq!(p.first_foreign_off, Some(0), "tick {t}");
            offsets.insert((p.ip + 65536 - 1000) % 65536);
        }
        assert_eq!(sim.genome_of(host).unwrap().first_foreign_off, None);
    }
    assert_eq!(entered_at, Some(1));
    assert!(offsets.len() > 5, "the pad stayed at {offsets:?}");
    let p = sim.genome_of(pad).unwrap();
    assert!(p.stats.exec_foreign > 1000);
    // Not in the state hash.
    let h = sim.state_hash();
    let k = sim.orgs.iter().position(|o| o.id == pad).unwrap();
    sim.orgs[k].first_foreign_off = Some(12345);
    assert_eq!(sim.state_hash(), h);
}
