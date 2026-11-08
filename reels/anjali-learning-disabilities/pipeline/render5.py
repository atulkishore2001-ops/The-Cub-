# Calm renderer: steady face-anchored framing (one zoom per camera set-up, slow-following camera), straight cuts where
# the clip / camera set-up changes, morph-style soft cuts only where a pause inside one take was shortened, an even grade with a soft key light on the speaker,
# graphics + captions, fade to the cream brand frame -> x264.
import os, sys, json, subprocess
import numpy as np
import cv2
from PIL import Image
import design5 as D
import faces
import gfx2 as G
from timeline3 import SPEED, FPS, SRC_FRAMES, scene_id
from anim2 import clamp, ease_io

W = os.environ["WORK"]
OUT_W, OUT_H = 1080, 1920
CREAM_RGB = G.CREAM[:3]
GRADE = "fps=30,eq=contrast=1.03:saturation=1.04,unsharp=5:5:0.25:3:3:0.0"
FACE_Y = 1080            # output height of the face centre (wall above stays free for the cards)
FACE_W_REF = 190
MORPH = 10               # frames of soft blend on a cut inside one camera set-up
SMOOTH = 40              # camera follow window (+/- frames): the frame drifts with her, it never chases gestures

BLK = D.BLK
FACES = faces.block_faces(BLK, W, f"{W}/faces.json")
FM = D.FM
TOTAL = D.TOTAL_FRAMES
N_EXP = len(FM)
sh, f = FM[-1]
while len(FM) < TOTAL:                       # after the last word the take keeps rolling under the fade to cream
    f = min(f + SPEED, SRC_FRAMES[sh] - 1)
    FM.append((sh, int(f)))
BLK[-1]["o_out"] = max(BLK[-1]["o_out"], TOTAL)
blk_of = np.zeros(TOTAL, int)
for i, b in enumerate(BLK):
    blk_of[b["o_in"]:min(b["o_out"], TOTAL)] = i

# one zoom per camera set-up (shot + scene), sized so her face is about the same size in every set-up
SCN = [b["scene"] for b in BLK]
Z_SCN = {}
for sc in set(SCN):
    fw = np.median([FACES[i]["w"] for i in range(len(BLK)) if SCN[i] == sc])
    Z_SCN[sc] = float(clamp(1.21 * (FACE_W_REF / fw) ** 0.5, 1.14, 1.30))
CUTS = [b["o_in"] for b in BLK[1:]]
TRACK = None

# per-shot grade: tiny skin-tone balance (measured on her face) so the three clips match; key light on the subject
SKIN = {1: (173.8, 110.2, 83.4), 2: (169.5, 112.2, 88.3), 3: (177.6, 108.1, 79.1)}
_m = np.mean(list(SKIN.values()), 0)
SKIN_GAIN = {k: np.clip(_m / np.array(v), 0.95, 1.05).astype(np.float32) for k, v in SKIN.items()}


def _key_mask():
    yy, xx = np.mgrid[0:OUT_H, 0:OUT_W].astype(np.float32)
    cx, cy = OUT_W / 2, FACE_Y + 170
    d = ((xx - cx) / 380) ** 2 + ((yy - cy) / 560) ** 2
    m = np.exp(-d * 1.4)                                   # soft oval over face and upper body, no visible edge
    return m[:, :, None]


KEY = _key_mask()


