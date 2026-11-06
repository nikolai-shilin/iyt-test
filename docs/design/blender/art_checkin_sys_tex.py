# Textures for the Charter Check-in system figures of art_checkin_{electrics,engine,plumbing,return}.py (system Python
# with Pillow; Blender's own Python has none, so art_checkin_sys_kit.tex() calls this through subprocess). Each texture
# is written into the article's own folder, tex/<name>.png.
#   python3 art_checkin_sys_tex.py KIND OUT.png [ARGS...]
#   switch OUT LABEL              a round label plate for a rotary battery switch: LABEL on top, OFF left, ON below
#   battery OUT TEXT              the label on a battery's side ("12 V|100 Ah|AGM")
#   plate OUT KIND                a printed panel plate: water | bilge
#   form OUT KIND                 paper: checkin (engine hours 2 290) | checkout (1 421) | settlement
#   phone OUT KIND                a phone screen: hours1371 (the check-in photo of the hour meter)
#   pedestal OUT                  the front of a pontoon power pedestal
#   sticker OUT TEXT              a small white sticker with black text ("TANK|SEA")
#   inset MAIN.jpg INSET.jpg TEXT an inset render pasted bottom right of MAIN, its label added to MAIN's labels file
import math, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SUP = '/System/Library/Fonts/Supplemental/'
BOLD, REG = SUP + 'Arial Bold.ttf', SUP + 'Arial.ttf'
HAND, MONO = SUP + 'Bradley Hand Bold.ttf', '/System/Library/Fonts/Menlo.ttc'
def f(p, n): return ImageFont.truetype(p, int(n))

def switch(out, label):
    S = 512; im = Image.new('RGB', (S, S), (22, 23, 25)); d = ImageDraw.Draw(im); c = S / 2
    d.ellipse([10, 10, S - 10, S - 10], fill=(200, 30, 30)); d.ellipse([40, 40, S - 40, S - 40], fill=(28, 29, 32))
    d.text((c, 92), label, font=f(BOLD, 52 if len(label) < 8 else 40), fill=(240, 240, 235), anchor='mm')
    d.text((92, c + 6), 'OFF', font=f(BOLD, 40), fill=(240, 240, 235), anchor='mm')
    d.text((c, S - 72), 'ON', font=f(BOLD, 40), fill=(240, 240, 235), anchor='mm')
    im.save(out)

def battery(out, text):
    w, h = 1024, 520; im = Image.new('RGB', (w, h), (30, 32, 36)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 90], fill=(200, 140, 20)); d.text((40, 45), 'DEEP CYCLE', font=f(BOLD, 56), fill=(20, 20, 20), anchor='lm')
    y = 190
    for i, t in enumerate(text.split('|')):
        d.text((50, y), t, font=f(BOLD, 120 if i < 2 else 64), fill=(240, 240, 235), anchor='lm'); y += 135 if i < 2 else 90
    im.save(out)

def plate(out, kind):
    w, h = 2040, 900; im = Image.new('RGB', (w, h), (26, 27, 30)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, w - 10, h - 10], 40, outline=(70, 72, 76), width=6)
    fb, ink = f(BOLD, 46), (200, 200, 195)
    if kind == 'water':
        d.text((w / 2, 70), 'FRESH WATER', font=f(BOLD, 52), fill=ink, anchor='mm')
        d.text((700, 830), 'LITRES', font=fb, fill=ink, anchor='mm')
        d.text((1500, 300), 'TANK', font=fb, fill=ink, anchor='mm')
        d.text((1300, 560), '1', font=f(BOLD, 60), fill=ink, anchor='mm'); d.text((1700, 560), '2', font=f(BOLD, 60), fill=ink, anchor='mm')
        d.text((1500, 830), 'PUMP', font=fb, fill=ink, anchor='mm')
    elif kind == 'bilge':
        d.text((w / 2, 70), 'BILGE PUMP', font=f(BOLD, 52), fill=ink, anchor='mm')
        d.text((1500, 830), 'OFF  AUTO  ON', font=fb, fill=ink, anchor='mm')
    im.save(out)

