# -*- coding: utf-8 -*-
"""round10_meeting_bound.py — 相遇高度上界与 (H1)(H2) 校准（第三刀 P1-1）

对 k = 64/128/256/512/1024：
 (a) 首次相遇高度 z 的尾部：P(z >= V)，V 取 2^j 网格；
 (b) 占居量 E[|A ∩ [V,∞)|]（每条轨线在 >=V 处经过的不同值个数），校准 (H1)；
 (c) 点命中 sup_{z>=V} p(z)（同一值被单条轨线访问的概率），校准 (H2)；
 (d) 核对候选界 min{1, C*(k-j+1)^2/V} 与 C_L*mean(L_a*L_b)/V 的成立与余量。

优化：相遇路径字典复用；L_a = s_z + σ(z)、L_b = t_z + σ(z)；
轨迹高值集合 = (路径字典键 ∪ z 下游) ∩ [2^10, ∞)，集合去重后计数。
输出：屏幕 + round10_out.txt。seed：20261002 + k。
"""
import random
import time
from collections import Counter

Ks = {64: 12000, 128: 9000, 256: 5000, 512: 2500, 1024: 1500}
V_MIN_EXP = 10
LOW = 1 << V_MIN_EXP


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


def walk_to_cycle_len(x):
    n = 0
    while x not in (1, 2, 4):
        x = T(x)
        n += 1
    return n


def first_meeting(a, b, max_steps=200000):
    """返回 (z, s_z, t_z, va, vb)：首次相遇值与两侧（首次）步数、两侧路径字典。"""
    va = {a: 0}; vb = {b: 0}; ca, cb = a, b
    for tot in range(1, max_steps + 1):
        ca = T(ca)
        if ca in vb:
            return ca, va.get(ca, tot), vb[ca], va, vb
        va[ca] = tot
        cb = T(cb)
        if cb in va:
            return cb, va[cb], vb.get(cb, tot), va, vb
        vb[cb] = tot
    return None, None, None, va, vb


def downstream_high(z):
    """z（含）到进入循环前的 >= LOW 不同值集合。"""
    s = set()
    while z not in (1, 2, 4):
        if z >= LOW:
            s.add(z)
        z = T(z)
    return s


def j_grid(k):
    js = list(range(V_MIN_EXP, 31, 2))
    js += list(range(40, k, 20 if k > 512 else 10))
    return [j for j in js if j <= k - 1]


def main():
    lines = []

    def emit(t=''):
        print(t, flush=True)
        lines.append(t)

    emit("round10_meeting_bound.py — 相遇高度上界与 (H1)(H2) 校准")
    emit("P = P(z>=V); E1 = E[#不同值>=V / 单轨线]; S = sup_{z'>=V} p(z')")
    emit()

    calib = []
    mean_prod = {}
    for k, M in Ks.items():
        rnd = random.Random(20261002 + k)
        lo, hi = 1 << (k - 1), 1 << k
        t0 = time.time()
        zs, L_side, prods = [], [], []
        counter = Counter()
        n_traj = 0
        step = max(1, M // 5)
        for i in range(M):
            a = rnd.randint(lo, hi - 1)
            b = rnd.randint(lo, hi - 1)
            z, sz, tz, va, vb = first_meeting(a, b)
            if z is not None:
                zs.append(z)
                sigma = walk_to_cycle_len(z)
                La, Lb = sz + sigma, tz + sigma
                L_side.append((La, Lb))
                prods.append(La * Lb)
                dh = downstream_high(z)
                Sa = {v for v in va if v >= LOW} | dh
                Sb = {v for v in vb if v >= LOW} | dh
                for v in Sa:
                    counter[v] += 1
                for v in Sb:
                    counter[v] += 1
                n_traj += 2
            if (i + 1) % step == 0:
                print(f"   k={k}: {i+1}/{M}  ({time.time()-t0:.0f}s)", flush=True)
        dt = time.time() - t0
        mean_prod[k] = sum(prods) / len(prods)
        mean_L = sum(x + y for x, y in L_side) / (2 * len(L_side))
        zmax = max(zs) if zs else 0
        zbl = sorted(z.bit_length() for z in zs)
        emit(f"== k={k}  M={M}  ({dt:.0f}s)  mean(L_a+L_b)={mean_L:.0f} "
             f"meanL/k={mean_L/(2*k):.2f}  mean(L_a*L_b)={mean_prod[k]:.3e} "
             f"(= {mean_prod[k]/k/k:.1f}*k^2)  z: max={zmax} med_bitlen={zbl[len(zbl)//2]}")
        emit(f"{'j':>4} {'V':>12} {'P(z>=V)':>9} {'cnt':>6} {'E1':>9} {'sup p':>8} "
             f"{'k-j+1':>6} {'E1/kj':>7} {'S*V/kj':>9}")
        items = list(counter.items())
        for j in j_grid(k):
            V = 1 << j
            cnt = sum(1 for z in zs if z >= V)
            P = cnt / len(zs)
            E1 = sum(c for v, c in items if v >= V) / n_traj
            S = 0.0
            for v, c in items:
                if v >= V:
                    q = c / n_traj
                    if q > S:
                        S = q
            kj = k - j + 1
            calib.append((k, j, P, E1, S, kj, V))
            emit(f"{j:>4} {V:>12} {P:>9.5f} {cnt:>6} {E1:>9.2f} {S:>8.4f} "
                 f"{kj:>6} {E1/kj:>7.3f} {S*V/kj:>9.3f}")
        emit()

    emit("===== (H1)(H2) 常数校准（全网格最大值）=====")
    r1 = max(E1 / kj for (k, j, P, E1, S, kj, V) in calib)
    r2 = max(S * V / kj for (k, j, P, E1, S, kj, V) in calib)
    emit(f"max over grid  E1/(k-j+1)   = {r1:.3f}")
    emit(f"max over grid  S*V/(k-j+1)  = {r2:.3f}")
    emit()
    emit("===== 候选界核对 min{1, C*(k-j+1)^2/V}（非平凡格点占用比 = P/界）=====")
    for C1, C2 in ((8, 2), (10, 2), (8, 3), (16, 2), (12, 3)):
        worst = 0.0
        n_cells = 0
        for (k, j, P, E1, S, kj, V) in calib:
            bound = min(1.0, C1 * C2 * kj * kj / V)
            if bound < 1.0:
                n_cells += 1
                worst = max(worst, P / bound)
        emit(f"C={C1}*{C2}={C1*C2:>3d}: 非平凡格点 {n_cells} 个, max P/界 = {worst:.4f} "
             f"(余量 x{(1/worst if worst > 0 else float('inf')):.1f})")
    emit()
    emit("===== L 形式核对 C_L * mean(L_a*L_b)/V =====")
    for C_L in (0.5, 1.0, 2.0):
        worst = 0.0
        n_cells = 0
        for (k, j, P, E1, S, kj, V) in calib:
            bound = min(1.0, C_L * mean_prod[k] / V)
            if bound < 1.0:
                n_cells += 1
                worst = max(worst, P / bound)
        emit(f"C_L={C_L}: 非平凡格点 {n_cells} 个, max P/界 = {worst:.4f}")

    with open('round10_out.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print("saved round10_out.txt")


if __name__ == '__main__':
    main()
