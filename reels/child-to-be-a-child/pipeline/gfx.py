# The Cub brand graphics for this reel, in the Sitaara reference style:
#   * big opening title (Playfair Display, white, soft shadow) over the chest, gone once the question is asked
#   * short white phrase captions with a soft shadow, lower middle of the frame
#   * name card: logo mark pops in, a charcoal band wipes out to the right, name + designation slide in
#   * closing logo reveal recreated from the supplied reference clip, with the new tagline
import os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FD = os.environ.get("FONT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"))
BRAND = os.environ.get("BRAND_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand"))
W, H = 1080, 1920
ORANGE = (240, 133, 62)      # The Cub Orange #F0853E
CHAR = (43, 43, 43)          # Charcoal #2B2B2B
CREAM = (253, 246, 238)      # Cream #FDF6EE
WHITE = (255, 255, 255)

TITLE_LINES = [("Do we allow a child", "PlayfairDisplay-700.ttf"), ("to be a child?", "PlayfairDisplay-700.ttf")]
TITLE_SIZE, TITLE_CY = 104, 1090
CAP_FONT, CAP_SIZE, CAP_CY = "GlacialIndifference-Bold.ttf", 66, 1352
NAME, ROLE = "Saisha Sawhney", "Developmental Psychologist, The Cub"
CARD_X, CARD_CY = 64, 1500
TAGLINE = "Everyone Deserves To Be Seen"


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(p):
    return 1 - (1 - clamp(p)) ** 3


def ease_io(p):
    p = clamp(p)
    return 3 * p * p - 2 * p * p * p


def back_out(p, s=1.6):
    p = clamp(p) - 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2


@lru_cache(None)
def font(name, size):
    return ImageFont.truetype(f"{FD}/{name}", size)


def with_alpha(im, k):
    if k >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * max(0.0, k))))
    return im


def shadowed(im, blur=10, off=(0, 4), alpha=150, spread=0):
    """Soft dark drop shadow under white type, as in the reference reel."""
    pad = blur * 3 + 8
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    m = Image.new("L", out.size, 0)
    m.paste(im.getchannel("A"), (pad + off[0], pad + off[1]))
    if spread:
        m = m.filter(ImageFilter.MaxFilter(spread * 2 + 1))
    m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", out.size, (20, 16, 12, 0)); sh.putalpha(m)
    out.alpha_composite(sh)
    out.alpha_composite(im, (pad, pad))
    return out


