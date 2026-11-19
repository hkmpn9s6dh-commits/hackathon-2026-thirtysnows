"""出工作流图 out/workflow.png（1600×900）。

AARON 必交材料里点名要 "Diagrams of workflows, system architecture"。
这张图要一眼看出：一条指令进去，30 秒出来；每一段都有断言拦着。
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"

W, H = 1600, 900
BG = (251, 252, 253)
INK = (16, 22, 28)
MUTED = (108, 122, 134)
RULE = (214, 221, 227)
ACCENT = (33, 92, 158)
WARN = (161, 74, 32)


def f(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def main() -> int:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = f("segoeuil.ttf", 40)
    f_sub = f("segoeuil.ttf", 20)
    f_stage = f("segoeuib.ttf", 21)
    f_body = f("segoeuil.ttf", 16)
    f_mono = f("NotoSerifSC-VF.ttf", 15)
    f_small = f("segoeuil.ttf", 15)

    d.text((72, 54), "From seven stills to a 30-second commercial", font=f_title, fill=INK)
    d.text((74, 110), "One source file · five build stages · four gates · every claim checkable by a command",
           font=f_sub, fill=MUTED)

    # ---- 主干
    y, h = 270, 186
    stages = [
        ("01", "SINGLE SOURCE", "film.py", ["8 shots · 3 supers", "end card · 10 sound cues"]),
        ("02", "PLATES", "render.py --prep", ["crop generator mark", "→ 1920 × 1080"]),
        ("03", "FRAMES", "render.py --pipe", ["camera move · grade", "grain · typography"]),
        ("04", "SOUND", "audio.py → master", ["noise · modal · FFT reverb", "normalise −14 LUFS"]),
        ("05", "MASTER", "ffmpeg", ["H.264 crf16 · AAC 192k", "30.000 s · 24 fps"]),
    ]
    bw, gap, x0 = 254, 36, 72
    for i, (num, name, cmd, lines) in enumerate(stages):
        x = x0 + i * (bw + gap)
        d.rounded_rectangle([x, y, x + bw, y + h], radius=10, outline=RULE, width=2, fill=(255, 255, 255))
        d.text((x + 22, y + 18), num, font=f_body, fill=ACCENT)
        d.text((x + 22, y + 42), name, font=f_stage, fill=INK)
        d.text((x + 22, y + 80), cmd, font=f_mono, fill=ACCENT)
        for j, ln in enumerate(lines):
            d.text((x + 22, y + 116 + j * 26), ln, font=f_body, fill=MUTED)
        if i < len(stages) - 1:
            ax = x + bw + 8
            d.line([(ax, y + 93), (ax + 18, y + 93)], fill=RULE, width=2)
            d.polygon([(ax + 18, y + 93), (ax + 10, y + 88), (ax + 10, y + 98)], fill=RULE)

    # ---- 回路（从 05 底下绕回 01 底下，不压卡片）
    ly = y + h + 44
    d.line([(x0 + 4 * (bw + gap) + bw / 2, y + h), (x0 + 4 * (bw + gap) + bw / 2, ly)], fill=WARN, width=2)
    d.line([(x0 + 4 * (bw + gap) + bw / 2, ly), (x0 + bw / 2, ly)], fill=WARN, width=2)
    d.line([(x0 + bw / 2, ly), (x0 + bw / 2, y + h)], fill=WARN, width=2)
    d.polygon([(x0 + bw / 2, y + h), (x0 + bw / 2 - 6, y + h + 13), (x0 + bw / 2 + 6, y + h + 13)], fill=WARN)
    d.text((x0 + bw / 2 + 18, ly + 8),
           "change one line in film.py → rebuild the whole film in 6 minutes; same inputs give the same bytes",
           font=f_body, fill=WARN)

    # ---- 闸
    d.line([(72, 560), (W - 72, 560)], fill=RULE, width=1)
    gates = [
        ("GATE A", "Spec, 30-second script, five reference films", "before the first frame"),
        ("GATE B", "25 assertions: timeline · safe area · palette · type coverage", "written before the render"),
        ("GATE C", "Fresh clone, README only, no cache", "scripts/verify.sh exits 0"),
        ("GATE D", "Blind read by three models from three families, author hidden", "pass = 3 of 3 name the line"),
    ]
    for i, (name, what, crit) in enumerate(gates):
        ry = 590 + i * 56
        d.ellipse([72, ry + 7, 84, ry + 19], fill=ACCENT)
        d.text((100, ry), name, font=f_stage, fill=INK)
        d.text((196, ry + 5), what, font=f_body, fill=MUTED)
        d.text((1100, ry + 5), crit, font=f_small, fill=MUTED)

    d.text((72, 836), "7 stills · 8 shots · 720 frames · 1.44 M audio samples · 0 external assets",
           font=f_body, fill=MUTED)

    out = ROOT / "out" / "workflow.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
