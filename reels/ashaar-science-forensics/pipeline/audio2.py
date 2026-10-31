# Soundtrack: levelled voice (3 clips + 2 promo audios), SFX, ducked music bed, loudness-normalised master.
import os, subprocess
import numpy as np
import soundfile_shim as sf
import design2 as D
import sounds2 as S
from timeline2 import SPEED, FPS

W = os.environ["WORK"]
SR = S.SR
VOICE_TARGET_DB = -23.0           # active-speech RMS every voice piece is levelled to (before the master loudnorm)


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


def fade(x, ms=6):
    f = int(ms / 1000 * SR)
    x = x.copy()
    x[:f] *= np.linspace(0, 1, f)[:, None]
    x[-f:] *= np.linspace(1, 0, f)[:, None]
    return x


VOICE_CHAIN = ("highpass=f=85,equalizer=f=250:t=q:w=1.0:g=-2,equalizer=f=3500:t=q:w=1.2:g=2.5,equalizer=f=9000:t=q:w=1.0:g=1.0,"
               "acompressor=threshold=-22dB:ratio=2.6:attack=6:release=140:makeup=2")


def explainer_voice():
    src = {i: decode(f"{W}/shot{i}.mp4") for i in (1, 2, 3)}
    labels, parts = [], {}
    for p in D.PIECES:
        if p["label"] not in labels:
            labels.append(p["label"])
        a, b = int(p["f_in"] / FPS * SR), int(p["f_out"] / FPS * SR)
        parts.setdefault(p["label"], []).append(fade(src[p["shot"]][a:b]))
    lev = {l: active_db(np.concatenate(parts[l])) for l in labels}
    print("sentence levels (dB):", {l[:14]: round(v, 1) for l, v in lev.items()})
    seen = {l: 0 for l in labels}
    out = []
    for p in D.PIECES:
        g = 10 ** (np.clip(VOICE_TARGET_DB - lev[p["label"]], -9, 20) / 20)
        out.append(parts[p["label"]][seen[p["label"]]] * g)
        seen[p["label"]] += 1
    v = np.concatenate(out)
    return ffilter(v, f"atempo={SPEED},{VOICE_CHAIN}")


def promo_voice(buf):
    src = {n: decode(f"{W}/{n}.mp4") for n in ("audio1", "audio2")}
    pcs = D.TL["promo"]
    lev = {}
    for n in src:
        sel = [p for p in pcs if p["src"] == n]
        cat = np.concatenate([src[n][int(p["s0"] * SR):int(p["s1"] * SR)] for p in sel])
        lev[n] = active_db(cat)
    print("promo levels (dB):", {k: round(v, 1) for k, v in lev.items()})
    for p in pcs:
        x = fade(src[p["src"]][int(p["s0"] * SR):int(p["s1"] * SR)], 5)
        x = x * 10 ** ((VOICE_TARGET_DB - lev[p["src"]]) / 20)
        x = ffilter(x, "highpass=f=70,acompressor=threshold=-24dB:ratio=2.0:attack=8:release=160:makeup=1")
        i = int(round(p["o0"] * SR))
        buf[i:i + len(x)] += x[:len(buf) - i]


def master(mix):
    """Two-pass loudnorm to -14 LUFS / -1.5 dBTP (Instagram-style), then a safety limiter."""
    import json, re
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], input=mix.astype(np.float32).tobytes(),
                       capture_output=True)
    j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr.decode(), re.S).group(0))
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,alimiter=limit=0.85:level=false")
    return ffilter(mix, af)


def lufs(x):
    import re
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af", "ebur128=peak=true",
                        "-f", "null", "-"], input=x.astype(np.float32).tobytes(), capture_output=True)
    return float(re.findall(r"\n\s+I:\s+(-?[\d.]+) LUFS", p.stderr.decode())[-1])


def place(buf, x, t, gain_db):
    i = int(round(t * SR))
    if i < 0:
        x, i = x[-i:], 0
    x = x[:len(buf) - i]
    buf[i:i + len(x)] += x * 10 ** (gain_db / 20)


def main():
    N = int(round(D.TOTAL * SR))
    vbuf = np.zeros((N, 2), np.float32)
    ev = explainer_voice()
    vbuf[:min(N, len(ev))] += ev[:N]
    print("explainer voice %.2fs (timeline says %.2fs)" % (len(ev) / SR, D.T_EXP_END))
    pbuf = np.zeros((N, 2), np.float32)
    promo_voice(pbuf)
    l_e, l_p = lufs(vbuf), lufs(pbuf)
    gain = l_e - l_p                                   # make the promo voice exactly as loud as the explainer voice
    print("voice loudness: explainer %.1f LUFS, promo %.1f LUFS -> promo gain %+.1f dB" % (l_e, l_p, gain))
    vbuf += pbuf * 10 ** (gain / 20)
    # --- sound effects (kept well under the voice)
    sbuf = np.zeros((N, 2), np.float32)
    for e in D.SFX:
        kw = {k: v for k, v in e.items() if k not in ("t", "name", "gain")}
        place(sbuf, S.make(e["name"], **kw), e["t"], e["gain"] - 7)
    # --- music, ducked under speech
    m = S.music(D.TOTAL, D.PROMO_T0, D.T_END - 0.55)
    mbuf = np.zeros((N, 2), np.float32)
    mbuf[:len(m)] = m[:N]
    vm = np.abs(vbuf.mean(1))
    hop = SR // 100
    n = len(vm) // hop
    r = np.sqrt((vm[:n * hop].reshape(n, hop) ** 2).mean(1))
    act = (20 * np.log10(r + 1e-9) > -48).astype(float)
    sm = np.zeros_like(act)
    for i in range(1, len(act)):
        k = 0.30 if act[i] > sm[i - 1] else 0.025
        sm[i] = sm[i - 1] + k * (act[i] - sm[i - 1])
    duck = np.repeat(10 ** (-8 * sm / 20), hop)
    duck = np.pad(duck, (0, N - len(duck)), constant_values=1)[:N]
    mbuf *= (duck * 10 ** (-10.5 / 20))[:, None]
    ft = int(0.5 * SR)
    mbuf[-ft:] *= np.linspace(1, 0, ft)[:, None]
    sf.write(f"{W}/voice_only.wav", vbuf, SR)
    sf.write(f"{W}/sfx_only.wav", sbuf, SR)
    sf.write(f"{W}/music_only.wav", mbuf, SR)
    for name, mus in (("mix_music", True), ("mix_nomusic", False)):
        mix = vbuf + sbuf + (mbuf if mus else 0)
        mix = master(mix)[:N]
        sf.write(f"{W}/{name}.wav", mix, SR)
        print("wrote", name, len(mix) / SR)


if __name__ == "__main__":
    main()
