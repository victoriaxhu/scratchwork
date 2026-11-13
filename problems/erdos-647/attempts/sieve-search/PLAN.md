# Plan: sieve-search

Search directly for n > 24 with max over m < n of (m + τ(m)) ≤ n + 2. Compute τ(m) with a divisor-pair sieve up to a bound N, take the running maximum M(n) of m + τ(m), and list every n with M(n) ≤ n + 2. A hit above 24 answers the question; no hit raises the floor for any example. Also formalise the known case n = 24 in Lean.
