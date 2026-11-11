# Schematics: what is left after the 1.7× text rollout (2026-11-11)

All schematics drawn by figure-schematic.js have text at 1.7× and place their labels themselves; the ~65 figures the
review flagged were then fixed by hand in their specs. A figure's spec can now nudge its own labels:
- note (`texts[i]`): `dx`, `dy` (frame pixels, the frame is 1280 wide), `fixed: true` to draw it exactly there;
- boat: `labelAt: 'below'|'above'|'left'|'right'`, `labelDx`/`labelDy`, `tagUp`, `tagDx`/`tagDy`, `hdgDx`/`hdgDy`;
  on a target boat or mark, `bearingDx`/`bearingDy` for its bearing pill.
Specs: questions `figure-style/questions/<level>/<id>/plan.json`; bareboat articles inline in `article-figures.html`
(`AFTER`); other articles `figure-style/articles/<level>/<article>/<n>-plan.json`. After a change, re-capture
(`blender/capture_article.mjs` / `capture_questions.mjs`, with and without `--ru`) and re-publish the -plan images.

## Small leftovers (readable, not wrong)
- q/ci-397 — the "к кормовым ступенькам" pill covers most of the MOB buoy; no free room below it.
- q/ci-458 — the last letter of "ваше место на ночь" touches the quay edge.
- yac/tides/8 — the "20 kn: 1 h 30" pill lies on part of the yellow course line.
- q/bs-713 — both fetch pills are pinned at a smaller size to keep them by A and B.
- bar/buoyage/9 — «Вы» sits on the course line.  bar/buoyage/13 — crowded round «Вы», still readable.
- q/bs-402 — "вы уступаете" touches the bottom of «Вы».  q/bs-423, bs-446 — your heading arrow runs through the bearing pill.
- q/bs-051 — «Вы» sits on the buoy column.

## Not in this renderer (still small text)
Hand-drawn figures keep their own type size: bar/emergency/3–7, bar/navigation/1–10, cha/electrics/1,3,4, cha/engine/5,
cha/ground/5,7,8, cha/hull/1,3, cha/plumbing/2–4, cha/return/5, yac/pilotage (most), yac/tides/1–7, yac/vessel/*, yac/weather/7–9.
English captions in the Russian version: vhf/gmdss/3, bar/navigation/8; yac/dr/15's caption is cut off.

## Data files
The plan images are taller now; the `"plan"` width/height ratio stored on figures in `data/theory/*.json` and the bank
sources is stale. The app sizes images by their own shape, so nothing breaks; refresh the ratios with
`blender/publish_figs.py` / `publish_q.py` when no one else is editing those data files.
