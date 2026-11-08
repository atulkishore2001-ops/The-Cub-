# Editing pipeline (reproducible)

Python + ffmpeg. The raw clips are not committed: copy them into a work dir as `shot1.mp4`, `shot2.mp4`, `shot3.mp4`.

| Step | Script | What it does |
|---|---|---|
| 1 | `asr.py`, `words.py`, `asr_med2.py` | Whisper turbo / medium.en and Parakeet word timestamps (sherpa-onnx) to transcribe and settle unclear words |
| 2 | `data/segments.json` | The spoken lines (as delivered) with their source times |
| 3 | `edl3.py` (+ `edl2.py`) | Each clip as one take: pauses over 0.4s (breaths count as pause below −50 dB) shortened to 0.25s |
| 4 | `timeline4.py` | Cut list → output timeline (1.025×), caption word timing |
| 5 | `illus.py` | The drawn illustrations: brain and vessels, risk-factor icons, FAST face/arms/speech, other-sign icons, clock, phone, hospital, no food/water/medicine, hourglass |
| 6 | `design7.py` (revision 2; `design6.py` = first version) | Every card, the FAST panel, captions, sound cues; the standard closing (same as `brand/outro/`) |
| 7 | `render7.py` (revision 2; `render6.py` = first version) | Decode, per-clip exposure match + cinematic grade, steady face-anchored framing, straight cuts between clips and soft blends inside a clip, soft blur behind the FAST panel, graphics, captions, x264. `--stills t1,t2 dir`, `--qa 3` (face check) |
| 8 | `sounds.py`, `sounds2.py`, `audio7.py` | Voice clean-up and per-sentence levelling, quiet SFX, calm music bed with natural fade-out, −14 LUFS master |

Environment: `WORK=<work dir>` (shots, `shotN.wav` at 16 kHz mono, `shotN_words.json`, `segments.json`), `BRAND=<dir with logo_*.png>`
(see `/brand/logo/`), `FONT_DIR` (DM Sans, Playfair Display Italic, Caveat from google/fonts). Models: sherpa-onnx Whisper and
Parakeet, Silero VAD, OpenCV YuNet face detector.
