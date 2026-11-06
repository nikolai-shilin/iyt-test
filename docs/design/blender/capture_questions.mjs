// Saves the plan-view schematics of test questions drawn by question-figures.html, at 2x, into
// docs/design/figure-style/questions/<level>/<slug>/plan.png (--ru: plan.ru.png, through that level's ru.json).
// Needs the figure-style server on :5182.   node docs/design/blender/capture_questions.mjs vhf-radio-operator [--ru]
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
//   node docs/design/blender/capture_questions.mjs bareboat-skipper --type encounter [--ru]   # <id>/plan[.ru].png and q[.ru].png
const HERE = dirname(fileURLToPath(import.meta.url)), level = process.argv[2] || 'vhf-radio-operator', RU = process.argv.includes('--ru');
const TYPE = process.argv.includes('--type') ? process.argv[process.argv.indexOf('--type') + 1] : '';
const OUT = join(HERE, '..', 'figure-style', 'questions', level);
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', PORT = 9400 + Math.floor(Math.random() * 500);   // several agents may capture at once
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--no-first-run', `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'q-cap-'))}`, 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
try {
  let ver; for (let i = 0; i < 50 && !ver; i++) { await sleep(200); ver = await fetch(`http://127.0.0.1:${PORT}/json/version`).then(r => r.json()).catch(() => null); }
  const tab = await fetch(`http://127.0.0.1:${PORT}/json/new?` + encodeURIComponent('about:blank'), { method: 'PUT' }).then(r => r.json());
  const ws = new WebSocket(tab.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r, { once: true }));
  let id = 0; const pending = new Map();
  ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); setTimeout(() => r({}), 60000); });
  const evaluate = async expression => (await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })).result?.result?.value;
  await send('Emulation.setDeviceMetricsOverride', { width: 1200, height: 1200, deviceScaleFactor: 2, mobile: false });
  await send('Page.enable');
  await send('Page.navigate', { url: `http://localhost:5182/question-figures.html?l=${level}${TYPE ? `&t=${TYPE}` : ''}${RU ? '&lang=ru' : ''}` });
  let done; for (let i = 0; i < 600 && done !== '1'; i++) { await sleep(250); done = await evaluate('document.body && document.body.dataset.done'); }
  if (done !== '1') throw new Error('page did not finish');
  await sleep(300);
  const boxes = await evaluate(`[...document.querySelectorAll('.q')].map(r => { const b = r.querySelector('.sch svg').getBoundingClientRect(); return { slug: r.dataset.slug, kind: r.dataset.kind || 'plan', clip: { x: b.x + scrollX, y: b.y + scrollY, width: b.width, height: b.height, scale: 1 } }; })`);
  for (const b of boxes) {
    const shot = await send('Page.captureScreenshot', { format: 'png', clip: b.clip, captureBeyondViewport: true });
    mkdirSync(join(OUT, b.slug), { recursive: true });
    writeFileSync(join(OUT, b.slug, `${b.kind}${RU ? '.ru' : ''}.png`), Buffer.from(shot.result.data, 'base64')); console.log(b.slug, b.kind, Math.round(b.clip.width), 'px');
  }
  ws.close();
} finally { chrome.kill(); }
