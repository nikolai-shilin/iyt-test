# Figures

A question's `figure` is a small JSON object. `docs/design/figures.js` turns it into an SVG (`figSvg(spec)`), and
`paintFigures(root)` fills every element with a `data-fig` attribute. One renderer per `type`. All figures are
320 × 200 units, scale to their container, and use the app's theme tokens (`--ink`, `--muted`, `--bg`, `--band`,
`--accent`, `--danger`) so they read in day and night; the only fixed colours are the lights and buoys (red, green,
yellow, white).

Conventions: compass directions are degrees clockwise from north (0 = N, 90 = E). **Wind is the direction it blows
from.** Boat headings are absolute. In `encounter`, the other vessel's `bearing` is *relative* to your bow (positive
to starboard, negative to port). Coordinates in `lights`, `chart`, `bay` are in the 320 × 200 grid, y down.

## encounter — two vessels, top view

```json
{ "type": "encounter",
  "you":   { "hdg": 45, "sail": true, "boom": -14, "label": "You" },
  "other": { "bearing": 300, "dist": 85, "hdg": 315, "sail": true, "boom": 14, "label": "Other", "scale": 1 },
  "wind": 0, "bearingLine": true, "note": "Bearing steady at 050° relative" }
```

Own boat at the centre with a blue dot; the other vessel at `dist` units on `bearing`. Dashed arrows show both
headings. `sail: true` draws a white hull with a sail; `boom` −14 = boom to port, 14 = to starboard. `wind` adds the
blue wind arrow top right. `bearingLine` draws the dashed line between the vessels. `scale: .3` with `label: "MOB"`
makes a casualty. A single-boat picture: give `other` `dist: 0` (anything under 1) and only your boat is drawn.

## lights — what you see at night

```json
{ "type": "lights", "lights": [ { "c": "w", "x": 200, "y": 78, "t": "white" }, { "c": "r", "x": 196, "y": 118, "t": "red" } ],
  "note": "Night · bearing 045° relative, steady", "hull": "M… optional faint hull path" }
```

Dark panel, horizon at y = 150. Colours `r g w y`; `r` default 6; `t` a label beside the dot. Typical layouts:
masthead high (y ≈ 60–80) over sidelights (y ≈ 120); a tricolour is three dots close together high up; a single
white low (y ≈ 122) is a sternlight or anchor light.

## buoy — IALA marks

```json
{ "type": "buoy", "kind": "card-n", "rhythm": "Q", "rhythmNote": "continuous quick", "region": "A", "topmark": true, "note": "" }
```

`kind`: `card-n card-e card-s card-w` (black/yellow bands + cones), `lat-port` (red can; green in region B),
`lat-stbd` (green cone; red in B), `iso` (black–red–black, two balls), `safe` (red/white stripes, red ball),
`special` (yellow, X), `wreck` (blue/yellow). `topmark` draws the can/cone topmark on lateral marks. `rhythm`
adds the night panel with the light in the right colour and the rhythm text (`Q(6)+LFl`, `Fl R`, `Iso`).

## compass — rose with variation

```json
{ "type": "compass", "variation": -4, "deviation": 3, "course": 215, "courseLabel": "Compass course", "note": "C → M → T" }
```

`variation` and `deviation` signed: east positive, west negative. Draws true north, the magnetic-north arrow (blue),
the course arrow (black) and a panel with the numbers.

## chart — a chart extract

```json
{ "type": "chart", "land": "M0 0 H320 V40 H0 Z",
  "depths": [ [60, 60, "8"], [150, 118, "1.5"], [170, 130, "0.8", true] ],
  "marks": [ [160, 30, "w", "rear"] ], "track": "M30 170 L150 118 L260 60", "boat": [40, 168, 45],
  "labels": [ [160, 125, "keep in line", "middle"] ], "panel": ["Now 14:00", "Height of tide 1.2 m", "Draft 1.9 m"],
  "note": "Depths in metres below chart datum" }
```

`depths`: `[x, y, text, underline?]` — underline marks a drying height. `marks`: `[x, y, colour, label]`.
`track` is an SVG path (dashed blue). `boat`: `[x, y, hdg]`. `panel` is a white box top right, first line bold.

## anchor — side view, depth and chain

```json
{ "type": "anchor", "depth": "5 m", "tide": "high water", "title": "Settled evening, F2", "lines": ["All-chain rode", "Bow roller 1 m above water"], "wind": 180 }
```

## isobars — pressure system

```json
{ "type": "isobars", "center": "L", "tight": true, "values": ["996", "1000", "1004"], "boat": [250, 150, 0], "hemisphere": "Northern hemisphere", "note": "Low centre to the NW" }
```

`tight` adds two more close isobars (strong wind).

## sail — points of sail

```json
{ "type": "sail", "wind": 0, "hdg": 45, "nogo": true, "note": "Close-hauled on starboard tack" }
```

Own boat with the sail set on the correct side for `hdg` relative to `wind`; `nogo` shades ±45° round the wind.

## dayshape — a boat with a day shape

```json
{ "type": "dayshape", "shape": "ball", "sail": false, "note": "Day shape forward" }
```

`shape`: `ball` (anchored), `cone-down` (motor-sailing), `two-cones` (fishing), `two-balls` (NUC),
`ball-diamond-ball` (RAM), `cylinder` (constrained by draught), `three-balls` (aground).

## bay — an anchorage or harbour, plan view

```json
{ "type": "bay", "wind": 180, "land": "M… path", "spots": [ [150, 150, "A"], [240, 60, "B"] ],
  "labels": [ [160, 185, "LAND (south)", "middle"] ], "note": "Forecast: wind backing south overnight" }
```

Grey land over a pale sea, the wind arrow bottom right, lettered spots to choose from.

## panel — engine and electrics readouts

```json
{ "type": "panel", "gauges": [ ["Temp", "110°", true], ["Oil", "OK", false], ["Volts", "14.1", false] ], "lines": ["Alarm sounding", "Exhaust water: a trickle"] }
```

Up to three gauges `[label, value, alarm?]`; alarmed gauges turn red with a `!`.

## card — a situation in a few lines

```json
{ "type": "card", "title": "Fire below", "lines": ["Engine-bay fire spreading", "5 people aboard, 6 miles offshore"], "tag": "MAYDAY?" }
```

For situations with nothing to draw but several facts to weigh. `tag` is a red pill top right (a time, a warning).

## rope — a line at a fitting

```json
{ "type": "rope", "kind": "winch", "labels": [ [80, 86, "sheet"], [255, 90, "tail"] ], "note": "" }
```

`kind`: `cleat`, `winch`, `rail`, `ring`, `sheet`. These are schematic (the line and the fitting), not knot
diagrams — knots are asked by name. Proper knot drawings would be hand-made SVGs or photos; see PLAN.md.

## Adding a type

Add `FIG.<name> = f => { … return svg }` in `figures.js` using the helpers (`NS`, `txt`, `boat`, `arrow`,
`windArrow`, `compassN`, `pol`), document it here, and use it in `build_bank.py`. Keep text in `txt()` so it
inherits Carlito, and colours in tokens so night mode works. Check the result in `questions.html`.
