"""
round7_sum_m.py — 公钥 (m, n) = (a+b, d(a,b)) 的完整实例

演示: 诚实密钥 -> 公钥 (和, 距离) -> 攻击者只用公钥采样伪造 -> 验证通过
"""
import random
import time

random.seed(20260916)

def T(x): return x // 2 if x % 2 == 0 else 3 * x + 1

def d_shortest(a, b, max_steps=30000):
    va = {a: 0}; vb = {b: 0}; ca, cb = a, b
    for tot in range(1, max_steps + 1):
        ca = T(ca)
        if ca in vb: return tot + vb[ca]
        va[ca] = tot
        cb = T(cb)
        if cb in va: return va[cb] + tot
        vb[cb] = tot
    return None

k = 64
lo, hi = 1 << (k - 1), 1 << k

# ---- 诚实密钥生成 ----
while True:
    a0 = random.randint(lo, hi - 1)
    b0 = random.randint(lo, hi - 1)
    n0 = d_shortest(a0, b0)
    if n0: break
m0 = a0 + b0   # 公钥 m = 和 (不是差!)

print("=" * 70)
print("[诚实密钥]")
print(f"  a0 = {a0}")
print(f"  b0 = {b0}")
print(f"[公钥] (m, n) = (a0+b0, d(a0,b0))")
print(f"  m  = {m0}   (位长 {m0.bit_length()})")
print(f"  n  = {n0}   (轨线最短汇合距离)")
print(f"  攻击者只知道 m 和 n, 不知道 a0, b0")
print("=" * 70)

# ---- 攻击: 采样 a', b' = m - a' (和给免费配对), 匹配 d == n ----
t0 = time.time()
tries = 0
while True:
    a_p = random.randint(lo, hi - 1)
    b_p = m0 - a_p
    if not (lo <= b_p < hi):
        continue          # b' 不在 k 位区间 -> 重采
    tries += 1
    if d_shortest(a_p, b_p) == n0:
        break
dt = time.time() - t0

print(f"\n[攻击者] 随机采样 a', 令 b' = m - a' (公开的 m 直接给出 b')")
print(f"  第 {tries} 次采样命中 ({dt*1000:.0f} ms)")
print(f"  替代 a' = {a_p}")
print(f"  替代 b' = {b_p}")
print(f"  a' 与 a0 相同? {a_p == a0}    b' 与 b0 相同? {b_p == b0}")

# ---- 验证者视角 ----
print(f"\n[验证者] 检查 (a', b'):")
ok1 = (a_p + b_p == m0)
print(f"  ① a' + b' == m ? {ok1}   (a'+b' = {a_p + b_p})")
ok2 = (d_shortest(a_p, b_p) == n0)
print(f"  ② d(a', b') == n ? {ok2}   (自算 = {d_shortest(a_p, b_p)})")
print(f"\n[结论] 伪造签名验证: {'通过! 伪造成功' if (ok1 and ok2) else '失败'}")
