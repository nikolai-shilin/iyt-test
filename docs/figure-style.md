# Figure style: Helm and Drone

The look agreed for the question figures on 2026-11-04, after twenty-one rendered sketches. Every figure is a
still image rendered from a 3D scene that the question's data builds: there are no photographs in the pictures,
so nothing can sit in front of a rigging line or behind a distant ship. Colours, haze and tone were measured
from Unsplash photographs of the same kinds of view and are fixed here as "looks".

The renderer that produces these settings is `docs/design/figure-style-spike.html` (a throwaway, kept as the
reference implementation; it loads three.js from a CDN and renders ten sample questions). Open it over HTTP,
not as a file. `?view=1` shows the images bare; `?only=crossing,tacks` renders a subset; `?mode=cg` is the
default renderer.

## Two cameras

**Helm view.** What the skipper sees: the own boat's foredeck, pulpit and rigging in the foreground, the
horizon at eye height, the subject (another vessel, a mark, lights) ahead. Everything in focus. The own boat
pitches and rolls on the swell, so the horizon tilts a little.

**Drone view.** A tilted view from above (pitch 38–44° down, eye 40–48 m up, horizontal field 60–62°) for
situations that need the whole picture: converging boats, a channel, an overtaking. No haze, bloom, grain,
vignette or lens softening: these are diagrams drawn as scenes, and read sharp and flat.

A third, rarely used: **low view** (eye 5.5 m, field 44°), for a boat seen from alongside, e.g. a day shape.

## Looks

A look is a palette and tone. One look serves all daylight helm views; one serves all drone views; two serve
the night views. Each look's brightness distribution (32 bins) is taken from its reference photo and the
render is histogram-matched to it (`histAmt` 0.6 for helm, 0.35 for drone), then a camera curve is applied
(toe 0.06, shoulder 0.12) with a warm cast in the midtones.

### Day helm: `backlit`

Measured from a foredeck shot toward islands with the sun ahead. Used for every daylight helm view and the low
view, each with its own sun direction.

| | |
|---|---|
| sky | top `#2f6593`, mid `#5385a9`, horizon `#7f9aa8`; thin cirrus; brighter band round the sun |
| sea | water `#0c1f29`, far `#102836`, near `#1a272d`; chop 1.7; foam 0.1; reflection 0.45; glitter `shiny` 28, `spec` 1.1, `waterSun` 4; troughs darkened 0.3 close in |
| land | near `#56686f`, far `#9db1b8`; noisy ridges, lighter rock faces, darker scrub, a pale beach line |
| haze | fog density 0.00017 |
| light | sun `#fff0d8` intensity 3.6, hemisphere 0.35 |
| tone | blacks 3, whites 215, saturation 0.9, warm 1.2, exposure 0.85 |

Per view the sun is placed so its reflection does not fall on the subject. In the crossing view the sun is
behind the viewer (`sun: [140, 45]`) and the water glitter is switched off (`waterSun: 0`), with no bow spray.

### Drone: `aerialDark` (sea) with per-view sky

Measured from a choppy sea seen from above. The sea, sky colours, histogram and tone of `aerialDark` apply to
all four drone looks; only the sun direction differs per view.

| | |
|---|---|
| sea | water `#1f4248`, near `#1a3435`; no swell, foam, streaks or wind ripples (`clean`); chop 1.2 |
| sky (for reflections only) | top `#6f8e95`, mid `#244c53`, horizon `#5f7d84` |
| light | sun intensity 2.2, hemisphere 0.5 |
| tone | blacks 18, whites 159, saturation 0.8, warm 0.6, exposure 0.8 |

The only water features are the wakes: each moving boat deforms the surface (Kelvin arms, a bow hump each side
of the stem with a hollow behind, a stern hump; transverse waves faint at 0.12), with foam on the arms and the
churned centre lifted toward turquoise.

### Night: `night` and `night2`

| | `night` (ship) | `night2` (yacht) |
|---|---|---|
| sky | zenith `#020304`, horizon `#0b0d0e` | zenith `#02222a`, horizon `#0a3a44` |
| sea | water `#05080c`, near `#010101` | water `#04202a`, near `#00181d` |
| moon path | 1.6 | 1.2 |
| light | sun 1.2, hemi 0.18 | sun 1.1, hemi 0.3 |
| tone | blacks 0, whites 250 at the 99.99th percentile, saturation 0.9, no toe, no warmth, exposure 0.75 | same, exposure 0.8 |

Both: chop 2.6, ripple 1.2, foam 0.25, reflection 0.5; stars. Tone is anchored on the lights, so the sky
stays near-black.

## The own boat (helm views)

A 12 m cruising yacht, white gelcoat with a dark blue cove line and boot top, a greenish grime band at the
waterline, the name *Meltemi* in italics on each quarter. Pale non-skid deck (`teak: false`) in daylight.

