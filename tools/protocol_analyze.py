#!/usr/bin/env python3
"""
DingTalk A1 私有 BLE 协议解析器

专门抽取 fe1c(命令,handle 0x8002)与 fe1b(通知,handle 0x8005)上的原始报文,
解出包头字段并按命令归类,目的是还原出足以自行实现客户端的协议规格。

用法:
    python protocol_analyze.py <bugreport.zip | btsnoop_hci.log>
"""

import sys
import os
import json
import struct
from collections import defaultdict, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from btsnoop_gatt import read_btsnoop, extract_btsnoop_from_zip

CMD_HANDLE = 0x8002     # fe1c  App -> 设备
NTF_HANDLE = 0x8005     # fe1b  设备 -> App
HEADER_SIZE = 8
MAX_PAYLOAD_LEN = 64 * 1024 * 1024
KNOWN_FRAME_TYPES = {0x13, 0x14, 0x31}


def collect_att_fragments(src):
    """重组 HCI/L2CAP,取出两个私有特征上的单个 ATT value。"""
    reasm = {}
    out = []
    for ts, from_dev, pkt in read_btsnoop(src):
        if not pkt or pkt[0] != 0x02 or len(pkt) < 5:
            continue
        hf, dlen = struct.unpack("<HH", pkt[1:5])
        conn, pb = hf & 0x0FFF, (hf >> 12) & 0x03
        payload = pkt[5:5 + dlen]

        # 同一 connection 的两个方向可能交错,必须分别维护 L2CAP 状态。
        key = (conn, from_dev)
        if pb == 0x01:
            if key not in reasm:
                continue
            reasm[key] += payload
        else:
            reasm[key] = payload

        buf = reasm[key]
        if len(buf) < 4:
            continue
        l2len, cid = struct.unpack("<HH", buf[:4])
        if len(buf) - 4 < l2len:
            continue
        body = buf[4:4 + l2len]
        del reasm[key]

        if cid != 0x0004 or not body:
            continue
        op = body[0]
        # 0x12/0x52 写, 0x1B 通知
        if op in (0x12, 0x52, 0x1B) and len(body) >= 3:
            h = struct.unpack("<H", body[1:3])[0]
            val = body[3:]
            if h in (CMD_HANDLE, NTF_HANDLE) and val:
                out.append((ts, h, val))
    return out


class A1MessageReassembler:
    """按 A1 头部声明的 32 位长度重组跨 ATT notification 的消息。"""

    def __init__(self, max_payload_len=MAX_PAYLOAD_LEN):
        self.max_payload_len = max_payload_len
        self.pending = {}       # handle -> 正在重组的消息
        self.orphan_fragments = 0

    def feed(self, ts, handle, value):
        """输入一个 ATT value,返回其中完成的零个或多个 A1 消息。"""
        completed = []
        chunk = value

        while chunk:
            state = self.pending.get(handle)
            if state is not None:
                need = state["declared_len"] - len(state["payload"])
                take = min(need, len(chunk))
                state["payload"].extend(chunk[:take])
                chunk = chunk[take:]
                if len(state["payload"]) < state["declared_len"]:
                    break
                completed.append((state["ts"], handle,
                                  state["header"] + bytes(state["payload"])))
                del self.pending[handle]
                continue

            if len(chunk) < HEADER_SIZE or chunk[0] not in KNOWN_FRAME_TYPES:
                # 抓包可能从一条长消息中途开始;这种片段不能安全解释成新命令。
                self.orphan_fragments += 1
                break

            declared_len = int.from_bytes(chunk[4:8], "big")
            if declared_len > self.max_payload_len:
                self.orphan_fragments += 1
                break

            header = chunk[:HEADER_SIZE]
            available = chunk[HEADER_SIZE:]
            take = min(declared_len, len(available))
            payload = bytearray(available[:take])
            chunk = available[take:]

            if len(payload) == declared_len:
                completed.append((ts, handle, header + bytes(payload)))
            else:
                self.pending[handle] = {
                    "ts": ts,
                    "header": header,
                    "declared_len": declared_len,
                    "payload": payload,
                }
                break

        return completed


def collect(src, return_stats=False):
    """返回重组后的 A1 消息;兼容原有调用方的三元组格式。"""
    fragments = collect_att_fragments(src)
    reasm = A1MessageReassembler()
    out = []
    for ts, handle, value in fragments:
        out.extend(reasm.feed(ts, handle, value))
    if return_stats:
        stats = {
            "att_fragments": len(fragments),
            "messages": len(out),
            "orphan_fragments": reasm.orphan_fragments,
            "unfinished_messages": len(reasm.pending),
        }
        return out, stats
    return out


