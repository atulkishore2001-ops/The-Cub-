# Turn the supplied logo JPEG into clean transparent PNGs (colour-unmixed against its flat off-white background).
import sys, numpy as np
from PIL import Image
src, outdir = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
H, W, _ = im.shape
bg = np.median(im.reshape(-1, 3), 0)                      # flat background (247,247,247)
fgs = np.array([[66, 66, 66], [240, 133, 62]], np.float32)  # logo charcoal + orange as drawn in the artwork
best_res = np.full((H, W), 1e9, np.float32); alpha = np.zeros((H, W), np.float32); col = np.zeros((H, W, 3), np.float32)
for c in fgs:
    v = c - bg
    a = np.clip(((im - bg) * v).sum(2) / (v * v).sum(), 0, 1)
    res = np.linalg.norm(im - (bg + a[..., None] * v), axis=2)
    m = res < best_res
    best_res[m], alpha[m], col[m] = res[m], a[m], c
alpha[alpha < 0.04] = 0                                    # kill JPEG halo
alpha = np.clip(alpha * 1.04, 0, 1)
# the artwork's whiskers run off both edges: feather the outer columns so they don't end in a hard cut
ramp = np.ones(W, np.float32); n = 26
ramp[:n] = np.linspace(0, 1, n) ** 1.5; ramp[-n:] = np.linspace(1, 0, n) ** 1.5
alpha *= ramp[None, :]
rgba = np.dstack([col, alpha * 255]).astype(np.uint8)
full = Image.fromarray(rgba, "RGBA")
full.crop((0, 262, W, 1338)).save(f"{outdir}/logo_full.png")        # face + wordmark
full.crop((0, 262, W, 1040)).save(f"{outdir}/logo_mark.png")        # face only
full.crop((60, 1120, W - 60, 1338)).save(f"{outdir}/logo_wordmark.png")
print(full.crop((0, 262, W, 1338)).size, full.crop((0, 262, W, 1040)).size, full.crop((60, 1120, W - 60, 1338)).size)
# preview on cream + charcoal
for name, bgc in (("cream", (253, 246, 238)), ("charcoal", (43, 43, 43))):
    cv = Image.new("RGB", (900, 700), bgc); lg = Image.open(f"{outdir}/logo_full.png"); lg = lg.resize((800, int(lg.height * 800 / lg.width)), Image.LANCZOS)
    cv.paste(lg, (50, 40), lg); cv.save(f"{outdir}/preview_{name}.png")
