# Builds the soundtrack: cut + levelled + cleaned voice, timed SFX, ducked music bed, loudness-normalised.
import os, subprocess, json
import numpy as np
import soundfile_shim as sf
import design as D
import sounds as S
from timeline import SPEED, FPS

W = os.environ["WORK"]
SR = S.SR


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def ffilter(x, af):
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af", af,
                        "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], input=x.astype(np.float32).tobytes(),
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()


def active_rms(x):
    m = x.mean(1)
    hop = SR // 100
    n = len(m) // hop
    r = np.sqrt((m[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(r)
    act = db > (db.max() - 30)
    return 20 * np.log10(np.sqrt((r[act] ** 2).mean()) + 1e-12)


def build_voice():
    src = {1: decode(f"{W}/shot1.mp4"), 2: decode(f"{W}/shot2.mp4")}
    labels = []
    for p in D.PIECES:
        if p["label"] not in labels:
            labels.append(p["label"])
    parts = {}
    for p in D.PIECES:
        a, b = int(p["f_in"] / FPS * SR), int(p["f_out"] / FPS * SR)
        x = src[p["shot"]][a:b].copy()
        f = int(0.006 * SR)
        x[:f] *= np.linspace(0, 1, f)[:, None]
        x[-f:] *= np.linspace(1, 0, f)[:, None]
        parts.setdefault(p["label"], []).append(x)
    lev = {l: active_rms(np.concatenate(parts[l])) for l in labels}
    target = np.median(list(lev.values()))
    out = []
    seen = {l: 0 for l in labels}
    for p in D.PIECES:
        g = 10 ** (np.clip(target - lev[p["label"]], -4, 4) / 20)
        out.append(parts[p["label"]][seen[p["label"]]] * g)
        seen[p["label"]] += 1
    v = np.concatenate(out)
    v = ffilter(v, f"atempo={SPEED},highpass=f=80,equalizer=f=220:t=q:w=1.0:g=-2,equalizer=f=3800:t=q:w=1.2:g=2.5,"
                   "equalizer=f=9000:t=q:w=1.0:g=1.5,acompressor=threshold=-24dB:ratio=2.8:attack=6:release=120:makeup=3")
    return v


def place(buf, x, t, gain_db):
    i = int(round(t * SR))
    if i < 0:
        x, i = x[-i:], 0
    x = x[:len(buf) - i]
    buf[i:i + len(x)] += x * 10 ** (gain_db / 20)


def main():
    N = int(round(D.TOTAL * SR))
    voice = build_voice()
    print("voice length", len(voice) / SR, "expected", D.SPEECH_END)
    vbuf = np.zeros((N, 2), np.float32)
    vbuf[:min(N, len(voice))] = voice[:N]
    # --- sfx
    sbuf = np.zeros((N, 2), np.float32)
    for e in D.SFX:
        kw = {k: v for k, v in e.items() if k not in ("t", "name", "gain")}
        x = S.make(e["name"], **kw)
        place(sbuf, x, e["t"], e["gain"] - 8)
    # --- music with ducking
    m = S.music(D.TOTAL, dict(groove_on=D.TRANSITIONS[0] - 0.05, lift_on=D.TRANSITIONS[3] - 0.05, outro_at=D.END_CARD))
    mbuf = np.zeros((N, 2), np.float32)
    mbuf[:len(m)] = m[:N]
    vm = np.abs(vbuf.mean(1))
    hop = SR // 100
    n = len(vm) // hop
    r = np.sqrt((vm[:n * hop].reshape(n, hop) ** 2).mean(1))
    act = (20 * np.log10(r + 1e-9) > -40).astype(float)
    sm = np.zeros_like(act)
    for i in range(1, len(act)):  # attack fast, release slow
        k = 0.35 if act[i] > sm[i - 1] else 0.03
        sm[i] = sm[i - 1] + k * (act[i] - sm[i - 1])
    duck = 10 ** (-7 * sm / 20)
    duck = np.repeat(duck, hop)
    duck = np.pad(duck, (0, N - len(duck)), constant_values=1)
    music_gain = 10 ** (-10 / 20)
    mbuf *= (duck * music_gain)[:, None]
    # fade the music tail out at the very end
    ft = int(0.6 * SR)
    mbuf[-ft:] *= np.linspace(1, 0, ft)[:, None]
    for name, mus in (("mix_music", True), ("mix_nomusic", False)):
        mix = vbuf + sbuf + (mbuf if mus else 0)
        mix = ffilter(mix, "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=none,alimiter=limit=0.84:level=false")
        mix = mix[:N]
        sf.write(f"{W}/{name}.wav", mix, SR)
        print("wrote", name, len(mix) / SR)
    sf.write(f"{W}/voice_only.wav", vbuf, SR)
    sf.write(f"{W}/sfx_only.wav", sbuf, SR)
    sf.write(f"{W}/music_only.wav", mbuf, SR)


if __name__ == "__main__":
    main()
