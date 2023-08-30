import json
import socket
import asyncio
import logging
import requests
from datetime import datetime
from urllib.parse import urlparse
from geoip_interface import lookup_country_code
from nextcord import VoiceClient, VoiceChannel, VoiceState, Member, FFmpegOpusAudio

from bot import client, MAX_IDLE_SECONDS, PREFERRED_PROXIES
from playlist import (
    initialize_playlist,
    add_to_playlist,
    clear_playlist,
    get_current_track,
    shuffle_playlist,
    get_playlist_size,
    voice_contexts,
    status_messages,
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
        f"Getting a connected VoiceClient for '{voice_channel.name}' ({voice_channel.id})"
    )
    voice_client: VoiceClient = get_voice_client_if_exists(voice_channel.guild.id)
    try:
        # Connect to voice if it is not already connected.
        if not voice_client:
            _logger.debug(
                "VoiceClient does not exist. Making a new VoiceClient connection "
                + f"to '{voice_channel.name}' ({voice_channel.id})."
            )
            voice_client = await voice_channel.connect(timeout=3, reconnect=True)
            _logger.debug(
                f"VoiceClient connection established to '{voice_channel.name}' ({voice_channel.id})."
            )
        if not voice_client.is_connected():
            _logger.debug(
                f"VoiceClient is not connected to '{voice_channel.name}' ({voice_channel.id}). "
                + f"Reconnecting..."
            )
            try:
                await disconnect_voice_client(voice_client)
                voice_client = await voice_channel.connect(timeout=3, reconnect=True)
                _logger.debug(
                    f"VoiceClient connection established to '{voice_channel.name}' ({voice_channel.id})."
                )
            except Exception:
                _logger.exception(
                    "Exception occurred while reconnecting the VoiceClient "
                    + f"to '{voice_channel.name} ({voice_channel.id})"
                )
    except Exception:
        _logger.exception(
            "Exception occurred while preparing a connected VoiceClient "
            + f"to '{voice_channel.name} ({voice_channel.id})"
        )
        return None

    # Move the bot to the current voice channel
    if voice_channel.id != voice_client.channel.id:
        _logger.debug(
            "VoiceClient is connected to another voice channel. Trying to move it "
            + f"from '{voice_client.channel.name}' ({voice_client.channel.id}) to "
            + f"'{voice_channel.name}' ({voice_channel.id})"
        )
        try:
            await disconnect_voice_client(voice_client)
            voice_client = await voice_channel.connect(timeout=3, reconnect=True)
            _logger.debug(
                f"VoiceClient connection established to '{voice_channel.name}' ({voice_channel.id})."
            )
        except Exception:
            _logger.exception(
                "Exception occurred while moving the VoiceClient "
                + f"to '{voice_channel.name} ({voice_channel.id})"
            )
            return None

    if not voice_contexts.get(voice_client.guild.id):
        initialize_playlist(voice_client.guild.id)

    _logger.debug(
        f"Connected VoiceClient for '{voice_channel.name}' ({voice_channel.id}) is ready."
    )

    return voice_client


async def disconnect_voice_client(voice_client: VoiceClient):
    try:
        if voice_client:
            if voice_client.is_playing():
                _stop_voice_client(voice_client)
            await voice_client.disconnect()
            _logger.debug(f"VoiceClient disonnected. guild_id: {voice_client.guild.id}")
    except Exception:
        _logger.exception(
            f"Exception occurred when disconnecting a voice client. guild_id: {voice_client.guild.id}"
        )


def _stop_voice_client(voice_client: VoiceClient):
    voice_contexts[voice_client.guild.id]["deciding_next_track"] = True
    voice_client.stop()


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
        # if the voice was intentionally paused don't resume it for no reason
        if vc.is_paused():
            return
        # if the voice isn't playing anything there is no sense in trying to resume
        if not vc.is_playing():
            return

        _logger.info(
            f"Bot was moved to a new voice channel '{after.channel.name}' ({after.channel.id}) "
            + f"while playing. Trying to resume the playback..."
        )
        await asyncio.sleep(1.5)  # wait a moment for it to set in
        vc.pause()
        vc.resume()


