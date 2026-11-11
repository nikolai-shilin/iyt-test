# Article figures, bareboat-skipper / buoyage, figures 8-14, rendered in Blender:
#   8  isolated danger mark (black, red band, two black balls, Fl(2))
#   9  safe water mark (red and white vertical stripes, red ball)
#   10 special mark (yellow, yellow X)
#   11 emergency wreck marking (blue and yellow vertical stripes, yellow cross)
#   12 light characteristics: three lights on a coast at dusk, seen from our foredeck
#   13 leading lights at night: front low, rear high, the front showing left of the rear (steer to port)
#   14 a power-driven vessel bow-on at night: masthead white over both sidelights
# The marks re-use the photo-scanned Poly Haven lateral marker: its red paint is repainted in the mark's colours
# (the scan's dirt and wear kept), its own grey metalwork left as it is, and the right topmark added on top.
#   blender --background --factory-startup --python docs/design/blender/art_buoyage_b.py -- --fig 8 [--out x.jpg]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_night as N
from common import node, link, setin, math_, mixc, lin

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'buoyage')
arg = C.cli(); FIG = arg('--fig', 8); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(ART, f'{FIG}-3d.jpg'))
def deg(a): return math.radians(a)

PAINT = {'black': '#141516', 'red': '#b5141b', 'white': '#e9e7e1', 'yellow': '#c99a00', 'blue': '#1a4c9e'}

# ---------- the marks ----------
def repaint(objs, kind, z0, z1):
    """Repaint the scan's red paint by the mark's pattern. Pattern in object space: z for bands, the angle round
    the axis for vertical stripes. The scan's red channel keeps its wear and dirt as a brightness factor."""
    for o in objs:
        if o.type != 'MESH': continue
        for sl in o.material_slots:
            m = sl.material.copy(); sl.material = m; nt = m.node_tree
            b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            if not b.inputs['Base Color'].is_linked: continue
            src = b.inputs['Base Color'].links[0].from_socket
            sp = node(nt, 'ShaderNodeSeparateColor'); link(nt, src, sp.inputs['Color'])
            R, G = sp.outputs[0], sp.outputs[1]
            red = node(nt, 'ShaderNodeMapRange', in_From_Min=0.07, in_From_Max=0.16); link(nt, math_(nt, 'SUBTRACT', R, G), red.inputs['Value'])
            wear = node(nt, 'ShaderNodeMapRange', in_From_Min=0.15, in_From_Max=0.85, in_To_Min=0.62, in_To_Max=1.0); link(nt, R, wear.inputs['Value'])
            oc = node(nt, 'ShaderNodeTexCoord').outputs['Object']; xyz = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, xyz.inputs['Vector'])
            h = math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', xyz.outputs['Z'], z0), z1 - z0)        # 0 at the waterline, 1 at the top
            ang = math_(nt, 'ARCTAN2', xyz.outputs['Y'], xyz.outputs['X'])
            stripe = math_(nt, 'LESS_THAN', math_(nt, 'FLOORED_MODULO', math_(nt, 'FLOOR', math_(nt, 'MULTIPLY', ang, 8 / math.tau)), 2.0), 0.5)
            P = {k: lin(v) for k, v in PAINT.items()}
            if kind == 'iso':        # black, one broad red band across the middle
                band = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', h, 0.30), math_(nt, 'LESS_THAN', h, 0.55))
                col = mixc(nt, band, P['black'], P['red'])
            elif kind == 'safe':
                col = mixc(nt, stripe, P['white'], P['red'])
            elif kind == 'wreck':
                col = mixc(nt, stripe, P['yellow'], P['blue'])
            else:
                col = mixc(nt, 0.0, P['yellow'], P['yellow'])
            worn = mixc(nt, 1.0, col, (1, 1, 1, 1), 'MULTIPLY')
            wf = node(nt, 'ShaderNodeCombineColor'); [link(nt, wear.outputs['Result'], wf.inputs[i]) for i in range(3)]
            worn = mixc(nt, 1.0, col, wf.outputs['Color'], 'MULTIPLY')
            if kind in ('special', 'wreck'): worn = mixc(nt, 0.55, worn, col)   # keep yellow clean: dirt turns it to tan
            link(nt, mixc(nt, red.outputs['Result'], src, worn), b.inputs['Base Color'])
            if kind == 'iso':        # black paint is a little glossier than the scan's red
                rr = node(nt, 'ShaderNodeMix', data_type='FLOAT'); link(nt, red.outputs['Result'], rr.inputs['Factor'])
                if b.inputs['Roughness'].is_linked: link(nt, b.inputs['Roughness'].links[0].from_socket, rr.inputs[2])
                else: setin(rr, 2, b.inputs['Roughness'].default_value)
                setin(rr, 3, 0.45); link(nt, rr.outputs[0], b.inputs['Roughness'])

