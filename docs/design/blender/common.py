# Shared building blocks for the Blender rope figures (rendered with Cycles, path traced).
# Three.js is Y-up, Blender is Z-up: every Three point goes through B(x, y, z) -> (x, -z, y).
# Scripts import this module, call reset(), build, then render(). Materials are procedural (no scanned textures).
import bpy, bmesh, math, random, sys, os, json, time
from mathutils import Vector, Matrix

W, H = 1280, 800
col = None  # the scene collection, set by reset()

# ---------- command line ----------
def cli():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def arg(name, default):
        return type(default)(argv[argv.index(name) + 1]) if name in argv else default
    return arg

def B(x, y, z):
    return Vector((x, -z, y))

def lin(hexs):  # sRGB hex -> linear RGBA
    h = hexs.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)

def reset():
    global col
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.context.scene.collection
    return bpy.context.scene

# ---------- node helpers ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    return m, nt, bsdf, out

def node(nt, kind, **props):
    n = nt.nodes.new(kind)
    for k, v in props.items():
        if k.startswith('in_'):
            n.inputs[k[3:].replace('_', ' ')].default_value = v
        else:
            setattr(n, k, v)
    return n

def link(nt, a, b):
    nt.links.new(a, b)

def setin(n, name, v):
    n.inputs[name].default_value = v

def math_(nt, op, a, b=None, c=None):
    """A Math node; a/b/c are sockets or numbers. Returns the output socket."""
    n = node(nt, 'ShaderNodeMath', operation=op)
    for i, v in enumerate((a, b, c)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: link(nt, v, n.inputs[i])
    return n.outputs[0]

def ramp(nt, stops, interp='LINEAR'):
    r = node(nt, 'ShaderNodeValToRGB'); r.color_ramp.interpolation = interp
    el = r.color_ramp.elements
    while len(el) < len(stops): el.new(0.5)
    for e, (p, c) in zip(el, stops):
        e.position = p; e.color = lin(c) if isinstance(c, str) else c
    return r

def mixc(nt, fac, a, b, blend='MIX'):
    """Colour mix; fac/a/b are sockets, numbers or colour tuples. Returns the output socket."""
    n = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type=blend)
    for sock, v in ((n.inputs['Factor'], fac), (n.inputs[6], a), (n.inputs[7], b)):
        if isinstance(v, (int, float, tuple)): sock.default_value = v
        else: link(nt, v, sock)
    return n.outputs[2]

def simple(name, color, rough=0.5, metal=0.0, coat=0.0, sheen=0.0):
    m, nt, b, _ = new_mat(name)
    setin(b, 'Base Color', lin(color)); setin(b, 'Roughness', rough); setin(b, 'Metallic', metal)
    if coat: setin(b, 'Coat Weight', coat); setin(b, 'Coat Roughness', 0.05)
    if sheen: setin(b, 'Sheen Weight', sheen)
    return m

def bump_from(nt, bsdf, height, strength=0.5, dist=0.001):
    bp = node(nt, 'ShaderNodeBump'); setin(bp, 'Strength', strength); setin(bp, 'Distance', dist)
    link(nt, height, bp.inputs['Height']); link(nt, bp.outputs['Normal'], bsdf.inputs['Normal'])
    return bp

def obj_coords(nt):
    return node(nt, 'ShaderNodeTexCoord').outputs['Object']

def noise(nt, vec, scale, detail=2.0, rough=0.5):
    n = node(nt, 'ShaderNodeTexNoise', in_Scale=scale, in_Detail=detail, in_Roughness=rough)
    link(nt, vec, n.inputs['Vector']); return n.outputs['Fac']

# ---------- materials ----------
def granite_mat(name, base='#b9b5ad', per_object=True, scale=1.0, dark='#4b4945', light='#e2ded6', dirt=True):
    """Speckled granite: dark mica, white quartz, a few pink feldspar grains, mottled at a larger scale."""
    m, nt, b, _ = new_mat(name)
    tc = node(nt, 'ShaderNodeTexCoord')
    speck = node(nt, 'ShaderNodeTexVoronoi', in_Scale=260 * scale, in_Randomness=1.0)
    link(nt, tc.outputs['Object'], speck.inputs['Vector'])
    grains = ramp(nt, [(0.0, dark), (0.3, dark), (0.31, base), (0.8, base), (0.81, light), (0.95, light), (0.96, '#a88472')], 'CONSTANT')
    # voronoi 'Color' is a random colour per grain; one channel picks the mineral
    sep = node(nt, 'ShaderNodeSeparateColor'); link(nt, speck.outputs['Color'], sep.inputs['Color']); link(nt, sep.outputs[0], grains.inputs['Fac'])
    mott = node(nt, 'ShaderNodeTexNoise', in_Scale=6 * scale, in_Detail=4.0)
    link(nt, tc.outputs['Object'], mott.inputs['Vector'])
    mix = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); setin(mix, 'Factor', 0.35)
    mr = ramp(nt, [(0.3, '#8d8a85'), (0.7, '#ffffff')])
    link(nt, mott.outputs['Fac'], mr.inputs['Fac'])
    link(nt, grains.outputs['Color'], mix.inputs[6]); link(nt, mr.outputs['Color'], mix.inputs[7])
    last = mix.outputs[2]
    if per_object:  # each block a slightly different stone: tint by the object's random value
        oi = node(nt, 'ShaderNodeObjectInfo')
        tint = ramp(nt, [(0.0, '#6f675d'), (0.3, '#a39a8c'), (0.65, '#bab1a3'), (0.85, '#9a9183'), (1.0, '#857c70')])
        link(nt, oi.outputs['Random'], tint.inputs['Fac'])
        m2 = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); setin(m2, 'Factor', 1.0)
        link(nt, last, m2.inputs[6]); link(nt, tint.outputs['Color'], m2.inputs[7]); last = m2.outputs[2]
    if dirt:  # grime settles in the hollows and round the edges: darken by ambient occlusion
        ao = node(nt, 'ShaderNodeAmbientOcclusion', samples=8, in_Distance=0.025)
        aor = ramp(nt, [(0.35, '#5a5248'), (0.95, '#ffffff')]); link(nt, ao.outputs['AO'], aor.inputs['Fac'])
        m3 = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); setin(m3, 'Factor', 1.0)
        link(nt, last, m3.inputs[6]); link(nt, aor.outputs['Color'], m3.inputs[7]); last = m3.outputs[2]
    link(nt, last, b.inputs['Base Color'])
    rough = node(nt, 'ShaderNodeMapRange', in_To_Min=0.72, in_To_Max=0.92); link(nt, mott.outputs['Fac'], rough.inputs['Value'])
    link(nt, rough.outputs['Result'], b.inputs['Roughness'])
    # surface: grain relief plus a pitted, weathered face
    pit = node(nt, 'ShaderNodeTexNoise', in_Scale=90 * scale, in_Detail=8.0, in_Roughness=0.65)
    link(nt, tc.outputs['Object'], pit.inputs['Vector'])
    h = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); link(nt, speck.outputs['Distance'], h.inputs[0]); setin(h, 1, 0.4); link(nt, pit.outputs['Fac'], h.inputs[2])
    bump_from(nt, b, h.outputs[0], 0.35, 0.002)
    return m

