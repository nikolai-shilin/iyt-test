# Data model

Proposed schema (Postgres / Supabase), one database behind the mini app, the bot and the website. Not created yet.

## Tables

```sql
-- catalogue (read-only for users; filled from data/questions/*.json)
levels               id text pk, title text, sort int, pass_mark int, exam_questions int, exam_minutes int, available bool
topics               id text pk, level_id → levels, title text, sort int
questions            id text pk, level_id → levels, topic_id → topics, difficulty int, q text,
                     figure jsonb null, options jsonb (text[4]), answer int, why text, ref text, version text
question_translations question_id → questions, lang text, q text, options jsonb, why text, figure_text jsonb,
                     pk (question_id, lang)
theory_notes         id serial, topic_id → topics, lang text, title text, body_md text

-- people
users                id bigint pk (telegram id), name text, username text, lang text default 'en',
                     theme text, level_id → levels, daily_question bool default true, reminder bool default true,
                     shuffle bool default true, created_at
web_sessions         id uuid pk, user_id → users null, created_at            -- anonymous website progress until login

-- activity
answers              id bigserial, user_id → users, question_id → questions, option int, correct bool,
                     mode text ('practice' | 'exam' | 'daily'), session_id uuid null, at timestamptz
sessions             id uuid pk, user_id, level_id, mode text, topic_ids text[], size int, feedback bool,
                     started_at, finished_at null, score int null
exam_sessions        id uuid pk, user_id, level_id, question_ids text[40], flags text[], started_at,
                     paused_at null, submitted_at null, score int null, passed bool null
flags                user_id, question_id, at   pk (user_id, question_id)
```

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

A script (`data/load.py`, to write) upserts `levels`, `topics`, `questions` from the JSON files and bumps
`questions.version`. The apps cache the catalogue by `version`. Figures are stored as the JSON spec and rendered on
the client by `figures.js` — no image files.

## Notes

- Row-level security: a user reads the catalogue and only their own rows in `users`, `answers`, `sessions`,
  `exam_sessions`, `flags`. Telegram `initData` is verified in an edge function that issues the session.
- Reporting a question: a `reports(user_id, question_id, text, at)` table and a button in the ••• menu.
- Share card for a passed exam: rendered server-side (1080 × 1080) from `exam_sessions` and sent by the bot.
