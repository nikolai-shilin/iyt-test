// api/game.mjs's rankings: the points of a daily race, the month's table, and the answers of GET ?day= and the POST of
// a start with the boat's flag, against a database played by a stub of fetch. Run: npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';

process.env.SUPABASE_URL = 'https://db.test';
process.env.SUPABASE_SECRET_KEY = 'sb_secret_test';
process.env.TELEGRAM_BOT_TOKEN = '1:test';
const { GET, POST, bests, rankDay, monthTable, playersOf, playersFrom, elosFrom, accountFlag, floorSecs, perfOf, endOf, visitOf, openOf, dailyYacht } = await import('../api/game.mjs');

const day = (d) => new Date(Date.now() - d * 864e5).toISOString().slice(0, 10);
const at = (d, h = 10) => `${day(d)}T${String(h).padStart(2, '0')}:00:00Z`;
// a finished daily race
const race = (o) => ({ started_at: at(0), finished_at: at(0), user_id: null, player: null, wind: 'medium', secs: 200, dsq: false, place: 1, daily: day(0), flag: null, ...o });

// The database: game_races gives back rows (whatever the filter, the URL is kept), users the Telegram names, Auth
// a site account's display name. missing: a column the table doesn't have yet. recent: what the read of the ranked
// players' latest races (for their flags: every race of the last 30 days, no daily= filter) gets, rows when not given.
function stub({ rows = [], recent = null, users = [], accounts = {}, missing = null, tokens = {} } = {}) {
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    const u = String(url); calls.push({ url: u, method: init.method || 'GET', body: init.body && JSON.parse(init.body) });
    const fail = (col) => new Response(JSON.stringify({ message: `column game_races.${col} does not exist` }), { status: 400 });
    if (u.includes('/rest/v1/game_races')) {
      if (missing && (init.method === 'POST' ? init.body.includes(`"${missing}"`) : u.includes(missing))) return fail(missing);
      if (init.method === 'POST' || init.method === 'PATCH') return Response.json([]);
      // GET ?me's look for one race of the player's: the rows that are theirs
      const one = /select=id&(user_id|player)=eq\.([^&]+)/.exec(u);
      if (one) return Response.json(rows.filter((r) => String(r[one[1]]) === decodeURIComponent(one[2])).slice(0, 1).map(() => ({ id: 'x' })));
      const off = Number(/offset=(\d+)/.exec(u)?.[1] || 0);
      return Response.json(off ? [] : recent && !u.includes('daily=') ? recent : rows);
    }
    if (u.includes('/rest/v1/game_visits')) {
      if (missing === 'game_visits') return new Response(JSON.stringify({ message: 'relation "public.game_visits" does not exist' }), { status: 404 });
      return Response.json([]);
    }
    if (u.includes('/rest/v1/users')) return Response.json(users);
    if (u.includes('/rest/v1/errors')) return Response.json([]);
    // Auth's user behind an access token (tokens: token → { id, app_metadata })
    if (u.endsWith('/auth/v1/user')) {
      const t = /^Bearer (.+)$/.exec((init.headers && init.headers.authorization) || '')?.[1];
      return tokens[t] ? Response.json(tokens[t]) : new Response('', { status: 401 });
    }
    const acc = /admin\/users\/([0-9a-f-]+)/.exec(u);
    const m = acc && accounts[acc[1]];
    if (acc) return m ? Response.json({ user_metadata: typeof m === 'string' ? { display_name: m } : m }) : new Response('', { status: 404 });
    return new Response('', { status: 404 });
  };
  return calls;
}
const A = '11111111-1111-4111-8111-111111111111', B = '22222222-2222-4222-8222-222222222222';

test('a day: the fastest gets as many points as players ranked, equal times share the better place', () => {
  const list = rankDay(bests([
    race({ user_id: 1, secs: 210 }), race({ user_id: 1, secs: 190, place: 3 }), // two races: the better time counts
    race({ user_id: 2, secs: 200, place: 2 }), race({ player: A, secs: 200 }),  // a tie for second
    race({ user_id: 3, secs: 250 }),
    race({ secs: 100 }), race({ secs: 120 }),                                    // guests: never ranked
    race({ user_id: 4, secs: 150, dsq: true }), race({ user_id: 5, secs: null }), // out: disqualified, no time
  ]));
  assert.deepEqual(list.map((x) => [x.key, x.s, x.place, x.pts, x.n]), [[1, 190, 1, 4, 2], [2, 200, 2, 3, 1], [`a:${A}`, 200, 2, 3, 1], [3, 250, 4, 1, 1]]);
  assert.equal(list[0].p, 1, 'the best place of their races');
});

test('the month adds the days up: most points, then wins, then podiums', () => {
  const d1 = rankDay(bests([race({ user_id: 1, secs: 100 }), race({ user_id: 2, secs: 110 }), race({ user_id: 3, secs: 120 })]));
  const d2 = rankDay(bests([race({ user_id: 2, secs: 100 }), race({ user_id: 1, secs: 110 })]));
  const d3 = rankDay(bests([race({ user_id: 3, secs: 100 })]));
  const m = monthTable([d1, d2, d3]);
  assert.deepEqual(m.map((x) => [x.key, x.pts, x.days, x.wins, x.podiums]), [[1, 4, 2, 1, 2], [2, 4, 2, 1, 2], [3, 2, 2, 1, 2]]);
});

