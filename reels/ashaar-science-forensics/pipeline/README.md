# Editing pipeline (reproducible)

Python + ffmpeg pipeline that produced this reel. The raw clips are not committed: copy them into a work dir as
`shot1.mp4`, `shot2.mp4`, `shot3.mp4` (explainer, in order) and `audio1.mp4`, `audio2.mp4` (promo voice-overs).

| Step | Script | What it does |
|---|---|---|
| 1 | `asr.py`, `words.py`, `asr_med.py` | Whisper (ONNX, via `sherpa-onnx`) transcripts, Parakeet word timestamps, and a second Whisper model to settle doubtful words |
| 2 | `env.py` | Prints the audio energy around cut candidates (the clips have digital silence between phrases, so cuts land cleanly) |
| 3 | `data/segments.json`, `edl2.py` | Kept lines, with cut points snapped to silence and inner pauses tightened, give a frame-accurate cut list |
| 4 | `timeline2.py` | Maps the cut list to the output timeline (1.06x), aligns caption words, finds scene blocks / location changes, places the promo voice |
| 5 | `faces.py`, `render2.py` | YuNet face tracking (smoothed per frame) so the face always sits clear of graphics and the cream panel |
| 6 | `gfx2.py`, `icons.py`, `tank.py`, `anim2.py` | Brand type (DM Sans, EB Garamond), vector icons, the float/sink tank animation, sprite and caption engine |
| 7 | `design2.py` | Every scene: layouts, graphics, captions, sound cues, all timed to spoken words |
| 8 | `render2.py` | Decode, reframe, split-screen layouts, push transitions, graphics, captions, x264 (`video_only.mp4`). `--stills t1,t2 dir` for previews, `--qa 3` for the face-overlap check |
| 9 | `sounds.py`, `sounds2.py`, `audio2.py` | Synthesised SFX and music bed, voice clean-up, per-sentence levelling, loudness-matched promo voice, ducking, two-pass loudnorm master |
| brand | `logo_cut.py`, `brand/` | Turns the supplied logo JPEG into clean transparent PNGs |

Final mux:

```
ffmpeg -i video_only.mp4 -i mix_music.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 20 \
  -maxrate 12M -bufsize 24M -profile:v high -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart reel.mp4
```

Environment: `WORK=<work dir>` (shots, `shotN.wav` / `audioN.wav` at 16 kHz mono, and `data/*.json` copied in),
`BRAND=<dir with logo_*.png>`, `FONT_DIR` (DM Sans, EB Garamond and Caveat variable fonts from google/fonts).
Models: Whisper turbo and medium.en and Parakeet-TDT (sherpa-onnx release assets), `silero_vad.onnx`, and the OpenCV
YuNet face detector (`face_detection_yunet_2023mar.onnx`; fetch the real file, not the Git LFS pointer).
Python deps: `numpy`, `scipy`, `pillow`, `sherpa-onnx`, `opencv-python-headless`.

To re-cut, edit `data/segments.json` and rerun steps 3 to 9.
