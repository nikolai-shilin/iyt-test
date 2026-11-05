# Theory Articles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Theory section in the mini app: one illustrated article per topic of every course (9 courses × 10 topics, English and Russian), reached from a Theory item in the bottom menu.

**Architecture:** Each article is a JSON file per topic and language under `data/theory/<level>/`. `miniapp/build.mjs` packs a course's articles into one file per language, content-named like the question banks, and writes the list into `index.html` as `window.THEORY`. The app loads a course's theory on demand and renders it with the figure generator the questions already use (`docs/design/figures.js`).

**Tech Stack:** Static mini app (plain JS, no framework), Node 20 build script, figures as JSON specs → SVG.

**Spec:** No separate spec. The design was agreed in chat on 2026-11-05 and is recorded in "Design decisions" below; the mockup is `.superpowers/brainstorm/10014-1793848871/content/topic-page-v2.html` (design A, the article). The article format and authoring rules are `docs/theory.md` (Task 1).

## Design decisions

- **Asked for by Nikolai:** a theory section; articles for each course; illustrations in each topic; every course's theory split into a separate page per topic; a Theory item in the bottom menu.
- **Claude's calls** (Nikolai did not pick between the three mockups): the topic page is design A, one article read top to bottom; sections follow the `ref` values of the question bank, so the reference chip under an answered question opens the matching section; the page ends with "Practise this topic"; read marks are kept with the progress; illustrations come from `figures.js`, with new figure types added where a topic has nothing to draw with (first: `boat`).
- The Theory tab shows the current course's ten topics and a row of chips to change course. A course whose articles are not written yet says so.
- Tab order: Learn, Theory, Exam, Progress, Profile.

## Global Constraints

