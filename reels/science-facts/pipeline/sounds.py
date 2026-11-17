# Synthesised sound effects and a light kalimba music bed (all generated, royalty-free).
import numpy as np
from scipy import signal

SR = 48000
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def env(n, a, d):
    """attack seconds, exponential decay time-constant d."""
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


def sweep(f0, f1, d, curve="exp"):
    t = t_(d)
    if curve == "exp":
        f = f0 * (f1 / f0) ** (t / d)
    else:
        f = f0 + (f1 - f0) * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="low", fs=SR, output="sos"), x)


def norm(x, peak=0.5):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def stereo(x, pan=0.0):
    if x.ndim == 2:
        return x
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([x * l * 1.414, x * r * 1.414], 1)


def stft_band_noise(d, centers, widths, amp):
    """Noise shaped by a time-varying band (via STFT masking). centers/widths/amp: arrays over time 0..1."""
    n = int(d * SR)
    x = rng.standard_normal(n + 2048)
    f, tt, Z = signal.stft(x, SR, nperseg=1024)
    pos = np.clip(tt / d, 0, 1)
    c = np.interp(pos, np.linspace(0, 1, len(centers)), centers)
    w = np.interp(pos, np.linspace(0, 1, len(widths)), widths)
    a = np.interp(pos, np.linspace(0, 1, len(amp)), amp)
    mask = np.exp(-0.5 * ((np.log(f[:, None] + 1) - np.log(c[None, :])) / w[None, :]) ** 2) * a[None, :]
    _, y = signal.istft(Z * mask, SR, nperseg=1024)
    return y[:n]


# ------------------------------------------------------------------ effects
def whoosh(dur=0.45, pan=0.0, **_):
    x = stft_band_noise(dur, [500, 1800, 3200, 1200], [0.5, 0.45, 0.5, 0.6], [0, 0.7, 1.0, 0])
    x = norm(x, 0.55)
    p = np.linspace(-pan, pan, len(x)) if pan else np.zeros(len(x))
    l, r = np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)
    return np.stack([x * l, x * r], 1) * 1.414


def swoosh(**k):
    return whoosh(0.28, **k) * 0.8


def tick(f=3200, **_):
    n = int(0.05 * SR)
    x = np.sin(2 * np.pi * f * t_(0.05)) * env(n, 0.0005, 0.006)
    x += hp(rng.standard_normal(n), 2500) * env(n, 0.0002, 0.002) * 0.6
    return norm(x, 0.35)


def tock(**k):
    return tick(2300) * 0.85


def pop(pitch=1.0, **_):
    d = 0.14
    x = sweep(950 * pitch, 260 * pitch, d) * env(int(d * SR), 0.001, 0.035)
    x += sweep(1900 * pitch, 500 * pitch, d) * env(int(d * SR), 0.001, 0.012) * 0.25
    return norm(x, 0.6)


def horn(**_):
    out = []
    for _ in range(2):
        t = t_(0.13)
        x = sum(np.sin(2 * np.pi * f * h * t) / h for f in (466, 587) for h in (1, 3, 5))
        x *= np.minimum(1, np.minimum(t / 0.008, (0.13 - t) / 0.02))
        out += [x, np.zeros(int(0.06 * SR))]
    return norm(lp(np.concatenate(out), 3500), 0.45)


def boing(**_):
    d = 0.55
    t = t_(d)
    f = 190 + 120 * np.exp(-t * 6) + 35 * np.sin(2 * np.pi * 16 * t) * np.exp(-t * 3)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.003, 0.22)
    return norm(x, 0.6)


def question(**_):
    a = sweep(520, 560, 0.09, "lin") * env(int(0.09 * SR), 0.004, 0.05)
    b = sweep(700, 940, 0.2, "lin") * env(int(0.2 * SR), 0.004, 0.09)
    x = np.concatenate([a, np.zeros(int(0.03 * SR)), b])
    x = x + 0.2 * np.sign(x) * np.abs(x) ** 2  # a little warmth
    return norm(x, 0.5)


