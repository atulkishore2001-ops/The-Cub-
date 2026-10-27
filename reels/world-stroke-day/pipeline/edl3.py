# Calm cut list: each clip is treated as one continuous take. Short pauses stay exactly as spoken (no cut, no jump);
# only pauses longer than `min_cut` are shortened, to a natural `keep` breath. A cut inside a pause that already
# contains a camera cut is placed exactly on that camera cut, so the edit never adds a second jump.
import numpy as np
from edl2 import load_db, snap_in, snap_out, SIL, FPS


def build(work, segs, durs, scene_cuts, min_cut=0.75, keep=0.42):
    DB = {i: load_db(f"{work}/shot{i}.wav") for i in durs}
    runs = {}
    for s in segs:
        runs.setdefault(s["shot"], []).append(s)
    out, log = [], []
    for shot, ss in runs.items():
        db = DB[shot]
        ti, _ = snap_in(db, ss[0]["in"], ss[0].get("pad_in", 0.12))
        if ss[-1].get("snap_out", True):
            to, _ = snap_out(db, ss[-1]["out"], ss[-1].get("pad_out", 0.18))
        else:
            to = ss[-1]["out"]
        to = min(to, durs[shot] - 0.02)
        pieces, cur = [], ti
        k, end = int(ti * 100) + 8, int(to * 100) - 8
        while k < end:
            if db[k] < SIL:
                j = k
                while j < end and db[j] < SIL:
                    j += 1
                a, b = k / 100, j / 100
                sc = [c for c in scene_cuts.get(shot, []) if a - 0.05 <= c <= b + 0.05]
                if sc:                                      # the camera already cuts here: cut on it, keep a breath
                    c = sc[0]
                    pieces.append([cur, max(min(c, a + keep / 2), a + 0.06)])
                    cur = min(max(c, b - keep / 2), b - 0.06)
                    log.append(f"shot{shot} scene-cut pause {a:.2f}-{b:.2f} -> cut at {c:.2f}")
                elif b - a >= min_cut:
                    pieces.append([cur, a + keep * 0.45]); cur = b - keep * 0.55
                    log.append(f"shot{shot} pause {a:.2f}-{b:.2f} ({b - a:.2f}s) -> {keep:.2f}s")
                k = j
            k += 1
        pieces.append([cur, to])
        for p in pieces:
            f0 = int(np.floor(p[0] * FPS + 1e-6)); f1 = int(np.ceil(p[1] * FPS - 1e-6))
            mid = (p[0] + p[1]) / 2
            lab = next((s["label"] for s in ss if s["in"] - 0.6 <= mid <= s["out"] + 0.6), ss[0]["label"])
            out.append({"label": lab, "shot": shot, "f_in": f0, "f_out": f1, "t_in": p[0], "t_out": p[1]})
    return out, sum((e["f_out"] - e["f_in"]) / FPS for e in out), log
