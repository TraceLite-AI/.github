#!/usr/bin/env bash
# 从视频里截一帧存成图片，用来做构图参考、首帧或尾帧。
# 用法: grab_frame.sh <视频.mp4> <秒数|last> <输出.png>
#   grab_frame.sh seg1.mp4 8 good.png      截第 8 秒
#   grab_frame.sh seg1.mp4 last tail.png   截最后一帧（给下一段当首帧，用来接戏）
set -euo pipefail
in="$1"; t="$2"; out="$3"
if [ "$t" = "last" ]; then
  ffmpeg -v error -y -sseof -0.1 -i "$in" -update 1 -frames:v 1 "$out"
else
  ffmpeg -v error -y -ss "$t" -i "$in" -frames:v 1 "$out"
fi
echo "$out"
