"""Render transparent 2160x3840 title overlays (credit + couple title) matching the reference look."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys, os
F = os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts')
W, H = 2160, 3840
out = sys.argv[1]; os.makedirs(out, exist_ok=True)

def tracked(draw, text, font, y, fill, track, cx=W//2):
    widths = [draw.textlength(c, font=font) for c in text]
    total = sum(widths) + track*(len(text)-1)
    x = cx - total/2
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=font, fill=fill); x += w + track

def var(name, wght, size):
    f = ImageFont.truetype(os.path.join(F, name), size)
    try: f.set_variation_by_axes([wght])
    except Exception: pass
    return f

# 1) "A FILM BY / ATUL KISHORE" — thin wide-tracked sans on black (reference opening)
im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
tracked(d, 'A FILM BY', var('Montserrat[wght].ttf', 300, 46), H//2 - 95, (200, 200, 200, 255), 10)
tracked(d, 'ATUL KISHORE', var('Montserrat[wght].ttf', 300, 104), H//2 - 10, (235, 235, 235, 255), 16)
im.save(os.path.join(out, 'credit.png'))

# 2) "Engagement Of" gold script + "ANKITA & VANSH" white serif caps (reference thumbnail)
im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
y0 = int(H*0.70)
script = ImageFont.truetype(os.path.join(F, 'GreatVibes-Regular.ttf'), 170)
d.text((W//2 + 150, y0), 'Engagement Of', font=script, fill=(226, 180, 72, 255), anchor='ms')
tracked(d, 'ANKITA & VANSH', var('Cinzel[wght].ttf', 400, 165), y0 + 40, (250, 246, 238, 255), 14)
# soft shadow for legibility over footage
sh = im.split()[3].filter(ImageFilter.GaussianBlur(18)).point(lambda a: int(a*0.55))
shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); shadow.putalpha(sh)
Image.alpha_composite(shadow, im).save(os.path.join(out, 'title.png'))
print('ok')
