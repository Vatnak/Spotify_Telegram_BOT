import time
import requests
from auth import get_valid_token, get_selected_device, set_selected_device

def get_available_devices(telegram_id: str) -> list:
    """Get list of available Spotify devices"""
    token = get_valid_token(telegram_id)
    if not token:
        return []
    
    response = requests.get(
        "https://api.spotify.com/v1/me/player/devices",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        devices = response.json().get("devices", [])
        return devices
    return []


def get_devices(telegram_id: str) -> str:
    token = get_valid_token(telegram_id)
    if not token:
        return "You're not logged in. Use /login first."

    devices = get_available_devices(telegram_id)
    if not devices:
        return "No Spotify devices found. Open Spotify on your phone or PC."

    lines = []
    for index, device in enumerate(devices, start=1):
        status = "✅ Active" if device.get("is_active") else "❌ Inactive"
        name = device.get("name", "Unknown")
        device_type = device.get("type", "Unknown")
        device_id = device.get("id", "Unknown")
        lines.append(
            f"{index}. {name} ({device_type}) — {status}\nID: `{device_id}`"
        )

    selected_device_id = get_selected_device(telegram_id)
    if selected_device_id:
        lines.append(f"\nSelected device ID: `{selected_device_id}`")

    if not any(d.get("is_active") for d in devices):
        lines.append(
            "\nTip: if Play or Queue fails, open Spotify on that device and start any song once, "
            "then try the bot again."
        )

    return "Available Spotify devices:\n" + "\n\n".join(lines)


def get_selected_device_id(telegram_id: str) -> str | None:
    selected_device_id = get_selected_device(telegram_id)
    if not selected_device_id:
        return None

    devices = get_available_devices(telegram_id)
    for device in devices:
        if device.get("id") == selected_device_id:
            return selected_device_id
    return None


def find_device_by_query(devices: list, query: str) -> dict | None:
    query_lower = query.lower().strip()
    if not query_lower:
        return None

    for device in devices:
        if device.get("id") == query:
            return device

    exact_matches = [d for d in devices if d.get("name", "").lower() == query_lower]
    if exact_matches:
        return exact_matches[0]

    partial_matches = [d for d in devices if query_lower in d.get("name", "").lower()]
    if len(partial_matches) == 1:
        return partial_matches[0]

    return None


def set_device(telegram_id: str, device_query: str) -> str:
    token = get_valid_token(telegram_id)
    if not token:
        return "You're not logged in. Use /login first."

    devices = get_available_devices(telegram_id)
    if not devices:
        return "No Spotify devices found. Open Spotify on your phone or PC."

    device = find_device_by_query(devices, device_query)
    if not device:
        return "Device not found. Use /device to list available devices."

    set_selected_device(telegram_id, device.get("id"))
    name = device.get("name", "Unknown")
    device_type = device.get("type", "Unknown")
    return f"Selected device: {name} ({device_type})\nID: `{device.get('id')}`"


def select_device(devices: list) -> str | None:
    """Choose the best available device for playback."""
    if not devices:
        return None
    for device in devices:
        if device.get("is_active"):
            return device.get("id")
    for prefer in ("Smartphone", "Speaker", "TV", "Computer", "WebPlayer"):
        for device in devices:
            if device.get("type") == prefer:
                return device.get("id")
    return devices[0].get("id")


def _prepare_device_for_control(telegram_id: str, device_id: str) -> None:
    """
    Wake / claim the device before play, queue, or resume.

    Spotify often returns 404 until the client has a recent playback session; short
    delays after transfer+play=true improve reliability but cannot replace the user
    opening Spotify and starting playback once on that device when the API still refuses.
    """
    transfer_playback(telegram_id, device_id, play=False)
    time.sleep(0.35)
    activate_device(telegram_id, device_id)
    time.sleep(0.55)


def _device_not_ready_hint() -> str:
    return (
        "❌ Spotify has no ready playback device for this account.\n\n"
        "Open Spotify on your phone or computer, start any song once (so the app is "
        "really playing), then use 📱 Select Device here and try again."
    )


def transfer_playback(telegram_id: str, device_id: str, play: bool = False) -> bool:
    """Transfer the Spotify session to the chosen device."""
    token = get_valid_token(telegram_id)
    if not token:
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"device_ids": [device_id], "play": play}
    response = requests.put(
        "https://api.spotify.com/v1/me/player",
        headers=headers,
        json=data
    )
    return response.status_code == 204


