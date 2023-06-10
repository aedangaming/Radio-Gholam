import io
import logging
from nextcord import (
    Interaction,
    SlashOption,
    VoiceChannel,
    VoiceClient,
    PartialInteractionMessage,
    Attachment,
    File,
)

import music_player
from bot import client, is_guild_allowed
from stations import (
    get_radio_station_names,
    get_radio_station_url,
    get_tv_station_names,
    get_tv_station_url,
)
from version import VERSION

_logger = logging.getLogger("main")


@client.slash_command(name="radio", description="Play a radio station")
async def radio(
    interaction: Interaction,
    station: str = SlashOption(
        name="station", required=True, choices=get_radio_station_names()
    ),
):
    try:
        if not await initial_checks_for_play_commands(interaction, "radio", station):
            return

        interaction_response = await interaction.send("Tuning...")

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = (
            await music_player.connect_or_get_connected_voice_client(user_voice_channel)
        )

        if not voice_client:
            _logger.debug(
                f"Could not connect to the voice channel. Maybe the bot's permissions are insufficient. "
                + f"Voice channel: '{user_voice_channel.name}' ({user_voice_channel.id}) "
                + f"guild_id: {user_voice_channel.guild.id}"
            )
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = await music_player.play(
            voice_client,
            get_radio_station_url(station),
            radio_tv=True,
            forced_title=station,
        )
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "radio")


@client.slash_command(name="tv", description="Play a TV station")
async def tv(
    interaction: Interaction,
    station: str = SlashOption(
        name="station", required=True, choices=get_tv_station_names()
    ),
):
    try:
        if not await initial_checks_for_play_commands(interaction, "tv", station):
            return

        interaction_response = await interaction.send("Tuning...")

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = (
            await music_player.connect_or_get_connected_voice_client(user_voice_channel)
        )

        if not voice_client:
            _logger.debug(
                f"Could not connect to the voice channel. Maybe the bot's permissions are insufficient. "
                + f"Voice channel: '{user_voice_channel.name}' ({user_voice_channel.id}) "
                + f"guild_id: {user_voice_channel.guild.id}"
            )
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = await music_player.play(
            voice_client,
            get_tv_station_url(station),
            radio_tv=True,
            forced_title=station,
        )
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "tv")


@client.slash_command(name="play", description="Play a link")
async def play(
    interaction: Interaction,
    input: str = SlashOption(name="link", required=True),
    starting_timestamp: str = SlashOption(
        name="timestamp", required=False, description="e.g. 130 , 2:10"
    ),
):
    try:
        if not await initial_checks_for_play_commands(
            interaction, "play", input, f"starting_timestamp: {starting_timestamp}"
        ):
            return

        interaction_response = await interaction.send("Please wait...")

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = (
            await music_player.connect_or_get_connected_voice_client(user_voice_channel)
        )

        if not voice_client:
            _logger.debug(
                f"Could not connect to the voice channel. Maybe the bot's permissions are insufficient. "
                + f"Voice channel: '{user_voice_channel.name}' ({user_voice_channel.id}) "
                + f"guild_id: {user_voice_channel.guild.id}"
            )
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = await music_player.play(
            voice_client, input, radio_tv=False, starting_timestamp=starting_timestamp
        )
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "play")


@client.slash_command(name="stop", description="Stop playing")
async def stop(interaction: Interaction):
    try:
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if not await initial_command_checks(interaction, voice_client, "stop"):
            return

        interaction_response = await interaction.send("Stopping...")
        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = await music_player.stop(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "stop")


@client.slash_command(name="next", description="Play the next track in the playlist")
async def next(interaction: Interaction):
    try:
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if not await initial_command_checks(interaction, voice_client, "next"):
            return

        if not await is_command_allowed_on_radio_and_tv_streams(
            interaction, voice_client, "next"
        ):
            return

        interaction_response = await interaction.send("Skipping...")
        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = await music_player.next(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "next")


@client.slash_command(
    name="previous", description="Play the previous track in the playlist"
)
async def previous(interaction: Interaction):
    try:
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if not await initial_command_checks(interaction, voice_client, "previous"):
            return

        if not await is_command_allowed_on_radio_and_tv_streams(
            interaction, voice_client, "previous"
        ):
            return

        interaction_response = await interaction.send("Rewinding...")
        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = await music_player.previous(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "previous")


