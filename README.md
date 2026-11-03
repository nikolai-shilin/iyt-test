# IYT Test

Practice questions for IYT certification levels — a Telegram mini app and a website. Every question is a
situation ("you see this mark ahead — where is the safe water?"), drawn as a figure where it can be, with four
options and a one-line note naming the rule. First level: **Bareboat Skipper** (100 questions, 10 topics).

Status (2026-11-02): design and question bank done; the Telegram mini app (practice, mock exam, progress, profile)
and a small bot are built and deployed (Vercel). Website not started.

## What is in the repo

```
README.md                       this file
docs/
  PLAN.md                       goal, decisions, next steps
  question-bank.md              JSON format of a bank, authoring rules, how to build it
  figures.md                    the figure spec: every type, its fields, an example
  design.md                     look & feel, components, the 21 screens, how to use the viewer
  data-model.md                 proposed database (Supabase) and how progress is computed
  design/
    flows.html                  hi-fi user flows (viewer: pages / overview, day / night)
    questions.html              the whole bank as the student sees it, filter by topic
    flows.css  flows.js         viewer + test UI pieces
    app.css                     app tokens and base components (day and night)
    test-icons.js               the app's icon set (24 grid, 2 px line) + svg()/paintIcons(), shared by the viewer and the app
    icons.html                  the icon sheet: every glyph at 24 px and in the topic circle, day / night
    icons.js                    older base set (Telegram chrome in the mockups; a few basics follow Lucide)
    figures.js                  figure generator (JSON spec → SVG)
    logo-black.svg              RYC logo
data/
  build_bank.py                 source of the Bareboat Skipper bank — edit here, then run
  build_level.py                builds the other levels from bank/<level>/<topic>.json (+ .ru.json)
  bank/<level>/<topic>.json     VHF Radio Operator, International Crew, Flotilla Skipper, Charter Check-in: 20 questions per topic; Racing Rules of Sailing: 100
  questions/<level>.json        the built banks the apps read
  questions/<level>.ru.json     Russian translation of each bank (overlay)
  i18n.py                       extract strings to translate / check an overlay
miniapp/
  index.html  app.js  app.css   the Telegram mini app (static, no framework, no backend)
  build.mjs                     copies the app + design files + banks into miniapp/dist (the folder to host)
bot/
  core.mjs                      the bot's replies: /start /exam /progress /settings open the app, /daily asks a question
  daily.mjs                     the daily question of the day to everyone who has it on
  bot.mjs                       runs core.mjs by long polling (local testing)
  scripts/setup.mjs             sets the bot's name, descriptions, commands and menu button
  scripts/webhook.mjs           points Telegram at the Vercel webhook, or removes it
api/
  telegram.mjs                  Vercel function: Telegram's webhook, runs core.mjs
  daily.mjs                     Vercel cron (09:00 UTC daily): runs bot/daily.mjs
  settings.mjs                  the app's question-of-the-day switch (users.daily_question), checked with Telegram initData
  admin.mjs                     every student's results, flagged and reported questions for the admins (ADMINS in settings.mjs — @fullcrimp; ADMIN_USERNAMES adds more)
```

## Mini app

```
npm run dev                     # http://localhost:5173 — works in a normal browser too
```

Screens follow `docs/design/flows.html`: A1–A9 practice (set-up sheet, Check → why → Next, results, mistakes),
B1–B5 mock exam (40 questions spread over all topics, timer that pauses while the app is closed, flag + grid,
pass/fail), C1 progress, C2 profile (theme, shuffle, reset). Mastery = right twice in a row. Progress is saved per
user in Telegram CloudStorage (localStorage in a browser), so there is no server or database yet. Inside Telegram
the app uses the native Back, Main and Secondary buttons and haptics; outside it draws the same bar itself.
Deep links: `?screen=exam|progress|profile|practice|level`, or `startapp=` with the same values.
Languages: English and Russian interface (follows the Telegram language until switched in Profile; the choice is saved, like the theme). All 1000 questions
are translated in `data/questions/bareboat-skipper.ru.json` (terms: [docs/glossary-ru.md](docs/glossary-ru.md)); see
[docs/question-bank.md](docs/question-bank.md#translations).

It is live at https://iyt-test.vercel.app and connected to [@iyt_test_bot](https://t.me/iyt_test_bot): the bot's
menu button opens the app, and the bot itself runs as a webhook on the same Vercel project (`api/telegram.mjs`).
To set it up again from scratch:

1. Put `TELEGRAM_BOT_TOKEN`, `WEBAPP_URL` and `TELEGRAM_WEBHOOK_SECRET` (`openssl rand -hex 32`) in `.env.local`,
   and the same three in the Vercel project's Production env.
2. `npx vercel deploy --prod` — builds `miniapp/dist` and deploys the webhook function next to it.
3. `npm run bot:setup` — name, descriptions, commands, menu button → the app.
   Then make it the bot's Main Mini App in @BotFather (Bot Settings → Configure Mini App → Enable Mini App,
   send `WEBAPP_URL`): the bot's profile gets an Open button and `t.me/iyt_test_bot?startapp=<screen>` links
   open the app straight away. Telegram has no API for this; `npm run bot:setup -- --check` shows whether it is on.
