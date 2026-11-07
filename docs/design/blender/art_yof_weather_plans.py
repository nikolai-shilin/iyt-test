# The plans (schematics) of yachtmaster-offshore/weather, written as <n>-plan.json beside the renders: {sch}
# (figure-schematic.js) for the isobars, lows, fronts, sea room and islands; {svg} for the barograph and the swell and
# shelf profiles. Wind directions follow the rules: round a low anticlockwise and 20° inwards in the north (clockwise
# in the south), round a high clockwise and 20° outwards.
#   python3 docs/design/blender/art_yof_weather_plans.py
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import art_yof_pilotage_svg as S
from art_yof_pilotage_svg import txt, pill, arrow, line, boat, dim, frame, f1, COL, path_polys

DIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'weather')
S.load_ru(DIR)
RED, INK, MUT, ACC = COL['red'], 'var(--ink)', 'var(--muted)', 'var(--accent)'
def t(x, z, text, **o): return {'x': x, 'z': z, 'text': text, **o}
def at(c, brg, r): return [round(c[0] + r * math.sin(math.radians(brg)), 1), round(c[1] - r * math.cos(math.radians(brg)), 1)]

def flow(kind, b):
    """Bearing the air flows towards at bearing b from a centre: 'low' (north), 'high' (north), 'low-s' (south)."""
    return {'low': b - 110, 'high': b + 70, 'low-s': b + 110}[kind]

def flow_arrow(c, kind, b, r, L=150, w=7, col='red'):
    p = at(c, b, r); f = flow(kind, b)
    return {'pts': [at(p, f, -L / 2), at(p, f, L / 2)], 'c': col, 'w': w, 'arrow': True}

def rings(c, radii, values, centre, size=64):
    return ([{'x': c[0], 'z': c[1], 'r': r, 'c': 'ink', 'dash': '0'} for r in radii],
            [t(*at(c, 60, r), f'{v}', size=22) for r, v in zip(radii, values)] + [t(c[0], c[1] + 20, centre, pill=False, size=size)])

def p1():
    c = [0, 0]; ci, tx = rings(c, [110, 220, 330], [1032, 1028, 1024], 'H')
    you = at(c, 180, 275); f = flow('high', 180)
    return {'noScale': True, 'sch': {'padPx': 50, 'title': 'Round a high · northern hemisphere', 'key': ['Clockwise round a high, angled slightly outwards', 'South of the centre the wind blows from the ENE'],
        'circles': ci, 'boats': [{'you': True, 'x': you[0], 'z': you[1], 'hdg': 270, 'noHeading': True}],
        'paths': [flow_arrow(c, 'high', b, 380) for b in (0, 120, 270)] + [{'pts': [at(you, f + 180, 260), at(you, f + 180, 70)], 'c': 'red', 'w': 9, 'arrow': True}],
        'texts': tx + [t(*at(you, f + 180, 300), 'ENE', kind='red', size=28)], 'fit': [{'x': -420, 'z': -420}, {'x': 420, 'z': 420}]}}

def p2():
    c = [0, 0]; ci, tx = rings(c, [110, 220, 330], [992, 996, 1000], 'L')
    you = at(c, 0, 275); f = flow('low-s', 0)
    return {'noScale': True, 'sch': {'padPx': 50, 'title': 'Round a low · southern hemisphere', 'key': ['In the south the wind turns clockwise round a low, angled slightly inwards', 'North of the centre: WNW · back to the wind, the low is on your right'],
        'circles': ci, 'boats': [{'you': True, 'x': you[0], 'z': you[1], 'hdg': 0, 'noHeading': True, 'labelAbove': True}],
        'paths': [flow_arrow(c, 'low-s', b, 380) for b in (120, 180, 240)] + [{'pts': [at(you, f + 180, 260), at(you, f + 180, 70)], 'c': 'red', 'w': 9, 'arrow': True}],
        'texts': tx + [t(*at(you, f + 180, 300), 'WNW', kind='red', size=28), t(330, 390, 'Southern hemisphere', pill=False, size=26)],
        'fit': [{'x': -420, 'z': -480}, {'x': 420, 'z': 420}]}}

