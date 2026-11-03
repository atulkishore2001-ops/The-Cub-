# Frame renderer: source decode -> reframe/zoom/transitions -> motion graphics + captions -> x264.
import os, sys, math, random, subprocess
import numpy as np
from PIL import Image, ImageFilter
import design as D
from timeline import frame_map, SPEED, FPS
from anim import clamp, ease_in_out, ease_out_cubic

W = os.environ["WORK"]
OUT_W, OUT_H = 1080, 1920
SRC_W, SRC_H = 720, 1280
K = OUT_W / SRC_W
SRC = {1: f"{W}/shot1.mp4", 2: f"{W}/shot2.mp4"}
SRC_FRAMES = {1: 1509, 2: 1703}
GRADE = "eq=contrast=1.05:saturation=1.10:brightness=0.004,unsharp=5:5:0.35:3:3:0"

# per-location base zoom and focal point (output px) so the face sits well in frame
LOC = {"posters": (1.00, 600), "garden": (1.10, 590), "corridor": (1.12, 840), "sofa": (1.12, 830),
       "painting": (1.00, 640), "plant": (1.06, 660)}

TOTAL_FRAMES = int(round(D.TOTAL * FPS))
FM = frame_map(D.PIECES)
last_shot, last_f = FM[-1]
k = 1
while len(FM) < TOTAL_FRAMES:  # run on past the last word, then hold
    FM.append((last_shot, min(last_f + int(k * SPEED), SRC_FRAMES[last_shot] - 1)))
    k += 1

BLK = D.BLOCKS
BLK[-1]["o_out"] = TOTAL_FRAMES
blk_of = np.zeros(TOTAL_FRAMES, int)
for i, b in enumerate(BLK):
    blk_of[b["o_in"]:b["o_out"]] = i
variant, prev = [], None
for i, b in enumerate(BLK):
    v = 0 if b["loc"] != prev else 1 - variant[-1]
    variant.append(v)
    prev = b["loc"]

TR_F = [int(round(t * FPS)) for t in D.TRANSITIONS]
yy, xx = np.mgrid[0:OUT_H, 0:OUT_W].astype(np.float32)
r2 = ((xx - OUT_W / 2) / (OUT_W / 2)) ** 2 * 0.7 + ((yy - OUT_H * 0.45) / (OUT_H / 2)) ** 2 * 0.5
VIG = np.clip(1 - 0.20 * r2, 0.72, 1)[..., None].astype(np.float32)
del yy, xx, r2


def camera(n):
    t = n / FPS
    b = BLK[blk_of[n]]
    z0, fy = LOC[b["loc"]]
    z = z0 * (1.0 + 0.07 * variant[blk_of[n]])
    z *= 1 + 0.03 * (n - b["o_in"]) / max(1, b["o_out"] - b["o_in"])  # slow push-in
    for (tp, amt) in D.PUNCH:
        if b["o_in"] / FPS - 0.01 <= tp < b["o_out"] / FPS and t >= tp:
            z *= 1 + amt * ease_out_cubic(clamp((t - tp) / 0.22))
    blur = 0
    for f in TR_F:
        if f - 4 <= n < f:
            p = (n - (f - 4) + 1) / 4
            z *= 1 + 0.22 * ease_in_out(p)
            blur = 70 * p
        elif f <= n < f + 5:
            p = 1 - (n - f) / 5
            z *= 1 + 0.22 * ease_in_out(p)
            blur = 70 * p
    dx = dy = 0.0
    for (ts, dur, amp) in D.SHAKE:
        if ts <= t < ts + dur:
            decay = 1 - (t - ts) / dur
            rnd = random.Random(n)
            dx += amp * decay * rnd.uniform(-1, 1)
            dy += amp * decay * rnd.uniform(-1, 1)
            z *= 1.02
    flash = 0.0
    for f in TR_F:
        if n == f:
            flash = 0.32
        elif n == f + 1:
            flash = 0.14
    return z, fy, dx, dy, blur, flash


def transform(src, z, fy, dx, dy):
    fx = OUT_W / 2
    a = 1 / (K * z)
    c = (fx - (fx + dx) / z) / K
    e = 1 / (K * z)
    f = (fy - (fy + dy) / z) / K
    return src.transform((OUT_W, OUT_H), Image.AFFINE, (a, 0, c, 0, e, f), resample=Image.BICUBIC)


def vblur(arr, strength):
    taps = 9
    acc = np.zeros_like(arr, dtype=np.float32)
    for o in np.linspace(-strength / 2, strength / 2, taps):
        acc += np.roll(arr, int(o), axis=0)
    return acc / taps


class Decoder:
    def __init__(self):
        self.proc, self.key, self.pos, self.last = None, None, None, None

    def get(self, shot, f):
        if self.key != shot or self.pos is None or f < self.pos - 1 or f > self.pos + 8:
            if self.proc:
                self.proc.kill()
            self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f / FPS:.4f}", "-i", SRC[shot], "-vf", GRADE,
                                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            self.key, self.pos, self.last = shot, f, None
        while self.pos <= f:
            buf = self.proc.stdout.read(SRC_W * SRC_H * 3)
            if len(buf) < SRC_W * SRC_H * 3:
                break
            self.last = buf
            self.pos += 1
        return Image.frombuffer("RGB", (SRC_W, SRC_H), self.last, "raw", "RGB", 0, 1)


def render_frame(n, dec):
    t = n / FPS
    shot, f = FM[n]
    src = dec.get(shot, f)
    z, fy, dx, dy, blur, flash = camera(n)
    img = transform(src, z, fy, dx, dy)
    arr = np.asarray(img).astype(np.float32)
    if blur > 1:
        arr = vblur(arr, blur)
    arr *= VIG
    if flash:
        arr = arr * (1 - flash) + 255 * flash
    # end card: blur + darken
    if t >= D.END_CARD:
        p = ease_in_out(clamp((t - D.END_CARD) / 0.35))
        im = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        im = im.filter(ImageFilter.GaussianBlur(2 + 16 * p))
        arr = np.asarray(im).astype(np.float32)
        ink = np.array([24, 27, 52], np.float32)
        arr = arr * (1 - 0.62 * p) + ink * 0.62 * p
    frame = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    for s in D.SPRITES:
        if s.active(t):
            s.render(frame, t)
    D.CAPTIONS.render(frame, t)
    return frame.convert("RGB")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        outdir = sys.argv[3]
        os.makedirs(outdir, exist_ok=True)
        dec = Decoder()
        for tt in sys.argv[2].split(","):
            n = int(round(float(tt) * FPS))
            render_frame(n, dec).save(f"{outdir}/f_{float(tt):06.2f}.png")
        return
    out = sys.argv[1]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OUT_W}x{OUT_H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "15",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    dec = Decoder()
    for n in range(TOTAL_FRAMES):
        enc.stdin.write(render_frame(n, dec).tobytes())
        if n % 150 == 0:
            print(f"frame {n}/{TOTAL_FRAMES}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("done", out)


if __name__ == "__main__":
    main()
