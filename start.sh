#!/bin/bash

echo "Starting Spotify Telegram Bot..."

# Run callback server in background
python src/callback_server.py &

# Run main bot
python src/bot.py