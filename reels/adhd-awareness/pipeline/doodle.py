# Rigged doodle characters (the boy and the girl from the reference) and simple line props, drawn with cairo.
# Style kept from the reference: black hand-drawn lines on white, round head, dot eyes, U smile; boy with messy hair,
# ears, T-shirt and shorts; girl with bangs, top bun and long ponytail, A-line dress; stick arms with little
# three-finger hands, stick legs with small feet.
import math
import cairo

INK = (0.07, 0.07, 0.07)
PAPER = (1, 1, 1)
ORANGE = (240 / 255, 133 / 255, 62 / 255)
CHAR = (43 / 255, 43 / 255, 43 / 255)
CREAM = (253 / 255, 246 / 255, 238 / 255)

BASE = dict(x=540, y=1330, R=92, lean=0.0, bob=0.0, sq=1.0, scale=1.0, flip=1,
            tilt=0.0, turn=0.0, lookx=0.0, looky=0.0, eyes="open", blink=0.0, mouth="smile", brows=None, mouth_open=0.0,
            la1=25.0, la2=0.0, ra1=25.0, ra2=0.0, ll=4.0, rl=4.0, lk=0.0, rk=0.0, pony=0.0, alpha=1.0, blush=0.0)


def _set_ink(c, a=1.0, col=INK):
    c.set_source_rgba(col[0], col[1], col[2], a)


def _stroke(c, w, a=1.0, col=INK):
    _set_ink(c, a, col)
    c.set_line_width(w)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.stroke()


def _fill_stroke(c, w, a=1.0, fill=PAPER, col=INK):
    c.set_source_rgba(fill[0], fill[1], fill[2], a)
    c.fill_preserve()
    _stroke(c, w, a, col)


def _limb(c, x, y, ang1, len1, ang2, len2, w, a):
    """Two-segment stick limb. Angles in degrees, 0 = straight down, positive = outward (caller mirrors)."""
    r1 = math.radians(ang1)
    x1, y1 = x + math.sin(r1) * len1, y + math.cos(r1) * len1
    r2 = math.radians(ang1 + ang2)
    x2, y2 = x1 + math.sin(r2) * len2, y1 + math.cos(r2) * len2
    c.move_to(x, y)
    c.curve_to(x + (x1 - x) * 0.6, y + (y1 - y) * 0.6, x1, y1, x1 + (x2 - x1) * 0.15, y1 + (y2 - y1) * 0.15)
    c.line_to(x2, y2)
    _stroke(c, w, a)
    return x2, y2, ang1 + ang2


def _hand(c, x, y, ang, R, w, a, side):
    """Little three-finger fork, pointing along the arm."""
    for d in (-34, 0, 34):
        r = math.radians(ang + d)
        L = R * (0.2 if d else 0.24)
        c.move_to(x, y)
        c.line_to(x + math.sin(r) * L, y + math.cos(r) * L)
        _stroke(c, w * 0.85, a)


def _foot(c, x, y, R, w, a, side):
    c.move_to(x, y)
    c.line_to(x + side * R * 0.28, y + R * 0.02)
    _stroke(c, w, a)


