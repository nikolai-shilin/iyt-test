# Article bareboat-skipper/safety, figures 1, 3, 4, 5, 6 as Blender renders (fig 2 reuses the man-overboard render).
#   1  dead run with a preventer: boom end led forward to the bow cleat and back to the cockpit
#   3  the CO alarm going off in the saloon, the gas valve off, the companionway open
#   4  the liferaft launched to leeward on its painter, the canister on the pushpit, the grab bag on deck
#   5  a tender going dead slow towards a beach with swimmers inside a buoyed swim zone; our yacht anchored off
#   6  stay in harbour: grey dawn from the quay, yachts with doubled lines, the sea breaking beyond the mole
#   blender --background --factory-startup --python docs/design/blender/art_safety.py -- --fig 1 [--out x.jpg]
import os, sys, math, random, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import common as C, kit as K, kit_world as KW, kit_instruments as KI
from common import lin

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'safety')
arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(OUTDIR, f'{FIG}-3d.jpg'))
def deg(a): return math.radians(a)

# kit.load_yacht minus the spinnaker leftovers (same local fix as art_colregs_a.py)
_load = K.load_yacht
def _yacht(*a, **k):
    yt = _load(*a, **k)
    for o in yt.objs:
        anc, q = [], o.parent
        while q: anc.append(q.name); q = q.parent
        if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                 any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
            o.hide_render = True
    return yt
K.load_yacht = _yacht

# the cloudy sky from art_weather_a.py, taken from its source (importing that module would run its figure)
_src = open(os.path.join(HERE, 'art_weather_a.py')).read()
exec(_src[_src.index('def cloud_sky('):_src.index('def compass(')], globals())

def T(v):
    """Blender point -> Three.js point object for common.braid / three_strand."""
    return C.V3((v.x, v.z, -v.y))

def line(name, pts, R=0.007, base='#e9e6dc', fleck='#1f3f78'):
    C.braid(name, [T(Vector(p)) for p in pts], R, base, fleck, False, None, None, 1.4)

def sag(a, b, n=10, s=0.15):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Vector((0, 0, s * math.sin(math.pi * i / n))) for i in range(n + 1)]

def sphere(name, r, mat, loc, scale=(1, 1, 1), seg=24):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.shade_smooth()
    o = C.obj(name, me, mat, Vector(loc)); o.scale = scale; return o

def torus(name, R, r, mat, loc, seg=48):
    o = C.obj(name, KI._torus(R, r), mat, Vector(loc)); return o

def dup(y, name):
    """A linked copy of a whole yacht (objects share their mesh data), returned as its root."""
    m = {}
    def walk(o):
        c = o.copy(); C.col.objects.link(c); m[o] = c
        for ch in o.children: walk(ch)
    walk(y.root)
    for o, c in m.items():
        if o.parent in m: c.parent = m[o.parent]
    m[y.root].name = name
    return m[y.root]

def place_root(root, x, y, heading):
    root.location = (x, y, 0.0); root.rotation_euler = (0, 0, deg(90 - heading))

C.reset()
labels, arrows, note, expo, extra = [], [], None, -0.6, None

