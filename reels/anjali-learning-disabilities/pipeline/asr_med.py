import sys, wave, numpy as np, sherpa_onnx
M="/tmp/claude-0/models/sherpa-onnx-whisper-medium.en"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{M}/medium.en-encoder.int8.onnx", decoder=f"{M}/medium.en-decoder.int8.onnx", tokens=f"{M}/medium.en-tokens.txt", language="en", task="transcribe", num_threads=4, tail_paddings=800)
def run(path, a=0, b=None, label=""):
    w=wave.open(path); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
    seg=x[int(a*sr):int((b or len(x)/sr)*sr)]
    seg=np.concatenate([np.zeros(8000,np.float32),seg,np.zeros(8000,np.float32)])
    s=rec.create_stream(); s.accept_waveform(sr,seg); rec.decode_stream(s); print(f"{label or path.split('/')[-1]} {a}-{b}: {s.result.text.strip()}", flush=True)
W=sys.argv[1]
run(f"{W}/audio1.wav", 3.2, 18.6); run(f"{W}/audio1.wav", 3.2, 11.4, "a1-first-sentence"); run(f"{W}/audio1.wav", 8.0, 11.4, "a1-let-the"); run(f"{W}/audio2.wav", 1.0, 8.0)
run(f"{W}/shot1.wav", 10.0, 14.2, "name"); run(f"{W}/shot1.wav", 4.4, 9.4, "congrats")
