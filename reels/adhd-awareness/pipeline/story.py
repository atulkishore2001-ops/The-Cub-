# ADHD awareness reel: the animated story. Two doodle characters on one continuous stage; every line of the
# voiceover gets a matching action, expression and prop. Times are the voiceover's word times (seconds).
import json, math, os
import numpy as np
import doodle as D
import props as PR

VO_WORDS = json.load(open(os.environ["WORK"] + "/vo_words.json"))
FPS = 30
T_LAST = 80.95                              # end of the last word ("child.")
T_CREAM0 = T_LAST + 0.05
T_CREAM1 = T_CREAM0 + 1.0
T_END = T_CREAM0 + 4.3
GROUND = 1380
L_OFF, R_OFF = -260, 1340


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)


def eout(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3


def W(word, n=0):
    """Start time of the n-th occurrence of a spoken word."""
    hits = [w["s"] for w in VO_WORDS if w["w"].lower().strip(",.?!:;\"'") == word.lower()]
    return hits[n]


class Track:
    def __init__(self, **base):
        self.base = dict(D.BASE); self.base.update(base)
        self.keys = []

    def key(self, t, dur=0.45, **vals):
        self.keys.append((t, dur, vals))
        return self

    def at(self, t):
        st = dict(self.base)
        for kt, dur, vals in sorted(self.keys, key=lambda k: k[0]):
            if t < kt:
                break
            p = ease((t - kt) / dur) if dur > 0 else 1.0
            for k, v in vals.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool) and isinstance(st.get(k), (int, float)):
                    st[k] = st[k] + (v - st[k]) * p
                elif t >= kt + dur * 0.35 or dur == 0:
                    st[k] = v
        return st


BOY = Track(x=L_OFF, y=1380, R=105, alpha=1.0)
GIRL = Track(x=R_OFF, y=1380, R=105, alpha=1.0)
PROPS = []          # (t0, t1, fn(c, t, a))
TEXTS = []          # (t0, t1, parts) top text cards
SFX = []


def prop(t0, t1, fn, fin=0.35, fout=0.35):
    PROPS.append((t0, t1, fn, fin, fout))


def text(t0, t1, parts):
    TEXTS.append((t0, t1, parts))


def sfx(t, name, gain=-14, **kw):
    SFX.append(dict(t=t, name=name, gain=gain, **kw))


# ---------------------------------------------------------------- 1. "We hear about ADHD all the time, but do we really understand it?"
BOY.key(0.0, 0.0, x=540, alpha=0.0, bob=60).key(0.15, 0.6, alpha=1.0, bob=0)
t_hear, t_but, t_und = W("hear"), W("but"), W("understand")
BOY.key(0.9, 0.4, turn=-0.6, lookx=-1).key(1.6, 0.4, turn=0.6, lookx=1).key(2.3, 0.4, turn=-0.3, lookx=-0.5)
BOY.key(t_but - 0.1, 0.5, turn=0, lookx=0, ra1=150, ra2=75, tilt=-8, brows="raised", mouth="o", la1=18)
BOY.key(4.7, 0.5, mouth="flat")
for k, (tt, x, y) in enumerate(((0.8, 230, 760), (1.25, 850, 700), (1.75, 270, 1000), (2.2, 820, 980))):
    prop(tt, t_but + 0.2, lambda c, t, a, tt=tt, x=x, y=y, k=k: PR.bubble(c, x, y + 6 * math.sin(t * 2 + k), "ADHD", a,
                                                                       PR.pop((t - tt) / 0.35), tail=(1 if x < 540 else -1, 1), size=48))
    sfx(tt, "pop", -15, pitch=0.9 + 0.08 * k)
prop(t_und, 5.1, lambda c, t, a: PR.question(c, 600, 610 - 10 * math.sin(t * 3), a, PR.pop((t - t_und) / 0.35)))
sfx(t_und, "pop", -13)
text(t_but - 0.1, 5.0, [("Do we really ", "n"), ("understand", "pf"), (" ADHD?", "n")])

