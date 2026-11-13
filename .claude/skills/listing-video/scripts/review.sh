#!/usr/bin/env bash
# 给一段视频出"每秒一帧"的缩略图总览，用来快速检查画面。
# 用法: review.sh <视频.mp4> [输出.png]
set -euo pipefail
in="$1"; out="${2:-${in%.mp4}_sheet.png}"
ffmpeg -v error -y -i "$in" -vf "fps=1,scale=400:-1,tile=5x3" -frames:v 1 "$out"
echo "$out"
