# The schematics (plan views) for the Racing Rules race figures of penalties, propulsion, protests, rightofway and
# starting: each FIG.race spec turned into the spec of docs/design/figure-schematic.js, geometry exactly as the
# figure (its units to metres at the scale of art_rr_b_kit: a 26.4-unit hull is the 14.6 m yacht), boats at true
# size with their heading, the boom drawn to leeward so the tack reads, marks with the zone, the line between the
# committee boat and the pin, tracks; plus the words of each figure. Writes
# figure-style/articles/racing-rules/<article>/<n>-plan.json. System Python.
#   python3 docs/design/blender/art_rr_b_plans.py [article ...]
import os, sys, json, math

HERE = os.path.dirname(os.path.abspath(__file__)); DESIGN = os.path.join(HERE, '..')
S = 14.6 / 26.4; L = 14.6
FILL = {'Grey': '#80878e', 'Blue': '#1f5fb8', 'Red': '#b01c1c', 'Yellow': '#d9a800', 'Green': '#1d7a3e', 'A': '#26303b',
        'starboard': '#1f5fb8', 'port': '#b01c1c', 'windward': '#1f5fb8', 'leeward': '#b01c1c', 'tacking': '#1f5fb8'}

def P(x, y): return [round((x - 160) * S, 1), round((y - 100) * S, 1)]
def fwd(h): return (math.sin(math.radians(h)), -math.cos(math.radians(h)))        # plan: x east, z south
def right(h): return (math.cos(math.radians(h)), math.sin(math.radians(h)))

def svg_path(d, step=1.5):
    toks = d.replace(',', ' ').replace('M', ' M ').replace('L', ' L ').replace('C', ' C ').split()
    pts, i, cmd, cur = [], 0, None, None
    while i < len(toks):
        if toks[i] in 'MLC': cmd = toks[i]; i += 1; continue
        if cmd == 'M': cur = (float(toks[i]), float(toks[i + 1])); pts.append(cur); i += 2; cmd = 'L'
        elif cmd == 'L': cur = (float(toks[i]), float(toks[i + 1])); pts.append(cur); i += 2
        elif cmd == 'C':
            c1 = (float(toks[i]), float(toks[i + 1])); c2 = (float(toks[i + 2]), float(toks[i + 3])); e = (float(toks[i + 4]), float(toks[i + 5])); i += 6
            for t in range(1, 17):
                t /= 16; a = (1 - t) ** 3; b = 3 * (1 - t) ** 2 * t; c = 3 * (1 - t) * t * t; dd = t ** 3
                pts.append((a * cur[0] + b * c1[0] + c * c2[0] + dd * e[0], a * cur[1] + b * c1[1] + c * c2[1] + dd * e[1]))
            cur = e
    return pts

def boom(x, z, hdg, wind=0, side=None, ang=None):
    """The boom, from the mast aft to leeward (the side FIG.race puts the sail): at least 30° out so it shows."""
    rel = (hdg - wind) % 360; s = side if side is not None else (1 if rel < 180 else -1)
    off = abs(((wind - hdg + 540) % 360) - 180)
    a = ang if ang is not None else (8 if off < 30 else 36 if off < 60 else 45 if off < 100 else 58 if off < 140 else 78)
    f, r = fwd(hdg), right(hdg); mx, mz = x + f[0] * 0.19 * L, z + f[1] * 0.19 * L; bl = 0.52 * L
    ex = mx - f[0] * math.cos(math.radians(a)) * bl + r[0] * s * math.sin(math.radians(a)) * bl
    ez = mz - f[1] * math.cos(math.radians(a)) * bl + r[1] * s * math.sin(math.radians(a)) * bl
    return {'pts': [[round(mx, 1), round(mz, 1)], [round(ex, 1), round(ez, 1)]], 'c': 'ink', 'w': 7}

def t(x, y, text, kind='light', **o): return {'x': P(x, y)[0], 'z': P(x, y)[1], 'text': text, 'kind': kind, **o}

