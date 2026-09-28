"""Record Action Pad takes from a script instead of a gamepad, then render.

    Blender -b shot.blend -P script_take.py -- --takes takes.json --out DIR [--no-render]

takes.json:
    {"takes": [
       {"puppet": "CHAR_A", "cam_fwd": "camera",
        "input": [{"t": 0,   "ly": 1.0},
                  {"t": 2.0, "lx": 0.6, "ly": 0.8},
                  {"t": 3.0, "ly": 0, "a": true},
                  {"t": 3.2, "a": false}]}]}

Each input row holds until the next one (a gamepad state, sampled at 60 Hz),
so this is exactly what a live take would have recorded given the same stick
and button history. Takes run in order, so a later take plays against the
earlier ones, just like recording passes live.
"""

import argparse
import json
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import puppet  # noqa: E402


def camera_forward(scene):
    cam = scene.camera
    if cam is None:
        return (0.0, 1.0)
    v = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    return (v.x, v.y) if abs(v.x) + abs(v.y) > 1e-4 else (0.0, 1.0)


def run_take(scene, take, hz=60):
    root = bpy.data.objects[take["puppet"]]
    cam_fwd = camera_forward(scene) if take.get("cam_fwd", "camera") == "camera" else tuple(take["cam_fwd"])
    rec = puppet.Take(root, scene, take.get("speed_scale", 1.0), take.get("turn_rate", 220.0), cam_fwd)
    rows = sorted(take["input"], key=lambda r: r["t"])
    state, i, dt = {}, 0, 1.0 / hz
    while True:
        t = rec.state["t"]
        while i < len(rows) and rows[i]["t"] <= t + 1e-9:
            state.update({k: v for k, v in rows[i].items() if k != "t"})
            i += 1
        if not rec.tick(state, dt):
            break
    return rec.finish()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--takes", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--still-only", action="store_true")
    args = ap.parse_args(argv)
    args.out = os.path.abspath(args.out)  # Blender resolves relative render paths against the .blend
    scene = bpy.context.scene
    with open(args.takes) as f:
        takes = json.load(f)["takes"]
    results = [run_take(scene, t) for t in takes]
    out = {"takes": results}
    os.makedirs(args.out, exist_ok=True)
    name = args.name or scene.get("shot_name", "TAKE")
    if not args.no_render:
        import blender_shot
        out.update(blender_shot.render_outputs(scene, name, args.out, args.still_only))
    blend = os.path.join(args.out, f"{name}_take.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    out["blend"] = blend
    print("TAKE_RESULT " + json.dumps(out))


if __name__ == "__main__":
    main()
