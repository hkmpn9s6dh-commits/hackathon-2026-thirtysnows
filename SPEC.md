# SPEC — 《三十年前的雪》/ Thirty Years

> AARON Awards 2027 · Category 08 **Best Speculative Ad**
> 30 秒 spec TVC ｜ 农夫山泉 · 长白雪（天然雪山矿泉水）｜ 16:9 / 1920×1080 / 24fps

## 0. 官方评分表（原文照录，来自 criteria-2027）

| 维度 | 权重 | 原文 |
| --- | --- | --- |
| Creative Experimentation & Originality | **30%** | — |
| Creative Idea & Storytelling | **25%** | — |
| Craft & Quality of Execution | **20%** | — |
| Innovative Use of AI | **15%** | — |
| Brand Relevance & Commercial Credibility | **10%** | — |

类别定义原文：*"Celebrates speculative brand commercials that use AI to experiment, push creative boundaries and explore bold new territories beyond traditional production constraints. The work must take the form of a compelling, commercially relevant ad for a real brand…"*
硬性材料：项目说明（挑战 / 创意与技术方法 / 结果）、支撑视觉、**工作流或系统架构图**、credits。

## 1. 黄金路径（golden path）

一个从没听过这个品牌的人，在 30 秒里应当依次得到四件事：

1. **这在哪里**（长白山，冷，雪）
2. **发生了什么**（一滴雪水钻进石头，往下走，走了很久）
3. **为什么值得喝**（那三十年就是它的配方）
4. **记住一句话**（你喝到的，是三十年前的雪）

任何一屏没有推进这四步之一，就是废镜头。**范围只删不加。**

## 2. 演示脚本（先写这个，再写验收条件）

| # | 时间 | 画面 | 声音 | 屏幕字 |
| --- | --- | --- | --- | --- |
| 1 | 00.0–04.0 | 长白山脊，蓝调时刻。风把雪从脊线上抽走，像一条慢速的河。镜头极缓推近。 | 风；一层几乎听不见的低频开始 | `长白山 · 自涌冷泉 · 7℃`（左下，00.8 进） |
| 2 | 04.0–07.5 | 微距：一片雪花落在黑色玄武岩上，融成一颗水珠。水珠把天光收成一个点。 | 风退；一声极轻的结晶"叮" | — |
| 3 | 07.5–11.0 | 水珠顺着发丝般的裂缝滑下去。镜头跟进去，光一层层掉。 | 一声"滑"，随后进混响 | — |
| 4 | 11.0–15.5 | **英雄镜头**：岩层内部。垂直下坠，湿的玄武岩壁、矿脉在侧光里闪一下。水在石头上铺成一层薄膜。 | 深潜般的低频；远处滴水 | `玄武岩 · 三十年`（左下，11.4 进） |
| 5 | 15.5–19.5 | 更深处。几乎全黑，只有水的边缘在发亮。光每隔几秒脉动一次，像年份在数。 | 心跳般的次低频；水声变得很遥远 | — |
| 6 | 19.5–23.0 | 裂缝张开，冷水涌出。镜头随水面抬起，冷雾贴着水面跑。 | 水声涌起；一记低音钟 | `水温 7℃`（左下，20.0 进） |
| 7 | 23.0–27.0 | 雪线边的泉眼。一只长白雪的瓶子立在雪岩上，瓶身挂着冷凝水。镜头缓慢后拉，露出后面的原始林。 | 弦乐第一次进来；风 | — |
| 8 | 27.0–30.0 | 黑场。品牌字标与三行字依次亮起。 | 钟声余韵收干净 | `你喝到的，是三十年前的雪。`／`农夫山泉 · 长白雪`／`我们不生产水，我们只是大自然的搬运工`／底部小字 `水源地影像为 AI 生成示意` |

英文对照（烧字幕，随中文字幕同位）：
- `Changbai Mountains · A cold spring at 7°C`
- `Thirty years through volcanic basalt`
- `What you taste is snow from thirty years ago`
- `NONGFU SPRING · Changbai Snow`

## 3. 验收条件（可判定）

| 编号 | 条件 | 怎么判 |
| --- | --- | --- |
| AC-1 | 30.00 s（±0.04）、1920×1080、24 fps、H.264+AAC | ffprobe |
| AC-2 | 8 个镜头，切点与 `film.py` 单一来源一致（±1 帧） | 抽帧比对 + film.py 导出 |
| AC-3 | 三处主字幕与末屏四行字在片中出现，时段与 `film.py` 一致 | 逐帧 OCR/像素比对（用已知渲染的 alpha 蒙版） |
| AC-4 | 全片不出现人脸 | OpenCV 人脸检测 0 命中（抽样每 6 帧） |
| AC-5 | 所有文字距画面边缘 ≥ 5%，且不压在产品主体上 | 版式断言（文字包围盒 vs 主体包围盒） |
| AC-6 | 响度 −14 LUFS ±1，真峰 ≤ −1 dBTP，无削波 | ffmpeg ebur128 + astats |
| AC-7 | 冷调：B>R 的像素占比 ≥ 60%（末屏除外） | 逐帧统计 |
| AC-8 | 可复现：同输入重跑，PSNR ≥ 45 dB | 重渲 + ffmpeg psnr |
| AC-9 | `docs/02-SCRIPT.md` 由 `film.py --doc` 生成，`--check` 通过 | 命令退出码 |
| AC-10 | 用到的字全部在随包字体子集里（无豆腐块） | 字表 vs 子集覆盖 |
| AC-11 | 线上页可播、文案一致 | Playwright e2e |
| AC-12 | 无第三方素材：画面全部由本项目生成，声音全部由 `audio.py` 合成或 TTS | 物料清单 + 无外部下载 |

## 4. 明确不做

- 不做人物、不做对白、不做产品特写旋转（30 秒装不下三个卖点，只留"时间"）
- 不做中英双语配音（只烧字幕；品牌名以字标出现）
- 不用任何现成音乐（版权与"AI 生成"披露都不干净）
- 不宣称医疗/健康功效（只讲水源与时间）
