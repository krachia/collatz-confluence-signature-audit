# -*- coding: utf-8 -*-
"""normalize_outputs.py — 输出文件的数值内容校验和（剥离计时字段、统一行尾）。

背景：部分输出文件含运行计时字段（随机器与负载变化），逐字节 MD5 在复跑后无法保持一致。
本工具按固定规则剥离计时字段并把行尾统一为 LF，再计算 MD5（数值内容校验和）。

规则（按文件名匹配；规则之外仅做行尾归一）：
  attacks/round9_out.txt    删除 | 分隔的第 6 列（表头「耗时」）
  attacks/round9c_out.txt   删除 "[耗时 ...]" 行
  attacks/round10_out.txt   删除 "(NNs)" / "(NN.Ns)" 计时段
  attacks/round12_out.txt   删除 "总耗时 ..." 行
  *.csv                     若末列为 "secs"，删除该列

用法：
  python normalize_outputs.py --write   生成 md5sums_numeric.txt
  python normalize_outputs.py --check   逐项核验（退出码 0/1）
  python normalize_outputs.py --diff    核验并定位首个差异行（需要 git）
说明：md5sums.txt 是原始文件快照（含计时字段）；数值口径结果写入 md5sums_numeric.txt。
"""
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(ROOT, "md5sums_numeric.txt")
TIMING_PAREN = re.compile(r"\(\d+(?:\.\d+)?\s*s\)\s*")
TIMING_BRACKET = re.compile(r"^\s*\[耗时 .*\]\s*$")


def normalize_text(rel, text):
    text = text.replace("\r\n", "\n")
    lines = text.split("\n")
    base = os.path.basename(rel)
    if base == "round9_out.txt":
        out = []
        for ln in lines:
            if ln.count("|") >= 6:
                parts = ln.split("|")
                del parts[5]
                ln = "|".join(parts)
            out.append(ln)
        lines = out
    elif base == "round9c_out.txt":
        lines = [ln for ln in lines if not TIMING_BRACKET.match(ln)]
    elif base == "round10_out.txt":
        lines = [TIMING_PAREN.sub("", ln) for ln in lines]
    elif base == "round12_out.txt":
        lines = [ln for ln in lines if not ln.strip().startswith("总耗时")]
    elif base.endswith(".csv"):
        rows = [ln.split(",") for ln in lines]
        if rows and rows[0] and rows[0][-1].strip() == "secs":
            rows = [r[:-1] if r else r for r in rows]
        lines = [",".join(r) for r in rows]
    return "\n".join(lines)


def output_files():
    rels = []
    for sub in ("attacks", "paper"):
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith((".txt", ".csv")) and not fn.startswith("md5sums"):
                rels.append(f"{sub}/{fn}")
    return rels


def numeric_md5(rel):
    path = os.path.join(ROOT, rel)
    text = open(path, "rb").read().decode("utf-8", "replace")
    return hashlib.md5(normalize_text(rel, text).encode("utf-8")).hexdigest()


def read_manifest():
    items = []
    with open(MANIFEST, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            h, rel = line.split(None, 1)
            items.append((h, rel.strip()))
    return items


def cmd_write():
    lines = [f"{numeric_md5(rel)}  {rel}" for rel in output_files()]
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {len(lines)} entries -> md5sums_numeric.txt")


def cmd_check(diff=False):
    items = read_manifest()
    bad = 0
    for expect, rel in items:
        got = numeric_md5(rel)
        ok = got == expect
        print(f"{'OK  ' if ok else 'FAIL'} {rel}  {got}")
        if not ok:
            bad += 1
            if diff:
                show_diff(rel)
    print(f"\n{len(items) - bad}/{len(items)} OK")
    return 1 if bad else 0


def show_diff(rel):
    try:
        old = subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{rel}"],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception as e:  # pragma: no cover
        print(f"  (diff unavailable: {e})")
        return
    cur = open(os.path.join(ROOT, rel), "rb").read().decode("utf-8", "replace")
    a = normalize_text(rel, old).split("\n")
    b = normalize_text(rel, cur).split("\n")
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else "<missing>"
        y = b[i] if i < len(b) else "<missing>"
        if x != y:
            print(f"  first diff at line {i + 1}:")
            print(f"    HEAD: {x[:160]}")
            print(f"    disk: {y[:160]}")
            return
    print("  (normalized texts identical)")


def main(argv):
    mode = argv[1] if len(argv) > 1 else "--check"
    if mode == "--write":
        cmd_write()
        return 0
    if mode == "--check":
        return cmd_check()
    if mode == "--diff":
        return cmd_check(diff=True)
    print("usage: python normalize_outputs.py [--write|--check|--diff]")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
