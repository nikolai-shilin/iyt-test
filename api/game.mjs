// The Regatta game's races, kept in public.game_races (supabase/migrations/20261111120000_game_races.sql) for the
// admins' Overview page (api/admin.mjs) and the game card on everyone's Home. miniapp/regatta/stats.js posts here
// when a race starts and when the player finishes it.
//
//   GET /api/game → { week: { races, players }, best: { w, l, c, n, top: [ { name, s } ] } | null }   (public, cached)
//     week: races started in the last 7 days and the players in them (everyone in a plain browser counts as one);
//     best: the course most finished on in the last 30 days (wind, laps, length, boats) and its 3 fastest players, by
//     their best time without a disqualification. name is the first name and the last initial ("Anna P."), null for
//     a player in a plain browser or one the app does not know; nothing else about a player leaves the server.
//
//   POST /api/game { ev: 'start', id: '<uuid>', wind: 'light' | 'medium' | 'strong', laps: 1,
//                    length: 'short' | 'medium' | 'long', boats: 10 }                                       → 204
//   POST /api/game { ev: 'finish', id: '<uuid>', place: 2 | null, boats: 4, secs: 431.2, dsq: false }       → 204
//
// The game also runs in a plain browser, so the launch data (x-telegram-init-data, as api/settings.mjs) is optional:
// with it the row names the player. Anyone can post, so each instance takes at most LIMIT posts per address per
// window, and a finish only fills in a race that was started and not finished yet. Without the database, or before
// the table is there, it answers 204 all the same; the game never waits on it.

import { verifyInitData, db, logError, SB, SB_KEY } from './settings.mjs';

const LIMIT = 60, WINDOW = 10 * 60e3;
const seen = new Map(); // address → [count, window start]
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const int = (v, lo, hi) => (Number.isInteger(v) && v >= lo && v <= hi ? v : null);
const done = (status = 204) => new Response(null, { status });

// For everyone: the numbers on the game card. Cached at the edge for 5 minutes, so the table is read at most that
// often however many people open Home.
const DAY = 864e5, MAX_ROWS = 20_000;
const shortName = (name) => { const w = String(name || '').trim().split(/\s+/).filter(Boolean); return w.length ? `${w[0].slice(0, 20)}${w[1] ? ` ${[...w[1]][0]}.` : ''}` : null; };
export async function GET() {
  const json = (body, status = 200) => Response.json(body, { status, headers: { 'cache-control': status === 200 ? 'public, max-age=60, s-maxage=300, stale-while-revalidate=600' : 'no-store' } });
  if (!SB || !SB_KEY) return json({ week: { races: 0, players: 0 }, best: null });
  try {
    const now = Date.now(), from = new Date(now - 30 * DAY).toISOString(), rows = [];
    for (let off = 0; off < MAX_ROWS; off += 1000) {
      const page = await db(`game_races?select=started_at,finished_at,user_id,wind,laps,length,boats,secs,dsq&started_at=gte.${from}&order=started_at.desc&limit=1000&offset=${off}`);
      rows.push(...page);
      if (page.length < 1000) break;
    }
    const week = rows.filter((r) => Date.parse(r.started_at) >= now - 7 * DAY);
    const players = new Set(week.map((r) => (r.user_id == null ? 'anon' : r.user_id))).size;
    // the courses finished on, the busiest first; on it, each player's best time
    const courses = new Map();
    for (const r of rows) {
      if (!r.finished_at || r.dsq || !(r.secs > 0) || !r.length || !r.boats) continue;
      const key = `${r.wind}|${r.laps || 1}|${r.length}|${r.boats}`, c = courses.get(key) || { w: r.wind, l: r.laps || 1, c: r.length, n: r.boats, races: 0, best: new Map() };
      c.races++;
      const k = r.user_id == null ? 'anon' : r.user_id;
      if (!c.best.has(k) || r.secs < c.best.get(k).s) c.best.set(k, { u: r.user_id, s: r.secs });
      courses.set(key, c);
    }
    const busiest = [...courses.values()].sort((a, b) => b.races - a.races)[0];
    let best = null;
    if (busiest) {
      const top = [...busiest.best.values()].sort((a, b) => a.s - b.s).slice(0, 3);
      const ids = top.map((x) => x.u).filter((u) => u != null);
      const names = new Map(ids.length ? (await db(`users?select=id,name&id=in.(${ids.join(',')})`)).map((u) => [u.id, shortName(u.name)]) : []);
      best = { w: busiest.w, l: busiest.l, c: busiest.c, n: busiest.n, top: top.map((x) => ({ name: names.get(x.u) || null, s: x.s })) };
    }
    return json({ week: { races: week.length, players }, best });
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
  const user = verifyInitData(request.headers.get('x-telegram-init-data'), process.env.TELEGRAM_BOT_TOKEN);
  try {
    if (b.ev === 'start') {
      await db('game_races?on_conflict=id', {
        method: 'POST', prefer: 'resolution=ignore-duplicates,return=representation',
        body: { id, user_id: user ? user.id : null, wind: ['light', 'medium', 'strong'].includes(b.wind) ? b.wind : null, laps: int(b.laps, 1, 9),
                length: ['short', 'medium', 'long'].includes(b.length) ? b.length : null, boats: int(b.boats, 1, 20) },
      });
    } else {
      const secs = Number.isFinite(b.secs) && b.secs >= 0 && b.secs < 86400 ? Math.round(b.secs * 10) / 10 : null;
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
