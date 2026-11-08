# Animated float/sink experiment: a water tank, objects dropped in, ripples and bubbles. Brand colours only.
import math
from PIL import Image, ImageDraw
import gfx2 as G
from anim2 import clamp, ease_io, ease_out

SS = 2
W_, H_ = 700, 440            # sprite size
TX0, TX1 = 60, 640           # tank x
TOP, BOT = 150, 410          # tank y (top rim / floor)
LW = 9


def _surface_y(level):
    return BOT - (BOT - TOP - 20) * level


def _wave(x, t, amp, y0):
    return y0 + amp * (math.sin(x * 0.045 + t * 3.1) + 0.5 * math.sin(x * 0.09 - t * 2.3))


def make(t_fill0, t_fill1, level0, level1, drops, fade_obj_at=None):
    """drops: list of dict(kind, x, t, r) with kind in ball|stone|block. Returns img(t)."""
    drops = sorted(drops, key=lambda d: d["t"])

    def obj_state(d, t, surf, level_now):
        """returns (x, y, rot, submerged_fraction, settled) for an object at time t."""
        dt = t - d["t"]
        r = d["r"]
        if dt < 0:
            return None
        g = 2600.0
        y_start = 20.0
        y_impact = surf - r * (0.2 if d["kind"] != "stone" else 0.4)
        t_imp = math.sqrt(max(1e-6, 2 * (y_impact - y_start) / g))
        if dt < t_imp:
            return d["x"], y_start + 0.5 * g * dt * dt, 0.0, 0.0, False
        u = dt - t_imp
        if d["kind"] == "stone":
            end = BOT - LW - r * 0.9
            v0 = g * t_imp * 0.22
            y = y_impact + (end - y_impact) * (1 - math.exp(-u * 3.4)) + (v0 * u * math.exp(-u * 5))
            y = min(y, end + 0)
            return d["x"], y, 0.0, 1.0, u > 1.2
        # floaters: damped bob around their rest depth
        rest = surf - r * (0.55 if d["kind"] == "ball" else 0.30)
        y = rest + (y_impact + r * 0.9 - rest) * math.exp(-u * 3.2) * math.cos(u * 11) * 0.9
        rot = (math.sin(u * 5.5) * 7 * math.exp(-u * 1.4)) if d["kind"] == "block" else 0.0
        return d["x"], y, rot, 0.45, u > 1.6

    def img(t):
        level = level0 + (level1 - level0) * ease_io(clamp((t - t_fill0) / (t_fill1 - t_fill0)))
        surf0 = _surface_y(level)
        s = SS
        im = Image.new("RGBA", (W_ * s, H_ * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        # water body
        pts = [(x * s, _wave(x, t, 3.0, surf0) * s) for x in range(TX0 + LW // 2, TX1 - LW // 2 + 1, 8)]
        poly = pts + [((TX1 - LW) * s, (BOT - LW) * s), ((TX0 + LW) * s, (BOT - LW) * s)]
        d.polygon(poly, fill=G.a(G.ORANGE, 70))
        d.line(pts, fill=G.ORANGE, width=int(5 * s))
        # objects (drawn inside water so they read as submerged)
        ripples = []
        for dr in drops:
            st = obj_state(dr, t, surf0, level)
            if st is None:
                continue
            x, y, rot, sub, settled = st
            r = dr["r"]
            if dr["kind"] == "ball":
                d.ellipse(((x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s), fill=G.ORANGE)
                d.ellipse(((x - r * 0.55) * s, (y - r * 0.6) * s, (x - r * 0.1) * s, (y - r * 0.2) * s), fill=G.a(G.CREAM, 150))
            elif dr["kind"] == "stone":
                d.ellipse(((x - r) * s, (y - r * 0.82) * s, (x + r) * s, (y + r * 0.82) * s), fill=G.CHAR)
            else:
                bl = Image.new("RGBA", (int(2.4 * r * s), int(2.4 * r * s)), (0, 0, 0, 0))
                bd = ImageDraw.Draw(bl)
                c = bl.width / 2
                bd.rounded_rectangle((c - r * s, c - r * s, c + r * s, c + r * s), radius=int(r * 0.25 * s), fill=G.CREAM, outline=G.CHAR, width=int(5 * s))
                bl = bl.rotate(rot, resample=Image.BICUBIC)
                im.alpha_composite(bl, (int(x * s - c), int(y * s - c)))
            # splash ripple at impact
            dt = t - dr["t"]
            imp = math.sqrt(max(1e-6, 2 * ((surf0 - r * 0.2) - 20) / 2600.0))
            ti = dt - imp
            if 0 < ti < 1.0:
                for k in range(2):
                    q = clamp(ti * 1.3 - k * 0.22)
                    if 0 < q < 1:
                        rr = 20 + 90 * ease_out(q)
                        ripples.append((x, rr, 1 - q))
            # bubbles trailing the sinking stone
            if dr["kind"] == "stone" and 0 < ti < 1.4:
                for k in range(5):
                    bq = clamp(ti * 0.9 - k * 0.12)
                    if 0 < bq < 1:
                        bx = x + 12 * math.sin(k * 2.3 + ti * 6)
                        by = y - 10 - bq * 80
                        if by > surf0:
                            rr = 4 + 2 * (k % 2)
                            d.ellipse(((bx - rr) * s, (by - rr) * s, (bx + rr) * s, (by + rr) * s), fill=G.a(G.CREAM, 230))
        for x, rr, al in ripples:
            d.ellipse(((x - rr) * s, (surf0 - rr * 0.16) * s, (x + rr) * s, (surf0 + rr * 0.16) * s), outline=G.a(G.ORANGE, int(210 * al)), width=int(3 * s))
        # tank glass outline (front)
        d.line([((TX0) * s, TOP * s), ((TX0) * s, (BOT - 30) * s)], fill=G.CHAR, width=LW * s)
        d.line([((TX1) * s, TOP * s), ((TX1) * s, (BOT - 30) * s)], fill=G.CHAR, width=LW * s)
        d.arc(((TX0) * s, (BOT - 60) * s, (TX0 + 60) * s, BOT * s), 90, 180, fill=G.CHAR, width=LW * s)
        d.arc(((TX1 - 60) * s, (BOT - 60) * s, (TX1) * s, BOT * s), 0, 90, fill=G.CHAR, width=LW * s)
        d.line([((TX0 + 30) * s, (BOT - LW // 2) * s), ((TX1 - 30) * s, (BOT - LW // 2) * s)], fill=G.CHAR, width=LW * s)
        for xx in (TX0, TX1):  # rim caps
            d.rounded_rectangle(((xx - 26) * s, (TOP - 8) * s, (xx + 26) * s, (TOP + 6) * s), radius=7 * s, fill=G.CHAR)
        return im.resize((W_, H_), Image.LANCZOS)

    return img
