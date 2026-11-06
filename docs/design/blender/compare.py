# Comparison sheets: today's Three.js render next to the Blender + Cycles one, with a close-up underneath.
# System Python with Pillow.
#   python3 docs/design/blender/compare.py            all sheets
#   python3 docs/design/blender/compare.py winch      one
import os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figure-style')
BL = os.path.join(ROOT, 'blender')
FONT = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
BG, FG = (11, 15, 20), (230, 230, 230)
W, H, G, HDR = 1280, 800, 24, 56

# name: (Three.js render, Blender render (labelled if it has labels), close-up box in the 1280x800 frame, zoom)
SHEETS = {
    'ring': ('types/rope.jpg', 'blender/rope-ring-labelled.jpg', 'blender/rope-ring.jpg', (440, 480, 760, 700), 3),
    'winch': ('types/rope-winch.jpg', 'blender/rope-winch-labelled.jpg', 'blender/rope-winch.jpg', (560, 220, 880, 440), 3),
    'cleat': ('types/rope-cleat.jpg', 'blender/rope-cleat-labelled.jpg', 'blender/rope-cleat.jpg', (430, 200, 750, 420), 3),
    'rail': ('types/rope-rail.jpg', 'blender/rope-rail-labelled.jpg', 'blender/rope-rail.jpg', (480, 420, 800, 640), 3),
    'sheet': ('types/rope-sheet.jpg', 'blender/rope-sheet-labelled.jpg', 'blender/rope-sheet.jpg', (380, 380, 700, 600), 3),
}
KNOTS = ['bowline', 'clove', 'reef', 'sheetbend', 'figure8', 'rolling', 'roundturn', 'cleat']

def font(n): return ImageFont.truetype(FONT, n)

