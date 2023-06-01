import logging
import os
import json
import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands


_logger = logging.getLogger("main")

_logger.debug("Loading .env file...")
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ALLOWED_SERVERS = json.loads(os.getenv("SERVER_ID"))
MAX_IDLE_SECONDS = os.getenv("MAX_IDLE_SECONDS")


intents = nextcord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)


def is_guild_allowed(id: int):
    _logger.debug(f"Checking if guild with id {str(id)} is allowed...")
    try:
        return ALLOWED_SERVERS[str(id)]
    except Exception:
        pass
    return False
