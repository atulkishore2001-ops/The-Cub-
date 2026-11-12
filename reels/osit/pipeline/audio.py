# OSIT ad soundtrack (adapted from the Saisha reel): the kept voice pieces (each section levelled to the same loudness, 10 ms fades at every splice),
# played 1.025x with pitch preserved, cleaned (light denoise, EQ, de-esser, gentle compression); a quiet warm
# piano-pad bed that ducks under speech and resolves on the logo; a soft swish for the name card and a chime on the
# logo reveal. Two masters at -14 LUFS: with music and voice + effects only.
import os, json, subprocess, re
import numpy as np
from scipy import signal
import soundfile_shim as sf
import sounds2 as S
from sounds import t_, lp, hp, norm, stereo, rng

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.environ["WORK"]
SR = S.SR
TL = json.load(open(f"{W}/timeline.json"))
SPEED = TL["speed"]
EDL = json.load(open(f"{HERE}/edl.json"))
VOICE_TARGET_DB = -23.0
VOICE_CHAIN = ("afftdn=nr=6:nf=-60:tn=1,highpass=f=80,dynaudnorm=f=150:g=7:p=0.9:m=6:r=0.3,equalizer=f=250:t=q:w=1.0:g=-2,equalizer=f=3200:t=q:w=1.2:g=2,"
               "equalizer=f=8500:t=q:w=1.0:g=1.0,deesser=i=0.2,acompressor=threshold=-22dB:ratio=2.4:attack=8:release=160:makeup=2")


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def ffilter(x, af):
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af", af, "-f", "f32le", "-ac", "2",
                        "-ar", str(SR), "-"], input=x.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()


