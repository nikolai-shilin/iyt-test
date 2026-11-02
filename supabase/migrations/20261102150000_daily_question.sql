-- Question of the day in the bot (bot/daily.mjs, run each morning by the Vercel cron api/daily.mjs).
-- users.daily_question (default true) is the user's own switch: /settings or the button under the question.
-- The bot writes users with the secret key; nobody else can (no RLS policies on users).

alter table public.users
  add column daily_sent_on date,         -- last UTC day the question was sent; a second run that day skips the user
  add column blocked_at    timestamptz;  -- Telegram said the user blocked the bot; cleared by their next message
