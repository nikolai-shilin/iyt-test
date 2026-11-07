# The schematics of the Yachtmaster Offshore seamanship figures: writes
# docs/design/figure-style/articles/yachtmaster-offshore/seamanship/<n>-plan.json, read by article-figures.html.
# A plan is a figure-schematic.js spec ({sch: ...}) where a plan view fits (lines, swinging room, two anchors, berthing,
# the tow's lights, heaving to), else a drawn SVG in the same style: 1280 x 800, theme tokens, Carlito, the key along
# the bottom. SVG text is translated on the page by exact match through ru.json, so every text node is a whole
# string; pills are sized for the longer of the English and the Russian (RU below). Figure 12 (night orders for the
# tow) has no plan: a list of orders has no plan view.
#   python3 docs/design/blender/art_yof_seamanship_plans.py           write the plans
#   python3 docs/design/blender/art_yof_seamanship_plans.py --ru      print RU (merged into ru.json)
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ADIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'seamanship')
W, H = 1280, 800
RED, GREEN, YEL, BLUE, ORANGE = '#e0251b', '#1aa34a', '#e0b400', 'var(--accent)', '#ff8a3d'

RU = {}
def ru(d): RU.update(d)

def esc(s): return str(s).replace('&', '&amp;').replace('<', '&lt;')
def txt(x, y, s, size=26, w=700, fill='var(--muted)', a='middle'):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{a}">{esc(s)}</text>'
def pill(x, y, text, kind='light', size=26, align='center'):
    n = max(len(text), len(RU.get(text, text)))
    w, h = n * size * 0.56 + size * 1.4, size * 1.7
    x = x + w / 2 if align == 'left' else x - w / 2 if align == 'right' else x
    fill = {'accent': BLUE, 'red': '#e8231a', 'green': GREEN, 'yellow': '#d9a400', 'ink': 'var(--ink)'}.get(kind, 'var(--bg)')
    ink = 'var(--ink)' if kind == 'light' else ('var(--bg)' if kind == 'ink' else '#fff')
    stroke = 'var(--tag-line)' if kind == 'light' else fill
    return f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>' + txt(x, y + size * 0.36, text, size, 700, ink)
def line(x1, y1, x2, y2, c='var(--ink)', w=5, dash=None):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w}" stroke-linecap="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
def path(d, c='var(--ink)', w=5, dash=None, fill='none', extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + f' {extra}/>'
def arrow(x1, y1, x2, y2, c='var(--ink)', w=5, h=18, dash=None):
    a = math.atan2(y2 - y1, x2 - x1); p1 = (x2 - h * math.cos(a - .5), y2 - h * math.sin(a - .5)); p2 = (x2 - h * math.cos(a + .5), y2 - h * math.sin(a + .5))
    return line(x1, y1, x2, y2, c, w, dash) + f'<path d="M{x2:.1f} {y2:.1f} L{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} Z" fill="{c}"/>'
def rect(x, y, w, h, fill='var(--bg)', stroke='var(--ink)', sw=4, rx=10, extra=''):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
def circle(x, y, r, fill='var(--bg)', stroke='var(--ink)', sw=4, dash=None):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
def anchor(x, y, s=1.0):
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({s})" fill="none" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"><circle cx="0" cy="-30" r="8"/><line x1="0" y1="-22" x2="0" y2="28"/><line x1="-16" y1="-10" x2="16" y2="-10"/><path d="M-26 8 C -24 26 -12 32 0 32 C 12 32 24 26 26 8"/><path d="M-30 14 L-26 6 L-18 12 M30 14 L26 6 L18 12"/></g>'
def svg(n, body, title, key):
    keyH = 40 + 40 * len(key) + 24
    s = f'<svg xmlns="http://www.w3.org/2000/svg" id="yof-sea-{n}" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="{W}" height="{H}" fill="var(--bg)"/>'
    s += body + f'<rect x="0" y="{H - keyH}" width="{W}" height="{keyH}" fill="var(--band)"/>' + txt(30, H - keyH + 40, title, 30, 700, 'var(--ink)', 'start')
    for i, k in enumerate(key): s += txt(30, H - keyH + 80 + 40 * i, '·', 27, 400, 'var(--ink)', 'start') + txt(44, H - keyH + 80 + 40 * i, k, 27, 400, 'var(--ink)', 'start')
    return {'noScale': True, 'svg': s + '</svg>'}
def T(x, z, text, kind='light', **o): return {'x': round(x, 1), 'z': round(z, 1), 'text': text, 'kind': kind, **o}
def fwd(h): return math.sin(math.radians(h)), math.cos(math.radians(h))
def bez(p0, p1, p2, p3=None, n=10):
    out = []
    for i in range(1, n + 1):
        t = i / n; u = 1 - t
        if p3 is None: out.append([u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]])
        else: out.append([u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0], u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]])
    return out

