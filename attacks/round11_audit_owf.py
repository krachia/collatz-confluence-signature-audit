# -*- coding: utf-8 -*-
"""round11_audit_owf.py — OWF candidate（Vuckovac 2018）最小可复现审计

审计口径（第三刀 P2）：原文自述其单向性基于「条件分支结构」与
「无分支化简的运行成本对分支数的指数依赖」（arXiv:1801.05079 摘要）。
本审计在标准 OWF 求逆目标（给定输出，找任一原语）下复算命题 1 的
平凡前驱构造，并核对两件事：
  (a) 求逆目标侧：任意 y 的 d 步前驱 2^d y 为 O(1) 构造（与 d 无关）；
  (b) 其「无分支化简成本」论述的对象是实现策略，不是求逆难度的下界
      （攻击者不被要求以无分支方式求逆——该成本不构成 OWF 的困难来源）。
不评价范围：不重建其完整构造与实现性能；不评价其非 Collatz 组件。

seed：20261003。
"""
import random

random.seed(20261003)


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


print("== (a) 任一输出的 O(1) 前驱构造（命题 1）==")
print(f"{'y bits':>7} {'d':>6} {'构造方式':>16} {'T^d(2^d*y)==y':>14} {'构造+核对(us)':>13}")
import time
for k, ds in ((64, (1, 10, 1000)), (256, (1, 10, 1000)), (1024, (1, 10, 1000))):
    y = random.getrandbits(k) | (1 << (k - 1))
    for d in ds:
        t0 = time.perf_counter()
        x = y << d                      # 2^d * y：左移 O(d) 位
        ok = True
        v = x
        for _ in range(d):              # 验证前驱链（这一步仅为审计核对，攻击者不需要）
            v = T(v)
        ok = (v == y)
        dt = (time.perf_counter() - t0) * 1e6
        print(f"{k:>7} {d:>6} {'2^d*y (左移)':>16} {str(ok):>14} {dt:>12.1f}")
        assert ok

print()
print("== (b) 奇分支逆映射的 O(1) 判定 ==")
n_valid = 0
N = 100000
for _ in range(N):
    y = random.getrandbits(64) | (1 << 63)
    if y % 2 == 0 and (y - 1) % 3 == 0:
        x = (y - 1) // 3
        if x % 2 == 1 and T(x) == y:
            n_valid += 1
print(f"随机 y（64 位）中奇前驱有效比例 ≈ {n_valid}/{N} = {n_valid/N:.4f}（理论 ≈ 1/6）")
print()
print("== 审计结论（对照 §7.3 表注口径）==")
print("- 求逆目标侧：给定输出 y，2^d y 是 O(1) 构造的合法前驱（d 任意）；")
print("- 「无分支化简成本指数级」是实现策略的成本陈述，与攻击者面对的求逆任务不对应——")
print("  不构成单向性的困难来源下界（攻击者不被要求以无分支方式求逆）。")
