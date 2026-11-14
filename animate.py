"""Cut-out animation of the cub: walks in, stops, starts crying (10 s, 30 fps).

Usage: python3 animate.py <source.png> <out.mp4> [preview_dir]
Needs: Pillow, numpy, scipy, ffmpeg on PATH.
"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

SRC, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, DUR = 1280, 720, 30, 10.0
S = 1.25            # source -> video scale
BG = (234, 233, 229)
INK = (28, 28, 28)

src = Image.open(SRC).convert("RGB")
arr = np.asarray(src).astype(int)
lum = arr.mean(axis=2)
h0, w0 = lum.shape
yy, xx = np.mgrid[0:h0, 0:w0]

# ---------------------------------------------------------------- masks
# background = light pixels connected to the border (character interior is
# enclosed by ink outlines, so it is not reached)
light = lum > 150
lab, _ = ndimage.label(light)
border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
bgmask = np.isin(lab, list(border))
fg = ~bgmask
# drop specks far from the boy (keeps the ground strokes near him)
fg &= ~((yy < 480) & ((xx < 140) | (xx > 420)))

# face interior (white) -> dilate to include outline
whiteish = lum > 200
flab, _ = ndimage.label(whiteish & fg)
face_int = flab == flab[200, 290]
face = ndimage.binary_dilation(face_int, iterations=8)
head = fg & ((yy < 150) | face | ((xx < 205) & (yy < 215)) | ((xx > 360) & (yy < 205)))
head &= yy < 250

# shoes (ellipses) and pant legs
def ell(cx, cy, rx, ry):
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1

SPLIT = 274
HEM = 418
legzone = (yy >= HEM) & (yy < 500) & (xx > 205) & (xx < 340)
lshoe = ell(233, 510, 40, 19)
rshoe = ell(316, 510, 36, 19)
lleg = fg & ((legzone & (xx < SPLIT)) | lshoe)
rleg = fg & ((legzone & (xx >= SPLIT)) | rshoe)
ground = fg & (yy >= 488) & ~lleg & ~rleg
torso = fg & ~head & ~lleg & ~rleg & ~ground


def layer(mask, fill_holes_white=False):
    a = np.zeros((h0, w0, 4), np.uint8)
    a[..., :3] = arr
    m = mask.copy()
    a[..., 3] = (m * 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def crop_scaled(img, box):
    c = img.crop(box)
    return c.resize((round(c.width * S), round(c.height * S)), Image.LANCZOS)


# head with original eyes / mouth erased (they are redrawn per frame so the
# face can change expression); white neck backing behind it
head_rgb = arr.copy()
for (cx, cy, r) in [(244, 177.5, 11), (345.5, 181, 11)]:
    head_rgb[ell(cx, cy, r, r)] = 255
head_rgb[(yy >= 217) & (yy <= 228) & (xx >= 285) & (xx <= 310)] = 255
ha = np.zeros((h0, w0, 4), np.uint8)
ha[..., :3] = head_rgb
ha[..., 3] = head * 255
HEAD_BOX = (140, 15, 410, 252)
head_img = Image.fromarray(ha, "RGBA").crop(HEAD_BOX)
HEAD_PIVOT = (292 - HEAD_BOX[0], 245 - HEAD_BOX[1])

neck = np.zeros((h0, w0, 4), np.uint8)
neck[ell(292, 225, 55, 30) & ~ndimage.binary_dilation(torso & (lum < 100), iterations=1)] = (255, 255, 255, 255)
neck_img = Image.fromarray(neck, "RGBA")

BODY_BOX = (130, 15, 430, 535)      # common frame for torso/legs/ground
torso_img = crop_scaled(layer(torso), BODY_BOX)
neck_img = crop_scaled(neck_img, BODY_BOX)
ground_img = crop_scaled(layer(ground), BODY_BOX)
LEG_PIVOTS = {"l": (243, HEM + 4), "r": (305, HEM + 4)}
legs = {}
for k, m in (("l", lleg), ("r", rleg)):
    box = (190, HEM - 2, 360, 532)
    legs[k] = (crop_scaled(layer(m), box), box)

# reference points in body-frame (scaled) coordinates
def bf(x, y):
    return ((x - BODY_BOX[0]) * S, (y - BODY_BOX[1]) * S)

LEG_LEN = (512 - HEM) * S      # pivot -> sole


# ---------------------------------------------------------------- helpers
def smooth(e0, e1, t):
    u = min(1.0, max(0.0, (t - e0) / (e1 - e0)))
    return u * u * (3 - 2 * u)


def paste_rot(canvas, img, pivot_img, pivot_canvas, angle, sy=1.0):
    """Paste img rotated by angle (deg, CCW) about pivot_img onto canvas so
    that the pivot lands on pivot_canvas. sy squashes vertically about pivot."""
    if sy != 1.0:
        img = img.resize((img.width, max(1, round(img.height * sy))), Image.BICUBIC)
        pivot_img = (pivot_img[0], pivot_img[1] * sy)
    pad = int(max(img.size))
    big = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad))
    big.paste(img, (pad, pad))
    c = (pivot_img[0] + pad, pivot_img[1] + pad)
    rot = big.rotate(angle, resample=Image.BICUBIC, center=c)
    canvas.alpha_composite(rot, (round(pivot_canvas[0] - c[0]), round(pivot_canvas[1] - c[1])))


# ---------------------------------------------------------------- face drawing
SS = 4  # supersampling for face overlay


def face_overlay(t, cry, well, quiver, blink):
    """Overlay in head-crop source pixel coords (before scaling)."""
    w, h = head_img.size
    ov = Image.new("RGBA", (w * SS, h * SS))
    d = ImageDraw.Draw(ov)

    def P(x, y):
        return ((x - HEAD_BOX[0]) * SS, (y - HEAD_BOX[1]) * SS)

    def line(pts, width, fill=INK + (255,)):
        pts = [P(*p) for p in pts]
        d.line(pts, fill=fill, width=int(width * SS), joint="curve")
        r = width * SS / 2
        for p in (pts[0], pts[-1]):
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)

    eyes = [(244, 177.5), (345.5, 181)]
    # --- eyes
    for i, (ex, ey) in enumerate(eyes):
        if cry > 0.5:
            # squeezed shut, crying arcs  (∩ shape, slightly slanted)
            s = 1 if i == 0 else -1
            pts = []
            for k in range(13):
                a = math.pi * k / 12
                pts.append((ex - 11 * math.cos(a), ey + 3 - 6 * math.sin(a) + s * 0.15 * (k - 6)))
            line(pts, 4.2)
        elif blink > 0:
            line([(ex - 8, ey), (ex + 8, ey)], 3.5)
        else:
            r = 7.5 + 2.0 * well
            x0, y0 = P(ex - r, ey - r)
            x1, y1 = P(ex + r, ey + r)
            d.ellipse([x0, y0, x1, y1], fill=INK + (255,))
            if well > 0:
                # watery shine
                for (ox, oy, rr) in [(-2.5, -2.5, 2.6 * well), (2.6, 2.4, 1.3 * well)]:
                    a0, b0 = P(ex + ox - rr, ey + oy - rr)
                    a1, b1 = P(ex + ox + rr, ey + oy + rr)
                    d.ellipse([a0, b0, a1, b1], fill=(255, 255, 255, 255))
                # tear pooling on lower lid
                if well > 0.4:
                    pw = (well - 0.4) / 0.6
                    a0, b0 = P(ex - 9, ey + 5)
                    a1, b1 = P(ex + 9, ey + 8 + 4 * pw)
                    d.chord([a0, b0, a1, b1], 0, 180, fill=(150, 205, 240, int(230 * pw)),
                            outline=INK + (int(255 * pw),), width=int(1.5 * SS))

    # --- worried brows
    bw = max(cry, well * 0.8)
    if bw > 0:
        for i, (ex, ey) in enumerate(eyes):
            s = 1 if i == 0 else -1
            inner = (ex + s * 9, ey - 19 - 4 * bw)
            outer = (ex - s * 9, ey - 15 + 1 * bw)
            line([outer, inner], 3.4, INK + (int(255 * min(1, bw * 1.5)),))

    # --- mouth
    mx, my = 297.5, 222.5
    if cry > 0.5:
        k = cry
        open_h = (14 + 5 * math.sin(t * 2 * math.pi * 2.3) + 2 * math.sin(t * 13.0)) * k
        mw = 21 + 2.5 * math.sin(t * 9.0)
        x0, y0 = P(mx - mw, my - 6)
        x1, y1 = P(mx + mw, my + open_h + 6)
        d.rounded_rectangle([x0, y0, x1, y1], radius=int(min(mw, open_h + 6) * SS * 0.9),
                            fill=INK + (255,))
        # tongue
        tx0, ty0 = P(mx - mw * 0.55, my + open_h * 0.45 + 1)
        tx1, ty1 = P(mx + mw * 0.55, my + open_h + 5)
        d.ellipse([tx0, ty0, tx1, ty1], fill=(225, 120, 125, 255))
        # upper teeth/lip highlight
        ux0, uy0 = P(mx - mw * 0.6, my - 4)
        ux1, uy1 = P(mx + mw * 0.6, my - 1)
        d.rounded_rectangle([ux0, uy0, ux1, uy1], radius=2 * SS, fill=(255, 255, 255, 255))
    else:
        # wobbly frown line
        pts = []
        for k2 in range(15):
            u = k2 / 14 - 0.5
            y = my + quiver * (0.9 * math.sin(u * 14 + t * 40) + 4 * u * u * 4) - quiver * 2
            pts.append((mx + u * (19 + 4 * quiver), y))
        line(pts, 3.3)
    return ov.resize((w, h), Image.LANCZOS)


# ---------------------------------------------------------------- tears
rng = np.random.default_rng(7)
DROPS = []  # flying droplets: (birth, eye_index, vx, vy, size)
for i in range(70):
    b = 6.9 + rng.uniform(0, 3.1)
    side = int(rng.integers(0, 2))
    DROPS.append((b, side, (rng.uniform(40, 160)) * (-1 if side == 0 else 1),
                  -rng.uniform(80, 200), rng.uniform(4, 8)))


def drop_shape(d, x, y, r, alpha=255):
    """Teardrop pointing up at (x, y) centre of round part."""
    d.polygon([(x, y - 2.2 * r), (x - r * 0.95, y - 0.2 * r), (x + r * 0.95, y - 0.2 * r)],
              fill=(150, 205, 240, alpha))
    d.ellipse([x - r, y - r, x + r, y + r], fill=(150, 205, 240, alpha),
              outline=INK + (alpha,), width=2)
    d.line([(x - r * 0.95, y - 0.3 * r), (x, y - 2.2 * r), (x + r * 0.95, y - 0.3 * r)],
           fill=INK + (alpha,), width=2)
    d.ellipse([x - r * 0.45, y - r * 0.5, x - r * 0.05, y - r * 0.1], fill=(255, 255, 255, alpha))


def stream_layer(t, cry, size):
    """Tear streams down the cheeks in head-crop coords (scaled S later)."""
    w, h = size
    ov = Image.new("RGBA", (w * SS, h * SS))
    d = ImageDraw.Draw(ov)
    if cry <= 0:
        return ov.resize((w, h), Image.LANCZOS)
    eyes = [(244, 177.5), (345.5, 181)]
    for i, (ex, ey) in enumerate(eyes):
        s = -1 if i == 0 else 1
        x0 = ex + s * 7
        length = 52 * cry
        pts_l, pts_r = [], []
        for k in range(24):
            u = k / 23
            y = ey + 5 + u * length
            x = x0 + s * 3 * math.sin(u * 3 + t * 6) * u
            wdt = 3.0 + 3.5 * u + 1.2 * math.sin(t * 9 + u * 8 + i)
            pts_l.append(((x - wdt - HEAD_BOX[0]) * SS, (y - HEAD_BOX[1]) * SS))
            pts_r.append(((x + wdt - HEAD_BOX[0]) * SS, (y - HEAD_BOX[1]) * SS))
        poly = pts_l + pts_r[::-1]
        d.polygon(poly, fill=(150, 205, 240, 235))
        d.line(pts_l, fill=INK + (255,), width=int(2 * SS))
        d.line(pts_r, fill=INK + (255,), width=int(2 * SS))
        # drip at end that grows and falls
        ph = (t * 1.6 + i * 0.5) % 1.0
        ex2 = (x0 + s * 3 * math.sin(3 + t * 6) - HEAD_BOX[0]) * SS
        ey2 = (ey + 5 + length + 4 + 30 * ph * ph - HEAD_BOX[1]) * SS
        r = (5 + 3 * ph) * SS
        d.ellipse([ex2 - r, ey2 - r, ex2 + r, ey2 + r], fill=(150, 205, 240, 235),
                  outline=INK + (255,), width=int(2 * SS))
    return ov.resize((w, h), Image.LANCZOS)


# ---------------------------------------------------------------- scene
def make_bg():
    bg = Image.new("RGB", (W, H), BG)
    noise = np.random.default_rng(1).normal(0, 3.0, (H, W, 1))
    a = np.clip(np.asarray(bg).astype(float) + noise, 0, 255).astype(np.uint8)
    bg = Image.fromarray(a)
    d = ImageDraw.Draw(bg)
    r = np.random.default_rng(3)
    # sparse hand-drawn floor dashes in the same ink style
    for _ in range(26):
        x = r.uniform(0, W)
        y = GROUND_Y + r.uniform(-6, 40)
        ln = r.uniform(12, 70)
        d.line([(x, y), (x + ln, y + r.uniform(-1.5, 1.5))], fill=(70, 70, 70), width=int(r.integers(2, 4)))
    return bg.convert("RGBA")


SOLE_Y_SRC = 524
BODY_TOP = H - 50 - (SOLE_Y_SRC - BODY_BOX[1]) * S  # canvas y of body frame top
GROUND_Y = BODY_TOP + (SOLE_Y_SRC - BODY_BOX[1]) * S
background = make_bg()

T_WALK_END = 5.2
STEP = 0.55                    # seconds per step (half cycle)


def walk_amp(t):
    return 15.0 * (1 - smooth(4.55, T_WALK_END, t))


def leg_angles(t):
    ph = math.pi * t / STEP
    a = walk_amp(t)
    return a * math.sin(ph), -a * math.sin(ph), ph


# integrate body x so the stance foot never slides
frames = int(DUR * FPS)
xs = []
x = -40.0
prev = None
SUB = 8
for f in range(frames):
    for k in range(SUB):
        t = (f + k / SUB) / FPS
        al, ar, _ = leg_angles(t)
        fl = LEG_LEN * math.sin(math.radians(al))
        fr = LEG_LEN * math.sin(math.radians(ar))
        if prev is not None:
            dl, dr = fl - prev[0], fr - prev[1]
            stance = min(dl, dr)          # the foot moving backwards (relative)
            x += max(0.0, -stance)
        prev = (fl, fr)
    xs.append(x)
# map so he stops a bit right of centre
shift = 660 - xs[-1]
xs = [v + shift for v in xs]

body_w = torso_img.width

proc = subprocess.Popen(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
     "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
     "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
     "-movflags", "+faststart", OUT],
    stdin=subprocess.PIPE)

for f in range(frames):
    t = f / FPS
    al, ar, ph = leg_angles(t)
    amp = walk_amp(t)

    # crying envelope
    well = smooth(5.9, 6.7, t)
    quiver = smooth(5.6, 6.2, t) * (1 - smooth(6.75, 6.85, t))
    cry = smooth(6.75, 7.1, t)
    blink = 1 if (5.35 < t < 5.47) or (1.8 < t < 1.92) else 0

    # body motion
    bob = -4.5 * S * (1 - abs(math.cos(ph))) * (amp / 15.0) + 4.5 * S * (amp / 15.0) * 0.5
    sob = 0.0
    if cry > 0:
        # sobbing: quick hiccup heaves
        sob = cry * (3.2 * max(0, math.sin(t * 2 * math.pi * 1.6)) ** 3 + 1.0 * math.sin(t * 40))
    sway = 1.2 * math.sin(ph) * (amp / 15.0)
    ox = xs[f] - body_w / 2
    oy = BODY_TOP + bob

    frame = background.copy()
    # shadow/ground strokes travel with him (no bob)
    frame.alpha_composite(ground_img, (round(ox), round(BODY_TOP)))

    # legs: back leg first
    for k, ang in (("r", ar), ("l", al)):
        img, box = legs[k]
        pv_src = LEG_PIVOTS[k]
        pv_img = ((pv_src[0] - box[0]) * S, (pv_src[1] - box[1]) * S)
        pv_can = (ox + (pv_src[0] - BODY_BOX[0]) * S, oy + (pv_src[1] - BODY_BOX[1]) * S)
        # lift the swinging leg (moving forward) a little
        dang = math.cos(ph) * (1 if k == "l" else -1)
        lift = 1 - 0.07 * max(0.0, dang) * (amp / 15.0)
        paste_rot(frame, img, pv_img, pv_can, ang, sy=lift)

    # torso (with slight sway + sob heave, pivot at hips)
    hip = bf(272, 420)
    torso_layer = Image.new("RGBA", torso_img.size)
    torso_layer.alpha_composite(neck_img)
    torso_layer.alpha_composite(torso_img)
    tsy = 1 - 0.012 * sob / 3.2
    paste_rot(frame, torso_layer, hip, (ox + hip[0], oy + hip[1] + 0.0), sway * 0.6, sy=tsy)
    neck_drop = torso_img.height * (1 - tsy) - 0  # how much the shoulders moved

    # head
    look_down = 3.0 * smooth(5.3, 6.0, t)
    head_tilt = 0.0
    if cry > 0:
        head_tilt = cry * (2.2 * math.sin(t * 2 * math.pi * 0.9) + 0.8 * math.sin(t * 37))
    head_bob_walk = 1.2 * S * abs(math.sin(ph)) * (amp / 15.0)
    hface = head_img.copy()
    hface.alpha_composite(face_overlay(t, cry, well, quiver, blink))
    tears = stream_layer(t, cry, hface.size)
    hface.alpha_composite(tears)
    hs = hface.resize((round(hface.width * S), round(hface.height * S)), Image.LANCZOS)
    hp = (HEAD_PIVOT[0] * S, HEAD_PIVOT[1] * S)
    neck_can = bf(292, 245)
    # torso sway rotates around hip; move head pivot accordingly
    r = math.radians(sway * 0.6)
    dx, dy = neck_can[0] - hip[0], (neck_can[1] - hip[1]) * tsy
    nx = hip[0] + dx * math.cos(r) + dy * math.sin(r)
    ny = hip[1] - dx * math.sin(r) + dy * math.cos(r)
    paste_rot(frame, hs, hp,
              (ox + nx, oy + ny + look_down * S - head_bob_walk * 0 + sob * 0.6),
              sway * 1.4 - look_down * 0.0 + head_tilt)

    # flying tear droplets + sob marks (canvas space)
    if cry > 0:
        d = ImageDraw.Draw(frame)
        hx, hy = ox + nx, oy + ny
        for (b, side, vx, vy, sz) in DROPS:
            age = t - b
            if 0 <= age < 0.9:
                ex, ey = [(244, 177.5), (345.5, 181)][side]
                sx = hx + (ex - 292 + (-12 if side == 0 else 12)) * S + vx * age
                sy_ = hy + (ey - 245) * S + vy * age + 420 * age * age
                alpha = int(255 * (1 - age / 0.9))
                drop_shape(d, sx, sy_, sz, alpha)
        # little "sob" emanata lines near the head
        if (t * 1.6) % 1.0 < 0.5:
            for s in (-1, 1):
                cx = hx + s * 150 * S
                cy = hy - 110 * S
                for k in range(3):
                    a = math.radians(-90 + s * (35 + k * 25))
                    r0, r1 = 10, 26
                    d.line([(cx + r0 * math.cos(a) * -s * -1, cy + r0 * math.sin(a)),
                            (cx + r1 * math.cos(a) * -s * -1, cy + r1 * math.sin(a))],
                           fill=INK, width=4)

    proc.stdin.write(frame.convert("RGB").tobytes())
    if len(sys.argv) > 3 and f % 30 == 0:   # optional preview stills
        frame.convert("RGB").save(f"{sys.argv[3]}/f{f:03d}.png")

proc.stdin.close()
proc.wait()
print("done", OUT)
