# Plan: new-style images for the VHF and Bareboat Skipper tests

The articles of both levels now show a Blender render with a plan-view schematic under it (`publish_figs.py`,
`"photo"` on a figure block). This plan does the same for the questions in `data/questions/<level>.json`.

## What there is

| Level | Questions | With a figure | Text cards | Drawn figures |
|---|---|---|---|---|
| Bareboat Skipper | 1000 | 672 | 330 | 342 (340 unique) |
| VHF Radio Operator | 200 | 65 | 60 | 5 |

Drawn figures by type (Bareboat, plus VHF in brackets): encounter 74 (+1), lights 63, chart 53 (+1), rope 40,
bay 23 (+2), sail 21, panel 21 (+1), buoy 15, anchor 10, dayshape 10, isobars 8, compass 4.

Article figures were tuned by hand, one scene each. Question figures cannot be: almost every one is different.
Each image has to come from a generator that reads the question's own `figure` data. A person then reviews contact
sheets and fixes only the outliers.

## Rules for test images

1. **Never give the answer away.** Labels come only from the figure's own data (its `labels`, `note`, `panel`,
   `gauges`), never from the answer or the explanation. The scene shows what the skipper sees, not who gives way.
2. **Same facts as the drawing.** Bearings, distances, headings, light colours, depths and gauge values stay exactly
   as in the data. A check script compares each generated label set with the data.
3. **Text cards stay text.** The 390 cards carry the question itself: a script, a checklist or a log entry. They
   keep today's card, with no photo. The articles already show the radio scenes.
4. **The size fits the question screen.** The figure box there is 16:10 (max-height 240 px), the same shape as the
   renders. Publish at 960 px wide, WebP q75, about 35 KB each.

## How the question screen shows them (to decide)

- **Recommended: the 3D on the question, the plan in the answer.** The question shows the render in today's
  figure box. Once you have answered, the explanation shows the schematic beside the explanation text. The
  question screen stays as compact as it is today.
- Alternative: a `3D · Plan` switch on the figure box.
- Alternative: both stacked, as in the articles. This doubles the scroll on a phone and pushes the options below
  the fold.

## Generators, by figure type

| Type | Count | 3D | Schematic | Reuse |
|---|---|---|---|---|
| encounter | 75 | yes: helm view or drone view, from `you`/`other` bearing, distance, heading, sails, wind | plan view of both boats | `fig_drone.py`, `fig_encounter.py`, `kit.Yacht`, ship models |
| lights | 63 | yes: night scene; the vessel type is worked out from the light pattern | plan view, plus the light diagram | `fig_lights.py`, `fig_night_yacht.py`, `kit_night.py` |
| chart | 54 | no Blender: the chartplotter screen render (as anchoring fig 6) | yes | `plotter()` in `article-figures.html` |
| rope | 40 | yes: by `kind`, from a library of about 15 knot and rope renders, relabelled per question | none, or a knot diagram | `rope_ring.py`, `knots/`, `rope_types.py` |
| bay | 25 | yes: terrain from the `land` path, spots as buoys or boats | yes | `fig_bay.py`, `kit_world.py` |
| sail | 21 | yes: from `wind`, `hdg`, `boom` | wind and sail plan | `fig_sail.py` |
| panel | 22 | yes: gauges drawn from the data | none | `fig_instruments.py --kind panel`, `make_faces.py` |
| buoy | 15 | yes: by `kind` | none | `fig_buoy.py` |
| anchor | 10 | yes: scope from `depth` | side profile | `fig_anchor.py`, `schematicProfile` |
| dayshape | 10 | yes | none | `fig_encounter.py --kind dayshape` |
| isobars | 8 | no 3D: a restyled synoptic chart | yes | new 2D generator |
| compass | 4 | yes: card at the given heading | none | `fig_instruments.py --kind compass` |

The lights generator is the riskiest. The data gives coloured dots and positions, not a vessel type. It needs a
table that maps each light pattern to a vessel: sailing vessel, power under or over 50 m, towing, trawling,
fishing, not under command, restricted in ability to manoeuvre, at anchor, pilot, aground. Any pattern the table
does not know goes to a "make by hand" list rather than being guessed.

## Pipeline

1. `extract_questions.py <level>`: list each drawn figure as `{id, topic, type, figure, ru figure}`, grouped by type.
2. `q_<type>.py`: one Blender script per type. It takes `--spec <figure json> --out` and writes `<id>-3d.jpg` and
   `.labels.json`, so `label.py` and `label.py --ru` work as they do for the articles.
3. Schematics: `figure-schematic.js` adapters per type (spec → schematic spec), captured headless as for the articles.
4. Russian: label text from each question's Russian overlay (`<level>.ru.json` → `figure`), plus a `ru.json` for any
   added strings. The same `--ru` capture and labelling as the articles.
5. `publish_q.py`: WebP into `miniapp/figs/q/<level>/<id>[.ru].webp` and `-plan`, and `"photo"`/`"plan"` on the
   question. The app, `pages.mjs` (question list on the article page) and the MCP `get_figure` link pick it up.
6. Review: contact sheets per type, 24 a page, before | 3D | plan, as for the articles. Fix the outliers by hand.

## Order and effort

1. **Pilot: VHF, 5 figures** (encounter, chart, bay ×2, panel). This tests every step end to end on a small set,
   including the question-screen layout.
2. **Bareboat by type, the biggest win first:** encounter 74, lights 63, rope 40, bay 23, sail 21, panel 21, then the
   small types. Chart 53 and isobars 8 go last, since they are 2D anyway.
3. Rendering takes 10–20 s a figure at 192 samples: about 2 hours of GPU for the 3D, run in the background by type.
   Building the generators is most of the work. Encounter and lights are the largest; rope, buoy and dayshape mostly
   reuse renders that exist.
4. Size: about 345 figures × 2 languages × (3D + plan) at about 35 KB, roughly 25–30 MB in `miniapp/figs/q/`.

## To decide before starting

- How the question screen shows the plan (see above; recommended: in the answer).
- Whether chart and isobars questions get a chartplotter or synoptic restyle, or keep today's drawing.
- Whether text cards stay as they are (recommended).
