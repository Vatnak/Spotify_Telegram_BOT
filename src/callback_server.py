import html
import os

from flask import Flask, request

from auth import exchange_code
from db import init_db

init_db()

app = Flask(__name__)


@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.get("/")
def root():
    return {"service": "spodify-telegram", "health": "/health", "spotify_callback": "/callback"}, 200


@app.route("/callback")
def spotify_callback():
    code = request.args.get("code")
    telegram_id = request.args.get("state")

    if not code or not telegram_id:
        return "<h3>Missing info. Try /login again.</h3>"

    try:
        exchange_code(code, telegram_id)
        return "<h3>✅ Spotify connected! Go back to Telegram.</h3>"
    except Exception as e:
        print("ERROR:", e)
        safe = html.escape(str(e))
        return f"<h3>❌ Error: {safe}</h3>"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
