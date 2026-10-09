//! Run recorder: writes a run directory of CSV files (docs/instrumentation.md).
//!
//! The recorder only reads the simulation. It never touches the PRNG or any
//! state the physics uses, so a run with a recorder and a run without one
//! end in the same `Sim::state_hash` (tests/instrumentation.rs).
//!
//! Rust notes for Zig/Go readers:
//! - `BufWriter<File>` is a buffered writer, like Go's `bufio.Writer`.
//!   It flushes when dropped (Rust's destructor), so files are complete
//!   when the `Recorder` goes out of scope.
//! - `io::Result<()>` is Rust's error-or-nothing return, roughly Zig's
//!   `!void`; the `?` operator returns early on error like Zig's `try`.

use crate::config::Config;
use crate::isa::disasm_at;
use crate::sim::{fnv1a, func_hash, Event, OrgStats, Sim};
use std::collections::HashMap;
use std::fs::File;
use std::io::{self, BufWriter, Write};
use std::path::{Path, PathBuf};

/// One row of `genomes.csv`.
struct GenomeRec {
    bytes: Vec<u8>,
    first_tick: u64,
    first_id: u32,
    origin: &'static str,
    parent_hash: u64,
}

/// Values for `meta.json` that are not in `Config`.
pub struct RunInfo {
    pub ticks_requested: u64,
    pub census_every: u64,
    pub ancestor_k: i8,
    pub ancestor_e: i8,
    /// Founders as (genome hex, copies), in seeding order (`--founder`,
    /// E009a); without the flag, the ancestor once.
    pub founders: Vec<(String, u32)>,
    /// Start address of every founder copy, in seeding order.
    pub founder_starts: Vec<u32>,
    /// `--inject` flags as given: (tick, genome hex, copies), E009b.
    pub injections: Vec<(u64, String, u32)>,
}

pub struct Recorder {
    dir: PathBuf,
    info: RunInfo,
    births: BufWriter<File>,
    deaths: BufWriter<File>,
    census: BufWriter<File>,
    orgs: BufWriter<File>,
    patches: BufWriter<File>,
    /// `world.bin`: world bytes and ownership state at every census tick.
    world: BufWriter<File>,
    genomes: HashMap<u64, GenomeRec>,
    /// Patch counters at the previous census row, to write per-interval totals.
    last_absorbed: Vec<i64>,
    last_overflow: Vec<i64>,
    /// Per `--inject` flag, the start of every copy (-1 if skipped); empty
    /// until the injection's tick has run.
    injection_starts: Vec<Vec<i64>>,
}

fn csv(dir: &Path, name: &str, header: &str) -> io::Result<BufWriter<File>> {
    let mut w = BufWriter::new(File::create(dir.join(name))?);
    writeln!(w, "{header}")?;
    Ok(w)
}

pub fn hex(h: u64) -> String {
    format!("{h:016x}")
}

pub fn disasm(bytes: &[u8]) -> String {
    let mut parts = Vec::new();
    let mut i = 0;
    while i < bytes.len() {
        let (t, l) = disasm_at(bytes, i);
        parts.push(t);
        i += l;
    }
    parts.join(" ; ")
}

impl Recorder {
    /// Create `dir` and the CSV files, and register the genomes already
    /// seeded into `sim` (origin `seed`). Call after seeding, before the
    /// first tick.
    pub fn create(dir: &Path, sim: &Sim, info: RunInfo) -> io::Result<Recorder> {
        std::fs::create_dir_all(dir)?;
        // Labels from an earlier run in the same directory would silently
        // mislabel this one; `--classify` regenerates them.
        match std::fs::remove_file(dir.join("classes.csv")) {
            Err(e) if e.kind() != io::ErrorKind::NotFound => return Err(e),
            _ => {}
        }
        let s = OrgStats::CSV_HEADER;
        let mut r = Recorder {
            dir: dir.to_path_buf(),
            info,
            births: csv(dir, "births.csv", "tick,child,executor,source,start,len,copy_errors,slips,endowment_m,raw_hash,parent_hash,parent_now_hash,source_hash")?,
            deaths: csv(dir, "deaths.csv", &format!("tick,id,cause,age,offspring,len,start,pending_len,ip_off,op_at_ip,energy_m,pool_m,birth_hash,now_hash,{s}"))?,
            census: csv(dir, "census.csv", "tick,now_hash,count")?,
            orgs: csv(dir, "orgs.csv", &format!("tick,id,parent,birth_tick,start,len,pending_len,energy_m,ip_off,op_at_ip,birth_hash,now_hash,offspring,{s}"))?,
            patches: csv(dir, "patches.csv", "tick,patch,pool_m,orgs,absorbed_m,overflow_m")?,
            world: BufWriter::new(File::create(dir.join("world.bin"))?),
            genomes: HashMap::new(),
            last_absorbed: sim.patches.iter().map(|p| p.absorbed).collect(),
            last_overflow: sim.patches.iter().map(|p| p.overflow).collect(),
            injection_starts: Vec::new(),
        };
        r.injection_starts = vec![Vec::new(); r.info.injections.len()];
        for o in sim.orgs.iter().filter(|o| o.alive) {
            r.add_genome(o.genome_hash, &o.genome, sim.tick, o.id, "seed", 0);
        }
        r.write_meta(&sim.cfg, None)?;
        Ok(r)
    }

