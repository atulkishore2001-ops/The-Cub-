# Reverse-engineer the user's re-cut (WhatsApp export) into a frame-accurate plan over our master render:
# for every output frame: one or two layers of (master frame, 2x3 affine in 1080x1920 px, weight).
import json, subprocess, numpy as np, cv2
WA, MASTER = "../wa/wa.mp4", "../anjali/video_only5.mp4"
N = 1784
OFF = [2006, -87, 201, 373, 568]                       # master frame = wa frame + OFF[seg]  (video)
A = [[1.0685, 0, -35.4], [0, 1.0698, -65.4]]           # 1080-px affines measured at 540 px (t x2)
B = [[1.0686, 0, -73.4], [0, 1.0698, -133.4]]
I = [[1, 0, 0], [0, 1, 0]]
# spans: (first, last, seg, state)
SPANS = [(0, 89, 0, A), (88, 321, 1, I), (321, 599, 2, B), (600, 1113, 2, I), (1114, 1284, 2, A),
         (1283, 1545, 3, I), (1544, 1783, 4, A)]
WINDOWS = [(86, 100, 0, 1), (319, 336, 1, 2), (1281, 1296, 2, 3), (1542, 1548, 3, 4)]   # joins: (lo, hi, seg_out, seg_in)
W5, H5 = 540, 960


def rng(p, a, b):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vf", f"trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS,"
                          f"scale={W5}:{H5},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H5, W5).astype(np.float32)


def to540(M):
    M = np.array(M, np.float32).copy(); M[:, 2] /= 2; return M


def to1080(M):
    M = np.array(M, np.float64).copy(); M[:, 2] *= 2; return M.tolist()


def ecc(ms, wa, init):
    try:
        return cv2.findTransformECC(ms, wa, init.astype(np.float32), cv2.MOTION_AFFINE, (3, 400, 1e-7), None, 5)
    except cv2.error:
        return 0.0, None


def state_of(seg, n):
    for a, b, s, st in SPANS:
        if s == seg and a <= n <= b:
            return st
    return I


plan = []
for n in range(N):
    segs = [s for a, b, s, st in SPANS if a <= n <= b]
    plan.append([[n + OFF[segs[-1]], to1080(to540(state_of(segs[-1], n))), 1.0]])

for lo, hi, so, si in WINDOWS:
    wa = rng(WA, lo, hi)
    mo = rng(MASTER, lo + OFF[so], hi + OFF[so])
    mi_lo = lo + OFF[si]
    mi = rng(MASTER, max(0, mi_lo), hi + OFF[si])
    if mi_lo < 0:
        mi = np.concatenate([np.repeat(mi[:1], -mi_lo, 0), mi])
    T_out = to540(state_of(so, lo))
    T_rest = to540(state_of(si, hi))
    tin = {}
    for k in range(hi - lo):                              # incoming zoom-settle curve, measured frame by frame
        best = max((ecc(mi[k], wa[k], init) for init in
                    (T_rest, to540([[1.06, 0, -33], [0, 1.06, -60]]), to540([[1.12, 0, -60], [0, 1.12, -110]]),
                     to540([[1.15, 0, -85], [0, 1.15, -150]]))), key=lambda r: r[0])
        tin[k] = best
    ro = {k: ecc(mo[k], wa[k], T_out) for k in range(hi - lo)}
    for k in range(hi - lo):
        n = lo + k
        r_o, r_i = ro[k][0], tin[k][0]
        Ti = tin[k][1] if tin[k][1] is not None else T_rest
        if r_i >= 0.99 and r_i >= r_o:
            plan[n] = [[n + OFF[si], to1080(Ti), 1.0]]
        elif r_o >= 0.99 and r_o > r_i:
            plan[n] = [[n + OFF[so], to1080(T_out), 1.0]]
        else:                                             # cross-fade frame: fit the two weights
            if r_i < 0.9:                                 # incoming transform contaminated: borrow the next frame's
                nxt = next(tin[j][1] for j in range(k + 1, hi - lo) if tin[j][0] > 0.95)
                Ti = nxt.copy(); Ti[0, 0] += 0.012; Ti[1, 1] += 0.012
            xo = cv2.warpAffine(mo[k], T_out, (W5, H5), borderMode=cv2.BORDER_REPLICATE).ravel()
            xi = cv2.warpAffine(mi[k], Ti, (W5, H5), borderMode=cv2.BORDER_REPLICATE).ravel()
            c, *_ = np.linalg.lstsq(np.stack([xo, xi], 1), wa[k].ravel(), rcond=None)
            c = np.clip(c, 0, 1); c = c / c.sum()
            pred = c[0] * xo + c[1] * xi
            r = np.corrcoef(pred, wa[k].ravel())[0, 1]
            plan[n] = [[n + OFF[so], to1080(T_out), float(c[0])], [n + OFF[si], to1080(Ti), float(c[1])]]
            print("  xfade", n, "w_out %.3f w_in %.3f  r=%.4f" % (c[0], c[1], r))
        print(n, "out %.4f in %.4f" % (r_o, r_i), "->", [(L[0], round(L[1][0][0], 4), round(L[1][0][2], 1), round(L[1][1][2], 1), round(L[2], 3)) for L in plan[n]])
json.dump(plan, open("plan.json", "w"))
print("frames", len(plan))
