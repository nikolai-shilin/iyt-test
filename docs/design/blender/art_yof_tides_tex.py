# Textures for the renders of art_yof_tides.py (yachtmaster-offshore/tides): a tide staff to 7 m, an almanac page of
# secondary-port differences with the pencilled working, the plotter's tide page for a Solent port (double high
# water), a tidal stream atlas page, an ocean plotting sheet with the DR and the EP.
# System Python with Pillow, helpers from art_yof_pilotage_tex.py; run by the Blender script when a texture is missing.
#   python3 docs/design/blender/art_yof_tides_tex.py <outdir> [name ...]
import os, sys, math, json, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from art_yof_pilotage_tex import F, front, chart_base, topbar, databox, SW, SH, paper, save, hand, PENCIL, INKB, main

def t1_staff(out):
    """A tide gauge board, 1 px = 2 mm: 0 to 7.2 m above chart datum, E-pattern decimetres, metre numbers."""
    W, Hh = 150, 3700
    im = Image.new('RGB', (W, Hh), (245, 245, 238)); d = ImageDraw.Draw(im)
    Y = lambda m: Hh - (m + 0.2) * 500
    for cm in range(-20, 721, 2):
        y = Y(cm / 100)
        if cm % 10 == 0:
            col = (190, 30, 30) if (cm // 100) % 2 else (20, 20, 20)
            if cm % 20 == 0: d.rectangle([12, y - 25, 70, y], fill=col)
            d.line([(12, y), (W - 12, y)], fill=col, width=3)
        elif cm % 2 == 0 and cm % 10 in (2, 4, 6, 8): d.line([(12, y), (34, y)], fill=(40, 40, 40), width=1)
    for m in range(0, 8):
        y = Y(m); d.rectangle([80, y - 70, W - 10, y - 6], fill=(245, 245, 238))
        d.text((W - 40, y - 38), str(m), font=F('bold', 66), fill=(190, 30, 30), anchor='mm')
    d.line([(10, 0), (10, Hh)], fill=(30, 30, 30), width=6)
    im.save(out + '.png')

def t2_almanac(out):
    w, h = 1240, 1754; im, d = paper(w, h, (250, 249, 244))
    d.text((90, 130), 'Secondary port', font=F('bold', 70), fill=(24, 30, 44), anchor='lm')
    d.text((90, 210), 'Time and height differences on the standard port', font=F('reg', 38), fill=(80, 88, 100), anchor='lm')
    head = ['', 'HW', '', 'LW', '', 'MHWS', 'MHWN', 'MLWN', 'MLWS']; xs = [90, 300, 420, 540, 660, 780, 900, 1020, 1140]
    y = 300; d.rectangle([90, y, w - 60, y + 70], fill=(226, 230, 236))
    for t, x in zip(head, xs): d.text((x + 40 if t else x, y + 35), t, font=F('bold', 34), fill=(40, 46, 60), anchor='mm' if t else 'lm')
    rows = [('Standard', ['0600', '1200', '0100', '1300', '5.8', '4.6', '2.0', '0.7']), ('', ['1800', '2400', '1300', '1900', '', '', '', '']),
            ('Secondary', ['−0030', '−0010', '−0040', '−0015', '−0.6', '−0.2', '−0.1', '0.0'])]
    y += 70
    for k, (lab, vals) in enumerate(rows):
        d.text((100, y + 45), lab, font=F('bold', 34), fill=(30, 34, 40), anchor='lm')
        for v, x in zip(vals, xs[1:]): d.text((x + 40, y + 45), v, font=F('reg', 36), fill=(30, 34, 40), anchor='mm')
        y += 90; d.line([(90, y), (w - 60, y)], fill=(200, 204, 210), width=2)
    # pencilled working below
    work = ['Std HW 0900 · 5.2 m', '0900 halfway 0600-1200:', '   −0030 to −0010: −0020', '   HW 0840', '5.2 halfway 5.8-4.6:', '   −0.6 to −0.2: −0.4', '   HW 4.8 m']
    ys = []
    for i, t in enumerate(work):
        yy = 880 + i * 100; ys.append(yy); d.text((140, yy), t, font=hand(58), fill=PENCIL, anchor='ls')
    for i in (3, 6): d.ellipse([120, ys[i] - 78, 560, ys[i] + 26], outline=(70, 70, 76), width=4)
    save(im, out, {'timediff': (xs[1] + 100, 300 + 70 + 180 + 45), 'hw': (300, ys[3] - 30), 'height': (330, ys[6] - 30), 'size': (w, h)})

def solent_f(hh):
    """Factor against hours from LW for a port with a double high water: a 6 h rise, a 2 h stand, a 5 h fall."""
    if hh < 0: return (1 + math.cos(math.pi * (hh + 5) / 5)) / 2 if hh > -5 else 1.0
    if hh <= 6: return (1 - math.cos(math.pi * hh / 6)) / 2
    if hh <= 8: return 1 - 0.05 * math.sin(math.pi * (hh - 6) / 2)
    return (1 + math.cos(math.pi * min(hh - 8, 5) / 5)) / 2

def t3_tide(out):
    """The plotter's tide page: LW 1000 0.6 m, the long double high water, the cursor at 1400, 3.3 m."""
    im = Image.new('RGB', (SW, SH), (14, 18, 24)); d = ImageDraw.Draw(im)
    x0, x1, y0, y1 = 150, SW - 70, SH - 170, 200
    t0, t1 = 6.0, 23.0; X = lambda t: x0 + (x1 - x0) * (t - t0) / (t1 - t0); Y = lambda m: y0 - (y0 - y1) * m / 4.8
    for m in range(0, 5): d.line([(x0, Y(m)), (x1, Y(m))], fill=(40, 50, 62), width=2); d.text((x0 - 20, Y(m)), f'{m}', font=F('bold', 36), fill=(150, 170, 186), anchor='rm')
    for t in range(6, 24, 2): d.line([(X(t), y0), (X(t), y1)], fill=(40, 50, 62), width=2); d.text((X(t), y0 + 40), f'{t:02d}00', font=F('bold', 32), fill=(150, 170, 186), anchor='mm')
    pts = [(X(t0 + i * 0.05), Y(0.6 + 3.6 * solent_f(t0 + i * 0.05 - 10))) for i in range(int((t1 - t0) / 0.05) + 1)]
    d.polygon(pts + [(x1, y0), (x0, y0)], fill=(20, 60, 92)); d.line(pts, fill=(90, 190, 255), width=7)
    cx, cy = X(14), Y(3.3)
    d.line([(cx, y0), (cx, y1)], fill=(255, 214, 60), width=4); d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(255, 214, 60))
    d.rounded_rectangle([cx + 30, cy - 120, cx + 330, cy - 30], 12, fill=(255, 214, 60)); d.text((cx + 180, cy - 75), '14:00  3.3 m', font=F('bold', 44), fill=(20, 20, 20), anchor='mm')
    lx, ly = X(10), Y(0.6); d.ellipse([lx - 12, ly - 12, lx + 12, ly + 12], fill=(230, 236, 240))
    topbar(d, [('TIDES', (230, 236, 240), None), ('Southampton', (255, 214, 60), None), ('Springs · range 3.6 m', (160, 176, 190), None)])
    front(im, out, {'cursor': (cx, Y(2.5)), 'lw': (lx, ly), 'stand': (X(17), Y(4.2) - 20), 'fall': (X(19.5), Y(2.4))})

