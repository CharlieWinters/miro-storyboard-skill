from street import write
from glbs import rigged, glb
# S4 reaction close-up: reverse angle ahead of the pair, from the kerb edge looking back down the
# street. They walk toward us and stop; the car comes from behind camera and passes in the far lane
# at ~2 s; CHAR_A turns sharply to her left (toward the road) to follow it, CHAR_B flinches a beat
# later (anim_offset shifts his reaction). Sun from behind camera so faces and the street read.
write("S4",{"loc":[2.9,16.8,1.5],"look_at":[3.6,12.8,1.45],"lens":35},
           {"loc":[2.9,16.2,1.5],"look_at":[3.6,12.8,1.45],"lens":35},
 [rigged("CHAR_A","A_REACT",[4.3,12.0,0.14],rot_z=180),
  rigged("CHAR_B","B_REACT",[5.1,12.2,0.14],rot_z=180,anim_offset=0.8),
  glb("PROP_Vehicle",[-1.6,40,0],rot_z=0,loc_end=[-1.6,-40,0],motion="linear")],
 extra={"sun":{"elevation_deg":35,"azimuth_deg":-30,"strength":3.5,"softness_deg":2}})
