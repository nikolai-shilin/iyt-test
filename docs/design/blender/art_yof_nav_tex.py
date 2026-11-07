# Textures for the Yachtmaster Offshore navigation renders (art_yof_charts.py, art_yof_compass.py, art_yof_dr.py):
# paper charts on a true Mercator projection with the worked examples plotted on them in pencil, log book and
# notebook pages, a table of meridional parts, the Breton plotter's base and dial, plotter screens and LCDs.
# System Python with Pillow. Each texture is written as tex/<name>.png in the article's folder, with tex/<name>.json:
# the pixel anchors the labels point at (and the sheet's size in metres for the charts).
#   python3 docs/design/blender/art_yof_nav_tex.py <article> [name ...]      (no names: all of the article's)
import os, sys, json, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ARTS = os.path.join(HERE, '..', 'figure-style', 'articles', 'yachtmaster-offshore')
SUP = '/System/Library/Fonts/Supplemental/'
FONTS = {'bold': SUP + 'Arial Bold.ttf', 'reg': SUP + 'Arial.ttf', 'ital': SUP + 'Arial Italic.ttf', 'boldital': SUP + 'Arial Bold Italic.ttf',
         'hand': SUP + 'Bradley Hand Bold.ttf', 'serif': SUP + 'Georgia Bold.ttf', 'serif_r': SUP + 'Georgia.ttf', 'serif_i': SUP + 'Georgia Italic.ttf',
         'dina': SUP + 'DIN Alternate Bold.ttf', 'narrow': SUP + 'Arial Narrow Bold.ttf', 'nar': SUP + 'Arial Narrow.ttf', 'mono': '/System/Library/Fonts/Menlo.ttc'}
def F(k, n): return ImageFont.truetype(FONTS[k], int(n))
R = math.radians

# ---------------------------------------------------------------- Mercator
def MP(lat, e2=0.00669438):
    """Meridional parts (minutes), WGS84: as Norie's tables."""
    p = R(lat)
    return 7915.7045 * math.log10(math.tan(math.pi / 4 + p / 2)) - 3437.7468 * (e2 * math.sin(p) + e2 ** 2 / 3 * math.sin(p) ** 3 + e2 ** 3 / 5 * math.sin(p) ** 5)

def lat_of_mp(m):
    lo, hi = -85.0, 85.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if MP(mid) < m: lo = mid
        else: hi = mid
    return (lo + hi) / 2

def dm(v, hemi='NS', lon=False, sec=False):
    """44.1667 -> 44°10.0'N (lon: 008°30.0'W)."""
    h = hemi[0] if v >= 0 else hemi[1]; v = abs(v); d = int(v + 1e-9); m = (v - d) * 60
    if m > 59.95: d += 1; m = 0
    return f"{d:03d}°{m:04.1f}'{h}" if lon else f"{d}°{m:04.1f}'{h}"

SEA, SHALLOW, LAND, COAST, MAG, INK = (250, 250, 246), (196, 224, 240), (240, 222, 160), (110, 88, 46), (168, 30, 120), (30, 30, 34)
PENCIL = (62, 62, 70, 235)

class Chart:
    """A Mercator chart sheet W x H px (6 px per mm), centred on (lat_c, lon_c), k px per minute of longitude.
    Margins with the latitude and longitude scales; draw content with the pixel helpers, then finish()."""
    def __init__(s, lat_c, lon_c, k, W=4800, H=3360, m=110, b=120, pxmm=6.0):
        s.W, s.H, s.k, s.m, s.b, s.pxmm = W, H, k, m, b, pxmm
        s.lat_c, s.lon_c = lat_c, lon_c; s.mpc = MP(lat_c)
        s.im = Image.new('RGB', (W, H), SEA); s.d = ImageDraw.Draw(s.im)
        s.pen = Image.new('RGBA', (W, H), (0, 0, 0, 0)); s.pd = ImageDraw.Draw(s.pen)
        s.x0, s.y0, s.x1, s.y1 = m + b, m + b, W - m - b, H - m - b
        s.anchors = {}
    # projection
    def P(s, lat, lon): return (s.W / 2 + (lon - s.lon_c) * 60 * s.k, s.H / 2 - (MP(lat) - s.mpc) * s.k)
    def inv(s, x, y): return lat_of_mp(s.mpc + (s.H / 2 - y) / s.k), s.lon_c + (x - s.W / 2) / (60 * s.k)
    def lat_lim(s): return s.inv(0, s.y1)[0], s.inv(0, s.y0)[0]
    def lon_lim(s): return s.inv(s.x0, 0)[1], s.inv(s.x1, 0)[1]
    def ppm(s, lat):
        """px per nautical mile at latitude lat."""
        return s.k / math.cos(R(lat))
    # a local plot in miles from an origin
    def set_origin(s, lat, lon): s.olat, s.olon = lat, lon
    def M(s, E, N):
        lat = s.olat + N / 60.0; mid = (s.olat + lat) / 2
        return s.P(lat, s.olon + E / (60.0 * math.cos(R(mid))))
    def scale_text(s, lat):
        mm_per_minute_lon = s.k / s.pxmm; metres = 1852 * math.cos(R(lat))
        return int(round(metres * 1000 / mm_per_minute_lon, -3))
    # printed content
    def land(s, polys_ll, label=None):
        for poly in polys_ll:
            pts = [s.P(la, lo) for la, lo in poly]
            s.d.line(pts + [pts[0]], fill=SHALLOW, width=int(70 * s.pxmm / 6), joint='curve')
            s.d.line(pts + [pts[0]], fill=(214, 234, 244), width=int(150 * s.pxmm / 6), joint='curve') if False else None
        for poly in polys_ll:
            pts = [s.P(la, lo) for la, lo in poly]
            s.d.polygon(pts, fill=LAND); s.d.line(pts + [pts[0]], fill=COAST, width=4, joint='curve')
    def shallow_band(s, polys_ll, w):
        for poly in polys_ll:
            pts = [s.P(la, lo) for la, lo in poly]
            s.d.line(pts + [pts[0]], fill=SHALLOW, width=int(w), joint='curve')
    def poly_px(s, pts, fill=None, outline=None, width=4):
        s.d.polygon(pts, fill=fill, outline=None)
        if outline: s.d.line(list(pts) + [pts[0]], fill=outline, width=width, joint='curve')
    def sounding(s, x, y, t, size=34):
        s.d.text((x, y), t, font=F('ital', size), fill=(50, 58, 70), anchor='mm')
    def soundings(s, items, size=34):
        for x, y, t in items: s.sounding(x, y, t, size)
    def contour(s, pts, label=None, dashed=False, color=(90, 110, 140), width=4):
        pts = list(pts)
        if dashed:
            for i in range(0, len(pts) - 1, 2): s.d.line([pts[i], pts[i + 1]], fill=color, width=width)
        else: s.d.line(pts, fill=color, width=width, joint='curve')
    def light(s, x, y, text=None, ang=135, size=30):
        """A light: the magenta flare from a star, its characteristic beside it."""
        a = R(ang); L = 90
        tip = (x + math.sin(a) * L, y - math.cos(a) * L); w = R(ang + 90)
        s.d.polygon([(x + math.sin(w) * 6, y - math.cos(w) * 6), tip, (x - math.sin(w) * 6, y + math.cos(w) * 6), (x + math.sin(a) * 30, y - math.cos(a) * 30)], fill=MAG)
        s.d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=INK)
        if text: s.d.text((tip[0] + 16, tip[1]), text, font=F('ital', size), fill=MAG, anchor='lm')
    def rose(s, cx, cy, Rr, var=None, text=None):
        """A compass rose: the true ring outside, the magnetic ring inside turned by the variation (deg, W negative)."""
        d = s.d
        for rr, w in ((Rr, 4), (Rr - 46, 2)): d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=MAG, width=w)
        for a in range(0, 360, 2):
            r0 = Rr - (34 if a % 10 == 0 else 16); t = R(a)
            d.line([(cx + math.sin(t) * r0, cy - math.cos(t) * r0), (cx + math.sin(t) * Rr, cy - math.cos(t) * Rr)], fill=MAG, width=3 if a % 10 == 0 else 2)
        for a in range(0, 360, 30):
            t = R(a); d.text((cx + math.sin(t) * (Rr - 70), cy - math.cos(t) * (Rr - 70)), str(a), font=F('reg', int(Rr * 0.09)), fill=MAG, anchor='mm')
        star = lambda a, r0, r1: [(cx + math.sin(R(a)) * r0, cy - math.cos(R(a)) * r0)]
        d.polygon([(cx, cy - Rr + 4), (cx - 14, cy - Rr + 70), (cx + 14, cy - Rr + 70)], fill=MAG)
        if var is not None:
            r2 = Rr * 0.62
            d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=MAG, width=3)
            for a in range(0, 360, 5):
                t = R(a + var); r0 = r2 - (24 if a % 30 == 0 else 12)
                d.line([(cx + math.sin(t) * r0, cy - math.cos(t) * r0), (cx + math.sin(t) * r2, cy - math.cos(t) * r2)], fill=MAG, width=2)
            t = R(var); d.line([(cx, cy), (cx + math.sin(t) * (r2 - 6), cy - math.cos(t) * (r2 - 6))], fill=MAG, width=4)
            ah = [(cx + math.sin(t) * (r2 - 4), cy - math.cos(t) * (r2 - 4)), (cx + math.sin(t + 0.12) * (r2 - 44), cy - math.cos(t + 0.12) * (r2 - 44)), (cx + math.sin(t - 0.12) * (r2 - 44), cy - math.cos(t - 0.12) * (r2 - 44))]
            d.polygon(ah, fill=MAG)
        if text:
            for i, ln in enumerate(text):
                d.text((cx, cy + 40 + i * Rr * 0.1), ln, font=F('reg', int(Rr * 0.085)), fill=MAG, anchor='mm')
    def title(s, x, y, lines, sizes=None, anchor='mm'):
        sizes = sizes or [64] + [40] * (len(lines) - 1)
        for i, (ln, sz) in enumerate(zip(lines, sizes)):
            s.d.text((x, y + sum(sizes[:i]) * 1.35), ln, font=F('serif' if i == 0 else 'serif_r', sz), fill=INK, anchor=anchor)
    def grid(s, lat_step, lon_step, color=(120, 120, 128), width=2):
        la0, la1 = s.lat_lim(); lo0, lo1 = s.lon_lim()
        v = math.ceil(la0 * 60 / lat_step) * lat_step
        while v <= la1 * 60:
            y = s.P(v / 60, 0)[1]; s.d.line([(s.x0, y), (s.x1, y)], fill=color, width=width); v += lat_step
        v = math.ceil(lo0 * 60 / lon_step) * lon_step
        while v <= lo1 * 60:
            x = s.P(0, v / 60)[0]; s.d.line([(x, s.y0), (x, s.y1)], fill=color, width=width); v += lon_step
    # pencil
    def pline(s, a, b, w=7, dash=None):
        if dash:
            L = math.dist(a, b); n = int(L // sum(dash)) + 1
            for i in range(n):
                t0 = i * sum(dash) / L; t1 = min(1, t0 + dash[0] / L)
                if t0 >= 1: break
                s.pd.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=PENCIL, width=w)
        else: s.pd.line([a, b], fill=PENCIL, width=w)
    def parrows(s, a, b, n=1, at=0.5, size=40, w=7):
        """n chevron arrowheads at fraction `at` along a->b, pointing to b: 1 water track, 2 ground track, 3 stream."""
        L = math.dist(a, b); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -uy, ux
        for i in range(n):
            cx, cy = a[0] + (b[0] - a[0]) * at + ux * (i - (n - 1) / 2) * size * 0.75, a[1] + (b[1] - a[1]) * at + uy * (i - (n - 1) / 2) * size * 0.75
            s.pd.line([(cx - ux * size + nx * size * 0.55, cy - uy * size + ny * size * 0.55), (cx, cy), (cx - ux * size - nx * size * 0.55, cy - uy * size - ny * size * 0.55)], fill=PENCIL, width=w, joint='curve')
    def pvec(s, a, b, n=1, w=7): s.pline(a, b, w); s.parrows(a, b, n)
    def pend_arrow(s, a, b, n=1, size=40, w=7):
        """arrowheads at the far end of a position line"""
        L = math.dist(a, b); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -uy, ux
        for i in range(n):
            cx, cy = b[0] - ux * i * size * 0.7, b[1] - uy * i * size * 0.7
            s.pd.line([(cx - ux * size + nx * size * 0.5, cy - uy * size + ny * size * 0.5), (cx, cy), (cx - ux * size - nx * size * 0.5, cy - uy * size - ny * size * 0.5)], fill=PENCIL, width=w, joint='curve')
    def pfix(s, p, r=28, w=7):
        s.pd.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], outline=PENCIL, width=w); s.pd.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5], fill=PENCIL)
    def pep(s, p, r=32, w=7):
        pts = [(p[0] + math.sin(R(a)) * r, p[1] - math.cos(R(a)) * r) for a in (0, 120, 240)]
        s.pd.line(pts + [pts[0]], fill=PENCIL, width=w, joint='curve'); s.pd.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5], fill=PENCIL)
    def pdr(s, p, along, r=28, w=7):
        """DR: a short bar across the track (along = track direction, degrees)"""
        a = R(along + 90); s.pd.line([(p[0] - math.sin(a) * r, p[1] + math.cos(a) * r), (p[0] + math.sin(a) * r, p[1] - math.cos(a) * r)], fill=PENCIL, width=w)
    def parc(s, c, r, a0, a1, w=7):
        """an arc round c (px) of radius r (px) from bearing a0 to a1 (degrees, clockwise)"""
        n = max(8, int(abs(a1 - a0) * r / 40)); pts = [(c[0] + math.sin(R(a0 + (a1 - a0) * i / n)) * r, c[1] - math.cos(R(a0 + (a1 - a0) * i / n)) * r) for i in range(n + 1)]
        s.pd.line(pts, fill=PENCIL, width=w, joint='curve')
    def ptext(s, p, t, size=46, ang=0.0, anchor='mm', color=PENCIL):
        f = F('hand', size); tw = int(s.pd.textlength(t, font=f)) + 20; th = int(size * 1.5)
        tile = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); ImageDraw.Draw(tile).text((tw / 2, th / 2), t, font=f, fill=color, anchor='mm')
        if ang: tile = tile.rotate(ang, expand=True, resample=Image.BICUBIC)
        ox = {'m': tile.width / 2, 'l': 0, 'r': tile.width}[anchor[0]]
        s.pen.alpha_composite(tile, (int(p[0] - ox), int(p[1] - tile.height / 2)))
    # the border scales
    def finish(s, out, lat_unit=None, lon_unit=None, lat_label=None, lon_label=None, extra=None):
        d = s.d; W, H, m, b = s.W, s.H, s.m, s.b
        # flatten the pencil on the chart, softly
        pen = s.pen.filter(ImageFilter.GaussianBlur(0.7))
        s.im = Image.alpha_composite(s.im.convert('RGBA'), pen).convert('RGB'); d = s.d = ImageDraw.Draw(s.im)
        # white margins
        d.rectangle([0, 0, W, s.y0], fill=SEA); d.rectangle([0, s.y1, W, H], fill=SEA); d.rectangle([0, 0, s.x0, H], fill=SEA); d.rectangle([s.x1, 0, W, H], fill=SEA)
        d.rectangle([m, m, W - m, H - m], outline=INK, width=5); d.rectangle([s.x0, s.y0, s.x1, s.y1], outline=INK, width=4)
        la0, la1 = s.lat_lim(); lo0, lo1 = s.lon_lim()
        # latitude scale, both sides: alternate bands of lat_unit minutes, ticks of a tenth
        sub = lat_unit / 10 if lat_unit <= 60 else lat_unit / 6
        v = math.floor(la0 * 60 / lat_unit) * lat_unit; i = 0
        while v < la1 * 60 + lat_unit:
            ya, yb = s.P(v / 60, 0)[1], s.P((v + lat_unit) / 60, 0)[1]
            ya2, yb2 = min(max(ya, s.y0), s.y1), min(max(yb, s.y0), s.y1)
            band = int(round(v / lat_unit)) % 2 == 0
            for xa in (s.x0 - 34, s.x1):
                if ya2 != yb2: d.rectangle([xa, yb2, xa + 34, ya2], fill=INK if band else SEA, outline=INK, width=2)
            for j in range(1, int(lat_unit / sub)):
                yy = s.P((v + j * sub) / 60, 0)[1]
                if s.y0 < yy < s.y1:
                    L = 22 if (j * sub) % (lat_unit / 2) == 0 else 12
                    d.line([(s.x0 - 34 - L, yy), (s.x0 - 34, yy)], fill=INK, width=2); d.line([(s.x1 + 34, yy), (s.x1 + 34 + L, yy)], fill=INK, width=2)
            v += lat_unit
        lab = lat_label or lat_unit
        v = math.ceil(la0 * 60 / lab) * lab
        while v <= la1 * 60:
            y = s.P(v / 60, 0)[1]; deg_, mn = divmod(round(v), 60)
            t = f"{deg_}°" if mn == 0 else f"{mn:02d}'"
            d.line([(m, y), (s.x0, y)], fill=INK, width=3); d.line([(s.x1, y), (W - m, y)], fill=INK, width=3)
            d.text((m + 14, y - 8), t, font=F('bold', 38), fill=INK, anchor='ls'); d.text((W - m - 14, y - 8), t, font=F('bold', 38), fill=INK, anchor='rs')
            v += lab
        # longitude scale, top and bottom
        unit = lon_unit; sub = unit / 10 if unit <= 60 else unit / 6
        v = math.floor(lo0 * 60 / unit) * unit
        while v < lo1 * 60 + unit:
            xa, xb = s.P(0, v / 60)[0], s.P(0, (v + unit) / 60)[0]
            xa2, xb2 = min(max(xa, s.x0), s.x1), min(max(xb, s.x0), s.x1)
            band = int(round(v / unit)) % 2 == 0
            for ya in (s.y0 - 34, s.y1):
                if xa2 != xb2: d.rectangle([xa2, ya, xb2, ya + 34], fill=INK if band else SEA, outline=INK, width=2)
            for j in range(1, int(unit / sub)):
                xx = s.P(0, (v + j * sub) / 60)[0]
                if s.x0 < xx < s.x1:
                    L = 22 if (j * sub) % (unit / 2) == 0 else 12
                    d.line([(xx, s.y0 - 34 - L), (xx, s.y0 - 34)], fill=INK, width=2); d.line([(xx, s.y1 + 34), (xx, s.y1 + 34 + L)], fill=INK, width=2)
            v += unit
        lab = lon_label or unit
        v = math.ceil(lo0 * 60 / lab) * lab
        while v <= lo1 * 60:
            x = s.P(0, v / 60)[0]; deg_, mn = divmod(round(abs(v)), 60)
            t = (f"{deg_}°" + ('W' if v < 0 else 'E' if v > 0 else '')) if mn == 0 else f"{mn:02d}'"
            d.line([(x, m), (x, s.y0)], fill=INK, width=3); d.line([(x, s.y1), (x, H - m)], fill=INK, width=3)
            d.text((x + 10, m + 8), t, font=F('bold', 38), fill=INK, anchor='lt'); d.text((x + 10, H - m - 8), t, font=F('bold', 38), fill=INK, anchor='lb')
            v += lab
        s.im.save(out + '.png')
        meta = {'W': s.W, 'H': s.H, 'w_m': s.W / s.pxmm / 1000, 'h_m': s.H / s.pxmm / 1000, 'anchors': s.anchors}
        if extra: meta.update(extra)
        json.dump(meta, open(out + '.json', 'w'), indent=1)

