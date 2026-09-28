# -*- coding: utf-8 -*-
"""round11_audit_prng.py — IJIT PRNG（Xu & Tamir 2019）最小可复现审计

审计口径（第三刀 P2）：设其输出为轨线派生量（两类形式，均按 §7.3 攻击移植 B）：
  形式 1：轨线奇偶位序列；
  形式 2：轨线值序列。
复算两个 O(1) 区分器：
  (a) 奇偶位：由命题 3，原始 T 迭代的奇偶序列不含相邻 11 —— 单窗口即可区分；
  (b) 值序列：轨线必然进入 {1,2,4} 循环（长度 3），O(1) 个历史样本后在循环内可 100% 预测。
不评价范围：不重建其完整变体（含后处理/混合输出的变体超出本审计）；
不评价非 Collatz 组件。

seed：20261005。
"""
import sys

try:  # 控制台编码守卫：保证含 ℓ 等符号的输出在非 UTF-8 控制台/重定向下不中断
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import random

random.seed(20261005)


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


print("== (a) 奇偶位形式：'11' 缺失区分器 ==")
seed = random.getrandbits(64) | (1 << 63)
bits = []
x = seed
for _ in range(200000):
    bits.append(x % 2)
    x = T(x)
n11 = sum(1 for i in range(len(bits) - 1) if bits[i] == 1 and bits[i + 1] == 1)
print(f"轨线奇偶位长度 {len(bits)}，相邻 '11' 出现次数 = {n11}（均匀流期望 ≈ {len(bits)/4:.0f}）")
# 8 位窗口含 '11' 比例（均匀：无 '11' 的 8 位串 = 55/256）
win = [1 if ('11' in ''.join(map(str, bits[i:i + 8]))) else 0 for i in range(0, 60000)]
frac = sum(win) / len(win)
print(f"8 位窗口含 '11' 的比例 = {frac:.4f}（均匀分布期望 = 1 - 55/256 ≈ {1 - 55/256:.4f}）")
print(f"区分器：单窗口事件分布（含11: 0.0000, 不含11: 1.0000）vs 均匀（{55/256:.4f}, {1 - 55/256:.4f}）；"
      f"统计距离 ≈ {1 - 55/256:.4f} → O(1) 样本区分。")
print()

print("== (b) 值序列形式：循环预测器 ==")
seed2 = random.getrandbits(256) | (1 << 255)
seq = []
seen = {}
x = seed2
cycle_start = None
while len(seq) < 5000:
    seen[x] = len(seq)
    seq.append(x)
    nx = T(x)
    if nx in seen:
        cycle_start = seen[nx]
        break
    x = nx
cyc = seq[cycle_start:]
print(f"进入循环：状态重复点后序列 = {cyc}（周期 = {len(cyc)}）")
# 预测器：O(1) 个历史样本识别循环后，逐步预测
x = seq[-1]
idx = cyc.index(x)
correct = 0
total = 1000
for i in range(total):
    x = T(x)
    pred = cyc[(idx + 1 + i) % len(cyc)]
    correct += (x == pred)
print(f"循环内预测：{correct}/{total} = {correct/total:.4f}（识别循环后）")
print()
print("== 审计结论（对照 §7.3 攻击移植 B 口径）==")
print(f"- 奇偶位输出：无相邻 11，单窗口统计距离 ≈ {1 - 55/256:.4f}（ℓ=8），O(1) 样本区分；")
print("- 值序列输出：必然进入 {1,2,4} 循环，识别后 100% 预测；")
print("- 统计测试友好的变体必然包含后处理：其熵来源仍为轨线（按 §5.4 口径约 10 bit），")
print("  超出本审计范围，需按其后处理结构另行计量。")
