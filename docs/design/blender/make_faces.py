# Draws instrument faces as PNG textures for the Blender instrument figures (system Python with Pillow; Blender's
# own Python has none, so the figure scripts call this through subprocess).
#   python3 make_faces.py tach  OUT.png HOURS          tachometer 0-4 x1000 rpm with an hour counter window
#   python3 make_faces.py volts OUT.png VALUE          voltmeter 8-16 V (the needle is a separate 3D part)
#   python3 make_faces.py fuel  OUT.png                fuel gauge E 1/4 1/2 3/4 F
#   python3 make_faces.py card  OUT.png                compass card, 5-degree ticks, numbers every 30, N E S W
import math, sys
from PIL import Image, ImageDraw, ImageFont

BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'; REG = '/System/Library/Fonts/Supplemental/Arial.ttf'
S = 1024; C = S / 2

def f(path, n): return ImageFont.truetype(path, n)

def arc_scale(d, a0, a1, n_major, n_minor, r_out, labels, font, col=(235, 235, 230)):
    """Ticks and numbers on an arc from angle a0 to a1 (degrees, clockwise from 12 o'clock)."""
    for i in range(n_major * n_minor + 1):
        a = math.radians(a0 + (a1 - a0) * i / (n_major * n_minor)); major = i % n_minor == 0
        r_in = r_out - (60 if major else 32)
        d.line([(C + math.sin(a) * r_in, C - math.cos(a) * r_in), (C + math.sin(a) * r_out, C - math.cos(a) * r_out)], fill=col, width=12 if major else 6)
        if major and labels:
            t = labels[i // n_minor]; rr = r_out - 125
            d.text((C + math.sin(a) * rr, C - math.cos(a) * rr), t, font=font, fill=col, anchor='mm')

def dial_base():
    im = Image.new('RGB', (S, S), (14, 15, 17)); d = ImageDraw.Draw(im)
    return im, d

def tach(out, hours):
    im, d = dial_base()
    arc_scale(d, -135, 135, 8, 5, 470, [str(v // 2) if v % 2 == 0 else '' for v in range(9)], f(BOLD, 110))
    # red zone above 3500 rpm
    d.arc([C - 470, C - 470, C + 470, C + 470], -90 + 135 - 270 * 1 / 8 - 0, -90 + 135, fill=(200, 30, 30), width=26)
    d.text((C, C - 190), 'x1000 r/min', font=f(REG, 52), fill=(200, 200, 195), anchor='mm')
    # hour counter: a black window with white digits, the last one on a white wheel (tenths)
    w, h = 380, 104; x0, y0 = C - w / 2, C + 150
    d.rectangle([x0 - 8, y0 - 8, x0 + w + 8, y0 + h + 8], fill=(60, 62, 66))
    whole, tenth = hours.split('.') if '.' in hours else (hours, '0')
    digits = list(whole.rjust(5, '0')) + [tenth]
    cw = w / len(digits)
    for i, ch in enumerate(digits):
        last = i == len(digits) - 1
        d.rectangle([x0 + i * cw + 3, y0, x0 + (i + 1) * cw - 3, y0 + h], fill=(235, 235, 230) if last else (8, 8, 9))
        d.text((x0 + (i + 0.5) * cw, y0 + h / 2 + 2), ch, font=f(BOLD, 86), fill=(10, 10, 10) if last else (240, 240, 235), anchor='mm')
    d.text((C, y0 + h + 52), 'HOURS', font=f(REG, 44), fill=(200, 200, 195), anchor='mm')
    im.save(out)

def volts(out):
    im, d = dial_base()
    arc_scale(d, -60, 60, 4, 4, 470, ['8', '10', '12', '14', '16'], f(BOLD, 96))
    d.arc([C - 470, C - 470, C + 470, C + 470], -90 - 60, -90 - 60 + 30, fill=(200, 30, 30), width=26)
    d.text((C, C + 170), 'VOLTS', font=f(REG, 64), fill=(200, 200, 195), anchor='mm')
    im.save(out)

def fuel(out):
    im, d = dial_base()
    arc_scale(d, -60, 60, 4, 2, 470, ['E', '¼', '½', '¾', 'F'], f(BOLD, 100))
    d.text((C, C + 170), 'FUEL', font=f(REG, 64), fill=(200, 200, 195), anchor='mm')
    im.save(out)

def card(out):
    """A compass card seen from above: white figures on black, the card turns so the heading sits under the
    lubber line. Degrees run clockwise; 0 at the top of the image."""
    im = Image.new('RGB', (S, S), (16, 17, 19)); d = ImageDraw.Draw(im)
    for deg in range(0, 360, 5):
        a = math.radians(deg); major = deg % 10 == 0; r_out = 500; r_in = r_out - (70 if deg % 30 == 0 else 46 if major else 28)
        d.line([(C + math.sin(a) * r_in, C - math.cos(a) * r_in), (C + math.sin(a) * r_out, C - math.cos(a) * r_out)], fill=(235, 235, 228), width=9 if major else 5)
    big = f(BOLD, 92)
    for deg in range(0, 360, 30):
        a = math.radians(deg); rr = 360
        t = {0: 'N', 90: 'E', 180: 'S', 270: 'W'}.get(deg, str(deg // 10))
        tx = Image.new('RGBA', (220, 140), (0, 0, 0, 0)); td = ImageDraw.Draw(tx)
        td.text((110, 70), t, font=big if deg % 90 == 0 else f(BOLD, 74), fill=(255, 140, 40) if deg == 0 else (240, 240, 235), anchor='mm')
        tx = tx.rotate(-deg, expand=True, resample=Image.BICUBIC)
        im.paste(tx, (int(C + math.sin(a) * rr - tx.width / 2), int(C - math.cos(a) * rr - tx.height / 2)), tx)
    for deg in range(0, 360, 10):
        if deg % 30 == 0: continue
        a = math.radians(deg); rr = 410
        tx = Image.new('RGBA', (120, 80), (0, 0, 0, 0)); ImageDraw.Draw(tx).text((60, 40), str(deg), font=f(REG, 40), fill=(200, 200, 195), anchor='mm')
        tx = tx.rotate(-deg, expand=True, resample=Image.BICUBIC)
        im.paste(tx, (int(C + math.sin(a) * rr - tx.width / 2), int(C - math.cos(a) * rr - tx.height / 2)), tx)
    d.ellipse([C - 150, C - 150, C + 150, C + 150], outline=(90, 92, 96), width=6)
    im.save(out)

if __name__ == '__main__':
    kind, out = sys.argv[1], sys.argv[2]
    {'tach': lambda: tach(out, sys.argv[3] if len(sys.argv) > 3 else '0.0'), 'volts': lambda: volts(out),
     'fuel': lambda: fuel(out), 'card': lambda: card(out)}[kind]()
