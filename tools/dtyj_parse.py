#!/usr/bin/env python3
"""
解析 A1 的 BABA/DTYJ 私有音频容器,并**用数据判定**帧排布。

背景
----
FINDINGS.md 第 11.3 节长期记着「尚未解出 data 块的边界与其中 Opus 帧的排布」。
公开项目 Shawn-TKD/dingtalk-a1-pc-tools 的 `tools/dtyj_to_ogg.py` 给出了一套
偏移量(fmt+12 采样率、fmt+24 记录长度、记录 = 4 字节前缀 + Opus 包)。

但那是**别人的结论**,而且他们的转换器不做解密 —— 与我实测「AES flag 默认为 1、
包体是密文」直接冲突。所以这里不照抄,而是把几种排布当作**假设**,拿真实文件
逐一检验,让数据自己说话。

判据(Opus TOC 字节)
-------------------
裸 Opus 每包首字节是 TOC:高 5 位 config、第 3 位 stereo、低 2 位 frame count。
同一路固定码率录音里,TOC 应当**高度集中**(理想情况下全同)。
若按某个假设切出来的首字节散布于 0..255,那这个假设就是错的
——或者包体是密文(那就谁也切不出结构)。

用法
----
    python dtyj_parse.py <file.dtyj>              # 解析 + 判定
    python dtyj_parse.py <file.dtyj> --ogg out.ogg  # 额外转封装
"""

import struct
import sys
from collections import Counter

# SILK/CELT 带宽与帧长,用于把 TOC 翻译成人话
_CONFIG = []
for _bw, _rates in (
    ("SILK-NB", (10, 20, 40, 60)),
    ("SILK-MB", (10, 20, 40, 60)),
    ("SILK-WB", (10, 20, 40, 60)),
    ("Hybrid-SWB", (10, 20)),
    ("Hybrid-FB", (10, 20)),
    ("CELT-NB", (2.5, 5, 10, 20)),
    ("CELT-WB", (2.5, 5, 10, 20)),
    ("CELT-SWB", (2.5, 5, 10, 20)),
    ("CELT-FB", (2.5, 5, 10, 20)),
):
    for _ms in _rates:
        _CONFIG.append((_bw, _ms))


def describe_toc(toc: int) -> str:
    """把 TOC 字节翻译成 配置/声道/帧数。"""
    cfg = toc >> 3
    stereo = (toc >> 2) & 1
    code = toc & 3
    bw, ms = _CONFIG[cfg] if cfg < len(_CONFIG) else ("?", 0)
    frames = {0: "1 帧", 1: "2 帧(等长)", 2: "2 帧(不等长)", 3: "任意帧数(带计数字节)"}[code]
    return f"config={cfg}({bw} {ms}ms) {'立体声' if stereo else '单声道'} {frames}"


# 真机 v1.7 文件上验证过的绝对偏移(来自客户端 BabaContainer.kt,
# 那套偏移是靠它查出"一批录音被截断"才反过来被证实的):
#
#    0  "BABA"      8  "DTYJ"     12 "ver " + v1.7
#   20  "fmt "     36  采样率     48  时长(ms)
#   52  "extr"
#   68  "data"     72  载荷长度   76  CRC32      80  载荷开始
#
# 注意 `data` 块**不是**标准 RIFF 块:长度之后还插了 4 字节 CRC 才到载荷。
# 按通用 RIFF 走法会把 CRC 当成载荷首 4 字节,导致后面每条记录都错位 4 字节。
DATA_CRC_EXTRA = 4
PAYLOAD_AT = 80


