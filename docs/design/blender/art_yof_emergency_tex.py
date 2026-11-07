# Textures for the Yachtmaster Offshore emergency renders (art_yof_emergency.py): the engine-room fire panel and the
# fixed-system release box, the DC panel and battery monitor, a pencilled paper chart, the deck log page, the
# insurance schedule and its written extension, the labels of the grab-bag beacons. System Python with Pillow
# (Blender's Python has no PIL); the Blender script runs it when a texture is missing, into the article's tex/.
# Documents also write <name>.json: anchor points as fractions (u across, v up) of the image, for label pills.
#   python3 docs/design/blender/art_yof_emergency_tex.py <outdir> [name ...]     (no names: all of them)
import os, sys, json, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SUP = '/System/Library/Fonts/Supplemental/'
FONTS = {'bold': SUP + 'Arial Bold.ttf', 'reg': SUP + 'Arial.ttf', 'ital': SUP + 'Arial Italic.ttf', 'din': SUP + 'DIN Condensed Bold.ttf',
         'dina': SUP + 'DIN Alternate Bold.ttf', 'narrow': SUP + 'Arial Narrow Bold.ttf', 'hand': SUP + 'Bradley Hand Bold.ttf',
         'serif': SUP + 'Georgia Bold.ttf', 'serif_r': SUP + 'Georgia.ttf', 'mono': '/System/Library/Fonts/Menlo.ttc'}
def F(k, n): return ImageFont.truetype(FONTS[k], int(n))
INK, PENCIL, BLUE_INK = (24, 30, 44), (70, 72, 78), (28, 40, 110)

def anchors(out, w, h, pts):
    json.dump({k: [x / w, 1 - y / h] for k, (x, y) in pts.items()}, open(out + '.json', 'w'))

def led(d, x, y, r, rgb, lit=True):
    if lit:
        for k in range(6, 0, -1):
            a = k / 6; d.ellipse([x - r * (1 + a), y - r * (1 + a), x + r * (1 + a), y + r * (1 + a)], fill=tuple(int(c * (0.25 + 0.1 * (6 - k))) for c in rgb))
        d.ellipse([x - r, y - r, x + r, y + r], fill=rgb); d.ellipse([x - r * 0.4, y - r * 0.5, x + r * 0.2, y - r * 0.1], fill=(255, 240, 230))
    else:
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(c * 0.22) for c in rgb), outline=(60, 60, 60), width=3)

# ---------------------------------------------------------------- 3: the engine-room fire panel and the release box
def firepanel(out):
    w, h = 1400, 900; im = Image.new('RGB', (w, h), (36, 39, 44)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 20, w - 20, h - 20], 30, outline=(80, 84, 90), width=6)
    d.text((70, 95), 'ENGINE ROOM', font=F('bold', 74), fill=(232, 234, 236), anchor='lm')
    d.text((w - 70, 95), 'FIRE & TEMP', font=F('reg', 48), fill=(160, 166, 174), anchor='rm')
    # the alarm strip, lit red
    d.rounded_rectangle([70, 170, w - 70, 330], 18, fill=(150, 14, 12))
    d.rounded_rectangle([84, 184, w - 84, 316], 12, fill=(214, 30, 24))
    d.text((w / 2, 250), 'FIRE  ALARM', font=F('bold', 100), fill=(255, 236, 230), anchor='mm')
    # the temperature read-out
    d.rounded_rectangle([70, 380, 680, 640], 16, fill=(10, 12, 14))
    d.text((100, 420), 'ENG ROOM TEMP', font=F('bold', 40), fill=(150, 156, 162), anchor='lm')
    d.text((375, 545), '95°C', font=F('dina', 170), fill=(255, 64, 40), anchor='mm')
    # fans and flaps
    rows = [('FANS', 'ON', (255, 170, 30), True), ('FLAPS', 'OPEN', (255, 170, 30), True), ('GENERATOR', 'RUN', (60, 230, 90), True)]
    y = 420
    for name, state, rgb, lit in rows:
        d.text((760, y), name, font=F('bold', 50), fill=(220, 224, 228), anchor='lm')
        led(d, 1150, y, 22, rgb, lit); d.text((1200, y), state, font=F('bold', 46), fill=rgb, anchor='lm'); y += 95
    d.text((760, y + 10), 'SILENCE', font=F('bold', 40), fill=(150, 156, 162), anchor='lm')
    d.rounded_rectangle([1100, y - 20, 1330, y + 40], 14, fill=(70, 74, 80)); d.text((1215, y + 10), 'RESET', font=F('bold', 34), fill=(220, 224, 228), anchor='mm')
    d.text((70, h - 120), 'Shut down engines, generator, fans · close flaps before release', font=F('reg', 38), fill=(180, 186, 192), anchor='lm')
    im.save(out + '.png')
    anchors(out, w, h, {'alarm': (w / 2, 175), 'temp': (375, 470), 'fans': (1150, 420), 'gen': (1150, 610)})

