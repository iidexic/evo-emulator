//! Instruction set: byte -> (opcode, modifier). PLAN.md §5.3.2–5.3.3.
//!
//! One byte per instruction. Low 5 bits = opcode (32 slots, 25 used, the
//! rest decode as `Pad`). High 3 bits = modifier: register select for
//! register ops (`mod & 3`, so each register has two encodings), variant
//! select for `Self_`, ignored otherwise.
//!
//! Opcode numbers are chosen so one-bit flips are mild (§5.3.2): paired ops
//! differ in one bit; `Copy`/`Alloc`/`Divide` sit at Hamming distance >= 2
//! from `Pad`/`Nop0`/`Nop1`.
//!
//! Rust note: `enum Op` with explicit discriminants is like a Zig
//! `enum(u5)` or a Go `const ( ... iota )` block, but exhaustive `match`
//! on it is checked by the compiler.

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
#[repr(u8)]
pub enum Op {
    Pad = 0,
    Nop0 = 1,
    Nop1 = 3,
    Inc = 4,
    Dec = 5,
    Shl = 6,
    Shr = 7,
    Skipz = 8,
    Skipnz = 9,
    Searchf = 10,
    Searchb = 11,
    Jmpr = 12,
    Jmpa = 13,
    Add = 14,
    Sub = 15,
    Zero = 16,
    Lit = 17,
    Swap = 18,
    Self_ = 19,
    Load = 20,
    Store = 21,
    Absorb = 22,
    Copy = 24,
    Alloc = 26,
    Divide = 28,
}

pub const OP_COUNT: usize = 25;

/// Decode table, built once. Index = low 5 bits of the byte.
const TABLE: [Op; 32] = {
    let mut t = [Op::Pad; 32];
    let ops = [
        Op::Pad, Op::Nop0, Op::Nop1, Op::Inc, Op::Dec, Op::Shl, Op::Shr,
        Op::Skipz, Op::Skipnz, Op::Searchf, Op::Searchb, Op::Jmpr, Op::Jmpa,
        Op::Add, Op::Sub, Op::Zero, Op::Lit, Op::Swap, Op::Self_, Op::Load,
        Op::Store, Op::Absorb, Op::Copy, Op::Alloc, Op::Divide,
    ];
    let mut i = 0;
    while i < ops.len() {
        t[ops[i] as usize] = ops[i];
        i += 1;
    }
    t
};

#[inline]
pub fn decode(byte: u8) -> (Op, u8) {
    (TABLE[(byte & 0x1F) as usize], byte >> 5)
}

#[inline]
pub fn encode(op: Op, modifier: u8) -> u8 {
    (op as u8) | ((modifier & 7) << 5)
}

/// Register index 0..4 (A, B, C, D) from a modifier.
#[inline]
pub fn reg_of(modifier: u8) -> usize {
    (modifier & 3) as usize
}

pub const REG_A: u8 = 0;
pub const REG_B: u8 = 1;
pub const REG_C: u8 = 2;
pub const REG_D: u8 = 3;

impl Op {
    pub fn is_nop(self) -> bool {
        matches!(self, Op::Nop0 | Op::Nop1)
    }

    /// Length in bytes of an instruction starting with this op.
    pub fn len(self) -> u32 {
        if self == Op::Lit { 2 } else { 1 }
    }

    pub fn name(self) -> &'static str {
        match self {
            Op::Pad => "pad", Op::Nop0 => "nop0", Op::Nop1 => "nop1",
            Op::Inc => "inc", Op::Dec => "dec", Op::Shl => "shl", Op::Shr => "shr",
            Op::Skipz => "skipz", Op::Skipnz => "skipnz",
            Op::Searchf => "searchf", Op::Searchb => "searchb",
            Op::Jmpr => "jmpr", Op::Jmpa => "jmpa", Op::Add => "add", Op::Sub => "sub",
            Op::Zero => "zero", Op::Lit => "lit", Op::Swap => "swap", Op::Self_ => "self",
            Op::Load => "load", Op::Store => "store", Op::Absorb => "absorb",
            Op::Copy => "copy", Op::Alloc => "alloc", Op::Divide => "divide",
        }
    }
}

