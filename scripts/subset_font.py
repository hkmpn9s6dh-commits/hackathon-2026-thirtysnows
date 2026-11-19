"""把网页用到的字做成子集 woff2（中文界面必须随包带字体，不依赖系统字体）。

用法：py -3 scripts/subset_font.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "fonts" / "NotoSerifSC-VF.ttf"
HTML = ROOT / "web" / "index.html"
OUT = ROOT / "web" / "assets" / "noto-serif-subset.woff2"

BASIC = "".join(chr(c) for c in range(0x20, 0x7F))
PUNCT = "·—–…「」『』（）《》、。，：；！？％°±×÷≈≤≥"


def main() -> int:
    if not SRC.exists():
        print("缺字体", SRC)
        return 1
    text = HTML.read_text(encoding="utf-8")
    chars = set(text) | set(BASIC) | set(PUNCT) | set("0123456789")
    chars = {c for c in chars if c.strip()}
    print("subset chars:", len(chars))

    args = [
        str(SRC),
        f"--text={''.join(sorted(chars))}",
        "--flavor=woff2",
        "--layout-features=*",
        "--no-hinting",
        "--desubroutinize",
        f"--output-file={OUT}",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subset.main(args)

    f = TTFont(str(OUT), lazy=True)
    cmap = set()
    for t in f["cmap"].tables:
        cmap |= set(t.cmap.keys())
    missing = [c for c in chars if ord(c) not in cmap and not c.isspace()]
    if missing:
        print("缺字：", "".join(missing))
        return 1
    print("wrote", OUT, OUT.stat().st_size // 1024, "KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
