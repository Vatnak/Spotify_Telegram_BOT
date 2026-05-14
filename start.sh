#!/usr/bin/env bash
# Local dev: Spotify callback + Telegram bot (same machine = one SQLite DB).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"

PORT="${PORT:-8000}"
python src/callback_server.py &
SERVER_PID=$!

sleep 2
python src/bot.py
kill "${SERVER_PID}" 2>/dev/null || true