def grade(img, shot):
    a = np.asarray(img).astype(np.float32)
    g = 1 + KEY * (SKIN_GAIN[shot] - 1)
    a = a * g
    a = a * (1 + 0.07 * KEY) + KEY * 10 * (1 - a / 255)       # +7% light on her, a little more in the shadows
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def build_track(step=3):
    """Per-frame face centre (YuNet), heavily smoothed within each continuous piece; cached on disk."""
    path = f"{W}/track4.json"
    key = f"v4:{TOTAL}:{SPEED}:{len(BLK)}:{BLK[3]['o_in']}:{SMOOTH}"
    if os.path.exists(path):
        c = json.load(open(path))
        if c.get("key") == key:
            return np.array(c["track"], np.float32)
    dec = Decoder()
    raw = {}
    for n in range(0, TOTAL, step):
        shot, f = FM[n]
        fc0 = FACES[int(blk_of[n])]
        bx = faces.face_in(np.asarray(dec.get(shot, f))[:, :, ::-1].copy(), prior=(fc0["cx"], fc0["cy"], fc0["w"], fc0["h"]))
        if bx:
            raw[n] = [bx[0] + bx[2] / 2, bx[1] + bx[3] / 2, bx[2], bx[3]]
    trk = np.zeros((TOTAL, 4), np.float32)
    for i, b in enumerate(BLK):
        a, e = b["o_in"], min(b["o_out"], TOTAL)
        fc = FACES[i]
        ns = [n for n in sorted(raw) if a <= n < e]
        if len(ns) < 2:
            trk[a:e] = [fc["cx"], fc["cy"], fc["w"], fc["h"]]
            continue
        pts = np.array([raw[n] for n in ns], np.float32)
        med = np.array([np.median(pts[max(0, k - 3):k + 4], 0) for k in range(len(ns))])
        full = np.stack([np.interp(np.arange(a, e), ns, med[:, c]) for c in range(4)], 1)
        sm = np.zeros_like(full)
        for k in range(len(full)):
            lo, hi = max(0, k - SMOOTH), min(len(full), k + SMOOTH + 1)
            wts = np.hanning(2 * SMOOTH + 3)[1:-1][SMOOTH - (k - lo):SMOOTH + (hi - k)]
            sm[k] = (full[lo:hi] * wts[:, None]).sum(0) / wts.sum()
        trk[a:e] = sm
    json.dump(dict(key=key, track=trk.tolist()), open(path, "w"))
    return trk


def cam(i, n):
    z = Z_SCN[SCN[i]]
    if TRACK is not None and n < len(TRACK) and TRACK[n][3] > 0:
        ax, ay = float(TRACK[n][0]), float(TRACK[n][1])
    else:
        ax, ay = FACES[i]["cx"], FACES[i]["cy"]
    ty = min(max(FACE_Y, OUT_H - (OUT_H - ay) * z), ay * z)
    tx = min(max(OUT_W / 2, OUT_W - (OUT_W - ax) * z), ax * z)
    return dict(z=z, tx=tx, ty=ty, ax=ax, ay=ay)


def warp(src, c):
    z = c["z"]
    return src.transform((OUT_W, OUT_H), Image.AFFINE, (1 / z, 0, c["ax"] - c["tx"] / z, 0, 1 / z, c["ay"] - c["ty"] / z),
                         resample=Image.BICUBIC)


_grab_cache = {}


def grab_frame(shot, f):
    key = (shot, f)
    if key not in _grab_cache:
        if len(_grab_cache) > 80:
            _grab_cache.clear()
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


_DIS = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)