def form(out, kind):
    w, h = 1240, 1754; im = Image.new('RGB', (w, h), (246, 244, 238)); d = ImageDraw.Draw(im)
    navy, ink, red = (24, 44, 84), (28, 30, 40), (200, 30, 30)
    if kind in ('checkin', 'checkout'):
        d.rectangle([0, 0, w, 210], fill=navy)
        d.text((70, 105), 'CHECK-IN FORM' if kind == 'checkin' else 'CHECK-OUT FORM', font=f(BOLD, 84), fill=(255, 255, 255), anchor='lm')
        d.text((w - 70, 105), 'yacht Nefeli', font=f(BOLD, 52), fill=(220, 226, 240), anchor='rm')
        rows = [('Date', 'Sat 14 June' if kind == 'checkin' else 'Sat 21 June'), ('Skipper', 'N. Petrov'),
                ('Engine hours', '2 290' if kind == 'checkin' else '1 421'), ('Fuel', 'Full'), ('Water', 'Full'),
                ('Holding tank', 'Empty'), ('Dinghy, outboard', 'OK'), ('Damage', 'none noted')]
        y = 330
        for k, v in rows:
            d.text((80, y), k, font=f(REG, 50), fill=(90, 92, 100), anchor='lm')
            d.text((560, y), v, font=f(HAND, 74), fill=ink, anchor='lm')
            d.line([(80, y + 58), (w - 80, y + 58)], fill=(200, 196, 186), width=3)
            if k == 'Engine hours': d.ellipse([520, y - 70, 860, y + 70], outline=red, width=9)
            y += 150
        d.text((80, h - 230), 'Signature', font=f(REG, 50), fill=(90, 92, 100), anchor='lm'); d.line([(360, h - 200), (w - 80, h - 200)], fill=(120, 120, 120), width=3)
    elif kind == 'settlement':
        d.text((80, 120), 'DAMAGE SETTLEMENT', font=f(BOLD, 76), fill=navy, anchor='lm')
        d.text((80, 210), 'Excess: €500 per incident', font=f(REG, 52), fill=(80, 80, 90), anchor='lm')
        y = 350
        for day, what, rep, pay in (('Mon', 'gelcoat chip', '€350', '€350'), ('Thu', 'bent pulpit', '€900', '€500')):
            d.text((80, y), day, font=f(BOLD, 56), fill=ink, anchor='lm'); d.text((240, y), what, font=f(REG, 56), fill=ink, anchor='lm')
            d.text((80, y + 90), 'repair ' + rep, font=f(REG, 50), fill=(90, 92, 100), anchor='lm')
            d.text((w - 80, y + 90), 'you pay ' + pay, font=f(BOLD, 56), fill=red if rep != pay else ink, anchor='rm')
            d.line([(80, y + 160), (w - 80, y + 160)], fill=(200, 196, 186), width=3); y += 260
        d.text((80, y + 40), 'From the deposit', font=f(BOLD, 60), fill=ink, anchor='lm'); d.text((w - 80, y + 40), '€850', font=f(BOLD, 86), fill=navy, anchor='rm')
        d.line([(80, y + 110), (w - 80, y + 110)], fill=navy, width=6)
        d.text((80, h - 220), 'Signed after the inspection', font=f(REG, 46), fill=(90, 92, 100), anchor='lm')
        pts = [(140 + i * 9, h - 140 + 22 * math.sin(i * 0.35) + 10 * math.sin(i * 1.2)) for i in range(50)]
        d.line(pts, fill=(30, 40, 90), width=6)
    im.filter(ImageFilter.GaussianBlur(0.5)).save(out)

def phone(out, kind):
    w, h = 600, 1240; im = Image.new('RGB', (w, h), (12, 12, 14)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 90], fill=(20, 20, 24)); d.text((w / 2, 50), 'Photos', font=f(BOLD, 40), fill=(240, 240, 240), anchor='mm')
    d.rectangle([0, 220, w, 860], fill=(26, 27, 30)); d.ellipse([20, 240, w - 20, 840], fill=(14, 15, 17), outline=(180, 180, 175), width=10)
    digits = '013710' if kind == 'hours1371' else '000000'
    x0, cw, y0 = 75, 75, 560
    d.rectangle([x0 - 8, y0 - 8, x0 + cw * 6 + 8, y0 + 110], fill=(60, 62, 66))
    for i, ch in enumerate(digits):
        last = i == 5
        d.rectangle([x0 + i * cw + 3, y0, x0 + (i + 1) * cw - 3, y0 + 102], fill=(235, 235, 230) if last else (8, 8, 9))
        d.text((x0 + (i + 0.5) * cw, y0 + 52), ch, font=f(BOLD, 80), fill=(10, 10, 10) if last else (240, 240, 235), anchor='mm')
    d.text((w / 2, 720), 'HOURS', font=f(REG, 40), fill=(200, 200, 195), anchor='mm')
    d.text((40, 930), 'Sat 14 June · 10:42', font=f(BOLD, 44), fill=(240, 240, 240), anchor='lm')
    d.text((40, 995), 'check-in, engine panel', font=f(REG, 40), fill=(170, 170, 175), anchor='lm')
    im.save(out)

