# Article charter-checkin/plumbing, figures 1-6, as Blender renders (art_checkin_sys_kit.py for the shared parts).
#   1  the fresh-water panel: the tank gauge at 300 L (tank 1 full), the tank selector on 1, the pump switch
#   2  card: the heads: the toilet and its pump, the Y-valve set to TANK, the holding tank beside it
#   3  card: a seacock in the bilge: lever along the pipe (open), two stainless clips on the hose, a softwood bung tied on
#   4  card: the gas locker open: the bottle in use with its regulator and gauge, the hose, a full spare upright, the drain
#   5  card: the galley when you smell gas: the stove off, the hatch above open, the switch panel left alone
#   6  the bilge with a floorboard up: salt water in the sump, the bilge pump that has run three times an hour
#   blender --background --factory-startup --python docs/design/blender/art_checkin_plumbing.py -- --fig 1 [--samples 160]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import common as C, kit as K, kit_instruments as KI
import art_checkin_sys_kit as A

arg = C.cli(); FIG = arg('--fig', 1); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100)
OUT = arg('--out', os.path.join(A.outdir('plumbing'), f'{FIG}-3d.jpg'))
A.use_article('plumbing'); deg = math.radians

labels, arrows, note, expo, extra = [], [], None, -0.5, {}
C.reset(); A.frame_setup(); M = K.mats()
liner = A.frp_mat('liner', '#dcd9d0'); bronze = C.simple('bronze', '#a7773f', 0.35, 1.0)
redlev = C.simple('lever-red', '#b8191c', 0.4, coat=0.5); hoseblk = C.simple('hose-black', '#1a1b1d', 0.6)
ceramic = C.simple('ceramic', '#e9e8e2', 0.12, coat=0.6)

def seacock(at, lever_along=True, r=0.03):
    """A bronze ball-valve seacock standing on a through-hull at `at`; the lever along the pipe (up) = open."""
    at = Vector(at)
    C.cyl('thruhull', r * 1.25, r * 1.4, 0.025, 24, bronze, at + Vector((0, 0, 0.012)))
    C.cyl('seacock', r, r, 0.10, 24, bronze, at + Vector((0, 0, 0.07))); A.sphere('ball', r * 1.35, bronze, at + Vector((0, 0, 0.07)))
    C.cyl('tail', r * 0.8, r * 0.8, 0.07, 24, bronze, at + Vector((0, 0, 0.15)))
    lv = A.box('lever', (0.016, 0.02, 0.15), at + Vector((r * 1.6, 0, 0.13)), redlev, 0.005)
    if not lever_along: lv.rotation_euler = (0, deg(90), 0); lv.location = at + Vector((r * 1.6 + 0.07, 0, 0.07))
    return at

if FIG == 1:
    KI.wall('bulkhead', -0.6, 0.7, -0.4, 0.4, 0.004, KI.joinery_mat())
    pl = A.tex('plate', 'water'); A.panel_box(pl)
    gx, gz = A.px(700, 430); KI.gauge(A.sysface('litres', '300'), (gx, -0.001, gz), 0.045, value_angle=60)
    kx, kz = A.px(1500, 450)
    C.obj('sel-base', KI._cyl_y(0.022, 0.006), M['satin'], (kx, -0.003, kz))
    kn = C.obj('sel-knob', C.rbox('kn', (0.012, 0.016, 0.034), 0.004, 2), M['dark'], (kx, -0.012, kz)); kn.rotation_euler = (0, deg(-128), 0)
    tip = C.obj('sel-tip', C.rbox('tip', (0.003, 0.004, 0.012), 0.001, 1), C.simple('tip-white', '#f2f2ee', 0.4), (0, -0.009, 0.01)); tip.parent = kn
    sx, sz = A.px(1500, 720)
    C.obj('pump-sw', C.rbox('psw', (0.016, 0.012, 0.024), 0.003, 2), C.simple('rocker', '#1a1b1d', 0.4), (sx, -0.007, sz)).rotation_euler = (deg(12), 0, 0)
    A.lamp(sx + 0.03, sz, 'green', True, glow=0.01)
    A.interior_light(7, 2.5, (0.0, 0.0, 0.0))
    K.camera((0.03, -0.55, 0.14), (0.0, 0, 0.03), 40)
    labels = [(Vector((gx, 0, gz + 0.052)), 'Tank 1: 300 L, full'), (Vector((kx, 0, kz + 0.03)), 'selector on 1: read tank 2 too', 'blue')]
    note = 'Two tanks, 600 L · 600 ÷ 8 crew ÷ 7 days = under 11 L each a day'
    extra = {'lines': ['Not enough: fill at every marina']}

