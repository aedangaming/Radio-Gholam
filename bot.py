import os
import ast
import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ALLOWD_SERVERS = ast.literal_eval(os.getenv("SERVER_ID"))


intents = nextcord.Intents.all()
intents.message_content = True
intents.members = True
client = commands.Bot(command_prefix="!", intents=intents)


def is_guild_allowed(id: int):
    try:
        return ALLOWD_SERVERS[id]
    except Exception as e:
        print(e)
    return False


@client.event
async def on_ready():
    print(f"Logged in as {str(client.user)}")
