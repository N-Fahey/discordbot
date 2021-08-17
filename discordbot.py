import os,discord
from discord.ext import commands,timers
from dotenv import load_dotenv

class game_state():
    def __init__(self):
        self.in_lobby = False # In Lobby
        self.in_game = False # In Game
        self.game_type = None # Game type usually a string 
        self.game = None
        self.game_players = []
    
    def start_lobby(self,game_type):
        self.in_lobby = True
        self.game_type = game_type

    def start_game(self,game):
        self.in_lobby = False
        self.in_game = True
        self.game = game

    def end_game(self):
        self.in_lobby = False
        self.in_game = False
        self.game_type = None
        self.game = None
        self.game_players = []
    
    def add_player(self,player):
        self.game_players.append(player)

#Get required environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILDID')

#Intents
intents = discord.Intents.default()
intents.members = True
intents.reactions = True

#Setup attributes
self = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)
self.timer = timers.TimerManager(self)
self.game = None
self.game_state = game_state()
self.gamePlayers = []
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