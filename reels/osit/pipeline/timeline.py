# OSIT ad timeline: output frame map for the one continuous take (straight cuts, framing alternating close / medium
# per section), captions with word times, the graphics schedule (each graphic timed to the word it belongs to), and
# the closing frame (title, logos, registration QR).
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ["WORK"]
FPS = 30
EDL = json.load(open(os.path.join(HERE, os.environ.get("EDL", "edl.json"))))
SPEED = EDL["speed"]
CAP_OFF = 0.02
ZOOMS = ("close", "medium")


def build():
    pieces, t, k = [], 0.0, 0
    for si, sec in enumerate(EDL["sections"]):
        for ri, (a, b) in enumerate(sec["ranges"]):
            last = ri == len(sec["ranges"]) - 1
            b_audio = (sec["speech_end"] + 0.10) if (last and "speech_end" in sec) else b
            dur = (b_audio - a) / SPEED
            pieces.append(dict(k=k, sec=si, sid=sec["id"], shot=1, a=a, b=b, b_audio=b_audio, hold=0.0, zoom=ZOOMS[k % 2],
                               n0=int(round(t * FPS)), n1=int(round((t + dur) * FPS)), t0=t, dur=dur))
            t += dur; k += 1
    return pieces, t


def main():
    pieces, t_end = build()
    t_close = t_end + EDL["end_hold"]
    total = t_close + EDL["closing"]
    t0 = {}
    for p in pieces:
        t0.setdefault(p["sid"], p["t0"])
    ct = json.load(open(f"{WORK}/caption_times.json"))
    caps, words = [], []
    for sid, phrases in ct.items():
        for c in phrases:
            ws = [dict(w=w["w"], s=t0[sid] + (w["s"] + CAP_OFF) / SPEED, e=t0[sid] + (w["e"] + CAP_OFF) / SPEED, sec=sid) for w in c["words"]]
            words += ws
            caps.append(dict(text=c["text"], sec=sid, s=max(ws[0]["s"] - 0.04, t0[sid]), e=ws[-1]["e"]))
    caps.sort(key=lambda c: c["s"]); words.sort(key=lambda w: w["s"])
    for i, c in enumerate(caps):
        nxt = caps[i + 1] if i + 1 < len(caps) else None
        c["show_until"] = (nxt["s"] if nxt and nxt["s"] - c["e"] < 0.7 else c["e"] + 0.3) if nxt else t_close

    def w(sec, word, nth=1):
        hits = [x for x in words if x["sec"] == sec and x["w"].strip('",.?!').lower() == word.lower()]
        return hits[nth - 1]["s"]

    def end(sec):
        p = [p for p in pieces if p["sid"] == sec][-1]
        return p["t0"] + p["dur"]

    g = []
    have = set(t0)

    def add(sec, fn):
        """Add a graphic only when its section (and the words it is timed to) are in this cut."""
        if sec in have:
            try:
                g.append(fn())
            except (IndexError, KeyError):
                pass
    for word, label in (("SLP", "SLP"), ("OT", "OT"), ("pediatrician", "Pediatrician"), ("neurologist", "Neurologist"), ("physiotherapist", "Physiotherapist")):
        add("hook", lambda word=word, label=label: dict(kind="pill", label=label, t_in=w("hook", word), t_out=end("hook") - 0.05))
    add("intro", lambda: dict(kind="namecard", t_in=t0["intro"] + 0.15, t_out=end("intro") + 0.6))
    add("value", lambda: dict(kind="photo", img="osit_photo_2_woman_cheek_tool.jpg", t_in=w("value", "practical"), t_out=end("value") - 0.02))
    add("announce", lambda: dict(kind="title", t_in=w("announce", "Oral") - 0.10, t_out=w("announce", "happening") - 0.05))
    add("announce", lambda: dict(kind="date", t_in=w("announce", "5th") - 0.10, t_out=end("announce") - 0.02))
    if len([p for p in pieces if p["sid"] == "collab"]) > 1:      # short cut: "...SpeechGears India, | with over 1,000+..."
        add("collab", lambda: dict(kind="logos", t_in=w("collab", "collaboration") - 0.15, t_out=w("collab", "with", 2) - 0.05))
    else:
        add("collab", lambda: dict(kind="logos", t_in=w("collab", "collaboration") - 0.15, t_out=w("collab", "is") - 0.05))
    add("collab", lambda: dict(kind="premier", t_in=w("collab", "premier") - 0.10, t_out=w("collab", "with", 2) - 0.10))
    add("collab", lambda: dict(kind="photo", img="osit_photo_4_therapist_cheek_massage.jpg", stat=True, t_in=w("collab", "1,000+") - 0.10, t_out=end("collab") - 0.02))
    add("opportunity", lambda: dict(kind="photo", img="osit_photo_3_therapist_lip_tool.jpg", t_in=w("opportunity", "learn") - 0.05, t_out=w("opportunity", "learn", 2) - 0.05))
    add("opportunity", lambda: dict(kind="photo", img="osit_photo_1_man_tongue_tool.jpg", t_in=w("opportunity", "learn", 2) - 0.05, t_out=end("opportunity") - 0.02))
    if "already" in [x["w"] for x in words if x["sec"] == "register"]:
        add("register", lambda: dict(kind="fast", t_in=w("register", "already") - 0.10, t_out=w("register", "So") - 0.05))
    else:                                                          # short cut opens on "So don't wait..."
        add("register", lambda: dict(kind="fast", t_in=t0["register"] + 0.10, t_out=w("register", "before") - 0.15))
    add("register", lambda: dict(kind="deadline", t_in=w("register", "before") - 0.10, t_out=end("register") - 0.02))
    tl = dict(fps=FPS, speed=SPEED, total=total, total_frames=int(round(total * FPS)), t_speech_end=t_end, t_close=t_close,
              pieces=pieces, captions=caps, words=words, graphics=g)
    json.dump(tl, open(f"{WORK}/timeline.json", "w"), indent=1)
    print(f"speech {t_end:.2f}s, closing frame at {t_close:.2f}s, total {total:.2f}s")
    for p in pieces:
        print(f"  {p['sid']:12s} {p['t0']:6.2f}-{p['t0'] + p['dur']:6.2f} {p['zoom']}")
    for x in g:
        print(f"  {x['kind']:9s} {x['t_in']:6.2f}-{x['t_out']:6.2f} {x.get('label', x.get('img', ''))}")


if __name__ == "__main__":
    main()
