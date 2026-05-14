import json
import logging
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


def _is_local_redirect(url: str) -> bool:
    u = url.lower()
    return "127.0.0.1" in u or "localhost" in u


def _normalize_spotify_redirect_uri(url: str) -> str:
    """Spotify compares redirect_uri byte-for-byte with Dashboard entries."""
    u = (url or "").strip()
    while u.endswith("/"):
        u = u[:-1]
    # Production callbacks should use https (Spotify may reject http on cloud URLs).
    if u.startswith("http://") and not _is_local_redirect(u):
        u = "https://" + u[len("http://") :]
    return u


def _resolve_spotify_redirect_uri() -> str | None:
    """
    Spotify must redirect to a URL that actually runs this app's /callback.

    On Render, prefer the live service URL (RENDER_EXTERNAL_URL) when SPOTIFY_REDIRECT_URI
    is localhost or points at a different host than this deployment — otherwise Spotify
    returns "redirect_uri: Not matching configuration" if the env is stale.
    """
    explicit = (os.getenv("SPOTIFY_REDIRECT_URI") or "").strip()
    on_render = os.getenv("RENDER", "").lower() == "true"
    render_base = (os.getenv("RENDER_EXTERNAL_URL") or "").strip().rstrip("/")
    public_base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    log = logging.getLogger(__name__)

    if public_base:
        return _normalize_spotify_redirect_uri(f"{public_base}/callback")

    if on_render and render_base:
        canonical = _normalize_spotify_redirect_uri(f"{render_base}/callback")
        if not explicit or _is_local_redirect(explicit):
            return canonical
        ex_norm = _normalize_spotify_redirect_uri(explicit)
        if ex_norm != canonical:
            log.warning(
                "SPOTIFY_REDIRECT_URI (%r) does not match this service (%r); using the Render URL for OAuth.",
                ex_norm,
                canonical,
            )
        return canonical

    if explicit and not (on_render and _is_local_redirect(explicit)):
        return _normalize_spotify_redirect_uri(explicit)

    return _normalize_spotify_redirect_uri(explicit) if explicit else None


SPOTIFY_REDIRECT_URI = _resolve_spotify_redirect_uri()
SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

_redirect_uri_logged = False


def get_selected_device(telegram_id: str) -> str | None:
    user = get_user(telegram_id)
    if not user:
        return None
    return user.get("selected_device_id")


def set_selected_device(telegram_id: str, device_id: str):
    update_selected_device(telegram_id, device_id)


def generate_auth_url(telegram_id: str) -> str:
    global _redirect_uri_logged
    if not SPOTIFY_CLIENT_ID:
        raise ValueError("Missing SPOTIFY_CLIENT_ID in environment.")
    if not SPOTIFY_REDIRECT_URI:
        raise ValueError(
            "Spotify redirect URI is not set. On Render, set SPOTIFY_REDIRECT_URI to "
            "https://<your-service>.onrender.com/callback (and add the same URL in the Spotify "
            "Developer Dashboard), or rely on RENDER_EXTERNAL_URL when SPOTIFY_REDIRECT_URI "
            "is localhost."
        )
    if not _redirect_uri_logged:
        logging.getLogger(__name__).warning(
            "Spotify OAuth redirect_uri=%r — add this EXACT string to Spotify Dashboard → "
            "Redirect URIs and click Save.",
            SPOTIFY_REDIRECT_URI,
        )
        _redirect_uri_logged = True
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

    if not SPOTIFY_REDIRECT_URI:
        raise ValueError(
            "Spotify redirect URI is not configured; token exchange cannot complete. "
            "Set SPOTIFY_REDIRECT_URI to your public /callback URL (same value used in login)."
        )

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
