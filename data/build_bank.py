"""Builds data/questions/bareboat-skipper.json from the question list below.

Each question: topic, difficulty, q (the situation), a (the right answer), o (three wrong ones), why (one line),
ref, and fig — a figure spec rendered by docs/design/figures.js, or None for a text question. Answers are placed so
that A/B/C/D are used equally. Run: python3 data/build_bank.py
"""
import json, random, os

Q = []
def q(topic, d, text, a, o, why, ref, fig=None): Q.append(dict(topic=topic, difficulty=d, q=text, a=a, o=o, why=why, ref=ref, fig=fig))

L = lambda **k: dict(type='lights', **k)          # lights: list of {c,x,y,t?}
E = lambda **k: dict(type='encounter', **k)
B = lambda **k: dict(type='buoy', **k)

# ---------------- terms & parts of the boat (10) ----------------
q('terms', 1, 'You are at the helm, sailing with the wind over your right shoulder and the boom out to the left. Which tack are you on?',
  'Starboard tack', ['Port tack', 'Windward tack', 'Lee tack'], 'The tack is named after the side the wind comes over.', 'Sailing terms',
  dict(type='sail', wind=45, hdg=0, note='Wind over the starboard side, boom to port'))
q('terms', 1, 'The skipper shouts "fender on the port quarter!". Where do you hang it?',
  'Left side, near the stern', ['Right side, near the bow', 'Left side, near the bow', 'Right side, near the stern'], 'Port = left; quarter = the side near the stern.', 'Nautical terms')
q('terms', 2, 'From this point of sail you want to turn to sail downwind. Which way do you turn the boat?',
  'Bear away — turn the bow away from the wind', ['Luff up — turn the bow towards the wind', 'Tack', 'Heave to'], 'Bearing away takes you from close-hauled towards a run.', 'Points of sail',
  dict(type='sail', wind=0, hdg=315, nogo=True, note='Close-hauled on starboard tack'))
q('terms', 2, 'The boat is on this heading relative to the wind. What point of sail is it?',
  'Beam reach', ['Close-hauled', 'Broad reach', 'Run'], 'Wind on the beam, about 90° off the bow.', 'Points of sail',
  dict(type='sail', wind=270, hdg=0, nogo=True))
q('terms', 2, 'The boat is pointing into the shaded sector. What happens?',
  'The sails flap and the boat stops — it is the no-go zone', ['The boat sails fastest', 'The boat gybes', 'The boat heels the most'], 'A yacht cannot sail closer than about 40–45° to the wind.', 'Points of sail',
  dict(type='sail', wind=0, hdg=15, nogo=True, note='Red sector: about 45° either side of the wind'))
q('terms', 2, 'The anchorage shows 2.4 m on the sounder at low water. The boat\'s draft is 1.9 m. Can you stay?',
  'Yes — 0.5 m under the keel, but allow for swell', ['No — the mast is too tall', 'No — draft must be at least twice the depth', 'Only if you lift the keel'], 'Draft is the keel depth below the waterline; compare it with depth at low water.', 'Nautical terms',
  dict(type='anchor', depth='2.4 m', tide='low water', title='Sounder at low water', lines=['Draft 1.9 m', 'Swell about 0.3 m']))
q('terms', 1, 'The genoa is flapping on a beam reach. Which line do you pull in?',
  'The genoa sheet', ['The genoa halyard', 'The topping lift', 'The mainsheet'], 'Sheets trim sails; halyards only hoist them.', 'Rigging')
q('terms', 3, 'Downwind the mainsail twists and the top spills wind. Which control pulls the boom down?',
  'The kicker (boom vang)', ['The Cunningham', 'The outhaul', 'The backstay'], 'Off the wind the mainsheet no longer holds the boom down; the vang does.', 'Rigging')
q('terms', 2, 'You are about to turn the stern through the wind on a run. What do you do first?',
  'Centre the mainsheet and warn the crew: "Gybe-ho"', ['Ease the mainsheet fully', 'Release the kicker', 'Drop the headsail'], 'A controlled gybe keeps the boom from slamming across.', 'Sailing manoeuvres',
  {'type': 'sail', 'wind': 180, 'hdg': 350, 'note': 'Running, about to gybe'})
q('terms', 2, 'Berthing in a marina with a strong crosswind, which yacht is harder to keep off the pontoon?',
  'The one with high freeboard — more hull for the wind to push', ['The one with low freeboard', 'The one with a longer keel', 'Freeboard makes no difference'], 'Freeboard is the hull above the water: more freeboard, more windage.', 'Nautical terms')

# ---------------- ropework & knots (10) ----------------
q('ropework', 1, 'You need to put a loop in the end of a mooring line to drop over a bollard. Which knot?',
  'Bowline', ['Clove hitch', 'Reef knot', 'Figure of eight'], 'A bowline makes a fixed loop that will not slip and unties after loading.', 'Knots',
  dict(type='rope', kind='ring', labels=[[160, 40, 'bollard']], note='Loop in the end of a line'))
q('ropework', 1, 'The jib sheet has run out through the block and is flogging. What stops this happening again?',
  'A figure of eight in the end of the sheet', ['A bowline tied to the clew', 'A clove hitch round the block', 'A reef knot in the end of the sheet'], 'The stopper will not pass through the block.', 'Knots',
  {'type': 'rope', 'kind': 'sheet', 'labels': [[90, 180, 'sheet end'], [220, 180, 'block']]})
q('ropework', 2, 'Hanging fenders on the guardrail before berthing, you want to adjust their height quickly. Which knot?',
  'Clove hitch', ['Bowline', 'Round turn and two half hitches', 'Sheet bend'], 'Quick to tie and slide; not for anything that must not work loose.', 'Knots',
  dict(type='rope', kind='rail', labels=[[160, 80, 'guardrail']]))
