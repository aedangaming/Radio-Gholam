from bot import client, is_guild_allowed
from nextcord import (
    Interaction,
    SlashOption,
    FFmpegOpusAudio,
    VoiceChannel,
    VoiceClient,
)
from voicecontext_manager import (
    connect_to_voice_channel,
    disconnect_voice_client,
    get_voice_client_if_exists,
    clear_playlist,
    get_input_tags,
    generate_input_info,
)
from stations import (
    get_radio_station_names,
    get_radio_station_url,
    get_tv_station_names,
    get_tv_station_url,
)
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

        interaction_response = await interaction.send("Tuning ...")

        voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = await connect_to_voice_channel(voice_channel)

        if not voice_client:
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        clear_playlist(voice_client.guild.id)

        if voice_client.is_playing():
            voice_client.stop()

        audio_source = FFmpegOpusAudio(
            get_radio_station_url(station), before_options="-fflags discardcorrupt"
        )
        voice_client.play(audio_source)

        await interaction_response.edit(
            content=f"Now playing  | 🔴 LIVE |  **{station}**."
        )

    except Exception as e:
        print(e)
        try:
            await disconnect_voice_client(voice_client)
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

        interaction_response = await interaction.send("Tuning ...")

        voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = await connect_to_voice_channel(voice_channel)

        if not voice_client:
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        clear_playlist(voice_client.guild.id)

        if voice_client.is_playing():
            voice_client.stop()

        audio_source = FFmpegOpusAudio(
            get_tv_station_url(station), before_options="-fflags discardcorrupt"
        )
        voice_client.play(audio_source)

        await interaction_response.edit(
            content=f"Now playing  | 🔴 LIVE |  **{station}**."
        )

    except Exception as e:
        print(e)
        try:
            await disconnect_voice_client(voice_client)
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
    interaction: Interaction,
    input: str = SlashOption(name="link", required=True),
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

        interaction_response = await interaction.send("Tuning ...")

        voice_channel: VoiceChannel = interaction.user.voice.channel
        voice_client: VoiceClient = await connect_to_voice_channel(voice_channel)

        if not voice_client:
            await interaction_response.edit(
                "Cannot connect to the voice channel. Check the bot permissions."
            )
            return

        clear_playlist(voice_client.guild.id)

        if voice_client.is_playing():
            voice_client.stop()

        audio_source = FFmpegOpusAudio(input, before_options="-fflags discardcorrupt")
        voice_client.play(audio_source)

        tags = get_input_tags(input)
        await interaction_response.edit(
            content=f"Now playing {generate_input_info(input, tags)}."
        )

    except Exception as e:
        print(e)
        try:
            await disconnect_voice_client(voice_client)
        except Exception as e:
            print(e)
        try:
            await interaction_response.edit(
                content=f"Cannot play **{input}** right now."
            )
        except Exception as e:
            print(e)


# @client.slash_command(name="delsookhtegan", description="Play from Delsookhtegan")
# async def play(
#     interaction: Interaction,
#     query: str = SlashOption(name="query", required=False),
# ):
#     try:
#         # Check if the guild is allowed
#         if not is_guild_allowed(interaction.guild_id):
#             await interaction.send(
#                 "This command is not allowed on this server.", ephemeral=True
#             )
#             return

#         # Check if user is in a voice channel
#         if interaction.user.voice is None:
#             await interaction.send(
#                 "You must be in a voice channel to use this command.", ephemeral=True
#             )
#             return

#         interaction_response = await interaction.send("Tuning ...")

#         voice_channel: VoiceChannel = interaction.user.voice.channel

#         # Check if there is an active VoiceClient
#         voice_client: VoiceClient = get_voice_context_if_exists(interaction.guild_id)

#         # Connect to voice if it is not already connected.
#         if voice_client is None:
#             voice_client = await voice_channel.connect()
#         if not voice_client.is_connected():
#             await voice_client.connect()

#         store_voice_client(voice_client)

#         if voice_client.is_playing():
#             voice_client.stop()

#         audio_source = FFmpegPCMAudio(input)
#         voice_client.play(audio_source)

#         await interaction_response.edit(content=f"Now playing **{input}**.")

#     except Exception as e:
#         print(e)
#         try:
#             if voice_client is not None:
#                 await voice_client.disconnect()
#                 remove_voice_client(voice_client)
#         except Exception as e:
#             print(e)
#         try:
#             await interaction_response.edit(
#                 content=f"Cannot play **{input}** right now."
#             )
#         except Exception as e:
#             print(e)


@client.slash_command(name="stop", description="Stop playing radio")
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

        voice_client: VoiceClient = get_voice_client_if_exists(interaction.guild_id)

        if voice_client is None:
            await interaction.send("Radio is not playing...", ephemeral=True)
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel

        if user_voice_channel.id != voice_client.channel.id:
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interation_response = await interaction.send("Stopping...")

        try:
            await disconnect_voice_client(voice_client)
        except Exception as e:
            print(e)

        await interation_response.edit(content="Stopped.")
    except Exception as e:
        print(e)


@client.slash_command(name="about", description="About Radio Gholam")
async def about(interaction: Interaction):
    try:
        await interaction.send(f"Radio Gholam v{VERSION} az **Aedan Gaming**.")
    except Exception as e:
        print(e)