def _face(c, P, R, w, a):
    t = P["turn"]
    ex = 0.30 * R
    fx = t * 0.22 * R
    lx, ly = P["lookx"] * 0.06 * R, P["looky"] * 0.06 * R
    eye_y = -0.06 * R
    kind = P["eyes"]
    blink = P["blink"]
    for s in (-1, 1):
        cx, cy = fx + s * ex + lx, eye_y + ly
        if kind in ("closed",) or blink > 0.85:
            c.move_to(cx - 0.09 * R, cy)
            c.curve_to(cx - 0.04 * R, cy + 0.05 * R, cx + 0.04 * R, cy + 0.05 * R, cx + 0.09 * R, cy)
            _stroke(c, w * 0.8, a)
        elif kind == "happy":
            c.move_to(cx - 0.1 * R, cy + 0.03 * R)
            c.curve_to(cx - 0.05 * R, cy - 0.07 * R, cx + 0.05 * R, cy - 0.07 * R, cx + 0.1 * R, cy + 0.03 * R)
            _stroke(c, w * 0.8, a)
        else:
            sc = 1.45 if kind == "wide" else 1.0
            h = 0.12 * R * sc * (1 - blink)
            c.save(); c.translate(cx, cy); c.scale(0.075 * R * sc, max(0.01, h))
            c.arc(0, 0, 1, 0, 2 * math.pi); c.restore()
            _set_ink(c, a); c.fill()
            if kind == "wide":
                c.arc(cx - 0.02 * R, cy - 0.04 * R, 0.022 * R, 0, 2 * math.pi)
                c.set_source_rgba(1, 1, 1, a); c.fill()
    br = P["brows"]
    if br:
        for s in (-1, 1):
            cx = fx + s * ex + lx
            y0 = eye_y - 0.24 * R
            if br == "worried":
                c.move_to(cx - s * 0.11 * R, y0 + 0.02 * R); c.line_to(cx + s * 0.1 * R, y0 + 0.07 * R)
            elif br == "angry":
                c.move_to(cx - s * 0.11 * R, y0 + 0.08 * R); c.line_to(cx + s * 0.1 * R, y0 + 0.01 * R)
            else:                                            # raised
                c.move_to(cx - 0.1 * R, y0 - 0.02 * R); c.curve_to(cx - 0.04 * R, y0 - 0.08 * R, cx + 0.04 * R, y0 - 0.08 * R,
                                                                   cx + 0.1 * R, y0 - 0.02 * R)
            _stroke(c, w * 0.75, a)
    if P["blush"] > 0:
        for s in (-1, 1):
            c.arc(fx + s * 0.5 * R, 0.2 * R, 0.1 * R, 0, 2 * math.pi)
            c.set_source_rgba(ORANGE[0], ORANGE[1], ORANGE[2], 0.35 * P["blush"] * a); c.fill()
    m = P["mouth"]
    my = 0.26 * R
    mw = 0.42 * R
    if m == "smile":
        c.move_to(fx - mw, my - 0.06 * R)
        c.curve_to(fx - mw * 0.6, my + 0.32 * R, fx + mw * 0.6, my + 0.32 * R, fx + mw, my - 0.06 * R)
        _stroke(c, w, a)
        for s in (-1, 1):                                    # the little dimple ticks at the ends of the smile
            c.move_to(fx + s * mw * 0.9, my - 0.12 * R); c.line_to(fx + s * mw * 1.08, my - 0.0 * R)
            _stroke(c, w * 0.7, a)
    elif m == "big":
        c.move_to(fx - mw, my - 0.04 * R)
        c.curve_to(fx - mw * 0.6, my + 0.42 * R, fx + mw * 0.6, my + 0.42 * R, fx + mw, my - 0.04 * R)
        c.close_path()
        _fill_stroke(c, w, a)
    elif m == "flat":
        c.move_to(fx - mw * 0.55, my + 0.06 * R); c.line_to(fx + mw * 0.55, my + 0.06 * R)
        _stroke(c, w, a)
    elif m == "frown":
        c.move_to(fx - mw * 0.6, my + 0.14 * R)
        c.curve_to(fx - mw * 0.3, my - 0.06 * R, fx + mw * 0.3, my - 0.06 * R, fx + mw * 0.6, my + 0.14 * R)
        _stroke(c, w, a)
    elif m == "o":
        c.save(); c.translate(fx, my + 0.08 * R); c.scale(0.1 * R, 0.13 * R)
        c.arc(0, 0, 1, 0, 2 * math.pi); c.restore()
        _stroke(c, w * 0.9, a)
    elif m == "wavy":
        c.move_to(fx - mw * 0.6, my + 0.08 * R)
        for k in range(1, 7):
            xx = fx - mw * 0.6 + k * mw * 1.2 / 6
            c.line_to(xx, my + 0.08 * R + (0.04 * R if k % 2 else -0.04 * R))
        _stroke(c, w * 0.85, a)
    elif m == "talk":
        o = 0.06 + 0.22 * P["mouth_open"]
        c.move_to(fx - mw * 0.7, my)
        c.curve_to(fx - mw * 0.4, my + o * R * 1.6, fx + mw * 0.4, my + o * R * 1.6, fx + mw * 0.7, my)
        c.curve_to(fx + mw * 0.3, my + o * R * 0.4, fx - mw * 0.3, my + o * R * 0.4, fx - mw * 0.7, my)
        _fill_stroke(c, w * 0.9, a)


