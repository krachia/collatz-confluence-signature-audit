# -*- coding: utf-8 -*-
"""entropy_replication.py — 统一采样量的熵复测（第三刀 P1-3）

设计：k ∈ {64,128,256,512,1024}，统一采样量 N=10000，独立重复 20 次。
每次重复：随机诚实实例给出 m = |a0-b0|；采样 d(a', a'±m) 的经验分布；
估计 U（唯一值数）、Hinf、H2（Renyi-2）、H1（Shannon，均为插件估计口径）。
输出：逐行 CSV（可断点续跑）+ 每 k 均值/中位/95% 置信区间/极值汇总。

seed 方案：base + k*97 + rep（确定性、可复现）。
用法：python entropy_replication.py --ks 64 128 256 --out entropy_rep_A.csv
      python entropy_replication.py --ks 512 --out entropy_rep_B.csv
      python entropy_replication.py --ks 1024 --out entropy_rep_C.csv
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


def run_rep(k, rep, N, base):
    rnd = random.Random(base + k * 97 + rep)
    lo, hi = 1 << (k - 1), 1 << k
    a0 = rnd.randint(lo, hi - 1)
    b0 = rnd.randint(lo, hi - 1)
    m = abs(a0 - b0)
    t0 = time.time()
    cnt = Counter()
    total = 0
    while total < N:
        a = rnd.randint(lo, hi - 1)
        for b in (a + m, a - m):
            if lo <= b < hi:
                d = d_shortest(a, b)
                if d is not None:
                    cnt[d] += 1
                    total += 1
                break
    U = len(cnt)
    pmax = max(cnt.values()) / total
    Hinf = -math.log2(pmax)
    H2 = -math.log2(sum((c / total) ** 2 for c in cnt.values()))
    H1 = -sum((c / total) * math.log2(c / total) for c in cnt.values())
    return dict(k=k, rep=rep, N=total, U=U, Hinf=round(Hinf, 3),
                H2=round(H2, 3), H1=round(H1, 3), secs=round(time.time() - t0, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ks', nargs='+', type=int, default=[64, 128, 256, 512, 1024])
    ap.add_argument('--reps', type=int, default=20)
    ap.add_argument('--n', type=int, default=10000)
    ap.add_argument('--seed-base', type=int, default=20261001)
    ap.add_argument('--out', default='entropy_replication.csv')
    args = ap.parse_args()

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.out)
    done = set()
    rows = []
    if os.path.exists(out):
        with open(out, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                rows.append(row)
                done.add((int(row['k']), int(row['rep'])))
        print(f"resume: {len(done)} rows already done", flush=True)

    fields = ['k', 'rep', 'N', 'U', 'Hinf', 'H2', 'H1', 'secs']
    new_file = not os.path.exists(out)
    fh = open(out, 'a', newline='', encoding='utf-8')
    w = csv.DictWriter(fh, fieldnames=fields)
    if new_file:
        w.writeheader()

    for k in args.ks:
        for rep in range(1, args.reps + 1):
            if (k, rep) in done:
                continue
            r = run_rep(k, rep, args.n, args.seed_base)
            w.writerow(r)
            fh.flush()
            print(f"  k={k} rep={rep:2d}  U={r['U']:5d}  Hinf={r['Hinf']:6.2f} "
                  f"H2={r['H2']:6.2f}  H1={r['H1']:6.2f}  ({r['secs']}s)", flush=True)
    fh.close()

    # 汇总
    with open(out, newline='', encoding='utf-8') as f:
        rows = [r for r in csv.DictReader(f)]
    print("\n===== 汇总（均值 / 中位 / 95%CI半宽 / min / max，N=" + str(args.n) + "）=====")
    for k in args.ks:
        sub = [r for r in rows if int(r['k']) == k]
        if not sub:
            continue
        n = len(sub)
        print(f"k={k} (reps={n})")
        for f_ in ('U', 'Hinf', 'H2', 'H1'):
            xs = [float(r[f_]) for r in sub]
            mean = statistics.mean(xs)
            med = statistics.median(xs)
            sd = statistics.stdev(xs) if n > 1 else 0.0
            ci = 2.093 * sd / math.sqrt(n) if n > 1 else 0.0
            print(f"   {f_:5s}  mean={mean:8.3f}  med={med:8.3f}  ±{ci:5.3f}  "
                  f"[{min(xs):.3f}, {max(xs):.3f}]")
    print("done")


if __name__ == '__main__':
    main()
