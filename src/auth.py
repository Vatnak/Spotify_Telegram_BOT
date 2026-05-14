import json
import os
import time
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from pathlib import Path

from db import delete_user, get_user, save_user, update_selected_device

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"


def get_selected_device(telegram_id: str) -> str | None:
    user = get_user(telegram_id)
    if not user:
        return None
    return user.get("selected_device_id")


def set_selected_device(telegram_id: str, device_id: str):
    update_selected_device(telegram_id, device_id)


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
    try:
        int(telegram_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid login session. Use /login from Telegram again.") from None

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
        },
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
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
    expires_at = int(time.time()) + int(expires_in)
    save_user(telegram_id, access_token, refresh_token, expires_at)


def refresh_access_token(telegram_id: str) -> bool:
    user = get_user(telegram_id)
    if not user:
        return False
    refresh_token = user.get("refresh_token")
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
    new_refresh = data.get("refresh_token") or refresh_token
    expires_at = int(time.time()) + int(data.get("expires_in", 3600))
    save_user(telegram_id, access_token, new_refresh, expires_at)
    return True


def get_valid_token(telegram_id: str) -> str | None:
    user = get_user(telegram_id)
    if not user:
        return None
    expires_at = user.get("expires_at") or 0
    if time.time() >= expires_at - 60:
        if not refresh_access_token(telegram_id):
            return None
        user = get_user(telegram_id)
        if not user:
            return None
    return user.get("access_token")


def logout(telegram_id: str):
    delete_user(telegram_id)
