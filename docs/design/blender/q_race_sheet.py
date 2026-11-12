"""Contact sheets of the Racing Rules race diagrams: 12 questions a sheet, the question image and the plan side by side,
the id, topic and answer under them. Writes figure-style/questions/racing-rules/sheet-race-<k>.jpg.
   python3 docs/design/blender/q_race_sheet.py [--ru] [--topic definitions] [--ids rr-001,rr-002] [--out <dir>]"""
import json, os, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, '..', 'figure-style', 'questions', 'racing-rules')
args = sys.argv[1:]
RU = '--ru' in args
opt = lambda k: args[args.index(k) + 1] if k in args else None
topic, ids, out = opt('--topic'), opt('--ids'), opt('--out') or DIR
items = json.load(open(os.path.join(DIR, 'race.json')))
if topic: items = [e for e in items if e['topic'] == topic]
if ids: items = [e for e in items if e['id'] in ids.split(',')]
TW, TH, CAP = 560, 350, 74
try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); bold = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 16)
except OSError: font = bold = ImageFont.load_default()
suf = '.ru' if RU else ''
for k in range(0, len(items), 12):
    chunk = items[k:k + 12]
    cols, rows = 2, (len(chunk) + 1) // 2
    sheet = Image.new('RGB', (cols * (2 * TW + 30), rows * (TH + CAP + 16)), 'white')
    d = ImageDraw.Draw(sheet)
    for n, e in enumerate(chunk):
        x0, y0 = (n % cols) * (2 * TW + 30), (n // cols) * (TH + CAP + 16)
        for j, kind in enumerate(['q', 'plan']):
            p = os.path.join(DIR, e['id'], f'{kind}{suf}.png')
            if not os.path.exists(p): continue
            im = Image.open(p).convert('RGB'); im.thumbnail((TW, TH))
            sheet.paste(im, (x0 + j * (TW + 6), y0))
        d.text((x0, y0 + TH + 4), f"{e['id']} · {e['topic']}", fill='black', font=bold)
        for i, line in enumerate(textwrap.wrap('A: ' + e['answer'], 140)[:3]):
            d.text((x0, y0 + TH + 24 + i * 17), line, fill=(60, 60, 60), font=font)
    name = f"sheet-race-{k // 12 + 1}{'-ru' if RU else ''}.jpg" if not (topic or ids) else f"sheet-race-{topic or 'ids'}-{k // 12 + 1}{'-ru' if RU else ''}.jpg"
    sheet.save(os.path.join(out, name), quality=82)
    print(name)
