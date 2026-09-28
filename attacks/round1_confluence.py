"""
round1_confluence.py — 第一轮攻击：汇合对假设筛查

H5  Collatz 汇合对困难性: 给定 (m=|a-b|, n=s+t) 求 (a,b,s,t) 使
     T^s(a) = T^t(b) = z 困难?   (旧 PPC 方案的核心假设)

实验:
  E1  真实密钥的汇合点 z 分布 —— z 是否常落在 4-2-1 低循环附近?
      (若 z 很小, 攻击者可从 z 反向; 若 z 巨大, 反向树不可行)
  E2  小参数全枚举攻击: 给定 (m,n), 穷举 a, b=a±m, 检查是否存在
      (s'+t'==n) 的汇合 —— 测量 k 增大时攻击成本/成功率的外推
  E3  延迟匹配问题复检: keygen 带随机延迟, 零延迟穷举的命中率
"""
import random
import statistics
import time

random.seed(20260904)


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


def find_confluence_delayed(a, b, max_steps, da=0, db=0):
    for _ in range(da):
        a = T(a)
    for _ in range(db):
        b = T(b)
    visited_a = {a: 0}
    visited_b = {b: 0}
    cur_a, cur_b = a, b
    for total in range(1, max_steps + 1):
        cur_a = T(cur_a)
        if cur_a in visited_b:
            return (da + total, db + visited_b[cur_a], cur_a)
        visited_a[cur_a] = total
        cur_b = T(cur_b)
        if cur_b in visited_a:
            return (da + visited_a[cur_b], db + total, cur_b)
        visited_b[cur_b] = total
    return None


def keygen(k, max_steps=2000):
    while True:
        a = random.randint(1, (1 << k) - 1)
        b = random.randint(1, (1 << k) - 1)
        if a == b:
            continue
        da = random.randint(0, 100)
        db = random.randint(0, 100)
        res = find_confluence_delayed(a, b, max_steps, da, db)
        if res:
            s, t, z = res
            return (a, b, s, t, z, da, db)


# ---------------------------------------------------------------- E1
print("=" * 70)
print("E1  真实密钥的汇合点 z 分布 (k=20, max_steps=2000, 与旧 PPC keygen 相同)")
print("=" * 70)
zs, ns, delays_used = [], [], 0
t0 = time.time()
N1 = 60
for i in range(N1):
    a, b, s, t, z, da, db = keygen(20)
    zs.append(z)
    ns.append(s + t)
    delays_used += (1 if da else 0) + (1 if db else 0)
    if i % 20 == 19:
        print(f"  ... {i+1}/{N1}  ({time.time()-t0:.0f}s)")
bl = [z.bit_length() for z in zs]
print(f"汇合点 z 的位长: 最小 {min(bl)}, 中位 {statistics.median(bl):.0f}, "
      f"最大 {max(bl)}")
low = sum(1 for z in zs if z <= 100)
print(f"z <= 100 (低循环附近, 便于反向): {low}/{N1} ({low/N1*100:.0f}%)")
print(f"n = s+t: 最小 {min(ns)}, 中位 {statistics.median(ns):.0f}, 最大 {max(ns)}")
print(f"使用非零延迟的密钥对: {delays_used}/{2*N1}")
print(f"耗时 {time.time()-t0:.0f}s")
print("=> 若 z 偏小/偏向 4-2-1 循环, 攻击者从 z 出发反向枚举前驱树即可;")
print("   若 z 普遍为大数, 反向树深度 s 不可行 -> H5 的这一攻击面暂闭。")

# ---------------------------------------------------------------- E2
print()
print("=" * 70)
print("E2  小参数全枚举攻击: 给定 (m,n), 找 a 使 b=a±m 且 s'+t'==n")
print("    测量: 成功率(攻击者视角) 与 单实例耗时")
print("=" * 70)

def brute_force(m, n, k, max_steps=2000, time_budget=25.0):
    start = time.time()
    for a in range(1, 1 << k):
        if time.time() - start > time_budget:
            return "timeout", time.time() - start
        for sign in (1, -1):
            b = a + sign * m
            if b <= 0 or b >= (1 << k):
                continue
            res = find_confluence_delayed(a, b, max_steps)
            if res:
                s, t, _ = res
                if s + t == n:
                    return (a, b), time.time() - start
    return None, time.time() - start

for k in [10, 12, 14]:
    succ = 0
    times = []
    timeouts = 0
    insts = 8 if k <= 12 else 5
    for _ in range(insts):
        a, b, s, t, z, da, db = keygen(k)
        m, n = abs(a - b), s + t
        found, dt = brute_force(m, n, k)
        times.append(dt)
        if found == "timeout":
            timeouts += 1
        elif found:
            succ += 1
    print(f"k={k}: {succ}/{insts} 实例被攻破 (找到合法替代密钥), "
          f"timeout {timeouts}, 平均耗时 {statistics.mean(times):.1f}s, "
          f"最大 {max(times):.1f}s")
print("=> 小 k 下攻击基本总能找到替代密钥; 关键是成功率随 k 的衰减速度。")

# ---------------------------------------------------------------- E3
print()
print("=" * 70)
print("E3  零延迟穷举 vs 真实密钥 (keygen 带随机延迟) —— 复检旧 attack_ppc 方法")
print("=" * 70)
found_e3 = 0
N3 = 40
for _ in range(N3):
    a, b, s, t, z, da, db = keygen(16)
    res = find_confluence_delayed(a, b, 2000)
    if res:
        s0, t0, _ = res
        if s0 + t0 == s + t:
            found_e3 += 1
print(f"真实密钥本身满足零延迟条件(s'+t'==n)的比例: {found_e3}/{N3}")
print("=> 若比例 << 1, 说明旧 attack_ppc 的攻击条件与真实密钥分布错配,")
print("   它的'未攻破'结论不能作为 H5 的任何证据。")
