// The Regatta game's races, kept in public.game_races (supabase/migrations/20261111120000_game_races.sql) for the
// admins' Overview page (api/admin.mjs) and the game card on everyone's Home. the game's stats.js (the ryc-regatta repo) posts here
// when a race starts and when the player finishes it. The game is a site of its own (regatta.rycrentals.com), so every
// answer allows any origin (CORS): the numbers are public, and a post carries no cookies.
//
//   GET /api/game → { week: { races, players }, best: { w, l, c, n, sh, top: [ { name, s, p, ph, fl } ] } | null,
//                     daily: { d, w, sh, races, top: [ { name, s, p, ph, fl } ] } | null }                            (public, cached)
//     week: races started in the last 7 days and the players in them (everyone in a plain browser counts as one);
//     best: the course most finished on in the last 30 days (wind, laps, length, boats) and its 3 fastest players, by
//     their best time without a disqualification, with their best place on that course (p). name is the first name
//     and the last initial ("Anna P."), null for a player in a plain browser or one the app does not know. ph is the
//     key to their picture (below), for a player inside Telegram; fl is the flag their site account's boat flies
//     (user_metadata.boat, accountFlag), else the one their boat flew in their latest race
//     ('gb', null for none); nothing else about a player leaves the server.
//     The course also has a shape (sh: 'wl' up and down, 'tri' triangle, 'trap' trapezoid, 'wlu' up and down with an
//     upwind finish; races from before it was kept count as 'wl'), so two shapes are two courses.
//     Daily races are left out of it: daily is today's daily race (UTC date d, its wind w), the races finished on it and
//     its 3 fastest players, guests left out (races counts their races all the same). Everyone sails the daily race in
//     the same wind (the seed is the date), so only there do times compare fairly.
//   GET /api/game?photo=<ph> → that player's Telegram profile photo (JPEG), 204 when the bot may see none. ph is
//     their Telegram id sealed with a key made from the bot token (AES-GCM, so it can be neither read nor made up);
//     the same player always gets the same ph, so the photo can be cached.
//   GET /api/game?race=<uuid> → the result page's record of that race, as the game posted it (below), 404 when there
//     is none. It is what a shared result link shows on another device; the id is unguessable, so only the people
//     the player gave the link to can find it.
//   GET /api/game?day=2026-11-14 → that day's daily race ranked, and the month's points to that day (public, cached):
//     { d, w, races, guests, rows: [ { k, name, ph, fl, s, p, pts, n } ],
//       month: { m: '2026-11', days, rows: [ { k, name, ph, fl, pts, days, wins, podiums } ] }, days: [ '2026-11-14', … ] }
//     name here is the whole name ("Anna Petrova", at most 40 characters), not the card's first name and initial.
//     races: the day's finished races (no disqualification, a time that passed the checks), guests' among them (how
//     many: guests); only a player who is somebody ranks. rows: each player's best time that day (s), their best place
//     in the fleet (p) and how many races they finished (n), the fastest first. Points (pts): on a day N players rank,
//     the first gets N, the last 1 (a point for finishing and one for every player beaten); equal times share the
//     better place. month: the points of the month's days up to d added up, with the days each player scored on, won
//     and was in the top three of, the most points first. days: the month's days up to d that ranked anyone, the
//     latest first. k is a key that stays the same for a player (not their id). A day in the future, more than
//     DAY_BACK days back or not a date is 404.
//
//   POST /api/game { ev: 'start', id: '<uuid>', wind: 'light' | 'medium' | 'strong', laps: 1,
//                    length: 'short' | 'medium' | 'long', boats: 10, daily: '2026-11-12' (the daily race only),
//                    shape: 'wl' | 'tri' | 'trap' | 'wlu', flag: 'gb' (the boat's flag, if she flies one) } → 204
//   POST /api/game { ev: 'finish', id: '<uuid>', place: 2 | null, boats: 4, secs: 431.2, dsq: false }       → 204
//   POST /api/game { ev: 'result', id: '<uuid>', result: { … } }  (the result page's record, at most RESULT_MAX) → 204
//
// Who the player is: inside Telegram, the launch data (initData in the body, or x-telegram-init-data as
// api/settings.mjs); on the site, the access token of their Regatta account (token in the body: the site's accounts
// are this project's Supabase Auth users). A Telegram account (app_metadata.telegram_id) counts as that Telegram
// user, any other as player (its Auth id, migration 20261113120000), named by its user_metadata.display_name. With
// neither the race is a guest's. Anyone can post, so each instance takes at most LIMIT posts per address per
// window, a finish only fills in a race that was started and not finished yet, and a result only a race that has
// none. The time is the player's word, so it is checked twice: against the clock (the game runs at most 3× as fast
// as life, so a finish posted sooner after the start than its time allows keeps no time) and against the course (no
// time under FLOOR seconds a metre of beat a lap, half what the game's own best computer skippers take). A time that
// fails either is kept as none, and so never ranks. Without the database, or before the table (or a later column) is
// there, it answers 204 all the same; the game never waits on it.

