# Break The Silence renderer.
#   * each shot is cropped straight from the 4K source (ffmpeg crop + Lanczos scale to 1080x1920), so close framing
#     stays native-sharp; framing alternates close / medium at every straight cut (Saisha reel, revision 2)
#   * skin retouch on the face only (forehead strongest): face tracked every frame, skin-colour mask, edge-preserving
#     smoothing + blemish lift, a little fine grain kept so it never looks plastic
#   * cinematic grade: soft S-curve, lifted blacks, warm highlights / slightly cool shadows, gentle vignette
#   * taunt highlights, title, name card, captions, end hold and the logo reveal
#   python render.py | python render.py --stills 1,5,9 [outdir]
import os, sys, json, subprocess
import numpy as np
import cv2
from PIL import Image
import gfx as G
import bts_gfx as B

WORK = os.environ["WORK"]
TL = json.load(open(f"{WORK}/timeline.json"))
FPS, SPEED = TL["fps"], TL["speed"]
OW, OH = 1080, 1920
SW, SH = 2160, 3840                       # 4K source
ZOOM = {"close": 1.75, "medium": 1.40}
FACE_Y = {"close": 640, "medium": 690}    # output height of the face centre
PIECES = TL["pieces"]
NTOT = TL["total_frames"]
T_REVEAL = TL["t_reveal"]
SRC = f"{WORK}/shot1.mp4"
SRC_LAST = int(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC],
                                    capture_output=True, text=True).stdout) * 30) - 3
_det = cv2.FaceDetectorYN.create(os.environ.get("MODELS", "models") + "/yunet.onnx", "", (OW, OH), 0.6, 0.3, 5000)


def grab_small(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", SRC, "-frames:v", "1", "-vf", "scale=1080:1920",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(OH, OW, 3)


def anchors():
    path = f"{WORK}/anchors.json"
    if os.path.exists(path):
        return {int(k): v for k, v in json.load(open(path)).items()}
    out = {}
    for p in PIECES:
        boxes = []
        for t in np.linspace(p["a"] + 0.2, p["b_audio"] - 0.2, max(3, int((p["b_audio"] - p["a"]) / 1.2))):
            _, f = _det.detect(grab_small(t))
            if f is not None:
                r = max(f, key=lambda r: r[-1] * r[2]); boxes.append([(r[0] + r[2] / 2) * 2, (r[1] + r[3] / 2) * 2])
        m = np.median(np.array(boxes), 0)
        out[p["k"]] = dict(cx=float(m[0]), cy=float(m[1]), n=len(boxes))
    json.dump(out, open(path, "w"), indent=0)
    return out


ANCH = anchors()


def crop_of(p):
    """Crop window in 4K source pixels (even integers) for this shot's framing."""
    z = ZOOM[p["zoom"]]; a = ANCH[p["k"]]
    cw, ch = SW / z, SH / z
    x0 = min(max(a["cx"] - cw / 2, 0), SW - cw)
    y0 = min(max(a["cy"] - FACE_Y[p["zoom"]] / OH * ch, 0), SH - ch)
    ev = lambda v: int(round(v / 2) * 2)
    return ev(cw), ev(ch), ev(x0), ev(y0)


class Decoder:
    def __init__(self):
        self.proc, self.key, self.pos, self.last = None, None, None, None

    def get(self, p, f):
        key = p["k"]
        if self.key != key or self.pos is None or f < self.pos - 1 or f > self.pos + 12:
            if self.proc:
                self.proc.kill()
            cw, ch, x0, y0 = crop_of(p)
            vf = f"fps=30,crop={cw}:{ch}:{x0}:{y0},scale={OW}:{OH}:flags=lanczos"
            self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f / 30:.4f}", "-i", SRC, "-vf", vf, "-f", "rawvideo",
                                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            self.key, self.pos, self.last = key, f, None
        while self.pos <= f:
            buf = self.proc.stdout.read(OW * OH * 3)
            if len(buf) < OW * OH * 3:
                break
            self.last = buf; self.pos += 1
        return np.frombuffer(self.last, np.uint8).reshape(OH, OW, 3).copy()


# ------------------------------------------------------------------ skin retouch
_track = {}


