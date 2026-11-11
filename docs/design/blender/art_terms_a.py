# Article bareboat-skipper/terms, figures 1-4: the names on board, labelled on our real yacht (the Sun Odyssey 49DS).
#   1  directions on board: top-down drone view, the boat motoring north, the directions round her
#   2  hull and deck: a waterline cut-away seen broadside, keel and rudder under water, draft and freeboard measured
#   3  the rig: broadside under main and jib
#   4  sails and their lines: the mainsail close, battens and a row of reef points added
#   blender --background --factory-startup --python docs/design/blender/art_terms_a.py -- --fig 1 [--out x.jpg]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C, kit as K, kit_world as KW

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'terms')
arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(OUTDIR, f'{FIG}-3d.jpg'))

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

def flat(name, color, rough=0.5, metal=0.0):
    return C.simple(name, color, rough, metal)

def hits(y_from, pts, toward=1):
    """Each world point pushed onto the first surface met by a ray along +Y (toward=1) from y_from; returns the hits."""
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); out = []
    for p in pts:
        h, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((p.x, y_from, p.z)), Vector((0, toward, 0)))
        out.append(loc if h else None)
    return out

def parts_below(y):
    """The keel and the rudder: the meshes that reach well below the waterline, split fore and aft."""
    bpy.context.view_layer.update(); keel, rud = [], []
    for o in y.objs:
        if o.type != 'MESH' or o.hide_render: continue
        lo, hi = K.bbox([o])
        if lo.z < -0.7 and (hi.y - lo.y) < 0.9 and (hi.x - lo.x) < 4.0:      # a thin fin hanging below the hull
            (keel if (lo.x + hi.x) / 2 > -3.0 else rud).append(o)
    return keel, rud

C.reset()
labels, arrows, note = [], [], None

if FIG == 1:
    y = K.load_yacht(name='yacht').place(0, 0, heading=0)          # mast at the origin, bow north
    K.wake(y, 40, 8, 1.1)
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=200, sun_el=55)
    cy = -1.6                                                      # the boat's middle, a little aft of the mast
    ring = 21.0
    names = [('ahead', 0, 'blue'), ('starboard bow', 45, None), ('abeam', 90, None), ('starboard quarter', 135, None),
             ('astern', 180, None), ('port quarter', 225, None), ('abeam', 270, None), ('port bow', 315, None)]
    for text, b, col in names:
        a = math.radians(b); p = (ring * math.sin(a), cy + ring * math.cos(a) * 1.0, 0.3)
        labels.append((p, text, col) if col else (p, text))
    labels += [((-8.5, cy - 1.0, 0.3), 'PORT', 'red'), ((8.5, cy - 1.0, 0.3), 'STARBOARD', 'green')]
    # dashed bearing lines on the water from the boat out to each name
    m = C.simple('dash-line', '#ffffff', 0.5); dash = C.rbox('dash', (0.9, 0.12, 0.04), 0.02, 2); dash.materials.append(m)
    for _, b, _c in names:
        a = math.radians(b); u = Vector((math.sin(a), math.cos(a), 0))
        for s in [9.0 + k * 1.6 for k in range(6)]:
            o = bpy.data.objects.new('dash', dash); C.col.objects.link(o)
            o.location = Vector((0, cy, 0.18)) + u * s; o.rotation_euler = (0, 0, math.atan2(u.y, u.x))
    K.camera((0.0, cy - 0.01, 90.0), (0.0, cy, 0.0), 38)
    note = 'Named from the boat, facing forward'

