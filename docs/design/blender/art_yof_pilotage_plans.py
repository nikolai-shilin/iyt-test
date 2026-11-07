# The plans (schematics) of yachtmaster-offshore/pilotage, written as <n>-plan.json beside the renders: {svg} for the
# departure timeline, the radar horizon and the relative plot, {sch} (figure-schematic.js) for the plan views.
# Figures 1, 9 and 13 (cards with nothing to draw from above) get no plan.
#   python3 docs/design/blender/art_yof_pilotage_plans.py
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import art_yof_pilotage_svg as S
from art_yof_pilotage_svg import txt, pill, arrow, line, boat, dim, frame, f1, COL
from art_yof_pilotage_svg import path_polys

DIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'pilotage')
S.load_ru(DIR)
RED, INK, MUT, ACC = COL['red'], 'var(--ink)', 'var(--muted)', 'var(--accent)'
def U(s): return lambda x, y: [round((x - 160) * s, 1), round((y - 100) * s, 1)]
def t(x, z, text, **o): return {'x': x, 'z': z, 'text': text, **o}
def xz(p): return {'x': p[0], 'z': p[1]}

def p2():
    def body(ha):
        X = lambda h: 90 + h * (1130 / 33)                       # hours from Fri 1200
        s = ''
        for h in range(0, 34, 3):
            x = X(h); s += f'<line x1="{f1(x)}" y1="90" x2="{f1(x)}" y2="{ha - 70}" stroke="var(--line)" stroke-width="2"/>'
            d, hh = ('Fri', 12 + h) if h < 12 else ('Sat', h - 12)
            s += txt(x, ha - 40, f'{hh:02d}00', 22, 700, INK) + (txt(x, ha - 14, d, 20, 400, MUT) if hh in (12, 0) or h == 0 else '')
        y1, y2, y3 = 150, 300, 430
        s += txt(40, y1 + 8, 'Model A', 24, 700, INK, 'start') + txt(40, y2 + 8, 'Model B', 24, 700, INK, 'start') + txt(40, y3 + 8, 'You', 24, 700, INK, 'start')
        for y, h, kind, lab in ((y1, 30, 'light', 'front Sat 1800'), (y2, 24, 'red', 'front Sat 1200')):
            s += f'<line x1="{f1(X(h))}" y1="{y - 40}" x2="{f1(X(h))}" y2="{y3 + 50}" stroke="{RED if kind == "red" else MUT}" stroke-width="5" stroke-dasharray="12 8"/>' + pill(X(h), y, lab, kind, 24)
        s += f'<rect x="{f1(X(3))}" y="{y3 - 26}" width="{f1(X(18) - X(3))}" height="52" rx="10" fill="var(--accent)"/>' + txt((X(3) + X(18)) / 2, y3 + 9, 'crossing 120 M at 8 kn: 15 h', 24, 700, '#fff')
        s += f'<rect x="{f1(X(18))}" y="{y3 - 26}" width="{f1(X(24) - X(18))}" height="52" rx="10" fill="none" stroke="var(--ink)" stroke-width="3" stroke-dasharray="8 6"/>' + txt((X(18) + X(24)) / 2, y3 + 9, '6 h margin', 22, 700, INK)
        s += arrow(X(3), y3 + 110, X(3), y3 + 34, ACC, 5, 18) + pill(X(3) + 20, y3 + 130, 'leave by Fri 1500', 'accent', 26) + pill(X(18), y3 - 70, 'in harbour Sat 0600', 'light', 22)
        return s
    return {'svg': frame('Latest departure · work back from the earlier front',
        ['Two models: the front Sat 1800 or Sat 1200 · plan on the earlier one', 'Sat 1200 − 6 h margin − 15 h crossing = Fri 1500'], body, grid=False)}