On deck: pulpit, pushpit, stanchions and wire lifelines (no netting); a furling drum and furled genoa at the
stem (`bag: true` shows the main in its lazy bag on the boom); windlass with gypsy, bow roller with a plough
anchor and chain; horn cleats with a line made fast on the port bow; genoa tracks with cars; a liferaft
canister strapped to the coachroof; two dorade vents with red cowls on the coachroof; a canvas dodger over the
forehatch; a fender on the port lifeline; a sheet bag on the starboard rail; rope coils; jacklines; a sprayhood;
cockpit cushions; wheel, pedestal and binnacle. Rig: in-mast furling slot, spreaders, halyards, topping lift,
lazy jacks, radar dome, steaming light, masthead wind vane, VHF whip and anchor light.

Camera: eye 2.0–3.0 m above the water, 0.2–1.3 m off the centreline, field 55–70°, horizon set per view.

### Own lights at night

Sidelights low on the pulpit (0.35 m above the rail base), red to port `#ff3a24`, green to starboard `#5cffb4`,
each a spot of intensity 1.4 shining outboard and ahead in a 56° cone, range 4 m. A steaming light on the mast
(42 % of its height), warm white `#fff1d2`, intensity 1.8, lighting the foredeck. A deck light, intensity 0.4.
Each is also drawn as a glow (sidelights size 16, steaming light 32) the same way other vessels' lights are.

## Other vessels, marks and lights

Yachts follow the rules from the data: sail set on the leeward side, boom angle from the wind, heel away from
the wind, lights on by their arcs (sidelights 112.5° each side, sternlight 135° aft, steaming light under
power). Sails have twist, batten creases, a curling leech, seams with zig-zag stitching, a sail number, a UV
strip and a window on the genoa, telltales; the shaded side takes the sky's blue; the sun glows through the
cloth from behind.

Buoys follow IALA region A: cardinal pillars (black and yellow bands, two black cones), lateral cans (red) and
cones (green), with sun-faded paint, rust streaks, weed at the waterline, a guard rail, solar panels, a glass
lantern and a radar reflector. A ship at night is a silhouette a shade lighter than the sea with dim deck lights
and warm cabin windows.

A light is drawn as a camera records it: a small hot white core, a tight coloured ring, a wide soft halo and a
faint broken smear on the water below. Colours: red `#ff3a24`, green `#5cffb4`, white `#fff1d2`.

## Annotations (drone views only)

- **Wind:** a bright red arrow on the water (`#ff2a1a`, 14–15 m long, 3–4 m wide) with a red pill labelled
  *Wind* (`#e8231a`, white text).
- **Course:** a bright yellow dashed line (`#ffe600`; dash 2.4 m, gap 1.6 m, width 0.6 m) ahead of every boat.
- **Boats:** a blue pill *You* (the app accent) over the own boat, a white pill *Other* over the other.
- Pills are Carlito bold, 34 px at 1280 × 800, with a small tail, above the masthead.

Helm views carry no labels.

## Image

1280 × 800 (16:10), JPEG quality 0.92. The card in the app shows it at phone width; the figures were checked
to read at that size.

Reference renders of the ten examples at 2560 × 1600 (PNG, lossless) are in `docs/design/figure-style/hires/`,
with a contact sheet. The spike renders them with `?scale=2`; pixel-space effects (labels, glows, grain, lens
softening, the horizon band) scale with the image.

## Schematic companions

Every realistic figure has a plan-view schematic drawn from the same geometry: the situation from above, north
up, in the app's flat figure language (`docs/design/figures.js` conventions, theme tokens, Carlito). It is made
for a phone: the frame is fitted round the boats and marks so the action fills it, and every symbol and label is
big enough to read without zooming (26–30 px type at 1280 × 800; boats 115 px long). It carries every marking
the picture leaves implicit:

- a compass rose and a scale bar at a round number of metres (the grid is drawn at that spacing);
- each boat as a plain hull (no sail: the tack is in the tag), with its heading as a thick yellow dashed arrow
  and the course in degrees at the tip, a *You* / *Other* pill and a one-line tag (tack, motoring, what is seen);
- a dashed bearing line from the own boat to every other vessel or mark, with a pill on it giving the relative
  bearing (port/stbd and degrees) and the distance;
- at night, one compact light ring hugging each hull: red 112.5° to port, green 112.5° to starboard, white 135°
  astern; a thin outer white 225° arc when under power;
- IALA marks as large chart symbols (cardinal bands with cones, red can, green cone) with a type label;
- the wind as a thick red arrow with a red *Wind ddd°* pill, top right;
- a key band along the bottom naming the rule and the answer in two lines.

Renderer: `docs/design/figure-schematic.js` (`schematic(spec)` returns an SVG; specs are in metres with the own
boat at the origin, x east, z south; per-boat `labelAbove`, `side` and `courseSide` move labels off a crowded
line). The spike renders them with `?mode=schematic`; the ten examples at 2560 × 1600 are in
`docs/design/figure-style/schematic/`, with `contact-sheet-pairs.jpg` showing each realistic render beside its
schematic.

## What a real build needs

- A scene builder per figure type in `docs/figures.md` (encounter, lights, buoy, bay, race, …) that turns the
  question's JSON into a scene with these looks.
- Rendering at build time in a headless browser, so the app ships still images and no 3D engine.
- The sun direction and camera per figure type chosen once, so the subject is never in the glitter.
