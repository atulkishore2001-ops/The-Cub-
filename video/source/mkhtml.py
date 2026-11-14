import json
D=open('data.json').read()
F='file:///tmp/claude-0/-home-user-The-Cub-/83cc25c2-c0d8-5cba-8bd1-5aa33f828b03/scratchpad/'
html='''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:DM;font-weight:500;src:url(FONTS/@fontsource/dm-sans/files/dm-sans-latin-500-normal.woff2)}
@font-face{font-family:DM;font-weight:700;src:url(FONTS/@fontsource/dm-sans/files/dm-sans-latin-700-normal.woff2)}
@font-face{font-family:PF;font-style:italic;src:url(FONTS/@fontsource/playfair-display/files/playfair-display-latin-500-italic.woff2)}
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;background:#FAF1E9;overflow:hidden;font-family:DM;position:relative}
#glow{position:absolute;left:-160px;top:330px;width:1400px;height:1400px;border-radius:50%;background:radial-gradient(circle,#FBDDBE 0%,#FBE9D4 38%,rgba(250,241,233,0) 68%)}
#label{position:absolute;top:118px;width:100%;text-align:center;color:#EE833D;font-weight:700;font-size:30px;letter-spacing:9px}
#label span{display:inline-block;width:70px;height:3px;background:#EE833D;vertical-align:middle;margin:0 22px;border-radius:2px;opacity:.7}
.title{position:absolute;top:226px;left:50%;white-space:nowrap;background:#fff;border-radius:30px;padding:26px 44px;font-size:47px;font-weight:700;color:#2b2b2b;box-shadow:0 10px 30px rgba(190,130,80,.18)}
.title i{font-family:PF;font-style:italic;font-weight:500;color:#EE833D;font-size:52px}
.card{position:absolute;left:80px;top:440px;width:920px;height:920px;border-radius:56px;background:#fff;padding:16px;box-shadow:0 26px 60px rgba(180,110,60,.26)}
.card .in{width:100%;height:100%;border-radius:42px;overflow:hidden;position:relative}
.card img{width:100%;height:100%;display:block;position:absolute}
.fx{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none}
.fx svg{position:absolute;overflow:visible}
#dots{position:absolute;top:1432px;width:100%;display:flex;justify-content:center;gap:14px}
#dots b{display:block;height:14px;width:14px;border-radius:7px;background:#E9D6C5}
#cap{position:absolute;top:1530px;left:50%;white-space:nowrap;background:#424242;color:#fff;font-weight:700;font-size:52px;padding:24px 46px;border-radius:60px;box-shadow:0 10px 26px rgba(60,40,30,.22)}
#cap span.on{color:#F59A55}
.deco{position:absolute}
</style></head><body>
<div id="glow"></div>
<div id="label"><span></span>WORLD PREMATURITY DAY<span></span></div>
<div id="decos"></div><div id="titles"></div><div id="cards"></div>
<div id="dots"></div><div id="cap"></div>
<script>
const D=DATA;const S=D.scenes;const $=q=>document.querySelector(q);
const cl=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const eo=x=>1-Math.pow(1-cl(x),3);
const back=x=>{x=cl(x);const c=1.9;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
const HEART='M0,9 C-22,-7 -13,-24 0,-12 C13,-24 22,-7 0,9Z';
const STAR='M0,-14 L3.5,-3.5 L14,0 L3.5,3.5 L0,14 L-3.5,3.5 L-14,0 L-3.5,-3.5Z';
S.forEach((s,i)=>{
  const c=document.createElement('div');c.className='card';
  let fx='';
  if(i==1||i==11)for(let k=0;k<3;k++)fx+=`<svg class="h"><path d="${HEART}" fill="#EE833D" stroke="#fff" stroke-width="3"/></svg>`;
  if(i==1||i==11)for(let k=0;k<4;k++)fx+=`<svg class="s"><path d="${STAR}" fill="#fff" stroke="#EE833D" stroke-width="2.5"/></svg>`;
  c.innerHTML=`<div class="in"><img src="BASE${s.img}"><div class="fx">${fx}</div></div>`;
  $('#cards').appendChild(c);s.el=c;s.imgEl=c.querySelector('img');s.h=[...c.querySelectorAll('.h')];s.st=[...c.querySelectorAll('.s')];
  s.titles.forEach(tl=>{const d=document.createElement('div');d.className='title';d.innerHTML=tl.a.replace(/ /g,'&nbsp;')+'<i>'+tl.b+'</i>';$('#titles').appendChild(d);tl.el=d;});
  const b=document.createElement('b');$('#dots').appendChild(b);s.dot=b;
});
// background decorations (orange stars/hearts around the card)
const DEC=[[58,400,1,0],[1010,430,0,.8],[40,1330,0,1.7],[1030,1290,1,2.4],[980,236,1,3.1],[96,250,0,.4]];
DEC.forEach(d=>{const e=document.createElement('div');e.className='deco';e.innerHTML=`<svg width="60" height="60" viewBox="-30 -30 60 60"><path d="${d[2]?STAR:HEART}" transform="scale(1.5)" fill="${d[2]?'none':'#EE833D'}" stroke="#EE833D" stroke-width="2.4"/></svg>`;$('#decos').appendChild(e);d.el=e;});
window.setT=function(t){
  const END=D.end, out=cl((t-END+0.1)/0.5);           // everything fades away before the logo
  $('#glow').style.opacity=(0.75+0.18*Math.sin(t*1.1))*eo(t/1.0)*(1-out);
  $('#glow').style.transform=`scale(${1+0.04*Math.sin(t*0.7)})`;
  $('#label').style.opacity=eo((t-0.1)/0.6)*(1-out);
  $('#label').style.transform=`translateY(${-20*(1-eo((t-0.1)/0.6))}px)`;
  const G=Math.max(eo((t-S[1].s-0.25)/0.5)*(1-cl((t-S[1].e+0.15)/0.35)),eo((t-S[11].s-0.25)/0.5));
  DEC.forEach((d,k)=>{const p=t*0.9+d[3]*2;const tw=0.55+0.45*Math.sin(p*1.7);
    d.el.style.left=(d[0]-30+6*Math.sin(p*0.6))+'px';d.el.style.top=(d[1]-30+9*Math.cos(p*0.5))+'px';
    d.el.style.opacity=tw*G*(1-out);d.el.style.transform=`scale(${0.75+0.3*tw}) rotate(${12*Math.sin(p*0.4)}deg)`;});
  S.forEach((s,i)=>{
    const a=t-s.s, dur=s.e-s.s, last=i==S.length-1;
    const vin=eo(a/0.45), vout=last?out:cl((t-s.e)/0.4);
    const vis=a>=0&&vout<1;
    s.el.style.display=vis?'block':'none';
    if(vis){
      const sc=(0.88+0.12*back(a/0.6))*(1-0.05*vout);
      const bob=7*Math.sin(t*1.45+i), rot=0.45*Math.sin(t*1.05+i*2)+(1-eo(a/0.6))*(i%2?2.5:-2.5);
      s.el.style.opacity=vin*(1-vout);s.el.style.zIndex=10+i;
      s.el.style.transform=`translate(${(1-eo(a/0.55))*(i%2?70:-70)-60*vout*(i%2?1:-1)}px,${bob+40*(1-eo(a/0.55))}px) rotate(${rot}deg) scale(${sc})`;
      // image: slow push-in on the character + soft "breathing"
      const p=cl(a/dur);const z=(i==8?1.02:1.05)+(i==8?0.05:0.12)*p+0.007*Math.sin(t*2.0);
      const dx=(i%2?-1:1)*10*(p-0.5);
      s.imgEl.style.transformOrigin=`${s.fx*100}% ${s.fy*100}%`;
      s.imgEl.style.transform=`translate(${dx}px,0) scale(${z})`;
      // hearts drifting up from the character
      s.h.forEach((h,k)=>{const ph=((a-0.5-k*0.9)/2.9);const f=ph-Math.floor(ph);const on=ph>=0;
        const x=s.fx*888+(k-1)*70+22*Math.sin(f*6+k*2), y=s.fy*888-60-170*f;
        h.style.left=x+'px';h.style.top=y+'px';h.style.opacity=on?Math.sin(Math.PI*f)*0.95:0;h.style.transform=`scale(${0.9+0.7*f})`;});
      s.st.forEach((st,k)=>{const ang=k*1.7+i, r=190+40*(k%2);const x=cl(s.fx*888+r*Math.cos(ang),60,830), y=cl(s.fy*888+r*Math.sin(ang)*0.8,60,830);
        const tw=Math.max(0,Math.sin(t*2.3+k*1.9+i));
        st.style.left=x+'px';st.style.top=y+'px';st.style.opacity=tw*eo((a-0.4)/0.4);st.style.transform=`scale(${0.5+0.9*tw}) rotate(${t*25+k*30}deg)`;});
    }
    s.titles.forEach((tl,k)=>{const nx=s.titles[k+1];const te=nx?nx.t:s.e;const b=t-tl.t;
      const i2=eo(b/0.45), o2=last&&!nx?out:cl((t-te)/0.3);const v=b>=0&&o2<1;
      tl.el.style.display=v?'block':'none';
      if(v){tl.el.style.opacity=i2*(1-o2);tl.el.style.transform=`translate(-50%,${-34*(1-back(b/0.5))+18*o2}px) scale(${0.94+0.06*back(b/0.5)})`;}});
    const act=t>=s.s&&(t<s.e||last);const dn=t>=s.e&&!last;
    s.dot.style.width=act?'46px':'14px';s.dot.style.background=act?'#EE833D':(dn?'#F3B58B':'#E9D6C5');
  });
  $('#dots').style.opacity=eo((t-0.3)/0.5)*(1-out);
  let c=null;for(const x of D.caps){if(t>=x.s&&t<x.e)c=x}
  const cap=$('#cap');
  if(c){const b=t-c.s;let ai=0;c.w.forEach((w,k)=>{if(t>=w[0]-0.04)ai=k});
    cap.innerHTML=c.w.map((w,k)=>`<span class="${k==ai?'on':''}">${w[1]}</span>`).join(' ');
    cap.style.display='block';cap.style.opacity=eo(b/0.12)*(1-out);cap.style.transform=`translate(-50%,${10*(1-eo(b/0.18))}px) scale(${0.95+0.05*back(b/0.22)})`;
  }else cap.style.display='none';
};
window.ready=Promise.all([document.fonts.ready,...[...document.images].map(im=>im.decode())]).then(()=>true);
</script></body></html>'''
html=html.replace('DATA',D).replace('BASE',F).replace('FONTS',F+'fonts/node_modules')
open('video.html','w').write(html)
