import sys, json, wave
import numpy as np, sherpa_onnx
M="/tmp/claude-0/models"
wav, out, lang = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv)>3 else "")
w = wave.open(wav); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768
cfg = sherpa_onnx.VadModelConfig(); cfg.silero_vad.model=f"{M}/silero_vad.onnx"; cfg.silero_vad.min_silence_duration=0.25; cfg.silero_vad.min_speech_duration=0.2; cfg.silero_vad.threshold=0.45; cfg.silero_vad.max_speech_duration=12; cfg.sample_rate=sr
vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=120)
ws = cfg.silero_vad.window_size; segs=[]
for i in range(0, len(x), ws):
    vad.accept_waveform(x[i:i+ws])
    while not vad.empty():
        segs.append((vad.front.start, np.array(vad.front.samples))); vad.pop()
vad.flush()
while not vad.empty():
    segs.append((vad.front.start, np.array(vad.front.samples))); vad.pop()
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{M}/sherpa-onnx-whisper-turbo/turbo-encoder.int8.onnx", decoder=f"{M}/sherpa-onnx-whisper-turbo/turbo-decoder.int8.onnx", tokens=f"{M}/sherpa-onnx-whisper-turbo/turbo-tokens.txt", language=lang, task="transcribe", num_threads=8, tail_paddings=800)
res=[]
for st, smp in segs:
    s = rec.create_stream(); s.accept_waveform(sr, smp); rec.decode_stream(s)
    r = s.result
    item = {"start": st/sr, "end": (st+len(smp))/sr, "text": r.text.strip(), "lang": getattr(r,"lang",""), "ts": list(getattr(r,"timestamps",[]) or []), "tokens": list(getattr(r,"tokens",[]) or [])}
    res.append(item); print(f"[{item['start']:6.2f}-{item['end']:6.2f}] ({item['lang']}) {item['text']}", flush=True)
json.dump(res, open(out,"w"), indent=1, ensure_ascii=False)
