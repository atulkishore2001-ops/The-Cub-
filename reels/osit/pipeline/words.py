# Word timestamps per shot with Parakeet-TDT (sherpa-onnx). Usage: words.py shotN.wav out.json
import os, sys, json, wave
import numpy as np, sherpa_onnx
M = os.environ.get("MODELS", "models") + "/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
wav, out = sys.argv[1], sys.argv[2]
w = wave.open(wav); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{M}/encoder.int8.onnx", decoder=f"{M}/decoder.int8.onnx",
        joiner=f"{M}/joiner.int8.onnx", tokens=f"{M}/tokens.txt", model_type="nemo_transducer", num_threads=4)
s = rec.create_stream(); s.accept_waveform(sr, x); rec.decode_stream(s); r = s.result
toks, ts = list(r.tokens), list(r.timestamps)
durs = list(getattr(r, "durations", []) or [])
words = []
for i, (t, st) in enumerate(zip(toks, ts)):
    d = durs[i] if i < len(durs) else 0.08
    if t.startswith(" ") or t.startswith("▁") or not words:
        words.append({"w": t.strip().replace("▁", ""), "s": round(st, 3), "e": round(st + d, 3)})
    else:
        words[-1]["w"] += t; words[-1]["e"] = round(st + d, 3)
json.dump(words, open(out, "w"), indent=0)
print(r.text)
