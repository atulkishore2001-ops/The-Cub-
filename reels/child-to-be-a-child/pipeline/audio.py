# Soundtrack: the kept voice pieces (each section levelled to the same loudness, 10 ms fades at every splice),
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
VOICE_CHAIN = ("afftdn=nr=6:nf=-60:tn=1,highpass=f=80,equalizer=f=250:t=q:w=1.0:g=-2,equalizer=f=3200:t=q:w=1.2:g=2,"
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
    src = {i: decode(f"{W}/shot{i}.mp4") for i in (1, 2, 3)}
    secs = []
    for p in TL["pieces"]:
        x = fade(src[p["shot"]][int(p["a"] * SR):int(p["b_audio"] * SR)])
        if not secs or secs[-1][0] != p["sec"]:
            secs.append([p["sec"], []])
        secs[-1][1].append(x)
    out = []
    for _, parts in secs:
        x = np.concatenate(parts)
        g = 10 ** (np.clip(VOICE_TARGET_DB - active_db(x), -9, 20) / 20)
        out.append(x * g)
    return ffilter(np.concatenate(out), f"atempo={SPEED},{VOICE_CHAIN}")


def music(total, resolve_at, end_at):
    """Slow (66 bpm) warm pad with sparse soft plucks (Fmaj7 Am G Cmaj7); resolves on the logo, fades out naturally."""
    beat = 60 / 66; bar = 4 * beat
    N = int((total + 4) * SR)
    pad = np.zeros(N); mel = np.zeros(N); bass = np.zeros(N)
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [(41, 48, 52, 57), (45, 52, 55, 60), (43, 50, 55, 59), (48, 52, 55, 59)]
    pat = [(0, 3), (1.5, 2), (2, 1), (3, 2)]

    def put(buf, x, tt, g=1.0):
        i = int(tt * SR)
        if 0 <= i < N:
            x = x[:N - i]; buf[i:i + len(x)] += x * g
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
    ch = (48, 55, 59, 64)
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
    a, b = int((end_at - 1.7) * SR), int(end_at * SR)                    # fades over the last 1.7 s, like the reference
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
    sec0 = {}
    for p in TL["pieces"]:
        sec0.setdefault(p["sid"], p["n0"] / TL["fps"])
    t_rev = TL["t_reveal"]
    sbuf = np.zeros((N, 2), np.float32)
    place(sbuf, S.make("whoosh", dur=0.45, pan=0.3), sec0["classes"] + 0.15, -22)       # name card wipes in
    place(sbuf, S.make("chime"), t_rev + 0.05, -17)                                        # logo settles
    m = music(total, t_rev - 0.05, total - 0.05)
    mbuf = np.zeros((N, 2), np.float32); mbuf[:len(m)] = m[:N]
    vm = np.abs(vbuf.mean(1)); hop = SR // 100; n = len(vm) // hop
    r = np.sqrt((vm[:n * hop].reshape(n, hop) ** 2).mean(1))
    act = (20 * np.log10(r + 1e-9) > -48).astype(float)
    sm = np.zeros_like(act)
    for i in range(1, len(act)):
        k = 0.12 if act[i] > sm[i - 1] else 0.015
        sm[i] = sm[i - 1] + k * (act[i] - sm[i - 1])
    duck = np.repeat(10 ** (-6 * sm / 20), hop)
    duck = np.pad(duck, (0, N - len(duck)), constant_values=1)[:N]
    mbuf *= (duck * 10 ** (-13.0 / 20))[:, None]
    i0 = int(t_rev * SR); lift = np.ones(N)
    lift[i0:] = 1 + 0.4 * np.minimum(1, np.arange(N - i0) / SR / 0.8)
    mbuf *= lift[:, None]
    for name, mus in (("mix_music", True), ("mix_nomusic", False)):
        mix = master(vbuf + sbuf + (mbuf if mus else 0))[:N]
        sf.write(f"{W}/{name}.wav", mix, SR)
        print("wrote", name, round(len(mix) / SR, 2))


if __name__ == "__main__":
    main()
