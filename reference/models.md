# Model routes

## Choosing and pricing

Per shot, choose an **image model** and name the **video model** the director
will use. Use the fal MCP rather than memory: `recommend_model`,
`get_model_schema` (does it even take an image input?), `get_pricing`.

Verified on 2026-09-12:

| Model | Price | Use |
|---|---|---|
| `fal-ai/nano-banana-2/edit` | $0.08/image | shots **with** a greybox — takes `image_urls`, so composition is inherited |
| `fal-ai/flux-2/klein/9b` | $0.006/MP | shots **without** — 13× cheaper, but **no image input at all** |
| `minimax/h3-max/reference-to-video` | — | **default video route.** 9 images + 3 video clips, so a `_MOVE` clip rides along as a real motion reference |
| `alibaba/wan-3.0/reference-to-video` | — | alternative with the same shape (10 images + 5 clips) |
| `fal-ai/kling-video/o3/pro/reference-to-video` | — | images only, no motion-clip slot |

### Do not default to Seedance for anything with a person in it

Verified 2026-09-12, generating the same shot against all eleven flagship
reference-to-video endpoints:

- **`bytedance/seedance-2.0/reference-to-video` refuses photoreal human
  references** under content policy. It accepts a stylised character. So it is
  the wrong default for a storyboard with an actor in it — which is most of
  them. This skill used to recommend it; that was wrong.
- **`bytedance/seedance-2.5/reference-to-video` currently rejects every
  reference image**, including one with no people in it. The message says
  "likenesses of real people"; the real reason is `partner_validation_failed`,
  which is account/platform-side and cannot be worked around in a prompt.
- H3 Max, MiniMax H3, Wan 3.0, Kling O3 Pro, Veo 3.1, Gemini Omni Flash 1.1,
  Grok Imagine 1.5, Happy Horse 1.1 and PixVerse C1 all handled a photoreal
  actor and held his identity.

**Every one of these wants its references in a different field, cited a
different way** — `image_urls` vs `reference_image_urls`, `@Image1` vs
`Image 1` vs `character1` vs `<IMAGE_0>`. Six dialects. Write the route with
the endpoint id, and let the app resolve the rest: it reads the field names off
the schema and adapts the prompt per dialect.

Name a video model **the app actually routes** — anything matching
`/reference-to-video/i` reaches that screen — otherwise the route on the board
is a dead end.

**Total the estimate and show it before spending.** Under about $1, just report
it and proceed. Over that, or if the user's ask sounded exploratory, confirm
first. Pre-generation is one image per shot — variations are the director's
call in the app, not yours.

## One model for the whole film

Recommend one video model for every clip in the film, and say why in
pre-flight. Mixing models across cuts shows: grain, colour response, motion
cadence and how faces are drawn all change at the cut. Switch a single shot only
for a reason the director agrees to, such as a model that refuses its reference.

## What each model accepts, and the traps

Read these from `get_model_schema`, not from memory. What has bitten so far:

- **MiniMax H3** (`minimax/h3/reference-to-video`, `minimax/h3-max/reference-to-video`):
  `reference_image_urls` up to 9, `reference_video_urls` up to 3,
  `reference_audio_urls` up to 3. Every reference image must be **between 0.4
  and 2.5 in aspect ratio and at least 256 × 256**. That applies to *every*
  reference, not just a start frame, so a long camera strip or a tiny crop fails
  the whole request. `aspect_ratio` defaults to `adaptive`, which takes the
  frame from the references. Always set it explicitly (16:9 for the festival),
  or a landscape plate turns a portrait shot landscape.
- **Veo 3.1**: `duration` is a string, `"8s"`, not a number.
- **Seedance**: see the warning above. It stays in the app's model list, but
  don't recommend it for a film with people in it.

## Planning clip lengths

Each model allows a fixed set of durations. Read `duration` from the schema:
its `enum`, or its `minimum` and `maximum`. Plan every scene in clips of an allowed
length. A 70-second film on a model that allows 6 or 10 seconds is, for
example, seven 10-second clips or a mix. State the arithmetic in the plan so
the director can see where the time goes. Leave a little spare, because a cut
usually trims both ends of a clip.
