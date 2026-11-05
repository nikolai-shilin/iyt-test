# Theory articles: review, 5 November 2026

The 90 English articles were read against each level's question bank (difficulty 2–3 questions first), and every
worked number in them was recomputed. Nothing was edited. All articles pass `check_theory.mjs` and cover 100% (or
nearly) of their references, so the problems are not missing topics. They are:

1. **Facts that are wrong or out of date**, a few of them also wrong in the bank (fix first: the site publishes these pages).
2. **Methods taught one way only.** The forward case is shown; the d3 questions ask the reverse ("when is there enough
   water?", "what course gives CPA 2 M?").
3. **Rules without the reason or the "don't".** The distractors are exactly the don'ts the article leaves out.
4. **Words spent twice**: the new `qa` openers repeated by the first paragraph, and tables repeated across articles.

No arithmetic or sign error was found in any existing worked example.

## How the 900-word cap really works

Almost every article sits at 880–900 words, but the checker counts only lead, kicker, title, `p`, `rule`, `list`,
`cap`, table cells and tile name/note. `card` and `panel` lines, figure notes/labels and `qa` are **not counted**. So a
worked example in a card is free, but a card holds only about 6 lines of about 40 characters (`FIG.card`).

Recommendation: keep worked numbers in cards, but raise the cap to about **1,100 words for calculation topics**
(coastal/offshore `dr`, `tides`, `fixing`, `compass`, `pilotage`; all of ocean; bareboat `navigation` and `buoyage`).
Otherwise the method ends up split across tiny cards with the explanation squeezed out. Elsewhere 900 is enough once
the duplicates below are cut.

## 1. Fix first: wrong or outdated

**Status (5 Nov):** fixed in the articles (English and Russian) and the matching bank questions, except two items.
Not done: the five mark-room "room to tack" questions (rr-061, 062, 344, 345, 375), which wait for a ruling on how
the 2025 definition treats a tack. The Ocean "up to 24 m" line stays: it matches the IYT certificate and yo-bank
uses it. The rule 17, rule 18.2, scoring and mark-room changes were checked against Dave Perry's US Sailing summary
of the 2025 changes and World Sailing Q&A 2025.009.

| Where | Problem | Fix |
|---|---|---|
| racing-rules `limits › r17` | The row "while the windward boat was tacking → No" is the old last sentence of rule 17, deleted in RRS 2025. | Delete the row; say an overlap that begins while she tacks still counts. Add a line in `rightofway › r13`. Bank: rr-279, rr-189. |
| racing-rules `definitions › mark`, `marks › room` | "Mark-room includes room to tack… when overlapped inside and to windward" was removed from the 2025 definition. | Drop it, or label it as guidance. Bank: rr-061, rr-062, rr-344, rr-345, rr-375. |
| racing-rules `starting › prep`, `penalties › scoring` | The Scoring Penalty and Z flag are rounded to a whole number. Under 2025 rule 44.3(c) they round to a tenth of a point. | "5 + 6 = 11" becomes 5 + 6.2 = 11.2. Bank: rr-553 (wrong answer), rr-990 (wrong why). |
| racing-rules `marks › who` | "Boat outside the zone gives room to the boat clear ahead" is not the 2025 18.2(a)(2) test. | The first boat to reach the zone gets mark-room. |
| racing-rules `marks › tack` | Uses "tack finished outside the zone" as the trigger. | Where she passes head to wind decides (rr-336). |
| racing-rules `penalties › exoneration` | Says "rule 15, 16 or 31". | Rule 43.1(b): a Section A rule, rule 15 or 16, or being *compelled* to break 31. |
| yachtmaster-coastal `tides › tables` | The secondary-port method is wrong. It interpolates "between springs and neaps" for both differences, and "LW 0.8 + 0.2" comes from nowhere. | Time difference by the standard port's HW time between the tabulated times; height difference by today's height between MHWN and MHWS. Two-step card. yc-371, 324, 325, 323. |
| yachtmaster-coastal `tides › datum` | "You seldom find less than charted" is said as if it held everywhere. | Not where charts are reduced to mean sea level (much of the Med), or under high pressure. yc-089, 348. |
| yachtmaster-offshore `dr › cts` | "asin(net stream ÷ water distance)" is true only for a stream straight across the track. | Use stream *across* the track, then check hours = ground distance ÷ SOG and redo once. yo-263, 268. |
| international-crew `lookout › rules` | "a vessel fishing with nets or lines" gives priority to anglers and trolling boats. | Use "engaged in fishing": gear that restricts her manoeuvring. ic-126. |
| flotilla-skipper `skipper › papers` | "Crossing to another country… means clearing customs and immigration" is said as if it held everywhere. | Not between Schengen states. Example: Greece to Turkey. fs-180. |
| charter-checkin `papers › papers` vs `› week` | Says only the named skipper may helm, then that the skipper answers for "whoever was steering". | Only a named skipper may be in command; anyone may steer under them. ci-014, 025. |
| charter-checkin `papers › money` | The exclusions list doesn't match the bank: "gross negligence"; no grounding, sails or inventory. Deposit, waiver and excess are blurred. | Full exclusions list plus a worked card (deposit €3,000, waiver excess €500 per incident). ci-003, 004, 023, 050. |
| vhf `licences` | Licensing is written as if it were universal, and the certificate is never named. | Name SRC (VHF/DSC, A1) and LRC. The flag state issues the licence, call sign and MMSI; requirements vary (the US needs none for domestic leisure use). |
| vhf `calls › call` | "Each name up to three times" is the distress form. | ITU-R M.1171 for routine calls: not more than twice. Wait 2–3 min before calling again. |
| international-crew `aboard › heads`, flotilla `systems › water` | "Well out at sea → overboard" is said as if it held everywhere. | "Where local rules allow, usually 3 M+ off; in Turkey never." |
| yachtmaster-ocean `passage` | "Yachtmaster Ocean covers yachts up to 24 m" is an RYA rule. | Remove, or attribute it (docs/theory.md: no official claims). |

Bank-only inconsistencies found along the way: ci-253 says fill water "until it overflows at the filler" but the
article and ci-271 use the hull vent. vhf-111's correct option leaves out the addressee that the article's relay card
includes.

## 2. Methods taught one way only (worked examples to add)

These are the biggest learning gains; most go in cards, so the cap doesn't block them.

- **Tides in reverse**: bareboat `navigation › tides`, coastal `tides › twelfths`. Show "tide needed = draft + clearance −
  charted depth → which twelfth → LW + n h". If the duration isn't 6 h, each "hour" is duration ÷ 6. Curve factor =
  (needed − LW) ÷ range. About 10 questions in coastal alone (yc-315, 316, 318, 338, 359, 363, 366, 372, 393; bs-525).
- **Clearances above HAT**: bareboat `navigation › symbols`. Clearance now = charted + (HAT − height of tide) (bs-470, 547).
- **Course to steer, full chain**: coastal `dr › cts`. Stream → leeway → variation → deviation, with the leeway flip
  (EP: away from the wind; CTS: into it). Card: 000°T, set 270° 1.5 kn → 017°T → leeway 5° → 022°T → 025°M → 024°C.
- **Stream from HDG/log vs COG/SOG**: coastal `dr › plotter`. Card: 000°/5.0 vs 020°/5.5 → about 085° 1.9 kn (yc-136).
- **Variation updated in the westerly case**: bareboat `navigation › compass`, coastal `fixing › compass`. Card: 4°30'W
  2016, 9'E a year → 3°00'W. Also deviation from a transit (bs-484, 493, 542, 546; yc-215, 261).
- **Deviation card between headings**: offshore `compass › deviation`. Card: 180°C 1°E, 225°C 5°W, steering 210°C →
  3°W. Enter the card near the expected compass heading (151, 152, 224, 226, 254).
- **Sounding reduced to datum**: coastal `fixing › radar`. Charted depth = reading + offset − height of tide (about 8
  questions across three topics).
- **Clearing bearings, which side you are on**: coastal `pilotage › lines` (yc-411, 483).
- **Secondary port with LW and the full curve**: offshore `tides › secondary` (308, 309, 354, 356, 357).
- **Radar plotting**: offshore `pilotage › plot`. Two cards: the O-A-W triangle, and the course for a chosen CPA. Seven
  d3 questions (433–435, 471–475).
- **One sun sight from start to finish**: ocean `sun`. Card 1: DR 17°10'N 38°40'W, LHA 329°04.6'. Card 2: Hc 43°40.6',
  Zn 137°, Ho 43°45.0', 4.4 M towards (yo-428–432, 491–497).
- **Azimuth formula**: ocean `sun`, `compass`, `stars`. cos Z = (sin Dec − sin Lat sin Hc) ÷ (cos Lat cos Hc), south
  negative; Zn = Z if LHA > 180°, else 360° − Z. It works in both hemispheres, so the repeated hemisphere tables can go.
- **Moving a position by arithmetic**: ocean `sun › fix`. dLat = d cos C, dep = d sin C, dLong = dep ÷ cos lat.
- **Longitude from noon timing**: ocean `meridian`, `time`. Peak 15 08 UT, Mer Pass 1144 → 3 h 24 min = 51°W; ±2 min ≈ ±30'.
- **Noon latitude**: ocean `meridian › latitude`. It teaches two methods; keep only the signed one the bank uses. Add the
  near-overhead ambiguity warning (yo-358).
- **Great circle**: ocean `greatcircle`. A clearer rule for initial course; the composite leg distance with a worked card
  (yo-718, 719, 775, 735, 779–782).
- **Energy budget**: bareboat `systems › electrics`, offshore `vessel`. Ah a day → usable bank → days → charge time.
- **Ship lights**: bareboat `buoyage › vessels`, `working`. Light arcs (225°, 112.5°, 135°); second masthead light from
  50 m; aground, long tow, dredger and mine clearance. About 30 questions, several d3 (bs-605, 626, 627, 637, 611, 636, 621, 622).
- **Geographic range of a light**: bareboat `buoyage › rhythm`. 2.08 × (√H + √h) (bs-595).
- **DSC alert received**: vhf `dsc › received`, `sar`. Listen about 5 min; if no coast station answers, send a voice
  MAYDAY RELAY. Acknowledge by voice only if you can help, never by DSC. False alert: cancel by voice and stay on 16
  (vhf-097–099, 110, 142, 154, 155).
- **Scripts to cancel**: vhf `urgency › after` (PAN-PAN cancel), `distress › after` (MAYDAY cancel).

## 3. Reasons and "don'ts" to add (one line each)

- Liferaft "step up, not down": give the reason (international-crew `emergency › raft`, flotilla `emergency › fire`).
- Hypothermia: don't rub or walk them about. Burns: no ice, no butter (flotilla `emergency › firstaid`, fs-195, 196).
- Hot engine: never open the coolant cap (flotilla `systems › alarms`, fs-145).
- Telltales: give both windward and leeward cases (flotilla `sailing › trim`, fs-056). Use one word, "flutters", in
  international-crew `sailing` and `helming`.
- Upwind leg: about 1.4 × the distance (flotilla `weather › decision`, fs-135).
- Decimal hours: 0.4 h = 24 min, not 40 (flotilla `skipper › routine`, fs-179).
- BOTH on the battery switch joins the banks (charter `electrics › banks`). Engine heats the calorifier through a coil
  (charter `plumbing › pump`).
- MOB: throw the bag beyond and *upwind* (charter `safety › mob`). Hand off pointing so your hands are free
  (international-crew `emergency › mob`, ic-200).
- Big ship's two masthead lights: the lower one is at the bow, so it shows her heading (international-crew
  `lookout › lights`).
