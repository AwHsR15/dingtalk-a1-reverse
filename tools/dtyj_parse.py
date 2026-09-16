#!/usr/bin/env python3
"""
解析 A1 的 BABA/DTYJ 私有音频容器,并判定包体是明文还是密文。

容器头是固定 80 字节,长得像 RIFF 但有三处不标准(见 parse_header)。
头之后的载荷有两种形态:

  - **原始记录**:设备写出的原件,定长记录数组,每条 = 前缀 + 一个 Opus 包;
  - **官方已转换**:`OpusConvertToOgg` 保留 80 字节头,把载荷换成 Ogg 流
    (只重新封装,不解密)。

判据:Opus 包首字节(TOC)的**高 5 位 config**。同一路录音 config 恒定,
明文时集中度接近 100%;密文的首字节均匀分布,config 集中度落在
1/32 ≈ 3% 附近。只看 config 而不看整字节,是因为真实 Opus 的低 2 位
(帧数码)会合法地变化 —— 实测同一文件里 0x4B 和 0x48 交替出现。

用法
----
    python dtyj_parse.py <file>          # 可以只给文件开头一截(几十 KB 就够判定)
"""

import struct
import sys
from collections import Counter

PAYLOAD_AT = 80

# 真机 v1.7 / v1.6 文件上验证过的绝对偏移
#
#    0  "BABA"        4  u32  从偏移 8 到文件末尾的字节数
#    8  "DTYJ"
#   12  "ver "       16  "v1.7" / "v1.6"          ← ① 没有长度字段
#   20  "fmt "       24  u32  写的是 0             ← ② 实际块体固定 24 字节
#   32  u32 码率     36  u32 采样率
#   41  u8  帧长 ms  42  u8  声道   43  u8 位深
#   44  u16 记录长   46  u8  每条记录的前缀长度
#   48  u32 时长 ms
#   52  "extr"       56  u8   未知(实测 0 / 1 / 2)
#                    58  u8   **加密标志**(1 = 包体是 AES 密文)
#   60  8 字节全 0
#   68  "data"       72  u32  载荷字节数
#   76  u32 CRC32                                  ← ③ 长度后面多插了 CRC
#   80  载荷
#
# 三种真机变体(33 份样本):
#   v1.7  32 kbps / 16 kHz   前缀 4   Opus 包 80    记录 84
#   v1.7  64 kbps / 48 kHz   前缀 4   Opus 包 160   记录 164
#   v1.6  32 kbps / 16 kHz   前缀 0   Opus 包 80    记录 80
# 恒有  记录长 == 码率 × 帧长 / 8000 + 前缀长。

_BANDS = (
    [("SILK-NB", ms) for ms in (10, 20, 40, 60)]
    + [("SILK-MB", ms) for ms in (10, 20, 40, 60)]
    + [("SILK-WB", ms) for ms in (10, 20, 40, 60)]
    + [("Hybrid-SWB", ms) for ms in (10, 20)]
    + [("Hybrid-FB", ms) for ms in (10, 20)]
    + [(bw, ms) for bw in ("CELT-NB", "CELT-WB", "CELT-SWB", "CELT-FB") for ms in (2.5, 5, 10, 20)]
)


def describe_config(cfg: int) -> str:
    bw, ms = _BANDS[cfg] if 0 <= cfg < len(_BANDS) else ("?", 0)
    return f"config {cfg} = {bw} {ms}ms"


def parse_header(buf: bytes) -> dict:
    """
    解析固定 80 字节头,并校验每个 tag 落在该落的位置。

    这**不是**通用 RIFF 解析。真机文件里三处不标准:

      ① `ver ` 没有长度字段(tag 后直接跟 4 字节版本串);
      ② `fmt ` 的长度字段**写的是 0**,实际块体固定 24 字节;
      ③ `data` 的长度之后还插了 4 字节 CRC32 才到载荷。

    按"tag + size + body"遍历必然跑飞 —— 会在 `fmt ` 处读到 size=0,
    再把码率字节当成下一个 tag。正确做法是认死偏移,用 tag 位置自检。
    """
    if len(buf) < PAYLOAD_AT or buf[:4] != b"BABA" or buf[8:12] != b"DTYJ":
        raise ValueError("不是 BABA/DTYJ 容器")

    expect = {12: b"ver ", 20: b"fmt ", 52: b"extr", 68: b"data"}
    return {
        "declared_total": struct.unpack_from("<I", buf, 4)[0] + 8,
        "version": buf[16:20].decode("ascii", "replace"),
        "bitrate": struct.unpack_from("<I", buf, 32)[0],
        "sample_rate": struct.unpack_from("<I", buf, 36)[0],
        "frame_ms": buf[41],
        "channels": buf[42],
        "bits": buf[43],
        "record_size": struct.unpack_from("<H", buf, 44)[0],
        "prefix_len": buf[46],
        "duration_ms": struct.unpack_from("<I", buf, 48)[0],
        "payload_len": struct.unpack_from("<I", buf, 72)[0],
        "crc32": struct.unpack_from("<I", buf, 76)[0],
        # 33 份真机样本:@58=1 的 32 份全是密文,@58=0 的 1 份是明文。
        # 与按 TOC 测出来的判定逐一吻合 —— 但明文样本只有 1 份,仍需更多样本确认。
        "aes_flag": buf[58],
        "extr_56": buf[56],
        "tag_errors": [(at, t, buf[at:at + 4]) for at, t in expect.items() if buf[at:at + 4] != t],
    }


