//! World, organisms, and the tick loop. PLAN.md §5.1–5.4, §5.7.
//!
//! Rust notes for Zig/Go readers:
//! - `Vec<T>` is a growable array (Zig `ArrayList`, Go slice with append).
//! - `Option<T>` is a value that may be absent; `match`/`if let` unpack it.
//!   There is no nil: a missing pending region is `None`, not a zero start.
//! - Methods take `&self` (read) or `&mut self` (write). Only one `&mut`
//!   may exist at a time, which is why the executor functions below take
//!   an organism *index* and reach into `self.orgs[i]`, instead of holding a
//!   `&mut Org` while also mutating `self.world`.

use crate::config::{Config, MILLI};
use crate::isa::{decode, reg_of, Op};
use crate::rng::Rng;

pub const FREE: u32 = 0;
pub const DEBRIS: u32 = 1;
pub const FIRST_ID: u32 = 2;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DeathCause {
    Upkeep,
    /// Removed by the single-genome harness, not by physics.
    Harness,
}

#[derive(Clone, Debug)]
pub enum Event {
    Birth {
        tick: u64,
        child: u32,
        executor: u32,
        /// Owner id of the first byte copied into the child's region, or
        /// DEBRIS/FREE if the child was scavenged without copying.
        source: u32,
        len: u32,
        /// Bit flips that landed in the child's region while it was pending.
        copy_errors: u32,
        /// Slips that landed in the child's region while it was pending.
        slips: u32,
        genome_hash: u64,
        parent_hash: u64,
        endowment: i64,
    },
    Death {
        tick: u64,
        id: u32,
        cause: DeathCause,
        age: u64,
        offspring: u32,
    },
}

#[derive(Clone, Debug)]
pub struct Org {
    pub id: u32,
    pub regs: [u32; 4],
    pub ip: u32,
    pub flag: bool,
    pub energy: i64,
    pub start: u32,
    pub len: u32,
    pub pending: Option<(u32, u32)>, // (start, len)
    pub pending_source: Option<u32>,
    pub pending_errors: u32,
    pub pending_slips: u32,
    pub alive: bool,
    pub birth_tick: u64,
    pub offspring: u32,
    pub genome_hash: u64,
    pub genome: Vec<u8>,
    pub parent: u32,
    pub executed: u64,
}

#[derive(Clone, Debug)]
pub struct Patch {
    pub pool: i64,
}

pub struct Sim {
    pub cfg: Config,
    pub rng: Rng,
    pub bytes: Vec<u8>,
    pub owner: Vec<u32>,
    pub patches: Vec<Patch>,
    pub orgs: Vec<Org>,
    pub tick: u64,
    pub events: Vec<Event>,
    next_id: u32,
    /// Total energy that has entered the world (sunlight), for conservation checks.
    pub energy_in: i64,
    /// Total energy dissipated by instruction costs and upkeep.
    pub energy_out: i64,
    /// Total energy lost to patch cap overflow.
    pub energy_overflow: i64,
}