def thump(**_):
    d = 0.45
    x = sweep(120, 42, d) * env(int(d * SR), 0.002, 0.12)
    x += lp(rng.standard_normal(int(d * SR)), 900) * env(int(d * SR), 0.0005, 0.01) * 0.3
    return norm(np.tanh(x * 1.5), 0.8)


def hit(**_):
    d = 1.0
    n = int(d * SR)
    x = sweep(95, 36, d) * env(n, 0.002, 0.28)
    x += lp(rng.standard_normal(n), 1500) * env(n, 0.0005, 0.05) * 0.5
    x += bp(rng.standard_normal(n), 2000, 6000) * env(n, 0.0005, 0.02) * 0.25
    return norm(np.tanh(x * 2.0), 0.85)


def bell(f0, d=1.2, partials=((1, 1, 1.0), (2.0, 0.35, 0.45), (3.0, 0.15, 0.25), (4.2, 0.08, 0.12))):
    n = int(d * SR)
    t = t_(d)
    return sum(a * np.sin(2 * np.pi * f0 * r * t) * env(n, 0.002, d * dd * 0.35) for r, a, dd in partials)


def chime(**_):
    x = np.zeros(int(1.4 * SR))
    for i, f in enumerate((1046.5, 1318.5, 1568.0)):
        b = bell(f, 1.2) * (0.8 - 0.15 * i)
        o = int(i * 0.06 * SR)
        x[o:o + len(b)] += b
    return norm(x, 0.45)


def ding(pitch=1.0, **_):
    return norm(bell(784 * pitch, 0.9), 0.45)


def sparkle(**_):
    x = np.zeros(int(1.2 * SR))
    notes = [1568, 2093, 2349, 2637, 3136, 3520, 4186]
    for i in range(9):
        f = notes[rng.integers(len(notes))]
        b = bell(f, 0.5, ((1, 1, 1.0), (2.01, 0.2, 0.4))) * (0.9 - 0.06 * i)
        o = int((i * 0.045 + rng.uniform(0, 0.02)) * SR)
        x[o:o + len(b)] += b
    return stereo(norm(x, 0.4), 0) * np.array([1.0, 0.85]) + 0


def buzz(**_):
    out = []
    for f in (233, 185):
        t = t_(0.12)
        x = signal.square(2 * np.pi * f * t, 0.5) * np.minimum(1, np.minimum(t / 0.005, (0.12 - t) / 0.03))
        out += [x, np.zeros(int(0.03 * SR))]
    return norm(lp(np.concatenate(out), 1800, 4), 0.35)


def riser(dur=2.5, **_):
    n = int(dur * SR)
    x = stft_band_noise(dur, [500, 1200, 3000, 7000], [0.35, 0.35, 0.4, 0.4], [0.05, 0.25, 0.6, 1.0])
    s = sweep(180, 720, dur) * np.linspace(0, 1, n) ** 2 * 0.35
    x = norm(x, 0.5) + s[:len(x)]
    x[-int(0.04 * SR):] *= np.linspace(1, 0, int(0.04 * SR))
    return norm(x, 0.5)


SFX = dict(whoosh=whoosh, swoosh=swoosh, tick=tick, tock=tock, pop=pop, horn=horn, boing=boing, question=question,
           thump=thump, hit=hit, chime=chime, ding=ding, sparkle=sparkle, buzz=buzz, riser=riser)


def make(name, **kw):
    x = SFX[name](**kw)
    return stereo(x, kw.get("pan", 0.0)) if x.ndim == 1 else x


# ------------------------------------------------------------------ music bed
def kalimba(f, d=1.6, vel=1.0):
    n = int(d * SR)
    t = t_(d)
    x = np.sin(2 * np.pi * f * t) * env(n, 0.003, 0.45)
    x += 0.18 * np.sin(2 * np.pi * f * 2 * t) * env(n, 0.002, 0.12)
    x += 0.07 * np.sin(2 * np.pi * f * 5.4 * t) * env(n, 0.001, 0.03)
    x += 0.05 * hp(rng.standard_normal(n), 3000) * env(n, 0.0003, 0.004)
    return x * vel


