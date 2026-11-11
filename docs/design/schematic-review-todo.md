# Schematics: fixes left after the 1.7× text rollout (2026-11-11)

All schematics (figure-schematic.js) now draw text at 1.7× and place labels themselves. A review of every Russian
schematic found these left to fix by hand. Most are a note to move in the figure's own spec: an article's entry in
`article-figures.html` (or `figure-style/articles/<level>/<article>/<n>-plan.json`), a question's
`figure-style/questions/<level>/<id>/plan.json`. "px" are on a 600 px wide preview; about ×2 in the 1280 frame.
Re-capture (blender/capture_article.mjs, capture_questions.mjs, with and without --ru) and re-publish the plan images
afterwards.

## A label next to the wrong thing (fix first)
- bar/colregs/5 — "000°" and "180°" read swapped: move "000°" ~60px down by your boat, "180°" ~60px up by the other.
- bar/terms/8 — «Вы» sits in the red dead sector: move it ~110px down below the boat.
- q/bs-433 — "Под парусом и мотором" + caption sit above your boat: move ~70px up, ~120px right, by the 300° vessel.
- q/bs-441 — caption "под парусом" (yours) sits by the restricted vessel: move ~150px left, ~80px down.
- q/bs-621 — "Буксировщик" sits over your boat: move ~110px up beside "Буксируемое"; red pill ~15px down.
- q/bs-730 — "B: укрыта от обоих" sits by C: ~60px up under B.  q/bs-748 — "A: за мысом" ~40px left, under A.
- q/bs-820 — «Вы» reads as the ball's label: ~160px down below the boat.
- q/ci-017 — "1 · заправиться" ~110px left under A, "2 · встать и доложить" ~100px left under B.
- q/yof-524 — «Вы» and "под парусом" sit under the pilot vessel: ~110px down.  q/yof-561 — "вы сохраняете курс" ~110px down beside «Вы».
- yac/weather/1 — «Вы» over the anticyclone: ~70px down, left of the boat.

## A note on top of «Вы» (move the note sideways)
q/bs-386 (~120px right), bs-420 (~70 right), bs-423 (~150 left), bs-426 (~120 right), bs-446 (~60 right), bs-457 (~140 right),
bs-947 (~100 right), ci-397 (~40 down), yof-519 (~25 down), yac/colregs/4 ("Лов рыбы" ~30 up, 20 left).

## A note covering the thing it names
- Harbour entrances q/bs-051 (~60 left), bs-551 (~50 right), bs-552 (~55 right), bs-553 (~45 left): the leave-to pill covers its
  highlighted buoy; "ГАВАНЬ" ~12px right in bs-051/551/552 and bar/buoyage/9.
- Leading lights: bar/buoyage/13, q/bs-499 (~100 left), bs-593 (~20 up): the pill covers the rear light.
- bar/anchoring/10 "свой конец" ~50 right; bar/colregs/10 "Лов рыбы"+"трал" ~60 right; bar/emergency/6 pill ~40 down;
  cha/safety/4 "фалинь закреплён" ~45 up; cha/sails/3 both pills ~80 right; cha/sails/4 ~100 left / ~60 right;
  q/bs-713 both fetch pills ~20 up; bs-736 "светлое пятно песка" ~25 down; bs-803 ~30 down; ci-361 ~25 right;
  yac/compass/5 "EBL ≈ 333°" ~50 up-right; yac/tides/11 ~40 up; yac/weather/12 ~80 left; q/yof-475 "2,1 мили" ~35 right.
- Marks under moored boats (spec positions): cha/ground/6 "B" ~30 left; cha/papers/6 "B" ~40 left.

## Two labels printed together
bar/colregs/1 (pill ~30 up), colregs/4 (upper "000°" ~35 left), colregs/16 ("200°" ~40 right, 25 down), q/bs-402 ("000°" ~50 down,
40 right), bs-431 ("000°" ~40 left, 30 down), bs-388 ("глубокая вода" ~60 right), bs-645 ("мёртвый сектор" ~35 down),
bs-960 ("бедствие" ~70 right), yof-557 ("090°" ~45 right), yac/colregs/17 ("препятствие" ~25 up), ci-457, ci-458 (names behind
moored boats ~40 right; "2 · ваше место" off the quay arm).

## Cut off or struck through
- q/bs-060 — the red pill is wider than its half: wrap or shorten the text.  q/bs-399 — the course line strikes "разделительная зона": ~12 up.
- q/bs-625 — "1000 м" under the trawler's ring: ~30 right.  q/yof-294 — "6 миль к N" ~45 left.  yac/tides/8 — "снос 10 миль" ~40 left.
- q/bs-761, q/yof-870 — "нейлоновый демпфер" under the hull: ~50 down into the water.
- Captions that do not wrap (side views / own layouts): q/yof-823, yac/dr/15; English captions in vhf/gmdss/3, bar/navigation/8.

## Not in this renderer (still small text)
Hand-drawn figures keep their own type size: bar/emergency/3–7, bar/navigation/1–10, cha/electrics/1,3,4, cha/engine/5,
cha/ground/5,7,8, cha/hull/1,3, cha/plumbing/2–4, cha/return/5, yac/pilotage (most), yac/tides/1–7, yac/vessel/*, yac/weather/7–9.
