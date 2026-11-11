# Blender figures for bareboat-skipper/colregs, figures 14-16:
#   --fig 14  traffic separation scheme: two lanes with ships, the separation zone between them, our yacht crossing
#             at right angles (aerial oblique, day)
#   --fig 15  sound and light signals in sight, at night: a ship on our starboard bow, masthead white over red,
#             flashing five quick flashes from her signal lamp
#   --fig 16  restricted visibility: a helm view into fog, a grey ship shape ahead, the radar on the plotter
#             showing her as a target fine on the starboard bow
#   blender --background --factory-startup --python docs/design/blender/art_colregs_c.py -- --fig 14 [--out ...]
# Figure 16 draws its radar screen with the system Python (Pillow); it runs that step itself through subprocess.
import os, sys, math, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
RADAR_PNG = os.path.join(TEX, 'axiom-radar.png')

def prep_radar():
    """System Python: a radar picture (heading up, 0.75 nm range) on the Axiom's own front texture."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    W, H = 920, 610
    im = Image.new('RGB', (W, H), (4, 10, 22)); d = ImageDraw.Draw(im)
    cx, cy, R = W // 2, H // 2 + 20, 270
    for k in range(1, 4):
        r = R * k / 3; d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(40, 120, 150), width=2)
    for a in range(0, 360, 30):
        t = math.radians(a); d.line([(cx, cy), (cx + R * math.sin(t), cy - R * math.cos(t))], fill=(18, 55, 75), width=1)
    d.line([(cx, cy), (cx, cy - R)], fill=(220, 230, 240), width=3)              # heading line, straight up
    glow = Image.new('RGB', (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow)
    # sea clutter near the centre, and the target: 20 degrees on the starboard bow, two thirds out, with a trail
    import random; rnd = random.Random(4)
    for _ in range(260):
        r = rnd.random() ** 1.6 * 60; t = rnd.random() * math.tau
        g.ellipse([cx + r * math.sin(t) - 2, cy - r * math.cos(t) - 2, cx + r * math.sin(t) + 2, cy - r * math.cos(t) + 2], fill=(200, 160, 30))
    tb, tr = math.radians(20), R * 0.62
    tx, ty = cx + tr * math.sin(tb), cy - tr * math.cos(tb)
    for k in range(9):    # the echo trail, behind her (she heads 200: comes towards us)
        q = tr + k * 7; px, py = cx + q * math.sin(tb), cy - q * math.cos(tb)
        g.ellipse([px - 7, py - 5, px + 7, py + 5], fill=(int(120 - 12 * k), int(90 - 9 * k), 20))
    g.ellipse([tx - 13, ty - 9, tx + 13, ty + 9], fill=(255, 215, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(1.5)); im = Image.composite(glow, im, glow.convert('L').point(lambda v: 255 if v > 8 else 0))
    d = ImageDraw.Draw(im)
    d.ellipse([tx - 22, ty - 22, tx + 22, ty + 22], outline=(80, 220, 255), width=3)   # acquired target
    F = lambda n: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', n)
    d.rectangle([0, 0, W, 58], fill=(10, 18, 30))
    d.text((24, 14), 'RADAR', font=F(30), fill=(230, 236, 240)); d.text((180, 18), 'H-UP  0.75 nm', font=F(24), fill=(150, 175, 190))
    d.text((W - 380, 18), 'TARGET 020°  0.5 nm  CPA 0.0', font=F(24), fill=(255, 210, 70))
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(230, 236, 240))
    front = Image.open(os.path.join(TEX, 'axiom-front.png')).convert('RGB')
    x0, y0, x1, y1 = 70, 72, 645, 432                     # the screen glass on the model's front texture
    front.paste(im.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0)); front.save(RADAR_PNG)
    print('wrote', RADAR_PNG)

if __name__ == '__main__' and '--prep' in sys.argv:
    prep_radar(); sys.exit(0)

sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Euler
import common as C, kit as K, kit_night as N

arg = C.cli(); FIG = arg('--fig', 14); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(HERE, '..', 'figure-style', 'articles', 'bareboat-skipper', 'colregs', f'{FIG}-3d.jpg'))
def deg(a): return math.radians(a)
C.reset()

def ferry(pos, heading, color=None):
    """The 55 m ferry from 3D Warehouse, its water disc dropped, floating; bow along the model's +X? (set by FLIP)."""
    root, objs = K.load_model('vessel-ferry.glb', drop_planes=False)
    for o in objs:
        if o.type == 'MESH' and any(sl.material and 'Water' in sl.material.name for sl in o.material_slots): o.hide_render = True
    bpy.context.view_layer.update()
    vis = [o for o in objs if o.type == 'MESH' and not o.hide_render]
    lo, hi = K.bbox(vis)
    cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
    for o in objs:   # re-centre on the hull, waterline at model z K.FERRY_WL
        if o.parent == root: o.location = Vector(o.location) - Vector((cx, cy, K.FERRY_WL))
    root.location = Vector((pos[0], pos[1], 0.0)); root.rotation_euler = Euler((0, 0, deg(90 - heading) + FERRY_TURN), 'XYZ')
    return root, vis

