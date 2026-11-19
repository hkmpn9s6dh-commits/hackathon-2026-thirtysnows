#!/usr/bin/env bash
# 把 web/ 发布到 gh-pages 分支（Pages 只认 / 或 /docs，所以用独立分支，不弄脏主干）。
set -euo pipefail
cd "$(dirname "$0")/.."
TMP="$(mktemp -d)"
cp -r web/. "$TMP/"
cd "$TMP"
git init -q
git add -A
git -c user.name=CB -c user.email=cb@local commit -q -m "site: Thirty Years"
git branch -M gh-pages
git remote add origin https://github.com/hkmpn9s6dh-commits/hackathon-2026-thirtysnows.git
git -c http.proxy=http://127.0.0.1:7897 -c http.version=HTTP/1.1 push -q origin gh-pages
echo "pushed gh-pages"