def p3():
    P = U(20.0)
    lanes = [{'pts': [P(-60, 58), P(160, 58), P(160, 93), P(-60, 93)], 'c': 'ink', 'fill': 'rgba(0,0,0,.03)'},
             {'pts': [P(-60, 105), P(160, 105), P(160, 140), P(-60, 140)], 'c': 'ink', 'fill': 'rgba(0,0,0,.03)'},
             {'pts': [P(-60, 93), P(160, 93), P(160, 105), P(-60, 105)], 'c': 'red', 'fill': 'rgba(212,20,140,.16)', 'dash': '0'},
             {'pts': [P(234 + 66 * math.cos(k / 24 * math.tau), 100 + 56 * math.sin(k / 24 * math.tau)) for k in range(24)], 'c': 'red', 'fill': 'rgba(212,20,140,.07)'}]
    return {'noScale': True, 'sch': {'padPx': 50, 'title': 'Crossing a traffic separation scheme', 'key': ['A: both lanes at right angles, on a steady heading and speed', 'B: the precautionary area, where ships turn and alter: keep clear'],
        'zones': lanes,
        'boats': [{'you': True, **xz(P(24, 176)), 'hdg': 0, 'noHeading': True, 'label': 'A'}, {'plain': True, **xz(P(110, 75)), 'hdg': 270, 'scale': 3.2}, {'plain': True, **xz(P(50, 123)), 'hdg': 90, 'scale': 3.2},
                  {'plain': True, **xz(P(240, 82)), 'hdg': 45, 'scale': 3.2}],
        'paths': [{'pts': [P(24, 160), P(24, 22)], 'c': 'course', 'w': 6, 'dash': '16 11', 'arrow': True}, {'pts': [P(292, 182), P(292, 74)], 'c': 'red', 'w': 5, 'dash': '12 10', 'arrow': True},
                  {'pts': [P(150, 66), P(70, 66)], 'c': 'ink', 'w': 5, 'arrow': True}, {'pts': [P(-10, 132), P(70, 132)], 'c': 'ink', 'w': 5, 'arrow': True}],
        'texts': [t(*P(110, 50), 'W-going lane', pill=False, size=26), t(*P(110, 150), 'E-going lane', pill=False, size=26), t(*P(95, 99), 'separation zone', pill=False, size=22),
                  t(*P(232, 40), 'precautionary area', pill=False, size=26), t(*P(70, 30), 'A: at right angles', kind='accent'), t(*P(275, 182), 'B: ships turn here', kind='red')],
        'fit': [xz(P(-20, 20)), xz(P(310, 205))]}}

def p4():
    fixes_out = [-1200, -900, -600, -300]; fixes_in = list(range(-240, 241, 60))
    return {'noScale': True, 'sch': {'padPx': 60, 'title': 'Fixing as a danger closes', 'key': ['Offshore a fix every 30 min: 3 M apart at 6 kn', 'Within 3 M of a danger every 6 min, 0.6 M apart: you cannot reach it between fixes'],
        'land': [[[-300, -600], [300, -600], [380, -330], [160, -200], [-120, -230], [-380, -360]]],
        'rocks': [{'x': 0, 'z': -60, 'label': 'danger'}], 'circles': [{'x': 0, 'z': -60, 'r': 300, 'c': 'red'}] + [{'x': x, 'z': 150, 'r': 18, 'c': 'ink', 'dash': '0', 'fill': 'var(--bg)'} for x in fixes_out + fixes_in],
        'boats': [{'you': True, 'x': 520, 'z': 150, 'hdg': 90, 'noHeading': True}],
        'paths': [{'pts': [[-1300, 150], [460, 150]], 'c': 'course', 'w': 5, 'dash': '14 10', 'arrow': True}],
        'texts': [t(-750, 230, 'every 30 min', kind='light'), t(0, 230, 'every 6 min', kind='red'), t(270, -330, '3 M', kind='red'), t(-750, 80, '3 M apart', pill=False, size=22)],
        'fit': [{'x': -1300, 'z': -620}, {'x': 600, 'z': 300}]}}

