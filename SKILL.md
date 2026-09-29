---
name: miro-storyboard
description: Turn a video idea into a Miro board a director can generate a film from — board-first. The director lays out a style frame and a loose frame per scene; Claude asks the pre-flight questions, plans scenes and clip lengths from one video model's limits, prices the film, builds a reference library and a cheap first-pass image per shot, and stages an editable image card for every generated image plus one video settings card per shot (which the Fal-for-Miro app converts into a clickable node), laid out in a separate Shots row under the director's scene frames. Stops before any video is generated. Use when someone wants a film, ad or video idea storyboarded, shot-listed or staged on a Miro board for AI video generation, or wants a template board to start one.
allowed-tools: [Bash, Read, Write]
argument-hint: [the video idea or a board URL, plus optional aspect / length / model]
---

# Miro storyboard, board-first

The **director** owns the board: the mood board, the style, and a loose
structure of scenes. **Claude does the heavy lifting in between**: it reads that
board, plans the film around one video model's limits, prices it, builds the
references and a first-pass image per shot, and stages one settings card per
shot. The director converts each card into a **node** in the Fal-for-Miro app
and generates from it. **Claude never generates video**: video is the
expensive, taste-driven call, and it stays with the person.

**No browser automation.** This runs on the Miro MCP, the fal MCP and, only
for greybox mode, the **`greybox-shot`** skill (headless Blender), which
renders the grey `_BLOCK` stills and `_MOVE` clips.

Read `reference/board-contract.md` before your first board. It records what
the app actually reads off a board, with citations. The other references are
read when a step points to them:

| File | When |
|---|---|
| `reference/board-contract.md` | always, before building |
| `reference/models.md` | Step 3: choosing, limits, pricing |
| `reference/image-generation.md` | Step 5: references, conditioning, camera boards |
| `reference/greybox.md` | only in greybox mode: what to hand `greybox-shot`, and how its renders go on the board |
| `reference/motion.md` | only for a greybox clip published as an mp4 |

## The shape of the board

| Frame | Who makes it | What it holds |
|---|---|---|
| **Style** (one, titled `STYLE`) | director | the film's look: palette, grade, lens feel, reference stills, a line or two of intent |
| **Scene N · <name>** (one per scene) | director | mood images and structure stickies only. **Claude never adds rows here** |
| **Shots · Scene N** (a row of frames under the scenes) | Claude | one row per shot: image card, key frame, prompt, video card, take lanes (Step 6) |
| **Reference library** (a band of frames) | Claude | one character sheet, prop or set plate per frame (`CHAR_*`, `PROP_*`, `SET_*`), each with its image card |
| **Plan · <film>** | Claude | the scene/clip arithmetic, the model and why, the cost estimate |

**A frame per scene is the default, not a rule.** If the director has
structured the board differently (a frame per shot, a single long frame,
columns), follow what's there and say how you read it in the pre-flight
message. Ask only if it can't be read.

## Step 0 — Pre-flight. Ask everything in one message, then wait.

Put these to the director in **one plain-text message** (never an
options picker), each with the default you'd pick, so the answer can be "yes to
all":

1. **Board.** Their board URL, a template board to start from (Step 1b), or a
   new board. `board_create` needs an explicit yes, so never create one unasked.
2. **Aspect ratio.** Default **16:9 widescreen** (the film-festival default).
   9:16 for social, 21:9 for scope.
3. **Resolution.** Default the model's own top tier that the budget allows
   (e.g. 2K on MiniMax H3). Say what 4K would add to the cost.
4. **Film length.** Default **just over a minute**. Planned clip by clip in
   Step 2.
5. **One video model for the whole film.** Recommend one and say why (see
   `reference/models.md`: one model across every cut). The default is
   `minimax/h3/reference-to-video`: it takes a photoreal actor, 9 reference
   images and 3 motion clips.
6. **Pass.** Images only (default: a look and a read in minutes) or a
   greybox too via the `greybox-shot` skill (literal camera geometry, and with
   rigged characters, real body performances; worth it for interiors, streets,
   object-heavy sets and performance beats, not open landscape; ≈10 min, or
   more with 3D characters). See `reference/greybox.md`.
7. **Budget ceiling** for the first pass. Default: confirm anything over $1.

