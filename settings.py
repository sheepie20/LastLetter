from tkinter import COMMAND
import discord
from discord.ext import commands

import os
from dotenv import load_dotenv
load_dotenv()

from pretty_help import PrettyHelp # type: ignore

INTENTS = discord.Intents.all()
COMMAND_PREFIX = commands.when_mentioned_or("ll ")
HELP_COMMAND = PrettyHelp(
    typing=False
)

TOKEN = os.getenv("DISCORD_TOKEN")