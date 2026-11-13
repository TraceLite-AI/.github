#!/usr/bin/env bash
# 把若干段视频按顺序拼成一条：统一 720p/24fps、统一响度、结尾半秒淡出。
# 没有音轨的片段（比如关掉生成音频的空镜）会自动补静音。
# 用法: stitch.sh <输出.mp4> <段1.mp4> <段2.mp4> ...
set -euo pipefail
out="$1"; shift
n=$#; inputs=(); filter=""; pairs=""; total=0
i=0
for f in "$@"; do
  inputs+=(-i "$f")
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  total=$(awk -v a="$total" -v b="$d" 'BEGIN{print a+b}')
  filter+="[$i:v]fps=24,scale=1280:720,setsar=1[v$i];"
  if [ -n "$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$f")" ]; then
    filter+="[$i:a]aresample=44100,aformat=channel_layouts=stereo,loudnorm=I=-16[a$i];"
  else
    filter+="anullsrc=r=44100:cl=stereo,atrim=duration=$d[a$i];"
  fi
  pairs+="[v$i][a$i]"
  i=$((i+1))
done
st=$(awk -v t="$total" 'BEGIN{print t-0.6}')
filter+="${pairs}concat=n=$n:v=1:a=1[v][a];[v]fade=t=out:st=$st:d=0.5[vo];[a]afade=t=out:st=$st:d=0.5[ao]"
ffmpeg -v error -y "${inputs[@]}" -filter_complex "$filter" -map "[vo]" -map "[ao]" \
  -c:v libx264 -crf 23 -preset slow -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart "$out"
echo "完成: $out  时长约 ${total}s"
