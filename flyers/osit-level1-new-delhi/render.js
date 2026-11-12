// Renders index.html to social-media images (4:5 portrait).
//   osit-level1-new-delhi-flyer.png            2160 x 2700  (master, lossless)
//   osit-level1-new-delhi-flyer-1080x1350.jpg  1080 x 1350  (small file for WhatsApp / Instagram)
// Usage: node flyers/osit-level1-new-delhi/render.js   (needs the `playwright` package)
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const dir = __dirname;
  const url = 'file://' + path.join(dir, 'index.html');
  const browser = await chromium.launch();

  for (const [scale, file, opts] of [
    [2, 'osit-level1-new-delhi-flyer.png', { type: 'png' }],
    [1, 'osit-level1-new-delhi-flyer-1080x1350.jpg', { type: 'jpeg', quality: 93 }],
  ]) {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: scale });
    await page.goto(url);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(dir, file), ...opts });
    await page.close();
  }

  await browser.close();
  console.log('Wrote PNG (2160x2700) and JPG (1080x1350)');
})();
