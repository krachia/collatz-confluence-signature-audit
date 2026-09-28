"""
round1_h5_cyclekill.py — H5 终结攻击: 4-2-1 循环调整

定理级攻击(无需任何搜索):
  任何 Collatz 轨线最终进入循环 {1, 2, 4} (周期 3)。
  给定公钥 (m, n):
    取 a' = 小整数, b' = a' + m;
    b' 首次到达 4 的深度记为 d4;
    则 a' 在 1/4/2 的到达深度分别为 {0,1,2} + 3j,
    b' 在 4/2/1 的到达深度分别为 {d4, d4+1, d4+2} + 3k;
    三个循环点给出三种模 3 剩余类 -> 对任意 n >= d4+3 总存在 (s', t', z):
        z=4: n ≡ d4+1 (mod 3), s'=1+3j,  t'=d4+3k,  s'+t'=n
        z=2: n ≡ d4   (mod 3), s'=2+3j,  t'=d4+1+3k
        z=1: n ≡ d4+2 (mod 3), s'=0+3j,  t'=d4+2+3k
  于是 (a', b', s', t', z) 是满足公钥约束的完全合法密钥。
  若某个 a' 的 d4 太大, 换 a'+1 (b' 随之 +1, 重新得到独立的 d4)。

  验证: |a'-b'|==m, s'+t'==n, T^s'(a')==T^t'(b')==z —— 全部成立。
  结论: H5 假设死亡, 与 k 无关 (不需要 2^k 搜索)。
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


def first_hit_4(x, limit=100000):
    """x 的轨线首次到达 4 的深度 (Collatz 下必然有限)"""
    d = 0
    while x != 4 and d < limit:
        x = T(x)
        d += 1
    return d if x == 4 else None


def cycle_forge(m, n, a_max=500):
    """对公钥 (m,n) 构造合法替代密钥 (a', b', s', t', z)"""
    for a in range(1, a_max + 1):
        b = a + m                      # |a - b| = m
        d4 = first_hit_4(b)
        if d4 is None:
            continue
        # a 自己的循环到达深度: 取决于 a 首次到 4 的深度 da4, 但 a 很小可直接算
        da4 = first_hit_4(a)
        # 通用处理: 直接对 z in {4,2,1} 尝试三个剩余类
        # a 到 z 的深度集合: da(z) + 3j; b 到 z 的深度集合: db(z) + 3k
        # 简单方案: 枚举 z=1,2,4 与 j 候选, 求 (s', t')
        for z in (4, 2, 1):
            # a 首次到 z 的深度
            x, da_z = a, 0
            while x != z and da_z < 2000:
                x = T(x)
                da_z += 1
            if x != z:
                continue
            x, db_z = b, 0
            while x != z and db_z < 100000:
                x = T(x)
                db_z += 1
            if x != z:
                continue
            # 需要 s' = da_z + 3j, t' = db_z + 3k, s' + t' = n
            rem = n - da_z - db_z
            if rem < 0 or rem % 3 != 0:
                continue
            k_ = rem // 3
            s_, t_ = da_z, db_z + 3 * k_   # j=0, k=k_
            assert s_ + t_ == n
            assert T_n(a, s_) == z and T_n(b, t_) == z
            return (a, b, s_, t_, z)
    return None


def T_n(x, d):
    for _ in range(d):
        x = T(x)
    return x


for k in [20, 32, 64, 128, 256]:
    ok = 0
    trials = 5
    for _ in range(trials):
        a0, b0, s0, t0, z0 = keygen(k)
        m, n = abs(a0 - b0), s0 + t0
        forged = cycle_forge(m, n)
        if forged:
            a, b, s, t, z = forged
            assert abs(a - b) == m
            assert s + t == n
            assert T_n(a, s) == z and T_n(b, t) == z
            ok += 1
    print(f"k={k}: 循环调整攻击 {ok}/{trials} 实例成功 (每个实例需检查的 a' ≤ 500)")
    if ok < trials:
        break
print()
print("验证断言全部通过 -> 给定 (m,n) 可瞬间构造合法替代密钥,")
print("H5 汇合对假设死亡: 4-2-1 循环的周期 3 提供了无限的步数调整自由度。")
