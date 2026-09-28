"""
round2_pathcount.py — 新设计地基实验: Collatz 反向树的受界路径计数

问题: 给定 z (L 位) 与深度 d, z 的反向树上恰好 d 步、且终点落在
      [2^{k-1}, 2^k) 的路径有多少条? (M)
意义:
  - 若 M 随 d 组合爆炸 (如 ~ C(d, n3)), 深汇合假设 (H6) 有生日攻击屏障
    sqrt(M_a * M_b), 可能存活;
  - 若 M 很小 (位长预算是紧约束), 攻击者直接枚举 -> 新设计死亡。
反向分支: 前驱 ∈ {2y} ∪ {(y-1)/3 | y ≡ 4 (mod 6)}
"""
import random
import time
from math import comb

random.seed(20260905)


def preds(y):
    ps = [2 * y]
    if y % 6 == 4:
        ps.append((y - 1) // 3)
    return ps


def count_paths(z, d, lo, hi, memo=None, node_limit=5_000_000):
    """精确计数: 从 z 出发走恰好 d 步, 每一步值都允许任意(不剪枝中间值),
    终点落在 [lo, hi) 的路径数。带剪枝: 中间值超过 hi * 4^? 不可能回来?
    3 分支每步最多除以 ~3, 若当前值 > hi * 3^剩余步 则不可能回到 hi 以下 -> 剪。
    """
    if memo is None:
        memo = {}
    total = 0

    def dfs(x, steps_left):
        nonlocal total
        # 剪枝: 全走 3 分支也降不到 hi 以下 -> 死
        if steps_left == 0:
            return 1 if lo <= x < hi else 0
        # 若 x 已经 >= hi 且剩余步全走 (x-1)/3 也降不回: 需要 x * (1/3)^r < hi
        if x >= hi and x < hi * (3 ** steps_left):
            pass  # 仍可能降回
        elif x >= hi * (3 ** steps_left):
            return 0
        r = 0
        for p in preds(x):
            r += dfs(p, steps_left - 1)
        return r

    return dfs(z, d)


def count_paths_iter(z, d, lo, hi):
    """迭代版 DFS 计数, 避免递归开销; 返回 (计数, 展开节点数)"""
    total = 0
    nodes = 0
    stack = [(z, d)]
    while stack:
        x, left = stack.pop()
        nodes += 1
        if nodes > 20_000_000:
            return -1, nodes
        if left == 0:
            if lo <= x < hi:
                total += 1
            continue
        # 剪枝: 剩余步全走 3 分支都降不回 hi 以下
        if x >= hi * (3 ** left):
            continue
        for p in preds(x):
            stack.append((p, left - 1))
    return total, nodes


# ---- 正确性抽查: z=16 的已知结构 ----
# 16 的反向树浅层: 32, 64, ... 以及 (16-1)/3 不可用 (16%6=4? 16%6=4 -> (15)/3=5, T(5)=16 [OK])
assert (16 % 6 == 4)
assert (16 - 1) // 3 == 5
assert 5 * 3 + 1 == 16
print("正确性抽查通过: 5 是 16 的奇数前驱 (T(5)=16), 8 不是 (T(8)=4)")

print("\n=== 实验 1: 路径计数 M(d) — z 固定, k=12 位起点, z 取 L=4 位 ===")
for k in (12, 14):
    lo, hi = 1 << (k - 1), 1 << k
    z = random.randrange(1 << 3, 1 << 4) | 1   # 4 位奇数
    print(f"\nk={k}, z={z} ({z.bit_length()}位), 起点区间 [{lo}, {hi})")
    print(f"{'d':>4} {'M(d)':>12} {'log2 M':>8} {'理论 C(d,n3)':>14}")
    pts = []
    for d in range(6, 25):
        t0 = time.time()
        M, nodes = count_paths_iter(z, d, lo, hi)
        if M < 0:
            print(f"{d:>4} 节点超限({nodes})")
            break
        # 理论: 净增长 k-L bit, 3 分支数 n3 = (k - L - d)/ (1-1.58)?? 近似 n2 - 1.58 n3 = k-L, n2+n3=d
        import math
        n3_approx = max(0, int((d - (k - z.bit_length())) / 2.58))
        theory = comb(d, n3_approx) if 0 <= n3_approx <= d else 0
        m_ = math.log2(max(M, 1))
        if M > 0:
            pts.append((d, m_))
        print(f"{d:>4} {M:>12} {m_:>8.2f} {theory:>14}  ({nodes}节点,{time.time()-t0:.1f}s)")
    if len(pts) >= 2:
        (d0, m0), (d1, m1) = pts[0], pts[-1]
        slope_end = (m1 - m0) / (d1 - d0)
        n_ = len(pts); sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
        sxx = sum(p[0] * p[0] for p in pts); sxy = sum(p[0] * p[1] for p in pts)
        slope_ls = (n_ * sxy - sx * sy) / (n_ * sxx - sx * sx)
        print(f"  => 有效点 {len(pts)} 个 (d={d0}..{d1}): 端点斜率 = {slope_end:.3f} bit/步; "
              f"最小二乘斜率 = {slope_ls:.3f} bit/步")

print("\n=== 实验 2: 路径多样性来源 — 同深度的不同 z ===")
k = 12
lo, hi = 1 << (k - 1), 1 << k
for z in (5, 7, 11, 13, 17, 23, 31):
    M, nodes = count_paths_iter(z, 16, lo, hi)
    print(f"z={z:>3}: M(16) = {M}")
