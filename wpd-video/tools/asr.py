from faster_whisper import WhisperModel
import json,sys
m=WhisperModel("medium.en",device="cpu",compute_type="int8")
import numpy as np,wave
wf=wave.open(sys.argv[1]);a=np.frombuffer(wf.readframes(wf.getnframes()),dtype=np.int16).astype(np.float32)/32768
segs,info=m.transcribe(a,word_timestamps=True,beam_size=5,vad_filter=False)
out=[]
for s in segs:
    print(f"[{s.start:.2f}-{s.end:.2f}] {s.text}")
    for w in s.words: out.append({"w":w.word,"s":w.start,"e":w.end})
json.dump(out,open("words.json","w"),indent=0)
