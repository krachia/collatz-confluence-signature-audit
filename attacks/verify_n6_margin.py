# -*- coding: utf-8 -*-
r"""verify_n6_margin.py — §4.3 实例的 τ(b')≤n−6 充分条件余量核验
复现 round2_noz_cyclekill.py 的 8 个实例（同种子 20260907），
对每个实例输出：n、τ(b')（b'=1+m 进入 {1,4,2} 的首达时间）与余量 (n−6)−τ(b')。
"""
import random
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

random.seed(20260907)


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


def first_meeting(a, b, max_steps):
    va = {a: 0}
    vb = {b: 0}
    ca, cb = a, b
    for total in range(1, max_steps + 1):
        ca = T(ca)
        if ca in vb:
            return (total, vb[ca], ca)
        va[ca] = total
        cb = T(cb)
        if cb in va:
            return (va[cb], total, cb)
        vb[cb] = total
    return None


def keygen_nodelay(k, max_steps=20000):
    while True:
        a = random.randint(1 << (k - 1), (1 << k) - 1)
        b = random.randint(1 << (k - 1), (1 << k) - 1)
        if a == b:
            continue
        r = first_meeting(a, b, max_steps)
        if r:
            s, t, z = r
            return a, b, s + t, z


def tau_first_cycle(x, limit=200000):
    d = 0
    while x not in (1, 2, 4) and d < limit:
        x = T(x)
        d += 1
    return d if x in (1, 2, 4) else None


print("k |  trial | n | tau(b') | 余量 (n-6)-tau")
worst = None
for k in (128, 256):
    for trial in range(4):
        a0, b0, n, z0 = keygen_nodelay(k)
        m = abs(a0 - b0)
        bp = 1 + m
        tb = tau_first_cycle(bp)
        margin = (n - 6) - tb
        print("%3d | %5d | %5d | %7d | %d" % (k, trial, n, tb, margin))
        if worst is None or margin < worst:
            worst = margin
print()
print("最小余量：", worst, "（正数即满足 τ(b') <= n-6）")
