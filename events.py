import logging
from nextcord import Member, VoiceState
from nextcord.ext import tasks

from bot import client
from music_player import (
    continue_playing_moved_voice_client,
    refresh_playback_or_disconnect_idle_voice_clients,
    log_status,
)

_logger = logging.getLogger("main")


@client.event
async def on_ready():
    _logger.info(f"Logged in as {str(client.user)}")
    cleanup.start()
    # debug.start()  # For extra debugging


@client.event
async def on_voice_state_update(
    member: Member,
    before: VoiceState,
    after: VoiceState,
):
    await continue_playing_moved_voice_client(member, before, after)


@tasks.loop(seconds=15)
async def cleanup():
    await refresh_playback_or_disconnect_idle_voice_clients()


@tasks.loop(seconds=3)
async def debug():
    log_status()
