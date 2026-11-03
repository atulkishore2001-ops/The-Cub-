# Sprite-building helpers (PIL): text, emoji, pills, rows/columns, shadows.
import os
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = os.environ.get("FONT_DIR", "/tmp/claude-0/fonts")
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

INK = (24, 27, 52, 255)
YEL = (255, 206, 58, 255)
CORAL = (255, 99, 99, 255)
TEAL = (38, 194, 176, 255)
CREAM = (255, 248, 236, 255)
WHITE = (255, 255, 255, 255)
BLACK = (12, 12, 18, 255)


@lru_cache(None)
def font(weight, size):
    return ImageFont.truetype(f"{FONT_DIR}/Poppins-{weight}.ttf", size)


@lru_cache(None)
def emoji(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (180, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    s = size / max(im.size)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def text(s, weight="ExtraBold", size=60, fill=WHITE, stroke=0, stroke_fill=BLACK, tracking=0):
    f = font(weight, size)
    pad = stroke + 4
    asc, desc = f.getmetrics()
    if tracking:
        widths = [f.getlength(c) + tracking for c in s]
        w = int(sum(widths) - tracking) + 2 * pad
    else:
        w = int(f.getlength(s)) + 2 * pad
    h = asc + desc + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if tracking:
        x = pad
        for c, cw in zip(s, widths):
            d.text((x, pad), c, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
            x += cw
    else:
        d.text((pad, pad), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    # trim vertical to glyph-ish box but keep consistent baseline: crop to cap-height band
    top = int(pad + asc * 0.18)
    bot = int(pad + asc + desc * 0.35)
    return im.crop((0, max(0, top - stroke - 2), w, min(h, bot + stroke + 2)))


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
    s = 3  # supersample for smooth corners
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * s - 1, h * s - 1), r * s, fill=fill,
                                         outline=outline, width=width * s)
    return im.resize((w, h), Image.LANCZOS)


def circle(d, fill):
    s = 4
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((0, 0, d * s - 1, d * s - 1), fill=fill)
    return im.resize((d, d), Image.LANCZOS)


def pill(content, bg=WHITE, px=34, py=18, r=None, outline=None, width=0, min_w=0):
    w = max(content.width + 2 * px, min_w)
    h = content.height + 2 * py
    im = rounded(w, h, r if r is not None else h // 2, bg, outline, width)
    im.alpha_composite(content, ((w - content.width) // 2, (h - content.height) // 2))
    return im


def shadow(im, off=(0, 10), blur=14, alpha=110, spread=0):
    pad = blur * 2 + max(abs(off[0]), abs(off[1])) + spread
    W, H = im.width + 2 * pad, im.height + 2 * pad
    a = im.getchannel("A")
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = Image.new("L", (W, H), 0)
    m.paste(a, (pad + off[0], pad + off[1]))
    if spread:
        m = m.filter(ImageFilter.MaxFilter(spread * 2 + 1))
    m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255)
    sh.putalpha(m)
    sh.alpha_composite(im, (pad, pad))
    return sh


def badge(n, d=64, bg=YEL, fg=INK, size=38):
    c = circle(d, bg)
    t = text(str(n), "Black", size, fg)
    c.alpha_composite(t, ((d - t.width) // 2, (d - t.height) // 2 + 1))
    return c


def line(w, h, color):
    return rounded(w, h, h // 2, color)
