#!/usr/bin/env bash
# Used by Render if Start Command is `bash start.sh`.
# Delegates to render_entry.py: Gunicorn on $PORT + Telegram bot (shared SQLite).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
exec python render_entry.py
