# Textures for the Yachtmaster Offshore renders of art_yof_pilotage.py (and the shared helpers the tides and weather
# texture scripts import): plotter and radar screens on the Raymarine Axiom's front (art_checkin_nps_tex.front: the
# model's own front texture 3x up, the screen pasted on its glass, <name>.json with the label anchors in the 828 x 481
# frame), and paper: a passage chart, notebooks, a night order book, a log book.
# System Python with Pillow; the Blender scripts run it when a texture is missing (or with --retex), into the
# article's own folder, figure-style/articles/yachtmaster-offshore/<article>/tex/<name>.png.
#   python3 docs/design/blender/art_yof_pilotage_tex.py <outdir> [name ...]     (no names: all of them)
import os, sys, math, json, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from art_checkin_nps_tex import F, front, chart_base, topbar, own_boat, sounding, databox, scalebar, SW, SH, SEA, SEA2, LAND, COAST

PENCIL, INKB = (70, 70, 76), (28, 40, 92)
def hand(n): return F('hand', n)

# ---------------------------------------------------------------- radar screens (SW x SH, dark)
RBG, RING, ECHO = (4, 10, 22), (40, 120, 150), (255, 200, 40)
def radar_base(cx=None, cy=None, R=470, rings=4, heading=0.0, north_up=True):
    im = Image.new('RGB', (SW, SH), RBG); d = ImageDraw.Draw(im)
    cx = SW * 0.42 if cx is None else cx; cy = SH * 0.53 if cy is None else cy
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(6, 16, 32))
    for k in range(1, rings + 1):
        r = R * k / rings; d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=RING, width=3)
    for a in range(0, 360, 30):
        t = math.radians(a); d.line([(cx, cy), (cx + R * math.sin(t), cy - R * math.cos(t))], fill=(16, 48, 66), width=2)
    for a in range(0, 360, 10):
        t = math.radians(a); r0 = R - (22 if a % 30 == 0 else 12)
        d.line([(cx + r0 * math.sin(t), cy - r0 * math.cos(t)), (cx + R * math.sin(t), cy - R * math.cos(t))], fill=(110, 160, 180), width=3)
    for a in range(0, 360, 30):
        t = math.radians(a); d.text((cx + (R + 34) * math.sin(t), cy - (R + 34) * math.cos(t)), f'{a:03d}', font=F('bold', 28), fill=(130, 170, 190), anchor='mm')
    h = math.radians(heading)
    d.line([(cx, cy), (cx + R * math.sin(h), cy - R * math.cos(h))], fill=(225, 232, 240), width=4)
    return im, d, (cx, cy, R)

def glow_layer(): g = Image.new('RGB', (SW, SH), (0, 0, 0)); return g, ImageDraw.Draw(g)
def merge_glow(im, g, blur=2.0):
    g = g.filter(ImageFilter.GaussianBlur(blur)); m = g.convert('L').point(lambda v: 255 if v > 10 else v * 25)
    return Image.composite(g, im, m)

def speckle(g, cx, cy, R, n, rmax=1.0, rnd=None, col=(150, 120, 30), size=3):
    rnd = rnd or random.Random(3)
    for _ in range(n):
        r = math.sqrt(rnd.random()) * R * rmax; t = rnd.random() * math.tau; x, y = cx + r * math.sin(t), cy - r * math.cos(t)
        g.ellipse([x - size, y - size, x + size, y + size], fill=col)

def blob_coast(g, pts, width=26, col=ECHO, rnd=None):
    """A coast echo: a thick bright ragged band along the polyline pts (near edge sharp)."""
    rnd = rnd or random.Random(5)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0); n = max(2, int(L / 6))
        for k in range(n):
            t = k / n; x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t; w = width * (0.6 + 0.8 * rnd.random())
            g.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=col)

def echo(g, x, y, w=26, h=18, col=ECHO): g.ellipse([x - w / 2, y - h / 2, x + w / 2, y + h / 2], fill=col)

def side_panel(d, x, rows, title=None, y=130, w=None, h=118):
    w = w or SW - x - 30
    if title: d.text((x + 10, y - 40), title, font=F('bold', 40), fill=(170, 190, 205), anchor='lm')
    databox(d, x, y, w, rows, h)

def radar_topbar(d, items): topbar(d, items)

