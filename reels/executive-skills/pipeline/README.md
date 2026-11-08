# Editing pipeline (reproducible)

Python + ffmpeg pipeline that produced the reel. The source shots are not committed. Copy them into a work dir as `shot1.mp4` and `shot2.mp4`.

| Step | Script | What it does |
|---|---|---|
| 1 | `asr.py` | Silero VAD + Whisper (turbo, ONNX via `sherpa-onnx`) phrase transcript |
| 2 | `words.py` | Parakeet-TDT (ONNX) word-level timestamps → `data/shot*_words.json` |
| 3 | `env.py`, `verify.py` | Inspect audio energy at cut points; re-transcribe candidate splices to confirm no clipped words |
| 4 | `edl.py` | `data/segments.json` (kept lines) → frame-accurate EDL snapped to silences, with long pauses tightened → `edl.json` |
| 5 | `timeline.py` | Maps the EDL onto the output timeline (1.03× speed), aligns caption words, detects blocks and location changes |
| 6 | `design.py` | All motion graphics, SFX cues, punch-ins and shakes, timed to spoken words |
| 7 | `gfx.py`, `anim.py` | Sprite builders (Poppins + Noto Color Emoji) and the animation/caption engine |
| 8 | `render.py` | Decode → grade → reframe/zoom/transitions → composite → x264 (`video_only.mp4`) |
| 9 | `sounds.py`, `audio.py` | Synthesised SFX + kalimba music bed, voice clean-up, ducking, loudnorm → `mix_music.wav`, `mix_nomusic.wav` |

Then mux the video and audio:
```
ffmpeg -i video_only.mp4 -i mix_music.wav -map 0:v -map 1:a -c:v libx264 -crf 20 -preset slow \
  -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart TheCub_ExecutiveSkills_Reel.mp4
```

Environment: `WORK=<work dir>` (copy `data/*.json` into it; it also holds the shots, `shot*.wav` at 16 kHz mono, json data), `FONT_DIR` (Poppins TTFs from google/fonts).
ASR models are expected under `/tmp/claude-0/models` (sherpa-onnx release assets: `sherpa-onnx-whisper-turbo`, `sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8`, `silero_vad.onnx`).
Python deps: `numpy`, `scipy`, `pillow`, `sherpa-onnx`.

To re-cut, edit `data/segments.json` (add, remove or trim lines) and rerun steps 4 → 9.
