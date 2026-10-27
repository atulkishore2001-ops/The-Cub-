# World Stroke Day reel: every graphic, caption and sound cue, timed to spoken words.
# Layout: captions in one fixed place just above the speaker's head; explanation cards over the dark shirt below the
# chin; the FAST sequence (F, A, S, other signs, T, what to do) on one consistent foreground panel while the speaker
# is softly blurred behind it. Ends on the standard The Cub logo reveal (same as the Anjali reel).
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
LOW_TOP = 1100               # explanation cards hang from here (below the chin, over the shirt)
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


# =============================================================== 1. HOOK: 7 million
t_7 = tw("Every year", "7")
t_any = E["And you know"][0]
big7 = line([("7 million", "o")], 120)
h1 = content(900, 300, [(line([("Every year, around", "m")], 40), 450, 52, None),
                        (big7, 450, 150, t_7 - 0.1),
                        (line([("people die from stroke", "n")], 50), 450, 250, t_7 + 0.25)])
h2 = content(900, 300, [(line([("It can happen to", "n")], 56), 450, 90, None),
                        (line([("anyone", "pf", 1.3), (", at ", "n"), ("any age", "pf", 1.3), (".", "n")], 56), 450, 190, None)])
States([(0, h1), (tw("And you know", "it") - 0.1, h2)], E["Every year"][0] + 0.05, E["So, what is"][0] - 0.25, 980, 330)

# =============================================================== 2. WHAT IS A STROKE (brain + vessels)
t_q = E["So, what is"][0]
t_blocked, t_burst = tw("It happens", "blocked"), tw("It happens", "bursts")
t_without, t_mins, t_2m = E["Without blood"][0], tw("Without blood", "minutes"), tw("Without blood", "2")
BR_S = 0.86
T_BR0 = E["It happens"][0] - 0.2


def brain_img(t):
    im = IL.brain(t - T_BR0, t_blocked - T_BR0 - 0.1, t_burst - T_BR0 - 0.1, t_without - T_BR0 + 0.3)
    return im.resize((int(im.width * BR_S), int(im.height * BR_S)), Image.LANCZOS)


def stage_text(parts_list, size=46):
    return col([line(p, size) for p in parts_list], gap=6, align="left")


ST = [(T_BR0, stage_text([[("Blood flow to the", "n")], [("brain is ", "n"), ("blocked", "pf", 1.15)]])),
      (tw("It happens", "or") - 0.05, stage_text([[("or a blood vessel", "n")], [("in the brain ", "n"), ("bursts", "pf", 1.15)]])),
      (t_without - 0.05, stage_text([[("Without blood,", "n")], [("brain cells start", "n")], [("dying within ", "n"), ("minutes", "pf", 1.15)]])),
      (t_2m - 0.1, col([line([("about", "m")], 38), line([("2 million", "o")], 76), line([("brain cells every minute", "r")], 34)],
                       gap=6, align="left"))]


def right_col(t):
    k = max(i for i, (ts, _) in enumerate(ST) if t >= ts - 0.2 or i == 0)
    p = clamp((t - (ST[k][0] - 0.2)) / 0.4) if k else clamp((t - ST[0][0]) / 0.4)
    im = blank(520, 300)
    if p < 0.5 and k:
        put(im, ST[k - 1][1], ST[k - 1][1].width / 2 + 4, 150, ease_io(1 - 2 * p))
    else:
        a = ease_io(2 * p - 1) if k else ease_io(p)
        put(im, ST[k][1], ST[k][1].width / 2 + 4, 150 + (1 - a) * 8, a)
    return im


q_title = line([("What is a ", "b"), ("stroke", "pf", 1.2), ("?", "b")], 50)
c2 = content(960, 400, [(q_title, 480, 46, None),
                        (brain_img, 40 + 344 / 2, 240, T_BR0),
                        (right_col, 400 + 520 / 2, 240, T_BR0)])