def ogg_packets(buf: bytes, start: int = PAYLOAD_AT):
    """从 start 起按 Ogg 页拆包。遇到不完整的页就停(允许只给文件开头一截)。"""
    packets, cur, i = [], b"", start
    while i + 27 <= len(buf) and buf[i:i + 4] == b"OggS":
        nseg = buf[i + 26]
        lacing = buf[i + 27:i + 27 + nseg]
        j = i + 27 + nseg
        for n in lacing:
            cur += buf[j:j + n]
            j += n
            if n < 255:
                packets.append(cur)
                cur = b""
        i = j
    return packets


def record_packets(buf: bytes, h: dict):
    """按头里声明的 记录长 / 前缀长 切原始记录,返回 Opus 包列表(只取完整记录)。"""
    rec, pre = h["record_size"], h["prefix_len"]
    if rec <= pre:
        return [], []
    body = buf[PAYLOAD_AT:PAYLOAD_AT + h["payload_len"]]
    n = len(body) // rec
    recs = [body[k * rec:(k + 1) * rec] for k in range(n)]
    return [r[pre:] for r in recs], [r[:pre] for r in recs]


def config_concentration(packets) -> tuple:
    """(最常见 config, 占比)。明文 → 接近 1.0;密文 → 接近 1/32。"""
    cfgs = Counter(p[0] >> 3 for p in packets if p)
    if not cfgs:
        return None, 0.0
    top, n = cfgs.most_common(1)[0]
    return top, n / sum(cfgs.values())


def classify(buf: bytes) -> dict:
    """解析 + 判定,返回结构化结果(供测试与批量脚本使用)。"""
    h = parse_header(buf)
    if buf[PAYLOAD_AT:PAYLOAD_AT + 4] == b"OggS":
        layout = "ogg"
        pk = ogg_packets(buf)
        audio = [p for p in pk if not p.startswith((b"OpusHead", b"OpusTags"))]
        prefixes = []
    else:
        layout = "records"
        audio, prefixes = record_packets(buf, h)

    cfg, conc = config_concentration(audio)
    if len(audio) < 50:
        verdict = "样本不足"
    elif conc >= 0.9:
        verdict = "明文"
    elif conc <= 0.1:
        verdict = "密文"
    else:
        verdict = "无法判定"
    return {**h, "layout": layout, "packets": len(audio), "config": cfg,
            "concentration": conc, "verdict": verdict, "prefixes": prefixes}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    with open(path, "rb") as f:
        buf = f.read()

    r = classify(buf)
    print(f"文件: {path}  (读入 {len(buf)} 字节)")
    print("=" * 70)
    if r["tag_errors"]:
        for at, want, got in r["tag_errors"]:
            print(f"  ! @{at} 期望 {want!r} 实际 {got!r}(可能是没见过的固件版本)")
    else:
        print("  头部标记就位: ver@12 fmt@20 extr@52 data@68 ✓")
    print(f"  版本 {r['version']}   {r['bitrate']} bps / {r['sample_rate']} Hz / "
          f"{r['channels']} 声道 / {r['bits']} bit / 帧长 {r['frame_ms']} ms")
    opus = r["record_size"] - r["prefix_len"]
    expect_opus = r["bitrate"] * r["frame_ms"] // 8000
    print(f"  记录长 {r['record_size']} = 前缀 {r['prefix_len']} + Opus 包 {opus}"
          f"   (码率推算 {expect_opus} {'✓' if opus == expect_opus else '✗'})")
    print(f"  加密标志(@58) = {r['aes_flag']}   @56 = {r['extr_56']}(含义未知)")
    print(f"  头里时长 {r['duration_ms'] / 1000:.1f} 秒   载荷 {r['payload_len']} 字节   CRC32 0x{r['crc32']:08x}")

    if r["payload_len"] and r["record_size"] and r["frame_ms"]:
        secs = r["payload_len"] // r["record_size"] * r["frame_ms"] / 1000
        print(f"  载荷记录数 × 帧长 = {secs:.1f} 秒(原始记录形态下应与头里时长吻合)")

    total = r["declared_total"]
    if len(buf) < total:
        print(f"  注意: 只读入了 {len(buf)} / {total} 字节"
              f"({len(buf) / total:.0%})—— 若这是完整文件,说明它被截断了")

    print("-" * 70)
    form = "官方已转换(BABA 头 + Ogg 流)" if r["layout"] == "ogg" else "原始记录"
    print(f"  载荷形态: {form}   取到 {r['packets']} 个 Opus 包")
    if r["config"] is not None:
        print(f"  主 config: {describe_config(r['config'])},占 {r['concentration']:.1%}")
    print(f"  判定: **{r['verdict']}**")
    flag_says = "密文" if r["aes_flag"] else "明文"
    if r["verdict"] in ("明文", "密文"):
        agree = "✓ 与加密标志一致" if flag_says == r["verdict"] else "✗ 与加密标志矛盾,请把这个样本记下来"
        print(f"    {agree}")
    if r["verdict"] == "明文":
        print("    → 可直接转封装成标准 Ogg Opus 播放。")
    elif r["verdict"] == "密文":
        print("    → 标准解码器只能解出噪声,需经官方 openAudioFile(deviceSecret) 解密。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