import { createCipheriv, createDecipheriv, createHash, createHmac } from 'node:crypto';
import { verifyInitData, db, logError, tgPhoto, SB, SB_KEY } from './settings.mjs';

const LIMIT = 60, WINDOW = 10 * 60e3;
const seen = new Map(); // address → [count, window start]
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const int = (v, lo, hi) => (Number.isInteger(v) && v >= lo && v <= hi ? v : null);
const SHAPES = ['wl', 'tri', 'trap', 'wlu']; // up and down, triangle, trapezoid, up and down with an upwind finish
const CORS = { 'access-control-allow-origin': '*' };
const done = (status = 204) => new Response(null, { status, headers: CORS });

// The shortest time a course allows. The game's beat (the start to the windward mark) is BEAT metres in each wind, times
// LEN for the course length; its computer skippers, who sail close to the boat's polar, take 0.75–1.2 s a metre of beat
// for each lap (public/game/sim.js, measured in the ryc-regatta repo's test/sim.test.mjs). No one sails it in half that.
const BEAT = { light: 200, medium: 260, strong: 280 }, LEN = { short: 1, medium: 2, long: 3.4 }, FLOOR = 0.45;
const floorSecs = (r) => (BEAT[r.wind] && LEN[r.length] ? FLOOR * BEAT[r.wind] * LEN[r.length] * (r.laps || 1) : 0);
const RESULT_MAX = 60_000; // bytes of JSON: twelve boats' thinned tracks and the log come to some 25 000

// Supabase Auth, with the same key rules as db() in settings.mjs (the admin API) or with a player's own token.
async function auth(path, token) {
  const headers = { apikey: SB_KEY, ...(token ? { authorization: `Bearer ${token}` } : SB_KEY.startsWith('eyJ') && { authorization: `Bearer ${SB_KEY}` }) };
  const res = await fetch(`${SB}/auth/v1/${path}`, { headers });
  return res.ok ? res.json() : null;
}
// the Regatta account behind an access token: { tg } for one made from Telegram, { player } for any other, else null
async function account(token) {
  if (typeof token !== 'string' || !token || token.length > 4096) return null;
  try {
    const u = await auth('user', token);
    if (!u || !UUID.test(u.id || '')) return null;
    const tg = u.app_metadata && Number(u.app_metadata.telegram_id);
    return Number.isSafeInteger(tg) && tg > 0 ? { tg } : { player: u.id };
  } catch { return null; }
}
// a row's player for the rankings: the Telegram id, 'a:<Auth id>' for a site account, 'anon' for a guest
const who = (r) => (r.user_id != null ? r.user_id : r.player ? `a:${r.player}` : 'anon');