if FIG == 1:
    # dead run, wind from the north, heading 180: main right out to starboard, a preventer from the boom end to the
    # bow cleat and back aft along the side deck to the cockpit
    K.day_sky(sun_az=230, sun_el=38)
    K.sea('breeze', repeat=10)
    y = K.load_yacht(name='you', sails={'main': True, 'genoa': 'port', 'boom': -78})
    y.place(0, 0, heading=180, heel=0)
    bpy.context.view_layer.update()
    end = y.boom_pivot.matrix_world @ Vector((-5.15, 0.0, 0.05))          # the boom end
    # rig the preventer on the side the boom is actually out on (model +y is port)
    sd = 1 if (y.world((0, 1, 3.5)) - end).length < (y.world((0, -1, 3.5)) - end).length else -1
    W = lambda x, yy, z: y.world((x, yy * sd, z))
    bow = W(10.25, 0.95, 3.62); fair = W(7.6, 1.75, 3.62); cock = W(-1.4, 1.2, 3.75)
    line('preventer', sag(end, fair, 8, 0.35)[:-1] + [fair, bow + Vector((0, 0, 0.05)), W(9.4, 1.2, 3.66), W(4.0, 1.85, 3.66), W(0.6, 1.7, 3.7), cock],
         R=0.028, base='#d23a2f', fleck='#f3efe6')   # drawn thicker than life so it reads
    eye = W(-21.0, 6.5, 21.0); look = W(2.0, 3.4, 4.0)
    if arg('--top', 0): eye, look = Vector((0.1, 0, 40)), Vector((0, 0, 0))
    K.camera(tuple(eye), tuple(look), 30)
    mid = end.lerp(fair, 0.45)
    labels = [(tuple(mid + Vector((0, 0, 0.6))), 'preventer', 'red'), (tuple(y.world((-0.5, 0.13, 6.2))), 'heads below the boom', 'blue')]
    w0, w1 = W(-6.0, -5.5, 7.5), W(1.0, -5.5, 6.5)
    arrows = [(tuple(w0), tuple(w1), 'blue')]; labels.append((tuple(w0 + Vector((0, 0, 1.0))), 'Wind astern', 'blue'))
    note = 'Dead run: rig a preventer, heads below the boom'; expo = -0.5

