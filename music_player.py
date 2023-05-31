import logging
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


_logger = logging.getLogger("main")


def get_voice_client_if_exists(guild_id: int):
    voice_client = None
    try:
        for item in client.voice_clients:
            if item.channel.guild.id == guild_id:
                voice_client = item
    except Exception:
        _logger.exception(
            f"Exception occurred while searching for VoiceClient with guild id of {guild_id}"
        )
    return voice_client


async def connect_or_get_connected_voice_client(voice_channel: VoiceChannel):
    # Check if there is an active VoiceClient for this guild
    _logger.debug(
        f"Getting a connected VoiceClient for '{voice_channel.name}' ({str(voice_channel.id)})"
    )
    voice_client: VoiceClient = get_voice_client_if_exists(voice_channel.guild.id)
    try:
        # Connect to voice if it is not already connected.
        if not voice_client:
            _logger.debug(
                "VoiceClient does not exist. Making a new VoiceClient connection "
                + f"to '{voice_channel.name}' ({str(voice_channel.id)})."
            )
            voice_client = await voice_channel.connect(timeout=3, reconnect=True)
            _logger.debug(
                f"VoiceClient connection established to '{voice_channel.name}' ({str(voice_channel.id)})."
            )
        if not voice_client.is_connected():
            _logger.debug(
                f"VoiceClient is not connected to '{voice_channel.name}' ({str(voice_channel.id)}). "
                + f"Reconnecting..."
            )
            try:
                await disconnect_voice_client(voice_client)
                voice_client = await voice_channel.connect(timeout=3, reconnect=True)
                _logger.debug(
                    f"VoiceClient connection established to '{voice_channel.name}' ({str(voice_channel.id)})."
                )
            except Exception:
                _logger.exception(
                    "Exception occurred while reconnecting the VoiceClient "
                    + f"to '{voice_channel.name} ({str(voice_channel.id)})"
                )
    except Exception:
        _logger.exception(
            "Exception occurred while preparing a connected VoiceClient "
            + f"to '{voice_channel.name} ({str(voice_channel.id)})"
        )
        return None

    # Move the bot to the current voice channel
    if voice_channel.id != voice_client.channel.id:
        _logger.debug(
            "VoiceClient is connected to another voice channel. Trying to move it "
            + f"from '{voice_client.channel.name}' ({str(voice_client.channel.id)}) to "
            + f"'{voice_channel.name}' ({str(voice_channel.id)})"
        )
        try:
            await disconnect_voice_client(voice_client)
            voice_client = await voice_channel.connect(timeout=3, reconnect=True)
            _logger.debug(
                f"VoiceClient connection established to '{voice_channel.name}' ({str(voice_channel.id)})."
            )
        except Exception:
            _logger.exception(
                "Exception occurred while moving the VoiceClient "
                + f"to '{voice_channel.name} ({str(voice_channel.id)})"
            )
            return None

    return voice_client


async def disconnect_voice_client(voice_client: VoiceClient):
    try:
        if voice_client:
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            _logger.debug(
                f"VoiceClient disonnected. guild_id: {str(voice_client.guild.id)}"
            )
            remove_voice_context(voice_client.guild.id)
    except Exception:
        _logger.exception(
            f"Exception occurred when disconnecting a voice client. guild_id: {voice_client.guild.id}"
        )


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

        _logger.info(
            f"Bot was moved to a new voice channel '{after.channel.name}' ({str(after.channel.id)}) "
            + f"while playing. Trying to resume the playback..."
        )
        await asyncio.sleep(1.5)  # wait a moment for it to set in
        vc.pause()
        vc.resume()


def play_on_voice_client(voice_client: VoiceClient, input: str, timestamp: int = None):
    _logger.debug(
        f"Trying to play '{input}' on '{voice_client.channel.name}' "
        + f"({str(voice_client.channel.id)}) timestamp: {str(timestamp)}"
    )
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
        voice_client.play(audio_source, after=lambda e: decide_next_track(voice_client))
        _logger.debug(
            f"Started playing '{input}' on '{voice_client.channel.name}' "
            + f"({str(voice_client.channel.id)}) timestamp: {str(timestamp)}"
        )


async def play(voice_client: VoiceClient, input: str, forced_title: str = None):
    tags = get_input_tags(input, forced_title)
    if not tags:
        return f"Cannot play **{input}** right now."

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
        if voice_client.is_playing():
            voice_client.stop()  # stopping the player will automatically fire "decide_next_track" function
        else:
            await decide_next_track(voice_client)
        _logger.info(
            f"Started playing '{input}' at '{voice_client.channel.name}' ({str(voice_client.channel.id)}) "
            + f"in '{voice_client.guild.name}' ({str(voice_client.guild.id)}) forced_title: '{forced_title}'"
        )
        return generate_playback_status_text(voice_client.guild.id)
    else:
        add_to_playlist(voice_client.guild.id, input, tags)
        _logger.info(
            f"Added '{input}' to the playlist at '{voice_client.channel.name}' ({str(voice_client.channel.id)}) "
            + f"in '{voice_client.guild.name}' ({str(voice_client.guild.id)}) forced_title: '{forced_title}'"
        )
        return f"**{generate_track_info(input, tags, False)}** has been added to the playlist."


