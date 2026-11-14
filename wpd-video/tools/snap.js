// usage: node snap.js out_dir t1 t2 ...   -> PNG stills (540x960 preview)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [out, ...ts] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 0.5 });
  p.on('pageerror', e => console.log('PAGEERR', e.message));
  p.on('console', m => console.log('CONSOLE', m.text()));
  await p.goto('file://' + path.resolve(__dirname, '../web/index.html'));
  await p.evaluate(() => window.assetsReady);
  for (const t of ts) {
    await p.evaluate(t => window.renderAt(t), parseFloat(t));
    await p.screenshot({ path: `${out}/t_${t}.png` });
  }
  await b.close();
})();
