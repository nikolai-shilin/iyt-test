# The plans (schematics) of yachtmaster-offshore/tides, written as <n>-plan.json beside the renders: {svg} for the tidal
# curves, the interpolations and the side views, {sch} (figure-schematic.js) for the plan views.
#   python3 docs/design/blender/art_yof_tides_plans.py
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import art_yof_pilotage_svg as S
from art_yof_pilotage_svg import txt, pill, arrow, line, boat, dim, frame, f1, COL
from art_yof_tides_tex import solent_f

DIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore', 'tides')
S.load_ru(DIR)
RED, INK, MUT = COL['red'], 'var(--ink)', 'var(--muted)'

def curve_diagram(title, key, lw, hw, hours, f, at, at_labels, times, curve_label=None):
    """The almanac's tidal curve: the heights panel (HW scale on top, LW scale below, the range line joining LW to
    HW) and the curve of factor against hours; the reading from the time up to the curve, across to the line and
    up to the height."""
    def body(ha):
        y0, y1 = ha - 150, 120                       # factor 0 and 1
        Xh = lambda m: 100 + m * 60                  # heights 0..6 m
        h0, h1 = hours; Xt = lambda h: 560 + (h - h0) * (1180 - 560) / (h1 - h0)
        Y = lambda fa: y0 - fa * (y0 - y1)
        s = ''
        for m in range(0, 7):
            x = Xh(m); s += f'<line x1="{x}" y1="{y1 - 12}" x2="{x}" y2="{y1}" stroke="{INK}" stroke-width="3"/><line x1="{x}" y1="{y0}" x2="{x}" y2="{y0 + 12}" stroke="{INK}" stroke-width="3"/>'
            s += txt(x, y1 - 22, str(m), 22, 700, MUT) + txt(x, y0 + 36, str(m), 22, 700, MUT)
        s += line([(Xh(0), y1), (Xh(6), y1)], INK, 3) + line([(Xh(0), y0), (Xh(6), y0)], INK, 3)
        s += txt(Xh(3), y1 - 56, 'HW heights, m', 22, 700, MUT) + txt(Xh(3), y0 + 70, 'LW heights, m', 22, 700, MUT)
        s += line([(Xh(lw), y0), (Xh(hw), y1)], INK, 5)
        for k in range(0, 11):
            yy = Y(k / 10); s += f'<line x1="{Xt(h0)}" y1="{f1(yy)}" x2="{Xt(h1)}" y2="{f1(yy)}" stroke="var(--line)" stroke-width="2"/>'
            if k % 2 == 0: s += txt(Xt(h0) - 12, yy + 8, f'{k / 10:.1f}', 22, 700, MUT, 'end')
        for h in range(int(h0), int(h1) + 1):
            x = Xt(h); s += f'<line x1="{f1(x)}" y1="{y0}" x2="{f1(x)}" y2="{y1}" stroke="var(--line)" stroke-width="2"/>'
            s += txt(x, y0 + 32, times[0](h), 22, 700, INK)
            if times[1]: s += txt(x, y0 + 60, times[1](h), 20, 400, MUT)
        s += txt(Xt(h1) + 10, y1 - 30, 'factor', 22, 700, MUT, 'end')
        pts = [(Xt(h0 + i * (h1 - h0) / 120), Y(f(h0 + i * (h1 - h0) / 120))) for i in range(121)]
        s += line(pts, INK, 6)
        fa = f(at); xa, ya = Xt(at), Y(fa); xl = Xh(lw + fa * (hw - lw))
        s += line([(xa, y0), (xa, ya)], RED, 5, '12 8') + line([(xa, ya), (xl, ya)], RED, 5, '12 8') + arrow(xl, ya, xl, y1 + 4, RED, 5, 20)
        s += f'<circle cx="{f1(xa)}" cy="{f1(ya)}" r="10" fill="{RED}"/><circle cx="{f1(xl)}" cy="{f1(ya)}" r="10" fill="{RED}"/>'
        s += pill(xa + 6, y0 - 34, at_labels[0], 'red', 24) + pill(xa + 110, ya - 34, at_labels[1], 'light', 24) + pill(xl, y1 + 50, at_labels[2], 'red', 26)
        s += pill(Xh(lw) + 4, y0 - 34, f'LW {lw:.1f} m'.replace('.0 m', '.0 m'), 'light', 22) + pill(Xh(hw) + 84, y1 + 40, f'HW {hw:.1f} m', 'light', 22)
        if curve_label: s += pill(*curve_label)
        return s
    return frame(title, key, body, grid=False)