def parse_header(buf: bytes):
    """
    解析固定 80 字节头,并校验每个 tag 落在该落的位置。

    这**不是**通用 RIFF 解析。真机 v1.7 文件里三处都不标准:

      ① `ver ` 没有长度字段(tag 后直接跟 4 字节版本串);
      ② `fmt ` 的长度字段**写的是 0**,实际块体固定 24 字节;
      ③ `data` 的长度之后还插了 4 字节 CRC32 才到载荷。

    所以按"tag + size + body"去遍历必然跑飞 —— 实测会在 `fmt ` 处
    读到 size=0,然后把码率字节当成下一个 tag。正确做法是认死偏移,
    再用 tag 位置做自检。
    """
    if buf[:4] != b"BABA" or buf[8:12] != b"DTYJ":
        raise ValueError("不是 BABA/DTYJ 容器")

    expect = {12: b"ver ", 20: b"fmt ", 52: b"extr", 68: b"data"}
    bad = [(at, tag, buf[at : at + 4]) for at, tag in expect.items() if buf[at : at + 4] != tag]

    return {
        "declared_total": struct.unpack_from("<I", buf, 4)[0],
        "version": buf[16:20].decode("ascii", "replace"),
        "bitrate": struct.unpack_from("<I", buf, 32)[0],
        "sample_rate": struct.unpack_from("<I", buf, 36)[0],
        "frame_ms": buf[41],
        "bits": buf[43],
        "record_size": struct.unpack_from("<H", buf, 44)[0],
        "payload_len": struct.unpack_from("<I", buf, 72)[0],
        "crc32": struct.unpack_from("<I", buf, 76)[0],
        "tag_errors": bad,
    }


def try_layout(records: bytes, record_size: int, prefix_len: int):
    """
    按 (记录长度, 前缀长度) 切分,统计 TOC 集中度。

    返回 (首字节计数器, 前缀样本, 记录数)。集中度越高越可能是正确排布。
    """
    tocs = Counter()
    prefixes = []
    n = len(records) // record_size
    for i in range(n):
        rec = records[i * record_size : (i + 1) * record_size]
        if prefix_len:
            prefixes.append(rec[:prefix_len])
        payload = rec[prefix_len:]
        if payload:
            tocs[payload[0]] += 1
    return tocs, prefixes, n


def concentration(tocs: Counter) -> float:
    """最常见首字节占比。1.0 = 完全一致(强烈支持该排布)。"""
    total = sum(tocs.values())
    return (tocs.most_common(1)[0][1] / total) if total else 0.0