q('ropework', 2, 'You must join the thin dinghy painter to a thick mooring line. Which knot?',
  'Sheet bend', ['Reef knot', 'Clove hitch', 'Bowline'], 'A sheet bend holds ropes of different sizes; a reef knot can capsize.', 'Knots')
q('ropework', 2, 'The dinghy is tugging hard on its painter and you must tie it to a ring on the quay. Which knot can you tie under load?',
  'Round turn and two half hitches', ['Reef knot', 'Figure of eight', 'Sheet bend'], 'The round turn takes the load while you tie the hitches.', 'Knots',
  dict(type='rope', kind='ring', labels=[[160, 40, 'quay ring']], note='Dinghy pulling on the line'))
q('ropework', 2, 'This line is being made fast to a cleat. What completes it correctly?',
  'A full turn round the base, figure-of-eight turns, one locking hitch', ['Five round turns and no hitch', 'A bowline round the cleat', 'Two half hitches on the horn'], 'The turn takes the load; the locking hitch holds without jamming.', 'Deckwork',
  dict(type='rope', kind='cleat', labels=[[160, 150, 'cleat']]))
q('ropework', 3, 'A riding turn has jammed the genoa sheet on the winch under full load. How do you free it?',
  'Tie a rolling hitch on the sheet with a spare line, take the load on another winch, then clear the turns', ['Cut the sheet', 'Release the halyard', 'Pull the tail harder to drag the riding turn through'], 'The rolling hitch grips the loaded sheet and lets you transfer the load.', 'Knots',
  {'type': 'rope', 'kind': 'winch', 'labels': [[80, 86, 'loaded sheet'], [255, 90, 'tail'], [160, 170, 'riding turn on the drum']]})
q('ropework', 2, 'You are choosing rope for a new anchor rode. Which material?',
  'Nylon — it stretches and absorbs shock loads', ['Polyester — low stretch', 'Polypropylene — it floats', 'Dyneema — strongest'], 'Elastic nylon protects the boat and fittings in gusts and waves.', 'Rope types')
q('ropework', 2, 'The dinghy painter keeps sinking and nearly fouled the propeller. Which rope should it be?',
  'Polypropylene — it floats', ['Nylon', 'Polyester', 'Wire'], 'A floating painter stays clear of the prop.', 'Rope types')
q('ropework', 2, 'You are loading the genoa sheet onto a winch in a fresh breeze. How many turns before you start winding?',
  'Two or three, clockwise, fingers clear of the drum', ['One, anticlockwise', 'Five, anticlockwise', 'As many as fit'], 'Yacht winches turn clockwise; three turns give grip without a riding turn.', 'Deckwork',
  dict(type='rope', kind='winch', labels=[[80, 86, 'sheet'], [255, 90, 'tail']]))

# ---------------- safety (10) ----------------
q('safety', 1, 'You are crossing to the next island at night in 20 knots. Who wears a lifejacket?',
  'Everyone on deck, clipped on when going forward', ['Only non-swimmers', 'Only the helm', 'Nobody — the sea is moderate'], 'Night, fresh wind and deck work are the standard triggers.', 'Personal safety',
  dict(type='card', title='Night passage', lines=['Wind 20 kn, sea moderate', 'Crew of 5, two have never sailed', '14 miles to go'], tag='2:10 am'))
q('safety', 2, 'A pan of oil has caught fire on the galley stove. What do you do?',
  'Turn off the gas, smother it with the fire blanket', ['Throw water on it', 'Carry the pan on deck', 'Open all hatches'], 'Water turns to steam and spreads burning fat.', 'Fire',
  dict(type='card', title='Galley fire', lines=['Pan of oil burning on the stove', 'Fire blanket beside the companionway', 'Extinguisher in the saloon'], tag='FIRE'))
q('safety', 2, 'Before lighting the stove you notice a faint gas smell in the cabin. What first?',
  'No flames or switches — ventilate, pump the bilge by hand, check the system', ['Light the stove quickly to burn it off', 'Start the engine to ventilate', 'Switch on the cabin fan'], 'LPG sinks into the bilge; any spark can ignite it.', 'Gas safety')
q('safety', 2, 'You are driving the dinghy alone to the beach. Where is the kill cord?',
  'Attached to your leg or lifejacket', ['Tied to the dinghy handle', 'In your pocket', 'Left on the yacht'], 'If you fall out, the cord pulls and the engine stops.', 'Dinghy safety')
q('safety', 2, 'A crew member goes over the side on a broad reach. What is the very first thing you shout and do?',
  '"Man overboard!" — throw the danbuoy and horseshoe, point at the casualty', ['Send a Mayday', 'Start the engine', 'Drop the sails'], 'Flotation first and a spotter who never looks away.', 'Man overboard',
  {'type': 'encounter', 'you': {'hdg': 0, 'sail': True, 'boom': 14}, 'other': {'bearing': -165, 'dist': 70, 'hdg': 0, 'scale': 0.3, 'label': 'MOB'}, 'wind': 225, 'note': 'Casualty astern to port'})
q('safety', 3, 'The yacht has hit a rock and is taking water, but the pumps are keeping up for now. The liferaft?',
  'Prepare it on deck on its painter, but stay aboard while the yacht floats', ['Launch and board it immediately', 'Leave it stowed until the deck is awash', 'Inflate it in the cockpit'], '"Step up into the liferaft" — the yacht is the better survival platform.', 'Abandoning ship')
q('safety', 2, 'The charter check-out is done and the crew are aboard. Before leaving the marina you…',
  'Give the safety briefing: lifejackets, gas, heads, fire, MOB, VHF, flares', ['Set the sails', 'Check their passports', 'Hand out the cabins'], 'Everyone must know where the gear is and how to call for help.', 'Skipper\'s responsibilities')
q('safety', 3, 'You have recovered a crew member after 15 minutes in 16 °C water. They shiver, mumble and cannot grip. What do you do?',
  'Handle gently and horizontally, strip wet clothes, insulate, warm slowly', ['Give brandy to warm them', 'Make them walk around the deck', 'Put them in a hot shower immediately'], 'Hypothermia: gradual rewarming, no alcohol, no rough handling.', 'First aid')
