# Figure type "sail": at the helm on starboard tack, wind over the starboard side, boom out to port.
# Camera at the wheel looking forward past the mast; sails set, a breeze on the sea, another yacht far off.
#   blender --background --factory-startup --python docs/design/blender/fig_sail.py -- --out .../fig-sail.jpg
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C, kit as K

arg = C.cli(); OUT = arg('--out', 'fig-sail.jpg'); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
C.reset()
y = K.load_yacht(boom=28, sails={'main': True, 'genoa': 'port'})
y.place(0, 0, heading=0, heel=-8)            # heading north, heeled to port (leeward)
K.sea('breeze')
K.day_sky(sun_az=140, sun_el=40)
# camera at the starboard wheel, eye height, looking forward and a little to port
eye = y.world((-2.6, -0.85, 4.95)); look = y.world((9.0, 0.3, 5.2))
cd = bpy.data.cameras.new('cam'); cd.lens = 20; cam = bpy.data.objects.new('cam', cd); C.col.objects.link(cam); bpy.context.scene.camera = cam
cam.location = eye; cam.rotation_euler = (look - eye).to_track_quat('-Z', 'Y').to_euler()
wind_from = y.world((7.0, -7.5, 8.5)); wind_to = y.world((3.5, -2.0, 7.2))
C.render(OUT, SAMPLES, SCALE, -0.9, [(tuple(wind_from), 'Wind', 'blue')], 'Wind over the starboard side, boom to port', space='blender',
         arrows=[(tuple(wind_from), tuple(wind_to), 'blue')])