def p8_radar(out):
    """Radar at 24 NM, north up: the cliff 24 M off to the NE paints at the edge, the low coast beyond it does not;
    a ship 19 M off to the west."""
    im, d, (cx, cy, R) = radar_base(rings=4)
    k = R / 24.0
    g, gd = glow_layer(); rnd = random.Random(8)
    speckle(gd, cx, cy, R, 300, 0.12, rnd, (120, 100, 30), 3)
    # the cliffed island 24 M at 040: only its high face paints, a short arc at the edge
    a0 = math.radians(40)
    pts = [(cx + (24 * k - 4 + 6 * math.sin(i)) * math.sin(a0 + (i - 3) * 0.05), cy - (24 * k - 4 + 6 * math.sin(i)) * math.cos(a0 + (i - 3) * 0.05)) for i in range(7)]
    blob_coast(gd, pts, 30, ECHO, rnd)
    sx, sy = cx + 19 * k * math.sin(math.radians(285)), cy - 19 * k * math.cos(math.radians(285)); echo(gd, sx, sy, 22, 16)
    im = merge_glow(im, g, 1.6); d = ImageDraw.Draw(im)
    # the chart overlay outline of the low coast that does not paint (dotted)
    for i in range(0, 40):
        a = math.radians(-10 + i * 2.2); r = 30 * k
        x, y = cx + r * math.sin(a), cy - r * math.cos(a)
        if math.hypot(x - cx, y - cy) < R - 4 and i % 2 == 0: d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(90, 110, 120))
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(230, 236, 240))
    radar_topbar(d, [('RADAR', (230, 236, 240), None), ('N-UP  24 NM', (150, 175, 190), None), ('Rings 6 NM', (150, 175, 190), None)])
    side_panel(d, SW - 470, [('Scanner', '9 m', (230, 236, 240)), ('Range', '24 NM', (255, 214, 60)), ('Target', '19 NM', (230, 236, 240))], 'RADAR')
    front(im, out, {'cliff': (pts[3][0], pts[3][1] - 30), 'ship': (sx, sy - 20), 'own': (cx, cy)})

def p9_radar(out):
    """Setting up: the picture tuned, gain up to a faint speckle, a little sea clutter left round the centre, a rain
    squall to the SW with rain control off; the GAIN / SEA / RAIN sliders on the right."""
    im, d, (cx, cy, R) = radar_base(rings=4, heading=0)
    g, gd = glow_layer(); rnd = random.Random(11)
    speckle(gd, cx, cy, R, 1500, 1.0, rnd, (70, 60, 20), 2)                    # gain: a faint speckle all over
    for _ in range(500):                                                        # sea clutter, a little, near the centre
        r = rnd.random() ** 2 * R * 0.16; t = rnd.random() * math.tau; x, y = cx + r * math.sin(t), cy - r * math.cos(t)
        gd.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(170, 140, 35))
    sq = (cx - R * 0.42, cy + R * 0.38)                                          # a rain squall, soft and grainy
    for _ in range(2600):
        r = abs(rnd.gauss(0, 1)) * 70; t = rnd.random() * math.tau; x, y = sq[0] + r * 1.4 * math.sin(t), sq[1] - r * math.cos(t)
        gd.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(120, 95, 28))
    for (b, rr) in ((25, 0.55), (300, 0.72), (140, 0.4)):
        t = math.radians(b); echo(gd, cx + R * rr * math.sin(t), cy - R * rr * math.cos(t), 20, 14)
    im = merge_glow(im, g, 1.2); d = ImageDraw.Draw(im)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(230, 236, 240))
    radar_topbar(d, [('RADAR', (230, 236, 240), None), ('H-UP  12 NM', (150, 175, 190), None), ('TUNE AUTO', (120, 220, 140), None)])
    x0 = SW - 500; d.rounded_rectangle([x0, 130, SW - 30, SH - 60], 18, fill=(18, 22, 28))
    for i, (k, v, col, frac) in enumerate((('GAIN', '72', (255, 214, 60), 0.72), ('SEA', '35', (230, 236, 240), 0.35), ('RAIN', 'OFF', (230, 236, 240), 0.0), ('TUNE', 'AUTO', (120, 220, 140), 0.6))):
        y = 200 + i * 205
        d.text((x0 + 30, y), k, font=F('bold', 44), fill=(150, 170, 186), anchor='lm'); d.text((SW - 60, y), v, font=F('dina', 60), fill=col, anchor='rm')
        d.rounded_rectangle([x0 + 30, y + 50, SW - 60, y + 74], 12, fill=(46, 52, 60))
        d.rounded_rectangle([x0 + 30, y + 50, x0 + 30 + (SW - 90 - x0) * max(frac, 0.02), y + 74], 12, fill=col)
    front(im, out, {'gain': (x0 + 240, 200), 'sea': (x0 + 240, 405), 'rain': (x0 + 240, 610), 'clutter': (cx, cy - 40), 'squall': (sq[0], sq[1] - 80)})

