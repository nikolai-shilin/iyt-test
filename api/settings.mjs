// The mini app's own settings that live on the server — for now only the question-of-the-day switch
// (Supabase users.daily_question, the same column the bot's /settings button flips; see bot/daily.mjs).
//
//   GET  /api/settings                 → { daily: true | false, admin?: true }
//   POST /api/settings  { daily: bool } → { daily: true | false }
//
// admin: true is sent to the people in ADMINS (below) — the app then shows the students' results page (api/admin.mjs).
//
// The caller proves who they are with the mini app's launch data (Telegram.WebApp.initData) in the
// x-telegram-init-data header: it is signed with the bot token, so nobody can read or change another user's switch.
// Env on Vercel: TELEGRAM_BOT_TOKEN, SUPABASE_URL, SUPABASE_SECRET_KEY. Without the database it answers 503 and the
// app hides the switch.

import { createHmac, timingSafeEqual } from 'node:crypto';

const MAX_AGE = 24 * 3600; // launch data older than a day is refused

// Checks the signature of Telegram.WebApp.initData (core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
// and returns its user, or null.
export function verifyInitData(initData, token, now = Date.now() / 1000) {
  if (!initData || !token) return null;
  const p = new URLSearchParams(initData);
  const hash = p.get('hash') || '';
  p.delete('hash');
  const check = [...p.entries()].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)).map(([k, v]) => `${k}=${v}`).join('\n');
  const secret = createHmac('sha256', 'WebAppData').update(token).digest();
  const want = createHmac('sha256', secret).update(check).digest('hex');
  if (hash.length !== want.length || !timingSafeEqual(Buffer.from(hash), Buffer.from(want))) return null;
  if (!(now - Number(p.get('auth_date')) < MAX_AGE)) return null;
  try { const u = JSON.parse(p.get('user') || 'null'); return u && Number.isInteger(u.id) ? u : null; } catch { return null; }
}

// Who may see every student's results (api/admin.mjs): Telegram usernames, without the @, case does not matter.
// ADMIN_USERNAMES in the env (comma-separated) adds more without a deploy of the code.
export const ADMINS = ['fullcrimp', ...(process.env.ADMIN_USERNAMES || '').split(',')].map((u) => u.trim().replace(/^@/, '').toLowerCase()).filter(Boolean);
export const isAdmin = (user) => !!(user && user.username) && ADMINS.includes(user.username.toLowerCase());

export const SB = (process.env.SUPABASE_URL || '').replace(/\/$/, ''), SB_KEY = process.env.SUPABASE_SECRET_KEY || '';
export async function db(path, { method = 'GET', body, prefer } = {}) {
  // New secret keys (sb_secret_…) go in apikey only; a legacy service_role JWT also goes in Authorization.
  const headers = { apikey: SB_KEY, 'content-type': 'application/json', ...(SB_KEY.startsWith('eyJ') && { authorization: `Bearer ${SB_KEY}` }), ...(prefer && { prefer }) };
  const res = await fetch(`${SB}/rest/v1/${path}`, { method, headers, body: body && JSON.stringify(body) });
  if (!res.ok) throw new Error(`db ${method} ${path.split('?')[0]}: ${res.status} ${await res.text()}`);
  return res.json();
}

// A failure for the admins' Errors chart: written to the console (Vercel's logs) as before, and as a row of
// public.errors (supabase/migrations/20261105120000_errors_log.sql). The row is best effort: a failure to write it
// (no table yet, no database) is only noted in the console, and the caller never waits for it to fail.
export function logError(place, message, userId = null, source = 'api') {
  const msg = String((message && message.message) || message || 'error').slice(0, 2000);
  console.error(place, ...(userId != null ? [userId] : []), msg);
  if (!SB || !SB_KEY) return Promise.resolve();
  return db('errors', { method: 'POST', prefer: 'return=minimal', body: { source, place: String(place).slice(0, 200), message: msg, user_id: Number.isSafeInteger(userId) ? userId : null } })
    .catch((e) => console.error('errors log', e.message));
}

const RU = (u) => /^(ru|uk|be|kk)\b/i.test(u?.language_code || ''); // same rule as the bot and the app
const json = (body, status = 200) => Response.json(body, { status, headers: { 'cache-control': 'no-store' } });

async function handle(request, write) {
  if (!SB || !SB_KEY) return json({ error: 'no database' }, 503);
  const user = verifyInitData(request.headers.get('x-telegram-init-data'), process.env.TELEGRAM_BOT_TOKEN);
  if (!user) return json({ error: 'forbidden' }, 403);
  try {
    if (!write) {
      const [row] = await db(`users?id=eq.${user.id}&select=daily_question,blocked_at`);
      // no row yet: the user never wrote to the bot, so nothing is sent until they switch it on here
      return json({ daily: !!(row && row.daily_question && !row.blocked_at), ...(isAdmin(user) && { admin: true }) });
    }
    let on;
    try { on = (await request.json()).daily; } catch { return json({ error: 'bad request' }, 400); }
    if (typeof on !== 'boolean') return json({ error: 'bad request' }, 400);
    const row = { id: user.id, name: [user.first_name, user.last_name].filter(Boolean).join(' ') || null, username: user.username || null,
      lang: RU(user) ? 'ru' : 'en', daily_question: on, blocked_at: null, updated_at: new Date().toISOString() };
    const [saved] = await db('users?on_conflict=id&select=daily_question', { method: 'POST', body: row, prefer: 'resolution=merge-duplicates,return=representation' });
    return json({ daily: !!saved.daily_question });
  } catch (e) {
    await logError('settings', e, user.id);
    return json({ error: 'failed' }, 500);
  }
}

export const GET = (request) => handle(request, false);
export const POST = (request) => handle(request, true);
