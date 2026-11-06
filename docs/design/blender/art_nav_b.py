# Article bareboat-skipper/navigation, figures 2, 4, 7, 9 and 10 in the Blender style:
#   --fig 2   a drying rock showing 0.9 m above a calm sea, from our foredeck
#   --fig 4   position fixing: a hand-bearing compass on the coaming, a coast with a lighthouse, a tower, a headland
#   --fig 7   depth over a shoal: an over/under cut-away, charted 1.5 m + tide 1.2 m = 2.7 m, keel 1.9 m
#   --fig 9   leading marks: front low, rear high, in line ahead between the harbour moles
#   --fig 10  clearing line: a church on the hillside, a reef with breaking water, our yacht passing south of it
#   blender --background --factory-startup --python docs/design/blender/art_nav_b.py -- --fig 2 [--out ...]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix, noise as mnoise
import common as C, kit as K, kit_world as KW
from common import node, link, setin, math_, ramp, mixc, lin, new_mat, obj_coords, noise, bump_from

arg = C.cli(); FIG = arg('--fig', 2); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'navigation')
OUT = arg('--out', os.path.join(OUTDIR, f'{FIG}-3d.jpg'))
C.reset()

def deg(a): return math.radians(a)
def pol(brg, d, z=0.0, at=(0, 0)): return Vector((at[0] + d * math.sin(deg(brg)), at[1] + d * math.cos(deg(brg)), z))

def flat_mat(name, color, emit=0.0, rough=0.5):
    m, nt, b, _ = new_mat(name)
    setin(b, 'Base Color', lin(color)); setin(b, 'Roughness', rough)
    if emit: setin(b, 'Emission Color', lin(color)); setin(b, 'Emission Strength', emit)
    return m

def ground_z(x, y, top=400.0):
    """Height of whatever lies under (x, y): land, mole or sea level."""
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((x, y, top)), Vector((0, 0, -1)))
    return max(loc.z, 0.0) if hit else 0.0

# ---------- rocks and white water ----------
def rock_mat():
    rm, nt, b, _ = new_mat('rock')
    oc = obj_coords(nt); z = KW.world_z(nt)
    c = ramp(nt, [(0.3, '#4a463f'), (0.55, '#6d675c'), (0.8, '#8b8475')]); link(nt, noise(nt, oc, 1.2, 6.0), c.inputs['Fac'])
    wet = node(nt, 'ShaderNodeMapRange', in_From_Min=0.05, in_From_Max=0.4, in_To_Min=1.0, in_To_Max=0.0); link(nt, z, wet.inputs['Value'])
    weed = mixc(nt, wet.outputs['Result'], c.outputs['Color'], lin('#2c3020'))
    link(nt, weed, b.inputs['Base Color'])
    rr = node(nt, 'ShaderNodeMix', data_type='FLOAT'); link(nt, wet.outputs['Result'], rr.inputs['Factor']); setin(rr, 2, 0.85); setin(rr, 3, 0.2); link(nt, rr.outputs[0], b.inputs['Roughness'])
    bump_from(nt, b, noise(nt, oc, 3.0, 8.0), 0.9, 0.06)
    return rm

def rock_cluster(at, parts, seed=11, squash=0.8):
    """Angular wet boulders: parts = [(dx, dy, radius, top above water), ...]."""
    rm = rock_mat(); random.seed(seed)
    for i, (dx, dy, r, top) in enumerate(parts):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=r)
        for v in bm.verts:
            v.co *= 1.0 + 0.25 * mnoise.noise(v.co * 0.9 / r + Vector((i * 5.0 + seed, 0, 0))) + 0.08 * mnoise.noise(v.co * 3.0 / r)
            v.co.z *= squash
        me = bpy.data.meshes.new('rock'); bm.to_mesh(me); bm.free()          # flat shaded: angular faces
        o = C.obj('rock', me, rm, (at[0] + dx, at[1] + dy, top - r * 0.8)); o.rotation_euler = (random.uniform(0, 0.4), random.uniform(0, 0.4), random.uniform(0, 6.28))
    return rm

