import numpy as np, wave, json, subprocess, re, sys
SR=48000
TEMPO=float(sys.argv[1]); PAUSE=float(sys.argv[2])
w=wave.open('vo_clean.wav'); v=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
out=subprocess.run(['ffmpeg','-hide_banner','-i','vo_clean.wav','-af','silencedetect=n=-36dB:d=0.18','-f','null','-'],capture_output=True,text=True).stderr
sil=[(float(e)-float(d),float(e)) for e,d in re.findall(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)',out)]
# merge the fumbled first attempt ("this World Prematur-") into one removable gap: 53.74 -> 57.08
sil=[s for s in sil if not (53.5<s[0]<57.2)]+[(53.76,57.07)]
sil.sort()
segs=[];pos=None
keep=[]  # (src_start, src_end) pieces to keep
cur=sil[0][1]-0.12   # lead-in
for a,b in sil[1:]:
    d=b-a
    if b>=64: # tail
        keep.append((cur,a+0.25)); break
    new = PAUSE if d>=0.5 else min(d,0.26)
    if a>53 and a<54: new=0.30
    keep.append((cur,a+new/2)); cur=b-new/2
F=int(0.012*SR)
outa=[];mp=[]  # mapping pieces (src_start, src_end, dst_start)
dst=0.0
for a,b in keep:
    x=v[int(a*SR):int(b*SR)].copy(); r=np.linspace(0,1,F); x[:F]*=r; x[-F:]*=r[::-1]
    outa.append(x); mp.append((a,b,dst)); dst+=len(x)/SR
vo=np.concatenate(outa)
ww=wave.open('vo_edit.wav','w');ww.setnchannels(1);ww.setsampwidth(2);ww.setframerate(SR);ww.writeframes((np.clip(vo,-1,1)*32767).astype(np.int16).tobytes());ww.close()
subprocess.run(['ffmpeg','-v','error','-y','-i','vo_edit.wav','-af',f'atempo={TEMPO},loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000','vo_final2.wav'],check=True)
def f(t):
    for a,b,d in mp:
        if t<a: return d/TEMPO
        if t<=b: return (d+t-a)/TEMPO
    return dst/TEMPO
W=json.load(open('words.json'))
fix={'this':57.10,'World':57.36,'Prematurity':57.64,'Day,':58.22,"let's":58.6,'celebrate':59.0}
W2=[]
for a,b,x in W:
    if 54.5<a<59.3 and x in fix: a=fix[x]; b=a+0.25
    W2.append([round(f(a),3),round(f(b),3),x,a])
W2[0][0]=round(f(1.36),3)
json.dump({'words':W2,'len':dst/TEMPO,'tempo':TEMPO},open('words3.json','w'))
print('edited',round(dst,2),'final',round(dst/TEMPO,2))
