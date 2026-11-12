# OSIT ad graphics, in the poster's design language (green #47B383, navy #15315C, red #D52828, yellow #FED84E,
# DM Sans). Every element only fades / rises / pops in and out; nothing slides around the frame.
# All key elements sit between y 270 and y 1250 (Meta Reels ad safe zone: top 14%, bottom 35%).
import os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import gfx as G

HERE = os.path.dirname(os.path.abspath(__file__))
FD = G.FD
ASSETS = os.environ.get("ASSET_DIR", os.path.join(HERE, "..", "assets"))
BR = os.path.join(HERE, "brand")
W, H = 1080, 1920
GREEN, NAVY, RED, YELLOW = (71, 179, 131), (21, 49, 92), (213, 40, 40), (254, 216, 78)
WHITE, INK = (255, 255, 255), (15, 18, 22)


@lru_cache(None)
def dm(size, wght=700):
    f = ImageFont.truetype(f"{FD}/DMSans-VF.ttf", size)
    f.set_variation_by_axes([min(40, max(9, size / 2.2)), wght])
    return f


def ink(s, f, fill, tracking=0):
    asc, desc = f.getmetrics()
    w = int(f.getlength(s) + tracking * max(0, len(s) - 1)) + 16
    im = Image.new("RGBA", (w, asc + desc + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 8
    if tracking:
        for ch in s:
            d.text((x, 8), ch, font=f, fill=fill + (255,)); x += f.getlength(ch) + tracking
    else:
        d.text((8, 8), s, font=f, fill=fill + (255,))
    return im.crop(im.getchannel("A").getbbox())


def rrect(w, h, r, fill, outline=None, width=0):
    s = 3
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * s - 1, h * s - 1), r * s, fill=fill, outline=outline, width=width * s)
    return im.resize((w, h), Image.LANCZOS)


def soft_shadow(im, blur=22, off=(0, 12), alpha=70):
    pad = blur * 3
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    m = Image.new("L", out.size, 0); m.paste(im.getchannel("A"), (pad + off[0], pad + off[1]))
    m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", out.size, (10, 20, 40, 0)); sh.putalpha(m)
    out.alpha_composite(sh); out.alpha_composite(im, (pad, pad))
    return out


def round_mask(im, r):
    m = rrect(im.width, im.height, r, (255, 255, 255, 255)).getchannel("A")
    out = im.convert("RGBA").copy()
    out.putalpha(Image.fromarray(np.minimum(np.asarray(out.getchannel("A")), np.asarray(m))))
    return out


def place(frame, im, cx, cy, k=1.0, scale=1.0, dy=0):
    """Composite `im` centred at (cx, cy) with opacity k, scale and vertical offset."""
    if k <= 0.01:
        return
    if abs(scale - 1) > 0.004:
        im = im.resize((max(2, int(im.width * scale)), max(2, int(im.height * scale))), Image.LANCZOS)
    frame.alpha_composite(G.with_alpha(im, k), (int(cx - im.width / 2), int(cy - im.height / 2 + dy)))


def env(t, t_in, t_out, a=0.30, b=0.25):
    """0..1 entrance progress and exit fade."""
    return G.clamp((t - t_in) / a), 1 - G.clamp((t - t_out) / b)


# ------------------------------------------------------------------ profession pills (hook)
PILL_ROWS = [["SLP", "OT", "Pediatrician"], ["Neurologist", "Physiotherapist"]]
PILL_Y = [955, 1065]