def t7_atlas(out):
    """A tidal stream atlas page, HW −3: a coast, arrows with neap,spring rates; the one you use marked in pencil."""
    w, h = 1754, 1240; im, d = paper(w, h, (250, 250, 246))
    d.polygon([(0, 0), (w, 0), (w, 260), (1400, 330), (1150, 300), (900, 420), (700, 380), (420, 450), (0, 380)], fill=(236, 230, 206), outline=(110, 100, 70))
    d.text((70, 90), 'HW −3', font=F('bold', 80), fill=(24, 30, 44), anchor='lm'); d.text((360, 96), 'hours before HW at the reference port', font=F('reg', 38), fill=(60, 66, 76), anchor='lm')
    rnd = random.Random(5); anc = None
    for gx in range(160, w - 100, 240):
        for gy in range(560, h - 80, 210):
            a = math.radians(80 + rnd.uniform(-12, 12)); L = 80 + rnd.uniform(0, 70)
            x2, y2 = gx + L * math.sin(a), gy - L * math.cos(a)
            d.line([(gx, gy), (x2, y2)], fill=(30, 30, 40), width=7); d.polygon([(x2, y2), (x2 - 26 * math.sin(a - 0.4), y2 + 26 * math.cos(a - 0.4)), (x2 - 26 * math.sin(a + 0.4), y2 + 26 * math.cos(a + 0.4))], fill=(30, 30, 40))
            n, s = rnd.randint(6, 16), 0
            s = n * 2 - rnd.randint(0, 2)
            txt = f'{n:02d},{s:02d}'
            if gx == 880 and gy == 770: txt = '18,34'; anc = (gx + 40, gy - 50); d.ellipse([gx - 60, gy - 120, gx + 260, gy + 50], outline=PENCIL, width=5)
            d.text((gx + 40, gy + 30), txt, font=F('bold', 36), fill=(30, 30, 40), anchor='lm')
    d.text((1180, 1120), 'today 4.2 m: 2.6 kn', font=hand(60), fill=PENCIL, anchor='mm')
    save(im, out, {'arrow': anc, 'today': (1180, 1080), 'size': (w, h)})