FERRY_TURN = 0.0   # radians to add if the model's bow points along -X (checked on a draft)

def dashes(p0, p1, dash=6.0, gap=4.0, w=0.9, mat=None):
    """A dashed line painted on the water (thin floating strips)."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length; u = d / L; n = 0
    while n * (dash + gap) < L:
        a = p0 + u * (n * (dash + gap)); b = p0 + u * min(L, n * (dash + gap) + dash); c = (a + b) / 2
        o = C.obj('dash', C.rbox('dash', ((b - a).length, w, 0.08), 0.0, 1), mat, (c.x, c.y, 0.22))
        o.rotation_euler = (0, 0, math.atan2(u.y, u.x)); n += 1

def band(name, x0, x1, y0, y1, rgba, z=0.18):
    """A translucent tint on the water marking a zone."""
    me = bpy.data.meshes.new(name); me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    m, nt, b, out = C.new_mat(name)
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = rgba[3]
    b.inputs['Base Color'].default_value = rgba[:3] + (1,); b.inputs['Roughness'].default_value = 0.6
    nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    o = C.obj(name, me, m); o.visible_shadow = False
    return o

def special_buoy(p, h=2.6, k=2.2):
    """A yellow special mark (a pillar with an X topmark), the kind that marks a separation zone's edge."""
    M = K.mats(); h *= k
    C.cyl('sp-body', 0.9 * k, 0.9 * k, 0.8 * k, 32, M['yellow'], (p[0], p[1], 0.25 * k))
    C.cyl('sp-pillar', 0.35 * k, 0.45 * k, h, 24, M['yellow'], (p[0], p[1], 0.6 * k + h / 2))
    for r in (45, -45):
        o = C.obj('sp-x', C.rbox('x', (0.9 * k, 0.12 * k, 0.12 * k), 0.02, 2), M['yellow'], (p[0], p[1], 0.9 * k + h)); o.rotation_euler = (0, deg(r), 0)

