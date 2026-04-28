# 🎵 Spodify Telegram Bot

A Side_Project made by a sophomore student bachelor in Artificial Intelligence - Telegram bot that lets you control Spotify playback directly from your Telegram chat — search, play, pause, resume, and queue tracks without leaving the app.

---

## Features

- **Play** any song by name
- **Pause** current playback
- **Resume** paused playback
- **Queue** a track to play next
- **Now Playing** — see what's currently on
- Spotify OAuth 2.0 login flow built in

---

## Tech Stack

- **Python** — core language
- **python-telegram-bot** — Telegram bot framework
- **Spotipy / Requests** — Spotify Web API calls
- **Flask** — OAuth callback server
- **Spotify Web API** — playback control & search

---

## Project Structure

```
Spodify_Telegram_BOT/
├── bot.py              # Telegram bot entry point & command handlers
├── auth.py             # OAuth 2.0 login flow & token management
├── spotify.py          # Spotify API functions (play, pause, resume, queue)
├── .env                # Environment variables (not committed)
├── .gitignore
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Vatnak/Spodify_Telegram_BOT.git
cd Spodify_Telegram_BOT
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:5000/callback
```

- Get your Telegram bot token from [@BotFather](https://t.me/BotFather)
- Get your Spotify credentials from the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

### 4. Run the bot

```bash
python bot.py
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and get a welcome message |
| `/help` | Show all available commands |
| `/login` | Connect your Spotify account via OAuth |
| `/logout` | Disconnect your Spotify account |
| `/play <song name>` | Search and play a track immediately |
| `/Pause` | Pause current playback |
| `/resume` | Resume paused playback |
| `/add <song name>` | Add a track to the queue |
| `/nowplaying` | Show the currently playing track |
| `/stop` | Stop the bot |

---

## Requirements

- Python 3.10+
- A **Spotify Premium** account (required for playback control)
- An active Spotify device (desktop, mobile, or web player)

---

## Notes

- Playback control endpoints require Spotify Premium — free accounts will get a `403` error.
- Make sure Spotify is open on at least one device before using `/play` or `/resume`.
- Tokens are stored per Telegram user ID and refreshed automatically.

---

## Author

**Nakscott** — [@Vatnak](https://github.com/Vatnak)
