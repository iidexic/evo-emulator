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

impl DeathCause {
    pub fn name(self) -> &'static str {
        match self {
            DeathCause::Upkeep => "upkeep",
            DeathCause::Harness => "harness",
        }
    }
}

/// Per-organism counters, cumulative over its life (docs/instrumentation.md).
/// The simulation writes them; nothing in the physics reads them.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct OrgStats {
    /// Energy at birth: seed energy or the parent's endowment.
    pub born_with_m: i64,
    pub executed: u64,
    pub absorbs: u64,
    pub absorb_gain_m: i64,
    /// Absorbs that got less than a full ration because the pool was short.
    pub absorb_short: u64,
    /// Absorbs that got less than a full ration because the store was near cap.
    pub absorb_capped: u64,
    pub copies: u64,
    /// `load`/`copy` reads of a byte owned by another organism.
    pub reads_foreign: u64,
    /// Instructions executed at an address owned by another organism.
    pub exec_foreign: u64,
    /// Instructions executed at a free or debris address.
    pub exec_unowned: u64,
    pub writes_blocked: u64,
    /// Reads or writes outside locality.
    pub range_faults: u64,
    pub allocs_ok: u64,
    pub allocs_fail: u64,
    pub divides_ok: u64,
    /// `divide` with no pending region.
    pub divides_fail: u64,
    pub endowed_m: i64,
    pub spent_m: i64,
    pub upkeep_m: i64,
    /// Ticks in which it paid upkeep but could not afford one instruction.
    pub starved_ticks: u64,
    /// Tick of the last successful `divide`, -1 if none.
    pub last_divide_tick: i64,
    pub max_energy_m: i64,
}

impl OrgStats {
    pub fn new(born_with_m: i64) -> OrgStats {
        OrgStats {
            born_with_m,
            executed: 0,
            absorbs: 0,
            absorb_gain_m: 0,
            absorb_short: 0,
            absorb_capped: 0,
            copies: 0,
            reads_foreign: 0,
            exec_foreign: 0,
            exec_unowned: 0,
            writes_blocked: 0,
            range_faults: 0,
            allocs_ok: 0,
            allocs_fail: 0,
            divides_ok: 0,
            divides_fail: 0,
            endowed_m: 0,
            spent_m: 0,
            upkeep_m: 0,
            starved_ticks: 0,
            last_divide_tick: -1,
            max_energy_m: born_with_m,
        }
    }

    /// CSV column names, in the order `csv_row` writes them.
    pub const CSV_HEADER: &'static str = "born_with_m,executed,absorbs,absorb_gain_m,absorb_short,absorb_capped,copies,reads_foreign,exec_foreign,exec_unowned,writes_blocked,range_faults,allocs_ok,allocs_fail,divides_ok,divides_fail,endowed_m,spent_m,upkeep_m,starved_ticks,last_divide_tick,max_energy_m";

