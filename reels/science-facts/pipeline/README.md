# 5 Science Facts pipeline (adapted from the Saisha / Anjali reels)

Python + ffmpeg. The sources are not committed: download `Main Raw Footage.mp4` into a work dir as `shot1.mp4` (+ `shot1.wav`,
16 kHz mono) and the B-roll files (`honey.mp4`, `octopus.mp4`, `sunlight.mp4`, `venus.mp4`, `banana.mp4`) into `BROLL_DIR`.

| Step | Script | What it does |
|---|---|---|
| 1 | `words.py`, `probe.py` | Word timestamps; Whisper checks of every piece |
| 2 | `edl.json`, `captions.json`, `align.py` | Kept audio pieces; caption phrases timed to the edited audio |
| 3 | `timeline.py` | Picture plan (speaker vs. B-roll, B-roll in-points and crops), speaker framing, every motion graphic timed to its word |
| 4 | `gfx.py`, `sf_gfx.py` | Captions, name card, logo reveal (shared); title, stamps, fact badges and chips, cards, hearts, Sun→Earth timer, Venus bars, radiation and potassium tile, number pills |
| 5 | `render.py` | Speaker + B-roll frames, grade, graphics → `video_only.mp4` (`--stills t1,t2 [dir]`) |
| 6 | `audio.py`, `sounds.py`, `sounds2.py` | Voice clean-up and levelling, music bed, SFX, two −14 LUFS masters |

Run with `WORK`, `BROLL_DIR` and `MODELS` set: `python align.py`, `python timeline.py`, `python render.py`, `python audio.py`, then mux
as in the other pipelines' READMEs.