async def refresh_playback_or_disconnect_idle_voice_clients():
    for voice_client in client.voice_clients:
        try:
            context = voice_contexts.get(voice_client.guild.id)
            if not context:
                continue
            if context["idle"]:
                if (
                    datetime.now().timestamp()
                    - context["last_interaction_time"].timestamp()
                    > MAX_IDLE_SECONDS
                ):
                    await disconnect_voice_client(voice_client)
                    _logger.debug(
                        f"Disconnected idle VoiceClient in guild '{voice_client.guild.name}' "
                        + f"({voice_client.guild.id})"
                    )
            elif (
                voice_client.is_playing() and not voice_client.is_paused()
            ):  # Refresh playback in case websocket was disconnected...
                voice_client.pause()
                voice_client.resume()
        except Exception:
            _logger.exception(
                "Exception occurred while checking idle status of a VoiceClient. "
                + f"guild_id: {voice_client.guild.id}"
            )


async def play_on_voice_client(
    voice_client: VoiceClient, playlist_item, seek_timestamp: str = None
):
    if not playlist_item["tags"]:
        _logger.debug(
            f"Tags are missing for the playlist_item: {playlist_item} "
            + "Getting input tags..."
        )
        playlist_item["tags"] = await get_input_tags(playlist_item["url"])

    input = playlist_item["url"]
    starting_timestamp = playlist_item["starting_timestamp"]

    _logger.debug(
        f"Trying to play {playlist_item} on '{voice_client.channel.name}' "
        + f"({voice_client.channel.id}) seek_timestamp: {seek_timestamp}"
    )

    if voice_client.is_playing():
        _stop_voice_client(voice_client)
        return

    final_timestamp = None
    if seek_timestamp:
        final_timestamp = seek_timestamp
    elif starting_timestamp:
        final_timestamp = starting_timestamp
        playlist_item["starting_timestamp"] = None

    audio_source = FFmpegOpusAudio(
        input,
        before_options=f"-fflags discardcorrupt"
        + f"{_generate_ffmpeg_http_proxy_option(input)}"
        + f"{_generate_ffmpeg_start_timestamp_option(final_timestamp)}",
    )

    voice_client.play(audio_source, after=lambda e: decide_next_track(voice_client))
    _logger.debug(
        f"Started playing {playlist_item} on '{voice_client.channel.name}' "
        + f"({voice_client.channel.id}) effective timestamp: {final_timestamp}"
    )
    await update_status_text(voice_client)


def _generate_ffmpeg_start_timestamp_option(timestamp: str):
    if timestamp is None:
        return ""
    return f" -ss {timestamp}"


def _generate_ffmpeg_http_proxy_option(link: str):
    parsed_url = urlparse(link)
    host = parsed_url.netloc.split(":")[0]
    ip = socket.gethostbyname(host)
    country_code = lookup_country_code(ip)
    _logger.debug(f"Host country detected as '{country_code}' for '{link}'")
    proxy_url = PREFERRED_PROXIES.get(country_code)

    if proxy_url is None:
        return ""

    if not _check_proxy_health(proxy_url):
        return ""

    _logger.debug(f"Using '{proxy_url}' as a proxy to play '{link}'")
    return f" -http_proxy {proxy_url}"


def _check_proxy_health(proxy_url: str):
    try:
        response = requests.get(
            "https://www.google.com",
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=1,
        )
        return True
    except:
        _logger.debug(f"Proxy server '{proxy_url}' is not operational.")
        return False


