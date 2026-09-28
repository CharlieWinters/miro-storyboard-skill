from street import write
from glbs import puppet
# Action Pad stage: the Night Walk street with both characters as puppets, a side-on camera
# side-on from the far lane, 12 s. Record CHAR_A, then CHAR_B against her playback.
write("S_PUPPET",{"loc":[-1.2,13.5,1.9],"look_at":[4.8,15.2,1.0],"lens":24},None,
 [puppet("CHAR_A",[4.3,12,0.14],rot_z=180),
  puppet("CHAR_B",[5.1,11.6,0.14],rot_z=180)],
 extra={"duration":12})
