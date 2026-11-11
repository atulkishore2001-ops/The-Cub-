# Transcribe short audio slices (shot:a:b[+shot:a:b...]) with Whisper medium.en to test candidate cut points.
import os, sys, wave
import numpy as np, sherpa_onnx
M = os.environ.get("MODELS", "models") + "/sherpa-onnx-whisper-medium.en"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{M}/medium.en-encoder.int8.onnx", decoder=f"{M}/medium.en-decoder.int8.onnx",
        tokens=f"{M}/medium.en-tokens.txt", language="en", task="transcribe", num_threads=4, tail_paddings=800)
work = sys.argv[1]; aud = {}
for i in (1, 2, 3):
    w = wave.open(f"{work}/shot{i}.wav"); sr = w.getframerate()
    aud[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
for spec in sys.argv[2:]:
    parts = []
    for p in spec.split("+"):
        n, a, b = p.split(":"); x = aud[int(n)][int(float(a) * sr):int(float(b) * sr)].copy(); f = int(0.01 * sr)
        x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f); parts.append(x)
    x = np.concatenate([np.zeros(8000, np.float32)] + parts + [np.zeros(8000, np.float32)])
    s = rec.create_stream(); s.accept_waveform(sr, x); rec.decode_stream(s); print(f"{spec:40s} -> {s.result.text.strip()}", flush=True)
