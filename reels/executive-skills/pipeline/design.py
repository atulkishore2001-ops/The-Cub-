# Scene-by-scene motion graphics, sound-effect cues and camera moves, timed to the spoken words.
import math, re
from PIL import Image, ImageDraw
import gfx
from gfx import INK, YEL, CORAL, TEAL, WHITE, BLACK, text, emoji, row, col, pill, shadow, rounded, badge
from anim import Sprite, Captions, ease_in_out, ease_out_cubic, clamp
from timeline import build, blocks, FPS

PIECES, WORDS, SPEECH_FRAMES = build()
BLOCKS = blocks(PIECES)
SPEECH_END = SPEECH_FRAMES / FPS
END_CARD = SPEECH_END - 0.2
TOTAL = round((SPEECH_END + 1.85) * FPS) / FPS


def T(word, seg=None, n=0):
    norm = lambda s: re.sub(r"[^a-z']", "", s.lower())
    c = [w for w in WORDS if norm(w["w"]) == norm(word) and (seg is None or seg.lower() in w["seg"].lower())]
    return c[n]["s"]


# location changes -> transitions
TRANSITIONS = [b["o_in"] / FPS for i, b in enumerate(BLOCKS) if i and b["loc"] != BLOCKS[i - 1]["loc"]]

SPRITES, SFX, PUNCH, SHAKE = [], [], [], []


def sfx(t, name, gain=0.0, pan=0.0, **kw):
    SFX.append(dict(t=t, name=name, gain=gain, pan=pan, **kw))


def add(*a, **k):
    s = Sprite(*a, **k)
    SPRITES.append(s)
    return s


def sh(im, blur=16, alpha=120, off=(0, 10)):
    return shadow(im, off, blur, alpha)


def bubble(content, bg, tail="left"):
    p = pill(content, bg, 34, 20, r=30)
    w, h = p.size
    im = Image.new("RGBA", (w, h + 26), (0, 0, 0, 0))
    im.alpha_composite(p, (0, 0))
    d = ImageDraw.Draw(im)
    x = 60 if tail == "left" else w - 60
    d.polygon([(x - 20, h - 2), (x + 20, h - 2), (x + (-12 if tail == "left" else 12), h + 24)], fill=bg)
    return sh(im)


def headline(lines, stroke=10):
    ims = [text(s, w, sz, c, stroke=stroke if st else 0, stroke_fill=INK) if isinstance(s, str) else s
           for (s, w, sz, c, st) in lines]
    return sh(col(ims, gap=-6), 18, 140)


# ---------------------------------------------------------------- HOOK
t_bus, t_away = T("bus"), T("away.")
TICK_END = TRANSITIONS[0] - 0.05


def timer_img(t, _c={}):
    remain = max(0, 300 - int(t))
    key = remain
    if key not in _c:
        _c[key] = sh(pill(row([emoji("⏰", 66), text(f"{remain // 60:02d}:{remain % 60:02d}", "Black", 78, YEL)], 16),
                          INK, 34, 18), 14, 130)
    return _c[key]


def timer_path(t, x, y, s):
    p = ease_in_out(clamp((t - (t_away + 0.25)) / 0.45))
    return x + (175 - x) * p, y + (135 - y) * p, s * (1 - 0.38 * p)


add(timer_img, 640, 235, 0.0, TICK_END, ain="pop", din=0.28, path=timer_path, layer=2)
for k in range(int(TICK_END * 2)):
    sfx(k * 0.5, "tick" if k % 2 == 0 else "tock", -10)


def bus_path(t, x, y, s):
    p_in = ease_out_cubic(clamp((t - t_bus + 0.08) / 0.5))
    p_out = clamp((t - (t_away + 0.2)) / 0.5) ** 2
    return -140 + (300 + 140) * p_in + 1100 * p_out, y + 4 * math.sin(t * 28), s


