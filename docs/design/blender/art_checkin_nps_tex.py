# Textures for the Charter Check-in renders of art_checkin_nav.py, art_checkin_papers.py and art_checkin_safety.py
# (nav, papers, safety: "nps"): plotter screens on the Raymarine Axiom's front, instrument LCDs, documents, labels.
# System Python with Pillow (Blender's Python has no PIL); the Blender scripts run it when a texture is missing, into
# the article's own folder, tex/<name>.png.
#   python3 docs/design/blender/art_checkin_nps_tex.py <outdir> [name ...]     (no names: all of them)
# Each plotter screen is written as a whole Axiom front (the model's own front texture, 3x up-scaled, the chart
# pasted on its glass) plus <name>.json with the pixel anchors of the things the labels point at, in the
# 828 x 481 frame of the original front texture (the frame art_vhf_scenes.screen_point() expects).
import os, sys, json, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SUP = '/System/Library/Fonts/Supplemental/'
FONTS = {'bold': SUP + 'Arial Bold.ttf', 'reg': SUP + 'Arial.ttf', 'ital': SUP + 'Arial Italic.ttf', 'din': SUP + 'DIN Condensed Bold.ttf',
         'dina': SUP + 'DIN Alternate Bold.ttf', 'narrow': SUP + 'Arial Narrow Bold.ttf', 'nar': SUP + 'Arial Narrow.ttf',
         'hand': SUP + 'Bradley Hand Bold.ttf', 'serif': SUP + 'Georgia Bold.ttf', 'serif_r': SUP + 'Georgia.ttf',
         'mono': '/System/Library/Fonts/Menlo.ttc'}
def F(k, n): return ImageFont.truetype(FONTS[k], int(n))

K3 = 3                                   # the front is drawn 3x the model's own texture
BOX = (70, 72, 645, 432)                 # the screen glass on the 828 x 481 front
SW, SH = (BOX[2] - BOX[0]) * K3, (BOX[3] - BOX[1]) * K3     # 1725 x 1080

def to_front(x, y):
    """Screen pixel (on the SW x SH chart) -> pixel on the 828 x 481 front texture."""
    return [BOX[0] + x / K3, BOX[1] + y / K3]

def front(screen, out, anchors):
    fr = Image.open(os.path.join(HERE, 'textures', 'axiom-front.png')).convert('RGB')
    fr = fr.resize((fr.width * K3, fr.height * K3), Image.LANCZOS)
    fr.paste(screen.resize((SW, SH), Image.LANCZOS), (BOX[0] * K3, BOX[1] * K3))
    fr.save(out + '.png')
    json.dump({k: to_front(*v) for k, v in anchors.items()}, open(out + '.json', 'w'))

# ---------------------------------------------------------------- chart helpers
SEA, SEA2, LAND, COAST = (206, 232, 244), (178, 214, 232), (240, 221, 150), (138, 122, 64)
def chart_base():
    im = Image.new('RGB', (SW, SH), SEA); return im, ImageDraw.Draw(im)

def topbar(d, items, h=96):
    d.rectangle([0, 0, SW, h], fill=(20, 24, 30))
    x = 24
    for txt, col, box in items:
        fo = F('bold', 50); w = d.textlength(txt, font=fo)
        if box:
            d.rounded_rectangle([x, 12, x + w + 40, h - 12], 12, fill=box); d.text((x + 20, h / 2), txt, font=fo, fill=col, anchor='lm'); x += w + 70
        else:
            d.text((x, h / 2), txt, font=fo, fill=col, anchor='lm'); x += w + 50

def own_boat(d, x, y, hdg, s=1.0, col=(17, 17, 17)):
    a = math.radians(hdg); R = lambda px, py: (x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a))
    d.polygon([R(0, -44 * s), R(26 * s, 32 * s), R(0, 18 * s), R(-26 * s, 32 * s)], fill=col)

def sounding(d, x, y, t, s=44): d.text((x, y), t, font=F('ital', s), fill=(40, 70, 100), anchor='mm')

def databox(d, x, y, w, rows, h=118):
    d.rounded_rectangle([x, y, x + w, y + h * len(rows) + 16], 18, fill=(18, 22, 28))
    for i, (k, v, col) in enumerate(rows):
        yy = y + 16 + i * h
        d.text((x + 24, yy + 26), k, font=F('bold', 34), fill=(150, 170, 186), anchor='lm')
        d.text((x + w - 24, yy + 76), v, font=F('dina', 66), fill=col, anchor='rm')

