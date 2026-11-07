# Plan-view schematics for the Yachtmaster Offshore navigation articles (charts, compass, dr): writes
# figure-style/articles/yachtmaster-offshore/<article>/<n>-plan.json, in the spec format of figure-schematic.js
# ({noScale, sch: {...}}; scene x east, z south) or {svg} drawn here in the same style. The geometry is worked from
# the articles' numbers: positions in miles x a factor, bearings clockwise from north.
#   python3 docs/design/blender/art_yof_nav_plans.py [charts|compass|dr]
import os, sys, json, math

HERE = os.path.dirname(os.path.abspath(__file__))
ARTS = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore')
R = math.radians

def MP(lat, e2=0.00669438):
    p = R(lat)
    return 7915.7045 * math.log10(math.tan(math.pi / 4 + p / 2)) - 3437.7468 * (e2 * math.sin(p) + e2 ** 2 / 3 * math.sin(p) ** 3 + e2 ** 3 / 5 * math.sin(p) ** 5)

def r1(v): return round(v, 1)
def P(x, z): return [r1(x), r1(z)]
def ray(x, z, b, L): return P(x + L * math.sin(R(b)), z - L * math.cos(R(b)))
def EN(E, N, k): return P(E * k, -N * k)          # miles east/north -> plan units
def line(a, b, c='ink', w=4, dash=None, arrow=False):
    d = {'pts': [list(a), list(b)], 'c': c, 'w': w}
    if dash: d['dash'] = dash
    if arrow: d['arrow'] = True
    return d
def arr(a, b, c='ink', w=5): return line(a, b, c, w, None, True)
def poly(pts, c='ink', w=4, dash=None):
    d = {'pts': [list(p) for p in pts], 'c': c, 'w': w}
    if dash: d['dash'] = dash
    return d
def t(x, z, text, kind=None, pill=True, size=None):
    d = {'x': r1(x), 'z': r1(z), 'text': text}
    if kind: d['kind'] = kind
    if not pill: d['pill'] = False
    if size: d['size'] = size
    return d
def tp(p, text, kind=None, dx=0, dz=0, **k): return t(p[0] + dx, p[1] + dz, text, kind, **k)
def arcpts(c, r, a0, a1, n=24): return [ray(c[0], c[1], a0 + (a1 - a0) * i / n, r) for i in range(n + 1)]
def plan(title, key, pad=60, scale=False, **o):
    d = {'sch': {'padPx': pad, 'title': title, 'key': key, **o}}
    if not scale: d['noScale'] = True
    return d
def boat(x, z, hdg, you=True, **o): return {'you': you, 'x': r1(x), 'z': r1(z), 'hdg': hdg, 'noHeading': True, **o}

def compass_lines(title, key, items, boat_hdg):
    """Course lines from a boat at the origin: items [(bearing, label, colour, dash, side, dist)]; the label at
    `dist` along its line, moved `side` across it (+ to the north-west for lines running south-west)."""
    paths, texts, xs, zs = [], [], [0], [0]
    for b, lab, c, dash, side, dist in items:
        e = ray(0, 0, b, 620); paths.append(line((0, 0), e, c, 5 if c != 'ink' else 4, dash)); xs.append(e[0]); zs.append(e[1])
        p = ray(0, 0, b, dist); n = (math.cos(R(b)) * side, math.sin(R(b)) * side)
        texts.append(t(p[0] + n[0], p[1] + n[1], lab, {'red': 'red', 'course': 'accent'}.get(c))); xs.append(p[0] + n[0]); zs.append(p[1] + n[1])
    fit = [{'x': min(xs) - 140, 'z': min(zs) - 60}, {'x': max(xs) + 140, 'z': max(zs) + 80}]
    return plan(title, key, 60, paths=paths, texts=texts, boats=[boat(0, 0, boat_hdg)], fit=fit)

# ---------------------------------------------------------------- svg helpers (the schematic's look)
W, H = 1280, 800
def esc(s): return str(s).replace('&', '&amp;').replace('<', '&lt;')
def stext(x, y, s, size=26, w=700, fill='var(--ink)', anchor='middle'):
    return f'<text x="{r1(x)}" y="{r1(y)}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{anchor}">{esc(s)}</text>'
def spill(x, y, s, kind='light', size=26):
    w = len(s) * size * 0.58 + size * 1.4; h = size * 1.7
    fill = {'accent': 'var(--accent)', 'red': '#e8231a'}.get(kind, 'var(--bg)'); ink = 'var(--ink)' if kind == 'light' else '#fff'
    stroke = 'var(--tag-line)' if kind == 'light' else fill
    return f'<rect x="{r1(x - w / 2)}" y="{r1(y - h / 2)}" width="{r1(w)}" height="{r1(h)}" rx="{r1(h / 2)}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>' + stext(x, y + size * 0.36, s, size, 700, ink)
def sline(x1, y1, x2, y2, c='var(--ink)', w=4, dash=None):
    return f'<line x1="{r1(x1)}" y1="{r1(y1)}" x2="{r1(x2)}" y2="{r1(y2)}" stroke="{c}" stroke-width="{w}" stroke-linecap="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
def sarrow(x1, y1, x2, y2, c='var(--ink)', w=5, h=20):
    a = math.atan2(y2 - y1, x2 - x1); p1 = (x2 - h * math.cos(a - .5), y2 - h * math.sin(a - .5)); p2 = (x2 - h * math.cos(a + .5), y2 - h * math.sin(a + .5))
    return sline(x1, y1, x2 - h * 0.6 * math.cos(a), y2 - h * 0.6 * math.sin(a), c, w) + f'<path d="M{r1(x2)} {r1(y2)} L{r1(p1[0])} {r1(p1[1])} L{r1(p2[0])} {r1(p2[1])} Z" fill="{c}"/>'
def svg_doc(body, title, key):
    keyH = 40 + 40 * len(key) + 24
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="{W}" height="{H}" fill="var(--bg)"/>'
    s += body + f'<rect x="0" y="{H - keyH}" width="{W}" height="{keyH}" fill="var(--band)"/>'
    ky = H - keyH + 40; s += stext(30, ky, title, 30, 700, 'var(--ink)', 'start')
    for k in key: ky += 40; s += stext(30, ky, '· ' + k, 27, 400, 'var(--ink)', 'start')
    return {'svg': s + '</svg>'}
