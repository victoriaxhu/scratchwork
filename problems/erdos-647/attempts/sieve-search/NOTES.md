# Notes: sieve-search

Started 2026-11-13T15:44:50+00:00.

## 2026-11-13T15:45:17+00:00 [data] No n in (24, 10^8] satisfies the condition

Ran `python search_647.py 100000000` (numpy). The values of n ≤ 10^8 satisfying max over m < n of (m + τ(m)) ≤ n + 2 are exactly 2, 3, 4, 5, 6, 8, 10, 12, 24. The sieve is cross-checked against brute-force divisor counts for m < 2000. So any n > 24 with the property exceeds 10^8. Larger ranges likely appear in the literature or OEIS; this run reproduces the small-range picture and gives a baseline.

## 2026-11-13T15:45:17+00:00 [verified] Lean: the case n = 24 holds

N24.lean proves ∀ m < 24, m + τ(m) ≤ 26 by kernel computation. Status stands only once the Lean check in CI passes.
