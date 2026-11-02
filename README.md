# IYT Test

Practice questions for IYT certification levels — a Telegram mini app and a website. Every question is a
situation ("you see this mark ahead — where is the safe water?"), drawn as a figure where it can be, with four
options and a one-line note naming the rule. First level: **Bareboat Skipper** (100 questions, 10 topics).

Status (2026-11-02): design and question bank done; the Telegram mini app (practice, mock exam, progress, profile)
and a small bot are built, not yet deployed. Website not started.

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
  questions/bareboat-skipper.json
miniapp/
  index.html  app.js  app.css   the Telegram mini app (static, no framework, no backend)
  build.mjs                     copies the app + design files + banks into miniapp/dist (the folder to host)
bot/
  bot.mjs                       long-polling bot: /start /exam /progress /settings open the app, /daily asks a question
  scripts/setup.mjs             sets the bot's name, descriptions, commands and menu button
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

To put it in Telegram:

1. `npm run build` and host `miniapp/dist` on any HTTPS static host (e.g. `npx vercel deploy miniapp/dist`).
2. Put the URL in `.env.local` as `WEBAPP_URL`, then `npm run bot:setup` — the bot's menu button opens the app.
3. Optional: `npm run bot` on a machine that stays on, so the commands and the daily question answer.

Not in this version (needs the Supabase backend in `docs/data-model.md`): translations, scheduled daily question
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
| Bareboat Skipper | 100 (10 topics × 10) | done — `data/questions/bareboat-skipper.json` |
| International Crew | 60 planned | — |
| Yachtmaster Coastal | 120 planned | — |
| Yachtmaster Offshore | — | 2027 |

Questions are written for study and are not official IYT exam content. The exam defaults in the app (40 questions,
60 minutes, 70 % to pass) must be verified against the current IYT exam before release.
