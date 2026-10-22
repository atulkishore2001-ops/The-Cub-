"""
Builds the image assets used by build.js from The Cub's own reference files
(brand docx + the three Instagram carousel PDFs). Nothing here is redrawn:
every asset is extracted, un-matted, up-scaled or cropped from the originals.

Run:  python3 -I prep_assets.py <uploads_dir> <out_dir>
Needs: pdfimages / pdftoppm (poppler), Pillow, numpy, node + sharp (for blob SVGs).
"""
import glob, json, os, re, subprocess, sys, tempfile, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

UP, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
TMP = tempfile.mkdtemp(prefix="cub_")

DOCX = glob.glob(f"{UP}/*Brand_Elements*.docx")[0]
PDF_LDM = glob.glob(f"{UP}/*Learning_Disability*.pdf")[0]
PDF_C4 = glob.glob(f"{UP}/*Carousel__4.pdf")[0]
PDF_C5 = glob.glob(f"{UP}/*Carousel__5.pdf")[0]

ORANGE = (240, 133, 62)  # #F0853E  The Cub Orange (brand colours image)


def save(im, name):
    im.save(f"{OUT}/{name}")
    print("wrote", name, im.size)


# --------------------------------------------------------------------- logo
with zipfile.ZipFile(DOCX) as z:
    z.extract("word/media/image2.png", TMP)
    z.extract("word/media/image1.png", TMP)
raw = Image.open(f"{TMP}/word/media/image2.png").convert("RGB")
a = np.asarray(raw).astype(float)
bg = 247.0                                   # flat #F7F7F7 background in the source
R, G, B = a[..., 0], a[..., 1], a[..., 2]
lum = a.mean(axis=2)
grey = np.abs(R - B) < 14
ink = float(np.percentile(lum[grey & (lum < 120)], 1))   # charcoal ink of the logo
orange_like = (R - B) > 28
alpha = np.where(orange_like, np.clip((bg - B) / (bg - ORANGE[2]), 0, 1),
                 np.clip((bg - lum) / (bg - ink), 0, 1))
alpha[alpha < 0.02] = 0
rgb = np.where(orange_like[..., None], np.array(ORANGE, float), np.array([ink] * 3))
logo = Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")
bb = logo.getbbox()
logo = logo.crop((bb[0], bb[1] - 6, bb[2], bb[3] + 6))
save(logo, "logo_full.png")

rows = np.asarray(logo)[..., 3].sum(axis=1)
empty = np.where(rows < 50)[0]
# first long empty run after the face = gap between face and wordmark
gap = None
for i in range(len(empty) - 1):
    if empty[i] > logo.height * 0.5 and empty[i + 1] - empty[i] == 1:
        gap = empty[i]
        break
face_bottom = gap
wm_rows = np.where(rows[face_bottom:] > 50)[0]
wm_top = face_bottom + wm_rows[0]
face = logo.crop((0, 0, logo.width, face_bottom + 4))
mark = logo.crop((0, wm_top - 4, logo.width, logo.height))
save(face, "mascot_face.png")
save(mark, "wordmark.png")


