# Figure type "bay": "A hot sunny morning, calm. By 14:00 a steady 15-knot onshore wind has set in. What is it?"
# An aerial oblique view of a Mediterranean bay in the afternoon: dry hills, a beach, a whitewashed village, two
# harbour moles, yachts at anchor heading into the breeze and others reaching across the bay, the sea breeze on
# the water blowing in towards the land.
#   blender --background --factory-startup --python docs/design/blender/fig_bay.py -- --out .../fig-bay.jpg
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C, kit as K, kit_world as KW

arg = C.cli(); OUT = arg('--out', 'fig-bay.jpg'); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
C.reset()

KW.terrain(-900, 900, -260, 2600, step=5.0)
houses = KW.town(cx=0.0, width=170.0, depth=110.0, n=270)
KW.trees(1500, avoid=houses)
KW.mole((78, KW.shore_y(78) - 4), (18, 66), width=9.0)
KW.mole((-96, KW.shore_y(-96) - 4), (-42, 74), width=8.0)
K.sea('breeze', size=36.0, res=9, repeat=22, center=(0, -120))
for o in bpy.data.objects:
    if o.name.startswith('ocean'): o.data.materials.clear(); o.data.materials.append(KW.bay_sea_mat())

# yachts: three at anchor lying head to the onshore wind (bows to the south), three reaching across the bay
for i, (x, y) in enumerate(((-120, 38), (112, 22), (-28, -6))):
    K.load_yacht(name=f'anchored{i}').place(x, y, heading=182 + 6 * i)
for i, (x, y, hdg) in enumerate(((-20, -95, 92), (105, -60, 268), (-175, -40, 95))):
    side = 'port' if hdg < 180 else 'starboard'; boom = 26 if side == 'port' else -26
    K.load_yacht(name=f'sailing{i}', sails={'main': True, 'genoa': side, 'boom': boom}).place(x, y, heading=hdg, heel=-9 if side == 'port' else 9)

K.day_sky(sun_az=232, sun_el=38, strength=0.25, haze=2.6)
KW.camera((40, -360, 150), (0, 190, 48), lens=30)

land = (35, 400, KW.height(35, 400) + 8)
labels = [(land, 'LAND · hot'), ((190, -25, 1.0), 'SEA · cool', 'blue'), ((-120, 10, 2.0), 'Wind', 'red')]
arrows = [((-120, -70, 2.0), (-45, 60, 2.0), 'red')]
C.render(OUT, SAMPLES, SCALE, -0.8, labels, 'Afternoon, clear sky, wind onshore', space='blender', arrows=arrows)
