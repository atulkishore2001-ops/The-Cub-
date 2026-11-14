s=open('video.html').read()
N=99
F='file:///tmp/claude-0/-home-user-The-Cub-/83cc25c2-c0d8-5cba-8bd1-5aa33f828b03/scratchpad/'
css='''#logo{position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:100;display:none;background:#FAF1E9}
#logo img{position:absolute;left:0;top:0;display:none}
#mask{position:absolute;left:0;top:1070px;width:1080px;height:190px;background:#FAF1E9}
#tag{position:absolute;top:1088px;width:1080px;text-align:center;font-family:PF;font-style:italic;font-size:62px;color:#424242;letter-spacing:.5px}
#ul{position:absolute;top:1206px;left:50%;height:8px;border-radius:4px;background:#EE833D}
</style>'''
s=s.replace('</style>',css,1)
s=s.replace('<script>','<div id="logo">'+''.join(f'<img src="{F}lg/{i:03d}.png">' for i in range(1,N+1))+'<div id="mask"></div><div id="tag">Everyone Deserves To Be Seen</div><div id="ul"></div></div><script>',1)
js='''
  const LT=D.end+0.15, lg=document.querySelector('#logo');
  if(t>=LT){lg.style.display='block';const u=t-LT;const k=Math.min(NN-1,Math.floor(u*30+1e-6));
    if(window._lk!==k){const im=lg.querySelectorAll('img');if(window._lk!=null)im[window._lk].style.display='none';im[k].style.display='block';window._lk=k;}
    const w=eo((u-0.9)/1.0);const tg=document.querySelector('#tag');tg.style.clipPath='inset(0 '+(100-(8+84*w))+'% 0 0)';tg.style.opacity=cl((u-0.85)/0.2);
    const g=eo((u-1.7)/0.5);const ul=document.querySelector('#ul');ul.style.width=(112*g)+'px';ul.style.marginLeft=(-56*g)+'px';
  }else lg.style.display='none';
};
window.ready='''.replace('NN',str(N))
assert "};\nwindow.ready=" in s
s=s.replace("};\nwindow.ready=",js,1)
open('video.html','w').write(s)
