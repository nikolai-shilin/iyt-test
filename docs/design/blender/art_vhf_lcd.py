# Draws the SIMRAD RS20S display for art_vhf.py (system Python with Pillow; Blender's Python has no PIL).
# The photographed front panel has "16 / HI / DISTRESS" baked in; this redraws the LCD so any channel and
# power can be shown, plus optional text lines for DSC screens.
#   python3 art_vhf_lcd.py OUT.png '{"channel": "72", "power": "LO", "name": "INTERSHIP", "lines": [], "tags": ["DSC", "INT"]}'
# The image covers the light LCD area of the front photo: px 362..625 x 142..352 (263 x 210 px), drawn at 4x.
import json, sys
from PIL import Image, ImageDraw, ImageFont

SUP = '/System/Library/Fonts/Supplemental/'
BIG = SUP + 'DIN Condensed Bold.ttf'; BOLD = SUP + 'Arial Narrow Bold.ttf'
W, H = 263 * 4, 210 * 4
BG, INK = (200, 208, 196), (18, 20, 18)
NAMES = {'16': 'DISTRESS', '70': 'DSC', '13': 'BRIDGE', '72': 'INTERSHIP', '77': 'INTERSHIP', '67': 'SMALL CRAFT',
         '9': 'CALLING', '06': 'SAR', '6': 'SAR', '12': 'PORT OPS', '14': 'PORT OPS', '11': 'PORT OPS'}

def f(path, n): return ImageFont.truetype(path, n)

def tag(d, x, y, text, filled):
    fo = f(BOLD, 64); w = d.textlength(text, font=fo) + 28
    if filled:
        d.rounded_rectangle([x, y, x + w, y + 78], 10, fill=INK); d.text((x + w / 2, y + 40), text, font=fo, fill=BG, anchor='mm')
    else:
        d.rounded_rectangle([x, y, x + w, y + 78], 10, outline=INK, width=6); d.text((x + w / 2, y + 40), text, font=fo, fill=INK, anchor='mm')
    return w

def draw(out, spec):
    ch = str(spec.get('channel', '16')); pw = spec.get('power', 'HI'); lines = spec.get('lines') or []
    name = spec.get('name', NAMES.get(ch, ''))
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    # a faint ghost of the unlit segments, as on a real LCD
    tag(d, 400, 40, pw, True)
    x = W - 60
    for t in reversed(spec.get('tags', ['DSC', 'INT'])):
        x -= f(BOLD, 64).getlength(t) + 28; tag(d, x, 40, t, False); x -= 18
    # volume bar left, squelch hatch right, as in the photo
    d.polygon([(70, 160), (130, 160), (100, 190)], fill=INK)
    d.rectangle([84, 230, 116, 760], fill=INK); d.text((100, 800), 'VOL', font=f(BOLD, 48), fill=INK, anchor='mm')
    for yy in range(560, 760, 16):
        for xx in range(W - 120, W - 70, 16): d.rectangle([xx + (yy // 16 % 2) * 8, yy, xx + 6 + (yy // 16 % 2) * 8, yy + 6], fill=INK)
    d.text((W - 95, 800), 'SQL', font=f(BOLD, 48), fill=INK, anchor='mm')
    d.line([(W - 70, 160), (W - 70, 520)], fill=INK, width=6)
    if lines:
        # a DSC screen: the channel small at the top left, then the text lines
        d.text((180, 100), f'CH {ch}', font=f(BIG, 110), fill=INK, anchor='lm')
        y = 230; n = len(lines); size = 118 if n <= 3 else 92
        for ln in lines:
            d.text((W / 2, y), ln, font=f(BIG, size), fill=INK, anchor='mt'); y += size + 26
    else:
        d.text((W / 2, 410), ch, font=f(BIG, 470), fill=INK, anchor='mm')
        if name: d.text((W / 2, 660), name, font=f(BOLD, 96), fill=INK, anchor='mm')
    im.save(out)

if __name__ == '__main__':
    draw(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})