// For everyone: the numbers on the game card. Cached at the edge for 5 minutes, so the table is read at most that
// often however many people open Home.
const DAY = 864e5, MAX_ROWS = 20_000;
// The picture key: 12 bytes of IV (from the id, so it is always the same), the 8-byte id encrypted, 16 bytes of tag.
const PKEY = createHash('sha256').update(`game-photo:${process.env.TELEGRAM_BOT_TOKEN || ''}`).digest();
function sealId(id) {
  const b = Buffer.alloc(8); b.writeBigInt64BE(BigInt(id));
  const iv = createHmac('sha256', PKEY).update(b).digest().subarray(0, 12), c = createCipheriv('aes-256-gcm', PKEY, iv);
  return Buffer.concat([iv, c.update(b), c.final(), c.getAuthTag()]).toString('base64url');
}
function openId(key) {
  try {
    const r = Buffer.from(String(key), 'base64url');
    if (r.length !== 36) return null;
    const d = createDecipheriv('aes-256-gcm', PKEY, r.subarray(0, 12)); d.setAuthTag(r.subarray(20));
    const id = Number(Buffer.concat([d.update(r.subarray(12, 20)), d.final()]).readBigInt64BE());
    return Number.isSafeInteger(id) && id > 0 ? id : null;
  } catch { return null; }
}
const shortName = (name) => { const w = String(name || '').trim().split(/\s+/).filter(Boolean); return w.length ? `${w[0].slice(0, 20)}${w[1] ? ` ${[...w[1]][0]}.` : ''}` : null; };
// the whole name, as the rating shows it ("Anna Petrova"): its words, one space apart, at most 40 characters
const fullName = (name) => { const n = String(name || '').trim().split(/\s+/).filter(Boolean).join(' '); return n ? [...n].slice(0, 40).join('') : null; };
// a boat's flag as the game posts it (lib/flags.ts in the ryc-regatta repo): 'gb', or one with a region, 'gb-sct'
const flagOf = (v) => (typeof v === 'string' && /^[a-z]{2}(-[a-z]{2,4})?$/.test(v) ? v : null);
// The flag a site account flies now: the site keeps a signed-in player's boat in user_metadata.boat (lib/boat.ts in
// the ryc-regatta repo), so a flag picked there is theirs at once, on any device, without a race to carry it. Its
// flag, or null for a boat that flies none; undefined for an account with no boat kept, whose latest race then says.
export const accountFlag = (meta) => {
  const boat = meta && meta.boat;
  return boat && typeof boat === 'object' && !Array.isArray(boat) ? flagOf(boat.flag) : undefined;
};
// the columns added after the table, newest last: a read or a write without one of them still works before its
// migration is applied (20261112120000, 20261113120000, 20261114120000, 20261114130000)
const LATER = ['player', 'daily', 'shape', 'flag'];

