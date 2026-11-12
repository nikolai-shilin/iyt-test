# The plan views of the racing-rules figures (articles course, definitions, limits, marks, obstructions): one
# docs/design/figure-style/articles/racing-rules/<a>/<n>-plan.json each, {"svg": ..., "strings": [...]}, drawn in the
# look of figure-schematic.js (a 1280-wide frame, faint grid, compass, red wind arrow, scale bar, big pills, the key
# band along the bottom) but with what a race needs that schematic() has no symbol for: each boat's mainsail and
# boom to leeward, the inflatable mark with its three-length zone, the line's pin and committee boat, the course
# sailed. Boats are drawn to scale (a hull length is 26.4 figure units, 14.9 m), at the figure's exact positions and
# headings, from the same description as the renders (art_rr_a_scenes.py). "strings" lists every text of the svg so
# capture_article.mjs --strings picks them up; pills are sized for the longer of the English and the ru.json text,
# because the page swaps the words of an svg in place. System Python.
#   python3 docs/design/blender/art_rr_a_plans.py [article ...]
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_rr_a_scenes as S

ART = os.path.join(S.DESIGN, 'figure-style', 'articles', 'racing-rules')
W, TS = 1280, 1.7
COURSE, WIND, ACC = '#e0b400', '#e8231a', 'var(--accent)'
COL = {'blue': ACC, 'red': WIND, None: 'var(--muted)', 'white': 'var(--muted)'}
RU = {}

def esc(s): return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
def tlen(s): return max(len(str(s)), len(RU.get(s, '')))
def txt(x, y, s, size=26, w=700, f='var(--muted)', a='middle', extra=''):
    STR.add(s)
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{round(size * TS)}" font-weight="{w}" fill="{f}" text-anchor="{a}" {extra}>{esc(s)}</text>'
def pill_wh(text, size): z = round(size * TS); return tlen(text) * z * 0.58 + z * 1.4, z * 1.7
def pill(x, y, text, kind='light', size=24):
    w, h = pill_wh(text, size); z = round(size * TS)
    fill = ACC if kind == 'accent' else WIND if kind == 'red' else 'var(--bg)'
    ink = 'var(--ink)' if kind == 'light' else '#fff'; stroke = 'var(--tag-line)' if kind == 'light' else fill
    return f'<rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>' + txt(x, y + z * 0.36, text, size, f=ink)
def arrow(x1, y1, x2, y2, c='var(--muted)', w=4, h=16, dash=None):
    a = math.atan2(y2 - y1, x2 - x1); p1 = (x2 - h * math.cos(a - .5), y2 - h * math.sin(a - .5)); p2 = (x2 - h * math.cos(a + .5), y2 - h * math.sin(a + .5))
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w}" stroke-linecap="round"{d}/><path d="M{x2:.1f} {y2:.1f} L{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} Z" fill="{c}"/>'
def spol(x, y, r, deg): return x + r * math.sin(math.radians(deg)), y - r * math.cos(math.radians(deg))