def p10_radar(out):
    """Clearing range: head up on 000, 1.5 NM range; the cliff paints to the east, the reef off it does not;
    the VRM set at 1.00 NM, the cliff echo just outside it."""
    im, d, (cx, cy, R) = radar_base(rings=3, heading=0)
    k = R / 1.5; g, gd = glow_layer(); rnd = random.Random(21)
    speckle(gd, cx, cy, R, 220, 0.1, rnd, (150, 120, 30), 3)
    pts = []
    for i in range(30):                    # the cliff face: x = 1.05..1.3 M east, curving away north and south
        yy = -1.6 + i * 0.11; xx = 1.08 + 0.12 * yy * yy
        pts.append((cx + xx * k, cy - yy * k))
    blob_coast(gd, pts, 30, ECHO, rnd)
    im = merge_glow(im, g, 1.5); d = ImageDraw.Draw(im)
    # land behind the face: a dark fill clipped to the scope
    mask = Image.new('L', (SW, SH), 0); md = ImageDraw.Draw(mask); md.ellipse([cx - R, cy - R, cx + R, cy + R], fill=255)
    land = Image.new('RGB', (SW, SH), (60, 48, 20)); lm = Image.new('L', (SW, SH), 0); ld = ImageDraw.Draw(lm)
    ld.polygon([(p[0] + 18, p[1]) for p in pts] + [(SW, pts[-1][1]), (SW, pts[0][1])], fill=110)
    im = Image.composite(land, im, Image.composite(lm, Image.new('L', (SW, SH), 0), mask)); d = ImageDraw.Draw(im)
    for a in range(0, 360, 6):          # the VRM: a dashed ring at 1.00 NM
        t0, t1 = math.radians(a), math.radians(a + 3.5); r = 1.0 * k
        d.line([(cx + r * math.sin(t0), cy - r * math.cos(t0)), (cx + r * math.sin(t1), cy - r * math.cos(t1))], fill=(90, 230, 255), width=6)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(230, 236, 240))
    radar_topbar(d, [('RADAR', (230, 236, 240), None), ('H-UP  1.5 NM', (150, 175, 190), None)])
    side_panel(d, SW - 470, [('VRM', '1.00 NM', (90, 230, 255)), ('Heading', '000°', (230, 236, 240)), ('Cliff', '1.06 NM', (255, 214, 60))], 'CLEARING RANGE')
    rx, ry = cx + 0.95 * k, cy + 0.15 * k
    front(im, out, {'vrm': (cx + 0.71 * k, cy - 0.71 * k), 'cliff': pts[18], 'reef': (rx, ry), 'own': (cx, cy)})

def p11_arpa(out):
    """ARPA at 0206, north up, 6 NM: own ship heading 180, the target 191° 3.9 NM with its plots, its relative
    motion line through the CPA, its true vector 081° 10.5 kn; the data box CPA 2.1 NM, TCPA 13 min."""
    im, d, (cx, cy, R) = radar_base(rings=3, heading=180)
    k = R / 6.0; P = lambda brg, rng: (cx + rng * k * math.sin(math.radians(brg)), cy - rng * k * math.cos(math.radians(brg)))
    g, gd = glow_layer(); rnd = random.Random(31); speckle(gd, cx, cy, R, 200, 0.1, rnd, (150, 120, 30), 3)
    p0, p1 = P(200, 5.2), P(191, 3.9)
    for t in range(0, 7):                       # the echo's trail: one dot a minute
        x = p0[0] + (p1[0] - p0[0]) * t / 6; y = p0[1] + (p1[1] - p0[1]) * t / 6; gd.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(120, 100, 30))
    echo(gd, *p1, 30, 20)
    im = merge_glow(im, g, 1.4); d = ImageDraw.Draw(im)
    # relative motion line extended past the CPA, the CPA point, the true vector (6 min) from the target
    ux, uy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(ux, uy); ux, uy = ux / L, uy / L
    cpa = P(135, 2.14)
    for s in range(0, int(L * 4.2), 18): d.line([(p0[0] + ux * s, p0[1] + uy * s), (p0[0] + ux * (s + 10), p0[1] + uy * (s + 10))], fill=(255, 140, 60), width=4)
    d.ellipse([cpa[0] - 10, cpa[1] - 10, cpa[0] + 10, cpa[1] + 10], outline=(255, 140, 60), width=4)
    tv = (p1[0] + 10.5 * 0.2 * k * math.sin(math.radians(81)), p1[1] - 10.5 * 0.2 * k * math.cos(math.radians(81)))
    d.line([p1, tv], fill=(90, 230, 255), width=6)
    d.rectangle([p1[0] - 24, p1[1] - 24, p1[0] + 24, p1[1] + 24], outline=(90, 230, 255), width=4)
    ov = (cx, cy + 9 * 0.2 * k); d.line([(cx, cy), ov], fill=(230, 236, 240), width=6)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(230, 236, 240))
    for p, t in ((p0, '0200'), (p1, '0206')): d.text((p[0] - 40, p[1]), t, font=F('bold', 30), fill=(200, 210, 220), anchor='rm')
    radar_topbar(d, [('RADAR', (230, 236, 240), None), ('N-UP  6 NM', (150, 175, 190), None), ('ARPA', (120, 220, 140), None), ('02:06', (230, 236, 240), None)])
    side_panel(d, SW - 470, [('BRG', '191°', (230, 236, 240)), ('RNG', '3.9 NM', (230, 236, 240)), ('CPA', '2.1 NM', (255, 214, 60)), ('TCPA', '13 min', (255, 214, 60)), ('COG', '081°', (90, 230, 255)), ('SOG', '10.5 kn', (90, 230, 255))], 'TARGET 1', h=104)
    front(im, out, {'p0': p0, 'p1': p1, 'cpa': cpa, 'box': (SW - 235, 380), 'own': (cx, cy), 'tv': tv})

