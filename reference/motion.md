# Motion references (greybox clips, mp4)

Only for shots with a rendered greybox move. Read before publishing a clip.

## Two forms of the same clip

The clip exists in two forms because they serve different readers.

**GIF, for the director** — no credentials, works always:

```bash
ffmpeg -v error -y -i SHOT01_move.mp4 \
  -vf "fps=10,scale=420:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=bayer:bayer_scale=3" \
  -loop 0 SHOT01_move.gif
```

~300–500 KB, well inside Miro's 6 MB. Upload as an image **outside** the shot
frame (no `moveToWidget`), titled `S1_MOVE`, with a caption saying what it is.

**mp4, for the model**, no key needed: the fal MCP's
`upload_file(prepare_upload=true, file_name="S1_move.mp4", file_size=<bytes>)`
returns `upload_url` and `file_url`; `curl -X PUT -H 'Content-Type: video/mp4'
--data-binary @S1_move.mp4 '<upload_url>'`, then use `file_url` (verified
2026-09-28). `scripts/fal_upload.sh` does the same with a `FAL_KEY` from the
environment, for use outside a Claude session. **Do not create the embed through the MCP.**
Verified 2026-09-25: an embed authored with `canvas_create_from_svg` or
`canvas_update_from_svg` (`data-type="custom-widget" data-widget-type="embed"`)
reads back through the MCP with the `data-url` you gave it, but the Web SDK sees
`url: ""` and `previewUrl: …/generic-preview.svg`. An inline embed with an empty
URL frames `https://miro.com/`, so the tile shows the board inside itself. The
app's `classifyEmbeds` reads that same empty `url`, so the item is not a video
reference either. `url` is read-only in the SDK, so the app cannot repair it
afterwards. Poster attributes (`data-preview-url`, `data-previewUrl`,
`data-poster`) are rejected as unsupported.

Instead, put the public mp4 URL on the board as text and let the director turn
it into an embed through the app's **Add Video from URL** tile (home screen), which creates a
real embed with a working URL:

- a sticky or caption titled `S1_MOVE` whose body is the fal URL, placed where
  the embed should go (top-left of the frame, 440 × 248);
- the GIF preview beside it, titled `S1_MOVE_PREVIEW`.

Say in the caption that one click in the app turns it into the video reference.

When you publish the mp4, rename the GIF to `S1_MOVE_PREVIEW` so one title
means one thing.


