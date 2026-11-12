# Times the hand-written caption phrases: each section's edited audio (exactly as it plays) is re-transcribed with
# Parakeet-TDT, and the caption words are matched to the recognised words in order (difflib); unmatched words are
# interpolated between their matched neighbours. Writes WORK/caption_times.json (section-local, source seconds).
import os, sys, json, wave, re, difflib
import numpy as np, sherpa_onnx

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ["WORK"]
M = os.environ.get("MODELS", "models") + "/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
EDL = json.load(open(f"{HERE}/edl.json"))
CAPS = json.load(open(f"{HERE}/captions.json"))
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f"{M}/encoder.int8.onnx", decoder=f"{M}/decoder.int8.onnx",
        joiner=f"{M}/joiner.int8.onnx", tokens=f"{M}/tokens.txt", model_type="nemo_transducer", num_threads=4)
aud = {}
for i in [k for k in (1, 2, 3) if os.path.exists(f"{WORK}/shot{k}.wav")]:
    w = wave.open(f"{WORK}/shot{i}.wav"); SR = w.getframerate()
    aud[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower().replace("-", ""))
LEAD = 0.5
out = {}
for k, sec in enumerate(EDL["sections"]):
    if sec["id"] not in CAPS:
        continue
    parts = []
    holds = sec.get("hold", [0.0] * len(sec["ranges"]))
    for j, (a, b) in enumerate(sec["ranges"]):
        if k == len(EDL["sections"]) - 1 and j == len(sec["ranges"]) - 1:
            b = sec["speech_end"] + 0.10
        x = aud[sec.get("shot", 1)][int(a * SR):int(b * SR)].copy(); f = int(0.01 * SR)
        x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f); parts.append(x)
        parts.append(np.zeros(int(holds[j] * EDL["speed"] * SR), np.float32))   # a hold plays as silence
    x = np.concatenate([np.zeros(int(LEAD * SR), np.float32)] + parts + [np.zeros(int(LEAD * SR), np.float32)])
    s = rec.create_stream(); s.accept_waveform(SR, x); rec.decode_stream(s); r = s.result
    rw = []
    durs = list(getattr(r, "durations", []) or [])
    for i, (t, st) in enumerate(zip(r.tokens, r.timestamps)):
        d = durs[i] if i < len(durs) else 0.08
        if t.startswith(" ") or not rw:
            rw.append([t.strip(), st - LEAD, st - LEAD + d])
        else:
            rw[-1][0] += t; rw[-1][2] = st - LEAD + d
    phrases = [p.strip() for p in CAPS[sec["id"]].split("|")]
    cw = [(pi, w) for pi, p in enumerate(phrases) for w in p.split()]
    sm = difflib.SequenceMatcher(a=[norm(w) for _, w in cw], b=[norm(w[0]) for w in rw], autojunk=False)
    t = [None] * len(cw)
    for blk in sm.get_matching_blocks():
        for q in range(blk.size):
            t[blk.a + q] = (rw[blk.b + q][1], rw[blk.b + q][2])
    known = [q for q in range(len(t)) if t[q]]
    miss = [cw[q][1] for q in range(len(t)) if not t[q]]
    for q in range(len(t)):
        if t[q] is None:
            lo = max([p for p in known if p < q], default=None); hi = min([p for p in known if p > q], default=None)
            ts = t[lo][1] if lo is not None else 0.0
            te = t[hi][0] if hi is not None else ts + 0.3
            n_gap = (hi if hi is not None else len(t)) - (lo if lo is not None else -1) - 1
            pos = q - (lo if lo is not None else -1)
            step = (te - ts) / (n_gap + 1)
            t[q] = (ts + step * (pos - 0.5), ts + step * (pos + 0.5))
    res = []
    for pi, p in enumerate(phrases):
        idx = [q for q in range(len(cw)) if cw[q][0] == pi]
        res.append(dict(text=p, s=t[idx[0]][0], e=t[idx[-1]][1], words=[dict(w=cw[q][1], s=t[q][0], e=t[q][1]) for q in idx]))
    out[sec["id"]] = res
    print(f"[{sec['id']}] recognised: {r.text.strip()}")
    print(f"   unmatched caption words: {miss}")
json.dump(out, open(f"{WORK}/caption_times.json", "w"), indent=1)
