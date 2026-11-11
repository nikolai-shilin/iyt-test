# Article bareboat-skipper/buoyage, figures 15-21: navigation and working lights at night, seen from our foredeck.
#   15 sailing vessel bow on: red and green sidelights, no white above them
#   16 sailing yacht under 20 m with a tricolour at the masthead (no deck-level sidelights)
#   17 any vessel seen from astern: one white sternlight, low
#   18 trawling: green over white all-round      19 fishing, not trawling: red over white
#   20 not under command: red over red           21 restricted in ability to manoeuvre: red, white, red
#   blender --background --factory-startup --python docs/design/blender/art_buoyage_c.py -- --fig 18
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Euler
import common as C, kit as K, kit_night as N

arg = C.cli(); FIG = arg('--fig', 15); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100); EXPO = arg('--exposure', 0.75)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = arg('--out', os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'buoyage', f'{FIG}-3d.jpg'))

def deg(a): return math.radians(a)

def work_vessel(pos, heading, stack, keep_booms=False, spacing=1.6):
    """The trawler model, dark, with all-round lights stacked on her mast top-down (colours in `stack`).
    Returns the world positions of the lights, top first."""
    root, objs = K.load_model('vessel-trawler.glb')
    bpy.context.view_layer.update()
    meshes = [o for o in objs if o.type == 'MESH']
    lo, hi = K.bbox(meshes); H = hi.z - lo.z; foot = max(hi.x - lo.x, hi.y - lo.y)
    for o in meshes:
        l, h = K.bbox([o])
        big = max(h.x - l.x, h.y - l.y) > 0.7 * foot and l.z < lo.z + 0.05 * H
        if o.name == 'Geom3D' or (big and ((h.z - l.z) < 0.12 * H or len(o.data.polygons) <= 40)): o.hide_render = True   # the slab
        elif not keep_booms and (h.z - l.z) < 0.4 and max(h.x - l.x, h.y - l.y) > 8 and h.z < 1.0: o.hide_render = True
    dull = C.simple('workboat-night', '#2c3035', 0.6)
    K.recolor(objs, lambda c, n: dull)
    for o in objs:
        if o.type == 'MESH' and not o.data.materials: o.data.materials.append(dull)
    root.location = (pos[0], pos[1], -K.TRAWLER_WL); root.rotation_euler = Euler((0, 0, deg(90 - heading)), 'XYZ')   # her waterline on the sea
    bpy.context.view_layer.update()
    top = root.matrix_world @ Vector((-1.43, 1.3, 8.45 + 0.4 + spacing * (len(stack) - 1) * 0.5))   # clear of her gantry
    out = []
    for i, col in enumerate(stack):
        p = top - Vector((0, 0, spacing * i)) + Vector((0, -0.6, 0))   # on the near side of the mast
        N.light(f'allround-{i}', p, col, strength={'red': 0.9, 'green': 0.5, 'white': 5.0}[col], power=40.0, radius=0.32)
        out.append(p)
    return out

SPECS = {
    15: ('Sail, bow on · sidelights, no white', None),
    16: ('Sail, tricolour · the colours at the masthead', None),
    17: ('From astern · one white light, low', None),
    18: ('Trawling · green over white', ('green', 'white')),
    19: ('Fishing · red over white', ('red', 'white')),
    20: ('Not under command · red over red', ('red', 'red')),
    21: ('Restricted in ability to manoeuvre · red, white, red', ('red', 'white', 'red')),
}
text, stack = SPECS[FIG]

C.reset()
me = K.load_yacht(name='own'); me.place(0, 0, heading=0)
N.night_scene('calm')
N.our_lights(me, steaming=True, power=0.4); N.cloth_furled(me)
bow = me.world((10.5, 0.13, 2.0))

if FIG in (15, 16, 17):
    dist = 70.0 if FIG != 16 else 52.0; p = N.at_bearing(bow, 6, dist)
    if FIG == 17:   # sailing away from us: we see her stern, one white light low on the pushpit
        other = K.load_yacht(name='other', sails={'main': True, 'genoa': 'starboard', 'boom': -20})
        other.place(p.x, p.y + 10, heading=2, heel=4)
        L = N.yacht_lights(other, sidelights=False, stern=True); top = L['stern']
    else:
        other = K.load_yacht(name='other', sails={'main': True, 'genoa': 'starboard', 'boom': -18})
        other.place(p.x, p.y, heading=182, heel=4)
        L = N.yacht_lights(other, sidelights=(FIG == 15))
        if FIG == 16:   # the tricolour lantern at the masthead: red and green sectors side by side (spread a little to read)
            r, g = other.world((5.06, 0.45, 20.75)), other.world((5.06, -0.19, 20.75))
            N.light('tri-red', r, 'red', strength=7.0, power=6.0, radius=0.1); N.light('tri-green', g, 'green', strength=7.0, power=6.0, radius=0.1)
            top = (r + g) / 2
        else:
            top = (L['red'] + L['green']) / 2
    N.cloth_furled(other)
    look = top if FIG != 16 else top - Vector((0, 0, 7.5))
    lens = 35 if FIG != 16 else 40
else:
    p = N.at_bearing(bow, 6, 110.0)
    lights = work_vessel(p, heading=82 if FIG != 20 else 140, stack=stack, keep_booms=(FIG == 18))
    top = lights[0]; look = lights[-1] + Vector((0, 0, -2.0)); lens = 75

# aim the camera from our foredeck at the lights, keeping our own bow lights low in the frame
eye = me.world((7.2, -1.2, 5.1))   # starboard side deck, the forestay off to the left
cd = bpy.data.cameras.new('cam'); cd.lens = lens; cd.clip_end = 3000
cam = bpy.data.objects.new('cam', cd); C.col.objects.link(cam); bpy.context.scene.camera = cam
d = (look - eye).normalized(); d.z -= 0.06
cam.location = eye; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
C.render(OUT, SAMPLES, SCALE, EXPO, [(tuple(top + Vector((0, 0, 1.4 if FIG < 18 else 1.2))), text)], None,
         space='blender', extra={'bloom': 1.0})
