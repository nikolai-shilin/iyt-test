# Racing Rules: figures that disagree with their question

Found while drawing the new race diagrams (November 2026). The question image (`q.png`) follows the figure data in
`data/bank/racing-rules/<topic>.json` exactly, so where the data is wrong the question picture is wrong too. The
answer plans work around it, usually with a faded "ghost" boat in the answer's position. Fixing the data (boat
positions or headings) would fix both the picture and the old 2D figure the MCP server serves.

## The figure contradicts the answer

| Id | Topic | Problem |
|---|---|---|
| rr-034 | definitions | Zone ring sized at the figure scale: Grey is drawn outside it, the answer says both are in the zone |
| rr-053, rr-473 | | Text says port tack; heading 315° draws starboard tack (answer does not depend on it) |
| rr-135 | rightofway | The three boats are in line astern, none overlaps; the answer needs Grey overlapping both |
| rr-155 | rightofway | Your bow 1 unit behind Black's transom line: clear astern, the answer needs an overlap |
| rr-164 | rightofway | Green's hull already overlaps; the text says only her bowsprit does |
| rr-182 | rightofway | Yellow drawn to windward of you; the text says you are to windward of her |
| rr-190 | rightofway | Headings mirrored: You 10° (port), Green 350° (starboard), diverging; the text needs them converging past head to wind |
| rr-199 | rightofway | White at 15°, short of head to wind, though the note says she is tacking |
| rr-260 | limits | Blue drawn ahead and to leeward (overlapped); the answer needs her clear astern on your leeward quarter |
| rr-265 | limits | White drawn ahead and to starboard; the text says she passes astern |
| rr-289, rr-295 | limits | Your heading 170 / 160 draws port tack; "10° / 20° higher on starboard" needs 190 / 200 |
| rr-318 | marks | Your bow already past White's transom (overlapped); the text says clear astern |
| rr-352 | marks | Both hulls well inside the zone; the text says your hull is still outside |
| rr-363 | marks | You drawn ahead of Red, not bow doubtfully level with her transom |
| rr-368 | marks | Zone ring at scale 0.6, neither boat's length (should be 66 units, your boat) |
| rr-375 | marks | Heading 10° is not yet past head to wind; both boats just outside the zone (81 vs 79.2) |
| rr-383 | marks | Grey to windward on port; the question calls her the leeward boat with rule 11 right of way |
| rr-392 | marks | Zone ring at scale 0.6 (should be 112.2, Grey's lengths); you drawn nearer the mark than Grey |
| rr-396 | marks | Red's bow nearer the mark than yours; the text has you reaching the zone first |
| rr-364 | marks | Both drawn on port; the text says both on starboard |
| rr-404 | obstructions | About 2 lengths between 4471 and the shore, and you not quite overlapped |
| rr-405 | obstructions | You still clear astern of Red (about 0.6 lengths) |
| rr-455 | obstructions | Both on the pre-start side heading up; Blue is not returning |
| rr-564 | starting | You drawn at the pin end; the note says near the committee boat |
| rr-669 | course | Flag S boat east of mark 2: crossing leaves the mark to starboard, not port |
| rr-684 | course | You heading south, away from the RIB; the text says running towards mark 2 |
| rr-696 | course | The track rounds the drawn gate mark to port; the text says to starboard |
| rr-833, rr-837, rr-877 | penalties | The outside boat drawn clear astern, not overlapped outside / to windward |
| rr-834 | penalties | Grey clear astern and slightly to windward, not overlapped to leeward |
| rr-855 | penalties | Red drawn to leeward of you; the answer needs her to windward |

## Smaller mismatches (left as drawn)

rr-061, rr-063 (positions don't match "would fetch after tacking" / "the mark abeam"); rr-070 ("15° high" drawn as
about 3°); rr-074, rr-080 (bow about 1 unit short of the line); rr-258 (Grey abeam, not clear astern); rr-412,
rr-803 (1 unit short of overlap); rr-441 (Grey borne away though the text says she luffed); rr-450 (Red would be
fetching, against the answer); rr-465 (Black still below the line though started); rr-499, rr-827, rr-888 (not yet
overlapped / clear ahead / just clear astern); rr-608 (you would pass the mark on the wrong side anyway); rr-637
(transom 1.3 lengths from the mark it "hits").

## Answers worth a rules check

- rr-142: reads like a rule 20 case (room to tack at an obstruction), not plain rule 11 as the answer says.
- rr-365: rule 21.1 cited, but the boat is drawn already below the line.
- rr-263–275: rule 16.2 wording ("shall not bear away") follows the data's 2025 claim; not checked against the text.
- rr-279: the data says 2025 deleted rule 17's last sentence; not checked.
- Rule numbers copied from the `why` texts without checking the 2025–2028 numbering: 61.4(b), 60.5(c), 20.2(e),
  18.1(a), 30.3, 43.1(c), 60.2(a)(1), 60.2(b)(2), 42.3(h)/(i), 48.2, 18.2(a).
