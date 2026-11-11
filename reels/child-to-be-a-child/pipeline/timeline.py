# Builds the output timeline from edl.json: frame map (output frame -> source shot/time), the cut list,
# caption chunks timed to Parakeet word stamps, and the key times for title, name card and logo reveal.
import json, os, re
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ["WORK"]
FPS = 30
EDL = json.load(open(f"{HERE}/edl.json"))
SPEED = EDL["speed"]
CAP_OFF = 0.02            # caption lead vs. the re-transcribed edit
WORD_OFF = 0.08            # Parakeet stamps run ~0.08 s ahead of the actual voice onset in these clips
OUTRO = 3.40               # logo reveal length, matching the reference clip
OUTRO_LEAD = 0.12          # reveal starts this long after the last word ends

FIX = {"CUB": "Cub", "Cub.": "Cub.", "realize": "realise"}


def _words(shot):
    return json.load(open(f"{WORK}/shot{shot}_words.json"))


def build():
    pieces, cuts, words = [], [], []
    t_out = 0.0                                   # running output time (seconds) at piece start
    t_last_word = None
    for si, sec in enumerate(EDL["sections"]):
        ws = _words(sec["shot"])
        for ri, (a, b) in enumerate(sec["ranges"]):
            if si == len(EDL["sections"]) - 1 and ri == len(sec["ranges"]) - 1:
                b_audio = sec["speech_end"] + 0.10      # voice stops here; picture keeps rolling under the reveal
            else:
                b_audio = b
            n0 = int(round(t_out * FPS))
            dur = (b_audio - a) / SPEED
            n1 = int(round((t_out + dur) * FPS))
            pieces.append(dict(sec=si, sid=sec["id"], shot=sec["shot"], a=a, b=b, b_audio=b_audio, zoom=sec["zoom"],
                               n0=n0, n1=n1, t0=t_out))
            if pieces[-1] is not pieces[0]:
                cuts.append(dict(n=n0, kind="join" if ri == 0 else "morph"))
            for w in ws:
                s = w["s"] + WORD_OFF
                if a <= s < b_audio - 0.03:
                    e = min(w["e"] + WORD_OFF + 0.06, b_audio)
                    words.append(dict(w=w["w"], s=t_out + (s - a) / SPEED, e=t_out + (e - a) / SPEED, sec=sec["id"]))
            t_out += dur
    t_speech_end = t_out
    t_reveal = t_speech_end + OUTRO_LEAD - 0.10 / SPEED
    total = t_reveal + OUTRO
    return pieces, cuts, words, t_speech_end, t_reveal, total


def clean(w):
    w = FIX.get(w, w)
    return w


WEAK = {"a", "the", "to", "of", "and", "that", "at", "in", "with", "on", "be", "is", "my", "your", "their", "for", "or", "from", "just", "we", "they", "you're", "it"}


def chunks(words):
    """2-4 word caption phrases, broken at punctuation, never ending on a weak word when avoidable (Sitaara style)."""
    out, cur = [], []
    def flush():
        if cur:
            out.append(dict(text=" ".join(x["w"] for x in cur), s=cur[0]["s"], e=cur[-1]["e"], sec=cur[0]["sec"]))
            cur.clear()
    for i, w in enumerate(words):
        if cur and cur[-1]["sec"] != w["sec"]:
            flush()
        cur.append(dict(w, w=clean(w["w"])))
        txt = " ".join(x["w"] for x in cur)
        nxt = words[i + 1] if i + 1 < len(words) else None
        punct = re.search(r"[.,?!]$", cur[-1]["w"]) is not None
        long_ = len(cur) >= 4 or len(txt) >= 20
        if punct and len(cur) >= 2:
            flush(); continue
        if punct and len(cur) == 1 and nxt is not None and re.search(r"[.?!]$", cur[-1]["w"]):
            flush(); continue
        if long_ and (cur[-1]["w"].lower() not in WEAK or len(cur) >= 5 or len(txt) >= 26):
            flush()
    flush()
    # merge single dangling words into the previous chunk when it stays short
    merged = []
    for c in out:
        if merged and len(c["text"].split()) == 1 and len(merged[-1]["text"]) + len(c["text"]) <= 24 and merged[-1]["sec"] == c["sec"] \
                and not re.search(r"[.?!]$", merged[-1]["text"]):
            merged[-1]["text"] += " " + c["text"]; merged[-1]["e"] = c["e"]
        else:
            merged.append(dict(c))
    for i, c in enumerate(merged):
        nxt = merged[i + 1] if i + 1 < len(merged) else None
        c["s"] -= 0.04
        c["show_until"] = nxt["s"] - 0.04 if (nxt and nxt["s"] - c["e"] < 0.7) else c["e"] + 0.25
    return merged


def main():
    pieces, cuts, words, t_end, t_rev, total = build()
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
        c["show_until"] = nxt["s"] - 0.04 + 0.04 if (nxt and nxt["s"] - c["e"] < 0.7) else c["e"] + 0.25
    # the title carries the opening question, so captions start with the second section
    hook_end = max(w["e"] for w in words if w["sec"] == "hook")
    tl = dict(fps=FPS, speed=SPEED, total=total, total_frames=int(round(total * FPS)), t_speech_end=t_end, t_reveal=t_rev,
              hook_end=hook_end, pieces=pieces, cuts=cuts, words=words, captions=caps)
    json.dump(tl, open(f"{WORK}/timeline.json", "w"), indent=1)
    print(f"speech {t_end:.2f}s, reveal at {t_rev:.2f}s, total {total:.2f}s ({tl['total_frames']} frames); hook ends {hook_end:.2f}s")
    print("joins at", [round(c["n"] / FPS, 2) for c in cuts if c["kind"] == "join"])
    print("morphs at", [round(c["n"] / FPS, 2) for c in cuts if c["kind"] == "morph"])
    for c in caps:
        print(f"  {c['s']:6.2f}-{c['show_until']:6.2f}  {c['text']}")


if __name__ == "__main__":
    main()
