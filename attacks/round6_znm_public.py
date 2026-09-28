"""
round6_znm_public.py — 公钥 = (z, m, n) 全公开的攻击检验

设定: 诚实者随机 k 位 a、b, 正向首次相遇得 (s,t,z); 公钥 (z, m=|a-b|, n=s+t)。
验证语义: 揭示 (a,b,s,t) -> 检查 C^s(a)==z, C^t(b)==z, |a-b|==m, s+t==n
         (验证者也可自算; 先测伪造密钥存在性 — 找到任何合法 (a',b',s',t') 即破)

攻击 A: 2 链扫描 — a' = 2^{s'}·z 恒在 z 的反向树上 (C^{s'}(2^{s'}z)=z),
        b' = a' ± m, 正向走 n-s' 步看是否到 z。扫 s' = 0..n。
攻击 B: 随机反向路径 — 从 z 反向随机走 s' 步得 a' (随机混合 2y/(y-1)/3 分支),
        b' = a' ± m, 正向验证 C^{n-s'}(b')==z。采样 N 次。
"""
import random
import time

random.seed(20260914)

def T(x): return x // 2 if x % 2 == 0 else 3 * x + 1

def first_meeting(a, b, max_steps=30000):
    va = {a: 0}; vb = {b: 0}; ca, cb = a, b
    for tot in range(1, max_steps + 1):
        ca = T(ca)
        if ca in vb: return (tot, vb[ca], ca)
        va[ca] = tot
        cb = T(cb)
        if cb in va: return (va[cb], tot, cb)
        vb[cb] = tot
    return None

def keygen(k):
    while True:
        a = random.randint(1 << (k - 1), (1 << k) - 1)
        b = random.randint(1 << (k - 1), (1 << k) - 1)
        if a == b: continue
        r = first_meeting(a, b)
        if r:
            s, t, z = r
            return a, b, s, t, z

def Tn(x, d):
    for _ in range(d):
        x = T(x)
    return x

def preds(y):
    ps = [2 * y]
    if y % 6 == 4:
        ps.append((y - 1) // 3)
    return ps

def attack_A(z, m, n):
    """2 链扫描: a' = 2^{s'} z, b' = a' ± m"""
    for s_p in range(0, n + 1):
        a_p = z << s_p
        for sign in (1, -1):
            b_p = a_p + sign * m
            if b_p <= 0: continue
            if Tn(b_p, n - s_p) == z:
                return (a_p, b_p, s_p, n - s_p)
    return None

def attack_B(z, m, n, N=20000, time_budget=90.0):
    """随机反向路径采样: 从 z 反向随机走 s' 步得 a', b' = a' ± m"""
    t0 = time.time()
    for _ in range(N):
        s_p = random.randint(0, n)
        x = z
        for _ in range(s_p):
            x = random.choice(preds(x))
        a_p = x
        for sign in (1, -1):
            b_p = a_p + sign * m
            if b_p <= 0: continue
            if Tn(b_p, n - s_p) == z:
                return (a_p, b_p, s_p, n - s_p)
        if time.time() - t0 > time_budget:
            return None
    return None

k = 64
for trial in range(4):
    a0, b0, s0, t0, z0 = keygen(k)
    m, n = abs(a0 - b0), s0 + t0
    print(f"\n=== 实例 {trial}: z={z0} (位长{z0.bit_length()}), m位长={m.bit_length()}, n={n} ===")
    t = time.time()
    rA = attack_A(z0, m, n)
    print(f"[攻击A 2链扫描] {'攻破! ' + str(rA[:2])[:80] + '...' if rA else '未破'} ({time.time()-t:.1f}s)")
    t = time.time()
    rB = attack_B(z0, m, n)
    print(f"[攻击B 随机反向] {'攻破! ' + str(rB[:2])[:80] + '...' if rB else '未破 (2万次采样)'} ({time.time()-t:.1f}s)")
    if rA:
        a, b, s, t = rA
        assert abs(a - b) == m and s + t == n and Tn(a, s) == z0 and Tn(b, t) == z0
        print("  验证断言全部通过")
    elif rB:
        a, b, s, t = rB
        assert abs(a - b) == m and s + t == n and Tn(a, s) == z0 and Tn(b, t) == z0
        print("  验证断言全部通过")
