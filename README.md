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
    icons.js                    base icon set (24 grid, 2 px line)
    figures.js                  figure generator (JSON spec → SVG)
    logo-black.svg              RYC logo
    test-icons.js               test glyphs + svg()/paintIcons(), shared by the viewer and the app
data/
  build_bank.py                 source of the Bareboat Skipper bank — edit here, then run
  build_level.py                builds the other levels from bank/<level>/<topic>.json (+ .ru.json)
  bank/<level>/<topic>.json     VHF Radio Operator, International Crew, Flotilla Skipper: 20 questions per topic
  questions/<level>.json        the built banks the apps read
  questions/<level>.ru.json     Russian translation of each bank (overlay)
  i18n.py                       extract strings to translate / check an overlay
miniapp/
  index.html  app.js  app.css   the Telegram mini app (static, no framework, no backend)
  build.mjs                     copies the app + design files + banks into miniapp/dist (the folder to host)
bot/
  core.mjs                      the bot's replies: /start /exam /progress /settings open the app, /daily asks a question
  bot.mjs                       runs core.mjs by long polling (local testing)
  scripts/setup.mjs             sets the bot's name, descriptions, commands and menu button
  scripts/webhook.mjs           points Telegram at the Vercel webhook, or removes it
api/
  telegram.mjs                  Vercel function: Telegram's webhook, runs core.mjs
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
Languages: English and Russian interface (picked from the Telegram language, switch in Profile). All 1000 questions
are translated in `data/questions/bareboat-skipper.ru.json` (terms: [docs/glossary-ru.md](docs/glossary-ru.md)); see
[docs/question-bank.md](docs/question-bank.md#translations).

It is live at https://iyt-test.vercel.app and connected to [@iyt_test_bot](https://t.me/iyt_test_bot): the bot's
menu button opens the app, and the bot itself runs as a webhook on the same Vercel project (`api/telegram.mjs`).
To set it up again from scratch:

1. Put `TELEGRAM_BOT_TOKEN`, `WEBAPP_URL` and `TELEGRAM_WEBHOOK_SECRET` (`openssl rand -hex 32`) in `.env.local`,
   and the same three in the Vercel project's Production env.
2. `npx vercel deploy --prod` — builds `miniapp/dist` and deploys the webhook function next to it.
3. `npm run bot:setup` — name, descriptions, commands, menu button → the app.
4. `npm run bot:webhook` — tells Telegram to send updates to `WEBAPP_URL/api/telegram` (`-- --check` shows its state).

To try bot changes locally: `npm run bot:webhook -- --delete`, then `npm run bot` (long polling), and
`npm run bot:webhook` again when done — Telegram delivers to a webhook or to polling, not both.

Not in this version (needs the Supabase backend in `docs/data-model.md`): DE/ES, scheduled daily question
and streak reminder, cross-device sync with the website, theory notes, the share image.

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
| ICC (International Certificate of Competency) | — | planned |
| Yachtmaster Coastal | 120 planned | — |
| Yachtmaster Offshore | — | 2027 |
| Yachtmaster Ocean | — | planned |

Order follows the [IYT course progression](https://www.iytworld.com/students/recreational/iyt-course-progression/).

Questions are written for study and are not official IYT exam content. The mock-exam defaults (Bareboat and Flotilla
Skipper 40 questions in 60 minutes, VHF and International Crew 30 in 45; 70 % to pass) must be verified against the
current IYT exams before release.
