"""
round2_noz_cyclekill.py — 正确攻击模型下的无 z 公钥检验

修正 round2_noz_scan 的模型错误:
  验证者只能检查 s+t == n 且 T^s(a)=T^t(b), 无法检查最短性。
  因此通用攻击 = cyclekill (4-2-1 循环绕圈凑步数), 而非最短匹配。

keygen: 无延迟, a,b 为 k 位随机, n = 首次汇合总步数 (诚实者语义, 最有利设定)。
攻击:   扫小 a' (b'=a'+m), 用循环点 {1,2,4} 的深度同余凑 s'+t'=n。
"""
import random
import time

random.seed(20260907)


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


def first_meeting(a, b, max_steps):
    """返回 (s, t, z) 首次汇合"""
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


def keygen_nodelay(k, max_steps=20000):
    while True:
        a = random.randint(1 << (k - 1), (1 << k) - 1)
        b = random.randint(1 << (k - 1), (1 << (k)) - 1)
        if a == b:
            continue
        r = first_meeting(a, b, max_steps)
        if r:
            s, t, z = r
            return a, b, s + t, z


def depth_to_first(x, target_set, limit=100000):
    d = 0
    while x not in target_set and d < limit:
        x = T(x)
        d += 1
    return d if x in target_set else None


def cycle_forge(m, n, a_max=20000, k=0):
    """对公钥 (m,n) 构造替代密钥: a' 小, b'=a'+m, z ∈ {1,2,4} 凑步数"""
    lo = 1 << (k - 1) if k else 0
    for a in range(1, a_max + 1):
        b = a + m
        if k and b >= (1 << k):
            break
        # a 与 b 各自首次到达 {1,2,4} 循环的深度
        for z in (4, 2, 1):
            x, da_z = a, 0
            while x != z and da_z < 5000:
                x = T(x)
                da_z += 1
            if x != z:
                continue
            x, db_z = b, 0
            while x != z and db_z < 200000:
                x = T(x)
                db_z += 1
            if x != z:
                continue
            rem = n - da_z - db_z
            if rem >= 0 and rem % 3 == 0:
                t_ = db_z + rem
                # 验证 s+t: s = da_z, t = t_ -> s+t = da_z + db_z + rem = n [OK]
                # T^{da_z}(a)=z, T^{t_}(b)=z [OK] (t_ ≡ db_z mod 3)
                return (a, b, da_z, t_, z)
    return None


def T_n(x, d):
    for _ in range(d):
        x = T(x)
    return x


for k in (128, 256):
    for trial in range(4):
        a0, b0, n, z0 = keygen_nodelay(k)
        m = abs(a0 - b0)
        t0 = time.time()
        f = cycle_forge(m, n, a_max=20000, k=k)
        dt = time.time() - t0
        if f:
            a, b, s, t, z = f
            # 完整语义验证 (与验证者一致)
            assert abs(a - b) == m and s + t == n
            assert T_n(a, s) == z and T_n(b, t) == z
            print(f"k={k} t={trial}: 攻破! n={n}, m位长={m.bit_length()}, "
                  f"a'={a} (位长{a.bit_length()}), z'={z}, {dt:.1f}s")
        else:
            print(f"k={k} t={trial}: 未破 (20000 候选, {dt:.1f}s, n={n}, m位长={m.bit_length()})")
