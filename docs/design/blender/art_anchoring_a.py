# Article bareboat-skipper/anchoring, figures 1, 7 and 8 as Blender renders (the 3D half of the before/after;
# the layouts follow the schematic specs in docs/design/article-figures.html):
#   --fig 1  shelter from the forecast wind: land to the south, a channel, anchoring spots A, B and C, wind S
#   --fig 7  Mediterranean mooring stern-to: a quay with yachts stern-to, ours reversing in, the drop point off
#   --fig 8  the same berth with the wind on the beam (E, F4): drop at B, upwind of the berth
# Blender space: x east, y north (the schematics' z is south, so y = -z), the sea at z = 0.
#   blender --background --factory-startup --python docs/design/blender/art_anchoring_a.py -- --fig 1 --out .../1-3d.jpg
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, noise as mnoise
import common as C, kit as K, kit_world as KW

arg = C.cli(); FIG = arg('--fig', 1); OUT = arg('--out', f'{FIG}-3d.jpg'); SAMPLES = arg('--samples', 192); SCALE = arg('--scale', 100)
C.reset()

def spot_ring(x, y, r=7.0, name='spot'):
    """A yellow ring on the water marking an anchoring spot or drop point."""
    bm = bmesh.new(); seg, ring = 72, 10; tube = r * 0.07; vs = []
    for i in range(seg):
        a = i / seg * math.tau
        row = []
        for j in range(ring):
            b = j / ring * math.tau
            row.append(bm.verts.new(((r + tube * math.cos(b)) * math.cos(a), (r + tube * math.cos(b)) * math.sin(a), tube * math.sin(b) * 0.5)))
        vs.append(row)
    for i in range(seg):
        for j in range(ring):
            bm.faces.new((vs[i][j], vs[(i + 1) % seg][j], vs[(i + 1) % seg][(j + 1) % ring], vs[i][(j + 1) % ring])).smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    m, nt, b, _ = C.new_mat('ring-yellow'); C.setin(b, 'Base Color', C.lin('#ffc400')); C.setin(b, 'Emission Color', C.lin('#ffc400'))
    C.setin(b, 'Emission Strength', 0.6); C.setin(b, 'Roughness', 0.5)
    return C.obj(name, me, m, (x, y, 0.35))

def dashes(p0, p1, dash=1.6, gap=1.0, r=0.12, color='#ffc400', z=0.32, name='dash'):
    """A dashed line floating on the water (chain lead, course)."""
    m = C.simple(name + '-mat', color, 0.5); m.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = C.lin(color)
    m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.5
    a, b = Vector((p0[0], p0[1], z)), Vector((p1[0], p1[1], z)); L = (b - a).length; d = (b - a).normalized(); s = 0.0
    while s < L:
        e = min(L, s + dash); C.tube(name, [a + d * s, a + d * e], r, 8, 1.0, m); s = e + gap

class YachtInstance:
    """A placed copy of a yacht loaded once (a collection instance): cheap, shares every mesh."""
    def __init__(self, src_coll, name):
        self.e = bpy.data.objects.new(name, None); self.e.instance_type = 'COLLECTION'; self.e.instance_collection = src_coll
        C.col.objects.link(self.e)
    def place(self, x, y, heading=0.0):
        self.e.location = (x, y, 0.0); self.e.rotation_euler = (0, 0, math.radians(90 - heading)); return self
    def world(self, p):
        bpy.context.view_layer.update()
        return self.e.matrix_world @ (Vector(p) - Vector((K.MAST.x, K.MAST.y, K.WL)))

def yacht_source(hull='white', name='src'):
    """Load the Sun Odyssey at the origin (heading 0) into its own collection, kept out of the render itself."""
    y = K.load_yacht(name=name, hull=hull)
    coll = bpy.data.collections.new(name + '-coll')
    bpy.context.scene.collection.children.link(coll)
    objs = [y.root] + list(y.root.children_recursive)
    for o in objs:
        for c in list(o.users_collection): c.objects.unlink(o)
        coll.objects.link(o)
    y.root.rotation_euler = (0, 0, 0)                      # bow along +X; the instance's own rotation sets the heading
    for lc in bpy.context.view_layer.layer_collection.children:
        if lc.collection == coll: lc.exclude = True
    return coll

