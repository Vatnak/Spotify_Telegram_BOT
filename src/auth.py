import os
import json
import time
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")


SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
USERS_FILE = "data/user.json"
print("CLIENT ID:", SPOTIFY_CLIENT_ID)
print("REDIRECT:", SPOTIFY_REDIRECT_URI)

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        content = f.read().strip()
        if not content:  
            return {}
        return json.loads(content)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def generate_auth_url(telegram_id: str) -> str:
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
        "state": telegram_id,
    }
    return "https://accounts.spotify.com/authorize?" + urlencode(params)


def exchange_code(code: str, telegram_id: str):
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
        }, 
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    print("Status:", response.status_code)
    print("Raw response:", response.text)
    data = response.json()
    print("Spotify response:", data) 
    users = load_users()
    users[telegram_id] = {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": int(time.time()) + data["expires_in"],
    }
    save_users(users)

def refresh_access_token(telegram_id: str):
    users = load_users()
    refresh_token = users[telegram_id]["refresh_token"]
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
    )
    data = response.json()
    users[telegram_id]["access_token"] = data["access_token"]
    users[telegram_id]["expires_at"] = int(time.time()) + data["expires_in"]
    save_users(users)


def get_valid_token(telegram_id: str) -> str | None:
    users = load_users()
    if telegram_id not in users:
        return None
    if time.time() >= users[telegram_id]["expires_at"] - 60:
        refresh_access_token(telegram_id)
        users = load_users()
    return users[telegram_id]["access_token"]

def logout(telegram_id: str):
    users = load_users()
    if telegram_id in users:
        del users[telegram_id]
        save_users(users)