def p3():
    c = [-150, 150]; ci, tx = rings(c, [100, 200, 300], [988, 992, 996], 'L')
    r_, l_ = at(c, 135, 250), at(c, 315, 250)
    return {'noScale': True, 'sch': {'padPx': 50, 'title': 'A low moving NE · northern hemisphere', 'key': ['Face the way the low moves: on its right the wind veers, S to W to NW, and is stronger', 'On its left the wind backs, E to N to NW, and is lighter'],
        'circles': ci, 'boats': [{'plain': True, 'x': r_[0], 'z': r_[1], 'hdg': 25, 'scale': 1.8}, {'plain': True, 'x': l_[0], 'z': l_[1], 'hdg': 205, 'scale': 1.8}],
        'paths': [{'pts': [at(c, 45, 40), at(c, 45, 700)], 'c': 'ink', 'w': 5, 'dash': '14 10', 'arrow': True}, flow_arrow(c, 'low', 135, 250, 170, 9), flow_arrow(c, 'low', 315, 250, 170, 9),
                  flow_arrow(c, 'low', 225, 300), flow_arrow(c, 'low', 45, 300)],
        'texts': tx + [t(*at(c, 45, 760), 'track NE', pill=False, size=26), t(*at(r_, 150, 200), 'right: veers · stronger', kind='red'), t(*at(l_, 300, 230), 'left: backs · lighter', kind='accent')],
        'fit': [{'x': -600, 'z': -500}, {'x': 600, 'z': 560}]}}

def p4():
    m, s = [-320, -260], [260, 240]
    ci1, tx1 = rings(m, [100, 200, 300], [972, 980, 988], 'L'); ci2, tx2 = rings(s, [70, 140], [998, 1002], 'L', 52)
    mid = [-20, -20]; far = at(s, 135, 200)
    def fl(c, p, kind='low', L=150, col='red'):
        b = math.degrees(math.atan2(p[0] - c[0], -(p[1] - c[1]))); f = flow(kind, b)
        return {'pts': [at(p, f, -L / 2), at(p, f, L / 2)], 'c': col, 'w': 8, 'arrow': True}
    return {'noScale': True, 'sch': {'padPx': 50, 'title': 'A secondary low SE of the main low', 'key': ['Between the two lows their winds oppose and cancel', 'On the far side of the secondary they add: the strongest wind'],
        'circles': ci1 + ci2,
        'paths': [fl(m, [mid[0] - 30, mid[1]], col='ink'), fl(s, [mid[0] + 30, mid[1]]), fl(m, [far[0] - 30, far[1]], col='ink'), fl(s, [far[0] + 30, far[1]])],
        'texts': tx1 + tx2 + [t(m[0], m[1] + 345, 'main 968', pill=False, size=24), t(s[0] + 230, s[1] + 20, 'secondary 994', pill=False, size=24),
                              t(mid[0] + 180, mid[1] - 90, 'winds oppose'), t(far[0] + 60, far[1] + 110, 'winds add: strongest', kind='red')],
        'fit': [{'x': -650, 'z': -600}, {'x': 650, 'z': 600}]}}