def interp(ha, x0, w, title, xs, ys, xlab, ylab, pa, pb, at, res, reading):
    """A small graph: the difference against the standard port's value, the straight line between the two
    tabulated points, the reading at today's value."""
    y0, y1 = ha - 120, 150; X = lambda v: x0 + (v - xs[0]) / (xs[1] - xs[0]) * w; Y = lambda v: y0 - (v - ys[0]) / (ys[1] - ys[0]) * (y0 - y1)
    s = txt(x0 + w / 2, 70, title, 28, 700, INK)
    s += line([(x0, y1 - 10), (x0, y0), (x0 + w + 10, y0)], INK, 3)
    for v, l in xlab: s += f'<line x1="{f1(X(v))}" y1="{y0}" x2="{f1(X(v))}" y2="{y1}" stroke="var(--line)" stroke-width="2"/>' + txt(X(v), y0 + 34, l, 22, 700, MUT)
    for v, l in ylab: s += f'<line x1="{x0}" y1="{f1(Y(v))}" x2="{x0 + w}" y2="{f1(Y(v))}" stroke="var(--line)" stroke-width="2"/>' + txt(x0 - 12, Y(v) + 8, l, 22, 700, MUT, 'end')
    s += line([(X(pa[0]), Y(pa[1])), (X(pb[0]), Y(pb[1]))], INK, 5)
    for p in (pa, pb): s += f'<circle cx="{f1(X(p[0]))}" cy="{f1(Y(p[1]))}" r="11" fill="var(--bg)" stroke="{INK}" stroke-width="4"/>'
    xa, ya = X(at), Y(res)
    s += line([(xa, y0), (xa, ya)], RED, 5, '12 8') + arrow(xa, ya, x0 + 6, ya, RED, 5, 18) + f'<circle cx="{f1(xa)}" cy="{f1(ya)}" r="10" fill="{RED}"/>'
    s += pill(xa, ya - 60, reading, 'red', 26)
    return s

def p1():
    return {'svg': curve_diagram('Standard port curve · the height at 1100',
        ['LW 0900 0.8 m, HW 1500 5.6 m: range 4.8 m · 1100 is HW−4, factor 0.25', 'Height = LW + factor × range = 0.8 + 0.25 × 4.8 = 2.0 m'],
        0.8, 5.6, (-6, 6), lambda h: (1 + math.cos(math.pi * h / 6)) / 2, -4, ['1100 · HW−4', 'factor 0.25', '2.0 m'],
        (lambda h: 'HW' if h == 0 else f'{h:+d}', lambda h: f'{(15 + h) % 24:02d}00'))}

def p3():
    return {'svg': curve_diagram('Solent curve · hours from low water',
        ['LW 1000 0.6 m, HW 4.2 m: range 3.6 m · 1400 is LW+4, factor 0.75', '0.6 + 0.75 × 3.6 = 3.3 m · a double high water: a long stand at the top'],
        0.6, 4.2, (-5, 8), solent_f, 4, ['1400 · LW+4', 'factor 0.75', '3.3 m'],
        (lambda h: 'LW' if h == 0 else f'{h:+d}', lambda h: f'{(10 + h) % 24:02d}00'), (1000, 115, 'double high water', 'light', 22))}