def _boy_head(c, P, R, w, a):
    t = P["turn"]
    # ears
    for s in (-1, 1):
        ex = s * R * 0.98 + t * 0.1 * R
        c.move_to(ex, -0.12 * R)
        c.curve_to(ex + s * 0.22 * R, -0.2 * R, ex + s * 0.24 * R, 0.12 * R, ex, 0.1 * R)
        _fill_stroke(c, w, a)
    c.arc(0, 0, R, 0, 2 * math.pi)
    _fill_stroke(c, w, a)
    # messy hair: short curly strokes on top
    for k, ang in enumerate((-58, -32, -8, 16, 40, 62)):
        r = math.radians(ang)
        x0, y0 = math.sin(r) * R * 0.98, -math.cos(r) * R * 0.98
        x1, y1 = math.sin(r) * R * 1.32, -math.cos(r) * R * 1.32
        cx_ = (x0 + x1) / 2 + (0.12 * R if k % 2 else -0.1 * R)
        cy_ = (y0 + y1) / 2
        c.move_to(x0, y0); c.curve_to(cx_, cy_, cx_, cy_, x1 + (0.06 * R if k % 2 else -0.06 * R), y1)
        _stroke(c, w * 0.85, a)
    _face(c, P, R, w, a)


def _girl_head(c, P, R, w, a):
    c.arc(0, 0, R, 0, 2 * math.pi)
    _fill_stroke(c, w, a)
    # hair line over the top, bangs
    c.arc(0, 0.02 * R, R * 1.02, math.radians(200), math.radians(340))
    _stroke(c, w, a)
    for k, xx in enumerate((-0.32, -0.14, 0.04, 0.22)):
        c.move_to(xx * R, -0.72 * R - abs(xx) * 0.3 * R)
        c.line_to(xx * R + 0.04 * R, -0.42 * R - abs(xx) * 0.2 * R)
        _stroke(c, w * 0.8, a)
    # bun / tie at the top right, then the long ponytail (sways with `pony`)
    bx, by = 0.36 * R, -1.02 * R
    c.arc(bx, by, 0.12 * R, 0, 2 * math.pi)
    _fill_stroke(c, w * 0.9, a)
    p = math.radians(P["pony"])
    def rot(x, y):
        dx, dy = x - bx, y - by
        return bx + dx * math.cos(p) - dy * math.sin(p), by + dx * math.sin(p) + dy * math.cos(p)
    # comma-shaped ponytail: sweeps up and right from the tie to a soft point, lower edge flows back
    up1, up2 = rot(bx + 0.25 * R, by - 0.62 * R), rot(bx + 1.0 * R, by - 0.78 * R)
    tip = rot(bx + 1.75 * R, by - 0.42 * R)
    lo1, lo2 = rot(bx + 1.35 * R, by - 0.18 * R), rot(bx + 0.55 * R, by + 0.08 * R)
    c.move_to(bx - 0.04 * R, by - 0.06 * R)
    c.curve_to(up1[0], up1[1], up2[0], up2[1], tip[0], tip[1])
    c.curve_to(lo1[0], lo1[1], lo2[0], lo2[1], bx + 0.08 * R, by + 0.08 * R)
    _fill_stroke(c, w, a)
    _face(c, P, R, w, a)


