"""成片规格断言：时长 / 画幅 / 帧率 / 编码。"""
from __future__ import annotations

import json
import subprocess
import sys


def main() -> int:
    p = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json",
                        "-show_format", "-show_streams", "out/thirty-years.mp4"],
                       capture_output=True, text=True)
    d = json.loads(p.stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    dur = float(d["format"]["duration"])
    num, den = v["r_frame_rate"].split("/")
    fps = float(num) / float(den)

    checks = [
        (abs(dur - 30.0) <= 0.04, f"时长 {dur:.3f}s ≈ 30.00s"),
        (v["width"] == 1920 and v["height"] == 1080, f"画幅 {v['width']}×{v['height']}"),
        (abs(fps - 24) < 0.01, f"帧率 {fps:.3f}"),
        (v["codec_name"] == "h264", f"视频编码 {v['codec_name']}"),
        (a is not None and a["codec_name"] == "aac", f"音频编码 {a['codec_name'] if a else '无'}"),
    ]
    ok = True
    for cond, msg in checks:
        print(("  PASS  " if cond else "  FAIL  ") + msg)
        ok = ok and cond
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
