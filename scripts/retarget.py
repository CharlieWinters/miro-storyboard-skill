"""Retarget a Hunyuan Motion clip onto a Meshy-rigged character, inside Blender.

A port of the Fal-for-Miro app's three.js retargeter
(fal-miro/frontend/src/embed/retarget.ts), so a greybox and the app's
motion embed move a character the same way.

Hunyuan Motion returns an FBX on its own SMPL-H skeleton (Pelvis, L_Hip,
Spine1..3, L_Collar, ...). Meshy Rigging returns a Mixamo-style skeleton (Hips,
LeftUpLeg, Spine02 -> Spine01 -> Spine, ...). Copying rotations across by bone
name leaves a crumpled figure: the two rigs' rest poses (T vs A) and bone axes
differ. So, per frame and for every mapped target bone:

  1. delta = sourceWorld(now) * inverse(sourceWorld(rest)): how far the
     mannequin's bone has turned from its own rest, in world space;
  2. world = delta * alignedRest: that turn applied to the character's rest,
     after first turning each character bone so its rest *direction* (towards
     its mapped child) matches the mannequin's. That alignment is what lets a
     T-pose mannequin drive an A-pose character without the arms ending up
     wrong;
  3. the world rotation is converted to a pose-bone basis and keyframed.

The hips also take the mannequin's pelvis travel, scaled by the two figures'
heights, so a walk actually walks. Unmapped bones (head_end, headfront) follow
their parent at their rest rotation.
"""

import re

import bpy
from mathutils import Quaternion, Vector

CANON_TO_SMPL = {
    "hips": "Pelvis",
    "leftupleg": "L_Hip", "leftleg": "L_Knee", "leftfoot": "L_Ankle", "lefttoebase": "L_Foot",
    "rightupleg": "R_Hip", "rightleg": "R_Knee", "rightfoot": "R_Ankle", "righttoebase": "R_Foot",
    "neck": "Neck", "head": "Head",
    "leftshoulder": "L_Collar", "leftarm": "L_Shoulder", "leftforearm": "L_Elbow", "lefthand": "L_Wrist",
    "rightshoulder": "R_Collar", "rightarm": "R_Shoulder", "rightforearm": "R_Elbow", "righthand": "R_Wrist",
}
# Spines are matched by depth below the hips: Meshy numbers them top-down
# (Spine02 -> Spine01 -> Spine), Mixamo bottom-up.
SMPL_SPINE = ["Spine1", "Spine2", "Spine3"]
# The clavicle is a stub on one rig and reaches the sternum on the other;
# aligning it only rolls the shoulder. It still takes the source's delta.
NO_ALIGN = {"L_Collar", "R_Collar"}


def canonical(name):
    return re.sub(r"[\s_:.]", "", re.sub(r"^mixamorig:?", "", name, flags=re.I)).lower()


def depth(bone):
    d, p = 0, bone.parent
    while p:
        d, p = d + 1, p.parent
    return d


def build_map(bones):
    m, spines = {}, []
    for b in bones:
        c = canonical(b.name)
        if c in CANON_TO_SMPL:
            m[b.name] = CANON_TO_SMPL[c]
        elif c.startswith("spine"):
            spines.append(b)
    spines.sort(key=depth)
    for bone, smpl in zip(spines, SMPL_SPINE):
        m[bone.name] = smpl
    return m


def rot(mat):
    return mat.to_3x3().normalized().to_quaternion()


def direction_child(bone, bmap):
    kids = list(bone.children)
    direct = [k for k in kids if k.name in bmap]
    if direct:
        spine = [k for k in direct if bmap[k.name].startswith("Spine")]
        return (spine or direct)[0]
    for k in kids:
        grand = [g for g in k.children if g.name in bmap]
        if grand:
            return grand[0]
    return None


def find_source_armature(objs):
    """The armature that owns Pelvis: Hunyuan's FBX carries one per body part in some exports."""
    arms = [o for o in objs if o.type == "ARMATURE"]
    for a in arms:
        if "Pelvis" in a.data.bones:
            return a
    return arms[0] if arms else None


