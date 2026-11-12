# Textures for the Racing Rules figures (art_rr_*.py), drawn with Pillow under the system Python:
#   the signal flags of the International Code of Signals and the race signals (RGBA, the alpha cutting the shape
#   of a swallowtail or a pennant), and the paper of the protest figures (a protest form filled in, the hearing's
#   notes, the rule book cover, the arbitration desk card).
#   python3 docs/design/blender/art_rr_b_tex.py <article> <name> [...]   -> figure-style/articles/racing-rules/<article>/tex/<name>.png
import os, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ARTS = os.path.join(HERE, '..', 'figure-style', 'articles', 'racing-rules')
SUP = '/System/Library/Fonts/Supplemental/'
FONT = {'bold': SUP + 'Arial Bold.ttf', 'reg': SUP + 'Arial.ttf', 'hand': SUP + 'Bradley Hand Bold.ttf', 'serif': SUP + 'Times New Roman Bold.ttf',
        'narrow': SUP + 'Arial Narrow Bold.ttf'}
F = lambda k, n: ImageFont.truetype(FONT[k], int(n))

# the code flag colours (as figures.js draws them, a shade deeper for cloth in sunlight)
BLUE, YEL, RED, BLK, WHT = (12, 70, 160), (255, 205, 0), (205, 28, 30), (16, 16, 18), (246, 246, 242)
FW, FH = 600, 400

def _flag(paint, shape=None):
    im = Image.new('RGBA', (FW, FH), WHT + (255,)); d = ImageDraw.Draw(im); paint(d)
    if shape:
        m = Image.new('L', (FW, FH), 0); ImageDraw.Draw(m).polygon(shape, fill=255); im.putalpha(m)
    return im

def flags():
    sq = lambda d, c: d.rectangle([0, 0, FW, FH], fill=c)
    swallow = [(0, 0), (FW, 0), (FW * 0.77, FH / 2), (FW, FH), (0, FH)]
    def P(d): sq(d, BLUE); a = FH * 0.21; d.rectangle([FW / 2 - a, FH / 2 - a, FW / 2 + a, FH / 2 + a], fill=WHT)
    def I(d): sq(d, YEL); r = FH * 0.24; d.ellipse([FW / 2 - r, FH / 2 - r, FW / 2 + r, FH / 2 + r], fill=BLK)
    def Z(d):
        c = (FW / 2, FH / 2); d.polygon([(0, 0), c, (0, FH)], fill=BLK); d.polygon([(0, 0), (FW, 0), c], fill=YEL)
        d.polygon([(FW, 0), (FW, FH), c], fill=BLUE); d.polygon([(0, FH), (FW, FH), c], fill=RED)
    def U(d): sq(d, WHT); d.rectangle([0, 0, FW / 2, FH / 2], fill=RED); d.rectangle([FW / 2, FH / 2, FW, FH], fill=RED)
    def L(d): sq(d, BLK); d.rectangle([0, 0, FW / 2, FH / 2], fill=YEL); d.rectangle([FW / 2, FH / 2, FW, FH], fill=YEL)
    def X(d): sq(d, WHT); d.rectangle([FW / 2 - FH / 8, 0, FW / 2 + FH / 8, FH], fill=BLUE); d.rectangle([0, FH / 2 - FH / 8, FW, FH / 2 + FH / 8], fill=BLUE)
    def N(d):
        sq(d, WHT)
        for r in range(4):
            for c in range(4):
                if (r + c) % 2 == 0: d.rectangle([c * FW / 4, r * FH / 4, (c + 1) * FW / 4, (r + 1) * FH / 4], fill=BLUE)
    def Y(d):
        sq(d, YEL); k = FW / 7
        for i in range(-6, 14, 2):
            x = i * k; d.polygon([(x, FH), (x + k, FH), (x + k + FH, 0), (x + FH, 0)], fill=RED)
    def O(d): sq(d, YEL); d.polygon([(0, 0), (FW, 0), (FW, FH)], fill=RED)
    def H(d): sq(d, WHT); d.rectangle([FW / 2, 0, FW, FH], fill=RED)
    def A(d): sq(d, BLUE); d.rectangle([0, 0, FW / 2, FH], fill=WHT)
    def B(d): sq(d, RED)
    def AP(d):
        for i in range(5): d.rectangle([i * FW / 5, 0, (i + 1) * FW / 5, FH], fill=RED if i % 2 == 0 else WHT)
    def SUB1(d): sq(d, BLUE); d.polygon([(0, FH * 0.24), (FW * 0.55, FH / 2), (0, FH * 0.76)], fill=YEL)
    out = {'P': _flag(P), 'I': _flag(I), 'Z': _flag(Z), 'U': _flag(U), 'L': _flag(L), 'X': _flag(X), 'N': _flag(N), 'Y': _flag(Y),
           'O': _flag(O), 'H': _flag(H), 'A': _flag(A, swallow), 'B': _flag(B, swallow), 'AP': _flag(AP, [(0, 0), (FW, FH * 0.33), (FW, FH * 0.67), (0, FH)]),
           'first-sub': _flag(SUB1, [(0, 0), (FW, FH / 2), (0, FH)])}
    for k, c in (('black', BLK), ('yellow', YEL), ('red', RED), ('orange', (255, 110, 0)), ('blue', BLUE)):
        out[k] = _flag(lambda d, c=c: sq(d, c))
    return out

