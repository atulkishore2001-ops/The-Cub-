#!/bin/bash
# Final audio mix: levelled voiceover (primary) + ducked background score.
set -e; cd "$(dirname "$0")/.."
ffmpeg -y -loglevel error -i audio/vo_trim.wav -i audio/music.wav -filter_complex "
[0:a]aresample=48000,adelay=600,apad=whole_dur=60.6,volume=8.8dB,alimiter=limit=0.80:attack=4:release=80:level=false,aformat=channel_layouts=stereo,asplit=2[vo][sc];
[1:a]aresample=48000,volume='pow(10,(-17+6*min(1,max(0,(t-56.2)/0.9)))/20)':eval=frame:precision=float,volume=0dB[mu];
[mu][sc]sidechaincompress=threshold=0.03:ratio=5:attack=40:release=450:makeup=1[duck];
[vo][duck]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.84:level=false,atrim=0:60.6,afade=t=out:st=59.4:d=1.2[out]" -map "[out]" -ar 48000 -c:a pcm_s24le audio/final_mix.wav
