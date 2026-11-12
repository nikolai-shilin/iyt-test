# Racing Rules articles course, definitions, limits, marks and obstructions: the situations for the Blender renders
# (art_rr_<article>.py through art_rr_a_kit.py) and for the plan views (art_rr_a_plans.py), from one description so the
# two agree. Plain Python (no bpy): the geometry comes from docs/design/article-figs/racing-rules-<a>.json, the race
# figures of figures.js (320 x 200 units, y down, north up, wind from the north), and this file adds what the renders
# and plans say about each figure: labels, notes, keys, and a few props the text needs (the other gate mark, a tack).
# Scale: a boat is 26.4 units long in FIG.race (44 x 0.6), and the Sun Odyssey is 14.9 m, so 1 unit = 0.565 m; the
# zone is three of those lengths (79.2 units, 44.7 m). A boat's (x, y) is the origin of the figure's hull symbol, 55 %
# of her length back from the bow.
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.join(HERE, '..')
LEN_U = 44 * 0.6            # a hull length in figure units
LEN_M = 14.9                # the Sun Odyssey 49DS overall
KM = LEN_M / LEN_U          # metres per figure unit
ZONE_U = 3 * LEN_U
BOW_U = 22 * 0.6            # figure origin to bow (units); stern is 18 x 0.6 behind it
STERN_U = 18 * 0.6
ARTICLES = ('course', 'definitions', 'limits', 'marks', 'obstructions')

def figs(article):
    with open(os.path.join(DESIGN, 'article-figs', f'racing-rules-{article}.json')) as f: return {d['n']: d for d in json.load(f)['figs']}

def world(x, y):
    """Figure units to Blender metres: x east, y north, the figure's centre (160, 100) at the origin."""
    return ((x - 160) * KM, -(y - 100) * KM)

def tack(hdg, wind=0):
    """'starboard' or 'port', from the side the wind comes over (a run: opposite the boom, as the figure draws it)."""
    rel = ((wind - hdg) % 360 + 360) % 360
    return 'starboard' if 0 < rel < 180 else 'port'

def off_wind(hdg, wind=0):
    return abs(((wind - hdg + 540) % 360) - 180)

def boom_angle(hdg, wind=0):
    """Degrees off the centreline for the point of sail (close-hauled 10, reach 32, broad 55, run 78)."""
    o = off_wind(hdg, wind)
    return 4 if o < 40 else 10 if o < 58 else 18 if o < 75 else 32 if o < 110 else 55 if o < 150 else 78

def near_on(q, px, py):
    """The point of polygon q's outline (figure units) nearest (px, py)."""
    best, bd = None, 1e18
    for (ax, ay), (bx, by) in zip(q, q[1:] + q[:1]):
        dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy or 1
        t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L)); cx, cy = ax + t * dx, ay + t * dy
        d = (cx - px) ** 2 + (cy - py) ** 2
        if d < bd: best, bd = (cx, cy), d
    return best

def path_points(d, step=2.0):
    """An SVG path of M, L and Q commands (as the figures use) as a polyline in figure units."""
    import re
    tok = re.findall(r'[MLQ]|-?[\d.]+', d); pts, i, cur = [], 0, None
    while i < len(tok):
        c = tok[i]; i += 1
        if c == 'M' or c == 'L':
            p = (float(tok[i]), float(tok[i + 1])); i += 2
            if c == 'L' and cur:
                n = max(1, int(math.dist(cur, p) / step))
                pts += [(cur[0] + (p[0] - cur[0]) * k / n, cur[1] + (p[1] - cur[1]) * k / n) for k in range(1, n + 1)]
            else: pts.append(p)
            cur = p
        elif c == 'Q':
            q = (float(tok[i]), float(tok[i + 1])); p = (float(tok[i + 2]), float(tok[i + 3])); i += 4
            n = max(2, int((math.dist(cur, q) + math.dist(q, p)) / step))
            for k in range(1, n + 1):
                t = k / n; pts.append(((1 - t) ** 2 * cur[0] + 2 * (1 - t) * t * q[0] + t * t * p[0], (1 - t) ** 2 * cur[1] + 2 * (1 - t) * t * q[1] + t * t * p[1]))
            cur = p
    return pts

