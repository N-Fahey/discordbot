from discord.ext import commands
from discord import Member,Embed

#########################
#       Extension       #
#########################

class currency(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    #########################
    #        COMMANDS       #
    #########################

    #Claim the dole
    @commands.command(name="dole",help="Claim your daily handout. Only available to povos.")
    async def dole(self,ctx):
        member_lobby = self.bot.get_member_lobby(ctx.author)

        if member_lobby is not None:
            await ctx.send("No dole while you're in a lobby ya rat dog.")
            return

        sqlCog = self.bot.get_cog("sql")
        authorId = ctx.author.id
        check = await sqlCog.queryCheckDole((authorId,))
        if check["allow"]:
            await sqlCog.queryPayDole([(authorId,)])
            reply = f"Your handout has been processed. Balance is now {self.bot.currencyCode}{check['balance']+self.bot.dolePayment}."
        elif check["balance"] >= self.bot.doleLimit:
            reply = "You have too much money. Poors only"
        else:
            hrs, rem = divmod(check['nextdole'].seconds, 3600)
            mins, sec = divmod(rem, 60)
            reply = f"`{ctx.author.display_name}`, you already received your daily handout. Wait {hrs}h {mins}m"
        
        await ctx.send(reply)

    #Transfer
    @commands.command(name="transfer",help="Usage: !transfer {@user} {amount}. Transfer money to the specified user.")
    async def transfer(self,ctx,target:Member = None,amount:int = 0):
        if target is not None and amount > 0:
            sqlCog = self.bot.get_cog("sql")
            if await sqlCog.queryTransfer([(amount,ctx.author.id,target.id)]):
                reply = f"Succesfully sent {self.bot.currencyCode}{amount} to `{target.display_name}`."
            else:
                reply = f"You don't have enough money to do that!"
        else:
            reply = "Transfer failed. Make sure you !transfer {@user} {amount}. Amount must be greater than zero!"
        await ctx.send(reply)
    
    #Check balance
    @commands.command(name="balance",help="Check your bank balance!")
    async def balance(self,ctx):
        sqlCog = self.bot.get_cog("sql")
        bal = await sqlCog.queryCheckBalance((ctx.author.id,))
        
        await ctx.send(f"`{ctx.author.display_name}`, your balance is {self.bot.currencyCode}{bal}")
    
    @commands.command(name="top10", help="View the top 10 currency holders on the server.")
    async def test(self,ctx):
        sql_cog = self.bot.get_cog('sql')
        top10 = await sql_cog.queryTop10()
        embed = Embed(title='The 1%')
        embed.add_field(name="Name",value='\n'.join(top10.keys()))
        embed.add_field(name="Bank",value='\n'.join(top10.values()))
        await ctx.send(embed=embed)
            
def setup(bot):
    bot.add_cog(currency(bot))