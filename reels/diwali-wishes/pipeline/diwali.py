# Diwali wishes reel: the five wishes with their silent lead-ins/tails trimmed (cuts on the existing shot changes), a
# light warm grade, brand captions, a few soft sparkles on the group shot, celebratory music, and The Cub logo reveal
# with "Happy Diwali from The Cub" as the tagline.
import os, sys, json, math, re, subprocess
import numpy as np
from PIL import Image, ImageDraw
import gfx2 as G
from anim2 import Captions, clamp, ease_io, ease_out
import soundfile_shim as sf
import sounds2 as SND
import sounds as S0

W = os.environ["WORK"]
FPS, OW, OH = 30, 1080, 1920
SRC = f"{W}/src.mp4"
# kept pieces of the source (seconds): each wish from just before its first word to just after its last
PIECES = [(0.66, 5.95), (6.86, 10.95), (12.46, 16.42), (18.70, 23.72), (25.06, 30.0)]
OUTRO = 4.3
cum = [0.0]
for a, b in PIECES:
    cum.append(cum[-1] + (b - a))
T_SPEECH_END = cum[-1]
T_CREAM0 = T_SPEECH_END - 0.25
T_CREAM1 = T_CREAM0 + 1.0
T_END = T_SPEECH_END + OUTRO - 0.25
TOTAL = int(round(T_END * FPS))
BRAND = "/tmp/claude-0/-home-user-The-Cub-/6a3c4bc0-104a-5ca4-adb7-aceaf8503d24/scratchpad/brand"


def s2o(t):
    """Source time -> output time (None if cut)."""
    for k, (a, b) in enumerate(PIECES):
        if a <= t <= b:
            return cum[k] + (t - a)
    return None


# ---------------------------------------------------------------- captions
def words():
    ws = json.load(open(f"{W}/words.json"))
    out, seg = [], 0
    for w in ws:
        txt = w["w"]
        if txt == "us,":
            txt = "us"
        if txt.startswith("Abel"):
            txt = "at The Cub,"
        s, e = s2o(w["s"]), s2o(min(w["e"], w["s"] + 1.2))
        if s is None:                                   # recogniser start a hair before the trim point: snap to it
            s = next((cum[k] for k, (a, _) in enumerate(PIECES) if a - 0.3 <= w["s"] < a), None)
        if s is None:
            continue
        e = e if e is not None else s + 0.3
        out.append(dict(w=txt, s=s, e=e, seg=str(seg)))
        if txt[-1] in ".!?":
            seg += 1
    return out


CAPS = Captions(words(), y=1540, hide=[(T_CREAM0 + 0.1, T_END + 1)], size=50, max_chars=28, max_words=5)

# ---------------------------------------------------------------- grade: light and warm, the same for every shot
_x = np.arange(256, dtype=np.float32) / 255
_s = _x * _x * (3 - 2 * _x)
_y = 0.86 * _x + 0.14 * _s
LUT = [np.clip((_y + d) * 255 * g, 0, 255).astype(np.uint8) for d, g in ((0.008, 1.025), (0.004, 1.0), (-0.004, 0.975))]
_yy, _xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
VIG = (1 - 0.08 * (((_xx - OW / 2) / (OW / 2)) ** 2 * 0.6 + ((_yy - OH / 2) / (OH / 2)) ** 2 * 0.4) ** 1.2)[:, :, None]


