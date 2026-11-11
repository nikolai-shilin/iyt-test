# Article bareboat-skipper/anchoring, figures 2, 3 and 9 in the Blender style:
#   --fig 2  how much chain: over/under cut-away at the waterline, 6 m of water, 35 m of chain in a catenary to the
#            Delta anchor dug into the sand (scope 5:1 on depth + bow height)
#   --fig 3  swing room: drone view of the yacht lying to an east wind, a 52 m swing circle round the anchor,
#            a rock 45 m east of the anchor breaking the surface
#   --fig 9  alongside: drone view of the yacht port side to a pontoon, bow and stern lines and two springs
#   blender --background --factory-startup --python docs/design/blender/art_anchoring_b.py -- --fig 2 --out ...
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix, noise as mnoise
import common as C, kit as K, kit_world as KW
from common import node, link, setin, math_, ramp, mixc, lin, new_mat, obj_coords, noise, bump_from

arg = C.cli(); FIG = arg('--fig', 2); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'anchoring')
OUT = arg('--out', os.path.join(OUTDIR, f'{FIG}-3d.jpg'))
C.reset()

def V3(p):
    """A Blender-space point as the Three.js-space object common.three_strand expects."""
    return C.V3((p.x, p.z, -p.y))

def flat_mat(name, color, emit=0.0, rough=0.5):
    m, nt, b, _ = new_mat(name)
    setin(b, 'Base Color', lin(color)); setin(b, 'Roughness', rough)
    if emit: setin(b, 'Emission Color', lin(color)); setin(b, 'Emission Strength', emit)
    return m

def dashes(points_fn, n, dash, gap, width, z, mat, name='dash', closed=True):
    """Flat dashes lying on the water along a path given by points_fn(s) for arc length s in [0, total)."""
    total = n * (dash + gap); me = C.rbox(name, (dash, width, 0.06), 0.02, 2)
    me.materials.append(mat)
    for k in range(n):
        s0 = k * (dash + gap) + dash / 2
        p, d = points_fn(s0)
        o = bpy.data.objects.new(name, me); C.col.objects.link(o)
        o.location = (p.x, p.y, z); o.rotation_euler = (0, 0, math.atan2(d.y, d.x))

def side_y(x, z, start=8.0, toward=-1):
    """The yacht's outboard surface facing +Y at (x, z), found by a ray cast."""
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((x, start, z)), Vector((0, toward, 0)))
    return loc.y if hit else None

