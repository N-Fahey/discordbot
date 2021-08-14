from discord.ext import commands
from discord import Member

#########################
#       Extension       #
#########################

class currency(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    #########################
    #        COMMANDS       #
    #########################

    @commands.command(name="dole",help="Claim your daily handout. Only available to povos.")
    async def dole(self,ctx):
        sqlCog = self.bot.get_cog("sql")
        authorId = ctx.author.id
        check = await sqlCog.queryCheckDole((authorId,))
        if check["allow"]:
            await sqlCog.queryPayDole([(authorId,)])
            reply = f"Your handout has been processed. Balance is now ${check['balance']+100}."
        elif check["balance"] >= 1000:
            reply = "You have too much money. Poors only"
        else:
            reply = "You already received your daily handout. Wait 24 hours."
        
        await ctx.send(reply)

    @commands.command(name="transfer",help="Usage: /transfer {@user} {amount}. Transfer money to the specified user.")
    async def transfer(self,ctx,target:Member = None,amount:int = 0):
        if target is not None and amount > 0:
            sqlCog = self.bot.get_cog("sql")
            if await sqlCog.queryTransfer([(amount,ctx.author.id,target.id)]):
                reply = f"Succesfully sent {amount} to {target.display_name}"
            else:
                reply = f"You don't have enough money to do that!"
        else:
            reply = "Transfer failed. Make sure you /transfer {@user} {amount}. Amount must be greater than zero!"
        await ctx.send(reply)
            
def setup(bot):
    bot.add_cog(currency(bot))
