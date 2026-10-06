//! All tunables in one place (PLAN.md §5.3.4, §5.4, §5.7). Energy is in
//! milli-units (1 energy unit = 1000) so fractional upkeep stays integer and
//! runs are bit-for-bit reproducible across machines.

pub const MILLI: i64 = 1000;

#[derive(Clone, Debug)]
pub struct Config {
    pub seed: u64,
    /// World size in bytes (1D ring in Phase 1).
    pub world_size: u32,
    /// Bytes per patch.
    pub patch_size: u32,
    /// Patch pools start full (true) or empty (false).
    pub pools_start_full: bool,
    /// Locality radius: max ring distance from IP for any memory op.
    pub locality: u32,

    // Energy (milli-units)
    pub patch_income: i64,
    pub patch_cap: i64,
    pub absorb_rate: i64,
    /// Upkeep per body byte per tick.
    pub upkeep_per_byte: i64,
    /// Max energy an organism can hold: store_cap_per_byte * body length.
    /// Absorb beyond it is wasted (stays in the patch). Matter holds finite
    /// energy; without this, non-replicating absorbers hoard without bound.
    pub store_cap_per_byte: i64,
    /// Per-tick execution cap: c0 + c1 * body_len.
    pub cap_c0: i64,
    pub cap_c1: i64,
    pub write_protection: bool,
    /// `alloc` claims the farthest fitting free run within locality instead
    /// of the nearest. Dispersal experiment (E002); default off.
    pub alloc_far: bool,
    /// `absorb` takes a ration proportional to how full the pool is,
    /// `absorb_rate * pool / patch_cap`, instead of `min(pool, absorb_rate)`.
    /// First-order uptake of a dilute resource (E004); default off.
    pub absorb_proportional: bool,

    // Costs (milli-units)
    pub cost_simple: i64,
    pub cost_load: i64,
    pub cost_store: i64,
    pub cost_copy: i64,
    pub cost_search_base: i64,
    pub cost_search_per16: i64,
    pub cost_alloc_base: i64,
    pub cost_alloc_per_byte: i64,
    pub cost_divide: i64,
    pub cost_absorb: i64,

    // Noise
    /// Probability a write stores a byte with one random bit flipped.
    pub p_write_flip: f64,
    /// Probability a `copy` slips (A or B fails to advance, or advances twice).
    pub q_slip: f64,
    /// Per-byte per-tick background bit-flip probability.
    pub p_bit_rot: f64,
    /// Per-byte per-tick probability that a debris byte becomes free.
    pub p_debris_decay: f64,
}

impl Config {
    /// Every field as (name, value text), for run metadata. The destructuring
    /// has no `..`, so adding a field without listing it here fails to compile.
    pub fn fields(&self) -> Vec<(&'static str, String)> {
        let Config {
            seed, world_size, patch_size, pools_start_full, locality,
            patch_income, patch_cap, absorb_rate, upkeep_per_byte,
            store_cap_per_byte, cap_c0, cap_c1, write_protection, alloc_far,
            absorb_proportional,
            cost_simple, cost_load, cost_store, cost_copy, cost_search_base,
            cost_search_per16, cost_alloc_base, cost_alloc_per_byte, cost_divide,
            cost_absorb, p_write_flip, q_slip, p_bit_rot, p_debris_decay,
        } = self;
        vec![
            ("seed", seed.to_string()),
            ("world_size", world_size.to_string()),
            ("patch_size", patch_size.to_string()),
            ("pools_start_full", pools_start_full.to_string()),
            ("locality", locality.to_string()),
            ("patch_income", patch_income.to_string()),
            ("patch_cap", patch_cap.to_string()),
            ("absorb_rate", absorb_rate.to_string()),
            ("upkeep_per_byte", upkeep_per_byte.to_string()),
            ("store_cap_per_byte", store_cap_per_byte.to_string()),
            ("cap_c0", cap_c0.to_string()),
            ("cap_c1", cap_c1.to_string()),
            ("write_protection", write_protection.to_string()),
            ("alloc_far", alloc_far.to_string()),
            ("absorb_proportional", absorb_proportional.to_string()),
            ("cost_simple", cost_simple.to_string()),
            ("cost_load", cost_load.to_string()),
            ("cost_store", cost_store.to_string()),
            ("cost_copy", cost_copy.to_string()),
            ("cost_search_base", cost_search_base.to_string()),
            ("cost_search_per16", cost_search_per16.to_string()),
            ("cost_alloc_base", cost_alloc_base.to_string()),
            ("cost_alloc_per_byte", cost_alloc_per_byte.to_string()),
            ("cost_divide", cost_divide.to_string()),
            ("cost_absorb", cost_absorb.to_string()),
            // `{:?}` prints f64 with enough digits to round-trip exactly.
            ("p_write_flip", format!("{p_write_flip:?}")),
            ("q_slip", format!("{q_slip:?}")),
            ("p_bit_rot", format!("{p_bit_rot:?}")),
            ("p_debris_decay", format!("{p_debris_decay:?}")),
        ]
    }
}

impl Default for Config {
    fn default() -> Config {
        Config {
            seed: 1,
            world_size: 1 << 16,
            patch_size: 1 << 12,
            locality: 512,
            pools_start_full: true,
            patch_income: 256 * MILLI,
            patch_cap: 4096 * MILLI,
            absorb_rate: 8 * MILLI,
            upkeep_per_byte: MILLI / 10,
            store_cap_per_byte: 64 * MILLI,
            cap_c0: 32 * MILLI,
            cap_c1: 0,
            write_protection: true,
            alloc_far: false,
            absorb_proportional: false,
            cost_simple: MILLI,
            cost_load: 2 * MILLI,
            cost_store: 2 * MILLI,
            cost_copy: 3 * MILLI,
            cost_search_base: MILLI,
            cost_search_per16: MILLI,
            cost_alloc_base: 2 * MILLI,
            cost_alloc_per_byte: MILLI,
            cost_divide: 8 * MILLI,
            cost_absorb: MILLI,
            p_write_flip: 0.1 / 21.0,
            q_slip: 0.1 / 21.0 / 4.0,
            p_bit_rot: 1e-5,
            p_debris_decay: 0.001,
        }
    }
}
