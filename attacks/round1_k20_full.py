"""
round1_k20_full.py — H5 决定性实验: 旧 PPC 项目的实际参数 k=20 是否可被全枚举攻破

攻击设定(攻击者视角, 与协议漏洞无关):
  公钥 (m, n) 已知; 穷举 a in [1, 2^k), b = a±m,
  找零延迟汇合 (s', t') 满足 s'+t' == n 的替代密钥 (a', b').
  找到即完全伪造密钥 —— 这是对 H5 假设本身的检验.
"""
import random
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
            return (a, b, s, t, z)


def brute_force(m, n, k, max_steps=2000, time_budget=540.0):
    start = time.time()
    checked = 0
    for a in range(1, 1 << k):
        if time.time() - start > time_budget:
            return "timeout", checked, time.time() - start
        for sign in (1, -1):
            b = a + sign * m
            if b <= 0 or b >= (1 << k):
                continue
            checked += 1
            res = find_confluence_delayed(a, b, max_steps)
            if res:
                s, t, _ = res
                if s + t == n:
                    return (a, b, s, t), checked, time.time() - start
    return None, checked, time.time() - start


if __name__ == "__main__":
    a0, b0, s0, t0, z0 = keygen(20)
    m, n = abs(a0 - b0), s0 + t0
    print(f"真实密钥: a={a0}, b={b0}, s={s0}, t={t0}, z={z0}")
    print(f"公钥: m={m}, n={n}")
    print("开始全枚举攻击 (2^20 x 2 候选)...")
    res, checked, dt = brute_force(m, n, 20)
    print(f"检查 {checked} 个候选, 耗时 {dt:.1f}s")
    if res == "timeout":
        print("结果: 超时, k=20 未被本次攻击攻破")
    elif res:
        a, b, s, t = res
        print(f"结果: 攻破! 找到替代密钥 a={a}, b={b}, s={s}, t={t}")
        print(f"验证: s+t={s+t} == n={n} ? {s+t==n}, |a-b|={abs(a-b)} == m ? {abs(a-b)==m}")
    else:
        print("结果: 未找到 (该实例对零延迟枚举免疫)")
