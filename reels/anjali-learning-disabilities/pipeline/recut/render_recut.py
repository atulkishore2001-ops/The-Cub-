# Renders the user's 59.5 s re-cut at full quality: every frame is re-rendered from the original clips through the
# revision-3 pipeline (render5, uncompressed in memory), then given the re-cut's zoom / position / cross-fade exactly as
# measured from their export (plan.json), and encoded once.
import os, sys, json, subprocess
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ["PIPELINE"])
os.chdir(os.environ["PIPELINE"])
import render5 as R

W, H, FPS = 1080, 1920, 30
plan = json.load(open(f"{HERE}/plan.json"))
out = sys.argv[1]
_cache = {}


def master(m, dec):
    m = max(0, min(R.TOTAL - 1, m))
    if m not in _cache:
        if len(_cache) > 8:
            _cache.pop(next(iter(_cache)))
        _cache[m] = np.asarray(R.render_frame(m, dec)).astype(np.float32)
    return _cache[m]


def frame(n, dec):
    acc = np.zeros((H, W, 3), np.float32)
    for m, T, w in plan[n]:
        src = master(m, dec)
        T = np.array(T, np.float64)
        if np.allclose(T, [[1, 0, 0], [0, 1, 0]], atol=1e-3):
            img = src
        else:
            img = cv2.warpAffine(src, T, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
        acc += w * img
    return np.clip(acc + 0.5, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--stills":
        dec = R.Decoder()
        os.makedirs(sys.argv[3], exist_ok=True)
        for n in map(int, sys.argv[2].split(",")):
            cv2.imwrite(f"{sys.argv[3]}/r_{n:04d}.png", frame(n, dec)[:, :, ::-1])
        sys.exit()
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p",
                            "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    dec = R.Decoder()
    for n in range(len(plan)):
        enc.stdin.write(frame(n, dec).tobytes())
        if n % 150 == 0:
            print(f"frame {n}/{len(plan)}", flush=True)
    enc.stdin.close(); enc.wait()
    print("done", out)