def active_db(x):
    m = x.mean(1); hop = SR // 100; n = len(m) // hop
    r = np.sqrt((m[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(r); act = db > (db.max() - 30)
    return 20 * np.log10(np.sqrt((r[act] ** 2).mean()) + 1e-12)


def fade(x, ms=10):
    f = int(ms / 1000 * SR); x = x.copy()
    x[:f] *= np.linspace(0, 1, f)[:, None]; x[-f:] *= np.linspace(1, 0, f)[:, None]
    return x


def voice():
    src = {1: decode(f"{W}/shot1.mp4")}
    secs = []
    for p in TL["pieces"]:
        x = fade(src[p["shot"]][int(p["a"] * SR):int(p["b_audio"] * SR)])
        if not secs or secs[-1][0] != p["sec"]:
            secs.append([p["sec"], [], []])
        secs[-1][1].append(x)
        secs[-1][2].append(np.zeros((int(round(p["hold"] * SPEED * SR)), 2), np.float32))   # a hold plays as silence
    out = []
    for _, parts, holds in secs:
        g = 10 ** (np.clip(VOICE_TARGET_DB - active_db(np.concatenate(parts)), -9, 20) / 20)
        for x, h in zip(parts, holds):
            out += [x * g, h]
    return ffilter(np.concatenate(out), f"atempo={SPEED},{VOICE_CHAIN}")


def music(total, resolve_at, end_at):
    """Light, upbeat corporate bed (100 bpm, C - G - Am - F): soft pad, eighth-note pluck arpeggio, gentle kick on 1 and 3,
    a quiet shaker. Resolves on C when the closing frame appears and fades out by end_at."""
    bpm = 100; beat = 60 / bpm; bar = 4 * beat
    N = int((total + 4) * SR)
    pad = np.zeros(N); mel = np.zeros(N); bass = np.zeros(N); kick = np.zeros(N); shk = np.zeros(N)
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [(48, 52, 55, 60), (43, 50, 55, 59), (45, 52, 57, 60), (41, 48, 53, 57)]

    def put(buf, x, tt, g=1.0):
        i = int(tt * SR)
        if 0 <= i < N:
            x = x[:N - i]; buf[i:i + len(x)] += x * g
    kd = t_(0.35); kx = np.sin(2 * np.pi * (45 * kd + 70 / 18 * (1 - np.exp(-18 * kd)))) * np.exp(-kd / 0.12)
    sd = int(0.06 * SR); sx = hp(rng.standard_normal(sd), 6000) * np.exp(-np.linspace(0, 6, sd))
    t, bi = 0.0, 0
    while t < resolve_at - 0.05:
        ch = prog[bi % 4]
        put(pad, S._pad([midi(m) for m in ch[1:]], bar + 0.8), t, 0.7)
        arp = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 24, ch[3] + 12, ch[2] + 12, ch[3] + 12]
        for k, m in enumerate(arp):
            tt = t + k * beat / 2
            if tt >= resolve_at - 0.05:
                break
            put(mel, S._pluck(midi(m), 0.9, 0.62 if k % 2 == 0 else 0.45), tt)
            if bi >= 1:
                put(shk, sx, tt, 0.5 if k % 2 else 0.3)
        for k in (0, 2):
            if bi >= 1 and t + k * beat < resolve_at - 0.05:
                put(kick, kx, t + k * beat)
        tb = t_(bar)
        put(bass, np.sin(2 * np.pi * midi(ch[0] - 12) * tb) * np.minimum(1, tb / 0.02) * np.exp(-tb / 1.2), t, 0.6)
        t += bar; bi += 1
    ch = (48, 55, 60, 64)
    put(pad, S._pad([midi(m) for m in ch[1:]], end_at - resolve_at + 1.0), resolve_at, 0.85)
    for k, m in enumerate([ch[1], ch[2], ch[3], ch[2] + 12]):
        put(mel, S._pluck(midi(m + 12), 2.5, 0.5), resolve_at + 0.10 * k)
    tb = t_(3.0)
    put(bass, np.sin(2 * np.pi * midi(36) * tb) * np.minimum(1, tb / 0.02) * np.exp(-tb / 1.4), resolve_at, 0.6)
    mix = stereo(norm(pad, 0.5) * 0.45 + norm(mel, 0.5) * 0.65 + hp(norm(bass, 0.5), 40) * 0.35 + norm(kick, 0.5) * 0.30 + norm(shk, 0.5) * 0.10)
    ir_n = int(1.2 * SR); ir_t = t_(1.2)
    ir = np.stack([lp(rng.standard_normal(ir_n) * np.exp(-ir_t / 0.35), 6000) for _ in range(2)], 1)
    wet = np.stack([signal.fftconvolve(mix[:, c], ir[:, c])[:N] for c in range(2)], 1)
    wet = norm(wet, np.max(np.abs(mix)) * 0.45)
    out = (mix + 0.25 * wet)[:int(total * SR)]
    a, b = int((end_at - 2.2) * SR), int(end_at * SR)
    out[a:b] *= (np.cos(np.linspace(0, np.pi / 2, b - a)) ** 1.5)[:, None]
    out[b:] = 0
    return out


def master(mix):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], input=mix.astype(np.float32).tobytes(), capture_output=True)
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
    total = TL["total"]; N = int(round(total * SR))
    v = voice()
    print("voice %.2fs (timeline speech %.2fs)" % (len(v) / SR, TL["t_speech_end"]))
    vbuf = np.zeros((N, 2), np.float32); vbuf[:min(N, len(v))] += v[:N]
    sbuf = np.zeros((N, 2), np.float32)
    for g in TL["graphics"]:
        k = g["kind"]
        if k == "pill":
            place(sbuf, S.make("pop", pitch=1.1), g["t_in"], -27)
        elif k in ("photo", "title", "logos", "date"):
            place(sbuf, S.make("whoosh", dur=0.4, pan=0.2), g["t_in"] - 0.05, -25)
        elif k in ("fast", "deadline"):
            place(sbuf, S.make("pop", pitch=0.9), g["t_in"], -24)
        elif k == "namecard":
            place(sbuf, S.make("whoosh", dur=0.45, pan=0.3), g["t_in"] + 0.15, -23)
    t_cl = TL["t_close"]
    place(sbuf, S.make("whoosh", dur=0.5), t_cl - 0.3, -22)
    place(sbuf, S.make("chime"), t_cl + 0.45, -16)
    m = music(total, t_cl - 0.05, total - 0.05)
    mbuf = np.zeros((N, 2), np.float32); mbuf[:len(m)] = m[:N]
    vm = np.abs(vbuf.mean(1)); hop = SR // 100; n = len(vm) // hop
    r = np.sqrt((vm[:n * hop].reshape(n, hop) ** 2).mean(1))
    act = (20 * np.log10(r + 1e-9) > -48).astype(float)
    sm = np.zeros_like(act)
    for i in range(1, len(act)):
        k = 0.12 if act[i] > sm[i - 1] else 0.015
        sm[i] = sm[i - 1] + k * (act[i] - sm[i - 1])
    duck = np.repeat(10 ** (-7 * sm / 20), hop)
    duck = np.pad(duck, (0, N - len(duck)), constant_values=1)[:N]
    mbuf *= (duck * 10 ** (-11.5 / 20))[:, None]
    i0 = int((t_cl - 0.3) * SR); lift = np.ones(N)
    lift[i0:] = 1 + 1.0 * np.minimum(1, np.arange(N - i0) / SR / 0.8)          # music comes up on the closing frame
    mbuf *= lift[:, None]
    for name, mus in (("mix_music", True), ("mix_nomusic", False)):
        mix = master(vbuf + sbuf + (mbuf if mus else 0))[:N]
        sf.write(f"{W}/{name}.wav", mix, SR)
        print("wrote", name, round(len(mix) / SR, 2))


if __name__ == "__main__":
    main()