async def play(
    voice_client: VoiceClient,
    input: str,
    radio_tv: bool = False,
    forced_title: str = None,
    starting_timestamp: str = None,
):
    tags = await get_input_tags(input, forced_title)
    if not tags:
        return f"Cannot play **{forced_title if forced_title else input}** right now."

    ignore_playlist = True
    converted_timestamp = None
    if not radio_tv:
        if not is_playing_radio_or_tv(voice_client) and not is_idle(voice_client):
            ignore_playlist = False

        if starting_timestamp:
            converted_timestamp = convert_timestamp(starting_timestamp)
            if converted_timestamp is None:
                return f"Invalid timestamp: **{starting_timestamp}**"

    if ignore_playlist:
        clear_playlist(voice_client.guild.id, radio_tv)
        add_to_playlist(voice_client.guild.id, input, tags, converted_timestamp)
        if voice_client.is_playing() or voice_client.is_paused():
            _stop_voice_client(
                voice_client
            )  # stopping the player will automatically fire "decide_next_track" function
            await wait_until_deciding_next_track_is_finished(voice_client, 5)
        else:
            await decide_next_track(voice_client)
        _logger.info(
            f"Started playing '{input}' at '{voice_client.channel.name}' ({voice_client.channel.id}) "
            + f"in '{voice_client.guild.name}' ({voice_client.guild.id}) forced_title: '{forced_title}'"
        )
        if not tags.get("duration"):  # Loop live stream so it will restart on failures
            voice_contexts[voice_client.guild.id]["loop"] = "track"
        if radio_tv:
            return f"Tuned to **{forced_title}**!"
        return f"Playlist initialized with **{generate_track_info(input, tags, include_duration=False)}**."
    else:
        add_to_playlist(voice_client.guild.id, input, tags, converted_timestamp)
        _logger.info(
            f"Added '{input}' to the playlist at '{voice_client.channel.name}' ({voice_client.channel.id}) "
            + f"in '{voice_client.guild.name}' ({voice_client.guild.id}) forced_title: '{forced_title}'"
        )
        return f"**{generate_track_info(input, tags, include_duration=False)}** has been added to the playlist."


async def decide_next_track(voice_client: VoiceClient):
    try:
        context = voice_contexts[voice_client.guild.id]
        _logger.debug(
            "Deciding next track... "
            + f"guild_id: {voice_client.guild.id} context: {context}"
        )
        index = context["current_track_index"]

        context["last_interaction_time"] = datetime.now()

        if context["stop"]:
            context["stop"] = False
            context["idle"] = True
            context["deciding_next_track"] = False
            return

        context["idle"] = False

        if context["replay"]:
            index = 0
            await play_on_voice_client(voice_client, context["playlist"][index])
            context["replay"] = None
            context["deciding_next_track"] = False
            return

        if context["seek"] is not None:  # Seek value can be zero
            await play_on_voice_client(
                voice_client, context["playlist"][index], seek_timestamp=context["seek"]
            )
            context["seek"] = None
            context["deciding_next_track"] = False
            return

        if context["previous"]:
            index = index - 1
            if index < 0:
                index = len(context["playlist"]) - 1
            context["current_track_index"] = index
            context["previous"] = False
            await play_on_voice_client(voice_client, context["playlist"][index])
            context["deciding_next_track"] = False
            return

        if context["loop"] == "track" and not context["next"]:  # repeat the same track
            await play_on_voice_client(voice_client, context["playlist"][index])
            context["deciding_next_track"] = False
            return

        # Go for the next track!
        if not context["next"] and index >= 0:
            _logger.debug(
                f"Track playback has reached to its end. guild_id: {voice_client.guild.id} "
                + f"context: {context}"
            )
        context["next"] = False
        index = index + 1
        if index >= len(context["playlist"]):  # End of the playlist
            index = 0
            context["current_track_index"] = index
            if context["loop"] in ["playlist", "track"]:  # repeat the playlist
                await play_on_voice_client(voice_client, context["playlist"][index])
            else:
                _logger.debug(
                    "The playlist has come to its end. There is nothing to play next. "
                    + f"guild_id: {voice_client.guild.id}"
                )
                context["last_interaction_time"] = datetime.now()
                context["idle"] = True
                await update_status_text(voice_client)
        else:
            context["current_track_index"] = index
            await play_on_voice_client(voice_client, context["playlist"][index])
        context["deciding_next_track"] = False
    except Exception:
        _logger.exception(
            "Exception occurred while deciding for next track "
            + f"guild_id: {voice_client.guild.id} context: {context}"
        )
        await disconnect_voice_client(voice_client)