// Every race the filter finds, 1000 a page, the latest first; a later column not there yet is left out of cols.
async function readRaces(cols, filter) {
  const rows = [];
  for (let off = 0; off < MAX_ROWS; off += 1000) {
    let page;
    try { page = await db(`game_races?select=${cols}&${filter}&order=started_at.desc&limit=1000&offset=${off}`); }
    catch (e) {
      const col = !off && LATER.find((c) => cols.includes(`,${c}`) && new RegExp(c).test(e.message));
      if (!col) throw e;
      cols = cols.replace(`,${col}`, ''); off -= 1000; continue;
    }
    rows.push(...page);
    if (page.length < 1000) break;
  }
  return rows;
}
// each player's flag, from their latest race among rows
function latestFlags(rows) {
  const out = new Map(), at = new Map();
  for (const r of rows) {
    const k = who(r), t = Date.parse(r.started_at) || 0;
    if (!at.has(k) || t > at.get(k)) { at.set(k, t); out.set(k, flagOf(r.flag)); }
  }
  return out;
}
// The flag each of a rating's players flies: the one of their latest race of any kind in the last 30 days (a start
// they didn't finish, a free race), read exactly as the game card reads it (every race of those 30 days, not a filter
// on the rating's players), so the card and the rating always show a player under the same flag; for a player with no
// race that recent, the one of their latest race among rows.
async function flyingFlags(rows, now) {
  let recent = [];
  try { recent = await readRaces('started_at,user_id,player,flag', `started_at=gte.${new Date(now - 30 * DAY).toISOString()}`); }
  catch (e) { await logError('rating flags', e); } // the rating's own rows then
  return latestFlags([...rows, ...recent]);
}
// each player's best time among rows (finished, no disqualification, a time), with their best place and how many
// of them they finished: key → { u, a, s, p, n }. Guests are left out unless guests is true.
export function bests(rows, guests = false) {
  const out = new Map();
  for (const r of rows) {
    if (!r.finished_at || r.dsq || !(r.secs > 0)) continue;
    const k = who(r);
    if (k === 'anon' && !guests) continue;
    const b = out.get(k) || { u: r.user_id ?? null, a: r.player || null, s: Infinity, p: 0, n: 0 };
    b.s = Math.min(b.s, r.secs); b.n++;
    if (r.place && (!b.p || r.place < b.p)) b.p = r.place;
    out.set(k, b);
  }
  return out;
}
// A day ranked: the players' bests (from bests) fastest first, each with their place and points. On a day N players
// rank the first gets N points and the last 1; equal times share the better place, and its points.
export function rankDay(best) {
  const list = [...best].map(([key, b]) => ({ key, ...b })).sort((a, b) => a.s - b.s), N = list.length;
  let place = 0;
  list.forEach((x, i) => { if (!i || x.s > list[i - 1].s) place = i + 1; x.place = place; x.pts = N - place + 1; });
  return list;
}
// The month's table: days is each day's ranking (rankDay). Each player's points added up, the days they scored on,
// won and were in the top three of; the most points first, then the most wins, then podiums.
export function monthTable(days) {
  const out = new Map();
  for (const day of days) for (const x of day) {
    const m = out.get(x.key) || { key: x.key, u: x.u, a: x.a, pts: 0, days: 0, wins: 0, podiums: 0 };
    m.pts += x.pts; m.days++;
    if (x.place === 1) m.wins++;
    if (x.place <= 3) m.podiums++;
    out.set(x.key, m);
  }
  return [...out.values()].sort((a, b) => b.pts - a.pts || b.wins - a.wins || b.podiums - a.podiums);
}
// Names for players ({ key, u, a }): a Telegram user's from the users table (one look-up a hundred), a site account's
// display name from Supabase Auth, at most cap of those (each is a request of its own). key → name: short ("Anna P."),
// or the whole name when full (the rating). flags, when given, takes each of those site accounts' own flag
// (accountFlag) in place of the one their latest race flew.
async function namesOf(players, cap, full = false, flags = null) {
  const nameOf = full ? fullName : shortName;
  const names = new Map(), ids = [...new Set(players.filter((x) => x.u != null).map((x) => x.u))];
  for (let i = 0; i < ids.length; i += 100) {
    for (const u of await db(`users?select=id,name&id=in.(${ids.slice(i, i + 100).join(',')})`)) names.set(String(u.id), nameOf(u.name));
  }
  for (const x of players) if (x.u != null) names.set(x.key, names.get(String(x.u)) || null);
  const site = [...new Map(players.filter((x) => x.u == null && x.a).map((x) => [x.key, x])).values()].slice(0, cap);
  for (let i = 0; i < site.length; i += 10) {
    await Promise.all(site.slice(i, i + 10).map(async (x) => {
      const u = await auth(`admin/users/${x.a}`).catch(() => null);
      names.set(x.key, nameOf(u && u.user_metadata && u.user_metadata.display_name));
      const fl = flags && u ? accountFlag(u.user_metadata) : undefined;
      if (fl !== undefined) flags.set(x.key, fl);
    }));
  }
  return names;
}
// what of a player leaves the server: a key that stays theirs (not their id), and their picture's key if in Telegram
const AKEY = createHash('sha256').update(`game-player:${process.env.TELEGRAM_BOT_TOKEN || ''}`).digest();
const keyOf = (x) => (x.u != null ? sealId(x.u) : createHmac('sha256', AKEY).update(`a:${x.a}`).digest('base64url').slice(0, 16));
const DAY_BACK = 400;

