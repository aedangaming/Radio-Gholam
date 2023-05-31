import logging
from bot import client, is_guild_allowed
from nextcord import (
    Interaction,
    SlashOption,
    VoiceChannel,
    VoiceClient,
)
from stations import (
    get_radio_station_names,
    get_radio_station_url,
    get_tv_station_names,
    get_tv_station_url,
)
import music_player
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
        _logger.info(
            f"Command 'radio' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)}) "
            + f"station: '{station}'"
        )
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            _logger.debug(
                f"Guild was not allowed: '{interaction.guild.name}' ({str(interaction.guild_id)})"
            )
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if the user is in a voice channel
        if interaction.user.voice is None:
            _logger.debug(
                f"User was not in a voice channel: '{interaction.user.name}' ({str(interaction.user.id)})"
            )
            await interaction.send(
                "You must be in a voice channel to use this command.", ephemeral=True
            )
            return

        interaction_response = await interaction.send("Tuning...")

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = (
            await music_player.connect_or_get_connected_voice_client(user_voice_channel)
        )

        if not voice_client:
            _logger.debug(
                f"Could not connect to the voice channel. Maybe the bot's permissions are insufficient. "
                + f"Voice channel: '{user_voice_channel.name}' ({str(user_voice_channel.id)}) "
                + f"guild_id: {str(user_voice_channel.guild.id)}"
            )
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        result_message = await music_player.play(
            voice_client, get_radio_station_url(station), forced_title=station
        )
        await interaction_response.edit(content=result_message)

    except Exception:
        _logger.exception("Exception occurred in the 'radio' command.")
        # await music_player.disconnect_voice_client(voice_client)
        try:
            await interaction_response.edit(content=f"Operation failed.")
        except Exception:
            _logger.exception(
                "Exception occurred when sending an error message to the user."
            )


@client.slash_command(name="tv", description="Play a TV station")
async def tv(
    interaction: Interaction,
    station: str = SlashOption(
        name="station", required=True, choices=get_tv_station_names()
    ),
):
    try:
        _logger.info(
            f"Command 'tv' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)}) "
            + f"station: '{station}'"
        )
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            _logger.debug(
                f"Guild was not allowed: '{interaction.guild.name}' ({str(interaction.guild_id)})"
            )
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if the user is in a voice channel
        if interaction.user.voice is None:
            _logger.debug(
                f"User was not in a voice channel: '{interaction.user.name}' ({str(interaction.user.id)})"
            )
            await interaction.send(
                "You must be in a voice channel to use this command.", ephemeral=True
            )
            return

        interaction_response = await interaction.send("Tuning...")

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = (
            await music_player.connect_or_get_connected_voice_client(user_voice_channel)
        )

        if not voice_client:
            _logger.debug(
                f"Could not connect to the voice channel. Maybe the bot's permissions are insufficient. "
                + f"Voice channel: '{user_voice_channel.name}' ({str(user_voice_channel.id)}) "
                + f"guild_id: {str(user_voice_channel.guild.id)}"
            )
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        result_message = await music_player.play(
            voice_client, get_tv_station_url(station), forced_title=station
        )
        await interaction_response.edit(content=result_message)

    except Exception:
        _logger.exception("Exception occurred in the 'tv' command.")
        # await music_player.disconnect_voice_client(voice_client)
        try:
            await interaction_response.edit(content=f"Operation failed.")
        except Exception:
            _logger.exception(
                "Exception occurred when sending an error message to the user."
            )


@client.slash_command(name="play", description="Play a link")
async def play(
    interaction: Interaction, input: str = SlashOption(name="link", required=True)
):
    try:
        _logger.info(
            f"Command 'play' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)}) "
            + f"input: '{input}'"
        )
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            _logger.debug(
                f"Guild was not allowed: '{interaction.guild.name}' ({str(interaction.guild_id)})"
            )
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if the user is in a voice channel
        if interaction.user.voice is None:
            _logger.debug(
                f"User was not in a voice channel: '{interaction.user.name}' ({str(interaction.user.id)})"
            )
            await interaction.send(
                "You must be in a voice channel to use this command.", ephemeral=True
            )
            return

        interaction_response = await interaction.send("Please wait...")

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = (
            await music_player.connect_or_get_connected_voice_client(user_voice_channel)
        )

        if not voice_client:
            _logger.debug(
                f"Could not connect to the voice channel. Maybe the bot's permissions are insufficient. "
                + f"Voice channel: '{user_voice_channel.name}' ({str(user_voice_channel.id)}) "
                + f"guild_id: {str(user_voice_channel.guild.id)}"
            )
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        result_message = await music_player.play(voice_client, input)
        await interaction_response.edit(content=result_message)

    except Exception:
        _logger.exception("Exception occurred in the 'play' command.")
        # await music_player.disconnect_voice_client(voice_client)
        try:
            await interaction_response.edit(content=f"Operation failed.")
        except Exception:
            _logger.exception(
                "Exception occurred when sending an error message to the user."
            )


