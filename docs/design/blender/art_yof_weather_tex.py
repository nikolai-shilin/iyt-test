# Textures for the renders of art_yof_weather.py (yachtmaster-offshore/weather): a depression's cloud from space
# (RGBA, for a plane over the ocean), two radiofax analysis charts (a secondary low; isobars with the geostrophic
# scale and the pencilled working), an aneroid barometer's dial.
# System Python with Pillow and numpy, helpers from art_yof_pilotage_tex.py.
#   python3 docs/design/blender/art_yof_weather_tex.py <outdir> [name ...]
import os, sys, math, json, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from art_yof_pilotage_tex import F, paper, save, hand, PENCIL, main

def fbm(n, octaves=6, seed=1):
    rng = np.random.default_rng(seed); out = np.zeros((n, n))
    for o in range(octaves):
        k = 2 ** (o + 2); g = rng.random((k + 1, k + 1))
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC)
        out += np.asarray(im, float) / 255 * 0.5 ** o
    return out / out.max()

def w3_sat(out):
    """A mature depression from above (north up): a cloud spiral wound anticlockwise into the centre, the cold front's
    band trailing south and south-west, the clear slot behind it. RGBA, 2048 px."""
    n = 2048; y, x = np.mgrid[0:n, 0:n] / n - 0.5; cx, cy = -0.05, -0.08
    dx, dy = x - cx, y - cy; r = np.hypot(dx, dy) + 1e-6; th = np.arctan2(-dy, dx)
    nz = fbm(n, 7, 3); nz2 = fbm(n, 5, 9)
    spiral = 0.5 + 0.5 * np.cos(2 * (th + 2.6 * np.log(r / 0.3)) + 3.0 * (nz2 - 0.5))      # arms winding in, anticlockwise (NH)
    core = np.clip(1 - r / 0.36, 0, 1)
    cloud = core ** 0.5 * (0.35 + 0.65 * spiral ** 1.5) * (0.6 + 0.6 * nz)
    # the frontal band: from the centre east, curving south and away south-west
    t = np.linspace(0, 1, 400); fx = cx + 0.08 + 0.25 * np.sin(t * 1.6) - 0.15 * t ** 2; fy = cy + 0.05 + 0.5 * t
    band = np.zeros_like(r)
    for px, py, tt in zip(fx[::4], fy[::4], t[::4]):
        band = np.maximum(band, np.exp(-((x - px) ** 2 + (y - py) ** 2) / (0.05 - 0.03 * tt) ** 2) * (0.55 + 0.6 * nz))
    warm = np.exp(-((y - cy + 0.02) ** 2) / 0.03 ** 2) * np.clip((x - cx) / 0.4, 0, 1) * np.clip(1 - (x - cx) / 0.45, 0, 1)
    cloud = np.maximum(cloud, band * 0.95); cloud = np.maximum(cloud, warm * 0.7)
    cells = np.clip((nz2 - 0.5) * 3, 0, 1) * np.clip((r - 0.22) / 0.15, 0, 1) * np.clip(1 - np.hypot(x + 0.2, y - 0.22) / 0.3, 0, 1)   # showers behind the front
    cloud = np.maximum(cloud, cells * 0.7)
    a = np.clip((cloud * (0.55 + 0.6 * nz) - 0.28) * 2.2, 0, 1)
    eye = np.exp(-(r / 0.018) ** 2); a = a * (1 - 0.6 * eye)
    v = 0.78 + 0.22 * nz
    img = np.dstack([v * 245, v * 247, v * 250, a * 255]).astype(np.uint8)
    Image.fromarray(img, 'RGBA').save(out + '.png')
    json.dump({'centre': [(cx + 0.5) * n, (cy + 0.5) * n], 'size': [n, n]}, open(out + '.json', 'w'))