- Define on first use: seacock, joker valve, saildrive diaphragm, close reach, headed/lifted, lazy sheet, sea-state
  words (slight/moderate/rough), "later" in a forecast (a UK Met Office convention).
- Bowline: "holds, but cannot be untied while loaded" (bareboat `ropework`, bs-261).

## 4. Words to free

- **Openers repeated in the first paragraph.** The new `qa` openers (bareboat-skipper so far) are often repeated
  almost word for word by the paragraph below. Rewriting those paragraphs frees 20–40 words a section, about 120 in
  bareboat `buoyage` alone. Whoever adds openers to the other levels should write the first paragraph to follow on
  from the opener, not repeat it.
- **Racing rules repeats**: the Appendix P table (propulsion and penalties), the restart exceptions list (three
  articles), the Z/U/black table (starting and penalties), the Appendix T 30% (penalties and protests). Keep each once.
- **Ocean**: the Hs→Ho steps are repeated in sun and meridian; the Zn hemisphere table appears three times.
- **VHF**: `licences › priority` repeats `urgency › priority`.
- Single cuts: coastal `dr › log` fog paragraph (about 45 words); offshore `tides › races` (about 30); flotilla
  `skipper` and `weather` repeats.

## 5. Figures

- international-crew `boat › rig`: the questions ask about shrouds and spreaders, which the figure doesn't show. Needs
  a bow-on view or new parts in `figures.js`.
