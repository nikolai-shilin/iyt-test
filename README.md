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
  figure-style.md               the agreed look of the rendered figures (cameras, looks, own boat, lights, annotations)
  design.md                     look & feel, components, the 21 screens, how to use the viewer
  data-model.md                 proposed database (Supabase) and how progress is computed
  theory.md                     the theory articles: format of an article, authoring rules, check and build
  superpowers/plans/            implementation plans (theory articles: 2026-11-05-theory-articles.md)
  design/
    flows.html                  hi-fi user flows (viewer: pages / overview, day / night)
    questions.html              the whole bank as the student sees it, filter by topic
    flows.css  flows.js         viewer + test UI pieces
    app.css                     app tokens and base components (day and night)
    test-icons.js               the app's icon set (24 grid, 2 px line) + svg()/paintIcons(), shared by the viewer and the app
    icons.html                  the icon sheet: every glyph at 24 px and in the topic circle, day / night
    icons.js                    older base set (Telegram chrome in the mockups; a few basics follow Lucide)
    figures.js                  figure generator (JSON spec → SVG)
    figure-style-spike.html     reference renderer for figure-style.md (three.js from a CDN; open over HTTP)
    figure-schematic.js         plan-view schematic renderer (the companion diagram to every realistic figure)
    figure-style/               sample renders of the ten example questions; hires/ at 2560 × 1600, schematic/ their plan views
    logo-black.svg              RYC logo
data/
  build_bank.py                 source of the Bareboat Skipper bank — edit here, then run
  build_level.py                builds the other levels from bank/<level>/<topic>.json (+ .ru.json)
  bank/<level>/<topic>.json     VHF Radio Operator, International Crew, Flotilla Skipper: 20 questions per topic; Charter Check-in: 50; Yachtmaster Coastal, Offshore and Ocean, Racing Rules of Sailing: 100
  questions/<level>.json        the built banks the apps read
  questions/<level>.ru.json     Russian translation of each bank (overlay)
  i18n.py                       extract strings to translate / check an overlay
  theory/<level>/<topic>.json   theory articles, one per topic of every level (+ .ru.json): 90 in all, each with figures
  check_theory.mjs              checks the articles against docs/theory.md and the banks (npm run check:theory)
miniapp/
  index.html  app.js  app.css   the Telegram mini app (static, no framework, no backend)
  build.mjs                     builds miniapp/dist (the folder to host): the app, design files, fonts and minified banks,
                                each linked file renamed after its content (h/…) so phones cache it for good, and the
                                list of banks written into index.html so only the current level's bank loads at start
  fonts/                        Merriweather and Carlito (woff2, Latin + Cyrillic, OFL), served with the app
  pages.mjs  site.css            the site around the app: a page per level and per theory article (EN + RU), sitemap, llms.txt
  site.mjs                      the public address, the bot and the IndexNow key
  indexnow.mjs                  npm run seo:ping: tells Bing and Yandex which pages changed
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
  admin.mjs                     every student's results, flagged and reported questions (admins can take a flag off), joins/answers/wrong answers per hour and day for the admins (ADMINS in settings.mjs — @fullcrimp; ADMIN_USERNAMES adds more)
  mcp.mjs                       the MCP server: the banks and the theory articles as tools for AI assistants (public, read-only)
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

It is live at https://iyt.rycrentals.com and connected to [@iyt_test_bot](https://t.me/iyt_test_bot): the bot's
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

### Search engines and AI assistants