def scalebar(d, x, y, px, txt):
    d.line([(x, y), (x + px, y)], fill=(27, 42, 68), width=6); d.line([(x, y - 14), (x, y + 14)], fill=(27, 42, 68), width=6); d.line([(x + px, y - 14), (x + px, y + 14)], fill=(27, 42, 68), width=6)
    d.text((x + px / 2, y - 34), txt, font=F('bold', 36), fill=(27, 42, 68), anchor='mm')

# ---------------------------------------------------------------- plotter screens
def nav1(out):
    """At the berth, Sat 17:00, no satellites: the plotter still shows Friday's last position, 0.4 M out in the bay."""
    im, d = chart_base()
    for k, c in enumerate((SEA2, (192, 224, 238))):
        d.rectangle([0, 0, SW, 470 + 90 * k], fill=None)
    d.polygon([(0, 0), (SW, 0), (SW, 330), (1200, 350), (980, 400), (760, 380), (520, 410), (0, 370)], fill=(196, 226, 240))
    d.polygon([(0, 0), (SW, 0), (SW, 280), (1200, 300), (980, 340), (760, 330), (520, 350), (0, 320)], fill=LAND, outline=COAST)
    d.line([(0, 320), (520, 350), (760, 330), (980, 340), (1200, 300), (SW, 280)], fill=COAST, width=5)
    for x0 in range(140, 520, 90):                        # the town: grey blocks
        for y0 in (110, 190):
            d.rectangle([x0, y0, x0 + 60, y0 + 50], fill=(205, 190, 140))
    d.text((150, 60), 'Town', font=F('bold', 52), fill=(90, 72, 40), anchor='lm')
    # the base pontoon, out from the quay, with its fingers
    px0, py0, py1 = 760, 330, 700
    d.rectangle([px0 - 14, py0, px0 + 14, py1], fill=(150, 150, 150), outline=(90, 90, 90))
    for yy in range(py0 + 50, py1, 55):
        d.rectangle([px0 - 90, yy, px0 - 14, yy + 8], fill=(150, 150, 150)); d.rectangle([px0 + 14, yy, px0 + 90, yy + 8], fill=(150, 150, 150))
    d.text((px0, py1 + 46), 'Base pontoon', font=F('bold', 44), fill=(40, 50, 70), anchor='mm')
    for x, y, t in ((1380, 520, '9'), (380, 640, '12'), (1100, 800, '14'), (520, 900, '17'), (1500, 940, '19'), (200, 470, '6')):
        sounding(d, x, y, t)
    # Friday's last position, 0.4 M out: the boat icon greyed, a dashed line back to the berth
    bx, by = 1330, 720
    for t in range(0, 100, 7):
        a, b = t / 100, (t + 4) / 100
        d.line([(px0 + 90 + (bx - px0 - 90) * a, 560 + (by - 560) * a), (px0 + 90 + (bx - px0 - 90) * b, 560 + (by - 560) * b)], fill=(200, 30, 40), width=5)
    d.text(((px0 + 90 + bx) / 2 + 10, (560 + by) / 2 - 40), '0.4 NM', font=F('bold', 40), fill=(200, 30, 40), anchor='mm')
    own_boat(d, bx, by, 20, 1.25, (80, 80, 84))
    d.ellipse([bx - 70, by - 70, bx + 70, by + 70], outline=(200, 30, 40), width=5)
    d.rounded_rectangle([bx + 90, by - 60, bx + 370, by + 10], 10, fill=(255, 255, 255), outline=(200, 30, 40), width=3)
    d.text((bx + 230, by - 25), 'Fri 18:10', font=F('bold', 40), fill=(200, 30, 40), anchor='mm')
    topbar(d, [('NO FIX', (255, 255, 255), (200, 30, 40)), ('GPS: 0 satellites', (230, 236, 240), None), ('Sat 17:00', (230, 236, 240), None)])
    databox(d, SW - 400, SH - 290, 370, [('SOG', '--.- kn', (230, 236, 240)), ('COG', '---°', (230, 236, 240))])
    scalebar(d, 40, SH - 50, 126, '0.1 NM')
    front(im, out, {'nofix': (110, 48), 'boat': (bx, by - 80), 'pontoon': (px0, 560)})

