import asyncio
import ffmpeg
from bot import client
from nextcord import VoiceClient, VoiceChannel, VoiceState, Member, FFmpegOpusAudio
from playlist import (
    add_to_playlist,
    clear_playlist,
    get_current_track,
    remove_voice_context,
    shuffle_playlist,
    voice_contexts,
)


def get_voice_client_if_exists(guild_id: int):
    voice_client = None
    for item in client.voice_clients:
        if item.channel.guild.id == guild_id:
            voice_client = item
    return voice_client


async def connect_or_get_connected_voice_client(voice_channel: VoiceChannel):
    # Check if there is an active VoiceClient for this guild
    voice_client: VoiceClient = get_voice_client_if_exists(voice_channel.guild.id)
    try:
        # Connect to voice if it is not already connected.
        if not voice_client:
            voice_client = await voice_channel.connect(timeout=3, reconnect=False)
        if not voice_client.is_connected():
            try:
                await voice_client.disconnect()
                remove_voice_context(voice_channel.guild.id)
                voice_client = await voice_channel.connect(timeout=3, reconnect=False)
            except Exception:
                pass
    except Exception:
        return None

    # Move the bot to the current voice channel
    if voice_channel.id != voice_client.channel.id:
        try:
            await voice_client.disconnect()
            remove_voice_context(voice_channel.guild.id)
            voice_client = await voice_channel.connect(timeout=3, reconnect=False)
        except Exception:
            return None

    return voice_client


async def disconnect_voice_client(voice_client: VoiceClient):
    if voice_client:
        if voice_client.is_playing():
            voice_client.stop()
        await voice_client.disconnect()
        remove_voice_context(voice_client.guild.id)


# Resume playing after moving the bot between voice channels
async def continue_playing_moved_voice_client(
    member: Member,
    before: VoiceState,
    after: VoiceState,
):
    if member != client.user:
        return

    vc = member.guild.voice_client
    # Ensure:
    # - this is a channel move as opposed to anything else
    # - this is our instance's voice client and we can action upon it
    if (
        before.channel
        and after.channel  # if this is None this could be a join
        and before.channel != after.channel  # if this is None this could be a leave
        and isinstance(  # if these match then this could be e.g. server deafen
            vc, VoiceClient
        )
        and vc.channel  # None & not external Protocol check
        == after.channel  # our current voice client is in this channel
    ):
        # If the voice was intentionally paused don't resume it for no reason
        if vc.is_paused():
            return
        # If the voice isn't playing anything there is no sense in trying to resume
        if not vc.is_playing():
            return

        await asyncio.sleep(1.5)  # wait a moment for it to set in
        vc.pause()
        vc.resume()


def play_on_voice_client(voice_client: VoiceClient, input: str, timestamp: int = None):
    if voice_client.is_playing():
        voice_client.stop()
    else:
        if timestamp:
            audio_source = FFmpegOpusAudio(
                input, before_options=f"-fflags discardcorrupt -ss {str(timestamp)}"
            )
        else:
            audio_source = FFmpegOpusAudio(
                input, before_options="-fflags discardcorrupt"
            )
        voice_client.play(audio_source, after=lambda e: after_playing(voice_client))


def play(voice_client: VoiceClient, input: str, force_title: str = None):
    tags = get_input_tags(input)
    ignore_playlist = True
    if tags:
        if tags.get("duration"):
            current = get_current_track(voice_client.guild.id)
            if current:
                if current["tags"]["duration"]:
                    ignore_playlist = False

    if ignore_playlist:
        clear_playlist(voice_client.guild.id)
        add_to_playlist(voice_client.guild.id, input, tags)
        play_on_voice_client(voice_client, input)
        return generate_playback_status_text(voice_client.guild.id, force_title)
    else:
        add_to_playlist(voice_client.guild.id, input, tags)
        return f"**{generate_track_info(input, tags, False)}** has been added to the playlist."


async def after_playing(voice_client: VoiceClient):
    context = voice_contexts[voice_client.guild.id]
    index = context["current_track_index"]

    if context["seek"]:
        play_on_voice_client(
            voice_client, context["playlist"][index]["url"], context["seek"]
        )
        context["seek"] = None
        return

    if context["previous"]:
        index = index - 1
        if index < 0:
            index = len(context["playlist"]) - 1
        context["current_track_index"] = index
        context["previous"] = False
        play_on_voice_client(voice_client, context["playlist"][index]["url"])
        return

    if context["loop"] == "track" and not context["next"]:  # repeat the same track
        play_on_voice_client(voice_client, context["playlist"][index]["url"])
        return

    # Go for the next track!
    context["next"] = False
    index = index + 1
    if index >= len(context["playlist"]):  # End of the playlist
        index = 0
        context["current_track_index"] = index
        if context["loop"] in ["playlist", "track"]:  # repeat the playlist
            play_on_voice_client(voice_client, context["playlist"][index]["url"])
        else:
            await disconnect_voice_client(voice_client)
    else:
        context["current_track_index"] = index
        play_on_voice_client(voice_client, context["playlist"][index]["url"])


