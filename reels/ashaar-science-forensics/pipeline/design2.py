# Scene-by-scene design: layouts, motion graphics, captions, sound cues. Everything is timed to spoken words.
import math, re, os
from PIL import Image, ImageDraw
import gfx2 as G
import icons as I
import tank as TK
from gfx2 import CHAR, CREAM, ORANGE, WHITE, text, row, col, pill, rounded, circle, shadow
from anim2 import Sprite, Captions, clamp, ease_io, ease_out, ease_in
import timeline2 as T

FPS = T.FPS
TL = T.build()
WORDS, PIECES = TL["words"], TL["pieces"]
T_EXP_END, T_END = TL["t_exp_end"], TL["t_end"]
TOTAL_FRAMES = TL["total_frames"]
TOTAL = TOTAL_FRAMES / FPS
FM = T.frame_map(PIECES)
BLK = T.blocks(FM)
BRAND = os.environ.get("BRAND", "/tmp/claude-0/-home-user-The-Cub-/6a3c4bc0-104a-5ca4-adb7-aceaf8503d24/scratchpad/brand")

SPRITES, SFX, TEXTS, PUNCH, SHAKE = [], [], [], [], []


def _n(s):
    return re.sub(r"[^a-z0-9'-]", "", s.lower())


def tw(seg, word, n=0, end=False):
    c = [w for w in WORDS if seg.lower() in w["seg"].lower() and _n(w["w"]) == _n(word)]
    return c[n]["e" if end else "s"]


def seg_span(seg):
    c = [w for w in WORDS if seg.lower() in w["seg"].lower()]
    return c[0]["s"], c[-1]["e"]


def sfx(t, name, gain=0.0, pan=0.0, **kw):
    SFX.append(dict(t=t, name=name, gain=gain, pan=pan, **kw))


def add(*a, **k):
    s = Sprite(*a, **k)
    SPRITES.append(s)
    return s


def log(s):
    TEXTS.append(s)
    return s


# ------------------------------------------------------------------ builders
def rich(parts, size=48, weight=700, gap=0, fg=CHAR):
    """parts: [(text, 'n'|'hl')]. 'hl' = orange pill with charcoal text."""
    ims = []
    for s, st in parts:
        log(s)
        t = text(s, "dm", weight, size, CHAR if st == "hl" else fg)
        ims.append(pill(t, ORANGE, int(size * 0.34), int(size * 0.16), r=int(size * 0.42)) if st == "hl" else t)
    # no gap before trailing punctuation
    g = max(gap, int(size * 0.20))
    out = ims[0]
    for (s, st), im in zip(parts[1:], ims[1:]):
        out = row([out, im], gap=-2 if s.strip() in ("?", ",", ".", "!") else g)
    return out


def chip(content, bg=CREAM, px=36, py=20, sh=True, alpha=246):
    if isinstance(content, str):
        log(content)
        content = text(content, "dm", 700, 46, CHAR)
    im = pill(content, G.a(bg, alpha), px, py)
    return shadow(im, (0, 8), 16, 62) if sh else im