def p5():
    arc = [[200 - 200 * math.cos(math.radians(a)), 200 - 200 * math.sin(math.radians(a))] for a in range(0, 91, 10)]
    return {'sch': {'padPx': 50, 'title': 'Pilotage plan · wheel-over and abort point', 'key': ['Wheel-over: radius 200 m × tan 45° = 200 m before the 90° turn', 'Abort point: the last place to turn away · the clearing bearing keeps you off the rock'],
        'land': [[[-1300, -900], [940, -900], [940, -250], [-1300, -250]], [[940, -900], [1600, -900], [1600, -70], [940, -70]], [[940, 70], [1600, 70], [1600, 900], [940, 900]]],
        'quays': [{'x1': 880, 'z1': -250, 'x2': 940, 'z2': -70}, {'x1': 880, 'z1': 70, 'x2': 940, 'z2': 500}],
        'rocks': [{'x': -330, 'z': 450, 'label': 'rock'}],
        'boats': [{'you': True, 'x': 0, 'z': 1150, 'hdg': 0, 'noHeading': True}],
        'paths': [{'pts': [[0, 1080], [0, 200]] + arc + [[870, 0]], 'c': 'course', 'w': 6, 'dash': '16 11', 'arrow': True},
                  {'pts': [[-120, -280], [-200, 1300]], 'c': 'red', 'w': 4, 'dash': '14 10'},
                  {'pts': [[-45, 610], [45, 690]], 'c': 'red', 'w': 7}, {'pts': [[-45, 690], [45, 610]], 'c': 'red', 'w': 7}],
        'dims': [{'a': [0, 200], 'b': [0, 0], 'text': '200 m', 'off': 110}],
        'texts': [t(-120, -330, 'tower', pill=False, size=24), t(-640, 1180, 'clearing bearing: tower NMT 003°', kind='red'), t(220, 240, 'wheel-over', kind='accent'),
                  t(330, 650, 'abort point', kind='red'), t(1260, -500, 'HARBOUR', pill=False, size=26)],
        'fit': [{'x': -1000, 'z': -350}, {'x': 1400, 'z': 1380}]}}

def p6():
    s = 10.0; P = U(s)
    poly = [P(*p) for p in path_polys('M0 0 H120 C116 30 108 50 100 60 C92 80 70 130 50 200 H0 Z')[0]]
    poly = [[x if x > P(0, 0)[0] + 1 else P(-40, 0)[0], z] for x, z in poly]
    L = P(104, 58)
    return {'noScale': True, 'sch': {'padPx': 50, 'title': 'Clearing lines from the light', 'key': ['Draught 3.4 m in a 3 m swell, at night: stay outside the 10 m contour, line C', 'Light bearing 314° or less: you are seaward of C'],
        'land': [poly], 'circles': [{'x': L[0], 'z': L[1], 'r': 35, 'c': 'ink', 'dash': '0', 'fill': '#ffffff'}],
        'zones': [{'pts': [P(108, 70), P(126, 110), P(100, 175), P(80, 175), P(96, 110)], 'c': 'red', 'fill': 'rgba(224,37,27,.10)'}],
        'boats': [{'you': True, **xz(P(268, 178)), 'hdg': 320, 'noHeading': True}],
        'paths': [{'pts': [L, P(118, 182)], 'c': 'ink', 'w': 4, 'dash': '12 10'}, {'pts': [L, P(169, 182)], 'c': 'ink', 'w': 4, 'dash': '12 10'}, {'pts': [L, P(229, 182)], 'c': 'red', 'w': 5, 'dash': '14 10'},
                  {'pts': [P(262, 170), P(110, 64)], 'c': 'ink', 'w': 3, 'dash': '4 8'}],
        'texts': [t(*P(96, 140), '1.4', pill=False, size=28), t(*P(131, 150), '3.8', pill=False, size=28), t(*P(174, 150), '7', pill=False, size=28), t(*P(238, 152), '14', pill=False, size=28),
                  t(*P(296, 152), '19', pill=False, size=28), t(*P(122, 46), 'light'), t(*P(118, 194), 'A · 2 m'), t(*P(169, 194), 'B · 5 m'), t(*P(229, 194), 'C · 10 m', kind='red'),
                  t(*P(80, 160), 'breakers', kind='red'), t(*P(205, 110), 'light 306°: safe', kind='accent')],
        'fit': [xz(P(40, 30)), xz(P(310, 200))]}}

def p7():
    return {'sch': {'padPx': 50, 'title': 'Port traffic signals · no entry', 'key': ['Three reds in a column on the mole head: no vessel may enter or leave', 'With the yellow beside the top red, only craft the port names may move'],
        'land': [[[-700, -900], [700, -900], [700, -560], [-700, -560]]],
        'quays': [{'x1': -460, 'z1': -340, 'x2': -50, 'z2': -300}, {'x1': 50, 'z1': -340, 'x2': 460, 'z2': -300}, {'x1': -480, 'z1': -560, 'x2': -440, 'z2': -300}, {'x1': 440, 'z1': -560, 'x2': 480, 'z2': -300}],
        'circles': [{'x': -60, 'z': -320, 'r': 14, 'c': 'red', 'dash': '0', 'fill': '#e0251b'}],
        'boats': [{'you': True, 'x': 80, 'z': 200, 'hdg': 350, 'noHeading': True, 'label': 'You: hold off'}, {'x': 0, 'z': -440, 'hdg': 180, 'noHeading': True, 'bearing': False, 'label': 'named craft', 'labelAbove': True, 'scale': 3.4}],
        'paths': [{'pts': [[0, -380], [0, -120]], 'c': 'ink', 'w': 4, 'dash': '10 8', 'arrow': True}],
        'texts': [t(-300, -230, 'three reds + yellow', kind='red'), t(-460, -680, 'HARBOUR', pill=False, size=26), t(300, 40, 'no entry', kind='red')],
        'fit': [{'x': -600, 'z': -700}, {'x': 600, 'z': 320}]}}

