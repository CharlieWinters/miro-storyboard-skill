#!/usr/bin/env bash
# Open a puppet shot in Blender with Action Pad loaded (no add-on install needed).
#   open_action_pad.sh <shot.blend>
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
exec "$BLENDER" "${1:?usage: open_action_pad.sh <shot.blend>}" --python "$HERE/__init__.py"
