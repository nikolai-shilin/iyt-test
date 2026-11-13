// The Regatta game's races, kept in public.game_races (supabase/migrations/20261111120000_game_races.sql) for the
// admins' Overview page (api/admin.mjs) and the game card on everyone's Home. the game's stats.js (the ryc-regatta repo) posts here
// when a race starts and when the player finishes it. The game is a site of its own (regatta.rycrentals.com), so every
// answer allows any origin (CORS): the numbers are public, and a post carries no cookies.
//
//   GET /api/game → { week: { races, players }, best: { w, l, c, n, top: [ { name, s, p, ph } ] } | null,
//                     daily: { d, w, races, top: [ { name, s, p, ph } ] } | null }                                (public, cached)
//     week: races started in the last 7 days and the players in them (everyone in a plain browser counts as one);
//     best: the course most finished on in the last 30 days (wind, laps, length, boats) and its 3 fastest players, by
//     their best time without a disqualification, with their best place on that course (p). name is the first name
//     and the last initial ("Anna P."), null for a player in a plain browser or one the app does not know. ph is the
//     key to their picture (below), for a player inside Telegram; nothing else about a player leaves the server.
//     Daily races are left out of it: daily is today's daily race (UTC date d, its wind w), the races finished on it and
//     its 3 fastest. Everyone sails the daily race in the same wind (the seed is the date), so only there do times
//     compare fairly.
//   GET /api/game?photo=<ph> → that player's Telegram profile photo (JPEG), 204 when the bot may see none. ph is
//     their Telegram id sealed with a key made from the bot token (AES-GCM, so it can be neither read nor made up);
//     the same player always gets the same ph, so the photo can be cached.
//
//   POST /api/game { ev: 'start', id: '<uuid>', wind: 'light' | 'medium' | 'strong', laps: 1,
//                    length: 'short' | 'medium' | 'long', boats: 10, daily: '2026-11-12' (the daily race only) } → 204
//   POST /api/game { ev: 'finish', id: '<uuid>', place: 2 | null, boats: 4, secs: 431.2, dsq: false }       → 204
//
// The game also runs in a plain browser, so the launch data (x-telegram-init-data, as api/settings.mjs) is optional:
// with it the row names the player. Anyone can post, so each instance takes at most LIMIT posts per address per
// window, and a finish only fills in a race that was started and not finished yet. The time is the player's word, so
// it is checked against the clock: the game runs at most 3× as fast as life, so a finish posted sooner after the start
// than its time allows keeps no time (and so never ranks). Without the database, or before the table (or its daily
// column, migration 20261112120000) is there, it answers 204 all the same; the game never waits on it.

import { createCipheriv, createDecipheriv, createHash, createHmac } from 'node:crypto';
import { verifyInitData, db, logError, tgPhoto, SB, SB_KEY } from './settings.mjs';

