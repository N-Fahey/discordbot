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

        result = await self.bot.api.try_dole(ctx.author.id, self.bot.dolePayment, self.bot.doleLimit)
        
        if result['success']:
            await ctx.send(f"Your handout has been processed. Balance is now {self.bot.currencyCode}{result['balance']}.")
            return
        
        match result['reason']:
            case 'balance':
                await ctx.send("You have too much money. Poors only")
            case 'time':
                hrs, rem = divmod(result['delta'].seconds, 3600)
                mins, sec = divmod(rem, 60)
                await ctx.send(f"`{ctx.author.display_name}`, you received your daily handout {hrs}h {mins}m ago.")
            case _:
                raise RuntimeError(f"Unexpected result received (command-dole): {result['reason']}")

    #Transfer
    @commands.command(name="transfer",help="Usage: !transfer {@user} {amount}. Transfer money to the specified user.")
    async def transfer(self,ctx,target:Member = None,amount:int = 0):
        if target is not None and amount > 0:
            result = await self.bot.api.try_transfer(ctx.author.id, target.id, amount)
            
            if not result:
                await ctx.send("You don't have enough money to do that!")
                return

            await ctx.send(f"Succesfully sent {self.bot.currencyCode}{amount} to `{target.display_name}`.")
            return
        else:
            await ctx.send("Transfer failed. Make sure you !transfer {@user} {amount}. Amount must be greater than zero!")
    
    #Check balance
    @commands.command(name="balance",help="Check your bank balance!")
    async def balance(self,ctx):
        res = await self.bot.api.get_balance(ctx.author.id)
        
        balance = res['json']['balance']
        
        await ctx.send(f"`{ctx.author.display_name}`, your balance is {self.bot.currencyCode}{balance}")
    
    #Top10
    @commands.command(name="top10", help="View the top 10 currency holders on the server.")
    async def test(self,ctx):
        res = await self.bot.api.get_balances(count=10)
        
        top10_balances = [str(bal['balance']) for bal in res['json']['balances']]
        top10_names = [bal['display_name'] for bal in res['json']['balances']]

        if not top10_balances:
            await ctx.send('Nobody has any money')
        else:
            embed = Embed(title='The 1%')
            embed.add_field(name="Name",value='\n'.join(top10_names))
            embed.add_field(name="Bank",value='\n'.join(top10_balances))
            await ctx.send(embed=embed)
            
async def setup(bot):
    await bot.add_cog(currency(bot))