@lru_cache(None)
def pill_img(label):
    t = ink(label, dm(46, 700), WHITE)
    p = rrect(t.width + 64, 86, 43, GREEN + (255,))
    p.alpha_composite(t, ((p.width - t.width) // 2, (p.height - t.height) // 2 + 1))
    return soft_shadow(p, blur=14, off=(0, 6), alpha=80)


@lru_cache(None)
def pill_layout():
    pos = {}
    for row, y in zip(PILL_ROWS, PILL_Y):
        ims = [pill_img(l) for l in row]
        gap = -28                                          # shadows overlap; visible gap is ~16 px
        total = sum(i.width for i in ims) + gap * (len(ims) - 1)
        x = (W - total) / 2
        for l, i in zip(row, ims):
            pos[l] = (x + i.width / 2, y); x += i.width + gap
    return pos


def draw_pill(frame, t, label, t_in, t_out):
    p, k = env(t, t_in, t_out, 0.28, 0.25)
    if p <= 0 or k <= 0:
        return
    cx, cy = pill_layout()[label]
    place(frame, pill_img(label), cx, cy, k=min(1, p * 2.5) * k, scale=max(0.3, G.back_out(p)) * (0.96 + 0.04 * k))


# ------------------------------------------------------------------ OSIT title card (the poster's own title design)
@lru_cache(None)
def title_card(width=1000):
    t = Image.open(f"{BR}/osit_title_no_bunting.png").convert("RGB")      # poster title, bunting removed
    t = t.resize((width, int(t.height * width / t.width)), Image.LANCZOS)
    return soft_shadow(round_mask(t, 30), blur=24, off=(0, 12), alpha=85)


def draw_title(frame, t, t_in, t_out, cy=1040):
    p, k = env(t, t_in, t_out, 0.40, 0.28)
    if p > 0 and k > 0:
        e = G.ease_out(p)
        place(frame, title_card(), W / 2, cy, k=e * k, scale=0.96 + 0.04 * e, dy=int(22 * (1 - e)))


# ------------------------------------------------------------------ date pill
@lru_cache(None)
def date_img():
    d = 92
    icon = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    ImageDraw.Draw(icon).ellipse((0, 0, d - 1, d - 1), fill=NAVY + (255,), outline=WHITE + (255,), width=4)
    ic = ImageDraw.Draw(icon)                                      # simple calendar glyph, as on the poster
    ic.rounded_rectangle((26, 30, 66, 66), 6, outline=WHITE + (255,), width=4)
    ic.line((26, 41, 66, 41), fill=WHITE + (255,), width=4)
    ic.line((36, 24, 36, 34), fill=WHITE + (255,), width=4); ic.line((56, 24, 56, 34), fill=WHITE + (255,), width=4)
    l1 = ink("5th – 6th December 2026", dm(50, 700), WHITE)
    l2 = ink("9:00 AM – 5:00 PM  ·  The Cub, New Delhi", dm(28, 500), WHITE)
    w = d + 30 + max(l1.width, l2.width) + 56
    box = rrect(w, 150, 34, GREEN + (255,))
    box.alpha_composite(icon, (22, (150 - d) // 2))
    box.alpha_composite(l1, (d + 48, 28)); box.alpha_composite(l2, (d + 50, 28 + l1.height + 16))
    return soft_shadow(box, blur=18, off=(0, 8), alpha=80)


def draw_date(frame, t, t_in, t_out, cy=1045):
    p, k = env(t, t_in, t_out, 0.32, 0.25)
    if p > 0 and k > 0:
        e = G.ease_out(p)
        place(frame, date_img(), W / 2, cy, k=e * k, scale=0.95 + 0.05 * G.back_out(p), dy=int(18 * (1 - e)))


# ------------------------------------------------------------------ collaboration logos card
@lru_cache(None)
def logos_img(card=True, scale=1.0):
    cub = Image.open(f"{BR}/logo_full.png").convert("RGBA")
    ch = int(150 * scale); cub = cub.resize((int(cub.width * ch / cub.height), ch), Image.LANCZOS)
    sg = Image.open(f"{BR}/speechgears_logo.png").convert("RGBA")
    sw = int(400 * scale); sg = sg.resize((sw, int(sg.height * sw / sg.width)), Image.LANCZOS)
    gap = int(44 * scale)
    row_w = cub.width + gap * 2 + 3 + sg.width
    row_h = max(cub.height, sg.height)
    row = Image.new("RGBA", (row_w, row_h), (0, 0, 0, 0))
    row.alpha_composite(cub, (0, (row_h - cub.height) // 2))
    ImageDraw.Draw(row).rectangle((cub.width + gap, int(row_h * 0.18), cub.width + gap + 2, int(row_h * 0.82)), fill=(200, 205, 214, 255))
    row.alpha_composite(sg, (cub.width + gap * 2 + 3, (row_h - sg.height) // 2))
    if not card:
        return row
    lab = ink("IN COLLABORATION WITH", dm(24, 600), (110, 118, 130), tracking=4)
    cw, chh = row_w + 120, row_h + lab.height + 96
    box = rrect(cw, chh, 32, WHITE + (255,))
    box.alpha_composite(lab, ((cw - lab.width) // 2, 34))
    box.alpha_composite(row, ((cw - row_w) // 2, 34 + lab.height + 26))
    return soft_shadow(box, blur=24, off=(0, 12), alpha=85)


def draw_logos(frame, t, t_in, t_out, cy=1010):
    p, k = env(t, t_in, t_out, 0.38, 0.28)
    if p > 0 and k > 0:
        e = G.ease_out(p)
        place(frame, logos_img(), W / 2, cy, k=e * k, scale=0.96 + 0.04 * e, dy=int(20 * (1 - e)))


# ------------------------------------------------------------------ photo cards over the softly blurred speaker
@lru_cache(None)
def photo_card(name, max_w=600, max_h=760):
    im = Image.open(f"{ASSETS}/{name}").convert("RGB")
    sc = min(max_w / im.width, max_h / im.height)
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))    # the photos are small: recover some crispness
    b = 14
    card = rrect(im.width + 2 * b, im.height + 2 * b, 26, WHITE + (255,))
    card.alpha_composite(round_mask(im, 16), (b, b))
    return card


@lru_cache(None)
def count_badge(v):
    """Navy badge with the running count ("0+" ... "1,000+"); always sized for the final number so it never jumps."""
    full = ink("1,000+", dm(92, 800), YELLOW)
    n = ink(f"{v:,}+", dm(92, 800), YELLOW)
    l = ink("professionals trained", dm(34, 600), WHITE)
    w = max(full.width, l.width) + 80
    box = rrect(w, full.height + l.height + 64, 28, NAVY + (255,))
    box.alpha_composite(n, ((w - n.width) // 2, 26 + (full.height - n.height)))
    box.alpha_composite(l, ((w - l.width) // 2, 26 + full.height + 14))
    return soft_shadow(box, blur=16, off=(0, 8), alpha=90)


def blur_amount(t, graphics):
    k = 0.0
    for g in graphics:
        if g["kind"] == "photo":
            p, o = env(t, g["t_in"] - 0.05, g["t_out"], 0.30, 0.30)
            k = max(k, min(G.ease_io(p), o))
    return k


def draw_photo(frame, t, g, idx):
    p, k = env(t, g["t_in"], g["t_out"], 0.32, 0.26)
    if p <= 0 or k <= 0:
        return
    e = G.ease_out(p)
    card = photo_card(g["img"])
    drift = 1.0 + 0.035 * G.clamp((t - g["t_in"]) / max(0.5, g["t_out"] - g["t_in"]))   # slow push-in
    rot = (-2.0 if idx % 2 == 0 else 2.0) * e
    c = card.rotate(rot, resample=Image.BICUBIC, expand=True)
    c = soft_shadow(c, blur=26, off=(0, 14), alpha=110)
    cy = 700 if g.get("stat") else 730
    place(frame, c, W / 2, cy, k=e * k, scale=(0.93 + 0.07 * e) * drift, dy=int(26 * (1 - e)))
    if g.get("stat"):
        ps = G.clamp((t - g["t_in"] - 0.25) / 0.35)
        if ps > 0:
            v = int(round(1000 * G.ease_out(G.clamp((t - g["t_in"] - 0.25) / 0.8)) / 10) * 10)
            place(frame, count_badge(v), W / 2, cy + c.height * 0.36, k=G.ease_out(ps) * k, scale=0.9 + 0.1 * G.back_out(ps))


# ------------------------------------------------------------------ urgency callouts
@lru_cache(None)
def fast_img():
    t = ink("SEATS ARE FILLING UP FAST", dm(44, 800), YELLOW, tracking=2)
    box = rrect(t.width + 90, 104, 52, NAVY + (255,))
    box.alpha_composite(t, ((box.width - t.width) // 2, (104 - t.height) // 2))
    return soft_shadow(box, blur=16, off=(0, 8), alpha=90)


@lru_cache(None)
def deadline_img():
    l1 = ink("LAST DATE TO REGISTER", dm(36, 700), WHITE, tracking=3)
    l2 = ink("21st November 2026", dm(64, 800), YELLOW)
    w = max(l1.width, l2.width) + 110
    box = rrect(w, l1.height + l2.height + 70, 40, RED + (255,))
    box.alpha_composite(l1, ((w - l1.width) // 2, 26)); box.alpha_composite(l2, ((w - l2.width) // 2, 26 + l1.height + 18))
    return soft_shadow(box, blur=18, off=(0, 8), alpha=90)


def draw_callout(frame, t, img, t_in, t_out, cy=1050):
    p, k = env(t, t_in, t_out, 0.30, 0.25)
    if p > 0 and k > 0:
        place(frame, img, W / 2, cy, k=min(1, p * 2) * k, scale=max(0.3, G.back_out(p)))


# ------------------------------------------------------------------ closing frame
@lru_cache(None)
def closing_bg():
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([248, 250, 253]), np.array([236, 241, 248])
    a = np.broadcast_to(top * (1 - y) + bot * y, (H, W, 3)).astype(np.uint8)
    im = Image.fromarray(a).convert("RGBA")
    # a faint green arc in the corner, echoing the poster's band
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ov).ellipse((-420, 1420, 640, 2480), fill=GREEN + (26,))
    ImageDraw.Draw(ov).ellipse((640, -520, 1500, 300), fill=GREEN + (22,))
    im.alpha_composite(ov.filter(ImageFilter.GaussianBlur(4)))
    return im


@lru_cache(None)
def cta_img():
    l1 = ink("REGISTER NOW!", dm(60, 800), YELLOW)
    l2 = ink("SPOTS ARE LIMITED  ·  LAST DATE 21 NOV", dm(28, 700), WHITE, tracking=2)
    w = 820
    box = rrect(w, l1.height + l2.height + 62, 32, NAVY + (255,))
    box.alpha_composite(l1, ((w - l1.width) // 2, 24)); box.alpha_composite(l2, ((w - l2.width) // 2, 24 + l1.height + 14))
    return soft_shadow(box, blur=18, off=(0, 8), alpha=80)


@lru_cache(None)
def date_line():
    return ink("5th – 6th December 2026  ·  9 AM – 5 PM  ·  New Delhi", dm(30, 600), NAVY)


QR_W = 500


@lru_cache(None)
def qr_img():
    q = Image.open(f"{BR}/osit_register_qr.png").convert("RGBA")
    # drop the poster background around the red frame: flood-fill the light area from the edges
    import cv2
    a = np.asarray(q.convert("RGB")).copy()
    mask = np.zeros((a.shape[0] + 2, a.shape[1] + 2), np.uint8)
    for x, y in [(0, 0), (a.shape[1] - 1, 0), (0, a.shape[0] - 1), (a.shape[1] - 1, a.shape[0] - 1), (a.shape[1] // 2, a.shape[0] - 1)]:
        cv2.floodFill(a, mask, (x, y), (0, 0, 0), (14, 14, 14), (14, 14, 14), cv2.FLOODFILL_MASK_ONLY | (255 << 8) | 8)
    alpha = 255 - mask[1:-1, 1:-1]
    alpha[14:462, 14:469] = 255                     # the frame's white inside stays solid (the fill can leak past the label)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8)
    q.putalpha(Image.fromarray(alpha))
    q = q.resize((QR_W, int(q.height * QR_W / q.width)), Image.LANCZOS)
    return soft_shadow(q, blur=20, off=(0, 10), alpha=70)


LAYOUT = dict(logos=336, title=508, date=630, cta=750, qr=1124)      # centres; ~40 px between blocks, all inside y 270-1400


def closing(t):
    """t = seconds since the closing frame started."""
    img = closing_bg().copy()
    items = [("logos", logos_img(card=False, scale=0.72), 0.00), ("title", title_card(900), 0.12), ("date", date_line(), 0.24),
             ("cta", cta_img(), 0.34), ("qr", qr_img(), 0.46)]
    for key, im, delay in items:
        p = G.clamp((t - delay) / 0.45)
        if p <= 0:
            continue
        e = G.ease_out(p)
        sc = (0.94 + 0.06 * G.back_out(p)) if key == "qr" else (0.97 + 0.03 * e)
        place(img, im, W / 2, LAYOUT[key], k=e, scale=sc, dy=int(24 * (1 - e)))
    return img
