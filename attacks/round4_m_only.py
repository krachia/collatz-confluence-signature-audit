"""
round4_m_only.py — 公钥只有 m 时的安全性演示

设定: 公钥 = m (只有差值), n 不公开 (签名时才由签名者给出)。
验证: 签名 (a,b,n_claimed) -> 检查 |a-b|==m 且 d(a,b)==n_claimed (自洽性)。

结论预告: 没有公开的 n 作对照, 验证者只能检查"自洽性",
         而自洽性任何攻击者都能自己制造 -> 攻击成本 = 1 次采样。
"""
import random

random.seed(20260911)


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


def d_shortest(a, b, max_steps=30000):
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


def verify_sig(a, b, n_claimed, m):
    """验证者: 只能检查这两个 (n_claimed 是签名者自己声称的)"""
    return abs(a - b) == m and d_shortest(a, b) == n_claimed


k = 256
a0, b0, n0 = keygen(k)
m = abs(a0 - b0)

print("=" * 72)
print(f"[密钥生成] 诚实私钥 (a0, b0), 秘密距离 n0 = {n0}")
print(f"[公钥发布] m = |a0-b0|  (只有 m! n 不在公钥里)")
print("=" * 72)

# 诚实者签名: 揭示 (a0, b0) 和自己算出的 n0
print("\n[诚实者] 签名 = (a0, b0, n0), 验证:", end=" ")
print("通过" if verify_sig(a0, b0, n0, m) else "拒绝")

# 攻击者: 只知道 m。他甚至不需要"算出 n" —— 自己造一对即可
print("\n[攻击者] 我只知道 m。攻击开始 (1 次采样):")
lo, hi = 1 << (k - 1), 1 << k
a_p = random.randint(lo, hi - 1)        # 随便选一个 a'
b_p = a_p + m if a_p + m < hi else a_p - m   # 用公开的 m 推出 b'
n_p = d_shortest(a_p, b_p)              # 自己算自己的距离 (公开算法!)
print(f"         选 a' = 随机数 (与 a0 无关)")
print(f"         由 m 得 b' = a' ± m")
print(f"         自算 n' = d(a', b') = {n_p}   <- 不需要知道诚实 n0 = {n0}")
print(f"         伪造签名 = (a', b', n'), 验证:", end=" ")
print("通过! 伪造成功" if verify_sig(a_p, b_p, n_p, m) else "拒绝")

print("\n[本质] 公钥没有 n 作对照物 -> 验证者只能检查'自洽性'")
print("       自洽性人人可造: 任何差值 m 的对 + 自己的距离声明都能通过。")
print(f"       诚实密钥相对攻击者没有任何秘密优势: 合法密钥数量 = 2^k 个,")
print(f"       攻击者随机选一个就是'合法持有者'。")