# ===================================================================================================== fig 2
if FIG == 2:
    DEPTH, CHAIN = 6.0, 35.0
    y = K.load_yacht(); y.place(0, 0, heading=0)
    KW.antifoul_hull(y)
    bow = y.world((10.95, 0.13, 3.72))
    sb = -DEPTH + 0.07                                   # chain lying on the sand
    H = bow.z - sb
    # a catenary from the bow roller down to the touch-down point, the rest lying along the bottom
    X = 12.5; a = 5.0
    for _ in range(80):                                  # solve H = a (cosh(X/a) - 1) for a
        f = a * (math.cosh(X / a) - 1) - H; df = (math.cosh(X / a) - 1) - (X / a) * math.sinh(X / a)
        a -= f / df
    hang_len = a * math.sinh(X / a); lie_len = CHAIN - hang_len
    print('catenary a', round(a, 2), 'hanging', round(hang_len, 1), 'lying', round(lie_len, 1))
    hang = [Vector((0.0, bow.y + (X - x), sb + a * (math.cosh(x / a) - 1))) for x in (X * (1 - i / 160) for i in range(161))]
    touch = hang[-1]
    anc_y = touch.y + lie_len - 0.6
    lie = [Vector((0.25 * math.sin(t * 9) * t, touch.y + (anc_y - touch.y) * t, sb)) for t in (i / 120 for i in range(1, 121))]
    # the Delta anchor, dug in with its shank pointing back along the chain
    root, objs = K.load_model('anchor-delta.glb', drop_planes=False)
    S = Matrix.Diagonal((1.7, 1.7, 1.7, 1.0))
    ang = 48 + (270 - math.degrees(math.atan2(-2.2, -2.6)) % 360)
    end = lie[-1]
    root.matrix_world = Matrix.Translation((0, 0, 0)) @ Matrix.Rotation(math.radians(ang), 4, 'Z') @ S @ Matrix.Translation((-0.48, -1.17, 0.0))
    bpy.context.view_layer.update()
    shackle = root.matrix_world @ Vector((0.48, 1.17, 0.52))
    root.matrix_world = Matrix.Translation((end.x - shackle.x, end.y - shackle.y + 0.05, 0)) @ root.matrix_world
    bpy.context.view_layer.update(); alo, ahi = K.bbox(objs)
    root.location.z += (-DEPTH - 0.25) - alo.z
    KW.chain(hang + lie, link_len=0.2, wire=0.028)   # drawn heavier than life so it reads at this distance
    # the water, the seabed, stones and seagrass over the length of the scene
    KW.water_body(depth=14.0, size=700.0, density=0.02, color='#0f4a4f', absorb='#2f8f86', reflect=0.25, absorb_density=0.035, center=(0, 15))
    KW.far_sea_ring(inner=350.0)
    KW.seabed(z=-DEPTH, size=170.0, res=260, center=(0, 18), colors=('#7d8669', '#99a07e', '#8b9274'))
    KW.stones(60, ((-16, -12), (-3, 52)), -DEPTH, scale=(0.15, 0.6))
    KW.seagrass(((-22, -14), (-3, 56)), -DEPTH, clumps=1400, length=0.65)   # behind the chain only
    # the near sand, below every sight line to the chain: stones and seagrass give the floor its depth
    KW.stones(70, ((7, -14), (26, 52)), -DEPTH, seed=8, scale=(0.15, 0.55))
    KW.seagrass(((7, -16), (26, 58)), -DEPTH, clumps=1600, seed=9, length=0.6)
    K.coast(distance=1500, bearing=270, height=90, town=False)
    K.day_sky(sun_az=120, sun_el=55, strength=0.25, haze=2.0)
    mid_y = (-10.5 + anc_y + 2.5) / 2
    KW.camera(Vector((34.0, mid_y, 0.002)), Vector((0.0, mid_y, -1.7)), lens=21)
    gy = bow.y + 4.5; gx = 2.0
    k = len(hang) // 2; cm = hang[k]
    labels = [((bow.x, bow.y + 0.3, bow.z + 0.4), 'bow roller 1 m above water'),
              ((0.0, bow.y + 22.0, 0.05), 'waterline'),
              ((gx, gy - 3.2, -DEPTH / 2 - 0.2), 'depth 6 m', 'blue'),
              ((0.0, touch.y + lie_len * 0.35, -DEPTH + 0.2), 'chain 35 m · 5 × (6 + 1)', 'blue')]
    arrows = [((gx, gy, -2.8), (gx, gy, -0.05), 'blue'), ((gx, gy, -2.8), (gx, gy, -DEPTH + 0.05), 'blue')]
    C.render(OUT, SAMPLES, SCALE, -0.55, labels, '(6 m + 1 m) × 5 = 35 m', space='blender', arrows=arrows)

