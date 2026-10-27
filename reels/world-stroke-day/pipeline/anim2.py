# Animated sprites + brand captions. Motion language: eased rises/slides/wipes, no bounce.
import math, re
from PIL import Image
import gfx2 as G


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(p):
    return 1 - (1 - p) ** 3


def ease_in(p):
    return p ** 3


def ease_io(p):
    return 3 * p * p - 2 * p * p * p


def ease_out_soft(p):  # gentle overshoot-free settle
    return 1 - (1 - p) ** 4


def paste(frame, im, cx, cy):
    x0, y0 = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x1, y1 = min(frame.width, x0 + im.width), min(frame.height, y0 + im.height)
    if x1 <= max(x0, 0) or y1 <= max(y0, 0):
        return
    src = im.crop((sx0, sy0, sx0 + x1 - max(x0, 0), sy0 + y1 - max(y0, 0)))
    frame.alpha_composite(src, (max(x0, 0), max(y0, 0)))


class Sprite:
    """img: RGBA image or callable(t)->RGBA. Anchored by its centre at (x, y)."""

    def __init__(self, img, x, y, t0, t1, ain="rise", aout="fade", din=0.38, dout=0.25, dist=44, scale=1.0, layer=0,
                 path=None, name="", wipe_soft=0.0):
        self.img, self.x, self.y, self.t0, self.t1 = img, x, y, t0, t1
        self.ain, self.aout, self.din, self.dout, self.dist, self.scale, self.layer = ain, aout, din, dout, dist, scale, layer
        self.path, self.name = path, name

    def active(self, t):
        return self.t0 <= t < self.t1

    def render(self, frame, t):
        img = self.img(t) if callable(self.img) else self.img
        if img is None:
            return
        x, y, s, a = self.x, self.y, self.scale, 1.0
        if self.path:
            x, y, s = self.path(t, x, y, s)
        pi = clamp((t - self.t0) / self.din) if self.din else 1.0
        po = clamp((self.t1 - t) / self.dout) if self.dout else 1.0
        ei = ease_out(pi)
        if self.ain == "rise":
            y += (1 - ei) * self.dist; a *= clamp(pi * 2.2)
        elif self.ain == "fade":
            a *= pi
        elif self.ain == "scale":
            s *= 0.92 + 0.08 * ei; a *= clamp(pi * 2.4)
        elif self.ain in ("left", "right"):
            x += (1 - ei) * self.dist * (-1 if self.ain == "left" else 1); a *= clamp(pi * 2.5)
        elif self.ain == "wipe" and pi < 1:
            w = max(1, int(img.width * ease_io(pi)))
            full = Image.new("RGBA", img.size, (0, 0, 0, 0))
            full.alpha_composite(img.crop((0, 0, w, img.height)), (0, 0))
            img = full
        elif self.ain == "wipe_up" and pi < 1:      # text rises out from a baseline mask
            h = max(1, int(img.height * ease_out(pi)))
            full = Image.new("RGBA", img.size, (0, 0, 0, 0))
            full.alpha_composite(img.crop((0, img.height - h, img.width, img.height)), (0, img.height - h))
            img = full
            y += (1 - ease_out(pi)) * 0.35 * img.height
        po_e = ease_in(po) if po < 1 else 1.0
        if self.aout == "fade":
            a *= po
        elif self.aout == "rise":
            y -= (1 - po) * 30; a *= po
        elif self.aout == "left":
            x -= (1 - po_e) * self.dist * 3; a *= clamp(po * 2)
        elif self.aout == "scale":
            s *= 0.94 + 0.06 * po; a *= po
        if a <= 0.01 or s <= 0.01:
            return
        if abs(s - 1) > 0.004:
            img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BICUBIC)
        paste(frame, G.with_alpha(img, a), x, y)


class Captions:
    """Word-by-word captions on a charcoal pill; the spoken word turns orange. No shadows, no emoji."""

    def __init__(self, words, y=1385, hide=(), size=56, max_chars=24, max_words=4, y_for=None):
        self.y, self.hide, self.size, self.y_for = y, hide, size, y_for
        self.chunks = []
        cur = []
        WEAK = {"a", "an", "the", "to", "of", "and", "or", "at", "in", "on", "for", "with", "by", "if", "as", "is", "are", "your", "their",
                "his", "her", "our", "my", "that", "this", "we", "they", "you", "it", "but", "so"}
        for i, w in enumerate(words):
            cur.append(w)
            txt = " ".join(x["w"] for x in cur)
            nxt = words[i + 1] if i + 1 < len(words) else None
            hard = nxt is None or w["w"][-1] in ".?!" or nxt["s"] - w["e"] > 0.5 or nxt.get("seg") != w.get("seg")
            soft = (w["w"][-1] == "," and len(cur) >= 2) or len(cur) >= max_words or (nxt is not None and len(txt + " " + nxt["w"]) > max_chars)
            last = re.sub(r"[^a-z0-9']", "", w["w"].lower())
            if soft and not hard and (last in WEAK or last.isdigit()) and len(cur) < max_words + 2 and len(txt) < max_chars + 8:
                soft = False                                   # never end a caption on a weak word or a number ("14 | November")
            if hard or soft:
                self.chunks.append(cur)
                cur = []
        # no one-word orphans at the end of a sentence
        for k in range(1, len(self.chunks)):
            c, p = self.chunks[k], self.chunks[k - 1]
            if len(c) == 1 and len(p) >= 3 and c[0]["w"][-1] in ".?!" and p[-1]["w"][-1] not in ".?!," and p[-1].get("seg") == c[0].get("seg"):
                c.insert(0, p.pop())
        self.times = []
        for k, c in enumerate(self.chunks):
            t0 = c[0]["s"] - 0.04
            if k + 1 < len(self.chunks):
                n0 = self.chunks[k + 1][0]["s"] - 0.04
                t1 = n0 if n0 - c[-1]["e"] < 0.9 else c[-1]["e"] + 0.35    # stay on screen through continuous speech
            else:
                t1 = c[-1]["e"] + 0.6
            self.times.append((t0, t1))
        self.cache = {}

    def chunk_img(self, k, ai):
        key = (k, ai)
        if key not in self.cache:
            f = G.font("dm", 700, self.size)
            ws = [w["w"].replace("'", "\u2019") for w in self.chunks[k]]
            sp = f.getlength(" ")
            asc, desc = f.getmetrics()
            cap_top = f.getbbox("H")[1]
            total = int(sum(f.getlength(w) for w in ws) + sp * (len(ws) - 1))
            px, py = 34, 16
            top, bot = cap_top - int(0.06 * self.size), asc + int(0.26 * self.size)
            th = bot - top
            W, H = total + 2 * px, th + 2 * py
            base = G.rounded(W, H, H // 2, G.a(G.CHAR, 224))
            x = px
            from PIL import ImageDraw
            d = ImageDraw.Draw(base)
            for i, w in enumerate(ws):
                d.text((x, py - top), w, font=f, fill=G.ORANGE if i == ai else G.CREAM)
                x += f.getlength(w) + sp
            self.cache[key] = base
        return self.cache[key]

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
                p = clamp((t - t0) / 0.12)
                y = self.y_for(t) if self.y_for else self.y
                paste(frame, G.with_alpha(im, ease_out(p)), 540, y + (1 - ease_out(p)) * 10)
                return
