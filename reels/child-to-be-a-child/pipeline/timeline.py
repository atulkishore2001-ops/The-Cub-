# Builds the output timeline from edl.json: frame map (output frame -> source shot/time), the cut list (every cut a
# straight cut with a framing change), caption times (from align.py), and the key times for title, name card and the
# closing logo reveal.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ["WORK"]
FPS = 30
EDL = json.load(open(f"{HERE}/edl.json"))
SPEED = EDL["speed"]
END_HOLD = EDL["end_hold"]      # stay on Saisha after the last line before the dissolve begins
OUTRO = 3.70                    # dissolve + logo reveal + hold (the reference clip's 3.4 s, given more room)
CAP_OFF = 0.02
ZOOMS = ("close", "medium")


def build():
    pieces, cuts = [], []
    t_out = 0.0
    last_sec = len(EDL["sections"]) - 1
    k = 0
    for si, sec in enumerate(EDL["sections"]):
        holds = sec.get("hold", [0.0] * len(sec["ranges"]))
        for ri, (a, b) in enumerate(sec["ranges"]):
            is_last = si == last_sec and ri == len(sec["ranges"]) - 1
            b_audio = sec["speech_end"] + 0.10 if is_last else b
            n0 = int(round(t_out * FPS))
            dur = (b_audio - a) / SPEED + holds[ri]
            n1 = int(round((t_out + dur) * FPS))
            pieces.append(dict(k=k, sec=si, sid=sec["id"], shot=sec["shot"], a=a, b=b, b_audio=b_audio, hold=holds[ri],
                               zoom=ZOOMS[k % 2], n0=n0, n1=n1, t0=t_out, dur=dur))
            if k:
                cuts.append(dict(n=n0, kind="join" if ri == 0 else "inside"))
            t_out += dur
            k += 1
    t_speech_end = t_out
    t_reveal = t_speech_end - 0.10 / SPEED + END_HOLD
    return pieces, cuts, t_speech_end, t_reveal, t_reveal + OUTRO


def main():
    pieces, cuts, t_end, t_rev, total = build()
    ct = json.load(open(f"{WORK}/caption_times.json"))
    sec_t0 = {}
    for p in pieces:
        sec_t0.setdefault(p["sid"], p["t0"])
    caps = []
    for sid, phrases in ct.items():
        for c in phrases:
            caps.append(dict(text=c["text"], sec=sid, s=sec_t0[sid] + (c["s"] + CAP_OFF) / SPEED, e=sec_t0[sid] + (c["e"] + CAP_OFF) / SPEED))
    caps.sort(key=lambda c: c["s"])
    for i, c in enumerate(caps):
        nxt = caps[i + 1] if i + 1 < len(caps) else None
        c["s"] = max(c["s"] - 0.04, sec_t0[c["sec"]])
        if nxt is None:
            c["show_until"] = t_rev                       # the last line stays up until the dissolve
        else:
            c["show_until"] = nxt["s"] - 0.04 if nxt["s"] - c["e"] < 0.7 else c["e"] + 0.25
    hook = pieces[0]
    hook_end = hook["dur"] - hook["hold"]
    tl = dict(fps=FPS, speed=SPEED, total=total, total_frames=int(round(total * FPS)), t_speech_end=t_end, t_reveal=t_rev,
              hook_end=hook_end, pieces=pieces, cuts=cuts, captions=caps)
    json.dump(tl, open(f"{WORK}/timeline.json", "w"), indent=1)
    print(f"speech {t_end:.2f}s, reveal at {t_rev:.2f}s, total {total:.2f}s ({tl['total_frames']} frames)")
    print("cuts at", [(round(c['n'] / FPS, 2), c['kind']) for c in cuts])
    for p in pieces:
        print(f"  shot {p['k']:2d} {p['sid']:8s} {p['t0']:6.2f}-{p['t0'] + p['dur']:6.2f} ({p['dur']:.2f}s) {p['zoom']}")


if __name__ == "__main__":
    main()
