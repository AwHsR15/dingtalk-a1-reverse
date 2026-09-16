#!/usr/bin/env python3
"""
`dtyj_parse.py` 的回归测试。

头部常量是三份**真机文件的前 80 字节**,覆盖三种实测变体。只含头部
(格式字段、长度、CRC),不含任何音频内容,也不含设备凭据。
载荷部分用合成数据模拟明文 / 密文。

运行:  python test_dtyj_parse.py
"""

import os
import random
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dtyj_parse import PAYLOAD_AT, classify, describe_config, parse_header

# v1.7 · 32 kbps / 16 kHz · 前缀 4 · 记录 84 · 加密标志 0(实测明文,WiFi 快传原件)
V17_16K = bytes.fromhex(
    "4241424148ab4a014454594a7665722076312e37666d74200000000000000000"
    "007d0000803e00000014011054000400f2b84e00657874720000000000000000"
    "000000006461746100ab4a01d98e898b")
# v1.7 · 64 kbps / 48 kHz · 前缀 4 · 记录 164 · 加密标志 1
V17_48K = bytes.fromhex(
    "424142410ce548004454594a7665722076312e37666d74200000000000000000"
    "00fa000080bb000000140110a400040051e50800657874720100010000000000"
    "0000000064617461c4e44800bfa51432")
# v1.6 · 32 kbps / 16 kHz · 前缀 0 · 记录 80 · 加密标志 1
V16_16K = bytes.fromhex(
    "424142417872cb004454594a7665722076312e36666d74200000000000000000"
    "007d0000803e00000014011050000000c5de3200657874720000010000000000"
    "00000000646174613072cb0065efb0ec")


def with_records(head: bytes, n: int, *, encrypted: bool) -> bytes:
    """在真机头后面拼 n 条合成记录(头里的长度字段不改,等价于"只读了开头一截")。"""
    h = parse_header(head)
    rec, pre = h["record_size"], h["prefix_len"]
    rnd = random.Random(7)
    body = bytearray()
    for _ in range(n):
        if encrypted:
            body += bytes(rnd.randrange(256) for _ in range(rec))
        else:
            r = bytearray(pre)  # 真机前缀全 0
            # config 9 (SILK-WB 20ms),低 2 位帧数码合法地变化 —— 真机就是 0x4B / 0x48 混着来
            r.append(0x48 | rnd.choice((0, 3)))
            r += bytes(rnd.randrange(256) for _ in range(rec - pre - 1))
            body += r
    return head + bytes(body)


class HeaderTest(unittest.TestCase):

    def test_tags_on_fixed_offsets(self):
        """三处非标准布局决定了 tag 必须恰好在 12 / 20 / 52 / 68。"""
        for head in (V17_16K, V17_48K, V16_16K):
            self.assertEqual(parse_header(head)["tag_errors"], [])

    def test_three_variants(self):
        cases = [
            (V17_16K, "v1.7", 32000, 16000, 4, 84),
            (V17_48K, "v1.7", 64000, 48000, 4, 164),
            (V16_16K, "v1.6", 32000, 16000, 0, 80),
        ]
        for head, ver, br, sr, pre, rec in cases:
            h = parse_header(head)
            self.assertEqual((h["version"], h["bitrate"], h["sample_rate"], h["prefix_len"], h["record_size"]),
                             (ver, br, sr, pre, rec))

    def test_record_size_formula(self):
        """记录长 == 码率 × 帧长 / 8000 + 前缀长 —— 三种变体恒成立。记录长不是常数。"""
        for head in (V17_16K, V17_48K, V16_16K):
            h = parse_header(head)
            self.assertEqual(h["record_size"], h["bitrate"] * h["frame_ms"] // 8000 + h["prefix_len"])

    def test_length_fields_agree(self):
        for head in (V17_16K, V17_48K, V16_16K):
            h = parse_header(head)
            self.assertEqual(PAYLOAD_AT + h["payload_len"], h["declared_total"])

    def test_duration_matches_records(self):
        """原始记录形态:记录数 × 帧长 ≈ 头里的时长(1h26m 那条录音)。"""
        h = parse_header(V17_16K)
        secs = h["payload_len"] // h["record_size"] * h["frame_ms"] / 1000
        self.assertAlmostEqual(secs, h["duration_ms"] / 1000, delta=1.0)

    def test_aes_flag(self):
        self.assertEqual(parse_header(V17_16K)["aes_flag"], 0)
        self.assertEqual(parse_header(V17_48K)["aes_flag"], 1)
        self.assertEqual(parse_header(V16_16K)["aes_flag"], 1)

    def test_rejects_foreign_file(self):
        with self.assertRaises(ValueError):
            parse_header(b"RIFF" + bytes(76))


class VerdictTest(unittest.TestCase):

    def test_plaintext_despite_zero_prefix(self):
        """
        回归:真机前缀全是 0。旧版按"整字节"算集中度,前缀=0 的切法会凑出
        100% 的 0x00 而判错。按 config(高 5 位)判定才对。
        """
        r = classify(with_records(V17_16K, 300, encrypted=False))
        self.assertEqual(r["verdict"], "明文")
        self.assertEqual(r["config"], 9)

    def test_ciphertext(self):
        for head in (V17_48K, V16_16K):
            self.assertEqual(classify(with_records(head, 300, encrypted=True))["verdict"], "密文")

    def test_v16_has_no_prefix(self):
        """v1.6 前缀为 0:若误按 4 字节前缀切,明文也会变成一团乱。"""
        r = classify(with_records(V16_16K, 300, encrypted=False))
        self.assertEqual(r["verdict"], "明文")

    def test_converted_ogg_payload(self):
        """官方转换后:80 字节头 + Ogg 流。要能跳过 OpusHead / OpusTags 拆出音频包。"""
        def page(seq, packets):
            lacing = bytearray()
            for p in packets:
                n = len(p)
                while n >= 255:
                    lacing.append(255); n -= 255
                lacing.append(n)
            return (b"OggS" + bytes(2) + struct.pack("<qII", 0, 1, seq) + bytes(4)
                    + bytes([len(lacing)]) + bytes(lacing) + b"".join(packets))
        rnd = random.Random(3)
        audio = [bytes([0x4B]) + bytes(rnd.randrange(256) for _ in range(79)) for _ in range(120)]
        ogg = page(0, [b"OpusHead" + bytes(11)]) + page(1, [b"OpusTags" + bytes(8)])
        for k in range(0, 120, 20):
            ogg += page(2 + k, audio[k:k + 20])
        r = classify(V17_16K + ogg)
        self.assertEqual(r["layout"], "ogg")
        self.assertEqual(r["packets"], 120)
        self.assertEqual(r["verdict"], "明文")

    def test_too_few_packets(self):
        self.assertEqual(classify(with_records(V17_16K, 10, encrypted=False))["verdict"], "样本不足")


class ConfigTest(unittest.TestCase):

    def test_config_9(self):
        self.assertEqual(describe_config(0x4B >> 3), "config 9 = SILK-WB 20ms")
        self.assertEqual(0x48 >> 3, 0x4B >> 3)  # 帧数码不同,config 相同


if __name__ == "__main__":
    unittest.main(verbosity=1)
