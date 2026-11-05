// Tells the IndexNow search engines (Bing, Yandex, Seznam, Naver…) which of the site's pages changed, so they crawl
// them soon instead of whenever they next pass by. Run it after a production deploy:
//
//   npm run seo:ping              # the pages that are new, changed or gone since the last ping
//   npm run seo:ping -- --dry     # list them, send nothing
//   npm run seo:ping -- --all     # every page
//   npm run seo:ping -- --check   # only check that SITE/<key>.txt is live (the engines read it to trust us)
//
// What changed comes from the live SITE/pages.json (pages.mjs: each address with a hash of its page) against the copy
// saved after the last ping, miniapp/.indexnow-sent.json (not in git: a machine without it sends every page once).
// Pinging pages that did not change does not speed anything up, and engines may start to ignore a site that does it.
// Google does not take IndexNow: it reads SITE/sitemap.xml, submitted once in Search Console.

import { readFile, writeFile } from 'node:fs/promises';
import { SITE, INDEXNOW_KEY } from './site.mjs';

const arg = (f) => process.argv.includes(f);
const sentFile = new URL('.indexnow-sent.json', import.meta.url);
const keyLocation = `${SITE}/${INDEXNOW_KEY}.txt`;

const live = await fetch(keyLocation).then((r) => (r.ok ? r.text() : '')).catch(() => '');
if (live.trim() !== INDEXNOW_KEY) {
  console.error(`${keyLocation} does not serve the key yet — deploy first (npx vercel deploy --prod).`);
  process.exit(1);
}
console.log(`key file live: ${keyLocation}`);
if (arg('--check')) process.exit(0);

const now = await fetch(`${SITE}/pages.json`, { cache: 'no-store' }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
if (!now) { console.error(`${SITE}/pages.json is not live — deploy a build that has it first.`); process.exit(1); }
const before = arg('--all') ? {} : JSON.parse(await readFile(sentFile, 'utf8').catch(() => '{}'));
// new or changed pages, and pages that are gone (an engine drops them sooner when told)
const paths = [...Object.keys(now).filter((p) => now[p] !== before[p]), ...Object.keys(before).filter((p) => !(p in now))];
if (!paths.length) { console.log('nothing changed since the last ping'); process.exit(0); }
console.log(`${paths.length} of ${Object.keys(now).length} pages to send${paths.length <= 12 ? `: ${paths.join(' ')}` : ''}`);
if (arg('--dry')) process.exit(0);

// at most 10 000 addresses a request
for (let i = 0; i < paths.length; i += 10000) {
  const urlList = paths.slice(i, i + 10000).map((p) => SITE + p);
  const res = await fetch('https://api.indexnow.org/indexnow', {
    method: 'POST',
    headers: { 'content-type': 'application/json; charset=utf-8' },
    body: JSON.stringify({ host: new URL(SITE).host, key: INDEXNOW_KEY, keyLocation, urlList }),
  });
  // 200 = taken, 202 = taken, key check pending; anything else says what is wrong
  console.log(`IndexNow: ${res.status} ${res.statusText} for ${urlList.length} pages`);
  if (res.status >= 300) { console.error(await res.text()); process.exit(1); }
}
await writeFile(sentFile, JSON.stringify(now, null, 1));
