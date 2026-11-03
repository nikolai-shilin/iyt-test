# Question bank

One JSON file per level in `data/questions/`. The Bareboat Skipper bank is generated from `data/build_bank.py`;
the JSON is what the app, the website and `docs/design/questions.html` read.

## File format

```json
{
  "level": "bareboat-skipper",
  "title": "IYT Bareboat Skipper",
  "lang": "en",
  "passMark": 70,
  "examQuestions": 40,
  "examMinutes": 60,
  "version": "2026-11-02b",
  "note": "…",
  "topics": [ { "id": "colregs", "title": "Rules of the road (COLREGs)", "count": 10 }, … ],
  "questions": [
    {
      "id": "bs-035",
      "topic": "colregs",
      "difficulty": 1,
      "q": "Two motor yachts are meeting head-on in a channel. What do you do?",
      "figure": { "type": "encounter", "you": { "hdg": 0 }, "other": { "bearing": 0, "dist": 90, "hdg": 180 }, "bearingLine": true },
      "options": [ "Stop and wait", "Hold course — the bigger one moves", "Alter course to starboard; pass port side to port side", "Alter to port" ],
      "answer": 2,
      "why": "Rule 14: both turn to starboard.",
      "ref": "COLREGs Rule 14"
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `level`, `title`, `lang` | Level slug (also the file name), display title, language of this file (`en` is the source; translations go in `question_translations`, see data-model.md). |
| `passMark`, `examQuestions`, `examMinutes` | Mock-exam defaults for the level. **To verify against the current IYT exam.** |
| `version` | Date of the last edit; bump it when questions change so the apps can re-sync. |
| `topics[]` | Ordered list; `count` is derived by the build script. Topic ids are stable — progress is keyed by them. |
| `questions[].id` | Stable id, `<level prefix>-<nnn>`. Never renumber: answers and mastery are keyed by it. |
| `difficulty` | 1 recall · 2 apply · 3 combine (a calculation, two rules at once, a judgement call). |
| `q` | The situation, written to the student ("You are…", "You see…"). Second person, present tense, no definitions. |
| `figure` | A spec for `docs/design/figures.js`, or `null` for a text-only question. See figures.md. |
| `options[]` | Exactly four. The build script shuffles the three wrong ones and places the right one so that A/B/C/D are used equally across the bank. The apps may shuffle again per session. |
| `answer` | Index of the right option (0–3). |
| `why` | One line, shown after answering. Names the rule or the reason — the situation was in the figure. |
| `ref` | Short reference: a COLREGs rule, a syllabus heading, a chart topic. Links to the theory note for the topic. |

## Topics of the Bareboat Skipper bank

| id | Title | Figures used |
|---|---|---|
| `terms` | Nautical terms & parts of the boat | sail, anchor, rope |
| `ropework` | Ropework & knots | rope |
| `safety` | Safety equipment & procedures | card, encounter |
| `colregs` | Rules of the road (COLREGs) | encounter, lights, dayshape |
| `navigation` | Charts, compass & position | compass, chart |
| `buoyage` | Buoyage & lights | buoy, lights |
| `weather` | Weather | isobars, bay, card |
| `anchoring` | Anchoring & mooring | anchor, bay, chart, dayshape |
| `systems` | Engine, electrics & boat systems | panel, card, encounter |
| `emergency` | VHF, distress & emergencies | card, encounter |

## Authoring rules

1. **A situation, not a definition.** "The anchorage shows 2.4 m at low water, your draft is 1.9 m — can you stay?"
   rather than "What is draft?". If the question could be answered by someone who has only read a glossary, rewrite it.
2. **Draw it when it can be drawn.** A mark, a set of lights, the other boat's bearing, a compass rose, a chart
   extract, a gauge panel. Use `card` for situations that are a short list of facts (fire below, barometer readings,
   what flares you have). Leave `figure` null only for procedures and choices with nothing to see (which knot, which
   rope, which VHF call).
3. **Put the facts in the figure, not in the question.** If the figure says "Height of tide 1.2 m", the question does
   not repeat it. The question asks; the figure tells.
4. **Four options, one clearly right.** Wrong options are plausible mistakes a beginner makes (the opposite rule, the
   right idea at the wrong moment), never jokes. Keep options the same length and shape so the right one does not stand
   out. No "all of the above".
5. **`why` is one line.** The rule and nothing else: "Rule 12: port tack keeps clear of starboard tack." The place for
   a paragraph is the theory note the `ref` points to.
6. **Mediterranean first.** Examples use IALA region A, Med mooring, Meltemi, Greek and Turkish harbours — where the
   students sail. Region B is mentioned where it matters (lateral marks).
7. **Spread difficulty.** About 2 × difficulty 1, 6 × difficulty 2, 2 × difficulty 3 per topic of ten.
8. **Never claim exam content.** The bank is close to the syllabus, written from scratch. No question is copied from an
   IYT paper, and the apps show the disclaimer once (profile / footer).

## Building

```
python3 data/build_bank.py
```

The bank has 1000 questions, 100 per topic. The first 100 (`bs-001`–`bs-100`, ten per topic) are
`q(topic, difficulty, text, right, [wrong ×3], why, ref, figure)` calls in the script. The other 90 per topic live in
`data/bank/<topic>.json`: an array of `{topic, difficulty, q, a, o, why, ref, fig}` objects with the same meaning. The
script appends the topic files in topic order (`bs-101`–`bs-190` terms, `bs-191`–`bs-280` ropework, … ), asserts there
are 1000, places the right answer at position `i % 4`, and writes the JSON. It prints the count, how many have figures,
and the answer distribution. Edit the script or the topic files, not the built JSON. Ids come from position, so fix a
question in place but never insert, delete or reorder one in a topic file — that renumbers everything after it. More
questions go in a new batch appended after the current ones.

Before building, check a topic file:

```
python3 data/check_topic.py <topic>
```

It checks the shape, the difficulty spread (about 18/54/18 of 90), near-duplicates within the file and against the
first 100, right answers that stand out by length, and that every figure renders with `figures.js` (needs Node).

## Other levels

VHF Radio Operator (`vhf-`), International Crew (`ic-`), Flotilla Skipper (`fs-`), Racing Rules of Sailing
(`rr-`) and Charter Check-in (`ci-`) are built by `data/build_level.py`, which also holds their topic lists, exam defaults and topic icons. Each
topic is `data/bank/<level>/<topic>.json` (20 questions, about 4/12/4 by difficulty; 100 and 20/60/20 for the
Racing Rules — `per` in `LEVELS`) with its Russian text beside it in
`<topic>.ru.json`: the same order, `{q, a, o, why, ref, fig}`, where `o` keeps the English order of the wrong options and
`fig` maps figure text paths to the translation. The build shuffles the options once and writes both
`data/questions/<level>.json` and the overlay `data/questions/<level>.ru.json` in that same order.

```
python3 data/check_topic.py <level> <topic>    # shape, spread, duplicates in the level, figures, the Russian file
python3 data/build_level.py [<level>]
```

To add a level: add it to `LEVELS` in `build_level.py`, write its topic files, build, then add its `id`, `prefix` and
deep-link name to `LEVELS` in `miniapp/app.js` and `bot/core.mjs`, a row to `public.levels` (a migration, as
`20261103120000_racing_rules_level.sql`) and its topic icons to `TOPIC_ICONS` in the app.

### Racing Rules of Sailing

Not an IYT course: the Racing Rules of Sailing 2025–2028 (World Sailing) as situations on the race course, 10 topics
× 100 — definitions, right of way (10–13), general limitations (14–17), mark-room (18), obstructions and Section D
(19–23), starting, sailing the course, Part 4 (propulsion and the rest), penalties (44), protests and scoring. The
Russian text follows the official translation ППГ-25 (Russian Sailing Federation); `ref` cites `RRS 18.2(b)` /
`ППГ 18.2(b)`. Most drawn questions use the `race` figure (figures.md): wind, boats on their tacks, a mark with its
zone, a start line, an obstruction. The level's title and note are its own (`title`, `note` in `LEVELS`), and the
app's disclaimer and share text name World Sailing instead of IYT for it.

### Charter Check-in

Not an IYT course: the Saturday at a Mediterranean charter base, as the skipper taking over a bareboat, 10 topics
× 20 — documents, contract and briefing; the hull, deck and rigging walk-round; sails and furling; engine and fuel;
batteries and shore power; water, gas, heads and bilge; instruments and VHF; safety equipment; anchor, mooring gear
and dinghy; inventory, deposit and the Friday check-out. The right answer is what a careful skipper does at the
base — tests it, notes it on the form, photographs it, has the base fix it before leaving, signs last. Anything that
varies by company (deposit, cruising limits, fuel policy, return time) is stated inside the figure as the contract
or the briefing, never as a general fact. Figures are mostly `card` (the form, the inventory, the readings),
`panel` (gauges), `rope`, `anchor`, `bay` and `lights` (the navigation-light test at the pontoon). The app's
disclaimer, exam note and share text name the contract and the base's briefing as the authority for it.

## Translations

The source language is English (the exam language). A translation is an overlay file
`data/questions/<level>.<lang>.json` holding only translated text, keyed by question id, in the source's option
order (so answers, progress and exams keyed by option index stay valid). Figure text is addressed by its path inside
the figure spec — `note`, `lines.1`, `labels.0.2`, `lights.1.t`, `gauges.0.0`, `you.label` — so a translation can
never move a coordinate. `topics` gives the topic titles, `short` the short names used on chips and buttons.

```
python3 data/i18n.py extract bareboat-skipper > /tmp/to-translate.json   # every string, in overlay shape
python3 data/i18n.py check bareboat-skipper ru                           # what is missing, wrong or out of date
```

The mini app and the bot load the overlay for the reader's language and fall back to English per question, so a
partial translation is safe to ship. `source` records the bank version the overlay was made from; `check` warns
when the bank has moved on. Built-in figure labels ("You", "wind", "Variation"…) are translated in the app
(`FIG_RU` in `miniapp/app.js`, via `FIG_TEXT` in figures.js) and used only on translated questions.

Status: `bareboat-skipper.ru.json` covers all 1000 questions (bank version 2026-11-02d). Terms and style for new or
changed questions: [glossary-ru.md](glossary-ru.md). After editing the bank, run `check` — it lists what to translate.
