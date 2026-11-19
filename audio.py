"""30 秒声音设计：全部由本文件合成，不引用任何外部音频。

原则：只做「风 / 石 / 水 / 一个低音钟」，不加音乐。原因是这条片子的主张是「时间」，
音乐会把时间说小；自然声 + 一条低频呼吸，才让 30 秒像一段真实的等待。
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

import film

SR = 48000
N = int(SR * film.DUR)
T = np.arange(N) / SR
ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------- utils
def rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def fft_band(x: np.ndarray, lo: float, hi: float, soft: float = 0.25) -> np.ndarray:
    """频域带通：边缘用升余弦过渡，避免时域振铃。"""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    mask = np.ones_like(f)
    if lo > 0:
        mask *= np.clip((f - lo * (1 - soft)) / (lo * soft + 1e-9), 0, 1)
    if hi < SR / 2:
        mask *= np.clip((hi * (1 + soft) - f) / (hi * soft + 1e-9), 0, 1)
    return np.fft.irfft(X * mask, n=len(x))


def env(points: list[tuple[float, float]]) -> np.ndarray:
    """分段线性包络，点之间用余弦插值，听起来没有折角。"""
    ts = np.array([p[0] for p in points], dtype=np.float64)
    vs = np.array([p[1] for p in points], dtype=np.float64)
    out = np.zeros(N, dtype=np.float64)
    idx = np.searchsorted(ts, T, side="right") - 1
    idx = np.clip(idx, 0, len(ts) - 2)
    t0, t1 = ts[idx], ts[idx + 1]
    v0, v1 = vs[idx], vs[idx + 1]
    u = np.clip((T - t0) / np.maximum(t1 - t0, 1e-9), 0, 1)
    u = 0.5 - 0.5 * np.cos(np.pi * u)
    out = v0 + (v1 - v0) * u
    out[T < ts[0]] = vs[0]
    out[T > ts[-1]] = vs[-1]
    return out


def place(buf: np.ndarray, sig: np.ndarray, at: float, gain: float = 1.0) -> None:
    i = int(at * SR)
    if i >= len(buf):
        return
    n = min(len(sig), len(buf) - i)
    buf[i : i + n] += sig[:n] * gain


def modal(f0: float, partials: list[tuple[float, float, float]], dur: float) -> np.ndarray:
    """模态合成：partials = [(倍频, 振幅, 衰减秒)]"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for mult, amp, tau in partials:
        out += amp * np.sin(2 * np.pi * f0 * mult * t + 0.11 * mult) * np.exp(-t / tau)
    return out


def reverb(x: np.ndarray, seconds: float = 2.4, mix: float = 0.55, seed: int = 3) -> np.ndarray:
    """FFT 卷积混响，IR 是指数衰减的去相关噪声。"""
    n_ir = int(seconds * SR)
    g = rng(seed)
    ir = g.normal(0, 1, n_ir) * np.exp(-np.arange(n_ir) / (SR * seconds / 6.5))
    ir = fft_band(ir, 180, 7000)
    ir[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    ir /= np.sqrt(np.sum(ir**2)) + 1e-9
    wet = np.fft.irfft(np.fft.rfft(x, n=len(x) + n_ir) * np.fft.rfft(ir, n=len(x) + n_ir),
                       n=len(x) + n_ir)[: len(x)]
    wet /= (np.max(np.abs(wet)) + 1e-9)
    return x * (1 - mix) + wet * mix * (np.max(np.abs(x)) + 1e-9) / (np.max(np.abs(wet)) + 1e-9)


# ---------------------------------------------------------------- beds
def wind(seed: int) -> np.ndarray:
    g = rng(seed)
    base = g.normal(0, 1, N)
    base = fft_band(base, 90, 1400)
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * 0.061 * T + 0.7) * np.sin(2 * np.pi * 0.017 * T)
    hiss = fft_band(rng(seed + 1).normal(0, 1, N), 1800, 6500) * 0.06
    return (base * gust + hiss) * env([(0, 0.55), (3.8, 0.50), (4.6, 0.06), (7.6, 0.04),
                                       (10.6, 0.02), (11.0, 0.0), (22.8, 0.0), (23.4, 0.30),
                                       (26.6, 0.36), (29.2, 0.0)])


def drone(seed: int) -> np.ndarray:
    base = np.sin(2 * np.pi * 38.0 * T) * 0.9
    base += np.sin(2 * np.pi * 57.0 * T + 0.4) * 0.45
    base += np.sin(2 * np.pi * 76.0 * T + 1.1) * 0.18
    base += fft_band(rng(seed).normal(0, 1, N), 20, 90) * 0.5
    return base * env([(0, 0.10), (4.0, 0.22), (7.5, 0.30), (11.0, 0.52), (15.0, 0.80),
                       (18.6, 0.95), (19.4, 0.42), (20.2, 0.26), (23.0, 0.22),
                       (26.8, 0.20), (29.0, 0.0)])


