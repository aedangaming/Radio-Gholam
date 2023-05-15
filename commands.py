from bot import client, is_guild_allowed
from nextcord import Interaction, SlashOption, FFmpegPCMAudio, VoiceChannel, VoiceClient
from voiceclient_manager import (
    store_voice_client,
    remove_voice_client,
    get_voice_client_if_exists,
)
from stations import get_station_names, get_station_url
from version import VERSION


@client.slash_command(name="radio", description="Play a radio station")
async def radio(
    interaction: Interaction,
    station: str = SlashOption(
        name="station", required=True, choices=get_station_names()
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

        # Check if there is an active VoiceClient
        voice_client: VoiceClient = get_voice_client_if_exists(interaction.guild_id)

        # Connect to voice if it is not already connected.
        if voice_client is None:
            voice_client = await voice_channel.connect()
        if not voice_client.is_connected():
            await voice_client.connect()

        store_voice_client(voice_client)

        audio_source = FFmpegPCMAudio(get_station_url(station))

        if voice_client.is_playing():
            voice_client.stop()
        voice_client.play(audio_source)

        await interaction_response.edit(content=f"Now playing **{station}**.")

    except Exception as e:
        print(e)
        try:
            if voice_client is not None:
                await voice_client.disconnect()
                remove_voice_client(voice_client)
        except Exception as e:
            print(e)
        try:
            await interaction_response.edit(
                content=f"Cannot play the station **{station}** right now."
            )
        except Exception as e:
            print(e)


@client.slash_command(name="stop", description="Stop playing radio")
async def stop(interaction: Interaction):
    try:
        # Check if the guild is allowed
        if not is_guild_allowed(interaction.guild_id):
            await interaction.send(
                "This command is not allowed on this server.", ephemeral=True
            )
            return

        voice_client: VoiceClient = get_voice_client_if_exists(interaction.guild_id)

        if voice_client is None:
            await interaction.send("Radio is not playing...", ephemeral=True)
            return

        # Check if user is in the same voice channel
        if interaction.user.voice is None:
            await interaction.send(
                "You must be in the target voice channel to use this command.",
                ephemeral=True,
            )
            return

        user_voice_channel: VoiceChannel = interaction.user.voice.channel

        if user_voice_channel.id != voice_client.channel.id:
            await interaction.send(
                "You must be in the same voice channel as Radio Gholam is.",
                ephemeral=True,
            )
            return

        interation_response = await interaction.send("Stopping...")
        voice_client.stop()
        await voice_client.disconnect()
        await interation_response.edit(content="Stopped.")
        remove_voice_client(voice_client)
    except Exception as e:
        print(e)


@client.slash_command(name="about", description="About Radio Gholam")
async def about(interaction: Interaction):
    try:
        await interaction.send(f"Radio Gholam v{VERSION} az **Aedan Gaming**.")
    except Exception as e:
        print(e)
