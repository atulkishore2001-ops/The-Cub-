// node render.js frames_dir [workers]  -> frames_dir/f_00000.png ... (1080x1920 @ 30fps)
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => {
  const out = process.argv[2], W = parseInt(process.argv[3] || '4');
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const url = 'file://' + path.resolve(__dirname, '../web/index.html');
  const probe = await b.newPage(); await probe.goto(url); await probe.evaluate(() => window.assetsReady);
  const total = await probe.evaluate(() => window.TOTAL), fps = 30; await probe.close();
  const N = Math.round(total * fps);
  console.log('frames', N);
  let done = 0;
  await Promise.all([...Array(W).keys()].map(async w => {
    const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
    p.on('pageerror', e => console.log('PAGEERR', e.message));
    await p.goto(url); await p.evaluate(() => window.assetsReady);
    for (let i = w; i < N; i += W) {
      await p.evaluate(t => window.renderAt(t), i / fps);
      await p.screenshot({ path: `${out}/f_${String(i).padStart(5, '0')}.png` });
      if (++done % 200 === 0) console.log(done);
    }
  }));
  await b.close();
})();