test('GET ?day=: the day ranked, the month to it, names, flags from the latest race, keys that are not ids', async () => {
  const calls = stub({
    rows: [
      race({ user_id: 7, secs: 180, flag: 'gb', started_at: at(0, 9) }), race({ user_id: 7, secs: 175, flag: 'it', started_at: at(0, 11), place: 2 }),
      race({ player: A, secs: 190, flag: 'gb-sct' }), race({ secs: 170 }),
      ...(day(0).slice(0, 7) === day(1).slice(0, 7) ? [race({ player: A, secs: 160, daily: day(1), started_at: at(1), finished_at: at(1) }), race({ user_id: 7, secs: 170, daily: day(1), started_at: at(1), finished_at: at(1) })] : []),
    ],
    users: [{ id: 7, name: ' Anna   Petrova ' }], accounts: { [A]: 'Fed' },
  });
  const r = await GET(new Request(`https://x.test/api/game?day=${day(0)}`));
  assert.equal(r.status, 200);
  assert.match(r.headers.get('cache-control'), /s-maxage=300/, "today's: the card's five minutes");
  const j = await r.json();
  assert.equal(j.d, day(0)); assert.equal(j.races, 4); assert.equal(j.guests, 1); assert.equal(j.w, 'medium');
  assert.deepEqual(j.rows.map((x) => [x.name, x.fl, x.s, x.p, x.pts, x.n]), [['Anna Petrova', 'it', 175, 1, 2, 2], ['Fed', 'gb-sct', 190, 1, 1, 1]]);
  assert.ok(j.rows[0].ph && j.rows[0].k === j.rows[0].ph, 'a Telegram player: the picture key is their key');
  assert.equal(j.rows[1].ph, null); assert.match(j.rows[1].k, /^[A-Za-z0-9_-]{16}$/);
  assert.ok(!JSON.stringify(j).includes(A) && !/"7"|:7[,}]/.test(JSON.stringify(j)), 'no raw ids');
  assert.equal(j.month.m, day(0).slice(0, 7));
  if (j.days.length === 2) {
    assert.deepEqual(j.days, [day(0), day(1)]);
    assert.deepEqual(j.month.rows.map((x) => [x.name, x.pts, x.days, x.wins, x.podiums]), [['Anna Petrova', 3, 2, 1, 2], ['Fed', 3, 2, 1, 2]]);
  }
  const q = calls.find((c) => c.url.includes('game_races')).url;
  assert.match(q, new RegExp(`daily=gte\\.${day(0).slice(0, 7)}-01&daily=lte\\.${day(0)}&finished_at=not\\.is\\.null`));
  assert.match(q, /select=[^&]*flag/);
});

test('GET ?day=: a past day is cached long; the future, a non-date and the far past are not found', async () => {
  stub({ rows: [] });
  const past = await GET(new Request(`https://x.test/api/game?day=${day(3)}`));
  assert.equal(past.status, 200); assert.match(past.headers.get('cache-control'), /s-maxage=86400/);
  assert.deepEqual((await past.json()).rows, []);
  for (const d of [day(-1), '2026-02-30', 'today', day(500)]) assert.equal((await GET(new Request(`https://x.test/api/game?day=${d}`))).status, 404, d);
});

test('GET ?day=: the flag a player flies is the one of their latest race of any kind, an unfinished one or a free race too', async () => {
  const calls = stub({
    rows: [race({ user_id: 7, secs: 180, started_at: at(0, 9) }), race({ player: A, secs: 190, flag: 'fr', started_at: at(0, 9) }), race({ user_id: 8, secs: 200, flag: 'nl' })],
    recent: [
      { started_at: at(0, 12), user_id: 7, player: null, flag: 'ge' },   // a later start, not finished: flies Georgia now
      { started_at: at(0, 12), user_id: null, player: A, flag: null },   // took their flag down since
      { started_at: at(0, 12), user_id: 99, player: null, flag: 'it' },  // not on the rating: no matter
    ],
    users: [{ id: 7, name: 'Anna' }, { id: 8, name: 'Bo' }], accounts: { [A]: 'Fed' },
  });
  const j = await (await GET(new Request(`https://x.test/api/game?day=${day(0)}`))).json();
  assert.deepEqual(j.rows.map((x) => [x.name, x.fl]), [['Anna', 'ge'], ['Fed', null], ['Bo', 'nl']]);
  const q = calls.filter((c) => c.url.includes('game_races')).at(-1).url;
  assert.match(q, /select=started_at,user_id,player,flag&/); assert.ok(!q.includes('finished_at'), 'any race, finished or not');
  assert.ok(!q.includes('or=') && !q.includes('daily='), 'every recent race, read as the game card reads them');
  assert.match(decodeURIComponent(q), /started_at=gte\.\d{4}-\d{2}-\d{2}T/);
});

test('GET ?day= before the flag column is there: read without it', async () => {
  const calls = stub({ rows: [race({ user_id: 7 })], users: [{ id: 7, name: 'Anna' }], missing: 'flag' });
  const j = await (await GET(new Request(`https://x.test/api/game?day=${day(0)}`))).json();
  assert.deepEqual(j.rows.map((x) => [x.name, x.fl]), [['Anna', null]]);
  assert.ok(calls.filter((c) => c.url.includes('game_races')).at(-1).url.includes('select=started_at') && !calls.filter((c) => c.url.includes('game_races')).at(-1).url.includes('flag'));
});

test('GET: the game card\'s podiums carry each player\'s flag', async () => {
  stub({ rows: [race({ user_id: 7, flag: 'nl', secs: 150 }), race({ player: B, secs: 160 })], users: [{ id: 7, name: 'Anna' }], accounts: { [B]: 'Bo Z' } });
  const j = await (await GET(new Request('https://x.test/api/game'))).json();
  assert.deepEqual(j.daily.top.map((x) => [x.name, x.fl]), [['Anna', 'nl'], ['Bo Z.', null]]);
});

