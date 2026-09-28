# Shared street block for all Night Walk shots: road runs along +y, centre x=0.
import json
def street():
    s = []
    s.append({"name":"ROAD","type":"cube","loc":[0,35,-0.05],"size":[7.0,170,0.1]})
    for side in (-1,1):
        t = "L" if side<0 else "R"
        s.append({"name":f"KERB_{t}","type":"cube","loc":[side*3.62,35,0.08],"size":[0.25,170,0.16]})
        s.append({"name":f"PAVE_{t}","type":"cube","loc":[side*4.9,35,0.07],"size":[2.4,170,0.14]})
        # building frontage: blocks of varying height and depth so the walls read as separate buildings
        y=-50; i=0
        heights=[12,14.5,11,13,15.5,12.5,10.5,14,13.5,11.5]
        lengths=[12,9,14,10,11,13,9,12,10,14]
        while y<120:
            h=heights[i%10]; L=lengths[(i+(side>0)*3)%10]; inset=0.35*((i+side)%2)
            s.append({"name":f"BLDG_{t}{i}","type":"cube","loc":[side*(7.6+inset),y+L/2,h/2],"size":[2.4,L-0.3,h]})
            # shopfront recess band + cornice ledge give the facade horizontal lines
            s.append({"name":f"CORN_{t}{i}","type":"cube","loc":[side*(6.3+inset),y+L/2,3.6],"size":[0.3,L-0.3,0.25]})
            y+=L; i+=1
        s.append({"name":f"POST_{t}","type":"cylinder","loc":[side*5.6,-28,2.25],"size":[0.16,0.16,4.5],"repeat":{"count":10,"offset":[0,15,0]}})
        s.append({"name":f"LAMP_{t}","type":"cube","loc":[side*5.3,-28,4.55],"size":[0.7,0.25,0.25],"repeat":{"count":10,"offset":[0,15,0]}})
    s.append({"name":"BACK_BLDG","type":"cube","loc":[0,-51,8],"size":[20,2,16]})
    s.append({"name":"END_BLDG","type":"cube","loc":[0,121,8],"size":[20,2,16]})
    return s
def write(name, camera, camera_end, subjects, extra=None):
    spec={"name":name,"aspect":"16:9","width":1280,"fps":24,"duration":6.0,"ground":True,"ground_size":400,
          "clay_color":"#b9b4ad","sky_color":"#d9dde3",
          "camera":camera,"sun":{"elevation_deg":35,"azimuth_deg":120,"strength":3.5,"softness_deg":2},
          "subjects":street()+subjects}
    if camera_end: spec["camera_end"]=camera_end
    if extra: spec.update(extra)
    json.dump(spec,open(name+".json","w"),indent=1)