HULL = 'M0 -22 C 7 -14 8 6 6 18 L -6 18 C -8 6 -7 -14 0 -22 Z'
def boat(x, y, hdg, sc, you=False, fill=None, sail=True, mast_down=None):
    """The hull from above in figures.js's sailing look (a pale hull, the ink mainsail to leeward): 40 long, origin
    22 behind the bow. The sail is a crescent from the mast to the boom end, swung out for the point of sail (at least
    16 degrees, so a close-hauled sail still shows)."""
    hullc = fill or ('var(--bg)' if sail else 'var(--ink)')
    body = (f'<path d="{HULL}" fill="{hullc}" stroke="var(--ink)" stroke-width="2" stroke-linejoin="round"/>'
            '<rect x="-3.4" y="5.5" width="6.8" height="9" rx="1.2" fill="var(--ink)" fill-opacity=".14"/>')
    if sail:
        side = 1 if S.tack(hdg) == 'port' else -1; ang = math.radians(max(16, S.boom_angle(hdg))); Lb = 16.0
        mx, my = 0.0, -9.5; ex, ey = mx + side * math.sin(ang) * Lb, my + math.cos(ang) * Lb
        nx, ny = (ey - my) * side, -(ex - mx) * side; n = math.hypot(nx, ny); nx, ny = nx / n, ny / n
        cx, cy = (mx + ex) / 2 + nx * 5.0, (my + ey) / 2 + ny * 5.0
        body += f'<path d="M{mx} {my} Q{cx:.2f} {cy:.2f} {ex:.2f} {ey:.2f} Z" fill="var(--ink)" fill-opacity=".85" stroke="var(--ink)" stroke-width="1.4" stroke-linejoin="round"/>'
    if mast_down:   # capsized: the mast lying on the water to one side
        body += f'<line x1="0" y1="-9.5" x2="{mast_down * 46}" y2="-9.5" stroke="var(--ink)" stroke-width="2.4" stroke-linecap="round"/><circle cx="{mast_down * 46}" cy="-9.5" r="2.6" fill="var(--ink)"/>'
    if you: body += '<circle cx="0" cy="-1" r="3.6" fill="var(--accent)" stroke="var(--bg)" stroke-width="1"/>'
    return f'<g transform="translate({x:.1f} {y:.1f}) rotate({hdg}) scale({sc:.3f})">{body}</g>'

FLAG_SVG = {   # 30 x 20 icons, as figures.js draws the code flags
    'S': '<rect width="30" height="20" fill="#fff"/><rect x="10" y="6.5" width="10" height="7" fill="#0b4ea2"/>',
    'X': '<rect width="30" height="20" fill="#fff"/><rect x="12.5" width="5" height="20" fill="#0b4ea2"/><rect y="7.5" width="30" height="5" fill="#0b4ea2"/>',
    'M': '<rect width="30" height="20" fill="#0b4ea2"/><path d="M0 0 L30 20 M30 0 L0 20" stroke="#fff" stroke-width="4"/>',
    'blue': '<rect width="30" height="20" fill="#0b4ea2"/>', 'orange': '<rect width="30" height="20" fill="#ff7a00"/>',
}
def flag_icon(x, y, code, k=1.6):
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({k})"><line x1="0" y1="0" x2="0" y2="34" stroke="var(--ink)" stroke-width="2"/>{FLAG_SVG[code]}<rect width="30" height="20" fill="none" stroke="#7d8a91" stroke-width="1"/></g>'

def key_lines(title, key):
    """The key band: the title and one line per key string (short enough not to wrap, in English and Russian)."""
    keyH = 66 + 54 * 0 + 60 * len(key) + 30
    return keyH, 800 - (40 + 40 * len(key) + 24) + keyH

