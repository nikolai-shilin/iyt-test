# IYT Test — Telegram mini app + website (plan)

Date: 2026-11-02. Status: **design + first question bank done; mini app built (`miniapp/`, static, progress in Telegram CloudStorage), not deployed.**

Goal: close-to-real practice questions for every IYT certification level, as a Telegram mini app (its own bot) and a
website, so students arrive at the theory exam already used to the paper.

Look and feel: **website** — Merriweather Light display, Carlito
kickers, one blue accent, 28px bands, 1180 wrap); **mini app** — the same tokens in Telegram mini-app chrome (`docs/design/app.css`,
day and night).

**Hi-fi user flows:** [docs/design/flows.html](design/flows.html) — 21 screens (mini app practice A1–A9, mock exam
B1–B5, progress/profile/bot C1–C3, website D1–D4), one per page with an index, or all at once in "Overview", day and
night. Open the file directly or serve `docs/design` (`npx serve docs/design` → `/flows.html#A4`). The viewer is in `flows.js`,
the base icon set in `icons.js`, test-specific glyphs in `flows.js`.

**Question bank:** [data/questions/bareboat-skipper.json](../data/questions/bareboat-skipper.json), built by
`data/build_bank.py` — 100 scenario questions ("you see this — what do you do?"), 10 topics × 10, 62 with a drawn
figure (`figure` = a JSON spec rendered by `docs/design/figures.js`: buoy, lights, encounter, compass, chart, anchor,
isobars, sail, dayshape, bay, panel, card, rope), four options (correct answers evenly spread over A–D), a one-line
`why` and a reference, difficulty 1–3. Review them all in [docs/design/questions.html](design/questions.html)
(serve the folder over HTTP). Written for study, not official IYT content; the pass mark (70 %), exam size (40) and time (60 min) are
app defaults to verify against the current IYT exam before release.

## Decisions (first draft)

1. **One bank, two front ends.** Questions, topics and progress live in one database; the mini app and the website
   render the same components (question card, option rows, topic rows with the mastery bar, result ring).
2. **Mastery per question**: right twice in a row = mastered; a wrong answer puts the question back in rotation. Topic
   mastery = mastered / total. Under 50 % = "weak" (red bar, preselected for practice).
3. **Two modes.** Practice: any topics, 10/20/all, explanation after every answer (or silent). Mock exam: 40 random
   questions over all topics, 60 min, flag + grid navigation, feedback only after submit, pass at 70 %.
4. **Retention**: daily question as an inline keyboard in the bot (answer without opening the app), streak, evening
   reminder. Both notifications off in one tap.
5. **Languages**: en (source), ru, de, es — `question_translations` per question.
6. **Figures** (buoys, lights, chart symbols) are our own SVGs in theme tokens + buoy yellow/red/green; no photos.
7. **One band, no promo**: theory notes (home, profile, level page) or the next level (passed exam). Nothing on
   questions. No affiliation with any school or brand.

## Docs

`README.md` (what and how to run) · `docs/question-bank.md` (format, authoring rules, build) · `docs/figures.md`
(figure spec reference) · `docs/design.md` (look, components, screens, viewer) · `docs/data-model.md` (proposed schema).

## Next

- Question banks done: VHF Radio Operator, International Crew, Flotilla Skipper (200 each, English + Russian),
  Bareboat Skipper (1000). Next: Yachtmaster Coastal; review the new banks with an instructor.
- Schema: `levels`, `topics`, `questions`, `question_translations`, `answers`, `exam_sessions`, `users` (Supabase).
- Deploy `miniapp/dist` over HTTPS, set `WEBAPP_URL`, run `npm run bot:setup`.
- Backend (Supabase) for the daily question schedule, reminders, translations and website sync; then the website.