def p12_gnss(out):
    """Jamming: the chart with the own-boat track jumping about, SOG 41 kn; the GNSS page: five satellites,
    HDOP 7.8, a red POSITION UNRELIABLE banner."""
    im, d = chart_base(); W2 = 1000
    d.polygon([(0, SH), (0, 820), (300, 760), (560, 860), (800, 940), (W2, 980), (W2, SH)], fill=LAND, outline=COAST)
    for x, y, t in ((150, 300, '62'), (520, 260, '71'), (800, 420, '58'), (320, 600, '44'), (700, 700, '38')): sounding(d, x, y, t)
    rnd = random.Random(7); pts = [(260, 640)]
    for i in range(14): pts.append((pts[-1][0] + 30 + rnd.uniform(-60, 120), pts[-1][1] - 30 + rnd.uniform(-110, 70)))
    d.line(pts, fill=(200, 30, 40), width=6)
    for p in pts: d.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7], fill=(200, 30, 40))
    own_boat(d, *pts[-1], 60, 1.2)
    d.line([(260, 640), (480, 520)], fill=(17, 17, 17), width=5)                            # the steady DR line
    # the GNSS status pane on the right
    d.rectangle([W2, 0, SW, SH], fill=(14, 18, 24))
    cx, cy, R = W2 + 360, 470, 250
    for r in (R, R * 0.66, R * 0.33): d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(70, 90, 110), width=3)
    d.line([(cx - R, cy), (cx + R, cy)], fill=(50, 66, 80), width=2); d.line([(cx, cy - R), (cx, cy + R)], fill=(50, 66, 80), width=2)
    for az, el, n in ((40, 30, '07'), (150, 20, '13'), (220, 60, '21'), (300, 15, '28'), (90, 70, '05')):
        r = R * (1 - el / 90); x, y = cx + r * math.sin(math.radians(az)), cy - r * math.cos(math.radians(az))
        d.ellipse([x - 24, y - 24, x + 24, y + 24], fill=(230, 160, 40)); d.text((x, y), n, font=F('bold', 26), fill=(20, 20, 20), anchor='mm')
    for i, h in enumerate((22, 14, 30, 9, 18)):
        x = W2 + 140 + i * 90; d.rectangle([x, 860 - h * 4, x + 56, 860], fill=(230, 160, 40)); d.text((x + 28, 890), str(h), font=F('bold', 26), fill=(150, 170, 186), anchor='mm')
    d.text((W2 + 40, 160), 'GNSS', font=F('bold', 44), fill=(230, 236, 240), anchor='lm')
    d.text((SW - 40, 160), 'Sats 5', font=F('bold', 44), fill=(230, 236, 240), anchor='rm')
    d.text((W2 + 40, 960), 'HDOP', font=F('bold', 40), fill=(150, 170, 186), anchor='lm'); d.text((SW - 40, 970), '7.8', font=F('dina', 80), fill=(255, 80, 70), anchor='rm')
    topbar(d, [('POSITION UNRELIABLE', (255, 255, 255), (200, 30, 40)), ('SOG 41.0 kn', (255, 120, 110), None), ('COG ---', (200, 208, 214), None)])
    front(im, out, {'track': pts[3], 'hdop': (SW - 150, 940), 'sats': (cx, cy - R), 'sog': (900, 48), 'banner': (300, 48)})

