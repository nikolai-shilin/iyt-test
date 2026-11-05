// Tells the IndexNow search engines (Bing, Yandex, Seznam, Naver…) that the site's pages changed, so they crawl them
// soon instead of whenever they next pass by. Run it after a production deploy:
//
//   npm run seo:ping              # submit every page in site.mjs
//   npm run seo:ping -- --check   # only check that SITE/<key>.txt is live (the engines read it to trust us)
//
// Google does not take IndexNow: it reads SITE/sitemap.xml, submitted once in Search Console.

import { SITE, INDEXNOW_KEY, PAGES } from './site.mjs';

const keyLocation = `${SITE}/${INDEXNOW_KEY}.txt`;
const live = await fetch(keyLocation).then((r) => (r.ok ? r.text() : '')).catch(() => '');
if (live.trim() !== INDEXNOW_KEY) {
  console.error(`${keyLocation} does not serve the key yet — deploy first (npx vercel deploy --prod).`);
  process.exit(1);
}
console.log(`key file live: ${keyLocation}`);
if (process.argv.includes('--check')) process.exit(0);

const urlList = PAGES.map((p) => SITE + p);
const res = await fetch('https://api.indexnow.org/indexnow', {
  method: 'POST',
  headers: { 'content-type': 'application/json; charset=utf-8' },
  body: JSON.stringify({ host: new URL(SITE).host, key: INDEXNOW_KEY, keyLocation, urlList }),
});
// 200 = taken, 202 = taken, key check pending; anything else says what is wrong
console.log(`IndexNow: ${res.status} ${res.statusText} for ${urlList.join(', ')}`);
if (res.status >= 300) { console.error(await res.text()); process.exit(1); }