YEL, RED = '#e0b400', '#e8231a'

# ================================================================ charts
def charts():
    out = {}
    # 1 Mercator: parallels spaced by meridional parts
    s = 0.3; z = lambda lat: -(MP(lat) - MP(50)) * s
    paths = [line((-300, z(v)), (300, z(v)), 'ink', 4) for v in (40, 50, 60)] + [line((x, z(60) - 20), (x, z(40) + 20), 'ink', 2) for x in (-270, -90, 90, 270)]
    out[1] = plan('Mercator · the latitude scale grows northward', ['10° of latitude is 600 M wherever it is', 'On paper 50°–60°N is 1.24 times as tall as 40°–50°N: measure beside the leg'],
                  60, paths=paths, dims=[{'a': [-120, r1(z(40))], 'b': [-120, r1(z(50))], 'text': '600 M'}, {'a': [-120, r1(z(50))], 'b': [-120, r1(z(60))], 'text': '600 M'}],
                  texts=[t(-380, z(v) + 9, f'{v}°N', pill=False, size=30) for v in (40, 50, 60)] + [t(150, (z(40) + z(50)) / 2, '849 parts'), t(150, (z(50) + z(60)) / 2, '1051 parts')],
                  fit=[{'x': -420, 'z': z(60) - 30}, {'x': 320, 'z': z(40) + 30}])
    # 2 the same opening on the scale beside the leg (48N) and at 42N
    s = 0.9; z = lambda lat: -(MP(lat) - MP(45)) * s; L = 67.25 * s
    paths = [line((-200, z(41)), (-200, z(49)), 'ink', 6)] + [line((-215, z(v)), (-185, z(v)), 'ink', 4) for v in range(41, 50)]
    paths += [line((-40, z(48)), (200, z(48)), 'ink', 2, '6 8'), line((-40, z(42)), (200, z(42)), 'ink', 2, '6 8'), arr((0, z(48)), (L, z(48)), 'course', 6)]
    out[2] = plan('Distance on a Mercator chart · beside the leg', ['A 45.0 M leg along 48°N: on the scale beside it the dividers span 45′', 'The same opening read at 42°N spans 50.0′: 50.0 × cos 48° ÷ cos 42° = 45.0'],
                  60, paths=paths, dims=[{'a': [-260, r1(z(48 + 22.5 / 60))], 'b': [-260, r1(z(48 - 22.5 / 60))], 'text': "45′"}, {'a': [-260, r1(z(42 + 25 / 60))], 'b': [-260, r1(z(42 - 25 / 60))], 'text': "50.0′"}],
                  texts=[t(-105, z(v) + 9, f'{v}°N', pill=False) for v in (42, 45, 48)] + [t(L / 2, z(48) - 50, 'leg 45.0 M', 'accent')],
                  fit=[{'x': -330, 'z': z(49)}, {'x': 220, 'z': z(41)}])
    # 3 mid-latitude sailing: the plane triangle
    k = 4.0; S0 = (0, 0); D = EN(-64.28, -76.60, k); C0 = (0, D[1])
    out[3] = plan('Mid-latitude sailing', ["d.lat 100 × cos 40° = 76.6′ · departure 100 × sin 40° = 64.3 M", "d.long = 64.3 ÷ cos 43°31.7′ = 88.7′ = 1°28.7′ W"],
                  60, paths=[arr(S0, D, 'course', 6), line(S0, C0, 'ink', 4, '12 10'), line(C0, D, 'ink', 4, '12 10')],
                  texts=[t(0, -45, "44°10.0′N 008°30.0′W"), tp(D, "DR 42°53.4′N 009°58.7′W", 'accent', 0, 125), t(95, D[1] / 2, "d.lat 76.6′"),
                         t(D[0] / 2, D[1] + 50, 'departure 64.3 M'), t(D[0] / 2 - 110, D[1] / 2, '220°T 100 M')],
                  fit=[{'x': -420, 'z': -80}, {'x': 220, 'z': D[1] + 140}])
    # 4 Mercator sailing: the triangle in meridional parts
    k = 1.4; E = P(-140 * k, 218.3 * k)
    out[4] = plan('Mercator sailing', ["tan C = d.long 140′ ÷ DMP 218.3: C = S 32.7° W = 213°T", "Distance = d.lat 150′ ÷ cos 32.7° = 178.2 M"],
                  60, paths=[arr((0, 0), E, 'course', 6), line((0, 0), (0, E[1]), 'ink', 4, '12 10'), line((0, E[1]), E, 'ink', 4, '12 10'), poly(arcpts((0, 0), 70, 180, 212.7), 'ink', 3)],
                  texts=[t(0, -45, "48°00.0′N 006°00.0′W"), tp(E, "45°30.0′N 008°20.0′W", None, 0, 125), t(100, E[1] / 2, 'DMP 218.3'), t(E[0] / 2, E[1] + 50, "d.long 140′"),
                         t(E[0] / 2 - 120, E[1] / 2, '213°T · 178.2 M', 'accent'), t(-40, 110, '32.7°', pill=False)],
                  fit=[{'x': -380, 'z': -80}, {'x': 200, 'z': E[1] + 140}])
    # 5 the bank and the EP, 1 M = 40
    k = 40.0
    def ell(a, b, rot, n=48):
        o = []
        for i in range(n):
            th = 2 * math.pi * i / n; x, y = a * math.cos(th), b * math.sin(th); r = R(rot)
            o.append(EN(x * math.cos(r) + y * math.sin(r), -x * math.sin(r) + y * math.cos(r), k))
        return o
    edge = EN(5.0 * math.sin(R(130)), 5.0 * math.cos(R(130)), k); ep = EN(5.945 * math.sin(R(130)), 5.945 * math.cos(R(130)), k)
    fix = ray(ep[0], ep[1], 25, 42 * k * 0.25)
    out[5] = plan('Scale 1:350,000 · what a millimetre is worth', ['1 mm on the chart is 350 m: the EP 5 mm off the 20 m line is 0.9 M off', 'Six hours of EP can be out by more than that: give the bank a wide berth'],
                  60, zones=[{'pts': ell(5.0, 2.2, 40), 'c': 'ink', 'fill': 'rgba(60,140,190,.18)', 'dash': '0'}, {'pts': ell(7.2, 3.6, 40), 'c': 'ink', 'fill': 'none'}],
                  paths=[line(fix, ep, 'ink', 4, '12 10')], spots=[{'x': ep[0], 'z': ep[1], 'label': 'EP'}],
                  dims=[{'a': edge, 'b': ep, 'text': '5 mm = 0.9 M', 'off': -70}],
                  texts=[t(0, 0, '20 m', pill=False), t(-60, 40, '14', pill=False), t(-250, -150, '30 m', pill=False), tp(fix, 'DR from the 0000 fix', None, 0, -40)],
                  fit=[{'x': -330, 'z': -220}, {'x': 360, 'z': 330}])
    # 6 the Breton plotter: true and magnetic
    out[6] = plan('Breton plotter · true and magnetic', ['Grid on a meridian, the arrow along the track: 205° at the index', 'At the 6°W mark the same setting reads 211°M'],
                  60, paths=[line((0, 0), (0, -380), 'ink', 3), line((0, 0), ray(0, 0, 354, 380), 'ink', 3, '10 8'), line((0, 0), ray(0, 0, 205, 620), 'red', 5), line((0, 0), ray(0, 0, 211, 640), 'course', 5)],
                  texts=[t(-160, -330, 'N (true)', pill=False), tp(ray(0, 0, 354, 420), 'MN 6°W', None, 110), tp(ray(0, 0, 205, 680), 'track 205°T', 'red', 80), tp(ray(0, 0, 211, 690), '211°M', 'accent', -90)],
                  boats=[boat(0, 0, 205)], fit=[{'x': -420, 'z': -440}, {'x': 260, 'z': 640}])
    # 8 the platform and its zone (metres)
    out[8] = plan('Platform · lights and safety zone', ['White Mo(U) 15s in the middle, red lights at its ends; in fog it sounds Mo(U)', 'A 500 m safety zone round it: pass outside'], 60, scale=True,
                  quays=[{'x1': -70, 'z1': -50, 'x2': 70, 'z2': 50}], circles=[{'x': 0, 'z': 0, 'r': 500, 'c': 'red'}, {'x': -82, 'z': 0, 'r': 22, 'c': 'red', 'dash': '0', 'fill': '#e0251b'},
                  {'x': 82, 'z': 0, 'r': 22, 'c': 'red', 'dash': '0', 'fill': '#e0251b'}, {'x': 0, 'z': 0, 'r': 22, 'c': 'ink', 'dash': '0', 'fill': '#ffffff'}],
                  paths=[arr((-800, 700), (700, 700), 'course', 5)], boats=[boat(-650, 700, 90)],
                  texts=[t(0, -140, 'white Mo(U) 15s'), t(260, 170, 'red at its ends', 'red'), t(0, -560, '500 m safety zone', 'red')],
                  fit=[{'x': -820, 'z': -620}, {'x': 820, 'z': 900}])
    # 9 the wind farm (metres)
    circ, paths = [], []
    for row in range(3):
        for col in range(5):
            x, z_ = col * 700 - 1400, row * 700 - 700; per = row in (0, 2) or col in (0, 4)
            circ.append({'x': x, 'z': z_, 'r': 60, 'c': 'course' if per else 'ink', 'dash': '0', 'fill': '#ffa800' if per else 'none'})
        paths.append(line((-1400, row * 700 - 700 + 120), (1400, row * 700 - 700 + 120), 'red', 3, '10 10'))
    paths += [line((1400, -580), (2300, -580), 'red', 3, '10 10'), arr((-2100, 1050), (2100, 1050), 'course', 5)]
    out[9] = plan('Wind farm · lights, rules, cables', ['Yellow lights on the structures flash together; red aviation lights on the nacelles', 'Transit by the chart note · check the blade-tip height · never anchor among the cables'],
                  60, scale=True, circles=circ, paths=paths, boats=[boat(-1800, 1050, 90)],
                  texts=[t(0, -1000, 'yellow, flashing together', 'accent'), t(1900, -470, 'export cable', 'red'), t(700, 1180, 'pass outside')],
                  fit=[{'x': -2200, 'z': -1150}, {'x': 2350, 'z': 1400}])
    # 11 the safety contour, a depth stack (svg)
    top, mpx = 90, 72.0; Y = lambda m: top + m * mpx
    b = sline(60, top, 1220, top, '#3c8cbe', 5) + stext(70, top - 18, 'sea level', 24, 700, 'var(--muted)', 'start')
    x0 = 220; parts = [(2.1, 'draught 2.1 m', '#1f2a3a', 1.05), (0.3, 'squat 0.3 m', '#5b6b80', 2.15), (0.8, 'half the swell 0.8 m', '#8aa2c0', 2.85), (1.0, 'margin 1.0 m', '#c4d2e2', 3.7)]
    acc = 0.0
    for v, lab, col, ly in parts:
        b += f'<rect x="{x0}" y="{r1(Y(acc))}" width="150" height="{r1(v * mpx)}" fill="{col}" stroke="var(--ink)" stroke-width="2"/>'
        b += stext(x0 + 172, Y(ly) + 9, lab, 26, 700, 'var(--ink)', 'start'); acc += v
    b += sline(x0 - 30, Y(4.2), x0 + 470, Y(4.2), RED, 4, '12 8') + spill(x0 + 560, Y(4.2), '4.2 m asked', 'red', 26)
    for dpt, bold in ((2, False), (5, True)):
        b += sline(820, Y(dpt), 1220, Y(dpt), 'var(--ink)', 10 if bold else 3) + stext(805, Y(dpt) + 9, f'{dpt} m', 26, 700, 'var(--ink)', 'end')
    b += spill(1020, Y(5) + 42, 'bold: 5 m', 'accent', 26) + stext(1020, Y(2) - 14, 'cell contours', 24, 700, 'var(--muted)') + stext(1020, Y(5) + 100, '10 m and 20 m deeper', 24, 700, 'var(--muted)')
    out[11] = svg_doc(b, 'Safety contour · 4.2 m asked, 5 m drawn bold', ['Draught 2.1 + squat 0.3 + half the 1.6 m swell 0.8 + margin 1.0 = 4.2 m',
                      'Cell contours 2, 5, 10, 20 m: the next deeper, 5 m, is bold · look-ahead 18 kn × 10 min = 3.0 M'])
    return out

