# Calm design for the learning-disabilities reel. One card per idea, held for the whole idea: cards fade in, stay put
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

# =============================================================== 4. EARLY SIGNS: one checklist, items added as spoken
t_signs0 = E["These signs"][0]


def sign_row(a, b):
    """Two signs side by side, each with an orange dot."""
    cells = []
    for s in (a, b):
        lab = line(s, 36)
        c = blank(430, lab.height)
        c.alpha_composite(circle(18, ORANGE), (0, (lab.height - 18) // 2 + 3))
        c.alpha_composite(lab, (34, 0))
        cells.append(c)
    return cells


SIGNS = [([("Mixing up ", "r"), ("b", "pf", 1.12), (" and ", "r"), ("d", "pf", 1.12)], tw("These signs", "mixing")),
         ([("Slow handwriting", "r")], tw("These signs", "slow")),
         ([("Inconsistent spelling", "r")], E["spelling"][0]),
         ([("Messy handwriting", "r")], tw("spelling", "messy")),
         ([("Trouble with numbers", "r")], tw("spelling", "trouble")),
         ([("Avoiding homework", "r")], tw("spelling", "avoiding"))]


class SignsGrid:
    """Rows of two: each sign fades in at its own time inside one fixed row image."""

    def __init__(self, a, b):
        self.cells = sign_row(a[0], b[0])
        self.ta, self.tb = a[1] - 0.1, b[1] - 0.1
        self.width, self.height = 880, self.cells[0].height

    def at(self, t):
        im = blank(self.width, self.height)
        for c, tt, x in ((self.cells[0], self.ta, 0), (self.cells[1], self.tb, 452)):
            p = ease_out(clamp((t - tt) / 0.45))
            if p > 0:
                im.alpha_composite(G.with_alpha(c, p), (x, 0))
        return im


class SignsCard(Card):
    def __init__(self, t0, t1):
        self.hdr = [line([("Signs can appear as early as", "m")], 38), line([("6–8 ", "pf", 1.4), ("years", "b")], 64)]
        self.rows = [SignsGrid(SIGNS[i], SIGNS[i + 1]) for i in (0, 2, 4)]
        items = [(self.hdr[0], t0), (self.hdr[1], tw("These signs", "6") - 0.1)]
        items += [(blank(880, r.height), r.ta) for r in self.rows]
        super().__init__(items, t0, t1, w=980, gap=22, py=40)

    def render(self, frame, t):
        # rows are time-dependent images: swap them in before drawing (cache key includes per-cell progress)
        for k, r in enumerate(self.rows):
            self.items[2 + k] = (r.at(t), r.ta)
        ps = tuple(round(ease_out(clamp((t - tt) / 0.45)), 2) for r in self.rows for tt in (r.ta, r.tb))
        if len(self.cache) > 60:
            self.cache = {}
        self._render(frame, t, ps)

    def _render(self, frame, t, ps):
        a = ease_out(clamp((t - self.t0) / FADE_IN)) * clamp((self.t1 - t) / FADE_OUT)
        if a <= 0.01:
            return
        hs = [self._h_until(k) for k in range(1, len(self.items) + 1)]
        h = hs[0]
        for k in range(1, len(self.items)):
            g = ease_io(clamp((t - (self.items[k][1] - 0.30)) / 0.45))
            h += (hs[k] - hs[k - 1]) * g
        h = int(round(h))
        ph = tuple(round(ease_out(clamp((t - ti) / 0.45)), 2) for _, ti in self.items[:2])
        key = (h, ph) + ps
        if key not in self.cache:
            im = rounded(self.w, h, 44, G.a(WHITE, 250))
            y = self.py
            for k, (it, ti) in enumerate(self.items):
                p = 1.0 if k >= 2 else (1.0 if k == 0 else ph[1])
                if p > 0 and y + it.height <= h + 2:
                    x = (self.w - it.width) // 2
                    im.alpha_composite(G.with_alpha(it, p), (x, y + int((1 - p) * 10)))
                y += it.height + self.gap
            self.cache[key] = shadow(im, (0, 10), 22, 44)
        im = self.cache[key]
        dy = int((1 - ease_out(clamp((t - self.t0) / FADE_IN))) * 14)
        frame.alpha_composite(G.with_alpha(im, a), (540 - im.width // 2, TOP_EDGE - SH_PAD + 10 + dy))


sfx(t_signs0 - 0.1, "tick", -14)
SignsCard(t_signs0 - 0.1, E["And these"][0] - 0.3)
for s in ("Mixing up b and d", "Slow handwriting", "Inconsistent spelling", "Messy handwriting", "Trouble with numbers", "Avoiding homework"):
    log(s)

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
