"""Clip library for a puppet: locomotion cycles and triggered performance clips.

A puppet's rig ends up with plain Actions (fake-user, so they survive saves),
one per clip, plus the numbers the puppet engine needs to keep feet planted:

- walk / run: Meshy Rigging's own cycles (`walking_armature.glb`,
  `running_armature.glb`), already on the character's skeleton, so no
  retargeting. Any net root travel is detrended out: the puppet's root empty
  does the travelling, the cycle only moves the legs. The cycle's ground
  distance is measured from how far a foot slides back while planted.
- idle and triggered clips: Hunyuan Motion FBXs retargeted onto the rig in
  place (scripts/retarget.py), trimmed to `in`..`out` seconds.

Everything is recorded on the armature as custom properties
(`ap_clips`, JSON) so the add-on can rebuild its UI from a saved .blend.
"""

import json

import bpy


def _new_objects_since(before):
    return [o for o in bpy.data.objects if o not in before]


def _action_fcurves(action):
    flat = getattr(action, "fcurves", None)
    if flat is not None:
        return list(flat)
    out = []
    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            for bag in getattr(strip, "channelbags", []):
                out.extend(getattr(bag, "fcurves", []))
    return out


def _detrend_root(action, root_bone="Hips"):
    """Remove the straight-line drift from the hips' location keys.

    A cycle that creeps forward would double up with the root empty's own
    travel. Subtracting the ramp between the first and last key keeps the
    bob and sway and removes the net displacement.
    """
    path = f'pose.bones["{root_bone}"].location'
    for fc in _action_fcurves(action):
        if fc.data_path != path or len(fc.keyframe_points) < 2:
            continue
        k0, k1 = fc.keyframe_points[0], fc.keyframe_points[-1]
        f0, v0, f1, v1 = k0.co.x, k0.co.y, k1.co.x, k1.co.y
        if f1 == f0:
            continue
        for kp in fc.keyframe_points:
            ramp = v0 + (v1 - v0) * (kp.co.x - f0) / (f1 - f0)
            d = ramp - v0
            kp.co.y -= d
            kp.handle_left.y -= d
            kp.handle_right.y -= d
        fc.update()


def _sample(arm, action, bones, frames):
    """World positions of `bones` at `frames` with `action` playing on `arm`."""
    scene = bpy.context.scene
    ad = arm.animation_data_create()
    keep = ad.action
    ad.action = action
    # Blender 5 slotted actions: an action imported for another object keeps
    # that object's slot name, so it isn't bound here until assigned by hand.
    if getattr(ad, "action_slot", None) is None and len(getattr(action, "slots", [])):
        ad.action_slot = action.slots[0]
    out = []
    for f in frames:
        scene.frame_set(int(f), subframe=f - int(f))
        out.append({b: (arm.matrix_world @ arm.pose.bones[b].head).copy() for b in bones})
    ad.action = keep
    return out


def import_cycle(arm, path, name):
    """Load a Meshy armature-only cycle GLB as an Action on `arm`; measure it."""
    before_objs, before_acts = set(bpy.data.objects), set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    new_acts = [a for a in bpy.data.actions if a not in before_acts]
    for o in _new_objects_since(before_objs):
        bpy.data.objects.remove(o, do_unlink=True)
    if not new_acts:
        raise RuntimeError(f"{path}: no animation in cycle file")
    act = new_acts[0]
    act.name = name
    act.use_fake_user = True
    _detrend_root(act)

    f0, f1 = act.frame_range
    n = 48
    frames = [f0 + (f1 - f0) * i / n for i in range(n)]
    samples = _sample(arm, act, ["LeftFoot", "RightFoot"], frames)
    # Rig faces -Y at rest, so a planted foot slides toward +Y. The foot's
    # fore-aft range is one step; a cycle is two steps.
    ranges = []
    for foot in ("LeftFoot", "RightFoot"):
        ys = [s[foot].y for s in samples]
        ranges.append(max(ys) - min(ys))
    step = sum(ranges) / len(ranges)
    fps = bpy.context.scene.render.fps
    duration = (f1 - f0) / fps
    return act, {"kind": "cycle", "start": f0, "end": f1,
                 "distance": round(2 * step, 4), "duration": round(duration, 4),
                 "speed": round(2 * step / duration, 4)}


def bake_clip(arm, fbx_path, name, t_in, t_out):
    """Retarget a Hunyuan Motion FBX onto `arm`, in place, trimmed, as an Action."""
    import retarget

    scene = bpy.context.scene
    fps = scene.render.fps
    keep = (scene.render.fps, scene.frame_start, scene.frame_end)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    src_objs = _new_objects_since(before)
    src_fps = scene.render.fps
    scene.render.fps, scene.frame_start, scene.frame_end = keep
    source = retarget.find_source_armature(src_objs)
    if source is None or not (source.animation_data and source.animation_data.action):
        raise RuntimeError(f"{fbx_path}: no animated armature")
    src_start = source.animation_data.action.frame_range[0]

    ad = arm.animation_data_create()
    keep_action = ad.action
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    ad.action = act
    frames = max(2, int(round((t_out - t_in) * fps)))
    mapped, _scale, _travel = retarget.bake(scene, arm, source, frames, fps, src_fps, src_start,
                                            src_offset_s=t_in, in_place=True)
    ad.action = keep_action
    for o in src_objs:
        bpy.data.objects.remove(o, do_unlink=True)
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    return act, {"kind": "clip", "start": 1.0, "end": float(frames), "mapped_bones": mapped,
                 "duration": round(frames / fps, 4)}


def build_library(arm, puppet_spec, resolve):
    """Build every clip named in `puppet_spec`; store the table on the armature.

    puppet_spec = {
      "walk": <cycle glb>, "run": <cycle glb>,
      "idle": {"anim": <fbx>, "in": 0, "out": 6},
      "clips": {"react_left": {"anim": <fbx>, "in": 1.0, "out": 5.0}, ...},
      "buttons": {"a": "react_left", "b": "flinch", ...}
    }
    `resolve` turns a path or URL into a local file.
    """
    table = {}
    tag = arm.parent.name if arm.parent else arm.name
    for key in ("walk", "run"):
        if puppet_spec.get(key):
            act, meta = import_cycle(arm, resolve(puppet_spec[key]), f"{tag}.{key}")
            table[key] = dict(meta, action=act.name)
    clips = dict(puppet_spec.get("clips") or {})
    if puppet_spec.get("idle"):
        clips["idle"] = puppet_spec["idle"]
    for cname, c in clips.items():
        act, meta = bake_clip(arm, resolve(c["anim"]), f"{tag}.{cname}",
                              float(c.get("in") or 0.0), float(c.get("out") or 6.0))
        table[cname] = dict(meta, action=act.name, blend=float(c.get("blend") or 0.3))
    arm["ap_clips"] = json.dumps(table)
    arm["ap_buttons"] = json.dumps(puppet_spec.get("buttons") or {})
    return table
