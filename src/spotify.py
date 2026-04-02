import requests
from auth import get_valid_token

def get_now_playing(telegram_id: str) -> str:
    token = get_valid_token(telegram_id)

    if not token:
        return "You're not logged in, Use /login first"
    
    response = requests.get(
        "https://api.spotify.com/v1/me/player/currently-playing",
        headers= {"Authorization": f"Bearer {token}"}
)  

    if response.status_code == 204:
        return "Nothing is playing right now."
    
    data = response.json()
    song = data["item"]["name"]
    artist = data["item"]["artists"][0]["name"]
    return f"🎵 {song} - {artist}"

def pause(telegram_id: str) -> str:
    token = get_valid_token(telegram_id)

    if not token:
        return "You're not logged in, use /login first"
    
    response = requests.put(
        "https://api.spotify.com/v1/me/player/pause",
        headers = {"Authorization": f"Bearer {token}"}
)
    if response.status_code == 200:
        return "⏸ Paused successfully"
    elif response.status_code == 404:
        return "No active device found — open Spotify on any device first"
    elif response.status_code == 403:
        return "Pause Succesful"
    elif response.status_code == 409:
        return "Nothing is playing right now"
    else:
        return f"Error: {response.status_code}"

def play(telegram_id: str, track_name: str) -> str:
    token = get_valid_token(telegram_id)
    
    if not token:
        return "You're not logged in. Use /login first."
    
    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Search for the track
    search_response = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={
            "q": track_name,
            "type": "track",
            "limit": 1
        }
    )

    if search_response.status_code != 200:
        return f"❌ Search failed: {search_response.status_code}"

    results = search_response.json()
    tracks = results["tracks"]["items"]

    if not tracks:
        return f"❌ No results found for: {track_name}"

    track = tracks[0]
    track_uri = track["uri"]               # e.g. spotify:track:xxxx
    track_title = track["name"]
    artist = track["artists"][0]["name"]

    # Step 2: Play the track
    play_response = requests.put(
        "https://api.spotify.com/v1/me/player/play",
        headers=headers,
        json={"uris": [track_uri]}
    )

    if play_response.status_code == 204:
        return f"▶️ Playing: {track_title} — {artist}"
    elif play_response.status_code == 403:
        return "⚠️ Spotify Premium required for playback control."
    else:
        return f"❌ Playback error {play_response.status_code}: {play_response.text}"