def p8():
    def body(ha):
        y0 = 150; x_you, x_h = 110, 394; k = 43.0; a = 34.0 / (x_h - x_you) ** 2
        Ys = lambda x: y0 + a * (x - x_h) ** 2
        s = f'<path d="' + ' '.join(('M' if i == 0 else 'L') + f1(x) + ' ' + f1(Ys(x)) for i, x in enumerate(range(60, 1230, 10))) + f' L1230 {ha} L60 {ha} Z" fill="{COL["sea"]}" stroke="{COL["seaLine"]}" stroke-width="5"/>'
        xc, xs = x_you + 24.2 * k, x_you + 19 * k
        # the yacht and her scanner; the ship's bridge; the cliff
        s += f'<path d="M{x_you - 40} {f1(Ys(x_you) - 6)} L{x_you + 40} {f1(Ys(x_you) - 6)} L{x_you + 30} {f1(Ys(x_you) + 8)} L{x_you - 30} {f1(Ys(x_you) + 8)} Z" fill="var(--ink)"/>' + line([(x_you, Ys(x_you) - 6), (x_you, y0)], INK, 5)
        s += f'<circle cx="{x_you}" cy="{y0}" r="7" fill="var(--accent)"/>'
        hs = Ys(xs) - y0; s += f'<rect x="{f1(xs - 50)}" y="{f1(Ys(xs) - 18)}" width="100" height="22" fill="var(--ink)"/><rect x="{f1(xs - 10)}" y="{f1(y0)}" width="34" height="{f1(hs - 16)}" fill="var(--ink)"/>'
        s += f'<path d="M{f1(xc - 20)} {f1(Ys(xc))} L{f1(xc - 6)} {y0} L{f1(xc + 80)} {y0 + 6} L{f1(xc + 90)} {f1(Ys(xc) + 30)} Z" fill="{COL["land"]}" stroke="{COL["coast"]}" stroke-width="5"/>'
        s += line([(x_you, y0), (xc, y0)], ACC, 4, '14 10') + f'<circle cx="{x_h}" cy="{y0}" r="9" fill="{RED}"/>'
        s += pill(x_h, y0 - 44, 'horizon 2.2 × √9 = 6.6 M', 'red', 22) + pill(xc - 40, y0 - 50, 'cliff 64 m: 2.2 × 8 = 17.6 M', 'light', 22)
        s += pill(xs, y0 + hs * 0.55, "ship's bridge 30 m: 19 M", 'light', 22) + pill(x_you + 50, y0 + 70, 'scanner 9 m', 'light', 22)
        yb = ha - 40; s += dim(x_you, yb, xc, yb, 'cliff paints at 2.2 × (3 + 8) = 24 M', 0, 'accent', 24)
        s += txt(1220, ha - 90, 'the earth’s curve, much exaggerated', 20, 400, MUT, 'end')
        return s
    return {'svg': frame('Radar horizon · side view', ['Range ≈ 2.2 × (√h₁ + √h₂) M, heights in metres: 2.2 × (√9 + √64) = 24 M',
        "A ship's bridge 30 m: 2.2 × (3 + 5.5) ≈ 19 M · her AIS from a high aerial reaches further"], body, grid=False)}