# ======================================================================================================
if FIG == 1:
    # land to the south-west and south-east of a channel (schematic: x = (sx-160)*3, y = -(sy-100)*3, metres)
    def shore1(x):   # north edge of the western land, x <= 90
        pts = [(-480, -90), (-330, -78), (-180, -69), (-30, -72), (90, -105)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x <= x1: t = (x - x0) / (x1 - x0); return y0 + (y1 - y0) * max(0, min(1, t))
        return pts[-1][1]
    def shore2(x):   # north edge of the eastern land, x >= 270
        pts = [(270, -150), (420, -63), (480, -30), (700, 20)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x <= x1: t = (x - x0) / (x1 - x0); return y0 + (y1 - y0) * max(0, min(1, t))
        return pts[-1][1]
    def wig(x, y):
        return 22 * mnoise.noise(Vector((x * 0.012, y * 0.012, 1.0))) + 7 * mnoise.noise(Vector((x * 0.05, y * 0.05, 2.0)))
    def inland(x, y):
        """Metres inland (negative at sea): the nearer of the two coasts and the channel's banks."""
        d1 = min(shore1(min(x, 90)) - y, (90 - x) * 1.0 + 0.4 * (shore1(90) - y) * 0.0) if x < 200 else -999
        d2 = min(shore2(max(x, 270)) - y, x - 270) if x > 160 else -999
        return max(d1, d2) + wig(x, y)
    def h(x, y):
        d = inland(x, y)
        if d < 0: return max(-14.0, d * 0.12) - 0.3
        beach = min(1.0, d / 14.0)
        hills = 1.4 + 95 * (1 - math.exp(-max(0.0, d - 14) / 140.0)) + 120 * (1 - math.exp(-max(0.0, d - 500) / 600.0))
        rough = (24 * mnoise.noise(Vector((x * 0.006, y * 0.006, 4.0))) + 6 * mnoise.noise(Vector((x * 0.025, y * 0.025, 4.0)))) * min(1.0, max(0.0, (d - 20) / 100.0))
        return (1.4 * beach if d < 14 else hills + rough) - 0.3
    step = 5.0; x0, x1, y0, y1 = -900, 900, -1700, 40
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step)
    verts = [(x0 + i * step, y0 + j * step, h(x0 + i * step, y0 + j * step)) for j in range(ny + 1) for i in range(nx + 1)]
    faces = [(j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i) for j in range(ny) for i in range(nx)]
    me = bpy.data.meshes.new('land'); me.from_pydata(verts, [], faces); me.update(); me.shade_smooth()
    C.obj('land', me, KW.land_mat())
    # olive and pine clumps, a small whitewashed hamlet above the western shore
    random.seed(31)
    fol = C.simple('foliage', '#3c4a26', 0.9)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts: v.co *= 1.0 + 0.2 * mnoise.noise(v.co * 2.0); v.co.z *= 0.8
    tme = bpy.data.meshes.new('tree'); bm.to_mesh(tme); bm.free(); tme.materials.append(fol); tme.shade_smooth()
    k = 0
    while k < 1400:
        x, y = random.uniform(-880, 880), random.uniform(-1600, 20)
        d = inland(x, y)
        if d < 30 or mnoise.noise(Vector((x * 0.012, y * 0.012, 3.0))) < -0.05: continue
        o = bpy.data.objects.new('tree', tme); C.col.objects.link(o)
        s = random.uniform(2.5, 5.0); o.scale = (s, s, s * random.uniform(0.8, 1.3)); o.location = (x, y, h(x, y) + s * 0.5); k += 1
    wm, rm = KW.plaster_mat(), KW.roof_mat()
    protos = [KW.house_mesh(random.uniform(7, 12), random.uniform(6, 9), random.uniform(4, 8), random.uniform(2.0, 3.0), wm, rm, f'house{k}') for k in range(8)]
    placed = []
    while len(placed) < 60:
        x = random.gauss(-260, 70); y = shore1(x) - 28 - abs(random.gauss(0, 50))
        if inland(x, y) < 20 or any((x - a) ** 2 + (y - b) ** 2 < 120 for a, b in placed): continue
        placed.append((x, y)); o = bpy.data.objects.new('house', random.choice(protos)); C.col.objects.link(o)
        o.location = (x, y, h(x, y) - 0.4); o.rotation_euler = (0, 0, math.radians(random.choice((0, 90)) + random.uniform(-8, 8)))
    K.sea('breeze', size=40.0, res=9, repeat=26, center=(-60, -100))
    K.day_sky(sun_az=210, sun_el=38, strength=0.25, haze=2.2)
    A, B, Cc = (-210, 15), (180, 120), (180, -150)
    for (x, y), n in ((A, 'A'), (B, 'B'), (Cc, 'C')): spot_ring(x, y, 16.0, 'spot' + n)
    # a yacht already at anchor in the lee at A, lying to the present north-westerly
    K.load_yacht(name='anchored').place(A[0] + 40, A[1] + 10, heading=320)
    KW.camera((30, -620, 600), (20, -10, 0), lens=30)
    labels = [((A[0], A[1], 14), 'A', 'blue'), ((B[0], B[1], 14), 'B', 'blue'), ((Cc[0], Cc[1], 14), 'C', 'blue'),
              ((-230, -300, 90), 'LAND (south)'), ((180, -330, 10), 'channel'), ((20, -70, 30), 'Wind S, F5 overnight', 'red')]
    arrows = [((20, -40, 30), (20, 190, 30), 'red')]
    note = 'Forecast: wind backing south overnight, F5'
    expo = -0.7

# ======================================================================================================
else:
    # the harbour: a quay along the north (y 0..30), the town behind it, yachts stern-to along it
    concrete = C.concrete_mat('quay-concrete')
    q = C.obj('quay', C.rbox('quay', (160, 30, 3.0), 0.15, 2), concrete, (0, 15, -0.3))
    C.obj('quay-edge', C.rbox('quay-edge', (160, 0.5, 0.25), 0.05, 2), C.simple('quay-cap', '#cfcac0', 0.8), (0, 0.25, 1.32))
    wm, rm = KW.plaster_mat(), KW.roof_mat()
    random.seed(7)
    x = -80
    while x < 80:                     # a terrace of waterfront houses behind the quay
        w = random.uniform(7, 11); hgt = random.uniform(7, 13)
        o = bpy.data.objects.new('house', KW.house_mesh(w, 10, hgt, 2.4, wm, rm, f'h{x:.0f}')); C.col.objects.link(o)
        o.location = (x + w / 2, 36, 1.2); x += w + random.uniform(0.0, 1.2)
    bol = C.simple('bollard', '#2a2b2d', 0.5, 0.3)
    line_m = C.simple('mooring-line', '#e7e2d4', 0.7)
    SRC = {'white': yacht_source('white', 'src-white'), 'navy': yacht_source('navy', 'src-navy')}
    def stern_to(xc, name, stern_gap=1.6, lines=True):
        """A Sun Odyssey stern-to the quay at x = xc: stern lines to two bollards, the bow held off by a lazy line."""
        y = YachtInstance(SRC['navy' if int(xc) in (-20, 15) else 'white'], name)
        mast_y = -stern_gap - 8.7            # stern is 8.7 m aft of the mast
        y.place(xc, mast_y, heading=180)
        if lines:
            for side in (-1, 1):
                bp = Vector((xc + side * 1.4, 0.7, 1.2)); C.cyl('bollard', 0.12, 0.12, 0.35, 16, bol, bp + Vector((0, 0, 0.17)))
                s = y.world((-3.5, 0.13 + side * 1.7 * (-1), 3.6))  # stern quarters (model +Y is port, mirrored by heading)
                pts = [s.lerp(bp + Vector((0, 0, 0.3)), t / 8) + Vector((0, 0, -0.25 * math.sin(math.pi * t / 8))) for t in range(9)]
                C.tube('stern-line', pts, 0.009, 8, 1.0, line_m)
            bow = y.world((10.6, 0.13, 3.9))     # lazy line from the bow down into the water
            C.tube('lazy-line', [bow, bow + Vector((0, -2.0, -2.2)), bow + Vector((0, -4.5, -4.5))], 0.008, 8, 1.0, line_m)
        return y
    for xc in (-30, -25, -20, -15, -10, -5, 5, 10, 15, 20, 25, 30):
        stern_to(xc, f'moored{xc}')
    K.sea('calm', size=30.0, res=10, repeat=12, center=(0, -60))
    K.day_sky(sun_az=215, sun_el=42, strength=0.25, haze=2.0)
    if FIG == 7:
        you = YachtInstance(SRC['white'], 'you')
        you.place(0, -27.0, heading=180)            # stern 18 m off the quay, backing in
        bow = you.world((10.6, 0.13, 3.9)); bow.z = 0
        spot_ring(0, -50, 3.2, 'drop')
        dashes((-0.6, -48.5), (bow.x - 0.6, bow.y - 0.4), 1.0, 0.7, 0.09, '#2a2b2d', 0.12, 'chain-lead')
        KW.camera((26, -82, 38), (0, -18, 0), lens=34)
        labels = [((-24, 6, 3), 'QUAY'), ((0, -27, 7.5), 'reversing in', 'blue'), ((16, -28, 2.5), '3–4 boat lengths'),
                  ((0, -50, 2.0), 'drop here')]
        arrows = [((5.5, -36, 0.4), (5.5, -18, 0.4), 'yellow')]
        note = 'Stern-to, reversing towards the quay'
    else:
        Bx, By = 16, -42
        spot_ring(Bx, By, 3.2, 'B')
        KW.camera((-24, -82, 38), (4, -18, 0), lens=34)
        labels = [((-24, 6, 3), 'QUAY'), ((0, -3, 2.0), 'your berth', 'blue'), ((Bx, By, 2.0), 'B · drop upwind', 'blue'),
                  ((48, -26, 4), 'Wind E, F4', 'red')]
        arrows = [((48, -30, 4), (30, -30, 4), 'red'), ((Bx - 2.5, By + 6, 0.4), (3, -12, 0.4), 'yellow')]
        note = 'Wind on the beam of the berth, F4'
    expo = -0.6

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows)
