// Assembles the mini app into miniapp/dist — a plain static folder to host anywhere over HTTPS
// (Telegram only opens mini apps from https URLs). Copies the app, the shared design files and the question banks.
//
//   node miniapp/build.mjs            # build once
//   node miniapp/build.mjs --serve    # build and serve on http://localhost:5173 (rebuilds on every request)

import { cp, mkdir, rm, readFile, stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const out = join(root, 'miniapp/dist');

const FILES = [
  ['miniapp/index.html', 'index.html'],
  ['miniapp/app.js', 'app.js'],
  ['miniapp/app.css', 'app.css'],
  ['docs/design/app.css', 'design/app.css'],
  ['docs/design/flows.css', 'design/flows.css'],
  ['docs/design/icons.js', 'design/icons.js'],
  ['docs/design/test-icons.js', 'design/test-icons.js'],
  ['docs/design/figures.js', 'design/figures.js'],
  ['docs/design/logo-black.svg', 'design/logo-black.svg'],
  ['docs/design/LICENSE-lucide.txt', 'design/LICENSE-lucide.txt'],
  ['data/questions', 'data'],
];

async function build() {
  await rm(out, { recursive: true, force: true });
  await mkdir(join(out, 'design'), { recursive: true });
  for (const [from, to] of FILES) await cp(join(root, from), join(out, to), { recursive: true });
}

await build();
console.log('built', out);

if (process.argv.includes('--serve')) {
  const port = +(process.env.PORT || 5173);
  const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.txt': 'text/plain' };
  createServer(async (req, res) => {
    try {
      const path = decodeURIComponent(new URL(req.url, 'http://x').pathname);
      if (path === '/' || path === '/index.html') await build(); // pick up edits on reload
      const file = normalize(join(out, path === '/' ? 'index.html' : path));
      if (!file.startsWith(out) || !(await stat(file)).isFile()) throw new Error('not found');
      res.writeHead(200, { 'content-type': TYPES[extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
      res.end(await readFile(file));
    } catch (e) {
      res.writeHead(404).end('not found');
    }
  }).listen(port, () => console.log(`serving http://localhost:${port}`));
}