States([(0, c2)], t_q - 0.1, E["So, what are"][0] - 0.25, 980, 410)
sfx(t_blocked - 0.1, "tick", -16, pitch=0.9); sfx(t_burst - 0.1, "tick", -16, pitch=0.85)

# =============================================================== 3. CAUSES -> PREVENTION
CAUSES = [("High blood\npressure", IL.ic_bp, tw("High blood", "high")), ("Diabetes", IL.ic_diabetes, tw("High blood", "diabetes")),
          ("Smoking", IL.ic_smoking, tw("High blood", "smoking")), ("Stress", IL.ic_stress, tw("High blood", "stress"))]


def cause_tile(lab, ic):
    lines = [line([(s, "r")], 34) for s in lab.split("\n")]
    im = ic(1.0)
    im = im.resize((150, 150), Image.LANCZOS)
    t_ = col([im] + [col(lines, gap=0)], gap=4)
    return t_


c3 = content(960, 330, [(line([("Common ", "b"), ("causes", "pf", 1.2)], 50), 480, 42, None)] +
             [(cause_tile(l, ic), 120 + 240 * k, 205, tt - 0.1) for k, (l, ic, tt) in enumerate(CAUSES)])
for k, (l, ic, tt) in enumerate(CAUSES):
    log(l.replace("\n", " "))
    if k:
        sfx(tt - 0.1, "tick", -17, pitch=0.95 + 0.05 * k)
t_good = E["but the good"][0]
c4 = content(960, 330, [(IL.ic_check(120), 150, 150, None),
                        (col([line([("The good news:", "m")], 42), line([("it can be ", "n"), ("prevented", "pf", 1.25)], 58)],
                             gap=10, align="left"), 560, 150, None)])
States([(0, c3), (t_good - 0.05, c4)], E["So, what are"][0] - 0.1, E["But first"][0] - 0.25, 980, 360)

# =============================================================== 4. FAST SEQUENCE (blurred speaker, foreground panel)
T_FAST0 = tw("But first", "remember") - 0.1           # blur in; panel appears
T_FAST1 = E["Neither"][1] + 0.35                       # blur out after "...nor wait for it to pass."
BLUR_IN, BLUR_OUT = 0.6, 0.6


def blur_amount(t):
    return ease_io(clamp((t - T_FAST0) / BLUR_IN)) * ease_io(clamp((T_FAST1 + BLUR_OUT - t) / BLUR_OUT))


LETTERS = "FAST"
WORDS4 = ["Face", "Arms", "Speech", "Time"]
FW, FH = 960, 450                                     # FAST card content size (same lower position as every card)