def p13_nofix(out):
    """GNSS lost: the chart frozen, NO FIX banner, the last fix ringed with its time; the radar overlay still paints."""
    im, d = chart_base()
    d.polygon([(SW, 0), (SW, SH), (1250, SH), (1180, 760), (1230, 520), (1150, 300), (1200, 0)], fill=LAND, outline=COAST)
    for x, y, t in ((300, 300, '48'), (700, 220, '52'), (900, 600, '31'), (420, 760, '40'), (1050, 900, '17')): sounding(d, x, y, t)
    g = Image.new('RGB', (SW, SH), (0, 0, 0)); gd = ImageDraw.Draw(g)
    pts = [(1170 + 18 * math.sin(i * 0.7), 40 + i * 70) for i in range(15)]; blob_coast(gd, pts, 40, (255, 120, 210))
    g = g.filter(ImageFilter.GaussianBlur(2)); im = Image.composite(g, im, g.convert('L').point(lambda v: 160 if v > 10 else 0)); d = ImageDraw.Draw(im)
    bx, by = 620, 520; own_boat(d, bx, by, 20, 1.2, (90, 90, 96))
    d.ellipse([bx - 70, by - 70, bx + 70, by + 70], outline=(200, 30, 40), width=6)
    d.rounded_rectangle([bx + 90, by - 60, bx + 420, by + 10], 10, fill=(255, 255, 255), outline=(200, 30, 40), width=3)
    d.text((bx + 255, by - 25), 'last fix 0412', font=F('bold', 40), fill=(200, 30, 40), anchor='mm')
    topbar(d, [('NO FIX', (255, 255, 255), (200, 30, 40)), ('GNSS lost', (230, 236, 240), None), ('AIS: no position', (255, 180, 170), None)])
    databox(d, SW - 470, SH - 420, 440, [('HDG', '047°M', (230, 236, 240)), ('LOG', '1243.6', (230, 236, 240)), ('DEPTH', '38 m', (230, 236, 240))])
    front(im, out, {'nofix': (110, 48), 'boat': (bx, by - 80), 'radar': pts[11], 'data': (SW - 250, SH - 330)})

def p2_grib(out):
    """GRIB on the plotter: model B for Sat 1200, the cold front over the route's far end, the timeline below."""
    im, d = chart_base()
    d.polygon([(0, 0), (520, 0), (430, 180), (260, 260), (0, 300)], fill=LAND, outline=COAST)
    d.polygon([(SW, SH), (SW, 640), (1450, 720), (1280, 900), (1200, SH)], fill=LAND, outline=COAST)
    # wind colours and barbs: SW 20 kn ahead of the front (green-yellow), W 30-35 behind it (orange-red)
    ov = Image.new('RGBA', (SW, SH), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for x in range(0, SW, 60):
        for y in range(100, SH - 150, 60):
            fx = 1150 + (y - 100) * -0.35
            col = (240, 120, 40, 90) if x < fx else (140, 210, 90, 80)
            od.rectangle([x, y, x + 60, y + 60], fill=col)
    im = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB'); d = ImageDraw.Draw(im)
    for x in range(90, SW, 180):
        for y in range(190, SH - 180, 170):
            fx = 1150 + (y - 100) * -0.35; brg = 260 if x < fx else 220
            a = math.radians(brg + 180); L = 70
            d.line([(x, y), (x + L * math.sin(a), y - L * math.cos(a))], fill=(30, 30, 40), width=5)
            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(30, 30, 40))
    fr = [(1150 + (y - 100) * -0.35, y) for y in range(100, SH - 150, 20)]
    d.line(fr, fill=(30, 70, 200), width=10)
    for i in range(1, len(fr) - 1, 3):
        x, y = fr[i]; d.polygon([(x - 18, y - 14), (x - 18, y + 14), (x - 48, y)], fill=(30, 70, 200))
    d.line([(300, 260), (1500, 700)], fill=(200, 30, 40), width=6)                          # the route
    for p in ((300, 260), (1500, 700)): d.ellipse([p[0] - 14, p[1] - 14, p[0] + 14, p[1] + 14], outline=(200, 30, 40), width=6)
    topbar(d, [('GRIB', (230, 236, 240), None), ('Model B', (255, 214, 60), None), ('Sat 12:00', (230, 236, 240), None)])
    d.rectangle([0, SH - 150, SW, SH], fill=(18, 22, 28))
    x0, x1 = 80, SW - 80
    d.line([(x0, SH - 75), (x1, SH - 75)], fill=(120, 136, 150), width=6)
    for i, t in enumerate(('Fri 12', 'Fri 18', 'Sat 00', 'Sat 06', 'Sat 12', 'Sat 18')):
        x = x0 + (x1 - x0) * i / 5; d.line([(x, SH - 95), (x, SH - 55)], fill=(120, 136, 150), width=4); d.text((x, SH - 120), t, font=F('bold', 30), fill=(160, 176, 190), anchor='mm')
    xb = x0 + (x1 - x0) * 4 / 5; d.ellipse([xb - 20, SH - 95, xb + 20, SH - 55], fill=(255, 214, 60))
    front(im, out, {'front': fr[14], 'route': (900, 480), 'slider': (xb, SH - 110)})