const LIMIT = 60, WINDOW = 10 * 60e3;
const seen = new Map(); // address → [count, window start]
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const int = (v, lo, hi) => (Number.isInteger(v) && v >= lo && v <= hi ? v : null);
const CORS = { 'access-control-allow-origin': '*' };
const done = (status = 204) => new Response(null, { status, headers: CORS });

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
export async function GET(request) {
  const key = request && new URL(request.url).searchParams.get('photo');
  if (key != null) {
    const id = openId(key);
    if (!id || !process.env.TELEGRAM_BOT_TOKEN) return new Response(null, { status: 404 });
    try { return await tgPhoto(id, 'public'); } catch (e) { await logError('game photo', e, id); return new Response(null, { status: 502 }); }
  }
  const json = (body, status = 200) => Response.json(body, { status, headers: { ...CORS, 'cache-control': status === 200 ? 'public, max-age=60, s-maxage=300, stale-while-revalidate=600' : 'no-store' } });
  if (!SB || !SB_KEY) return json({ week: { races: 0, players: 0 }, best: null });
  try {
    const now = Date.now(), from = new Date(now - 30 * DAY).toISOString(), rows = [];
    let cols = 'started_at,finished_at,user_id,wind,laps,length,boats,secs,dsq,place,daily';
    for (let off = 0; off < MAX_ROWS; off += 1000) {
      let page;
      try { page = await db(`game_races?select=${cols}&started_at=gte.${from}&order=started_at.desc&limit=1000&offset=${off}`); }
      catch (e) { if (off || !/daily/.test(e.message)) throw e; cols = cols.replace(',daily', ''); off -= 1000; continue; } // no daily column yet
      rows.push(...page);
      if (page.length < 1000) break;
    }
    const week = rows.filter((r) => Date.parse(r.started_at) >= now - 7 * DAY);
    const players = new Set(week.map((r) => (r.user_id == null ? 'anon' : r.user_id))).size;
    // the courses finished on, the busiest first; on it, each player's best time
    const courses = new Map();
    for (const r of rows) {
      if (!r.finished_at || r.dsq || !(r.secs > 0) || !r.length || !r.boats || r.daily) continue;
      const key = `${r.wind}|${r.laps || 1}|${r.length}|${r.boats}`, c = courses.get(key) || { w: r.wind, l: r.laps || 1, c: r.length, n: r.boats, races: 0, best: new Map() };
      c.races++;
      const k = r.user_id == null ? 'anon' : r.user_id;
      const b = c.best.get(k) || { u: r.user_id, s: Infinity, p: 0 };
      b.s = Math.min(b.s, r.secs); if (r.place && (!b.p || r.place < b.p)) b.p = r.place;
      c.best.set(k, b);
      courses.set(key, c);
    }
    // the three fastest of a set of players' bests, with their names and pictures
    const podium = async (bests) => {
      const top = [...bests.values()].sort((a, b) => a.s - b.s).slice(0, 3);
      const ids = top.map((x) => x.u).filter((u) => u != null);
      const names = new Map(ids.length ? (await db(`users?select=id,name&id=in.(${ids.join(',')})`)).map((u) => [u.id, shortName(u.name)]) : []);
      return top.map((x) => ({ name: names.get(x.u) || null, s: x.s, p: x.p || null, ph: x.u != null ? sealId(x.u) : null }));
    };
    const busiest = [...courses.values()].sort((a, b) => b.races - a.races)[0];
    const best = busiest ? { w: busiest.w, l: busiest.l, c: busiest.c, n: busiest.n, top: await podium(busiest.best) } : null;
    // today's daily race (UTC): each player's best time on it
    const today = new Date(now).toISOString().slice(0, 10), dBest = new Map();
    let dWind = null, dRaces = 0;
    for (const r of rows) {
      if (r.daily !== today || !r.finished_at || r.dsq || !(r.secs > 0)) continue;
      dWind = r.wind; dRaces++;
      const k = r.user_id == null ? 'anon' : r.user_id, b = dBest.get(k) || { u: r.user_id, s: Infinity, p: 0 };
      b.s = Math.min(b.s, r.secs); if (r.place && (!b.p || r.place < b.p)) b.p = r.place;
      dBest.set(k, b);
    }
    const daily = dRaces ? { d: today, w: dWind, races: dRaces, top: await podium(dBest) } : null;
    return json({ week: { races: week.length, players }, best, daily });
  } catch (e) {
    if (!/: 404 /.test(e.message)) await logError('game stats', e);
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
  if (!UUID.test(id) || !['start', 'finish'].includes(b.ev)) return done(400);
  if (!SB || !SB_KEY) return done();
  // the launch data: in the body from the game (a simple cross-site post, see stats.js), or in the header as from the app
  const user = verifyInitData(request.headers.get('x-telegram-init-data') || (typeof b.initData === 'string' ? b.initData : ''), process.env.TELEGRAM_BOT_TOKEN);
  try {
    if (b.ev === 'start') {
      // a daily race names its day: today or yesterday (UTC), for a player just past midnight
      const daily = typeof b.daily === 'string' && [0, 1].some((d) => new Date(now - d * DAY).toISOString().slice(0, 10) === b.daily) ? b.daily : null;
      const row = { id, user_id: user ? user.id : null, wind: ['light', 'medium', 'strong'].includes(b.wind) ? b.wind : null, laps: int(b.laps, 1, 9),
                    length: ['short', 'medium', 'long'].includes(b.length) ? b.length : null, boats: int(b.boats, 1, 20) };
      const insert = (body) => db('game_races?on_conflict=id', { method: 'POST', prefer: 'resolution=ignore-duplicates,return=representation', body });
      if (!daily) await insert(row);
      else try { await insert({ ...row, daily }); } catch (e) { if (!/daily/.test(e.message)) throw e; await insert(row); } // no daily column yet
    } else {
      let secs = Number.isFinite(b.secs) && b.secs >= 0 && b.secs < 86400 ? Math.round(b.secs * 10) / 10 : null;
      // the time can't be more than 3× the time since the start was posted (the game's fastest speed), less a little slack
      const [st] = await db(`game_races?select=started_at&id=eq.${id}&finished_at=is.null`);
      if (!st) return done();
      if (secs != null && secs > ((now - Date.parse(st.started_at)) / 1000) * 3 + 20) secs = null;
      await db(`game_races?id=eq.${id}&finished_at=is.null`, {
        method: 'PATCH', prefer: 'return=representation',
        body: { finished_at: new Date().toISOString(), place: b.dsq ? null : int(b.place, 1, 20), boats: int(b.boats, 1, 20), secs, dsq: !!b.dsq },
      });
    }
  } catch (e) {
    if (!/: 404 /.test(e.message)) await logError('game', e, user ? user.id : null); // 404: the table is not there yet
  }
  return done();
}
