# -*- coding: utf-8 -*-
"""analyze_round10.py — 从 round10_out.txt 解析并重做 (H1)(H2) 校准。
关键：大 V 区 sup p(z) 的观测受分辨下限（1/n_traj）限制，校准只用
"sup 支撑计数 >= MIN_SUPPORT" 的可分辨格点；其余区间另行报告。
"""
import re

MIN_SUPPORT = 30   # sup 值的支撑观测数下限（可分辨）

rows = []          # (k, j, P, cnt, E1, S, kj, V, n_traj_est)
k_meta = {}
cur_k = None
n_traj = None
with open('round10_out.txt', encoding='utf-8') as f:
    for line in f:
        m = re.match(r'== k=(\d+)\s+M=(\d+)', line)
        if m:
            cur_k = int(m.group(1))
            n_traj = 2 * int(m.group(2))
            k_meta[cur_k] = {'M': int(m.group(2)), 'n_traj': n_traj}
            continue
        parts = line.split()
        if cur_k and len(parts) == 9 and parts[0].isdigit():
            try:
                j = int(parts[0]); V = int(parts[1]); P = float(parts[2])
                cnt = int(parts[3]); E1 = float(parts[4]); S = float(parts[5])
                kj = int(parts[6])
                rows.append((cur_k, j, P, cnt, E1, S, kj, V))
            except ValueError:
                pass

print(f"parsed {len(rows)} grid cells over k={sorted(set(r[0] for r in rows))}")
print()

# ---- r1: E1/(k-j+1) over all cells ----
r1 = max(E1 / kj for (k, j, P, cnt, E1, S, kj, V) in rows)
r1_at = max(rows, key=lambda r: r[4] / r[6])
print(f"r1 = max E1/(k-j+1) = {r1:.3f}  (at k={r1_at[0]}, j={r1_at[1]})")

# ---- r2: S*V/(k-j+1) over resolvable cells ----
res = [(k, j, P, cnt, E1, S, kj, V) for (k, j, P, cnt, E1, S, kj, V) in rows
       if round(S * k_meta[k]['n_traj']) >= MIN_SUPPORT]
print(f"resolvable cells: {len(res)} / {len(rows)}")
r2 = max(S * V / kj for (k, j, P, cnt, E1, S, kj, V) in res)
r2_at = max(res, key=lambda r: r[5] * r[7] / r[6])
print(f"r2 = max S*V/(k-j+1) = {r2:.3f}  (at k={r2_at[0]}, j={r2_at[1]}, "
      f"S={r2_at[5]:.5f}, support={round(r2_at[5]*k_meta[r2_at[0]]['n_traj'])})")

# 不可分辨区（支撑 < MIN_SUPPORT）的报告：S 的上界估计
unres = [(k, j, P, cnt, E1, S, kj, V) for (k, j, P, cnt, E1, S, kj, V) in rows
         if round(S * k_meta[k]['n_traj']) < MIN_SUPPORT]
if unres:
    mx = max(unres, key=lambda r: r[5])
    print(f"unresolvable cells: {len(unres)}; max observed S in them = {mx[5]:.6f} "
          f"(k={mx[0]}, j={mx[1]}, support={round(mx[5]*k_meta[mx[0]]['n_traj'])})")
    print(f"  —— 该区 S 的估计仅受单次访问支撑；以 < {max(round(mx[5]*k_meta[mx[0]]['n_traj'])+1,2)}/n_traj 记录为止")

print()
# ---- 候选常数核对 ----
print("===== 候选常数核对 =====")
for C1, C2 in ((8, 2), (10, 2), (12, 2), (8, 4), (10, 4), (12, 4), (16, 4)):
    C = C1 * C2
    worst = 0.0
    ncells = 0
    for (k, j, P, cnt, E1, S, kj, V) in rows:
        bound = min(1.0, C * kj * kj / V)
        if bound < 1.0:
            ncells += 1
            worst = max(worst, P / bound)
    ok1 = C1 >= r1
    ok2 = C2 >= r2
    print(f"C={C1}*{C2}={C:>3d}: (H1) c1>={r1:.2f}? {ok1}  (H2) c2>={r2:.2f}? {ok2}  "
          f"非平凡格点 {ncells} 个, max P/界 = {worst:.4f}")

print()
print("===== 全格点核对（对选定常数）=====")
C1, C2 = 16, 8   # 保守默认，按上面结果调整
C = C1 * C2
bad = 0
for (k, j, P, cnt, E1, S, kj, V) in rows:
    bound = min(1.0, C * kj * kj / V)
    if P > bound * 1.0 + 1e-12:
        bad += 1
        print("VIOLATION:", k, j, P, bound)
print(f"C1={C1}, C2={C2}, C={C}: violations = {bad}")

# ---- L 形式 ----
print()
print("===== L 形式（per-k 的 mean(L_aL_b)/k^2 从 meta 行读取）=====")
# 从 round10_out.txt 里解析 "mean(L_a*L_b)=X (= Y*k^2)"
meta_prod = {}
with open('round10_out.txt', encoding='utf-8') as f:
    for line in f:
        m = re.search(r'== k=(\d+).*mean\(L_a\*L_b\)=([\d.e+]+) \(= ([\d.]+)\*k\^2\)', line)
        if m:
            meta_prod[int(m.group(1))] = float(m.group(3))
print("mean(L_aL_b)/k^2 per k:", meta_prod)
for C_L in (0.25, 0.5, 1.0):
    worst = 0.0; ncell = 0
    for (k, j, P, cnt, E1, S, kj, V) in rows:
        bound = min(1.0, C_L * meta_prod[k] * k * k / V)
        if bound < 1.0:
            ncell += 1
            worst = max(worst, P / bound)
    print(f"C_L={C_L}: 非平凡格点 {ncell}, max P/界 = {worst:.4f}")
