# Minimal 16-bit stereo WAV writer (avoids an extra dependency).
import wave
import numpy as np


def write(path, x, sr):
    x = np.clip(np.asarray(x, np.float32), -1, 1)
    if x.ndim == 1:
        x = x[:, None]
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype("<i2").tobytes())
