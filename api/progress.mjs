// The student's progress on the server (Supabase public.progress + public.answers, see
// supabase/migrations/20261102160000_progress.sql). The mini app sends its whole state and the answers given since the
// last sync; the server keeps whichever state is newer (state.ts) and appends the answers once.
//
//   POST /api/progress  {}                         → { ts, state }   read: the server copy (state null if none)
//   POST /api/progress  { state, answers: [...] }  → { ts, state }   state is null unless the server's copy is newer
//
// answers: [{ q: 'bs-001', ok: true, o: 0–3 | null, m: 'practice' | 'exam' | 'daily', at: ISO time }]
// The caller proves who they are with Telegram.WebApp.initData in the x-telegram-init-data header (as api/settings.mjs).
// Env on Vercel: TELEGRAM_BOT_TOKEN, SUPABASE_URL, SUPABASE_SECRET_KEY. Without the database it answers 503 and the
// app keeps its progress on the device as before.

import { verifyInitData } from './settings.mjs';

const SB = (process.env.SUPABASE_URL || '').replace(/\/$/, ''), SB_KEY = process.env.SUPABASE_SECRET_KEY || '';
const MAX_ANSWERS = 2000;     // per request; the app sends at most 500
const MAX_STATE = 1_000_000;  // chars of JSON; a full state for every level is ~100 KB

const RU = (u) => /^(ru|uk|be|kk)\b/i.test(u?.language_code || ''); // same rule as the bot and the app
const json = (body, status = 200) => Response.json(body, { status, headers: { 'cache-control': 'no-store' } });

// Keeps only well-formed answers, so one bad item cannot fail the whole sync in the database.
function cleanAnswers(list) {
  if (!Array.isArray(list)) return [];
  const now = Date.now(), out = [];
  for (const a of list.slice(0, MAX_ANSWERS)) {
    if (!a || typeof a.q !== 'string' || !/^[a-z]{1,8}-\d{1,5}$/.test(a.q) || typeof a.ok !== 'boolean') continue;
    if (!['practice', 'exam', 'daily'].includes(a.m)) continue;
    const at = Date.parse(a.at);
    if (!(at > now - 400 * 86400e3 && at < now + 86400e3)) continue;
    const o = Number.isInteger(a.o) && a.o >= 0 && a.o <= 3 ? a.o : null;
    out.push({ q: a.q, ok: a.ok, o, m: a.m, at: new Date(at).toISOString() });
  }
  return out;
}

export async function POST(request) {
  if (!SB || !SB_KEY) return json({ error: 'no database' }, 503);
  const user = verifyInitData(request.headers.get('x-telegram-init-data'), process.env.TELEGRAM_BOT_TOKEN);
  if (!user) return json({ error: 'forbidden' }, 403);

  let body = {};
  try { const text = await request.text(); if (text) body = JSON.parse(text); } catch { return json({ error: 'bad request' }, 400); }
  const state = body && body.state && typeof body.state === 'object' && !Array.isArray(body.state) && Number.isSafeInteger(body.state.ts) ? body.state : null;
  if (state && JSON.stringify(state).length > MAX_STATE) return json({ error: 'too large' }, 413);

  const args = {
    p_user: user.id, p_name: [user.first_name, user.last_name].filter(Boolean).join(' ') || null, p_username: user.username || null,
    p_lang: RU(user) ? 'ru' : 'en', p_state: state, p_ts: state ? state.ts : null, p_answers: cleanAnswers(body && body.answers),
  };
  try {
    // New secret keys (sb_secret_…) go in apikey only; a legacy service_role JWT also goes in Authorization.
    const headers = { apikey: SB_KEY, 'content-type': 'application/json', ...(SB_KEY.startsWith('eyJ') && { authorization: `Bearer ${SB_KEY}` }) };
    const res = await fetch(`${SB}/rest/v1/rpc/sync_progress`, { method: 'POST', headers, body: JSON.stringify(args) });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    const r = await res.json();
    return json({ ts: r.ts, state: r.state, answers: r.answers });
  } catch (e) {
    console.error('progress', user.id, e.message);
    return json({ error: 'failed' }, 500);
  }
}
