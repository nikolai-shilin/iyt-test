# World pieces for the anchoring and bay figures: the water seen from above and below, a seabed with stones and
# seagrass, an anchor chain, a hull that is antifouled below the waterline, and a Mediterranean bay (hills, beach,
# whitewashed town, harbour moles). Blender space, Z up, the sea surface at z = 0. Builds on common.py and kit.py.
import os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, noise as mnoise
import common as C, kit as K
from common import node, link, setin, math_, ramp, mixc, lin, new_mat, obj_coords, noise, bump_from

def deg(a): return math.radians(a)

def world_z(nt):
    """World-space height of the shaded point."""
    g = node(nt, 'ShaderNodeNewGeometry'); s = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, g.outputs['Position'], s.inputs['Vector'])
    return s.outputs['Z']

def camera(eye, look, lens=24.0, name='cam'):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.05; cd.clip_end = 20000
    cam = bpy.data.objects.new(name, cd); C.col.objects.link(cam); bpy.context.scene.camera = cam
    eye, look = Vector(eye), Vector(look)
    cam.location = eye; cam.rotation_euler = (look - eye).to_track_quat('-Z', 'Y').to_euler()
    return cam

# ---------- hull below the waterline ----------
def hull_wl_mat():
    """Gelcoat above the waterline, a navy boot stripe at it, dark antifouling below (by world height)."""
    m, nt, b, _ = new_mat('hull-waterline')
    z = world_z(nt)
    c = ramp(nt, [(0.0, '#22252b'), (0.455, '#22252b'), (0.46, '#16213b'), (0.505, '#16213b'), (0.51, '#f1f1ec'), (1.0, '#f1f1ec')], 'CONSTANT')
    zz = math_(nt, 'MULTIPLY_ADD', z, 1.0, 0.5)  # z = 0 -> 0.5
    link(nt, zz, c.inputs['Fac'])
    link(nt, c.outputs['Color'], b.inputs['Base Color'])
    rr = node(nt, 'ShaderNodeMapRange', in_From_Min=0.45, in_From_Max=0.52, in_To_Min=0.85, in_To_Max=0.3); link(nt, zz, rr.inputs['Value'])
    link(nt, rr.outputs['Result'], b.inputs['Roughness'])
    cw = node(nt, 'ShaderNodeMapRange', in_From_Min=0.45, in_From_Max=0.52, in_To_Min=0.0, in_To_Max=1.0); link(nt, zz, cw.inputs['Value'])
    link(nt, cw.outputs['Result'], b.inputs['Coat Weight'])
    return m

def antifoul_hull(y):
    """Give every part of the yacht that dips below the water the waterline material."""
    bpy.context.view_layer.update()
    wl = hull_wl_mat()
    for o in y.objs:
        if o.type != 'MESH' or o.hide_render: continue
        lo, hi = K.bbox([o])
        if lo.z < -0.05:
            for s in o.material_slots: s.material = wl