def p2():
    def body(ha):
        s = interp(ha, 130, 440, 'Time difference', (5.5, 12.5), (-35, -5), [(6, '0600'), (9, '0900'), (12, '1200')], [(-30, '−0030'), (-20, '−0020'), (-10, '−0010')],
                   (6, -30), (12, -10), 9, -20, 'HW 0840')
        s += interp(ha, 760, 440, 'Height difference', (4.4, 6.0), (-0.7, -0.1), [(4.6, 'MHWN 4.6'), (5.2, '5.2'), (5.8, 'MHWS 5.8')], [(-0.6, '−0.6'), (-0.4, '−0.4'), (-0.2, '−0.2')],
                    (4.6, -0.2), (5.8, -0.6), 5.2, -0.4, 'HW 4.8 m')
        return s
    return {'svg': frame('Secondary port · interpolate both differences',
        ['0900 is halfway from 0600 to 1200: −0030 to −0010 gives −0020, HW 0840', '5.2 m is halfway from MHWN 4.6 to MHWS 5.8: −0.2 to −0.6 gives −0.4, HW 4.8 m'], body, grid=False)}

def hull_side(hx, wl, L=420, keel=150, k=70.0, draught=2.2):
    """A yacht in profile, bow left, her keel draught m below the waterline (k px per metre)."""
    kd = draught * k
    s = f'<path d="M{hx} {wl - 34} L{hx + L} {wl - 26} L{hx + L - 30} {wl + 22} L{hx + 40} {wl + 26} Z" fill="var(--ink)"/>'
    s += f'<path d="M{hx + L * 0.42} {wl + 20} L{hx + L * 0.42 + 70} {wl + 20} L{hx + L * 0.42 + 54} {wl + kd} L{hx + L * 0.42 + 8} {wl + kd} Z" fill="var(--ink)"/>'
    s += f'<line x1="{hx + L * 0.5}" y1="{wl - 34}" x2="{hx + L * 0.5}" y2="{wl - 160}" stroke="var(--ink)" stroke-width="6"/>'
    return s, hx + L * 0.42 + 31

def p4():
    def body(ha):
        k = 68.0; sea = 175; cd = sea + 1.2 * k; bed = cd + 5.4 * k
        s = f'<rect x="0" y="{sea}" width="{S.W}" height="{bed - sea}" fill="{COL["sea"]}"/><rect x="0" y="{bed}" width="{S.W}" height="{ha - bed}" fill="{COL["bed"]}"/>'
        s += line([(0, bed), (S.W, bed)], COL['bedLine'], 5)
        wave = [(x, sea - 1.0 * k * math.cos((x - 470) / 360 * math.pi)) for x in range(0, S.W + 1, 10)]
        s += line(wave, COL['seaLine'], 4, '10 8') + line([(0, sea), (S.W, sea)], COL['seaLine'], 5)
        s += line([(0, cd), (S.W, cd)], COL['course'], 4, '14 10') + txt(20, cd - 12, 'chart datum', 22, 700, INK, 'start')
        h, kx = hull_side(260, sea, k=k, draught=2.2)
        low = sea + 3.5 * k
        s += line([(kx - 170, low), (kx + 150, low)], RED, 4, '10 8')
        s += dim(kx - 120, sea, kx - 120, sea + 2.2 * k, 'draught 2.2 m', 0, 'light', 22)
        s += dim(kx + 100, sea + 2.2 * k, kx + 100, sea + 3.2 * k, '½ swell 1.0', 0, 'red', 22, 80) + dim(kx + 100, sea + 3.2 * k, kx + 100, low, 'squat 0.3', 0, 'red', 22, 230)
        s += dim(kx + 30, low, kx + 30, bed, '3.1 m under the keel', 0, 'accent', 24, 150)
        s += dim(1040, sea, 1040, cd, 'tide +1.2', 0, 'light', 22, 80) + dim(1040, cd, 1040, bed, 'charted 5.4', 0, 'light', 22, 80)
        s += h + txt(1000, sea - 1.0 * k - 18, 'swell 2.0 m: crest and trough', 22, 700, INK)
        return s
    return {'svg': frame('Over the bank in a swell · side view',
        ['Charted 5.4 + tide 1.2 = 6.6 m of water at the mean level', 'In a trough she drops half the swell, 1.0 m, and squats 0.3 m: 6.6 − 2.2 − 1.3 = 3.1 m'], body, grid=False)}

