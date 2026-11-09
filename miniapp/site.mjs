// Where the app lives in public, for search engines: build.mjs writes robots.txt and the IndexNow key file from this,
// pages.mjs the site's pages, sitemap.xml and llms.txt; indexnow.mjs tells Bing and Yandex (and the other IndexNow
// engines) which pages changed. index.html carries the same address in its canonical link and og:url — change it
// there too.
export const SITE = 'https://iyt.rycrentals.com';
// IndexNow proves we own the site by serving this key at SITE/<key>.txt. Any 32 hex characters; not a secret.
export const INDEXNOW_KEY = '3ed2766d7e6387078868387d41a53138';
// The bot the pages open the app in (t.me/<BOT>?startapp=<level link>).
export const BOT = 'iyt_test_bot';
// Levels switched off for now: left out of the app (build.mjs ships no bank or articles for them), the site's pages, the
// bot and the MCP server. Their banks, articles and the students' progress on them stay as they are; take a level off
// this list to bring it back.
export const PAUSED = ['international-crew', 'flotilla-skipper', 'yachtmaster-coastal', 'yachtmaster-offshore', 'yachtmaster-ocean', 'racing-rules', 'charter-checkin'];