elif FIG == 3:
    # the saloon: galley to port with a two-burner hob, the gas valve below the counter turned OFF (red lever across
    # the pipe), the CO alarm on the bulkhead flashing red, the companionway open to daylight on the right
    os.makedirs(KI.TEX, exist_ok=True)
    co_png = os.path.join(KI.TEX, 'co-alarm.png')
    subprocess.run(['python3', '-c', f'''
from PIL import Image, ImageDraw, ImageFont
im = Image.new("RGB", (512, 256), (28, 8, 8)); d = ImageDraw.Draw(im)
f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 92); s = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 40)
d.text((256, 96), "CO ALARM", font=f, fill=(255, 70, 50), anchor="mm"); d.text((256, 200), "312 ppm", font=s, fill=(255, 120, 90), anchor="mm")
im.save("{co_png}")'''], check=True)
    sc = bpy.context.scene
    w = bpy.data.worlds.new('dim'); sc.world = w; w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.025, 0.03, 1)
    M = K.mats(); join = KI.joinery_mat(); white = C.simple('cabinet', '#e9e6df', 0.45, coat=0.3)
    # sole, back bulkhead (y = 1.2) and the galley run along it, a side bulkhead (x = -1.6)
    C.tbox((5.0, 0.04, 4.0), (0, -0.02, 0), M['teak'], 0.0, 1, 'sole') if False else None
    sole = C.obj('sole', C.rbox('sole', (5.0, 4.0, 0.04), 0.0, 1), M['teak'], (0, 0, -0.02))
    KI.wall('bulkhead', -2.5, 2.5, 0.0, 2.1, 1.2, join).rotation_euler = (0, 0, 0)
    side = bpy.data.objects['bulkhead'].copy(); side.data = bpy.data.objects['bulkhead'].data.copy(); C.col.objects.link(side)
    side.rotation_euler = (0, 0, deg(90)); side.location = (-1.6 - 1.2, 0, 0)
    C.obj('counter', C.rbox('counter', (2.2, 0.62, 0.9), 0.01, 2), white, (-0.4, 0.89, 0.45))
    C.obj('worktop', C.rbox('worktop', (2.3, 0.66, 0.04), 0.008, 2), C.simple('worktop', '#c9c3b6', 0.35, coat=0.6), (-0.4, 0.88, 0.92))
    hob = C.obj('hob', C.rbox('hob', (0.6, 0.42, 0.02), 0.005, 2), C.simple('hob-steel', '#b9bcbe', 0.3, 0.9), (-0.85, 0.86, 0.95))
    blk = C.simple('burner', '#151516', 0.5, 0.3)
    for i, x in enumerate((-1.0, -0.7)):
        C.cyl(f'burner{i}', 0.07, 0.065, 0.025, 32, blk, (x, 0.86, 0.97))
        torus(f'grate{i}', 0.11, 0.008, blk, (x, 0.86, 0.985))
    # the gas valve on the counter front: a brass body on its pipe, the red lever at right angles to the pipe = OFF
    brass = C.simple('brass', '#b08a3a', 0.35, 1.0)
    C.cyl('gas-pipe', 0.008, 0.008, 0.6, 12, C.simple('copper', '#b26a3c', 0.4, 1.0), (-0.85, 0.575, 0.55))
    C.obj('valve', C.rbox('valve', (0.05, 0.04, 0.06), 0.008, 2), brass, (-0.85, 0.56, 0.62))
    lever = C.obj('lever', C.rbox('lever', (0.14, 0.018, 0.022), 0.006, 2), C.simple('lever-red', '#c4161c', 0.4, coat=0.6), (-0.79, 0.535, 0.62))
    C.obj('label-off', C.rbox('lab', (0.06, 0.004, 0.025), 0.001, 1), C.simple('label', '#f4f2ea', 0.5), (-0.85, 0.556, 0.68))
    # the CO alarm on the bulkhead: a white puck-box, a red LED and a small screen
    C.obj('co-body', C.rbox('co', (0.13, 0.035, 0.13), 0.012, 3), C.simple('co-white', '#f1f0ec', 0.4), (0.15, 1.18, 1.42))
    scr = KI.disc('co-screen', 0.04, KI.image_mat('co-screen', co_png, 0.3, emit=2.5), (0.15, 1.158, 1.43))
    scr.scale = (1.2, 0.6, 1)
    led = sphere('co-led', 0.009, C.simple('led', '#ff2010', 0.2), (0.2, 1.16, 1.375))
    em = led.data.materials[0]; b = next(n for n in em.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Emission Color'].default_value = (1, 0.05, 0.02, 1); b.inputs['Emission Strength'].default_value = 80
    pl = bpy.data.lights.new('led-glow', 'POINT'); pl.energy = 1.5; pl.color = (1, 0.1, 0.05); lo = bpy.data.objects.new('led-glow', pl); C.col.objects.link(lo); lo.location = (0.2, 1.1, 1.37)
    # the companionway: a bright opening in the deckhead to the right, daylight pouring in
    sky = C.new_mat('companionway-sky')[0]; nt = sky.node_tree; nt.nodes.clear()
    o_ = nt.nodes.new('ShaderNodeOutputMaterial'); e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = lin('#cfe0ee'); e_.inputs['Strength'].default_value = 6.0
    nt.links.new(e_.outputs[0], o_.inputs['Surface'])
    hatch = bpy.data.meshes.new('hatch'); hatch.from_pydata([(1.2, -0.5, 2.1), (2.0, -0.5, 2.1), (2.0, 0.6, 2.1), (1.2, 0.6, 2.1)], [], [(0, 1, 2, 3)])
    C.obj('hatch', hatch, sky)
    deckhead = bpy.data.meshes.new('deckhead'); deckhead.from_pydata([(-2.5, -2, 2.1), (1.2, -2, 2.1), (1.2, 1.2, 2.1), (-2.5, 1.2, 2.1)], [], [(0, 1, 2, 3)])
    C.obj('deckhead', deckhead, C.simple('lining', '#e6e2d8', 0.8))
    KI.area_light((1.6, 0.05, 2.6), (0.0, 0.7, 0.8), 420, 0.9, (0.95, 0.97, 1.0))
    KI.area_light((-1.0, -1.6, 1.9), (-0.4, 0.8, 0.9), 60, 1.0, (1.0, 0.92, 0.82))
    for i, (x, z) in enumerate(((1.35, 0.4), (1.55, 0.75), (1.75, 1.1), (1.95, 1.45))):   # companionway steps
        C.obj(f'step{i}', C.rbox(f'step{i}', (0.5, 0.22, 0.04), 0.01, 2), M['teak'], (x - 0.25, 0.05, z))
    K.camera((0.75, -1.25, 1.4), (-0.35, 0.95, 1.0), 26)
    labels = [((0.15, 1.15, 1.53), 'CO alarm', 'red'), ((-0.8, 0.53, 0.66), 'gas valve OFF', 'blue')]
    note = 'No smell, nobody ill yet: everyone out into fresh air'; expo = 0.6

elif FIG == 4:
    # abandon ship: wind from the east, the raft launched to leeward (west) on its painter from the stern cleat,
    # the canister on the pushpit rail, the grab bag on the cockpit seat
    K.day_sky(sun_az=210, sun_el=30)
    K.sea('breeze', repeat=10)
    y = K.load_yacht(name='you').place(0, 0, heading=0)                   # head north, beam to the east wind: port is leeward
    root, objs = K.load_model('liferaft-canister.glb', drop_planes=False)
    bpy.context.view_layer.update(); vis = [o for o in objs if o.type == 'MESH' and not o.hide_render]; lo, hi = K.bbox(vis)
    k = 1.05 / max(hi.x - lo.x, hi.y - lo.y); root.scale = (k,) * 3
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    seat = y.world((-3.25, 0.13, 3.82))
    root.location = (root.location.x + seat.x - (lo.x + hi.x) / 2, root.location.y + seat.y - (lo.y + hi.y) / 2, root.location.z + seat.z - lo.z)
    root.rotation_euler = (0, 0, 0)
    # the inflated raft: two orange buoyancy tubes, a dark floor, an arch and a canopy, a boarding ladder
    orange = C.simple('raft-orange', '#b02e00', 0.7); dark = C.simple('raft-floor', '#202428', 0.8)
    rc = Vector((-6.6, -3.0, 0.0))
    torus('raft-tube-lo', 1.05, 0.17, orange, rc + Vector((0, 0, 0.12))); torus('raft-tube-hi', 1.05, 0.17, orange, rc + Vector((0, 0, 0.44)))
    C.cyl('raft-floor', 1.0, 1.0, 0.05, 48, dark, rc + Vector((0, 0, 0.02)))
    arch = C.obj('raft-arch', KI._torus(0.95, 0.07), orange, rc + Vector((0, 0, 0.6))); arch.rotation_euler = (deg(90), 0, deg(20))
    can = sphere('raft-canopy', 1.0, C.simple('raft-canopy', '#b83800', 0.8), rc + Vector((0, 0, 0.55)), (0.96, 0.96, 0.62), 48)
    bm = bmesh.new(); bm.from_mesh(can.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 0.0 or (v.co.x > 0.55 and v.co.z < 0.65)], context='VERTS'); bm.to_mesh(can.data); bm.free()
    C.obj('raft-band', KI._torus(1.06, 0.03), C.simple('reflective', '#e8ecef', 0.2, 0.6), rc + Vector((0, 0, 0.62)))
    # the painter: from the stern cleat on the port quarter, slack across the water to the raft
    cleat = y.world((-2.9, 1.65, 3.62))
    p_end = rc + Vector((0.95, 0.35, 0.45))
    d = (p_end - cleat); d.z = 0; L = d.length; d.normalize(); side = Vector((-d.y, d.x, 0))
    pts = [cleat, cleat + d * 0.3 + Vector((0, 0, 0.08)), cleat + d * 0.55 + Vector((0, 0, -0.5)), cleat + d * 0.75 + Vector((0, 0, -1.2))]
    w = cleat + d * 1.0; w.z = 0.03; pts.append(w)                         # into the water off the quarter
    for t in (0.2, 0.4, 0.6, 0.8):                                         # floating in a slack curve to the raft
        q = w.lerp(p_end, t) + side * math.sin(t * math.pi) * 0.6; q.z = 0.03; pts.append(q)
    q = p_end.copy(); q.z = 0.06; pts += [q - d * 0.15, p_end]
    line('painter', pts, R=0.016, base='#f0ede4', fleck='#c4161c')
    # the grab bag on the cockpit seat: a yellow drybag with a black roll top
    bag = sphere('grab-bag', 0.22, C.simple('grab-yellow', '#f2c200', 0.5, coat=0.2), y.world((-1.9, 0.9, 4.18)), (1.0, 0.75, 1.25))
    C.cyl('grab-top', 0.12, 0.12, 0.08, 24, C.simple('grab-black', '#111214', 0.6), y.world((-1.9, 0.9, 4.47)))
    eye = y.world((-13.5, 9.5, 7.5)); look = y.world((-3.6, 3.6, 2.2))
    K.camera(tuple(eye), tuple(look), 28)
    labels = [(tuple(rc + Vector((0, 0, 1.55))), 'liferaft · painter made fast', 'red'), (tuple(y.world((-1.9, 0.9, 4.75))), 'grab bag', 'blue')]
    w0, w1 = rc + Vector((4.5, -7.5, 0.8)), rc + Vector((0.2, -5.6, 0.8)); arrows = [(tuple(w0), tuple(w1), 'blue')]; labels.append((tuple(w0 + Vector((0, 0, 1.0))), 'Wind', 'blue'))
    note = 'Launch to leeward, pull the painter'; expo = -0.5

