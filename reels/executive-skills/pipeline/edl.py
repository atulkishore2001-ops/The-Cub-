# Build a frame-accurate edit decision list from rough segment times, snapping to silence and tightening pauses.
import json, wave, sys, numpy as np
W = sys.argv[1]  # work dir
FPS = 30
SIL = -50.0
def load(i):
    w = wave.open(f"{W}/shot{i}.wav"); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768
    hop = sr//100; n = len(x)//hop
    db = 20*np.log10(np.sqrt((x[:n*hop].reshape(n, hop)**2).mean(1))+1e-10)
    return db
DB = {1: load(1), 2: load(2)}
DUR = {1: 50.30, 2: 56.766}
# (label, shot, rough_in, rough_out, snap_in, snap_out)
SEGS = json.load(open(f"{W}/segments.json"))
def snap_in(db, t):
    a, b = int((t-0.25)*100), int((t+0.10)*100); a = max(a, 0)
    k = a + int(np.argmin(db[a:b])); m = db[k]
    if m > SIL: return t, f"TIGHT-in {m:.0f}dB"
    j = k
    while j < k+100 and db[j] < SIL: j += 1
    return max(k, j-4)/100, ""
def snap_out(db, t):
    a, b = int((t-0.15)*100), int((t+0.25)*100); b = min(b, len(db))
    k = a + int(np.argmin(db[a:b])); m = db[k]
    if m > SIL: return t, f"TIGHT-out {m:.0f}dB"
    j = k
    while j > k-100 and db[j] < SIL: j -= 1
    return min(k, j+7)/100, ""
out = []; total = 0
for s in SEGS:
    lab, shot, ti, to = s["label"], s["shot"], s["in"], s["out"]
    db = DB[shot]
    fi = fo = ""
    if s.get("snap_in", True): ti, fi = snap_in(db, ti)
    if s.get("snap_out", True): to, fo = snap_out(db, to)
    to = min(to, DUR[shot])
    # split on long internal pauses
    pieces = []; cur = ti; k = int(ti*100)+8
    end = int(to*100)-8
    while k < end:
        if db[k] < SIL:
            j = k
            while j < end and db[j] < SIL: j += 1
            if (j-k) >= 20 and s.get("tighten", True):
                pieces.append([cur, (k+5)/100]); cur = (j-5)/100
            k = j
        k += 1
    pieces.append([cur, to])
    for p in pieces:
        fi_ = int(np.floor(p[0]*FPS+1e-6)); fo_ = int(np.ceil(p[1]*FPS-1e-6))
        out.append({"label": lab, "shot": shot, "f_in": fi_, "f_out": fo_, "zoom": s.get("zoom")})
        total += (fo_-fi_)/FPS
    print(f"{lab[:60]:60s} shot{shot} {ti:6.2f}-{to:6.2f} pieces={len(pieces)} {fi} {fo}")
print("TOTAL", round(total, 2), "s,", sum(o['f_out']-o['f_in'] for o in out), "frames")
json.dump(out, open(f"{W}/edl.json", "w"), indent=1)
