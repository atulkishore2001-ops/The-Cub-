# Simple, calm vector illustrations for the World Stroke Day reel (drawn in code, supersampled).
# Line-icon style: charcoal strokes, brand-orange accents, muted grey for "lost" states. No gore, no alarm red.
import math
from PIL import Image, ImageDraw, ImageFilter
import gfx2 as G

SS = 3
CHAR = (43, 43, 43, 255)
ORANGE = (240, 133, 62, 255)
BLOOD = (214, 84, 52, 255)          # a deeper brand orange-red for blood
GREY = (190, 186, 180, 255)
LIGHT = (240, 232, 222, 255)
WHITE = (255, 255, 255, 255)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(p):
    p = clamp(p)
    return 3 * p * p - 2 * p * p * p


def eout(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3


class Cv:
    """Draw at SSx resolution in logical units, return a smooth RGBA image."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def P(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def line(self, pts, fill=CHAR, width=8, joint="curve"):
        self.d.line(self.P(pts), fill=fill, width=int(width * SS), joint=joint)
        r = width * SS / 2
        for x, y in (pts[0], pts[-1]):
            self.d.ellipse((x * SS - r, y * SS - r, x * SS + r, y * SS + r), fill=fill)

    def circle(self, cx, cy, r, fill=None, outline=None, width=8):
        self.d.ellipse(((cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS), fill=fill, outline=outline,
                       width=int(width * SS) if outline else 0)

    def poly(self, pts, fill=None, outline=None, width=8):
        self.d.polygon(self.P(pts), fill=fill)
        if outline:
            self.line(list(pts) + [pts[0]], outline, width)

    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, width=8):
        self.d.rounded_rectangle((x0 * SS, y0 * SS, x1 * SS, y1 * SS), int(r * SS), fill=fill, outline=outline,
                                 width=int(width * SS) if outline else 0)

    def arc(self, cx, cy, r, a0, a1, fill=CHAR, width=8):
        self.d.arc(((cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS), a0, a1, fill=fill, width=int(width * SS))

    def text(self, xy, s, size, fill=CHAR, fam="dm", wt=800, anchor="mm"):
        f = G.font(fam, wt, size * SS)
        self.d.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=fill, anchor=anchor)

    def img(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)


def bez(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def along(path, s):
    """Point at fraction s (0..1) of a polyline's length."""
    L = [0.0]
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        L.append(L[-1] + math.hypot(x1 - x0, y1 - y0))
    target = s * L[-1]
    for i in range(1, len(L)):
        if L[i] >= target:
            k = (target - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
            (x0, y0), (x1, y1) = path[i - 1], path[i]
            return x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    return path[-1]


def sub(path, s0, s1, n=30):
    return [along(path, s0 + (s1 - s0) * i / n) for i in range(n + 1)]


# ---------------------------------------------------------------- brain + vessels (what is a stroke)
BW, BH = 400, 340
_LOBES = [(150, 150, 95), (235, 130, 100), (300, 175, 78), (110, 205, 72), (200, 215, 90), (275, 230, 62)]
_V_MAIN = bez((205, 330), (200, 290), (195, 260), (200, 225))
_V_A = bez((200, 225), (180, 190), (140, 170), (100, 160))      # left branch: gets blocked
_V_B = bez((200, 225), (225, 185), (265, 160), (310, 150))      # right branch: bursts
_V_C = bez((200, 225), (200, 180), (210, 130), (225, 85))       # top branch: stays healthy
_CELLS_A = [(90, 125), (118, 108), (70, 170), (122, 140), (95, 200), (140, 120), (75, 140), (110, 225)]
_CELLS_B = [(300, 120), (330, 165), (278, 125), (318, 205), (345, 135), (290, 190)]


def _brain_mask():
    m = Image.new("L", (BW * SS, BH * SS), 0)
    d = ImageDraw.Draw(m)
    for cx, cy, r in _LOBES:
        d.ellipse(((cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS), fill=255)
    return m


_BMASK = _brain_mask()


def brain(t, t_block, t_burst, t_cells):
    """Side-view brain with three vessels. Blood flows; at t_block a clot stops the left branch, at t_burst the right
    branch leaks; from t_cells the starved areas fade from healthy to grey."""
    c = Cv(BW, BH)
    # brain body
    body = Image.new("RGBA", (BW * SS, BH * SS), LIGHT)
    c.im.paste(body, (0, 0), _BMASK)
    edge = _BMASK.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(15))
    c.im.paste(Image.new("RGBA", c.im.size, CHAR), (0, 0), edge)
    # gentle folds
    for pts in (bez((120, 95), (150, 120), (130, 150), (160, 170)), bez((230, 60), (215, 95), (250, 110), (235, 140)),
                bez((290, 120), (270, 150), (300, 170), (285, 200)), bez((150, 240), (175, 215), (200, 255), (230, 235)),
                bez((80, 190), (100, 175), (90, 215), (120, 215))):
        c.line(pts, (43, 43, 43, 90), 5)
    lost = clamp((t - t_cells) / 2.5)
    # cells in the two at-risk areas fade to grey once starved
    for (x, y) in _CELLS_A:
        k = lost if t > t_block else 0
        col = tuple(int(ORANGE[i] * (1 - k) + GREY[i] * k) for i in range(3)) + (255,)
        c.circle(x, y, 8, fill=col)
    for (x, y) in _CELLS_B:
        k = lost if t > t_burst else 0
        col = tuple(int(ORANGE[i] * (1 - k) + GREY[i] * k) for i in range(3)) + (255,)
        c.circle(x, y, 8, fill=col)
    # vessels
    for v in (_V_MAIN, _V_C, _V_A, _V_B):
        c.line(v, BLOOD, 13)
    blocked = eout((t - t_block) / 0.5)
    if blocked > 0:                                     # clot plug, beyond it the vessel drains to grey
        x, y = along(_V_A, 0.45)
        c.line(sub(_V_A, 0.48, 1.0), GREY, 13)
        c.circle(x, y, 13 * blocked + 2, fill=CHAR)
    burst = eout((t - t_burst) / 0.7)
    if burst > 0:                                       # a small leak spreading from the right branch
        x, y = along(_V_B, 0.55)
        c.line(sub(_V_B, 0.58, 1.0), GREY, 13)
        for k, (dx, dy, r) in enumerate(((0, 0, 26), (18, -14, 16), (-14, 16, 14), (22, 14, 12))):
            c.circle(x + dx * burst, y + dy * burst, r * burst, fill=(214, 84, 52, 200))
        c.circle(x, y, 7, fill=WHITE)
    # flowing blood dots
    for v, stop, alive in ((_V_MAIN, 1.0, True), (_V_C, 1.0, True), (_V_A, 0.42 if blocked > 0 else 1.0, True),
                           (_V_B, 0.55 if burst > 0 else 1.0, True)):
        for k in range(6):
            s = ((t * 0.55 + k / 6) % 1.0)
            if s <= stop:
                x, y = along(v, s)
                c.circle(x, y, 3.5, fill=(255, 235, 220, 255))
    return c.img()


# ---------------------------------------------------------------- risk-factor icons (120 x 120)
def ic_bp(p=1.0):
    c = Cv(120, 120)
    c.arc(60, 68, 44, 180, 360, CHAR, 8)
    for a in (200, 240, 270, 300, 340):
        r = math.radians(a)
        c.line([(60 + 34 * math.cos(r), 68 + 34 * math.sin(r)), (60 + 42 * math.cos(r), 68 + 42 * math.sin(r))], CHAR, 4)
    a = math.radians(200 + 130 * eout(p))
    c.line([(60, 68), (60 + 34 * math.cos(a), 68 + 34 * math.sin(a))], ORANGE, 8)
    c.circle(60, 68, 8, fill=CHAR)
    c.rrect(30, 84, 90, 100, 6, fill=CHAR)
    return c.img()


def ic_diabetes(p=1.0):
    c = Cv(120, 120)
    pts = [(60, 14)] + bez((60, 14), (95, 58), (100, 78), (60, 106))[1:] + bez((60, 106), (20, 78), (25, 58), (60, 14))[1:]
    c.poly(pts, fill=(214, 84, 52, 255))
    c.text((60, 72), "+", 46, WHITE)
    return c.img()


def ic_smoking(p=1.0):
    c = Cv(120, 120)
    c.rrect(10, 66, 92, 84, 4, fill=WHITE, outline=CHAR, width=5)
    c.rrect(70, 66, 92, 84, 3, fill=ORANGE)
    for k in range(2):
        x = 100 + k * 9
        c.line(bez((x, 62), (x - 8, 50), (x + 8, 40), (x, 26), 20), (43, 43, 43, 150), 4)
    return c.img()


def ic_stress(p=1.0):
    c = Cv(120, 120)
    c.circle(60, 66, 36, outline=CHAR, width=7)
    c.line([(46, 58), (54, 62)], CHAR, 5); c.line([(74, 58), (66, 62)], CHAR, 5)
    c.line([(48, 82), (56, 78), (64, 82), (72, 78)], CHAR, 5)
    for k, (x, y) in enumerate(((22, 22), (60, 10), (98, 22))):
        c.line([(x - 6, y + 4), (x, y - 4), (x + 4, y + 2), (x + 10, y - 6)], ORANGE, 5)
    return c.img()


def ic_check(size=120):
    c = Cv(size, size)
    c.circle(size / 2, size / 2, size / 2 - 4, fill=ORANGE)
    s = size / 120
    c.line([(36 * s, 62 * s), (53 * s, 79 * s), (86 * s, 44 * s)], WHITE, 11 * s)
    return c.img()


# ---------------------------------------------------------------- FAST illustrations (300 x 300)
def face_droop(p):
    """A friendly face whose right side droops (mouth corner + eyelid) as p goes 0 -> 1."""
    c = Cv(300, 300)
    c.circle(150, 150, 120, fill=(255, 226, 196, 255), outline=CHAR, width=8)
    d = 34 * ease(p)
    c.circle(105, 125, 12, fill=CHAR)                               # left eye (normal)
    c.circle(195, 125 + d * 0.25, 12, fill=CHAR)                    # right eye, lid lowers
    c.line([(110, 98), (90, 92)], CHAR, 6); c.line([(190, 98 + d * 0.15), (212, 100 + d * 0.35)], CHAR, 6)
    left = bez((90, 185), (110, 215), (140, 222), (150, 220))                  # smile: left half lifts
    right = bez((150, 220), (165, 218 + d * 0.3), (190, 200 + d * 0.9), (210, 185 + d * 1.4))
    c.line(left + right[1:], CHAR, 8)
    return c.img()


def arms(p):
    """Front view, both arms held out; the right arm drifts down as p goes 0 -> 1."""
    c = Cv(300, 300)
    c.circle(150, 70, 40, fill=(255, 226, 196, 255), outline=CHAR, width=7)
    c.rrect(105, 115, 195, 260, 30, fill=CHAR)
    c.line([(110, 140), (30, 130)], (255, 226, 196, 255), 26)             # left arm, held up
    c.line([(110, 140), (30, 130)], CHAR, 4)
    a = math.radians(-6 + 46 * ease(p))
    x, y = 190 + 82 * math.cos(a), 140 + 82 * math.sin(a)
    c.line([(190, 140), (x, y)], (255, 226, 196, 255), 26)
    if p > 0.05:                                                       # dotted line: where the arm should be
        for k in range(5):
            xx = 200 + k * 16
            c.circle(xx, 132 - k * 1.5, 3.5, fill=(240, 133, 62, int(255 * clamp(p * 3))))
        c.arc(198, 140, 70, -8, -8 + 42 * ease(p), ORANGE, 5)
    return c.img()


def speech_bubble(t, t0):
    """A speech bubble whose words come out wobbly and smeared: slurred speech."""
    c = Cv(300, 300)
    c.rrect(20, 50, 280, 200, 46, fill=WHITE, outline=CHAR, width=8)
    c.poly([(80, 196), (70, 250), (120, 198)], fill=WHITE)
    c.line([(80, 198), (70, 250), (120, 199)], CHAR, 8)
    im = c.img()
    f = G.font("cav", 700, 64)
    word = "Hel..lo?"
    lay = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x = 52
    n = int(clamp((t - t0) / 1.2) * len(word) + 0.999)
    for i, ch in enumerate(word[:n]):
        dy = 10 * math.sin(i * 1.3 + t * 3)
        d.text((x, 125 + dy), ch, font=f, fill=CHAR, anchor="lm")
        x += f.getlength(ch) * 0.92
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    im.alpha_composite(lay)
    return im


def ic_dizzy(t=0.0):
    c = Cv(120, 120)
    c.circle(60, 70, 34, outline=CHAR, width=7)
    for k in range(3):
        a = t * 2.4 + k * 2.09
        x, y = 60 + 46 * math.cos(a), 26 + 10 * math.sin(a)
        c.circle(x, y, 6, fill=ORANGE)
    c.arc(52, 70, 9, 0, 300, CHAR, 4); c.arc(72, 70, 9, 0, 300, CHAR, 4)
    return c.img()


def ic_vision(t=0.0):
    c = Cv(120, 120)
    for dx, col in ((-8, (43, 43, 43, 90)), (0, CHAR)):
        c.line(bez((14 + dx, 60), (40 + dx, 26), (80 + dx, 26), (106 + dx, 60)), col, 7)
        c.line(bez((14 + dx, 60), (40 + dx, 94), (80 + dx, 94), (106 + dx, 60)), col, 7)
    c.circle(60, 60, 16, fill=ORANGE)
    c.circle(60, 60, 6, fill=CHAR)
    return c.img()


def ic_headache(t=0.0):
    c = Cv(120, 120)
    c.circle(54, 66, 36, outline=CHAR, width=7)
    c.poly([(86, 12), (70, 46), (86, 46), (74, 78), (104, 36), (88, 36), (100, 12)], fill=ORANGE)
    return c.img()


def ic_clock(p=1.0, size=120):
    c = Cv(size, size)
    s = size / 120
    c.circle(60 * s, 62 * s, 46 * s, fill=WHITE, outline=CHAR, width=8 * s)
    a = -math.pi / 2 + 2 * math.pi * p
    c.line([(60 * s, 62 * s), (60 * s + 30 * s * math.cos(a), 62 * s + 30 * s * math.sin(a))], ORANGE, 7 * s)
    c.line([(60 * s, 62 * s), (60 * s, 38 * s)], CHAR, 7 * s)
    c.circle(60 * s, 62 * s, 6 * s, fill=CHAR)
    return c.img()


def ic_phone(size=120):
    c = Cv(size, size)
    s = size / 120
    pts = bez((30 * s, 22 * s), (12 * s, 40 * s), (40 * s, 90 * s), (92 * s, 102 * s), 30)
    c.line(pts, WHITE, 22 * s)
    c.rrect(18 * s, 14 * s, 44 * s, 38 * s, 8 * s, fill=WHITE)
    c.rrect(82 * s, 84 * s, 108 * s, 108 * s, 8 * s, fill=WHITE)
    return c.img()


def ic_hospital(size=120):
    c = Cv(size, size)
    s = size / 120
    c.rrect(20 * s, 30 * s, 100 * s, 108 * s, 8 * s, fill=WHITE, outline=CHAR, width=7 * s)
    c.rrect(50 * s, 44 * s, 70 * s, 84 * s, 3 * s, fill=ORANGE)
    c.rrect(40 * s, 54 * s, 80 * s, 74 * s, 3 * s, fill=ORANGE)
    c.rrect(52 * s, 92 * s, 68 * s, 108 * s, 2 * s, fill=CHAR)
    return c.img()


def ic_no_food(size=120):
    c = Cv(size, size)
    s = size / 120
    c.poly([(30 * s, 40 * s), (62 * s, 40 * s), (58 * s, 96 * s), (34 * s, 96 * s)], fill=WHITE, outline=CHAR, width=6 * s)
    c.line([(32 * s, 58 * s), (60 * s, 58 * s)], (86, 156, 214, 255), 6 * s)
    c.rrect(70 * s, 52 * s, 104 * s, 72 * s, 10 * s, fill=ORANGE)
    c.rrect(87 * s, 52 * s, 104 * s, 72 * s, 10 * s, fill=WHITE, outline=ORANGE, width=3 * s)
    c.circle(60 * s, 66 * s, 52 * s, outline=(214, 84, 52, 255), width=8 * s)
    c.line([(24 * s, 30 * s), (96 * s, 102 * s)], (214, 84, 52, 255), 8 * s)
    return c.img()


def ic_hourglass(size=120):
    c = Cv(size, size)
    s = size / 120
    c.line([(34 * s, 20 * s), (86 * s, 20 * s)], CHAR, 7 * s); c.line([(34 * s, 100 * s), (86 * s, 100 * s)], CHAR, 7 * s)
    c.line([(40 * s, 22 * s), (60 * s, 60 * s), (40 * s, 98 * s)], CHAR, 6 * s)
    c.line([(80 * s, 22 * s), (60 * s, 60 * s), (80 * s, 98 * s)], CHAR, 6 * s)
    c.poly([(46 * s, 96 * s), (60 * s, 74 * s), (74 * s, 96 * s)], fill=ORANGE)
    c.circle(60 * s, 60 * s, 52 * s, outline=(214, 84, 52, 255), width=8 * s)
    c.line([(24 * s, 30 * s), (96 * s, 102 * s)], (214, 84, 52, 255), 8 * s)
    return c.img()


def ic_bookmark(size=80, fill=WHITE):
    c = Cv(size, size)
    s = size / 80
    c.poly([(20 * s, 10 * s), (60 * s, 10 * s), (60 * s, 72 * s), (40 * s, 56 * s), (20 * s, 72 * s)], fill=fill)
    return c.img()


def ic_share(size=80, fill=WHITE):
    c = Cv(size, size)
    s = size / 80
    c.poly([(8 * s, 38 * s), (72 * s, 10 * s), (52 * s, 72 * s), (38 * s, 46 * s)], fill=fill)
    return c.img()


if __name__ == "__main__":                      # contact sheet of every illustration
    import sys
    tiles = [brain(6.0, 1.0, 3.0, 3.5), brain(1.5, 1.0, 9.0, 9.0), face_droop(0.0), face_droop(1.0), arms(0.0), arms(1.0),
             speech_bubble(2.0, 0.0)]
    tiles += [ic(1.0) for ic in (ic_bp, ic_diabetes, ic_smoking, ic_stress, ic_clock)] + [ic_dizzy(0.4), ic_vision(), ic_headache(),
              ic_phone(), ic_hospital(), ic_no_food(), ic_hourglass(), ic_check(), ic_bookmark(fill=CHAR), ic_share(fill=CHAR)]
    W = 1600
    sheet = Image.new("RGBA", (W, 1100), (253, 246, 238, 255))
    x = y = 10; rowh = 0
    for im in tiles:
        if x + im.width > W:
            x, y = 10, y + rowh + 10; rowh = 0
        sheet.alpha_composite(im, (x, y)); x += im.width + 10; rowh = max(rowh, im.height)
    sheet.convert("RGB").save(sys.argv[1])
