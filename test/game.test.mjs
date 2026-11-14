// api/game.mjs's rankings: the points of a daily race, the month's table, and the answers of GET ?day= and the POST of
// a start with the boat's flag, against a database played by a stub of fetch. Run: npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';

process.env.SUPABASE_URL = 'https://db.test';
process.env.SUPABASE_SECRET_KEY = 'sb_secret_test';
process.env.TELEGRAM_BOT_TOKEN = '1:test';
const { GET, POST, bests, rankDay, monthTable } = await import('../api/game.mjs');

const day = (d) => new Date(Date.now() - d * 864e5).toISOString().slice(0, 10);
const at = (d, h = 10) => `${day(d)}T${String(h).padStart(2, '0')}:00:00Z`;
// a finished daily race
const race = (o) => ({ started_at: at(0), finished_at: at(0), user_id: null, player: null, wind: 'medium', secs: 200, dsq: false, place: 1, daily: day(0), flag: null, ...o });

// The database: game_races gives back rows (whatever the filter, the URL is kept), users the Telegram names, Auth
// a site account's display name. missing: a column the table doesn't have yet. recent: what the read of the ranked
// players' latest races (for their flags, an or= filter) gets, rows when not given.
function stub({ rows = [], recent = null, users = [], accounts = {}, missing = null } = {}) {
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    const u = String(url); calls.push({ url: u, method: init.method || 'GET', body: init.body && JSON.parse(init.body) });
    const fail = (col) => new Response(JSON.stringify({ message: `column game_races.${col} does not exist` }), { status: 400 });
    if (u.includes('/rest/v1/game_races')) {
      if (missing && (init.method === 'POST' ? init.body.includes(`"${missing}"`) : u.includes(missing))) return fail(missing);
      if (init.method === 'POST' || init.method === 'PATCH') return Response.json([]);
      const off = Number(/offset=(\d+)/.exec(u)?.[1] || 0);
      return Response.json(off ? [] : recent && u.includes('or=(') ? recent : rows);
    }
    if (u.includes('/rest/v1/users')) return Response.json(users);
    if (u.includes('/rest/v1/errors')) return Response.json([]);
    const acc = /admin\/users\/([0-9a-f-]+)/.exec(u);
    if (acc) return accounts[acc[1]] ? Response.json({ user_metadata: { display_name: accounts[acc[1]] } }) : new Response('', { status: 404 });
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
    users: [{ id: 7, name: 'Anna Petrova' }], accounts: { [A]: 'Fed' },
  });
  const r = await GET(new Request(`https://x.test/api/game?day=${day(0)}`));
  assert.equal(r.status, 200);
  assert.match(r.headers.get('cache-control'), /s-maxage=300/, "today's: the card's five minutes");
  const j = await r.json();
  assert.equal(j.d, day(0)); assert.equal(j.races, 4); assert.equal(j.guests, 1); assert.equal(j.w, 'medium');
  assert.deepEqual(j.rows.map((x) => [x.name, x.fl, x.s, x.p, x.pts, x.n]), [['Anna P.', 'it', 175, 1, 2, 2], ['Fed', 'gb-sct', 190, 1, 1, 1]]);
  assert.ok(j.rows[0].ph && j.rows[0].k === j.rows[0].ph, 'a Telegram player: the picture key is their key');
  assert.equal(j.rows[1].ph, null); assert.match(j.rows[1].k, /^[A-Za-z0-9_-]{16}$/);
  assert.ok(!JSON.stringify(j).includes(A) && !/"7"|:7[,}]/.test(JSON.stringify(j)), 'no raw ids');
  assert.equal(j.month.m, day(0).slice(0, 7));
  if (j.days.length === 2) {
    assert.deepEqual(j.days, [day(0), day(1)]);
    assert.deepEqual(j.month.rows.map((x) => [x.name, x.pts, x.days, x.wins, x.podiums]), [['Anna P.', 3, 2, 1, 2], ['Fed', 3, 2, 1, 2]]);
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
  assert.match(decodeURIComponent(q), new RegExp(`or=\\(user_id\\.in\\.\\(7,8\\),player\\.in\\.\\(${A}\\)\\)`), "only the rating's players");
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
