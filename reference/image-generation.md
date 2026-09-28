# Image generation: references, first pass, camera boards

The verified rules behind the skill's first pass. Read before generating.

## A real reference photo beats a greybox you invented

If the user has already dropped reference images on the board — a location
photo, a product shot, a framing they like — **condition on those instead**.
They carry true perspective, true proportion and set dressing that no clay
render has, and `nano-banana-2/edit` takes several `image_urls` at once, so a
location photo and a product photo can drive the same frame. Reach for Blender
only for geometry that exists nowhere yet.

## The reference library

Once a director has seen a first pass and wants video, the next thing they need
is **one reference per element**, not more shot frames. Generate these as their
own frames, each with a caption sticky saying where it is used:

| Kind | What it is | Aspect |
|---|---|---|
| `CHAR_*_SHEET` | turnaround — front, three-quarter, side, back at matched scale, plus head studies and **accessory insets** for anything the character always carries | 16:9 |
| `CHAR_CREW_SHEET` | supporting cast in one line-up, deliberately given different silhouettes, builds and hair so they read apart in motion | 16:9 |
| `PROP_*` | multi-angle turnaround on a plain grey field, one object per sheet | 4:3 |
| `SET_*` | **clean empty plate, no characters** — so anyone can be placed into it | 16:9, or 21:9 for a vista |

Three things that make these work:

- **Say "no people" explicitly on set plates**, or you get the shot back again
  instead of a plate.
- **Ask for the model-sheet layout by name** ("the same character drawn four
  times in a row at identical height and scale, neutral A-pose") — the models
  do this well and it is far more useful than four separate images.
- **Build the character sheet from an approved shot frame**, not from text, and
  build everything else from the sheet. That is what keeps a face consistent
  across a cut.

Put the library in its own labelled band on the board, one frame per reference.
`addFromFrame` then pulls exactly one asset, and the director composes baskets
from named parts instead of hunting through shot frames.

## Camera-movement boards

For any shot with more than one camera action, a single still cannot express
the move. Generate a **three-panel camera strip** with
`openai/gpt-image-2/edit`, conditioned on that shot's `_KEY`:

- three 9:16 panels in a row on an off-white sheet, labelled `0.0s`, mid, end
- a bold header naming the shot, its duration and the move
- move arrows across the panels, and a **small side-elevation or plan-view
  camera path diagram** in a corner

GPT Image 2 is the right tool here specifically because it renders **clean,
correctly spelled typography** — timecodes and labels come out legible, which
is the whole point of a camera plan. Ask for it plainly and it obliges.

**It costs $1 per image**, roughly 12× nano-banana, so restrict it to shots
that genuinely move and say so in the estimate. Three boards is usually the
whole film.

## Conditioning on board images, and the first pass

For a shot **with** a greybox, condition on it — this is the entire payoff of
the Blender leg:

1. `image_get_url` on the item → a signed `r.miro.com` URL, **good for 15 minutes**
2. **Immediately** `upload_file(url=…)` it to fal → a durable fal CDN URL
3. `run_model` on `fal-ai/nano-banana-2/edit` with that fal URL in `image_urls`

> **Miro signed URLs work as fal inputs — for 15 minutes.** Verified
> 2026-09-25: `image_get_url` returned an `r.miro.com` link with
> `Expires` set **900 s** after issue; `upload_file(url=…)` on it produced a
> fal copy that was byte-identical to the original (same PNG, 768×1376,
> 2,088,525 bytes). The same link form past its expiry returns **403**.
>
> An earlier version of this doc said these URLs never work, from a 2026-09-14
> test where fal got 403 on a link `curl` had just fetched. Expiry is the most
> likely explanation, since model queues can fetch inputs well after
> submission, but it was not proven. So do not rely on the signed URL
> surviving: **re-host it on fal the moment you get it** (step 2 above), and
> pass the fal URL — which does not expire — to anything that may run later.
>
> Two traps that look the same from the outside:
> - an expired signed URL as a model input surfaces as a generic
>   `422 "Could not generate images with the given prompts and images"`,
>   which reads like a content refusal. It is not the prompt.
> - the `href` that `canvas_read_as_svg` shows is an `api.miro.com/v2/…` URL;
>   it needs auth and returns **401** to fal. Only `image_get_url`'s
>   `download_url` is fetchable.
>
> **Do not base64 references through context** to work around any of this —
> it pushes the whole payload through the conversation.

**Mirror the app's own binding** so the director can reproduce the result
in-app: prepend the default legend exactly as `bindReferences` does —
`Reference image 1 is S1_BLOCK.` — then the prompt with its asset-id prefix
stripped. Tell the model plainly to treat the reference as geometry: *"Use it
as the exact camera geometry: match its camera height, the convergence and
spacing of the rows, and the horizon line precisely."*

For a shot conditioned on **the user's own reference photos**, the same three
calls work — `image_get_url` each one, pass them all in `image_urls`, and name
each in the legend by its board title so the director can rebuild the basket
in-app. Tell the model what each reference is *for*: "hold the architecture and
the vegetation from the street photo; take the chassis and wheel proportion
from the deck photo."

**Reference order is not neutral — the FIRST `image_urls` entry dominates.**
Conditioning a crest shot on a speed shot with the speed shot listed first
returned a near-copy of the speed shot instead of an edit of the crest. When
you are editing one image and merely *consulting* another, put the image being
edited first and label the roles in words: *"Image 1 is the shot to edit. Image
2 is ONLY a reference for how the riders should look."* Then enumerate the
changes as a short numbered list and say "everything else identical".

**Conditioning images leak their effects.** That same speed reference dragged a
glowing motion trail into a shot where everyone was standing still. If a
reference carries a look you do not want — motion blur, a glow, a time of day —
name it and negate it explicitly: *"there is no speed trail and nothing is
glowing; they are only just pushing off."* A generic "match the style" will not
suppress it.

**Chain shots that need character consistency.** Once shot 2's `_KEY` exists,
condition shots 4 and 5 on it. The protagonist then survives the cut at no
extra cost, which text prompting alone will not give you.

For a shot with **no reference at all**, `fal-ai/flux-2/klein/9b` on the prompt
alone.

Then `image_create` with `image_url` (the fal URL), `title: S1_KEY`, and
centre coordinates. Miro copies the bytes at creation, so fal's URL expiring
later does not matter.