# ------------------------------------------------------------------------------------------------ 1 tow line
def p1():
    x0, X = 330, lambda t: 330 + t * 140
    rows = [('new: breaks at', 6.0, 'var(--muted)'), ('wet × 0.85', 5.1, BLUE), ('bowline × 0.6', 3.06, ORANGE), ('÷ safety factor 5', 0.612, GREEN)]
    b = ''
    for i, (lab, v, col) in enumerate(rows):
        y = 70 + i * 120
        b += txt(300, y + 46, lab, 30, 700, 'var(--ink)', 'end') + rect(x0, y, X(v) - x0, 70, col, 'none', 0, 10, 'opacity=".85"')
        b += txt(X(v) + 18, y + 47, f'{v:.2f} t'.replace('6.00', '6.0').replace('5.10', '5.1').replace('0.61', '≈ 0.6'), 32, 700, 'var(--ink)', 'start')
    b += pill(X(0.612) + 230, 70 + 3 * 120 + 35, 'working load', 'green', 26, 'left')
    ru({'new: breaks at': 'новый: разрыв', 'wet × 0.85': 'мокрый × 0,85', 'bowline × 0.6': 'беседочный × 0,6', '÷ safety factor 5': '÷ запас прочности 5',
        '6.0 t': '6,0 т', '5.1 t': '5,1 т', '3.06 t': '3,06 т', '≈ 0.6 t': '≈ 0,6 т', 'working load': 'рабочая нагрузка',
        'Working load of a 16 mm nylon tow line': 'Рабочая нагрузка нейлонового буксира 16 мм',
        'Each loss multiplies: 6.0 × 0.85 × 0.6 = 3.06 t left in the knotted wet line': 'Потери перемножаются: 6,0 × 0,85 × 0,6 = 3,06 т у мокрого троса с узлом',
        'Divide by a safety factor of 5: work it at about 0.6 t; a splice keeps 90 %': 'Делим на запас прочности 5: работать около 0,6 т; сплесень сохраняет 90 %'})
    return svg(1, b, 'Working load of a 16 mm nylon tow line', ['Each loss multiplies: 6.0 × 0.85 × 0.6 = 3.06 t left in the knotted wet line',
                                                              'Divide by a safety factor of 5: work it at about 0.6 t; a splice keeps 90 %'])