def p5():
    def body(ha):
        k = 24.0; base = ha - 40; Y = lambda m: base - m * k
        s = f'<rect x="0" y="{f1(Y(6.1))}" width="{S.W}" height="{f1(base - Y(6.1))}" fill="{COL["sea"]}"/>' + line([(0, Y(6.1)), (S.W, Y(6.1))], COL['seaLine'], 5)
        s += line([(0, Y(0)), (S.W, Y(0))], COL['course'], 4, '14 10') + txt(20, Y(0) - 10, 'chart datum', 22, 700, INK, 'start')
        s += line([(0, Y(6.0)), (400, Y(6.0))], INK, 3, '6 8') + txt(20, Y(6.0) + 26, 'HAT 6.0', 22, 700, INK, 'start')
        s += line([(0, Y(5.6)), (400, Y(5.6))], MUT, 3, '6 8') + txt(20, Y(5.6) + 50, 'HW 5.6 + surge 0.5 = 6.1', 22, 400, INK, 'start')
        s += f'<rect x="400" y="{f1(Y(23.4))}" width="860" height="{f1(2.4 * k)}" fill="#bdb8ad" stroke="var(--ink)" stroke-width="4"/>'
        for x in (420, 1170): s += f'<rect x="{x}" y="{f1(Y(21.0))}" width="60" height="{f1(21.0 * k)}" fill="#bdb8ad" stroke="var(--ink)" stroke-width="4"/>'
        sx = 790; wl = Y(6.1); mt = Y(6.1 + 14.2)
        s += f'<path d="M{sx - 150} {wl - 10} L{sx + 160} {wl - 6} L{sx + 140} {wl + 14} L{sx - 120} {wl + 16} Z" fill="var(--ink)"/>' + line([(sx, wl - 10), (sx, mt)], INK, 6)
        s += dim(540, Y(6.0), 540, Y(21.0), 'clearance 15.0 above HAT', 0, 'light', 22, 0, -60)
        s += dim(1040, wl, 1040, Y(21.0), 'room 14.9 m', 0, 'accent', 24) + dim(sx - 60, wl, sx - 60, mt, 'air draught 14.2', 0, 'light', 22, 0, 60)
        s += pill(sx + 140, (mt + Y(21.0)) / 2, '0.7 m to spare', 'red', 24)
        return s
    return {'svg': frame('Bridge clearance on a surge · side view',
        ['Room = clearance 15.0 + HAT 6.0 − HW tonight 6.1 = 14.9 m', 'HW 6.1 = 5.6 predicted + 0.5 surge · air draught 14.2 m: 0.7 m to spare'], body, grid=False)}

def p7():
    def body(ha):
        x0, w = 200, 900; y0, y1 = ha - 110, 110
        X = lambda r: x0 + (r - 2.0) / (6.4 - 2.0) * w; Y = lambda v: y0 - (v - 1.2) / (4.0 - 1.2) * (y0 - y1)
        s = line([(x0, y1 - 10), (x0, y0), (x0 + w + 10, y0)], INK, 3)
        for r in (2.0, 2.8, 4.2, 5.6, 6.4): s += f'<line x1="{f1(X(r))}" y1="{y0}" x2="{f1(X(r))}" y2="{y1}" stroke="var(--line)" stroke-width="2"/>' + txt(X(r), y0 + 34, f'{r:.1f} m', 22, 700, MUT)
        for v in (1.8, 2.6, 3.4): s += f'<line x1="{x0}" y1="{f1(Y(v))}" x2="{x0 + w}" y2="{f1(Y(v))}" stroke="var(--line)" stroke-width="2"/>' + txt(x0 - 12, Y(v) + 8, f'{v:.1f} kn', 22, 700, MUT, 'end')
        s += txt(x0 + w / 2, y0 + 70, 'range at the reference port', 22, 700, MUT) + txt(x0 - 12, y1 - 30, 'rate', 22, 700, MUT, 'start')
        sl = (3.4 - 1.8) / (5.6 - 2.8); fv = lambda r: 1.8 + sl * (r - 2.8)
        s += line([(X(2.0), Y(fv(2.0))), (X(2.8), Y(1.8))], INK, 4, '10 8') + line([(X(5.6), Y(3.4)), (X(6.4), Y(fv(6.4)))], INK, 4, '10 8') + line([(X(2.8), Y(1.8)), (X(5.6), Y(3.4))], INK, 6)
        for r, v, l in ((2.8, 1.8, 'neaps 1.8'), (5.6, 3.4, 'springs 3.4')):
            s += f'<circle cx="{f1(X(r))}" cy="{f1(Y(v))}" r="12" fill="var(--bg)" stroke="{INK}" stroke-width="4"/>' + pill(X(r) + (90 if r < 4 else -100), Y(v) - 42, l, 'light', 22)
        xa, ya = X(4.2), Y(2.6)
        s += line([(xa, y0), (xa, ya)], RED, 5, '12 8') + arrow(xa, ya, x0 + 6, ya, RED, 5, 18) + f'<circle cx="{f1(xa)}" cy="{f1(ya)}" r="10" fill="{RED}"/>'
        s += pill(xa + 40, ya + 60, 'today 4.2 m: 2.6 kn', 'red', 26) + pill(X(6.2), Y(fv(6.2)) + 70, 'this line you may extend', 'light', 20)
        return s
    return {'svg': frame('Rate for today · interpolate by the range',
        ['Atlas 18,34: 1.8 kn at mean neaps (range 2.8 m), 3.4 kn at mean springs (5.6 m)', "Today's range 4.2 m is halfway: 1.8 + ½ × (3.4 − 1.8) = 2.6 kn"], body, grid=False)}

