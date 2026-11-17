// api/game.mjs's rankings: the points of a daily race, the month's table, and the answers of GET ?day= and the POST of
// a start with the boat's flag, against a database played by a stub of fetch. Run: npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';

process.env.SUPABASE_URL = 'https://db.test';
process.env.SUPABASE_SECRET_KEY = 'sb_secret_test';
process.env.TELEGRAM_BOT_TOKEN = '1:test';
const { GET, POST, bests, rankDay, monthTable, accountFlag, floorSecs, perfOf, endOf, visitOf, openOf } = await import('../api/game.mjs');

const day = (d) => new Date(Date.now() - d * 864e5).toISOString().slice(0, 10);
const at = (d, h = 10) => `${day(d)}T${String(h).padStart(2, '0')}:00:00Z`;
// a finished daily race
const race = (o) => ({ started_at: at(0), finished_at: at(0), user_id: null, player: null, wind: 'medium', secs: 200, dsq: false, place: 1, daily: day(0), flag: null, ...o });

// The database: game_races gives back rows (whatever the filter, the URL is kept), users the Telegram names, Auth
// a site account's display name. missing: a column the table doesn't have yet. recent: what the read of the ranked
// players' latest races (for their flags: every race of the last 30 days, no daily= filter) gets, rows when not given.
function stub({ rows = [], recent = null, users = [], accounts = {}, missing = null } = {}) {
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    const u = String(url); calls.push({ url: u, method: init.method || 'GET', body: init.body && JSON.parse(init.body) });
    const fail = (col) => new Response(JSON.stringify({ message: `column game_races.${col} does not exist` }), { status: 400 });
    if (u.includes('/rest/v1/game_races')) {
      if (missing && (init.method === 'POST' ? init.body.includes(`"${missing}"`) : u.includes(missing))) return fail(missing);
      if (init.method === 'POST' || init.method === 'PATCH') return Response.json([]);
      const off = Number(/offset=(\d+)/.exec(u)?.[1] || 0);
      return Response.json(off ? [] : recent && !u.includes('daily=') ? recent : rows);
    }
    if (u.includes('/rest/v1/game_visits')) {
      if (missing === 'game_visits') return new Response(JSON.stringify({ message: 'relation "public.game_visits" does not exist' }), { status: 404 });
      return Response.json([]);
    }
    if (u.includes('/rest/v1/users')) return Response.json(users);
    if (u.includes('/rest/v1/errors')) return Response.json([]);
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
  // a Laser's 0.8 of it, a J/70's and an RS21's 0.9: in a blow they sail as near their polars as in a breeze
  assert.equal(Math.round(floorSecs({ wind: 'medium', length: 'short', laps: 1, yacht: 'laser' }) * 10) / 10, 93.6);
  assert.equal(Math.round(floorSecs({ wind: 'medium', length: 'short', laps: 1, yacht: 'j70' }) * 10) / 10, 105.3);
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
  const perf = { fps: 58.8, low: 31.2, stall: 0.4, secs: 312, q0: 'high', q: 'medium', gfx: 'auto', saver: 0, dev: 'phone', tg: 1, os: 'ios', br: 'safari',
    dpr: 3, cores: 6, mem: 4, gpu: 'Apple GPU', w: 1170, h: 2532, load: 6.4 };
  calls = stub();
  assert.equal((await post({ ev: 'perf', id, perf })).status, 204);
  const patch = calls.find((c) => c.method === 'PATCH');
  assert.match(patch.url, /id=eq\.6+-.*&perf=is\.null/);
  assert.deepEqual(patch.body, { perf });
  // anything else dropped, out of bounds left out, and no frame rate is no perf at all
  assert.deepEqual(perfOf({ fps: 60, q: 'ultra', dev: 'fridge', gpu: 'NVIDIA <b>RTX</b> 4090', name: 'Anna', mem: -1, load: 1e9 }), { fps: 60, gpu: 'NVIDIA bRTX/b 4090' });
  assert.equal(perfOf({ low: 20 }), null);
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
