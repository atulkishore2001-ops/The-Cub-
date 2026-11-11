# Renders the reel picture: steady framing per section (two framings that alternate at each section join, like the
# jump cuts in the reference), soft optical-flow morph cuts where a pause was shortened inside one flow of speech,
# a light warm grade, title / captions / name card, and the closing logo reveal. Writes WORK/video_only.mp4.
#   python render.py                 full render
#   python render.py --stills 1,5,9  preview frames into WORK/stills
import os, sys, json, subprocess
import numpy as np
import cv2
from PIL import Image
import gfx as G

WORK = os.environ["WORK"]
TL = json.load(open(f"{WORK}/timeline.json"))
FPS, SPEED = TL["fps"], TL["speed"]
OW, OH = 1080, 1920
ZOOM = {"close": 1.60, "medium": 1.36}
FACE_Y = {"close": 560, "medium": 610}       # output height of the face centre
PIECES = TL["pieces"]
NTOT = TL["total_frames"]
MORPH = 8                                     # frames of soft blend on a cut inside one section

# ---------------------------------------------------------------- face anchor per section (median of a few samples)
_det = cv2.FaceDetectorYN.create(os.environ.get("MODELS", "models") + "/yunet.onnx", "", (OW, OH), 0.6, 0.3, 5000)