def p10():
    s = 1852 / 60.0; P = U(s)
    poly = [P(*p) for p in path_polys('M320 0 V200 H252 C242 160 232 124 236 92 C240 60 256 30 268 0 Z')[0]]
    you = P(176, 142)
    return {'noScale': True, 'sch': {'padPx': 50, 'title': 'Clearing range on a cliff', 'key': ['The reef lies 0.6 M off the cliff and gives no echo', 'VRM at 0.6 + 0.4 M margin = 1.0 M: keep the cliff echo outside the ring'],
        'land': [poly], 'rocks': [xz(P(204, 142))], 'circles': [{**xz(you), 'r': 1852, 'c': 'course'}],
        'boats': [{'you': True, **xz(you), 'hdg': 0, 'noHeading': True}],
        'paths': [{'pts': [P(176, 196), P(176, 8)], 'c': 'course', 'w': 5, 'dash': '14 10', 'arrow': True}],
        'dims': [{'a': P(176, 100), 'b': P(201, 100), 'text': 'margin 0.4 M', 'off': 0}, {'a': P(201, 62), 'b': P(239, 62), 'text': 'reef 0.6 M off', 'off': 0}],
        'texts': [t(*P(120, 70), '35', pill=False, size=28), t(*P(96, 150), '40', pill=False, size=28), t(*P(280, 120), 'cliff', pill=False, size=26), t(*P(176, 30), 'VRM 1.0 M', kind='accent'), t(*P(232, 190), 'reef: no echo', kind='red')],
        'fit': [xz(P(90, 0)), xz(P(300, 200))]}}

def p11():
    def body(ha):
        cx, cy, k = 660, 80, 95.0
        P = lambda b, r: (cx + r * k * math.sin(math.radians(b)), cy - r * k * math.cos(math.radians(b)))
        s = ''
        for r in (2, 4, 6, 8):
            s += f'<circle cx="{cx}" cy="{cy}" r="{r * k}" fill="none" stroke="var(--line)" stroke-width="3"/>' + txt(cx + r * k * 0.71 + 8, cy + r * k * 0.71 + 20, f'{r} M', 20, 700, MUT, 'start')
        s += boat(cx, cy, 180, 2.0, you=True) + line([(cx, cy + 30), (cx, cy + 6.3 * k)], INK, 3, '6 8')
        O, Aa = P(200, 5.2), P(191, 3.9); W = (O[0], O[1] - 0.9 * k); C = P(135, 2.14)
        u = ((Aa[0] - O[0]), (Aa[1] - O[1])); L = math.hypot(*u); u = (u[0] / L, u[1] / L); E = (O[0] + u[0] * 8.5 * k, O[1] + u[1] * 8.5 * k)
        s += line([O, E], RED, 4, '12 9') + line([(cx, cy), C], RED, 4, '6 6')
        s += arrow(W[0], W[1], O[0], O[1], INK, 5, 16) + arrow(W[0], W[1], Aa[0], Aa[1], ACC, 5, 16) + arrow(O[0], O[1], Aa[0], Aa[1], RED, 6, 18)
        for p, l in ((O, 'O'), (Aa, 'A'), (W, 'W')):
            s += f'<circle cx="{f1(p[0])}" cy="{f1(p[1])}" r="9" fill="var(--bg)" stroke="var(--ink)" stroke-width="4"/>' + txt(p[0] - 18, p[1] + 8, l, 24, 700, INK, 'end')
        s += f'<circle cx="{f1(C[0])}" cy="{f1(C[1])}" r="10" fill="{RED}"/>'
        s += pill(O[0] - 140, O[1] + 40, '0200 · 200° 5.2 M', 'light', 22) + pill(Aa[0] + 150, Aa[1] + 30, '0206 · 191° 3.9 M', 'light', 22)
        s += pill(C[0] + 150, C[1] - 6, 'CPA 2.1 M · 0219', 'red', 24) + pill(W[0] - 120, W[1] - 70, 'her true course 081°, 10.5 kn', 'accent', 22)
        s += pill(W[0] - 150, (W[1] + O[1]) / 2 + 4, 'your run 180°, 0.9 M', 'light', 20)
        return s
    return {'svg': frame('Relative plot · her CPA and true course',
        ['O 0200 → A 0206: 1.5 M in 6 min, 15 kn relative · CPA 2.1 M, 3.2 M on: 13 min, 0219', 'W → O is your own run, 180° 0.9 M · W → A is hers: 081°, 10.5 kn'], body, grid=False)}