def joint_mat():
    """The grit between the setts: dark sand, a little green where it stays damp."""
    m, nt, b, _ = new_mat('joint')
    tc = node(nt, 'ShaderNodeTexCoord')
    n1 = node(nt, 'ShaderNodeTexNoise', in_Scale=180.0, in_Detail=6.0); link(nt, tc.outputs['Object'], n1.inputs['Vector'])
    n2 = node(nt, 'ShaderNodeTexNoise', in_Scale=8.0, in_Detail=3.0); link(nt, tc.outputs['Object'], n2.inputs['Vector'])
    r = ramp(nt, [(0.35, '#100f0c'), (0.55, '#24211c'), (0.7, '#38342a')]); link(nt, n1.outputs['Fac'], r.inputs['Fac'])
    g = ramp(nt, [(0.45, '#ffffff'), (0.65, '#7d8a5a')]); link(nt, n2.outputs['Fac'], g.inputs['Fac'])
    mx = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); setin(mx, 'Factor', 0.6)
    link(nt, r.outputs['Color'], mx.inputs[6]); link(nt, g.outputs['Color'], mx.inputs[7]); link(nt, mx.outputs[2], b.inputs['Base Color'])
    setin(b, 'Roughness', 0.95)
    bump_from(nt, b, n1.outputs['Fac'], 0.8, 0.003)
    return m

def iron_mat():
    """Cast-iron bollard: black paint chipped to rust at the base and the cap rim, rust streaks running down,
    and a rope-polished band of bare grey iron where lines bear on the barrel."""
    m, nt, b, _ = new_mat('iron')
    tc = node(nt, 'ShaderNodeTexCoord')
    sepz = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, tc.outputs['Object'], sepz.inputs['Vector'])
    hz = node(nt, 'ShaderNodeMath', operation='DIVIDE'); link(nt, sepz.outputs['Z'], hz.inputs[0]); setin(hz, 1, 0.462)
    # where chips are likely: the base flange and the cap rim, a few on the barrel
    zone = ramp(nt, [(0.0, (0.9, 0.9, 0.9, 1)), (0.1, (0.78, 0.78, 0.78, 1)), (0.2, (0.3, 0.3, 0.3, 1)), (0.7, (0.22, 0.22, 0.22, 1)), (0.8, (0.7, 0.7, 0.7, 1)), (0.86, (0.3, 0.3, 0.3, 1)), (1.0, (0.18, 0.18, 0.18, 1))])
    link(nt, hz.outputs[0], zone.inputs['Fac'])
    chips = node(nt, 'ShaderNodeTexNoise', in_Scale=38.0, in_Detail=10.0, in_Roughness=0.7)
    link(nt, tc.outputs['Object'], chips.inputs['Vector'])
    # chip mask = noise above a threshold that the zone lowers
    thr = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); link(nt, zone.outputs['Color'], thr.inputs[0]); setin(thr, 1, -0.28); setin(thr, 2, 0.74)
    chip = node(nt, 'ShaderNodeMath', operation='SUBTRACT'); link(nt, chips.outputs['Fac'], chip.inputs[0]); link(nt, thr.outputs[0], chip.inputs[1])
    chipm = node(nt, 'ShaderNodeMapRange', in_From_Min=0.0, in_From_Max=0.025); link(nt, chip.outputs[0], chipm.inputs['Value'])
    # rust streaks: noise stretched vertically, hanging below the cap rim
    mp = node(nt, 'ShaderNodeMapping'); setin(mp, 'Scale', (60.0, 60.0, 2.5)); link(nt, tc.outputs['Object'], mp.inputs['Vector'])
    st = node(nt, 'ShaderNodeTexNoise', in_Scale=1.0, in_Detail=2.0); link(nt, mp.outputs['Vector'], st.inputs['Vector'])
    stz = ramp(nt, [(0.32, (0, 0, 0, 1)), (0.55, (0.35, 0.35, 0.35, 1)), (0.76, (1, 1, 1, 1)), (0.79, (0, 0, 0, 1))]); link(nt, hz.outputs[0], stz.inputs['Fac'])
    stm = node(nt, 'ShaderNodeMapRange', in_From_Min=0.55, in_From_Max=0.7); link(nt, st.outputs['Fac'], stm.inputs['Value'])
    streak = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); link(nt, stm.outputs['Result'], streak.inputs[0]); link(nt, stz.outputs['Color'], streak.inputs[1])
    # polished band
    band = ramp(nt, [(0.26, (0, 0, 0, 1)), (0.32, (1, 1, 1, 1)), (0.38, (1, 1, 1, 1)), (0.44, (0, 0, 0, 1))]); link(nt, hz.outputs[0], band.inputs['Fac'])
    bn = node(nt, 'ShaderNodeTexNoise', in_Scale=25.0, in_Detail=4.0); link(nt, tc.outputs['Object'], bn.inputs['Vector'])
    bandm = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); link(nt, band.outputs['Color'], bandm.inputs[0]); link(nt, bn.outputs['Fac'], bandm.inputs[1])
    bandc = node(nt, 'ShaderNodeMapRange', in_From_Min=0.25, in_From_Max=0.6); link(nt, bandm.outputs[0], bandc.inputs['Value'])
    # colours
    rustn = node(nt, 'ShaderNodeTexNoise', in_Scale=120.0, in_Detail=6.0); link(nt, tc.outputs['Object'], rustn.inputs['Vector'])
    rustc = ramp(nt, [(0.3, '#3a1d10'), (0.5, '#6b3519'), (0.7, '#8f4f26')]); link(nt, rustn.outputs['Fac'], rustc.inputs['Fac'])
    paintn = node(nt, 'ShaderNodeTexNoise', in_Scale=15.0, in_Detail=3.0); link(nt, tc.outputs['Object'], paintn.inputs['Vector'])
    paintc = ramp(nt, [(0.3, '#060607'), (0.7, '#111214')]); link(nt, paintn.outputs['Fac'], paintc.inputs['Fac'])
    c1 = node(nt, 'ShaderNodeMix', data_type='RGBA'); link(nt, streak.outputs[0], c1.inputs['Factor']); link(nt, paintc.outputs['Color'], c1.inputs[6]); setin(c1, 7, lin('#4a2614'))
    c2 = node(nt, 'ShaderNodeMix', data_type='RGBA'); link(nt, bandc.outputs['Result'], c2.inputs['Factor']); link(nt, c1.outputs[2], c2.inputs[6]); setin(c2, 7, lin('#5d5c59'))
    c3 = node(nt, 'ShaderNodeMix', data_type='RGBA'); link(nt, chipm.outputs['Result'], c3.inputs['Factor']); link(nt, c2.outputs[2], c3.inputs[6]); link(nt, rustc.outputs['Color'], c3.inputs[7])
    link(nt, c3.outputs[2], b.inputs['Base Color'])
    # paint semi-gloss, rust dry, the polished band metallic
    r1 = node(nt, 'ShaderNodeMix', data_type='FLOAT'); link(nt, bandc.outputs['Result'], r1.inputs['Factor']); setin(r1, 2, 0.5); setin(r1, 3, 0.32)
    r2 = node(nt, 'ShaderNodeMix', data_type='FLOAT'); link(nt, chipm.outputs['Result'], r2.inputs['Factor']); link(nt, r1.outputs[0], r2.inputs[2]); setin(r2, 3, 0.92)
    link(nt, r2.outputs[0], b.inputs['Roughness'])
    met = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); link(nt, bandc.outputs['Result'], met.inputs[0]); setin(met, 1, 0.7)
    link(nt, met.outputs[0], b.inputs['Metallic'])
    # relief: chips sit below the paint, the casting is a little lumpy, rust is rough
    lump = node(nt, 'ShaderNodeTexNoise', in_Scale=30.0, in_Detail=6.0); link(nt, tc.outputs['Object'], lump.inputs['Vector'])
    hh = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); link(nt, chipm.outputs['Result'], hh.inputs[0]); setin(hh, 1, -0.6); link(nt, lump.outputs['Fac'], hh.inputs[2])
    hh2 = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); link(nt, rustn.outputs['Fac'], hh2.inputs[0]); link(nt, chipm.outputs['Result'], hh2.inputs[1]); link(nt, hh.outputs[0], hh2.inputs[2])
    bump_from(nt, b, hh2.outputs[0], 0.5, 0.0015)
    return m

