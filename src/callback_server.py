from flask import Flask, request
from auth import exchange_code

app = Flask(__name__)

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
        print("ERORR:", e)
        return f"<h3>❌ Error: {e}</h3>"

if __name__ == "__main__":
    app.run(port=8000)