"""
round3_demo_attacker_view.py — 攻击者视角演示

场景: 验证者自算最短距离语义。
  - 诚实密钥 (a0, b0), 公钥 (m, n) = (|a0-b0|, d(a0,b0))
  - 攻击者只知道公钥 (m, n), 不知道 a0, b0
  - 攻击: 采样 a' ~ k位随机, b' = a'±m, 算 d(a',b'), 匹配 d==n
  - 验证者检查函数 verify(a,b): |a-b|==m 且 d(a,b)==n —— 对原始密钥和
    替代密钥一视同仁
"""
import random
import time

random.seed(20260910)


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


def d_shortest(a, b, max_steps=30000):
    """最短首次相遇距离 (验证者自己算的 d)"""
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


def keygen(k):
    while True:
        a = random.randint(1 << (k - 1), (1 << k) - 1)
        b = random.randint(1 << (k - 1), (1 << k) - 1)
        if a == b:
            continue
        n = d_shortest(a, b)
        if n is not None:
            return a, b, n


def verify(a, b, m, n):
    """验证者视角: 只查这两个关系"""
    return abs(a - b) == m and d_shortest(a, b) == n


k = 256
# ---- 诚实密钥生成 ----
a0, b0, n = keygen(k)
m = abs(a0 - b0)
print("=" * 72)
print(f"[密钥生成] 诚实私钥: a0={a0}")
print(f"           诚实私钥: b0={b0}")
print(f"[公钥发布] m = |a0-b0| = {m}")
print(f"           n = d(a0,b0) = {n}")
print(f"           (攻击者现在只知道 m 和 n, 不知道 a0, b0)")
print("=" * 72)

# ---- 攻击者: 只用 (m, n) ----
print("\n[攻击者] 我只有公钥 (m, n)。开始采样攻击...")
lo, hi = 1 << (k - 1), 1 << k
t0 = time.time()
tries = 0
found = None
while True:
    a = random.randint(lo, hi - 1)          # 随机猜一个 a'
    for b in (a + m, a - m):                 # m 公开 -> b' 被唯一确定
        if not (lo <= b < hi):
            continue
        tries += 1
        if d_shortest(a, b) == n:            # n 公开 -> 检查距离是否匹配
            found = (a, b)
            break
    if found:
        break
a_p, b_p = found
dt = time.time() - t0
print(f"[攻击者] 第 {tries} 次采样找到替代密钥 ({dt*1000:.0f} ms)!")
print(f"         替代 a' = {a_p}")
print(f"         替代 b' = {b_p}")
print(f"         (与诚实密钥完全不同: a'={'是' if a_p==a0 else '不是'} a0, "
      f"b'={'是' if b_p==b0 else '不是'} b0)")
print(f"         我全程只用了公钥里的 m 和 n, 从未见过 a0, b0")

# ---- 验证者视角 ----
print("\n[验证者] 检查两对密钥, 一视同仁:")
ok0 = verify(a0, b0, m, n)
okf = verify(a_p, b_p, m, n)
print(f"  诚实密钥 (a0, b0): |a-b|==m ? {abs(a0-b0)==m}, "
      f"d==n ? {d_shortest(a0,b0)==n} -> {'通过' if ok0 else '拒绝'}")
print(f"  替代密钥 (a', b'): |a-b|==m ? {abs(a_p-b_p)==m}, "
      f"d==n ? {d_shortest(a_p,b_p)==n} -> {'通过' if okf else '拒绝'}")
print(f"\n[结论] 验证者无法区分两者 -> 攻击者用伪造密钥签名的验证结果: "
      f"{'通过! 伪造成功' if okf else '失败'}")
