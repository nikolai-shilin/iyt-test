// Assembles the mini app into miniapp/dist — a plain static folder to host anywhere over HTTPS
// (Telegram only opens mini apps from https URLs). Copies the app, the shared design files (with the icon sheet at
// design/icons.html), the fonts and the question banks.
//
// What the browser loads is content-addressed, so it can be cached for good (vercel.json: /h/* and /fonts/* are
// immutable) while index.html itself is checked on every open:
//   h/<name>.<hash>.<ext>   every script and stylesheet index.html links, renamed after its content
//   h/<level>[.ru].<hash>.json   each question bank, minified
//   window.BANKS            written into index.html: level → { en, ru: the bank files, n: questions, t: topics },
//                           so the home screen can show every level while only the current level's bank downloads
// The unhashed data/<level>[.ru].json stay too (minified) for an app.js still open from before a deploy.
//
//   node miniapp/build.mjs            # build once
//   node miniapp/build.mjs --serve    # build and serve on http://localhost:5173 (rebuilds on every request)

import { cp, mkdir, rm, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const out = join(root, 'miniapp/dist');

const FILES = [
  ['miniapp/index.html', 'index.html'],
  ['miniapp/app.js', 'app.js'],
  ['miniapp/app.css', 'app.css'],
  ['miniapp/intro.jpg', 'intro.jpg'], // the photo on the bot's /start welcome (bot/core.mjs)
  ['miniapp/fonts', 'fonts'],
  ['docs/design/app.css', 'design/app.css'],
  ['docs/design/flows.css', 'design/flows.css'],
  ['docs/design/icons.js', 'design/icons.js'],
  ['docs/design/test-icons.js', 'design/test-icons.js'],
  ['docs/design/icons.html', 'design/icons.html'],
  ['docs/design/figures.js', 'design/figures.js'],
  ['docs/design/logo-black.svg', 'design/logo-black.svg'],
  ['docs/design/LICENSE-lucide.txt', 'design/LICENSE-lucide.txt'],
];
// The files index.html links, in the order they appear there; each gets a hashed copy in h/.
const LINKED = ['fonts/fonts.css', 'design/app.css', 'design/flows.css', 'app.css', 'design/icons.js', 'design/test-icons.js', 'design/figures.js', 'app.js'];

const hash = (buf) => createHash('sha256').update(buf).digest('hex').slice(0, 10);

async function build() {
  await rm(out, { recursive: true, force: true });
  for (const d of ['design', 'h', 'data']) await mkdir(join(out, d), { recursive: true });
  for (const [from, to] of FILES) await cp(join(root, from), join(out, to), { recursive: true });

  // banks: minified, under their own name in data/ and their content's name in h/
  const banks = {};
  for (const f of (await readdir(join(root, 'data/questions'))).filter((x) => x.endsWith('.json')).sort()) {
    const json = JSON.parse(await readFile(join(root, 'data/questions', f), 'utf8'));
    const min = JSON.stringify(json);
    const [level, lang = 'en'] = f.slice(0, -5).split('.');
    const name = `h/${f.slice(0, -5)}.${hash(min)}.json`;
    await writeFile(join(out, 'data', f), min);
    await writeFile(join(out, name), min);
    const b = (banks[level] = banks[level] || {});
    b[lang] = name;
    if (lang === 'en') Object.assign(b, { n: json.questions.length, t: json.topics.length });
  }

  let html = await readFile(join(out, 'index.html'), 'utf8');
  const swap = (from, to) => { if (!html.includes(from)) throw new Error(`index.html has no ${from}`); html = html.replace(from, to); };
  swap('<script src="app.js"></script>', `<script>window.BANKS = ${JSON.stringify(banks)};</script>\n<script src="app.js"></script>`);
  for (const f of LINKED) {
    const buf = await readFile(join(out, f));
    const name = `h/${f.replace(/\//g, '-').replace(/(\.\w+)$/, `.${hash(buf)}$1`)}`;
    await writeFile(join(out, name), buf);
    swap(`"${f}"`, `"${name}"`);
  }
  await writeFile(join(out, 'index.html'), html);
}

await build();
console.log('built', out);

if (process.argv.includes('--serve')) {
  const port = +(process.env.PORT || 5173);
  const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.txt': 'text/plain', '.woff2': 'font/woff2' };
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
