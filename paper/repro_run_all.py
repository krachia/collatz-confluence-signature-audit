# -*- coding: utf-8 -*-
"""repro_run_all.py — 全量复现核查 runner：运行所有脚本并捕获输出。

注：
- attacks/ 自动纳入全部 round*.py（排除依赖型分析工具 analyze_*.py 与 _ 前缀辅助脚本）；
- 熵复测以 k=64、20 次重复的快速口径登记（完整五档运行见 entropy_rep_*.csv）。
- 环境：Python >= 3.10；除 figures/make_figures.py 需 matplotlib 外仅用标准库。
"""
import subprocess, time, os, sys
from pathlib import Path

PY = sys.executable
ROOT = Path(__file__).resolve().parent.parent  # 仓库根目录（含 attacks/ 与 paper/）
env = dict(os.environ)
env.pop('PYTHONPATH', None)
env['PYTHONIOENCODING'] = 'utf-8'

jobs = [('attacks', f, [], 1800) for f in sorted(os.listdir(ROOT / 'attacks'))
        if f.endswith('.py') and not f.startswith(('analyze', '_'))]
jobs += [
    ('paper', 'estimate_min_entropy.py', [], 1800),
    ('paper', 'estimate_min_entropy_large.py', [], 1800),
    ('paper', 'verify_rem_condition.py', [], 1800),
    ('paper', 'audit_nonmeasured.py', [], 1800),
    ('paper', 'check_m_distribution.py', [], 1800),
    ('paper', 'entropy_replication.py', ['--ks', '64', '--reps', '20', '--out', 'entropy_rep_A.csv'], 1800),
]

outpath = ROOT / 'paper' / 'repro_check_all.txt'
with open(outpath, 'w', encoding='utf-8') as out:
    for d, f, args, tmo in jobs:
        out.write(f'\n===== {d}/{f} =====\n'); out.flush()
        t0 = time.time()
        try:
            r = subprocess.run([PY, '-I', '-X', 'utf8', f] + args, cwd=ROOT / d, env=env,
                               capture_output=True, text=True, timeout=tmo)
            dt = time.time() - t0
            out.write(f'[exit={r.returncode} time={dt:.0f}s]\n')
            out.write(r.stdout[-8000:])
            if r.stderr.strip():
                out.write('\nSTDERR:\n' + r.stderr[-2000:])
        except subprocess.TimeoutExpired:
            out.write(f'[TIMEOUT >{tmo}s]\n')
        out.flush()
        print(f'{f}: done', flush=True)

print('ALL DONE')