elif FIG == 2:
    y = K.load_yacht(name='yacht').place(0, 0, heading=90)         # bow east, starboard side to the camera (-Y)
    KW.antifoul_hull(y)
    keel, rud = parts_below(y)
    klo, khi = K.bbox(keel); rlo, rhi = K.bbox(rud)
    print('KEEL', tuple(round(v, 2) for v in klo), tuple(round(v, 2) for v in khi), 'RUDDER', tuple(round(v, 2) for v in rlo), tuple(round(v, 2) for v in rhi))
    KW.water_body(depth=12.0, size=600.0, density=0.009, color='#16606a', absorb='#3aa39a', reflect=0.25, absorb_density=0.012, center=(0, 0))
    KW.far_sea_ring(inner=300.0)
    KW.seabed(z=-5.0, size=150.0, res=200, center=(0, 20), colors=('#7d8669', '#99a07e', '#8b9274'))
    KW.stones(50, ((-25, 12), (25, 45)), -5.0, scale=(0.15, 0.5))
    KW.seagrass(((-25, 14), (25, 50)), -5.0, clumps=900, length=0.55)
    K.coast(distance=1400, bearing=0, height=80, town=False)
    K.day_sky(sun_az=200, sun_el=50, strength=0.25, haze=2.0)
    bow, stern = y.world((10.85, 0.13, 3.6)), y.world((-3.75, 0.13, 3.4))
    mid_x = (bow.x + stern.x) / 2
    KW.camera(Vector((mid_x, -21.0, 0.002)), Vector((mid_x, 0.0, -0.1)), lens=30)
    near = -3.2                                                    # measuring gauges just outboard of her side
    kx = (klo.x + khi.x) / 2; dz = klo.z
    deck_x = mid_x - 1.5; deck = hits(-12.0, [Vector((deck_x, 0, 1.45))])[0]
    fz = 1.5
    for k in range(40):                                           # the deck edge at deck_x: highest hit on her side
        h = hits(-12.0, [Vector((deck_x, 0, 0.6 + k * 0.03))])[0]
        if h is not None and h.y < -1.0: fz = 0.6 + k * 0.03
    gx = kx - 3.2
    arrows += [((gx, near, dz / 2), (gx, near, 0.0), 'yellow'), ((gx, near, dz / 2), (gx, near, dz), 'yellow'),
               ((deck_x + 2.5, near, fz / 2), (deck_x + 2.5, near, fz), 'blue'), ((deck_x + 2.5, near, fz / 2), (deck_x + 2.5, near, 0.0), 'blue')]
    labels += [((gx + 1.7, near, dz / 2 - 0.3), f'draft {abs(dz):.1f} m'), ((deck_x + 2.5, near, fz + 0.2), f'freeboard {fz:.1f} m', 'blue'),
               ((bow.x - 0.4, -1.0, 2.4), 'bow'), ((stern.x + 0.4, -1.5, 2.3), 'stern'),
               ((mid_x - 2.5, -1.8, 0.9), 'hull'), ((kx + 0.6, -0.6, klo.z + 0.3), 'keel'), (((rlo.x + rhi.x) / 2, -0.4, (rlo.z + rhi.z) / 2), 'rudder'),
               (y.world((10.4, -0.8, 4.35)), 'pulpit'), (y.world((-3.3, -1.2, 4.35)), 'pushpit'), ((stern.x - 2.5, -3.0, 0.05), 'waterline')]
    note = 'Hull and deck'

elif FIG == 3:
    y = K.load_yacht(name='yacht', sails={'main': True, 'genoa': 'starboard', 'boom': -12}).place(0, 0, heading=90, heel=6)
    K.sea('breeze', size=36.0, repeat=10); K.day_sky(sun_az=200, sun_el=45)
    K.coast(distance=1800, bearing=0, height=90, town=False)
    W = lambda p: y.world(p)
    head, mast_mid = W((4.93, 0.13, 20.6)), W((4.93, 0.13, 13.0))
    fs0, fs1 = W((10.62, 0.13, 3.95)), W((5.25, 0.13, 20.1))
    bs0, bs1 = W((-3.7, 0.13, 3.9)), W((4.93, 0.13, 20.6))
    labels = [(tuple(W((4.93, -0.3, 21.4))), 'mast'), (tuple(W((2.0, -0.6, 5.6))), 'boom'), (tuple(W((2.4, -1.0, 9.0))), 'mainsail'),
              (tuple(W((7.4, -1.3, 8.0))), 'jib'), (tuple(fs0.lerp(fs1, 0.6)), 'forestay'), (tuple(bs0.lerp(bs1, 0.72)), 'backstay')]
    c = W((3.4, 0.13, 10.0))
    K.camera((c.x + 1.0, c.y - 42.0, 8.0), (c.x + 1.0, c.y, 10.6), 40)
    note = 'The rig'

