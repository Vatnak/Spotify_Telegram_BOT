#!/usr/bin/env bash
# Local or Render: delegates to Python entrypoint (avoids CRLF / bash quirks on deploy).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
exec python render_entry.py
