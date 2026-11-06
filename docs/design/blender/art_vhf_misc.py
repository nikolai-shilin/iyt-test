# Article bareboat-skipper/vhf-radio-operator: six figures that are not the radio's own screens, as Blender renders.
#   --article licences --fig 2  the ship station licence, framed on the nav-station bulkhead beside the VHF
#   --article licences --fig 5  the radio log open on the chart table, four entries in pencil, the pencil on the page
#   --article gmdss    --fig 4  the NAVTEX receiver, its screen showing the message header ZCZC HB45
#   --article phonetic --fig 1  the code flags N, O, V, A hoisted under the starboard spreader: "Nova"
#   --article set      --fig 4  the battery monitor at 11.2 V in red beside the VHF on 25 W (HI)
#   --article set      --fig 5  the yacht broadside, sails down: a whip antenna at the masthead, a short one on the pushpit
# Textures (licence, log pages, NAVTEX screen, flags, LCDs) are drawn with Pillow by this same file run under the
# system Python (python3 art_vhf_misc.py --prep); Blender runs it on its own when a texture is missing.
#   blender --background --factory-startup --python docs/design/blender/art_vhf_misc.py -- --article licences --fig 2
import os, sys, math, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(HERE, 'textures')
SUP = '/System/Library/Fonts/Supplemental/'
FONTS = {'bold': SUP + 'Arial Bold.ttf', 'reg': SUP + 'Arial.ttf', 'serif': SUP + 'Times New Roman Bold.ttf',
         'serif_r': SUP + 'Times New Roman.ttf', 'mono': '/System/Library/Fonts/Menlo.ttc', 'din': SUP + 'DIN Condensed Bold.ttf',
         'hand': SUP + 'Bradley Hand Bold.ttf', 'narrow': SUP + 'Arial Narrow Bold.ttf'}
T = lambda name: os.path.join(TEX, 'vhfm-' + name + '.png')
NAMES = ['licence', 'radiolog', 'navtex', 'flag-N', 'flag-O', 'flag-V', 'flag-A', 'battery', 'vhf-lcd']


