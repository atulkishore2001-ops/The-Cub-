# 5 Science Facts renderer: speaker shots (straight cuts, framing alternating close / medium, cinematic grade),
# full-screen B-roll for each fact (vertical crop of the sharpest relevant moment, slow push-in, soft top/bottom
# shading so text reads), motion graphics, Saisha-style captions and name card, end hold and the logo reveal.
#   python render.py | python render.py --stills 1,5,9 [outdir]
import os, sys, json, subprocess
import numpy as np
import cv2
from PIL import Image
import gfx as G
import sf_gfx as F

WORK = os.environ["WORK"]
BROLL_DIR = os.environ.get("BROLL_DIR", WORK)
TL = json.load(open(f"{WORK}/timeline.json"))
FPS, SPEED = TL["fps"], TL["speed"]
OW, OH = 1080, 1920
ZOOM = {"close": 1.60, "medium": 1.30}
FACE_Y = {"close": 640, "medium": 700}
PIECES, VIS, ZONES, BROLL = TL["pieces"], TL["vis"], TL["zones"], TL["broll"]
NTOT, T_REVEAL = TL["total_frames"], TL["t_reveal"]
SRC = f"{WORK}/shot1.mp4"
SRC_LAST = int(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC],
                                    capture_output=True, text=True).stdout) * 30) - 3
_wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", SRC],
                     capture_output=True, text=True).stdout.strip().split(",")
SW, SH = int(_wh[0]), int(_wh[1])          # speaker source size (4K in the revised take)
SC = SW / OW
_det = cv2.FaceDetectorYN.create(os.environ.get("MODELS", "models") + "/yunet.onnx", "", (OW, OH), 0.6, 0.3, 5000)


def face_anchor():
    path = f"{WORK}/anchor.json"
    if os.path.exists(path):
        return json.load(open(path))
    pts = []
    for t in np.linspace(3, float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC], capture_output=True, text=True).stdout) - 3, 12):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", SRC, "-frames:v", "1", "-vf", f"scale={OW}:{OH}",
                              "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
        _, f = _det.detect(np.frombuffer(raw, np.uint8).reshape(OH, OW, 3))
        if f is not None:
            r = max(f, key=lambda r: r[-1] * r[2]); pts.append([r[0] + r[2] / 2, r[1] + r[3] / 2])
    m = np.median(np.array(pts), 0)
    out = dict(cx=float(m[0]), cy=float(m[1]))
    json.dump(out, open(path, "w"))
    return out


ANCH = face_anchor()


def zone_at(t):
    z = ZONES[0]
    for zz in ZONES:
        if zz["t"] <= t + 1e-6:
            z = zz
    return z


def crop_for(zoom):
    z = ZOOM[zoom]                                   # crop window in source pixels (anchor is in 1080-wide units)
    cw, ch = SW / z, SH / z
    x0 = min(max(ANCH["cx"] * SC - cw / 2, 0), SW - cw)
    y0 = min(max(ANCH["cy"] * SC - FACE_Y[zoom] / OH * ch, 0), SH - ch)
    ev = lambda v: int(round(v / 2) * 2)
    return ev(cw), ev(ch), ev(x0), ev(y0)


class Pipe:
    """Sequential ffmpeg frame reader that restarts when the requested key or position jumps."""
    def __init__(self):
        self.proc, self.key, self.pos, self.last = None, None, None, None

    def get(self, key, f, cmd):
        if self.key != key or self.pos is None or f < self.pos - 1 or f > self.pos + 12:
            if self.proc:
                self.proc.kill()
            self.proc = subprocess.Popen(cmd(f), stdout=subprocess.PIPE)
            self.key, self.pos, self.last = key, f, None
        while self.pos <= f:
            buf = self.proc.stdout.read(OW * OH * 3)
            if len(buf) < OW * OH * 3:
                break
            self.last = buf; self.pos += 1
        return np.frombuffer(self.last, np.uint8).reshape(OH, OW, 3).copy()


