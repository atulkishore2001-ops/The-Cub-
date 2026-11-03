# print RMS envelope (dB) around given times for a shot, 10ms hop
import sys, wave, numpy as np
wav=sys.argv[1]; w=wave.open(wav); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
hop=int(sr*0.01); n=len(x)//hop
rms=np.sqrt(np.array([np.mean(x[i*hop:(i+1)*hop]**2) for i in range(n)])+1e-10); db=20*np.log10(rms)
for t in map(float, sys.argv[2:]):
    a=int((t-0.35)/0.01); b=int((t+0.35)/0.01)
    seg=db[max(a,0):b]
    s=' '.join(f'{v:4.0f}' for v in seg[::2])
    print(f'{t:6.2f}: min {seg.min():.0f}dB @ {(max(a,0)+seg.argmin())*0.01:.2f} | {s}')