FAX = (24, 24, 26)
def fax_base(w=2400, h=1700, title='SURFACE ANALYSIS 00 UTC'):
    im, d = paper(w, h, (244, 243, 238))
    for gx in range(100, w, 260): d.line([(gx, 0), (gx + 120, h)], fill=(196, 196, 196), width=2)
    for gy in range(140, h, 230): d.arc([-w * 0.5, gy - 300, w * 1.5, gy + 900], 200, 340, fill=(196, 196, 196), width=2)
    d.rectangle([30, 30, w - 30, h - 30], outline=FAX, width=4)
    d.text((70, 90), title, font=F('bold', 52), fill=FAX, anchor='lm')
    return im, d

def isobars(d, cx, cy, radii, values, sx=1.25, label_at=200, w=5, low=True):
    for r, v in zip(radii, values):
        d.ellipse([cx - r * sx, cy - r, cx + r * sx, cy + r], outline=FAX, width=w)
        a = math.radians(label_at); tx, ty = cx + r * sx * math.cos(a), cy - r * math.sin(a)
        d.rectangle([tx - 44, ty - 22, tx + 44, ty + 22], fill=(244, 243, 238)); d.text((tx, ty), str(v), font=F('bold', 34), fill=FAX, anchor='mm')

def front_line(d, pts, kind, w=7):
    d.line(pts, fill=FAX, width=w)
    for i in range(1, len(pts) - 1, 2):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]; a = math.atan2(y1 - y0, x1 - x0); nx, ny = -math.sin(a), math.cos(a); mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        if kind == 'cold': d.polygon([(x0, y0), (x1, y1), (mx + nx * 30, my + ny * 30)], fill=FAX)
        elif kind == 'warm': d.pieslice([mx - 22, my - 22, mx + 22, my + 22], math.degrees(a), math.degrees(a) + 180, fill=FAX)
        else:
            if i % 4 == 1: d.polygon([(x0, y0), (x1, y1), (mx + nx * 30, my + ny * 30)], fill=FAX)
            else: d.pieslice([mx - 22, my - 22, mx + 22, my + 22], math.degrees(a), math.degrees(a) + 180, fill=FAX)

def w4_fax(out):
    """The main low 968 north-west, a secondary 994 south-east of it at the triple point; the fronts."""
    im, d = fax_base()
    L1, L2 = (800, 560), (1280, 1160)
    isobars(d, *L1, [90, 190, 300, 420, 540, 660], [972, 980, 988, 996, 1004, 1012], label_at=150)
    isobars(d, *L2, [60, 130], [998, 1002], label_at=60, w=4)
    for (x, y), t, v in ((L1, 'L', '968'), (L2, 'L', '994')):
        d.text((x, y - 10), t, font=F('bold', 110), fill=FAX, anchor='mm'); d.text((x + 10, y + 80), v, font=F('bold', 46), fill=FAX, anchor='mm')
    occ = [(L1[0] + 40 * i, L1[1] + 50 * i) for i in range(0, 13)]
    front_line(d, occ, 'occl')
    tp = occ[-1]
    front_line(d, [(tp[0] + 60 * i, tp[1] + 5 * i - 0.8 * i * i) for i in range(0, 12)], 'warm')
    front_line(d, [(tp[0] - 40 * i - 2 * i * i, tp[1] + 55 * i) for i in range(0, 11)], 'cold')
    for (x, y), a in (((1040, 860), 300), ((1560, 1400), 230)):
        L = 90; t = math.radians(a); d.line([(x, y), (x + L * math.sin(t), y - L * math.cos(t))], fill=FAX, width=6)
        for k in range(3): bx, by = x + (L - 22 * k) * math.sin(t), y - (L - 22 * k) * math.cos(t); d.line([(bx, by), (bx + 34 * math.sin(t + 1.3), by - 34 * math.cos(t + 1.3))], fill=FAX, width=6)
    save(im, out, {'main': L1, 'secondary': L2, 'oppose': (1040, 860), 'strongest': (1560, 1400), 'size': (2400, 1700)}, blur=0.8)

