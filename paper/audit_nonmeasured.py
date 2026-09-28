# -*- coding: utf-8 -*-
"""
审计验证：找出论文中可疑的非实测数字。
A) B 补充里的「k 位种子产生 ~1.7k 位输出」—— 实测半压缩步数
B) 「压缩串无低阶硬约束」—— 实测 I/O 窗口分布 vs 均匀期望
C) z 高位「相交概率 ~2^-500」—— 对照引理 3 的界
"""
import random
random.seed(1)

def halfcomp_steps(n):
    x = n; s = 0
    while x != 1 and s < 5_000_000:
        x = (3 * x + 1) // 2 if x % 2 else x // 2
        s += 1
    return s

print("=== A: 半压缩步数 vs k (30 样本均值) ===")
for k in (64, 128, 256):
    vals = []
    for _ in range(30):
        n = random.randint(1 << (k - 1), (1 << k) - 1)
        vals.append(halfcomp_steps(n))
    avg = sum(vals) / len(vals)
    print(f"k={k}: 半压缩步数均值 = {avg:.1f}  (比值 vs k = {avg/k:.2f})")

print()
print("=== A2: 原始步数（对照） vs k ===")
def raw_steps(n):
    x = n; s = 0
    while x != 1 and s < 5_000_000:
        x = x // 2 if x % 2 == 0 else 3 * x + 1
        s += 1
    return s
for k in (64, 128, 256):
    vals = []
    for _ in range(30):
        n = random.randint(1 << (k - 1), (1 << k) - 1)
        vals.append(raw_steps(n))
    avg = sum(vals) / len(vals)
    print(f"k={k}: 原始步数均值 = {avg:.1f}  (比值 vs k = {avg/k:.2f})")

print()
print("=== B: 半压缩 I/O 串窗口分布 (k=64, 200 样本) ===")
from collections import Counter
c2 = Counter(); c3 = Counter(); total = 0
for _ in range(200):
    n = random.randint(1 << 63, 1 << 64)
    seq = []
    x = n
    while x != 1 and len(seq) < 100000:
        if x % 2:
            x = (3 * x + 1) // 2; seq.append('I')
        else:
            x = x // 2; seq.append('O')
    s = ''.join(seq)
    total += len(s)
    for i in range(len(s) - 1): c2[s[i:i+2]] += 1
    for i in range(len(s) - 2): c3[s[i:i+3]] += 1
n2 = sum(c2.values()); n3 = sum(c3.values())
print(f"位数总计 {total}, 二元组样本 {n2}, 三元组样本 {n3}")
print("二元组频率（均匀期望 0.25）:")
for k2 in ('II', 'IO', 'OI', 'OO'):
    print(f"  {k2}: {c2[k2]/n2:.3f}")
print("三元组频率（均匀期望 0.125）:")
for k3 in ('III', 'IIO', 'IOI', 'IOO', 'OII', 'OIO', 'OOI', 'OOO'):
    print(f"  {k3}: {c3[k3]/n3:.3f}")

print()
print("=== C: z 高位相交概率（引理 3 界）===")
# 引理 3: Pr[相交于 >= V] <= L^2/V, L ~ 原始步数 ~14.5k? 实际单轨线步 ~7k?
# k=256: L ≈ 1900 (单轨线到循环的步数), V = 2^256
L = 1900
for Vbits in (64, 128, 256):
    import math
    pbound = L * L / (2 ** Vbits)
    print(f"V=2^{Vbits}: 引理3界 L^2/V = {L*L}/{2**Vbits} ≈ 2^{{{math.log2(L*L) - Vbits:.0f}}}")
