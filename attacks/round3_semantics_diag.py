"""
round3_semantics_diag.py — 「验证者自算最短距离」语义下的诊断

验证语义: 签名揭示 (a,b); 验证者自己算 d(a,b) = 首次相遇总步数 (最短),
          检查 d(a,b)==n 且 |a-b|==m。cyclekill 绕圈无效。

诊断问题:
  1. k=64 扫描秒破 (历史数据), k=128/256 扫 20 万候选未破 —— 机制?
  2. 扫描候选的 d 值分布 vs 公钥 n: 重叠? 错位 (全 < n 或全 > n)?
  3. 如果错位, 攻击者可调整扫描区间; 如果重叠却不命中, 需要换攻击。
"""
import random
import time
import statistics

random.seed(20260908)


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


def keygen(k, max_steps=20000):
    while True:
        a = random.randint(1 << (k - 1), (1 << k) - 1)
        b = random.randint(1 << (k - 1), (1 << k) - 1)
        if a == b:
            continue
        r = first_meeting_total(a, b, max_steps)
        if r is not None:
            return a, b, r


def diagnose(k, cap=50000, max_steps=8000, time_budget=60.0):
    a0, b0, n = keygen(k)
    m = abs(a0 - b0)
    print(f"\nk={k}: 诚实密钥 n={n}, m 位长={m.bit_length()}, a0位长={a0.bit_length()}")
    vals = []
    hits = 0
    long_ = 0
    t0 = time.time()
    for a in range(1, cap + 1):
        if time.time() - t0 > time_budget:
            print(f"  [时间到, 扫了 {a} 候选]")
            break
        for sign in (1, -1):
            b = a + sign * m
            if b <= 0:
                continue
            d = first_meeting_total(a, b, max_steps)
            if d is None:
                long_ += 1
                continue
            vals.append(d)
            if d == n:
                hits += 1
                print(f"  命中! a'={a}, b'=a'±m, d={d} == n")
                return
    if vals:
        below = sum(1 for d in vals if d < n)
        above = sum(1 for d in vals if d > n)
        print(f"  扫描 {len(vals)} 候选: d 值 min={min(vals)}, 中位={statistics.median(vals):.0f}, "
              f"max={max(vals)}")
        print(f"  与 n={n} 的关系: d<n 有 {below} ({below/len(vals)*100:.1f}%), "
              f"d>n 有 {above} ({above/len(vals)*100:.1f}%), 未汇合 {long_}")
        # 直方图: n 附近 ±500 的分布
        near = sum(1 for d in vals if abs(d - n) <= 100)
        print(f"  |d-n|<=100 的候选: {near} ({near/len(vals)*100:.3f}%)")
    print(f"  结果: {'攻破' if hits else '未破'} ({time.time()-t0:.0f}s)")


for k in (64, 128, 256):
    diagnose(k)