def nav3(out):
    """The test run: north-up chart, the boat's COG line pointing just south of east, COG 098°T big on the data bar."""
    im, d = chart_base()
    d.polygon([(0, SH), (0, 760), (260, 720), (460, 780), (720, 840), (980, 900), (1200, SH)], fill=LAND, outline=COAST)
    d.line([(0, 760), (260, 720), (460, 780), (720, 840), (980, 900), (1200, SH)], fill=COAST, width=5)
    for x, y, t in ((300, 300, '42'), (800, 200, '55'), (1050, 500, '48'), (420, 560, '27'), (760, 650, '18'), (200, 620, '9')): sounding(d, x, y, t)
    bx, by = 380, 420
    ex, ey = bx + 820 * math.sin(math.radians(98)), by - 820 * math.cos(math.radians(98))
    d.line([(bx, by), (ex, ey)], fill=(17, 17, 17), width=7)
    for k in range(1, 4):
        tx, ty = bx + k * 205 * math.sin(math.radians(98)), by - k * 205 * math.cos(math.radians(98)); d.line([(tx, ty - 18), (tx, ty + 18)], fill=(17, 17, 17), width=6)
    own_boat(d, bx, by, 98, 1.3)
    d.line([(bx - 260, by + 30), (bx - 40, by + 6)], fill=(200, 30, 40), width=8)      # the track behind
    topbar(d, [('CHART', (230, 236, 240), None), ('North up', (160, 176, 190), None), ('GPS 3D fix', (120, 220, 140), None)])
    databox(d, SW - 520, 140, 490, [('COG', '098°T', (255, 214, 60)), ('SOG', '6.1 kn', (230, 236, 240)), ('XTE', '0.00 NM', (230, 236, 240))], h=150)
    scalebar(d, 40, SH - 50, 260, '0.5 NM')
    front(im, out, {'cog': (SW - 275, 230), 'boat': (bx, by - 60)})

def nav4(out):
    """North-up, we head 000; a ferry's AIS triangle at 050° relative, crossing west, its vector across our bow:
    the CPA alarm banner is up."""
    im, d = chart_base()
    d.polygon([(0, 0), (520, 0), (430, 120), (260, 170), (0, 210)], fill=LAND, outline=COAST)
    for x, y, t in ((400, 500, '64'), (900, 330, '72'), (1300, 700, '58'), (300, 860, '49'), (1050, 900, '61')): sounding(d, x, y, t)
    bx, by = 760, 860
    d.line([(bx, by), (bx, by - 520)], fill=(17, 17, 17), width=7)                 # our heading/COG vector
    own_boat(d, bx, by, 0, 1.3)
    a = math.radians(50); fx, fy = bx + 560 * math.sin(a), by - 560 * math.cos(a)
    cpa = (bx, fy - 10)
    d.line([(fx, fy), (bx - 260, fy - 10)], fill=(30, 110, 40), width=7)            # the ferry's vector, across our bow
    tri = [(fx - 40, fy), (fx + 30, fy - 30), (fx + 30, fy + 30)]                   # an AIS triangle pointing west
    d.polygon(tri, fill=(30, 160, 60), outline=(10, 60, 20))
    d.ellipse([cpa[0] - 40, cpa[1] - 40, cpa[0] + 40, cpa[1] + 40], outline=(200, 30, 40), width=7)
    d.text((cpa[0] - 60, cpa[1] - 60), 'CPA', font=F('bold', 44), fill=(200, 30, 40), anchor='rm')
    d.rounded_rectangle([fx + 50, fy - 40, fx + 520, fy + 100], 12, fill=(255, 255, 255), outline=(30, 110, 40), width=3)
    d.text((fx + 70, fy - 2), 'FERRY', font=F('bold', 46), fill=(20, 60, 30), anchor='lm'); d.text((fx + 70, fy + 56), 'COG 270°  SOG 15 kn', font=F('reg', 38), fill=(20, 30, 40), anchor='lm')
    topbar(d, [('CHART · AIS', (230, 236, 240), None), ('North up', (160, 176, 190), None)])
    d.rounded_rectangle([200, 150, SW - 200, 300], 20, fill=(200, 30, 40))
    d.text((SW / 2, 196), 'DANGEROUS TARGET', font=F('bold', 60), fill=(255, 255, 255), anchor='mm')
    d.text((SW / 2, 262), 'CPA 0.34 NM  ·  TCPA 4 min', font=F('bold', 50), fill=(255, 235, 230), anchor='mm')
    scalebar(d, 40, SH - 50, 260, '0.5 NM')
    front(im, out, {'alarm': (SW / 2, 160), 'target': (fx, fy - 40), 'cpa': cpa})

