import sys, wave, numpy as np, sherpa_onnx
M="/tmp/claude-0/models/sherpa-onnx-whisper-medium.en"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{M}/medium.en-encoder.int8.onnx", decoder=f"{M}/medium.en-decoder.int8.onnx", tokens=f"{M}/medium.en-tokens.txt", language="en", task="transcribe", num_threads=4, tail_paddings=800)
W=sys.argv[1]
for spec in sys.argv[2:]:
    n,a,b=spec.split(":"); a=float(a); b=float(b)
    w=wave.open(f"{W}/{n}.wav"); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
    seg=np.concatenate([np.zeros(8000,np.float32),x[int(a*sr):int(b*sr)],np.zeros(8000,np.float32)])
    s=rec.create_stream(); s.accept_waveform(sr,seg); rec.decode_stream(s); print(f"{spec}: {s.result.text.strip()}", flush=True)
