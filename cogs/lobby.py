from discord.ext import commands,timers
from discord import Embed,Member

#########################
#       Extension       #
#########################

class Lobby:
    def __init__(self,lobby_owner,game_type):
        self.lobby_players = [lobby_owner]
        self.lobby_owner = lobby_owner
        self.in_game = False
        self.game_type = game_type
        self.game = None
        self.message = None
        self.timer = None

        # you can include stuff like lobby betting pot in here


    def has_member(self,member):
        if member in self.lobby_players:
            return True
    
    def is_owner(self, member):
        return self.lobby_owner == member


    def start_game(self, game_object):
        self.in_game = True
        self.game = game_object


class lobby(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.bot.game_lobbies = []
        self.bot.get_lobby_from_owner = self.get_lobby_from_owner
        self.bot.get_member_lobby = self.get_member_lobby
        self.bot.lobby_end_game = self.lobby_end_game

    def get_member_lobby(self,member):
        for lobby in self.bot.game_lobbies:
            if lobby.has_member(member):
                return lobby

        return None

    def get_lobby_from_owner(self,lobby_owner):
        for lobby in self.bot.game_lobbies:
            if lobby.lobby_owner == lobby_owner:
                return lobby

        return None
    
    async def lobby_end_game(self,lobby):
        await lobby.message.edit(embed=self.get_lobby_embed_message(lobby,closed=True)) 
        self.bot.game_lobbies.remove(lobby)


    def get_lobby_embed_message(self,lobby, closed=False):
        embed = Embed(title=f"{lobby.lobby_owner.display_name} wants to play {self.bot.prettyGames[lobby.game_type]}")
        player_list = ', '.join(i.name for i in lobby.lobby_players)
        embed.set_thumbnail(url=lobby.lobby_owner.avatar_url)
        embed.add_field(name='Game',value=self.bot.prettyGames[lobby.game_type])
        embed.add_field(name='Owner',value=lobby.lobby_owner.mention)
        if not closed:
            embed.add_field(name='State',value="Waiting for players..." if not lobby.in_game else "In Game")
            embed.add_field(name='Players',value=player_list if len(player_list) > 0 else "None",inline=False)
            embed.add_field(name='Instructions',value=f"If you want to join the lobby type !join {lobby.lobby_owner.mention}",inline=False)
        else:
            embed.add_field(name='State',value="Closed")
            embed.add_field(name='Closed',value=f"Lobby is now closed.",inline=False)
        return embed





    #########################
    #        COMMANDS       #
    #########################
    #join
    @commands.command(name="join",help="Join a currently open game lobby")
    async def join(self,ctx, lobby_owner:Member="default"):
        #Restrict lobby commands to game channel (Don't tell anyone that the game commands still work jeff)
        if ctx.channel.id != self.bot.game_channel_id:
            game_channel = self.bot.get_channel(self.bot.game_channel_id)
            if game_channel is not None:
                self.bot.dispatch("sendReply",ctx,f"Games can only be played in the game channel: {game_channel.mention}")
                return

        member_lobby = self.get_member_lobby(ctx.author)
        #If no lobby
        if member_lobby:
            self.bot.dispatch("sendReply",ctx,"You're already in a lobby!")
            return

        if not lobby_owner:
            self.bot.dispatch("sendReply",ctx,"lobby not found")
            return
        
        lobby_to_join = None

        if lobby_owner == "default" and len(self.bot.game_lobbies) == 1:
            lobby_to_join = self.bot.game_lobbies[0]

        else:
            lobby_to_join = self.get_lobby_from_owner(lobby_owner)
    
        
        if not lobby_to_join:
            self.bot.dispatch("sendReply",ctx,"lobby not found")
            return

        if lobby_to_join.in_game:
            self.bot.dispatch("sendReply",ctx,"Can't join a running game")
            return


        game_cog = self.bot.get_cog(lobby_to_join.game_type+"_game")
        if game_cog.lobby_capacity_check_join(lobby_to_join.lobby_players):
            lobby_to_join.lobby_players.append(ctx.author)
            self.bot.dispatch("log",f"lobby: {ctx.author} joined {lobby_to_join.game_type} lobby")
            await lobby_to_join.message.edit(embed=self.get_lobby_embed_message(lobby_to_join)) 
        else:
            reply = self.bot.get_cog(lobby_to_join.game_type+"_game").lobby_capacity_fail_message()
            self.bot.dispatch("sendReply",ctx,reply)

    @commands.command(name="game",help="Start a game {gamename}")
    async def game(self,ctx, game:str = "help"):
        #Restrict lobby commands to game channel (Don't tell anyone that the game commands still work jeff)
        if ctx.channel.id != self.bot.game_channel_id:
            game_channel = self.bot.get_channel(self.bot.game_channel_id)
            if game_channel is not None:
                self.bot.dispatch("sendReply",ctx,f"Games can only be played in the game channel: {game_channel.mention}")
                return

        if self.get_member_lobby(ctx.author):
            self.bot.dispatch("sendReply",ctx,"Can't start a new lobby, you're already in one!")
            return 


        if game == "help":
            embed = Embed()
            embed.add_field(name="Supported Games",value="\n".join([i for i in self.bot.prettyGames]))
            await ctx.send(embed=embed)
            return          


        match = [i for i in self.bot.prettyGames if game in i]
        if len(match) == 1:
            lobby = Lobby(ctx.author,match[0])
            lobby.timer = timers.TimerManager(self.bot)
            lobby.timer.create_timer("lobbytimer",self.bot.lobbyTimeout,[lobby])
            self.bot.game_lobbies.append(lobby)
            self.bot.dispatch("log",f"lobby: {ctx.author} created {match[0]} lobby.")
            lobby.message = await ctx.send(embed=self.get_lobby_embed_message(lobby)) 
            return

        self.bot.dispatch("sendReply",ctx,f"game not found.")


    #start
    @commands.command(name="start",help="Start the currently open game lobby")
    async def start(self,ctx):
        #Restrict lobby commands to game channel (Don't tell anyone that the game commands still work jeff)
        if ctx.channel.id != self.bot.game_channel_id:
            game_channel = self.bot.get_channel(self.bot.game_channel_id)
            if game_channel is not None:
                self.bot.dispatch("sendReply",ctx,f"Games can only be played in the game channel: {game_channel.mention}")
                return

        #Check lobby is running & starter is lobby creator

        member_lobby = self.get_member_lobby(ctx.author)
        if not member_lobby:
            self.bot.dispatch("sendReply",ctx,"You aren't part of any lobby. Please create a new one using the game command.")
            return 

        if not member_lobby.is_owner(ctx.author):
            self.bot.dispatch("sendReply",ctx,"Only the user that created the lobby can start it!")
            return

        if member_lobby.in_game:
            self.bot.dispatch("sendReply",ctx,"You can't start the lobby, it's already running a game!")
            return
        

        game_cog = self.bot.get_cog(member_lobby.game_type+"_game")

        if not game_cog.lobby_capacity_check_start(member_lobby.lobby_players):
            self.bot.dispatch("sendReply",ctx,game_cog.lobby_capacity_fail_message())
            return
        

        member_lobby.game = game_cog.get_game_class(member_lobby.lobby_players)
        member_lobby.in_game = True
        member_lobby.timer.clear()
        await member_lobby.message.edit(embed=self.get_lobby_embed_message(member_lobby)) 
        self.bot.dispatch("log",f"{member_lobby.game_type}: game started by {ctx.author} with players:{','.join(i.name for i in member_lobby.lobby_players[1:])}")
        game_cog.on_game_start(ctx)
        return
    
    #Leave lobby
    @commands.command(name="leave",help="Leave the game lobby you're currently a member of")
    async def leave_lobby(self,ctx):
        #Restrict lobby commands to game channel (Don't tell anyone that the game commands still work jeff)
        if ctx.channel.id != self.bot.game_channel_id:
            game_channel = self.bot.get_channel(self.bot.game_channel_id)
            if game_channel is not None:
                self.bot.dispatch("sendReply",ctx,f"Games can only be played in the game channel: {game_channel.mention}")
                return

        member_lobby = self.get_member_lobby(ctx.author)
        if not member_lobby:
            self.bot.dispatch("sendReply",ctx,"You're not in a lobby")
            return

        if member_lobby.is_owner(ctx.author):
            self.bot.dispatch("sendReply",ctx,"You're the lobby owner! You can only leave by cancelling the lobby with !cancel.")
            return
        
        member_lobby.lobby_players.remove(ctx.author)
        self.bot.dispatch("log",f"lobby: {ctx.author} left {member_lobby.game_type} lobby")
        await member_lobby.message.edit(embed=self.get_lobby_embed_message(member_lobby))         

    #kill_lobby
    @commands.command(name="cancel",help="Close the currently open game lobby\nLobby will automatically time out after 5 minutes.")
    async def kill_lobby(self,ctx):
        #Restrict lobby commands to game channel (Don't tell anyone that the game commands still work jeff)
        if ctx.channel.id != self.bot.game_channel_id:
            game_channel = self.bot.get_channel(self.bot.game_channel_id)
            if game_channel is not None:
                self.bot.dispatch("sendReply",ctx,f"Games can only be played in the game channel: {game_channel.mention}")
                return

        member_lobby = self.get_member_lobby(ctx.author)
        if not member_lobby:
            self.bot.dispatch("sendReply",ctx,"You're not in a lobby")
            return
        if not member_lobby.is_owner(ctx.author):
            self.bot.dispatch("sendReply",ctx,"You're not the owner")
            return
        if member_lobby.in_game:
            self.bot.dispatch("sendReply",ctx,"Can't cancel a running game")
            return

        await member_lobby.message.edit(embed=self.get_lobby_embed_message(member_lobby,closed=True)) 
        self.bot.game_lobbies.remove(member_lobby)
        reply = f"{member_lobby.lobby_owner.mention}'s {self.bot.prettyGames[member_lobby.game_type]} lobby closed."
        self.bot.dispatch("log",f"lobby: {member_lobby.game_type} lobby killed by {ctx.author}.")
        self.bot.dispatch("sendReply",ctx,reply)

    #########################
    #    EVENT LISTENERS    #
    #########################

    @commands.Cog.listener()
    async def on_lobbytimer(self,member_lobby):
        await member_lobby.message.edit(embed=self.get_lobby_embed_message(member_lobby,closed=True))
        self.bot.game_lobbies.remove(member_lobby)
        self.bot.dispatch("log",f"lobby: {member_lobby.game_type} lobby timed out.")
        self.bot.dispatch("sendReply",member_lobby.message.channel,f"{member_lobby.lobby_owner.mention}'s {self.bot.prettyGames[member_lobby.game_type]} lobby timed out.")
        
#########################
#      FINAL SETUP      #
#########################

def setup(bot):
    bot.add_cog(lobby(bot))