def papers3(out):
    """17:30, the route to the marina 14 M on: TTG 2 h 48, ETA 20:18 against sunset 19:40; a harbour 6 M abeam."""
    im, d = chart_base()
    d.polygon([(0, 0), (260, 0), (330, 300), (430, 560), (540, 840), (520, SH), (0, SH)], fill=LAND, outline=COAST)
    d.line([(260, 0), (330, 300), (430, 560), (540, 840), (520, SH)], fill=COAST, width=5)
    for x, y, t in ((600, 300, '38'), (760, 650, '45'), (1050, 420, '52'), (700, 1000, '33')): sounding(d, x, y, t)
    bx, by = 900, 900; wx, wy = 900, 140
    d.line([(bx, by), (wx, wy)], fill=(200, 30, 140), width=9)
    d.ellipse([wx - 26, wy - 26, wx + 26, wy + 26], outline=(200, 30, 140), width=8)
    d.text((wx + 40, wy), 'MARINA', font=F('bold', 46), fill=(120, 20, 90), anchor='lm')
    own_boat(d, bx, by, 0, 1.3)
    hx, hy = 560, 900                                     # the harbour abeam, to port: 6 M at 54 px a mile
    d.rectangle([hx - 50, hy - 40, hx + 10, hy + 40], fill=(150, 150, 150))
    d.text((hx - 60, hy - 80), 'Harbour', font=F('bold', 42), fill=(90, 72, 40), anchor='lm')
    for t in range(0, 100, 6):
        a, b = t / 100, (t + 3) / 100
        d.line([(bx + (hx + 20 - bx) * a, by + (hy - by) * a), (bx + (hx + 20 - bx) * b, by + (hy - by) * b)], fill=(27, 42, 68), width=5)
    d.text(((bx + hx) / 2 + 20, (by + hy) / 2 - 40), '6.0 NM', font=F('bold', 40), fill=(27, 42, 68), anchor='mm')
    topbar(d, [('ROUTE', (230, 236, 240), None), ('17:30', (230, 236, 240), None), ('Sunset 19:40', (255, 214, 60), None)])
    databox(d, SW - 470, 130, 440, [('DTW', '14.0 NM', (230, 236, 240)), ('SOG', '5.0 kn', (230, 236, 240)), ('TTG', '2 h 48', (230, 236, 240)), ('ETA', '20:18', (255, 90, 80))], h=150)
    front(im, out, {'eta': (SW - 250, 130 + 16 + 3 * 150 + 76), 'harbour': (hx - 20, hy - 40), 'wp': (wx, wy - 30)})

# ---------------------------------------------------------------- instrument LCDs (i70-like: black, white digits)
def lcd(out, title, value, unit, sub=''):
    w, h = 800, 800; im = Image.new('RGB', (w, h), (6, 8, 10)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 120], fill=(24, 30, 38)); d.text((w / 2, 62), title, font=F('bold', 74), fill=(235, 238, 240), anchor='mm')
    d.text((w / 2 - 20, 430), value, font=F('dina', 380), fill=(250, 250, 250), anchor='mm')
    d.text((w - 50, 640), unit, font=F('bold', 84), fill=(200, 205, 210), anchor='rm')
    if sub: d.text((50, 720), sub, font=F('bold', 52), fill=(150, 160, 170), anchor='lm')
    im.save(out + '.png')

# ---------------------------------------------------------------- documents
def paper(w, h, tint=(247, 245, 238)): im = Image.new('RGB', (w, h), tint); return im, ImageDraw.Draw(im)

