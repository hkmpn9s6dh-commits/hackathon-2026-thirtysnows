#!/usr/bin/env bash
# 一条命令复验：从仓库根目录跑 `bash scripts/verify.sh`，不联网、不依赖全局缓存。
set -uo pipefail
cd "$(dirname "$0")/.."

# 这台机器上 `python` 与 `py -3` 不是同一个解释器（前者没装 numpy），统一用能找到 numpy 的那个。
if py -3 -c "import numpy" >/dev/null 2>&1; then
  PY="py -3"
elif python3 -c "import numpy" >/dev/null 2>&1; then
  PY="python3"
else
  PY="python"
fi

FAIL=0
say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
ok()  { printf '  PASS  %s\n' "$1"; }
bad() { printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL+1)); }

say "1/8 单一来源：分镜文档与 film.py 一致"
$PY film.py --check || bad "docs/02-SCRIPT.md 与 film.py 不一致"

say "2/8 关键帧齐备"
for k in k1_ridge k2_flake k3_bead k4_inside k5_deep k6_spring k7_bottle; do
  [ -f "keyframes/raw/$k.png" ] && ok "$k" || bad "缺 keyframes/raw/$k.png"
done

say "3/8 画面版准备（裁生成器水印 → 1920×1080）"
$PY render.py --prep || bad "prep 失败"
for k in k1_ridge k2_flake k3_bead k4_inside k5_deep k6_spring k7_bottle; do
  [ -f "keyframes/plate/$k.png" ] && ok "plate/$k" || bad "缺 plate/$k"
done

say "4/8 断言（时间轴 / 字幕 / 冷调 / 无肤色块 / 字体覆盖）"
$PY -m unittest discover -s tests -q || bad "单元断言未全过"

say "5/8 成片规格"
if [ ! -f out/thirty-years.mp4 ]; then
  bad "缺 out/thirty-years.mp4（先跑 bash scripts/build.sh）"
else
  $PY scripts/check_probe.py || FAIL=$((FAIL+1))
fi

say "6/8 响度与真峰（-14 LUFS ±1，真峰 ≤ -1 dBTP）"
if [ -f out/audio-master.wav ]; then
  $PY - <<'PY' || FAIL=$((FAIL+1))
import json, re, subprocess, sys
out = subprocess.run(["ffmpeg", "-hide_banner", "-i", "out/audio-master.wav", "-af",
                      "loudnorm=I=-14:TP=-1.5:print_format=json", "-f", "null", "-"],
                     capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", out, re.S)
d = json.loads(m.group(0))
i, tp = float(d["input_i"]), float(d["input_tp"])
print(f"  {'PASS' if abs(i+14) <= 1 else 'FAIL'}  响度 {i:.2f} LUFS")
print(f"  {'PASS' if tp <= -1 else 'FAIL'}  真峰 {tp:.2f} dBFS")
sys.exit(0 if abs(i + 14) <= 1 and tp <= -1 else 1)
PY
else
  bad "缺 out/audio-master.wav"
fi

say "7/8 可复现：重渲 8 帧与成片比对（PSNR ≥ 42 dB）"
$PY scripts/check_repro.py || bad "重渲帧与成片不一致"

say "8/8 交付物齐备"
for f in submission/entry.md submission/credits.md out/workflow.png out/still-snow.png out/still-inside.png out/still-spring.png; do
  [ -f "$f" ] && ok "$f" || bad "缺 $f"
done

printf '\n'
if [ "$FAIL" -eq 0 ]; then
  printf '\033[32m全部通过（EXIT=0）\033[0m\n'
  exit 0
else
  printf '\033[31m%d 项未通过（EXIT=1）\033[0m\n' "$FAIL"
  exit 1
fi
