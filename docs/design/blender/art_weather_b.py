# Article bareboat-skipper/weather, figures 5, 6, 7, 9, 11 as Blender renders.
#   5  felt wind running: true 20 kn from astern, felt 13 kn (drone view)
#   6  felt wind close-hauled: true 20 kn, felt about 25 kn from further ahead (drone view)
#   7  a Navtex gale warning on the receiver at the nav station
#   9  funnelling between Evia and Andros: the strait much rougher at A than outside (aerial view)
#   11 a squall line coming from the west, seen from the helm with the sails down
# Run in Blender:  blender --background --factory-startup --python docs/design/blender/art_weather_b.py -- --fig 5
# Fig 7 draws its screen with Pillow first:  python3 docs/design/blender/art_weather_b.py --prep
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
NAVTEX_PNG = os.path.join(TEX, 'navtex-gale.png')

def prep_navtex():
    """The Navtex LCD: dark text on a pale green-grey screen, a header bar, the gale warning."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1200, 750
    im = Image.new('RGB', (W, H), (178, 196, 170)); d = ImageDraw.Draw(im)
    mono = '/System/Library/Fonts/Menlo.ttc'
    f = lambda n: ImageFont.truetype(mono, n)
    ink = (24, 32, 26)
    d.rectangle([0, 0, W, 92], fill=ink); d.text((28, 46), 'NAVTEX  518 kHz', font=f(54), fill=(178, 196, 170), anchor='lm')
    d.text((W - 28, 46), 'MSG 3/7', font=f(46), fill=(178, 196, 170), anchor='rm')
    lines = [('ZCZC JA42', 46), ('090900 UTC NOV', 58), ('GALE WARNING', 92), ('SOUTHERN AEGEAN', 72), ('N 8 IMMINENT', 92), ('NNNN', 46)]
    y = 140
    for t, s in lines:
        d.text((40, y), t, font=f(s), fill=ink); y += s + 26
    # LCD texture: faint pixel grid
    for x in range(0, W, 6): d.line([(x, 92), (x, H)], fill=(170, 188, 162), width=1)
    os.makedirs(TEX, exist_ok=True); im.save(NAVTEX_PNG); print('wrote', NAVTEX_PNG)

try:
    import bpy
except ImportError:
    if '--prep' in sys.argv: prep_navtex()
    sys.exit(0)

sys.path.insert(0, HERE)
import bmesh
from mathutils import Vector
import common as C, kit as K
from common import node, link, setin, math_, ramp, mixc, lin, new_mat, obj_coords, noise, bump_from

OUTDIR = os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'weather')
arg = C.cli(); FIG = arg('--fig', 5); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(OUTDIR, f'{FIG}-3d.jpg'))

_load = K.load_yacht
def _yacht(*a, **k):
    """kit.load_yacht minus the spinnaker's pale triangle and tack line the model keeps when the spinnaker is down."""
    yt = _load(*a, **k)
    for o in yt.objs:
        anc, q = [], o.parent
        while q: anc.append(q.name); q = q.parent
        if o.type == 'MESH' and (any(n.startswith('SPINNAKER') for n in anc) or
                                 any(sl.material and sl.material.name.startswith(('[Color_F12]', '[Color_H09]')) for sl in o.material_slots)):
            o.hide_render = True
    return yt
K.load_yacht = _yacht

def look_from(c, dist, az, el, lens):
    a, e = math.radians(az), math.radians(el)
    eye = Vector(c) + Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))) * dist
    return K.camera(tuple(eye), tuple(c), lens)

def dirv(frm):
    """Unit vector pointing where a wind FROM compass `frm` comes from (horizontal)."""
    a = math.radians(frm); return Vector((math.sin(a), math.cos(a), 0.0))

C.reset()
labels, arrows, note, expo, extra = [], [], None, -0.7, None