q('safety', 2, 'During check-in you find the spare gas bottle stowed under the aft bunk. Where should it be?',
  'In the gas locker that drains overboard', ['Under the bunk is fine', 'In the engine bay', 'In the cockpit locker with the fuel'], 'Leaking gas must drain over the side, not into the bilge.', 'Gas safety')
q('safety', 2, 'Reefing in a rising wind, the foredeck crew goes forward. What is clipped where?',
  'Harness tether to the jackstay before leaving the cockpit', ['Tether to the guardrail', 'Nothing — it only takes a minute', 'Tether to the halyard'], 'Jackstays run the length of the deck; guardrails are not strong points.', 'Personal safety')

# ---------------- COLREGs (10) ----------------
q('colregs', 1, 'Both yachts are sailing. Who gives way?',
  'You — you are on port tack, she is on starboard', ['She gives way', 'The windward boat', 'Neither'], 'Rule 12: port tack keeps clear of starboard tack.', 'COLREGs Rule 12',
  E(you=dict(hdg=45, sail=True, boom=14), other=dict(bearing=300, dist=85, hdg=315, sail=True, boom=-14), wind=0, bearingLine=True))
q('colregs', 2, 'Both yachts are on starboard tack. Who gives way?',
  'You — you are the windward boat', ['She gives way', 'The faster boat', 'The one to port'], 'Rule 12: same tack, windward keeps clear of leeward.', 'COLREGs Rule 12',
  E(you=dict(hdg=60, sail=True, boom=-14), other=dict(bearing=-80, dist=80, hdg=60, sail=True, boom=-14), wind=150, bearingLine=True))
q('colregs', 2, 'You are motor-sailing with the engine in gear. A yacht under sail alone is crossing from your starboard. Who gives way?',
  'You — under power you are a power-driven vessel', ['She does — you have sails up', 'Nobody, both are sailing', 'The one on port tack'], 'Rule 3: sail plus engine = power-driven; show the cone by day.', 'COLREGs Rule 3 / 18',
  E(you=dict(hdg=0, sail=True, boom=-14), other=dict(bearing=60, dist=85, hdg=270, sail=True, boom=-14), wind=45, bearingLine=True, note='Your engine is running and in gear'))
q('colregs', 2, 'Motoring, you see a motorboat crossing on this bearing, which has not changed for five minutes. What do you do?',
  'Give way — alter course to starboard, early and clearly, and pass astern of her', ['Hold course, she is to starboard so she gives way', 'Speed up to cross ahead', 'Alter course to port'], 'Rule 15: she is on your starboard side, so you keep clear; avoid crossing ahead.', 'COLREGs Rule 15',
  E(you=dict(hdg=0), other=dict(bearing=50, dist=90, hdg=270), bearingLine=True, note='Bearing steady at 050° relative'))
q('colregs', 1, 'Two motor yachts are meeting head-on in a channel. What do you do?',
  'Alter course to starboard; pass port side to port side', ['Alter to port', 'Hold course — the bigger one moves', 'Stop and wait'], 'Rule 14: both turn to starboard.', 'COLREGs Rule 14',
  E(you=dict(hdg=0), other=dict(bearing=0, dist=90, hdg=180), bearingLine=True))
q('colregs', 2, 'Under sail you are catching up a slow motorboat from astern. Who gives way?',
  'You — the overtaking vessel always keeps clear', ['The motorboat — sail has priority', 'Neither', 'The one to starboard'], 'Rule 13 overrides sail-over-power.', 'COLREGs Rule 13',
  E(you=dict(hdg=0, sail=True, boom=-14), other=dict(bearing=5, dist=85, hdg=0), wind=120, bearingLine=True, note='You are faster, approaching from well abaft her beam'))
q('colregs', 2, 'Under sail you meet a vessel with these shapes, towing nets. Who gives way?',
  'You — sail keeps clear of a vessel engaged in fishing', ['The fishing vessel', 'Whoever is on port tack', 'Neither, pass at a distance'], 'Rule 18: sail gives way to fishing, NUC and RAM.', 'COLREGs Rule 18',
  dict(type='dayshape', shape='two-cones', note='Two cones apexes together: vessel engaged in fishing'))
q('colregs', 2, 'In sight of a ship, you hear one short blast from her. What is she telling you?',
  'I am altering my course to starboard', ['I am altering to port', 'I am going astern', 'I do not understand your intentions'], 'One short: starboard; two: port; three: astern; five: doubt.', 'COLREGs Rule 34')
q('colregs', 2, 'You are sailing up a narrow channel with a ferry coming behind you. Where do you keep?',
  'As far to the starboard side of the channel as is safe, and do not impede the ferry', ['In the middle, you have right of way under sail', 'On the port side', 'Tack across the channel freely'], 'Rule 9: keep right and do not hamper vessels confined to the channel.', 'COLREGs Rule 9')
q('colregs', 3, 'Motoring at night you see these lights on a steady bearing, closing. What vessel is it and what do you do?',
  'A power-driven vessel crossing from your starboard — give way, turn to starboard', ['A sailing vessel — hold course', 'A vessel at anchor — pass either side', 'A vessel overtaking you — hold course'], 'Red sidelight with a masthead light above: a power vessel showing you her port side.', 'COLREGs Rules 15 / 23',
  L(lights=[dict(c='w', x=200, y=78, t='white'), dict(c='r', x=196, y=118, t='red')], note='Night · bearing 045° relative, steady'))

# ---------------- navigation (10) ----------------
q('navigation', 1, 'You need the distance between two headlands on the chart. Where do you measure it?',
  'On the latitude scale at the side, level with the position', ['On the longitude scale along the bottom', 'Anywhere on the border', 'With the compass rose'], 'One minute of latitude = one nautical mile; longitude minutes shrink with latitude.', 'Chartwork')
