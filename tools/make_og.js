#!/usr/bin/env node
// Share-preview images (1200 x 630) for link cards on X, Slack, etc.
//
// Usage, from the repo root after `python3 build.py SRC_DIR .`:
//   node tools/make_og.js            # every explainer in STEP, plus the homepage
//   node tools/make_og.js ternary    # one page ("home" for the homepage)
// then run build.py again so the page heads link og/<key>.png.
//
// Each explainer card shows its signature story scene (the step below), the
// kicker, the page title and the homepage card blurb (the page's meta description).
const fs = require('fs'), path = require('path');
let pw; try { pw = require('playwright') } catch { pw = require('/opt/node22/lib/node_modules/playwright') }
const CHROMIUM = process.env.PW_CHROMIUM || (fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined);

// key -> index of the story step whose scene represents the paper (0-based)
const STEP = { ff: 1, cocrystal: 3, lockring: 1, barrierless: 7, vloss: 1, ternary: 6, optgap: 7, arrhenius: 5, backtransfer: 6, tta: 8, timeline: 3, damacro: 0, tpa: 4, giwaxs: 8, whitelight: 3, photodet: 4, laser: 3 };
const HOME_CARDS = ['ff', 'cocrystal', 'lockring', 'barrierless'];

const ROOT = path.resolve(__dirname, '..'), OUT = path.join(ROOT, 'og');
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function card({ img, imgs, kicker, title, desc, foot }) {
  const pic = imgs
    ? `<div class="grid">${imgs.map(s => `<img src="${s}">`).join('')}</div>`
    : `<div class="pic" style="background-image:url(${img})"></div>`;
  return `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&family=Source+Code+Pro:wght@500&family=Source+Sans+3:wght@400;600&display=swap">
<style>body{margin:0;width:1200px;height:630px;background:#0b0e14;color:#e8eef7;display:grid;grid-template-columns:640px 1fr;font-family:"Source Sans 3",system-ui,sans-serif;overflow:hidden}
.pic{background:#0b0e14 center/cover no-repeat;border-right:1px solid #1d2430}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:40px 30px;align-content:center;border-right:1px solid #1d2430}.grid img{width:100%;border-radius:4px}
.t{padding:56px 52px;display:flex;flex-direction:column;gap:22px;justify-content:center}
.k{font:500 18px "Source Code Pro",ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:#e6a75c}
h1{font:600 46px/1.1 "Source Serif 4",Georgia,serif;margin:0}
.d{font-size:22px;color:#a3aab4;line-height:1.35}.n{font-size:20px;color:#a3aab4;margin-top:auto}.n b{color:#e8eef7}</style></head>
<body>${pic}<div class="t"><div class="k">${esc(kicker)}</div><h1>${esc(title)}</h1><div class="d">${esc(desc)}</div><div class="n">${foot}</div></div></body></html>`;
}

async function shot(page, html, out) {
  const tmp = path.join(OUT, '.card.html'); fs.writeFileSync(tmp, html);
  await page.goto('file://' + tmp); await page.waitForLoadState('networkidle').catch(() => {}); await page.waitForTimeout(800);
  await page.screenshot({ path: out }); fs.unlinkSync(tmp);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const keys = process.argv.slice(2).length ? process.argv.slice(2) : [...Object.keys(STEP), 'home'];
  const b = await pw.chromium.launch({ executablePath: CHROMIUM });
  const page = await b.newPage({ viewport: { width: 1280, height: 860 } });
  const cardPage = await b.newPage({ viewport: { width: 1200, height: 630 } });
  for (const k of keys) {
    if (k === 'home') {
      await page.goto('file://' + path.join(ROOT, 'index.html')); await page.waitForTimeout(1500);
      const imgs = [];
      for (const c of HOME_CARDS) { const el = await page.$(`canvas[data-k="${c}"]`); imgs.push('data:image/png;base64,' + (await el.screenshot()).toString('base64')) }
      const title = await page.$eval('h1', e => e.textContent.trim());
      await shot(cardPage, card({ imgs, kicker: 'Organic solar cells · device physics', title, desc: 'Interactive explainers of papers by Huotian Zhang and co-authors.', foot: '<b>Huotian Zhang</b> · University of Potsdam' }), path.join(OUT, 'home.png'));
      console.log('og/home.png'); continue;
    }
    if (!(k in STEP)) { console.error(`no signature step for "${k}": add it to STEP`); process.exitCode = 1; continue }
    await page.goto('file://' + path.join(ROOT, 'explainers', k + '.html')); await page.waitForTimeout(600);
    await page.evaluate(i => document.querySelectorAll('.step')[i].scrollIntoView({ block: 'center' }), STEP[k]); await page.waitForTimeout(1500);
    const img = 'data:image/png;base64,' + (await (await page.$('#story')).screenshot()).toString('base64');
    const [kicker, title, desc] = await page.evaluate(() => [document.querySelector('.kicker').textContent.trim(), document.querySelector('h1').textContent.trim(), document.querySelector('meta[name=description]').content]);
    await shot(cardPage, card({ img, kicker, title, desc, foot: '<b>Huotian Zhang</b> · interactive explainer' }), path.join(OUT, k + '.png'));
    console.log(`og/${k}.png`);
  }
  await b.close();
})();