def piece_at(t):
    for p in PIECES:
        if p["t0"] <= t < p["t0"] + p["dur"]:
            return p
    return PIECES[-1]


# ---- grade
def _lut(lift=0.02, curve=0.22, split=1.0):
    """Filmic S-curve with lifted blacks and a gentle split tone: teal in the shadows, warm highlights."""
    x = np.arange(256, dtype=np.float32) / 255
    x = np.clip(x * 1.02, 0, 1)
    s = x * x * (3 - 2 * x)
    y = (1 - curve) * x + curve * s
    y = lift + y * (1 - lift - 0.01)
    sh, hi = (1 - y) ** 2, y ** 2
    r_ = y - 0.012 * split * sh + 0.016 * split * hi
    g_ = y + 0.004 * split * sh + 0.004 * split * hi
    b_ = y + 0.020 * split * sh - 0.014 * split * hi
    return [np.clip(c * 255, 0, 255).astype(np.uint8) for c in (r_, g_, b_)]


LUT_SP, LUT_BR = _lut(lift=0.022, curve=0.30, split=1.0), _lut(lift=0.012, curve=0.24, split=0.8)   # revision 3: richer, cinematic
_yy, _xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
VIG = (1 - 0.16 * (((_xx - OW / 2) / (OW / 2)) ** 2 * 0.6 + ((_yy - OH / 2) / (OH / 2)) ** 2 * 0.4) ** 1.2)[:, :, None]
yv = np.arange(OH, dtype=np.float32)
SHADE = (1 - 0.40 * np.clip((520 - yv) / 520, 0, 1) - 0.38 * np.clip((yv - 1150) / 770, 0, 1))[:, None, None]   # B-roll: text bands


def grade(img, lut, sat=0.96, shade=False):
    out = np.stack([lut[0][img[..., 0]], lut[1][img[..., 1]], lut[2][img[..., 2]]], 2).astype(np.float32)
    m = out.mean(2, keepdims=True)
    out = m + (out - m) * sat
    out *= VIG
    if shade:
        out *= SHADE
    return np.clip(out, 0, 255).astype(np.uint8)


SP, BR = Pipe(), Pipe()


