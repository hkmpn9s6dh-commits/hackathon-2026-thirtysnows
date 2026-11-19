# Credits

**Thirty Years / 三十年前的雪**
A 30-second speculative film for Nongfu Spring · Changbai Snow (农夫山泉 · 长白雪)

| Role | Name |
| --- | --- |
| Concept, art direction, edit | Zhang Yi（张一） |
| Keyframes (generative image) | Zhang Yi, with an AI image model |
| Motion, grade, compositing, typography | Zhang Yi — `render.py` |
| Sound design and mix | Zhang Yi — `audio.py` |
| Build, tests, reproducibility | Zhang Yi — `film.py`, `scripts/verify.sh` |
| Production system | A single-repository pipeline: one source file → 720 frames → master |

**Tools.** Generative image model (keyframes) · Python / OpenCV / NumPy / Pillow (motion,
grade, compositing, typography, synthesis) · FFmpeg (encode) · Source Han Serif SC and
Noto Serif SC (type, rasterised into the film only).

**Commission.** None. This is speculative work made for the AARON Awards 2027, category 08.
Not affiliated with or endorsed by Nongfu Spring. No media spend, no broadcast, no client.

**Disclosure.** All imagery is AI-generated and composited by code; the end card states
「水源地影像为 AI 生成示意」. Product facts (30–60 years of basalt filtration, 7 °C spring,
the brand line) are quoted from Nongfu Spring's own product pages — see `docs/03-SOURCES.md`.