4. `npm run bot:webhook` — tells Telegram to send updates to `WEBAPP_URL/api/telegram` (`-- --check` shows its state).

To try bot changes locally: `npm run bot:webhook -- --delete`, then `npm run bot` (long polling), and
`npm run bot:webhook` again when done — Telegram delivers to a webhook or to polling, not both.

### Question of the day

Every day (Vercel cron, `0 9 * * *` UTC — 13:00 Dubai, 12:00 Moscow) the bot sends one text question with A–D
buttons to each user who has it on; the answer and the note come back in the same message. Everyone gets the same
question that day. The bot saves each user who writes to it in Supabase `users` (`daily_question` on by default).

- **Per user**: a switch button under the daily question and in `/settings` ("Question of the day: on/off").
- **Whole bot**: `DAILY_QUESTION=off` in the Vercel env stops the send for everyone (users' own switches stay).
- Users who block the bot are marked (`blocked_at`) and skipped until they write again.

Needs on Vercel: `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `CRON_SECRET` (`openssl rand -hex 32`), and the migration
`supabase/migrations/20261102150000_daily_question.sql`. Try it: `npm run bot:daily -- --to <your chat id>` (add
`--ru` for Russian) sends today's question to one chat; `npm run bot:daily -- --dry` counts who would get it.

Not in this version (needs the Supabase backend in `docs/data-model.md`): DE/ES, the
streak reminder, cross-device sync with the website, theory notes, the share image.

## Look at it

Open `docs/design/flows.html` directly in a browser for the screens. `questions.html` loads the bank JSON, so it
needs a local server:

```
npx serve docs/design          # then http://localhost:3000/questions.html
```

Arrow keys turn pages in the flows; `#A4`, `#D1` link to a screen; "Overview" shows every lane at once.

## Edit the questions

Questions live in `data/build_bank.py` as Python calls (question, right answer, three wrong ones, note, reference,
figure spec). Run it to regenerate the JSON with answers spread evenly over A–D:

```
python3 data/build_bank.py
```

Then reload `questions.html` to see them. Format and rules: [docs/question-bank.md](docs/question-bank.md).
Figure types: [docs/figures.md](docs/figures.md).

## Levels

| Level | Questions | Status |
|---|---|---|
| VHF Radio Operator | 200 (10 topics × 20) | done — `data/questions/vhf-radio-operator.json` |
| International Crew | 200 (10 topics × 20) | done — `data/questions/international-crew.json` |
| Flotilla Skipper | 200 (10 topics × 20) | done — `data/questions/flotilla-skipper.json` |
| Bareboat Skipper | 1000 (10 topics × 100) | done — `data/questions/bareboat-skipper.json` |
| Racing Rules of Sailing (not an IYT course) | 1000 (10 topics × 100) | done — `data/questions/racing-rules.json` |
| Charter Check-in (not an IYT course) | 200 (10 topics × 20) | done — `data/questions/charter-checkin.json` |
| ICC (International Certificate of Competency) | — | planned |
| Yachtmaster Coastal | 120 planned | — |
| Yachtmaster Offshore | — | 2027 |
| Yachtmaster Ocean | — | planned |

Order follows the [IYT course progression](https://www.iytworld.com/students/recreational/iyt-course-progression/);
the Racing Rules of Sailing (World Sailing, 2025–2028; Russian text ППГ-25 by the Russian Sailing Federation) come
after the IYT levels as situations on the race course — right of way, mark-room, starts, penalties, protests. The
Charter Check-in is the Saturday at the base: papers and contract, the walk-round, sails, engine, electrics, water and
gas, instruments, safety gear, ground tackle and dinghy, inventory, deposit and the Friday check-out.

Questions are written for study and are not official IYT exam content. The mock-exam defaults (Bareboat and Flotilla
Skipper 40 questions in 60 minutes, VHF and International Crew 30 in 45; 70 % to pass) must be verified against the
current IYT exams before release.
