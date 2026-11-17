# Break The Silence timeline: output frame map (one 4K take, straight cuts, framing alternating close / medium per
# shot), captions with word times, the taunt highlights, title, name card, and the closing logo reveal.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ["WORK"]
FPS = 30
EDL = json.load(open(os.path.join(HERE, os.environ.get("EDL", "edl.json"))))
SPEED = EDL["speed"]
CAP_OFF = 0.02
OUTRO = 3.70                       # logo reveal after the end hold (as in the Saisha reel, revision 2)
ZOOMS = ("close", "medium")


def build():
    pieces, t, k = [], 0.0, 0
    for si, sec in enumerate(EDL["sections"]):
        for ri, (a, b) in enumerate(sec["ranges"]):
            last = ri == len(sec["ranges"]) - 1
            b_audio = (sec["speech_end"] + 0.10) if (last and "speech_end" in sec) else b
            dur = (b_audio - a) / SPEED
            pieces.append(dict(k=k, sec=si, sid=sec["id"], ri=ri, a=a, b=b, b_audio=b_audio, zoom=ZOOMS[k % 2],
                               n0=int(round(t * FPS)), n1=int(round((t + dur) * FPS)), t0=t, dur=dur))
            t += dur; k += 1
    return pieces, t


def main():
    pieces, t_end = build()
    t_reveal = t_end - 0.10 / SPEED + EDL["end_hold"]
    total = t_reveal + OUTRO
    t0 = {}
    for p in pieces:
        t0.setdefault(p["sid"], p["t0"])
    ct = json.load(open(f"{WORK}/caption_times.json"))
    caps = []
    for sid, phrases in ct.items():
        for c in phrases:
            ws = [dict(w=w["w"], s=t0[sid] + (w["s"] + CAP_OFF) / SPEED, e=t0[sid] + (w["e"] + CAP_OFF) / SPEED) for w in c["words"]]
            caps.append(dict(text=c["text"], sec=sid, s=max(ws[0]["s"] - 0.04, t0[sid]), e=ws[-1]["e"], words=ws))
    caps.sort(key=lambda c: c["s"])
    # the taunts are shown as big highlight words, not captions
    taunts = [c for c in caps if c["sec"] == "taunts"]
    caps = [c for c in caps if c["sec"] != "taunts"]
    for i, c in enumerate(caps):
        nxt = caps[i + 1] if i + 1 < len(caps) else None
        c["show_until"] = (nxt["s"] if nxt and nxt["s"] - c["e"] < 0.7 else c["e"] + 0.3) if nxt else t_reveal
    hl = []
    for i, c in enumerate(taunts):
        nxt_s = taunts[i + 1]["s"] if i + 1 < len(taunts) else t0["familiar"]
        hl.append(dict(text=c["text"], t_in=c["s"] - 0.04, t_out=min(c["e"] + 0.45, nxt_s - 0.05)))
    fam = [p for p in pieces if p["sid"] == "familiar"]
    g = dict(highlights=hl,
             title=dict(t_in=fam[0]["t0"], t_out=fam[0]["t0"] + 2.9),
             namecard=dict(t_in=fam[1]["t0"] + 0.15, t_out=fam[1]["t0"] + 4.75))
    tl = dict(fps=FPS, speed=SPEED, total=total, total_frames=int(round(total * FPS)), t_speech_end=t_end, t_reveal=t_reveal,
              pieces=pieces, captions=caps, graphics=g)
    json.dump(tl, open(f"{WORK}/timeline.json", "w"), indent=1)
    print(f"speech {t_end:.2f}s, reveal at {t_reveal:.2f}s, total {total:.2f}s")
    for p in pieces:
        print(f"  {p['sid']:9s} {p['t0']:6.2f}-{p['t0'] + p['dur']:6.2f} ({p['dur']:.2f}s) {p['zoom']}")
    for h in hl:
        print(f"  highlight {h['t_in']:5.2f}-{h['t_out']:5.2f} {h['text']}")
    print("  title", round(g["title"]["t_in"], 2), round(g["title"]["t_out"], 2), " namecard", round(g["namecard"]["t_in"], 2), round(g["namecard"]["t_out"], 2))


if __name__ == "__main__":
    main()
