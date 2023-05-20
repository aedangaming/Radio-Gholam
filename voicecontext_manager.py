import random
import asyncio
from bot import client
from nextcord import VoiceClient, VoiceChannel, VoiceState, Member

# Store active voice contexts, including VoiceClient and other variables like playlist
voice_contexts = {}


def get_voice_client_if_exists(guild_id: int):
    voice_client = None
    for item in client.voice_clients:
        if item.channel.guild.id == guild_id:
            voice_client = item
    return voice_client


def remove_voice_context(guild_id: int):
    if voice_contexts.get(guild_id):
        voice_contexts.pop(guild_id)


def clear_playlist(guild_id: int):
    if voice_contexts.get(guild_id):
        voice_contexts[guild_id]["playlist"] = None


def add_to_playlist(guild_id: int, item: str):
    if not voice_contexts.get(guild_id):
        voice_contexts[guild_id] = {}
    if not voice_contexts[guild_id]["playlist"]:
        voice_contexts[guild_id]["playlist"] = []
    voice_contexts[guild_id]["playlist"].append(item)


def shuffle_playlist(guild_id: int):
    new_list = []
    while len(voice_contexts[guild_id]["playlist"]) > 0:
        rand = random.randint(0, len(voice_contexts[guild_id]["playlist"]) - 1)
        new_list.append(voice_contexts[guild_id]["playlist"][rand])
        voice_contexts[guild_id]["playlist"].pop(rand)
    voice_contexts[guild_id]["playlist"] = new_list


async def connect_to_voice_channel(voice_channel: VoiceChannel):
    # Check if there is an active VoiceClient for this guild
    voice_client: VoiceClient = get_voice_client_if_exists(voice_channel.guild.id)
    try:
        # Connect to voice if it is not already connected.
        if voice_client is None:
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
    if voice_client is not None:
        await voice_client.disconnect()
        remove_voice_context(voice_client.guild.id)


# Resume playing after moving the bot between voice channels
@client.event
async def on_voice_state_update(
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