def release(out):
    w, h = 800, 1100; im = Image.new('RGB', (w, h), (200, 22, 26)); d = ImageDraw.Draw(im)
    d.rectangle([30, 30, w - 30, h - 30], outline=(255, 255, 255), width=8)
    d.text((w / 2, 120), 'FIXED FIRE', font=F('bold', 84), fill=(255, 255, 255), anchor='mm')
    d.text((w / 2, 215), 'EXTINGUISHER', font=F('bold', 84), fill=(255, 255, 255), anchor='mm')
    d.text((w / 2, 320), 'ENGINE ROOM', font=F('bold', 56), fill=(255, 230, 220), anchor='mm')
    d.rectangle([60, 380, w - 60, 400], fill=(255, 255, 255))
    for i, t in enumerate(['1  STOP ENGINES, FANS', '2  CLOSE FLAPS, DOOR', '3  EVERYONE OUT: COUNT', '4  PULL TO RELEASE']):
        d.text((80, 460 + i * 80), t, font=F('narrow', 54), fill=(255, 255, 255), anchor='lm')
    d.rounded_rectangle([200, 800, 600, 1020], 20, fill=(150, 12, 14), outline=(255, 255, 255), width=6)
    d.text((w / 2, 910), 'PULL', font=F('bold', 110), fill=(255, 255, 255), anchor='mm')
    im.save(out + '.png')

# ---------------------------------------------------------------- 6: the DC panel, the battery monitor, the chart
DC = [('NAV LIGHTS', True), ('ANCHOR LIGHT', False), ('STEAMING LIGHT', False), ('VHF', True), ('INSTRUMENTS', False),
      ('PLOTTER · RADAR', False), ('AUTOPILOT', False), ('FRIDGE', False), ('WATER PUMP', False), ('CABIN LIGHTS', False)]
def dcpanel(out):
    w, h = 1000, 1500; im = Image.new('RGB', (w, h), (30, 32, 36)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 14, w - 14, h - 14], 24, outline=(90, 94, 100), width=6)
    d.text((w / 2, 80), 'DC 12 V', font=F('bold', 64), fill=(230, 232, 236), anchor='mm')
    y0, step = 190, 125; pts = {}
    for i, (name, on) in enumerate(DC):
        y = y0 + i * step
        led(d, 90, y, 16, (60, 235, 90) if on else (60, 235, 90), on)
        d.text((150, y), name, font=F('bold', 44), fill=(235, 238, 240) if on else (150, 154, 160), anchor='lm')
        d.rounded_rectangle([700, y - 38, 900, y + 38], 10, fill=(18, 19, 22), outline=(70, 72, 78), width=3)
        pts[name] = (800, y)
    im.save(out + '.png'); anchors(out, w, h, pts)
    json.dump({'rows': [[n, on] for n, on in DC], 'y0': y0 / h, 'step': step / h, 'x': 800 / w}, open(out + '-layout.json', 'w'))