q('navigation', 3, 'The chart gives this variation; your compass has no deviation. Your plotted true course is 090°. What do you steer?',
  '094°M', ['086°M', '090°M', '098°M'], 'True to magnetic: add west ("west is best").', 'Compass conversion',
  {'type': 'compass', 'variation': -4, 'course': 90})
q('navigation', 3, 'The compass reads 215°C. Deviation on this heading is 3°E, variation 2°W. What is the true course?',
  '216°T', ['210°T', '214°T', '220°T'], 'Compass → true: add east, subtract west: 215 + 3 − 2 = 216.', 'Compass conversion',
  dict(type='compass', variation=-2, deviation=3, course=215, courseLabel='Compass course', note='C → M → T'))
q('navigation', 2, 'The hand-bearing compass agrees with the steering compass on some headings but differs by 5° on others. What is this error?',
  'Deviation — the boat\'s own magnetic field', ['Variation', 'Leeway', 'Tidal set'], 'Deviation changes with heading; variation does not.', 'Compass')
q('navigation', 2, 'You left the marina at 09:30 and the log reads 12.0 M at 12:00. What has your average speed been?',
  '4.8 knots', ['6.0 knots', '5.2 knots', '4.0 knots'], '12 miles in 2.5 hours.', 'Speed, time, distance')
q('navigation', 2, 'Your draft is 1.9 m. Can you cross the shoal on the track at the time shown?',
  'Yes — 1.5 m charted + 1.2 m tide = 2.7 m, about 0.8 m clearance', ['No — 1.5 m is less than the draft', 'Only at low water', 'Only if the tide is falling'], 'Depth now = charted depth + height of tide.', 'Charts / tides',
  {'type': 'chart', 'depths': [[60, 60, '8'], [110, 90, '5'], [150, 118, '1.5'], [120, 150, '4'], [220, 150, '7'], [90, 170, '12']], 'track': 'M30 170 L150 118 L260 60', 'boat': [40, 168, 67], 'panel': ['Now 14:00', 'Height of tide 1.2 m', 'Draft 1.9 m'], 'note': 'Depths in metres below chart datum'})
q('navigation', 2, 'Which of the depths on this chart will dry at low water?',
  'The underlined 0.8 — a drying height above chart datum', ['The 1.5', 'The 4', 'None of them'], 'Underlined figures are heights above datum that uncover.', 'Charts',
  dict(type='chart', depths=[[60, 60, '8'], [120, 100, '4'], [170, 130, '0.8', True], [230, 90, '1.5'], [90, 160, '12']], note='Depths in metres · underlined = drying height'))
q('navigation', 2, 'Entering harbour, the two beacons must be kept in line. What are they called and what do they give you?',
  'A transit (leading line) — a precise position line without a compass', ['A cardinal pair — safe water between them', 'A range marker for distance', 'A traffic lane'], 'Two charted objects in line = one accurate position line.', 'Pilotage',
  dict(type='chart', land='M0 0 H320 V40 H200 V100 H120 V40 H0 Z', marks=[[160, 30, 'w', 'rear'], [160, 70, 'w', 'front']], track='M160 190 L160 80', boat=[160, 180, 0], labels=[[160, 125, 'keep in line', 'middle']], note='Leading marks into the harbour'))
q('navigation', 3, 'You take bearings of the lighthouse, the tower and the headland and plot them. They form a small triangle. Where are you?',
  'Inside the cocked hat — take the corner nearest danger as your position', ['At the lighthouse bearing', 'Halfway to the tower', 'You cannot tell without GPS'], 'A three-bearing fix; the triangle shows the error.', 'Position fixing',
  dict(type='chart', land='M0 0 H320 V36 H0 Z', marks=[[40, 30, 'k', 'lighthouse'], [160, 30, 'k', 'tower'], [290, 30, 'k', 'headland']], track='M40 36 L170 150 M160 36 L172 160 M290 36 L166 156', labels=[[200, 170, 'cocked hat', 'middle']], note='Three bearings plotted'))
q('navigation', 2, 'High water is 3.6 m, low water 1.2 m. What is the range, and what does the rule of twelfths say about the third hour of the rise?',
  'Range 2.4 m; 3/12 of it (0.6 m) rises in the third hour', ['Range 4.8 m; 1/12 in the third hour', 'Range 2.4 m; half of it in the third hour', 'Range 1.2 m; 3/12 in the third hour'], 'Range = HW − LW; twelfths: 1, 2, 3, 3, 2, 1.', 'Tides')

# ---------------- buoyage & lights (10) ----------------
q('buoyage', 1, 'Entering a Mediterranean harbour from seaward you see this buoy. Which side do you leave it on?',
  'To port', ['To starboard', 'Either side', 'Pass astern of it'], 'Region A: red can to port when returning.', 'IALA buoyage',
  B(kind='lat-port', topmark=True, rhythm='Fl R', note='Entering harbour from seaward'))
q('buoyage', 2, 'This mark is ahead. Where is the safe water?',
  'North of the mark', ['South of the mark', 'Either side', 'West of the mark'], 'North cardinal: black over yellow, both cones up.', 'Cardinal marks',
  B(kind='card-n', rhythm='Q', rhythmNote='continuous quick'))
q('buoyage', 2, 'At night you see a white light flashing six times then one long flash. What is it and where do you pass?',
  'A south cardinal — pass south of it', ['A north cardinal — pass north', 'A west cardinal — pass west', 'An isolated danger — any side'], "Clock face: 6 o'clock plus a long flash = south.", 'Cardinal marks',
  {'type': 'lights', 'lights': [{'c': 'w', 'x': 160, 'y': 128, 't': 'Q(6)+LFl 15s'}], 'note': 'Night · six quick flashes, then one long'})
