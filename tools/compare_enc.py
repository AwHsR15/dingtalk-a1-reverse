#!/usr/bin/env python3
"""
对比"加密关闭"与"加密开启"两轮抓包中,文件下载通道(cmd 0x0115)的数据。

目的:实时流(0x17)已确认始终是明文 Opus。真正要回答的是——当 App 开启加密后,
从设备下载的录音文件(经 cmd 0x15 传输)是否变成 AES 密文。
除了熵,还会比较完整 payload 指纹。Android btsnoop 经常跨 bugreport 累积;
若两轮样本逐字节相同,说明是重复历史数据,不能作为开关前后的对照实验。

用法:
    python compare_enc.py <未加密.zip> <加密.zip>
"""
import sys, os, math, hashlib
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from btsnoop_gatt import read_btsnoop, extract_btsnoop_from_zip
from protocol_analyze import collect, NTF_HANDLE


def entropy(data):
    if not data: return 0.0
    c = Counter(data); n = len(data)
    return -sum((v/n)*math.log2(v/n) for v in c.values())


def frame_payload(d):
    """剥掉 8 字节通用头 + 可能的元数据,取真正的净荷。"""
    if len(d) < 8: return b""
    return d[8:]


def payload_fingerprints(frames):
    return [(len(frame_payload(d)), hashlib.sha256(frame_payload(d)).hexdigest())
            for d in frames]


def analyze(zip_path, label):
    data = extract_btsnoop_from_zip(zip_path)[0][1]
    pkts = collect(data)
    # cmd 在包头 byte[1:3] 大端
    by_cmd = {}
    for ts, h, d in pkts:
        if h != NTF_HANDLE or len(d) < 8:
            continue
        cmd = (d[1] << 8) | d[2]
        by_cmd.setdefault(cmd, []).append(d)

    print(f"\n{'='*70}\n[{label}]  notify 各 cmd 的包数与净荷熵\n{'='*70}")
    for cmd in sorted(by_cmd):
        pkts_c = by_cmd[cmd]
        body = b"".join(frame_payload(p) for p in pkts_c)
        if len(body) < 64:
            continue
        e = entropy(body)
        tag = ""
        if e > 7.9: tag = "  <== 高熵(压缩音频/密文均可能)"
        elif e < 7.3: tag = "  <== 明文/压缩数据"
        print(f"  cmd=0x{cmd:04X}  {len(pkts_c):5d} 包  净荷 {len(body):7d}B  熵={e:.3f}{tag}")
    return by_cmd


def main():
    if len(sys.argv) < 3:
        print("usage: compare_enc.py <plain.zip> <enc.zip>")
        return 1
    plain = analyze(sys.argv[1], "加密关闭")
    encrypted = analyze(sys.argv[2], "加密开启")

    print(f"\n{'='*70}\n[0x0115 文件数据有效性检查]\n{'='*70}")
    plain_fp = payload_fingerprints(plain.get(0x0115, []))
    encrypted_fp = payload_fingerprints(encrypted.get(0x0115, []))
    if plain_fp and plain_fp == encrypted_fp:
        short = [(size, digest[:16]) for size, digest in plain_fp]
        print(f"  两份抓包中的样本逐字节相同: {short}")
        print("  结论:这是累计 btsnoop 中的同一批历史传输,不是独立的开关前/后样本。")
        print("  目前不能判断加密开关是否改变 0x0115 文件下载格式。")
    elif not plain_fp or not encrypted_fp:
        print("  至少一轮没有 0x0115 样本,无法比较文件下载格式。")
    else:
        print("  两轮 0x0115 样本不同,可继续结合容器头、Opus TOC 与熵做判定。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