@client.slash_command(name="stop", description="Stop playing")
async def stop(interaction: Interaction):
    try:
        _logger.info(
            f"Command 'stop' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)})"
        )
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            _logger.debug(
                f"Guild was not allowed: '{interaction.guild.name}' ({str(interaction.guild_id)})"
            )
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if the user is in the same voice channel
        if interaction.user.voice is None:
            _logger.debug(
                f"User was not in a voice channel: '{interaction.user.name}' ({str(interaction.user.id)})"
            )
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            _logger.debug(
                f"No active voice client was found for the guild "
                + f"'{interaction.guild.name}' ({interaction.guild_id}). "
                + f"Invalid command: 'stop'"
            )
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        if user_voice_channel.id != voice_client.channel.id:
            _logger.debug(
                f"User was in a different voice channel than the bot. "
                + f"User: '{interaction.user.name}' ({str(interaction.user.id)}) "
                + f"is in '{user_voice_channel.name}' ({str(user_voice_channel.id)}) "
                + f"Bot is in '{voice_client.channel.name}' ({str(voice_client.channel.id)})"
            )
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interaction_response = await interaction.send("Stopping...")
        result_message = await music_player.stop(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        _logger.exception("Exception occurred in the 'stop' command.")
        try:
            await interaction_response.edit(content=f"Operation failed.")
        except Exception:
            _logger.exception(
                "Exception occurred when sending an error message to the user."
            )


@client.slash_command(name="next", description="Play the next track in the playlist")
async def next(interaction: Interaction):
    try:
        _logger.info(
            f"Command 'next' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)})"
        )
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            _logger.debug(
                f"Guild was not allowed: '{interaction.guild.name}' ({str(interaction.guild_id)})"
            )
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if the user is in the same voice channel
        if interaction.user.voice is None:
            _logger.debug(
                f"User was not in a voice channel: '{interaction.user.name}' ({str(interaction.user.id)})"
            )
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            _logger.debug(
                f"No active voice client was found for the guild "
                + f"'{interaction.guild.name}' ({interaction.guild_id}). "
                + f"Invalid command: 'next'"
            )
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        if user_voice_channel.id != voice_client.channel.id:
            _logger.debug(
                f"User was in a different voice channel than the bot. "
                + f"User: '{interaction.user.name}' ({str(interaction.user.id)}) "
                + f"is in '{user_voice_channel.name}' ({str(user_voice_channel.id)}) "
                + f"Bot is in '{voice_client.channel.name}' ({str(voice_client.channel.id)})"
            )
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interaction_response = await interaction.send("Skipping...")
        result_message = await music_player.next(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        _logger.exception("Exception occurred in the 'next' command.")
        try:
            await interaction_response.edit(content=f"Operation failed.")
        except Exception:
            _logger.exception(
                "Exception occurred when sending an error message to the user."
            )


@client.slash_command(
    name="previous", description="Play the previous track in the playlist"
)
async def previous(interaction: Interaction):
    try:
        _logger.info(
            f"Command 'previous' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)})"
        )
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            _logger.debug(
                f"Guild was not allowed: '{interaction.guild.name}' ({str(interaction.guild_id)})"
            )
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if the user is in the same voice channel
        if interaction.user.voice is None:
            _logger.debug(
                f"User was not in a voice channel: '{interaction.user.name}' ({str(interaction.user.id)})"
            )
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            _logger.debug(
                f"No active voice client was found for the guild "
                + f"'{interaction.guild.name}' ({interaction.guild_id}). "
                + f"Invalid command: 'previous'"
            )
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        if user_voice_channel.id != voice_client.channel.id:
            _logger.debug(
                f"User was in a different voice channel than the bot. "
                + f"User: '{interaction.user.name}' ({str(interaction.user.id)}) "
                + f"is in '{user_voice_channel.name}' ({str(user_voice_channel.id)}) "
                + f"Bot is in '{voice_client.channel.name}' ({str(voice_client.channel.id)})"
            )
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interaction_response = await interaction.send("Rewinding...")
        result_message = await music_player.previous(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        _logger.exception("Exception occurred in the 'previous' command.")
        try:
            await interaction_response.edit(content=f"Operation failed.")
        except Exception:
            _logger.exception(
                "Exception occurred when sending an error message to the user."
            )


@client.slash_command(name="loop", description="Repeat the playlist or a single track")
async def loop(
    interaction: Interaction,
    loop: str = SlashOption(
        name="loop", choices=["playlist", "track", "disabled"], required=True
    ),
):
    try:
        _logger.info(
            f"Command 'loop' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)}) loop: '{loop}'"
        )
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            _logger.debug(
                f"Guild was not allowed: '{interaction.guild.name}' ({str(interaction.guild_id)})"
            )
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if the user is in the same voice channel
        if interaction.user.voice is None:
            _logger.debug(
                f"User was not in a voice channel: '{interaction.user.name}' ({str(interaction.user.id)})"
            )
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            _logger.debug(
                f"No active voice client was found for the guild "
                + f"'{interaction.guild.name}' ({interaction.guild_id}). "
                + f"Invalid command: 'loop'"
            )
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        if user_voice_channel.id != voice_client.channel.id:
            _logger.debug(
                f"User was in a different voice channel than the bot. "
                + f"User: '{interaction.user.name}' ({str(interaction.user.id)}) "
                + f"is in '{user_voice_channel.name}' ({str(user_voice_channel.id)}) "
                + f"Bot is in '{voice_client.channel.name}' ({str(voice_client.channel.id)})"
            )
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interaction_response = await interaction.send("Please wait...")
        result_message = music_player.loop(voice_client, loop)
        await interaction_response.edit(content=result_message)

    except Exception:
        _logger.exception("Exception occurred in the 'loop' command.")
        try:
            await interaction_response.edit(content=f"Operation failed.")
        except Exception:
            _logger.exception(
                "Exception occurred when sending an error message to the user."
            )


@client.slash_command(name="shuffle", description="Shuffles current playlist")
async def shuffle(interaction: Interaction):
    try:
        _logger.info(
            f"Command 'shuffle' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)})"
        )
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            _logger.debug(
                f"Guild was not allowed: '{interaction.guild.name}' ({str(interaction.guild_id)})"
            )
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if the user is in the same voice channel
        if interaction.user.voice is None:
            _logger.debug(
                f"User was not in a voice channel: '{interaction.user.name}' ({str(interaction.user.id)})"
            )
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            _logger.debug(
                f"No active voice client was found for the guild "
                + f"'{interaction.guild.name}' ({interaction.guild_id}). "
                + f"Invalid command: 'shuffle'"
            )
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        if user_voice_channel.id != voice_client.channel.id:
            _logger.debug(
                f"User was in a different voice channel than the bot. "
                + f"User: '{interaction.user.name}' ({str(interaction.user.id)}) "
                + f"is in '{user_voice_channel.name}' ({str(user_voice_channel.id)}) "
                + f"Bot is in '{voice_client.channel.name}' ({str(voice_client.channel.id)})"
            )
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interaction_response = await interaction.send("Please wait...")
        result_message = music_player.shuffle(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        _logger.exception("Exception occurred in the 'shuffle' command.")
        try:
            await interaction_response.edit(content=f"Operation failed.")
        except Exception:
            _logger.exception(
                "Exception occurred when sending an error message to the user."
            )


@client.slash_command(name="pause", description="Pause playback")
async def pause(interaction: Interaction):
    try:
        _logger.info(
            f"Command 'pause' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)})"
        )
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            _logger.debug(
                f"Guild was not allowed: '{interaction.guild.name}' ({str(interaction.guild_id)})"
            )
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if the user is in the same voice channel
        if interaction.user.voice is None:
            _logger.debug(
                f"User was not in a voice channel: '{interaction.user.name}' ({str(interaction.user.id)})"
            )
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            _logger.debug(
                f"No active voice client was found for the guild "
                + f"'{interaction.guild.name}' ({interaction.guild_id}). "
                + f"Invalid command: 'pause'"
            )
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        if user_voice_channel.id != voice_client.channel.id:
            _logger.debug(
                f"User was in a different voice channel than the bot. "
                + f"User: '{interaction.user.name}' ({str(interaction.user.id)}) "
                + f"is in '{user_voice_channel.name}' ({str(user_voice_channel.id)}) "
                + f"Bot is in '{voice_client.channel.name}' ({str(voice_client.channel.id)})"
            )
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interaction_response = await interaction.send("Please wait...")
        result_message = music_player.pause(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        _logger.exception("Exception occurred in the 'pause' command.")
        try:
            await interaction_response.edit(content=f"Operation failed.")
        except Exception:
            _logger.exception(
                "Exception occurred when sending an error message to the user."
            )


@client.slash_command(name="resume", description="Resume playback")
async def resume(interaction: Interaction):
    try:
        _logger.info(
            f"Command 'resume' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)})"
        )
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            _logger.debug(
                f"Guild was not allowed: '{interaction.guild.name}' ({str(interaction.guild_id)})"
            )
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if the user is in the same voice channel
        if interaction.user.voice is None:
            _logger.debug(
                f"User was not in a voice channel: '{interaction.user.name}' ({str(interaction.user.id)})"
            )
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            _logger.debug(
                f"No active voice client was found for the guild "
                + f"'{interaction.guild.name}' ({interaction.guild_id}). "
                + f"Invalid command: 'resume'"
            )
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        if user_voice_channel.id != voice_client.channel.id:
            _logger.debug(
                f"User was in a different voice channel than the bot. "
                + f"User: '{interaction.user.name}' ({str(interaction.user.id)}) "
                + f"is in '{user_voice_channel.name}' ({str(user_voice_channel.id)}) "
                + f"Bot is in '{voice_client.channel.name}' ({str(voice_client.channel.id)})"
            )
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interaction_response = await interaction.send("Please wait...")
        result_message = music_player.resume(voice_client)
        await interaction_response.edit(content=result_message)

    except Exception:
        _logger.exception("Exception occurred in the 'resume' command.")
        try:
            await interaction_response.edit(content=f"Operation failed.")
        except Exception:
            _logger.exception(
                "Exception occurred when sending an error message to the user."
            )


@client.slash_command(name="seek", description="Seek to a specific timestamp")
async def seek(
    interaction: Interaction,
    timestamp: str = SlashOption(
        name="timestamp", required=True, description="e.g. 130 , 2:10"
    ),
):
    try:
        _logger.info(
            f"Command 'seek' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)}) timestamp: '{timestamp}'"
        )
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            _logger.debug(
                f"Guild was not allowed: '{interaction.guild.name}' ({str(interaction.guild_id)})"
            )
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if the user is in the same voice channel
        if interaction.user.voice is None:
            _logger.debug(
                f"User was not in a voice channel: '{interaction.user.name}' ({str(interaction.user.id)})"
            )
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            _logger.debug(
                f"No active voice client was found for the guild "
                + f"'{interaction.guild.name}' ({interaction.guild_id}). "
                + f"Invalid command: 'seek'"
            )
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        if user_voice_channel.id != voice_client.channel.id:
            _logger.debug(
                f"User was in a different voice channel than the bot. "
                + f"User: '{interaction.user.name}' ({str(interaction.user.id)}) "
                + f"is in '{user_voice_channel.name}' ({str(user_voice_channel.id)}) "
                + f"Bot is in '{voice_client.channel.name}' ({str(voice_client.channel.id)})"
            )
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interaction_response = await interaction.send("Please wait...")
        result_message = music_player.seek(voice_client, timestamp)
        await interaction_response.edit(content=result_message)

    except Exception:
        _logger.exception("Exception occurred in the 'seek' command.")
        try:
            await interaction_response.edit(content=f"Operation failed.")
        except Exception:
            _logger.exception(
                "Exception occurred when sending an error message to the user."
            )


@client.slash_command(name="about", description="About Radio Gholam")
async def about(interaction: Interaction):
    try:
        _logger.info(
            f"Command 'about' called by '{interaction.user.name}' ({str(interaction.user.id)}) "
            + f"in '{interaction.guild.name}' ({str(interaction.guild_id)})"
        )
        await interaction.send(f"Radio Gholam v{VERSION} az **Aedan Gaming**.")
    except Exception:
        _logger.exception("Exception occurred in the 'about' command.")
