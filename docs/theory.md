# Theory articles

One article per topic of every level, in English and Russian. The mini app shows them under the Theory tab: a level's
ten topics, each on a page of its own, and the reference chip under an answered question opens the section that
explains it. Plan and order of work: `docs/superpowers/plans/2026-11-05-theory-articles.md`.

## Files

```
data/theory/<level>/<topic>.json       the English article (the source)
data/theory/<level>/<topic>.ru.json    the Russian article: the same structure, translated
data/check_theory.mjs                  checks every article against the rules below and against the bank
```

`<level>` and `<topic>` are the ids of the question bank (`data/questions/<level>.json`). `miniapp/build.mjs` packs a
level's articles into `theory-<level>[.ru].json` and writes the list into `index.html` (`window.THEORY`); nothing built
is kept in the repo.

## Format

```json
{
  "topic": "buoyage",
  "lead": "Every mark answers one question: where is the safe water?",
  "sections": [
    {
      "id": "lateral",
      "kicker": "Lateral marks",
      "title": "The sides of the channel",
      "refs": ["IALA lateral marks", "IALA region B"],
      "blocks": [
        { "p": "Lateral marks stand on the edges of a channel. They are laid for a vessel **coming in from the sea**." },
        { "tiles": [
            { "fig": { "type": "buoy", "kind": "lat-port", "topmark": true }, "view": "68 10 120 178", "name": "Port hand", "note": "red · can" },
            { "fig": { "type": "buoy", "kind": "lat-stbd", "topmark": true }, "view": "68 10 120 178", "name": "Starboard hand", "note": "green · cone" } ] },
        { "rule": "Entering harbour in Region A: red to port, green to starboard." }
      ]
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `topic` | The topic id; the page's title is the bank's title of that topic. |
| `lead` | Two or three sentences under the title: what the topic is for. |
| `sections[].id` | Short, lower case, unique in the article, the same in both languages. The chip under a question links to it. |
| `kicker` | The plain name of the section ("Cardinal marks"): the label above the heading and the chip in the contents row. |
| `title` | The heading: what the section says ("Which side of the danger is safe"). |
| `refs` | The `ref` values of the English bank that this section explains, spelled exactly as in the bank. The same list in both languages. |
| `qa` | Optional. The section's opener: `{ "q": "…?", "a": "…" }`, the question a student would type into a search engine or ask an assistant, and the answer in one or two sentences. Shown under the heading, before the blocks; search engines and AI assistants quote passages like it. Not counted in the article's words. |
| `blocks` | The section's content, in order. |

A block is one of:

| Block | What it draws |
|---|---|
| `{ "p": "…" }` | A paragraph. `**bold**` is the only markup, for the term being defined. |
| `{ "list": ["…", "…"] }` | A bulleted list: steps, a checklist. |
| `{ "fig": { … }, "cap": "…", "view": "x y w h" }` | One figure at full width: a spec for `docs/design/figures.js` (see `figures.md`). `cap` is an optional caption. `view` optionally crops the 320 × 200 drawing (an SVG viewBox). |
| `{ "tiles": [ { "fig", "view", "name", "note" } ], "cols": 2 }` | Small figures side by side, each with a name and an optional note: things to tell apart. `cols` 2–4 (default: the number of tiles, at most 4). A buoy alone is `"view": "68 10 120 178"`. |
| `{ "rule": "…", "label": "Remember" }` | The one line to take away, in a band. The label is "Rule" unless given. |
| `{ "table": { "head": ["…"], "rows": [["…"]] } }` | A small table, two to four columns: values to look up. |

## Rules

- **Teach what the questions ask.** Before writing, list the topic's references and how many questions use each
  (the checker prints them). Every reference used by ten or more questions is explained by a section and named in
  its `refs`. The article gives the rule and the reason; the questions give the situations.
- **4–7 sections, 400–900 words.** One idea per section, short paragraphs, the term in bold where it is defined.
- **A picture in every section**, at least four in an article. A table counts for the section, not for the four.
  Use the figure type that shows the thing itself (`buoy`, `lights`, `encounter`, `chart`, `compass`, `isobars`,
  `sail`, `anchor`, `bay`, `dayshape`, `panel`, `rope`, `race`, `boat`, `lines`, `radio`, `flag`, `tide`, `sphere`,
  `altitude`); `card` is for a procedure or a script to
  say (a MAYDAY call), not a substitute for a drawing. If nothing can draw it, add a type to `figures.js` first.
- **Second person, present tense**, as in the questions: "you leave the red marks to port".
- **No official claims.** These are study notes close to the syllabus, not IYT text. Facts follow COLREGs, IALA and
  standard practice; where practice differs by region (IALA A and B, local rules), say so.
- **Openers** (`qa`): the question in the student's words, specific to the section ("Which side do I leave a red buoy on, coming into harbour?", not "What are lateral marks?"), at most 18 words; the answer starts with the answer itself, names the rule or term, stands on its own without the rest of the section, 8–45 words. Every section of an article has one or none does; the Russian file has them where the English one does.
- **Russian** follows `glossary-ru.md`: «вы», the glossary's terms, international abbreviations for lights left as
  they are. Labels inside figures are translated in the Russian file (keep them as short as the English); labels the
  renderer draws itself ("You", "wind") are translated by the app.
- **English terms in the Russian text**: a marine term is followed by its English as a tag, `**створом** [[transit]]`,
  the first time it appears in the article, with the English article's own word. The app shows it as «створом
  (transit)» when "Учить английские термины" is on in Profile and leaves it out otherwise; the site pages and the
  bot leave it out, the MCP server shows it in brackets. Not in headings, figures, tiles or `refs`.

## In the app

- **Read marks**: an article is read once its end has been on screen (`state.read['<prefix>-<topic>']`).
- **Reports**: the flag beside a section's heading opens a sheet with a comment box; what the student writes is kept
  in `state.notes['<prefix>-<topic>/<section>'] = { text, at }` and goes to the server with the rest of the progress.
  Each picture has its own flag in its corner, for a mistake in that picture: its note is kept under
  `'<prefix>-<topic>/<section>/f<n>'`, n the picture's place in the section from 1 (a figure, then each tile of a row),
  and the admins see the picture beside the comment.
  The admins read the comments at the top of their Reported page (`api/admin.mjs` → `notes`), newest first, and a
  tap opens the article at that section. A student can change or withdraw a report from the same flag. Admins cannot
  take one off yet: `public.flag_clears` only knows question flags.
- **Where to read**: the result of a practice session or a mock exam lists the topics of the wrong answers that have
  an article, most mistakes first, with the sections that explain them (through `refs`).

## Check and build

```
node data/check_theory.mjs                    # every level that has articles
node data/check_theory.mjs bareboat-skipper   # one level, with the references of each topic
npm run dev                                   # the app with the articles, http://localhost:5173/?screen=theory
```

The checker fails on: a topic or reference the bank does not have, a figure the renderer cannot draw, a section with
no picture or table, an article outside the limits, a Russian file whose sections, blocks or figures differ from the
English one. It prints, per topic, the words, the pictures and the share of the topic's questions whose reference a
section covers.