def p5():
    return {'noScale': True, 'sch': {'padPx': 60, 'title': 'When does the front arrive?', 'key': ['The front comes E at 25 kn, you go W at 5 kn: closing at 30 kn', '120 M ÷ 30 kn = 4 h: reef before then'],
        'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 270, 'noHeading': True, 'scale': 1.8}, {'x': -200, 'z': 0, 'hdg': 270, 'noHeading': True, 'bearing': False, 'label': 'you, in 4 h', 'labelAbove': True, 'fill': '#9aa0a6', 'scale': 1.8}],
        'paths': [{'pts': [[-1200, -450], [-1240, -150], [-1200, 150], [-1240, 450]], 'c': 'red', 'w': 8}, {'pts': [[-200, -450], [-240, -150], [-200, 150], [-240, 450]], 'c': 'red', 'w': 4, 'dash': '12 10'},
                  {'pts': [[-1150, -300], [-900, -300]], 'c': 'red', 'w': 7, 'arrow': True}, {'pts': [[-60, 0], [-160, 0]], 'c': 'course', 'w': 6, 'arrow': True}],
        'dims': [{'a': [-1200, 300], 'b': [-200, 300], 'text': 'front: 4 h × 25 kn = 100 M', 'off': 0}, {'a': [-200, -170], 'b': [0, -170], 'text': '20 M', 'off': 0}],
        'texts': [t(-1220, -520, 'cold front now', kind='red'), t(-220, -520, 'the front in 4 h'), t(-1020, -380, '25 kn E', pill=False, size=24), t(140, 100, 'W at 5 kn', pill=False, size=24)],
        'fit': [{'x': -1350, 'z': -600}, {'x': 250, 'z': 520}]}}

def p6():
    c = [0, -1500]; pt = at(c, 180, 1100)
    return {'noScale': True, 'sch': {'padPx': 60, 'title': 'From the isobars to the wind on deck', 'key': ['Geostrophic scale 40 kn · curved round a low −15 % = 34 kn · at the sea × 0.8 = 27 kn', 'Backed 15° across the isobars: from 255°, force 6'],
        'paths': [{'pts': [at(c, b, r) for b in range(130, 231, 4)], 'c': 'ink', 'w': 5} for r in (800, 950, 1100, 1250, 1400)] + [{'pts': [at(pt, 270, 330), at(pt, 270, 20)], 'c': 'ink', 'w': 7, 'arrow': True}, {'pts': [at(pt, 255, 280), at(pt, 255, 20)], 'c': 'red', 'w': 9, 'arrow': True}],
        'dims': [{'a': at(c, 152, 950), 'b': at(c, 152, 1100), 'text': 'spacing', 'off': 0}],
        'texts': [t(pt[0] - 260, pt[1] - 80, 'geostrophic 40 kn from 270°'), t(pt[0] - 280, pt[1] + 120, 'at the sea 27 kn from 255°', kind='red'),
                  t(*at(c, 212, 800), '996', size=22), t(*at(c, 212, 950), '1000', size=22), t(*at(c, 212, 1100), '1004', size=22), t(*at(c, 212, 1250), '1008', size=22), t(0, -880, 'low to the north', pill=False, size=24)],
        'fit': [{'x': -900, 'z': -800}, {'x': 900, 'z': -150}]}}

def p7():
    def body(ha):
        x0, x1, y0, y1 = 170, 1180, ha - 90, 90
        X = lambda h: x0 + (h - 6) / 6 * (x1 - x0); Y = lambda p: y0 - (p - 990) / 20 * (y0 - y1)
        s = ''
        for p in range(990, 1011, 5): s += f'<line x1="{x0}" y1="{f1(Y(p))}" x2="{x1}" y2="{f1(Y(p))}" stroke="var(--line)" stroke-width="2"/>' + txt(x0 - 14, Y(p) + 8, f'{p}', 22, 700, MUT, 'end')
        for h in range(6, 13):
            s += f'<line x1="{f1(X(h))}" y1="{y0}" x2="{f1(X(h))}" y2="{y1}" stroke="var(--line)" stroke-width="2"/>' + txt(X(h), y0 + 34, f'{h:02d}00', 22, 700, INK)
        s += txt(x0 - 14, y1 - 26, 'hPa', 22, 700, MUT, 'end')
        trace = [(X(6 + i * 0.05), Y(1006.0 - 0.25 * math.sin(i * 0.3) + (0 if 6 + i * 0.05 <= 9 else -(1005 - 995) * ((6 + i * 0.05 - 9) / 3) ** 1.15) - (0 if 6 + i * 0.05 <= 9 else 1.0 * 0)))
                 for i in range(121)]
        trace = [(x, Y(1006.0 + 0.2 * math.sin(i * 0.4) if 6 + i * 0.05 <= 9 else 1005.0 - 10.0 * ((6 + i * 0.05 - 9) / 3) ** 1.15)) for i, (x, _) in enumerate(trace)]
        s += line(trace, INK, 6)
        s += f'<circle cx="{f1(X(9))}" cy="{f1(Y(1005))}" r="10" fill="var(--bg)" stroke="var(--ink)" stroke-width="4"/><circle cx="{f1(X(12))}" cy="{f1(Y(995))}" r="11" fill="{RED}"/>'
        s += pill(X(9) - 20, Y(1005) - 46, '0900 · 1005', 'light', 22) + pill(X(12) - 110, Y(995) + 46, 'now 995', 'red', 24)
        s += dim(X(12) + 40, Y(1005), X(12) + 40, Y(995), 'fall 10 hPa in 3 h', 0, 'red', 24, -140)
        s += line([(X(9), Y(1005)), (X(12) + 40, Y(1005))], MUT, 3, '6 8')
        return s
    return {'svg': frame('The barometer · a fall of 10 hPa in 3 h', ['6–9 hPa in 3 h: a gale likely · 10 or more: a storm likely', 'A slow fall means a long blow'], body, grid=False)}

