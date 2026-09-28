#!/usr/bin/env bash
# Run the gamepad bridge, creating a private venv with pygame on first use.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${ACTION_PAD_VENV:-$HOME/.cache/action_pad/venv}"
if [ ! -x "$VENV/bin/python" ]; then
  echo "First run: creating $VENV with pygame..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" -q install --upgrade pip pygame
fi
exec "$VENV/bin/python" -u "$HERE/pad_bridge.py"
