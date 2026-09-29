# The Fal-for-Miro board contract

What the app actually reads off a board. Everything here was read out of
`~/platform-architect2026/fal-miro` and confirmed live on a board on
2026-09-12. Re-check it if the app has moved on — the citations are there so
you can.

> **`ARCHITECTURE.md` is stale on one point.** It says references are ordered
> by "first mention of their board title in the prompt". That behaviour was
> removed. `shared/referenceBinding.ts` explains why: a reference titled
> "texture" jumped to position 1 the moment a prompt said "granite texture",
> silently overriding the order the user had set. Baskets replaced it. Trust
> the code, not the doc.

## Prompts

- **A prompt is a sticky note.** The director selects a sticky, and the app
  sends its text.
- **The leading token names the asset.** `shared/assetNaming.ts`,
  `DEFAULT_ASSET_NAMING`: `^\s*([A-Za-z0-9][\w-]*)\s*,`. So
  `S1_KEY, a wide shot…` titles the generated image `S1_KEY`. `[\w-]*`
  includes underscores and hyphens, so `S1_KEY` and `SHOT-01` both survive
  intact.
- **The id is stripped before the model sees it** (`stripAssetName`), and only
  when it sits at the very start. Write `S1_KEY, <prompt>` and the model
  receives `<prompt>`.
- The pattern is per-board configurable, so do not hard-code a different
  scheme and assume it works.

## References are baskets, not connectors

`panel/hooks/basket.ts`. A basket is an ordered list the director builds by
hand. Order is load-bearing — the models take a flat `image_urls` array, so
position *is* the meaning, and the rows are drag-reorderable.

Four ways to fill one:

| Action | What it takes |
|---|---|
| `addSelection` | whatever is selected on the board |
| `addFromConnectors` | one selected anchor **plus everything wired to it** |
| `addFromFrame` | everything of that kind inside the selected frame |
| `addUrl` | a pasted URL with no board item behind it |

**`addFromFrame` is the one to design for.** It calls
`miro.board.get({ type })` and filters on `parentId === frameId`, appending in
the order the query returns — which is creation order. Verified live: two
images created into a frame came back `[S1_BLOCK, S1_KEY]`, the order they were
made in. So **create a shot's references in the order you want them numbered**
and the director gets a correct basket from one click.

`getCommonFrameParent` in `shared/boardHelpers.ts` shows the app already
blesses this shape — it calls a frame holding a prompt and its references a
"prompt frame", and uses membership instead of drawing a connector per
reference.

## Names come from titles

`panel/hooks/boardSelection.ts:60`, `labelOf`: a sticky's label is its
(HTML-stripped) content; **everything else uses `title`**. An untitled image
is an unnamed reference, so always set `title` on an image you create.

## How a prompt binds to its references

`shared/referenceBinding.ts`:

- **Default** — prepends a legend: `Reference image 1 is S1_BLOCK.` The prompt
  itself is untouched.
- **Kling** — rewrites each reference's title in the prompt to `@Image{n}`.
- **OmniGen v1** — same, as `<|image_{n}|>`.
- **Single-input models** take basket item 1 and nothing else.
- **Seedance** (`bindSeedanceReferences`) rewrites titles to `@Image1` /
  `@Video1` / `@Audio1` by basket position, per modality — unless the prompt
  already contains explicit `@`-tokens, in which case it is left alone.

### The rule this implies

**Write prompts that name references by their board title, never as
`@Image1`.** A title is rewritten to whatever position the reference actually
occupies, so the prompt stays correct even if the director reorders the
basket. A hard-coded `@Image1` is a promise about ordering that you are not in
a position to make — and it suppresses the rewrite entirely.

### Caps

- Seedance 2.0 reference-to-video: **9 images + 3 videos** (≤12 total).
- Veo 3.1 reference-to-video: **3 images**, blended, no video refs, and it
  blocks identifiable people.

The 3-video slot is why a Blender playblast is worth rendering at all: it
rides along as a genuine motion reference rather than a description of one.

## Reference dialects (changed by PR #38)

The app used to send every reference-to-video model Seedance's field names
(`image_urls` / `video_urls` / `audio_urls`) and `@Image1` tokens. That silently
broke every model using `reference_image_urls` — MiniMax H3, H3 Max, Wan 3.x,
Grok — which received no references and failed from the queue.

