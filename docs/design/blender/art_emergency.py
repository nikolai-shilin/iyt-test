# Article bareboat-skipper/emergency, figures 2-7, as Blender renders (figure 1 reuses the VHF radio render).
#   2  MAYDAY: the fixed VHF on 16, the red DISTRESS cover flipped open
#   3  position by radio: Cape Sounion light due north, seen from 2 miles south
#   4  a red hand flare burning on a yacht on our starboard bow
#   5  a distress signal: a person in a dinghy slowly raising and lowering both arms
#   6  man overboard, the final approach under sail: close reach, sheets eased, the casualty close to leeward
#   7  towing: our yacht tows another, the towline to a bridle from her bow cleats
#   blender --background --factory-startup --python docs/design/blender/art_emergency.py -- --fig 2 [--out x.jpg]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import common as C, kit as K

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'emergency')
arg = C.cli(); FIG = arg('--fig', 2); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
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

def emit_mat(name, rgb, strength):
    m, nt, b, out = C.new_mat(name)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = rgb + (1,); em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs['Surface']); return m

def sphere(name, r, mat, loc, seg=24):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.shade_smooth()
    return C.obj(name, me, mat, Vector(loc))

def limb(name, p0, p1, r, mat):
    """A capsule-ish cylinder from p0 to p1 (world space)."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o = C.cyl(name, r, r * 0.85, d.length, 12, mat, (p0 + p1) / 2)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    sphere(name + '-j', r, mat, p1, 12)
    return o

def person(at, heading=0.0, arms='up', scale=1.0, sit=0.0):
    """A minimal crew figure: orange lifejacket on a dark torso, a head, arms raised in a V or down."""
    at = Vector(at); s = scale
    skin = C.simple('skin', '#c8916b', 0.6); jacket = C.simple('lifejacket', '#f05a1a', 0.5); dark = C.simple('clothes', '#1f2a3a', 0.8)
    rot = Matrix.Rotation(math.radians(-heading), 3, 'Z')
    P = lambda x, y, z: at + rot @ (Vector((x, y, z)) * s)
    hip = 0.85 - sit
    if sit < 0.3:
        limb('leg-l', P(-0.1, 0, 0.0), P(-0.1, 0, hip), 0.07, dark); limb('leg-r', P(0.1, 0, 0.0), P(0.1, 0, hip), 0.07, dark)
    limb('torso', P(0, 0, hip), P(0, 0, hip + 0.55), 0.17, jacket)
    sphere('head', 0.11 * s, skin, P(0, 0, hip + 0.75))
    sh_l, sh_r = P(-0.2, 0, hip + 0.5), P(0.2, 0, hip + 0.5)
    if arms == 'up':
        limb('arm-l', sh_l, P(-0.5, 0, hip + 1.1), 0.05, jacket); limb('arm-r', sh_r, P(0.5, 0, hip + 1.1), 0.05, jacket)
    else:
        limb('arm-l', sh_l, P(-0.3, 0, hip + 0.05), 0.05, jacket); limb('arm-r', sh_r, P(0.3, 0, hip + 0.05), 0.05, jacket)

def T(p):
    return C.V3((p.x, p.z, -p.y))      # Blender -> Three.js space for common.braid / three_strand

def drone(c, D, az=180.0, el=37.0, k=2.5, lens=32.0):
    a, e = math.radians(az), math.radians(el); dist = k * D
    eye = Vector(c) + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * dist
    K.camera(tuple(eye), tuple(c), lens)

labels, arrows, note, extra, expo = [], [], None, None, -0.7
C.reset()

if FIG == 2:
    # the radio scene from fig_instruments.py --kind radio, with the DISTRESS cover flipped open
    import kit_instruments as KI
    M = K.mats()
    root, objs = K.load_model('radio-vhf-simrad-rs20s.glb', drop_planes=False)
    for o in objs:
        if o.type == 'MESH' and all(sl.material is None for sl in o.material_slots) and len(o.data.polygons) <= 4: o.hide_render = True
    KI.wall('bulkhead', -0.42, 0.40, -0.26, 0.30, 0.004, KI.joinery_mat())
    for o in objs:
        for sl in getattr(o, 'material_slots', []):
            m = sl.material
            if m and m.node_tree:
                b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if b: b.inputs['Roughness'].default_value = 0.62; b.inputs['Specular IOR Level'].default_value = 0.25
    for o in objs:
        if o.type != 'MESH': continue
        names = {sl.material.name for sl in o.material_slots if sl.material}
        if 'Material-7503' in names:
            mw = o.matrix_world.copy(); mw.translation.y -= 0.0006; o.matrix_world = mw
            old = next(sl.material for sl in o.material_slots if sl.material)
            img = next(n.image for n in old.node_tree.nodes if n.type == 'TEX_IMAGE')
            fm, fnt, fb, _ = C.new_mat('vhf-front'); tx = fnt.nodes.new('ShaderNodeTexImage'); tx.image = img
            uvn = fnt.nodes.new('ShaderNodeUVMap'); fnt.links.new(uvn.outputs['UV'], tx.inputs['Vector'])
            fnt.links.new(tx.outputs['Color'], fb.inputs['Base Color']); fb.inputs['Roughness'].default_value = 0.5
            # the display backlight: a touch of glow so the 16 reads
            fnt.links.new(tx.outputs['Color'], fb.inputs['Emission Color']); fb.inputs['Emission Strength'].default_value = 0.08
            for sl in o.material_slots: sl.material = fm
        if names & {'Fig30', '[Color M07]', '[Color_007]1'}:
            for sl in o.material_slots:
                bb = next((n for n in sl.material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if bb and not bb.inputs['Base Color'].is_linked: bb.inputs['Base Color'].default_value = (0.018, 0.019, 0.021, 1)
    # the DISTRESS button (photo px 712..810 x 378..465 over 170 x 90 mm): a red plastic cover hinged along its top,
    # flipped up and out; under it the button glows red
    px = lambda u, v: Vector((u / 999 * 0.17, 0.0, (1 - v / 531) * 0.09))
    c0, c1 = px(712, 378), px(810, 465); w, h = c1.x - c0.x, c0.z - c1.z
    hinge = Vector(((c0.x + c1.x) / 2, -0.002, c0.z + 0.001))
    cov_m, cnt, cb, _ = C.new_mat('distress-cover')
    cb.inputs['Base Color'].default_value = C.lin('#d0161c'); cb.inputs['Roughness'].default_value = 0.15
    cb.inputs['Transmission Weight'].default_value = 0.55; cb.inputs['IOR'].default_value = 1.49
    piv = bpy.data.objects.new('cover-hinge', None); C.col.objects.link(piv); piv.location = hinge
    cov = C.obj('cover', C.rbox('cover', (w * 1.1, 0.008, h * 1.1), 0.002, 2), cov_m, (0, -0.004, -h * 0.55))
    cov.parent = piv; piv.rotation_euler = (math.radians(-115), 0, 0)
    C.obj('distress-btn', C.rbox('btn', (w * 0.8, 0.004, h * 0.75), 0.0015, 2), emit_mat('btn-glow', (1.0, 0.08, 0.05), 2.5), ((c0.x + c1.x) / 2, -0.0025, (c0.z + c1.z) / 2))
    K.day_sky(sun_az=150, sun_el=40, strength=0.08)
    KI.area_light((0.5, -0.9, 0.55), (0.05, 0, 0.04), 7, 0.6)
    KI.area_light((-0.6, -0.8, 0.3), (0, 0, 0.04), 2, 1.0, (0.85, 0.9, 1.0))
    K.camera((0.17, -0.36, 0.14), (0.1, 0, 0.048), 50)
    labels = [(tuple(px(470, 160)), 'MAYDAY on 16', 'red'), (tuple(px(760, 470) + Vector((0, -0.01, 0))), 'DISTRESS cover open', 'red'),
              ((0.19, -0.05, 0.085), 'handset: press to talk')]
    note = 'MAYDAY ×3 · this is … · position · nature · help · persons aboard · OVER'; expo = -0.4

elif FIG == 3:
    # 2 M south of Cape Sounion, heading west along the coast; the cape due north, its light on the point,
    # the columns of the temple on the summit behind. The cape is brought in to ~1.3 km so it reads.
    y = K.load_yacht().place(0, 0, heading=275)
    K.sea('breeze'); K.day_sky(sun_az=230, sun_el=32)
    D = 1100.0
    rnd = random.Random(5)
    # the headland: a rounded rocky promontory pointing south, cliffs to the sea
    verts, faces = [], []; nx, ny = 90, 50
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = (i / nx - 0.5) * 1600; yy = D - 60 + j / ny * 900
            r = math.hypot(x / 300, (yy - D - 260) / 330)
            z = 75 * max(0, 1 - r ** 1.6) + 4 * math.sin(x * 0.03) * math.sin(yy * 0.025) - 6
            z += 30 * max(0, 1 - math.hypot(x / 650, (yy - D - 700) / 260) ** 2)     # higher land behind
            verts.append((x, yy, z))
    for j in range(ny):
        for i in range(nx):
            k = j * (nx + 1) + i; faces.append((k, k + 1, k + nx + 2, k + nx + 1))
    me = bpy.data.meshes.new('cape'); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
    m, nt, b, out = C.new_mat('cape-rock')
    oc = C.obj_coords(nt); sep = C.node(nt, 'ShaderNodeSeparateXYZ'); C.link(nt, oc, sep.inputs['Vector'])
    n1 = C.noise(nt, oc, 0.02, 6.0)
    rock = C.ramp(nt, [(0.3, '#6f6656'), (0.6, '#8d8370'), (0.8, '#5f6248')]); C.link(nt, n1, rock.inputs['Fac'])
    scrub = C.ramp(nt, [(0.35, (1, 1, 1, 1)), (0.65, C.lin('#6c7350'))]); C.link(nt, C.noise(nt, oc, 0.18, 6.0), scrub.inputs['Fac'])
    C.link(nt, C.mixc(nt, 1.0, rock.outputs['Color'], scrub.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.95
    C.bump_from(nt, b, C.noise(nt, oc, 0.3, 8.0), 0.6, 1.0)
    K.distance_fog(nt, b.outputs[0], out.inputs['Surface'], half=4000.0)
    C.obj('cape', me, m)
    # the temple of Poseidon: a stylobate and two rows of white columns on the summit
    marble = C.simple('marble', '#e9e3d4', 0.6)
    top = Vector((0, D + 260, 0))
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, top + Vector((0, 0, 500)), Vector((0, 0, -1))); zt = loc.z if hit else 60
    C.tbox((32, 1.5, 15), (top.x, zt + 0.5, -top.y), marble, 0.1, 1, 'stylobate')
    for side in (-6.5, 6.5):
        for k in range(9):
            C.cyl('column', 0.65, 0.55, 6.2, 12, marble, (top.x - 15 + k * 3.7, top.y + side, zt + 1.2 + 3.1))
    for k in range(3):
        C.cyl('column', 0.65, 0.55, 6.2, 12, marble, (top.x - 15 + k * 3.7, top.y, zt + 1.2 + 3.1))
    C.tbox((18, 0.9, 1.4), (top.x - 8, zt + 7.8, -(top.y + 6.5)), marble, 0.05, 1, 'architrave')
    # the light: a small white tower with a lantern on the point of the cape, low by the sea
    pt = Vector((0, D - 10, 0))
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, pt + Vector((0, 0, 500)), Vector((0, 0, -1))); zp = max(loc.z if hit else 8, 6)
    C.cyl('lt-tower', 2.0, 1.6, 9.0, 24, C.simple('lt-white', '#f2f0ea', 0.5), (pt.x, pt.y, zp + 4.5))
    C.cyl('lt-lantern', 1.5, 1.5, 2.0, 24, C.simple('lt-glass', '#2b3036', 0.2, 0.4), (pt.x, pt.y, zp + 10))
    C.cyl('lt-roof', 1.7, 0.2, 1.4, 24, C.simple('lt-roof', '#7a1d18', 0.5), (pt.x, pt.y, zp + 11.7))
    # from the starboard side deck amidships, looking over the starboard rail to the north (the boat heads west)
    eye = y.world((4.0, -1.5, 5.0)); look = Vector((0, D + 120, 42))
    K.camera(tuple(eye), tuple(look), 150)
    labels = [((pt.x, pt.y, zp + 16), 'Sounion lt · bearing 000°'), ((top.x, top.y, zt + 14), 'temple of Poseidon')]
    note = '180° from Cape Sounion light, 2 miles'

elif FIG == 4:
    # dusk; a yacht on our starboard bow at ~180 m with a red hand flare held up in her cockpit
    you = K.load_yacht(name='you').place(0, 0, heading=0)
    K.sea('breeze'); K.day_sky(sun_az=300, sun_el=3, strength=0.2)
    rel, d = 40, 180.0
    ox, oy = d * math.sin(math.radians(rel)), d * math.cos(math.radians(rel))
    oth = K.load_yacht(name='other', sails={'main': True, 'genoa': 'starboard', 'boom': -20}).place(ox, oy, heading=270, heel=6)
    fp = oth.world((-1.6, 0.9, 5.4))
    sphere('flare', 0.35, emit_mat('flare-core', (1.0, 0.06, 0.02), 35.0), fp)
    ld = bpy.data.lights.new('flare-light', 'POINT'); ld.energy = 2500; ld.color = (1.0, 0.18, 0.08); ld.shadow_soft_size = 0.3
    lo = bpy.data.objects.new('flare-light', ld); C.col.objects.link(lo); lo.location = fp
    # the smoke: a leaning plume, lit red from below
    sm_m, snt, _, sout = C.new_mat('flare-smoke'); snt.nodes.remove(next(n for n in snt.nodes if n.type == 'BSDF_PRINCIPLED'))
    pv = snt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (0.95, 0.55, 0.5, 1)
    tc = snt.nodes.new('ShaderNodeTexCoord'); sepz = snt.nodes.new('ShaderNodeSeparateXYZ'); snt.links.new(tc.outputs['Generated'], sepz.inputs['Vector'])
    nz = snt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 4.0; nz.inputs['Detail'].default_value = 6.0; snt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    fall = snt.nodes.new('ShaderNodeMath'); fall.operation = 'SUBTRACT'; fall.inputs[0].default_value = 1.0; snt.links.new(sepz.outputs['Z'], fall.inputs[1])
    dens = snt.nodes.new('ShaderNodeMath'); dens.operation = 'MULTIPLY'; snt.links.new(nz.outputs['Fac'], dens.inputs[0]); snt.links.new(fall.outputs[0], dens.inputs[1])
    dens2 = snt.nodes.new('ShaderNodeMath'); dens2.operation = 'MULTIPLY'; dens2.inputs[1].default_value = 10.0; snt.links.new(dens.outputs[0], dens2.inputs[0])
    snt.links.new(dens2.outputs[0], pv.inputs['Density']); snt.links.new(pv.outputs[0], sout.inputs['Volume'])
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.6, radius2=3.0, depth=14)
    me = bpy.data.meshes.new('plume'); bm.to_mesh(me); bm.free()
    pl = C.obj('plume', me, sm_m, fp + Vector((2.5, 0, 7.0))); pl.rotation_euler = (0, math.radians(-22), 0)   # blown downwind to the east
    eye = you.world((6.6, -0.6, 5.3)); look = Vector((ox * 0.85, oy * 0.85, 6.0))
    K.camera(tuple(eye), tuple(look), 45)
    labels = [(tuple(fp + Vector((0, 0, 6))), 'red hand flare', 'red')]
    note = 'Red hand flare from this yacht, nothing on the radio'; extra = {'bloom': 1.0}; expo = -0.4

elif FIG == 5:
    # a small inflatable at ~70 m on our starboard bow, a person standing in it raising both arms
    you = K.load_yacht(name='you').place(0, 0, heading=0)
    K.sea('calm'); K.day_sky(sun_az=210, sun_el=35)
    rel, d = 30, 70.0
    ox, oy = d * math.sin(math.radians(rel)), d * math.cos(math.radians(rel))
    root, objs = K.load_model('tender-rib.glb')
    M = K.mats()
    def rule(c, name):
        if c is None: return None
        l = sum(c) / 3
        return M['dark'] if l < 0.2 else C.simple('tube-grey', '#9aa0a6', 0.55) if l > 0.6 else None
    K.recolor(objs, rule)
    bpy.context.view_layer.update(); vis = [o for o in objs if o.type == 'MESH' and not o.hide_render]; lo, hi = K.bbox(vis)
    root.rotation_euler = (0, 0, math.radians(-110))
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    root.location = (root.location.x + ox - (lo.x + hi.x) / 2, root.location.y + oy - (lo.y + hi.y) / 2, root.location.z - lo.z - 0.35)
    bpy.context.view_layer.update(); lo, hi = K.bbox(vis)
    person(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + 0.45), heading=200, arms='up')
    eye = you.world((6.4, -0.7, 5.2)); look = Vector((ox, oy, 1.4))
    K.camera(tuple(eye), tuple(look), 120)
    labels = [((ox, oy, 3.2), 'arms raised and lowered: I need help', 'red')]
    note = 'A distress signal · turn towards them, keep them in sight'

elif FIG == 6:
    # wind N; the yacht on a close reach heading 300, sheets eased (boom out to port, the leeward side);
    # the casualty in a lifebuoy close to leeward of her bow, the dan buoy thrown after them
    K.sea('breeze', size=40.0, repeat=12); K.day_sky(sun_az=200, sun_el=45)
    y = K.load_yacht(name='you', sails={'main': True, 'genoa': 'port', 'boom': 30}).place(0, 0, heading=300, heel=-6)
    K.wake(y, 22, 6, 0.6)
    mob = y.world((K.MAST.x + 14.0, K.MAST.y + 3.2, K.WL)); mob.z = 0.0
    lb = K.load_model('lifebuoy.glb')[0]; lb.location = mob + Vector((0, 0, 0.02))
    skin = C.simple('skin', '#c8916b', 0.6); jacket = C.simple('lifejacket', '#f05a1a', 0.5)
    sphere('mob-head', 0.13, skin, mob + Vector((0, 0, 0.32))); sphere('mob-shoulders', 0.24, jacket, mob + Vector((0, 0, 0.06)))
    K.dan_buoy(tuple(y.world((K.MAST.x + 8.0, K.MAST.y + 9.0, K.WL)).xy))
    c = (mob + y.world((K.MAST.x, K.MAST.y, K.WL))) / 2; c.z = 0
    drone(c, 18.0, az=150, el=40, k=2.1, lens=35)
    # wind arrow from the north, to the right of the scene as the camera sees it
    w0 = c + Vector((12, 10, 4)); w1 = c + Vector((12, 2, 3))
    arrows = [(tuple(w0), tuple(w1), 'blue')]
    labels = [(tuple(mob + Vector((0, 0, 1.6))), 'MOB', 'red'), (tuple(y.world((K.MAST.x - 3.0, K.MAST.y, 10.0))), 'close reach, sheets eased', 'blue'), (tuple(w0 + Vector((0, 0, 1.5))), 'Wind', 'blue')]
    note = 'Final approach under sail: close reach, sheets eased'

else:  # FIG 7
    # our yacht motoring north towing another; the towline from our stern to a bridle on her bow cleats
    K.sea('breeze', size=40.0, repeat=12); K.day_sky(sun_az=210, sun_el=45)
    L = 45.0
    you = K.load_yacht(name='you').place(0, 0, heading=0)
    tow = K.load_yacht(name='tow', hull='navy').place(0, -L - 14.6, heading=0)
    K.wake(you, 40, 9, 1.0); K.wake(tow, 30, 7, 0.6)
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    def deck(yt, mx, my):
        p = yt.world((mx, my, 8.0)); hit, loc, *_ = bpy.context.scene.ray_cast(dg, p, Vector((0, 0, -1)))
        return loc if hit else yt.world((mx, my, 3.6))
    stern = deck(you, -3.2, K.MAST.y) + Vector((0, 0, 0.15))
    bl = deck(tow, 9.0, K.MAST.y + 0.75) + Vector((0, 0, 0.08)); br = deck(tow, 9.0, K.MAST.y - 0.75) + Vector((0, 0, 0.08))
    stem = tow.world((10.7, K.MAST.y, 4.0))
    apex = stem + Vector((0, 4.0, -1.4))
    def sag(a, b, n, s):
        return [a.lerp(b, i / n) - Vector((0, 0, s * math.sin(math.pi * i / n))) for i in range(n + 1)]
    line_pts = sag(stern, apex, 14, 1.1)
    C.three_strand('towline', [T(p) for p in line_pts], 0.012, 0.07)
    for nm, cl in (('bridle-l', bl), ('bridle-r', br)):
        C.three_strand(nm, [T(p) for p in [cl, cl.lerp(stem, 0.6) + Vector((0, 0, 0.05)), stem + Vector((0, 0.3, 0)) + (cl - stem) * 0.1, apex]], 0.011, 0.07)
    c = stern.lerp(stem, 0.6); c.z = 0
    drone(c, 32.0, az=120, el=38, k=2.5, lens=35)
    mid = line_pts[len(line_pts) // 2]
    labels = [(tuple(mid + Vector((0, 0, 1.5))), 'towline'), (tuple(apex + Vector((0, 0, 2.0))), 'bridle', 'blue'),
              (tuple(tow.world((K.MAST.x, K.MAST.y, 12.0))), 'Tow'), (tuple(you.world((K.MAST.x, K.MAST.y, 12.0))), 'You', 'blue')]
    note = 'Towline to a bridle from both bow cleats'

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
