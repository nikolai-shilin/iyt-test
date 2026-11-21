// A message from the Regatta site (the ryc-regatta repo, www.sailupdown.com) to one of its sailors through this bot:
// a 1-on-1 Match found while they are away from the site (lib/push-send.ts there; who may be written to is the
// database's regatta_pair_push, supabase/migrations/20261121235000_regatta_telegram.sql). The bot token stays here.
//
//   POST /api/regatta-notify  Authorization: Bearer $REGATTA_NOTIFY_SECRET
//        { telegram_id, text, button: { text, url } }   → 200 { sent: true } | 410 { blocked: true } | 4xx/5xx
//
// The text goes as plain text (no markup), with one button that opens the site's page inside Telegram as a mini app
// (web_app), so the sailor arrives signed in from the launch data. The button only ever opens a page of the site.
// A user who has blocked the bot (or whose chat is gone) is marked blocked_at, as the daily question does, and the
// database stops offering them. Env on Vercel: REGATTA_NOTIFY_SECRET (the same on the site), TELEGRAM_BOT_TOKEN,
// SUPABASE_URL, SUPABASE_SECRET_KEY.

import { db, logError } from './settings.mjs';

const SITE = 'https://www.sailupdown.com';
const json = (body, status = 200) => Response.json(body, { status, headers: { 'cache-control': 'no-store' } });

// the message as asked, or null: a Telegram id, a short text, and a button to a page of the site
export function readNotice(b) {
  if (!b || typeof b !== 'object') return null;
  const id = Number(b.telegram_id), text = typeof b.text === 'string' ? b.text.trim() : '';
  const btn = b.button && typeof b.button === 'object' ? b.button : null;
  const label = btn && typeof btn.text === 'string' ? btn.text.trim() : '', url = btn && typeof btn.url === 'string' ? btn.url : '';
  if (!Number.isSafeInteger(id) || id <= 0 || !text || text.length > 1000 || !label || label.length > 64) return null;
  let u;
  try { u = new URL(url); } catch { return null; }
  if (u.origin !== SITE) return null;
  return { id, text, label, url: u.href };
}

export async function POST(request, { send = defaultSend, mark = markBlocked } = {}) {
  const secret = process.env.REGATTA_NOTIFY_SECRET;
  if (!secret || request.headers.get('authorization') !== `Bearer ${secret}`) return json({ error: 'forbidden' }, 403);
  let b = null;
  try { b = await request.json(); } catch {}
  const n = readNotice(b);
  if (!n) return json({ error: 'bad request' }, 400);
  try {
    await send(n);
    return json({ sent: true });
  } catch (e) {
    if (e.code === 403 || /chat not found|user is deactivated|bot was blocked/i.test(e.message || '')) {
      await mark(n.id).catch(() => {});
      return json({ blocked: true }, 410);
    }
    await logError('regatta-notify', e, n.id).catch(() => {});
    return json({ error: 'failed' }, 502);
  }
}

async function defaultSend(n) {
  const res = await fetch(`https://api.telegram.org/bot${process.env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, signal: AbortSignal.timeout(8000),
    body: JSON.stringify({ chat_id: n.id, text: n.text, link_preview_options: { is_disabled: true }, reply_markup: { inline_keyboard: [[{ text: n.label, web_app: { url: n.url } }]] } }),
  });
  const data = await res.json().catch(() => ({}));
  if (!data.ok) throw Object.assign(new Error(data.description || `sendMessage ${res.status}`), { code: data.error_code });
}

const markBlocked = (id) => db(`users?id=eq.${+id}`, { method: 'PATCH', body: { blocked_at: new Date().toISOString() } });
