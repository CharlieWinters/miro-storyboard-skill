# Greybox mode (Blender)

Only when the director chose the greybox pass in pre-flight. Read this before rendering.

## Deciding the greybox — this is the judgement call

Greybox earns its keep when **geometry is the shot**: a wide establishing
frame, converging lines, a product's proportion, a camera move that has to
stay honest, anything where scale between two things matters.

It actively hurts on an **organic close-up**. A hand approximated from a
cylinder and a cube is not a hand, and a video model conditioned on that image
will faithfully render a cylinder and a cube. Block only what you want the
model to obey, and let the prompt carry the rest.

**Expect a director to cut the greybox leg entirely, and take the note.** On
the one film this skill has run end to end, the director looked at clay stills
next to illustrated camera boards and said the boards did the job better — so
the greyboxes came off the board. That is the right call for exterior
landscape. Keep the greybox in your pocket for interiors and object-heavy sets
and do not argue for it on open ground.

If a shot's answer is no, say so on the board. A director reading "no —
organic macro, a blocked hand would render as a block" learns the tool.

## Rendering

One JSON spec per shot; `loc`/`size` in metres, camera in the same world.

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b \
  -P ~/.claude/skills/miro-storyboard/scripts/blender_shot.py -- \
  --spec "$CLAUDE_JOB_DIR/tmp/sb/SHOT01.json" \
  --out  "$CLAUDE_JOB_DIR/tmp/sb"
```

Prints `SHOT_RESULT {json}` with the still, clip, saved `.blend` and
resolution. About 5 s per shot for a still plus a 3 s clip. Add `--still-only`
to skip the clip.

```json
{
  "name": "SHOT01", "aspect": "16:9", "width": 960, "fps": 24, "duration": 3.0,
  "ground": true, "ground_size": 240,
  "clay_color": "#b9b4ad", "sky_color": "#e6e2dc",
  "camera":     { "loc": [1.9, -7.0, 1.70], "look_at": [0, 26, 1.1], "lens": 32 },
  "camera_end": { "loc": [1.9, -1.0, 1.55], "look_at": [0, 28, 1.0], "lens": 32 },
  "sun": { "elevation_deg": 6, "azimuth_deg": 95, "strength": 4.5, "softness_deg": 1.5 },
  "subjects": [
    { "name": "ROW1", "type": "cube", "loc": [-14, 34, 0.5], "size": [1.6, 78, 1.0] },
    { "name": "PICKER", "type": "human", "loc": [-2.1, 9, 0], "height": 1.75, "rot_z": 150 },
    { "name": "TOMATO", "type": "sphere", "loc": [0, 0, 1.02], "size": [0.085, 0.085, 0.085],
      "loc_end": [0, -0.04, 1.11] }
  ]
}
```

- `type`: `cube` · `cylinder` · `sphere` · `cone` · `plane` · `wall` · `human` · `glb`
- `loc` is a primitive's **centre** but a figure's (and a GLB's) **feet**
- `rot_x` / `rot_y` / `rot_z` in degrees — reach for pitch before faking an
  angle with extra geometry
- `loc_end` moves a subject over the clip (eased; `"motion": "linear"` for constant speed); `camera_end` moves the camera
- omit `camera_end` for a locked-off shot

## Real meshes instead of clay: `type: "glb"`

When the mannequin is too crude (it has no facing, no silhouette, no
costume), generate the characters and props as meshes and block with those.
Verified 2026-09-28 on the *Night Walk* demo board (`uXjVHh8qBX0=`).

```json
{ "name": "CHAR_A", "type": "glb", "path": "https://v3b.fal.media/…/model.glb",
  "loc": [4.3, 24, 0.14], "loc_end": [4.3, 20.5, 0.14], "rot_z": 0,
  "height": 1.68, "decimate": 0.25 }
