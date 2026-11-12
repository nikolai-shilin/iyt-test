// Every student's results, for the admins (ADMINS in api/settings.mjs). The mini app shows them on the Students page
// behind a button in the profile that only admins see.
//
//   GET /api/admin            → { users: [ { id, name, username, lang, uiLang, daily, joined, active, level, total, streak, lastDay,
//                                 week, levels: { fs: { mastered, seen, mistakes }, … }, exams: [{ lv, at, pct, passed }],
//                                 flags: ['bs-012', …], wrong: ['bs-034', …],
//                                 wrongNote: { 'bs-034': { text, at, lang } },
//                                 notes: [ { k: 'bs-buoyage/cardinal', text, at, lang } ] } ],
//                               series: { hour: [ { at, joined, answers, wrong, reads, reports, races } × 24 ], day: [ … × 91 ] } | null,
//                               game: [ { at, u, w, l, c, f, p, n, s, d } ] | null }
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
// see which questions people get stuck on and which need a fix. wrongNote is what the student wrote about a question
// they reported (state.wrongNote, the sheet behind the red flag), for the ids still in wrong. notes is what the student wrote about a section of a
// theory article (state.notes, the flag beside a section's heading): the article and section, the comment, when, and
// the language the article was shown in (notes written before that was kept have none). uiLang is the language the
// student reads the app in: their EN/RU pick (state.set.lang), else lang (the bot's guess from Telegram, the same rule
// the app uses until they pick); the admin pages show each student's flagged questions in it.
// series is for the charts on the Overview page, per UTC hour (the last 24) and per UTC day (the last 91), oldest first:
// people who joined (users.created_at), answers given and the wrong ones among them (public.answers), theory articles
// read to the end (the times in the students' state.read; an article read before those were kept, as 1, is not on
// the chart) and mistakes the students reported: a question's red flag (when, in state.wrongAt) and a comment on a
// section of an article (state.notes[…].at). A report counts at the time it was made (a changed comment, at the
// change) and stays on the chart after an admin takes the flag off; one the student withdrew is gone. Question
// reports made before their times were kept are not on the chart. The app cuts its 24h / 7d / 30d / 3m views out of
// it. Joins and answers come from public.admin_series() (supabase/migrations/20261105120000_errors_log.sql); until
// that function is in the database they are counted here from the rows. Reads and reports are always counted here.
// null when neither worked — the rest of the page still loads.
// game is the Regatta game's races over the same 91 days, newest first (public.game_races, written by api/game.mjs):
// at = when it started (ms), u = the Telegram user (null: played in a plain browser), w = the wind, l = laps, c = the course
// length ('short' | 'medium' | 'long', null before it was kept; wind, laps, length and boats make the course, so times
// compare only within one), f = when the
// player finished (ms, 0 = left before the finish), p = their place (null: not finished or disqualified), n = boats in
// the race, s = their time (s), d = disqualified. The app counts the races, players and places for the range on
// screen; series.races is the chart of races started. null until the table is in the database.
// An admin taking a flag off writes public.flag_clears; the student's app drops the flag on its next sync
// (api/progress.mjs), and until then the lists here leave it out.
// The caller proves who they are with Telegram.WebApp.initData in the x-telegram-init-data header (as api/settings.mjs);
// anyone who is not an admin gets 403, exactly like a bad signature. Env on Vercel: TELEGRAM_BOT_TOKEN, SUPABASE_URL,
// SUPABASE_SECRET_KEY. Without the database it answers 503.

import { verifyInitData, isAdmin, db, logError, tgPhoto, SB, SB_KEY } from './settings.mjs';

const json = (body, status = 200) => Response.json(body, { status, headers: { 'cache-control': 'no-store' } });
const MAX_USERS = 1000;
const MAX_FLAGS = 500; // per student, per kind
// Question ids out of a state list: well-formed, no repeats (the app never sends anything else; the state is the app's).
const cleanIds = (list) => [...new Set((Array.isArray(list) ? list : []).filter((id) => typeof id === 'string' && /^[a-z]{1,8}-\d{1,5}$/.test(id)))].slice(0, MAX_FLAGS);