def rumble(seed: int) -> np.ndarray:
    x = fft_band(rng(seed).normal(0, 1, N), 25, 160)
    return x * env([(0, 0), (11.0, 0), (12.4, 0.55), (15.2, 0.62), (16.2, 0.42), (19.0, 0.30),
                    (20.2, 0.0), (30, 0.0)])


# ---------------------------------------------------------------- events
def crystal() -> np.ndarray:
    n = int(0.30 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f, a, tau in ((4200, 1.0, 0.045), (6100, 0.55, 0.030), (3300, 0.35, 0.060)):
        out += a * np.sin(2 * np.pi * f * t) * np.exp(-t / tau)
    out[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return out


def slip() -> np.ndarray:
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    g = rng(11)
    x = fft_band(g.normal(0, 1, n), 500, 5200)
    x *= np.exp(-t / 0.075)
    x[: int(0.006 * SR)] *= np.linspace(0, 1, int(0.006 * SR))
    tone = np.sin(2 * np.pi * (900 - 2600 * t) * t) * np.exp(-t / 0.09) * 0.25
    return x + tone


def bell() -> np.ndarray:
    return modal(110.0, [(1.0, 1.00, 5.2), (2.01, 0.42, 3.4), (2.98, 0.26, 2.4),
                         (4.07, 0.14, 1.5), (5.43, 0.08, 0.9)], 9.5)


def swell(seed: int) -> np.ndarray:
    n = int(2.6 * SR)
    x = fft_band(rng(seed).normal(0, 1, n), 120, 3800)
    e = np.concatenate([np.linspace(0, 1, int(1.1 * SR)) ** 2,
                        np.exp(-np.arange(n - int(1.1 * SR)) / (0.45 * SR))])
    return x * e[:n] / (np.max(np.abs(x * e[:n])) + 1e-9)


def fifth() -> np.ndarray:
    """A2 + E3 的持续音：锯齿过柔化，像一件被压得很低的弦。"""
    def saw(f: float) -> np.ndarray:
        x = np.zeros(N)
        for k in range(1, 9):
            x += np.sin(2 * np.pi * f * k * T + k * 0.3) / k
        return x

    vib = 1 + 0.0018 * np.sin(2 * np.pi * 5.1 * T) * np.clip((T - 24) / 2, 0, 1)
    tone = saw(110.0 * vib) * 0.6 + saw(164.81 * vib) * 0.4
    tone = fft_band(tone, 40, 900, 0.4)
    return tone * env([(0, 0), (23.0, 0), (24.8, 0.85), (26.6, 1.0), (28.2, 0.55), (29.4, 0.0)])


def pulses() -> np.ndarray:
    out = np.zeros(N)
    for i in range(2):
        n = int(0.5 * SR)
        t = np.arange(n) / SR
        x = np.sin(2 * np.pi * 62 * t) * np.exp(-t / 0.10)
        x[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))
        place(out, x, 15.5 + i * 2.0, 0.9)
    return out


# ---------------------------------------------------------------- mix
def build() -> np.ndarray:
    mono = np.zeros(N)
    for at, kind, p in film.AUDIO_EVENTS:
        g = p.get("gain", 1.0)
        if kind == "wind":
            mono += wind(1) * g
        elif kind == "drone":
            mono += drone(2) * g
        elif kind == "rumble":
            mono += rumble(3) * p.get("gain", 1.0) * 0.8
        elif kind == "pulse":
            mono += pulses() * g
        elif kind == "fifth":
            mono += fifth() * g
        else:
            sig = {"crystal": crystal, "slip": slip, "bell": bell,
                   "swell": lambda: swell(9), "tail": lambda: np.zeros(N)}[kind]()
            place(mono, sig if kind in ("swell",) else reverb(sig, 2.8, 0.6), at, g)

    # 立体声：右声道轻微延迟 + 去相关，得到宽度
    d = int(0.011 * SR)
    left = mono.copy()
    right = np.concatenate([np.zeros(d), mono[:-d]]) * 0.985
    right += fft_band(rng(21).normal(0, 1, N), 300, 4200) * 0.004
    st = np.stack([left, right], axis=1)
    st /= (np.max(np.abs(st)) + 1e-9)
    st *= 0.89  # 留 headroom，之后统一按 LUFS 归一
    return st


def write_wav(path: Path, st: np.ndarray) -> None:
    pcm = np.clip(st, -1, 1)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    out = ROOT / "out" / "audio.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    st = build()
    write_wav(out, st)
    print("wrote", out, st.shape, "peak", float(np.max(np.abs(st))))
