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
    /// Energy charged to this organism for instructions other organisms
    /// executed in its body (`charge_owner`, E008; the owner's share under
    /// `charge_owner_pct`, E009). Included in `spent_m`.
    pub paid_for_others_m: i64,
    /// Energy other organisms paid for this organism's instructions (the
    /// owners of the bytes it ran: the whole charge under `charge_owner`,
    /// the owner's share under `charge_owner_pct`). Not in `spent_m`.
    pub paid_by_others_m: i64,
    /// Energy received from the owners of the bytes this organism ran,
    /// under `transfer_pct` (E010): what the owner lost, capped by this
    /// organism's room below its store cap. The owner's loss is in its
    /// `spent_m` and `paid_for_others_m`. 0 without the flag.
    pub gained_from_others_m: i64,
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
            paid_for_others_m: 0,
            paid_by_others_m: 0,
            gained_from_others_m: 0,
        }
    }

    /// CSV column names, in the order `csv_row` writes them.
    pub const CSV_HEADER: &'static str = "born_with_m,executed,absorbs,absorb_gain_m,absorb_short,absorb_capped,copies,reads_foreign,exec_foreign,exec_unowned,writes_blocked,range_faults,allocs_ok,allocs_fail,divides_ok,divides_fail,endowed_m,spent_m,upkeep_m,starved_ticks,last_divide_tick,max_energy_m,paid_for_others_m,paid_by_others_m,gained_from_others_m";

    pub fn csv_row(&self) -> String {
        format!(
            "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}",
            self.born_with_m, self.executed, self.absorbs, self.absorb_gain_m,
            self.absorb_short, self.absorb_capped, self.copies, self.reads_foreign,
            self.exec_foreign, self.exec_unowned, self.writes_blocked, self.range_faults,
            self.allocs_ok, self.allocs_fail, self.divides_ok, self.divides_fail,
            self.endowed_m, self.spent_m, self.upkeep_m, self.starved_ticks,
            self.last_divide_tick, self.max_energy_m, self.paid_for_others_m,
            self.paid_by_others_m, self.gained_from_others_m,
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
    /// Owner of the first byte copied into the pending region, with that
    /// owner's birth genome hash (0 for free or debris bytes). The hash is
    /// taken at copy time because the owner may be dead and retired by
    /// `divide`.
    pub pending_source: Option<(u32, u64)>,
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
    /// Living organisms in birth order, plus those that died since the
    /// last `retire` (the start of the next tick). Dead organisms are
    /// dropped then, so the per-tick scans stay proportional to the
    /// population rather than to every birth so far (E007 found a 250,000
    /// tick run slowing to a fifth of its starting speed before this).
    pub orgs: Vec<Org>,
    /// Position in `orgs` of each id ever issued (id - FIRST_ID), or
    /// `u32::MAX` once retired.
    index: Vec<u32>,
    /// Instructions executed and energy absorbed by organisms already
    /// retired (`executed_total`, `absorb_gain_total`).
    retired_executed: u64,
    retired_absorb_gain_m: i64,
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
        // E010's transfer and the owner-pays rules (E008, E009) each decide
        // who pays for foreign execution; `step` assumes at most one is on.
        assert!(
            cfg.transfer_pct >= 0 && !(cfg.transfer_pct > 0 && (cfg.charge_owner || cfg.charge_owner_pct > 0)),
            "transfer_pct cannot be combined with charge_owner or charge_owner_pct"
        );
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
            index: Vec::new(),
            retired_executed: 0,
            retired_absorb_gain_m: 0,
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
        // ids are allocated sequentially from FIRST_ID, so `index` is
        // addressed by id - FIRST_ID; retired organisms are not found.
        let i = *self.index.get(id.checked_sub(FIRST_ID)? as usize)?;
        if i == u32::MAX { None } else { Some(i as usize) }
    }

    /// Drop the organisms that have died, keeping the living in birth
    /// order. Called at the start of every tick, so a death is visible
    /// (with its final state) until the next `run_tick`.
    fn retire(&mut self) {
        if self.orgs.iter().all(|o| o.alive) {
            return;
        }
        let mut kept = 0usize;
        for i in 0..self.orgs.len() {
            let o = &self.orgs[i];
            let slot = (o.id - FIRST_ID) as usize;
            if o.alive {
                self.index[slot] = kept as u32;
                self.orgs.swap(kept, i);
                kept += 1;
            } else {
                self.index[slot] = u32::MAX;
                self.retired_executed += o.stats.executed;
                self.retired_absorb_gain_m += o.stats.absorb_gain_m;
            }
        }
        self.orgs.truncate(kept);
    }

    /// Instructions executed by every organism so far, retired ones included.
    pub fn executed_total(&self) -> u64 {
        self.retired_executed + self.orgs.iter().map(|o| o.stats.executed).sum::<u64>()
    }

    /// Energy every organism so far gained by `absorb`, retired ones included.
    pub fn absorb_gain_total(&self) -> i64 {
        self.retired_absorb_gain_m + self.orgs.iter().map(|o| o.stats.absorb_gain_m).sum::<i64>()
    }

    // ---- seeding --------------------------------------------------------

    /// Place a genome at `start` as a living organism with `energy` milli-units.
    pub fn seed(&mut self, start: u32, genome: &[u8], energy: i64, parent: u32) -> u32 {
        let id = self.next_id;
        self.next_id += 1;
        self.index.push(self.orgs.len() as u32);
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

    /// Seed several founders (`--founder`, E009a): `founders` is a list of
    /// (genome, copies); every copy gets `energy` and they are placed at
    /// `founder_starts` in list order (the first entry's copies first).
    /// Returns the start addresses. One entry with one copy is exactly the
    /// single-founder seeding at `world_size / 2`.
    ///
    /// Rust note: `&[(Vec<u8>, u32)]` is a borrowed slice of tuples, like a
    /// Go `[]struct{...}` passed by reference; the function cannot keep it.
    pub fn seed_founders(&mut self, founders: &[(Vec<u8>, u32)], energy: i64) -> Vec<u32> {
        let total: u32 = founders.iter().map(|(_, n)| *n).sum();
        let starts = founder_starts(self.cfg.world_size, total);
        // Bodies must not overlap: each must fit before the next start.
        let gap = if total > 1 { self.cfg.world_size / total } else { self.cfg.world_size };
        let mut j = 0;
        for (g, n) in founders {
            assert!(g.len() as u32 <= gap, "founder of {} bytes does not fit in a spacing of {gap}", g.len());
            for _ in 0..*n {
                self.seed(starts[j], g, energy, 0);
                j += 1;
            }
        }
        starts
    }

    /// Place `count` copies of `genome` into memory not owned by a living
    /// organism (`--inject`, E009b), each with `energy` and birth tick
    /// `birth_tick`, `parent` 0. Copy j targets `founder_starts(world_size,
    /// count)[j]` and takes the first run of `genome.len()` bytes, scanning
    /// forward from the target, in which no byte is owned by a living
    /// organism (free and debris bytes both qualify and are overwritten, as
    /// `alloc` plus `copy` would). The run must begin before the next copy's
    /// target (for the last copy, before the first copy's target plus the
    /// world size); if none does, the copy is skipped. Copies are placed in
    /// order, so a later copy sees the earlier ones as living. No PRNG draw.
    /// Returns, per copy, its start address or -1 if skipped, and the ids
    /// of the copies placed.
    pub fn inject(&mut self, genome: &[u8], count: u32, energy: i64, birth_tick: u64) -> (Vec<i64>, Vec<u32>) {
        let n = self.cfg.world_size;
        let len = genome.len() as u32;
        assert!(len > 0 && len <= n, "injected genome must be 1..world_size bytes");
        let targets = founder_starts(n, count);
        let mut starts = Vec::with_capacity(count as usize);
        let mut ids = Vec::new();
        for j in 0..count as usize {
            // Distance to the next copy's target along the ring; the last
            // copy wraps to the first. One copy may scan the whole ring.
            let gap = if count == 1 {
                n
            } else {
                let next = targets[(j + 1) % count as usize];
                (next + n - targets[j]) % n
            };
            // `(0..gap).find(...)` returns the first offset whose run is
            // clear, or None: an Option, Rust's typed "maybe".
            let found = (0..gap).find(|&d| {
                let s = targets[j] + d;
                (0..len).all(|k| self.owner[self.wrap(s + k) as usize] < FIRST_ID)
            });
            match found {
                Some(d) => {
                    let s = self.wrap(targets[j] + d);
                    let id = self.seed(s, genome, energy, 0);
                    let at = self.org_index(id).expect("just seeded");
                    self.orgs[at].birth_tick = birth_tick;
                    starts.push(s as i64);
                    ids.push(id);
                }
                None => starts.push(-1),
            }
        }
        (starts, ids)
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

    /// Execute one instruction for organism `i`. Returns the energy charged
    /// (to whoever paid it, all parts together), or None if the payer (the
    /// organism, or under `charge_owner` the owner of the byte at IP) could
    /// not afford the base cost, or under `charge_owner_pct` the executor
    /// could not afford its part of it (nothing runs).
    /// `cap_left` is the per-tick budget still available.
    /// Under `transfer_pct` (E010) the executor pays as with no flag, then
    /// the owner of the byte at IP passes energy to it (see the end of the
    /// function); the returned charge, and so the tick budget, does not
    /// include that transfer.
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
        let own = self.owner[ip as usize];
        // Who pays: the executor, or with `charge_owner` (E008) the living
        // owner of the byte at IP when that is another organism. The
        // executor's own body and pending region count as its own. Killing
        // an organism turns its bytes to debris, so a dead owner should not
        // appear here; if one did, the executor would pay.
        //
        // Or, with `charge_owner_pct` (E009) and `charge_owner` off, the
        // cost is split: that owner (the `sharer`) pays `floor(cost * pct /
        // 100)` or its whole store if less, the executor the rest. When both
        // flags are set `charge_owner` wins.
        let mut payer = i;
        // `Option<usize>` is Rust's "maybe an index": `None` here means no
        // split. It is Zig's `?usize`; Go would use a pointer or a -1
        // sentinel, which the compiler would not make every use check.
        let mut sharer: Option<usize> = None;
        let pct = self.cfg.charge_owner_pct;
        if (self.cfg.charge_owner || pct > 0) && own >= FIRST_ID && own != self.orgs[i].id {
            if let Some(j) = self.org_index(own) {
                if self.orgs[j].alive {
                    if self.cfg.charge_owner {
                        payer = j;
                    } else {
                        sharer = Some(j);
                    }
                }
            }
        }
        // The payer must afford its part of the base cost (all of it, unless
        // the cost is split) and the executor's per-tick budget must cover
        // the whole base cost; otherwise nothing runs and the executor's
        // tick ends. Under the split an owner at zero pays nothing and the
        // executor needs the full base cost, as on debris.
        let need = match sharer {
            Some(j) => base - (base * pct / 100).min(self.orgs[j].energy),
            None => base,
        };
        if self.orgs[payer].energy < need || cap_left < base {
            return None;
        }
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
                    // Phase 1: the executing organism. With `self_owner`
                    // (E006, H8): the living owner of the byte at IP, so a
                    // host's copy loop run by an intruder copies the host.
                    let mut who = i;
                    if self.cfg.self_owner && own >= FIRST_ID && own != self.orgs[i].id {
                        if let Some(j) = self.org_index(own) {
                            who = j;
                        }
                    }
                    self.orgs[i].regs[0] = self.orgs[who].start;
                    self.orgs[i].regs[1] = self.orgs[who].len;
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
                            let s = self.owner[self.wrap(b) as usize];
                            let sh = if s >= FIRST_ID {
                                self.org_index(s).map_or(0, |j| self.orgs[j].genome_hash)
                            } else {
                                0
                            };
                            self.orgs[i].pending_source = Some((s, sh));
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
                    let (source, source_hash) = self.orgs[i].pending_source.take().unwrap_or((DEBRIS, 0));
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

        // Split charge (E009): the sharer pays its share of the actual cost
        // first (the op itself never changes the sharer's store, so the
        // share is at least what the check above assumed), then the payer
        // (here the executor) pays the rest, capped at its store as before.
        let mut shared = 0;
        if let Some(j) = sharer {
            shared = (cost * pct / 100).min(self.orgs[j].energy);
            let q = &mut self.orgs[j];
            q.energy -= shared;
            q.stats.spent_m += shared;
            q.stats.paid_for_others_m += shared;
        }
        let charge = (cost - shared).min(self.orgs[payer].energy);
        let p = &mut self.orgs[payer];
        p.energy -= charge;
        p.stats.spent_m += charge;
        if payer != i {
            p.stats.paid_for_others_m += charge;
        }
        let o = &mut self.orgs[i];
        o.ip = new_ip;
        o.stats.executed += 1;
        if payer != i {
            o.stats.paid_by_others_m += charge;
        }
        o.stats.paid_by_others_m += shared;
        // Each unit left exactly one store: `shared` the owner's, `charge`
        // the payer's. The executor's per-tick budget is debited by both.
        let total = shared + charge;
        self.energy_out += total;

        // Transfer (E010): the executor has paid its own full cost above
        // (with `transfer_pct` on, the other two flags are off, so `payer`
        // is `i` and there is no `sharer`). Now, if the byte at IP belongs
        // to another living organism j, j loses `take` and the executor
        // gains as much of it as fits under its store cap, measured after
        // it paid; the rest is dissipated. Debris, free bytes and a dead
        // owner give nothing. `own` was read before the op ran; no op can
        // change the owner of a byte a living organism holds.
        let tpct = self.cfg.transfer_pct;
        if tpct > 0 && own >= FIRST_ID && own != self.orgs[i].id {
            // `if let Some(j) = ...` runs the block only when the lookup
            // found an index; a retired owner gives `None` and is skipped.
            if let Some(j) = self.org_index(own) {
                if self.orgs[j].alive {
                    let take = (cost * tpct / 100).min(self.orgs[j].energy);
                    // `q` is a checked pointer into the list, valid until
                    // its last use three lines down; only then may the code
                    // touch `self.orgs[i]` (one `&mut` at a time).
                    let q = &mut self.orgs[j];
                    q.energy -= take;
                    q.stats.spent_m += take;
                    q.stats.paid_for_others_m += take;
                    let cap = self.cfg.store_cap_per_byte * self.orgs[i].len as i64;
                    let room = (cap - self.orgs[i].energy).max(0);
                    let gain = take.min(room);
                    let o = &mut self.orgs[i];
                    o.energy += gain;
                    o.stats.gained_from_others_m += gain;
                    o.stats.max_energy_m = o.stats.max_energy_m.max(o.energy);
                    self.energy_out += take - gain;
                }
            }
        }
        // The tick budget is debited by the executor's own charge only;
        // the transfer is not work.
        Some(total)
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

    /// Single-genome harness support: remove every organism except id `keep`.
    pub fn cull_all_but(&mut self, keep: u32) {
        self.cull_except(&[keep]);
    }

    /// Remove every living organism whose id is not in `keep`.
    pub fn cull_except(&mut self, keep: &[u32]) {
        for i in 0..self.orgs.len() {
            if !keep.contains(&self.orgs[i].id) && self.orgs[i].alive {
                self.kill(i, DeathCause::Harness);
            }
        }
    }

    // ---- one tick -------------------------------------------------------

    pub fn run_tick(&mut self) {
        self.retire();
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
            h.u64(o.pending_source.map_or(u64::MAX, |(s, _)| s as u64));
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

// ---- founders ---------------------------------------------------------------

/// Start addresses of `total` founders (`--founder`, E009a): founder j sits
/// at `world_size / 2 + world_size * j / total` (integer division), modulo
/// the world size. The offset `world_size / 2` is where the single founder
/// has always been seeded, so one founder lands exactly there. Starts are
/// at least `floor(world_size / total)` apart (also across the wrap), so
/// when `total` is at most the number of patches no two share a patch
/// (the default world has 128 patches of 512 bytes).
pub fn founder_starts(world_size: u32, total: u32) -> Vec<u32> {
    // u64 so `world_size * j` cannot overflow a u32.
    let (n, t) = (world_size as u64, total as u64);
    (0..t).map(|j| ((n / 2 + n * j / t) % n) as u32).collect()
}

// ---- injections -------------------------------------------------------------

/// One `--inject TICK:HEX:COUNT` (E009b): `count` copies of `genome` placed
/// at the start of tick `tick`, before any organism steps.
#[derive(Clone, Debug)]
pub struct Injection {
    pub tick: u64,
    pub genome: Vec<u8>,
    pub count: u32,
}

/// Result of one injection: its index in the list given to `inject_due`,
/// the start of every copy (-1 if skipped) and the ids of those placed.
pub struct Injected {
    pub index: usize,
    pub starts: Vec<i64>,
    pub ids: Vec<u32>,
}

// A second `impl` block for the same type is allowed in Rust; it keeps the
// injection code next to its types.
impl Sim {
    /// Call just before `run_tick`: performs every injection whose tick is
    /// the one about to run (`self.tick + 1`), in list order, each copy
    /// with `energy` (100 units from the CLI) and that tick as its birth
    /// tick. Between ticks is the start of the next one: `run_tick` only
    /// retires the dead and adds sunlight before organisms step, and
    /// neither depends on the new bodies. With an empty list this does
    /// nothing, so a run without `--inject` is unchanged.
    pub fn inject_due(&mut self, injections: &[Injection], energy: i64) -> Vec<Injected> {
        let next = self.tick + 1;
        let mut done = Vec::new();
        for (index, inj) in injections.iter().enumerate() {
            if inj.tick == next {
                let (starts, ids) = self.inject(&inj.genome, inj.count, energy, next);
                done.push(Injected { index, starts, ids });
            }
        }
        done
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
        // Phase 1 world: nearest-free `alloc`, so the child sits adjacent.
        // The default (E004) world is covered by alloc_far_places_child_at_locality_edge.
        let mut cfg = Config::e001();
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
            sim.cull_all_but(FIRST_ID);
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
    fn charge_owner_conserves_energy_and_balances_ledgers() {
        // E008: a `pad` in front of the ancestor, noise on. The owner pays
        // for foreign execution; world totals and every ledger still balance
        // because `spent_m` includes what an organism paid for others.
        let mut cfg = Config::default();
        cfg.charge_owner = true;
        let mut sim = Sim::new(cfg);
        let seed_energy = 100 * MILLI;
        let host = sim.seed(1000, &ancestor(64, 16), seed_energy, 0);
        sim.seed(999, &[0x00], seed_energy, 0);
        let mut host_paid = 0;
        for _ in 0..2000 {
            sim.run_tick();
            for ev in sim.events.drain(..) {
                if let Event::Death { id, stats, .. } = ev {
                    if id == host {
                        host_paid = stats.paid_for_others_m;
                    }
                }
            }
            for o in sim.orgs.iter().filter(|o| o.alive) {
                let s = &o.stats;
                assert_eq!(o.energy, s.born_with_m + s.absorb_gain_m - s.spent_m - s.upkeep_m - s.endowed_m);
                assert!(s.paid_for_others_m <= s.spent_m);
            }
        }
        if let Some(o) = sim.genome_of(host) {
            host_paid = o.stats.paid_for_others_m;
        }
        assert!(host_paid > 0, "the host never paid for the pad");
        let initial_pools = sim.patches.len() as i64 * sim.cfg.patch_cap;
        let lhs = 2 * seed_energy + initial_pools + sim.energy_in;
        let rhs = sim.energy_in_organisms() + sim.energy_in_patches() + sim.energy_out + sim.energy_overflow;
        assert_eq!(lhs, rhs);
    }

    #[test]
    fn charge_owner_pct_conserves_energy_and_balances_ledgers() {
        // E009: the E008 ledger test under the split charge at 50%. Each
        // unit an owner pays for an intruder is in the owner's `spent_m` and
        // `paid_for_others_m`, and in the intruder's `paid_by_others_m`
        // (not its `spent_m`), so every store still balances against its
        // own ledger, and the two counters agree summed over the world.
        let mut cfg = Config::default();
        cfg.charge_owner_pct = 50;
        let mut sim = Sim::new(cfg);
        let seed_energy = 100 * MILLI;
        let host = sim.seed(1000, &ancestor(64, 16), seed_energy, 0);
        let pad = sim.seed(999, &[0x00], seed_energy, 0);
        let (mut host_paid, mut pad_helped) = (0, 0);
        // Lifetime totals of the organisms that died, then of the living.
        let (mut paid_for, mut paid_by) = (0, 0);
        for _ in 0..2000 {
            sim.run_tick();
            for ev in sim.events.drain(..) {
                if let Event::Death { id, stats, .. } = ev {
                    paid_for += stats.paid_for_others_m;
                    paid_by += stats.paid_by_others_m;
                    if id == host {
                        host_paid = stats.paid_for_others_m;
                    }
                    if id == pad {
                        pad_helped = stats.paid_by_others_m;
                    }
                }
            }
            for o in sim.orgs.iter().filter(|o| o.alive) {
                let s = &o.stats;
                assert_eq!(o.energy, s.born_with_m + s.absorb_gain_m - s.spent_m - s.upkeep_m - s.endowed_m);
                assert!(s.paid_for_others_m <= s.spent_m);
            }
        }
        for o in sim.orgs.iter().filter(|o| o.alive) {
            paid_for += o.stats.paid_for_others_m;
            paid_by += o.stats.paid_by_others_m;
            if o.id == host {
                host_paid = o.stats.paid_for_others_m;
            }
            if o.id == pad {
                pad_helped = o.stats.paid_by_others_m;
            }
        }
        assert!(host_paid > 0, "the host never paid for the pad");
        assert!(pad_helped > 0, "nobody paid for the pad");
        assert_eq!(paid_for, paid_by);
        let initial_pools = sim.patches.len() as i64 * sim.cfg.patch_cap;
        let lhs = 2 * seed_energy + initial_pools + sim.energy_in;
        let rhs = sim.energy_in_organisms() + sim.energy_in_patches() + sim.energy_out + sim.energy_overflow;
        assert_eq!(lhs, rhs);
    }

    #[test]
    fn charge_owner_pct_zero_is_the_default_world() {
        // E009: N = 0 must leave the E007 world untouched. The full check is
        // the CLI hash at tick 20,000 of seed 1 (census.csv 6f523da9f7e05a4e,
        // births.csv 33b07ce87cc80ea6); this is a short version of it, with
        // reference numbers taken from the default world at tick 2,000.
        let run = |cfg: Config| {
            let mut sim = Sim::new(cfg);
            sim.seed(sim.cfg.world_size / 2, &ancestor(64, 16), 100 * MILLI, 0);
            let (mut births, mut deaths) = (0u64, 0u64);
            for _ in 0..2000 {
                sim.run_tick();
                for ev in sim.events.drain(..) {
                    match ev {
                        Event::Birth { .. } => births += 1,
                        Event::Death { .. } => deaths += 1,
                    }
                }
            }
            (sim.alive_count(), births, deaths, sim.energy_in_organisms(), sim.energy_out)
        };
        let mut cfg = Config::default();
        cfg.charge_owner_pct = 0;
        let zero = run(cfg);
        assert_eq!(zero, run(Config::default()));
        assert_eq!(zero, (895, 28627, 27733, 688492519, 36317283733));
    }

    #[test]
    fn transfer_pct_zero_is_the_default_world() {
        // E010: N = 0 must leave the E007 world untouched; the same short
        // check as for `charge_owner_pct`, with the same reference numbers
        // (the CLI hash at tick 20,000 of seed 1 is the full check).
        let run = |cfg: Config| {
            let mut sim = Sim::new(cfg);
            sim.seed(sim.cfg.world_size / 2, &ancestor(64, 16), 100 * MILLI, 0);
            let (mut births, mut deaths) = (0u64, 0u64);
            let mut gained = 0;
            for _ in 0..2000 {
                sim.run_tick();
                for ev in sim.events.drain(..) {
                    match ev {
                        Event::Birth { .. } => births += 1,
                        Event::Death { stats, .. } => {
                            deaths += 1;
                            gained += stats.gained_from_others_m;
                        }
                    }
                }
            }
            gained += sim.orgs.iter().map(|o| o.stats.gained_from_others_m).sum::<i64>();
            assert_eq!(gained, 0);
            (sim.alive_count(), births, deaths, sim.energy_in_organisms(), sim.energy_out)
        };
        let mut cfg = Config::default();
        cfg.transfer_pct = 0;
        let zero = run(cfg);
        assert_eq!(zero, run(Config::default()));
        assert_eq!(zero, (895, 28627, 27733, 688492519, 36317283733));
    }

    #[test]
    fn transfer_conserves_energy_and_balances_ledgers() {
        // E010 at N = 150: a `pad` in front of the ancestor, noise on, so
        // the world fills with descendants and intruders of every kind.
        // Every store balances against its own ledger, now with
        // `gained_from_others_m` on the income side (the owner's loss is in
        // its `spent_m`), at every tick for the living and at death for the
        // dead. Nobody is paid for (`paid_by_others_m` stays 0), and the
        // world gained no more than owners lost (the rest went to
        // `energy_out` when the receiver's store was full).
        let mut cfg = Config::default();
        cfg.transfer_pct = 150;
        let mut sim = Sim::new(cfg);
        let seed_energy = 100 * MILLI;
        let host = sim.seed(1000, &ancestor(64, 16), seed_energy, 0);
        let pad = sim.seed(999, &[0x00], seed_energy, 0);
        let (mut host_paid, mut pad_gained) = (0, 0);
        // Lifetime totals of the organisms that died, then of the living.
        let (mut paid_for, mut gained) = (0, 0);
        let ledger = |energy: i64, s: &OrgStats| {
            assert_eq!(energy, s.born_with_m + s.absorb_gain_m + s.gained_from_others_m - s.spent_m - s.upkeep_m - s.endowed_m);
            assert_eq!(s.paid_by_others_m, 0);
            assert!(s.paid_for_others_m <= s.spent_m);
        };
        for _ in 0..2000 {
            sim.run_tick();
            for ev in sim.events.drain(..) {
                if let Event::Death { id, energy, stats, .. } = ev {
                    // `energy` is the store just before the failed upkeep
                    // (or the cull), so the ledger holds for it too.
                    ledger(energy, &stats);
                    paid_for += stats.paid_for_others_m;
                    gained += stats.gained_from_others_m;
                    if id == host {
                        host_paid = stats.paid_for_others_m;
                    }
                    if id == pad {
                        pad_gained = stats.gained_from_others_m;
                    }
                }
            }
            for o in sim.orgs.iter().filter(|o| o.alive) {
                ledger(o.energy, &o.stats);
            }
        }
        for o in sim.orgs.iter().filter(|o| o.alive) {
            paid_for += o.stats.paid_for_others_m;
            gained += o.stats.gained_from_others_m;
            if o.id == host {
                host_paid = o.stats.paid_for_others_m;
            }
            if o.id == pad {
                pad_gained = o.stats.gained_from_others_m;
            }
        }
        assert!(host_paid > 0, "the host never paid the pad");
        assert!(pad_gained > 0, "the pad never gained");
        assert!(gained > 0 && gained <= paid_for, "gained {gained}, paid for others {paid_for}");
        let initial_pools = sim.patches.len() as i64 * sim.cfg.patch_cap;
        let lhs = 2 * seed_energy + initial_pools + sim.energy_in;
        let rhs = sim.energy_in_organisms() + sim.energy_in_patches() + sim.energy_out + sim.energy_overflow;
        assert_eq!(lhs, rhs);
        eprintln!("transfer N=150, 2000 ticks: owners lost {paid_for}, executors gained {gained} (milli-units)");
    }

    /// E010 unit setups: an 8-byte host of `zero D` at 2000 and a one-byte
    /// `pad` at 1999 whose IP is put on the host's byte 0, both quiet.
    /// Returns the sim and the two ids (host, pad); `pad` is `orgs[1]`.
    fn transfer_pair(pct: i64, host_energy: i64, pad_energy: i64) -> (Sim, u32, u32) {
        let mut cfg = Config::default();
        quiet(&mut cfg);
        cfg.transfer_pct = pct;
        let mut sim = Sim::new(cfg);
        let body = crate::isa::assemble(&"zero D\n".repeat(8)).unwrap();
        let host = sim.seed(2000, &body, host_energy, 0);
        let pad = sim.seed(1999, &[0x00], pad_energy, 0);
        sim.orgs[1].ip = 2000;
        (sim, host, pad)
    }

    #[test]
    fn transfer_takes_nothing_from_debris_free_bytes_or_a_dead_owner() {
        // E010: only a living owner pays. The baseline step shows the setup
        // does transfer (N = 300: the host loses 3 units, the pad gains them);
        // then the same `zero D` run on debris, on a byte whose owner id is
        // a dead organism not yet retired, on one whose owner was retired,
        // and on free memory costs the pad exactly its own 1 unit.
        let cs = Config::default().cost_simple;
        let (mut sim, host, pad) = transfer_pair(300, 100 * MILLI, 50 * MILLI);
        let cap = sim.cfg.cap_c0;
        assert_eq!(sim.step(1, cap), Some(cs));
        assert_eq!(sim.orgs[0].energy, 100 * MILLI - 3 * cs);
        assert_eq!(sim.orgs[1].energy, 50 * MILLI - cs + 3 * cs);
        assert_eq!(sim.orgs[1].stats.gained_from_others_m, 3 * cs);
        // `check` steps the pad at `at` and asserts that nothing moved but
        // its own cost. A closure that mutates `sim` is passed it explicitly,
        // because it cannot also hold a borrow of it. The pad's index is
        // looked up each time: `retire` moves it from 1 to 0.
        let check = |sim: &mut Sim, at: u32, what: &str| {
            let k = sim.org_index(pad).unwrap();
            let (e, g, out) = (sim.orgs[k].energy, sim.orgs[k].stats.gained_from_others_m, sim.energy_out);
            sim.orgs[k].ip = at;
            assert_eq!(sim.step(k, cap), Some(cs), "{what}");
            assert_eq!(sim.orgs[k].energy, e - cs, "{what}");
            assert_eq!(sim.orgs[k].stats.gained_from_others_m, g, "{what}");
            assert_eq!(sim.energy_out, out + cs, "{what}");
        };
        // Kill the host: its bytes become debris but keep their code.
        sim.cull_all_but(pad);
        assert!(!sim.orgs[0].alive);
        assert_eq!(sim.owner[2001], DEBRIS);
        check(&mut sim, 2001, "debris");
        // A dead owner's id on a byte (kill rewrites them, so set by hand).
        sim.owner[2002] = host;
        check(&mut sim, 2002, "dead owner, not retired");
        sim.retire();
        assert!(sim.genome_of(host).is_none());
        sim.owner[2003] = host;
        check(&mut sim, 2003, "retired owner");
        sim.owner[2004] = FREE;
        check(&mut sim, 2004, "free byte");
        assert_eq!(sim.genome_of(pad).unwrap().stats.paid_by_others_m, 0);
    }

    #[test]
    fn transfer_receipt_is_capped_at_the_store() {
        // E010: the executor's room is measured after it paid its own cost,
        // and what does not fit is dissipated; the owner's loss is capped
        // by its store. N = 300, `zero D` (1 unit): take 3 units.
        let cs = Config::default().cost_simple;
        let cap_pad = Config::default().store_cap_per_byte; // 1-byte body
        // The pad starts full: after paying 1 it has room for 1 of the 3.
        let (mut sim, _, _) = transfer_pair(300, 100 * MILLI, cap_pad);
        let cap = sim.cfg.cap_c0;
        let out = sim.energy_out;
        assert_eq!(sim.step(1, cap), Some(cs), "the tick budget sees the executor's cost only");
        assert_eq!(sim.orgs[0].energy, 100 * MILLI - 3 * cs);
        assert_eq!(sim.orgs[0].stats.paid_for_others_m, 3 * cs);
        assert_eq!(sim.orgs[0].stats.spent_m, 3 * cs);
        assert_eq!(sim.orgs[1].energy, cap_pad);
        assert_eq!(sim.orgs[1].stats.gained_from_others_m, cs);
        assert_eq!(sim.orgs[1].stats.spent_m, cs);
        assert_eq!(sim.orgs[1].stats.max_energy_m, cap_pad);
        assert_eq!(sim.energy_out, out + cs + 2 * cs, "own cost plus the 2 units that did not fit");
        // An owner with 2 units gives 2, not 3, and then nothing.
        sim.orgs[0].energy = 2 * cs;
        let out = sim.energy_out;
        assert_eq!(sim.step(1, cap), Some(cs));
        assert_eq!(sim.orgs[0].energy, 0);
        assert_eq!(sim.orgs[1].energy, cap_pad);
        assert_eq!(sim.energy_out, out + cs + cs);
        let out = sim.energy_out;
        assert_eq!(sim.step(1, cap), Some(cs));
        assert_eq!(sim.orgs[0].stats.paid_for_others_m, 5 * cs);
        assert_eq!(sim.orgs[1].energy, cap_pad - cs);
        assert_eq!(sim.energy_out, out + cs);
        assert_eq!(sim.orgs[1].stats.gained_from_others_m, 2 * cs);
    }

    #[test]
    #[should_panic(expected = "cannot be combined")]
    fn transfer_refuses_an_owner_pays_rule() {
        let mut cfg = Config::default();
        cfg.transfer_pct = 150;
        cfg.charge_owner_pct = 25;
        Sim::new(cfg);
    }

    #[test]
    fn founders_are_placed_by_the_formula() {
        // E009a: two founders, one ancestor then one other genome, sit at
        // world_size / 2 + world_size * j / 2 for j = 0, 1, in flag order.
        let mut sim = Sim::new(Config::default());
        let n = sim.cfg.world_size;
        let other = crate::isa::assemble("zero D\nzero D").unwrap();
        let starts = sim.seed_founders(&[(ancestor(120, 16), 1), (other.clone(), 1)], 100 * MILLI);
        assert_eq!(starts, vec![n / 2, 0]);
        assert_eq!(sim.orgs[0].start, n / 2);
        assert_eq!(sim.orgs[0].genome, ancestor(120, 16));
        assert_eq!(sim.orgs[1].start, 0);
        assert_eq!(sim.orgs[1].genome, other);
        assert_eq!(sim.region(0, 2), other);
        assert!(sim.orgs.iter().all(|o| o.energy == 100 * MILLI));
        // E009a's 110 founders, and 128: no two in one patch of the default world.
        for total in [110, 128] {
            let s = founder_starts(n, total);
            assert_eq!(s.len(), total as usize);
            assert_eq!(s[1], n / 2 + n / total);
            let patches: std::collections::HashSet<usize> = s.iter().map(|&a| sim.patch_of(a)).collect();
            assert_eq!(patches.len(), total as usize, "{total} founders share a patch");
        }
    }

    #[test]
    fn one_founder_is_the_default_seeding() {
        // E009a: `--founder <ancestor hex>:1` must be the run with no flag.
        // The founder lands at world_size / 2 (j = 0), as the default seed
        // does, so the two sims match tick for tick.
        let mut a = Sim::new(Config::default());
        a.seed(a.cfg.world_size / 2, &ancestor(64, 16), 100 * MILLI, 0);
        let mut b = Sim::new(Config::default());
        b.seed_founders(&[(ancestor(64, 16), 1)], 100 * MILLI);
        for _ in 0..1000 {
            a.run_tick();
            b.run_tick();
        }
        assert_eq!(a.state_hash(), b.state_hash());
        assert_eq!(a.events.len(), b.events.len());
    }

    #[test]
    fn inject_targets_and_skip_rule() {
        // E009b: a 1,024-byte world, 4 copies of a 4-byte genome. Targets
        // 512, 768, 0, 256. Ownership is set by hand (99 stands for any
        // living id): copy 0 finds 512-513 living and lands at 514; copy 1
        // finds 768-1022 living, and its run beginning at 1023 (the last
        // offset before copy 2's target) wraps over debris at 0-2, so it
        // lands at 1023; copy 2 then finds 0-2 owned by copy 1 and lands at
        // 3 (debris and free bytes); copy 3 finds 256-510 living and the run
        // at 511 blocked by 512, so no run begins before 512: skipped.
        let mut cfg = Config::default();
        quiet(&mut cfg);
        cfg.world_size = 1024;
        cfg.patch_size = 256;
        let mut sim = Sim::new(cfg);
        let live = 99;
        for a in [512, 513].into_iter().chain(768..1023).chain(256..511) {
            sim.owner[a] = live;
        }
        for a in 0..5 {
            sim.owner[a] = DEBRIS;
            sim.bytes[a] = 0xee;
        }
        let rng_before = sim.rng.state();
        let g = vec![0x11, 0x22, 0x33, 0x44];
        let (starts, ids) = sim.inject(&g, 4, 100 * MILLI, 7);
        assert_eq!(starts, vec![514, 1023, 3, -1]);
        assert_eq!(ids.len(), 3);
        assert_eq!(sim.rng.state(), rng_before, "inject drew from the PRNG");
        assert_eq!(sim.region(1023, 4), g);
        assert_eq!(sim.region(3, 4), g);
        for (&id, &s) in ids.iter().zip([514u32, 1023, 3].iter()) {
            let o = sim.genome_of(id).unwrap();
            assert_eq!((o.start, o.birth_tick, o.parent, o.energy), (s, 7, 0, 100 * MILLI));
            for k in 0..4 {
                assert_eq!(sim.owner[sim.wrap(s + k) as usize], id);
            }
        }
        // Copy 2 covers 3-6; byte 7 is free and untouched.
        assert_eq!(sim.owner[7], FREE);
    }

    #[test]
    fn inject_leaves_earlier_ticks_identical() {
        // An injection at tick T changes nothing before T: the state hash
        // after tick T - 1 matches a run without it, and differs after T.
        let t = 300;
        let inj = [Injection { tick: t, genome: ancestor(120, 16), count: 5 }];
        let mut a = Sim::new(Config::default());
        let mut b = Sim::new(Config::default());
        for s in [&mut a, &mut b] {
            s.seed_founders(&[(ancestor(64, 16), 1)], 100 * MILLI);
        }
        let mut placed = Vec::new();
        for _ in 0..t - 1 {
            assert!(a.inject_due(&[], 100 * MILLI).is_empty());
            a.run_tick();
            placed.extend(b.inject_due(&inj, 100 * MILLI));
            b.run_tick();
        }
        assert_eq!(a.tick, t - 1);
        assert!(placed.is_empty());
        assert_eq!(a.state_hash(), b.state_hash());
        let done = b.inject_due(&inj, 100 * MILLI);
        b.run_tick();
        a.run_tick();
        assert_eq!(done.len(), 1);
        assert_eq!(done[0].starts.len(), 5);
        assert!(!done[0].ids.is_empty());
        for &id in &done[0].ids {
            assert_eq!(b.genome_of(id).map(|o| o.birth_tick), Some(t));
        }
        assert_ne!(a.state_hash(), b.state_hash());
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
        // Dead organisms are retired at the next tick, so it is gone.
        assert_eq!(sim.alive_count(), 0);
        assert!(sim.genome_of(FIRST_ID).is_none());
        assert_eq!(sim.owner[100], DEBRIS);
    }
}