def foam_ring(at, r_in, r_out, size, z=0.06, scale=0.9):
    """A ring of white water round a rock or a reef: a transparent decal floating on the sea."""
    fm, nt, b, out = new_mat('foam')
    oc = obj_coords(nt); sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, sep.inputs['Vector'])
    rad = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', sep.outputs['X'], sep.outputs['X']), math_(nt, 'MULTIPLY', sep.outputs['Y'], sep.outputs['Y'])))
    ring = node(nt, 'ShaderNodeMapRange', in_From_Min=r_out, in_From_Max=r_in); link(nt, rad, ring.inputs['Value'])
    nz = ramp(nt, [(0.42, (0, 0, 0, 1)), (0.62, (1, 1, 1, 1))]); link(nt, noise(nt, oc, scale, 8.0), nz.inputs['Fac'])
    msk = math_(nt, 'MULTIPLY', ring.outputs['Result'], nz.outputs['Color'])
    setin(b, 'Base Color', lin('#eef3f4')); setin(b, 'Roughness', 0.8)
    tp = node(nt, 'ShaderNodeBsdfTransparent'); mx = node(nt, 'ShaderNodeMixShader')
    link(nt, msk, mx.inputs['Fac']); link(nt, tp.outputs[0], mx.inputs[1]); link(nt, b.outputs[0], mx.inputs[2]); link(nt, mx.outputs[0], out.inputs['Surface'])
    s = size; pm = bpy.data.meshes.new('foam'); pm.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    o = C.obj('foam', pm, fm, (at[0], at[1], z)); o.visible_shadow = False
    return o

# ---------- landmarks ----------
def lighthouse(at, z0, h=26.0):
    white = flat_mat('lh-white', '#eeece6', rough=0.6); red = flat_mat('lh-red', '#b8261e', rough=0.45); black = flat_mat('lh-black', '#1a1b1d', rough=0.5)
    C.cyl('lh-tower', 2.6, 1.8, h, 32, white, (at[0], at[1], z0 + h / 2))
    C.cyl('lh-band', 2.25, 2.05, 3.0, 32, red, (at[0], at[1], z0 + h * 0.62))
    C.cyl('lh-gallery', 2.5, 2.5, 0.4, 32, black, (at[0], at[1], z0 + h + 0.2))
    C.cyl('lh-lantern', 1.4, 1.4, 2.4, 24, C.simple('lh-glass', '#2e3a40', 0.05, 0.3, coat=1.0), (at[0], at[1], z0 + h + 1.6))
    C.cyl('lh-dome', 1.5, 0.2, 1.2, 24, red, (at[0], at[1], z0 + h + 3.4))
    house = C.obj('lh-house', C.rbox('lhh', (10, 7, 5), 0.2, 2), white, (at[0] + 7, at[1] + 2, z0 + 2.5))

def watch_tower(at, z0, h=16.0):
    stone = C.granite_mat('tower-stone', base='#b9ad97', per_object=False, scale=0.15, dark='#8c826f', light='#d6ccb8', dirt=False)
    C.cyl('watch-tower', 6.0, 5.2, h, 32, stone, (at[0], at[1], z0 + h / 2))
    for k in range(10):     # crenellations
        a = k / 10 * math.tau
        C.obj('merlon', C.rbox('merlon', (1.8, 1.2, 1.8), 0.05, 1), stone, (at[0] + 4.9 * math.cos(a), at[1] + 4.9 * math.sin(a), z0 + h + 0.9)).rotation_euler = (0, 0, a)

def headland(at, size=(240, 140, 70), seed=5):
    """A high promontory pushed out from the coast: a noisy dome of dry land."""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=1.0)
    for v in bm.verts:
        n = mnoise.noise(v.co * 2.5 + Vector((seed, 0, 0)))
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) * (1.0 + 0.12 * n)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new('headland'); bm.to_mesh(me); bm.free()
    return C.obj('headland', me, KW.land_mat(), (at[0], at[1], -size[2] * 0.25))