# ===================================================================================================== fig 3
elif FIG == 3:
    R_SWING = 52.0
    K.sea('calm', size=40.0, repeat=12)
    y = K.load_yacht(name='at-anchor'); y.place(-46.0 + 1.43, 0.0, heading=90)    # boat centre 46 m west, bow to the east wind
    # the swing circle: yellow dashes on the water, the rode as dark dashes from the bow to the anchor
    yel = flat_mat('swing', '#ffbf00', emit=0.4)
    def circ(s):
        t = s / R_SWING; return Vector((R_SWING * math.cos(t), R_SWING * math.sin(t), 0)), Vector((-math.sin(t), math.cos(t), 0))
    dashes(circ, 46, 4.0, 3.1, 0.7, 0.16, yel, 'swing')
    bow = y.world((10.83, 0.13, 2.1))
    ink = flat_mat('rode', '#1b1d20', rough=0.8)
    L0 = abs(bow.x)
    dashes(lambda s: (Vector((bow.x + s, 0, 0)), Vector((1, 0, 0))), int(L0 / 2.2), 1.2, 1.0, 0.25, 0.14, ink, 'rode')
    # an orange tripping-line buoy marks where the anchor lies
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.45)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new('anchor-buoy'); bm.to_mesh(me); bm.free()
    C.obj('anchor-buoy', me, C.simple('buoy-orange', '#ff6a00', 0.35, coat=0.5), (0.0, 0.0, 0.15))
    # the rock: a few weathered boulders breaking the surface, a ring of white water round them
    rm, nt, b, _ = new_mat('rock')
    oc = obj_coords(nt); z = KW.world_z(nt)
    c = ramp(nt, [(0.3, '#4a463f'), (0.55, '#6d675c'), (0.8, '#8b8475')]); link(nt, noise(nt, oc, 1.2, 6.0), c.inputs['Fac'])
    wet = node(nt, 'ShaderNodeMapRange', in_From_Min=0.15, in_From_Max=0.6, in_To_Min=1.0, in_To_Max=0.0); link(nt, z, wet.inputs['Value'])
    weed = mixc(nt, wet.outputs['Result'], c.outputs['Color'], lin('#2f3322'))
    link(nt, weed, b.inputs['Base Color'])
    rr = node(nt, 'ShaderNodeMix', data_type='FLOAT'); link(nt, wet.outputs['Result'], rr.inputs['Factor']); setin(rr, 2, 0.85); setin(rr, 3, 0.25); link(nt, rr.outputs[0], b.inputs['Roughness'])
    bump_from(nt, b, noise(nt, oc, 3.0, 8.0), 0.8, 0.08)
    random.seed(11)
    for i, (dx, dy, r, top) in enumerate([(0, 0, 2.4, 1.3), (2.6, 1.2, 1.6, 0.7), (-2.2, -1.0, 1.7, 0.5), (1.0, -2.3, 1.2, 0.3), (-1.0, 2.4, 1.1, 0.25), (3.4, -1.6, 0.8, 0.1)]):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=r)
        for v in bm.verts:
            v.co *= 1.0 + 0.22 * mnoise.noise(v.co * 0.9 + Vector((i * 5.0, 0, 0))) + 0.08 * mnoise.noise(v.co * 3.0)
            v.co.z *= 0.75
        for f in bm.faces: f.smooth = True
        me = bpy.data.meshes.new('rock'); bm.to_mesh(me); bm.free()
        C.obj('rock', me, rm, (45.0 + dx, dy, top - r * 0.75)).rotation_euler = (0, 0, random.uniform(0, 6.28))
    fm, nt, b, out = new_mat('rock-foam')
    oc = obj_coords(nt); sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, sep.inputs['Vector'])
    rad = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', sep.outputs['X'], sep.outputs['X']), math_(nt, 'MULTIPLY', sep.outputs['Y'], sep.outputs['Y'])))
    ring = node(nt, 'ShaderNodeMapRange', in_From_Min=6.5, in_From_Max=2.5); link(nt, rad, ring.inputs['Value'])
    nz = ramp(nt, [(0.45, (0, 0, 0, 1)), (0.65, (1, 1, 1, 1))]); link(nt, noise(nt, oc, 0.9, 8.0), nz.inputs['Fac'])
    msk = math_(nt, 'MULTIPLY', ring.outputs['Result'], nz.outputs['Color'])
    setin(b, 'Base Color', lin('#eef3f4')); setin(b, 'Roughness', 0.8)
    tp = node(nt, 'ShaderNodeBsdfTransparent'); mx = node(nt, 'ShaderNodeMixShader')
    link(nt, msk, mx.inputs['Fac']); link(nt, tp.outputs[0], mx.inputs[1]); link(nt, b.outputs[0], mx.inputs[2]); link(nt, mx.outputs[0], out.inputs['Surface'])
    pm = bpy.data.meshes.new('foam'); pm.from_pydata([(-8, -8, 0), (8, -8, 0), (8, 8, 0), (-8, 8, 0)], [], [(0, 1, 2, 3)])
    C.obj('foam', pm, fm, (45.0, 0.0, 0.14)).visible_shadow = False
    K.day_sky(sun_az=200, sun_el=50)
    KW.camera(Vector((-6.0, -100.0, 82.0)), Vector((-2.0, 4.0, 0.0)), lens=32)
    labels = [((0.0, R_SWING, 1.0), 'swing circle · 52 m', 'blue'), ((0.0, 0.0, 0.6), 'anchor'), ((45.0, 0.0, 3.2), 'rock · 45 m'),
              ((92.0, 36.0, 10.0), 'Wind E, going W', 'red')]
    arrows = [((92.0, 30.0, 10.0), (64.0, 30.0, 10.0), 'red')]
    C.render(OUT, SAMPLES, SCALE, -0.6, labels, 'Chain 40 m in 5 m, boat 13 m: she swings 52 m round the anchor', space='blender', arrows=arrows)