def rope_mat(name, tracer=False):
    """Three-strand polyester: each strand is yarns twisted the other way, so the crown shows ribs
    that run nearly along the rope. UV: U = length / 3 cm, V = round the strand."""
    m, nt, b, _ = new_mat(name)
    uv = node(nt, 'ShaderNodeUVMap')
    sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, uv.outputs['UV'], sep.inputs['Vector'])
    w = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); link(nt, sep.outputs['Y'], w.inputs[0]); setin(w, 1, 12.0)
    w2 = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); link(nt, sep.outputs['X'], w2.inputs[0]); setin(w2, 1, 7.1)
    link(nt, w2.outputs[0], w.inputs[2])
    # rounded yarn profile: 1 at the yarn crown, 0 in the groove
    tri = node(nt, 'ShaderNodeMath', operation='PINGPONG'); link(nt, w.outputs[0], tri.inputs[0]); setin(tri, 1, 0.5)
    prof = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); link(nt, tri.outputs[0], prof.inputs[0]); setin(prof, 1, 2.0)
    sm = node(nt, 'ShaderNodeMath', operation='POWER'); link(nt, prof.outputs[0], sm.inputs[0]); setin(sm, 1, 0.6)
    # fibre fuzz
    tc = node(nt, 'ShaderNodeTexCoord')
    fuzz = node(nt, 'ShaderNodeTexNoise', in_Scale=900.0, in_Detail=4.0); link(nt, tc.outputs['Object'], fuzz.inputs['Vector'])
    dirt = node(nt, 'ShaderNodeTexNoise', in_Scale=9.0, in_Detail=3.0); link(nt, tc.outputs['Object'], dirt.inputs['Vector'])
    base = ramp(nt, [(0.0, '#8d8371'), (0.55, '#d9d2c1'), (1.0, '#f1ece0')]); link(nt, sm.outputs[0], base.inputs['Fac'])
    dr = ramp(nt, [(0.4, '#ffffff'), (0.75, '#cfc6b2')]); link(nt, dirt.outputs['Fac'], dr.inputs['Fac'])
    mx = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); setin(mx, 'Factor', 1.0)
    link(nt, base.outputs['Color'], mx.inputs[6]); link(nt, dr.outputs['Color'], mx.inputs[7])
    last = mx.outputs[2]
    if tracer:  # one blue tracer yarn in every six on one strand
        fl = node(nt, 'ShaderNodeMath', operation='FLOOR'); link(nt, w.outputs[0], fl.inputs[0])
        md = node(nt, 'ShaderNodeMath', operation='FLOORED_MODULO'); link(nt, fl.outputs[0], md.inputs[0]); setin(md, 1, 6.0)
        lt = node(nt, 'ShaderNodeMath', operation='LESS_THAN'); link(nt, md.outputs[0], lt.inputs[0]); setin(lt, 1, 0.5)
        t2 = node(nt, 'ShaderNodeMix', data_type='RGBA'); link(nt, lt.outputs[0], t2.inputs['Factor']); link(nt, last, t2.inputs[6]); link(nt, base.outputs['Color'], t2.inputs[7])
        t3 = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); link(nt, lt.outputs[0], t3.inputs['Factor']); link(nt, t2.outputs[2], t3.inputs[6]); setin(t3, 7, lin('#2a4a86'))
        last = t3.outputs[2]
    link(nt, last, b.inputs['Base Color'])
    setin(b, 'Roughness', 0.78)
    setin(b, 'Sheen Weight', 0.6); setin(b, 'Sheen Roughness', 0.5)
    setin(b, 'Subsurface Weight', 0.12); setin(b, 'Subsurface Scale', 0.002)
    h = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); link(nt, fuzz.outputs['Fac'], h.inputs[0]); setin(h, 1, 0.25); link(nt, sm.outputs[0], h.inputs[2])
    bump_from(nt, b, h.outputs[0], 0.9, 0.0008)
    return m

