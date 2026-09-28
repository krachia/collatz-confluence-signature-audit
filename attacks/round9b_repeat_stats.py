# -*- coding: utf-8 -*-
"""
round9b_repeat_stats.py — L 扩展的重复运行统计（回应审稿：单次运行波动大）

目的: 检验「总伪造成本与 L 成正比」是否为可重复的期望性质（而非单次巧合）。
方法: 对 L ∈ {4,16,64,256} 各独立重复 5 次（不同随机种子与消息摘要），
      报告总成本的均值±标准差、每位均值，以及跨 L 的线性度。
"""
import random
import hashlib
import time

K = 64
REP = 5

def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1

def first_meeting(a, b, max_steps=30000):
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

def d_shortest(a, b, max_steps=30000):
    r = first_meeting(a, b, max_steps)
    return r[0] + r[1] if r else None

def hash_bits(msg, L):
    h = hashlib.sha256(msg.encode()).digest()
    return [(h[i // 8] >> (i % 8)) & 1 for i in range(L)]

def keygen(k, L):
    sk, pk = [], []
    lo, hi = 1 << (k - 1), 1 << k
    for i in range(L):
        for b in (0, 1):
            while True:
                a = random.randint(lo, hi - 1)
                bb = random.randint(lo, hi - 1)
                if a == bb:
                    continue
                r = first_meeting(a, bb)
                if r:
                    s, t, z = r
                    break
            sk.append(((a, bb, s, t), (i, b)))
            pk.append(((abs(a - bb), s + t), (i, b)))
    return sk, pk

def forge_measure(pk, msg, L, k, cap_per_pair=200000, time_budget=900.0):
    e = hash_bits(msg, L)
    lo, hi = 1 << (k - 1), 1 << k
    sig_fake = []
    per_bit = []
    total_tries = 0
    t0 = time.time()
    for i in range(L):
        for ((m, n), (idx, bit)) in pk:
            if idx == i and bit == e[i]:
                break
        tries = 0
        hit = False
        while tries < cap_per_pair:
            if time.time() - t0 > time_budget:
                return None, total_tries, per_bit, time.time() - t0
            a = random.randint(lo, hi - 1)
            for b in (a + m, a - m):
                if not (lo <= b < hi):
                    continue
                tries += 1
                total_tries += 1
                if d_shortest(a, b) == n:
                    sig_fake.append((a, b))
                    hit = True
                    break
            if hit:
                break
        if not hit:
            return None, total_tries, per_bit, time.time() - t0
        per_bit.append(tries)
    return sig_fake, total_tries, per_bit, time.time() - t0

print(f"=== round9b: L 扩展重复统计 (k={K}, {REP} 次独立重复) ===")
print(f"{'L':>4} | {'各次总成本':>32} | {'均值':>8} | {'标准差':>7} | {'相对sd':>7} | 每位均值")
summary = []
for L in (4, 16, 64, 256):
    totals = []
    per_bit_all = []
    t0 = time.time()
    for rep in range(REP):
        random.seed(20260913 + 1000 * rep + L)
        sk, pk = keygen(K, L)
        msg = f"attack-run {rep} targeting L={L}"
        sig, total, per_bit, dt = forge_measure(pk, msg, L, K)
        if sig is None:
            print(f"L={L} rep{rep} 超预算, total={total}")
            totals.append(total)
        else:
            totals.append(total)
            per_bit_all.append(sum(per_bit) / len(per_bit))
    mean = sum(totals) / len(totals)
    var = sum((x - mean) ** 2 for x in totals) / (len(totals) - 1)
    sd = var ** 0.5
    per_mean = sum(per_bit_all) / len(per_bit_all) if per_bit_all else 0
    rel = sd / mean
    lst = "/".join(str(t) for t in totals)
    print(f"{L:>4} | {lst:>32} | {mean:>8.0f} | {sd:>7.0f} | {rel:>6.0%} | {per_mean:.0f}")
    summary.append((L, mean, sd, per_mean))

print()
print("跨 L 线性度（均值口径）: ")
for L, mean, sd, per_mean in summary:
    print(f"  L={L:>4}: 总成本均值 {mean:>9.0f}, 每位均值 {per_mean:>7.0f}")
print()
print("结论模板: 若「每位均值」跨 L 大致稳定（个位到千位量级）则支持期望线性;")
print("          单次运行的相对 sd 量化了评审担心的波动。")