def bake(scene, target, source, frames, fps, src_fps, src_start=1, src_offset_s=0.0, in_place=False):
    """Keyframe `target`'s pose bones on frames 1..frames from `source`'s action.

    Returns (mapped bone count, height scale, hips travel over the clip in
    world metres, before the character's root transform). The source is sampled at
    src_start + (t / fps + src_offset_s) * src_fps, so a 30 fps Hunyuan clip lands
    correctly on a 24 fps shot.
    """
    tb = target.data.bones
    sb = source.data.bones
    bmap = build_map(tb)
    s_names = {b.name for b in sb}
    t_mw, s_mw = target.matrix_world.copy(), source.matrix_world.copy()
    arm_q = rot(t_mw)
    order = sorted(tb, key=depth)

    t_rest_w = {b.name: t_mw @ b.matrix_local for b in tb}
    s_rest_w = {b.name: s_mw @ b.matrix_local for b in sb}
    t_rest_q = {n: rot(m) for n, m in t_rest_w.items()}
    s_rest_q = {n: rot(m) for n, m in s_rest_w.items()}
    t_rest_p = {n: m.to_translation() for n, m in t_rest_w.items()}
    s_rest_p = {n: m.to_translation() for n, m in s_rest_w.items()}

    def height(ps):
        zs = [p.z for p in ps.values()]
        return max(zs) - min(zs)

    scale = height(t_rest_p) / max(height(s_rest_p), 1e-6)

    rest_local, aligned = {}, {}
    for b in order:
        pq = t_rest_q[b.parent.name] if b.parent else arm_q
        rest_local[b.name] = pq.inverted() @ t_rest_q[b.name]
    for b in order:
        start = (aligned[b.parent.name] if b.parent else arm_q) @ rest_local[b.name]
        q = start
        src = bmap.get(b.name)
        if src in s_names and src not in NO_ALIGN:
            kid = direction_child(b, bmap)
            ksrc = bmap.get(kid.name) if kid else None
            if kid and ksrc in s_names:
                off = t_rest_q[b.name].inverted() @ (t_rest_p[kid.name] - t_rest_p[b.name])
                d_now = (start @ off).normalized()
                d_src = (s_rest_p[ksrc] - s_rest_p[src]).normalized()
                if d_now.length > 0 and d_src.length > 0:
                    q = d_now.rotation_difference(d_src) @ start
        aligned[b.name] = q

    pbs = target.pose.bones
    for pb in pbs:
        pb.rotation_mode = "QUATERNION"
    hips = next((b for b in order if bmap.get(b.name) == "Pelvis"), None)
    prev = {}
    travel = Vector((0.0, 0.0, 0.0))
    mapped = sum(1 for b in tb if bmap.get(b.name) in s_names)

    for f in range(1, frames + 1):
        sf = src_start + ((f - 1) / fps + src_offset_s) * src_fps
        scene.frame_set(int(sf), subframe=sf - int(sf))
        s_now = {pb.name: s_mw @ pb.matrix for pb in source.pose.bones}
        world = {}
        for b in order:
            src = bmap.get(b.name)
            if src in s_now:
                delta = rot(s_now[src]) @ s_rest_q[src].inverted()
                world[b.name] = delta @ aligned[b.name]
            else:
                pw = world[b.parent.name] if b.parent else arm_q
                world[b.name] = pw @ rest_local[b.name]
        for b in order:
            R = arm_q.inverted() @ world[b.name]
            L = rot(b.matrix_local)
            if b.parent:
                Rp = arm_q.inverted() @ world[b.parent.name]
                Lp = rot(b.parent.matrix_local)
                basis = L.inverted() @ Lp @ Rp.inverted() @ R
            else:
                basis = L.inverted() @ R
            if b.name in prev and prev[b.name].dot(basis) < 0:
                basis = -basis
            prev[b.name] = basis
            pb = pbs[b.name]
            pb.rotation_quaternion = basis
            pb.keyframe_insert("rotation_quaternion", frame=f)
        if hips is not None and "Pelvis" in s_now:
            # Travel is measured from the clip's FIRST frame, not the bind pose:
            # Hunyuan's bind pose has the pelvis at the origin while the
            # animation carries the real standing height and a start offset, so
            # a bind-relative delta floats the character ~1 m up and jumps it
            # sideways. The first frame is assumed upright, so `loc` is exactly
            # where the character stands at the start of the shot.
            if f == 1:
                s_first = s_now["Pelvis"].to_translation()
            travel = (s_now["Pelvis"].to_translation() - s_first) * scale
            if in_place:  # keep the bob and crouch, drop the ground travel
                travel = Vector((0.0, 0.0, travel.z))
            want_arm = t_mw.inverted() @ (t_rest_p[hips.name] + travel)
            head_arm = hips.matrix_local.to_translation()
            pbs[hips.name].location = rot(hips.matrix_local).inverted() @ (want_arm - head_arm)
            pbs[hips.name].keyframe_insert("location", frame=f)
    return mapped, scale, travel
