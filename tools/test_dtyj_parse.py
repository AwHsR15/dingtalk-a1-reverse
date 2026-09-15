#!/usr/bin/env python3
"""
`dtyj_parse.py` 的回归测试。

用的是**真机文件头**:三份 84 字节的头取自客户端
`BabaContainerTest.kt` 的 fixture(从真机上抓下来的),这里内联成常量,
所以这个测试不依赖任何外部文件,也不含任何设备凭据。

运行:  python test_dtyj_parse.py
"""

import os
import random
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dtyj_parse import PAYLOAD_AT, concentration, describe_toc, parse_header, try_layout

# 真机 v1.7 文件头(仅头部,不含音频内容)
REAL_HEADS = [
    "4241424148ab4a014454594a7665722076312e37666d742000000000000000"
    "00007d0000803e00000014011054000400f2b84e0065787472000000000000"
    "0000000000006461746100ab4a01d98e898b00000000",
    "42414241080b8f004454594a7665722076312e37666d742000000000000000"
    "00007d0000803e00000014011054000400600e220065787472000001000000"
    "00000000000064617461c00a8f001cc77ee100000000",
]


def make_container(head_hex: str, records: int, *, encrypted: bool, truncate: int = 0) -> bytes:
    """按真机头造一个容器。加密态用随机字节模拟密文。"""
    head = bytearray(bytes.fromhex(head_hex)[:PAYLOAD_AT])
    rec = struct.unpack_from("<H", head, 44)[0]
    rnd = random.Random(1234)  # 固定种子,测试要可重复

    body = bytearray()
    for i in range(records):
        if encrypted:
            body += bytes(rnd.randrange(256) for _ in range(rec))
        else:
            r = bytearray(rec)
            struct.pack_into("<I", r, 0, i)   # 4 字节前缀
            r[4] = 0x4B                       # Opus TOC
            for j in range(5, rec):
                r[j] = rnd.randrange(256)
            body += r

    struct.pack_into("<I", head, 72, len(body))        # 载荷长
    struct.pack_into("<I", head, 4, 72 + len(body))    # BABA 总长
    blob = bytes(head) + bytes(body)
    return blob[: len(blob) - truncate] if truncate else blob


class HeaderTest(unittest.TestCase):
    """头部解析 —— 三处不标准全在这儿把关。"""

    def test_tags_land_on_fixed_offsets(self):
        """ver@12 / fmt@20 / extr@52 / data@68 必须各就各位。"""
        for hex_head in REAL_HEADS:
            h = parse_header(bytes.fromhex(hex_head))
            self.assertEqual(h["tag_errors"], [], "真机头的标记位置不应有偏差")

    def test_fields_match_real_device(self):
        for hex_head in REAL_HEADS:
            h = parse_header(bytes.fromhex(hex_head))
            self.assertEqual(h["version"], "v1.7")
            self.assertEqual(h["bitrate"], 32000)
            self.assertEqual(h["sample_rate"], 16000)
            self.assertEqual(h["frame_ms"], 20)
            self.assertEqual(h["bits"], 16)
            # 记录长 84 = 4 字节前缀 + 80 字节 Opus 包。
            # 别和官方 SDK 打印的 `Frame size: 80`(指 Opus 包)搞混。
            self.assertEqual(h["record_size"], 84)

    def test_two_length_fields_agree(self):
        """80 + 载荷长 == BABA@4 + 8。两个长度字段必须自洽。"""
        for hex_head in REAL_HEADS:
            h = parse_header(bytes.fromhex(hex_head))
            self.assertEqual(PAYLOAD_AT + h["payload_len"], h["declared_total"] + 8)

    def test_payload_divides_by_record_size(self):
        """真机载荷长必须被记录长整除 —— 定长记录数组的硬性要求。"""
        for hex_head in REAL_HEADS:
            h = parse_header(bytes.fromhex(hex_head))
            self.assertEqual(h["payload_len"] % h["record_size"], 0)

    def test_duration_matches_record_count(self):
        """
        记录数 × 帧长 应当等于录音时长。

        样本 1 有 257984 条 × 20 ms = 5159.68 秒 ≈ 1h26m,
        正是界面上那条标着「1h 26m 5s」的录音 —— 容器解析和用户
        看得见的时长在这里对上了。
        """
        h = parse_header(bytes.fromhex(REAL_HEADS[0]))
        n = h["payload_len"] // h["record_size"]
        self.assertEqual(n, 257984)
        self.assertAlmostEqual(n * h["frame_ms"] / 1000.0, 5159.68, places=2)

    def test_rejects_foreign_file(self):
        with self.assertRaises(ValueError):
            parse_header(b"RIFF\x00\x00\x00\x00WAVEfmt ")


class LayoutTest(unittest.TestCase):
    """排布判定 —— 明文该判明文,密文该判密文。"""

    def _probe(self, blob: bytes, record_size: int, prefix_len: int) -> float:
        h = parse_header(blob)
        body = blob[PAYLOAD_AT : PAYLOAD_AT + h["payload_len"]]
        tocs, _, _ = try_layout(body, record_size, prefix_len)
        return concentration(tocs)

    def test_plaintext_is_recognised(self):
        blob = make_container(REAL_HEADS[1], 400, encrypted=False)
        self.assertEqual(self._probe(blob, 84, 4), 1.0, "切对了应当 TOC 全同")

    def test_off_by_four_destroys_structure(self):
        """
        前缀算成 0(等价于把 CRC 当载荷、整体错位 4 字节)会毁掉结构。

        这正是那个坑的样子:看起来像"包体是密文",其实只是切错了。
        """
        blob = make_container(REAL_HEADS[1], 400, encrypted=False)
        self.assertLess(self._probe(blob, 84, 0), 0.1)

    def test_ciphertext_looks_uniform(self):
        """密文的首字节应当接近均匀分布(1/256 量级)。"""
        blob = make_container(REAL_HEADS[1], 400, encrypted=True)
        self.assertLess(self._probe(blob, 84, 4), 0.05)

    def test_truncated_file_is_detectable(self):
        """截断文件:头里声明的长度大于磁盘实际大小。"""
        full = make_container(REAL_HEADS[1], 400, encrypted=False)
        cut = make_container(REAL_HEADS[1], 400, encrypted=False, truncate=84 * 280)
        h = parse_header(cut)
        expected = PAYLOAD_AT + h["payload_len"]
        self.assertEqual(expected, len(full))
        self.assertLess(len(cut), expected)
        self.assertAlmostEqual(len(cut) / expected, 0.30, places=2)


class TocTest(unittest.TestCase):

    def test_0x4b_is_silk_wb_20ms_mono(self):
        """0x4B 必须解成 SILK-WB 20ms 单声道 —— 与头里 16 kHz / 20 ms 一致。"""
        d = describe_toc(0x4B)
        self.assertIn("config=9", d)
        self.assertIn("SILK-WB", d)
        self.assertIn("20ms", d)
        self.assertIn("单声道", d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
