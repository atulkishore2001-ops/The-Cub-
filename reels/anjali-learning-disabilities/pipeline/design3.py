# Scene-by-scene design for the learning-disabilities reel: concern cards, sign callouts, takeaways, name card,
# captions, closing logo reveal, sound cues. Everything is timed to spoken words. Graphics live in the wall area
# above the speaker's head (y 270-760); captions sit on her torso; nothing is placed over the face.
import math, re, os
from PIL import Image, ImageDraw, ImageFilter
import gfx2 as G
from gfx2 import CHAR, CREAM, ORANGE, WHITE, text, row, col, pill, rounded, circle, shadow
from anim2 import Sprite, Captions, clamp, ease_io, ease_out, ease_in, paste
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


def add(*a, **k):
    s = Sprite(*a, **k)
    SPRITES.append(s)
    return s


def log(s):
    TEXTS.append(s)
    return s


# ------------------------------------------------------------------ type
STY = {"n": ("dm", 700, CHAR), "m": ("dm", 500, MUTED), "b": ("dm", 800, CHAR), "o": ("dm", 800, ORANGE),
       "pf": ("pfi", 600, ORANGE), "pfc": ("pfi", 500, CHAR), "cream": ("dm", 700, CREAM)}


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
    top = 10 + asc - int(size * 0.80)                   # crop to a fixed band so lines of one size stack evenly
    bot = 10 + asc + int(size * 0.30)
    return im.crop((bb[0] - 2, max(0, min(top, bb[1] - 2)), bb[2] + 2, max(bot, bb[3] + 2)))


