#!/usr/bin/env python3
"""A1 应用层分片重组的离线回归测试;不连接设备。"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from protocol_analyze import (
    A1MessageReassembler,
    CMD_HANDLE,
    NTF_HANDLE,
    parse_header,
)


def make_frame(frame_type, cmd, seq, payload):
    return (bytes([frame_type]) + cmd.to_bytes(2, "big") + bytes([seq])
            + len(payload).to_bytes(4, "big") + payload)


class A1MessageReassemblerTests(unittest.TestCase):
    def test_unfragmented_message(self):
        frame = make_frame(0x31, 0x0132, 7, b'{"code":200}')
        reasm = A1MessageReassembler()

        self.assertEqual(reasm.feed(1, NTF_HANDLE, frame),
                         [(1, NTF_HANDLE, frame)])
        self.assertEqual(parse_header(frame)["cmd"], 0x0132)

    def test_507_byte_continuations_are_not_fake_commands(self):
        # 首片为 8 字节头 + 499 字节 payload;续片故意以旧解析器会误认的
        # 0x78 fd 22 开头,验证它仍被视为 0x0115 的数据。
        payload = b"A" * 499 + b"\x78\xfd\x22\x1e\x85\x4a\x92\xbc" + b"B" * 700
        frame = make_frame(0x13, 0x0115, 0x99, payload)
        fragments = [frame[:507], frame[507:1014], frame[1014:]]
        reasm = A1MessageReassembler()

        completed = []
        for fragment in fragments:
            completed.extend(reasm.feed(1, NTF_HANDLE, fragment))

        self.assertEqual(completed, [(1, NTF_HANDLE, frame)])
        self.assertEqual(parse_header(completed[0][2])["cmd"], 0x0115)
        self.assertFalse(reasm.pending)

    def test_handles_have_independent_pending_state(self):
        long_frame = make_frame(0x13, 0x0115, 1, b"x" * 900)
        short_frame = make_frame(0x31, 0x0008, 2, b"ok")
        reasm = A1MessageReassembler()

        self.assertEqual(reasm.feed(1, NTF_HANDLE, long_frame[:507]), [])
        self.assertEqual(reasm.feed(2, CMD_HANDLE, short_frame),
                         [(2, CMD_HANDLE, short_frame)])
        self.assertEqual(reasm.feed(3, NTF_HANDLE, long_frame[507:]),
                         [(1, NTF_HANDLE, long_frame)])

    def test_multiple_messages_in_one_att_value(self):
        first = make_frame(0x31, 0x0008, 1, b"one")
        second = make_frame(0x31, 0x0009, 2, b"two")
        reasm = A1MessageReassembler()

        self.assertEqual(reasm.feed(1, NTF_HANDLE, first + second), [
            (1, NTF_HANDLE, first),
            (1, NTF_HANDLE, second),
        ])

    def test_orphan_continuation_does_not_poison_next_message(self):
        reasm = A1MessageReassembler()
        self.assertEqual(reasm.feed(1, NTF_HANDLE, b"\x78\xfd\x22garbage"), [])
        self.assertEqual(reasm.orphan_fragments, 1)

        frame = make_frame(0x31, 0x013F, 3, b'{"code":200}')
        self.assertEqual(reasm.feed(2, NTF_HANDLE, frame),
                         [(2, NTF_HANDLE, frame)])


if __name__ == "__main__":
    unittest.main()