test('a site account\'s flag is its boat\'s, else its latest race\'s', async () => {
  assert.equal(accountFlag({ boat: { flag: 'by', num: '7' } }), 'by');
  assert.equal(accountFlag({ boat: { num: '7' } }), null, 'a boat that flies no flag');
  assert.equal(accountFlag({ boat: { flag: 'Evil<' } }), null);
  assert.equal(accountFlag({ display_name: 'Fed' }), undefined, 'no boat kept: the race says');
  assert.equal(accountFlag({ boat: ['by'] }), undefined);
  assert.equal(accountFlag(null), undefined);
  const C = '33333333-3333-4333-8333-333333333334';
  stub({
    rows: [race({ player: A, secs: 150 }), race({ player: B, secs: 160, flag: 'nl' }), race({ player: C, secs: 170, flag: 'it' }), race({ user_id: 7, secs: 180, flag: 'gb' })],
    users: [{ id: 7, name: 'Anna' }],
    accounts: { [A]: { display_name: 'Nikolai S', boat: { flag: 'by' } }, [B]: { display_name: 'Bo Z', boat: { num: '3' } }, [C]: 'Cy' },
  });
  const j = await (await GET(new Request(`https://x.test/api/game?day=${day(0)}`))).json();
  assert.deepEqual(j.rows.map((x) => [x.name, x.fl]), [['Nikolai S', 'by'], ['Bo Z', null], ['Cy', 'it'], ['Anna', 'gb']]);
  assert.deepEqual(j.month.rows.find((x) => x.name === 'Nikolai S').fl, 'by');
  const card = await (await GET(new Request('https://x.test/api/game'))).json();
  assert.deepEqual(card.daily.top.map((x) => [x.name, x.fl]), [['Nikolai S.', 'by'], ['Bo Z.', null], ['Cy', 'it']]);
});

test('POST start: the boat\'s flag is kept when it is a flag, and left out before its column is there', async () => {
  const id = '33333333-3333-4333-8333-333333333333', post = (body) => POST(new Request('https://x.test/api/game', { method: 'POST', body: JSON.stringify(body), headers: { 'x-forwarded-for': `10.0.0.${Math.random() * 250 | 0}` } }));
  let calls = stub();
  await post({ ev: 'start', id, wind: 'light', laps: 1, length: 'short', boats: 4, flag: 'gb-sct' });
  assert.equal(calls.find((c) => c.method === 'POST').body.flag, 'gb-sct');
  calls = stub();
  await post({ ev: 'start', id, wind: 'light', flag: 'GB<script>' });
  assert.ok(!('flag' in calls.find((c) => c.method === 'POST').body));
  calls = stub({ missing: 'flag' });
  await post({ ev: 'start', id, wind: 'light', flag: 'fr' });
  const posts = calls.filter((c) => c.method === 'POST');
  assert.equal(posts.length, 2); assert.ok(!('flag' in posts[1].body));
});

test('POST finish: a finish without a good fleet keeps the start\'s, and a place outside the fleet is none', async () => {
  const id = '44444444-4444-4444-8444-444444444444', post = (body) => POST(new Request('https://x.test/api/game', { method: 'POST', body: JSON.stringify(body), headers: { 'x-forwarded-for': `10.0.1.${Math.random() * 250 | 0}` } }));
  const started = [{ started_at: new Date(Date.now() - 600e3).toISOString(), wind: 'medium', length: 'short', laps: 1, boats: 5 }];
  const patch = (calls) => calls.find((c) => c.method === 'PATCH').body;
  let calls = stub({ rows: started });
  await post({ ev: 'finish', id, place: 2, secs: 300, dsq: false });
  assert.equal(patch(calls).boats, 5, 'the start\'s fleet is kept');
  assert.equal(patch(calls).place, 2);
  calls = stub({ rows: started });
  await post({ ev: 'finish', id, place: 7, boats: 5, secs: 300, dsq: false });
  assert.equal(patch(calls).place, null);
  assert.equal(patch(calls).boats, 5);
  calls = stub({ rows: started });
  await post({ ev: 'finish', id, place: 3, boats: 4, secs: 300, dsq: true });
  assert.equal(patch(calls).place, null);
  assert.equal(patch(calls).dsq, true);
  assert.equal(patch(calls).secs, 300);
});

test('GET ?day=&brief: the day alone, its top named and every ranked time, without the month', async () => {
  const calls = stub({
    rows: [race({ user_id: 7, secs: 175, flag: 'it' }), race({ player: A, secs: 190 }), race({ player: B, secs: 182 }), race({ secs: 150 })],
    users: [{ id: 7, name: 'Anna Petrova' }], accounts: { [A]: 'Fed', [B]: 'Bo' },
  });
  const r = await GET(new Request(`https://x.test/api/game?day=${day(0)}&brief`));
  assert.equal(r.status, 200); assert.match(r.headers.get('cache-control'), /s-maxage=300/);
  const j = await r.json();
  assert.equal(j.ranked, 3); assert.equal(j.races, 4); assert.equal(j.guests, 1);
  assert.deepEqual(j.s, [175, 182, 190], 'every ranked time, a guest\'s left out');
  assert.deepEqual(j.top.map((x) => [x.name, x.fl, x.s, x.pts]), [['Anna Petrova', 'it', 175, 3], ['Bo', null, 182, 2], ['Fed', null, 190, 1]]);
  assert.equal(j.month, undefined); assert.equal(j.rows, undefined);
  const q = calls.find((c) => c.url.includes('game_races')).url;
  assert.match(q, new RegExp(`daily=eq\\.${day(0)}&finished_at`), "that day's races only");
  const past = await GET(new Request(`https://x.test/api/game?day=${day(3)}&brief`));
  assert.match(past.headers.get('cache-control'), /s-maxage=86400/);
});

