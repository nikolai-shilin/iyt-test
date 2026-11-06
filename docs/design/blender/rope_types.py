# Rope types side by side on a teak cockpit seat: a three-strand (laid) line and a braided (plaited cover) line
# of the same 16 mm size, each ending in a whipping. A sample for the rope pages, built only in Blender.
#
# Run:  blender --background --factory-startup --python docs/design/blender/rope_types.py -- \
#         --out docs/design/figure-style/blender/rope-types.jpg --samples 256
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
from common import V3

arg = C.cli()
OUT = arg('--out', 'rope-types.jpg'); SAMPLES = arg('--samples', 256); SCALE = arg('--scale', 100); BLEND = arg('--blend', '')

C.reset()
C.tbox((1.6, 0.04, 1.0), (0, -0.02, 0), C.teak_mat(), 0.004, 2, 'seat')

R = 0.008  # 16 mm lines
def lazy(z0, phase):
    """A line lying slack across the seat in a long, gentle S, ending near the middle (Three.js coordinates)."""
    pts = []
    for i in range(15):
        t = i / 14; x = -0.46 + 0.5 * t
        pts.append(V3((x, R, z0 + 0.03 * math.sin(t * math.pi * 1.3 + phase) + 0.02 * t)))
    return pts

C.three_strand('laid', lazy(-0.07, 0.0), R, 0.052, whip='#f2eee2')
C.braid('braid', lazy(0.07, 1.4), R, '#1b2c4c', '#e9e3d2', shiny=False, whip='#141414', fine=1.4)

C.sky((-1.2, 2.6, -1.0), (0, 0, 0))
import kit as K; K.darken_visible_sky()   # the darker daylight look shared with the figure types
cam = C.camera_lookat((-0.17, 0.5, 0.4), (-0.2, 0.0, 0.0), 34)
C.focus_on_centre(cam, 11.0)
C.render(OUT, SAMPLES, SCALE, -0.7, [((-0.33, R * 2, -0.075), 'three-strand (laid)'), ((-0.33, R * 2, 0.09), 'braided')], 'Rope types', BLEND)
