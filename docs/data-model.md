# Data model

One Postgres database behind the mini app, the bot and the website: Supabase project **iyt-test**
(`xpdhkahgvusuicynssxq`, eu-north-1, https://xpdhkahgvusuicynssxq.supabase.co). Created 2026-11-02.

The schema lives in `supabase/migrations/` (apply new files in order with the Supabase dashboard SQL editor, the MCP
`apply_migration` tool or `supabase db push`).

**What is in it now:** the catalogue — 8 levels (Bareboat Skipper `available`, the rest `planned`/`soon`), its 10 topics,
1000 questions and their Russian translations, loaded from `data/questions/*.json`. The progress tables exist but are
empty: progress still lives on each student's device (Telegram CloudStorage), so there is nothing to move until the
app writes to the database.

**Who reads it:** the mini app (`fetchBank` in `miniapp/app.js`, with the publishable key) and the bot (`read` in
`bot/core.mjs`, with `SUPABASE_URL` + a key from the env) call `bank(level)` and `bank_overlay(level, lang)`, which
return exactly the shape of the JSON files. If the database does not answer within 8 s or has no such level, both fall
back to the JSON files (the app's static `data/` folder, the files bundled into the Vercel functions).

**Source of truth:** still the JSON files built by `data/build_bank.py` / `data/build_level.py`. After changing a bank,
run `npm run db:load` — until then the apps keep showing the old version from the database.

## Tables

```sql
-- catalogue (anyone may read it with the publishable key; written only by load_bank())
levels                id text pk, prefix text, link text, title, sort, status ('available'|'planned'|'soon'|'soon2027'),
                      pass_mark, exam_questions, exam_minutes, version, note, updated_at
topics                (level_id, id) pk, title, icon, sort
questions             id text pk, level_id, topic_id → topics, sort, difficulty 1–3, q, figure jsonb null,
                      options jsonb (text[4]), answer 0–3, why, ref, active bool, updated_at
level_languages       (level_id, lang) pk, source_version, note            -- one row per overlay file
topic_translations    (level_id, topic_id, lang) pk, title, short
question_translations (question_id, lang) pk, q, options, why, ref, figure  -- null field = use English;
                                                                            -- figure = translated text fields only

-- progress (RLS on, no policies yet: only the server with the secret key can read or write)
users                 id bigint pk (telegram id), name, username, lang, theme, level_id, shuffle, feedback,
                      daily_question, reminder, created_at, updated_at
answers               id bigint identity, user_id, question_id, option 0–3 null, correct, mode ('practice'|'exam'|'daily'),
                      exam_id → exam_sessions null, at
exam_sessions         id uuid pk, user_id, level_id, question_ids text[], flags text[], started_at, paused_at,
                      submitted_at, score, passed
flags                 (user_id, question_id) pk, at
reports               id, user_id null, question_id, text, at, resolved_at
```

Not created yet (add when a feature needs them): `theory_notes`, `web_sessions` (anonymous website progress),
practice `sessions`, the `mastery` materialised view.

## Derived values

- **Mastered question** = the last two answers by this user are both correct. Computed from `answers`, cached in a
  materialised view `mastery(user_id, question_id, mastered bool, wrong_count int)`.
- **Topic mastery** = mastered / total questions of the topic. Under 50 % = weak (red, preselected for practice).
- **Mistakes list** = questions with at least one wrong answer and not currently mastered.
- **Streak** = consecutive days (user's local date) with at least one answer in `answers`.
- **Session score** = correct / size; **exam score** = correct / 40, `passed = score ≥ pass_mark`.
- Unanswered exam questions at submit count as wrong. An exam can be paused once (`paused_at`) for up to 24 h.

## Flows against the schema

| Screen | Reads | Writes |
|---|---|---|
| A1 Home | levels, mastery per level, streak | — |
| A2 Level | topics + topic mastery | — |
| A3 Set up | topics, mistakes count | `sessions` row |
| A4–A6 Question | question (+ translation), figure | `answers` row per answer; `flags` |
| A8 Results | answers of the session grouped by topic | `sessions.finished_at, score` |
| B1–B5 Exam | `exam_sessions` | `exam_sessions`, `answers` with `mode='exam'` |
| C1 Progress | mastery, answers per day, mistakes | — |
| C2 Profile | users | users |
| C3 Bot daily question | one question not mastered, weighted to weak topics | `answers` with `mode='daily'` |
| D1–D4 Website | same, keyed by `web_sessions` until Telegram login merges it into `users` | same |

## Loading the bank

`data/load.mjs` sends each `data/questions/<level>.json` with its `<level>.<lang>.json` overlays to the database
function `load_bank(bank, overlays)`. It sets the level `available` with its exam settings and version, upserts topics,
questions and translations, and marks questions that left the bank `active = false` (answers keep pointing at them).
Rerunning it changes nothing if the files did not change.

```
npm run db:load                       # every level in data/questions
npm run db:load -- flotilla-skipper   # one level
```

It needs `SUPABASE_URL` and `SUPABASE_SECRET_KEY` (dashboard → Project Settings → API keys) in `.env.local`. Only
the secret key may run `load_bank`. A new level must first have a row in `levels` (the eight IYT levels are there).
Figures are stored as the JSON spec and rendered on the client by `figures.js` — no image files.

## Notes

- Row-level security: a user reads the catalogue and only their own rows in `users`, `answers`, `sessions`,
  `exam_sessions`, `flags`. Telegram `initData` is verified in an edge function that issues the session.
- Reporting a question: a `reports(user_id, question_id, text, at)` table and a button in the ••• menu.
- Share card for a passed exam: rendered server-side (1080 × 1080) from `exam_sessions` and sent by the bot.
