# Subtle UI-style sound effects and a warm minimal music bed — all synthesised (royalty-free).
import numpy as np
from scipy import signal
import sounds as S0
from sounds import SR, rng, t_, env, sweep, bp, hp, lp, norm, stereo, stft_band_noise, bell

# ------------------------------------------------------------------ effects
def tick(pitch=1.0, **_):
    n = int(0.06 * SR)
    f = 2600 * pitch
    x = np.sin(2 * np.pi * f * t_(0.06)) * env(n, 0.0006, 0.007)
    x += 0.5 * np.sin(2 * np.pi * f * 1.5 * t_(0.06)) * env(n, 0.0004, 0.004)
    x += hp(rng.standard_normal(n), 3500) * env(n, 0.0002, 0.0015) * 0.25
    return norm(x, 0.35)


def swipe(**_):
    d = 0.24
    x = stft_band_noise(d, [900, 2200, 3600, 2600], [0.5, 0.45, 0.5, 0.6], [0, 0.8, 1.0, 0])
    return norm(x, 0.35)


def whoosh(dur=0.4, pan=0.0, **_):
    x = stft_band_noise(dur, [400, 1500, 2800, 1000], [0.55, 0.5, 0.5, 0.6], [0, 0.7, 1.0, 0])
    x = norm(x, 0.45)
    p = np.linspace(-pan, pan, len(x)) if pan else np.zeros(len(x))
    l, r = np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)
    return np.stack([x * l, x * r], 1) * 1.414


def slide(**_):
    d = 0.36
    x = stft_band_noise(d, [260, 700, 1300, 600], [0.5, 0.5, 0.5, 0.5], [0, 0.8, 1.0, 0])
    return norm(x, 0.3)


def scratch(**_):
    d = 0.2
    n = int(d * SR)
    x = bp(rng.standard_normal(n), 2200, 7000)
    x *= (0.55 + 0.45 * np.sin(2 * np.pi * 38 * t_(d))) * np.hanning(n) ** 0.6
    return norm(x, 0.3)


def check(pitch=1.0, **_):
    a = bell(1318.5 * pitch, 0.32, ((1, 1, 1.0), (2.0, 0.25, 0.4)))
    b = bell(1760.0 * pitch, 0.45, ((1, 1, 1.0), (2.0, 0.2, 0.4)))
    x = np.zeros(int(0.6 * SR))
    x[:len(a)] += a * 0.7
    o = int(0.07 * SR)
    x[o:o + len(b)] += b
    return norm(x, 0.32)


def plop(pitch=1.0, **_):
    d = 0.22
    n = int(d * SR)
    f = 260 * pitch * (1 + 2.2 * np.exp(-t_(d) * 38))                     # droplet: pitch falls quickly
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.05)
    x += 0.5 * hp(rng.standard_normal(n), 1500) * env(n, 0.0005, 0.012)
    x += 0.4 * np.sin(2 * np.pi * 90 * t_(d)) * env(n, 0.002, 0.04)
    return norm(x, 0.5)


def pour(dur=1.2, **_):
    n = int(dur * SR)
    x = bp(rng.standard_normal(n), 700, 3800)
    x *= (0.75 + 0.25 * np.sin(2 * np.pi * 9 * t_(dur) + 1.0)) * np.hanning(n) ** 0.5
    return norm(x, 0.3)


def sweep_fx(dur=0.9, **_):
    x = stft_band_noise(dur, [500, 900, 1600, 700], [0.6, 0.6, 0.6, 0.6], [0.0, 0.6, 0.7, 0.0])
    return norm(x, 0.22)


def key(pitch=1.0, **_):
    n = int(0.05 * SR)
    x = hp(rng.standard_normal(n), 1800) * env(n, 0.0002, 0.003)
    x += 0.5 * np.sin(2 * np.pi * 1300 * pitch * t_(0.05)) * env(n, 0.0003, 0.008)
    return norm(x, 0.35)


def send(**_):
    d = 0.4
    n = int(d * SR)
    x = stft_band_noise(d, [900, 2500, 5000], [0.5, 0.5, 0.5], [0, 1.0, 0.0])
    x = norm(x, 0.3) + 0.3 * np.sin(2 * np.pi * np.cumsum(900 + 1500 * (t_(d) / d) ** 2) / SR) * env(n, 0.005, 0.12)
    ping = bell(2093, 0.4, ((1, 1, 1.0), (2.0, 0.2, 0.4)))
    y = np.zeros(int(0.6 * SR)); y[:len(x)] += x; o = int(0.2 * SR); y[o:o + len(ping)] += ping * 0.5
    return norm(y, 0.35)


def pop(pitch=1.0, **_):
    d = 0.12
    x = sweep(820 * pitch, 240 * pitch, d) * env(int(d * SR), 0.001, 0.03)
    x += 0.2 * sweep(1700 * pitch, 450 * pitch, d) * env(int(d * SR), 0.001, 0.012)
    return norm(x, 0.5)


def chime(**_):
    x = np.zeros(int(1.6 * SR))
    for i, f in enumerate((1046.5, 1568.0, 2093.0)):
        b = bell(f, 1.3) * (0.8 - 0.2 * i)
        o = int(i * 0.07 * SR)
        x[o:o + len(b)] += b
    return norm(x, 0.35)


