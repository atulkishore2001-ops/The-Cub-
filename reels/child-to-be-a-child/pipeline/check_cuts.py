# Assemble every section's audio exactly as the edit will (10 ms fades at each splice) and transcribe it with
# Whisper medium.en, so no splice clips a word. Prints duration totals too.
import os, sys, json, wave
import numpy as np, sherpa_onnx
M = os.environ.get("MODELS", "models") + "/sherpa-onnx-whisper-medium.en"
work, edl = sys.argv[1], json.load(open(sys.argv[2]))
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{M}/medium.en-encoder.int8.onnx", decoder=f"{M}/medium.en-decoder.int8.onnx",
        tokens=f"{M}/medium.en-tokens.txt", language="en", task="transcribe", num_threads=4, tail_paddings=800)
aud = {}
for i in (1, 2, 3):
    w = wave.open(f"{work}/shot{i}.wav"); sr = w.getframerate()
    aud[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
tot = 0
for s in edl["sections"]:
    parts = []
    for a, b in s["ranges"]:
        x = aud[s["shot"]][int(a * sr):int(b * sr)].copy(); f = int(0.01 * sr)
        x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f); parts.append(x)
    x = np.concatenate(parts); d = len(x) / sr; tot += d
    st = rec.create_stream(); st.accept_waveform(sr, np.concatenate([np.zeros(8000, np.float32), x, np.zeros(8000, np.float32)]))
    rec.decode_stream(st)
    print(f"[{s['id']:8s} {d:5.2f}s] {st.result.text.strip()}", flush=True)
print(f"speech total {tot:.2f}s; at {edl['speed']}x = {tot / edl['speed']:.2f}s")
