# Output timeline: explainer cut list -> frame map, scene blocks, aligned caption words; promo voice placement.
import json, os, re, wave, difflib
import numpy as np
import edl2, edl3

W = os.environ["WORK"]
FPS = 30
SPEED = float(os.environ.get("SPEED", "1.025"))

# Hard cuts inside each source clip (seconds), from ffmpeg scene detection, and the location of each stretch.
SCENE = {1: [21.1833], 2: [20.1333], 3: []}
LOC = {1: [(0, 99, "desk")], 2: [(0, 99, "desk")], 3: [(0, 99, "desk")]}
SRC_FRAMES = {1: 977, 2: 959, 3: 745}      # 30 fps frame counts of the three clips
DURS = {1: 32.55, 2: 31.95, 3: 24.83}
OUTRO = float(os.environ.get("OUTRO", "4.3"))   # closing logo reveal after the last word

# Promo voice (Audio 1 + Audio 2): speech regions, long pauses shortened, small gaps between pieces.
PROMO_BEAT = 0.34        # breath between the last explainer word and the promo voice
PROMO_GAP = 0.20         # between Audio 1 and Audio 2
PROMO_HOLD = 0.36        # logo hold after the last word
PROMO_SRC = {"audio1": (3.30, 18.52), "audio2": (1.20, 7.90)}
PAUSE_MIN, PAUSE_KEEP = 0.42, 0.15   # promo pauses longer than this are cut to 2*PAUSE_KEEP


def loc_of(shot, t):
    for a, b, n in LOC[shot]:
        if a <= t < b:
            return n


def scene_id(shot, f):
    t = (f + 0.5) / FPS
    return (shot, sum(1 for c in SCENE[shot] if c <= t))


def norm(s):
    return re.sub(r"[^a-z0-9']", "", s.lower())


_onset_cache = {}


def onsets(name):
    """Times (s) where speech starts after >=65 ms of near-silence (the clips/voice-overs have digital silence between phrases)."""
    if name not in _onset_cache:
        w = wave.open(f"{W}/{name}.wav"); sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        hop = sr // 200; m = len(x) // hop
        db = 20 * np.log10(np.sqrt((x[:m * hop].reshape(m, hop) ** 2).mean(1)) + 1e-10)
        out, run = [], 0
        for j in range(m):
            if db[j] < -78:
                run += 1
            else:
                if run >= 14:                      # >=70 ms of near-silence, then sound begins here
                    out.append(j / 200)
                run = 0
        _onset_cache[name] = out
    return _onset_cache[name]


def snap_first(name, toks, a):
    """Move the first token of a piece to the real speech onset (recogniser start times include lead-in)."""
    if not toks:
        return
    first = min(toks, key=lambda t: t["s"])
    cand = [o for o in onsets(name) if a - 0.03 <= o <= a + 0.6]
    if cand:
        first["s"] = min(cand[0], first["e"] - 0.05)


def build_explainer():
    segs = json.load(open(f"{W}/segments.json"))
    edl, total, _ = edl3.build(W, segs, DURS, SCENE, float(os.environ.get("MIN_CUT", "0.6")), float(os.environ.get("KEEP", "0.32")))
    cum, pieces = 0, []
    for p in edl:
        n = p["f_out"] - p["f_in"]
        o0 = round(cum / SPEED); cum += n; o1 = round(cum / SPEED)
        pieces.append(dict(p, o_in=o0, o_out=o1))
    return segs, pieces


def frame_map(pieces, sliver=8):
    """Per output frame: (shot, source_frame). Short slivers across a scene cut are frozen, not flashed."""
    fm = []
    for p in pieces:
        n = p["o_out"] - p["o_in"]
        src = [min(p["f_in"] + int(k * SPEED + 1e-6), p["f_out"] - 1, SRC_FRAMES[p["shot"]] - 1) for k in range(n)]
        ids = [scene_id(p["shot"], f) for f in src]
        run = sum(1 for x in ids if x == ids[-1])
        if run < sliver and run < n:
            keep = src[n - run - 1]
            for k in range(n - run, n): src[k] = keep
        ids = [scene_id(p["shot"], f) for f in src]
        run = 0
        while run < n and ids[run] == ids[0]: run += 1
        if run < sliver and run < n:
            for k in range(run): src[k] = src[run]
        fm += [(p["shot"], f) for f in src]
    return fm