test('POST start and finish: the yacht is kept, and a faster class gets her share of the floor', async () => {
  const id = '55555555-5555-4555-8555-555555555555', post = (body) => POST(new Request('https://x.test/api/game', { method: 'POST', body: JSON.stringify(body), headers: { 'x-forwarded-for': `10.0.2.${Math.random() * 250 | 0}` } }));
  let calls = stub();
  await post({ ev: 'start', id, wind: 'medium', laps: 1, length: 'short', boats: 5, yacht: 'ac75' });
  assert.equal(calls.find((c) => c.method === 'POST').body.yacht, 'ac75');
  calls = stub();
  await post({ ev: 'start', id, wind: 'medium', yacht: 'AC75; drop' });
  assert.ok(!('yacht' in calls.find((c) => c.method === 'POST').body));
  // the floor of one short lap in medium wind: 0.45 s a metre of 260 m, 117 s; an AC75's, 0.4 of it
  assert.equal(floorSecs({ wind: 'medium', length: 'short', laps: 1 }), 117);
  assert.equal(Math.round(floorSecs({ wind: 'medium', length: 'short', laps: 1, yacht: 'ac75' }) * 10) / 10, 46.8);
  assert.equal(floorSecs({ wind: 'medium', length: 'short', laps: 1, yacht: 'bavaria46' }), 117);
  // an F50's, as fast round her course as the AC75 round hers, the AC75's
  assert.equal(Math.round(floorSecs({ wind: 'medium', length: 'short', laps: 1, yacht: 'f50' }) * 10) / 10, 46.8);
  // a Laser's and a J/70's 0.8 of it, an RS21's 0.9: in a blow they sail as near their polars as in a breeze
  assert.equal(Math.round(floorSecs({ wind: 'medium', length: 'short', laps: 1, yacht: 'laser' }) * 10) / 10, 93.6);
  assert.equal(Math.round(floorSecs({ wind: 'medium', length: 'short', laps: 1, yacht: 'j70' }) * 10) / 10, 93.6);
  // an Optimist's, 0.6 of it: her course is sized to her
  assert.equal(Math.round(floorSecs({ wind: 'medium', length: 'short', laps: 1, yacht: 'optimist' }) * 10) / 10, 70.2);
  const started = (yacht) => [{ started_at: new Date(Date.now() - 600e3).toISOString(), wind: 'medium', length: 'short', laps: 1, boats: 5, yacht }];
  const patch = (calls) => calls.find((c) => c.method === 'PATCH').body;
  calls = stub({ rows: started('ac75') });
  await post({ ev: 'finish', id, place: 1, secs: 106, dsq: false });
  assert.equal(patch(calls).secs, 106, 'an AC75 lap under the 40-footer\'s floor is kept');
  calls = stub({ rows: started('optimist') });
  await post({ ev: 'finish', id, place: 1, secs: 106, dsq: false });
  assert.equal(patch(calls).secs, 106, 'an Optimist\'s short course under the 40-footer\'s floor is kept');
  calls = stub({ rows: started(null) });
  await post({ ev: 'finish', id, place: 1, secs: 106, dsq: false });
  assert.equal(patch(calls).secs, null, 'the same time in the 40-footer is not');
  // before the column is there, the start is read without it: the 40-footer's floor
  calls = stub({ rows: started(undefined), missing: 'yacht' });
  await post({ ev: 'finish', id, place: 1, secs: 300, dsq: false });
  assert.equal(patch(calls).secs, 300);
});

test('POST start keeps the venue; POST perf keeps how the game ran, once, each field checked, nothing before its column', async () => {
  const id = '66666666-6666-4666-8666-666666666666', post = (body) => POST(new Request('https://x.test/api/game', { method: 'POST', body: JSON.stringify(body), headers: { 'x-forwarded-for': `10.0.3.${Math.random() * 250 | 0}` } }));
  let calls = stub();
  await post({ ev: 'start', id, wind: 'light', venue: 'cowes' });
  assert.equal(calls.find((c) => c.method === 'POST').body.venue, 'cowes');
  calls = stub();
  await post({ ev: 'start', id, wind: 'light', venue: 'Cowes; drop' });
  assert.ok(!('venue' in calls.find((c) => c.method === 'POST').body));
  // the game's summary: kept as it is, on the race's row while it has none
  const perf = { fps: 58.8, low: 31.2, stall: 0.4, secs: 312, q0: 'high', q: 'medium', gfx: 'auto', saver: 0, rs: 0.65, dev: 'phone', tg: 1, os: 'ios', br: 'safari',
    dpr: 3, cores: 6, mem: 4, gpu: 'Apple GPU', w: 1170, h: 2532, load: 6.4 };
  calls = stub();
  assert.equal((await post({ ev: 'perf', id, perf })).status, 204);
  const patch = calls.find((c) => c.method === 'PATCH');
  assert.match(patch.url, /id=eq\.6+-.*&perf=is\.null/);
  assert.deepEqual(patch.body, { perf });
  // anything else dropped, out of bounds left out, and no frame rate is no perf at all
  assert.deepEqual(perfOf({ fps: 60, q: 'ultra', dev: 'fridge', gpu: 'NVIDIA <b>RTX</b> 4090', name: 'Anna', mem: -1, load: 1e9 }), { fps: 60, gpu: 'NVIDIA bRTX/b 4090' });
  assert.equal(perfOf({ low: 20 }), null);
  // the resolution below Low (rs: 1 none, 0.8 or 0.65): a share of a pixel, nothing else
  for (const rs of [1, 0.8, 0.65]) assert.equal(perfOf({ fps: 20, rs }).rs, rs);
  for (const rs of [0, 0.1, 1.5, '0.8', null]) assert.ok(!('rs' in perfOf({ fps: 20, rs })), String(rs));
  assert.deepEqual(perfOf({ fps: 30.3, busy: 21.254, busy95: 34.75, sim: 4.1, draw: 13.6 }), { fps: 30.3, busy: 21.25, busy95: 34.75, sim: 4.1, draw: 13.6 });
  assert.deepEqual(perfOf({ fps: 30.3, busy: -1, busy95: '9', sim: 1e6, draw: NaN }), { fps: 30.3 });
  for (const aa of [0, 1]) assert.equal(perfOf({ fps: 30.3, aa }).aa, aa);
  for (const aa of [2, '0', null, true]) assert.ok(!('aa' in perfOf({ fps: 30.3, aa })), String(aa));
  // the setting: Auto, a level (Lowest: Low drawn at two thirds of its resolution) or Custom
  for (const gfx of ['auto', 'high', 'medium', 'low', 'lowest', 'custom']) assert.equal(perfOf({ fps: 20, gfx }).gfx, gfx);
  assert.ok(!('gfx' in perfOf({ fps: 20, gfx: 'ultra' })));
  calls = stub();
  assert.equal((await post({ ev: 'perf', id, perf: { low: 20 } })).status, 400);
  assert.ok(!calls.some((c) => c.method === 'PATCH'));
  // before the column is there: nothing kept, nothing logged as an error
  calls = stub({ missing: 'perf' });
  assert.equal((await post({ ev: 'perf', id, perf })).status, 204);
  assert.ok(!calls.some((c) => c.url.includes('/rest/v1/errors')));
});

