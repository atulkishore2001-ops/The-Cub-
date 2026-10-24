# Editing pipeline (reproducible)

Python + ffmpeg pipeline that produced this reel. The raw clips are not committed: copy them into a work dir as
`shot1.mp4`, `shot2.mp4`, `shot3.mp4` (Anjali 1, 2, 3, in order).

| Step | Script | What it does |
|---|---|---|
| 1 | `asr.py`, `words.py`, `asr_med.py`, `asr_med2.py` | Whisper (ONNX, via `sherpa-onnx`) transcripts, Parakeet word timestamps, and a second Whisper model to settle doubtful words |
| 2 | `env.py` | Prints the audio energy around cut candidates (the clips have digital silence between phrases) |
| 3 | `data/segments.json`, `edl2.py` | Kept lines, with cut points snapped to silence and inner pauses tightened, give a frame-accurate cut list |
| 4 | `timeline3.py` | Maps the cut list to the output timeline (1.04x), aligns caption words, snaps sentence starts to the true voice onset |
| 5 | `faces.py`, `render3.py` | YuNet face tracking (smoothed per frame): the face is held at one height so the wall above stays free for graphics |
| 6 | `gfx2.py`, `anim2.py` | Brand type (DM Sans, Playfair Display Italic, Caveat), shapes, sprite and caption engine |
| 7 | `design3.py` | Every graphic, caption and sound cue, timed to spoken words; the closing logo + tagline reveal |
| 8 | `render3.py` | Decode, reframe, soft 4-frame dissolves on cuts, graphics, captions, fade to the cream brand frame, x264 (`video_only.mp4`). `--stills t1,t2 dir` for previews, `--qa 3` for the face-overlap check |
| 9 | `sounds.py`, `sounds2.py`, `audio3.py` | Synthesised SFX and music bed, voice clean-up (denoise, EQ, compression), per-sentence levelling, gentle ducking, natural music fade-out, two-pass loudnorm master |
| brand | `logo_cut.py`, `brand/` | Turns the supplied logo JPEG into clean transparent PNGs |

Final mux:

```
ffmpeg -i video_only.mp4 -i mix_music.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 20 \
  -maxrate 12M -bufsize 24M -profile:v high -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart reel.mp4
```

Environment: `WORK=<work dir>` (shots, `shotN.wav` at 16 kHz mono, `shotN_words.json` from step 1, and `segments.json`),
`BRAND=<dir with logo_*.png>`, `FONT_DIR` (DM Sans, Playfair Display Italic and Caveat variable fonts from google/fonts).
Models: Whisper turbo and medium.en and Parakeet-TDT (sherpa-onnx release assets), `silero_vad.onnx`, and the OpenCV
YuNet face detector (`face_detection_yunet_2023mar.onnx`; fetch the real file, not the Git LFS pointer).
Python deps: `numpy`, `scipy`, `pillow`, `sherpa-onnx`, `opencv-python-headless`.

To re-cut, edit `segments.json` and rerun steps 3 to 9.