def tile(ch, active, size=60):
    im = G.rounded(size, size, int(size * 0.24), ORANGE if active else G.a(CREAM, 255),
                   outline=None if active else G.a(CHAR, 40), width=0 if active else 3)
    t_ = text(ch, "dm", 800, int(size * 0.56), WHITE if active else G.a(CHAR, 120))
    im.alpha_composite(t_, ((size - t_.width) // 2, (size - t_.height) // 2))
    return im


def progress(active):                                   # the F A S T row: same place on every FAST screen
    return row([tile(c, i == active) for i, c in enumerate(LETTERS)], gap=14)


def header(letter_i, title, size=62):
    if letter_i is None:
        return line([(title, "b")], size)
    return line([(LETTERS[letter_i], "o", 1.15), ("  \u00b7  ", "m"), (title, "b")], size)


def qtext(lines_, size=48):
    return col([line(l, size) for l in lines_], gap=4, align="left")


def left(im, x, y):                                     # left-aligned placement helper for content()
    return (im, x + im.width / 2, y, None)


t_fword = tw("But first", "FAST")
t_F, t_A, t_S, t_also, t_T = E["F is"][0], E["A is"][0], E["S is"][0], E["And also"][0], E["And finally"][0]
t_ifever, t_call, t_now = E["If you ever"][0], tw("If you ever", "call"), tw("If you ever", "immediately")
t_note = E["Note when"][0]
PROG_Y, ILL = 52, 290
RX = 380                                                # right column x

big_tiles = [col([tile(c, True, 120), line([(w, "r")], 34)], gap=10) for c, w in zip(LETTERS, WORDS4)]
SC_INTRO = content(FW, FH, [(line([("Learn the signs. Remember one word:", "b")], 46), 480, 70, None)] +
                   [(im, 480 + (k - 1.5) * 200, 270, t_fword - 0.05 + 0.13 * k) for k, im in enumerate(big_tiles)])


def sign_screen(i, title, ill_fn, q):
    h = header(i, title)
    qq = qtext(q)
    return content(FW, FH, [(progress(i), 480, PROG_Y, None),
                            (lambda t: ill_fn(t).resize((ILL, ILL), Image.LANCZOS), 40 + ILL / 2, 270, None),
                            left(h, RX, 200), left(qq, RX, 200 + h.height / 2 + 30 + qq.height / 2)])


SC_F = sign_screen(0, "Face", lambda t: IL.face_droop(ease_io((t - (tw("F is", "droop") - 0.1)) / 0.7)),
                   [[("Does one side", "n")], [("droop", "pf", 1.15), (" when they", "n")], [("smile?", "n")]])
SC_A = sign_screen(1, "Arms", lambda t: IL.arms(ease_io((t - (tw("A is", "drift") - 0.1)) / 0.9)),
                   [[("Does one arm", "n")], [("drift down", "pf", 1.15)], [("or feel weak?", "n")]])
SC_S = sign_screen(2, "Speech", lambda t: IL.speech_bubble(t, tw("S is", "is", 1) - 0.1),
                   [[("Is it ", "n"), ("slurred", "pf", 1.15)], [("or hard to", "n")], [("understand?", "n")]])


def icon_row(ic, label, size=50, w=880, ih=96):
    lab = line(label, size)
    im = blank(w, ih)
    put(im, ic, ih / 2, ih / 2)
    put(im, lab, ih + 30 + lab.width / 2, ih / 2)
    return im


def sc(ic, k):
    return ic.resize((int(ic.width * k), int(ic.height * k)), Image.LANCZOS)


ALSO = [(lambda t: icon_row(sc(IL.ic_dizzy(t), 0.8), [("Sudden ", "n"), ("dizziness", "pf", 1.15)]), tw("And also", "sudden") - 0.1),
        (lambda t: icon_row(sc(IL.ic_vision(t), 0.8), [("Vision ", "n"), ("trouble", "pf", 1.15)]), tw("And also", "vision") - 0.1),
        (lambda t: icon_row(sc(IL.ic_headache(t), 0.8), [("Severe ", "n"), ("headache", "pf", 1.15)]), tw("And also", "severe") - 0.1)]
SC_ALSO = content(FW, FH, [(progress(-1), 480, PROG_Y, None), left(line([("Also watch for", "m")], 40), 60, 125)] +
                  [(fn, 40 + 440, 200 + k * 92, ti) for k, (fn, ti) in enumerate(ALSO)])

call_pill = pill(row([IL.ic_phone(64), line([("Call ", "w"), ("108", "w", 1.25), (" or ", "wr"), ("112", "w", 1.25)], 54)], gap=16),
                 ORANGE, 40, 22)
hT = header(3, "Time")
SC_T = content(FW, FH, [(progress(3), 480, PROG_Y, None),
                        (lambda t: IL.ic_clock(clamp((t - t_T) / 6.0), 230), 40 + ILL / 2, 270, None),
                        left(hT, RX, 160),
                        (lambda t: line([("See even ", "n"), ("one sign", "pf", 1.15), ("?", "n")], 48), RX + 210, 238, t_ifever - 0.1),
                        (call_pill, RX + call_pill.width / 2 - 20, 322, t_call - 0.15),
                        (pill(line([("immediately", "cream")], 40), G.a(CHAR, 250), 30, 12), RX + 120, 410, t_now - 0.1)])

DO = [(sc(IL.ic_clock(1.0, 96), 0.72), [("Note when ", "n"), ("symptoms started", "pf", 1.12)], t_note - 0.1),
      (sc(IL.ic_hospital(96), 0.72), [("Go to the ", "n"), ("hospital", "pf", 1.12), (", even if they go away", "n")], E["Even if"][0] - 0.1),
      (sc(IL.ic_no_food(96), 0.72), [("No food, water or ", "n"), ("medicine", "pf", 1.12)], E["Neither"][0] - 0.1),
      (sc(IL.ic_hourglass(96), 0.72), [("Never ", "n"), ("wait", "pf", 1.12), (" for it to pass", "n")], tw("Neither", "nor") - 0.1)]
SC_DO = content(FW, FH, [(progress(3), 480, PROG_Y, None), left(line([("Act fast", "m")], 40), 60, 122)] +
                [(icon_row(ic, lab, 40, 900, 74), 40 + 450, 182 + k * 76, ti) for k, (ic, lab, ti) in enumerate(DO)])

FAST_STATES = [(T_FAST0, SC_INTRO), (t_F - 0.1, SC_F), (t_A - 0.1, SC_A), (t_S - 0.1, SC_S), (t_also - 0.1, SC_ALSO),
               (t_T - 0.1, SC_T), (t_note - 0.15, SC_DO)]
PANEL = States(FAST_STATES, T_FAST0 + 0.15, T_FAST1 + 0.15, 980, FH + 10)
for ts, _ in FAST_STATES[1:]:
    sfx(ts - 0.2, "swipe", -18)
sfx(T_FAST0, "whoosh", -22, dur=0.7)
sfx(t_call - 0.15, "tick", -12, pitch=1.1)

# =============================================================== 5. WORLD STROKE DAY: save & share
t_wsd, t_save, t_life = E["This World"][0], tw("This World", "save"), tw("This World", "as")
mark = Image.open(f"{BRAND}/logo_mark.png").convert("RGBA")
mark = mark.resize((96, int(96 * mark.height / mark.width)), Image.LANCZOS)
date_pill = pill(row([mark, line([("World Stroke Day", "b"), ("  ·  ", "m"), ("29 October", "o")], 44)], gap=14),
                 G.a(CREAM, 255), 30, 14)
save_row = row([pill(IL.ic_bookmark(56), CHAR, 18, 14), line([("Save", "n")], 46), blank(30, 10),
                pill(IL.ic_share(56), CHAR, 18, 14), line([("Share with family", "n")], 46)], gap=14)
c5 = content(960, 340, [(date_pill, 480, 66, None), (save_row, 480, 175, t_save - 0.1),
                        (line([("It could ", "n"), ("save a life", "pf", 1.2), (".", "n")], 50), 480, 280, t_life - 0.1)])
T_CREAM0 = T_EXP_END - 0.10
T_CREAM1 = T_CREAM0 + 1.0
States([(0, c5)], t_wsd - 0.05, T_CREAM0 + 0.5, 980, 350)
sfx(t_save - 0.1, "tick", -16)

# =============================================================== CLOSING: standard logo + tagline (brand/outro)


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

# =============================================================== captions: one style, one place, whole reel
CAPTIONS = Captions(WORDS, y=CAP_Y, hide=[(T_CREAM0 + 0.2, T_END + 1)], size=48, max_chars=30, max_words=6)
SPRITES.sort(key=lambda s: s.layer)

if __name__ == "__main__":
    print("total %.2fs (%d frames); FAST %.2f-%.2f; cream %.2f" % (TOTAL, TOTAL_FRAMES, T_FAST0, T_FAST1, T_CREAM0))
    print(len(SPRITES), "layers,", len(SFX), "sfx")
    print("TEXTS:")
    for s in sorted(set(TEXTS)):
        print("  ", s)
    for k, c in enumerate(CAPTIONS.chunks):
        print("%6.2f-%6.2f %s" % (CAPTIONS.times[k][0], CAPTIONS.times[k][1], " ".join(w["w"] for w in c)))
