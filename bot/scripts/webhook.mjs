// Points @iyt_test_bot at its Vercel webhook (api/telegram.mjs), or removes it for local polling.
//
//   npm run bot:webhook                 # set the webhook to $WEBAPP_URL/api/telegram
//   npm run bot:webhook -- --delete     # remove it (then `npm run bot` can poll)
//   npm run bot:webhook -- --check      # print the current webhook state
//
// Needs TELEGRAM_BOT_TOKEN, WEBAPP_URL and TELEGRAM_WEBHOOK_SECRET in .env.local. The same secret must be set on
// Vercel, so the function can tell Telegram's calls from anyone else's.

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) { console.error('TELEGRAM_BOT_TOKEN is not set (put it in .env.local)'); process.exit(1); }

async function call(method, params = {}) {
  const res = await fetch(`https://api.telegram.org/bot${token}/${method}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(params) });
  const data = await res.json();
  if (!data.ok) throw new Error(`${method}: ${data.description}`);
  return data.result;
}

const show = async () => {
  const { url, pending_update_count, last_error_date, last_error_message } = await call('getWebhookInfo');
  console.log('webhook:', url || '(none)', '· pending updates:', pending_update_count);
  if (last_error_date) console.log('last error:', new Date(last_error_date * 1000).toISOString(), last_error_message);
};

if (process.argv.includes('--check')) { await show(); process.exit(0); }

if (process.argv.includes('--delete')) {
  await call('deleteWebhook');
  console.log('webhook removed');
} else {
  const base = (process.env.WEBAPP_URL || '').replace(/\/$/, '');
  const secret = process.env.TELEGRAM_WEBHOOK_SECRET;
  if (!base || !secret) { console.error('Set WEBAPP_URL and TELEGRAM_WEBHOOK_SECRET in .env.local'); process.exit(1); }
  await call('setWebhook', { url: `${base}/api/telegram`, secret_token: secret, allowed_updates: ['message', 'callback_query'] });
  console.log('webhook set');
}
await show();
