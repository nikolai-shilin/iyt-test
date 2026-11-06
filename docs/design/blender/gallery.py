# Gallery sheets of the Blender renders (labelled versions where they exist), for review.
#   python3 docs/design/blender/gallery.py ropes|knots|types
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont
BL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figure-style', 'blender')
FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 24)
SETS = {
    'ropes': ['rope-ring', 'rope-winch', 'rope-cleat', 'rope-rail', 'rope-sheet', 'rope-types'],
    'knots': ['knots/knot-' + k for k in ('bowline', 'clove', 'reef', 'sheetbend', 'figure8', 'rolling', 'roundturn', 'cleat')],
    'types': ['types/fig-' + k for k in ('sail', 'buoy', 'buoy-starboard', 'cardinal-north', 'mob', 'dayshape', 'lights', 'night-yacht',
              'anchor', 'bay', 'drone-tacks', 'drone-overtake', 'drone-headon', 'drone-channel', 'drone-anchored')],
    'instruments': ['types/fig-' + k for k in ('radio', 'panel', 'compass')],
}
def sheet(name, cols=3, w=852, h=533, g=14, hdr=40):
    items = SETS[name]; rows = (len(items) + cols - 1) // cols
    out = Image.new('RGB', (g + cols * (w + g), rows * (h + hdr) + g), (11, 15, 20)); d = ImageDraw.Draw(out)
    for i, base in enumerate(items):
        p = os.path.join(BL, base + '-labelled.jpg'); p = p if os.path.exists(p) else os.path.join(BL, base + '.jpg')
        x, y = g + (i % cols) * (w + g), (i // cols) * (h + hdr) + hdr
        d.text((x, y - 32), os.path.basename(base), font=FONT, fill=(230, 230, 230))
        try: out.paste(Image.open(p).convert('RGB').resize((w, h), Image.LANCZOS), (x, y))
        except FileNotFoundError: d.text((x + 20, y + 20), 'missing', font=FONT, fill=(220, 90, 90))
    p = os.path.join(BL, f'gallery-{name}.jpg'); out.save(p, quality=86); return p
if __name__ == '__main__':
    for n in sys.argv[1:] or SETS: print(sheet(n))