else:  # FIG 4
    y = K.load_yacht(name='yacht', sails={'main': True, 'boom': -3}).place(0, 0, heading=90)
    K.sea('calm', size=30.0, repeat=10); K.day_sky(sun_az=210, sun_el=40)
    K.coast(distance=1800, bearing=0, height=90, town=False)
    b = math.radians(-3)
    T = lambda lx, ly, lz: y.world((lx + K.MAST.x, ly + K.MAST.y, lz + K.WL))
    tack, head = T(-0.12, 0.0, 5.5 - K.WL), T(-0.1, 0.0, 20.0 - K.WL)
    clew = T(-5.4 * math.cos(b), 5.4 * math.sin(b), 5.55 - K.WL)
    dark = flat('batten', '#40454b', 0.5); white = flat('reef-tie', '#f2f2ee', 0.6)
    # battens: four, from the leech in towards the luff, pushed onto the sail's camera-facing face
    batten_lines = []
    for v, frac in ((0.24, 0.55), (0.46, 0.7), (0.66, 0.92), (0.84, 0.92)):
        L, R = tack.lerp(head, v), clew.lerp(head, v)
        pts = [R.lerp(L, frac * i / 12) for i in range(13)]
        hp = [h for h in hits(-20.0, pts) if h is not None]
        hp = [h for h in hp if abs(h.y - hp[0].y) < 0.25 and h.x < L.x - 0.12]   # stay on the sail, clear of the mast
        if len(hp) > 3:
            C.tube('batten', [h + Vector((0, -0.035, 0)) for h in hp], 0.055, 8, 1.0, dark); batten_lines.append(hp)
    # reef points: a row of short ties across the lower panel
    v = 0.13; L, R = tack.lerp(head, v), clew.lerp(head, v)
    ties = [h for h in hits(-20.0, [L.lerp(R, 0.08 + 0.84 * i / 9) for i in range(10)]) if h is not None]
    for h in ties:
        C.tube('tie', [h + Vector((0, -0.03, 0.12)), h + Vector((0, -0.08, -0.05)), h + Vector((0, -0.06, -0.25))], 0.02, 6, 1.0, white)
    bpy.context.view_layer.update()
    c = tack.lerp(head, 0.45).lerp(clew.lerp(head, 0.45), 0.5)
    K.camera((c.x, c.y - 27.0, c.z - 1.0), (c.x, c.y, c.z + 0.8), 28)
    mid = lambda a, b2, t: tuple(a.lerp(b2, t))
    bl = batten_lines[1] if len(batten_lines) > 1 else [clew]
    # the sail is narrow on the image, so most pills sit off to the side on a leader (px offsets), clear of each other
    labels = [(tuple(head + Vector((0, -0.3, 0.3))), 'head'), (tuple(tack + Vector((0.2, -0.3, -0.2))), 'tack', None, (165, 0)),
              (tuple(clew + Vector((-0.2, -0.3, -0.2))), 'clew', None, (-200, -30)),
              (mid(tack, head, 0.55), 'luff', None, (170, 0)), (mid(clew, head, 0.58), 'leech', None, (-190, -10)), (mid(tack, clew, 0.5), 'foot', None, (-150, 95)),
              (tuple(bl[2]), 'batten', 'blue', (-210, 55)), (tuple(ties[len(ties) // 2] if ties else tack), 'reef points', 'blue', (-230, -15))]
    note = 'Sails and their lines'

C.render(OUT, SAMPLES, SCALE, -0.7, labels, note, space='blender', arrows=arrows)
