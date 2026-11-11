// Telegram webhook for @iyt_test_bot: Telegram POSTs every update here (set by bot/scripts/webhook.mjs).
// Env on Vercel: TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, WEBAPP_URL.

import { handleUpdate } from '../bot/core.mjs';
import { logError } from './settings.mjs';

export async function POST(request) {
  // Telegram echoes the secret given to setWebhook in this header; anything else is not from Telegram.
  const secret = process.env.TELEGRAM_WEBHOOK_SECRET;
  if (!secret || request.headers.get('x-telegram-bot-api-secret-token') !== secret) return new Response('forbidden', { status: 403 });

  let update;
  try { update = await request.json(); } catch { return new Response('bad request', { status: 400 }); }
  // Always answer 200: a failed reply should not make Telegram resend the same update over and over.
  try { await handleUpdate(update); } catch (e) { await logError(`update ${update.update_id}`, e, update.message?.from?.id ?? update.callback_query?.from?.id ?? null); }
  return new Response('ok');
}

export function GET() {
  return new Response('Sailing Certification Test bot webhook', { headers: { 'content-type': 'text/plain' } });
}
