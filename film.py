"""单一真相源：《三十年前的雪》30 秒 spec TVC。

改片子只改这个文件：镜头、字幕、末屏、声音事件都在这里。
docs/02-SCRIPT.md 由 `python film.py --doc` 生成，`--check` 反向核对。
"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

W, H, FPS = 1920, 1080, 24
DUR = 30.0
TOTAL_FRAMES = int(round(DUR * FPS))  # 720

BRAND = "农夫山泉 · 长白雪"
TITLE_CN = "三十年前的雪"
TITLE_EN = "THIRTY YEARS"


@dataclasses.dataclass(frozen=True)
class Shot:
    idx: int
    key: str
    src: str
    dur: float
    z0: float
    z1: float
    cx0: float
    cx1: float
    cy0: float
    cy1: float
    fade_in: float = 0.0   # 与上一镜的叠化，秒
    note: str = ""

    @property
    def start(self) -> float:
        return sum(s.dur for s in SHOTS[: self.idx - 1])

    @property
    def end(self) -> float:
        return self.start + self.dur

    @property
    def frames(self) -> int:
        return int(round(self.dur * FPS))


SHOTS: list[Shot] = [
    Shot(1, "k1_ridge", "keyframes/raw/k1_ridge.png", 4.0, 1.00, 1.10, 0.50, 0.52, 0.50, 0.455,
         note="长白山脊，蓝调，风抽雪成一条烟。极缓推近。"),
    Shot(2, "k2_flake", "keyframes/raw/k2_flake.png", 3.5, 1.07, 1.00, 0.50, 0.51, 0.50, 0.505,
         note="微距：雪花落在玄武岩上，融成一颗珠。"),
    Shot(3, "k3_bead", "keyframes/raw/k3_bead.png", 3.5, 1.00, 1.16, 0.47, 0.44, 0.44, 0.55,
         note="水珠沿发丝裂缝下滑，镜头跟进去，光一层层掉。"),
    Shot(4, "k4_inside", "keyframes/raw/k4_inside.png", 4.5, 1.02, 1.20, 0.50, 0.50, 0.30, 0.74,
         fade_in=0.45, note="英雄镜头：岩层内部垂直下坠，湿壁与矿脉。"),
    Shot(5, "k5_deep", "keyframes/raw/k5_deep.png", 3.0, 1.26, 1.10, 0.50, 0.48, 0.54, 0.50,
         fade_in=0.55, note="更深处，近全黑，只有水的边缘发亮；光每几秒脉动一次。"),
    Shot(6, "k6_spring", "keyframes/raw/k6_spring.png", 4.5, 1.12, 1.00, 0.50, 0.50, 0.56, 0.50,
         fade_in=0.50, note="裂缝张开，冷水涌出；镜头随水面抬起，冷雾贴水跑。"),
    Shot(7, "k7_bottle", "keyframes/raw/k7_bottle.png", 3.19, 1.15, 1.00, 0.50, 0.50, 0.52, 0.50,
         note="泉眼边的雪岩上，一支长白雪；缓慢后拉露出原始林。"),
    Shot(8, "endcard", "", 3.81, 1.0, 1.0, 0.5, 0.5, 0.5, 0.5,
         note="黑场，品牌字标与三行字依次亮起。"),
]

assert abs(sum(s.dur for s in SHOTS) - DUR) < 1e-6, "镜头总长必须等于 30 秒"


@dataclasses.dataclass(frozen=True)
class Super:
    cn: str
    en: str
    t_in: float
    t_out: float
    x: float = 0.080   # 左侧 8%（安全区内）
    y: float = 0.775


SUPERS: list[Super] = [
    Super("长白山 · 自涌冷泉", "CHANGBAI MOUNTAINS · A COLD SPRING", 0.80, 3.60),
    Super("玄武岩 · 三十年", "THIRTY YEARS THROUGH VOLCANIC BASALT", 11.40, 15.10),
    Super("三十年之后，它才涌出来", "AFTER THIRTY YEARS, IT SURFACES", 18.90, 22.30),
]

ENDCARD = {
    "t_start": 26.19,
    "lines": [
        (0.45, "你喝到的，是三十年前的雪。", 46),
    ],
    "lockup": (1.35, "农夫山泉", "长白雪", "天然雪山矿泉水"),
    "slogan": (2.05, "我们不生产水，我们只是大自然的搬运工。"),
    "disclaimer": (2.55, "水源地影像为 AI 生成示意 · Spec work, not commissioned"),
    "en": (1.55, "WHAT YOU TASTE IS SNOW FROM THIRTY YEARS AGO"),
}

# 瓶身标签（归一化，plate 坐标系）。生成的瓶子是空白标签，字由代码排上去。
LABEL_BOX = (0.464, 0.367, 0.598, 0.758)
LABEL_TEXT = ("长白雪", "天然雪山矿泉水")

AUDIO_EVENTS = [
    (0.00, "wind", {"gain": 0.55}),
    (0.00, "drone", {"gain": 0.35, "f0": 38.0}),
    (4.10, "crystal", {"gain": 0.28}),
    (7.90, "slip", {"gain": 0.34}),
    (11.20, "rumble", {"gain": 0.40}),
    (15.50, "pulse", {"gain": 0.30, "period": 2.0, "count": 2}),
    (18.62, "bell", {"gain": 0.42, "f0": 110.0}),
    (18.72, "swell", {"gain": 0.42}),
    (23.10, "fifth", {"gain": 0.30}),
    (26.80, "tail", {"gain": 0.30}),
]


def frame_at(t: float) -> int:
    return min(TOTAL_FRAMES - 1, max(0, int(t * FPS)))


def shot_at(t: float) -> Shot:
    for s in SHOTS:
        if s.start <= t < s.end:
            return s
    return SHOTS[-1]


def _script_md() -> str:
    rows = ["| # | 时间 | 时长 | 画面 | 关键帧 | 运动（z / cx / cy） |", "| --- | --- | --- | --- | --- | --- |"]
    for s in SHOTS:
        rows.append(
            f"| {s.idx} | {s.start:05.2f}–{s.end:05.2f} | {s.dur:.2f}s | {s.note} | "
            f"`{s.src or '（代码绘制）'}` | {s.z0:.2f}→{s.z1:.2f} / "
            f"{s.cx0:.2f}→{s.cx1:.2f} / {s.cy0:.2f}→{s.cy1:.2f} |"
        )
    sup = ["| 中文 | 英文 | 进 | 出 |", "| --- | --- | --- | --- |"]
    for s in SUPERS:
        sup.append(f"| {s.cn} | {s.en} | {s.t_in:.2f} | {s.t_out:.2f} |")
    return f"""# 02 · 分镜与字幕（由 film.py 生成，勿手改）

