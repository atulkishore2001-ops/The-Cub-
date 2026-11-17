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


def build():
    pieces, t = [], 0.0
    for si, sec in enumerate(EDL["sections"]):
        for ri, (a, b) in enumerate(sec["ranges"]):
            last = ri == len(sec["ranges"]) - 1
            b_audio = (sec["speech_end"] + 0.10) if (last and "speech_end" in sec) else b
            dur = (b_audio - a) / SPEED
            pieces.append(dict(sec=si, sid=sec["id"], ri=ri, a=a, b=b, b_audio=b_audio,
                               n0=int(round(t * FPS)), n1=int(round((t + dur) * FPS)), t0=t, dur=dur))
            t += dur
    return pieces, t


def main():
    pieces, t_end = build()
    t_reveal = t_end - 0.10 / SPEED + EDL["end_hold"]
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
            ws = [dict(w=w["w"], s=t0[sid] + (w["s"] + CAP_OFF) / SPEED, e=t0[sid] + (w["e"] + CAP_OFF) / SPEED, sec=sid) for w in c["words"]]
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
        G.append(dict(kind="number", num=num, t_in=t0[sid] + 0.02, t_out=w(sid, ("one", "two", "three", "four", "five")[num - 1].strip(), at="e") + 0.35))
        G.append(dict(kind="chip", num=num, text=label, t_in=w(sid, ("one", "two", "three", "four", "five")[num - 1], at="e") + 0.1, t_out=end[sid] - 0.08))
    # honey
    G.append(dict(kind="card", icon="pyramid", text="Found in ancient\nEgyptian tombs", t_in=w("honey", "ancient") - 0.1, t_out=w("honey", "was") - 0.05))
    G.append(dict(kind="card", icon="hourglass", text="Thousands of\nyears old", t_in=w("honey", "was") - 0.05, t_out=w("honey", "still") - 0.05))
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
    G.append(dict(kind="radiation", t_in=w("banana", "radioactive") - 0.15, t_out=w("banana", "natural") - 0.05))
    G.append(dict(kind="element", t_in=w("banana", "natural") - 0.1, t_out=w("banana", "completely") - 0.05))
    G.append(dict(kind="card", icon="check", text="Completely\nharmless", t_in=w("banana", "completely") - 0.1, t_out=end["banana"] - 0.08))
    # call to action
    G.append(dict(kind="numbers", t_in=w("cta", "comment") - 0.1, t_out=t_reveal + 0.3))

    tl = dict(fps=FPS, speed=SPEED, total=total, total_frames=int(round(total * FPS)), t_speech_end=t_end, t_reveal=t_reveal,
              pieces=pieces, vis=vis, zones=zone, broll=BROLL, captions=caps, words=words, graphics=G)
    json.dump(tl, open(f"{WORK}/timeline.json", "w"), indent=1)
    print(f"speech {t_end:.2f}s, reveal at {t_reveal:.2f}s, total {total:.2f}s")
    for v in vis:
        print(f"  {v['t0']:6.2f}-{v['t1']:6.2f} {v['layer']}")
    print("  speaker zooms:", [(round(z['t'], 2), z['zoom']) for z in zone])
    for g in G:
        print(f"  {g['kind']:10s} {g.get('t_in', g.get('t_day', 0)):6.2f}-{g['t_out']:6.2f} {g.get('text', g.get('num', ''))}")


if __name__ == "__main__":
    main()