# ---------------------------------------------------------------- 2. "Hey, this is Saanchi, RCI-certified special educator..."
t_hey = W("hey")
BOY.key(t_hey - 0.4, 0.6, ra1=25, ra2=0, tilt=0, brows=None, mouth="smile", la1=25)
BOY.key(t_hey - 0.2, 1.0, x=330)
GIRL.key(t_hey - 0.3, 1.1, x=760)
GIRL.key(t_hey + 0.8, 0.35, ra1=150, ra2=-20).key(t_hey + 1.15, 0.3, ra2=20).key(t_hey + 1.45, 0.3, ra2=-20).key(t_hey + 1.75, 0.3, ra2=20)
GIRL.key(t_hey + 2.05, 0.4, ra1=25, ra2=0)
BOY.key(t_hey + 1.0, 0.4, la1=150, la2=-15).key(t_hey + 1.4, 0.3, la2=15).key(t_hey + 1.7, 0.3, la2=-15).key(t_hey + 2.0, 0.4, la1=25, la2=0)
t_talk = W("talk")
GIRL.key(t_talk - 0.2, 0.4, mouth="big", eyes="happy")
BOY.key(t_talk - 0.2, 0.4, mouth="big", eyes="happy")
text(t_hey, t_talk + 0.9, "NAME")
sfx(t_hey, "slide", -16)

# ---------------------------------------------------------------- 3. "It's not just being distracted."
t_not = W("not")
GIRL.key(t_not - 0.9, 0.9, x=R_OFF, mouth="smile", eyes="open")
BOY.key(t_not - 0.9, 0.8, x=540, mouth="smile", eyes="open")
BF0 = t_not - 0.3


def bf_pos(t):
    u = t - BF0
    return 540 + 230 * math.sin(u * 1.6), 640 + 70 * math.sin(u * 3.1)


prop(BF0, W("knowing") + 0.3, lambda c, t, a: PR.butterfly(c, *bf_pos(t), t, a, 1.35))
for k in range(8):
    tt = BF0 + 0.25 + k * 0.32
    bx = 540 + 230 * math.sin((tt + 0.2 - BF0) * 1.6)
    BOY.key(tt, 0.3, lookx=clamp((bx - 540) / 230, -1, 1), turn=clamp((bx - 540) / 300, -0.7, 0.7), tilt=-(bx - 540) / 40)
text(t_not, W("knowing") - 0.1, [("Not ", "n"), ("just", "pf"), (" being distracted", "n")])

T_TB = W("blindness") - 0.32                # "It's time blindness"

# ---------------------------------------------------------------- 4. "knowing exactly what you need to do and still not being able to start"
t_know, t_still, t_start = W("knowing"), W("still"), W("start")
BOY.key(t_know - 0.2, 0.5, x=650, lookx=0, turn=0, tilt=0)
prop(t_know - 0.3, T_TB - 0.4, lambda c, t, a: PR.desk(c, 300, GROUND, a))
PEN = lambda t: (0, 0)
prop(t_know + 0.2, T_TB - 0.4, lambda c, t, a: (PR.thought(c, 640, 560, 300, 200, a, PR.pop((t - t_know - 0.2) / 0.4), src=(650, 720)),
                                                     PR.checklist(c, 640, 560, a * clamp((t - t_know - 0.4) / 0.3), 3 if t > t_know + 1.4 else int((t - t_know) / 0.45))))
BOY.key(t_know + 0.2, 0.4, brows="raised", mouth="smile", eyes="open", looky=-1)
# reaches for the pencil, stops, pulls back (twice)
for k in range(2):
    t0 = t_still + k * 0.9
    BOY.key(t0, 0.35, la1=65, la2=10, lean=-6, looky=0.6, lookx=-1, brows="worried", mouth="wavy")
    BOY.key(t0 + 0.45, 0.35, la1=25, la2=0, lean=0)
prop(t_know - 0.3, T_TB - 0.4, lambda c, t, a: PR.pencil(c, 330, GROUND - 312, -8, a))
BOY.key(t_start + 0.2, 0.4, mouth="frown", brows="worried")
prop(t_start, T_TB - 0.3, lambda c, t, a: PR.sweat(c, 740, 610, a, 1.2))
text(t_know, T_TB - 0.4, [("Knows what to do… ", "n"), ("can’t start", "pf")])
sfx(t_know + 0.2, "pop", -15); sfx(t_still, "tick", -16)

