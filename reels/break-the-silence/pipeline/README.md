# Break The Silence pipeline (adapted from the Saisha reel)

Python + ffmpeg. The 4K source is not committed: download it from Google Drive into a work dir as `shot1.mp4` and make
`shot1.wav` (`ffmpeg -i shot1.mp4 -ac 1 -ar 16000 shot1.wav`).

| Step | Script | What it does |
|---|---|---|
| 1 | `words.py`, `probe.py` | Word timestamps; Whisper checks of every piece |
| 2 | `edl.json` | The kept ranges (each one shot), speed, end hold |
| 3 | `captions.json`, `align.py` | Caption phrases, timed against the edited audio |
| 4 | `timeline.py` | Frame map, captions, taunt highlights, title and name card timing, logo reveal |
| 5 | `gfx.py`, `bts_gfx.py` | Captions, name card and logo reveal (shared with the Saisha reel); taunt highlights and the title |
| 6 | `render.py` | Crops each shot from the 4K source, retouches skin (face-tracked), grades, adds graphics → `video_only.mp4` (`--stills t1,t2 [dir]`) |
| 7 | `audio.py`, `sounds.py`, `sounds2.py` | Voice clean-up and levelling, calm music bed, SFX, two −14 LUFS masters |

Run with `WORK=<work dir>` and `MODELS=<models dir>`: `python words.py $WORK/shot1.wav $WORK/shot1_words.json`,
`python align.py`, `python timeline.py`, `python render.py`, `python audio.py`, then mux:

```
ffmpeg -i $WORK/video_only.mp4 -i $WORK/mix_music.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 19 \
  -maxrate 12M -bufsize 24M -profile:v high -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart reel.mp4
```

Models: Parakeet-TDT and Whisper medium.en (sherpa-onnx), `yunet.onnx` (OpenCV Zoo). Fonts in `fonts/` (SIL OFL).
