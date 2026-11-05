// Where the app lives in public, for search engines: build.mjs writes robots.txt and the IndexNow key file from this,
// pages.mjs the site's pages, sitemap.xml and llms.txt; indexnow.mjs tells Bing and Yandex (and the other IndexNow
// engines) which pages changed. index.html carries the same address in its canonical link and og:url — change it
// there too.
export const SITE = 'https://iyt.rycrentals.com';
// IndexNow proves we own the site by serving this key at SITE/<key>.txt. Any 32 hex characters; not a secret.
export const INDEXNOW_KEY = '3ed2766d7e6387078868387d41a53138';
// The bot the pages open the app in (t.me/<BOT>?startapp=<level link>).
export const BOT = 'iyt_test_bot';
