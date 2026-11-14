import json,re
mp=json.load(open('audio/map.json')); OFF=0.6
def m(t):
    for a,b,ns in mp:
        if t<=b: return round(max(t,a)-a+ns+OFF,3)
    a,b,ns=mp[-1]; return round(t-a+ns+OFF,3)
w=json.load(open('words_large.json'))
# drop the false start, insert retake timings
w=[x for x in w if not (54.0<x['s']<57.2)]
w+= [{'w':'So','s':57.0,'e':57.09},{'w':'this','s':57.09,'e':57.27}]
w.sort(key=lambda x:x['s'])
for x in w:
    if x['w'].strip()=='World' and x['s']>57: x['s']=57.27
text="""Did your little one arrive earlier than you expected?
Or do you know a parent whose journey began in a neonatal care unit?
Well, a premature birth can bring a lot of questions.
Will my baby catch up? Will they grow and develop like other children?
Or what, potentially, should we look out for?
Babies born before 37 weeks may need some extra medical care and support as they grow.
Sometimes, what happens is they may reach milestones like sitting, walking or talking a little later than we expect.
That's why keeping track of their growth and development can be important.
And as a parent, you don't have to figure it out all on your own.
Regular check-ins on your child's development can help identify areas where they might need that little extra support.
With early support, timely guidance and the right care, they can reach their full potential.
So this World Prematurity Day, let's celebrate every little beginning and every milestone that follows."""
toks=text.split()
norm=lambda s:re.sub(r"[^a-z0-9']","",s.lower().replace('’',"'"))
# merge ASR tokens like 'check' '-ins'
asr=[]
for x in w:
    t=x['w'].strip()
    if t.startswith('-') and asr: asr[-1]['w']+=t; asr[-1]['e']=x['e']
    else: asr.append({'w':t,'s':x['s'],'e':x['e']})
out=[];j=0
for t in toks:
    k=j
    while k<len(asr) and norm(asr[k]['w'])!=norm(t): k+=1
    if k>=len(asr) or k-j>3: print('MISMATCH',t,[a['w'] for a in asr[j:j+4]]); a=asr[j]
    else: a=asr[k]; j=k+1
    out.append({'w':t,'s':m(a['s']),'e':m(a['e'])})
json.dump(out,open('words_video.json','w'))
print(len(out),' '.join(f"{i}:{x['w']}@{x['s']}" for i,x in enumerate(out)))
