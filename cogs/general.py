from random import randint

from discord.ext import commands
from datetime import datetime

#########################
#       Extension       #
#########################

class general(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name="roll", help="Roll a random number between 1 & 100\nChange the maximum number with !roll max.\nChange both minimum & maximum numbers with !roll min max.")
    async def roll(self,ctx, range_opt1:int = 100, range_opt2:int = None):

        if range_opt2:
            min = range_opt1
            max = range_opt2
        else:
            min = 1
            max = range_opt1
        self.bot.dispatch("sendReply",ctx,f"Rolling ({min}-{max}): {randint(min,max)}")
    
    @commands.command(name="bigemoji",help="Sends the given emoji in original size. Usage: !bigemoji :emoji:")
    async def bigemoji(self,ctx,emoji):
        if emoji in self.bot.emojiDict:
            id = self.bot.emojiDict[emoji].split(":")[2][:-1]
            reply = f"https://cdn.discordapp.com/emojis/{id}"
            await ctx.message.delete()
            logmsg = f"bigemoji: {ctx.author} used bigemoji on {emoji}."
        elif emoji in self.bot.emojiDict.values():
            id = emoji.split(":")[2][:-1]
            reply = f"https://cdn.discordapp.com/emojis/{id}"
            await ctx.message.delete()
            logmsg = f"bigemoji: {ctx.author} used bigemoji on {emoji}."
        else:
            reply = "Unrecognised emoji"
        self.bot.dispatch("log",logmsg)
        self.bot.dispatch("sendReply",ctx,reply)


    @commands.command(name="onedaycloser",help="We're always one day closer...")
    async def onedaycloser(self, ctx):

        now = datetime.now()
        the_day = datetime(2026, 6, 27)
        time_to_d_day = the_day - now

        self.bot.dispatch("sendReply",ctx,f"We're {time_to_d_day.days} days away...")
        


#########################
#      FINAL SETUP      #
#########################

async def setup(bot):
    await bot.add_cog(general(bot))