def riser(dur=1.0, **_):
    n = int(dur * SR)
    x = stft_band_noise(dur, [600, 1500, 3500, 7000], [0.4, 0.4, 0.4, 0.4], [0.05, 0.3, 0.7, 1.0])
    x = norm(x, 0.3)
    x[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    return x


SFX = dict(tick=tick, swipe=swipe, whoosh=whoosh, slide=slide, scratch=scratch, check=check, plop=plop, pour=pour,
           sweep=sweep_fx, key=key, send=send, pop=pop, chime=chime, riser=riser)


def make(name, **kw):
    x = SFX[name](**kw)
    return stereo(x, kw.get("pan", 0.0)) if x.ndim == 1 else x


# ------------------------------------------------------------------ music bed
def _pad(freqs, d, vel=1.0):
    n = int(d * SR)
    t = t_(d)
    x = np.zeros(n)
    for f in freqs:
        for det in (-0.004, 0.0, 0.004):
            x += np.sin(2 * np.pi * f * (1 + det) * t) + 0.35 * np.sin(2 * np.pi * 2 * f * (1 + det) * t) * 0.5
    a = np.minimum(1, t / 0.7) * np.minimum(1, (d - t) / 0.9)
    return lp(x, 1500) * a * vel / (len(freqs) * 3)


def _pluck(f, d=1.3, vel=1.0):
    n = int(d * SR)
    t = t_(d)
    x = np.sin(2 * np.pi * f * t) * env(n, 0.003, 0.34)
    x += 0.30 * np.sin(2 * np.pi * 2 * f * t) * env(n, 0.002, 0.12)
    x += 0.10 * np.sin(2 * np.pi * 3.01 * f * t) * env(n, 0.001, 0.05)
    return x * vel


def music(total, promo_at, outro_at):
    bpm = 92
    beat = 60 / bpm
    bar = 4 * beat
    N = int((total + 3) * SR)
    pad = np.zeros(N); mel = np.zeros(N); bass = np.zeros(N); drums = np.zeros(N)
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [(48, 55, 59, 64), (45, 52, 57, 60), (41, 48, 52, 57), (43, 50, 55, 59)]     # Cmaj7 Am7 Fmaj7 G6
    arp = [0, 2, 3, 2, 1, 2, 3, 1]

    def put(buf, x, tt, g=1.0):
        i = int(tt * SR)
        if 0 <= i < N:
            x = x[:N - i]
            buf[i:i + len(x)] += x * g

    t = 0.0; bi = 0
    while t < outro_at:
        ch = prog[bi % 4]
        put(pad, _pad([midi(m) for m in ch[1:]], bar + 0.9), t, 0.9)
        for k in range(8):
            tt = t + k * beat / 2 + (0.02 if k % 2 else 0)
            if tt >= outro_at: break
            if tt < promo_at and k % 2 and bi < 2:      # open sparsely
                continue
            m = ch[arp[k] % len(ch)] + 12
            put(mel, _pluck(midi(m), 1.2, 0.8 if k % 2 == 0 else 0.5), tt)
        for b in (0, 2):
            r = midi(ch[0])
            d = beat * (1.6 if b == 0 else 1.2)
            tb = t_(d)
            put(bass, np.sin(2 * np.pi * r * tb) * np.minimum(1, tb / 0.01) * np.exp(-tb / (d * 0.65)), t + b * beat, 0.7)
        if t >= promo_at - 0.05:                          # promo lifts: soft kick + shaker
            for b in range(4):
                tb = t + b * beat
                if b in (0, 2):
                    put(drums, sweep(100, 48, 0.28) * env(int(0.28 * SR), 0.002, 0.07), tb, 0.8)
                for h in range(2):
                    put(drums, hp(rng.standard_normal(int(0.05 * SR)), 7000) * env(int(0.05 * SR), 0.003, 0.01), tb + h * beat / 2 + (0.02 if h else 0), 0.09 if h else 0.06)
        t += bar; bi += 1
    ch = prog[0]
    put(pad, _pad([midi(m) for m in ch], 3.4), outro_at, 1.0)
    for k, m in enumerate([ch[1], ch[2], ch[3], ch[3] + 12]):
        put(mel, _pluck(midi(m + 12), 2.4, 0.7), outro_at + k * 0.05)
    put(bass, np.sin(2 * np.pi * midi(ch[0]) * t_(2.5)) * np.exp(-t_(2.5) / 1.0), outro_at, 0.7)
    mix = stereo(norm(pad, 0.5) * 0.5 + norm(mel, 0.5) * 0.8 + hp(norm(bass, 0.5), 50) * 0.38 + hp(norm(drums, 0.5), 60) * 0.34)
    ir_n = int(1.2 * SR); ir_t = t_(1.2)
    ir = np.stack([lp(rng.standard_normal(ir_n) * np.exp(-ir_t / 0.32), 5500) for _ in range(2)], 1)
    wet = np.stack([signal.fftconvolve(mix[:, c], ir[:, c])[:N] for c in range(2)], 1)
    wet = norm(wet, np.max(np.abs(mix)) * 0.5)
    return (mix + 0.3 * wet)[:int(total * SR)]