# ---------- water seen from both sides ----------
def water_body(depth=6.0, size=600.0, color='#2a7f86', density=0.06, center=(0, 0), absorb='#3f9fa6', reflect=1.0, absorb_density=0.0):
    """A closed box of water from z = -depth to z = 0: the top face is the surface (partly mirror, partly clear,
    by Fresnel, both from above and from below), the inside is a green-blue scattering volume."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size + center[0], v.co.y * size + center[1], (v.co.z - 0.5) * depth))
    me = bpy.data.meshes.new('water'); bm.to_mesh(me); bm.free()
    m, nt, b, out = new_mat('water-body')
    nt.nodes.remove(b)
    # surface: transparent where you look into it, glossy where Fresnel says it reflects; small ripples
    fr = node(nt, 'ShaderNodeFresnel'); setin(fr, 'IOR', 1.333)
    oc = obj_coords(nt); rip = noise(nt, oc, 1.4, 6.0)
    bp = node(nt, 'ShaderNodeBump'); setin(bp, 'Strength', 0.08); setin(bp, 'Distance', 0.05); link(nt, rip, bp.inputs['Height'])
    link(nt, bp.outputs['Normal'], fr.inputs['Normal'])
    gl = node(nt, 'ShaderNodeBsdfGlossy'); setin(gl, 'Roughness', 0.02); link(nt, bp.outputs['Normal'], gl.inputs['Normal'])
    tp = node(nt, 'ShaderNodeBsdfTransparent')
    # a teaching figure needs to see in: the surface reflects only part of what Fresnel says
    frs = math_(nt, 'MULTIPLY', fr.outputs[0], reflect)
    mx = node(nt, 'ShaderNodeMixShader'); link(nt, frs, mx.inputs['Fac']); link(nt, tp.outputs[0], mx.inputs[1]); link(nt, gl.outputs[0], mx.inputs[2])
    link(nt, mx.outputs[0], out.inputs['Surface'])
    vol = node(nt, 'ShaderNodeVolumePrincipled'); setin(vol, 'Color', lin(color)); setin(vol, 'Density', density)
    setin(vol, 'Absorption Color', lin(absorb)); setin(vol, 'Anisotropy', 0.55)
    ab = node(nt, 'ShaderNodeVolumeAbsorption'); setin(ab, 'Color', lin(absorb)); setin(ab, 'Density', absorb_density)
    add = node(nt, 'ShaderNodeAddShader'); link(nt, vol.outputs[0], add.inputs[0]); link(nt, ab.outputs[0], add.inputs[1])
    link(nt, add.outputs[0], out.inputs['Volume'])
    me.materials.append(m)
    return C.obj('water', me)

# ---------- seabed ----------
def seabed(z=-2.4, size=120.0, res=200, center=(0, 0), seed=4, colors=('#b8a57e', '#d6c49b', '#c9b68b')):
    """Sand with soft ripples and dips, at height z."""
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=res, y_segments=res, size=size / 2)
    for v in bm.verts:
        p = Vector((v.co.x * 0.08, v.co.y * 0.08, seed))
        v.co.z = 0.08 * mnoise.noise(p) + 0.03 * mnoise.noise(p * 4.0)
        v.co.x += center[0]; v.co.y += center[1]
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new('seabed'); bm.to_mesh(me); bm.free()
    m, nt, b, _ = new_mat('sand')
    oc = obj_coords(nt)
    n1 = noise(nt, oc, 0.6, 4.0); n2 = noise(nt, oc, 30.0, 6.0)
    c = ramp(nt, [(0.3, colors[0]), (0.55, colors[1]), (0.75, colors[2])]); link(nt, n1, c.inputs['Fac'])
    g = ramp(nt, [(0.4, (1, 1, 1, 1)), (0.7, (0.86, 0.84, 0.8, 1))]); link(nt, n2, g.inputs['Fac'])
    link(nt, mixc(nt, 1.0, c.outputs['Color'], g.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color'])
    setin(b, 'Roughness', 0.95)
    # wave ripples in the sand
    wv = node(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', in_Scale=6.0, in_Distortion=4.0, in_Detail=2.0); link(nt, oc, wv.inputs['Vector'])
    h = math_(nt, 'MULTIPLY_ADD', wv.outputs['Fac'], 0.6, n2)
    bump_from(nt, b, h, 0.5, 0.02)
    o = C.obj('seabed', me, m, (0, 0, z))
    return o

def stones(n, area, z, seed=5, scale=(0.15, 0.5)):
    """Rounded stones half sunk in the sand, a little weed on top."""
    random.seed(seed)
    m, nt, b, _ = new_mat('stone')
    oc = obj_coords(nt); n1 = noise(nt, oc, 8.0, 6.0)
    c = ramp(nt, [(0.35, '#6c6a5f'), (0.6, '#8e8a7b'), (0.75, '#5d6b3e')]); link(nt, n1, c.inputs['Fac'])
    link(nt, c.outputs['Color'], b.inputs['Base Color']); setin(b, 'Roughness', 0.9)
    bump_from(nt, b, noise(nt, oc, 25.0, 8.0), 0.6, 0.01)
    meshes = []
    for k in range(5):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        for v in bm.verts:
            v.co *= 1.0 + 0.25 * mnoise.noise(v.co * 1.3 + Vector((k * 7.0, 0, 0)))
            v.co.z *= 0.55
        for f in bm.faces: f.smooth = True
        me = bpy.data.meshes.new(f'stone{k}'); bm.to_mesh(me); bm.free(); me.materials.append(m); meshes.append(me)
    (x0, y0), (x1, y1) = area
    for i in range(n):
        o = bpy.data.objects.new('stone', random.choice(meshes)); C.col.objects.link(o)
        s = random.uniform(*scale); o.scale = (s * random.uniform(0.8, 1.4), s, s)
        o.location = (random.uniform(x0, x1), random.uniform(y0, y1), z + s * 0.05)
        o.rotation_euler = (0, 0, random.uniform(0, 6.28))

def seagrass(area, z, clumps=420, seed=6, length=0.55, patches=True):
    """Posidonia-like seagrass: clumps of long ribbon leaves, bending with the swell, in patches on the sand."""
    (x0, y0), (x1, y1) = area
    random.seed(seed)
    gm, nt, b, out = new_mat('seagrass')
    oc = obj_coords(nt); oi = node(nt, 'ShaderNodeObjectInfo')
    sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, sep.inputs['Vector'])
    tipf = node(nt, 'ShaderNodeMapRange', in_From_Min=0.0, in_From_Max=length); link(nt, sep.outputs['Z'], tipf.inputs['Value'])
    c = ramp(nt, [(0.0, '#2f4a1f'), (0.6, '#5b7a33'), (1.0, '#8a8a52')]); link(nt, tipf.outputs['Result'], c.inputs['Fac'])
    v = ramp(nt, [(0.0, (0.75, 0.75, 0.75, 1)), (1.0, (1.1, 1.1, 1.0, 1))]); link(nt, oi.outputs['Random'], v.inputs['Fac'])
    link(nt, mixc(nt, 1.0, c.outputs['Color'], v.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color'])
    setin(b, 'Roughness', 0.55); setin(b, 'Subsurface Weight', 0.3); setin(b, 'Subsurface Scale', 0.01)
    # a few clump shapes: 7-11 ribbons from one root, each a narrow strip bending over with a lean
    protos = []
    for k in range(6):
        bm = bmesh.new()
        for leaf in range(random.randint(10, 16)):
            L = length * random.uniform(0.6, 1.25); w = random.uniform(0.012, 0.02)
            a = random.uniform(0, math.tau); lean = random.uniform(0.15, 0.6); twist = random.uniform(-0.6, 0.6)
            dirv = Vector((math.cos(a), math.sin(a), 0))
            prev = None; nseg = 10
            for i in range(nseg + 1):
                t = i / nseg
                p = dirv * (lean * L * t * t) + Vector((0, 0, L * t * (1 - 0.35 * lean * t)))
                side = Vector((-dirv.y, dirv.x, 0)); side.rotate(Euler((0, 0, twist * t)))
                l, r = bm.verts.new(p - side * w / 2), bm.verts.new(p + side * w / 2)
                if prev: bm.faces.new((prev[0], prev[1], r, l)).smooth = True
                prev = (l, r)
        me = bpy.data.meshes.new(f'grass{k}'); bm.to_mesh(me); bm.free(); me.materials.append(gm); protos.append(me)
    n = 0; tries = 0
    while n < clumps and tries < clumps * 20:
        tries += 1
        x, y = random.uniform(x0, x1), random.uniform(y0, y1)
        if patches and mnoise.noise(Vector((x * 0.16, y * 0.16, seed))) < 0.05: continue
        o = bpy.data.objects.new('grass', random.choice(protos)); C.col.objects.link(o)
        o.location = (x, y, z - 0.03); o.rotation_euler = (random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(0, 6.28))
        s = random.uniform(0.7, 1.3); o.scale = (s, s, s); n += 1
    return n

# ---------- anchor chain ----------
def chain(points, link_len=0.06, wire=0.0085, name='chain'):
    """Galvanised chain along a polyline: oval links, every other one turned 90 degrees about the run."""
    m, nt, b, _ = new_mat('galv-chain')
    oc = obj_coords(nt)
    c = ramp(nt, [(0.4, '#8d9296'), (0.6, '#a8adb0')]); link(nt, noise(nt, oc, 60.0, 4.0), c.inputs['Fac'])
    link(nt, c.outputs['Color'], b.inputs['Base Color']); setin(b, 'Metallic', 0.85); setin(b, 'Roughness', 0.45)
    # one link mesh: a stretched torus in the XZ plane, long axis X
    bm = bmesh.new()
    R = link_len / 2 - wire
    ring = 20; tube = 8
    verts = []
    for i in range(ring):
        a = i / ring * math.tau
        cx, cz = math.cos(a) * R * 1.55, math.sin(a) * R
        tx, tz = -math.sin(a) * 1.55, math.cos(a); tl = math.hypot(tx, tz); tx, tz = tx / tl, tz / tl
        nx, nz = tz, -tx
        row = []
        for j in range(tube):
            bta = j / tube * math.tau
            p = Vector((cx + (nx * math.cos(bta)) * wire, math.sin(bta) * wire, cz + (nz * math.cos(bta)) * wire))
            row.append(bm.verts.new(p))
        verts.append(row)
    for i in range(ring):
        for j in range(tube):
            a, bb = verts[i][j], verts[(i + 1) % ring][j]; c2, d = verts[(i + 1) % ring][(j + 1) % tube], verts[i][(j + 1) % tube]
            f = bm.faces.new((a, bb, c2, d)); f.smooth = True
    me = bpy.data.meshes.new('link'); bm.to_mesh(me); bm.free(); me.materials.append(m)
    # resample the path at link pitch
    P = [Vector(p) for p in points]
    acc = [0.0]
    for a, bq in zip(P, P[1:]): acc.append(acc[-1] + (bq - a).length)
    pitch = link_len * 0.78; n = int(acc[-1] / pitch); j = 0
    for k in range(n):
        s = k * pitch
        while j < len(acc) - 2 and acc[j + 1] < s: j += 1
        t = (s - acc[j]) / max(1e-9, acc[j + 1] - acc[j]); p = P[j].lerp(P[j + 1], t); d = (P[j + 1] - P[j]).normalized()
        q = d.to_track_quat('X', 'Z')
        o = bpy.data.objects.new(name, me); C.col.objects.link(o)
        o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = q @ Euler((deg(90) * (k % 2), 0, 0)).to_quaternion()
        o.location = p
    return me

def bezier(p0, p1, p2, p3, n=60):
    P = [Vector(p) for p in (p0, p1, p2, p3)]
    return [P[0] * (1 - t) ** 3 + P[1] * 3 * (1 - t) ** 2 * t + P[2] * 3 * (1 - t) * t * t + P[3] * t ** 3 for t in (i / n for i in range(n + 1))]

# ---------- land for the bay ----------
def plaster_mat():
    m, nt, b, _ = new_mat('whitewash')
    oc = obj_coords(nt); oi = node(nt, 'ShaderNodeObjectInfo')
    c = ramp(nt, [(0.0, '#dcd6c8'), (0.6, '#e8e4da'), (0.85, '#e4d3b2'), (1.0, '#d9c29a')]); link(nt, oi.outputs['Random'], c.inputs['Fac'])
    g = ramp(nt, [(0.3, (0.9, 0.9, 0.9, 1)), (0.7, (1, 1, 1, 1))]); link(nt, noise(nt, oc, 3.0, 4.0), g.inputs['Fac'])
    link(nt, mixc(nt, 1.0, c.outputs['Color'], g.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color']); setin(b, 'Roughness', 0.85)
    return m

def roof_mat():
    m, nt, b, _ = new_mat('terracotta')
    oc = obj_coords(nt); oi = node(nt, 'ShaderNodeObjectInfo')
    c = ramp(nt, [(0.0, '#8a3218'), (0.5, '#a3401f'), (1.0, '#7a3a24')]); link(nt, oi.outputs['Random'], c.inputs['Fac'])
    link(nt, c.outputs['Color'], b.inputs['Base Color']); setin(b, 'Roughness', 0.8)
    wv = node(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=40.0); link(nt, oc, wv.inputs['Vector'])
    bump_from(nt, b, wv.outputs['Fac'], 0.4, 0.02)
    return m

def land_mat():
    """Dry Mediterranean hillside by height and slope: sand at the shore, golden dry grass, dark maquis
    in patches and on the higher slopes, bare rock where it is steep."""
    m, nt, b, _ = new_mat('land')
    oc = obj_coords(nt); z = world_z(nt)
    g = node(nt, 'ShaderNodeNewGeometry'); sn = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, g.outputs['Normal'], sn.inputs['Vector'])
    patch = noise(nt, oc, 0.012, 5.0)
    veg = ramp(nt, [(0.34, '#a8915c'), (0.46, '#7d7c45'), (0.56, '#4a5a2c'), (0.75, '#33421f')]); link(nt, patch, veg.inputs['Fac'])
    fine = ramp(nt, [(0.3, (0.82, 0.82, 0.82, 1)), (0.7, (1.05, 1.05, 1.05, 1))]); link(nt, noise(nt, oc, 0.4, 6.0), fine.inputs['Fac'])
    vc = mixc(nt, 1.0, veg.outputs['Color'], fine.outputs['Color'], 'MULTIPLY')
    steep = node(nt, 'ShaderNodeMapRange', in_From_Min=0.86, in_From_Max=0.72); link(nt, sn.outputs['Z'], steep.inputs['Value'])
    rock = mixc(nt, steep.outputs['Result'], vc, lin('#8a7f6c'))
    sand = node(nt, 'ShaderNodeMapRange', in_From_Min=2.8, in_From_Max=1.4); link(nt, z, sand.inputs['Value'])
    col = mixc(nt, sand.outputs['Result'], rock, lin('#d8c79f'))
    wet = node(nt, 'ShaderNodeMapRange', in_From_Min=0.35, in_From_Max=-0.2); link(nt, z, wet.inputs['Value'])
    col = mixc(nt, wet.outputs['Result'], col, lin('#9c8a63'))
    link(nt, col, b.inputs['Base Color']); setin(b, 'Roughness', 0.92)
    bump_from(nt, b, noise(nt, oc, 0.6, 8.0), 0.6, 0.3)
    return m

def shore_y(x, inland=150.0, arms=0.0022):
    """The bay's shoreline: furthest inland in the middle, the headlands reaching out to sea at the sides."""
    return inland - arms * x * x + 12 * math.sin(x * 0.021) + 6 * math.sin(x * 0.07)