elif FIG == 2:
    # the heads compartment: a white liner, a teak grating sole, the toilet against the hull side at the back
    KI.wall('back', -1.0, 1.2, 0.0, 1.6, 0.42, liner); KI.wall('side', -1.0, 1.0, 0.0, 1.6, 0.0, liner).rotation_euler = (0, 0, deg(90))
    bpy.data.objects['side'].location = (1.0, 0.0, 0.0)
    A.box('sole', (2.4, 1.6, 0.02), (0.1, -0.3, -0.01), M['teak'])
    A.box('plinth', (0.5, 0.42, 0.10), (0.0, 0.2, 0.05), liner, 0.02)
    prof = [(0.0, 0.10), (0.11, 0.10), (0.13, 0.16), (0.15, 0.26), (0.19, 0.36), (0.20, 0.38), (0.17, 0.385), (0.13, 0.30), (0.05, 0.22), (0.0, 0.21)]
    bowl = C.lathe('bowl', prof, 48, ceramic); bowl.location = (0.0, 0.16, 0.0); bowl.scale = (1.0, 1.15, 1.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.165, minor_radius=0.018, location=(0.0, 0.16, 0.395)); seat = bpy.context.active_object
    seat.scale = (1.0, 1.15, 0.6); seat.data.materials.append(C.simple('seat', '#f2f1ec', 0.3, coat=0.4)); [setattr(p, 'use_smooth', True) for p in seat.data.polygons]
    lid = A.box('lid', (0.36, 0.02, 0.40), (0.0, 0.38, 0.60), C.simple('seat', '#f2f1ec', 0.3, coat=0.4), 0.03); lid.rotation_euler = (deg(-8), 0, 0)
    # the hand pump on the right of the bowl: base, barrel, handle; the wet/dry lever at its foot
    pg = C.simple('pump-grey', '#c9c9c4', 0.35)
    C.cyl('pump-base', 0.05, 0.055, 0.06, 24, pg, (0.25, 0.22, 0.13)); C.cyl('pump-barrel', 0.035, 0.035, 0.30, 24, pg, (0.25, 0.22, 0.31))
    C.cyl('pump-rod', 0.008, 0.008, 0.08, 12, M['satin'], (0.25, 0.22, 0.50)); A.box('pump-handle', (0.03, 0.12, 0.025), (0.25, 0.18, 0.55), M['dark'], 0.008)
    A.hose('bowl-pump', [(0.14, 0.22, 0.30), (0.2, 0.25, 0.22), (0.25, 0.24, 0.16)], 0.016, C.simple('hose-white', '#e6e4dc', 0.5))
    # the Y-valve on the hull side behind, its handle to TANK; a hose up to the holding tank, one down to the seacock
    yv = Vector((0.52, 0.36, 0.55))
    A.box('yv-body', (0.08, 0.06, 0.12), yv, C.simple('yv-white', '#ecebe5', 0.35), 0.015)
    hd = A.box('yv-handle', (0.10, 0.02, 0.025), yv + Vector((-0.04, -0.045, 0.02)), C.simple('yv-handle', '#1d5fa8', 0.4), 0.008); hd.rotation_euler = (0, deg(-35), 0)
    A.quad('yv-tank', 0.06, 0.02, A.tex('sticker', 'TANK'), yv + Vector((-0.08, -0.031, 0.10)), 0.0, 0.6)
    A.quad('yv-sea', 0.06, 0.02, A.tex('sticker', 'SEA'), yv + Vector((0.06, -0.031, 0.10)), 0.0, 0.6)
    A.hose('pump-yv', [(0.25, 0.24, 0.12), (0.35, 0.36, 0.2), (0.46, 0.38, 0.35), (0.52, 0.36, 0.48)], 0.018, C.simple('hose-white', '#e6e4dc', 0.5))
    tank = C.simple('tank-grey', '#b9bab4', 0.5)
    A.box('holding-tank', (0.34, 0.34, 0.42), (0.80, 0.22, 0.75), tank, 0.04); A.box('shelf', (0.40, 0.40, 0.03), (0.80, 0.22, 0.525), liner, 0.01)
    A.hose('yv-tank', [(0.52, 0.36, 0.62), (0.56, 0.36, 0.74), (0.63, 0.30, 0.80)], 0.018, C.simple('hose-white', '#e6e4dc', 0.5))
    A.hose('yv-sea', [(0.55, 0.36, 0.49), (0.6, 0.38, 0.3), (0.62, 0.38, 0.08), (0.62, 0.38, -0.05)], 0.018, C.simple('hose-white', '#e6e4dc', 0.5))
    A.hose('tank-vent', [(0.80, 0.22, 0.96), (0.80, 0.3, 1.1), (0.95, 0.4, 1.25)], 0.008, C.simple('hose-white', '#e6e4dc', 0.5))
    A.hose('tank-deck', [(0.72, 0.22, 0.96), (0.7, 0.3, 1.2), (0.7, 0.38, 1.6)], 0.02, C.simple('hose-white', '#e6e4dc', 0.5))
    K.day_sky(sun_az=150, sun_el=40, strength=0.06)
    KI.area_light((0.2, -0.9, 1.4), (0.3, 0.2, 0.5), 30, 0.6); KI.area_light((-0.8, -0.5, 1.2), (0.3, 0.2, 0.5), 8, 1.0, (0.85, 0.9, 1.0))
    K.camera((-0.2, -1.55, 1.25), (0.36, 0.25, 0.62), 34)
    labels = [(yv + Vector((-0.02, 0, 0.13)), 'valve to TANK: harbours and bays', 'blue'), (Vector((0.80, 0.22, 0.98)), 'holding tank')]
    note = 'Holding tank: empty at check-in · discharge only offshore, where allowed'
    extra = {'lines': ['Waste at the hull vent: the tank is full']}

