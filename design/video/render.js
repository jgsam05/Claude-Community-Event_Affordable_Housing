// Renders design/video/oca-demo.html to PNG frames (30 fps, 30 s), then stitches an MP4 with ffmpeg.
// Usage: node render.js [outDir] [fromSeconds toSeconds]   (a range renders a few frames for review)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

(async () => {
  const out = process.argv[2] || path.join(__dirname, 'frames');
  const from = process.argv[3] !== undefined ? parseFloat(process.argv[3]) : 0;
  const to = process.argv[4] !== undefined ? parseFloat(process.argv[4]) : 30;
  const FPS = 30;
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'oca-demo.html') + '#manual');
  await page.waitForFunction('window.__ready === true', null, { timeout: 30000 });
  const start = Math.round(from * FPS), end = Math.round(to * FPS);
  for (let f = start; f < end; f++) {
    await page.evaluate((t) => window.render(t), f / FPS);
    await page.screenshot({ path: path.join(out, 'f' + String(f).padStart(4, '0') + '.png') });
    if (f % 90 === 0) console.log('frame', f);
  }
  await browser.close();
  if (from === 0 && to === 30 && process.argv[5] !== 'noencode') {
    execSync(`ffmpeg -y -loglevel error -framerate ${FPS} -i ${out}/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 ${path.join(out, '..', 'oca-demo.mp4')}`);
    console.log('encoded');
  }
})();