def battmon(out):
    w, h = 900, 600; im = Image.new('RGB', (w, h), (8, 10, 12)); d = ImageDraw.Draw(im)
    d.text((40, 60), 'HOUSE', font=F('bold', 48), fill=(150, 170, 190), anchor='lm')
    d.text((w - 40, 60), 'ALT 0.0 A', font=F('bold', 56), fill=(255, 80, 60), anchor='rm')
    d.text((w / 2 - 30, 290), '11.9', font=F('dina', 300), fill=(255, 196, 60), anchor='mm')
    d.text((w - 70, 330), 'V', font=F('bold', 110), fill=(255, 196, 60), anchor='mm')
    d.text((40, 520), '−4.2 A', font=F('bold', 64), fill=(200, 210, 220), anchor='lm')
    d.text((w - 40, 520), 'NO CHARGE', font=F('bold', 56), fill=(255, 80, 60), anchor='rm')
    im.save(out + '.png')

def chartplot(out):
    """A paper chart with the night's plot in pencil: hourly DR positions along 205°T, a fix at 0200."""
    w, h = 2400, 1700; im = Image.new('RGB', (w, h), (236, 238, 230)); d = ImageDraw.Draw(im)
    rnd = random.Random(4)
    # land to the top right, the shallows in blue, depth contours
    land = [(1500, 0), (2400, 0), (2400, 700), (2250, 640), (2120, 520), (1990, 470), (1840, 330), (1700, 260), (1580, 120)]
    for k, col in ((140, (200, 224, 236)), (70, (178, 212, 230))):
        d.polygon([(x - k * 1.6, y + k * 1.2) for x, y in land[:1]] + [(x - k, y + k) for x, y in land[1:]], fill=col)
    d.polygon(land, fill=(238, 222, 160), outline=(130, 112, 60))
    for i in range(60):
        x, y = rnd.uniform(80, 1500), rnd.uniform(400, 1650)
        d.text((x, y), str(rnd.choice([42, 55, 68, 74, 81, 96, 103, 120])), font=F('ital', 30), fill=(70, 90, 110), anchor='mm')
    # lat/long grid
    for x in range(0, w, 400): d.line([(x, 0), (x, h)], fill=(190, 196, 200), width=2)
    for y in range(0, h, 400): d.line([(0, y), (w, y)], fill=(190, 196, 200), width=2)
    # compass rose
    cx, cy, R = 520, 520, 230
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(150, 60, 90), width=4); d.ellipse([cx - R + 40, cy - R + 40, cx + R - 40, cy + R - 40], outline=(150, 60, 90), width=2)
    for a in range(0, 360, 10):
        t = math.radians(a); r0 = R - (30 if a % 30 == 0 else 16)
        d.line([(cx + math.sin(t) * r0, cy - math.cos(t) * r0), (cx + math.sin(t) * R, cy - math.cos(t) * R)], fill=(150, 60, 90), width=3)
    d.polygon([(cx, cy - R + 40), (cx - 16, cy), (cx + 16, cy)], fill=(150, 60, 90))
    # the track in pencil: from 2200 to 0300, course 205°T, 6 kn; hourly DR crosses, a fix circle at 0200
    t = math.radians(205); step = 230; p = [1700, 420]; pts = {}
    pl = []
    for k in range(6):
        pl.append(tuple(p)); p = [p[0] + math.sin(t) * step, p[1] - math.cos(t) * step]
    d.line(pl, fill=PENCIL, width=5)
    for k, (x, y) in enumerate(pl):
        hh = (22 + k) % 24; lab = f'{hh:02d}00'
        if k == 4: d.ellipse([x - 22, y - 22, x + 22, y + 22], outline=PENCIL, width=5); d.point((x, y), fill=PENCIL); lab += ' fix'
        else:
            d.line([(x - 18, y - 18), (x + 18, y + 18)], fill=PENCIL, width=5); d.line([(x - 18, y + 18), (x + 18, y - 18)], fill=PENCIL, width=5)
        d.text((x + 40, y), lab, font=F('hand', 44), fill=PENCIL, anchor='lm')
    mx, my = (pl[1][0] + pl[2][0]) / 2, (pl[1][1] + pl[2][1]) / 2
    d.text((mx - 40, my), '205°T  6 kn', font=F('hand', 46), fill=PENCIL, anchor='rm')
    pts['track'] = pl[3]; pts['fix'] = pl[4]
    im.filter(ImageFilter.GaussianBlur(0.6)).save(out + '.png'); anchors(out, w, h, pts)

