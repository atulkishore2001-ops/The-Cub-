# Calm design for the learning-disabilities reel (revision 3: draft-1 sign cards restored). One card per idea, held for the whole idea: cards fade in, stay put
# and fade out (no sliding, no swapping); list items are added in place as they are spoken. Every card hangs from the
# same top line in the wall area above her head; captions run continuously on her torso. Ends on the logo + tagline.
import math, re, os
import numpy as np
from PIL import Image, ImageDraw
import gfx2 as G
from gfx2 import CHAR, CREAM, ORANGE, WHITE, text, row, col, pill, rounded, circle, shadow
from anim2 import Sprite, Captions, clamp, ease_io, ease_out
import timeline3 as T

FPS = T.FPS
TL = T.build()
WORDS, PIECES = TL["words"], TL["pieces"]
T_EXP_END, T_END = TL["t_exp_end"], TL["t_end"]
TOTAL_FRAMES = TL["total_frames"]
TOTAL = TOTAL_FRAMES / FPS
FM = T.frame_map(PIECES)
BLK = T.blocks(FM)
BRAND = os.environ.get("BRAND", "/tmp/claude-0/-home-user-The-Cub-/6a3c4bc0-104a-5ca4-adb7-aceaf8503d24/scratchpad/brand")

SPRITES, SFX, TEXTS = [], [], []
MUTED = G.a(CHAR, 190)
TOP_EDGE = 300               # every card hangs from this line
CAP_Y = 1480                 # captions: on the torso, under the chin, above Instagram's bottom UI
SH_PAD = 22 * 2 + 10         # shadow() padding around a card (blur 22, offset 10)
FADE_IN, FADE_OUT = 0.5, 0.45

# a short word followed by a long "gap" inside a sentence is a recogniser timing slip: the next word really starts there
for i in range(1, len(WORDS)):
    p, w = WORDS[i - 1], WORDS[i]
    if p["seg"] == w["seg"] and w["s"] - p["e"] > 0.3:
        if w["e"] - w["s"] < 0.15:
            w["s"] = p["e"] + 0.03
        elif p["e"] - p["s"] < 0.15:
            p["e"] = w["s"] - 0.03


def _n(s):
    return re.sub(r"[^a-z0-9'-]", "", s.lower())


def tw(seg, word, n=0, end=False):
    c = [w for w in WORDS if w["seg"].lower().startswith(seg.lower()) and _n(w["w"]) == _n(word)]
    return c[n]["e" if end else "s"]


def seg_span(seg):
    c = [w for w in WORDS if w["seg"].lower().startswith(seg.lower())]
    return c[0]["s"], c[-1]["e"]


def sfx(t, name, gain=0.0, pan=0.0, **kw):
    SFX.append(dict(t=t, name=name, gain=gain, pan=pan, **kw))


def log(s):
    TEXTS.append(s)
    return s


STY = {"n": ("dm", 700, CHAR), "m": ("dm", 500, MUTED), "b": ("dm", 800, CHAR), "o": ("dm", 800, ORANGE),
       "pf": ("pfi", 600, ORANGE), "pfc": ("pfi", 500, CHAR), "cream": ("dm", 700, CREAM), "r": ("dm", 600, CHAR)}


def line(parts, size=56):
    """Runs of mixed fonts on one shared baseline. parts: [(text, style[, size_mult])]."""
    runs = []
    for p in parts:
        s, st = p[0], p[1]
        k = p[2] if len(p) > 2 else 1.0
        fam, wt, col_ = STY[st]
        runs.append((s, G.font(fam, wt, int(size * k)), col_))
    log("".join(r[0] for r in runs))
    asc = max(f.getmetrics()[0] for _, f, _ in runs)
    desc = max(f.getmetrics()[1] for _, f, _ in runs)
    w = int(sum(f.getlength(s) for s, f, _ in runs)) + 24
    im = Image.new("RGBA", (w, asc + desc + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 12
    for s, f, c in runs:
        d.text((x, 10 + asc), s, font=f, fill=c, anchor="ls")
        x += f.getlength(s)
    bb = im.getchannel("A").getbbox()
    top = 10 + asc - int(size * 0.80)
    bot = 10 + asc + int(size * 0.30)
    return im.crop((bb[0] - 2, max(0, min(top, bb[1] - 2)), bb[2] + 2, max(bot, bb[3] + 2)))


def blank(w, h):
    return Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))


