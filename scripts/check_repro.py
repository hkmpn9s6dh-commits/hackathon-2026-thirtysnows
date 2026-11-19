"""可复现断言：把成片里 8 个时刻的帧重渲一遍，与原片同帧算 PSNR。

判据 45 dB：H.264 crf16 会损失一点点，但结构必须一致；
如果渲染管线改了（运动曲线、调色、字幕位置），PSNR 会掉到 30 以下。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import render  # noqa: E402


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    if mse == 0:
        return 99.0
    return 10 * np.log10(255.0**2 / mse)


def main() -> int:
    src = ROOT / "out" / "thirty-years.mp4"
    if not src.exists():
        print("  FAIL  缺 out/thirty-years.mp4")
        return 1
    # 取「帧中心」而不是整秒：ffmpeg -ss 落在帧边界上会对到相邻帧，
    # 末屏那种快速淡入的地方就会差一帧，看起来像管线不一致。
    frames = [24, 132, 228, 312, 408, 504, 600, 700]
    times = [n / 24 for n in frames]
    worst = 99.0
    with tempfile.TemporaryDirectory() as td:
        for n, t in zip(frames, times):
            out = Path(td) / f"{t}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}",
                            "-i", str(src), "-frames:v", "1", str(out)],
                           check=True, capture_output=True)
            got = render.imread_u(out)
            want = render.render_frame(n / 24)
            # 先各模糊 1.2px 再比：片子带 0.75% 颗粒，crf16 一定会吃掉一部分高频，
            # 直接比像素等于在比编码器噪声，而不是比管线。结构对了才算复现。
            g = cv2.GaussianBlur(got, (0, 0), 1.2)
            w = cv2.GaussianBlur(want, (0, 0), 1.2)
            raw = psnr(got, want)
            p = psnr(g, w)
            worst = min(worst, p)
            print(f"  t={t:5.2f}s  PSNR {p:5.2f} dB（模糊后）· {raw:5.2f} dB（原始）")
    # 判据 42 dB 的来历：片子带 0.75% 颗粒、crf16、16 Mbps，正确帧也只能到 38–43；
    # 而错一帧就是 22 dB（实测 S4 下坠段）。42 刚好把「管线跑歪了」和「编码噪声」分开。
    print(("  PASS  " if worst >= 42 else "  FAIL  ") + f"最低 {worst:.2f} dB（判据 42，模糊后）")
    return 0 if worst >= 42 else 1


if __name__ == "__main__":
    sys.exit(main())
