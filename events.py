from bot import client
from nextcord import Member, VoiceState
from music_player import continue_playing_moved_voice_client


@client.event
async def on_ready():
    print(f"Logged in as {str(client.user)}")


@client.event
async def on_voice_state_update(
    member: Member,
    before: VoiceState,
    after: VoiceState,
):
    await continue_playing_moved_voice_client(member, before, after)
