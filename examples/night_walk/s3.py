from street import write
from glbs import glb
# S3 the car passes, whip-pan: camera just behind the pair on the right kerb, looking up the street.
# The car comes toward us in the far lane at a constant ~42 km/h and passes the camera at mid-clip;
# the look-at target sweeps along the car's lane, so the eased camera holds, whips as the car
# passes, then settles on it driving away.
write("S3",{"loc":[3.1,8.0,1.55],"look_at":[1.0,45,1.3],"lens":28},
           {"loc":[3.1,8.0,1.55],"look_at":[-1.6,-30,1.0],"lens":28},
 [glb("CHAR_A",[4.0,11.5,0.14],rot_z=180,loc_end=[4.0,13.5,0.14]),
  glb("CHAR_B",[4.8,11.8,0.14],rot_z=180,loc_end=[4.8,13.8,0.14]),
  glb("PROP_Vehicle",[-1.6,43,0],rot_z=0,loc_end=[-1.6,-27,0],motion="linear")])
