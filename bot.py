import os
import json
import logging
import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands

_logger = logging.getLogger("main")

_logger.debug("Loading .env file...")
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ALLOWED_SERVERS = json.loads(os.getenv("SERVER_ID"))

MAX_IDLE_SECONDS = os.getenv("MAX_IDLE_SECONDS")
if not MAX_IDLE_SECONDS or MAX_IDLE_SECONDS == "":
    MAX_IDLE_SECONDS = "300"
MAX_IDLE_SECONDS = float(MAX_IDLE_SECONDS)

PREFERRED_PROXIES = os.getenv("PREFERRED_PROXIES")
if not PREFERRED_PROXIES or PREFERRED_PROXIES == "":
    PREFERRED_PROXIES = "{}"
PREFERRED_PROXIES = json.loads(PREFERRED_PROXIES)


intents = nextcord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)


def is_guild_allowed(id: int):
    _logger.debug(f"Checking if guild with id {str(id)} is allowed...")
    try:
        return ALLOWED_SERVERS[str(id)]
    except Exception:
        pass
    return False