def scatter_soundings(c, n, f, seed=3, avoid=(), size=34, box=None):
    """n soundings at random points in the frame (or box), value f(x, y) or None to skip; avoid: [(x, y, r)]"""
    import random
    rnd = random.Random(seed); out = []
    x0, y0, x1, y1 = box or (c.x0 + 60, c.y0 + 60, c.x1 - 60, c.y1 - 60)
    tries = 0
    while len(out) < n and tries < n * 40:
        tries += 1
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        if any(math.dist((x, y), (ax, ay)) < ar for ax, ay, ar in avoid): continue
        if any(math.dist((x, y), (ox, oy)) < 150 for ox, oy, _ in out): continue
        if c.im.getpixel((int(x), int(y))) != SEA: continue
        v = f(x, y)
        if v is None: continue
        out.append((x, y, v))
    c.soundings(out, size)

# ---------------------------------------------------------------- coasts (rough, lat/long)
FRANCE_SPAIN = [(49.8, 3.0), (49.7, -1.4), (49.65, -1.95), (49.35, -1.8), (48.85, -1.6), (48.65, -1.5), (48.65, -2.0), (48.55, -2.7), (48.85, -3.0), (48.82, -3.5), (48.72, -4.0),
                (48.65, -4.5), (48.45, -4.78), (48.36, -4.55), (48.25, -4.62), (48.1, -4.3), (48.02, -4.72), (47.82, -4.35), (47.85, -4.0), (47.72, -3.5), (47.55, -3.05),
                (47.48, -2.6), (47.25, -2.2), (47.0, -2.2), (46.6, -1.85), (46.2, -1.2), (45.7, -1.25), (45.5, -1.08), (44.6, -1.25), (43.6, -1.45), (43.38, -1.75),
                (43.32, -2.0), (43.38, -3.0), (43.45, -3.8), (43.52, -5.0), (43.57, -5.8), (43.55, -6.5), (43.58, -7.4), (43.78, -7.7), (43.5, -8.2), (43.37, -8.4),
                (43.25, -8.95), (43.12, -9.2), (42.88, -9.28), (42.6, -9.05), (42.2, -8.9), (41.9, -8.88), (41.15, -8.68), (40.6, -8.75), (40.0, -8.9), (39.4, -9.38),
                (38.7, -9.5), (38.45, -9.2), (37.95, -8.88), (37.0, -8.95), (36.0, -8.9), (35.0, -6.0), (35.0, 3.0)]
IRELAND = [(55.35, -7.3), (55.2, -8.3), (54.6, -8.6), (54.3, -10.0), (53.5, -10.1), (53.2, -9.0), (52.6, -9.9), (52.1, -10.4), (51.6, -10.1), (51.45, -9.8), (51.55, -9.0),
           (51.8, -8.2), (52.0, -7.5), (52.2, -6.4), (52.6, -6.2), (53.3, -6.1), (53.9, -6.2), (54.3, -5.6), (54.7, -5.7), (55.2, -6.2)]