q('buoyage', 2, 'You see this mark. Which way round do you go?',
  'Keep clear, but you may pass on any side', ['Only to the north', 'Only to the east', 'Through the middle'], 'Isolated danger: black with red bands, two balls; danger right under it.', 'Isolated danger marks',
  B(kind='iso', rhythm='Fl(2)', rhythmNote='white, group of two'))
q('buoyage', 2, 'This buoy is at the harbour approach. What does it tell you?',
  'Safe water all round — a landfall or mid-channel mark', ['Danger right here', 'Keep to the west', 'An anchorage limit'], 'Red and white vertical stripes, red ball: safe water.', 'Safe water marks',
  B(kind='safe', rhythm='Iso / LFl 10s', rhythmNote='white'))
q('buoyage', 2, 'A yellow buoy with this topmark sits off the beach. What is it?',
  'A special mark — check the chart (swimming area, pipeline, spoil ground)', ['A cardinal mark', 'A wreck mark', 'A lateral mark'], 'Yellow with an X: not a navigation mark in itself.', 'Special marks',
  B(kind='special', rhythm='Fl Y'))
q('buoyage', 2, 'At night you see these lights ahead and no others. What is it?',
  'A sailing vessel under sail (red over green masthead lights optional)', ['A trawler', 'A pilot vessel', 'A vessel aground'], 'Red over green at the masthead plus sidelights is a sailing vessel.', 'Navigation lights',
  L(lights=[dict(c='r', x=160, y=60, t='red'), dict(c='g', x=160, y=84, t='green'), dict(c='g', x=140, y=124), dict(c='r', x=180, y=124)]))
q('buoyage', 2, 'You see a single steady white light low down, its bearing slowly changing. What is most likely?',
  'The sternlight of a vessel moving away — or an anchored vessel; watch the bearing', ['A vessel coming straight at you', 'A lighthouse', 'A fishing vessel'], 'One white light: stern view or at anchor; only the bearing tells you which.', 'Navigation lights',
  {'type': 'lights', 'lights': [{'c': 'w', 'x': 160, 'y': 122, 't': 'white'}], 'note': 'Night · steady white light, bearing drawing slowly left'})
q('buoyage', 3, 'At night you see these lights. What vessel, and who gives way?',
  'A trawler — green over white; you keep clear under sail or power', ['A pilot vessel — hold course', 'A vessel not under command', 'A vessel towing'], 'Green over white = trawling; fishing has priority over sail.', 'Navigation lights',
  L(lights=[dict(c='g', x=160, y=58, t='green'), dict(c='w', x=160, y=82, t='white'), dict(c='g', x=140, y=124), dict(c='r', x=180, y=124)]))
q('buoyage', 3, 'You are switching from sail to engine at night. Which lights do you turn on and off?',
  'Off: tricolour. On: steaming light plus deck-level sidelights and sternlight', ['Leave the tricolour on and add the steaming light', 'Tricolour and anchor light', 'Only the all-round white'], 'Tricolour is for sail only; never with the steaming light.', 'Navigation lights',
  L(lights=[dict(c='r', x=140, y=46), dict(c='g', x=180, y=46), dict(c='w', x=160, y=40, t='tricolour (masthead)')], note='Yacht under sail — about to start the engine'))

# ---------------- weather (10) ----------------
q('weather', 1, 'The forecast chart shows isobars packed tightly over your area tomorrow. What do you expect?',
  'Strong wind — stay in port or reef early', ['Calm and fog', 'Light variable winds', 'A sea breeze only'], 'Close isobars = steep pressure gradient = strong wind.', 'Synoptic charts',
  dict(type='isobars', center='L', tight=True, values=['996', '1000', '1004'], boat=[250, 150, 0]))
q('weather', 2, 'The low is to the north-west of you. From which direction will the wind blow?',
  'From the south-west, veering as the low passes', ['From the north-east', 'From the east, steady', 'Straight towards the low'], 'Northern hemisphere: wind anticlockwise round a low; Buys Ballot — back to wind, low on the left.', 'Pressure systems',
  {'type': 'isobars', 'center': 'L', 'boat': [260, 160, 0], 'note': 'Low centre to the NW of the yacht'})
q('weather', 1, 'The forecast says "F6, occasionally 7". What wind speed is that?',
  'About 22–33 knots', ['11–16 knots', '4–6 knots', '41–47 knots'], 'F6 is 22–27 kn, F7 28–33 kn — the limit for comfortable cruising.', 'Beaufort scale')
q('weather', 2, 'In three hours the barometer has fallen from 1012 to 1006 hPa. What does it mean for your afternoon passage?',
  'A depression is approaching — expect strengthening wind; reconsider', ['Fine settled weather', 'Fog is likely', 'No change'], 'A fall of 6 hPa in 3 h is a strong warning.', 'Barometer',
  dict(type='card', title='Barometer', lines=['09:00  1012 hPa', '12:00  1006 hPa', 'Sky: high cloud thickening from the west'], tag='−6 hPa / 3 h'))
q('weather', 2, 'A hot sunny morning, calm. By 14:00 a steady 15-knot onshore wind has set in. What is it?',
  'A sea breeze — it will die at sunset', ['A front passing', 'The Meltemi', 'A land breeze'], 'Warm land draws air in from the sea on sunny afternoons.', 'Local winds',
  dict(type='bay', wind=180, spots=[], labels=[[160, 30, 'LAND — hot', 'middle'], [160, 170, 'SEA — cool', 'middle']], note='Afternoon, clear sky, wind onshore'))
q('weather', 2, 'Aegean, July. The forecast shows this pattern for a week. What wind?',
  'The Meltemi — strong dry northerly, F5–7, strongest in the afternoon', ['A warm southerly', 'Sea fog', 'Thunderstorms'], 'High over the Balkans, low over Turkey: the Meltemi.', 'Mediterranean winds',
  dict(type='isobars', center='H', boat=[250, 170, 0], hemisphere='Aegean · July', note='High to the NW, low over Anatolia to the E'))