def activate_device(telegram_id: str, device_id: str) -> bool:
    """Activate the selected device if it is available but inactive."""
    return transfer_playback(telegram_id, device_id, play=True)


def get_now_playing(telegram_id: str) -> dict:
    token = get_valid_token(telegram_id)

    if not token:
        return {"text": "You're not logged in. Use /login first."}
    
    response = requests.get(
        "https://api.spotify.com/v1/me/player/currently-playing",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 204:
        return {"text": "Nothing is playing right now."}
    
    if response.status_code != 200:
        return {"text": f"❌ Error fetching current track: {response.status_code}"}
    
    data = response.json()
    
    if not data or data.get("item") is None:
        return {"text": "Nothing is playing right now."}
    
    item = data["item"]
    song = item.get("name", "Unknown")
    artists = item.get("artists") or []
    artist = artists[0]["name"] if artists else "Unknown Artist"
    album = item.get("album", {})
    images = album.get("images", [])
    image_url = images[0].get("url") if images else None
    return {
        "text": f"🎵 {song} - {artist}",
        "image_url": image_url
    }

def pause(telegram_id: str) -> str:
    token = get_valid_token(telegram_id)

    if not token:
        return "You're not logged in. Use /login first."

    headers = {"Authorization": f"Bearer {token}"}

    # Get available devices
    devices = get_available_devices(telegram_id)
    device_id = None

    # Try to find a phone/mobile device or active device
    for device in devices:
        if device.get("is_active") or device.get("type") == "Smartphone":
            device_id = device.get("id")
            break
    
    # If no mobile device, use the first available device
    if not device_id and devices:
        device_id = devices[0].get("id")
    
    # Prepare request params
    params = {}
    if device_id:
        params["device_id"] = device_id
    
    response = requests.put(
        "https://api.spotify.com/v1/me/player/pause",
        headers=headers,
        params=params
    )
    if response.status_code in (200, 204):
        return "⏸ Paused successfully"
    elif response.status_code == 404:
        if not devices:
            return "❌ No devices found. Open Spotify on your phone first."
        return "❌ No active device. Make sure Spotify is open on your phone."
    elif response.status_code == 403:
        return "❌ Spotify Premium required for playback control."
    elif response.status_code == 409:
        return "Nothing is playing right now."
    else:
        return f"❌ Error pausing playback: {response.status_code}"

def play(telegram_id: str, track_name: str) -> dict:
    token = get_valid_token(telegram_id)
    
    if not token:
        return {"text": "You're not logged in. Use /login first."}
    
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
        return {"text": f"❌ Search failed: {search_response.status_code}"}

    results = search_response.json()
    tracks = results["tracks"]["items"]

    if not tracks:
        return {"text": f"❌ No results found for: {track_name}"}

    track = tracks[0]
    track_uri = track["uri"]               
    track_title = track["name"]
    artists = track.get("artists") or []
    artist = artists[0]["name"] if artists else "Unknown Artist"
    album = track.get("album", {})
    images = album.get("images", [])
    image_url = images[0].get("url") if images else None

    # Step 2: Get available devices and select target device
    devices = get_available_devices(telegram_id)
    device_id = get_selected_device_id(telegram_id)
    if not device_id:
        device_id = select_device(devices)

    if not device_id:
        return {"text": "❌ No devices found. Open Spotify on your phone or PC first."}

    _prepare_device_for_control(telegram_id, device_id)

    # Step 3: Play the track on the selected device
    params = {"device_id": device_id}
    play_data = {"uris": [track_uri]}

    play_response = requests.put(
        "https://api.spotify.com/v1/me/player/play",
        headers=headers,
        params=params,
        json=play_data,
    )

    if play_response.status_code == 404:
        devices = get_available_devices(telegram_id)
        _prepare_device_for_control(telegram_id, device_id)
        play_response = requests.put(
            "https://api.spotify.com/v1/me/player/play",
            headers=headers,
            params=params,
            json=play_data,
        )

    if play_response.status_code == 204:
        return {
            "text": f"▶️ Playing: {track_title} — {artist}",
            "image_url": image_url
        }
    elif play_response.status_code == 404:
        if not devices:
            return {"text": "❌ No devices found. Open Spotify on your phone first."}
        return {"text": _device_not_ready_hint()}
    elif play_response.status_code == 403:
        return {"text": "⚠️ Spotify Premium required for playback control."}
    else:
        return {"text": f"❌ Playback error {play_response.status_code}: {play_response.text}"}

def resume(telegram_id: str) -> dict:
    token = get_valid_token(telegram_id)

    if not token:
        return {"text": "You're not logged in. Use /login first."}

    headers = {"Authorization": f"Bearer {token}"}

    # Get available devices
    devices = get_available_devices(telegram_id)
    device_id = get_selected_device_id(telegram_id)
    if not device_id:
        device_id = select_device(devices)

    if device_id:
        _prepare_device_for_control(telegram_id, device_id)

    # Prepare request params
    params = {}
    if device_id:
        params["device_id"] = device_id

    response = requests.put(
        "https://api.spotify.com/v1/me/player/play",
        headers=headers,
        params=params,
    )

    # Retry once on 404 — device may need a moment to become active
    if response.status_code == 404 and device_id:
        import time
        time.sleep(1)
        response = requests.put(
            "https://api.spotify.com/v1/me/player/play",
            headers=headers,
            params=params,
        )

    if response.status_code in (200, 204):
        now_playing = get_now_playing(telegram_id)
        if isinstance(now_playing, dict):
            now_playing["text"] = f"▶️ Resumed playback\n\n{now_playing.get('text', '')}"
            return now_playing
        return {"text": "▶️ Resumed playback"}

    elif response.status_code == 403:
        now_playing = get_now_playing(telegram_id)
        if isinstance(now_playing, dict) and now_playing.get("is_playing"):
            now_playing["text"] = f"▶️ Resumed playback\n\n{now_playing.get('text', '')}"
            return now_playing
        return {"text": "❌ Spotify Premium required for playback control."}

    elif response.status_code == 404:
        if not devices:
            return {"text": "❌ No devices found. Open Spotify on your phone first."}
        return {"text": _device_not_ready_hint()}

    else:
        return {"text": f"❌ Error resuming playback: {response.status_code}"}
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
    artists = track.get("artists") or []
    artist = artists[0]["name"] if artists else "Unknown Artist"

    # Step 2: Get available devices and select target device
    devices = get_available_devices(telegram_id)
    device_id = get_selected_device_id(telegram_id)
    if not device_id:
        device_id = select_device(devices)

    if not device_id:
        return "❌ No devices found. Open Spotify on your phone or PC first."

    _prepare_device_for_control(telegram_id, device_id)

    # Step 3: Add to queue
    params = {"uri": track_uri, "device_id": device_id}
    queue_response = requests.post(
        "https://api.spotify.com/v1/me/player/queue",
        headers=headers,
        params=params,
    )

    if queue_response.status_code == 404:
        devices = get_available_devices(telegram_id)
        _prepare_device_for_control(telegram_id, device_id)
        queue_response = requests.post(
            "https://api.spotify.com/v1/me/player/queue",
            headers=headers,
            params=params,
        )

    if queue_response.status_code in (200, 201, 202, 204):
        return f"✅ Added to queue: {track_display} by {artist}"
    elif queue_response.status_code == 401:
        return "Token expired. Please /login again."
    elif queue_response.status_code == 403:
        return "❌ This requires Spotify Premium."
    elif queue_response.status_code == 404:
        if not devices:
            return "❌ No devices found. Open Spotify on your phone first."
        return _device_not_ready_hint()
    else:
        return f"❌ Failed to add to queue. Status: {queue_response.status_code} - {queue_response.text}"