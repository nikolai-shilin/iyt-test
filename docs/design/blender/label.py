# Draws the figure labels on the Blender renders, in the same style as figure-rope-3d.html: white pills with a
# pointer at each anchor, and the dark note pill top left. Reads <render>.labels.json written by common.render().
# Writes <render>-labelled.jpg. System Python with Pillow (Blender's own Python has no PIL).
#   python3 docs/design/blender/label.py docs/design/figure-style/blender/rope-winch.jpg [...]
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

FONT = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
W = 1280

COLORS = {'red': (214, 40, 40), 'blue': (19, 132, 214), 'green': (30, 150, 70), 'yellow': (255, 214, 0)}

def arrow(img, x0, y0, x1, y1, color='red'):
    """A fat arrow from (x0, y0) to (x1, y1), outlined, like the wind arrows on the Three.js figures."""
    import math
    d = ImageDraw.Draw(img, 'RGBA'); c = COLORS.get(color, (214, 40, 40)); L = math.hypot(x1 - x0, y1 - y0)
    if L < 1: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L; nx, ny = -uy, ux; w, hw, hl = 11, 26, 40
    bx, by = x1 - ux * hl, y1 - uy * hl
    poly = [(x0 + nx * w, y0 + ny * w), (bx + nx * w, by + ny * w), (bx + nx * hw, by + ny * hw), (x1, y1),
            (bx - nx * hw, by - ny * hw), (bx - nx * w, by - ny * w), (x0 - nx * w, y0 - ny * w)]
    d.polygon(poly, fill=c + (240,), outline=(0, 0, 0, 160), width=2)

def leader(img, x0, y0, x1, y1):
    """A thin white line with a dark edge from a label's anchor (a dot) to its pill, when the pill sits off to one side."""
    d = ImageDraw.Draw(img, 'RGBA')
    d.line([(x0, y0), (x1, y1)], fill=(0, 0, 0, 110), width=6); d.line([(x0, y0), (x1, y1)], fill=(255, 255, 255, 240), width=3)
    d.ellipse([x0 - 7, y0 - 7, x0 + 7, y0 + 7], fill=(255, 255, 255, 245), outline=(0, 0, 0, 140), width=2)

def bloom(img, strength=1.0):
    """Glow round bright lights (night scenes): blur the brightest pixels and add them back."""
    from PIL import ImageFilter, ImageChops
    rgb = img.convert('RGB'); lum = rgb.convert('L').point(lambda v: 255 if v > 200 else int(max(0, v - 120) * 2))
    bright = Image.composite(rgb, Image.new('RGB', rgb.size), lum)
    glow = ImageChops.add(bright.filter(ImageFilter.GaussianBlur(6)), bright.filter(ImageFilter.GaussianBlur(22)))
    glow = glow.point(lambda v: min(255, int(v * strength)))
    return ImageChops.add(rgb, glow).convert('RGBA')

def pill(img, x, y, text, s=1.0, color=None):
    d = ImageDraw.Draw(img, 'RGBA'); f = ImageFont.truetype(FONT, int(30 * s))
    w = d.textlength(text, font=f) + 34 * s; h = 52 * s
    cx = max(w / 2 + 12, min(W - w / 2 - 12, x)); px, py = cx - w / 2, y - h - 18 * s
    shadow = Image.new('RGBA', img.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([px, py + 3, px + w, py + h + 3], 26 * s, fill=(0, 0, 0, 60))
    img.alpha_composite(shadow) if img.mode == 'RGBA' else None
    bg = COLORS[color] + (245,) if color else (255, 255, 255, 242); fg = (255, 255, 255) if color else (0, 0, 0)
    d.rounded_rectangle([px, py, px + w, py + h], 26 * s, fill=bg)
    d.polygon([(x - 9 * s, py + h - 1), (x, py + h + 11 * s), (x + 9 * s, py + h - 1)], fill=bg)
    d.text((cx, py + h / 2 + 1), text, font=f, fill=fg, anchor='mm')

def note(img, text, y=27, size=27):
    d = ImageDraw.Draw(img, 'RGBA'); f = ImageFont.truetype(FONT, size)
    w = d.textlength(text, font=f) + 36; h = 50 if size >= 27 else 44; x = 28
    d.rounded_rectangle([x, y, x + w, y + h], 25, fill=(10, 14, 20, 210))
    d.text((x + w / 2, y + h / 2 + 1), text, font=f, fill=(255, 255, 255), anchor='mm')

def label(path, ru=False):
    base = os.path.splitext(path)[0]
    with open(base + '.labels.json') as f: lab = json.load(f)
    if ru:   # the Russian copy: every text through ru.json beside the render (written for the article's figures)
        with open(os.path.join(os.path.dirname(path) or '.', 'ru.json')) as f: RU = json.load(f)
        if lab.get('note'): lab['note'] = RU.get(lab['note'], lab['note'])
        for L in lab['labels']: L['text'] = RU.get(L['text'], L['text'])
        lab['lines'] = [RU.get(t, t) for t in lab.get('lines', [])]
    img = Image.open(path).convert('RGBA')
    if lab.get('bloom'): img = bloom(img, lab['bloom'])
    for A in lab.get('arrows', []): arrow(img, *A['from'], *A['to'], A.get('color', 'red'))
    for L in lab['labels']:
        x, y = L['x'], L['y']
        if 'dx' in L:   # off to one side: a leader from the anchor to the pill's pointer
            leader(img, x, y, x + L['dx'], y + L['dy'] - 7); x, y = x + L['dx'], y + L['dy']
        pill(img, x, y - 4, L['text'], color=L.get('color'))
    if lab.get('note'): note(img, lab['note'])
    for k, t in enumerate(lab.get('lines', [])): note(img, t, 27 + 58 + k * 52, 24)   # more lines of the figure's data, under the note
    out = base + ('-labelled.ru.jpg' if ru else '-labelled.jpg'); img.convert('RGB').save(out, quality=92); return out

if __name__ == '__main__':
    #   python3 docs/design/blender/label.py --ru <render>.jpg   writes <render>-labelled.ru.jpg
    ru = '--ru' in sys.argv
    for p in sys.argv[1:]:
        if p != '--ru': print(label(p, ru))