# ================================================================ compass
def compass():
    out = {}
    out[1] = compass_lines('Steering compass · true to magnetic', ['245°T + 3° west variation = 248°M', 'The lubber line parallel to the fore-and-aft line reads the heading'],
                           [(245, '245°T', 'red', None, -60, 700), (248, '248°M', 'course', None, 60, 700)], 248)
    # 3 deviation by the sun's azimuth
    out[3] = plan('Deviation by the sun’s azimuth', ['Tabled azimuth 118°T + 4°W = 122°M; over the compass the sun bears 119°C', 'The compass reads 3° low: deviation 3°E on 165°C'],
                  60, boats=[boat(0, 0, 165)], paths=[line((0, 0), ray(0, 0, 165, 300), 'ink', 3, '10 8'), line((0, 0), ray(0, 0, 122, 620), 'red', 5), line((0, 0), ray(0, 0, 119, 640), 'course', 5)],
                  texts=[tp(ray(0, 0, 165, 340), 'heading 165°C'), tp(ray(0, 0, 122, 690), '122°M tabled', 'red', 0, 50), tp(ray(0, 0, 119, 700), '119°C by the compass', 'accent', 0, -55)], circles=[{'x': ray(0, 0, 120, 700)[0], 'z': ray(0, 0, 120, 700)[1], 'r': 26, 'c': 'course', 'dash': '0', 'fill': '#ffd34a'}],
                  fit=[{'x': -120, 'z': -420}, {'x': 820, 'z': 360}])
    out[4] = compass_lines('Deviation by satellite compass', ['Satellite compass 240°T + 3° west variation = 243°M', 'The compass reads 248°C: deviation 5°W on this heading'],
                           [(240, '240°T satellite', 'red', None, -70, 700), (243, '243°M', 'ink', '14 10', -40, 420), (248, '248°C compass', 'course', None, 70, 700)], 248)
    # 5 two radar ranges, 1 M = 30
    k = 30.0; A = (0, 0); B = EN(11.775, -10.235, k); rA, rB = 9.3 * k, 7.8 * k
    dx, dz = B[0] - A[0], B[1] - A[1]; dd = math.hypot(dx, dz); a = (rA * rA - rB * rB + dd * dd) / (2 * dd); hh = math.sqrt(rA * rA - a * a)
    px_, pz_ = A[0] + a * dx / dd, A[1] + a * dz / dd
    X1 = P(px_ - hh * dz / dd, pz_ + hh * dx / dd); X2 = P(px_ + hh * dz / dd, pz_ - hh * dx / dd)
    X, Yp = (X1, X2) if X1[1] > X2[1] else (X2, X1)
    brg = (math.degrees(math.atan2(A[0] - X[0], (X[1] - A[1]))) + 360) % 360
    isl = lambda c, r: [P(c[0] + math.cos(th) * r * (1 + 0.2 * math.sin(3 * th)), c[1] + math.sin(th) * r * 0.8) for th in [i * math.pi / 12 for i in range(24)]]
    out[5] = plan('Two radar ranges · and a rough bearing', ['Ranges A 9.3 M and B 7.8 M: the two circles cross at X and at Y', f'A rough bearing of A, about 333°T, picks X'],
                  60, land=[isl(A, 30), isl(B, 36)], circles=[{'x': A[0], 'z': A[1], 'r': r1(rA), 'c': 'ink', 'dash': '12 10'}, {'x': B[0], 'z': B[1], 'r': r1(rB), 'c': 'ink', 'dash': '12 10'}],
                  paths=[line(X, A, 'course', 4, '14 10')], spots=[{'x': X[0], 'z': X[1], 'label': 'X'}, {'x': Yp[0], 'z': Yp[1], 'label': 'Y'}],
                  texts=[tp(A, 'A', None, -60, -40, pill=False, size=34), tp(B, 'B', None, 60, 50, pill=False, size=34), tp(ray(A[0], A[1], 250, rA), '9.3 M', None, 0, 0),
                         tp(ray(B[0], B[1], 120, rB), '7.8 M'), tp(ray(X[0], X[1], brg, 120), 'EBL ≈ 333°T', 'accent', 130, 30)],
                  fit=[{'x': -300, 'z': -300}, {'x': 600, 'z': 560}])
    print('radar plan brg', round(brg, 1))
    # 6 four-point bearing, 1 M = 40
    k = 40.0; L = EN(0, 8, k); P0 = EN(-8, 0, k); B1 = (0, 0)
    out[6] = plan('Four-point bearing · 45° and abeam', ['0100: the light 45° on the bow · 0130: abeam', 'Distance off abeam = the run between: 8 M'],
                  60, land=[[P(-90, -330), P(90, -330), P(110, -400), P(-110, -400)]], paths=[arr(P(-420, 0), P(160, 0), 'course', 5), line(P0, L, 'ink', 4, '12 10'), line(B1, L, 'ink', 4, '12 10'), poly(arcpts(P0, 70, 45, 90), 'ink', 3)],
                  boats=[boat(0, 0, 90)], spots=[{'x': P0[0], 'z': P0[1], 'label': ''}],
                  texts=[tp(L, 'Light', None, 0, -24, pill=False, size=30), tp(P0, '0100', None, 0, 60), t(70, 70, '0130'), t(-160, 50, 'run 8 M', 'accent'), t(80, -160, '8 M off', 'accent'), tp(P0, '45°', None, 75, -55, pill=False)],
                  fit=[{'x': -440, 'z': -420}, {'x': 200, 'z': 120}])
    # 7 running fix with stream, 1 M = 20
    k = 20.0; L = (0, 0)
    P0 = EN(-11.161, -9.366, k); Wt = EN(-11.161 + 16 * math.sin(R(80)), -9.366 + 16 * math.cos(R(80)), k)
    G = EN(-11.161 + 16 * math.sin(R(80)) + 2 * math.sin(R(170)), -9.366 + 16 * math.cos(R(80)) + 2 * math.cos(R(170)), k); Fx = EN(9.885 * math.sin(R(150)), 9.885 * math.cos(R(150)), k)
    out[7] = plan('Running fix with stream', ['Ground run: 080°T 16.0 M + stream 170°T 2.0 M = 087°T 16.1 M', 'The 0100 line (050°T) moved along it, cut by the 0300 line (330°T): the fix'],
                  50, land=[[P(-300, -60), P(-80, -30), P(0, 0), P(60, -20), P(200, -30), P(300, -70), P(300, -140), P(-300, -140)]],
                  paths=[line(L, ray(0, 0, 230, 17 * k), 'ink', 4), line(ray(Fx[0], Fx[1], 230, 4 * k), ray(Fx[0], Fx[1], 50, 6 * k), 'ink', 4, '14 10'), line(L, ray(0, 0, 150, 12.5 * k), 'ink', 4),
                         arr(P0, Wt, 'ink', 4), arr(Wt, G, 'course', 5), arr(P0, G, 'red', 5)],
                  spots=[{'x': Fx[0], 'z': Fx[1], 'label': ''}],
                  texts=[t(0, -30, 'Light', pill=False, size=30), tp(ray(0, 0, 230, 13 * k), '0100: 050°T', None, -80, 0), tp(ray(0, 0, 150, 12.5 * k), '0300: 330°T', None, 60, 30),
                         tp(Fx, 'fix', 'accent', 70, 30), tp(P0, 'water 080°T 16.0 M', None, 150, -70), tp(Wt, 'stream 2.0 M', 'accent', -40, -50), tp(P0, 'ground 087°T 16.1 M', 'red', 170, 60),
                         tp(ray(Fx[0], Fx[1], 50, 6 * k), '0100 line moved', None, 100, -10)],
                  fit=[{'x': -320, 'z': -150}, {'x': 300, 'z': 280}])
    # 8 rising range, side view (svg)
    def rising():
        sea_y, cx, kc = 470, 640, 110 / 600 ** 2
        ya = lambda x: sea_y + (x - cx) ** 2 * kc
        curve = ' '.join(f'{"M" if i == 0 else "L"}{r1(60 + i * 23.2)} {r1(ya(60 + i * 23.2))}' for i in range(51))
        b = f'<path d="{curve}" fill="none" stroke="#3c8cbe" stroke-width="6"/>'
        hx = 860; slope = 2 * (hx - cx) * kc; tan = lambda x: ya(hx) + slope * (x - hx)
        lx, ex = 120, 1040; ltop, etop = tan(lx), tan(ex)
        b += f'<rect x="{lx - 12}" y="{r1(ltop)}" width="24" height="{r1(ya(lx) - ltop)}" fill="var(--ink)"/><circle cx="{lx}" cy="{r1(ltop)}" r="16" fill="#ffd34a" stroke="var(--ink)" stroke-width="3"/>'
        b += f'<rect x="{ex - 6}" y="{r1(etop)}" width="12" height="{r1(ya(ex) - etop)}" fill="var(--accent)"/><circle cx="{ex}" cy="{r1(etop)}" r="12" fill="var(--accent)"/>'
        b += sline(lx, ltop, ex, etop, YEL, 5, '14 10') + f'<circle cx="{hx}" cy="{r1(ya(hx))}" r="9" fill="var(--ink)"/>'
        b += spill(lx + 110, (ltop + ya(lx)) / 2, 'H 43 m', 'light', 26) + spill(ex + 90, (etop + ya(ex)) / 2, 'h 4 m', 'accent', 26) + stext(hx, ya(hx) + 44, 'your horizon', 26, 700, 'var(--muted)')
        b += spill((lx + hx) / 2, tan((lx + hx) / 2) - 50, '2.08 × √43 = 13.6 M', 'light', 26) + spill((hx + ex) / 2, tan((hx + ex) / 2) - 50, '2.08 × √4 = 4.2 M', 'light', 26)
        return svg_doc(b, 'Rising range · the light on your horizon', ['Rising range 2.08 × (√H + √h) = 13.6 + 4.2 = 17.8 M', 'Seen only from the crests: the light is just on your horizon'])
    out[8] = rising()
    # 9 vertical sextant angle (svg)
    def vsa():
        wy = 500; k = 6.5; b = sline(40, wy, 1240, wy, '#3c8cbe', 6)          # 6.5 px per metre of height
        hw = wy - 3.0 * k
        b += f'<path d="M80 {wy} L80 {r1(wy - 26 * k)} L230 {r1(wy - 27 * k)} L250 {wy} Z" fill="#d8c9a3" stroke="#6b5a3a" stroke-width="4"/>'
        tx = 160; ly = wy - 43 * k
        b += f'<rect x="{tx - 10}" y="{r1(ly)}" width="20" height="{r1(27 * k - 43 * k + 43 * k - 27 * k + (43 - 26.5) * k)}" fill="var(--ink)"/><circle cx="{tx}" cy="{r1(ly)}" r="15" fill="#ffd34a" stroke="var(--ink)" stroke-width="3"/>'
        b += sline(60, hw, 330, hw, 'var(--ink)', 3, '10 8') + stext(340, hw + 8, 'MHWS', 24, 700, 'var(--ink)', 'start')
        ox = 1150; th = math.atan2(wy - 6 - ly, ox - tx)
        b += sline(ox, wy - 6, tx, ly, YEL, 4) + sline(ox, wy - 6, 250, wy - 2, YEL, 4)
        r = 230; b += f'<path d="M{ox - r} {wy - 6} A{r} {r} 0 0 1 {r1(ox - r * math.cos(th))} {r1(wy - 6 - r * math.sin(th))}" fill="none" stroke="var(--accent)" stroke-width="5"/>'
        b += spill(ox - r - 120, wy - 40, "angle 0°20.0′", 'accent', 26) + spill(tx + 210, ly - 10, 'H = 40 + 3.0 = 43 m', 'light', 26)
        b += spill((ox + 250) / 2, wy + 50, 'distance off 4.0 M', 'light', 26)
        b += f'<circle cx="{ox}" cy="{wy - 6}" r="10" fill="var(--accent)"/>'
        return svg_doc(b, 'Vertical sextant angle · distance off', ['Light 40 m above MHWS; the tide is 3.0 m below MHWS: H = 43 m', 'Distance off = 1.854 × 43 ÷ 20.0′ = 4.0 M (index error applied)'])
    out[9] = vsa()
    # 10 one position line, 1 M = 50
    k = 80.0; L = (0, 0); Q = EN(6 * math.sin(R(200)), 6 * math.cos(R(200)), k)
    EPp = P(Q[0] + 1.2 * k * math.sin(R(110)), Q[1] - 1.2 * k * math.cos(R(110))); end = ray(0, 0, 200, 10.5 * k)
    out[10] = plan('One position line · the point nearest the EP', ['One line only: the light bears 020°T, so you are somewhere on the line', 'Take the point on it nearest the EP, and log the line with its time'],
                   60, land=[[P(-520, -40), P(-200, -30), P(0, 0), P(200, -40), P(520, -30), P(520, -140), P(-520, -140)]],
                   paths=[arr(L, end, 'ink', 4), line(EPp, Q, 'red', 4, '10 8')], spots=[{'x': EPp[0], 'z': EPp[1], 'label': 'EP'}],
                   texts=[t(0, -40, 'Light', pill=False, size=30), tp(ray(0, 0, 200, 3.0 * k), 'light bears 020°T', None, -150, 0), tp(Q, 'here', 'accent', -90, 0)],
                   fit=[{'x': -520, 'z': -140}, {'x': 420, 'z': 860}])
    return out

