# Builds a voiceover time map (original VO time -> new reel time): pauses longer than KEEP are shortened to KEEP,
# speech plays SPEED x faster (pitch preserved). Chosen so the whole reel (with the 4.3 s closing) lasts TARGET s.
import sys, json
import numpy as np
sys.path.insert(0, "/tmp/claude-0/-home-user-The-Cub-/6a3c4bc0-104a-5ca4-adb7-aceaf8503d24/scratchpad/scripts4")
from edl2 import load_db

W = sys.argv[1]; TARGET = float(sys.argv[2])
T_LAST = 80.95
db = load_db(f"{W}/vo.wav")
q = db < -50
runs, k = [], 0
while k < len(q):
    if q[k]:
        j = k
        while j < len(q) and q[j]:
            j += 1
        if j - k >= 25:
            runs.append((k / 100, j / 100))
        k = j
    k += 1
runs = [(a, b) for a, b in runs if b < T_LAST + 0.02]
first = runs[0][1] if runs[0][0] < 0.05 else 0.0
pauses = [(a, b) for a, b in runs if a > first]


def build(speed, keep, lead=0.22):
    vo, out = [first - min(first, lead)], [0.0]
    t = first; o = min(first, lead)
    vo.append(t); out.append(o)
    for a, b in pauses:
        o += (a - t) / speed; t = a
        vo.append(t); out.append(o)
        L = b - a
        o += min(L, keep); t = b
        vo.append(t); out.append(o)
    o += (T_LAST - t) / speed; t = T_LAST
    vo.append(t); out.append(o)
    vo.append(T_LAST + 30); out.append(o + 30)                 # after the last word: real time (closing stays 4.3 s)
    return vo, out


best = None
for speed in np.arange(1.00, 1.081, 0.005):
    for keep in np.arange(0.30, 0.61, 0.02):
        vo, out = build(speed, keep)
        total = np.interp(T_LAST, vo, out) + 0.05 + 4.3
        err = abs(total - TARGET)
        score = err * 10 + (speed - 1) * 8 - keep              # hit the target, prefer gentle speed-up and fuller pauses
        if best is None or score < best[0]:
            best = (score, speed, keep, total, vo, out)
_, speed, keep, total, vo, out = best
print("speed %.3f  keep pauses at %.2fs  total %.2fs  (%d pauses)" % (speed, keep, total, len(pauses)))
json.dump(dict(speed=float(speed), keep=float(keep), vo=[float(v) for v in vo], out=[float(v) for v in out],
               pauses=pauses, first=first), open(f"{W}/retime.json", "w"))