def text_img(s, fname, size, fill=WHITE, tracking=0):
    f = font(fname, size)
    asc, desc = f.getmetrics()
    w = int(f.getlength(s) + tracking * max(0, len(s) - 1)) + 8
    im = Image.new("RGBA", (w, asc + desc + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if tracking:
        x = 4
        for ch in s:
            d.text((x, 4), ch, font=f, fill=fill + (255,)); x += f.getlength(ch) + tracking
    else:
        d.text((4, 4), s, font=f, fill=fill + (255,))
    return im


# ------------------------------------------------------------------ title
@lru_cache(None)
def title_img():
    lines = [text_img(s, fn, TITLE_SIZE) for s, fn in TITLE_LINES]
    lines = [l.crop(l.getchannel("A").getbbox()) for l in lines]
    gap = int(TITLE_SIZE * 0.20)
    w = max(l.width for l in lines); h = sum(l.height for l in lines) + gap * (len(lines) - 1)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
    for l in lines:
        im.alpha_composite(l, ((w - l.width) // 2, y)); y += l.height + gap
    return shadowed(im, blur=16, off=(0, 5), alpha=175, spread=2)


def draw_title(frame, t, t_out):
    """Visible from the first frame; fades and lifts slightly once the opening question has been asked."""
    k = 1 - ease_io((t - t_out) / 0.30)
    if k <= 0:
        return
    im = with_alpha(title_img(), k)
    y = TITLE_CY - im.height // 2 - int(8 * (1 - k))
    frame.alpha_composite(im, ((W - im.width) // 2, y))


# ------------------------------------------------------------------ captions
@lru_cache(None)
def caption_img(s):
    im = text_img(s, CAP_FONT, CAP_SIZE)
    bb = im.getchannel("A").getbbox()
    f = font(CAP_FONT, CAP_SIZE); asc, _ = f.getmetrics()
    im = im.crop((bb[0], 4 + asc - int(CAP_SIZE * 0.78), bb[2], 4 + asc + int(CAP_SIZE * 0.26)))
    return shadowed(im, blur=9, off=(0, 3), alpha=185, spread=1)


def draw_caption(frame, s):
    im = caption_img(s)
    if im.width > W - 60:
        im = im.resize((W - 60, int(im.height * (W - 60) / im.width)), Image.LANCZOS)
    frame.alpha_composite(im, ((W - im.width) // 2, CAP_CY - im.height // 2))


# ------------------------------------------------------------------ name card
@lru_cache(None)
def _logo(name):
    return Image.open(f"{BRAND}/{name}").convert("RGBA")


@lru_cache(None)
def card_parts():
    d = 112
    s = 4
    badge = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    ImageDraw.Draw(badge).ellipse((0, 0, d * s - 1, d * s - 1), fill=WHITE + (255,), outline=ORANGE + (255,), width=5 * s)
    badge = badge.resize((d, d), Image.LANCZOS)
    mark = _logo("logo_mark.png")
    mw = int(d * 0.80); mark = mark.resize((mw, int(mark.height * mw / mark.width)), Image.LANCZOS)
    badge.alpha_composite(mark, ((d - mark.width) // 2, (d - mark.height) // 2 + 2))
    glow = Image.new("RGBA", (d + 80, d + 80), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((40 - 6, 40 - 6, 40 + d + 6, 40 + d + 6), fill=ORANGE + (150,))
    glow = glow.filter(ImageFilter.GaussianBlur(16))
    name = text_img(NAME, "Lexend-600.ttf", 44)
    name = name.crop(name.getchannel("A").getbbox())
    role = text_img(ROLE, "Lexend-400.ttf", 28, fill=(255, 196, 150))
    role = role.crop(role.getchannel("A").getbbox())
    bw = max(name.width, role.width) + 150 + 120
    bh = 128
    g = np.zeros((bh, bw), np.float32)
    x = np.linspace(0, 1, bw)
    a = np.clip(1.0 - np.clip((x - 0.62) / 0.38, 0, 1) ** 1.3, 0, 1) * 0.90
    g[:] = a[None, :]
    band = Image.new("RGBA", (bw, bh), CHAR + (0,))
    band.putalpha(Image.fromarray((g * 255).astype(np.uint8)))
    return dict(badge=badge, glow=glow, name=name, role=role, band=band, d=d)


def draw_namecard(frame, t, t_in, t_out):
    """Reference timing: icon pops (0-0.35 s), band wipes out (0.15-0.6 s), text slides in (0.3-0.75 s); the
    whole card slides back and fades over 0.35 s at the end."""
    lt = t - t_in
    if lt < 0 or t > t_out + 0.4:
        return
    P = card_parts(); d = P["d"]
    k_out = 1 - ease_io((t - t_out) / 0.35)
    cy = CARD_CY
    bx = CARD_X + d // 2
    # band
    pw = ease_out((lt - 0.15) / 0.45)
    if pw > 0:
        band = P["band"]
        vis = band.crop((0, 0, max(1, int(band.width * pw)), band.height))
        frame.alpha_composite(with_alpha(vis, k_out), (bx, cy - band.height // 2))
    # text
    pt = ease_out((lt - 0.30) / 0.45)
    if pt > 0:
        tx = CARD_X + d + 26 - int(30 * (1 - pt)) - int(24 * (1 - k_out))
        frame.alpha_composite(with_alpha(P["name"], pt * k_out), (tx, cy - 40))
        frame.alpha_composite(with_alpha(P["role"], pt * k_out), (tx, cy + 18))
    # badge pops with a little overshoot
    pb = back_out(lt / 0.38) if lt < 0.38 else 1.0
    if pb > 0.02:
        sc = max(0.05, pb)
        g = P["glow"]; gs = int(g.width * sc)
        frame.alpha_composite(with_alpha(g.resize((gs, gs), Image.LANCZOS), 0.8 * k_out * clamp(lt / 0.25)), (bx - gs // 2, cy - gs // 2))
        b = P["badge"]; bs = max(2, int(d * sc))
        frame.alpha_composite(with_alpha(b.resize((bs, bs), Image.LANCZOS), k_out * clamp(lt / 0.12)), (bx - bs // 2, cy - bs // 2))


# ------------------------------------------------------------------ closing logo reveal
# Recreated from the reference clip (1080x1920, 3.4 s), given more time (3.7 s): the last frame dissolves to white while the full logo fades in
# and settles (94% -> 100%); the tagline is revealed by a soft left-to-right ink wipe while rising; a short orange
# rule draws out under it; hold. Layout measured from the reference: logo 420 px wide centred at y 820, tagline
# Playfair Display Italic 60 px centred at y 1130, rule 110 x 8 px at y 1212.
OUT_BG = WHITE
LOGO_W, LOGO_CY = 420, 820
TAG_SIZE, TAG_CY = 62, 1130
RULE_Y, RULE_W, RULE_H = 1212, 110, 8
R_DISSOLVE = (0.00, 0.75)     # revision 2: a slower, calmer hand-off than the reference (which dissolves in 0.45 s)
R_LOGO = (0.30, 1.10)
R_TAG = (1.15, 2.25)
R_RULE = (2.00, 2.50)


@lru_cache(None)
def outro_parts():
    lg = _logo("logo_full.png")
    lg = lg.resize((LOGO_W, int(LOGO_W * lg.height / lg.width)), Image.LANCZOS)
    f = font("PlayfairDisplay-400i.ttf", TAG_SIZE)
    asc, desc = f.getmetrics()
    tw = int(f.getlength(TAGLINE)) + 24
    tag = Image.new("RGBA", (tw, asc + desc + 20), (0, 0, 0, 0))
    ImageDraw.Draw(tag).text((12, 10 + asc), TAGLINE, font=f, fill=CHAR + (255,), anchor="ls", stroke_width=1, stroke_fill=CHAR + (255,))  # ~medium weight, as in the reference
    bb = tag.getchannel("A").getbbox()
    tag = tag.crop((bb[0] - 2, bb[1] - 2, bb[2] + 2, bb[3] + 2))
    return lg, tag


def _wipe(im, p, feather=160):
    if p >= 1:
        return im
    m = np.zeros((im.height, im.width), np.float32)
    x = (im.width + feather) * p
    xs = np.arange(im.width)
    m[:] = np.clip((x - xs) / feather, 0, 1)[None, :]
    out = im.copy()
    out.putalpha(Image.fromarray((np.asarray(im.getchannel("A")).astype(np.float32) * m).astype(np.uint8)))
    return out


def reveal(base, t):
    """t = seconds since the reveal started (may be slightly negative while the dissolve begins)."""
    k = ease_io((t - R_DISSOLVE[0]) / (R_DISSOLVE[1] - R_DISSOLVE[0]))
    bg = Image.new("RGB", (W, H), OUT_BG)
    img = Image.blend(base.convert("RGB"), bg, k) if k < 1 else bg
    img = img.convert("RGBA")
    lg, tag = outro_parts()
    pl = ease_out((t - R_LOGO[0]) / (R_LOGO[1] - R_LOGO[0]))
    if pl > 0:
        sc = 0.94 + 0.06 * pl
        l2 = lg.resize((int(lg.width * sc), int(lg.height * sc)), Image.LANCZOS)
        img.alpha_composite(with_alpha(l2, pl), ((W - l2.width) // 2, LOGO_CY - l2.height // 2))
    pt = (t - R_TAG[0]) / (R_TAG[1] - R_TAG[0])
    if pt > 0:
        rise = int(12 * (1 - ease_out(pt)))
        img.alpha_composite(_wipe(tag, ease_io(pt)), ((W - tag.width) // 2, TAG_CY - tag.height // 2 + rise))
    pr = ease_out((t - R_RULE[0]) / (R_RULE[1] - R_RULE[0]))
    if pr > 0:
        rw = max(2, int(RULE_W * pr))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle(((W - rw) // 2, RULE_Y - RULE_H // 2, (W + rw) // 2, RULE_Y + RULE_H // 2), RULE_H // 2, fill=ORANGE + (255,))
    return img
