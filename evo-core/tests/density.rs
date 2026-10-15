//! T07: replicator density by uniform sampling (`--density LEN:N`,
//! `--enumerate LEN`, `harness::density`). docs/tasks/T07-density.md §4.

use evo_core::config::Config;
use evo_core::harness::{self, density, density_config, run_alone_with, DensitySource, DensitySpec};
use evo_core::rng::Rng;
use evo_core::sim::ancestor;

fn spec(len: usize, n: u64, ticks: u64, seed: u64) -> DensitySpec {
    DensitySpec { len, n, ticks, source: DensitySource::Uniform { seed }, plant: None, keep_all: false }
}

fn rows_text(r: &harness::DensityResult) -> Vec<String> {
    r.rows.iter().map(|x| x.csv_row()).collect()
}

#[test]
fn density_sample_is_reproducible() {
    // T07 §4 test 1: the same seed gives the same first bodies at any N and
    // any thread count, and the sample is the PRNG stream in order.
    let cfg = Config::default();
    let all = |n, seed, threads| density(&DensitySpec { keep_all: true, ..spec(8, n, 100, seed) }, &cfg, threads);
    let a = all(300, 7, 1);
    let b = all(1000, 7, 4);
    assert_eq!((a.rows.len(), b.rows.len()), (300, 1000));
    assert_eq!(a.counts.iter().sum::<u64>(), 300);
    let mut rng = Rng::new(7);
    for (i, r) in b.rows.iter().enumerate() {
        let want: Vec<u8> = (0..8).map(|_| rng.below(256) as u8).collect();
        assert_eq!((r.index, &r.genome), (i as u64, &want), "body {i}");
    }
    assert_eq!(rows_text(&a)[..], rows_text(&b)[..300]);
    // The same N at another thread count: the same rows and counts.
    let c = all(300, 7, 3);
    assert_eq!((rows_text(&a), a.counts), (rows_text(&c), c.counts));
    // Another seed is another sample.
    assert_ne!(all(300, 8, 1).rows[0].genome, a.rows[0].genome);

    // The CLI: the file and the counts are the same at 1 and 4 threads
    // (stdout's last column is the wall time). 3,000 bodies of 21 bytes
    // keep a few `inexact` rows, so the file is not just its header.
    let exe = env!("CARGO_BIN_EXE_evo-core");
    let dir = std::env::temp_dir().join(format!("evo-test-density-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    let run = |t: u32| {
        let out = dir.join(format!("t{t}.csv"));
        let o = std::process::Command::new(exe)
            .args(["--density", "21:3000", "--density-ticks", "200", "--seed", "3", "--threads", &t.to_string(),
                   "--density-out"])
            .arg(&out)
            .output()
            .unwrap();
        assert!(o.status.success(), "{}", String::from_utf8_lossy(&o.stderr));
        let stdout = String::from_utf8(o.stdout).unwrap();
        let mut lines = stdout.lines();
        assert_eq!(lines.next().unwrap(), harness::DENSITY_SUMMARY_HEADER);
        let row = lines.next().unwrap();
        let counts = row.rsplit_once(',').unwrap().0.to_string();
        (std::fs::read_to_string(&out).unwrap(), counts)
    };
    let (f1, c1) = run(1);
    let (f4, c4) = run(4);
    assert!(f1.lines().count() > 1, "no kept rows: the test is weak");
    assert_eq!(f1.lines().next().unwrap(), harness::DENSITY_HEADER);
    assert!(f1.lines().skip(1).all(|l| !l.contains(",dies,") && !l.contains(",loafer,")));
    assert!(f1 == f4, "the density file differs between 1 and 4 threads");
    assert_eq!(c1, c4);
    assert!(c1.starts_with("21,3000,200,"), "{c1}");
    // The library gives the CLI's counts.
    let lib = density(&spec(21, 3000, 200, 3), &cfg, 2);
    let want: Vec<String> = lib.counts.iter().map(|c| c.to_string()).collect();
    assert_eq!(c1, format!("21,3000,200,{}", want.join(",")));
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn density_finds_the_ancestor_if_planted() {
    // T07 §4 test 2: with body 0 replaced by the 21-byte ancestor the count
    // has one replicator, at index 0; the other bodies do not move.
    let cfg = Config::default();
    let anc = ancestor(64, 16);
    assert_eq!(anc.len(), 21);
    let plain = spec(21, 64, 1000, 1);
    let planted = DensitySpec { plant: Some(anc.clone()), ..plain.clone() };
    let p = density(&planted, &cfg, 4);
    let q = density(&plain, &cfg, 4);
    assert_eq!((p.counts[0], q.counts[0]), (1, 0));
    assert_eq!(p.counts.iter().sum::<u64>(), 64);
    let r0 = &p.rows[0];
    assert_eq!((r0.index, &r0.genome, r0.result.class()), (0, &anc, "replicator"));
    let rest = |r: &harness::DensityResult| rows_text(r).into_iter().filter(|l| !l.starts_with("0,")).collect::<Vec<_>>();
    assert_eq!(rest(&p), rest(&q));
    // The density world (8,192 bytes, 16 patches) gives the lone ancestor
    // the run it has in the default world.
    let small = run_alone_with(&anc, 1000, &density_config(&cfg));
    let big = run_alone_with(&anc, 1000, &cfg);
    assert_eq!(density_config(&cfg).world_size, 8192);
    assert_eq!(
        (small.births, small.exact_births, small.first_birth_tick, small.executed, small.final_energy),
        (big.births, big.exact_births, big.first_birth_tick, big.executed, big.final_energy)
    );
}

#[test]
fn enumerate_covers_every_body() {
    // `--enumerate 1`: the 256 one-byte bodies in order, `pad` among the
    // dead.
    let cfg = Config::default();
    let s = DensitySpec { len: 1, n: 256, ticks: 100, source: DensitySource::Every, plant: None, keep_all: true };
    let r = density(&s, &cfg, 4);
    assert_eq!(r.counts.iter().sum::<u64>(), 256);
    for (i, row) in r.rows.iter().enumerate() {
        assert_eq!((row.index, &row.genome), (i as u64, &vec![i as u8]));
    }
    assert_eq!(r.rows[0].result.class(), "dies");
    // Two bytes, most significant first.
    let two = density(&DensitySpec { len: 2, n: 300, ..s.clone() }, &cfg, 2);
    assert_eq!((&two.rows[0].genome, &two.rows[257].genome), (&vec![0, 0], &vec![1, 1]));
    // The CLI prints n = 256^LEN.
    let o = std::process::Command::new(env!("CARGO_BIN_EXE_evo-core"))
        .args(["--enumerate", "1", "--density-ticks", "100", "--threads", "2"])
        .output()
        .unwrap();
    assert!(o.status.success(), "{}", String::from_utf8_lossy(&o.stderr));
    let out = String::from_utf8(o.stdout).unwrap();
    let c = r.counts;
    assert!(out.contains(&format!("\n1,256,100,{},{},{},{},{},", c[0], c[1], c[2], c[3], c[4])), "{out}");
}
