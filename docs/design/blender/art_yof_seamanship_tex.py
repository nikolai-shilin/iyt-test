# Textures for the Yachtmaster Offshore seamanship renders (art_yof_seamanship.py): the anchor-watch plotter screen
# of figure 6, drawn on the Raymarine Axiom's own front texture (as art_checkin_nps_tex.py does), plus <name>.json
# with the pixel anchors of what the labels point at, in the 828 x 481 frame of the front texture.
# System Python with Pillow; the Blender script runs it when a texture is missing.
#   python3 docs/design/blender/art_yof_seamanship_tex.py <outdir> [name ...]
import os, sys, json, math
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SUP = '/System/Library/Fonts/Supplemental/'
FONTS = {'bold': SUP + 'Arial Bold.ttf', 'reg': SUP + 'Arial.ttf', 'ital': SUP + 'Arial Italic.ttf', 'dina': SUP + 'DIN Alternate Bold.ttf'}
def F(k, n): return ImageFont.truetype(FONTS[k], int(n))

K3 = 3
BOX = (70, 72, 645, 432)                 # the screen glass on the 828 x 481 front
SW, SH = (BOX[2] - BOX[0]) * K3, (BOX[3] - BOX[1]) * K3
def to_front(x, y): return [BOX[0] + x / K3, BOX[1] + y / K3]

def front(screen, out, anchors):
    fr = Image.open(os.path.join(HERE, 'textures', 'axiom-front.png')).convert('RGB')
    fr = fr.resize((fr.width * K3, fr.height * K3), Image.LANCZOS)
    fr.paste(screen.resize((SW, SH), Image.LANCZOS), (BOX[0] * K3, BOX[1] * K3))
    fr.save(out + '.png')
    json.dump({k: to_front(*v) for k, v in anchors.items()}, open(out + '.json', 'w'))

SEA, SEA2, LAND, COAST = (206, 232, 244), (178, 214, 232), (240, 221, 150), (138, 122, 64)

def bezq(p0, p1, p2, n=30):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]

def drag(out):
    """Anchor watch at 0200: the track since 2200, an arc round the anchor while she swung, then since the wind
    veered at 0130 a straight line away downwind: dragging. Night palette is not used: the figure's day chart."""
    im = Image.new('RGB', (SW, SH), SEA); d = ImageDraw.Draw(im)
    # the figure's 320 x 200 drawing scaled into the screen, below the data bar
    k = 4.6; ox, oy = 60, 90
    P = lambda x, y: (ox + x * k, oy + y * k)
    # depth contours and the shore to the north-west, as on the figure's anchorage
    for r in (300, 520, 760):
        d.ellipse([P(20, -40)[0] - r, P(20, -40)[1] - r * 0.7, P(20, -40)[0] + r, P(20, -40)[1] + r * 0.7], outline=(120, 170, 205), width=4)
    d.polygon([P(0, 0), P(150, 0), P(120, 22), P(60, 30), P(0, 40)], fill=LAND, outline=COAST)
    for x, y, t in ((180, 60, '6'), (60, 150, '7'), (150, 190, '8'), (260, 120, '9'), (290, 190, '11')):
        d.text(P(x, y), t, font=F('ital', 46), fill=(40, 70, 100), anchor='mm')
    # the alarm circle round the anchor (dashed) and the anchor
    ax, ay = P(96, 52); R = 60 * k
    for a in range(0, 360, 8):
        a0, a1 = math.radians(a), math.radians(a + 5)
        d.arc([ax - R, ay - R, ax + R, ay + R], a, a + 5, fill=(216, 27, 42), width=6)
    ink = (27, 42, 68)
    d.ellipse([ax - 13, ay - 62, ax + 13, ay - 36], outline=ink, width=8)
    d.line([(ax, ay - 36), (ax, ay + 50)], fill=ink, width=9); d.line([(ax - 28, ay - 18), (ax + 28, ay - 18)], fill=ink, width=9)
    d.arc([ax - 46, ay - 10, ax + 46, ay + 56], 20, 160, fill=ink, width=9)
    # the track: the swinging arc, back, then the straight drag
    pts = bezq((62, 98), (96, 124), (130, 98)) + bezq((130, 98), (100, 120), (70, 102))[1:] + [(176, 150), (236, 178)]
    d.line([P(*p) for p in pts], fill=(216, 27, 42), width=12, joint='curve')
    # the boat at (240, 180) heading 300
    bx, by = P(240, 180); a = math.radians(300)
    Rt = lambda px, py: (bx + px * math.cos(a) - py * math.sin(a), by + px * math.sin(a) + py * math.cos(a))
    d.polygon([Rt(0, -70), Rt(40, 50), Rt(0, 28), Rt(-40, 50)], fill=(17, 17, 17))
    d.line([Rt(0, -70), Rt(0, -230)], fill=(17, 17, 17), width=6)
    # scale bar, data bar, alarm
    d.line([(60, SH - 60), (60 + 25 * k, SH - 60)], fill=(27, 42, 68), width=7)
    d.text((60 + 12.5 * k, SH - 98), '25 m', font=F('bold', 40), fill=(27, 42, 68), anchor='mm')
    d.rectangle([0, 0, SW, 110], fill=(18, 22, 28))
    x = 30
    for lab, val in (('', '02:00'), ('WIND', '27 kn'), ('SOG', '0.9 kn'), ('DEPTH', '9.6 m')):
        if lab: d.text((x, 55), lab, font=F('bold', 36), fill=(150, 170, 186), anchor='lm'); x += d.textlength(lab, font=F('bold', 36)) + 16
        d.text((x, 57), val, font=F('dina', 58), fill=(232, 238, 242), anchor='lm'); x += d.textlength(val, font=F('dina', 58)) + 50
    d.rounded_rectangle([SW - 480, 16, SW - 24, 94], 12, fill=(216, 27, 42))
    d.text((SW - 252, 56), 'ANCHOR ALARM', font=F('bold', 46), fill=(255, 255, 255), anchor='mm')
    d.rounded_rectangle([SW - 470, 140, SW - 30, 224], 14, fill=(18, 22, 28))
    d.text((SW - 250, 182), 'TRACK SINCE 22:00', font=F('bold', 38), fill=(232, 238, 242), anchor='mm')
    anchors = {'anchor': (ax, ay), 'arc': P(96, 118), 'drag': P(196, 160), 'boat': (bx, by), 'alarm': (SW - 252, 56)}
    front(im, out, anchors)

ALL = {'drag': drag}

if __name__ == '__main__':
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    for n in (sys.argv[2:] or ALL):
        ALL[n](os.path.join(od, n)); print('tex', n)