def card(content, w=None, h=None, bg=WHITE, px=40, py=26, r=36, sh=True):
    w = w or content.width + 2 * px
    h = h or content.height + 2 * py
    im = rounded(w, h, r, bg)
    im.alpha_composite(content, ((w - content.width) // 2, (h - content.height) // 2))
    return shadow(im, (0, 10), 20, 56) if sh else im


def dot(d=22, c=ORANGE):
    return circle(d, c)


# ------------------------------------------------------------------ layout (panel height over time)
def seg0(k):
    return seg_span(k)[0]


E = {k: seg_span(k) for k in ("Does your", "Congratulations", "Hi, I am", "We often", "But what if we are", "Some children",
                                "But that doesn't", "Sometimes", "Instead of asking", "Fill a bucket", "Now they are", "And what if your")}
t_B0, t_B1 = E["We often"][0], E["Sometimes"][0]
t_D0, t_D1 = E["Fill a bucket"][0], E["And what if your"][0]
P_B, P_D = 700, 760
PANELS = [(t_B0 - 0.10, t_B0 + 0.38, 0, P_B), (t_B1 - 0.16, t_B1 + 0.26, P_B, 0),
          (t_D0 - 0.18, t_D0 + 0.30, 0, P_D), (t_D1 - 0.18, t_D1 + 0.24, P_D, 0),
          (T_EXP_END - 0.34, T_EXP_END + 0.34, 0, 1920)]
PROMO_T0 = T_EXP_END + 0.34          # panel fully covers the frame


def panel_h(t):
    h = 0.0
    for a, b, h0, h1 in PANELS:
        if t >= b:
            h = h1
        elif t >= a:
            h = h0 + (h1 - h0) * ease_io((t - a) / (b - a))
            break
        else:
            break
    return h


for a, b, h0, h1 in PANELS[:-1]:
    sfx(a - 0.02, "slide", -4)
sfx(PANELS[-1][0] - 0.02, "whoosh", -3, dur=0.7)

# location changes -> horizontal push transitions on the video layer
TRANSITIONS = [b["o_in"] / FPS for i, b in enumerate(BLK) if i and b["loc"] != BLK[i - 1]["loc"]]
for tc in TRANSITIONS:
    sfx(tc - 0.03, "whoosh", -7, dur=0.34)

# =============================================================== EXPLAINER
CAP_HIDE = []

# ---- E1: hook (full screen)
a1, b1 = E["Does your"]
c = chip(rich([("Hates doing ", "n"), ("homework", "hl"), ("?", "n")], 50), CREAM)
add(c, 540, 306, a1 + 0.15, E["Congratulations"][0] - 0.1, ain="rise", aout="rise", dist=34)
sfx(a1 + 0.12, "tick", -6)

# ---- E2: little scientist
a2, b2 = E["Congratulations"]
log("A little scientist at home")
add(lambda t: chip(row([I.flask(78, t - a2, 0.55), text("A little scientist at home", "dm", 700, 46, CHAR)], 16), CREAM, px=34),
    540, 306, tw("Congratulations", "little") - 0.1, E["Hi, I am"][0] - 0.1, ain="rise", aout="rise", dist=34)
sfx(tw("Congratulations", "little") - 0.1, "tick", -6, pitch=1.15)

# ---- E3: name card (lower third)
a3, b3 = E["Hi, I am"]
mark = Image.open(f"{BRAND}/logo_mark.png")
mk = mark.resize((96, int(96 * mark.height / mark.width)), Image.LANCZOS)
badge = circle(118, CREAM)
badge.alpha_composite(mk, ((118 - mk.width) // 2, (118 - mk.height) // 2 + 2))
log("Ashaar"); log("Science Educator"); log("The Cub")
name_t = text("Ashaar", "dm", 800, 66, CREAM)
role_t = row([text("Science Educator", "dm", 600, 35, ORANGE), text("·", "dm", 700, 35, CREAM), text("The Cub", "dm", 600, 35, CREAM)], 12)
info = col([name_t, role_t], gap=14, align="left")
ncard = rounded(info.width + badge.width + 3 * 36 + 8, 150, 40, G.a(CHAR, 238))
ncard.alpha_composite(badge, (22, 16)); ncard.alpha_composite(info, (22 + badge.width + 30, (150 - info.height) // 2))
ncard = shadow(ncard, (0, 10), 20, 70)
add(ncard, 14 + ncard.width / 2, 1205, tw("Hi, I am", "Ashaar,") - 0.18, b3 + 0.05, ain="left", aout="left", din=0.5, dout=0.35, dist=520, name="name-card")
sfx(tw("Hi, I am", "Ashaar,") - 0.18, "swipe", -6, pan=-0.3)
sfx(b3 - 0.25, "swipe", -10, pan=-0.3)

# ---- E4: panel — "lazy / irresponsible" vs the real struggles
a4, b4 = E["We often"]
lazy = chip(text("Lazy", "dm", 700, 54, CHAR), WHITE, 44, 24); log("Lazy")
irr = chip(text("Irresponsible", "dm", 700, 54, CHAR), WHITE, 44, 24); log("Irresponsible")
gapx = 28
tot = lazy.width + irr.width + gapx
xl = 540 - tot / 2 + lazy.width / 2 - 20
xr = 540 + tot / 2 - irr.width / 2 + 20
t_lazy, t_irr, t_struggle = tw("We often", "lazy"), tw("We often", "irresponsible"), tw("We often", "struggle")
t4_out = b4 + 0.05
def dimmed(im, t0, k=0.5):
    def f(t):
        return G.with_alpha(im, 1 - (1 - k) * clamp((t - t0) / 0.3))
    return f


log("We often call them")
add(text("We often call them", "dm", 600, 40, G.a(CHAR, 200)), 540, 292, t_B0 + 0.28, t4_out, ain="rise", aout="rise", dist=24)
sfx(t_B0 + 0.28, "tick", -9, pitch=0.8)
add(dimmed(lazy, t_struggle), xl, 372, t_lazy - 0.08, t4_out, ain="rise", aout="rise", dist=30)
add(dimmed(irr, t_struggle), xr, 372, t_irr - 0.08, t4_out, ain="rise", aout="rise", dist=30)
sfx(t_lazy - 0.08, "tick", -6, pitch=0.9); sfx(t_irr - 0.08, "tick", -6, pitch=0.8)
# strike lines wipe across both labels
for im, x, t0 in ((lazy, xl, t_struggle - 0.15), (irr, xr, t_struggle - 0.02)):
    add(G.rounded(im.width - 70, 9, 4, ORANGE), x, 372, t0, t4_out, ain="wipe", din=0.26, aout="rise", dist=30, layer=2)
sfx(t_struggle - 0.15, "scratch", -8, pan=-0.2); sfx(t_struggle - 0.02, "scratch", -8, pan=0.2)
log("Struggling to")
add(text("Struggling to", "dm", 600, 36, G.a(CHAR, 190)), 540, 482, t_struggle - 0.02, t4_out, ain="rise", aout="rise", dist=24)
struggles = [("Sit still", tw("We often", "sit")), ("Concentrate", tw("We often", "concentrate")), ("Finish homework", tw("We often", "finish"))]
pills = [pill(text(s, "dm", 700, 40, CHAR), ORANGE, 32, 18) for s, _ in struggles]
for s, _ in struggles: log(s)
g = 18
totw = sum(p.width for p in pills) + 2 * g
x = 540 - totw / 2
for p_, (s, tt) in zip(pills, struggles):
    add(shadow(p_, (0, 7), 12, 50), x + p_.width / 2, 574, tt - 0.08, t4_out, ain="rise", aout="rise", dist=26)
    sfx(tt - 0.08, "tick", -6, pitch=1.0 + 0.12 * struggles.index((s, tt)), pan=-0.2 + 0.2 * struggles.index((s, tt)))
    x += p_.width + g

# ---- E5: panel — "the wrong way?"
a5, b5 = E["But what if we are"]
log("What if we’re looking at it"); log("the "); log("wrong way?")
l1 = text("What if we’re looking at it", "dm", 600, 54, CHAR)
l2 = row([text("the", "ebi", 500, 140, CHAR), text("wrong way?", "ebi", 500, 140, CHAR)], 24)
t_wrong = tw("But what if we are", "wrong")
add(l1, 540, 372, a5 + 0.02, b5 + 0.02, ain="rise", aout="rise", dist=30)
add(l2, 540, 510, tw("But what if we are", "looking") - 0.05, b5 + 0.02, ain="rise", aout="rise", dist=40, din=0.5)
ul_w = G.text_w("wrong way?", "ebi", 500, 140)
add(G.underline(ul_w, 10), 540 + l2.width / 2 - ul_w / 2 - 6 + 0, 600, t_wrong - 0.04, b5 + 0.02, ain="wipe", din=0.45, aout="rise", dist=20)
sfx(a5 + 0.02, "tick", -7); sfx(tw("But what if we are", "looking") - 0.05, "swipe", -9); sfx(t_wrong - 0.04, "scratch", -10)

# ---- E6: panel — ADHD & traditional learning
a6, b6 = E["Some children"]
log("Children with"); log("ADHD"); log("Traditional learning"); log("harder")
t_adhd = tw("Some children", "ADHD,")
t_ctext = text("Children with", "dm", 600, 46, G.a(CHAR, 215))
adhd = pill(text("ADHD", "dm", 800, 66, CHAR), ORANGE, 40, 20)
grp = t_ctext.width + 26 + adhd.width
add(t_ctext, 540 - grp / 2 + t_ctext.width / 2, 372, a6 - 0.02, b6 + 0.02, ain="rise", aout="rise", dist=26)
add(shadow(adhd, (0, 8), 14, 56), 540 + grp / 2 - adhd.width / 2, 372, t_adhd - 0.10, b6 + 0.02, ain="scale", din=0.34, aout="rise", dist=26)
sfx(t_adhd - 0.10, "tick", -5, pitch=0.9)
trad_c = text("Traditional learning", "dm", 700, 48, CHAR)
trad = card(trad_c, px=40, py=26)
hard = pill(text("harder", "dm", 800, 48, CHAR), ORANGE, 36, 20)
t_trad, t_hard = tw("Some children", "traditional"), tw("Some children", "difficult.")
tw_body = trad_c.width + 80
grp2 = tw_body + 26 + hard.width
add(trad, 540 - grp2 / 2 + tw_body / 2, 520, t_trad - 0.08, b6 + 0.02, ain="rise", aout="rise", dist=30)
add(shadow(hard, (0, 8), 14, 56), 540 + grp2 / 2 - hard.width / 2, 520, t_hard - 0.15, b6 + 0.02, ain="scale", din=0.34, aout="rise", dist=26)
sfx(t_trad - 0.08, "tick", -6, pitch=1.0); sfx(t_hard - 0.15, "tick", -5, pitch=0.8)

# ---- E7: panel — intelligence & creativity
a7, b7 = E["But that doesn't"]
log("Not lacking in"); log("Intelligence"); log("Creativity")
add(text("Not lacking in", "dm", 600, 46, G.a(CHAR, 215)), 540, 372, a7 + 0.05, t_B1 - 0.18, ain="rise", aout="rise", dist=26)
t_int, t_cre = tw("But that doesn't", "intelligence"), tw("But that doesn't", "creativity.")
cards7 = [(lab, tt, card(row([I.check_badge(60, 1.0), text(lab, "dm", 700, 46, CHAR)], 18), px=34, py=26, sh=False)) for lab, tt in (("Intelligence", t_int), ("Creativity", t_cre))]
g7 = 28
tot7 = sum(c_[2].width for c_ in cards7) + g7
x7 = 540 - tot7 / 2
for lab, tt, cd in cards7:
    add(shadow(cd, (0, 10), 20, 56), x7 + cd.width / 2, 520, tt - 0.1, t_B1 - 0.18, ain="rise", aout="rise", dist=32)
    sfx(tt - 0.1, "check", -5, pitch=1.0 if lab == "Intelligence" else 1.2, pan=-0.2 if lab == "Intelligence" else 0.2)
    x7 += cd.width + g7

# ---- E8: full screen — a different way to learn
a8, b8 = E["Sometimes"]
t_diff = tw("Sometimes", "different")
add(chip(rich([("A ", "n"), ("different", "hl"), (" way to learn", "n")], 50), CREAM), 540, 306, t_diff - 0.5, b8 + 0.05, ain="rise", aout="rise", dist=34)
sfx(t_diff - 0.5, "tick", -6)

# ---- E9: full screen — float or sink
a9, b9 = E["Instead of asking"]
t_why = tw("Instead of asking", "why")
float_sink = chip(rich([("Why things ", "n"), ("float", "hl"), (" or ", "n"), ("sink", "hl"), ("?", "n")], 48), CREAM)
add(float_sink, 540, 306, t_why - 0.1, b9 - 0.07, ain="rise", aout="rise", dist=34)
sfx(t_why - 0.1, "tick", -6); sfx(tw("Instead of asking", "float") - 0.05, "plop", -9, pitch=1.3); sfx(tw("Instead of asking", "sink,") - 0.05, "plop", -9, pitch=0.8)

# ---- E10: panel — fill a bucket, everyday objects (tank)
a10, b10 = E["Fill a bucket"]
t_fill0 = tw("Fill a bucket", "fill") - 0.05
t_fill1 = tw("Fill a bucket", "water") + 0.5
t_exp, t_every, t_obj = tw("Fill a bucket", "experiment"), tw("Fill a bucket", "everyday"), tw("Fill a bucket", "objects.")
drops = [dict(kind="ball", x=250, t=t_exp + 0.05, r=36), dict(kind="stone", x=370, t=t_every - 0.12, r=30), dict(kind="block", x=500, t=t_obj - 0.05, r=34)]
tank_img = TK.make(t_fill0, t_fill1, 0.22, 0.62, drops)
add(tank_img, 540, 546, t_D0 + 0.30, E["Now they are"][0] + 0.10, ain="rise", din=0.5, aout="rise", dist=40, dout=0.25, name="tank")
sfx(t_fill0, "pour", -10, dur=t_fill1 - t_fill0 + 0.1)
for dd, pit in zip(drops, (1.25, 0.8, 1.0)):
    sfx(dd["t"] + math.sqrt(2 * (330 - 20) / 2600.0) - 0.04, "plop", -6, pitch=pit)
for lab, key in (("Bucket", "bucket"), ("Water", "water"), ("Everyday objects", "everyday")):
    log(lab)
chips10 = [("Bucket", tw("Fill a bucket", "bucket")), ("Water", tw("Fill a bucket", "water")), ("Everyday objects", t_every)]
for fs in (42, 40, 38, 36, 34, 32):
    bodies = [pill(row([dot(18), text(s, "dm", 700, fs, CHAR)], 12), WHITE, 30, 16) for s, _ in chips10]
    if sum(b_.width for b_ in bodies) + 2 * 22 <= 900:
        break
g = 22
x = 540 - (sum(b_.width for b_ in bodies) + 2 * g) / 2
for body, (s, tt) in zip(bodies, chips10):
    add(shadow(body, (0, 8), 14, 56), x + body.width / 2, 296, tt - 0.12, E["Now they are"][0] + 0.05, ain="rise", aout="rise", dist=26)
    sfx(tt - 0.12, "tick", -6, pitch=1.0 + 0.1 * [c_[0] for c_ in chips10].index(s))
    x += body.width + g

# ---- E11: panel — predict / test / ask / learn
a11, b11 = E["Now they are"]
steps = [("Predict", tw("Now they are", "predicting,")), ("Test", tw("Now they are", "testing,")),
         ("Ask questions", tw("Now they are", "asking")), ("Learn", tw("Now they are", "learning"))]
lab_w = max(G.text_w(s, "dm", 700, 42) for s, _ in steps)
CW = lab_w + 64 + 22 + 2 * 36
pos = [(540 - CW / 2 - 12, 400), (540 + CW / 2 + 12, 400), (540 - CW / 2 - 12, 556), (540 + CW / 2 + 12, 556)]
for k, ((s, tt), (px_, py_)) in enumerate(zip(steps, pos)):
    log(s)
    num = circle(64, ORANGE)
    nt = text(str(k + 1), "dm", 800, 36, CHAR)
    num.alpha_composite(nt, ((64 - nt.width) // 2, (64 - nt.height) // 2 + 1))
    cd = card(row([num, text(s, "dm", 700, 42, CHAR)], 22), w=int(CW), h=118, px=34, py=22, r=34)
    add(cd, px_, py_, tt - 0.12, t_D1 - 0.20, ain="rise", aout="rise", dist=32)
    sfx(tt - 0.12, "tick", -6, pitch=[0.9, 1.0, 1.12, 1.26][k], pan=(-0.25 if px_ < 540 else 0.25))
t_own = tw("Now they are", "own")
log("From their own experience")
add(chip(text("From their own experience", "dm", 600, 38, CHAR), WHITE, 34, 18), 540, 690, t_own - 0.12, t_D1 - 0.20, ain="rise", aout="rise", dist=24)
sfx(t_own - 0.12, "chime", -12)

# ---- E12: full screen — curiosity to another level
a12, b12 = E["And what if your"]
t_cur = tw("And what if your", "curiosity")
log("Curiosity to another level")
add(lambda t: chip(row([I.steps(66, clamp((t - t_cur) / 1.0), CHAR, ORANGE), text("Curiosity to another level", "dm", 700, 44, CHAR)], 18), CREAM, 36),
    540, 292, t_cur - 0.12, PANELS[-1][0] - 0.02, ain="rise", aout="rise", dist=34)
sfx(t_cur - 0.12, "tick", -6); sfx(t_cur + 0.1, "riser", -14, dur=1.1)

# =============================================================== PROMO (Audio 1 + Audio 2)
logo = Image.open(f"{BRAND}/logo_full.png")


def logo_at(width):
    return logo.resize((width, int(width * logo.height / logo.width)), Image.LANCZOS)


LOGO_BIG, LOGO_SMALL, LOGO_FINAL = logo_at(720), logo_at(330), logo_at(640)
pA = "audio1"; pB = "audio2"
t_at = tw(pA, "At"); t_cub = tw(pA, "Cub,"); t_junior = tw(pA, "Junior"); t_forensics = tw(pA, "Forensics"); t_academy = tw(pA, "Academy,")
t_start = tw(pA, "starting"); t_14 = tw(pA, "14"); t_nov = tw(pA, "November,"); t_let = tw(pA, "let")
t_little = tw(pA, "little"); t_detect = tw(pA, "detectives."); t_through = tw(pA, "Through"); t_finger = tw(pA, "fingerprinting,")
t_hand = tw(pA, "handwriting"); t_hands = tw(pA, "hands-on"); t_they = tw(pA, "they"); t_toge = tw(pA, "together"); t_crack = tw(pA, "crack"); t_myst = tw(pA, "mystery.")
t_hurry = tw(pB, "Hurry"); t_spots = tw(pB, "spots"); t_lim = tw(pB, "limited."); t_comm = tw(pB, "Comment"); t_sci = tw(pB, "SCIENCE")
t_dm = tw(pB, "DM"); t_enrol = tw(pB, "enrol"); t_det2 = tw(pB, "detective."); t_det2_end = tw(pB, "detective.", end=True)
t_final = t_det2 - 0.05

# logo: reveal large in the centre, then settle at the top for the rest of the promo, then return as the closing lockup
t_logo_move0, t_logo_move1 = t_junior - 0.38, t_junior + 0.22


def logo_path(t, x, y, s):
    if t < t_logo_move0:                                           # soft scale-in while it fades up
        return 540, 780, 0.94 + 0.06 * ease_out(clamp((t - (t_at - 0.34)) / 0.8))
    if t < t_logo_move1:
        p = ease_io((t - t_logo_move0) / (t_logo_move1 - t_logo_move0))
        k = 1 + (LOGO_SMALL.width / LOGO_BIG.width - 1) * p
        return 540, 780 + (410 - 780) * p, k
    if t < t_final:
        return 540, 410, 1.0
    p = ease_io(clamp((t - t_final) / 0.55))
    return 540, 410 + (740 - 410) * p, (LOGO_SMALL.width / LOGO_FINAL.width) + (1 - LOGO_SMALL.width / LOGO_FINAL.width) * p


def logo_img(t):
    if t < t_logo_move1:
        return LOGO_BIG
    if t < t_final:
        return LOGO_SMALL
    return LOGO_FINAL


add(logo_img, 540, 780, t_at - 0.34, T_END + 1, ain="fade", din=0.5, aout="none", dout=0.0, path=logo_path, layer=3, name="logo")
sfx(t_at - 0.30, "chime", -9)
sfx(t_final, "chime", -9)

# background: slow concentric "print" rings, very light, fades in with the promo
RING_CACHE = {}


def rings(t):
    k = int(((t - PROMO_T0) * 14) % 100)
    if k not in RING_CACHE:
        im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for r in range(-100 + k, 1900, 100):
            if r > 20:
                d.ellipse((880 - r, 1560 - r, 880 + r, 1560 + r), outline=G.a(ORANGE, 30), width=3)
        RING_CACHE[k] = im
    return RING_CACHE[k]


add(rings, 540, 960, PROMO_T0 - 0.2, T_END + 1, ain="fade", din=0.9, aout="none", layer=-1, name="rings")

# --- headline block: Junior / Forensics / Academy + date
log("Junior"); log("Forensics"); log("Academy"); log("Starts 14 November")
t_head_out = t_let - 0.1
l_j = text("Junior", "ebi", 500, 132, CHAR)
l_f = text("Forensics", "dm", 800, 120, CHAR)
l_a = pill(text("Academy", "dm", 800, 120, CHAR), ORANGE, 44, 14, r=46)
for im, y, tt in ((l_j, 840, t_junior), (l_f, 970, t_forensics), (l_a, 1118, t_academy - 0.05)):
    add(im, 540, y, tt - 0.05, t_head_out, ain="wipe_up", din=0.5, aout="rise", dist=26, dout=0.25)
    sfx(tt - 0.05, "swipe", -9, pan=0.0)
datep = shadow(pill(row([dot(22, ORANGE), text("Starts 14 November", "dm", 700, 52, CREAM)], 18), CHAR, 46, 24), (0, 10), 18, 60)
add(datep, 540, 1290, t_14 - 0.14, t_head_out, ain="rise", aout="rise", dist=34)
sfx(t_14 - 0.14, "tick", -6, pitch=0.9)

# --- little detectives
log("Let the children become"); log("little"); log("detectives")
add(text("Let the children become", "dm", 600, 48, G.a(CHAR, 220)), 540, 790, t_let - 0.05, t_through - 0.1, ain="rise", aout="rise", dist=26)
add(text("little", "ebi", 500, 150, CHAR), 540, 930, t_little - 0.05, t_through - 0.1, ain="wipe_up", din=0.5, aout="rise", dist=26)
det = text("detectives", "ebi", 500, 170, CHAR)
add(det, 540, 1100, t_detect - 0.05, t_through - 0.1, ain="wipe_up", din=0.5, aout="rise", dist=26)
add(G.underline(det.width - 20, 12), 540, 1196, t_detect + 0.28, t_through - 0.1, ain="wipe", din=0.5, aout="rise", dist=20, layer=1)
mag = I.magnifier(160, CHAR)


def mag_path(t, x, y, s):
    p = ease_io(clamp((t - (t_detect + 0.05)) / 0.9))
    return 300 + p * 480, 1262 - 14 * math.sin(p * math.pi), s            # scans along the underline, below the word


add(mag, 300, 1262, t_detect + 0.05, t_through - 0.1, ain="fade", din=0.25, aout="rise", path=mag_path, layer=2)
sfx(t_little - 0.05, "swipe", -9); sfx(t_detect - 0.05, "swipe", -9); sfx(t_detect + 0.05, "sweep", -12, dur=0.9)

# --- three activities
labels3 = [("Fingerprinting", t_finger), ("Handwriting analysis", t_hand), ("Hands-on science experiments", t_hands)]
ys3 = [770, 950, 1130]
t_cards_out = t_they - 0.12
CAV = G.font  # (handwriting glyphs use Caveat below)
from PIL import ImageFont


def hand_icon(p):
    fs = 104
    while True:
        f = ImageFont.truetype(f"{G.FD}/Caveat-VF.ttf", fs)
        f.set_variation_by_axes([700])
        if f.getlength("Abc") <= 126 or fs <= 60:
            break
        fs -= 4
    im = Image.new("RGBA", (150, 110), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, -10), "Abc", font=f, fill=CHAR)
    w = max(1, int(im.width * ease_io(clamp(p))))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(im.crop((0, 0, w, im.height)), (0, 0))
    d = ImageDraw.Draw(out)
    if p > 0.8:
        d.rounded_rectangle((10, 96, 10 + int(124 * clamp((p - 0.8) / 0.2)), 104), radius=4, fill=ORANGE)
    return out


def activity_card(idx, label, t0):
    log(label)

    def f(t):
        p = clamp((t - t0) / 1.0)
        if idx == 0:
            ic = I.fingerprint(112, p)
        elif idx == 1:
            ic = hand_icon(p)
        else:
            ic = I.flask(112, t - t0, 0.55)
        lab = text(label, "dm", 700, 42, CHAR)
        w, h = 920, 150
        im = rounded(w, h, 40, WHITE)
        im.alpha_composite(ic, (40 + (150 - ic.width) // 2, (h - ic.height) // 2))
        im.alpha_composite(lab, (222, (h - lab.height) // 2))
        return shadow(im, (0, 10), 20, 56)
    return f


for k, ((lab, tt), y) in enumerate(zip(labels3, ys3)):
    add(activity_card(k, lab, tt - 0.1), 540, y, tt - 0.12, t_cards_out, ain="rise", aout="rise", dist=40, din=0.45, dout=0.25)
    sfx(tt - 0.12, "tick", -6, pitch=[0.9, 1.0, 1.12][k])

# --- together / crack a mystery
log("Work together"); log("Crack a"); log("mystery")
tri = Image.new("RGBA", (96, 62), (0, 0, 0, 0))
tri.alpha_composite(circle(54, G.a(CHAR, 255)), (0, 4))
tri.alpha_composite(circle(54, G.a(ORANGE, 235)), (36, 4))
add(shadow(pill(row([tri, text("Work together", "dm", 700, 46, CHAR)], 18), WHITE, 34, 18), (0, 8), 16, 56), 540, 800,
    t_they - 0.05, t_hurry - 0.35, ain="rise", aout="rise", dist=30)
add(text("Crack a", "dm", 800, 110, CHAR), 540, 960, t_crack - 0.05, t_hurry - 0.35, ain="wipe_up", din=0.45, aout="rise", dist=26)
mys = text("mystery", "ebi", 500, 190, CHAR)
add(mys, 540, 1130, t_myst - 0.10, t_hurry - 0.35, ain="wipe_up", din=0.5, aout="rise", dist=26)
add(G.underline(mys.width - 30, 12), 540, 1236, t_myst + 0.25, t_hurry - 0.35, ain="wipe", din=0.5, aout="rise", dist=20, layer=1)
sfx(t_they - 0.05, "tick", -6); sfx(t_crack - 0.05, "swipe", -9); sfx(t_myst - 0.10, "swipe", -9); sfx(t_myst + 0.3, "chime", -12)

# --- CTA: limited spots, comment, DM
t_cta_out = t_final - 0.12
log("Hurry up"); log("Limited spots")


def spots_card(t):
    w, h = 920, 380
    im = rounded(w, h, 52, ORANGE)
    d = ImageDraw.Draw(im)
    a = text("Hurry up", "dm", 600, 46, CHAR)
    b = text("Limited spots", "dm", 800, 104, CHAR)
    im.alpha_composite(a, ((w - a.width) // 2, 44))
    im.alpha_composite(b, ((w - b.width) // 2, 118))
    n_fill = int(clamp((t - t_spots) / (t_lim - t_spots + 0.5)) * 7.999) if t > t_spots else 0
    for i in range(8):
        cx = (w - 7 * 85) / 2 + i * 85
        cy = h - 68
        r = 24
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=CHAR, width=5, fill=CHAR if i < n_fill else None)
    return shadow(im, (0, 12), 24, 60)


add(spots_card, 540, 800, t_hurry - 0.1, t_cta_out, ain="scale", din=0.5, aout="fade", dout=0.3)
sfx(t_hurry - 0.1, "pop", -7)
for i in range(7):
    sfx(t_spots + 0.04 + i * (t_lim - t_spots + 0.45) / 7, "tick", -13, pitch=0.9 + 0.05 * i)

log("Add a comment…"); log("SCIENCE")


def comment_box(t):
    w, h = 920, 140
    im = rounded(w, h, 70, WHITE)
    im.alpha_composite(circle(76, ORANGE), (36, 32))
    u = text("A", "dm", 800, 40, CHAR)
    im.alpha_composite(u, (36 + (76 - u.width) // 2, 32 + (76 - u.height) // 2))
    word = "SCIENCE"
    n = int(clamp((t - t_sci) / 0.52) * len(word) + 0.0001) if t >= t_sci else 0
    if n == 0:
        im.alpha_composite(text("Add a comment…", "dm", 500, 40, G.a(CHAR, 120)), (140, (h - 30) // 2 - 2))
    else:
        tt = text(word[:n], "dm", 800, 52, CHAR)
        im.alpha_composite(tt, (140, (h - tt.height) // 2))
        if int(t * 3) % 2 == 0 and n < len(word):
            im.alpha_composite(rounded(4, 56, 2, ORANGE), (140 + tt.width + 6, (h - 56) // 2))
    sendb = circle(76, ORANGE)
    sendb.alpha_composite(I.paper_plane(40, CHAR), (18, 18))
    im.alpha_composite(sendb, (w - 76 - 34, 32))
    return shadow(im, (0, 10), 20, 56)


add(comment_box, 540, 1082, t_comm - 0.1, t_cta_out, ain="rise", aout="fade", dist=40, din=0.45, dout=0.3)
sfx(t_comm - 0.1, "tick", -7)
for i in range(7):
    sfx(t_sci + i * 0.52 / 7, "key", -10, pitch=0.95 + 0.03 * (i % 3))
log("DM us to enrol")
dmcard = shadow(pill(row([I.paper_plane(54, CREAM), text("DM us to enrol", "dm", 700, 54, CREAM)], 22), CHAR, 50, 26), (0, 10), 20, 64)
add(dmcard, 540, 1228, t_dm - 0.1, t_cta_out, ain="rise", aout="fade", dist=44, din=0.45, dout=0.3)
sfx(t_dm - 0.1, "send", -7)

# --- closing lockup text
log("Junior Forensics Academy")
fin1 = text("Junior Forensics Academy", "dm", 800, 58, CHAR)
fin2 = shadow(pill(row([dot(22, ORANGE), text("Starts 14 November", "dm", 700, 46, CREAM)], 16), CHAR, 40, 20), (0, 8), 16, 56)
add(fin1, 540, 1130, t_final + 0.12, T_END + 1, ain="rise", din=0.4, aout="none", dist=26)
add(fin2, 540, 1235, t_final + 0.24, T_END + 1, ain="rise", din=0.4, aout="none", dist=26)

# =============================================================== punch-ins on the key words (full-screen moments)
for tp, amt in ((tw("Does your", "hate") - 0.05, 0.04), (tw("Congratulations", "scientist") - 0.05, 0.05),
                (t_diff - 0.1, 0.05), (tw("Instead of asking", "float") - 0.1, 0.04), (t_cur - 0.1, 0.05)):
    PUNCH.append((tp, amt))

# =============================================================== captions (all words, whole reel)
_t = PANELS[-1][0]
while panel_h(_t) < 820 and _t < PANELS[-1][1]:
    _t += 1 / 120
CAP_HIDE.append((_t, PROMO_T0 + 0.1))                                   # captions step aside as the video slides down under the cream
CAPTIONS = Captions(WORDS, y=1400, hide=CAP_HIDE,
                    y_for=lambda t: 1400 + 32 * ease_io(clamp(panel_h(t) / 300.0)) if t < PROMO_T0 else 1432)
SPRITES.sort(key=lambda s: s.layer)

if __name__ == "__main__":
    print("total %.2fs (%d frames); promo covers frame at %.2fs" % (TOTAL, TOTAL_FRAMES, PROMO_T0))
    print("transitions", [round(t, 2) for t in TRANSITIONS])
    print(len(SPRITES), "sprites,", len(SFX), "sfx")
    print("TEXTS:", sorted(set(TEXTS)))
    for k, c in enumerate(CAPTIONS.chunks):
        print("%6.2f-%6.2f %s" % (CAPTIONS.times[k][0], CAPTIONS.times[k][1], " ".join(w["w"] for w in c)))
