# Frame renderer: decode -> face-aware reframe (gentle zoom, face held at one height) -> soft cuts -> graphics +
# captions -> cream brand frame -> x264.
import os, sys, json, subprocess
import numpy as np
from PIL import Image
import design3 as D
import faces
import gfx2 as G
from timeline3 import SPEED, FPS, SRC_FRAMES
from anim2 import clamp, ease_io

W = os.environ["WORK"]
OUT_W, OUT_H = 1080, 1920
CREAM_RGB = G.CREAM[:3]
GRADE = "fps=30,eq=contrast=1.03:saturation=1.04,unsharp=5:5:0.25:3:3:0.0"
FACE_Y = 1062            # output height of the face centre: leaves the wall above her head for graphics
XF = 4                   # cross-dissolve length (frames) on every cut, so jump cuts read as soft
FACE_W_REF = 190

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

# sentence of each block, and the span of each sentence (for a slow push-in that runs across inner cuts)
piece_of = np.zeros(TOTAL, int)
for k, p in enumerate(D.PIECES):
    piece_of[p["o_in"]:p["o_out"]] = k
piece_of[N_EXP:] = len(D.PIECES) - 1
label_of = [D.PIECES[piece_of[b["o_in"]]]["label"] for b in BLK]
labels = []
for l in label_of:
    if l not in labels:
        labels.append(l)
SPAN = {l: (min(p["o_in"] for p in D.PIECES if p["label"] == l), max(p["o_out"] for p in D.PIECES if p["label"] == l)) for l in labels}
SPAN[labels[-1]] = (SPAN[labels[-1]][0], TOTAL)

# per-sentence zoom: normalise face size, alternate a small step between sentences (subtle reframing, never a punch)
Z_SENT = {}
for k, l in enumerate(labels):
    fw = np.median([FACES[i]["w"] for i, x in enumerate(label_of) if x == l])
    z0 = clamp(1.20 * (FACE_W_REF / fw) ** 0.5, 1.14, 1.28)
    Z_SENT[l] = z0 * (1.05 if k % 2 else 1.0)

CUTS = [b["o_in"] for b in BLK[1:]]
TRACK = None


def build_track(step=3):
    """Per-frame smoothed face box (YuNet on the graded source frame), cached on disk."""
    path = f"{W}/track.json"
    key = f"v3:{TOTAL}:{SPEED}:{len(BLK)}:{BLK[3]['o_in']}"
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
        base = np.array([fc["cx"], fc["cy"], fc["w"], fc["h"]], np.float32)
        ns = [n for n in sorted(raw) if a <= n < e]
        if len(ns) < 2:
            trk[a:e] = base
            continue
        pts = np.array([raw[n] for n in ns], np.float32)
        med = np.array([np.median(pts[max(0, k - 2):k + 3], 0) for k in range(len(ns))])
        full = np.stack([np.interp(np.arange(a, e), ns, med[:, c]) for c in range(4)], 1)
        sm = np.zeros_like(full)
        for k in range(len(full)):
            lo, hi = max(0, k - 10), min(len(full), k + 11)
            sm[k] = full[lo:hi].mean(0)
        trk[a:e] = sm
    json.dump(dict(key=key, track=trk.tolist()), open(path, "w"))
    return trk


def cam(i, n):
    """Camera for block i at output frame n: zoom z and the source point (ax, ay) that lands at output (tx, ty)."""
    l = label_of[i]
    a, e = SPAN[l]
    prog = clamp((n - a) / max(1, e - a))
    z = Z_SENT[l] * (1 + 0.025 * ease_io(prog))                                  # slow push-in through each sentence
    fc = FACES[i]
    if TRACK is not None and n < len(TRACK) and TRACK[n][3] > 0:
        ax, ay = float(TRACK[n][0]), float(TRACK[n][1])
    else:
        ax, ay = fc["cx"], fc["cy"]
    ty = min(max(FACE_Y, OUT_H - (OUT_H - ay) * z), ay * z)                      # never reveal past the source edges
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


def video_layer(n, dec):
    i = int(blk_of[n])
    shot, f = FM[n]
    img = warp(dec.get(shot, f), cam(i, n))
    for cc in CUTS:
        k = n - cc
        if 0 <= k < XF:                                       # outgoing take keeps rolling for a few frames under the dissolve
            ip = int(blk_of[cc - 1])
            sh0, f0 = FM[cc - 1]
            f_out = min(int(f0 + (k + 1) * SPEED), SRC_FRAMES[sh0] - 1)
            prev = warp(grab_frame(sh0, f_out), cam(ip, cc - 1))
            a = ease_io((k + 1) / (XF + 1))
            img = Image.blend(prev, img, a)
            break
    return img


TRACK = build_track()


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
