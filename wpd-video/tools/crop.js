// node crop.js out.png t x y w h scale
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const [out, t, x, y, w, h, sc] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: parseFloat(sc || 1) });
  p.on('pageerror', e => console.log('PAGEERR', e.message));
  await p.goto('file://' + path.resolve(__dirname, '../web/index.html'));
  await p.evaluate(() => window.assetsReady);
  await p.evaluate(t => window.renderAt(t), parseFloat(t));
  await p.screenshot({ path: out, clip: { x: +x, y: +y, width: +w, height: +h } });
  await b.close();
})();
