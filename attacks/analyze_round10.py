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

# ===== v187 增补：被剔除格点范围与保守复核（供论文附录 A.3 引用）=====
from math import exp, lgamma, log, log1p


def _binom_cdf(m, n, p):
    """P(X<=m), X~Bin(n,p)，对数空间求和。"""
    if p <= 0:
        return 1.0
    if p >= 1:
        return 0.0
    logs = []
    for i in range(m + 1):
        logs.append(lgamma(n + 1) - lgamma(i + 1) - lgamma(n - i + 1)
                    + i * log(p) + (n - i) * log1p(-p))
    mx = max(logs)
    return exp(mx) * sum(exp(x - mx) for x in logs)


def _cp_upper(m, n, alpha=0.05):
    """Clopper-Pearson 单侧 95% 上界（解 CDF(m;n,p)=alpha）。"""
    if m >= n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if _binom_cdf(m, n, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


C1F, C2F = 16, 1 << 13
print()
print("===== 被剔除格点与保守复核（v187）=====")
excl = [r for r in rows if round(r[5] * k_meta[r[0]]["n_traj"]) < MIN_SUPPORT]
print("剔除格点（支撑 < %d）共 %d 个，按 k 的 j 范围：" % (MIN_SUPPORT, len(excl)))
for k in sorted({r[0] for r in excl}):
    js = sorted(r[1] for r in excl if r[0] == k)
    print("  k=%d: j in [%d, %d]  (%d 格点)" % (k, js[0], js[-1], len(js)))
testable, untestable = [], []
for (k, j, P_, cnt, E1, S, kj, V) in excl:
    n = k_meta[k]["n_traj"]
    need = C2F * kj / V
    S_cons = _cp_upper(round(S * n), n)
    bd = min(1.0, C1F * C2F * kj * kj / V)
    if need >= 1.0 / n:
        testable.append((k, j, S_cons * V / kj, bd, P_))
    else:
        untestable.append((k, j, bd))
mx_t = max(testable, key=lambda r: r[2])
print("可检验被剔除格点（所需 S 界 >= 1/n_traj）：%d 个" % len(testable))
print("  最大比 S_cons*V/(k-j+1) = %.4g  (k=%d, j=%d)，c2=2^13=%d，超限数 = %d"
      % (mx_t[2], mx_t[0], mx_t[1], C2F, sum(1 for r in testable if r[2] > C2F)))
print("  该格点：P=%.3g，P 界=%.3g" % (mx_t[4], mx_t[3]))
print("不可检验被剔除格点：%d 个；其 P 界 <= %.3g；被剔除格点 P 实测最大 = %.3g"
      % (len(untestable), max(r[2] for r in untestable), max(r[2] for r in excl)))
print("（复核方法：按观测支持数的 95% 置信上界代入 S；剔除标准仅为可分辨性。）")