BRITAIN = [(50.05, -5.7), (50.2, -5.0), (50.3, -4.2), (50.6, -3.4), (50.7, -2.0), (50.8, -1.0), (50.75, 0.0), (50.9, 0.8), (51.2, 1.4), (51.5, 1.0), (51.8, 1.3), (52.5, 1.75),
           (52.95, 1.0), (53.3, 0.3), (53.6, 0.1), (54.0, -0.2), (54.6, -1.2), (55.5, -1.6), (56.0, -2.6), (56.5, -2.6), (57.2, -1.9), (57.7, -2.0), (57.6, -3.5),
           (58.6, -3.0), (58.6, -5.0), (58.0, -5.3), (57.3, -5.8), (56.5, -6.0), (55.8, -5.6), (55.3, -5.7), (54.8, -5.0), (54.6, -3.6), (54.0, -3.0), (53.4, -3.1),
           (53.3, -4.6), (52.8, -4.7), (52.1, -4.7), (51.7, -5.1), (51.6, -4.0), (51.4, -3.2), (51.2, -4.2), (50.9, -4.6), (50.5, -5.0)]

# ================================================================ charts article
def merc(out):
    """Mercator, 38-62 N: the same 10 degrees of latitude, 600 M, takes more paper further north."""
    W, H = 4200, 4800; inner = H - 2 * (110 + 120); k = inner / (MP(62.2) - MP(37.8))
    c = Chart(lat_of_mp((MP(62.2) + MP(37.8)) / 2), -15.5, k, W, H)
    c.land([FRANCE_SPAIN, IRELAND, BRITAIN])
    c.grid(600, 600, (90, 90, 96), 3)
    shelf = lambda x, y: None
    import random
    rnd = random.Random(5)
    def depth(x, y):
        la, lo = c.inv(x, y)
        near = lo > -11 and la > 43 or (lo > -10.5)
        return str(rnd.choice([92, 105, 118, 126, 140, 155, 170])) if near else str(rnd.choice([3850, 4120, 4370, 4590, 4810, 2920, 3460, 4005, 4680, 5010]))
    scatter_soundings(c, 120, depth, seed=7, size=30, avoid=[(*c.P(60.2, -24.5), 560), (*c.P(44.0, -22.0), 340)] + [(c.P(50, -26.5)[0], c.P(v, 0)[1], 140) for v in range(38, 63)])
    c.rose(*c.P(44.0, -22.0), 300, var=-4, text=['VAR 4°W 2026', "(8'E)"])
    c.title(*c.P(60.7, -24.5), ['NORTH ATLANTIC OCEAN', 'Eastern part', 'Mercator projection', f'Natural scale 1:{c.scale_text(50):,} at lat 50°'], [70, 50, 44, 44])
    # pencil: two brackets at 26°W, 40-50 and 50-60, each 600 M
    x = c.P(50, -26.5)[0]
    for a, b, key in ((40, 50, 'b1'), (50, 60, 'b2')):
        ya, yb = c.P(a, 0)[1], c.P(b, 0)[1]
        c.pline((x, ya - 6), (x, yb + 6), 12); c.pline((x - 40, ya), (x + 40, ya), 12); c.pline((x - 40, yb), (x + 40, yb), 12)
        c.pend_arrow((x, (ya + yb) / 2), (x, yb + 4)); c.pend_arrow((x, (ya + yb) / 2), (x, ya - 4))
        c.ptext((x + 70, (ya + yb) / 2), '600 M', 90, 90)
        c.anchors[key] = (x, (ya + yb) / 2)
    for v in (40, 50, 60): c.anchors[str(v)] = (c.x0 - 17, c.P(v, 0)[1])
    c.finish(out, 60, 60, 300, 600)

def biscay(out):
    """Bay of Biscay, Mercator: a leg along 48N measured beside the leg (45.0 M) and wrongly at 42N (50.0')."""
    W, H = 4800, 3360; k = (H - 460) / (MP(49.25) - MP(41.35))
    c = Chart(lat_of_mp((MP(49.25) + MP(41.35)) / 2), -6.4, k, W, H)
    c.land([FRANCE_SPAIN]); c.grid(60, 60)
    import random
    rnd = random.Random(4)
    def depth(x, y):
        la, lo = c.inv(x, y)
        if lo > -5 and la > 46.5 or (la < 44.3 and lo > -9.5 and la > 43.6): return str(rnd.choice([86, 102, 115, 128, 134, 142]))
        return str(rnd.choice([4120, 4410, 4730, 4860, 4950, 2950, 3820, 1380]))
    c.rose(*c.P(45.7, -9.2), 260, var=-1, text=['VAR 1°W 2026', "(9'E)"])
    c.title(*c.P(46.85, -4.4), ['BAY OF BISCAY', 'Mercator projection', f'Natural scale 1:{c.scale_text(45):,} at lat 45°'], [64, 44, 44])
    # the leg along 48N, 45.0 M east: d.long 45 / cos 48 = 67.25'
    A, B = c.P(48.0, -8 - 40 / 60), c.P(48.0, -8 - 40 / 60 + 67.25 / 60)
    c.pline(A, B); c.pfix(A, 22); c.pfix(B, 22); c.parrows(A, B, 1)
    c.ptext(((A[0] + B[0]) / 2, A[1] - 52), '45.0 M', 52)
    scatter_soundings(c, 90, depth, seed=9, size=30, avoid=[((A[0] + B[0]) / 2, A[1], 260)])
    # pencil ticks on the left latitude scale: 47°37.5'-48°22.5' and 41°35'-42°25'
    xs = c.x0 - 34
    for a, b, key, txt in ((48 - 22.5 / 60, 48 + 22.5 / 60, 'scale48', "45'"), (42 - 25 / 60, 42 + 25 / 60, 'scale42', "50'")):
        ya, yb = c.P(a, 0)[1], c.P(b, 0)[1]
        for yy in (ya, yb): c.pline((xs - 10, yy), (xs + 100, yy), 5)
        c.ptext((xs + 120, (ya + yb) / 2), txt, 50, 0, 'lm'); c.anchors[key] = (xs + 17, (ya + yb) / 2)
        c.anchors[key + 'a'] = (xs + 17, ya); c.anchors[key + 'b'] = (xs + 17, yb)
    c.anchors['leg'] = ((A[0] + B[0]) / 2, A[1]); c.anchors['A'] = A; c.anchors['B'] = B
    c.finish(out, 60, 60, 60, 120)

def bank(out):
    """1:350,000: a bank inside its 20 m contour, the EP 5 mm (0.9 M) outside it after six hours of DR."""
    lat_c = 54.25; pxmm = 6.0; k = 1852 * math.cos(R(lat_c)) / 350.0 * pxmm       # px per minute of longitude
    c = Chart(lat_c, 2.6, k)
    c.set_origin(54.25, 2.6)
    # the bank: an ellipse 10 x 4.4 M along 050, its 20 m contour; a 30 m contour round it, dashed
    def ell(a, b, rot, cx=0, cy=0, n=72):
        out = []
        for i in range(n):
            t = 2 * math.pi * i / n; x, y = a * math.cos(t), b * math.sin(t); r = R(rot)
            out.append(c.M(cx + x * math.cos(r) + y * math.sin(r), cy - x * math.sin(r) + y * math.cos(r)))
        return out
    c20 = ell(5.0, 2.2, 40); c30 = ell(7.2, 3.6, 40)
    c.d.polygon(c20, fill=SHALLOW)
    pts = c30 + [c30[0]]
    for i in range(0, len(pts) - 1, 2): c.d.line([pts[i], pts[i + 1]], fill=(90, 110, 140), width=3)
    c.d.line(c20 + [c20[0]], fill=(60, 90, 130), width=5)
    c.d.text(c.M(-2.0, 0.6), '20', font=F('ital', 26), fill=(60, 90, 130), anchor='mm')
    for (E, N, t) in ((0.2, 0.0, '14'), (-1.3, -0.9, '18'), (1.4, 1.0, '16'), (-2.6, -1.8, '19')): c.sounding(*c.M(E, N), t)
    # the EP: 0.94 M beyond the 20 m line, south-east of the bank's middle
    # edge point of the 20 m ellipse on the 130 deg radial, and 0.94 M further out
    import itertools
    best = min(((math.dist(p, c.M(0, 0)), p) for p in ell(5.0, 2.2, 40, n=720) if abs(((math.degrees(math.atan2(p[0] - c.M(0, 0)[0], -(p[1] - c.M(0, 0)[1]))) - 130 + 540) % 360) - 180) < 1.0))[1]
    ux, uy = math.sin(R(130)), -math.cos(R(130)); ppm = c.ppm(lat_c)
    ep = (best[0] + ux * 0.945 * ppm, best[1] + uy * 0.945 * ppm)
    # the DR track: from the 0000 fix 6 h back up 205 deg (7 kn), on to the EP at 0600
    fx, fy = ep[0] - math.sin(R(205)) * 42 * ppm, ep[1] + math.cos(R(205)) * 42 * ppm
    c.pline((fx, fy), (ep[0] + math.sin(R(205)) * 6 * ppm, ep[1] - math.cos(R(205)) * 6 * ppm)); c.pfix((fx, fy)); c.pep(ep, 26)
    c.ptext((fx + 90, fy), '0000', 48, 0, 'lm'); c.ptext((ep[0] + 70, ep[1] + 10), '0600 EP', 46, 0, 'lm')
    for h in range(1, 6):
        p = (fx + math.sin(R(205)) * 7 * h * ppm, fy - math.cos(R(205)) * 7 * h * ppm); c.pdr(p, 205, 18)
    import random
    rnd = random.Random(11)
    def depth(x, y):
        if math.dist((x, y), c.M(0, 0)) < 9 * ppm: return str(rnd.choice([24, 27, 29, 32]))
        return str(rnd.choice([38, 41, 44, 46, 48, 50, 52, 55, 58, 60]))
    c.soundings([(*c.M(-6.2, 4.6), '46'), (*c.M(-1.6, -4.6), '52'), (*c.M(7.6, -5.4), '60'), (*c.M(-8.0, -3.3), '41')])
    scatter_soundings(c, 110, depth, seed=12, size=32, avoid=[(ep[0], ep[1], 120), ((fx + ep[0]) / 2, (fy + ep[1]) / 2, 60), (c.M(0, 0)[0], c.M(0, 0)[1], 6.2 * ppm)])
    c.d.text(c.M(-13, 5.5), 'Outer Bank', font=F('serif_i', 56), fill=INK, anchor='mm')
    c.rose(*c.M(-24, -8), 300, var=1, text=['VAR 1°E 2026'])
    c.title(*c.M(-30, 14), ['NORTH SEA', 'Central part', 'Mercator projection', 'Scale 1:350,000 at lat 54°15\''], [64, 46, 40, 44])
    c.anchors.update({'ep': ep, 'edge': best, 'fix': (fx, fy), 'bank': c.M(0, 0)})
    c.finish(out, 10, 10, 10, 10, extra={'ppm': ppm})

def breton_chart(out):
    """Western approaches, 1:150,000-ish: a 205 T track ruled from a waypoint."""
    lat_c = 49.35; k = 1852 * math.cos(R(lat_c)) / 150000.0 * 1000 * 6.0
    c = Chart(lat_c, -6.4, k); c.set_origin(49.55, -6.15)
    c.grid(10, 10)
    import random
    rnd = random.Random(21)
    c.rose(*c.M(7.0, -9.0), 330, var=-6, text=['VAR 6°W 2026', "(7'E)"])
    c.title(*c.M(-12.5, 6.0), ['APPROACHES', 'TO THE CHANNEL', 'Scale 1:150,000 at lat 49°20\''], [60, 60, 42])
    A = c.M(0, 0); ppm = c.ppm(49.4)
    B = (A[0] + math.sin(R(205)) * 15 * ppm, A[1] - math.cos(R(205)) * 15 * ppm)
    c.pline((A[0] - math.sin(R(205)) * 1.0 * ppm, A[1] + math.cos(R(205)) * 1.0 * ppm), B); c.pfix(A, 24); c.parrows(A, B, 1, 0.82)
    c.ptext((A[0] + 60, A[1] - 40), 'WP 3', 46, 0, 'lm')
    scatter_soundings(c, 120, lambda x, y: str(rnd.choice([86, 92, 97, 101, 104, 108, 112, 117, 121])), seed=22, size=32,
                      avoid=[((A[0] + B[0]) / 2, (A[1] + B[1]) / 2, 900), (A[0], A[1], 260)])
    c.anchors.update({'A': A, 'B': B, 'ppm': ppm})
    c.finish(out, 10, 10, 10, 10, extra={'ppm': ppm, 'track': 205})

