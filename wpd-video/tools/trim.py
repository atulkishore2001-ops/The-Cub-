import numpy as np, soundfile as sf, json
x,sr=sf.read('audio/vo_clean_full.wav')
gaps=[(7.364,8.882,0.9),(18.805,20.183,0.9),(25.074,25.971,0.8),(31.549,32.818,0.85),(44.905,47.834,1.0),(50.999,52.158,0.75)]
cuts=[(m-(b-a-t)/2, m+(b-a-t)/2) for a,b,t in gaps for m in [(a+b)/2]]
cuts.append((53.727+0.42, 57.0-0.38))   # false start "So this World Pre-... okay"
cuts.sort()
start=0.45; end=62.95
keeps=[]; cur=start
for a,b in cuts: keeps.append((cur,a)); cur=b
keeps.append((cur,end))
xf=int(0.02*sr); out=None; mp=[]
for i,(a,b) in enumerate(keeps):
    seg=x[int(a*sr):int(b*sr)].copy()
    if out is None: mp.append([a,b,0.0]); out=seg; continue
    mp.append([a,b,(len(out)-xf)/sr])
    r=np.linspace(0,1,xf); out[-xf:]=out[-xf:]*(1-r)+seg[:xf]*r; out=np.concatenate([out,seg[xf:]])
fi=int(0.08*sr); out[:fi]*=np.linspace(0,1,fi); fo=int(0.25*sr); out[-fo:]*=np.linspace(1,0,fo)
sf.write('audio/vo_trim.wav',out,sr,subtype='PCM_24')
json.dump(mp,open('audio/map.json','w'))
print('dur',len(out)/sr)
