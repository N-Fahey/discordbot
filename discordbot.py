import os
import discord
import yaml

from discord.ext import commands
from dotenv import load_dotenv
from asyncio import run

#Get required environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILDID')
OPENAI_KEY = os.getenv('OPENAI_KEY')

#Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

async def get_prefix(bot,msg):
    #Allows using mention instead of prefix
    #prefixes = commands.when_mentioned(bot,msg)
    prefixes = []

    if hasattr(bot,"prefixes"):
        for i in bot.prefixes:
            prefixes.append(i)
    else: #If no prefixes to load, use default prefix !
        prefixes.append("!")

    return prefixes

#Setup attributes
self = commands.Bot(command_prefix=get_prefix, intents=intents)
self.emojiDict = {}
self.console_listener = None
self.vc = None
self.ai_key = OPENAI_KEY
self.loaded_cogs = []

#Get settings
async def load_settings():
    with open("settings.yaml", "r") as f:
        settings = yaml.safe_load(f)
        return settings

#load extensions
async def load_extensions():    
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await self.load_extension(f"cogs.{file}"[:-3])
            self.loaded_cogs.append(file[:-3])

#Setup event, triggers on login & refresh
@self.event
async def on_ready():
    self.dispatch("log",f"Loaded extensions: {', '.join(self.loaded_cogs)}")
    self.emojiDict = {e.name:str(e) for e in self.emojis}

    #Load settings
    settings = await load_settings()

    if isinstance(settings,dict):
        for setting in settings:
            setattr(self,setting,settings[setting])
        self.dispatch("log",f"Succesfully loaded settings: {', '.join(settings.keys())}")
    else:
        raise ValueError(f"Failed to load settings: {settings}")

    self.guild = discord.utils.find(lambda g: g.id == int(GUILD), self.guilds)
    self.dispatch('populate_db')
    
    self.dispatch("log",f"{self.user} now ready on guild: {self.guild.name}, guild ID: {self.guild.id}")
    self.console_listener = self.loop.create_task(self.get_cog('console_shell').console_handler())

@self.event
async def on_reload(ctx):
    if self.console_listener is not None:
        self.console_listener.cancel()
        self.console_listener = None

    self.loaded_cogs = list(self.extensions)
    for cog in self.loaded_cogs:
        await self.unload_extension(cog)
    self.loaded_cogs = []
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await self.load_extension(f"cogs.{file}"[:-3])
            self.loaded_cogs.append(file[:-3])

    print(f"Reloaded extensions: {', '.join(self.loaded_cogs)}")
    if ctx is not None:
        await ctx.send(f"Reloaded extensions: {', '.join(self.loaded_cogs)}")

    self.console_listener = self.loop.create_task(self.get_cog('console_shell').console_handler())

#Initialise the bot
async def main():
    async with self:
        discord.utils.setup_logging()
        await load_extensions()
        await self.start(TOKEN)

run(main())