def church(at, z0, rot=0.0):
    """A whitewashed Greek chapel: nave, a blue dome on a drum, a small bell gable."""
    white = flat_mat('church-white', '#f3f1ea', rough=0.7); blue = C.simple('church-dome', '#1e4fa0', 0.35, coat=0.4)
    root = bpy.data.objects.new('church', None); C.col.objects.link(root); root.location = (at[0], at[1], z0); root.rotation_euler = (0, 0, deg(rot))
    def put(o): o.parent = root; return o
    put(C.obj('nave', C.rbox('nave', (16, 9, 8), 0.3, 2), white, (0, 0, 4)))
    put(C.cyl('drum', 3.3, 3.3, 2.4, 32, white, (2, 0, 9.2)))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=3.4)
    for v in list(bm.verts):
        if v.co.z < 0: v.co.z = 0
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new('dome'); bm.to_mesh(me); bm.free(); put(C.obj('dome', me, blue, (2, 0, 10.4)))
    put(C.obj('gable', C.rbox('gable', (1.2, 4.0, 4.0), 0.1, 1), white, (-8.2, 0, 10)))
    put(C.cyl('cross', 0.12, 0.12, 1.6, 8, flat_mat('cross', '#d9c47a', rough=0.4), (2, 0, 14.4)))
    return root

def daymark(at, z_board, board=(3.0, 4.0), post_z0=0.0, stripe='#ffffff', bg='#f06a1a', name='mark'):
    """A leading-line daymark: an orange board with a vertical white stripe on a lattice post, facing south."""
    b = C.obj(name + '-board', C.rbox(name, (board[0], 0.2, board[1]), 0.02, 1), flat_mat(name + '-bg', bg, emit=0.15, rough=0.6), (at[0], at[1], z_board))
    C.obj(name + '-stripe', C.rbox(name + 's', (board[0] * 0.3, 0.05, board[1] * 0.98), 0.0, 1), flat_mat(name + '-st', stripe, emit=0.15, rough=0.6), (at[0], at[1] - 0.13, z_board))
    h = z_board - board[1] / 2 - post_z0; grey = C.simple(name + '-steel', '#3a3d40', 0.5, 0.6)
    for dx in (-0.8, 0.8):
        C.cyl(name + '-leg', 0.12, 0.12, h, 8, grey, (at[0] + dx, at[1], post_z0 + h / 2))
    for k in range(int(h / 2)):
        z = post_z0 + 1 + k * 2
        o = C.obj(name + '-brace', C.rbox('br', (2.2, 0.08, 0.08), 0.0, 1), grey, (at[0], at[1], z)); o.rotation_euler = (0, deg(38 if k % 2 else -38), 0)
    return b

def thin_fog(factor=3.0):
    """kit.coast fades land into haze by camera distance; on a near coast that washes it out: push the haze back."""
    m = bpy.data.materials.get('coast')
    for n in m.node_tree.nodes:
        if n.type == 'MATH' and n.operation == 'DIVIDE' and n.inputs[1].default_value < 0:
            n.inputs[1].default_value *= factor

def dashes(p0, p1, dash, gap, width, z, mat, name='dash'):
    """Glowing dashes floating just above the water along p0 -> p1 (a bearing drawn on the sea)."""
    d = (p1 - p0); L = d.length; u = d.normalized(); me = C.rbox(name, (dash, width, 0.08), 0.0, 1); me.materials.append(mat)
    for k in range(int(L / (dash + gap))):
        p = p0 + u * (k * (dash + gap) + dash / 2)
        o = bpy.data.objects.new(name, me); C.col.objects.link(o); o.location = (p.x, p.y, z); o.rotation_euler = (0, 0, math.atan2(u.y, u.x))
        o.visible_shadow = False

labels, arrows, note, expo = [], [], None, -0.6