def pgauge(out):
    """A small gas regulator pressure gauge: 0-4 bar, a green band, white on black."""
    S = 512; c = S / 2; im = Image.new('RGB', (S, S), (240, 240, 236)); d = ImageDraw.Draw(im)
    d.arc([40, 40, S - 40, S - 40], 135, 225 + 90 - 45, fill=(40, 160, 70), width=26)
    for i in range(9):
        a = math.radians(-135 + 270 * i / 8); r0, r1 = 200 - (30 if i % 2 == 0 else 15), 200
        d.line([(c + math.sin(a) * r0, c - math.cos(a) * r0), (c + math.sin(a) * r1, c - math.cos(a) * r1)], fill=(20, 20, 20), width=8)
        if i % 2 == 0: d.text((c + math.sin(a) * 140, c - math.cos(a) * 140), str(i // 2), font=f(BOLD, 48), fill=(20, 20, 20), anchor='mm')
    d.text((c, c + 120), 'bar', font=f(BOLD, 40), fill=(20, 20, 20), anchor='mm')
    im.save(out)

def pedestal(out):
    w, h = 600, 1000; im = Image.new('RGB', (w, h), (232, 234, 230)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 140], fill=(20, 90, 160)); d.text((w / 2, 72), 'B 14', font=f(BOLD, 90), fill=(255, 255, 255), anchor='mm')
    d.text((w / 2, 200), '230 V  16 A', font=f(BOLD, 60), fill=(30, 30, 30), anchor='mm')
    d.rectangle([80, 260, w - 80, 420], outline=(60, 60, 60), width=5)
    d.text((w / 2, 300), 'SWITCH', font=f(BOLD, 40), fill=(60, 60, 60), anchor='mm')
    d.text((w / 2, 380), 'OFF  ·  ON', font=f(BOLD, 40), fill=(60, 60, 60), anchor='mm')
    d.text((w / 2, 920), 'WATER', font=f(BOLD, 46), fill=(20, 90, 160), anchor='mm')
    im.save(out)

def sticker(out, text):
    lines = text.split('|'); w, h = 900, 120 + 130 * len(lines); im = Image.new('RGB', (w, h), (240, 238, 230)); d = ImageDraw.Draw(im)
    d.rectangle([8, 8, w - 8, h - 8], outline=(40, 40, 40), width=8)
    for i, t in enumerate(lines): d.text((w / 2, 125 + i * 130), t, font=f(BOLD, 96), fill=(25, 25, 25), anchor='mm')
    im.save(out)

def inset(main, ins, text):
    """Paste an inset render into the bottom-right corner of the main render and add its label to the labels file."""
    import json, os
    im = Image.open(main).convert('RGB'); sm = Image.open(ins).convert('RGB')
    w = int(im.width * 0.36); sm = sm.resize((w, int(w * sm.height / sm.width)), Image.LANCZOS)
    x, y = im.width - w - 26, im.height - sm.height - 26
    d = ImageDraw.Draw(im); d.rounded_rectangle([x - 6, y - 6, x + w + 6, y + sm.height + 6], 14, fill=(255, 255, 255))
    im.paste(sm, (x, y)); im.save(main, quality=92)
    lp = os.path.splitext(main)[0] + '.labels.json'; lab = json.load(open(lp)); k = im.width / 1280
    lab['labels'].append({'text': text, 'x': (x + w * 0.5) / k, 'y': (y + sm.height * 0.25) / k, 'color': 'red'})
    json.dump(lab, open(lp, 'w'))

if __name__ == '__main__':
    k, out, a = sys.argv[1], sys.argv[2], sys.argv[3:]
    {'switch': lambda: switch(out, a[0]), 'battery': lambda: battery(out, a[0]), 'plate': lambda: plate(out, a[0]),
     'form': lambda: form(out, a[0]), 'phone': lambda: phone(out, a[0]), 'pedestal': lambda: pedestal(out), 'pgauge': lambda: pgauge(out), 'sticker': lambda: sticker(out, a[0]), 'inset': lambda: inset(out, a[0], a[1])}[k]()
