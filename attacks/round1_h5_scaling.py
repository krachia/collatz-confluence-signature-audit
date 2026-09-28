"""
round1_h5_scaling.py — H5 扩展实验: 早期枚举攻击在更大 k 下是否同样瞬间成功?

猜测: 小 a 的轨线很快停在 4-2-1 主干附近, b=a+m 的轨线并入主干时经过该点,
      s'+t' 的取值覆盖 n 的邻域 -> 命中只需几百~几千候选, 与 k 无关。
验证: k = {24, 28, 32, 40, 64}, 每 k 生成 3 个真实密钥,
      穷举 a 从 1 起但最多检查 CAP 个候选, 记录是否命中与命中位置。
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


def early_attack(m, n, cap=20000, max_steps=3000):
    """从 a=1 起检查, 最多 cap 个候选, 返回 (是否命中, 检查数, 命中的a)"""
    checked = 0
    for a in range(1, 1 << 40):
        for sign in (1, -1):
            b = a + sign * m
            if b <= 0:
                continue
            checked += 1
            if checked > cap:
                return False, checked, None
            res = find_confluence_delayed(a, b, max_steps)
            if res:
                s, t, _ = res
                if s + t == n:
                    return True, checked, a
    return False, checked, None


for k in [24, 28, 32, 40, 64]:
    for trial in range(3):
        a0, b0, s0, t0, z0 = keygen(k)
        m, n = abs(a0 - b0), s0 + t0
        t0_ = time.time()
        hit, checked, a_hit = early_attack(m, n)
        dt = time.time() - t0_
        status = f"命中! a={a_hit}" if hit else "未命中(达到cap)"
        print(f"k={k} trial={trial}: m 位长={m.bit_length()}, n={n}, z位长={z0.bit_length()} | "
              f"{status} (检查 {checked} 候选, {dt:.1f}s)")