# ---------------------------------------------------------------- 12: the deck log
def logbook(out):
    w, h = 2000, 1400; im = Image.new('RGB', (w, h), (246, 243, 232)); d = ImageDraw.Draw(im)
    d.text((80, 80), 'DECK LOG', font=F('serif', 64), fill=INK, anchor='lm')
    d.text((w - 80, 80), 'Thu 12 June · Lisbon – Madeira', font=F('serif_r', 44), fill=(80, 86, 96), anchor='rm')
    cols = [('Time', 170), ('Course °T', 360), ('Log', 230), ('Wind', 210), ('Baro', 170), ('Remarks', 700)]
    y = 170; x = 80
    d.rectangle([80, y, w - 80, y + 80], fill=(222, 226, 222))
    for t, cw in cols:
        d.text((x + 16, y + 40), t, font=F('bold', 40), fill=INK, anchor='lm'); d.line([(x, y), (x, h - 100)], fill=(170, 176, 176), width=2); x += cw
    d.line([(w - 80, y), (w - 80, h - 100)], fill=(170, 176, 176), width=2)
    rows = [('0000', '245', '1062.4', 'N 4', '1018', 'Watch: Ana, Ben'), ('0100', '245', '1068.5', 'N 4', '1018', 'Ship passed 2 M to stbd'),
            ('0200', '245', '1074.3', 'NNE 5', '1017', 'Fix by GPS, on track'), ('0300', '245', '1080.2', 'NNE 5', '1017', 'Reefed main'),
            ('0400', '254', '1086.0', 'NNE 5', '1016', 'Watch: Cara, Dan')]
    y += 80; pts = {}
    hand = F('hand', 56)
    for i, r in enumerate(rows):
        yc = y + 70; x = 80
        for j, ((t, cw), v) in enumerate(zip(cols, r)):
            if i == 3 and j == 1:
                d.text((x + 24, yc), '245', font=hand, fill=BLUE_INK, anchor='lm')
                bw = d.textlength('245', font=hand)
                d.line([(x + 14, yc + 2), (x + 34 + bw, yc - 4)], fill=BLUE_INK, width=6)
                d.text((x + 70 + bw, yc - 6), '254', font=hand, fill=BLUE_INK, anchor='lm')
                d.text((x + 90 + bw * 2, yc + 14), 'JK', font=F('hand', 34), fill=BLUE_INK, anchor='lm')
                pts['struck'] = (x + 24 + bw / 2, yc - 30); pts['new'] = (x + 70 + bw * 1.5, yc - 34)
            else:
                d.text((x + 24, yc), v, font=hand, fill=BLUE_INK, anchor='lm')
            x += cw
        y += 140; d.line([(80, y), (w - 80, y)], fill=(190, 196, 196), width=2)
    pts['page'] = (w / 2, y + 60)
    for k in range(3):
        y2 = y + 140 * (k + 1)
        if y2 < h - 100: d.line([(80, y2), (w - 80, y2)], fill=(190, 196, 196), width=2)
    im.filter(ImageFilter.GaussianBlur(0.6)).save(out + '.png'); anchors(out, w, h, pts)

