# Night pieces for the lights figures, on top of kit.py: a dark sea and sky, our own yacht's navigation lights
# (bicolour on the pulpit, steaming light on the mast lighting the foredeck), a small ship with its lights, and a
# camera on our foredeck. Blender space, sea surface at z = 0, our yacht heading north (+Y).
import math
import bpy
from mathutils import Vector, Euler
import common as C, kit as K

def deg(a): return math.radians(a)

def night_scene(state='calm', moon=0.0025, star_gain=3.5):
    """Night sky with stars and a dim moon, and a near-black blue sea that still mirrors the lights."""
    K.night_sky(moon=moon, stars=True)
    for n in bpy.context.scene.world.node_tree.nodes:   # brighter stars than kit.night_sky's default
        if n.type == 'VALTORGB' and abs(n.color_ramp.elements[0].color[0] - 0.6) < 1e-3:
            n.color_ramp.elements[0].color = (0.6 * star_gain, 0.62 * star_gain, 0.7 * star_gain, 1)
    moon_lamp = bpy.data.objects.get('moon')
    if moon_lamp:   # the moon behind us (south-south-west, 35 degrees up): its glints on deck and sea stay out of view
        moon_lamp.data.angle = deg(2)
        moon_lamp.rotation_euler = Vector((0.25, 0.8, -0.57)).to_track_quat('-Z', 'Y').to_euler()
    K.sea(state, color='#050d14', foam=False)

def light(name, p, color, strength=6.0, power=1.5, radius=0.05):
    """kit.nav_light with a lens dim enough that the colour survives the tone mapping (very bright red or green
    lenses turn white under AgX)."""
    o = K.nav_light(name, p, color, power=power, radius=radius)
    for n in o.active_material.node_tree.nodes:
        if n.type == 'EMISSION': n.inputs['Strength'].default_value = strength
    return o

def our_lights(y, steaming=True, power=0.5):
    """Bicolour light on the stemhead (red to port, green to starboard), and the steaming light on the front of the
    mast, which lights the foredeck. Model-space positions of the Sun Odyssey (bow along +X, port +Y)."""
    light('own-red', y.world((10.52, 0.21, 4.18)), 'red', strength=2.5, power=0.8, radius=0.022)
    light('own-green', y.world((10.52, 0.05, 4.18)), 'green', strength=2.5, power=0.8, radius=0.022)
    if steaming:
        p = y.world((5.45, 0.13, 11.5))
        ld = bpy.data.lights.new('steaming', 'SPOT'); ld.energy = power; ld.color = (1.0, 0.86, 0.66)
        ld.spot_size = deg(100); ld.spot_blend = 0.7; ld.shadow_soft_size = 0.03
        lo = bpy.data.objects.new('steaming', ld); C.col.objects.link(lo); lo.location = p
        tgt = y.world((9.5, 0.13, 3.6)); lo.rotation_euler = (tgt - p).to_track_quat('-Z', 'Y').to_euler()

def foredeck_camera(y, bearing=0.0, lens=18.0, eye=(6.0, -0.55, 5.25), pitch=-4.0):
    """Camera standing on our deck just aft of the mast, looking `bearing` degrees relative (+ to starboard)."""
    e = y.world(eye)
    hdg = math.radians(bearing)   # yacht heads +Y, starboard is +X
    d = Vector((math.sin(hdg), math.cos(hdg), math.tan(deg(pitch))))
    cd = bpy.data.cameras.new('cam'); cd.lens = lens; cd.clip_end = 3000
    cam = bpy.data.objects.new('cam', cd); C.col.objects.link(cam); bpy.context.scene.camera = cam
    cam.location = e; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return cam

def at_bearing(origin, bearing, dist):
    """A sea-level point `dist` metres from `origin` on a relative bearing (our yacht heading north)."""
    a = math.radians(bearing)
    return Vector((origin.x + math.sin(a) * dist, origin.y + math.cos(a) * dist, 0.0))

def ship(pos, heading, lights=('masthead', 'red')):
    """The 26 m trawler model without its outriggers, as a generic small power-driven vessel, dark, carrying the
    named lights. heading: compass degrees. Returns {light name: world position}."""
    root, objs = K.load_model('vessel-trawler.glb')
    bpy.context.view_layer.update()
    for o in objs:   # the trawl booms span the whole beam at the top, and a flat waterline sheet: drop them
        if o.type != 'MESH': continue
        l, h = K.bbox([o])
        if o.name == 'Geom3D' or ((h.z - l.z) < 0.4 and max(h.x - l.x, h.y - l.y) > 8 and h.z < 1.0): o.hide_render = True
    dull = C.simple('ship-night', '#2a2e33', 0.6)
    K.recolor(objs, lambda c, n: dull)
    for o in objs:   # parts that came without any material would render default white
        if o.type == 'MESH' and not o.data.materials: o.data.materials.append(dull)
    # model: bow along +X, centreline y ~ 1.2, waterline z 0; pivot on the centreline amidships
    root.location = pos; root.rotation_euler = Euler((0, 0, deg(90 - heading)), 'XYZ')
    bpy.context.view_layer.update()
    W = lambda p: root.matrix_world @ Vector(p)
    spots = {'masthead': ((-1.43, 1.3, 8.45), 'white'), 'red': ((-1.0, 3.6, 5.0), 'red'), 'green': ((-1.0, -1.2, 5.0), 'green'),
             'stern': ((-21.8, 1.2, 3.0), 'white')}
    out = {}
    for name in lights:
        p, col = spots[name]; wp = W(p)
        light('ship-' + name, wp, col, strength=7.0 if col != 'white' else 9.0, power=40.0, radius=0.45)
        out[name] = wp
    return out

def yacht_lights(y, sidelights=True, stern=False, tricolour=False):
    """A sailing yacht's lights on another Sun Odyssey (model space): bicolour on the pulpit, sternlight on the
    pushpit, or one tricolour at the masthead instead. Each lens shows only its own colour in our direction, so
    the caller picks what a viewer would see."""
    out = {}
    if tricolour:
        out['tri-red'] = y.world((5.06, 0.30, 20.75)); out['tri-green'] = y.world((5.06, -0.04, 20.75))
        light('tri-red', out['tri-red'], 'red', strength=7.0, power=6.0, radius=0.09)
        light('tri-green', out['tri-green'], 'green', strength=7.0, power=6.0, radius=0.09)
    if sidelights:
        out['red'] = y.world((10.2, 0.58, 4.22)); out['green'] = y.world((10.2, -0.32, 4.22))   # on the pulpit legs
        light('their-red', out['red'], 'red', strength=8.0, power=10.0, radius=0.2)
        light('their-green', out['green'], 'green', strength=8.0, power=10.0, radius=0.2)
    if stern:
        out['stern'] = y.world((-3.75, 0.13, 4.3)); light('their-stern', out['stern'], 'white', strength=9.0, power=6.0, radius=0.09)
    return out

def cloth_furled(y):
    """The furled genoa on the forestay came in with the glossy hull colour; give it sailcloth so it stops shining."""
    cloth = C.simple('furled-cloth', '#a9a69d', 0.8)
    for o in y.objs:
        if o.type == 'MESH' and (o.name.startswith('Geom3D_genoa') or o.name.startswith('Geom3D_Forestay')):
            for sl in o.material_slots: sl.material = cloth
            if not o.material_slots: o.data.materials.append(cloth)
