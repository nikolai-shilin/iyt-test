# Article bareboat-skipper/buoyage, figures 1-7: the marks themselves, close up from a dinghy's height.
#   1 port-hand lateral (red can, Fl R)   2 starboard-hand lateral (green cone, Fl G)
#   3-6 north, east, south, west cardinals  7 south cardinal at night, its light lit: Q(6)+LFl 15s
#   blender --background --factory-startup --python docs/design/blender/art_buoyage_a.py -- --fig 3 [--out ...]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C, kit as K

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'buoyage')
arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(ART, f'{FIG}-3d.jpg'))

CARD = {3: ('north', 'North cardinal · Q', 'Cones both up · black over yellow'),
        4: ('east', 'East cardinal · Q(3)', 'Cones base to base · black, yellow, black'),
        5: ('south', 'South cardinal · Q(6)+LFl', 'Cones both down · yellow over black'),
        6: ('west', 'West cardinal · Q(9)', 'Cones point to point · yellow, black, yellow'),
        7: ('south', 'Q(6)+LFl 15s · six quick, one long', 'South cardinal at night')}

def frame(root, objs, dist, lens, eye_h=1.5, side=0.0, aim=0.48):
    """A camera `dist` metres off the mark, at eye height in a dinghy, aimed at the middle of what shows above water."""
    bpy.context.view_layer.update()
    lo, hi = K.bbox([o for o in objs if o.type == 'MESH' and not o.hide_render])
    c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, max(0.0, lo.z)))
    top = hi.z; mid = Vector((c.x, c.y, top * aim))
    eye = Vector((c.x + side, c.y - dist, eye_h))
    K.camera(eye, mid, lens)
    return c, top

def deepen(objs, sat, val, hue=None):
    """The photo-scanned lateral marker is sun-faded: richer, darker paint (adds or retunes a Hue/Saturation node)."""
    seen = set()
    for o in objs:
        for sl in getattr(o, 'material_slots', []):
            m = sl.material
            if not m or m.name in seen or not m.node_tree: continue
            seen.add(m.name); nt = m.node_tree
            b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if not b or not b.inputs['Base Color'].is_linked: continue
            src = b.inputs['Base Color'].links[0].from_node
            hs = src if src.type == 'HUE_SAT' else None
            if hs is None:
                hs = nt.nodes.new('ShaderNodeHueSaturation')
                nt.links.new(b.inputs['Base Color'].links[0].from_socket, hs.inputs['Color']); nt.links.new(hs.outputs['Color'], b.inputs['Base Color'])
            hs.inputs['Saturation'].default_value = sat; hs.inputs['Value'].default_value = val
            if hue is not None: hs.inputs['Hue'].default_value = hue

def paint_cardinal(objs):
    """Real cardinal paint: deep black and signal yellow; drop the white foam disc the author floated round it."""
    black = C.simple('card-black', '#08090a', 0.55, coat=0.15); yellow = C.simple('card-yellow', '#f0b800', 0.5, coat=0.15)
    for o in objs:
        if o.type != 'MESH': continue
        for sl in o.material_slots:
            n = sl.material.name if sl.material else ''
            if n.startswith('Noir'): sl.material = black
            elif n.startswith('Orange'): sl.material = yellow
            elif n.startswith('blanc') and len(o.data.polygons) < 64: o.hide_render = True

C.reset()
labels, note, extra, expo = [], None, None, -0.6
if FIG in (1, 2):
    side = 'port' if FIG == 1 else 'starboard'
    K.day_sky(sun_az=215, sun_el=34)
    K.sea('breeze', size=30.0, repeat=10)
    root, objs = K.lateral_buoy(side, topmark=True, light=True, at=(0, 0))
    if side == 'port': deepen(objs, 1.25, 0.8)
    else: deepen(objs, 1.15, 0.6, 0.83)
    K.coast(distance=1600, bearing=10, height=90, town=True)
    c, top = frame(root, objs, 22.0, 50)
    labels = [((c.x, c.y, top + 0.9), 'Port hand · Fl R' if side == 'port' else 'Starboard hand · Fl G')]
    note = 'Red · can · red light' if side == 'port' else 'Green · cone · green light'
else:
    which, pill, note = CARD[FIG]
    night = FIG == 7
    if night:
        K.night_sky(moon=0.03, stars=True)
        K.sea('calm', size=30.0, repeat=10, color='#050d14', foam=False)
        expo = 1.6; extra = {'bloom': 1.2}
    else:
        K.day_sky(sun_az=230, sun_el=30)
        K.sea('breeze', size=30.0, repeat=10)
        K.coast(distance=2000, bearing=355, height=80, town=False); expo = -1.1
    root, objs = K.cardinal_buoy(which, at=(0, 0), height=4.6)
    paint_cardinal(objs)
    c, top = frame(root, objs, 17.0, 45, aim=0.6)
    if night:   # the light, just under the topmark: lit white
        bpy.context.view_layer.update()
        K.nav_light('card-light', (c.x, c.y, top - 1.25), 'white', power=6.0, radius=0.09)
    labels = [((c.x, c.y, top + 0.35), pill)]
C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', extra=extra)
