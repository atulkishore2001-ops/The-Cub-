# OSIT ad renderer: one continuous take cut into sections (straight cuts, framing alternating close / medium), a
# clean natural grade (magenta cast from the blue shirt neutralised, gentle contrast, natural skin), graphics timed
# to the words, photo cards over a softly blurred speaker, captions in the Saisha-reel style, and a closing frame with
# the workshop title, logos and the registration QR. Writes WORK/video_only.mp4.
#   python render.py                 full render
#   python render.py --stills 1,5,9  preview frames into WORK/stills
import os, sys, json, subprocess
import numpy as np
import cv2
from PIL import Image
import gfx as G
import osit_gfx as O

WORK = os.environ["WORK"]
TL = json.load(open(f"{WORK}/timeline.json"))
FPS, SPEED = TL["fps"], TL["speed"]
OW, OH = 1080, 1920
ZOOM = {"close": 1.28, "medium": 1.06}
FACE_Y = {"close": 700, "medium": 780}
PIECES = TL["pieces"]
NTOT = TL["total_frames"]
GR = TL["graphics"]
T_CLOSE = TL["t_close"]
XFADE = 0.40                                   # picture -> closing frame dissolve
SRC_LAST = int(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                     f"{WORK}/shot1.mp4"], capture_output=True, text=True).stdout) * 30) - 3

_det = cv2.FaceDetectorYN.create(os.environ.get("MODELS", "models") + "/yunet.onnx", "", (OW, OH), 0.6, 0.3, 5000)


