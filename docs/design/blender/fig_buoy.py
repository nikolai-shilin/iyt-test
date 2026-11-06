# Figure type "buoy": entering a Mediterranean harbour from seaward, a red port-hand lateral mark (IALA A, can
# topmark, Fl R) fine on the port bow; the harbour moles and the town behind it. Also the sketch-9 helm views:
#   --kind lat-port (default) | lat-stbd (green conical topmark) | north (north cardinal, backlit)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C, kit as K

arg = C.cli(); OUT = arg('--out', 'fig-buoy.jpg'); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100); KIND = arg('--kind', 'lat-port')
C.reset()
y = K.load_yacht()
y.place(0, 0, heading=0)
K.sea('breeze' if KIND == 'north' else 'calm')
if KIND == 'north':
    K.day_sky(sun_az=8, sun_el=14, strength=0.3)          # low sun almost dead ahead: the mark is backlit
    b, _ = K.cardinal_buoy('north', at=(-7, 44))
    K.coast(distance=2600, bearing=350, height=90, town=False)
    labels = [((-7, 44, 6.5), 'two cones up')]; note = 'North cardinal: pass north of it'
else:
    K.day_sky(sun_az=230, sun_el=38)
    side = 'port' if KIND == 'lat-port' else 'starboard'
    bx = -8 if side == 'port' else 8
    b, _ = K.lateral_buoy(side, at=(bx, 40))
    K.coast(distance=950, bearing=0, height=110, town=True)
    K.breakwater((-260, 330), (-60, 300), light='red'); K.breakwater((260, 320), (60, 300), light='green')
    labels = [((bx, 40, 7.2), 'Fl R' if side == 'port' else 'Fl G')]
    note = 'Entering harbour from seaward'
K.haze(0.00045)
# on the foredeck just ahead of the mast, eye height, looking forward over the pulpit
eye = y.world((6.3, 0.75, 5.2)); look = y.world((45.0, 3.2, 3.2))
K.camera(eye, look, 24)
C.render(OUT, SAMPLES, SCALE, -0.8, labels, note, space='blender')