# Horizontal lockup (face + wordmark side by side), as used in the co-brand
# line-up on Carousel 4 (slides 1 and 6): wordmark ~2.2x the face width.
fw = 900
f2 = face.resize((fw, round(face.height * fw / face.width)), Image.LANCZOS)
ww = round(fw * 2.2)
w2 = mark.resize((ww, round(mark.height * ww / mark.width)), Image.LANCZOS)
gap = 90
lock = Image.new("RGBA", (fw + gap + ww, f2.height), (0, 0, 0, 0))
lock.alpha_composite(f2, (0, 0))
lock.alpha_composite(w2, (fw + gap, (f2.height - w2.height) // 2 + 20))
save(lock, "logo_horizontal.png")

# ------------------------------------------------- doodles (LDM post rasters)
subprocess.run(["pdfimages", "-png", PDF_LDM, f"{TMP}/ldm"], check=True)
for img_i, mask_i, name in ((1, 2, "doodle_question.png"), (3, 4, "doodle_parent_child.png")):
    im = Image.open(f"{TMP}/ldm-{img_i:03d}.png").convert("RGB")
    im.putalpha(Image.open(f"{TMP}/ldm-{mask_i:03d}.png").convert("L"))
    save(im, name)


# ------------------------------------------- small motifs from the carousels
def pair_images(pdf, tag):
    d = f"{TMP}/{tag}"
    os.makedirs(d, exist_ok=True)
    subprocess.run(["pdfimages", "-png", pdf, f"{d}/i"], check=True)
    files = {int(os.path.basename(f)[2:5]): f for f in glob.glob(f"{d}/i-*.png")}
    out = {}
    for k in sorted(files):
        im = Image.open(files[k])
        nxt = files.get(k + 1)
        if nxt:
            m = Image.open(nxt)
            if m.mode == "L" and m.size == im.size and im.mode in ("RGB", "RGBA"):
                im = im.convert("RGB")
                im.putalpha(m)
                out[k] = im
                continue
        if im.mode == "L" and (k - 1) in out and out[k - 1].size == im.size:
            continue
        out[k] = im.convert("RGBA")
    return out


c5 = pair_images(PDF_C5, "c5")


def smooth_up(im, scale=4, k=3.2, recolor=None):
    """Up-scale a flat-colour RGBA motif and re-sharpen its soft alpha edge."""
    im = im.convert("RGBA")
    w, h = im.size
    big = im.resize((w * scale, h * scale), Image.LANCZOS)
    r, g, b, al = big.split()
    al = al.filter(ImageFilter.GaussianBlur(scale * 0.35))
    arr = np.asarray(al).astype(float) / 255
    arr = np.clip((arr - 0.5) * k + 0.5, 0, 1)
    al = Image.fromarray((arr * 255).astype(np.uint8))
    if recolor:
        flat = Image.new("RGB", big.size, recolor)
        r, g, b = flat.split()
    return Image.merge("RGBA", (r, g, b, al))


motifs = {  # element index in Carousel 5 -> (file name, recolour to guideline colour?)
    5: ("spark.png", ORANGE),
    11: ("bulb.png", ORANGE),
    47: ("heart_doodle.png", ORANGE),
    36: ("quote.png", ORANGE),
    39: ("heart_white.png", None),
    3: ("dots_cream.png", None),
    13: ("blob_cream_a.png", None),
    7: ("blob_cream_b.png", None),
    59: ("blob_cream_c.png", None),
    41: ("blob_cream_d.png", None),
    19: ("quarter.png", ORANGE),
    9: ("curve_line.png", ORANGE),
}
for idx, (name, col) in motifs.items():
    save(smooth_up(c5[idx], recolor=col), name)

# ------------------------------------------ photos used in the posts (rounded)
def rounded(im, radius_frac=0.07, border=None, border_w=0, max_w=1200):
    im = im.convert("RGBA")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    ss = 4
    w, h = im.size
    r = int(min(w, h) * radius_frac)
    mask = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    mask = mask.resize((w, h), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    if border:
        ring = Image.new("L", (w * ss, h * ss), 0)
        d = ImageDraw.Draw(ring)
        d.rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
        d.rounded_rectangle((border_w * ss, border_w * ss, (w - border_w) * ss - 1, (h - border_w) * ss - 1),
                            max(r - border_w, 2) * ss, fill=0)
        ring = ring.resize((w, h), Image.LANCZOS)
        out.paste(Image.new("RGBA", (w, h), border + (255,)), (0, 0), ring)
    return out


save(rounded(c5[21]), "photo_yarn.png")          # tangled thread / head
save(rounded(c5[65], max_w=900), "photo_blocks.png")   # ADHD letter blocks on orange
save(rounded(c5[38], border=ORANGE, border_w=18), "photo_notebook.png")

# ------------------------------------------------ real blob vectors (LDM post)
# The two big orange organic shapes in the LDM carousel are vector paths filled
# with exactly #F0853E. They are rasterised here, cropped to their own extent.
svg = subprocess.run(["pdftocairo", "-svg", PDF_LDM, f"{TMP}/ldm.svg"], check=True)
from lxml import etree  # noqa: E402

SV = "{http://www.w3.org/2000/svg}"
root = etree.parse(f"{TMP}/ldm.svg", etree.XMLParser(huge_tree=True)).getroot()
paths = list(root.iter(SV + "path"))
blobs = {}
for idx, clip in ((763, "clip-7"), (764, "clip-12")):
    p = paths[idx]
    assert "94.1" in (p.getparent().get("fill") or p.get("fill") or "94.1"), "unexpected blob fill"
    cd = root.xpath(f'//*[@id="{clip}"]')[0][0].get("d")
    blobs[idx] = {"d": p.get("d"), "clip": cd}
json.dump(blobs, open(f"{TMP}/blobs.json", "w"))
js = f"""
const sharp=require('sharp'),fs=require('fs');
const b=JSON.parse(fs.readFileSync('{TMP}/blobs.json'));
const crops={{763:[523,1709],764:[2296,3338]}};
(async()=>{{for(const k of Object.keys(b)){{
  const [x0,x1]=crops[k], w=x1-x0;
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${{w*2}}" height="2025" viewBox="${{x0}} 0 ${{w}} 1012.5"><defs><clipPath id="c"><path d="${{b[k].clip}}"/></clipPath></defs><g clip-path="url(#c)"><path d="${{b[k].d}}" fill="#F0853E"/></g></svg>`;
  await sharp(Buffer.from(svg),{{density:72}}).png().toFile('{OUT}/blob_orange_'+(k==763?'a':'b')+'.png');
}}}})();
"""
open(f"{TMP}/blob.js", "w").write(js)
subprocess.run(["node", f"{TMP}/blob.js"], check=True, env={**os.environ, "NODE_PATH": os.path.abspath("node_modules")})
for n in ("blob_orange_a.png", "blob_orange_b.png"):
    im = Image.open(f"{OUT}/{n}")
    im = im.crop(im.getbbox())
    save(im, n)

# ---------------------------------------------------------- post renders
def render_post(pdf, prefix, dpi=76):
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), pdf, f"{TMP}/{prefix}"], check=True)
    return sorted(glob.glob(f"{TMP}/{prefix}-*.png"))


for i, f in enumerate(render_post(PDF_C5, "p5"), 1):
    save(rounded(Image.open(f), 0.035), f"post_c5_{i}.png")
for i, f in enumerate(render_post(PDF_C4, "p4"), 1):
    if i in (1, 5, 6):
        save(rounded(Image.open(f), 0.035), f"post_c4_{i}.png")
wide = render_post(PDF_LDM, "pl", dpi=76)[0]
wi = Image.open(wide)
sw = wi.width // 5
for i in range(5):
    save(rounded(wi.crop((i * sw, 0, (i + 1) * sw, wi.height)), 0.035), f"post_ldm_{i + 1}.png")
print("done ->", OUT)
