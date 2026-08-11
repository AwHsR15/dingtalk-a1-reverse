#!/usr/bin/env python3
"""
btsnoop -> BLE GATT 时序提取器

从 Android 的 btsnoop_hci.log(或包含它的 bugreport zip)中提取 BLE ATT 层
的完整交互:服务发现结果、特征 UUID/handle 映射、以及所有 write / notify 的原始字节。

之所以自己写而不用 Wireshark:我们要的不是逐包浏览,而是把「哪个特征、
什么时候、收发了什么字节」直接整理成协议时序表,方便反推私有协议格式。

注:HCI 层记录的 ATT 数据是明文 —— BLE 的链路加密发生在 controller 的 link layer,
host 与 controller 之间的 ACL 数据未加密,所以即使设备已配对也能看到内容。

用法:
    python btsnoop_gatt.py <btsnoop_hci.log | bugreport.zip> [--peer <MAC后缀>]
"""

import sys
import os
import struct
import zipfile
import argparse
from datetime import datetime, timedelta

# ---------- ATT 协议常量 ----------

ATT_OPS = {
    0x01: "ERROR_RSP",
    0x02: "MTU_REQ",        0x03: "MTU_RSP",
    0x04: "FIND_INFO_REQ",  0x05: "FIND_INFO_RSP",
    0x06: "FIND_BY_TYPE_REQ", 0x07: "FIND_BY_TYPE_RSP",
    0x08: "READ_BY_TYPE_REQ", 0x09: "READ_BY_TYPE_RSP",
    0x0A: "READ_REQ",       0x0B: "READ_RSP",
    0x0C: "READ_BLOB_REQ",  0x0D: "READ_BLOB_RSP",
    0x0E: "READ_MULTI_REQ", 0x0F: "READ_MULTI_RSP",
    0x10: "READ_BY_GROUP_REQ", 0x11: "READ_BY_GROUP_RSP",
    0x12: "WRITE_REQ",      0x13: "WRITE_RSP",
    0x16: "PREP_WRITE_REQ", 0x17: "PREP_WRITE_RSP",
    0x18: "EXEC_WRITE_REQ", 0x19: "EXEC_WRITE_RSP",
    0x1B: "NOTIFY",         0x1D: "INDICATE",  0x1E: "CONFIRM",
    0x52: "WRITE_CMD",      0xD2: "SIGNED_WRITE_CMD",
}

ATT_ERRS = {
    0x01: "Invalid Handle", 0x02: "Read Not Permitted", 0x03: "Write Not Permitted",
    0x04: "Invalid PDU", 0x05: "Insufficient Authentication", 0x06: "Request Not Supported",
    0x07: "Invalid Offset", 0x08: "Insufficient Authorization", 0x09: "Prepare Queue Full",
    0x0A: "Attribute Not Found", 0x0B: "Attribute Not Long",
    0x0C: "Insufficient Encryption Key Size", 0x0D: "Invalid Attribute Value Length",
    0x0E: "Unlikely Error", 0x0F: "Insufficient Encryption",
    0x10: "Unsupported Group Type", 0x11: "Insufficient Resources",
}

BASE_UUID_SUFFIX = "-0000-1000-8000-00805f9b34fb"


def fmt_uuid(raw: bytes) -> str:
    """把小端字节序的 UUID 转成标准字符串;16 位的展开成完整形式便于比对。"""
    if len(raw) == 2:
        return f"0000{raw[1]:02x}{raw[0]:02x}{BASE_UUID_SUFFIX}"
    if len(raw) == 16:
        b = raw[::-1]
        return (f"{b[0]:02x}{b[1]:02x}{b[2]:02x}{b[3]:02x}-{b[4]:02x}{b[5]:02x}-"
                f"{b[6]:02x}{b[7]:02x}-{b[8]:02x}{b[9]:02x}-"
                + "".join(f"{x:02x}" for x in b[10:]))
    return raw.hex()


def is_standard_uuid(u: str) -> bool:
    return u.endswith(BASE_UUID_SUFFIX)


def hexdump(data: bytes, limit: int = 64) -> str:
    shown = data[:limit]
    h = " ".join(f"{b:02x}" for b in shown)
    a = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in shown)
    tail = f" ...(+{len(data)-limit}B)" if len(data) > limit else ""
    return f"{h}  |{a}|{tail}"


# ---------- btsnoop 解析 ----------

