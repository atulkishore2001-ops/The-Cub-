# Audio of the re-cut, rebuilt from the uncompressed master mix: 5 pieces at the measured offsets, 0.1 s linear
# cross-fades at the measured join centres, 0.5 s fade-out at the end (all as in the user's export).
import sys, subprocess
import numpy as np

SR = 48000
OFF = [66.8657, -2.9010, 6.7323, 12.4323, 18.9323]      # master time = output time + OFF[piece]
JOIN = [2.94, 10.72, 42.79, 51.48]                      # cross-fade centres (s)
XF = 0.10
DUR = 1784 / 30


def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def main(src, out):
    m = load(src)
    N = int(round(DUR * SR))
    t = np.arange(N) / SR
    y = np.zeros((N, 2), np.float32)
    edges = [-1e9] + JOIN + [1e9]
    for k, o in enumerate(OFF):
        a, b = edges[k], edges[k + 1]
        g = np.clip((t - (a - XF / 2)) / XF, 0, 1) * np.clip(((b + XF / 2) - t) / XF, 0, 1)   # linear in/out ramps
        idx = np.round((t + o) * SR).astype(int)
        ok = (g > 0) & (idx >= 0) & (idx < len(m))
        y[ok] += m[idx[ok]] * g[ok, None]
    f = int(0.5 * SR)
    y[-f:] *= np.linspace(1, 0, f)[:, None]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", out],
                   input=y.astype(np.float32).tobytes(), check=True)
    print("wrote", out, N / SR)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
