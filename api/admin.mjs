// Every student's results, for the admins (ADMINS in api/settings.mjs). The mini app shows them on the Students page
// behind a button in the profile that only admins see.
//
//   GET /api/admin            → { users: [ { id, name, username, lang, daily, joined, active, level, total, streak, lastDay,
//                                 week, levels: { fs: { mastered, seen, mistakes }, … }, exams: [{ lv, at, pct, passed }],
//                                 flags: ['bs-012', …], wrong: ['bs-034', …] } ],
//                               series: { hour: [ { at, joined, answers, wrong } × 24 ], day: [ … × 91 ] } | null }
//   POST /api/admin { unflag: { q: 'bs-012', k: 'flags' | 'wrong', users: [id, …] } } → { ok: true, users: [id, …] }
//                             takes that flag off those students' question (public.flag_clears, see below); 501 when the
//                             table is not in the database yet
//   GET /api/admin?photo=<id> → the student's Telegram profile photo (JPEG, smallest size), 204 when they have none
//                               that the bot may see. The bot fetches it (getUserProfilePhotos + getFile) because the file
//                               link carries the bot token, so the app never sees that link.
//
// One entry per row of public.users (people who wrote to the bot or opened the app), newest activity first. The
// numbers come from public.progress — the app's own state (see fresh() in miniapp/app.js), summed up here per level
// prefix (fs = Flotilla Skipper, bs = Bareboat Skipper, …; the app knows the bank sizes and turns counts into %).
// flags are the question ids the student marked to come back to (state.flags) and wrong the ones they reported as
// having a mistake (state.wrong, the red flag); the app groups both by question on the Students page, so the admins
// see which questions people get stuck on and which need a fix.
// series is for the charts on the Overview page, per UTC hour (the last 24) and per UTC day (the last 91), oldest first:
// people who joined (users.created_at), answers given and the wrong ones among them (public.answers); the app cuts its
// 24h / 7d / 30d / 3m views out of it. It comes from public.admin_series()
// (supabase/migrations/20261104190000_admin_series_flag_clears.sql); until that function is in the database the same
// numbers are counted here from the answer rows. null when neither worked — the rest of the page still loads.
// An admin taking a flag off writes public.flag_clears; the student's app drops the flag on its next sync
// (api/progress.mjs), and until then the lists here leave it out.
// The caller proves who they are with Telegram.WebApp.initData in the x-telegram-init-data header (as api/settings.mjs);
// anyone who is not an admin gets 403, exactly like a bad signature. Env on Vercel: TELEGRAM_BOT_TOKEN, SUPABASE_URL,
// SUPABASE_SECRET_KEY. Without the database it answers 503.

import { verifyInitData, isAdmin, db, SB, SB_KEY } from './settings.mjs';

const json = (body, status = 200) => Response.json(body, { status, headers: { 'cache-control': 'no-store' } });
const MAX_USERS = 1000;
const MAX_FLAGS = 500; // per student, per kind
// Question ids out of a state list: well-formed, no repeats (the app never sends anything else; the state is the app's).
const cleanIds = (list) => [...new Set((Array.isArray(list) ? list : []).filter((id) => typeof id === 'string' && /^[a-z]{1,8}-\d{1,5}$/.test(id)))].slice(0, MAX_FLAGS);

