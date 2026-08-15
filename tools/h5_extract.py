#!/usr/bin/env python3
"""
从官方 mobile-recording H5 bundle 里提取「行为契约」。

目的不是抄它的代码,而是搞清楚:
  - 它通过哪些 JSAPI 桥调设备能力(对应我们已复刻的 A1 协议栈)
  - 它调哪些外部服务接口、什么参数(这些要替换成自建/可切换服务商)
  - 它的业务状态与数据字段(决定我们原生 UI 的数据模型)

bundle 是 webpack 压缩的单行文件,用正则按类别抽取,不做整段搬运。
"""
import re
import sys
import json
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parent.parent / "official_h5" / "web_assets" / \
    "g.alicdn.com" / "dingding" / "smart-hardware-ai-assistant" / "0.181.1"


PATTERNS = {
    # 钉钉 JSAPI / bridge 调用名
    "jsapi": r'["\']((?:biz|device|internal|runtime|util|ui)\.[a-zA-Z0-9.]{3,60})["\']',
    # mtop / 后端接口
    "mtop": r'["\']((?:mtop|dingtalk)\.[a-z0-9.]{5,80})["\']',
    # 我们已知的 dinger 能力名(从反编译 DingerInterface 得知的语义)
    "dinger_call": r'["\'](realStreamOperation|startAsr|stopAsr|needAsr|recordStart|recordStop|'
                   r'getFileList|downloadFile|deleteFile|deviceStatus|syncDevice|graySwitch|'
                   r'audioMode|voicePrint|incognito|openAp|closeAp|otaUpgrade)["\']',
    # 业务字段名(决定数据模型)
    "biz_field": r'["\'](fid|did|corpId|corp_id|deviceId|mediaId|audioId|recordId|taskId|'
                 r'transcript|translation|summary|chapters|speakers|keywords|todos|'
                 r'audio_status|storage_total_size|duration|stream_type|alg_mode)["\']',
    # 外部服务 URL
    "url": r'["\']((?:https?|wss?)://[a-zA-Z0-9._/-]{6,120})["\']',
    # 事件名
    "event": r'["\'](on[A-Z][a-zA-Z]{3,30})["\']',
}


def scan(path: Path) -> dict[str, Counter]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    out = {}
    for name, pat in PATTERNS.items():
        out[name] = Counter(m.group(1) for m in re.finditer(pat, text))
    return out


def main():
    targets = sorted(BASE.rglob("*.js"))
    # i18n 包只是文案,跳过
    targets = [p for p in targets if "i18n-" not in str(p)]
    if not targets:
        print(f"!! 没找到 bundle,检查路径: {BASE}")
        return 1

    merged = {k: Counter() for k in PATTERNS}
    per_file = {}
    for p in targets:
        r = scan(p)
        per_file[p.name] = r
        for k, c in r.items():
            merged[k].update(c)

    want = sys.argv[1] if len(sys.argv) > 1 else None
    for cat, counter in merged.items():
        if want and cat != want:
            continue
        items = counter.most_common(60)
        if not items:
            continue
        print(f"\n{'='*70}\n### {cat}  ({len(counter)} 种)\n{'='*70}")
        for val, n in items:
            print(f"  {n:5d}  {val}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