def corrections(out):
    """A chart's bottom-left corner: the small corrections in the margin and a stamp."""
    lat_c = 50.4; k = 1852 * math.cos(R(lat_c)) / 75000.0 * 1000 * 6.0
    c = Chart(lat_c, -4.3, k); c.set_origin(50.4, -4.3)
    c.land([[(50.62, -4.75), (50.55, -4.6), (50.48, -4.4), (50.45, -4.2), (50.38, -4.1), (50.36, -3.9), (50.6, -3.8), (50.7, -3.8), (50.7, -4.8)]])
    c.grid(5, 5)
    import random
    rnd = random.Random(31)
    scatter_soundings(c, 110, lambda x, y: str(rnd.choice([12, 15, 18, 21, 24, 27, 31, 36, 39, 42])), seed=32, size=32)
    c.rose(*c.M(4, -3), 300, var=-1, text=['VAR 1°20′W 2026', "(9'E)"])
    c.finish(out + '-tmp', 5, 5, 5, 5)
    im = Image.open(out + '-tmp.png'); os.remove(out + '-tmp.png'); os.remove(out + '-tmp.json'); d = ImageDraw.Draw(im)
    # bottom margin, left: the record of small corrections, and the stamp
    x0, y0 = 160, c.H - 104
    d.text((x0, y0 + 40), 'Small Corrections  2025-2104 · 2025-2988 · 2026-1132 · 2026-1876 · 2026-2341 · 2026-3207', font=F('reg', 38), fill=INK, anchor='ls')
    d.text((x0 + 1580, y0 + 40), '2026-3524', font=F('hand', 40), fill=(40, 52, 140), anchor='ls')
    d.text((c.W - 200, y0 + 40), 'Edition No 7 · 12 March 2021', font=F('reg', 38), fill=INK, anchor='rs')
    st = Image.new('RGBA', (900, 300), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([8, 8, 892, 292], 20, outline=(150, 30, 60, 220), width=10)
    sd.text((450, 92), 'CORRECTED TO', font=F('bold', 66), fill=(150, 30, 60, 220), anchor='mm')
    sd.text((450, 200), 'NM WEEK 31 / 26', font=F('bold', 86), fill=(150, 30, 60, 220), anchor='mm')
    st = st.rotate(4, expand=True, resample=Image.BICUBIC); im = im.convert('RGBA'); im.alpha_composite(st, (240, c.H - 640))
    # a (P) notice in pencil on the chart
    pen = Image.new('RGBA', im.size, (0, 0, 0, 0)); pd = ImageDraw.Draw(pen)
    px, py = c.M(-4.0, -1.6)
    pd.ellipse([px - 26, py - 26, px + 26, py + 26], outline=PENCIL, width=5); pd.line([(px - 40, py), (px + 40, py)], fill=PENCIL, width=5); pd.line([(px, py - 40), (px, py + 40)], fill=PENCIL, width=5)
    pd.text((px + 60, py - 10), 'Wk (P) 3412/26', font=F('hand', 50), fill=PENCIL, anchor='lm')
    pd.text((px + 60, py + 50), 'wreck reported', font=F('hand', 44), fill=PENCIL, anchor='lm')
    im = Image.alpha_composite(im, pen.filter(ImageFilter.GaussianBlur(0.7))).convert('RGB'); im.save(out + '.png')
    json.dump({'W': c.W, 'H': c.H, 'w_m': c.W / 6000, 'h_m': c.H / 6000, 'anchors': {'stamp': (690, c.H - 490), 'smallcorr': (1300, y0 + 24), 'pnotice': (px, py)}}, open(out + '.json', 'w'))

def nm_booklet(out):
    """The weekly Notices to Mariners, Week 36, open at a chart correction."""
    w, h = 1600, 2260; im = Image.new('RGB', (w, h), (250, 249, 244)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 260], fill=(24, 44, 92))
    d.text((80, 90), 'NOTICES TO MARINERS', font=F('bold', 92), fill=(255, 255, 255), anchor='lm')
    d.text((80, 196), 'Weekly Edition 36 · 3 September 2026', font=F('reg', 60), fill=(220, 228, 240), anchor='lm')
    d.text((80, 360), 'Section II · Charts', font=F('bold', 64), fill=INK, anchor='lm')
    y = 460
    for no, title, body in (('3520*', 'ENGLAND - South Coast - Wreck.', ['Insert   wreck, depth 14 m  (a)  50°21′.42N., 4°19′.06W.', 'Chart  1613 (INT 1701) · 2454 (INT 1702)']),
                            ('3524', 'ENGLAND - Plymouth Sound - Light.', ['Amend   light to, Fl(2) WR 10s 15m 8M', 'Chart  1900 · 30']),
                            ('3531(T)', 'ENGLAND - Eddystone - Buoy.', ['Note   buoy temporarily withdrawn', 'Chart  1613 · 1267']),
                            ('3412(P)', 'ENGLAND - Approaches - Wreck.', ['Wreck reported, position approximate', 'Chart  1613'])):
        d.text((80, y), no, font=F('bold', 54), fill=INK, anchor='lm'); d.text((330, y), title, font=F('bold', 50), fill=INK, anchor='lm'); y += 80
        for ln in body: d.text((330, y), ln, font=F('reg', 46), fill=(40, 40, 46), anchor='lm'); y += 70
        y += 60
    d.line([(80, y), (w - 80, y)], fill=(120, 120, 120), width=3)
    im.save(out + '.png'); json.dump({'w_px': w, 'h_px': h, 'anchors': {'week': (600, 196), 'n3524': (200, 460 + 80 + 140 + 60 + 0)}}, open(out + '.json', 'w'))

def page_lines(d, x0, y0, w, rows, pitch, color=(170, 190, 215)):
    for i in range(rows + 1): d.line([(x0, y0 + i * pitch), (x0 + w, y0 + i * pitch)], fill=color, width=2)

def notebook(out, lines, sketch=None, title=None):
    """A squared notebook page with the working in pencil."""
    w, h = 2100, 2970; im = Image.new('RGB', (w, h), (251, 251, 247)); d = ImageDraw.Draw(im)
    for x in range(0, w, 60): d.line([(x, 0), (x, h)], fill=(208, 220, 234), width=2)
    for y in range(0, h, 60): d.line([(0, y), (w, y)], fill=(208, 220, 234), width=2)
    d.line([(150, 0), (150, h)], fill=(230, 140, 150), width=4)
    pen = Image.new('RGBA', (w, h), (0, 0, 0, 0)); pd = ImageDraw.Draw(pen); an = {}
    y = 220
    if title: pd.text((200, y), title, font=F('hand', 90), fill=PENCIL, anchor='lm'); pd.line([(200, y + 60), (200 + pd.textlength(title, font=F('hand', 90)), y + 60)], fill=PENCIL, width=5); y += 210
    for i, ln in enumerate(lines):
        key = None
        if isinstance(ln, tuple): key, ln = ln
        pd.text((200, y), ln, font=F('hand', 84), fill=PENCIL, anchor='lm')
        if key: an[key] = (200 + pd.textlength(ln, font=F('hand', 84)) / 2, y)
        y += 205
    if sketch: sketch(pd, an, y)
    im = Image.alpha_composite(im.convert('RGBA'), pen.filter(ImageFilter.GaussianBlur(0.8))).convert('RGB'); im.save(out + '.png')
    json.dump({'w_px': w, 'h_px': h, 'anchors': an}, open(out + '.json', 'w'))

def midlat(out):
    lines = ["From 44°10.0'N 008°30.0'W", '220°T  100 M',
             ('dlat', "d.lat = 100 cos 40° = 76.6' S"), ('dep', 'dep = 100 sin 40° = 64.3 M W'),
             ('mid', "mid-lat 43°31.7'   cos = 0.725"), ('dlong', "d.long = 64.3 ÷ 0.725 = 88.7' W"),
             ('dr', "DR  42°53.4'N  009°58.7'W")]
    def sketch(pd, an, y):
        # the triangle: d.lat down, departure west, the course 220 between
        x0, y0, s = 1500, y + 120, 6.0
        a = (x0, y0); b = (x0, y0 + 76.6 * s); cpt = (x0 - 64.3 * s, y0 + 76.6 * s)
        pd.line([a, b, cpt, a], fill=PENCIL, width=6, joint='curve')
        pd.text((x0 + 30, y0 + 38 * s), 'd.lat', font=F('hand', 60), fill=PENCIL, anchor='lm')
        pd.text((x0 - 32 * s, y0 + 76.6 * s + 70), 'dep', font=F('hand', 60), fill=PENCIL, anchor='mm')
        pd.text((x0 - 40 * s, y0 + 30 * s), '100 M', font=F('hand', 60), fill=PENCIL, anchor='rm')
    notebook(out, lines, sketch, 'Mid-latitude sailing')

def mercsail(out):
    lines = ["From 48°00.0'N 006°00.0'W", "To  45°30.0'N 008°20.0'W",
             ('dlat', "d.lat 2°30' = 150'   d.long 2°20' = 140'"), ('dmp', 'MP 3274.4 − 3056.1 = DMP 218.3'),
             ('tan', 'tan C = 140 ÷ 218.3 = 0.641'), ('c', 'C = S 32.7° W = 213°T'), ('dist', 'dist = 150 ÷ cos 32.7° = 178.2 M')]
    notebook(out, lines, None, 'Mercator sailing')

