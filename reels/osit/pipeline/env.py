# Print the 10 ms RMS envelope (dB) of a shot between two times, to place cuts in true silence.
# Usage: env.py shotN.wav t0 t1 [t0 t1 ...]
import sys, wave, numpy as np
w = wave.open(sys.argv[1]); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
hop = sr // 100; n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
a = list(map(float, sys.argv[2:]))
for t0, t1 in zip(a[::2], a[1::2]):
    i0, i1 = int(t0 * 100), int(t1 * 100)
    seg = db[i0:i1]
    print(f"{t0:6.2f}-{t1:6.2f} min {seg.min():.0f} @ {(i0 + seg.argmin()) / 100:.2f}")
    print("   " + " ".join(f"{v:3.0f}" for v in seg[::2]))
