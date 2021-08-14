from discord.ext import commands
from discord import VoiceChannel
import string, datetime, asyncio

#########################
#       Extension       #
#########################

class events(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    #########################
    #   DEFAULT LISTENERS   #
    #########################

    #on_message for prop responses & any future general replies
    @commands.Cog.listener()
    async def on_message(self,msg):
        if msg.author.bot == True and msg.channel.id != 872774897926025266: #If a bot msg (& not in the spy channel) then go away
            return

        responses = {
            "who":"cares?",
            "what":"ever.",
            "why":"are you still talking?",
            "when":"did I ask?",
            "how":"uhh.. how did I ask?"}

        s = str.lower(msg.content.translate(str.maketrans('', '', string.punctuation))).replace(" ","")

        if s in responses:
            reply = responses[s]
            await msg.reply(reply)
            self.bot.dispatch("log",f"on_message: Gottem! Replied \"{reply}\" to {msg.author}. They said \"{msg.content}\"")

        if msg.channel.id == 872774897926025266:
            self.bot.dispatch("log",f"on_message: Deleted spy message from: {msg.author}. Message: {msg.content}")
            await self.bot.dispatch("delete_message",msg)

    
    #Add new members to db
    @commands.Cog.listener()
    async def on_member_join(self,member):
        if member.bot:
            return
        self.bot.dispatch("queryAddMember", [(member.id,member.name,member.display_name)])

    #Update member info, just use AddMember as it handles duplicates fine. This just updates display_name
    @commands.Cog.listener()
    async def on_member_update(self,before,after):
        if before.bot:
            return
        if before.display_name != after.display_name:
            self.bot.dispatch("queryAddMember", [(after.id,after.name,after.display_name)])

    #Update user info, same as above but will also see changes to username
    @commands.Cog.listener()
    async def on_user_update(self,before,after):
        if before.bot:
            return
        if before.name != after.name:
            self.bot.dispatch("queryAddMember", [(after.id,after.name,after.display_name)])
    
    #Fishy Reaction Matching
    @commands.Cog.listener()
    async def on_reaction_add(self,reaction,user):
        if user.bot:
            return

        if self.bot.gameStatus == ["active","connect4"]:
            self.bot.dispatch("connect4Reaction",user,reaction)
            return

        if user.id == 195114381820952577: #mine
            await reaction.message.add_reaction(reaction.emoji)

    #Fishy reaction removing
    @commands.Cog.listener()
    async def on_reaction_remove(self,reaction,user):
        if user.bot:
            return

        if self.bot.gameStatus == ["active","connect4"]: #Just ignore this when the game's running
            return

        if user.id == 195114381820952577:
            await reaction.message.remove_reaction(reaction.emoji,self.bot.user)
    
    #YNWA
    @commands.Cog.listener()
    async def on_voice_state_update(self,member,before,after):
        if member.bot:
            return
        if after.channel != before.channel:
            channels = [i for i in member.guild.channels if isinstance(i,VoiceChannel)]
            for channel in channels:
                if len(channel.members) == 1 and channel.members[0].id == 195114381820952577:
                    self.bot.vc = await channel.members[0].voice.channel.connect()
                    self.bot.dispatch("log",f"ynwa: Joined {self.bot.vc.channel.name}")
                    break                
                else:
                    if self.bot.vc is not None and self.bot.vc.is_connected() and self.bot.vc.channel == channel:
                        self.bot.dispatch("log",f"ynwa: Leaving {self.bot.vc.channel.name}")
                        await self.bot.vc.disconnect()
                        self.bot.vc = None
                        break

    #########################
    #    EVENT LISTENERS    #
    #########################

    #General send event
    @commands.Cog.listener()
    async def on_sendReply(self,ctx,msg):
        await ctx.send(msg)
        with open("replies.log","a") as logfile:
            logfile.write(f"{datetime.datetime.now()} - {msg}\n")

    #Logging
    @commands.Cog.listener()
    async def on_log(self,msg):
        print(f"{datetime.datetime.now()} - {msg}")
        with open("general.log","a") as logfile:
            logfile.write(f"{datetime.datetime.now()} - {msg}\n")

    #Error handling
    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        with open("error.log","a") as logfile:
            if event == "on_message":
                logfile.write(f"{datetime.datetime.now()} - Event: on_message - {args[0]}\n")
                raise
            else:
                raise
    
    #Message deleter
    @commands.Cog.listener()
    async def on_delete_message(self, message):
        await asyncio.sleep(5)
        await message.delete()

#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(events(bot))