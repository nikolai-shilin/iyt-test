// The Regatta site's message to a sailor through the bot (api/regatta-notify.mjs): only with the shared secret, only a
// short text and a button to a page of the site, sent as plain text with a web_app button; a blocked user marked and
// answered 410. Run: node --test test/regatta-notify.test.mjs
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { POST, readNotice } from '../api/regatta-notify.mjs';

const OK = { telegram_id: 990000001, text: 'Match found: Bea K.\n1585 · Fleet. Tap within 60 s to say Ready.', button: { text: 'Open Match found', url: 'https://www.sailupdown.com/duel?resume' } };
const req = (body, auth = 'Bearer s3cret') => new Request('https://iyt.example/api/regatta-notify', { method: 'POST', headers: { 'content-type': 'application/json', ...(auth && { authorization: auth }) }, body: JSON.stringify(body) });
beforeEach(() => { process.env.REGATTA_NOTIFY_SECRET = 's3cret'; });

test('the message as asked: a Telegram id, a short text, a button to a page of the site; anything else is nothing', () => {
  assert.deepEqual(readNotice(OK), { id: 990000001, text: OK.text, label: 'Open Match found', url: 'https://www.sailupdown.com/duel?resume' });
  for (const bad of [null, {}, { ...OK, telegram_id: 'x' }, { ...OK, telegram_id: -5 }, { ...OK, text: '' }, { ...OK, text: 'x'.repeat(1001) },
    { ...OK, button: { text: 'Go', url: 'https://evil.example/duel' } }, { ...OK, button: { text: 'Go', url: 'javascript:alert(1)' } }, { ...OK, button: { text: '', url: OK.button.url } }, { ...OK, button: null }])
    assert.equal(readNotice(bad), null, JSON.stringify(bad));
});

test('sent with the secret: the text as it is and one web_app button to the page', async () => {
  const sent = [];
  const r = await POST(req(OK), { send: async (n) => { sent.push(n); }, mark: async () => { throw new Error('not to be marked'); } });
  assert.equal(r.status, 200); assert.deepEqual(await r.json(), { sent: true });
  assert.deepEqual(sent, [{ id: 990000001, text: OK.text, label: 'Open Match found', url: 'https://www.sailupdown.com/duel?resume' }]);
});

test('without the secret, or a wrong one, or with no secret set here: refused, nothing sent', async () => {
  const send = async () => { throw new Error('not to be sent'); };
  assert.equal((await POST(req(OK, null), { send })).status, 403);
  assert.equal((await POST(req(OK, 'Bearer nope'), { send })).status, 403);
  delete process.env.REGATTA_NOTIFY_SECRET;
  assert.equal((await POST(req(OK, 'Bearer '), { send })).status, 403);
});

test('a bad message is 400; a user who blocked the bot is marked and answered 410; another failure 502', async () => {
  assert.equal((await POST(req({ ...OK, button: { text: 'x', url: 'https://evil.example/' } }), { send: async () => {} })).status, 400);
  const marked = [];
  const blocked = await POST(req(OK), { send: async () => { throw Object.assign(new Error('Forbidden: bot was blocked by the user'), { code: 403 }); }, mark: async (id) => { marked.push(id); } });
  assert.equal(blocked.status, 410); assert.deepEqual(marked, [990000001]);
  const failed = await POST(req(OK), { send: async () => { throw new Error('Too Many Requests'); }, mark: async () => { throw new Error('not to be marked'); } });
  assert.equal(failed.status, 502);
});
