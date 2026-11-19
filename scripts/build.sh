#!/usr/bin/env bash
# 从零构建整条片子。约 8 分钟（渲染 6 分 + 编码 3 分）。
set -euo pipefail
cd "$(dirname "$0")/.."

PY="py -3"
py -3 -c "import numpy" >/dev/null 2>&1 || PY="python3"

$PY audio.py
$PY scripts/master_audio.py
$PY render.py --prep
$PY render.py --pipe --out out/thirty-years.mp4 --audio out/audio-master.wav
$PY film.py --doc
$PY scripts/make_stills.py
$PY scripts/make_workflow.py
$PY scripts/subset_font.py
echo "done: out/thirty-years.mp4"