q('weather', 2, 'Thin high cloud is thickening from the west, a halo rings the sun, the glass is falling. What is coming?',
  'A warm front — rain and strengthening wind within hours', ['A sea breeze', 'Settled high pressure', 'A squall line in minutes'], 'Cirrus → cirrostratus → altostratus is the warm-front sequence.', 'Fronts')
q('weather', 2, 'You have no internet. Where do you get a reliable marine forecast?',
  'Navtex, the coastal VHF broadcast or the harbour office', ['Yesterday\'s newspaper', 'A crew member\'s guess', 'The marina bar'], 'Use current official sources and note the time of issue.', 'Forecast sources')
q('weather', 3, 'Wind F5 blowing against a 2-knot current in the strait you are about to enter. What sea do you expect?',
  'Short, steep breaking seas — worse than the wind suggests', ['Flatter water', 'A long smooth swell', 'No change'], 'Wind against tide shortens and steepens the waves.', 'Sea state',
  E(you=dict(hdg=0), other=dict(bearing=0, dist=0, hdg=0, scale=0.01), wind=0, note='Wind from the north · current setting north at 2 kn'))
q('weather', 2, 'The forecast says visibility "poor". What does that mean for your passage?',
  '1000 m to 2 miles — post a lookout, slow down, sound fog signals if it closes', ['Under 100 m', 'More than 5 miles', 'Normal summer haze'], 'Fog <1000 m; poor 1000 m–2 M; moderate 2–5 M; good >5 M.', 'Forecast terms')

# ---------------- anchoring & mooring (10) ----------------
q('anchoring', 1, 'You anchor in 5 m at high water with all chain, settled weather. How much chain do you let out?',
  'At least 24 m (4 × depth to the roller), more if wind is expected', ['5 m', '10 m', '50 m'], 'Chain scope 4:1 minimum, measured from the bow roller; 6:1 or more in strong wind.', 'Anchoring',
  {'type': 'anchor', 'depth': '5 m', 'tide': 'high water', 'title': 'Settled evening, F2', 'lines': ['All-chain rode', 'Bow roller 1 m above water']})
q('anchoring', 2, 'Wind is forecast to go round to the south overnight. Which spot do you anchor in?',
  'Spot A — sheltered by the land to the south', ['Spot B — open to the south', 'Spot C — in the channel', 'Any, the bay is calm now'], 'Choose shelter from the forecast wind, not the present one.', 'Anchoring',
  {'type': 'bay', 'wind': 180, 'land': 'M0 200 H190 V135 C 150 120 60 125 0 130 Z M250 200 H320 V110 C 300 120 270 140 250 150 Z', 'spots': [[90, 95, 'A'], [220, 60, 'B'], [220, 150, 'C']], 'labels': [[95, 165, 'LAND (south)', 'middle'], [220, 128, 'channel', 'middle']], 'note': 'Forecast: wind backing south overnight, F5'})
q('anchoring', 2, 'The chart shows these seabeds. Where will the anchor hold best?',
  'Sand (S)', ['Weed (Wd)', 'Rock (R)', 'Shingle (Sn)'], 'Sand and mud let the anchor dig in; weed and rock do not.', 'Anchoring',
  dict(type='chart', depths=[[60, 80, 'S'], [140, 60, 'Wd'], [220, 90, 'R'], [120, 150, 'Sn'], [240, 160, 'M']], note='Chart seabed abbreviations'))
q('anchoring', 2, 'The anchor is down and the chain paid out. What next?',
  'Reverse gently to dig it in, then check transits ashore or the anchor alarm', ['Go below for dinner', 'Motor ahead over the anchor', 'Tie the chain to the pulpit'], 'Set the anchor and prove it is holding before relaxing.', 'Anchoring')
q('anchoring', 2, 'You are anchored in a busy bay by day. What do you hoist?',
  'A black ball forward', ['A black cone', 'A yellow flag', 'Nothing by day'], 'Rule 30: ball by day, all-round white light at night.', 'COLREGs Rule 30',
  dict(type='dayshape', shape='ball', note='Day shape forward'))
q('anchoring', 3, 'The anchor is fouled under a rock and will not come up. What would have made this easy?',
  'A trip line and buoy on the anchor crown', ['A longer chain', 'A second anchor', 'A heavier anchor'], 'Pull the crown and the anchor comes out backwards.', 'Anchoring')
q('anchoring', 2, 'Berthing stern-to with your own anchor in a Greek harbour. When do you drop the anchor?',
  'About 3–4 boat lengths out, reversing towards the quay, paying out as you go', ['When the stern touches the quay', 'Before turning, at the harbour entrance', 'After the stern lines are on'], 'Drop early, keep tension, stern lines ashore, then snug the chain.', 'Med mooring',
  dict(type='chart', land='M0 0 H320 V40 H0 Z', track='M160 180 L160 60', marks=[[160, 170, 'k', 'drop here']], boat=[160, 90, 180], labels=[[160, 30, 'QUAY', 'middle'], [200, 130, '3–4 boat lengths', 'start']], note='Stern-to, reversing towards the quay'))
q('anchoring', 2, 'The marinero hands you a slimy line from the quay as you reverse in. What is it and where does it go?',
  'A lazy line — walk it forward and make the heavy end fast on the bow cleat', ['A spring — tie it to the midship cleat', 'The stern line — cleat it aft', 'A fender line'], 'The lazy line replaces your anchor; it holds the bow.', 'Med mooring')
q('anchoring', 2, 'Alongside a pontoon the boat surges back and forth with the wash. Which line stops it?',
  'A spring — run diagonally from bow aft or from stern forward', ['A breast line', 'The bow line', 'A second stern line'], 'Breasts and bow/stern lines hold the boat in; springs stop fore-and-aft movement.', 'Mooring alongside')
