# Article racing-rules/course: the figures as Blender renders, a high drone view of each race situation (see
# art_rr_a_scenes.py for what each figure shows and art_rr_a_kit.py for how it is built).
#   blender --background --factory-startup --python docs/design/blender/art_rr_course.py -- --fig 1 [--samples 144] [--scale 100]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_rr_a_kit as RK
RK.main('course')