def read_btsnoop(path_or_bytes):
    """产出 (timestamp, is_from_device, hci_payload) 三元组。"""
    if isinstance(path_or_bytes, bytes):
        data = path_or_bytes
    else:
        with open(path_or_bytes, "rb") as f:
            data = f.read()

    if not data.startswith(b"btsnoop\x00"):
        raise ValueError("不是 btsnoop 文件(缺少魔数)")

    version, datalink = struct.unpack(">II", data[8:16])
    pos = 16
    # btsnoop 时间戳:自公元0年1月1日起的微秒数
    EPOCH = datetime(2000, 1, 1)
    OFFSET = 0x00dcddb30f2f8000

    while pos + 24 <= len(data):
        olen, ilen, flags, drops, ts = struct.unpack(">IIIIq", data[pos:pos + 24])
        pos += 24
        if ilen < 0 or pos + ilen > len(data):
            break
        pkt = data[pos:pos + ilen]
        pos += ilen

        try:
            t = EPOCH + timedelta(microseconds=ts - OFFSET)
        except (OverflowError, OSError):
            t = None

        # flags bit0: 1 = controller->host (设备侧发来)
        from_device = bool(flags & 0x01)
        yield t, from_device, pkt


def extract_btsnoop_from_zip(zp):
    """从 bugreport zip 中找出 btsnoop 日志。"""
    found = []
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            ln = n.lower()
            if "btsnoop" in ln or ("bluetooth" in ln and ln.endswith(".log")):
                found.append((n, z.read(n)))
    return found


# ---------- HCI / L2CAP / ATT ----------