def nories(out):
    """A page of the table of meridional parts, 44-48 degrees, the two values of the worked example ringed."""
    w, h = 2100, 2970; im = Image.new('RGB', (w, h), (246, 243, 232)); d = ImageDraw.Draw(im)
    d.text((w / 2, 130), 'MERIDIONAL PARTS', font=F('serif', 88), fill=INK, anchor='mm')
    d.text((w / 2, 230), 'Spheroid: WGS 84', font=F('serif_r', 52), fill=INK, anchor='mm')
    cols = [44, 45, 46, 47, 48]; x0, y0, cw, rh = 140, 340, 380, 42
    d.text((x0 + 60, y0), "Min", font=F('serif', 50), fill=INK, anchor='mm')
    for j, dg in enumerate(cols): d.text((x0 + 120 + cw * j + cw / 2, y0), f'{dg}°', font=F('serif', 56), fill=INK, anchor='mm')
    d.line([(x0, y0 + 40), (w - 100, y0 + 40)], fill=INK, width=3)
    an = {}
    for mn in range(60):
        y = y0 + 80 + mn * rh + (mn // 10) * 18
        d.text((x0 + 60, y), f'{mn}', font=F('serif_r', 38), fill=INK, anchor='mm')
        for j, dg in enumerate(cols):
            v = MP(dg + mn / 60); d.text((x0 + 120 + cw * j + cw / 2, y), f'{v:.1f}', font=F('serif_r', 38), fill=INK, anchor='mm')
            if (dg, mn) in ((45, 30), (48, 0)): an[f'{dg}{mn:02d}'] = (x0 + 120 + cw * j + cw / 2, y)
    pen = Image.new('RGBA', (w, h), (0, 0, 0, 0)); pd = ImageDraw.Draw(pen)
    for k_, (x, y) in an.items(): pd.ellipse([x - 120, y - 32, x + 120, y + 32], outline=PENCIL, width=6)
    im = Image.alpha_composite(im.convert('RGBA'), pen.filter(ImageFilter.GaussianBlur(0.8))).convert('RGB'); im.save(out + '.png')
    json.dump({'w_px': w, 'h_px': h, 'anchors': an}, open(out + '.json', 'w'))

def logbook(out, title, head, widths, rows, notes=(), keys=None):
    """A log book page (A4 landscape spread, one page): ruled columns, the entries in pencil-hand ink."""
    w, h = 2970, 2100; im = Image.new('RGB', (w, h), (250, 248, 240)); d = ImageDraw.Draw(im)
    d.text((120, 120), title, font=F('serif', 80), fill=(30, 40, 80), anchor='lm')
    x0, y0, rh = 120, 230, 118; xs = [x0]
    for cw in widths: xs.append(xs[-1] + cw)
    d.rectangle([x0, y0, xs[-1], y0 + rh], fill=(222, 228, 240))
    for i, t in enumerate(head): d.text(((xs[i] + xs[i + 1]) / 2, y0 + rh / 2), t, font=F('bold', 44), fill=(30, 40, 80), anchor='mm')
    nrows = 14
    for r in range(nrows + 2): d.line([(x0, y0 + r * rh), (xs[-1], y0 + r * rh)], fill=(120, 140, 180), width=3)
    for x in xs: d.line([(x, y0), (x, y0 + (nrows + 1) * rh)], fill=(120, 140, 180), width=3)
    pen = Image.new('RGBA', (w, h), (0, 0, 0, 0)); pd = ImageDraw.Draw(pen); an = {}
    ink = (28, 40, 110, 240)
    for r, row in enumerate(rows):
        yy = y0 + (r + 1) * rh + rh / 2
        for i, t in enumerate(row):
            pd.text((xs[i] + 22, yy), t, font=F('hand', 58), fill=ink, anchor='lm')
        if keys and r in keys: an[keys[r]] = ((xs[0] + xs[2]) / 2, yy)
    for (x, y, t, key) in notes:
        pd.text((x, y), t, font=F('hand', 62), fill=PENCIL, anchor='lm')
        if key: an[key] = (x + pd.textlength(t, font=F('hand', 62)) / 2, y)
    im = Image.alpha_composite(im.convert('RGBA'), pen.filter(ImageFilter.GaussianBlur(0.7))).convert('RGB'); im.save(out + '.png')
    json.dump({'w_px': w, 'h_px': h, 'anchors': an, 'cols': xs, 'y0': y0, 'rh': rh}, open(out + '.json', 'w'))

def log_speed(out):
    rows = [('2130', '512.4', '196', '7', 'SW 4', '1016', 'Abeam Start Pt'), ('2230', '519.6', '196', '7', 'SW 4', '1016', ''), ('2330', '527.0', '196', '7½', 'SW 4', '1015', ''),
            ('0030', '534.4', '196', '7½', 'SW 5', '1015', ''), ('0130', '541.7', '196', '7', 'SW 5', '1014', ''), ('0230', '548.9', '196', '7', 'SW 5', '1014', ''),
            ('0330', '556.0', '196', '7', 'W 5', '1013', ''), ('0415', '561.9', '196', '7', 'W 5', '1013', 'Fix by bearings')]
    notes = [(1700, 1480, '561.9 − 512.4 = 49.5 M', 'run'), (1700, 1600, '6 h 45 min = 6.75 h', 'time'), (1700, 1720, '49.5 ÷ 6.75 = 7.3 kn', 'speed')]
    logbook(out, 'LOG  ·  Wed 2 – Thu 3 Sept', ['Time', 'Log', 'Co °C', 'kn', 'Wind', 'Bar', 'Remarks'], [230, 260, 220, 160, 240, 220, 1400], rows, notes, {0: 'r2130', 7: 'r0415'})

def log_dr(out):
    rows = [('2000', '1204.6', '240', '8', 'NW 4', 'Fix 3 brgs'), ('2100', '1212.6', '240', '8', 'NW 4', ''), ('2200', '1220.6', '240', '8', 'NW 4', ''),
            ('2300', '1228.6', '200', '8', 'NW 4', 'A/C 200°T'), ('0000', '1236.6', '200', '8', 'NW 5', ''), ('0100', '1244.6', '200', '8', 'NW 5', ''),
            ('0200', '1252.6', '200', '8', 'NW 5', 'DR plotted')]
    logbook(out, 'LOG  ·  courses in °T', ['Time', 'Log', 'Co °T', 'kn', 'Wind', 'Remarks'], [230, 290, 230, 160, 240, 1500], rows, [], {0: 'r2000', 3: 'r2300', 6: 'r0200'})

# ---------------------------------------------------------------- the Breton plotter (RGBA: printed lines on clear acrylic)
def breton(out):
    """Base 330 x 140 mm, 8 px/mm: arrows along it, the index at the top of the dial with a variation scale either side
    (W clockwise of the index), a mm rule along both edges. The dial (separate) turns over the base's centre."""
    pm = 8; w, h = 330 * pm, 140 * pm; im = Image.new('RGBA', (w, h), (255, 255, 255, 0)); d = ImageDraw.Draw(im)
    ink = (20, 24, 30, 255); red = (200, 30, 30, 255)
    cx, cy, Rd = w / 2, h / 2 + 4 * pm, 60 * pm           # dial centre (y down; arrows point to -y? no: along +x)
    # the plotter lies with its long side along the track: the direction of travel is +x (right)
    for x in range(0, w, pm):
        mm = x // pm; L = 6 if mm % 10 else 12
        d.line([(x, 0), (x, L * pm / 4 * 2)], fill=ink, width=2 if mm % 10 else 3); d.line([(x, h), (x, h - L * pm / 4 * 2)], fill=ink, width=2 if mm % 10 else 3)
        if mm % 10 == 0 and 0 < mm < 330: d.text((x, 30 * pm / 4 * 2 - 6), str(mm // 10), font=F('reg', 34), fill=ink, anchor='mm')
    for yy in (h * 0.30, h * 0.70):
        for x0 in (12 * pm, 250 * pm):
            d.line([(x0, yy), (x0 + 60 * pm, yy)], fill=ink, width=4); d.polygon([(x0 + 66 * pm, yy), (x0 + 58 * pm, yy - 3 * pm), (x0 + 58 * pm, yy + 3 * pm)], fill=ink)
    # the index (direction of travel = +x, so the index is at angle 90 deg in image terms: to the right of the dial)
    ix = cx + Rd + 2 * pm
    d.polygon([(ix, cy), (ix + 8 * pm, cy - 4 * pm), (ix + 8 * pm, cy + 4 * pm)], fill=red)
    # variation scale either side of the index, 1 deg ticks to 20 deg; W clockwise of the index (+y here, as the
    # plotter's +x is the course and clockwise from it is towards +y in image space with y down)
    for k in range(-20, 21):
        a = math.radians(k); r0, r1 = Rd + 2 * pm, Rd + (7 if k % 5 == 0 else 5) * pm
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0); p1 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1)
        d.line([p0, p1], fill=ink, width=3)
        if k and k % 10 == 0:
            p2 = (cx + math.cos(a) * (Rd + 11 * pm), cy + math.sin(a) * (Rd + 11 * pm)); d.text(p2, str(abs(k)), font=F('bold', 34), fill=ink, anchor='mm')
    d.text((cx + Rd + 13 * pm, cy + 26 * pm), 'W', font=F('bold', 46), fill=ink, anchor='mm'); d.text((cx + Rd + 13 * pm, cy - 26 * pm), 'E', font=F('bold', 46), fill=ink, anchor='mm')
    d.text((cx + Rd + 16 * pm, cy + 44 * pm), 'VAR', font=F('bold', 34), fill=ink, anchor='mm'); d.text((cx + Rd + 16 * pm, cy - 44 * pm), 'VAR', font=F('bold', 34), fill=ink, anchor='mm')
    d.text((26 * pm, h / 2), 'BRETON', font=F('bold', 52), fill=(20, 24, 30, 160), anchor='mm')
    im.save(out + '-base.png')
    # the dial: 0-360 ring and a square grid, N at the top of the image (+y image up = north when unturned)
    s = 1200; D = Image.new('RGBA', (s, s), (255, 255, 255, 0)); dd = ImageDraw.Draw(D); c0 = s / 2; Rr = s / 2 - 4
    dd.ellipse([4, 4, s - 4, s - 4], fill=(250, 252, 255, 40), outline=ink, width=5)
    for a in range(0, 360):
        t = math.radians(a); L = 60 if a % 10 == 0 else 40 if a % 5 == 0 else 24
        dd.line([(c0 + math.sin(t) * (Rr - L), c0 - math.cos(t) * (Rr - L)), (c0 + math.sin(t) * Rr, c0 - math.cos(t) * Rr)], fill=ink, width=4 if a % 10 == 0 else 2)
    for a in range(0, 360, 10):
        t = math.radians(a); tile = Image.new('RGBA', (160, 80), (0, 0, 0, 0)); ImageDraw.Draw(tile).text((80, 40), f'{a:03d}' if a else 'N', font=F('bold', 48 if a else 56), fill=red if a == 0 else ink, anchor='mm')
        tile = tile.rotate(-a, expand=True, resample=Image.BICUBIC); p = (c0 + math.sin(t) * (Rr - 100), c0 - math.cos(t) * (Rr - 100))
        D.alpha_composite(tile, (int(p[0] - tile.width / 2), int(p[1] - tile.height / 2)))
    g = 60
    for k in range(-7, 8):
        for (x0, y0_, x1, y1) in ((c0 + k * g, c0 - 420, c0 + k * g, c0 + 420), (c0 - 420, c0 + k * g, c0 + 420, c0 + k * g)):
            # clip to a circle of radius 430
            L = 430; off = abs(k * g)
            if off >= L: continue
            half = math.sqrt(L * L - off * off)
            if x0 == x1: dd.line([(x0, c0 - half), (x0, c0 + half)], fill=(20, 24, 30, 200) if k else red, width=3 if k else 5)
            else: dd.line([(c0 - half, y0_), (c0 + half, y0_)], fill=(20, 24, 30, 200) if k else red, width=3 if k else 5)
    dd.polygon([(c0, c0 - 440), (c0 - 22, c0 - 390), (c0 + 22, c0 - 390)], fill=red)
    D.save(out + '-dial.png')
    json.dump({'base_mm': [330, 140], 'dial_centre_mm': [165, 70 - 4], 'dial_r_mm': 60}, open(out + '.json', 'w'))

# ---------------------------------------------------------------- compass article charts
def rose_var(out):
    """The rose on a chart: its variation note, and the pencilled update."""
    lat_c = 50.1; k = 1852 * math.cos(R(lat_c)) / 75000.0 * 1000 * 6.0
    c = Chart(lat_c, -5.3, k); c.set_origin(50.1, -5.3)
    c.grid(5, 5)
    import random
    rnd = random.Random(41)
    cx, cy = c.M(0, 0); Rr = 600
    c.rose(cx, cy, Rr, var=-(4 + 10 / 60))
    c.d.text((cx, cy - 120), "4°10'W 2016 (8'E)", font=F('reg', 64), fill=MAG, anchor='mm')
    scatter_soundings(c, 120, lambda x, y: str(rnd.choice([38, 42, 45, 51, 56, 62, 66, 70, 73])), seed=42, size=32, avoid=[(cx, cy, Rr + 120)])
    c.ptext((cx + 90, cy + 230), "2026: 2°50'W", 66)
    c.anchors.update({'var': (cx, cy - 140), 'pencil': (cx + 90, cy + 210), 'rose': (cx, cy - Rr)})
    c.finish(out, 5, 5, 5, 5)

def radar_chart(out):
    """Two islands A and B; radar ranges 9.3 and 7.8 M swung as arcs: they cross at X and Y; A bears 333 from X."""
    lat_c = 49.45; k = 1852 * math.cos(R(lat_c)) / 100000.0 * 1000 * 6.0
    c = Chart(lat_c, -2.55, k); c.set_origin(49.55, -2.75)
    ppm = c.ppm(49.5)
    A = c.M(0, 0); B = c.M(11.775, -10.235)
    rA, rB = 9.3 * ppm, 7.8 * ppm
    # intersections (pixel space is conformal here: Mercator over a few miles)
    dx, dy = B[0] - A[0], B[1] - A[1]; dd = math.hypot(dx, dy); a = (rA * rA - rB * rB + dd * dd) / (2 * dd); hh = math.sqrt(rA * rA - a * a)
    px_, py_ = A[0] + a * dx / dd, A[1] + a * dy / dd
    X1 = (px_ - hh * dy / dd, py_ + hh * dx / dd); X2 = (px_ + hh * dy / dd, py_ - hh * dx / dd)
    X, Y = (X1, X2) if X1[1] > X2[1] else (X2, X1)          # X: the southern one
    brg = (math.degrees(math.atan2(A[0] - X[0], -(A[1] - X[1]))) + 360) % 360
    isl = lambda p, r, sd: [(p[0] + math.cos(t) * r * (0.75 + 0.35 * math.sin(3 * t + sd)), p[1] + math.sin(t) * r * (0.8 + 0.25 * math.cos(2 * t + sd))) for t in [i * math.pi / 30 for i in range(60)]]
    for p, r, sd in ((A, 260, 0.4), (B, 320, 1.7)):
        pts = isl(p, r, sd); c.d.line(pts + [pts[0]], fill=SHALLOW, width=110, joint='curve'); c.d.polygon(pts, fill=LAND); c.d.line(pts + [pts[0]], fill=COAST, width=4)
    c.d.text((A[0], A[1] - 330), 'Île Aval', font=F('serif', 54), fill=INK, anchor='mm'); c.d.text((B[0] + 30, B[1] + 380), 'Île Basse', font=F('serif', 54), fill=INK, anchor='mm')
    c.light(A[0] + 60, A[1] + 40, 'Fl 5s 32m 18M', 120); c.light(B[0] - 40, B[1] - 60, 'Q(3) 10s 21m 11M', 300)
    import random
    rnd = random.Random(51)
    scatter_soundings(c, 110, lambda x, y: str(rnd.choice([36, 41, 47, 52, 58, 61, 66, 72, 77, 83])), seed=52, size=32, avoid=[(X[0], X[1], 200), (Y[0], Y[1], 200)])
    c.rose(*c.M(18.5, 2.5), 300, var=-2, text=['VAR 2°W 2026'])
    def brg_of(p, q): return (math.degrees(math.atan2(q[0] - p[0], -(q[1] - p[1]))) + 360) % 360
    for cen, r, P_ in ((A, rA, (X, Y)), (B, rB, (X, Y))):
        bs = [brg_of(cen, q) for q in P_]
        for b in bs: c.parc(cen, r, b - 14, b + 14)
    c.pfix(X, 26); c.ptext((X[0] - 90, X[1] + 30), 'X', 70); c.ptext((Y[0] + 80, Y[1] - 20), 'Y', 70)
    # the rough EBL from X towards A
    e = (X[0] + (A[0] - X[0]) * 0.55, X[1] + (A[1] - X[1]) * 0.55); c.pline(X, e, 4, (26, 18)); c.ptext((e[0] - 30, e[1] + 40), '333°', 52, 63, 'rm')
    c.ptext((A[0] + rA * 0.72, A[1] - rA * 0.62), '9.3 M', 54, -40);
    c.anchors.update({'A': A, 'B': B, 'X': X, 'Y': Y, 'arcA': (A[0] + math.sin(R(brg_of(A, X) + 9)) * rA, A[1] - math.cos(R(brg_of(A, X) + 9)) * rA),
                      'arcB': (B[0] + math.sin(R(brg_of(B, X) - 9)) * rB, B[1] - math.cos(R(brg_of(B, X) - 9)) * rB), 'ebl': e})
    print('EBL from X to A', round(brg, 1), 'Y bears A', round(brg_of(Y, A), 1))
    c.finish(out, 5, 5, 5, 5, extra={'ppm': ppm, 'rB': rB, 'brg': brg})

def runfix(out):
    """Running fix with stream: 0100 line 050 through the light, the run 080 16 M + stream 170 2 M = ground 087 16.1 M,
    0300 line 330: the fix."""
    lat_c = 48.2; k = 1852 * math.cos(R(lat_c)) / 120000.0 * 1000 * 6.0
    c = Chart(lat_c, -4.85, k); c.set_origin(48.3, -4.82)
    ppm = c.ppm(48.25)
    L = c.M(0, 0)
    u = lambda b, d: (math.sin(R(b)) * d * ppm, -math.cos(R(b)) * d * ppm)
    add = lambda p, v: (p[0] + v[0], p[1] + v[1])
    P0 = add(L, u(230, 14.571)); Wt = add(P0, u(80, 16.0)); G = add(Wt, u(170, 2.0)); Fx = add(L, u(150, 9.885))
    print('fix error px', math.dist(G, Fx))
    c.land([[(48.30 + dy / 60, -4.82 + dx / (60 * math.cos(R(48.3)))) for dx, dy in
             ((-40, 5.0), (-22, 4.4), (-16, 4.0), (-11, 3.4), (-7, 2.6), (-3.5, 1.4), (-1.0, 0.5), (0, 0), (1.2, 0.6), (3.5, 1.6), (6.5, 1.0), (9.5, 2.4), (13, 2.0), (16, 3.0), (22, 2.2), (40, 3.5), (40, 20), (-40, 20))]])
    c.light(L[0], L[1] - 10, 'Fl(2) 10s 52m 23M', 30)
    c.d.text((L[0] + 330, L[1] - 300), 'Pointe du Phare', font=F('serif', 50), fill=INK, anchor='mm')
    import random
    rnd = random.Random(61)
    c.rose(*c.M(-12.5, -15.5), 300, var=-2, text=['VAR 2°W 2026'])
    # pencil: 0100 PL through the light (050/230), its transfer through the fix, 0300 PL (330/150)
    e1 = add(L, u(230, 17.0)); c.pline(L, e1); c.pend_arrow(L, e1, 1); c.ptext(add(e1, (-40, -60)), '0100', 54)
    t0, t1 = add(Fx, u(230, 3.5)), add(Fx, u(50, 7.0)); c.pline(t0, t1); c.pend_arrow(t1, t0, 2)
    e3 = add(L, u(150, 12.5)); c.pline(L, e3); c.pend_arrow(L, e3, 1); c.ptext(add(e3, (40, 40)), '0300', 54)
    c.pvec(P0, Wt, 1); c.pvec(Wt, G, 3); c.pvec(P0, G, 2)
    c.pfix(Fx, 30); c.ptext(add(Fx, (110, -40)), '0300 fix', 52, 0, 'lm')
    c.ptext(add(add(P0, u(80, 8)), (0, -60)), '080°T 16.0 M', 46, -10)
    c.ptext(add(add(P0, u(87, 9)), (0, 60)), '087°T 16.1 M', 46, -3)
    scatter_soundings(c, 120, lambda x, y: str(rnd.choice([28, 33, 39, 44, 51, 57, 62, 68, 74])), seed=62, size=32,
                      avoid=[((P0[0] + Fx[0]) / 2, (P0[1] + Fx[1]) / 2, 260), (Fx[0], Fx[1], 220), (P0[0], P0[1], 120)])
    c.anchors.update({'L': L, 'P0': P0, 'Wt': Wt, 'G': G, 'fix': Fx, 'pl1': add(L, u(230, 9.0)), 'pl3': add(L, u(150, 5.0)),
                      'tr': add(Fx, u(230, 2.5)), 'water': add(P0, u(80, 8)), 'ground': add(P0, u(87, 12)), 'stream': add(Wt, u(170, 1.0))})
    c.finish(out, 5, 5, 5, 5, extra={'ppm': ppm})

def oneline(out):
    """One position line: the light bears 020; the EP lies off it; take the point of the line nearest the EP."""
    lat_c = 50.0; k = 1852 * math.cos(R(lat_c)) / 100000.0 * 1000 * 6.0
    c = Chart(lat_c, -5.1, k); c.set_origin(50.08, -5.05)
    ppm = c.ppm(50.0)
    u = lambda b, d: (math.sin(R(b)) * d * ppm, -math.cos(R(b)) * d * ppm)
    add = lambda p, v: (p[0] + v[0], p[1] + v[1])
    L = c.M(0, 0)
    c.land([[(50.08 + dy / 60, -5.05 + dx / (60 * math.cos(R(50.08)))) for dx, dy in
             ((-40, 3.4), (-25, 2.8), (-16, 2.4), (-10, 1.6), (-5, 1.0), (-1.5, 0.5), (0, 0), (1.5, 0.6), (5, 1.4), (10, 0.8), (16, 2.0), (24, 1.6), (40, 2.6), (40, 20), (-40, 20))]])
    c.light(L[0], L[1] - 10, 'Fl 15s 44m 25M', 40)
    Q = add(L, u(200, 6.0)); EP = add(Q, u(110, 1.2))
    e = add(L, u(200, 10.5)); c.pline(L, e); c.pend_arrow(L, e, 1); c.ptext(add(e, (0, 60)), '0400  020°T', 50, 0)
    c.pep(EP, 30); c.ptext(add(EP, (80, 0)), '0400 EP', 50, 0, 'lm')
    c.pline(EP, Q, 4, (18, 14)); c.pfix(Q, 18)
    import random
    rnd = random.Random(71)
    c.rose(*c.M(-9.5, -9.0), 320, var=-2, text=['VAR 2°W 2026'])
    c.soundings([(*c.M(-6.5, -3.4), '95'), (*c.M(-8.5, -7.6), '88'), (*c.M(4.5, -4.8), '102'), (*c.M(6.8, -8.4), '110')])
    scatter_soundings(c, 110, lambda x, y: str(rnd.choice([84, 91, 97, 99, 104, 107, 113, 118])), seed=72, size=32, avoid=[(Q[0], Q[1], 200), (EP[0], EP[1], 200), ((L[0] + e[0]) / 2, (L[1] + e[1]) / 2, 100)])
    c.anchors.update({'L': L, 'Q': Q, 'EP': EP, 'line': add(L, u(200, 3.5))})
    c.finish(out, 5, 5, 5, 5, extra={'ppm': ppm})

# ---------------------------------------------------------------- dr article charts
def plotchart(lat_c, lon_c, scale, olat, olon, seed, var, rosepos, land=None, name=None, dep=(60, 160)):
    k = 1852 * math.cos(R(lat_c)) / scale * 1000 * 6.0
    c = Chart(lat_c, lon_c, k); c.set_origin(olat, olon); c.ppmv = c.ppm(olat)
    if land: c.land([[(olat + dy / 60, olon + dx / (60 * math.cos(R(olat)))) for dx, dy in land]])
    c.rose(*c.M(*rosepos), 300, var=var, text=[f"VAR {abs(var)}°{'W' if var < 0 else 'E'} 2026"])
    import random
    c.rnd = random.Random(seed); c.dep = dep
    return c

def U(c, b, d): return (math.sin(R(b)) * d * c.ppmv, -math.cos(R(b)) * d * c.ppmv)
def ADD(p, v): return (p[0] + v[0], p[1] + v[1])

def twolegs(out):
    c = plotchart(46.9, -7.1, 200000, 47.2, -6.6, 81, -4, (-6, -30))
    Fx = c.M(0, 0); D1 = ADD(Fx, U(c, 240, 24)); D2 = ADD(D1, U(c, 200, 24)); Wr = ADD(Fx, U(c, 220, 48))
    c.pline(Fx, D1); c.parrows(Fx, D1, 1); c.pline(D1, D2); c.parrows(D1, D2, 1)
    c.pline(Fx, D2, 4, (22, 16))
    c.pfix(Fx); c.pdr(D1, 240); c.pdr(D2, 200)
    c.ptext(ADD(Fx, (70, -40)), '2000 fix', 50, 0, 'lm'); c.ptext(ADD(D1, (-60, -50)), '2300', 50, 0, 'rm'); c.ptext(ADD(D2, (-60, 40)), '0200 DR', 50, 0, 'rm')
    c.ptext(ADD(ADD(Fx, U(c, 240, 12)), (-20, -60)), '240°T 24.0 M', 44, 30); c.ptext(ADD(ADD(D1, U(c, 200, 12)), (-70, 0)), '200°T 24.0 M', 44, 70)
    c.ptext(ADD(ADD(Fx, U(c, 220, 30)), (70, 10)), '220°T 45.1 M', 44, 50)
    # the wrong one: 220 48 M, crossed out
    scatter_soundings(c, 120, lambda x, y: str(c.rnd.choice([4120, 4380, 4510, 4660, 4730, 4815])), seed=82, size=32,
                      avoid=[((Fx[0] + D1[0]) / 2, (Fx[1] + D1[1]) / 2, 150), ((D1[0] + D2[0]) / 2, (D1[1] + D2[1]) / 2, 150), ((Fx[0] + D2[0]) / 2, (Fx[1] + D2[1]) / 2, 120), (Wr[0], Wr[1], 120), (D2[0], D2[1], 150)])
    c.anchors.update({'fix': Fx, 'D1': D1, 'D2': D2, 'wrong': Wr, 'res': ADD(Fx, U(c, 220, 22)), 'leg1': ADD(Fx, U(c, 240, 12)), 'leg2': ADD(D1, U(c, 200, 12))})
    c.finish(out, 10, 10, 10, 10, extra={'ppm': c.ppmv})

def ep_chart(out):
    c = plotchart(47.49, -6.22, 120000, 47.6, -6.0, 91, -3, (8.5, -15.0))
    Fx = c.M(0, 0); H = ADD(Fx, U(c, 250, 21)); Wt = ADD(Fx, U(c, 245, 21))
    t1 = ADD(Wt, U(c, 160, 1.0)); t2 = ADD(t1, U(c, 165, 1.5)); t3 = ADD(t2, U(c, 170, 1.0))
    c.pline(Fx, H, 4, (22, 16)); c.pvec(Fx, Wt, 1); c.pvec(Wt, t1, 3); c.pvec(t1, t2, 3); c.pvec(t2, t3, 3)
    c.pline(Fx, t3, 4, (8, 14))
    c.pfix(Fx); c.pep(t3, 30)
    c.ptext(ADD(Fx, (70, -40)), '0000 fix', 50, 0, 'lm'); c.ptext(ADD(t3, (-60, 60)), '0300 EP', 50, 0, 'rm')
    c.ptext(ADD(ADD(Fx, U(c, 250, 11)), (0, -55)), 'heading 250°T', 42, 20); c.ptext(ADD(ADD(Fx, U(c, 245, 11)), (20, 50)), '245°T 21.0 M', 42, 25)
    scatter_soundings(c, 120, lambda x, y: str(c.rnd.choice([118, 124, 131, 137, 142, 146, 151])), seed=92, size=32,
                      avoid=[((Fx[0] + Wt[0]) / 2, (Fx[1] + Wt[1]) / 2, 350), (t2[0], t2[1], 260), (Fx[0], Fx[1], 160)])
    c.anchors.update({'fix': Fx, 'H': ADD(Fx, U(c, 250, 15)), 'Wt': Wt, 'wt': ADD(Fx, U(c, 245, 15)), 'tide': t2, 'EP': t3})
    c.finish(out, 5, 5, 5, 5, extra={'ppm': c.ppmv})

def cts_chart(out):
    c = plotchart(50.0, -1.75, 300000, 49.66, -1.62, 101, -5, (-14, 12),
                  land=[(-60, -3.0), (-30, -2.5), (-12, -2.0), (-6, -1.6), (-2, -1.4), (0, -1.0), (2.5, -1.4), (7, -1.2), (14, -2.2), (30, -1.8), (60, -2.6), (60, -30), (-60, -30)])
    c.land([[(49.66 + dy / 60, -1.62 + dx / (60 * math.cos(R(49.66)))) for dx, dy in
             ((-60, 43.0), (-30, 42.5), (-14, 42.8), (-6, 42.4), (-1.5, 42.3), (1.5, 42.6), (7, 43.6), (16, 43.0), (30, 43.5), (60, 42.8), (60, 80), (-60, 80))]])
    A = c.M(0, 0); B = c.M(0, 41.57); S = ADD(A, U(c, 90, 6.0))
    c.pvec(A, B, 2, 5); c.pvec(A, S, 3); c.pline(S, B); c.parrows(S, B, 1, 0.4)
    brgSB = (math.degrees(math.atan2(B[0] - S[0], -(B[1] - S[1]))) + 360) % 360
    c.parc(S, 42 * c.ppmv, brgSB - 4, brgSB + 4)
    c.pfix(A, 24); c.pfix(B, 24)
    c.ptext(ADD(A, (-60, 40)), 'A', 64, 0, 'rm'); c.ptext(ADD(B, (-60, 30)), 'B', 64, 0, 'rm')
    c.ptext(ADD(A, (180, 60)), '6 M', 50); c.ptext(ADD(ADD(A, U(c, 0, 20)), (-70, 0)), '000°T 41.6 M', 46, 90)
    c.ptext(ADD(ADD(S, U(c, 352, 23)), (75, 0)), '352°T  42 M', 46, 82)
    scatter_soundings(c, 110, lambda x, y: str(c.rnd.choice([42, 48, 53, 57, 61, 66, 71, 74])), seed=102, size=30,
                      avoid=[((A[0] + B[0]) / 2, (A[1] + B[1]) / 2, 260)])
    c.anchors.update({'A': A, 'B': B, 'S': S, 'track': ADD(A, U(c, 0, 30)), 'water': ADD(S, U(c, 352, 30)), 'stream': ADD(A, U(c, 90, 3)), 'arc': ADD(S, U(c, brgSB + 3, 42))})
    print('S->B', round(brgSB, 2), math.dist(S, B) / c.ppmv)
    c.finish(out, 10, 10, 10, 10, extra={'ppm': c.ppmv, 'brgSB': brgSB})

def eperr_chart(out):
    c = plotchart(46.55, -9.0, 100000, 46.5, -8.85, 111, -3, (9.0, 6.5))
    Wd = c.M(0, 0); E0 = ADD(Wd, U(c, 90, 22)); EP = ADD(Wd, U(c, 180, 8)); Rl = ADD(Wd, U(c, 210, 8))
    c.pline(E0, Wd); c.parrows(E0, Wd, 1, 0.5)
    c.pvec(Wd, EP, 3); c.pvec(Wd, Rl, 3)
    c.pep(EP, 30); c.pfix(Rl, 28)
    c.pline(EP, Rl, 4, (16, 12))
    c.ptext(ADD(EP, (70, 30)), '1600 EP', 48, 0, 'lm'); c.ptext(ADD(Rl, (-60, 40)), '1600 fix', 48, 0, 'rm')
    c.ptext(ADD(ADD(Wd, U(c, 180, 4)), (90, 0)), '180° 8 M', 44, 90); c.ptext(ADD(ADD(Wd, U(c, 210, 4)), (-110, -10)), '210° 8 M', 44, 60)
    c.ptext(ADD(ADD(Wd, U(c, 90, 10)), (0, -50)), '270°T  70 M', 44)
    scatter_soundings(c, 120, lambda x, y: str(c.rnd.choice([4380, 4510, 4620, 4705, 4790])), seed=112, size=32,
                      avoid=[(Wd[0], Wd[1] + 4 * c.ppmv, 6 * c.ppmv), (ADD(Wd, U(c, 90, 10))[0], ADD(Wd, U(c, 90, 10))[1], 250)])
    c.anchors.update({'Wd': Wd, 'EP': EP, 'fix': Rl, 'used': ADD(Wd, U(c, 180, 4)), 'real': ADD(Wd, U(c, 210, 4)), 'gap': ((EP[0] + Rl[0]) / 2, (EP[1] + Rl[1]) / 2), 'wt': ADD(Wd, U(c, 90, 10))})
    c.finish(out, 5, 5, 5, 5, extra={'ppm': c.ppmv})

def curfix_chart(out):
    c = plotchart(49.95, -3.25, 75000, 49.98, -3.55, 121, -2, (13, -9.5))
    F0 = c.M(0, 0); DR = ADD(F0, U(c, 90, 18)); F6 = ADD(F0, U(c, 100, 20)); Hd = ADD(F0, U(c, 93, 18))
    c.pline(F0, Hd, 4, (22, 16)); c.pvec(F0, DR, 1); c.pvec(F0, F6, 2); c.pvec(DR, F6, 3)
    c.pfix(F0); c.pfix(F6); c.pdr(DR, 90)
    c.ptext(ADD(F0, (-60, -50)), '0300 fix', 50, 0, 'rm'); c.ptext(ADD(F6, (60, 60)), '0600 fix', 50, 0, 'lm'); c.ptext(ADD(DR, (60, -50)), '0600 DR', 48, 0, 'lm')
    c.ptext(ADD(ADD(F0, U(c, 90, 9)), (0, -55)), '090°T 18.0 M', 44); c.ptext(ADD(ADD(F0, U(c, 100, 9)), (0, 65)), '100°T 20.0 M', 44, -10)
    scatter_soundings(c, 120, lambda x, y: str(c.rnd.choice([52, 57, 61, 64, 68, 71, 75])), seed=122, size=32,
                      avoid=[(ADD(F0, U(c, 95, 9))[0], ADD(F0, U(c, 95, 9))[1], 9.5 * c.ppmv), (DR[0], DR[1] + 200, 400)])
    c.anchors.update({'F0': F0, 'DR': DR, 'F6': F6, 'cur': ((DR[0] + F6[0]) / 2, (DR[1] + F6[1]) / 2), 'water': ADD(F0, U(c, 90, 9)), 'ground': ADD(F0, U(c, 100, 9))})
    c.finish(out, 5, 5, 5, 5, extra={'ppm': c.ppmv})

# ---------------------------------------------------------------- plotter screens (on the Axiom front of art_checkin_nps_tex)
def _nps():
    sys.path.insert(0, HERE); import art_checkin_nps_tex as T; return T

def enc_safety(out):
    """ENC with the safety contour at 5 m drawn bold, the shallow side shaded; the settings box: 4.2 m asked for."""
    T = _nps(); SW, SH = T.SW, T.SH; im = Image.new('RGB', (SW, SH), (200, 228, 244)); d = ImageDraw.Draw(im)
    deep, mid, shal, dry = (214, 236, 250), (176, 212, 236), (130, 186, 222), (156, 190, 130)
    d.rectangle([0, 0, SW, SH], fill=deep)
    blob = lambda cx, cy, rx, ry, sd: [(cx + math.cos(t) * rx * (0.85 + 0.2 * math.sin(3 * t + sd)), cy + math.sin(t) * ry * (0.85 + 0.18 * math.cos(2 * t + sd))) for t in [i * math.pi / 40 for i in range(80)]]
    c10 = blob(560, 560, 520, 330, 0.3); c5 = blob(560, 560, 380, 230, 0.9); c2 = blob(540, 560, 220, 130, 1.4)
    d.polygon(c10, fill=mid); d.polygon(c5, fill=shal); d.polygon(c2, fill=(110, 170, 210)); d.polygon(blob(520, 560, 80, 50, 2.0), fill=dry)
    d.line(c10 + [c10[0]], fill=(90, 110, 130), width=3); d.line(c2 + [c2[0]], fill=(90, 110, 130), width=3)
    d.line(c5 + [c5[0]], fill=(20, 24, 30), width=12)          # the safety contour, bold
    for x, y, t in ((560, 470, '3.4'), (720, 600, '4.1'), (380, 640, '2.6'), (1010, 300, '12'), (1150, 760, '18'), (240, 220, '14'), (900, 900, '9.6'), (820, 460, '6.2')):
        d.text((x, y), t, font=F('ital', 46), fill=(10, 30, 60) if float(t) <= 5 else (60, 80, 110), anchor='mm')
    d.text((1080, 470), '10', font=F('bold', 34), fill=(90, 110, 130), anchor='mm'); d.text((930, 640), '5', font=F('bold', 40), fill=(20, 24, 30), anchor='mm')
    # own boat heading 300, a look-ahead box ahead
    bx, by = 1320, 820; T.own_boat(d, bx, by, 300, 1.3)
    a = R(300); ex, ey = bx + math.sin(a) * 520, by - math.cos(a) * 520
    d.line([(bx, by), (ex, ey)], fill=(17, 17, 17), width=6)
    T.topbar(d, [('CHART · ENC', (230, 236, 240), None), ('Safety contour 5 m', (255, 214, 60), None)])
    T.databox(d, SW - 520, 140, 490, [('DEPTH', '9.8 m', (230, 236, 240)), ('SOG', '18.0 kn', (230, 236, 240))], h=150)
    d.rounded_rectangle([60, SH - 400, 780, SH - 60], 20, fill=(18, 22, 28))
    for i, (k_, v) in enumerate((('Safety contour', '4.2 m'), ('Bold contour', '5 m'), ('Look-ahead', '3.0 NM'))):
        y = SH - 340 + i * 100; d.text((100, y), k_, font=F('bold', 44), fill=(150, 170, 186), anchor='lm'); d.text((740, y), v, font=F('dina', 56), fill=(255, 214, 60) if i == 1 else (230, 236, 240), anchor='rm')
    T.scalebar(d, SW - 340, SH - 60, 260, '0.5 NM')
    T.front(im, out, {'contour': (c5[10][0], c5[10][1]), 'settings': (420, SH - 240), 'boat': (bx, by - 60), 'shallow': (560, 470)})

def xte_screen(out):
    """Zoomed in on the boat: the route from A (off the screen, left) to B (off it, right), the boat 4.0 M left of it."""
    T = _nps(); SW, SH = T.SW, T.SH; im = Image.new('RGB', (SW, SH), (214, 236, 250)); d = ImageDraw.Draw(im)
    s = 30.0; y0 = 760; bx = 520; by = y0 - 4.0 * s; xa = bx - 80 * s
    d.line([(0, y0), (SW, y0)], fill=(200, 30, 140), width=8)
    for xx in range(150, SW - 500, 360): d.polygon([(xx + 26, y0), (xx - 8, y0 - 18), (xx - 8, y0 + 18)], fill=(200, 30, 140))
    d.text((SW - 560, y0 + 50), 'to B  48 NM', font=F('bold', 46), fill=(200, 30, 140), anchor='rm')
    for k in range(0, 60):         # the track sailed, dotted, from A far off to the left
        x = bx - k * 14; y = by + (y0 - by) * (bx - x) / (bx - xa)
        if x > 0: d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(40, 40, 40))
    T.own_boat(d, bx, by, 87, 1.3)
    d.line([(bx, by + 46), (bx, y0 - 8)], fill=(200, 30, 40), width=7)
    d.text((bx + 24, (by + y0) / 2 + 18), 'XTE 4.0 NM', font=F('bold', 46), fill=(200, 30, 40), anchor='lm')
    for x, y, t in ((300, 350, '112'), (700, 980, '96'), (1050, 360, '104'), (1150, 920, '99'), (180, 900, '120')): T.sounding(d, x, y, t)
    T.topbar(d, [('NAVIGATE TO B', (230, 236, 240), None), ('Route', (160, 176, 190), None)])
    T.databox(d, SW - 520, 130, 490, [('XTE', '4.0 NM L', (255, 90, 80)), ('DTW', '48.2 NM', (230, 236, 240)), ('BTW', '095°T', (230, 236, 240)), ('COG', '087°T', (230, 236, 240))], h=150)
    T.scalebar(d, 40, SH - 50, int(2 * s), '2 NM')
    T.front(im, out, {'xte': (SW - 275, 130 + 16 + 76), 'boat': (bx, by - 60), 'route': (bx + 300, y0), 'bar': (bx, (by + y0) / 2)})

