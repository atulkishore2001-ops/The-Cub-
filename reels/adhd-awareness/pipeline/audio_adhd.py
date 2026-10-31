# Soundtrack for the ADHD reel: the supplied voiceover cleaned up (gentle EQ, light compression, level), quiet SFX on
# the animation beats, a light music bed that ducks under the voice and resolves under the logo, -14 LUFS master.
import os, subprocess, json, re
import numpy as np
import soundfile_shim as sf
import story as S
import sounds2 as SND

W = os.environ["WORK"]
SR = SND.SR
VOICE_CHAIN = ("highpass=f=80,equalizer=f=250:t=q:w=1.0:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=2,"
               "deesser=i=0.2,acompressor=threshold=-22dB:ratio=2.2:attack=8:release=160:makeup=2")


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def ffilter(x, af):
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af", af,
                        "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], input=x.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).copy()


def master(mix):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], input=mix.astype(np.float32).tobytes(),
                       capture_output=True)
    j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr.decode(), re.S).group(0))
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,alimiter=limit=0.85:level=false")
    return ffilter(mix, af)


def place(buf, x, t, g):
    i = int(round(t * SR))
    if i < 0:
        x, i = x[-i:], 0
    x = x[:len(buf) - i]
    buf[i:i + len(x)] += x * 10 ** (g / 20)


def main():
    N = int(round(S.T_END * SR))
    v = ffilter(decode(f"{W}/vo.mp3"), VOICE_CHAIN)
    vbuf = np.zeros((N, 2), np.float32)
    vbuf[:min(N, len(v))] = v[:N]
    sbuf = np.zeros((N, 2), np.float32)
    for e in S.SFX:
        kw = {k: x for k, x in e.items() if k not in ("t", "name", "gain")}
        place(sbuf, SND.make(e["name"], **kw), e["t"], e["gain"] - 6)
    m = SND.music(S.T_END, S.T_END + 30, S.T_CREAM0 + 0.6)          # warm pad + plucks, final chord under the logo
    mbuf = np.zeros((N, 2), np.float32); mbuf[:min(N, len(m))] = m[:N]
    vm = np.abs(vbuf.mean(1)); hop = SR // 100; n = len(vm) // hop
    r = np.sqrt((vm[:n * hop].reshape(n, hop) ** 2).mean(1))
    act = (20 * np.log10(r + 1e-9) > -45).astype(float)
    sm = np.zeros_like(act)
    for i in range(1, len(act)):
        k = 0.12 if act[i] > sm[i - 1] else 0.015
        sm[i] = sm[i - 1] + k * (act[i] - sm[i - 1])
    duck = np.repeat(10 ** (-7 * sm / 20), hop); duck = np.pad(duck, (0, N - len(duck)), constant_values=1)[:N]
    mbuf *= (duck * 10 ** (-13 / 20))[:, None]
    a, b = int((S.T_END - 2.6) * SR), N
    mbuf[a:b] *= (np.cos(np.linspace(0, np.pi / 2, b - a)) ** 1.5)[:, None]
    sf.write(f"{W}/voice_only.wav", vbuf, SR)
    for name, mus in (("mix_music", True), ("mix_nomusic", False)):
        mix = master(vbuf + sbuf + (mbuf if mus else 0))[:N]
        sf.write(f"{W}/{name}.wav", mix, SR)
        print("wrote", name, len(mix) / SR)


if __name__ == "__main__":
    main()