const MAX_NOTES = 50; // per student
// What a student wrote about the theory articles: state.notes['<prefix>-<topic>/<section>'] = { text, at }, or about
// one picture of that section: '<prefix>-<topic>/<section>/f<n>', n its place among the section's pictures from 1.
const cleanNotes = (notes) => Object.entries(notes && typeof notes === 'object' && !Array.isArray(notes) ? notes : {})
  .filter(([k, n]) => /^[a-z]{1,8}-[a-z0-9-]{1,40}\/[a-z0-9-]{1,40}(\/f[1-9]\d?)?$/.test(k) && n && typeof n.text === 'string' && n.text.trim())
  .slice(0, MAX_NOTES).map(([k, n]) => ({ k, text: n.text.trim().slice(0, 1000), at: Number.isFinite(n.at) ? n.at : 0, ...(LANGS.includes(n.lang) && { lang: n.lang }) }));
const LANGS = ['en', 'ru']; // the app's languages (miniapp/app.js LANGS)
// What a student wrote about the questions they reported: state.wrongNote[id] = { text, at, lang }, kept for ids.
const cleanQNotes = (notes, ids) => {
  const o = notes && typeof notes === 'object' && !Array.isArray(notes) ? notes : {};
  return Object.fromEntries(ids.filter((id) => o[id] && typeof o[id].text === 'string' && o[id].text.trim())
    .map((id) => [id, { text: o[id].text.trim().slice(0, 1000), at: Number.isFinite(o[id].at) ? o[id].at : 0, ...(LANGS.includes(o[id].lang) && { lang: o[id].lang }) }]));
};