def p8():
    def body(ha):
        sea, k = 230, 1.0                                  # 1 px per metre along; heights exaggerated
        X = lambda m: 60 + m * 1.0
        wave = [(X(m), sea - 34 * math.cos(2 * math.pi * (m - 80) / 400)) for m in range(0, 1170, 6)]
        bed = lambda m: sea + 40 + (420 - 0.32 * m)       # sea bed shallowing to the right (depth not to scale)
        s = f'<path d="M{X(0)} {sea} ' + ' '.join(f'L{f1(x)} {f1(y)}' for x, y in wave) + f' L{X(1170)} {ha} L{X(0)} {ha} Z" fill="{COL["sea"]}"/>'
        s += line(wave, COL['seaLine'], 5)
        bedpts = [(X(m), bed(m)) for m in range(0, 1171, 30)]
        s += f'<path d="M{X(0)} {f1(bed(0))} ' + ' '.join(f'L{f1(x)} {f1(y)}' for x, y in bedpts) + f' L{X(1170)} {ha} L{X(0)} {ha} Z" fill="{COL["bed"]}" stroke="{COL["bedLine"]}" stroke-width="5"/>'
        s += dim(X(80), sea - 70, X(480), sea - 70, 'wavelength ≈ 1.56 × 16² = 400 m', 0, 'accent', 24)
        xb = 860; s += line([(X(xb), sea + 40), (X(xb), bed(xb))], RED, 4, '10 8') + pill(X(xb), (sea + bed(xb)) / 2 + 30, 'depth 200 m: it feels the bottom', 'red', 22)
        s += f'<path d="M{X(270) - 30} {sea + 26} L{X(270) + 30} {sea + 26} L{X(270) + 22} {sea + 36} L{X(270) - 22} {sea + 36} Z" fill="var(--ink)"/>' + line([(X(270), sea + 26), (X(270), sea - 4)], INK, 3)
        s += pill(X(270), sea + 80, 'a 12 m yacht', 'light', 20) + txt(1220, ha - 20, 'heights and depths not to scale', 20, 400, MUT, 'end')
        return s
    return {'svg': frame('Swell with a period of 16 s · side view', ['Wavelength ≈ 1.56 × 16² = 400 m: it feels the bottom at half that, 200 m',
        'Speed ≈ 3 × 16 = 48 kn; the swell itself arrives at half that, 24 kn'], body, grid=False)}

