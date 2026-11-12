# The signal flags the racing-rules renders fly (International Code of Signals, as the race signals use them), drawn
# with Pillow as 600 x 400 PNGs (the swallowtail A with a transparent notch) into
# docs/design/figure-style/articles/racing-rules/course/tex/flag-<code>.png. Colours as figures.js draws them.
#   python3 docs/design/blender/art_rr_a_flags.py
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, '..', 'figure-style', 'articles', 'racing-rules', 'course', 'tex')
BLUE, YEL, RED, WHITE, ORANGE = (11, 78, 162), (255, 212, 0), (214, 40, 40), (250, 250, 248), (255, 122, 0)
W, H = 600, 400

def flag(code):
    im = Image.new('RGBA', (W, H), WHITE + (255,)); d = ImageDraw.Draw(im); u = W / 60   # figures.js draws in 60 x 40
    R = lambda x0, y0, x1, y1, c: d.rectangle([x0 * u, y0 * u, x1 * u - 1, y1 * u - 1], fill=c)
    if code == 'S': R(20, 13, 40, 27, BLUE)
    elif code == 'N':
        for r in range(4):
            for c in range(4):
                if (r + c) % 2 == 0: R(c * 15, r * 10, c * 15 + 15, r * 10 + 10, BLUE)
    elif code == 'H': R(30, 0, 60, 40, RED)
    elif code == 'A':
        d.polygon([(30 * u, 0), (60 * u, 0), (46 * u, 20 * u), (60 * u, 40 * u), (30 * u, 40 * u)], fill=BLUE)
        d.polygon([(60 * u, 0), (46 * u, 20 * u), (60 * u, 40 * u), (61 * u, 40 * u), (61 * u, 0)], fill=(0, 0, 0, 0))
    elif code == 'C':
        for i, c in enumerate((BLUE, WHITE, RED, WHITE, BLUE)): R(0, i * 8, 60, i * 8 + 8, c)
    elif code == 'M':
        R(0, 0, 60, 40, BLUE); d.line([(0, 0), (W, H)], fill=WHITE, width=int(8 * u)); d.line([(W, 0), (0, H)], fill=WHITE, width=int(8 * u))
    elif code == 'X': R(25, 0, 35, 40, BLUE); R(0, 15, 60, 25, BLUE)
    elif code == 'blue': R(0, 0, 60, 40, BLUE)
    elif code == 'orange': R(0, 0, 60, 40, ORANGE)
    return im

if __name__ == '__main__':
    os.makedirs(TEX, exist_ok=True)
    for c in ('S', 'N', 'H', 'A', 'C', 'M', 'X', 'blue', 'orange'):
        p = os.path.join(TEX, f'flag-{c}.png'); flag(c).save(p); print(p)