def sphere(name, r, mat, loc):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return C.obj(name, me, mat, Vector(loc))

def bar(name, dims, mat, loc, rot):
    o = C.obj(name, C.rbox(name, dims, min(dims) * 0.25, 2), mat, Vector(loc)); o.rotation_euler = rot; return o

def mark(kind, at=(0, 0), heading=0.0):
    """One IALA mark at `at` (x, y), the sea at z 0. Returns (root, top of the topmark, light position)."""
    coll, objs = K.import_glb(os.path.join(K.MODELS, 'buoy-lateral-red', 'lateral_sea_marker.gltf'))
    root = bpy.data.objects.new('mark-' + kind, None); C.col.objects.link(root)
    for o in objs:
        if o.parent is None: o.parent = root
    bpy.context.view_layer.update(); lo, hi = K.bbox(objs)
    repaint(objs, kind, 0.0, hi.z)
    top = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))
    M = K.mats(); paint = {k: C.simple('tm-' + k, v, 0.35, coat=0.6) for k, v in PAINT.items()}
    post = C.cyl('topmark-post', 0.035, 0.035, 1.5, 12, M['black'], top + Vector((0, 0, 0.55))); post.parent = root
    parts = [post]
    if kind == 'iso':            # two black balls, one above the other
        parts += [sphere('ball', 0.3, paint['black'], top + Vector((0, 0, 0.75))), sphere('ball', 0.3, paint['black'], top + Vector((0, 0, 1.45)))]
    elif kind == 'safe':         # one red ball
        parts += [sphere('ball', 0.33, paint['red'], top + Vector((0, 0, 1.1)))]
    elif kind == 'special':      # a yellow X, in two planes so it reads from any side
        c = top + Vector((0, 0, 1.15))
        for spin in (0, 90):
            for tilt in (45, -45): parts.append(bar('x-arm', (0.11, 0.06, 0.95), paint['yellow'], c, (0, deg(tilt), deg(spin))))
    else:                        # wreck: an upright yellow cross
        c = top + Vector((0, 0, 1.0))
        for spin in (0, 90):
            parts.append(bar('cross-v', (0.11, 0.06, 1.05), paint['yellow'], c + Vector((0, 0, 0.05)), (0, 0, deg(spin))))
            parts.append(bar('cross-h', (0.7, 0.06, 0.11), paint['yellow'], c + Vector((0, 0, 0.2)), (0, 0, deg(spin))))
    for p in parts: p.parent = root
    light = top + Vector((0, 0, -0.32))
    root.location = (at[0], at[1], 0.0); root.rotation_euler = (0, 0, deg(heading))
    bpy.context.view_layer.update()
    return root, root.matrix_world @ (top + Vector((0, 0, 2.0))), root.matrix_world @ light

def foredeck(y, look_at, lens):
    """Our bow, standing at the starboard side of the pulpit, looking at a point on the starboard bow: the
    pulpit rail at the bottom of the frame, the furled genoa out of the way to the left."""
    eye = y.world((9.0, -0.85, 5.15))
    return K.camera(eye, look_at, lens)

def sea_day():
    K.sea('breeze', size=40.0, repeat=10)