def t11_sheet(out):
    """An ocean plotting sheet: parallels and meridians, the current arrows, the 30 h DR and the EP 12 M NE of it."""
    w, h = 2400, 1600; im, d = paper(w, h, (240, 244, 242))
    for x in range(100, w, 300): d.line([(x, 0), (x, h)], fill=(170, 180, 190), width=3)
    for y in range(100, h, 300): d.line([(0, y), (w, y)], fill=(170, 180, 190), width=3)
    d.polygon([(w, 0), (w, h), (2080, h), (2010, 1200), (2120, 900), (2000, 600), (2060, 300), (1980, 0)], fill=(243, 229, 178), outline=(110, 90, 50))
    for x in range(250, 1900, 330):
        for y in range(250, 1450, 300):
            d.line([(x, y), (x + 70, y - 70)], fill=(40, 140, 90), width=6); d.polygon([(x + 70, y - 70), (x + 40, y - 66), (x + 66, y - 40)], fill=(40, 140, 90))
            d.text((x + 10, y + 26), '0.4', font=F('bold', 30), fill=(40, 140, 90), anchor='lm')
    a, b = (400, 1250), (1300, 650)
    d.line([a, b], fill=PENCIL, width=6)
    for p in (a, b): d.ellipse([p[0] - 24, p[1] - 24, p[0] + 24, p[1] + 24], outline=PENCIL, width=5)
    e = (b[0] + 300, b[1] - 300); d.line([b, e], fill=PENCIL, width=5)
    for k in range(3): d.line([(b[0] + 100 * k + 40, b[1] - 100 * k - 60), (b[0] + 100 * k + 60, b[1] - 100 * k - 40)], fill=PENCIL, width=5)
    d.polygon([(e[0] - 26, e[1]), (e[0], e[1] - 26), (e[0] + 26, e[1]), (e[0], e[1] + 26)], outline=PENCIL, width=5)
    d.text((b[0] - 60, b[1] + 60), 'DR 30 h', font=hand(56), fill=PENCIL, anchor='rm'); d.text((e[0] + 50, e[1]), 'EP', font=hand(60), fill=PENCIL, anchor='lm')
    d.text(((b[0] + e[0]) / 2 + 60, (b[1] + e[1]) / 2 + 40), '12 M', font=hand(52), fill=PENCIL, anchor='lm')
    save(im, out, {'dr': b, 'ep': e, 'cur': (580, 880), 'size': (w, h)})

JOBS = {'t1-staff': t1_staff, 't2-almanac': t2_almanac, 't3-tide': t3_tide, 't7-atlas': t7_atlas, 't11-sheet': t11_sheet}
if __name__ == '__main__': main(JOBS)
