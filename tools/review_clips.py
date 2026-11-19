"""Per-clip review: specs, 4 fps contact sheet (display-rotated), per-0.25s sharpness & motion profile."""
import cv2, json, subprocess, sys, os, numpy as np
raw, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
report = {}
for fn in sorted(os.listdir(raw)):
    if not fn.lower().endswith(('.mp4', '.mov')) or fn.endswith('.part'): continue
    p = os.path.join(raw, fn)
    pr = json.loads(subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries',
        'stream=width,height,r_frame_rate,codec_name,pix_fmt:stream_side_data=rotation:format=duration',
        '-of','json',p],capture_output=True,text=True).stdout)
    s = pr['streams'][0]; dur = float(pr['format']['duration'])
    rot = next((sd.get('rotation',0) for sd in s.get('side_data_list',[])), 0)
    w,h = (s['height'],s['width']) if abs(rot)==90 else (s['width'],s['height'])
    num,den = map(int, s['r_frame_rate'].split('/'))
    base = os.path.splitext(fn)[0]
    # 4 fps sheet, tile cols depend on orientation
    cols = 8 if h > w else 5
    n = int(dur*4)+1; rows = (n+cols-1)//cols
    sc = 'scale=-2:360' if h > w else 'scale=480:-2'
    subprocess.run(['ffmpeg','-v','error','-i',p,'-vf',
        f"fps=4,{sc},drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6,tile={cols}x{rows}",
        '-frames:v','1','-y',os.path.join(out,base+'.jpg')])
    # sharpness/motion profile from low-res decode (ffmpeg applies rotation)
    proc = subprocess.run(['ffmpeg','-v','error','-i',p,'-vf','fps=8,scale=-2:540,format=gray','-f','rawvideo','-'],capture_output=True)
    fw = int(round(540*w/h/2)*2)
    frames = np.frombuffer(proc.stdout,np.uint8)
    nf = len(frames)//(fw*540); frames = frames[:nf*fw*540].reshape(nf,540,fw)
    sharp = [float(cv2.Laplacian(f,cv2.CV_64F).var()) for f in frames]
    mot = [0.0]+[float(np.abs(frames[i].astype(int)-frames[i-1]).mean()) for i in range(1,nf)]
    report[fn] = dict(w=w,h=h,fps=round(num/den,3),dur=round(dur,2),codec=s['codec_name'],pix=s['pix_fmt'],
        orient='vertical' if h>w else 'landscape',
        sharp=[round(x) for x in sharp[::2]], motion=[round(x,1) for x in mot[::2]])
    print(fn, report[fn]['orient'], report[fn]['fps'], report[fn]['dur'], flush=True)
json.dump(report, open(os.path.join(out,'report.json'),'w'), indent=1)
