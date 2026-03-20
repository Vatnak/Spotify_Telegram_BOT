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




    