elif FIG == 3:
    # in the bilge under a berth: the hull bottom, a seacock with its hose, two clips, the bung tied to it
    me = bpy.data.meshes.new('hull-in'); me.from_pydata([(-1.6, -1.2, -0.04), (1.6, -1.2, -0.04), (1.6, 0.6, 0.12), (-1.6, 0.6, 0.12)], [], [(0, 1, 2, 3)]); C.obj('hull-in', me, A.frp_mat('bilge', '#d3cfc2'))
    KI.wall('stringer-wall', -1.6, 1.6, 0.0, 1.0, 0.45, A.frp_mat('bilge2', '#cdc8bb'))
    at = seacock((0.0, 0.0, 0.06), True, 0.032)
    hose_pts = [at + Vector((0, 0, 0.18)), at + Vector((0, 0, 0.32)), at + Vector((0.02, 0.06, 0.48)), at + Vector((0.12, 0.25, 0.58))]
    A.hose('hose', hose_pts, 0.03, hoseblk)
    for dz in (0.215, 0.255): A.clip(at + Vector((0, 0, dz)), (0, 0, 1), 0.03, M['satin'])
    # the softwood bung, a cone, tied on with a lanyard round the valve body
    wood = C.simple('softwood', '#c9a26a', 0.7)
    bung = C.cyl('bung', 0.035, 0.008, 0.13, 24, wood, at + Vector((-0.12, -0.04, 0.05))); bung.rotation_euler = (deg(10), deg(-70), 0)
    A.hose('lanyard', [at + Vector((-0.035, 0, 0.09)), at + Vector((-0.07, -0.03, 0.07)), at + Vector((-0.12, -0.05, 0.06)), at + Vector((-0.17, -0.04, 0.04))], 0.0025, C.simple('twine', '#d8cfae', 0.8))
    K.day_sky(sun_az=150, sun_el=40, strength=0.05)
    KI.area_light((0.3, -0.8, 0.9), (0, 0, 0.15), 14, 0.5); KI.area_light((-0.6, -0.5, 0.6), (0, 0, 0.15), 4, 0.8, (0.85, 0.9, 1.0))
    K.camera((0.14, -0.9, 0.55), (0.0, 0.06, 0.22), 36)
    labels = [(at + Vector((0.03, 0, 0.26)), 'two stainless clips'),
              (at + Vector((-0.17, -0.05, 0.09)), 'softwood bung tied on')]
    note = 'Lever along the pipe: open · each one found and turned by hand'
    extra = {'lines': ['Leaving the boat, or heeled: heads seacocks closed']}