```

- `path`: a local file (relative to the spec) or an http(s) URL, cached in
  `<out>/_assets` so a re-render doesn't re-download.
- `height` (m, bounds z) or `length` (m, longest horizontal side) sets a
  uniform scale; `scale` multiplies on top.
- The mesh is recentred so `loc` is the **bottom-centre** of its bounds: feet
  for a person, tyres on the road for a car.
- Facing: a glTF front (+Z) imports facing **-Y**, i.e. toward a camera at
  negative y. `rot_z` turns it from there.
- `decimate` (0–1) thins image-to-3D output (≈500k faces) so the `.blend`
  stays small. 0.25 still reads fine in a wide.
- Materials are ignored. Workbench draws everything in clay, so a textured
  GLB costs money for nothing: generate **geometry only**.
- A GLB is rigid. `loc_end` slides it, so a walking figure glides in its
  A-pose. That's fine for position and scale; don't promise a gait.

**Which image-to-3D model** (live prices, 2026-09-28): Hunyuan 3D v3.1 Pro
(`fal-ai/hunyuan-3d/v3.1/pro/image-to-3d`) is the one that takes a
turnaround: front + back + left + right (+ ¾) view slots and a
`generate_type: "Geometry"` mode. $0.375, +$0.15 for multi-view, +$0.15 for a
custom face count. Crop each view out of the sheet onto a padded square and
map them by what the view *shows*: a figure facing screen-right shows its
**right** side. Tripo H3.1 ($0.20 untextured) and Trellis 2 ($0.30 at 1024) are
single-image only. Of four turnaround sheets, only the car's had a bad view
(the "right profile" was a mirrored left), so check every crop before
uploading it.

The Fal app has no multi-view card format: an image-to-3D recipe card saves
`referenceField: null` and the director assigns each view to its slot in the
panel. Wire the sheet and the view crops to the card so they're at hand.

**A vehicle passing with a whip-pan** (Shot 3 of *Night Walk*): give the car
`"motion": "linear"` so it holds a constant speed (subjects ease by default,
which reads as pulling away from a stop), keep the camera fixed and animate
only `look_at`, sweeping it **along the car's lane** from far ahead to far
behind, with the car passing the camera at mid-clip. The camera's default
ease then holds on the approach, whips as the car passes and settles on it
driving away. Sweeping `look_at` through the camera's own position instead
flips the view. Extend the set **behind** the camera and close that end too,
or the whip lands on open sky.

**Want to perform it yourself?** Give a rigged subject a `"puppet"` block
instead of `anim`, build with `--setup-only`, and drive it live with a gamepad
in Blender: `scripts/action_pad/README.md`.

## Performing characters: `type: "rigged"` (Meshy Rigging + Hunyuan Motion)

A GLB is a statue. For a shot whose point is a performance (a walk-and-talk, a
flinch, a head turn), rig the character and drive it with a text-described
motion. Verified 2026-09-28 on *Night Walk* shots 2 and 4.

1. **Rig** each character GLB with `fal-ai/meshy/rigging` ($0.80): pass
   `model_url` and `height_meters`. Our 500k-face, untextured Hunyuan meshes
   rigged first time, no decimation. You get a Mixamo-style 24-bone skeleton
   (spine numbered top-down: Spine02 → Spine01 → Spine).
2. **Motion** from `fal-ai/hunyuan-motion` ($0.08, ~11 s): a prompt and a
   `duration` (0.5–12 s). It returns an FBX on an SMPL-H skeleton at 30 fps.
   Write the performance as body language with timing: "takes two slow steps
   and stops, then flinches, throws the right arm out, turns the head sharply
   to the left".
3. **Subject:**
   ```json
   { "name": "CHAR_B", "type": "rigged", "path": "<rigged_character.glb>",
     "anim": "<hy_motion.fbx>", "loc": [5.1, 12.2, 0.14], "rot_z": 180,
     "anim_offset": 0.8 }
   ```
   `scripts/retarget.py` (a port of the Fal app's `embed/retarget.ts`) bakes the
   motion onto the rig: it maps bones by name, turns each character bone to point
   the way the mannequin's does, and scales the hips' travel by height. The
   SHOT_RESULT reports `mapped_bones` (22 is all of them) and `travel_m`.

What bit, and the fixes now in the script:

- **Hips travel is measured from the clip's first frame, not the bind pose.**
  Hunyuan's bind pose has the pelvis at the origin, so a bind-relative delta
  floated the figure a metre up and jumped it sideways.
- **Motions wander.** A "walk" veers 6–8° and a "reaction" once walked 5 m
  diagonally before reacting. Read `travel_m`, then either counter-rotate
  with `rot_z` (atan of the lateral drift over the forward travel), set
  `in_place: true` (keeps the bob, drops the ground travel), or regenerate
  the clip with "stays in place" in the prompt. Regenerating gave the best
  reaction.
- **Two walkers drift apart and out of step.** Each clip has its own pace:
  offset the slower walker's start by the difference in `travel_m`.
- **`anim_offset`** staggers two reactions so one lands a beat after the
  other. Past the clip's end, the last pose holds.
- Both rigs face -Y at rest, like `glb`: `rot_z: 180` turns a walk toward
  +Y, travel included.
- A long coat skins to the legs as a skirt. Fine in grey; don't promise cloth.
  There are no finger or face bones: performance means head, shoulders, arms, gait.
- Frame a reaction wider than feels natural, and light the faces
  (`extra={"sun": …}` with the sun behind camera). The first S4 at 50 mm hid
  the car it was reacting to, and its walls rendered black.

`repeat: {"count": 8, "offset": [0, 15, 0]}` on any subject lays out copies
along a line (`NAME_1`, `NAME_2`, …). Use it for lamp posts, bollards and
parked cars.

**A street that reads in grey:** a road slab, raised kerbs (0.16 m) and
pavements both sides, building blocks of varying height and depth with a
cornice ledge for horizontal lines, lamp posts every 15 m on both kerbs, and a
building across the far end so the vanishing point terminates instead of
opening onto sky.

**Greybox fails on open terrain, and no amount of iterating fixes it.**
Verified over four passes on a downhill road: an untextured clay road on an
open hillside renders as one flat grey field, because there is nothing for the
eye to catch — no occluders, no cast shadows across the surface, no scale
objects. Greybox earns its keep in a set with *stuff in it* (rows, walls,
furniture, a product on a table). For an open landscape, a camera-movement
board (`image-generation.md`, "Camera-movement boards") communicates the move far better and in one pass. Decide this
before you render, not after the third attempt.

**The mannequin is symmetric, so it has no readable facing.** Box torso, sphere
head, cylinder legs — front and back are identical. Do not try to judge or fix
which way a figure faces from a greybox, and do not promise a director that it
shows orientation. Only position, scale and camera read.

**`ground: true` will silently eat a descending set.** The ground plane is flat
at `z=0` and the same clay colour as everything on it, so any geometry you put
below zero — a road falling away into a valley, a shot looking *down* at
something — is buried, and the frame renders as an empty grey field with a
correct-but-invisible model underneath. For anything that descends, set
`ground: false` and build the terrain as explicit slabs under the road.

**Give a road edge rails.** A flat ribbon the same colour as the ground has no
readable convergence. Two thin raised cubes along the verges (`size: [0.35,
<len>, 1.0]` at `x = ±7`) give the model the converging lines that are the
entire point of blocking a road shot.

**Stage subjects close enough to read.** A 1.75 m figure 12 m from a wide lens
is ~10% of frame height — fine when you *want* them dwarfed, useless when the
shot is about them. Work out the vertical extent at the subject's distance
before rendering, not after.

**Look at the render before you put it on a board.** `Read` the PNG — or stack
several with `ffmpeg ... vstack` into one contact sheet and read that. A spec
error is invisible in JSON and obvious in the image: rows laid *across* frame
instead of *away* from camera read as flat bands rather than converging on a
vanishing point, and that is the difference between a useful reference and a
misleading one.

## Placing a rendered still on the board

Three calls per image. **`x`/`y` are the image's CENTRE**, relative to frame
top-left — see the contract doc, this one bites.

```
h = w * srcH / srcW          # 450 wide from a 960×540 render → 253.125
x = topLeftX + w/2           # 40  + 225   → 265
y = topLeftY + h/2           # 90  + 126.5 → 217
```

1. `image_get_upload_url` — board URL + `?moveToWidget=<frameId>`, with
   `title`, `x`, `y`, `width`, `content_type: image/png`
2. `curl -X PUT -H 'Content-Type: image/png' --data-binary @file '<upload_url>'`
3. `image_create` with the returned `image_token` (title/x/y/width come from
   the token; anything passed again is ignored)

Get the URL into a file before curling it — it is long and full of `&`.

Position must be correct at creation: an image made this way is a foreign item
to the canvas composer, which will claim to have moved it and not move it.