def licence(out):
    w, h = 1712, 1080; im, d = paper(w, h, (232, 238, 244))
    for i in range(0, w, 6): d.line([(i, 0), (i - 300, h)], fill=(224, 232, 240))
    d.rectangle([0, 0, w, 190], fill=(26, 58, 110))
    d.text((60, 95), "SKIPPER'S LICENCE", font=F('bold', 92), fill=(255, 255, 255), anchor='lm')
    d.text((w - 60, 95), 'Sail · coastal', font=F('reg', 60), fill=(200, 215, 235), anchor='rm')
    d.rounded_rectangle([60, 260, 470, 780], 20, fill=(196, 204, 214))
    d.ellipse([175, 330, 355, 520], fill=(120, 130, 145)); d.chord([110, 520, 420, 900], 180, 360, fill=(120, 130, 145))
    rows = [('Holder', 'Mara Lindqvist'), ('Born', '12.03.1984'), ('Craft', 'Sailing yacht, up to 24 m'), ('Area', 'Coastal waters'), ('No.', 'SL 0048 1173'), ('Valid until', '14.06.2031')]
    y = 290
    for k, v in rows:
        d.text((540, y), k, font=F('reg', 46), fill=(90, 100, 115), anchor='lm'); d.text((840, y), v, font=F('bold', 58), fill=(20, 26, 36), anchor='lm'); y += 105
    d.text((60, h - 90), 'Issued by the national maritime authority', font=F('ital', 44), fill=(80, 90, 105), anchor='lm')
    im.save(out + '.png')

def src(out):
    w, h = 1712, 1080; im, d = paper(w, h, (240, 236, 222))
    d.rectangle([0, 0, w, 170], fill=(150, 30, 40))
    d.text((60, 85), 'VHF OPERATOR', font=F('bold', 88), fill=(255, 255, 255), anchor='lm')
    d.text((w - 60, 85), 'SRC', font=F('bold', 88), fill=(255, 220, 210), anchor='rm')
    d.text((60, 260), 'Short Range Certificate', font=F('serif', 70), fill=(60, 30, 30), anchor='lm')
    rows = [('Holder', 'Mara Lindqvist'), ('Certificate', 'SRC 2019 / 08 412'), ('Valid', 'for life')]
    y = 400
    for k, v in rows:
        d.text((60, y), k, font=F('reg', 50), fill=(100, 90, 80), anchor='lm'); d.text((480, y), v, font=F('bold', 62), fill=(30, 26, 22), anchor='lm'); y += 120
    d.ellipse([w - 420, h - 420, w - 90, h - 90], outline=(150, 30, 40), width=10)
    d.text((w - 255, h - 255), 'GMDSS', font=F('bold', 60), fill=(150, 30, 40), anchor='mm')
    im.save(out + '.png')

def passport(out):
    w, h = 880, 1250; im = Image.new('RGB', (w, h), (92, 22, 34)); d = ImageDraw.Draw(im)
    gold = (206, 170, 92)
    d.text((w / 2, 230), 'PASSPORT', font=F('serif', 104), fill=gold, anchor='mm')
    cx, cy, R = w / 2, 640, 190
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=gold, width=10); d.ellipse([cx - R + 40, cy - R + 40, cx + R - 40, cy + R - 40], outline=gold, width=5)
    for a in range(0, 360, 45):
        t = math.radians(a); d.line([(cx, cy), (cx + math.sin(t) * (R - 40), cy - math.cos(t) * (R - 40))], fill=gold, width=6)
    d.rounded_rectangle([cx - 70, 1010, cx + 70, 1090], 10, outline=gold, width=6)
    im.filter(ImageFilter.GaussianBlur(0.8)).save(out + '.png')

def table_doc(out, title, sub, head, rows, widths, tint=(250, 249, 244), foot=None, hand_cols=()):
    w, h = 1240, 1754; im, d = paper(w, h, tint)
    d.text((90, 140), title, font=F('bold', 74), fill=(24, 30, 44), anchor='lm')
    d.text((90, 225), sub, font=F('reg', 44), fill=(80, 88, 100), anchor='lm')
    y = 330; x = 90
    d.rectangle([90, y, w - 90, y + 80], fill=(226, 230, 236))
    for t, cw in zip(head, widths):
        d.text((x + 14, y + 40), t, font=F('bold', 36), fill=(40, 46, 60), anchor='lm'); x += cw
    y += 80
    for r in rows:
        x = 90
        for j, (t, cw) in enumerate(zip(r, widths)):
            fo = F('hand', 44) if j in hand_cols else F('reg', 38)
            d.text((x + 14, y + 48), t, font=fo, fill=(28, 34, 60) if j in hand_cols else (30, 34, 40), anchor='lm'); x += cw
        y += 96; d.line([(90, y), (w - 90, y)], fill=(200, 204, 210), width=2)
    if foot: foot(d, w, h, y)
    im.filter(ImageFilter.GaussianBlur(0.5)).save(out + '.png')