# ---------------------------------------------------------------------------------------------------------------
# Per figure. names: the boats' labels in the render (and plan: plan_names when they differ), in the order of the
# figure's boats; colour 'blue' for you, 'red' for the boat in the wrong. mark / line / obstruction labels; extra
# points (x, y, text, colour) in figure units; note; the plan's title and key. Props: gate (the other gate mark),
# paths (extra courses: (svg path, colour, arrow?)), rc_flags (flags on the committee boat), kind of obstruction.
# ---------------------------------------------------------------------------------------------------------------
B, R, W = 'blue', 'red', None
EXTRA = {
'course': {
  1: dict(names=[('You', B)], mark='Right-hand gate mark', gate=(110, 100, 'Left-hand gate mark'), plan_textpos={'Left-hand gate mark': (0, 54)}, pts_plan={'your track: outside the gate': 'your track'}, plan_at={'your track: outside the gate': (130, 40)},
          pts=[(262, 70, 'your track: outside the gate', R)],
          title='Rule 28 · the string test at a gate'),
  2: dict(names=[('You', B)], mark='Windward mark: leave it to port', pts=[(222, 66, 'left to starboard', R)], plan_textpos={'Windward mark': (-210, 0)}, mark_plan='Windward mark',
          title='Rule 28.2 · unwind the error'),
  3: dict(names=[('You', B)], mark='Windward mark', pts=[(166, 96, 'hull, crew or gear on it: a touch', R)], pts_plan={'hull, crew or gear on it: a touch': 'a touch'}, plan_at={'hull, crew or gear on it: a touch': (215, 88)},
          title='Rule 31 · touching a mark'),
  4: dict(names=[('You', B)], line='Finishing line', rc='Committee boat · blue flag', rc_flags=['blue'], pts=[(160, 86, 'bow across: finished', B)],
          title='Finishing'),
  5: dict(flags=True, title=None),
  6: dict(names=[('You', B)], mark='Mark 3', line='New finishing line', line_dy=70, rc='Committee boat · flag S', rc_flags=['S'],
          title='Course shortened at mark 3'),
  7: dict(flags=True, title=None),
  8: dict(names=[('You', B)], rib='RIB with flag M: now the mark', el=40.0,
          title='A missing mark replaced'),
},
'definitions': {
  1: dict(names=[('starboard tack', W), ('starboard tack: boom to port', W), ('port tack', W)], plan_names=['starboard', 'starboard', 'port'],
          title='Tack: named after the windward side'),
  2: dict(names=[('A', W), ('B: clear astern', W), ('C: overlaps A', B)], plan_names=['A', 'B', 'C'], line_abeam="line abeam from A's stern", track_fit=False,
          title='Clear astern and overlap'),
  3: dict(names=[('port: not keeping clear', R), ('starboard: has to luff', W)], plan_names=['port', 'starboard'],
          paths=[('M225 130 Q217 116 223 102', B, True)], note='Not keeping clear · starboard has to luff',
          title='Keep clear: port fails'),
  4: dict(names=[('windward: not keeping clear', R), ('leeward: cannot luff without contact', W)], plan_names=['windward', 'leeward'],
          note='Not keeping clear · leeward cannot luff without contact', el=64.0, fill=(0.6, 0.45),
          title='Keep clear: overlapped'),
  5: dict(names=[('in the zone', B), ('outside', W)], mark='Windward mark', zone_label='zone: 3 hull lengths',
          title='The zone'),
  6: dict(names=[('You', B)], obstruction='Moored yacht: an obstruction', kind='moored', pts=[(128, 116, 'one length away, straight at it', W)], plan_textpos={'one length away, straight at it': (-250, 30)}, pts_plan={'one length away, straight at it': 'one length away'},
          note='Obstruction · one length away, straight at it',
          title='Obstruction'),
  7: dict(names=[(None, W), (None, W)], obstruction='Shore: a continuing obstruction', kind='shore', dim=((70, 40), (70, 40 + 3 * LEN_U), '3 lengths'),
          note='Continuing obstruction · three lengths or more along it',
          title='Continuing obstruction'),
  8: dict(names=[('A: over: must come back', R), ('B: may start', B)], plan_names=['A', 'B'], line='Start line', rc='Committee boat · flag X', rc_flags=['X'],
          title='Starting'),
},
'limits': {
  1: dict(names=[('port: not keeping clear', R), ('starboard: must act too', W)], plan_names=['port', 'starboard'],
          title='Rule 14 · avoid contact'),
  2: dict(names=[('she needs room to keep clear', W), ('You: just tacked onto starboard', B)], plan_names=[None, 'You'], paths=[('M176 154 L197 133 Q212 120 205 112', B, False)],
          note='Your tack: rule 15 · she needs room to keep clear',
          title='Rule 15 · you tacked'),
  3: dict(names=[('You: right of way, no rule 15', B), ('she tacked: keeps clear at once', R)], plan_names=['You', None], paths=[('M222 72 L204 90 Q190 104 195 100', R, False)],
          note='Her tack: no rule 15 · she keeps clear at once',
          title='Rule 15 · she tacked'),
  4: dict(names=[('windward: room to respond', W), ('You: luffing slowly', B)], plan_names=[None, 'You'], paths=[('M147 118 Q139 104 145 93', B, True)],
          title='Rule 16.1 · changing course'),
  5: dict(names=[('starboard: bears away', R), ('port: ducking astern', W)], plan_names=['starboard', 'port'], paths=[('M118 132 Q170 124 206 116', W, True)], plan_pos={0: 'above'},
          title='Rule 16.2 · on a beat'),
  6: dict(names=[('windward', W), ('You: overlapped from clear astern', B)], plan_names=['windward', 'You'], dim=((190, 130), (190, 130 - 2 * LEN_U), '2 lengths'),
          title='Rule 17 · proper course'),
},
'marks': {
  1: dict(names=[('You: bow in the zone', B), ('A', W)], mark='Mark',
          title='Rule 18 · the zone'),
  2: dict(names=[('You: port, keep clear', B), ('A: starboard', W)], plan_names=['You', 'A'], mark='Windward mark', note='Beat, opposite tacks · port keeps clear',
          title='Rule 18 off · opposite tacks on a beat'),
  3: dict(names=[('You: windward, keep clear', B), ('A: leeward', W)], plan_names=['You', 'A'], line='Start line', rc='Committee boat: a starting mark', rc_flags=['orange'], wind_uv=(0.62, 0.86),
          note='Approaching to start · windward keeps clear',
          title='Rule 18 off · approaching to start'),
  4: dict(names=[('outside: gives room', W), ('inside: gets mark-room', B)], plan_names=['outside', 'inside'], mark='Leeward mark', note='Overlapped at the zone · outside gives room',
          title='Rule 18.2 · overlapped at the zone'),
  5: dict(names=[('astern: gives room', W), ('clear ahead: gets mark-room', B)], plan_names=['astern', 'ahead'], mark='Leeward mark', note='Clear ahead at the zone · astern gives room',
          title='Rule 18.2 · clear ahead at the zone'),
  6: dict(names=[('A: leeward', W), ('You: inside, windward', B)], plan_names=['A', 'You'], mark='Leeward mark', pts=[(70, 150, 'wide loop: not mark-room', R)],
          title='Mark-room is not right of way'),
  7: dict(names=[('You: on starboard, fetching', B), ('A: tacks in the zone', R)], plan_names=['You', 'A'], mark='Windward mark', paths=[('M185 118 Q197 104 189 95', R, True)],
          title='Rule 18.3 · tacking in the zone'),
  8: dict(names=[('A', W), ('You: starboard, inside', B)], plan_names=['A', 'You'], mark='Leeward mark', paths=[('M140 48 L145 98 Q151 118 168 113', B, True)],
          pts=[(95, 165, 'too far before the gybe', R), (225, 100, 'proper course', B)],
          title='Rule 18.4 · gybing at the mark'),
},
'obstructions': {
  1: dict(names=[('You: port', B), ('A: port', W), ('B: starboard: an obstruction', R)], plan_names=['You', 'A', 'B'],
          title='A right-of-way boat as an obstruction'),
  2: dict(names=[('inside: room at the pier', B), ('outside: gives room', W)], plan_names=['inside', 'outside'], obstruction='Pier', kind='pier', plan_textpos={'Pier': (0, -34)}, note='Overlapped at a pier · outside gives room',
          title='Rule 19.2(b) · passing an obstruction'),
  3: dict(names=[('A: squeezed in: keep clear', R), ('B: owes no room', W)], plan_names=['A', 'B'], obstruction='Sea wall', kind='wall',
          note='Along a sea wall · A squeezes in with no room: no rights',
          title='Rule 19.2(c) · a continuing obstruction'),
  4: dict(names=[("You: 'Room to tack!'", B), ("A: tacks, or answers 'You tack'", W)], plan_names=['You', 'A'], obstruction='Quay', kind='quay',
          title='Rule 20 · room to tack'),
  5: dict(names=[('You: returning: keep clear', B), ('A', W), ('B', W)], plan_names=['You', 'A', 'B'], line='Start line', rc='Committee boat · flag X', rc_flags=['X'],
          title='Rule 21 · returning to start'),
  6: dict(names=[('You', B), ('A: capsized', R)], capsized=1, plan_pos={1: 'left'}, el=40.0, fill=(0.8, 0.72),
          title='Rule 22 · a capsized boat'),
  7: dict(names=[('You: finished: not racing', B), ('A: still racing', W)], plan_names=['You', 'A'], line='Finishing line', rc='Committee boat · blue flag', rc_flags=['blue'],
          title='Rule 23 · finished, not racing'),
},
}