def blocks(fm):
    bl = []
    for n, (shot, f) in enumerate(fm):
        new = n == 0 or shot != fm[n - 1][0] or f < fm[n - 1][1] or f - fm[n - 1][1] > 3 or scene_id(shot, f) != scene_id(*fm[n - 1])
        if new:
            bl.append(dict(o_in=n, o_out=n + 1, shot=shot, scene=scene_id(shot, f), loc=loc_of(shot, (f + 0.5) / FPS),
                           f_in=f, f_out=f))
        else:
            bl[-1]["o_out"] = n + 1; bl[-1]["f_out"] = f
    return bl


MERGE = {("foreign", "six"): "forensics", ("finger", "printing"): "fingerprinting", ("hands", "on"): "hands-on"}


def align(label, toks):
    """Map the words of `label` onto recognised tokens (list of dict w/s/e); returns [(word, s, e)] for each label word."""
    lw = label.split()
    # merge known split tokens so counts line up
    t2, i = [], 0
    while i < len(toks):
        if i + 1 < len(toks) and (norm(toks[i]["w"]), norm(toks[i + 1]["w"])) in MERGE:
            t2.append(dict(w=MERGE[(norm(toks[i]["w"]), norm(toks[i + 1]["w"]))], s=toks[i]["s"], e=toks[i + 1]["e"])); i += 2
        else:
            t2.append(toks[i]); i += 1
    a = [norm(w) for w in lw]; b = [norm(t["w"]) for t in t2]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    res = [None] * len(lw)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1): res[i1 + k] = (t2[j1 + k]["s"], t2[j1 + k]["e"])
        elif tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1): res[i1 + k] = (t2[j1 + k]["s"], t2[j1 + k]["e"])
    # interpolate anything unmatched
    for k in range(len(res)):
        if res[k] is None:
            lo = next((j for j in range(k - 1, -1, -1) if res[j]), None); hi = next((j for j in range(k + 1, len(res)) if res[j]), None)
            if lo is None and hi is None: raise RuntimeError("cannot align " + label)
            if lo is None: res[k] = (res[hi][0] - 0.2 * (hi - k), res[hi][0] - 0.2 * (hi - k) + 0.2)
            elif hi is None: res[k] = (res[lo][1] + 0.05, res[lo][1] + 0.25)
            else:
                f = (k - lo) / (hi - lo); s = res[lo][1] + (res[hi][0] - res[lo][1]) * (f - 0.5 / (hi - lo)); res[k] = (s, s + 0.2)
    return list(zip(lw, [r[0] for r in res], [r[1] for r in res]))


def src2out(pieces, shot, t):
    """Source time in a clip -> output time (a time inside a removed pause snaps to the next kept frame)."""
    ps = [p for p in pieces if p["shot"] == shot]
    for p in ps:
        a, b = p["f_in"] / FPS, p["f_out"] / FPS
        if t < a:
            return p["o_in"] / FPS
        if t < b:
            return p["o_in"] / FPS + (t - a) / SPEED
    return ps[-1]["o_out"] / FPS


def explainer_words(segs, pieces):
    words = {i: json.load(open(f"{W}/shot{i}_words.json")) for i in (1, 2, 3)}
    out = []
    for seg in segs:
        sh = seg["shot"]
        src = [dict(t) for t in words[sh] if seg["in"] - 0.3 <= t["s"] < seg["out"] - 0.02]
        snap_first(f"shot{sh}", src, seg["in"] - 0.12)
        toks = [dict(w=t["w"], s=src2out(pieces, sh, t["s"]), e=src2out(pieces, sh, t["e"])) for t in src]
        for w, s, e in align(seg["label"], toks):
            out.append(dict(w=w, s=s, e=max(e, s + 0.08), seg=seg["label"]))
    return out


