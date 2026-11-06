# Renders a rope scene or knot exported from figure-rope-3d.html (see export.html, export_scenes.mjs):
# the glTF brings the geometry, the JSON the rope centrelines, camera, labels and note. Materials are swapped
# for procedural ones and the ropes rebuilt as laid three-strand or plaited braid.
#
# Run:  blender --background --factory-startup --python docs/design/blender/render_scene.py -- \
#         --name winch --out docs/design/figure-style/blender/rope-winch.jpg --samples 256
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

arg = C.cli()
NAME = arg('--name', 'winch')
OUT = arg('--out', f'{NAME}.jpg'); SAMPLES = arg('--samples', 256); SCALE = arg('--scale', 100); BLEND = arg('--blend', '')
# per-scene look: exposure, aperture (f-stop) and sky brightness
LOOK = {
    'winch': dict(exposure=-0.7, fstop=8.0), 'cleat': dict(exposure=-1.35, fstop=22.0), 'rail': dict(exposure=-0.8, fstop=11.0),
    'sheet': dict(exposure=-0.7, fstop=8.0),
}
look = dict(exposure=-0.6, fstop=16.0, sky=0.22)  # knots: close-ups, so a small aperture keeps the whole knot sharp
look.update(LOOK.get(NAME, {}))
EXPOSURE = arg('--exposure', float(look['exposure'])); FSTOP = arg('--fstop', float(look['fstop']))

C.reset()
d = C.load_exported(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scenes', NAME))
C.sky(d['sun']['pos'], d['sun']['target'], look.get('sky', 0.22))
import kit as K; K.darken_visible_sky()   # the darker daylight look shared with the figure types
cam = C.camera_matrix(d['cam']['matrix'], d['cam']['fov'])
C.focus_on_centre(cam, FSTOP)
C.render(OUT, SAMPLES, SCALE, EXPOSURE, [(l['p'], l['text']) for l in d['labels']], d['note'], BLEND)