elif FIG == 5:
    # a beach with swimmers inside a buoyed swim zone, a tender going dead slow towards it, our yacht 300 m off
    K.day_sky(sun_az=215, sun_el=42)
    KW.terrain(-420, 420, -60, 900, step=4.0)
    K.sea('calm', size=30.0, res=9, repeat=24, center=(0, -60))
    for o in bpy.data.objects:
        if o.name.startswith('ocean'): o.data.materials.clear(); o.data.materials.append(KW.bay_sea_mat())
    sy = KW.shore_y(0)
    # swim zone: yellow buoys along the outer line, a faint red tint over the water inside
    ybuoy = C.simple('swim-buoy', '#f2b800', 0.45, coat=0.5)
    zone = [(-90, sy - 55), (90, sy - 55)]
    for i in range(10):
        x = -90 + i * 20; sphere(f'swim-buoy{i}', 0.45, ybuoy, (x, sy - 55, 0.15))
    for x in (-90, 90):
        for j in range(1, 3): sphere(f'swim-side{x}{j}', 0.45, ybuoy, (x, sy - 55 + j * 18, 0.15))
    tint = C.new_mat('swim-zone')[0]; nt = tint.node_tree; nt.nodes.clear()
    o_ = nt.nodes.new('ShaderNodeOutputMaterial'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); em = nt.nodes.new('ShaderNodeEmission'); mx = nt.nodes.new('ShaderNodeMixShader')
    em.inputs['Color'].default_value = (1, 0.15, 0.1, 1); em.inputs['Strength'].default_value = 0.6; mx.inputs['Fac'].default_value = 0.16
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o_.inputs['Surface'])
    zm = bpy.data.meshes.new('zone'); zm.from_pydata([(-90, sy - 55, 0.25), (90, sy - 55, 0.25), (90, sy - 2, 0.25), (-90, sy - 2, 0.25)], [], [(0, 1, 2, 3)])
    zo = C.obj('swim-zone', zm, tint); zo.visible_shadow = False
    # swimmers: heads in the water with a ripple ring, a few standing in the shallows
    random.seed(5); skin = C.simple('skin', '#c48a62', 0.5); caps = [C.simple(f'cap{i}', c, 0.4) for i, c in enumerate(('#e8463a', '#2a6ad1', '#f1f0ea', '#f2c200'))]
    foam = C.simple('ripple', '#eef3f4', 0.6)
    for i in range(16):
        x, yy = random.uniform(-75, 75), sy - random.uniform(10, 48)
        sphere(f'head{i}', 0.3, random.choice(caps), (x, yy, 0.15))
        r = torus(f'ripple{i}', 0.9, 0.08, foam, (x, yy, 0.05)); r.scale = (1, 1, 0.3)
    for i in range(6):
        x, yy = random.uniform(-70, 70), sy - random.uniform(1, 6)
        C.cyl(f'body{i}', 0.17, 0.14, 1.0, 12, skin, (x, yy, 0.5)); sphere(f'bhead{i}', 0.12, skin, (x, yy, 1.12))
    # the tender heading in dead slow, a small wake; our yacht anchored 300 m off
    root, objs = K.load_model('tender-rib.glb'); bpy.context.view_layer.update()
    vis = [o for o in objs if o.type == 'MESH' and not o.hide_render]; lo, hi = K.bbox(vis)
    root.rotation_euler = (0, 0, deg(90) if (hi.x - lo.x) > (hi.y - lo.y) else 0)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    tx, ty = 55, sy - 110
    root.location = (root.location.x + tx - (lo.x + hi.x) / 2, root.location.y + ty - (lo.y + hi.y) / 2, root.location.z - lo.z - 0.25)
    wk = bpy.data.meshes.new('tender-wake'); wk.from_pydata([(tx - 0.8, ty - 2.0, 0.05), (tx + 0.8, ty - 2.0, 0.05), (tx + 2.4, ty - 12, 0.05), (tx - 2.4, ty - 12, 0.05)], [], [(0, 1, 2, 3)])
    wm = C.new_mat('tender-wake')[0]; nt = wm.node_tree; nt.nodes.clear(); o_ = nt.nodes.new('ShaderNodeOutputMaterial')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); bd = nt.nodes.new('ShaderNodeBsdfDiffuse'); bd.inputs['Color'].default_value = (0.9, 0.93, 0.94, 1)
    mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 0.35
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(bd.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o_.inputs['Surface'])
    C.obj('tender-wake', wk, wm)
    yt = K.load_yacht(name='anchored').place(60, sy - 300, heading=200)
    KW.camera((135, sy - 430, 48), (0, sy - 90, 0), lens=40)
    labels = [((-45, sy - 30, 2.5), 'swimmers', 'red'), ((tx, ty, 3.5), 'tender: dead slow', 'blue'), (tuple(yt.world((K.MAST.x, K.MAST.y, 18.0))), 'Y · your yacht', 'blue')]
    note = 'Y: your yacht, 300 m off the beach'; expo = -0.7