def promo_pieces():
    """Voice pieces of Audio 1 / Audio 2 on the output timeline (long pauses shortened)."""
    exp_segs, exp_pieces = build_explainer()
    t_exp_end = exp_pieces[-1]["o_out"] / FPS
    t = t_exp_end + PROMO_BEAT
    res = []; words = []
    for name in ("audio1", "audio2"):
        a, b = PROMO_SRC[name]
        w = wave.open(f"{W}/{name}.wav"); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        db = 20 * np.log10(np.sqrt((x[:len(x) // 160 * 160].reshape(-1, 160) ** 2).mean(1)) + 1e-10)  # 10 ms
        k0, k1 = int(a * 100), int(b * 100)
        pcs, cur, k = [], a, k0
        while k < k1:
            if db[k] < -75:
                j = k
                while j < k1 and db[j] < -75: j += 1
                if (j - k) / 100 > PAUSE_MIN:
                    pcs.append([cur, k / 100 + PAUSE_KEEP]); cur = j / 100 - PAUSE_KEEP
                k = j
            k += 1
        pcs.append([cur, b])
        toks = json.load(open(f"{W}/{name}_words.json"))
        o = t; kept = []
        for s0, s1 in pcs:
            snap_first(name, [v for v in toks if s0 - 0.05 <= v["s"] <= s1], s0)
        for s0, s1 in pcs:
            kept.append(dict(src=name, s0=s0, s1=s1, o0=o, o1=o + (s1 - s0)))
            o += s1 - s0
        res += kept
        # words -> output time
        def mp(ts):
            for p in kept:
                if p["s0"] - 0.02 <= ts <= p["s1"] + 0.02:
                    return p["o0"] + max(0.0, ts - p["s0"])
            near = min(kept, key=lambda p: min(abs(ts - p["s0"]), abs(ts - p["s1"])))
            return near["o0"] + (0.0 if ts < near["s0"] else near["s1"] - near["s0"])
        tw = [dict(w=v["w"], s=mp(v["s"]), e=mp(v["e"])) for v in toks if a - 0.05 <= v["s"] <= b]
        words.append((name, tw))
        t = o + PROMO_GAP
    t_end = res[-1]["o1"] + PROMO_HOLD
    return exp_pieces, res, words, t_exp_end, t_end


PROMO_LABELS = {
    "audio1": "At The Cub, our Junior Forensics Academy, starting 14 November, let the children become little detectives. "
              "Through fingerprinting, handwriting analysis and hands-on science experiments, they will work together to crack a mystery.",
    "audio2": "Hurry up as spots are limited. Comment SCIENCE below and DM us to enrol your little detective.",
}


def build():
    exp_segs, exp_pieces = build_explainer()
    ew = explainer_words(exp_segs, exp_pieces)
    t_exp_end = exp_pieces[-1]["o_out"] / FPS
    t_end = t_exp_end + OUTRO
    return dict(pieces=exp_pieces, promo=[], words=ew, t_exp_end=t_exp_end, t_end=t_end,
                total_frames=int(round(t_end * FPS)))


if __name__ == "__main__":
    tl = build()
    print("explainer ends %.2fs  reel ends %.2fs (%d frames)  speed %.2f" % (tl["t_exp_end"], tl["t_end"], tl["total_frames"], SPEED))
    for p in tl["pieces"]: print(f'{p["o_in"] / FPS:6.2f}-{p["o_out"] / FPS:6.2f} shot{p["shot"]} {p["label"][:50]}')
    for p in tl["promo"]: print(f'{p["o0"]:6.2f}-{p["o1"]:6.2f} {p["src"]} {p["s0"]:.2f}-{p["s1"]:.2f}')
    fm = frame_map(tl["pieces"])
    for b in blocks(fm): print("  block %6.2f-%6.2f shot%d %s" % (b["o_in"] / FPS, (b["o_out"]) / FPS, b["shot"], b["loc"]))
    print(" ".join("%s[%.2f]" % (w["w"], w["s"]) for w in tl["words"]))
