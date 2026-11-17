# 5 Science Facts motion graphics, in The Cub's palette (orange #F0853E, charcoal #2B2B2B, cream, white) with DM Sans.
# Every element pops, fades or draws on; nothing flies around. Captions (y 1352) and the name card (y 1500) come from gfx.py.
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import gfx as G

FD = G.FD
W, H = 1080, 1920
ORANGE, CHAR, CREAM, WHITE = G.ORANGE, G.CHAR, G.CREAM, (255, 255, 255)
GREEN, RED, BLUE, YELLOW = (46, 175, 98), (226, 54, 64), (52, 128, 255), (255, 206, 46)
clamp, ease_out, ease_io, back_out = G.clamp, G.ease_out, G.ease_io, G.back_out


@lru_cache(None)
def dm(size, wght=800):
    f = ImageFont.truetype(f"{FD}/DMSans-VF.ttf", size)
    f.set_variation_by_axes([min(40, max(9, size / 2.2)), wght])
    return f


def ink(s, f, fill, tracking=0):
    asc, desc = f.getmetrics()
    wdt = int(f.getlength(s) + tracking * max(0, len(s) - 1)) + 20
    im = Image.new("RGBA", (wdt, asc + desc + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); x = 10
    if tracking:
        for ch in s:
            d.text((x, 10), ch, font=f, fill=fill + (255,)); x += f.getlength(ch) + tracking
    else:
        d.text((10, 10), s, font=f, fill=fill + (255,))
    return im.crop(im.getchannel("A").getbbox())


def rrect(w, h, r, fill, outline=None, width=0):
    s = 3
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * s - 1, h * s - 1), r * s, fill=fill, outline=outline, width=width * s)
    return im.resize((w, h), Image.LANCZOS)


def shadow(im, blur=18, off=(0, 8), alpha=110):
    pad = blur * 3
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    m = Image.new("L", out.size, 0); m.paste(im.getchannel("A"), (pad + off[0], pad + off[1]))
    m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", out.size, (10, 10, 10, 0)); sh.putalpha(m)
    out.alpha_composite(sh); out.alpha_composite(im, (pad, pad))
    return out