elif FIG == 4:
    # the gas locker in the cockpit seat, lid up: bottle in use with regulator and gauge, the spare beside it
    loc_w, loc_d, loc_h = 0.62, 0.42, 0.50
    for name, dims, loc in (('floor', (loc_w, loc_d, 0.02), (0, 0, 0.0)), ('back', (loc_w, 0.02, loc_h), (0, loc_d / 2, loc_h / 2)),
                            ('l', (0.02, loc_d, loc_h), (-loc_w / 2, 0, loc_h / 2)), ('r', (0.02, loc_d, loc_h), (loc_w / 2, 0, loc_h / 2)),
                            ('front', (loc_w, 0.02, loc_h), (0, -loc_d / 2, loc_h / 2))):
        A.box('locker-' + name, dims, loc, liner, 0.004)
    A.box('seat-top-f', (1.6, 0.4, 0.04), (0, -loc_d / 2 - 0.2, loc_h), M['teak']); A.box('seat-top-l', (0.5, 0.9, 0.04), (-0.56, 0, loc_h), M['teak']); A.box('seat-top-r', (0.5, 0.9, 0.04), (0.56, 0, loc_h), M['teak'])
    lid = A.box('lid', (loc_w + 0.04, 0.03, loc_d + 0.04), (0, loc_d / 2 + 0.03, loc_h + loc_d / 2 + 0.02), M['teak']); lid.rotation_euler = (deg(-8), 0, 0)
    A.box('coaming', (1.6, 0.06, 0.4), (0, loc_d / 2 + 0.25, loc_h + 0.2), C.gel_mat('coaming'), 0.02)
    # the drain: a hole in the floor at the front corner with a fitting
    C.cyl('drain-ring', 0.022, 0.022, 0.006, 24, M['satin'], (0.0, 0.18, 0.012)); C.cyl('drain-hole', 0.015, 0.015, 0.008, 24, C.simple('hole', '#050505', 0.9), (0.0, 0.18, 0.013))
    blue = C.simple('gas-blue', '#1f5fae', 0.35, coat=0.4)
    prof = [(0.0, 0.0), (0.11, 0.0), (0.12, 0.02), (0.12, 0.27), (0.10, 0.32), (0.05, 0.345), (0.03, 0.36), (0.0, 0.36)]
    used, spare = Vector((-0.155, -0.04, 0.01)), Vector((0.155, -0.04, 0.01))
    for p in (used, spare):
        b = C.lathe('bottle', prof, 48, blue); b.location = p
        C.cyl('valve', 0.02, 0.02, 0.04, 16, M['satin'], p + Vector((0, 0, 0.38)))
    C.cyl('spare-cap', 0.024, 0.024, 0.03, 16, C.simple('cap', '#141414', 0.5), spare + Vector((0, 0, 0.415)))
    reg = used + Vector((0.0, 0.0, 0.43))
    A.box('regulator', (0.07, 0.06, 0.05), reg, C.simple('reg', '#e8e6df', 0.35), 0.01)
    KI.gauge(A.tex('pgauge'), (reg.x, reg.y - 0.036, reg.z + 0.035), 0.022, value_angle=-15, bezel='dark')
    hose_or = C.simple('hose-orange', '#d8641c', 0.55)
    A.hose('gas-hose', [reg + Vector((-0.03, 0.01, 0)), reg + Vector((-0.07, 0.06, -0.02)), Vector((-0.27, 0.16, 0.36)), Vector((-0.29, 0.2, 0.42))], 0.008, hose_or)
    K.day_sky(sun_az=150, sun_el=45, strength=0.22)
    K.camera((0.03, -0.52, 1.3), (0.0, 0.08, 0.2), 38)
    labels = [(reg + Vector((0, -0.036, 0.06)), 'gauge holds'), (Vector((-0.24, 0.12, 0.36)), 'hose: date printed, no cracks'),
              (spare + Vector((0.08, -0.03, 0.31)), 'full spare, upright'), (Vector((0.0, 0.18, 0.02)), 'drain clear', 'blue')]
    note = 'Leak test: open the bottle, close it, the gauge holds for minutes'
    extra = {'lines': ['Gas alarm connected and tested']}; expo = -0.6

