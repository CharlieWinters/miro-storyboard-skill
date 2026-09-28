#!/usr/bin/env bash
# Upload a local file to fal's CDN and print the resulting public URL.
#
#   FAL_KEY=... fal_upload.sh SHOT01_move.mp4 [content-type]
#
# Only needed for MOTION CLIPS. A greybox still goes to Miro's own image
# storage (image_get_upload_url), which needs no key at all — so the still
# half of this skill works with no credentials. An mp4 cannot be hosted by
# Miro, and both the board embed and fal's `video_urls` need a fetchable URL,
# so the clip has to live somewhere public. fal's own CDN is the least
# surprising place: it is where every other asset in this pipeline already
# lives, and the key is the user's own.
#
# The key is read from the environment and passed to curl through a --config
# file on stdin, never as an argument — an `-H "Authorization: Key $FAL_KEY"`
# would put it in argv, where `ps` can read it. It is never echoed, written to
# a file, or logged.
set -euo pipefail

FILE="${1:?usage: fal_upload.sh <file> [content-type]}"
[ -f "$FILE" ] || { echo "no such file: $FILE" >&2; exit 1; }

if [ -z "${FAL_KEY:-}" ]; then
  cat >&2 <<'MSG'
FAL_KEY is not set, so the motion clip cannot be uploaded.

Re-run the storyboard skill with the key exported for that one command, e.g.
  FAL_KEY=<your fal key> claude ...
or export it in your shell before starting the session. Get a key at
https://fal.ai/dashboard/keys

Nothing else in the skill needs it: greybox stills are hosted by Miro, and
generation runs through the fal MCP server, which holds its own key.
MSG
  exit 3
fi

NAME="$(basename "$FILE")"
TYPE="${2:-}"
if [ -z "$TYPE" ]; then
  case "$NAME" in
    *.mp4) TYPE="video/mp4" ;;
    *.webm) TYPE="video/webm" ;;
    *.mov) TYPE="video/quicktime" ;;
    *.png) TYPE="image/png" ;;
    *.jpg|*.jpeg) TYPE="image/jpeg" ;;
    *) TYPE="application/octet-stream" ;;
  esac
fi

# 1. Ask fal where to put it. The key goes in via stdin config, not argv.
INITIATE_BODY=$(printf '{"file_name":%s,"content_type":%s}' \
  "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$NAME")" \
  "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$TYPE")")

INITIATE=$(printf 'header = "Authorization: Key %s"\nheader = "Content-Type: application/json"\n' "$FAL_KEY" \
  | curl -sS --config - -X POST \
      --data-binary "$INITIATE_BODY" \
      "https://rest.alpha.fal.ai/storage/upload/initiate")

read -r UPLOAD_URL FILE_URL <<EOF
$(python3 - "$INITIATE" <<'PY'
import json, sys
try:
    d = json.loads(sys.argv[1])
except Exception:
    sys.stderr.write("fal did not return JSON from upload/initiate:\n" + sys.argv[1][:500] + "\n")
    sys.exit(4)
u, f = d.get("upload_url"), d.get("file_url")
if not u or not f:
    # Most often a rejected key. Print fal's own message, never the key.
    sys.stderr.write("fal upload/initiate gave no upload_url — response was:\n" + json.dumps(d)[:500] + "\n")
    sys.exit(4)
print(u, f)
PY
)
EOF

# 2. Put the bytes. The upload URL is pre-signed, so no auth header here.
curl -sS -X PUT -H "Content-Type: $TYPE" --data-binary "@$FILE" "$UPLOAD_URL" >/dev/null

# 3. The only thing on stdout is the public URL, so a caller can capture it.
echo "$FILE_URL"
