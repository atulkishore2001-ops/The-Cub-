const {chromium}=require('playwright');const {spawn}=require('child_process');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('file://'+__dirname+'/video.html');await p.evaluate(()=>window.ready);
await p.evaluate(()=>document.fonts.load('700 40px DM').then(()=>document.fonts.load('italic 40px PF')));
const mode=process.argv[2];
if(mode==='probe'){for(const t of process.argv.slice(3)){await p.evaluate(t=>window.setT(t),+t);await p.screenshot({path:`fr/p_${t}.png`});}await b.close();return;}
const DUR=+process.argv[3],N=Math.round(DUR*30);
const ff=spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-c:v','mjpeg','-framerate','30','-i','-','-c:v','libx264','-preset','medium','-crf','15','-pix_fmt','yuv420p','-r','30','video_silent.mp4'],{stdio:['pipe','inherit','inherit']});
const t0=Date.now();
for(let i=0;i<N;i++){await p.evaluate(t=>window.setT(t),i/30);const buf=await p.screenshot({type:'jpeg',quality:96});
  if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));
  if(i%300==0)console.log(i,N,((Date.now()-t0)/1000).toFixed(0)+'s');}
ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();console.log('done');})();