@client.slash_command(name="loop", description="Repeat the playlist or a single track")
async def loop(
    interaction: Interaction,
    loop: str = SlashOption(
        name="loop", choices=["playlist", "track", "disabled"], required=True
    ),
):
    try:
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if not await initial_command_checks(
            interaction, voice_client, "loop", f"loop: '{loop}'"
        ):
            return

        if not await is_command_allowed_on_radio_and_tv_streams(
            interaction, voice_client, "loop"
        ):
            return

        interaction_response = await interaction.send("Please wait...")
        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = music_player.loop(voice_client, loop)
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "loop")


@client.slash_command(name="shuffle", description="Shuffles current playlist")
async def shuffle(interaction: Interaction):
    try:
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if not await initial_command_checks(interaction, voice_client, "shuffle"):
            return

        if not await is_command_allowed_on_radio_and_tv_streams(
            interaction, voice_client, "shuffle"
        ):
            return

        interaction_response = await interaction.send("Please wait...")
        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = music_player.shuffle(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "shuffle")


@client.slash_command(name="pause", description="Pause playback")
async def pause(interaction: Interaction):
    try:
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if not await initial_command_checks(interaction, voice_client, "pause"):
            return

        if not await is_command_allowed_on_radio_and_tv_streams(
            interaction, voice_client, "pause"
        ):
            return

        interaction_response = await interaction.send("Please wait...")
        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = music_player.pause(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "pause")


@client.slash_command(name="resume", description="Resume playback")
async def resume(interaction: Interaction):
    try:
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if not await initial_command_checks(interaction, voice_client, "resume"):
            return

        if not await is_command_allowed_on_radio_and_tv_streams(
            interaction, voice_client, "resume"
        ):
            return

        interaction_response = await interaction.send("Please wait...")
        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = music_player.resume(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "resume")


@client.slash_command(name="seek", description="Seek to a specific timestamp")
async def seek(
    interaction: Interaction,
    timestamp: str = SlashOption(
        name="timestamp", required=True, description="e.g. 130 , 2:10"
    ),
):
    try:
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if not await initial_command_checks(
            interaction, voice_client, "seek", f"timestamp: '{timestamp}'"
        ):
            return

        if not await is_command_allowed_on_radio_and_tv_streams(
            interaction, voice_client, "seek"
        ):
            return

        interaction_response = await interaction.send("Please wait...")
        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = music_player.seek(voice_client, timestamp)
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "seek")


@client.slash_command(name="export", description="Export current playlist as a file")
async def export_playlist(interaction: Interaction):
    try:
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if not await initial_command_checks(interaction, voice_client, "export"):
            return

        if not await is_command_allowed_on_radio_and_tv_streams(
            interaction, voice_client, "export"
        ):
            return

        interaction_response = await interaction.send("Please wait...")
        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result = music_player.export_playlist(voice_client)
        file = File(io.BytesIO(bytes(result, "utf-8")), "playlist.txt")
        await interaction_response.edit(
            content="The playlist has been exported.", files=[file]
        )

    except Exception:
        await handle_command_exception(interaction, interaction_response, "export")


@client.slash_command(name="import", description="Import playlist from a file")
async def import_playlist(interaction: Interaction, playlist_file: Attachment):
    try:
        if not await initial_checks_for_play_commands(
            interaction,
            "import",
            f"attachment: {playlist_file.filename} {playlist_file.size} Bytes",
        ):
            return

        interaction_response = await interaction.send("Please wait...")

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = (
            await music_player.connect_or_get_connected_voice_client(user_voice_channel)
        )

        if not voice_client:
            _logger.debug(
                f"Could not connect to the voice channel. Maybe the bot's permissions are insufficient. "
                + f"Voice channel: '{user_voice_channel.name}' ({user_voice_channel.id}) "
                + f"guild_id: {user_voice_channel.guild.id}"
            )
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        file_contents_bytes = await playlist_file.read()
        file_contents_str = file_contents_bytes.decode(errors="ignore")
        music_player.set_active_text_channel(voice_client, interaction.channel_id)
        result_message = await music_player.import_playlist(
            voice_client, file_contents_str
        )
        await interaction_response.edit(content=result_message)

    except Exception:
        await handle_command_exception(interaction, interaction_response, "import")


@client.slash_command(name="about", description="About Radio Gholam")
async def about(interaction: Interaction):
    try:
        _logger.info(
            f"Command 'about' called by '{interaction.user.name}' ({interaction.user.id}) "
            + f"in '{interaction.guild.name}' ({interaction.guild_id})"
        )
        await interaction.send(f"Radio Gholam v{VERSION} az **Aedan Gaming**.")
    except Exception:
        _logger.exception("Exception occurred in the 'about' command.")


