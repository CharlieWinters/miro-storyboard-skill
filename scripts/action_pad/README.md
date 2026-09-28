# Action Pad: gamepad puppeteering for greybox characters

Drive Meshy-rigged characters live in Blender with a gamepad (or the
keyboard), trigger performance clips on a button, and render the result as
a storyboard motion reference (`<name>_block.png` + `<name>_move.mp4`).

## Quick start

```bash
# 1. Build a puppet stage from a spec (rigged subjects with a "puppet" block):
Blender -b -P scripts/blender_shot.py -- --spec S_PUPPET.json --out DIR --setup-only

# 2. Open it with Action Pad loaded (no add-on install):
scripts/action_pad/open_action_pad.sh DIR/S_PUPPET.blend

# 3. In the 3D view: N > Action Pad > Connect gamepad (first run installs pygame, ~1 min)
```

Pair the pad in System Settings > Bluetooth first. Anything SDL knows works:
Xbox, DualSense and DualShock, Switch Pro, 8BitDo.

## Controls (during a take)

| Pad | Keyboard | Does |
|---|---|---|
| left stick | WASD / arrows | walk, relative to the viewport (or the shot camera, or world +Y) |
| right trigger | Shift | push from walk into run (analogue) |
| left trigger | Ctrl | half speed |
| A B X Y | 1 2 3 4 | trigger the clip mapped to that button |
| Start | Space | start / stop the take (Esc stops too) |
| LB / RB | (panel dropdown) | previous / next puppet, between takes |

A take records **one puppet** from the start of the scene range while the
others play back, so you build a scene in passes. Re-recording a puppet
replaces its take. **Clear take** removes it.

During a take the heavy meshes hide and the rigs show as stick figures
(the "Stick figures while recording" option), so playback keeps up. Render
**Render grey clip** afterwards for the full-quality greybox.

## How it works

- **Locomotion** uses Meshy's own walk and run cycles (already on the
  character's skeleton). Their stride is measured when the library is built
  (CHAR_A: walk 1.40 m/s over 1.45 m, run 2.49 m/s over 1.58 m). The cycle
  advances by *distance covered / stride*, so feet stay planted at any
  speed. Walk and run blend by speed over an idle clip.
- **Performance clips** are Hunyuan Motion FBXs retargeted in place
  (`../retarget.py`), trimmed with `in`/`out`, and dropped on an NLA layer
  when a button is pressed. They blend in and out over 0.3 s, and movement
  pauses while one plays. A clip can't be retriggered until 60% of it has
  played.
- The movement logic (`puppet.step`) is plain Python: the live operator and
  `script_take.py` share it, so a scripted take is exactly what the same
  stick and button history would have recorded live.
- The gamepad is read outside Blender (Blender has no gamepad input) by
  `pad_bridge.py`, which streams the pad state as JSON over UDP to
  127.0.0.1:47811, 60 times a second.

## Spec

```json
{"name": "CHAR_A", "type": "rigged", "path": "<rigged_character.glb>", "loc": [4.3, 12, 0.14], "rot_z": 180,
 "puppet": {"walk": "<walking_armature.glb>", "run": "<running_armature.glb>",
            "idle": {"anim": "<idle.fbx>", "in": 0, "out": 6},
            "clips": {"flinch": {"anim": "<react.fbx>", "in": 1.6, "out": 6.0, "blend": 0.3}},
            "buttons": {"a": "flinch"}}}
```

## Scripted takes (no pad needed)

```bash
Blender -b DIR/S_PUPPET.blend -P scripts/action_pad/script_take.py -- \
  --takes takes.json --out DIR --name S_PUPPET_DEMO
```

`takes.json` lists input rows per puppet (`{"t": 2.0, "ly": 1, "rt": 0.6}`,
`{"t": 6.0, "b": true}`); each row holds until the next one. See
`examples/night_walk/demo_takes.json`.

## Limits

- Puppets don't collide: one will walk through another.
- Walk/run look right from about 0.3x to 1.8x of their natural pace. Past
  that, feet still plant but the gait reads wrong.
- The walk into a triggered clip is a 0.3 s crossfade, so there's a
  visible blend if the poses differ a lot.
- The same Meshy skinning as before: loose clothing stretches.
- The live operator needs a normal Blender window. Headless, use `script_take.py`.
