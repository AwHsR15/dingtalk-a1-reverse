#!/usr/bin/env python3
"""
抽取官方 H5 里指定关键词周围的代码上下文,用来还原调用参数与业务逻辑。

压缩后的 bundle 没有换行,直接看无从下手;这里按关键词定位后取前后若干字符,
再做轻度可读化(在语句分隔处断行),足够看清参数结构和分支逻辑。
仅用于理解行为契约,不做代码搬运。

用法:
    python h5_context.py <关键词> [前后字符数] [最多几处]
"""
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "official_h5" / "web_assets" / \
    "g.alicdn.com" / "dingding" / "smart-hardware-ai-assistant" / "0.181.1"


def humanize(s: str) -> str:
    """在语句边界插换行,让压缩代码勉强可读。"""
    s = re.sub(r'([;{}])', r'\1\n', s)
    s = re.sub(r'\n{2,}', '\n', s)
    return s


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    kw = sys.argv[1]
    span = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    files = [p for p in sorted(BASE.rglob("*.js")) if "i18n-" not in str(p)]
    shown = 0
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(re.escape(kw), text):
            if shown >= limit:
                return 0
            a = max(0, m.start() - span)
            b = min(len(text), m.end() + span)
            print(f"\n{'='*74}\n# {p.name}  @{m.start()}\n{'='*74}")
            print(humanize(text[a:b]))
            shown += 1
    if shown == 0:
        print(f"(没有命中 {kw})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
