# World Stroke Day reel, revision 2: every graphic, layout change, caption and sound cue, timed to spoken words.
# Full-screen speaker, full-screen animated B-roll, speaker/graphics split screen and the blurred-background FAST
# sequence, all on one centred, symmetric grid. Ends on the standard The Cub logo reveal (same as the Anjali reel).
import math, re, os
import numpy as np
from PIL import Image, ImageDraw
import gfx2 as G
from gfx2 import CHAR, CREAM, ORANGE, WHITE, text, row, col, pill, rounded, circle, shadow
from anim2 import Sprite, Captions, clamp, ease_io, ease_out
import timeline4 as T
import illus as IL

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
CAP_Y = 458                  # captions: just above the head, below Instagram's top bar
LOW_TOP = 1120               # explanation cards hang from here (below the chin, over the shirt)
SH = 22 * 2 + 10             # shadow() padding (blur 22, offset 10)
FADE_IN, FADE_OUT = 0.45, 0.4

# a short word followed by a long "gap" inside a sentence is a recogniser timing slip
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
       "pf": ("pfi", 600, ORANGE), "pfc": ("pfi", 500, CHAR), "cream": ("dm", 700, CREAM), "r": ("dm", 600, CHAR),
       "w": ("dm", 800, WHITE), "wr": ("dm", 600, WHITE)}


def line(parts, size=56):
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
    top, bot = 10 + asc - int(size * 0.80), 10 + asc + int(size * 0.30)
    return im.crop((bb[0] - 2, max(0, min(top, bb[1] - 2)), bb[2] + 2, max(bot, bb[3] + 2)))


def blank(w, h):
    return Image.new("RGBA", (max(1, int(w)), max(1, int(h))), (0, 0, 0, 0))


def put(base, im, cx, cy, a=1.0):
    if im is None or a <= 0.01:
        return
    base.alpha_composite(G.with_alpha(im, a), (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))


def fade_ab(t, t0, t1, din=FADE_IN, dout=FADE_OUT):
    return ease_out(clamp((t - t0) / din)) * clamp((t1 - t) / dout)


E = {k: seg_span(k) for k in ("Every year", "And you know", "So, what is", "It happens", "Without blood", "So, what are",
                                "High blood", "but the good", "But first", "F is", "A is", "S is", "And also", "And finally",
                                "If you ever", "Note when", "Even if", "Neither", "This World")}


class Layer:
    """A time-ranged drawing function: draw(frame, t)."""
    layer = 0

    def __init__(self, t0, t1, fn, layer=0):
        self.t0, self.t1, self.fn, self.layer = t0, t1, fn, layer
        SPRITES.append(self)

    def active(self, t):
        return self.t0 <= t < self.t1

    def render(self, frame, t):
        self.fn(frame, t)


