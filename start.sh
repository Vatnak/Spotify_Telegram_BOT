#!/bin/bash

echo "Starting Spotify Telegram Bot..."

set -e

# Start callback server in background
python src/callback_server.py &
SERVER_PID=$!

# Give it a second to start
sleep 2

# Start bot (foreground - REQUIRED)
python src/bot.py

# If bot stops, kill server
kill $SERVER_PID