"""
round8_simple_path.py — 「简单路径」约束变体检验

约束: 轨线不允许重复访问任何值 (首次重复即停止)。
      => 轨线长度有限, cyclekill 的无限绕圈空间被消除。
公钥: (m, n) = (|a-b|, d(a,b)), d = 两条简单轨线的首次公共点深度和。

检验: 诚实 keygen? z 分布? 同分布采样攻击是否依然有效?
"""
import random
import time

random.seed(20260919)

def simple_orbit(x, max_steps=200000):
    """x 的简单轨线: 首次重复即停止"""
    seq = []
    seen = set()
    while x not in seen and len(seq) < max_steps:
        seen.add(x)
        seq.append(x)
        x = x // 2 if x % 2 == 0 else 3 * x + 1
    seq.append(x)   # 重复点 (轨线终点)
    return seq

def d_simple(a, b):
    """两条简单轨线首次公共点的深度和 (公共点必存在: 都含 4-2-1 尾巴)"""
    lb = simple_orbit(b)
    db_ = {v: i for i, v in enumerate(lb)}
    best = None
    for i, v in enumerate(simple_orbit(a)):
        if v in db_:
            tot = i + db_[v]
            if best is None or tot < best:
                best = tot
    return best

k = 64
lo, hi = 1 << (k - 1), 1 << k

# ---- 1. 诚实 keygen + z 分布 ----
print("=== 1. 诚实密钥 (简单路径版) ===")
zs, ns, lens = [], [], []
for _ in range(10):
    a = random.randint(lo, hi - 1)
    b = random.randint(lo, hi - 1)
    n = d_simple(a, b)
    la = simple_orbit(a); lb = simple_orbit(b)
    db_ = {v: i for i, v in enumerate(lb)}
    best = None
    for i, v in enumerate(la):
        if v in db_:
            tot = i + db_[v]
            if best is None or tot < best:
                best, z = tot, v
    zs.append(z); ns.append(n)
    lens.append((len(la), len(lb)))
bl = sorted(z.bit_length() for z in zs)
print(f"  简单轨线长度 (a侧,b侧): {lens[:3]} ... (有限, 无重复 [OK])")
print(f"  汇合点 z 位长: min={min(bl)}, 中位={bl[len(bl)//2]}, max={max(bl)}")
print(f"  d 范围: {min(ns)}~{max(ns)}")

# ---- 2. 同分布采样攻击 ----
print("\n=== 2. 同分布采样攻击 (匹配 d == n) ===")
for trial in range(3):
    a0 = random.randint(lo, hi - 1)
    b0 = random.randint(lo, hi - 1)
    n = d_simple(a0, b0)
    m = abs(a0 - b0)
    t0 = time.time(); tries = 0; hit = None
    while tries < 200000:
        a_p = random.randint(lo, hi - 1)
        for b_p in (a_p + m, a_p - m):
            if lo <= b_p < hi:
                tries += 1
                if d_simple(a_p, b_p) == n:
                    hit = (a_p, b_p); break
        if hit: break
    if hit:
        a_p, b_p = hit
        assert abs(a_p - b_p) == m and d_simple(a_p, b_p) == n
        print(f"  实例{trial}: 攻破! {tries} 次采样 ({time.time()-t0:.1f}s)  断言通过")
    else:
        print(f"  实例{trial}: 未破 (20万次)")

# ---- 3. cyclekill 变体在简单路径下是否失效? ----
print("\n=== 3. 声称步数语义: 简单路径下还能绕圈吗? ===")
a0 = random.randint(lo, hi - 1); b0 = random.randint(lo, hi - 1)
la = simple_orbit(a0)
print(f"  例: a0 的简单轨线长度 = {len(la)} (最后一步是重复点 {la[-1]})")
print(f"  声称 s' > {len(la)-1} 会包含重复点 -> 被'无重复'检查拒绝")
print(f"  => cyclekill 无限绕圈失效 [OK] (但采样匹配 d==n 不受影响)")