# ---------------------------------------------------------------- paper
def paper(w, h, tint=(247, 245, 238)): im = Image.new('RGB', (w, h), tint); return im, ImageDraw.Draw(im)
def ruled(d, w, h, top=200, step=86, margin=150, col=(196, 210, 228)):
    for y in range(top, h - 60, step): d.line([(40, y), (w - 40, y)], fill=col, width=3)
    d.line([(margin, 0), (margin, h)], fill=(226, 150, 150), width=3)

def written(d, x, y, lines, size=58, step=86, col=INKB, font='hand'):
    for i, t in enumerate(lines):
        d.text((x, y + i * step), t, font=F(font, size), fill=col, anchor='ls')
    return [y + i * step for i in range(len(lines))]

def save(im, out, anchors=None, blur=0.5):
    im.filter(ImageFilter.GaussianBlur(blur)).save(out + '.png')
    if anchors is not None: json.dump(anchors, open(out + '.json', 'w'))

def p1_chart(out):
    """A passage chart, the crossing pencilled on it: departure, waypoints off the lanes, a port of refuge ringed."""
    w, h = 2400, 1600; im, d = paper(w, h, (236, 243, 244))
    for poly in ([(0, 0), (900, 0), (820, 200), (600, 330), (380, 380), (200, 520), (0, 560)], [(w, h), (w, 900), (2050, 960), (1820, 1130), (1700, 1360), (1500, h)]):
        for k, col in ((120, (214, 232, 240)), (50, (196, 224, 236))):
            d.polygon([(x + (k if x > w / 2 else -k) * 0.4, y + (k if y > h / 2 else -k) * 0.5) for x, y in poly], fill=col)
        d.polygon(poly, fill=(243, 229, 178), outline=(110, 90, 50)); d.line(poly + [poly[0]], fill=(90, 72, 40), width=4)
    rnd = random.Random(2)
    for _ in range(70):
        x, y = rnd.uniform(300, 2200), rnd.uniform(300, 1400)
        if (x < 900 and y < 600) or (x > 1500 and y > 900): continue
        d.text((x, y), str(rnd.randint(30, 95)), font=F('ital', 30), fill=(60, 70, 80), anchor='mm')
    # the TSS lanes in magenta, across the middle
    mg = (190, 40, 130)
    for y in (700, 760, 820, 880):
        for x in range(0, w, 50): d.line([(x, y + (x - 1200) * 0.12), (x + 28, y + (x + 28 - 1200) * 0.12)], fill=mg, width=4 if y in (760, 820) else 3)
    d.text((1900, 690), 'TSS', font=F('bold', 42), fill=mg, anchor='mm')
    # pencil: the track, waypoints, the port of refuge
    wps = [(420, 420), (760, 560), (1060, 980), (1700, 1180)]
    d.line(wps, fill=PENCIL, width=5)
    for i, (x, y) in enumerate(wps):
        d.rectangle([x - 20, y - 20, x + 20, y + 20], outline=PENCIL, width=4); d.text((x + 34, y - 34), f'WP{i + 1}', font=F('reg', 38), fill=PENCIL, anchor='lm')
    d.ellipse([1880 - 70, 1050 - 70, 1880 + 70, 1050 + 70], outline=PENCIL, width=4); d.text((1880, 960), 'refuge', font=hand(46), fill=PENCIL, anchor='mm')
    d.text((900, 1100), 'cross at 90°', font=hand(46), fill=PENCIL, anchor='mm')
    # a fix with its time
    fx, fy = 900, 760
    d.ellipse([fx - 22, fy - 22, fx + 22, fy + 22], outline=PENCIL, width=4); d.ellipse([fx - 5, fy - 5, fx + 5, fy + 5], fill=PENCIL); d.text((fx - 40, fy + 10), '1430', font=F('reg', 36), fill=PENCIL, anchor='rm')
    d.rectangle([30, 30, w - 30, h - 30], outline=(20, 20, 20), width=4)
    save(im, out, {'track': wps[2], 'fix': (fx, fy), 'refuge': (1880, 1050), 'size': (w, h)})

def book(out, title, sub, color, w=900, h=1240, band=(240, 236, 220)):
    im = Image.new('RGB', (w, h), color); d = ImageDraw.Draw(im)
    d.rectangle([0, 300, w, 520], fill=band)
    d.text((w / 2, 380), title, font=F('serif', 96), fill=color, anchor='mm'); d.text((w / 2, 470), sub, font=F('bold', 48), fill=(60, 60, 60), anchor='mm')
    d.text((w / 2, h - 120), '2026', font=F('bold', 70), fill=band, anchor='mm')
    save(im, out, blur=0.7)

