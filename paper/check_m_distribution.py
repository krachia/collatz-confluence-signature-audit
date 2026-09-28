# -*- coding: utf-8 -*-
"""check_m_distribution.py — 固定 m 同分布假设的对照检验（第三刀 P1-2）

对照两个分布：
  D_A：独立均匀对 (a,b) 的 d(a,b)（命题 5 声称的"诚实密钥分布"）
  D_B：固定 m 的采样对 (a', a'±m) 的 d(a',b')（攻击者实际采样分布）
检验：两样本 KS 统计量（附渐近 p 值）、总变差距离（经验插件）。
重复：每个 k 独立抽 20 组 m，每组两分布各 n=3000 样本。

用法：python check_m_distribution.py --ks 64 128 256
输出：m_distribution_check.csv + 屏幕汇总。
seed 方案：base + k*101 + rep。
"""
import argparse
import csv
import math
import os
import random
import statistics
import time
from collections import Counter


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


def d_shortest(a, b, max_steps=200000):
    va = {a: 0}; vb = {b: 0}; ca, cb = a, b
    for tot in range(1, max_steps + 1):
        ca = T(ca)
        if ca in vb:
            return tot + vb[ca]
        va[ca] = tot
        cb = T(cb)
        if cb in va:
            return va[cb] + tot
        vb[cb] = tot
    return None


def ks_two_sample(xs, ys):
    xs = sorted(xs); ys = sorted(ys)
    nx, ny = len(xs), len(ys)
    i = j = 0
    d = 0.0
    fx = fy = 0.0
    while i < nx and j < ny:
        if xs[i] <= ys[j]:
            i += 1
            while i < nx and xs[i] == xs[i - 1]:
                i += 1
        else:
            j += 1
            while j < ny and ys[j] == ys[j - 1]:
                j += 1
        fx, fy = i / nx, j / ny
        d = max(d, abs(fx - fy))
    return d


def ks_pvalue(d, nx, ny):
    if d <= 0:
        return 1.0
    en = math.sqrt(nx * ny / (nx + ny))
    lam = (en + 0.12 + 0.11 / en) * d
    s = sum((-1.0) ** (j - 1) * math.exp(-2.0 * j * j * lam * lam)
            for j in range(1, 101))
    return min(1.0, max(0.0, 2.0 * s))


def tv_two_sample(ca, cb, na, nb):
    keys = set(ca) | set(cb)
    return 0.5 * sum(abs(ca.get(x, 0) / na - cb.get(x, 0) / nb) for x in keys)


def quantize_counter(counter, qw):
    q = Counter()
    for v, c in counter.items():
        q[v // qw] += c
    return q


def sample_A(rnd, k, n):
    lo, hi = 1 << (k - 1), 1 << k
    ds = []
    while len(ds) < n:
        a = rnd.randint(lo, hi - 1)
        b = rnd.randint(lo, hi - 1)
        d = d_shortest(a, b)
        if d is not None:
            ds.append(d)
    return ds


def sample_B(rnd, k, n, m):
    lo, hi = 1 << (k - 1), 1 << k
    ds = []
    while len(ds) < n:
        a = rnd.randint(lo, hi - 1)
        for b in (a + m, a - m):
            if lo <= b < hi:
                d = d_shortest(a, b)
                if d is not None:
                    ds.append(d)
                break
    return ds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ks', nargs='+', type=int, default=[64, 128, 256])
    ap.add_argument('--reps', type=int, default=20)
    ap.add_argument('--n', type=int, default=3000)
    ap.add_argument('--seed-base', type=int, default=20261002)
    ap.add_argument('--qw', type=int, default=64, help='TV 量化宽度')
    ap.add_argument('--out', default='m_distribution_check.csv')
    args = ap.parse_args()

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.out)
    fields = ['k', 'rep', 'N', 'ks', 'pval', 'tv', 'meanA', 'meanB',
              'medA', 'medB', 'secs']
    fh = open(out, 'w', newline='', encoding='utf-8')
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()

    summary = {}
    for k in args.ks:
        for rep in range(1, args.reps + 1):
            rnd = random.Random(args.seed_base + k * 101 + rep)
            lo, hi = 1 << (k - 1), 1 << k
            a0 = rnd.randint(lo, hi - 1)
            b0 = rnd.randint(lo, hi - 1)
            m = abs(a0 - b0)
            t0 = time.time()
            A = sample_A(rnd, k, args.n)
            B = sample_B(rnd, k, args.n, m)
            ks = ks_two_sample(A, B)
            pv = ks_pvalue(ks, len(A), len(B))
            # TV 在量化格上计算（宽度 qw；原始支撑过稀会导致 TV 噪音偏大）
            ca = quantize_counter(Counter(A), args.qw)
            cb = quantize_counter(Counter(B), args.qw)
            tv = tv_two_sample(ca, cb, len(A), len(B))
            row = dict(k=k, rep=rep, N=args.n, ks=round(ks, 5), pval=round(pv, 4),
                       tv=round(tv, 5), meanA=round(statistics.mean(A), 1),
                       meanB=round(statistics.mean(B), 1),
                       medA=round(statistics.median(A), 1),
                       medB=round(statistics.median(B), 1),
                       secs=round(time.time() - t0, 1))
            w.writerow(row); fh.flush()
            summary.setdefault(k, []).append(row)
            print(f"  k={k} rep={rep:2d}  KS={ks:.4f} (p={pv:.3f})  TV={tv:.4f}  "
                  f"med {row['medA']:.0f}/{row['medB']:.0f}  ({row['secs']}s)", flush=True)
    fh.close()

    print("\n===== 汇总（20 组 m）=====")
    for k in args.ks:
        sub = summary.get(k, [])
        if not sub:
            continue
        ks_l = [r['ks'] for r in sub]
        tv_l = [r['tv'] for r in sub]
        pv_l = [r['pval'] for r in sub]
        rej = sum(1 for p in pv_l if p < 0.05)
        print(f"k={k}: KS mean={statistics.mean(ks_l):.4f} med={statistics.median(ks_l):.4f} "
              f"max={max(ks_l):.4f} | TV(q={args.qw}) mean={statistics.mean(tv_l):.4f} "
              f"max={max(tv_l):.4f} | p<0.05: {rej}/{len(sub)}")
    print("done")


if __name__ == '__main__':
    main()
