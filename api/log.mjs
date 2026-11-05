// Errors the mini app did not catch (window 'error' and 'unhandledrejection', reportError in miniapp/app.js), kept in
// public.errors, to read in the database (no chart shows them; the admins' Overview charts reported mistakes instead).
//
//   POST /api/log { m: 'message', w: 'app.js:123' } → 204
//
// The app also runs in a plain browser, so the launch data (x-telegram-init-data, as api/settings.mjs) is optional:
// with it the row names the user. Anyone can post, so each instance takes at most LIMIT reports per address per
// window, and the message is cut short. Without the database it answers 204 all the same; the app never waits on it.

import { verifyInitData, logError } from './settings.mjs';

const LIMIT = 20, WINDOW = 10 * 60e3;
const seen = new Map(); // address → [count, window start]

export async function POST(request) {
  const ip = (request.headers.get('x-forwarded-for') || '').split(',')[0].trim() || '?', now = Date.now();
  const s = seen.get(ip);
  if (s && now - s[1] < WINDOW) { if (++s[0] > LIMIT) return new Response(null, { status: 429 }); }
  else { seen.set(ip, [1, now]); if (seen.size > 5000) seen.clear(); }
  let body;
  try { body = await request.json(); } catch { return new Response(null, { status: 400 }); }
  const m = body && typeof body.m === 'string' ? body.m.trim().slice(0, 1000) : '';
  if (!m) return new Response(null, { status: 400 });
  const w = body && typeof body.w === 'string' ? body.w.slice(0, 200) : 'app';
  const user = verifyInitData(request.headers.get('x-telegram-init-data'), process.env.TELEGRAM_BOT_TOKEN);
  await logError(w, m, user ? user.id : null, 'app');
  return new Response(null, { status: 204 });
}
