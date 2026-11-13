"""Erdős problem 647: find n with max_{1 <= m < n} (m + tau(m)) <= n + 2.

Usage: python search_647.py N
Requires numpy. Prints every n <= N satisfying the condition.
tau is computed by a divisor-pair sieve: for each d <= sqrt(N), d^2 gains 1
divisor and every d*k with k > d gains 2 (d and k).
"""
import sys
import time
import numpy as np

N = int(sys.argv[1]) if len(sys.argv) > 1 else 10**7
t0 = time.time()
tau = np.zeros(N + 1, dtype=np.int32)
d = 1
while d * d <= N:
    tau[d * d] += 1
    tau[d * (d + 1)::d] += 2
    d += 1

# Sanity check against brute force for small m.
for m in range(1, 2000):
    assert tau[m] == sum(1 for k in range(1, m + 1) if m % k == 0), m

val = np.arange(N + 1, dtype=np.int64) + tau      # m + tau(m)
val[0] = 0                                       # m = 0 is not a positive integer
M = np.maximum.accumulate(val)                   # M[j] = max_{m <= j} (m + tau(m))
n = np.arange(2, N + 1, dtype=np.int64)
ok = M[n - 1] <= n + 2                           # condition for n uses m <= n - 1
hits = n[ok]
print(f"N = {N}")
print(f"n <= N satisfying the condition: {hits.tolist()}")
print(f"largest: {int(hits.max())}; any above 24: {bool((hits > 24).any())}")
print(f"elapsed: {time.time() - t0:.1f} s")
