# Racing Rules test images: the contract

Each drawn test figure gets a folder `<id>/` here (id as in `data/questions/racing-rules.json`, e.g. `rr-123`).
The lists per figure type are `<type>.json` (written by `docs/design/blender/extract_questions.py`):
`[{id, topic, q, answer, why, figure, ru}]`. `ru` maps the figure's own English strings to the bank's Russian.

## What a folder holds

| File | Who writes it | What |
|---|---|---|
| `3d.jpg`, `3d.labels.json` | the type's generator, `docs/design/blender/q_<type>.py` (Blender, `common.render`) | the render, 1280×800, and its labels: `note`, optional `lines` (more note lines), `labels` [{text, x, y, color?}], `arrows`, `bloom` |
| `q.png` | capture of `q.json` | instead of a render: a 2D image for the question (chart, isobars) |
| `plan.json` → `plan.png` | the generator; captured | the plan-view schematic shown **with the answer**; `{sch}` / `{profile}` / `{rhythm}` / `{svg}` as in `article-figures.html`, `noScale: true` drops the scale bar |
| `ru.json` | the generator | the Russian of every English string in `3d.labels.json`, `plan.json` and `q.json` |

Captures: `node docs/design/blender/capture_questions.mjs racing-rules --type <type>` and the same with `--ru`
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
4. **Russian** follows the bank's own (`ru`) and the article's terms (`data/theory/racing-rules/<topic>.ru.json`),
   kept as short as the English.

## Racing Rules: race diagrams are 2D

Every drawn figure here is a race diagram (`type: race`: wind, boats with heading and tack, a mark with its zone,
a line, an obstruction, a track). The question image is `q.json` → `q.png`, a race diagram in the schematic style,
drawn by `docs/design/blender/q_race.mjs` from the figure's data alone. The plan for the answer is the same diagram
with the reasoning on it, drawn by the same script from `<id>/plan.spec.json` (format: see the top of `q_race.mjs`).

### The race diagrams: `q_race.mjs`

`node docs/design/blender/q_race.mjs [rr-001 | <topic> ...] [--check]` writes, for every id in `race.json`, `<id>/q.json`,
`<id>/ru.json` and, where `<id>/plan.spec.json` exists, `<id>/plan.json` (`--check` only validates the specs and the
Russian). Then capture: `node docs/design/blender/capture_questions.mjs racing-rules --type race` and the same with `--ru`;
contact sheets: `python3 docs/design/blender/q_race_sheet.py [--ru] [--topic <topic>]` (12 a sheet, q and plan side by side).

- **Geometry is figures.js `FIG.race`'s**: the 320×200 frame mapped uniformly (zoomed to fit what is drawn, never
  distorted), every boat at its `x, y, hdg` and scale, hull 40 × scale long, a length 44 × scale, the zone 3 lengths
  (of the figure's `scale`), the line from the pin to the committee boat, the obstruction rect or path (land touching
  the frame runs on past it), the track. The sail is on the leeward side for the wind: heading − wind in (0°, 180°)
  → boom to starboard, port tack; otherwise boom to port, starboard tack; exactly head to wind the boom is on the
  centreline, the sail flapping. The boom opens with the point of sail (close-hauled ~10°, run ~80°).
- **Colours**: You in the app's accent (with a white dot on the foredeck), Red, Blue (navy), Green, Yellow, Grey, Black,
  White as named; A, B, C and other names from a spare palette, never two alike. Every boat has its name on a pill of
  its colour, placed clear of hulls, booms, headings and other labels, nearer its own boat than any other.
- **Question image**: only the figure's data. The note is the title of the key band; nothing else is written.

**Plans** come from `<id>/plan.spec.json`, written from the question, `answer` and `why` (no drawing code):

```json
{
  "title": "Red is clear astern",
  "key": ["Red's hull is behind the line abeam your transom", "Definition Clear Astern and Clear Ahead; Overlap"],
  "keep": ["Red"], "right": ["You"],
  "tags": [["Red", "clear astern", "red"]],
  "tack": true, "abeam": ["You"], "zone": true,
  "arrows": [[x1, y1, x2, y2, "red"]], "lines": [[x1, y1, x2, y2, "ink", "dash"]], "rings": [[x, y, r, "red"]],
  "tracks": [["M120 55 L95 100", "accent"]], "ghosts": [{ "of": "You", "x": 150, "y": 90, "hdg": 45, "text": "after the tack" }],
  "pills": [[x, y, "text", "accent"]],
  "ru": { "Red is clear astern": "Red чисто позади", "…": "…" }
}
```

- Coordinates are the figure's own (320×200, x right, y down); boats are named by their label.
- `title` (required): the answer in a few words. `key`: 1–3 lines (≤ ~70 characters), the rule or definition named last.
- `keep` / `right`: red ring + "keeps clear" / blue ring + "right of way" round the hull; `["Red", "must give mark-room"]`
  puts other words on the tag (red = the boat with the obligation, blue = the boat entitled). Use them whenever the
  answer says who keeps clear or who owes room; they must agree with `answer` and `why`.
- `tags`: more pills under a boat's name, kind `light|red|accent|ink|green`. `tack`: true or a list: "port tack" /
  "starboard tack" from the drawing itself. `abeam`: the line abeam the named boat's transom. `zone`: the mark's zone
  drawn bold with "zone · 3 hull lengths"; a number is a radius in figure units (a bigger boat nearer the mark).
- `arrows`, `lines` (colour `red|accent|ink|green|course|muted`, 6th item `"dash"`), `rings` (dashed circle), `tracks`
  (a path with an arrowhead), `ghosts` (the named boat faded at another place or heading), `pills` (text near a point).
- `ru`: Russian for every string the spec adds. Built in: keeps clear, right of way, port tack, starboard tack, line
  abeam, zone · 3 hull lengths, and every figure string. Run with `--check`: it reports unknown boats, keys and colours,
  and every string without Russian. The definitions topic is the reference set (71 specs).