pub fn fnv1a(bytes: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for &b in bytes {
        h ^= b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

impl Sim {
    pub fn new(cfg: Config) -> Sim {
        let n = cfg.world_size as usize;
        let np = (n + cfg.patch_size as usize - 1) / cfg.patch_size as usize;
        Sim {
            rng: Rng::new(cfg.seed),
            bytes: vec![0; n],
            owner: vec![FREE; n],
            patches: (0..np).map(|_| Patch { pool: if cfg.pools_start_full { cfg.patch_cap } else { 0 } }).collect(),
            orgs: Vec::new(),
            tick: 0,
            events: Vec::new(),
            next_id: FIRST_ID,
            energy_in: 0,
            energy_out: 0,
            energy_overflow: 0,
            cfg,
        }
    }

    // ---- addressing helpers -------------------------------------------

    #[inline]
    pub fn wrap(&self, a: u32) -> u32 {
        a % self.cfg.world_size
    }

    #[inline]
    fn off(&self, a: u32, d: i64) -> u32 {
        let n = self.cfg.world_size as i64;
        (((a as i64 + d) % n + n) % n) as u32
    }

    #[inline]
    pub fn ring_dist(&self, a: u32, b: u32) -> u32 {
        let n = self.cfg.world_size;
        let a = a % n;
        let b = b % n;
        let d = if a > b { a - b } else { b - a };
        d.min(n - d)
    }

    #[inline]
    fn in_range(&self, ip: u32, addr: u32) -> bool {
        self.ring_dist(ip, addr) <= self.cfg.locality
    }

    fn patch_of(&self, addr: u32) -> usize {
        (self.wrap(addr) / self.cfg.patch_size) as usize
    }

    fn org_index(&self, id: u32) -> Option<usize> {
        // ids are allocated sequentially from FIRST_ID, so index = id - FIRST_ID.
        let i = id.checked_sub(FIRST_ID)? as usize;
        if i < self.orgs.len() { Some(i) } else { None }
    }

    // ---- seeding --------------------------------------------------------

    /// Place a genome at `start` as a living organism with `energy` milli-units.
    pub fn seed(&mut self, start: u32, genome: &[u8], energy: i64, parent: u32) -> u32 {
        let id = self.next_id;
        self.next_id += 1;
        for (k, &b) in genome.iter().enumerate() {
            let a = self.wrap(start + k as u32) as usize;
            self.bytes[a] = b;
            self.owner[a] = id;
        }
        self.orgs.push(Org {
            id,
            regs: [0; 4],
            ip: self.wrap(start),
            flag: false,
            energy,
            start: self.wrap(start),
            len: genome.len() as u32,
            pending: None,
            pending_source: None,
            pending_errors: 0,
            pending_slips: 0,
            alive: true,
            birth_tick: self.tick,
            offspring: 0,
            genome_hash: fnv1a(genome),
            genome: genome.to_vec(),
            parent,
            executed: 0,
        });
        id
    }

    // ---- memory access with physics ------------------------------------

    /// Attempt a write by organism `i` at `addr`. Applies locality, write
    /// protection, and write noise. Returns whether the write landed.
    fn write(&mut self, i: usize, addr: u32, val: u8) -> bool {
        let addr = self.wrap(addr);
        let ip = self.orgs[i].ip;
        if !self.in_range(ip, addr) {
            self.orgs[i].flag = true;
            return false;
        }
        let own = self.owner[addr as usize];
        let me = self.orgs[i].id;
        if self.cfg.write_protection && own >= FIRST_ID && own != me {
            self.orgs[i].flag = true;
            return false;
        }
        let mut v = val;
        if self.rng.chance(self.cfg.p_write_flip) {
            v ^= 1 << self.rng.below(8);
            if let Some((ps, pl)) = self.orgs[i].pending {
                if self.ring_dist(ps, addr) < pl && self.wrap(addr.wrapping_sub(ps)) < pl {
                    self.orgs[i].pending_errors += 1;
                }
            }
        }
        self.bytes[addr as usize] = v;
        true
    }

    fn read(&mut self, i: usize, addr: u32) -> u8 {
        let addr = self.wrap(addr);
        if !self.in_range(self.orgs[i].ip, addr) {
            self.orgs[i].flag = true;
            return 0;
        }
        self.bytes[addr as usize]
    }

    // ---- one instruction ----------------------------------------------

    /// Execute one instruction for organism `i`. Returns the energy charged,
    /// or None if the organism could not afford the base cost (nothing runs).
    /// `cap_left` is the per-tick budget still available.
    fn step(&mut self, i: usize, cap_left: i64) -> Option<i64> {
        let cfg_cost_simple = self.cfg.cost_simple;
        let ip = self.orgs[i].ip;
        let byte = self.bytes[ip as usize];
        let (op, m) = decode(byte);
        let r = reg_of(m);
        let base = match op {
            Op::Load => self.cfg.cost_load,
            Op::Store => self.cfg.cost_store,
            Op::Copy => self.cfg.cost_copy,
            Op::Searchf | Op::Searchb => self.cfg.cost_search_base,
            Op::Alloc => self.cfg.cost_alloc_base,
            Op::Divide => self.cfg.cost_divide,
            Op::Absorb => self.cfg.cost_absorb,
            _ => cfg_cost_simple,
        };
        if self.orgs[i].energy < base || cap_left < base {
            return None;
        }
        let mut cost = base;
        let next = self.wrap(ip + op.len());
        let mut new_ip = next;

        match op {
            Op::Pad | Op::Nop0 | Op::Nop1 => {}
            Op::Inc => self.orgs[i].regs[r] = self.orgs[i].regs[r].wrapping_add(1),
            Op::Dec => self.orgs[i].regs[r] = self.orgs[i].regs[r].wrapping_sub(1),
            Op::Shl => self.orgs[i].regs[r] <<= 1,
            Op::Shr => self.orgs[i].regs[r] >>= 1,
            Op::Add => {
                let v = self.orgs[i].regs[r];
                self.orgs[i].regs[0] = self.orgs[i].regs[0].wrapping_add(v);
            }
            Op::Sub => {
                let v = self.orgs[i].regs[r];
                self.orgs[i].regs[0] = self.orgs[i].regs[0].wrapping_sub(v);
            }
            Op::Zero => self.orgs[i].regs[r] = 0,
            Op::Lit => {
                let v = self.bytes[self.wrap(ip + 1) as usize] as i8 as i32 as u32;
                self.orgs[i].regs[r] = v;
            }
            Op::Swap => self.orgs[i].regs.swap(0, r),
            Op::Skipz | Op::Skipnz => {
                let z = self.orgs[i].regs[r] == 0;
                if z == (op == Op::Skipz) {
                    let (nop, _) = decode(self.bytes[next as usize]);
                    new_ip = self.wrap(next + nop.len());
                }
            }
            Op::Jmpr => new_ip = self.off(next, self.orgs[i].regs[r] as i32 as i64),
            Op::Jmpa => new_ip = self.wrap(self.orgs[i].regs[r]),
            Op::Self_ => match m {
                0 => {
                    self.orgs[i].regs[0] = self.orgs[i].start;
                    self.orgs[i].regs[1] = self.orgs[i].len;
                }
                1 => self.orgs[i].regs[0] = ip,
                _ => {
                    self.orgs[i].regs[0] = self.orgs[i].flag as u32;
                    self.orgs[i].flag = false;
                }
            },
            Op::Load => {
                let a = self.orgs[i].regs[0];
                let v = self.read(i, a);
                self.orgs[i].regs[r] = v as u32;
            }
            Op::Store => {
                let a = self.orgs[i].regs[0];
                let v = self.orgs[i].regs[r] as u8;
                self.write(i, a, v);
            }
            Op::Copy => {
                let a = self.orgs[i].regs[0];
                let b = self.orgs[i].regs[1];
                let v = self.read(i, b);
                // Record the copy source for lineage: owner of the first byte
                // copied into the pending region.
                if self.orgs[i].pending_source.is_none() {
                    if let Some((ps, pl)) = self.orgs[i].pending {
                        if self.wrap(a.wrapping_sub(ps)) < pl {
                            self.orgs[i].pending_source = Some(self.owner[self.wrap(b) as usize]);
                        }
                    }
                }
                self.write(i, a, v);
                let (mut da, mut db) = (1u32, 1u32);
                if self.rng.chance(self.cfg.q_slip) {
                    match self.rng.below(4) {
                        0 => da = 0,
                        1 => da = 2,
                        2 => db = 0,
                        _ => db = 2,
                    }
                    if let Some((ps, pl)) = self.orgs[i].pending {
                        if self.wrap(a.wrapping_sub(ps)) < pl {
                            self.orgs[i].pending_slips += 1;
                        }
                    }
                }
                self.orgs[i].regs[0] = a.wrapping_add(da);
                self.orgs[i].regs[1] = b.wrapping_add(db);
            }
            Op::Searchf | Op::Searchb => {
                // Read template.
                let mut tmpl: Vec<bool> = Vec::new();
                let mut p = next;
                loop {
                    let (o, _) = decode(self.bytes[p as usize]);
                    if !o.is_nop() || tmpl.len() as u32 >= self.cfg.locality {
                        break;
                    }
                    tmpl.push(o == Op::Nop1);
                    p = self.wrap(p + 1);
                }
                new_ip = p;
                let tl = tmpl.len() as u32;
                let mut found: Option<u32> = None;
                let mut scanned: u32 = 0;
                if tl > 0 {
                    let forward = op == Op::Searchf;
                    for k in 0..self.cfg.locality {
                        let cand = if forward {
                            self.wrap(p + k)
                        } else {
                            self.off(ip, -(tl as i64) - k as i64)
                        };
                        scanned = k + 1;
                        let mut ok = true;
                        for (j, &bit) in tmpl.iter().enumerate() {
                            let (o, _) = decode(self.bytes[self.wrap(cand + j as u32) as usize]);
                            // complement: nop0 in template matches nop1 in target
                            let want = if bit { Op::Nop0 } else { Op::Nop1 };
                            if o != want {
                                ok = false;
                                break;
                            }
                        }
                        if ok {
                            found = Some(self.wrap(cand + tl));
                            break;
                        }
                    }
                }
                cost += self.cfg.cost_search_per16 * (scanned as i64 / 16);
                match found {
                    Some(d) => {
                        self.orgs[i].regs[3] = d;
                        self.orgs[i].regs[2] = tl;
                    }
                    None => {
                        self.orgs[i].regs[3] = 0;
                        self.orgs[i].flag = true;
                    }
                }
            }
            Op::Alloc => {
                let want = self.orgs[i].regs[r];
                // Release any earlier pending region (content stays).
                if let Some((ps, pl)) = self.orgs[i].pending.take() {
                    for k in 0..pl {
                        let a = self.wrap(ps + k) as usize;
                        self.owner[a] = FREE;
                    }
                    self.orgs[i].pending_source = None;
                    self.orgs[i].pending_errors = 0;
                    self.orgs[i].pending_slips = 0;
                }
                let me = self.orgs[i].id;
                let mut got: Option<u32> = None;
                if want > 0 && want <= self.cfg.locality {
                    'outer: for d in 0..=self.cfg.locality {
                        for s in [self.wrap(ip + d), self.off(ip, -(d as i64) - want as i64 + 1)] {
                            // every byte of [s, s+want) must be free/debris and in range
                            let mut ok = self.in_range(ip, self.wrap(s + want - 1));
                            if ok {
                                for k in 0..want {
                                    let o = self.owner[self.wrap(s + k) as usize];
                                    if o >= FIRST_ID {
                                        ok = false;
                                        break;
                                    }
                                }
                            }
                            if ok {
                                got = Some(s);
                                break 'outer;
                            }
                        }
                    }
                }
                match got {
                    Some(s) => {
                        for k in 0..want {
                            let a = self.wrap(s + k) as usize;
                            self.owner[a] = me;
                        }
                        self.orgs[i].pending = Some((s, want));
                        self.orgs[i].regs[0] = s;
                        cost += self.cfg.cost_alloc_per_byte * want as i64;
                    }
                    None => {
                        self.orgs[i].regs[0] = 0;
                        self.orgs[i].flag = true;
                    }
                }
            }
            Op::Divide => match self.orgs[i].pending.take() {
                Some((ps, pl)) => {
                    let ask = self.orgs[i].regs[r] as i64 * MILLI;
                    let give = ask.min(self.orgs[i].energy - base).max(0);
                    self.orgs[i].energy -= give;
                    let genome: Vec<u8> = (0..pl).map(|k| self.bytes[self.wrap(ps + k) as usize]).collect();
                    let parent_id = self.orgs[i].id;
                    let parent_hash = self.orgs[i].genome_hash;
                    let source = self.orgs[i].pending_source.take().unwrap_or(DEBRIS);
                    let errs = std::mem::take(&mut self.orgs[i].pending_errors);
                    let slips = std::mem::take(&mut self.orgs[i].pending_slips);
                    self.orgs[i].offspring += 1;
                    let child = self.seed(ps, &genome, give, parent_id);
                    self.events.push(Event::Birth {
                        tick: self.tick,
                        child,
                        executor: parent_id,
                        source,
                        len: pl,
                        copy_errors: errs,
                        slips,
                        genome_hash: fnv1a(&genome),
                        parent_hash,
                        endowment: give,
                    });
                }
                None => self.orgs[i].flag = true,
            },
            Op::Absorb => {
                let p = self.patch_of(ip);
                let room = (self.cfg.store_cap_per_byte * self.orgs[i].len as i64 - self.orgs[i].energy).max(0);
                let take = self.patches[p].pool.min(self.cfg.absorb_rate).min(room);
                self.patches[p].pool -= take;
                self.orgs[i].energy += take;
            }
        }

        let charge = cost.min(self.orgs[i].energy);
        self.orgs[i].energy -= charge;
        self.energy_out += charge;
        self.orgs[i].ip = new_ip;
        self.orgs[i].executed += 1;
        Some(charge)
    }

    // ---- death ----------------------------------------------------------

    fn kill(&mut self, i: usize, cause: DeathCause) {
        let o = &mut self.orgs[i];
        o.alive = false;
        let regions = [Some((o.start, o.len)), o.pending.take()];
        let id = o.id;
        let age = self.tick - o.birth_tick;
        let offspring = o.offspring;
        // Leftover energy dissipates (dead bodies carry no energy in Phase 1).
        self.energy_out += o.energy;
        o.energy = 0;
        for (s, l) in regions.into_iter().flatten() {
            for k in 0..l {
                let a = self.wrap(s + k) as usize;
                if self.owner[a] == id {
                    self.owner[a] = DEBRIS;
                }
            }
        }
        self.events.push(Event::Death { tick: self.tick, id, cause, age, offspring });
    }

    /// Single-genome harness support: remove every organism except `keep`.
    pub fn cull_all_but(&mut self, keep: usize) {
        for i in 0..self.orgs.len() {
            if i != keep && self.orgs[i].alive {
                self.kill(i, DeathCause::Harness);
            }
        }
    }

    // ---- one tick -------------------------------------------------------

    pub fn run_tick(&mut self) {
        self.tick += 1;

        // Sunlight.
        for p in self.patches.iter_mut() {
            p.pool += self.cfg.patch_income;
            self.energy_in += self.cfg.patch_income;
            if p.pool > self.cfg.patch_cap {
                self.energy_overflow += p.pool - self.cfg.patch_cap;
                p.pool = self.cfg.patch_cap;
            }
        }

        // Upkeep, then execution, in a fresh random order. Births during
        // this tick are appended to self.orgs and skipped until next tick.
        let n_before = self.orgs.len();
        let mut order: Vec<usize> = (0..n_before).filter(|&i| self.orgs[i].alive).collect();
        self.rng.shuffle(&mut order);
        for i in order {
            let o = &self.orgs[i];
            let owned = o.len + o.pending.map(|(_, l)| l).unwrap_or(0);
            let upkeep = owned as i64 * self.cfg.upkeep_per_byte;
            if o.energy < upkeep {
                self.kill(i, DeathCause::Upkeep);
                continue;
            }
            self.orgs[i].energy -= upkeep;
            self.energy_out += upkeep;

            let cap = self.cfg.cap_c0 + self.cfg.cap_c1 * self.orgs[i].len as i64;
            let mut left = cap;
            while left > 0 {
                match self.step(i, left) {
                    Some(c) => left -= c,
                    None => break,
                }
            }
        }

        // Entropy: bit rot and debris decay.
        if self.cfg.p_bit_rot > 0.0 {
            for a in 0..self.bytes.len() {
                if self.rng.chance(self.cfg.p_bit_rot) {
                    self.bytes[a] ^= 1 << self.rng.below(8);
                }
            }
        }
        if self.cfg.p_debris_decay > 0.0 {
            for a in 0..self.owner.len() {
                if self.owner[a] == DEBRIS && self.rng.chance(self.cfg.p_debris_decay) {
                    self.owner[a] = FREE;
                }
            }
        }
    }

    // ---- reporting ------------------------------------------------------

    pub fn alive_count(&self) -> usize {
        self.orgs.iter().filter(|o| o.alive).count()
    }

    /// Genome census: (hash, count, len) for living organisms, most common first.
    pub fn census(&self) -> Vec<(u64, usize, u32)> {
        let mut m: std::collections::HashMap<u64, (usize, u32)> = Default::default();
        for o in self.orgs.iter().filter(|o| o.alive) {
            let e = m.entry(o.genome_hash).or_insert((0, o.len));
            e.0 += 1;
        }
        let mut v: Vec<_> = m.into_iter().map(|(h, (c, l))| (h, c, l)).collect();
        v.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
        v
    }

    pub fn energy_in_organisms(&self) -> i64 {
        self.orgs.iter().filter(|o| o.alive).map(|o| o.energy).sum()
    }

    pub fn energy_in_patches(&self) -> i64 {
        self.patches.iter().map(|p| p.pool).sum()
    }

    pub fn genome_of(&self, id: u32) -> Option<&Org> {
        self.org_index(id).map(|i| &self.orgs[i])
    }
}

// ---- the ancestor ---------------------------------------------------------

/// PLAN.md §5.3.3 ancestor. K = absorb count, E = endowment (energy units).
pub fn ancestor(k: i8, e: i8) -> Vec<u8> {
    crate::isa::assemble(&format!(
        "self
swap B
swap C
lit D -4
lit A {k}
absorb
dec A
skipz A
jmpr D
alloc C
copy
dec C
skipz C
jmpr D
lit A {e}
divide A
self
jmpa A
"
    ))
    .unwrap()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn quiet(cfg: &mut Config) {
        cfg.p_write_flip = 0.0;
        cfg.q_slip = 0.0;
        cfg.p_debris_decay = 0.0;
        cfg.p_bit_rot = 0.0;
    }

    #[test]
    fn ancestor_is_21_bytes() {
        assert_eq!(ancestor(64, 16).len(), 21);
    }

    #[test]
    fn ancestor_replicates_exactly_without_noise() {
        let mut cfg = Config::default();
        quiet(&mut cfg);
        let mut sim = Sim::new(cfg);
        let g = ancestor(64, 16);
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
        // Child sits adjacent to the parent (nearest free run from IP).
        assert_eq!(child.start, 1000 + 21);
    }

    #[test]
    fn ancestor_pays_for_itself() {
        // Single-genome harness: parent alone, generous sunlight. Over many
        // cycles its energy must not trend down (PLAN §5.3.3 budget table).
        let mut cfg = Config::default();
        quiet(&mut cfg);
        let mut sim = Sim::new(cfg);
        let g = ancestor(64, 16);
        sim.seed(1000, &g, 100 * MILLI, 0);
        let mut min_energy = i64::MAX;
        for _ in 0..3000 {
            sim.run_tick();
            sim.cull_all_but(0);
            min_energy = min_energy.min(sim.orgs[0].energy);
        }
        let births = sim.events.iter().filter(|e| matches!(e, Event::Birth { .. })).count();
        assert!(births >= 100, "only {births} births");
        assert!(sim.orgs[0].alive, "ancestor died");
        // Store cap is 64 x 21 = 1344 energy; a self-sustaining genome rides
        // near it rather than draining toward zero.
        assert!(sim.orgs[0].energy > 500 * MILLI, "energy {} too low", sim.orgs[0].energy);
        eprintln!("harness: {births} births in 3000 ticks, min energy {min_energy}, final {}", sim.orgs[0].energy);
    }

    #[test]
    fn energy_is_conserved() {
        let mut sim = Sim::new(Config::default());
        let g = ancestor(64, 16);
        let seed_energy = 100 * MILLI;
        sim.seed(1000, &g, seed_energy, 0);
        for _ in 0..500 {
            sim.run_tick();
        }
        let initial_pools = sim.patches.len() as i64 * sim.cfg.patch_cap;
        let lhs = seed_energy + initial_pools + sim.energy_in;
        let rhs = sim.energy_in_organisms() + sim.energy_in_patches() + sim.energy_out + sim.energy_overflow;
        assert_eq!(lhs, rhs);
    }

    #[test]
    fn write_protection_blocks_foreign_store_and_sets_flag() {
        let mut cfg = Config::default();
        quiet(&mut cfg);
        let mut sim = Sim::new(cfg);
        // Victim: a body of nops at 2000.
        let victim = vec![crate::isa::encode(Op::Nop0, 0); 8];
        sim.seed(2000, &victim, 10 * MILLI, 0);
        // Attacker at 1900: A = start + 100 = 2000, then store C (0) there.
        let src = "self
lit B 100
add B
store C
self 2
";
        let att = crate::isa::assemble(src).unwrap();
        sim.seed(1900, &att, 100 * MILLI, 0);
        sim.run_tick();
        assert_eq!(sim.bytes[2000], crate::isa::encode(Op::Nop0, 0));
        // `self 2` moved the flag into A and cleared it.
        assert_eq!(sim.orgs[1].regs[0], 1);
        assert!(!sim.orgs[1].flag);
    }

    #[test]
    fn search_finds_complement_forward() {
        let mut cfg = Config::default();
        quiet(&mut cfg);
        let mut sim = Sim::new(cfg);
        // searchf 1 1 0 ; pad ; ... ; 0 0 1
        let src = "searchf\nnop1\nnop1\nnop0\npad\npad\nnop0\nnop0\nnop1\npad\n";
        let g = crate::isa::assemble(src).unwrap();
        sim.seed(100, &g, 100 * MILLI, 0);
        sim.run_tick();
        assert_eq!(sim.orgs[0].regs[2], 3);
        assert_eq!(sim.orgs[0].regs[3], 100 + 9);
    }

    #[test]
    fn loafer_dies_of_upkeep() {
        let mut cfg = Config::default();
        quiet(&mut cfg);
        cfg.patch_income = 0;
        let mut sim = Sim::new(cfg);
        let g = crate::isa::assemble("pad\n").unwrap();
        sim.seed(100, &g, 1 * MILLI, 0);
        for _ in 0..100 {
            sim.run_tick();
        }
        assert!(!sim.orgs[0].alive);
        assert_eq!(sim.owner[100], DEBRIS);
    }
}