async def initial_checks_for_play_commands(
    interaction: Interaction,
    command_name: str,
    input: str,
    command_args: str = None,
):
    _logger.info(
        f"Command '{command_name}' called by '{interaction.user.name}' ({interaction.user.id}) "
        + f"in '{interaction.guild.name}' ({interaction.guild_id}) input: '{input}' command_args: {command_args}"
    )
    # Check if the guild is allowed
    if not is_guild_allowed(interaction.guild_id):
        _logger.debug(
            f"Guild was not allowed: '{interaction.guild.name}' ({interaction.guild_id})"
        )
        await interaction.send(
            "This command is not allowed on this server.", ephemeral=True
        )
        return False

    # Check if the user is in a voice channel
    if interaction.user.voice is None:
        _logger.debug(
            f"User was not in a voice channel: '{interaction.user.name}' ({interaction.user.id})"
        )
        await interaction.send(
            "You must be in a voice channel to use this command.", ephemeral=True
        )
        return False

    if command_name == "play":
        if not music_player.validate_input(input):
            _logger.debug(f"User input was not valid: '{input}'")
            await interaction.send("Your input is not a valid link.", ephemeral=True)
            return False

    return True


async def initial_command_checks(
    interaction: Interaction,
    voice_client: VoiceClient,
    command_name: str,
    command_args: str = None,
):
    _logger.info(
        f"Command '{command_name}' called by '{interaction.user.name}' ({interaction.user.id}) "
        + f"in '{interaction.guild.name}' ({interaction.guild_id}) command_args: {command_args}"
    )
    # Check if the guild is allowed
    if not is_guild_allowed(interaction.guild_id):
        _logger.debug(
            f"Guild was not allowed: '{interaction.guild.name}' ({interaction.guild_id})"
        )
        await interaction.send(
            "This command is not allowed on this server.", ephemeral=True
        )
        return False

    # Check if the user is in the same voice channel
    if interaction.user.voice is None:
        _logger.debug(
            f"User was not in a voice channel: '{interaction.user.name}' ({interaction.user.id})"
        )
        await interaction.send(
            "You must be in the target voice channel to use this command.",
            ephemeral=True,
        )
        return False

    user_voice_channel: VoiceChannel = interaction.user.voice.channel

    if voice_client is None:
        _logger.debug(
            f"No active voice client was found for the guild "
            + f"'{interaction.guild.name}' ({interaction.guild_id}). "
            + f"Invalid command: '{command_name}'"
        )
        await interaction.send("Play something first!", ephemeral=True)
        return False

    if user_voice_channel.id != voice_client.channel.id:
        _logger.debug(
            f"User was in a different voice channel than the bot. "
            + f"User: '{interaction.user.name}' ({interaction.user.id}) "
            + f"is in '{user_voice_channel.name}' ({user_voice_channel.id}) "
            + f"Bot is in '{voice_client.channel.name}' ({voice_client.channel.id})"
        )
        await interaction.send(
            "You must be in the same voice channel as Radio Gholam is.",
            ephemeral=True,
        )
        return False

    return True


async def is_command_allowed_on_radio_and_tv_streams(
    interaction: Interaction, voice_client: VoiceClient, command_name: str
):
    if music_player.is_playlist_empty(voice_client):
        _logger.debug(
            f"Cannot perform '{command_name}' command when the playlist is empty. "
            + f"guild_id: {voice_client.guild.id}"
        )
        await interaction.send("Play something first!", ephemeral=True)
        return False

    if music_player.is_playing_radio_or_tv(voice_client):
        _logger.debug(
            f"Cannot perform '{command_name}' command while playing Radio or a TV station. "
            + f"guild_id: {voice_client.guild.id}"
        )
        await interaction.send(
            f"Cannot perform this command while playing Radio or a TV station.",
            ephemeral=True,
        )
        return False

    return True


async def handle_command_exception(
    interaction: Interaction,
    interaction_response: PartialInteractionMessage,
    command_name: str,
):
    _logger.exception(f"Exception occurred in the '{command_name}' command.")
    try:
        if interaction_response:
            await interaction_response.edit(content=f"Operation failed.")
        else:
            await interaction.send(content=f"Operation failed.")
    except Exception:
        _logger.exception(
            "Exception occurred when sending an error message to the user."
        )
