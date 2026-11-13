"""Erdős problem 458: is lcm(1..p_{k+1}-1) < p_k * lcm(1..p_k) for every k?

Reduction: every integer strictly between consecutive primes p_k < p_{k+1} is
composite, and lcm(1..x) gains a factor q exactly when x passes a prime power
q^a. So

    lcm(1..p_{k+1}-1) / lcm(1..p_k) = product of q over prime powers q^a (a >= 2)
                                      with p_k < q^a < p_{k+1}.

The inequality fails only if that product is >= p_k. This script
  1. checks the reduction against exact lcm computation for small k, and
  2. enumerates every prime power q^a <= X (a >= 2), finds the prime gap that
     contains it, and tests the inequality for every gap with p_{k+1} <= X.
Usage: python gaps_458.py X     (standard library only)
"""
import math
import sys
import time
from collections import defaultdict

X = int(float(sys.argv[1])) if len(sys.argv) > 1 else 10**12

SMALL = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]


def is_prime(n: int) -> bool:
    """Deterministic Miller-Rabin for n < 3.3e24."""
    if n < 2:
        return False
    for p in SMALL:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in SMALL:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def prev_prime(n: int) -> int:
    n -= 1
    while not is_prime(n):
        n -= 1
    return n


def next_prime(n: int) -> int:
    n += 1
    while not is_prime(n):
        n += 1
    return n


def primes_upto(n: int) -> list[int]:
    sieve = bytearray([1]) * (n + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
    return [i for i in range(n + 1) if sieve[i]]


t0 = time.time()

# 1. Exact check of the reduction for primes below 3000.
ps = primes_upto(3000)
for pk, pk1 in zip(ps, ps[1:]):
    lhs = math.lcm(*range(1, pk1))
    base = math.lcm(*range(1, pk + 1))
    ratio = lhs // base
    pred = math.prod(q for q in ps if q * q < pk1 for a in range(2, 40) if pk < q ** a < pk1)
    assert lhs % base == 0 and ratio == pred, (pk, ratio, pred)
    assert lhs < pk * base, ("inequality fails", pk)
print(f"reduction matches exact lcm for all {len(ps) - 1} gaps below 3000")

# 2. Every prime power q^a <= X with a >= 2.
gap_factors = defaultdict(list)      # p_k -> [(q, q^a), ...]
gap_end = {}
qs = primes_upto(math.isqrt(X))
count = 0
for q in qs:
    x = q * q
    while x <= X:
        pk = prev_prime(x)
        gap_factors[pk].append((q, x))
        if pk not in gap_end:
            gap_end[pk] = next_prime(x)
        count += 1
        x *= q

worst = (0.0, None)
fail = []
multi = []
for pk, items in gap_factors.items():
    if gap_end[pk] > X:
        continue
    prod = math.prod(q for q, _ in items)
    r = prod / pk
    if r > worst[0]:
        worst = (r, pk)
    if prod >= pk:
        fail.append(pk)
    if len(items) >= 2:
        multi.append((pk, gap_end[pk], items, prod))

print(f"X = {X:.3e}: {count} prime powers, {len(gap_factors)} gaps contain at least one")
print(f"gaps containing two or more prime powers: {len(multi)}")
for pk, pk1, items, prod in sorted(multi)[:12]:
    print(f"  ({pk}, {pk1}): {[x for _, x in items]}  product of bases {prod}  ratio to p_k {prod / pk:.3g}")
print(f"largest ratio product/p_k: {worst[0]:.4g} at p_k = {worst[1]}")
print(f"failures of the inequality: {fail if fail else 'none'}")
print(f"elapsed: {time.time() - t0:.1f} s")