def grab(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", f"{WORK}/shot1.mp4", "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(OH, OW, 3)


def anchors():
    path = f"{WORK}/anchors.json"
    if os.path.exists(path):
        return {int(k): v for k, v in json.load(open(path)).items()}
    out = {}
    for p in PIECES:
        boxes = []
        for t in np.linspace(p["a"] + 0.2, p["b_audio"] - 0.2, max(3, int((p["b_audio"] - p["a"]) / 1.5))):
            _, f = _det.detect(cv2.cvtColor(grab(t), cv2.COLOR_RGB2BGR))
            if f is not None:
                f = [r for r in f if r[2] > 150]
                if f:
                    r = max(f, key=lambda r: r[-1] * r[2]); boxes.append([r[0] + r[2] / 2, r[1] + r[3] / 2])
        m = np.median(np.array(boxes), 0)
        out[p["k"]] = dict(cx=float(m[0]), cy=float(m[1]), n=len(boxes))
    json.dump(out, open(path, "w"), indent=0)
    return out


ANCH = anchors()


def cam(p):
    z = ZOOM[p["zoom"]]; a = ANCH[p["k"]]
    ww, wh = OW / z, OH / z
    x0 = min(max(a["cx"] - ww / 2, 0), OW - ww)
    y0 = min(max(a["cy"] - FACE_Y[p["zoom"]] / z, 0), OH - wh)
    return z, x0, y0


# grade: neutralise the slight magenta cast, +4% exposure, gentle S-curve, a touch of warmth in the highlights,
# natural skin (no extra saturation), soft vignette
def _lut():
    x = np.arange(256, dtype=np.float32) / 255
    x = np.clip(x * 1.04, 0, 1)
    s = x * x * (3 - 2 * x)
    y = 0.80 * x + 0.20 * s
    y = 0.010 + y * 0.985
    hi = y ** 2
    r = y * 0.990 + 0.006 * hi
    g = y * 1.018
    b = y * 0.985 - 0.006 * hi
    return [np.clip(c * 255, 0, 255).astype(np.uint8) for c in (r, g, b)]


LUT = _lut()
_yy, _xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
VIG = (1 - 0.08 * (((_xx - OW / 2) / (OW / 2)) ** 2 * 0.6 + ((_yy - OH / 2) / (OH / 2)) ** 2 * 0.4) ** 1.2)[:, :, None]


def frame_from(src, p):
    z, x0, y0 = cam(p)
    M = np.array([[z, 0, -x0 * z], [0, z, -y0 * z]], np.float32)
    img = cv2.warpAffine(src, M, (OW, OH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    if z > 1.1:
        blur = cv2.GaussianBlur(img, (0, 0), 1.2)
        img = cv2.addWeighted(img, 1.3, blur, -0.3, 0)
    out = np.stack([LUT[0][img[..., 0]], LUT[1][img[..., 1]], LUT[2][img[..., 2]]], 2).astype(np.float32)
    m = out.mean(2, keepdims=True)
    out = m + (out - m) * 0.98
    out *= VIG
    return np.clip(out, 0, 255).astype(np.uint8)


class Decoder:
    def __init__(self):
        self.proc, self.pos, self.last = None, None, None

    def get(self, f):
        if self.pos is None or f < self.pos - 1 or f > self.pos + 12:
            if self.proc:
                self.proc.kill()
            self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f / 30:.4f}", "-i", f"{WORK}/shot1.mp4", "-vf", "fps=30",
                                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            self.pos, self.last = f, None
        while self.pos <= f:
            buf = self.proc.stdout.read(OW * OH * 3)
            if len(buf) < OW * OH * 3:
                break
            self.last = buf; self.pos += 1
        return np.frombuffer(self.last, np.uint8).reshape(OH, OW, 3)


def piece_at(n):
    for p in PIECES:
        if p["n0"] <= n < p["n1"]:
            return p
    return PIECES[-1]


def video(n, dec):
    p = piece_at(n)
    f = min(int(round((p["a"] + (n - p["n0"] + 0.5) / FPS * SPEED) * 30)), SRC_LAST)
    img = frame_from(dec.get(f), p)
    kb = O.blur_amount(n / FPS, GR)
    if kb > 0.01:                                             # photo moments: speaker softly blurred and dimmed behind the card
        small = cv2.resize(img, (OW // 4, OH // 4), interpolation=cv2.INTER_AREA)
        b = cv2.resize(cv2.GaussianBlur(small, (0, 0), 6), (OW, OH), interpolation=cv2.INTER_LINEAR).astype(np.float32) * 0.72
        img = np.clip(img.astype(np.float32) * (1 - kb) + b * kb, 0, 255).astype(np.uint8)
    return img


CAPS = TL["captions"]


def talk_frame(n, dec):
    t = n / FPS
    base = Image.fromarray(video(n, dec)).convert("RGBA")
    photos = [g for g in GR if g["kind"] == "photo"]
    for i, g in enumerate(photos):
        O.draw_photo(base, t, g, i)
    for g in GR:
        k = g["kind"]
        if k == "pill":
            O.draw_pill(base, t, g["label"], g["t_in"], g["t_out"])
        elif k == "title":
            O.draw_title(base, t, g["t_in"], g["t_out"])
        elif k == "date":
            O.draw_date(base, t, g["t_in"], g["t_out"])
        elif k == "logos":
            O.draw_logos(base, t, g["t_in"], g["t_out"])
        elif k == "fast":
            O.draw_callout(base, t, O.fast_img(), g["t_in"], g["t_out"])
        elif k == "premier":
            O.draw_callout(base, t, O.premier_img(), g["t_in"], g["t_out"])
        elif k == "deadline":
            O.draw_callout(base, t, O.deadline_img(), g["t_in"], g["t_out"])
        elif k == "namecard":
            G.draw_namecard(base, t, g["t_in"], g["t_out"])
    cur = None
    for c in CAPS:
        if c["s"] <= t < c["show_until"]:
            cur = c
    if cur is not None:
        G.draw_caption(base, cur["text"])
    return base


def render(n, dec):
    t = n / FPS
    if t < T_CLOSE - XFADE / 2:
        return talk_frame(n, dec).convert("RGB")
    cl = O.closing(max(0.0, t - T_CLOSE + XFADE / 2))
    k = G.ease_io((t - (T_CLOSE - XFADE / 2)) / XFADE)
    if k < 1:
        return Image.blend(talk_frame(n, dec).convert("RGB"), cl.convert("RGB"), k)
    return cl.convert("RGB")


def main():
    dec = Decoder()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        os.makedirs(f"{WORK}/stills", exist_ok=True)
        for tt in sys.argv[2].split(","):
            render(int(round(float(tt) * FPS)), dec).save(f"{WORK}/stills/f_{float(tt):06.2f}.png")
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
