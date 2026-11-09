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
//   h/theory-<level>[.ru].<hash>.json   a level's theory articles (data/theory/<level>/<topic>[.ru].json, see
//                           docs/theory.md) packed into one file per language, in the order of the bank's topics
//   window.THEORY           level → { en, ru: the theory files, t: the topics that have an article }
// The unhashed data/<level>[.ru].json stay too (minified) for an app.js still open from before a deploy.
//
//   node miniapp/build.mjs            # build once
//   node miniapp/build.mjs --serve    # build and serve on http://localhost:5173 (rebuilds on every request)

import { cp, mkdir, rm, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { SITE, INDEXNOW_KEY, PAUSED } from './site.mjs';
import { buildPages } from './pages.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));
const out = join(root, 'miniapp/dist');

const FILES = [
  ['miniapp/index.html', 'index.html'],
  ['miniapp/app.js', 'app.js'],
  ['miniapp/app.css', 'app.css'],
  ['miniapp/intro.jpg', 'intro.jpg'], // the photo on the bot's /start welcome (bot/core.mjs)
  ['miniapp/fullcrimp.jpg', 'fullcrimp.jpg'], // the author's photo on the Home feedback card
  ['miniapp/group.png', 'group.png'], // the students' Telegram group picture on the Home group card
  // the RYC flag icons, taken from rycrentals.com
  ['miniapp/favicon.ico', 'favicon.ico'],
  ['miniapp/icon.png', 'icon.png'],
  ['miniapp/apple-icon.png', 'apple-icon.png'],
  ['miniapp/fonts', 'fonts'],
  ['miniapp/figs', 'figs'], // the articles' photos and plans (docs/design/blender/publish_figs.py)
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
  const banks = {}, order = {}, titles = {};
  for (const f of (await readdir(join(root, 'data/questions'))).filter((x) => x.endsWith('.json')).sort()) {
    const json = JSON.parse(await readFile(join(root, 'data/questions', f), 'utf8'));
    const min = JSON.stringify(json);
    const [level, lang = 'en'] = f.slice(0, -5).split('.');
    if (PAUSED.includes(level)) continue; // switched off for now (site.mjs); its articles go with it
    const name = `h/${f.slice(0, -5)}.${hash(min)}.json`;
    await writeFile(join(out, 'data', f), min);
    await writeFile(join(out, name), min);
    const b = (banks[level] = banks[level] || {});
    b[lang] = name;
    if (lang === 'en') { Object.assign(b, { n: json.questions.length, t: json.topics.length }); order[level] = json.topics.map((tp) => tp.id); titles[level] = json.title; }
  }

  // theory: a level's articles in one file per language; a topic with no article yet is simply not in it
  const theory = {};
  for (const level of (await readdir(join(root, 'data/theory')).catch(() => [])).sort()) {
    if (!order[level]) continue;
    let source = {};
    for (const lang of ['en', 'ru']) {
      let topics = {};
      for (const id of order[level]) {
        const file = join(root, 'data/theory', level, lang === 'en' ? `${id}.json` : `${id}.${lang}.json`);
        try { topics[id] = JSON.parse(await readFile(file, 'utf8')); } catch (e) { if (e.code !== 'ENOENT') throw new Error(`${file}: ${e.message}`); }
        // an article that is not shaped like one (data/check_theory.mjs says why) is left out, not shipped to break the tab
        const a = topics[id];
        if (a && !(typeof a.lead === 'string' && Array.isArray(a.sections) && a.sections.every((s) => s && s.id && Array.isArray(s.blocks)))) { console.warn(`skipped ${file}: not an article`); delete topics[id]; }
      }
      if (!Object.keys(topics).length) continue;
      if (lang === 'en') source = topics;
      // a topic not translated yet is read in English (en: true) rather than missing from the translated level
      else topics = Object.fromEntries(Object.keys(source).map((id) => [id, topics[id] || { ...source[id], en: true }]));
      const min = JSON.stringify({ level, lang, topics });
      const plain = `theory-${level}${lang === 'en' ? '' : `.${lang}`}`;
      await writeFile(join(out, 'data', `${plain}.json`), min);
      await writeFile(join(out, `h/${plain}.${hash(min)}.json`), min);
      const th = (theory[level] = theory[level] || {});
      th[lang] = `h/${plain}.${hash(min)}.json`;
      if (lang === 'en') th.t = Object.keys(topics);
    }
    if (theory[level] && !theory[level].en) delete theory[level]; // a translation without its source is not shown
  }

  let html = await readFile(join(out, 'index.html'), 'utf8');
  const swap = (from, to) => { if (!html.includes(from)) throw new Error(`index.html has no ${from}`); html = html.replace(from, to); };
  // the levels in the no-JavaScript copy of Home, smallest bank first (VHF … Yachtmaster), as search engines read it
  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const lv = Object.keys(titles).sort((a, b) => banks[a].n - banks[b].n || titles[a].localeCompare(titles[b]));
  swap('<ul data-levels></ul>', `<ul>${lv.map((l) => `<li><a href="/${l}">${esc(titles[l])}</a>: ${banks[l].n} questions in ${banks[l].t} topics${theory[l] ? `, theory articles for ${theory[l].t.length} of them` : ''}</li>`).join('')}</ul>`);
  swap('<script src="app.js"></script>', `<script>window.BANKS = ${JSON.stringify(banks)}; window.THEORY = ${JSON.stringify(theory)};</script>\n<script src="app.js"></script>`);
  const linked = {};
  for (const f of LINKED) {
    const buf = await readFile(join(out, f));
    const name = `h/${f.replace(/\//g, '-').replace(/(\.\w+)$/, `.${hash(buf)}$1`)}`;
    await writeFile(join(out, name), buf);
    swap(`"${f}"`, `"${name}"`);
    linked[f] = name;
  }
  await writeFile(join(out, 'index.html'), html);

  // for search engines (site.mjs): what to crawl and the key that lets indexnow.mjs announce the pages; then the
  // site's own pages, sitemap.xml and llms.txt (pages.mjs), in the app's look
  // AI crawlers are named, and welcome, search and training alike: the content is free and the MCP server gives it
  // out anyway. A crawler named in a group of its own skips the `*` group, so the group repeats its rules.
  const AI = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'PerplexityBot', 'Perplexity-User',
    'Google-Extended', 'Applebot-Extended', 'Amazonbot', 'meta-externalagent', 'DuckAssistBot', 'MistralAI-User', 'CCBot'];
  await writeFile(join(out, 'robots.txt'), `User-agent: *\nDisallow: /api/\n\n# AI search, assistants and training: welcome (the same content is at ${SITE}/llms.txt and ${SITE}/api/mcp)\n` +
    `${AI.map((a) => `User-agent: ${a}`).join('\n')}\nAllow: /\nDisallow: /api/\n\nSitemap: ${SITE}/sitemap.xml\n`);
  await writeFile(join(out, `${INDEXNOW_KEY}.txt`), INDEXNOW_KEY);
  await buildPages(out, { css: ['fonts/fonts.css', 'design/app.css', 'design/flows.css', 'app.css'].map((f) => linked[f]) });
}

await build();
console.log('built', out);

if (process.argv.includes('--serve')) {
  const port = +(process.env.PORT || 5173);
  const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.txt': 'text/plain', '.xml': 'application/xml', '.woff2': 'font/woff2' };
  createServer(async (req, res) => {
    try {
      const path = decodeURIComponent(new URL(req.url, 'http://x').pathname);
      if (path === '/' || path === '/index.html' || !extname(path)) await build(); // pick up edits on reload
      let file = normalize(join(out, path === '/' ? 'index.html' : path));
      if (!file.startsWith(out)) throw new Error('not found');
      // a page's clean address (/bareboat-skipper → bareboat-skipper.html), as cleanUrls does on Vercel
      if (!(await stat(file).catch(() => null))?.isFile()) file = `${file.replace(/\/$/, '')}.html`;
      if (!(await stat(file)).isFile()) throw new Error('not found');
      res.writeHead(200, { 'content-type': TYPES[extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
      res.end(await readFile(file));
    } catch (e) {
      const page = await readFile(join(out, '404.html')).catch(() => 'not found');
      res.writeHead(404, { 'content-type': 'text/html' }).end(page);
    }
  }).listen(port, () => console.log(`serving http://localhost:${port}`));
}
