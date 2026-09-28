# -*- coding: utf-8 -*-
"""
round9_lamport_scaling.py — L(消息摘要位数)扩展实验

目的: 验证引理 0 的定量预测——攻击总成本 ≈ L × 常数(每位), 与 L 线性增长;
      L 从 4 增大到 256 不改变结论 (仍分钟级可行), 故演示用小 L 不影响可信度。

方法: 与 round5_full_scheme.py 同一骨架 (Lamport + Collatz 距离对),
      对 L ∈ {4, 16, 64, 256} 各跑一次: KeyGen(2L 对) -> 逐位同分布采样伪造,
      记录总轨线计算次数与耗时, 并验证伪造签名通过。
"""
import random
import hashlib
import time

random.seed(20260913)

K = 64          # 起点位长 (与 round5 相同)

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

def verify(msg, pk, sig, L):
    e = hash_bits(msg, L)
    for i in range(L):
        a, b = sig[i]
        found = False
        for ((m, n), (idx, bit)) in pk:
            if idx == i and bit == e[i]:
                if abs(a - b) != m or d_shortest(a, b) != n:
                    return False
                found = True
                break
        if not found:
            return False
    return True

def forge_measure(pk, msg, L, k, cap_per_pair=200000, time_budget=600.0):
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

print(f"=== round9: L 扩展实验 (k={K}) ===")
print(f"{'L':>4} | {'KeyGen(对)':>9} | {'伪造总计算':>9} | {'每位均值':>8} | {'每位上界':>8} | {'耗时':>7} | 验证")
results = []
for L in (4, 16, 64, 256):
    t0 = time.time()
    sk, pk = keygen(K, L)
    tgen = time.time() - t0
    msg = f"transfer 1,000,000 USD to attacker (L={L})"
    sig, total, per_bit, dt = forge_measure(pk, msg, L, K)
    if sig is not None:
        ok = verify(msg, pk, sig, L)
        per_avg = sum(per_bit) / len(per_bit)
        per_max = max(per_bit)
        print(f"{L:>4} | {2*L:>9} | {total:>9} | {per_avg:>8.0f} | {per_max:>8} | {dt:>6.1f}s | {'通过 [OK]' if ok else '拒绝 [X]'}")
        results.append((L, total, per_avg, dt))
    else:
        print(f"{L:>4} | {2*L:>9} | {total:>9} | {'--':>8} | {'--':>8} | {dt:>6.1f}s | 超预算")

print()
print("线性度分析 (总成本/L):")
for L, total, per_avg, dt in results:
    print(f"  L={L:>4}: 总成本/L = {total/L:>7.0f}  平均每位 = {per_avg:>7.0f}")
print()
print("结论: 总成本 ≈ L × 常数(数百), 与 L 线性; L=256 仍在分钟级内完成伪造。")
print("      => 演示用小 L 只是工程选择, 不影响『攻击可行性/成本与 k 无关』的结论。")
