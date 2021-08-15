import operator,asyncio
from discord.ext import commands
from discord import VoiceChannel
from random import randint

#########################
#       Extension       #
#########################

class admin(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    #########################
    #        COMMANDS       #
    #########################
    
    #TESTING
    @commands.command(name="test", help="Testing")
    @commands.has_permissions(administrator=True)
    async def test(self,ctx, count:int=1):
        vcList = [i for i in ctx.guild.channels if isinstance(i,VoiceChannel)]
        vcCount = len(vcList)
        chatters = {}
        for vc in vcList:
            mems = vc.members
            for mem in mems:
                chatters[mem] = vc

        for _ in range(count):
            for chatter in chatters:
                await chatter.move_to(vcList[randint(0,vcCount - 1)])
            await asyncio.sleep(0.5)

        for chatter in chatters:
            await chatter.move_to(chatters[chatter])
        
        self.bot.dispatch("log",f"admin: {ctx.author} unleashed the kraken {count} times.")

    #RESET
    @commands.command(name="reset",help="Reset bot attributes.")
    @commands.has_permissions(administrator=True)
    async def reset(self,ctx):
        self.bot.dispatch("reset")
        await ctx.send("All attributes reset")

    #RELOAD
    @commands.command(name="reload",help="Reload all extensions")
    @commands.has_permissions(administrator=True)
    async def reload(self,ctx):
        try:
            self.bot.dispatch("reload",ctx)
        except:
            await ctx.send("Error reloading extensions")  
    
    #Get Attribute
    @commands.command(name="gattr")
    @commands.has_permissions(administrator=True)
    async def gattr(self, ctx, attr:str=""):
        if attr == "":
            reply = "No attribute supplied"
        try:
            reply = str(operator.attrgetter(attr)(self.bot))
        except:
            reply = "Invalid attribute"

        self.bot.dispatch("sendReply",ctx,reply)

    #########################
    #    EVENT LISTENERS    #
    #########################

    #Reset
    @commands.Cog.listener()
    async def on_reset(self):
        self.bot.game = None
        self.bot.timer.clear()    
        self.bot.gamePlayers = []
        self.bot.emojiDict = {}
        self.bot.emojiDict = {e.name:str(e) for e in self.bot.emojis}
        self.bot.vc = None
        self.bot.game_state  = {
            in_lobby: False # In Lobby
            in_game  : False # In Game
            game_type: None # Game type usually a string 
        }
        return True

#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(admin(bot))