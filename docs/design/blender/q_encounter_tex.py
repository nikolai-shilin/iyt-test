# Screen pictures for q_encounter.py, drawn with the system Python (Pillow) on the Axiom's own front texture
# (textures/axiom-front.png, the screen glass at 70,72 - 645,432 of 828 x 481):
#   radar  heading-up radar, one target at a relative bearing and a fraction of the range
#   sart   a heading-up chart page with an AIS-SART target and its alarm box
# Prints JSON {png, px: [x, y]}: where the target sits on the 828 x 481 texture.
#   python3 q_encounter_tex.py radar <bearing> <frac> <out.png>
#   python3 q_encounter_tex.py sart <bearing> <frac> <out.png> [range text]
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FRONT = os.path.join(HERE, 'textures', 'axiom-front.png')
X0, Y0, X1, Y1 = 70, 72, 645, 432
F = lambda n: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', n)

def radar(brg, frac, out):
    W, H = 920, 610
    im = Image.new('RGB', (W, H), (4, 10, 22)); d = ImageDraw.Draw(im)
    cx, cy, R = W // 2, H // 2 + 20, 270
    for k in range(1, 4):
        r = R * k / 3; d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(40, 120, 150), width=2)
    for a in range(0, 360, 30):
        t = math.radians(a); d.line([(cx, cy), (cx + R * math.sin(t), cy - R * math.cos(t))], fill=(18, 55, 75), width=1)
    d.line([(cx, cy), (cx, cy - R)], fill=(220, 230, 240), width=3)
    glow = Image.new('RGB', (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow); rnd = random.Random(4)
    for _ in range(260):
        r = rnd.random() ** 1.6 * 60; t = rnd.random() * math.tau
        g.ellipse([cx + r * math.sin(t) - 2, cy - r * math.cos(t) - 2, cx + r * math.sin(t) + 2, cy - r * math.cos(t) + 2], fill=(200, 160, 30))
    tb, tr = math.radians(brg), R * frac
    tx, ty = cx + tr * math.sin(tb), cy - tr * math.cos(tb)
    g.ellipse([tx - 13, ty - 9, tx + 13, ty + 9], fill=(255, 215, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(1.5)); im = Image.composite(glow, im, glow.convert('L').point(lambda v: 255 if v > 8 else 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 58], fill=(10, 18, 30))
    d.text((24, 14), 'RADAR', font=F(30), fill=(230, 236, 240)); d.text((180, 18), 'H-UP  0.75 nm', font=F(24), fill=(150, 175, 190))
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(230, 236, 240))
    return im, (tx, ty), (W, H)

def sart(brg, frac, out, rng='3.0 nm'):
    W, H = 920, 610
    im = Image.new('RGB', (W, H), (78, 128, 172)); d = ImageDraw.Draw(im)
    # a coast in the top left, a few depth contours
    d.polygon([(0, 58), (300, 58), (250, 120), (140, 150), (60, 210), (0, 230)], fill=(196, 178, 124), outline=(90, 80, 60))
    for k, c in enumerate([(120, 175, 215), (100, 160, 205)]):
        d.line([(0, 260 + 40 * k), (180, 210 + 40 * k), (330, 150 + 50 * k), (420, 58)], fill=c, width=3)
    cx, cy, R = W // 2, H - 110, 400
    for k in (1, 2):
        r = R * k / 2; d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(70, 110, 150), width=2)
    d.text((cx + 8, cy - R / 2 - 26), '1.5', font=F(18), fill=(40, 70, 100)); d.text((cx + 8, cy - R - 26), '3', font=F(18), fill=(40, 70, 100))
    d.line([(cx, cy), (cx, 70)], fill=(30, 30, 30), width=2)                       # heading line
    d.polygon([(cx, cy - 22), (cx - 12, cy + 14), (cx + 12, cy + 14)], fill=(20, 20, 20))   # own boat
    tb, tr = math.radians(brg), R * frac
    tx, ty = cx + tr * math.sin(tb), cy - tr * math.cos(tb)
    d.ellipse([tx - 16, ty - 16, tx + 16, ty + 16], outline=(220, 20, 20), width=5)
    d.line([(tx - 11, ty - 11), (tx + 11, ty + 11)], fill=(220, 20, 20), width=5); d.line([(tx - 11, ty + 11), (tx + 11, ty - 11)], fill=(220, 20, 20), width=5)
    # the alarm box
    bx, by = 520, 120
    d.rectangle([bx, by, bx + 360, by + 110], fill=(250, 250, 250), outline=(220, 20, 20), width=5)
    d.text((bx + 20, by + 16), 'SART ACTIVE', font=F(34), fill=(220, 20, 20))
    d.text((bx + 20, by + 64), f'RNG {rng}', font=F(26), fill=(30, 30, 30))
    d.rectangle([0, 0, W, 58], fill=(10, 18, 30))
    d.text((24, 14), 'CHART', font=F(30), fill=(230, 236, 240)); d.text((180, 18), 'H-UP  3 nm', font=F(24), fill=(150, 175, 190))
    return im, (tx, ty), (W, H)

if __name__ == '__main__':
    kind, brg, frac, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    im, (tx, ty), (W, H) = (radar if kind == 'radar' else sart)(brg, frac, out, *sys.argv[5:])
    front = Image.open(FRONT).convert('RGB')
    front.paste(im.resize((X1 - X0, Y1 - Y0), Image.LANCZOS), (X0, Y0)); front.save(out)
    px = (X0 + tx * (X1 - X0) / W, Y0 + ty * (Y1 - Y0) / H)
    print(json.dumps({'png': out, 'px': px}))