# ---------------------------------------------------------------- paper
PAPER, INK, PEN, RULE = (247, 245, 238), (30, 32, 38), (22, 52, 140), (120, 124, 130)

def protest_form():
    w, h = 1240, 1754; im = Image.new('RGB', (w, h), PAPER); d = ImageDraw.Draw(im)
    d.rectangle([60, 60, w - 60, 200], fill=(32, 40, 52))
    d.text((90, 92), 'PROTEST FORM', font=F('bold', 64), fill=(255, 255, 255))
    d.text((w - 90, 112), 'also for redress and reopening', font=F('reg', 28), fill=(210, 214, 220), anchor='ra')
    y = 240
    def box(title, lines, hand, hh, tick=None):
        nonlocal y
        d.rectangle([60, y, w - 60, y + hh], outline=RULE, width=3)
        d.text((80, y + 14), title, font=F('bold', 30), fill=INK)
        for k, (lab, val) in enumerate(lines):
            yy = y + 66 + k * 64
            d.text((80, yy), lab, font=F('reg', 28), fill=(90, 94, 100))
            d.line([(360, yy + 40), (w - 90, yy + 40)], fill=(190, 192, 196), width=2)
            if val: d.text((370, yy - 6), val, font=F('hand', 44), fill=PEN)
        y += hh + 16
    box('1  EVENT', [('Race', '3  ·  Saturday')], True, 140)
    box('2  PROTESTOR', [('Boat, sail no.', 'Tern  GBR 1234'), ('Represented by', 'J. Hall, helm')], True, 200)
    box('3  PROTESTEE', [('Boat, sail no.', 'Blue  GBR 877')], True, 140)
    box('4  INCIDENT', [('Where, when', 'leg 1, 200 m below the windward mark'), ('What happened', 'Blue on port did not keep clear;'), ('', 'we bore away hard to avoid her')], True, 250)
    # informing the protestee: hail and flag ticked
    d.rectangle([60, y, w - 60, y + 150], outline=RULE, width=3); d.text((80, y + 14), '5  INFORMING THE PROTESTEE', font=F('bold', 30), fill=INK)
    for k, (lab, when) in enumerate((('Hail "Protest"', 'at once'), ('Red flag displayed', 'at once'))):
        x = 80 + k * 560; yy = y + 74
        d.rectangle([x, yy, x + 44, yy + 44], outline=INK, width=3)
        d.line([(x + 6, yy + 22), (x + 18, yy + 38), (x + 46, yy - 6)], fill=PEN, width=8)
        d.text((x + 62, yy + 4), lab, font=F('reg', 30), fill=INK); d.text((x + 62 + d.textlength(lab, font=F('reg', 30)) + 18, yy - 10), when, font=F('hand', 40), fill=PEN)
    y += 166
    # the diagram
    d.rectangle([60, y, w - 60, y + 260], outline=RULE, width=3); d.text((80, y + 14), '6  DIAGRAM', font=F('bold', 30), fill=INK)
    def hull(cx, cy, hdg, col):
        a = math.radians(hdg); pts = []
        for px, py in ((0, -60), (21, -15), (18, 45), (-18, 45), (-21, -15)):
            pts.append((cx + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a)))
        d.polygon(pts, outline=col, width=5)
    hull(470, y + 165, 45, PEN); hull(700, y + 150, -45, PEN)
    d.line([(930, y + 70), (930, y + 170)], fill=PEN, width=6); d.polygon([(914, y + 160), (946, y + 160), (930, y + 192)], fill=PEN)
    d.text((955, y + 90), 'wind', font=F('hand', 40), fill=PEN)
    d.text((330, y + 190), 'Blue', font=F('hand', 40), fill=PEN); d.text((740, y + 190), 'Tern', font=F('hand', 40), fill=PEN)
    y += 276
    # received at the race office
    d.rectangle([60, y, w - 60, h - 60], fill=(232, 236, 240), outline=RULE, width=3)
    d.text((80, y + 14), 'RACE OFFICE USE', font=F('bold', 30), fill=INK)
    d.text((80, y + 70), 'Time limit  17:30', font=F('reg', 32), fill=INK)
    cx, cy = 880, y + 95
    stamp = Image.new('RGBA', (320, 170), (0, 0, 0, 0)); sd = ImageDraw.Draw(stamp)
    sd.rounded_rectangle([8, 8, 312, 162], 18, outline=(176, 34, 40, 230), width=8)
    sd.text((160, 48), 'RECEIVED', font=F('bold', 42), fill=(176, 34, 40, 230), anchor='mm'); sd.text((160, 112), '16:42', font=F('bold', 62), fill=(176, 34, 40, 230), anchor='mm')
    stamp = stamp.rotate(-6, expand=True, resample=Image.BICUBIC); im.paste(stamp, (cx - stamp.width // 2, cy - stamp.height // 2), stamp)
    return im.filter(ImageFilter.GaussianBlur(0.5))

def notes():
    """The chairman's pad: the hearing in four steps, filled in."""
    w, h = 1000, 1400; im = Image.new('RGB', (w, h), (250, 247, 226)); d = ImageDraw.Draw(im)
    for yy in range(160, h - 40, 62): d.line([(40, yy), (w - 40, yy)], fill=(170, 196, 220), width=2)
    d.line([(120, 0), (120, h)], fill=(220, 120, 120), width=3)
    d.text((140, 70), 'Protest 7 · Tern v Blue', font=F('hand', 54), fill=PEN)
    rows = [('1  Valid?', 'hail, flag, in time: yes'), ('2  Evidence', 'Tern, Blue, 1 witness'), ('3  Facts', 'Blue on port, no room'),
            ('', 'to cross; Tern bore away'), ('4  Rules', '10: Blue broke it'), ('   Decision', 'Blue DSQ')]
    yy = 165
    for a, b in rows:
        if a: d.text((140, yy), a, font=F('hand', 46), fill=INK)
        d.text((480, yy), b, font=F('hand', 46), fill=PEN); yy += 124
    return im.filter(ImageFilter.GaussianBlur(0.5))

def rulebook():
    w, h = 900, 1260; im = Image.new('RGB', (w, h), (18, 52, 110)); d = ImageDraw.Draw(im)
    d.rectangle([0, h - 300, w, h - 230], fill=(220, 40, 46))
    d.text((70, 140), 'THE RACING', font=F('bold', 110), fill=(255, 255, 255)); d.text((70, 270), 'RULES OF', font=F('bold', 110), fill=(255, 255, 255))
    d.text((70, 400), 'SAILING', font=F('bold', 110), fill=(255, 255, 255)); d.text((70, 580), '2025–2028', font=F('reg', 70), fill=(200, 214, 236))
    return im

def desk_card():
    w, h = 1400, 420; im = Image.new('RGB', (w, h), (250, 250, 247)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 40], fill=(32, 40, 52)); d.rectangle([0, h - 40, w, h], fill=(32, 40, 52))
    d.text((w / 2, h / 2 - 20), 'ARBITRATION', font=F('bold', 150), fill=(20, 24, 30), anchor='mm')
    d.text((w / 2, h / 2 + 105), 'Appendix T', font=F('reg', 60), fill=(90, 96, 104), anchor='mm')
    return im

def penalty_slip():
    w, h = 1240, 877; im = Image.new('RGB', (w, h), PAPER); d = ImageDraw.Draw(im)
    d.rectangle([50, 50, w - 50, 170], fill=(32, 40, 52)); d.text((80, 80), 'POST-RACE PENALTY  30 %', font=F('bold', 56), fill=(255, 255, 255))
    for k, (a, b) in enumerate((('Boat', 'Blue  GBR 877'), ('Race', '3'), ('Protest', '7'))):
        yy = 230 + k * 110; d.text((80, yy), a, font=F('reg', 38), fill=(90, 94, 100)); d.line([(300, yy + 50), (w - 80, yy + 50)], fill=(190, 192, 196), width=2)
        d.text((310, yy - 8), b, font=F('hand', 56), fill=PEN)
    d.text((80, 620), 'Signed', font=F('reg', 38), fill=(90, 94, 100))
    pts = [(300 + i * 9, 640 + 22 * math.sin(i * 0.4) + 10 * math.sin(i * 1.3)) for i in range(50)]; d.line(pts, fill=PEN, width=6)
    return im

PAPERS = {'protest-form': protest_form, 'notes': notes, 'rulebook': rulebook, 'desk-card': desk_card, 'penalty-slip': penalty_slip}

if __name__ == '__main__':
    art, names = sys.argv[1], sys.argv[2:]
    out = os.path.join(ARTS, art, 'tex'); os.makedirs(out, exist_ok=True)
    fl = None
    for n in names:
        if n.startswith('flag-'):
            fl = fl or flags(); fl[n[5:]].save(os.path.join(out, n + '.png'))
        else:
            PAPERS[n]().save(os.path.join(out, n + '.png'))
        print('wrote', os.path.join(out, n + '.png'))