def speaker_frame(n):
    t = n / FPS
    p = piece_at(t)
    lt = t - p["t0"] + 0.5 / FPS
    src = p["b_audio"]
    for sa, sb, oa, ob, v in p["segs"]:                    # variable-speed time map (pauses faster than speech)
        if lt < ob:
            src = sa + max(0.0, lt - oa) * v; break
    f = min(int(round(src * 30)), SRC_LAST)
    zm = zone_at(t)["zoom"]
    cw, ch, x0, y0 = crop_for(zm)
    cmd = lambda f0: ["ffmpeg", "-v", "error", "-ss", f"{f0 / 30:.4f}", "-i", SRC, "-vf",
                      f"fps=30,crop={cw}:{ch}:{x0}:{y0},scale={OW}:{OH}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    return grade(SP.get(("sp", zm), f, cmd), LUT_SP, sat=1.02)


def broll_frame(n, seg):
    b = BROLL[seg["layer"]]
    path = f"{BROLL_DIR}/{b['file']}"
    local = n / FPS - seg["t0"]
    f = int(round((b["start"] + local) * 30))
    info = BROLL_INFO[seg["layer"]]
    sw, sh = info
    if sw > sh:                                     # landscape 4K -> 9:16 window around the subject
        ch = sh; cw = int(round(sh * 9 / 16 / 2) * 2)
        x0 = int(round(min(max(b["cx"] * sw - cw / 2, 0), sw - cw) / 2) * 2)
        vf = f"fps=30,crop={cw}:{ch}:{x0}:0,scale={OW}:{OH}:flags=lanczos"
    else:
        vf = f"fps=30,scale={OW}:{OH}:flags=lanczos"
    cmd = lambda f0: ["ffmpeg", "-v", "error", "-ss", f"{f0 / 30:.4f}", "-i", path, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    img = BR.get(("br", seg["layer"], seg["t0"]), f, cmd)
    dur = seg["t1"] - seg["t0"]
    z = 1.0 + b["push"] * G.ease_io(local / max(0.5, dur))                     # slow push-in
    M = np.array([[z, 0, OW / 2 * (1 - z)], [0, z, OH / 2 * (1 - z)]], np.float32)
    img = cv2.warpAffine(img, M, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return grade(img, LUT_BR, sat=1.08, shade=True)


BROLL_INFO = {}
for k, b in BROLL.items():
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0",
                        f"{BROLL_DIR}/{b['file']}"], capture_output=True, text=True).stdout.strip().split(",")
    BROLL_INFO[k] = (int(o[0]), int(o[1]))

CAPS, GR = TL["captions"], TL["graphics"]


def render(n):
    t = n / FPS
    seg = [v for v in VIS if v["t0"] <= t < v["t1"]] or [VIS[-1]]
    seg = seg[0]
    img = speaker_frame(n) if seg["layer"] == "speaker" else broll_frame(n, seg)
    base = Image.fromarray(img).convert("RGBA")
    for g in GR:
        k = g["kind"]
        if k == "pill_top":
            F.pop(base, F.pill(g["text"], F.ORANGE), t, g["t_in"], g["t_out"], F.W / 2, 300)
        elif k == "title":
            F.draw_title(base, t, g["t_in"], g["t_out"])
        elif k == "stamp":
            F.pop(base, F.stamp_img(g["text"], g["color"]), t, g["t_in"], g["t_out"], F.W / 2, 1225, rot=-7)
        elif k == "pill_mid":
            F.pop(base, F.pill(g["text"], F.CHAR, size=40), t, g["t_in"], g["t_out"], F.W / 2, 1190)
        elif k == "number":
            F.draw_number(base, t, g["num"], g["t_in"], g["t_out"])
        elif k == "chip":
            F.draw_chip(base, t, g["num"], g["text"], g["t_in"], g["t_out"])
        elif k == "card":
            F.draw_card(base, t, g["icon"], g["text"], g["t_in"], g["t_out"])
        elif k == "hearts":
            F.draw_hearts(base, t, g["t_in"], g["t_out"])
        elif k == "blue_blood":
            F.pop(base, F.blue_img(), t, g["t_in"], g["t_out"], F.W / 2, 1170)
        elif k == "sun_earth":
            F.draw_sun_earth(base, t, g["t_in"], g["t_out"], g["t_arrive"])
        elif k == "bars":
            F.draw_bars(base, t, g["t_day"], g["t_year"], g["t_out"])
        elif k == "radiation":
            F.draw_radiation(base, t, g["t_in"], g["t_out"])
        elif k == "element":
            F.rise(base, F.element_img(), t, g["t_in"], g["t_out"], F.W / 2, 950)
        elif k == "numbers":
            F.draw_numbers(base, t, g["t_in"], g["t_out"])
        elif k == "follow":
            F.draw_follow(base, t, g["t_in"], g["t_out"])
        elif k == "namecard":
            G.draw_namecard(base, t, g["t_in"], g["t_out"])
    cur = None
    for c in CAPS:
        if c["s"] <= t < c["show_until"]:
            cur = c
    if cur is None and t >= T_REVEAL - 0.5:
        cur = CAPS[-1]
    if cur is not None:
        G.draw_caption(base, cur["text"])
    if t >= T_REVEAL:
        return G.reveal(base, t - T_REVEAL).convert("RGB")
    return base.convert("RGB")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        out = sys.argv[3] if len(sys.argv) > 3 else f"{WORK}/stills"
        os.makedirs(out, exist_ok=True)
        for tt in sys.argv[2].split(","):
            render(int(round(float(tt) * FPS))).save(f"{out}/f_{float(tt):06.2f}.png")
        return
    out = f"{WORK}/video_only.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for n in range(NTOT):
        enc.stdin.write(render(n).tobytes())
        if n % 150 == 0:
            print(f"frame {n}/{NTOT}", flush=True)
    enc.stdin.close(); enc.wait()
    print("done", out)


if __name__ == "__main__":
    main()
