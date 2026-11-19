"""把 out/audio.wav 归一化到 -14 LUFS（±0.3），真峰 ≤ -1.5 dBTP。

做法：测 → 加增益 → 限幅 → 再测，最多 4 轮。限幅器是瞬时攻击 + 缓释，
不会把低频钟的起振削平。
"""
from __future__ import annotations

import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR = 48000
TARGET = -14.0
CEIL_DB = -1.5


def read_wav(p: Path) -> np.ndarray:
    with wave.open(str(p), "rb") as w:
        assert w.getnchannels() == 2 and w.getsampwidth() == 2
        n = w.getnframes()
        raw = w.readframes(n)
    x = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    return x.reshape(-1, 2)


def write_wav(p: Path, x: np.ndarray) -> None:
    pcm = (np.clip(x, -1, 1) * 32767.0).astype("<i2")
    with wave.open(str(p), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def measure(p: Path) -> tuple[float, float]:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(p), "-af",
                          "loudnorm=I=-14:TP=-1.5:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", out, re.S)
    if not m:
        raise SystemExit("测不出响度：\n" + out[-1500:])
    import json
    d = json.loads(m.group(0))
    return float(d["input_i"]), float(d["input_tp"])


def limiter(x: np.ndarray, ceil_db: float = -2.2) -> np.ndarray:
    """前视限幅：先把增益按 15ms 窗口取最小值（提前压），再平滑。

    没有前视的限幅器压不住瞬态——上一版就是把钟的起振原样放过去了。
    """
    ceil = 10 ** (ceil_db / 20)
    a = np.abs(x).max(axis=1)
    g = np.minimum(1.0, ceil / np.maximum(a, 1e-9))

    L = int(0.015 * SR)
    nb = int(np.ceil(len(g) / L))
    pad = np.ones(nb * L)
    pad[: len(g)] = g
    blocks = pad.reshape(nb, L).min(axis=1)
    # 每个样本取本块与下一块的最小值 = 最多提前 15ms 压
    nxt = np.concatenate([blocks[1:], [1.0]])
    per_block = np.minimum(blocks, nxt)
    g2 = np.repeat(per_block, L)[: len(g)]

    alpha = 1 - np.exp(-1.0 / (0.004 * SR))
    sm = np.empty_like(g2)
    acc = 1.0
    for i in range(len(g2)):
        acc += alpha * (g2[i] - acc)
        sm[i] = min(acc, g2[i])
    return x * sm[:, None]


def main() -> int:
    src = ROOT / "out" / "audio.wav"
    if not src.exists():
        raise SystemExit("先跑 python audio.py")
    x = read_wav(src)
    tmp = ROOT / "out" / ".master.wav"
    gain_db = 0.0
    for attempt in range(4):
        y = x * (10 ** (gain_db / 20))
        y = limiter(y)
        write_wav(tmp, y)
        lufs, tp = measure(tmp)
        print(f"round {attempt}: gain {gain_db:+.2f} dB -> {lufs:.2f} LUFS, TP {tp:.2f} dBFS")
        if abs(lufs - TARGET) <= 0.3 and tp <= CEIL_DB + 0.1:
            dst = ROOT / "out" / "audio-master.wav"
            write_wav(dst, y)
            print("wrote", dst)
            tmp.unlink(missing_ok=True)
            return 0
        gain_db += (TARGET - lufs)
    raise SystemExit("4 轮还没收敛，检查素材")


if __name__ == "__main__":
    sys.exit(main())