async def wait_until_deciding_next_track_is_finished(
    voice_client: VoiceClient, timeout: float
):
    start = datetime.now()
    while datetime.now().timestamp() - start.timestamp() < timeout:
        await asyncio.sleep(0.2)
        if voice_contexts[voice_client.guild.id]["deciding_next_track"] == False:
            break


async def stop(voice_client: VoiceClient):
    context = voice_contexts.get(voice_client.guild.id)
    if context:
        context["stop"] = True
    await disconnect_voice_client(voice_client)

    _logger.info(
        f"Stopped playing at '{voice_client.channel.name}' ({voice_client.channel.id}) "
        + f"in '{voice_client.guild.name}' ({voice_client.guild.id})"
    )
    await update_status_text(voice_client)
    return "Stopped."


async def next(voice_client: VoiceClient):
    voice_contexts[voice_client.guild.id]["next"] = True
    _stop_voice_client(voice_client)
    await wait_until_deciding_next_track_is_finished(voice_client, 5)
    _logger.info(
        f"Skipped a track at '{voice_client.channel.name}' ({voice_client.channel.id}) "
        + f"in '{voice_client.guild.name}' ({voice_client.guild.id})"
    )
    return "Skipped."


async def previous(voice_client: VoiceClient):
    voice_contexts[voice_client.guild.id]["previous"] = True
    _stop_voice_client(voice_client)
    await wait_until_deciding_next_track_is_finished(voice_client, 5)
    _logger.info(
        f"Rewinded a track at '{voice_client.channel.name}' ({voice_client.channel.id}) "
        + f"in '{voice_client.guild.name}' ({voice_client.guild.id})"
    )
    return "Rewinded."


def loop(voice_client: VoiceClient, loop: str):
    if is_playlist_empty(voice_client.guild.id):
        return "Play something first!"

    context = voice_contexts[voice_client.guild.id]
    context["loop"] = loop
    _logger.info(
        f"Loop mode set to '{loop}' at '{voice_client.channel.name}' ({voice_client.channel.id}) "
        + f"in '{voice_client.guild.name}' ({voice_client.guild.id})"
    )
    return f"Loop mode: **{loop}**"


def shuffle(voice_client: VoiceClient):
    if is_playlist_empty(voice_client.guild.id):
        return "Play something first!"

    shuffle_playlist(voice_client.guild.id)
    _logger.info(
        f"Shuffled playlist at '{voice_client.channel.name}' ({voice_client.channel.id}) "
        + f"in '{voice_client.guild.name}' ({voice_client.guild.id})"
    )
    return "The playlist has been **shuffled**."


def pause(voice_client: VoiceClient):
    if voice_client.is_paused():
        return "Playback is already paused."

    voice_client.pause()
    _logger.info(
        f"Paused playing at '{voice_client.channel.name}' ({voice_client.channel.id}) "
        + f"in '{voice_client.guild.name}' ({voice_client.guild.id})"
    )
    return f"Playback has been **paused**."


def resume(voice_client: VoiceClient):
    if not voice_client.is_paused():
        return "Playback is already resuming."

    voice_client.resume()
    _logger.info(
        f"Resumed playing at '{voice_client.channel.name}' ({voice_client.channel.id}) "
        + f"in '{voice_client.guild.name}' ({voice_client.guild.id})"
    )
    return f"Playback has been **resumed**."


