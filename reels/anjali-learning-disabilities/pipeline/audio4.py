# Soundtrack: light denoise + levelled, EQ'd voice; quiet SFX on graphics; an understated piano-pad bed that ducks under
# speech, resolves on the brand frame and fades out naturally; two-pass loudnorm master (-14 LUFS).
import os, subprocess
import numpy as np
from scipy import signal
import soundfile_shim as sf
import design4 as D
import sounds2 as S
from sounds import t_, lp, hp, norm, stereo, rng
from timeline3 import SPEED, FPS

W = os.environ["WORK"]
SR = S.SR
VOICE_TARGET_DB = -23.0
VOICE_CHAIN = ("afftdn=nr=8:nf=-55:tn=1,highpass=f=80,equalizer=f=250:t=q:w=1.0:g=-2,equalizer=f=3200:t=q:w=1.2:g=2,"
               "equalizer=f=8500:t=q:w=1.0:g=1.0,deesser=i=0.25,acompressor=threshold=-22dB:ratio=2.4:attack=8:release=160:makeup=2")


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def ffilter(x, af):
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af", af,
                        "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], input=x.astype(np.float32).tobytes(),
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()


def active_db(x):
    m = x.mean(1)
    hop = SR // 100
    n = len(m) // hop
    r = np.sqrt((m[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(r)
    act = db > (db.max() - 30)
    return 20 * np.log10(np.sqrt((r[act] ** 2).mean()) + 1e-12)


def fade(x, ms=8):
    f = int(ms / 1000 * SR)
    x = x.copy()
    x[:f] *= np.linspace(0, 1, f)[:, None]
    x[-f:] *= np.linspace(1, 0, f)[:, None]
    return x


def voice():
    """Each sentence is levelled to the same loudness (gain changes sit in the silences between sentences),
    then the kept pieces are joined with short fades and cleaned up."""
    import json
    src = {i: decode(f"{W}/shot{i}.mp4") for i in (1, 2, 3)}
    segs = json.load(open(f"{W}/segments.json"))
    gain = {i: np.ones(len(src[i]), np.float32) for i in src}
    for i in src:
        ss = [s for s in segs if s["shot"] == i]
        bounds = [0] + [int((ss[k]["out"] + ss[k + 1]["in"]) / 2 * SR) for k in range(len(ss) - 1)] + [len(src[i])]
        gs = []
        for k, s in enumerate(ss):
            lev = active_db(src[i][int(s["in"] * SR):int(s["out"] * SR)])
            gs.append(10 ** (np.clip(VOICE_TARGET_DB - lev, -9, 20) / 20))
        for k, g in enumerate(gs):
            gain[i][bounds[k]:bounds[k + 1]] = g
        r = int(0.05 * SR)
        gain[i] = np.convolve(np.pad(gain[i], r, mode="edge"), np.ones(2 * r + 1) / (2 * r + 1), "valid")[:len(src[i])].astype(np.float32)
    out = []
    for p in D.PIECES:
        a, b = int(p["f_in"] / FPS * SR), int(p["f_out"] / FPS * SR)
        out.append(fade(src[p["shot"]][a:b] * gain[p["shot"]][a:b, None], 12))
    return ffilter(np.concatenate(out), f"atempo={SPEED},{VOICE_CHAIN}")


def music(total, resolve_at, end_at):
    """Slow (66 bpm) warm pad with sparse soft plucks; resolves to the tonic on the brand frame and dies away by end_at."""
    beat = 60 / 66
    bar = 4 * beat
    N = int((total + 4) * SR)
    pad = np.zeros(N); mel = np.zeros(N); bass = np.zeros(N)
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [(41, 48, 52, 57), (45, 52, 55, 60), (43, 50, 55, 59), (48, 52, 55, 59)]     # Fmaj7 Am G Cmaj7
    pat = [(0, 3), (1.5, 2), (2, 1), (3, 2)]                                           # (beat, chord tone)

    def put(buf, x, tt, g=1.0):
        i = int(tt * SR)
        if 0 <= i < N:
            x = x[:N - i]
            buf[i:i + len(x)] += x * g

    t, bi = 0.0, 0
    while t < resolve_at - 0.05:
        ch = prog[bi % 4]
        put(pad, S._pad([midi(m) for m in ch[1:]], bar + 1.2), t, 0.85 if bi else 0.6)
        for b, k in pat:
            tt = t + b * beat
            if tt >= resolve_at - 0.05:
                break
            if bi == 0 and b > 0:
                continue
            put(mel, S._pluck(midi(ch[k] + 12), 1.6, 0.55 if b % 2 else 0.7), tt)
        tb = t_(bar)
        put(bass, np.sin(2 * np.pi * midi(ch[0]) * tb) * np.minimum(1, tb / 0.02) * np.exp(-tb / 1.6), t, 0.55)
        t += bar; bi += 1
    ch = (48, 55, 59, 64)                                                              # Cmaj7 resolution under the logo
    put(pad, S._pad([midi(m) for m in ch[1:]], end_at - resolve_at + 1.0), resolve_at, 0.9)
    for k, m in enumerate([ch[1], ch[2], ch[3], ch[3] + 12]):
        put(mel, S._pluck(midi(m + 12), 3.0, 0.5), resolve_at + 0.12 * k)
    tb = t_(3.5)
    put(bass, np.sin(2 * np.pi * midi(ch[0]) * tb) * np.minimum(1, tb / 0.02) * np.exp(-tb / 1.4), resolve_at, 0.55)
    mix = stereo(norm(pad, 0.5) * 0.55 + norm(mel, 0.5) * 0.7 + hp(norm(bass, 0.5), 45) * 0.3)
    ir_n = int(1.6 * SR); ir_t = t_(1.6)
    ir = np.stack([lp(rng.standard_normal(ir_n) * np.exp(-ir_t / 0.45), 5000) for _ in range(2)], 1)
    wet = np.stack([signal.fftconvolve(mix[:, c], ir[:, c])[:N] for c in range(2)], 1)
    wet = norm(wet, np.max(np.abs(mix)) * 0.55)
    out = (mix + 0.35 * wet)[:int(total * SR)]
    a, b = int((end_at - 2.6) * SR), int(end_at * SR)                                  # natural fade-out, no hard stop
    out[a:b] *= (np.cos(np.linspace(0, np.pi / 2, b - a)) ** 1.5)[:, None]
    out[b:] = 0
    return out


def master(mix):
    import json, re
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], input=mix.astype(np.float32).tobytes(),
                       capture_output=True)
    j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr.decode(), re.S).group(0))
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,alimiter=limit=0.85:level=false")
    return ffilter(mix, af)