# ===================================================================================================== fig 2
if FIG == 2:
    y = K.load_yacht(); y.place(0, 0, heading=0)
    K.sea('calm'); K.day_sky(sun_az=215, sun_el=38)
    R = (15.0, 44.0)
    rock_cluster(R, [(0, 0, 1.3, 0.9), (1.5, 0.6, 1.0, 0.55), (-1.4, -0.5, 1.0, 0.4), (0.6, -1.5, 0.8, 0.2), (-0.7, 1.4, 0.7, 0.12), (2.2, -1.0, 0.5, 0.0)], squash=1.25)
    foam_ring(R, 1.6, 4.8, 6.0, z=0.05, scale=1.6)
    K.coast(distance=900, bearing=8, height=110, town=True)
    eye = y.world((6.0, -0.55, 5.2)); look = Vector((R[0] - 3.0, R[1], 1.2))
    K.camera(eye, look, 50)
    labels = [((R[0], R[1], 2.5), 'rock · shows 0.9 m now', 'red')]
    note = 'Underlined 1.5 = drying height · tide 0.6 m'

# ===================================================================================================== fig 4
elif FIG == 4:
    y = K.load_yacht(); y.place(0, 0, heading=90)          # heading east, the coast to the north on her port side
    K.sea('calm', size=40.0, repeat=10); K.day_sky(sun_az=150, sun_el=40)
    D = 460.0
    K.coast(distance=D, bearing=2, length=5000, height=95, town=False)
    LH, TW, HL = pol(330, D + 40), pol(5, D + 70), pol(35, D - 60)
    headland((HL.x + 20, HL.y + 40), size=(150, 100, 55))
    bpy.context.view_layer.update()
    lighthouse((LH.x, LH.y), ground_z(LH.x, LH.y), 32.0)
    watch_tower((TW.x, TW.y), ground_z(TW.x, TW.y), 26.0)
    # the hand-bearing compass resting on the port cockpit coaming, close to the eye
    import kit_instruments as KI
    spot = y.world((-1.0, 1.48, 6.0)); bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, spot, Vector((0, 0, -1)))
    base = loc if hit else spot - Vector((0, 0, 1.8))
    print('compass on', base)
    dark = C.simple('hbc-body', '#16181b', 0.45, 0.2)
    C.cyl('hbc-body', 0.055, 0.05, 0.035, 48, dark, base + Vector((0, 0, 0.018)))
    card = KI.disc('hbc-card', 0.042, KI.image_mat('hbc-card', KI.face_png('card'), 0.4, emit=0.15), base + Vector((0, 0, 0.037)), normal='Z+')
    card.rotation_euler = (0, 0, deg(5))                # 005 under the lubber, the tower dead ahead of the sight
    bmc = bmesh.new(); bmesh.ops.create_uvsphere(bmc, u_segments=48, v_segments=24, radius=0.046)
    for v in list(bmc.verts):
        if v.co.z < 0: v.co.z = 0
    gme = bpy.data.meshes.new('hbc-dome'); bmc.to_mesh(gme); bmc.free(); gme.shade_smooth()
    C.obj('hbc-dome', gme, KI.glass_mat('hbc-glass'), base + Vector((0, 0, 0.036)))
    C.obj('hbc-sight', C.rbox('hbcs', (0.012, 0.03, 0.03), 0.003, 2), dark, base + Vector((0, 0.05, 0.05)))
    eye = y.world((-1.45, 0.75, 4.4)); look = eye + Vector((60, 900, -900 * math.tan(deg(9))))
    cam = K.camera(eye, look, 20)
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = 450.0; cam.data.dof.aperture_fstop = 5.6
    labels = [((LH.x, LH.y, ground_z(LH.x, LH.y) + 40), 'lighthouse 330°'), ((TW.x, TW.y, ground_z(TW.x, TW.y) + 26), 'tower 005°'),
              ((HL.x, HL.y, 50), 'headland 035°'), (tuple(base + Vector((0, 0, 0.09))), 'hand-bearing compass', 'blue')]
    note = 'Three bearings plotted'