def draw_char(c, kind, P0):
    P = dict(BASE); P.update(P0)
    a = P["alpha"]
    if a <= 0.01:
        return
    R = P["R"] * P["scale"]
    w = max(2.5, R * 0.075)
    c.save()
    c.translate(P["x"], P["y"] + P["bob"])
    c.rotate(math.radians(P["lean"]))
    c.scale(P["flip"] / P["sq"] ** 0.5, P["sq"])
    if kind == "boy":
        hip_y, sh_y, head_y = -1.72 * R, -4.15 * R, -5.33 * R
        tw, bw = 0.52 * R, 0.55 * R
        leg_len = 1.72 * R
        arm = (0.95 * R, 0.9 * R)
        sh_x = 0.5 * R
    else:
        hip_y, sh_y, head_y = -1.42 * R, -3.75 * R, -4.92 * R
        tw, bw = 0.4 * R, 0.98 * R
        leg_len = 1.42 * R
        arm = (0.9 * R, 0.85 * R)
        sh_x = 0.38 * R
    # legs
    for s, ang, kn in ((-1, P["ll"], P["lk"]), (1, P["rl"], P["rk"])):
        hx = s * (0.22 * R if kind == "boy" else 0.24 * R)
        x2, y2, _ = _limb(c, hx, hip_y, s * ang, leg_len * 0.5, -s * kn, leg_len * 0.5, w, a)
        _foot(c, x2, y2, R, w, a, s)
    # torso
    if kind == "boy":
        c.move_to(-0.5 * R, hip_y - 0.05 * R); c.line_to(-0.52 * R, hip_y - 0.95 * R); c.line_to(0.52 * R, hip_y - 0.95 * R)
        c.line_to(0.5 * R, hip_y - 0.05 * R); c.line_to(0.04 * R, hip_y - 0.05 * R); c.line_to(0.0, hip_y - 0.42 * R)
        c.line_to(-0.04 * R, hip_y - 0.05 * R); c.close_path()
        _fill_stroke(c, w, a)
        c.move_to(-0.5 * R, hip_y - 0.95 * R); c.line_to(-tw, sh_y); c.line_to(tw, sh_y); c.line_to(0.5 * R, hip_y - 0.95 * R)
        c.close_path()
        _fill_stroke(c, w, a)
    else:
        c.move_to(-tw, sh_y)
        c.curve_to(-tw * 1.1, sh_y + 0.8 * R, -bw * 0.8, hip_y - 0.4 * R, -bw, hip_y + 0.02 * R)
        c.curve_to(-bw * 0.4, hip_y + 0.14 * R, bw * 0.4, hip_y + 0.1 * R, bw, hip_y - 0.02 * R)
        c.curve_to(bw * 0.8, hip_y - 0.4 * R, tw * 1.1, sh_y + 0.8 * R, tw, sh_y)
        c.close_path()
        _fill_stroke(c, w, a)
    # neck
    c.move_to(0, sh_y); c.line_to(0, head_y + R * 0.98)
    _stroke(c, w, a)
    # arms (angles: 0 = down, 90 = straight out, 160 = up)
    for s, a1, a2 in ((-1, P["la1"], P["la2"]), (1, P["ra1"], P["ra2"])):
        x2, y2, ang = _limb(c, s * sh_x, sh_y + 0.08 * R, s * a1, arm[0], s * a2, arm[1], w, a)
        _hand(c, x2, y2, ang, R, w, a, s)
    # head
    c.save()
    c.translate(0, head_y)
    c.rotate(math.radians(P["tilt"]))
    (_boy_head if kind == "boy" else _girl_head)(c, P, R, w, a)
    c.restore()
    c.restore()


def head_pos(kind, P0):
    """Screen position of the head centre (for thought bubbles, symbols etc.)."""
    P = dict(BASE); P.update(P0)
    R = P["R"] * P["scale"]
    hy = (-5.33 if kind == "boy" else -4.92) * R * P["sq"]
    r = math.radians(P["lean"])
    return P["x"] - hy * math.sin(r), P["y"] + P["bob"] + hy * math.cos(r), R


def hand_pos(kind, P0, side=1):
    P = dict(BASE); P.update(P0)
    R = P["R"] * P["scale"]
    sh_y = (-4.15 if kind == "boy" else -3.75) * R + 0.08 * R
    sh_x = (0.5 if kind == "boy" else 0.38) * R * side
    arm = (0.95 * R, 0.9 * R) if kind == "boy" else (0.9 * R, 0.85 * R)
    a1 = P["ra1"] if side > 0 else P["la1"]
    a2 = P["ra2"] if side > 0 else P["la2"]
    r1 = math.radians(side * a1)
    x1, y1 = sh_x + math.sin(r1) * arm[0], sh_y + math.cos(r1) * arm[0]
    r2 = math.radians(side * (a1 + a2))
    x2, y2 = x1 + math.sin(r2) * arm[1], y1 + math.cos(r2) * arm[1]
    x2 *= P["flip"]
    lr = math.radians(P["lean"])
    X = x2 * math.cos(lr) - y2 * math.sin(lr)
    Y = x2 * math.sin(lr) + y2 * math.cos(lr)
    return P["x"] + X, P["y"] + P["bob"] + Y
