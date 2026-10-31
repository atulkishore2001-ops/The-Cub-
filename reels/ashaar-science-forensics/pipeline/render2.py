# Frame renderer: decode -> face-aware reframe -> split-screen layout / push transitions -> graphics + captions -> x264.
import os, sys, json, subprocess
import numpy as np
from PIL import Image, ImageDraw
import design2 as D
import faces
import gfx2 as G
from timeline2 import SPEED, FPS
from anim2 import clamp, ease_io, ease_out

W = os.environ["WORK"]
OUT_W, OUT_H = 1080, 1920
CREAM_RGB = G.CREAM[:3]
GRADE = "fps=30,eq=contrast=1.03:saturation=1.05,unsharp=5:5:0.25:3:3:0.0"
TARGET_FACE_W = 300
PUSH_N = 7

BLK = D.BLK
FACES = faces.block_faces(BLK, W, f"{W}/faces.json")
FM = D.FM
TOTAL = D.TOTAL_FRAMES
while len(FM) < TOTAL:                      # hold the last source frame (covered by the promo graphics anyway)
    FM.append(FM[-1])
BLK[-1]["o_out"] = max(BLK[-1]["o_out"], TOTAL)
blk_of = np.zeros(TOTAL, int)
for i, b in enumerate(BLK):
    blk_of[b["o_in"]:min(b["o_out"], TOTAL)] = i

# per-block base zoom: normalise face size, and alternate zoom on jump cuts inside one location
alt, z_base = [], []
for i, b in enumerate(BLK):
    same = i > 0 and BLK[i - 1]["loc"] == b["loc"]
    alt.append((not alt[-1]) if same else False)
    fw = FACES[i]["w"]
    z0 = clamp(1 + 0.6 * (TARGET_FACE_W / fw - 1), 1.0, 1.16)
    z_base.append(z0 * (1.07 if alt[-1] else 1.0))
PUSH_AT = {}
for i, b in enumerate(BLK):
    if i and BLK[i - 1]["loc"] != b["loc"]:
        PUSH_AT[b["o_in"]] = i


TRACK = None


def build_track(step=3):
    """Per-frame smoothed face box for the explainer (YuNet on the graded source frame), cached on disk."""
    path = f"{W}/track.json"
    n_exp = min(TOTAL, int(D.PROMO_T0 * FPS) + 2)
    key = f"v2:{n_exp}:{SPEED}:{len(BLK)}:{BLK[3]['o_in']}"
    if os.path.exists(path):
        c = json.load(open(path))
        if c.get("key") == key:
            return np.array(c["track"], np.float32)
    dec = Decoder()
    raw = {}
    for n in range(0, n_exp, step):
        shot, f = FM[n]
        fc0 = FACES[int(blk_of[n])]
        bx = faces.face_in(np.asarray(dec.get(shot, f))[:, :, ::-1].copy(), prior=(fc0["cx"], fc0["cy"], fc0["w"], fc0["h"]))
        if bx:
            raw[n] = [bx[0] + bx[2] / 2, bx[1] + bx[3] / 2, bx[2], bx[3]]
    trk = np.zeros((TOTAL, 4), np.float32)
    for i, b in enumerate(BLK):
        a, e = b["o_in"], min(b["o_out"], TOTAL)
        fc = FACES[i]
        base = np.array([fc["cx"], fc["cy"], fc["w"], fc["h"]], np.float32)
        ns = [n for n in sorted(raw) if a <= n < e]
        if len(ns) < 2:
            trk[a:e] = base
            continue
        pts = np.array([raw[n] for n in ns], np.float32)
        med = np.array([np.median(pts[max(0, k - 2):k + 3], 0) for k in range(len(ns))])      # drop outliers
        full = np.stack([np.interp(np.arange(a, e), ns, med[:, c]) for c in range(4)], 1)
        sm = np.zeros_like(full)
        for k in range(len(full)):
            lo, hi = max(0, k - 8), min(len(full), k + 9)
            sm[k] = full[lo:hi].mean(0)
        trk[a:e] = sm
    json.dump(dict(key=key, track=trk.tolist()), open(path, "w"))
    return trk


