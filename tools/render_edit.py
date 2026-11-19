"""Render the engagement reel from an EDL.

usage: python render_edit.py EDL.json RAW_DIR WORK_DIR OUT.mp4 --res draft|4k
Pipeline: per-shot render (speed, 9:16 reframe, grade) -> photo-burst -> xfade assembly
          -> light-leak / bokeh overlays -> finish (bloom, vignette, grain) -> titles -> music.
"""
import argparse, json, os, subprocess, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FPS = 25

def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(' '.join(cmd) + '\n' + r.stderr[-3000:]); sys.exit(1)
    return r.stdout

def grade_chain():
    env = subprocess.run(['bash', '-c', f'source {HERE}/grade.sh; echo "$GRADE"'], capture_output=True, text=True).stdout
    return env.strip().replace('\n', '')

def probe(path):
    j = json.loads(sh(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=width,height:stream_side_data=rotation:format=duration', '-of', 'json', path]))
    s = j['streams'][0]; rot = next((d.get('rotation', 0) for d in s.get('side_data_list', [])), 0)
    w, h = (s['height'], s['width']) if abs(rot) == 90 else (s['width'], s['height'])
    return w, h, float(j['format']['duration'])

_pose = None
def auto_cx(path, t, w, h):
    """Horizontal centre (0..1) that keeps faces + hands of the main people in a 9:16 crop."""
    global _pose
    from ultralytics import YOLO
    if _pose is None: _pose = YOLO('yolov8s-pose.pt')
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', path, '-frames:v', '1',
        '-vf', 'scale=1280:-2', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
    fh = int(round(1280 * h / w / 2) * 2); f = np.frombuffer(raw, np.uint8).reshape(fh, 1280, 3)
    r = _pose(f, verbose=False)[0]; W = 1280; cw = fh * 9 / 16
    people = []
    for i, b in enumerate(r.boxes):
        if b.conf < 0.35: continue
        kp = r.keypoints.data[i].cpu().numpy(); bx = b.xyxy[0].cpu().numpy()
        xs = [k[0] for k in list(kp[0:5]) + list(kp[9:11]) if k[2] > 0.4]
        people.append(((bx[2] - bx[0]) * (bx[3] - bx[1]), xs or [(bx[0] + bx[2]) / 2]))
    if not people: return 0.5
    mx = max(a for a, _ in people)
    main = [xs for a, xs in people if a >= 0.3 * mx]
    pts = [x for xs in main for x in xs]; lo, hi = min(pts), max(pts)
    if hi - lo > cw:   # cannot fit all: centre on the biggest person
        pts = max(people, key=lambda p: p[0])[1]; lo, hi = min(pts), max(pts)
    return float(np.clip((lo + hi) / 2 / W, 0, 1))

def render_shot(i, shot, nxt_at, nxt_d, raw, work, W, H, grade, enc):
    out = os.path.join(work, f'shot_{i:02d}.mp4')
    d_in = shot.get('d', 0.04) if shot.get('tr', 'cut') != 'cut' else 0.04
    L = (nxt_at - shot['at']) + d_in / 2 + nxt_d / 2
    shot['_L'] = L
    if os.path.exists(out): return out
    if shot.get('black'):
        sh(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}:d={L:.3f}',
            *enc, '-y', out]); return out
    path = os.path.join(raw, shot['src']); w, h, dur = probe(path)
    sp = shot['speed']; start = max(0.0, shot['in'] - d_in / 2 * sp); span = L * sp
    start = min(start, max(0.0, dur - span - 0.05))
    if w > h and shot.get('track'):   # moving camera: crop follows the couple through the shot
        n = max(3, int(span / 0.35) + 1)
        ts = [start + span * k / (n - 1) for k in range(n)]
        cs = [auto_cx(path, t, w, h) for t in ts]
        cs = [float(np.mean(cs[max(0, k - 1):k + 2])) for k in range(n)]   # smooth
        shot['_cx'] = [round(c, 3) for c in cs]
        to = [(t - start) / sp for t in ts]
        expr = f'{cs[-1]}'
        for k in range(n - 2, -1, -1):
            expr = f'if(lt(t,{to[k+1]:.3f}),{cs[k]}+({cs[k+1]}-{cs[k]})*(t-{to[k]:.3f})/{to[k+1]-to[k]:.3f},{expr})'
        crop = f"crop=ih*9/16:ih:x='clip(({expr})*iw-ih*9/32,0,iw-ih*9/16)':y=0"
    elif w > h:   # landscape -> 9:16 crop on the people
        cx = shot.get('cx') or auto_cx(path, start + span / 2, w, h); shot['_cx'] = round(cx, 3)
        crop = f"crop=ih*9/16:ih:x='clip({cx}*iw-ih*9/32,0,iw-ih*9/16)':y=0"
    else:
        z = shot.get('zoom', 1.0); cx = shot.get('cx', 0.5); cy = shot.get('cy', 0.5)
        crop = (f"crop=iw/{z}:ih/{z}:x='clip({cx}*iw-iw/{z}/2,0,iw-iw/{z})':y='clip({cy}*ih-ih/{z}/2,0,ih-ih/{z})'"
                if z > 1.0 else 'null')
    pre = 'framerate=fps=75,' if shot.get('interp') else ''   # 25p source slowed down: blend in-between frames
    vf = (f"{pre}setpts=(PTS-STARTPTS)/{sp},fps={FPS},{crop},scale={W}:{H}:flags=lanczos,setsar=1,"
          f"{grade},format=yuv420p10le,trim=duration={L:.3f}")
    sh(['ffmpeg', '-v', 'error', '-ss', f'{start:.3f}', '-t', f'{span + 0.3:.3f}', '-i', path,
        '-vf', vf, '-an', *enc, '-y', out])
    return out