def stack(items, gap=12):
    w = max(i.width for i in items); h = sum(i.height for i in items) + gap * (len(items) - 1)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
    for i in items:
        im.alpha_composite(i, ((w - i.width) // 2, y)); y += i.height + gap
    return im


def place(frame, im, cx, cy, k=1.0, scale=1.0, dy=0, rot=0.0):
    if k <= 0.01:
        return
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if abs(scale - 1) > 0.004:
        im = im.resize((max(2, int(im.width * scale)), max(2, int(im.height * scale))), Image.LANCZOS)
    frame.alpha_composite(G.with_alpha(im, k), (int(cx - im.width / 2), int(cy - im.height / 2 + dy)))


def life(t, t_in, t_out, a=0.30, b=0.25):
    return clamp((t - t_in) / a), 1 - ease_io((t - t_out) / b)


def pop(frame, im, t, t_in, t_out, cx, cy, rot=0.0):
    p, k = life(t, t_in, t_out, 0.28, 0.25)
    if p > 0 and k > 0:
        place(frame, im, cx, cy, k=min(1, p * 3) * k, scale=max(0.3, back_out(p)), rot=rot)


def rise(frame, im, t, t_in, t_out, cx, cy):
    p, k = life(t, t_in, t_out, 0.35, 0.25)
    if p > 0 and k > 0:
        e = ease_out(p)
        place(frame, im, cx, cy, k=e * k, scale=0.96 + 0.04 * e, dy=int(22 * (1 - e)))


# ------------------------------------------------------------------ hook
@lru_cache(None)
def pill(text, bg, fg=WHITE, size=34):
    t = ink(text, dm(size, 800), fg, tracking=3)
    p = rrect(t.width + 70, t.height + 40, (t.height + 40) // 2, bg + (255,))
    p.alpha_composite(t, (35, 20))
    return shadow(p, 14, (0, 6), 90)


@lru_cache(None)
def title_img():
    a = ink("5 FACTS THAT", dm(104, 900), WHITE)
    b1 = ink("SOUND", dm(132, 900), WHITE); b2 = ink("FAKE", dm(132, 900), ORANGE)
    gap = 38                                                        # word space (ink() crops trailing spaces)
    line2 = Image.new("RGBA", (b1.width + gap + b2.width, max(b1.height, b2.height)), (0, 0, 0, 0))
    line2.alpha_composite(b1, (0, line2.height - b1.height)); line2.alpha_composite(b2, (b1.width + gap, line2.height - b2.height))
    return G.shadowed(stack([a, line2], 14), blur=16, off=(0, 6), alpha=200, spread=2)


def draw_title(frame, t, t_in, t_out):
    rise(frame, title_img(), t, t_in, t_out, W / 2, 1085)


@lru_cache(None)
def stamp_img(text, color):
    c = {"green": GREEN, "orange": ORANGE}[color]
    t = ink(text, dm(78, 900), c, tracking=4)
    w, h = t.width + 80, t.height + 56
    im = rrect(w, h, 18, (255, 255, 255, 235), outline=c + (255,), width=8)
    im.alpha_composite(t, (40, 28))
    return shadow(im, 16, (0, 8), 110)


# ------------------------------------------------------------------ fact number badge + chip
@lru_cache(None)
def number_img(n):
    d = 250; s = 3
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((0, 0, d * s - 1, d * s - 1), fill=ORANGE + (255,), outline=WHITE + (255,), width=10 * s)
    im = im.resize((d, d), Image.LANCZOS)
    tx = ink(f"#{n}", dm(120, 900), WHITE)
    im.alpha_composite(tx, ((d - tx.width) // 2, (d - tx.height) // 2 - 4))
    return shadow(im, 22, (0, 10), 120)


@lru_cache(None)
def chip_img(n, text):
    num = ink(f"FACT {n}/5", dm(30, 800), WHITE, tracking=2)
    lab = ink(text, dm(36, 800), CHAR, tracking=1)
    nb = rrect(num.width + 40, 64, 14, ORANGE + (255,)); nb.alpha_composite(num, (20, (64 - num.height) // 2))
    w = nb.width + lab.width + 60
    im = rrect(w, 84, 22, (255, 255, 255, 245))
    im.alpha_composite(nb, (10, 10)); im.alpha_composite(lab, (nb.width + 34, (84 - lab.height) // 2))
    return shadow(im, 14, (0, 6), 90)


def draw_number(frame, t, n, t_in, t_out):
    p, k = life(t, t_in, t_out, 0.26, 0.15)
    if p > 0 and k > 0:
        place(frame, number_img(n), W / 2, 1120, k=min(1, p * 3) * k, scale=max(0.3, back_out(p)) * (1 + 0.15 * (1 - k)),
              rot=-12 * (1 - ease_out(p)))


def draw_chip(frame, t, n, text, t_in, t_out):
    p, k = life(t, t_in, t_out, 0.35, 0.25)
    if p > 0 and k > 0:
        e = ease_out(p)
        place(frame, chip_img(n, text), W / 2, 300, k=e * k, dy=-int(26 * (1 - e)))


# ------------------------------------------------------------------ icons
def icon(kind, d=120):
    s = 4; D = d * s
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    if kind == "check":
        g.ellipse((0, 0, D - 1, D - 1), fill=GREEN + (255,))
        g.line([(D * .27, D * .52), (D * .44, D * .69), (D * .74, D * .34)], fill=WHITE + (255,), width=int(D * .1), joint="curve")
    elif kind == "pyramid":
        g.ellipse((0, 0, D - 1, D - 1), fill=(250, 226, 170, 255))
        g.polygon([(D * .5, D * .2), (D * .82, D * .74), (D * .18, D * .74)], fill=(214, 160, 70, 255))
        g.polygon([(D * .5, D * .2), (D * .82, D * .74), (D * .56, D * .74)], fill=(176, 122, 44, 255))
        g.line([(D * .12, D * .76), (D * .88, D * .76)], fill=(150, 104, 40, 255), width=int(D * .03))
    elif kind == "hourglass":
        g.ellipse((0, 0, D - 1, D - 1), fill=CREAM + (255,))
        g.rectangle((D * .28, D * .2, D * .72, D * .26), fill=CHAR + (255,)); g.rectangle((D * .28, D * .74, D * .72, D * .8), fill=CHAR + (255,))
        g.polygon([(D * .33, D * .26), (D * .67, D * .26), (D * .52, D * .5), (D * .67, D * .74), (D * .33, D * .74), (D * .48, D * .5)], outline=CHAR + (255,), fill=(255, 255, 255, 255), width=int(D * .025))
        g.polygon([(D * .4, D * .34), (D * .6, D * .34), (D * .5, D * .48)], fill=ORANGE + (255,))
        g.polygon([(D * .37, D * .72), (D * .63, D * .72), (D * .5, D * .6)], fill=ORANGE + (255,))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def card_img(ic, text):
    lines = [ink(l, dm(54, 800), CHAR) for l in text.split("\n")]
    txt = stack(lines, 8)
    i = icon(ic, 130)
    w = i.width + txt.width + 110; h = max(i.height, txt.height) + 70
    im = rrect(w, h, 34, (255, 255, 255, 245))
    im.alpha_composite(i, (35, (h - i.height) // 2)); im.alpha_composite(txt, (i.width + 70, (h - txt.height) // 2))
    return shadow(im, 20, (0, 10), 110)


def draw_card(frame, t, ic, text, t_in, t_out):
    rise(frame, card_img(ic, text), t, t_in, t_out, W / 2, 1080)


# ------------------------------------------------------------------ octopus: three hearts + blue blood
@lru_cache(None)
def heart(d=150, color=RED):
    s = 4; D = d * s
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    pts = []
    for i in range(200):
        a = 2 * math.pi * i / 200
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((D / 2 + x * D / 36, D / 2 - y * D / 36 + D * .04))
    g.polygon(pts, fill=color + (255,))
    g.ellipse((D * .26, D * .26, D * .38, D * .38), fill=(255, 255, 255, 120))
    return shadow(im.resize((d, d), Image.LANCZOS), 12, (0, 6), 110)


@lru_cache(None)
def hearts_label():
    return G.shadowed(ink("3 HEARTS", dm(96, 900), WHITE), blur=14, off=(0, 6), alpha=200, spread=2)


def draw_hearts(frame, t, t_in, t_out):
    k_out = 1 - ease_io((t - t_out) / 0.25)
    if t < t_in or k_out <= 0:
        return
    for i in range(3):
        p = clamp((t - t_in - 0.18 * i) / 0.28)
        if p > 0:
            beat = 1 + 0.06 * max(0.0, math.sin((t - t_in) * 2 * math.pi * 1.6 - i))
            place(frame, heart(), W / 2 + (i - 1) * 175, 860, k=min(1, p * 3) * k_out, scale=max(0.3, back_out(p)) * beat)
    p = clamp((t - t_in - 0.5) / 0.3)
    if p > 0:
        place(frame, hearts_label(), W / 2, 1010, k=ease_out(p) * k_out, dy=int(16 * (1 - ease_out(p))))


@lru_cache(None)
def blue_img():
    d = 92; s = 4; D = d * s
    drop = Image.new("RGBA", (D, D), (0, 0, 0, 0)); g = ImageDraw.Draw(drop)
    g.ellipse((D * .2, D * .38, D * .8, D * .98), fill=BLUE + (255,)); g.polygon([(D * .5, 0), (D * .78, D * .55), (D * .22, D * .55)], fill=BLUE + (255,))
    drop = drop.resize((d, d), Image.LANCZOS)
    t = ink("BLUE BLOOD", dm(80, 900), (120, 180, 255))
    im = Image.new("RGBA", (drop.width + t.width + 24, max(d, t.height)), (0, 0, 0, 0))
    im.alpha_composite(drop, (0, (im.height - d) // 2)); im.alpha_composite(t, (d + 24, (im.height - t.height) // 2))
    return G.shadowed(im, blur=14, off=(0, 6), alpha=210, spread=2)


# ------------------------------------------------------------------ sunlight: Sun -> Earth light-travel diagram
def draw_sun_earth(frame, t, t_in, t_out, t_arrive):
    p, k = life(t, t_in, t_out, 0.35, 0.25)
    if p <= 0 or k <= 0:
        return
    cw, ch = 940, 420
    card = rrect(cw, ch, 36, (18, 22, 32, 205))
    g = ImageDraw.Draw(card)
    sx, ex, cy = 150, cw - 150, 175
    # Sun with glow
    glow = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((60, 60, 240, 240), fill=(255, 190, 60, 200))
    glow = glow.filter(ImageFilter.GaussianBlur(26)); card.alpha_composite(glow, (sx - 150, cy - 150))
    g.ellipse((sx - 70, cy - 70, sx + 70, cy + 70), fill=(255, 196, 60, 255))
    g.ellipse((sx - 52, cy - 52, sx + 52, cy + 52), fill=(255, 226, 120, 255))
    # Earth
    g.ellipse((ex - 46, cy - 46, ex + 46, cy + 46), fill=(52, 120, 220, 255))
    g.pieslice((ex - 46, cy - 46, ex + 46, cy + 46), 200, 290, fill=(70, 170, 90, 255))
    g.ellipse((ex - 20, cy - 4, ex + 16, cy + 30), fill=(70, 170, 90, 255))
    # dashed path, drawn as the light travels
    prog = clamp((t - t_in - 0.2) / max(0.4, t_arrive - t_in - 0.2))
    x0, x1 = sx + 82, ex - 58
    xe = x0 + (x1 - x0) * prog
    x = x0
    while x < xe:
        g.line([(x, cy), (min(x + 18, xe), cy)], fill=(255, 220, 120, 255), width=6); x += 30
    if prog < 1:
        g.ellipse((xe - 14, cy - 14, xe + 14, cy + 14), fill=(255, 245, 200, 255))
    # labels and timer
    for txt, xx in (("SUN", sx), ("EARTH", ex)):
        lb = ink(txt, dm(30, 800), (220, 225, 235), tracking=3); card.alpha_composite(lb, (int(xx - lb.width / 2), cy + 92))
    secs = 480 * ease_io(prog)
    tm = ink(f"{int(secs // 60)}:{int(secs % 60):02d}", dm(70, 900), WHITE)
    card.alpha_composite(tm, (int(cw / 2 - tm.width / 2), cy - 140))
    if prog >= 1:
        lab = ink("≈ 8 MINUTES", dm(48, 900), YELLOW); card.alpha_composite(lab, (int(cw / 2 - lab.width / 2), ch - 92))
    e = ease_out(p)
    place(frame, shadow(card, 22, (0, 10), 120), W / 2, 900, k=e * k, scale=0.95 + 0.05 * e, dy=int(20 * (1 - e)))


# ------------------------------------------------------------------ Venus: day vs year bars
def draw_bars(frame, t, t_day, t_year, t_out):
    p, k = life(t, t_day - 0.25, t_out, 0.35, 0.25)
    if p <= 0 or k <= 0:
        return
    cw, ch = 960, 470
    card = rrect(cw, ch, 36, (18, 22, 32, 210))
    hd = ink("ON VENUS", dm(38, 800), (210, 215, 225), tracking=6); card.alpha_composite(hd, ((cw - hd.width) // 2, 34))
    full = 760
    rows = [("1 DAY", 243, ORANGE, t_day), ("1 YEAR", 225, (235, 235, 240), t_year)]
    for i, (lab, val, col, ts) in enumerate(rows):
        y = 140 + i * 150
        q = ease_out(clamp((t - ts) / 0.9))
        lb = ink(lab, dm(40, 900), WHITE); card.alpha_composite(lb, (90, y))
        bar_w = int(full * (val / 243) * q)
        if bar_w > 4:
            card.alpha_composite(rrect(bar_w, 44, 22, col + (255,)), (90, y + 56))
        if q > 0:
            num = ink(f"{int(round(val * q))} Earth days", dm(36, 800), col)
            card.alpha_composite(num, (cw - 90 - num.width, y + 4))
    e = ease_out(p)
    place(frame, shadow(card, 22, (0, 10), 120), W / 2, 940, k=e * k, scale=0.95 + 0.05 * e, dy=int(20 * (1 - e)))


# ------------------------------------------------------------------ bananas: radiation, potassium tile
@lru_cache(None)
def radiation_icon(d=230):
    s = 4; D = d * s
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    g.ellipse((0, 0, D - 1, D - 1), fill=YELLOW + (255,), outline=CHAR + (255,), width=int(D * .03))
    c = D / 2; r1, r2 = D * .12, D * .42
    for a0 in (-90 + 30, 30 + 30, 150 + 30):
        g.pieslice((c - r2, c - r2, c + r2, c + r2), a0 - 30, a0 + 30, fill=CHAR + (255,))
    g.ellipse((c - r1 - D * .03, c - r1 - D * .03, c + r1 + D * .03, c + r1 + D * .03), fill=YELLOW + (255,))
    g.ellipse((c - D * .08, c - D * .08, c + D * .08, c + D * .08), fill=CHAR + (255,))
    return shadow(im.resize((d, d), Image.LANCZOS), 18, (0, 8), 120)


@lru_cache(None)
def radio_label():
    return G.shadowed(stack([ink("SLIGHTLY", dm(60, 800), WHITE), ink("RADIOACTIVE", dm(96, 900), YELLOW)], 6), blur=14, off=(0, 6), alpha=210, spread=2)


def draw_radiation(frame, t, t_in, t_out):
    p, k = life(t, t_in, t_out, 0.3, 0.25)
    if p <= 0 or k <= 0:
        return
    pulse = 1 + 0.05 * math.sin((t - t_in) * 2 * math.pi * 1.2)
    place(frame, radiation_icon(), W / 2, 800, k=min(1, p * 3) * k, scale=max(0.3, back_out(p)) * pulse, rot=-(t - t_in) * 25)
    q = clamp((t - t_in - 0.25) / 0.3)
    if q > 0:
        place(frame, radio_label(), W / 2, 1040, k=ease_out(q) * k, dy=int(16 * (1 - ease_out(q))))


@lru_cache(None)
def element_img():
    w, h = 300, 340
    tile = rrect(w, h, 26, (255, 255, 255, 250), outline=ORANGE + (255,), width=8)
    a = ink("19", dm(44, 700), CHAR); tile.alpha_composite(a, (30, 26))
    b = ink("K", dm(170, 900), ORANGE); tile.alpha_composite(b, ((w - b.width) // 2, 92))
    c = ink("Potassium", dm(40, 700), CHAR); tile.alpha_composite(c, ((w - c.width) // 2, h - 70))
    lab = G.shadowed(ink("Natural potassium", dm(56, 800), WHITE), blur=14, off=(0, 6), alpha=210, spread=2)
    return stack([shadow(tile, 20, (0, 10), 120), lab], 4)


# ------------------------------------------------------------------ call to action: number pills 1-5
@lru_cache(None)
def num_pill(n):
    d = 150; s = 3
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((0, 0, d * s - 1, d * s - 1), fill=(255, 255, 255, 250), outline=ORANGE + (255,), width=8 * s)
    im = im.resize((d, d), Image.LANCZOS)
    t = ink(str(n), dm(84, 900), ORANGE); im.alpha_composite(t, ((d - t.width) // 2, (d - t.height) // 2 - 3))
    return shadow(im, 14, (0, 6), 110)


@lru_cache(None)
def cta_label():
    return G.shadowed(ink("Comment your number", dm(66, 900), WHITE), blur=14, off=(0, 6), alpha=210, spread=2)


def draw_numbers(frame, t, t_in, t_out):
    k = 1 - ease_io((t - t_out) / 0.3)
    if t < t_in or k <= 0:
        return
    q = clamp((t - t_in) / 0.3)
    place(frame, cta_label(), W / 2, 1010, k=ease_out(q) * k, dy=int(16 * (1 - ease_out(q))))
    for i in range(5):
        p = clamp((t - t_in - 0.15 - 0.09 * i) / 0.25)
        if p > 0:
            place(frame, num_pill(i + 1), W / 2 + (i - 2) * 172, 1170, k=min(1, p * 3) * k, scale=max(0.3, back_out(p)))


# ------------------------------------------------------------------ "follow for more science"
@lru_cache(None)
def follow_img():
    a = ink("FOLLOW", dm(64, 900), WHITE, tracking=4)
    b = ink("for more science", dm(56, 800), CHAR)
    box_a = rrect(a.width + 90, a.height + 50, (a.height + 50) // 2, ORANGE + (255,)); box_a.alpha_composite(a, (45, 25))
    box_b = rrect(b.width + 80, b.height + 44, 26, (255, 255, 255, 245)); box_b.alpha_composite(b, (40, 22))
    return shadow(stack([box_a, box_b], 14), 18, (0, 8), 110)


def draw_follow(frame, t, t_in, t_out):
    p, k = life(t, t_in, t_out, 0.32, 0.25)
    if p > 0 and k > 0:
        place(frame, follow_img(), W / 2, 1120, k=min(1, p * 3) * k, scale=max(0.3, back_out(p)))