# the plan's key: two short lines each (each line is one string for ru.json, so it never wraps)
KEYS = {
  ('course', 1): ['Your track passed outside the gate', 'The string never passed between the marks'],
  ('course', 2): ['This mark was left to starboard', 'Unwind: sail back, then round it to port'],
  ('course', 3): ['Hull, crew or gear on the mark: a touch', 'Penalty: one turn, a tack and a gybe'],
  ('course', 4): ['Hull across from the course side: finished', 'Blue flag: committee boat on station'],
  ('course', 6): ['Flag S, two sounds: course shortened', 'Finish between mark 3 and the boat with S'],
  ('course', 8): ['Mark 2 is missing: flag M on the RIB', 'The RIB is the mark: round it instead'],
  ('definitions', 1): ['The tack is named after the windward side', 'Boom to port on a run: starboard tack'],
  ('definitions', 2): ["B is behind A's stern line: clear astern", 'C is not: C overlaps A, however far apart'],
  ('definitions', 3): ['Starboard must luff to avoid port', 'So port is not keeping clear'],
  ('definitions', 4): ['Leeward cannot luff without contact', 'So windward is not keeping clear'],
  ('definitions', 5): ['Three hull lengths of the nearer boat', 'In it once any part of the hull is'],
  ('definitions', 6): ['Straight at it from one length away', 'You cannot pass it without a big turn'],
  ('definitions', 7): ['Passed along for three lengths or more', 'A shore or wall; never a vessel under way'],
  ('definitions', 8): ['A is over at the signal: she must return', 'B starts when her hull crosses the line'],
  ('limits', 1): ['Port is not keeping clear', 'Starboard must act too: avoid contact'],
  ('limits', 2): ['Your own tack gave you right of way', 'At first, give her room to keep clear'],
  ('limits', 3): ['Her own tack put her to windward', 'She keeps clear at once: no rule 15'],
  ('limits', 4): ['You may luff, giving her room to respond', 'Slowly: she has time to keep clear'],
  ('limits', 5): ['Port ducks to pass astern of starboard', 'Starboard must not bear away at her'],
  ('limits', 6): ['You came from clear astern, to leeward', 'Within 2 lengths: not above proper course'],
  ('marks', 1): ['Your bow is in the zone', 'Rule 18 now applies to both boats'],
  ('marks', 2): ['Opposite tacks on a beat: no rule 18', 'Rule 10 alone: port keeps clear'],
  ('marks', 3): ['Approaching to start: no rule 18', 'No mark-room: windward keeps clear'],
  ('marks', 4): ['Overlapped as the first reaches the zone', 'Outside gives inside mark-room'],
  ('marks', 5): ['Clear ahead as she reaches the zone', 'Astern keeps clear and gives mark-room'],
  ('marks', 6): ['Inside but windward: mark-room only', 'The wide loop: you must keep clear of A'],
  ('marks', 7): ['A tacked in the zone, onto your tack', 'She must not make you luff to avoid her'],
  ('marks', 8): ['Inside with right of way, you must gybe', 'Gybe no farther from the mark than needed'],
  ('obstructions', 1): ['Both port-tack boats keep clear of B', 'To them she is an obstruction'],
  ('obstructions', 2): ['Overlapped: outside gives inside room', 'Room between her and the pier'],
  ('obstructions', 3): ['A overlapped inside from clear astern', 'No room at the wall: she must keep clear'],
  ('obstructions', 4): ['You hail "Room to tack" near the quay', 'A tacks, or answers "You tack"'],
  ('obstructions', 5): ['Returning to start: keep clear of all', 'Until your hull is behind the line'],
  ('obstructions', 6): ['Avoid a capsized boat if possible', 'Her tack does not matter'],
  ('obstructions', 7): ['Finished and clear: you are not racing', 'Do not interfere with boats racing'],
}

# the flag figures (course 5 and 7): staffs on the committee boat, each a hoist of one or two flags, top first
FLAG_FIGS = {
  ('course', 5): dict(hoists=[['S'], ['N'], ['N', 'H'], ['N', 'A']],
                      labels=['S · shortened', 'N · abandoned', 'H under N · see ashore', 'A under N · no more today'], note='S: two sounds · N: three sounds'),
  ('course', 7): dict(hoists=[['C'], ['M']], labels=['C · leg changed', 'M · missing mark'], note='Both with repeated sounds'),
}

def spec(article, n):
    """The figure (from article-figs) merged with its EXTRA: fig, boats, names, note, ..."""
    f = figs(article)[n]; e = dict(EXTRA[article][n]); fig = f['fig']
    e['fig'] = fig; e['boats'] = fig.get('boats', [])
    e['note'] = e.get('note') or fig.get('note') or ' · '.join(x for x in (f.get('name'), f.get('cap')) if x)
    e['key'] = KEYS.get((article, n), [])
    if 'names' not in e: e['names'] = [(b.get('label'), B if b.get('you') else W) for b in e['boats']]
    return e