# ---------------------------------------------------------------- 5. "It's time blindness. Five minutes feels like an hour..."
t_time, t_five, t_hour2 = T_TB, W("five"), W("hour", 1)
BOY.key(t_time - 0.6, 0.9, x=L_OFF, mouth="smile", brows=None)
GIRL.key(t_time - 0.6, 0.9, x=430, mouth="smile", eyes="open")
CX, CY, CR = 790, 860, 150


def clock_hands(t):
    if t < t_five:
        return 300, 0
    if t < t_hour2 - 0.3:                                # crawling
        m = (t - t_five) * 6
        return 300 + m / 12, m
    m0 = (t_hour2 - 0.3 - t_five) * 6
    u = t - (t_hour2 - 0.3)
    m = m0 + 1440 * eout(u / 2.0)                        # whizzing round
    return 300 + m / 12, m


prop(t_time - 0.3, W("mind") - 0.4, lambda c, t, a: PR.clock(c, CX, CY, CR, *clock_hands(t), a,
                                                            spin_lines=clamp((t - t_hour2 + 0.3) / 0.3) * clamp((t_hour2 + 1.8 - t) / 0.4)))
GIRL.key(t_five, 0.5, la1=70, la2=105, ra1=70, ra2=105, eyes="open", blink=0.45, mouth="flat", turn=0.4, lookx=1)
for k in range(5):                                       # foot tap
    GIRL.key(t_five + 0.3 + k * 0.4, 0.15, rl=14).key(t_five + 0.5 + k * 0.4, 0.15, rl=4)
GIRL.key(t_hour2 - 0.3, 0.35, blink=0.0, eyes="wide", mouth="o", la1=140, ra1=140, la2=-10, ra2=-10, bob=-10, lean=-4)
GIRL.key(t_hour2 + 1.4, 0.5, bob=0, la1=25, ra1=25, la2=0, ra2=0, lean=0, eyes="open", mouth="o", turn=0, lookx=0)
text(t_time, W("mind") - 0.4, [("Time ", "n"), ("blindness", "pf")])
sfx(t_hour2 - 0.3, "whoosh", -15, dur=1.2)

# ---------------------------------------------------------------- 6. "It's a mind with ten tabs open, and no way to close them."
t_mind, t_ten, t_close = W("mind"), W("ten"), W("close")
GIRL.key(t_mind - 0.4, 0.6, x=540, mouth="flat", brows="worried", eyes="open")
TABS = [(-150, -60, -8), (40, -95, 6), (170, -40, -5), (-60, 10, 4), (120, 40, 10), (-170, 60, -12), (10, 85, -3), (180, 110, 8),
        (-90, 125, 7), (70, 150, -6)]


def tabs_fn(c, t, a):
    PR.thought(c, 560, 470, 520, 360, a, PR.pop((t - t_mind) / 0.4), src=(560, 720))
    for k, (dx, dy, rot) in enumerate(TABS):
        tk = t_ten - 0.2 + k * 0.14
        p = PR.pop((t - tk) / 0.25)
        if t > t_close and k == 4:                         # tries to close one ... it pops straight back
            u = t - t_close
            p *= 1 - 0.85 * math.sin(clamp(u / 0.5) * math.pi)
        if p > 0:
            PR.tab(c, 560 + dx * 1.0, 470 + dy * 0.9, 150 * p, 95 * p, a, rot + 4 * math.sin(t * 2 + k))


prop(t_mind, W("forgetting") - 0.3, tabs_fn)
GIRL.key(t_ten, 0.4, la1=150, la2=75, ra1=150, ra2=75, mouth="wavy", eyes="wide", brows="worried")
GIRL.key(t_close - 0.1, 0.25, ra1=120, ra2=0, la1=150, la2=75).key(t_close + 0.4, 0.3, ra1=150, ra2=75)
for k in range(10):
    sfx(t_ten - 0.2 + k * 0.14, "tick", -18, pitch=0.9 + 0.03 * k)
text(t_mind, W("forgetting") - 0.3, [("10 tabs open, ", "n"), ("none close", "pf")])

