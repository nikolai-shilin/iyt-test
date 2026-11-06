# Figure type "lights": motoring at night, a vessel's white masthead light above its red sidelight on a steady
# bearing of 045 degrees relative: a power-driven vessel showing her port side, closing. Seen from our foredeck.
#   blender --background --factory-startup --python docs/design/blender/fig_lights.py -- --out .../fig-lights.jpg
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C, kit as K, kit_night as N

arg = C.cli(); OUT = arg('--out', 'fig-lights.jpg'); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
DIST = arg('--dist', 150.0); EXPO = arg('--exposure', 0.75); STEAM = arg('--steam', 0.5)
C.reset()
y = K.load_yacht(); y.place(0, 0, heading=0)
N.night_scene('calm')
N.our_lights(y, steaming=STEAM > 0, power=STEAM); N.cloth_furled(y)
bow = y.world((10.5, 0.13, 2.0))
L = N.ship(N.at_bearing(bow, 45, DIST), heading=300, lights=('masthead', 'red'))
N.foredeck_camera(y, bearing=18, lens=18)
C.render(OUT, SAMPLES, SCALE, EXPO, [(tuple(L['masthead'] + Vector((0, 0, 1.2))), 'white over red')],
         'Night · bearing 045° relative, steady', space='blender', extra={'bloom': 1.0})