def height(x, y, seed=11.0):
    d = y - shore_y(x)                                  # metres inland (negative = under water)
    if d < 0: return max(-12.0, d * 0.09) - 0.3
    beach = min(1.0, d / 26.0)
    hills = 1.6 + 130 * (1 - math.exp(-max(0.0, d - 24) / 160.0)) + 170 * (1 - math.exp(-max(0.0, d - 700) / 800.0))
    rough = 30 * mnoise.noise(Vector((x * 0.005, y * 0.005, seed))) + 7 * mnoise.noise(Vector((x * 0.022, y * 0.022, seed))) + 60 * mnoise.noise(Vector((x * 0.0015, y * 0.0015, seed + 3)))
    rough *= min(1.0, max(0.0, (d - 30) / 120.0))
    return (1.6 * beach if d < 26 else hills + rough) - 0.3 + (0 if d >= 26 else 0)

def terrain(x0=-700, x1=700, y0=-250, y1=900, step=4.0, seed=11.0):
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step)
    verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x, y = x0 + i * step, y0 + j * step
            verts.append((x, y, height(x, y, seed)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i; faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    me = bpy.data.meshes.new('land'); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
    return C.obj('land', me, land_mat())

def house_mesh(w, d, h, roof_h, wall_mat, roof_m, name='house'):
    """A box house with a low hipped terracotta roof (two materials)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * w, v.co.y * d, (v.co.z + 0.5) * h))
    for f in bm.faces: f.material_index = 0
    top = [bm.verts.new(p) for p in ((-w / 2 - 0.3, -d / 2 - 0.3, h), (w / 2 + 0.3, -d / 2 - 0.3, h), (w / 2 + 0.3, d / 2 + 0.3, h), (-w / 2 - 0.3, d / 2 + 0.3, h))]
    r0 = bm.verts.new((-max(0, w - d) / 2, 0, h + roof_h)); r1 = bm.verts.new((max(0, w - d) / 2, 0, h + roof_h))
    for f in (bm.faces.new((top[0], top[1], r1, r0)), bm.faces.new((top[2], top[3], r0, r1)), bm.faces.new((top[1], top[2], r1)), bm.faces.new((top[3], top[0], r0)), bm.faces.new((top[3], top[2], top[1], top[0]))):
        f.material_index = 1
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(wall_mat); me.materials.append(roof_m)
    return me

def town(cx=0.0, width=260.0, depth=150.0, n=220, seed=21):
    """A whitewashed village climbing from the beach: houses on a jittered grid, a church with a bell tower."""
    random.seed(seed)
    wm, rm = plaster_mat(), roof_mat()
    protos = [house_mesh(random.uniform(7, 13), random.uniform(6, 10), random.uniform(4, 9), random.uniform(2.0, 3.2), wm, rm, f'house{k}') for k in range(12)]
    placed = []
    tries = 0
    while len(placed) < n and tries < n * 30:
        tries += 1
        x = cx + random.gauss(0, width / 3.2)
        d = 30 + abs(random.gauss(0, depth / 2.2))
        y = shore_y(x) + d
        if any((x - px) ** 2 + (y - py) ** 2 < 105 for px, py in placed): continue
        placed.append((x, y))
        o = bpy.data.objects.new('house', random.choice(protos)); C.col.objects.link(o)
        o.location = (x, y, height(x, y) - 0.4); o.rotation_euler = (0, 0, deg(random.choice((0, 90, 180, 270)) + random.uniform(-8, 8)))
    # church and its tower near the waterfront
    x, y = cx + 25, shore_y(cx + 25) + 48
    ch = bpy.data.objects.new('church', house_mesh(12, 24, 11, 3.0, wm, rm, 'church')); C.col.objects.link(ch); ch.location = (x, y, height(x, y) - 0.4)
    tw = bpy.data.objects.new('tower', house_mesh(4.5, 4.5, 22, 3.5, wm, rm, 'tower')); C.col.objects.link(tw); tw.location = (x + 8, y - 12, height(x, y) - 0.4)
    return placed

def trees(n=1600, seed=31, avoid=()):
    """Olive and pine clumps scattered over the hills, thinner on the steep and high ground."""
    random.seed(seed)
    m = C.simple('foliage', '#3c4a26', 0.9)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts: v.co *= 1.0 + 0.2 * mnoise.noise(v.co * 2.0); v.co.z *= 0.8
    me = bpy.data.meshes.new('tree'); bm.to_mesh(me); bm.free(); me.materials.append(m); me.shade_smooth()
    k = 0
    while k < n:
        x, y = random.uniform(-650, 650), random.uniform(-150, 850)
        d = y - shore_y(x)
        if d < 35: continue
        if any((x - ax) ** 2 + (y - ay) ** 2 < 14 ** 2 for ax, ay in avoid): continue
        if mnoise.noise(Vector((x * 0.012, y * 0.012, 3.0))) < -0.05: continue
        o = bpy.data.objects.new('tree', me); C.col.objects.link(o)
        s = random.uniform(2.0, 4.5); o.scale = (s, s, s * random.uniform(0.8, 1.3))
        o.location = (x, y, height(x, y) + s * 0.5); k += 1

def mole(start, end, width=8.0, height_=2.2, light=True):
    """A rubble-mound harbour mole: a concrete walkway on a bank of boulders, a small light at its head."""
    s, e = Vector(start), Vector(end); d = e - s; L = d.length; ang = math.atan2(d.y, d.x)
    concrete = C.concrete_mat('mole-concrete')
    top = C.rbox('mole', (L, width, height_ + 3), 0.3, 2); o = C.obj('mole', top, concrete, ((s + e) / 2).to_3d())
    o.location.z = height_ - (height_ + 3) / 2; o.rotation_euler = (0, 0, ang)
    # armour stones along the seaward side
    random.seed(int(abs(start[0]) + abs(end[1])))
    sm = C.simple('armour', '#b9b2a2', 0.9)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    me = bpy.data.meshes.new('armour'); bm.to_mesh(me); bm.free(); me.materials.append(sm)
    nrm = Vector((-math.sin(ang), math.cos(ang), 0))
    for k in range(int(L / 1.6)):
        for side in (-1, 1):
            p = s.to_3d() + d.to_3d().normalized() * (k * 1.6 + random.uniform(0, 1)) + nrm * side * (width / 2 + random.uniform(0.5, 2.2))
            r = bpy.data.objects.new('armour', me); C.col.objects.link(r)
            sc = random.uniform(1.0, 1.8); r.scale = (sc * 1.2, sc, sc * 0.8); r.location = (p.x, p.y, random.uniform(-0.6, 0.8))
            r.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
    if light:
        tw = C.cyl('mole-light', 1.0, 0.9, 6.0, 20, C.simple('lighthouse-white', '#f2f0ea', 0.6), (e.x, e.y, height_ + 3.0))
        C.cyl('mole-light-top', 0.75, 0.75, 1.4, 20, C.simple('lighthouse-red', '#c0261f', 0.5), (e.x, e.y, height_ + 6.7))

def far_sea_ring(inner=350.0, outer=9000.0, z=-0.003, color='#0c2e3a'):
    """Open sea from the edge of the water box out to the horizon (four strips round it, leaving the box clear)."""
    I, O = inner, outer
    rects = [(-O, -O, O, -I), (-O, I, O, O), (-O, -I, -I, I), (I, -I, O, I)]
    verts, faces = [], []
    for x0, y0, x1, y1 in rects:
        k = len(verts); verts += [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]; faces.append((k, k + 1, k + 2, k + 3))
    me = bpy.data.meshes.new('far-sea'); me.from_pydata(verts, [], faces); me.update()
    return C.obj('far-sea', me, K.sea_mat(color, False, far=True))

def bay_sea_mat(color='#0c2e3a', shallow='#2f9e98', reach=30.0):
    """The sea material from kit.sea_mat with the water turning turquoise over the sand near the beach."""
    m = K.sea_mat(color, True)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    old = b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].is_linked else None
    g = node(nt, 'ShaderNodeNewGeometry'); sp = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, g.outputs['Position'], sp.inputs['Vector'])
    x2 = math_(nt, 'MULTIPLY', sp.outputs['X'], sp.outputs['X'])
    shore = math_(nt, 'MULTIPLY_ADD', x2, -0.0022, 150.0)          # shore_y without its small wiggles
    d = math_(nt, 'SUBTRACT', shore, sp.outputs['Y'])               # metres out from the beach
    t = node(nt, 'ShaderNodeMapRange', in_From_Min=reach, in_From_Max=2.0); link(nt, d, t.inputs['Value'])
    base = old if old is not None else lin(color)
    link(nt, mixc(nt, t.outputs['Result'], base, lin(shallow)), b.inputs['Base Color'])
    return m