/// Tiny assembler for hand-written genomes and tests. One instruction per
/// element: `"self"`, `"swap B"`, `"lit D -4"`, `"self 2"` (modifier).
pub fn assemble(src: &str) -> Result<Vec<u8>, String> {
    let mut out = Vec::new();
    for line in src.lines() {
        let line = line.split(';').next().unwrap().trim();
        if line.is_empty() {
            continue;
        }
        let mut parts = line.split_whitespace();
        let name = parts.next().unwrap();
        let op = ALL.iter().copied().find(|o| o.name() == name)
            .ok_or_else(|| format!("unknown op {name:?}"))?;
        let arg = parts.next();
        let modifier = match arg {
            Some("A") => 0, Some("B") => 1, Some("C") => 2, Some("D") => 3,
            Some(n) => n.parse::<u8>().map_err(|e| format!("{line}: {e}"))?,
            None => 0,
        };
        out.push(encode(op, modifier));
        if op == Op::Lit {
            let v: i32 = parts.next().ok_or(format!("{line}: lit needs a value"))?
                .parse().map_err(|e| format!("{line}: {e}"))?;
            if !(-128..=127).contains(&v) {
                return Err(format!("{line}: literal out of range"));
            }
            out.push(v as i8 as u8);
        }
    }
    Ok(out)
}

pub const ALL: [Op; OP_COUNT] = [
    Op::Pad, Op::Nop0, Op::Nop1, Op::Inc, Op::Dec, Op::Shl, Op::Shr,
    Op::Skipz, Op::Skipnz, Op::Searchf, Op::Searchb, Op::Jmpr, Op::Jmpa,
    Op::Add, Op::Sub, Op::Zero, Op::Lit, Op::Swap, Op::Self_, Op::Load,
    Op::Store, Op::Absorb, Op::Copy, Op::Alloc, Op::Divide,
];

/// Disassemble one instruction at `bytes[i]`. Returns text and length.
pub fn disasm_at(bytes: &[u8], i: usize) -> (String, usize) {
    let (op, m) = decode(bytes[i]);
    let regname = ["A", "B", "C", "D"][reg_of(m)];
    match op {
        Op::Lit => {
            let v = bytes.get(i + 1).copied().unwrap_or(0) as i8;
            (format!("lit {regname} {v}"), 2)
        }
        Op::Inc | Op::Dec | Op::Shl | Op::Shr | Op::Add | Op::Sub | Op::Zero
        | Op::Swap | Op::Load | Op::Store | Op::Skipz | Op::Skipnz | Op::Jmpr
        | Op::Jmpa | Op::Alloc | Op::Divide => (format!("{} {regname}", op.name()), 1),
        Op::Self_ => (format!("self {}", m), 1),
        _ => (op.name().to_string(), 1),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_byte_decodes_and_unassigned_is_pad() {
        for b in 0..=255u8 {
            let (op, m) = decode(b);
            assert!(m < 8);
            let slot = b & 0x1F;
            if ALL.iter().any(|o| *o as u8 == slot) {
                assert_eq!(op as u8, slot);
            } else {
                assert_eq!(op, Op::Pad);
            }
        }
        assert_eq!(decode(0).0, Op::Pad);
    }

    #[test]
    fn hamming_rules() {
        let ham = |a: Op, b: Op| ((a as u8) ^ (b as u8)).count_ones();
        for (a, b) in [(Op::Inc, Op::Dec), (Op::Shl, Op::Shr), (Op::Skipz, Op::Skipnz),
                       (Op::Searchf, Op::Searchb), (Op::Nop0, Op::Nop1), (Op::Jmpr, Op::Jmpa)] {
            assert_eq!(ham(a, b), 1, "{a:?}/{b:?}");
        }
        for d in [Op::Copy, Op::Alloc, Op::Divide] {
            for f in [Op::Pad, Op::Nop0, Op::Nop1] {
                assert!(ham(d, f) >= 2, "{d:?} vs {f:?}");
            }
        }
    }

    #[test]
    fn assemble_roundtrip() {
        let g = assemble("self\nswap B\nlit D -4\ncopy ; comment\n").unwrap();
        assert_eq!(g.len(), 5);
        assert_eq!(decode(g[1]), (Op::Swap, REG_B));
        assert_eq!(g[3] as i8, -4);
        assert_eq!(disasm_at(&g, 2).0, "lit D -4");
    }
}
