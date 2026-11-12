# OSIT ad pipeline (reproducible)

Same toolchain as `reels/child-to-be-a-child/pipeline` (Python + ffmpeg). The source video is not committed: download
"OSIT REEL.mp4" from Google Drive into a work dir as `shot1.mp4` and make `shot1.wav`
(`ffmpeg -i shot1.mp4 -ac 1 -ar 16000 shot1.wav`).

| Step | Script | What it does |
|---|---|---|
| 1 | `words.py`, `probe.py`, `env.py` | Word timestamps; Whisper checks of candidate cuts; audio envelope |
| 2 | `edl.json` | Sections of the take to keep, speed, end hold, closing-frame length |
| 3 | `captions.json`, `align.py` | Hand-written caption phrases, timed (with word times) against the edited audio |
| 4 | `timeline.py` | Frame map, captions, and the graphics schedule (each graphic timed to its word) |
| 5 | `gfx.py` | Captions and name card (shared with the Saisha reel) |
| 6 | `osit_gfx.py` | Profession pills, OSIT title card, date / urgency callouts, logos card, photo cards, closing frame with QR |
| 7 | `render.py` | Reframe, grade, blur behind photo cards, graphics, closing dissolve → `video_only.mp4` (`--stills t1,t2` for previews) |
| 8 | `audio.py`, `sounds.py`, `sounds2.py` | Voice clean-up and levelling, music bed, SFX, two −14 LUFS masters |

Run (with `WORK=<work dir>` and `MODELS=<models dir>`): `python words.py $WORK/shot1.wav $WORK/shot1_words.json`,
`python align.py`, `python timeline.py`, `python render.py`, `python audio.py`, then mux as in the Saisha pipeline README.

`brand/` holds the logos, the OSIT title block and the QR (cropped from `../assets/osit_poster.webp`); the photos are
read from `../assets/`. Fonts in `fonts/` (SIL Open Font License): Glacial Indifference, Lexend, Playfair Display, DM Sans.