# ---- plan views ({sch}): drawing units of the figure (320 x 200, y down) -> metres east, metres south
def U(s): return lambda x, y: [round((x - 160) * s, 1), round((y - 100) * s, 1)]
def t(x, z, text, **o): return {'x': x, 'z': z, 'text': text, **o}

def p6():
    P = U(4.0)
    land = [[P(-60, -60), P(128, -60), P(128, 84), P(-60, 84)], [P(192, -60), P(380, -60), P(380, 84), P(192, 84)]]
    return {'sch': {'padPx': 50, 'title': 'River bar in a 2 m swell', 'key': ['Breaks where the depth is under 1.3 × 2.0 m = 2.6 m', 'Bar charted 0.4 m: cross on the flood once the tide is past 2.2 m'],
        'land': land, 'zones': [{'pts': [P(108, 106), P(212, 106), P(212, 124), P(108, 124)], 'c': 'red', 'fill': 'rgba(224,37,27,.16)'}],
        'boats': [{'you': True, 'x': P(160, 182)[0], 'z': P(160, 182)[1], 'hdg': 0, 'noHeading': True}],
        'paths': [{'pts': [P(250, 200), P(250, 150)], 'c': 'ink', 'w': 5, 'arrow': True}, {'pts': [P(70, 200), P(70, 150)], 'c': 'ink', 'w': 5, 'arrow': True}],
        'texts': [t(*P(160, 40), '4', pill=False, size=30), t(*P(160, 100), '0.4', pill=False, size=30), t(*P(160, 150), '12', pill=False, size=30), t(*P(70, 135), '9', pill=False, size=30),
                  t(*P(160, 64), 'river', pill=False, size=26), t(*P(258, 115), 'breaks under 2.6 m', kind='red'), t(*P(250, 214), 'swell 2.0 m'), t(*P(70, 214), 'swell 2.0 m'),
                  t(*P(236, 160), 'wait for 2.2 m of tide', kind='accent')],
        'fit': [dict(zip('xz', P(40, 20))), dict(zip('xz', P(280, 215)))]}}