def crewlist(out):
    rows = [('1', 'Mara Lindqvist', 'skipper', 'X4 8812 07'), ('2', 'Tomas Berg', 'co-skipper', 'P 3317 920'), ('3', 'Ines Duarte', 'crew', 'CB 412 088'),
            ('4', 'Paul Duarte', 'crew', 'CB 412 091'), ('5', 'Lea Duarte (9)', 'crew', 'CB 650 214'), ('6', 'Jonas Weil', 'crew', 'C7 99 1043')]
    def foot(d, w, h, y):
        d.text((90, y + 120), 'Sent to the base: 02 June', font=F('ital', 40), fill=(80, 88, 100), anchor='lm')
    table_doc(out, 'CREW LIST', 'S/Y Nefeli · 14–21 June · everyone sleeping aboard', ['No.', 'Name', 'Role', 'Passport no.'], rows, [110, 450, 250, 250], foot=foot)

def booking(out):
    w, h = 1240, 1754; im, d = paper(w, h)
    d.rectangle([0, 0, w, 220], fill=(18, 60, 92)); d.text((90, 110), 'Nefeli Charters', font=F('serif', 80), fill=(255, 255, 255), anchor='lm')
    d.text((90, 330), 'Booking confirmation', font=F('bold', 66), fill=(24, 30, 44), anchor='lm')
    rows = [('Yacht', 'Sun Odyssey 49 · Nefeli'), ('Dates', 'Sat 14 – Sat 21 June'), ('Check-in', 'Saturday from 17:00'), ('Check-out', 'Saturday by 09:00'),
            ('Skipper', 'Mara Lindqvist'), ('Deposit', 'EUR 2,500 at check-in'), ('Booking no.', 'NC-26-0614-07')]
    y = 470
    for k, v in rows:
        d.text((90, y), k, font=F('reg', 44), fill=(90, 98, 110), anchor='lm'); d.text((480, y), v, font=F('bold', 50), fill=(24, 30, 44), anchor='lm')
        d.line([(90, y + 50), (w - 90, y + 50)], fill=(214, 216, 220), width=2); y += 118
    im.filter(ImageFilter.GaussianBlur(0.5)).save(out + '.png')

def card(out):
    w, h = 1712, 1080; im = Image.new('RGB', (w, h), (20, 40, 78)); d = ImageDraw.Draw(im)
    for i in range(0, w + h, 14): d.line([(i, 0), (i - h, h)], fill=(24, 46, 88), width=5)
    d.text((90, 120), 'HARBOUR BANK', font=F('bold', 74), fill=(225, 230, 240), anchor='lm')
    d.rounded_rectangle([150, 360, 380, 540], 26, fill=(196, 170, 100));
    for k in range(1, 4): d.line([(150, 360 + k * 45), (380, 360 + k * 45)], fill=(160, 130, 70), width=4)
    d.text((150, 720), '••••  ••••  ••••  4821', font=F('dina', 110), fill=(232, 236, 244), anchor='lm')
    d.text((150, 900), 'M LINDQVIST', font=F('bold', 64), fill=(220, 226, 236), anchor='lm'); d.text((w - 150, 900), '09/29', font=F('bold', 64), fill=(220, 226, 236), anchor='rm')
    im.save(out + '.png')

