//! Build script: bake the git commit into the binary so every run directory
//! records which code produced it (docs/instrumentation.md, meta.json).
//!
//! Rust note: cargo compiles and runs this file before the crate itself,
//! like a `build.zig` step. `cargo:rustc-env=K=V` lines become compile-time
//! constants readable with `env!("K")`.

use std::process::Command;

fn git(args: &[&str]) -> Option<String> {
    let out = Command::new("git").args(args).output().ok()?;
    out.status.success().then(|| String::from_utf8_lossy(&out.stdout).trim().to_string())
}

fn main() {
    let commit = git(&["rev-parse", "--short=7", "HEAD"]).unwrap_or_else(|| "unknown".into());
    // Dirty = uncommitted changes or new (unignored) files in this crate.
    let dirty = git(&["status", "--porcelain", "--", "."])
        .map_or(false, |s| !s.is_empty());
    println!("cargo:rustc-env=EVO_GIT_COMMIT={commit}");
    println!("cargo:rustc-env=EVO_GIT_DIRTY={dirty}");
    for p in ["src", "Cargo.toml", "build.rs", "../.git/HEAD", "../.git/index", "../.git/refs"] {
        println!("cargo:rerun-if-changed={p}");
    }
}
