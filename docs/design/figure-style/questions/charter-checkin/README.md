# Charter Check-in test images: the contract

Each drawn test figure gets a folder `<id>/` here (id as in `data/questions/charter-checkin.json`, e.g. `ci-123`).
The lists per figure type are `<type>.json` (written by `docs/design/blender/extract_questions.py`):
`[{id, topic, q, answer, why, figure, ru}]`. `ru` maps the figure's own English strings to the bank's Russian.

## What a folder holds

| File | Who writes it | What |
|---|---|---|
| `3d.jpg`, `3d.labels.json` | the type's generator, `docs/design/blender/q_<type>.py` (Blender, `common.render`) | the render, 1280×800, and its labels: `note`, optional `lines` (more note lines), `labels` [{text, x, y, color?}], `arrows`, `bloom` |
| `q.png` | capture of `q.json` | instead of a render: a 2D image for the question (chart, isobars) |
| `plan.json` → `plan.png` | the generator; captured | the plan-view schematic shown **with the answer**; `{sch}` / `{profile}` / `{rhythm}` / `{svg}` as in `article-figures.html`, `noScale: true` drops the scale bar |
| `ru.json` | the generator | the Russian of every English string in `3d.labels.json`, `plan.json` and `q.json` |

Captures: `node docs/design/blender/capture_questions.mjs charter-checkin --type <type>` and the same with `--ru`
(needs `python3 -m http.server 5182 --directory docs/design`). Labels are drawn at publish time by `label.py`
(`--ru` for the Russian copy); run it yourself to look at a result.

## Rules

1. **The question image never gives the answer away.** Labels and notes come only from the figure's own data
   (`note`, `labels`, `panel`, `gauges`, light `t`, `other.label`, mark names…). The scene shows what the skipper would
   see, nothing more: at night only lights (and what lights show), a vessel type that is itself the answer is not
   given away by the hull, the shapes or a label. The `answer` and `why` are for checking, never for printing.
2. **Same facts as the data.** Bearings, distances, headings, sides, colours, counts, values: exactly as in `figure`.
3. **The plan may explain.** It is shown after answering, so it can carry the reasoning, and it must agree with
   `answer` and `why`.
4. **Russian** follows the bank's own (`ru`) and the article's terms (`data/theory/charter-checkin/<topic>.ru.json`),
   kept as short as the English.