def plan(article, n):
    sp = S.spec(article, n); fig = sp['fig']; title, key = sp.get('title'), sp.get('key', [])
    if not title: return None
    global STR; STR = set()
    keyH, H = key_lines(title, key); planB = H - keyH
    # the extent: boats, marks, zone, line, courses, extra labels
    pts = []
    for b in sp['boats']: pts += [(b['x'] - 18, b['y'] - 18), (b['x'] + 18, b['y'] + 18)]
    m = fig.get('mark'); ln = fig.get('line'); ob = fig.get('obstruction')
    if m:
        pts.append((m['x'], m['y']))
        if m.get('zone'): pts += [(m['x'] - S.ZONE_U, m['y'] - S.ZONE_U), (m['x'] + S.ZONE_U, m['y'] + S.ZONE_U)]
    if sp.get('gate'): pts.append(sp['gate'][:2])
    if ln: pts += [(ln['x1'], ln['y1']), (ln['x2'], ln['y2'])]
    for d in ([fig['track']] if fig.get('track') else []) + [p[0] for p in sp.get('paths', [])]: pts += S.path_points(d, 6)
    for x, y, *_ in sp.get('pts', []): pts.append((x, y))
    if ob and sp.get('kind') in ('moored', None): pts += [(ob['x'], ob['y']), (ob['x'] + ob['w'], ob['y'] + ob['h'])]
    if ob and sp.get('kind') in ('pier', 'wall', 'quay', 'shore'):
        if 'path' in ob:
            tk = ob['path'].replace('M', ' ').replace('L', ' ').replace('Z', ' ').split(); q = [(float(a), float(b)) for a, b in zip(tk[::2], tk[1::2])]
        else: q = [(ob['x'], ob['y']), (ob['x'] + ob['w'], ob['y']), (ob['x'] + ob['w'], ob['y'] + ob['h']), (ob['x'], ob['y'] + ob['h'])]
        pts += [S.near_on(q, b['x'], b['y']) for b in sp['boats']]
        if 'lx' in ob: pts.append((ob['lx'], ob['ly']))
    if sp.get('dim'): pts += [sp['dim'][0], sp['dim'][1]]
    pts += sp.get('fit_plan', [])
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pad = sp.get('pad', 80); x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    L_, R_, T_, B_ = sp.get('area', (150, W - 240, 40, planB - 70))
    s = min((R_ - L_) / max(1, x1 - x0), (B_ - T_) / max(1, y1 - y0), 120 / S.LEN_U) * sp.get('zoom', 1.0)
    # shrink until nothing of the scene sits under the compass (top left) or the wind arrow (top right)
    solid = [(b['x'], b['y'], 16) for b in sp['boats']] + ([(m['x'], m['y'], 6)] if m else []) + ([(ln['x1'], ln['y1'], 6), (ln['x2'] + 14, ln['y2'], 30)] if ln else []) + ([(sp['gate'][0], sp['gate'][1], 6)] if sp.get('gate') else [])
    for _ in range(12):
        cx, cy = (L_ + R_) / 2 - (x0 + x1) / 2 * s + sp.get('pdx', 0), (T_ + B_) / 2 - (y0 + y1) / 2 * s + sp.get('pdy', 0)
        hitc = any((cx + x * s - r * s < 150 and cy + y * s - r * s < 190) or (cx + x * s + r * s > W - 290 and cy + y * s - r * s < 240) for x, y, r in solid)
        if not hitc or sp.get('noshrink'): break
        s *= 0.92
    P = lambda x, y: (cx + x * s, cy + y * s)
    sc = S.LEN_U / 40 * s; R = 20 * sc
    mpp = S.KM / s
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Carlito, Arial, sans-serif" style="background:var(--bg)">',
           f'<rect width="{W}" height="{H}" fill="var(--bg)"/><rect width="{W}" height="{planB}" fill="rgba(60,140,190,.07)"/>']
    stepM = next((mm for mm in (5, 10, 20, 50, 100) if mm / mpp >= 110), 100); step = stepM / mpp
    gx = cx % step
    while gx < W: out.append(f'<line x1="{gx:.1f}" y1="0" x2="{gx:.1f}" y2="{planB}" stroke="var(--line)" stroke-width="2"/>'); gx += step
    gy = cy % step
    while gy < planB: out.append(f'<line x1="0" y1="{gy:.1f}" x2="{W}" y2="{gy:.1f}" stroke="var(--line)" stroke-width="2"/>'); gy += step
    boxes = [(16, 30, 136, 166), (W - 170 - 110, 20, W - 170 + 110, 80 + 104 + 30), (20, planB - 82, 40 + step, planB - 18)]
    def ov(b, o): return max(0, min(b[2], o[2]) - max(b[0], o[0])) * max(0, min(b[3], o[3]) - max(b[1], o[1]))
    def box(x, y, w, h): return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    def inframe(x, y, w, h): return min(max(x, w / 2 + 16), W - w / 2 - 16), min(max(y, h / 2 + 12), planB - h / 2 - 12)
    def place(cands, w, h):
        best, bc = None, 1e18
        for k, (x, y) in enumerate(cands):
            x, y = inframe(x, y, w, h); b = box(x, y, w, h); c = sum(ov(b, o) for o in boxes) * 10 + k * 400
            if c < bc: best, bc = (x, y), c
        boxes.append(box(*best, w, h)); return best
    for b in sp['boats']:      # the boats' room, before anything is placed
        X, Y = P(b['x'], b['y']); boxes.append((X - R, Y - R, X + R, Y + R))
    later = []   # labels drawn after the boats
    # obstruction
    kind = sp.get('kind')
    if ob and kind == 'shore':
        xe = ob['x'] + ob['w']; X, _ = P(xe, 0)
        out.append(f'<path d="M-10 -10 L{X:.1f} -10 L{X:.1f} {planB + 10} L-10 {planB + 10} Z" fill="#e6d9b4" stroke="none"/>')
        for i in range(40):
            jx = 20 + (i * 37) % max(10, X - 50); jy = 30 + (i * 83) % max(10, planB - 60)
            if jx < X - 30: out.append(f'<circle cx="{jx:.0f}" cy="{jy:.0f}" r="{5 + i % 4}" fill="#9aae6e" fill-opacity=".75"/>')
        out.append(f'<line x1="{X:.1f}" y1="-10" x2="{X:.1f}" y2="{planB + 10}" stroke="#6b5a3a" stroke-width="5"/>')
        boxes.append((-10, -10, X, planB))
        later.append(('ob', (X - 0.5 * (X + 10) , planB * 0.62), sp['obstruction'].split(':')[0], None))
    elif ob and kind in ('pier', 'wall', 'quay'):
        if 'path' in ob:
            tk = ob['path'].replace('M', ' ').replace('L', ' ').replace('Z', ' ').split(); q = [(float(a), float(b)) for a, b in zip(tk[::2], tk[1::2])]
        else: q = [(ob['x'], ob['y']), (ob['x'] + ob['w'], ob['y']), (ob['x'] + ob['w'], ob['y'] + ob['h']), (ob['x'], ob['y'] + ob['h'])]
        qq = []
        for x, y in q:
            X, Y = P(x, y)
            if x <= 0: X = -20
            if x >= 320: X = W + 20
            if y <= 0: Y = -20
            qq.append((X, Y))
        out.append('<path d="M' + ' L'.join(f'{a:.1f} {b:.1f}' for a, b in qq) + f' Z" fill="{"#a9a397" if kind == "wall" else "#bdb8ad"}" stroke="var(--ink)" stroke-width="4"/>')
        xs_, ys_ = [a for a, _ in qq], [b for _, b in qq]; boxes.append((min(xs_), min(ys_), max(xs_), max(ys_)))
        lx, ly = (P(ob['lx'], ob['ly'] - 8) if 'lx' in ob else ((max(16, min(xs_)) + min(W, max(xs_))) / 2, (max(0, min(ys_)) + max(ys_)) / 2))
        later.append(('obtext', (lx, ly), sp['obstruction'].split(':')[0], None))
    elif ob and kind == 'moored':
        X, Y = P(ob['x'] + ob['w'] / 2, ob['y'] + ob['h'] / 2); k = ob['w'] * s / 40
        out.append(boat(X, Y, 90, k, fill='var(--ink)', sail=False))
        boxes.append((X - 20 * k, Y - 6 * k, X + 20 * k, Y + 6 * k))
        later.append(('below', (X, Y + 7 * k), sp['obstruction'].split(':')[0], None))
    elif ob:   # the RIB with flag M
        X, Y = P(ob['x'] + ob['w'] / 2, ob['y'] + ob['h'] / 2); k = 6.0 / S.KM * s / 40
        out.append(boat(X, Y, 0, k, fill='var(--muted)', sail=False)); out.append(flag_icon(X + 6, Y - 60, 'M'))
        boxes.append((X - 10, Y - 64, X + 60, Y + 22))
        later.append(('below', (X, Y + 26), 'RIB · flag M', 'red'))
    # zone, marks, gate
    if m and m.get('zone'):
        X, Y = P(m['x'], m['y']); r = S.ZONE_U * s
        out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="{r:.1f}" fill="var(--accent)" fill-opacity=".06"/><circle cx="{X:.1f}" cy="{Y:.1f}" r="{r:.1f}" fill="none" stroke="var(--accent)" stroke-width="5" stroke-dasharray="16 12"/>')
        zl = sp.get('zone_label_plan', 'zone')
        zw = tlen(zl) * 24 * TS * 0.56
        zx, zy = place([(X, Y - r + 36), (X, Y + r - 36), (X - r + zw / 2 + 20, Y), (X + r - zw / 2 - 20, Y), (X - r * 0.7, Y - r * 0.7 + 36), (X + r * 0.7, Y - r * 0.7 + 36)], zw, 44)
        out.append(txt(zx, zy + 14, zl, 24, f='var(--accent)'))
    if sp.get('gate'):
        (ax, ay), (bx, by) = P(*sp['gate'][:2]), P(m['x'], m['y'])
        out.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="var(--muted)" stroke-width="4" stroke-dasharray="6 10"/>')
    if ln:
        (ax, ay), (bx, by) = P(ln['x1'], ln['y1']), P(ln['x2'], ln['y2'])
        out.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="var(--ink)" stroke-width="4" stroke-dasharray="10 12"/>')
        if sp.get('line'):
            t = sp['line']; tx, ty = ax + (bx - ax) * sp.get('line_at', 0.5), ay + (by - ay) * sp.get('line_at', 0.5) - 22 + sp.get('line_dy', 0)
            out.append(txt(tx, ty, t, 24, f='var(--ink)')); boxes.append(box(tx, ty - 14, tlen(t) * 24 * TS * 0.56, 44))
    # courses
    if fig.get('track'):
        q = [P(*p) for p in S.path_points(fig['track'])]
        c, dash, wd = ('var(--muted)', '6 10', 4) if sp.get('line_abeam') else (COURSE, '16 12', 6)
        out.append(f'<path d="M' + ' L'.join(f'{a:.1f} {b:.1f}' for a, b in q) + f'" fill="none" stroke="{c}" stroke-width="{wd}" stroke-linecap="round" stroke-dasharray="{dash}"/>')
        if sp.get('line_abeam'): later.append(('free', P(*S.path_points(fig['track'])[3]), sp.get('abeam_plan', "A's stern abeam"), None))
    for d, col, arr in sp.get('paths', []):
        q = [P(*p) for p in S.path_points(d)]; c = COL[col] if col else 'var(--muted)'
        out.append(f'<path d="M' + ' L'.join(f'{a:.1f} {b:.1f}' for a, b in q[:-2]) + f'" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round" stroke-dasharray="14 10"/>')
        if arr: out.append(arrow(*q[-6], *q[-1], c, 6, 22))
        else: out.append(f'<line x1="{q[-3][0]:.1f}" y1="{q[-3][1]:.1f}" x2="{q[-1][0]:.1f}" y2="{q[-1][1]:.1f}" stroke="{c}" stroke-width="6" stroke-linecap="round"/>')
    for (a, b, t) in ([sp['dim']] if sp.get('dim') else []):
        (X1, Y1), (X2, Y2) = P(*a), P(*b); ang = math.atan2(Y2 - Y1, X2 - X1)
        tick = lambda X, Y: f'<line x1="{X - math.sin(ang) * 14:.1f}" y1="{Y + math.cos(ang) * 14:.1f}" x2="{X + math.sin(ang) * 14:.1f}" y2="{Y - math.cos(ang) * 14:.1f}" stroke="var(--ink)" stroke-width="4"/>'
        out.append(f'<line x1="{X1:.1f}" y1="{Y1:.1f}" x2="{X2:.1f}" y2="{Y2:.1f}" stroke="var(--ink)" stroke-width="4"/>' + tick(X1, Y1) + tick(X2, Y2))
        later.append(('dim', ((X1 + X2) / 2, (Y1 + Y2) / 2), t, None))
    # committee boat and pin
    if ln:
        X, Y = P(ln['x2'], ln['y2']); k = 12.0 / S.KM * s / 40
        out.append(boat(X, Y, ln.get('hdg', 0), k, fill='var(--muted)', sail=False)); boxes.append((X - 8 * k, Y - 22 * k, X + 8 * k, Y + 18 * k))
        fl = sp.get('rc_flags') or []
        for i, f in enumerate(fl): out.append(flag_icon(X + 10, Y - 70, f)); boxes.append((X + 6, Y - 74, X + 62, Y - 14))
        later.append(('rc', (X, Y + 18 * k), 'committee boat', None))
        if not m or (ln['x1'], ln['y1']) != (m['x'], m['y']):
            X, Y = P(ln['x1'], ln['y1']); out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="12" fill="#ff7a00" stroke="var(--ink)" stroke-width="3"/>')
            boxes.append((X - 14, Y - 14, X + 14, Y + 14)); later.append(('pin', (X, Y + 16), 'pin', None))
    for mk in ([m] if m else []) + ([dict(x=sp['gate'][0], y=sp['gate'][1], label=sp['gate'][2])] if sp.get('gate') else []):
        X, Y = P(mk['x'], mk['y'])
        out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="16" fill="#ffa800" stroke="var(--ink)" stroke-width="4"/>'); boxes.append((X - 18, Y - 18, X + 18, Y + 18))
        lt = sp.get('mark_plan', mk.get('label')) if mk is m else mk['label']
        if lt: later.append(('mark', (X, Y), lt, None))
    # boats: the heading as a dashed arrow, hull and sail
    for i, b in enumerate(sp['boats']):
        X, Y = P(b['x'], b['y']); hd = b['hdg']
        cap = sp.get('capsized') == i
        if not cap:
            bx, by = spol(X, Y, 22 * sc, hd); tx, ty = spol(X, Y, 22 * sc + 0.9 * S.LEN_U * s, hd)
            out.append(arrow(bx, by, tx, ty, 'var(--muted)', 4, 18, '8 8'))
        out.append(boat(X, Y, hd, sc, you=b.get('you', False), sail=not cap, mast_down=1 if cap else None))
        boxes.append((X - R, Y - R, X + R, Y + R))
        if not cap: boxes.append(box((bx + tx) / 2, (by + ty) / 2, abs(tx - bx) + 16, abs(ty - by) + 16))
    # labels: boats first (beside their own boat), then the rest
    pn = sp.get('plan_names')
    pos = sp.get('plan_pos', {})
    for i, b in enumerate(sp['boats']):
        name, col = sp['names'][i] if i < len(sp['names']) else (None, None)
        lab = pn[i] if pn else (name.split(':')[0] if name else None)
        if not lab: continue
        X, Y = P(b['x'], b['y']); w, h = pill_wh(lab, 28); g = R * 0.85 + 14
        c = {'below': (X, Y + g + h / 2), 'above': (X, Y - g - h / 2), 'right': (X + g + w / 2, Y), 'left': (X - g - w / 2, Y)}
        order = [pos[i]] if i in pos else ['below', 'above', 'right', 'left']
        x, y = place([c[o] for o in order], w, h)
        dx, dy = sp.get('plan_off', {}).get(i, (0, 0))
        out.append(pill(x + dx, y + dy, lab, 'accent' if b.get('you') or col == 'blue' else 'red' if col == 'red' else 'light', 28))
    for kind_, (X, Y), t, col in later:
        if kind_ in ('mark', 'rc', 'pin', 'below', 'ob', 'obtext'):
            size = 24 if kind_ in ('mark', 'below', 'obtext', 'ob') else 22
            w, h = tlen(t) * size * TS * 0.56, size * TS * 1.1
            if kind_ == 'mark': cands = [(X, Y + 30 + h / 2), (X, Y - 30 - h / 2), (X + 30 + w / 2, Y), (X - 30 - w / 2, Y)]
            elif kind_ in ('ob', 'obtext'): cands = [(X, Y), (X, Y + h), (X, Y - h)]
            else: cands = [(X, Y + 10 + h / 2), (X + w / 2 + 30, Y), (X - w / 2 - 30, Y), (X, Y - 80 - h / 2)]
            if t in sp.get('plan_textpos', {}): cands = [(X + sp['plan_textpos'][t][0], Y + sp['plan_textpos'][t][1])]
            x, y = place(cands, w, h)
            if kind_ == 'below' and col: out.append(pill(x, y, t, 'red', 22))
            else: out.append(txt(x, y + size * TS * 0.36, t, size, f='var(--ink)' if kind_ != 'pin' and kind_ != 'rc' else 'var(--muted)'))
        else:
            w, h = pill_wh(t, 24)
            off = sp.get('plan_textpos', {}).get(t)
            if off: cands = [(X + off[0], Y + off[1])]
            else: cands = [(X, Y), (X, Y - h), (X, Y + h), (X + w * 0.3, Y), (X - w * 0.3, Y), (X, Y - 2 * h), (X, Y + 2 * h)]
            x, y = place(cands, w, h); out.append(pill(x, y, t, 'light', 24))
    for x, y, t, col in sp.get('pts', []):
        t2 = sp.get('pts_plan', {}).get(t, t)
        if not t2: continue
        if t in sp.get('plan_at', {}): x, y = sp['plan_at'][t]
        X, Y = P(x, y); w, h = pill_wh(t2, 24); off = sp.get('plan_textpos', {}).get(t)
        cands = [(X + off[0], Y + off[1])] if off else [(X, Y), (X, Y - h), (X, Y + h), (X + w * 0.3, Y), (X - w * 0.3, Y), (X, Y - 2 * h), (X, Y + 2 * h)]
        x2, y2 = place(cands, w, h)
        out.append(pill(x2, y2, t2, 'accent' if col == 'blue' else 'red' if col == 'red' else 'light', 24))
    # compass, wind, scale bar, key
    out.append(compass(76, 116)); out.append(wind(W - 170, 80))
    bars = ''.join(f'<rect x="{30 + i * step / 4:.1f}" y="{planB - 35}" width="{step / 4:.1f}" height="10" fill="{"var(--bg)" if i % 2 else "var(--ink)"}"/>' for i in range(4))
    out.append(f'<g>{bars}<rect x="30" y="{planB - 35}" width="{step:.1f}" height="10" fill="none" stroke="var(--ink)" stroke-width="2.5"/>' + txt(max(30 + step / 2, 86), planB - 48, f'{stepM} m', 24, f='var(--ink)') + '</g>')
    out.append(f'<rect x="0" y="{planB}" width="{W}" height="{keyH}" fill="var(--band)"/>')
    ky = planB + 64
    STR.add(title); out.append(f'<text x="30" y="{ky}" font-size="{round(28 * TS)}" font-weight="700" fill="var(--ink)" text-anchor="start">{esc(title)}</text>')
    for k in key:
        ky += 60; STR.add(k)
        out.append(f'<text x="30" y="{ky}" font-size="{round(26 * TS)}" font-weight="400" fill="var(--ink)" text-anchor="start"><tspan>· </tspan><tspan>{esc(k)}</tspan></text>')
    out.append('</svg>')
    return dict(svg=''.join(out), strings=sorted(x for x in STR if x not in ('N',) and not x.endswith(' m')))