def braid_mat(name, base, fleck, shiny=False, fine=1.0, R=0.006):
    """A plaited cover: two families of carriers spiralling opposite ways, each passing over two and under two
    of the other. One carrier in four of the first family is the fleck colour, so the tracer runs as a dashed
    helix. Tube UV: U = length in circumferences, V = round the line."""
    m, nt, b, _ = new_mat(name)
    uv = node(nt, 'ShaderNodeUVMap')
    sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, uv.outputs['UV'], sep.inputs['Vector'])
    N = 8.0 * fine                                    # carriers per family round the line
    U, Vv = sep.outputs['X'], sep.outputs['Y']
    a = math_(nt, 'MULTIPLY', math_(nt, 'ADD', Vv, math_(nt, 'MULTIPLY', U, 0.85)), N)
    bb = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', Vv, math_(nt, 'MULTIPLY', U, 0.85)), N)
    ia, ib = math_(nt, 'FLOOR', a), math_(nt, 'FLOOR', bb)
    fa, fb = math_(nt, 'SUBTRACT', a, ia), math_(nt, 'SUBTRACT', bb, ib)
    # 2-over-2-under: which family is on top in this cell
    topA = math_(nt, 'LESS_THAN', math_(nt, 'FLOORED_MODULO', math_(nt, 'ADD', math_(nt, 'FLOOR', math_(nt, 'MULTIPLY', ia, 0.5)), math_(nt, 'FLOOR', math_(nt, 'MULTIPLY', ib, 0.5))), 2.0), 0.5)
    # each carrier is a flat bundle of fibres: rounded across its width, dipping where it goes under
    sA = math_(nt, 'POWER', math_(nt, 'SINE', math_(nt, 'MULTIPLY', fa, math.pi)), 0.45)
    sB = math_(nt, 'POWER', math_(nt, 'SINE', math_(nt, 'MULTIPLY', fb, math.pi)), 0.45)
    pa = math_(nt, 'FRACT', math_(nt, 'MULTIPLY', bb, 0.5)); pb = math_(nt, 'FRACT', math_(nt, 'MULTIPLY', a, 0.5))
    lA = math_(nt, 'MULTIPLY_ADD', math_(nt, 'SINE', math_(nt, 'MULTIPLY', pa, math.pi)), 0.4, 0.6)
    lB = math_(nt, 'MULTIPLY_ADD', math_(nt, 'SINE', math_(nt, 'MULTIPLY', pb, math.pi)), 0.4, 0.6)
    hA, hB = math_(nt, 'MULTIPLY', sA, lA), math_(nt, 'MULTIPLY', sB, lB)
    hmix = node(nt, 'ShaderNodeMix', data_type='FLOAT'); link(nt, topA, hmix.inputs['Factor']); link(nt, hB, hmix.inputs[2]); link(nt, hA, hmix.inputs[3])
    h = hmix.outputs[0]
    # fleck: one carrier in four of family A, only where it is on top
    fl = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', math_(nt, 'FLOORED_MODULO', ia, 4.0), 0.5), topA)
    # fibres along each carrier
    fib = node(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=1.0, in_Distortion=2.0, in_Detail=3.0)
    fv = node(nt, 'ShaderNodeCombineXYZ'); link(nt, math_(nt, 'MULTIPLY', a, 7.0), fv.inputs['X']); link(nt, bb, fv.inputs['Y'])
    fv2 = node(nt, 'ShaderNodeCombineXYZ'); link(nt, math_(nt, 'MULTIPLY', bb, 7.0), fv2.inputs['X']); link(nt, a, fv2.inputs['Y'])
    fsel = node(nt, 'ShaderNodeMix', data_type='VECTOR'); link(nt, topA, fsel.inputs['Factor']); link(nt, fv2.outputs[0], fsel.inputs[4]); link(nt, fv.outputs[0], fsel.inputs[5])
    link(nt, fsel.outputs[1], fib.inputs['Vector'])
    colr = mixc(nt, fl, lin(base), lin(fleck))
    shade = ramp(nt, [(0.0, (0.28, 0.28, 0.28, 1)), (0.55, (0.8, 0.8, 0.8, 1)), (1.0, (1, 1, 1, 1))]); link(nt, h, shade.inputs['Fac'])
    c2 = mixc(nt, 1.0, colr, shade.outputs['Color'], 'MULTIPLY')
    fshade = ramp(nt, [(0.0, (0.86, 0.86, 0.86, 1)), (1.0, (1, 1, 1, 1))]); link(nt, fib.outputs['Fac'], fshade.inputs['Fac'])
    c3 = mixc(nt, 1.0, c2, fshade.outputs['Color'], 'MULTIPLY')
    link(nt, c3, b.inputs['Base Color'])
    setin(b, 'Roughness', 0.38 if shiny else 0.72)
    setin(b, 'Sheen Weight', 0.15 if shiny else 0.3); setin(b, 'Sheen Roughness', 0.45); setin(b, 'Sheen Tint', lin(base))
    hh = math_(nt, 'MULTIPLY_ADD', fib.outputs['Fac'], 0.12, h)
    bump_from(nt, b, hh, 1.0, R * 0.12)
    return m

