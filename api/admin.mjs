// Every student's results, for the admins (ADMINS in api/settings.mjs). The mini app shows them on the Students page
// behind a button in the profile that only admins see.
//
//   GET /api/admin            → { users: [ { id, name, username, lang, daily, joined, active, level, total, streak, lastDay,
//                                 week, levels: { fs: { mastered, seen, mistakes }, … }, exams: [{ lv, at, pct, passed }] } ] }
//   GET /api/admin?photo=<id> → the student's Telegram profile photo (JPEG, smallest size), 204 when they have none
//                               that the bot may see. The bot fetches it (getUserProfilePhotos + getFile) because the file
//                               link carries the bot token, so the app never sees that link.
//
// One entry per row of public.users (people who wrote to the bot or opened the app), newest activity first. The
// numbers come from public.progress — the app's own state (see fresh() in miniapp/app.js), summed up here per level
// prefix (fs = Flotilla Skipper, bs = Bareboat Skipper, …; the app knows the bank sizes and turns counts into %).
// The caller proves who they are with Telegram.WebApp.initData in the x-telegram-init-data header (as api/settings.mjs);
// anyone who is not an admin gets 403, exactly like a bad signature. Env on Vercel: TELEGRAM_BOT_TOKEN, SUPABASE_URL,
// SUPABASE_SECRET_KEY. Without the database it answers 503.

import { verifyInitData, isAdmin, db, SB, SB_KEY } from './settings.mjs';

const json = (body, status = 200) => Response.json(body, { status, headers: { 'cache-control': 'no-store' } });
const MAX_USERS = 1000;

const pad = (n) => String(n).padStart(2, '0');
const dkey = (d) => `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;

// Consecutive days with answers up to today (UTC; the app keys days by the student's local date, so this can be a day off).
function streakOf(days) {
  const d = new Date();
  if (!days[dkey(d)]) d.setUTCDate(d.getUTCDate() - 1);
  let n = 0;
  while (days[dkey(d)]) { n++; d.setUTCDate(d.getUTCDate() - 1); }
  return n;
}

// One student's line: the users row plus the sums of their progress state (null when they have no state yet).
export function summarise(u, p) {
  const out = {
    id: u.id, name: u.name || null, username: u.username || null, lang: u.lang || 'en', daily: !!(u.daily_question && !u.blocked_at),
    joined: u.created_at, active: p ? p.updated_at : u.updated_at,
    level: null, total: 0, streak: 0, lastDay: null, week: 0, levels: {}, exams: [],
  };
  if (!p) return out;
  const q = p.q && typeof p.q === 'object' ? p.q : {}, days = p.days && typeof p.days === 'object' ? p.days : {};
  out.level = (p.set && typeof p.set.level === 'string' && p.set.level) || null;
  out.total = Number.isFinite(p.total) ? p.total : 0;
  for (const id in q) {
    const r = Array.isArray(q[id]) ? q[id] : ['', 0], prefix = id.split('-')[0];
    const L = out.levels[prefix] || (out.levels[prefix] = { mastered: 0, seen: 0, mistakes: 0 });
    L.seen++;
    if (r[0] === '11') L.mastered++;
    else if (r[1] > 0) L.mistakes++;
  }
  const keys = Object.keys(days).filter((k) => /^\d{4}-\d{2}-\d{2}$/.test(k)).sort();
  out.lastDay = keys[keys.length - 1] || null;
  out.streak = streakOf(days);
  const from = new Date(); from.setUTCDate(from.getUTCDate() - 6);
  const fk = dkey(from);
  out.week = keys.filter((k) => k >= fk).reduce((a, k) => a + (+days[k] || 0), 0);
  out.exams = (Array.isArray(p.exams) ? p.exams : []).slice(0, 10)
    .filter((e) => e && Number.isFinite(e.at) && Number.isFinite(e.pct))
    .map((e) => ({ lv: e.lv || 'bareboat-skipper', at: e.at, pct: e.pct, passed: !!e.passed }));
  return out;
}

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
async function tg(method, params) {
  const res = await fetch(`https://api.telegram.org/bot${TOKEN}/${method}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(params), signal: AbortSignal.timeout(8000) });
  const data = await res.json();
  if (!data.ok) throw new Error(`${method}: ${data.description}`);
  return data.result;
}
async function photo(id) {
  const { photos } = await tg('getUserProfilePhotos', { user_id: id, limit: 1 });
  const sizes = photos && photos[0];
  if (!sizes || !sizes.length) return new Response(null, { status: 204, headers: { 'cache-control': 'private, max-age=3600' } });
  const { file_path } = await tg('getFile', { file_id: sizes[0].file_id }); // [0] is the smallest size (160 px)
  const file = await fetch(`https://api.telegram.org/file/bot${TOKEN}/${file_path}`, { signal: AbortSignal.timeout(8000) });
  if (!file.ok) throw new Error(`file ${file.status}`);
  return new Response(await file.arrayBuffer(), { headers: { 'content-type': 'image/jpeg', 'cache-control': 'private, max-age=86400' } });
}

export async function GET(request) {
  if (!SB || !SB_KEY) return json({ error: 'no database' }, 503);
  const user = verifyInitData(request.headers.get('x-telegram-init-data'), TOKEN);
  if (!user || !isAdmin(user)) return json({ error: 'forbidden' }, 403);
  const id = new URL(request.url).searchParams.get('photo');
  if (id != null) {
    if (!/^\d{1,20}$/.test(id)) return json({ error: 'bad request' }, 400);
    try { return await photo(+id); } catch (e) { console.error('admin photo', id, e.message); return json({ error: 'failed' }, 500); }
  }
  try {
    const [users, progress] = await Promise.all([
      db(`users?select=id,name,username,lang,daily_question,blocked_at,created_at,updated_at&order=updated_at.desc&limit=${MAX_USERS}`),
      // only the parts of the state the summary needs; the whole state can be ~100 KB per student
      db(`progress?select=user_id,ts,updated_at,total:state->total,q:state->q,exams:state->exams,days:state->days,set:state->set&limit=${MAX_USERS}`),
    ]);
    const byUser = new Map(progress.map((p) => [p.user_id, p]));
    const list = users.map((u) => summarise(u, byUser.get(u.id)));
    list.sort((a, b) => Date.parse(b.active) - Date.parse(a.active));
    return json({ users: list });
  } catch (e) {
    console.error('admin', user.id, e.message);
    return json({ error: 'failed' }, 500);
  }
}