    fn add_genome(&mut self, hash: u64, bytes: &[u8], tick: u64, id: u32, origin: &'static str, parent: u64) {
        self.genomes.entry(hash).or_insert_with(|| GenomeRec {
            bytes: bytes.to_vec(),
            first_tick: tick,
            first_id: id,
            origin,
            parent_hash: parent,
        });
    }

    /// Register an injection just performed (`Sim::inject_due`, E009b):
    /// the copies placed are recorded as founders are (a `genomes.csv` row
    /// with origin `seed` if the genome is new, no `births.csv` row; their
    /// deaths and census rows as usual), and the starts go to `meta.json`.
    pub fn injected(&mut self, sim: &Sim, done: &crate::sim::Injected) {
        self.injection_starts[done.index] = done.starts.clone();
        if let Some(o) = done.ids.first().and_then(|&id| sim.genome_of(id)) {
            let (h, g, t, id) = (o.genome_hash, o.genome.clone(), o.birth_tick, o.id);
            self.add_genome(h, &g, t, id, "seed", 0);
        }
    }

    /// Write rows for the events of one tick. Call after `run_tick`, before
    /// anything else mutates `sim`.
    pub fn events(&mut self, sim: &Sim, events: &[Event]) -> io::Result<()> {
        for ev in events {
            match *ev {
                Event::Birth {
                    tick, child, executor, source, start, len, copy_errors, slips,
                    genome_hash, parent_hash, parent_now_hash, source_hash, endowment,
                } => {
                    writeln!(
                        self.births,
                        "{tick},{child},{executor},{source},{start},{len},{copy_errors},{slips},{endowment},{},{},{},{}",
                        hex(genome_hash), hex(parent_hash), hex(parent_now_hash), hex(source_hash)
                    )?;
                    let c = sim.genome_of(child).expect("child exists");
                    // The executor's body as it was at `divide`, if it changed
                    // since birth. Its bytes are read now, after the tick, so
                    // keep them only if they still hash to what `divide` saw;
                    // an exact child carries the same bytes. Otherwise the
                    // child's parent link below points at a hash with no row.
                    if parent_now_hash != parent_hash && !self.genomes.contains_key(&parent_now_hash) {
                        let now = sim.genome_of(executor).map(|p| sim.region(p.start, p.len));
                        let bytes = match now {
                            Some(b) if fnv1a(&b) == parent_now_hash => Some(b),
                            _ if genome_hash == parent_now_hash => Some(c.genome.clone()),
                            _ => None,
                        };
                        if let Some(b) = bytes {
                            self.add_genome(parent_now_hash, &b, tick, executor, "somatic", parent_hash);
                        }
                    }
                    // A child's lineage parent is the executor's body at
                    // `divide` (see docs/instrumentation.md, genomes.csv).
                    self.add_genome(genome_hash, &c.genome, tick, child, "birth", parent_now_hash);
                }
                Event::Death {
                    tick, id, cause, age, offspring, start, len, pending_len, ip_off,
                    op_at_ip, energy, pool, birth_hash, now_hash, stats,
                } => {
                    writeln!(
                        self.deaths,
                        "{tick},{id},{},{age},{offspring},{len},{start},{pending_len},{ip_off},{},{energy},{pool},{},{},{}",
                        cause.name(), op_at_ip.name(), hex(birth_hash), hex(now_hash), stats.csv_row()
                    )?;
                }
            }
        }
        Ok(())
    }

