from street import write
from glbs import glb
# S1 wide establishing push-in: camera low-centre, dollies 8 m down the street; the pair walk toward us far down the right pavement.
write("S1",{"loc":[0.6,-6,2.4],"look_at":[0.8,45,2.2],"lens":24},{"loc":[0.6,2,2.1],"look_at":[0.8,47,2.0],"lens":24},
 [glb("CHAR_A",[4.3,24,0.14],loc_end=[4.3,20.5,0.14]),
  glb("CHAR_B",[5.1,24.4,0.14],loc_end=[5.1,20.9,0.14])])