# ================================================================ dr
def dr():
    out = {}
    out[1] = compass_lines('Compass to true · and back', ['237°C − 3° west deviation = 234°M', '234°M − 4° west variation = 230°T: plot 230°T'],
                           [(230, '230°T', 'red', None, -60, 700), (234, '234°M', 'ink', '14 10', -40, 420), (237, '237°C', 'course', None, 60, 700)], 230)
    # 2 two legs, 1 M = 10
    k = 10.0; F = (0, 0); D1 = EN(24 * math.sin(R(240)), 24 * math.cos(R(240)), k)
    D2 = P(D1[0] + 24 * k * math.sin(R(200)), D1[1] - 24 * k * math.cos(R(200)))
    out[2] = plan('Dead reckoning · each leg a vector', ['2000–2300: 240°T 24.0 M · 2300–0200: 200°T 24.0 M', 'Added as vectors: 220°T 45.1 M from the fix, not 48 M'],
                  60, paths=[arr(F, D1, 'ink', 5), arr(D1, D2, 'ink', 5), line(F, D2, 'course', 5, '14 10')], spots=[{'x': D2[0], 'z': D2[1], 'label': 'DR'}],
                  texts=[t(40, -40, '2000 fix'), tp(D1, '2300', None, -60, -30), tp(D2, '0200', None, -90, 0), tp(((F[0] + D1[0]) / 2, (F[1] + D1[1]) / 2), '240°T 24.0 M', None, -40, -50),
                         tp(((D1[0] + D2[0]) / 2, (D1[1] + D2[1]) / 2), '200°T 24.0 M', None, -120, 0), tp(((F[0] + D2[0]) / 2, (F[1] + D2[1]) / 2), '220°T 45.1 M', 'accent', 110, 20)],
                  fit=[{'x': -380, 'z': -60}, {'x': 120, 'z': 400}])
    # 3, 4 leeway
    def lee(hdg, port):
        wt = hdg + 5 if port else hdg - 5
        return plan(f"Leeway · {'port' if port else 'starboard'} tack", [f"Wind N, heading {hdg:03d}°T: {'port' if port else 'starboard'} tack, she slips to {'starboard' if port else 'port'}",
                    f"Water track = heading {'+' if port else '−'} leeway: {hdg:03d}° {'+' if port else '−'} 5° = {wt:03d}°T"],
                    70, wind=0, boats=[boat(0, 0, hdg, sail=True)], paths=[line((0, 0), ray(0, 0, hdg, 300), 'ink', 4, '14 10'), arr((0, 0), ray(0, 0, wt, 320), 'course', 5)],
                    texts=[tp(ray(0, 0, hdg - (8 if port else -8), 330), f'heading {hdg:03d}°'), tp(ray(0, 0, wt + (6 if port else -6), 390), f'water track {wt:03d}°', 'accent')],
                    fit=[{'x': -380 if not port else -120, 'z': -330}, {'x': 120 if not port else 380, 'z': 120}])
    out[3] = lee(50, True); out[4] = lee(310, False)
    # 5 EP, 1 M = 15
    k = 15.0; F = (0, 0); Hd = ray(0, 0, 250, 21 * k); Wt = ray(0, 0, 245, 21 * k)
    t1 = ray(*Wt, 160, 1.0 * k); t2 = ray(*t1, 165, 1.5 * k); t3 = ray(*t2, 170, 1.0 * k)
    out[5] = plan('Estimated position · leeway, then stream', ['Heading 250°T, wind NW on the starboard side: leeway 5° to port, water track 245°T 21.0 M', 'Then three hours of stream, 3.5 M toward 165°T: EP 236°T 21.9 M from the fix'],
                  60, paths=[line(F, Hd, 'ink', 3, '12 10'), arr(F, Wt, 'ink', 5), arr(Wt, t1, 'course', 5), arr(t1, t2, 'course', 5), arr(t2, t3, 'course', 5), line(F, t3, 'red', 4, '8 8')],
                  circles=[{'x': t3[0], 'z': t3[1], 'r': 8, 'c': 'red', 'dash': '0', 'fill': '#e0251b'}],
                  texts=[t(40, -40, '0000 fix'), tp(ray(0, 0, 252, 13 * k), 'heading 250°T', None, 0, -50), tp(ray(0, 0, 243, 13 * k), 'water track 245°T 21.0 M', None, 30, 50),
                         tp(t2, 'stream 3.5 M, 165°T', 'accent', 160, 0), tp(t3, '0300 EP: 236°T 21.9 M', 'red', 0, 70)],
                  fit=[{'x': -400, 'z': -60}, {'x': 80, 'z': 260}])
    # 6 course to steer, 1 M = 8
    k = 8.0; A = (0, 0); B = EN(0, 41.57, k); S = EN(6, 0, k)
    bSB = (math.degrees(math.atan2(B[0] - S[0], -(B[1] - S[1]))) + 360) % 360
    out[6] = plan('Course to steer · one triangle', ['Lay off the whole crossing’s stream from A: 6 M east', 'From its end swing 7 kn × 6 h = 42 M to the track: steer 352°T'],
                  60, paths=[arr(A, B, 'ink', 4), arr(A, S, 'course', 5), arr(S, B, 'red', 5), poly(arcpts(S, 42 * k, bSB - 5, bSB + 5), 'ink', 3, '8 8')],
                  texts=[tp(A, 'A', None, -40, 20, pill=False, size=34), tp(B, 'B', None, -40, 10, pill=False, size=34), tp(((A[0] + B[0]) / 2, (A[1] + B[1]) / 2), 'track 000°T 41.6 M', None, -150, 0),
                         tp(S, 'stream 6 M east', 'accent', 60, 50), tp(((S[0] + B[0]) / 2, (S[1] + B[1]) / 2), 'water 42 M: steer 352°T', 'red', 170, 60)],
                  fit=[{'x': -260, 'z': B[1] - 40}, {'x': 260, 'z': 80}])
    # 8 meeting the sister, 1 M = 10
    k = 10.0; Yp = (0, 0); Sp = EN(24, 0, k); Mt = EN(24, -13.86, k)
    out[8] = plan('Meeting a vessel · keep her bearing steady', ['Sister 24 M east, 180°T 5 kn · you 10 kn', 'sin A = 5 × sin 90° ÷ 10: A = 30°, steer 120°T · meet in 2 h 46 min'],
                  60, paths=[line(Yp, Sp, 'ink', 3, '12 10'), arr(Sp, Mt, 'ink', 5), arr(Yp, Mt, 'course', 5), poly(arcpts(Yp, 70, 90, 120), 'ink', 3)],
                  boats=[boat(0, 0, 120), boat(Sp[0], Sp[1], 180, False, label='Sister', bearing=False)],
                  texts=[t(120, -40, '24 M, bearing 090°T'), tp(Sp, '180°T 5 kn', None, 110, 70), tp(((Yp[0] + Mt[0]) / 2, (Yp[1] + Mt[1]) / 2), '120°T 10 kn', 'accent', -40, 60),
                         tp(Mt, 'meet in 2 h 46 min', 'red', 0, 60), t(95, 40, '30°', pill=False)],
                  fit=[{'x': -80, 'z': -100}, {'x': 330, 'z': 220}])
    # 9 cross-track error, 1 M = 8
    k = 8.0; A = (0, 0); B = EN(128, 0, k); Bt = EN(80, 4, k)
    out[9] = plan('1 in 60 · back to the line', ['XTE 4.0 M after 80 M: 4 × 60 ÷ 80 = 3° off track', '48 M to go: 4 × 60 ÷ 48 = 5° more · alter 3° + 5° = 8° to starboard for B'],
                  60, paths=[line(A, B, 'ink', 4, '14 10'), line(A, Bt, 'red', 4), arr(Bt, B, 'course', 5)], boats=[boat(Bt[0], Bt[1], 87)],
                  
                  texts=[tp(A, 'A', None, -30, 10, pill=False, size=34), tp(B, 'B', None, 30, 10, pill=False, size=34), t(320, 40, '80 M run'), t(840, 40, '48 M to go'),
                         t(170, -60, '3° off track', 'red'), t(860, -70, 'alter 8° to starboard', 'accent'), t(640, -110, 'XTE 4 M', 'red')],
                  fit=[{'x': -60, 'z': -140}, {'x': 1080, 'z': 80}])
    # 10 the current wrong by 30°, 1 M = 30
    k = 30.0; Wd = (0, 0); EP = ray(0, 0, 180, 8 * k); Fx = ray(0, 0, 210, 8 * k)
    gap = (math.degrees(math.atan2(Fx[0] - EP[0], -(Fx[1] - EP[1]))) + 360) % 360; dist = math.dist(Fx, EP) / k
    out[10] = plan('Where the error puts you', ['Current used 180° 0.8 kn, real 210° 0.8 kn, for 10 h: 8 M each', f'The fix lies {dist:.1f} M toward {gap:.0f}° from the EP'],
                   60, paths=[arr(P(330, 0), Wd, 'ink', 4), arr(Wd, EP, 'course', 5), arr(Wd, Fx, 'red', 5), line(EP, Fx, 'ink', 4, '10 8')],
                   spots=[{'x': EP[0], 'z': EP[1], 'label': 'EP'}],
                   texts=[t(180, -40, 'water track 270°T'), tp(ray(0, 0, 180, 4 * k), 'used 180°', 'accent', 100, 0), tp(ray(0, 0, 210, 4 * k), 'real 210°', 'red', -110, 0),
                          tp(Fx, 'fix', None, -60, 40), tp(((EP[0] + Fx[0]) / 2, (EP[1] + Fx[1]) / 2), '4.1 M toward 285°', None, 0, 60)],
                   fit=[{'x': -260, 'z': -80}, {'x': 360, 'z': 320}])
    print('eperr', round(gap, 1), round(dist, 2))
    # 11 current from two fixes, 1 M = 25
    k = 25.0; F0 = (0, 0); DR = ray(0, 0, 90, 18 * k); F6 = ray(0, 0, 100, 20 * k)
    cs = (math.degrees(math.atan2(F6[0] - DR[0], -(F6[1] - DR[1]))) + 360) % 360; cd = math.dist(F6, DR) / k
    out[11] = plan('Current from two fixes', ['Water 090°T 18.0 M by the log · ground 100°T 20.0 M, fix to fix in 3 h', f'Current = ground − water: {cd:.1f} M toward {cs:.0f}°T, {cd / 3:.1f} kn'],
                   60, paths=[arr(F0, DR, 'ink', 5), arr(F0, F6, 'red', 5), arr(DR, F6, 'course', 6)], spots=[{'x': DR[0], 'z': DR[1], 'label': 'DR'}],
                   texts=[t(0, -40, '0300 fix'), tp(F6, '0600 fix', None, 0, 50), t(225, -40, 'water 090°T 18.0 M'), t(130, 90, 'ground 100°T 20.0 M', 'red'), tp(((DR[0] + F6[0]) / 2, (DR[1] + F6[1]) / 2), 'current 154°T 3.9 M', 'accent', 175, -10)],
                   fit=[{'x': -40, 'z': -80}, {'x': 720, 'z': 140}])
    print('current', round(cs, 1), round(cd, 2))
    # 13 VMG, 1 kn = 60
    k = 60.0; O = (0, 0); Wv = ray(0, 0, 48, 7 * k); Pv = (0, Wv[1])
    out[13] = plan('Velocity made good · beating', ['7.0 kn through the water, 48° off the course to the mark', 'VMG = 7.0 × cos 48° = 4.7 kn: 80 M takes 17 h 05, from 0600 to 2305'],
                   70, wind=0, paths=[line(O, (0, -560), 'ink', 3, '12 10'), arr(O, Wv, 'course', 6), arr(O, Pv, 'red', 7), line(Wv, Pv, 'ink', 3, '8 8'), poly(arcpts(O, 90, 0, 48), 'ink', 3)],
                   boats=[boat(0, 0, 43, sail=True)],
                   texts=[t(0, -600, 'to the mark, 80 M'), tp(Wv, '7.0 kn', 'accent', 60, 20), tp(Pv, 'VMG 4.7 kn', 'red', -120, 0), t(55, -125, '48°', pill=False)],
                   fit=[{'x': -260, 'z': -620}, {'x': 420, 'z': 120}])
    # 14 aiming off for a low coast, 1 M = 6
    k = 6.0; S0 = (0, 0); Hh = EN(96, 0, k); Aim = EN(96, 5, k); St = ray(0, 0, 92, 96 * k)
    out[14] = plan('Aim off · know which way to turn', ['Current N 0.5 kn for 16 h at 6 kn: 8 M of set, and you want 5 M north', 'Steer 3 × 60 ÷ 96 = 2° south of the direct line, 092°T: arrive north, turn south'],
                   60, land=[[P(600, -260), P(590, -100), P(598, 60), P(592, 200), P(760, 200), P(760, -260)]],
                   paths=[line(S0, Hh, 'ink', 3, '12 10'), line(S0, St, 'ink', 3, '4 8'), arr(S0, Aim, 'course', 5), arr(Aim, P(Hh[0] - 10, Hh[1] - 6), 'red', 5)],
                   boats=[boat(0, 0, 92)], circles=[{'x': Hh[0], 'z': Hh[1], 'r': 9, 'c': 'red', 'dash': '0', 'fill': '#e0251b'}],
                   texts=[t(300, 40, 'direct 090°T, 96 M'), tp(St, 'steer 092°T', None, -110, 30), tp(Aim, '5 M north', 'accent', -80, -40), tp(Hh, 'Harbour', None, 90, 30), tp(Aim, 'turn south', 'red', 90, 20)],
                   fit=[{'x': -60, 'z': -120}, {'x': 760, 'z': 120}])
    # 15 the fuel curve (svg)
    def curve():
        x0, y0, x1, y1 = 140, 560, 1180, 80
        X = lambda kn: x0 + (kn - 6) / 16 * (x1 - x0); Yl = lambda lpm: y0 - lpm / 15 * (y0 - y1)
        b = ''
        for v in range(0, 16, 5): b += sline(x0, Yl(v), x1, Yl(v), 'var(--line)', 2) + stext(x0 - 14, Yl(v) + 9, f'{v}', 24, 700, 'var(--muted)', 'end')
        for kn in (8, 12, 16, 20): b += sline(X(kn), y0, X(kn), y1, 'var(--line)', 2) + stext(X(kn), y0 + 34, f'{kn} kn', 24, 700, 'var(--ink)')
        b += stext(x0 - 14, y1 - 22, 'l/M', 24, 700, 'var(--muted)', 'end')
        pts = [(8, 5.0), (12, 9.2), (16, 13.1), (20, 11.0)]
        b += '<path d="' + ' '.join(f'{"M" if i == 0 else "L"}{r1(X(a))} {r1(Yl(c))}' for i, (a, c) in enumerate(pts)) + f'" fill="none" stroke="var(--ink)" stroke-width="5"/>'
        for (a, c), lab, kind, (ox, oy) in zip(pts, ('8 kn 40 l/h: 5.0 l/M', '12 kn 110 l/h: 9.2 l/M', '16 kn 210 l/h: 13.1 l/M', '20 kn 220 l/h: 11.0 l/M'), ('light', 'accent', 'red', 'light'), ((150, 45), (160, 45), (0, -40), (-40, 55))):
            b += f'<circle cx="{r1(X(a))}" cy="{r1(Yl(c))}" r="10" fill="var(--ink)"/>' + spill(X(a) + ox, Yl(c) + oy, lab, kind, 24)
        return svg_doc(b, 'Range from the fuel curve · litres per mile', ['Litres per mile = l/h ÷ speed: lowest slow, worst at the hump, better again on the plane', 'Usable 2000 l: 18.2 h and 218 M at 12 kn · 9.1 h and 182 M at 20 kn'])
    out[15] = curve()
    # 16 fast first, then slow (svg)
    def fastslow():
        x0, x1 = 80, 1200; X = lambda m: x0 + m / 200 * (x1 - x0)
        b = stext(x0, 120, 'Distance, 200 M', 26, 700, 'var(--muted)', 'start')
        b += f'<rect x="{X(0)}" y="140" width="{r1(X(150) - X(0))}" height="80" fill="#e8231a"/><rect x="{r1(X(150))}" y="140" width="{r1(X(200) - X(150))}" height="80" fill="var(--accent)"/>'
        b += stext((X(0) + X(150)) / 2, 192, '150 M at 15 kn · 10 h', 28, 700, '#fff') + stext((X(150) + X(200)) / 2, 192, '50 M at 8 kn', 26, 700, '#fff')
        b += stext(x0, 300, 'Fuel, 1800 l usable', 26, 700, 'var(--muted)', 'start'); F = lambda l: x0 + l / 1800 * (x1 - x0)
        b += f'<rect x="{F(0)}" y="320" width="{r1(F(1500) - F(0))}" height="80" fill="#e8231a" opacity=".85"/><rect x="{r1(F(1500))}" y="320" width="{r1(F(1800) - F(1500))}" height="80" fill="var(--accent)" opacity=".85"/>'
        b += stext((F(0) + F(1500)) / 2, 372, '150 l/h × 10 h = 1500 l', 28, 700, '#fff') + stext((F(1500) + F(1800)) / 2, 372, '300 l', 26, 700, '#fff')
        b += spill(640, 480, 'all at 15 kn: 1800 l lasts 12 h, 180 M', 'red', 26)
        return svg_doc(b, 'Fast first, then slow', ['x h at 15 kn: 150x + 48 × (200 − 15x) ÷ 8 = 1800, so x = 10 h', '150 M fast with 1500 l, then 50 M at 8 kn with 300 l: arrive on the reserve'])
    out[16] = fastslow()
    return out

if __name__ == '__main__':
    arts = sys.argv[1:] or ['charts', 'compass', 'dr']
    for a in arts:
        res = {'charts': charts, 'compass': compass, 'dr': dr}[a]()
        d = os.path.join(ARTS, a)
        for n, spec in res.items():
            json.dump(spec, open(os.path.join(d, f'{n}-plan.json'), 'w'), ensure_ascii=False, indent=1)
        print(a, sorted(res))
