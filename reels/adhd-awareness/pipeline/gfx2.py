# Brand type + shape primitives (PIL). Palette from the supplied brand sheet.
import os
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FD = os.environ.get("FONT_DIR", "/tmp/claude-0/fonts")
ORANGE = (240, 133, 62, 255)     # The Cub Orange  #F0853E
CHAR = (43, 43, 43, 255)         # Charcoal        #2B2B2B
CREAM = (253, 246, 238, 255)     # Cream           #FDF6EE
WHITE = (255, 255, 255, 255)

FAMILIES = {"dm": "DMSans-VF.ttf", "dmi": "DMSans-Italic-VF.ttf", "eb": "EBGaramond-VF.ttf", "ebi": "EBGaramond-Italic-VF.ttf",
            "pfi": "PlayfairDisplay-Italic-VF.ttf", "cav": "Caveat-VF.ttf"}


def a(c, alpha):
    return (c[0], c[1], c[2], int(alpha))


@lru_cache(None)
def font(fam, weight, size):
    f = ImageFont.truetype(f"{FD}/{FAMILIES[fam]}", size)
    if fam.startswith("dm"):
        f.set_variation_by_axes([min(40, max(9, size / 2.2)), weight])
    else:
        f.set_variation_by_axes([weight])
    return f


def text_w(s, fam="dm", weight=700, size=60, tracking=0):
    f = font(fam, weight, size)
    return int(f.getlength(s) + tracking * max(0, len(s) - 1))


def text(s, fam="dm", weight=700, size=60, fill=CHAR, tracking=0):
    """Text image cropped to cap-height .. descender band, so strings of different shape share one baseline box."""
    f = font(fam, weight, size)
    asc, desc = f.getmetrics()
    cap_top = f.getbbox("H")[1]
    pad = 4
    w = text_w(s, fam, weight, size, tracking) + 2 * pad
    top = max(0, cap_top - int(0.06 * size))
    bot = asc + int(0.26 * size)
    im = Image.new("RGBA", (w, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if tracking:
        x = pad
        for ch in s:
            d.text((x, pad), ch, font=f, fill=fill)
            x += f.getlength(ch) + tracking
    else:
        d.text((pad, pad), s, font=f, fill=fill)
    return im.crop((0, top + pad - 2, w, bot + pad))


def row(items, gap=14, valign="center"):
    items = [i for i in items if i is not None]
    w = sum(i.width for i in items) + gap * (len(items) - 1)
    h = max(i.height for i in items)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for i in items:
        y = (h - i.height) // 2 if valign == "center" else (h - i.height if valign == "bottom" else 0)
        im.alpha_composite(i, (x, y))
        x += i.width + gap
    return im


def col(items, gap=10, align="center"):
    items = [i for i in items if i is not None]
    w = max(i.width for i in items)
    h = sum(i.height for i in items) + gap * (len(items) - 1)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for i in items:
        x = (w - i.width) // 2 if align == "center" else (0 if align == "left" else w - i.width)
        im.alpha_composite(i, (x, y))
        y += i.height + gap
    return im


def rounded(w, h, r, fill, outline=None, width=0):
    s = 3
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * s - 1, h * s - 1), r * s, fill=fill, outline=outline, width=width * s)
    return im.resize((w, h), Image.LANCZOS)


def circle(d, fill, outline=None, width=0):
    s = 4
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((0, 0, d * s - 1, d * s - 1), fill=fill, outline=outline, width=width * s)
    return im.resize((d, d), Image.LANCZOS)


def pill(content, bg=CREAM, px=34, py=18, r=None, outline=None, width=0, min_w=0):
    w = max(content.width + 2 * px, min_w)
    h = content.height + 2 * py
    im = rounded(w, h, r if r is not None else h // 2, bg, outline, width)
    im.alpha_composite(content, ((w - content.width) // 2, (h - content.height) // 2))
    return im


def shadow(im, off=(0, 10), blur=18, alpha=70, color=(43, 43, 43)):
    pad = blur * 2 + max(abs(off[0]), abs(off[1]))
    W, H = im.width + 2 * pad, im.height + 2 * pad
    m = Image.new("L", (W, H), 0)
    m.paste(im.getchannel("A"), (pad + off[0], pad + off[1]))
    m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", (W, H), color + (0,))
    sh.putalpha(m)
    sh.alpha_composite(im, (pad, pad))
    return sh


def with_alpha(im, k):
    if k >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * k)))
    return im


def underline(w, h=10, color=ORANGE):
    return rounded(w, h, h // 2, color)
