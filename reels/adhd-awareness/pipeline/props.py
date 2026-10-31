# Simple doodle props in the same line style as the characters (cairo). Every function draws at a given position
# with an alpha and an animation parameter, so the story can fade/scale/move them smoothly.
import math
import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from doodle import INK, PAPER, ORANGE, CHAR, CREAM, _stroke, _fill_stroke, _set_ink

FD = "/tmp/claude-0/fonts"
_FONTS = {}


def font(fam, wt, size):
    key = (fam, wt, size)
    if key not in _FONTS:
        path = {"dm": "DMSans-VF.ttf", "pfi": "PlayfairDisplay-Italic-VF.ttf", "cav": "Caveat-VF.ttf"}[fam]
        f = ImageFont.truetype(f"{FD}/{path}", size)
        try:
            f.set_variation_by_axes([min(40, max(9, size / 2.2)), wt] if fam == "dm" else [wt])
        except Exception:
            pass
        _FONTS[key] = f
    return _FONTS[key]


_TXT = {}


def text_surface(s, fam="dm", wt=800, size=48, col=(43, 43, 43)):
    """PIL-rendered text as a cairo surface (premultiplied BGRA). Returns (surface, w, h)."""
    key = (s, fam, wt, size, col)
    if key not in _TXT:
        f = font(fam, wt, size)
        w = int(f.getlength(s)) + 16
        asc, desc = f.getmetrics()
        im = Image.new("RGBA", (w, asc + desc + 12), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((8, 6), s, font=f, fill=col + (255,))
        a = np.asarray(im).astype(np.float32)
        al = a[..., 3:4] / 255
        bgra = np.concatenate([a[..., 2:3] * al, a[..., 1:2] * al, a[..., 0:1] * al, a[..., 3:4]], 2).astype(np.uint8)
        bgra = np.ascontiguousarray(bgra)
        surf = cairo.ImageSurface.create_for_data(memoryview(bgra), cairo.FORMAT_ARGB32, im.width, im.height, im.width * 4)
        _TXT[key] = (surf, im.width, im.height, bgra)
    s_, w, h, _ = _TXT[key]
    return s_, w, h


def draw_text(c, s, x, y, a=1.0, scale=1.0, rot=0.0, **kw):
    surf, w, h = text_surface(s, **kw)
    c.save()
    c.translate(x, y); c.rotate(math.radians(rot)); c.scale(scale, scale)
    c.set_source_surface(surf, -w / 2, -h / 2)
    c.paint_with_alpha(a)
    c.restore()
    return w * scale, h * scale


def pop(p):
    """Scale curve for a soft pop-in (slight overshoot, no bounce-back)."""
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3 * (1 - 0.9 * p) if p < 1 else 1.0


def rrect(c, x, y, w, h, r):
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()


def bubble(c, x, y, s, a=1.0, scale=1.0, tail=(0, 1), size=46, fill=PAPER, tcol=(43, 43, 43), wt=800, fam="dm", lw=6):
    """Speech bubble centred at (x, y) with a little tail pointing toward `tail` (unit vector)."""
    if a <= 0.01 or scale <= 0.01:
        return
    surf, tw, th = text_surface(s, fam, wt, size, tcol)
    w, h = tw + 44, th + 30
    c.save(); c.translate(x, y); c.scale(scale, scale)
    rrect(c, -w / 2, -h / 2, w, h, h / 2)
    tx, ty = tail
    bx, by = tx * w * 0.25, h / 2 if ty > 0 else -h / 2
    c.move_to(bx - 16, by - (2 if ty > 0 else -2)); c.line_to(bx + tx * 30 + 6, by + ty * 34); c.line_to(bx + 16, by - (2 if ty > 0 else -2))
    c.set_source_rgba(fill[0], fill[1], fill[2], a); c.fill_preserve()
    _stroke(c, lw, a)
    rrect(c, -w / 2, -h / 2, w, h, h / 2)
    c.set_source_rgba(fill[0], fill[1], fill[2], a); c.fill()
    c.set_source_surface(surf, -tw / 2, -th / 2); c.paint_with_alpha(a)
    c.restore()
    return w * scale, h * scale


def question(c, x, y, a=1.0, scale=1.0, col=ORANGE):
    if a <= 0.01:
        return
    draw_text(c, "?", x, y, a, scale, fam="dm", wt=800, size=150, col=tuple(int(v * 255) for v in col))


def exclaim(c, x, y, a=1.0, scale=1.0):
    draw_text(c, "!", x, y, a, scale, fam="dm", wt=800, size=130, col=(240, 133, 62))


def butterfly(c, x, y, t, a=1.0, s=1.0):
    if a <= 0.01:
        return
    flap = 0.35 + 0.65 * abs(math.sin(t * 14))
    c.save(); c.translate(x, y); c.scale(s, s)
    for side in (-1, 1):
        c.save(); c.scale(side * flap, 1)
        c.move_to(0, 0); c.curve_to(30, -50, 70, -30, 50, 0); c.curve_to(65, 25, 30, 45, 0, 5); c.close_path()
        c.set_source_rgba(ORANGE[0], ORANGE[1], ORANGE[2], a); c.fill_preserve(); _stroke(c, 4, a)
        c.restore()
    c.move_to(0, -18); c.line_to(0, 18); _stroke(c, 6, a)
    c.move_to(0, -18); c.curve_to(-6, -30, -12, -34, -16, -36); _stroke(c, 3, a)
    c.move_to(0, -18); c.curve_to(6, -30, 12, -34, 16, -36); _stroke(c, 3, a)
    c.restore()


def desk(c, x, y, a=1.0):
    """Small desk seen from the front with a notebook and a pencil (pencil position animatable via return)."""
    if a <= 0.01:
        return
    c.rectangle(x - 150, y - 300, 300, 22); _fill_stroke(c, 6, a)
    c.move_to(x - 130, y - 278); c.line_to(x - 130, y); _stroke(c, 6, a)
    c.move_to(x + 130, y - 278); c.line_to(x + 130, y); _stroke(c, 6, a)
    # notebook
    c.save(); c.translate(x - 30, y - 300)
    c.move_to(-70, 0); c.line_to(-60, -40); c.line_to(60, -40); c.line_to(70, 0); c.close_path()
    _fill_stroke(c, 5, a)
    c.move_to(0, -40); c.line_to(0, 0); _stroke(c, 4, a)
    c.restore()


def pencil(c, x, y, ang=0.0, a=1.0, L=110):
    if a <= 0.01:
        return
    c.save(); c.translate(x, y); c.rotate(math.radians(ang))
    c.rectangle(-L / 2, -9, L, 18)
    c.set_source_rgba(ORANGE[0], ORANGE[1], ORANGE[2], a); c.fill_preserve(); _stroke(c, 4, a)
    c.move_to(L / 2, -9); c.line_to(L / 2 + 24, 0); c.line_to(L / 2, 9); c.close_path(); _fill_stroke(c, 4, a)
    c.move_to(L / 2 + 16, -3); c.line_to(L / 2 + 24, 0); c.line_to(L / 2 + 16, 3); _stroke(c, 4, a)
    c.restore()


def thought(c, x, y, w, h, a=1.0, scale=1.0, src=None):
    """Cloud-shaped thought bubble centred at (x, y); small circles lead down toward `src` (head top)."""
    if a <= 0.01 or scale <= 0.01:
        return
    c.save(); c.translate(x, y); c.scale(scale, scale)
    n = 9
    pts = []
    for k in range(n):
        ang = 2 * math.pi * k / n
        pts.append((math.cos(ang) * w / 2, math.sin(ang) * h / 2))
    c.new_path()
    for k in range(n):
        x0, y0 = pts[k]; x1, y1 = pts[(k + 1) % n]
        mx, my = (x0 + x1) / 2 * 1.28, (y0 + y1) / 2 * 1.28
        if k == 0:
            c.move_to(x0, y0)
        c.curve_to(mx, my, mx, my, x1, y1)
    c.close_path()
    _fill_stroke(c, 6, a)
    c.restore()
    if src:
        sx, sy = src
        for k, r in enumerate((16, 11, 7)):
            f = 0.55 + 0.15 * k
            px, py = x + (sx - x) * f, y + h / 2 * scale + (sy - (y + h / 2 * scale)) * f
            c.arc(px, py, r * scale, 0, 2 * math.pi); _fill_stroke(c, 5, a)


def checklist(c, x, y, a=1.0, ticks=3):
    if a <= 0.01:
        return
    for k in range(3):
        yy = y - 50 + k * 50
        c.rectangle(x - 90, yy - 15, 30, 30); _fill_stroke(c, 5, a)
        if k < ticks:
            c.move_to(x - 84, yy); c.line_to(x - 76, yy + 9); c.line_to(x - 62, yy - 12); _stroke(c, 6, a, ORANGE)
        c.move_to(x - 40, yy); c.line_to(x + 90 - k * 25, yy); _stroke(c, 6, a)


def lightbulb(c, x, y, a=1.0, glow=1.0):
    if a <= 0.01:
        return
    if glow > 0:
        for k in range(8):
            ang = 2 * math.pi * k / 8
            c.move_to(x + math.cos(ang) * 70, y + math.sin(ang) * 70 - 10)
            c.line_to(x + math.cos(ang) * (70 + 24 * glow), y + math.sin(ang) * (70 + 24 * glow) - 10)
            _stroke(c, 6, a * glow, ORANGE)
    c.arc(x, y - 10, 48, math.radians(140), math.radians(40))
    c.line_to(x + 20, y + 52); c.line_to(x - 20, y + 52); c.close_path()
    c.set_source_rgba(1, 0.93, 0.75, a); c.fill_preserve(); _stroke(c, 6, a)
    for k in range(2):
        c.move_to(x - 20, y + 62 + k * 12); c.line_to(x + 20, y + 62 + k * 12); _stroke(c, 6, a)


def clock(c, x, y, r, hour, minute, a=1.0, spin_lines=0.0):
    if a <= 0.01:
        return
    c.arc(x, y, r, 0, 2 * math.pi); _fill_stroke(c, 8, a)
    for k in range(12):
        ang = 2 * math.pi * k / 12
        c.move_to(x + math.sin(ang) * r * 0.82, y - math.cos(ang) * r * 0.82)
        c.line_to(x + math.sin(ang) * r * 0.92, y - math.cos(ang) * r * 0.92)
        _stroke(c, 6 if k % 3 == 0 else 4, a)
    for ang, L, wd, col in ((hour, 0.5, 9, INK), (minute, 0.75, 7, ORANGE)):
        rr = math.radians(ang)
        c.move_to(x, y); c.line_to(x + math.sin(rr) * r * L, y - math.cos(rr) * r * L); _stroke(c, wd, a, col)
    c.arc(x, y, 9, 0, 2 * math.pi); _set_ink(c, a); c.fill()
    if spin_lines > 0:
        for k in range(3):
            c.arc(x, y, r + 24 + k * 14, math.radians(-60 + k * 10), math.radians(20 + k * 10))
            _stroke(c, 5, a * spin_lines)


def tab(c, x, y, w, h, a=1.0, rot=0.0, label=None):
    if a <= 0.01:
        return
    c.save(); c.translate(x, y); c.rotate(math.radians(rot))
    rrect(c, -w / 2, -h / 2, w, h, 10); _fill_stroke(c, 5, a)
    c.move_to(-w / 2, -h / 2 + 22); c.line_to(w / 2, -h / 2 + 22); _stroke(c, 4, a)
    for k, col in enumerate((ORANGE, CHAR, CHAR)):
        c.arc(-w / 2 + 14 + k * 14, -h / 2 + 11, 4, 0, 2 * math.pi); c.set_source_rgba(col[0], col[1], col[2], a); c.fill()
    c.move_to(w / 2 - 20, -h / 2 + 6); c.line_to(w / 2 - 10, -h / 2 + 16); c.move_to(w / 2 - 10, -h / 2 + 6); c.line_to(w / 2 - 20, -h / 2 + 16)
    _stroke(c, 3, a)
    for k in range(2):
        c.move_to(-w / 2 + 14, -h / 2 + 40 + k * 16); c.line_to(w / 2 - 14 - k * 20, -h / 2 + 40 + k * 16); _stroke(c, 4, a * 0.6)
    c.restore()


def notebook(c, x, y, a=1.0, rot=0.0, tick=1.0, s=1.0):
    if a <= 0.01:
        return
    c.save(); c.translate(x, y); c.rotate(math.radians(rot)); c.scale(s, s)
    rrect(c, -60, -78, 120, 156, 8); _fill_stroke(c, 6, a)
    c.rectangle(-60, -78, 18, 156); c.set_source_rgba(ORANGE[0], ORANGE[1], ORANGE[2], a); c.fill_preserve(); _stroke(c, 5, a)
    for k in range(4):
        c.move_to(-30, -45 + k * 26); c.line_to(42, -45 + k * 26); _stroke(c, 4, a * 0.5)
    if tick > 0:
        c.move_to(-10, 10); c.line_to(5, 28 * tick); c.line_to(5 + 30 * tick, -22 * tick); _stroke(c, 10, a, ORANGE)
    c.restore()


def poof(c, x, y, p, a=1.0):
    """Burst of short lines + a small puff: something vanishing."""
    if p <= 0 or p >= 1:
        return
    for k in range(10):
        ang = 2 * math.pi * k / 10 + 0.3
        r0, r1 = 30 + 70 * p, 55 + 95 * p
        c.move_to(x + math.cos(ang) * r0, y + math.sin(ang) * r0)
        c.line_to(x + math.cos(ang) * r1, y + math.sin(ang) * r1)
        _stroke(c, 6, a * (1 - p))
    c.arc(x, y, 30 * (1 - p) + 6, 0, 2 * math.pi)
    _stroke(c, 5, a * (1 - p) * 0.6)


def sweat(c, x, y, a=1.0, s=1.0):
    if a <= 0.01:
        return
    c.save(); c.translate(x, y); c.scale(s, s)
    c.move_to(0, -22); c.curve_to(14, -2, 14, 14, 0, 14); c.curve_to(-14, 14, -14, -2, 0, -22); c.close_path()
    c.set_source_rgba(0.72, 0.86, 0.96, a); c.fill_preserve(); _stroke(c, 4, a)
    c.restore()


def gear(c, x, y, r, ang, a=1.0, col=ORANGE):
    if a <= 0.01:
        return
    c.save(); c.translate(x, y); c.rotate(math.radians(ang))
    teeth = 8
    c.new_path()
    for k in range(teeth * 2):
        aa = math.pi * k / teeth
        rr = r if k % 2 == 0 else r * 0.78
        c.line_to(math.cos(aa) * rr, math.sin(aa) * rr)
        aa2 = math.pi * (k + 1) / teeth
        c.line_to(math.cos(aa2 - 0.05) * rr, math.sin(aa2 - 0.05) * rr)
    c.close_path()
    c.set_source_rgba(col[0], col[1], col[2], a); c.fill_preserve(); _stroke(c, 5, a)
    c.arc(0, 0, r * 0.3, 0, 2 * math.pi); _fill_stroke(c, 5, a)
    c.restore()


def cloud(c, x, y, s=1.0, a=1.0, dark=False, bolt=0.0):
    if a <= 0.01:
        return
    c.save(); c.translate(x, y); c.scale(s, s)
    c.new_path()
    for cx, cy, r in ((-80, 10, 55), (-20, -30, 70), (55, -10, 60), (95, 20, 45), (0, 25, 60)):
        c.new_sub_path(); c.arc(cx, cy, r, 0, 2 * math.pi)
    col = (0.55, 0.57, 0.62) if dark else (1, 1, 1)
    c.set_source_rgba(col[0], col[1], col[2], a); c.fill()
    for cx, cy, r, a0, a1 in ((-80, 10, 55, 100, 260), (-20, -30, 70, 190, 340), (55, -10, 60, 230, 400), (95, 20, 45, 280, 470),
                              (0, 25, 60, 20, 160)):
        c.arc(cx, cy, r, math.radians(a0), math.radians(a1)); _stroke(c, 6, a)
    if bolt > 0:
        c.move_to(0, 70); c.line_to(-26, 130); c.line_to(2, 130); c.line_to(-18, 190); c.line_to(30, 115); c.line_to(4, 115)
        c.line_to(22, 70); c.close_path()
        c.set_source_rgba(1, 0.82, 0.3, a * bolt); c.fill_preserve(); _stroke(c, 5, a * bolt)
    c.restore()


def tag(c, x, y, s, a=1.0, rot=0.0, scale=1.0):
    if a <= 0.01:
        return
    surf, tw, th = text_surface(s, "dm", 800, 44, (43, 43, 43))
    w, h = tw + 70, th + 20
    c.save(); c.translate(x, y); c.rotate(math.radians(rot)); c.scale(scale, scale)
    c.move_to(-w / 2, -h / 2 + 10); c.line_to(-w / 2 + 26, -h / 2); c.line_to(w / 2, -h / 2); c.line_to(w / 2, h / 2)
    c.line_to(-w / 2 + 26, h / 2); c.line_to(-w / 2, h / 2 - 10); c.close_path()
    c.set_source_rgba(1, 0.92, 0.85, a); c.fill_preserve(); _stroke(c, 5, a)
    c.arc(-w / 2 + 22, 0, 7, 0, 2 * math.pi); _stroke(c, 4, a)
    c.set_source_surface(surf, -tw / 2 + 12, -th / 2); c.paint_with_alpha(a)
    c.restore()


def magnifier(c, x, y, a=1.0, rot=-30):
    if a <= 0.01:
        return
    c.save(); c.translate(x, y); c.rotate(math.radians(rot))
    c.move_to(0, 46); c.line_to(0, 120); _stroke(c, 16, a, ORANGE)
    c.arc(0, 0, 46, 0, 2 * math.pi); c.set_source_rgba(0.85, 0.94, 1, a * 0.7); c.fill_preserve(); _stroke(c, 8, a)
    c.arc(-14, -14, 14, math.radians(180), math.radians(270)); _stroke(c, 5, a, (1, 1, 1))
    c.restore()


def flower(c, x, y, grow=1.0, a=1.0, col=ORANGE):
    """Sprout -> flower. grow 0..1."""
    if a <= 0.01 or grow <= 0:
        return
    h = 40 + 170 * min(1, grow * 1.3)
    c.move_to(x, y); c.curve_to(x - 10, y - h * 0.4, x + 10, y - h * 0.7, x, y - h); _stroke(c, 7, a, (0.25, 0.55, 0.3))
    for s, f in ((-1, 0.45), (1, 0.62)):
        lx, ly = x, y - h * f
        lg = min(1, grow * 2)
        c.move_to(lx, ly); c.curve_to(lx + s * 40 * lg, ly - 30 * lg, lx + s * 70 * lg, ly - 10 * lg, lx + s * 70 * lg, ly)
        c.curve_to(lx + s * 50 * lg, ly + 14 * lg, lx + s * 20 * lg, ly + 10 * lg, lx, ly)
        c.set_source_rgba(0.45, 0.72, 0.42, a); c.fill_preserve(); _stroke(c, 4, a)
    bloom = max(0, (grow - 0.55) / 0.45)
    if bloom > 0:
        for k in range(6):
            ang = 2 * math.pi * k / 6
            c.arc(x + math.cos(ang) * 28 * bloom, y - h + math.sin(ang) * 28 * bloom, 22 * bloom, 0, 2 * math.pi)
            c.set_source_rgba(col[0], col[1], col[2], a); c.fill_preserve(); _stroke(c, 4, a)
        c.arc(x, y - h, 16 * bloom, 0, 2 * math.pi); c.set_source_rgba(1, 0.85, 0.3, a); c.fill_preserve(); _stroke(c, 4, a)


def star(c, x, y, r, a=1.0, rot=0.0, col=ORANGE):
    if a <= 0.01:
        return
    c.save(); c.translate(x, y); c.rotate(math.radians(rot))
    for k in range(10):
        ang = math.pi * k / 5 - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.45
        (c.move_to if k == 0 else c.line_to)(math.cos(ang) * rr, math.sin(ang) * rr)
    c.close_path(); c.set_source_rgba(col[0], col[1], col[2], a); c.fill_preserve(); _stroke(c, 4, a)
    c.restore()


def scribble(c, pts, p, a=1.0, col=ORANGE, w=10):
    """A painted stroke that draws on (p 0..1)."""
    if a <= 0.01 or p <= 0:
        return
    n = max(2, int(len(pts) * min(1, p)))
    c.move_to(*pts[0])
    for q in pts[1:n]:
        c.line_to(*q)
    _stroke(c, w, a, col)


def map_scroll(c, x, y, w, h, p, a=1.0, path_p=1.0):
    """A map that unrolls horizontally (p 0..1) with a dotted winding path and a star at the end."""
    if a <= 0.01 or p <= 0:
        return
    ww = max(20, w * p)
    c.save(); c.translate(x, y)
    c.move_to(-ww / 2, -h / 2)
    for k in range(5):
        xx = -ww / 2 + ww * (k + 1) / 5
        c.line_to(xx, -h / 2 + (8 if k % 2 == 0 else 0))
    c.line_to(ww / 2, h / 2)
    for k in range(5):
        xx = ww / 2 - ww * (k + 1) / 5
        c.line_to(xx, h / 2 - (8 if k % 2 == 0 else 0))
    c.close_path()
    c.set_source_rgba(1, 0.96, 0.86, a); c.fill_preserve(); _stroke(c, 6, a)
    if p > 0.9:
        q = (p - 0.9) / 0.1 * path_p
        pts = [(-ww / 2 + 50 + (ww - 140) * i / 40, 35 * math.sin(i / 40 * 3 * math.pi) + 10) for i in range(41)]
        nshow = int(len(pts) * q)
        for i in range(0, nshow, 3):
            c.arc(pts[i][0], pts[i][1], 5, 0, 2 * math.pi); c.set_source_rgba(ORANGE[0], ORANGE[1], ORANGE[2], a); c.fill()
        if q >= 0.98:
            c.restore(); star(c, x + pts[-1][0] + 30, y + pts[-1][1], 26, a); return
    c.restore()


def plane(c, x, y, a=1.0, rot=-10, s=1.0):
    if a <= 0.01:
        return
    c.save(); c.translate(x, y); c.rotate(math.radians(rot)); c.scale(s, s)
    c.move_to(-60, 0); c.line_to(60, -10); c.line_to(-20, 30); c.close_path(); _fill_stroke(c, 5, a)
    c.move_to(-20, 30); c.line_to(-8, 4); c.line_to(60, -10); _stroke(c, 5, a)
    c.restore()


def heart(c, x, y, s=1.0, a=1.0, col=ORANGE):
    if a <= 0.01:
        return
    c.save(); c.translate(x, y); c.scale(s, s)
    c.move_to(0, 18); c.curve_to(-40, -10, -22, -40, 0, -20); c.curve_to(22, -40, 40, -10, 0, 18); c.close_path()
    c.set_source_rgba(col[0], col[1], col[2], a); c.fill_preserve(); _stroke(c, 4, a)
    c.restore()


def motion_lines(c, x, y, a=1.0, side=1, n=3, L=40):
    for k in range(n):
        c.move_to(x + side * 10, y - 30 + k * 30); c.line_to(x + side * (10 + L), y - 30 + k * 30)
        _stroke(c, 5, a)
