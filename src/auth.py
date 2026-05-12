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
USERS_FILE = Path(__file__).parent.parent / "data" / "user.json"

def load_users():
    if not os.path.exists(str(USERS_FILE)):
        return {}
    with open(str(USERS_FILE), "r") as f:
        content = f.read().strip()
        if not content:  
            return {}
        return json.loads(content)


def save_users(users):
    os.makedirs(str(USERS_FILE.parent), exist_ok=True)
    with open(str(USERS_FILE), "w") as f:
        json.dump(users, f, indent=2)


def get_selected_device(telegram_id: str) -> str | None:
    users = load_users()
    if telegram_id not in users:
        return None
    return users[telegram_id].get("selected_device_id")


def set_selected_device(telegram_id: str, device_id: str):
    users = load_users()
    if telegram_id not in users:
        return
    users[telegram_id]["selected_device_id"] = device_id
    save_users(users)


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
    try:
        data = response.json()
    except json.JSONDecodeError:
        raise ValueError(f"Spotify token error (HTTP {response.status_code}).") from None
    if not response.ok:
        msg = data.get("error_description") or data.get("error") or response.text
        raise ValueError(msg)
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    expires_in = data.get("expires_in")
    if not access_token or not refresh_token or expires_in is None:
        raise ValueError("Invalid token response from Spotify (missing fields).")
    users = load_users()
    users[telegram_id] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": int(time.time()) + int(expires_in),
    }
    save_users(users)


def refresh_access_token(telegram_id: str) -> bool:
    users = load_users()
    if telegram_id not in users:
        return False
    refresh_token = users[telegram_id].get("refresh_token")
    if not refresh_token:
        return False
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
    )
    try:
        data = response.json()
    except json.JSONDecodeError:
        return False
    if not response.ok:
        return False
    access_token = data.get("access_token")
    if not access_token:
        return False
    users[telegram_id]["access_token"] = access_token
    users[telegram_id]["expires_at"] = int(time.time()) + int(data.get("expires_in", 3600))
    if data.get("refresh_token"):
        users[telegram_id]["refresh_token"] = data["refresh_token"]
    save_users(users)
    return True


def get_valid_token(telegram_id: str) -> str | None:
    users = load_users()
    if telegram_id not in users:
        return None
    expires_at = users[telegram_id].get("expires_at", 0)
    if time.time() >= expires_at - 60:
        if not refresh_access_token(telegram_id):
            return None
        users = load_users()
        if telegram_id not in users:
            return None
    return users[telegram_id].get("access_token")

def logout(telegram_id: str):
    users = load_users()
    if telegram_id in users:
        del users[telegram_id]
        save_users(users)