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
    if response.status_code == 204 :
        return "Nothing is playing rightnow"
    elif response.status_code == 200:
        return "Pause Successful"
    elif response.status_code == 403:
        "No active device"
    else:
        return f"Error: {response.status_code}"




    