Search engines and most AI crawlers read a page without running its JavaScript, so next to the app the build writes
the site as plain pages (`miniapp/pages.mjs`, styled by `miniapp/site.css` over the app's own CSS), at
https://iyt.rycrentals.com (`SITE` in `miniapp/site.mjs`):

| Address | Page |
|---|---|
| `/` | the app; its `<noscript>` copy of Home links every level |
| `/<level>` | the level: questions, topics, the mock exam, every topic with its article |
| `/<level>/<topic>` | the topic's theory article with its drawings, then sample questions (one per section, a drawn one where there is one) with the answer, the note and a link to the section that explains it |
| `/about` | what IYT Test is and is not, the author, the MCP server |
| `/ru`, `/ru/<level>`, `/ru/<level>/<topic>`, `/ru/about` | the same in Russian; `/ru` lists the levels |

Every page has its own title and description, a canonical link, `hreflang` links to its other language, link
preview tags and structured data (breadcrumbs; `Article` and `Quiz` on a topic). Nothing is written by hand but the
strings in `pages.mjs`: a new article or a new level gets its pages on the next build. A section's opener (`qa` in
[docs/theory.md](docs/theory.md): the question a student would ask, answered in a sentence or two) goes under its
heading and into the page's `FAQPage` data, the passage search engines and AI assistants quote. The build also writes
`robots.txt` (AI crawlers named and let in, search and training alike: the content is free and the MCP server gives it out anyway), `sitemap.xml` (every page with its other language), `llms.txt` (the site's map for AI assistants),
`404.html`, the IndexNow key file and `pages.json` (each address with a hash of its page). `npm run dev` serves the
pages at their clean addresses, as Vercel does (`cleanUrls`).

After a production deploy:

- `npm run seo:ping` tells Bing and Yandex (IndexNow) which pages are new, changed or gone since the last ping (the
  live `pages.json` against `miniapp/.indexnow-sent.json`, which is not in git); `-- --dry` lists them, `-- --all`
  sends every page, `-- --check` only checks the key file is live.
- Once, by hand (each needs your account): add `iyt.rycrentals.com` in [Google Search Console](https://search.google.com/search-console),
  verify it with the DNS TXT record it gives (on the `rycrentals.com` zone), and submit `sitemap.xml`; then
  [Bing Webmaster Tools](https://www.bing.com/webmasters) → Import from Google Search Console; then
  [Yandex Webmaster](https://webmaster.yandex.com) → add the site, verify (DNS or meta tag), add the sitemap.

## MCP server

`api/mcp.mjs` gives the question banks and the theory articles to AI assistants (Claude, ChatGPT and anything else
that speaks the [Model Context Protocol](https://modelcontextprotocol.io)): a student adds
`https://iyt.rycrentals.com/api/mcp` as a remote MCP server (a custom connector) and practises in their own
assistant. It is public and read-only: no sign-in, nothing is saved, and it returns only what the app already serves.
What the site, the app, the bot and the server keep about people is on https://iyt.rycrentals.com/privacy (the
strings in `miniapp/pages.mjs`, `privBody`): change it there when any of them starts keeping something new.

| Tool | What it gives |
|---|---|
| `list_levels` | the levels, their topics, exam settings and which topics have an article |
| `get_questions` | random questions of a level, a topic or a difficulty, without the answers |
| `check_answer` | right or wrong, the right option, the note, and the theory section that explains it |
| `search_questions` | questions by words |
| `start_mock_exam`, `grade_exam` | an exam-sized set spread over the topics; then the score, pass or fail, the mistakes and what to read |
| `question_of_the_day` | the question the bot sends that day |
| `list_theory`, `get_theory`, `search_theory` | the articles and their sections, as text with links to the drawings |
| `explain_question` | a question with its answer and the section behind it |
| `practice_section` | the questions a theory section covers |
| `get_figure` | a drawing as SVG markup |

Every tool takes `lang` (`en` or `ru`); what is not translated yet comes in English. A drawing has an address of
its own, `/api/mcp?figure=bs-001` for a question and `/api/mcp?figure=<level>/<topic>/<section>/<n>` for the nth
figure of a theory section: an SVG image drawn by `docs/design/figures.js` with the day colours written in. Card
figures (a script, a checklist) go out as text.

No dependencies and no state: the function answers JSON-RPC over HTTP (`initialize`, `tools/list`, `tools/call`) and
reads the banks, the articles and `figures.js` bundled with it (`vercel.json` → `includeFiles`), so a deploy puts new
articles in front of the assistants. Try it against a deployment:

```
curl -s https://iyt.rycrentals.com/api/mcp -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_questions","arguments":{"level":"bareboat-skipper","count":1}}}'
```

It is listed in the [official MCP Registry](https://registry.modelcontextprotocol.io) as
`io.github.nikolai-shilin/iyt-test`, from `server.json` (Glama and PulseMCP copy the registry). A
new tool or a changed description goes out with a new `version` (also `serverInfo.version` in `api/mcp.mjs`): a
published version cannot be changed.

```
brew install mcp-publisher
mcp-publisher validate
mcp-publisher login github      # as nikolai-shilin: the name must start with io.github.<your GitHub login>/
mcp-publisher publish
```

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
| Charter Check-in (not an IYT course) | 500 (10 topics × 50) | done — `data/questions/charter-checkin.json` |
| ICC (International Certificate of Competency) | — | planned |
| Yachtmaster Coastal | 1000 (10 topics × 100) | done — `data/questions/yachtmaster-coastal.json` |
| Yachtmaster Offshore | 1000 (10 topics × 100) | done — `data/questions/yachtmaster-offshore.json` |
| Yachtmaster Ocean | 1000 (10 topics × 100) | done — `data/questions/yachtmaster-ocean.json` |

Order follows the [IYT course progression](https://www.iytworld.com/students/recreational/iyt-course-progression/);
the Racing Rules of Sailing (World Sailing, 2025–2028; Russian text ППГ-25 by the Russian Sailing Federation) come
after the IYT levels as situations on the race course — right of way, mark-room, starts, penalties, protests. The
Charter Check-in is the Saturday at the base: papers and contract, the walk-round, sails, engine, electrics, water and
gas, instruments, safety gear, ground tackle and dinghy, inventory, deposit and the Friday check-out.

Questions are written for study and are not official IYT exam content. The mock-exam defaults (Bareboat and Flotilla
Skipper 40 questions in 60 minutes, Yachtmaster Coastal and Offshore 50 in 90, Yachtmaster Ocean 50 in 120, VHF and International Crew 30 in 45; 70 % to pass) must be verified against the
current IYT exams before release.