def p8():
    return {'noScale': True, 'sch': {'padPx': 60, 'title': 'Two yachts, one beam stream', 'key': ['30 M at 6 kn: 5 h in a 2 kn stream, set 10 M · at 20 kn: 1 h 30, set 3 M', 'Set = rate × time in the stream: the slow yacht is set further'],
        'boats': [{'you': True, 'x': 0, 'z': 0, 'hdg': 90, 'noHeading': True, 'label': 'A'}, {'x': 3000, 'z': 1000, 'hdg': 90, 'noHeading': True, 'bearing': False, 'label': '6 kn: 5 h'},
                  {'x': 3000, 'z': 300, 'hdg': 90, 'noHeading': True, 'bearing': False, 'label': '20 kn: 1 h 30', 'labelAbove': True}],
        'spots': [{'x': 3000, 'z': -40, 'label': 'B'}],
        'paths': [{'pts': [[90, 0], [2900, 0]], 'c': 'ink', 'w': 4, 'dash': '10 10'}, {'pts': [[90, 20], [2880, 960]], 'c': 'red', 'w': 5, 'arrow': True}, {'pts': [[90, 10], [2880, 290]], 'c': 'course', 'w': 5, 'arrow': True},
                  {'pts': [[900, -700], [900, -380]], 'c': 'ink', 'w': 6, 'arrow': True}, {'pts': [[1900, -700], [1900, -380]], 'c': 'ink', 'w': 6, 'arrow': True}],
        'dims': [{'a': [3000, 0], 'b': [3000, 1000], 'text': 'set 10 M', 'off': -200}, {'a': [3000, 0], 'b': [3000, 300], 'text': 'set 3 M', 'off': -90}],
        'texts': [t(1400, -540, 'stream 2 kn'), t(1500, -90, 'course 090°, 30 M')],
        'fit': [{'x': -150, 'z': -760}, {'x': 3900, 'z': 1250}]}}

HEAD = 'M110 0 H210 V10 C205 50 185 80 165 95 C150 85 130 55 115 20 Z'
def p9():
    P = U(6.0); land = [[P(110, -40), P(210, -40)] + [P(*p) for p in poly_of_head()][2:]]
    return {'sch': {'padPx': 50, 'title': 'Race off a headland', 'key': ['E-going stream: the race lies downstream, E and SE of the point', 'When the stream turns to the W, the race moves to the W side'],
        'land': land, 'zones': [{'pts': ellipse(P(222, 120), 70 * 6, 32 * 6, -20), 'c': 'red', 'fill': 'rgba(224,37,27,.14)'}, {'pts': ellipse(P(108, 120), 60 * 6, 28 * 6, 20), 'c': 'ink', 'fill': 'rgba(0,0,0,.03)'}],
        'boats': [{'you': True, 'x': P(40, 150)[0], 'z': P(40, 150)[1], 'hdg': 90, 'noHeading': True}],
        'paths': [{'pts': [P(70, 182), P(140, 182)], 'c': 'ink', 'w': 6, 'arrow': True}, {'pts': [P(170, 182), P(240, 182)], 'c': 'ink', 'w': 6, 'arrow': True}],
        'texts': [t(*P(155, 194), 'E-going stream'), t(*P(236, 158), 'race', kind='red'), t(*P(80, 92), 'race when the stream runs W'), t(*P(160, 30), 'headland', pill=False, size=26),
                  t(*P(60, 60), '22', pill=False, size=28), t(*P(270, 60), '25', pill=False, size=28), t(*P(150, 170), '30', pill=False, size=28)],
        'fit': [dict(zip('xz', P(10, 0))), dict(zip('xz', P(300, 195)))]}}

def p10():
    P = U(6.0); land = [[P(110, -40), P(210, -40)] + [P(*p) for p in poly_of_head()][2:]]
    return {'sch': {'padPx': 50, 'wind': 270, 'title': 'Three ways round', 'key': ['A inshore, a few cables off: settled weather, neaps, daylight, the pilot\'s time', 'B the race: no · C outside the race and a margin: the default'],
        'land': land, 'zones': [{'pts': ellipse(P(176, 136), 60 * 6, 14 * 6, 0), 'c': 'red', 'fill': 'rgba(224,37,27,.14)'}],
        'spots': [{'x': P(166, 110)[0], 'z': P(166, 110)[1], 'label': 'A'}, {'x': P(170, 136)[0], 'z': P(170, 136)[1], 'label': 'B'}, {'x': P(168, 166)[0], 'z': P(168, 166)[1], 'label': 'C'}],
        'paths': [{'pts': [P(40, 120), P(120, 108), P(150, 110)], 'c': 'course', 'w': 5, 'dash': '12 10'}, {'pts': [P(182, 110), P(220, 108), P(290, 120)], 'c': 'course', 'w': 5, 'dash': '12 10', 'arrow': True},
                  {'pts': [P(40, 170), P(150, 166)], 'c': 'course', 'w': 5}, {'pts': [P(186, 166), P(290, 170)], 'c': 'course', 'w': 5, 'arrow': True}],
        'texts': [t(*P(92, 96), 'inshore passage'), t(*P(236, 140), 'the race', kind='red'), t(*P(240, 182), 'outside: the default', kind='accent'), t(*P(160, 30), 'headland', pill=False, size=26)],
        'fit': [dict(zip('xz', P(30, 0))), dict(zip('xz', P(300, 195)))]}}