# ---------------------------------------------------------------- 7. "It's forgetting your homework even after you've finished it."
t_forg, t_even, t_fin = W("forgetting"), W("even"), W("finished")
GIRL.key(t_forg - 0.5, 0.9, x=R_OFF, la1=25, ra1=25, la2=0, ra2=0, mouth="smile", brows=None)
BOY.key(t_forg - 0.5, 0.9, x=540, mouth="smile", brows=None, eyes="open", la1=25, ra1=25)
BOY.key(t_forg + 0.3, 0.4, ra1=55, ra2=60, eyes="happy", mouth="big")


def nb_fn(c, t, a):
    hx, hy = D.hand_pos("boy", BOY.at(t), 1)
    if t < t_fin + 0.15:
        PR.notebook(c, hx + 40, hy - 50, a, -8, clamp((t - t_forg - 0.5) / 0.4), 0.9)
    PR.poof(c, hx + 40, hy - 50, (t - t_fin - 0.15) / 0.5, a)


prop(t_forg + 0.2, W("told") - 0.45, nb_fn)
BOY.key(t_fin + 0.2, 0.3, ra1=25, ra2=0, eyes="wide", mouth="o", brows="worried")
BOY.key(t_fin + 0.6, 0.3, la1=40, ra1=40, la2=40, ra2=40, turn=-0.7, lookx=-1).key(t_fin + 1.0, 0.3, turn=0.7, lookx=1)
prop(t_fin + 0.5, W("told") - 0.45, lambda c, t, a: PR.sweat(c, 650, 600, a, 1.2))
prop(t_fin + 0.4, W("told") - 0.45, lambda c, t, a: PR.question(c, 690, 620 - 8 * math.sin(t * 3), a, 0.6 * PR.pop((t - t_fin - 0.4) / 0.3)))
text(t_forg, W("told") - 0.45, [("Forgets homework… ", "n"), ("after finishing it", "pf")])
sfx(t_fin + 0.15, "pop", -14); sfx(t_forg + 0.4, "check", -16)

# ---------------------------------------------------------------- 8. "It's being told 'sit still', 'pay attention', 'stop daydreaming' ..."
t_sit, t_pay, t_stop, t_when, t_twice = W("sit"), W("pay"), W("stop"), W("when"), W("twice")
BOY.key(W("told") - 0.4, 0.4, turn=0, lookx=0, la1=25, ra1=25, la2=0, ra2=0, mouth="flat", brows=None, eyes="open")
for k in range(10):                                      # fidgeting: sways and bounces a knee
    tt = W("told") - 0.3 + k * 0.42
    BOY.key(tt, 0.2, lean=3 * (1 if k % 2 else -1), lk=12 if k % 2 else 0)
for tt, x, y, s in ((t_sit, 270, 760, "Sit still!"), (t_pay, 810, 690, "Pay attention!"), (t_stop, 300, 560, "Stop daydreaming!")):
    prop(tt - 0.1, t_when + 0.1, lambda c, t, a, tt=tt, x=x, y=y, s=s: PR.bubble(c, x, y, s, a, PR.pop((t - tt + 0.1) / 0.3),
                                                                             tail=(1 if x < 540 else -1, 1), size=44,
                                                                             fill=(0.17, 0.17, 0.17), tcol=(253, 246, 238)))
    BOY.key(tt, 0.15, eyes="wide", lean=-5, bob=6).key(tt + 0.25, 0.3, bob=0, lean=0)
    sfx(tt - 0.1, "pop", -13)
BOY.key(t_when, 0.4, eyes="open", brows="worried", mouth="wavy", lk=0, lean=0)


def brain_fn(c, t, a):
    hx, hy, R = D.head_pos("boy", BOY.at(t))
    p = PR.pop((t - t_when) / 0.4)
    PR.thought(c, 540, 480, 330, 230, a, p, src=(540, 700))
    speed = 260 if t > t_twice else 120
    PR.gear(c, 500, 480, 62 * p, t * speed, a)
    PR.gear(c, 605, 450, 42 * p, -t * speed * 1.5, a, (0.17, 0.17, 0.17))
    PR.gear(c, 600, 535, 30 * p, t * speed * 2, a)
    PR.sweat(c, hx + R * 1.05, hy - R * 0.3 + 30 * ((t * 1.3) % 1), a * clamp((t - t_twice) / 0.3), 1.1)