def _probe(data_body: bytes, record_sizes):
    """对每个候选记录长试 0 / 4 两种前缀,返回按可信度排序的结果并打印。"""
    out = []
    for rs in record_sizes:
        if not rs or len(data_body) < rs * 4:
            continue
        for pl in (0, 4):
            tocs, prefixes, n = try_layout(data_body, rs, pl)
            if not tocs:
                continue
            conc = concentration(tocs)
            top = tocs.most_common(1)[0][0]
            # 防退化:切偏了可能切出一串填充零,集中度同样 100%,
            # 但 0x00 不是合法 TOC。故「首字节非零」作次级判据。
            out.append(((conc, top != 0), rs, pl, top, n, prefixes))
            print(f"  记录={rs:<4} 前缀={pl}  记录数={n:<6} "
                  f"最常见首字节=0x{top:02x} 占 {conc:6.1%}")
    out.sort(reverse=True, key=lambda c: c[0])
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    path = sys.argv[1]
    with open(path, "rb") as f:
        buf = f.read()

    print(f"文件: {path}  ({len(buf)} 字节)")
    print("=" * 70)

    h = parse_header(buf)
    if h["tag_errors"]:
        print("  ! 标记位置不对(可能是别的固件版本):")
        for at, want, got in h["tag_errors"]:
            print(f"      @{at} 期望 {want!r} 实际 {got!r}")
    else:
        print("  头部标记全部就位: ver@12 fmt@20 extr@52 data@68 ✓")

    print(f"  版本 {h['version']}   码率 {h['bitrate']}   采样率 {h['sample_rate']} Hz")
    print(f"  帧长 {h['frame_ms']} ms   位深 {h['bits']}   记录长 {h['record_size']} 字节")
    print(f"  载荷长 {h['payload_len']}   CRC32 0x{h['crc32']:08x}")

    # 校验一:头里两个长度字段必须自洽
    implied = PAYLOAD_AT + h["payload_len"]
    declared = h["declared_total"] + 8
    print(f"\n  80 + 载荷长 = {implied}   BABA@4 + 8 = {declared}   "
          f"{'✓ 一致' if implied == declared else '✗ 差 %d' % (declared - implied)}")

    # 校验二:磁盘上的文件够不够长(截断检测,客户端就是靠这个发现半截录音的)
    if len(buf) < implied:
        pct = len(buf) / implied
        print(f"  ! 文件被截断: 只有 {len(buf)} 字节,应为 {implied}  (传下来 {pct:.0%})")
    data_body = buf[PAYLOAD_AT : PAYLOAD_AT + h["payload_len"]]
    if len(data_body) < h["payload_len"]:
        print(f"  ! 载荷不完整,按实际可用的 {len(data_body)} 字节继续分析")

    rec = h["record_size"]
    print(f"\ndata 载荷 {len(data_body)} 字节")
    if rec and len(data_body) % rec == 0:
        n_rec = len(data_body) // rec
        print(f"  能被记录长 {rec} 整除 → {n_rec} 条记录 ✓")
        if h["frame_ms"]:
            secs = n_rec * h["frame_ms"] / 1000.0
            print(f"  记录数 × {h['frame_ms']}ms = {secs:.1f} 秒 "
                  f"= {int(secs//3600)}h {int(secs%3600//60)}m {secs%60:04.1f}s"
                  f"   ← 应与界面显示的时长一致")
    elif rec:
        print(f"  ! 不能被 {rec} 整除(余 {len(data_body)%rec})")

    declared_rec = rec

    # ---- 判定排布 ----
    print("\n" + "=" * 70)
    print("排布判定(TOC 集中度越高越可信;密文会接近 0.004 = 1/256)")
    print("-" * 70)
    # 先只试头里声明的记录长(已在真机验证)。它成立就不必刷一屏候选;
    # 只有当它站不住时,才退回去把所有整除因子扫一遍找真相。
    trial = [declared_rec] if declared_rec else []
    candidates = _probe(data_body, trial)
    # 若声明值下的集中度已经低到 1/256 量级,那是**密文特征**,不是切错了 ——
    # 再扫一屏候选也只会得到同样的噪声,没有意义,直接下结论。
    top_conc = candidates[0][0][0] if candidates else 0.0
    ciphertext_like = bool(candidates) and top_conc < 0.05
    if not ciphertext_like and (not candidates or top_conc < 0.9):
        divisors = [d for d in range(40, 401) if len(data_body) % d == 0]
        if divisors:
            print(f"  (声明值不成立,回退扫描 {len(divisors)} 个整除因子)")
        candidates = _probe(data_body, sorted(set(divisors) | set(trial)))

    if not candidates:
        print("  没有可用候选")
        return 1
    candidates.sort(reverse=True, key=lambda c: c[0])
    (conc, _nonzero), rs, pl, top, n, prefixes = candidates[0]
    print("-" * 70)
    if conc >= 0.9:
        print(f"判定: 记录长度 {rs}、前缀 {pl} 字节 —— TOC 集中度 {conc:.1%}")
        print(f"      TOC 0x{top:02x} = {describe_toc(top)}")
        if pl and prefixes:
            uniq = Counter(prefixes)
            print(f"      前缀取值 {len(uniq)} 种,最常见: {uniq.most_common(3)}")
        print("\n  → 包体是**明文 Opus**,可以直接转封装成 Ogg。")
    else:
        print(f"判定: 所有假设的 TOC 都很分散(最高 {conc:.1%})。")
        print("      这与『AES flag=1、包体是密文』一致 —— 见 FINDINGS.md 第 12 节。")
        print("      密文无法靠切分还原,必须先经官方 openAudioFile(deviceSecret)解密。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
