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

ANIM.update({
 "IDLE": "https://v3b.fal.media/files/b/0aac3e51/P9Oegl1befztDmZ8TL8h5_hy_motion_000.fbx",      # stands, breathing, weight shift
 "WAVE": "https://v3b.fal.media/files/b/0aac3e53/GX7t5zdZbXnqaaWhYyUpd_hy_motion_000.fbx",      # waves hello, right hand
 "LOOK_BACK": "https://v3b.fal.media/files/b/0aac3e54/tKPFS6XepWaOa-dOoDlJx_hy_motion_000.fbx", # looks back over right shoulder
})
# Meshy Rigging's own locomotion cycles, already on each character's skeleton.
CYCLES = {
 "CHAR_A": {"walk": "https://v3b.fal.media/files/b/0aac3ca3/kXPdOPfiLAS4zFbCfCJcu_walking_armature.glb",
            "run": "https://v3b.fal.media/files/b/0aac3ca3/0abmlzpGtjAWXFP2hzX9x_running_armature.glb"},
 "CHAR_B": {"walk": "https://v3b.fal.media/files/b/0aac3ca4/9NXtlna9u89ehVJAirei__walking_armature.glb",
            "run": "https://v3b.fal.media/files/b/0aac3ca4/3ojhxwXA8WhJTRa-JHURI_running_armature.glb"},
}
def puppet(name, loc, rot_z=0):
    """A rigged character set up for Action Pad instead of a baked clip."""
    return {"name": name, "type": "rigged", "path": RIG[name], "loc": loc, "rot_z": rot_z,
            "puppet": {"walk": CYCLES[name]["walk"], "run": CYCLES[name]["run"],
                       "idle": {"anim": ANIM["IDLE"], "in": 0, "out": 6},
                       "clips": {"react_left": {"anim": ANIM["A_REACT"], "in": 1.0, "out": 5.0},
                                 "flinch": {"anim": ANIM["B_REACT"], "in": 1.6, "out": 6.0},
                                 "wave": {"anim": ANIM["WAVE"], "in": 0, "out": 4},
                                 "look_back": {"anim": ANIM["LOOK_BACK"], "in": 0, "out": 4}},
                       "buttons": {"a": "react_left", "b": "flinch", "x": "wave", "y": "look_back"}}}
