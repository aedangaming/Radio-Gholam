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


@client.slash_command(name="radio", description="Play a radio station")
async def radio(
    interaction: Interaction,
    station: str = SlashOption(
        name="station", required=True, choices=get_radio_station_names()
    ),
):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if user is in a voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in a voice channel to use this command.", ephemeral=True
            )
            return

        interaction_response = await interaction.send("Tuning...")

        voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = (
            await music_player.connect_or_get_connected_voice_client(voice_channel)
        )

        if not voice_client:
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        result_message = music_player.play(
            voice_client, get_radio_station_url(station), force_title=station
        )
        await interaction_response.edit(content=result_message)

    except Exception as e:
        print(e)
        try:
            await music_player.disconnect_voice_client(voice_client)
        except Exception as e:
            print(e)
        try:
            await interaction_response.edit(
                content=f"Cannot play the station **{station}** right now."
            )
        except Exception as e:
            print(e)


@client.slash_command(name="tv", description="Play a TV station")
async def tv(
    interaction: Interaction,
    station: str = SlashOption(
        name="station", required=True, choices=get_tv_station_names()
    ),
):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if user is in a voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in a voice channel to use this command.", ephemeral=True
            )
            return

        interaction_response = await interaction.send("Tuning...")

        voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = (
            await music_player.connect_or_get_connected_voice_client(voice_channel)
        )

        if not voice_client:
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        result_message = music_player.play(
            voice_client, get_tv_station_url(station), force_title=station
        )
        await interaction_response.edit(content=result_message)

    except Exception as e:
        print(e)
        try:
            await music_player.disconnect_voice_client(voice_client)
        except Exception as e:
            print(e)
        try:
            await interaction_response.edit(
                content=f"Cannot play the station **{station}** right now."
            )
        except Exception as e:
            print(e)


@client.slash_command(name="play", description="Play a link")
async def play(
    interaction: Interaction, input: str = SlashOption(name="link", required=True)
):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if user is in a voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in a voice channel to use this command.", ephemeral=True
            )
            return

        interaction_response = await interaction.send("Please wait...")

        voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = (
            await music_player.connect_or_get_connected_voice_client(voice_channel)
        )

        if not voice_client:
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        result_message = music_player.play(voice_client, input)
        await interaction_response.edit(content=result_message)

    except Exception as e:
        print(e)
        try:
            await music_player.disconnect_voice_client(voice_client)
        except Exception as e:
            print(e)
        try:
            await interaction_response.edit(
                content=f"Cannot play **{input}** right now."
            )
        except Exception as e:
            print(e)


@client.slash_command(name="stop", description="Stop playing")
async def stop(interaction: Interaction):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if user is in the same voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel

        if user_voice_channel.id != voice_client.channel.id:
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interation_response = await interaction.send("Stopping...")
        await music_player.stop(voice_client)
        await interation_response.edit(content="Stopped.")
    except Exception as e:
        print(e)


@client.slash_command(name="next", description="Play the next track in the playlist")
async def next(interaction: Interaction):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if user is in the same voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel

        if user_voice_channel.id != voice_client.channel.id:
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interation_response = await interaction.send("Skipping...")
        result_message = await music_player.next(voice_client)
        await interation_response.edit(content=result_message)
    except Exception as e:
        print(e)


@client.slash_command(
    name="previous", description="Play the previous track in the playlist"
)
async def previous(interaction: Interaction):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if user is in the same voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel

        if user_voice_channel.id != voice_client.channel.id:
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interation_response = await interaction.send("Rewinding...")
        result_message = await music_player.previous(voice_client)
        await interation_response.edit(content=result_message)
    except Exception as e:
        print(e)


@client.slash_command(name="loop", description="Repeat the playlist or a single track")
async def loop(
    interaction: Interaction,
    loop: str = SlashOption(
        name="loop", choices=["playlist", "track", "none"], required=True
    ),
):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if user is in the same voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel

        if user_voice_channel.id != voice_client.channel.id:
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interation_response = await interaction.send("Please wait...")
        music_player.loop(voice_client, loop)
        await interation_response.edit(content=f"Loop mode: **{loop}**")
    except Exception as e:
        print(e)


@client.slash_command(name="shuffle", description="Shuffles current playlist")
async def shuffle(interaction: Interaction):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if user is in the same voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel

        if user_voice_channel.id != voice_client.channel.id:
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interation_response = await interaction.send("Please wait...")
        result = music_player.shuffle(voice_client.guild.id)
        if result:
            await interation_response.edit(
                content=f"The playlist has been **shuffled**."
            )
        else:
            await interation_response.edit(content=f"Operation failed.")
    except Exception as e:
        print(e)


@client.slash_command(name="pause", description="Pause playback")
async def pause(interaction: Interaction):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if user is in the same voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel

        if user_voice_channel.id != voice_client.channel.id:
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interation_response = await interaction.send("Please wait...")
        result = music_player.pause(voice_client)
        if result:
            await interation_response.edit(content=f"Playback has been **paused**.")
        else:
            await interation_response.edit(content=f"Operation failed.")
    except Exception as e:
        print(e)


@client.slash_command(name="resume", description="Resume playback")
async def resume(interaction: Interaction):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if user is in the same voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel

        if user_voice_channel.id != voice_client.channel.id:
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interation_response = await interaction.send("Please wait...")
        result = music_player.resume(voice_client)
        if result:
            await interation_response.edit(content=f"Playback has been **resumed**.")
        else:
            await interation_response.edit(content=f"Operation failed.")
    except Exception as e:
        print(e)


@client.slash_command(name="seek", description="Seek to a specific timestamp")
async def seek(
    interaction: Interaction,
    timestap: str = SlashOption(
        name="seek", required=True, description="e.g. 130 , 2:10"
    ),
):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        # Check if user is in the same voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        voice_client: VoiceClient = music_player.get_voice_client_if_exists(
            interaction.guild_id
        )

        if voice_client is None:
            await interaction.send("The playlist is empty.", ephemeral=True)
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel

        if user_voice_channel.id != voice_client.channel.id:
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interation_response = await interaction.send("Please wait...")
        result = music_player.seek(voice_client, timestap)
        if result:
            await interation_response.edit(content=f"Seeking to **{timestap}**")
        else:
            await interation_response.edit(content=f"Operation failed.")
    except Exception as e:
        print(e)


@client.slash_command(name="about", description="About Radio Gholam")
async def about(interaction: Interaction):
    try:
        await interaction.send(f"Radio Gholam v{VERSION} az **Aedan Gaming**.")
    except Exception as e:
        print(e)