Since PR #38 the field names are read off the model's schema
(`pickReferenceField` and siblings) and the prompt is adapted per dialect via
`videoReferenceDialect` in `shared/referenceBinding.ts`. Six dialects exist:
`@Image1` (Seedance, Kling), `Image 1` (MiniMax, Wan), `character1` (Happy
Horse), `<IMAGE_0>` zero-indexed (Grok), list-order-only (Veo, Gemini Omni),
and a neutral legend for anything unclassified.

**What this means for a storyboard:** name the endpoint in the route and write
prompts that name references **by board title**. The app rewrites a title into
whatever token that model actually wants, so one prompt works across all of
them. Hardcoding `@Image1` breaks on four of the eleven.

Verify a model still accepts your subject before recommending it: Seedance 2.0
refuses photoreal human references, and Seedance 2.5 currently refuses every
reference image on this account.

## Video references are embeds

`panel/hooks/basket.ts:274` `classifyEmbeds` keeps an item only if
`type === 'embed'` and `unwrapVideoEmbedUrl(url)` returns something.

`lib/api.ts:398`:

```js
const u = new URL(embedUrl, window.location.origin);
if (!u.pathname.endsWith('/embed-video.html')) return null;
return u.searchParams.get('url');
```

So a video reference is an **embed item whose URL path ends
`/embed-video.html` and carries `?url=<the real video>`**. `window.location.origin`
is only a base for relative URLs — **the host is never checked**. A
Claude-authored embed therefore classifies as a video reference no matter which
origin you point it at; getting the origin wrong only breaks playback of the
little player on the board, not the reference itself.

Miro cannot host video, which is why the mp4 has to live somewhere public
(`fal_upload.sh`).

## Embeds: the base URL, the cache-buster, and the poster