def plan(f, c):
    """FIG.race spec f + the figure's words c -> {sch}."""
    wind = f.get('wind', 0) or 0
    boats, paths, circles, texts, zones, land = [], [], [], list(c.get('texts', [])), list(c.get('zones', [])), []
    for i, b in enumerate(f.get('boats', [])):
        key = b.get('label') if b.get('label') in c.get('boats', {}) else i
        bc = c.get('boats', {}).get(key, {})
        x, z = P(b['x'] + bc.get('nudge', (0, 0))[0], b['y'] + bc.get('nudge', (0, 0))[1])
        o = {'x': x, 'z': z, 'hdg': b['hdg'], 'L': L, 'bearing': False, 'label': bc.get('label', b.get('label') or ''), **bc.get('o', {})}
        if b.get('you'): o['you'] = True
        else: o['fill'] = FILL.get(b.get('label'), '#4a5563') if 'fill' not in bc else bc['fill']
        if not o['label']: o.pop('label')
        boats.append(o)
        if bc.get('boom', True) is not False: paths.append(boom(x, z, b['hdg'], wind, *(bc.get('boom') or (None, None))))
    if f.get('line'):
        l = f['line']; lc = c.get('line', {})
        a, b2 = P(l['x1'], l['y1']), P(l['x2'], l['y2'])
        paths.append({'pts': [a, b2], 'c': 'ink', 'w': 4, 'dash': '14 12'})
        if lc.get('cb', True): boats.append({'x': b2[0], 'z': b2[1] + 0.0, 'hdg': 0, 'L': 14.0, 'label': lc.get('cb_label', 'Committee boat'), 'fill': '#c9ced3', 'noHeading': True, 'bearing': False, **lc.get('cb_o', {})})
        circles.append({'x': a[0], 'z': a[1], 'r': 1.6, 'fill': '#ff7a00', 'c': 'ink', 'dash': '0'})
        texts.append({'x': a[0], 'z': a[1] + 9, 'text': lc.get('pin', 'pin'), 'pill': False, 'size': 22})
        if lc.get('text', l.get('label')):
            tt = lc.get('at', 0.5); texts.append({'x': round(a[0] + (b2[0] - a[0]) * tt, 1), 'z': round(a[1] + (b2[1] - a[1]) * tt - 8, 1), 'text': lc.get('text', l.get('label')), 'pill': False, 'size': 24})
    if f.get('mark'):
        m = f['mark']; x, z = P(m['x'], m['y']); mc = c.get('mark', {})
        if m.get('zone'):
            R = (m['zone'] * S) if not isinstance(m['zone'], bool) else 3 * L
            circles.append({'x': x, 'z': z, 'r': round(R, 1), 'fill': 'rgba(0,118,190,.06)', 'c': 'course', 'dash': '16 12'})
            texts.append({'x': x, 'z': round(z - R + 6, 1), 'text': c.get('zone_text', 'zone: 3 lengths'), 'kind': 'accent', 'size': 22})
        circles.append({'x': x, 'z': z, 'r': 2.4, 'fill': '#ffa800', 'c': 'ink', 'dash': '0'})
        if mc.get('text', m.get('label')): texts.append({'x': x, 'z': round(z + mc.get('dz', 9), 1), 'text': mc.get('text', m.get('label')), 'pill': False, 'size': 24})
    if f.get('track') and c.get('track', True):
        tp = [P(*p) for p in svg_path(f['track'])]
        paths.append({'pts': tp, 'c': 'course', 'w': 5, 'dash': '12 10', 'arrow': True})
    if f.get('obstruction') and c.get('land'): land += c['land']
    paths += c.get('paths', []); circles += c.get('circles', [])
    sch = {'padPx': c.get('padPx', 80), 'trueScale': True, 'title': c['title'], 'key': c['key'], 'boats': boats, 'paths': paths, 'circles': circles, 'texts': texts}
    if c.get('wind', True): sch['wind'] = wind
    if zones: sch['zones'] = zones
    if land: sch['land'] = land
    if c.get('fit'): sch['fit'] = c['fit']
    if c.get('fitu'): sch['fit'] = [{'x': P(*q)[0], 'z': P(*q)[1]} for q in c['fitu']]
    return {'sch': sch}