test('POST end, rate, open and visit: each checked, the race\'s kept once, a visit made and then filled in', async () => {
  const id = '77777777-7777-4777-8777-777777777777', vid = '88888888-8888-4888-8888-888888888888';
  const post = (body) => POST(new Request('https://x.test/api/game', { method: 'POST', body: JSON.stringify(body), headers: { 'x-forwarded-for': `10.0.4.${Math.random() * 250 | 0}` } }));
  // the start names the browser and the visit
  let calls = stub();
  await post({ ev: 'start', id, wind: 'light', vid, visit: vid });
  assert.deepEqual([calls.find((c) => c.method === 'POST').body.vid, calls.find((c) => c.method === 'POST').body.visit], [vid, vid]);
  // how it ended: once (ended=is.null), its incidents and settings kept, anything else dropped
  const end = { how: 'menu', leg: 1, legs: 3, clock: 95, place: 5, boats: 6, done: 0, inc: { ocs: 1, touched: 2 }, last: 'touched', ago: 12, pens: 1, mins: 2.4,
    use: { cam: 'drone', trim: 1, sound: 1, music: 'racing', speed: 2 } };
  calls = stub();
  assert.equal((await post({ ev: 'end', id, end: { ...end, name: 'Anna' } })).status, 204);
  const patch = calls.find((c) => c.method === 'PATCH');
  assert.match(patch.url, /ended=is\.null/); assert.deepEqual(patch.body, { ended: end });
  assert.equal(endOf({ how: 'quit' }), null);
  assert.deepEqual(endOf({ how: 'close', inc: { '<b>': 1, ocs: -1 }, use: { cam: '<script>' } }), { how: 'close', done: 0, inc: {}, use: {} });
  // the rating and the comment, each once; out of range or empty is refused
  calls = stub();
  await post({ ev: 'rate', id, rating: 4 });
  assert.deepEqual(calls.find((c) => c.method === 'PATCH').body, { rating: 4 }); assert.match(calls.find((c) => c.method === 'PATCH').url, /rating=is\.null/);
  calls = stub();
  await post({ ev: 'rate', id, comment: '  The start\u0000 was hard  ' });
  assert.deepEqual(calls.find((c) => c.method === 'PATCH').body, { comment: 'The start was hard' });
  for (const bad of [{ rating: 6 }, { rating: 0 }, { comment: '   ' }]) assert.equal((await post({ ev: 'rate', id, ...bad })).status, 400);
  // a visit: opened, then what it came to (stamped), errors kept within bounds
  calls = stub();
  await post({ ev: 'open', id: vid, open: { vid, ref: 'tg', kind: 'today', tg: 1, dev: 'phone', ua: 'x' } });
  assert.deepEqual(calls.find((c) => c.url.includes('game_visits')).body, { id: vid, vid, ref: 'tg', kind: 'today', tg: 1, dev: 'phone' });
  calls = stub();
  await post({ ev: 'visit', id: vid, visit: { stage: 'loaded', vid, races: 1, finished: 0, mins: 0.5, load: 6.2, errors: [{ m: 'TypeError: boom', src: 'world.js:9', n: 2 }] } });
  const v = calls.filter((c) => c.url.includes('game_visits'));
  assert.equal(v.length, 2); assert.equal(v[1].method, 'PATCH');
  assert.ok(v[1].body.loaded_at && v[1].body.last_at); assert.equal(v[1].body.load, 6.2); assert.deepEqual(v[1].body.errors, [{ m: 'TypeError: boom', src: 'world.js:9', n: 2 }]);
  assert.equal(visitOf({ stage: 'done' }), null); assert.equal(openOf(null), null);
  // no game_visits table yet: nothing kept, nothing logged
  calls = stub({ missing: 'game_visits' });
  assert.equal((await post({ ev: 'visit', id: vid, visit: { stage: 'left', races: 2 } })).status, 204);
  assert.ok(!calls.some((c) => c.url.includes('/rest/v1/errors')));
});

test('GET ?players: the somebodies, the most points first, a page at a time, named, with keys that are not ids', async () => {
  const rows = [
    race({ user_id: 7, place: 1, flag: 'gb', yacht: 'j70', started_at: at(0, 9) }), race({ user_id: 7, place: 3, yacht: 'j70', daily: null, started_at: at(1) }),
    race({ user_id: 7, finished_at: null, place: null, secs: null, started_at: at(2) }),
    race({ player: A, place: 4, boats: 8, secs: 210, started_at: at(0, 11) }), race({ player: A, place: 5, daily: null, started_at: at(4) }), race({ player: A, place: 6, daily: null, started_at: at(5) }), race({ player: A, dsq: true, place: null, started_at: at(3) }),
    race({ place: 1 }), race({ place: 2 }), race({ place: 1 }), race({ place: 1 }), // guests: not players
  ];
  stub({ rows, users: [{ id: 7, name: 'Anna Petrova' }], accounts: { [A]: { display_name: 'Fed', boat: { hull: '#112233', flag: 'by' } } } });
  const r = await GET(new Request('https://x.test/api/game?players'));
  assert.equal(r.status, 200);
  const j = await r.json();
  assert.deepEqual([j.total, j.page, j.pages, j.per], [2, 1, 1, 20]);
  assert.deepEqual(j.rows.map((x) => [x.name, x.fl, x.pts, x.n, x.fin, x.wins, x.podiums, x.days, x.yacht]),
    [['Anna Petrova', 'gb', 2, 3, 2, 1, 2, 3, 'j70'], ['Fed', 'by', 1, 4, 3, 0, 0, 4, 'jpk1050']], 'the most points first, though Fed sailed more races; each in the yacht they sailed last');
  assert.ok(!JSON.stringify(j).includes(A) && !/"7"|:7[,}]/.test(JSON.stringify(j)), 'no raw ids');
  const far = await (await GET(new Request('https://x.test/api/game?players&page=9'))).json();
  assert.equal(far.page, 1, 'a page past the last is the last');
});