def grade(a):
    out = np.stack([LUT[0][a[..., 0]], LUT[1][a[..., 1]], LUT[2][a[..., 2]]], 2).astype(np.float32)
    m = out.mean(2, keepdims=True)
    out = (m + (out - m) * 1.05) * VIG
    return np.clip(out, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- soft sparkles on the group shot (no particles elsewhere)
rng = np.random.default_rng(3)
SPARKS = [(rng.uniform(80, 1000), rng.uniform(200, 900), rng.uniform(0, 4), rng.uniform(7, 15)) for _ in range(22)]


def sparkles(ov, t):
    t0 = cum[4]
    if t < t0 + 0.2 or t > T_CREAM1:
        return
    d = ImageDraw.Draw(ov)
    a_all = clamp((t - t0 - 0.2) / 0.8) * (1 - clamp((t - T_CREAM0) / 0.8))
    for x, y, ph, r in SPARKS:
        tw = 0.5 + 0.5 * math.sin((t + ph) * 3.2)
        a = int(200 * a_all * tw)
        if a < 8:
            continue
        yy = y - 18 * ((t - t0) % 6)
        rr = r * (0.6 + 0.4 * tw)
        col = (255, 214, 120, a)
        d.polygon([(x, yy - rr * 1.6), (x + rr * 0.35, yy - rr * 0.35), (x + rr * 1.6, yy), (x + rr * 0.35, yy + rr * 0.35),
                   (x, yy + rr * 1.6), (x - rr * 0.35, yy + rr * 0.35), (x - rr * 1.6, yy), (x - rr * 0.35, yy - rr * 0.35)], fill=col)


# ---------------------------------------------------------------- closing: standard logo reveal, Diwali tagline
LOGO = Image.open(f"{BRAND}/logo_full.png").convert("RGBA")
LOGO = LOGO.resize((420, int(420 * LOGO.height / LOGO.width)), Image.LANCZOS)
T_LOGO, T_TAG = T_CREAM0 + 0.65, T_CREAM0 + 1.5
TAGLINE = "Happy Diwali from The Cub"
_tf = G.font("pfi", 500, 64)
_asc, _desc = _tf.getmetrics()
TAG = Image.new("RGBA", (int(_tf.getlength(TAGLINE)) + 24, _asc + _desc + 20), (0, 0, 0, 0))
ImageDraw.Draw(TAG).text((12, 10 + _asc), TAGLINE, font=_tf, fill=G.CHAR, anchor="ls")
TAG = TAG.crop(TAG.getchannel("A").getbbox())


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


def outro(ov, t):
    p = clamp((t - T_LOGO) / 1.1)
    if p > 0:
        s = 0.94 + 0.06 * ease_out(p)
        im = LOGO.resize((int(LOGO.width * s), int(LOGO.height * s)), Image.LANCZOS) if s < 0.999 else LOGO
        ov.alpha_composite(G.with_alpha(im, ease_io(clamp(p * 1.3))), (540 - im.width // 2, 820 - im.height // 2))
    p = clamp((t - T_TAG) / 1.15)
    if p > 0:
        im = G.with_alpha(_wipe(TAG, ease_io(p)), clamp(p * 2.5))
        dy = 12 * (1 - ease_out(clamp((t - T_TAG) / 1.0)))
        ov.alpha_composite(im, (540 - im.width // 2, int(1130 - im.height / 2 + dy)))
    if t >= T_TAG + 0.7:
        w = max(2, int(110 * ease_io(clamp((t - T_TAG - 0.7) / 0.6))))
        ov.alpha_composite(G.underline(w, 6), (540 - w // 2, 1212))


# ---------------------------------------------------------------- frames
def frames():
    """Yield graded source frames for every output frame (the last frame holds under the fade to cream)."""
    last = None
    for a, b in PIECES:
        n = int(round((b - a) * FPS))
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-i", SRC, "-vf", "fps=30", "-frames:v", str(n),
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        for _ in range(n):
            buf = p.stdout.read(OW * OH * 3)
            if len(buf) < OW * OH * 3:
                break
            last = grade(np.frombuffer(buf, np.uint8).reshape(OH, OW, 3))
            yield last
        p.wait()
    while True:
        yield last


def render(out, stills=None):
    enc = None
    if not stills:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", "30",
                                "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", out],
                               stdin=subprocess.PIPE)
    cream = np.array(G.CREAM[:3], np.float32)
    for n, fr in zip(range(TOTAL), frames()):
        t = n / FPS
        k = ease_io(clamp((t - T_CREAM0) / (T_CREAM1 - T_CREAM0)))
        base = fr.astype(np.float32) * (1 - k) + cream * k if k > 0 else fr
        img = Image.fromarray(np.asarray(base, np.uint8)).convert("RGBA")
        ov = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
        sparkles(ov, t)
        CAPS.render(ov, t)
        if t >= T_LOGO - 0.05:
            outro(ov, t)
        img.alpha_composite(ov)
        if stills is not None:
            if any(abs(t - s) < 0.017 for s in stills):
                img.convert("RGB").save(f"{out}/f_{t:06.2f}.png")
            if t > max(stills) + 0.1:
                return
        else:
            enc.stdin.write(img.convert("RGB").tobytes())
    if enc:
        enc.stdin.close(); enc.wait()


# ---------------------------------------------------------------- audio
SR = SND.SR


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def ffilter(x, af):
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af", af,
                        "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], input=x.astype(np.float32).tobytes(), capture_output=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()


def active_db(x):
    m = x.mean(1); hop = SR // 100; n = len(m) // hop
    r = np.sqrt((m[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12); db = 20 * np.log10(r)
    act = db > db.max() - 30
    return 20 * np.log10(np.sqrt((r[act] ** 2).mean()) + 1e-12)


def audio():
    x = decode(SRC)
    N = int(T_END * SR)
    v = np.zeros((N, 2), np.float32)
    for k, (a, b) in enumerate(PIECES):
        seg = x[int(a * SR):int(b * SR)].copy()
        seg *= 10 ** ((-20 - active_db(seg)) / 20)                       # every speaker at the same level
        f = int(0.015 * SR); seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]
        i = int(cum[k] * SR); v[i:i + len(seg)] += seg[:N - i]
    v = ffilter(v, "highpass=f=80,equalizer=f=3000:t=q:w=1.2:g=1.5,acompressor=threshold=-22dB:ratio=2.2:attack=8:release=160:makeup=1.5")
    v = np.pad(v, ((0, max(0, N - len(v))), (0, 0)))[:N]
    m = SND.music(T_END + 1, 0.0, T_CREAM0 + 0.6)[:N]                    # bright pluck + light percussion, resolves under the logo
    m = np.pad(m, ((0, max(0, N - len(m))), (0, 0)))[:N]
    vm = np.abs(v.mean(1)); hop = SR // 100; n = len(vm) // hop
    r = np.sqrt((vm[:n * hop].reshape(n, hop) ** 2).mean(1))
    act = (20 * np.log10(r + 1e-9) > -45).astype(float); sm = np.zeros_like(act)
    for i in range(1, len(act)):
        sm[i] = sm[i - 1] + (0.12 if act[i] > sm[i - 1] else 0.015) * (act[i] - sm[i - 1])
    duck = np.pad(np.repeat(10 ** (-7 * sm / 20), hop), (0, N), constant_values=1)[:N]
    m = m * (duck * 10 ** (-12 / 20))[:, None]
    a_, b_ = int((T_END - 2.4) * SR), N
    m[a_:b_] *= (np.cos(np.linspace(0, np.pi / 2, b_ - a_)) ** 1.5)[:, None]
    sfx = np.zeros((N, 2), np.float32)
    ch = SND.make("chime")
    i = int((T_LOGO + 0.05) * SR); sfx[i:i + len(ch)] += ch[:N - i] * 10 ** (-21 / 20)
    for name, mus in (("mix_music", True), ("mix_nomusic", False)):
        mix = v + sfx + (m if mus else 0)
        p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af",
                            "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], input=mix.astype(np.float32).tobytes(),
                           capture_output=True)
        j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr.decode(), re.S).group(0))
        mix = ffilter(mix, f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
                           f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,"
                           f"alimiter=limit=0.85:level=false")[:N]
        sf.write(f"{W}/{name}.wav", mix, SR)
        print("wrote", name, len(mix) / SR)


if __name__ == "__main__":
    if sys.argv[1] == "--audio":
        audio()
    elif sys.argv[1] == "--stills":
        os.makedirs(sys.argv[3], exist_ok=True)
        render(sys.argv[3], [float(x) for x in sys.argv[2].split(",")])
    else:
        render(sys.argv[1])
        print("done", TOTAL, "frames", T_END)
