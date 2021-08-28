from discord.ext import commands

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
    async def test(self,ctx):
        pass


    #Eval
    @commands.command(name="eval")
    @commands.has_permissions(administrator=True)
    async def cmd_eval(self,ctx,arg):
        await ctx.send(f"```python\n{eval('self.bot.' + arg)}```")

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


    #POPULATE DATABASE (This occurs on each restart)
    @commands.command(name="populatedb",help="Populate database")
    @commands.has_permissions(administrator=True)
    async def populatedb(self,ctx):
        try:
            self.bot.dispatch("populatedb",ctx)
        except:
            await ctx.send("Error populating db")  

    #########################
    #    EVENT LISTENERS    #
    #########################

    #Reset
    @commands.Cog.listener()
    async def on_reset(self):
        self.bot.emojiDict = {}
        self.bot.emojiDict = {e.name:str(e) for e in self.bot.emojis}
        self.bot.vc = None
        self.bot.game_lobbies = []
        return True

#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(admin(bot))