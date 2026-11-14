#!/bin/bash
# Rebuild the World Prematurity Day reel.
# Inputs: audio/vo_trim.wav (cleaned + pause-tightened voiceover, made by tools/trim.py from the Drive voiceover)
# Optional: drop the official logo at web/logo.png — the end card picks it up automatically.
set -e; cd "$(dirname "$0")"
FR=${FRAMES:-/tmp/wpd_frames}
python3 tools/make_data.py > /dev/null          # captions/timing -> web/data.js
python3 tools/music.py audio/music.wav 60.6      # original background score
tools/mix.sh                                     # VO + ducked music -> audio/final_mix.wav
rm -rf "$FR"; node tools/render.js "$FR" 4       # 1080x1920 PNG frames @30fps
mkdir -p ../output
ffmpeg -y -loglevel error -framerate 30 -i "$FR/f_%05d.png" -i audio/final_mix.wav -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 16 -profile:v high -level 4.2 -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 256k -ar 48000 -ac 2 -movflags +faststart -shortest ../output/WorldPrematurityDay_TheCub_9x16.mp4
echo done