# ---------------------------------------------------------------- 13: the insurance schedule and its extension
def policy(out):
    w, h = 1240, 1754; im = Image.new('RGB', (w, h), (250, 249, 244)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 200], fill=(26, 46, 82)); d.text((90, 100), 'YACHT POLICY · SCHEDULE', font=F('bold', 64), fill=(255, 255, 255), anchor='lm')
    d.text((90, 270), 'Yacht: S/Y Ardea, 15.2 m · Policy YP-26-41180', font=F('reg', 38), fill=(70, 76, 88), anchor='lm')
    secs = [('Cruising limits', ['Mediterranean, within 60 M of the coast', 'Season 1 April – 31 October', 'Outside these: only by written extension']),
            ('Warranties', ["Skipper holds a Yachtmaster Offshore", 'Private pleasure use only: no paying guests', 'At least two competent crew offshore']),
            ('Cover', ['Hull and machinery: € 380,000', 'Third-party liability: € 3,000,000']),
            ('Disclosure', ['Every material fact disclosed, or the policy is void'])]
    y = 360; pts = {}
    for title, lines in secs:
        d.text((90, y), title, font=F('bold', 50), fill=INK, anchor='lm'); y0 = y; y += 75
        for i, ln in enumerate(lines):
            if title == 'Cruising limits' and i < 2: d.rectangle([84, y - 30, w - 90, y + 30], fill=(255, 236, 120))
            d.text((110, y), ln, font=F('reg', 40), fill=(36, 40, 48), anchor='lm'); y += 62
        pts[title] = (360, y0 - 10); y += 50
    d.line([(90, 1600), (480, 1600)], fill=(120, 120, 120), width=2); d.text((90, 1640), 'Underwriter', font=F('reg', 32), fill=(110, 116, 126), anchor='lm')
    im.filter(ImageFilter.GaussianBlur(0.5)).save(out + '.png'); anchors(out, w, h, pts)

def extension(out):
    w, h = 1240, 1000; im = Image.new('RGB', (w, h), (246, 247, 250)); d = ImageDraw.Draw(im)
    d.text((90, 110), 'ENDORSEMENT No. 2', font=F('bold', 58), fill=INK, anchor='lm')
    d.text((90, 200), 'Policy YP-26-41180 · S/Y Ardea', font=F('reg', 38), fill=(70, 76, 88), anchor='lm')
    for i, ln in enumerate(['Cruising limits extended for the passage', 'Gibraltar – Madeira, 10 – 25 May,', 'two crew besides the skipper.', 'Additional premium: € 240']):
        d.text((90, 320 + i * 70), ln, font=F('reg', 42), fill=(36, 40, 48), anchor='lm')
    d.ellipse([w - 380, h - 380, w - 90, h - 90], outline=(30, 70, 150), width=8); d.text((w - 235, h - 235), 'AGREED', font=F('bold', 52), fill=(30, 70, 150), anchor='mm')
    pts = [(120 + i * 8, h - 170 + 18 * math.sin(i * 0.4) + 9 * math.sin(i * 1.3)) for i in range(45)]; d.line(pts, fill=(30, 40, 90), width=5)
    im.filter(ImageFilter.GaussianBlur(0.5)).save(out + '.png'); anchors(out, w, h, {'ext': (w / 2, 330)})

# ---------------------------------------------------------------- 10: beacon labels
def beacon_label(out, title, lines, bg=(250, 250, 246), band=(232, 92, 18)):
    w, h = 600, 800; im = Image.new('RGB', (w, h), bg); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 170], fill=band); d.text((w / 2, 88), title, font=F('bold', 96 if len(title) < 7 else 74), fill=(255, 255, 255), anchor='mm')
    for i, ln in enumerate(lines): d.text((w / 2, 260 + i * 90), ln, font=F('bold', 54), fill=INK, anchor='mm')
    im.save(out + '.png')

def epirb(out): beacon_label(out, 'EPIRB', ['406 MHz', 'GPS', 'Registered:', 'S/Y Ardea', 'MMSI 2551 0472 0'])
def sart(out): beacon_label(out, 'SART', ['Radar', '9 GHz', 'Search and', 'rescue', 'transponder'])
def aissart(out): beacon_label(out, 'AIS-SART', ['AIS', 'GPS position', 'to every', 'AIS screen'])

ALL = {'firepanel': firepanel, 'release': release, 'dcpanel': dcpanel, 'battmon': battmon, 'chartplot': chartplot,
       'logbook': logbook, 'policy': policy, 'extension': extension, 'epirb': epirb, 'sart': sart, 'aissart': aissart}

if __name__ == '__main__':
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    for n in sys.argv[2:] or list(ALL):
        ALL[n](os.path.join(od, n)); print('wrote', n)
