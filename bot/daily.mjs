// The daily send (09:00 UTC = 13:00 Dubai): the question of the day to every user who has it on (users.daily_question), once per UTC day.
// It goes with its photo, in the language the user picked in the app, else their Telegram app's (bot/core.mjs).
// Run by the Vercel cron (api/daily.mjs, schedule in vercel.json) or by hand: bot/scripts/daily.mjs.
//
// Switches:
//   per user   users.daily_question — the button under the question and in /settings (bot/core.mjs)
//   whole bot  env DAILY_QUESTION=off — the cron still fires but sends nothing

import { db, hasDb, sendQuestion, questionOfTheDay, chosenLangs } from './core.mjs';

export const enabled = () => !/^(off|false|0|no)$/i.test(process.env.DAILY_QUESTION || '');
const today = () => new Date().toISOString().slice(0, 10);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Sends one user's message; retries once on Telegram's flood limit. Returns 'sent' | 'blocked' | 'failed'.
async function sendOne(user, day) {
  const q = questionOfTheDay(day, user.level_id);
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      await sendQuestion(user.id, q, user.lang === 'ru', true);
      return 'sent';
    } catch (e) {
      if (e.code === 429 && attempt === 0) { await sleep((e.retryAfter || 1) * 1000); continue; }
      if (e.code === 403 || /chat not found|user is deactivated/i.test(e.message)) return 'blocked';
      console.error('daily', user.id, e.message);
      return 'failed';
    }
  }
  return 'failed';
}

// Telegram allows about 30 messages a second to different chats; 20 at a time with a 1 s pause stays well under.
const BATCH = 20;

export async function sendDaily({ dry = false } = {}) {
  const day = today();
  if (!enabled()) return { day, skipped: 'DAILY_QUESTION is off' };
  if (!hasDb) return { day, skipped: 'SUPABASE_URL / SUPABASE_SECRET_KEY not set' };

  const result = { day, sent: 0, blocked: 0, failed: 0, users: 0 };
  let after = 0;
  for (;;) {
    // Due today: switch on, not blocked, not yet sent today. Paged by id so each page is a fresh query.
    const users = await db(`users?select=id,lang,level_id&daily_question=is.true&blocked_at=is.null` +
      `&or=(daily_sent_on.is.null,daily_sent_on.lt.${day})&id=gt.${after}&order=id&limit=500`);
    if (!users.length) break;
    after = users[users.length - 1].id;
    result.users += users.length;
    if (dry) continue;
    // The language the user picked in the app wins over users.lang (their Telegram app's language, kept by the bot).
    const chosen = await chosenLangs(users.map((u) => u.id));
    for (const u of users) u.lang = chosen[u.id] || u.lang;

    for (let i = 0; i < users.length; i += BATCH) {
      const part = users.slice(i, i + BATCH);
      const outcome = await Promise.all(part.map((u) => sendOne(u, day)));
      const ids = (k) => part.filter((_, j) => outcome[j] === k).map((u) => u.id);
      const sent = ids('sent'), blocked = ids('blocked');
      if (sent.length) await db(`users?id=in.(${sent})`, { method: 'PATCH', body: { daily_sent_on: day } });
      if (blocked.length) await db(`users?id=in.(${blocked})`, { method: 'PATCH', body: { blocked_at: new Date().toISOString() } });
      result.sent += sent.length; result.blocked += blocked.length; result.failed += outcome.length - sent.length - blocked.length;
      if (i + BATCH < users.length) await sleep(1000);
    }
  }
  return result;
}

// Sends today's question to one chat, ignoring the switches and the database — for trying it out.
export async function sendDailyTo(chatId, { lang = 'en', levelId = null } = {}) {
  return sendOne({ id: chatId, lang, level_id: levelId }, today());
}