    /// Census, per-organism, and per-patch rows for the current tick.
    pub fn snapshot(&mut self, sim: &Sim) -> io::Result<()> {
        let t = sim.tick;
        let mut counts: HashMap<u64, usize> = HashMap::new();
        let mut per_patch = vec![0usize; sim.patches.len()];
        for o in sim.orgs.iter().filter(|o| o.alive) {
            let body = sim.region(o.start, o.len);
            let now = fnv1a(&body);
            *counts.entry(now).or_insert(0) += 1;
            if now != o.genome_hash {
                self.add_genome(now, &body, t, o.id, "somatic", o.genome_hash);
            }
            per_patch[sim.patch_of(o.start)] += 1;
            let pending_len = o.pending.map_or(0, |(_, l)| l);
            let op = crate::isa::decode(sim.bytes[o.ip as usize]).0;
            writeln!(
                self.orgs,
                "{t},{},{},{},{},{},{pending_len},{},{},{},{},{},{},{}",
                o.id, o.parent, o.birth_tick, o.start, o.len, o.energy, sim.ip_off(o), op.name(),
                hex(o.genome_hash), hex(now), o.offspring, o.stats.csv_row()
            )?;
        }
        // Sorted so the file is identical across runs (HashMap order is random).
        let mut counts: Vec<_> = counts.into_iter().collect();
        counts.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
        for (h, c) in counts {
            writeln!(self.census, "{t},{},{c}", hex(h))?;
        }
        for (k, p) in sim.patches.iter().enumerate() {
            writeln!(
                self.patches,
                "{t},{k},{},{},{},{}",
                p.pool, per_patch[k], p.absorbed - self.last_absorbed[k], p.overflow - self.last_overflow[k]
            )?;
            self.last_absorbed[k] = p.absorbed;
            self.last_overflow[k] = p.overflow;
        }
        // World snapshot: one record per census tick (docs/instrumentation.md).
        // Dead bodies keep their bytes in free memory (E005's trampolines),
        // so the bytes are the only way to read what an IP ran there.
        let n = sim.bytes.len() as u32;
        self.world.write_all(&t.to_le_bytes())?;
        self.world.write_all(&n.to_le_bytes())?;
        self.world.write_all(&sim.bytes)?;
        let state: Vec<u8> = sim
            .owner
            .iter()
            .map(|&o| if o == crate::sim::FREE { 0 } else if o == crate::sim::DEBRIS { 1 } else { 2 })
            .collect();
        self.world.write_all(&state)?;
        Ok(())
    }

    fn write_meta(&self, cfg: &Config, ticks_run: Option<u64>) -> io::Result<()> {
        let mut w = BufWriter::new(File::create(self.dir.join("meta.json"))?);
        writeln!(w, "{{")?;
        writeln!(w, "  \"crate_version\": \"{}\",", env!("CARGO_PKG_VERSION"))?;
        writeln!(w, "  \"git_commit\": \"{}\",", env!("EVO_GIT_COMMIT"))?;
        writeln!(w, "  \"git_dirty\": {},", env!("EVO_GIT_DIRTY"))?;
        writeln!(w, "  \"ticks_requested\": {},", self.info.ticks_requested)?;
        match ticks_run {
            Some(t) => writeln!(w, "  \"ticks_run\": {t},")?,
            None => writeln!(w, "  \"ticks_run\": null,")?,
        }
        writeln!(w, "  \"census_every\": {},", self.info.census_every)?;
        writeln!(w, "  \"ancestor_k\": {},", self.info.ancestor_k)?;
        writeln!(w, "  \"ancestor_e\": {},", self.info.ancestor_e)?;
        let founders: Vec<String> = self
            .info
            .founders
            .iter()
            .map(|(h, n)| format!("{{\"hex\": \"{h}\", \"count\": {n}}}"))
            .collect();
        writeln!(w, "  \"founders\": [{}],", founders.join(", "))?;
        let starts: Vec<String> = self.info.founder_starts.iter().map(|s| s.to_string()).collect();
        writeln!(w, "  \"founder_starts\": [{}],", starts.join(", "))?;
        let injections: Vec<String> = self
            .info
            .injections
            .iter()
            .zip(&self.injection_starts)
            .map(|((t, h, n), s)| {
                let s: Vec<String> = s.iter().map(|x| x.to_string()).collect();
                format!("{{\"tick\": {t}, \"hex\": \"{h}\", \"count\": {n}, \"starts\": [{}]}}", s.join(", "))
            })
            .collect();
        writeln!(w, "  \"injections\": [{}],", injections.join(", "))?;
        writeln!(w, "  \"config\": {{")?;
        let fields = cfg.fields();
        for (n, (k, v)) in fields.iter().enumerate() {
            let comma = if n + 1 < fields.len() { "," } else { "" };
            writeln!(w, "    \"{k}\": {v}{comma}")?;
        }
        writeln!(w, "  }}")?;
        writeln!(w, "}}")?;
        Ok(())
    }

    /// Write `genomes.csv` and the final `meta.json`, and flush everything.
    pub fn finish(mut self, sim: &Sim) -> io::Result<()> {
        let mut g = csv(&self.dir, "genomes.csv", "raw_hash,func_hash,len,first_tick,first_id,origin,parent_hash,bytes_hex,disasm")?;
        let mut rows: Vec<_> = self.genomes.iter().collect();
        rows.sort_by_key(|(h, r)| (r.first_tick, r.first_id, **h));
        for (h, r) in rows {
            let bytes_hex: String = r.bytes.iter().map(|b| format!("{b:02x}")).collect();
            writeln!(
                g,
                "{},{},{},{},{},{},{},{bytes_hex},{}",
                hex(*h), hex(func_hash(&r.bytes)), r.bytes.len(), r.first_tick, r.first_id,
                r.origin, hex(r.parent_hash), disasm(&r.bytes)
            )?;
        }
        g.flush()?;
        self.write_meta(&sim.cfg, Some(sim.tick))?;
        for w in [&mut self.births, &mut self.deaths, &mut self.census, &mut self.orgs, &mut self.patches, &mut self.world] {
            w.flush()?;
        }
        Ok(())
    }
}