def dim_coast_fog(strength):
    m = bpy.data.materials.get('coast')
    if m:
        for n in m.node_tree.nodes:
            if n.type == 'EMISSION': n.inputs['Strength'].default_value = strength

# ---------- lighthouses and beacons ----------
def dark_beach(strength=0.12):
    """The coast's pale beach band lights up under the moon: darken it for the night figures."""
    m = bpy.data.materials.get('coast')
    for n in m.node_tree.nodes:
        if n.type == 'MIX' and n.data_type == 'RGBA' and not n.inputs[7].is_linked:
            c = n.inputs[7].default_value
            if c[0] > 0.5 and c[1] > 0.5: n.inputs[7].default_value = (c[0] * strength, c[1] * strength, c[2] * strength, 1)

def ground_z(x, y):
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((x, y, 2000)), Vector((0, 0, -1)))
    return loc.z if hit else 0.0

def lamp(name, p, color='white', strength=40.0, r=0.9):
    o = K.nav_light(name, p, color, power=2.0e4, radius=r)
    for n in o.active_material.node_tree.nodes:
        if n.type == 'EMISSION': n.inputs['Strength'].default_value = strength
    return o

def lighthouse(x, y, tower=24.0, light_h=None):
    """A white masonry tower with a black lantern and gallery, standing on the land at (x, y). Returns the lamp
    position. light_h: the light's height above the sea (the tower is raised on the cliff to reach it)."""
    g = ground_z(x, y); M = K.mats()
    white = C.simple('lighthouse-white', '#d9d6cc', 0.75); black = C.simple('lantern-black', '#1a1b1d', 0.5)
    C.lathe('tower', [(0, 0), (2.6, 0), (2.4, 0.4), (1.7, tower), (2.1, tower + 0.2), (2.1, tower + 0.6), (0, tower + 0.6)], 48, white).location = (x, y, g - 0.5)
    C.cyl('lantern', 1.3, 1.3, 2.6, 24, C.simple('lantern-glass', '#2a3036', 0.05, coat=1.0), (x, y, g - 0.5 + tower + 1.9))
    C.cyl('cupola', 1.5, 0.2, 1.4, 24, black, (x, y, g - 0.5 + tower + 3.9))
    return lamp('lighthouse-lamp', (x, y, g - 0.5 + tower + 1.9), r=2.6, strength=80.0)

def beacon(x, y, h=9.0):
    """A small light structure: a white concrete pillar with a lantern on top."""
    g = ground_z(x, y)
    C.cyl('beacon', 1.2, 0.9, h, 24, C.simple('beacon-white', '#d4d1c8', 0.8), (x, y, g + h / 2 - 0.4))
    return lamp('beacon-lamp', (x, y, g + h + 0.4), r=1.9, strength=60.0)

# ---------- the figures ----------
C.reset()
labels, note, extra, expo = [], None, None, -0.7
if FIG in (8, 9, 10, 11):
    kind = {8: 'iso', 9: 'safe', 10: 'special', 11: 'wreck'}[FIG]
    y = K.load_yacht(); y.place(0, 0, heading=0)
    sea_day(); K.day_sky(sun_az=215, sun_el=34)
    K.coast(distance=2600, bearing=345, height=100, town=False)
    at = (6.0, 30.0)
    root, top, lightp = mark(kind, at, heading=20)
    col = {'iso': 'white', 'safe': 'white', 'special': 'yellow', 'wreck': 'yellow'}[kind]
    lamp('mark-light', lightp, col, strength=4.0, r=0.12).parent = None
    foredeck(y, Vector((at[0], at[1], 4.3)), 54)
    text = {'iso': 'Isolated danger · Fl(2)', 'safe': 'Safe water · Iso, Oc or LFl 10s', 'special': 'Special mark · yellow light',
            'wreck': 'New wreck · Al.Bu/Y'}[kind]
    labels = [(tuple(top + Vector((0, 0, 0.2))), text)]
    note = {'iso': 'A small danger with safe water all round it', 'safe': 'Safe water all round: the landfall or mid-channel',
            'special': 'Marks a zone or a feature, not a channel: read the chart', 'wreck': 'A wreck too new to be on the chart yet'}[kind]
