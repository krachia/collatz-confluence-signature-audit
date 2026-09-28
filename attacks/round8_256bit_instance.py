"""
round8_256bit_instance.py — 生成 256 位 Collatz 密钥实例 (a, b, m, n, z)

验证: C^s(a)==z, C^t(b)==z, |a-b|==m, s+t==n, a,b 均为 256 位
"""
import random

random.seed(20260917)

def T(x): return x // 2 if x % 2 == 0 else 3 * x + 1

def first_meeting(a, b, max_steps=50000):
    va = {a: 0}; vb = {b: 0}; ca, cb = a, b
    for tot in range(1, max_steps + 1):
        ca = T(ca)
        if ca in vb: return (tot, vb[ca], ca)
        va[ca] = tot
        cb = T(cb)
        if cb in va: return (va[cb], tot, cb)
        vb[cb] = tot
    return None

k = 256
lo, hi = 1 << (k - 1), 1 << k
while True:
    a = random.randint(lo, hi - 1)
    b = random.randint(lo, hi - 1)
    if a == b: continue
    r = first_meeting(a, b)
    if r: break
s, t, z = r
m = abs(a - b)
n = s + t

# ---- 完整验证 ----
x = a
for _ in range(s): x = T(x)
assert x == z, "a 侧验证失败"
x = b
for _ in range(t): x = T(x)
assert x == z, "b 侧验证失败"
assert abs(a - b) == m
assert s + t == n
assert lo <= a < hi and lo <= b < hi

print("=" * 76)
print("256 位 Collatz 密钥实例 (私钥 a,b,s,t; 公钥 m,n; 汇合点 z)")
print("=" * 76)
print(f"\n[私钥]")
print(f"  a = {a}")
print(f"  b = {b}")
print(f"  s = {s}   (a 走到汇合点的步数)")
print(f"  t = {t}   (b 走到汇合点的步数)")
print(f"\n[公钥]")
print(f"  m = {m}")
print(f"  n = {n}")
print(f"\n[汇合点]")
print(f"  z = {z}   (C^{s}(a) = C^{t}(b) = z)")
print(f"\n[验证]")
print(f"  a 位长: {a.bit_length()}   b 位长: {b.bit_length()}   (均为 256 位)")
print(f"  C^{s}(a) == z ? {x == z if False else '见断言'}")
print(f"  |a - b| == m ? True")
print(f"  s + t == n ? {s + t == n}   (n = {n})")
print(f"  m 位长: {m.bit_length()},  n 值域参考: 之前实测 256 位密钥 n ~ 3300-3900")
print(f"\n[十六进制形式 (便于复制)]")
print(f"  a = 0x{a:x}")
print(f"  b = 0x{b:x}")
print(f"  m = 0x{m:x}")
print(f"  n = {n}   (十进制, 小整数)")
print(f"  z = {z}   (十进制)")
