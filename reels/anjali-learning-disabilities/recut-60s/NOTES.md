# 59.5-second re-cut, full quality

**File:** `TheCub_LearningDisabilities_Reel_60s.mp4`: **59.47s** (1784 frames), 1080×1920, 30 fps, H.264 High, two-pass 11.5 Mbps (just under GitHub's 100 MB file limit; SSIM 0.996 against the lossless-quality CRF 12 master) + AAC 320 kbps, −14 LUFS
**Alt:** `TheCub_LearningDisabilities_Reel_60s_NoMusic.mp4`: the same cut without the music bed.

This is a frame-accurate, full-resolution rebuild of the re-cut you sent as `WhatsApp Video 2026-10-24 at 6.02.32 PM.mp4` (576×1024, about 1.3 Mbps). Every frame is rendered again from the original Anjali 1/2/3 clips, through the same pipeline as revision 3, and encoded only once. Nothing is upscaled from the WhatsApp file.

## What your re-cut does (measured from the WhatsApp export)

| Re-cut time | Content (revision 3 time) | Framing |
|---|---|---|
| 0:00.0–0:02.9 | "Your child is not lazy. He just learns differently." (1:06.9–1:09.8) | 1.069× zoom, centred |
| 0:02.9–0:10.7 | "Is your child also struggling… but his marks are low?" (0:00.1–0:07.8) | No zoom |
| 0:10.7–0:20.0 | "Hi, this is Anjali Rawat…" through "nothing to do with intelligence" (0:17.4–0:26.7) | 1.069× zoom, framed up and left |
| 0:20.0–0:37.1 | Early signs: the "6–8 years" card, b/d, handwriting and spelling cards (0:26.7–0:43.8) | No zoom |
| 0:37.1–0:42.8 | "And these are not because they aren't bright… works differently" (0:43.8–0:49.5) | 1.069× zoom, centred |
| 0:42.8–0:51.5 | "Don't label your child… support can start much earlier" (0:55.2–1:03.9) | No zoom |
| 0:51.5–0:59.5 | "If you notice the signs…" then the logo and tagline (1:10.4–1:18.4) | 1.069× zoom, centred |

Removed from revision 3: "He can read but doesn't understand…", "He knows the answer at home…", "Many of the children do best… small and specific steps", and "With early help, your child can do wonders."

**Joins.** At 0:02.9, 0:10.7 and 0:42.8 there is a 2-frame cross-fade, then the incoming shot settles from slightly zoomed-in to its framing over about 10 frames. At 0:51.5 there is a 2-frame cross-fade. Each was measured frame by frame and reproduced.

**Audio.** The revision-3 mix (uncompressed source), cut at the same points with 0.1s cross-fades and a 0.5s fade-out at the end, as in your export.

## Accuracy check
Rendered frames were compared with the matching frames of your export (both scaled down to the same size): correlation 0.995–0.999, including the cross-fade frames. The remaining difference is WhatsApp compression. The audio lines up with your export to within a quarter of a millisecond. The small colour difference in the WhatsApp file (reds 1–4 levels higher) comes from WhatsApp's re-encoding, so the original colours are kept.

## Note
Because the re-cut ends at 59.47s, the tagline finishes revealing at about 0:59.1 and its orange rule at about 0:59.2. The complete closing frame is therefore on screen for only about 0.25s before the video ends (as in your export). If you'd like it to hold longer, extending the ending by 1–2s is a quick change.

Pipeline: `../pipeline/recut/` (`plan.py` measures the re-cut, `plan.json` is the measured frame plan, `render_recut.py` and `audio_recut.py` render it).
