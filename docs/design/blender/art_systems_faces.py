# Faces for the systems figures (system Python with Pillow; Blender's own Python has none). Adds to make_faces.py:
#   temp OUT.png            engine temperature 40-120 °C, red from 100
#   litres OUT.png FULL     a tank gauge in litres, 0..FULL
#   lcd OUT.png W H "line|line|..."   a backlit LCD: lines "TEXT" or "TEXT@red" for a red line
#   plate OUT.png KIND      the engine panel's printed plate (lamp symbols and captions); KIND engine|power|water
import math, sys
from PIL import Image, ImageDraw, ImageFont
BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'; REG = '/System/Library/Fonts/Supplemental/Arial.ttf'
MONO = '/System/Library/Fonts/Menlo.ttc'
S = 1024; C = S / 2
def f(p, n): return ImageFont.truetype(p, n)

def scale(d, a0, a1, labels, minor, r_out=470, red_from=None, font=None):
    n = (len(labels) - 1) * minor
    if red_from is not None:
        a = -90 + a0 + (a1 - a0) * red_from
        d.arc([C - r_out, C - r_out, C + r_out, C + r_out], a, -90 + a1, fill=(200, 30, 30), width=28)
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n); major = i % minor == 0; r_in = r_out - (60 if major else 32)
        d.line([(C + math.sin(a) * r_in, C - math.cos(a) * r_in), (C + math.sin(a) * r_out, C - math.cos(a) * r_out)], fill=(235, 235, 230), width=12 if major else 6)
        if major:
            rr = r_out - 125; d.text((C + math.sin(a) * rr, C - math.cos(a) * rr), labels[i // minor], font=font or f(BOLD, 92), fill=(235, 235, 230), anchor='mm')

def temp(out):
    im = Image.new('RGB', (S, S), (14, 15, 17)); d = ImageDraw.Draw(im)
    scale(d, -60, 60, ['40', '60', '80', '100', '120'], 4, red_from=0.75)
    d.text((C, C + 150), '°C', font=f(BOLD, 80), fill=(200, 200, 195), anchor='mm'); d.text((C, C + 240), 'WATER', font=f(REG, 56), fill=(200, 200, 195), anchor='mm')
    im.save(out)

def litres(out, full):
    full = int(full); im = Image.new('RGB', (S, S), (14, 15, 17)); d = ImageDraw.Draw(im)
    scale(d, -60, 60, [str(int(full * k / 4)) for k in range(5)], 2, red_from=None, font=f(BOLD, 74))
    d.arc([C - 470, C - 470, C + 470, C + 470], -150, -150 + 15, fill=(200, 30, 30), width=28)
    d.text((C, C + 160), 'LITRES', font=f(REG, 60), fill=(200, 200, 195), anchor='mm')
    im.save(out)

def lcd(out, w, h, text):
    w, h = int(w), int(h); im = Image.new('RGB', (w, h), (150, 178, 160)); d = ImageDraw.Draw(im)
    lines = text.split('|'); lh = h / (len(lines) + 0.4)
    for i, ln in enumerate(lines):
        red = ln.endswith('@red'); ln = ln.replace('@red', '')
        if red: d.rectangle([12, 0.2 * lh + i * lh + 6, w - 12, 0.2 * lh + (i + 1) * lh - 6], fill=(170, 30, 30))
        d.text((24, 0.2 * lh + (i + 0.5) * lh), ln, font=f(MONO, int(lh * 0.62)), fill=(255, 240, 235) if red else (20, 28, 24), anchor='lm')
    im.save(out)

def plate(out, kind):
    w, h = 2040, 900; im = Image.new('RGB', (w, h), (26, 27, 30)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, w - 10, h - 10], 40, outline=(70, 72, 76), width=6)
    fb = f(BOLD, 46)
    if kind == 'engine':
        for x, t in ((180, 'OIL'), (360, 'CHARGE'), (540, 'TEMP')): d.text((x, 830), t, font=fb, fill=(200, 200, 195), anchor='mm')
        for x, t in ((1250, 'KEY'), (1520, 'START'), (1740, 'STOP')): d.text((x, 830), t, font=fb, fill=(200, 200, 195), anchor='mm')
    elif kind == 'power':
        for x, t in ((330, 'HOUSE'), (1020, 'ENGINE'), (1710, 'SOLAR')): d.text((x, 830), t, font=fb, fill=(200, 200, 195), anchor='mm')
        d.text((w / 2, 70), 'BATTERY MONITOR', font=f(BOLD, 52), fill=(200, 200, 195), anchor='mm')
    elif kind == 'water':
        d.text((w / 2, 830), 'BOTH TANKS', font=fb, fill=(200, 200, 195), anchor='mm')
        d.text((w / 2, 70), 'FRESH WATER', font=f(BOLD, 52), fill=(200, 200, 195), anchor='mm')
    im.save(out)

def inset(main, ins):
    """Paste the exhaust inset into the bottom-right corner of the main render and add its label."""
    import json, os
    im = Image.open(main).convert('RGB'); sm = Image.open(ins).convert('RGB')
    w = int(im.width * 0.36); sm = sm.resize((w, int(w * sm.height / sm.width)), Image.LANCZOS)
    x, y = im.width - w - 26, im.height - sm.height - 26
    d = ImageDraw.Draw(im); d.rounded_rectangle([x - 6, y - 6, x + w + 6, y + sm.height + 6], 14, fill=(255, 255, 255))
    im.paste(sm, (x, y)); im.save(main, quality=92)
    lp = os.path.splitext(main)[0] + '.labels.json'; lab = json.load(open(lp)); k = im.width / 1280
    lab['labels'].append({'text': 'exhaust: a trickle', 'x': (x + w * 0.5) / k, 'y': (y + sm.height * 0.25) / k, 'color': 'red'})
    json.dump(lab, open(lp, 'w'))

if __name__ == '__main__':
    k, out = sys.argv[1], sys.argv[2]; a = sys.argv[3:]
    {'temp': lambda: temp(out), 'litres': lambda: litres(out, a[0]), 'lcd': lambda: lcd(out, a[0], a[1], a[2]), 'plate': lambda: plate(out, a[0]), 'inset': lambda: inset(out, a[0])}[k]()