test('a player\'s yacht is the one they sailed last, not the one they sailed most', () => {
  const rows = [race({ user_id: 7, yacht: 'j70', started_at: at(3) }), race({ user_id: 7, yacht: 'j70', started_at: at(2) }), race({ user_id: 7, yacht: 'ac75', started_at: at(0) }),
    race({ user_id: 7, yacht: 'j70', started_at: at(1) })];
  const [p] = playersOf(rows);
  assert.equal(p.yacht, 'ac75');
  assert.deepEqual(p.yachts[0], { id: 'j70', n: 3 }, 'the card still counts the most sailed first');
});

test('GET ?players: twenty a page', async () => {
  const rows = Array.from({ length: 45 }, (_, i) => race({ user_id: 100 + i, started_at: at(0, 1 + (i % 20)) }));
  stub({ rows, users: [] });
  const j = await (await GET(new Request('https://x.test/api/game?players&page=3'))).json();
  assert.deepEqual([j.total, j.page, j.pages, j.rows.length], [45, 3, 3, 5]);
});

test('GET ?player=: one player\'s card with their boat, checked; a key nobody has is not found', async () => {
  const calls = stub({
    rows: [race({ player: A, place: 2, boats: 6, venue: 'cowes', yacht: 'dragon' }), race({ player: A, place: 1, boats: 4, venue: 'cowes', daily: null }), race({ user_id: 7, place: 1, secs: 190 })],
    users: [{ id: 7, name: 'Anna' }], accounts: { [A]: 'Fed' },
  });
  const list = await (await GET(new Request('https://x.test/api/game?players'))).json();
  const fed = list.rows.find((x) => x.name === 'Fed');
  const real = globalThis.fetch;
  globalThis.fetch = async (url, init) => String(url).includes('/rpc/regatta_boat')
    ? Response.json({ hull: '#AABBCC', cloth: 'red', deck: 'teak', name: 'Sea <b>Wolf</b>', num: '12345', flag: 'it', logoImg: 'data:image/png;base64,xx', email: 'x@y.z' })
    : real(url, init);
  const r = await GET(new Request(`https://x.test/api/game?player=${fed.k}`));
  globalThis.fetch = real;
  assert.equal(r.status, 200);
  const j = await r.json();
  assert.deepEqual([j.name, j.n, j.fin, j.wins, j.podiums, j.best, j.fleet], ['Fed', 2, 2, 1, 2, 1, 4]);
  assert.deepEqual([j.pts, j.daily.n, j.daily.days, j.daily.wins, j.daily.podiums], [1, 1, 1, 0, 1], 'second of two on the day: a point, a podium');
  assert.deepEqual(list.rows.map((x) => [x.name, x.pts]), [['Anna', 2], ['Fed', 1]]);
  assert.deepEqual(j.yachts, [{ id: 'dragon', n: 1 }, { id: 'jpk1050', n: 1 }]);
  assert.deepEqual(j.venues, [{ id: 'cowes', n: 2 }]);
  assert.deepEqual(j.boat, { hull: '#aabbcc', deck: 'teak', name: 'Sea bWolf/b', num: '1234', flag: 'it' });
  assert.ok(calls.length);
  assert.equal((await GET(new Request('https://x.test/api/game?player=nobodyAtAll'))).status, 404);
  assert.equal((await GET(new Request('https://x.test/api/game?player=%3Cx%3E'))).status, 404);
});

test('GET ?me: the key of the player whose token it is, the one /players has; none for a guest or a new account', async () => {
  const C = '33333333-3333-4333-8333-333333333333';
  stub({
    rows: [race({ player: A }), race({ user_id: 7, secs: 190 })], users: [{ id: 7, name: 'Anna' }], accounts: { [A]: 'Fed' },
    tokens: { site: { id: A, app_metadata: { provider: 'google' } }, tg: { id: B, app_metadata: { telegram_id: 7 } }, fresh: { id: C, app_metadata: {} } },
  });
  const list = await (await GET(new Request('https://x.test/api/game?players'))).json();
  const keyOf = (name) => list.rows.find((x) => x.name === name).k;
  const ask = (token) => GET(new Request('https://x.test/api/game?me', token == null ? {} : { headers: { authorization: `Bearer ${token}` } }));
  const site = await ask('site');
  assert.equal(site.status, 200);
  assert.match(site.headers.get('cache-control'), /no-store/);
  assert.deepEqual(await site.json(), { k: keyOf('Fed') });
  assert.deepEqual(await (await ask('tg')).json(), { k: keyOf('Anna') }, 'a Telegram account: the key of their Telegram id');
  assert.equal((await ask('fresh')).status, 404, 'signed in, never raced: not a player');
  assert.equal((await ask('forged')).status, 401);
  assert.equal((await ask(null)).status, 401);
  assert.equal((await GET(new Request(`https://x.test/api/game?me&player=${A}`))).status, 401, 'no way round the token');
});

