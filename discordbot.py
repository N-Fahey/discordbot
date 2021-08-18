import os,discord
from discord.ext import commands
from dotenv import load_dotenv

#Get required environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILDID')

#Intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True

async def get_prefix(bot,msg):
    #Allows using mention instead of prefix
    prefixes = commands.when_mentioned(bot,msg)

    if hasattr(bot,"prefixes"):
        for i in bot.prefixes:
            prefixes.append(i)
    else: #If no prefixes to load, use default prefix !
        prefixes.append("!")

    return prefixes

#Setup attributes
self = commands.Bot(command_prefix=get_prefix, intents=intents)
self.emojiDict = {}
self.vc = None

#Load cogs
cogs = []

if __name__ == "__main__":
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            self.load_extension(f"cogs.{file}"[:-3])
            cogs.append(file[:-3])

#Setup event, triggers on login & refresh
@self.event
async def on_ready():
    self.dispatch("log",f"Loaded extensions: {', '.join(cogs)}")
    self.emojiDict = {e.name:str(e) for e in self.emojis}

    #Load settings
    sqlCog = self.get_cog('sql')
    settings = await sqlCog.queryRetrieveSettings()
    await sqlCog.on_populatedb(None)
    if isinstance(settings,dict):
        for setting in settings:
            setattr(self,setting,settings[setting])
        self.dispatch("log",f"Succesfully loaded settings: {settings.keys()}")
    else:
        raise ConnectionError(f"Failed to load settings: {settings}")

    guild = discord.utils.find(lambda g: g.id == int(GUILD), self.guilds)
    self.dispatch("log",f"{self.user} now ready on guild: {guild.name}, guild ID: {guild.id}")
    # populate database with users
    

@self.event
async def on_reload(ctx):
    cogs = list(self.extensions)
    for cog in cogs:
        self.unload_extension(cog)
    cogs = []
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            self.load_extension(f"cogs.{file}"[:-3])
            cogs.append(file[:-3])
    
    await ctx.send(f"Reloaded extensions: {', '.join(cogs)}")

#Initialise the bot
self.run(TOKEN)