elif FIG == 5:
    # the galley: the stove in its gimbals, the hatch above it open, the switch panel on the bulkhead beside it
    wood = KI.joinery_mat(); steel = C.simple('stove-steel', '#c8ccd0', 0.3, 1.0)
    KI.wall('back', -2.5, 2.5, -0.2, 2.2, 0.35, liner)
    sw_ = KI.wall('side', -1.6, 0.36, -0.2, 2.2, 0.0, liner); sw_.rotation_euler = (0, 0, deg(90)); sw_.location = (0.98, 0.0, 0.0)
    A.box('counter-l', (0.6, 0.6, 0.9), (-0.65, 0.05, 0.45), wood, 0.01); A.box('counter-r', (0.6, 0.6, 0.9), (0.65, 0.05, 0.45), wood, 0.01)
    A.box('worktop-l', (0.62, 0.62, 0.03), (-0.65, 0.05, 0.915), C.simple('worktop', '#e6e2d8', 0.35)); A.box('worktop-r', (0.62, 0.62, 0.03), (0.65, 0.05, 0.915), C.simple('worktop', '#e6e2d8', 0.35))
    A.box('stove', (0.6, 0.45, 0.5), (0, 0.08, 0.65), steel, 0.02)
    A.box('oven-door', (0.5, 0.02, 0.3), (0, -0.15, 0.6), C.simple('oven-glass', '#151719', 0.08, coat=1.0), 0.01)
    A.box('hob', (0.56, 0.42, 0.01), (0, 0.08, 0.905), C.simple('hob', '#1b1c1e', 0.3, 0.5), 0.005)
    for x in (-0.13, 0.13):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.008, location=(x, 0.1, 0.915)); t = bpy.context.active_object; t.data.materials.append(M['dark'])
        C.cyl('burner', 0.035, 0.035, 0.012, 24, C.simple('burner', '#2e2f31', 0.4, 0.6), (x, 0.1, 0.915))
    knobs = []
    for i, x in enumerate((-0.18, -0.06, 0.06, 0.18)):
        knobs.append(C.obj('knob', KI._cyl_y(0.017, 0.02), M['dark'], (x, -0.145, 0.835)).location)
    for s in (-1, 1): C.cyl('gimbal', 0.015, 0.015, 0.04, 16, steel, (s * 0.31, 0.08, 0.80), (0, deg(90), 0))
    A.box('fiddle', (0.6, 0.015, 0.05), (0, -0.14, 0.94), steel, 0.004)
    # the ceiling with the hatch over the stove, its lid propped open; daylight coming in
    zc = 1.9; ceil = C.simple('headlining', '#ebe8e0', 0.7)
    hx = 0.35
    for name, dims, loc in (('c-f', (3.0, 0.8, 0.03), (0, -0.7, zc)), ('c-b', (3.0, 0.5, 0.03), (0, 0.55, zc)),
                            ('c-l', (1.4, 0.5, 0.03), (hx - 0.92, 0.05, zc)), ('c-r', (1.0, 0.5, 0.03), (hx + 0.72, 0.05, zc))):
        A.box(name, dims, loc, ceil)
    hl = A.box('hatch-lid', (0.44, 0.48, 0.02), (hx, 0.33, zc + 0.24), C.simple('hatch-acrylic', '#1c2228', 0.08, coat=1.0), 0.01); hl.rotation_euler = (deg(-60), 0, 0)
    A.box('hatch-frame', (0.46, 0.04, 0.05), (hx, -0.2, zc + 0.03), M['alu'], 0.005)
    K.day_sky(sun_az=170, sun_el=55, strength=0.25)
    KI.area_light((hx, 0.05, zc + 0.3), (0, 0.05, 0.9), 50, 0.4, (1.0, 0.98, 0.95))
    KI.area_light((-0.4, -1.2, 1.4), (0, 0.1, 0.9), 8, 1.0, (0.85, 0.9, 1.0))
    # the switch panel on the bulkhead to the right
    px0 = Vector((0.66, 0.345, 1.3))
    A.box('panel', (0.26, 0.012, 0.18), px0, M['dark'], 0.006)
    for i in range(6):
        C.obj('toggle', C.rbox('tg', (0.008, 0.016, 0.018), 0.002, 1), M['satin'], px0 + Vector((-0.1 + i * 0.04, -0.012, 0.02)))
        A.lamp(px0.x - 0.1 + i * 0.04, px0.z - 0.04, 'red', False, y=px0.y - 0.006, r=0.004)
    K.camera((-0.3, -1.75, 1.3), (0.12, 0.1, 1.4), 24)
    labels = [(Vector((hx + 0.18, -0.18, zc - 0.01)), 'hatch open', 'blue'), (Vector((0.0, -0.15, 0.97)), '2 no flames', 'red'),
              (px0 + Vector((0, 0, 0.1)), '2 no switches', 'red')]
    note = 'Smell of gas: 1 close the valve at the bottle'
    extra = {'lines': ['3 Ventilate · 4 then soapy water on the joints']}