def pt(x, y): return P(x, y)

# ---------------------------------------------------------------- the words, per figure
def fan(cx, cy, r_units, a0, a1, n=24):
    c = P(cx, cy); return [c] + [[round(c[0] + math.sin(math.radians(a0 + (a1 - a0) * k / n)) * r_units, 1), round(c[1] - math.cos(math.radians(a0 + (a1 - a0) * k / n)) * r_units, 1)] for k in range(n + 1)]

SPEC = {
 'penalties': {
  1: dict(title='Two-Turns Penalty · port and starboard', key=['You, on port tack, failed to keep clear of Grey on starboard', 'A Part 2 rule broken: two turns, promptly, protest or no protest'],
          boats={'You': dict(label='You: port'), 'Grey': dict(label='Grey: starboard')}),
  2: dict(title='One-Turn Penalty · touching a mark', key=['You touched the mark (rule 31)', 'One turn; a Part 2 breach in the same incident makes it two'],
          boats={'You': dict(label='You')}, mark=dict(text='Mark')),
  3: dict(title='Taking the turns · one turn on a run', key=['Gybe, luff, tack, bear away: a tack and a gybe in each turn', 'Both turns the same way, well clear of other boats'],
          boats={'You': dict(label='You')}, texts=[t(205, 128, 'gybe'), t(222, 92, 'luff'), t(175, 52, 'tack'), t(128, 86, 'bear away')]),
  4: dict(title='Turns at the finish', key=['Turns done beyond the line do not finish you', 'Come back until the hull is on the course side, then cross the line again'],
          boats={'You': dict(label='You')}, line=dict(text='Finish line', at=0.2), texts=[t(110, 150, 'course side', 'accent')], fitu=[(60, 25), (250, 160)]),
  5: dict(title='Retiring · serious damage', key=["Your bow made a hole in Grey's side", 'Injury, serious damage or a significant advantage: retire, turns do not count'],
          boats={'You': dict(label='You', nudge=(1.9, -1.9)), 'Grey': dict(label='Grey')}, texts=[t(188, 140, 'serious damage', 'red')]),
  6: dict(title='Exoneration · compelled', key=['Blue, to windward, did not keep clear and pushed you onto the mark', 'Compelled by her breach: you are exonerated, no penalty'],
          boats={'You': dict(label='You'), 'Blue': dict(label='Blue')}, mark=dict(text='Mark', dz=12), texts=[t(205, 140, 'pushes you', 'red')]),
  7: dict(title='Exoneration · within mark-room', key=['Yellow owed you mark-room and left too little', 'Sailing within it, you broke a rule against her: exonerated'],
          boats={'You': dict(label='You'), 'Yellow': dict(label='Yellow')}, mark=dict(text='Mark', dz=-9), texts=[t(220, 150, 'too little room', 'red')]),
 },
 'propulsion': {
  1: dict(title='Rule 42.1 · backing the mainsail', key=['Pushing the boom out uses the wind: legal, and it moves you astern', 'Moving astern through the water you keep clear of Grey (rule 21)'],
          boats={'You': dict(label='You', boom=(1, 62)), 'Grey': dict(label='Grey')}, line=dict(text='Start line', at=0.2), texts=[t(140, 125, 'astern', 'accent')],
          paths=[{'pts': [pt(140, 108), pt(140, 124)], 'c': 'course', 'w': 6, 'arrow': True}], fitu=[(30, 30), (275, 165)]),
  2: dict(title='Rule 42.2 · repeated gybes', key=['Steady wind and nobody near: gybe after gybe only propels the boat', 'Gybing on the shifts is tactics; in rhythm down an empty run it is not'],
          boats={'You': dict(label='You')}),
  3: dict(title='Rule 42.3 · sculling to bear away', key=['Stopped within 45° of the wind: you may scull to bear away', 'To the edge of the shaded sector, no further'],
          wind=True, zones=[{'pts': fan(160, 100, 34, -45, 45), 'c': 'red', 'fill': 'rgba(224,37,27,.10)'}], texts=[t(160, 52, 'within 45° of the wind', 'red'), t(222, 66, 'scull to here', 'accent')]),
  4: dict(title='Rule 42.3 · aground', key=['Aground: the crew may push her off by hand', 'Not a tow under engine, nor any help from outside'],
          boats={'You': dict(label='You')}, land=[[pt(0, 120), pt(320, 120), pt(320, 175), pt(0, 175)]], texts=[t(200, 150, 'sandbank', pill=False, size=28), t(150, 92, 'crew pushes by hand', 'accent')]),
  6: dict(title='Rule 45 · anchoring', key=['No wind, a foul tide: you may anchor and hold your place', 'The anchor comes back aboard before you sail on'],
          boats={'You': dict(label='You: at anchor', boom=(-1, 8)), 'Blue': dict(label='Blue', boom=(-1, 8)), 'Red': dict(label='Red', boom=(1, 8))}, mark=dict(text='Windward mark'), wind=False,
          paths=[{'pts': [pt(108, 60), pt(108, 100)], 'c': 'red', 'w': 8, 'arrow': True}, {'pts': [pt(85, 148), pt(85, 162)], 'c': 'red', 'w': 5, 'arrow': True}, {'pts': [pt(232, 152), pt(232, 166)], 'c': 'red', 'w': 5, 'arrow': True}],
          texts=[t(108, 52, 'tide', 'red')]),
 },
 'protests': {
  1: dict(title='Protesting · hail and flag', key=['Blue, on port, did not keep clear of you on starboard', 'Hail "Protest" at once; over 6 m, a red flag too, kept up until you finish'],
          boats={'You': dict(label='You'), 'Blue': dict(label='Blue')}, texts=[t(90, 160, '"Protest!" + red flag', 'red')]),
  5: dict(title='The hearing · who is a party', key=['Green forced Red onto you: you protest Red', 'Green is not a party: the committee must protest her to penalise her'],
          boats={'You': dict(label='You'), 'Red': dict(label='Red'), 'Green': dict(label='Green')}, mark=dict(text='Leeward mark'), zone_text='zone', fitu=[(60, 20), (250, 190)]),
  6: dict(title='Decisions · the protestor penalised', key=['You luffed and gave Blue no room to keep clear: rule 16.1', 'Blue is not penalised; you are, though you protested'],
          boats={'You': dict(label='You: luffing'), 'Blue': dict(label='Blue')}, texts=[t(95, 95, '16.1: no room', 'red')]),
  7: dict(title='Redress · a wrong OCS', key=['The committee boat dragged her anchor and the line moved', 'Scored OCS by the moved line, through no fault of yours: ask for redress'],
          boats={'You': dict(label='You')}, line=dict(text='line as laid', at=0.3, cb_o={'x': round((300 - 160) * S, 1), 'z': round((146 - 100) * S, 1)}, cb_label='Committee boat'), track=False,
          paths=[{'pts': [pt(40, 112), pt(300, 146)], 'c': 'red', 'w': 5, 'dash': '14 12'}, {'pts': [pt(280, 112), pt(298, 138)], 'c': 'course', 'w': 5, 'dash': '8 8', 'arrow': True}],
          texts=[t(110, 140, 'line after she dragged', 'red'), t(250, 98, 'anchored here')]),
 },
 'rightofway': {
  1: dict(title='Rule 10 on a beat', key=['Port tack keeps clear of starboard tack', 'Cross ahead if you safely can, bear away astern of her, or tack'],
          boats={'port': dict(label='port tack'), 'starboard': dict(label='starboard tack')}, texts=[t(105, 100, 'keeps clear', 'red')]),
  2: dict(title='Rule 10 on a run', key=['Read the tack from the boom: boom to starboard is port tack', 'The port-tack boat keeps clear'],
          boats={0: dict(label='port tack'), 1: dict(label='starboard tack', fill='#1f5fb8')}, texts=[t(90, 128, 'keeps clear', 'red')], fitu=[(60, 60), (260, 140)]),
  3: dict(title='Rule 11 · same tack, overlapped', key=['The windward boat keeps clear of the leeward boat', 'With her hull, boom and sails, and a margin for gusts'],
          boats={'windward': dict(label='windward'), 'leeward': dict(label='leeward')}, texts=[t(238, 120, 'keeps clear', 'red')]),
  4: dict(title='Rule 11 · barging at the start', key=['No mark-room at a starting mark as boats approach to start', 'The windward boat squeezing in has no rights: she keeps clear'],
          boats={0: dict(label='leeward', fill='#b01c1c', o={'hdgDx': -40}), 'windward': dict(label='windward', o={'hdgDx': 30})}, line=dict(text='Start line', at=0.3),
          texts=[t(268, 160, 'no room', 'red')], fitu=[(20, 50), (300, 185)]),
  5: dict(title='Rule 12 · passing to windward', key=['Clear astern you keep clear (rule 12); overlapped to windward you still do (rule 11)', 'So you keep clear all the way past'],
          boats={0: dict(label='ahead'), 'You': dict(label='You')}, texts=[t(285, 112, 'keep clear', 'red')], fitu=[(150, 70), (295, 145)]),
  6: dict(title='Rule 12 · passing to leeward', key=['Clear astern you keep clear (rule 12)', 'Overlapped to leeward you have right of way (rule 11), after giving her room (rule 15)'],
          boats={0: dict(label='ahead'), 'You': dict(label='You')}),
  7: dict(title='Rule 13 · while tacking', key=['Past head to wind and not yet close-hauled: she keeps clear of everyone', 'Rules 10, 11 and 12 do not apply until she is close-hauled'],
          boats={'starboard': dict(label='starboard'), 'tacking': dict(label='tacking')}, texts=[t(105, 95, 'keeps clear', 'red')], fitu=[(110, 55), (250, 165)]),
 },
 'starting': {
  3: dict(title='Flags Z, U, black · the triangle', key=['The triangle joins the ends of the line and the first mark', 'In it during the last minute: Z costs 20 %, U and black disqualify'],
          boats={'You': dict(label='You')}, mark=dict(text='First mark', dz=-9), track=False,
          zones=[{'pts': [pt(40, 135), pt(160, 40), pt(280, 135)], 'c': 'red', 'fill': 'rgba(224,37,27,.10)'}], texts=[t(120, 112, 'the triangle', 'red')], line=dict(text='', at=0.5)),
  4: dict(title='Starting correctly · over at the gun', key=['Any part of the hull over at the signal: you have not started', 'Bring the whole hull back to the pre-start side, then cross again'],
          boats={'You': dict(label='You')}, texts=[t(205, 80, 'over at the gun', 'red'), t(100, 150, 'pre-start side', 'accent')], line=dict(text='Start line', at=0.85)),
  7: dict(title='Before the gun · right of way on the line', key=['A reaches in to windward: no mark-room at a starting mark', 'You, to leeward, may hold your course; she keeps clear'],
          boats={'You': dict(label='You'), 'A': dict(label='A')}, line=dict(text='Start line', at=0.3), texts=[t(270, 150, 'no room', 'red')], fitu=[(30, 5), (275, 175)]),
 },
}

if __name__ == '__main__':
    arts = sys.argv[1:] or list(SPEC)
    for a in arts:
        data = {f['n']: f for f in json.load(open(os.path.join(DESIGN, 'article-figs', f'racing-rules-{a}.json')))['figs']}
        out = os.path.join(DESIGN, 'figure-style', 'articles', 'racing-rules', a)
        for n, c in SPEC[a].items():
            f = data[n]['fig']
            if f['type'] == 'sail':   # no race: one boat in the middle
                f = {'type': 'race', 'wind': f.get('wind', 0), 'boats': [{'x': 160, 'y': 100, 'hdg': f['hdg'], 'label': 'You', 'you': True}]}
                c = {**c, 'boats': {'You': dict(label='You', boom=(1, 8))}}
            os.makedirs(out, exist_ok=True)
            json.dump(plan(f, c), open(os.path.join(out, f'{n}-plan.json'), 'w'), ensure_ascii=False)
            print('wrote', a, n)
