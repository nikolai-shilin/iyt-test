# Instruments for the Blender figures: gauges with drawn faces (make_faces.py), an engine panel, a pedestal
# steering compass with a glass dome, joinery for the nav station. Blender space, Z up, metres.
import os, math, subprocess
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K
from common import node, link, setin, math_, ramp, mixc, lin, new_mat, obj_coords, noise, bump_from

HERE = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(HERE, 'textures')
def deg(a): return math.radians(a)

def face_png(kind, *args):
    """Draw a face with the system Python (Pillow) and return its path."""
    os.makedirs(TEX, exist_ok=True)
    out = os.path.join(TEX, f"{kind}{'-' + '-'.join(args) if args else ''}.png")
    subprocess.run(['python3', os.path.join(HERE, 'make_faces.py'), kind, out, *args], check=True)
    return out

def image_mat(name, path, rough=0.35, emit=0.0):
    m, nt, b, out = new_mat(name)
    tx = node(nt, 'ShaderNodeTexImage'); tx.image = bpy.data.images.load(path)
    link(nt, tx.outputs['Color'], b.inputs['Base Color']); setin(b, 'Roughness', rough)
    if emit: link(nt, tx.outputs['Color'], b.inputs['Emission Color']); setin(b, 'Emission Strength', emit)
    return m

def disc(name, r, mat, loc, normal='Y-', seg=96):
    """A flat disc with UVs mapping the square image onto it (image top = +Z for a wall disc, +Y for a flat one)."""
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=seg, radius=r)
    uv = bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        for l in f.loops: co = l.vert.co; l[uv].uv = (co.x / (2 * r) + 0.5, co.y / (2 * r) + 0.5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = C.obj(name, me, mat, Vector(loc))
    if normal == 'Y-': o.rotation_euler = (deg(90), 0, 0)      # stands up, facing -Y (towards the camera)
    return o

def glass_mat(name='gauge-glass'):
    m, nt, b, _ = new_mat(name)
    setin(b, 'Base Color', (1, 1, 1, 1)); setin(b, 'Roughness', 0.0); setin(b, 'IOR', 1.5); setin(b, 'Transmission Weight', 1.0)
    return m

def gauge(face, at, r, value_angle=None, needle_color='#f08a24', bezel='chrome'):
    """A round gauge on a wall facing -Y at `at` (x, y, z): drawn face, needle, chrome bezel, glass."""
    at = Vector(at); M = K.mats()
    disc('face', r, image_mat('face-' + os.path.basename(face), face, 0.5), at)
    ring = C.obj('bezel', _torus(r * 1.04, r * 0.07), M['chrome'] if bezel == 'chrome' else M['dark'], at + Vector((0, -0.002, 0)))
    ring.rotation_euler = (deg(90), 0, 0)
    gl = disc('glass', r * 1.0, glass_mat(), at + Vector((0, -0.006, 0)))
    if value_angle is not None:
        nm = C.rbox('needle', (r * 0.06, 0.002, r * 0.86), 0.0005, 1)
        n = C.obj('needle', nm, C.simple('needle', needle_color, 0.4), at + Vector((0, -0.003, 0)))
        n.rotation_mode = 'XYZ'
        piv = bpy.data.objects.new('needle-pivot', None); C.col.objects.link(piv); piv.location = at + Vector((0, -0.003, 0))
        n.parent = piv; n.location = (0, 0, r * 0.38)
        piv.rotation_euler = (0, deg(value_angle), 0)            # clockwise from 12 o'clock, seen from the front
        C.obj('hub', _cyl_y(r * 0.08, 0.004), M['dark'], at + Vector((0, -0.004, 0)))
    return ring

def _torus(R, r):
    bm = bmesh.new(); seg, ring = 64, 12
    verts = []
    for i in range(seg):
        a = i / seg * math.tau
        for j in range(ring):
            b = j / ring * math.tau
            verts.append(bm.verts.new(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b))))
    for i in range(seg):
        for j in range(ring):
            a0 = i * ring + j; a1 = i * ring + (j + 1) % ring; b0 = ((i + 1) % seg) * ring + j; b1 = ((i + 1) % seg) * ring + (j + 1) % ring
            bm.faces.new((verts[a0], verts[b0], verts[b1], verts[a1]))
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new('torus'); bm.to_mesh(me); bm.free(); return me

def _cyl_y(r, h):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=r, radius2=r, depth=h)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(deg(90), 3, 'X'))
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new('cyl'); bm.to_mesh(me); bm.free(); return me

def joinery_mat(name='joinery'):
    """Varnished teak or mahogany veneer: warm, straight grain, a satin clear coat."""
    m, nt, b, _ = new_mat(name)
    oc = obj_coords(nt)
    mp = node(nt, 'ShaderNodeMapping'); setin(mp, 'Scale', (3.0, 3.0, 160.0)); link(nt, oc, mp.inputs['Vector'])
    g = node(nt, 'ShaderNodeTexNoise', in_Scale=1.0, in_Detail=6.0, in_Roughness=0.6); link(nt, mp.outputs['Vector'], g.inputs['Vector'])
    c = ramp(nt, [(0.3, '#5a2f17'), (0.55, '#7a4422'), (0.75, '#8f5530')]); link(nt, g.outputs['Fac'], c.inputs['Fac'])
    link(nt, c.outputs['Color'], b.inputs['Base Color']); setin(b, 'Roughness', 0.45); setin(b, 'Coat Weight', 0.6); setin(b, 'Coat Roughness', 0.15)
    bump_from(nt, b, g.outputs['Fac'], 0.15, 0.0005)
    return m

def wall(name, x0, x1, z0, z1, y, mat):
    me = bpy.data.meshes.new(name); me.from_pydata([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [], [(0, 1, 2, 3)])
    return C.obj(name, me, mat)

def area_light(loc, look, power, size, color=(1.0, 0.95, 0.88)):
    ld = bpy.data.lights.new('soft', 'AREA'); ld.energy = power; ld.size = size; ld.color = color
    o = bpy.data.objects.new('soft', ld); C.col.objects.link(o); o.location = Vector(loc)
    o.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o

def lathe(name, prof, mat, seg=96):
    return C.lathe(name, prof, seg, mat)