def render_burst(shot, nxt_at, edl, raw, work, W, H, grade, enc):
    out = os.path.join(work, 'burst.mp4'); L = nxt_at - shot['at'] + 0.04; shot['_L'] = L
    if os.path.exists(out): return out
    bdir = os.path.join(work, 'burst'); os.makedirs(bdir, exist_ok=True)
    rnd = random.Random(7); stills = []
    for k, (src, t) in enumerate(edl['burst']):
        p = os.path.join(bdir, f'still_{k:02d}.png')
        sh(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', os.path.join(raw, src), '-frames:v', '1',
            '-vf', f"scale='if(gt(iw,ih),{int(W*0.86)},-2)':'if(gt(iw,ih),-2,{int(H*0.8)})',{grade},format=rgb24", '-y', p])
        stills.append(Image.open(p).convert('RGB'))
    n = int(round(L * FPS)); per = max(1, n // len(stills)); prev = None
    bg = Image.new('RGB', (W, H), (238, 232, 223))
    for f in range(n):
        im = stills[min(f // per, len(stills) - 1)]
        jitter = rnd.uniform(-3.5, 3.5); dx, dy = rnd.randint(-W // 60, W // 60), rnd.randint(-H // 80, H // 80)
        card = Image.new('RGB', (im.width + W // 60, im.height + W // 60), (250, 248, 244)); card.paste(im, (W // 120, W // 120))
        card = card.rotate(jitter, expand=True, resample=Image.BICUBIC, fillcolor=(238, 232, 223))
        frame = bg.copy()
        frame.paste(card, ((W - card.width) // 2 + dx, (H - card.height) // 2 + dy))
        if prev is not None: frame = Image.blend(frame, prev, 0.28)   # ghosted edges like the reference
        prev = frame; frame.save(os.path.join(bdir, f'f_{f:04d}.png'))
    sh(['ffmpeg', '-v', 'error', '-framerate', str(FPS), '-i', os.path.join(bdir, 'f_%04d.png'),
        '-vf', f'format=yuv420p10le,trim=duration={L:.3f}', *enc, '-y', out])
    return out

def make_fx(kind, work, W, H, dur):
    """Light-leak or bokeh overlay as RGBA PNG sequence (generated at low res, upscaled)."""
    d = os.path.join(work, f'fx_{kind}'); os.makedirs(d, exist_ok=True)
    w, h = W // 4, H // 4; n = int(dur * FPS); rnd = np.random.default_rng(3 if kind == 'leak' else 5)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    if kind == 'bokeh':
        balls = [(rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(w * .06, w * .16), rnd.uniform(.5, 1)) for _ in range(14)]
    for f in range(n):
        t = f / max(1, n - 1); env = math.sin(math.pi * t) ** 1.2
        rgb = np.zeros((h, w, 3), np.float32)
        if kind == 'leak':   # warm red-orange wash sweeping left -> right
            cx = -0.3 * w + 1.6 * w * t
            for (ox, oy, r, col) in [(0, .35, .32, (1, .35, .08)), (.15, .7, .26, (1, .6, .2)), (-.1, .1, .24, (.9, .15, .05))]:
                g = np.exp(-(((xx - cx - ox * w) / (r * w)) ** 2 + ((yy - oy * h) / (r * h * 1.4)) ** 2))
                rgb += g[..., None] * np.array(col, np.float32)
        else:                # big soft white circles drifting upward
            for (bx, by, r, a) in balls:
                cyb = by - t * h * 0.25
                g = np.clip(1.2 - np.sqrt((xx - bx) ** 2 + (yy - cyb) ** 2) / r, 0, 1) ** 1.5
                rgb += g[..., None] * a * np.array((1, .95, .85), np.float32)
        rgb = np.clip(rgb * env, 0, 1); alpha = np.clip(rgb.max(axis=2) * (0.55 if kind == 'leak' else 0.8), 0, 1)
        im = Image.fromarray((np.dstack([rgb, alpha]) * 255).astype(np.uint8), 'RGBA')
        im.filter(ImageFilter.GaussianBlur(2)).resize((W, H), Image.BICUBIC).save(os.path.join(d, f'f_{f:03d}.png'))
    return os.path.join(d, 'f_%03d.png')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('edl'); ap.add_argument('raw'); ap.add_argument('work'); ap.add_argument('out')
    ap.add_argument('--res', default='draft'); a = ap.parse_args()
    W, H = (540, 960) if a.res == 'draft' else (2160, 3840)
    enc = (['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p10le', '-r', str(FPS)] if a.res == 'draft'
           else ['-c:v', 'libx264', '-preset', 'fast', '-crf', '12', '-pix_fmt', 'yuv420p10le', '-r', str(FPS)])
    edl = json.load(open(a.edl)); shots = edl['shots']; os.makedirs(a.work, exist_ok=True); grade = grade_chain()
    cuts = [s['at'] for s in shots] + [edl['end']]
    ds = [(s.get('d', 0.04) if s.get('tr', 'cut') != 'cut' else 0.04) for s in shots] + [0.0]
    files = []
    for i, s in enumerate(shots):
        nd = ds[i + 1]
        f = (render_burst(s, cuts[i + 1], edl, a.raw, a.work, W, H, grade, enc) if s.get('burst')
             else render_shot(i, s, cuts[i + 1], nd, a.raw, a.work, W, H, grade, enc))
        files.append(f); print(f'shot {i:02d} {s.get("label","")} ok', flush=True)
    json.dump(shots, open(os.path.join(a.work, 'shots_resolved.json'), 'w'), indent=1)

    # ---- assembly with transitions
    XF = {'dissolve': 'fade', 'fadein': 'fade', 'leak': 'fade', 'bokeh': 'fade', 'flash': 'fadewhite', 'dipblack': 'fadeblack', 'cut': 'fade'}
    # Stage 1: join shots in small batches (a single 41-input 4K graph runs out of memory),
    # each batch trimmed to frame-exact boundaries, then stream-copied together into base.mp4
    base = os.path.join(a.work, 'base.mp4')
    if not os.path.exists(base):
        n = len(files); fr = lambda t: round(t * FPS) / FPS
        start_abs = [0.0] + [cuts[j] - ds[j] / 2 for j in range(1, n)]
        bounds = list(range(0, n, 7)) + [n]; parts = []
        for ci in range(len(bounds) - 1):
            a0, b0 = bounds[ci], bounds[ci + 1]
            j0, j1 = max(0, a0 - 1), min(n - 1, b0)          # include neighbours for the transitions at the edges
            T0 = start_abs[j0]; idx = list(range(j0, j1 + 1))
            cin = []; [cin.extend(['-i', files[j]]) for j in idx]
            cg = [f'[{k}:v]settb=AVTB,fps={FPS},format=yuv420p10le,tpad=stop_mode=clone:stop_duration=0.5[c{k}]' for k in range(len(idx))]
            prv = 'c0'
            for k in range(1, len(idx)):
                j = idx[k]; d = ds[j]
                cg.append(f'[{prv}][c{k}]xfade=transition={XF[shots[j].get("tr","cut")]}:duration={d:.3f}:offset={cuts[j]-d/2-T0:.3f}[y{k}]'); prv = f'y{k}'
            Ba = fr(cuts[a0]) if a0 > 0 else 0.0; Bb = fr(cuts[b0]) if b0 < n else edl['end']
            cg.append(f'[{prv}]trim=start={Ba-T0:.3f}:end={Bb-T0:.3f},setpts=PTS-STARTPTS,format=yuv420p10le[cout]')
            part = os.path.join(a.work, f'part_{ci:02d}.mp4'); parts.append(part)
            sh(['ffmpeg', '-v', 'error', *cin, '-filter_complex', ';'.join(cg), '-map', '[cout]', *enc, '-y', part])
            print(f'batch {ci} ({a0}-{b0-1}) ok', flush=True)
        lst = os.path.join(a.work, 'parts.txt'); open(lst, 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in parts))
        sh(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-y', base])
    files_n = 1
    inputs = ['-i', base]
    fx = []
    for i, s in enumerate(shots):
        if s.get('tr') in ('leak', 'bokeh'):
            dur = 1.1; seq = make_fx(s['tr'], a.work, W, H, dur)
            fx.append((files_n + len(fx), s['at'] - dur / 2, seq))
    for idx, t0, seq in fx: inputs.extend(['-itsoffset', f'{t0:.3f}', '-framerate', str(FPS), '-i', seq])
    titles = os.path.join(REPO, 'assets', 'titles')
    ti = files_n + len(fx)
    inputs.extend(['-loop', '1', '-framerate', str(FPS), '-t', str(edl['end']), '-i', os.path.join(titles, 'credit.png'),
                   '-loop', '1', '-framerate', str(FPS), '-t', str(edl['end']), '-i', os.path.join(titles, 'title.png'),
                   '-ss', '0', '-t', str(edl['end']), '-i', os.path.join(REPO, 'music', 'song_full.mp3')])
    g = [f'[0:v]settb=AVTB,fps={FPS},format=yuv420p10le[s0]']; prev = 's0'
    g.append(f'[{prev}]format=yuv420p10le[base0]'); prev = 'base0'
    for k, (idx, t0, seq) in enumerate(fx):
        g.append(f'[{idx}:v]format=rgba[fx{k}];[{prev}][fx{k}]overlay=eof_action=pass:format=auto[fxo{k}]'); prev = f'fxo{k}'
    # finish: warm bloom (computed at 1/4 res), vignette, fine grain
    g.append(f'[{prev}]format=gbrp,split[fb][fh];[fh]scale={W//4}:{H//4},curves=master=\'0/0 0.70/0 1/1\',gblur=sigma={max(2,W//270)},'
             f'colorchannelmixer=rr=1:gg=0.78:bb=0.62,scale={W}:{H}[fgl];[fb][fgl]blend=all_mode=screen:all_opacity=0.35,'
             f'vignette=angle=PI/4.5:mode=forward,noise=alls=5:allf=t+u,format=yuva420p[fin]')
    # titles: credit 0.4-3.0 on black, couple title 4.0-8.3 ; fade in/out via alpha
    g.append(f'[{ti}:v]scale={W}:{H},format=rgba,fade=in:st=0.5:d=0.7:alpha=1,fade=out:st=2.4:d=0.6:alpha=1[cr];'
             f'[{ti+1}:v]scale={W}:{H},format=rgba,fade=in:st=4.1:d=0.9:alpha=1,fade=out:st=7.5:d=0.8:alpha=1[tt];'
             f'[fin][cr]overlay=enable=\'lt(t,3.2)\'[t1];[t1][tt]overlay=enable=\'between(t,4,8.4)\',fade=out:st={edl["end"]-1.3}:d=1.3,format=yuv420p[vout]')
    g.append(f'[{ti+2}:a]afade=out:st={edl["end"]-1.6}:d=1.6[aout]')
    fin_enc = (['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20'] if a.res == 'draft'
               else ['-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-profile:v', 'high', '-level', '5.2', '-threads', '4'])
    cmd = ['ffmpeg', '-v', 'error', *inputs, '-filter_complex', ';'.join(g), '-map', '[vout]', '-map', '[aout]',
           *fin_enc, '-pix_fmt', 'yuv420p', '-r', str(FPS), '-c:a', 'aac', '-b:a', '320k', '-t', str(edl['end']),
           '-movflags', '+faststart', '-y', a.out]
    open(os.path.join(a.work, 'assemble_cmd.txt'), 'w').write(' '.join(cmd))
    sh(cmd); print('DONE', a.out)

if __name__ == '__main__':
    main()
