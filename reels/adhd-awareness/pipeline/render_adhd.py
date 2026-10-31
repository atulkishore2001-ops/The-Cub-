# Renders the ADHD doodle reel: cairo stage (background, characters, props) + PIL text cards, captions and the
# standard The Cub closing (logo + tagline), encoded with x264.
import os, sys, math, subprocess, re
import numpy as np
import cairo
from PIL import Image, ImageDraw
import doodle as D
import props as PR
import story as S
import gfx2 as G
from anim2 import Captions, clamp, ease_io, ease_out

W_, H_ = 1080, 1920
FPS = S.FPS
TOTAL = int(round(S.T_END * FPS))
BRAND = os.environ.get("BRAND", "/tmp/claude-0/-home-user-The-Cub-/6a3c4bc0-104a-5ca4-adb7-aceaf8503d24/scratchpad/brand")
TEXT_Y = 330
CAP_Y = 1530


# ---------------------------------------------------------------- captions (word for word, from the voiceover)
def caption_words():
    out, seg = [], 0
    ws = S.VO_WORDS
    i = 0
    while i < len(ws):
        w = dict(ws[i]); txt = w["w"]
        if txt.lower().startswith("sanji"):
            txt = "Saanchi" + txt[5:]
        if txt == "RCI" and i + 1 < len(ws) and ws[i + 1]["w"].lower().startswith("certified"):
            txt = "RCI-certified"; w["e"] = ws[i + 1]["e"]; i += 1
        if txt in ("Special", "Educator"):
            txt = txt.lower()
        w["w"] = txt
        w["seg"] = str(seg)
        out.append(dict(w=txt, s=w["s"], e=w["e"], seg=str(seg)))
        if txt[-1] in ".?!":
            seg += 1
        i += 1
    return out


CAPTIONS = Captions(caption_words(), y=CAP_Y, hide=[(S.T_CREAM0 + 0.1, S.T_END + 1)], size=48, max_chars=28, max_words=5)