Also say, briefly, how you read their board: "I see a STYLE frame and 5 scene
frames; I'll treat each as a scene".

**Always individual clips.** The deliverable is one video per shot, generated
by the director from its node. Editing them into a film happens afterwards in
iMovie or similar. Don't plan merges, and don't stage a single long take.

## Step 1 — Read the board

`canvas_search` with `result_mode: "overview"` for frame titles, then
`canvas_read_as_svg` scoped to each frame. From each scene frame take:

- the **structure stickies**: what happens, in the director's words. These
  are the brief. Quote them back; don't rewrite their story.
- the **mood images** and their titles. A titled image is a reference that
  the director has already chosen. Untitled ones are mood, so give them a title
  before relying on them (`labelOf` binds by title).

From the **STYLE** frame take the look, and carry it into every prompt as one
consistent style line (e.g. "Stylised 2D cel-shaded anime, hard shading, thick
linework, humid green and rust palette").

### Step 1b — A template board, for someone starting from nothing

If the board is empty or the director asked for a template, lay out the empty
structure and **stop**: the director fills it before anything is generated.

- A `STYLE` frame with three instruction stickies: *"Drop 3–6 images whose
  look you want"*, *"One line: what should this film feel like?"*, *"Anything
  it must never look like"*.
- Four `Scene N · …` frames (the director adds or deletes), each with two
  stickies: *"What happens in this scene, in a sentence or two"* and *"Drop
  any images for this scene: places, people, props, framing you like"*.
- A short `How this board works` note: fill the frames, then ask Claude to
  plan; Claude adds shots, references and one settings card per shot; convert
  each card to a node in the Fal app and press Generate.

Build it in **one** `canvas_create_from_svg` call so the layout survives
collision avoidance. Report the URL and stop.

## Step 2 — Plan the film around the model

With the model fixed in pre-flight, read its limits with `get_model_schema`
(`reference/models.md`, "Planning clip lengths"):

- the allowed **durations** (`enum`, or `minimum` / `maximum`);
- the **reference caps** (images, videos, audio) and any image rules. MiniMax
  H3 needs every reference between 0.4 and 2.5 in aspect ratio and at least
  256 × 256.

Then, for each scene, decide the shots and their clip lengths so the film
comes out at the agreed length. Write the arithmetic down, e.g. *"Scene 1: 3
shots × 6 s = 18 s … total 7 scenes, 12 shots, 76 s"*. Per shot decide:

- a **title**, `Shot 3 · The crest` (numbered across the whole film);
- the **references** it needs: which characters, props, sets, and whether it
  needs a camera board (a move with more than one camera action);
- an **image prompt** for the first-pass still (the frame as a photograph:
  subject, light, lens, palette, plus the style line);
- a **video prompt**: what moves, for how long, how the camera behaves, which
  references it names **by board title** (never `@Image1`; the app rewrites
  titles into the model's own dialect).

Put the plan on the board in a `Plan · <film>` frame: scene table, model and
why, clip arithmetic, and the estimate from Step 3.

## Step 3 — Price it, and confirm before spending

Two numbers, both from `get_pricing` (never from memory):

1. **This pass (what Claude spends):** reference sheets + one first-pass
   image per shot + camera boards. With nano-banana-2 at $0.08 an image and GPT
   Image 2 camera boards at $1, write the total out.
2. **The film (what the director will spend):** video cost per clip × clips,
   at the chosen resolution and durations. Claude does not spend this, but the
   director should see it before starting.

Under the budget ceiling, report and proceed. Over it, or if the ask sounded
exploratory, confirm first.

## Step 4 — Build the reference library first

Before any shot image, make **one reference per element**, each in its own
frame in a `Reference library` band: character turnaround sheets, a crew
line-up, prop turnarounds, clean set plates with **no people**. Build the
character sheet from the director's reference or an approved first-pass frame,
and everything else from the sheet: that is what keeps a face consistent
across cuts. Details and prompts: `reference/image-generation.md`, "The
reference library".

**Keep every reference inside the model's image rules.** For MiniMax H3 that
means aspect between 0.4 and 2.5: a 16:9 sheet (1.78) is fine; a 4-panel strip
at 32:9 (3.56) is not.

**Every reference gets an image card too** (Step 6, "Image cards"). Lay each
library frame out as `[image card][80 px][sheet]`: the card at the frame's
left edge and the sheet 80 px to its right, which is exactly where the app
drops a regenerated image. The frame is about 1,900 wide.

## Step 5 — First pass, per shot

In cut order, per shot:

1. **Key frame** `S3_KEY`: one image, conditioned on its references (the
   library sheets, the director's own photos, the previous shot's key for
   continuity). Follow `reference/image-generation.md` exactly for board images
   as inputs: `image_get_url` gives a signed URL that lives **15 minutes**, so
   `upload_file(url=…)` it to fal **immediately** and pass the fal URL. The
   first `image_urls` entry dominates, so put the image being edited first.
2. **Camera board** `S3_CAM` (only for a shot with a real move): the
   three-panel GPT Image 2 strip. It's a reference, not a start frame, but it
   must still obey the model's image rules. Generate it as one 16:9 sheet so
   it stays inside MiniMax's 0.4–2.5.
3. **Look at every image** before it goes on the board (`Read` it).
4. **Keep the recipe of every image you keep**: endpoint, the exact prompt,
   `aspect_ratio`, `resolution`, and the ordered list of board images it was
   conditioned on. That becomes its image card in Step 6. A redo replaces
   the recipe; don't stage the rejected one.

**No `FAL_KEY` is needed for any of this**, including local files: the fal MCP
carries its own credentials. `upload_file(url=…)` re-hosts a board image, and
`upload_file(prepare_upload=true, file_name, file_size)` returns a signed URL
to `curl -X PUT` a local greybox render or mp4 to (verified 2026-09-28).

In greybox mode, render the shots with the `greybox-shot` skill first, place
the `_BLOCK` stills, and condition each key frame on its `_BLOCK`
(`reference/greybox.md`).

## Step 6 — Build the Shots row: image cards, key frames, prompts, video cards

**Never touch the director's scene frames.** Directly under each one, make a
`Shots · Scene N · <name>` frame. Laid left to right, they form a separate
Shots row the director works through frame by frame. Each shot is one row inside
its frame, with a grey column header along the top of the frame:

| Column (x inside the frame) | Item | Notes |
|---|---|---|
| 80 | **image card** `S3_KEY · <image model>` | green (`#00b86b`); regenerates the key frame |
| 480 | **key frame** `S3_KEY`, 720 wide | 80 px right of the image card, where a regenerated image lands. `image_create` x/y is the **centre** |
| 480, under the key | camera board `S3_CAM` | only if the shot has one; makes that row taller |
| 1240 | video prompt sticky | light blue, 350 × 228; names references by board title |
| 1640 | **video card** `Shot 3 · <video model>` | orange; becomes the node |
| 2040 / 2834 | **TAKE 1 / TAKE 2** lanes, 720 wide each | empty: the app drops a clip 80 px right of the node |

Rows are 480 apart, or about 900 for a row with a camera board. The frame is
about 3,640 wide. Put the video card's top at `row + 17`: a node takes the
card's top-left and is 320 × 448, so its middle, and the clip it produces,
line up with the key frame. Keep the reference library below the tallest
Shots frame. If it's in the way, move it: frames carry their images with
them.

**The video settings card** (`reference/board-contract.md`, "Settings cards" and
"Nodes"):

- `description` = compact recipe JSON: `{"v":1,"endpointId":"minimax/h3/reference-to-video","capability":"video","input":{"prompt":"<video prompt, references by title>","aspect_ratio":"16:9","resolution":"2K","duration":6},"referenceField":null,"videoReferenceField":null}`.
  **Always set `aspect_ratio`**; never leave it `adaptive`.
- **Wire each reference to the card with a connector, in the order you want
  them numbered**: key frame first, then characters, props, set, camera board.
  Wired references override the frame's own images, so the mood board doesn't
  ride along.
- **Create the card and its connectors in the same `canvas_create_from_svg` /
  `canvas_update_from_svg` call**, stubbing existing images with a local `id`
  plus their `data-miro-id`. **Never send the card back through an update
  afterwards**: that re-encodes its description and breaks it. To change a
  card, delete it and recreate it with its connectors.
- Stay inside the model's caps (H3: 9 images). If a shot needs more, drop
  the weakest reference and say which.

**Image cards: one per image Claude generated**, including key frames, reference
sheets, set plates and camera boards. The director will want to tweak these.
A card holds the exact recipe from Step 5, so they can reopen it, edit the
prompt or swap a reference, and regenerate without starting from scratch.

- `description` = `{"v":1,"endpointId":"fal-ai/nano-banana-2/edit","capability":"image","input":{"prompt":"S3_KEY, <the prompt you sent>","aspect_ratio":"16:9","resolution":"1K"},"referenceField":{"name":"image_urls","multiple":true,"required":true},"videoReferenceField":null}`.
  For a camera board use `openai/gpt-image-2/edit` with
  `"image_size":"landscape_16_9","quality":"high"`. For an image made from text
  alone, use the model's text-to-image endpoint and set `referenceField: null`.
- **Lead the prompt with the asset name** (`S3_KEY, …`) so the regenerated
  image is titled the same and can replace the old one. The app strips the
  prefix before the model sees it.
- **Wire its inputs in the exact `image_urls` order you used**: the image
  being edited first. The director's own photos count, and wiring the
  untitled originals is fine.
- **Rewrite the role lines by title, not number.** The app prepends its own
  `Reference image 1 is S2_KEY.` legend, so drop yours and write the roles as
  "SET_DerelictRoad is the shot to edit; PROP_TapeBoard is only a reference
  for the board". Never write `Image 1`.
- Title it `S3_KEY · Nano Banana 2 Edit`. **Don't convert image cards to
  nodes:** an image node only offers *Open in Fal*. Selecting the card
  already reopens its model screen in the panel with the recipe and wired
  references loaded.
- Same rules as video cards: create each card with its connectors in one
  call, and never send a card back through an update.

**Regenerating a key frame means rewiring.** The new image lands on top of
the old one, which is still wired to the video card. Tell the director to
delete the old one, keep the same title on the new one, and wire the new one
to the video card. Wired references are live, so the node picks it up.

**Build one scene first and ask.** Show the director the first scene's rows
and cards, get a yes, then roll out the rest.

## Step 7 — Verify, then hand over

`canvas_read_as_svg` per scene frame and check, because each maps to something
the app needs:

- every image has a title, so `labelOf` has a name to bind;
- every card's connectors land on the intended references (read the lines'
  `data-start` / `data-end`);
- every card title is `Shot N · <model>` and its description parsed at
  create time (verify one by selecting it in the app; the API reads quotes
  back as `&#34;`, which is normal).
- every generated image has an image card beside it, wired in its
  `image_urls` order.
- **Re-read the board before any rework.** The director converts cards and
  moves nodes between turns, so a card id you remember may now be a node
  somewhere else. Leave nodes, clips and anything else the director made
  where they are, unless asked to move them.

Then report: the board URL, what this pass cost, the film estimate, and **the
director's next steps, in order**:

1. Select a shot's settings card → **Convert to node** in the Fal panel (or
   convert them one by one as you go).
