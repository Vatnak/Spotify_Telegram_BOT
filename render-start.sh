#!/usr/bin/env bash
# Single Render Web service: Telegram bot (polling) + Spotify OAuth callback (HTTP).
# Both share one filesystem so SQLite in DATA_DIR (or ./data) stays consistent.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"

python src/bot.py &
BOT_PID=$!

term_handler() {
  kill -TERM "${BOT_PID:-}" 2>/dev/null || true
  kill -TERM "${GUNICORN_PID:-}" 2>/dev/null || true
}
trap term_handler SIGTERM SIGINT

PORT="${PORT:-8000}"
python -m gunicorn --chdir src callback_server:app \
  --bind "0.0.0.0:${PORT}" \
  --workers 1 \
  --threads 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - &
GUNICORN_PID=$!

wait "${GUNICORN_PID}"
status=$?
kill -TERM "${BOT_PID}" 2>/dev/null || true
wait "${BOT_PID}" 2>/dev/null || true
exit "${status}"
