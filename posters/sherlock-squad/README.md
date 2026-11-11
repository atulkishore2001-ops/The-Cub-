# The Sherlock Squad – poster

Cleaned-up rebuild of the Canva poster for The Cub's *Junior Forensics Academy* workshop.

| File | Use |
| --- | --- |
| `sherlock-squad-poster.pdf` | Print. 768 × 1152 pt, the same size as the original. Text is vector. |
| `sherlock-squad-poster.png` | Sharing (WhatsApp, Instagram, email). 2048 × 3072 px. |
| `index.html` + `assets/` | Editable source. |

## What changed from the original

**Repeats removed**
- Fingerprinting, Handwriting Analysis and Chemistry were listed three times: in the intro paragraph, in a three-card row, and again in "Activities they'll love". They now appear once, in "Activities they'll love".
- "Group size: 6 children" and "Spots limited to 6 detectives per case" were merged into a single **Group size: 6 detectives per case** fact with a *Spots limited!* tag.
- The "Hands-on Science" benefit repeated the Chemistry text (chromatography and simple lab tests). It was folded into **Builds real deductive skills**, so there are now five benefits instead of six.
- "Collaboration" no longer repeats the group size of six.
- The second deerstalker hat icon in the info strip was removed. The hat beside the title stays.

**Clutter removed:** the floating magnifying glass beside the cards, the paw-print circles, the stray arrows, and the scattered brush marks and dots. The duplicated logo layer is gone too.

**Kept the same:** The Cub logo (the original file), the boy-detective photo, the colours, the title with its magnifying glass and hat, the "Starting 14 Nov" badge, the facts and the contact details.

## Editing and re-exporting

Edit `index.html`, then run this from the repository root:

```bash
node posters/sherlock-squad/render.js
```

This needs Node and the `playwright` package with Chromium.

Fonts are Lilita One, Baloo 2 and Nunito from Google Fonts, under the SIL Open Font License. Icons are from Tabler Icons (MIT).
