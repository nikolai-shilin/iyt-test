# Before / after sheets for one article: today's figure, the Blender 3D render and the schematic, a row per figure,
# five rows to a sheet. Reads docs/design/article-figs/<level>-<article>.json and the images saved by
# capture_article.mjs and the art_*.py scripts in docs/design/figure-style/articles/<level>/<article>/.
# Keeps the old Three.js render of each figure as <n>-threejs.jpg the first time it runs.
#   python3 docs/design/blender/article_sheet.py bareboat-skipper/anchoring
import json, os, shutil, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); DESIGN = os.path.join(HERE, '..')
BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'; REG = '/System/Library/Fonts/Supplemental/Arial.ttf'
BG, INK, MUTED, ACC = (255, 255, 255), (20, 24, 28), (110, 118, 126), (0, 118, 190)

def fit(im, w, h):
    im = im.convert('RGB'); k = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)

def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) > width and cur: lines.append(cur); cur = w
        else: cur = t
    return lines + ([cur] if cur else [])

def sheets(article, per=7):
    level, name = article.split('/')
    data = json.load(open(os.path.join(DESIGN, 'article-figs', f'{level}-{name}.json')))
    folder = os.path.join(DESIGN, 'figure-style', 'articles', level, name)
    figs = data['figs']; out = []
    for start in range(0, len(figs), per):
        part = figs[start:start + per]
        CW, CH, G, HDR = [700, 820, 820], 512, 28, 150; W = G + sum(CW) + G * 3
        rowh = CH + 150
        img = Image.new('RGB', (W, HDR + rowh * len(part) + G), BG); d = ImageDraw.Draw(img)
        d.text((G, 30), f"{level} · {name} · before and after", font=ImageFont.truetype(REG, 56), fill=INK)
        d.text((G, 100), data.get('lead', '')[:150], font=ImageFont.truetype(REG, 26), fill=MUTED)
        for i, f in enumerate(part):
            n = f['n']; y0 = HDR + i * rowh; x = G
            heads = [(f"{n}. {f['fig']['type'].upper()}", 'today'), ('3D', 'Blender render'), ('SCHEMATIC', 'plan view')]
            if f.get('name'): heads[0] = (heads[0][0], f['name'])
            srcs = [f'{n}-before.png', f'{n}-3d-labelled.jpg' if os.path.exists(os.path.join(folder, f'{n}-3d-labelled.jpg')) else f'{n}-3d.jpg', f'{n}-schematic.png']
            for (h, sub), src, cw in zip(heads, srcs, CW):
                d.text((x, y0 + 8), h, font=ImageFont.truetype(BOLD, 26), fill=ACC)
                d.text((x + d.textlength(h, font=ImageFont.truetype(BOLD, 26)) + 14, y0 + 8), sub, font=ImageFont.truetype(BOLD, 26), fill=MUTED)
                p = os.path.join(folder, src)
                if os.path.exists(p):
                    im = fit(Image.open(p), cw, CH); img.paste(im, (x, y0 + 48))
                else:
                    d.rounded_rectangle([x, y0 + 48, x + cw, y0 + 48 + CH], 16, fill=(240, 243, 246)); d.text((x + cw / 2, y0 + 48 + CH / 2), 'not rendered yet', font=ImageFont.truetype(REG, 28), fill=MUTED, anchor='mm')
                x += cw + G
            cap = f"{f['section']}" + (f" · {f['name']}" if f.get('name') else '') + (f" · {f['cap']}" if f.get('cap') else '')
            for k, line in enumerate(wrap(d, cap, ImageFont.truetype(REG, 30), CW[0])[:2]):
                d.text((G, y0 + 48 + CH + 12 + k * 38), line, font=ImageFont.truetype(REG, 30), fill=INK)
            d.line([(G, y0 + rowh - 14), (W - G, y0 + rowh - 14)], fill=(226, 230, 234), width=3)
        p = os.path.join(folder, f'before-after-blender-{part[0]["n"]}-{part[-1]["n"]}.jpg'); img.save(p, quality=86); out.append(p)
    return out

def keep_threejs(article):
    level, name = article.split('/'); folder = os.path.join(DESIGN, 'figure-style', 'articles', level, name)
    for f in os.listdir(folder):
        base, ext = os.path.splitext(f)
        if ext == '.jpg' and base.isdigit() and not os.path.exists(os.path.join(folder, f'{base}-threejs.jpg')):
            shutil.copy(os.path.join(folder, f), os.path.join(folder, f'{base}-threejs.jpg'))

if __name__ == '__main__':
    a = sys.argv[1]; keep_threejs(a)
    for p in sheets(a): print(p)
