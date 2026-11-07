# Plan-view and side-view drawings ({svg} plans) for the Yachtmaster Offshore articles pilotage, tides and weather, in
# the style of figure-schematic.js: 1280 x 800, theme tokens, Carlito, pills, a faint grid, the key band along the
# bottom (title 30 px, lines 27 px). Every text node holds one whole string, so ru.json can translate it; pills are
# sized for the longer of the English and the Russian (read from the article's ru.json when it exists).
# Used by art_yof_pilotage_plans.py, art_yof_tides_plans.py and art_yof_weather_plans.py (system Python).
import os, json, math, re

W, H = 1280, 800
COL = {'red': '#e8231a', 'rr': '#e0251b', 'green': '#1aa34a', 'yellow': '#ffa800', 'course': '#e0b400', 'accent': 'var(--accent)',
       'ink': 'var(--ink)', 'muted': 'var(--muted)', 'magenta': '#d4148c', 'sea': 'rgba(60,140,190,.14)', 'seaLine': '#3c8cbe',
       'bed': '#e3d6b4', 'bedLine': '#8a7650', 'land': '#d8c9a3', 'coast': '#6b5a3a'}
RU = {}
USED = []

def load_ru(folder):
    global RU
    p = os.path.join(folder, 'ru.json'); RU = json.load(open(p)) if os.path.exists(p) else {}

def f1(v): return f'{v:.1f}'
def esc(s): return str(s).replace('&', '&amp;').replace('<', '&lt;')
def CW(c):
    if c == ' ': return .23
    if c in '.,:;\'|il′·()[]': return .26
    if c in 'ftrI': return .34
    if c in 'mwMWшщжмШЩЖЮюы': return .78
    if c.isdigit(): return .507
    if c == '°': return .36
    if c in '←→': return .95
    if c.isupper(): return .6
    return .52
def tw0(s, size): return sum(CW(c) for c in str(s)) * size
def tw(s, size): return max(tw0(s, size), tw0(RU.get(s, s), size))

def txt(x, y, s, size=26, w=700, f='var(--ink)', a='middle', halo=False, extra=''):
    s = str(s)
    if any(ch.isalpha() for ch in s) and s not in USED: USED.append(s)
    h = 'stroke="var(--bg)" stroke-width="8" stroke-linejoin="round" paint-order="stroke"' if halo else ''
    return f'<text x="{f1(x)}" y="{f1(y)}" font-size="{size}" font-weight="{w}" fill="{f}" text-anchor="{a}" {h} {extra}>{esc(s)}</text>'

def pill(x, y, text, kind='light', size=24):
    w = tw(text, size) + size * 1.3; h = size * 1.7
    fill = {'accent': 'var(--accent)', 'red': COL['red'], 'ink': 'var(--ink)', 'yellow': COL['course']}.get(kind, 'var(--bg)')
    ink = 'var(--ink)' if kind in ('light', 'yellow') else '#fff'; stroke = 'var(--tag-line)' if kind == 'light' else fill
    return (f'<rect x="{f1(x - w / 2)}" y="{f1(y - h / 2)}" width="{f1(w)}" height="{f1(h)}" rx="{f1(h / 2)}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'
            + txt(x, y + size * 0.36, text, size, 700, ink))

def arrow(x1, y1, x2, y2, c='var(--ink)', w=4, h=None, dash=None):
    a = math.atan2(y2 - y1, x2 - x1); h = h or max(16, w * 3.2)
    p1 = (x2 - h * math.cos(a - .5), y2 - h * math.sin(a - .5)); p2 = (x2 - h * math.cos(a + .5), y2 - h * math.sin(a + .5))
    ex, ey = x2 - h * 0.6 * math.cos(a), y2 - h * 0.6 * math.sin(a)
    d = f'stroke-dasharray="{dash}"' if dash else ''
    return (f'<line x1="{f1(x1)}" y1="{f1(y1)}" x2="{f1(ex)}" y2="{f1(ey)}" stroke="{c}" stroke-width="{w}" stroke-linecap="round" {d}/>'
            f'<path d="M{f1(x2)} {f1(y2)} L{f1(p1[0])} {f1(p1[1])} L{f1(p2[0])} {f1(p2[1])} Z" fill="{c}"/>')

def line(pts, c='var(--ink)', w=4, dash=None, fill='none', close=False, cap='round'):
    d = ' '.join(('M' if i == 0 else 'L') + f1(x) + ' ' + f1(y) for i, (x, y) in enumerate(pts)) + (' Z' if close else '')
    da = f'stroke-dasharray="{dash}"' if dash else ''
    return f'<path d="{d}" fill="{fill}" stroke="{c}" stroke-width="{w}" stroke-linecap="{cap}" stroke-linejoin="round" {da}/>'

