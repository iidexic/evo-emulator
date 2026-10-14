//! T04: full-state snapshots and replay from a tick, through the CLI as
//! E016 uses them (docs/tasks/T04-snapshots-replay.md): `--state-every N`
//! with `--out DIR` writes `DIR/state/<tick>.bin` every N ticks and at the
//! final tick; `--replay-from FILE [--seed S]` runs on from one to the
//! absolute `--ticks`. The lib-level tests (`snapshot_round_trips`, the
//! loader's refusals) are in `sim.rs`.
//!
//! The spec's `replay_events_match` records 10,000 ticks and replays from
//! 5,000; here it is 5,000 from 2,500 (the debug build runs about 250
//! ticks a second), once in the default world with the std ancestor and
//! once in E016's `tierra_t50` world (`--ancestor tierra --sun 2
//! --cycle-theft-pct 50`).

use evo_core::config::Config;
use evo_core::sim::Sim;
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::process::Command;

const EXE: &str = env!("CARGO_BIN_EXE_evo-core");

fn scratch(name: &str) -> PathBuf {
    let d = std::env::temp_dir().join(format!("evo-test-t04-{name}-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&d);
    std::fs::create_dir_all(&d).unwrap();
    d
}

fn s(p: &Path) -> &str {
    p.to_str().unwrap()
}

/// Run the CLI and return its stderr; fail the test if it fails.
fn evo(args: &[&str]) -> String {
    let o = Command::new(EXE).args(args).output().unwrap();
    assert!(o.status.success(), "evo-core {} failed: {}", args.join(" "), String::from_utf8_lossy(&o.stderr));
    String::from_utf8(o.stderr).unwrap()
}

/// Run the CLI expecting a refusal (exit status 2); return its stderr.
fn refused(args: &[&str]) -> String {
    let o = Command::new(EXE).args(args).output().unwrap();
    assert_eq!(o.status.code(), Some(2), "evo-core {} was not refused", args.join(" "));
    String::from_utf8(o.stderr).unwrap()
}

/// Data rows of a run-directory CSV whose tick (first column) passes `keep`.
fn rows(dir: &Path, name: &str, keep: impl Fn(u64) -> bool) -> Vec<String> {
    let text = std::fs::read_to_string(dir.join(name)).unwrap();
    text.lines()
        .skip(1)
        .filter(|l| keep(l.split(',').next().unwrap().parse().unwrap()))
        .map(String::from)
        .collect()
}

/// `world.bin` records (tick, record bytes) whose tick passes `keep`.
fn world(dir: &Path, keep: impl Fn(u64) -> bool) -> Vec<(u64, Vec<u8>)> {
    let b = std::fs::read(dir.join("world.bin")).unwrap();
    let mut out = Vec::new();
    let mut at = 0;
    while at < b.len() {
        let tick = u64::from_le_bytes(b[at..at + 8].try_into().unwrap());
        let n = u32::from_le_bytes(b[at + 8..at + 12].try_into().unwrap()) as usize;
        let end = at + 12 + 2 * n;
        if keep(tick) {
            out.push((tick, b[at..end].to_vec()));
        }
        at = end;
    }
    out
}

/// `genomes.csv` as raw hash -> its nine fields.
fn genomes(dir: &Path) -> HashMap<String, Vec<String>> {
    let text = std::fs::read_to_string(dir.join("genomes.csv")).unwrap();
    let mut lines = text.lines();
    assert_eq!(lines.next().unwrap(), "raw_hash,func_hash,len,first_tick,first_id,origin,parent_hash,bytes_hex,disasm");
    lines
        .map(|l| {
            let f: Vec<String> = l.splitn(9, ',').map(String::from).collect();
            (f[0].clone(), f)
        })
        .collect()
}

fn load(file: &Path, cfg: &Config) -> Sim {
    let mut f = std::io::BufReader::new(std::fs::File::open(file).unwrap());
    Sim::load_state(&mut f, cfg.clone()).unwrap()
}

/// Record `--seed 5 --ticks 5000 --census 500 --state-every 2500` under
/// `flags` (whose config is `cfg`), replay from the 2,500 snapshot to
/// 5,000 without `--seed`, and check that the replay is the original's
/// continuation: the same state file at 5,000 (so the same state hash),
/// the same rows in every CSV after 2,500, the same world.bin records, and
/// genomes.csv agreeing apart from where each genome was first seen.
/// Returns the snapshot at 2,500 and the state hash at 5,000.
fn replay_matches(name: &str, flags: &[&str], cfg: &Config) -> (Sim, u64) {
    const T: u64 = 2500;
    let dir = scratch(name);
    let (a, b) = (dir.join("orig"), dir.join("replay"));
    let common = ["--ticks", "5000", "--census", "500", "--state-every", "2500"];
    let mut args = vec!["--seed", "5", "--out", s(&a)];
    args.extend(common);
    args.extend(flags);
    evo(&args);
    let snap = a.join("state").join("2500.bin");
    assert!(a.join("state").join("5000.bin").exists());
    let mut args = vec!["--replay-from", s(&snap), "--out", s(&b)];
    args.extend(common);
    args.extend(flags);
    let err = evo(&args);
    assert!(err.contains("at tick 2500 (seed 5, stream continued)"), "{err}");

    // The state at 5,000: the same file, so the same hash.
    let (fa, fb) = (a.join("state").join("5000.bin"), b.join("state").join("5000.bin"));
    assert!(!b.join("state").join("2500.bin").exists(), "the replay rewrote its own start");
    assert!(std::fs::read(&fa).unwrap() == std::fs::read(&fb).unwrap(), "{name}: the state files at 5000 differ");
    let (ha, hb) = (load(&fa, cfg).state_hash(), load(&fb, cfg).state_hash());
    assert_eq!(ha, hb, "{name}: state hash at 5000");
    let start = load(&snap, cfg);
    assert_eq!(start.tick, T);
    assert_ne!(start.state_hash(), ha);

    // Events and census rows after the snapshot tick. The replay's first
    // census, at the snapshot tick, is the original's census there too
    // (patches.csv's per-interval totals at that tick are 0 in the replay).
    for f in ["births.csv", "deaths.csv", "census.csv", "orgs.csv", "patches.csv"] {
        let (ra, rb) = (rows(&a, f, |t| t > T), rows(&b, f, |t| t > T));
        assert!(!ra.is_empty(), "{name}: {f} has no rows after {T}: the test is vacuous");
        assert!(ra == rb, "{name}: {f} rows after {T} differ ({} against {} rows)", ra.len(), rb.len());
    }
    for f in ["census.csv", "orgs.csv"] {
        assert!(rows(&a, f, |t| t == T) == rows(&b, f, |t| t == T), "{name}: {f} at {T}");
    }
    assert!(rows(&b, "births.csv", |t| t <= T).is_empty());
    let (wa, wb) = (world(&a, |t| t >= T), world(&b, |t| t >= T));
    assert_eq!(wa.iter().map(|w| w.0).collect::<Vec<_>>(), (5..=10).map(|k| 500 * k).collect::<Vec<u64>>());
    assert!(wa == wb, "{name}: world.bin records from {T} differ");

    // genomes.csv. Every genome alive at the snapshot is a `replay` row
    // first seen at it, with parent 0, and every row agrees with the
    // original's on the genome itself; genomes the original first saw
    // after the snapshot have identical rows in both.
    let (ga, gb) = (genomes(&a), genomes(&b));
    let alive: std::collections::HashSet<u64> = start.orgs.iter().filter(|o| o.alive).map(|o| o.genome_hash).collect();
    let replayed: Vec<&Vec<String>> = gb.values().filter(|r| r[5] == "replay").collect();
    assert_eq!(replayed.len(), alive.len(), "{name}: one replay row per genome alive at {T}");
    for (h, r) in &gb {
        let o = ga.get(h).unwrap_or_else(|| panic!("{name}: replay genome {h} not in the original"));
        assert_eq!((&o[1], &o[2], &o[7], &o[8]), (&r[1], &r[2], &r[7], &r[8]), "{name}: genome {h}");
        if r[5] == "replay" {
            assert!(alive.contains(&u64::from_str_radix(h, 16).unwrap()));
            assert_eq!((r[3].as_str(), r[6].as_str()), ("2500", "0000000000000000"), "{name}: {r:?}");
        }
    }
    let late: Vec<_> = ga.iter().filter(|(_, o)| o[3].parse::<u64>().unwrap() > T).collect();
    assert!(!late.is_empty());
    for (h, o) in late {
        assert_eq!(gb.get(h), Some(o), "{name}: genome {h} first seen after {T}");
    }

    let meta = std::fs::read_to_string(b.join("meta.json")).unwrap();
    for key in ["\"tick\": 2500, \"file_seed\": 5, \"reseed\": null}", "\"state_every\": 2500,", "\"ticks_run\": 5000,", "\"seed\": 5,"] {
        assert!(meta.contains(key), "{name}: meta.json lacks {key}:\n{meta}");
    }
    assert!(meta.contains("\"replay_from\": {\"path\": \""));
    let orig_meta = std::fs::read_to_string(a.join("meta.json")).unwrap();
    assert!(orig_meta.contains("\"replay_from\": null,"));
    eprintln!("{name}: state hash at 5000 0x{ha:016x} in both; {} replay genomes; snapshot {} bytes",
              replayed.len(), std::fs::metadata(&snap).unwrap().len());
    let _ = std::fs::remove_dir_all(&dir);
    (start, ha)
}

#[test]
fn replay_events_match() {
    // T04 §4 test 2, default physics, the std ancestor.
    replay_matches("default", &[], &Config::default());
}

#[test]
fn replay_events_match_tierra_theft() {
    // The same in E016's `tierra_t50` world: `--sun 2` scales the patch
    // income and cap, theft debt is in the state.
    let mut cfg = Config::default();
    cfg.patch_income *= 2;
    cfg.patch_cap *= 2;
    cfg.cycle_theft_pct = 50;
    let (start, _) = replay_matches("tierra-t50", &["--ancestor", "tierra", "--sun", "2", "--cycle-theft-pct", "50"], &cfg);
    // The snapshot carries the state theft adds, so the test covers it.
    assert!(start.orgs.iter().any(|o| o.cycle_debt > 0), "no organism owes cycles at 2500");
    assert!(start.orgs.iter().any(|o| o.first_foreign_off.is_some()));
}

#[test]
fn replay_reseed_diverges_deterministically() {
    // T04 §4 test 3: `--seed 2` from the same file twice gives the same
    // state, and not the continuation's; the continuation is the original.
    let dir = scratch("reseed");
    let a = dir.join("orig");
    evo(&["--seed", "5", "--ticks", "1000", "--census", "250", "--state-every", "500", "--out", s(&a)]);
    let snap = a.join("state").join("500.bin");
    let run = |name: &str, seed: Option<&str>| {
        let d = dir.join(name);
        let mut args = vec!["--replay-from", s(&snap), "--ticks", "1000", "--census", "250", "--state-every", "500", "--out", s(&d)];
        if let Some(x) = seed {
            args.extend(["--seed", x]);
        }
        evo(&args);
        let f = d.join("state").join("1000.bin");
        (load(&f, &Config::default()).state_hash(), std::fs::read(&f).unwrap(), std::fs::read_to_string(d.join("meta.json")).unwrap())
    };
    let (h1, f1, m1) = run("s2a", Some("2"));
    let (h2, f2, _) = run("s2b", Some("2"));
    let (hc, fc, mc) = run("cont", None);
    assert_eq!(h1, h2);
    assert!(f1 == f2);
    assert_ne!(h1, hc, "re-seeding did not change the run");
    assert!(fc == std::fs::read(a.join("state").join("1000.bin")).unwrap(), "the continuation is not the original");
    assert!(m1.contains("\"tick\": 500, \"file_seed\": 5, \"reseed\": 2}") && m1.contains("\"seed\": 2,"), "{m1}");
    assert!(mc.contains("\"reseed\": null}") && mc.contains("\"seed\": 5,"), "{mc}");
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn loader_refuses_a_config_mismatch() {
    // T04 §4 test 4: a file saved under --cycle-theft-pct 50 is refused
    // under no flag, naming the field; and the CLI's other refusals.
    let dir = scratch("refuse");
    let a = dir.join("orig");
    evo(&["--seed", "5", "--ticks", "200", "--cycle-theft-pct", "50", "--state-every", "100", "--out", s(&a)]);
    let snap = a.join("state").join("100.bin");
    let e = refused(&["--replay-from", s(&snap), "--ticks", "200"]);
    assert!(e.contains("cycle_theft_pct") && e.contains("50"), "{e}");
    let e = refused(&["--replay-from", s(&snap), "--ticks", "200", "--cycle-theft-pct", "50", "--sun", "2"]);
    assert!(e.contains("patch_income"), "{e}");
    // The matching flags and another seed run.
    evo(&["--replay-from", s(&snap), "--ticks", "150", "--cycle-theft-pct", "50", "--seed", "9"]);
    let theft = ["--replay-from", s(&snap), "--cycle-theft-pct", "50"];
    let with = |more: &[&str]| -> Vec<String> { theft.iter().chain(more).map(|x| x.to_string()).collect() };
    let r = |more: &[&str]| {
        let v = with(more);
        refused(&v.iter().map(String::as_str).collect::<Vec<_>>())
    };
    assert!(r(&["--ticks", "100"]).contains("not above the snapshot's tick 100"));
    assert!(r(&["--ticks", "200", "--inject", "100:000000:1"]).contains("--inject at tick 100"));
    assert!(r(&["--ticks", "200", "--founder", "000000:1"]).contains("--founder"));
    assert!(r(&["--ticks", "200", "--state-every", "50"]).contains("needs --out"));
    assert!(refused(&["--replay-from", s(&dir.join("none.bin")), "--ticks", "200"]).contains("none.bin"));
    // An injection after the snapshot works and is recorded as usual.
    let d = dir.join("inject");
    let v = with(&["--ticks", "120", "--inject", "110:000000:2", "--out", s(&d)]);
    evo(&v.iter().map(String::as_str).collect::<Vec<_>>());
    let meta = std::fs::read_to_string(d.join("meta.json")).unwrap();
    assert!(meta.contains("{\"tick\": 110, \"hex\": \"000000\", \"count\": 2, \"starts\": [") && !meta.contains("\"starts\": []"), "{meta}");
    let g = genomes(&d);
    assert!(g.values().any(|r| r[7] == "000000" && r[5] == "seed" && r[3] == "110"));
    let _ = std::fs::remove_dir_all(&dir);
}
