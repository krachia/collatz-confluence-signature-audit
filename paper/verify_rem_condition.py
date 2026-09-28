# -*- coding: utf-8 -*-
"""
验证审稿意见 #4: cyclekill 的 rem>=0 漏洞 + 修正引理。
引理（修正版）: 对任意两起点 x, y (轨线到达循环), {tau_z(x)+tau_z(y) : z in {1,2,4}} 覆盖 mod 3 全部剩余类。
同时检验: S_min <= n-4 的实际满足率（真实密钥场景）。
"""
import random

def tau_cycle(n):
    """返回 (tau4, tau2, tau1): 到 4/2/1 的首次步数; None 若未在限步内到达。"""
    LIM = 100000
    x = n
    t = 0
    t4 = t2 = t1 = None
    while t < LIM:
        if x == 4 and t4 is None: t4 = t
        if x == 2 and t2 is None: t2 = t
        if x == 1 and t1 is None: t1 = t
        if t4 is not None and t2 is not None and t1 is not None:
            return (t4, t2, t1)
        x = x // 2 if x % 2 == 0 else 3 * x + 1
        t += 1
    return None

random.seed(42)
print("=== 测试1: 和覆盖引理 (随机对) ===")
fail = 0
N = 2000
for i in range(N):
    x = random.getrandbits(random.randint(8, 256))
    y = random.getrandbits(random.randint(8, 256))
    if x < 1: x = 1
    if y < 1: y = 1
    tx = tau_cycle(x); ty = tau_cycle(y)
    if tx is None or ty is None: continue
    sums = set((tx[k] + ty[k]) % 3 for k in range(3))  # get: 0=tau4,1=tau2,2=tau1
    if sums != {0, 1, 2}:
        fail += 1
        if fail <= 5:
            print(f"  FAIL: x={x} y={y} tx={tx} ty={ty} sums={sums}")
print(f"覆盖引理: {N} 随机对, 失败 {fail} 例 -> {'成立' if fail == 0 else '有反例!'}")

print()
print("=== 测试2: rem>=0 条件满足率 (真实密钥场景, a'=1) ===")
# 诚实 keygen: a0,b0 随机 k 位, n = 首次相遇总步数 (最短)
def meeting(a, b, lim=300000):
    """两轨线首次相遇的最短 s+t"""
    seen = {}
    x = a; s = 0
    while s <= lim:
        if x in seen: break
        seen[x] = s
        x = x // 2 if x % 2 == 0 else 3 * x + 1
        s += 1
    y = b; t = 0
    while t <= lim:
        if y in seen: return seen[y] + t
        if y == 1: break
        y = y // 2 if y % 2 == 0 else 3 * y + 1
        t += 1
    return None

random.seed(7)
ok = 0; total = 0; fails = []
for k in (64, 128, 256):
    for i in range(10):
        a0 = random.getrandbits(k) | (1 << (k-1))
        b0 = random.getrandbits(k) | (1 << (k-1))
        m = abs(a0 - b0)
        n = meeting(a0, b0)
        if n is None: continue
        # 攻击: a'=1 (若 m+1 合法), b'=1+m
        x = 1; b = 1 + m
        tx = tau_cycle(x); tb = tau_cycle(b)
        if tx is None or tb is None: continue
        S = [tx[j] + tb[j] for j in range(3)]  # tau4, tau2, tau1 的和
        Smin = min(S)
        total += 1
        if Smin <= n - 4:
            ok += 1
        else:
            fails.append((k, n, Smin))
print(f"rem>=0 条件: {total} 实例, 满足 {ok}, 不满足 {len(fails)}")
for f in fails[:8]:
    print("  close-call:", f)

print()
print("=== 测试3: 若 S_min 不满足, 换 x 重试的期望次数 ===")
random.seed(99)
retries = []
for k in (64, 128):
    for i in range(5):
        a0 = random.getrandbits(k) | (1 << (k-1))
        b0 = random.getrandbits(k) | (1 << (k-1))
        m = abs(a0 - b0); n = meeting(a0, b0)
        if n is None: continue
        r = 0
        for x in range(1, 2000):
            b = x + m
            tx = tau_cycle(x); tb = tau_cycle(b)
            if tx is None or tb is None: continue
            S = [tx[j] + tb[j] for j in range(3)]
            if min(S) <= n - 4:
                r += 1
                break
            r += 1
        retries.append(r)
print(f"重试次数分布: min={min(retries)}, max={max(retries)}, 均值={sum(retries)/len(retries):.1f}")
