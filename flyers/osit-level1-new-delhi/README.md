# OSIT Level-1 – New Delhi flyer

4:5 portrait promotional flyer (1080 × 1350 layout) for WhatsApp and social media.

| File | Use |
| --- | --- |
| `osit-level1-new-delhi-flyer.png` | Master, 2160 × 2700. |
| `osit-level1-new-delhi-flyer-1080x1350.jpg` | Smaller file for WhatsApp and Instagram. |
| `index.html` + `assets/` | Editable source. |

To change anything, edit `index.html` and run this from the repository root (needs Node and the `playwright` package):

```bash
node flyers/osit-level1-new-delhi/render.js
```

## Notes

- The QR code is the exact image from the speakers flyer (`assets/qr/`). It decodes to `https://wa.me/message/NUBO5ZCGO5DCG1?src=qr` in both exports.
- The Cub logo is the horizontal lockup from the speakers flyer, rebuilt from the original high-resolution logo artwork with the same arrangement and proportions. The SpeechGears logo is the cut-out from that flyer (about 265 px wide), so it is slightly soft in the 2160 px version.
- Speaker photos are the small crops saved from the speakers flyer. Swap in the originals if available.
- The bunting under the "O" is recoloured from the Philippine flag colours in the reference to saffron, white and green.
- Fonts: Poppins (SIL Open Font License). Icons: Tabler Icons (MIT).
