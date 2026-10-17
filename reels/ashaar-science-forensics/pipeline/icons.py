# Minimal vector icons drawn in code (supersampled) so the reel needs no emoji or stock art.
import math
from PIL import Image, ImageDraw
from gfx2 import ORANGE, CHAR, CREAM, WHITE, circle

S = 4  # supersample


def _new(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def _done(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def _pl(d, pts, fill, width, joint="curve"):
    pts = [(x * S, y * S) for x, y in pts]
    d.line(pts, fill=fill, width=int(width * S), joint=joint)
    r = width * S / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def check_badge(size, p=1.0, bg=ORANGE, fg=CREAM):
    im = circle(size, bg)
    if p <= 0:
        return im
    big = _new(size, size)
    d = ImageDraw.Draw(big)
    pts = [(size * 0.28, size * 0.52), (size * 0.44, size * 0.67), (size * 0.73, size * 0.34)]
    seg = [pts[0]]
    l1 = math.dist(pts[0], pts[1]); l2 = math.dist(pts[1], pts[2]); tot = l1 + l2; run = p * tot
    if run <= l1:
        f = run / l1; seg.append((pts[0][0] + (pts[1][0] - pts[0][0]) * f, pts[0][1] + (pts[1][1] - pts[0][1]) * f))
    else:
        f = (run - l1) / l2; seg += [pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * f, pts[1][1] + (pts[2][1] - pts[1][1]) * f)]
    _pl(d, seg, fg, size * 0.095)
    im.alpha_composite(_done(big, size, size))
    return im


def magnifier(size, color=CHAR, lw=0.085):
    w = h = size
    im = _new(w, h); d = ImageDraw.Draw(im)
    r = size * 0.33; cx, cy = size * 0.40, size * 0.40
    d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), outline=color, width=int(size * lw * S))
    x0, y0 = cx + r * 0.72, cy + r * 0.72
    _pl(d, [(x0, y0), (size * 0.90, size * 0.90)], color, size * lw * 1.25)
    return _done(im, w, h)


def fingerprint(size, p=1.0, color=CHAR, lw=0.036):
    """Concentric broken ridges (classic fingerprint glyph) swept on from the core outwards; p = 0..1."""
    im = _new(size, size); d = ImageDraw.Draw(im)
    cx, cy = size / 2, size * 0.52
    n = 8
    # (start, end) sweep in degrees (0 = east, clockwise) — gaps wander so rings read as ridges, not circles
    spans = [(-200, 20), (-215, 35), (-225, 10), (-205, 40), (-230, 25), (-210, 5), (-235, 30), (-220, 15)]
    for i in range(n):
        q = min(1.0, max(0.0, p * (n + 1.2) - i))
        if q <= 0:
            continue
        rx = size * (0.055 + 0.052 * i); ry = rx * (1.12 + 0.02 * i)
        a0, a1 = spans[i]
        end = a0 + (a1 - a0) * q + 360 * (1 if a1 < a0 else 0)
        box = ((cx - rx) * S, (cy - ry + size * 0.04 * (i / n)) * S, (cx + rx) * S, (cy + ry + size * 0.04 * (i / n)) * S)
        d.arc(box, a0, a0 + (a1 - a0 + 360) * q if a1 < a0 else end, fill=color, width=int(size * lw * S))
    core = size * 0.045 * min(1, p * 4)
    d.ellipse(((cx - core) * S, (cy - core) * S, (cx + core) * S, (cy + core) * S), fill=ORANGE)
    return _done(im, size, size)