if FIG == 14:
    # north up: eastbound lane to the south (near), the separation zone, the westbound lane to the north (far)
    K.sea('breeze', size=40.0, repeat=18)
    K.day_sky(sun_az=200, sun_el=45)
    LANE_E, ZONE, LANE_W = (-150.0, -30.0), (-30.0, 30.0), (30.0, 150.0)
    band('zone', -900, 900, ZONE[0], ZONE[1], (0.9, 0.35, 0.2, 0.13))
    yel = C.simple('course', '#f2c200', 0.4, coat=0.3); white = C.simple('lane-line', '#e9eef0', 0.6)
    for yy in (ZONE[0], ZONE[1]):
        dashes((-900, yy, 0), (900, yy, 0), 14, 10, 0.7, white)
    for x in (-330, -110, 110, 330):
        special_buoy((x, ZONE[0] + 4)); special_buoy((x + 110, ZONE[1] - 4))
    e_root, e_vis = ferry((-150, -90), 90)            # eastbound, near lane
    w_root, w_vis = ferry((170, 90), 270)              # westbound, far lane
    you = K.load_yacht(name='you', sails={'main': True, 'genoa': 'starboard', 'boom': -25}).place(0, -180, heading=0, heel=4)
    K.wake(you, 55, 9)
    dashes((0, -160, 0), (0, 210, 0), 7, 5, 1.0, yel)
    K.camera((0, -480, 250), (0, -40, 0), 36)
    lab = [((-260, 100, 2), 'westbound lane'), ((260, 0, 2), 'separation zone', 'red'), ((270, -100, 2), 'eastbound lane'),
           (tuple(you.world((K.MAST.x, K.MAST.y, 21.0))), 'You', 'blue'), ((60, 150, 8), 'cross at right angles', 'blue')]
    arrows = [((-80, -90, 4), (10, -90, 4), 'blue'), ((100, 90, 4), (10, 90, 4), 'blue')]
    C.render(OUT, SAMPLES, SCALE, -0.6, lab, 'Traffic separation scheme', space='blender', arrows=arrows)

elif FIG == 15:
    me = K.load_yacht(name='own'); me.place(0, 0, heading=0)
    N.night_scene('calm')
    N.our_lights(me, steaming=True, power=0.4); N.cloth_furled(me)
    bow = me.world((10.5, 0.13, 2.0))
    L = N.ship(N.at_bearing(bow, 38, 95), heading=245, lights=('masthead', 'red'))
    # her signal lamp on the bridge wing: five quick flashes; we show one flash lit, the lamp bright and big
    lamp = L['masthead'] + Vector((0.0, 0.0, -2.6)) + (L['red'] - L['masthead']).normalized() * 0.0
    # Rule 34(b): the light signal is an all-round white light, flashed with the whistle; it stands at the masthead,
    # above her masthead (steaming) light. Show it lit, mid-flash.
    lamp = L['masthead'] + Vector((0, 0, 1.5))
    tr = [o for o in bpy.data.collections['vessel-trawler'].objects if o.type == 'MESH' and not o.hide_render]
    lo, hi = K.bbox(tr); Hh = hi.z - lo.z; foot = max(hi.x - lo.x, hi.y - lo.y)
    for o in tr:   # the slab the model stands on (kit_night.ship keeps it): wide, at the bottom, few faces
        l, h = K.bbox([o])
        if max(h.x - l.x, h.y - l.y) > 0.7 * foot and l.z < lo.z + 0.05 * Hh and ((h.z - l.z) < 0.12 * Hh or len(o.data.polygons) <= 40):
            o.hide_render = True
    N.light('signal-lamp', lamp, 'white', strength=40.0, power=400.0, radius=0.35)
    for n in bpy.data.objects['ship-red'].active_material.node_tree.nodes:   # a deeper red, so it does not read pink
        if n.type == 'EMISSION': n.inputs['Strength'].default_value = 1.6
    N.foredeck_camera(me, bearing=30, lens=32)
    C.render(OUT, SAMPLES, SCALE, 0.75, [(tuple(lamp + Vector((0, 0, 0.7))), '5 rapid flashes')],
             'Night · the same signals by light', space='blender', extra={'bloom': 1.0})

