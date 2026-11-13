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
//   GET /api/game?race=<uuid> → the result page's record of that race, as the game posted it (below), 404 when there
//     is none. It is what a shared result link shows on another device; the id is unguessable, so only the people
//     the player gave the link to can find it.
//
//   POST /api/game { ev: 'start', id: '<uuid>', wind: 'light' | 'medium' | 'strong', laps: 1,
//                    length: 'short' | 'medium' | 'long', boats: 10, daily: '2026-11-12' (the daily race only) } → 204
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
export async function GET(request) {
  const key = request && new URL(request.url).searchParams.get('photo');
  if (key != null) {
    const id = openId(key);
    if (!id || !process.env.TELEGRAM_BOT_TOKEN) return new Response(null, { status: 404 });
    try { return await tgPhoto(id, 'public'); } catch (e) { await logError('game photo', e, id); return new Response(null, { status: 502 }); }
  }
  const json = (body, status = 200) => Response.json(body, { status, headers: { ...CORS, 'cache-control': status === 200 ? 'public, max-age=60, s-maxage=300, stale-while-revalidate=600' : 'no-store' } });
  const race = request && new URL(request.url).searchParams.get('race');
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
  if (!SB || !SB_KEY) return json({ week: { races: 0, players: 0 }, best: null });
  try {
    const now = Date.now(), from = new Date(now - 30 * DAY).toISOString(), rows = [];
    let cols = 'started_at,finished_at,user_id,player,wind,laps,length,boats,secs,dsq,place,daily';
    for (let off = 0; off < MAX_ROWS; off += 1000) {
      let page;
      try { page = await db(`game_races?select=${cols}&started_at=gte.${from}&order=started_at.desc&limit=1000&offset=${off}`); }
      catch (e) {
        // a column not there yet (migrations 20261112120000, 20261113120000): read without it
        const col = !off && ['player', 'daily'].find((c) => cols.includes(`,${c}`) && new RegExp(c).test(e.message));
        if (!col) throw e;
        cols = cols.replace(`,${col}`, ''); off -= 1000; continue;
      }
      rows.push(...page);
      if (page.length < 1000) break;
    }
    const week = rows.filter((r) => Date.parse(r.started_at) >= now - 7 * DAY);
    const players = new Set(week.map(who)).size;
    // the courses finished on, the busiest first; on it, each player's best time
    const courses = new Map();
    for (const r of rows) {
      if (!r.finished_at || r.dsq || !(r.secs > 0) || !r.length || !r.boats || r.daily) continue;
      const key = `${r.wind}|${r.laps || 1}|${r.length}|${r.boats}`, c = courses.get(key) || { w: r.wind, l: r.laps || 1, c: r.length, n: r.boats, races: 0, best: new Map() };
      c.races++;
      const k = who(r);
      const b = c.best.get(k) || { u: r.user_id, a: r.player || null, s: Infinity, p: 0 };
      b.s = Math.min(b.s, r.secs); if (r.place && (!b.p || r.place < b.p)) b.p = r.place;
      c.best.set(k, b);
      courses.set(key, c);
    }
    // the three fastest of a set of players' bests, with their names and pictures
    const podium = async (bests) => {
      const top = [...bests.values()].sort((a, b) => a.s - b.s).slice(0, 3);
      const ids = top.map((x) => x.u).filter((u) => u != null);
      const names = new Map(ids.length ? (await db(`users?select=id,name&id=in.(${ids.join(',')})`)).map((u) => [u.id, shortName(u.name)]) : []);
      // site accounts: the name they gave for the ranking (at most three look-ups, and the answer is cached)
      for (const x of top) {
        if (x.u != null || !x.a) continue;
        const u = await auth(`admin/users/${x.a}`).catch(() => null);
        names.set(`a:${x.a}`, shortName(u && u.user_metadata && u.user_metadata.display_name));
      }
      return top.map((x) => ({ name: names.get(x.u != null ? x.u : `a:${x.a}`) || null, s: x.s, p: x.p || null, ph: x.u != null ? sealId(x.u) : null }));
    };
    const busiest = [...courses.values()].sort((a, b) => b.races - a.races)[0];
    const best = busiest ? { w: busiest.w, l: busiest.l, c: busiest.c, n: busiest.n, top: await podium(busiest.best) } : null;
    // today's daily race (UTC): each player's best time on it
    const today = new Date(now).toISOString().slice(0, 10), dBest = new Map();
    let dWind = null, dRaces = 0;
    for (const r of rows) {
      if (r.daily !== today || !r.finished_at || r.dsq || !(r.secs > 0)) continue;
      dWind = r.wind; dRaces++;
      const k = who(r), b = dBest.get(k) || { u: r.user_id, a: r.player || null, s: Infinity, p: 0 };
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
                  length: ['short', 'medium', 'long'].includes(b.length) ? b.length : null, boats: int(b.boats, 1, 20), ...(daily && { daily }), ...(player && { player }) };
      // a column not there yet (migrations 20261112120000, 20261113120000): written without it
      for (;;) {
        try { await db('game_races?on_conflict=id', { method: 'POST', prefer: 'resolution=ignore-duplicates,return=representation', body: row }); break; }
        catch (e) {
          const col = ['player', 'daily'].find((c) => c in row && new RegExp(c).test(e.message));
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
      const [st] = await db(`game_races?select=started_at,wind,length,laps&id=eq.${id}&finished_at=is.null`);
      if (!st) return done();
      // the time can't be more than 3× the time since the start was posted (the game's fastest speed), less a little slack
      if (secs != null && secs > ((now - Date.parse(st.started_at)) / 1000) * 3 + 20) secs = null;
      // nor shorter than the course allows
      if (secs != null && secs < floorSecs(st)) secs = null;
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
