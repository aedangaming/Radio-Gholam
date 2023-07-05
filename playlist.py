import random
from datetime import datetime

# Store active voice contexts, including playlist, current audio_source and other variables
voice_contexts = {}
status_messages = {}


def remove_voice_context(guild_id: int):
    if voice_contexts.get(guild_id):
        voice_contexts.pop(guild_id)


def initialize_playlist(guild_id: int, radio_tv: bool = False):
    voice_contexts[guild_id] = {
        "seek": None,
        "loop": "disabled",
        "next": False,
        "previous": False,
        "replay": False,
        "playlist": None,
        "current_track_index": -1,
        "radio/tv": radio_tv,
        "idle": True,
        "last_interaction_time": datetime.now(),
        "deciding_next_track": False,
    }


def clear_playlist(guild_id: int, radio_tv: bool = False):
    initialize_playlist(guild_id, radio_tv)


def add_to_playlist(
    guild_id: int, item: str, tags=None, starting_timestamp: str = None
):
    if not voice_contexts.get(guild_id):
        initialize_playlist(guild_id)
    if not voice_contexts[guild_id].get("playlist"):
        voice_contexts[guild_id]["playlist"] = []
    voice_contexts[guild_id]["playlist"].append(
        {"url": item, "tags": tags, "starting_timestamp": starting_timestamp}
    )


# def remove_from_playlist(guild_id: int, index: int):


def shuffle_playlist(guild_id: int):
    new_list = []
    while len(voice_contexts[guild_id]["playlist"]) > 0:
        rand = random.randint(0, len(voice_contexts[guild_id]["playlist"]) - 1)
        new_list.append(voice_contexts[guild_id]["playlist"][rand])
        voice_contexts[guild_id]["playlist"].pop(rand)
    voice_contexts[guild_id]["playlist"] = new_list


def get_playlist_size(guild_id: int):
    try:
        playlist = voice_contexts[guild_id]["playlist"]
        return len(playlist)
    except Exception:
        return 0


def get_current_track(guild_id: int):
    try:
        if voice_contexts[guild_id]["idle"]:
            return None

        playlist = voice_contexts[guild_id]["playlist"]
        index = voice_contexts[guild_id]["current_track_index"]
        return playlist[index]
    except Exception:
        return None
