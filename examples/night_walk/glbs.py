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

# Meshy Rigging output (rigged from the GLBs above) and Hunyuan Motion clips.
RIG = {
 "CHAR_A": "https://v3b.fal.media/files/b/0aac3ca4/7kL5i-9_OJxbfyisFTPbu_rigged_character.glb",
 "CHAR_B": "https://v3b.fal.media/files/b/0aac3ca5/P3CMdxLJbfB4XECKTvuoO_rigged_character.glb",
}
ANIM = {
 "A_WALK": "https://v3b.fal.media/files/b/0aac3c9d/HNib2LTaHJ9hqUtq-oMC-_hy_motion_000.fbx",   # walks, talking, glances left
 "B_WALK": "https://v3b.fal.media/files/b/0aac3ca8/90wBRv-hUepXoays92iVV_hy_motion_000.fbx",   # walks, hands in pockets, glances right
 "A_REACT": "https://v3b.fal.media/files/b/0aac3ca9/dcGEvDPgdfUYenAnTPriN_hy_motion_000.fbx",  # stops, turns sharply left
 "B_REACT": "https://v3b.fal.media/files/b/0aac3cdf/2hyDoyCsEX_97GXA2r2m__hy_motion_000.fbx",  # stops, flinches, arm out, turns left
}
def rigged(name, anim, loc, rot_z=0, **kw):
    s = {"name": name, "type": "rigged", "path": RIG[name], "anim": ANIM[anim], "loc": loc, "rot_z": rot_z}
    s.update(kw); return s
