# 5 Science Facts timeline: audio pieces (cuts inside a fact sit under B-roll), the picture plan (speaker shots with the
# framing alternating close / medium, full-screen B-roll for each fact), captions, and every motion graphic timed to
# the word it belongs to. Ends with a short hold and the logo reveal.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ["WORK"]
FPS = 30
EDL = json.load(open(os.path.join(HERE, "edl.json")))
SPEED = EDL["speed"]
CAP_OFF = 0.02
OUTRO = 3.70

# B-roll: source file, start time in that file, crop centre x as a fraction of its width, slow push-in amount
BROLL = {
    "honey":  dict(file="honey.mp4",    start=0.3,  cx=0.50, push=0.06),
    "octo":   dict(file="octopus.mp4",  start=2.0,  cx=0.50, push=0.05),
    "sun":    dict(file="sunlight.mp4", start=45.0, cx=0.69, push=0.05),
    "venus":  dict(file="venus.mp4",    start=8.0,  cx=0.50, push=0.07),
    "banana": dict(file="banana.mp4",   start=1.0,  cx=0.50, push=0.07),
}


import wave
import numpy as np

TARGET = EDL.get("target_total")              # revision 4: solve the speeds so the reel lands on this length
PAUSE_SPEED = EDL.get("pause_speed", 1.0)     # pauses inside a line play this much faster (short breaths)
SPEED_RANGE = EDL.get("speed_range", [SPEED, SPEED])