q('anchoring', 3, 'The wind is pinning you against the pontoon. How do you leave?',
  'Spring the stern out: bow spring led aft, fender the bow, helm towards the pontoon, gently ahead, then astern clear', ['Full ahead with full rudder', 'Push off by hand and hope', 'Wait for the wind to change'], 'Ahead against a bow spring pivots the boat on the bow and swings the stern out into the wind.', 'Boat handling',
  dict(type='bay', wind=90, land='M0 0 H40 V200 H0 Z', spots=[], labels=[[20, 100, 'PONTOON', 'middle'], [130, 100, 'yacht pinned on', 'middle']], note='Wind onto the pontoon, F4'))

# ---------------- systems (10) ----------------
q('systems', 1, 'Before starting the engine for the day, what do you check?',
  'Oil, coolant, belt, raw-water seacock open, bilge, gear in neutral', ['Fuel level only', 'Battery voltage only', 'That the sails are furled'], 'A daily engine check takes two minutes and prevents most breakdowns.', 'Engine checks')
q('systems', 2, 'The engine has just started. What is wrong here?',
  'No cooling water at the exhaust — stop, check the seacock and strainer', ['Nothing, it needs to warm up', 'The oil pressure is too high', 'The battery is flat'], 'Running dry overheats the engine and shreds the impeller.', 'Engine cooling',
  dict(type='panel', gauges=[['Temp', '40°', False], ['Oil', 'OK', False], ['Volts', '13.8', False]], lines=['Exhaust: dry, no water pulsing out', 'Seacock: ?']))
q('systems', 2, 'Half an hour into the passage you see this. What do you do?',
  'Stop the engine, sail or anchor, let it cool and find the cause', ['Keep going to the marina', 'Open the coolant cap and add cold water now', 'Rev it to clear the blockage'], 'An overheating engine can seize; never open a hot pressurised cap.', 'Engine troubleshooting',
  dict(type='panel', gauges=[['Temp', '110°', True], ['Oil', 'OK', False], ['Volts', '14.1', False]], lines=['Alarm sounding', 'Exhaust water: a trickle']))
q('systems', 2, 'Morning after a night at anchor with fridge and lights on. Can you start the engine?',
  'Yes — the engine battery was isolated; the house bank is low', ['No — all batteries are flat', 'Only after an hour of solar', 'Only by hand crank'], 'Separate banks keep starting power away from house loads.', 'Electrics',
  {'type': 'panel', 'gauges': [['House', '11.8 V', True], ['Engine', '12.7 V', False], ['Solar', '2 A', False]], 'lines': ['Fridge and anchor light ran all night']})
q('systems', 2, 'The engine loses power, surges and stops after you refuelled at a dusty quay. Most likely?',
  'Dirty or watery fuel — drain the separator, change the filter', ['A broken belt', 'A flat battery', 'A fouled propeller'], 'Fuel contamination is the commonest cause of stopping.', 'Fuel system')
q('systems', 2, 'A loud bang, the engine stops; the dinghy painter is no longer in the water. What now?',
  'Do not restart; try to free the rope from the prop from the dinghy, engine off and key out', ['Restart in reverse to unwind it', 'Keep trying to start', 'Send a Mayday'], 'A line round the prop; a spinning prop and a swimmer never mix.', 'Propeller')
q('systems', 2, 'Water is coming in at the heads inlet hose. What do you do first?',
  'Close that seacock', ['Open all seacocks', 'Pump the heads faster', 'Switch off the batteries'], 'Every through-hull has a seacock; know where they are.', 'Hull fittings')
q('systems', 2, 'Briefing the crew on the marine toilet, what are the rules?',
  'Nothing but what you have eaten, a little paper, pump plenty, close the seacocks at sea', ['Use bleach daily', 'Flush with the inlet closed', 'Pump once only'], 'Blocked heads are the number-one charter complaint.', 'Heads')
q('systems', 3, 'Reversing out of the berth the stern swings to port by itself. What is happening and how do you use it?',
  'Prop walk from a right-handed propeller — berth port-side-to and use a burst astern to pull the stern in', ['Rudder failure', 'A crosswind', 'The bow thruster is stuck'], 'A right-handed prop kicks the stern to port in astern.', 'Boat handling under power',
  E(you=dict(hdg=0), other=dict(bearing=0, dist=0, hdg=0, scale=0.01), note='Engine astern, rudder centred: stern walks to port'))
q('systems', 2, 'At the fuel berth with two deck fillers side by side. What do you do?',
  'Check the cap says DIESEL, engine and electrics off, no smoking, fill slowly', ['Fill the nearer one', 'Keep the engine running to save time', 'Fill to the brim'], 'Diesel in the water tank ruins the trip; a spill is a fine.', 'Fuelling',
  dict(type='card', title='Fuel berth', lines=['Deck fillers: WATER · DIESEL · WASTE', 'Engine running, cabin lights on', 'Crew smoking on the quay'], tag='check'))

# ---------------- VHF, distress & emergencies (10) ----------------
q('emergency', 1, 'You want to call the marina for a berth. Which channel do you call on, and where do you move to?',
  'Call on 16 (or the marina\'s working channel if known), then switch to the working channel', ['Call and talk on 16', 'Channel 70', 'Channel 6 only'], 'Channel 16 is for calling and distress; routine talk moves off it.', 'VHF')
q('emergency', 2, 'Which call is right for this situation?',
  'MAYDAY — grave and imminent danger to the vessel and crew', ['PAN-PAN', 'SÉCURITÉ', 'A routine call to the coastguard'], 'Fire spreading below with people aboard is grave and imminent danger.', 'Distress procedure',
  dict(type='card', title='Fire below', lines=['Engine-bay fire spreading to the saloon', 'Extinguishers used, smoke everywhere', '5 people aboard, 6 miles offshore'], tag='MAYDAY?'))