# ===================================================================================================== fig 9
else:
    K.sea('calm', size=30.0, repeat=8)
    y = K.load_yacht(name='alongside'); y.place(1.43, 0.0, heading=90)     # bow east, port side to the pontoon (north)
    bpy.context.view_layer.update()
    out_y = max(v for v in (side_y(x, z) for x in (-2, 1, 4) for z in (0.3, 0.8, 1.3)) if v is not None)
    edge = out_y + 0.26                                   # pontoon edge: a fender's width off her widest point
    W_P, TOP = 2.4, 0.45
    M = K.mats()
    # the pontoon: a concrete float, cross planks, a rubber rubbing strip along the edge
    C.tbox((52.0, 0.8, W_P - 0.1), (0.0, -0.05, -(edge + W_P / 2)), K.mats()['float'], 0.08, 2, 'float')
    plank_me = C.rbox('plank', (0.14, W_P, 0.035), 0.004, 1); plank_me.materials.append(M['planks'])
    x = -26.0
    while x < 26.0:
        o = bpy.data.objects.new('plank', plank_me); C.col.objects.link(o)
        o.location = (x, edge + W_P / 2, TOP - 0.0175); x += 0.155
    C.tbox((52.0, 0.12, 0.07), (0.0, TOP - 0.11, -(edge + 0.02)), M['rubber'], 0.02, 2, 'rubbing-strip')
    def cleat_at(px):
        p = Vector((px, edge + 0.32, TOP))
        C.cyl('cleat-horn', 0.022, 0.022, 0.34, 20, M['galv'], p + Vector((0, 0, 0.085)), (0, math.pi / 2, 0))
        for dx in (-0.07, 0.07): C.cyl('cleat-leg', 0.025, 0.032, 0.08, 16, M['galv'], p + Vector((dx, 0, 0.04)))
        return p + Vector((0, 0, 0.09))
    P = {k: cleat_at(px) for k, px in (('bow', 11.5), ('stern', -11.5))}
    # fenders between hull and pontoon
    sock = C.fabric_mat('fender-sock', '#1e2f55', '#5d75a8', 1400.0)
    for fx in (-3.0, 1.5, 5.0):
        hy = max(v for v in (side_y(fx, z, start=edge - 0.01) for z in (0.25, 0.45, 0.7)) if v is not None)
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.11)
        for v in bm.verts: v.co.z += 0.2 if v.co.z > 0 else (-0.2 if v.co.z < 0 else 0)
        for f in bm.faces: f.smooth = True
        me = bpy.data.meshes.new('fender'); bm.to_mesh(me); bm.free()
        C.obj('fender', me, sock, (fx, hy + 0.115, 0.42))
    # the lines: off her cleats, over the toe rail, sagging down to the pontoon cleats
    def line(name, boat_pt, cleat_pt, sag=0.25, color='#1b2c4c'):
        bp = Vector(boat_pt); ey = side_y(bp.x, 1.45, start=edge - 0.01)
        over = Vector((bp.x + (cleat_pt.x - bp.x) * 0.06, (ey if ey is not None else bp.y) + 0.04, 1.58))
        pts = [bp + Vector((0, 0, 0.03)), over]
        for t in (0.2, 0.4, 0.6, 0.8):
            q = over.lerp(cleat_pt, t); q.z -= math.sin(t * math.pi) * sag; pts.append(q)
        pts.append(cleat_pt + Vector((0, -0.02, 0.0)))
        C.braid(name, [V3(p) for p in pts], 0.022, color, '#e9e3d2', whip='#141414', fine=1.4)   # thick enough to read from the drone
        return pts
    bowc, midc, stc = y.world((8.9, 0.84, 3.58)), y.world((3.66, 2.25, 3.58)), y.world((-1.46, 2.05, 3.58))
    P['mid'] = cleat_at((bowc.x + stc.x) / 2)             # abreast her middle: both springs go to it
    lb = line('bow-line', bowc, P['bow'])
    ls = line('stern-line', stc, P['stern'])
    # the springs from her bow and stern cleats to the one pontoon cleat abreast her middle (as a reviewer asked):
    # the one from the bow runs aft and stops her surging forward, the one from the stern runs forward and stops her going astern
    lf = line('fwd-spring', bowc + Vector((-0.12, 0, 0)), P['mid'] + Vector((0.06, 0, 0)), 0.15, '#e2601e')   # springs in orange
    la = line('aft-spring', stc + Vector((0.12, 0, 0)), P['mid'] + Vector((-0.06, 0, 0)), 0.15, '#e2601e')
    K.day_sky(sun_az=330, sun_el=48)                       # sun behind the camera: no glare, her side lit
    KW.camera(Vector((-1.0, 19.0, 12.0)), Vector((0.5, 0.2, 0.9)), lens=36)   # from over the pontoon: the lines lie in front
    labels = [(tuple(lb[3] + Vector((0, 0, 0.3))), 'bow line'), (tuple(ls[3] + Vector((0, 0, 0.3))), 'stern line'),
              (tuple(lf[4] + Vector((0, 0, 0.3))), 'spring', 'blue'), (tuple(la[4] + Vector((0, 0, 0.3))), 'spring', 'blue')]
    C.render(OUT, SAMPLES, SCALE, -0.6, labels, 'Alongside: breast lines hold, springs stop the surge', space='blender')