def p1_plan(out):
    w, h = 1240, 1754; im, d = paper(w, h, (250, 249, 240)); ruled(d, w, h, 260, 86)
    d.text((200, 170), 'Passage plan', font=hand(80), fill=INKB, anchor='ls')
    lines = ['Appraisal: charts, pilot, tides,', '   forecasts, notices', 'Plan: WP1-WP4, cross TSS at 90°', '   leave 0600, ETA 2100', '   plan B: refuge at Fowey',
             'Exec: 0500 forecast, brief crew', 'Monitor: fix every 30 min', '   off track > 0.5 M: act']
    ys = written(d, 180, 346, lines, 54)
    save(im, out, {'appraisal': (420, ys[0] - 20), 'planning': (420, ys[2] - 20), 'execution': (420, ys[5] - 20), 'monitoring': (420, ys[6] - 20), 'size': (w, h)})

def p1_forecast(out):
    w, h = 1240, 1754; im, d = paper(w, h, (252, 252, 250))
    d.text((90, 140), 'INSHORE WATERS FORECAST', font=F('bold', 58), fill=(20, 20, 20), anchor='lm')
    d.text((90, 220), 'Issued 0500 UTC Sat', font=F('reg', 42), fill=(60, 60, 60), anchor='lm')
    body = ['Wind: southwest 4 or 5, occasionally 6 later.', 'Sea state: slight or moderate.', 'Weather: fair, rain later.', 'Visibility: good, occasionally moderate.', '',
            'Outlook: southwest 5 to 7, perhaps gale 8 later.']
    for i, t in enumerate(body): d.text((90, 340 + i * 70), t, font=F('reg', 44), fill=(30, 30, 30), anchor='lm')
    d.rectangle([90, 820, w - 90, 1500], outline=(120, 120, 120), width=3)
    for i in range(9): d.line([(90, 820 + i * 85), (w - 90, 820 + i * 85)], fill=(200, 200, 200), width=2)
    save(im, out)

def p2_note(out):
    w, h = 1240, 1754; im, d = paper(w, h, (250, 249, 240)); ruled(d, w, h, 260, 96)
    d.text((200, 170), 'Latest departure', font=hand(80), fill=INKB, anchor='ls')
    lines = ['120 M ÷ 8 kn = 15 h', 'Front: model A Sat 1800', '           model B Sat 1200 (earlier)', 'In harbour 6 h before:', 'Sat 1200 − 6 h = Sat 0600', 'Sat 0600 − 15 h = Fri 1500', 'Leave by Fri 1500']
    ys = written(d, 180, 356, lines, 60, 96)
    d.rectangle([170, ys[6] - 70, 840, ys[6] + 22], outline=(200, 30, 40), width=5)
    save(im, out, {'crossing': (500, ys[0] - 20), 'earlier': (700, ys[2] - 20), 'leave': (500, ys[6] - 20), 'size': (w, h)})

def p4_orders(out):
    w, h = 1240, 1754; im, d = paper(w, h, (246, 242, 230)); ruled(d, w, h, 260, 104)
    d.text((200, 170), 'Night orders · Tue', font=hand(80), fill=INKB, anchor='ls')
    lines = ['Fix every 30 min offshore', 'Within 3 M of danger: every 6 min', 'Call me: CPA under 1 M,', '   or any doubt at all', 'Close quarters: act first,', '   then call me', 'Watch alarm on · log hourly', '                       — Skipper']
    ys = written(d, 180, 364, lines, 58, 104)
    save(im, out, {'fix': (520, ys[0] - 20), 'six': (620, ys[1] - 20), 'call': (520, ys[2] - 20), 'act': (520, ys[4] - 20), 'alarm': (520, ys[6] - 20), 'size': (w, h)})

