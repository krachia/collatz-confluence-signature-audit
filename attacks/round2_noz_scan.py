"""
round2_noz_scan.py — 无 z 公钥 (m,n) 的终结检验 (k=128/256)

攻击: 给定公钥 (m, n), 扫描 a' = 1,2,3,..., 令 b' = a'+m (及 a'-m),
      计算最短汇合距离 d(a',b') (零延迟首次相遇 s'+t'),
      命中 d == n 即找到合法替代密钥 (a',b') -> 伪造成功。
这与验证者的视角一致: 验证者只查 |a'-b'|=m 与 s'+t'=n, 无法区分替代密钥。

若命中位置不随 k 增长 (几百~几万), 则攻击成本与安全参数无关 -> 假设层死亡。
"""
import random
import time

random.seed(20260906)


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


def first_meeting_total(a, b, max_steps):
    """最短汇合总步数 (两轨线首次相遇的 s+t), 无延迟"""
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


def keygen(k, max_steps=20000):
    """随机 a,b; n = 最短汇合总步数 (无延迟, 与验证语义一致)"""
    while True:
        a = random.randint(1 << (k - 1), (1 << k) - 1)
        b = random.randint(1 << (k - 1), (1 << k) - 1)
        if a == b:
            continue
        d = first_meeting_total(a, b, max_steps)
        if d is not None:
            return a, b, d


def scan_attack(m, n, k, cap=200000, max_steps=6000, time_budget=90.0):
    """扫 a' 从小开始; 返回 (是否命中, 检查数, 命中的 a', 耗时)"""
    t0 = time.time()
    checked = 0
    miss_long = 0
    for a in range(1, 1 << k):
        for sign in (1, -1):
            if time.time() - t0 > time_budget:
                return "timeout", checked, None, time.time() - t0, miss_long
            if checked >= cap:
                return "cap", checked, None, time.time() - t0, miss_long
            b = a + sign * m
            if b <= 0:
                continue
            checked += 1
            d = first_meeting_total(a, b, max_steps)
            if d is None:
                miss_long += 1
                continue
            if d == n:
                return (a, b), checked, a, time.time() - t0, miss_long
    return None, checked, None, time.time() - t0, miss_long


for k in (128, 256):
    for trial in range(3):
        a0, b0, n = keygen(k)
        m = abs(a0 - b0)
        res, checked, a_hit, dt, miss = scan_attack(m, n, k)
        if isinstance(res, tuple):
            a, b = res
            print(f"k={k} t={trial}: 攻破! m位长={m.bit_length()} n={n} | "
                  f"a'={a} (检查 {checked} 候选, {dt:.0f}s, 超时未汇合 {miss})")
            # 验证
            assert abs(a - b) == m
        else:
            print(f"k={k} t={trial}: {res} (检查 {checked}, {dt:.0f}s, 未汇合 {miss})")