    pub fn csv_row(&self) -> String {
        format!(
            "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}",
            self.born_with_m, self.executed, self.absorbs, self.absorb_gain_m,
            self.absorb_short, self.absorb_capped, self.copies, self.reads_foreign,
            self.exec_foreign, self.exec_unowned, self.writes_blocked, self.range_faults,
            self.allocs_ok, self.allocs_fail, self.divides_ok, self.divides_fail,
            self.endowed_m, self.spent_m, self.upkeep_m, self.starved_ticks,
            self.last_divide_tick, self.max_energy_m,
        )
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Event {
    Birth {
        tick: u64,
        child: u32,
        executor: u32,
        /// Owner id of the first byte copied into the child's region, or
        /// DEBRIS/FREE if the child was scavenged without copying.
        source: u32,
        start: u32,
        len: u32,
        /// Bit flips that landed in the child's region while it was pending.
        copy_errors: u32,
        /// Slips that landed in the child's region while it was pending.
        slips: u32,
        genome_hash: u64,
        /// Executor's genome hash at its birth.
        parent_hash: u64,
        /// Hash of the executor's body bytes at the moment of `divide`. Differs
        /// from `parent_hash` when the executor's body changed since birth.
        parent_now_hash: u64,
        /// Birth genome hash of the copy source organism, 0 if `source` is
        /// free space or debris.
        source_hash: u64,
        endowment: i64,
    },
    Death {
        tick: u64,
        id: u32,
        cause: DeathCause,
        age: u64,
        offspring: u32,
        start: u32,
        len: u32,
        /// Length of a half-built child region at death, 0 if none.
        pending_len: u32,
        /// IP minus body start, wrapped around the ring.
        ip_off: u32,
        op_at_ip: Op,
        /// Energy just before the failed upkeep charge (or the harness cull).
        energy: i64,
        /// Pool of the patch holding the body start.
        pool: i64,
        birth_hash: u64,
        /// Hash of the body bytes at death.
        now_hash: u64,
        stats: OrgStats,
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
    pub stats: OrgStats,
}

#[derive(Clone, Debug)]
pub struct Patch {
    pub pool: i64,
    /// Cumulative energy taken from this pool by `absorb`.
    pub absorbed: i64,
    /// Cumulative income lost to the pool cap.
    pub overflow: i64,
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
            patches: (0..np)
                .map(|_| Patch {
                    pool: if cfg.pools_start_full { cfg.patch_cap } else { 0 },
                    absorbed: 0,
                    overflow: 0,
                })
                .collect(),
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

    pub fn patch_of(&self, addr: u32) -> usize {
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
            stats: OrgStats::new(energy),
        });
        id
    }

    /// Current bytes of a region (an organism's body as it is now, which can
    /// differ from `Org.genome` after bit rot or foreign writes).
    pub fn region(&self, start: u32, len: u32) -> Vec<u8> {
        (0..len).map(|k| self.bytes[self.wrap(start + k) as usize]).collect()
    }

    /// IP minus body start, wrapped around the ring.
    pub fn ip_off(&self, o: &Org) -> u32 {
        self.off(o.ip, -(o.start as i64))
    }

    // ---- memory access with physics ------------------------------------

    /// Attempt a write by organism `i` at `addr`. Applies locality, write
    /// protection, and write noise. Returns whether the write landed.
    fn write(&mut self, i: usize, addr: u32, val: u8) -> bool {
        let addr = self.wrap(addr);
        let ip = self.orgs[i].ip;
        if !self.in_range(ip, addr) {
            self.orgs[i].flag = true;
            self.orgs[i].stats.range_faults += 1;
            return false;
        }
        let own = self.owner[addr as usize];
        let me = self.orgs[i].id;
        if self.cfg.write_protection && own >= FIRST_ID && own != me {
            self.orgs[i].flag = true;
            self.orgs[i].stats.writes_blocked += 1;
            return false;
        }
        let mut v = val;
        if self.rng.chance(self.cfg.p_write_flip) {
            v ^= 1 << self.rng.below(8);
            if let Some((ps, pl)) = self.orgs[i].pending {
                if self.off(addr, -(ps as i64)) < pl {
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
            self.orgs[i].stats.range_faults += 1;
            return 0;
        }
        let own = self.owner[addr as usize];
        if own >= FIRST_ID && own != self.orgs[i].id {
            self.orgs[i].stats.reads_foreign += 1;
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
        let own = self.owner[ip as usize];
        if own >= FIRST_ID {
            if own != self.orgs[i].id {
                self.orgs[i].stats.exec_foreign += 1;
            }
        } else {
            self.orgs[i].stats.exec_unowned += 1;
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
                self.orgs[i].stats.copies += 1;
                let v = self.read(i, b);
                // Record the copy source for lineage: owner of the first byte
                // copied into the pending region.
                if self.orgs[i].pending_source.is_none() {
                    if let Some((ps, pl)) = self.orgs[i].pending {
                        if self.off(a, -(ps as i64)) < pl {
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
                        if self.off(a, -(ps as i64)) < pl {
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
                    let loc = self.cfg.locality;
                    'outer: for step in 0..=loc {
                        // Nearest-first by default; alloc_far scans from the
                        // locality edge inward (E002 dispersal arm).
                        let d = if self.cfg.alloc_far { loc - step } else { step };
                        for s in [self.wrap(ip + d), self.off(ip, -(d as i64) - want as i64 + 1)] {
                            // every byte of [s, s+want) must be free/debris and in range;
                            // both ends in range means the whole run is (want <= locality)
                            let mut ok = self.in_range(ip, s) && self.in_range(ip, self.wrap(s + want - 1));
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
                        self.orgs[i].stats.allocs_ok += 1;
                        cost += self.cfg.cost_alloc_per_byte * want as i64;
                    }
                    None => {
                        self.orgs[i].regs[0] = 0;
                        self.orgs[i].flag = true;
                        self.orgs[i].stats.allocs_fail += 1;
                    }
                }
            }
            Op::Divide => match self.orgs[i].pending.take() {
                Some((ps, pl)) => {
                    let ask = self.orgs[i].regs[r] as i64 * MILLI;
                    let give = ask.min(self.orgs[i].energy - base).max(0);
                    self.orgs[i].energy -= give;
                    let genome = self.region(ps, pl);
                    let parent_id = self.orgs[i].id;
                    let parent_hash = self.orgs[i].genome_hash;
                    let parent_now_hash = fnv1a(&self.region(self.orgs[i].start, self.orgs[i].len));
                    let source = self.orgs[i].pending_source.take().unwrap_or(DEBRIS);
                    let source_hash = if source >= FIRST_ID {
                        self.org_index(source).map_or(0, |j| self.orgs[j].genome_hash)
                    } else {
                        0
                    };
                    let errs = std::mem::take(&mut self.orgs[i].pending_errors);
                    let slips = std::mem::take(&mut self.orgs[i].pending_slips);
                    self.orgs[i].offspring += 1;
                    let st = &mut self.orgs[i].stats;
                    st.divides_ok += 1;
                    st.endowed_m += give;
                    st.last_divide_tick = self.tick as i64;
                    let child = self.seed(ps, &genome, give, parent_id);
                    self.events.push(Event::Birth {
                        tick: self.tick,
                        child,
                        executor: parent_id,
                        source,
                        start: ps,
                        len: pl,
                        copy_errors: errs,
                        slips,
                        genome_hash: fnv1a(&genome),
                        parent_hash,
                        parent_now_hash,
                        source_hash,
                        endowment: give,
                    });
                }
                None => {
                    self.orgs[i].flag = true;
                    self.orgs[i].stats.divides_fail += 1;
                }
            },
            Op::Absorb => {
                let p = self.patch_of(ip);
                let room = (self.cfg.store_cap_per_byte * self.orgs[i].len as i64 - self.orgs[i].energy).max(0);
                let pool = self.patches[p].pool;
                let ration = if self.cfg.absorb_proportional {
                    self.cfg.absorb_rate * pool / self.cfg.patch_cap
                } else {
                    self.cfg.absorb_rate
                };
                let avail = pool.min(ration);
                let take = avail.min(room);
                self.patches[p].pool -= take;
                self.patches[p].absorbed += take;
                let o = &mut self.orgs[i];
                o.energy += take;
                o.stats.absorbs += 1;
                o.stats.absorb_gain_m += take;
                o.stats.max_energy_m = o.stats.max_energy_m.max(o.energy);
                // Short: the pool gave less than a full ration (under the
                // proportional rule, any pool below the cap). Capped: the
                // store was too full to take what the pool offered.
                if take < self.cfg.absorb_rate {
                    if room < avail {
                        o.stats.absorb_capped += 1;
                    } else {
                        o.stats.absorb_short += 1;
                    }
                }
            }
        }

        let charge = cost.min(self.orgs[i].energy);
        let o = &mut self.orgs[i];
        o.energy -= charge;
        o.ip = new_ip;
        o.stats.executed += 1;
        o.stats.spent_m += charge;
        self.energy_out += charge;
        Some(charge)
    }

    // ---- death ----------------------------------------------------------

    fn kill(&mut self, i: usize, cause: DeathCause) {
        // Snapshot for the death record before anything changes.
        let o = &self.orgs[i];
        let death = Event::Death {
            tick: self.tick,
            id: o.id,
            cause,
            age: self.tick - o.birth_tick,
            offspring: o.offspring,
            start: o.start,
            len: o.len,
            pending_len: o.pending.map_or(0, |(_, l)| l),
            ip_off: self.ip_off(o),
            op_at_ip: decode(self.bytes[o.ip as usize]).0,
            energy: o.energy,
            pool: self.patches[self.patch_of(o.start)].pool,
            birth_hash: o.genome_hash,
            now_hash: fnv1a(&self.region(o.start, o.len)),
            stats: o.stats,
        };
        let o = &mut self.orgs[i];
        o.alive = false;
        let regions = [Some((o.start, o.len)), o.pending.take()];
        let id = o.id;
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
        self.events.push(death);
    }

    /// Single-genome harness support: remove every organism except `keep`.
    pub fn cull_all_but(&mut self, keep: usize) {
        self.cull_except(&[keep]);
    }

    /// Remove every living organism whose index is not in `keep`.
    pub fn cull_except(&mut self, keep: &[usize]) {
        for i in 0..self.orgs.len() {
            if !keep.contains(&i) && self.orgs[i].alive {
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
                let over = p.pool - self.cfg.patch_cap;
                self.energy_overflow += over;
                p.overflow += over;
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
            self.orgs[i].stats.upkeep_m += upkeep;
            self.energy_out += upkeep;

            let cap = self.cfg.cap_c0 + self.cfg.cap_c1 * self.orgs[i].len as i64;
            let mut left = cap;
            let mut ran = false;
            while left > 0 {
                match self.step(i, left) {
                    Some(c) => {
                        left -= c;
                        ran = true;
                    }
                    None => break,
                }
            }
            if !ran {
                self.orgs[i].stats.starved_ticks += 1;
            }
        }

        // Entropy: bit rot and debris decay. Each is a per-byte Bernoulli
        // trial; sampling the gap to the next hit gives the same event
        // distribution without one RNG call per byte. Debris decay trials
        // that land on non-debris bytes do nothing, as in a per-byte loop.
        let n = self.bytes.len() as u64;
        let p = self.cfg.p_bit_rot;
        if p > 0.0 {
            let mut a = self.rng.geometric(p);
            while a < n {
                self.bytes[a as usize] ^= 1 << self.rng.below(8);
                a = a.saturating_add(self.rng.geometric(p)).saturating_add(1);
            }
        }
        let p = self.cfg.p_debris_decay;
        if p > 0.0 {
            let mut a = self.rng.geometric(p);
            while a < n {
                if self.owner[a as usize] == DEBRIS {
                    self.owner[a as usize] = FREE;
                }
                a = a.saturating_add(self.rng.geometric(p)).saturating_add(1);
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

    /// Hash of everything that can influence the future of the run: tick,
    /// PRNG state, world bytes and owners, pools, and each organism's VM and
    /// energy state. Two runs that agree on this agree on every later tick.
    /// Counters (`OrgStats`, patch totals) are left out: they never feed back.
    pub fn state_hash(&self) -> u64 {
        let mut h = Fnv::new();
        h.u64(self.tick);
        for w in self.rng.state() {
            h.u64(w);
        }
        h.bytes(&self.bytes);
        for &o in &self.owner {
            h.u64(o as u64);
        }
        for p in &self.patches {
            h.u64(p.pool as u64);
        }
        h.u64(self.next_id as u64);
        for o in &self.orgs {
            h.u64(o.id as u64);
            for r in o.regs {
                h.u64(r as u64);
            }
            h.u64(o.ip as u64);
            h.u64(o.flag as u64);
            h.u64(o.energy as u64);
            h.u64(o.start as u64);
            h.u64(o.len as u64);
            let (ps, pl) = o.pending.unwrap_or((u32::MAX, 0));
            h.u64(ps as u64);
            h.u64(pl as u64);
            h.u64(o.pending_source.map_or(u64::MAX, |s| s as u64));
            h.u64(o.alive as u64);
        }
        h.0
    }
}

/// Incremental FNV-1a, same constants as `fnv1a`.
struct Fnv(u64);

impl Fnv {
    fn new() -> Fnv {
        Fnv(0xcbf29ce484222325)
    }
    fn bytes(&mut self, b: &[u8]) {
        for &x in b {
            self.0 ^= x as u64;
            self.0 = self.0.wrapping_mul(0x100000001b3);
        }
    }
    fn u64(&mut self, v: u64) {
        self.bytes(&v.to_le_bytes());
    }
}

/// Hash of the canonical form (docs/instrumentation.md): equal for genomes
/// that differ only in bits the decoder ignores.
pub fn func_hash(bytes: &[u8]) -> u64 {
    fnv1a(&crate::isa::canonical(bytes))
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
    fn absorb_proportional_scales_with_pool() {
        // One `absorb` from a half-full pool: the fixed rule gives a full
        // ration, the proportional rule half of one.
        for (prop, gain) in [(false, 8 * MILLI), (true, 4 * MILLI)] {
            let mut cfg = Config::default();
            quiet(&mut cfg);
            cfg.absorb_proportional = prop;
            let mut sim = Sim::new(cfg.clone());
            let g = crate::isa::assemble("absorb
").unwrap();
            sim.seed(1000, &g, 10 * MILLI, 0);
            let p = sim.patch_of(1000);
            sim.patches[p].pool = cfg.patch_cap / 2;
            assert!(sim.step(0, cfg.cap_c0).is_some());
            assert_eq!(sim.orgs[0].energy, 10 * MILLI + gain - cfg.cost_absorb);
            assert_eq!(sim.patches[p].pool, cfg.patch_cap / 2 - gain);
            assert_eq!(sim.orgs[0].stats.absorb_short, prop as u64);
        }
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
    fn alloc_far_places_child_at_locality_edge() {
        let mut cfg = Config::default();
        quiet(&mut cfg);
        cfg.alloc_far = true;
        let mut sim = Sim::new(cfg);
        let g = ancestor(64, 16);
        sim.seed(1000, &g, 100 * MILLI, 0);
        for _ in 0..200 {
            sim.run_tick();
            if sim.orgs.len() > 1 {
                break;
            }
        }
        let child = &sim.orgs[1];
        assert_eq!(child.genome, g);
        // `alloc` is at offset 11; the farthest 21-byte run whose end is
        // within 512 of IP starts 512 - 20 bytes ahead.
        assert_eq!(child.start, 1011 + 492);
    }

    #[test]
    fn alloc_region_lies_within_locality() {
        // Block forward space and the near backward space so the nearest
        // backward run that fits extends past the locality radius.
        let mut cfg = Config::default();
        quiet(&mut cfg);
        cfg.locality = 64;
        let mut sim = Sim::new(cfg);
        let g = crate::isa::assemble("lit C 40
alloc C
").unwrap();
        sim.seed(1000, &g, 100 * MILLI, 0);
        sim.seed(1003, &vec![0u8; 100], 100 * MILLI, 0);
        sim.seed(1000 - 40, &vec![0u8; 40], 100 * MILLI, 0);
        // The only free 40-byte run ending within reach is [920, 960), whose
        // start is 80 bytes from IP. It must be refused, not half-claimed.
        sim.run_tick();
        assert_eq!(sim.orgs[0].pending, None);
        assert!(sim.orgs[0].flag);
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