prop(t_when, W("big") - 0.3, brain_fn)
text(t_when, W("big") - 0.3, [("Working ", "n"), ("twice as hard", "pf")])
sfx(t_when, "pop", -15)

# ---------------------------------------------------------------- 9. "It's big emotions that arrive fast and leave slowly..."
t_big, t_arr, t_leave, t_lazy, t_believe = W("big"), W("arrive"), W("leave"), W("lazy"), W("believing")
BOY.key(t_big - 0.6, 0.9, x=L_OFF, mouth="smile", brows=None)
GIRL.key(t_big - 0.6, 0.9, x=540, mouth="smile", brows=None, la1=25, ra1=25, la2=0, ra2=0, eyes="open")


def storm(c, t, a):
    # arrives fast, leaves slowly
    if t < t_leave:
        x = 1300 - (1300 - 560) * eout((t - t_arr + 0.25) / 0.45)
    else:
        x = 560 - 900 * ease((t - t_leave) / 2.4)
    PR.cloud(c, x, 520, 1.1, a, dark=True, bolt=1.0 if (t_arr < t < t_leave and int(t * 5) % 3 == 0) else 0.0)


prop(t_arr - 0.3, t_lazy - 0.3, storm, fin=0.1, fout=0.4)
GIRL.key(t_arr + 0.1, 0.25, brows="angry", mouth="frown", eyes="open", la1=50, ra1=50, la2=60, ra2=60, bob=4)
GIRL.key(t_leave + 0.4, 1.6, brows="worried", mouth="flat", la1=25, ra1=25, la2=0, ra2=0, bob=0)
sfx(t_arr - 0.25, "whoosh", -14, dur=0.4)
LAZY = [(250, 640, -8), (820, 720, 6), (300, 980, 5), (800, 1010, -6), (560, 560, 0)]
for k, (x, y, r) in enumerate(LAZY):
    tt = t_lazy - 0.1 + k * 0.22
    prop(tt, W("but", 1) - 0.1, lambda c, t, a, tt=tt, x=x, y=y, r=r: PR.draw_text(c, "“Lazy”", x, y, a * clamp((t - tt) / 0.2),
                                                                             PR.pop((t - tt) / 0.3), r, fam="dm", wt=800, size=58,
                                                                             col=(120, 120, 120)), fout=0.5)
    sfx(tt, "tick", -16)
GIRL.key(t_lazy, 0.6, scale=0.94, tilt=8, looky=1, mouth="frown", brows="worried", la1=8, ra1=8)
prop(t_believe, W("but", 1) - 0.1, lambda c, t, a: PR.tag(c, 545, 1000, "lazy", a, -8, PR.pop((t - t_believe) / 0.35)))
sfx(t_believe, "plop", -14)
text(t_big, t_lazy - 0.3, [("Big emotions: ", "n"), ("fast in, slow out", "pf")])
text(t_lazy - 0.2, W("but", 1) - 0.1, [("They start ", "n"), ("believing it", "pf")])

# ---------------------------------------------------------------- 10. "But there's a part of ADHD which we often ignore."
t_but2, t_ign = W("but", 1), W("ignore")
GIRL.key(t_but2, 0.8, scale=1.0, tilt=0, looky=-1, mouth="smile", brows="raised", la1=25, ra1=25)
GIRL.key(t_but2 + 0.4, 0.8, x=760)
BOY.key(t_but2 + 0.4, 0.9, x=330, mouth="smile", brows="raised", looky=-1, eyes="open")
GLOW = (t_but2, T_CREAM0)
text(t_but2 + 0.1, W("curious") - 0.3, [("The part we often ", "n"), ("ignore", "pf")])
sfx(t_but2, "chime", -18)