def p9():
    def body(ha):
        pts = [(20, 4200), (40, 4200), (70, 3000), (130, 1000), (170, 600), (200, 200), (250, 150), (292, 120), (310, 110)]
        sea = 150; X = lambda u: 40 + (u - 20) / 290 * 1180
        D = lambda d: sea + 30 + (math.log10(d) - 2) / (math.log10(4200) - 2) * (ha - sea - 70)    # depth on a log scale
        prof = [(X(u), D(d)) for u, d in pts]
        s = f'<rect x="0" y="{sea}" width="{S.W}" height="{ha - sea}" fill="{COL["sea"]}"/>'
        s += f'<path d="M{f1(prof[0][0])} {ha} ' + ' '.join(f'L{f1(x)} {f1(y)}' for x, y in prof) + f' L{f1(prof[-1][0])} {ha} Z" fill="{COL["bed"]}" stroke="{COL["bedLine"]}" stroke-width="5"/>'
        wave = []
        for i in range(0, 1201, 5):
            u = 20 + i / 1200 * 290; amp = 10 + 26 * math.exp(-((u - 185) / 30) ** 2); lam = 140 - 70 * math.exp(-((u - 185) / 40) ** 2)
            wave.append((X(u), sea - amp * math.cos(2 * math.pi * i / lam)))
        s += line(wave, COL['seaLine'], 5)
        for u, d in pts[1:-1]: s += txt(X(u), D(d) + 36, f'{d}', 24, 700, INK)
        s += pill(X(185), sea - 70, 'steepest sea: the shelf edge', 'red', 24) + pill(X(70), sea - 70, 'swell 16 s', 'light', 22) + pill(X(270), sea - 70, 'SW 8 by 1800', 'accent', 22)
        s += txt(1220, ha - 16, 'depths in metres, not to scale', 20, 400, MUT, 'end')
        return s
    return {'svg': frame('Crossing the shelf edge · side view', ['The bottom rises from 1000 to 200 m at the edge; there the 16 s swell feels it and steepens',
        'Wind against it makes it worse: cross before the gale arrives'], body, grid=False)}

def p10():
    return {'noScale': True, 'sch': {'padPx': 60, 'title': 'Sea room before a gale', 'key': ['A W gale for 24 h, hove-to: drift 24 h × 2 kn = 48 M', 'Only 40 M to the lee shore: make offing to the west before you heave to'],
        'land': [[[4000, -1500], [5600, -1500], [5600, 1500], [4100, 1500], [3950, 600], [4050, -300]]],
        'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 300, 'noHeading': True, 'scale': 1.8}, {'x': -1300, 'z': 0, 'hdg': 270, 'noHeading': True, 'bearing': False, 'label': 'make offing', 'fill': '#9aa0a6', 'scale': 1.8}],
        'paths': [{'pts': [[80, 220], [4700, 220]], 'c': 'red', 'w': 6, 'dash': '14 10', 'arrow': True}, {'pts': [[-100, 0], [-1150, 0]], 'c': 'course', 'w': 6, 'arrow': True},
                  {'pts': [[-1300, -600], [-700, -600]], 'c': 'red', 'w': 10, 'arrow': True}],
        'dims': [{'a': [0, -260], 'b': [4000, -260], 'text': 'sea room 40 M', 'off': 0}],
        'texts': [t(2400, 330, 'drift 24 h × 2 kn = 48 M', kind='red'), t(4800, 0, 'lee shore', pill=False, size=28), t(4300, 420, 'aground', kind='red'), t(-1000, -730, 'W gale, 24 h', kind='red')],
        'fit': [{'x': -1600, 'z': -850}, {'x': 5400, 'z': 700}]}}

