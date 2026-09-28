"""
round8_trunc4.py — 「4 截断 Collatz」变体检验

修改: 轨线到达 4 即停止 (值永不 < 4, 永不进入 1-2-4 震荡)。
      T4(x) = x/2 (x 偶), 3x+1 (x 奇), x > 4; 到 4 终止。
公钥: (m, n) = (|a-b|, d4(a,b)), d4 = 截断轨线的首次相遇距离。

检验:
  1. 诚实 keygen (截断版) 是否可行? z 分布?
  2. 同分布采样攻击 (匹配 d4 == n) 是否依然有效?
  3. cyclekill 原版 (绕圈) 是否失效? 是否出现新的步数调整机制?
"""
import random
import time

random.seed(20260918)

def trunc_orbit(x, max_steps=100000):
    """x 的截断轨线: 到 4 停止。返回 [(值, 深度)] 与终点"""
    seq = []
    d = 0
    while x != 4 and d < max_steps:
        seq.append((x, d))
        x = x // 2 if x % 2 == 0 else 3 * x + 1
        d += 1
    seq.append((4, d))   # 4 也在轨线上 (深度 d)
    return seq

def d4(a, b):
    """截断轨线首次相遇距离: min over 公共点 (ia + ib)"""
    la = trunc_orbit(a)
    lb = trunc_orbit(b)
    # dict: b 的值 -> 深度
    db_ = {v: i for v, i in lb}
    best = None
    for v, i in la:
        if v in db_:
            tot = i + db_[v]
            if best is None or tot < best:
                best = tot
    return best   # 4 必是公共点 -> 非 None

k = 64
lo, hi = 1 << (k - 1), 1 << k

# ---- 1. 诚实 keygen + z 分布 ----
print("=== 1. 诚实密钥 (截断版) ===")
zs, ns = [], []
t0 = time.time()
for _ in range(10):
    while True:
        a = random.randint(lo, hi - 1)
        b = random.randint(lo, hi - 1)
        n = d4(a, b)
        if n is not None: break
    # 找汇合点 z (首次相遇点)
    la = trunc_orbit(a); lb_ = {v: i for v, i in trunc_orbit(b)}
    best = None
    for v, i in la:
        if v in lb_:
            tot = i + lb_[v]
            if best is None or tot < best:
                best, z = tot, v
    zs.append(z); ns.append(n)
bl = sorted(z.bit_length() for z in zs)
print(f"  keygen 可行 [OK] ({time.time()-t0:.1f}s)")
print(f"  汇合点 z 位长: min={min(bl)}, 中位={bl[len(bl)//2]}, max={max(bl)}")
print(f"  含 1/2/4? {sum(1 for z in zs if z in (1,2,4))}/10  <- 截断后汇合点不会落在震荡段")
print(f"  d4 范围: {min(ns)}~{max(ns)}")

# ---- 2. 同分布采样攻击 ----
print("\n=== 2. 同分布采样攻击 (匹配 d4 == n) ===")
for trial in range(3):
    while True:
        a0 = random.randint(lo, hi - 1)
        b0 = random.randint(lo, hi - 1)
        n = d4(a0, b0)
        if n is not None: break
    m = abs(a0 - b0)
    t0 = time.time(); tries = 0; hit = None
    while tries < 200000:
        a_p = random.randint(lo, hi - 1)
        for b_p in (a_p + m, a_p - m):
            if lo <= b_p < hi:
                tries += 1
                if d4(a_p, b_p) == n:
                    hit = (a_p, b_p); break
        if hit: break
    if hit:
        a_p, b_p = hit
        assert abs(a_p - b_p) == m and d4(a_p, b_p) == n
        print(f"  实例{trial}: 攻破! {tries} 次采样 ({time.time()-t0:.1f}s)  断言通过")
    else:
        print(f"  实例{trial}: 未破 (20万次)")