def cam(i, n, prog=None, H=None):
    """Camera for block i at output frame n. Returns dict(z, tx, ty, ax, ay)."""
    t = n / FPS
    b = BLK[i]; fc = FACES[i]
    z = z_base[i]
    if prog is None:
        prog = (n - b["o_in"]) / max(1, b["o_out"] - b["o_in"])
    z *= 1 + 0.03 * prog                                                       # slow push-in
    for tp, amt in D.PUNCH:
        if b["o_in"] / FPS - 0.01 <= tp < b["o_out"] / FPS and t >= tp:
            z *= 1 + amt * ease_out(clamp((t - tp) / 0.25))
    z = min(z, 1.30)
    H = D.panel_h(t) if H is None else H
    ax, ay = (float(TRACK[n][0]), float(TRACK[n][1])) if TRACK is not None and n < len(TRACK) and TRACK[n][3] > 0 else (fc["cx"], fc["cy"])
    h = fc["h"]                                                                # block-median face height (robust to leaning)
    m = ease_io(clamp(H / 300.0))
    z = 1 + (z - 1) * (1 - 0.65 * m)                                           # calmer framing in split-screen
    ty_full = min(max(ay, 410 + 0.85 * h * z), ay * z)                          # headroom above the hair for top graphics
    ty_split = H + 70 + 0.85 * h * z                                           # face sits below the cream panel
    ty = ty_full + (ty_split - ty_full) * m
    ty = max(min(ty, H + ay * z), OUT_H - (OUT_H - ay) * z)
    lo, hi = OUT_W - (OUT_W - ax) * z, ax * z
    tx = min(max(OUT_W / 2, lo), hi)
    return dict(z=z, tx=tx, ty=ty, ax=ax, ay=ay)


def warp(src, c):
    z = c["z"]
    return src.transform((OUT_W, OUT_H), Image.AFFINE, (1 / z, 0, c["ax"] - c["tx"] / z, 0, 1 / z, c["ay"] - c["ty"] / z),
                         resample=Image.BICUBIC)