def p5_plan(out):
    """A pilotage plan page: the entrance sketched with its clearing bearing, wheel-over and abort point; the numbers."""
    w, h = 1754, 1240; im, d = paper(w, h, (250, 249, 240))
    for y in range(100, h, 60):
        for x in range(60, w, 60): d.point((x, y), fill=(190, 200, 214))
    d.text((60, 90), 'Pilotage plan · the entrance', font=hand(70), fill=INKB, anchor='ls')
    # sketch: coast north, an entrance, the approach from the south turning in
    P = lambda x, y: (100 + x, 160 + y)
    coast = [P(0, 0), P(980, 0), P(980, 180), P(640, 200), P(600, 120), P(520, 120), P(480, 220), P(0, 260)]
    d.line(coast, fill=INKB, width=6)
    d.polygon([P(760, 420), P(820, 400), P(860, 450), P(800, 480)], outline=(200, 30, 40), width=5)            # a rock
    d.text(P(870, 470), 'rock', font=hand(46), fill=(200, 30, 40), anchor='lm')
    d.line([P(560, 120), P(860, 900)], fill=(200, 30, 40), width=4)                                             # clearing bearing
    d.text(P(720, 640), 'NMT 160°', font=hand(46), fill=(200, 30, 40), anchor='lm')
    d.line([P(560, 900), P(560, 560)], fill=PENCIL, width=6); d.arc([P(560, 360)[0] - 200, P(560, 360)[1] - 0, P(560, 360)[0] + 0, P(560, 360)[1] + 400], 270, 360, fill=PENCIL, width=6)
    d.line([P(560, 560), P(560, 120)], fill=PENCIL, width=6)
    wo = P(560, 560); d.line([(wo[0] - 40, wo[1]), (wo[0] + 40, wo[1])], fill=INKB, width=8); d.text((wo[0] - 60, wo[1]), 'wheel-over', font=hand(46), fill=INKB, anchor='rm')
    ab = P(560, 760); d.line([(ab[0] - 50, ab[1] - 50), (ab[0] + 50, ab[1] + 50)], fill=(200, 30, 40), width=8); d.line([(ab[0] - 50, ab[1] + 50), (ab[0] + 50, ab[1] - 50)], fill=(200, 30, 40), width=8)
    d.text((ab[0] - 70, ab[1]), 'abort', font=hand(46), fill=(200, 30, 40), anchor='rm')
    lines = ['Tide needed:', '2.2 + 1.0 + 0.5 − 1.8', '   = 1.9 m', 'Bridge:', '18.0 + 5.4 − 4.6 = 18.8', '   ≥ air draught 17.5', 'VTS ch 12: name,', 'position, intention,', 'ETA, then listen']
    written(d, 1130, 260, lines, 46, 84)
    save(im, out, {'clearing': P(600, 225), 'wheel': wo, 'abort': ab, 'notes': (1400, 300), 'size': (w, h)})

def p13_log(out):
    w, h = 1754, 1240; im, d = paper(w, h, (248, 246, 236))
    cols = [('Time', 160), ('Position', 640), ('Log', 190), ('Co °M', 160), ('Remarks', 480)]
    x = 60; d.rectangle([60, 80, w - 60, 160], fill=(226, 230, 236))
    for t, cw in cols: d.text((x + 16, 120), t, font=F('bold', 42), fill=(40, 46, 60), anchor='lm'); x += cw
    rows = [('0300', '49°41.0N 004°31.2W', '1225.1', '047', 'fix GNSS'), ('0330', '49°43.3N 004°27.4W', '1229.9', '047', 'fix GNSS'),
            ('0400', '49°45.6N 004°23.6W', '1234.7', '047', 'HDOP rising'), ('0412', '49°46.6N 004°21.9W', '1236.6', '047', 'GNSS LOST: DR'),
            ('0430', 'DR 49°47.9N 004°19.7W', '1239.4', '047', 'radar ranges')]
    y = 160
    for i, r in enumerate(rows):
        x = 60
        for j, (t, (_, cw)) in enumerate(zip(r, cols)):
            d.text((x + 16, y + 60), t, font=hand(46), fill=(200, 30, 40) if i == 3 and j in (0, 4) else INKB, anchor='lm'); x += cw
        y += 120; d.line([(60, y), (w - 60, y)], fill=(200, 204, 210), width=2)
    save(im, out, {'lost': (1300, 160 + 3 * 120 + 40), 'size': (w, h)})

JOBS = {'p1-chart': p1_chart, 'p1-plan': p1_plan, 'p1-forecast': p1_forecast,
        'p1-pilot': lambda o: book(o, 'PILOT', 'West Country', (24, 60, 110)), 'p1-tides': lambda o: book(o, 'TIDES', 'tables and curves', (150, 30, 40)),
        'p2-note': p2_note, 'p2-grib': p2_grib, 'p4-orders': p4_orders, 'p5-plan': p5_plan,
        'p8-radar': p8_radar, 'p9-radar': p9_radar, 'p10-radar': p10_radar, 'p11-arpa': p11_arpa, 'p12-gnss': p12_gnss,
        'p13-nofix': p13_nofix, 'p13-log': p13_log}

def main(jobs):
    outdir = sys.argv[1]; names = sys.argv[2:] or list(jobs)
    os.makedirs(outdir, exist_ok=True)
    for n in names: jobs[n](os.path.join(outdir, n)); print('tex', n)

if __name__ == '__main__': main(JOBS)