async def decide_next_track(voice_client: VoiceClient):
    try:
        context = voice_contexts[voice_client.guild.id]
        _logger.debug(
            "Deciding next track... "
            + f"guild_id: {str(voice_client.guild.id)} context: {str(context)}"
        )
        index = context["current_track_index"]

        if context["seek"] is not None:
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
                _logger.debug(
                    "The playlist has come to its end. There is nothing to play next. "
                    + f"guild_id: {voice_client.guild.id}"
                )
                await disconnect_voice_client(voice_client)
        else:
            context["current_track_index"] = index
            play_on_voice_client(voice_client, context["playlist"][index]["url"])
    except Exception:
        _logger.exception(
            "Exception occurred while deciding for next track "
            + f"guild_id: {str(voice_client.guild.id)} context: {str(context)}"
        )
        raise


async def stop(voice_client: VoiceClient):
    await disconnect_voice_client(voice_client)
    _logger.info(
        f"Stopped playing at '{voice_client.channel.name}' ({str(voice_client.channel.id)}) "
        + f"in '{voice_client.guild.name}' ({str(voice_client.guild.id)})"
    )
    return "Stopped."


async def next(voice_client: VoiceClient):
    voice_contexts[voice_client.guild.id]["next"] = True
    voice_client.stop()
    await asyncio.sleep(0.5)
    _logger.info(
        f"Skipped a track at '{voice_client.channel.name}' ({str(voice_client.channel.id)}) "
        + f"in '{voice_client.guild.name}' ({str(voice_client.guild.id)})"
    )
    return generate_playback_status_text(voice_client.guild.id)


async def previous(voice_client: VoiceClient):
    voice_contexts[voice_client.guild.id]["previous"] = True
    voice_client.stop()
    await asyncio.sleep(0.5)
    _logger.info(
        f"Rewinded a track at '{voice_client.channel.name}' ({str(voice_client.channel.id)}) "
        + f"in '{voice_client.guild.name}' ({str(voice_client.guild.id)})"
    )
    return generate_playback_status_text(voice_client.guild.id)


def loop(voice_client: VoiceClient, loop: str):
    context = voice_contexts[voice_client.guild.id]
    context["loop"] = loop
    _logger.info(
        f"Loop mode set to '{loop}' at '{voice_client.channel.name}' ({str(voice_client.channel.id)}) "
        + f"in '{voice_client.guild.name}' ({str(voice_client.guild.id)})"
    )
    return f"Loop mode: **{loop}**"


def shuffle(voice_client: VoiceClient):
    shuffle_playlist(voice_client.guild.id)
    _logger.info(
        f"Shuffled playlist at '{voice_client.channel.name}' ({str(voice_client.channel.id)}) "
        + f"in '{voice_client.guild.name}' ({str(voice_client.guild.id)})"
    )
    return "The playlist has been **shuffled**."


def pause(voice_client: VoiceClient):
    if voice_client.is_paused():
        return "Playback is already paused."

    voice_client.pause()
    _logger.info(
        f"Paused playing at '{voice_client.channel.name}' ({str(voice_client.channel.id)}) "
        + f"in '{voice_client.guild.name}' ({str(voice_client.guild.id)})"
    )
    return f"Playback has been **paused**."


def resume(voice_client: VoiceClient):
    if not voice_client.is_paused():
        return "Playback is already resuming."

    voice_client.resume()
    _logger.info(
        f"Resumed playing at '{voice_client.channel.name}' ({str(voice_client.channel.id)}) "
        + f"in '{voice_client.guild.name}' ({str(voice_client.guild.id)})"
    )
    return f"Playback has been **resumed**."


def seek(voice_client: VoiceClient, timestamp: str):
    converted_timestamp = convert_timestamp(timestamp)
    if converted_timestamp is None:
        return f"Invalid timestamp: **{timestamp}**"

    context = voice_contexts[voice_client.guild.id]
    context["seek"] = converted_timestamp
    _logger.info(
        f"Seeking to '{timestamp}' at '{voice_client.channel.name}' ({str(voice_client.channel.id)}) "
        + f"in '{voice_client.guild.name}' ({str(voice_client.guild.id)})"
    )
    voice_client.stop()
    return f"Seeking to **{timestamp}**"


def get_input_tags(input: str, forced_title: str = None):
    try:
        meta = ffmpeg.probe(input)
    except Exception:
        _logger.warning(
            f"Exception occurred while probing the input: '{input}' maybe the link is invalid."
        )
        return None

    _logger.debug(f"Probing for '{input}' finished. result: {meta}")

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

    tags = {
        "duration": duration,
        "title": title,
        "forced_title": forced_title,
        "artist": artist,
        "stream_title": stream_title,
    }
    _logger.debug(
        f"Tags generated for '{input}'. forced_title '{forced_title}'. tags: {tags}"
    )
    return tags


def generate_track_info(url, tags, include_duration: bool):
    info = f"{url}"
    if not tags:
        return info

    if tags["forced_title"]:
        return tags["forced_title"]

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

    _logger.debug(
        f"Track info was generated for input: '{url}' tags: {tags} "
        + f"include_duration: '{include_duration}' result: '{info}'"
    )
    return info


def generate_playback_status_text(guild_id: int):
    result = "The playlist is empty."
    current_track = get_current_track(guild_id)
    if current_track:
        track_info = generate_track_info(
            current_track["url"], current_track["tags"], include_duration=True
        )
        if current_track["tags"]["duration"]:  # it is a single track
            result = f"Now playing  🔊  **{track_info}**"
        else:  # it is a stream
            result = f"Now playing  🔴 LIVE |  **{track_info}**"

    _logger.debug(
        f"Generated playback status text. guild_id: {guild_id} "
        + f"current_track: {current_track} result: '{result}'"
    )
    return result


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
        _logger.exception(f"Failed to convert '{timestamp}' to a valid timestamp.")
        return None
