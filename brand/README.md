# The Cub brand kit (for reels)

## Colours
| Name | Hex |
|---|---|
| The Cub Orange | `#F0853E` |
| Charcoal | `#2B2B2B` |
| Cream | `#FDF6EE` |
| White | `#FFFFFF` |

## Logo (`logo/`)
- `logo_src.jpg`, `palette_src.jpg`: originals as supplied.
- `logo_full.png` (tiger face + THE CUB), `logo_mark.png` (face only), `logo_wordmark.png` (THE CUB only): transparent cut-outs. Use on cream or white backgrounds only.

## Type
DM Sans (body and captions), Playfair Display Italic (tagline and accent words), EB Garamond Italic (accents). All are free from google/fonts.

## Standard ending: logo reveal (`outro/`)
**Every reel ends with this closing frame**, exactly as in the Anjali learning-disabilities reel:

1. Right after the last spoken word, the picture cross-fades into cream (1.0s, eased).
2. The full logo fades in while settling from 94% to 100% size.
3. "*Every Child Deserves To Be Seen*" in Playfair Display Italic is revealed by a soft left-to-right ink wipe, rising slightly.
4. A short orange rule draws out under the tagline.
5. Hold for about 1.5s. A soft chime plays with the logo; the music resolves on a final chord and fades out naturally (no hard stop).

The full sequence runs 4.2s after the last word. `outro/outro.py` renders it frame by frame (`outro.frame(t, base_frame)`), with all positions, sizes and timings in the file header. `outro_reference.mp4` and `outro_reference_final.png` show the result.
