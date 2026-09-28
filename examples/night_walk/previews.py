import json
from glbs import glb
for name, cam in [("CHAR_A",([2.2,-3.2,1.3],[0,0,0.85],50)),("CHAR_B",([2.2,-3.4,1.4],[0,0,0.93],50)),("PROP_Vehicle",([4.2,-5.4,2.0],[0,0,0.7],40))]:
    spec={"name":name+"_GLB","aspect":"1:1","width":720,"fps":24,"duration":1,"ground":True,"ground_size":30,
      "clay_color":"#b9b4ad","sky_color":"#d9dde3","camera":{"loc":cam[0],"look_at":cam[1],"lens":cam[2]},
      "sun":{"elevation_deg":40,"azimuth_deg":130,"strength":3.5,"softness_deg":2},
      "subjects":[glb(name,[0,0,0])]}
    json.dump(spec,open(spec["name"]+".json","w"),indent=1)