async def next(voice_client: VoiceClient):
    try:
        voice_contexts[voice_client.guild.id]["next"] = True
        voice_client.stop()
        await asyncio.sleep(0.5)
        return generate_playback_status_text(voice_client.guild.id)
    except Exception as e:
        print(e)
        return "Stopped."


async def previous(voice_client: VoiceClient):
    try:
        voice_contexts[voice_client.guild.id]["previous"] = True
        voice_client.stop()
        await asyncio.sleep(0.5)
        return generate_playback_status_text(voice_client.guild.id)
    except Exception as e:
        print(e)
        return "Stopped."


def loop(voice_client: VoiceClient, loop: str):
    context = voice_contexts[voice_client.guild.id]
    context["loop"] = loop


def shuffle(voice_client: VoiceClient):
    return shuffle_playlist(voice_client.guild.id)


def pause(voice_client: VoiceClient):
    try:
        voice_client.pause()
        return True
    except Exception as e:
        print(e)
        return False


def resume(voice_client: VoiceClient):
    try:
        voice_client.resume()
        return True
    except Exception as e:
        print(e)
        return False


async def stop(voice_client: VoiceClient):
    try:
        await disconnect_voice_client(voice_client)
    except Exception as e:
        print(e)


def seek(voice_client: VoiceClient, timestamp: str):
    try:
        converted_timestamp = convert_timestamp(timestamp)
        if converted_timestamp is None:
            return None
        context = voice_contexts[voice_client.guild.id]
        context["seek"] = converted_timestamp
        voice_client.stop()
        return True
    except Exception as e:
        print(e)
        return False


def get_input_tags(input):
    try:
        meta = ffmpeg.probe(input)
    except Exception as e:
        print(e)
        return None

    if not meta["format"]:
        return None

    duration = meta["format"].get("duration")
    title = None
    artist = None
    stream_title = None

    if meta["format"].get("tags"):
        title = meta["format"]["tags"].get("title")
        artist = meta["format"]["tags"].get("artist")
        stream_title = meta["format"]["tags"].get("StreamTitle")

    return {
        "duration": duration,
        "title": title,
        "artist": artist,
        "stream_title": stream_title,
    }


def generate_track_info(url, tags, include_duration: bool):
    info = f"**{url}**"
    if not tags:
        return info

    title = tags["title"]
    artist = tags["artist"]
    stream_title = tags["stream_title"]
    duration = tags["duration"]

    if title and artist:
        info = f"{title} - {artist}"
    elif title:
        info = f"{title} - [unknown artist]"
    elif artist:
        info = f"[unknown title] - {artist}"
    elif stream_title:
        info = f"{stream_title}"

    if include_duration and duration:
        duration = duration.split(".")[0]
        info = (
            info
            + "‎ ["  # Left-to-right mark
            + str(int(int(duration) / 60))
            + ":"
            + "{:02d}]".format(int(duration) % 60)
        )

    return info


def generate_playback_status_text(guild_id: int, force_title: str = None):
    current_track = get_current_track(guild_id)
    if current_track:
        track_info = force_title
        if not track_info:
            track_info = generate_track_info(
                current_track["url"], current_track["tags"], include_duration=True
            )
        if current_track["tags"]["duration"]:  # it is a single track
            return f"Now playing  🔊  **{track_info}**"
        else:  # it is a stream
            return f"Now playing  🔴 LIVE |  **{track_info}**"

    return "The playlist is empty."


def convert_timestamp(timestamp: str):
    try:
        result = 0
        hours = None
        minutes = None
        seconds = None
        parts = timestamp.split(":")
        if len(parts) > 3:
            return None
        parts.reverse()
        if len(parts) > 0:
            seconds = parts[0]
        if len(parts) > 1:
            minutes = parts[1]
        if len(parts) > 2:
            hours = parts[2]

        if hours:
            if "." in hours:
                return None
            if int(hours) < 0:
                return None
            result = result + int(hours) * 3600

        if minutes:
            if "." in minutes:
                return None
            if int(minutes) < 0:
                return None
            result = result + int(minutes) * 60

        if seconds:
            if int(seconds) < 0:
                return None
            result = result + int(seconds)

        return result
    except Exception:
        return None