def place(buf, x, t, gain_db):
    i = int(round(t * SR))
    if i < 0:
        x, i = x[-i:], 0
    x = x[:len(buf) - i]
    buf[i:i + len(x)] += x * 10 ** (gain_db / 20)


def main():
    N = int(round(D.TOTAL * SR))
    vbuf = np.zeros((N, 2), np.float32)
    v = voice()
    vbuf[:min(N, len(v))] += v[:N]
    print("voice %.2fs (timeline says %.2fs)" % (len(v) / SR, D.T_EXP_END))
    sbuf = np.zeros((N, 2), np.float32)
    for e in D.SFX:
        kw = {k: x for k, x in e.items() if k not in ("t", "name", "gain")}
        place(sbuf, S.make(e["name"], **kw), e["t"], e["gain"] - 7)
    m = music(D.TOTAL, D.T_LOGO, D.T_END - 0.05)
    mbuf = np.zeros((N, 2), np.float32)
    mbuf[:len(m)] = m[:N]
    vm = np.abs(vbuf.mean(1))
    hop = SR // 100
    n = len(vm) // hop
    r = np.sqrt((vm[:n * hop].reshape(n, hop) ** 2).mean(1))
    act = (20 * np.log10(r + 1e-9) > -48).astype(float)
    sm = np.zeros_like(act)
    for i in range(1, len(act)):
        k = 0.12 if act[i] > sm[i - 1] else 0.015                                   # slow, gentle ducking: no pumping
        sm[i] = sm[i - 1] + k * (act[i] - sm[i - 1])
    duck = np.repeat(10 ** (-6 * sm / 20), hop)
    duck = np.pad(duck, (0, N - len(duck)), constant_values=1)[:N]
    mbuf *= (duck * 10 ** (-12.5 / 20))[:, None]
    i0 = int(D.T_CREAM0 * SR)                                                         # bed comes up a little on the brand frame
    lift = np.ones(N)
    lift[i0:] = 1 + 0.35 * np.minimum(1, np.arange(N - i0) / SR / 1.2)
    mbuf *= lift[:, None]
    sf.write(f"{W}/voice_only.wav", vbuf, SR)
    for name, mus in (("mix_music", True), ("mix_nomusic", False)):
        mix = vbuf + sbuf + (mbuf if mus else 0)
        mix = master(mix)[:N]
        sf.write(f"{W}/{name}.wav", mix, SR)
        print("wrote", name, len(mix) / SR)


if __name__ == "__main__":
    main()
