# Editing pipeline (reproducible)

Python + ffmpeg pipeline that produced this reel. The raw clips are not committed: copy them into a work dir as
`shot1.mp4`, `shot2.mp4`, `shot3.mp4` (Anjali 1, 2, 3, in order).

| Step | Script | What it does |
|---|---|---|
| 1 | `asr.py`, `words.py`, `asr_med.py`, `asr_med2.py` | Whisper (ONNX, via `sherpa-onnx`) transcripts, Parakeet word timestamps, and a second Whisper model to settle doubtful words |
| 2 | `env.py` | Prints the audio energy around cut candidates (the clips have digital silence between phrases) |
| 3 | `data/segments.json`, `edl3.py` | Each clip as one continuous take: only pauses over 0.6s are shortened (to 0.3s), cuts snap to silence and to the camera's own cuts (`edl2.py` holds the shared helpers) |
| 4 | `timeline3.py` | Maps the cut list to the output timeline (1.025x), aligns caption words, snaps sentence starts to the true voice onset |
| 5 | `faces.py`, `render4.py` | YuNet face tracking, heavily smoothed: one steady framing per camera set-up, face held at one height and size |
| 6 | `gfx2.py`, `anim2.py` | Brand type (DM Sans, Playfair Display Italic, Caveat), shapes, sprite and caption engine |
| 7 | `design4.py` | The 9 cards, continuous captions and sound cues, timed to spoken words; the closing logo + tagline reveal |
| 8 | `render4.py` | Decode, steady reframe, optical-flow morph cuts, key-light grade, graphics, captions, fade to the cream brand frame, x264 (`video_only.mp4`). `--stills t1,t2 dir` for previews, `--qa 3` for the face-overlap check |
| 9 | `sounds.py`, `sounds2.py`, `audio4.py` | Synthesised SFX and music bed, voice clean-up (denoise, EQ, compression), per-sentence levelling, gentle ducking, natural music fade-out, two-pass loudnorm master |
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

`design3.py`, `render3.py`, `audio3.py` produced the first version (74.0s, more cuts and animations) and are kept for reference.
