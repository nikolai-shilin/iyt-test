# Figure type "anchor": "The anchorage shows 2.4 m on the sounder at low water. The boat's draft is 1.9 m. Can you
# stay?" A split view at the waterline beside the yacht at anchor: hull and rig above, keel, chain and anchor below,
# the sandy seabed with stones and seagrass 2.4 m down.
#   blender --background --factory-startup --python docs/design/blender/fig_anchor.py -- --out .../fig-anchor.jpg
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix, noise as mnoise
import common as C, kit as K, kit_world as KW

arg = C.cli(); OUT = arg('--out', 'fig-anchor.jpg'); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
DEPTH, DRAFT = 2.4, 1.9
C.reset()

# the yacht, lifted a touch so her keel draws 1.9 m (the model draws 2.0)
y = K.load_yacht(); y.place(0, 0, heading=0)
y.root.location.z = 2.0 - DRAFT
KW.antifoul_hull(y)
bpy.context.view_layer.update()
keel = [o for o in y.objs if o.type == 'MESH' and not o.hide_render and K.bbox([o])[0].z < -DRAFT + 0.15]
klo, khi = K.bbox(keel); keel_bottom = Vector(((klo.x + khi.x) / 2, (klo.y + khi.y) / 2, klo.z))
print('keel bottom', keel_bottom)

# water, seabed, stones, seagrass
KW.water_body(depth=8.0, size=700.0, density=0.06, color='#0f4a4f', absorb='#3aa79b', reflect=0.25, absorb_density=0.07)
KW.far_sea_ring(inner=350.0)
KW.seabed(z=-DEPTH, size=140.0, res=220, center=(0, 10), colors=('#8f9a7e', '#b2b593', '#a3a886'))
KW.stones(70, ((-25, -20), (30, 45)), -DEPTH, scale=(0.12, 0.45))
KW.seagrass(((-30, -25), (40, 50)), -DEPTH, clumps=2600, length=0.55)

# the Delta anchor, blade dug into the sand ahead of the boat, shank towards her
root, objs = K.load_model('anchor-delta.glb', drop_planes=False)
S = Matrix.Diagonal((1.35, 1.35, 1.35, 1.0))
M = Matrix.Translation((3.9, 10.6, 0.0)) @ Matrix.Rotation(math.radians(48), 4, 'Z') @ S @ Matrix.Translation((-0.48, -1.17, 0.0))
root.matrix_world = M
bpy.context.view_layer.update()
alo, ahi = K.bbox(objs)
root.location.z += (-DEPTH - 0.2) - alo.z
bpy.context.view_layer.update()
shackle = root.matrix_world @ Vector((0.48, 1.17, 0.52))
print('shackle', shackle)

# the chain: from the bow roller in a catenary-like curve to the sand, then along the bottom to the shackle
bow = y.world((10.95, 0.13, 3.72))
touch = Vector((1.3, 8.4, -DEPTH + 0.06))
hang = KW.bezier(bow, bow + Vector((0.1, 0.5, -1.5)), touch - Vector((0.5, 1.1, 0.0)), touch, 80)
lie = [touch.lerp(shackle, t) + Vector((-0.12 * math.sin(t * 6), 0.1 * math.sin(t * 6), 0.0)) for t in (i / 30 for i in range(1, 31))]
KW.chain(hang + lie, link_len=0.07, wire=0.0095)

# a low coast far behind the boat, hazy
verts, faces = [], []
nx, ny = 160, 20
for j in range(ny + 1):
    for i in range(nx + 1):
        X = -1300 + j * 25; Yv = -1500 + i * 25
        h = max(0.0, 28 + 26 * mnoise.noise(Vector((Yv * 0.003, X * 0.003, 2.0))) + 12 * mnoise.noise(Vector((Yv * 0.01, X * 0.01, 5.0)))) * min(1.0, (ny - j) / 5)
        verts.append((X, Yv, h - 1.0))
for j in range(ny):
    for i in range(nx):
        a = j * (nx + 1) + i; faces.append((a, a + nx + 1, a + nx + 2, a + 1))
me = bpy.data.meshes.new('coast'); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
C.obj('coast', me, KW.land_mat())

K.day_sky(sun_az=120, sun_el=55, strength=0.25, haze=2.0)

# camera at the waterline off the starboard side, a little forward, so the frame splits at the surface
eye = Vector((13.0, 3.8, 0.002)); look = Vector((0.0, 4.4, -0.5))
KW.camera(eye, look, lens=16)

kb = keel_bottom
# two gauges between the boat and the camera: draft beside the keel, depth further forward
gx = 3.5
dg = Vector((gx, kb.y - 1.0, 0.0)); sg = Vector((gx, kb.y + 6.5, 0.0))
labels = [((dg.x, dg.y - 2.2, -0.75), f'Draft {DRAFT} m', 'yellow'),
          ((sg.x + 3.0, sg.y - 1.0, -DEPTH + 0.05), f'Depth {DEPTH} m at low water', 'blue')]
arrows = [((dg.x, dg.y, -0.95), (dg.x, dg.y, -0.03), 'yellow'), ((dg.x, dg.y, -0.95), (dg.x, dg.y, -DRAFT + 0.03), 'yellow'),
          ((sg.x, sg.y, -1.2), (sg.x, sg.y, -0.03), 'blue'), ((sg.x, sg.y, -1.2), (sg.x, sg.y, -DEPTH + 0.03), 'blue')]
C.render(OUT, SAMPLES, SCALE, -0.55, labels, 'Sounder at low water', space='blender', arrows=arrows)