# ---------------------------------------------------------------- top text cards
def rich(parts, size=60):
    runs = []
    for s, st in parts:
        f = G.font("pfi", 600, int(size * 1.12)) if st == "pf" else G.font("dm", 700, size)
        runs.append((s, f, G.ORANGE if st == "pf" else G.CHAR))
    asc = max(f.getmetrics()[0] for _, f, _ in runs); desc = max(f.getmetrics()[1] for _, f, _ in runs)
    w = int(sum(f.getlength(s) for s, f, _ in runs)) + 24
    im = Image.new("RGBA", (w, asc + desc + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 12
    for s, f, c in runs:
        d.text((x, 10 + asc), s, font=f, fill=c, anchor="ls"); x += f.getlength(s)
    bb = im.getchannel("A").getbbox()
    return im.crop((bb[0] - 2, bb[1] - 2, bb[2] + 2, bb[3] + 2))


def card(content, px=46, py=28):
    im = G.rounded(content.width + 2 * px, content.height + 2 * py, 38, G.a(G.WHITE, 248))
    im.alpha_composite(content, (px, py))
    return G.shadow(im, (0, 8), 18, 40)


_card_cache = {}


def text_card(kind, t):
    if kind == "NAME":
        key = kind
        if key not in _card_cache:
            n1 = G.text("Saanchi", "dm", 800, 64, G.CHAR)
            n2 = G.text("RCI-certified Special Educator", "dm", 500, 38, G.a(G.CHAR, 200))
            _card_cache[key] = card(G.col([n1, n2], gap=10))
        return _card_cache[key]
    if kind == "CCE":
        items = [("Curious", S.W("curious")), ("Creative", S.W("creative")), ("Full of energy", S.W("full"))]
        pills = []
        for s, tt in items:
            p = ease_out(clamp((t - tt + 0.1) / 0.35))
            im = G.pill(G.text(s, "dm", 700, 46, G.WHITE), G.a(G.ORANGE, 255), 30, 16)
            pills.append(G.with_alpha(im, p) if p > 0 else Image.new("RGBA", im.size, (0, 0, 0, 0)))
        return G.shadow(G.row(pills, gap=16), (0, 6), 14, 30)
    if kind == "FLAW":
        key = kind
        if key not in _card_cache:
            _card_cache[key] = (rich([("ADHD isn’t a ", "n")]), rich([("flaw to fix", "pf")]))
        a_, b_ = _card_cache[key]
        im = G.row([a_, b_], gap=4)
        p = ease_io(clamp((t - S.W("flaw") - 0.5) / 0.4))
        if p > 0:
            d = ImageDraw.Draw(im)
            y = im.height * 0.55
            d.line((a_.width + 4, y, a_.width + 4 + b_.width * p, y), fill=G.CHAR, width=7)
        return card(im)
    key = str(kind)
    if key not in _card_cache:
        size = 60
        im = card(rich(kind, size))
        while im.width > 1000 and size > 40:                  # long lines shrink to stay inside the frame
            size -= 2
            im = card(rich(kind, size))
        _card_cache[key] = im
    return _card_cache[key]


def draw_texts(ov, t):
    for t0, t1, kind in S.TEXTS:
        if not (t0 <= t < t1):
            continue
        a = ease_out(clamp((t - t0) / 0.4)) * clamp((t1 - t) / 0.35)
        if a <= 0.01:
            continue
        im = text_card(kind, t)
        dy = int((1 - ease_out(clamp((t - t0) / 0.4))) * 12)
        ov.alpha_composite(G.with_alpha(im, a), (540 - im.width // 2, TEXT_Y - im.height // 2 + dy))


# ---------------------------------------------------------------- closing (same as brand/outro)
def _wipe(im, p, feather=140):
    if p >= 1:
        return im
    m = Image.new("L", im.size, 0)
    x = int((im.width + feather) * p)
    grad = Image.linear_gradient("L").rotate(90).resize((feather, im.height))
    m.paste(255, (0, 0, max(0, x - feather), im.height)); m.paste(grad, (x - feather, 0))
    out = im.copy()
    out.putalpha(Image.fromarray((np.asarray(im.getchannel("A")).astype(np.uint16) * np.asarray(m) // 255).astype(np.uint8)))
    return out


LOGO = Image.open(f"{BRAND}/logo_full.png").convert("RGBA")
LOGO = LOGO.resize((420, int(420 * LOGO.height / LOGO.width)), Image.LANCZOS)
T_LOGO = S.T_CREAM0 + 0.65
T_TAG = T_LOGO + 0.85
_tf = G.font("pfi", 500, 60)
_asc, _desc = _tf.getmetrics()
TAG = Image.new("RGBA", (int(_tf.getlength("Every Child Deserves To Be Seen")) + 24, _asc + _desc + 20), (0, 0, 0, 0))
ImageDraw.Draw(TAG).text((12, 10 + _asc), "Every Child Deserves To Be Seen", font=_tf, fill=G.CHAR, anchor="ls")
TAG = TAG.crop(TAG.getchannel("A").getbbox())


def draw_outro(ov, t):
    p = clamp((t - T_LOGO) / 1.1)
    if p > 0:
        s = 0.94 + 0.06 * ease_out(p)
        im = LOGO.resize((int(LOGO.width * s), int(LOGO.height * s)), Image.LANCZOS) if s < 0.999 else LOGO
        im = G.with_alpha(im, ease_io(clamp(p * 1.3)))
        ov.alpha_composite(im, (540 - im.width // 2, 820 - im.height // 2))
    p = clamp((t - T_TAG) / 1.15)
    if p > 0:
        im = G.with_alpha(_wipe(TAG, ease_io(p)), clamp(p * 2.5))
        dy = 12 * (1 - ease_out(clamp((t - T_TAG) / 1.0)))
        ov.alpha_composite(im, (540 - im.width // 2, int(1130 - im.height / 2 + dy)))
    if t >= T_TAG + 0.7:
        w = max(2, int(110 * ease_io(clamp((t - T_TAG - 0.7) / 0.6))))
        u = G.underline(w, 6)
        ov.alpha_composite(u, (540 - w // 2, 1209))


# ---------------------------------------------------------------- stage
def draw_stage(t):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_, H_)
    c = cairo.Context(surf)
    c.set_source_rgb(*D.CREAM); c.paint()
    g = S.glow(t)
    if g > 0:                                                     # warm light for the hopeful second half
        rg = cairo.RadialGradient(540, 820, 50, 540, 820, 900)
        rg.add_color_stop_rgba(0, 1.0, 0.86, 0.68, 0.55 * g); rg.add_color_stop_rgba(1, 1.0, 0.86, 0.68, 0)
        c.set_source(rg); c.paint()
    # ground: a soft hand-drawn line
    c.move_to(40, S.GROUND + 8)
    for k in range(1, 21):
        c.line_to(40 + k * 50, S.GROUND + 8 + 2.5 * math.sin(k * 1.3))
    D._stroke(c, 5, 0.18)
    poses = {"girl": S.girl_pose(t), "boy": S.pose("boy", t)}
    for name, P in poses.items():                                 # contact shadows
        if -100 < P["x"] < 1180 and P["alpha"] > 0.01:
            lift = clamp(-P["bob"] / 260)
            c.save(); c.translate(P["x"], S.GROUND + 10); c.scale(1, 0.18)
            c.arc(0, 0, 95 * (1 - 0.4 * lift), 0, 2 * math.pi); c.restore()
            c.set_source_rgba(0.17, 0.17, 0.17, 0.10 * P["alpha"] * (1 - 0.6 * lift)); c.fill()
    back, front = [], []
    for t0, t1, fn, fin, fout in S.PROPS:
        if t0 <= t < t1 + 0.0:
            a = clamp((t - t0) / fin) if fin > 0 else 1.0
            a *= clamp((t1 - t) / fout) if fout > 0 else 1.0
            if a > 0.01:
                front.append((fn, a))
    for name in ("girl", "boy"):
        P = poses[name]
        if -300 < P["x"] < 1380:
            D.draw_char(c, name, P)
    for fn, a in front:
        fn(c, t, a)
    surf.flush()
    buf = np.ndarray((H_, W_, 4), np.uint8, surf.get_data()).copy()
    rgb = buf[..., [2, 1, 0]]
    return Image.fromarray(rgb, "RGB")


def render_frame(n):
    t = n / FPS
    base = draw_stage(t).convert("RGBA")
    k = S.cream_alpha(t)
    if k > 0.001:
        base = Image.blend(base, Image.new("RGBA", (W_, H_), G.CREAM), k)
    ov = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    draw_texts(ov, t)
    CAPTIONS.render(ov, t)
    if t >= T_LOGO - 0.05:
        draw_outro(ov, t)
    base.alpha_composite(ov)
    return base.convert("RGB")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        os.makedirs(sys.argv[3], exist_ok=True)
        for tt in sys.argv[2].split(","):
            render_frame(int(round(float(tt) * FPS))).save(f"{sys.argv[3]}/f_{float(tt):06.2f}.png")
        return
    out = sys.argv[1]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W_}x{H_}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
                            "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for n in range(TOTAL):
        enc.stdin.write(render_frame(n).tobytes())
        if n % 300 == 0:
            print(f"frame {n}/{TOTAL}", flush=True)
    enc.stdin.close(); enc.wait()
    print("done", out)


if __name__ == "__main__":
    main()