def music(total, sections):
    """sections: dict with times: groove_on, lift_on, outro_at."""
    bpm = 100
    beat = 60 / bpm
    bar = 4 * beat
    N = int((total + 2) * SR)
    mel = np.zeros(N)
    bass = np.zeros(N)
    drums = np.zeros(N)
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)]  # C G Am F
    pattern = [0, 2, 1, 3, 2, 1, 3, 2]

    def put(buf, x, t, g=1.0):
        i = int(t * SR)
        if i >= N:
            return
        x = x[:N - i]
        buf[i:i + len(x)] += x * g

    t = 0.0
    bi = 0
    groove, lift, outro = sections["groove_on"], sections["lift_on"], sections["outro_at"]
    while t < outro:
        ch = prog[bi % 4]
        notes = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[0] + 24]
        for k in range(8):
            tt = t + k * beat / 2 + (0.03 if k % 2 else 0)  # light swing
            if tt >= outro:
                break
            if tt < groove and k % 2:
                continue
            vel = 0.8 if k % 2 == 0 else 0.55
            put(mel, kalimba(midi(notes[pattern[k]]), 1.4, vel), tt)
        if t >= lift:  # glockenspiel sprinkles
            for k, m in enumerate([ch[2] + 24, ch[1] + 24, ch[0] + 36]):
                put(mel, bell(midi(m), 0.9) * 0.22, t + beat * (1.5 + k))
        if t >= groove:
            r = midi(ch[0] - 24)
            for (bt, dd) in ((0, beat * 1.4), (2.5 * beat, beat * 0.9)):
                n = int(dd * SR)
                tb = t_(dd)
                x = (np.sin(2 * np.pi * r * tb) + 0.25 * np.sin(4 * np.pi * r * tb)) * np.minimum(1, tb / 0.01) * np.exp(-tb / (dd * 0.7))
                put(bass, x, t + bt)
            for b in range(4):
                tb = t + b * beat
                if b in (0, 2):
                    put(drums, sweep(95, 48, 0.3) * env(int(0.3 * SR), 0.002, 0.07), tb, 0.9)
                else:
                    put(drums, bp(rng.standard_normal(int(0.12 * SR)), 1200, 3500) * env(int(0.12 * SR), 0.001, 0.03), tb, 0.35)
                for h in range(2):
                    th = tb + h * beat / 2 + (0.03 if h else 0)
                    put(drums, hp(rng.standard_normal(int(0.06 * SR)), 6500) * env(int(0.06 * SR), 0.004, 0.012), th, 0.16 if h else 0.1)
        t += bar
        bi += 1
    # outro: final chord ring
    ch = prog[0]
    for k, m in enumerate([ch[0], ch[1], ch[2], ch[0] + 12, ch[1] + 12, ch[2] + 12]):
        put(mel, kalimba(midi(m + 12), 2.5, 0.7), outro + k * 0.045)
    put(mel, bell(midi(ch[2] + 24), 2.0) * 0.3, outro + 0.3)
    put(bass, np.sin(2 * np.pi * midi(ch[0] - 24) * t_(2.0)) * np.exp(-t_(2.0) / 0.9), outro)
    put(drums, sweep(95, 45, 0.5) * env(int(0.5 * SR), 0.002, 0.12), outro, 0.9)

    mel = norm(mel, 0.5)
    bass = norm(bass, 0.5)
    drums = norm(drums, 0.5)
    mix = stereo(mel * 0.85 + hp(bass, 55) * 0.32 + hp(drums, 70) * 0.32)
    # simple stereo reverb
    ir_n = int(1.3 * SR)
    ir_t = t_(1.3)
    ir = np.stack([rng.standard_normal(ir_n) * np.exp(-ir_t / 0.35) for _ in range(2)], 1)
    ir[:, 0] = lp(ir[:, 0], 6000)
    ir[:, 1] = lp(ir[:, 1], 6000)
    wet = np.stack([signal.fftconvolve(mix[:, c], ir[:, c])[:N] for c in range(2)], 1)
    wet = norm(wet, np.max(np.abs(mix)) * 0.5)
    out = mix + 0.35 * wet
    return out[:int(total * SR)]