elif FIG == 6:
    # the saloon sole with one board lifted; below it the sump, keel bolts, the bilge pump, salt water
    wood = KI.joinery_mat('sole-wood')
    A.box('sole-a', (2.0, 0.8, 0.03), (0, -0.75, 0.0), wood); A.box('sole-b', (2.0, 0.6, 0.03), (0, 0.65, 0.0), wood)
    A.box('sole-l', (0.7, 0.7, 0.03), (-0.65, -0.0, 0.0), wood); A.box('sole-r', (0.7, 0.7, 0.03), (0.65, -0.0, 0.0), wood)
    board = A.box('board', (0.6, 0.7, 0.03), (-0.2, 0.42, 0.25), wood); board.rotation_euler = (deg(70), 0, deg(10))
    frp = A.frp_mat('sump', '#cfcabd')
    prof_pts = [(-0.3, -0.35, -0.02), (0.3, -0.35, -0.02), (0.3, 0.35, -0.02), (-0.3, 0.35, -0.02)]
    for name, dims, loc in (('s-f', (0.6, 0.02, 0.42), (0, -0.35, -0.22)), ('s-b', (0.6, 0.02, 0.42), (0, 0.35, -0.22)),
                            ('s-l', (0.02, 0.7, 0.42), (-0.3, 0, -0.22)), ('s-r', (0.02, 0.7, 0.42), (0.3, 0, -0.22)), ('s-bot', (0.6, 0.7, 0.02), (0, 0, -0.42))):
        A.box(name, dims, loc, frp)
    for x, y in ((-0.1, -0.15), (0.1, -0.15), (-0.1, 0.12), (0.1, 0.12)):
        A.box('backing', (0.09, 0.09, 0.012), (x, y, -0.405), M['galv']); C.cyl('nut', 0.022, 0.022, 0.03, 6, M['galv'], (x, y, -0.385)); C.cyl('stud', 0.01, 0.01, 0.07, 12, M['galv'], (x, y, -0.36))
    water = C.water_mat(); wb = water.node_tree.nodes.get('Principled BSDF')
    KI.wall('water', -0.29, 0.29, -0.34, 0.34, 0, water).data.vertices.foreach_set('co', [-0.29, -0.34, -0.375, 0.29, -0.34, -0.375, 0.29, 0.34, -0.375, -0.29, 0.34, -0.375])
    pump = C.simple('pump-body', '#2a2d31', 0.4)
    C.cyl('pump', 0.04, 0.045, 0.12, 24, pump, (0.18, 0.2, -0.35)); C.cyl('pump-strainer', 0.05, 0.05, 0.02, 24, C.simple('strainer', '#e7e4da', 0.5), (0.18, 0.2, -0.41))
    fl = A.box('float', (0.05, 0.08, 0.03), (0.06, 0.24, -0.34), C.simple('float', '#e7e4da', 0.5), 0.008); fl.rotation_euler = (deg(-12), 0, 0)
    A.hose('pump-hose', [(0.18, 0.2, -0.29), (0.2, 0.25, -0.15), (0.22, 0.33, -0.03), (0.24, 0.5, -0.02)], 0.016, C.simple('hose-grey', '#8c9094', 0.55))
    A.hose('wire', [(0.06, 0.24, -0.32), (0.1, 0.32, -0.2), (0.15, 0.34, -0.05)], 0.004, C.simple('wire-brown', '#5a3a1e', 0.6))
    K.day_sky(sun_az=150, sun_el=40, strength=0.06)
    KI.area_light((0.2, -0.8, 1.2), (0, 0, -0.3), 30, 0.5); KI.area_light((-0.6, -0.4, 1.0), (0, 0, -0.3), 8, 1.0, (0.85, 0.9, 1.0))
    K.camera((0.05, -0.95, 0.95), (0.0, 0.03, -0.28), 38)
    labels = [(Vector((-0.12, -0.22, -0.375)), 'salt water, and it keeps coming', 'red'), (Vector((0.18, 0.2, -0.27)), 'bilge pump: 3 times an hour', 'red')]
    note = 'Pressure pump off: no change · find it now, and call the base'
    extra = {'lines': ['Salt: seacocks, hoses, stern gland, rudder seal']}

C.render(OUT, SAMPLES, SCALE, expo, labels, note, space='blender', arrows=arrows, extra=extra)