class States:
    """One fixed-size card whose content changes in place: old content fades out, then the new fades in.
    states: [(t_switch, fn(t) -> RGBA content)]. Card hangs from `top` (y of the card's top edge)."""

    def __init__(self, states, t0, t1, w, h, top=LOW_TOP, bg=WHITE):
        self.states, self.t0, self.t1, self.w, self.h, self.top, self.bg = states, t0, t1, w, h, top, bg
        self.base = shadow(rounded(w, h, 44, G.a(bg, 250)), (0, 10), 22, 46)
        Layer(t0, t1, self.draw)
        sfx(t0, "tick", -14)

    def draw(self, frame, t):
        a = fade_ab(t, self.t0, self.t1)
        if a <= 0.01:
            return
        k = max(i for i, (ts, _) in enumerate(self.states) if t >= ts - 0.25 or i == 0)
        p = clamp((t - (self.states[k][0] - 0.25)) / 0.45) if k else 1.0
        card = self.base.copy()
        if p < 0.5 and k:
            ci, ca = self.states[k - 1][1](t), ease_io(1 - 2 * p)
        else:
            ci, ca = self.states[k][1](t), (ease_io(2 * p - 1) if k else 1.0)
        dy = int((1 - ca) * 8)
        put(card, ci, card.width / 2, card.height / 2 + dy, ca)
        rise = int((1 - ease_out(clamp((t - self.t0) / FADE_IN))) * 14)
        frame.alpha_composite(G.with_alpha(card, a), (540 - card.width // 2, self.top - SH + 10 + rise))


def content(w, h, items):
    """items: [(image_or_fn, x_center, y_center, t_in or None)] -> fn(t) giving a w x h RGBA content image."""
    def f(t):
        im = blank(w, h)
        for it, cx, cy, ti in items:
            img = it(t) if callable(it) else it
            p = 1.0 if ti is None else ease_out(clamp((t - ti) / 0.4))
            if p > 0:
                put(im, img, cx, cy + (1 - p) * 10, p)
        return im
    return f



# ======================================================================= LAYOUT MODES (revision 2)
# FULL : full-screen speaker, face at y 860.            Graphics: one centred card above the head.
# BROLL: full-screen animated B-roll on cream (voice continues).
# SPLIT: speaker on top (face at y 470), cream panel from y 880 down with centred graphics.
# FAST : speaker softly blurred and enlarged (face at y 480, still recognisable), one centred card below the face.
# Captions sit at one fixed place (CAP_Y) in every mode. Every switch is a 0.6 s eased move; only 5 switches.
CAP_Y = 1500
MODES = {"FULL": dict(panel=1920, fy=860, z=1.05, blur=0.0),
         "BROLL": dict(panel=0, fy=500, z=1.05, blur=0.0),
         "SPLIT": dict(panel=880, fy=500, z=1.05, blur=0.0),
         "FAST": dict(panel=1920, fy=500, z=1.40, blur=1.0)}
SPLIT_TOP = 880
SPLIT_CY = 1170                       # centre of the panel's content area (910-1430, above the captions)
TR = 0.6

t_it, t_causes, t_but = E["It happens"][0], E["So, what are"][0], E["But first"][0]
T_FAST0 = tw("But first", "remember") - 0.35
T_FAST1 = E["Neither"][1] + 0.3
t_wsd = E["This World"][0]
SCHED = [(0.0, "FULL"), (t_it - 0.45, "BROLL"), (t_causes - 0.35, "SPLIT"), (T_FAST0, "FAST"), (T_FAST1, "SPLIT")]


def _mode_val(t, key):
    v = MODES[SCHED[0][1]][key]
    for ts, m in SCHED[1:]:
        p = ease_io(clamp((t - ts) / TR))
        v = v + (MODES[m][key] - v) * p
    return v


def panel_top(t):
    return _mode_val(t, "panel")


def face_y(t):
    return _mode_val(t, "fy")


def zoom(t):
    return _mode_val(t, "z")


def blur_amount(t):
    return _mode_val(t, "blur")


def mode_at(t):
    m = SCHED[0][1]
    for ts, mm in SCHED:
        if t >= ts:
            m = mm
    return m


for ts, m in SCHED[1:]:
    sfx(ts - 0.05, "whoosh" if m in ("BROLL", "FAST") else "slide", -21, dur=0.6)


def layer_fade(t0, t1, fn, din=0.45, dout=0.4):
    """Draw fn(t) -> RGBA (full frame size) between t0 and t1 with a fade."""
    def draw(frame, t):
        a = fade_ab(t, t0, t1, din, dout)
        if a > 0.01:
            frame.alpha_composite(G.with_alpha(fn(t), a))
    return Layer(t0, t1, draw)


def centred(items, h=1920):
    """items: [(img_or_fn, cy, t_in)] all centred on x = 540 -> fn(t) giving a full-frame RGBA."""
    def f(t):
        im = blank(1080, h)
        for it, cy, ti in items:
            img = it(t) if callable(it) else it
            p = 1.0 if ti is None else ease_out(clamp((t - ti) / 0.4))
            if p > 0:
                put(im, img, 540, cy + (1 - p) * 10, p)
        return im
    return f


def swap(states):
    """states: [(t_switch, fn(t) -> RGBA)]; old fades out, then new fades in (no motion), same place."""
    def f(t):
        k = max(i for i, (ts, _) in enumerate(states) if t >= ts - 0.25 or i == 0)
        p = clamp((t - (states[k][0] - 0.25)) / 0.45) if k else 1.0
        if p < 0.5 and k:
            return G.with_alpha(states[k - 1][1](t), ease_io(1 - 2 * p))
        return G.with_alpha(states[k][1](t), ease_io(2 * p - 1) if k else 1.0)
    return f


# ======================================================================= 1. FULL: hook card above the head
TOP_CARD_Y = 400                      # centre; the head starts below y ~560


def top_card(parts_lines, sizes):
    ls = [line(p, s) for p, s in zip(parts_lines, sizes)]
    c = col(ls, gap=8)
    card = rounded(c.width + 2 * 52, c.height + 2 * 30, 40, G.a(WHITE, 250))
    card.alpha_composite(c, (52, 30))
    return shadow(card, (0, 10), 22, 46)


t_7 = tw("Every year", "7")
HOOK = [(0.0, lambda t: top_card([[("Every year, around ", "n"), ("7 million", "o", 1.25)], [("people die from stroke", "n")]], [50, 50])),
        (tw("And you know", "it") - 0.1, lambda t: top_card([[("It can happen to ", "n"), ("anyone", "pf", 1.2), (",", "n")],
                                                             [("at ", "n"), ("any age", "pf", 1.2), (".", "n")]], [52, 52])),
        (E["So, what is"][0] - 0.05, lambda t: top_card([[("What is a ", "b"), ("stroke", "pf", 1.25), ("?", "b")]], [64]))]
_hook = swap(HOOK)
layer_fade(E["Every year"][0] + 0.05, t_it - 0.45, lambda t: centred([(_hook, TOP_CARD_Y, None)])(t))
sfx(E["Every year"][0] + 0.05, "tick", -14)

# ======================================================================= 2. BROLL: what is a stroke (full screen)
t_blocked, t_burst = tw("It happens", "blocked"), tw("It happens", "bursts")
t_without, t_about = E["Without blood"][0], tw("Without blood", "about")
T_BR0 = t_it - 0.2
BR_SCALE = 2.05


def big_brain(t):
    im = IL.brain(t - T_BR0, t_blocked - T_BR0 - 0.1, t_burst - T_BR0 - 0.1, t_without - T_BR0 + 0.3)
    return im.resize((int(im.width * BR_SCALE), int(im.height * BR_SCALE)), Image.LANCZOS)


def ctext(lines_, size=54):
    return col([line(l, size) for l in lines_], gap=6)


BR_TEXT = [(T_BR0, lambda t: ctext([[("Blood flow to the brain", "n")], [("is ", "n"), ("blocked", "pf", 1.2)]])),
           (tw("It happens", "or") - 0.05, lambda t: ctext([[("or a blood vessel", "n")], [("in the brain ", "n"), ("bursts", "pf", 1.2)]])),
           (t_without - 0.05, lambda t: ctext([[("Without blood, brain cells", "n")], [("start dying within ", "n"), ("minutes", "pf", 1.2)]])),
           (t_about - 0.1, lambda t: col([line([("about ", "n"), ("2 million", "o", 1.5)], 60), line([("brain cells every minute", "n")], 50)], gap=10))]
BR_TITLE = line([("What is a ", "b"), ("stroke", "pf", 1.25), ("?", "b")], 60)
_brt = swap(BR_TEXT)
layer_fade(t_it + 0.12, t_causes - 0.35, centred([(BR_TITLE, 330, None), (big_brain, 800, None), (_brt, 1290, None)]), din=0.5, dout=0.3)
sfx(t_blocked - 0.1, "tick", -16, pitch=0.9); sfx(t_burst - 0.1, "tick", -16, pitch=0.85)

# ======================================================================= 3. SPLIT: causes -> prevention
CAUSES = [("High blood\npressure", IL.ic_bp, tw("High blood", "high")), ("Diabetes", IL.ic_diabetes, tw("High blood", "diabetes")),
          ("Smoking", IL.ic_smoking, tw("High blood", "smoking")), ("Stress", IL.ic_stress, tw("High blood", "stress"))]


def cause_tile(lab, ic):
    lines = [line([(s, "r")], 36) for s in lab.split("\n")]
    im = ic(1.0).resize((170, 170), Image.LANCZOS)
    return col([im, col(lines, gap=0)], gap=6)


def causes_scene(t):
    im = blank(1080, 1920)
    put(im, line([("Common ", "b"), ("causes", "pf", 1.25)], 60), 540, SPLIT_CY - 190)
    for k, (lab, ic, tt) in enumerate(CAUSES):
        p = ease_out(clamp((t - (tt - 0.1)) / 0.4))
        if p > 0:
            put(im, cause_tile(lab, ic), 540 + (k - 1.5) * 245, SPLIT_CY + 40 + (1 - p) * 10, p)
    return im


for k, (lab, ic, tt) in enumerate(CAUSES):
    log(lab.replace("\n", " "))
    sfx(tt - 0.1, "tick", -17, pitch=0.95 + 0.05 * k)
_cause_tiles = {k: cause_tile(l, ic) for k, (l, ic, _) in enumerate(CAUSES)}
t_good = E["but the good"][0]
prevent = lambda t: centred([(IL.ic_check(150), SPLIT_CY - 110, None),
                             (line([("The good news:", "m")], 46), SPLIT_CY + 30, None),
                             (line([("it can be ", "n"), ("prevented", "pf", 1.25)], 64), SPLIT_CY + 115, None)])(t)
layer_fade(t_causes - 0.1, T_FAST0 + 0.1, swap([(0, causes_scene), (t_good - 0.05, prevent)]), dout=0.35)

# ======================================================================= 4. FAST: one centred card, strict grid
LETTERS, WORDS4 = "FAST", ["Face", "Arms", "Speech", "Time"]
CW, CH, CTOP = 960, 640, 800          # card size and top edge (blurred face stays visible above it)
GY_PROG, GY_TITLE, GY_BODY = 62, 150, 410     # grid rows inside the card: progress, title, body centre


def tile(ch, active, size=60):
    im = G.rounded(size, size, int(size * 0.24), ORANGE if active else G.a(CREAM, 255),
                   outline=None if active else G.a(CHAR, 40), width=0 if active else 3)
    t_ = text(ch, "dm", 800, int(size * 0.56), WHITE if active else G.a(CHAR, 120))
    im.alpha_composite(t_, ((size - t_.width) // 2, (size - t_.height) // 2))
    return im


def progress(active):
    return row([tile(c, i == active) for i, c in enumerate(LETTERS)], gap=14)


def header(letter_i, title, size=62):
    if letter_i is None:
        return line([(title, "b")], size)
    return line([(LETTERS[letter_i], "o", 1.15), ("  ·  ", "m"), (title, "b")], size)


def screen(prog, title, body):
    """Every FAST screen uses the same grid: progress row, title, centred body."""
    def f(t):
        im = blank(CW, CH)
        if prog is not None:
            put(im, progress(prog), CW / 2, GY_PROG)
        put(im, title, CW / 2, GY_TITLE)
        put(im, body(t), CW / 2, GY_BODY)
        return im
    return f


def stack(items, w, h):
    """items: [(img_or_fn, cy, t_in)] centred on x -> fn(t) giving a w x h RGBA."""
    def f(t):
        im = blank(w, h)
        for it, cy, ti in items:
            img = it(t) if callable(it) else it
            p = 1.0 if ti is None else ease_out(clamp((t - ti) / 0.4))
            if p > 0:
                put(im, img, w / 2, cy + (1 - p) * 8, p)
        return im
    return f


def rows_block(rows, w, row_h, ih, size):
    """Icon rows left-aligned inside a block that is itself centred: icons in one column, text in another."""
    labs = [line(lab, size) for _, lab, _ in rows]
    bw = ih + 28 + max(l.width for l in labs)
    def f(t):
        im = blank(w, row_h * len(rows))
        x0 = (w - bw) / 2
        for k, ((ic, _, ti), lab) in enumerate(zip(rows, labs)):
            p = ease_out(clamp((t - ti) / 0.4))
            if p <= 0:
                continue
            icon = ic(t) if callable(ic) else ic
            cy = row_h * k + row_h / 2 + (1 - p) * 8
            put(im, icon, x0 + ih / 2, cy, p)
            put(im, lab, x0 + ih + 28 + lab.width / 2, cy, p)
        return im
    return f


def sc(ic, k):
    return ic.resize((int(ic.width * k), int(ic.height * k)), Image.LANCZOS)


t_fword = tw("But first", "FAST")
t_F, t_A, t_S, t_also, t_T = E["F is"][0], E["A is"][0], E["S is"][0], E["And also"][0], E["And finally"][0]
t_ifever, t_call, t_now = E["If you ever"][0], tw("If you ever", "call"), tw("If you ever", "immediately")
t_note = E["Note when"][0]
ILL = 270
BODY_H = 440

big_tiles = [col([tile(c, True, 130), line([(w, "r")], 36)], gap=12) for c, w in zip(LETTERS, WORDS4)]
SC_INTRO = screen(None, line([("Remember one word", "b")], 62),
                  lambda t: (lambda im: im)(_intro_body(t)))


def _intro_body(t):
    im = blank(CW, BODY_H)
    put(im, line([("Learn the signs.", "m")], 42), CW / 2, 40)
    for k, tl_ in enumerate(big_tiles):
        p = ease_out(clamp((t - (t_fword - 0.05 + 0.13 * k)) / 0.4))
        if p > 0:
            put(im, tl_, CW / 2 + (k - 1.5) * 205, 230 + (1 - p) * 8, p)
    return im


def sign(i, title, ill_fn, q):
    qq = col([line(l, 48) for l in q], gap=4)
    return screen(i, header(i, title), stack([(lambda t: ill_fn(t).resize((ILL, ILL), Image.LANCZOS), 150, None),
                                              (qq, 365, None)], CW, BODY_H))


SC_F = sign(0, "Face", lambda t: IL.face_droop(ease_io((t - (tw("F is", "droop") - 0.1)) / 0.7)),
            [[("Does one side ", "n"), ("droop", "pf", 1.15)], [("when they smile?", "n")]])
SC_A = sign(1, "Arms", lambda t: IL.arms(ease_io((t - (tw("A is", "drift") - 0.1)) / 0.9)),
            [[("Does one arm ", "n"), ("drift down", "pf", 1.15)], [("or feel weak?", "n")]])
SC_S = sign(2, "Speech", lambda t: IL.speech_bubble(t, tw("S is", "is", 1) - 0.1),
            [[("Is it ", "n"), ("slurred", "pf", 1.15)], [("or hard to understand?", "n")]])

ALSO = [(lambda t: sc(IL.ic_dizzy(t), 0.85), [("Sudden ", "n"), ("dizziness", "pf", 1.15)], tw("And also", "sudden") - 0.1),
        (lambda t: sc(IL.ic_vision(t), 0.85), [("Vision ", "n"), ("trouble", "pf", 1.15)], tw("And also", "vision") - 0.1),
        (lambda t: sc(IL.ic_headache(t), 0.85), [("Severe ", "n"), ("headache", "pf", 1.15)], tw("And also", "severe") - 0.1)]
SC_ALSO = screen(-1, header(None, "Also watch for"), stack([(rows_block(ALSO, CW, 120, 102, 50), 200, None)], CW, BODY_H))

call_pill = pill(row([IL.ic_phone(66), line([("Call ", "w"), ("108", "w", 1.25), (" or ", "wr"), ("112", "w", 1.25)], 58)], gap=18),
                 ORANGE, 46, 24)
SC_T = screen(3, header(3, "Time"), stack([(line([("See even ", "n"), ("one sign", "pf", 1.15), ("?", "n")], 50), 70, t_ifever - 0.1),
                                          (call_pill, 210, t_call - 0.15),
                                          (pill(line([("immediately", "cream")], 42), G.a(CHAR, 250), 32, 13), 345, t_now - 0.1)],
                                         CW, BODY_H))
DO = [(sc(IL.ic_clock(1.0, 96), 0.8), [("Note when ", "n"), ("symptoms started", "pf", 1.12)], t_note - 0.1),
      (sc(IL.ic_hospital(96), 0.8), [("Go to ", "n"), ("hospital", "pf", 1.12), (", even if they go away", "n")], E["Even if"][0] - 0.1),
      (sc(IL.ic_no_food(96), 0.8), [("No food, water or ", "n"), ("medicine", "pf", 1.12)], E["Neither"][0] - 0.1),
      (sc(IL.ic_hourglass(96), 0.8), [("Never ", "n"), ("wait", "pf", 1.12), (" for it to pass", "n")], tw("Neither", "nor") - 0.1)]
SC_DO = screen(3, header(3, "Act fast"), stack([(rows_block(DO, CW, 98, 78, 40), 205, None)], CW, BODY_H))

FAST_STATES = [(T_FAST0, SC_INTRO), (t_F - 0.1, SC_F), (t_A - 0.1, SC_A), (t_S - 0.1, SC_S), (t_also - 0.1, SC_ALSO),
               (t_T - 0.1, SC_T), (t_note - 0.15, SC_DO)]
_fast = swap(FAST_STATES)
_card_bg = shadow(rounded(CW + 20, CH, 48, G.a(WHITE, 250)), (0, 10), 22, 46)


def fast_layer(t):
    im = blank(1080, 1920)
    c = _card_bg.copy()
    put(c, _fast(t), c.width / 2, c.height / 2 - 5)
    put(im, c, 540, CTOP + CH / 2)
    return im


layer_fade(T_FAST0 + 0.3, T_FAST1 + 0.15, fast_layer, din=0.5, dout=0.4)
for ts, _ in FAST_STATES[1:]:
    sfx(ts - 0.2, "swipe", -18)
sfx(t_call - 0.15, "tick", -12, pitch=1.1)

# ======================================================================= 5. SPLIT: World Stroke Day, save & share
t_save, t_life = tw("This World", "save"), tw("This World", "as")
mark = Image.open(f"{BRAND}/logo_mark.png").convert("RGBA")
mark = mark.resize((110, int(110 * mark.height / mark.width)), Image.LANCZOS)
date_pill = pill(row([mark, line([("World Stroke Day", "b"), ("  ·  ", "m"), ("29 October", "o")], 46)], gap=14), WHITE, 34, 16)
save_row = row([pill(IL.ic_bookmark(56), CHAR, 18, 14), line([("Save", "n")], 48), blank(36, 10),
                pill(IL.ic_share(56), CHAR, 18, 14), line([("Share with family", "n")], 48)], gap=14)
T_CREAM0 = T_EXP_END - 0.10
T_CREAM1 = T_CREAM0 + 1.0
layer_fade(T_FAST1 + 0.45, T_CREAM0 + 0.5, centred([(date_pill, SPLIT_CY - 170, None), (save_row, SPLIT_CY + 10, t_save - 0.1),
                                                     (line([("It could ", "n"), ("save a life", "pf", 1.2), (".", "n")], 56),
                                                      SPLIT_CY + 170, t_life - 0.1)]), din=0.5, dout=0.45)
sfx(t_save - 0.1, "tick", -16)

# ======================================================================= CLOSING: standard logo + tagline (brand/outro)


def cream_alpha(t):
    return ease_io(clamp((t - T_CREAM0) / (T_CREAM1 - T_CREAM0)))


def _wipe(im, p, feather=140):
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
    return G.with_alpha(_wipe(tag, ease_io(p)), clamp(p * 2.5))


SPRITES.append(Sprite(logo_img, 540, 820, T_LOGO, T_END + 1, ain="none", aout="none", din=0, dout=0, layer=5))
SPRITES.append(Sprite(tag_img, 540, 1130, T_TAG, T_END + 1, ain="none", aout="none", din=0, dout=0, layer=5,
                      path=lambda t, x, y, s: (x, y + 12 * (1 - ease_out(clamp((t - T_TAG) / 1.0))), s)))
SPRITES.append(Sprite(lambda t: G.underline(max(2, int(110 * ease_io(clamp((t - T_TAG - 0.7) / 0.6)))), 6), 540, 1212,
                      T_TAG + 0.7, T_END + 1, ain="none", aout="none", din=0, dout=0, layer=5))
sfx(T_LOGO + 0.05, "chime", -15)

# ======================================================================= captions: one style, one place, whole reel
CAPTIONS = Captions(WORDS, y=CAP_Y, hide=[(T_CREAM0 + 0.2, T_END + 1)], size=48, max_chars=30, max_words=6)
SPRITES.sort(key=lambda s: s.layer)

if __name__ == "__main__":
    print("total %.2fs (%d frames); modes %s; cream %.2f" % (TOTAL, TOTAL_FRAMES, [(round(a, 2), m) for a, m in SCHED], T_CREAM0))
    print(len(SPRITES), "layers,", len(SFX), "sfx")
    for k, c in enumerate(CAPTIONS.chunks):
        print("%6.2f-%6.2f %s" % (CAPTIONS.times[k][0], CAPTIONS.times[k][1], " ".join(w["w"] for w in c)))