def signature(w, h, p=1.0, color=CHAR, lw=0.07):
    """Cursive scribble drawn on progressively, with a pen nib at the head."""
    im = _new(w, h); d = ImageDraw.Draw(im)
    pts = []
    N = 160
    for k in range(N + 1):
        t = k / N
        env = 0.35 + 0.65 * math.sin(math.pi * min(1, t * 1.05)) ** 0.7
        x = w * (0.05 + 0.88 * t + 0.045 * math.sin(2 * math.pi * 5.5 * t + 0.6))
        y = h * (0.52 + 0.36 * env * math.cos(2 * math.pi * 5.5 * t) * (0.9 if k % 2 else 1.0) * 0.9 - 0.10 * t)
        pts.append((x, y))
    # underline flourish
    m = int(N * max(0.0, min(1.0, p)))
    if m >= 2:
        _pl(d, pts[:m + 1], color, h * lw)
    if p >= 0.98:
        _pl(d, [(w * 0.10, h * 0.90), (w * 0.60, h * 0.88), (w * 0.93, h * 0.86)], ORANGE, h * lw * 0.9)
    elif p > 0:
        x, y = pts[m]
        nib = [(x, y), (x + w * 0.05, y - h * 0.22), (x + w * 0.08, y - h * 0.16), (x + w * 0.015, y + h * 0.04)]
        d.polygon([(a * S, b * S) for a, b in nib], fill=ORANGE)
    return _done(im, w, h)


def flask(size, t=0.0, fill=0.55, color=CHAR, liquid=ORANGE, bubbles=True):
    im = _new(size, size); d = ImageDraw.Draw(im)
    lw = size * 0.055
    nx0, nx1 = size * 0.40, size * 0.60
    ntop, nbot = size * 0.08, size * 0.38
    bl, br, bb = size * 0.14, size * 0.86, size * 0.90
    body = [(nx0, nbot), (bl, bb), (br, bb), (nx1, nbot)]
    # liquid (clipped to body) — flat surface at `fill`
    ly = bb - (bb - nbot) * fill
    def xat(y, side):
        f = (y - nbot) / (bb - nbot)
        return (nx0 + (bl - nx0) * f) if side == 0 else (nx1 + (br - nx1) * f)
    liq = [(xat(ly, 0), ly), (xat(ly, 1), ly), (br, bb), (bl, bb)]
    d.polygon([(x * S, y * S) for x, y in liq], fill=liquid)
    if bubbles:
        for k in range(4):
            ph = (t * 0.9 + k * 0.27) % 1.0
            bx = size * (0.38 + 0.08 * k + 0.02 * math.sin(6 * ph + k))
            by = bb - size * 0.04 - (bb - ly) * ph * 0.95
            rr = size * (0.022 + 0.01 * (k % 2)) * (1 - 0.3 * ph)
            if by > ly + rr:
                d.ellipse(((bx - rr) * S, (by - rr) * S, (bx + rr) * S, (by + rr) * S), fill=CREAM)
    _pl(d, [(nx0, ntop), (nx0, nbot), (bl, bb), (br, bb), (nx1, nbot), (nx1, ntop)], color, lw)
    _pl(d, [(nx0 - size * 0.035, ntop), (nx1 + size * 0.035, ntop)], color, lw)
    return _done(im, size, size)


def paper_plane(size, color=CHAR):
    im = _new(size, size); d = ImageDraw.Draw(im)
    pts = [(0.08, 0.50), (0.94, 0.10), (0.68, 0.90), (0.50, 0.58)]
    d.polygon([(x * size * S, y * size * S) for x, y in pts], fill=color)
    d.polygon([(0.50 * size * S, 0.58 * size * S), (0.94 * size * S, 0.10 * size * S), (0.40 * size * S, 0.66 * size * S)], fill=(0, 0, 0, 60))
    return _done(im, size, size)


def steps(size, p=1.0, color=CHAR, hi=ORANGE):
    """Three ascending bars; p raises them in sequence (a 'next level' staircase)."""
    im = _new(size, size); d = ImageDraw.Draw(im)
    bw = size * 0.24; gap = size * 0.07
    for i in range(3):
        q = max(0.0, min(1.0, p * 3 - i)); q = 1 - (1 - q) ** 3
        h = size * (0.28 + 0.26 * i) * q
        x0 = size * 0.06 + i * (bw + gap)
        d.rounded_rectangle((x0 * S, (size * 0.92 - h) * S, (x0 + bw) * S, size * 0.92 * S), radius=int(size * 0.05 * S),
                            fill=hi if i == 2 else color)
    return _done(im, size, size)


def dot(d, fill):
    return circle(d, fill)
