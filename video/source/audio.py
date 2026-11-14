import numpy as np, wave, json
from scipy.signal import fftconvolve, butter, lfilter
SR=48000
def rd(f):
    w=wave.open(f); a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768; return a
def wr(f,a,ch=1):
    a=np.clip(a,-1,1); w=wave.open(f,'w'); w.setnchannels(ch); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a*32767).astype(np.int16).tobytes()); w.close()
# ---- voice: trim lead-in and the long 2.9s pause
v=rd('vo_clean.wav')
CUTS=[(0.5,45.5),(47.3,63.0)]
def fade(x,n=int(0.03*SR)):
    x=x.copy(); r=np.linspace(0,1,n); x[:n]*=r; x[-n:]*=r[::-1]; return x
vo=np.concatenate([fade(v[int(a*SR):int(b*SR)]) for a,b in CUTS])
def remap(t):
    return t-0.5 if t<46.4 else t-0.5-1.8
W=json.load(open('words.json'))
W2=[[round(remap(a),2),round(remap(b),2),w] for a,b,w in W]
json.dump(W2,open('words2.json','w'))
VOLEN=len(vo)/SR
TOTAL=VOLEN-1.6+0.5+3.31+1.2   # see timeline: logo at vo_end+0.5
print('vo len',VOLEN,'last word end',W2[-1][1])
wr('vo_final.wav',vo)
# ---- soothing BGM (synthesised): warm pad + soft music-box arpeggio
DUR=70.0; n=int(DUR*SR); t=np.arange(n)/SR
def note(m): return 440*2**((m-69)/12)
bpm=66; beat=60/bpm; bar=4*beat
chords=[[48,55,60,64,67,71],[45,52,57,60,64,67],[41,48,57,60,64,69],[43,50,55,59,62,69]]  # Cmaj7 Am7 Fmaj7 G6/9
L=np.zeros(n); R=np.zeros(n)
def add(sig,start,pan=0.5):
    i=int(start*SR); j=min(n,i+len(sig)); 
    if i>=n: return
    L[i:j]+=sig[:j-i]*(1-pan); R[i:j]+=sig[:j-i]*pan
nb=int(DUR/bar)+1
for b in range(nb):
    ch=chords[b%4]; t0=b*bar
    # pad
    d=bar*1.35; tt=np.arange(int(d*SR))/SR
    env=np.minimum(tt/1.4,1)*np.minimum((d-tt)/1.6,1)
    for k,m in enumerate(ch[:5]):
        f=note(m); s=(np.sin(2*np.pi*f*tt)+0.5*np.sin(2*np.pi*f*1.003*tt+1)+0.18*np.sin(2*np.pi*2*f*tt))*env*0.05/(1+k*0.15)
        add(s,t0,0.35+0.08*k)
    # music-box arpeggio, 8th notes, gentle pattern
    pat=[2,3,4,3,5,4,3,4]
    for q,idx in enumerate(pat):
        if (b%2==1 and q in (1,5)): continue
        m=ch[idx]+12; f=note(m); d2=2.2; tt=np.arange(int(d2*SR))/SR
        s=(np.sin(2*np.pi*f*tt)+0.35*np.sin(2*np.pi*2*f*tt)*np.exp(-tt*6)+0.12*np.sin(2*np.pi*3.01*f*tt)*np.exp(-tt*9))*np.exp(-tt*2.6)*np.minimum(tt/0.006,1)
        vel=0.10*(1.0 if q%4==0 else 0.7)
        add(s*vel,t0+q*beat/2,0.3+0.4*((q*37)%10)/10)
    # soft bass
    f=note(ch[0]-12); tt=np.arange(int(bar*SR))/SR
    add(np.sin(2*np.pi*f*tt)*np.minimum(tt/0.3,1)*np.minimum((bar-tt)/0.6,1)*0.07,t0,0.5)
# reverb
rng=np.random.default_rng(3); ir_t=np.arange(int(2.2*SR))/SR
def ir(): 
    x=rng.standard_normal(len(ir_t))*np.exp(-ir_t*2.8); b,a=butter(2,3500/(SR/2)); return lfilter(b,a,x)
L2=L+0.22*fftconvolve(L,ir())[:n]/8; R2=R+0.22*fftconvolve(R,ir())[:n]/8
b,a=butter(2,5500/(SR/2)); L2=lfilter(b,a,L2); R2=lfilter(b,a,R2)
st=np.stack([L2,R2],1); st/=np.abs(st).max()/0.7
fi=np.minimum(t/2.0,1)[:,None]; st*=fi
wr('bgm.wav',st.reshape(-1),ch=2)
print('ok')
