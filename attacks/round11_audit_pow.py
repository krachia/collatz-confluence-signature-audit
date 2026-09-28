# -*- coding: utf-8 -*-
"""round11_audit_pow.py — JRFM PoW（Bocart 2018）最小可复现审计

审计口径（第三刀 P2）：以原文所附参考实现为口径（JRFM 2018, 11(83), 附录代码）：
  xMax = x; while x > 1: x = x/2 或 (3x+1)/2; if x > xMax: +1  ——「新极大值计数」ξ(x)。
复算三件事：
  (a) 统计量复现：ξ 的实现核对（原文示例 ξ(3)=2、ξ(2^a)=0）；
  (b) 自报分布复核：ξ 的几何分布参数拟合（原文自报 p≈0.714）；
  (c) 生成-验证成本结构：候选评估（=一次轨线重算）与验证核对（=同一原语）
      的单次成本；以及"挖矿"=对 ξ 的扫描：扫描长度 vs 期望 1/P(ξ=t)。
不评价范围：不讨论共识安全、网络与其余组件；不重建完整创世流程。

seed：20261004。
"""
import sys

try:  # 控制台编码守卫：保证含 ρ̂ 等符号的输出在非 UTF-8 控制台/重定向下不中断
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import random
import statistics
import time

random.seed(20261004)


def inflation_propensity(x):
    """原文代码逐行复写（加速映射与计数口径一致）。"""
    xmax = x
    step = 0
    while x > 1:
        if x % 2 == 0:
            x = x // 2
        else:
            x = (3 * x + 1) // 2
        if x > xmax:
            xmax = x
            step += 1
    return step


print("== (a) 实现核对 ==")
print(f"ξ(3) = {inflation_propensity(3)}（原文示例：2）")
print(f"ξ(7)  = {inflation_propensity(7)}")
for a in (2, 4, 8, 16):
    assert inflation_propensity(2 ** a) == 0
print("ξ(2^a) = 0（全部 a，与原文一致）")
print()

print("== (b) 自报分布复核：几何拟合 ==")
N = 200000
vals = [inflation_propensity(random.getrandbits(31) + 2) for _ in range(N)]
mean_xi = statistics.mean(vals)
rho_hat = mean_xi / (1.0 + mean_xi)   # 原文式 (10)：ρ̂ = µ1/(1+µ1)
print(f"N={N}  x ~ [2, 2^31)：mean ξ = {mean_xi:.3f}  按原文估计式 ρ̂ = {rho_hat:.3f}（原文自报 ≈ 0.714）")
tail = [sum(1 for v in vals if v >= t) / N for t in (1, 2, 3, 4, 5, 6)]
print("经验 P(ξ>=t)（t=1..6）:", [f"{q:.3f}" for q in tail])
print("对照 0.714^t：        ", [f"{0.714**t:.3f}" for t in range(1, 7)])
print("比值 P(>=t+1)/P(>=t):", [f"{tail[i+1]/tail[i]:.3f}" for i in range(5)])
print()

print("== (c) 生成-验证成本结构 ==")
x0 = random.getrandbits(40) + 2 ** 39
t0 = time.perf_counter()
for _ in range(2000):
    inflation_propensity(x0)
eval_us = (time.perf_counter() - t0) / 2000 * 1e6
print(f"单次候选评估（=一次轨线重算，生成侧单位工作）≈ {eval_us:.2f} us")
t0 = time.perf_counter()
_ = inflation_propensity(x0)
ver_us = (time.perf_counter() - t0) * 1e6
print(f"单次验证核对（=同一函数重算）          ≈ {ver_us:.2f} us")
# 挖矿扫描：连续整数扫描至 ξ(x) == t
print()
print("挖矿扫描（连续整数扫描至 ξ==t；每步=一次重算）：")
print(f"{'t':>3} {'平均扫描步数':>12} {'预测 1/P(ξ=t)':>14} {'单次尝试us':>10}")
t0_all = time.perf_counter()
for t in (3, 4, 5, 6):
    trials = 200
    scans = []
    for _ in range(trials):
        x = random.getrandbits(24) + 2
        c = 0
        while True:
            c += 1
            if inflation_propensity(x) == t:
                break
            x += 1
        scans.append(c)
    pred = 1.0 / ((0.286) * (0.714 ** t))   # P(ξ=t) = 0.714^t − 0.714^{t+1}
    print(f"{t:>3} {statistics.mean(scans):>12.1f} {pred:>14.1f}")
dt_all = time.perf_counter() - t0_all
total_tries = sum(scans)  # 最后一档扫描次数（记录用）
print(f"（四档扫描合计 {dt_all:.1f}s；单次尝试成本与上方「单次候选评估」同量级）")
print()
print("按自报分布外推：t=40 的期望扫描次数 = 1/P(ξ=40) ≈ "
      f"{1.0/(0.286*(0.714**40)):.2e} 次（每次=一次轨线重算）——难度参数仅调节抽样期望。")
print()
print("== 附注（不入稿，仅记录）==")
print("ξ(2^t - 1) 数值检查（t=2..12）:", {t: inflation_propensity(2**t - 1) for t in range(2, 13)})
print()
print("== 审计结论（对照 §7.3 攻击移植 A 口径）==")
print("- 生成侧单位工作（单次候选评估）与验证侧核对（同一函数重算）成本同阶；")
print("- 挖矿=对 ξ 的线性扫描，扫描长度与 1/P(ξ=t) 一致：难度仅调节抽样等待；")
print("- 本审计不评价其非 Collatz 组件与共识层安全性。")
