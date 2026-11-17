# Break The Silence graphics (on top of the shared Saisha-reel graphics in gfx.py):
#   * taunt highlights: the insults in big white bold type, punched in as she says them, fading out after
#   * the big "Break The Silence" title (Playfair Display Bold, "Silence" in The Cub orange)
import os
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
import gfx as G

FD = G.FD
W, H = 1080, 1920
WHITE, ORANGE = (255, 255, 255), G.ORANGE

# text on screen for each taunt phrase: (small lead line, big key words)
HIGHLIGHTS = {
    "Hey, you loser!": ("Hey, you", "LOSER!"),
    "You fatty dumbo!": ("You", "FATTY DUMBO!"),
    "Why do you always cry?": ("Why do you", "ALWAYS CRY?"),
    "You crybaby?": ("You", "CRYBABY?"),
}
HL_CY = 1150


@lru_cache(None)
def dm(size, wght=800):
    f = ImageFont.truetype(f"{FD}/DMSans-VF.ttf", size)
    f.set_variation_by_axes([min(40, max(9, size / 2.2)), wght])
    return f


def ink(s, f, fill):
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (int(f.getlength(s)) + 20, asc + desc + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), s, font=f, fill=fill + (255,))
    return im.crop(im.getchannel("A").getbbox())


@lru_cache(None)
def highlight_img(text):
    lead, key = HIGHLIGHTS[text]
    a = ink(lead, dm(62, 700), WHITE)
    size = 150
    b = ink(key, dm(size, 900), WHITE)
    while b.width > W - 90:                                   # keep the big line inside the frame
        size -= 6; b = ink(key, dm(size, 900), WHITE)
    gap = 18
    im = Image.new("RGBA", (max(a.width, b.width), a.height + gap + b.height), (0, 0, 0, 0))
    im.alpha_composite(a, ((im.width - a.width) // 2, 0)); im.alpha_composite(b, ((im.width - b.width) // 2, a.height + gap))
    return G.shadowed(im, blur=16, off=(0, 6), alpha=200, spread=2)


def draw_highlight(frame, t, text, t_in, t_out):
    """Punch in (scale 1.12 -> 1.0, 0.18 s), hold, then fade out (0.35 s) drifting up slightly."""
    if t < t_in or t > t_out + 0.35:
        return
    p = G.clamp((t - t_in) / 0.18)
    k_in = G.clamp((t - t_in) / 0.10)
    k_out = 1 - G.ease_io((t - t_out) / 0.35)
    k = min(k_in, k_out)
    if k <= 0.01:
        return
    sc = 1.12 - 0.12 * G.ease_out(p)
    im = highlight_img(text)
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    dy = -int(14 * (1 - k_out))
    frame.alpha_composite(G.with_alpha(im, k), ((W - im.width) // 2, HL_CY - im.height // 2 + dy))


# ------------------------------------------------------------------ title
TITLE_CY = 1110


@lru_cache(None)
def title_img():
    f = ImageFont.truetype(f"{FD}/PlayfairDisplay-700.ttf", 168)
    l1 = ink("Break The", f, WHITE)
    l2 = ink("Silence", f, ORANGE)
    gap = 26
    im = Image.new("RGBA", (max(l1.width, l2.width), l1.height + gap + l2.height), (0, 0, 0, 0))
    im.alpha_composite(l1, ((im.width - l1.width) // 2, 0)); im.alpha_composite(l2, ((im.width - l2.width) // 2, l1.height + gap))
    return G.shadowed(im, blur=18, off=(0, 6), alpha=190, spread=2)


def draw_title(frame, t, t_in, t_out):
    if t < t_in or t > t_out + 0.35:
        return
    p = G.ease_out(G.clamp((t - t_in) / 0.40))
    k = min(p, 1 - G.ease_io((t - t_out) / 0.35))
    if k <= 0.01:
        return
    sc = 0.94 + 0.06 * p
    im = title_img()
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    frame.alpha_composite(G.with_alpha(im, k), ((W - im.width) // 2, TITLE_CY - im.height // 2 + int(16 * (1 - p))))