const pad = (n) => String(n).padStart(2, '0');
const dkey = (d) => `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;

const UNITS = { hour: [24, 3600e3], day: [91, 86400e3] }; // buckets in the series, and their length in ms
const MAX_ANSWER_ROWS = 50_000; // the fallback below reads the rows themselves; past this the database function is a must
// Joins, answers and wrong answers per UTC hour and per UTC day, oldest first (see the header).
async function series(users) {
  try {
    const units = Object.keys(UNITS);
    const rows = await Promise.all(units.map((u) => db('rpc/admin_series', { method: 'POST', body: { p_unit: u, p_count: UNITS[u][0] } })));
    const out = {};
    units.forEach((u, i) => { out[u] = rows[i].map((r) => ({ at: new Date(r.at).toISOString(), joined: +r.joined || 0, answers: +r.answers || 0, wrong: +r.wrong || 0 })); });
    return out;
  } catch (e) {
    if (!/: 404 /.test(e.message)) throw e; // anything but "no such function" is a real failure
  }
  const out = {}, starts = {};
  for (const [u, [n, step]] of Object.entries(UNITS)) {
    const s = new Date();
    if (u === 'hour') s.setUTCMinutes(0, 0, 0); else s.setUTCHours(0, 0, 0, 0);
    starts[u] = +s - (n - 1) * step;
    out[u] = Array.from({ length: n }, (_, i) => ({ at: new Date(starts[u] + i * step).toISOString(), joined: 0, answers: 0, wrong: 0 }));
  }
  const add = (time, f) => { for (const u in UNITS) { const i = Math.floor((time - starts[u]) / UNITS[u][1]); if (i >= 0 && i < out[u].length) f(out[u][i]); } };
  for (const u of users) add(Date.parse(u.created_at), (r) => r.joined++);
  const from = new Date(starts.day).toISOString();
  for (let off = 0; off < MAX_ANSWER_ROWS; off += 1000) {
    const page = await db(`answers?select=at,correct&at=gte.${from}&order=id.asc&limit=1000&offset=${off}`);
    for (const a of page) add(Date.parse(a.at), (r) => { r.answers++; if (!a.correct) r.wrong++; });
    if (page.length < 1000) break;
  }
  return out;
}
// The flags admins took off that the students' apps have not dropped yet ([] while the table is not there).
const pendingClears = () => db('flag_clears?select=user_id,question_id,kind&limit=10000').catch((e) => {
  if (!/: 404 /.test(e.message)) console.error('admin clears', e.message);
  return [];
});

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
    level: null, total: 0, streak: 0, lastDay: null, week: 0, levels: {}, exams: [], flags: [], wrong: [],
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
  out.flags = cleanIds(p.flags);
  out.wrong = cleanIds(p.wrong);
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
    const [users, progress, clears] = await Promise.all([
      db(`users?select=id,name,username,lang,daily_question,blocked_at,created_at,updated_at&order=updated_at.desc&limit=${MAX_USERS}`),
      // only the parts of the state the summary needs; the whole state can be ~100 KB per student
      db(`progress?select=user_id,ts,updated_at,total:state->total,q:state->q,exams:state->exams,days:state->days,set:state->set,flags:state->flags,wrong:state->wrong&limit=${MAX_USERS}`),
      pendingClears(),
    ]);
    const byUser = new Map(progress.map((p) => [p.user_id, p]));
    const list = users.map((u) => summarise(u, byUser.get(u.id)));
    list.sort((a, b) => Date.parse(b.active) - Date.parse(a.active));
    const byId = new Map(list.map((u) => [u.id, u]));
    for (const c of clears) { const u = byId.get(c.user_id); if (u && (c.kind === 'flags' || c.kind === 'wrong')) u[c.kind] = u[c.kind].filter((id) => id !== c.question_id); }
    const data = await series(users).catch((e) => { console.error('admin series', e.message); return null; });
    return json({ users: list, series: data });
  } catch (e) {
    console.error('admin', user.id, e.message);
    return json({ error: 'failed' }, 500);
  }
}

// An admin takes a flag off some students' question: one flag_clears row per student (a repeat just renews it).
export async function POST(request) {
  if (!SB || !SB_KEY) return json({ error: 'no database' }, 503);
  const user = verifyInitData(request.headers.get('x-telegram-init-data'), TOKEN);
  if (!user || !isAdmin(user)) return json({ error: 'forbidden' }, 403);
  let body;
  try { body = await request.json(); } catch { return json({ error: 'bad request' }, 400); }
  const u = body && body.unflag, k = u && u.k, q = u && u.q;
  const ids = [...new Set((Array.isArray(u && u.users) ? u.users : []).filter(Number.isSafeInteger))].slice(0, MAX_USERS);
  if (!['flags', 'wrong'].includes(k) || typeof q !== 'string' || !/^[a-z]{1,8}-\d{1,5}$/.test(q) || !ids.length) return json({ error: 'bad request' }, 400);
  try {
    const at = new Date().toISOString();
    await db('flag_clears?on_conflict=user_id,question_id,kind', {
      method: 'POST', prefer: 'resolution=merge-duplicates,return=representation',
      body: ids.map((id) => ({ user_id: id, question_id: q, kind: k, by_user: user.id, at })),
    });
    return json({ ok: true, users: ids });
  } catch (e) {
    if (/: 404 /.test(e.message)) return json({ error: 'not set up' }, 501); // the migration is not in the database yet
    console.error('admin unflag', user.id, e.message);
    return json({ error: 'failed' }, 500);
  }
}
