import sys, json, wave
import numpy as np, sherpa_onnx
M="/tmp/claude-0/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
wav, out = sys.argv[1], sys.argv[2]
w = wave.open(wav); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{M}/encoder.int8.onnx", decoder=f"{M}/decoder.int8.onnx", joiner=f"{M}/joiner.int8.onnx", tokens=f"{M}/tokens.txt", model_type="nemo_transducer", num_threads=4)
s = rec.create_stream(); s.accept_waveform(sr, x); rec.decode_stream(s); r = s.result
toks, ts = list(r.tokens), list(r.timestamps)
durs = list(getattr(r, "durations", []) or [])
print(r.text)
words=[]
for i,(t,st) in enumerate(zip(toks,ts)):
    d = durs[i] if i < len(durs) else 0.08
    if t.startswith(" ") or t.startswith("▁") or not words:
        words.append({"w": t.strip().replace("▁",""), "s": st, "e": st+d})
    else:
        words[-1]["w"] += t; words[-1]["e"] = st+d
json.dump(words, open(out,"w"), indent=0)
print(len(words), "words; durations available:", bool(durs))