def seek(voice_client: VoiceClient, timestamp: str):
    converted_timestamp = convert_timestamp(timestamp)
    if converted_timestamp is None:
        return f"Invalid timestamp: **{timestamp}**"

    context = voice_contexts[voice_client.guild.id]
    context["seek"] = converted_timestamp
    _logger.info(
        f"Seeking to '{timestamp}' at '{voice_client.channel.name}' ({voice_client.channel.id}) "
        + f"in '{voice_client.guild.name}' ({voice_client.guild.id})"
    )
    _stop_voice_client(voice_client)
    return f"Seeking to **{timestamp}**"


async def replay(voice_client: VoiceClient):
    if is_playlist_empty(voice_client.guild.id):
        return "There is nothing to play!"

    if not is_idle(voice_client):
        return "The player is already playing!"

    context = voice_contexts[voice_client.guild.id]
    context["replay"] = True
    _logger.info(
        f"Replayed playlist at '{voice_client.channel.name}' ({voice_client.channel.id}) "
        + f"in '{voice_client.guild.name}' ({voice_client.guild.id})"
    )
    await decide_next_track(voice_client)
    return "Replaying last playlist."


def export_playlist(voice_client: VoiceClient):
    context = voice_contexts[voice_client.guild.id]

    if not context["playlist"]:
        return None

    result = ""
    for item in context["playlist"]:
        tags = item["tags"]
        if tags:
            if tags["title"]:
                result = result + f"# {tags['title']}"
                if tags["artist"]:
                    result = result + f" - {tags['artist']}"
                result = result + "\n"
        result = result + f"{item['url']}\n\n"

    _logger.info(
        f"Exported {len(context['playlist'])} "
        + f"{'items' if len(context['playlist']) > 1 else 'item'} of the playlist. "
        + f"guild_id: {voice_client.guild.id}"
    )
    debug_result = result.replace("\n", " ")
    debug_result = debug_result.replace("\r", " ")
    _logger.debug(
        f"Exported {len(context['playlist'])} "
        + f"{'items' if len(context['playlist']) > 1 else 'item'} of the playlist. "
        + f"guild_id: {voice_client.guild.id} result: {debug_result}"
    )
    return result


async def import_playlist(voice_client: VoiceClient, input: str):
    ignore_playlist = is_playing_radio_or_tv(voice_client) or is_idle(voice_client)

    if ignore_playlist:
        clear_playlist(voice_client.guild.id, radio_tv=False)

    count = 0
    for item in input.split("\n"):
        if item.startswith("#") or not validate_input(item):
            continue
        add_to_playlist(voice_client.guild.id, item)
        count = count + 1

    _logger.info(
        f"Imported {count} {'links' if count > 1 else 'link'} to the playlist. "
        + f"guild_id: {voice_client.guild.id}"
    )
    debug_input = input.replace("\n", " ")
    debug_input = debug_input.replace("\r", " ")
    _logger.debug(
        f"Imported {count} {'links' if count > 1 else 'link'} to the playlist. "
        + f"guild_id: {voice_client.guild.id} input: {debug_input}"
    )

    if ignore_playlist:
        if voice_client.is_playing() or voice_client.is_paused():
            _stop_voice_client(voice_client)
            await wait_until_deciding_next_track_is_finished(voice_client, 5)
        else:
            await decide_next_track(voice_client)

    return f"Added **{count}** {'links' if count > 1 else 'link'} to the playlist."


def set_active_text_channel(voice_client, channel_id):
    status_msg = status_messages.get(voice_client.guild.id)
    if status_msg:
        status_msg["channel_id"] = channel_id
    else:
        status_messages[voice_client.guild.id] = {
            "last_channel_id": None,
            "channel_id": channel_id,
            "message_id": None,
        }