def lcd(out, title, value, unit, sub=''):
    w, h = 800, 800; im = Image.new('RGB', (w, h), (6, 8, 10)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 120], fill=(24, 30, 38)); d.text((w / 2, 62), title, font=F('bold', 70), fill=(235, 238, 240), anchor='mm')
    d.text((w / 2 - 10, 420), value, font=F('dina', 300 if len(value) > 4 else 360), fill=(250, 250, 250), anchor='mm')
    d.text((w - 50, 640), unit, font=F('bold', 84), fill=(200, 205, 210), anchor='rm')
    if sub: d.text((50, 720), sub, font=F('bold', 52), fill=(150, 160, 170), anchor='lm')
    im.save(out + '.png')

def fuel_mfd(out):
    """A motor yacht's engine page: two engines, fuel flow, speed, l/M and fuel left."""
    w, h = 1600, 1000; im = Image.new('RGB', (w, h), (10, 12, 16)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 110], fill=(24, 30, 38)); d.text((40, 55), 'FUEL', font=F('bold', 64), fill=(235, 238, 240), anchor='lm')
    d.text((w - 40, 55), 'Range at this speed', font=F('bold', 44), fill=(160, 176, 190), anchor='rm')
    cells = [('SOG', '15.0', 'kn', (230, 236, 240)), ('FLOW', '150', 'l/h', (255, 214, 60)), ('ECON', '10.0', 'l/M', (230, 236, 240)),
             ('FUEL', '1800', 'l usable', (230, 236, 240)), ('RANGE', '180', 'M', (120, 220, 140)), ('TIME', '12.0', 'h', (230, 236, 240))]
    for i, (k_, v, u_, col) in enumerate(cells):
        x = 30 + (i % 3) * 520; y = 140 + (i // 3) * 420
        d.rounded_rectangle([x, y, x + 500, y + 400], 18, fill=(22, 26, 32))
        d.text((x + 30, y + 50), k_, font=F('bold', 48), fill=(150, 170, 186), anchor='lm')
        d.text((x + 470, y + 220), v, font=F('dina', 170), fill=col, anchor='rm'); d.text((x + 470, y + 345), u_, font=F('bold', 48), fill=(170, 176, 182), anchor='rm')
    im.save(out + '.png'); json.dump({'w_px': w, 'h_px': h, 'anchors': {'flow': (800, 330), 'range': (800, 750), 'fuel': (280, 750)}}, open(out + '.json', 'w'))

def steel_rule(out):
    """A 300 mm steel rule, 25 mm wide, 10 px/mm: mm ticks along one edge, numbers every cm (RGBA print)."""
    pm = 10; w, h = 308 * pm, 25 * pm; im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); ink = (18, 18, 20, 255)
    for mm in range(0, 301):
        x = 4 * pm + mm * pm; L = 9 if mm % 10 == 0 else 6 if mm % 5 == 0 else 4
        d.line([(x, h), (x, h - L * pm)], fill=ink, width=3 if mm % 10 == 0 else 2)
        if mm % 10 == 0 and mm: d.text((x, h - 14 * pm), str(mm // 10), font=F('bold', 60), fill=ink, anchor='mm')
    d.text((60 * pm, 5 * pm), 'STAINLESS  ·  mm', font=F('bold', 44), fill=(18, 18, 20, 200), anchor='mm')
    im.save(out + '.png')

def clock_face(out, hh, mm):
    s = 800; im = Image.new('RGB', (s, s), (246, 242, 230)); d = ImageDraw.Draw(im); c = s / 2
    for i in range(60):
        t = R(i * 6); r0 = c - (60 if i % 5 == 0 else 34)
        d.line([(c + math.sin(t) * r0, c - math.cos(t) * r0), (c + math.sin(t) * (c - 16), c - math.cos(t) * (c - 16))], fill=INK, width=10 if i % 5 == 0 else 4)
    for i in range(1, 13):
        t = R(i * 30); d.text((c + math.sin(t) * (c - 120), c - math.cos(t) * (c - 120)), str(i), font=F('serif', 84), fill=INK, anchor='mm')
    ah = R((hh % 12) * 30 + mm * 0.5); am = R(mm * 6)
    d.line([(c, c), (c + math.sin(ah) * 200, c - math.cos(ah) * 200)], fill=INK, width=26)
    d.line([(c, c), (c + math.sin(am) * 310, c - math.cos(am) * 310)], fill=INK, width=16)
    d.ellipse([c - 22, c - 22, c + 22, c + 22], fill=INK)
    im.save(out + '.png')

def calc_lcd(out, text):
    w, h = 680, 260; im = Image.new('RGB', (w, h), (176, 186, 168)); d = ImageDraw.Draw(im)
    d.text((w - 30, h / 2 + 10), text, font=F('dina', 170), fill=(30, 34, 30), anchor='rm'); im.save(out + '.png')

COMMON = {'rule': steel_rule, 'clock-0415': lambda o: clock_face(o, 4, 15), 'calc-7.33': lambda o: calc_lcd(o, '7.333'),
          'calc-88.7': lambda o: calc_lcd(o, '88.69'), 'calc-213': lambda o: calc_lcd(o, '32.66')}

JOBS = {
    'charts': {'merc': merc, 'biscay': biscay, 'bank': bank, 'breton-chart': breton_chart, 'breton': breton, 'corrections': corrections, 'nm': nm_booklet,
               'midlat': midlat, 'mercsail': mercsail, 'nories': nories, 'log-speed': log_speed, 'enc': enc_safety},
    'compass': {'rose-var': rose_var, 'radar-chart': radar_chart, 'runfix': runfix, 'oneline': oneline,
                'lcd-sat': lambda o: lcd(o, 'HEADING', '240°', 'T', 'satellite compass'), 'lcd-hdg': lambda o: lcd(o, 'HEADING', '240°', 'T', 'sat compass')},
    'dr': {'twolegs': twolegs, 'log-dr': log_dr, 'ep': ep_chart, 'cts': cts_chart, 'eperr': eperr_chart, 'curfix': curfix_chart, 'breton': breton,
           'xte': xte_screen, 'fuel': fuel_mfd},
}

if __name__ == '__main__':
    art = sys.argv[1]; J = {**COMMON, **JOBS[art]}; names = sys.argv[2:] or list(JOBS[art])
    od = os.path.join(ARTS, art, 'tex'); os.makedirs(od, exist_ok=True)
    for n in names: J[n](os.path.join(od, n)); print('tex', art, n)
