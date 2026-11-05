// Vercel cron (vercel.json "crons"): sends the question of the day once a day at 09:00 UTC (13:00 Dubai) — see bot/daily.mjs.
// Vercel calls it with "Authorization: Bearer $CRON_SECRET"; anything else is refused, so nobody else can
// trigger a send to every user. Env on Vercel: CRON_SECRET, SUPABASE_URL, SUPABASE_SECRET_KEY, TELEGRAM_BOT_TOKEN,
// WEBAPP_URL, and optionally DAILY_QUESTION=off to stop the send for everyone.

import { sendDaily } from '../bot/daily.mjs';
import { logError } from './settings.mjs';

export async function GET(request) {
  const secret = process.env.CRON_SECRET;
  if (!secret || request.headers.get('authorization') !== `Bearer ${secret}`) return new Response('forbidden', { status: 403 });
  try {
    const result = await sendDaily();
    console.log('daily', JSON.stringify(result));
    return Response.json(result);
  } catch (e) {
    await logError('daily', e);
    return Response.json({ error: e.message }, { status: 500 });
  }
}