**Base URL** (Sean's deployment, confirmed 200 on 2026-09-16):
`https://charliewinters.github.io/fal-miro/` — a GitHub Pages project site, so
everything lives under a subpath and the origin root 404s. The app derives this
at runtime (`window.location.origin + import.meta.env.BASE_URL`), so it only
has to be known when authoring embeds from outside the app. Read it off an
existing embed's `data-url` rather than guessing; four wasted console round
trips went into guessing it.

**Always append a unique `&cb=`.** Miro resolves an embed URL once and caches
the result against that exact URL. A first resolution that fails is cached as a
failure — grey placeholder, no error, no retry, and re-creating the item at the
same URL changes nothing. `embedPageUrl` in `lib/api.ts` documents the live
case: two rig embeds stuck while an identical 3D embed rendered, and a fresh
`cb` fixed both immediately.

**A card with no `previewUrl` shows Miro's own grey placeholder** —
`https://mirostatic.com/partners-embed/preview-images/…`, verified live. An
http(s) `previewUrl` is kept verbatim; a `data:` URI is refused (Miro rehosts
previews via `uploadResourceFromUrl`, which 400s on a data URI). Since PR #48
the app resolves one itself with `fal-ai/ffmpeg-api/extract-frame`
($0.0002/second), but **the canvas DSL exposes no `previewUrl`**, so a
Claude-authored embed cannot set one. Put the animated GIF next to it instead.

**MCP-authored embeds are broken, not just posterless** (verified 2026-09-25,
three fixtures on `uXjVHnxlsEw=`). The MCP accepts
`data-type="custom-widget" data-widget-type="embed" data-url=…` and reads the
URL back, but through the Web SDK the item has `url: ""` and the generic
preview. The empty inline iframe then loads `https://miro.com/` (the console
shows an X-Frame-Options warning for it), so the tile renders the board inside
itself. This happens with both create and update, inside a frame or not.
`classifyEmbeds` also sees the empty `url`, so the item is never a video
reference. `url` is read-only in the SDK, so the app cannot fix one later.
Every embed has to come from the app (`createEmbed`) or the REST API.

## Miro API behaviours worth knowing

Learned the hard way while building; each one cost a wrong result first.

- **An image's `x`/`y` is its CENTRE**, relative to the frame's top-left when
  the URL carries `?moveToWidget=<frameId>`. `image_create`'s description says
  top-left; the API returns `position.origin: "center"`, and the centre is what
  it honours. For a desired top-left `(tx, ty)`:
  `x = tx + w/2`, `y = ty + h/2`, with `h = w × srcH / srcW`.
- **Images made by `image_create` are foreign to the canvas composer.**
  `canvas_update_from_svg` reports `1 updated` for a geometry change and moves
  nothing. Position has to be right at creation time. (`data-deleted="true"`
  does work on them, so a misplaced one can be removed and redone.)
- **To place new items at EXACT coordinates, create them with
  `canvas_update_from_svg`, not `canvas_create_from_svg`.** An element with no
  `data-miro-id` in an update is created, and the update path honours the
  coordinates you give — which is the only way to extend an existing row so it
  lines up with what is already there. `create_from_svg`'s collision-avoidance
  translate makes that impossible.
- **`canvas_create_from_svg` ignores your absolute coordinates.** It wraps the
  whole composition in one `translate(...)` for collision avoidance — a create
  at `y=2320` landed at `y=5672`. Author everything whose *relative* layout
  matters **in a single call**, then read `data-rendered-bounds` for where it
  really went. `canvas_update_from_svg` on a `data-miro-id` does honour exact
  coordinates, so that is the way to place something precisely.
- **A frame resize is validated against where its children are *now*.**
  Shrinking a frame in the same call that moves its children out of the way
  fails with *"child widget cannot be placed outside the bounds of its
  parent"* — the new bounds are checked against the old child positions. Move
  the children in one call, confirm, then resize in a second.
- **Restate a child's geometry with the exact numbers from `result_svg`.** A
  sticky authored at `520x338` reads back as `519x338`; sending `520` again
  updates the content but silently leaves the position untouched. Copy the live
  values verbatim or the move is a no-op that still reports success.
- **To update a widget that lives inside a frame, wrap it in that frame's
  group.** A bare `<textArea data-miro-id=...>` with absolute x/y is rejected:
  *"Attempted to move a widget relative to canvas, while it has a parent"*.
  Send `<g data-miro-id="<frameId>" transform="translate(fx,fy)"
  data-frame="<exact title>">` containing the frame's background rect and the
  child, with the child's coordinates relative to the frame. A bare `<g
  data-miro-id>` with no `data-frame` is ignored with a warning — harmless if
  the children carry their own ids, but it does not scope them.
- **`canvas_update_from_svg` can time out and still have applied.** An
  `upstream request timeout` is not a rollback. Read the item back before
  retrying, or you will double-apply.
- **Do not send HTML tags in a `textArea` body on update.** `<b>x</b>` comes
  back as literal `&lt;b&gt;x&lt;/b&gt;` and displays as text. Markup is fine
  on create; plain text only on update.
- **Miro hosts PNG and GIF up to 6 MB** (`image_get_upload_url`). Its
  `image_get_url` link **is** a usable fal input, but only for **15 minutes**:
  verified 2026-09-25, `Expires` sits 900 s after issue, fal's `upload_file`
  copy was byte-identical to the original, and the same link form past expiry
  returns 403. An expired link as a model input shows up as a generic
  `422 "Could not generate images..."`, which looks like a content refusal and
  is not one. Re-host on fal with `upload_file(url=…)` the moment you get the
  link. The `api.miro.com/v2/…` href from `canvas_read_as_svg` needs auth and
  returns 401 — never pass that one. (Earlier versions of this doc swung both
  ways on this; the 2026-09-14 "always 403" note was most likely an expired
  link.)
- `board_list_items` is deprecated and goes away 2026-09-14 — but it is the
  only tool that reports an image's `title`, `parent` and `position` together,
  which is exactly what verifying this contract needs. Move to
  `canvas_search`/`canvas_read_as_svg` when it goes, and re-verify ordering
  then.

## Blender notes

Moved to the `greybox-shot` skill (`reference/blocking.md`, "Blender notes").

## Settings cards and connectors (the "generation node" pattern)

Read out of `shared/recipeCard.ts` and `panel/screens/ReferenceToVideoScreen.tsx`
on 2026-09-14. The feature is live.

**A settings card is a Miro Card whose `description` is compact recipe JSON:**

```json
{"v":1,"endpointId":"minimax/h3/reference-to-video","capability":"video",
 "input":{"prompt":"…","aspect_ratio":"9:16","resolution":"2K","duration":3},
 "referenceField":null,"videoReferenceField":null}
```

`capability` is one of `image|video|audio|music|segment|model3d|panorama|rig|motion|layers`.
For a reference-to-video model both `*ReferenceField`s are `null` — that screen
owns its own ordered multi-reference list. Selecting the card on the board makes
`HomeScreen` offer to reopen that model screen (`parseRecipeCard`).

**Connected stickies are field overrides, not notes.** `resolveStickyFieldOverrides`
turns a sticky shaped `Label: value` into an override on whichever field's name
or label matches, case- and spacing-insensitively — `Seed: 42`,
`Aspect ratio: 9:16`. A single sticky matching nothing falls back to the
model's primary text field, so a bare prompt sticky still works; prefix it
`Prompt:` to be explicit.

### Authoring connectors through the canvas composer

- **`data-start` / `data-end` only resolve LOCAL ids in the same SVG.** Passing
  a raw `data-miro-id` is silently skipped: *"connector endpoint unresolved"*.
- To wire an **existing** item, include it as a sparse stub carrying both a
  local `id` and its `data-miro-id` (`<image id="i1" data-miro-id="…"
  data-type="image" />`), then reference `i1`. This works even for images made
  by `image_create`, which are otherwise foreign to the composer.
- To wire a **new** card, create the card and its connectors **in the same
  call** — you cannot add connectors to it afterwards without stubbing it, and
  stubbing a card is destructive (below).

### Never send a card back through an update

**Including a Card as a sparse stub in `canvas_update_from_svg` re-encodes its
`description`.** A value stored as `"` comes back as the literal `&#34;`, which
breaks `JSON.parse` in `parseRecipeCard`. Set the description at create time
and never touch that card again — if it needs changing, delete and recreate it
along with its connectors.

Separately, Miro stores a Card description as rich text and HTML-encodes
quotes, so it reads back as `&#34;` through the API even on a healthy card.
That is expected; the Web SDK path the app uses decodes it. Do not try to
"fix" it from the API side, and verify a card by clicking it in the app rather
than by reading it back.

## Nodes: what a settings card becomes (PR #52, 25 Sep 2026)

A **node** is an embed of the app's `node.html?nid=<uuid>` that replaces a
settings card. **Claude cannot make one**: the Miro MCP can't create a working
embed (the SDK sees `url: ""`, reported to Miro). So Claude stages a settings
card exactly as above, and the director converts it in the app:

1. select the card → the panel offers **Convert to node**;
2. the node takes the card's top-left corner and frame, the card's recipe moves
   unchanged into the node's app metadata, the card's connectors are redrawn to
   the node, and the card is deleted;
3. the node shows the model, key settings, wired references, the prompt and the
   last result. **Generate** on the node runs a reference-to-video recipe
   directly; other models get **Open in Fal**, which opens the panel on the node.

What that means for authoring:

- **The card title becomes the node title.** `Shot 2 · MiniMax H3 Reference to
  Video` → `Shot 2` (the part before the first `·`). Title every card
  `<Shot name> · <model label>`.
- **References come from the card's connectors and its frame**, and since #46
  wired references win per modality. A scene frame full of mood-board images
  would all ride along by frame membership, so **wire each shot's chosen
  references to its card with connectors**. Wired images then replace the
  frame's images entirely.
- **Set `aspect_ratio` explicitly in the recipe.** The node and the panel send
  exactly what the recipe says, and MiniMax H3's default `adaptive` takes the
  frame from the references.

## Image settings cards (added 25 Sep 2026)

Read from `panel/screens/ImageGenScreen.tsx` (`onSaveCard`) and
`headless/nodeBridge.ts`. An image recipe is the same card with
`"capability":"image"` and a `referenceField` taken from the schema by
`pickReferenceField`. For `fal-ai/nano-banana-2/edit` that is
`{"name":"image_urls","multiple":true,"required":true}`. Connected images feed
that field in connector order. Only reference-to-video models get **Generate** on a
node (`canGenerate: isReferenceToVideo(model)`). An image node shows only
*Open in Fal*, so leave image cards as cards: selecting one already reopens the
model screen with the recipe loaded. Results place **80 px to the right** of a
card that has connections (`resolvePlaceholderAnchor`, `createImageBelow` with
`side: 'right'`), centred on its y and 720 wide. That is why the Shots row
puts each key frame 80 px right of its image card, and the take lanes 80 px
right of each video card.
