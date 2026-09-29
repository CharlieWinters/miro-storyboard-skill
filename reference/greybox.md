# Greybox mode

Only when the director chose the greybox pass in pre-flight. The rendering
itself (sets, 3D characters, rigs and motion, cameras, Action Pad
puppeteering) lives in the **`greybox-shot`** skill. Load it and follow it for
each shot. This file covers the storyboard side: what to decide, what to hand
over, and how the renders go on the board.

## Per shot: greybox or not

Decide per shot, not per film (`greybox-shot`, `reference/blocking.md`, first
section). Yes when geometry, a camera move or a body performance is the point;
no for organic close-ups; never for open landscape (use a camera board,
`image-generation.md`). If a shot's answer is no, say so on its row in one
line.

## What to hand `greybox-shot`

- One spec per shot, named `S<n>` so the renders come back as
  `S<n>_block.png` / `S<n>_move.mp4`. Same aspect and fps as the film;
  `duration` = the clip length planned in Step 2.
- For 3D characters or props: the storyboard's reference sheets
  (`CHAR_*`, `PROP_*`) are the input to its asset lane. Generate them as
  turnarounds in a neutral A-pose with no labels, and they crop straight into
  image-to-3D views.
- Build the set at the size the film needs, then make `SET_*` plates **from
  the greybox**, not the other way round. A plate made first imposes its own
  street width on every key frame conditioned on it
  (`image-generation.md`).

## On the board

Per shot, in its Shots row (Step 6), left of the image card:

- `S<n>_BLOCK`: the still, 480 wide, top-left at (80, row).
- `S<n>_MOVE_PREVIEW`: the GIF, 240 wide, under the still.
- `S<n>_MOVE`: a caption with the fal URL of the mp4 and the one-line
  instruction to turn it into an embed with the app's "Add Video from URL"
  and wire it to the shot's card (`motion.md`; the MCP can't make embeds).
- Condition `S<n>_KEY` on `S<n>_BLOCK`, **first** in `image_urls`, and wire it
  to the key's image card in that order.
- A short note of what the performance is, if characters are rigged (e.g.
  "A: stops, turns left; B: flinches 0.8 s later").

For the library: a 3D asset gets a purple image-to-3D card (endpoint
`fal-ai/hunyuan-3d/v3.1/pro/image-to-3d`, `capability: "model3d"`,
`input: {"generate_type": "Geometry"}`, `referenceField: null`) wired to its
sheet and view crops, a grey preview render, and the GLB URL as text. The
app has no multi-view card format, so the director assigns views to slots in
the panel.

## Placing a rendered still on the board

Three calls per image. **`x`/`y` are the image's CENTRE**, relative to frame
top-left; see the contract doc, this one bites.

```
h = w * srcH / srcW          # 480 wide from a 1280×720 render → 270
x = topLeftX + w/2           # 80  + 240   → 320
y = topLeftY + h/2           # 180 + 135   → 315
```

1. `image_get_upload_url`: board URL + `?moveToWidget=<frameId>`, with
   `title`, `x`, `y`, `width`, `content_type: image/png`
2. `curl -X PUT -H 'Content-Type: image/png' --data-binary @file '<upload_url>'`
3. `image_create` with the returned `image_token` (title/x/y/width come from
   the token; anything passed again is ignored)

Get the URL into a file before curling it: it is long and full of `&`.

Position must be correct at creation: an image made this way is a foreign item
to the canvas composer, which will claim to have moved it and not move it.
