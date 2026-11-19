# 03 · 事实与出处

> 规则：片子里出现的每一个事实，都要能在这里指到原文。查不到原文的，不写进片子。

## 产品事实

| 用途 | 事实 | 原文 | 出处 |
| --- | --- | --- | --- |
| S4「三十年」 | 长白雪水源经**约 30–60 年**火山玄武岩深层溶滤、自然净化 | 「经由约30-60年火山玄武岩深层溶滤、自然净化」 | 农夫山泉官网 · 长白雪产品页 https://www.nongfuspring.com/goods/detail-all.html?pid=28&id=6&product_id=105 |
| S6「7℃」 | 自涌冷泉恒温**约 7 摄氏度** | 「最终汇成恒温约7摄氏度的自涌冷泉」 | 农夫山泉长白雪 TVC 报道（品牌方发布内容转载）http://mp.weixin.qq.com/s?__biz=MzI0OTA0NjI5OA==&mid=2247502694 |
| S1「自涌冷泉」 | 源自长白山原始森林、距天池 < 60 公里的自涌冷泉 | 「源自长白山原始森林、距离天池< 60公里的自涌冷泉」 | 同上产品页 |
| 末屏口号 | 我们不生产水，我们只是大自然的搬运工 | 品牌长期口号（多处引用） | 同上报道；官网品牌页 https://www.nongfuspring.com/ |
| 末屏产品名 | 长白雪 · 天然雪山矿泉水 | 「长白雪·天然雪山矿泉水」 | 同上产品页 |

## 赛事事实

| 事实 | 原文 | 出处 |
| --- | --- | --- |
| 只有 Spec Ad 不要求品牌委托 | "For all categories except Best Speculative Ad, entries must meet all of the following: 01 Commercially Commissioned Work (Required)" | https://www.aaronawards.com/criteria-2027/index.html |
| 早鸟免费至 2027-01-15 | "Nov 2026 – 15 Jan 2027 / Early bird entries / Free" | https://www.aaronawards.com/ |
| 08 类定义与权重 | 见 00-BRIEF 第 0 节 | 同上 criteria 页 |
| 必交材料含工作流图 | "Diagrams of workflows, system architecture, or collaboration structure" | 同上 criteria 页（Submission Guidelines） |

## 影像与声音的来源

| 素材 | 来源 | 说明 |
| --- | --- | --- |
| 7 张关键帧 | 本项目用 ImageGen 生成，prompt 见 `docs/06-PROMPTS.md` | 生成器右下角带「AI生成 WORKBUDDY」水印，构建时统一裁掉 8.2% 边距并放大到 1920×1080 |
| 全部声音 | `audio.py` 合成（噪声整形 / 模态合成 / FFT 卷积混响） | 无任何外部音频素材 |
| 字体 | Noto Serif SC（SIL OFL）、Source Han Serif SC Heavy（SIL OFL）、Segoe UI Light（随 Windows 授权，仅用于本片栅格化） | 视频内为栅格化字形，不再分发字体文件 |

## 不写进片子的东西

- 「海拔 2,000 米」：查不到长白山水源地的准确海拔，删掉
- 「低钠」「偏硅酸」：真实但 30 秒装不下，只留在 case 里
- 任何「更健康」「更适合婴幼儿」类功效暗示：不碰