q('emergency', 2, 'After "MAYDAY ×3, this is Aurora ×3", what comes next?',
  'MAYDAY Aurora, position, nature of distress, help required, persons aboard, OVER', ['Weather and destination', 'The charter company\'s phone number', 'Switch to channel 70'], 'Position early so rescue starts even if you are cut off.', 'Distress procedure')
q('emergency', 2, 'Your DSC radio has a red button under a flap. What happens when you hold it for five seconds?',
  'A digital distress alert with your MMSI and position goes out on channel 70; the radio switches to 16 for the voice Mayday', ['A flare fires', 'The EPIRB activates', 'It calls the marina'], 'DSC first, then voice on 16.', 'DSC')
q('emergency', 2, 'Which signal for this situation?',
  'A red parachute flare', ['Orange smoke', 'A white hand flare', 'A green flare'], 'Parachute flares are seen from far away at night; hand flares when help is close.', 'Distress signals',
  dict(type='card', title='Night, 10 miles offshore', lines=['Radio dead, lights of a ship on the horizon', 'Taking water, pumps barely coping', 'Flares: 2 parachute, 2 hand, 1 smoke'], tag='02:30'))
q('emergency', 2, 'Smoke is coming from the engine compartment hatch. What do you do?',
  'Stop the engine, do not open the hatch, discharge an extinguisher through the fire port', ['Open the hatch wide to see', 'Pour sea water in', 'Abandon ship at once'], 'Opening the hatch feeds the fire with air.', 'Fire')
q('emergency', 2, 'Water is rising fast in the bilge. First action?',
  'Find and stop the inflow — seacocks, hoses, stern gland — while pumping', ['Send a Mayday and wait', 'Head for deep water', 'Launch the liferaft'], 'Pumps only buy time: find the inflow and stop it. Taste the water — fresh = tank, salt = hull or fitting; bungs ready.', 'Flooding')
q('emergency', 2, 'Which call for this?',
  'PAN-PAN — urgent, not yet life-threatening', ['MAYDAY', 'SÉCURITÉ', 'No call needed'], 'Engine failure drifting slowly with time in hand: urgency, not distress.', 'Urgency procedure',
  dict(type='card', title='Engine failure', lines=['No wind, drifting at 0.5 kn towards rocks 3 miles off', 'Anchor ready, 60 m depth — too deep', 'Crew well, boat sound'], tag='PAN-PAN?'))
q('emergency', 3, 'You are coming back to the man overboard under power. How do you make the final approach?',
  'Slowly, heading into the wind; neutral as they come alongside near the bow', ['Downwind, engine ahead to hold position', 'Stern-first, so they can reach the ladder', 'Fast, then a burst astern beside them'], 'Into the wind you stop easily; a turning prop next to a swimmer is lethal.', 'Man overboard',
  E(you=dict(hdg=0), other=dict(bearing=-20, dist=60, hdg=0, scale=.3, label='MOB'), wind=0, note='Final approach under power, wind from ahead'))
q('emergency', 2, 'The yacht has an EPIRB in the cockpit locker. When do you use it?',
  'In a real emergency when the vessel or crew are in grave danger — it alerts rescue services by satellite', ['To test the batteries each morning', 'To call the marina', 'When the VHF is busy'], 'Cospas-Sarsat alerts rescue worldwide; false alerts cost real rescues.', 'Distress signals')

# ---------------- build ----------------
TOPICS = [('terms', 'Nautical terms & parts of the boat'), ('ropework', 'Ropework & knots'), ('safety', 'Safety equipment & procedures'),
          ('colregs', 'Rules of the road (COLREGs)'), ('navigation', 'Charts, compass & position'), ('buoyage', 'Buoyage & lights'),
          ('weather', 'Weather'), ('anchoring', 'Anchoring & mooring'), ('systems', 'Engine, electrics & boat systems'), ('emergency', 'VHF, distress & emergencies')]
assert len(Q) == 100, len(Q)
# Questions 101+ live in data/bank/<topic>.json (same fields as q()), appended in topic order so ids 1–100 never move.
# Check a file with: python3 data/check_topic.py <topic>
BANK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bank')
for t, _ in TOPICS:
    p = os.path.join(BANK, f'{t}.json')
    if os.path.exists(p):
        for x in json.load(open(p)): q(x['topic'], x['difficulty'], x['q'], x['a'], x['o'], x['why'], x['ref'], x['fig'])
assert len(Q) == 1000, len(Q)
# the Blender photos of the figures and the plans that go with the answers (docs/design/blender/publish_q.py), by question text
PH = os.path.join(BANK, 'photos.json')
PHOTOS = json.load(open(PH)) if os.path.exists(PH) else {}
rnd = random.Random(2026)
out = []
for i, x in enumerate(Q):
    wrong = x['o'][:]; rnd.shuffle(wrong); target = i % 4
    opts = wrong[:]; opts.insert(target, x['a'])
    out.append(dict(id=f'bs-{i + 1:03d}', topic=x['topic'], difficulty=x['difficulty'], q=x['q'], figure=x['fig'], options=opts, answer=target, why=x['why'], ref=x['ref'], **PHOTOS.get(x['q'], {})))
bank = dict(level='bareboat-skipper', title='IYT Bareboat Skipper', lang='en', passMark=70, examQuestions=40, examMinutes=60, version='2026-11-02d',
            note='Scenario questions written for study, close to the IYT Bareboat Skipper theory syllabus. Not official IYT exam content. '
                 'figure is a spec for docs/design/figures.js (null = text question). Pass mark, exam size and time are app defaults to verify.',
            topics=[dict(id=t, title=n, count=sum(1 for x in Q if x['topic'] == t)) for t, n in TOPICS], questions=out)
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions', 'bareboat-skipper.json')
json.dump(bank, open(path, 'w'), ensure_ascii=False, indent=2)
print(len(out), 'questions,', sum(1 for x in out if x['figure']), 'with figures, answers by position:', [sum(1 for x in out if x['answer'] == k) for k in range(4)])