def p11():
    s = 20.0; P = lambda x, y: [round((x - 160) * s, 1), round((y - 100) * s, 1)]
    poly = [P(*p) for p in path_polys('M150 50 C185 50 200 75 198 98 C196 125 175 142 150 142 C120 142 102 122 102 96 C102 70 120 50 150 50 Z')[0]]
    def ell(cx, cz, rx, rz, rot):
        a = math.radians(rot); return [[round(cx + rx * math.cos(k / 24 * math.tau) * math.cos(a) - rz * math.sin(k / 24 * math.tau) * math.sin(a), 1),
                                        round(cz + rx * math.cos(k / 24 * math.tau) * math.sin(a) + rz * math.sin(k / 24 * math.tau) * math.cos(a), 1)] for k in range(24)]
    nw, se, sw = P(86, 44), P(214, 150), P(70, 156)
    return {'noScale': True, 'sch': {'padPx': 50, 'wind': 45, 'title': 'A high island in the NE trade wind', 'key': ['The wind speeds up round the flanks, at the corners across the wind', 'Downwind lies its wind shadow: light and fluky, gusty at the edges'],
        'land': [poly], 'zones': [{'pts': ell(*nw, 520, 260, 45), 'c': 'red', 'fill': 'rgba(224,37,27,.12)'}, {'pts': ell(*se, 520, 260, 45), 'c': 'red', 'fill': 'rgba(224,37,27,.12)'},
                                   {'pts': [P(108, 118), P(128, 138), P(110, 180), P(60, 200), P(20, 180), P(40, 140), P(80, 128)], 'c': 'ink', 'fill': 'rgba(0,0,0,.05)'}],
        'paths': [{'pts': [P(250, 10), P(215, 45)], 'c': 'red', 'w': 8, 'arrow': True}, {'pts': [P(150, 0), P(110, 40)], 'c': 'red', 'w': 6, 'arrow': True}, {'pts': [P(250, 100), P(225, 125)], 'c': 'red', 'w': 6, 'arrow': True},
                  {'pts': [P(110, 40), P(60, 80)], 'c': 'red', 'w': 10, 'arrow': True}, {'pts': [P(222, 140), P(182, 190)], 'c': 'red', 'w': 10, 'arrow': True}],
        'texts': [t(*P(80, 30), 'stronger', kind='red'), t(*P(226, 168), 'stronger', kind='red'), t(*P(62, 165), 'wind shadow'), t(*P(150, 96), 'high island', pill=False, size=26)],
        'fit': [{'x': P(20, 0)[0], 'z': P(20, 0)[1]}, {'x': P(290, 205)[0], 'z': P(290, 205)[1]}]}}

def p12():
    cell = [1540, -840]; c30 = at(cell, 173, 900)
    return {'noScale': True, 'sch': {'padPx': 60, 'title': 'A thunderstorm cell on radar', 'key': ['Plot the cell like a ship: S at 18 kn, it crosses your track well ahead', 'You cannot outrun it: reef, and pass astern of it · CAPE 1800 J/kg: expect more'],
        'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 90, 'noHeading': True, 'label': 'You, 6 kn'}, {'x': 300, 'z': 0, 'hdg': 90, 'noHeading': True, 'bearing': False, 'label': 'in 30 min', 'labelAbove': True, 'fill': '#9aa0a6'}],
        'circles': [{'x': cell[0], 'z': cell[1], 'r': 170, 'c': 'red', 'dash': '0', 'fill': 'rgba(224,37,27,.25)'}, {'x': c30[0], 'z': c30[1], 'r': 170, 'c': 'red', 'fill': 'rgba(224,37,27,.08)'}],
        'paths': [{'pts': [at(cell, 173, 190), at(cell, 173, 1500)], 'c': 'red', 'w': 5, 'dash': '14 10', 'arrow': True}, {'pts': [[60, 0], [1200, 0]], 'c': 'course', 'w': 5, 'dash': '14 10', 'arrow': True}],
        'texts': [t(cell[0] - 560, cell[1], 'Cb cell, 18 kn S', kind='red'), t(c30[0] + 380, c30[1] - 40, 'in 30 min'), t(950, -260, 'it crosses ahead: pass astern of it', kind='accent')],
        'fit': [{'x': -250, 'z': -1100}, {'x': 2200, 'z': 800}]}}

if __name__ == '__main__':
    os.makedirs(DIR, exist_ok=True)
    for n, fn in ((1, p1), (2, p2), (3, p3), (4, p4), (5, p5), (6, p6), (7, p7), (8, p8), (9, p9), (10, p10), (11, p11), (12, p12)):
        S.write(DIR, n, fn()); print('plan', n)
    print('svg strings:', len(S.USED))
