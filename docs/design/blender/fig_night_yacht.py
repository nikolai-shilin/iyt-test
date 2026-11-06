# Night figure: a sailing yacht dead ahead, coming straight at us. Both her sidelights show, red AND green side by
# side, under a dark sail silhouette against the faintly lighter sky. Seen from our foredeck, our own lights on.
#   blender --background --factory-startup --python docs/design/blender/fig_night_yacht.py -- --out .../fig-night-yacht.jpg
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C, kit as K, kit_night as N

arg = C.cli(); OUT = arg('--out', 'fig-night-yacht.jpg'); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
DIST = arg('--dist', 65.0); EXPO = arg('--exposure', 0.75)
C.reset()
me = K.load_yacht(name='own'); me.place(0, 0, heading=0)
N.night_scene('calm')
N.our_lights(me); N.cloth_furled(me)
# the other yacht a little to starboard of dead ahead, heading straight back at us, sailing (main and genoa up)
bow = me.world((10.5, 0.13, 2.0)); p = N.at_bearing(bow, 6, DIST)
other = K.load_yacht(name='other', sails={'main': True, 'genoa': 'starboard', 'boom': -18})
other.place(p.x, p.y, heading=182, heel=4)
L = N.yacht_lights(other, sidelights=True)
N.foredeck_camera(me, bearing=4, lens=24, pitch=-2.0)
mid = (L['red'] + L['green']) / 2
C.render(OUT, SAMPLES, SCALE, EXPO, [(tuple(mid + Vector((0, 0, 1.0))), 'red and green')],
         'Head-on: red and green', space='blender', extra={'bloom': 1.0})
