# Animated sprite + caption layers composited onto RGBA frames.
import math
from PIL import Image
import gfx


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out_cubic(p):
    return 1 - (1 - p) ** 3


def ease_in_cubic(p):
    return p ** 3


def ease_in_out(p):
    return 3 * p * p - 2 * p * p * p


def ease_out_back(p, k=1.70158):
    p -= 1
    return 1 + (k + 1) * p ** 3 + k * p ** 2


def paste(frame, im, cx, cy):
    """Alpha-composite `im` centred at (cx, cy), clipping at frame edges."""
    x0, y0 = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x1, y1 = min(frame.width, x0 + im.width), min(frame.height, y0 + im.height)
    if x1 <= max(x0, 0) or y1 <= max(y0, 0):
        return
    src = im.crop((sx0, sy0, sx0 + x1 - max(x0, 0), sy0 + y1 - max(y0, 0)))
    frame.alpha_composite(src, (max(x0, 0), max(y0, 0)))


def with_alpha(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


class Sprite:
    def __init__(self, img, x, y, t0, t1, ain="pop", aout="fade", din=0.3, dout=0.22, dist=520,
                 rot=0.0, wobble=None, bob=None, scale=1.0, layer=0, path=None, dim=None, pulse=None):
        self.img, self.x, self.y, self.t0, self.t1 = img, x, y, t0, t1
        self.ain, self.aout, self.din, self.dout, self.dist = ain, aout, din, dout, dist
        self.rot, self.wobble, self.bob, self.scale, self.layer = rot, wobble, bob, scale, layer
        self.path, self.dim, self.pulse = path, dim, pulse

    def active(self, t):
        return self.t0 <= t < self.t1

    def render(self, frame, t):
        img = self.img(t) if callable(self.img) else self.img
        x, y, s = self.x, self.y, self.scale
        if self.path:
            x, y, s = self.path(t, x, y, s)
        a, dx, dy, rot = 1.0, 0.0, 0.0, self.rot
        pi = clamp((t - self.t0) / self.din) if self.din else 1.0
        po = clamp((self.t1 - t) / self.dout) if self.dout else 1.0
        # --- in
        if self.ain == "pop":
            s *= 0.25 + 0.75 * ease_out_back(pi, 2.2) if pi < 1 else 1
            a *= clamp(pi * 3)
        elif self.ain == "fade":
            a *= pi
        elif self.ain in ("slide_l", "slide_r", "slide_u", "slide_d"):
            k = (1 - ease_out_cubic(pi)) * self.dist
            dx += {"slide_l": -k, "slide_r": k}.get(self.ain, 0)
            dy += {"slide_u": k * 0.35, "slide_d": -k * 0.35}.get(self.ain, 0)
            a *= clamp(pi * 2.5)
        elif self.ain == "wipe" and pi < 1:
            w = max(1, int(img.width * ease_out_cubic(pi)))
            full = Image.new("RGBA", img.size, (0, 0, 0, 0))
            full.alpha_composite(img.crop((0, 0, w, img.height)), (0, 0))
            img = full
        # --- out
        if self.aout == "fade":
            a *= po
        elif self.aout == "pop":
            s *= ease_in_out(po) if po < 1 else 1
        elif self.aout in ("slide_l", "slide_r"):
            k = (1 - ease_out_cubic(po)) * self.dist
            dx += -k if self.aout == "slide_l" else k
            a *= clamp(po * 2)
        elif self.aout == "up":
            dy -= (1 - po) * 60
            a *= po
        if self.wobble:
            amp, f = self.wobble
            rot += amp * math.sin(2 * math.pi * f * (t - self.t0))
        if self.bob:
            amp, f = self.bob
            dy += amp * math.sin(2 * math.pi * f * (t - self.t0))
        if self.pulse:
            amp, f = self.pulse
            s *= 1 + amp * (0.5 - 0.5 * math.cos(2 * math.pi * f * max(0, t - self.t0 - self.din)))
        if self.dim and t > self.dim[0]:
            a *= 1 - (1 - self.dim[1]) * clamp((t - self.dim[0]) / 0.25)
        if a <= 0.01 or s <= 0.01:
            return
        if abs(s - 1) > 0.004:
            img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BICUBIC)
        if abs(rot) > 0.05:
            img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
        paste(frame, with_alpha(img, a), x + dx, y + dy)


class Captions:
    """Word-highlight captions. words: [{w, s, e}] in output seconds."""
    KEY = {"executive", "skills", "adhd", "autism", "struggling", "organize", "independently", "knowing", "doing",
           "familiar", "socks", "shoes", "plan", "visual", "schedule", "predictable", "single", "break", "bus",
           "management", "brain's", "different", "gradually", "ignoring", "listening", "remind"}

    def __init__(self, words, y=1350, hide=(), size=68, max_chars=17, max_words=3):
        self.y, self.hide, self.size = y, hide, size
        self.chunks = []
        cur = []
        for i, w in enumerate(words):
            cur.append(w)
            txt = " ".join(x["w"] for x in cur)
            nxt = words[i + 1] if i + 1 < len(words) else None
            brk = (w["w"][-1] in ",.?!" or len(cur) >= max_words or nxt is None
                   or len(txt + " " + nxt["w"]) > max_chars or nxt["s"] - w["e"] > 0.45
                   or nxt.get("seg") != w.get("seg") and w["w"][-1] in ",.?!")
            if brk:
                self.chunks.append(cur)
                cur = []
        self.cache = {}
        self.times = []
        for k, c in enumerate(self.chunks):
            t0 = c[0]["s"] - 0.05
            nxt = self.chunks[k + 1][0]["s"] - 0.05 if k + 1 < len(self.chunks) else c[-1]["e"] + 0.6
            t1 = min(nxt, max(c[-1]["e"] + 0.5, c[-1]["s"] + 0.35))
            self.times.append((t0, t1))

    def word_img(self, w, active):
        clean = w.strip()
        key = clean.lower().strip(",.?!\"'")
        if active:
            t = gfx.text(clean, "ExtraBold", self.size, gfx.INK)
            box = gfx.rounded(t.width + 22, t.height + 10, 16, gfx.YEL)
            box.alpha_composite(t, (11, 5))
            return box
        fill = gfx.YEL if key in self.KEY else gfx.WHITE
        return gfx.text(clean, "ExtraBold", self.size, fill, stroke=8, stroke_fill=gfx.BLACK)

    def chunk_img(self, k, ai):
        if (k, ai) not in self.cache:
            ims = [self.word_img(w["w"], i == ai) for i, w in enumerate(self.chunks[k])]
            self.cache[(k, ai)] = gfx.shadow(gfx.row(ims, gap=4), (0, 6), 10, 120)
        return self.cache[(k, ai)]

    def render(self, frame, t):
        if any(a <= t < b for a, b in self.hide):
            return
        for k, (t0, t1) in enumerate(self.times):
            if t0 <= t < t1:
                c = self.chunks[k]
                ai = -1
                for i, w in enumerate(c):
                    if t >= w["s"] - 0.03:
                        ai = i
                im = self.chunk_img(k, ai)
                p = clamp((t - t0) / 0.14)
                s = 0.82 + 0.18 * ease_out_back(p, 2.0) if p < 1 else 1.0
                if s != 1.0:
                    im = im.resize((int(im.width * s), int(im.height * s)), Image.BICUBIC)
                paste(frame, with_alpha(im, clamp(p * 3)), 540, self.y)
                return
