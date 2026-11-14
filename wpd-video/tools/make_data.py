# Builds web/data.js: words (video timeline), caption chunks, emphasis, scene times.
import json,sys,os
D=os.path.join(os.path.dirname(__file__),'..','web')
w=json.load(open(os.path.join(D,'words_video.json')))
import math
def clen(ids): return len(' '.join(w[j]['w'] for j in ids))
def best_split(ids,n):
    # split ids into n contiguous groups minimising max length, bonus for comma ends
    import itertools
    best=None
    for cuts in itertools.combinations(range(1,len(ids)),n-1):
        gs=[ids[a:b] for a,b in zip((0,)+cuts,cuts+(len(ids),))]
        score=max(clen(g) for g in gs)-sum(6 for g in gs[:-1] if w[g[-1]]['w'][-1] in ',')
        score+=sum(8 for g in gs if len(g)==1)
        if best is None or score<best[0]: best=(score,gs)
    return best[1]
sents=[];cur=[]
for i,x in enumerate(w):
    cur.append(i)
    if x['w'][-1] in '.?': sents.append(cur); cur=[]
if cur: sents.append(cur)
chunks=[]
for sids in sents:
    n=max(1,math.ceil(clen(sids)/46))
    for g in best_split(sids,n):
        chunks.append(best_split(g,2) if clen(g)>24 else [g])
emph=[56,57,58,77,95,96,97,135,136,137,138,141,142,151,152,153]
scenes=[0,4.30,8.25,19.05,24.7,31.1,34.3,44.15,50.4,56.45,60.6]
open(os.path.join(D,'data.js'),'w').write('const WORDS='+json.dumps(w)+';\nconst CHUNKS='+json.dumps(chunks)+';\nconst EMPH='+json.dumps(emph)+';\nconst SCENES='+json.dumps(scenes)+';\n')
for c in chunks: print(' / '.join(' '.join(w[j]['w'] for j in l) for l in c))
