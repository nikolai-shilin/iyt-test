# Drone views of the collision-rule situations, and the low view of a yacht at anchor:
#   --kind tacks     port tack meets starboard tack, converging close-hauled
#   --kind overtake  you come up from astern of the other yacht
#   --kind headon    two yachts motoring head-on
#   --kind channel   motoring up a buoyed channel between red and green marks
#   --kind anchored  low view of a yacht at anchor showing a black ball
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import common as C, kit as K

arg = C.cli(); OUT = arg('--out', 'fig-drone.jpg'); SAMPLES = arg('--samples', 160); SCALE = arg('--scale', 100); KIND = arg('--kind', 'tacks')
C.reset()
if KIND != 'anchored': K.sea('breeze', size=40.0, repeat=10)
K.day_sky(sun_az=200, sun_el=48)
labels, arrows, note = [], [], None
def label_on(y, text, color='blue', h=19.0): labels.append((tuple(y.world((K.MAST.x, K.MAST.y, h + K.WL))), text, color))
if KIND == 'tacks':
    # wind from north (0°). You: port tack heading 315 (wind over port, boom to starboard). Other: starboard tack, 045.
    you = K.load_yacht(name='you', sails={'main': True, 'genoa': 'starboard', 'boom': -12}).place(14, -10, heading=315, heel=12)
    oth = K.load_yacht(name='other', sails={'main': True, 'genoa': 'port', 'boom': 12}).place(-30, -6, heading=45, heel=-12)
    for y in (you, oth): K.wake(y, 45, 9)
    K.camera((-6, -95, 70), (-6, -2, 0), 32)
    label_on(you, 'You'); label_on(oth, 'Other')
    arrows = [((-6, 30, 12), (-6, 12, 12), 'blue')]; labels.append(((-6, 30, 12), 'Wind', 'blue'))
    note = 'Port tack meets starboard tack'
elif KIND == 'overtake':
    oth = K.load_yacht(name='other', sails={'main': True, 'genoa': 'port', 'boom': 35}).place(0, 30, heading=0, heel=-6)
    you = K.load_yacht(name='you', sails={'main': True, 'genoa': 'port', 'boom': 35}).place(9, -18, heading=0, heel=-6)
    for y in (you, oth): K.wake(y, 50, 9)
    K.camera((40, -80, 62), (4, 8, 0), 34)
    label_on(you, 'You'); label_on(oth, 'Other')
    arrows = [((50, 10, 12), (32, 4, 12), 'blue')]; labels.append(((50, 10, 12), 'Wind', 'blue'))
    note = 'You are overtaking'
elif KIND == 'headon':
    you = K.load_yacht(name='you').place(0, -26, heading=0)
    oth = K.load_yacht(name='other').place(2, 30, heading=180)
    for y in (you, oth): K.wake(y, 55, 10, 1.3)
    K.camera((-55, -70, 55), (0, 0, 0), 32)
    label_on(you, 'You'); label_on(oth, 'Other')
    note = 'Head-on, both under power'
elif KIND == 'channel':
    you = K.load_yacht(name='you').place(0, -30, heading=0); K.wake(you, 60, 10, 1.3)
    for i in range(4):
        K.lateral_buoy('port', topmark=True, light=False, at=(-22, -5 + i * 55))
        K.lateral_buoy('starboard', topmark=True, light=False, at=(22, -5 + i * 55))
    K.coast(distance=900, bearing=0, height=90)
    K.camera((-30, -100, 48), (0, 30, 0), 30)
    label_on(you, 'You'); note = 'Buoyed channel, entering from seaward'
else:  # anchored
    K.sea('calm', size=30.0, repeat=24, center=(-30, -22))   # waves centred on the low camera, out past the yacht
    y = K.load_yacht(name='anchored').place(0, 0, heading=20)
    bow = y.world((10.6, 0.13, 3.9)); K.ball(y.world((8.6, 0.13, 9.0)), 0.3)
    # the anchor chain leaving the bow roller into the water
    import bmesh
    p0, p1 = bow, bow + Vector((math.sin(math.radians(20)) * 4, math.cos(math.radians(20)) * 4, -bow.z - 0.2))
    C.tube('chain', [p0.lerp(p1, t / 10) + Vector((0, 0, -0.4 * math.sin(math.pi * t / 10))) for t in range(11)], 0.012, 8, 1.0, C.simple('chain', '#6b6e70', 0.5, 0.8))
    K.coast(distance=700, bearing=40, height=120)
    K.camera((-30, -22, 1.6), (4, 6, 5.5), 40)
    labels = [(tuple(y.world((8.6, 0.13, 9.6))), 'black ball')]; note = 'At anchor: one ball, forward'
C.render(OUT, SAMPLES, SCALE, -0.7, labels, note, space='blender', arrows=arrows)
