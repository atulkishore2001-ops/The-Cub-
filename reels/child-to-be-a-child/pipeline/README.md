# Editing pipeline (reproducible)

Python + ffmpeg pipeline that produced this reel. The raw clips are not committed: copy them into a work dir as
`shot1.mp4`, `shot2.mp4`, `shot3.mp4` (Saisha 1, 2, 3, in order) and make 16 kHz mono WAVs of each
(`ffmpeg -i shotN.mp4 -ac 1 -ar 16000 shotN.wav`).

| Step | Script | What it does |
|---|---|---|
| 1 | `words.py` | Parakeet-TDT word timestamps per shot (`shotN_words.json`) |
| 2 | `env.py`, `probe.py` | Audio envelope around cut candidates; Whisper transcripts of candidate splices |
| 3 | `edl.json`, `check_cuts.py` | The cut list (sections → ranges, framing per section, speed) and a full re-transcription of every section as edited |
| 4 | `captions.json`, `align.py` | Hand-written caption phrases, timed by re-transcribing each edited section and matching words in order |
| 5 | `timeline.py` | Output frame map, cut list (joins vs. soft morph cuts), caption times, title / name card / reveal timing |
| 6 | `gfx.py` | Title, captions, name card and the closing logo reveal (brand colours and fonts) |
| 7 | `render.py` | Decode, reframe per section, morph cuts, grade, graphics → `video_only.mp4`. `--stills t1,t2` for previews |
| 8 | `audio.py`, `sounds.py`, `sounds2.py` | Voice levelling + clean-up, music bed, sound effects, two −14 LUFS masters |
| brand | `logo_cut.py`, `brand/` | Turns the supplied logo JPEG into transparent PNGs |

Run order (with `WORK=<work dir>` and `MODELS=<models dir>` set):

```
python words.py $WORK/shot1.wav $WORK/shot1_words.json   # and 2, 3
python align.py
python timeline.py
python render.py
python audio.py
ffmpeg -i $WORK/video_only.mp4 -i $WORK/mix_music.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 19 \
  -maxrate 12M -bufsize 24M -profile:v high -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart reel.mp4
```

Models (in `$MODELS`): `sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/`, `sherpa-onnx-whisper-medium.en/`
(sherpa-onnx release assets) and `yunet.onnx` (OpenCV Zoo `face_detection_yunet_2023mar.onnx`; fetch the real file, not
the Git LFS pointer). Python deps: `numpy`, `scipy`, `pillow`, `sherpa-onnx`, `opencv-python-headless`.

Fonts in `fonts/` (all SIL Open Font License): Playfair Display, Lexend, Glacial Indifference.

To change the name card, title or tagline text, edit the constants at the top of `gfx.py` and rerun `render.py` and the mux.
To re-cut, edit `edl.json` (and `captions.json` if words change) and rerun steps 4 to 8.
