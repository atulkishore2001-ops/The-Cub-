# Face boxes (source coordinates) per scene block, via YuNet; cached so the layout can keep Ashaar's face clear of graphics.
import json, os, subprocess
import numpy as np
import cv2

MODEL = "/tmp/claude-0/models/face/yunet.onnx"
_det = None


def detector():
    global _det
    if _det is None:
        _det = cv2.FaceDetectorYN.create(MODEL, "", (1080, 1920), 0.6, 0.3, 5000)
    return _det


def grab(path, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3).copy()


def face_in(img, prior=None, tol=280):
    """Best face box [x,y,w,h]. `prior`=(cx,cy,w,h) restricts to a plausible neighbourhood (rejects hands / posters)."""
    _, f = detector().detect(img)
    if f is None:
        return None
    f = [r for r in f if r[2] > 90 and r[-1] >= 0.8]
    if prior is not None:
        cx, cy, w, h = prior
        f = [r for r in f if abs(r[0] + r[2] / 2 - cx) < tol and abs(r[1] + r[3] / 2 - cy) < tol and 0.6 < r[2] / w < 1.5]
    else:
        f = [r for r in f if 350 < r[1] + r[3] / 2 < 1100]
    if not f:
        return None
    r = max(f, key=lambda r: r[-1] * r[2])
    return [float(r[0]), float(r[1]), float(r[2]), float(r[3])]


def block_faces(blocks, work, cache_path):
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    out = []
    for b in blocks:
        key = f"{b['shot']}:{b['f_in']}:{b['f_out']}"
        if key not in cache:
            fr = np.linspace(b["f_in"], b["f_out"], 5)[1:-1] if b["f_out"] - b["f_in"] > 6 else [b["f_in"]]
            boxes = []
            for f in fr:
                bx = face_in(grab(f"{work}/shot{b['shot']}.mp4", f / 30.0))
                if bx: boxes.append(bx)
            if not boxes:
                raise RuntimeError("no face found in block " + key)
            m = np.median(np.array(boxes), 0)
            cache[key] = dict(cx=float(m[0] + m[2] / 2), cy=float(m[1] + m[3] / 2), w=float(m[2]), h=float(m[3]))
        out.append(cache[key])
    json.dump(cache, open(cache_path, "w"), indent=0)
    return out