# ---------------------------------------------------------------- 11. "curious, creative and full of energy"
t_cur, t_cre, t_full = W("curious"), W("creative"), W("full")
BOY.key(t_cur - 0.4, 0.4, looky=0.6, lookx=-0.5, ra1=70, ra2=-20, brows="raised", mouth="o", lean=-6)
prop(t_cur - 0.4, W("ADHD", 3) - 0.3, lambda c, t, a: PR.flower(c, 190, GROUND, 1.0, a, (0.95, 0.75, 0.3)))
prop(t_cur - 0.4, t_full, lambda c, t, a: PR.magnifier(c, *[v for v in D.hand_pos("boy", BOY.at(t), 1)], a, -40))
STROKES = [[(640 + i * 9, 640 + 40 * math.sin(i / 5)) for i in range(40)], [(660 + i * 9, 720 + 30 * math.cos(i / 4)) for i in range(36)],
           [(700 + 80 * math.cos(i / 6), 560 + 50 * math.sin(i / 6)) for i in range(38)]]
for k, (pts, col) in enumerate(zip(STROKES, ((0.94, 0.52, 0.24), (0.36, 0.62, 0.86), (0.55, 0.78, 0.4)))):
    tk = t_cre - 0.1 + k * 0.35
    prop(tk, W("ADHD", 3) - 0.3, lambda c, t, a, pts=pts, tk=tk, col=col: PR.scribble(c, pts, (t - tk) / 0.5, a, col, 12))
GIRL.key(t_cre - 0.2, 0.3, la1=25, ra1=120, ra2=-30, mouth="big", eyes="happy", brows=None, looky=-1, lookx=-1)
GIRL.key(t_cre + 0.3, 0.3, ra1=150, ra2=10).key(t_cre + 0.6, 0.3, ra1=110, ra2=-30)
for who in (BOY, GIRL):                                   # full of energy: jump twice
    who.key(t_full - 0.1, 0.2, la1=150, ra1=150, la2=-10, ra2=-10, mouth="big", eyes="happy", brows=None, lean=0, looky=0, lookx=0)
    for k in range(2):
        tt = t_full + k * 0.6
        who.key(tt, 0.25, bob=-70, sq=0.94, lk=20, rk=20).key(tt + 0.27, 0.25, bob=0, sq=1.05, lk=0, rk=0).key(tt + 0.5, 0.1, sq=1.0)
for k in range(5):
    tt = t_full + 0.1 + k * 0.12
    x, y = (240, 520, 600, 860, 940)[k], (700, 560, 520, 600, 760)[k]
    prop(tt, W("ADHD", 3) - 0.3, lambda c, t, a, tt=tt, x=x, y=y: PR.star(c, x, y, 26 * PR.pop((t - tt) / 0.3), a, t * 40))
text(t_cur, W("ADHD", 3) - 0.3, "CCE")
sfx(t_cur, "pop", -15); sfx(t_cre, "pop", -15, pitch=1.1); sfx(t_full, "pop", -15, pitch=1.2)

# ---------------------------------------------------------------- 12. "And with the right support, they thrive."
t_sup, t_thr = W("support"), W("thrive")
for who in (BOY, GIRL):
    who.key(t_sup - 0.5, 0.4, la1=25, ra1=25, la2=0, ra2=0, mouth="smile", eyes="open")
BOY.key(t_sup - 0.5, 0.4, looky=0.5, lookx=1); GIRL.key(t_sup - 0.5, 0.4, looky=0.5, lookx=-1)
prop(t_sup - 0.4, W("ADHD", 3) - 0.3, lambda c, t, a: PR.flower(c, 545, GROUND, eout((t - t_sup + 0.4) / 1.8), a))
text(t_sup - 0.2, W("ADHD", 3) - 0.3, [("With the right support, they ", "n"), ("thrive", "pf")])

# ---------------------------------------------------------------- 13. "ADHD isn't a flaw to fix. It's a brain that needs a different map."
t_flaw, t_map, t_diff = W("flaw"), W("map"), W("different")
for who in (BOY, GIRL):
    who.key(W("ADHD", 3) - 0.2, 0.4, looky=0, lookx=0)
BOY.key(t_map - 1.0, 0.5, ra1=80, ra2=-10)
GIRL.key(t_map - 1.0, 0.5, la1=80, la2=-10)
prop(t_map - 1.2, W("give") + 2.5, lambda c, t, a: PR.map_scroll(c, 545, 880, 300, 220, eout((t - t_map + 1.2) / 0.9), a,
                                                                    clamp((t - t_map + 0.2) / 1.2)))