def poly_of_head():
    import re
    sys.path.insert(0, HERE)
    toks = re.findall(r'[MLHVCZ]|-?\d*\.?\d+', HEAD); pts, i, cmd, x, y = [], 0, None, 0.0, 0.0
    while i < len(toks):
        tk = toks[i]
        if tk in 'MLHVCZ': cmd = tk; i += 1; continue
        v = lambda k: float(toks[k])
        if cmd == 'M': x, y = v(i), v(i + 1); i += 2; pts.append((x, y)); cmd = 'L'
        elif cmd == 'L': x, y = v(i), v(i + 1); i += 2; pts.append((x, y))
        elif cmd == 'H': x = v(i); i += 1; pts.append((x, y))
        elif cmd == 'V': y = v(i); i += 1; pts.append((x, y))
        elif cmd == 'C':
            x1, y1, x2, y2, x3, y3 = (v(i + k) for k in range(6)); i += 6
            for k in range(1, 9):
                q = k / 8; u = 1 - q; pts.append((u ** 3 * x + 3 * u * u * q * x1 + 3 * u * q * q * x2 + q ** 3 * x3, u ** 3 * y + 3 * u * u * q * y1 + 3 * u * q * q * y2 + q ** 3 * y3))
            x, y = x3, y3
        else: i += 1
    return pts

def ellipse(c, rx, rz, rot=0.0, n=28):
    a = math.radians(rot)
    return [[round(c[0] + rx * math.cos(k / n * math.tau) * math.cos(a) - rz * math.sin(k / n * math.tau) * math.sin(a), 1),
             round(c[1] + rx * math.cos(k / n * math.tau) * math.sin(a) + rz * math.sin(k / n * math.tau) * math.cos(a), 1)] for k in range(n)]

def p11():
    e = [round(1200 * math.sin(math.radians(45))), -round(1200 * math.cos(math.radians(45)))]
    return {'noScale': True, 'sch': {'padPx': 60, 'title': 'Ocean current in the DR', 'key': ['Rotary tidal streams, up to 0.8 kn, cancel out over 30 h', 'Mean current NE 0.4 kn: 30 h × 0.4 = 12 M NE of the DR'],
        'boats': [{'you': True, 'x': e[0], 'z': e[1], 'hdg': 30, 'noHeading': True, 'label': 'EP'}],
        'spots': [{'x': 0, 'z': 0, 'label': 'DR'}],
        'paths': [{'pts': [[-1100, 700], [-50, 40]], 'c': 'ink', 'w': 4, 'dash': '12 10'}, {'pts': [[30, -30], [e[0] - 40, e[1] + 40]], 'c': 'course', 'w': 6, 'arrow': True}],
        'circles': [{'x': -700, 'z': -500, 'r': 160, 'c': 'ink', 'dash': '10 8'}],
        'dims': [{'a': [0, 0], 'b': e, 'text': '12 M', 'off': -170}],
        'texts': [t(-760, 640, 'your track by log', pill=False, size=24), t(700, -150, 'current NE 0.4 kn', kind='accent'), t(-700, -720, 'rotary stream: it cancels')],
        'fit': [{'x': -1150, 'z': 750}, {'x': 1100, 'z': -1100}]}}

if __name__ == '__main__':
    os.makedirs(DIR, exist_ok=True)
    for n, fn in ((1, p1), (2, p2), (3, p3), (4, p4), (5, p5), (6, p6), (7, p7), (8, p8), (9, p9), (10, p10), (11, p11)):
        S.write(DIR, n, fn()); print('plan', n)
    print('svg strings:', len(S.USED))
