from street import write
from glbs import rigged
# S2 two-shot tracking: the pair walk toward camera on the right pavement (Hunyuan walks, ~0.95 m/s),
# the camera leads them from the road side, dollying back at their pace. Each walk veers a little
# (A 6 deg toward the kerb, B 7.6 deg toward the wall, measured from travel_m), so rot_z cancels it
# and they stay side by side. B walks 0.8 m less, so he starts 0.7 m ahead.
write("S2",{"loc":[2.6,25.2,1.6],"look_at":[4.6,30,1.35],"lens":35},
           {"loc":[2.6,19.5,1.6],"look_at":[4.6,24.5,1.35],"lens":35},
 [rigged("CHAR_A","A_WALK",[4.3,30,0.14],rot_z=5.9),
  rigged("CHAR_B","B_WALK",[5.1,29.6,0.14],rot_z=-7.6)])
