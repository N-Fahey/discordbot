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
            "how":"uhh.. how did I ask?",
            "bazinga":"https://i.kym-cdn.com/entries/icons/original/000/011/946/Bazinga-Sheldon-Cooper-The-Big-Bang-Theory-85831432.jpg"
            }

        s = str.lower(msg.content.translate(str.maketrans('', '', string.punctuation))).replace(" ","")

        if s in responses:
            reply = responses[s]
            await msg.reply(reply)
            self.bot.dispatch("log",f"on_message: Gottem! Replied \"{reply}\" to {msg.author}. They said \"{msg.content}\"")

        if msg.channel.id == 872774897926025266:
            self.bot.dispatch("log",f"on_message: Deleted spy message from: {msg.author}. Message: {msg.content}")
            self.bot.dispatch("delete_message",msg)

        if msg.author == 120826860883017728:
            msg_tokens = msg.split()
            tagged_anyone = False
            tagged_fish = False
            for token in msg_tokens:
                if token.startswith("<") and token.endswith(">") and not token == "<@195114381820952577>":
                    tagged_anyone = True
                if token == "<@195114381820952577>":
                    tagged_fish = True
            if tagged_anyone and not tagged_fish:
                await msg.reply("And your thoughts as well, Mr. <@195114381820952577>")
                self.bot.dispatch("log",f"on_message: I included Mr Fish in the tags too!")

    
    #Add new members to db
    @commands.Cog.listener()
    async def on_member_join(self,member):
        if member.bot:
            return
        self.bot.dispatch("queryAddMember",member.id,member.name,member.display_name)

    #Update member info, just use AddMember as it handles duplicates fine. This just updates display_name
    @commands.Cog.listener()
    async def on_member_update(self,before,after):
        if before.bot:
            return
        if before.display_name != after.display_name:
            self.bot.dispatch("queryAddMember",after.id,after.name,after.display_name)

    #Update user info, same as above but will also see changes to username
    @commands.Cog.listener()
    async def on_user_update(self,before,after):
        if before.bot:
            return
        if before.name != after.name:
            self.bot.dispatch("queryAddMember",after.id,after.name,after.display_name)
    
    #Fishy Reaction Matching
    @commands.Cog.listener()
    async def on_reaction_add(self,reaction,user):
        if user.bot:
            return


        member_lobby = self.bot.get_member_lobby(user)
        if member_lobby and member_lobby.in_game:
            if member_lobby.game_type == "connect4": #Just ignore this when the game's running
                self.bot.dispatch("connect4Reaction",user,reaction)
                return

        if user.id == 195114381820952577: #mine
            await reaction.message.add_reaction(reaction.emoji)

    #Fishy reaction removing
    @commands.Cog.listener()
    async def on_reaction_remove(self,reaction,user):
        if user.bot:
            return

        member_lobby = self.bot.get_member_lobby(user)
        if member_lobby and member_lobby.in_game:
            if member_lobby.game_type == "connect4": #Just ignore this when the game's running
                return

        if user.id == 195114381820952577:
            await reaction.message.remove_reaction(reaction.emoji,self.bot.user)
    
    #YNWA
    @commands.Cog.listener()
    async def on_voice_state_update(self,member,before,after):
        if member.bot:
            return
        
        if member.guild.id == 629288645257461780:
            try:
                target_channel = self.bot.guild.get_member(195114381820952577).voice.channel
            except AttributeError:
                target_channel = None

            if target_channel:
                if len(target_channel.members) == 1:
                    if self.bot.vc:
                        await self.bot.vc.move_to(target_channel)
                    else:
                        self.bot.vc = await target_channel.connect()
                elif (self.bot.user in target_channel.members and len(target_channel.members) != 2):
                    await self.bot.vc.disconnect()
                    self.bot.vc = None
                else:
                    pass
            else:
                if self.bot.vc:
                    await self.bot.vc.disconnect()
                    self.bot.vc = None

    #########################
    #    EVENT LISTENERS    #
    #########################

    #General send event
    @commands.Cog.listener()
    async def on_sendReply(self,ctx,msg):
        await ctx.send(msg)
        with open("replies.log","a",encoding="utf-8") as logfile:
            logfile.write(f"{datetime.datetime.now()} - {msg}\n")

    #Logging
    @commands.Cog.listener()
    async def on_log(self,msg):
        print(f"{datetime.datetime.now()} - {msg}")
        with open("general.log","a", encoding="utf-8") as logfile:
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