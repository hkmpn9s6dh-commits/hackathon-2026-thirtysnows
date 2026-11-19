"""出三张 case still（AARON 要求的 supporting visuals）。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import render  # noqa: E402

SHOTS = [
    (1.85, "still-snow"),     # S1 雪脊
    (12.60, "still-inside"),  # S4 岩层内部
    (25.40, "still-spring"),  # S7 泉眼与瓶
]


def main() -> int:
    out = ROOT / "out"
    out.mkdir(parents=True, exist_ok=True)
    for t, name in SHOTS:
        f = render.render_frame(t)
        p = out / f"{name}.png"
        render.imwrite_u(p, f)
        print("wrote", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
