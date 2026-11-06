// Runs export.html in headless Chrome (over the DevTools protocol, so it waits for the CDN modules and the
// async glTF export) and writes, per scene, <name>.glb (everything but the ropes) and <name>.json (ropes,
// camera, labels, note, sun) into docs/design/blender/scenes/.
// Needs the figure-style server on :5182 (python3 -m http.server 5182 --directory docs/design).
//   node docs/design/blender/export_scenes.mjs winch cleat rail sheet
//   node docs/design/blender/export_scenes.mjs --knots
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url)), OUT = join(HERE, 'scenes');
const args = process.argv.slice(2), query = args[0] === '--knots' ? 'set=knots' : 'kind=' + args.join(',');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', PORT = 9339;
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--no-first-run', `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'rope-export-'))}`, 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
try {
  let ver; for (let i = 0; i < 50 && !ver; i++) { await sleep(200); ver = await fetch(`http://127.0.0.1:${PORT}/json/version`).then(r => r.json()).catch(() => null); }
  const tab = await fetch(`http://127.0.0.1:${PORT}/json/new?` + encodeURIComponent(`http://localhost:5182/blender/export.html?${query}`), { method: 'PUT' }).then(r => r.json());
  const ws = new WebSocket(tab.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r, { once: true }));
  let id = 0; const pending = new Map();
  ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
  const evaluate = expression => new Promise(r => { setTimeout(() => r({}), 60000); const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method: 'Runtime.evaluate', params: { expression, returnByValue: true } })); }).then(m => m.result?.result?.value);
  let done; for (let i = 0; i < 600 && !done; i++) { await sleep(500); done = await evaluate('document.body && document.body.dataset.done'); }
  const len = await evaluate("document.getElementById('out').textContent.length"); let text = '';
  for (let i = 0; i < len; i += 1 << 20) text += await evaluate(`document.getElementById('out').textContent.slice(${i}, ${i + (1 << 20)})`);
  if (done !== '1') throw new Error('export failed: ' + String(text).slice(0, 2000));
  mkdirSync(OUT, { recursive: true });
  for (const [name, d] of Object.entries(JSON.parse(text))) {
    const glb = Buffer.from(d.glb, 'base64'); delete d.glb;
    writeFileSync(join(OUT, name + '.glb'), glb); writeFileSync(join(OUT, name + '.json'), JSON.stringify(d));
    console.log(`${name}: glb ${Math.round(glb.length / 1024)} KB, ropes ${d.ropes.length}, labels ${d.labels.length}`);
  }
  ws.close();
} finally { chrome.kill(); }
