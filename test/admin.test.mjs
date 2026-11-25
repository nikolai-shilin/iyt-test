// api/admin.mjs's GET against a database played by a stub of fetch: the races and the chart's numbers each in one
// question when the database has the functions, the old reads before their migrations. Run: npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';

process.env.SUPABASE_URL = 'https://db.test';
process.env.SUPABASE_SECRET_KEY = 'sb_secret_test';
process.env.TELEGRAM_BOT_TOKEN = '1:test';
process.env.ADMIN_USERNAMES = 'tester';
const { GET } = await import('../api/admin.mjs');

// launch data signed with the test bot token, as Telegram signs it
function initData(user) {
  const p = new URLSearchParams({ auth_date: String(Math.floor(Date.now() / 1000)), user: JSON.stringify(user) });
  const check = [...p.entries()].sort(([a], [b]) => (a < b ? -1 : 1)).map(([k, v]) => `${k}=${v}`).join('\n');
  const secret = createHmac('sha256', 'WebAppData').update(process.env.TELEGRAM_BOT_TOKEN).digest();
  p.set('hash', createHmac('sha256', secret).update(check).digest('hex'));
  return p.toString();
}
const admin = () => new Request('https://x.test/api/admin', { headers: { 'x-telegram-init-data': initData({ id: 1, username: 'tester' }) } });

const t0 = Date.parse('2026-11-25T10:00:00.123Z');
const rows = [
  { started_at: '2026-11-25T10:00:00.123456+00:00', finished_at: '2026-11-25T10:05:00.5+00:00', user_id: 7, wind: 'medium', laps: 2, length: 'short', place: 1, boats: 6, secs: 300.5, dsq: false, shape: 'tri' },
  { started_at: '2026-11-25T09:00:00+00:00', finished_at: null, user_id: null, wind: 'light', laps: 1, length: null, place: null, boats: 4, secs: null, dsq: false, shape: null },
];
const records = [
  { at: t0, u: 7, w: 'medium', l: 2, c: 'short', f: Date.parse('2026-11-25T10:05:00.5Z'), p: 1, n: 6, s: 300.5, d: false, sh: 'tri' },
  { at: Date.parse('2026-11-25T09:00:00Z'), u: null, w: 'light', l: 1, c: null, f: 0, p: null, n: 4, s: null, d: false, sh: 'wl' },
];

// fns: whether the database has regatta_admin_races and admin_series. hold: a path whose answer waits for another's question.
function stub({ fns = true, hold = null } = {}) {
  const calls = [];
  let release = null;
  const asked = new Promise((r) => { release = r; });
  globalThis.fetch = async (url, init = {}) => {
    const u = String(url);
    calls.push(u);
    if (hold && u.includes(hold.ask)) release();
    if (hold && u.includes(hold.wait)) hold.overlapped = await Promise.race([asked.then(() => true), new Promise((r) => setTimeout(() => r(false), 500))]);
    if (u.includes('/rpc/regatta_admin_races')) return fns ? Response.json(records) : new Response('{}', { status: 404 });
    if (u.includes('/rpc/admin_series')) {
      if (!fns) return new Response('{}', { status: 404 });
      const unit = JSON.parse(init.body).p_unit, now = new Date();
      if (unit === 'hour') now.setUTCMinutes(0, 0, 0); else now.setUTCHours(0, 0, 0, 0);
      return Response.json([{ at: now.toISOString(), joined: 2, answers: 9, wrong: 3 }]);
    }
    if (u.includes('/rest/v1/game_races')) return Response.json(Number(/offset=(\d+)/.exec(u)?.[1] || 0) ? [] : rows);
    if (u.includes('/rest/v1/users')) return Response.json([{ id: 7, name: 'Anna', created_at: '2026-11-20T00:00:00Z', updated_at: '2026-11-25T00:00:00Z' }]);
    if (u.includes('/rest/v1/answers')) return Response.json([]);
    if (u.includes('/rest/v1/errors')) return Response.json([]);
    return Response.json([]); // progress, flag_clears
  };
  return calls;
}

test('GET: the races in one question, as the short records the app counts, and none of the pages', async () => {
  const calls = stub();
  const j = await (await GET(admin())).json();
  assert.deepEqual(j.game, records);
  assert.equal(calls.filter((u) => u.includes('regatta_admin_races')).length, 1);
  assert.ok(!calls.some((u) => u.includes('/rest/v1/game_races')), 'no page of races read');
  assert.equal(j.series.day.at(-1).answers, 9); assert.equal(j.series.hour.at(-1).joined, 2);
  assert.equal(j.series.day.reduce((a, b) => a + b.races, 0), 2, 'the chart counts the races');
});

test('GET: before the races function, the same records from the pages', async () => {
  stub({ fns: false });
  const j = await (await GET(admin())).json();
  assert.deepEqual(j.game, records);
  assert.equal(j.series.day.at(-1).joined + j.series.day.at(-6).joined, 1, 'joins counted from the users before admin_series');
});

test('GET: the chart\'s numbers are asked at the same time as the students', async () => {
  const hold = { ask: '/rpc/admin_series', wait: '/rest/v1/users' };
  stub({ hold });
  const j = await (await GET(admin())).json();
  assert.ok(hold.overlapped, 'admin_series asked while the users were');
  assert.equal(j.users.length, 1);
});

test('GET: not an admin, refused', async () => {
  stub();
  const r = await GET(new Request('https://x.test/api/admin', { headers: { 'x-telegram-init-data': initData({ id: 2, username: 'someone' }) } }));
  assert.equal(r.status, 403);
});