export async function GET(request) {
  const params = request ? new URL(request.url).searchParams : new URLSearchParams();
  const key = params.get('photo');
  if (key != null) {
    const id = openId(key);
    if (!id || !process.env.TELEGRAM_BOT_TOKEN) return new Response(null, { status: 404 });
    try { return await tgPhoto(id, 'public'); } catch (e) { await logError('game photo', e, id); return new Response(null, { status: 502 }); }
  }
  const json = (body, status = 200, cache = 'public, max-age=60, s-maxage=300, stale-while-revalidate=600') =>
    Response.json(body, { status, headers: { ...CORS, 'cache-control': status === 200 ? cache : 'no-store' } });
  const race = params.get('race');
  if (race != null) {
    // a shared result: once posted it never changes, so it is cached for a day
    const id = race.toLowerCase();
    if (!UUID.test(id) || !SB || !SB_KEY) return json({ error: 'not found' }, 404);
    try {
      const [r] = await db(`game_races?select=result&id=eq.${id}&result=not.is.null`);
      if (!r) return json({ error: 'not found' }, 404);
      return Response.json(r.result, { headers: { ...CORS, 'cache-control': 'public, max-age=3600, s-maxage=86400' } });
    } catch (e) {
      if (!/: 404 |result/.test(e.message)) await logError('game result', e); // 404 or no result column: not there yet
      return json({ error: 'not found' }, 404);
    }
  }
  const day = params.get('day');
  if (day != null) return dayRating(day, json);
  if (!SB || !SB_KEY) return json({ week: { races: 0, players: 0 }, best: null });
  try {
    const now = Date.now(), from = new Date(now - 30 * DAY).toISOString();
    const rows = await readRaces('started_at,finished_at,user_id,player,wind,laps,length,boats,secs,dsq,place,daily,shape,flag', `started_at=gte.${from}`);
    const week = rows.filter((r) => Date.parse(r.started_at) >= now - 7 * DAY);
    const players = new Set(week.map(who)).size;
    const flags = latestFlags(rows);
    // the courses finished on, the busiest first; on it, each player's best time
    const courses = new Map();
    for (const r of rows) {
      if (!r.finished_at || r.dsq || !(r.secs > 0) || !r.length || !r.boats || r.daily) continue;
      const sh = r.shape || 'wl', key = `${r.wind}|${r.laps || 1}|${r.length}|${r.boats}|${sh}`, c = courses.get(key) || { w: r.wind, l: r.laps || 1, c: r.length, n: r.boats, sh, races: 0, rows: [] };
      c.races++; c.rows.push(r);
      courses.set(key, c);
    }
    // the three fastest of a set of players' bests, with their names, pictures and flags
    const podium = async (best) => {
      const top = [...best].map(([key, b]) => ({ key, ...b })).sort((a, b) => a.s - b.s).slice(0, 3);
      const names = await namesOf(top, 3, false, flags);
      return top.map((x) => ({ name: names.get(x.key) || null, s: x.s, p: x.p || null, ph: x.u != null ? sealId(x.u) : null, fl: flags.get(x.key) ?? null }));
    };
    const busiest = [...courses.values()].sort((a, b) => b.races - a.races || SHAPES.indexOf(a.sh) - SHAPES.indexOf(b.sh))[0];
    // (the course's ranking is everyone's, guests together counting as one, as it always has)
    const best = busiest ? { w: busiest.w, l: busiest.l, c: busiest.c, n: busiest.n, sh: busiest.sh, top: await podium(bests(busiest.rows, true)) } : null;
    // today's daily race (UTC): each player's best time on it. Every race counts in races, but only a player who is
    // somebody ranks: the site asks a guest to sign in to get on this ranking, and all guests together are not a player.
    const today = new Date(now).toISOString().slice(0, 10);
    const dRows = rows.filter((r) => r.daily === today && r.finished_at && !r.dsq && r.secs > 0);
    // today's shape: the one most of today's rows name (a game from before the shapes posts none, so a row without one
    // says nothing about it), up and down if none does
    const dShapes = new Map();
    for (const r of dRows) if (r.shape) dShapes.set(r.shape, (dShapes.get(r.shape) || 0) + 1);
    const dShape = [...dShapes].sort((a, b) => b[1] - a[1] || SHAPES.indexOf(a[0]) - SHAPES.indexOf(b[0]))[0]?.[0] || 'wl';
    const daily = dRows.length ? { d: today, w: dRows[dRows.length - 1].wind, sh: dShape, races: dRows.length, top: await podium(bests(dRows)) } : null;
    return json({ week: { races: week.length, players }, best, daily });
  } catch (e) {
    if (!/: 404 /.test(e.message)) await logError('game stats', e);
    return json({ error: 'failed' }, 500);
  }
}

