"""把关键帧渲成 30 秒片子：镜头运动、叠化、调色、颗粒、字幕、末屏。

用法：
  python render.py --frames out/frames            # 只出帧序列（png，用于核对）
  python render.py --pipe                          # 直接喂 ffmpeg（build.py 用）
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import film

ROOT = Path(__file__).resolve().parent
PLATES = ROOT / "keyframes" / "plate"
CACHE = ROOT / ".cache"
FONTS = ROOT / "assets" / "fonts"

CN_SERIF = FONTS / "NotoSerifSC-VF.ttf"
CN_HEAVY = FONTS / "SourceHanSerifSC-Heavy.ttf"
EN_LIGHT = FONTS / "segoeuil.ttf"

WATERMARK_CROP = 0.082  # 生成器右下角水印：右边与下边各去 8.2%，再放大到 1920×1080


# ---------------------------------------------------------------- plates
def prep_plates() -> None:
    """裁掉生成器水印并统一到 1920×1080。只做一次，结果可复现。"""
    PLATES.mkdir(parents=True, exist_ok=True)
    for s in film.SHOTS:
        if not s.src:
            continue
        dst = PLATES / f"{s.key}.png"
        if dst.exists():
            continue
        im = Image.open(ROOT / s.src).convert("RGB")
        w, h = im.size
        cw, ch = int(w * (1 - WATERMARK_CROP)), int(h * (1 - WATERMARK_CROP))
        im = im.crop((0, 0, cw, ch)).resize((film.W, film.H), Image.LANCZOS)
        bgr = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2BGR)
        if s.key == "k7_bottle":
            bgr = add_label(bgr)
        imwrite_u(dst, bgr)
        print(f"plate {s.key}: {w}x{h} -> {film.W}x{film.H}")


def imread_u(path: Path) -> np.ndarray:
    """Windows 上路径含中文时 cv2.imread 会失败，统一走 fromfile。"""
    buf = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"读不出图片：{path}")
    return img


def imwrite_u(path: Path, img: np.ndarray) -> None:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise SystemExit(f"写不出图片：{path}")
    buf.tofile(str(path))


def add_label(plate_bgr: np.ndarray) -> np.ndarray:
    """在空白标签上排版：竖排「长白雪」+ 小字副名 + 一条细线。

    生成器画不出可靠的中文，所以字一律由代码排——这也是「单一来源」的一部分：
    改标签只要改 film.LABEL_TEXT。
    """
    x0, y0, x1, y1 = film.LABEL_BOX
    X0, Y0, X1, Y1 = int(x0 * film.W), int(y0 * film.H), int(x1 * film.W), int(y1 * film.H)
    img = Image.fromarray(cv2.cvtColor(plate_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ink = (38, 44, 50, 232)
    thin = (70, 78, 86, 150)

    # 细线（标签上缘内侧）
    d.line([(X0 + 34, Y0 + 46), (X1 - 34, Y0 + 46)], fill=thin, width=2)

    # 竖排主名
    f_main = font(CN_SERIF, 52)
    cw = (X1 - X0)
    cx = X0 + cw * 0.52
    y = Y0 + 128
    for ch in film.LABEL_TEXT[0]:
        d.text((cx, y), ch, font=f_main, fill=ink, anchor="ma")
        y += 64

    # 副名：竖排小字，靠右
    f_sub = font(CN_SERIF, 15)
    y2 = Y0 + 250
    for ch in film.LABEL_TEXT[1]:
        d.text((X1 - 46, y2), ch, font=f_sub, fill=(60, 68, 76, 190), anchor="ma")
        y2 += 19

    # 标签底缘的一条短线
    d.line([(cx - 22, Y1 - 84), (cx + 22, Y1 - 84)], fill=thin, width=2)

    out = Image.alpha_composite(img, layer).convert("RGB")
    return cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR)


def load_plate(key: str) -> np.ndarray:
    p = PLATES / f"{key}.png"
    if not p.exists():
        raise SystemExit(f"缺少 plate {p}，先跑 python render.py --prep")
    return imread_u(p)


# ---------------------------------------------------------------- easing
def smooth(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 3


# ---------------------------------------------------------------- grade
_VIGNETTE: np.ndarray | None = None


def vignette() -> np.ndarray:
    global _VIGNETTE
    if _VIGNETTE is None:
        yy, xx = np.mgrid[0 : film.H, 0 : film.W].astype(np.float32)
        nx = (xx - film.W / 2) / (film.W / 2)
        ny = (yy - film.H / 2) / (film.H / 2)
        r = np.sqrt(nx * nx + ny * ny) / math.sqrt(2)
        _VIGNETTE = (1.0 - 0.28 * r**2.1).clip(0.55, 1.0)[..., None]
    return _VIGNETTE


_GAIN = np.array([1.055, 1.005, 0.965], dtype=np.float32)  # BGR：偏冷
_LIFT = np.array([0.014, 0.011, 0.009], dtype=np.float32)

_NOISE = [np.random.default_rng(7 + i).normal(0, 1, (film.H // 2, film.W // 2)).astype(np.float32) for i in range(5)]


def grade(img: np.ndarray, shot_idx: int, frame_idx: int) -> np.ndarray:
    x = img.astype(np.float32) / 255.0
    x = np.power(x, 1.03)
    x = x * _GAIN + _LIFT
    x = x * vignette()
    n = _NOISE[frame_idx % len(_NOISE)]
    n = cv2.resize(n, (film.W, film.H), interpolation=cv2.INTER_LINEAR)
    x = x + (n * 0.0075)[..., None]
    return (np.clip(x, 0.0, 1.0) * 255.0).astype(np.uint8)


# ---------------------------------------------------------------- text
_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    k = (str(path), size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(str(path), size)
    return _font_cache[k]


def tracked_size(text: str, f: ImageFont.FreeTypeFont, tracking: float) -> tuple[float, float]:
    w = sum(f.getlength(ch) for ch in text) + tracking * max(0, len(text) - 1)
    a, d = f.getmetrics()
    return w, a + d


def draw_tracked(d: ImageDraw.ImageDraw, xy: tuple[float, float], text: str,
                 f: ImageFont.FreeTypeFont, fill, tracking: float, center: bool = False) -> tuple[float, float]:
    w, h = tracked_size(text, f, tracking)
    x, y = xy
    if center:
        x -= w / 2
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += f.getlength(ch) + tracking
    return w, h


def text_layer(spec: list[tuple]) -> Image.Image:
    """spec: [(text, fontpath, size, tracking, y, alpha, kind)] -> RGBA 图层"""
    layer = Image.new("RGBA", (film.W, film.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for text, fp, size, tracking, y, alpha, kind in spec:
        f = font(fp, size)
        a = int(255 * alpha)
        if kind == "cn":
            draw_tracked(d, (film.W * 0.5, y), text, f, (255, 255, 255, a), tracking, center=True)
        elif kind == "en":
            draw_tracked(d, (film.W * 0.5, y), text, f, (255, 255, 255, int(a * 0.72)), tracking, center=True)
    return layer


def super_layer(cn: str, en: str, x: float, y: float) -> Image.Image:
    layer = Image.new("RGBA", (film.W, film.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    px, py = int(film.W * x), int(film.H * y)
    fcn, fen = font(CN_SERIF, 34), font(EN_LIGHT, 18)
    draw_tracked(d, (px, py), cn, fcn, (255, 255, 255, 236), 3.2)
    draw_tracked(d, (px, py + 30), en, fen, (255, 255, 255, 150), 4.4)
    return layer


_SUPER_CACHE: dict[str, Image.Image] = {}


def get_super(s: film.Super) -> Image.Image:
    k = s.cn
    if k not in _SUPER_CACHE:
        _SUPER_CACHE[k] = super_layer(s.cn, s.en, s.x, s.y)
    return _SUPER_CACHE[k]


def alpha_of(t: float, t_in: float, t_out: float, fade: float = 0.36) -> float:
    if t < t_in or t > t_out:
        return 0.0
    return min(1.0, (t - t_in) / fade, (t_out - t) / fade)


def composite(base: np.ndarray, layer: Image.Image, a: float) -> np.ndarray:
    if a <= 0.001:
        return base
    arr = np.array(layer, dtype=np.float32)
    rgb, al = arr[..., :3], (arr[..., 3:4] / 255.0) * a
    out = base.astype(np.float32) * (1 - al) + rgb * al
    return out.astype(np.uint8)


# ---------------------------------------------------------------- frames
def camera_frame(plate: np.ndarray, s: film.Shot, u: float) -> np.ndarray:
    e = smooth(u)
    z = s.z0 + (s.z1 - s.z0) * e
    cx = s.cx0 + (s.cx1 - s.cx0) * e
    cy = s.cy0 + (s.cy1 - s.cy0) * e
    cw, chh = film.W / z, film.H / z
    cx_px = min(max(cx * film.W, cw / 2), film.W - cw / 2)
    cy_px = min(max(cy * film.H, chh / 2), film.H - chh / 2)
    crop = cv2.getRectSubPix(plate, (int(round(cw)), int(round(chh))),
                             (cx_px, cy_px))
    return cv2.resize(crop, (film.W, film.H), interpolation=cv2.INTER_CUBIC)


_YROW = np.arange(film.H, dtype=np.float32)[:, None]


def light_sweep(img: np.ndarray, shot: "film.Shot", t: float) -> np.ndarray:
    """一条光带贴着岩壁往下走：让「时间在走」看得见，而不是只写在字幕上。

    只给下坠的三段（S4/S5/S6）。进出为零，不留接缝。
    """
    if shot.idx not in (4, 5, 6):
        return img
    u = min(1.0, max(0.0, (t - shot.start) / shot.dur))
    yc = (-0.25 + 1.5 * u) * film.H
    sigma = 0.20 * film.H
    band = np.exp(-0.5 * ((_YROW - yc) / sigma) ** 2)
    amp = (0.22 if shot.idx == 5 else 0.16) * np.sin(np.pi * u)
    add = band * amp * 255.0
    out = img.astype(np.float32) + add[..., None] * np.array([1.04, 1.01, 0.97], np.float32)
    return np.clip(out, 0, 255).astype(np.uint8)


def endcard_frame(t: float, with_text: bool = True) -> np.ndarray:
    img = Image.new("RGB", (film.W, film.H), (6, 8, 11))
    if not with_text:
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    d = ImageDraw.Draw(img)
    e = film.ENDCARD
    rel = t - e["t_start"]

    def fade(t_in: float, dur: float = 0.7) -> float:
        return min(1.0, max(0.0, (rel - t_in) / dur))

    a1 = fade(e["lines"][0][0])
    if a1 > 0:
        f = font(CN_SERIF, e["lines"][0][2])
        draw_tracked(d, (film.W * 0.5, film.H * 0.385), e["lines"][0][1], f,
                     (238, 242, 246, int(255 * a1)), 4.0, center=True)
    a1e = fade(e["en"][0])
    if a1e > 0:
        fe = font(EN_LIGHT, 15)
        draw_tracked(d, (film.W * 0.5, film.H * 0.435), e["en"][1], fe,
                     (200, 210, 220, int(170 * a1e)), 5.2, center=True)

    al = fade(e["lockup"][0], 0.8)
    if al > 0:
        f = font(CN_HEAVY, 62)
        draw_tracked(d, (film.W * 0.5, film.H * 0.575), e["lockup"][1], f,
                     (252, 252, 252, int(255 * al)), 8.0, center=True)
        d.line([(film.W * 0.5 - 26, film.H * 0.600), (film.W * 0.5 + 26, film.H * 0.600)],
               fill=(255, 255, 255, int(120 * al)), width=1)
        f2 = font(CN_SERIF, 26)
        draw_tracked(d, (film.W * 0.5, film.H * 0.644), e["lockup"][2], f2,
                     (235, 240, 245, int(235 * al)), 6.0, center=True)
        f3 = font(CN_SERIF, 16)
        draw_tracked(d, (film.W * 0.5, film.H * 0.688), e["lockup"][3], f3,
                     (222, 229, 236, int(210 * al)), 3.4, center=True)

    asl = fade(e["slogan"][0], 0.8)
    if asl > 0:
        fs = font(CN_SERIF, 21)
        draw_tracked(d, (film.W * 0.5, film.H * 0.765), e["slogan"][1], fs,
                     (232, 238, 244, int(205 * asl)), 2.2, center=True)

    ad = fade(e["disclaimer"][0], 0.8)
    if ad > 0:
        fd = font(CN_SERIF, 14)
        draw_tracked(d, (film.W * 0.5, film.H * 0.928), e["disclaimer"][1], fd,
                     (212, 220, 228, int(165 * ad)), 1.3, center=True)

    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def render_frame(t: float, with_text: bool = True) -> np.ndarray:
    s = film.shot_at(t)
    if s.key == "endcard":
        return endcard_frame(t, with_text)

    u = (t - s.start) / s.dur
    plate = load_plate(s.key)
    frame = camera_frame(plate, s, u)
    frame = grade(frame, s.idx, film.frame_at(t))
    frame = light_sweep(frame, s, t)

    if s.fade_in > 0 and (t - s.start) < s.fade_in:
        prev = film.SHOTS[s.idx - 2]
        if prev.key != "endcard":
            pp = camera_frame(load_plate(prev.key), prev, 1.0)
            pp = grade(pp, prev.idx, film.frame_at(t))
            a = smooth((t - s.start) / s.fade_in)
            frame = cv2.addWeighted(frame, a, pp, 1 - a, 0)

    if with_text:
        for sp in film.SUPERS:
            a = alpha_of(t, sp.t_in, sp.t_out)
            if a > 0:
                frame = composite(frame, get_super(sp), a)
    return frame


# ---------------------------------------------------------------- main
def ffmpeg_cmd(out: Path, with_audio: Path | None) -> list[str]:
    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
           "-s", f"{film.W}x{film.H}", "-r", str(film.FPS), "-i", "-"]
    if with_audio:
        cmd += ["-i", str(with_audio)]
    # 不加 -movflags +faststart：这台机器上末尾重写 moov 会把 mp4 写坏（见过的坑）。
    # 30 秒的片子不需要边下边播，页面直接整段加载。
    # 显式写死色彩管线：不写的话 ffmpeg 按 limited range + 默认矩阵转，
    # 解回来黑位会整体掉 3-4 级（实测 B-3 G-2 R-4），暗部细节被吃掉。
    cmd += ["-vf", "scale=in_range=full:out_range=pc:out_color_matrix=bt709",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-color_range", "pc",
            "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-tune", "film"]
    if with_audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [str(out)]
    return cmd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep", action="store_true")
    ap.add_argument("--frames", type=str)
    ap.add_argument("--pipe", action="store_true")
    ap.add_argument("--out", type=str, default="out/thirty-years.mp4")
    ap.add_argument("--audio", type=str, default=None)
    args = ap.parse_args()

    if args.prep:
        prep_plates()
        return 0

    if args.frames:
        d = Path(args.frames)
        d.mkdir(parents=True, exist_ok=True)
        for i in range(film.TOTAL_FRAMES):
            cv2.imwrite(str(d / f"{i:04d}.png"), render_frame(i / film.FPS))
            if i % 48 == 0:
                print("frame", i)
        return 0

    if args.pipe:
        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        audio = ROOT / args.audio if args.audio else None
        log = (ROOT / "out" / "ffmpeg.log").open("wb")
        proc = subprocess.Popen(ffmpeg_cmd(out, audio), stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=log)
        assert proc.stdin is not None
        for i in range(film.TOTAL_FRAMES):
            proc.stdin.write(render_frame(i / film.FPS).tobytes())
            if i % 96 == 0:
                print("frame", i, flush=True)
        proc.stdin.close()
        rc = proc.wait()
        log.close()
        if rc != 0:
            print((ROOT / "out" / "ffmpeg.log").read_text(encoding="utf-8", errors="replace")[-3000:])
            return rc
        print("wrote", out)
        return 0

    print("nothing to do; try --prep / --frames / --pipe")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
