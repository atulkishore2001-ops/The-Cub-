# Original warm, gentle piano + pad score (procedurally synthesised; royalty-free).
import numpy as np, soundfile as sf, sys
SR=48000; DUR=float(sys.argv[2]) if len(sys.argv)>2 else 61.0; out=sys.argv[1]
N=int(SR*DUR); L=np.zeros(N); Rr=np.zeros(N)
bpm=76; beat=60/bpm; bar=4*beat
def hz(m): return 440*2**((m-69)/12)
rng=np.random.default_rng(7)
def piano(m,t0,dur,vel,pan=0.0):
    f=hz(m); n=int(dur*SR); t=np.arange(n)/SR
    env=np.exp(-t*(2.2+f/900))*(1-np.exp(-t*400))
    x=sum(a*np.sin(2*np.pi*f*k*t*(1+0.0004*k*k))*np.exp(-t*k*0.9) for k,a in [(1,1),(2,.42),(3,.18),(4,.08),(5,.04)])
    x*=env*vel; i=int(t0*SR)
    if i>=N: return
    j=min(N,i+n); x=x[:j-i]
    L[i:j]+=x*(1-pan)*.7; Rr[i:j]+=x*(1+pan)*.7
def pad(ms,t0,dur,vel):
    n=int(dur*SR); t=np.arange(n)/SR
    env=np.minimum(1,t/1.2)*np.minimum(1,(dur-t)/1.0).clip(0)
    x=np.zeros(n); y=np.zeros(n)
    for m in ms:
        f=hz(m)
        for d,p in [(-0.12,-.5),(0.12,.5),(0,0)]:
            s=np.sin(2*np.pi*f*(1+d/100)*t+rng.random()*6)+.25*np.sin(2*np.pi*2*f*(1+d/100)*t)
            x+=s*(1-p); y+=s*(1+p)
    i=int(t0*SR); j=min(N,i+n)
    L[i:j]+=(x*env*vel)[:j-i]; Rr[i:j]+=(y*env*vel)[:j-i]
# progression: C  G/B  Am  F   |  F  G  Em  Am  ... ends on C
prog=[(48,[60,64,67]),(47,[59,62,67]),(45,[57,60,64]),(41,[57,60,65]),
      (48,[60,64,67]),(43,[59,62,67]),(45,[57,60,64]),(41,[57,60,65]),
      (41,[57,60,65]),(43,[59,62,67]),(40,[59,64,67]),(45,[57,60,64]),
      (41,[57,60,65]),(43,[59,62,67]),(48,[60,64,67]),(48,[60,64,67]),
      (41,[57,60,65]),(43,[59,62,67]),(48,[60,64,67]),(48,[60,64,67])]
melody={4:[76,74,72,74],5:[71,72,74,0],6:[76,79,76,74],7:[72,0,72,0],
        8:[72,74,76,0],9:[74,76,79,0],10:[79,76,74,76],11:[72,0,0,0],
        12:[77,76,74,72],13:[74,76,79,81],14:[79,0,76,0],15:[72,0,0,0],
        16:[77,76,74,72],17:[74,0,79,0],18:[76,0,0,0]}
t=0.0; b=0
while t<DUR-0.5:
    bass,ch=prog[b%len(prog)]
    late=t>30
    pad([bass+12]+ch,t,bar+1.2,.010 if not late else .013)
    piano(bass,t,4.5,.22,-.2)
    if late: piano(bass-12,t,4.5,.12,-.2)
    arp=[ch[0],ch[1],ch[2],ch[1]+12 if late else ch[1]]
    for k in range(8):
        piano(arp[k%4]+12*(k>=4 and late),t+k*beat/2,2.4,.075+.02*(k%2==0),.25 if k%2 else -.1)
    if b in melody and t>4:
        for k,m in enumerate(melody[b]):
            if m: piano(m,t+k*beat,3.0,.11,.1)
    t+=bar; b+=1
# simple stereo reverb
def reverb(x,seed):
    r=np.random.default_rng(seed); n=int(2.4*SR); tt=np.arange(n)/SR
    ir=r.standard_normal(n)*np.exp(-tt*2.6); ir[:int(.02*SR)]=0; ir/=np.sqrt((ir**2).sum())
    from scipy.signal import fftconvolve
    return fftconvolve(x,ir)[:len(x)]
try:
    import scipy; Lw=L+.35*reverb(L,1); Rw=Rr+.35*reverb(Rr,2)
except ImportError:
    Lw,Rw=L,Rr
y=np.stack([Lw,Rw],1)
fi=int(2.0*SR); y[:fi]*=np.linspace(0,1,fi)[:,None]
fo=int(3.0*SR); y[-fo:]*=np.linspace(1,0,fo)[:,None]**1.5
y/=np.abs(y).max()*1.12
sf.write(out,y,SR,subtype='PCM_24')
print('music',DUR)
