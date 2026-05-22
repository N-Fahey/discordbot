import asyncio
import datetime
import string
from random import randint

from discord.ext import commands

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
            "where":"is my care?",
            "when":"did I ask?",
            "how":"is my cow?",
            "bazinga":"https://i.kym-cdn.com/entries/icons/original/000/011/946/Bazinga-Sheldon-Cooper-The-Big-Bang-Theory-85831432.jpg",
            "test":"test"
            }

        s = str.lower(msg.content.translate(str.maketrans('', '', string.punctuation))).replace(" ","")

        if s in responses:
            reply = responses[s]
            await msg.reply(reply)
            self.bot.dispatch("log",f"on_message: Gottem! Replied \"{reply}\" to {msg.author}. They said \"{msg.content}\"")

        if msg.channel.id == 872774897926025266:
            self.bot.dispatch("log",f"on_message: Deleted spy message from: {msg.author}. Message: {msg.content}")
            self.bot.dispatch("delete_message",msg)
        
        #AI responses
        if self.bot.user.mentioned_in(msg):
            if msg.content.startswith(self.bot.user.mention):
                self.bot.dispatch("bot_mentioned",msg)
        
        #AI responses for direct replies to the bot
        if msg.reference is not None:
            if msg.reference.cached_message is not None:
                if msg.reference.cached_message.author == self.bot.user:
                    self.bot.dispatch("bot_mentioned",msg)
                    
        if randint(1, 1000000) == 999999:
            await msg.reply("rip bozo")
            await asyncio.sleep(5)
            msg.author.ban(reason="shit luck better luck next time")
        
        #Special reacts
        if msg.author.id == 142309150016143360 and randint(1, 4) == 1:
            await msg.add_reaction("👲")
    
    #Add new members to db
    @commands.Cog.listener()
    async def on_member_join(self,member):
        if member.bot:
            return
        
        res = await self.bot.api.add_user(member.id, member.name, member.display_name)

        if not res['success']:
            raise RuntimeError(f"Error adding user (on_member_join): {member.name}, uid: {member.id}")

    #Update member info, just use AddMember as it handles duplicates fine. This just updates display_name
    @commands.Cog.listener()
    async def on_member_update(self,before,after):
        if before.bot:
            return
        if before.display_name != after.display_name:
            await self.bot.api.update_user(after.id, display_name=after.display_name)

    #Update user info, same as above but will also see changes to username
    @commands.Cog.listener()
    async def on_user_update(self,before,after):
        if before.bot:
            return
        if before.name != after.name:
            await self.bot.api.update_user(after.id, username=after.name)
    
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
        #Don't do on test guild
        if member.guild.id != 629288645257461780:
            return

	#Ignore bot changes
        if member.bot:
            return

        #Get fish channel / None if not connected
        try:
            fish_channel = self.bot.guild.get_member(195114381820952577).voice.channel
        except AttributeError:
            fish_channel = None

        #DC if fish not connected
        if not fish_channel:
            if self.bot.vc:
                self.bot.dispatch('log','YNWA: Fish left! Leaving...')
                self.bot.dispatch('vc_disconnect')
            return

        #Fish in channel alone - Connect / move
        if len(fish_channel.members) == 1:
            if self.bot.vc: #Move if already connected
                self.bot.dispatch('log','YNWA: Fish moved channels! Following...')
                await self.bot.vc.move_to(fish_channel)
                return
            else: #Connect
                self.bot.dispatch('log','YNWA: Fish is all alone! Joining...')
                self.bot.vc = await fish_channel.connect()
                return
        
        #If not connected stop processing
        if not self.bot.vc:
            return

        #Just fish & bot in channel - no action
        if len(fish_channel.members) == 2 and self.bot.user in fish_channel.members:
            return

        #2 or more members in channel, leave
        self.bot.dispatch('log','YNWA: Fish has other friends! Leaving...')
        self.bot.dispatch('vc_disconnect')

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
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  INFO  {msg}")
        with open("general.log","a", encoding="utf-8") as logfile:
            logfile.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  INFO  {msg}\n")

    #Error Log
    @commands.Cog.listener()
    async def on_error(self,msg):
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ERROR  {msg}")
        with open("error.log","a", encoding="utf-8") as logfile:
            logfile.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ERROR  {msg}\n")

    @commands.Cog.listener()
    async def on_vc_disconnect(self):
        if self.bot.vc:
            await self.bot.vc.disconnect(force=True)
            if not self.bot.vc.is_connected():
                self.bot.dispatch('log',"Deleting Voice Client")
                self.bot.vc = None
    
    #Message deleter
    @commands.Cog.listener()
    async def on_delete_message(self, message):
        await asyncio.sleep(5)
        await message.delete()

#########################
#      FINAL SETUP      #
#########################

async def setup(bot):
    await bot.add_cog(events(bot))