def morph(a_img, b_img, alpha):
    """Optical-flow morph between two aligned frames: both are warped toward each other, then blended."""
    A, B = np.asarray(a_img), np.asarray(b_img)
    s = 0.25
    ga = cv2.cvtColor(cv2.resize(A, None, fx=s, fy=s, interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
    gb = cv2.cvtColor(cv2.resize(B, None, fx=s, fy=s, interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
    fab = cv2.resize(_DIS.calc(ga, gb, None), (OUT_W, OUT_H)) / s
    fba = cv2.resize(_DIS.calc(gb, ga, None), (OUT_W, OUT_H)) / s
    fab = cv2.GaussianBlur(fab, (0, 0), 6); fba = cv2.GaussianBlur(fba, (0, 0), 6)
    yy, xx = np.mgrid[0:OUT_H, 0:OUT_W].astype(np.float32)
    aw = cv2.remap(A, xx + alpha * fba[..., 0], yy + alpha * fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    bw = cv2.remap(B, xx + (1 - alpha) * fab[..., 0], yy + (1 - alpha) * fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    out = aw.astype(np.float32) * (1 - alpha) + bw.astype(np.float32) * alpha
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def _same_setup(shot, f0, f1):
    return scene_id(shot, f0) == scene_id(shot, f1)


def video_layer(n, dec):
    i = int(blk_of[n])
    shot, f = FM[n]
    img = grade(warp(dec.get(shot, f), cam(i, n)), shot)
    for cc in CUTS:
        if SCN[int(blk_of[cc - 1])] != SCN[int(blk_of[cc])]:
            continue                                          # new camera set-up / clip: a clean straight cut in the pause
        L = MORPH
        k = n - (cc - L // 2)
        if not 0 <= k < L:
            continue
        ia, ib = int(blk_of[cc - 1]), int(blk_of[cc])
        sha, fa = FM[cc - 1]
        shb, fb = FM[cc]
        if n < cc:                                            # before the cut: borrow the incoming take's lead-in
            fbn = int(round(fb - (cc - n) * SPEED))
            if fbn < 0 or not _same_setup(shb, fbn, fb):
                fbn = fb
            a_img = img
            b_img = grade(warp(grab_frame(shb, fbn), cam(ib, cc)), shb)
        else:                                                 # after the cut: the outgoing take keeps rolling
            fan = int(round(fa + (n - cc + 1) * SPEED))
            if fan >= SRC_FRAMES[sha] or not _same_setup(sha, fa, fan):
                fan = fa
            a_img = grade(warp(grab_frame(sha, fan), cam(ia, cc - 1)), sha)
            b_img = img
        alpha = ease_io((k + 0.5) / L)
        return morph(a_img, b_img, alpha)
    return img


def render_parts(n, dec):
    t = n / FPS
    k = D.cream_alpha(t)
    if k >= 0.999:
        base = Image.new("RGB", (OUT_W, OUT_H), CREAM_RGB)
    else:
        base = video_layer(n, dec)
        if k > 0.001:
            base = Image.blend(base, Image.new("RGB", (OUT_W, OUT_H), CREAM_RGB), k)
    ov = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    for s in D.SPRITES:
        if s.active(t):
            s.render(ov, t)
    D.CAPTIONS.render(ov, t)
    return base, ov


def render_frame(n, dec):
    base, ov = render_parts(n, dec)
    out = base.convert("RGBA")
    out.alpha_composite(ov)
    return out.convert("RGB")


def qa_faces(step=2):
    """No graphic or caption pixel may touch the face, hair or chin (face box grown 30% up, 10% sides, 5% down)."""
    dec = Decoder()
    bad, n_chk, miss = [], 0, 0
    for n in range(0, TOTAL, step):
        t = n / FPS
        if t >= D.T_CREAM0:
            break
        base, ov = render_parts(n, dec)
        i = int(blk_of[n]); c = cam(i, n)
        pr = (c["tx"], c["ty"], FACES[i]["w"] * c["z"], FACES[i]["h"] * c["z"])
        fb = faces.face_in(np.asarray(base)[:, :, ::-1].copy(), prior=pr, tol=320)
        if fb is None:
            miss += 1
            continue
        n_chk += 1
        x, y, w, h = fb
        x0, x1 = max(0, int(x - 0.10 * w)), min(OUT_W, int(x + 1.10 * w))
        y0, y1 = max(0, int(y - 0.30 * h)), min(OUT_H, int(y + 1.05 * h))
        a = np.asarray(ov.getchannel("A"))[y0:y1, x0:x1]
        if a.max() > 24:
            bad.append((n, round(t, 2), (int(x), int(y), int(w), int(h)), "graphic over face (alpha %d)" % a.max()))
    return bad, n_chk, miss


TRACK = build_track()


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
        bad, n, miss = qa_faces(int(sys.argv[2]) if len(sys.argv) > 2 else 2)
        print("checked", n, "frames (face not detected on", miss, "); violations:", len(bad))
        for b in bad[:60]:
            print(b)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--info":
        print("zoom per set-up:", {k: round(v, 3) for k, v in Z_SCN.items()})
        print("cuts at", [round(c / FPS, 2) for c in CUTS])
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
