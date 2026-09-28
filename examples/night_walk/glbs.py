GLB = {
 "CHAR_A": "https://v3b.fal.media/files/b/0aac3b69/uRjWP6Djf89TXFlYVqomX_model.glb",
 "CHAR_B": "https://v3b.fal.media/files/b/0aac3b6a/XDRK0b74hC3_nfEg697Oj_model.glb",
 "PROP_Vehicle": "https://v3b.fal.media/files/b/0aac3b6a/Zow75zvukI7bWkW4k2KwU_model.glb",
}
def glb(name, loc, rot_z=0, loc_end=None, **kw):
    s = {"name": name, "type": "glb", "path": GLB[name], "loc": loc, "rot_z": rot_z, "decimate": 0.25}
    if name == "CHAR_A": s["height"] = 1.68
    elif name == "CHAR_B": s["height"] = 1.86
    else: s["length"] = 4.1
    if loc_end: s["loc_end"] = loc_end
    s.update(kw); return s