if FIG in (5, 6):
    if FIG == 5:     # running dead downwind: heading 180, wind from 000; boom well out to port
        y = K.load_yacht(name='you', sails={'main': True, 'genoa': 'port', 'boom': 62}); y.place(0, 0, heading=180, heel=3)
        K.sea('breeze', size=40.0, repeat=14); K.wake(y, 30, 7, 0.8)
        true_kn, felt_kn, felt_from, felt_dir_from = 20, 13, 0.0, 0.0
        note = 'Running · true 20 kn, boat 7 kn: 13 kn felt'
    else:            # close-hauled on port tack: heading 045, wind from 000; heeled, some spray
        y = K.load_yacht(name='you', sails={'main': True, 'genoa': 'starboard', 'boom': -9}); y.place(0, 0, heading=45, heel=22)
        K.sea('fresh', size=48.0, repeat=12); K.wake(y, 34, 9, 1.3)
        true_kn, felt_kn, felt_dir_from = 20, 25, 10.0
        note = 'Close-hauled · true 20 kn, boat 6 kn: about 25 kn felt'
    K.day_sky(sun_az=210, sun_el=42)
    mast = y.world((K.MAST.x, K.MAST.y, K.WL + 10.0)); base = Vector((mast.x, mast.y, 26.0))
    k = 1.25                                          # metres of arrow per knot
    side = Vector((-1, 0, 0)) if FIG == 5 else Vector((-0.7, 0.7, 0))
    t_end = base + side * 4.0; t_start = t_end + dirv(0) * true_kn * k
    f_end = base - side * 4.0 + Vector((0, 0, -3.0)); f_start = f_end + dirv(felt_dir_from) * felt_kn * k
    arrows = [(tuple(t_start), tuple(t_end), 'red'), (tuple(f_start), tuple(f_end), 'blue')]
    labels = [(tuple(t_start + Vector((0, 0, 1.5))), f'true {true_kn} kn', 'red'), (tuple(f_start + Vector((0, 0, 1.5))), f'felt {felt_kn} kn', 'blue')]
    # the boat's own motion, a yellow arrow along her heading ahead of the bow
    hd = math.radians(180 if FIG == 5 else 45); fw = Vector((math.sin(hd), math.cos(hd), 0))
    bow = y.world((11.5, K.MAST.y, K.WL + 1.0)); arrows.append((tuple(bow), tuple(bow + fw * (7 if FIG == 5 else 6) * k * 1.4), 'yellow'))
    labels.append((tuple(bow + fw * 13 + Vector((0, 0, 2))), f'boat {7 if FIG == 5 else 6} kn'))
    c = Vector((mast.x, mast.y, 9.0 if FIG == 5 else 13.0)) + (Vector((0, 8, 0)) if FIG == 5 else Vector((0, 5, 0)))
    look_from(c, 78, 95 if FIG == 5 else 120, 34, 34)