// GET ?day=: the day's daily race ranked and the month's points to that day (see the top of the file).
async function dayRating(day, json) {
  const now = Date.now(), today = new Date(now).toISOString().slice(0, 10), t = Date.parse(`${day}T00:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || !Number.isFinite(t) || new Date(t).toISOString().slice(0, 10) !== day
      || day > today || t < Date.parse(`${today}T00:00:00Z`) - DAY_BACK * DAY) return json({ error: 'not found' }, 404);
  // a past day no longer changes; today's does, so it keeps the card's five minutes
  const cache = day < today ? 'public, max-age=300, s-maxage=86400, stale-while-revalidate=86400' : undefined;
  const m = day.slice(0, 7), empty = { d: day, w: null, races: 0, guests: 0, rows: [], month: { m, days: 0, rows: [] }, days: [] };
  if (!SB || !SB_KEY) return json(empty, 200, cache);
  try {
    let rows;
    try {
      rows = await readRaces('started_at,finished_at,user_id,player,wind,secs,dsq,place,daily,flag',
        `daily=gte.${m}-01&daily=lte.${day}&finished_at=not.is.null&dsq=is.false&secs=gt.0`);
    } catch (e) {
      if (/daily/.test(e.message)) return json(empty, 200, cache); // no daily column yet: no daily races either
      throw e;
    }
    const byDay = new Map();
    for (const r of rows) (byDay.get(r.daily) || byDay.set(r.daily, []).get(r.daily)).push(r);
    const ranked = new Map([...byDay].map(([d, rs]) => [d, rankDay(bests(rs))]).filter(([, list]) => list.length));
    const days = [...ranked.keys()].sort().reverse();
    const mine = byDay.get(day) || [], dayList = ranked.get(day) || [], month = monthTable([...ranked.values()]);
    const flags = await flyingFlags(rows, now);
    // names: the day's players first, then the month's, the most points first
    const names = await namesOf([...dayList, ...month], 80, true, flags);
    const pub = (x) => ({ k: keyOf(x), name: names.get(x.key) || null, ph: x.u != null ? sealId(x.u) : null, fl: flags.get(x.key) ?? null });
    const nameSort = (a, b) => (a.name == null) - (b.name == null) || String(a.name || '').localeCompare(String(b.name || ''));
    return json({
      d: day, w: mine.length ? mine[mine.length - 1].wind : null, races: mine.length, guests: mine.filter((r) => who(r) === 'anon').length,
      rows: dayList.map((x) => ({ ...pub(x), s: x.s, p: x.p || null, pts: x.pts, n: x.n })),
      month: { m, days: days.length, rows: month.map((x) => ({ ...pub(x), pts: x.pts, days: x.days, wins: x.wins, podiums: x.podiums }))
        .sort((a, b) => b.pts - a.pts || b.wins - a.wins || b.podiums - a.podiums || nameSort(a, b)) },
      days,
    }, 200, cache);
  } catch (e) {
    if (!/: 404 /.test(e.message)) await logError('game rating', e);
    return json({ error: 'failed' }, 500);
  }
}

export async function POST(request) {
  const ip = (request.headers.get('x-forwarded-for') || '').split(',')[0].trim() || '?', now = Date.now();
  const s = seen.get(ip);
  if (s && now - s[1] < WINDOW) { if (++s[0] > LIMIT) return done(429); }
  else { seen.set(ip, [1, now]); if (seen.size > 5000) seen.clear(); }
  let b;
  try { b = await request.json(); } catch { return done(400); }
  const id = b && typeof b.id === 'string' ? b.id.toLowerCase() : '';
  if (!UUID.test(id) || !['start', 'finish', 'result'].includes(b.ev)) return done(400);
  if (!SB || !SB_KEY) return done();
  // the launch data: in the body from the game (a simple cross-site post, see stats.js), or in the header as from the app
  const user = verifyInitData(request.headers.get('x-telegram-init-data') || (typeof b.initData === 'string' ? b.initData : ''), process.env.TELEGRAM_BOT_TOKEN);
  try {
    if (b.ev === 'start') {
      // without the launch data, the player's site account (only the start names the player; the finish finds the row)
      const acct = user ? null : await account(b.token);
      const tg = user ? user.id : acct && acct.tg ? acct.tg : null, player = acct && acct.player ? acct.player : null;
      // a daily race names its day: today or yesterday (UTC), for a player just past midnight
      const daily = typeof b.daily === 'string' && [0, 1].some((d) => new Date(now - d * DAY).toISOString().slice(0, 10) === b.daily) ? b.daily : null;
      let row = { id, user_id: tg, wind: ['light', 'medium', 'strong'].includes(b.wind) ? b.wind : null, laps: int(b.laps, 1, 9),
                  length: ['short', 'medium', 'long'].includes(b.length) ? b.length : null, boats: int(b.boats, 1, 20), ...(daily && { daily }), ...(player && { player }),
                  shape: SHAPES.includes(b.shape) ? b.shape : null, ...(flagOf(b.flag) && { flag: b.flag }) };
      // a column not there yet (LATER): written without it
      for (;;) {
        try { await db('game_races?on_conflict=id', { method: 'POST', prefer: 'resolution=ignore-duplicates,return=representation', body: row }); break; }
        catch (e) {
          const col = LATER.find((c) => c in row && new RegExp(c).test(e.message));
          if (!col) throw e;
          const { [col]: _, ...rest } = row; row = rest;
        }
      }
    } else if (b.ev === 'result') {
      // the result page's record, for a shared link: once, for a race that was started here, and not too big
      const text = JSON.stringify(b.result || null);
      if (!b.result || typeof b.result !== 'object' || Array.isArray(b.result) || text.length > RESULT_MAX) return done(400);
      await db(`game_races?id=eq.${id}&result=is.null`, { method: 'PATCH', prefer: 'return=representation', body: { result: b.result } }).catch((e) => {
        if (!/result/.test(e.message)) throw e; // no result column yet
      });
    } else {
      let secs = Number.isFinite(b.secs) && b.secs >= 0 && b.secs < 86400 ? Math.round(b.secs * 10) / 10 : null;
      const [st] = await db(`game_races?select=started_at,wind,length,laps,boats&id=eq.${id}&finished_at=is.null`);
      if (!st) return done();
      // the time can't be more than 3× the time since the start was posted (the game's fastest speed), less a little slack
      if (secs != null && secs > ((now - Date.parse(st.started_at)) / 1000) * 3 + 20) secs = null;
      // nor shorter than the course allows
      if (secs != null && secs < floorSecs(st)) secs = null;
      // the fleet as the finish counts it, else as the start did: a finish without a good one never blanks the start's,
      // which would drop the race from its course's ranking. A place outside the fleet is no place (the table's
      // game_races_place_in_fleet check would refuse the whole finish).
      const boats = int(b.boats, 1, 20) ?? st.boats ?? null;
      const place = b.dsq ? null : int(b.place, 1, boats ?? 20);
      await db(`game_races?id=eq.${id}&finished_at=is.null`, {
        method: 'PATCH', prefer: 'return=representation',
        body: { finished_at: new Date().toISOString(), place, boats, secs, dsq: !!b.dsq },
      });
    }
  } catch (e) {
    if (!/: 404 /.test(e.message)) await logError('game', e, user ? user.id : null); // 404: the table is not there yet
  }
  return done();
}
