"""
estimate_min_entropy_large.py — k=512/1024 熵估计 (§6.1 外推斜率确认)

小样本策略: 熵估计只需要分布形状, 样本 6k-15k 足够 H1 ±0.3 bit。
"""
import random
import time
import math
from collections import Counter

random.seed(20260922)

def T(x): return x // 2 if x % 2 == 0 else 3 * x + 1

def d_shortest(a, b, max_steps=200000):
    va = {a: 0}; vb = {b: 0}; ca, cb = a, b
    for tot in range(1, max_steps + 1):
        ca = T(ca)
        if ca in vb: return tot + vb[ca]
        va[ca] = tot
        cb = T(cb)
        if cb in va: return va[cb] + tot
        vb[cb] = tot
    return None

def keygen(k):
    while True:
        a = random.randint(1 << (k - 1), (1 << k) - 1)
        b = random.randint(1 << (k - 1), (1 << k) - 1)
        n = d_shortest(a, b)
        if n: return a, b, n

print(f"{'k':>5} {'N':>7} {'U':>8} {'Hinf':>8} {'H2':>8} {'H1':>8}  耗时")
for k, N in ((512, 15000), (1024, 6000)):
    a0, b0, n = keygen(k)
    m = abs(a0 - b0)
    lo, hi = 1 << (k - 1), 1 << k
    t0 = time.time()
    cnt = Counter()
    while sum(cnt.values()) < N:
        a = random.randint(lo, hi - 1)
        for b in (a + m, a - m):
            if lo <= b < hi:
                d = d_shortest(a, b)
                if d is not None:
                    cnt[d] += 1
                break
    total = sum(cnt.values())
    U = len(cnt)
    pmax = max(cnt.values()) / total
    Hinf = -math.log2(pmax)
    H2 = -math.log2(sum((c / total) ** 2 for c in cnt.values()))
    H1 = -sum((c / total) * math.log2(c / total) for c in cnt.values())
    print(f"{k:>5} {total:>7} {U:>8} {Hinf:>8.2f} {H2:>8.2f} {H1:>8.2f}  {time.time()-t0:.0f}s")
    print(f"      (n={n}, m位长={m.bit_length()})", flush=True)