def scene_sheet(name, secs=None):
    three, bl_lab, bl_raw, box, z = SHEETS[name]
    a = Image.open(os.path.join(ROOT, three)).convert('RGB').resize((W, H), Image.LANCZOS)
    b = Image.open(os.path.join(ROOT, bl_lab if os.path.exists(os.path.join(ROOT, bl_lab)) else bl_raw)).convert('RGB')
    braw = Image.open(os.path.join(ROOT, bl_raw)).convert('RGB')
    cw, ch = (box[2] - box[0]) * z, (box[3] - box[1]) * z
    out = Image.new('RGB', (W * 2 + G * 3, HDR + H + G + HDR + ch + G), BG); d = ImageDraw.Draw(out)
    d.text((G, 14), 'Now: Three.js in the browser', font=font(30), fill=FG)
    d.text((W + 2 * G, 14), 'Blender + Cycles (path traced)' + (f', {secs} s on the M3 Max GPU' if secs else ''), font=font(30), fill=FG)
    out.paste(a, (G, HDR)); out.paste(b, (W + 2 * G, HDR)); y2 = HDR + H + G
    d.text((G, y2 + 14), f'Close-up, {z}x', font=font(30), fill=FG)
    out.paste(a.crop(box).resize((cw, ch), Image.LANCZOS), (G + (W - cw) // 2, y2 + HDR))
    out.paste(braw.crop(box).resize((cw, ch), Image.LANCZOS), (W + 2 * G + (W - cw) // 2, y2 + HDR))
    p = os.path.join(BL, f'compare-{name}.jpg'); out.save(p, quality=90); return p

def knots_sheet():
    """All eight knots: each row a pair, Three.js left, Blender right, at half size."""
    w, h = W // 2, H // 2
    out = Image.new('RGB', (G + (w * 2 + G) * 2 + G, HDR + len(KNOTS) // 2 * (h + HDR) + G), BG); d = ImageDraw.Draw(out)
    for i, k in enumerate(KNOTS):
        r, c = divmod(i, 2); x0 = G + c * (w * 2 + G * 2); y0 = HDR + r * (h + HDR)
        a = Image.open(os.path.join(ROOT, 'knots', f'knot-{k}.jpg')).convert('RGB').resize((w, h), Image.LANCZOS)
        lab = os.path.join(BL, 'knots', f'knot-{k}-labelled.jpg'); raw = os.path.join(BL, 'knots', f'knot-{k}.jpg')
        b = Image.open(lab if os.path.exists(lab) else raw).convert('RGB').resize((w, h), Image.LANCZOS)
        d.text((x0, y0 - 40), f'{k}: Three.js | Blender', font=font(26), fill=FG)
        out.paste(a, (x0, y0)); out.paste(b, (x0 + w + 4, y0))
    p = os.path.join(BL, 'compare-knots.jpg'); out.save(p, quality=90); return p

def knot_closeups():
    """Each knot at full size, Three.js above Blender, cropped to the knot itself."""
    paths = []
    for k in KNOTS:
        a = Image.open(os.path.join(ROOT, 'knots', f'knot-{k}.jpg')).convert('RGB').resize((W, H), Image.LANCZOS)
        lab = os.path.join(BL, 'knots', f'knot-{k}-labelled.jpg'); raw = os.path.join(BL, 'knots', f'knot-{k}.jpg')
        b = Image.open(lab if os.path.exists(lab) else raw).convert('RGB')
        out = Image.new('RGB', (W * 2 + G * 3, HDR + H + G), BG); d = ImageDraw.Draw(out)
        d.text((G, 14), f'knot-{k} · now: Three.js', font=font(30), fill=FG); d.text((W + 2 * G, 14), 'Blender + Cycles', font=font(30), fill=FG)
        out.paste(a, (G, HDR)); out.paste(b, (W + 2 * G, HDR))
        p = os.path.join(BL, 'knots', f'compare-knot-{k}.jpg'); out.save(p, quality=88); paths.append(p)
    return paths

if __name__ == '__main__' and sys.argv[1:] != ['types']:
    names = sys.argv[1:] or list(SHEETS) + ['knots']
    for n in names:
        if n == 'knots': print(knots_sheet()); print(*knot_closeups(), sep='\n')
        else: print(scene_sheet(n))

# ---------- figure types: today's Three.js render next to the Blender one ----------
TYPES = [('sail', 'fig-sail'), ('buoy', 'fig-buoy'), ('encounter', 'fig-mob'), ('dayshape', 'fig-dayshape'),
         ('lights', 'fig-lights'), ('anchor', 'fig-anchor'), ('bay', 'fig-bay')]
EXTRAS = ['fig-cardinal-north', 'fig-buoy-starboard', 'fig-night-yacht', 'fig-drone-tacks', 'fig-drone-overtake',
          'fig-drone-headon', 'fig-drone-channel', 'fig-drone-anchored']

def types_sheet():
    w, h = W // 2, H // 2
    out = Image.new('RGB', (G + (w * 2 + G) * 2, HDR + (len(TYPES) + 1) // 2 * (h + HDR) + G), BG); d = ImageDraw.Draw(out)
    for i, (t, f) in enumerate(TYPES):
        r, c = divmod(i, 2); x0 = G + c * (w * 2 + G * 2); y0 = HDR + r * (h + HDR)
        a = Image.open(os.path.join(ROOT, 'types', f'{t}.jpg')).convert('RGB').resize((w, h), Image.LANCZOS)
        p = os.path.join(BL, 'types', f'{f}-labelled.jpg')
        b = Image.open(p if os.path.exists(p) else os.path.join(BL, 'types', f'{f}.jpg')).convert('RGB').resize((w, h), Image.LANCZOS)
        d.text((x0, y0 - 40), f'{t}: Three.js | Blender', font=font(26), fill=FG)
        out.paste(a, (x0, y0)); out.paste(b, (x0 + w + 4, y0))
    p = os.path.join(BL, 'compare-types.jpg'); out.save(p, quality=88); return p

def extras_sheet():
    w, h = W // 2, H // 2; cols = 3
    out = Image.new('RGB', (G + cols * (w + G), HDR + (len(EXTRAS) + cols - 1) // cols * (h + HDR)), BG); d = ImageDraw.Draw(out)
    for i, f in enumerate(EXTRAS):
        r, c = divmod(i, cols); x0 = G + c * (w + G); y0 = HDR + r * (h + HDR)
        p = os.path.join(BL, 'types', f'{f}-labelled.jpg')
        b = Image.open(p if os.path.exists(p) else os.path.join(BL, 'types', f'{f}.jpg')).convert('RGB').resize((w, h), Image.LANCZOS)
        d.text((x0, y0 - 40), f.replace('fig-', ''), font=font(26), fill=FG); out.paste(b, (x0, y0))
    p = os.path.join(BL, 'blender-extras.jpg'); out.save(p, quality=88); return p

if __name__ == '__main__' and sys.argv[1:] == ['types']:
    print(types_sheet()); print(extras_sheet())