text(W("ADHD", 3) - 0.1, t_map - 1.2, "FLAW")
text(t_map - 1.2, W("give") - 0.2, [("A brain that needs a ", "n"), ("different map", "pf")])
sfx(t_map - 1.2, "slide", -16)

# ---------------------------------------------------------------- 14. "Give them the map and watch them fly."
t_give, t_fly = W("give"), W("fly")
for who, x in ((BOY, 360), (GIRL, 730)):
    who.key(t_give, 0.4, mouth="big", eyes="happy")
    who.key(t_fly - 0.3, 0.6, bob=-260, la1=110, ra1=110, la2=0, ra2=0, lk=25, rk=25, lean=-6)
    who.key(t_fly + 1.0, 0.7, bob=0, lk=0, rk=0, lean=0, la1=25, ra1=25)
prop(t_fly - 0.4, t_fly + 1.6, lambda c, t, a: (PR.cloud(c, 1200 - 260 * (t - t_fly), 520, 0.7, a), PR.cloud(c, 200 - 180 * (t - t_fly), 760, 0.55, a),
                                                PR.plane(c, -100 + 900 * eout((t - t_fly + 0.4) / 1.6), 600 - 120 * (t - t_fly), a)))
text(t_give, W("next") - 0.3, [("Give them the map… watch them ", "n"), ("fly", "pf")])
sfx(t_fly - 0.3, "whoosh", -15, dur=0.8)

# ---------------------------------------------------------------- 15. "So next time you see a child who just can't focus,"
t_next, t_focus = W("next"), W("focus")
BOY.key(t_next, 0.4, mouth="flat", eyes="open")
for k in range(6):                                       # restless, eyes darting
    tt = t_next + 0.2 + k * 0.4
    BOY.key(tt, 0.2, turn=0.6 * (1 if k % 2 else -1), lookx=1 if k % 2 else -1, lean=2 * (1 if k % 2 else -1))
GIRL.key(t_next, 0.5, mouth="smile", eyes="open", turn=-0.5, lookx=-1)

# ---------------------------------------------------------------- 16/17. "don't ask 'What's wrong with you?' Ask 'What do you need?'"
t_dont, t_ask2, t_need = W("don't"), W("ask", 1), W("need", 1)
BOY.key(t_dont, 0.3, turn=0.3, lookx=1, lean=0, mouth="frown", brows="worried")


def wrong_fn(c, t, a):
    PR.bubble(c, 610, 640, "What’s wrong with you?", a, PR.pop((t - t_dont) / 0.3), tail=(1, 1), size=44)
    p = clamp((t - (t_dont + 1.1)) / 0.35)
    if p > 0:
        c.move_to(330, 640); c.line_to(330 + 560 * p, 640); D._stroke(c, 12, a, D.ORANGE)


prop(t_dont, t_ask2 - 0.05, wrong_fn, fout=0.25)
sfx(t_dont, "pop", -14); sfx(t_dont + 1.1, "scratch", -16)
GIRL.key(t_dont + 0.8, 0.3, tilt=-6).key(t_dont + 1.1, 0.3, tilt=6).key(t_dont + 1.4, 0.3, tilt=0)
prop(t_ask2, W("because") + 0.2, lambda c, t, a: PR.bubble(c, 700, 640, "What do you need?", a, PR.pop((t - t_ask2) / 0.3), tail=(1, 1),
                                                           size=48, fill=D.ORANGE, tcol=(255, 255, 255)), fout=0.3)
GIRL.key(t_ask2, 0.5, x=650, la1=75, la2=-10, lean=-6, mouth="smile", eyes="open", turn=-0.4, lookx=-1)
BOY.key(t_need, 0.5, mouth="big", eyes="happy", brows=None, turn=0.3, lookx=1, ra1=70, ra2=-10)
sfx(t_ask2, "pop", -13, pitch=1.15)

