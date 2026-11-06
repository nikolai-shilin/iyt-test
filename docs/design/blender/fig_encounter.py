# Helm-view encounters on our own Sun Odyssey:
#   --kind mob       man overboard on a broad reach: lifebuoy, dan buoy and a life jacket astern to port
#   --kind dayshape  under sail, a fishing vessel ahead to starboard showing two cones apexes together
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C, kit as K

arg = C.cli(); OUT = arg('--out', 'fig-encounter.jpg'); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100); KIND = arg('--kind', 'mob')
C.reset()
labels, arrows = [], []
if KIND == 'mob':
    # broad reach on port tack: wind on the port quarter, boom out to starboard
    y = K.load_yacht(sails={'main': True, 'genoa': 'starboard', 'boom': -55}); y.place(0, 0, heading=0, heel=4)
    K.sea('breeze'); K.day_sky(sun_az=250, sun_el=30)
    # the casualty about 16 m astern on the port quarter: lifebuoy, life jacket, the dan buoy thrown after them
    mob = y.world((-15.0, 5.5, K.WL)); mob.z = 0.0
    lb = K.load_model('lifebuoy.glb')[0]; lb.location = mob + Vector((1.2, -0.8, 0.04))
    K.dan_buoy(tuple(mob + Vector((-2.2, 1.4, 0))))
    lj, ljo = K.import_glb(os.path.join(K.MODELS, 'life-jacket', 'life_jacket.gltf'))
    for o in ljo:
        if o.parent is None: o.location = mob + Vector((0, 0, -0.18)); o.rotation_euler = (math.radians(70), 0, math.radians(30))
    # from the helm, looking aft over the port quarter: the pushpit and transom in the foreground
    eye = y.world((-0.6, 0.9, 5.1)); look = y.world((-15.0, 5.0, -0.8)); K.camera(eye, look, 22)
    labels = [(tuple(mob + Vector((0, 0, 1.3))), 'MOB')]; note = 'Casualty astern to port'
else:
    # close-hauled on starboard tack; the trawler crosses ahead from starboard
    y = K.load_yacht(sails={'main': True, 'genoa': 'port', 'boom': 10}); y.place(0, 0, heading=0, heel=-10)
    K.sea('breeze'); K.day_sky(sun_az=150, sun_el=42)
    root, objs = K.load_model('vessel-trawler.glb')
    M = K.mats()
    meshes = [o for o in objs if o.type == 'MESH' and not o.hide_render]
    lo, hi = K.bbox(meshes); H = hi.z - lo.z; foot = max(hi.x - lo.x, hi.y - lo.y)
    for o in meshes:                               # the slab the model stands on: wide, low, at the bottom
        l, h = K.bbox([o])
        big = max(h.x - l.x, h.y - l.y) > 0.7 * foot and l.z < lo.z + 0.05 * H
        if big and ((h.z - l.z) < 0.12 * H or len(o.data.polygons) <= 40): o.hide_render = True   # flat slab or plain box
    meshes = [o for o in meshes if not o.hide_render]
    lo, hi = K.bbox(meshes); H = hi.z - lo.z
    def rule_obj(o):
        l, h = K.bbox([o])
        return M['navy'] if h.z < lo.z + 0.42 * H else None
    for o in meshes:
        m = rule_obj(o)
        if m: o.data.materials.clear() if False else None; [setattr(sl, 'material', m) for sl in o.material_slots]
    root.rotation_euler = (0, 0, math.radians(-70))
    bpy.context.view_layer.update(); lo, hi = K.bbox(meshes)
    root.location = (root.location.x + 26 - (lo.x + hi.x) / 2, root.location.y + 52 - (lo.y + hi.y) / 2, root.location.z - lo.z - 2.0)
    bpy.context.view_layer.update(); lo, hi = K.bbox(meshes)
    # the mast: the tallest thin part; hoist the shapes on a halyard a little below its top
    mast = max(meshes, key=lambda o: (K.bbox([o])[1].z, -(K.bbox([o])[1] - K.bbox([o])[0]).xy.length))
    ml, mh = K.bbox([mast]); mx = Vector(((ml.x + mh.x) / 2, (ml.y + mh.y) / 2, mh.z))
    K.cone(mx + Vector((0, 0, -1.4)), 0.32, 0.65, up=False); K.cone(mx + Vector((0, 0, -2.1)), 0.32, 0.65, up=True)
    # from the starboard side of the foredeck, clear of our genoa, looking at the trawler on the starboard bow
    eye = y.world((6.0, -1.1, 5.3)); look = y.world((52.0, -22.0, 6.5)); K.camera(eye, look, 42)
    labels = [(tuple(mx + Vector((0, 0, 0.3))), 'two cones')]; note = 'Two cones apexes together: vessel engaged in fishing'
C.render(OUT, SAMPLES, SCALE, -0.7, labels, note, space='blender', arrows=arrows)
