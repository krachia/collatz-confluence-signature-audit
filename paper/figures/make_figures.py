"""
make_figures.py — 生成论文核心图表 (paper/figures/)

fig1_z_distribution.png  低空汇聚: 汇合点 z 的位长分布 (k=20 vs k=256)
fig2_attack_cost.png     攻击成本 vs k (H7 同分布采样命中数, 实测数据)
fig3_d_entropy.png       d 值分布 (k=128 同分布采样, 有效取值 ~10^3)
"""
import math
import os
import random
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(__file__))
random.seed(20260920)

def T(x): return x // 2 if x % 2 == 0 else 3 * x + 1

def first_meeting_z(a, b, max_steps=50000):
    va = {a: 0}; vb = {b: 0}; ca, cb = a, b
    for tot in range(1, max_steps + 1):
        ca = T(ca)
        if ca in vb: return ca, tot + vb[ca]
        va[ca] = tot
        cb = T(cb)
        if cb in va: return cb, va[cb] + tot
        vb[cb] = tot
    return None, None

# ---------- fig 1: z 分布 ----------
def sample_zs(k, n=80):
    zs = []
    for _ in range(n):
        a = random.randint(1 << (k - 1), (1 << k) - 1)
        b = random.randint(1 << (k - 1), (1 << k) - 1)
        z, _ = first_meeting_z(a, b)
        if z: zs.append(z)
    return zs

z20 = sample_zs(20)
z256 = sample_zs(256)

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, data, title in ((axes[0], z20, 'k=20'), (axes[1], z256, 'k=256')):
    bl = [z.bit_length() for z in data]
    ax.hist(bl, bins=range(0, max(bl) + 2), color='#4C72B0', edgecolor='white')
    ax.set_title(f'汇合点 z 位长分布 ({title}, 起点位长={title[2:]})')
    ax.set_xlabel('z 的位长'); ax.set_ylabel('密钥数')
    ax.axvline(statistics.median(bl), color='red', ls='--', label=f'中位 {statistics.median(bl):.0f}')
    ax.legend()
fig.suptitle('低空汇聚结构: 起点越大, 汇合点仍然极低 (4-2-1 循环附近)', fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig1_z_distribution.png'), dpi=150)
plt.close(fig)
print("fig1 done")

# ---------- fig 2: 攻击成本 vs k ----------
# H7 实测数据: 每 k 3 实例的命中采样数 (round3_bigA_scan.py)
data = {
    64:  [276, 674, 6515],
    128: [495, 4071, 115],
    256: [122, 308, 605],
}
fig, ax = plt.subplots(figsize=(7, 4.5))
for k, tries in data.items():
    ax.scatter([k] * len(tries), tries, s=60, color='#C44E52', zorder=3)
    ax.scatter([k], [statistics.median(tries)], marker='_', s=200, color='black',
               label=f'k={k} 中位 {statistics.median(tries):.0f}' if k == 64 else None)
ax.set_yscale('log')
ax.set_xticks(sorted(data.keys()))
ax.set_xlabel('安全参数 k (起点位长)')
ax.set_ylabel('攻击命中所需采样数 (对数)')
ax.set_title('同分布采样攻击成本 vs k: 不随 k 增长 (9/9 实例攻破)')
ax.grid(True, which='both', alpha=0.3)
ax.legend()
# 参考线: 2^k 穷举 (不可行) vs 实测 (~300 常数)
ks = [64, 128, 256]
ax.plot(ks, [2 ** k for k in ks], ls='--', color='gray', label='2^k 穷举 (参考)')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig2_attack_cost.png'), dpi=150)
plt.close(fig)
print("fig2 done")

# ---------- fig 3: d 值分布 (k=128) ----------
k = 128
lo, hi = 1 << (k - 1), 1 << k
a0 = random.randint(lo, hi - 1)
b0 = random.randint(lo, hi - 1)
_, n0 = first_meeting_z(a0, b0)
m = abs(a0 - b0)
ds = []
while len(ds) < 4000:
    a = random.randint(lo, hi - 1)
    for b in (a + m, a - m):
        if lo <= b < hi:
            _, d = first_meeting_z(a, b)
            if d: ds.append(d)
            break
uniq = len(set(ds))
h2e = math.log2(uniq)
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.hist(ds, bins=80, color='#55A868', edgecolor='white')
ax.axvline(n0, color='red', ls='--', label=f'公钥 n = {n0}')
ax.set_xlabel('d(a\', a\'+m) 取值')
ax.set_ylabel('采样对数')
ax.set_title(f'k=128: d 值分布 — {len(ds)} 次采样仅 {uniq} 个不同值 (熵 ~{h2e:.1f} bit)')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig3_d_entropy.png'), dpi=150)
plt.close(fig)
print(f"fig3 done (唯一值 {uniq}, log2 = {h2e:.2f})")

# ---------- fig 4: 熵 vs k 五点图 (§6.1) ----------
# 数据来自 entropy_replication.py (2026-09-28；每 k 20 次重复均值，每次 N=10000)
ks = [64, 128, 256, 512, 1024]
H2 = [8.61, 9.04, 9.59, 10.05, 10.55]   # Rényi-2：定理实际使用的口径 (§5.4)
H2ci = [0.103, 0.156, 0.067, 0.098, 0.050]
Hinf = [7.22, 7.65, 8.07, 8.48, 8.89]
Hinfci = [0.103, 0.180, 0.083, 0.099, 0.075]
H1 = [8.97, 9.42, 9.95, 10.40, 10.87]
H1ci = [0.064, 0.098, 0.042, 0.063, 0.033]
fig, ax = plt.subplots(figsize=(7.5, 5))
ax.errorbar(ks, H1, yerr=H1ci, fmt='o-', color='#C44E52', label='Shannon 熵 H1 (20 次均值±95%CI)')
ax.errorbar(ks, H2, yerr=H2ci, fmt='^-', color='#55A868', label='Rényi-2 熵 H2 (20 次均值±95%CI)')
ax.errorbar(ks, Hinf, yerr=Hinfci, fmt='s--', color='#4C72B0', label='min-entropy H∞ (20 次均值±95%CI)')
ax.axhline(128, color='gray', ls=':', label='128 bit 安全目标')
# 平均斜率外推 (k 每翻倍 +0.475 bit)
kx = [1024 * (2 ** j) for j in range(1, 13)]
hy = [10.87 + 0.475 * j for j in range(1, 13)]
ax.plot(kx, hy, color='#C44E52', alpha=0.4, ls='--', label='外推 (平均斜率 +0.475 bit/倍频)')
ax.set_xscale('log', base=2)
_n = (6, 9, 12, 15, 18, 21)
ax.set_xticks([2 ** n for n in _n])
ax.set_xticklabels([f'$2^{{{n}}}$' for n in _n])
ax.annotate('外推方向', xy=(kx[-1], hy[-1]), xytext=(1.2e6, 10.3),
            fontsize=9, color='#C44E52', ha='center',
            arrowprops=dict(arrowstyle='->', color='#C44E52', alpha=0.7, lw=1.4))
ax.set_xlabel('安全参数 k (起点位长, 对数轴)')
ax.set_ylabel('熵 (bit)')
ax.set_title('轨线距离熵 vs k: 五点实测 (20 次重复均值) + 平均斜率外推\n(按平均斜率外推, 128 bit 需 k ≈ 2^257; min-entropy 口径 ≈ 2^295)')
ax.legend(loc='upper left', fontsize=8)
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig4_entropy_vs_k.png'), dpi=150)
plt.close(fig)
print("fig4 done")
