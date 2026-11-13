#!/usr/bin/env bash
# 把原图和几张候选优化帧拼成一张带编号的对比图，给用户挑选。
# 用法: compare.sh <输出.png> <原图> <候选1> [候选2] [候选3] ...
# 左上角标签：第一张是"0 原图"，其余依次是 1、2、3…
set -euo pipefail
out="$1"; shift
inputs=(); filter=""; tiles=""; i=0
for f in "$@"; do
  inputs+=(-i "$f")
  label="$i"; [ "$i" = "0" ] && label="0 original"
  filter+="[$i]scale=800:534:force_original_aspect_ratio=decrease,pad=800:534:(ow-iw)/2:(oh-ih)/2,drawtext=text='$label':x=14:y=12:fontsize=40:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=8[t$i];"
  tiles+="[t$i]"; i=$((i+1))
done
cols=2; [ "$i" -le 2 ] && cols=$i
rows=$(( (i + cols - 1) / cols ))
layout=""
for ((k=0; k<i; k++)); do layout+="$(( (k % cols) * 800 ))_$(( (k / cols) * 534 ))|"; done
ffmpeg -v error -y "${inputs[@]}" -filter_complex "${filter}${tiles}xstack=inputs=$i:layout=${layout%|}:fill=black" -frames:v 1 "$out"
echo "$out  （共 $i 张，${cols}x${rows}）"
