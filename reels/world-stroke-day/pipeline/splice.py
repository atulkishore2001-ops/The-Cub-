# Re-render only the opening (where "the" was removed and its caption shown) and reuse the rest of the existing
# render, shifted by the removed frames. Usage: WORK=... python3 splice.py old_video.mp4 out.mp4 N0 SHIFT
import sys, subprocess, numpy as np
import render7 as R
old, out, N0, K = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
W, H = 1080, 1920
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
dec = R.Decoder()
for n in range(N0):
    enc.stdin.write(R.render_frame(n, dec).tobytes())
import json
old_fm = json.load(open(sys.argv[5]))                    # frame map of the old render
new_fm = R.FM
src = subprocess.Popen(["ffmpeg", "-v", "error", "-i", old, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
buf, pos = {}, -1


def old_frame(m):
    global pos
    while pos < m:
        b = src.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            return buf[pos]
        pos += 1
        buf[pos] = b
        buf.pop(pos - 12, None)
    return buf[m]


prev = N0 + K - 1
for n in range(N0, R.TOTAL):
    cands = [n + k for k in range(K - 2, K + 3) if 0 <= n + k < len(old_fm) and n < len(new_fm) and tuple(old_fm[n + k]) == tuple(new_fm[n])]
    m = min(cands, key=lambda c: abs(c - (prev + 1))) if cands else prev + 1     # the same source frame, else keep pace
    m = max(m, prev)                                                             # never step backwards in the old file
    enc.stdin.write(old_frame(m)); prev = m
n = R.TOTAL
enc.stdin.close(); enc.wait()
print("frames", n, "of", R.TOTAL)
