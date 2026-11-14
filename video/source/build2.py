import json, re
OFF=0.25
W=[[a+OFF,b+OFF,w] for a,b,w in json.load(open('words4.json'))]
# merge "check" + "-ins"
M=[]
for a,b,w in W:
    if w.startswith('-') and M: M[-1][1]=b; M[-1][2]+=w
    else: M.append([a,b,w])
# first word really starts ~0.85
chunks=[];cur=[]
for i,(a,b,w) in enumerate(M):
    cur.append([a,b,w])
    nxt=M[i+1][0] if i+1<len(M) else 1e9
    if re.search(r'[,.?!]$',w) or len(cur)>=4 or nxt-b>0.45:
        if len(cur)==1 and chunks and not re.search(r'[.?!]$',chunks[-1][-1][2]) and cur[0][0]-chunks[-1][-1][1]<0.3 and len(chunks[-1])<5:
            chunks[-1]+=cur
        else: chunks.append(cur)
        cur=[]
caps=[]
for i,c in enumerate(chunks):
    end=chunks[i+1][0][0] if i+1<len(chunks) else c[-1][1]+0.5
    end=min(end,c[-1][1]+0.7)
    caps.append({'s':c[0][0]-0.06,'e':end,'w':[[a,w] for a,b,w in c]})
S=[0]+[round(x-0.12+OFF,2) for x in [2.56,5.62,8.48,14.1,16.28,18.7,21.54,23.92,26.88,34.86,39.66]]+[45.35]
names=['01_arrived_early','02_neonatal_unit','03_questions','04_catch_up','05_before_37_weeks','06_medical_care','07_sitting_milestone','08_walking_talking','09_development_areas','10_regular_checkins','11_early_support','12_celebrate']
focus=[(.62,.62),(.45,.45),(.5,.42),(.6,.55),(.55,.6),(.62,.64),(.6,.6),(.68,.55),(.5,.5),(.42,.55),(.5,.6),(.55,.3)]
titles=[[["Arrived ","earlier than expected?"]],[["A journey that began ","in the NICU"]],[["So many ","questions"]],[["Will my baby ","catch up?"]],
 [["Born before ","37 weeks"]],[["A little ","extra care"]],[["Milestones, ","a little later"]],[["Walking, talking… ","in their own time"]],
 [["Keep track of ","growth & development"]],[["You're ","not alone"],["Regular ","check-ins",29.4+OFF]],[["Early support, ","the right care"]],[["Celebrate ","every little beginning"]]]
scenes=[]
for i in range(12):
    tl=[{'t':(x[2] if len(x)>2 else S[i]),'a':x[0],'b':x[1]} for x in titles[i]]
    scenes.append({'img':f'up/{names[i]}.png','s':S[i],'e':S[i+1],'fx':focus[i][0],'fy':focus[i][1],'titles':tl})
json.dump({'scenes':scenes,'caps':caps,'end':S[-1]},open('data.json','w'))
for c in caps: print(round(c['s'],2),round(c['e'],2),' '.join(w for _,w in c['w']))
