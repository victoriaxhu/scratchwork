# Notes: prime-powers-in-gaps

Started 2026-11-13T15:47:40+00:00.

## 2026-11-13T15:47:40+00:00 [lemma] Reduction to prime powers in prime gaps; one prime power never fails

**Claim 1.** lcm(1..p_{k+1}-1) / lcm(1..p_k) = ∏ q over prime powers q^a with a ≥ 2 and p_k < q^a < p_{k+1}.
Every integer strictly inside the gap is composite, and lcm(1..x) is multiplied by q exactly when x reaches a power of the prime q. Checked against exact lcm computation for all 429 gaps below 3000 (gaps_458.py).

**Claim 2.** If a gap contains exactly one prime power q^a, the inequality holds.
The ratio is q, and q ≤ √(q^a) < √(p_{k+1}) ≤ p_k, using p_{k+1} < 2p_k ≤ p_k² (Bertrand) for p_k ≥ 2.

So a counterexample needs at least two prime powers in one prime gap whose bases multiply to at least p_k. With two prime powers the product of bases is at most p_{k+1}, so roughly this needs two prime squares q², r² in one gap with qr ≥ p_k, i.e. a gap of length about 2√p_k, far beyond what is expected (Cramér) but not ruled out by any proven gap bound.

## 2026-11-13T15:47:40+00:00 [data] No counterexample for any gap with p_{k+1} ≤ 10^14

Enumerated all 670,121 prime powers q^a ≤ 10^14 (a ≥ 2), located each one's prime gap with deterministic Miller-Rabin, and tested every gap. Only 5 gaps contain two or more prime powers: (7, 11), (23, 29), (113, 127), (2179, 2203), (32749, 32771). The largest ratio of product to p_k is 6/7 ≈ 0.857 at p_k = 7. No failures.