# ===================================================================================================== fig 7
elif FIG == 7:
    DEPTH, TIDE, CHART, DRAFT = 2.7, 1.2, 1.5, 1.9
    y = K.load_yacht(); y.place(0, 0, heading=0)
    y.root.location.z = 2.0 - DRAFT
    KW.antifoul_hull(y)
    bpy.context.view_layer.update()
    keel = [o for o in y.objs if o.type == 'MESH' and not o.hide_render and K.bbox([o])[0].z < -DRAFT + 0.15]
    klo, khi = K.bbox(keel); kb = Vector(((klo.x + khi.x) / 2, (klo.y + khi.y) / 2, klo.z))
    print('keel bottom', kb)
    KW.water_body(depth=8.0, size=700.0, density=0.06, color='#0f4a4f', absorb='#3aa79b', reflect=0.25, absorb_density=0.07)
    KW.far_sea_ring(inner=350.0)
    KW.seabed(z=-DEPTH, size=140.0, res=220, center=(0, 10), seed=9, colors=('#9a9a7c', '#bdb895', '#aeab89'))
    KW.stones(60, ((-25, -20), (30, 45)), -DEPTH, scale=(0.12, 0.4))
    KW.seagrass(((-30, -25), (40, 50)), -DEPTH, clumps=1400, length=0.4)
    K.coast(distance=1300, bearing=270, height=60, town=False)
    K.day_sky(sun_az=120, sun_el=55, strength=0.25, haze=2.0)
    # chart datum: a dashed yellow line under the surface, the level the charted depths are measured from
    dashes(Vector((3.0, -10.0, 0)), Vector((3.0, 22.0, 0)), 0.7, 0.45, 0.06, -TIDE, flat_mat('datum', '#ffd21a', emit=3.0), 'datum')
    eye = Vector((13.0, 3.8, 0.002)); look = Vector((0.0, 4.4, -0.6))
    KW.camera(eye, look, lens=16)
    g1 = Vector((3.4, kb.y - 1.2, 0)); g2 = Vector((3.4, kb.y + 0.9, 0)); g3 = Vector((3.4, kb.y + 7.0, 0))
    labels = [((g1.x, g1.y - 1.9, -0.8), f'draft {DRAFT} m', 'yellow'), ((g2.x, g2.y + 2.4, -DRAFT - 0.35), '0.8 m under the keel', 'red'),
              ((g3.x, g3.y + 2.6, -TIDE * 0.45), f'tide {TIDE} m', 'blue'), ((g3.x, g3.y + 2.8, -TIDE - 0.85), f'charted {CHART} m', 'green'),
              ((3.0, 19.0, -TIDE + 0.12), 'chart datum')]
    mid = lambda a, b: (a + b) / 2
    arrows = [((g1.x, g1.y, -0.95), (g1.x, g1.y, -0.03), 'yellow'), ((g1.x, g1.y, -0.95), (g1.x, g1.y, -DRAFT + 0.03), 'yellow'),
              ((g2.x, g2.y, mid(-DRAFT, -DEPTH)), (g2.x, g2.y, -DRAFT - 0.02), 'red'), ((g2.x, g2.y, mid(-DRAFT, -DEPTH)), (g2.x, g2.y, -DEPTH + 0.02), 'red'),
              ((g3.x, g3.y, -TIDE / 2), (g3.x, g3.y, -0.03), 'blue'), ((g3.x, g3.y, -TIDE / 2), (g3.x, g3.y, -TIDE + 0.03), 'blue'),
              ((g3.x, g3.y, -TIDE - CHART / 2), (g3.x, g3.y, -TIDE - 0.03), 'green'), ((g3.x, g3.y, -TIDE - CHART / 2), (g3.x, g3.y, -DEPTH + 0.03), 'green')]
    note = 'Shoal at 14:00: 1.5 + 1.2 = 2.7 m · 0.8 m under the keel'
    expo = -0.55

