// Saves an article's figures as images from article-figures.html: each figure's "before" (today's figure) and its
// schematic, at 2x, into docs/design/figure-style/articles/<level>/<article>/<n>-before.png and <n>-schematic.png.
// Needs the figure-style server on :5182 (python3 -m http.server 5182 --directory docs/design).
//   node docs/design/blender/capture_article.mjs bareboat-skipper/anchoring
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

//   node docs/design/blender/capture_article.mjs bareboat-skipper/anchoring --ru        # <n>-schematic.ru.png, through ru.json
//   node docs/design/blender/capture_article.mjs bareboat-skipper/anchoring --strings   # strings.json: what ru.json translates
const HERE = dirname(fileURLToPath(import.meta.url)), article = process.argv[2] || 'bareboat-skipper/anchoring';
const RU = process.argv.includes('--ru'), STRINGS = process.argv.includes('--strings');
const OUT = join(HERE, '..', 'figure-style', 'articles', ...article.split('/'));
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', PORT = 9341;
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--no-first-run', `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'art-cap-'))}`, 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
try {
  let ver; for (let i = 0; i < 50 && !ver; i++) { await sleep(200); ver = await fetch(`http://127.0.0.1:${PORT}/json/version`).then(r => r.json()).catch(() => null); }
  const tab = await fetch(`http://127.0.0.1:${PORT}/json/new?` + encodeURIComponent('about:blank'), { method: 'PUT' }).then(r => r.json());
  const ws = new WebSocket(tab.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r, { once: true }));
  let id = 0; const pending = new Map();
  ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); setTimeout(() => r({}), 60000); });
  const evaluate = async expression => (await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })).result?.result?.value;
  await send('Emulation.setDeviceMetricsOverride', { width: 2200, height: 1200, deviceScaleFactor: 2, mobile: false });
  await send('Page.enable');
  await send('Page.navigate', { url: `http://localhost:5182/article-figures.html?a=${article}${RU ? '&lang=ru' : ''}` });
  let done; for (let i = 0; i < 240 && done !== '1'; i++) { await sleep(250); done = await evaluate('document.body && document.body.dataset.done'); }
  if (done !== '1') throw new Error('page did not finish');
  await sleep(500);
  const boxes = await evaluate(`[...document.querySelectorAll('.row')].map(r => {
    const n = (r.querySelector('h3')?.textContent || '').split('.')[0].trim(), box = el => { if (!el) return null; const b = el.getBoundingClientRect(); return { x: b.x + scrollX, y: b.y + scrollY, width: b.width, height: b.height, scale: 1 }; };
    const sch = r.querySelector('.sch svg') || r.querySelector('.sch');
    return { n, before: box(r.querySelector('.before')), sch: box(sch) };
  })`);
  mkdirSync(OUT, { recursive: true });
  if (STRINGS) {
    // the schematic's strings (from the page) and the render's labels (<n>-3d.labels.json), per figure
    const sch = await evaluate('window.__strings'), out = {};
    for (const n of Object.keys(sch)) {
      let lab = []; try { const L = JSON.parse(readFileSync(join(OUT, `${n}-3d.labels.json`), 'utf8')); lab = [L.note, ...(L.labels || []).map((x) => x.text)].filter(Boolean); } catch {}
      out[n] = { render: lab, schematic: sch[n] };
    }
    writeFileSync(join(OUT, 'strings.json'), JSON.stringify(out, null, 1)); console.log('strings', Object.keys(out).length); ws.close(); process.exit(0);
  }
  for (const b of boxes) {
    for (const [key, clip] of [['before', b.before], ['schematic', b.sch]]) {
      if (!clip || clip.width < 10) continue;
      const shot = await send('Page.captureScreenshot', { format: 'png', clip, captureBeyondViewport: true });
      const data = shot.result?.data; if (!data) { console.log('no shot', b.n, key); continue; }
      writeFileSync(join(OUT, `${b.n}-${key}${RU ? '.ru' : ''}.png`), Buffer.from(data, 'base64'));
    }
    console.log(`fig ${b.n}: before ${Math.round(b.before?.width || 0)} px, schematic ${Math.round(b.sch?.width || 0)} px`);
  }
  ws.close();
} finally { chrome.kill(); }