add(sh(emoji("🚌", 150), 10, 90), 0, 240, t_bus - 0.08, t_away + 0.75, ain="none", aout="none", path=bus_path, layer=3)
sfx(t_bus - 0.12, "whoosh", -4, pan=-0.5, dur=0.45)
sfx(t_bus + 0.45, "horn", -9)
sfx(t_away + 0.2, "whoosh", -5, pan=0.6, dur=0.5)

# nagging bubbles x3
t_sh, t_three, t_now = T("shoes"), T("three"), T("now.")
t_theyre = T("They're")
b1 = bubble(row([text("Shoes on!", "Bold", 44, INK), emoji("👟", 52)], 10), WHITE, "left")
b2 = bubble(row([text("SHOES ON!!", "ExtraBold", 50, INK), emoji("👟", 56)], 10), YEL, "right")
b3 = bubble(row([text("SHOES. ON. NOW!", "Black", 54, WHITE), emoji("😤", 60)], 12), CORAL, "left")
add(b1, 330, 205, t_sh - 0.05, t_theyre - 0.05, ain="pop", aout="pop", rot=5, dout=0.15)
add(b2, 760, 278, t_three - 0.05, t_theyre, ain="pop", aout="pop", rot=-5, dout=0.15)
add(b3, 540, 360, t_now - 0.08, t_theyre + 0.05, ain="pop", aout="pop", rot=2, dout=0.15, layer=1)
sfx(t_sh - 0.05, "pop", -3, pitch=1.0, pan=-0.3)
sfx(t_three - 0.05, "pop", -2, pitch=1.2, pan=0.3)
sfx(t_now - 0.08, "pop", -1, pitch=1.45)
SHAKE.append((t_now - 0.05, 0.22, 7))

# searching for socks
t_socks, t_does = T("socks."), T("Does")
add(sh(emoji("🔍", 120), 10, 90), 540, 250, t_theyre, t_does - 0.02, ain="pop", aout="pop", dout=0.12,
    path=lambda t, x, y, s: (x + 230 * math.sin(2 * math.pi * 0.9 * (t - t_theyre)), y + 25 * math.sin(2 * math.pi * 1.8 * (t - t_theyre)), s), layer=2)
add(sh(emoji("🧦", 170), 12, 100), 540, 255, t_socks - 0.04, t_does - 0.02, ain="pop", aout="pop", dout=0.12,
    wobble=(10, 2.4), layer=1)
add(sh(emoji("❓", 84), 8, 80), 690, 160, t_socks + 0.12, t_does - 0.02, ain="pop", aout="pop", dout=0.12, bob=(8, 3))
sfx(t_theyre, "whoosh", -12, dur=0.3)
sfx(t_socks - 0.04, "boing", -4)

# sound familiar?
t_sound = T("sound")
add(headline([("Does this sound", "ExtraBold", 58, WHITE, 1), (row([text("FAMILIAR?", "Black", 100, YEL, stroke=10, stroke_fill=INK), emoji("🤔", 96)], 8), 0, 0, 0, 0)]),
    540, 270, t_sound - 0.12, TRANSITIONS[0] - 0.02, ain="pop", aout="fade", dout=0.08, din=0.32)
sfx(t_sound - 0.12, "question", -4)
sfx(T("familiar?") + 0.05, "thump", -6)
PUNCH.append((t_does, 0.14))

# ---------------------------------------------------------------- INTRO / NAME CARD
t_hi = T("Hi,")
t_intro_end = BLOCKS[[b["o_in"] / FPS for b in BLOCKS].index(min(b["o_in"] / FPS for b in BLOCKS if b["o_in"] / FPS > t_hi + 1.0))]["o_in"] / FPS
name = pill(text("SAISHA", "Black", 80, INK, tracking=4), YEL, 40, 16, r=22)
role = pill(text("Developmental Psychologist", "SemiBold", 40, WHITE), INK, 30, 16, r=20)
card = sh(col([name, role], gap=12, align="left"), 18, 130)
cx = 64 + card.width / 2
add(card, cx, 1335, T("I'm", "Saisha") - 0.05, t_intro_end - 0.03, ain="slide_l", aout="slide_l", din=0.45, dout=0.28, dist=750)
add(sh(emoji("👋", 104), 10, 90), 64 + card.width + 50, 1270, t_hi - 0.02, t_intro_end - 0.03, ain="pop", aout="pop",
    dout=0.15, wobble=(16, 2.6))
