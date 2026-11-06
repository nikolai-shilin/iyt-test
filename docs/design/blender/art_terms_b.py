# Article bareboat-skipper/terms, figures 5-9: the points of sail, drone views. Wind from the north in all; port tack
# (wind over the port side, boom to starboard). The same camera for every figure so the wind arrow, the red no-go fan
# (±45° of the wind) and the boat line up from one figure to the next.
#   5 close-hauled 045   6 beam reach 090   7 broad reach 135   8 run 175   9 in irons 000
#   blender --background --factory-startup --python docs/design/blender/art_terms_b.py -- --fig 5 [--out x.jpg]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'terms')
arg = C.cli(); FIG = arg('--fig', 5); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
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

#        heading, boom (− = to starboard), genoa side, heel (+ = to starboard), pill, note
SPEC = {
    5: (45, -10, 'starboard', 16, 'close-hauled · about 45° off the wind', 'Close-hauled: sails pulled in tight'),
    6: (90, -38, 'starboard', 10, 'beam reach · wind on the beam', 'Beam reach: sails eased about halfway'),
    7: (135, -62, 'starboard', 5, 'broad reach · wind on the quarter', 'Broad reach: sails well out'),
    8: (175, -82, 'port', 2, 'run · wind astern, main right out', 'Run: genoa goosewinged'),
    9: (0, 0, 'starboard', 0, 'in irons · head to wind, stopped', 'In irons: sails flapping, no way on'),
}
hdg, boom, gside, heel, pill, note = SPEC[FIG]

def no_go_fan(r=34.0, half=45.0, z=0.35):
    """A thin red, half-transparent fan on the water: the arc the boat cannot sail, ±45° either side of the wind."""
    bm = bmesh.new(); c = bm.verts.new((0, 0, z)); ring = []
    for i in range(25):
        a = math.radians(-half + 2 * half * i / 24); ring.append(bm.verts.new((r * math.sin(a), r * math.cos(a), z)))
    for i in range(24): bm.faces.new((c, ring[i], ring[i + 1]))
    me = bpy.data.meshes.new('nogo'); bm.to_mesh(me); bm.free()
    m, nt, b, out = C.new_mat('nogo')
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.9, 0.05, 0.03, 1); em.inputs['Strength'].default_value = 1.6
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = 0.18
    nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    o = C.obj('nogo', me, m); o.visible_shadow = False
    # its dashed edges: two thin red strips along the ±45° lines
    for s in (-1, 1):
        a = math.radians(s * half); d = Vector((math.sin(a), math.cos(a), 0))
        for k in range(8):
            p0 = d * (5 + k * 3.8); p1 = d * (5 + k * 3.8 + 2.2)
            C.tube('nogo-edge', [p0 + Vector((0, 0, z + 0.05)), p1 + Vector((0, 0, z + 0.05))], 0.18, 6, 1.0, C.simple('nogo-edge', '#e0251b', 0.6))
    return o

C.reset()
sails = {'main': True, 'genoa': gside, 'boom': boom}
if FIG == 9: sails.update(camber=0.015, genoa_camber=0.02)
y = K.load_yacht(name='you', sails=sails).place(0, 0, heading=hdg, heel=heel)
if FIG == 9:   # luffing: ripple the slack cloth
    tex = bpy.data.textures.new('flap', 'CLOUDS'); tex.noise_scale = 0.9
    for o in bpy.data.objects:
        if o.name.startswith(('main', 'genoa')) and o.type == 'MESH':
            md = o.modifiers.new('flap', 'DISPLACE'); md.texture = tex; md.strength = 0.35; md.mid_level = 0.5
            o.modifiers.move(len(o.modifiers) - 1, 0)
else:
    K.wake(y, 26 if FIG != 8 else 30, 7, 1.0)
K.sea('breeze', size=40.0, repeat=10)
K.day_sky(sun_az=215, sun_el=42)
no_go_fan()

# one camera for all five: south of the boat, high, looking north over her at the fan
c = Vector((0, 9, 0))
a, e, dist = math.radians(180), math.radians(52), 72.0
eye = c + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * dist
K.camera(tuple(eye), tuple(c), 30)

labels = [(tuple(y.world((K.MAST.x, K.MAST.y, 21.5 + K.WL))), pill, 'blue'), ((0, 36, 1.0), 'no-go zone', 'red')]
w0, w1 = Vector((24, 34, 6)), Vector((24, 16, 6))
labels.append((tuple(w0 + Vector((0, 0, 2))), 'Wind', 'blue'))
C.render(OUT, SAMPLES, SCALE, -0.7, labels, note, space='blender', arrows=[(tuple(w0), tuple(w1), 'blue')])
