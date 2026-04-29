import requests
from auth import get_valid_token

def get_now_playing(telegram_id: str) -> str:
    token = get_valid_token(telegram_id)

    if not token:
        return "You're not logged in. Use /login first"
    
    response = requests.get(
        "https://api.spotify.com/v1/me/player/currently-playing",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 204:
        return "Nothing is playing right now."
    
    if response.status_code != 200:
        return f"❌ Error fetching current track: {response.status_code}"
    
    data = response.json()
    
    if not data or data.get("item") is None:
        return "Nothing is playing right now."
    
    song = data["item"].get("name", "Unknown")
    artists = data["item"].get("artists", [])
    artist = artists[0]["name"] if artists else "Unknown Artist"
    return f"🎵 {song} - {artist}"

def pause(telegram_id: str) -> str:
    token = get_valid_token(telegram_id)

    if not token:
        return "You're not logged in. Use /login first"
    
    response = requests.put(
        "https://api.spotify.com/v1/me/player/pause",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return "⏸ Paused successfully"
    elif response.status_code == 404:
        return "No active device found. Open Spotify on any device first."
    elif response.status_code == 403:
        return "❌ Spotify Premium required for playback control."
    elif response.status_code == 409:
        return "Nothing is playing right now."
    else:
        return f"❌ Error pausing playback: {response.status_code}"

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
    track_uri = track["uri"]               
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

def resume(telegram_id: str) -> str:
    token = get_valid_token(telegram_id)

    if not token:
        return "You're not logged in. Use /login first"
    
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.put(
        "https://api.spotify.com/v1/me/player/resume",
        headers=headers
    )

    if response.status_code == 200:
        return "▶️ Resumed playback"
    elif response.status_code == 404:
        return "No active device found. Open Spotify on any device first."
    elif response.status_code == 403:
        return "❌ Spotify Premium required for playback control."
    else:
        return f"❌ Error resuming playback: {response.status_code}"

def add_queue(telegram_id: str, track_name: str) -> str:
    token = get_valid_token(telegram_id)

    if not token:
        return "Please log in first. Use /login"

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

    result = search_response.json()
    items = result["tracks"]["items"]

    if not items:
        return f"❌ No track found for: {track_name}"

    track = items[0]
    track_uri = track["uri"]
    track_display = track["name"]
    artist = track["artists"][0]["name"] if track["artists"] else "Unknown Artist"

    # Step 2: Add to queue
    queue_response = requests.post(
        "https://api.spotify.com/v1/me/player/queue",
        headers=headers,
        params={"uri": track_uri}
    )

    if queue_response.status_code == 204:
        return f"✅ Added to queue: {track_display} by {artist}"
    elif queue_response.status_code == 401:
        return "Token expired. Please /login again."
    elif queue_response.status_code == 403:
        return "❌ This requires Spotify Premium."
    elif queue_response.status_code == 404:
        return "No active device found. Open Spotify on a device first."
    else:
        return f"❌ Failed to add to queue. Status: {queue_response.status_code}"