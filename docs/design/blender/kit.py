# Scene kit for the figure types (sail, buoys, encounters, lights, day shapes, anchoring, bay), built on the
# downloaded models in models/ (see models/README.md). Blender space throughout: Z up, the sea surface at z = 0.
#
# The yacht is the Jeanneau Sun Odyssey 49DS from 3D Warehouse. In its own file the bow points along +X
# (stem x 10.8, transom x -3.8), the centreline is y 0.13, the deck is at z 3.5 and the waterline at z 2.0.
import os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import common as C
from common import node, link, setin, math_, ramp, mixc, lin, new_mat, obj_coords, noise, bump_from

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, 'models')
WL = 2.0                     # yacht waterline in model space
MAST = Vector((4.93, 0.13))  # mast centre, model space (x, y)
FORESTAY = (Vector((10.62, 0.13, 3.95)), Vector((5.25, 0.13, 20.1)))   # tack and head of the forestay

def deg(a): return math.radians(a)

# ---------- import helpers ----------
def import_glb(path, into=None):
    """Import a glTF/GLB, move what it brought into a new collection (linked under `into` or the scene) and
    return (collection, objects)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    name = os.path.splitext(os.path.basename(path))[0]
    coll = bpy.data.collections.new(name); (into or bpy.context.scene.collection).children.link(coll)
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        coll.objects.link(o)
    return coll, new

def fix_normals(objs):
    """SketchUp exports carry custom normals that turn mirrored parts black: drop them, smooth by angle."""
    seen = set()
    for o in objs:
        if o.type != 'MESH' or o.data in seen: continue
        me = o.data; seen.add(me)
        try:
            with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
        except Exception:
            pass
        me.shade_smooth()
        try: me.set_sharp_from_angle(angle=deg(35))
        except Exception: pass

def _line_like(o):
    """A rope or wire: long, with a tiny surface for its length (a 1 cm tube has area/length about 0.06)."""
    lo, hi = bbox([o]); L = (hi - lo).length
    if L < 2.0: return False
    sc = max(o.matrix_world.to_scale())
    area = sum(p.area for p in o.data.polygons) * sc * sc
    return area / L < 0.15

def parent_all(objs, parent):
    for o in objs:
        if o.parent is None:
            o.parent = parent

def base_color(mat):
    if not mat or not mat.node_tree: return None
    b = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not b or b.inputs['Base Color'].is_linked: return None
    return tuple(b.inputs['Base Color'].default_value[:3])

def bbox(objs):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs:
        if o.type != 'MESH' or o.hide_render: continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi

# ---------- materials ----------
_M = {}
def mats():
    """The procedural set, made once per scene."""
    if not _M:
        _M.update(C.scene_materials())
        _M['hull'] = C.gel_mat('hull-white')
        _bsdf(_M['hull']).inputs['Base Color'].default_value = lin(YACHT_WHITE)   # toned down so it holds detail in sun
        _M['navy'] = C.simple('navy', '#1d2c4f', 0.25, coat=1.0)
        _M['boot'] = C.simple('boot', '#16213b', 0.3, coat=0.8)
        _M['antifoul'] = C.simple('antifoul', '#2a2d33', 0.85)
        _M['grey'] = C.simple('deck-grey', '#9da3a8', 0.5)
        _M['dark'] = C.simple('dark-fitting', '#1b1c1e', 0.45, 0.3)
        _M['cloth'] = sail_mat()
        _M['red'] = C.simple('paint-red', '#c4161c', 0.35, coat=0.6)
        _M['green'] = C.simple('paint-green', '#0e8a3a', 0.35, coat=0.6)
        _M['yellow'] = C.simple('paint-yellow', '#f2c200', 0.35, coat=0.6)
        _M['black'] = C.simple('paint-black', '#111214', 0.4, coat=0.6)
    return _M

def sail_mat():
    """Dacron sailcloth: off-white, horizontal panel seams, a little light through it when backlit."""
    m, nt, b, out = new_mat('sailcloth')
    oc = obj_coords(nt); sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, sep.inputs['Vector'])
    seam = math_(nt, 'LESS_THAN', math_(nt, 'FRACT', math_(nt, 'DIVIDE', sep.outputs['Z'], 0.95)), 0.012)
    weave = noise(nt, oc, 400.0, 3.0)
    c = mixc(nt, seam, lin(SAIL_WHITE), lin('#bdb9ad'))
    wr = ramp(nt, [(0.4, (0.96, 0.96, 0.96, 1)), (0.6, (1, 1, 1, 1))]); link(nt, weave, wr.inputs['Fac'])
    link(nt, mixc(nt, 1.0, c, wr.outputs['Color'], 'MULTIPLY'), b.inputs['Base Color'])
    setin(b, 'Roughness', 0.6); setin(b, 'Sheen Weight', 0.3)
    # thin, slightly translucent cloth: mix in a translucent BSDF so the sun glows through
    tr = node(nt, 'ShaderNodeBsdfTranslucent'); setin(tr, 'Color', lin('#e8e2cf'))
    mx = node(nt, 'ShaderNodeMixShader'); setin(mx, 'Fac', 0.22)
    link(nt, b.outputs[0], mx.inputs[1]); link(nt, tr.outputs[0], mx.inputs[2]); link(nt, mx.outputs[0], out.inputs['Surface'])
    bump_from(nt, b, seam, 0.3, 0.002)
    return m

# ---------- the yacht ----------
class Yacht:
    """One Sun Odyssey 49DS. `root` is an empty at the waterline under the mast foot... placed with place()."""
    def __init__(self, root, objs, boom_pivot):
        self.root, self.objs, self.boom_pivot = root, objs, boom_pivot
    def place(self, x=0.0, y=0.0, heading=0.0, heel=0.0):
        """Heading in degrees, 0 = bow towards +Y (north), clockwise like a compass. Heel to starboard positive."""
        self.root.location = (x, y, 0.0)
        self.root.rotation_euler = Euler((deg(heel), 0.0, deg(90 - heading)), 'XYZ')  # roll about the length (model X)
        return self
    def world(self, p):
        """A model-space point (as in the GLB) in world space, after place()."""
        bpy.context.view_layer.update()
        return self.root.matrix_world @ (Vector(p) - Vector((MAST.x, MAST.y, WL)))

def load_yacht(hull='white', boom=None, spinnaker=False, sails=None, name='yacht'):
    """Import the Sun Odyssey, swap its SketchUp colours for real materials and hang it under an empty whose origin
    is the mast foot at the waterline. boom: degrees off the centreline, + to port. sails: None, or a dict
    {'main': True, 'genoa': 'port'|'starboard', 'boom': deg} to hoist cloth."""
    path = os.path.join(MODELS, 'sun-odyssey-49ds.glb')
    coll, objs = import_glb(path)
    M = mats()
    fix_normals(objs)
    for o in objs:
        if o.type != 'MESH': continue
        for s in o.material_slots:
            m = s.material; nm = m.name if m else ''
            if nm.startswith('[Color_H01]2'):           # the spinnaker
                o.hide_render = not spinnaker; continue
            if not spinnaker and nm[:8] in ('[Color_G', '[Color_F', '[Color_H', '[Color_E') and _line_like(o):
                o.hide_render = True; continue          # its sheets and guys, coloured lines running outboard
            if nm.startswith('[Color_I17]'):            # dark blue topsides
                s.material = M['hull'] if hull == 'white' else M['navy']; continue
            if nm.startswith('Teak'): s.material = M['teak']; continue
            if 'Glass' in nm: s.material = M['glass']; continue
            c = base_color(m)
            if c is None: continue
            l = sum(c) / 3
            if l > 0.85: s.material = M['hull']
            elif 0.7 < l <= 0.85: s.material = M['satin'] if max(c) - min(c) < 0.05 else s.material
            elif 0.5 < l <= 0.7 and max(c) - min(c) < 0.05: s.material = M['grey']
            elif l < 0.15 and max(c) - min(c) < 0.05: s.material = M['dark']
    root = bpy.data.objects.new(name, None); C.col.objects.link(root)
    for o in objs:
        if o.parent is None:
            o.parent = root; o.location = Vector(o.location) - Vector((MAST.x, MAST.y, WL))
    # the boom and everything on it (stack-pack, outhaul) swing round the mast on a pivot
    pivot = bpy.data.objects.new(name + '-boom', None); C.col.objects.link(pivot); pivot.parent = root
    pivot.location = (0.0, 0.0, 5.3 - WL)
    bpy.context.view_layer.update()
    for o in objs:
        if o.type != 'MESH': continue
        lo, hi = bbox([o])
        if lo.x > -1.2 and hi.x < MAST.x + 0.02 and lo.z > 5.0 and hi.z < 7.6 and abs((lo.y + hi.y) / 2 - MAST.y) < 0.8:
            mw = o.matrix_world.copy(); o.parent = pivot; o.matrix_world = mw
    y = Yacht(root, objs, pivot)
    if boom is not None: pivot.rotation_euler = (0, 0, deg(boom))
    if sails: hoist(y, **sails)
    return y

# ---------- sails ----------
def sail_surface(name, luff0, luff1, clew, camber, side, twist=0.0, nu=26, nv=40, roach=0.0, parent=None):
    """A sail as a cambered surface. luff0/luff1: tack and head; clew: clew point (model space, mast-relative).
    camber: depth as a fraction of chord; side: +1 bellies to +Y (port), -1 to starboard. twist: degrees the leech
    opens at the head."""
    verts, faces = [], []
    for j in range(nv + 1):
        v = j / nv
        L = luff0.lerp(luff1, v)                       # luff point at this height
        foot_leech = clew.lerp(luff1, v)               # straight leech line from clew to head
        chord = foot_leech - L
        # twist: rotate the chord about the luff, more towards the head
        ang = deg(twist) * v * side
        rot = Matrix.Rotation(ang, 3, 'Z')
        chord = rot @ chord
        n = Vector((-chord.y, chord.x, 0.0))
        n = n.normalized() if n.length > 1e-6 else Vector((0, 1, 0))
        if n.y * side < 0: n = -n
        for i in range(nu + 1):
            u = i / nu
            depth = camber * chord.length * (4 * u * (1 - u)) * (1 - 0.35 * v) * (u ** 0.15)
            r = roach * math.sin(math.pi * v) * u ** 4 * chord.length
            p = L + chord * u + n * (depth + r * 0.0) + chord.normalized() * r
            verts.append(p)
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i; faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update(); me.shade_smooth()
    o = C.obj(name, me, mats()['cloth'])
    if parent: o.parent = parent
    sol = o.modifiers.new('cloth', 'SOLIDIFY'); sol.thickness = 0.004
    return o

def hoist(y, main=True, genoa=None, boom=None, camber=0.11, genoa_camber=0.13):
    """Mainsail on the boom angle, genoa sheeted to the given side ('port' or 'starboard')."""
    if boom is not None: y.boom_pivot.rotation_euler = (0, 0, deg(boom))
    b = deg(y.boom_pivot.rotation_euler.z if boom is None else boom) if False else y.boom_pivot.rotation_euler.z
    side = 1 if b > 0 else -1
    if main:
        tack = Vector((-0.12, 0.0, 5.5 - WL)); head = Vector((-0.1, 0.0, 20.0 - WL))
        boom_len = 5.4; clew = Vector((-math.cos(b) * boom_len, math.sin(b) * boom_len * 1.0, 5.55 - WL))
        # the boom swings aft of the mast: angle measured from the centreline aft, + to port (+Y)
        clew = Vector((-boom_len * math.cos(b), boom_len * math.sin(b), 5.55 - WL))
        sail_surface('main', tack, head, clew, camber, side, twist=12, roach=0.06, parent=y.root)
    if genoa:
        gs = 1 if genoa == 'port' else -1
        t0 = FORESTAY[0] - Vector((MAST.x, MAST.y, WL)); t1 = FORESTAY[1] - Vector((MAST.x, MAST.y, WL))
        t1 = t0.lerp(t1, 0.93)
        clew = Vector((-2.2, gs * 1.95, 4.35 - WL))
        sail_surface('genoa', t0, t1, clew, genoa_camber, gs, twist=8, parent=y.root)

# ---------- sea and sky ----------
SEA_STATES = {  # wind m/s, wave height scale, choppiness, tile size m
    'calm': dict(wind=3.0, wave_scale=0.12, chop=0.8, size=30.0),
    'breeze': dict(wind=7.0, wave_scale=0.32, chop=1.3, size=36.0),
    'fresh': dict(wind=10.0, wave_scale=0.55, chop=1.5, size=48.0),
}

def sea(state=None, wind=6.0, wave_scale=1.0, chop=1.0, size=60.0, res=11, repeat=6, center=(0, 0), color='#0c2e3a', foam=True):
    """A real wave field (Blender's Ocean modifier) tiled round `center`, and a flat sea beyond it to the horizon.
    state: 'calm', 'breeze' or 'fresh' sets wind, wave height, chop and tile size together."""
    if state: wind, wave_scale, chop, size = (SEA_STATES[state][k] for k in ('wind', 'wave_scale', 'chop', 'size'))
    me = bpy.data.meshes.new('ocean'); o = C.obj('ocean', me, None)
    md = o.modifiers.new('ocean', 'OCEAN')
    md.geometry_mode = 'GENERATE'; md.resolution = res; md.spatial_size = int(size); md.repeat_x = repeat; md.repeat_y = repeat
    md.wave_scale = wave_scale; md.choppiness = chop; md.wind_velocity = wind; md.wave_alignment = 0.3
    md.random_seed = 7
    if foam:
        md.use_foam = True; md.foam_layer_name = 'foam'; md.foam_coverage = 0.25
    o.location = (center[0] - size * repeat / 2, center[1] - size * repeat / 2, 0.0)
    m = sea_mat(color, foam); o.data.materials.append(m)
    far = bpy.data.meshes.new('far-sea'); far.from_pydata([(-8000, -8000, 0), (8000, -8000, 0), (8000, 8000, 0), (-8000, 8000, 0)], [], [(0, 1, 2, 3)])
    fo = C.obj('far-sea', far, sea_mat(color, False, far=True), (center[0], center[1], -0.02))
    return o

def sea_mat(color='#0c2e3a', foam=True, far=False):
    m, nt, b, _ = new_mat('sea-far' if far else 'sea')
    setin(b, 'Base Color', lin(color)); setin(b, 'Roughness', 0.06 if far else 0.03); setin(b, 'IOR', 1.333)
    oc = obj_coords(nt)
    # capillary ripples on top of the waves
    mp = node(nt, 'ShaderNodeMapping'); setin(mp, 'Scale', (1.0, 2.2, 1.0)); link(nt, oc, mp.inputs['Vector'])
    r1 = node(nt, 'ShaderNodeTexNoise', in_Scale=1.6 if not far else 0.4, in_Detail=8.0, in_Roughness=0.6); link(nt, mp.outputs['Vector'], r1.inputs['Vector'])
    bump_from(nt, b, r1.outputs['Fac'], 0.12 if not far else 0.35, 0.05)
    if foam:
        at = node(nt, 'ShaderNodeAttribute', attribute_name='foam')
        fr = ramp(nt, [(0.25, (0, 0, 0, 1)), (0.6, (1, 1, 1, 1))]); link(nt, at.outputs['Fac'], fr.inputs['Fac'])
        fm = math_(nt, 'MULTIPLY', fr.outputs['Color'], noise(nt, oc, 3.0, 6.0))
        link(nt, mixc(nt, fm, lin(color), lin('#e9eef0')), b.inputs['Base Color'])
        rr = node(nt, 'ShaderNodeMix', data_type='FLOAT'); link(nt, fm, rr.inputs['Factor']); setin(rr, 2, 0.03); setin(rr, 3, 0.7); link(nt, rr.outputs[0], b.inputs['Roughness'])
    return m

YACHT_WHITE = '#979995'   # gelcoat, decks: white but not blown out
SAIL_WHITE = '#b0ada3'    # dacron

def _bsdf(m): return next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')

DAY_HAZE = 0.35   # scales every scene's haze: lower = deeper blue sky, more contrast against sunlit boats and sea
DAY_SUN = 0.75    # sun disc intensity, so subjects stay bright while the sky darkens
DAY_SKY_VALUE = 0.32   # brightness of the sky as seen in the picture (1 = as lit)
DAY_SKY_SAT = 1.2      # and its colour saturation
DAY_EXPOSURE = -0.3    # extra exposure for every daylight scene, on top of each script's own

def day_sky(sun_az=210.0, sun_el=35.0, strength=0.25, haze=1.6):
    """Sky with the sun at compass azimuth sun_az (from +Y clockwise) and elevation sun_el."""
    a, e = deg(sun_az), deg(sun_el)
    d = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    C.sky((d.x * 10, d.z * 10, -d.y * 10), (0, 0, 0), strength, sun_intensity=DAY_SUN)   # common.sky takes Three.js axes
    bpy.context.scene['exposure_offset'] = DAY_EXPOSURE
    wt = bpy.context.scene.world.node_tree
    sk = next(n for n in wt.nodes if n.type == 'TEX_SKY')
    for k, v in (('aerosol_density', haze * DAY_HAZE), ('dust_density', haze * DAY_HAZE)):
        if hasattr(sk, k): setattr(sk, k, v)
    darken_visible_sky()

def darken_visible_sky():
    """The daylight look shared by every scene: the sky seen directly by the camera darker and bluer than the
    light it gives (contrast without dulling), the frame DAY_EXPOSURE darker, white gelcoat toned down.
    Works on any world made by common.sky()."""
    bpy.context.scene['exposure_offset'] = DAY_EXPOSURE
    for m in bpy.data.materials:
        if m.name.startswith('gelcoat') and m.node_tree: _bsdf(m).inputs['Base Color'].default_value = lin(YACHT_WHITE)
    wt = bpy.context.scene.world.node_tree
    sk = next(n for n in wt.nodes if n.type == 'TEX_SKY')
    bg = next(n for n in wt.nodes if n.type == 'BACKGROUND')
    hs = wt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = DAY_SKY_SAT; hs.inputs['Value'].default_value = DAY_SKY_VALUE
    wt.links.new(sk.outputs['Color'], hs.inputs['Color'])
    lp = wt.nodes.new('ShaderNodeLightPath')
    mx = wt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    wt.links.new(lp.outputs['Is Camera Ray'], mx.inputs['Factor']); wt.links.new(sk.outputs['Color'], mx.inputs[6]); wt.links.new(hs.outputs['Color'], mx.inputs[7])
    wt.links.new(mx.outputs[2], bg.inputs['Color'])

def night_sky(moon=0.004, stars=True):
    """A dark night: deep blue-black sky brighter at the horizon, faint stars, a little moonlight."""
    scene = bpy.context.scene
    world = bpy.data.worlds.new('night'); scene.world = world
    wt = world.node_tree; wt.nodes.clear()
    out = wt.nodes.new('ShaderNodeOutputWorld'); bg = wt.nodes.new('ShaderNodeBackground')
    tc = wt.nodes.new('ShaderNodeTexCoord'); sep = wt.nodes.new('ShaderNodeSeparateXYZ'); wt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    grad = wt.nodes.new('ShaderNodeValToRGB'); el = grad.color_ramp.elements
    el[0].position = 0.0; el[0].color = (0.006, 0.009, 0.018, 1); el[1].position = 0.18; el[1].color = (0.0012, 0.0018, 0.0045, 1)
    wt.links.new(sep.outputs['Z'], grad.inputs['Fac'])
    col = grad.outputs['Color']
    if stars:
        vor = wt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 420.0
        wt.links.new(tc.outputs['Generated'], vor.inputs['Vector'])
        st = wt.nodes.new('ShaderNodeValToRGB'); st.color_ramp.elements[0].position = 0.0; st.color_ramp.elements[0].color = (0.6, 0.62, 0.7, 1)
        st.color_ramp.elements[1].position = 0.035; st.color_ramp.elements[1].color = (0, 0, 0, 1)
        wt.links.new(vor.outputs['Distance'], st.inputs['Fac'])
        up = wt.nodes.new('ShaderNodeMath'); up.operation = 'GREATER_THAN'; up.inputs[1].default_value = 0.02; wt.links.new(sep.outputs['Z'], up.inputs[0])
        rnd = wt.nodes.new('ShaderNodeMath'); rnd.operation = 'GREATER_THAN'; rnd.inputs[1].default_value = 0.55
        sepc = wt.nodes.new('ShaderNodeSeparateColor'); wt.links.new(vor.outputs['Color'], sepc.inputs['Color']); wt.links.new(sepc.outputs[0], rnd.inputs[0])
        m1 = wt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; wt.links.new(up.outputs[0], m1.inputs[0]); wt.links.new(rnd.outputs[0], m1.inputs[1])
        mix = wt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'ADD'
        wt.links.new(m1.outputs[0], mix.inputs['Factor']); wt.links.new(col, mix.inputs[6]); wt.links.new(st.outputs['Color'], mix.inputs[7])
        col = mix.outputs[2]
    wt.links.new(col, bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0
    wt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    if moon:
        ld = bpy.data.lights.new('moon', 'SUN'); ld.energy = moon * 300; ld.color = (0.75, 0.82, 1.0); ld.angle = deg(0.5)
        lo = bpy.data.objects.new('moon', ld); C.col.objects.link(lo); lo.rotation_euler = (deg(70), 0, deg(200))

def nav_light(name, p, color, power=2.0, radius=0.05, cone=None):
    """A navigation light: a small glowing lens and a point light, so it lights its surroundings and shows in
    reflections. color: 'red', 'green', 'white', 'yellow'."""
    rgb = {'red': (1.0, 0.05, 0.03), 'green': (0.05, 1.0, 0.25), 'white': (1.0, 0.92, 0.75), 'yellow': (1.0, 0.75, 0.1)}[color]
    m, nt, b, out = new_mat(name + '-lens')
    em = node(nt, 'ShaderNodeEmission'); setin(em, 'Color', rgb + (1,)); setin(em, 'Strength', 60.0)
    link(nt, em.outputs[0], out.inputs['Surface'])
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=radius)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = C.obj(name, me, m, Vector(p))
    ld = bpy.data.lights.new(name, 'POINT'); ld.energy = power; ld.color = rgb; ld.shadow_soft_size = radius
    lo = bpy.data.objects.new(name + '-lamp', ld); C.col.objects.link(lo); lo.location = Vector(p)
    return o

# ---------- other models ----------
def load_model(file, keep=None, drop_planes=True, scale=1.0):
    """Import one of models/*.glb into its own empty. drop_planes removes big flat 'ground' or 'sea' parts the
    SketchUp author left in. keep: optional predicate on objects."""
    coll, objs = import_glb(os.path.join(MODELS, file))
    fix_normals(objs)
    root = bpy.data.objects.new(os.path.splitext(file)[0], None); C.col.objects.link(root)
    for o in objs:
        if o.parent is None: o.parent = root
    bpy.context.view_layer.update()
    if drop_planes:
        meshes = [o for o in objs if o.type == 'MESH']
        lo, hi = bbox(meshes); span = max(hi.x - lo.x, hi.y - lo.y)
        for o in meshes:
            l, h = bbox([o]); s = max(h.x - l.x, h.y - l.y)
            if s > 0.6 * span and (h.z - l.z) < 0.08 * span and len(o.data.polygons) < 400:
                o.hide_render = True
    if keep:
        for o in objs:
            if o.type == 'MESH' and not keep(o): o.hide_render = True
    root.scale = (scale,) * 3
    return root, objs

def recolor(objs, rule):
    """rule(base_colour_tuple, material_name) -> material or None (keep)."""
    for o in objs:
        if o.type != 'MESH': continue
        for s in o.material_slots:
            m = rule(base_color(s.material), s.material.name if s.material else '')
            if m is not None: s.material = m

def ground_on(root, objs, z=0.0):
    """Move a model so its lowest visible point sits at z (or its waterline when it floats, see draft)."""
    bpy.context.view_layer.update(); lo, hi = bbox(objs)
    root.location.z += z - lo.z
    return lo, hi

# ---------- coast, harbour ----------
def coast(distance=1800.0, bearing=0.0, length=6000.0, height=120.0, seed=3, town=True, color='#6f7a64'):
    """A hilly coastline `distance` metres away on compass `bearing` from the origin, running across the view:
    a ridge mesh fading into haze, a pale beach line, optionally a white town on the lower slopes."""
    rnd = random.Random(seed)
    a = deg(bearing); fwd = Vector((math.sin(a), math.cos(a), 0)); side = Vector((fwd.y, -fwd.x, 0))
    nx, ny = 160, 24; verts, faces = [], []
    ph = [rnd.random() * 10 for _ in range(4)]
    for j in range(ny + 1):
        dep = j / ny                                 # 0 at the shore, 1 inland
        for i in range(nx + 1):
            t = i / nx - 0.5
            h = height * (0.55 + 0.25 * math.sin(t * 9 + ph[0]) + 0.15 * math.sin(t * 23 + ph[1]) + 0.08 * math.sin(t * 61 + ph[2]))
            z = h * (dep ** 0.7) * (1 - 0.15 * dep) - 2.0 + 2.0 * min(1, dep * 8)
            p = fwd * (distance + dep * height * 6 + 40 * math.sin(t * 13 + ph[3])) + side * (t * length)
            verts.append((p.x, p.y, z))
    for j in range(ny):
        for i in range(nx):
            k = j * (nx + 1) + i; faces.append((k, k + 1, k + nx + 2, k + nx + 1))
    me = bpy.data.meshes.new('coast'); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
    m, nt, b, _ = new_mat('coast')
    oc = obj_coords(nt); sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, oc, sep.inputs['Vector'])
    veg = noise(nt, oc, 0.02, 6.0)
    c = ramp(nt, [(0.35, '#7d7a5c'), (0.55, color), (0.75, '#556347')]); link(nt, veg, c.inputs['Fac'])
    beach = math_(nt, 'LESS_THAN', sep.outputs['Z'], 1.2)
    col = mixc(nt, beach, c.outputs['Color'], lin('#d8cdb0'))
    if town:
        # white town: blocks of light colour low on the slope, broken up by noise
        tn = noise(nt, oc, 0.08, 2.0); tz = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', sep.outputs['Z'], 28.0), math_(nt, 'GREATER_THAN', sep.outputs['Z'], 2.0))
        tw = math_(nt, 'MULTIPLY', tz, math_(nt, 'GREATER_THAN', tn, 0.56))
        vor = node(nt, 'ShaderNodeTexVoronoi', in_Scale=0.6); link(nt, oc, vor.inputs['Vector'])
        sc = node(nt, 'ShaderNodeSeparateColor'); link(nt, vor.outputs['Color'], sc.inputs['Color'])
        houses = ramp(nt, [(0.0, '#efe9dc'), (0.6, '#e8e2d4'), (0.61, '#b8644a'), (1.0, '#c5755a')], 'CONSTANT'); link(nt, sc.outputs[0], houses.inputs['Fac'])
        col = mixc(nt, tw, col, houses.outputs['Color'])
    link(nt, col, b.inputs['Base Color']); setin(b, 'Roughness', 0.95)
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    distance_fog(nt, b.outputs[0], out.inputs['Surface'], half=distance * 1.1)
    o = C.obj('coast', me, m)
    return o

def haze(*_a, **_k):
    """Kept for old scripts: a world volume blocks the sky light entirely, so haze lives in the coast material
    (fog by camera distance, see coast())."""
    return None

def distance_fog(nt, bsdf_out, out_socket, half=1800.0, color=(0.62, 0.7, 0.8), strength=1.0):
    """Fade a surface into a pale sky colour with distance from the camera (aerial perspective)."""
    cd = node(nt, 'ShaderNodeCameraData')
    f = math_(nt, 'SUBTRACT', 1.0, math_(nt, 'EXPONENT', math_(nt, 'DIVIDE', cd.outputs['View Distance'], -half)))
    em = node(nt, 'ShaderNodeEmission'); setin(em, 'Color', color + (1,)); setin(em, 'Strength', strength)
    mx = node(nt, 'ShaderNodeMixShader'); link(nt, f, mx.inputs['Fac'])
    link(nt, bsdf_out, mx.inputs[1]); link(nt, em.outputs[0], mx.inputs[2]); link(nt, mx.outputs[0], out_socket)

def breakwater(p0, p1, width=8.0, height=3.0, light=None):
    """A rubble mole from p0 to p1 (x, y), with an optional light tower on its head ('red' or 'green')."""
    p0, p1 = Vector((p0[0], p0[1], 0)), Vector((p1[0], p1[1], 0)); d = p1 - p0; L = d.length
    o = C.obj('mole', C.rbox('mole', (L, width, height * 2), 1.2, 3), C.concrete_mat('mole-stone'))
    o.location = (p0 + p1) / 2; o.rotation_euler = (0, 0, math.atan2(d.y, d.x))
    if light:
        t = C.cyl('tower', 1.2, 1.0, 9.0, 24, mats()['red' if light == 'red' else 'green'], (p1.x, p1.y, height + 4.5))
        C.cyl('tower-top', 1.35, 1.35, 0.4, 24, mats()['black'], (p1.x, p1.y, height + 9.2))
    return o

# ---------- buoys ----------
def lateral_buoy(side='port', topmark=True, light=True, at=(0, 0), scale=1.0):
    """The Poly Haven lateral marker (photo-scanned, red) as a port mark, or tinted green as a starboard mark.
    IALA A topmarks: a red can for port, a green cone point up for starboard."""
    coll, objs = import_glb(os.path.join(MODELS, 'buoy-lateral-red', 'lateral_sea_marker.gltf'))
    root = bpy.data.objects.new('buoy-' + side, None); C.col.objects.link(root)
    for o in objs:
        if o.parent is None: o.parent = root
    if side == 'starboard':
        for o in objs:
            for s in getattr(o, 'material_slots', []):
                m = s.material.copy(); s.material = m; nt = m.node_tree
                b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
                src = b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].is_linked else None
                if src:
                    hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Hue'].default_value = 0.83; hs.inputs['Saturation'].default_value = 0.78; hs.inputs['Value'].default_value = 0.72
                    nt.links.new(src, hs.inputs['Color']); nt.links.new(hs.outputs['Color'], b.inputs['Base Color'])
    bpy.context.view_layer.update(); lo, hi = bbox(objs)
    top = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))
    M = mats(); col = M['red'] if side == 'port' else M['green']
    if topmark:
        if side == 'port':
            C.cyl('topmark', 0.32, 0.32, 0.6, 24, col, top + Vector((0, 0, 0.55))).parent = root
        else:
            C.cyl('topmark', 0.38, 0.0, 0.7, 24, col, top + Vector((0, 0, 0.6))).parent = root
        C.cyl('topmark-post', 0.03, 0.03, 0.3, 8, M['black'], top + Vector((0, 0, 0.1))).parent = root
    if light:
        nav_light('buoy-light', top + Vector((0, 0, -0.35)), 'red' if side == 'port' else 'green', power=3.0, radius=0.08).parent = root
    root.location = (at[0], at[1], 0.0); root.scale = (scale,) * 3
    return root, objs

def cardinal_buoy(which='north', at=(0, 0), height=4.6):
    """One of the four cardinal marks from 3D Warehouse, the sea disc it came on removed, scaled so the mark
    stands `height` metres above the water (topmark included)."""
    root, objs = load_model(f'buoy-cardinal-{which}.glb')
    bpy.context.view_layer.update()
    vis = [o for o in objs if o.type == 'MESH' and not o.hide_render]
    lo, hi = bbox(vis)
    k = height / ((hi.z - lo.z) * 0.85)               # about 15% of the model is below the waterline
    root.scale = (k,) * 3
    bpy.context.view_layer.update(); lo, hi = bbox(vis)
    root.location = (root.location.x + at[0] - (lo.x + hi.x) / 2, root.location.y + at[1] - (lo.y + hi.y) / 2,
                     root.location.z - lo.z - (hi.z - lo.z) * 0.15)
    return root, objs

def dan_buoy(at, color='#ff5a00'):
    """A man-overboard dan buoy: a float, a 2 m pole with an orange flag, and a horseshoe lifebuoy nearby."""
    M = mats(); p = Vector((at[0], at[1], 0))
    fl = C.cyl('dan-float', 0.18, 0.18, 0.5, 24, C.simple('dan', color, 0.4, coat=0.5), p + Vector((0, 0, 0.05)))
    C.cyl('dan-pole', 0.025, 0.02, 2.0, 12, M['black'], p + Vector((0, 0, 1.2)))
    fm = bpy.data.meshes.new('flag'); fm.from_pydata([(0, 0, 0), (0.45, 0, 0.02), (0.45, 0, 0.3), (0, 0, 0.32)], [], [(0, 1, 2, 3)])
    f = C.obj('dan-flag', fm, C.simple('flag', color, 0.7), p + Vector((0.02, 0, 1.85)))
    return fl

# ---------- day shapes ----------
def ball(p, r=0.3):
    return C.obj('ball', _sphere('ball', r), mats()['black'], Vector(p))

def cone(p, r=0.3, h=0.6, up=True):
    o = C.cyl('cone', r, 0.0, h, 24, mats()['black'], Vector(p))
    if not up: o.rotation_euler = (math.pi, 0, 0)
    return o

def _sphere(name, r):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.shade_smooth(); return me

# ---------- wakes (overhead views) ----------
def wake(y, length=40.0, width=10.0, strength=1.0):
    """A foam wake behind a yacht: a V of white water spreading from the stern plus a turbulent centre stripe.
    A transparent decal floating just over the waves, parented to the yacht."""
    me = bpy.data.meshes.new('wake'); L, Wd = length, width
    me.from_pydata([(-L, -Wd, 0), (0, -Wd, 0), (0, Wd, 0), (-L, Wd, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name='UVMap'); me.uv_layers[0].data.foreach_set('uv', [0, 0, 1, 0, 1, 1, 0, 1])
    m, nt, b, out = new_mat('wake')
    uv = node(nt, 'ShaderNodeUVMap'); sep = node(nt, 'ShaderNodeSeparateXYZ'); link(nt, uv.outputs['UV'], sep.inputs['Vector'])
    u = math_(nt, 'SUBTRACT', 1.0, sep.outputs['X'])           # 0 at the stern, 1 at the far end
    v = math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', sep.outputs['Y'], 2.0), 1.0))   # 0 centre, 1 edge
    arm = math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', v, math_(nt, 'MULTIPLY', u, 0.36)))                 # Kelvin arms at ~19.5°
    armm = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', arm, math_(nt, 'MULTIPLY_ADD', u, 0.06, 0.015)), math_(nt, 'SUBTRACT', 1.0, u))
    centre = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', v, math_(nt, 'MULTIPLY_ADD', u, 0.12, 0.04)), math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, u), 1.5))
    oc = obj_coords(nt); n1 = noise(nt, oc, 1.5, 8.0, 0.65)
    nr = ramp(nt, [(0.42, (0, 0, 0, 1)), (0.62, (1, 1, 1, 1))]); link(nt, n1, nr.inputs['Fac'])
    mask = math_(nt, 'MULTIPLY', math_(nt, 'MAXIMUM', armm, centre), nr.outputs['Color'])
    mask = math_(nt, 'MULTIPLY', mask, strength)
    setin(b, 'Base Color', lin('#eef3f4')); setin(b, 'Roughness', 0.8)
    tp = node(nt, 'ShaderNodeBsdfTransparent'); mx = node(nt, 'ShaderNodeMixShader')
    link(nt, mask, mx.inputs['Fac']); link(nt, tp.outputs[0], mx.inputs[1]); link(nt, b.outputs[0], mx.inputs[2]); link(nt, mx.outputs[0], out.inputs['Surface'])
    o = C.obj('wake', me, m); o.parent = y.root; o.location = (-(MAST.x + 3.8) + 0.5, 0.0, 0.25)
    o.visible_shadow = False
    return o

def camera(eye, look, lens=24.0):
    cd = bpy.data.cameras.new('cam'); cd.lens = lens; cam = bpy.data.objects.new('cam', cd); C.col.objects.link(cam)
    bpy.context.scene.camera = cam; e, t = Vector(eye), Vector(look)
    cam.location = e; cam.rotation_euler = (t - e).to_track_quat('-Z', 'Y').to_euler(); cd.clip_end = 20000
    return cam