# ---------------------------------------------------------------- textures (system Python, Pillow)
def prep():
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    f = lambda k, n: ImageFont.truetype(FONTS[k], int(n))
    os.makedirs(TEX, exist_ok=True)

    # the licence: an A4 page, portrait
    w, h = 1240, 1754; im = Image.new('RGB', (w, h), (246, 243, 234)); d = ImageDraw.Draw(im)
    navy = (22, 44, 86)
    d.rectangle([40, 40, w - 40, h - 40], outline=navy, width=10); d.rectangle([62, 62, w - 62, h - 62], outline=navy, width=3)
    d.rectangle([62, 62, w - 62, 330], fill=navy)
    d.text((w / 2, 150), 'SHIP STATION', font=f('serif', 112), fill=(255, 255, 255), anchor='mm')
    d.text((w / 2, 262), 'LICENCE', font=f('serif', 112), fill=(255, 255, 255), anchor='mm')
    d.text((w / 2, 395), 'Radio licence for the radio equipment on board', font=f('serif_r', 40), fill=(60, 60, 60), anchor='mm')
    rows = [('Vessel', 'sailing yacht Nefeli'), ('Licensee', 'Nefeli Charters Ltd'), ('Call sign', 'SY7NF'),
            ('MMSI', '237 004 810'), ('Equipment', 'fixed VHF with DSC'), ('', 'handheld VHF'), ('Valid until', '31 December 2027')]
    y = 520
    for k, v in rows:
        if k: d.text((120, y), k, font=f('reg', 44), fill=(90, 90, 90), anchor='lm')
        d.text((470, y), v, font=f('bold', 56), fill=(20, 20, 24), anchor='lm')
        if k: d.line([(120, y + 52), (w - 120, y + 52)], fill=(200, 196, 186), width=2)
        y += 118 if k else 90
    # the stamp and a signature
    cx, cy = 900, 1500
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], outline=(150, 40, 50), width=8)
    d.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], outline=(150, 40, 50), width=3)
    d.text((cx, cy - 20), 'RADIO', font=f('bold', 46), fill=(150, 40, 50), anchor='mm'); d.text((cx, cy + 34), 'LICENSING', font=f('bold', 34), fill=(150, 40, 50), anchor='mm')
    pts = [(160 + i * 9, 1520 + 26 * math.sin(i * 0.33) - i * 0.6 + 14 * math.sin(i * 1.1)) for i in range(45)]
    d.line(pts, fill=(30, 40, 90), width=6); d.line([(150, 1590), (560, 1590)], fill=(120, 120, 120), width=2)
    d.text((150, 1625), 'for the licensing office', font=f('serif_r', 34), fill=(90, 90, 90), anchor='lm')
    im.filter(ImageFilter.GaussianBlur(0.6)).save(T('licence'))

    # the radio log: both pages of an open book, the far edge at the top of the image
    w, h = 2400, 1700; im = Image.new('RGB', (w, h), (244, 240, 228)); d = ImageDraw.Draw(im)
    R0, RS = 300, 150                                                          # first rule, row pitch
    for x0 in (0, w // 2):
        for yy in range(R0, h - 60, RS): d.line([(x0 + 80, yy), (x0 + w // 2 - 60, yy)], fill=(170, 190, 215), width=3)
        for xx in (x0 + 300, x0 + 390): d.line([(xx, 200), (xx, h - 60)], fill=(220, 120, 120), width=3)
        d.text((x0 + 190, 250), 'TIME', font=f('bold', 34), fill=(110, 120, 140), anchor='mm')
        d.text((x0 + 345, 250), 'CH', font=f('bold', 34), fill=(110, 120, 140), anchor='mm')
        d.text((x0 + 410, 250), 'STATION · MESSAGE', font=f('bold', 34), fill=(110, 120, 140), anchor='lm')
    d.text((80, 120), 'RADIO LOG', font=f('bold', 64), fill=(40, 50, 80), anchor='lm')
    d.text((w // 2 - 60, 120), 'yacht Nefeli', font=f('bold', 46), fill=(60, 70, 100), anchor='rm')
    d.text((w // 2 + 80, 120), 'Tuesday 14 May', font=f('hand', 70), fill=(70, 72, 80), anchor='lm')
    ink = (28, 30, 40)
    def entry(x0, row, t, ch, msg, size=70):
        yy = R0 + (row + 1) * RS - 48; room = w // 2 - 60 - 405 - 10
        while d.textlength(msg, font=f('hand', size)) > room: size -= 2
        d.text((x0 + 190, yy), t, font=f('hand', 58), fill=ink, anchor='mm')
        d.text((x0 + 345, yy), ch, font=f('hand', 58), fill=ink, anchor='mm')
        d.text((x0 + 405, yy), msg, font=f('hand', size), fill=ink, anchor='lm')
    entry(0, 0, '08:30', '72', 'Radio check, loud and clear', 60)
    entry(0, 1, '09:15', '16', 'Weather from coast stn: NW 4', 60)
    entry(0, 2, '11:50', '72', 'Called yacht Selene, no answer', 60)
    entry(w // 2, 0, '14:05', '16', 'MAYDAY heard, yacht Selene')
    entry(w // 2, 1, '14:07', '16', 'Acknowledged by coast station')
    entry(w // 2, 2, '14:40', '16', 'PAN-PAN heard, MV Ionian')
    entry(w // 2, 3, '15:10', '16', 'SÉCURITÉ sent: buoy adrift')
    sh = Image.new('L', (w, h), 0); sd = ImageDraw.Draw(sh)                 # shade towards the spine
    for i in range(160): sd.line([(w // 2 - i, 0), (w // 2 - i, h)], fill=int(70 * (1 - i / 160) ** 2)); sd.line([(w // 2 + i, 0), (w // 2 + i, h)], fill=int(70 * (1 - i / 160) ** 2))
    im = Image.composite(Image.new('RGB', (w, h), (120, 110, 90)), im, sh)
    im.filter(ImageFilter.GaussianBlur(0.7)).save(T('radiolog'))

    # the NAVTEX screen: header bar, then the message with its ZCZC header line big
    w, h = 1200, 750; im = Image.new('RGB', (w, h), (178, 196, 170)); d = ImageDraw.Draw(im)
    for x in range(0, w, 6): d.line([(x, 0), (x, h)], fill=(170, 189, 163))
    d.rectangle([0, 0, w, 86], fill=(36, 48, 40))
    d.text((24, 44), 'NAVTEX 518 kHz', font=f('mono', 44), fill=(178, 196, 170), anchor='lm')
    d.text((w - 24, 44), 'MSG 4/7', font=f('mono', 44), fill=(178, 196, 170), anchor='rm')
    big = f('mono', 132); hx, hy = 40, 190; text = 'ZCZC HB45'
    d.text((hx, hy), text, font=big, fill=(18, 24, 18), anchor='lm'); cw = d.textlength('M', font=big)
    marks = {'H': hx + cw * 5.5, 'B': hx + cw * 6.5, '45': hx + cw * 8.0}
    for i, ln in enumerate(['081340 UTC NOV', 'GALE WARNING', 'NW 8, LOCALLY 9 LATER', 'NNNN']):
        d.text((40, 340 + i * 98), ln, font=f('mono', 66), fill=(18, 24, 18), anchor='lm')
    im.save(T('navtex'))
    json.dump({k: [x / w, (hy - 66) / h] for k, x in marks.items()}, open(T('navtex').replace('.png', '.json'), 'w'))

    # the code flags, hoist on the left, 6 : 5
    w, h = 600, 500; blue, red, yel, white = (8, 46, 120), (160, 14, 18), (215, 160, 0), (218, 218, 212)   # dyed bunting: darker than print, it is in full sun
    im = Image.new('RGB', (w, h), white); d = ImageDraw.Draw(im)
    for i in range(4):
        for j in range(4):
            if (i + j) % 2 == 0: d.rectangle([i * w / 4, j * h / 4, (i + 1) * w / 4, (j + 1) * h / 4], fill=blue)
    im.save(T('flag-N'))
    im = Image.new('RGB', (w, h), yel); d = ImageDraw.Draw(im); d.polygon([(0, 0), (w, 0), (w, h)], fill=red); im.save(T('flag-O'))
    im = Image.new('RGB', (w, h), white); d = ImageDraw.Draw(im)
    d.line([(0, 0), (w, h)], fill=red, width=110); d.line([(0, h), (w, 0)], fill=red, width=110); im.save(T('flag-V'))
    im = Image.new('RGB', (w, h), white); d = ImageDraw.Draw(im); d.rectangle([w * 0.5, 0, w, h], fill=blue); im.save(T('flag-A'))

    # the battery monitor's LCD
    w, h = 800, 560; im = Image.new('RGB', (w, h), (150, 178, 160)); d = ImageDraw.Draw(im)
    d.text((30, 52), 'HOUSE BATTERY', font=f('bold', 50), fill=(20, 28, 24), anchor='lm')
    d.rounded_rectangle([24, 108, w - 24, 360], 18, fill=(178, 28, 28))
    d.text((w / 2, 236), '11.2 V', font=f('din', 230), fill=(255, 240, 235), anchor='mm')
    d.text((30, 420), '-6.4 A', font=f('bold', 58), fill=(20, 28, 24), anchor='lm')
    d.text((w - 30, 420), '38 %', font=f('bold', 58), fill=(20, 28, 24), anchor='rm')
    d.text((w / 2, 505), '!  LOW VOLTAGE', font=f('bold', 48), fill=(170, 20, 20), anchor='mm')
    im.save(T('battery'))

    # the VHF's own LCD redrawn: channel 16, HI, 25 W (covers px 362..625 x 142..352 of the front photo)
    w, h = 1052, 840; bg, ink = (200, 208, 196), (18, 20, 18); im = Image.new('RGB', (w, h), bg); d = ImageDraw.Draw(im)
    d.text((40, 40), 'INT', font=f('narrow', 70), fill=ink, anchor='lt'); d.text((220, 40), 'DSC', font=f('narrow', 70), fill=ink, anchor='lt')
    d.rounded_rectangle([w - 300, 30, w - 40, 130], 12, fill=ink); d.text((w - 170, 82), 'HI', font=f('narrow', 84), fill=bg, anchor='mm')
    d.text((w - 170, 200), '25 W', font=f('narrow', 80), fill=ink, anchor='mm')
    d.text((w / 2 - 80, 450), '16', font=f('din', 520), fill=ink, anchor='mm')
    d.text((w / 2, 760), 'DISTRESS', font=f('narrow', 96), fill=ink, anchor='mm')
    im.save(T('vhf-lcd'))
    print('textures ->', TEX)


try:
    import bpy
except ImportError:
    bpy = None
if bpy is None:
    prep(); sys.exit(0)

# ---------------------------------------------------------------- Blender
sys.path.insert(0, HERE)
import bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
import common as C, kit as K, kit_instruments as KI

if not all(os.path.exists(T(n)) for n in NAMES) or '--retex' in sys.argv:
    subprocess.run(['python3', os.path.abspath(__file__)], check=True)

arg = C.cli(); ART = arg('--article', 'licences'); FIG = arg('--fig', 2); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(HERE, '..', 'figure-style', 'articles', 'vhf-radio-operator', ART, f'{FIG}-3d.jpg'))
deg = math.radians

_load = K.load_yacht
def _yacht(*a, **k):
    """kit.load_yacht, minus the spinnaker's pale triangle and tack line the model keeps when the spinnaker is down."""
    yt = _load(*a, **k)
    for o in yt.objs:
        anc, q = [], o.parent
        while q: anc.append(q.name); q = q.parent
        if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                 any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
            o.hide_render = True
    return yt
K.load_yacht = _yacht

def quad(name, w, h, path, loc, emit=0.0, rough=0.4, normal='-Y'):
    """A flat image w x h metres centred at loc, facing -Y (on a bulkhead) or +Z (lying on a table)."""
    me = bpy.data.meshes.new(name); x, z = w / 2, h / 2
    pts = [(-x, 0, -z), (x, 0, -z), (x, 0, z), (-x, 0, z)] if normal == '-Y' else [(-x, -z, 0), (x, -z, 0), (x, z, 0), (-x, z, 0)]
    me.from_pydata(pts, [], [(0, 1, 2, 3)])
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    return C.obj(name, me, KI.image_mat(name, path, rough, emit), Vector(loc))

def vhf(at=(0, 0, 0)):
    """The SIMRAD RS20S fixed VHF, front panel facing -Y, its front's lower left corner at `at`. Returns the y of
    the photographed front (for drawing over its LCD)."""
    root, objs = K.load_model('radio-vhf-simrad-rs20s.glb', drop_planes=False)
    for o in objs:
        if o.type == 'MESH' and all(sl.material is None for sl in o.material_slots) and len(o.data.polygons) <= 4: o.hide_render = True
    for o in objs:
        for sl in getattr(o, 'material_slots', []):
            m = sl.material
            if m and m.node_tree:
                b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if b: b.inputs['Roughness'].default_value = 0.62; b.inputs['Specular IOR Level'].default_value = 0.25
    front = None
    for o in objs:
        if o.type != 'MESH': continue
        names = {sl.material.name for sl in o.material_slots if sl.material}
        if 'Material-7503' in names:
            mw = o.matrix_world.copy(); mw.translation.y -= 0.0006; o.matrix_world = mw; front = o
            old = next(sl.material for sl in o.material_slots if sl.material)
            img = next(n.image for n in old.node_tree.nodes if n.type == 'TEX_IMAGE')
            fm, fnt, fb, _ = C.new_mat('vhf-front'); tx = fnt.nodes.new('ShaderNodeTexImage'); tx.image = img
            uvn = fnt.nodes.new('ShaderNodeUVMap'); fnt.links.new(uvn.outputs['UV'], tx.inputs['Vector'])
            fnt.links.new(tx.outputs['Color'], fb.inputs['Base Color']); fb.inputs['Roughness'].default_value = 0.5
            for sl in o.material_slots: sl.material = fm
        if names & {'Fig30', '[Color M07]', '[Color_007]1'}:
            for sl in o.material_slots:
                bb = next((n for n in sl.material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if bb and not bb.inputs['Base Color'].is_linked: bb.inputs['Base Color'].default_value = (0.018, 0.019, 0.021, 1)
    root.location = Vector(at)
    bpy.context.view_layer.update()
    return min((front.matrix_world @ v.co).y for v in front.data.vertices)

def setup_frame():
    r = bpy.context.scene.render; r.resolution_x, r.resolution_y, r.resolution_percentage = C.W, C.H, 100

def to_px(p):
    bpy.context.view_layer.update()
    q = world_to_camera_view(bpy.context.scene, bpy.context.scene.camera, Vector(p)); return Vector((q.x * C.W, (1 - q.y) * C.H))

def shift_px(p, dx, dy):
    """`p` moved by (dx, dy) pixels in the frame (dy down), at the same depth from the camera."""
    bpy.context.view_layer.update()
    m = bpy.context.scene.camera.matrix_world.to_3x3(); right, up = m @ Vector((1, 0, 0)), m @ Vector((0, 1, 0))
    p = Vector(p); a = to_px(p); kx = (to_px(p + right * 0.01) - a).length / 0.01; ky = (to_px(p + up * 0.01) - a).length / 0.01
    return p + right * (dx / kx) - up * (dy / ky)

def nav_light():
    K.day_sky(sun_az=150, sun_el=40, strength=0.08)
    KI.area_light((0.5, -0.9, 0.55), (0.1, 0, 0.04), 7, 0.6)                 # the porthole, front right
    KI.area_light((-0.6, -0.8, 0.3), (0.1, 0, 0.04), 2, 1.0, (0.85, 0.9, 1.0))  # fill from the companionway

def frame(x0, z0, w, h, mat):
    """A picture frame on the bulkhead: four moulded bars round w x h, its lower left inner corner at (x0, z0)."""
    b, d = 0.016, 0.014
    for name, dims, loc in (('fr-t', (w + 2 * b, d, b), (x0 + w / 2, -d / 2, z0 + h + b / 2)), ('fr-b', (w + 2 * b, d, b), (x0 + w / 2, -d / 2, z0 - b / 2)),
                            ('fr-l', (b, d, h), (x0 - b / 2, -d / 2, z0 + h / 2)), ('fr-r', (b, d, h), (x0 + w + b / 2, -d / 2, z0 + h / 2))):
        C.obj(name, C.rbox(name, dims, 0.003, 2), mat, loc)

labels, note, expo, extra = [], None, -0.4, {}
C.reset(); setup_frame()
M = K.mats()

if ART == 'licences' and FIG == 2:
    KI.wall('bulkhead', -0.30, 0.70, -0.30, 0.45, 0.004, KI.joinery_mat())
    vhf((0.0, 0.0, 0.0))
    w, h = 0.17, 0.24; x0, z0 = 0.275, -0.075
    frame(x0 - 0.012, z0 - 0.012, w + 0.024, h + 0.024, C.simple('frame-wood', '#2a1a10', 0.35, coat=0.6))
    C.obj('mount', C.rbox('mount', (w + 0.024, 0.003, h + 0.024), 0.0, 1), C.simple('mount', '#ece8de', 0.8), (x0 + w / 2, -0.0015, z0 + h / 2))
    quad('licence', w, h, T('licence'), (x0 + w / 2, -0.0035, z0 + h / 2), 0.0, 0.6)
    nav_light()
    K.camera((0.235, -0.70, 0.11), (0.235, 0, 0.07), 42)
    labels = [(shift_px((x0 + w / 2, -0.012, z0 + h + 0.03), 0, 0), 'ship station licence')]
    note = 'Vessel, call sign, MMSI: the licence goes with the boat'

elif ART == 'licences' and FIG == 5:
    # the chart table (z = 0), the bulkhead behind it with the VHF, the log open on the table
    KI.wall('table', -0.6, 0.6, -0.35, 0.40, 0.0, KI.joinery_mat('table-wood')).data.vertices.foreach_set('co', [-0.6, -0.35, 0, 0.6, -0.35, 0, 0.6, 0.40, 0, -0.6, 0.40, 0])
    C.obj('fiddle', C.rbox('fiddle', (1.2, 0.02, 0.03), 0.004, 2), KI.joinery_mat('fiddle-wood'), (0, -0.34, 0.015))
    KI.wall('bulkhead', -0.6, 0.6, 0.0, 0.6, 0.40, KI.joinery_mat())
    vhf((0.18, 0.396, 0.24))
    pw, ph = 0.21, 0.297
    C.obj('cover', C.rbox('cover', (2 * pw + 0.012, ph + 0.012, 0.004), 0.0015, 2), C.simple('cloth', '#1d2a4a', 0.85, sheen=0.4), (0, 0, 0.002))
    for s in (-1, 1):
        C.obj('block', C.rbox('block', (pw - 0.05, ph - 0.004, 0.008), 0.002, 2), C.simple('paper-edge', '#e9e4d6', 0.9), (s * (0.04 + (pw - 0.05) / 2), 0, 0.008))
    bm = bmesh.new(); nu, nv = 80, 8; uvl = bm.loops.layers.uv.new('UVMap'); V = []
    zf = lambda x: 0.007 + 0.0095 * min(1.0, abs(x) / 0.035) ** 0.5 - 0.002 * (abs(x) / pw) ** 2
    for j in range(nv + 1):
        for i in range(nu + 1):
            x = -pw + 2 * pw * i / nu; yv = -ph / 2 + ph * j / nv; V.append(bm.verts.new((x, yv, zf(x))))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i; fc = bm.faces.new((V[a], V[a + 1], V[a + nu + 2], V[a + nu + 1])); fc.smooth = True
            for lp, (ii, jj) in zip(fc.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))): lp[uvl].uv = (ii / nu, jj / nv)
    me = bpy.data.meshes.new('pages'); bm.to_mesh(me); bm.free(); C.obj('pages', me, KI.image_mat('pages', T('radiolog'), 0.85))
    # the pencil, lying across the lower right page
    pr, pl = 0.0036, 0.15; pen = []
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=pr, radius2=pr, depth=pl)
    me = bpy.data.meshes.new('pencil'); bm.to_mesh(me); bm.free()
    pen.append(C.obj('pencil', me, C.simple('pencil-paint', '#e2a917', 0.35, coat=0.6), (0, 0, 0)))
    pen.append(C.cyl('pencil-wood', pr, 0.0008, 0.018, 24, C.simple('pencil-wood', '#d8b48a', 0.7), (0, 0, pl / 2 + 0.009)))
    pen.append(C.cyl('pencil-lead', 0.0008, 0.0001, 0.003, 12, C.simple('graphite', '#2a2a2c', 0.4, 0.6), (0, 0, pl / 2 + 0.0195)))
    pen.append(C.cyl('pencil-ferrule', pr * 1.02, pr * 1.02, 0.01, 24, M['satin'], (0, 0, -pl / 2 - 0.005)))
    pen.append(C.cyl('pencil-eraser', pr, pr, 0.008, 24, C.simple('eraser', '#e48a8a', 0.8), (0, 0, -pl / 2 - 0.014)))
    pivot = bpy.data.objects.new('pencil-pivot', None); C.col.objects.link(pivot)
    for o in pen: o.parent = pivot
    pivot.rotation_euler = (deg(90), 0, deg(-62)); pivot.location = (0.115, -0.095, zf(0.115) + pr)
    nav_light()
    KI.area_light((0.0, -0.5, 0.9), (0, 0, 0), 4, 0.8)
    K.camera((0.0, -0.44, 0.46), (0.0, 0.03, 0.0), 40); expo = -0.7
    labels = [(shift_px((0.105, ph / 2, zf(0.105)), 0, 0), 'radio log')]
    note = 'Distress, urgency and safety traffic: time, station, what was said'

elif ART == 'gmdss' and FIG == 4:
    KI.wall('bulkhead', -0.50, 0.40, -0.30, 0.32, 0.004, KI.joinery_mat())
    C.obj('navtex-case', C.rbox('nc', (0.215, 0.09, 0.145), 0.008, 3), C.simple('navtex-plastic', '#2b2e31', 0.55), (-0.17, -0.04, 0.03))
    C.obj('navtex-bezel', C.rbox('nb', (0.150, 0.006, 0.098), 0.004, 2), C.simple('navtex-bezel', '#151719', 0.4), (-0.185, -0.0875, 0.045))
    sw, sh = 0.136, 0.085; sc = Vector((-0.185, -0.0912, 0.045))
    quad('navtex-lcd', sw, sh, T('navtex'), sc, 0.9, 0.25)
    for i in range(6):                                  # six keys down the right of the screen, a red LED below
        C.obj('key', C.rbox('k', (0.014, 0.006, 0.010), 0.002, 2), C.simple('navtex-key', '#3c4044', 0.5), (-0.088, -0.087, 0.085 - i * 0.016))
    C.obj('led', KI._cyl_y(0.0025, 0.002), C.simple('led-red', '#c81a12', 0.3, coat=1.0), (-0.088, -0.0875, -0.018))
    vhf((0.02, 0.0, -0.015))
    K.day_sky(sun_az=150, sun_el=40, strength=0.08)
    KI.area_light((0.3, -0.9, 0.55), (-0.15, 0, 0.04), 6, 0.6)
    KI.area_light((-0.8, -0.8, 0.3), (-0.15, 0, 0.04), 2, 1.0, (0.85, 0.9, 1.0))
    K.camera((-0.17, -0.40, 0.10), (-0.16, 0, 0.045), 50)
    pos = json.load(open(T('navtex').replace('.png', '.json')))
    at = lambda k: sc + Vector(((pos[k][0] - 0.5) * sw, -0.001, (0.5 - pos[k][1]) * sh))
    labels = [(at('H'), 'H · station'), (shift_px(at('B'), 0, -66), 'B · subject: weather'), (shift_px(at('45'), 0, -132), '45 · number')]
    note = 'NNNN · end of the message'

elif ART == 'phonetic' and FIG == 1:
    K.day_sky(sun_az=25, sun_el=38)                              # the sun behind the camera: the flags lit
    K.sea('calm', center=(0, 0))
    y = K.load_yacht(name='yacht').place(0, 0, heading=270)       # bow to -X (left), her starboard side towards +Y
    tip = y.world((4.51, -1.60, 9.30)); foot = y.world((4.45, -1.56, 4.30))   # under the lower starboard spreader
    flagdir = Vector((-1, 0, 0)); side = Vector((0, 1, 0))       # a breeze from astern blows them towards the bow
    hl, fl, gap = 0.60, 0.75, 0.14; top = tip.z - 0.25
    tie = [tip, Vector((tip.x, tip.y, top))]
    rope = C.simple('halyard', '#ece6d8', 0.8)
    anchors = []
    for k, (letter, name) in enumerate((('N', 'November'), ('O', 'Oscar'), ('V', 'Victor'), ('A', 'Alfa'))):
        zt = top - k * (hl + gap); hoist = Vector((tip.x + 0.02 * k, tip.y, zt))
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); nu, nv = 40, 20; V = []
        for j in range(nv + 1):
            v = j / nv
            umax = (0.75 + 0.25 * abs(v - 0.5) / 0.5) if letter == 'A' else 1.0
            for i in range(nu + 1):
                u = i / nu * umax
                p = hoist + Vector((0, 0, -(1 - v) * hl)) + flagdir * (u * fl * (1 - 0.05 * u)) \
                    + side * (0.05 * u ** 1.2 * math.sin(2 * math.pi * 1.15 * u + k * 1.3 + 0.7 * v)) + Vector((0, 0, -0.04 * u * u))
                V.append((bm.verts.new(p), (u, v)))
        for j in range(nv):
            for i in range(nu):
                a = j * (nu + 1) + i; q = (V[a], V[a + 1], V[a + nu + 2], V[a + nu + 1])
                fc = bm.faces.new([t[0] for t in q]); fc.smooth = True
                for lp, t in zip(fc.loops, q): lp[uvl].uv = t[1]
        me = bpy.data.meshes.new('flag-' + letter); bm.to_mesh(me); bm.free()
        mt = KI.image_mat('flag-' + letter, T('flag-' + letter), 0.85)
        C.obj('flag-' + letter, me, mt)
        tie += [Vector((hoist.x, hoist.y, zt)), Vector((hoist.x, hoist.y, zt - hl))]
        anchors.append((hoist + flagdir * fl + Vector((0, 0, -hl / 2)), name))
    tie.append(foot)
    C.tube('halyard', tie, 0.005, 8, 0.05, rope)
    eye = Vector((tip.x - 1.6, tip.y + 12.5, 3.2)); look = Vector((tip.x - 1.4, tip.y, 4.5))
    K.camera(eye, look, 44)
    for p, name in anchors:
        labels.append((shift_px(p, 100, 46), name))
    note = 'The code flags carry the same names'; expo = -0.9

elif ART == 'set' and FIG == 4:
    KI.wall('bulkhead', -0.30, 0.70, -0.30, 0.40, 0.004, KI.joinery_mat())
    fy = vhf((0.0, 0.0, 0.0))
    # the redrawn LCD over the photographed one: 25 W, HI, channel 16
    u0, u1, v0, v1 = 362 / 999, 625 / 999, 142 / 531, 352 / 531
    quad('vhf-lcd', (u1 - u0) * 0.17, (v1 - v0) * 0.09, T('vhf-lcd'), ((u0 + u1) / 2 * 0.17, fy - 0.0004, (1 - (v0 + v1) / 2) * 0.09), 0.5, 0.3)
    # the battery monitor beside it
    bx, bz = 0.29, 0.045
    C.obj('bm-case', C.rbox('bmc', (0.12, 0.024, 0.095), 0.006, 3), C.simple('bm-plastic', '#1c1e21', 0.5), (bx, -0.012, bz))
    C.obj('bm-bezel', C.rbox('bmb', (0.094, 0.004, 0.068), 0.003, 2), C.simple('bm-bezel', '#0e0f11', 0.35), (bx, -0.0245, bz + 0.008))
    quad('bm-lcd', 0.086, 0.060, T('battery'), (bx, -0.0268, bz + 0.008), 0.8, 0.25)
    for i, col in enumerate(('#3a3e43', '#3a3e43', '#3a3e43')):
        C.obj('bm-key', C.rbox('bmk', (0.016, 0.004, 0.008), 0.002, 2), C.simple('bm-key', col, 0.5), (bx - 0.025 + i * 0.025, -0.0245, bz - 0.036))
    m, nt, b, out = C.new_mat('bm-led'); em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.06, 0.04, 1); em.inputs['Strength'].default_value = 3.0
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    C.obj('bm-led', KI._cyl_y(0.0028, 0.003), m, (bx + 0.05, -0.0255, bz - 0.036))
    nav_light()
    K.camera((0.17, -0.60, 0.10), (0.17, 0, 0.045), 42)
    labels = [(Vector((bx, -0.03, bz + 0.05)), 'battery 11.2 V: low', 'red')]
    note = 'Engine off since yesterday: the radio is weak'

elif ART == 'set' and FIG == 5:
    K.day_sky(sun_az=25, sun_el=38)
    K.sea('calm', center=(0, 0))
    y = K.load_yacht(name='yacht').place(0, 0, heading=270)
    for o in y.objs:                                   # the model's own thin grey stub at the masthead
        if o.type == 'MESH' and o.name.startswith('Geom3D.925'): o.hide_render = True
    white = C.simple('antenna-white', '#f2f2ee', 0.35, coat=0.5)
    mh = y.world((5.02, 0.03, 20.62)); L = 1.5
    C.cyl('whip-mast', 0.04, 0.022, L, 16, white, mh + Vector((0, 0, L / 2)))
    C.cyl('whip-mast-base', 0.04, 0.04, 0.10, 16, M['dark'], mh + Vector((0, 0, 0.05)))
    pp = y.world((-3.30, -1.22, 4.40)); Lp = 1.0
    C.cyl('whip-rail', 0.032, 0.02, Lp, 16, white, pp + Vector((0, 0, Lp / 2 + 0.03)))
    C.cyl('whip-rail-mount', 0.026, 0.026, 0.08, 16, M['chrome'], pp + Vector((0, 0, 0.0)))
    mid = (mh + pp) / 2
    K.camera(Vector((mid.x + 4.0, 46.0, 8.5)), Vector((mid.x + 4.5, 0.0, 10.9)), 42)   # the yacht right of centre, clear of the note
    labels = [(mh + Vector((0, 0, L)), 'masthead antenna: reaches far'), (pp + Vector((0, 0, Lp + 0.05)), 'on the rail: short range')]
    note = 'The higher the antenna, the further its horizon'; expo = -0.6

else:
    raise SystemExit(f'no figure {ART} {FIG}')

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', extra=extra)