def contract(out):
    w, h = 1240, 1754; im, d = paper(w, h)
    d.text((90, 130), 'CHARTER AGREEMENT', font=F('bold', 64), fill=(24, 30, 44), anchor='lm'); d.text((w - 90, 130), 'page 3 of 6', font=F('reg', 36), fill=(110, 116, 126), anchor='rm')
    para = [('6.', 'Cruising area', ['The yacht sails within the area of Annex B. No sailing', 'between sunset and sunrise, nor in winds above F6.']),
            ('7.', 'Security deposit', ['A deposit of EUR 2,500 is held on a card or in cash at', 'check-in. It is the charterer\'s limit of liability for', 'damage covered by the yacht\'s insurance.',
                                         'Not covered, payable in full: damage from negligence,', 'grounding, loss of the dinghy, outboard or sails.', 'The deposit is settled at check-out against the', 'check-in report.']),
            ('8.', 'Damage waiver', ['A non-refundable waiver lowers the deposit to EUR 500;', 'clause 7 exclusions apply.'])]
    y = 260; marks = {}
    for num, head, lines in para:
        d.text((90, y), num, font=F('bold', 48), fill=(24, 30, 44), anchor='lm'); d.text((170, y), head, font=F('bold', 48), fill=(24, 30, 44), anchor='lm'); y += 80
        for i, ln in enumerate(lines):
            if num == '7.' and i in (1, 2): d.rectangle([160, y - 30, 1140, y + 30], fill=(255, 236, 120)); marks.setdefault('limit', y)
            if num == '7.' and i in (3, 4): d.rectangle([160, y - 30, 1140, y + 30], fill=(255, 196, 180)); marks.setdefault('excl', y)
            d.text((170, y), ln, font=F('reg', 40), fill=(36, 40, 48), anchor='lm'); y += 62
        y += 60
    d.line([(170, 1560), (560, 1560)], fill=(120, 120, 120), width=2); d.text((170, 1600), 'Charterer', font=F('reg', 34), fill=(110, 116, 126), anchor='lm')
    pts = [(190 + i * 8, 1530 + 20 * math.sin(i * 0.4) + 10 * math.sin(i * 1.3)) for i in range(40)]; d.line(pts, fill=(30, 40, 90), width=5)
    im.filter(ImageFilter.GaussianBlur(0.5)).save(out + '.png')
    json.dump({k: v / h for k, v in marks.items()}, open(out + '.json', 'w'))

def terminal(out):
    w, h = 480, 600; im = Image.new('RGB', (w, h), (214, 226, 214)); d = ImageDraw.Draw(im)
    d.text((w / 2, 70), 'PRE-AUTHORISATION', font=F('bold', 40), fill=(20, 30, 20), anchor='mm')
    d.text((w / 2, 220), 'EUR 2,500.00', font=F('dina', 86), fill=(10, 16, 10), anchor='mm')
    d.rounded_rectangle([60, 300, w - 60, 380], 10, fill=(30, 120, 60)); d.text((w / 2, 340), 'APPROVED', font=F('bold', 50), fill=(255, 255, 255), anchor='mm')
    d.text((w / 2, 450), 'held, not charged', font=F('bold', 40), fill=(20, 30, 20), anchor='mm')
    d.text((w / 2, 520), 'card •••• 4821', font=F('reg', 36), fill=(40, 50, 40), anchor='mm')
    im.save(out + '.png')

def checkin_form(out):
    rows = [('Hull, stbd quarter', 'scratch 10 cm, photo 14'), ('Hull, bow', 'chip 2 cm in gelcoat, stem'), ('Fenders', '6 aboard, inventory says 8'),
            ('Mooring lines', '4, as inventory'), ('Fuel / water', '4/4 · 2/2 tanks'), ('Engine hours', '2,312.1'), ('Dinghy, outboard', 'OK, 2.5 hp starts')]
    def foot(d, w, h, y):
        for i, (lab, sig) in enumerate((('Charterer', 'M. Lindqvist'), ('Base', 'K. Petrou'))):
            x0 = 90 + i * 560
            d.line([(x0, y + 210), (x0 + 450, y + 210)], fill=(120, 120, 120), width=2); d.text((x0, y + 250), lab, font=F('reg', 36), fill=(110, 116, 126), anchor='lm')
            d.text((x0 + 20, y + 170), sig, font=F('hand', 56), fill=(30, 40, 100), anchor='lm')
    table_doc(out, 'CHECK-IN REPORT', 'S/Y Nefeli · Sat 14 June, 17:40', ['Item', 'Found'], rows, [430, 630], foot=foot, hand_cols=(1,))

# ---------------------------------------------------------------- safety
def service_label(out):
    w, h = 600, 300; im = Image.new('RGB', (w, h), (250, 250, 246)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 70], fill=(30, 120, 60)); d.text((w / 2, 36), 'SERVICED', font=F('bold', 48), fill=(255, 255, 255), anchor='mm')
    d.text((30, 130), 'Next service', font=F('reg', 40), fill=(40, 40, 40), anchor='lm'); d.text((w - 30, 130), '03 / 2027', font=F('bold', 52), fill=(20, 20, 20), anchor='rm')
    d.text((30, 220), 'Cylinder 33 g CO₂', font=F('reg', 40), fill=(40, 40, 40), anchor='lm')
    im.save(out + '.png')