def parse_header(d: bytes):
    """
    观察到的包头(8 字节):
        [0]     类型/方向
        [1:3]   16 位命令 ID(大端)
        [3]     序列号
        [4:8]   payload 长度(32 位大端)
    """
    if len(d) < HEADER_SIZE:
        return None
    return {
        "type": d[0],
        "cmd": int.from_bytes(d[1:3], "big"),
        "seq": d[3],
        "len": int.from_bytes(d[4:8], "big"),
        "payload": d[HEADER_SIZE:],
    }


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "capture/bugreport.zip"
    if src.lower().endswith(".zip"):
        got = extract_btsnoop_from_zip(src)
        if not got:
            print("!! 没找到 btsnoop")
            return 1
        data = got[0][1]
    else:
        data = src

    pkts, stats = collect(data, return_stats=True)
    print(f"提取到 {stats['att_fragments']} 个私有特征 ATT 片段,"
          f"重组为 {len(pkts)} 条完整 A1 消息")
    if stats["orphan_fragments"] or stats["unfinished_messages"]:
        print(f"  跳过孤立续片 {stats['orphan_fragments']} 个,"
              f"末尾未完成消息 {stats['unfinished_messages']} 条")
    print()

    # ---- 1. 头部字段分布,用于验证字段含义 ----
    print("=" * 78)
    print("### 包头字段分布")
    print("=" * 78)
    dist = defaultdict(lambda: defaultdict(int))
    for ts, h, d in pkts:
        hd = parse_header(d)
        if not hd:
            continue
        dist["type"][hd["type"]] += 1
        dist["cmd"][hd["cmd"]] += 1
        dist["seq"][hd["seq"]] += 1
    for field in ("type", "cmd", "seq"):
        vals = sorted(dist[field].items(), key=lambda x: -x[1])[:14]
        width = 4 if field == "cmd" else 2
        print(f"  {field:4s}: " + "  ".join(f"0x{v:0{width}x}×{c}" for v, c in vals))

    # ---- 2. 长度字段验证 ----
    print("\n" + "=" * 78)
    print("### 长度字段验证 (头[4:8] 大端值是否等于 payload 实际长度)")
    print("=" * 78)
    ok = bad = 0
    samples = []
    for ts, h, d in pkts:
        hd = parse_header(d)
        if not hd:
            continue
        if hd["len"] == len(hd["payload"]):
            ok += 1
        else:
            bad += 1
            if len(samples) < 6:
                samples.append((hd["len"], len(hd["payload"]), d[:16].hex()))
    print(f"  吻合: {ok}    不吻合: {bad}")
    if samples:
        print("  不吻合样本 (声明长度 / 实际长度 / 头16字节):")
        for a, b, hx in samples:
            print(f"    {a:5d} / {b:5d}   {hx}")

    # ---- 3. 按命令 ID 归类 ----
    print("\n" + "=" * 78)
    print("### 命令分类 (cmd -> JSON 内容)")
    print("=" * 78)
    bycmd = OrderedDict()
    for ts, h, d in pkts:
        hd = parse_header(d)
        if not hd:
            continue
        cmd = hd["cmd"]
        direction = "REQ" if h == CMD_HANDLE else "RSP"
        p = hd["payload"]
        try:
            txt = p.decode("utf-8")
            if not txt.lstrip().startswith(("{", "[")):
                raise ValueError
            js = json.loads(txt)
            kind = "json"
        except Exception:
            js, kind = None, "bin"
            txt = None

        key = (cmd, direction)
        bycmd.setdefault(key, {"n": 0, "json": [], "binlen": []})
        e = bycmd[key]
        e["n"] += 1
        if kind == "json":
            s = json.dumps(js, ensure_ascii=False, sort_keys=True)
            if s not in e["json"] and len(e["json"]) < 4:
                e["json"].append(s)
        else:
            e["binlen"].append(len(p))

    for (cmd, direction), e in sorted(bycmd.items()):
        print(f"\n  cmd=0x{cmd:04X}  {direction}  ({e['n']} 次)")
        for s in e["json"]:
            print(f"      {s[:300]}")
        if e["binlen"]:
            tot = sum(e["binlen"])
            print(f"      [二进制 {len(e['binlen'])} 包, 共 {tot} 字节, "
                  f"单包 {min(e['binlen'])}~{max(e['binlen'])}]")

    # ---- 4. 二进制块(音频数据)结构 ----
    print("\n" + "=" * 78)
    print("### 二进制数据块结构分析")
    print("=" * 78)
    bins = []
    for ts, h, d in pkts:
        hd = parse_header(d)
        if not hd:
            continue
        p = hd["payload"]
        if not p:
            continue
        try:
            t = p.decode("utf-8")
            if t.lstrip().startswith(("{", "[")):
                continue
        except Exception:
            pass
        bins.append((hd["cmd"], p, d))

    print(f"  二进制块总数: {len(bins)}")
    if bins:
        # 找公共前缀 —— 若存在稳定前缀,说明是块头而非整体加密
        first = bins[0][2]
        common = 0
        for i in range(min(32, len(first))):
            if all(len(b[2]) > i and b[2][i] == first[i] for b in bins[:40]):
                common += 1
            else:
                break
        print(f"  前 40 块的公共前缀长度: {common} 字节")
        if common:
            print(f"  公共前缀: {first[:common].hex(' ')}")
            print("  -> 存在稳定块头,说明数据不是整体加密(整体加密的话头部不会重复)")
        print("\n  前 5 块样本:")
        for cmd, p, d in bins[:5]:
            print(f"    cmd=0x{cmd:04X} len={len(p):4d}  {d[:40].hex(' ')}")

        # 统计块大小分布
        sizes = defaultdict(int)
        for cmd, p, d in bins:
            sizes[len(p)] += 1
        top = sorted(sizes.items(), key=lambda x: -x[1])[:8]
        print("\n  块大小分布 (长度×次数): " + "  ".join(f"{s}×{c}" for s, c in top))

    return 0


if __name__ == "__main__":
    sys.exit(main())