def p12():
    H1, H2, Y = (-1500, -1200), (1400, -900), (0, 300)
    def arcp(c, r, sp=16):
        b = math.degrees(math.atan2(Y[0] - c[0], Y[1] - c[1]))
        return [[round(c[0] + r * math.sin(math.radians(b + d)), 1), round(c[1] + r * math.cos(math.radians(b + d)), 1)] for d in range(-sp, sp + 1, 2)]
    r1, r2 = math.hypot(Y[0] - H1[0], Y[1] - H1[1]), math.hypot(Y[0] - H2[0], Y[1] - H2[1])
    jumps = [[-200, 500], [500, -100], [-600, 100], [800, 600], [200, -400], [-300, 900], [700, 200]]
    return {'noScale': True, 'sch': {'padPx': 50, 'title': 'Jamming · fix by radar ranges', 'key': ['The GNSS position jumps about; SOG reads 41 kn', 'Two radar ranges of steep points cross where you really are: check the depth and the DR'],
        'land': [[[-2300, -2000], [-900, -2000], [-1100, -1500], [-1450, -1150], [-1700, -1300], [-2300, -1250]], [[2300, -2000], [900, -2000], [1100, -1300], [1350, -880], [1700, -1000], [2300, -900]]],
        'boats': [{'you': True, 'x': Y[0], 'z': Y[1], 'hdg': 40, 'noHeading': True}],
        'circles': [{'x': x, 'z': z, 'r': 40, 'c': 'red', 'dash': '0', 'fill': 'rgba(224,37,27,.25)'} for x, z in jumps],
        'paths': [{'pts': jumps, 'c': 'red', 'w': 3, 'dash': '6 8'}, {'pts': arcp(H1, r1), 'c': 'ink', 'w': 5}, {'pts': arcp(H2, r2), 'c': 'ink', 'w': 5},
                  {'pts': [list(H1), [round(H1[0] + (Y[0] - H1[0]) * 0.55, 1), round(H1[1] + (Y[1] - H1[1]) * 0.55, 1)]], 'c': 'ink', 'w': 3, 'dash': '4 8'},
                  {'pts': [list(H2), [round(H2[0] + (Y[0] - H2[0]) * 0.55, 1), round(H2[1] + (Y[1] - H2[1]) * 0.55, 1)]], 'c': 'ink', 'w': 3, 'dash': '4 8'}],
        'texts': [t(-1100, -620, f'radar range {r1 / 1852:.2f} M'), t(1050, -380, f'radar range {r2 / 1852:.2f} M'), t(1250, 650, 'GNSS: jumping', kind='red'), t(-1650, -1700, 'point', pill=False, size=24), t(1650, -1500, 'point', pill=False, size=24)],
        'fit': [{'x': -2000, 'z': -1900}, {'x': 1900, 'z': 1050}]}}

def p14():
    return {'sch': {'padPx': 90, 'trueScale': True, 'minMpp': 0.02, 'title': "Dutchman's log", 'key': ['A chip dropped at the bow mark passes the stern mark 5.0 s later: 18 m in 5.0 s = 3.6 m/s', '3.6 × 3,600 ÷ 1,852 = 7.0 kn, through the water'],
        'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 90, 'L': 21, 'noHeading': True}],
        'circles': [{'x': 9, 'z': 4.5, 'r': 0.45, 'c': 'ink', 'dash': '0', 'fill': '#c58b4a'}, {'x': -9, 'z': 4.5, 'r': 0.45, 'c': 'ink', 'dash': '0', 'fill': '#c58b4a'}],
        'paths': [{'pts': [[9, 1.6], [9, 4.0]], 'c': 'course', 'w': 6}, {'pts': [[-9, 1.6], [-9, 4.0]], 'c': 'course', 'w': 6}, {'pts': [[7.8, 4.5], [-7.6, 4.5]], 'c': 'ink', 'w': 3, 'dash': '8 8', 'arrow': True}],
        'dims': [{'a': [9, 6.5], 'b': [-9, 6.5], 'text': 'marks 18 m apart', 'off': 0}],
        'texts': [t(9, 9.2, 'mark 1 · 0 s'), t(-9, 9.2, 'mark 2 · 5.0 s', kind='accent'), t(-12.5, 4.5, 'chip', pill=False, size=24)],
        'fit': [{'x': -14, 'z': -5}, {'x': 14, 'z': 10.5}]}}

if __name__ == '__main__':
    os.makedirs(DIR, exist_ok=True)
    for n in (1, 9, 13): S.drop(DIR, n)
    for n, fn in ((2, p2), (3, p3), (4, p4), (5, p5), (6, p6), (7, p7), (8, p8), (10, p10), (11, p11), (12, p12), (14, p14)):
        S.write(DIR, n, fn()); print('plan', n)
    print('svg strings:', len(S.USED))