def compass(x, y):
    t = ''.join(f'<line x1="{spol(x, y, 34 if d % 90 else 30, d)[0]:.1f}" y1="{spol(x, y, 34 if d % 90 else 30, d)[1]:.1f}" x2="{spol(x, y, 40, d)[0]:.1f}" y2="{spol(x, y, 40, d)[1]:.1f}" stroke="var(--ink)" stroke-width="{2 if d % 90 else 3}"/>' for d in range(0, 360, 45))
    return f'<g><circle cx="{x}" cy="{y}" r="40" fill="var(--bg)" stroke="var(--tag-line)" stroke-width="3"/>{t}{arrow(x, y + 24, x, y - 24, "var(--ink)", 4, 14)}{txt(x, y - 52, "N", 26, f="var(--ink)")}</g>'

def wind(x, y):
    return f'<g>{arrow(x, y - 50, x, y + 50, WIND, 9, 24)}{pill(x, y + 104, "Wind", "red", 24)}</g>'

def main(articles):
    global RU
    for a in articles:
        p = os.path.join(ART, a, 'ru.json'); RU = json.load(open(p)) if os.path.exists(p) else {}
        for n in S.figs(a):
            r = plan(a, n); out = os.path.join(ART, a, f'{n}-plan.json')
            if r is None:
                if os.path.exists(out): os.remove(out)
                continue
            with open(out, 'w') as f: json.dump(r, f, ensure_ascii=False)
            print(out)

if __name__ == '__main__':
    main(sys.argv[1:] or list(S.ARTICLES))