class GattExtractor:
    def __init__(self):
        self.reasm = {}          # handle -> 正在重组的 L2CAP 缓冲
        self.handle_uuid = {}    # att handle -> uuid
        self.services = []       # (start, end, uuid)
        self.chars = []          # (decl_handle, value_handle, props, uuid)
        self.events = []         # 协议时序
        self.mtu = None
        self.pending_read = {}   # 记录 READ_REQ 的 handle,便于把 RSP 关联回去

    def feed(self, ts, from_device, pkt):
        if len(pkt) < 1:
            return
        ptype = pkt[0]
        if ptype != 0x02:        # 只关心 ACL 数据
            return
        if len(pkt) < 5:
            return

        handle_flags, dlen = struct.unpack("<HH", pkt[1:5])
        conn = handle_flags & 0x0FFF
        pb = (handle_flags >> 12) & 0x03
        payload = pkt[5:5 + dlen]

        if pb == 0x01:           # continuing fragment
            if conn in self.reasm:
                self.reasm[conn] += payload
            else:
                return
        else:                    # first fragment
            self.reasm[conn] = payload

        buf = self.reasm[conn]
        if len(buf) < 4:
            return
        l2len, cid = struct.unpack("<HH", buf[:4])
        if len(buf) - 4 < l2len:
            return               # 还没收齐
        body = buf[4:4 + l2len]
        del self.reasm[conn]

        if cid == 0x0004:        # ATT
            self.parse_att(ts, from_device, conn, body)

    def parse_att(self, ts, from_device, conn, d):
        if not d:
            return
        op = d[0]
        name = ATT_OPS.get(op, f"UNKNOWN_0x{op:02X}")
        arg = d[1:]
        direction = "DEV->APP" if from_device else "APP->DEV"

        rec = {"ts": ts, "dir": direction, "op": name, "conn": conn, "raw": d}

        if op == 0x02 and len(arg) >= 2:
            rec["info"] = f"客户端请求 MTU = {struct.unpack('<H', arg[:2])[0]}"
        elif op == 0x03 and len(arg) >= 2:
            self.mtu = struct.unpack("<H", arg[:2])[0]
            rec["info"] = f"服务端接受 MTU = {self.mtu}"
        elif op == 0x11 and len(arg) >= 1:      # 服务发现响应
            ln = arg[0]
            items = arg[1:]
            svc = []
            for i in range(0, len(items) - ln + 1, ln):
                e = items[i:i + ln]
                if len(e) < 4:
                    break
                s, en = struct.unpack("<HH", e[:4])
                u = fmt_uuid(e[4:])
                self.services.append((s, en, u))
                svc.append(f"0x{s:04x}-0x{en:04x} {u}")
            rec["info"] = "服务: " + "; ".join(svc)
        elif op == 0x09 and len(arg) >= 1:      # 特征发现响应
            ln = arg[0]
            items = arg[1:]
            ch = []
            for i in range(0, len(items) - ln + 1, ln):
                e = items[i:i + ln]
                if len(e) < 5:
                    break
                decl = struct.unpack("<H", e[:2])[0]
                props = e[2]
                vh = struct.unpack("<H", e[3:5])[0]
                u = fmt_uuid(e[5:])
                self.chars.append((decl, vh, props, u))
                self.handle_uuid[vh] = u
                p = []
                if props & 0x02: p.append("read")
                if props & 0x04: p.append("write-no-rsp")
                if props & 0x08: p.append("write")
                if props & 0x10: p.append("notify")
                if props & 0x20: p.append("indicate")
                ch.append(f"h=0x{vh:04x} [{','.join(p)}] {u}")
            rec["info"] = "特征: " + "; ".join(ch)
        elif op in (0x12, 0x52) and len(arg) >= 2:   # 写
            h = struct.unpack("<H", arg[:2])[0]
            val = arg[2:]
            rec["handle"] = h
            rec["value"] = val
            u = self.handle_uuid.get(h, "?")
            rec["info"] = f"写 handle=0x{h:04x} ({u})"
        elif op in (0x1B, 0x1D) and len(arg) >= 2:   # 通知/指示
            h = struct.unpack("<H", arg[:2])[0]
            val = arg[2:]
            rec["handle"] = h
            rec["value"] = val
            u = self.handle_uuid.get(h, "?")
            rec["info"] = f"通知 handle=0x{h:04x} ({u})"
        elif op == 0x0A and len(arg) >= 2:
            h = struct.unpack("<H", arg[:2])[0]
            self.pending_read[conn] = h
            rec["handle"] = h
            rec["info"] = f"读 handle=0x{h:04x}"
        elif op == 0x0B:
            h = self.pending_read.get(conn)
            rec["value"] = arg
            if h is not None:
                rec["handle"] = h
            rec["info"] = "读响应"
        elif op == 0x01 and len(arg) >= 4:
            req_op, h, err = arg[0], struct.unpack("<H", arg[1:3])[0], arg[3]
            rec["info"] = (f"错误: 请求 {ATT_OPS.get(req_op, hex(req_op))} "
                           f"handle=0x{h:04x} -> {ATT_ERRS.get(err, hex(err))}")

        self.events.append(rec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="btsnoop_hci.log 或 bugreport.zip")
    ap.add_argument("--full", action="store_true", help="打印全部事件(含服务发现噪音)")
    ap.add_argument("--min-len", type=int, default=0, help="只显示 payload 不小于该长度的收发")
    args = ap.parse_args()

    sources = []
    if args.input.lower().endswith(".zip"):
        got = extract_btsnoop_from_zip(args.input)
        if not got:
            print("!! bugreport 里没找到 btsnoop 日志")
            return 1
        for n, b in got:
            print(f"[+] 从 zip 提取: {n}  ({len(b)} 字节)")
            sources.append(b)
    else:
        sources.append(args.input)

    ex = GattExtractor()
    total = 0
    for src in sources:
        try:
            for ts, from_dev, pkt in read_btsnoop(src):
                total += 1
                ex.feed(ts, from_dev, pkt)
        except ValueError as e:
            print(f"!! 解析失败: {e}")
            continue

    print(f"\n{'='*78}\n共解析 {total} 个 HCI 包,提取到 {len(ex.events)} 个 ATT 事件\n{'='*78}")

    # --- GATT 结构总览 ---
    if ex.services:
        print("\n### 发现的服务\n")
        seen = set()
        for s, e, u in ex.services:
            if u in seen:
                continue
            seen.add(u)
            mark = "" if is_standard_uuid(u) else "   <== 厂商自定义"
            print(f"  0x{s:04x}-0x{e:04x}  {u}{mark}")

    if ex.chars:
        print("\n### 发现的特征\n")
        seen = set()
        for decl, vh, props, u in ex.chars:
            if (vh, u) in seen:
                continue
            seen.add((vh, u))
            p = []
            if props & 0x02: p.append("read")
            if props & 0x04: p.append("write-no-rsp")
            if props & 0x08: p.append("write")
            if props & 0x10: p.append("notify")
            if props & 0x20: p.append("indicate")
            mark = "" if is_standard_uuid(u) else "  <== 厂商自定义"
            print(f"  handle=0x{vh:04x}  [{','.join(p):28s}]  {u}{mark}")

    if ex.mtu:
        print(f"\n### 协商 MTU = {ex.mtu} 字节")

    # --- 数据流时序(这才是协议逆向的核心) ---
    print(f"\n{'='*78}\n### 数据收发时序\n{'='*78}\n")
    noise = {"READ_BY_GROUP_REQ", "READ_BY_GROUP_RSP", "READ_BY_TYPE_REQ",
             "READ_BY_TYPE_RSP", "FIND_INFO_REQ", "FIND_INFO_RSP"}
    n = 0
    for r in ex.events:
        if not args.full and r["op"] in noise:
            continue
        val = r.get("value", b"")
        if args.min_len and len(val) < args.min_len:
            continue
        t = r["ts"].strftime("%H:%M:%S.%f")[:-3] if r["ts"] else "??"
        n += 1
        print(f"[{t}] {r['dir']}  {r['op']:16s} {r.get('info','')}")
        if val:
            print(f"           {hexdump(val, 96)}")
    if n == 0:
        print("(没有数据事件 —— 日志可能是在设备交互之前录的)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
