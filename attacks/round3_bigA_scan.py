"""
round3_bigA_scan.py — 同分布采样攻击 (正确的攻击姿势)

验证语义: 验证者自算 d(a,b) (最短首次相遇), 检查 d==n, |a-b|==m。
攻击:     随机采样 a' ~ U[2^{k-1}, 2^k) (与诚实密钥同分布), b' = a'±m,
          算 d(a',b'), 匹配 d==n。
问题:     命中所需采样数随 k 如何增长?
          - 多项式 (~k^2): 方案死 (攻击成本 = 采样数 × 每候选 k 步)
          - 指数: 方案活 (第一个存活的 Collatz 假设)
"""
import random
import time

random.seed(20260909)


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


def first_meeting_total(a, b, max_steps):
    va = {a: 0}
    vb = {b: 0}
    ca, cb = a, b
    for total in range(1, max_steps + 1):
        ca = T(ca)
        if ca in vb:
            return total + vb[ca]
        va[ca] = total
        cb = T(cb)
        if cb in va:
            return va[cb] + total
        vb[cb] = total
    return None


def keygen(k, max_steps=30000):
    while True:
        a = random.randint(1 << (k - 1), (1 << k) - 1)
        b = random.randint(1 << (k - 1), (1 << k) - 1)
        if a == b:
            continue
        r = first_meeting_total(a, b, max_steps)
        if r is not None:
            return a, b, r


def attack(k, cap=300000, time_budget=150.0):
    a0, b0, n = keygen(k)
    m = abs(a0 - b0)
    lo, hi = 1 << (k - 1), 1 << k
    t0 = time.time()
    tries = 0
    while tries < cap:
        if time.time() - t0 > time_budget:
            return None, tries, n, m.bit_length(), time.time() - t0
        a = random.randint(lo, hi - 1)
        for b in (a + m, a - m):
            if not (lo <= b < hi):
                continue
            tries += 1
            d = first_meeting_total(a, b, 30000)
            if d == n:
                return (a, b), tries, n, m.bit_length(), time.time() - t0
    return None, tries, n, m.bit_length(), time.time() - t0


for k in (64, 128, 256):
    results = []
    for trial in range(3):
        hit, tries, n, mbits, dt = attack(k)
        if hit:
            a, b = hit
            print(f"k={k} t={trial}: 攻破! n={n} | {tries} 次采样, {dt:.0f}s")
            results.append(tries)
        else:
            print(f"k={k} t={trial}: 未破 (cap {tries}, {dt:.0f}s, n={n})")
            results.append(None)
    print(f"k={k}: 命中采样数 {results}")
