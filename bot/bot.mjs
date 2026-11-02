// @iyt_test_bot by long polling — for testing on your own machine. In production the bot runs as a webhook on
// Vercel (api/telegram.mjs); both use the same replies in bot/core.mjs.
//
//   npm run bot        # = node --env-file=.env.local bot/bot.mjs
//
// Telegram sends updates either to a webhook or to getUpdates, never both: remove the webhook first with
// `npm run bot:webhook -- --delete`, and set it again with `npm run bot:webhook` when done.

import { api, handleUpdate, webapp, ALLOWED_UPDATES } from './core.mjs';

if (!webapp) console.warn('WEBAPP_URL is not set: replies will have no "Open" buttons');

const me = await api('getMe');
const hook = await api('getWebhookInfo');
if (hook.url) { console.error(`A webhook is set (${hook.url}); long polling will not receive updates. Remove it with: npm run bot:webhook -- --delete`); process.exit(1); }
console.log(`@${me.username} polling…`);

let offset = 0;
for (;;) {
  try {
    const updates = await api('getUpdates', { offset, timeout: 30, allowed_updates: ALLOWED_UPDATES });
    for (const u of updates) {
      offset = u.update_id + 1;
      try { await handleUpdate(u); } catch (e) { console.error('update', u.update_id, e.message); }
    }
  } catch (e) {
    console.error(e.message);
    await new Promise((r) => setTimeout(r, 3000));
  }
}