test('the players added up by the database rank as the ones read race by race', () => {
  const rows = [race({ user_id: 7, place: 1, secs: 190, boats: 6, flag: 'gb', yacht: 'j70', venue: 'cowes' }), race({ player: A, place: 2, secs: 200, boats: 6 }),
    race({ user_id: 7, place: 3, daily: null, boats: 4, started_at: at(2) }), race({ player: A, dsq: true, place: null, daily: null, started_at: at(3) })];
  const sum = { players: [
    { u: 7, a: null, n: 2, fin: 2, wins: 1, podiums: 2, dsq: 0, days: 2, first: at(2), last: at(0), yacht: 'j70', best: 1, fleet: 6, dn: 1, flag: 'gb', yachts: { j70: 1, jpk1050: 1 }, venues: { cowes: 1 } },
    { u: null, a: A, n: 2, fin: 1, wins: 0, podiums: 1, dsq: 1, days: 2, first: at(3), last: at(0), yacht: 'jpk1050', best: 2, fleet: 6, dn: 1, flag: null, yachts: { jpk1050: 2 }, venues: {} },
  ], days: [{ d: day(0), u: 7, a: null, s: 190, p: 1, n: 1 }, { d: day(0), u: null, a: A, s: 200, p: 2, n: 1 }] };
  assert.deepEqual(playersFrom(sum), playersOf(rows));
});

test('a site account\'s name and flag come in one question once the function is there', async () => {
  const calls = stub({ rows: [race({ player: A, place: 1 }), race({ player: B, place: 2, secs: 210 })] });
  const real = globalThis.fetch;
  globalThis.fetch = async (url, init) => (String(url).includes('/rpc/regatta_names')
    ? (calls.push({ url: String(url) }), Response.json([{ id: A, display_name: 'Fed', boat: { flag: 'by' } }, { id: B, display_name: 'Ann', boat: null }])) : real(url, init));
  const j = await (await GET(new Request(`https://x.test/api/game?day=${day(0)}`))).json();
  globalThis.fetch = real;
  assert.deepEqual(j.rows.map((x) => [x.name, x.fl]), [['Fed', 'by'], ['Ann', null]]);
  assert.ok(!calls.some((c) => c.url.includes('/auth/v1/admin/users/')), 'no account asked for by itself');
});

test('POST start: a daily race is that day\'s only in that day\'s yacht (a page left open past midnight sails the day before\'s)', async () => {
  // the days so far, as the game's classes.js dailyYacht names them
  assert.deepEqual(['2026-11-15', '2026-11-16', '2026-11-17', '2026-11-18', '2026-11-19', '2026-11-20'].map(dailyYacht), ['jpk1050', 'laser', 'optimist', 'rs21', 'ac75', 'dragon']);
  // …and the days to come: the J Class's first on the 22nd; the F50 joins on the 23rd and first sails on the 28th
  assert.deepEqual(['2026-11-21', '2026-11-22', '2026-11-23', '2026-11-28'].map(dailyYacht), ['bavaria46', 'jclass', 'laser', 'f50']);
  const id = '66666666-6666-4666-8666-666666666666', post = (body) => POST(new Request('https://x.test/api/game', { method: 'POST', body: JSON.stringify(body), headers: { 'x-forwarded-for': `10.0.3.${Math.random() * 250 | 0}` } }));
  const today = new Date().toISOString().slice(0, 10), y = dailyYacht(today), other = y === 'ac75' ? 'dragon' : 'ac75';
  let calls = stub();
  await post({ ev: 'start', id, wind: 'light', laps: 1, length: 'short', boats: 5, daily: today, ...(y !== 'jpk1050' && { yacht: y }) });
  assert.equal(calls.find((c) => c.method === 'POST').body.daily, today, 'in the day\'s yacht: the day\'s race');
  calls = stub();
  await post({ ev: 'start', id, wind: 'light', laps: 1, length: 'short', boats: 5, daily: today, yacht: other });
  const body = calls.find((c) => c.method === 'POST').body;
  assert.ok(!('daily' in body), 'in another: a race of no day'); assert.equal(body.yacht, other);
});