elif FIG == 6:
    # grey dawn, NW 7: from the quay, yachts stern-to with doubled lines, inside the harbour calm,
    # beyond the mole the sea white and breaking
    cloud_sky(zenith='#4f5862', horizon='#a49c90', dark='#4a5059', light='#7b8189', cover=0.95, sharp=0.35, scale=1.5,
              sun=(110, 8, 0.8), strength=1.0, haze=0.12, shade_scale=1.8)
    # outside: a fresh, foaming sea beyond the mole (north); inside: a flat harbour plane
    sea = K.sea(wind=18.0, wave_scale=1.3, chop=2.1, size=60.0, res=11, repeat=9, center=(0, 400), color='#26383d')
    sea.modifiers['ocean'].foam_coverage = 0.6
    hm = bpy.data.meshes.new('harbour'); hm.from_pydata([(-200, -60, 0.02), (200, -60, 0.02), (200, 128, 0.02), (-200, 128, 0.02)], [], [(0, 1, 2, 3)])
    C.obj('harbour-water', hm, K.sea_mat('#1e3036', False))
    KW.mole((-200, 135), (60, 135), width=10.0, height_=3.2)
    # the quay along the south, bollards, and three yachts stern-to with doubled stern lines
    quay = C.obj('quay', C.rbox('quay', (200, 30, 3.0), 0.2, 2), C.concrete_mat('quay-concrete'), (0, -75, 0.0))
    iron = C.simple('bollard-iron', '#141416', 0.5, 0.4)
    y0 = K.load_yacht(name='berth0')
    roots = [y0.root, dup(y0, 'berth1'), dup(y0, 'berth2')]
    xs = (-10.0, -4.8, 0.4)
    stern_from_mast = 3.8 + K.MAST.x               # mast to transom along the boat
    for r, x in zip(roots, xs):
        place_root(r, x, -60 + 2.5 + stern_from_mast, 0)       # bow out (north), transom 2.5 m off the quay edge
    bpy.context.view_layer.update()
    for i, x in enumerate(xs):
        for side in (-1, 1):
            bx = x + side * 1.6
            C.cyl(f'bollard{i}{side}', 0.14, 0.14, 0.35, 20, iron, (bx, -61.2, 1.67))
            st = Vector((x + side * 1.45, -60 + 2.6, 1.55))         # stern cleats near the transom corners
            for k, dx in enumerate((-0.05, 0.05)):                   # doubled: two lines to each bollard
                line(f'stern{i}{side}{k}', sag(st + Vector((dx, 0, 0)), Vector((bx + dx * 0.6, -61.15, 1.75)), 8, 0.12), R=0.009, base='#e9e6dc', fleck='#1f3f78')
    KW.camera((-17.0, -82.0, 13.0), (-6.0, 20.0, -14.0), lens=30)
    labels = [((-60, 150, 9.0), 'NW 7 outside', 'red'), ((-5.0, -40.0, 9.0), 'stay in harbour', 'blue'), ((-10.0, -60.5, 2.6), 'doubled lines')]
    note = 'Tomorrow: NW F7 from dawn, all day'; expo = 0.9

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
