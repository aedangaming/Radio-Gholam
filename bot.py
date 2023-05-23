import os
import json
import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ALLOWED_SERVERS = json.loads(os.getenv("SERVER_ID"))


intents = nextcord.Intents.all()
intents.message_content = True
intents.members = True
client = commands.Bot(command_prefix="!", intents=intents)


def is_guild_allowed(id: int):
    try:
        return ALLOWED_SERVERS[str(id)]
    except Exception as e:
        print(e)
    return False
