// The Regatta game's races, kept in public.game_races (supabase/migrations/20261111120000_game_races.sql) for the
// admins' Overview page (api/admin.mjs). miniapp/regatta/stats.js posts here when a race starts and when the player
// finishes it.
//
//   POST /api/game { ev: 'start', id: '<uuid>', wind: 'light' | 'medium' | 'strong', laps: 1 }               → 204
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
        body: { id, user_id: user ? user.id : null, wind: ['light', 'medium', 'strong'].includes(b.wind) ? b.wind : null, laps: int(b.laps, 1, 9) },
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