# ---------------------------------------------------------------- 18. "Because that one question can change everything for a child."
t_bec, t_change = W("because"), W("change")
GIRL.key(t_bec + 0.2, 0.5, x=720, lean=0, la1=25, la2=0, turn=0, lookx=0)
BOY.key(t_bec + 0.2, 0.5, x=380, ra1=25, ra2=0, turn=0, lookx=0)
for who in (BOY, GIRL):                                    # the reference pose: both arms up, happy
    who.key(t_change - 0.2, 0.5, la1=150, ra1=150, la2=-12, ra2=-12, mouth="big", eyes="happy", brows=None, blush=1.0)
    for k in range(3):
        tt = t_change + k * 0.55
        who.key(tt, 0.25, bob=-30, sq=0.97).key(tt + 0.27, 0.25, bob=0, sq=1.0)
for k in range(9):
    tt = t_change + 0.1 + k * 0.15
    x = 160 + k * 95
    prop(tt, T_CREAM0 + 0.3, lambda c, t, a, tt=tt, x=x, k=k: (PR.heart if k % 2 else PR.star)(
        c, x, 560 + 60 * math.sin(k * 1.7) - 30 * (t - tt), *((0.8 * PR.pop((t - tt) / 0.3), a) if k % 2 else (24 * PR.pop((t - tt) / 0.3), a))))
text(t_bec, T_CREAM0, [("One question can ", "n"), ("change everything", "pf")])
sfx(t_change, "chime", -16)


# ---------------------------------------------------------------- per-frame state with idle life (breathing, sway, blinks, walking)
def _idle(name, st, t):
    off = 0.0 if name == "boy" else 1.7
    st["bob"] += 2.2 * math.sin(2 * math.pi * t / 3.1 + off)
    st["lean"] += 0.8 * math.sin(2 * math.pi * t / 4.3 + off)
    st["la1"] += 2.0 * math.sin(2 * math.pi * t / 2.9 + off)
    st["ra1"] += 2.0 * math.sin(2 * math.pi * t / 3.3 + off + 1)
    ph = (t + off * 1.3) % 3.4
    st["blink"] = max(st["blink"], clamp(1 - abs(ph - 0.08) / 0.08)) if st["eyes"] in ("open", "wide") else st["blink"]


def pose(name, t):
    tr = BOY if name == "boy" else GIRL
    st = tr.at(t)
    x0, x1 = tr.at(t - 0.05)["x"], tr.at(t + 0.05)["x"]
    v = (x1 - x0) / 0.1
    if abs(v) > 40:                                         # walking: legs, arms and a little bob, driven by distance
        ph = st["x"] / (st["R"] * 0.9)
        k = clamp((abs(v) - 40) / 200)
        st["ll"] += 22 * k * math.sin(ph); st["rl"] -= 22 * k * math.sin(ph)
        st["lk"] += 10 * k * max(0, math.sin(ph)); st["rk"] += 10 * k * max(0, -math.sin(ph))
        st["la1"] += 14 * k * math.sin(ph); st["ra1"] -= 14 * k * math.sin(ph)
        st["bob"] -= 7 * k * abs(math.sin(ph))
        st["lean"] += 3 * k * (1 if v > 0 else -1)
        st["flip"] = 1
    _idle(name, st, t)
    return st


# ponytail: a damped spring driven by the girl's motion, simulated once for the whole reel
_N = int(T_END * FPS) + 2
PONY = np.zeros(_N)
_a, _v = 0.0, 0.0
_prev = None
for n in range(_N):
    t = n / FPS
    g = GIRL.at(t)
    cur = (g["x"], g["bob"], g["lean"])
    if _prev is None:
        _prev = cur
    acc_x = (cur[0] - _prev[0]) * FPS
    acc_y = (cur[1] - _prev[1]) * FPS
    target = -0.05 * acc_x + 0.06 * acc_y - 1.5 * cur[2]
    _v += (clamp(target, -40, 40) - _a) * 0.08 - _v * 0.18
    _a += _v
    PONY[n] = _a + 3 * math.sin(t * 1.9)
    _prev = cur


def girl_pose(t):
    st = pose("girl", t)
    st["pony"] = PONY[min(_N - 1, int(t * FPS))]
    return st


def glow(t):
    return ease((t - GLOW[0]) / 1.2) * (1 - ease((t - T_CREAM0) / 0.5))


def cream_alpha(t):
    return ease((t - T_CREAM0) / (T_CREAM1 - T_CREAM0))