def whip_mat(color):
    """Whipping twine: tight turns round the line (object Z runs along the line)."""
    m, nt, b, _ = new_mat('whip')
    sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, obj_coords(nt), sep.inputs['Vector'])
    turns = math_(nt, 'PINGPONG', math_(nt, 'MULTIPLY', sep.outputs['Z'], 650.0), 0.5)
    prof = math_(nt, 'POWER', math_(nt, 'MULTIPLY', turns, 2.0), 0.5)
    sh = ramp(nt, [(0.0, (0.35, 0.35, 0.35, 1)), (1.0, (1, 1, 1, 1))]); link(nt, prof, sh.inputs['Fac'])
    link(nt, mixc(nt, 1.0, lin(color), sh.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color'])
    setin(b, 'Roughness', 0.55); setin(b, 'Sheen Weight', 0.1)
    bump_from(nt, b, prof, 1.0, 0.0007)
    return m

def gel_mat(name='gelcoat'):
    m, nt, b, _ = new_mat(name)
    setin(b, 'Base Color', lin('#f1f1ec')); setin(b, 'Roughness', 0.3)
    setin(b, 'Coat Weight', 1.0); setin(b, 'Coat Roughness', 0.04)
    tc = node(nt, 'ShaderNodeTexCoord')
    n = node(nt, 'ShaderNodeTexNoise', in_Scale=3.0, in_Detail=2.0); link(nt, tc.outputs['Object'], n.inputs['Vector'])
    bp = node(nt, 'ShaderNodeBump'); setin(bp, 'Strength', 0.03); link(nt, n.outputs['Fac'], bp.inputs['Height'])
    link(nt, bp.outputs['Normal'], b.inputs['Coat Normal'])  # slight orange peel in the clear coat
    return m

def water_mat():
    m, nt, b, _ = new_mat('water')
    setin(b, 'Base Color', lin('#0e2a2f')); setin(b, 'Roughness', 0.03); setin(b, 'IOR', 1.33)
    tc = node(nt, 'ShaderNodeTexCoord')
    n = node(nt, 'ShaderNodeTexNoise', in_Scale=3.0, in_Detail=6.0)
    mp = node(nt, 'ShaderNodeMapping'); setin(mp, 'Scale', (1.0, 2.5, 1.0)); link(nt, tc.outputs['Object'], mp.inputs['Vector']); link(nt, mp.outputs['Vector'], n.inputs['Vector'])
    bump_from(nt, b, n.outputs['Fac'], 0.25, 0.05)
    return m

def teak_mat(name='teak'):
    """Laid teak: 5 cm planks along X with black caulking seams, each plank its own shade, grain running along."""
    m, nt, b, _ = new_mat(name)
    oc = obj_coords(nt); sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, sep.inputs['Vector'])
    y = math_(nt, 'DIVIDE', sep.outputs['Y'], 0.05)
    plank = math_(nt, 'FLOOR', y); fy = math_(nt, 'FRACT', y)
    seam = math_(nt, 'LESS_THAN', fy, 0.09)
    wn = node(nt, 'ShaderNodeTexWhiteNoise', noise_dimensions='1D'); link(nt, plank, wn.inputs['W'])
    shade = ramp(nt, [(0.0, '#5a4330'), (0.5, '#6e5238'), (1.0, '#7c5e40')]); link(nt, wn.outputs['Value'], shade.inputs['Fac'])
    # grain: noise stretched along the plank, offset per plank
    mp = node(nt, 'ShaderNodeMapping'); setin(mp, 'Scale', (4.0, 120.0, 40.0)); link(nt, oc, mp.inputs['Vector'])
    off = node(nt, 'ShaderNodeCombineXYZ'); link(nt, math_(nt, 'MULTIPLY', wn.outputs['Value'], 37.0), off.inputs['X']); link(nt, off.outputs[0], mp.inputs['Location'])
    gr = node(nt, 'ShaderNodeTexNoise', in_Scale=1.0, in_Detail=6.0, in_Roughness=0.55); link(nt, mp.outputs['Vector'], gr.inputs['Vector'])
    grain = ramp(nt, [(0.35, (0.62, 0.62, 0.62, 1)), (0.65, (1, 1, 1, 1))]); link(nt, gr.outputs['Fac'], grain.inputs['Fac'])
    wood = mixc(nt, 1.0, shade.outputs['Color'], grain.outputs['Color'], 'MULTIPLY')
    weather = noise(nt, oc, 6.0, 3.0)
    wr = ramp(nt, [(0.3, '#ffffff'), (0.7, '#d9cdbd')]); link(nt, weather, wr.inputs['Fac'])
    wood2 = mixc(nt, 1.0, wood, wr.outputs['Color'], 'MULTIPLY')
    link(nt, mixc(nt, seam, wood2, lin('#15110d')), b.inputs['Base Color'])
    rough = node(nt, 'ShaderNodeMix', data_type='FLOAT'); link(nt, seam, rough.inputs['Factor']); setin(rough, 2, 0.72); setin(rough, 3, 0.9); link(nt, rough.outputs[0], b.inputs['Roughness'])
    hgt = math_(nt, 'MULTIPLY_ADD', gr.outputs['Fac'], 0.25, math_(nt, 'SUBTRACT', 1.0, seam))
    bump_from(nt, b, hgt, 0.6, 0.0015)
    return m

def nonskid_mat(name='nonskid'):
    """Moulded non-skid: a fine grid of raised squares in pale gelcoat, a little grubby."""
    m, nt, b, _ = new_mat(name)
    oc = obj_coords(nt)
    vor = node(nt, 'ShaderNodeTexVoronoi', distance='CHEBYCHEV', in_Scale=240.0, in_Randomness=0.15); link(nt, oc, vor.inputs['Vector'])
    bumpv = ramp(nt, [(0.3, (1, 1, 1, 1)), (0.45, (0.25, 0.25, 0.25, 1))]); link(nt, vor.outputs['Distance'], bumpv.inputs['Fac'])
    dirt = noise(nt, oc, 14.0, 4.0)
    dr = ramp(nt, [(0.35, '#d6d1c4'), (0.75, '#b9b1a0')]); link(nt, dirt, dr.inputs['Fac'])
    tops = mixc(nt, bumpv.outputs['Color'], lin('#b3ab99'), lin('#ffffff'), 'MIX')
    link(nt, mixc(nt, 1.0, dr.outputs['Color'], tops, 'MULTIPLY'), b.inputs['Base Color'])
    setin(b, 'Roughness', 0.6)
    bump_from(nt, b, bumpv.outputs['Color'], 0.45, 0.0006)
    return m

def galv_mat(name='galv'):
    """Hot-dip galvanised steel: dull grey with a spangle and the odd dark stain."""
    m, nt, b, _ = new_mat(name)
    oc = obj_coords(nt)
    vor = node(nt, 'ShaderNodeTexVoronoi', in_Scale=90.0); link(nt, oc, vor.inputs['Vector'])
    sp = node(nt, 'ShaderNodeSeparateColor'); link(nt, vor.outputs['Color'], sp.inputs['Color'])
    c = ramp(nt, [(0.0, '#8e9396'), (1.0, '#b2b7ba')]); link(nt, sp.outputs[0], c.inputs['Fac'])
    st = ramp(nt, [(0.55, '#ffffff'), (0.75, '#6d6a62')]); link(nt, noise(nt, oc, 12.0, 4.0), st.inputs['Fac'])
    link(nt, mixc(nt, 1.0, c.outputs['Color'], st.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color'])
    setin(b, 'Metallic', 0.85)
    rr = node(nt, 'ShaderNodeMapRange', in_To_Min=0.38, in_To_Max=0.6); link(nt, sp.outputs[1], rr.inputs['Value']); link(nt, rr.outputs['Result'], b.inputs['Roughness'])
    return m

def fabric_mat(name, color, sheen='#5b6f99', scale=900.0):
    """Woven acrylic canvas or fleece: colour with a sheen and a fine weave bump."""
    m, nt, b, _ = new_mat(name)
    oc = obj_coords(nt)
    wx = node(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', in_Scale=scale); link(nt, oc, wx.inputs['Vector'])
    wy = node(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', in_Scale=scale); link(nt, oc, wy.inputs['Vector'])
    h = math_(nt, 'MULTIPLY', wx.outputs['Fac'], wy.outputs['Fac'])
    vr = ramp(nt, [(0.3, '#d8d8d8'), (0.7, '#ffffff')]); link(nt, noise(nt, oc, 5.0, 3.0), vr.inputs['Fac'])
    link(nt, mixc(nt, 1.0, lin(color), vr.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color'])
    setin(b, 'Roughness', 0.9); setin(b, 'Sheen Weight', 0.8); setin(b, 'Sheen Roughness', 0.5); setin(b, 'Sheen Tint', lin(sheen))
    bump_from(nt, b, h, 0.3, 0.0005)
    return m

def planks_mat(name='planks'):
    """Weathered pontoon decking: silver-grey hardwood, grain running along, each plank its own shade."""
    m, nt, b, _ = new_mat(name)
    oc = obj_coords(nt)
    oi = node(nt, 'ShaderNodeObjectInfo')
    shade = ramp(nt, [(0.0, '#8a8174'), (0.5, '#a39a8b'), (1.0, '#b9b0a1')]); link(nt, oi.outputs['Random'], shade.inputs['Fac'])
    mp = node(nt, 'ShaderNodeMapping'); setin(mp, 'Scale', (90.0, 90.0, 3.0)); link(nt, oc, mp.inputs['Vector'])
    off = node(nt, 'ShaderNodeCombineXYZ'); link(nt, math_(nt, 'MULTIPLY', oi.outputs['Random'], 50.0), off.inputs['Z']); link(nt, off.outputs[0], mp.inputs['Location'])
    gr = node(nt, 'ShaderNodeTexNoise', in_Scale=1.0, in_Detail=8.0, in_Roughness=0.6); link(nt, mp.outputs['Vector'], gr.inputs['Vector'])
    g = ramp(nt, [(0.3, (0.55, 0.55, 0.55, 1)), (0.7, (1, 1, 1, 1))]); link(nt, gr.outputs['Fac'], g.inputs['Fac'])
    link(nt, mixc(nt, 1.0, shade.outputs['Color'], g.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color'])
    setin(b, 'Roughness', 0.92)
    bump_from(nt, b, gr.outputs['Fac'], 0.7, 0.002)
    return m

def concrete_mat(name='float'):
    m, nt, b, _ = new_mat(name)
    oc = obj_coords(nt)
    c = ramp(nt, [(0.3, '#6f6c66'), (0.7, '#9a968e')]); link(nt, noise(nt, oc, 20.0, 6.0), c.inputs['Fac'])
    link(nt, c.outputs['Color'], b.inputs['Base Color']); setin(b, 'Roughness', 0.92)
    bump_from(nt, b, noise(nt, oc, 200.0, 4.0), 0.4, 0.002)
    return m

# materials the exported Three.js scenes name, swapped for these procedural ones on import
def scene_materials():
    return {
        'gel': gel_mat(), 'teak': teak_mat(), 'nonskid': nonskid_mat(), 'water': water_mat(), 'galv': galv_mat(),
        'planks': planks_mat(), 'float': concrete_mat(),
        'chrome': simple('chrome', '#e6e9ec', 0.08, 1.0), 'satin': simple('satin', '#c8ccd0', 0.36, 1.0),
        'post': simple('post', '#c9cdd1', 0.22, 1.0), 'alu': simple('alu', '#c4c8cc', 0.34, 1.0),
        'anod': simple('anod', '#19191b', 0.38, 0.4), 'rubber': simple('rubber', '#141516', 0.72),
        'strake': simple('strake', '#3b3e42', 0.45, coat=0.4), 'wire': simple('wire', '#f2f2ee', 0.3, coat=0.5),
        'glass': simple('glass', '#0e1318', 0.03, 0.2, coat=1.0),
        'canvas': fabric_mat('canvas', '#1f2c48'), 'sock': fabric_mat('sock', '#1e2f55', '#5d75a8', 1400.0),
    }

# ---------- mesh helpers ----------
def obj(name, me, mat=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = loc
    if mat is not None and not me.materials: me.materials.append(mat)
    return o

def weighted(me):
    """Bake weighted normals so big flat faces stay flat next to their rounded edges."""
    tmp = bpy.data.objects.new('tmp', me); col.objects.link(tmp)
    md = tmp.modifiers.new('wn', 'WEIGHTED_NORMAL'); md.keep_sharp = True; md.mode = 'FACE_AREA'
    bpy.context.view_layer.update()
    me2 = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp); bpy.data.meshes.remove(me)
    return me2

def rbox(name, dims, r, seg=3):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * dims[0], v.co.y * dims[1], v.co.z * dims[2]))
    if r > 0:
        bmesh.ops.bevel(bm, geom=bm.verts[:] + bm.edges[:], offset=r, segments=seg, affect='EDGES', profile=0.5, clamp_overlap=True)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return weighted(me)

def tbox(dims3, at3, mat, r=0.0, seg=3, name='box'):
    """A box given in Three.js terms (size x,y,z and centre), placed in Blender."""
    return obj(name, rbox(name, (dims3[0], dims3[2], dims3[1]), r, seg), mat, B(*at3))

def cyl(name, r1, r2, h, seg, mat, loc, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=h)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.set_sharp_from_angle(angle=math.radians(50))
    o = obj(name, me, mat, loc); o.rotation_euler = rot
    return o

def lathe(name, prof, seg, mat):
    """Spin a (r, y) profile round the vertical axis. Poles at r = 0 become single vertices."""
    verts, faces, rings = [], [], []
    for r, y in prof:
        if r == 0:
            rings.append([len(verts)]); verts.append((0, 0, y))
        else:
            ring = []
            for j in range(seg):
                a = j / seg * math.tau; ring.append(len(verts)); verts.append((math.cos(a) * r, math.sin(a) * r, y))
            rings.append(ring)
    for A, Bb in zip(rings, rings[1:]):
        for j in range(seg):
            if len(A) == 1: faces.append((A[0], Bb[j], Bb[(j + 1) % seg]))
            elif len(Bb) == 1: faces.append((A[j], A[(j + 1) % seg], Bb[0]))
            else: faces.append((A[j], A[(j + 1) % seg], Bb[(j + 1) % seg], Bb[j]))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(38))
    return obj(name, me, mat)

# ---------- curves ----------
def catmull_centripetal(P, per=48):
    """Three.js CatmullRomCurve3('centripetal'), sampled densely along each segment."""
    n = len(P); out = []
    for i in range(n - 1):
        p0 = P[i - 1] if i > 0 else 2 * P[0] - P[1]
        p1, p2 = P[i], P[i + 1]
        p3 = P[i + 2] if i + 2 < n else 2 * P[-1] - P[-2]
        dt0 = (p1 - p0).length_squared ** 0.25; dt1 = (p2 - p1).length_squared ** 0.25; dt2 = (p3 - p2).length_squared ** 0.25
        if dt1 < 1e-4: dt1 = 1.0
        if dt0 < 1e-4: dt0 = dt1
        if dt2 < 1e-4: dt2 = dt1
        t1 = ((p1 - p0) / dt0 - (p2 - p0) / (dt0 + dt1) + (p2 - p1) / dt1) * dt1
        t2 = ((p2 - p1) / dt1 - (p3 - p1) / (dt1 + dt2) + (p3 - p2) / dt2) * dt1
        c0, c1 = p1, t1
        c2 = -3 * p1 + 3 * p2 - 2 * t1 - t2
        c3 = 2 * p1 - 2 * p2 + t1 + t2
        for k in range(per):
            t = k / per; out.append(c0 + c1 * t + c2 * t * t + c3 * t * t * t)
    out.append(P[-1].copy())
    return out

def spaced(Pd, n):
    acc = [0.0]
    for a, b in zip(Pd, Pd[1:]): acc.append(acc[-1] + (b - a).length)
    L = acc[-1]; res = []; j = 0
    for i in range(n + 1):
        s = L * i / n
        while j < len(acc) - 2 and acc[j + 1] < s: j += 1
        seg = acc[j + 1] - acc[j]; t = 0 if seg == 0 else (s - acc[j]) / seg
        res.append(Pd[j].lerp(Pd[j + 1], t))
    return res, L

def frames(P, up=Vector((0, 1, 0))):
    n = len(P)
    T = [(P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized() for i in range(n)]
    n0 = up.cross(T[0])
    if n0.length_squared < 1e-6: n0 = Vector((1, 0, 0)).cross(T[0])
    N = [n0.normalized()]
    for i in range(1, n):
        v = N[-1] - T[i] * N[-1].dot(T[i]); N.append(v.normalized())
    Bn = [T[i].cross(N[i]) for i in range(n)]
    return T, N, Bn

def tube(name, P, r, radial, uv_len, mat, caps=False):
    """Tube along points P (already in Blender space) with UVs: U = length / uv_len, V = round."""
    T, N, Bn = frames(P, Vector((0, 0, 1)))
    verts = []; s = [0.0]
    for i in range(1, len(P)): s.append(s[-1] + (P[i] - P[i - 1]).length)
    for i, p in enumerate(P):
        for j in range(radial):
            a = j / radial * math.tau; d = N[i] * math.cos(a) + Bn[i] * math.sin(a)
            verts.append(p + d * r)
    faces, uvs = [], []
    for i in range(len(P) - 1):
        for j in range(radial):
            a, b = i * radial + j, i * radial + (j + 1) % radial
            faces.append((a, b, b + radial, a + radial))
            u0, u1 = s[i] / uv_len, s[i + 1] / uv_len; v0, v1 = j / radial, (j + 1) / radial
            uvs += [(u0, v0), (u0, v1), (u1, v1), (u1, v0)]
    if caps:  # flat ends, for line ends that show
        last = (len(P) - 1) * radial
        faces.append(tuple(range(radial - 1, -1, -1))); uvs += [(0, 0)] * radial
        faces.append(tuple(range(last, last + radial))); uvs += [(0, 0)] * radial
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    lay = me.uv_layers.new(name='UVMap')
    flat = [c for uv in uvs for c in uv]; lay.data.foreach_set('uv', flat)
    me.shade_smooth()
    if caps: me.set_sharp_from_angle(angle=math.radians(60))
    return obj(name, me, mat)

def whipping(name, end, direction, R, color):
    """A whipping at a line's end: tight turns of twine over 3 diameters, the end cut and heat-sealed."""
    d = direction.normalized(); L = R * 3.2
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=R * 1.1, radius2=R * 1.1, depth=L)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.set_sharp_from_angle(angle=math.radians(50))
    o = obj(name, me, whip_mat(color), end - d * (L / 2 - R * 0.2))
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    return o

def three_strand(name, pts3, R=0.013, lay=0.085, whip=None, per=None):
    """rope() from the Three.js page: three strands as helices round the centreline, a dark core between them.
    pts3 are Three.js-space points (anything with .x .y .z)."""
    P0 = [B(p.x, p.y, p.z) for p in pts3]
    dense = catmull_centripetal(P0, per or (48 if len(P0) < 200 else 3))
    L = sum((b - a).length for a, b in zip(dense, dense[1:]))
    n = math.ceil(L / min(0.002, lay / 32))
    P, L = spaced(dense, n)
    T, N, Bn = frames(P, Vector((0, 0, 1)))
    a, rs = R * 0.56, R * 0.52
    for k in range(3):
        Q = []
        for i, p in enumerate(P):
            th = (i / n) * L / lay * math.tau + k * math.tau / 3
            Q.append(p + N[i] * (math.cos(th) * a) + Bn[i] * (math.sin(th) * a))
        tube(f'{name}-strand{k}', Q, rs, 14, 0.03, rope_mat(f'rope{k}', tracer=(k == 0)))
    tube(f'{name}-core', P, R * 0.5, 8, 1.0, simple('rope-core', '#7d7466', 1.0))
    if whip: whipping(f'{name}-whip', P[-1], P[-1] - P[-2], R, whip)

def braid(name, pts3, R, base, fleck, shiny=False, whip=None, whipStart=None, fine=None):
    """braid() from the Three.js page: a plaited cover over the centreline."""
    P0 = [B(p.x, p.y, p.z) for p in pts3]
    dense = catmull_centripetal(P0, 4 if len(P0) > 60 else 24)
    L = sum((b - a).length for a, b in zip(dense, dense[1:]))
    P, L = spaced(dense, max(8, math.ceil(L / (R * 0.3))))
    tube(name, P, R, 28, math.tau * R, braid_mat(name, base, fleck, shiny, fine or 1.0, R), caps=True)
    if whip: whipping(f'{name}-whip', P[-1], P[-1] - P[-2], R, whip)
    if whipStart: whipping(f'{name}-whip0', P[0], P[0] - P[1], R, whipStart)

# ---------- an exported Three.js scene (export.html -> scenes/<name>.glb + .json) ----------
class V3:
    def __init__(s, a): s.x, s.y, s.z = a

def load_exported(path_noext, rope_fn=None):
    """Import the glTF (everything but the ropes), swap named materials for procedural ones, rebuild the ropes."""
    with open(path_noext + '.json') as f: d = json.load(f)
    bpy.ops.import_scene.gltf(filepath=path_noext + '.glb')
    mats = scene_materials()
    for o in list(col.all_objects):
        if o.type != 'MESH': continue
        for slot in o.material_slots:
            if slot.material is None: continue
            key = slot.material.name.split('.')[0]
            if key in mats: slot.material = mats[key]
            if key == 'water': o.scale.x *= 40; o.scale.y *= 40  # reach the horizon
    if not any(s.material and s.material.name.split('.')[0] == 'water' for o in col.all_objects if o.type == 'MESH' for s in o.material_slots):
        # scenes without their own sea get one, so the horizon is water rather than the sky's dark ground
        lo = min((o.matrix_world @ Vector(c)).z for o in col.all_objects if o.type == 'MESH' for c in o.bound_box)
        wm = bpy.data.meshes.new('sea'); wm.from_pydata([(-600, -600, 0), (600, -600, 0), (600, 600, 0), (-600, 600, 0)], [], [(0, 1, 2, 3)])
        obj('sea', wm, mats['water'], (0, 0, lo - 0.6))
    for i, r in enumerate(d['ropes']):
        if rope_fn: r['P'] = rope_fn(i, r['P'])          # a figure can re-route a rope (Three.js space points)
        pts = [V3(p) for p in r['P']]
        if r['type'] == 'laid':
            three_strand(f'rope{i}', pts, r['R'], r['lay'], whip=r.get('whip'))
        else:
            braid(f'braid{i}', pts, r['R'], r['base'], r['fleck'], r['shiny'], r.get('whip'), r.get('whipStart'), r.get('fine'))
    return d

# ---------- light, camera, render ----------
def sky(sun_pos3, sun_target3, strength=0.22, sun_intensity=0.6):
    scene = bpy.context.scene
    world = bpy.data.worlds.new('sky'); scene.world = world
    try: world.use_nodes = True
    except Exception: pass
    wt = world.node_tree; wt.nodes.clear()
    wout = wt.nodes.new('ShaderNodeOutputWorld'); bg = wt.nodes.new('ShaderNodeBackground')
    sk = wt.nodes.new('ShaderNodeTexSky')
    d3 = [p - t for p, t in zip(sun_pos3, sun_target3)]
    sun_dir = B(*d3).normalized()
    elev = math.asin(sun_dir.z); azim = math.atan2(sun_dir.x, sun_dir.y)
    types = [i.identifier for i in sk.bl_rna.properties['sky_type'].enum_items]
    for t in ('MULTIPLE_SCATTERING', 'SINGLE_SCATTERING', 'NISHITA'):
        if t in types: sk.sky_type = t; break
    for k, v in (('sun_elevation', elev), ('sun_rotation', azim), ('altitude', 50.0), ('air_density', 1.0), ('aerosol_density', 1.8), ('dust_density', 1.8), ('ozone_density', 1.0), ('sun_intensity', sun_intensity), ('sun_disc', True)):
        if hasattr(sk, k): setattr(sk, k, v)
    wt.links.new(sk.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = strength
    wt.links.new(bg.outputs['Background'], wout.inputs['Surface'])

def camera_lookat(pos3, target3, fov_y):
    scene = bpy.context.scene
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 24.0; cd.angle_y = math.radians(fov_y)
    cam = bpy.data.objects.new('cam', cd); col.objects.link(cam); scene.camera = cam
    cam.location = B(*pos3); target = B(*target3)
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    return cam

def camera_matrix(m16, fov_y):
    """A Three.js camera.matrixWorld (column-major array) -> a Blender camera. Both look down local -Z with +Y up."""
    scene = bpy.context.scene
    M = Matrix([[m16[c * 4 + r] for c in range(4)] for r in range(4)])
    C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 24.0; cd.angle_y = math.radians(fov_y)
    cam = bpy.data.objects.new('cam', cd); col.objects.link(cam); scene.camera = cam
    cam.matrix_world = C @ M
    return cam

def focus_on_centre(cam, fstop):
    """Depth of field focused on whatever the centre of the frame hits."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    origin = cam.matrix_world.translation; direction = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    hit, loc, *_ = bpy.context.scene.ray_cast(dg, origin, direction)
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop
    cam.data.dof.focus_distance = (loc - origin).length if hit else 2.0

def render(out, samples=256, scale=100, exposure=-0.6, labels=(), note=None, blend='', space='three', arrows=(), extra=None):
    """Render to `out` (JPEG) and write <out>.labels.json with the label anchors in pixels.
    labels: [(point, text) or (point, text, colour)]; arrows: [(from, to, colour)]; points in Three.js space,
    or Blender space with space='blender'. extra: more keys for the labels file (e.g. {'bloom': 1.0})."""
    scene = bpy.context.scene; cam = scene.camera
    r = scene.render
    r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, scale
    r.image_settings.file_format = 'JPEG'; r.image_settings.quality = 92
    scene.cycles.samples = samples; scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'METAL'; prefs.get_devices()
        for dv in prefs.devices: dv.use = True
        scene.cycles.device = 'GPU'
    except Exception as e:
        print('GPU setup failed, CPU render:', e)
    vs = scene.view_settings
    try: vs.view_transform = 'AgX'
    except Exception: pass
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
        try: vs.look = look; break
        except Exception: pass
    vs.exposure = exposure + scene.get('exposure_offset', 0.0)   # kit.day_sky can darken all daylight scenes at once
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    P = (lambda p: Vector(p)) if space == 'blender' else (lambda p: B(*p))
    px = lambda p: (lambda q: (q.x * W, (1 - q.y) * H))(world_to_camera_view(scene, cam, P(p)))
    lab = []
    for item in labels:
        x, y = px(item[0]); d = {'text': item[1], 'x': x, 'y': y}
        if len(item) > 2: d['color'] = item[2]
        if len(item) > 3: d['dx'], d['dy'] = item[3]   # the pill moved off its anchor by (dx, dy) px, on a leader line
        lab.append(d)
    arr = [{'from': px(a), 'to': px(b), 'color': c} for a, b, c in arrows]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    r.filepath = os.path.abspath(out)
    if blend: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
    t0 = time.time()
    bpy.ops.render.render(write_still=True); print('render s', round(time.time() - t0, 1), '->', r.filepath)
    with open(os.path.splitext(os.path.abspath(out))[0] + '.labels.json', 'w') as f:
        json.dump({'note': note, 'labels': lab, 'arrows': arr, **(extra or {})}, f)
