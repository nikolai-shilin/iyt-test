// api/progress.mjs's sync against a database played by a stub of fetch: the admins' cleared flags looked up while the
// state is kept, and the ones done deleted only once it is. Run: npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';

process.env.SUPABASE_URL = 'https://db.test';
process.env.SUPABASE_SECRET_KEY = 'sb_secret_test';
process.env.TELEGRAM_BOT_TOKEN = '1:test';
const { POST } = await import('../api/progress.mjs');

function initData(user) {
  const p = new URLSearchParams({ auth_date: String(Math.floor(Date.now() / 1000)), user: JSON.stringify(user) });
  const check = [...p.entries()].sort(([a], [b]) => (a < b ? -1 : 1)).map(([k, v]) => `${k}=${v}`).join('\n');
  const secret = createHmac('sha256', 'WebAppData').update(process.env.TELEGRAM_BOT_TOKEN).digest();
  p.set('hash', createHmac('sha256', secret).update(check).digest('hex'));
  return p.toString();
}
const sync = (body) => POST(new Request('https://x.test/api/progress', { method: 'POST', body: JSON.stringify(body), headers: { 'x-telegram-init-data': initData({ id: 7, first_name: 'Anna' }) } }));

// clears: the flag_clears rows; ok: whether sync_progress keeps the state. The sync's answer waits for the clears'
// question (or a timeout), so overlapped says whether they were asked at once.
function stub({ clears = [], ok = true } = {}) {
  const calls = [], seen = { overlapped: false };
  let asked = null;
  const clearsAsked = new Promise((r) => { asked = r; });
  globalThis.fetch = async (url, init = {}) => {
    const u = String(url), method = init.method || 'GET';
    calls.push({ u, method });
    if (u.includes('/rpc/sync_progress')) {
      seen.overlapped = await Promise.race([clearsAsked.then(() => true), new Promise((r) => setTimeout(() => r(false), 500))]);
      return ok ? Response.json({ ts: 5, state: null, answers: 1 }) : new Response('boom', { status: 500 });
    }
    if (u.includes('/rest/v1/flag_clears')) {
      if (method === 'GET') { asked(); return Response.json(clears); }
      return Response.json([]);
    }
    return Response.json([]); // errors
  };
  return { calls, seen };
}

test('a sync: the cleared flags are looked up while the state is kept; the done ones deleted, the rest sent back', async () => {
  const { calls, seen } = stub({ clears: [{ question_id: 'bs-012', kind: 'flags' }, { question_id: 'bs-034', kind: 'wrong' }] });
  const r = await sync({ state: { ts: 4, flags: ['bs-012'], wrong: [] }, answers: [] });
  assert.equal(r.status, 200);
  const j = await r.json();
  assert.equal(j.ts, 5); assert.deepEqual(j.clear, [{ q: 'bs-012', k: 'flags' }], 'still held: sent back');
  assert.ok(seen.overlapped, 'flag_clears asked while sync_progress was');
  const del = calls.filter((c) => c.method === 'DELETE');
  assert.equal(del.length, 1); assert.match(del[0].u, /question_id=eq\.bs-034&kind=eq\.wrong/);
});

test('a sync that fails deletes nothing', async () => {
  const { calls } = stub({ clears: [{ question_id: 'bs-034', kind: 'wrong' }], ok: false });
  const r = await sync({ state: { ts: 4, flags: [], wrong: [] } });
  assert.equal(r.status, 500);
  await new Promise((r) => setTimeout(r, 20));
  assert.ok(!calls.some((c) => c.method === 'DELETE'), 'no flag_clears row deleted');
});

test('a read (no state) returns every cleared flag and deletes none', async () => {
  const { calls } = stub({ clears: [{ question_id: 'bs-034', kind: 'wrong' }] });
  const j = await (await sync({})).json();
  assert.deepEqual(j.clear, [{ q: 'bs-034', k: 'wrong' }]);
  assert.ok(!calls.some((c) => c.method === 'DELETE'));
});