- yachtmaster-offshore `vessel › stability`: needs a GZ-curve figure type.
- vhf `sar › helicopter`: replace the empty encounter with a card of the helicopter brief.
- bareboat `weather` Buys Ballot: `isobars` would show it better than `encounter`.
- charter `return › baseline`: a card ("cushions 10; 2 torn seams, photos 14–15") makes the point; the hour-meter
  panel doesn't.

## Verdicts by level

| Level | Needs work | Minor | OK |
|---|---|---|---|
| racing-rules | definitions, limits, marks, starting, penalties | rightofway, obstructions, propulsion, protests | course |
| yachtmaster-ocean | meridian, sun, compass, greatcircle | sphere, time, stars | sextant, weather, passage |
| yachtmaster-coastal | dr, fixing, tides | charts, pilotage, weather | passage, colregs, safety, seamanship |
| yachtmaster-offshore | dr, pilotage | compass, tides, colregs, weather, vessel, seamanship | charts, emergency |
| bareboat-skipper | navigation, buoyage | terms, colregs, weather, anchoring, systems | ropework, safety, emergency |
| vhf-radio-operator | dsc, sar, licences | calls, distress, urgency, gmdss | set, channels, phonetic |
| charter-checkin | papers | engine, electrics, plumbing, nav, safety, return | hull, sails, ground |
| flotilla-skipper | none | power, mooring, sailing, colregs, weather, systems, skipper, emergency | buoyage, pilotage |
| international-crew | none | boat, sailing, lookout, weather, aboard, emergency | knots, deck, helming, safety |

Uncovered references worth a line: offshore colregs Rule 1(e) (553); offshore weather stable vs unstable gusts (644)
and back/veer defined (666); offshore vessel energy budget (795), chainplate load (755), starting circuit (738),
injectors (781), fuel in sump (730). The rest are common sense and can stay uncovered.