def boat(x, y, hdg, scale=2.4, fill='var(--ink)', you=False, ghost=False):
    body = f'<path d="M0 -22 C 7 -14 8 6 6 18 L -6 18 C -8 6 -7 -14 0 -22 Z" fill="{fill}" stroke="var(--ink)" stroke-width="1.5" stroke-linejoin="round" {"opacity=.45" if ghost else ""}/>'
    dot = '<circle cx="0" cy="-2" r="4" fill="var(--accent)" stroke="var(--bg)" stroke-width="1.2"/>' if you else ''
    return f'<g transform="translate({f1(x)} {f1(y)}) rotate({hdg}) scale({scale})">{body}{dot}</g>'

def compass(x, y):
    return f'<g><circle cx="{x}" cy="{y}" r="40" fill="var(--bg)" stroke="var(--tag-line)" stroke-width="3"/>{arrow(x, y + 24, x, y - 24, "var(--ink)", 4, 14)}{txt(x, y - 50, "N", 26)}</g>'

def dim(x1, y1, x2, y2, text, off=0, kind='light', size=24, pdx=0, pdy=0):
    a = math.atan2(y2 - y1, x2 - x1); nx, ny = -math.sin(a) * off, math.cos(a) * off
    def tk(x, y): return f'<line x1="{f1(x - math.sin(a) * 14)}" y1="{f1(y + math.cos(a) * 14)}" x2="{f1(x + math.sin(a) * 14)}" y2="{f1(y - math.cos(a) * 14)}" stroke="var(--ink)" stroke-width="4"/>'
    return (f'<g><line x1="{f1(x1 + nx)}" y1="{f1(y1 + ny)}" x2="{f1(x2 + nx)}" y2="{f1(y2 + ny)}" stroke="var(--ink)" stroke-width="4"/>{tk(x1 + nx, y1 + ny)}{tk(x2 + nx, y2 + ny)}'
            + pill((x1 + x2) / 2 + nx + pdx, (y1 + y2) / 2 + ny + pdy, text, kind, size) + '</g>')

def key_band(title, key):
    kh = 40 + 40 * len(key) + 24
    s = f'<rect x="0" y="{H - kh}" width="{W}" height="{kh}" fill="var(--band)"/>' + txt(30, H - kh + 40, title, 30, 700, 'var(--ink)', 'start')
    for i, l in enumerate(key):
        y = H - kh + 40 + 40 * (i + 1); s += txt(30, y, '·', 27, 400, 'var(--ink)', 'start') + txt(46, y, l, 27, 400, 'var(--ink)', 'start')
    return s, H - kh

def frame(title, key, body, grid=True, north=False, step=60):
    """The page: background, an optional faint grid over the drawing area, the body (a function of the area's
    height), the N arrow, the key band."""
    band, ha = key_band(title, key)
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)"><rect width="{W}" height="{H}" fill="var(--bg)"/>'
    if grid:
        for gx in range(step // 2, W, step): s += f'<line x1="{gx}" y1="0" x2="{gx}" y2="{ha}" stroke="var(--line)" stroke-width="2"/>'
        for gy in range(step // 2, ha, step): s += f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}" stroke="var(--line)" stroke-width="2"/>'
    s += body(ha)
    if north: s += compass(70, 76)
    return s + band + '</svg>'

def path_polys(d, n=14):
    """An SVG path of M/L/H/V/C/Z (absolute) as polygons in drawing units (q_scenes.path_polys)."""
    toks = re.findall(r'[MLHVCZ]|-?\d*\.?\d+', d)
    polys, cur, cmd, x, y, i = [], None, None, 0.0, 0.0, 0
    v = lambda k: float(toks[k])
    while i < len(toks):
        t = toks[i]
        if t in 'MLHVCZ':
            cmd = None if t == 'Z' else t; i += 1; continue
        if cmd == 'M': x, y = v(i), v(i + 1); i += 2; cur = [(x, y)]; polys.append(cur); cmd = 'L'
        elif cmd == 'L': x, y = v(i), v(i + 1); i += 2; cur.append((x, y))
        elif cmd == 'H': x = v(i); i += 1; cur.append((x, y))
        elif cmd == 'V': y = v(i); i += 1; cur.append((x, y))
        elif cmd == 'C':
            x1, y1, x2, y2, x3, y3 = (v(i + k) for k in range(6)); i += 6
            for k in range(1, n + 1):
                q = k / n; u = 1 - q
                cur.append((u ** 3 * x + 3 * u * u * q * x1 + 3 * u * q * q * x2 + q ** 3 * x3, u ** 3 * y + 3 * u * u * q * y1 + 3 * u * q * q * y2 + q ** 3 * y3))
            x, y = x3, y3
        else: i += 1
    return [p[:-1] if p[0] == p[-1] else p for p in polys]

def write(folder, n, spec):
    with open(os.path.join(folder, f'{n}-plan.json'), 'w') as f: json.dump(spec, f, ensure_ascii=False, indent=1)

def drop(folder, n):
    p = os.path.join(folder, f'{n}-plan.json')
    if os.path.exists(p): os.remove(p)
