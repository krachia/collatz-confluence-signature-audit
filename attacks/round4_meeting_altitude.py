"""
round4_meeting_altitude.py — 两条 256 位轨线的首次相遇发生在多高?

论证: 每条轨线 ~ L 个点 (L ~ 总停止时间 ~ 1800)。
两条轨线在值域 V 处相遇的概率 ~ L^2 / V (两随机点集碰撞)。
  - 高空 (V ~ 2^256): 概率 ~ 1800^2 / 2^256 ~ 2^{-234} (引理 3 的界; 旧稿曾误写 2^{-500}) ~ 0
  - 相遇要发生, V 必须 ~ L^2 ~ 3e6 (~2^22)
所以: 无论起点多大, 首次相遇几乎必然发生在低空固定子图内。
"""
import random

random.seed(20260912)


def T(x):
    return x // 2 if x % 2 == 0 else 3 * x + 1


def first_meeting_z(a, b, max_steps=30000):
    va = {a: 0}
    vb = {b: 0}
    ca, cb = a, b
    for total in range(1, max_steps + 1):
        ca = T(ca)
        if ca in vb:
            return ca, total + vb[ca]   # z, s+t
        va[ca] = total
        cb = T(cb)
        if cb in va:
            return cb, va[cb] + total
        vb[cb] = total
    return None, None


k = 256
zs = []
ns = []
for i in range(20):
    a = random.randint(1 << (k - 1), (1 << k) - 1)
    b = random.randint(1 << (k - 1), (1 << k) - 1)
    z, n = first_meeting_z(a, b)
    zs.append(z)
    ns.append(n)

bl = [z.bit_length() for z in zs]
print(f"20 对随机 256 位起点:")
print(f"  汇合点 z 的位长: min={min(bl)}, 中位={sorted(bl)[len(bl)//2]}, max={max(bl)}")
print(f"  z <= 1000 的比例: {sum(1 for z in zs if z <= 1000)}/20")
print(f"  z <= 10^6 的比例: {sum(1 for z in zs if z <= 10**6)}/20")
print(f"  d 值范围: min={min(ns)}, max={max(ns)}")
print()
print("对照: 起点是 256 位 (~10^77), 汇合点却是这个量级:")
for z in zs[:5]:
    print(f"    z = {z}   (起点 ~10^77, 汇合点 ~10^{len(str(z))-1})")