def _envelope():
    w = wave.open(f"{WORK}/shot1.wav"); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    hop = sr // 100
    return 20 * np.log10(np.sqrt((x[:len(x) // hop * hop].reshape(-1, hop) ** 2).mean(1)) + 1e-9)


DB = _envelope()


def _segments(a, b):
    """Split [a, b] into speech / pause runs (pauses: >= 0.15 s below -50 dB, keeping 0.06 s of air at each edge)."""
    q = DB[int(a * 100):int(b * 100)] < -50
    out, k, cur = [], 0, a
    while k < len(q):
        if q[k]:
            j = k
            while j < len(q) and q[j]:
                j += 1
            if j - k >= 15:
                pa, pb = a + k / 100 + 0.06, a + j / 100 - 0.06
                if pa > cur:
                    out.append([cur, pa, "speech"])
                out.append([pa, pb, "pause"]); cur = pb
            k = j
        else:
            k += 1
    if b > cur:
        out.append([cur, b, "speech"])
    return out


def _words_in(a, b):
    return sum(1 for w in json.load(open(f"{WORK}/shot1_words.json")) if a <= w["s"] < b)


OVERRIDES = EDL.get("speed_overrides", [])   # [[src_a, src_b, speed], ...]: lines that should play slower / faster


def _plan(R):
    """Per-section speech speed = R / that section's speaking rate, clamped to SPEED_RANGE (or fixed in section_speed)."""
    if "section_speed" in EDL:
        return dict(EDL["section_speed"])
    sp = {}
    for sec in EDL["sections"]:
        dur = sum(b - a for a, b in sec["ranges"]); n = sum(_words_in(a, b) for a, b in sec["ranges"])
        sp[sec["id"]] = min(max(R / (n / dur), SPEED_RANGE[0]), SPEED_RANGE[1]) if TARGET else SPEED
    return sp


def build(sp=None):
    if sp is None:
        sp = _solve()
    pieces, t = [], 0.0
    for si, sec in enumerate(EDL["sections"]):
        for ri, (a, b) in enumerate(sec["ranges"]):
            last = ri == len(sec["ranges"]) - 1
            b_audio = (sec["speech_end"] + 0.10) if (last and "speech_end" in sec) else b
            segs, o = [], 0.0
            for sa0, sb0, kind in _segments(a, b_audio):
                cuts = sorted({sa0, sb0} | {x for oa_, ob_, _ in OVERRIDES for x in (oa_, ob_) if sa0 < x < sb0})
                for sa, sb in zip(cuts[:-1], cuts[1:]):            # split at override edges
                    base = sp[sec["id"]]
                    for oa_, ob_, ov in OVERRIDES:
                        if oa_ <= (sa + sb) / 2 < ob_:
                            base = ov
                    v = base * (PAUSE_SPEED if kind == "pause" else 1.0)
                    segs.append([sa, sb, o, o + (sb - sa) / v, v]); o += (sb - sa) / v
            dur = o
            pieces.append(dict(sec=si, sid=sec["id"], ri=ri, a=a, b=b, b_audio=b_audio, speed=sp[sec["id"]], segs=segs,
                               n0=int(round(t * FPS)), n1=int(round((t + dur) * FPS)), t0=t, dur=dur))
            t += dur
    return pieces, t


def _solve():
    if not TARGET or "section_speed" in EDL:
        return _plan(None)
    lo, hi = 1.5, 5.0
    for _ in range(40):                                   # bisection on the target speaking rate
        R = (lo + hi) / 2
        _, t = build(_plan(R))
        if t + EDL["end_hold"] + OUTRO > TARGET:
            lo = R
        else:
            hi = R
    return _plan(hi)


def src_to_out(pieces, sid, local):
    """Section-local source time (pieces of the section laid end to end) -> output time."""
    ps = [p for p in pieces if p["sid"] == sid]
    for p in ps:
        L = p["b_audio"] - p["a"]
        if local <= L + 1e-6 or p is ps[-1]:
            s = p["a"] + min(local, L)
            for sa, sb, oa, ob, v in p["segs"]:
                if s <= sb + 1e-6:
                    return p["t0"] + oa + max(0.0, s - sa) / v
            return p["t0"] + p["dur"]
        local -= L
    return ps[-1]["t0"] + ps[-1]["dur"]


def main():
    pieces, t_end = build()
    t_reveal = t_end - 0.10 / pieces[-1]["speed"] + EDL["end_hold"]
    total = t_reveal + OUTRO
    t0 = {}
    for p in pieces:
        t0.setdefault(p["sid"], p["t0"])
    end = {p["sid"]: p["t0"] + p["dur"] for p in pieces}
    ct = json.load(open(f"{WORK}/caption_times.json"))
    caps, words = [], []
    for sid, phrases in ct.items():
        # times in caption_times are section-local and continuous across that section's pieces
        for c in phrases:
            ws = [dict(w=w["w"], s=src_to_out(pieces, sid, w["s"] + CAP_OFF), e=src_to_out(pieces, sid, w["e"] + CAP_OFF), sec=sid) for w in c["words"]]
            words += ws
            caps.append(dict(text=c["text"], sec=sid, s=max(ws[0]["s"] - 0.04, t0[sid]), e=ws[-1]["e"]))
    caps.sort(key=lambda c: c["s"]); words.sort(key=lambda w: w["s"])
    for i, c in enumerate(caps):
        nxt = caps[i + 1] if i + 1 < len(caps) else None
        c["show_until"] = (nxt["s"] if nxt and nxt["s"] - c["e"] < 0.7 else c["e"] + 0.3) if nxt else t_reveal

    def w(sec, word, nth=1, at="s"):
        hits = [x for x in words if x["sec"] == sec and x["w"].strip('",.?!:').lower() == word.lower()]
        return hits[nth - 1][at]

    # ---- picture plan: (t_start, t_end, layer)  layer = "speaker" or a B-roll key
    vis = []

    def seg(a, b, layer):
        vis.append(dict(t0=a, t1=b, layer=layer))
    seg(0.0, t0["honey"], "speaker")
    seg(t0["honey"], w("honey", "honey") - 0.05, "speaker")                      # "Number one," on camera
    seg(w("honey", "honey") - 0.05, end["honey"], "honey")
    seg(end["honey"], w("octo", "an") - 0.05, "speaker")
    seg(w("octo", "an") - 0.05, end["octo"], "octo")
    seg(end["octo"], w("sun", "sunlight") - 0.05, "speaker")
    seg(w("sun", "sunlight") - 0.05, [p for p in pieces if p["sid"] == "sun"][1]["t0"], "sun")
    seg([p for p in pieces if p["sid"] == "sun"][1]["t0"], w("venus", "on") - 0.05, "speaker")   # punchline + "Number four"
    seg(w("venus", "on") - 0.05, [p for p in pieces if p["sid"] == "venus"][2]["t0"], "venus")
    seg([p for p in pieces if p["sid"] == "venus"][2]["t0"], w("banana", "bananas") - 0.05, "speaker")
    seg(w("banana", "bananas") - 0.05, end["banana"], "banana")
    seg(end["banana"], total, "speaker")
    # speaker framing alternates at every visible change on the speaker (new speaker segment or an audio cut on camera)
    cuts = sorted(set([v["t0"] for v in vis if v["layer"] == "speaker"] + [p["t0"] for p in pieces]))
    zone, k = [], 0
    for c in cuts:
        on_speaker = any(v["t0"] <= c + 1e-6 < v["t1"] and v["layer"] == "speaker" for v in vis)
        if on_speaker:
            zone.append(dict(t=c, zoom=("close", "medium")[k % 2])); k += 1

    # ---- motion graphics, each timed to its word
    G = []
    G.append(dict(kind="title", t_in=0.0, t_out=w("hook", "true", at="e") + 0.4))
    G.append(dict(kind="stamp", text="100% TRUE", color="green", t_in=w("hook", "100%") - 0.05, t_out=end["hook"] - 0.05))
    G.append(dict(kind="namecard", t_in=t0["intro"] + 0.15, t_out=t0["intro"] + 4.0))
    G.append(dict(kind="pill_mid", text="WAIT FOR #4", t_in=w("intro", "number") - 0.05, t_out=end["intro"] - 0.05))
    facts = [("honey", 1, "HONEY NEVER SPOILS"), ("octo", 2, "OCTOPUS: 3 HEARTS"), ("sun", 3, "SUNLIGHT IS 8 MIN OLD"),
             ("venus", 4, "VENUS: DAY > YEAR"), ("banana", 5, "BANANAS ARE RADIOACTIVE")]
    for sid, num, label in facts:
        G.append(dict(kind="number", num=num, t_in=t0[sid] + 0.02, t_out=w(sid, ("one", "two", "three", "four", "five")[num - 1].strip(), at="e") + 0.02))
        G.append(dict(kind="chip", num=num, text=label, t_in=w(sid, ("one", "two", "three", "four", "five")[num - 1], at="e") + 0.1, t_out=end[sid] - 0.08))
    # honey
    G.append(dict(kind="card", icon="pyramid", text="Found in ancient\nEgyptian tombs", t_in=w("honey", "ancient") - 0.1, t_out=w("honey", "thousands") - 0.30))
    G.append(dict(kind="card", icon="hourglass", text="Thousands of\nyears old", t_in=w("honey", "thousands") - 0.05, t_out=w("honey", "still") - 0.30))
    G.append(dict(kind="card", icon="check", text="Still good\nto eat", t_in=w("honey", "still") - 0.05, t_out=end["honey"] - 0.08))
    # octopus
    G.append(dict(kind="hearts", t_in=w("octo", "three") - 0.05, t_out=end["octo"] - 0.08))
    G.append(dict(kind="blue_blood", t_in=w("octo", "blue-coloured") - 0.05, t_out=end["octo"] - 0.08))
    # sunlight: Sun -> Earth light-travel diagram with a timer
    sun2 = [p for p in pieces if p["sid"] == "sun"][1]["t0"]
    G.append(dict(kind="sun_earth", t_in=w("sun", "sunlight") + 0.1, t_out=sun2 - 0.05, t_arrive=w("sun", "minutes", at="e")))
    G.append(dict(kind="stamp", text="8 MINUTES AGO", color="orange", t_in=w("sun", "minutes", 2) - 0.1, t_out=end["sun"] - 0.05))
    # venus: day vs year bars, then the punchline stamp on camera
    v3 = [p for p in pieces if p["sid"] == "venus"][2]["t0"]
    G.append(dict(kind="bars", t_day=w("venus", "243") - 0.15, t_year=w("venus", "225") - 0.15, t_out=v3 - 0.05))
    G.append(dict(kind="stamp", text="DAY > YEAR", color="orange", t_in=w("venus", "longer") - 0.1, t_out=end["venus"] - 0.05))
    # bananas
    G.append(dict(kind="radiation", t_in=w("banana", "radioactive") - 0.15, t_out=w("banana", "natural") - 0.40))
    G.append(dict(kind="element", t_in=w("banana", "natural") - 0.1, t_out=w("banana", "completely") - 0.30))
    G.append(dict(kind="card", icon="check", text="Completely\nharmless", t_in=w("banana", "completely") - 0.1, t_out=end["banana"] - 0.08))
    # call to action
    G.append(dict(kind="numbers", t_in=w("cta", "comment") - 0.1, t_out=w("cta", "follow") - 0.15))
    G.append(dict(kind="follow", t_in=w("cta", "follow") - 0.1, t_out=t_reveal + 0.3))

    tl = dict(fps=FPS, speed=SPEED, total=total, total_frames=int(round(total * FPS)), t_speech_end=t_end, t_reveal=t_reveal,
              pieces=pieces, vis=vis, zones=zone, broll=BROLL, captions=caps, words=words, graphics=G)
    json.dump(tl, open(f"{WORK}/timeline.json", "w"), indent=1)
    print(f"speech {t_end:.2f}s, reveal at {t_reveal:.2f}s, total {total:.2f}s")
    print("  speech speed per section:", {p['sid']: round(p['speed'], 3) for p in pieces})
    for v in vis:
        print(f"  {v['t0']:6.2f}-{v['t1']:6.2f} {v['layer']}")
    print("  speaker zooms:", [(round(z['t'], 2), z['zoom']) for z in zone])
    for g in G:
        print(f"  {g['kind']:10s} {g.get('t_in', g.get('t_day', 0)):6.2f}-{g['t_out']:6.2f} {g.get('text', g.get('num', ''))}")


if __name__ == "__main__":
    main()