test('GET ?month=&k=: one player\'s month day by day, adding up to their points on the month\'s table', async () => {
  const m = day(0).slice(0, 7), ds = [2, 1, 0].map(day).filter((d) => d.startsWith(m));
  const on = (d, o) => race({ daily: d, started_at: `${d}T10:00:00Z`, finished_at: `${d}T10:00:00Z`, ...o });
  // each day: Anna (7) and Fed (A) and Bo (B) and a guest; Anna wins the first day, Fed the others
  const rows = ds.flatMap((d, i) => [on(d, { user_id: 7, secs: i ? 190 : 170 }), on(d, { player: A, secs: 180 }), on(d, { player: B, secs: 200 + i }), on(d, { secs: 100 })]);
  stub({ rows, users: [{ id: 7, name: 'Anna Petrova' }], accounts: { [A]: 'Fed', [B]: 'Bo' } });
  const board = await (await GET(new Request(`https://x.test/api/game?day=${day(0)}`))).json();
  const fed = board.month.rows.find((x) => x.name === 'Fed'), bo = board.month.rows.find((x) => x.name === 'Bo');
  const calls = stub({ rows, users: [{ id: 7, name: 'Anna Petrova' }], accounts: { [A]: 'Fed', [B]: 'Bo' } });
  const r = await GET(new Request(`https://x.test/api/game?month=${m}&k=${fed.k}`));
  assert.equal(r.status, 200); assert.match(r.headers.get('cache-control'), /s-maxage=300/, 'this month: five minutes');
  const j = await r.json();
  assert.equal(j.m, m); assert.equal(j.k, fed.k); assert.equal(j.sailed, ds.length); assert.equal(j.of, 3);
  assert.deepEqual(j.days.map((x) => x.d), ds, 'the days they ranked on, the earliest first');
  assert.ok(j.days.every((x) => x.of === 3 && x.pts === x.of - x.place + 1), 'each day: ranked less place plus one');
  assert.equal(j.days.reduce((a, x) => a + x.pts, 0), j.pts, 'the days add up');
  assert.equal(j.pts, fed.pts, "to the board's points");
  assert.equal(j.days[0].place, 2, "second to Anna on the first day"); assert.equal(j.days[0].s, 180);
  assert.deepEqual(j.near.map((x) => x.name), board.month.rows.map((x) => x.name), 'the rows around them, named, in the board\'s order');
  assert.ok(j.near.find((x) => x.me).k === fed.k && j.near.filter((x) => x.me).length === 1);
  assert.ok(!JSON.stringify(j).includes(A), 'no raw ids');
  if (ds.length > 1) { assert.equal(j.place, 1); assert.equal(j.above, null); }
  // Bo: last every day, a point a day, and the place ahead of theirs
  const b = await (await GET(new Request(`https://x.test/api/game?month=${m}&k=${bo.k}`))).json();
  assert.equal(b.pts, ds.length); assert.equal(b.place, 3); assert.deepEqual(b.days.map((x) => x.place), ds.map(() => 3));
  assert.deepEqual(b.above, { place: 2, pts: board.month.rows[1].pts });
  const q = calls.find((c) => c.url.includes('game_races')).url;
  assert.match(q, new RegExp(`daily=gte\\.${m}-01&daily=lte\\.${day(0)}&finished_at`));
  // a key not on the table: no days, and nothing said about whose it might be
  const x = await (await GET(new Request(`https://x.test/api/game?month=${m}&k=abcdefghijklmnop`))).json();
  assert.deepEqual([x.pts, x.place, x.days, x.near, x.of], [0, null, [], [], 3]);
  // a month gone by is cached long; the future, a non-month, the far past and a key not shaped as one are not found
  const prev = new Date(Date.UTC(+m.slice(0, 4), +m.slice(5, 7) - 2, 1)).toISOString().slice(0, 7);
  assert.match((await GET(new Request(`https://x.test/api/game?month=${prev}&k=${fed.k}`))).headers.get('cache-control'), /s-maxage=86400/);
  const next = new Date(Date.UTC(+m.slice(0, 4), +m.slice(5, 7), 1)).toISOString().slice(0, 7);
  for (const [mm, kk] of [[next, fed.k], ['2026-13', fed.k], ['2024-01', fed.k], [m, 'short'], [m, 'a b c d e f g h']]) {
    assert.equal((await GET(new Request(`https://x.test/api/game?month=${mm}&k=${encodeURIComponent(kk)}`))).status, 404, `${mm} ${kk}`);
  }
});

test('GET ?player=: the card carries the achievements the database works out for that account, each checked', async () => {
  const calls = stub({ rows: [race({ player: A, place: 1, boats: 4, venue: 'cowes' })], accounts: { [A]: 'Fed' } });
  const list = await (await GET(new Request('https://x.test/api/game?players'))).json();
  const fed = list.rows.find((x) => x.name === 'Fed');
  const real = globalThis.fetch, asked = [];
  globalThis.fetch = async (url, init) => {
    if (String(url).includes('/rpc/regatta_achievements_of')) {
      asked.push(JSON.parse(init.body));
      return Response.json([
        { key: 'first_race', at: '2026-11-14T10:00:00Z', detail: {} },
        { key: 'giant', at: '2026-11-19T19:30:00Z', detail: { them: 'Tomás R.', rating: 1752, gap: 214, email: 'x'.repeat(60), 'Bad Key': 1, obj: { a: 1 } } },
        { key: 'BAD KEY', at: '2026-11-19T19:30:00Z' }, { key: 'week', at: 'never' }, null,
      ]);
    }
    return real(url, init);
  };
  const j = await (await GET(new Request(`https://x.test/api/game?player=${fed.k}`))).json();
  globalThis.fetch = real;
  assert.deepEqual(asked, [{ acct: A }]);
  assert.deepEqual(j.achievements, [
    { key: 'first_race', at: '2026-11-14T10:00:00Z', detail: {} },
    { key: 'giant', at: '2026-11-19T19:30:00Z', detail: { them: 'Tomás R.', rating: 1752, gap: 214 } },
  ]);
  assert.ok(calls.length);
  // before the migration (the database says 404): none, and the card all the same
  stub({ rows: [race({ player: A, place: 1, boats: 4, venue: 'cowes' })], accounts: { [A]: 'Fed' } });
  const k = await (await GET(new Request(`https://x.test/api/game?player=${fed.k}`))).json();
  assert.deepEqual(k.achievements, []); assert.equal(k.name, 'Fed');
});

test('elosFrom: each player their 1-on-1 rating, by Telegram id or account, none without a rated race', () => {
  const list = [
    { tg: 77, acct: '00000000-0000-4000-8000-000000000001', rating: 1532, races: 2 },
    { tg: null, acct: '00000000-0000-4000-8000-000000000002', rating: 1618, races: 9 },
    { tg: null, acct: '00000000-0000-4000-8000-000000000003', rating: 1500, races: 0 },
    { tg: null, acct: '00000000-0000-4000-8000-000000000004', rating: '1500', races: 3 },
  ];
  const players = [
    { key: 77, u: 77, a: null },
    { key: 'a:00000000-0000-4000-8000-000000000002', u: null, a: '00000000-0000-4000-8000-000000000002' },
    { key: 'a:00000000-0000-4000-8000-000000000003', u: null, a: '00000000-0000-4000-8000-000000000003' },
    { key: 'a:00000000-0000-4000-8000-000000000004', u: null, a: '00000000-0000-4000-8000-000000000004' },
    { key: 99, u: 99, a: null },
  ];
  assert.deepEqual([...elosFrom(list, players)], [[77, { r: 1532, n: 2 }], ['a:00000000-0000-4000-8000-000000000002', { r: 1618, n: 9 }]]);
  assert.deepEqual([...elosFrom(null, players)], []);
});
