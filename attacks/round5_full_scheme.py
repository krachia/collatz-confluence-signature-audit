"""
round5_full_scheme.py — Collatz-OTS 完整方案: 诚实流程 vs 公钥-only 伪造

方案: 见文件头注释 (Lamport 骨架 + Collatz 距离对)。
验证语义: 验证者自算最短首次相遇距离 (不信任声称步数)。

演示:
  1. KeyGen 生成 2L 个 (m,n) 对
  2. 诚实者签 msg0 -> 验证通过
  3. 攻击者只用公钥, 对 msg1 伪造签名 -> 验证通过? (预期: 通过)
"""
import random
import hashlib
import time

random.seed(20260913)

K = 64          # 起点位长 (演示用小参数, 结论与 256 相同)
L = 4           # 消息摘要位数 (演示)

def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1

def first_meeting(a, b, max_steps=30000):
    """返回 (s, t, z): 首次相遇"""
    va = {a: 0}
    vb = {b: 0}
    ca, cb = a, b
    for total in range(1, max_steps + 1):
        ca = T(ca)
        if ca in vb:
            return (total, vb[ca], ca)
        va[ca] = total
        cb = T(cb)
        if cb in va:
            return (va[cb], total, cb)
        vb[cb] = total
    return None

def d_shortest(a, b, max_steps=30000):
    r = first_meeting(a, b, max_steps)
    return r[0] + r[1] if r else None

def hash_bits(msg, L):
    h = hashlib.sha256(msg.encode()).digest()
    return [(h[i // 8] >> (i % 8)) & 1 for i in range(L)]

# ---------------- KeyGen ----------------
def keygen(k=K, L=L):
    sk, pk = [], []
    lo, hi = 1 << (k - 1), 1 << k
    for i in range(L):
        for b in (0, 1):
            while True:
                a = random.randint(lo, hi - 1)
                bb = random.randint(lo, hi - 1)
                if a == bb:
                    continue
                r = first_meeting(a, bb)
                if r:
                    s, t, z = r
                    break
            sk.append(((a, bb, s, t), (i, b)))
            pk.append(((abs(a - bb), s + t), (i, b)))
    return sk, pk

# ---------------- Sign / Verify ----------------
def sign(msg, sk, L=L):
    e = hash_bits(msg, L)
    sig = []
    for i in range(L):
        for (key, (idx, bit)) in sk:
            if idx == i and bit == e[i]:
                a, b, s, t = key
                sig.append((a, b))
                break
    return sig

def verify(msg, pk, sig, L=L):
    e = hash_bits(msg, L)
    for i in range(L):
        a, b = sig[i]
        found = False
        for ((m, n), (idx, bit)) in pk:
            if idx == i and bit == e[i]:
                if abs(a - b) != m:
                    return False
                if d_shortest(a, b) != n:
                    return False
                found = True
                break
        if not found:
            return False
    return True

# ---------------- 攻击者: 只用公钥 ----------------
def forge(msg, pk, k=K, cap_per_pair=30000, time_budget=120.0):
    e = hash_bits(msg, L)
    lo, hi = 1 << (k - 1), 1 << k
    sig_fake = []
    total_tries = 0
    t0 = time.time()
    for i in range(L):
        # 找到被挑战的公钥对 (m, n)
        for ((m, n), (idx, bit)) in pk:
            if idx == i and bit == e[i]:
                break
        # 同分布采样攻击: 找替代 (a', b')
        tries = 0
        while True:
            if time.time() - t0 > time_budget:
                return None, total_tries
            a = random.randint(lo, hi - 1)
            for b in (a + m, a - m):
                if not (lo <= b < hi):
                    continue
                tries += 1
                total_tries += 1
                if d_shortest(a, b) == n:
                    sig_fake.append((a, b))
                    break
            else:
                continue
            break
        if tries > cap_per_pair:
            return None, total_tries
    return sig_fake, total_tries

# ---------------- 演示 ----------------
print(f"参数: k={K}, L={L}")
t0 = time.time()
sk, pk = keygen()
print(f"[KeyGen] 生成 {2*L} 个 (m,n) 公钥对 ({time.time()-t0:.1f}s)")
print(f"         例: pk[0] = (m={pk[0][0][0]}, n={pk[0][0][1]})")
print(f"         例: pk[1] = (m={pk[1][0][0]}, n={pk[1][0][1]})")

msg0 = "hello, honest message"
sig0 = sign(msg0, sk)
print(f"\n[诚实者] 签 '{msg0}'")
print(f"         验证结果: {'通过 [OK]' if verify(msg0, pk, sig0) else '拒绝 [X]'}")

msg1 = "transfer 1,000,000 USD to attacker"
print(f"\n[攻击者] 目标消息 '{msg1}'")
print(f"         我只有公钥 pk ({2*L} 个 (m,n) 对), 不知道任何 (a,b,s,t)")
t0 = time.time()
sig_fake, tries = forge(msg1, pk)
dt = time.time() - t0
if sig_fake:
    ok = verify(msg1, pk, sig_fake)
    print(f"         伪造签名完成: {tries} 次轨线计算, {dt:.1f}s")
    print(f"         验证结果: {'通过 [OK] 伪造成功!' if ok else '拒绝'}")
    # 对照: 诚实者也没有签过 msg1
    print(f"         (诚实者从未签过 '{msg1}', 但攻击者的签名通过了验证)")
else:
    print(f"         伪造失败 (超预算, {tries} 次计算)")
