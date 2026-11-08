# Frame-accurate EDL for N source clips: snap cuts to digital silence, tighten pauses.
import json, wave, sys, os, numpy as np
FPS = 30
SIL = -72.0
def load_db(path):
    w = wave.open(path); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    hop = sr // 100; n = len(x) // hop
    return 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-10)
def snap_in(db, t, pad=0.05):
    a, b = max(int((t - 0.30) * 100), 0), int((t + 0.12) * 100)
    k = a + int(np.argmin(db[a:b]))
    if db[k] > SIL: return t, "TIGHT-in"
    j = k
    while j < k + 150 and db[j] < SIL: j += 1
    return max(k, j - int(pad * 100)) / 100, ""
def snap_out(db, t, pad=0.07):
    a, b = int((t - 0.15) * 100), min(int((t + 0.30) * 100), len(db))
    k = a + int(np.argmin(db[a:b]))
    if db[k] > SIL: return t, "TIGHT-out"
    j = k
    while j > k - 150 and db[j] < SIL: j -= 1
    return min(k, j + int(pad * 100)) / 100, ""
def build(work, segs, durs, inner_gap=0.16, tighten=True):
    DB = {i: load_db(f"{work}/shot{i}.wav") for i in durs}
    out = []; total = 0; log = []
    for s in segs:
        shot, db = s["shot"], DB[s["shot"]]
        ti, to, fi, fo = s["in"], s["out"], "", ""
        if s.get("snap_in", True): ti, fi = snap_in(db, ti, s.get("pad_in", 0.05))
        if s.get("snap_out", True): to, fo = snap_out(db, to, s.get("pad_out", 0.07))
        to = min(to, durs[shot] - 0.02)
        pieces = []; cur = ti; k = int(ti * 100) + 8; end = int(to * 100) - 8
        half = inner_gap / 2
        while k < end:
            if db[k] < SIL:
                j = k
                while j < end and db[j] < SIL: j += 1
                if (j - k) >= int((inner_gap + 0.06) * 100) and tighten and not s.get("keep_pauses"):
                    pieces.append([cur, k / 100 + half]); cur = j / 100 - half
                k = j
            k += 1
        pieces.append([cur, to])
        for p in pieces:
            f0 = int(np.floor(p[0] * FPS + 1e-6)); f1 = int(np.ceil(p[1] * FPS - 1e-6))
            out.append({"label": s["label"], "shot": shot, "f_in": f0, "f_out": f1})
            total += (f1 - f0) / FPS
        log.append(f"{s['label'][:58]:58s} shot{shot} {ti:6.2f}-{to:6.2f} pieces={len(pieces)} {fi} {fo}")
    return out, total, log
if __name__ == "__main__":
    work = sys.argv[1]
    segs = json.load(open(f"{work}/segments.json"))
    durs = {1: 26.30, 2: 20.58, 3: 16.02}
    edl, total, log = build(work, segs, durs)
    print("\n".join(log)); print("TOTAL", round(total, 2), "s", sum(e["f_out"] - e["f_in"] for e in edl), "frames")
    json.dump(edl, open(f"{work}/edl.json", "w"), indent=1)
