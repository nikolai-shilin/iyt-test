// NO LONGER SERVED from here. The Go port in the ryc-regatta repo (www.sailupdown.com/api/regatta-session) serves this endpoint now, and
// vercel.json forwards /api/regatta-session to it. This file stays, with its tests, until the old code is deleted.

// A Telegram player's sign-in on the Regatta site (the ryc-regatta repo, www.sailupdown.com), whose accounts are
// this Supabase project's Auth users. The app's Regatta button opens the site with the launch data in the hash; the
// site's server posts it here. It is checked with the bot token, the player's Auth user is made the first time
// (tg-<telegram id>@telegram.rycrentals.com, never mailed, named after the Telegram name, app_metadata.telegram_id),
// and the answer is a one-time sign-in token that the site turns into its session cookie
// (supabase.auth.verifyOtp({ token_hash, type: 'magiclink' }) in app/auth/telegram/route.ts there).
//
//   POST /api/regatta-session  { initData }  → { token_hash, telegram_id }   403 when the launch data is not good
//
// The token lets whoever holds it sign in as that player, so it goes only to a caller who already holds that player's
// signed launch data. Env on Vercel: TELEGRAM_BOT_TOKEN, SUPABASE_URL, SUPABASE_SECRET_KEY.

import { verifyInitData, logError, noEmoji, SB, SB_KEY } from '../api/settings.mjs';

const json = (body, status = 200) => Response.json(body, { status, headers: { 'cache-control': 'no-store' } });

// a new account's name for the ranking, as the site's own name page would make it: the first name and the first letter
// of the surname, without emoji
export const accountName = (user) => {
  const first = noEmoji(user.first_name), last = noEmoji(user.last_name);
  return [first, last && `${[...last][0]}.`].filter(Boolean).join(' ').slice(0, 24) || user.username || null;
};

// Supabase Auth's admin API, with the same key rules as db() in settings.mjs.
async function auth(path, body) {
  const headers = { apikey: SB_KEY, 'content-type': 'application/json', ...(SB_KEY.startsWith('eyJ') && { authorization: `Bearer ${SB_KEY}` }) };
  const res = await fetch(`${SB}/auth/v1/${path}`, { method: 'POST', headers, body: JSON.stringify(body) });
  return { ok: res.ok, status: res.status, data: await res.json().catch(() => ({})) };
}

export async function POST(request) {
  if (!SB || !SB_KEY) return json({ error: 'no database' }, 503);
  let b;
  try { b = await request.json(); } catch { return json({ error: 'bad request' }, 400); }
  const user = verifyInitData(b && typeof b.initData === 'string' ? b.initData : '', process.env.TELEGRAM_BOT_TOKEN);
  if (!user) return json({ error: 'forbidden' }, 403);

  const email = `tg-${user.id}@telegram.rycrentals.com`;
  try {
    // the first time only: a confirmed user, named for the ranking; later the player's own choice of name is left alone
    const name = accountName(user);
    const made = await auth('admin/users', {
      email, email_confirm: true,
      user_metadata: { ...(name && { display_name: name }) },
      app_metadata: { telegram_id: user.id, ...(user.username && { telegram_username: user.username }) },
    });
    if (!made.ok && made.data?.error_code !== 'email_exists' && made.status !== 422) throw new Error(`create user: ${made.status} ${JSON.stringify(made.data)}`);
    const link = await auth('admin/generate_link', { type: 'magiclink', email });
    const token_hash = link.data?.hashed_token || link.data?.properties?.hashed_token;
    if (!link.ok || !token_hash) throw new Error(`generate link: ${link.status} ${JSON.stringify(link.data)}`);
    return json({ token_hash, telegram_id: user.id });
  } catch (e) {
    await logError('regatta-session', e, user.id);
    return json({ error: 'failed' }, 500);
  }
}