else:  # 16
    if not os.path.exists(RADAR_PNG):
        subprocess.run(['python3', os.path.abspath(__file__), '--prep'], check=True)
    M = K.mats()
    you = K.load_yacht(name='own'); you.place(0, 0, heading=0)
    K.sea('calm', size=30.0, repeat=10)
    K.day_sky(sun_az=180, sun_el=30, strength=0.18)
    # the fog: a volume over the sea round the boat, about 150 m visibility
    fm = bpy.data.meshes.new('fog'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(fm); bm.free()
    fog = C.obj('fog', fm, None, (0, 120, 15)); fog.scale = (700, 700, 32)
    m, nt, b, out = C.new_mat('fog'); nt.nodes.remove(b)
    vs = nt.nodes.new('ShaderNodeVolumePrincipled'); vs.inputs['Density'].default_value = 0.022; vs.inputs['Color'].default_value = (0.86, 0.88, 0.9, 1)
    nt.links.new(vs.outputs[0], out.inputs['Volume']); fog.data.materials.append(m)
    bpy.context.scene.cycles.volume_bounces = 1; bpy.context.scene.cycles.volume_step_rate = 4.0
    # the ship: 20 degrees on our starboard bow, 120 m, coming towards us
    s_root, s_vis = ferry(tuple(N.at_bearing(you.world((10.5, 0.13, 2.0)), 20, 115))[:2], 200)
    grey = C.simple('ship-fog', '#5d6166', 0.6)
    K.recolor(s_vis, lambda c, n: grey)          # in fog she shows no colour, only a grey shape
    # the plotter on the helm pod in front of the wheel, showing the radar
    pod_at = you.world((-1.25, -0.32, 4.6))
    root, objs = K.load_model('chartplotter-raymarine-axiom.glb', drop_planes=False)
    bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    k = 0.235 / (hi.x - lo.x); root.scale = (k,) * 3; bpy.context.view_layer.update(); lo, hi = K.bbox([o for o in objs if o.type == 'MESH'])
    root.location = (root.location.x - (lo.x + hi.x) / 2 + pod_at.x, root.location.y - (lo.y + hi.y) / 2 + pod_at.y, root.location.z - lo.z + pod_at.z)
    root.rotation_euler = (deg(-14), 0, 0)
    img = bpy.data.images.load(RADAR_PNG)
    for o in objs:
        for sl in getattr(o, 'material_slots', []):
            if sl.material and sl.material.name.startswith('raymarine--displays'):
                mm, mnt, mb, _ = C.new_mat('axiom-radar')
                uv = mnt.nodes.new('ShaderNodeUVMap'); tx = mnt.nodes.new('ShaderNodeTexImage'); tx.image = img
                mnt.links.new(uv.outputs['UV'], tx.inputs['Vector']); mb.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1)
                mnt.links.new(tx.outputs['Color'], mb.inputs['Emission Color']); mb.inputs['Emission Strength'].default_value = 4.0
                mb.inputs['Roughness'].default_value = 0.35; mb.inputs['Coat Weight'].default_value = 0.0
                sl.material = mm
    C.obj('pod', C.rbox('pod', (0.3, 0.14, 0.12), 0.035, 4), M['dark'], tuple(pod_at - Vector((0, 0, 0.07))))
    # camera at the wheel: the plotter in the lower right, the bow and the fog beyond
    bpy.context.view_layer.update(); plo, phi = K.bbox([o for o in objs if o.type == 'MESH'])
    eye = you.world((-2.05, -0.5, 5.05)); look = you.world((9.0, -0.3, 3.55))
    K.camera(tuple(eye), tuple(look), 24)
    bpy.context.view_layer.update(); slo, shi = K.bbox(s_vis)
    ship_top = Vector(((slo.x + shi.x) / 2, (slo.y + shi.y) / 2, shi.z - 2))
    C.render(OUT, SAMPLES, SCALE, -0.3, [(tuple(ship_top), 'Radar target'), (tuple(Vector(((plo.x + phi.x) / 2, (plo.y + phi.y) / 2, phi.z + 0.01))), 'target 020° · 0.5 nm', 'blue')],
             'Fog · turn boldly to starboard, or slow down', space='blender')
