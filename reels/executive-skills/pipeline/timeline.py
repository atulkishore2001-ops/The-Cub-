# Maps the EDL onto the output timeline (with speed-up) and aligns display words.
import json, re, os
W = os.environ.get("WORK")
FPS = 30
SPEED = float(os.environ.get("SPEED", "1.03"))
SCENE = {1: [2.333, 9.6, 12.633, 14.033, 17.0, 24.733, 28.033, 45.167, 48.133], 2: [11.567, 18.067, 19.8, 37.0, 52.933]}
# location ids per shot time (for transitions between different backdrops)
LOC = {1: [(0, 14.033, "posters"), (14.033, 28.033, "garden"), (28.033, 45.167, "corridor"), (45.167, 99, "sofa")],
       2: [(0, 18.067, "sofa"), (18.067, 37.0, "painting"), (37.0, 99, "plant")]}
def loc_of(shot, t):
    for a, b, n in LOC[shot]:
        if a <= t < b: return n
def build():
    edl = json.load(open(f"{W}/edl.json"))
    segs = json.load(open(f"{W}/segments.json"))
    words = {i: json.load(open(f"{W}/shot{i}_words.json")) for i in (1, 2)}
    cum = 0; pieces = []
    for p in edl:
        n = p["f_out"] - p["f_in"]
        o0 = round(cum / SPEED); cum += n; o1 = round(cum / SPEED)
        p = dict(p, o_in=o0, o_out=o1, loc=loc_of(p["shot"], p["f_in"]/FPS))
        pieces.append(p)
    total_frames = pieces[-1]["o_out"]
    # words per label in order
    out_words = []
    for seg in segs:
        lab = seg["label"]; shot = seg["shot"]
        ps = [p for p in pieces if p["label"] == lab]
        ws = []
        for p in ps:
            a, b = p["f_in"]/FPS, p["f_out"]/FPS
            for w in words[shot]:
                if a - 0.12 <= w["s"] < b - 0.01:
                    ws.append(dict(src=w["w"], s=p["o_in"]/FPS + (max(w["s"], a)-a)/SPEED, e=p["o_in"]/FPS + (min(w["e"], b)-a)/SPEED))
        disp = lab.split()
        ws = ws[:len(disp)]
        if len(disp) != len(ws):
            print("WARN align", lab, len(disp), len(ws), [w["src"] for w in ws])
        for d, w in zip(disp, ws):
            w["w"] = d; w["seg"] = lab
            out_words.append(w)
    return pieces, out_words, total_frames

def scene_id(shot, f):
    t = (f + 0.5) / FPS
    return (shot, sum(1 for c in SCENE[shot] if c <= t))
def frame_map(pieces, sliver=8):
    """Per output frame: (shot, source_frame). Clamps short slivers across scene cuts (freeze instead of flash)."""
    fm = []
    for p in pieces:
        n = p["o_out"] - p["o_in"]
        src = [min(p["f_in"] + int(k * SPEED + 1e-6), p["f_out"] - 1) for k in range(n)]
        # take ids of each frame
        ids = [scene_id(p["shot"], f) for f in src]
        # end sliver: frames after last cut within final `sliver` frames -> clamp to before cut
        last = ids[-1]
        run = sum(1 for x in ids if x == last)
        if run < sliver and run < n:
            keep = src[n - run - 1]
            for k in range(n - run, n): src[k] = keep
        ids = [scene_id(p["shot"], f) for f in src]
        first = ids[0]; run = 0
        while run < n and ids[run] == first: run += 1
        if run < sliver and run < n:
            for k in range(run): src[k] = src[run]
        fm += [(p["shot"], f) for f in src]
    return fm
def blocks(pieces):
    fm = frame_map(pieces); bl = []
    for n, (shot, f) in enumerate(fm):
        new = n == 0 or shot != fm[n-1][0] or f < fm[n-1][1] or f - fm[n-1][1] > 3 or scene_id(shot, f) != scene_id(*fm[n-1])
        if new: bl.append(dict(o_in=n, o_out=n+1, shot=shot, loc=loc_of(shot, (f+0.5)/FPS)))
        else: bl[-1]["o_out"] = n + 1
    return bl
if __name__ == "__main__":
    pieces, ws, tf = build()
    print("total frames", tf, "=", tf/FPS, "s")
    for p in pieces: print(f'{p["o_in"]/FPS:6.2f}-{p["o_out"]/FPS:6.2f} {p["loc"]:9s} {p["label"][:50]}')
    for b in blocks(pieces): print("  block", f'{b["o_in"]/FPS:6.2f}-{b["o_out"]/FPS:6.2f}', b["loc"])
    line = ""
    for w in ws: line += f'{w["w"]}[{w["s"]:.2f}] '
    print(line)
