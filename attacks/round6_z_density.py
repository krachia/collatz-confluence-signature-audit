"""
round6_z_density.py — z 的反向树在 k 位随机数中的密度

设定: z 固定为网中一点, a 完全随机 (k 位)。
问题: 随机 a 的轨线经过 z 的概率 p(z) 是多少?
      p 大 -> 诚实者拒绝采样可行, 但攻击者同样可行 (对称性 -> 破)
      p 小 -> 诚实者自己都生成不了密钥 (方案不可行)

对照: 低空 z (诚实 keygen 实际产生的 z ~ 几十) vs 高空 z (2^60 级)
"""
import random
import time

random.seed(20260915)

def T(x): return x // 2 if x % 2 == 0 else 3 * x + 1

def passes_through(x, z, max_steps=30000):
    """x 的轨线在 max_steps 内是否经过 z"""
    for _ in range(max_steps):
        if x == z:
            return True
        x = T(x)
    return x == z

k = 64
lo, hi = 1 << (k - 1), 1 << k
N = 3000   # 每 z 测试的随机 a 数

print(f"k={k}: 随机 {N} 个 {k} 位 a, 测量轨线经过固定 z 的比例\n")
print(f"{'z':>12} {'z位长':>6} {'经过比例':>10} {'拒绝采样期望':>12}")
for z in (40, 16, 328, 1000, 1 << 20, (1 << 40) + 7, (1 << 60) + 13):
    hit = 0
    for _ in range(N):
        a = random.randint(lo, hi - 1)
        if passes_through(a, z):
            hit += 1
    p = hit / N
    exp_trials = 1 / p if p > 0 else float('inf')
    note = ""
    if z < 1000:
        note = "  <- 诚实 keygen 实际产生的 z 量级"
    elif z >= (1 << 40):
        note = "  <- 高空 z"
    print(f"{z:>12} {z.bit_length():>6} {p:>10.4%} {exp_trials:>12.0f}{note}")