def w6_fax(out):
    """Isobars round a low at 4 hPa, the geostrophic scale in the corner and the pencilled working."""
    im, d = fax_base(title='SURFACE ANALYSIS 12 UTC')
    Lc = (700, 520)
    isobars(d, *Lc, [100, 220, 340, 460, 580, 700], [984, 988, 992, 996, 1000, 1004], label_at=120, w=5)
    d.text(Lc, 'L', font=F('bold', 110), fill=FAX, anchor='mm')
    # the geostrophic scale: latitude rows, curves of wind speed against isobar spacing
    x0, y0, x1, y1 = 1560, 1080, 2300, 1600
    d.rectangle([x0, y0, x1, y1], outline=FAX, width=4); d.text((x0 + 20, y0 + 36), 'GEOSTROPHIC WIND · 4 hPa', font=F('bold', 30), fill=FAX, anchor='lm')
    for i, lat in enumerate((40, 50, 60)):
        yy = y0 + 120 + i * 150; d.text((x0 + 20, yy), f'{lat}°', font=F('bold', 34), fill=FAX, anchor='lm'); d.line([(x0 + 100, yy), (x1 - 20, yy)], fill=FAX, width=3)
        for kn, frac in ((80, 0.12), (60, 0.2), (40, 0.36), (30, 0.5), (20, 0.75), (15, 0.95)):
            xx = x0 + 100 + (x1 - x0 - 140) * frac * (1 + 0.12 * (1 - i));
            if xx < x1 - 20: d.line([(xx, yy - 18), (xx, yy + 18)], fill=FAX, width=3); d.text((xx, yy - 40), str(kn), font=F('reg', 26), fill=FAX, anchor='mm')
    a = math.radians(300); r0, r1 = 460, 580
    p0 = (Lc[0] + r0 * 1.25 * math.cos(a), Lc[1] - r0 * math.sin(a)); p1 = (Lc[0] + r1 * 1.25 * math.cos(a), Lc[1] - r1 * math.sin(a))
    d.line([p0, p1], fill=PENCIL, width=5)
    work = ['40 kn − 15 % = 34', '× 0.8 = 27 kn', 'backed 15°: 255°, F6']
    for i, t in enumerate(work): d.text((1560, 460 + i * 90), t, font=hand(64), fill=PENCIL, anchor='ls')
    save(im, out, {'p0': p0, 'p1': p1, 'scale': (x0 + 100 + (x1 - x0 - 140) * 0.36 * 1.0, y0 + 270), 'work': (1800, 640), 'size': (2400, 1700)}, blur=0.8)

def w7_dial(out):
    n = 1024; im = Image.new('RGB', (n, n), (238, 233, 220)); d = ImageDraw.Draw(im); c = n / 2
    for p in range(950, 1051):
        a = math.radians(-135 + (p - 950) * 2.7); r0 = 440; r1 = r0 - (46 if p % 10 == 0 else 30 if p % 5 == 0 else 18)
        d.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + r1 * math.sin(a), c - r1 * math.cos(a))], fill=(30, 30, 30), width=5 if p % 10 == 0 else 3)
        if p % 10 == 0: d.text((c + 350 * math.sin(a), c - 350 * math.cos(a)), str(p), font=F('bold', 40), fill=(30, 30, 30), anchor='mm')
    for p, t in ((960, 'STORMY'), (980, 'RAIN'), (1000, 'CHANGE'), (1020, 'FAIR'), (1040, 'DRY')):
        a = math.radians(-135 + (p - 950) * 2.7); d.text((c + 225 * math.sin(a), c - 225 * math.cos(a)), t, font=F('serif', 36), fill=(110, 30, 30), anchor='mm')
    d.text((c, c + 210), 'hPa', font=F('bold', 44), fill=(60, 60, 60), anchor='mm')
    d.ellipse([20, 20, n - 20, n - 20], outline=(150, 120, 60), width=10)
    im.save(out + '.png')

JOBS = {'w3-sat': w3_sat, 'w4-fax': w4_fax, 'w6-fax': w6_fax, 'w7-dial': w7_dial}
if __name__ == '__main__': main(JOBS)
