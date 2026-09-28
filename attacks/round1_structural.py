"""
round1_structural.py — 第一轮攻击：结构性候选假设筛查

检验下列候选假设能否活过「平凡攻击」：
  H1  原始 Collatz 链单向性  (T(x) = x/2 if even else 3x+1)
  H2  压缩 Collatz 链单向性  (C(x) = (3x+1)/2^v2(3x+1), 奇数域)
  H3  奇偶位序列伪随机性    (parity vector 与均匀比特不可区分)
  H4  模 Collatz 投影的周期/伪随机性

每个假设：攻击 → 实测数据 → 判定 (存活/阵亡)
"""
import random
import statistics
import time

random.seed(20260904)

# ---------------------------------------------------------------- 工具
def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1

def v2(x):
    return (x & -x).bit_length() - 1

def C(x):
    """压缩 Collatz：奇数 -> 奇数"""
    assert x % 2 == 1
    y = 3 * x + 1
    return y >> v2(y)

def parity_bits(x, k):
    bits = []
    for _ in range(k):
        bits.append(x & 1)
        x = T(x)
    return bits

# ================================================================ H1
print("=" * 70)
print("H1  原始 Collatz 链单向性: 给定 y=T(x) 求 x 困难?")
print("=" * 70)
# 攻击: 任何 y 都有平凡 1 步前驱 2y, 因为 T(2y)=y
ok = all(T(2 * y) == y for y in [3, 5, 7, 9, 12345, 2 ** 200 + 1])
print(f"平凡攻击: T(2y) = y 恒成立?  {ok}")
print("=> 给定终点 y, 上游 1 步前驱 2y 无条件可得 (且 2^k·y 给出 k 步前驱)。")
print("判定: 阵亡。'给定终点求上游点' 在原始 T 上平凡, 无法支撑任何链式构造。")
print("      (附带: 偶数分支 x/2 也给出平凡下游压缩——结构完全透明)")

# ================================================================ H2
print()
print("=" * 70)
print("H2  压缩 Collatz 链单向性: 给定 y=C(x) 求奇数 x 困难?")
print("=" * 70)
N = 100000
success = 0
bounded_ok = 0
KB = 256
for _ in range(N):
    y = random.randrange(1, 1 << 256) | 1          # 奇数终点
    r = y % 3
    if r == 0:
        continue                                    # y≡0 mod 3: 无奇数前驱
    v = 2 if r == 1 else 1                          # 最小可行 v
    num = (1 << v) * y - 1
    assert num % 3 == 0
    x = num // 3
    assert x % 2 == 1
    assert C(x) == y, "逆推验证失败!"
    success += 1
    if x < (1 << KB):
        bounded_ok += 1
print(f"1 步逆推: 尝试 {N} 个随机奇数终点")
print(f"  存在奇数前驱且逆推成功: {success} ({success / N * 100:.1f}%)")
print(f"  其中前驱仍落在 2^{KB} 界内: {bounded_ok} ({bounded_ok / N * 100:.1f}%)")
print("=> 以 >= 2/3 概率, 给定公钥(链终点)可直接算出上游 1 层的合法点。")
print("   链式/WOTS 式签名中 '伪造消息 m-1' 只需 1 步逆推 -> 灾难性。")
print("判定: 阵亡。压缩消除了 2y 平凡前驱, 但 1 步逆推仍有条件地平凡可行。")
print("      若再加 '链点 <= 2^k' 界, 攻击成功率只是降到 ~50-60%, 仍不可接受。")

# ================================================================ H3
print()
print("=" * 70)
print("H3  奇偶位序列伪随机性: (parity of T^i(x))_{i<k} ≈ 均匀 k 比特?")
print("=" * 70)
LEN = 8
N = 200000
pats = [0] * (1 << LEN)
for _ in range(N):
    x = random.randrange(1, 1 << 128)
    bits = parity_bits(x, LEN)
    val = 0
    for b in bits:
        val = (val << 1) | b
    pats[val] += 1
# 相邻 11 是否出现
has11 = sum(c for v, c in enumerate(pats) if v & (v >> 1) & 0b01111111)
# 简化: 直接统计含 '11' 的模式
def contains11(v, l):
    for i in range(l - 1):
        if ((v >> i) & 3) == 3:
            return True
    return False
has11 = sum(c for v, c in enumerate(pats) if contains11(v, LEN))
exp_uniform = N / (1 << LEN)
# 均匀随机下含相邻 11 的比例 = 1 - F(LEN+2)/2^LEN  (F=Fibonacci)
from math import comb
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
no11_uniform = fib(LEN + 2) / (1 << LEN)
print(f"前 {LEN} 奇偶位中出现相邻 '11' 的样本: {has11} / {N}  ({has11 / N * 100:.3f}%)")
print(f"均匀随机序列中出现相邻 '11' 的期望:     {(1 - no11_uniform) * 100:.1f}%")
print("=> 奇数后必接偶数 (3x+1 为偶), 序列天然 '11-free', 与均匀的统计距离接近 1。")
print("判定: 阵亡。原始奇偶序列连 2 阶统计都过不了, 不能直接当 PRG;")
print("      任何后处理都需要额外假设, 回到无依据状态。")

# ================================================================ H4
print()
print("=" * 70)
print("H4  模 Collatz 投影的伪随机性 (整数轨迹 mod m 的循环结构)")
print("=" * 70)

def mod_cycle(x, mod, max_steps=100000):
    seen = {}
    cur = x % mod
    for i in range(max_steps):
        if cur in seen:
            return i - seen[cur], seen[cur]
        seen[cur] = i
        cur = T(cur) % mod
    return -1, -1

for mod in [2 ** 8, 2 ** 12, 2 ** 16, 2 ** 20]:
    trials = 200 if mod <= 2 ** 8 else (100 if mod <= 2 ** 12 else (40 if mod <= 2 ** 16 else 15))
    periods, pres = [], []
    t0 = time.time()
    for _ in range(trials):
        x = random.randrange(1, 1 << 40)
        p, pre = mod_cycle(x, mod)
        if p > 0:
            periods.append(p)
            pres.append(pre)
    if periods:
        print(f"mod 2^{v2(mod)}: {len(periods)}/{trials} 进入循环, "
              f"周期中位数 {statistics.median(periods)}, 最大 {max(periods)}, "
              f"前导中位数 {statistics.median(pres)}  ({time.time()-t0:.1f}s)")
    else:
        print(f"mod 2^{v2(mod)}: 无样本在限步内入循环 ({time.time()-t0:.1f}s)")
print("=> 若模投影周期很短, 序列可预测; 若周期随模指数增长, 则状态空间大但")
print("   仍未提供任何困难性论证。本数据仅作情报: 周期规模决定 H4 是否值得继续。")
print("判定: 待定(视数据)。即便周期长, 也只是 '无已知攻击', 非可证明对象。")