- English is the source; Russian follows `docs/glossary-ru.md` and must read like a Russian sailing textbook.
- An article teaches what the topic's questions ask: every `ref` used by ten or more questions of the topic is covered by a section.
- 4–7 sections and 400–900 words per article; at least 4 pictures per article and at least one picture or table in every section.
- Figures are `figures.js` specs only: no photos, no external images, no inline SVG in articles.
- Written for study, not official IYT content: no claim of being the IYT syllabus; facts follow COLREGs, IALA and standard practice.
- Colours and type come from the app's tokens (`docs/design/app.css`); every screen must read in day and night themes and at 320 px width.
- Another Claude session may be editing this checkout: check `git status --short` and file mtimes before editing shared files, patch by exact match, never commit unasked (commit steps below wait for Nikolai's word).

## Review Focus

- A course with no theory yet (8 of 9 at first): the Theory tab says it is being written, nothing breaks, the ref chip under a question stays a plain chip.
- Russian chosen but only the English article exists: the English article is shown, never an empty page.
- Theory file fails to download (offline): the tab shows an error line with Retry, the rest of the app keeps working.
- A `ref` that no section lists: the chip opens the article at the top.
- A saved state from before this change (no `read` field) loads without error.

---

### Task 1: Article format, build and checker

**Files:**
- Create: `docs/theory.md`, `data/check_theory.mjs`
- Modify: `miniapp/build.mjs`, `package.json` (script `check:theory`)

**Interfaces:**
- Produces: article source `data/theory/<level>/<topic>.json` and `<topic>.ru.json`:
  `{ topic, lead, sections: [{ id, kicker, title, refs: [bank ref…], blocks: [block…] }] }`, a block being one of
  `{ p }`, `{ list: [..] }`, `{ fig: spec, cap?, view? }`, `{ tiles: [{ fig, view?, name, note? }], cols? }`, `{ rule, label? }`, `{ table: { head: [..], rows: [[..]] } }`. `**bold**` is the only inline markup. `view` is an SVG viewBox that crops the 320 × 200 figure.
- Produces: built files `data/theory-<level>[.ru].json` and `h/theory-<level>[.ru].<hash>.json` = `{ level, lang, topics: { <topic>: article } }`; `window.THEORY = { <level>: { en, ru?, t: [topic ids] } }` in `index.html`.
- Produces: `node data/check_theory.mjs [level]` exits 1 on any error and prints per topic: words, pictures, share of the topic's questions whose `ref` a section covers.

- [ ] Write `docs/theory.md` (format, authoring rules, how to check and build).
- [ ] Write `data/check_theory.mjs`: topic exists in the bank; section ids unique; block kinds known; every figure renders through `figSvg` without throwing; every `refs` entry is a `ref` of that topic in the English bank; the Russian file has the same sections, block kinds and figure types as the English one; limits from Global Constraints.
- [ ] Extend `miniapp/build.mjs` to pack theory and write `window.THEORY`.
- [ ] Run `node data/check_theory.mjs` and `node miniapp/build.mjs`: both pass with the pilot article (Task 3).

### Task 2: Theory in the app

**Files:**
- Modify: `miniapp/app.js`, `miniapp/app.css`, `docs/design/test-icons.js` (glyph `page`)

**Interfaces:**
- Consumes: `window.THEORY` and the built files of Task 1.
- Produces: views `theory` (tab) and `article` (`{ t: topic id, s?: section id }`); actions `theory` (open an article), `tlevel` (change course on the tab), `tsec` (scroll to a section); state `S.read = { '<prefix>-<topic>': 1 }`; deep link `?screen=theory`.

- [ ] Add `['theory', 'page', 'theory']` to `NAV` after Learn; strings in `STR.en` and `STR.ru`.
- [ ] `loadTheory(level, lang)` with the English fallback; the tab draws a skeleton, then the list, or the error line with Retry.
- [ ] `article` view as in mockup A: head, lead, section chips, sections, previous / next topic, main button "Practise this topic · N questions" (`openSetup([topic])`).
- [ ] The reference chip under an answered question opens the article at the section whose `refs` holds the question's English `ref`.
- [ ] A read mark when the end of the article has been on screen; shown on the tab and counted on the level page row "Theory · read n of 10".
- [ ] Verify in the browser preview: day, night, 320 px, English and Russian, each Review Focus line.

### Task 3: Pilot course: Bareboat Skipper (10 articles, EN + RU)

**Files:**
- Create: `data/theory/bareboat-skipper/{terms,ropework,safety,colregs,navigation,buoyage,weather,anchoring,systems,emergency}.json` and `.ru.json`
- Modify: `docs/design/figures.js`, `docs/figures.md` (new type `boat`: a yacht in profile, in plan and its sail, with labelled parts)

- [ ] Buoyage first, as the reference article the others copy.
- [ ] For each topic: list the topic's `ref` values with counts from the bank, outline sections from them, write the English article, then the Russian one.
- [ ] `node data/check_theory.mjs bareboat-skipper` passes; read every article in the app once in each language.
- [ ] Checkpoint: Nikolai reads the pilot course before the other eight are written in the same mould.

### Task 4: The other eight courses

Same steps as Task 3, one course at a time, in the order of the course progression: International Crew, VHF Radio Operator, Flotilla Skipper, Yachtmaster Coastal, Yachtmaster Offshore, Yachtmaster Ocean, Racing Rules of Sailing, Charter Check-in.

- [ ] Before each course: name the pictures its topics need that `figures.js` cannot draw yet (expected: knots, the sextant and the PZX triangle, tidal curves, radio set, flags) and add those types first.
- [ ] Topics shared between courses (COLREGs, buoyage, weather) are written for the level, not copied: Flotilla repeats the essentials, Yachtmaster goes deeper.
- [ ] After each course: checker passes, both languages read in the app.

### Task 5: Docs

- [ ] `README.md`: the repo tree (`data/theory/`, `data/check_theory.mjs`, `docs/theory.md`) and the status of theory per course.
- [ ] `docs/design.md`: the Theory tab and the article screen in the screen list.