elif FIG == 12:
    y = K.load_yacht(); y.place(0, 0, heading=0)
    K.sea('calm', size=40.0, repeat=10, color='#0a1a24'); K.day_sky(sun_az=280, sun_el=-2.5, strength=0.35)
    K.coast(distance=1500, bearing=0, height=120, town=False, color='#3e4636'); dim_coast_fog(0.02)
    bpy.context.view_layer.update()
    shore = lambda x: 1500 + 60
    L1 = beacon(-560, shore(-560) + 40, 10.0)
    L2 = lighthouse(60, shore(60) + 110, tower=26.0)
    L3 = beacon(600, shore(600) + 30, 12.0)
    K.camera(y.world((9.0, -0.85, 5.15)), Vector((40, 1500, 40)), 32)
    up = Vector((0, 0, 30))
    labels = [(tuple(L1.location + up), 'Fl 5s'), (tuple(L2.location + up), 'Fl(3) 15s 49m 22M', 'blue'), (tuple(L3.location + up), 'Oc 4s')]
    note = 'Dusk · time each light to name it'; extra = {'bloom': 1.0}; expo = 0.6
elif FIG == 13:
    y = K.load_yacht(); y.place(140, 0, heading=0)
    N.night_scene('calm'); N.cloth_furled(y)
    K.coast(distance=1150, bearing=0, height=40, town=False, color='#262b22'); dim_coast_fog(0.0); dark_beach()
    bpy.context.view_layer.update()
    gz = ground_z(0, 1190)
    front = lamp('front', (0, 1190, gz + 4.0), r=0.9, strength=45.0)
    eye = y.world((9.0, -0.85, 5.15)); rz = max(ground_z(0, 1420) + 14.0, gz + 4.0 + 34.0)
    dg = bpy.context.evaluated_depsgraph_get()
    for _ in range(40):                 # raise the rear light until nothing on the land hides it from us
        tgt = Vector((0, 1420, rz)); d = tgt - eye
        hit, loc, *_ = bpy.context.scene.ray_cast(dg, eye, d.normalized(), distance=d.length - 2.0)
        if not hit: break
        rz += 4.0
    print('REAR z', round(rz, 1), 'front z', round(gz + 4.0, 1))
    rear = lamp('rear', (0, 1420, rz), r=1.0, strength=45.0)
    for i, (x, yy) in enumerate(((-420, 1190), (-380, 1215), (360, 1200), (520, 1240), (-610, 1260))):   # a few house lights along the shore
        lamp(f'house{i}', (x, yy, ground_z(x, yy) + 3.0), 'yellow', strength=8.0, r=0.5)
    N.foredeck_camera(y, bearing=-6.5, lens=60, eye=(9.0, -0.85, 5.15), pitch=0.6)
    labels = [(tuple(front.location + Vector((-60, 0, 2))), 'front, low'), (tuple(rear.location + Vector((0, 0, 12))), 'rear, high')]
    note = 'Front light left of the rear: steer to port'; extra = {'bloom': 1.0}; expo = 0.75
else:  # 14
    y = K.load_yacht(); y.place(0, 0, heading=0)
    N.night_scene('calm'); N.our_lights(y, steaming=True, power=0.5); N.cloth_furled(y)
    bow = y.world((10.5, 0.13, 2.0))
    L = N.ship(N.at_bearing(bow, 6, 140), heading=186, lights=('masthead', 'red', 'green'))
    N.foredeck_camera(y, bearing=4.0, lens=26, eye=(9.0, -0.85, 5.15), pitch=-6.0)
    labels = [(tuple(L['masthead'] + Vector((0, 0, 1.4))), 'white over red and green')]
    note = 'Power, bow on: white over both sidelights'; extra = {'bloom': 1.0}; expo = 0.75
C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', extra=extra)
