#!/usr/bin/env python3
"""
判定 A1 传输的音频数据是裸 Opus 还是 AES 密文。

判据:
  1. 香农熵 —— 密文接近 8.0 bit/byte 且分布极均匀;Opus 虽是压缩流但仍有结构。
  2. Opus TOC 字节 —— 裸 Opus 每帧首字节是 TOC,同一配置下取值高度集中。
     若首字节均匀散布于 0..255,基本可判定为密文。
  3. 字节值分布的卡方 —— 对均匀分布做检验。
  4. 包头递增性 —— 找出序列号字段(判断哪几字节是头,哪些是净荷)。

用法:
    python audio_check.py <bugreport.zip>
"""

import sys
import os
import math
import struct
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from btsnoop_gatt import read_btsnoop, extract_btsnoop_from_zip
from protocol_analyze import collect, CMD_HANDLE, NTF_HANDLE


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    c = Counter(data)
    n = len(data)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def chi_square_uniform(data: bytes) -> float:
    """对 256 值均匀分布做卡方检验。自由度 255,临界值约 293(p=0.05)。"""
    if not data:
        return 0.0
    c = Counter(data)
    exp = len(data) / 256.0
    return sum((c.get(i, 0) - exp) ** 2 / exp for i in range(256))


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "capture/bugreport.zip"
    got = extract_btsnoop_from_zip(src)
    data = got[0][1]
    pkts = collect(data)

    # 先看 notify 方向的包长分布,再挑出数量最多的那一档作为流数据
    from collections import Counter as _C
    ntf = [d for ts, h, d in pkts if h == NTF_HANDLE]
    lens = _C(len(d) for d in ntf)
    print("notify 包长分布 (长度×次数):")
    for L, c in lens.most_common(10):
        print(f"    {L}×{c}")
    print()

    target_len = lens.most_common(1)[0][0]
    stream = [d for d in ntf if len(d) == target_len]
    print(f"取 {target_len} 字节的包作为流数据,共 {len(stream)} 个\n")
    if not stream:
        print("没有找到流包")
        return 1

    # ---- 逐字节位置的取值多样性,用来切分「包头」与「净荷」 ----
    print("=" * 78)
    print("### 按字节位置统计取值种类 (头部字段应种类少或单调递增)")
    print("=" * 78)
    for pos in range(0, 24):
        vals = [p[pos] for p in stream]
        uniq = len(set(vals))
        sample = " ".join(f"{v:02x}" for v in vals[:10])
        note = ""
        if uniq == 1:
            note = "  <= 恒定"
        elif uniq <= 6:
            note = "  <= 少量取值"
        else:
            # 检查是否单调递增(序列号特征)
            inc = sum(1 for a, b in zip(vals, vals[1:]) if (b - a) % 256 == 1)
            if inc > len(vals) * 0.7:
                note = "  <= 递增(疑似序列号)"
        print(f"  [{pos:2d}] 取值{uniq:4d}种   {sample}{note}")

    # ---- 熵分析:分别对整包、和剥掉不同长度头之后 ----
    print("\n" + "=" * 78)
    print("### 熵与卡方 (密文: 熵≈8.0, 卡方≈255±40)")
    print("=" * 78)
    allb = b"".join(stream)
    print(f"  整包合并 ({len(allb)} 字节):  熵 = {entropy(allb):.4f}   卡方 = {chi_square_uniform(allb):.1f}")
    for hdr in (8, 12, 16):
        body = b"".join(p[hdr:] for p in stream)
        print(f"  剥掉前{hdr:2d}字节 ({len(body)} 字节):  熵 = {entropy(body):.4f}   卡方 = {chi_square_uniform(body):.1f}")

    # ---- Opus TOC 检验 ----
    print("\n" + "=" * 78)
    print("### Opus TOC 字节检验")
    print("=" * 78)
    print("  裸 Opus 每帧首字节为 TOC,同一编码配置下应高度集中(通常仅 1~3 种取值)")
    for hdr in (8, 12, 16):
        toc = Counter(p[hdr] for p in stream if len(p) > hdr)
        top = toc.most_common(6)
        print(f"  以第 {hdr} 字节为帧首: {len(toc)} 种取值,最常见 = " +
              ", ".join(f"0x{v:02x}×{c}" for v, c in top))

    # ---- 重复块检测 ----
    print("\n" + "=" * 78)
    print("### 重复模式检测")
    print("=" * 78)
    blocks16 = Counter(allb[i:i+16] for i in range(0, len(allb) - 16, 16))
    dup = [(b, c) for b, c in blocks16.items() if c > 1]
    print(f"  16 字节对齐块: 共 {len(blocks16)} 个不同块, 其中重复的 {len(dup)} 个")
    if dup:
        for b, c in sorted(dup, key=lambda x: -x[1])[:5]:
            print(f"    {b.hex(' ')}  ×{c}")
        print("  -> 存在重复块。若为 ECB 模式加密,相同明文会产生相同密文块")
    else:
        print("  -> 无重复块(符合 CBC/CTR 流加密,或高熵压缩数据)")

    print("\n" + "=" * 78)
    print("### 前 3 包完整十六进制")
    print("=" * 78)
    for i, p in enumerate(stream[:3]):
        print(f"\n  包 {i}:")
        for off in range(0, len(p), 16):
            chunk = p[off:off+16]
            h = " ".join(f"{b:02x}" for b in chunk)
            a = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
            print(f"    {off:04x}  {h:<48}  |{a}|")

    return 0


if __name__ == "__main__":
    sys.exit(main())
