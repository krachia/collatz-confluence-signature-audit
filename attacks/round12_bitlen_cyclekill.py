# -*- coding: utf-8 -*-
"""round12_bitlen_cyclekill.py — 验证端位长约束（P0）下的 cyclekill 变体实测。

背景：定义 1 的验证范围说明指出，验证谓词默认不含起点位长约束；本脚本检验
「若验证者额外强制 a', b' ∈ [2^{k-1}, 2^k)（位长谓词 P0），循环回绕攻击是否仍可行」。

对每个 k ∈ {64,128,256,1024}，生成 20 个诚实实例（n = s0+t0 最短汇合总步数，m=|a0-b0|）；
攻击者在 k 位区间重采样 a'（b'=a'+m，二者均为 k 位），按定理 cyclekill 的构造
找 z*（S_z* ≡ n mod 3 且 S_z* ≤ n）、令 s'=τ_z*(a')，t'=τ_z*(b')+rem，逐条验证谓词：
|a'-b'|=m, s'+t'=n, T^{s'}(a')=T^{t'}(b')。统计首样本命中率、重采样次数上界。

输出同时写入 round12_out.txt。
"""
import io
import random
import sys
import time

CAP = 10 ** 7

def tau_cycle(x):
    """返回 {z: 首次到达 z 的步数}，z ∈ {1,2,4}（轨线进入循环后三个值均会达到）。"""
    steps = {}
    y, i = x, 0
    while len(steps) < 3 and i <= CAP:
        if y in (1, 2, 4) and y not in steps:
            steps[y] = i
        y = y // 2 if y % 2 == 0 else 3 * y + 1
        i += 1
    return steps

def meeting(a, b):
    """首次相遇：返回 (s, t, z)。"""
    da = {}
    y, i = a, 0
    while y not in da:
        da[y] = i
        y = y // 2 if y % 2 == 0 else 3 * y + 1
        i += 1
        assert i <= CAP
    y2, j = b, 0
    while y2 not in da:
        y2 = y2 // 2 if y2 % 2 == 0 else 3 * y2 + 1
        j += 1
        assert j <= CAP
    return da[y2], j, y2

def Tj(x, j):
    for _ in range(j):
        x = x // 2 if x % 2 == 0 else 3 * x + 1
    return x

buf = []
def P(*args):
    line = " ".join(str(a) for a in args)
    print(line)
    buf.append(line)

t_start = time.time()
P("round12_bitlen_cyclekill: k 位版本循环回绕（P0 位长约束下）")
for k in (64, 128, 256, 1024):
    random.seed(20261004 + k)
    ok = 0
    first_try = 0
    samples_total = 0
    max_tries = 0
    for t in range(20):
        a0 = random.randrange(2 ** (k - 1), 2 ** k)
        b0 = random.randrange(2 ** (k - 1), 2 ** k)
        m = abs(a0 - b0)
        s0, t0, z0 = meeting(a0, b0)
        n = s0 + t0
        found = False
        for att in range(1, 201):
            ap = random.randrange(2 ** (k - 1), 2 ** k - m)
            bp = ap + m
            ta, tb = tau_cycle(ap), tau_cycle(bp)
            cand = None
            for z in (1, 2, 4):
                if z in ta and z in tb:
                    Sz = ta[z] + tb[z]
                    if Sz <= n and (n - Sz) % 3 == 0:
                        cand = z
                        break
            if cand is None:
                continue
            z = cand
            rem = n - (ta[z] + tb[z])
            sp, tp = ta[z], tb[z] + rem
            assert rem >= 0 and rem % 3 == 0
            if Tj(ap, sp) == z and Tj(bp, tp) == z and sp + tp == n and abs(ap - bp) == m:
                found = True
                samples_total += att
                if att == 1:
                    first_try += 1
                max_tries = max(max_tries, att)
                break
        if found:
            ok += 1
    P("k=%4d: 攻破 %2d/20 | 首样本命中 %2d/20 | 平均采样 %.1f 次 | 最大采样 %d 次"
      % (k, ok, first_try, samples_total / 20.0, max_tries))
P("总耗时 %.1f s（确定性种子；每次采样 = 两个 k 位轨线模拟）" % (time.time() - t_start))
io.open(r"D:/projects/Hermes_Test/collatz_crypto/attacks/round12_out.txt", "w",
        encoding="utf-8", newline="\n").write("\n".join(buf) + "\n")