def grab(shot, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", f"{WORK}/shot{shot}.mp4", "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(OH, OW, 3)


def anchors():
    path = f"{WORK}/anchors.json"
    if os.path.exists(path):
        return {int(k): v for k, v in json.load(open(path)).items()}
    out = {}
    for si in sorted(set(p["sec"] for p in PIECES)):
        ps = [p for p in PIECES if p["sec"] == si]
        ts = []
        for p in ps:
            ts += list(np.linspace(p["a"] + 0.1, p["b_audio"] - 0.1, max(2, int((p["b_audio"] - p["a"]) / 1.2))))
        boxes = []
        for t in ts:
            _, f = _det.detect(cv2.cvtColor(grab(ps[0]["shot"], t), cv2.COLOR_RGB2BGR))
            if f is None:
                continue
            f = [r for r in f if r[2] > 120 and 400 < r[1] + r[3] / 2 < 1200]
            if f:
                r = max(f, key=lambda r: r[-1] * r[2]); boxes.append([r[0] + r[2] / 2, r[1] + r[3] / 2, r[2], r[3]])
        m = np.median(np.array(boxes), 0)
        out[si] = dict(cx=float(m[0]), cy=float(m[1]), w=float(m[2]), n=len(boxes))
    json.dump(out, open(path, "w"), indent=0)
    return out


ANCH = anchors()


def cam(p):
    z = ZOOM[p["zoom"]]; a = ANCH[p["sec"]]
    ww, wh = OW / z, OH / z
    x0 = min(max(a["cx"] - ww / 2, 0), OW - ww)
    y0 = min(max(a["cy"] - FACE_Y[p["zoom"]] / z, 0), OH - wh)
    return z, x0, y0


# ---------------------------------------------------------------- grade: gentle contrast, a touch of warmth, soft vignette
def _lut():
    x = np.arange(256, dtype=np.float32) / 255
    s = x * x * (3 - 2 * x)
    y = 0.82 * x + 0.18 * s
    y = 0.012 + y * 0.988
    sh, hi = (1 - y) ** 2, y ** 2
    r = y + 0.006 * hi
    g = y
    b = y + 0.010 * sh - 0.012 * hi
    return [np.clip(c * 255, 0, 255).astype(np.uint8) for c in (r, g, b)]


LUT = _lut()
_yy, _xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
VIG = (1 - 0.09 * (((_xx - OW / 2) / (OW / 2)) ** 2 * 0.6 + ((_yy - OH / 2) / (OH / 2)) ** 2 * 0.4) ** 1.2)[:, :, None]


def frame_from(src, p):
    z, x0, y0 = cam(p)
    M = np.array([[z, 0, -x0 * z], [0, z, -y0 * z]], np.float32)
    img = cv2.warpAffine(src, M, (OW, OH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    blur = cv2.GaussianBlur(img, (0, 0), 1.2)
    img = cv2.addWeighted(img, 1.35, blur, -0.35, 0)                     # recover a little crispness after the zoom
    out = np.stack([LUT[0][img[..., 0]], LUT[1][img[..., 1]], LUT[2][img[..., 2]]], 2).astype(np.float32)
    m = out.mean(2, keepdims=True)
    out = m + (out - m) * 1.04
    out *= VIG
    return np.clip(out, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- decoding
class Decoder:
    def __init__(self):
        self.proc, self.shot, self.pos, self.last = None, None, None, None

    def get(self, shot, f):
        if self.shot != shot or self.pos is None or f < self.pos - 1 or f > self.pos + 12:
            if self.proc:
                self.proc.kill()
            self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f / 30:.4f}", "-i", f"{WORK}/shot{shot}.mp4", "-vf", "fps=30",
                                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            self.shot, self.pos, self.last = shot, f, None
        while self.pos <= f:
            buf = self.proc.stdout.read(OW * OH * 3)
            if len(buf) < OW * OH * 3:
                break
            self.last = buf; self.pos += 1
        return np.frombuffer(self.last, np.uint8).reshape(OH, OW, 3)


_cache = {}


def grab30(shot, f):
    k = (shot, f)
    if k not in _cache:
        if len(_cache) > 40:
            _cache.clear()
        _cache[k] = grab(shot, f / 30 + 0.001)
    return _cache[k]


def piece_at(n):
    for i, p in enumerate(PIECES):
        if p["n0"] <= n < p["n1"]:
            return i
    return len(PIECES) - 1


def src_frame(p, n):
    return int(round((p["a"] + (n - p["n0"] + 0.5) / FPS * SPEED) * 30))


_DIS = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)


def morph(A, B, alpha):
    s = 0.25
    ga = cv2.cvtColor(cv2.resize(A, None, fx=s, fy=s, interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
    gb = cv2.cvtColor(cv2.resize(B, None, fx=s, fy=s, interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
    fab = cv2.GaussianBlur(cv2.resize(_DIS.calc(ga, gb, None), (OW, OH)) / s, (0, 0), 6)
    fba = cv2.GaussianBlur(cv2.resize(_DIS.calc(gb, ga, None), (OW, OH)) / s, (0, 0), 6)
    aw = cv2.remap(A, _xx + alpha * fba[..., 0], _yy + alpha * fba[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    bw = cv2.remap(B, _xx + (1 - alpha) * fab[..., 0], _yy + (1 - alpha) * fab[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return np.clip(aw.astype(np.float32) * (1 - alpha) + bw.astype(np.float32) * alpha, 0, 255).astype(np.uint8)


MORPH_CUTS = [c["n"] for c in TL["cuts"] if c["kind"] == "morph"]


def video(n, dec):
    i = piece_at(n); p = PIECES[i]
    img = frame_from(dec.get(p["shot"], src_frame(p, n)), p)
    for cn in MORPH_CUTS:
        ia = piece_at(cn - 1); ib = piece_at(cn)
        pa, pb = PIECES[ia], PIECES[ib]
        L = min(MORPH, (pa["n1"] - pa["n0"]) // 2, (pb["n1"] - pb["n0"]) // 2)
        k = n - (cn - L // 2)
        if L < 2 or not 0 <= k < L:
            continue
        if n < cn:      # before the cut: borrow the incoming take's lead-in
            other = frame_from(grab30(pb["shot"], max(0, src_frame(pb, pb["n0"]) - int(round((cn - n) * SPEED)))), pb)
            A, B = img, other
        else:           # after the cut: the outgoing take keeps rolling
            other = frame_from(grab30(pa["shot"], src_frame(pa, n)), pa)
            A, B = other, img
        return morph(A, B, G.ease_io((k + 0.5) / L))
    return img


CAPS = TL["captions"]
T_REVEAL = TL["t_reveal"]
SEC0 = {}
for p in PIECES:
    SEC0.setdefault(p["sid"], p["n0"] / FPS)
NAME_IN = SEC0["classes"] + 0.15          # right after the opening question, as in the reference (about 3 s in)
NAME_OUT = NAME_IN + 4.6


def render(n, dec):
    t = n / FPS
    base = Image.fromarray(video(n, dec)).convert("RGBA")
    if t >= T_REVEAL + G.R_DISSOLVE[0]:
        frame = G.reveal(base, t - T_REVEAL)
        return frame.convert("RGB")
    G.draw_title(base, t, TL["hook_end"] - 0.34)            # fully gone before the first cut
    cur = None
    for c in CAPS:
        if c["s"] <= t < c["show_until"]:
            cur = c
    if cur is not None and t < T_REVEAL - 0.05:
        G.draw_caption(base, cur["text"])
    G.draw_namecard(base, t, NAME_IN, NAME_OUT)
    return base.convert("RGB")


def main():
    dec = Decoder()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        os.makedirs(f"{WORK}/stills", exist_ok=True)
        for tt in sys.argv[2].split(","):
            n = int(round(float(tt) * FPS))
            render(n, dec).save(f"{WORK}/stills/f_{float(tt):06.2f}.png")
        print("anchors", ANCH)
        return
    out = f"{WORK}/video_only.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out],
                           stdin=subprocess.PIPE)
    for n in range(NTOT):
        enc.stdin.write(render(n, dec).tobytes())
        if n % 150 == 0:
            print(f"frame {n}/{NTOT}", flush=True)
    enc.stdin.close(); enc.wait()
    print("done", out)


if __name__ == "__main__":
    main()