const pad = (n) => String(n).padStart(2, '0');
const dkey = (d) => `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;

const UNITS = { hour: [24, 3600e3], day: [91, 86400e3] }; // buckets in the series, and their length in ms
const MAX_ANSWER_ROWS = 50_000; // the fallback below reads the rows themselves; past this the database function is a must
// Joins, answers, wrong answers, theory reads and reported mistakes per UTC hour and per UTC day, oldest first (see the header).
async function series(users, progress, game) {
  const out = {}, starts = {};
  for (const [u, [n, step]] of Object.entries(UNITS)) {
    const s = new Date();
    if (u === 'hour') s.setUTCMinutes(0, 0, 0); else s.setUTCHours(0, 0, 0, 0);
    starts[u] = +s - (n - 1) * step;
    out[u] = Array.from({ length: n }, (_, i) => ({ at: new Date(starts[u] + i * step).toISOString(), joined: 0, answers: 0, wrong: 0, reads: 0, reports: 0, races: 0 }));
  }
  const add = (time, f) => { for (const u in UNITS) { const i = Math.floor((time - starts[u]) / UNITS[u][1]); if (i >= 0 && i < out[u].length) f(out[u][i]); } };
  // state.read['<prefix>-<topic>'] = when the article was read to the end (ms), or 1 from before the times were kept
  for (const p of progress) for (const v of Object.values(p.read && typeof p.read === 'object' ? p.read : {})) if (v > 1e12) add(v, (r) => r.reads++);
  // state.wrongAt[question id] = when the red flag went up; state.notes['<prefix>-<topic>/<section>'].at = when the
  // comment was written (ms)
  const obj = (o) => (o && typeof o === 'object' && !Array.isArray(o) ? o : {});
  for (const p of progress) {
    for (const v of Object.values(obj(p.wrongAt))) if (v > 1e12) add(v, (r) => r.reports++);
    for (const n of Object.values(obj(p.notes))) if (n && n.at > 1e12) add(n.at, (r) => r.reports++);
  }
  for (const g of game || []) add(g.at, (r) => r.races++);
  let fn = null;
  try {
    fn = await Promise.all(Object.keys(UNITS).map((u) => db('rpc/admin_series', { method: 'POST', body: { p_unit: u, p_count: UNITS[u][0] } })));
  } catch (e) {
    if (!/: 404 /.test(e.message)) throw e; // anything but "no such function" is a real failure
  }
  if (fn) {
    // the function's buckets are the same UTC hours and days as out's, matched by their start (the hour may have
    // rolled over between the two clocks; a row with no bucket here is left out)
    Object.keys(UNITS).forEach((u, k) => {
      const at = new Map(out[u].map((b) => [b.at, b]));
      for (const r of fn[k]) { const b = at.get(new Date(r.at).toISOString()); if (b) Object.assign(b, { joined: +r.joined || 0, answers: +r.answers || 0, wrong: +r.wrong || 0 }); }
    });
    return out;
  }
  for (const u of users) add(Date.parse(u.created_at), (r) => r.joined++);
  const from = new Date(starts.day).toISOString();
  for (let off = 0; off < MAX_ANSWER_ROWS; off += 1000) {
    const page = await db(`answers?select=at,correct&at=gte.${from}&order=id.asc&limit=1000&offset=${off}`);
    for (const a of page) add(Date.parse(a.at), (r) => { r.answers++; if (!a.correct) r.wrong++; });
    if (page.length < 1000) break;
  }
  return out;
}
// The Regatta races of the last 91 days, newest first (see the header), a page of 1000 at a time (the most the database
// gives at once); null while the table is not there, or when it fails (the rest of the page still loads).
const MAX_GAME_ROWS = 20_000;
async function gameRaces() {
  const from = new Date(Date.now() - UNITS.day[0] * UNITS.day[1]).toISOString(), out = [];
  try {
    for (let off = 0; off < MAX_GAME_ROWS; off += 1000) {
      const page = await db(`game_races?select=started_at,finished_at,user_id,wind,laps,length,place,boats,secs,dsq&started_at=gte.${from}&order=started_at.desc&limit=1000&offset=${off}`);
      for (const r of page) out.push({ at: Date.parse(r.started_at), u: r.user_id, w: r.wind, l: r.laps, c: r.length, f: r.finished_at ? Date.parse(r.finished_at) : 0, p: r.place, n: r.boats, s: r.secs, d: !!r.dsq });
      if (page.length < 1000) break;
    }
    return out;
  } catch (e) {
    if (!/: 404 /.test(e.message)) await logError('admin game', e);
    return null;
  }
}
// The flags admins took off that the students' apps have not dropped yet ([] while the table is not there).
const pendingClears = () => db('flag_clears?select=user_id,question_id,kind&limit=10000').catch(async (e) => {
  if (!/: 404 /.test(e.message)) await logError('admin clears', e);
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
    id: u.id, name: u.name || null, username: u.username || null, lang: u.lang || 'en', uiLang: u.lang || 'en', daily: !!(u.daily_question && !u.blocked_at),
    joined: u.created_at, active: p ? p.updated_at : u.updated_at,
    level: null, total: 0, streak: 0, lastDay: null, week: 0, levels: {}, exams: [], flags: [], wrong: [], wrongNote: {}, notes: [],
  };
  if (!p) return out;
  const q = p.q && typeof p.q === 'object' ? p.q : {}, days = p.days && typeof p.days === 'object' ? p.days : {};
  out.level = (p.set && typeof p.set.level === 'string' && p.set.level) || null;
  if (p.set && LANGS.includes(p.set.lang)) out.uiLang = p.set.lang;
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
  out.wrongNote = cleanQNotes(p.wrongNote, out.wrong);
  out.notes = cleanNotes(p.notes);
  return out;
}

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;

export async function GET(request) {
  if (!SB || !SB_KEY) return json({ error: 'no database' }, 503);
  const user = verifyInitData(request.headers.get('x-telegram-init-data'), TOKEN);
  if (!user || !isAdmin(user)) return json({ error: 'forbidden' }, 403);
  const id = new URL(request.url).searchParams.get('photo');
  if (id != null) {
    if (!/^\d{1,20}$/.test(id)) return json({ error: 'bad request' }, 400);
    try { return await tgPhoto(+id); } catch (e) { await logError('admin photo', e, +id); return json({ error: 'failed' }, 500); }
  }
  try {
    const [users, progress, clears, game] = await Promise.all([
      db(`users?select=id,name,username,lang,daily_question,blocked_at,created_at,updated_at&order=updated_at.desc&limit=${MAX_USERS}`),
      // only the parts of the state the summary needs; the whole state can be ~100 KB per student
      db(`progress?select=user_id,ts,updated_at,total:state->total,q:state->q,exams:state->exams,days:state->days,set:state->set,flags:state->flags,wrong:state->wrong,wrongAt:state->wrongAt,wrongNote:state->wrongNote,notes:state->notes,read:state->read&limit=${MAX_USERS}`),
      pendingClears(),
      gameRaces(),
    ]);
    const byUser = new Map(progress.map((p) => [p.user_id, p]));
    const list = users.map((u) => summarise(u, byUser.get(u.id)));
    list.sort((a, b) => Date.parse(b.active) - Date.parse(a.active));
    const byId = new Map(list.map((u) => [u.id, u]));
    for (const c of clears) { const u = byId.get(c.user_id); if (u && (c.kind === 'flags' || c.kind === 'wrong')) u[c.kind] = u[c.kind].filter((id) => id !== c.question_id); }
    const data = await series(users, progress, game).catch(async (e) => { await logError('admin series', e); return null; });
    return json({ users: list, series: data, game });
  } catch (e) {
    await logError('admin', e, user.id);
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
    await logError('admin unflag', e, user.id);
    return json({ error: 'failed' }, 500);
  }
}
