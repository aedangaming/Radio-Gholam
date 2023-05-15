from nextcord import VoiceClient

# Store active VoiceClients
voice_clients = []


def voice_client_exists(voice_client: VoiceClient):
    for item in voice_clients:
        if item.guild.id == voice_client.guild.id:
            return True
    return False


def get_voice_client_if_exists(guild_id: int):
    for item in voice_clients:
        if item.guild.id == guild_id:
            return item
    return None


def store_voice_client(voice_client: VoiceClient):
    if not voice_client_exists(voice_client):
        voice_clients.append(voice_client)


def remove_voice_client(voice_client: VoiceClient):
    for item in voice_clients:
        if item.guild.id == voice_client.guild.id:
            voice_clients.remove(item)
