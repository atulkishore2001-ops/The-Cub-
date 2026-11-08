# Transcribe given (shot,in,out) snippets with Whisper to verify clean word boundaries
import sys, json, wave, numpy as np, sherpa_onnx
M="/tmp/claude-0/models/sherpa-onnx-whisper-turbo"
W=sys.argv[1]; items=json.loads(sys.argv[2])
X={}
for i in (1,2):
    w=wave.open(f"{W}/shot{i}.wav"); X[i]=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{M}/turbo-encoder.int8.onnx",decoder=f"{M}/turbo-decoder.int8.onnx",tokens=f"{M}/turbo-tokens.txt",language="en",task="transcribe",num_threads=4,tail_paddings=800)
for sh,a,b in items:
    seg=np.concatenate([np.zeros(4000,np.float32), X[sh][int(a*16000):int(b*16000)], np.zeros(4000,np.float32)])
    s=rec.create_stream(); s.accept_waveform(16000,seg); rec.decode_stream(s)
    print(f"shot{sh} {a:6.2f}-{b:6.2f}: {s.result.text.strip()}", flush=True)