sfx(t_hi - 0.02, "pop", -6, pitch=1.1)
sfx(T("I'm", "Saisha") - 0.1, "swoosh", -4, pan=-0.4)
sfx(t_intro_end - 0.3, "swoosh", -9, pan=-0.4)
CAPTION_HIDE = [(t_hi - 0.1, t_intro_end - 0.02)]

# ---------------------------------------------------------------- KNOWING != DOING
t_knowing, t_doing, t_compl = T("knowing"), T("doing"), T("completely")
t_kd_end = T("So", "skills") - 0.06
kn = sh(pill(row([text("KNOWING", "Black", 62, WHITE), emoji("✅", 50)], 10), TEAL, 32, 18), 14, 120)
do = sh(pill(row([text("DOING", "Black", 62, WHITE), emoji("❌", 46)], 10), CORAL, 32, 18), 14, 120)
neq = gfx.circle(122, INK)
neq_t = text("≠", "Black", 96, YEL)
neq.alpha_composite(neq_t, ((122 - neq_t.width) // 2, (122 - neq_t.height) // 2 - 4))
neq = sh(neq, 12, 120)
add(kn, 278, 245, t_knowing - 0.06, t_kd_end, ain="slide_l", aout="up", din=0.35)
add(do, 812, 245, t_doing - 0.06, t_kd_end, ain="slide_r", aout="up", din=0.35)
add(neq, 552, 245, t_compl - 0.05, t_kd_end, ain="pop", aout="up", din=0.3, layer=2)
sfx(t_knowing - 0.1, "swoosh", -7, pan=-0.5)
sfx(t_doing - 0.1, "swoosh", -7, pan=0.5)
sfx(t_compl - 0.05, "hit", -5)
SHAKE.append((t_compl - 0.03, 0.25, 10))
PUNCH.append((t_compl - 0.05, 0.08))

# ---------------------------------------------------------------- EXECUTIVE SKILLS
chips_t = [T("plan,"), T("follow"), T("get"), T("avoid")]
t_exec = T("executive")
chip = lambda e, s: sh(pill(row([emoji(e, 50), text(s, "Bold", 40, INK)], 12), WHITE, 26, 16), 12, 110)
c = [chip("📋", "Plan"), chip("👂", "Follow instructions"), chip("🚀", "Get started"), chip("🎯", "Avoid distractions")]
for r_, (i, j) in enumerate([(0, 1), (2, 3)]):
    tot = c[i].width + c[j].width - 30
    x0 = (1080 - tot) / 2
    xs = [x0 + c[i].width / 2, x0 + c[i].width - 30 + c[j].width / 2]
    for k, idx in enumerate((i, j)):
        add(c[idx], xs[k], 200 + r_ * 112, chips_t[idx] - 0.05, t_exec - 0.12 + 0.05 * idx, ain="pop", aout="up", dout=0.2)
        sfx(chips_t[idx] - 0.05, "pop", -5, pitch=0.9 + 0.12 * idx, pan=(-0.3 if k == 0 else 0.3))
t_mgmt_end = TRANSITIONS[2] - 0.04
add(headline([("EXECUTIVE", "Black", 108, WHITE, 1), (row([text("SKILLS", "Black", 108, YEL, stroke=10, stroke_fill=INK), emoji("✨", 84)], 8), 0, 0, 0, 0)]),
    540, 275, t_exec - 0.1, t_mgmt_end, ain="pop", din=0.36, aout="fade", dout=0.12)
sfx(t_exec - 0.25, "whoosh", -6, dur=0.35)
sfx(t_exec - 0.05, "sparkle", -5)
PUNCH.append((t_exec - 0.1, 0.10))
t_brain = T("brain's")
add(sh(pill(row([emoji("🧠", 52), text("the brain's management system", "SemiBold", 38, WHITE)], 12), INK, 28, 16), 12, 120),
    540, 470, t_brain - 0.12, t_mgmt_end, ain="slide_u", din=0.35, dist=200, aout="fade", dout=0.12)
sfx(t_brain - 0.12, "pop", -9, pitch=0.8)

# ---------------------------------------------------------------- GROWS GRADUALLY
t_fully, t_grow, t_child, t_adol = T("fully"), T("grow"), T("childhood"), T("adolescence.")
t_grow_end = T("So", "ADHD") - 0.08
add(sh(row([emoji("🌱", 64), text("STILL DEVELOPING", "Black", 62, WHITE, stroke=8, stroke_fill=INK)], 10), 12, 110),
    540, 160, t_fully - 0.05, t_grow_end, ain="pop", aout="fade")
BAR_W, BAR_H = 800, 46


def bar_img(t, _c={}):
    p = 0.12 + 0.88 * ease_in_out(clamp((t - t_grow) / (t_adol + 0.35 - t_grow)))
    key = int(p * 200)
    if key not in _c:
        im = gfx.rounded(BAR_W + 12, BAR_H + 12, (BAR_H + 12) // 2, (255, 255, 255, 235))
        fw = max(BAR_H, int(BAR_W * p))
        grad = Image.new("RGBA", (fw, BAR_H))
        for x in range(fw):
            f = x / BAR_W
            grad.paste(tuple(int(TEAL[i] + (YEL[i] - TEAL[i]) * f) for i in range(3)) + (255,), (x, 0, x + 1, BAR_H))
        mask = gfx.rounded(fw, BAR_H, BAR_H // 2, (255, 255, 255, 255)).getchannel("A")
        grad.putalpha(mask)
        im.alpha_composite(grad, (6, 6))
        pct = text(f"{int(p * 100)}%", "Black", 30, INK)
        im.alpha_composite(pct, (min(BAR_W - pct.width - 10, max(14, fw - pct.width - 10)), (BAR_H + 12 - pct.height) // 2))
        _c[key] = sh(im, 12, 110)
    return _c[key]


add(bar_img, 540, 262, t_fully + 0.1, t_grow_end, ain="fade", din=0.25, aout="fade")
add(sh(row([emoji("🧒", 50), text("Childhood", "ExtraBold", 40, WHITE, stroke=6, stroke_fill=INK)], 8), 10, 110),
    250, 345, t_child - 0.05, t_grow_end, ain="pop", aout="fade")
add(sh(row([text("Adolescence", "ExtraBold", 40, WHITE, stroke=6, stroke_fill=INK), emoji("🧑", 50)], 8), 10, 110),
    815, 345, t_adol - 0.05, t_grow_end, ain="pop", aout="fade")
sfx(t_grow - 0.1, "riser", -10, dur=t_adol + 0.35 - t_grow + 0.1)
sfx(t_child - 0.05, "pop", -7, pitch=1.0)
sfx(t_adol - 0.05, "pop", -7, pitch=1.25)
sfx(t_adol + 0.3, "chime", -8)

# ---------------------------------------------------------------- ADHD / AUTISM
t_adhd, t_aut, t_diff = T("ADHD"), T("autism,"), T("difficult")
t_ad_end = T("So", "ignoring") - 0.06
add(sh(text("Especially for kids with", "SemiBold", 46, WHITE, stroke=6, stroke_fill=INK), 10, 110),
    540, 150, T("especially") - 0.05, t_ad_end, ain="fade", aout="fade")
add(sh(pill(text("ADHD", "Black", 66, WHITE), CORAL, 34, 16), 12, 120), 382, 250, t_adhd - 0.05, t_ad_end, ain="pop", aout="up")
add(sh(text("or", "ExtraBold", 40, WHITE, stroke=5, stroke_fill=INK), 8, 100), 545, 250, t_aut - 0.2, t_ad_end, ain="fade", aout="up")
add(sh(pill(text("AUTISM", "Black", 66, WHITE), TEAL, 34, 16), 12, 120), 735, 250, t_aut - 0.05, t_ad_end, ain="pop", aout="up")
add(sh(pill(text("harder to use these skills consistently", "SemiBold", 36, WHITE), INK, 28, 14), 12, 120),
    540, 365, t_diff - 0.1, t_ad_end, ain="slide_u", dist=180, aout="up")
sfx(t_adhd - 0.05, "pop", -5, pitch=0.95, pan=-0.3)
sfx(t_aut - 0.05, "pop", -5, pitch=1.15, pan=0.3)
sfx(t_diff - 0.1, "swoosh", -10)

# ---------------------------------------------------------------- REFRAME
t_ign, t_act, t_str = T("ignoring"), T("actually"), T("struggling")
t_rf_end = TRANSITIONS[-2] - 0.04
ig = sh(pill(row([emoji("🙉", 56), text("Ignoring you?", "ExtraBold", 50, INK)], 12), WHITE, 30, 16), 12, 110)
add(ig, 540, 205, t_ign - 0.06, t_rf_end, ain="pop", aout="up", dim=(t_act, 0.55))
add(gfx.line(ig.width - 60, 12, CORAL), 540, 205, t_act - 0.02, t_rf_end, ain="wipe", din=0.22, aout="up", layer=2)
add(sh(pill(row([text("Struggling to organize", "Black", 52, INK), emoji("🧩", 56)], 12), YEL, 32, 18), 14, 130),
    540, 330, t_str - 0.06, t_rf_end, ain="pop", aout="up", din=0.33)
sfx(t_ign - 0.06, "pop", -6)
sfx(t_act - 0.02, "buzz", -10)
sfx(t_str - 0.06, "ding", -5)
PUNCH.append((t_str - 0.06, 0.09))

# ---------------------------------------------------------------- WHAT CAN YOU DO + TIPS
t_wcyd = T("So", "what can you do") - 0.02
t_inst = T("Instead")
tips_t = [T("break"), T("single"), T("visual"), T("Keep")]
t_tips_end = T("Your", "independently") - 0.08
HEAD = headline([("SO, WHAT CAN", "Black", 84, WHITE, 1), (row([text("YOU DO?", "Black", 100, YEL, stroke=10, stroke_fill=INK), emoji("💡", 92)], 8), 0, 0, 0, 0)])


def head_path(t, x, y, s):
    p = ease_in_out(clamp((t - (t_inst - 0.12)) / 0.4))
    return x, y + (88 - y) * p, s * (1 - 0.56 * p)


add(HEAD, 540, 280, t_wcyd, t_tips_end, ain="pop", din=0.36, aout="up", path=head_path, layer=3)
sfx(t_wcyd - 0.05, "whoosh", -6, dur=0.35)
sfx(t_wcyd + 0.3, "chime", -6)
PUNCH.append((t_wcyd, 0.12))
rep = sh(pill(row([emoji("🔁", 50), text("Repeating the same instruction", "Bold", 40, INK)], 12), WHITE, 28, 16), 12, 110)
t_rep_end = tips_t[0] - 0.25
add(rep, 540, 215, t_inst + 0.05, t_rep_end, ain="pop", aout="fade", dim=(T("instructions,", "Instead") + 0.2, 0.6))
add(gfx.line(rep.width - 50, 11, CORAL), 540, 215, T("instructions,", "Instead") + 0.15, t_rep_end, ain="wipe", din=0.22, aout="fade", layer=2)
sfx(t_inst + 0.05, "pop", -8)
sfx(T("instructions,", "Instead") + 0.15, "buzz", -11)
tips = [("Break the task down", "🧩"), ("One instruction at a time", "👆"), ("Use a visual schedule", "📅"), ("Keep mornings predictable", "⏰")]
ROW_W = 860
for i, ((s, e), t0) in enumerate(zip(tips, tips_t)):
    content = row([badge(i + 1, 58, YEL, INK, 34), text(s, "Bold", 40, INK)], 18)
    content = row([content, emoji(e, 48)], ROW_W - content.width - 48 - 2 * 18 - 10)
    im = sh(pill(content, (255, 255, 255, 245), 18, 10, r=40), 12, 110)
    add(im, 540, 185 + i * 86, t0 - 0.06, t_tips_end + 0.05 * i, ain="slide_l", din=0.32, dist=300, aout="slide_l", dout=0.25)
    sfx(t0 - 0.06, "ding", -7, pitch=[1.0, 1.122, 1.26, 1.498][i])

# ---------------------------------------------------------------- GOAL / ENDING
t_ind, t_without = T("independently"), T("without")
add(headline([("THE GOAL:", "ExtraBold", 60, WHITE, 1), (row([text("INDEPENDENCE", "Black", 92, YEL, stroke=10, stroke_fill=INK), emoji("🌟", 84)], 8), 0, 0, 0, 0)]),
    540, 250, t_ind - 0.08, END_CARD, ain="pop", din=0.36, aout="fade", dout=0.2)
sfx(t_ind - 0.2, "whoosh", -7, dur=0.3)
sfx(t_ind - 0.02, "sparkle", -5)
PUNCH.append((t_ind - 0.08, 0.08))
add(sh(pill(row([emoji("✅", 46), text("No reminders needed", "SemiBold", 42, WHITE)], 12), INK, 30, 16), 12, 120),
    540, 420, t_without - 0.05, END_CARD, ain="slide_u", dist=180, aout="fade", dout=0.2)
sfx(t_without - 0.05, "pop", -8, pitch=0.9)

# ---------------------------------------------------------------- END CARD
E = END_CARD
add(sh(text("Found this helpful?", "SemiBold", 54, WHITE), 10, 120), 540, 700, E + 0.15, TOTAL + 1, ain="slide_u", dist=150, aout="none", layer=5)
add(sh(text("THE CUB", "Black", 150, YEL, stroke=10, stroke_fill=INK, tracking=6), 18, 140), 540, 860, E + 0.25, TOTAL + 1,
    ain="pop", din=0.4, aout="none", layer=5)
add(sh(pill(text("+ Follow for more", "Black", 52, WHITE), CORAL, 44, 22), 14, 130), 540, 1035, E + 0.5, TOTAL + 1,
    ain="pop", din=0.35, aout="none", pulse=(0.05, 1.6), layer=5)
add(sh(row([emoji("🔖", 46), text("Save this for your next school morning", "SemiBold", 36, WHITE)], 10), 10, 120),
    540, 1160, E + 0.75, TOTAL + 1, ain="slide_u", dist=150, aout="none", layer=5)
sfx(E, "whoosh", -6, dur=0.45)
sfx(E + 0.25, "thump", -8)
sfx(E + 0.5, "pop", -5, pitch=1.2)
sfx(E + 0.75, "sparkle", -8)
CAPTION_HIDE.append((E, TOTAL + 1))

for tc in TRANSITIONS:
    sfx(tc - 0.18, "whoosh", -5, dur=0.4)

CAPTIONS = Captions(WORDS, y=1350, hide=CAPTION_HIDE)
SPRITES.sort(key=lambda s: s.layer)

if __name__ == "__main__":
    print("speech end", SPEECH_END, "total", TOTAL, "transitions", [round(t, 2) for t in TRANSITIONS])
    print(len(SPRITES), "sprites", len(SFX), "sfx")
    for k, c in enumerate(CAPTIONS.chunks):
        print(f"{CAPTIONS.times[k][0]:6.2f}-{CAPTIONS.times[k][1]:6.2f}", " ".join(w["w"] for w in c))