def gauge(out, needle):
    w = 400; im = Image.new('RGB', (w, w), (240, 240, 236)); d = ImageDraw.Draw(im); c = w / 2
    d.pieslice([30, 30, w - 30, w - 30], 200, 250, fill=(220, 40, 30)); d.pieslice([30, 30, w - 30, w - 30], 250, 290, fill=(40, 170, 70))
    d.pieslice([30, 30, w - 30, w - 30], 290, 340, fill=(220, 40, 30)); d.ellipse([90, 90, w - 90, w - 90], fill=(240, 240, 236))
    d.text((c, 290), 'RECHARGE', font=F('bold', 34), fill=(60, 60, 60), anchor='mm')
    a = math.radians({'green': 270, 'red': 215}[needle])
    d.line([(c, c), (c + math.cos(a) * 150, c + math.sin(a) * 150)], fill=(20, 20, 20), width=12); d.ellipse([c - 18, c - 18, c + 18, c + 18], fill=(20, 20, 20))
    im.save(out + '.png')

def ext_label(out):
    w, h = 400, 700; im = Image.new('RGB', (w, h), (190, 24, 24)); d = ImageDraw.Draw(im)
    d.rectangle([30, 120, w - 30, 600], fill=(246, 244, 236))
    d.text((w / 2, 190), 'FIRE', font=F('bold', 76), fill=(190, 24, 24), anchor='mm'); d.text((w / 2, 270), 'EXTINGUISHER', font=F('narrow', 50), fill=(190, 24, 24), anchor='mm')
    d.text((w / 2, 380), 'ABC powder', font=F('bold', 44), fill=(30, 30, 30), anchor='mm'); d.text((w / 2, 450), '2 kg', font=F('bold', 60), fill=(30, 30, 30), anchor='mm')
    d.text((w / 2, 545), 'service 05/26', font=F('reg', 36), fill=(30, 30, 30), anchor='mm')
    im.save(out + '.png')

def fireport_label(out):
    w, h = 500, 160; im = Image.new('RGB', (w, h), (190, 24, 24)); d = ImageDraw.Draw(im)
    d.text((w / 2, h / 2), 'FIRE PORT', font=F('bold', 70), fill=(255, 255, 255), anchor='mm'); im.save(out + '.png')

def raft_label(out):
    w, h = 700, 260; im = Image.new('RGB', (w, h), (245, 245, 240)); d = ImageDraw.Draw(im)
    d.text((w / 2, 70), 'LIFERAFT · 8 PERSONS', font=F('bold', 52), fill=(30, 30, 30), anchor='mm')
    d.text((w / 2, 160), 'service due 04 / 2027', font=F('bold', 46), fill=(190, 24, 24), anchor='mm')
    d.text((w / 2, 220), 'pull painter to inflate', font=F('reg', 36), fill=(30, 30, 30), anchor='mm')
    im.save(out + '.png')

def sign(out, text, bg=(20, 60, 130), fg=(255, 255, 255), w=900, h=300):
    im = Image.new('RGB', (w, h), bg); d = ImageDraw.Draw(im)
    d.text((w / 2, h / 2), text, font=F('bold', int(h * 0.55)), fill=fg, anchor='mm'); im.save(out + '.png')

JOBS = {'nav1': nav1, 'nav3': nav3, 'nav4': nav4, 'papers3': papers3,
        'lcd-log': lambda o: lcd(o, 'SPEED', '6.0', 'KTS', 'log'), 'lcd-sog': lambda o: lcd(o, 'SOG', '4.2', 'KTS', 'GPS'),
        'lcd-depth': lambda o: lcd(o, 'DEPTH', '42.0', 'M'),
        'licence': licence, 'src': src, 'passport': passport, 'crewlist': crewlist, 'booking': booking, 'card': card, 'contract': contract,
        'terminal': terminal, 'checkin': checkin_form, 'service': service_label, 'gauge-green': lambda o: gauge(o, 'green'),
        'gauge-red': lambda o: gauge(o, 'red'), 'ext-label': ext_label, 'fireport': fireport_label, 'raft-label': raft_label,
        'sign-fuel': lambda o: sign(o, 'FUEL', (200, 30, 40)), 'sign-base': lambda o: sign(o, 'CHARTER BASE', (18, 60, 92), w=1600)}

if __name__ == '__main__':
    outdir = sys.argv[1]; names = sys.argv[2:] or list(JOBS)
    os.makedirs(outdir, exist_ok=True)
    for n in names: JOBS[n](os.path.join(outdir, n)); print('tex', n)
