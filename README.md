# 三十年前的雪 / Thirty Years

A 30-second speculative TVC for **农夫山泉 · 长白雪** (Nongfu Spring "Changbai Snow"),
made for **AARON Awards 2027 · 08 Best Speculative Ad**.

> 你喝到的，是三十年前的雪。
> What you taste is snow from thirty years ago.

The film is one continuous descent: a snowflake lands on basalt, slips into a fissure,
falls for thirty years through volcanic rock, and surfaces as a 7 °C spring — where a
bottle is waiting. It is a shot no camera can fly, which is the point.

- 成片 `out/thirty-years.mp4`（30.00s / 1920×1080 / 24fps / H.264 + AAC）
- 线上页 `web/index.html`
- 赛事材料 `submission/entry.md`、`submission/credits.md`
- 四道闸的证据 `proof/`

## 从零复现（全新 clone）

需要：Python 3.10+、ffmpeg（带 libx264 与 aac）、`pillow numpy opencv-python fonttools`。

```bash
pip install pillow numpy opencv-python fonttools

python audio.py                      # 合成声音 → out/audio.wav
python scripts/master_audio.py       # 响度归一到 -14 LUFS → out/audio-master.wav
python render.py --prep              # 关键帧裁水印 → keyframes/plate/*.png
python render.py --pipe --out out/thirty-years.mp4 --audio out/audio-master.wav
python film.py --doc                 # 生成 docs/02-SCRIPT.md
python scripts/make_stills.py        # 出 3 张 case still
python scripts/make_workflow.py      # 出工作流图 out/workflow.png
bash scripts/verify.sh               # 全部断言（EXIT=0 才算过）
```

`bash scripts/build.sh` 是上面这一串的封装。

## 目录

| 路径 | 是什么 |
| --- | --- |
| `film.py` | **单一真相源**：镜头、运动、字幕、末屏、声音事件 |
| `render.py` | 关键帧 → 帧序列 → ffmpeg（运动 / 调色 / 颗粒 / 字幕） |
| `audio.py` | 声音设计（噪声整形 / 模态合成 / FFT 卷积混响） |
| `keyframes/raw/` | 7 张生成的原图（带生成器水印，构建时裁掉） |
| `docs/` | 00 赛事简报 · 01 创意 · 02 分镜（生成） · 03 出处 · 07 视觉规格 |
| `tests/` | 闸 B 的断言（25 条） |
| `proof/` | 闸 C / 闸 D 的原始记录 |

## 已知限制

- 这台机器没有 `cv2.CascadeClassifier`，人脸判据用「肤色连通域」代理；它不是人脸检测器。
- 生成器在每张图右下角带「AI生成 WORKBUDDY」水印，构建时统一裁掉 8.2% 边距再放大到 1920×1080。
- 声音全部合成，没有真人演唱 / 演奏；这支片子刻意不用音乐。

## 披露

本项目为**未受委托的 spec 作品**（spec work, not commissioned），不投放、不商用。
片尾已标「水源地影像为 AI 生成示意」。品牌与产品事实引自农夫山泉官网，见 `docs/03-SOURCES.md`。