2. Click the node: it shows the model, settings, wired references and prompt.
3. **Generate** on the node (it shows the cost); the clip lands beside the
   node. Regenerate, rewire or re-prompt freely: that's the director's loop.
4. To change a key frame or sheet: select its green image card, edit it in
   the panel and generate. Then delete the old image and wire the new one in
   (see "Regenerating a key frame").
5. Download the clips and cut them together in iMovie.

## Rules worth keeping

- **Ask the pre-flight questions in one message and wait.** Widescreen and
  just-over-a-minute are the defaults; one model for the whole film.
- **The director's words are the brief.** Quote their structure stickies;
  don't replace their story with yours.
- **Use the director's own reference photos before building geometry.** A
  real location photo beats clay for everything except geometry that doesn't
  exist yet.
- **Name references by board title in prompts, never `@Image1`.** The app
  rewrites titles into each model's dialect at whatever position the reference
  really holds.
- **Wire references to cards; don't rely on frame membership** in a scene frame
  that also holds mood images.
- **Every generated image gets an image card; every shot gets a video card.**
  The director owns both loops.
- **The director's scene frames stay theirs.** Shot rows go in the Shots row
  under them.
- **Every reference obeys the model's image rules**, camera boards included.
- **Look at every image before it goes on the board.**
- **Don't generate video, and don't create embeds.** Stage cards; the director
  converts them to nodes and spends the money. The Miro MCP can't make a
  working embed.
