# OSIT Workshop: promotional video ad (Meta Reels)

**Speaker:** Stuti Sharma, Clinical Director & Speech-Language Pathologist, The Cub
**Source:** `OSIT REEL.mp4` (Google Drive, 1:44.8, 1080×1920 @ 60 fps, one continuous take), the four workshop photos, The Cub and SpeechGears logos, the OSIT poster (title design and registration QR). All in `assets/`.
**Output:** `TheCub_OSIT_Ad.mp4`: **73.7s** (revision 2), 1080×1920 (9:16), 30 fps, H.264 + AAC, −14 LUFS
**Alt version:** `TheCub_OSIT_Ad_NoMusic.mp4` has the same edit with voice and sound effects only.

---

## 0. Revision 2

| Feedback | Change |
|---|---|
| Sentence endings ("children", "clinicians", "practice"…) cut off before the frame changes | Every section now runs until her last word has fully died away, plus about 0.25s on her face before the cut. "Clinicians" had been cut 0.39s early, "practice" 0.21s and "children" 0.09s. She also drops her voice at the end of sentences, so a gentle voice leveller (dynamic normalisation) now lifts those quiet endings. Checked by re-transcribing the end of every section in the final mix: each one ends on its full last word |
| Closing frame elements felt stuck together | Re-spaced: about 40px of clear space between logos, title, date line, the "Register now" box and the QR (was 15–30px). The QR is 500px wide and still decodes from the rendered frames |
| Remove the bunting (multi-flag string) from the title | Removed from the poster's title design: the string and flags are gone, and the bottoms of the "O" and "S" are rebuilt with the same soft shadow. Used mid-video and in the closing frame (`assets/osit_title_no_bunting.png`) |
| Use the HD versions of the photos | All four replaced with the HD shots (1024–1254px wide), sharp as photo cards |

Also fixed: the "1,000+" count-up badge now redraws cleanly at every step.

The extra breathing room adds 2.5s (71.2s → 73.7s). The QR closing frame is still 6.6s.

## 1. Brief checklist

| Brief | Result |
|---|---|
| About 70s, 9:16, for paid Meta placements | **73.7s**, 1080×1920. Captions, graphics and the QR all sit between y 270 and y 1300 (Meta's Reels ad safe zone keeps the top 14% and bottom 35% clear of key content) |
| Strong hook in the first 3s | She opens on "If you're an SLP, OT, pediatrician, neurologist or physiotherapist watching this reel…". Each profession pops up as a green pill (poster green) the moment she says it, so the target audience recognises itself within 3 seconds |
| Introduction, purpose, practical learning, highlights, closing | Hook (0:00) → who she is, with name card (0:06) → why learning matters (0:10) → the workshop: OSIT title + dates (0:21) → SpeechGears collaboration + 1,000+ professionals trained (0:29) → the practical learning, over the workshop photos (0:43) → seats filling fast, last date 21 Nov (0:53) → "Join us…" (1:04) → closing frame with title, logos and QR (1:07.1–1:13.7) |
| Subtitles exactly as in the earlier reel | Same font (Glacial Indifference Bold 66 px), white with the same soft shadow, same 2–5 word phrases, same timing method (each phrase timed to the re-transcribed edit). Only the position moved up (to y 1215, from 1352) to stay above Meta's ad safe line |
| Use the provided title design, not a recreation | The OSIT title block is taken directly from the poster (bunting removed, as requested; rounded card, soft shadow), mid-video and in the closing frame |
| Logos in original proportions | The Cub and SpeechGears logos are scaled uniformly only. Shown together on an "In collaboration with" card when she mentions SpeechGears, and at the top of the closing frame |
| QR large, clear, scannable, 5–7s | **6.6s** of closing frame. The QR is 500 px wide (code area about 380 px, 35% of the screen width) in its red "SCAN TO REGISTER" frame. Checked: it decodes from the rendered frame at full size and at one third size, to `https://wa.me/message/NUBO5ZCGO5DCG1?src=qr` |
| Training photos for variety | All four, as framed photo cards over the speaker (softly blurred and dimmed behind them) while her voice continues: at "practical techniques", "1,000+ professionals trained", and through "learn oral sensory motor integration… apply it effectively into your clinical practice" |
| Animated callouts for key information | Date card ("5th – 6th December 2026 · 9 AM – 5 PM · The Cub, New Delhi"), "1,000+ professionals trained" (counts up), "Seats are filling up fast", "Last date to register: 21st November 2026". All use the poster's colours and DM Sans, and only fade, rise or pop in |
| Grade | Natural and bright: the slight magenta cast from the blue shirt is neutralised, exposure +4%, gentle contrast, a touch of warmth in the highlights, no added saturation (skin stays natural), soft vignette |
| Cuts and transitions | Straight cuts with a zoom change at each new section (close 1.28× / medium 1.06×), as in the Saisha reel revision 2. No blends. A 0.4s dissolve into the closing frame |
| Audio | Original voice, cleaned (light noise reduction, EQ, de-esser, gentle compression, every section levelled). Light, upbeat music bed (100 bpm piano pluck, soft pad, gentle kick and shaker) about 16 dB under the voice, rising on the closing frame and resolving with a chime. Very quiet pops and whooshes on the graphics only |

## 2. What was cut (104.8s → 66.7s of speech)

- Long pauses between sentences (up to 2.6s each; the audio is noise-gated, so they were digital silence).
- "The workshop is specifically designed for speech language pathologists, occupational therapists, pediatricians, neurologists and physiotherapists, as well as students pursuing their masters in these fields." The opening hook already names every profession; this was the longest repeat.
- "Join us on 5th and 6th December at The Cub for this OSIT workshop for two days of focused learning, meaningful insights and practical techniques." It repeats the dates and the "practical techniques" line said just before.
- A stray "Yes" before "That's why I'm really excited…".

Everything else plays as she said it, at 1.04× with pitch preserved. Every section was re-transcribed after editing to make sure no word is clipped.

## 3. Please check

1. **Masters students.** Cutting the "designed for…" line also drops the mention that Master's students can attend. If that matters for the ad, I can add a short "Also open to Master's students" callout, or put the line back (+11s).
2. **QR link.** The QR opens a WhatsApp chat (`wa.me/message/NUBO5ZCGO5DCG1`). Please confirm this is the registration link you want in a paid ad.
3. **Caption position.** Captions are slightly higher than in the Saisha reel, to stay clear of Meta's ad overlay. Font, size, colour and animation are unchanged.