def wipe(im, p, feather=24):
    """Left-to-right reveal with a soft edge."""
    if p >= 1:
        return im
    m = Image.new("L", im.size, 0)
    x = int((im.width + feather) * p)
    grad = Image.linear_gradient("L").rotate(90).resize((feather, im.height))
    m.paste(255, (0, 0, max(0, x - feather), im.height))
    m.paste(grad, (x - feather, 0))
    out = im.copy()
    out.putalpha(Image.fromarray((np.asarray(im.getchannel("A")).astype(np.uint16) * np.asarray(m) // 255).astype(np.uint8)))
    return out


class Card:
    """A white card hanging from TOP_EDGE. items: [(image, t_in, x_align)] stacked vertically. Items fade in place when
    spoken; the card's height eases to fit the items shown so far (it grows, it never jumps). Whole card fades in/out."""

    def __init__(self, items, t0, t1, w=None, px=56, py=40, gap=18, align="center", min_w=0):
        self.items, self.t0, self.t1 = items, t0, t1
        self.px, self.py, self.gap, self.align = px, py, gap, align
        self.w = w or max(min_w, max(i[0].width for i in items) + 2 * px)
        self.cache = {}
        SPRITES.append(self)
        self.layer = 0

    def active(self, t):
        return self.t0 <= t < self.t1

    def _h_until(self, k):
        its = self.items[:k]
        return sum(i[0].height for i in its) + self.gap * max(0, len(its) - 1) + 2 * self.py

    def render(self, frame, t):
        a = ease_out(clamp((t - self.t0) / FADE_IN)) * clamp((self.t1 - t) / FADE_OUT)
        if a <= 0.01:
            return
        ps = [ease_out(clamp((t - ti) / 0.45)) for _, ti, *_ in self.items]
        ps[0] = max(ps[0], 1.0 if t >= self.t0 else 0)                     # first item comes with the card
        n_vis = sum(1 for _, ti, *_ in self.items if t >= ti - 0.25) or 1
        # height eases between "items so far" sizes
        h_full = self._h_until(len(self.items))
        hs = [self._h_until(k) for k in range(1, len(self.items) + 1)]
        h = hs[0]
        for k in range(1, len(self.items)):
            g = ease_io(clamp((t - (self.items[k][1] - 0.30)) / 0.45))
            h += (hs[k] - hs[k - 1]) * g
        h = int(round(h))
        key = (h, tuple(round(p, 2) for p in ps))
        if key not in self.cache:
            im = rounded(self.w, h, 44, G.a(WHITE, 250))
            y = self.py
            for (it, ti, *al), p in zip(self.items, ps):
                if p > 0 and y + it.height <= h + 2:
                    al = al[0] if al else self.align
                    x = (self.w - it.width) // 2 if al == "center" else self.px
                    im.alpha_composite(G.with_alpha(it, p), (x, y + int((1 - p) * 10)))
                y += it.height + self.gap
            self.cache[key] = shadow(im, (0, 10), 22, 44)
        im = self.cache[key]
        dy = int((1 - ease_out(clamp((t - self.t0) / FADE_IN))) * 14)
        frame.alpha_composite(G.with_alpha(im, a), (540 - im.width // 2, TOP_EDGE - SH_PAD + 10 + dy))


def card(items, t0, t1, **kw):
    sfx(t0, "tick", -14)
    return Card(items, t0, t1, **kw)


E = {k: seg_span(k) for k in ("Is your", "As a parent", "He can read", "He knows", "Hi, this", "These concerns", "These signs",
                                "spelling", "And these", "Many of", "Don't label", "A formal", "With early", "Your child is",
                                "If you notice")}

# =============================================================== 1. OPENING: one card, the concern text changes in place
O_STATES = [
    (E["Is your"][0], [line([("Struggling in ", "n"), ("academics", "pf", 1.12), ("?", "n")], 58)]),
    (tw("As a parent", "my") - 0.05, [line([("“My child is ", "n"), ("smart", "pf", 1.12), (",", "n")], 56),
                                     line([("but his marks are ", "n"), ("low", "pf", 1.12), (".”", "n")], 56)]),
    (E["He can read"][0] - 0.05, [line([("Can ", "n"), ("read", "pf", 1.12), (",", "n")], 56),
                                  line([("but doesn’t ", "n"), ("understand", "pf", 1.12)], 56)]),
    (E["He knows"][0] - 0.05, [line([("Knows the answer at ", "n"), ("home", "pf", 1.12), (",", "n")], 56),
                               line([("but forgets in ", "n"), ("exam", "pf", 1.12)], 56)]),
]
O_T0, O_T1 = E["Is your"][0] + 0.05, E["Hi, this"][0] - 0.25
O_W = max(max(l.width for l in ls) for _, ls in O_STATES) + 2 * 56
O_H = max(sum(l.height for l in ls) + 6 * (len(ls) - 1) for _, ls in O_STATES) + 2 * 40


def _state_img(ls):
    im = blank(O_W, O_H)
    h = sum(l.height for l in ls) + 6 * (len(ls) - 1)
    y = (O_H - h) // 2
    for l in ls:
        im.alpha_composite(l, ((O_W - l.width) // 2, y))
        y += l.height + 6
    return im


O_IMGS = [_state_img(ls) for _, ls in O_STATES]


class Opening:
    layer = 0

    def __init__(self):
        self.cache = {}
        SPRITES.append(self)
        sfx(O_T0, "tick", -14)

    def active(self, t):
        return O_T0 <= t < O_T1

    def render(self, frame, t):
        a = ease_out(clamp((t - O_T0) / FADE_IN)) * clamp((O_T1 - t) / FADE_OUT)
        k = max(i for i, (ts, _) in enumerate(O_STATES) if t >= ts - 0.2 or i == 0)
        p = clamp((t - (O_STATES[k][0] - 0.3)) / 0.5) if k else 1.0       # old text fades out, then the new one fades in
        key = (k, round(p, 2))
        if key not in self.cache:
            im = rounded(O_W, O_H, 44, G.a(WHITE, 250))
            if p < 0.5:
                im.alpha_composite(G.with_alpha(O_IMGS[k - 1], ease_io(1 - 2 * p)))
            else:
                im.alpha_composite(G.with_alpha(O_IMGS[k], ease_io(2 * p - 1)))
            self.cache[key] = shadow(im, (0, 10), 22, 44)
        im = self.cache[key]
        dy = int((1 - ease_out(clamp((t - O_T0) / FADE_IN))) * 14)
        frame.alpha_composite(G.with_alpha(im, a), (540 - im.width // 2, TOP_EDGE - SH_PAD + 10 + dy))


Opening()

# =============================================================== 2. NAME CARD (top, captions keep running)
t_hi0, t_hi1 = E["Hi, this"]
mark = Image.open(f"{BRAND}/logo_mark.png").convert("RGBA")
mark = mark.resize((150, int(150 * mark.height / mark.width)), Image.LANCZOS)
nm = col([line([("Anjali Rawat", "b")], 60),
          line([("Clinical Psychologist", "m"), ("  ·  ", "m"), ("The Cub", "o")], 36)], gap=8, align="left")
nc = blank(mark.width + 34 + nm.width, max(mark.height, nm.height))
nc.alpha_composite(mark, (0, (nc.height - mark.height) // 2))
nc.alpha_composite(rounded(4, 110, 2, G.a(ORANGE, 255)), (mark.width + 15, (nc.height - 110) // 2))
nc.alpha_composite(nm, (mark.width + 34, (nc.height - nm.height) // 2))
card([(nc, t_hi0 - 0.1)], t_hi0 - 0.1, E["These concerns"][0] - 0.3, py=34)

# =============================================================== 3. WHAT IT MAY BE
t_noth = tw("These concerns", "nothing")
intel = pill(line([("Nothing to do with ", "cream"), ("intelligence", "pf", 1.12)], 46), G.a(CHAR, 250), 40, 18)
card([(line([("These concerns may point to", "m")], 40), E["These concerns"][0] - 0.1),
      (line([("specific learning ", "b"), ("disability", "pf", 1.18)], 58), E["These concerns"][0] - 0.1),
      (intel, t_noth - 0.1)],
     E["These concerns"][0] - 0.1, E["These signs"][0] - 0.3, gap=20, py=42)

# =============================================================== 4. EARLY SIGNS (draft-1 sign cards, kept on request)
t_signs0 = E["These signs"][0]
t_six = tw("These signs", "6")
t_like = tw("These signs", "like")
T_SIGNS_END = tw("spelling", "homework", end=True) + 0.75


def add(*a, **k):
    s = Sprite(*a, **k)
    SPRITES.append(s)
    return s


card([(line([("Signs can appear as early as", "m")], 40), t_signs0 - 0.1),
      (line([("6\u20138 ", "pf", 1.5), ("years", "b")], 76), t_six - 0.1)],
     t_signs0 - 0.1, t_like - 0.05, gap=10, py=40)
chip_s = shadow(pill(line([("Early signs", "cream"), ("  \u00b7  ", "cream"), ("6\u20138 years", "pf", 1.1)], 36), G.a(CHAR, 240), 30, 14),
                (0, 6), 14, 44)
add(chip_s, 540, 330, t_like + 0.10, T_SIGNS_END, ain="fade", aout="fade", din=0.45, dout=FADE_OUT)

CW, CH = 900, 300
ILL = 252


def sign_card(label_lines, ill):
    """White card: animated illustration tile on the left, label on the right."""
    lab = col([line(l, 50) for l in label_lines], gap=4, align="left")
    cache = {}

    def f(t):
        im = rounded(CW, CH, 44, G.a(WHITE, 252))
        tile = rounded(ILL, ILL, 34, G.a(CREAM, 255))
        tile.alpha_composite(ill(t), (0, 0))
        im.alpha_composite(tile, (24, (CH - ILL) // 2))
        im.alpha_composite(lab, (24 + ILL + 40, (CH - lab.height) // 2))
        return shadow(im, (0, 10), 22, 46)
    return f


def glyph(ch, size, fill, fam="dm", wt=800):
    f = G.font(fam, wt, size)
    im = Image.new("RGBA", (ILL, ILL), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((ILL / 2, ILL / 2), ch, font=f, fill=fill, anchor="mm")
    return im


def ill_bd(t_flip):
    b, d = glyph("b", 190, CHAR), glyph("d", 190, ORANGE)

    def f(t):
        p = clamp((t - t_flip) / 0.42)
        s = math.cos(math.pi * ease_io(p))                 # 1 -> -1: the letter turns round on its vertical axis
        src = b if s > 0 else d
        w = max(2, int(ILL * abs(s)))
        g = src.resize((w, ILL), Image.BICUBIC)
        im = Image.new("RGBA", (ILL, ILL), (0, 0, 0, 0))
        im.alpha_composite(g, ((ILL - w) // 2, 0))
        return im
    return f


def handwriting(word, size, wt=600, color=CHAR):
    f = G.font("cav", wt, size)
    w = int(f.getlength(word)) + 20
    im = Image.new("RGBA", (w, int(size * 1.3)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, int(size * 0.95)), word, font=f, fill=color, anchor="ls")
    return im


def wipe(im, p, feather=24):
    """Left-to-right reveal with a soft edge (like ink going down)."""
    if p >= 1:
        return im
    m = Image.new("L", im.size, 0)
    x = int((im.width + feather) * p)
    grad = Image.linear_gradient("L").rotate(90).resize((feather, im.height))
    m.paste(255, (0, 0, max(0, x - feather), im.height))
    m.paste(grad, (x - feather, 0))
    out = im.copy()
    out.putalpha(Image.fromarray((__import__("numpy").asarray(im.getchannel("A")).astype("uint16") *
                                  __import__("numpy").asarray(m) // 255).astype("uint8")))
    return out


def ill_slow(t0, dur):
    wd = handwriting("cat", 120, 600)
    clock_r = 34

    def f(t):
        im = Image.new("RGBA", (ILL, ILL), (0, 0, 0, 0))
        p = clamp((t - t0) / dur)
        im.alpha_composite(wipe(wd, p), ((ILL - wd.width) // 2, 70))
        d = ImageDraw.Draw(im)
        cx, cy = ILL - 56, 54
        d.ellipse((cx - clock_r, cy - clock_r, cx + clock_r, cy + clock_r), outline=ORANGE, width=6)
        a = -math.pi / 2 + 2 * math.pi * p
        d.line((cx, cy, cx + 0.72 * clock_r * math.cos(a), cy + 0.72 * clock_r * math.sin(a)), fill=CHAR, width=5)
        d.line((cx, cy, cx, cy - 0.5 * clock_r), fill=CHAR, width=5)
        return im
    return f


def ill_spell(times):
    vs = [handwriting(w, 66, 600, c) for w, c in (("becos", CHAR), ("becuz", CHAR), ("beacuse", CHAR))]

    def f(t):
        im = Image.new("RGBA", (ILL, ILL), (0, 0, 0, 0))
        for k, (v, tt) in enumerate(zip(vs, times)):
            p = ease_out(clamp((t - tt) / 0.35))
            if p > 0:
                im.alpha_composite(G.with_alpha(v, p), ((ILL - v.width) // 2, 14 + k * 74 + int((1 - p) * 10)))
        return im
    return f


def ill_messy(times):
    import random
    rnd = random.Random(7)
    tries = []
    for k in range(3):
        v = handwriting("apple", 70, 500, CHAR).rotate(rnd.uniform(-7, 7), Image.BICUBIC, expand=True)
        tries.append(v)

    def f(t):
        im = Image.new("RGBA", (ILL, ILL), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for k, (v, tt) in enumerate(zip(tries, times)):
            p = clamp((t - tt) / 0.45)
            if p <= 0:
                continue
            y = 12 + k * 76
            x = (ILL - v.width) // 2 + (-14, 10, -4)[k]
            im.alpha_composite(wipe(v, p), (x, y))
            if k < 2 and k + 1 < len(times):                # earlier attempts get scribbled out as the next one starts
                q = clamp((t - times[k + 1] + 0.05) / 0.25)
                if q > 0:
                    yy = y + v.height // 2 + 4
                    d.line((x + 6, yy, x + 6 + (v.width - 12) * q, yy - 6 * q), fill=ORANGE, width=6)
        return im
    return f




def two_signs(times):
    rows = [line([("Trouble with ", "n"), ("numbers", "pf", 1.15)], 50), line([("Avoiding ", "n"), ("homework", "pf", 1.15)], 50)]

    def f(t):
        im = rounded(CW, CH, 44, G.a(WHITE, 252))
        y = (CH - (rows[0].height + rows[1].height + 30)) // 2
        for r, tt in zip(rows, times):
            p = ease_out(clamp((t - tt) / 0.45))
            if p > 0:
                c = blank(r.width + 46, r.height)
                c.alpha_composite(circle(22, ORANGE), (0, (r.height - 22) // 2 + 4))
                c.alpha_composite(r, (46, 0))
                im.alpha_composite(G.with_alpha(c, p), ((CW - 560) // 2, y + int((1 - p) * 10)))
            y += r.height + 30
        return shadow(im, (0, 10), 22, 46)
    return f


t_mix = tw("These signs", "mixing")
t_slow = tw("These signs", "slow")
t_spell = E["spelling"][0]
t_messy = tw("spelling", "messy")
t_trouble = tw("spelling", "trouble")
t_avoid = tw("spelling", "avoiding")
SIGNS = [
    (t_mix, sign_card([[("Mixing up ", "n"), ("b", "pf", 1.15), (" and ", "n"), ("d", "pf", 1.15)]], ill_bd(tw("These signs", "d") - 0.12))),
    (t_slow, sign_card([[("Slow", "n")], [("handwriting", "n")]], ill_slow(t_slow + 0.1, t_spell - t_slow + 0.2))),
    (t_spell, sign_card([[("Spelling the same", "n")], [("word ", "n"), ("differently", "pf", 1.1)], [("each time", "n")]],
                        ill_spell([t_spell + 0.15, tw("spelling", "differently") - 0.05, tw("spelling", "each") - 0.02]))),
    (t_messy, sign_card([[("Messy handwriting", "n")], [("despite ", "n"), ("several", "pf", 1.1)], [("attempts", "pf", 1.1)]],
                        ill_messy([t_messy + 0.05, tw("spelling", "despite") + 0.05, tw("spelling", "several") + 0.05]))),
    (t_trouble, two_signs([t_trouble - 0.1, t_avoid - 0.1])),
]
for k, (t0, img) in enumerate(SIGNS):
    last = k + 1 == len(SIGNS)
    t1 = T_SIGNS_END if last else SIGNS[k + 1][0] - 0.06 + 0.18
    add(img, 540, 590, t0 - 0.12, t1, ain="fade" if k == 0 else "right", aout="fade" if last else "left",
        dist=56, din=0.34 if k else 0.45, dout=FADE_OUT if last else 0.22)
    sfx(t0 - 0.12, "tick" if k == 0 else "swipe", -14 if k == 0 else -17, pitch=1.0 + 0.03 * k)

# =============================================================== 5. NOT ABOUT BEING BRIGHT
t_not, t_but = tw("And these", "not"), tw("And these", "but")
card([(line([("Not because they aren’t bright,", "m")], 42), t_not - 0.15),
      (line([("but because their brain", "b")], 56), t_but - 0.1),
      (line([("works ", "b"), ("differently", "pf", 1.45)], 56), t_but - 0.1)],
     t_not - 0.15, E["Many of"][0] - 0.3, gap=12)

# =============================================================== 6. SMALL, SPECIFIC STEPS
t_learn, t_broken, t_small = tw("Many of", "learning"), tw("Many of", "broken"), tw("Many of", "small")
T_STEPS = t_broken + 0.1


def steps_img(t):
    w, h = 600, 210
    im = blank(w, h)
    d = ImageDraw.Draw(im)
    bw, gap = 120, 26
    x0 = (w - (4 * bw + 3 * gap)) // 2
    for i in range(4):
        q = ease_out(clamp((t - (T_STEPS + i * 0.38)) / 0.5))       # the steps rise once, in order, then stay
        if q <= 0:
            continue
        hh = (60 + 46 * i) * q
        x = x0 + i * (bw + gap)
        d.rounded_rectangle((x, h - hh, x + bw, h), 16, fill=ORANGE if i == 3 else G.a(CHAR, 235))
    return im


class StepsCard(Card):
    def render(self, frame, t):
        self.items[1] = (steps_img(t), self.items[1][1])
        self.cache = {}
        Card.render(self, frame, t)


lab_bot = pill(line([("small and ", "cream"), ("specific steps", "pf", 1.14)], 46), G.a(CHAR, 250), 40, 18)
sfx(t_learn - 0.4, "tick", -14)
StepsCard([(line([("When learning is broken down into", "b")], 46), t_learn - 0.4),
           (steps_img(1e9), t_learn - 0.4),
           (lab_bot, t_small - 0.1)],
          t_learn - 0.4, E["Don't label"][0] - 0.3, w=900, gap=24, py=40)
log("When learning is broken down into small and specific steps")

# =============================================================== 7. WHAT PARENTS CAN DO (one list, grows as spoken)


def takeaway(num, parts, size=50):
    badge = circle(60, ORANGE)
    nn = text(str(num), "dm", 800, 32, WHITE)
    badge.alpha_composite(nn, ((60 - nn.width) // 2, (60 - nn.height) // 2 + 1))
    return row([badge, line(parts, size)], gap=24)


t_dont, t_get, t_support = E["Don't label"][0], tw("Don't label", "get"), tw("A formal", "support")
card([(takeaway(1, [("Don’t ", "n"), ("label", "pf", 1.14), (" your child", "n")]), t_dont - 0.1, "left"),
      (takeaway(2, [("Get an ", "n"), ("assessment", "pf", 1.14)]), t_get - 0.1, "left"),
      (takeaway(3, [("Support can start ", "n"), ("much earlier", "pf", 1.14)]), t_support - 0.1, "left")],
     t_dont - 0.1, E["Your child is"][0] - 0.3, gap=22, py=42, align="left")

# =============================================================== 8. NOT LAZY
t_lazy, t_he = E["Your child is"][0], tw("Your child is", "he")
card([(line([("Your child is not ", "b"), ("lazy", "pf", 1.16), (".", "b")], 58), t_lazy - 0.1),
      (line([("He just learns ", "b"), ("differently", "pf", 1.3), (".", "b")], 58), t_he - 0.1)],
     t_lazy - 0.1, E["If you notice"][0] - 0.3, gap=14)

# =============================================================== 9. CALL TO ACTION
t_if, t_cub = E["If you notice"][0], tw("If you notice", "the", 1)
wm = Image.open(f"{BRAND}/logo_wordmark.png").convert("RGBA")
wm = wm.resize((300, int(300 * wm.height / wm.width)), Image.LANCZOS)
log("THE CUB (wordmark)")
T_CREAM0 = T_EXP_END - 0.10                 # cross-fade to the brand frame starts right after the last word
T_CREAM1 = T_CREAM0 + 1.0
card([(line([("If you notice the signs,", "m")], 40), t_if - 0.1),
      (line([("please reach out to us at", "n")], 52), t_if - 0.1),
      (wm, t_cub - 0.15),
      (line([("We are here to help you", "pfc")], 50), t_cub - 0.15)],
     t_if - 0.1, T_CREAM0 + 0.5, gap=18, py=40)

# =============================================================== CLOSING: logo + tagline on cream (unchanged)


def cream_alpha(t):
    return ease_io(clamp((t - T_CREAM0) / (T_CREAM1 - T_CREAM0)))


logo = Image.open(f"{BRAND}/logo_full.png").convert("RGBA")
logo = logo.resize((420, int(420 * logo.height / logo.width)), Image.LANCZOS)
T_LOGO = T_CREAM0 + 0.65
T_TAG = T_LOGO + 0.85
TAGLINE = "Every Child Deserves To Be Seen"
tag = line([(TAGLINE, "pfc")], 60)


def logo_img(t):
    p = clamp((t - T_LOGO) / 1.1)
    s = 0.94 + 0.06 * ease_out(p)
    im = logo.resize((int(logo.width * s), int(logo.height * s)), Image.LANCZOS) if s < 0.999 else logo
    return G.with_alpha(im, ease_io(clamp(p * 1.3)))


def tag_img(t):
    p = clamp((t - T_TAG) / 1.15)
    return G.with_alpha(wipe(tag, ease_io(p), feather=140), clamp(p * 2.5))


SPRITES.append(Sprite(logo_img, 540, 820, T_LOGO, T_END + 1, ain="none", aout="none", din=0, dout=0, layer=5))
SPRITES.append(Sprite(tag_img, 540, 1130, T_TAG, T_END + 1, ain="none", aout="none", din=0, dout=0, layer=5,
                      path=lambda t, x, y, s: (x, y + 12 * (1 - ease_out(clamp((t - T_TAG) / 1.0))), s)))
SPRITES.append(Sprite(lambda t: G.underline(max(2, int(110 * ease_io(clamp((t - T_TAG - 0.7) / 0.6)))), 6), 540, 1212,
                      T_TAG + 0.7, T_END + 1, ain="none", aout="none", din=0, dout=0, layer=5))
sfx(T_LOGO + 0.05, "chime", -15)

# =============================================================== captions: continuous, one style, whole reel
CAPTIONS = Captions(WORDS, y=CAP_Y, hide=[(T_CREAM0 + 0.2, T_END + 1)], size=50, max_chars=30, max_words=6)
SPRITES.sort(key=lambda s: s.layer)

if __name__ == "__main__":
    print("total %.2fs (%d frames); cream from %.2f, logo %.2f, tagline %.2f" % (TOTAL, TOTAL_FRAMES, T_CREAM0, T_LOGO, T_TAG))
    print(len(SPRITES), "sprites,", len(SFX), "sfx at", [round(s["t"], 2) for s in SFX])
    for s in SPRITES:
        print("  %-12s %6.2f - %6.2f" % (type(s).__name__, s.t0 if hasattr(s, "t0") else O_T0, s.t1 if hasattr(s, "t1") else O_T1))
    print("TEXTS:")
    for s in sorted(set(TEXTS)):
        print("  ", s)
    for k, c in enumerate(CAPTIONS.chunks):
        print("%6.2f-%6.2f %s" % (CAPTIONS.times[k][0], CAPTIONS.times[k][1], " ".join(w["w"] for w in c)))
