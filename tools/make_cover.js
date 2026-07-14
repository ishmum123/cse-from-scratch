// Generate cover.png (1600x2560) using Playwright Chromium.
// Usage: node make_cover.js <output_path>
//
// Tries to load playwright from npx cache locations common on macOS.

function findPlaywright() {
  const tries = [
    // direct require (works if called via npx playwright)
    'playwright',
  ];

  // Scan npx cache
  const fs = require('fs');
  const path = require('path');
  const home = process.env.HOME || '/Users/' + (process.env.USER || 'ishmum');
  const npxCache = path.join(home, '.npm', '_npx');
  if (fs.existsSync(npxCache)) {
    for (const hash of fs.readdirSync(npxCache)) {
      const p = path.join(npxCache, hash, 'node_modules', 'playwright');
      if (fs.existsSync(p)) {
        try {
          const pkg = JSON.parse(fs.readFileSync(path.join(p, 'package.json'), 'utf8'));
          if (pkg.version && pkg.version.startsWith('1.61')) {
            tries.unshift(p);
          } else {
            tries.push(p);
          }
        } catch(e) {
          tries.push(p);
        }
      }
    }
  }

  for (const t of tries) {
    try {
      return require(t);
    } catch(e) { /* try next */ }
  }
  throw new Error('Cannot find playwright module. Run: npx playwright@1.61.1 install chromium');
}

const pw = findPlaywright();
const { chromium } = pw;

(async () => {
  const outPath = process.argv[2] || '/tmp/cover.png';

  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: 1600px;
  height: 2560px;
  background: #0d1117;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-family: 'Georgia', serif;
  color: #e6edf3;
  overflow: hidden;
}
.accent {
  width: 80px;
  height: 4px;
  background: #58a6ff;
  margin-bottom: 64px;
}
.title {
  font-size: 88px;
  font-weight: 700;
  text-align: center;
  line-height: 1.15;
  letter-spacing: -1px;
  max-width: 1280px;
  color: #f0f6fc;
}
.divider {
  width: 120px;
  height: 2px;
  background: #30363d;
  margin: 72px 0 56px;
}
.subtitle {
  font-size: 38px;
  color: #8b949e;
  letter-spacing: 1px;
  font-style: italic;
  max-width: 1100px;
  text-align: center;
  line-height: 1.4;
}
.author {
  position: absolute;
  bottom: 180px;
  font-size: 40px;
  color: #8b949e;
  letter-spacing: 4px;
  text-transform: uppercase;
}
.glow {
  position: absolute;
  top: 320px;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(88,166,255,0.08) 0%, transparent 70%);
}
</style>
</head>
<body>
<div class="glow"></div>
<div class="accent"></div>
<div class="title">Rebuilding<br/>Computer Science<br/>From Scratch</div>
<div class="divider"></div>
<div class="subtitle">A discovery-driven course —<br/>from counting to inference servers</div>
<div class="author">Ishmum Jawad Khan</div>
</body>
</html>`;

  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1600, height: 2560 });
  await page.setContent(html, { waitUntil: 'load' });
  await page.screenshot({ path: outPath, fullPage: false });
  await browser.close();
  console.log(`Cover written to ${outPath}`);
})().catch(e => { console.error(e.message); process.exit(1); });
