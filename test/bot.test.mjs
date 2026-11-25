// bot/core.mjs's replies against Telegram and a database played by a stub of fetch: who wrote is saved while the reply
// goes, /settings waits for their row, and the daily-question switch is one write. Run: npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';

process.env.TELEGRAM_BOT_TOKEN = '1:test';
process.env.SUPABASE_URL = 'https://db.test';
process.env.SUPABASE_SECRET_KEY = 'sb_secret_test';
process.env.WEBAPP_URL = 'https://app.test';
const { handleUpdate } = await import('../bot/core.mjs');

const from = { id: 7, first_name: 'Anna', language_code: 'en' }, chat = { id: 7, type: 'private' };
// row: what the users upsert gives back (or fail: it fails). hold: a call whose answer waits for another's (overlapped).
function stub({ row = { id: 7, daily_question: true }, fail = false, hold = null } = {}) {
  const calls = [];
  let release = null;
  const asked = new Promise((r) => { release = r; });
  globalThis.fetch = async (url, init = {}) => {
    const u = String(url), body = init.body ? JSON.parse(init.body) : null;
    calls.push({ u, method: init.method || 'GET', body });
    if (hold && u.includes(hold.ask)) release();
    if (hold && u.includes(hold.wait)) hold.overlapped = await Promise.race([asked.then(() => true), new Promise((r) => setTimeout(() => r(false), 500))]);
    if (u.startsWith('https://api.telegram.org/')) return Response.json({ ok: true, result: { message_id: 1 } });
    if (u.includes('/rest/v1/users')) return fail ? new Response('boom', { status: 500 }) : Response.json([{ ...row, ...(body && 'daily_question' in body && { daily_question: body.daily_question }) }]);
    return Response.json([]); // progress
  };
  return calls;
}
const tg = (calls, method) => calls.filter((c) => c.u.endsWith(`/${method}`));

test('a command is answered while who wrote is saved, and both are done before it returns', async () => {
  const hold = { ask: '/sendMessage', wait: '/rest/v1/users' };
  const calls = stub({ hold });
  await handleUpdate({ message: { from, chat, text: '/exam' } });
  assert.ok(hold.overlapped, 'the reply went while the user was being saved');
  assert.equal(tg(calls, 'sendMessage').length, 1);
  assert.equal(calls.filter((c) => c.u.includes('/rest/v1/users')).length, 1, 'the user saved');
});

test('/settings waits for the row and shows the switch as it is', async () => {
  const calls = stub({ row: { id: 7, daily_question: false } });
  await handleUpdate({ message: { from, chat, text: '/settings' } });
  const sent = tg(calls, 'sendMessage')[0].body;
  assert.match(sent.reply_markup.inline_keyboard[0][0].callback_data, /^dq:1:/, 'off: the button turns it on');
});

test('/daily: the language and the save at once, then the question', async () => {
  const hold = { ask: '/rest/v1/progress', wait: '/rest/v1/users' };
  const calls = stub({ hold });
  await handleUpdate({ message: { from, chat, text: '/daily' } });
  assert.ok(hold.overlapped, 'the chosen language looked up while the user was being saved');
  assert.equal(tg(calls, 'sendPhoto').length + tg(calls, 'sendMessage').length, 1);
});

test('the switch: one write with the row, then the tap answered and the button redrawn at once', async () => {
  const hold = { ask: '/editMessageReplyMarkup', wait: '/answerCallbackQuery' };
  const calls = stub({ hold });
  const message = { chat, message_id: 5, reply_markup: { inline_keyboard: [[{ text: 'on', callback_data: 'dq:0:e' }], [{ text: 'open', url: 'https://app.test/' }]] } };
  await handleUpdate({ callback_query: { id: 'c1', from, message, data: 'dq:0:e' } });
  const writes = calls.filter((c) => c.u.includes('/rest/v1/users'));
  assert.equal(writes.length, 1); assert.equal(writes[0].method, 'POST'); assert.equal(writes[0].body.daily_question, false);
  assert.ok(hold.overlapped, 'answered while the button was being redrawn');
  const kbd = tg(calls, 'editMessageReplyMarkup')[0].body.reply_markup.inline_keyboard;
  assert.match(kbd[0][0].callback_data, /^dq:1:/); assert.equal(kbd[1][0].text, 'open');
});

test('the switch: a write that fails is thrown (the webhook logs it), and the button is left as it was', async () => {
  const calls = stub({ fail: true });
  const message = { chat, message_id: 5, reply_markup: { inline_keyboard: [[{ text: 'on', callback_data: 'dq:0:e' }]] } };
  await assert.rejects(handleUpdate({ callback_query: { id: 'c1', from, message, data: 'dq:0:e' } }), /db POST users: 500/);
  assert.equal(tg(calls, 'editMessageReplyMarkup').length, 0);
});
