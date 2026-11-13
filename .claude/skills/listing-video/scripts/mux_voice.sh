#!/usr/bin/env bash
# 把一段视频自带的声音整个换成指定配音（视频模型自己生成的人声一律不用）。
# 用法: mux_voice.sh <视频.mp4> <配音.mp3> <输出.mp4> [配音从第几秒开始，默认 0] [只保留视频前几秒]
# 配音比画面短就补静音；画面长度不变。
set -euo pipefail
v="$1"; a="$2"; out="$3"; off="${4:-0}"; keep="${5:-}"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$v")
[ -n "$keep" ] && dur="$keep"
ms=$(awk -v o="$off" 'BEGIN{printf "%d", o*1000}')
ffmpeg -v error -y -i "$v" -i "$a" -filter_complex \
  "[1:a]aresample=44100,aformat=channel_layouts=stereo,adelay=${ms}:all=1,apad[a]" \
  -map 0:v -map "[a]" -t "$dur" -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a aac -b:a 160k "$out"
echo "$out  画面 ${dur}s，配音从 ${off}s 开始"
