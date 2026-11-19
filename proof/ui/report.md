# UI 量测报告（只管卫生，不判过线）

跑法：`python -m unittest discover -s tests`（片内版式）+ `node scripts/e2e_online.cjs`（页面）。

## 片内（1920×1080）

| 项 | 判据 | 实测 | 结论 |
| --- | --- | --- | --- |
| 字幕包围盒左边界 | ≥ 5% = 96 px | 153 px | PASS |
| 字幕包围盒下边界 | ≤ 95% = 1026 px | 867 px | PASS |
| 字幕包围盒右边界 | ≤ 95% = 1824 px | 624 px | PASS |
| 最小字号 | ≥ 1.2% 画高 ≈ 13 px | 13 px（披露行） | PASS |
| 末屏行距 | ≥ 字号 × 1.15 | 最近一行 48 px（16 px 字）≥ 18.4 | PASS |
| 末屏「主张—英文」行距 | ≥ 46×1.15 = 52.9 px | 54 px | PASS |
| 人脸 / 肤色连通块 | < 1% 画面（本片应无） | 0 命中（每 12 帧抽样） | PASS |
| 冷调（B>R 的可见像素） | ≥ 60% | 见 `tests/test_film.py::test_cold_palette`，7 个抽样点全过 | PASS |

> 说明：这台机器的 opencv 没有 haar 级联，也没有 yunet 的 onnx 权重，所以「无人物」用的是
> 肤色连通域代理判据，不是人脸检测器。本片是雪 / 岩 / 水，正常不会出现成片肤色。

## 页面（线上）

`scripts/e2e_online.cjs` 对 **两个视口** 各跑 9 项，共 18 项，全部 PASS：

| 项 | 1440×1000 | 390×844 |
| --- | --- | --- |
| 标题含 "Thirty Years" | PASS | PASS |
| h1 存在 | PASS | PASS |
| 视频时长 30.00 s | PASS | PASS |
| 视频源 `thirty-years.mp4` | PASS | PASS |
| 4 张图全部 `naturalWidth > 0` | PASS | PASS |
| 子集字体 `document.fonts.check` | PASS | PASS |
| 横向溢出 | 0 px | 0 px |
| 正文长度 | 4004 字符 | 4004 字符 |
| JS 报错 | 0 | 0 |

截图：`proof/ui/online-desktop.png`、`proof/ui/online-idea.png`、`proof/ui/online-mobile.png`。

## 改过的一处（记录在案）

首屏 `.meta` 与视频之间原本是 0 间距（`film.y == meta.bottom`），看上去像文字被视频压掉。
改的是容器间距（`.meta{margin-bottom:30px}`），不是缩字号 —— 版式不动，只让两块分开。
