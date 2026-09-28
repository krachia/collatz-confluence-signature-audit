"""
estimate_min_entropy.py — 轨线距离 d 的熵估计 (§5.4 数据) — v2 补测 H2

对 k=64/128/256: 诚实 keygen 1 实例 -> (m, n), 然后同分布采样 (a', a'±m)
统计 d 值的经验分布, 直接估计三个口径:
  - 唯一值数 U（= 平均期望攻击成本的严格值：E_n*[1/p(n*)] = U）
  - min-entropy   Hinf = -log2(p_max)        （最坏实例上界）
  - Renyi-2       H2 = -log2(sum p^2)      （期望命中率 2^{-H2}，定理 4）
  - Shannon       H1 = -sum p log p        （分布形状）
偏差说明: 有限采样下 p_max_hat 倾向偏小于真 p_max => Hinf_hat 倾向偏大(乐观)。

v2 变更: 直接测量 H2（此前论文中的 H2 为 Hinf≤H2≤H1 插值估计, 现改为实测）。
"""
import random
import time
import math
from collections import Counter

random.seed(20260921)  # 与原版一致，保证数据可比

def T(x): return x // 2 if x % 2 == 0 else 3 * x + 1

def d_shortest(a, b, max_steps=50000):
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

print(f"{'k':>5} {'采样N':>7} {'唯一值U':>8} {'max频率':>9} {'Hinf':>7} "
      f"{'H2':>7} {'H1':>7} {'2^Hinf':>9} {'2^H2':>9} "
      f"{'N_valid(上界)':>14} {'N_valid(期望)':>14}")
results = []
for k, N in ((64, 50000), (128, 30000), (256, 20000)):
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
    nv_ub = 2 ** (k - 1 - Hinf)   # 上界口径（任何实例不超过）
    nv_exp = 2 ** (k - 1 - H2)    # 期望口径（对随机诚实实例）
    print(f"{k:>5} {total:>7} {U:>8} {pmax:>9.5f} {Hinf:>7.2f} "
          f"{H2:>7.2f} {H1:>7.2f} {2**Hinf:>9.1f} {2**H2:>9.1f} "
          f"{nv_ub:>14.2e} {nv_exp:>14.2e}   ({time.time()-t0:.0f}s)")
    print(f"      (n={n}, m位长={m.bit_length()}; 检验排序 Hinf≤H2≤H1: "
          f"{Hinf <= H2 <= H1})")
    results.append((k, U, Hinf, H2, H1))

print()
print("=== 攻击者成本口径对照（对随机诚实实例的平均） ===")
print(f"{'k':>5} {'U(严格平均E[1/p])':>18} {'平滑估计 2^H2':>14} {'下界 2^Hinf':>10}")
for k, U, Hinf, H2, H1 in results:
    print(f"{k:>5} {U:>18} {2**H2:>14.1f} {2**Hinf:>10.1f}")

print()
print("=== 与实测攻击成本对照（论文 §5.3 数据） ===")
print("k=64: 实测命中 276~6515 | k=128: 115~4071 | k=256: 122~605")
print("（实测为单个实例的 1/p(n*)；理论：实例间波动, 均值≈U, 下界≈2^Hinf）")