def face_box(img, k):
    """Face box + landmarks on the output frame, lightly smoothed over time within a shot."""
    _, f = _det.detect(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    prev = _track.get(k)
    if f is None or len(f) == 0:
        return prev
    r = max(f, key=lambda r: r[-1] * r[2])[:14].astype(np.float32)
    if prev is not None and abs(r[0] - prev[0]) < 60:
        r = prev * 0.6 + r * 0.4
    _track[k] = r
    return r


def retouch(img, r):
    if r is None:
        return img
    x, y, w, h = r[:4]
    eye_y = (r[5] + r[7]) / 2                           # yunet landmarks: right eye (4,5), left eye (6,7)
    X0, X1 = int(max(0, x - 0.05 * w)), int(min(OW, x + 1.05 * w))
    Y0, Y1 = int(max(0, y - 0.30 * h)), int(min(OH, y + 1.05 * h))
    R = img[Y0:Y1, X0:X1]
    if R.size == 0:
        return img
    ycc = cv2.cvtColor(R, cv2.COLOR_RGB2YCrCb)
    skin = ((ycc[..., 1] > 132) & (ycc[..., 1] < 178) & (ycc[..., 2] > 77) & (ycc[..., 2] < 132) & (ycc[..., 0] > 55)).astype(np.uint8)
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    # keep eyes, brows and lips crisp: cut soft holes around the eye and mouth landmarks
    keep = np.zeros_like(skin, np.float32)
    for (lx, ly, rad) in ((r[4], r[5], 0.17), (r[6], r[7], 0.17), ((r[10] + r[12]) / 2, (r[11] + r[13]) / 2, 0.20)):
        cv2.circle(keep, (int(lx - X0), int(ly - Y0)), int(rad * w), 1.0, -1)
    keep = cv2.GaussianBlur(keep, (0, 0), w * 0.04)
    yy = np.arange(Y1 - Y0, dtype=np.float32)[:, None] + Y0
    band = np.clip(((eye_y - 0.10 * h) - yy) / (0.10 * h), 0, 1)        # 1 on the forehead, fading out by the brows
    wmap = (0.45 + 0.53 * band) * skin.astype(np.float32) * (1 - keep)
    wmap = cv2.GaussianBlur(wmap, (0, 0), max(2.0, w * 0.012))[..., None]
    Rf = R.astype(np.float32)
    s = max(3.0, w / 55)
    smooth = cv2.bilateralFilter(R, 0, 30, s).astype(np.float32)
    med = cv2.medianBlur(R, int(max(5, (w / 15) // 2 * 2 + 1))).astype(np.float32)
    # blemishes: small spots darker or redder than the surrounding skin -> pull them to the local skin tone
    lum = Rf.mean(2); mlum = med.mean(2)
    red = (Rf[..., 0] - Rf[..., 1]) - (med[..., 0] - med[..., 1])
    spot = np.clip((mlum - lum - 1) / 6, 0, 1) + np.clip((red - 3) / 8, 0, 1)
    spot = spot * (0.5 + 0.5 * band)                                    # strongest on the forehead
    spot = cv2.GaussianBlur(np.clip(spot, 0, 1), (0, 0), max(1.5, w / 160))[..., None]
    fixed = smooth * (1 - spot * 0.95) + med * (spot * 0.95)
    grain = Rf - cv2.GaussianBlur(Rf, (0, 0), 0.9)
    fixed = fixed + grain * 0.30                                         # keep fine skin texture
    out = Rf * (1 - wmap) + fixed * wmap
    img[Y0:Y1, X0:X1] = np.clip(out, 0, 255).astype(np.uint8)
    return img


# ------------------------------------------------------------------ grade
def _lut():
    x = np.arange(256, dtype=np.float32) / 255
    x = np.clip(x * 1.03, 0, 1)
    s = x * x * (3 - 2 * x)
    y = 0.78 * x + 0.22 * s                    # soft filmic contrast
    y = 0.025 + y * 0.965                      # lifted blacks
    sh, hi = (1 - y) ** 2, y ** 2
    r = y - 0.006 * sh + 0.010 * hi            # warm highlights
    g = y + 0.002 * sh + 0.002 * hi
    b = y + 0.016 * sh - 0.012 * hi            # slightly cool shadows
    return [np.clip(c * 255, 0, 255).astype(np.uint8) for c in (r, g, b)]


LUT = _lut()
_yy, _xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
VIG = (1 - 0.13 * (((_xx - OW / 2) / (OW / 2)) ** 2 * 0.6 + ((_yy - OH / 2) / (OH / 2)) ** 2 * 0.4) ** 1.2)[:, :, None]


def grade(img):
    out = np.stack([LUT[0][img[..., 0]], LUT[1][img[..., 1]], LUT[2][img[..., 2]]], 2).astype(np.float32)
    m = out.mean(2, keepdims=True)
    out = m + (out - m) * 0.95                 # a touch less saturated: calmer, more cinematic
    out *= VIG
    return np.clip(out, 0, 255).astype(np.uint8)


def piece_at(n):
    for p in PIECES:
        if p["n0"] <= n < p["n1"]:
            return p
    return PIECES[-1]


def video(n, dec):
    p = piece_at(n)
    f = min(int(round((p["a"] + (n - p["n0"] + 0.5) / FPS * SPEED) * 30)), SRC_LAST)
    img = dec.get(p, f)
    img = retouch(img, face_box(img, p["k"]))
    return grade(img)


CAPS = TL["captions"]
GR = TL["graphics"]


def render(n, dec):
    t = n / FPS
    base = Image.fromarray(video(n, dec)).convert("RGBA")
    for h in GR["highlights"]:
        B.draw_highlight(base, t, h["text"], h["t_in"], h["t_out"])
    B.draw_title(base, t, GR["title"]["t_in"], GR["title"]["t_out"])
    cur = None
    for c in CAPS:
        if c["s"] <= t < c["show_until"]:
            cur = c
    if cur is None and t >= T_REVEAL - 0.5:
        cur = CAPS[-1]                                       # the last line stays up and dissolves with the picture
    if cur is not None:
        G.draw_caption(base, cur["text"])
    G.draw_namecard(base, t, GR["namecard"]["t_in"], GR["namecard"]["t_out"])
    if t >= T_REVEAL:
        return G.reveal(base, t - T_REVEAL).convert("RGB")
    return base.convert("RGB")


def main():
    dec = Decoder()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        out = sys.argv[3] if len(sys.argv) > 3 else f"{WORK}/stills"
        os.makedirs(out, exist_ok=True)
        for tt in sys.argv[2].split(","):
            render(int(round(float(tt) * FPS)), dec).save(f"{out}/f_{float(tt):06.2f}.png")
        return
    out = f"{WORK}/video_only.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for n in range(NTOT):
        enc.stdin.write(render(n, dec).tobytes())
        if n % 150 == 0:
            print(f"frame {n}/{NTOT}", flush=True)
    enc.stdin.close(); enc.wait()
    print("done", out)


if __name__ == "__main__":
    main()
