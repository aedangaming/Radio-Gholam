import random


# Store active voice contexts, including playlist, current audio_source and other variables
voice_contexts = {}


def remove_voice_context(guild_id: int):
    if voice_contexts.get(guild_id):
        voice_contexts.pop(guild_id)


def initialize_playlist(guild_id: int):
    voice_contexts[guild_id] = {
        "seek": None,
        "loop": "none",
        "next": False,
        "previous": False,
        "playlist": None,
        "current_track_index": 0,
        "new_playlist": True,
    }


def clear_playlist(guild_id: int):
    initialize_playlist(guild_id)


def add_to_playlist(guild_id: int, item: str, tags):
    if not voice_contexts.get(guild_id):
        initialize_playlist(guild_id)
    if not voice_contexts[guild_id].get("playlist"):
        voice_contexts[guild_id]["playlist"] = []
    voice_contexts[guild_id]["playlist"].append({"url": item, "tags": tags})


# def remove_from_playlist(guild_id: int, index: int):


def shuffle_playlist(guild_id: int):
    try:
        new_list = []
        while len(voice_contexts[guild_id]["playlist"]) > 0:
            rand = random.randint(0, len(voice_contexts[guild_id]["playlist"]) - 1)
            new_list.append(voice_contexts[guild_id]["playlist"][rand])
            voice_contexts[guild_id]["playlist"].pop(rand)
        voice_contexts[guild_id]["playlist"] = new_list
        return True
    except Exception:
        return False


def get_current_track(guild_id: int):
    try:
        playlist = voice_contexts[guild_id]["playlist"]
        index = voice_contexts[guild_id]["current_track_index"]
        return playlist[index]
    except Exception:
        return None
