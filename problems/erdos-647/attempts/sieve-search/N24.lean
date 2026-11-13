import Mathlib

/-!
Erdős problem 647, the known case n = 24: every m < 24 has m + τ(m) ≤ 26 = 24 + 2,
where τ(m) is the number of divisors of m.
-/

theorem erdos647_n24 : ∀ m < 24, m + (Nat.divisors m).card ≤ 24 + 2 := by
  decide +kernel