# ===================================================================================================== fig 9
elif FIG == 9:
    y = K.load_yacht()
    y.place(0.0, -20.0, heading=0)                      # the foredeck eye exactly on the leading line x = 0
    K.sea('calm', size=40.0, repeat=10, center=(0, 120)); K.day_sky(sun_az=210, sun_el=35)
    K.coast(distance=380, bearing=0, length=4000, height=70, town=False, seed=6); thin_fog(4.0)
    KW.mole((-130, 400), (-45, 225), width=9.0, light=False); KW.mole((130, 400), (45, 225), width=9.0, light=False)
    for x, col in ((-45, 'red'), (45, 'green')):
        z = 2.2 + 3.0
        C.cyl('mole-tower', 1.0, 0.9, 6.0, 20, K.mats()['red' if col == 'red' else 'green'], (x, 225, z))
    bpy.context.view_layer.update()
    F, Rr = Vector((0, 420, 0)), Vector((0, 560, 0))
    fz, rz = ground_z(F.x, F.y), ground_z(Rr.x, Rr.y)
    print('ground front', fz, 'rear', rz)
    daymark(F, fz + 9.0, (4.0, 5.0), post_z0=fz, name='front')
    daymark(Rr, rz + 22.0, (5.0, 6.5), post_z0=rz, name='rear')
    eye = y.world((11.0, 0.13, 4.9)); look = Vector((0.0, 480.0, (fz + 9 + rz + 22) / 2 - 4))   # from just ahead of the stem: on the line
    K.camera(eye, look, 70)
    labels = [((0, 420, fz + 12.5), 'front, low'), ((0, 560, rz + 26.5), 'rear, high'), ((0, 120, 0.3), 'keep in line', 'blue')]
    note = 'Leading marks into the harbour'

# ===================================================================================================== fig 10
elif FIG == 10:
    y = K.load_yacht(); y.place(-80, 100, heading=90)
    K.sea('calm', size=40.0, repeat=12, center=(-60, 100)); K.day_sky(sun_az=200, sun_el=40)
    K.coast(distance=640, bearing=35, length=5000, height=110, town=False, seed=8); thin_fog(2.0)
    bpy.context.view_layer.update()
    CH = Vector((600, 520, 0)); cz = ground_z(CH.x, CH.y)
    print('church ground', cz)
    church((CH.x, CH.y), cz, rot=-30); bpy.data.objects['church'].scale = (1.5, 1.5, 1.5)
    REEF = CH - Vector((math.sin(deg(60)), math.cos(deg(60)), 0)) * 720
    rock_cluster((REEF.x, REEF.y), [(0, 0, 1.8, 0.8), (3.5, 1.5, 1.4, 0.5), (-3.8, -1.2, 1.5, 0.6), (7, -2, 1.1, 0.3), (-7, 2.5, 1.0, 0.25), (1.5, -4, 1.0, 0.35), (10, 1, 0.9, 0.15), (-10, -1, 0.9, 0.1)], seed=23, squash=1.0)
    foam_ring((REEF.x, REEF.y), 2.0, 20.0, 22.0, z=0.08, scale=1.0)
    # the clearing line: church bearing 060°T drawn on the sea from the reef's outer edge, out past our track
    p0 = REEF - Vector((math.sin(deg(60)), math.cos(deg(60)), 0)) * 20; p1 = CH - Vector((math.sin(deg(60)), math.cos(deg(60)), 0)) * 560
    dashes(p0 - (p1 - p0).normalized() * 160, p1, 7.0, 5.0, 1.4, 0.55, flat_mat('clear-line', '#ff2a1a', emit=8.0), 'clear')
    eye = y.world((-2.6, 1.3, 5.1)); look = eye + Vector((math.sin(deg(53)), math.cos(deg(53)), 0)) * 300 + Vector((0, 0, -4))
    K.camera(eye, look, 58)
    labels = [((CH.x, CH.y, cz + 26), 'church'), ((REEF.x, REEF.y, 3.0), 'reef · dries 0.6', 'red'), (tuple(REEF - (CH - REEF).normalized() * 45 + Vector((0, 0, 1.5))), 'clearing line 060°T', 'red')]
    note = 'Church bearing less than 060°T: south of the reef'

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows)
