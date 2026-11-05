// Where the app lives in public, for search engines: build.mjs writes robots.txt, sitemap.xml and the IndexNow key
// file from this; indexnow.mjs tells Bing and Yandex (and the other IndexNow engines) when it changed.
// index.html carries the same address in its canonical link and og:url — change it there too.
export const SITE = 'https://iyt.rycrentals.com';
// IndexNow proves we own the site by serving this key at SITE/<key>.txt. Any 32 hex characters; not a secret.
export const INDEXNOW_KEY = '3ed2766d7e6387078868387d41a53138';
// The pages to index: the app has one address (screens are not separate pages yet).
export const PAGES = ['/'];
