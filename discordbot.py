import os,discord
from discord.ext import commands,timers
from dotenv import load_dotenv

#Get required environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILDID')

#Intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True


#Setup attributes
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)
bot.timer = timers.TimerManager(bot)
bot.game = None
bot.gameStatus = ["inactive",""]
bot.gamePlayers = []
bot.emojiDict = {}
bot.vc = None

#Load cogs
cogs = []

if __name__ == "__main__":
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            bot.load_extension(f"cogs.{file}"[:-3])
            cogs.append(file[:-3])

#Setup event, triggers on login & refresh
@bot.event
async def on_ready():
    bot.dispatch("log",f"Loaded extensions: {', '.join(cogs)}")
    bot.emojiDict = {e.name:str(e) for e in bot.emojis}

    #Load settings
    sqlCog = bot.get_cog('sql')
    settings = await sqlCog.queryRetrieveSettings()
    if isinstance(settings,dict):
        for setting in settings:
            setattr(bot,setting,settings[setting])
        bot.dispatch("log",f"Succesfully loaded settings: {settings.keys()}")
    else:
        raise ConnectionError(f"Failed to load settings: {settings}")

    guild = discord.utils.find(lambda g: g.id == int(GUILD), bot.guilds)
    bot.dispatch("log",f"{bot.user} now ready on guild: {guild.name}, guild ID: {guild.id}")

@bot.event
async def on_reload(ctx):
    cogs = list(bot.extensions)
    for cog in cogs:
        bot.unload_extension(cog)
    cogs = []
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            bot.load_extension(f"cogs.{file}"[:-3])
            cogs.append(file[:-3])
    
    await ctx.send(f"Reloaded extensions: {', '.join(cogs)}")

#Initialise the bot
bot.run(TOKEN)