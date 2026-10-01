//! Seeded PRNG: xoshiro256** (Blackman & Vigna). Hand-rolled so the crate
//! has zero dependencies and the stream is fixed forever by this file.
//!
//! Rust note for Zig/Go readers: `impl Rng { fn next_u64(&mut self) }` is a
//! method taking a mutable borrow of self, like a Zig `fn next(self: *Rng)`
//! or a Go pointer receiver. The caller must hold a `&mut Rng`, and Rust
//! checks at compile time that nobody else reads it meanwhile.

#[derive(Clone, Debug)]
pub struct Rng {
    s: [u64; 4],
}

impl Rng {
    /// Seed via splitmix64 so that nearby seeds give unrelated streams.
    pub fn new(seed: u64) -> Rng {
        let mut x = seed;
        let mut s = [0u64; 4];
        for v in s.iter_mut() {
            x = x.wrapping_add(0x9E3779B97F4A7C15);
            let mut z = x;
            z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
            z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);
            *v = z ^ (z >> 31);
        }
        Rng { s }
    }

    pub fn next_u64(&mut self) -> u64 {
        let s = &mut self.s;
        let result = s[1].wrapping_mul(5).rotate_left(7).wrapping_mul(9);
        let t = s[1] << 17;
        s[2] ^= s[0];
        s[3] ^= s[1];
        s[1] ^= s[2];
        s[0] ^= s[3];
        s[2] ^= t;
        s[3] = s[3].rotate_left(45);
        result
    }

    /// Uniform in [0, n). n must be > 0.
    pub fn below(&mut self, n: u64) -> u64 {
        // Lemire's multiply-shift, unbiased enough for simulation use.
        ((self.next_u64() as u128 * n as u128) >> 64) as u64
    }

    /// Uniform f64 in [0, 1).
    pub fn unit(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 * (1.0 / (1u64 << 53) as f64)
    }

    /// Bernoulli trial with probability p.
    pub fn chance(&mut self, p: f64) -> bool {
        p > 0.0 && self.unit() < p
    }

    /// Number of failed Bernoulli(p) trials before the next success.
    /// Lets a loop over n bytes with per-byte probability p jump straight
    /// to the next hit instead of drawing n random numbers; the resulting
    /// event positions have the same distribution.
    pub fn geometric(&mut self, p: f64) -> u64 {
        if p >= 1.0 {
            return 0;
        }
        if p <= 0.0 {
            return u64::MAX;
        }
        // 1 - unit() is in (0, 1], so ln is finite. ln_1p(-p) keeps
        // precision for tiny p. f64 -> u64 casts saturate, never wrap.
        let u = 1.0 - self.unit();
        (u.ln() / (-p).ln_1p()).floor() as u64
    }

    /// Fisher–Yates shuffle in place.
    pub fn shuffle<T>(&mut self, v: &mut [T]) {
        for i in (1..v.len()).rev() {
            let j = self.below(i as u64 + 1) as usize;
            v.swap(i, j);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn deterministic() {
        let mut a = Rng::new(42);
        let mut b = Rng::new(42);
        for _ in 0..100 {
            assert_eq!(a.next_u64(), b.next_u64());
        }
    }

    #[test]
    fn below_in_range() {
        let mut r = Rng::new(1);
        for _ in 0..10_000 {
            assert!(r.below(7) < 7);
        }
    }

    #[test]
    fn geometric_matches_bernoulli_rate() {
        // Hits over n positions should average p * n.
        let mut r = Rng::new(3);
        let (p, n) = (1e-3, 10_000_000u64);
        let mut hits = 0u64;
        let mut a = r.geometric(p);
        while a < n {
            hits += 1;
            a += 1 + r.geometric(p);
        }
        let want = p * n as f64; // 10,000; sd ~100
        assert!((hits as f64 - want).abs() < 5.0 * want.sqrt(), "hits {hits}");
    }

    #[test]
    fn geometric_edges() {
        let mut r = Rng::new(1);
        assert_eq!(r.geometric(1.0), 0);
        assert_eq!(r.geometric(0.0), u64::MAX);
    }
}
