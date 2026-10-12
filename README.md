# Collatz 轨线汇合型签名的结构排除研究 · 复现材料

Reproducibility package for the manuscript *"Structural Exclusion of Trajectory-Confluence Collatz Signatures within a Defined Design Space"*（《Collatz 轨线汇合型签名在限定设计空间内的结构性排除：三个屏障、一项熵审计与一类设计空间的边界》，投稿中）。

本仓库与论文附录 A 的清单一一对应：**38 个实验与分析脚本、4 张图及其生成脚本、实验输出数据**。脚本与论文小节/附录的对应关系、预期输出与运行时间，见论文附录 A 的逐项列表。全部文件的 MD5 校验和见 `md5sums.txt`。

## 目录结构

```
attacks/                攻击实验（30 个脚本；论文正文与附录）
├── round1--round9*     逐轮攻击实验（确定性种子，可完全复现）
├── round10_meeting_bound.py        相遇高度界校准网格（输出 round10_out.txt）
├── analyze_round10.py              由 round10_out.txt 复算校准常数（依赖 round10 输出）
├── round11_audit_owf.py / _pow.py / _prng.py   三方案最小复现审计（附录 B）
├── round12_bitlen_cyclekill.py    位长约束下 k 位重采样回绕（输出 round12_out.txt）
├── verify_n6_margin.py            定理 1 条件余量核验（输出 verify_n6_margin_out.txt）
└── round9_out.txt / round9b_out.txt / round9c_out.txt / round10_out.txt /
    round12_out.txt / verify_n6_margin_out.txt                              代表性实验输出

paper/                  熵估计与图表（8 个脚本 + 数据；论文正文与附录）
├── estimate_min_entropy.py          初测：k=64/128/256 熵点
├── estimate_min_entropy_large.py    初测：k=512/1024 熵点
├── entropy_replication.py           表 1 主口径复测（每 k 20 次重复 × N=10,000）
├── check_m_distribution.py          固定 m 对照实验（KS 与量化 TV 输出）
├── verify_rem_condition.py          模 3 覆盖引理与 S_min 条件数值核查
├── audit_nonmeasured.py             非实测项审计（半压缩步数、窗口频率）
├── repro_run_all.py                 一键全量核查 runner（输出 repro_check_all.txt）
├── entropy_rep_A.csv / B / C        熵复测三档输出
├── m_distribution_check.csv         分布对照输出
├── m_range_check.csv                配对空间极端区间概率（(C4) 数值表）
└── figures/             4 张图（PNG）与生成脚本 make_figures.py（需 matplotlib）
```

## 环境与运行

- Python ≥ 3.10；除 `paper/figures/make_figures.py`（需要 matplotlib）外，**全部脚本仅用标准库**，Windows/Linux 通用。
- 单个脚本：`cd attacks`（或 `cd paper`）后执行 `python <脚本名>.py`。
- 一键全量核查：`cd paper && python repro_run_all.py`（运行全部实验脚本，约 30 分钟；其中熵复测为 k=64 快速口径；完整五档结果见 `entropy_rep_*.csv`）。

## 数据、确定性与口径

- 全部实验使用确定性种子，可完全复现；重复实验报均值与观察波动，不同条件（k、L、变体）分别列出（口径详见论文附录 A、B）。
- 计时为桌面级单进程环境下的结果，仅供量级参考。
- 图文件与论文图号的对应关系：`fig1_z_distribution.png` → 图 2；`fig4_entropy_vs_k.png` → 图 3；`fig3_d_entropy.png` → 图 4；`fig2_attack_cost.png` → 图 5（图 1 为论文内示意图，非生成图）。

## 许可

- 代码（全部 `*.py`）：MIT 许可，见 `LICENSE`。
- 数据与图表（`*.csv`、代表性 `*.txt` 输出、`*.png`）：CC BY 4.0，见 `LICENSE-DATA`。

## 引用

论文投稿中；正式发布后此处将更新引用格式与 DOI。如使用本仓库材料，暂请引用上述论文题目。
