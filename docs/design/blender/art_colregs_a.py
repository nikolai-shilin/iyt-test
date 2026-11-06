# Article bareboat-skipper/colregs, figures 1-7: the encounters, as Blender renders.
#   1  risk of collision: from our side deck, a ship on a steady bearing 050° relative, crossing to port
#   2  sail meets sail, opposite tacks (wind N): you on port tack keep clear
#   3  sail meets sail, same tack (wind 150°): you are to windward, keep clear
#   4  overtaking   5  head-on   6  crossing, she is to starboard   7  crossing, she is to port
# Positions follow the schematic in article-figures.html ('bareboat-skipper/colregs'): the same relative bearings and
# headings; drone views shrink the distances (x SHRINK) so both boats read in one frame.
#   blender --background --factory-startup --python docs/design/blender/art_colregs_a.py -- --fig 2 [--out x.jpg]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C, kit as K

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'colregs')
arg = C.cli(); FIG = arg('--fig', 2); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(OUTDIR, f'{FIG}-3d.jpg'))
SHRINK = 0.18

def pos(hdg, rel, d):
    a = math.radians(hdg + rel); return (d * math.sin(a), d * math.cos(a))

labels, arrows = [], []
def label_on(y, text, color='blue', h=19.0):
    labels.append((tuple(y.world((K.MAST.x, K.MAST.y, h + K.WL))), text, color))

def wind_arrow(c, frm, D, az):
    """A blue wind arrow blowing from compass `frm`, set to the right of the boats as the camera (on bearing az from
    them) sees it, clear of the pills and the note."""
    a = math.radians(frm); u = Vector((math.sin(a), math.cos(a), 0))
    r = math.radians(az + 90); right = Vector((-math.sin(r), -math.cos(r), 0))
    fwd = Vector((-math.sin(math.radians(az)), -math.cos(math.radians(az)), 0))
    mid = Vector((c.x, c.y, 8.0)) + right * 1.05 * D + fwd * 0.35 * D; p0 = mid + u * 0.28 * D; p1 = mid - u * 0.28 * D
    arrows.append((tuple(p0), tuple(p1), 'blue')); labels.append((tuple(p0 + Vector((0, 0, 2))), 'Wind', 'blue'))

def drone(c, D, az=180.0, el=37.0, k=2.5, lens=32.0):
    """Camera k*D from the centre c, on compass bearing az from it, el degrees up, looking at c."""
    a, e = math.radians(az), math.radians(el); dist = k * D
    eye = c + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * dist
    K.camera(tuple(eye), tuple(c), lens)

def sailing(name, hdg, wind, x, y):
    """A yacht under sail, sails and heel set from the wind's side: boom to leeward, genoa on the leeward side."""
    rel = ((wind - hdg + 540) % 360) - 180          # wind relative to the bow: + from starboard
    stbd = rel > 0; off = abs(rel)
    boom = 10 if off < 60 else (35 if off < 120 else 60)
    yt = K.load_yacht(name=name, sails={'main': True, 'genoa': 'port' if stbd else 'starboard', 'boom': boom if stbd else -boom})
    return yt.place(x, y, heading=hdg, heel=(-12 if stbd else 12) if off < 120 else (-5 if stbd else 5))

def motoring(name, hdg, x, y):
    return K.load_yacht(name=name).place(x, y, heading=hdg)

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

C.reset()
note = None
if FIG == 1:
    you = K.load_yacht(name='you').place(0, 0, heading=0)
    K.sea('breeze'); K.day_sky(sun_az=210, sun_el=35)
    root, objs = K.load_model('vessel-ferry.glb')
    bpy.context.view_layer.update()
    vis = [o for o in objs if o.type == 'MESH' and not o.hide_render]
    lo, hi = K.bbox(vis)
    root.scale = (1.5,) * 3                         # the 57 m ferry made an 85 m coaster
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    sx, sy = pos(0, 50, 330)                        # her bearing 050° relative; shortened from 600 m to read
    root.location = (sx - (lo.x + hi.x) / 2, sy - (lo.y + hi.y) / 2, -lo.z - 1.6)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    # from our starboard side deck by the shrouds, looking along her bearing over the bow
    # from the starboard wheel, looking 32° to starboard: the bow and pulpit on the left, the ship on the right
    d = Vector((math.cos(math.radians(32)), -math.sin(math.radians(32)), 0))      # model space: x fwd, y port
    eye = you.world((-2.4, -0.9, 5.1)); look = you.world(tuple(Vector((-2.4, -0.9, 3.4)) + d * 60))
    K.camera(tuple(eye), tuple(look), 24)
    labels = [(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z + 4), 'Ship')]
    note = 'Bearing steady, range closing'
else:
    K.sea('breeze', size=40.0, repeat=12); K.day_sky(sun_az=200, sun_el=48)
    if FIG == 2:     # wind N; you port tack 045; she starboard tack 315 at rel 255°, 260 m
        ox, oy = pos(45, 255, 260 * SHRINK)
        you = sailing('you', 45, 0, 0, 0); oth = sailing('other', 315, 0, ox, oy)
        wind = 0; note = 'Opposite tacks · you are on port: keep clear'
    elif FIG == 3:   # wind 150°; both 060; she at rel -80°, 240 m
        ox, oy = pos(60, -80, 240 * SHRINK)
        you = sailing('you', 60, 150, 0, 0); oth = sailing('other', 60, 150, ox, oy)
        wind = 150; note = 'Same tack · you are to windward: keep clear'
    elif FIG == 4:   # she is ahead at rel 5°, 320 m, heading 000; you come up from astern
        ox, oy = pos(0, 5, 320 * SHRINK)
        you = motoring('you', 0, 0, 0); oth = motoring('other', 0, ox, oy)
        wind = None; note = 'Overtaking · you keep clear'
    elif FIG == 5:   # head-on, 400 m
        ox, oy = pos(0, 0, 400 * SHRINK)
        you = motoring('you', 0, 0, 0); oth = motoring('other', 180, ox, oy)
        wind = None; note = 'Head-on · both turn to starboard'
    elif FIG == 6:   # crossing, she is to starboard: rel 50°, 380 m, heading 270
        ox, oy = pos(0, 50, 380 * SHRINK)
        you = motoring('you', 0, 0, 0); oth = motoring('other', 270, ox, oy)
        wind = None; note = 'She is to starboard · you give way'
    else:            # crossing, she is to port: rel -50°, 360 m, heading 080
        ox, oy = pos(0, -50, 360 * SHRINK)
        you = motoring('you', 0, 0, 0); oth = motoring('other', 80, ox, oy)
        wind = None; note = 'She is to port · you stand on'
    for yt in (you, oth): K.wake(yt, 28 if wind is not None else 45, 8, 0.9 if wind is not None else 1.3)
    c = Vector((ox / 2, oy / 2, 0.0)); D = max(Vector((ox, oy)).length, 40.0)
    view = {2: (180, 40), 3: (240, 40), 4: (250, 34), 5: (240, 36), 6: (200, 40), 7: (160, 40)}[FIG]
    drone(c, D, az=view[0], el=view[1], k=2.6)
    label_on(you, 'You'); label_on(oth, 'Other', color=None)
    if wind is not None: wind_arrow(c, wind, D, view[0])
labels = [l if len(l) < 3 or l[2] else l[:2] for l in labels]
C.render(OUT, SAMPLES, SCALE, -0.7, labels, note, space='blender', arrows=arrows)
