// Renders index.html to a print PDF (768 x 1152 pt, same size as the original)
// and a 2048 x 3072 PNG for sharing.
// Usage: node posters/sherlock-squad/render.js   (needs the `playwright` package)
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const dir = __dirname;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1024, height: 1536 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.join(dir, 'index.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);

  await page.screenshot({ path: path.join(dir, 'sherlock-squad-poster.png') });
  await page.pdf({
    path: path.join(dir, 'sherlock-squad-poster.pdf'),
    width: '1024px',
    height: '1536px',
    printBackground: true,
    pageRanges: '1',
  });

  await browser.close();
  console.log('Wrote sherlock-squad-poster.png and sherlock-squad-poster.pdf');
})();