# ------------------------------------------------------------------------------------------------ 2 doubled lines
def p2():
    cl = (6.5, -1.0); A = (12.0, -3.5); B = (18.4, -3.5)
    sch = {'padPx': 60, 'trueScale': True, 'minMpp': 0.01, 'title': 'Doubled lines in a surge', 'key': ['Line A 6 m, line B 12 m, both just taut: stiffness ∝ 1 ÷ length, A is twice as stiff', 'A takes two-thirds of every snatch: make doubled lines the same length'],
           'quays': [{'x1': -10, 'z1': -9, 'x2': 24, 'z2': -2.7}],
           'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 90, 'noHeading': True, 'L': 14}],
           'circles': [{'x': A[0], 'z': A[1], 'r': 0.35, 'c': 'ink', 'dash': '1 0', 'fill': 'var(--ink)'}, {'x': B[0], 'z': B[1], 'r': 0.35, 'c': 'ink', 'dash': '1 0', 'fill': 'var(--ink)'}],
           'paths': [{'pts': [list(cl), list(A)], 'c': 'red', 'w': 7}, {'pts': [list(cl), list(B)], 'c': 'line', 'w': 7}],
           'texts': [T(10.5, 0.6, 'A 6 m: two-thirds', 'red'), T(18.0, -1.2, 'B 12 m: one-third'), T(4, -5.6, 'QUAY', pill=False, size=30)],
           'fit': [{'x': -8, 'z': -7}, {'x': 22, 'z': 4}]}
    ru({'Doubled lines in a surge': 'Удвоенные швартовы при тягуне',
        'Line A 6 m, line B 12 m, both just taut: stiffness ∝ 1 ÷ length, A is twice as stiff': 'Конец A 6 м, конец B 12 м, оба чуть натянуты: жёсткость ∝ 1 ÷ длина, A вдвое жёстче',
        'A takes two-thirds of every snatch: make doubled lines the same length': 'A берёт две трети каждого рывка: удвоенные концы делайте одной длины',
        'A 6 m: two-thirds': 'A 6 м: две трети', 'B 12 m: one-third': 'B 12 м: треть', 'QUAY': 'ПРИЧАЛ'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 3 snubber
def p3():
    b = '<rect x="0" y="380" width="1280" height="236" fill="rgba(60,140,190,.14)"/><line x1="0" y1="380" x2="1280" y2="380" stroke="#3c8cbe" stroke-width="5"/>'
    b += '<path d="M120 210 L760 210 C 820 214 860 230 880 250 L 820 380 L 700 470 L 120 470 Z" fill="var(--ink)"/>'
    b += '<rect x="700" y="196" width="190" height="20" rx="6" fill="#9aa3ab"/><circle cx="880" cy="206" r="20" fill="#c9ced3" stroke="var(--ink)" stroke-width="4"/>'
    b += '<rect x="520" y="150" width="70" height="60" rx="10" fill="#9aa3ab" stroke="var(--ink)" stroke-width="4"/><circle cx="555" cy="150" r="34" fill="#c9ced3" stroke="var(--ink)" stroke-width="5"/>'
    b += '<rect x="400" y="196" width="80" height="14" rx="5" fill="#c9ced3" stroke="var(--ink)" stroke-width="3"/>'
    # chain: from the gypsy over the roller, hanging in a slack bight below the hook, then on down to the anchor
    b += path('M 555 116 C 640 110 640 196 720 196 C 800 196 850 190 880 188 C 930 200 935 420 980 470 C 1000 480 1015 470 1012 440 L 1060 530 L 1130 600', '#4a4f55', 9, '12 6')
    b += path('M 440 200 C 600 200 800 222 896 230 C 940 270 990 360 1008 432', '#8a6a3a', 10)
    b += '<path d="M 998 426 l 24 10 l -8 22 z" fill="var(--accent)" stroke="var(--ink)" stroke-width="3"/>'
    b += pill(330, 130, 'made fast on a cleat', 'accent', 26) + pill(1100, 330, 'nylon on a chain hook', 'light', 26)
    b += pill(850, 520, 'chain slack below the hook', 'light', 24) + pill(1150, 590, 'to the anchor', 'red', 24)
    ru({'made fast on a cleat': 'закреплён на утке', 'nylon on a chain hook': 'нейлон на гаке за цепь', 'chain slack below the hook': 'цепь провисла ниже гака',
        'to the anchor': 'к якорю', 'Snubber rigged · 8 m of water': 'Демпфер заведён · глубина 8 м',
        'Nylon hooked to the chain below the roller, made fast on a cleat': 'Нейлон на гаке за цепь ниже роульса, закреплён на утке',
        'The chain behind the hook hangs slack: the snubber spares the windlass, not the chain': 'Цепь за гаком провисла: демпфер бережёт брашпиль, а не цепь'})
    return svg(3, b, 'Snubber rigged · 8 m of water', ['Nylon hooked to the chain below the roller, made fast on a cleat',
                                                      'The chain behind the hook hangs slack: the snubber spares the windlass, not the chain'])

# ------------------------------------------------------------------------------------------------ 4 scope
def p4():
    sea, bed = 190, 500
    b = f'<rect x="0" y="{sea}" width="1280" height="{bed - sea}" fill="rgba(60,140,190,.14)"/><line x1="0" y1="{sea}" x2="1280" y2="{sea}" stroke="#3c8cbe" stroke-width="5"/>'
    b += f'<rect x="0" y="{bed}" width="1280" height="{560 - bed + 40}" fill="#e3d6b4"/><line x1="0" y1="{bed}" x2="1280" y2="{bed}" stroke="#8a7650" stroke-width="5"/>'
    hx, L, bowY = 1040, 150, sea - 34
    b += f'<path d="M{hx} {bowY} L{hx + L} {bowY + 10} L{hx + L - 8} {sea + 22} L{hx + L * 0.12} {sea + 26} Z" fill="var(--ink)"/><line x1="{hx + L * 0.42}" y1="{bowY}" x2="{hx + L * 0.42}" y2="{bowY - 130}" stroke="var(--ink)" stroke-width="6"/>'
    b += circle(hx, bowY, 9, BLUE, 'var(--bg)', 3)
    # nylon from the roller to the join, then the chain's catenary to the bottom and along it to the anchor
    jx, jy = 640, 380
    b += path(f'M{hx} {bowY} C {hx - 150} {bowY + 70} {jx + 160} {jy - 50} {jx} {jy}', '#c9b98e', 9)
    b += path(f'M{jx} {jy} C {jx - 90} {jy + 60} {jx - 200} {bed - 8} {jx - 300} {bed - 8} L 130 {bed - 8}', '#4a4f55', 9, '12 6')
    b += circle(jx, jy, 9, 'var(--bg)', 'var(--ink)', 4) + anchor(110, bed - 34, 1.2)
    b += line(hx + L + 50, sea, hx + L + 50, bed, 'var(--ink)', 4) + pill(hx + L + 50 - 70, (sea + bed) / 2, 'depth 18 m', 'light', 24)
    b += line(hx - 46, bowY, hx - 46, sea, 'var(--ink)', 4) + pill(hx - 46, bowY - 36, 'bow 2 m', 'light', 22)
    b += pill(880, 250, '60 m nylon', 'light', 26) + pill(420, 440, '80 m chain', 'accent', 26) + pill(jx + 10, jy + 54, 'join', 'light', 22)
    b += txt(40, 80, '(18 + 2) × 7 = 140 m', 40, 700, 'var(--ink)', 'start')
    ru({'depth 18 m': 'глубина 18 м', 'bow 2 m': 'нос 2 м', '60 m nylon': '60 м нейлона', '80 m chain': '80 м цепи', 'join': 'соединение',
        'Scope for a gale · chain and rope (depth drawn deeper to read)': 'Длина каната на шторм · цепь с тросом (глубина преувеличена)',
        'Measured from the bow roller: depth 18 m + roller 2 m, times 7': 'Считают от роульса: глубина 18 м + роульс 2 м, умножить на 7',
        '80 m of chain on the bottom, 60 m of nylon up to the bow: 140 m': '80 м цепи по дну, 60 м нейлона до носа: 140 м'})
    return svg(4, b, 'Scope for a gale · chain and rope (depth drawn deeper to read)', ['Measured from the bow roller: depth 18 m + roller 2 m, times 7',
                                                                                       '80 m of chain on the bottom, 60 m of nylon up to the bow: 140 m'])

# ------------------------------------------------------------------------------------------------ 5 room to swing
def p5():
    A2 = (133, 8)
    sch = {'padPx': 50, 'trueScale': True, 'title': 'Room to swing', 'key': ['Radius = chain along the bottom + boat: √(60² − 12²) ≈ 59 m, + 24 m = 83 m', 'Boats lying differently: add both radii, 83 m + 50 m apart'],
           'circles': [{'x': 0, 'z': 0, 'r': 83}, {'x': A2[0], 'z': A2[1], 'r': 50, 'c': 'red'}],
           'anchors': [{'x': 0, 'z': 0, 's': 0.9}, {'x': A2[0], 'z': A2[1], 's': 0.9}],
           'boats': [{'you': True, 'x': 0, 'z': 71, 'hdg': 0, 'noHeading': True, 'L': 24}, {'x': A2[0] - 38.5, 'z': A2[1], 'hdg': 90, 'noHeading': True, 'L': 17, 'label': 'motor yacht', 'bearing': False}],
           'paths': [{'pts': [[0, 3], [0, 59]], 'c': 'ink', 'w': 4, 'dash': '10 8'}, {'pts': [[A2[0] - 30, A2[1]], [A2[0] - 3, A2[1]]], 'c': 'ink', 'w': 4, 'dash': '10 8'}],
           'dims': [{'a': [-20, 0], 'b': [-20, 59], 'text': 'chain 59 m', 'off': 0}, {'a': [-20, 59], 'b': [-20, 83], 'text': '24 m', 'off': 0}],
           'texts': [T(0, -98, 'radius 83 m', 'accent'), T(A2[0], A2[1] - 64, 'radius 50 m', 'red')],
           'fit': [{'x': -85, 'z': -110}, {'x': 185, 'z': 90}]}
    ru({'Room to swing': 'Круг разворота', 'Radius = chain along the bottom + boat: √(60² − 12²) ≈ 59 m, + 24 m = 83 m': 'Радиус = цепь по дну + корпус: √(60² − 12²) ≈ 59 м, + 24 м = 83 м',
        'Boats lying differently: add both radii, 83 m + 50 m apart': 'Яхты стоят по-разному: сложите радиусы, 83 м + 50 м между якорями',
        'motor yacht': 'моторная яхта', 'chain 59 m': 'цепь 59 м', '24 m': '24 м', 'radius 83 m': 'радиус 83 м', 'radius 50 m': 'радиус 50 м'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 6 anchor watch
def p6():
    P = lambda x, y: [x - 96, y - 52]
    arc = [P(62, 98)] + [P(*q) for q in bez((62, 98), (96, 124), (130, 98))] + [P(*q) for q in bez((130, 98), (100, 120), (70, 102))]
    drag = [P(70, 102), P(176, 150), P(236, 178)]
    sch = {'padPx': 60, 'title': 'Anchor watch · plotter, 0200', 'key': ['Track since 2200: an arc round the anchor is swinging', 'Since the wind shifted at 0130 a straight line downwind: dragging'],
           'anchors': [{'x': 0, 'z': 0}], 'circles': [{'x': 0, 'z': 0, 'r': 60, 'c': 'red'}],
           'paths': [{'pts': arc, 'c': 'accent', 'w': 7}, {'pts': drag, 'c': 'red', 'w': 7}],
           'boats': [{'you': True, 'x': 144, 'z': 128, 'hdg': 300, 'noHeading': True}],
           'texts': [T(-34, 92, 'arc: swinging', 'accent'), T(118, 70, 'straight: dragging', 'red'), T(0, -78, 'alarm circle')],
           'fit': [{'x': -70, 'z': -90}, {'x': 170, 'z': 175}]}
    ru({'Anchor watch · plotter, 0200': 'Якорная вахта · плоттер, 0200', 'Track since 2200: an arc round the anchor is swinging': 'След с 2200: дуга вокруг якоря — разворот',
        'Since the wind shifted at 0130 a straight line downwind: dragging': 'После смены ветра в 0130 прямая под ветер: якорь ползёт',
        'arc: swinging': 'дуга: разворот', 'straight: dragging': 'прямая: ползёт', 'alarm circle': 'круг тревоги'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 7 two anchors in a V
def p7():
    o = (240, 60); P = lambda x, y: [round(x - o[0], 1), round(y - o[1], 1)]
    land = [P(0, 0), P(70, 0)] + [P(*q) for q in bez((70, 0), (95, 70), (90, 130), (120, 170))] + [P(*q) for q in bez((120, 170), (150, 190), (200, 195), (240, 200))] + [P(0, 200)]
    bow = [round(fwd(247)[0] * 7, 1), round(-fwd(247)[1] * 7, 1)]
    sch = {'padPx': 50, 'wind': 225, 'title': 'Two anchors in a V', 'key': ['Gale SW 8 forecast to veer W: lay an anchor towards each', 'Both ahead, across the shift: each takes its share as she swings'],
           'land': [land], 'anchors': [{'x': -57, 'z': 48, 'label': 'SW'}, {'x': -74, 'z': 6, 'label': 'W'}],
           'paths': [{'pts': [bow, [-57, 44]], 'c': 'ink', 'w': 4, 'dash': '10 8'}, {'pts': [bow, [-72, 4]], 'c': 'ink', 'w': 4, 'dash': '10 8'}],
           'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 247}],
           'texts': [T(-190, 40, 'LAND', pill=False, size=32), T(-100, -40, 'veering W', 'red')],
           'fit': [{'x': -150, 'z': -70}, {'x': 40, 'z': 110}]}
    ru({'Two anchors in a V': 'Два якоря вилкой', 'Gale SW 8 forecast to veer W: lay an anchor towards each': 'Шторм SW 8, по прогнозу зайдёт к W: по якорю на каждый',
        'Both ahead, across the shift: each takes its share as she swings': 'Оба впереди, поперёк захода: каждый берёт свою долю при развороте',
        'LAND': 'БЕРЕГ', 'veering W': 'заходит к W'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 8 Bahamian moor
def p8():
    sch = {'padPx': 50, 'title': 'Bahamian moor · a reversing stream', 'key': ['Let go up-stream, drop back twice the scope, let go again, heave back to the middle', 'A swivel joins the rodes below the bow · weigh the slack anchor first'],
           'land': [[[-150, -110], [150, -110], [150, -55], [-150, -55]], [[-150, 55], [150, 55], [150, 110], [-150, 110]]],
           'anchors': [{'x': -80, 'z': 0, 'label': 'first'}, {'x': 80, 'z': 0, 'label': 'second'}],
           'paths': [{'pts': [[-8, 0], [-77, 0]], 'c': 'ink', 'w': 4, 'dash': '10 8'}, {'pts': [[-8, 2], [77, 2]], 'c': 'ink', 'w': 4, 'dash': '10 8'},
                     {'pts': [[-110, 40], [-55, 40]], 'c': 'accent', 'w': 7, 'arrow': True}, {'pts': [[110, -40], [55, -40]], 'c': 'accent', 'w': 7, 'arrow': True, 'dash': '12 10'}],
           'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 270, 'noHeading': True}],
           'texts': [T(-82, 54, 'flood', 'accent'), T(82, -54, 'ebb'), T(-14, -24, 'swivel'), T(0, -82, 'LAND', pill=False, size=30), T(0, 82, 'LAND', pill=False, size=30)],
           'fit': [{'x': -110, 'z': -90}, {'x': 110, 'z': 90}]}
    ru({'Bahamian moor · a reversing stream': 'Багамская постановка · реверсивное течение',
        'Let go up-stream, drop back twice the scope, let go again, heave back to the middle': 'Отдать выше по течению, сдать на двойную длину, отдать второй, подтянуться на середину',
        'A swivel joins the rodes below the bow · weigh the slack anchor first': 'Канаты сходятся на вертлюге под носом · первым выбирают слабый якорь',
        'first': 'первый', 'second': 'второй', 'flood': 'прилив', 'ebb': 'отлив', 'swivel': 'вертлюг', 'LAND': 'БЕРЕГ'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 9 springing off
def p9():
    h = 112; fx, fz = fwd(h)
    def at(a, s=0.0):   # a metres along her from amidships (+ forward), s to starboard
        return [round(fx * a + fz * s, 2), round(-(fz * a - fx * s), 2)]
    st_q = at(-6.2, -1.9); bow = at(6.8, 0)
    sch = {'padPx': 60, 'trueScale': True, 'minMpp': 0.01, 'title': 'Springing off · the bow swings out', 'key': ['Slow astern on the stern spring, a fender at the quarter: the stern holds on the quay', 'Bow line let go: the bow swings out; then ahead, slip the spring and go'],
           'quays': [{'x1': -14, 'z1': -13, 'x2': 16, 'z2': -5.0}],
           'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': h, 'noHeading': True, 'L': 14}],
           'circles': [{'x': 1.6, 'z': -5.6, 'r': 0.35, 'c': 'ink', 'dash': '1 0', 'fill': 'var(--ink)'}, {'x': st_q[0] + 0.2, 'z': -4.55, 'r': 0.45, 'c': 'ink', 'dash': '1 0', 'fill': '#1e2f55'}],
           'paths': [{'pts': [st_q, [1.6, -5.6]], 'c': 'line', 'w': 7},
                     {'pts': [bow, [bow[0] - 0.6, bow[1] - 2.4], [bow[0] - 2.4, bow[1] - 3.0]], 'c': 'line', 'w': 5, 'dash': '10 8'},
                     {'pts': [[bow[0] + 1.0, bow[1] - 0.8], [bow[0] + 2.4, bow[1] + 1.6], [bow[0] + 3.0, bow[1] + 4.0]], 'c': 'accent', 'w': 7, 'arrow': True}],
           'texts': [T(-2.0, -7.2, 'stern spring'), T(st_q[0] - 3.5, -1.0, 'fender aft', 'accent'), T(bow[0] - 1.0, bow[1] - 5.0, 'bow line: let go'),
                     T(bow[0] + 5.5, bow[1] + 3.0, 'bow swings out', 'accent'), T(at(-7.5)[0] + 1.0, at(-7.5)[1] + 3.6, 'slow astern'), T(1, -8.5, 'QUAY', pill=False, size=30)],
           'fit': [{'x': -12, 'z': -10}, {'x': 14, 'z': 10}]}
    ru({'Springing off · the bow swings out': 'Отход на шпринге · нос отходит',
        'Slow astern on the stern spring, a fender at the quarter: the stern holds on the quay': 'Малый назад на кормовом шпринге, кранец на раковине: корма держится у причала',
        'Bow line let go: the bow swings out; then ahead, slip the spring and go': 'Носовой отдан: нос отходит; затем вперёд, отдать шпринг и уходить',
        'stern spring': 'кормовой шпринг', 'fender aft': 'кранец на корме', 'bow line: let go': 'носовой: отдать', 'bow swings out': 'нос отходит',
        'slow astern': 'малый назад', 'QUAY': 'ПРИЧАЛ'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 10 twin screws
def p10():
    sch = {'padPx': 60, 'trueScale': True, 'minMpp': 0.01, 'title': 'Twin screws · walking her sideways', 'key': ['Starboard engine ahead, port astern: the stern swings to starboard', 'Bow thruster to starboard as well: bow and stern go together, she walks sideways'],
           'quays': [{'x1': 11, 'z1': -14, 'x2': 13.5, 'z2': 14}],
           'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 0, 'noHeading': True, 'L': 16}],
           'paths': [{'pts': [[1.1, 8.5], [1.1, 14.5]], 'c': 'green' if False else 'ink', 'w': 6, 'arrow': True},
                     {'pts': [[-1.1, 8.5], [-1.1, 2.5]], 'c': 'red', 'w': 6, 'arrow': True},
                     {'pts': [[-1.4, -5.5], [-6.5, -5.5]], 'c': 'ink', 'w': 6, 'arrow': True, 'dash': '10 8'},
                     {'pts': [[3.4, 0], [9.6, 0]], 'c': 'accent', 'w': 9, 'arrow': True}],
           'texts': [T(-7.0, 15.0, 'starboard ahead: wash aft'), T(-6.6, 4.5, 'port astern', 'red'), T(-7.0, -8.0, 'thruster to starboard'),
                     T(6.6, -3.0, 'walks sideways', 'accent'), T(14.8, 16.2, 'PONTOON', pill=False, size=26)],
           'fit': [{'x': -12, 'z': -12}, {'x': 15, 'z': 19}]}
    ru({'Twin screws · walking her sideways': 'Два винта · яхта идёт лагом', 'Starboard engine ahead, port astern: the stern swings to starboard': 'Правый вперёд, левый назад: корма уходит вправо',
        'Bow thruster to starboard as well: bow and stern go together, she walks sideways': 'Подруливающее тоже вправо: нос и корма идут вместе, яхта идёт лагом',
        'starboard ahead: wash aft': 'правый вперёд: струя назад', 'port astern': 'левый назад', 'thruster to starboard': 'подрулька вправо', 'walks sideways': 'идёт лагом', 'PONTOON': 'ПОНТОН'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 11 stern-to, crosswind
def p11():
    nb = [{'x': x, 'z': 8.6, 'hdg': 180, 'plain': True, 'L': 14} for x in (-13.2, -6.6, 6.6, 12.4, 18.2)]
    sch = {'padPx': 50, 'wind': 270, 'trueScale': True, 'title': 'Stern-to in a gusty crosswind', 'key': ['Gusts 26 kn on 24 m² of bow: 26² ÷ 60 × 24 ≈ 270 kgf; the 160 kgf thruster cannot hold it', 'Anchor upwind, chain snubbed: it holds the bow · the engines place the stern'],
           'quays': [{'x1': -22, 'z1': -14, 'x2': 26, 'z2': 0}],
           'boats': nb + [{'you': True, 'x': 0, 'z': 9.2, 'hdg': 180, 'noHeading': True, 'L': 16}],
           'anchors': [{'x': -26, 'z': 62}],
           'paths': [{'pts': [[0, 17.5], [-24, 58]], 'c': 'ink', 'w': 4, 'dash': '10 8'}, {'pts': [[-36, 12], [-17, 12]], 'c': 'red', 'w': 7, 'arrow': True}],
           'texts': [T(-27, 4, 'gusts 26 kn', 'red'), T(4, 44, 'anchor upwind, chain snubbed'), T(13, -7, 'QUAY', pill=False, size=30)],
           'fit': [{'x': -38, 'z': -12}, {'x': 24, 'z': 68}]}
    ru({'Stern-to in a gusty crosswind': 'Кормой в порывистый боковой ветер',
        'Gusts 26 kn on 24 m² of bow: 26² ÷ 60 × 24 ≈ 270 kgf; the 160 kgf thruster cannot hold it': 'Порывы 26 уз на 24 м² носа: 26² ÷ 60 × 24 ≈ 270 кгс; подруливающее 160 кгс не удержит',
        'Anchor upwind, chain snubbed: it holds the bow · the engines place the stern': 'Якорь на ветре, цепь на стопоре держит нос · моторы ставят корму',
        'gusts 26 kn': 'порывы 26 уз', 'anchor upwind, chain snubbed': 'якорь на ветре, цепь на стопоре', 'QUAY': 'ПРИЧАЛ'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 13-15 towing lights
def lights(n):
    if n in (13, 14):
        tow_d = 150 if n == 13 else 300
        stack = ['w', 'w'] if n == 13 else ['w', 'w', 'w']
        sch = {'padPx': 70, 'night': True, 'title': 'Towing, tow up to 200 m · seen from ahead' if n == 13 else 'Towing, tow over 200 m · seen from ahead',
               'key': ['Two masthead lights in a vertical line, sidelights, a sternlight and the yellow towing light' if n == 13 else 'Three masthead lights in a vertical line: the tow is over 200 m (a diamond by day)',
                       'Length of tow: from her stern to the stern of the tow'],
               'boats': [{'x': 0, 'z': 0, 'hdg': 180, 'power': True, 'stack': stack, 'label': 'tug', 'noHeading': True, 'bearing': False, 'scale': 1.8},
                         {'x': 0, 'z': -tow_d, 'hdg': 180, 'label': 'tow', 'noHeading': True, 'bearing': False, 'scale': 1.8, 'labelAbove': True},
                         {'you': True, 'x': 60, 'z': 300, 'hdg': 0, 'noHeading': True, 'scale': 1.8}],
               'paths': [{'pts': [[0, -12], [0, -tow_d + 12]], 'c': 'line', 'w': 5}],
               'dims': [{'a': [-90, 0], 'b': [-90, -tow_d], 'text': 'tow 150 m' if n == 13 else 'tow 300 m'}],
               'fit': [{'x': -160, 'z': -tow_d - 120}, {'x': 160, 'z': 340}]}
    else:
        sch = {'padPx': 70, 'night': True, 'title': 'Towing · seen from astern', 'key': ['The yellow towing light over the white sternlight, both 135° astern', 'Nearer, the sternlight of the tow'],
               'boats': [{'x': 0, 'z': 0, 'hdg': 180, 'power': True, 'stack': ['y', 'w'], 'label': 'tug', 'noHeading': True, 'bearing': False, 'scale': 1.8},
                         {'x': 0, 'z': -150, 'hdg': 180, 'label': 'tow', 'noHeading': True, 'bearing': False, 'scale': 1.8, 'labelAbove': True},
                         {'you': True, 'x': -40, 'z': -400, 'hdg': 180, 'noHeading': True, 'scale': 1.8, 'labelAbove': True}],
               'paths': [{'pts': [[0, -12], [0, -138]], 'c': 'line', 'w': 5}],
               'fit': [{'x': -160, 'z': -460}, {'x': 160, 'z': 60}]}
    ru({'Towing, tow up to 200 m · seen from ahead': 'Буксировка, буксир до 200 м · вид с носа', 'Towing, tow over 200 m · seen from ahead': 'Буксировка, буксир больше 200 м · вид с носа',
        'Two masthead lights in a vertical line, sidelights, a sternlight and the yellow towing light': 'Два топовых огня по вертикали, бортовые, кормовой и жёлтый буксировочный',
        'Three masthead lights in a vertical line: the tow is over 200 m (a diamond by day)': 'Три топовых огня по вертикали: буксир больше 200 м (днём — ромб)',
        'Length of tow: from her stern to the stern of the tow': 'Длина буксира: от её кормы до кормы буксируемого',
        'Towing · seen from astern': 'Буксировка · вид с кормы', 'The yellow towing light over the white sternlight, both 135° astern': 'Жёлтый буксировочный над белым кормовым, оба на 135° в корму',
        'Nearer, the sternlight of the tow': 'Ближе — кормовой огонь буксируемого', 'tug': 'буксировщик', 'tow': 'буксируемое', 'tow 150 m': 'буксир 150 м', 'tow 300 m': 'буксир 300 м'})
    return {'noScale': True, 'sch': sch}

# ------------------------------------------------------------------------------------------------ 16 hove-to
def p16():
    sch = {'padPx': 70, 'wind': 0, 'minMpp': 0.01, 'title': 'Hove-to, 50° off the wind', 'key': ['Jib backed to windward, main eased, helm to leeward: she lies quiet and drifts slowly', 'Forereaching? Ease the main · never lie a-hull, beam-on to the breaking crests'],
           'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 50, 'scale': 3.4}],
           'paths': [{'pts': [[6, 6], [14, 18], [18, 26]], 'c': 'accent', 'w': 6, 'arrow': True, 'dash': '12 10'}, {'pts': [[-12, -4], [-4, -14]], 'c': 'ink', 'w': 3, 'dash': '4 8'}],
           'texts': [T(-13, -9, 'jib backed to windward'), T(13, -4, 'main eased'), T(-13, 6, 'helm to leeward'), T(22, 22, 'drift', 'accent'), T(-15, -18, 'slick to windward')],
           'fit': [{'x': -24, 'z': -20}, {'x': 26, 'z': 28}]}
    ru({'Hove-to, 50° off the wind': 'В дрейфе, 50° к ветру', 'Jib backed to windward, main eased, helm to leeward: she lies quiet and drifts slowly': 'Стаксель вывернут на ветер, грот потравлен, руль под ветер: лежит спокойно, дрейф малый',
        'Forereaching? Ease the main · never lie a-hull, beam-on to the breaking crests': 'Идёт вперёд? Потравите грот · никогда не лежите лагом под гребнями',
        'jib backed to windward': 'стаксель вывернут на ветер', 'main eased': 'грот потравлен', 'helm to leeward': 'руль под ветер', 'drift': 'дрейф', 'slick to windward': 'гладь на ветре'})
    return {'sch': sch}

# ------------------------------------------------------------------------------------------------ 17 running before the seas
def p17():
    x0, X = 330, lambda v: 330 + v * 42
    b = ''
    for i, (lab, v, col, t) in enumerate((('the seas', 18, RED, '18 kn'), ('hull speed', 11, BLUE, '11 kn'))):
        y = 110 + i * 150
        b += txt(300, y + 50, lab, 32, 700, 'var(--ink)', 'end') + rect(x0, y, X(v) - x0, 80, col, 'none', 0, 10, 'opacity=".85"') + txt(X(v) + 18, y + 52, t, 34, 700, 'var(--ink)', 'start')
    b += line(X(11), 260, X(11), 410, 'var(--ink)', 4, '8 8') + arrow(X(11) + 10, 430, X(18) - 6, 430, RED, 6, 20)
    b += pill((X(11) + X(18)) / 2, 480, 'they overtake her: 7 kn', 'red', 24)
    b += txt(330, 560, 'LWL 21.5 m = 70.5 ft: 1.34 × √70.5 ≈ 11 kn', 28, 400, 'var(--ink)', 'start')
    ru({'the seas': 'волна', 'hull speed': 'скорость корпуса', '18 kn': '18 уз', '11 kn': '11 уз', 'they overtake her: 7 kn': 'волна обгоняет на 7 уз',
        'LWL 21.5 m = 70.5 ft: 1.34 × √70.5 ≈ 11 kn': 'LWL 21,5 м = 70,5 фут: 1,34 × √70,5 ≈ 11 уз',
        'Can she run with the seas?': 'Угонится ли она за волной?', 'Period 6 s: 1.56 × 6 = 9.4 m/s ≈ 18 kn': 'Период 6 с: 1,56 × 6 = 9,4 м/с ≈ 18 уз',
        'She cannot keep up: slow down, let them pass under her': 'Не угонится: сбавьте ход, пусть волны проходят под ней'})
    return svg(17, b, 'Can she run with the seas?', ['Period 6 s: 1.56 × 6 = 9.4 m/s ≈ 18 kn', 'She cannot keep up: slow down, let them pass under her'])

PLANS = {1: p1, 2: p2, 3: p3, 4: p4, 5: p5, 6: p6, 7: p7, 8: p8, 9: p9, 10: p10, 11: p11, 13: lambda: lights(13), 14: lambda: lights(14), 15: lambda: lights(15), 16: p16, 17: p17}

if __name__ == '__main__':
    out = {n: f() for n, f in PLANS.items()}
    if '--ru' in sys.argv: print(json.dumps(RU, ensure_ascii=False, indent=1)); sys.exit()
    out = {n: f() for n, f in PLANS.items()}      # twice: every pill sized for its Russian
    os.makedirs(ADIR, exist_ok=True)
    for n, spec in out.items():
        p = os.path.join(ADIR, f'{n}-plan.json'); json.dump(spec, open(p, 'w'), ensure_ascii=False); print(p)