def card(content, w=None, h=None, bg=WHITE, px=48, py=34, r=40, alpha=250):
    w = w or content.width + 2 * px
    h = h or content.height + 2 * py
    im = rounded(w, h, r, G.a(bg, alpha))
    im.alpha_composite(content, ((w - content.width) // 2, (h - content.height) // 2))
    return shadow(im, (0, 10), 22, 46)


def reveal_card(lines, times, w=None, gap=14, bg=WHITE, px=52, py=36, r=42, align="center"):
    """Card at its final size; each line fades/rises in at its own time (lines: images, times: absolute)."""
    w = w or max(l.width for l in lines) + 2 * px
    h = sum(l.height for l in lines) + gap * (len(lines) - 1) + 2 * py
    base = rounded(w, h, r, G.a(bg, 250))
    ys, y = [], py
    for l in lines:
        ys.append(y)
        y += l.height + gap
    cache = {}

    def f(t):
        ps = tuple(round(ease_out(clamp((t - tt) / 0.40)), 2) for tt in times)
        if ps not in cache:
            im = base.copy()
            for l, yy, p in zip(lines, ys, ps):
                if p <= 0:
                    continue
                x = (w - l.width) // 2 if align == "center" else px
                im.alpha_composite(G.with_alpha(l, p), (x, yy + int((1 - p) * 14)))
            cache[ps] = shadow(im, (0, 10), 22, 46)
        return cache[ps]
    return f


TOP = 470                     # centre of the graphics zone above her head
CAP_Y = 1470                  # captions (on the torso, well under the chin, above Instagram's bottom UI)
CAP_HIDE = []

E = {k: seg_span(k) for k in ("Is your", "As a parent", "He can read", "He knows", "Hi, this", "These concerns", "These signs",
                                "spelling", "And these", "Many of", "Don't label", "A formal", "With early", "Your child is",
                                "If you notice")}

# =============================================================== OPENING: parent concerns, one at a time
t_c2 = tw("As a parent", "my")
add(card(line([("Struggling in ", "n"), ("academics", "pf", 1.12), ("?", "n")], 58)), 540, TOP,
    E["Is your"][0] + 0.12, t_c2 - 0.18, ain="rise", aout="rise", dist=30, din=0.45, dout=0.3)
sfx(E["Is your"][0] + 0.10, "tick", -10)

c2 = reveal_card([line([("“My child is ", "n"), ("smart", "pf", 1.12), (",", "n")], 56),
                  line([("but his marks are ", "n"), ("low", "pf", 1.12), (".”", "n")], 56)],
                 [t_c2 - 0.05, tw("As a parent", "but") - 0.05], gap=6)
add(c2, 540, TOP, t_c2 - 0.08, E["He can read"][0] - 0.12, ain="rise", aout="rise", dist=30, din=0.45, dout=0.3)
sfx(t_c2 - 0.08, "tick", -10, pitch=1.06)

c3 = reveal_card([line([("Can ", "n"), ("read", "pf", 1.12), (",", "n")], 56),
                  line([("but doesn’t ", "n"), ("understand", "pf", 1.12)], 56)],
                 [E["He can read"][0] - 0.02, tw("He can read", "doesn't") - 0.05], gap=6)
add(c3, 540, TOP, E["He can read"][0] - 0.05, E["He knows"][0] - 0.12, ain="rise", aout="rise", dist=30, din=0.45, dout=0.3)
sfx(E["He can read"][0] - 0.05, "tick", -10, pitch=0.96)

t_or = tw("He knows", "or")
c4 = reveal_card([line([("Knows the answer at ", "n"), ("home", "pf", 1.12), (",", "n")], 56),
                  line([("but forgets in ", "n"), ("exam", "pf", 1.12)], 56)],
                 [E["He knows"][0] - 0.02, tw("He knows", "but") - 0.05], gap=6)
add(c4, 540, TOP, E["He knows"][0] - 0.05, t_or - 0.10, ain="rise", aout="rise", dist=30, din=0.45, dout=0.3)
sfx(E["He knows"][0] - 0.05, "tick", -10, pitch=1.03)

c5 = reveal_card([line([("or does not know how to", "n")], 56),
                  line([("write it down", "pf", 1.16)], 56)],
                 [t_or - 0.02, tw("He knows", "write") - 0.08], gap=6)
add(c5, 540, TOP, t_or - 0.05, E["Hi, this"][0] - 0.10, ain="rise", aout="rise", dist=30, din=0.45, dout=0.3)
sfx(t_or - 0.05, "tick", -10, pitch=0.98)

# =============================================================== NAME CARD (replaces the caption for this line)
t_hi0, t_hi1 = E["Hi, this"]
mark = Image.open(f"{BRAND}/logo_mark.png").convert("RGBA")
mark = mark.resize((150, int(150 * mark.height / mark.width)), Image.LANCZOS)
nm = col([line([("Anjali Rawat", "b")], 60),
          line([("Clinical Psychologist", "m"), ("  ·  ", "m"), ("The Cub", "o")], 36)], gap=8, align="left")
nc_w = 52 + mark.width + 34 + nm.width + 56
nc = rounded(nc_w, 196, 44, G.a(WHITE, 252))
nc.alpha_composite(mark, (52, (196 - mark.height) // 2))
nc.alpha_composite(rounded(4, 110, 2, G.a(ORANGE, 255)), (52 + mark.width + 16, 43))
nc.alpha_composite(nm, (52 + mark.width + 34, (196 - nm.height) // 2))
nc = shadow(nc, (0, 10), 22, 50)
add(nc, 540, CAP_Y - 30, t_hi0 - 0.05, t_hi1 + 0.12, ain="rise", aout="fade", dist=34, din=0.5, dout=0.3)
CAP_HIDE.append((t_hi0 - 0.08, t_hi1 + 0.12))
sfx(t_hi0 - 0.05, "slide", -9)

# =============================================================== MAIN: what it may be
t_sp = tw("These concerns", "specific")
t_noth = tw("These concerns", "nothing")
m1 = reveal_card([line([("These concerns may point to", "m")], 40),
                  line([("specific learning", "b")], 62),
                  line([("disability", "pf", 1.18)], 62)],
                 [E["These concerns"][0] - 0.02, t_sp - 0.08, tw("These concerns", "disability") - 0.08], gap=8)
add(m1, 540, TOP - 50, E["These concerns"][0] - 0.06, E["These signs"][0] - 0.15, ain="rise", aout="rise", dist=30, din=0.45, dout=0.3)
sfx(E["These concerns"][0] - 0.06, "tick", -10)
intel = shadow(pill(line([("Nothing to do with ", "cream"), ("intelligence", "pf", 1.12)], 46), G.a(CHAR, 244), 40, 18),
               (0, 8), 18, 50)
add(intel, 540, TOP + 222, t_noth - 0.08, E["These signs"][0] - 0.15, ain="scale", aout="rise", din=0.45, dout=0.3)
sfx(t_noth - 0.08, "swipe", -13)

# =============================================================== MAIN: early signs
t_signs0 = E["These signs"][0]
t_six = tw("These signs", "6")
t_like = tw("These signs", "like")
t_signs1 = E["spelling"][1]
hdr = reveal_card([line([("Signs can appear as early as", "m")], 40),
                   line([("6–8 ", "pf", 1.5), ("years", "b")], 76)],
                  [t_signs0 - 0.02, t_six - 0.08], gap=10)
add(hdr, 540, TOP, t_signs0 - 0.06, t_like - 0.05, ain="rise", aout="rise", dist=30, din=0.45, dout=0.28)
sfx(t_signs0 - 0.06, "tick", -10); sfx(t_six - 0.08, "tick", -11, pitch=1.1)
chip_s = shadow(pill(line([("Early signs", "cream"), ("  ·  ", "cream"), ("6–8 years", "pf", 1.1)], 36), G.a(CHAR, 240), 30, 14),
                (0, 6), 14, 44)
add(chip_s, 540, 318, t_like + 0.10, t_signs1 + 0.25, ain="rise", aout="rise", dist=20, din=0.4, dout=0.3)

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


def ill_numbers(t_swap):
    one, two = glyph("1", 150, CHAR), glyph("2", 150, CHAR)

    def f(t):
        p = ease_io(clamp((t - t_swap) / 0.55))
        im = Image.new("RGBA", (ILL, ILL), (0, 0, 0, 0))
        dx = 49
        x1 = -dx + 2 * dx * p                               # "12" -> "21": the digits trade places over a small arc
        x2 = dx - 2 * dx * p
        lift = math.sin(math.pi * p) * 34
        im.alpha_composite(one, (int(x1), int(-lift)))
        im.alpha_composite(two if p < 1 else glyph("2", 150, ORANGE), (int(x2), int(lift)))
        return im
    return f


def ill_homework(t_push):
    def f(t):
        p = ease_io(clamp((t - t_push) / 0.6))
        im = Image.new("RGBA", (ILL * 2, ILL * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        bw, bh = 150, 186
        x0, y0 = ILL - bw // 2, ILL - bh // 2
        d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 14, fill=WHITE, outline=CHAR, width=6)
        d.rectangle((x0, y0 + 6, x0 + 22, y0 + bh - 6), fill=ORANGE)
        for k in range(4):
            yy = y0 + 46 + k * 34
            d.line((x0 + 42, yy, x0 + bw - 22, yy), fill=G.a(CHAR, 150), width=5)
        im = im.rotate(-14 * p, Image.BICUBIC, center=(ILL, ILL))
        im = G.with_alpha(im, 1 - 0.55 * p)
        out = Image.new("RGBA", (ILL, ILL), (0, 0, 0, 0))
        out.alpha_composite(im, (-ILL // 2 + int(52 * p), -ILL // 2))
        return out
    return f


t_mix = tw("These signs", "mixing")
t_slow = tw("These signs", "slow")
t_spell = E["spelling"][0]
t_messy = tw("spelling", "messy")
t_trouble = tw("spelling", "trouble")
t_avoid = tw("spelling", "avoiding")
SIGNS = [
    (t_mix, [[("Mixing up ", "n"), ("b", "pf", 1.15), (" and ", "n"), ("d", "pf", 1.15)]], ill_bd(tw("These signs", "d") - 0.12)),
    (t_slow, [[("Slow", "n")], [("handwriting", "n")]], ill_slow(t_slow + 0.1, t_spell - t_slow + 0.2)),
    (t_spell, [[("Spelling the same", "n")], [("word ", "n"), ("differently", "pf", 1.1)], [("each time", "n")]],
     ill_spell([t_spell + 0.15, tw("spelling", "differently") - 0.05, tw("spelling", "each") - 0.02])),
    (t_messy, [[("Messy handwriting", "n")], [("despite ", "n"), ("several", "pf", 1.1)], [("attempts", "pf", 1.1)]],
     ill_messy([t_messy + 0.05, tw("spelling", "despite") + 0.05, tw("spelling", "several") + 0.05])),
    (t_trouble, [[("Trouble with", "n")], [("numbers", "pf", 1.15)]], ill_numbers(tw("spelling", "numbers") - 0.05)),
    (t_avoid, [[("Avoiding", "n")], [("homework", "pf", 1.15)]], ill_homework(tw("spelling", "homework") - 0.05)),
]
for k, (t0, lab, ill) in enumerate(SIGNS):
    t1 = SIGNS[k + 1][0] - 0.06 if k + 1 < len(SIGNS) else t_signs1 + 0.25
    last = k + 1 == len(SIGNS)
    add(sign_card(lab, ill), 540, 572, t0 - 0.12, t1 + (0 if last else 0.18), ain="fade" if k == 0 else "right",
        aout="rise" if last else "left", dist=56, din=0.34, dout=0.3 if last else 0.22)
    sfx(t0 - 0.12, "tick" if k == 0 else "swipe", -11 if k == 0 else -15, pitch=1.0 + 0.03 * k)

# =============================================================== MAIN: not about being bright
t_not = tw("And these", "not")
t_but = tw("And these", "but")
m3 = reveal_card([line([("Not because they aren’t bright,", "m")], 42),
                  line([("but because their brain", "b")], 56),
                  line([("works ", "b", 1.0), ("differently", "pf", 1.5)], 56)],
                 [t_not - 0.08, t_but - 0.06, tw("And these", "works") - 0.06], gap=10)
add(m3, 540, TOP, t_not - 0.12, E["Many of"][0] - 0.12, ain="rise", aout="rise", dist=30, din=0.45, dout=0.3)
sfx(t_not - 0.12, "tick", -10); sfx(tw("And these", "works") - 0.06, "chime", -19)

# =============================================================== MAIN: small, specific steps
t_learn = tw("Many of", "learning")
t_broken = tw("Many of", "broken")
t_small = tw("Many of", "small")
t_steps = tw("Many of", "steps")
lab_top = line([("Children do best when learning is", "m")], 40)
lab_mid = line([("broken down into", "b")], 58)
lab_bot = shadow(pill(line([("small and ", "cream"), ("specific steps", "pf", 1.14)], 48), G.a(CHAR, 244), 40, 18), (0, 8), 18, 50)
log("Children do best when learning is broken down into small and specific steps")


def steps_panel(t):
    w, h = 900, 470
    im = rounded(w, h, 44, G.a(WHITE, 252))
    p0 = ease_out(clamp((t - (t_learn - 0.3)) / 0.4))
    im.alpha_composite(G.with_alpha(lab_top, p0), ((w - lab_top.width) // 2, 34))
    p1 = ease_out(clamp((t - (t_broken - 0.05)) / 0.4))
    im.alpha_composite(G.with_alpha(lab_mid, p1), ((w - lab_mid.width) // 2, 90 + int((1 - p1) * 12)))
    d = ImageDraw.Draw(im)
    n = 4
    bw, gap, x0, base = 118, 22, (w - (4 * 118 + 3 * 22)) // 2, 420
    span = (t_steps - t_broken) + 0.1
    hop = None
    for i in range(n):
        q = ease_out(clamp((t - (t_broken + 0.25 + i * span / n)) / 0.35))
        if q <= 0:
            continue
        hh = (54 + 46 * i) * q
        x = x0 + i * (bw + gap)
        d.rounded_rectangle((x, base - hh, x + bw, base), 16, fill=ORANGE if i == n - 1 else G.a(CHAR, 235))
        hop = (x + bw / 2, base - hh - 26, q)
    if hop:
        x, y, q = hop
        d.ellipse((x - 18, y - 18 - 22 * math.sin(math.pi * q), x + 18, y + 18 - 22 * math.sin(math.pi * q)), fill=ORANGE)
    return shadow(im, (0, 10), 22, 46)


t_m4_out = E["Don't label"][0] - 0.12
add(steps_panel, 540, 470, t_learn - 0.35, t_m4_out, ain="rise", aout="rise", dist=30, din=0.45, dout=0.3)
add(lab_bot, 540, 742, t_small - 0.08, t_m4_out, ain="rise", aout="rise", dist=20, din=0.4, dout=0.3, layer=1)
sfx(t_learn - 0.35, "tick", -10)
for i in range(4):
    sfx(t_broken + 0.25 + i * ((t_steps - t_broken) + 0.1) / 4, "tick", -16, pitch=0.9 + 0.08 * i)

# =============================================================== ENDING: calm takeaways
def takeaway(num, parts, size=52, sub=None):
    badge = circle(64, ORANGE)
    nn = text(str(num), "dm", 800, 34, WHITE)
    badge.alpha_composite(nn, ((64 - nn.width) // 2, (64 - nn.height) // 2 + 1))
    body = line(parts, size)
    if sub is not None:
        body = col([body, sub], gap=6, align="left")
    return row([badge, body], gap=26)


def page(items, w=None):
    """items: [(image, t_in)] stacked left-aligned on one white card; each item fades up at its time."""
    px, py, gap = 52, 40, 26
    w = w or max(760, max(i.width for i, _ in items) + 2 * px)
    h = sum(i.height for i, _ in items) + gap * (len(items) - 1) + 2 * py
    cache = {}

    def f(t):
        ps = tuple(round(ease_out(clamp((t - tt) / 0.45)), 2) for _, tt in items)
        if ps not in cache:
            im = rounded(w, h, 44, G.a(WHITE, 252))
            y = py
            for (it, _), p in zip(items, ps):
                if p > 0:
                    im.alpha_composite(G.with_alpha(it, p), (px, y + int((1 - p) * 14)))
                y += it.height + gap
            cache[ps] = shadow(im, (0, 10), 22, 46)
        return cache[ps]
    return f


t_dont, t_get, t_formal = E["Don't label"][0], tw("Don't label", "get"), E["A formal"][0]
t_support = tw("A formal", "support")
t_with, t_lazy, t_learns = E["With early"][0], E["Your child is"][0], tw("Your child is", "he")
sub = line([("A formal one is usually done once schooling begins", "m")], 32)
pA = page([(takeaway(1, [("Don’t ", "n"), ("label", "pf", 1.14), (" your child", "n")]), t_dont - 0.05),
           (takeaway(2, [("Get an ", "n"), ("assessment", "pf", 1.14)], sub=None), t_get - 0.05),
           (row([Image.new("RGBA", (64, 4)), sub], gap=26), t_formal - 0.02)])
add(pA, 540, TOP, t_dont - 0.10, t_support - 0.45, ain="rise", aout="rise", dist=30, din=0.5, dout=0.35)
sfx(t_dont - 0.08, "tick", -11); sfx(t_get - 0.05, "tick", -12, pitch=1.06)

pB = page([(takeaway(3, [("Support can start ", "n"), ("much earlier", "pf", 1.14)]), t_support - 0.08),
           (takeaway(4, [("With early help, your child", "n")], sub=line([("can do ", "n"), ("wonders", "pf", 1.14)], 52)),
            t_with - 0.05)])
add(pB, 540, TOP, t_support - 0.12, t_lazy - 0.15, ain="rise", aout="rise", dist=30, din=0.5, dout=0.35)
sfx(t_support - 0.10, "tick", -11, pitch=0.97); sfx(t_with - 0.05, "tick", -12, pitch=1.04)

pC = reveal_card([line([("Your child is not ", "b"), ("lazy", "pf", 1.16), (".", "b")], 60),
                  line([("He just learns ", "b"), ("differently", "pf", 1.3), (".", "b")], 60)],
                 [t_lazy - 0.02, t_learns - 0.05], gap=14)
add(pC, 540, TOP, t_lazy - 0.08, E["If you notice"][0] - 0.12, ain="rise", aout="rise", dist=30, din=0.5, dout=0.35)
sfx(t_lazy - 0.08, "tick", -11); sfx(t_learns - 0.05, "chime", -19)

# CTA
t_if, t_reach, t_cub, t_as = E["If you notice"][0], tw("If you notice", "reach"), tw("If you notice", "the", 1), tw("If you notice", "as")
wm = Image.open(f"{BRAND}/logo_wordmark.png").convert("RGBA")
wm = wm.resize((300, int(300 * wm.height / wm.width)), Image.LANCZOS)
log("THE CUB (wordmark)")
cta = reveal_card([line([("If you notice the signs,", "m")], 40),
                   line([("please reach out to us at", "n")], 52),
                   wm,
                   line([("We are here to help you", "pfc", 1.0)], 50)],
                  [t_if - 0.02, t_reach - 0.15, t_cub - 0.08, t_as - 0.02], gap=18, py=40)
T_CREAM0 = T_EXP_END - 0.14                 # gentle cross-fade to the brand frame starts right after the last word
T_CREAM1 = T_CREAM0 + 0.85
add(cta, 540, TOP, t_if - 0.08, T_CREAM0 + 0.45, ain="rise", aout="fade", dist=30, din=0.5, dout=0.45)
sfx(t_if - 0.08, "tick", -11); sfx(t_cub - 0.08, "chime", -18)
CAP_HIDE.append((T_CREAM0, T_END + 1))

# =============================================================== CLOSING: logo + tagline on cream


def cream_alpha(t):
    return ease_io(clamp((t - T_CREAM0) / (T_CREAM1 - T_CREAM0)))


logo = Image.open(f"{BRAND}/logo_full.png").convert("RGBA")
logo = logo.resize((420, int(420 * logo.height / logo.width)), Image.LANCZOS)
T_LOGO = T_CREAM0 + 0.55
T_TAG = T_LOGO + 0.85
TAGLINE = "Every Child Deserves To Be Seen"
log(TAGLINE)
tag = line([(TAGLINE, "pfc")], 60)


def logo_img(t):
    p = clamp((t - T_LOGO) / 1.1)
    e = ease_out(p)
    s = 0.94 + 0.06 * e
    im = logo.resize((int(logo.width * s), int(logo.height * s)), Image.LANCZOS) if s < 0.999 else logo
    return G.with_alpha(im, ease_io(clamp(p * 1.3)))


def tag_img(t):
    p = clamp((t - T_TAG) / 1.15)
    return G.with_alpha(wipe(tag, ease_io(p), feather=140), clamp(p * 2.5))


add(logo_img, 540, 820, T_LOGO, T_END + 1, ain="none", aout="none", din=0, dout=0, layer=5)
add(tag_img, 540, 1130, T_TAG, T_END + 1, ain="none", aout="none", din=0, dout=0, layer=5,
    path=lambda t, x, y, s: (x, y + 12 * (1 - ease_out(clamp((t - T_TAG) / 1.0))), s))
add(lambda t: G.underline(max(2, int(110 * ease_io(clamp((t - T_TAG - 0.7) / 0.6)))), 6), 540, 1212, T_TAG + 0.7, T_END + 1,
    ain="none", aout="none", din=0, dout=0, layer=5)
sfx(T_CREAM0 - 0.05, "whoosh", -20, dur=0.9)
sfx(T_LOGO + 0.05, "chime", -14)

# =============================================================== captions (whole reel)
CAPTIONS = Captions(WORDS, y=CAP_Y, hide=CAP_HIDE, size=50, max_chars=28, max_words=5)
SPRITES.sort(key=lambda s: s.layer)

if __name__ == "__main__":
    print("total %.2fs (%d frames); cream from %.2f, logo %.2f, tagline %.2f" % (TOTAL, TOTAL_FRAMES, T_CREAM0, T_LOGO, T_TAG))
    print(len(SPRITES), "sprites,", len(SFX), "sfx")
    print("TEXTS:")
    for s in sorted(set(TEXTS)):
        print("  ", s)
    for k, c in enumerate(CAPTIONS.chunks):
        print("%6.2f-%6.2f %s" % (CAPTIONS.times[k][0], CAPTIONS.times[k][1], " ".join(w["w"] for w in c)))