elif FIG == 7:
    import kit_instruments as KI
    if not os.path.exists(NAVTEX_PNG):
        import subprocess; subprocess.run(['python3', os.path.abspath(__file__), '--prep'], check=True)
    M = K.mats()
    KI.wall('bulkhead', -0.46, 0.40, -0.26, 0.30, 0.004, KI.joinery_mat())
    # the receiver: a dark grey case with a bevelled front, the LCD, six keys and a maker strip
    case = C.obj('navtex-case', C.rbox('nc', (0.215, 0.09, 0.145), 0.008, 3), C.simple('navtex-plastic', '#2b2e31', 0.55), (-0.17, -0.04, 0.03))
    bez = C.obj('navtex-bezel', C.rbox('nb', (0.150, 0.006, 0.098), 0.004, 2), C.simple('navtex-bezel', '#141516', 0.4), (-0.185, -0.0875, 0.045))
    scr = bpy.data.meshes.new('lcd'); sw, sh = 0.136, 0.085
    scr.from_pydata([(-sw / 2, 0, -sh / 2), (sw / 2, 0, -sh / 2), (sw / 2, 0, sh / 2), (-sw / 2, 0, sh / 2)], [], [(0, 1, 2, 3)])
    scr.uv_layers.new(name='UVMap'); scr.uv_layers[0].data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    C.obj('navtex-lcd', scr, KI.image_mat('navtex-lcd', NAVTEX_PNG, 0.25, emit=0.9), (-0.185, -0.0912, 0.045))
    for i in range(6):
        C.obj('key', C.rbox('k%d' % i, (0.016, 0.006, 0.011), 0.002, 2), C.simple('navtex-key', '#55595d', 0.5), (-0.247 + i * 0.0245, -0.0885, -0.016))
    C.obj('navtex-led', C.rbox('led', (0.006, 0.004, 0.006), 0.001, 1), C.simple('led', '#e02010', 0.3), (-0.083, -0.088, 0.083)).data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.0
    # the VHF beside it, as on the radio figure
    root, objs = K.load_model('radio-vhf-simrad-rs20s.glb', drop_planes=False)
    for o in objs:
        if o.type == 'MESH' and all(sl.material is None for sl in o.material_slots) and len(o.data.polygons) <= 4: o.hide_render = True
    for o in objs:
        if o.type != 'MESH': continue
        names = {sl.material.name for sl in o.material_slots if sl.material}
        for sl in o.material_slots:
            m = sl.material
            if m and m.node_tree:
                b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if b: b.inputs['Roughness'].default_value = 0.62; b.inputs['Specular IOR Level'].default_value = 0.25
        if 'Material-7503' in names:
            mw = o.matrix_world.copy(); mw.translation.y -= 0.0006; o.matrix_world = mw
            old = next(sl.material for sl in o.material_slots if sl.material)
            img = next(n.image for n in old.node_tree.nodes if n.type == 'TEX_IMAGE')
            fm, fnt, fb, _ = C.new_mat('vhf-front'); tx = fnt.nodes.new('ShaderNodeTexImage'); tx.image = img
            uvn = fnt.nodes.new('ShaderNodeUVMap'); fnt.links.new(uvn.outputs['UV'], tx.inputs['Vector'])
            fnt.links.new(tx.outputs['Color'], fb.inputs['Base Color']); fb.inputs['Roughness'].default_value = 0.5
            for sl in o.material_slots: sl.material = fm
        if names & {'Fig30', '[Color M07]', '[Color_007]1'}:
            for sl in o.material_slots:
                bb = next((n for n in sl.material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if bb and not bb.inputs['Base Color'].is_linked: bb.inputs['Base Color'].default_value = (0.018, 0.019, 0.021, 1)
    K.day_sky(sun_az=150, sun_el=40, strength=0.08)
    KI.area_light((0.4, -0.9, 0.55), (-0.08, 0, 0.04), 6, 0.6)
    KI.area_light((-0.8, -0.8, 0.3), (-0.1, 0, 0.04), 2, 1.0, (0.85, 0.9, 1.0))
    K.camera((-0.10, -0.52, 0.14), (-0.11, 0, 0.035), 40)
    labels = [((-0.185, -0.09, 0.098), 'Navtex 09:00 UTC'), ((-0.11, -0.09, -0.03), 'gale by 18:00 local', 'red')]
    note = 'Gale warning · 09:00 UTC is 12:00 Greek summer time'; expo = -0.4

elif FIG == 9:
    import kit_world as KW
    from mathutils import noise as mnoise
    # the strait runs N-S; Evia to the west, Andros to the east; A in the narrows at the origin
    def coast_e(y): return -620 - 120 * math.sin(y / 900.0) - 0.00016 * y * y      # Evia's east coast (x)
    def coast_a(y): return 560 + 140 * math.sin(y / 700.0 + 1.0) + 0.00018 * y * y  # Andros's west coast (x)
    def h(x, y):
        d = max(coast_e(y) - x, x - coast_a(y))       # metres inland from the nearer coast (negative in the strait)
        if d < 0: return max(-30.0, d * 0.08) - 0.5
        ridge = 520 * (1 - math.exp(-d / 900.0))
        rough = 110 * mnoise.noise(Vector((x * 0.0016, y * 0.0016, 3.0))) + 30 * mnoise.noise(Vector((x * 0.008, y * 0.008, 5.0)))
        edge = min(1.0, (5200 - abs(x)) / 1400.0, (6200 - abs(y)) / 1400.0)   # islands end before the grid does
        if edge <= 0: return -30.0
        return min(d * 0.35, ridge + rough * min(1.0, d / 300.0)) * edge - 0.5 - 30 * (1 - edge) * (edge < 0.15)
    step = 30.0; x0, x1, y0, y1 = -5200, 5200, -6200, 6200
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step); verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x, yy = x0 + i * step, y0 + j * step; verts.append((x, yy, h(x, yy)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i; faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    me = bpy.data.meshes.new('islands'); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
    lm, lnt, lb, lout = new_mat('aegean-land'); loc = obj_coords(lnt)
    lg = node(lnt, 'ShaderNodeNewGeometry'); ln = node(lnt, 'ShaderNodeSeparateXYZ'); link(lnt, lg.outputs['Normal'], ln.inputs['Vector'])
    base = ramp(lnt, [(0.3, '#5c4f3e'), (0.5, '#6f6249'), (0.7, '#4f473a')]); link(lnt, noise(lnt, loc, 0.0012, 5.0), base.inputs['Fac'])
    maq = ramp(lnt, [(0.48, (0, 0, 0, 1)), (0.6, (1, 1, 1, 1))]); link(lnt, noise(lnt, loc, 0.004, 6.0), maq.inputs['Fac'])
    col = mixc(lnt, math_(lnt, 'MULTIPLY', maq.outputs['Color'], 0.8), base.outputs['Color'], lin('#4b4a33'))
    steep = node(lnt, 'ShaderNodeMapRange', in_From_Min=0.9, in_From_Max=0.7); link(lnt, ln.outputs['Z'], steep.inputs['Value'])
    col = mixc(lnt, steep.outputs['Result'], col, lin('#7c766d'))
    sep9 = node(lnt, 'ShaderNodeSeparateXYZ'); link(lnt, node(lnt, 'ShaderNodeNewGeometry').outputs['Position'], sep9.inputs['Vector'])
    shore = node(lnt, 'ShaderNodeMapRange', in_From_Min=8.0, in_From_Max=1.0); link(lnt, sep9.outputs['Z'], shore.inputs['Value'])
    col = mixc(lnt, shore.outputs['Result'], col, lin('#a8987a'))
    link(lnt, col, lb.inputs['Base Color']); setin(lb, 'Roughness', 0.95); bump_from(lnt, lb, noise(lnt, loc, 0.05, 8.0), 0.5, 4.0)
    K.distance_fog(lnt, lb.outputs[0], lout.inputs['Surface'], half=60000.0, color=(0.42, 0.5, 0.6), strength=0.6)
    C.obj('islands', me, lm)
    fsm = bpy.data.meshes.new('farther-sea'); R = 900000
    fsm.from_pydata([(-R, -R, 0), (R, -R, 0), (R, R, 0), (-R, R, 0)], [], [(0, 1, 2, 3)])
    fsea, fnt, fb, fout = new_mat('farther-sea')       # no ripple bump: at 10-20 km it aliases into a dark band
    setin(fb, 'Base Color', lin('#0c2e3a')); setin(fb, 'Roughness', 0.12); setin(fb, 'IOR', 1.333)
    K.distance_fog(fnt, fb.outputs[0], fout.inputs['Surface'], half=60000.0, color=(0.42, 0.5, 0.6), strength=0.6)
    C.obj('farther-sea', fsm, fsea, (0, 0, -0.12))

    K.sea('breeze', size=48.0, repeat=36, center=(0, 300))
    for o in bpy.data.objects:
        if o.name.startswith('far-sea'): o.hide_render = True   # kit's 8 km sea: darker than the near sea seen from this high
    # the funnelled water: whitecaps and wind streaks, densest in the narrows, fading outside
    sm = bpy.data.meshes.new('streaks'); S = 4200
    sm.from_pydata([(-S, -S, 0), (S, -S, 0), (S, S, 0), (-S, S, 0)], [], [(0, 1, 2, 3)])
    m, nt, b, out = new_mat('funnel-foam'); oc = obj_coords(nt)
    sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, sep.inputs['Vector'])
    across = math_(nt, 'ABSOLUTE', sep.outputs['X']); along = math_(nt, 'ABSOLUTE', sep.outputs['Y'])
    zone = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MINIMUM', 1.0, math_(nt, 'DIVIDE', across, 900.0))),
                 math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MINIMUM', 1.0, math_(nt, 'DIVIDE', along, 2600.0))))
    mp = node(nt, 'ShaderNodeMapping'); setin(mp, 'Scale', (1.0, 0.18, 1.0)); setin(mp, 'Rotation', (0, 0, math.radians(-20))); link(nt, oc, mp.inputs['Vector'])
    st = node(nt, 'ShaderNodeTexNoise', in_Scale=0.05, in_Detail=6.0, in_Roughness=0.7); link(nt, mp.outputs['Vector'], st.inputs['Vector'])
    caps = node(nt, 'ShaderNodeTexVoronoi', in_Scale=0.06); link(nt, oc, caps.inputs['Vector'])
    cr = ramp(nt, [(0.0, (1, 1, 1, 1)), (0.12, (0, 0, 0, 1))]); link(nt, caps.outputs['Distance'], cr.inputs['Fac'])
    sr = ramp(nt, [(0.52, (0, 0, 0, 1)), (0.66, (0.7, 0.7, 0.7, 1))]); link(nt, st.outputs['Fac'], sr.inputs['Fac'])
    mask = math_(nt, 'MULTIPLY', math_(nt, 'MAXIMUM', cr.outputs['Color'], sr.outputs['Color']), math_(nt, 'POWER', zone, 0.7))
    dark = math_(nt, 'MULTIPLY', zone, 0.35)        # rougher water reads darker between the caps
    setin(b, 'Base Color', lin('#eef2f3')); setin(b, 'Roughness', 0.85)
    dk = node(nt, 'ShaderNodeBsdfPrincipled'); setin(dk, 'Base Color', lin('#061820')); setin(dk, 'Roughness', 0.3)
    tp = node(nt, 'ShaderNodeBsdfTransparent')
    m1 = node(nt, 'ShaderNodeMixShader'); link(nt, dark, m1.inputs['Fac']); link(nt, tp.outputs[0], m1.inputs[1]); link(nt, dk.outputs[0], m1.inputs[2])
    m2 = node(nt, 'ShaderNodeMixShader'); link(nt, mask, m2.inputs['Fac']); link(nt, m1.outputs[0], m2.inputs[1]); link(nt, b.outputs[0], m2.inputs[2])
    link(nt, m2.outputs[0], out.inputs['Surface'])
    so = C.obj('streaks', sm, m, (0, 0, 0.35)); so.visible_shadow = False
    # a yacht at A, reefed main and a scrap of genoa, beating north-east into it
    yt = K.load_yacht(name='at-A', sails={'main': True, 'genoa': 'port', 'boom': 10}); yt.place(0, 0, heading=60, heel=-22)
    for o in yt.root.children_recursive:
        if o.name.startswith(('main', 'genoa')): o.scale = (1.0, 1.0, 0.62) if o.name.startswith('main') else (0.6, 0.6, 0.6)
    K.wake(yt, 40, 9, 1.4)
    K.day_sky(sun_az=230, sun_el=40)
    # view from the south-south-west, up the strait towards the wind: Evia left, Andros right, as on the schematic
    look_from((0, 1400, 0), 8200, 200, 25, 32).data.clip_end = 1e6   # the sea reaches past the kit camera's 20 km clip
    wf = Vector((0, 0, 0)) + dirv(20) * 2600 + Vector((0, 0, 420)); wt = dirv(20) * 900 + Vector((0, 0, 260))
    arrows = [(tuple(wf), tuple(wt), 'red')]
    labels = [(tuple(wf + Vector((0, 0, 120))), 'Wind NNE 5–6', 'red'), ((-2300, 600, 420), 'EVIA'), ((2300, 600, 420), 'ANDROS'), ((0, 0, 60), 'A · F7, steep seas', 'red')]
    note = 'Forecast NE 5–6 · in the strait expect 7 and steep seas'

else:  # FIG 11: squall from the west
    y = K.load_yacht(name='you'); y.place(0, 0, heading=0, heel=0)
    K.sea('fresh', size=48.0, res=12, repeat=24, center=(-300, 0))
    K.day_sky(sun_az=95, sun_el=38)              # sun behind us, in the east
    # the western sky goes dark: mix the sky colour towards slate where the view looks west and low
    wt = bpy.context.scene.world.node_tree
    bg = next(n for n in wt.nodes if n.type == 'BACKGROUND'); src = bg.inputs['Color'].links[0].from_socket
    tc = wt.nodes.new('ShaderNodeTexCoord'); sp = wt.nodes.new('ShaderNodeSeparateXYZ'); wt.links.new(tc.outputs['Generated'], sp.inputs['Vector'])
    mr = wt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.2; mr.inputs['From Max'].default_value = -0.85; wt.links.new(sp.outputs['X'], mr.inputs['Value'])
    hz = wt.nodes.new('ShaderNodeMapRange'); hz.inputs['From Min'].default_value = 0.35; hz.inputs['From Max'].default_value = 0.02; wt.links.new(sp.outputs['Z'], hz.inputs['Value'])
    fm = wt.nodes.new('ShaderNodeMath'); fm.operation = 'MULTIPLY'; wt.links.new(mr.outputs['Result'], fm.inputs[0]); wt.links.new(hz.outputs['Result'], fm.inputs[1])
    mx = wt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; wt.links.new(fm.outputs[0], mx.inputs['Factor']); wt.links.new(src, mx.inputs[6]); mx.inputs[7].default_value = (0.03, 0.036, 0.045, 1)
    wt.links.new(mx.outputs[2], bg.inputs['Color'])
    # the shelf cloud: a long dark volume, flat base at 450 m, billowing upwards, 3-8 km west
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); cme = bpy.data.meshes.new('squall'); bm.to_mesh(cme); bm.free()
    cl = C.obj('squall-cloud', cme, None, (-6200, 1500, 2300)); cl.scale = (6000, 16000, 3700)
    m, nt, b, out = new_mat('squall-vol'); nt.nodes.remove(b)
    oc = obj_coords(nt); sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, sep.inputs['Vector'])
    n1 = node(nt, 'ShaderNodeTexNoise', in_Scale=5.0, in_Detail=8.0, in_Roughness=0.66); link(nt, oc, n1.inputs['Vector'])
    zf = node(nt, 'ShaderNodeMapRange', in_From_Min=-0.44, in_From_Max=-0.30); link(nt, sep.outputs['Z'], zf.inputs['Value'])   # flat base
    top = node(nt, 'ShaderNodeMapRange', in_From_Min=0.45, in_From_Max=0.1); link(nt, math_(nt, 'ADD', sep.outputs['Z'], math_(nt, 'MULTIPLY', n1.outputs['Fac'], 0.5)), top.inputs['Value'])
    front = node(nt, 'ShaderNodeMapRange', in_From_Min=0.48, in_From_Max=0.25); link(nt, math_(nt, 'ADD', sep.outputs['X'], math_(nt, 'MULTIPLY', n1.outputs['Fac'], 0.35)), front.inputs['Value'])
    dn = node(nt, 'ShaderNodeMapRange', in_From_Min=0.45, in_From_Max=0.6); link(nt, n1.outputs['Fac'], dn.inputs['Value'])
    dens = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', zf.outputs['Result'], top.outputs['Result']), front.outputs['Result']), math_(nt, 'MULTIPLY_ADD', dn.outputs['Result'], 0.7, 0.3))
    vp = node(nt, 'ShaderNodeVolumePrincipled'); setin(vp, 'Color', lin('#aab0b8')); link(nt, math_(nt, 'MULTIPLY', math_(nt, 'POWER', dens, 1.6), 0.0025), vp.inputs['Density'])
    setin(vp, 'Anisotropy', 0.2); link(nt, vp.outputs[0], out.inputs['Volume']); cl.data.materials.append(m)
    # the rain curtain under it: streaked grey sheets falling to the sea
    for k, (x, yy, w) in enumerate(((-3600, -1500, 5200), (-4300, 2600, 6000))):
        rm = bpy.data.meshes.new('rain'); rm.from_pydata([(0, -w / 2, 0), (0, w / 2, 0), (0, w / 2, 470), (0, -w / 2, 470)], [], [(0, 1, 2, 3)])
        rmat, rnt, rb, rout = new_mat('rain%d' % k); roc = obj_coords(rnt)
        rmp = node(rnt, 'ShaderNodeMapping'); setin(rmp, 'Scale', (1.0, 0.06, 1.6)); link(rnt, roc, rmp.inputs['Vector'])
        rn = node(rnt, 'ShaderNodeTexNoise', in_Scale=0.02, in_Detail=4.0); link(rnt, rmp.outputs['Vector'], rn.inputs['Vector'])
        rs = node(rnt, 'ShaderNodeSeparateXYZ'); link(rnt, roc, rs.inputs['Vector'])
        fadey = math_(rnt, 'SUBTRACT', 1.0, math_(rnt, 'POWER', math_(rnt, 'DIVIDE', math_(rnt, 'ABSOLUTE', rs.outputs['Y']), w / 2), 3.0))
        a = math_(rnt, 'MULTIPLY', math_(rnt, 'MULTIPLY_ADD', rn.outputs['Fac'], 0.9, 0.35), fadey)
        em = node(rnt, 'ShaderNodeBsdfDiffuse'); setin(em, 'Color', lin('#3d434a'))
        tp = node(rnt, 'ShaderNodeBsdfTransparent'); mm = node(rnt, 'ShaderNodeMixShader'); link(rnt, a, mm.inputs['Fac'])
        link(rnt, tp.outputs[0], mm.inputs[1]); link(rnt, em.outputs[0], mm.inputs[2]); link(rnt, mm.outputs[0], rout.inputs['Surface'])
        ro = C.obj('rain%d' % k, rm, rmat, (x, yy, 0)); ro.rotation_euler = (0, math.radians(-8), 0); ro.visible_shadow = False
    # the gust front: dark, streaked water ahead of the squall, ruffled into whitecaps, its edge 900 m off
    gm = bpy.data.meshes.new('gust'); gm.from_pydata([(-60000, -60000, 0), (-700, -60000, 0), (-700, 60000, 0), (-60000, 60000, 0)], [], [(0, 1, 2, 3)])
    mg, gnt, gb, gout = new_mat('gust-front'); goc = obj_coords(gnt)
    gs = node(gnt, 'ShaderNodeSeparateXYZ'); link(gnt, goc, gs.inputs['Vector'])
    edge = node(gnt, 'ShaderNodeMapRange', in_From_Min=-700, in_From_Max=-1500); link(gnt, math_(gnt, 'ADD', gs.outputs['X'], math_(gnt, 'MULTIPLY', noise(gnt, goc, 0.004, 3.0), 500.0)), edge.inputs['Value'])
    gc = node(gnt, 'ShaderNodeTexVoronoi', in_Scale=0.12); link(gnt, goc, gc.inputs['Vector'])
    gcr = ramp(gnt, [(0.0, (1, 1, 1, 1)), (0.1, (0, 0, 0, 1))]); link(gnt, gc.outputs['Distance'], gcr.inputs['Fac'])
    # darken what lies beneath (a tinted transparent shader keeps the waves), with whitecaps on top
    clear = node(gnt, 'ShaderNodeBsdfTransparent'); tint = node(gnt, 'ShaderNodeBsdfTransparent'); setin(tint, 'Color', (0.2, 0.24, 0.28, 1))
    md = node(gnt, 'ShaderNodeMixShader'); link(gnt, edge.outputs['Result'], md.inputs['Fac']); link(gnt, clear.outputs[0], md.inputs[1]); link(gnt, tint.outputs[0], md.inputs[2])
    fw = node(gnt, 'ShaderNodeBsdfPrincipled'); setin(fw, 'Base Color', lin('#dfe5e8')); setin(fw, 'Roughness', 0.9)
    mf = node(gnt, 'ShaderNodeMixShader'); link(gnt, math_(gnt, 'MULTIPLY', gcr.outputs['Color'], math_(gnt, 'MULTIPLY', edge.outputs['Result'], 0.7)), mf.inputs['Fac'])
    link(gnt, md.outputs[0], mf.inputs[1]); link(gnt, fw.outputs[0], mf.inputs[2]); link(gnt, mf.outputs[0], gout.inputs['Surface'])
    go = C.obj('gust-front', gm, mg, (0, 0, 0.4)); go.visible_shadow = False
    sc = bpy.context.scene.cycles; sc.volume_bounces = 0; sc.volume_step_rate = 12.0; sc.volume_max_steps = 256
    # from the starboard wheel, looking over the port side to the west
    eye = y.world((-1.8, 0.2, 5.1)); look = y.world((1.0, 40.0, 1.0)); K.camera(tuple(eye), tuple(look), 22)
    labels = [((-1100, 120, 40), '40 kn', 'red')]
    arrows = [((-1500, 60, 25), (-700, 60, 25), 'red')]
    note = 'Squall coming · reef hard or drop the sails, close the hatches'

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