async def update_status_text(voice_client: VoiceClient):
    status_msg = status_messages.get(voice_client.guild.id)
    if not status_msg:
        return

    try:
        if status_msg["message_id"]:  # Delete previous status message
            try:
                channel = client.get_channel(status_msg["last_channel_id"])
                message = await channel.fetch_message(status_msg["message_id"])
                await message.delete()
                status_messages[voice_client.guild.id]["message_id"] = None
                _logger.debug(
                    f"Deleted old playback status message. guild_id: {voice_client.guild.id} "
                    + f"channel: '{channel.name}' ({channel.id})"
                )
            except Exception:
                _logger.exception(
                    "Exception occured while deleting previous status message. "
                    + f"guild_id: {voice_client.guild.id}"
                )

        # Send new status message
        channel = client.get_channel(status_msg["channel_id"])
        status = generate_playback_status_text(voice_client.guild.id)
        sent_message = await channel.send(status)
        status_messages[voice_client.guild.id]["last_channel_id"] = channel.id
        status_messages[voice_client.guild.id]["message_id"] = sent_message.id
        _logger.debug(
            f"Sent new playback status message. guild_id: {voice_client.guild.id} "
            + f"channel: '{channel.name}' ({channel.id}) message: '{status}'"
        )
    except Exception:
        _logger.exception(
            "Exception occured while updating status message. "
            + f"guild_id: {voice_client.guild.id}"
        )


def is_idle(voice_client: VoiceClient):
    try:
        idle = voice_contexts[voice_client.guild.id]["idle"]
        if not idle:
            idle = not (voice_client.is_playing() or voice_client.is_paused())
        return idle
    except Exception:
        return True


def is_playlist_empty(guild_id: int):
    return get_playlist_size(guild_id) == 0


def is_playing_radio_or_tv(voice_client: VoiceClient):
    context = voice_contexts[voice_client.guild.id]
    return context["radio/tv"]


def is_playing_live_stream(voice_client: VoiceClient):
    current = get_current_track(voice_client.guild.id)
    if not current:
        return False
    if current["tags"]["duration"]:
        return False
    return True


def validate_input(input: str):
    input = input.strip()
    if (
        input.startswith("http://")
        or input.startswith("https://")
        or input.startswith("rtmp://")
        or input.startswith("rtmps://")
        or input.startswith("ftp://")
    ):
        return True

    return False


async def get_input_tags(input: str, forced_title: str = None):
    try:
        input = input.strip()
        proxy_option = _generate_ffmpeg_http_proxy_option(input)

        if proxy_option == "":
            process = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                "-timeout",
                "5000000",  # 5 seconds
                input,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            process = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                "-timeout",
                "5000000",  # 5 seconds
                proxy_option.strip().split()[0],
                proxy_option.strip().split()[1],
                input,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

        stdout, stderr = await process.communicate()
        output = stdout.decode("utf-8").strip()
        error = stderr.decode("utf-8").strip()
        metadata = json.loads(output)
        if metadata == {}:
            raise Exception("Probing did not succeed.")
    except Exception:
        _logger.warning(
            f"Exception occurred while probing the input: '{input}'. "
            + f"stderr: '{error}'"
        )
        return None

    _logger.debug(f"Probing for '{input}' finished. result: {metadata}")

    if not metadata["format"]:
        return None

    duration = None
    try:
        duration = float(metadata["format"].get("duration"))
        if duration == 0:
            duration = None
    except Exception:
        pass

    title = None
    artist = None
    stream_title = None

    if metadata["format"].get("tags"):
        title = metadata["format"]["tags"].get("title")
        artist = metadata["format"]["tags"].get("artist")
        stream_title = metadata["format"]["tags"].get("StreamTitle")

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
        info = f"‎{title} - {artist}"
    elif title:
        info = f"‎{title} - [unknown artist]"
    elif artist:
        info = f"‎[unknown title] - {artist}"
    elif stream_title:
        info = f"‎{stream_title}"

    if include_duration and duration:
        info = (
            info
            + "‎ ["  # Left-to-right mark
            + str(int(duration / 60))
            + ":"
            + "{:02d}]".format(int(duration % 60))
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


# Only for debugging purposes
def log_status():
    for voice_client in client.voice_clients:
        try:
            context = voice_contexts[voice_client.guild.id]
            _logger.debug(
                f"Status in {voice_client.guild.id}: is_playing: {voice_client.is_playing()} "
                + f"context: {context}"
            )
        except Exception:
            pass