> 生成命令：`python film.py --doc`　核对命令：`python film.py --check`
> 规格：{W}×{H} · {FPS}fps · {DUR:.2f}s · {TOTAL_FRAMES} 帧

## 镜头

{chr(10).join(rows)}

## 字幕

{chr(10).join(sup)}

## 末屏

- `{ENDCARD['lines'][0][1]}`（{ENDCARD['lines'][0][0]:.2f}s 起，{ENDCARD['lines'][0][2]}px）
- 品牌锁定：{ENDCARD['lockup'][1]} · {ENDCARD['lockup'][2]} · {ENDCARD['lockup'][3]}
- 口号：{ENDCARD['slogan'][1]}
- 披露：{ENDCARD['disclaimer'][1]}

## 声音

{chr(10).join(f"- {t:05.2f}s `{k}` {json.dumps(p, ensure_ascii=False)}" for t, k, p in AUDIO_EVENTS)}
"""


def write_doc() -> None:
    (ROOT / "docs" / "02-SCRIPT.md").write_text(_script_md(), encoding="utf-8")


def check_doc() -> int:
    p = ROOT / "docs" / "02-SCRIPT.md"
    if not p.exists():
        print("FAIL: docs/02-SCRIPT.md 不存在，先跑 --doc")
        return 1
    if p.read_text(encoding="utf-8") != _script_md():
        print("FAIL: docs/02-SCRIPT.md 与 film.py 不一致（改了片子没重新生成文档）")
        return 1
    print("OK: 分镜文档与单一来源一致")
    return 0


if __name__ == "__main__":
    if "--doc" in sys.argv:
        write_doc()
        print("wrote docs/02-SCRIPT.md")
    elif "--check" in sys.argv:
        raise SystemExit(check_doc())
    else:
        for s in SHOTS:
            print(f"{s.idx} {s.start:05.2f}-{s.end:05.2f} {s.key} {s.frames}f")
        print("total frames", sum(s.frames for s in SHOTS))