def hblur(arr, k):
    if k < 3:
        return arr
    k |= 1
    p = np.pad(arr, ((0, 0), (k // 2 + 1, k // 2), (0, 0)), mode="edge").astype(np.float32)
    cs = np.cumsum(p, axis=1)
    return (cs[:, k:] - cs[:, :-k]) / k


_grab_cache = {}


def grab_frame(shot, f):
    """One-off decode of a single (graded) source frame, cached — used for the frozen outgoing side of a push."""
    key = (shot, f)
    if key not in _grab_cache:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{f / FPS:.4f}", "-i", f"{W}/shot{shot}.mp4", "-vf", GRADE,
                              "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        _grab_cache[key] = Image.frombuffer("RGB", (OUT_W, OUT_H), raw, "raw", "RGB", 0, 1)
    return _grab_cache[key]


class Decoder:
    def __init__(self):
        self.proc, self.key, self.pos, self.last = None, None, None, None

    def get(self, shot, f):
        if self.key != shot or self.pos is None or f < self.pos - 1 or f > self.pos + 10:
            if self.proc:
                self.proc.kill()
            self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f / FPS:.4f}", "-i", f"{W}/shot{shot}.mp4", "-vf", GRADE,
                                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            self.key, self.pos, self.last = shot, f, None
        while self.pos <= f:
            buf = self.proc.stdout.read(OUT_W * OUT_H * 3)
            if len(buf) < OUT_W * OUT_H * 3:
                break
            self.last = buf
            self.pos += 1
        return Image.frombuffer("RGB", (OUT_W, OUT_H), self.last, "raw", "RGB", 0, 1)


_mask_cache = {}


def top_round_mask(w, h, r):
    key = (w, h, r)
    if key not in _mask_cache:
        s = 3
        m = Image.new("L", (w * s, (h + r * 2) * s), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w * s - 1, (h + r * 2) * s), r * s, fill=255)
        _mask_cache[key] = m.resize((w, h + r * 2), Image.LANCZOS).crop((0, 0, w, h))
    return _mask_cache[key]


def video_layer(n, dec, H):
    i = int(blk_of[n])
    shot, f = FM[n]
    c = cam(i, n, H=H)
    if n in PUSH_AT or any(0 <= n - cc < PUSH_N for cc in PUSH_AT):
        cc = max(k for k in PUSH_AT if k <= n)
        if n - cc < PUSH_N:
            ip = PUSH_AT[cc]
            p = ease_io((n - cc + 1) / PUSH_N)
            sh0, f0 = FM[cc - 1]
            out_img = warp(grab_frame(sh0, f0), cam(ip - 1, cc - 1, prog=1.0, H=H))
            in_img = warp(dec.get(shot, f), c)
            xo = int(round(-p * OUT_W))
            comp = Image.new("RGB", (OUT_W, OUT_H))
            comp.paste(out_img, (xo, 0)); comp.paste(in_img, (xo + OUT_W, 0))
            k = int(110 * np.sin(np.pi * p))
            if k >= 3:
                comp = Image.fromarray(np.clip(hblur(np.asarray(comp), k), 0, 255).astype(np.uint8))
            return comp
    return warp(dec.get(shot, f), c)


TRACK = build_track()


def render_parts(n, dec):
    t = n / FPS
    H = D.panel_h(t)
    if H >= OUT_H - 2:
        base = Image.new("RGB", (OUT_W, OUT_H), CREAM_RGB)
    else:
        layer = video_layer(n, dec, H)
        if H < 2:
            base = layer
        else:
            Hi = int(round(H))
            base = Image.new("RGB", (OUT_W, OUT_H), CREAM_RGB)
            r = int(min(46, H / 5))
            base.paste(layer.crop((0, Hi, OUT_W, OUT_H)), (0, Hi), top_round_mask(OUT_W, OUT_H - Hi, r))
            a = np.asarray(base).astype(np.float32)
            y0 = max(0, Hi - 30)
            ramp = np.linspace(0, 1, Hi - y0)[:, None, None]
            a[y0:Hi] *= (1 - 0.07 * ramp ** 2)
            base = Image.fromarray(a.astype(np.uint8))
    ov = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    for s in D.SPRITES:
        if s.active(t):
            s.render(ov, t)
    D.CAPTIONS.render(ov, t)
    return base, ov, H


def render_frame(n, dec):
    base, ov, _ = render_parts(n, dec)
    out = base.convert("RGBA")
    out.alpha_composite(ov)
    return out.convert("RGB")


def qa_faces(step=2):
    """Check no graphic/caption pixel falls on Ashaar's face and that the cream panel never overlaps it."""
    dec = Decoder()
    bad = []
    n_chk = 0
    for n in range(0, TOTAL, step):
        t = n / FPS
        if t >= D.PROMO_T0 - 0.05:
            break
        if any(0 <= n - cc < PUSH_N + 1 for cc in PUSH_AT):
            continue                                                           # mid-push frames: two shots on screen
        base, ov, H = render_parts(n, dec)
        i = int(blk_of[n]); c = cam(i, n, H=H)
        pr = (c["tx"], c["ty"], FACES[i]["w"] * c["z"], FACES[i]["h"] * c["z"])
        fb = faces.face_in(np.asarray(base)[:, :, ::-1].copy(), prior=pr, tol=320)
        if fb is None:
            continue
        n_chk += 1
        x, y, w, h = fb
        x0, x1 = max(0, int(x - 0.10 * w)), min(OUT_W, int(x + 1.10 * w))
        y0, y1 = max(0, int(y - 0.30 * h)), min(OUT_H, int(y + 1.05 * h))
        a = np.asarray(ov.getchannel("A"))[y0:y1, x0:x1]
        why = []
        if a.max() > 24:
            why.append("graphic over face (alpha %d)" % a.max())
        if H > 4 and (y - 0.30 * h) < H - 2:
            why.append("panel edge %.0f vs hair-top %.0f" % (H, y - 0.30 * h))
        if why:
            bad.append((n, round(t, 2), (int(x), int(y), int(w), int(h)), "; ".join(why)))
    return bad, n_chk


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        outdir = sys.argv[3]
        os.makedirs(outdir, exist_ok=True)
        dec = Decoder()
        for tt in sys.argv[2].split(","):
            n = int(round(float(tt) * FPS))
            render_frame(n, dec).save(f"{outdir}/f_{float(tt):06.2f}.png")
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--qa":
        bad, n = qa_faces(int(sys.argv[2]) if len(sys.argv) > 2 else 2)
        print("checked", n, "frames; violations:", len(bad))
        for b in bad[:60]:
            print(b)
        return
    out = sys.argv[1]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "15",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    dec = Decoder()
    for n in range(TOTAL):
        enc.stdin.write(render_frame(n, dec).tobytes())
        if n % 150 == 0:
            print(f"frame {n}/{TOTAL}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("done", out)


if __name__ == "__main__":
    main()
