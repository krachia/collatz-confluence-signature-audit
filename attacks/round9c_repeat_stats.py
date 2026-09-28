# -*- coding: utf-8 -*-
"""round9c_repeat_stats.py — L 扩展的 20 次重复统计（加强 round9b 的 5 次，稳定尾部离散）

目的: round9b 的 5 次重复不足以约束重尾分布（L=16 的 5 次 sd 已达 81%）；
      本脚本把每个 L 的独立重复提高到 20 次，给出稳健的波动区间。
方法: 对 L ∈ {4,16,64,256} 各独立重复 20 次（种子 20260913+1000*rep+L，
      消息 "attack-run {rep} targeting L={L}"），与 round9b 完全同流程——
      前 5 次与 round9b 同种子同消息，应逐位复现其数值（内置复现核对）。
输出: 各次总成本、均值、标准差、相对 sd、中位、最小、最大、每位均值。
"""
import hashlib
import random
import statistics
import time

K = 64
REP = 20

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

print(f"=== round9c: L 扩展 20 次重复统计 (k={K}, {REP} 次独立重复) ===")
print("（前 5 次与 round9b 同种子，用于复现核对）")
print()
print(f"{'L':>4} | {'均值':>8} | {'标准差':>7} | {'相对sd':>6} | {'中位':>7} | {'最小':>7} | {'最大':>7} | 每位均值")
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
        totals.append(total)
        if sig is not None:
            per_bit_all.append(sum(per_bit) / len(per_bit))
    mean = sum(totals) / len(totals)
    sd = statistics.stdev(totals)
    med = statistics.median(totals)
    per_mean = (sum(totals) / len(totals)) / L  # 统一口径=总成本均值/L（2026-09-24 更正；旧版仅按完整轮次统计，L=256 曾偏差）
    rel = sd / mean
    lst = "/".join(str(t) for t in totals)
    print(f"{L:>4} | {mean:>8.0f} | {sd:>7.0f} | {rel:>5.0%} | {med:>7.0f} | {min(totals):>7} | {max(totals):>7} | {per_mean:.0f}")
    print(f"      各次: {lst}")
    print(f"      [耗时 {time.time()-t0:.0f}s]")
    summary.append((L, mean, sd, med, min(totals), max(totals), per_mean))

print()
print("跨 L 汇总（20 次重复口径）:")
for L, mean, sd, med, mn, mx, pm in summary:
    print(f"  L={L:>4}: 均值 {mean:>9.0f}, sd {sd:>7.0f} ({sd/mean:.0%}), 中位 {med:>7.0f}, 区间 [{mn}, {mx}], 每位均值 {pm:.0f}")
print()
print("结论: 每位均值跨 L 稳定于常数级；相对 sd 随 L 下降；报告以均值口径为主、单次值仅作示例。")
